"""Definitions every beat tool shares. CONTRACT.md section 0: these live here and nowhere else."""
import hashlib, json, math


def canon(x):
    """Same form as sound_mix.py's plan hash."""
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(x):
    """x is a str or a JSON value."""
    return hashlib.sha256((x if isinstance(x, str) else canon(x)).encode("utf8")).hexdigest()


def frame_of(t, fps):
    """First frame on which a change at t shows: timeline.js's A(t) on the frame grid. Never use round() for a frame."""
    return 0 if t <= 0 else math.ceil((t - 0.004) * fps - 1e-6)


def source_frame_time(t, source_fps=30):
    """Beat cuts stay on the source grid at every output rate. At source fps this is exactly frame_of(t)."""
    return frame_of(t, source_fps) / source_fps


def overlaps(frames, beat):
    """True if any half-open interval in frames meets the beat's own half-open range."""
    return any(a < beat["end_frame"] and beat["start_frame"] < b for a, b in frames)
