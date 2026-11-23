#!/usr/bin/env python3
"""The stills storyboard Chase approves graphics from, before anything is rendered ([Chase] 2026-11-11).

  python templates/charcoal/build_kit/storyboard.py work/<id> [--name storyboard-v1]

Reads work/<id>/storyboard/<name>.json and writes work/<id>/storyboard/<name>.html: one row per graphic, numbered, with
stills from the build (a snapshot of the page, not a render), what he says there, what is on screen, and which on-screen
words are not his. Self-contained (stills embedded), so the one file can be sent to him.

  { "title": "Storyboard: graphics for the face-only stretches",
    "lead":  "Stills from the build. Tell me which to keep, change or drop, by number.",
    "rows": [ { "title": "Words vs pictures",
                "at": [196.5, 201, 206.8],            seconds of today's video to take stills at (after a full build)
                "say": "the line he speaks there, verbatim from raw/edit.txt",
                "screen": "what happens on screen, in order",
                "wording": "every on-screen word that is not his, or 'all his'",
                "when": "3:09 - 3:27"                 optional: default is the first and last `at`
                "stills": ["a/file.png"]              optional: ready-made images instead of `at`, relative to the storyboard folder
              } ] }

Run `node tools/build.mjs` in work/<id>/full first: the stills come from that page. A row's scene must be built (its
section file written); the rest of the video can still be missing (build with --partial).
"""
import argparse, base64, html, json, subprocess, sys
from pathlib import Path


def stamp(t):
    return f"{int(t) // 60}:{int(t) % 60:02d}"


def name_at(t):
    return f"at-{('%.3f' % t).rstrip('0').rstrip('.')}s.png"       # the name `hyperframes snapshot --keep` gives a still


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", help="work/<id>"); ap.add_argument("--name", default="storyboard-v1")
    a = ap.parse_args()
    H = Path(a.run).resolve(); SB = H / "storyboard"; spec_file = SB / f"{a.name}.json"
    if not spec_file.is_file():
        sys.exit(f"{spec_file} is missing: write it first (format at the top of this file)")
    spec = json.loads(spec_file.read_text(encoding="utf8")); rows = spec["rows"]
    times = sorted({t for r in rows for t in r.get("at", [])})
    stills = SB / "stills" / a.name
    if times:
        stills.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(f'npx hyperframes snapshot --at {",".join(str(t) for t in times)} --no-end --keep -o "{stills}"', cwd=H / "full", shell=True, capture_output=True, text=True)
        missing = [t for t in times if not (stills / name_at(t)).is_file()]
        if r.returncode and not missing:      # every still was written: e.g. a footage-only scene whose clip file is not made
            print("snapshot exited non-zero but wrote every still; a still of a footage-only scene may be blank (make_clips.py --all makes those clips)")
        if missing:
            sys.exit(f"snapshot failed (missing stills for {missing}):\n" + (r.stdout + r.stderr)[-1200:])

    def img(p):
        jpg = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vf", "scale=960:-2", "-q:v", "4", "-f", "mjpeg", "-"], capture_output=True, check=True).stdout
        return "data:image/jpeg;base64," + base64.b64encode(jpg).decode()

    e = html.escape; out_rows = []
    for n, r in enumerate(rows, 1):
        at = r.get("at", [])
        files = [stills / name_at(t) for t in at] + [SB / s for s in r.get("stills", [])]
        when = r.get("when") or (f"{stamp(at[0])} - {stamp(at[-1])}" if len(at) > 1 else stamp(at[0]) if at else "")
        out_rows.append(f"""
<section>
  <header><span class="n">{n}</span><h2>{e(r['title'])}</h2><span class="t">{e(when)}</span></header>
  <div class="imgs">{''.join(f'<img src="{img(f)}" alt="">' for f in files)}</div>
  <dl><dt>You say</dt><dd>{e(r.get('say', ''))}</dd><dt>On screen</dt><dd>{e(r.get('screen', ''))}</dd><dt>Wording</dt><dd>{e(r.get('wording', ''))}</dd></dl>
</section>""")
    title = spec.get("title", f"{H.name} storyboard")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(H.name)} {e(a.name)}</title>
<style>
:root{{--bg:#f6f4ef;--ink:#1a1917;--mut:#6b675f;--line:#d9d5cb;--acc:#d9481c}}
@media (prefers-color-scheme:dark){{:root{{--bg:#1a1917;--ink:#ebe8e0;--mut:#aaa69d;--line:#423f3b;--acc:#ff7a50}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,sans-serif}}
main{{max-width:1040px;margin:0 auto;padding:28px 16px 60px}}
h1{{font-size:26px;margin:0 0 6px}} p.lead{{color:var(--mut);margin:0 0 26px;max-width:70ch}}
section{{border-top:1px solid var(--line);padding:22px 0}}
header{{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:12px}}
.n{{font:600 14px/1 ui-monospace,monospace;color:var(--bg);background:var(--acc);padding:5px 8px}}
h2{{font-size:19px;margin:0}} .t{{color:var(--mut);font:14px ui-monospace,monospace}}
.imgs{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px;margin-bottom:12px}}
.imgs img{{display:block;width:100%;height:auto;border:1px solid var(--line)}}
dl{{display:grid;grid-template-columns:90px 1fr;gap:6px 14px;margin:0}} dt{{color:var(--mut);font-size:14px}} dd{{margin:0}}
@media (max-width:560px){{dl{{grid-template-columns:1fr}}}}
</style></head><body><main>
<h1>{e(title)}</h1>
<p class="lead">{e(spec.get('lead', 'Stills from the build. Times are in the current video. Tell me which to keep, change or drop, by number.'))}</p>
{''.join(out_rows)}
</main></body></html>"""
    out = SB / f"{a.name}.html"
    out.write_text(page, encoding="utf8")
    print(out, f"{out.stat().st_size / 1e6:.1f} MB, {len(rows)} rows, {len(times)} stills taken")


if __name__ == "__main__":
    main()
