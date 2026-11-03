#!/usr/bin/env python3
"""Generates ../index.html from plan.json, style.css, scenes.py and timeline.js. Then beats.lock.json, ownership.json and events.json, without which run.py refuses the project.

From templates/ivory/build_kit/. The README there says what a project writes, and what each build stop means.
"""
import json, math, os, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ED = HERE.parent
ROOT = ED.parent.parent
sys.path.insert(0, str(HERE))
sys.path.append(str(ROOT.parent.parent / "tools" / "beat_render"))
sys.path.append(str(ROOT.parent.parent / "tools" / "beat_check"))
import scenes, owners
import confine, events, lock, ownership
from common import frame_of, source_frame_time

# tools/beat_review/final.py edits this line for a 60 fps derivative, with data-fps below, two lines in scenes.py and one in timeline.js
FPS = 30
LAYOUTS = ("split", "full-graphic", "full-face")
POS = {"seam": 912, "takeover": 1477, "fullface": 1640}
SOURCES = ["tools_local/build.py", "tools_local/scenes.py", "tools_local/timeline.js", "tools_local/style.css", "tools_local/owners.py"]
GUIDE = "templates/ivory/build_kit/README.md"
CHIP_LEAD = 5  # frames a chip may open ahead of its first word. tools/beat_check/conform.py CHIP_LEAD_FRAMES


def stop(problems):
    """Nothing is written, and any map from an earlier build goes, so run.py cannot take this project for built."""
    (ED / ownership.NAME).unlink(missing_ok=True)
    sys.exit("BUILD STOPPED\n" + "\n".join(f"  {p}" for p in problems) + f"\nFix these in plan.json or tools_local, never in index.html. {GUIDE} says what each one means.")


def plan_problems(plan, end):
    """What this build needs from plan.json, in words a builder can act on."""
    problems = [f'plan.json has no "{k}"' for k in ("duration", "beats", "captions", "cta_start", "composition_files") if k not in plan]
    if problems:
        return problems
    if type(plan["duration"]) not in (int, float) or not math.isfinite(plan["duration"]) or plan["duration"] != end:
        problems.append(f"plan.json duration must equal metadata.json duration {end}, got {plan['duration']!r}")
    if not isinstance(plan.get("allow_full_face"), bool):
        problems.append("plan.json allow_full_face must be a JSON Boolean")
    if "allow_full_face_source" not in plan:
        problems.append('plan.json has no "allow_full_face_source"')
    if plan["composition_files"] != SOURCES:
        problems.append(f"plan.json composition_files must be {SOURCES}")
    for b in plan["beats"]:
        where = b.get("id", "a beat")
        problems += [f'{where} has no "{k}"' for k in ("id", "start", "end", "say", "layout", "anchor", "sub_anchors", "actions", "proof_span") if k not in b]
        if b.get("layout") not in LAYOUTS:
            problems.append(f"{where} has layout {b.get('layout')!r}, not one of {LAYOUTS}")
        if b.get("layout") == "full-face" and plan.get("allow_full_face") is not True:
            problems.append(f"{where} is full-face, and allow_full_face is not true")
        rows = [b.get("anchor")] + b.get("sub_anchors", []) + b.get("actions", [])
        problems += [f"{where} has an event with no event_id" for e in rows if not isinstance(e, dict) or not e.get("event_id")]
    if plan["beats"] and plan["beats"][-1].get("end") != end:
        problems.append(f"the last beat ends at {plan['beats'][-1].get('end')}, and metadata.json's duration is {end}")
    for c in plan["captions"].get("chunks", []):
        problems += [f'caption chunk {c.get("text")!r} has no "{k}"' for k in ("beat", "text", "words", "on", "off", "position") if k not in c]
        if c.get("position") not in POS:
            problems.append(f"caption chunk {c.get('text')!r} has position {c.get('position')!r}, not one of {list(POS)}")
    return problems


def layout_runs(beats):
    """Runs of one layout, from the beats, so the page and the lock cannot disagree."""
    runs = []
    for b in beats:
        if runs and runs[-1][2] == b["layout"]:
            runs[-1][1] = b["end"]
        else:
            runs.append([b["start"], b["end"], b["layout"]])
    return runs


meta = json.loads((ROOT / "metadata.json").read_text(encoding="utf8"))
words = json.loads((ROOT / "words.json").read_text(encoding="utf8"))
END = meta["duration"]
plan = json.loads((ED / "plan.json").read_text(encoding="utf8"))
found = plan_problems(plan, END)
if found:
    stop(found)
try:
    beat_lock = lock.write(ED, plan, END, FPS)
except ValueError as e:
    stop([e])


# ---- face layers: full-face beats only. Plan says none unless a template or Chase turned them on
runs = layout_runs(plan["beats"])
face_vids = []
for b in plan["beats"]:
    if b["layout"] != "full-face":
        continue
    f0, f1 = frame_of(source_frame_time(b["start"]), FPS), frame_of(source_frame_time(b["end"]), FPS)
    start = math.floor(f0 / FPS * 1e5) / 1e5
    media = math.ceil(f0 / FPS * 1e4) / 1e4
    dur = (END - start) if b is plan["beats"][-1] else math.floor((f1 - f0) / FPS * 1e3) / 1e3
    face_vids.append(f'<video id="ff-{b["id"]}" class="clip ffull" src="assets/face_full.mp4" muted playsinline data-start="{start}" data-duration="{dur:.3f}" data-media-start="{media}" data-track-index="1"></video>')

# ---- captions
caps = []
words_txt = plan["captions"]["chunks"]
for i, c in enumerate(words_txt):
    html = c["text"]
    acc = c.get("accent_words") or []
    if c.get("accent") and acc:
        toks = html.split(" ")
        out, inb = [], False
        for t in toks:
            on = t in acc
            if on and not inb:
                t = "<b>" + t
                inb = True
            elif not on and inb:
                out[-1] += "</b>"
                inb = False
            out.append(t)
        if inb:
            out[-1] += "</b>"
        html = " ".join(out)
    off = c["off"]
    if i == len(words_txt) - 1:
        off = END + 1
    caps.append([c["on"], off, html, POS[c["position"]], f'cap.w{c["words"][0]:04d}-{c["words"][-1]:04d}'])

# a chip changes height only on the layout switch itself, never a frame ahead of it. One whose word is too far off to open there waits, and the seam is empty until it does
switches = [y["start"] for x, y in zip(plan["beats"], plan["beats"][1:]) if x["layout"] != y["layout"]]
for prev, cur, chunk in zip(caps, caps[1:], words_txt[1:]):
    if prev[3] != cur[3] and switches:
        t = min(switches, key=lambda s: abs(s - cur[0]))
        if abs(t - cur[0]) < 0.12:
            prev[1] = t
            if words[chunk["words"][0]]["start"] - t <= CHIP_LEAD / FPS:
                if t != cur[0]:
                    print(f"chip moved to switch: {cur[0]} -> {t}")
                cur[0] = t

# ---- logos as symbols
syms = []
for n in owners.LOGOS:
    s = (ED / "assets" / "logos" / f"{n}.svg").read_text(encoding="utf8")
    box = re.search(r'viewBox="([^"]+)"', s).group(1)
    inner = re.sub(r"<title>.*?</title>", "", s[s.index(">", s.index("<svg")) + 1:s.rindex("</svg>")], flags=re.S)
    syms.append(f'<symbol id="logo-{n}" viewBox="{box}">{inner}</symbol>')
ICONS = '''<symbol id="i-grid" viewBox="0 0 24 24"><rect x="3" y="3" width="8" height="8" rx="1.6"/><rect x="13" y="3" width="8" height="8" rx="1.6"/><rect x="3" y="13" width="8" height="8" rx="1.6"/><rect x="13" y="13" width="8" height="8" rx="1.6"/></symbol>
<symbol id="i-slash" viewBox="0 0 24 24"><path d="M16 3 8 21"/></symbol>
<symbol id="i-mic" viewBox="0 0 24 24"><rect x="9" y="2.5" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0"/><path d="M12 18v3.5"/></symbol>
<symbol id="i-branch" viewBox="0 0 24 24"><circle cx="6" cy="5" r="2.5"/><circle cx="6" cy="19" r="2.5"/><circle cx="18" cy="9" r="2.5"/><path d="M6 7.5v9"/><path d="M6 13c0-3 3-4 6-4h3.5"/></symbol>
<symbol id="i-calendar" viewBox="0 0 24 24"><rect x="3" y="4.5" width="18" height="17" rx="2.4"/><path d="M3 9.5h18"/><path d="M8 2.5v4M16 2.5v4"/></symbol>
<symbol id="i-computer" viewBox="0 0 24 24"><rect x="2.5" y="4" width="19" height="13" rx="2"/><path d="M8.5 21h7"/><path d="M12 17v4"/></symbol>'''

# ---- HUD: the strip exists only if owners.py has HUD rows. What it counts on a new short is an open decision in layout.md
seats = [name for name, _ in owners.HUD if name.startswith("seat")]
if len(seats) > 5:
    stop([f"owners.py has {len(seats)} seat rows, and the strip has five sockets"])
count = "".join(f'<span id="cn{i}">{i}</span>' for i in range(len(seats) + 1))
strip = f'''<div id="strip"><div id="strip-s"><div id="strip-pop">
          <div id="strip-body"></div><div id="hm-mark"><i></i></div><div id="lbl">{owners.HUD_LABEL}</div>
          <div id="count">{count}/{len(seats)}</div>
          <div id="dot-gray" class="dot"></div><div id="dot-on" class="dot"></div>
          <div id="socks"></div><div id="rings"></div><div id="plugs"></div>
        </div></div></div>''' if owners.HUD else ""

try:
    body = scenes.build()
except FileNotFoundError as e:
    stop([f"scene asset missing: {e.filename}. Add it to shared/ and rerun new_project.py, or correct the scene's asset path"])
css = (HERE / "style.css").read_text(encoding="utf8")
js = (HERE / "timeline.js").read_text(encoding="utf8")
# the markers stay in the output, so ownership.py reads each table from the page itself
tables = {"END": END, "RUNS": runs, "WINDOWS": owners.WINDOWS, "HUD": owners.HUD, "CAPS": caps}
for name, value in tables.items():
    empty = "0" if name == "END" else "[]"
    js = js.replace(f"/*@{name}*/{empty}", f"/*@{name}*/" + json.dumps(value, ensure_ascii=False))
js = js.replace("/*@PLUGS*/[]", json.dumps(owners.HUD_PLUGS)).replace("/*@SIZES*/{}", json.dumps(scenes.SIZES))
nl = "\n      "
html = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
{css}    </style>
  </head>
  <body>
    <svg width="0" height="0" style="position:absolute"><defs>
{chr(10).join(syms)}
{ICONS}
    </defs></svg>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{END}" data-width="1080" data-height="1920" data-fps="30">
      <div id="bg" data-layout-allow-overflow="true"><div id="grid" data-layout-allow-overflow="true"></div></div>
      <div id="face-wrap"><video id="face" class="clip" src="assets/face_half.mp4" muted playsinline data-start="0" data-duration="{END}" data-track-index="0"></video></div>
      <audio id="voice" src="assets/voice.m4a" data-start="0" data-duration="{END}" data-track-index="9"></audio>
{body}
      {nl.join(face_vids)}
      <div id="hud">{strip}</div>
      <div id="caps"></div>
    </div>
    <script>
{js}
    </script>
  </body>
</html>
'''
tmp = ED / "index.html.tmp"
tmp.write_text(html, encoding="utf8", newline="\n")
os.replace(tmp, ED / "index.html")
try:
    m = ownership.emit(ED, beat_lock, owners.CHAINS, owners.EXTRA_ROOTS, {cap[4]: c["beat"] for cap, c in zip(caps, words_txt)}, library=owners.LIBRARY, helpers=owners.BLOCK_HELPERS)
    events.emit(ED, plan, beat_lock, m, owners.EVENT_BINDS, owners.COPY_BINDS, owners.HUD_BINDS, {cap[4]: c for cap, c in zip(caps, words_txt)})
except ValueError as e:
    stop([e])
except Exception:
    # a half-built project must leave no map, or run.py would accept it
    (ED / ownership.NAME).unlink(missing_ok=True)
    raise
for id_, why in m["shared"]["unconfined"].items():
    print(f"WHOLE RENDER: {id_} stays in the shell, so a note on it re-renders every beat: {'; '.join(why)}")
for id_, roots in owners.EXTRA_ROOTS.items():
    if roots:
        print(f"WHOLE RENDER: {id_} has extra roots {roots}, so a note on it re-renders from its first window to the end, even after its scene is hidden")
for sel, t in confine.frame_gaps(js):
    print(f"FRAME GAP: show({sel}, {t}) lands before its tween at {t}, so a 60 fps final can flash it for one frame. Give the tween A({t})")
print("index.html", len(html), "bytes;", len(caps), "chips;", len(face_vids), "face clips;", len(m["owners"]), "owners;", len(m["shared"]["unconfined"]), "in the shell")
