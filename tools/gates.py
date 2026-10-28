"""Mechanical quality gates on an ENCODED render (run after every render; also run on donor reels to set targets).

Usage: python gates.py <video.mp4> [--band 0,0,1080,930] [--json out.json] [--max-frozen-per-30 1.0] [--max-hold 1.5]

Checks
  frozen band   graphics band sampled at 10 fps; a sample is "static" when the mean frame-to-frame luma change < 0.35.
                Reports static seconds per 30 s and the longest continuous hold.
  freezes       ffmpeg freezedetect on the band (n=0.003, d=0.6 s).
  black         ffmpeg blackdetect on the full frame (d=0.1 s).
  layout        split <-> full-graphic <-> full-face switches, detected as cuts in the face band (y 1010-1920: a cut moves
                its mean frame-to-frame luma change by 40-220, talking stays < 20). Reports switches per 30 s and the
                longest run in one layout (reference only; editorial warns softly on a run over 8 s - switching follows the content).
  loudness      EBU R128 integrated LUFS + true peak on the encoded audio; target -14 +/-1 LUFS, TP <= -1.5 dBTP.
  audio stream  sample rate / channels (catches a 16 kHz mono scratch track muxed by mistake).
Exit code: 0 pass, 1 pass with warnings, 2 fail.
"""
import argparse
import json
import re
import subprocess
import sys

# (static seconds per 30 s, longest hold s) - measured donor targets, styles/CALIBRATION.md
PACK_TARGETS = {"saraev": (3.5, 1.5), "editorial": (8.0, 2.5), "signal": (3.0, 1.2)}
# longest run in one layout (s) before a soft warning - editorial (author's call, 2026-10-23): switching follows the content
# (styles/editorial/STYLE.md house rule 1), so there is no switch quota; the count is reported for reference only
# (reference A ~9 / 30 s, reference B ~2.3, our first editorial finals 3.6-3.75 with a 27 s opening split)
LAYOUT_TARGETS = {"editorial": 8.0}
CUT_THRESHOLD = 30.0


def ff(args):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats"] + args, capture_output=True, text=True).stderr


def band_motion(video, band):
    x, y, w, h = band
    out = ff(["-i", video, "-an", "-vf", f"crop={w}:{h}:{x}:{y},fps=10,scale=320:-2,format=gray,tblend=all_mode=difference,"
              "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-", "-f", "null", "-"])
    vals = [float(v) for v in re.findall(r"lavfi\.signalstats\.YAVG=([0-9.]+)", out)]
    if not vals:  # metadata=print to file=- goes to stdout on some builds
        res = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", video, "-an", "-vf",
                              f"crop={w}:{h}:{x}:{y},fps=10,scale=320:-2,format=gray,tblend=all_mode=difference,"
                              "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-", "-f", "null", "-"],
                             capture_output=True, text=True)
        vals = [float(v) for v in re.findall(r"lavfi\.signalstats\.YAVG=([0-9.]+)", res.stdout + res.stderr)]
    return vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--band", default="0,0,1080,930")
    ap.add_argument("--json")
    ap.add_argument("--max-frozen-per-30", type=float, default=1.0)
    ap.add_argument("--max-hold", type=float, default=1.5)
    ap.add_argument("--pack", help="use the measured per-pack targets from styles/CALIBRATION.md")
    a = ap.parse_args()
    if a.pack in PACK_TARGETS:
        a.max_frozen_per_30, a.max_hold = PACK_TARGETS[a.pack]
    band = list(map(int, a.band.split(",")))
    report = {"video": a.video, "band": band, "findings": []}

    def finding(sev, check, msg):
        report["findings"].append({"severity": sev, "check": check, "msg": msg})

    probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                       "stream=codec_type,sample_rate,channels:format=duration", "-of", "json", a.video],
                                      capture_output=True, text=True).stdout)
    dur = float(probe["format"]["duration"])
    report["duration"] = dur
    audio = [s for s in probe["streams"] if s["codec_type"] == "audio"]
    if not audio:
        finding("CRITICAL", "audio", "no audio stream")
    else:
        sr, ch = int(audio[0].get("sample_rate", 0)), int(audio[0].get("channels", 0))
        report["audio"] = {"sample_rate": sr, "channels": ch}
        if sr < 44100 or ch < 2:
            finding("HIGH", "audio", f"suspicious audio stream {sr} Hz / {ch} ch (scratch track muxed?)")

    vals = band_motion(a.video, band)
    static = [v < 0.35 for v in vals]
    longest = run = 0
    holds = []
    for i, s in enumerate(static):
        run = run + 1 if s else 0
        if run == 1:
            start = i
        if s and run > longest:
            longest = run
        if not s and i and static[i - 1]:
            holds.append((start / 10, i / 10))
    frozen_s = sum(static) / 10
    per30 = frozen_s / max(dur, 1e-6) * 30
    report["band"] = {"samples": len(vals), "static_seconds": round(frozen_s, 2), "static_per_30s": round(per30, 2),
                      "longest_hold_s": longest / 10,
                      "holds_over_max": [h for h in holds if h[1] - h[0] > a.max_hold]}
    if per30 > a.max_frozen_per_30:
        finding("HIGH", "frozen-band", f"{per30:.2f}s static per 30s in the graphics band (max {a.max_frozen_per_30})")
    if longest / 10 > a.max_hold:
        finding("MEDIUM", "hold", f"longest static hold {longest / 10:.1f}s (max {a.max_hold}s)")

    lv = band_motion(a.video, [0, 1010, 1080, 910])
    cuts = []
    for i, v in enumerate(lv):
        if v > CUT_THRESHOLD and (not cuts or i / 10 - cuts[-1] >= 0.5):
            cuts.append(round(i / 10, 1))
    edges = [0.0] + cuts + [dur]
    runs = [round(b - e, 1) for e, b in zip(edges, edges[1:])]
    sw30 = len(cuts) / max(dur, 1e-6) * 30
    report["layout"] = {"switches": cuts, "switches_per_30s": round(sw30, 2), "longest_run_s": max(runs) if runs else dur}
    if a.pack in LAYOUT_TARGETS and max(runs) > LAYOUT_TARGETS[a.pack]:
        i = runs.index(max(runs))
        finding("MEDIUM", "layout-run", f"{max(runs):.1f}s in one layout ({edges[i]:.1f}-{edges[i + 1]:.1f}s) - look for a "
                f"line there that earns a takeover or a punch-in (soft guardrail {LAYOUT_TARGETS[a.pack]}s)")

    x, y, w, h = band
    fz = ff(["-i", a.video, "-an", "-vf", f"crop={w}:{h}:{x}:{y},freezedetect=n=0.003:d=0.6", "-f", "null", "-"])
    freezes = re.findall(r"freeze_start: ([0-9.]+).*?freeze_end: ([0-9.]+)", fz.replace("\n", " "))
    report["freezes"] = [(float(s), float(e)) for s, e in freezes]
    for s, e in report["freezes"]:
        finding("MEDIUM", "freeze", f"band frozen {float(s):.2f}-{float(e):.2f}s")

    bd = ff(["-i", a.video, "-an", "-vf", "blackdetect=d=0.1:pix_th=0.05", "-f", "null", "-"])
    blacks = re.findall(r"black_start:([0-9.]+) black_end:([0-9.]+)", bd)
    report["black"] = [(float(s), float(e)) for s, e in blacks]
    for s, e in report["black"]:
        finding("CRITICAL", "black", f"black frames {s}-{e}s")

    if audio:
        eb = ff(["-i", a.video, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"])
        m_i = re.findall(r"I:\s+(-?[0-9.]+) LUFS", eb)
        m_tp = re.findall(r"Peak:\s+(-?[0-9.]+) dBFS", eb)
        lufs = float(m_i[-1]) if m_i else None
        tp = float(m_tp[-1]) if m_tp else None
        report["loudness"] = {"lufs": lufs, "true_peak": tp}
        if lufs is not None and abs(lufs + 14) > 1:
            finding("MEDIUM", "loudness", f"integrated {lufs} LUFS (target -14 +/-1; run finish.py)")
        if tp is not None and tp > -1.5:
            finding("MEDIUM", "true-peak", f"true peak {tp} dBTP (max -1.5)")

    sev = [f["severity"] for f in report["findings"]]
    report["verdict"] = "FAIL" if ("CRITICAL" in sev or "HIGH" in sev) else ("PASS_WITH_WARNINGS" if sev else "PASS")
    out = json.dumps(report, indent=1)
    if a.json:
        open(a.json, "w").write(out)
    print(out)
    sys.exit({"PASS": 0, "PASS_WITH_WARNINGS": 1, "FAIL": 2}[report["verdict"]])


if __name__ == "__main__":
    main()
