"""Output detector: compares sampled frames of a rendered file to validated reference captures. CONTRACT.md section 6.

Frames pair by decoded frame number, never by timestamp, because a file re-muxed through a millisecond step reads as false differences otherwise.
Sampling cannot clear every frame. Every frame is screened for the observed fault's one signature, and a suspect joins the sample. Anything else
that lasts less than the gap between samples can pass, and each report says how many frames were not compared.
A whole-frame number averages a small change away, so each compared frame also has its worst block measured. A wrong word in a small label scores 36 dB whole and fails only there.
"""
import hashlib, json, subprocess, tempfile
from pathlib import Path
import numpy as np

from common import overlaps

PSNR_MIN = 34.0  # qualified on clean reruns against injected faults, see stage1/phase2-renderer.md
BLOCK_PX = 48  # at 1080 wide. Scaled with the frame, so a block covers the same part of the picture at every profile
BLOCK_MAX = 10.0  # largest mean absolute luma difference, 0 to 255, on any block. Clean worst 5.41 review, 3.36 final. Lowest planted wrong word 20.83, 18.52. See stage1/phase2-fixes.md
REGION_TOP = 960  # the face half, at 1080x1920
# The observed fault paints the composition only inside the top left 800x600 of a 1080x1920 frame. Past those edges everything is page background.
CLIP_RIGHT, CLIP_BOTTOM = 0.75, 0.32
FLAT_RANGE = 6
# What HyperFrames' encoder does to a capture (SDR_CAPTURE_TO_BT709_FILTER, unchanged from 0.8.184 to 0.9.13), so a clean comparison measures the encoder and no colour step.
STILL_FILTER = "scale=in_color_matrix=bt601:in_range=pc:flags=neighbor+accurate_rnd,format=gbrp,scale=out_color_matrix=bt709:out_range=tv:flags=neighbor"


def frame_bytes(width, height):
    return width * height * 3 // 2


def scan(path, width, height, wanted=(), keep_suspects=0):
    """Decodes every frame of path as yuv420p. Returns its framemd5 rows, the wanted frames' bytes and the frames that look clipped. Those keep their bytes too, up to keep_suspects."""
    size = frame_bytes(width, height)
    wanted = set(wanted)
    rows, picked, suspects = [], {}, []
    n = 0
    # passthrough, or rawvideo's default constant rate pads a gap and the count is no longer what decoded. stderr goes to a file, or a damaged file fills its pipe and ffmpeg never finishes
    with tempfile.TemporaryFile() as log:
        with subprocess.Popen(["ffmpeg", "-v", "error", "-threads", "2", "-i", str(path), "-map", "0:v:0", "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"], stdout=subprocess.PIPE, stderr=log) as p:
            while True:
                data = p.stdout.read(size)
                if len(data) < size:
                    break
                rows.append(hashlib.md5(data).hexdigest())
                if n in wanted:
                    picked[n] = data
                if clipped(data, width, height):
                    suspects.append(n)
                    if len(suspects) <= keep_suspects:
                        picked[n] = data
                n += 1
        log.seek(0, 2)
        log.seek(max(0, log.tell() - 2000))
        err = log.read()
    if p.returncode or data:
        raise RuntimeError(f"decode of {path} failed: {err.decode(errors='replace')} trailing bytes {len(data)}")
    return rows, picked, suspects


def luma(data, width, height):
    return np.frombuffer(data, dtype=np.uint8, count=width * height).reshape(height, width)


def clipped(data, width, height):
    y = luma(data, width, height)
    below = y[int(height * CLIP_BOTTOM):, ::4]
    right = y[::4, int(width * CLIP_RIGHT):]
    return int(below.max()) - int(below.min()) <= FLAT_RANGE and int(right.max()) - int(right.min()) <= FLAT_RANGE


def psnr(a, b, width, height, top=0):
    """Plane-weighted PSNR, as ffmpeg's psnr_avg. top is a luma row: the region from it down to the last row."""
    top -= top % 2
    aa, bb = np.frombuffer(a, dtype=np.uint8), np.frombuffer(b, dtype=np.uint8)
    if aa.size != bb.size or aa.size != frame_bytes(width, height):
        raise ValueError("frames differ in size")
    y_end = width * height
    chroma = (width // 2) * (height // 2)
    start = (top // 2) * (width // 2)
    keep = [(top * width, y_end), (y_end + start, y_end + chroma), (y_end + chroma + start, y_end + 2 * chroma)]
    x = np.concatenate([aa[s:e] for s, e in keep]).astype(np.int32)
    w = np.concatenate([bb[s:e] for s, e in keep]).astype(np.int32)
    mse = float(np.mean((x - w) ** 2))
    return 99.0 if mse == 0 else min(99.0, 10 * float(np.log10(255 ** 2 / mse)))


def worst_block(a, b, width, height, size=None):
    """Largest mean absolute luma difference over any block, on a half-block grid, so a word on a block edge is not split in two."""
    size = size or max(8, round(BLOCK_PX * width / 1080))
    d = np.abs(luma(a, width, height).astype(np.int32) - luma(b, width, height).astype(np.int32))
    total = np.zeros((height + 1, width + 1), dtype=np.int64)
    total[1:, 1:] = d.cumsum(0).cumsum(1)
    step = max(1, size // 2)
    ys, xs = np.arange(0, height - size + 1, step), np.arange(0, width - size + 1, step)
    s = total[np.ix_(ys + size, xs + size)] - total[np.ix_(ys, xs + size)] - total[np.ix_(ys + size, xs)] + total[np.ix_(ys, xs)]
    return float(s.max()) / (size * size)


def decode_stills(paths, width, height):
    """Reference stills, through the same decoder the encoder's input goes through."""
    if not paths:
        return []
    r = subprocess.run(["ffmpeg", "-v", "error", "-f", "image2pipe", "-vcodec", "mjpeg", "-i", "pipe:0", "-vf", STILL_FILTER, "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"],
                       input=b"".join(Path(p).read_bytes() for p in paths), capture_output=True)
    size = frame_bytes(width, height)
    if r.returncode or len(r.stdout) != size * len(paths):
        raise RuntimeError(f"reference decode failed: {r.stderr.decode(errors='replace')[-2000:]}")
    return [r.stdout[i * size:(i + 1) * size] for i in range(len(paths))]


def receipt_valid(receipt, first_frame=None):
    """A page can keep what a frame it landed on did, so a reference counts only if it reached its frame as a render does, stepping from the beat's first frame."""
    if not receipt or receipt.get("problems") or receipt.get("stepped_from") is None:
        return False
    return first_frame is None or receipt["stepped_from"] == first_frame


def load_stills(folder, frames, width, height):
    """Decoded references from a refs folder, frame number to bytes. None for a frame with no valid one: no receipt, a failed DOM probe, a reference that was not stepped from its beat's
    first frame, or one that is itself clipped."""
    usable = []
    for frame in frames:
        path = Path(folder) / f"{frame}.jpg"
        try:
            receipt = json.loads(Path(str(path) + ".json").read_text(encoding="utf8"))
        except (OSError, ValueError):
            continue
        if path.is_file() and receipt_valid(receipt):
            usable.append((frame, path))
    out = {frame: None for frame in frames}
    for (frame, _), data in zip(usable, decode_stills([p for _, p in usable], width, height)):
        if not clipped(data, width, height):
            out[frame] = data
    return out


def samples(beat, events=()):
    """First, middle and last frame of a beat, plus each event frame inside it. Global frame numbers."""
    a, b = beat["start_frame"], beat["end_frame"]
    picked = {a, (a + b - 1) // 2, b - 1}
    picked.update(e["frame"] for e in events if a <= e["frame"] < b)
    return sorted(picked)


def expected(frame, beat, m):
    """What the DOM probe must see on this frame of this beat, from the ownership map."""
    chips = [o["id"] for o in m["owners"] if o["kind"] == "caption" and overlaps(o["frames"], {"start_frame": frame, "end_frame": frame + 1})]
    return {"layout": beat["layout"], "chips": chips, "face": "ff-" + beat["beat_id"] if beat["layout"] == "full-face" else None}


def compare(picked, stills, frames, width, height, region_top, minimum=PSNR_MIN, block_max=BLOCK_MAX):
    """picked: frame number to decoded bytes. stills: frame number to decoded reference bytes, or None for an invalid reference.

    Returns a sentinel record for those frames. A failed frame is FAIL. A frame with no valid reference leaves the rest UNVERIFIED.
    """
    failed, unverified, whole, region, blocks = [], [], [], [], []
    for frame in frames:
        still = stills.get(frame)
        if still is None:
            unverified.append(frame)
            continue
        w, r, k = psnr(picked[frame], still, width, height), psnr(picked[frame], still, width, height, region_top), worst_block(picked[frame], still, width, height)
        whole.append(w)
        region.append(r)
        blocks.append(k)
        if w < minimum or r < minimum or k > block_max:
            failed.append({"frame": frame, "psnr": round(w, 2), "psnr_region": round(r, 2), "block": round(k, 2)})
    status = "FAIL" if failed else "UNVERIFIED" if unverified or not whole else "PASS"
    return {"status": status, "sampled": list(frames), "failed": failed, "unverified": unverified,
            "min_psnr": round(min(whole), 2) if whole else None, "min_psnr_region": round(min(region), 2) if region else None, "psnr_min": minimum,
            "max_block": round(max(blocks), 2) if blocks else None, "block_max": block_max}
