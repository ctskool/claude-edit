"""Replace Whisper's word times with forced-alignment times (Qwen3-ForcedAligner, Apache-2.0). The text never changes.

Usage: python tools/align_words.py <audio16k.wav> <words.json|transcript.json>

Takes rawcut's words.json ([[text, start, end], ...]) or transcribe.py's transcript.json ({"segments": [{"words": [...]}]}),
rewrites start/end in place and keeps the old file as <name>.whisper.json. Whisper ends words ~190 ms early at pauses and sits
~120 ms off inside phrases; the aligner lands within ~40 ms. It hears digits ("3.1 Pro"), which wav2vec2 aligners smear by up to
0.5 s. Its grid is 80 ms, so two words can share a step: those get a 40 ms share of the word before them. A window whose word
count comes back different keeps Whisper's times and is reported.

Setup (once): python -m pip install "transformers>=5.13,<6"
"""
import json
import os
import re
import shutil
import sys
import wave

import numpy as np
import torch
from transformers import AutoModelForTokenClassification, AutoProcessor

MODEL = "Qwen/Qwen3-ForcedAligner-0.6B-hf"
MAX_S = 25.0     # the model takes 5 min; short windows keep a slip local


def read16k(path):
    w = wave.open(path)
    assert w.getframerate() == 16000 and w.getnchannels() == 1, "16 kHz mono wav expected"
    return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


def units(tokens):
    """Whisper tokens -> spoken words: "5" ".5," and "head" "-to" "-head" are one word to the aligner. [(first, last, text)]"""
    out = []
    for i, t in enumerate(tokens):
        if out and (t.startswith("-") or (t[:1] == "." and t[1:2].isdigit())):
            out[-1] = (out[-1][0], i, out[-1][2] + t)
        elif re.search(r"\w", t):
            out.append((i, i, t))
    return out


def windows(U, starts, ends):
    """Split at pauses so no window passes MAX_S: lists of indices into U."""
    groups, cur = [], []
    for k, (a, b, _) in enumerate(U):
        if cur and (starts[a] - ends[U[cur[-1]][1]] > 0.5 or ends[b] - starts[U[cur[0]][0]] > MAX_S):
            groups.append(cur)
            cur = []
        cur.append(k)
    return groups + [cur] if cur else groups


def align(proc, model, audio, text):
    inputs, lists = proc.prepare_forced_aligner_inputs(audio=audio, transcript=text, language="English", sampling_rate=16000)
    inputs = inputs.to(model.device, model.dtype)
    with torch.inference_mode():
        out = model(**inputs)
    return proc.decode_forced_alignment(logits=out.logits, input_ids=inputs["input_ids"], word_lists=lists,
                                        timestamp_token_id=model.config.timestamp_token_id)[0]


def main():
    wav, path = sys.argv[1], sys.argv[2]
    audio = read16k(wav)
    data = json.load(open(path, encoding="utf-8"))
    flat = data if isinstance(data, list) else [w for s in data["segments"] for w in s["words"]]
    is_list = isinstance(data, list)
    tokens = [w[0] if is_list else w["word"] for w in flat]
    starts = [w[1] if is_list else w["start"] for w in flat]
    ends = [w[2] if is_list else w["end"] for w in flat]
    U = units(tokens)
    proc = AutoProcessor.from_pretrained(MODEL)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("WARN alignment on CPU is slow; Whisper times are kept if alignment fails", file=sys.stderr)
    dtype = torch.bfloat16 if device == "cuda" and torch.cuda.is_bf16_supported() else torch.float32
    model = AutoModelForTokenClassification.from_pretrained(MODEL, dtype=dtype).to(device)
    groups = windows(U, starts, ends)
    moved, kept, new = 0, 0, {}
    for g_i, g in enumerate(groups):
        first, last = U[g[0]][0], U[g[-1]][1]
        lo = starts[first] - 0.25 if g_i == 0 else (ends[U[groups[g_i - 1][-1]][1]] + starts[first]) / 2
        hi = ends[last] + 0.25 if g_i == len(groups) - 1 else (ends[last] + starts[U[groups[g_i + 1][0]][0]]) / 2
        lo, hi = max(0.0, max(lo, starts[first] - 1.0)), min(len(audio) / 16000, min(hi, ends[last] + 1.0))
        stamps = align(proc, model, audio[int(lo * 16000):int(hi * 16000)], " ".join(U[k][2] for k in g))
        if len(stamps) != len(g):
            kept += len(g)
            print(f"  window {lo:.1f}-{hi:.1f}: {len(g)} words, aligner gave {len(stamps)}; kept Whisper's times", file=sys.stderr)
            continue
        for k, s in zip(g, stamps):
            new[k] = [round(float(s["start_time"]) + lo, 3), round(float(s["end_time"]) + lo, 3)]
            moved += 1
    # words that landed on one 80 ms step: take 40 ms from the word before
    keys = sorted(new)
    for p, k in zip(keys, keys[1:]):
        if new[k][1] - new[k][0] < 0.04 and new[p][1] - new[p][0] >= 0.12 and new[p][1] >= new[k][0] - 0.001:
            new[p][1] = round(new[p][1] - 0.04, 3)
            new[k][0] = round(new[k][0] - 0.04, 3)
    shutil.copyfile(path, os.path.splitext(path)[0] + ".whisper.json")
    for k, (s, e) in new.items():
        a, b, _ = U[k]
        n = b - a + 1
        for j, i in enumerate(range(a, b + 1)):                       # "5" ".5" share the word's span
            t0, t1 = round(s + (e - s) * j / n, 3), round(s + (e - s) * (j + 1) / n, 3)
            if is_list:
                flat[i][1], flat[i][2] = t0, t1
            else:
                flat[i]["start"], flat[i]["end"] = t0, t1
    if not is_list:
        for seg in data["segments"]:
            if seg["words"]:
                seg["start"], seg["end"] = seg["words"][0]["start"], seg["words"][-1]["end"]
    json.dump(data, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"aligned {moved} words in {len(groups)} windows, {kept} kept Whisper's times")


if __name__ == "__main__":
    main()
