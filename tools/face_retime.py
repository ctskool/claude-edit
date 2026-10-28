"""Content-aware 60 -> 30 fps retime of the face cam in 60 fps split-screen exports.

Why: the finished exports are 60 fps files that carry an irregular ~30 fps camera cadence (camera frames are duplicated or
dropped). A plain fps=30 filter shows source frame 2k at tick k, which sometimes lands on two copies of one camera frame in a
row and skips a unique one, so the face judders.

What this does (the editorial v10 fixer, work/1022-2/v2/editorial/_v10work/retime_*.py, generalised):
1. Stream-decodes the face region ONCE as a small grey proxy (320 px wide, area scale, native frame rate) and keeps only each
   frame's mean abs difference (0-255) to the previous frame. Nothing big is held in memory or written to disk.
2. Unique frames = difference >= 0.3. A DP gives every 30 fps tick k one unique frame i, ticks strictly increasing in i, near
   its capture time i/2: cost |k - i/2|, +1.0 when it is 2 ticks from round(i/2) (never further), +1.5 per unique dropped,
   +1.0 per empty tick (the previous frame is held), +2.0 for an isolated 2-tick hold (step, hold, step).
   Parameters (0.3, 1.5, 1.0, 1.0, 2.0) - the fixer's retime_sweep.solve, bit for bit.
3. Writes the tick -> source-frame map as JSON (with the per-frame differences and old-vs-new stats).
4. For every --crop / --scale / --out group, stream-decodes the source at its native rate through crop + scale (the same
   filters prep_source.py uses) and pipes the mapped frame of each tick to libx264 (crf 16, g 15, preset medium, yuv420p,
   +faststart). The source's colour tags (tv / bt709 for typical OBS exports) are set on the INPUT side of the raw pipe, so ffmpeg
   inserts no matrix conversion and the file is tagged like prep_source's output. Tick count = round(duration * 30).

Usage:
  python face_retime.py <source.mp4> --map <out_map.json> [--proxy-crop W:H:X:Y] [--reuse]
                        [--crop W:H:X:Y] [--scale WxH] --out <file.mp4>   [... more groups]

Each --out closes a group; the --crop / --scale given before it apply to that output. No --crop = full frame, no --scale = crop
size, and a -2 (or -1) dimension is derived exactly like ffmpeg's scale=W:-2. The proxy region defaults to the bounding box of
all crops. --reuse loads an existing map instead of solving again when its source, tick count, proxy and parameters match.
Outputs are encoded to a temp file and moved into place; an existing output that is hard-linked (an asset shared by several
projects) is never overwritten. Deterministic: same source + arguments -> same map JSON and same bitstream.
"""
import argparse
import json
import math
import os
import subprocess
import sys

import numpy as np

FPS_OUT = 30
PARAMS = [0.3, 1.5, 1.0, 1.0, 2.0]  # unique threshold, DROP, EMPTY, FAR, ISO (editorial v10 fixer)
HORIZON = 40  # ticks a carried (held) state stays alive in the DP (fixer value)
PROXY_W = 320
DEVNULL = subprocess.DEVNULL


# ---------------------------------------------------------------------------------------------------------------- probing
def probe(src):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate,color_range,color_space,color_transfer,color_primaries"
                          ":format=duration", "-of", "json", src],
                         check=True, capture_output=True, text=True, stdin=DEVNULL).stdout
    d = json.loads(out)
    s = d["streams"][0]
    num, den = s["r_frame_rate"].split("/")

    def tag(key, default):
        v = s.get(key)
        return v if v and v != "unknown" else default

    return {"width": int(s["width"]), "height": int(s["height"]), "fps": float(num) / float(den),
            "duration": float(d["format"]["duration"]),
            "color": {"color_range": tag("color_range", "tv"), "colorspace": tag("color_space", "bt709"),
                      "color_trc": tag("color_transfer", "bt709"), "color_primaries": tag("color_primaries", "bt709")}}


def parse_crop(s):
    p = [int(v) for v in s.split(":")]
    if len(p) != 4 or p[0] <= 0 or p[1] <= 0 or p[2] < 0 or p[3] < 0:
        raise ValueError(f"bad crop {s!r}, want W:H:X:Y")
    return p


def ffmpeg_dims(sw, sh, iw, ih):
    """Output size of ffmpeg's scale=sw:sh on an iw x ih input (-1 / -2 = keep aspect, rounded to a multiple of 1 / 2)."""
    def rescale(a, b, c):  # av_rescale, AV_ROUND_NEAR_INF, positive values
        return (a * b + c // 2) // c
    if sw < 0 and sh < 0:
        sw, sh = iw, ih
    if sw < 0:
        sw = rescale(sh, iw, ih * -sw) * -sw
    if sh < 0:
        sh = rescale(sw, ih, iw * -sh) * -sh
    return sw, sh


def parse_scale(s, crop_w, crop_h):
    if s is None:
        return crop_w, crop_h
    sep = "x" if "x" in s else ":"
    a, b = (int(v) for v in s.split(sep))
    if a == 0 or b == 0 or a < -2 or b < -2:
        raise ValueError(f"bad scale {s!r}, want WxH (a -2 / -1 side keeps the aspect)")
    return ffmpeg_dims(a, b, crop_w, crop_h)


def crop_vf(crop):
    return "crop={}:{}:{}:{},".format(*crop) if crop else ""


# ---------------------------------------------------------------------------------------------------------------- the map
def proxy_diffs(src, crop, pw, ph):
    """Mean abs grey difference of every source frame to the previous one (frame 0 -> 0), streamed from a pw x ph proxy."""
    vf = f"{crop_vf(crop)}scale={pw}:{ph}:flags=area,format=gray"
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-i", src, "-an", "-sn", "-dn", "-fps_mode", "passthrough", "-vf", vf,
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    fs = pw * ph
    p = subprocess.Popen(cmd, stdin=DEVNULL, stdout=subprocess.PIPE, bufsize=fs * 8)
    diffs, prev = [], None
    while True:
        b = p.stdout.read(fs)
        if len(b) < fs:
            if b:
                raise SystemExit(f"proxy decode: truncated frame after {len(diffs)} frames")
            break
        cur = np.frombuffer(b, np.uint8).reshape(ph, pw).astype(np.int16)
        diffs.append(0.0 if prev is None else float(np.abs(cur - prev).mean()))
        prev = cur
    p.stdout.close()
    if p.wait() != 0:
        raise SystemExit(f"proxy decode failed (ffmpeg exit {p.returncode})")
    if not diffs:
        raise SystemExit("proxy decode produced no frames")
    return np.array(diffs)


def solve(diff, ticks, ratio, th, DROP, EMPTY, FAR, ISO):
    """retime_sweep.solve from the fixer (ratio = source fps / 30, 2 for the 60 fps exports). Returns (U, frame map)."""
    N = len(diff)
    U = [0] + [i for i in range(1, N) if diff[i] >= th]
    M = len(U)
    r = [int(math.floor(u / ratio + 0.5)) for u in U]
    INF = float("inf")

    def acost(j, k):
        d = abs(k - r[j])
        if d > 2:
            return INF
        return abs(k - U[j] / ratio) + (FAR if d == 2 else 0.0)

    cand = [[] for _ in range(ticks)]
    for j in range(M):
        for k in range(r[j] - 2, r[j] + 3):
            if 0 <= k < ticks:
                cand[k].append(j)
    # state (j, run): unique j on screen, shown for `run` consecutive ticks (capped at 3); ISO charges a hold of exactly 2
    # ticks that is followed by a step (the isolated duplicate that reads as judder)
    best = [{}]
    for j in cand[0]:
        best[0][(j, 1)] = (acost(j, 0) + DROP * j, None)
    for k in range(1, ticks):
        prev = best[k - 1]
        cur = {}
        for (j, run), (c, _) in prev.items():
            if r[j] < k - HORIZON:
                continue
            key = (j, min(run + 1, 3))
            v = c + EMPTY
            if key not in cur or v < cur[key][0]:
                cur[key] = (v, (j, run))
        items = sorted(prev.items())
        for j in cand[k]:
            ac = acost(j, k)
            bestc, bestp = INF, None
            for (jp, run), (c, _) in items:
                if jp >= j:
                    break
                v = c + DROP * (j - jp - 1) + (ISO if run == 2 else 0.0)
                if v < bestc:
                    bestc, bestp = v, (jp, run)
            if bestp is None:
                continue
            key = (j, 1)
            tot = bestc + ac
            if key not in cur or tot < cur[key][0]:
                cur[key] = (tot, bestp)
        if not cur:
            # a frozen stretch longer than HORIZON with no unique near this tick: keep holding (the fixer would stop here;
            # never reached on a normal take, so the result is unchanged whenever the fixer succeeds)
            for (j, run), (c, _) in prev.items():
                key = (j, min(run + 1, 3))
                v = c + EMPTY
                if key not in cur or v < cur[key][0]:
                    cur[key] = (v, (j, run))
        best.append(cur)
    last = best[ticks - 1]
    kend = min(last, key=lambda s: last[s][0] + DROP * (M - 1 - s[0]))
    seq = [None] * ticks
    s = kend
    for k in range(ticks - 1, -1, -1):
        seq[k] = s[0]
        s = best[k][s][1]
    return U, [U[j] for j in seq]


def map_stats(fmap, diff, th, ratio):
    """Judder stats of a tick -> source-frame map, counted on unique groups (frames since the last diff >= th)."""
    uid = np.cumsum(np.r_[0, (diff[1:] >= th).astype(np.int64)])
    starts = np.r_[0, np.nonzero(diff[1:] >= th)[0] + 1]
    ids = uid[np.asarray(fmap)]
    step = ids[1:] != ids[:-1]
    n = len(step)
    iso = sum(1 for i in range(1, n - 1) if step[i - 1] and not step[i] and step[i + 1])
    off = starts[ids] / ratio - np.arange(len(fmap))  # capture time of the shown unique vs its tick, in ticks
    return {"ticks": len(fmap), "uniques": len(starts), "skipped_uniques": int(len(starts) - len(set(ids.tolist()))),
            "held_ticks": int((~step).sum()), "isolated_holds": int(iso),
            "offset_ticks": {"mean": round(float(off.mean()), 3), "p5": round(float(np.percentile(off, 5)), 2),
                             "p95": round(float(np.percentile(off, 95)), 2), "max_abs": round(float(np.abs(off).max()), 2)}}


def build_map(src, info, ticks, proxy, map_path, reuse):
    ratio = info["fps"] / FPS_OUT
    pw = PROXY_W
    ph = int(math.floor(PROXY_W * proxy[1] / proxy[0] / 2 + 0.5)) * 2
    src_size = os.path.getsize(src)
    if reuse and os.path.exists(map_path):
        d = json.load(open(map_path))
        if (d.get("src_size") == src_size and os.path.basename(d.get("src", "")) == os.path.basename(src)
                and d.get("ticks") == ticks and d.get("params") == PARAMS and d.get("proxy", {}).get("crop") == proxy):
            print(f"face_retime: reusing {map_path}", file=sys.stderr)
            return d
        print(f"face_retime: {map_path} does not match this source / settings, solving again", file=sys.stderr)
    diff = proxy_diffs(src, proxy, pw, ph)
    N = len(diff)
    th = PARAMS[0]
    if ratio >= 1.5:
        U, fmap = solve(diff, ticks, ratio, *PARAMS)
        method = "dp"
    else:  # not a high-rate export: nothing to choose between, take the nearest frame like fps=30 does
        fmap = [min(N - 1, int(math.floor(k * ratio + 0.5))) for k in range(ticks)]
        method = "nearest"
    assert len(fmap) == ticks and all(b >= a for a, b in zip(fmap, fmap[1:])) and fmap[-1] < N, "bad frame map"
    plain = [min(N - 1, int(math.floor(k * ratio + 0.5))) for k in range(ticks)]
    d = {"tool": "face_retime.py", "src": os.path.abspath(src), "src_size": src_size, "src_frames": N,
         "src_fps": info["fps"], "duration": info["duration"], "fps": FPS_OUT, "ticks": ticks, "method": method,
         "params": PARAMS, "proxy": {"crop": proxy, "size": [pw, ph]},
         "stats": {"retime": map_stats(fmap, diff, th, ratio), "fps_filter": map_stats(plain, diff, th, ratio)},
         "map": fmap, "diff": [round(float(v), 4) for v in diff]}
    tmp = map_path + ".part"
    with open(tmp, "w") as f:
        json.dump(d, f)
    os.replace(tmp, map_path)
    return d


# ---------------------------------------------------------------------------------------------------------------- encode
def encode(src, info, fmap, crop, size, out):
    sw, sh = size
    if sw % 2 or sh % 2:
        raise SystemExit(f"{out}: yuv420p needs even dimensions, got {sw}x{sh}")
    fs = sw * sh * 3 // 2
    vf = f"{crop_vf(crop)}scale={sw}:{sh}"
    c = info["color"]
    tmp = out + ".part"
    dec = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-i", src, "-an", "-sn", "-dn", "-fps_mode", "passthrough",
                            "-vf", vf, "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"],
                           stdin=DEVNULL, stdout=subprocess.PIPE, bufsize=fs * 4)
    # colour tags are INPUT options on the raw pipe: as output options on an untagged pipe ffmpeg 8 inserts a BT.601 -> BT.709
    # matrix conversion (fixer v10 QA). Tagged on the input, the frames pass through untouched.
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p",
                            "-s", f"{sw}x{sh}", "-r", str(FPS_OUT), "-color_range", c["color_range"],
                            "-colorspace", c["colorspace"], "-color_trc", c["color_trc"],
                            "-color_primaries", c["color_primaries"], "-i", "-", "-an", "-c:v", "libx264", "-crf", "16",
                            "-g", "15", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-f", "mp4",
                            tmp], stdin=subprocess.PIPE)
    idx, buf, ok = -1, None, False
    try:
        for n, want in enumerate(fmap):
            while idx < want:
                b = dec.stdout.read(fs)
                if len(b) < fs:
                    raise SystemExit(f"{out}: decoder ended at source frame {idx} (tick {n} wants {want})")
                buf, idx = b, idx + 1
            enc.stdin.write(buf)
        enc.stdin.close()
        while len(dec.stdout.read(fs)) == fs:  # drain: the source can run a frame or two past the last tick
            pass
        dec.stdout.close()
        if dec.wait() != 0:
            raise SystemExit(f"{out}: decoder failed (exit {dec.returncode})")
        ok = True
    except BrokenPipeError:
        raise SystemExit(f"{out}: encoder exited early")
    finally:
        if dec.poll() is None:
            dec.kill()
            dec.wait()
        if not ok:  # leave no half-written file behind
            enc.kill()
            enc.wait()
            if os.path.exists(tmp):
                os.remove(tmp)
    if enc.wait() != 0:
        raise SystemExit(f"{out}: encoder failed (exit {enc.returncode})")
    got = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=nb_frames", "-of",
                          "csv=p=0", tmp], check=True, capture_output=True, text=True, stdin=DEVNULL).stdout.strip()
    if got != str(len(fmap)):
        raise SystemExit(f"{out}: wrote {got} frames, expected {len(fmap)}")
    os.replace(tmp, out)


# ---------------------------------------------------------------------------------------------------------------- cli
class _Job(argparse.Action):
    def __call__(self, parser, ns, values, option_string=None):
        seq = list(getattr(ns, "job_args", None) or [])
        seq.append((self.dest, values))
        setattr(ns, "job_args", seq)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("--map", required=True, help="frame map JSON to write")
    ap.add_argument("--proxy-crop", help="W:H:X:Y region for the unique-frame proxy (default: bounding box of the crops)")
    ap.add_argument("--reuse", action="store_true", help="reuse --map when it matches this source and settings")
    ap.add_argument("--crop", dest="crop", action=_Job, metavar="W:H:X:Y")
    ap.add_argument("--scale", dest="scale", action=_Job, metavar="WxH")
    ap.add_argument("--out", dest="out", action=_Job, metavar="FILE.mp4")
    a = ap.parse_args(argv)

    jobs, cur = [], {}
    for key, val in getattr(a, "job_args", None) or []:
        if key == "out":
            jobs.append((cur.get("crop"), cur.get("scale"), os.path.abspath(val)))
            cur = {}
        elif key in cur:
            ap.error(f"--{key} given twice before --out")
        else:
            cur[key] = val
    if cur:
        ap.error("--crop / --scale must be followed by --out")
    src = os.path.abspath(a.source)
    outs = [j[2] for j in jobs]
    if len(set(os.path.normcase(o) for o in outs)) != len(outs) or os.path.normcase(src) in map(os.path.normcase, outs):
        ap.error("outputs must be distinct and differ from the source")
    for o in outs:
        if os.path.exists(o) and os.stat(o).st_nlink > 1:
            raise SystemExit(f"refusing to overwrite {o}: it is hard-linked ({os.stat(o).st_nlink} links, a shared asset); "
                             "write a new file instead")

    info = probe(src)
    W, H = info["width"], info["height"]
    ticks = int(math.floor(info["duration"] * FPS_OUT + 0.5))
    parsed = []
    for crop, scale, out in jobs:
        try:
            c = parse_crop(crop) if crop else None
            cw, ch = (c[0], c[1]) if c else (W, H)
            if c and (c[0] + c[2] > W or c[1] + c[3] > H):
                raise ValueError(f"crop {crop} exceeds the {W}x{H} source")
            parsed.append((c, parse_scale(scale, cw, ch), out))
        except ValueError as e:
            ap.error(str(e))
    if a.proxy_crop:
        proxy = parse_crop(a.proxy_crop)
    elif parsed and all(c for c, _, _ in parsed):
        x0 = min(c[2] for c, _, _ in parsed)
        y0 = min(c[3] for c, _, _ in parsed)
        x1 = max(c[2] + c[0] for c, _, _ in parsed)
        y1 = max(c[3] + c[1] for c, _, _ in parsed)
        proxy = [x1 - x0, y1 - y0, x0, y0]
    else:
        proxy = [W, H, 0, 0]

    d = build_map(src, info, ticks, proxy, os.path.abspath(a.map), a.reuse)
    st = d["stats"]
    for label in ("fps_filter", "retime"):
        s = st[label]
        print(f"face_retime: {label:10s} ticks {s['ticks']}  held ticks {s['held_ticks']}  isolated holds "
              f"{s['isolated_holds']}  skipped uniques {s['skipped_uniques']} of {s['uniques']}  offset ticks mean "
              f"{s['offset_ticks']['mean']:+.3f} p5 {s['offset_ticks']['p5']:+.1f} p95 {s['offset_ticks']['p95']:+.1f}",
              file=sys.stderr)
    print(f"face_retime: map -> {os.path.abspath(a.map)} ({d['method']}, {d['src_frames']} source frames at "
          f"{d['src_fps']:g} fps)", file=sys.stderr)
    for c, size, out in parsed:
        encode(src, info, d["map"], c, size, out)
        print(f"face_retime: wrote {out} {size[0]}x{size[1]} {len(d['map'])} frames", file=sys.stderr)


if __name__ == "__main__":
    main()
