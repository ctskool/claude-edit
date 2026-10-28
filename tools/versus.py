"""Raw vs Claude: one 16:9 talking-head take in which the speaker asks for edits out loud -> a 9:16 short with the edited
take on top (each edit lands on the word that names it) and the raw take (dead space cut only) below.

Usage (after tools/rawcut.py has written work/<id>/raw/cut.mp4):
  python tools/versus.py prep   <id> [--cut <video>] [--no-matte]   # panels, voice, words.json + words.txt, cut-out, draft edits.json
  (Claude writes work/<id>/versus/edits.json: header, labels, the edit list anchored on words, caption key words)
  python tools/versus.py chunks <id>                                # (re)draft caption chunks in edits.json from words.json
  python tools/versus.py music  <id> [--bpm 84] [--seed 7]          # synth music bed from the music_in / music_level edits
  python tools/versus.py build  <id>                                # validate edits.json -> versus/index.html + edits.js
  python tools/versus.py render <id> [--draft]                      # -> out/<id>_versus.mp4 (+ contact sheet, gates)

edits.json (times are seconds on the cut clock = words.json):
  {"duration": 48.15, "speech_end": 47.8,
   "header": {"line1": [["Same", 0.85], ["take,", 1.05]], "line2": [["One", 2.5], ["edited", 3.44]]},
   "labels": {"top": "A &middot; Edited by Claude", "bottom": "B &middot; Raw", "bottom_note": "dead space cut only", "pulse": 4.0},
   "captions": [["First, give me captions.", 8.10, 8.84, []], ["the key words pop.", 10.08, 11.97, [[3, 11.18]]], ...],
   "edits": [{"op": "captions", "t": 8.10, "word": 12, "label": "Captions"}, ...],
   "end_card": {"text": "Raw <i>vs</i> Claude", "t": 45.02}}
Edit ops (t = start of the word that names the edit; `label` = its row in the edit log, omit to keep it off the log;
`updates: "<op>"` rewrites that op's row instead of adding one):
  captions | keywords | caption_font {font: serif|mono|grotesk} | grade {look: warm|cool|bw|punchy|none, strength}
  title_behind {words: [[w, t], ...], italic_from, out} | edit_log {show, out} | sfx_on_change | punch_in {scale} | punch_out
  music_in | music_level {db} | bg_blur {px} | text_pop {text, out} | lower_third {name, role, out} | custom {js}
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import ROOT, encoder_args, hwaccel_args, strip_hw  # noqa: E402

TEMPLATE = os.path.join(ROOT, "templates", "versus")
OPS = {"captions", "keywords", "caption_font", "grade", "title_behind", "edit_log", "sfx_on_change", "punch_in", "punch_out",
       "music_in", "music_level", "bg_blur", "text_pop", "lower_third", "custom"}
NEEDS_CUTOUT = {"title_behind", "bg_blur"}
# one sound per edit once the speaker asks for sound, rotated so no two in a row repeat: (file, dur, volume, fade-out)
SFX = [("click-soft.mp3", .37, .32, None), ("whoosh-short.mp3", .57, .2, None), ("whoosh.mp3", .57, .14, .3),
       ("click.mp3", .35, .22, None), ("key-press.mp3", .3, .3, None), ("sparkle.mp3", 1.2, .08, .4), ("pop.mp3", .72, .3, None)]
FINAL_SFX = ("chime.mp3", .8, .1, .4)


def V(vid, *p):
    return os.path.join(ROOT, "work", vid, "versus", *p)


def run(cmd, **kw):
    print(" ".join(str(c) for c in cmd), file=sys.stderr)
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def dur(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                capture_output=True, text=True, check=True).stdout.strip())


def load_edits(vid):
    p = V(vid, "edits.json")
    if not os.path.exists(p):
        sys.exit(f"{p} missing: run `python tools/versus.py prep {vid}` first")
    return json.load(open(p, encoding="utf-8"))


def save_edits(vid, E):
    json.dump(E, open(V(vid, "edits.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def words_of(vid):
    return json.load(open(V(vid, "words.json"), encoding="utf-8"))


# ------------------------------------------------------------------------------------------------------------- prep
def prep(a):
    vid = a.id
    W = os.path.join(ROOT, "work", vid)
    cut = a.cut or os.path.join(W, "raw", "cut.mp4")
    if not os.path.exists(cut):
        sys.exit(f"{cut} missing: tight-cut the take first (tools/rawcut.py session / transcribe / cut / verify / render)")
    A = V(vid, "assets"); os.makedirs(A, exist_ok=True)
    cam = os.path.join(A, "cam_1080.mp4")
    if not os.path.exists(cam):
        cmd = ["ffmpeg", "-v", "error", "-y", *hwaccel_args(), "-i", cut, "-an", "-vf",
               "fps=30,scale=1920:1080:flags=lanczos,format=yuv420p", *encoder_args("final"), "-g", "30", "-movflags", "+faststart", cam]
        if subprocess.run(cmd).returncode:
            run(strip_hw(cmd))
    run(["ffmpeg", "-v", "error", "-y", "-i", cam, "-vf", "scale=1080:608:flags=lanczos", "-c:v", "libx264", "-crf", "17",
         "-preset", "medium", "-g", "30", "-pix_fmt", "yuv420p", "-movflags", "+faststart", os.path.join(A, "cam_raw.mp4")])
    run(["ffmpeg", "-v", "error", "-y", "-i", cut, "-vn", "-c:a", "aac", "-b:a", "192k", os.path.join(A, "voice.m4a")])
    for sub in ("fonts", "vendor", "sfx"):
        src = os.path.join(ROOT, "assets", sub)
        if not os.path.isdir(src):
            sys.exit(f"assets/{sub} missing: run `python setup.py`")
        shutil.copytree(src, os.path.join(A, sub), dirs_exist_ok=True)
    # words on the CUT clock: rawcut's verified cut_words.json when the cut came from rawcut, else a fresh transcript
    words = V(vid, "words.json")
    cw = os.path.join(os.path.dirname(cut), "cut_words.json")
    if not a.cut and os.path.exists(cw):
        ws = [{"i": k, "text": t, "start": round(s, 3), "end": round(e, 3)} for k, (t, s, e, *_) in enumerate(json.load(open(cw, encoding="utf-8")))]
        json.dump(ws, open(words, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    elif not os.path.exists(words):
        wav = V(vid, "audio16k.wav")
        run(["ffmpeg", "-v", "error", "-y", "-i", cut, "-vn", "-ac", "1", "-ar", "16000", wav])
        from prep_source import GLOSSARY
        run([sys.executable, os.path.join(HERE, "transcribe.py"), wav, V(vid, "transcript.json"), "large-v3", GLOSSARY])
        run([sys.executable, os.path.join(HERE, "make_words.py"), V(vid, "transcript.json"), words])
    ws = json.load(open(words, encoding="utf-8"))
    with open(V(vid, "words.txt"), "w", encoding="utf-8") as f:
        for w in ws:
            f.write(f"{w['i']:4d} {w['start']:7.2f} {w['end']:7.2f}  {w['text']}\n")
    fg = os.path.join(A, "cam_fg.webm")
    if not a.no_matte and not os.path.exists(fg):
        r = subprocess.run([sys.executable, os.path.join(HERE, "matte.py"), cam, fg])
        if r.returncode:
            print("WARNING: cut-out failed - title_behind and bg_blur will be unavailable", file=sys.stderr)
    D = round(dur(cam), 3)
    if not os.path.exists(V(vid, "edits.json")):
        E = {"duration": D, "speech_end": round(min(D, ws[-1]["end"] - 0.25), 2) if ws else D,
             "header": {"line1": [], "line2": []},
             "labels": {"top": "A &middot; Edited by Claude", "bottom": "B &middot; Raw", "bottom_note": "dead space cut only"},
             "captions": chunk(ws, D), "edits": [], "end_card": {"text": "Raw <i>vs</i> Claude", "t": None}}
        save_edits(vid, E)
    print(f"prepped {V(vid)} ({D:.2f}s, {len(ws)} words, cut-out {'yes' if os.path.exists(fg) else 'NO'}).\n"
          f"Next: read {V(vid, 'words.txt')}, write the edit list + header in {V(vid, 'edits.json')}, then music / build / render.")


def chunk(ws, D, max_words=5, max_secs=1.9, gap=0.5):
    """Caption chunks [text, on, off, []]: break after punctuation, at 5 words, 1.9 s or a pause; off = next chunk's on."""
    out, cur = [], []
    for k, w in enumerate(ws):
        if cur and (re.search(r"[.,?!;:]$", cur[-1]["text"]) and len(cur) >= 2 or len(cur) >= max_words
                    or w["end"] - cur[0]["start"] > max_secs or w["start"] - cur[-1]["end"] > gap):
            out.append(cur); cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    res = []
    for k, c in enumerate(out):
        off = out[k + 1][0]["start"] if k + 1 < len(out) else min(D, c[-1]["end"] + .3)
        res.append([" ".join(w["text"] for w in c), round(c[0]["start"], 2), round(off, 2), []])
    return res


def chunks(a):
    E = load_edits(a.id)
    E["captions"] = chunk(words_of(a.id), E["duration"])
    save_edits(a.id, E)
    print(f"{len(E['captions'])} caption chunks written; add key words as [word_index_in_chunk, time] pairs")


# ------------------------------------------------------------------------------------------------------------ music
def music(a):
    E = load_edits(a.id)
    mi = next((e for e in E["edits"] if e["op"] == "music_in"), None)
    if not mi:
        sys.exit("no music_in edit in edits.json - nothing to do")
    import numpy as np
    from versus_music import synth
    start = max(0.0, mi["t"] - .07)
    secs = round(E["duration"] - start, 3)
    L, R = synth(secs, a.bpm, a.seed)
    sr = 48000
    gain = np.full(len(L), 1.0)
    for e in sorted((e for e in E["edits"] if e["op"] == "music_level"), key=lambda e: e["t"]):
        k = int(max(0.0, e["t"] - start) * sr); ramp = int(.5 * sr)
        g = 10 ** (e.get("db", -5) / 20)
        cur = gain[k - 1] if k > 0 else 1.0
        gain[k:k + ramp] = np.linspace(cur, cur * g, len(gain[k:k + ramp]))
        gain[k + ramp:] = cur * g
    L, R = L * gain, R * gain
    pcm = (np.clip(np.stack([L, R], 1), -1, 1) * 32767).astype(np.int16)
    out = V(a.id, "assets", "music.wav")
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())
    E["music"] = {"start": round(start, 3), "duration": secs}
    save_edits(a.id, E)
    print(f"wrote {out}: {secs:.1f}s from {start:.2f}s")


# ------------------------------------------------------------------------------------------------------------ build
def validate(E, ws, has_cutout):
    errs, warns = [], []
    D = E["duration"]
    for k, e in enumerate(E["edits"]):
        if e.get("op") not in OPS:
            errs.append(f"edit {k}: unknown op {e.get('op')!r} (use custom with js for anything else)")
            continue
        if not isinstance(e.get("t"), (int, float)) or not 0 <= e["t"] <= D:
            errs.append(f"edit {k} ({e['op']}): t {e.get('t')} outside 0..{D}")
            continue
        if "word" in e and 0 <= e["word"] < len(ws) and abs(ws[e["word"]]["start"] - e["t"]) > .15:
            warns.append(f"edit {k} ({e['op']}): t {e['t']} is {ws[e['word']]['start'] - e['t']:+.2f}s off word {e['word']} "
                         f"'{ws[e['word']]['text']}'")
        if e["op"] in NEEDS_CUTOUT and not has_cutout:
            errs.append(f"edit {k} ({e['op']}) needs the cut-out (assets/cam_fg.webm): run prep without --no-matte")
        if e.get("updates") and not any(x["op"] == e["updates"] and x["t"] <= e["t"] for x in E["edits"]):
            errs.append(f"edit {k} ({e['op']}): updates {e['updates']!r} but no earlier edit has that op")
    if any(e["op"] == "music_in" for e in E["edits"]) and not E.get("music"):
        errs.append("music_in edit but no music bed: run `python tools/versus.py music <id>`")
    for k, c in enumerate(E.get("captions", [])):
        if c[1] >= c[2]:
            errs.append(f"caption {k}: on {c[1]} >= off {c[2]}")
        for i, t in c[3]:
            if i >= len(c[0].split(" ")):
                errs.append(f"caption {k}: key word index {i} past the end of '{c[0]}'")
    if not E["header"]["line1"]:
        warns.append("header.line1 is empty")
    return errs, warns


def build(a):
    vid = a.id
    E = load_edits(vid)
    ws = words_of(vid)
    has_cutout = os.path.exists(V(vid, "assets", "cam_fg.webm"))
    errs, warns = validate(E, ws, has_cutout)
    for w in warns:
        print("warn:", w)
    if errs:
        sys.exit("edits.json has problems:\n  " + "\n  ".join(errs))
    E["has_cutout"] = has_cutout
    D = E["duration"]
    # sound on change: one cue per edit from the moment the speaker asks for sound, never the same twice in a row
    cues = []
    son = next((e for e in E["edits"] if e["op"] == "sfx_on_change"), None)
    if son:
        k = 0
        for e in sorted(E["edits"], key=lambda e: e["t"]):
            if e["t"] >= son["t"] and e["op"] not in ("custom",) and (e.get("label") or e["op"] == "sfx_on_change"):
                f, d, v, fo = SFX[k % len(SFX)]; k += 1
                cues.append({"file": f, "t": round(e["t"], 3), "dur": d, "vol": v, "fade": fo})
        if E.get("end_card", {}).get("t") is not None and ws:
            f, d, v, fo = FINAL_SFX
            cues.append({"file": f, "t": round(min(ws[-1]["start"] - .1, D - d - .02), 3), "dur": d, "vol": v, "fade": fo})
    E["sfx"] = cues
    if E.get("end_card") and E["end_card"].get("t") is None:
        E["end_card"] = None
    audio = []
    if E.get("music"):
        audio.append(f'      <audio id="music" class="clip" src="assets/music.wav" data-start="{E["music"]["start"]:.3f}" '
                     f'data-duration="{E["music"]["duration"]:.3f}" data-track-index="10" data-volume="1"></audio>')
    for i, c in enumerate(cues):
        audio.append(f'      <audio id="sfx-{i + 1}" class="clip" src="assets/sfx/{c["file"]}" data-start="{c["t"]:.3f}" '
                     f'data-duration="{c["dur"]}" data-track-index="11" data-volume="{c["vol"]}"'
                     + (f' data-fade-out="{c["fade"]}"' if c["fade"] else "") + "></audio>")
    fg = (f'<div id="fgw"><video id="vfg" class="camv clip" src="assets/cam_fg.webm" muted playsinline data-start="0" '
          f'data-duration="{D}" data-track-index="1"></video></div>') if has_cutout else ""
    html = open(os.path.join(TEMPLATE, "index.html"), encoding="utf-8").read()
    html = html.replace("{{DURATION}}", str(D)).replace("{{FOREGROUND}}", fg).replace("{{AUDIO}}", "\n".join(audio))
    open(V(vid, "index.html"), "w", encoding="utf-8").write(html)
    with open(V(vid, "edits.js"), "w", encoding="utf-8") as f:
        f.write("window.EDITS = " + json.dumps(E, ensure_ascii=False, indent=1) + ";\n")
    for name in ("hyperframes.json", "package.json"):
        shutil.copy2(os.path.join(TEMPLATE, name), V(vid, name))
    print(f"built {V(vid, 'index.html')}: {len(E['edits'])} edits, {len(E.get('captions', []))} caption chunks, "
          f"{len(cues)} sound cues, music {'yes' if E.get('music') else 'no'}, cut-out {'yes' if has_cutout else 'no'}")
    r = subprocess.run("npx hyperframes lint", cwd=V(vid), shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print((r.stdout + r.stderr).strip()[-1500:])


def render(a):
    out = f"{a.id}_versus"
    r = subprocess.run([sys.executable, os.path.join(HERE, "render.py"), "one", V(a.id), out,
                        "--quality", "draft" if a.draft else "looks"])
    sys.exit(r.returncode)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prep"); p.add_argument("id"); p.add_argument("--cut"); p.add_argument("--no-matte", action="store_true")
    p = sub.add_parser("chunks"); p.add_argument("id")
    p = sub.add_parser("music"); p.add_argument("id"); p.add_argument("--bpm", type=float, default=84); p.add_argument("--seed", type=int, default=7)
    p = sub.add_parser("build"); p.add_argument("id")
    p = sub.add_parser("render"); p.add_argument("id"); p.add_argument("--draft", action="store_true")
    a = ap.parse_args()
    {"prep": prep, "chunks": chunks, "music": music, "build": build, "render": render}[a.cmd](a)


if __name__ == "__main__":
    main()
