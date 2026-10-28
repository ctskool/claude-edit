"""Flatten a faster-whisper transcript into words.json ([{i, text, start, end}]) for the content plan.

Usage: python make_words.py <transcript.json> <words.json> [--fix "11 Labs=ElevenLabs" --fix "Hua Shu=Huashu" ...]

Whisper splits hyphenated words into "open" "-source"; those are re-joined. Each --fix "A B=C" merges the consecutive
words A B (case-insensitive, trailing punctuation kept) into C, keeping the first start and last end, so misheard
product names can be corrected without touching the timings.
"""
import argparse
import json
import re


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript")
    ap.add_argument("out")
    ap.add_argument("--fix", action="append", default=[])
    a = ap.parse_args()
    d = json.load(open(a.transcript, encoding="utf-8"))
    ws = d.get("words") or [w for s in d["segments"] for w in s["words"]]
    out = []
    for w in ws:
        t = (w.get("word") or w.get("text")).strip()
        if t.startswith("-") and out:
            out[-1]["text"] += t
            out[-1]["end"] = round(w["end"], 3)
            continue
        out.append({"text": t, "start": round(w["start"], 3), "end": round(w["end"], 3)})
    for f in a.fix:
        src, dst = f.split("=", 1)
        parts = src.split()
        n = len(parts)
        i = 0
        while i <= len(out) - n:
            seg = out[i:i + n]
            bare = [re.sub(r"[^\w]+$", "", x["text"]).lower() for x in seg]
            if bare == [p.lower() for p in parts]:
                tail = re.search(r"[^\w]*$", seg[-1]["text"]).group(0)
                out[i:i + n] = [{"text": dst + tail, "start": seg[0]["start"], "end": seg[-1]["end"]}]
            i += 1
    words = [{"i": i, "text": w["text"], "start": w["start"], "end": w["end"]} for i, w in enumerate(out)]
    json.dump(words, open(a.out, "w", encoding="utf-8"), indent=0)
    print(f"{len(words)} words -> {a.out}")
    print(" ".join(w["text"] for w in words))


if __name__ == "__main__":
    main()
