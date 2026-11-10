"""Reference breakdown, layers 1 and 2 of references/HOW.md: the measured facts of a reel, and the stills around every change.

  python tools/reference.py measure <folder> [--video <file>] [--label <name>] [--no-sound]

<folder> is references/<slug>/, whose video is clip.mp4, or any folder given --video. Writes into the folder:
  words.json      word-timed transcript (tools/transcribe.py), kept if already there
  measure.json    the numbers
  measure.md      the same in plain words, next to our own numbers from references/_baseline/ when they exist
  changes-N.jpg   every visual change as a strip: before, then consecutive native frames until it settles, with the words around it
  frames.jpg      1 fps contact sheet (row = 10 s), kept if already there
Sound separates voice from everything else with Demucs (_ext/demucs-lib, model in the Hugging Face cache) on the GPU, through
the matte venv's torch. Hard cuts and the look come from HyperFrames' measure tools (`measure cuts`, `measure look`), pinned
to the version they were checked at (HF below). Nothing leaves this machine.

What it cannot see: text content, fonts, what a graphic shows, why. Those come from looking at the stills (layer 2) and from
Chase's notes. The layout split is a face finder's guess and the halves are a straight cut at mid-frame, so both are rough.
"""
import argparse, json, math, os, shutil, subprocess, sys, tempfile, types
from datetime import date
from pathlib import Path
import numpy as np

from paths import project_root
ROOT = project_root()
MATTE_PY = sys.executable
DEMUCS_LIB = ROOT / "_ext" / "demucs-lib"
BASELINE = ROOT / "references" / "_baseline"
SCAN_FPS, SCAN_W = 15, 144  # change scan: small grey frames, 67 ms apart
FACE_FPS, FACE_W = 2, 540
FLOOR, RATIO = 2.5, 3.0  # a change: mean pixel difference over FLOOR and RATIO x the median of the second around it
NEAR = 0.1  # a change "on a word" starts within this many seconds of a word onset. Fast speech has an onset every ~0.3 s,
# so the share only means something next to its chance level
SR = 44100
# HyperFrames' measure tools, checked 2026-11-04 on a reel we already knew. Pinned apart from the project's render engine
# (package.json), so the breakdown can move to a newer CLI without touching renders. Bump it only after re-checking.
HF = [shutil.which("npx") or "npx", "-y", "hyperframes@0.9.13", "measure"]
STRIP = 10  # most consecutive frames per change on a sheet; longer moves are evenly thinned


def run(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], check=True, capture_output=True, **kw)


def probe(video):
    j = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration",
                        "-of", "json", video], text=True).stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    n, d = v["r_frame_rate"].split("/")
    return {"width": v["width"], "height": v["height"], "fps": round(int(n) / int(d), 2), "duration": round(float(j["format"]["duration"]), 2),
            "audio": any(s["codec_type"] == "audio" for s in j["streams"])}


def frames(video, fps, w, info, gray=True):
    h = int(round(w * info["height"] / info["width"] / 2)) * 2
    fmt, c = ("gray", 1) if gray else ("rgb24", 3)
    a = np.frombuffer(run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={fps},scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", fmt, "-"]).stdout, np.uint8)
    return a.reshape(-1, h, w) if gray else a.reshape(-1, h, w, 3)


# ------------------------------------------------------------------------------------------------------------- picture
def changes(g):
    """Visual changes per half: runs of frame-to-frame difference well above the level of the second around them. A run is one
    change, so a card that animates in over 0.4 s counts once. The same moment in both halves is one whole-frame change."""
    f = g.astype(np.int16); h = f.shape[1] // 2
    found = []
    for region, part in (("top", f[:, :h]), ("bottom", f[:, h:])):
        x = np.abs(np.diff(part, axis=0)).mean((1, 2))
        pad = np.pad(x, SCAN_FPS, mode="edge")
        local = np.array([np.median(pad[i:i + 2 * SCAN_FPS + 1]) for i in range(len(x))])
        hit = x > np.maximum(FLOOR, RATIO * local)
        i = 0
        while i < len(x):
            if not hit[i]:
                i += 1; continue
            j = i
            while j + 1 < len(x) and (hit[j + 1] or (j + 2 < len(x) and hit[j + 2])):  # one quiet frame inside a move is still the move
                j += 1
            found.append({"t": round((i + 1) / SCAN_FPS, 2), "region": region, "dur": round((j - i + 1) / SCAN_FPS, 2),
                          "size": round(float(x[i:j + 1].max()), 1), "span": [i, j]})
            i = j + 1
    found.sort(key=lambda c: c["t"]); out = []
    for c in found:
        if out and abs(c["t"] - out[-1]["t"]) <= 2 / SCAN_FPS and c["region"] != out[-1]["region"]:
            o = out[-1]; o["region"] = "whole"; o["dur"] = max(o["dur"], c["dur"]); o["size"] = max(o["size"], c["size"])
            o["span"] = [min(o["span"][0], c["span"][0]), max(o["span"][1], c["span"][1])]
        else:
            out.append(c)
    H = f.shape[1]
    # Hard edges only: text and card edges swing by 60+ grey levels when they change, skin and shirt in live video mostly less.
    moving = np.abs(np.diff(f, axis=0)) > 60
    live = moving.mean(0) > 0.1  # pixels that swing a tenth of the time are live video, not a designed change
    for c in out:
        c["kind"] = "cut" if c["dur"] <= 1 / SCAN_FPS else "animated"
        i, j = c.pop("span")
        mask = moving[i:j + 1].any(0) & ~live  # every still pixel the change touched, start to settle
        rows = np.flatnonzero(mask.any(1))
        c["area"] = round(float(mask.mean()), 3)
        c["rows"] = [round(rows[0] / H, 2), round((rows[-1] + 1) / H, 2)] if len(rows) else [0.5, 0.5]
    bands = captions(out)
    # Most swaps are too small to show in a half's average, so count them inside their own band.
    swaps = set()
    for b in bands:
        r0, r1 = int((b - 0.03) * H), int((b + 0.03) * H) + 1
        x = (moving[:, r0:r1] & ~live[r0:r1]).mean((1, 2))
        hit = np.flatnonzero((x > 0.02) & (x >= np.roll(x, 1)) & (x > np.roll(x, -1)))
        swaps |= {round((i + 1) / SCAN_FPS, 1) for i in hit}
    return out, {"bands": bands, "swaps": sorted(swaps)}


def captions(ch):
    """Burned-in captions swap every few words in a small band, so they would swamp the count. Small changes in a band that
    repeats at least six times become kind "caption", counted apart from the visual changes. A reel can have more than one band
    (ivory moves its chip lower on full-frame beats), so bands are taken until none is left."""
    bands = []
    while True:
        small = [c for c in ch if c["kind"] != "caption" and c["area"] < 0.04 and c["rows"][1] - c["rows"][0] < 0.1]
        if len(small) < 6:
            return bands
        mids = np.array([(c["rows"][0] + c["rows"][1]) / 2 for c in small])
        best = max(np.arange(0, 1, 0.01), key=lambda y: (np.abs(mids - y) <= 0.04).sum())
        band = [c for c, m in zip(small, mids) if abs(m - best) <= 0.04]
        if len(band) < 6:
            return bands
        for c in band:
            c["kind"] = "caption"
        bands.append(round(float(best), 2))


def layout(g):
    """Where his face is, twice a second (OpenCV Haar, rough): bottom half = split with the face below, top = split with the face
    above, full = a full-screen face, none = graphics only (or a face the finder missed: caps and profiles)."""
    import cv2
    det = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
    H = g.shape[1]; labels = []
    for fr in g:
        f = det.detectMultiScale(fr, 1.1, 6, minSize=(36, 36))
        if not len(f):
            labels.append("none"); continue
        x, y, w, h = max(f, key=lambda b: b[2] * b[3])
        labels.append("bottom" if y + h / 2 > 0.55 * H else "full" if h >= 0.14 * H else "top")
    sm = [max(set(labels[max(0, i - 1):i + 2]), key=labels[max(0, i - 1):i + 2].count) for i in range(len(labels))]  # drop one-sample blips
    segs = []
    for i, lab in enumerate(sm):
        if segs and segs[-1]["face"] == lab:
            segs[-1]["to"] = round((i + 1) / FACE_FPS, 1)
        else:
            segs.append({"face": lab, "from": round(i / FACE_FPS, 1), "to": round((i + 1) / FACE_FPS, 1)})
    share = {k: round(sm.count(k) / len(sm), 3) for k in ("bottom", "top", "full", "none") if k in sm}
    return share, segs


def palette(rgb, n=8):
    px = rgb.reshape(-1, 3); q = px // 32; keys = q[:, 0].astype(int) * 64 + q[:, 1] * 8 + q[:, 2]
    count = np.bincount(keys, minlength=512); out = []
    for k in np.argsort(count)[::-1][:n]:
        if count[k]:
            m = px[keys == k].mean(0)
            out.append({"hex": "#%02x%02x%02x" % tuple(int(v) for v in m), "share": round(float(count[k] / count.sum()), 3)})
    return out


def hf(op, video, *args):
    """One HyperFrames measure command as JSON, or None (with a note) when the CLI can't run, so a breakdown still finishes offline."""
    try:
        j = json.loads(run([*HF, op, video, *args], text=True, encoding="utf8", cwd=ROOT).stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError) as e:
        print(f"  hyperframes measure {op} failed, skipping it: {getattr(e, 'stderr', '') or e}"[:300], flush=True)
        return None
    return j if j.get("ok") else None


def hard_cuts(video, ch):
    """Frame-exact hard cuts (measure cuts), which also catch jump cuts and punch-ins inside one take. A change within 0.15 s of
    one is a cut, any other an animation: our 15 fps scan can't tell a one-frame switch from a fast move on its own. Each cut
    goes to its nearest change only, since a cut can show up in both halves a frame apart. Cuts no change matched are kept apart."""
    j = hf("cuts", video)
    if j is None:
        return None
    for c in ch:
        c["kind"] = "animated"
    for k in j["cuts"]:
        near = [c for c in ch if abs(k["t"] - c["t"]) <= 0.15 and "cut_frame" not in c]
        if near:
            c = min(near, key=lambda c: abs(k["t"] - c["t"])); c["kind"] = "cut"; c["cut_frame"] = k["frame"]
    matched = {c["cut_frame"] for c in ch if "cut_frame" in c}
    return {"count": len(j["cuts"]), "frames": [k["frame"] for k in j["cuts"]],
            "unmatched": [k for k in j["cuts"] if k["frame"] not in matched], "shots": len(j["shots"])}


def look(video, info):
    """Brightness, contrast, saturation and warmth (measure look), for the whole frame and the top half."""
    out = {}
    for name, roi in (("whole", None), ("top_half", f"0,0,{info['width']},{info['height'] // 2}")):
        j = hf("look", video, *(["--roi", roi] if roi else []))
        if j:
            out[name] = {k: j[k] for k in ("luma", "contrast", "saturation", "bw_share", "warmth")}
    return out or None


def holds(times, dur):
    gaps = np.diff([0.0, *times, dur])
    if not len(times):
        return {"count": 0, "per_10s": 0, "median_hold": dur, "longest_still": round(dur, 1)}
    return {"count": len(times), "per_10s": round(len(times) / dur * 10, 1), "median_hold": round(float(np.median(gaps)), 2),
            "hold_middle_half": [round(float(v), 2) for v in np.percentile(gaps, [25, 75])], "longest_still": round(float(gaps.max()), 1)}


# ------------------------------------------------------------------------------------------------------------- words
def words_of(folder, video):
    p = folder / "words.json"
    if not p.exists():
        run([sys.executable, ROOT / "tools" / "transcribe.py", video, p])
    j = json.loads(p.read_text(encoding="utf8"))
    return [(w["start"], w["end"], w["word"]) for s in j["segments"] for w in s["words"]]


def said(words, t):
    """The words around t, with the word nearest t in brackets."""
    near = [w for w in words if t - 1.5 <= w[0] <= t + 0.8]
    if not near:
        return "", None, None
    k = min(near, key=lambda w: abs(w[0] - t))
    return " ".join(f"[{w[2]}]" if w is k else w[2] for w in near), k[2], round(t - k[0], 2)


def on_word_chance(words, dur, grid=0.05):
    """How often a random moment in the speech falls within NEAR of a word onset, so the on-word share has something to beat."""
    if not words:
        return None
    on = np.array([w[0] for w in words]); ts = np.arange(words[0][0], min(words[-1][1], dur), grid)
    return round(float((np.abs(ts[:, None] - on[None]).min(1) <= NEAR).mean()), 3)


# ------------------------------------------------------------------------------------------------------------- sound
def stems(video, out):
    """Runs under MATTE_PY. Voice and everything-else stems as .npy, 44.1 kHz stereo. Same model and options as the 2026-11-01
    sound study (reports/2026-11-01-sound-strategy/separate.py), so the numbers compare."""
    # Honor HF_HUB_OFFLINE from the user; allow the first model download.
    sys.path.insert(0, str(DEMUCS_LIB)); sys.modules.setdefault("torchaudio", types.ModuleType("torchaudio"))
    import torch
    old = torch.load
    torch.load = lambda *a, **k: old(*a, **{**k, "weights_only": False})
    from demucs.hf import get_hf_model
    from demucs.apply import apply_model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("WARN optional reference stems are slow on CPU; --no-sound skips them", file=sys.stderr)
    m = get_hf_model("htdemucs").to(device).eval()
    raw = run(["ffmpeg", "-v", "error", "-i", video, "-vn", "-ac", "2", "-ar", SR, "-f", "f32le", "-"]).stdout
    x = torch.from_numpy(np.frombuffer(raw, dtype="<f4").copy().reshape(-1, 2).T)[None]; ref = x.mean(1); mu, sd = ref.mean(), ref.std()
    torch.manual_seed(0)
    with torch.no_grad():
        y = apply_model(m, (x - mu) / sd, device=device, shifts=1, split=True, overlap=.25, progress=False)[0] * sd + mu
    y = y.cpu().numpy(); i = m.sources.index("vocals")
    np.save(Path(out) / "voice.npy", y[i].astype("float32")); np.save(Path(out) / "rest.npy", (y.sum(0) - y[i]).astype("float32"))


def db(x):
    return 20 * np.log10(x + 1e-9)


def rms(x, w):
    n = int(SR * w); k = len(x) // n
    return np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(1))


def lufs(x):
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-f", "f32le", "-ar", SR, "-ac", x.shape[0], "-i", "pipe:0", "-af", "ebur128=framelog=quiet",
             "-f", "null", "-"], input=x.T.astype("<f4").tobytes()).stderr.decode()
    import re
    v = re.findall(r"I:\s+(-?[\d.]+|-inf) LUFS", r)[-1]
    return None if v == "-inf" else float(v)


# dB over the previous 140 ms, dB under the voice at most, s between cues. Checked 2026-11-02 on the 1030-2 ivory final, whose
# 12 cues are known (work/1030-2/v2/editorial/sound.json): these settings find 5 and invent none. Looser ones find up to 12 but
# invent 40-100, because Demucs leaves voice in the other stem and folds quiet cues under the voice into the voice stem
# (7 of the 12 sat 30-45 dB down in the other stem). So the count is a floor: what it finds is real, quiet cues are missed.
CUE_JUMP, CUE_OVER, CUE_GAP = 10, 30, 0.25


def cues_in(vm, rm, jump=CUE_JUMP, over=CUE_OVER, gap=CUE_GAP):
    """Onsets in the everything-else stem: a jump over the 140 ms before it, loud enough against the voice (its 90th percentile
    in 20 ms windows)."""
    vv = db(rms(vm, .02)); vref = float(np.percentile(vv[vv > -60], 90)) if (vv > -60).any() else -60.0
    ev = rms(rm, .02); ed = db(ev); cues = []; last = -99
    for i in range(8, len(ed)):
        base = db(np.sqrt((ev[i - 8:i - 1] ** 2).mean()))
        if ed[i] - base >= jump and ed[i] > vref - over and (i - last) * .02 > gap:
            seg = rm[int(i * .02 * SR):int((i * .02 + .25) * SR)]
            if len(seg) < 2048:
                continue
            sp = abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2; fr = np.fft.rfftfreq(len(seg), 1 / SR)
            cues.append({"t": round(i * .02, 2), "under_voice_db": round(float(vref - db(np.sqrt((seg ** 2).mean()))), 1),
                         "centroid_hz": int((sp * fr).sum() / (sp.sum() + 1e-12))})
            last = i
    return vref, cues


def sound(video, folder):
    """Cue onsets in the everything-else stem, their level against the voice, and the bed under the voice. The stems are cached in
    <folder>/.cache/ (local, safe to delete). Separation under-reads quiet sounds, so a quiet reel may show fewer cues than it has."""
    cache = folder / ".cache" / "stems.npz"
    if not cache.exists():
        cache.parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            run([MATTE_PY, Path(__file__), "stems", video, tmp])
            np.savez(cache, voice=np.load(Path(tmp) / "voice.npy"), rest=np.load(Path(tmp) / "rest.npy"))
    z = np.load(cache); v, r = z["voice"], z["rest"]
    vm, rm = v.mean(0), r.mean(0)
    vref, cues = cues_in(vm, rm)
    lv, lr = lufs(v), lufs(r); w4 = db(rms(rm, .4))
    return {"cues": cues, "count": len(cues), "per_30s": round(len(cues) / (len(vm) / SR) * 30, 1),
            "median_under_voice_db": float(np.median([c["under_voice_db"] for c in cues])) if cues else None,
            "rest_LU_under_voice": round(lv - lr, 1) if lv is not None and lr is not None else None,
            "bed_floor_vs_voice_db": round(float(np.percentile(w4, 20) - vref), 1),
            "note": "bed floor: the quietest fifth of the everything-else stem against the voice. Near -60 means silence under the voice; "
                    "above about -35 means a music bed or room tone runs under it."}


# ------------------------------------------------------------------------------------------------------------- output
def strip_frames(c, fps, total):
    """The native frames a change's strip shows: from just before it starts (its cut frame, else up to 3 frames before the scan
    saw it, which runs at 15 fps) until 0.15 s after it settles, evenly thinned to STRIP with both ends kept."""
    f0 = c["cut_frame"] - 1 if "cut_frame" in c else round(c["t"] * fps) - 3
    f0 = max(0, f0); f1 = min(total - 1, max(f0 + 1, round((c["t"] + c["dur"] + 0.15) * fps)))
    n = f1 - f0 + 1
    return [f0 + int(i) for i in np.unique(np.linspace(0, n - 1, min(n, STRIP)).round())], n


def sheets(video, info, ch, folder):
    """One row per change: the frame a quarter second before, then consecutive native frames through the move, cropped to the
    rows it touched. How a thing arrives (slides from where, types on, pops, builds) and how many frames it takes is read here."""
    import cv2
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.truetype("arial.ttf", 13); small = ImageFont.truetype("arial.ttf", 11)
    except OSError:
        font = small = ImageFont.load_default()
    fw, band, tag, per = 150, 40, 14, 6
    W, H, fps = info["width"], info["height"], info["fps"]
    cap = cv2.VideoCapture(str(video)); total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or int(info["duration"] * fps)
    for old in folder.glob("changes-*.jpg"):
        old.unlink()

    def crop(b, c):
        r0 = max(0, int((c["rows"][0] - 0.03) * H)); r1 = min(H, int((c["rows"][1] + 0.03) * H))
        if r1 - r0 < H * 0.15:  # a thin band (a caption-sized change) keeps some context around it
            mid = (r0 + r1) // 2; r0, r1 = max(0, mid - int(H * 0.075)), min(H, mid + int(H * 0.075))
        return Image.fromarray(cv2.cvtColor(b[r0:r1], cv2.COLOR_BGR2RGB))

    for p in range(math.ceil(len(ch) / per)):
        rows = ch[p * per:(p + 1) * per]; cells = []
        for c in rows:
            cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, c["t"] - 0.25) * 1000); ok, b = cap.read()
            pics = [("before", crop(b, c) if ok else None)]
            want, n = strip_frames(c, fps, total)
            cap.set(cv2.CAP_PROP_POS_FRAMES, want[0]); f = want[0]
            for w in want:
                while f <= w:
                    ok, b = cap.read(); f += 1
                    if not ok:
                        break
                pics.append((f"f{w}", crop(b, c) if ok else None))
            fh = max((im.height * fw // im.width for _, im in pics if im), default=fw)
            cells.append((c, pics, fh, n))
        img = Image.new("RGB", (fw * (STRIP + 1), sum(band + tag + fh for _, _, fh, _ in cells)), "white"); d = ImageDraw.Draw(img); y = 0
        for r, (c, pics, fh, n) in enumerate(cells):
            thin = f", every {n / (len(pics) - 1):.1f} frames" if n > len(pics) - 1 else ""
            d.text((4, y + 3), f"#{p * per + r + 1}  {c['t']:.2f} s  {c['region']}  {c['kind']}" + ("  + sound" if c.get("sound") else "")
                   + f"   {n} frames to settle{thin}", font=font, fill="black")
            d.text((4, y + 21), c["said"][:120], font=font, fill="#555")
            for col, (label, im) in enumerate(pics):
                d.text((fw * col + 3, y + band), label, font=small, fill="#a33" if label == "before" else "#333")
                if im:
                    img.paste(im.resize((fw, im.height * fw // im.width)), (fw * col, y + band + tag))
            y += band + tag + fh
        img.save(folder / f"changes-{p + 1}.jpg", quality=84)
    cap.release()
    return math.ceil(len(ch) / per)


def contact(video, info, folder):
    if not (folder / "frames.jpg").exists():
        run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", f"fps=1,scale=108:-2,tile=10x{math.ceil(info['duration'] / 10)}",
             "-frames:v", "1", folder / "frames.jpg"])


def pct(x):
    return "n/a" if x is None else f"{round(x * 100)}%"


def summary(m):
    """The rows of the comparison table, as plain words."""
    p, s = m["picture"], m.get("sound")
    by = p["by_region"]; lay = m["layout"]["share"]
    rows = {
        "Length": f"{m['info']['duration']:.0f} s",
        "Visual changes": f"{p['all']['count']} ({p['all']['per_10s']} per 10 s)",
        "...in the top half / bottom / whole frame": f"{by.get('top', 0)} / {by.get('bottom', 0)} / {by.get('whole', 0)}",
        "...hard cuts / animated": f"{p['kinds'].get('cut', 0)} / {p['kinds'].get('animated', 0)}" if p.get("cuts") else "not measured",
        "Hard cuts, frame-exact (incl. jump cuts)": "not measured" if not p.get("cuts") else
            f"{p['cuts']['count']}, {p['cuts']['shots']} shots" + (f"; {len(p['cuts']['unmatched'])} the change scan missed" if p["cuts"]["unmatched"] else ""),
        "Median hold between changes": f"{p['all']['median_hold']} s",
        "Longest stretch with no change": f"{p['all']['longest_still']} s",
        "First change / changes in the first 3 s": f"{p['first_change']} s / {p['first_3s']}",
        "Changes that land on a word onset": f"{pct(p['on_word'])} (chance {pct(p['on_word_chance'])})",
        "Burned-in captions": "none found" if not m["captions"]["count"] else
            f"{m['captions']['count']} swaps, about {m['captions']['words_each']} words each, centred at "
            + " and ".join(f"{round(b * 100)}%" for b in m["captions"]["bands"]) + " of the height",
        "Face (rough)": ", ".join(f"{k} {round(v * 100)}%" for k, v in lay.items()),
        "Top colours": " ".join(c["hex"] for c in m["colours"]["top_half"][:5]),
    }
    lk = (m.get("look") or {}).get("top_half")
    rows["Look, top half (luma / contrast / saturation / warmth)"] = "not measured" if not lk else \
        f"{lk['luma']:.0f} / {lk['contrast']:.0f} / {lk['saturation']:.2f} / {lk['warmth']:+.0f}"
    if s:
        rows.update({
            "Sound cues (at least)": f"{s['count']} ({s['per_30s']} per 30 s)",
            "...median level": "n/a" if s["median_under_voice_db"] is None else f"{s['median_under_voice_db']} dB under the voice",
            "...on a visual change": pct(s.get("on_change")),
            "Effects and music against the voice": "n/a" if s["rest_LU_under_voice"] is None else f"{s['rest_LU_under_voice']} LU under",
            "Bed under the voice": f"{s['bed_floor_vs_voice_db']} dB",
        })
    return rows


def write_md(folder, m):
    base = sorted(BASELINE.glob("*/measure.json")) if folder.parent != BASELINE else []
    others = [json.loads(b.read_text(encoding="utf8")) for b in base]
    mine = summary(m); cols = [summary(o) for o in others]
    L = [f"# Measured: {m['label']}", "",
         f"_tools/reference.py, {m['made']}. Layer 1 of references/HOW.md: numbers, not taste. The face split and the halves are rough._", "",
         "| | " + " | ".join([m["label"], *[o["label"] for o in others]]) + " |", "|---|" + "---|" * (1 + len(others))]
    for k, v in mine.items():
        L.append(f"| {k} | {v} | " + " | ".join(c.get(k, "") for c in cols) + (" |" if cols else ""))
    L += ["", "## Face over time (rough)", "", ", ".join(f"{s['from']:.0f}-{s['to']:.0f} s {s['face']}" for s in m["layout"]["segments"]), "",
          "## Every change", "", "Stills: `changes-N.jpg`, six to a page. The word in brackets is the nearest word onset; offset is change minus onset.", "",
          "| # | t (s) | where | kind | sound | offset | words |", "|---|---|---|---|---|---|---|"]
    for i, c in enumerate(m["picture"]["changes"], 1):
        L.append(f"| {i} | {c['t']:.2f} | {c['region']} | {c['kind']} | {'yes' if c.get('sound') else ''} | "
                 f"{'' if c['word_offset'] is None else c['word_offset']} | {c['said']} |")
    missed = (m["picture"].get("cuts") or {}).get("unmatched")
    if missed:
        L += ["", "## Hard cuts the change scan missed", "", "Often a jump cut or punch-in on the face. Look at them with "
              "`npx hyperframes@0.9.13 measure frames <clip> --range a,b`.", "",
              ", ".join(f"{k['t']:.2f} s (frame {k['frame']})" for k in missed)]
    if m.get("sound"):
        loose = [c for c in m["sound"]["cues"] if not c.get("change")]
        if loose:
            L += ["", "## Sounds with no visual change", "", ", ".join(f"{c['t']:.2f} s ({c['under_voice_db']} dB under)" for c in loose)]
    (folder / "measure.md").write_text("\n".join(L) + "\n", encoding="utf8")


def measure(folder, video, label, with_sound):
    info = probe(video)
    print("scanning picture", flush=True)
    g = frames(video, SCAN_FPS, SCAN_W, info)
    ch, capinfo = changes(g)
    share, segs = layout(frames(video, FACE_FPS, FACE_W, info))
    rgb = frames(video, 1, 108, info, gray=False)
    print("words", flush=True)
    words = words_of(folder, video)
    caps = [c for c in ch if c["kind"] == "caption"]; ch = [c for c in ch if c["kind"] != "caption"]
    for c in ch:
        c["said"], c["word"], c["word_offset"] = said(words, c["t"])
    print("hard cuts and look (hyperframes measure)", flush=True)
    cuts = hard_cuts(video, ch)
    m = {"label": label, "made": str(date.today()), "video": str(video), "info": info, "layout": {"share": share, "segments": segs},
         "colours": {"whole": palette(rgb), "top_half": palette(rgb[:, :rgb.shape[1] // 2])},
         "captions": {"count": len(capinfo["swaps"]), "per_10s": round(len(capinfo["swaps"]) / info["duration"] * 10, 1),
                      "bands": capinfo["bands"], "words_each": round(len(words) / len(capinfo["swaps"]), 1) if capinfo["swaps"] else None,
                      "times": capinfo["swaps"], "note": "swaps counted in the band; a reel whose captions change one word at a "
                                                        "time can under-count when the swaps run together"}}
    times = [c["t"] for c in ch]
    offs = [c["word_offset"] for c in ch if c["word_offset"] is not None]
    m["picture"] = {
        "changes": ch, "all": holds(times, info["duration"]),
        "top": holds([c["t"] for c in ch if c["region"] in ("top", "whole")], info["duration"]),
        "by_region": {k: sum(c["region"] == k for c in ch) for k in ("top", "bottom", "whole")},
        "kinds": {k: sum(c["kind"] == k for c in ch) for k in ("cut", "animated")},
        "cuts": cuts,
        "first_change": times[0] if times else None, "first_3s": sum(t < 3 for t in times),
        "on_word": round(sum(abs(o) <= NEAR for o in offs) / len(ch), 3) if ch else None,
        "on_word_chance": on_word_chance(words, info["duration"]),
        "scan": f"{SCAN_FPS} fps at {SCAN_W} px wide; change = mean difference > {FLOOR} and > {RATIO}x the local median"}
    m["look"] = look(video, info)
    if with_sound and info["audio"]:
        print("separating sound", flush=True)
        s = sound(video, folder)
        for cue in s["cues"]:
            hit = [c for c in ch if abs(c["t"] - cue["t"]) <= 0.15]
            cue["change"] = bool(hit)
            for c in hit:
                c["sound"] = True
        s["on_change"] = round(sum(c["change"] for c in s["cues"]) / len(s["cues"]), 3) if s["cues"] else None
        m["sound"] = s
    (folder / "measure.json").write_text(json.dumps(m, indent=1, ensure_ascii=False), encoding="utf8")
    pages = sheets(video, info, ch, folder)
    contact(video, info, folder)
    write_md(folder, m)
    print(f"{len(ch)} changes, {pages} sheet pages, {m.get('sound', {}).get('count', 'no')} sound cues -> {folder / 'measure.md'}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "stems":
        return stems(sys.argv[2], sys.argv[3])
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    mp = sub.add_parser("measure")
    mp.add_argument("folder", type=Path)
    mp.add_argument("--video", type=Path)
    mp.add_argument("--label")
    mp.add_argument("--no-sound", action="store_true")
    a = ap.parse_args()
    folder = a.folder.resolve(); folder.mkdir(parents=True, exist_ok=True)
    video = (a.video or folder / "clip.mp4").resolve()
    if not video.exists():
        sys.exit(f"no video: {video}")
    measure(folder, video, a.label or folder.name, not a.no_sound)


if __name__ == "__main__":
    main()
