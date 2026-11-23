#!/usr/bin/env python3
"""Checks that every BIG join of the cut sits on a scene change (CARD.md: within 0.3 s), after `node tools/build.mjs`.

  python templates/charcoal/build_kit/joins_check.py work/<id>

Reads the BIG joins from `tools/rawcut.py times work/<id>/raw` and the scene starts from full/tools/slices.json.
Prints each join that no scene change covers, with the nearest one, and exits 1 if there is any. It also lists every
join (big or small) with a scene that starts 1 to 12 frames AFTER it: for those frames the old shot shows the new
footage (1113-nod: six frames of his desktop under the wrong shot). Start such a scene with at(), which snaps to the join. It needs no rendered
picture, so it runs on a --quick project while Chase is still listening to the cut. A join inside a stretch of his
full-frame face or one screen shot is fixed by starting a new shot there (a new entry in shots()).
"""
import json, re, subprocess, sys
from pathlib import Path

SHORTS = Path(__file__).resolve().parents[3]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    H = Path(sys.argv[1]).resolve()
    out = subprocess.run([sys.executable, str(SHORTS / "tools" / "rawcut.py"), "times", str(H / "raw")], capture_output=True, text=True).stdout
    big = [(float(m.group(1)), m.group(2)) for m in re.finditer(r"^\s*([\d.]+)\s+BIG\s+\S+\s+removed\s+[\d.]+s\s+(.*)$", out, re.M)]
    f = H / "full" / "tools" / "slices.json"
    if not f.is_file():
        sys.exit(f"{f} is missing: run node tools/build.mjs in {H / 'full'} first (a full build, not --sections)")
    sl = json.loads(f.read_text(encoding="utf8"))
    starts = sorted(s["frame0"] / 30 for s in (sl["slices"] if isinstance(sl, dict) else sl))
    bad = [(t, x) for t, x in big if min(abs(t - s) for s in starts) > 0.3]
    print(f"{len(big)} BIG joins, {len(bad)} not on a scene change")
    for t, x in bad:
        print(f"  {t:8.2f}  {x[:70]}   nearest scene change {min(starts, key=lambda s: abs(s - t)):.2f}")
    edl = json.loads((H / "raw" / "edl.json").read_text(encoding="utf8"))
    f0 = sorted(s["frame0"] for s in (sl["slices"] if isinstance(sl, dict) else sl))
    late, t = [], 0.0
    for a, b in edl["keeps"][:-1]:
        t += (b - a) / edl["fps"]
        jf = -int(-(t * 30 - 1e-6) // 1)                             # the first project frame that shows footage after the join
        nxt = [g for g in f0 if 0 < g - jf <= 12]
        if jf not in f0 and nxt:
            late.append((t, jf, nxt[0]))
    print(f"{len(edl['keeps']) - 1} joins, {len(late)} with a scene that starts a few frames late")
    for t, jf, g in late:
        print(f"  {t:8.2f}  join on frame {jf}, scene starts on frame {g} ({g - jf} frames late): use at() or joinNear()")
    sys.exit(1 if bad or late else 0)


if __name__ == "__main__":
    main()
