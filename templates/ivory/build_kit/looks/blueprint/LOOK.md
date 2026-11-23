# blueprint

The short as **one engineering drawing**. Chase asked for it on 2026-11-19 ("a blueprint grid style... be unusually ambitious"), refined it over two rounds of stills, and approved the full-length motion test on the rea short ("that's really good"): `work/1119-pixel-guide-test/blueprint/out/blueprint-motion.mp4`.

**This is not a `build.py` look.** There is no `look.css`, so `"look": "blueprint"` in an ivory `plan.json` stops the kit build with a message, on purpose. A blueprint short is hand-built on this folder's engine, after the cut is approved, like charcoal long-form is built by hand from its kit. It is still reviewed in the player and approved by his click: "Review in the player" below. Record `look: blueprint` and his words in `RUN.md` as usual. His real face and voice sit underneath in the normal split; the top half (1080 x 998) is the drawing.

## What is in this folder

| File | What it is |
|---|---|
| `bp.py` | The engine's Python side: drafting primitives, the HyperFrames project it writes (`index.html` + assets), the sound mix, `check` / `stills` / `render` through HyperFrames 0.9.13 |
| `engine.js` | The engine's timeline: camera and pen, every region drafting itself in, typing, plates developing into colour, HUD, captions, seeded grain. Registered on `window.__timelines["blueprint"]` after the fonts load. Generic; a short adds its own moves through two hooks |
| `fonts/` | Barlow Condensed 600/700/800, JetBrains Mono 600/600 italic/700/800, Caveat 500 (SIL OFL 1.1, licences beside them). Safe to ship publicly |
| `blueprint.css`, `defs.html` | The sheet, strokes, plates, labels, HUD and captions; the arrowheads, hatching and the duotone filter |
| `examples/rea.py` | The approved rea short, complete. Copy it to start a new one |

It renders through **HyperFrames** like every other short [Chase, 2026-11-19: "get it working on HyperFrames like the rest"]. `bp.py` writes a standalone HyperFrames project at the spec's `OUT` (root `data-composition-id="blueprint"`, 1080 x 1920, the drawing on top, his face as a framework-owned `<video>` at y 998, the voice and the cue track as `<audio>`). Run a short:

- `python templates/ivory/build_kit/looks/blueprint/examples/<id>.py check`: HyperFrames check. Expect warnings for word-length captions (`line_unread`) and contrast flags on the soft grey labels and orange on blue; those are the approved design. Lint and runtime must be clean.
- `... stills 3.9 8.2`: HyperFrames snapshots in `<OUT>/checks`.
- `... render 4k`: `hyperframes render --resolution portrait-4k`, then `tools/finish.py` to -14 LUFS: `<OUT>/<NAME>_4k30.mp4`. The rea short took 16 minutes at 4K on the RTX 5090; run it in the background. `render` without `4k` gives 1080.

## The system

- **One drawing, a camera.** Each beat (or pair of beats) is a region of a big blueprint sheet. Regions are laid out in a snake (left to right, then right to left) so every move goes to a neighbour. Dashed match lines with "MATCH LINE · SHEET 01 → 02" labels join them, as on a multi-sheet drawing.
- **The pen leads the camera.** On each region change a red pen draws the path into the next region and the camera follows: 0.7 s, power3.inOut, centred just before the cut. No other transitions.
- **Every region drafts itself in** as the camera arrives: faint construction lines first, then strokes trace on, plates wipe down, titles wipe in as outlines and then fill. Anything with a `t` draws on that word instead.
- **Colour rule.** Proof plates sit in blueprint duotone (`duo=True`). The one that matters develops into full colour (`dev=(t0, t1)`), a bright scan line leading the wipe. Red-orange `#ff7a45` is the redline accent: the one word in a title, the line that matters, every cut and markup.
- **The ending pulls back** (`PULL_AT`) to the whole drawing, and a title block rises in front of it as the call to action.
- **Paper**: blueprint blue with a 24/120 px grid, cyanotype mottling, fold creases, chalky line glow, film grain flickering at 12 fps. **HUD**: "SHEET 03 / 14" top right, per beat. **Captions**: white chips on the seam, Barlow Condensed caps, 1 to 3 words.
- **Type**: Barlow Condensed 800 for headlines and numbers, JetBrains Mono for labels and drawing text, Caveat for handwritten redline notes. All Google Fonts (OFL).

## Drafting conventions to tell the story with

Pick the one that fits what the line says; each is a primitive in `bp.py` or a pattern in `examples/rea.py`.

| Convention | Use it for | In the rea short |
|---|---|---|
| Dimension lines (`dim_h`, `dim_v`) | sizes, durations, gaps, a measured claim | 1080 x 1920 on the video; "19.0 s · 10 SHOTS"; "< 3 WEEKS" |
| Section cut (red dash-dot line + A/B/C) | splitting something, "shot by shot", cutting into it | three cuts on "shot by shot"; section A-A on "actual code" |
| Detail circle (magnified, in colour) | the one small proof on a page | the "Star 10.6k" button |
| Count-up + plot | a number | 10,000+ and stars over days |
| Exploded view (front + side, or a 3D stack) with balloons and a parts list | "pieces", "every part", what something is made of | the four layers; the 10-shot stack and its parts list |
| Flowchart (decision diamond, branches) | a choice, a classifier | real / AI / code |
| Typed spec box | real text the tool outputs | the shot-02 prompt, the remake note |
| Redlines: revision clouds, rev triangles, a strike-through, handwritten notes, a revision table | "edit", "change it", "make it yours" | the recipe |
| Title block | the name, the call to action | the end card |

## Writing a new short

1. Copy `examples/rea.py` to `work/<id>/v2/blueprint/short.py` (the two path lines at the top change: see `work/1118-rea-blueprint/v2/blueprint/short.py`). Set the paths (`WORDS`, `FACE`, `VOICE`, `OUT`), `END`, `COLS`/`ROWS`, `BEATS` (his cut's beat starts), `ARR` (when the camera reaches each region), `PULL_AT`, `SHEETNO`, `HUD`.
2. One function per region returning `(html, svg)` in region coordinates (1080 x 998). Give every keyed element `t=` the start of its word from `words.json`. Use real material only: his captures, the tool's real output, real numbers. Start the titles at y 150 (`title()` does by default) so they clear the phone's status bar and Dynamic Island [Chase, 2026-11-20: the rea titles at y 44 sat under the island]. Drop rea's `y=44` pins and `HUD_TOP`: those keep the posted rea short as it went out.
3. Moves the engine does not do go in `JS`: `BP_PRE(tl)` measures the finished layout before anything hides (leaders to a 3D stack); `BP_KEYED(tl)` adds the short's own tweens (count-ups, explosions, the end block). Elements those show get class `bp-keyed`; SVG groups filled in by `BP_PRE` get class `bp-late`.
4. Sounds: few, on his actions only (the rea short has six); `SOUNDS` uses the vetted slices in `templates/ivory/sfx` at the house levels. His approved pencil strokes (`pencil-a`, `pencil-b`) are for strike-throughs and cuts.
5. `stills` across the whole timeline, look at them, then `player`.

## Review in the player

A blueprint short is reviewed like a kit short [Chase, 2026-11-22]: the beat review player, notes at exact seconds, rounds, and his Approve click starting the 4K final. `tools/look_player.py` is the bridge; both hand-built looks use it.

- **Where the short lives.** `work/<id>/v2/blueprint/short.py`, with `OUT` = that folder (`HERE` in the worked copy `work/1118-rea-blueprint/v2/blueprint/short.py`). The player needs that layout, and a spec inside the project is snapshotted by every round, so Go back restores it. `BEATS` (the second each beat of his cut starts, the first 0) is what the player shows as beats.
- **First picture.** `python work/<id>/v2/blueprint/short.py player`: the 1080 review render (waits its turn on `gpu_lock`), then loaded into the player. Serve it with `python -B tools/beat_review_v2/server.py work/<id>/v2/blueprint` and give him the handoff as SKILL.md section 6 says.
- **A note round** (he says go in chat): `review.freeze(project)`, the smallest change in `short.py`, `player` again, `review.close_round(project, done=[...], not_done={...})`. The whole short re-renders each round (about 4 minutes for the 49 s rea short on a quiet machine, up to three times that when it is busy); beats whose frames changed are marked in the player.
- **Approval.** His click in the player. It runs `short.py final <rev>` through `autofinal.py`: rebuild, refuse unless that is the composition he approved, 4K30 at -14 LUFS, delivered as `out/<id>_blueprint_final_4k30.mp4`. The few cues are already in the review picture, so there is no separate sound stop.
- **What it does not have.** No per-beat render in use: `player --partial b04` films only the named beats and checks the rest with stills, but measured on 2026-11-22 it is slower than the whole render (HyperFrames' ranged render pays about 1 min 50 s of start-up per stretch, in software capture), so rounds use the whole render until that is solved. Also no native-size beat button, and none of the kit's automatic checks (motion lint, flashes, copy, geometry): the only automatic check is the render's length and that it has sound. Look at stills across the whole timeline yourself before the handoff.

## Rules learned building it

- Never place a tween before 0: GSAP shifts the whole timeline later (it ran 1.1 s late once).
- HyperFrames refuses tweens on layout properties (`left`, `top`): move things with `x`/`y`. It also refuses template literals inside `querySelector` (build the selector with `+`).
- No unseeded `Math.random`: the grain uses a seeded generator so every render is the same.
- The end card sits over the zoomed-out drawing on purpose: `data-layout-allow-overlap` on the sheet and the end block.
- SVG fills set with the `fill` attribute lose to the `.l` class; put a hatch fill in `style`.
- A region empty when the camera arrives looks dead: start its first element drawing at, or just before, the arrival.
- Keep the HUD clear of titles (titles end by x ≈ 800).

## Known gaps

- The worked example's images live in `work/1119-pixel-guide-test/img`, which is local only.
- Its first motion test (`work/1119-pixel-guide-test/blueprint/motion.py`) was a standalone screenshot renderer; the HyperFrames 4K render matched it frame for frame (mean difference about 3/255, from the grain) and is sharper.
- Not in the public repo yet.
