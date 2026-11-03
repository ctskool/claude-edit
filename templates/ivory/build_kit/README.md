# Ivory build kit

A new raw's project starts here. Its first build writes `beats.lock.json`, `ownership.json` and `events.json`, so `tools/beat_render/run.py` accepts it. A project with none of those is refused, and nothing falls back to all-shared.

`recut-build.js` uses it. For a real look at the same sources in use, read `work/beat-fixture/v2/editorial` (a 107 s ivory edit). Read it only: its content is another video's.

## Start

```
python templates/ivory/build_kit/new_project.py <id> [--full-face, only with allow_full_face true]
```

It needs `work/<id>/` to hold `metadata.json`, `beats.json`, `words.json`, `assets/face_half.mp4` and `assets/voice.m4a`. It makes `work/<id>/v2/editorial`: a copy of `tools_local/`, `hyperframes.json`, `package.json`, `meta.json`, `CLAUDE.md`, the kit's fonts and GSAP, and hard links to `shared/*` and the face and voice files. `--full-face` also links `face_full.mp4`, only when the run has `allow_full_face` true. A repeat run keeps existing sources and assets and links newly added shared files. Replaced assets need an explicit replacement; Setup never silently overwrites one.

HyperFrames stays 0.8.184. `run.py` fails closed on anything else.

## What you write

| File | You write |
|---|---|
| `plan.json` | Everything below. The director writes it |
| `tools_local/owners.py` | Windows, HUD rows, binds |
| `tools_local/scenes.py` | Scenes in `build()`, where `# @SCENES` sits |
| `tools_local/timeline.js` | One block per scene, where `// @BLOCKS` sits |
| `tools_local/style.css` | Only what a new component needs |

Leave `build.py` and the shell of `timeline.js` alone. A change to either touches every beat. `index.html`, `beats.lock.json`, `ownership.json` and `events.json` are generated: never edit them.

## plan.json

Required, and `build.py` stops in words if one is missing:

- `duration`: a finite number equal to `metadata.json` duration. The build stops before a render if missing or different.
- `beats[]`: `id`, `start`, `end`, `say` (its transcript text), `layout` (`split`, `full-graphic`, or `full-face` when `allow_full_face` is true), `anchor`, `sub_anchors` (a list), `actions` (a list), `proof_span` (`[start, end]` or null), plus its `assets` and `crops`.
- Every anchor, sub-anchor and action is an object with its own `event_id`, `b12.e1`, `t` in seconds, `what`, and `word_i` when it lands on a word. An event id is never renumbered.
- `captions.chunks[]`: `beat`, `text`, `words` (word indexes), `on`, `off`, `position` (`seam`, `takeover`, `fullface`), `accent`, `accent_words`. A chip opens at most 5 frames ahead of its first word, or the source check reads FAIL. Near a layout switch the build moves it onto the switch, and if that is too far ahead the chip waits and the seam stays empty until it opens.
- `cta_start`, `allow_full_face` (a JSON Boolean), `allow_full_face_source`.
- `composition_files`: exactly `["tools_local/build.py","tools_local/scenes.py","tools_local/timeline.js","tools_local/style.css","tools_local/owners.py"]`.

Beats touch end to start, the first starts at 0, the last ends on `metadata.json` duration exactly, and none is empty at 30 fps. Layout runs come from the beats, so there is no table of them to keep in step.

`cta_start` comes from the first CTA word's start in `words.json`; `cta_start_source` records the word index and quote, or the reason there is no CTA. A beat's `proof_span` covers audible product/demo evidence under `sound.md`, with `proof_span_source` naming the clip and composition interval. Muted screen footage under narration has null with that reason. The content planner writes these in `beats.json`; the director carries them into `plan.json` and derives them from transcript/media only for older content plans. The plan checker verifies both sources. They are never invented as placeholders for sound.

The director owns scene images, only when the run has Codex (`codex` true); without it there are none. Generate missing `shared/scenes/<beat>.png` before the independent plan check and Setup, and append each exact prompt, path and dimensions to `ASSETS.md`. In Codex use the built-in image tool; in Claude Code hand the job to `codex exec`. The builder uses the linked `assets/scenes/` file. If one arrives after Setup, rerun `new_project.py` to link it.

## A scene, end to end

`scenes.py`, one call per scene group. One balanced element, its id the scene's root, class `scene`, or `scene full` on a full-graphic layout. The root's style holds nothing but opacity.

```python
S.append(own("sc-price", f'''<div id="sc-price" class="scene">
  {card("pr-card", (72, 120, 936, 620))}
  {plate("pr-pl", "shots/pricing.png", (0, 0, 1600, 900), (90, 138, 900, 506))}
  {lbl("pr-w", 90, 680, "Half the cost", 44, "opacity:0")}
</div>'''))
```

`timeline.js`, one block per scene, in window order. Its marker sits alone on a line, and the shell's closing marker stays after the last block. Never write the marker in a comment.

```js
own("scene.sc-price");
// ---- b13 pricing
cutIn("#pr-pl", 23.85, 26.62);
on("#pr-w", 24.4);
```

`owners.py`:

```python
WINDOWS = [["#sc-price", 23.85, 26.62]]             # one row per time the scene is up. A scene can have several
EVENT_BINDS = {"b13.e1": ("scene.sc-price", "#pr-w", "appear", "Half the cost", None)}   # event_id: (owner, target, expect, copy, hold_frames)
COPY_BINDS = [("b13", "Half the cost", "scene.sc-price", "#pr-w", 26.5)]                 # every line of beats.json copy: (beat, line, owner, target, t)
```

- `expect` is `appear`, `change` or `present`. The target is what the plan says happens on the word, not whichever element tweens then. A clip's content cannot be measured, so an anchor inside a clip binds its plate as `present`.
- An event with no bind is `UNVERIFIED`, never skipped and never a pass. Bind every anchor.
- `WORD_FRAMES = 2`: a word-bound anchor may be at most 2 frames early or late. A chip may open at most 5 frames early and at most 2 frames late. An `appear` target must not already be readable on the frame before its word; use `present` only when the plan truly calls for something already on screen. Text's default hold is 30 frames (clipped to its owner's actual window); design that readable hold, or give an explicit justified `hold_frames`. An extra-root owner reaches the end, so its binds need an explicit hold within the real scene window.
- A copy line must match `beats.json` character for character. A sixth field `{"symbol": "logo-x"}` marks a mark rather than text. `{"image": "assets/shots/x.png"}` marks text inside a real capture, which stays `UNVERIFIED`.
- A word changed in a graphic must also change `beats.json` copy and its `COPY_BINDS` row, or the source check reads FAIL.

## A clip that ends before its scene

Keep a clip window within the source length remaining after `media_start`, or hold its last real frame underneath with `vplate`'s `stills` argument. From the project folder:

```bash
mkdir assets/held
ffmpeg -sseof -0.04 -i assets/clips/demo.mp4 -frames:v 1 -update 1 assets/held/demo.png
```

```python
vplate("demo-pl", [("demo-held", "held/demo.png", "")], "clips/demo.mp4",
       (0, 0, 960, 540), (90, 138, 900, 506), 12.0, 3.0, 0)
```

The video plays for its real 3 seconds; the still remains through the scene window. The still uses its own PNG path and dimensions. Snapshot after the video ends as well as during it. A black panel is a defect.

## HUD

HUD rows in `owners.py` turn on the strip: `["strip", t]`, then `["seat0", t]` up to `seat4`, and `ring0` to flash a socket. Set `HUD_LABEL`, `HUD_PLUGS` (one `[symbol id, "ic" or "mk"]` per seat) and `HUD_BINDS`:

```python
HUD = [["strip", 6.8], ["seat0", 7.36], ["seat1", 32.2]]
HUD_LABEL = "THREE TOOLS"
HUD_PLUGS = [["i-grid", "ic"], ["logo-claude", "mk"]]
HUD_BINDS = {"strip": "#strip", "seat0": "#plugs .plug:nth-child(1)", "seat1": "#plugs .plug:nth-child(2)"}
```

Every link runs to the last frame, so a note on one touches everything after it. What the HUD counts on a new short is an open decision in `layout.md`. If the plan has nothing to count, leave `HUD` empty and flag it.

## Bottom-half punch-in

Use `EXTRA_ROOTS` for a split beat marked as a jump-cover punch-in. Put an action in `plan.json` with its stable `event_id`, join time `t`, `what: "bottom-half punch-in"`, `scale: 1.08` and `end` (normally 1-2.5 seconds later). Keep it inside that scene's split window. This changes only the real `face_half.mp4` pixels inside the clipped `#face-wrap`; no synthesized person, bottom fade or full-screen layout.

In `owners.py`, add `EXTRA_ROOTS = {"scene.sc-cover": ["#face"]}`. In that scene's existing timeline block, for a join at 12.0 and a window covering 12.0-14.0:

```js
tl.set("#face", { scale: 1.08, transformOrigin: "50% 50%" }, A(12.0));
tl.to("#face", { scale: 1, duration: 0.16, ease: "power2.out" }, 13.34);
tl.set("#face", { scale: 1 }, A(13.5));
```

The scale is cut in on the join, held, and reset before the window ends. All extra-root tweens, including the reset, must start and end within one of this scene's windows (`--audit` checks that). Bind its action as `change` on `#face`, with an explicit `hold_frames` ending before the reset. Give other text binds explicit holds within the actual scene window too: ownership's conservative interval reaches the last frame.

The build prints a `WHOLE RENDER` line for every extra-root owner. Its cost is all beats from the first window to the end, not just the scene's visible beats. Put that cost in `RUN.md`. For locating a note, inspect `WINDOWS`, not just the stretched owner interval. This recipe was rendered on real footage at the review profile (540x960, 30 fps) in `work/beat-first-real-punch-20261101`; `python tools/tests/test_kit_media.py work/beat-first-real-punch-20261101` checks the decoded punch-in and held-frame pixels. A source audit alone does not prove a rendered punch-in.

## Popout bottom

`plan.json` may carry `"bottom": "popout"` and `"bottom_source"`. Without it, or with `"split"`, the page is byte for byte what it was before popout existed. With popout, `build.py` reads `assets/popout.json` (written by `python tools/popout.py make <project>`) and swaps in the shared card, cut-out and styles from `tools/popout.py`. It doubles every `"#face"` tween onto `#face-fg` and adds `#face-fg` to any `EXTRA_ROOTS` entry that names `#face`, so a punch-in still works. Write punch-ins on `#face` as before. Rules: `templates/HOUSE.md` "Popout bottom".

## A beat that holds the last beat's picture

If a beat shows the same card or capture in the same place as the beat before it, give it no entrance. `cutIn` drops the card 33 px and snaps it back, so on an unchanged picture it reads as a hitch. [Chase] heard this on 1030-2, b28 into b29.

Open with the slow push only, and start its scale where the last beat's push ended, so the join holds still:

```js
tl.fromTo("#b-g", { scale: 1.01508, transformOrigin: "50% 50%" }, { scale: 1.03085, duration: 3.033, ease: "none", immediateRender: false }, A(21.267));
```

Fade anything that won't carry over, such as an outline, before the join.

## One frame early

`show(sel, t)` fires at `A(t)`, 4 ms before `t`, so it lands on the frame at `t`. A tween that starts the same thing at plain `t` starts after it, and a frame that falls in those 4 ms shows the thing finished for one frame. Most times have no 30 fps frame there, so review never sees it, and a 60 fps final does. Any tween paired with a `show` takes the same time: `show("#x", 2.32)` with `tl.fromTo("#x", ..., A(2.32))`, as `popFirst` and `slotPop` do. The build prints `FRAME GAP` for a pair that misses. It does not stop the build.

## Build stops

`python tools_local/build.py` prints `BUILD STOPPED`, writes no `ownership.json`, and exits 1. Fix the source it names and build again. These rules come from `tools/beat_render/confine.py` and `ownership.py`, because no hash of one block can cover what they allow.

| The message says | It means | Fix |
|---|---|---|
| `tl.to() with no position`, `with a label or relative position`, `with a position that is not a number` | A tween would land relative to whatever came last, in another block | Pass a number: a literal, arithmetic on literals, or a name in the block that only ever holds those |
| `show() with no time`, `with a time that is not a number` | The same, through a helper | The same |
| `.to() chained after another call` | The chained tween has no position of its own | One call per tween |
| `tl used other than by a call`, `<helper> used other than by a call` | Something holds `tl` or a helper where it cannot be read | Call them directly |
| `N top-level elements, not 1`, `its one element is not #sc-x`, `<x> is not closed` | A region must be one balanced element, its scene's root, because a window controls that root's opacity | Wrap the scene in its root, and close what is open |
| `defines #x, and the shell uses that id` | A selector in the shell would find the scene's element | Rename it. Scene ids carry a scene prefix |
| `declares X, and code outside the block uses it` | A constant crossed blocks, and block hashes cover their own text only | Keep it inside one block |
| `id x is in both` | Two regions share an id | Rename one |
| `windows and owners differ`, `DOM regions and JS blocks differ` | A scene has no window, no block or no region | Add what is missing. An empty block still needs its marker |
| `binds unknown owner`, `binds for events the plan does not have`, `copy binds that match no line` | A bind points at nothing | Fix the row, or `beats.json` copy if a word changed on purpose |
| anything naming `plan.json` or a beat | `plan.json` lacks what the build reads | The field list above |

`conform.py --audit` is the same idea, in the page. It runs before anything renders, and anything but PASS stops the run. It catches a block tweening outside its own root, a window opened from inside, and any position that was not a number when the page built.

## Whole render lines

`WHOLE RENDER: scene.sc-x stays in the shell` is not a stop. The scene is treated as shared, so any later change to it re-renders every beat. It costs time, never a wrong picture. The first whole-render figure on a shared machine was 346 s for 107 s of video. A five-note round was 173 s.

A block stays local only if all it does is on the short list: `tl.to`, `tl.set`, `tl.from`, `tl.fromTo` with numeric positions, the helpers in `BLOCK_HELPERS`, a few pure methods (`forEach`, `map`, `filter`, `slice`, `Math.*` and the like), and arithmetic on its own names. It reads nothing else and writes no member. A template literal, a regular expression, `.style`, an `onUpdate`, or any shell name sends it to the shell.

A region stays local only with tags and attributes on `confine.py`'s short list. Tags: `div`, `span`, `p`, `b`, `i`, `em`, `strong`, `br`, `img`, `video`, and plain SVG shapes. `<canvas>`, `<iframe>`, `<style>`, a `data-` attribute of your own, or an id another owner points at sends it to the shell.

Fix each line unless the plan truly needs it, and list what is left in the build's result.

## QA, in this order

```
python tools_local/build.py
python tools/beat_check/conform.py work/<id>/v2/editorial --audit
python tools/beat_check/conform.py work/<id>/v2/editorial --all
npx hyperframes lint
python tools/motionlint.py index.html --pack editorial
```

Before a render, `--all` normally exits 3 for missing rendered references: read its report and require no FAIL lines. Exit 0 is valid too. Fix every FAIL; exit 4 means it never measured the page and stops QA. Then `npx hyperframes snapshot` for a look. Rendering is `run.py`'s job, after the build.
