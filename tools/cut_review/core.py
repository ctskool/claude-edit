"""Cut review state: the tight cut as kept frame ranges that Chase adjusts by ear before any picture is rendered.

Files in <raw_dir> (all next to rawcut.py's own):
  edl.json               what `rawcut.py render` cuts both files from. After an approval it carries "reviewed": true.
  cut_review.json        his review: {"auto": keeps the review started from, "keeps": his keeps, "notes", "general",
                         "approved": ISO time or null}. Saved on every change, so a reload loses nothing.
  edl.auto.json, cut_words.auto.json, cuts.auto.json
                         the machine's cut, copied aside at the first approval after each `rawcut.py cut`.

A new `rawcut.py cut` writes a fresh edl.json without "reviewed". The next load carries his changes onto it:
keeps = (new auto + what he added) - what he removed, as sets of session frames. So a re-cut for one line does not
throw away the joins he already fixed elsewhere.

  python tools/cut_review/core.py <raw_dir>          # carry + apply without the page (after a re-cut)
  python tools/cut_review/core.py <raw_dir> --video  # only make the small camera copies the page plays (see videos)
"""
import datetime
import json
import os
import shutil
import struct
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rawcut  # noqa: E402

SR = rawcut.SR
FADE = int(0.008 * SR)                                               # rawcut.edit_audio's fade at every join


def open_audio(d):
    """a48.wav as an int16 memmap (frames, channels): an 84-minute session is 900 MB, never read whole."""
    p = os.path.join(d, "a48.wav")
    with open(p, "rb") as f:
        if f.read(4) != b"RIFF":
            sys.exit(f"{p}: not a WAV file")
        f.seek(12); ch = None
        while True:
            head = f.read(8)
            if len(head) < 8:
                sys.exit(f"{p}: no data chunk")
            name, size = head[:4], struct.unpack("<I", head[4:])[0]
            if name == b"fmt ":
                fmt = f.read(size); ch, sr, bits = struct.unpack("<H", fmt[2:4])[0], struct.unpack("<I", fmt[4:8])[0], struct.unpack("<H", fmt[14:16])[0]
                if sr != SR or bits != 16:
                    sys.exit(f"{p}: {sr} Hz {bits}-bit, expected {SR} Hz 16-bit")
            elif name == b"data":
                off = f.tell(); n = min(size, os.path.getsize(p) - off) // (2 * ch)
                return np.memmap(p, dtype="<i2", mode="r", offset=off, shape=(n, ch))
            else:
                f.seek(size + (size & 1), 1)


def peaks(A):
    """Loudest sample per 10 ms of the session as bytes 0-255 (square-root scale, so quiet speech still shows)."""
    h = SR // 100; out = []
    for i in range(0, len(A) - h + 1, SR * 60):
        c = np.abs(A[i:i + SR * 60].astype(np.int32)).max(1); m = len(c) // h
        out.append(c[: m * h].reshape(m, h).max(1))
    p = np.concatenate(out) if out else np.zeros(0)
    return (np.sqrt(np.minimum(p, 32767) / 32767) * 255).astype(np.uint8).tobytes()


def bounds(S):
    return [f["start_frame"] for f in S["files"][1:]]


def norm(keeps, S):
    """Sorted, merged, inside the session, never across two take files, nothing under 2 frames."""
    M = []
    for s, e in sorted([max(0, int(s)), min(S["frames"], int(e))] for s, e in keeps):
        if e <= s:
            continue
        if M and s <= M[-1][1]:
            M[-1][1] = max(M[-1][1], e)
        else:
            M.append([s, e])
    fb = bounds(S); out = []
    for s, e in M:
        cuts = [c for c in fb if s < c < e]
        out += [[u, v] for u, v in zip([s] + cuts, cuts + [e])]
    return [k for k in out if k[1] - k[0] >= 2]


def minus(A, B):
    """Frame ranges of A that are not in B (both sorted, non-overlapping)."""
    out = []
    for s, e in A:
        cur = s
        for p, q in B:
            if q <= cur:
                continue
            if p >= e:
                break
            if p > cur:
                out.append([cur, p])
            cur = max(cur, q)
        if cur < e:
            out.append([cur, e])
    return out


def carry(old_auto, old_keeps, new_auto, S):
    """His changes on an older machine cut, moved onto a new one."""
    added, removed = minus(old_keeps, old_auto), minus(old_auto, old_keeps)
    return norm(minus(norm(new_auto + added, S), removed), S)


def inside(keeps, f):
    return any(s <= f < e for s, e in keeps)


def load_state(d):
    """Everything the page needs. `keeps` is where he left off, `auto` the machine cut it is compared with."""
    S = rawcut.load(d, "session.json"); E = rawcut.load(d, "edl.json"); R = rawcut.load(d, "cut_review.json")
    if not S or not E:
        sys.exit(f"{d}: needs session.json and edl.json (run rawcut.py session, transcribe and cut first)")
    carried = 0
    if E.get("reviewed") and os.path.exists(os.path.join(d, "edl.auto.json")):
        base = rawcut.load(d, "edl.auto.json")["keeps"]
        cw, cuts = rawcut.load(d, "cut_words.auto.json", []), rawcut.load(d, "cuts.auto.json", [])
        auto = norm(base, S); keeps = norm(R["keeps"], S) if R else norm(E["keeps"], S)
        approved = R.get("approved") if R and keeps == norm(E["keeps"], S) else None
    else:
        base = E["keeps"]; cw, cuts = rawcut.load(d, "cut_words.json", []), rawcut.load(d, "cuts.json", [])
        auto = norm(base, S); keeps, approved = auto, None
        if R:
            keeps = carry(norm(R["auto"], S), norm(R["keeps"], S), auto, S)
            carried = int(norm(R["auto"], S) != auto and keeps != auto)
    # the machine's joins by their two edges, so an untouched join keeps its kind, BIG flag and RUN-ON warning
    joins = {}
    if len(cuts) == len(base) - 1:
        joins = {f"{base[k][1]}|{base[k + 1][0]}": c for k, c in enumerate(cuts)}
    return {"S": S, "fps": S["fps"], "auto": auto, "keeps": keeps, "approved": approved, "carried": carried,
            "base_words": {w[3]: w[0] for w in cw}, "auto_joins": joins,
            "notes": (R or {}).get("notes", []), "general": (R or {}).get("general", "")}


def save_draft(d, st):
    rawcut.save(d, "cut_review.json", {"fps": st["fps"], "auto": st["auto"], "keeps": st["keeps"], "notes": st["notes"],
                                       "general": st["general"], "approved": st["approved"]})


def kept_words(words, st):
    """Word indexes in the cut: the machine's kept words that are still inside a keep, plus dropped words he pulled
    back in (inside a keep now, outside the machine's)."""
    fps, base = st["fps"], st["base_words"]; out = []
    for i, w in enumerate(words):
        m = (w[1] + w[2]) / 2 * fps
        if inside(st["keeps"], m) and (i in base or not inside(st["auto"], m)):
            out.append(i)
    return out


def apply(d, st):
    """His keeps become the cut: edl.json, cut_words.json, cuts.json and edit.txt, the way `rawcut.py cut` writes them."""
    S, fps, keeps = st["S"], st["fps"], st["keeps"]; words = rawcut.load(d, "words.json")
    if not rawcut.load(d, "edl.json").get("reviewed"):               # a fresh machine cut: keep it beside ours
        for n in ("edl", "cut_words", "cuts"):
            if os.path.exists(os.path.join(d, n + ".json")):
                shutil.copyfile(os.path.join(d, n + ".json"), os.path.join(d, n + ".auto.json"))
    starts, acc = [], 0
    for s, e in keeps:
        starts.append(acc); acc += e - s
    total = acc / fps

    def cut_t(t):
        f = t * fps
        for (s, e), st0 in zip(keeps, starts):
            if f < s:
                return st0 / fps
            if f <= e:
                return (st0 + f - s) / fps
        return total

    kept = kept_words(words, st)
    cw = [[st["base_words"].get(i, words[i][0]), round(cut_t(words[i][1]), 3), round(cut_t(words[i][2]), 3), i] for i in kept]
    joins = []
    for k in range(len(keeps) - 1):
        p, q = keeps[k][1], keeps[k + 1][0]
        take = rawcut.file_of(S, p / fps - 0.01) != rawcut.file_of(S, q / fps + 0.01)
        old = st["auto_joins"].get(f"{p}|{q}")
        j = {"t": round(starts[k + 1] / fps, 3), "removed": round((q - p) / fps, 2)}
        if old:
            j.update({x: old[x] for x in ("kind", "big", "runon") if x in old})
        else:
            j.update(kind="take" if take else "hand", big=bool(take or (q - p) / fps > 0.6))
        joins.append(j)
    rawcut.save(d, "edl.json", {"keeps": keeps, "fps": fps, "dur": round(total, 3), "reviewed": True})
    rawcut.save(d, "cut_words.json", cw); rawcut.save(d, "cuts.json", joins)
    marks = {next((w[3] for w in cw if w[1] >= j["t"] - 0.02), None) for j in joins if j["big"]}
    lines, start = [], 0
    for i, w in enumerate(cw):
        if i == len(cw) - 1 or w[0][-1:] in ".?!":
            lines.append(f"[{cw[start][1]:7.2f}] " + " ".join(("|| " if y[3] in marks else "") + y[0] for y in cw[start:i + 1]))
            start = i + 1
    open(os.path.join(d, "edit.txt"), "w", encoding="utf-8").write(
        "\n".join(lines) + "\n\nWORDS (cut-timeline start, end, word)\n" + "\n".join(f"{w[1]:8.2f} {w[2]:8.2f}  {w[0]}" for w in cw) + "\n")
    st["approved"] = datetime.datetime.now().isoformat(timespec="seconds")
    save_draft(d, st)
    return {"dur": round(total, 3), "joins": len(joins), "words": len(cw)}


def cut_pcm(A, keeps, fps, a, n):
    """n samples of the cut from cut sample a, as int16 bytes: the same sound `rawcut.py render` writes (8 ms fades)."""
    out = np.zeros((n, A.shape[1]), np.int16); pos = 0
    for s, e in keeps:
        ks, ke = int(round(s / fps * SR)), int(round(e / fps * SR)); L = ke - ks
        lo, hi = max(a, pos), min(a + n, pos + L)
        if lo < hi:
            c = A[ks + lo - pos: ks + hi - pos].astype(np.float32)
            if L > 2 * FADE:
                i = np.arange(lo - pos, lo - pos + len(c), dtype=np.float64)
                c *= np.minimum(1, np.minimum(i, L - 1 - i) / (FADE - 1))[:, None]
            out[lo - a: lo - a + len(c)] = c
        pos += L
        if pos >= a + n:
            break
    return out.tobytes()


def video_sources(S):
    """Per take: the file the page shows (his camera when there is one, else the take) and its frame lag to the take."""
    out, seen = [], {}
    for f in S["files"]:
        v = {"src": f["camera"]["path"], "lag": f["camera"]["lag"]} if "camera" in f else {"src": f["path"], "lag": 0}
        v["vid"] = seen.setdefault(v["src"], len(seen)); v["first"] = f.get("first", 0)   # `rawcut.py move` pieces share a file
        v["delay"] = f.get("pic_delay", 0)                            # picture behind the voice (rawcut.py sync)
        out.append(v)
    return out


def video_path(d, k):
    return os.path.join(d, f"review_cam_{k}.mp4")


def videos(d, S, done=None):
    """A small copy of each take's camera for the page (540 px high, 30 fps, a keyframe every 8 frames so a jump
    across a join lands fast). About 10x real time on the GPU, so start it right after `session`, in the background:
    it does not need the cut. A copy newer than its source is kept."""
    srcs = {v["vid"]: v["src"] for v in video_sources(S)}

    def one(k):
        src, out = srcs[k], video_path(d, k)
        if not (os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(src)):
            tail = ["-r", "30", "-c:v", "h264_nvenc", "-preset", "p1", "-g", "8", "-bf", "0", "-b:v", "1200k", "-movflags",
                    "+faststart", "-f", "mp4", out + ".part"]
            gpu = ["ffmpeg", "-v", "error", "-y", "-hwaccel", "cuda", "-hwaccel_output_format", "cuda", "-i", src, "-an",
                   "-vf", "scale_cuda=-2:540", *tail]
            mac = ["ffmpeg", "-v", "error", "-y", "-hwaccel", "videotoolbox", "-i", src, "-an", "-vf", "scale=-2:540", "-r", "30",
                   "-c:v", "h264_videotoolbox", "-g", "8", "-bf", "0", "-b:v", "1200k", "-pix_fmt", "yuv420p", *tail[tail.index("-movflags"):]]
            if sys.platform == "darwin" and subprocess.run(mac, capture_output=True).returncode == 0:
                pass                                                     # a Mac: VideoToolbox did it (not yet run on a Mac)
            elif subprocess.run(gpu, capture_output=True).returncode:    # no CUDA decode for this file: scale on the CPU
                cpu = ["ffmpeg", "-v", "error", "-y", "-i", src, "-an", "-vf", "scale=-2:540", *tail]
                if subprocess.run(cpu, capture_output=True).returncode:  # no NVENC either (no NVIDIA card, a Mac): libx264
                    soft = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-pix_fmt", "yuv420p", "-g", "8", "-bf", "0"]
                    i, j = cpu.index("-c:v"), cpu.index("-movflags")
                    subprocess.run(cpu[:i] + soft + cpu[j:], check=True)
            os.replace(out + ".part", out)
        if done:
            done(k)
        return k
    with ThreadPoolExecutor(2) as ex:
        list(ex.map(one, sorted(srcs)))


def cut_samples(keeps, fps):
    return sum(int(round(e / fps * SR)) - int(round(s / fps * SR)) for s, e in keeps)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[2] == "--video":
        videos(sys.argv[1], rawcut.load(sys.argv[1], "session.json"), lambda k: print(f"camera copy {k + 1} ready", flush=True))
        sys.exit(0)
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    st = load_state(sys.argv[1]); r = apply(sys.argv[1], st)
    print(f"applied his review to {sys.argv[1]}: cut {r['dur']:.2f}s, {r['joins']} joins, {r['words']} words"
          + ("  (changes carried onto a new machine cut)" if st["carried"] else ""))
