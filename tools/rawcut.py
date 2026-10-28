"""Raw OBS takes -> one tight, verified split-screen cut that claude-edit can take as its source.

Usage (all files land in <raw_dir>, e.g. work/<id>/raw):
  python rawcut.py session    <raw_dir> <take1.mkv> <take2.mkv> ...   # stitch takes into one session timeline + audio
  python rawcut.py transcribe <raw_dir> [--model large-v3-turbo]      # words.json, words.txt, script + hints to choose takes
  (write <raw_dir>/drops.json yourself: {"words": [[i, j], ...], "secs": [[a, b], ...]})
  python rawcut.py cut        <raw_dir> [--gap 0.12] [--pad-out 0.13] [--pad-in 0.08] [--min-cut 0.3]
  python rawcut.py verify     <raw_dir>                              # re-transcribes the edited audio and diffs it
  python rawcut.py render     <raw_dir>                              # cut.mp4 at source res/fps (NVENC / VideoToolbox / x264), edit audio
  python rawcut.py times      <raw_dir>                              # every join on the cut timeline, BIG = visible jump

Then: python prep_source.py <raw_dir>/cut.mp4 work/<id> --face-top 0.52   (raw OBS split: seam at 51.9%)

Camera files (OBS Source Record filter on the camera, named CAMERA-<YYYY-MM-DD hh-mm-ss>.mkv next to the take): `session`
pairs each take with the CAMERA file started within 5 s of it, measures the frame offset by matching face-cam motion in the
take's bottom half against the camera (one fixed lag per take; Source Record starts a few frames late), and `render` then
also writes <raw_dir>/cam_cut.mp4 - the clean 4K camera cut on exactly the same frames as cut.mp4. prep_source.py picks
cam_cut.mp4 up automatically for the face crops. --no-camera skips all of it.

drops.json: inclusive word-index ranges (from words.txt) and session-second ranges to remove - failed takes, false
starts, repeats, asides, fillers. Keep the LAST complete take of each line unless an earlier one is clearly better.
The cut step removes on its own: pauses longer than --gap between kept words, breaths, head and tail, and it always
cuts at a take-file boundary. Word edges come from audio energy and a guard stops any cut eating into a kept word.

Session timeline: take files back to back, each file's length = its VIDEO length (frames / fps); the audio of each
file is shifted by its stream start offset and padded/trimmed to that length, so frame n and audio sample n/fps*48000
always line up. A keep never spans two files.

Cut + verify logic ported (faster-whisper, hardware encode where available) from the Creator Skill Pack's cut stage
(explainer-panel-reel scripts 02-05).
"""
import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import wave
from concurrent.futures import ThreadPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import encoder_args, hwaccel_args, load_whisper, strip_hw  # noqa: E402
SR = 48000
FILL = {"um", "uh", "erm", "er", "ah", "hmm", "mm", "uhm", "umm"}
# Bias Whisper toward verbatim output (fillers, repeats) so failed takes stay visible.
VERBATIM = "Um, uh, so, like, I mean, okay, let me, let me redo that. Uh, okay."


def load(d, name, default=None):
    p = os.path.join(d, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def save(d, name, obj):
    json.dump(obj, open(os.path.join(d, name), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def ffprobe(path, *args):
    return json.loads(subprocess.run(["ffprobe", "-v", "error", "-of", "json", *args, path],
                                     check=True, capture_output=True, text=True).stdout)


def read_wav(path):
    w = wave.open(path)
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, w.getnchannels()).astype(np.float32) / 32768
    return a, w.getframerate()


def write_wav(path, a, sr):
    a = np.clip(a, -1, 1)
    a = a if a.ndim == 2 else a[:, None]
    o = wave.open(path, "wb")
    o.setnchannels(a.shape[1]); o.setsampwidth(2); o.setframerate(sr)
    o.writeframes((a * 32767).astype(np.int16).tobytes()); o.close()


def edit_audio(a, keeps, fps):
    """Concatenate the kept frame ranges of session audio with 8 ms fades at every join."""
    X = int(0.008 * SR); r = np.linspace(0, 1, X)[:, None]; parts = []
    for s, e in keeps:
        c = a[int(round(s / fps * SR)): int(round(e / fps * SR))].copy()
        if len(c) > 2 * X:
            c[:X] *= r; c[-X:] *= r[::-1]
        parts.append(c)
    return np.concatenate(parts)


def chunks(audio, max_s=25.0, min_sil=0.35):
    """Split 16 kHz audio at pauses into pieces of at most max_s seconds: [(start_sample, end_sample)].
    Whisper over a whole take merges restarts ("and it's neck, and it is neck and neck") into one sentence with wrong
    times; short independent windows come back verbatim, which is what choosing takes needs."""
    h = 160; m = len(audio) // h
    r = 20 * np.log10(np.sqrt((audio[: m * h].reshape(m, h) ** 2).mean(1)) + 1e-9)
    # quiet = near the noise floor OR 32 dB under loud speech (a noise gate can make the floor digital silence)
    quiet = r < max(np.percentile(r, 10) + 12, np.percentile(r, 90) - 32)
    sil, run = [], 0
    for i, q in enumerate(quiet):
        run = run + 1 if q else 0
        if run >= int(min_sil * 100) and (i + 1 == m or not quiet[i + 1]):
            # cut candidates: middle of a short pause; both ends of a long one (so a chunk starts where speech resumes)
            sil += [i - run // 2] if run < 200 else [i - run + 30, i - 30]
    cuts, start = [0], 0
    for c in sil + [m]:
        while (c - start) / 100 > max_s:                         # too long: cut at the last pause before the limit
            prev = [x for x in sil if start < x < c and (x - start) / 100 <= max_s]
            if prev:
                start = prev[-1]
            else:                                                 # no pause: the quietest 10 ms in the last 10 s of the window
                lo, hi = start + int((max_s - 10) * 100), start + int(max_s * 100)
                start = lo + int(np.argmin(r[lo:hi]))
            cuts.append(start)
    cuts.append(m)
    return [(cuts[k] * h, cuts[k + 1] * h) for k in range(len(cuts) - 1) if cuts[k + 1] > cuts[k]]


def whisper(audio, model_name):
    """faster-whisper words [[text, start, end]] for a 16 kHz mono float array (CUDA, else CPU), in short chunks."""
    from prep_source import GLOSSARY
    m = load_whisper(model_name)
    out = []
    for a0, a1 in chunks(audio):
        off = a0 / 16000
        segs, _ = m.transcribe(audio[a0:a1], language="en", word_timestamps=True, vad_filter=True,
                               condition_on_previous_text=False, initial_prompt=VERBATIM + " " + GLOSSARY)
        for s in segs:
            for w in s.words or []:
                t = w.word.strip()
                if out and (t.startswith("-") or (t[:2].startswith(".") and t[1:2].isdigit() and out[-1][0][-1:].isdigit())):
                    out[-1][0] += t; out[-1][2] = round(w.end + off, 3)  # "open" "-source", "5" ".5" -> one word
                elif any(c.isalnum() for c in t):
                    out.append([t, round(w.start + off, 3), round(w.end + off, 3)])
    return out


def find_camera(take):
    """CAMERA-<timestamp>.mkv/.mp4 in the take's folder whose timestamp is within 5 s of the take's name timestamp."""
    import datetime as dt
    stamp = lambda s: dt.datetime.strptime(re.search(r"\d{4}-\d\d-\d\d \d\d-\d\d-\d\d", s).group(0), "%Y-%m-%d %H-%M-%S")
    try:
        t = stamp(os.path.basename(take))
    except AttributeError:
        return None
    best = None
    for f in os.listdir(os.path.dirname(take)):
        if f.upper().startswith("CAMERA") and f.lower().endswith((".mkv", ".mp4", ".mov")):
            try:
                d = abs((stamp(f) - t).total_seconds())
            except AttributeError:
                continue
            if d <= 5 and (best is None or d < best[0]):
                best = (d, os.path.join(os.path.dirname(take), f))
    return best and best[1]


def motion(path, vf, secs=60):
    """Per-frame mean abs difference of a small grey proxy (motion energy), every frame (passthrough), first `secs`.
    The camera lag is fixed per take (no drift over 3.5 min measured on 2026-10-23), so a minute is enough."""
    W, H = 96, 82
    cmd = ["ffmpeg", "-v", "error", *hwaccel_args(), "-t", str(secs), "-i", path, "-fps_mode", "passthrough", "-vf",
           f"{vf},scale={W}:{H},format=gray", "-f", "rawvideo", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode:
        r = subprocess.run(strip_hw(cmd), capture_output=True, check=True)
    F = np.frombuffer(r.stdout, np.uint8).reshape(-1, H, W).astype(np.float32)
    m = np.abs(np.diff(F, axis=0)).mean((1, 2))
    return (m - m.mean()) / (m.std() + 1e-9)


def sync_camera(take, cam, max_lag=180):
    """Frame lag so that take frame = camera frame + lag, from face motion (take's bottom half vs camera centre)."""
    mm = motion(take, "crop=iw:ih*0.46:0:ih*0.54")
    cm = motion(cam, "crop=iw*0.5:ih:iw*0.25:0")
    best = (-9, 0)
    for lag in range(-max_lag, max_lag + 1):
        x, y = mm[max(0, lag):], cm[max(0, -lag):]; n = min(len(x), len(y))
        if n > 60:
            best = max(best, (float((x[:n] * y[:n]).mean()), lag))
    return best[1], best[0]


def session(a):
    os.makedirs(a.dir, exist_ok=True)
    files, audio, frames0, fps0, size0 = [], [], 0, None, None
    for f in a.files:
        f = os.path.abspath(f)
        v = ffprobe(f, "-select_streams", "v:0", "-count_packets", "-show_entries",
                    "stream=width,height,r_frame_rate,nb_read_packets,start_time")["streams"][0]
        au = ffprobe(f, "-select_streams", "a:0", "-show_entries", "stream=start_time")["streams"][0]
        fmt0 = float(ffprobe(f, "-show_entries", "format=start_time")["format"].get("start_time", 0))
        num, den = map(int, v["r_frame_rate"].split("/")); fps = num / den; n = int(v["nb_read_packets"])
        if fps0 and (fps != fps0 or (v["width"], v["height"]) != size0):
            sys.exit(f"{f}: {v['width']}x{v['height']}@{fps} differs from the first take; record takes with the same settings")
        fps0, size0 = fps, (v["width"], v["height"])
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-vn", "-ac", "2", "-ar", str(SR), "-f", "s16le", "-"],
                             check=True, capture_output=True).stdout
        x = np.frombuffer(raw, np.int16).reshape(-1, 2).astype(np.float32) / 32768
        off = int(round((float(v.get("start_time", 0)) - float(au.get("start_time", 0))) * SR))   # audio starts earlier: drop
        x = x[off:] if off >= 0 else np.concatenate([np.zeros((-off, 2), np.float32), x])
        need = int(round(n / fps * SR))
        x = x[:need] if len(x) >= need else np.concatenate([x, np.zeros((need - len(x), 2), np.float32)])
        audio.append(x)
        # -ss counts from the container start (OBS: the audio, ~21 ms before the first video frame)
        files.append({"path": f, "frames": n, "start_frame": frames0, "start": round(frames0 / fps, 3), "dur": round(n / fps, 3),
                      "seek_off": round(float(v.get("start_time", 0)) - fmt0, 6)})
        print(f"take {len(files):2d}  {os.path.basename(f)}  {n / fps:7.2f}s  at {frames0 / fps:7.2f}s")
        cam = None if a.no_camera else find_camera(f)
        if cam:
            cv = ffprobe(cam, "-select_streams", "v:0", "-count_packets", "-show_entries",
                         "stream=width,height,r_frame_rate,nb_read_packets,start_time")["streams"][0]
            cf0 = float(ffprobe(cam, "-show_entries", "format=start_time")["format"].get("start_time", 0))
            cn, cd = map(int, cv["r_frame_rate"].split("/"))
            if cn / cd != fps:
                sys.exit(f"{cam}: {cn / cd:g} fps but the take is {fps:g} fps; set the Source Record frame rate to match")
            lag, corr = sync_camera(f, cam)
            files[-1]["camera"] = {"path": cam, "lag": lag, "corr": round(corr, 3), "frames": int(cv["nb_read_packets"]),
                                   "size": [cv["width"], cv["height"]],
                                   "seek_off": round(float(cv.get("start_time", 0)) - cf0, 6)}
            print(f"         camera {os.path.basename(cam)} {cv['width']}x{cv['height']}: take frame = camera frame "
                  f"{lag:+d} (motion match {corr:.2f}{'  <-- WEAK, check by eye' if corr < 0.5 else ''})")
        frames0 += n
    A = np.concatenate(audio)
    write_wav(os.path.join(a.dir, "a48.wav"), A, SR)
    m16 = A.mean(1)[:: SR // 16000]                                   # 48k -> 16k (speech band, fine for ASR/voicing)
    write_wav(os.path.join(a.dir, "a16.wav"), m16, 16000)
    save(a.dir, "session.json", {"fps": fps0, "width": size0[0], "height": size0[1], "frames": frames0, "files": files})
    print(f"session: {len(files)} takes, {frames0 / fps0:.1f}s at {fps0:g} fps, {size0[0]}x{size0[1]}")


def file_of(S, t):
    return next((k for k, f in enumerate(S["files"]) if f["start"] <= t < f["start"] + f["dur"]), len(S["files"]) - 1)


def transcribe(a):
    S = load(a.dir, "session.json")
    x, _ = read_wav(os.path.join(a.dir, "a16.wav"))
    words = whisper(x[:, 0], a.model)
    save(a.dir, "words.json", words)
    with open(os.path.join(a.dir, "words.txt"), "w", encoding="utf-8") as f:
        cur = -1
        for i, (t, s, e) in enumerate(words):
            k = file_of(S, s)
            if k != cur:
                cur = k; f.write(f"----- take {k + 1}: {os.path.basename(S['files'][k]['path'])} (starts {S['files'][k]['start']:.2f}s)\n")
            gap = s - words[i - 1][2] if i else s
            f.write(f"{i:5d}  {s:8.2f} {e:8.2f}  {t}{f'    <- {gap:.1f}s pause' if gap > 0.6 else ''}\n")
    print(f"{len(words)} words over {len(S['files'])} takes. Script ([word index, session time] per line):\n")
    start, cur = 0, -1
    for i, (t, s, e) in enumerate(words):
        k = file_of(S, s)
        if k != cur:
            cur = k; print(f"\n===== take {k + 1} ({os.path.basename(S['files'][k]['path'])})")
        last = i == len(words) - 1
        if last or t[-1] in ".?!" or words[i + 1][1] - e > 0.7 or file_of(S, words[i + 1][1]) != k:
            print(f"[{start:4d} {words[start][1]:7.2f}] " + " ".join(w[0] for w in words[start:i + 1]))
            start = i + 1
    print("\nHINTS (read the script yourself as well):")
    n = [norm(w[0]) for w in words]
    for i, x in enumerate(n):
        if x in FILL:
            print(f"  filler   word {i} at {words[i][1]:.2f}: {words[i][0]}")
        if i and x and x == n[i - 1]:
            print(f"  repeat   words {i - 1}-{i} at {words[i - 1][1]:.2f}: {words[i - 1][0]} {words[i][0]}")
    hit = set()
    for i in range(len(n) - 2):
        for j in range(i + 1, min(i + 40, len(n) - 2)):
            if n[i:i + 3] == n[j:j + 3]:
                if (i - 1, j - 1) not in hit:                       # one line per restart, not one per overlapping 3-gram
                    print(f"  restart? words {i}-{j - 1} at {words[i][1]:.2f}: \"{' '.join(w[0] for w in words[i:i + 3])}\" "
                          f"said again at word {j} ({words[j][1]:.2f})")
                hit.add((i, j))
                break


def cut(a):
    S = load(a.dir, "session.json"); FPS = S["fps"]; words = load(a.dir, "words.json"); D = load(a.dir, "drops.json", {}) or {}
    A48, _ = read_wav(os.path.join(a.dir, "a48.wav")); x = A48.mean(1); DUR = len(x) / SR; h = 480; m = len(x) // h
    rms = 20 * np.log10(np.sqrt((x[: m * h].reshape(m, h) ** 2).mean(1)) + 1e-9); rms = np.convolve(rms, np.ones(3) / 3, "same")
    bounds = [f["start"] for f in S["files"][1:]]

    dropped = set()
    for i, j in D.get("words", []):
        dropped.update(range(i, j + 1))
    SECS = [tuple(s) for s in D.get("secs", [])]
    for i, (t, s, e) in enumerate(words):
        if any(p <= (s + e) / 2 < q for p, q in SECS):
            dropped.add(i)
    kept = [i for i in range(len(words)) if i not in dropped]
    kept or sys.exit("nothing kept")
    above = lambda t: rms[min(len(rms) - 1, max(0, int(t * 100)))] > -46

    def word_end(i):
        lim = min(words[i][2] + 1.0, words[i + 1][1] if i + 1 < len(words) else DUR)
        lim = min([lim] + [b for b in bounds if b > words[i][2]])
        t = words[i][2]; q = 0
        while t < lim:
            q = 0 if above(t) else q + 1
            if q >= 10:
                return max(words[i][2], t - 0.09), True
            t += 0.01
        return max(words[i][2], lim), False

    def word_start(i):
        # After a pause Whisper starts a word 0.3-0.4 s early, inside the silence: snap forward to the first sustained
        # sound, or every cut before that word leaves that much dead air ahead of it.
        t, hi = words[i][1], min(words[i][2], words[i][1] + 0.8)
        if not above(t):
            while t < hi and not (above(t) and above(t + 0.01)):
                t += 0.01
            if t < hi:
                return round(t - 0.01, 3), True
        lim = max(words[i][1] - 1.0, words[i - 1][2] if i else 0)
        lim = max([lim] + [b for b in bounds if b < words[i][1]])
        t = words[i][1]; q = 0
        while t > lim:
            q = 0 if above(t) else q + 1
            if q >= 10:
                return min(words[i][1], t + 0.09), True
            t -= 0.01
        return min(words[i][1], lim), False

    cuts = [[p, q, "drop"] for p, q in SECS]
    for p, nx in zip(kept, kept[1:]):
        (e, es), (s, ss) = word_end(p), word_start(nx)
        if nx != p + 1 or file_of(S, words[p][1]) != file_of(S, words[nx][1]):    # dropped words or another take
            A, B = e + (a.pad_out if es else 0), s - (a.pad_in if ss else 0)
            if B - A > 0.02:
                cuts.append([A, B, "drop"])
        elif s - e > a.gap:
            A, B = e + a.pad_out, s - a.pad_in
            seg = rms[int(A * 100): int(B * 100)] > -40; run = mx = 0
            for v in seg:
                run = run + 1 if v else 0; mx = max(mx, run)
            if B - A > 0.04 and not (B - A < 0.4 and mx >= 6):     # short gap with sustained sound = part of a word
                cuts.append([A, B, "gap"])
    cuts.append([0, max(0, word_start(kept[0])[0] - 0.08), "head"])
    cuts.append([min(DUR, word_end(kept[-1])[0] + 0.12), DUR, "tail"])
    for b in bounds:                                                  # a keep never spans two take files
        cuts.append([b - 0.001, b + 0.001, "drop"])

    def keeps_from(cs):
        cs = sorted(c for c in cs if c[1] > c[0]); Mg = []
        for p, q, t in cs:
            if Mg and p <= Mg[-1][1] + 0.02:
                Mg[-1][1] = max(Mg[-1][1], q)
            else:
                Mg.append([p, q, t])
        K, cur = [], 0.0
        for p, q, t in Mg:
            if p > cur:
                K.append([cur, p])
            cur = max(cur, q)
        if cur < DUR:
            K.append([cur, DUR])
        return K

    # breaths / air between words: unvoiced AND quiet for >= 0.18 s
    K = keeps_from(cuts)
    b16, _ = read_wav(os.path.join(a.dir, "a16.wav")); b = b16[:, 0]
    hop, win = 160, 640; nn = (len(b) - win) // hop; vo = np.zeros(nn, np.float32)
    for s0 in range(0, nn, 20000):
        idx = np.arange(s0, min(nn, s0 + 20000)); fr = np.lib.stride_tricks.sliding_window_view(b, win)[idx * hop]
        fr = fr - fr.mean(1, keepdims=True); X = np.fft.rfft(fr, n=2 * win, axis=1); ac = np.fft.irfft(np.abs(X) ** 2, axis=1)[:, :win]
        vo[idx] = (ac / (ac[:, :1] + 1e-9))[:, 53:229].max(1)
    mm = min(len(rms), len(vo)); quiet = (vo[:mm] < 0.45) & (rms[:mm] < -30); breaths = []
    for ks, ke in K:
        run = 0; hi = min(int(ke * 100), mm)
        for i in range(int(ks * 100), hi + 1):
            if i < hi and quiet[i]:
                run += 1
                continue
            if run >= 18:
                t0, t1 = (i - run) / 100, i / 100
                if not [w for w in words if t0 + 0.06 < w[1] < t1 - 0.06] and t0 > ks + 0.05 and t1 < ke - 0.05:
                    breaths.append([t0 + 0.05, t1 - 0.04, "breath"])
            run = 0

    # guard: no cut may eat into a kept word. Whisper's word edges are tight (a trailing "s" or a soft onset falls
    # outside them and looks like a breath), so each kept word is protected out to its audible edges.
    spans = [(word_start(i)[0], word_end(i)[0]) for i in kept]; safe = []
    for p, q, kind in cuts + breaths:
        segs = [[p, q]]
        for s, e in spans:
            if e <= p or s >= q:
                continue
            segs = [g for u, v in segs for g in ([[u, v]] if e <= u or s >= v else [[u, s], [e, v]]) if g[1] - g[0] > 0]
        floor = a.min_cut if kind in ("gap", "breath") else 0.06      # a short pause beats a visible face-cam jump
        safe += [[u, v, kind] for u, v in segs if v - u >= floor or kind in ("head", "tail") or (kind == "drop" and v - u < 0.01)]
    K = keeps_from(safe)
    keeps = [[round(s * FPS), round(e * FPS)] for s, e in K]
    fb = [f["start_frame"] for f in S["files"][1:]]                  # split any keep that still straddles a boundary
    keeps = [k for s, e in keeps for k in ([[s, e]] if not [c for c in fb if s < c < e] else
                                           [[u, v] for u, v in zip([s] + [c for c in fb if s < c < e], [c for c in fb if s < c < e] + [e])])]
    keeps = [k for k in keeps if k[1] - k[0] >= 2]

    starts, acc = [], 0
    for s, e in keeps:
        starts.append(acc); acc += e - s
    total = acc / FPS

    def cut_t(t):
        f = t * FPS
        for (s, e), st in zip(keeps, starts):
            if f < s:
                return st / FPS
            if f <= e:
                return (st + f - s) / FPS
        return total

    cw = [[words[i][0], round(cut_t(words[i][1]), 3), round(cut_t(words[i][2]), 3), i] for i in kept]
    joins = []
    for k in range(len(keeps) - 1):
        p, q = keeps[k][1] / FPS, keeps[k + 1][0] / FPS
        kind = max(((min(q, c[1]) - max(p, c[0]), c[2]) for c in safe), default=(0, "gap"))[1]
        take_change = file_of(S, p - 0.01) != file_of(S, q + 0.01)
        joins.append({"t": round(starts[k + 1] / FPS, 3), "removed": round(q - p, 2), "kind": "take" if take_change else kind,
                      "big": bool(take_change or kind == "drop" or q - p > 0.6)})
    save(a.dir, "edl.json", {"keeps": keeps, "fps": FPS, "dur": round(total, 3)})
    save(a.dir, "cut_words.json", cw); save(a.dir, "cuts.json", joins)
    short = [k for k in keeps if (k[1] - k[0]) / FPS < 0.2]
    print(f"session {DUR:.1f}s -> cut {total:.1f}s | {len(keeps)} keeps, {len(joins)} joins ({sum(j['big'] for j in joins)} big), "
          f"{len({tuple(c[:2]) for c in safe if c[2] == 'breath'})} breath cuts, {len(dropped)} words dropped")
    if short:
        print(f"WARNING {len(short)} keeps under 0.2s (slivers between cuts), session frames {short[:6]}: check drops.json around them")
    marks = {next((w[3] for w in cw if w[1] >= j["t"] - 0.02), None) for j in joins if j["big"]}
    lines, start = [], 0
    for i, w in enumerate(cw):
        if i == len(cw) - 1 or w[0][-1] in ".?!":
            lines.append(f"[{cw[start][1]:7.2f}] " + " ".join(("|| " if y[3] in marks else "") + y[0] for y in cw[start:i + 1]))
            start = i + 1
    open(os.path.join(a.dir, "edit.txt"), "w", encoding="utf-8").write(
        "\n".join(lines) + "\n\nWORDS (cut-timeline start, end, word)\n" + "\n".join(f"{w[1]:8.2f} {w[2]:8.2f}  {w[0]}" for w in cw) + "\n")
    print("\nEDIT ( || = a big jump cut lands just before this word):\n" + "\n".join(lines))


def verify(a):
    E = load(a.dir, "edl.json"); cw = load(a.dir, "cut_words.json"); FPS = E["fps"]
    A48, _ = read_wav(os.path.join(a.dir, "a48.wav"))
    ed = edit_audio(A48, E["keeps"], FPS)
    write_wav(os.path.join(a.dir, "edit.wav"), ed, SR)
    V = whisper(ed.mean(1)[:: SR // 16000], a.model); save(a.dir, "verify_words.json", V)
    toks = lambda L: [(norm(p), k) for k, w in enumerate(L) for p in w[0].split("-") if norm(p)]   # "open-source" == "open source"
    TA, TB = toks(cw), toks(V); A, B = [t for t, _ in TA], [t for t, _ in TB]; issues = 0
    ctx = lambda L, T, i, j: " ".join(y[0] for y in L[max(0, T[min(i, len(T) - 1)][1] - 3): T[min(max(j - 1, i), len(T) - 1)][1] + 4])
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        issues += 1; t = cw[TA[min(i1, len(TA) - 1)][1]][1]
        name = {"delete": "MISSING", "insert": "EXTRA", "replace": "CHANGED"}[op]
        print(f"{name:8s} at {t:7.2f}s  meant: \"{ctx(cw, TA, i1, i2)}\"  |  heard: \"{ctx(V, TB, j1, j2)}\"")
    for p, q in zip(V, V[1:]):
        if q[1] - p[2] > 0.45:
            issues += 1; print(f"PAUSE    at {p[2]:7.2f}s  {q[1] - p[2]:.2f}s between \"{p[0]}\" and \"{q[0]}\"")
        if norm(p[0]) == norm(q[0]):
            print(f"REPEAT   at {p[1]:7.2f}s  \"{p[0]} {q[0]}\"  (fine if meant)")
    dur = len(ed) / SR
    print(f"\nhead {V[0][1]:.2f}s before the first word, tail {dur - V[-1][2]:.2f}s after the last (both should be under ~0.25s)")
    print(f"{issues} issue(s); edit is {dur:.1f}s, {len(V)} words\n\nHEARD: " + " ".join(y[0] for y in V))


def render(a):
    S = load(a.dir, "session.json"); E = load(a.dir, "edl.json"); FPS = S["fps"]
    tmp = os.path.join(a.dir, "_segs"); os.makedirs(tmp, exist_ok=True)
    A48, _ = read_wav(os.path.join(a.dir, "a48.wav"))
    write_wav(os.path.join(tmp, "edit.wav"), edit_audio(A48, E["keeps"], FPS), SR)
    want = sum(e - s for s, e in E["keeps"])

    def segment(path, seek_off, lf, n, total, out):
        """n frames from local frame lf of path; frames before 0 / past `total` repeat the first / last frame."""
        pre, post = max(0, -lf), max(0, lf + n - total)
        pad = f"tpad=start={pre}:start_mode=clone:stop={post}:stop_mode=clone," if pre or post else ""
        return ["ffmpeg", "-v", "error", "-y", *hwaccel_args(), "-ss", f"{(max(lf, 0) - 0.5) / FPS + seek_off:.6f}", "-i", path,
                "-frames:v", str(n), "-an", *encoder_args("high"), "-pix_fmt", "yuv420p",
                "-vf", f"{pad}setpts=N/({FPS:g}*TB)", "-fps_mode", "passthrough", "-video_track_timescale", "60000", out]

    def go(cmd):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:                                              # no hardware decode -> software decode
            r = subprocess.run(strip_hw(cmd), capture_output=True, text=True)
        return r.returncode, r.stderr[-300:]

    def build(name, jobs, audio):
        with ThreadPoolExecutor(4) as ex:
            for k, (rc, err) in enumerate(ex.map(go, [j for j, _ in jobs])):
                if rc:
                    sys.exit(f"{name} segment {k} failed: {err}")
        lst = os.path.join(tmp, "list.txt")
        with open(lst, "w") as L:
            L.writelines(f"file '{os.path.basename(p)}'\n" for _, p in jobs)
        out = os.path.join(a.dir, name)
        aud = ["-i", os.path.join(tmp, "edit.wav"), "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "320k"] if audio else ["-map", "0:v"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, *aud, "-c:v", "copy",
                        "-movflags", "+faststart", out], check=True)
        got = int(ffprobe(out, "-select_streams", "v:0", "-count_packets", "-show_entries", "stream=nb_read_packets")["streams"][0]["nb_read_packets"])
        print(f"wrote {out}: {got} frames ({got / FPS:.2f}s), expected {want}" + ("" if got == want else "  <-- FRAME COUNT MISMATCH"))
        for _, p in jobs:
            os.remove(p)

    take = lambda s: next(f for f in reversed(S["files"]) if f["start_frame"] <= s)
    jobs = []
    for k, (s, e) in enumerate(E["keeps"]):
        f = take(s); p = os.path.join(tmp, f"s{k:04d}.mp4")
        jobs.append((segment(f["path"], f.get("seek_off", 0), s - f["start_frame"], e - s, f["frames"], p), p))
    build("cut.mp4", jobs, True)

    if all("camera" in take(s) for s, _ in E["keeps"]):              # clean camera on the same frames (lag per take)
        jobs = []
        for k, (s, e) in enumerate(E["keeps"]):
            c = take(s)["camera"]; p = os.path.join(tmp, f"c{k:04d}.mp4")
            jobs.append((segment(c["path"], c["seek_off"], s - take(s)["start_frame"] - c["lag"], e - s, c["frames"], p), p))
        build("cam_cut.mp4", jobs, False)
    elif any("camera" in f for f in S["files"]):
        print("NOTE some kept takes have no CAMERA file: cam_cut.mp4 not written (face crops will come from cut.mp4)")
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)


def times(a):
    cuts = load(a.dir, "cuts.json"); cw = load(a.dir, "cut_words.json"); E = load(a.dir, "edl.json")
    print(f"cut length {E['dur']:.2f}s, {len(cuts)} joins ({sum(c['big'] for c in cuts)} BIG). BIG joins are visible jumps in the "
          "face cam: put a full-graphic takeover or a face punch-in on each.\n")
    for c in cuts:
        k = next((i for i, w in enumerate(cw) if w[1] >= c["t"] - 0.02), len(cw) - 1)
        print(f"{c['t']:8.3f}  {'BIG  ' if c['big'] else 'small'} {c['kind']:6s} removed {c['removed']:5.2f}s   "
              f"...{' '.join(w[0] for w in cw[max(0, k - 3):k])} | {' '.join(w[0] for w in cw[k:k + 3])}...")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("session"); p.add_argument("dir"); p.add_argument("files", nargs="+")
    p.add_argument("--no-camera", action="store_true", help="ignore CAMERA-* Source Record files")
    for name in ("transcribe", "verify"):
        p = sub.add_parser(name); p.add_argument("dir"); p.add_argument("--model", default="large-v3-turbo")
    p = sub.add_parser("cut"); p.add_argument("dir")
    p.add_argument("--gap", type=float, default=0.12); p.add_argument("--pad-out", type=float, default=0.13,
                                                                     help="air kept after a word before a cut (lets the sentence land)")
    p.add_argument("--pad-in", type=float, default=0.08, help="air kept before a word after a cut (a join is ~0.2 s of silence)")
    p.add_argument("--min-cut", type=float, default=0.3, help="leave pauses/breaths shorter than this uncut (0.06 = pack's tight cut)")
    for name in ("render", "times"):
        p = sub.add_parser(name); p.add_argument("dir")
    a = ap.parse_args()
    {"session": session, "transcribe": transcribe, "cut": cut, "verify": verify, "render": render, "times": times}[a.cmd](a)


if __name__ == "__main__":
    main()
