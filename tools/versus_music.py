"""Subtle instrumental bed rendered offline in numpy (no samples, no services, nothing to license): warm detuned pad,
sine sub, soft plucked arpeggio, light reverb. Used by tools/versus.py music; also runs on its own.

  python tools/versus_music.py <out.wav> [--secs 18] [--bpm 84] [--seed 7]
"""
import argparse
import wave

import numpy as np

SR = 48000
A4 = 440.0
# Fmaj7 - Am7 - Dm9 - Cmaj7 (voiced mid-low, soft): (notes, sub root)
CHORDS = [([53, 57, 60, 64], 41), ([57, 60, 64, 67], 45), ([50, 57, 60, 64, 65], 38), ([48, 55, 59, 64], 36)]


def hz(m):
    return A4 * 2 ** ((m - 69) / 12)


def lowpass(x, cut):
    """One-pole low-pass run twice (gentle 12 dB/oct), as a convolution with its impulse response cut at -140 dB."""
    a = np.exp(-2 * np.pi * cut / SR)
    k = int(np.ceil(np.log(1e-7) / np.log(a)))
    h = (1 - a) * a ** np.arange(k)
    for _ in range(2):
        x = np.convolve(x, h)[:len(x)]
    return x


def env(n, att, rel):
    e = np.ones(n); a = int(att * SR); r = int(rel * SR)
    e[:a] = np.linspace(0, 1, a) ** 2
    e[-r:] *= np.linspace(1, 0, r) ** 1.5
    return e


def saw(f, t, ph):
    return 2 * ((f * t + ph) % 1.0) - 1


def synth(secs, bpm=84, seed=7):
    """(L, R) float arrays at 48 kHz, peak 0.5, faded in over 1.5 s and out over 2.5 s."""
    rng = np.random.default_rng(seed)
    beat = 60 / bpm; bar = 4 * beat
    n = int(secs * SR); L = np.zeros(n); R = np.zeros(n)
    t_bar = np.arange(int(bar * SR)) / SR
    k = 0; pos = 0
    while pos < n:
        notes, root = CHORDS[k % len(CHORDS)]
        m = min(len(t_bar), n - pos); t = t_bar[:m]
        e = env(m, min(0.9, m / SR / 3), min(0.9, m / SR / 3))
        padL = sum(saw(hz(p) * 0.997, t, rng.random()) + saw(hz(p) * 1.004, t, rng.random()) for p in notes)
        padR = sum(saw(hz(p) * 1.002, t, rng.random()) + saw(hz(p) * 0.995, t, rng.random()) for p in notes)
        sub = np.sin(2 * np.pi * hz(root) * t) * env(m, min(0.3, m / SR / 3), min(0.6, m / SR / 3))
        L[pos:pos + m] += 0.05 * padL * e + 0.22 * sub
        R[pos:pos + m] += 0.05 * padR * e + 0.22 * sub
        for j in range(8):                                   # plucked arpeggio, 8th notes, an octave up
            s = pos + int(j * beat / 2 * SR)
            if s >= n:
                break
            p = notes[[0, 1, 2, 3, 2, 1, 3, 2][j] % len(notes)] + 12
            d = int(0.9 * SR); tt = np.arange(min(d, n - s)) / SR
            pl = (np.sin(2 * np.pi * hz(p) * tt) + 0.25 * np.sin(4 * np.pi * hz(p) * tt)) * np.exp(-tt * 5.5)
            pan = 0.35 + 0.3 * (j % 2)
            L[s:s + len(tt)] += 0.07 * pl * (1 - pan); R[s:s + len(tt)] += 0.07 * pl * pan
        pos += m; k += 1
    L = lowpass(L, 1500); R = lowpass(R, 1500)
    ir_n = int(1.8 * SR); it = np.arange(ir_n) / SR             # reverb: decaying-noise impulse, different per side
    out = []
    for x, sd in ((L, 1), (R, 2)):
        ir = np.random.default_rng(sd).standard_normal(ir_n) * np.exp(-it * 3.2); ir[0] = 0
        wet = np.fft.irfft(np.fft.rfft(x, n + ir_n) * np.fft.rfft(ir, n + ir_n))[:n]
        out.append(0.8 * x + 0.03 * wet)
    L, R = out
    fade = env(n, min(1.5, secs / 4), min(2.5, secs / 4)); L *= fade; R *= fade
    peak = max(np.abs(L).max(), np.abs(R).max(), 1e-9)
    return L / peak * 0.5, R / peak * 0.5


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--secs", type=float, default=18)
    ap.add_argument("--bpm", type=float, default=84); ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    L, R = synth(a.secs, a.bpm, a.seed)
    pcm = (np.stack([L, R], 1) * 32767).astype(np.int16)
    with wave.open(a.out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    print(f"wrote {a.out}: {a.secs:.1f}s at {a.bpm:g} bpm")


if __name__ == "__main__":
    main()
