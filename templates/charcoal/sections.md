# Writing a section in charcoal

A charcoal video is 16:9, 1920x1080 at 30 fps. The voice track and his footage are fixed. A section file covers one stretch of the timeline, usually one chapter: it tiles that stretch with base shots (his camera, his screen) and puts a designed scene where an idea needs one.
The look is the template's: do not restyle it. Read `CARD.md` first. For designed scenes read `build_kit/examples/01-effort.mjs` and match it (the approved rule 1 of `work/1109-fable`, so its facts belong to that video). For base shots with graphics between them, read `work/1110-slop/full/tools/sections/01-slop.mjs`.

Proven on two videos. Rules tagged [Chase] are his words on those videos; the rest are ours and yield to him.

## Files in a run

`P = work/<id>/full` is the project. Run every command below from `P`.

| File | What it is |
|---|---|
| `work/<id>/raw/edit.txt` | The kept script, each sentence with its time, `\|\|` before a BIG join |
| `work/<id>/facts.json` | Every figure and verbatim prompt text, each with its source. Use only these |
| `work/<id>/pulls.json`, `work/<id>/docs/<pull>.json` | The real docs captures and their measured sentences |
| `P/tools/kit.mjs` | The helpers and the look. Do not edit it |
| `P/tools/local.mjs` | A helper only this video needs (a card with this video's step names). Sections import it from `"../local.mjs"` |
| `P/tools/segments.json` | The video as named segments, `[[start, "name"], ...]`: one idea each, 10 to 40 s. The player shows one beat per segment |
| `P/assets/stills/` | Stills for graphics: frames of `raw/cut.mp4` cropped, or captures |
| `P/tools/sections/NN-name.mjs` | One file per section, numbered in video order. This is what you write |
| `P/tools/build.mjs` | `node tools/build.mjs --sections=NN[,NN]` builds only those sections |
| `P/assets/words.json` | The cut's word timings. `cue()` reads them |

## How a section file works

```js
import fs from "node:fs";
import { END, cue, r, r3, chars, selX, selector, scene, face, docs, ruleTitle, promptCard, wipe, sweep, grow, pop, count,
         blurIn, show, slideIn, type, blink, WIDE, RIGHT } from "../kit.mjs";

export const title = "Rule 2: make it prove its work";      // the chapter's name in the YouTube chapter list

face(128.5, "right", 0.6);                    // where the face window is from this second on
ruleTitle("r2-title", 2, 128.717, 133.8, "Make it", "prove it.", "It sounds sure even when it's wrong.", cue("prove its work", 128));
scene("r2-claims", 133.8, 145.3, { wrap, css, html, tl: (T) => [ ...timeline lines... ].join("\n") });
```

- **`shots(prefix, end, list)`** lays the base: `[start, "face"]` is his camera full frame with the window off, `[start, "screen", {face: "pip", crop}]` his screen full frame with the window in a corner, `[start, "skip"]` leaves the stretch for a scene you write. Each shot runs to the next entry's start, the last to `end`. Hard cuts, nothing moves. Long shots are divided into slices of 22 s at most by themselves.

```js
shots("sl", 151.0, [
  [114.966, "screen"],                       // he walks through the page on his screen
]);
face(151.0, "pip", 0);                       // dur 0: the window is placed on that frame, a hard cut
scene("sl-fix", 151.0, tQ, { wrap: FULLW, exit: false, css, html, tl });   // a graphic for the next idea
shots("sl", 173.85, [[tQ, "face"]]);         // back to him for one sentence
```

- `scene(id, start, end, {wrap, css, html, tl})`. `start` and `end` are seconds on the video. Scenes must tile the section's range exactly: no gaps, no overlaps. The full build stops on either.
  Put scene boundaries on sentence starts from `edit.txt` with **`at("spoken phrase", after)`**: it starts the scene on the cut's join when one lies just before the sentence (his screen and camera change on the join), else 0.05 s before the first word. A boundary typed as a number, or made from `cue()` minus a bit, can leave a few frames of the old shot over the new footage [Chase, 2026-11-13]. `joinNear(t)` is for a shot whose first word `cue()` cannot match.
- `tl` is a function of `T`, which turns a video second into the scene's own clock. It returns GSAP lines as a string.
  Everything is timed in video seconds through `T(...)`. Small fixed offsets from the scene start can be literal (`0.08`).
- **`cue("spoken phrase", after)`** returns the second that phrase is spoken, first match at or after `after`. Use the words exactly as `edit.txt` has them. Time every reveal to the word it belongs to, usually `T(cue(...) - 0.1)`.
  A reveal with no spoken anchor is a mistake.
- Ids: prefix every scene id with its section (`r2-...`, `sp-...`, `out-...`) and every element id with the scene id (`r2-claims-row1`). Element ids are global.
- `css` is scoped to the scene automatically. Write plain rules (`.h{...}`): no `@media`, no nested rules, no `}` inside values.
- Each scene fades out by itself (a blur swap) in its last 0.26 s. Do not add your own exit. Pass `exit: false` when the next thing is a hard cut to a base shot or to another full-frame scene.
- **A still layout with his footage in it renders without the browser** [Chase, 2026-11-13]: when nothing in a scene moves except his footage inside one rounded rectangle (his app in a card on a still page), add `cardPage(css, html)` and `cardFootage(id, a, {crop, page, x, y, w, h, r, from})` beside the `scene()` (the comment above them in `kit.mjs` has the rules; `work/1113-nod/full/tools/local.mjs` `appShot()` is the worked example). The renderer draws the page once and the GPU lays his footage and the face window in. A scene with any timeline line, or a face window that moves during it, stays a browser scene.
- His footage inside a designed scene: `clipTag(id, {src: "screen" | "cam", crop, w, h, start, end})` (animate a wrapper, never the video), or `screenCard(...)` for his screen in a card with a bar naming the real site. The renderer cuts the clip files itself.
- Timeline helpers, all returning a line, times in scene-clock seconds: `blurIn(sel, at)`, `show(sel, at, dur)`, `slideIn(sel, at)`, `type(sel, at, perChar)` with `chars("text")`, `blink(sel, on, off)`, `grow(sel, at)` for bars, `pop(sel, at)` for chips, `count(sel, at, to)` for a number counting up, `wipe(sel, at, lines)` and `sweep(markSel, at)` for prompt cards.
  Raw GSAP `tl.fromTo(...)` lines are fine too: always `fromTo`, never `from` or `to` alone.
- HyperFrames rules that break renders if ignored: animate only `opacity`, `filter`, transforms (`x`, `y`, `scale`, `scaleX`), colours, `clipPath`, `backgroundSize`, `strokeDashoffset`. Never `left`, `top`, `width`, `height` or `display`. No CSS `transform` on an element GSAP also transforms: put it on a wrapper. No randomness, timers or fetches.

## Layout

The stage is 1920x1080, charcoal. The ASCII strip runs along the bottom from y = 884: keep content above y = 860 (opaque cards may overlap it a little). Side margin is 96 px.

Say where the face window is with `face(t, place, dur)`. `dur` 0 is a hard cut; `shots()` sets it for base shots.

| Place | Window (x, y, w x h) | Use this wrap | Content area |
|---|---|---|---|
| `"off"` | none: his camera is the whole frame | `wrap: FULLW` | nothing over his face |
| `"pip"` | 1512, 582, 360 x 450 | `wrap: FULLW` | full frame, but nothing right of x = 1470 below y = 540 |
| `"pipL"` | 48, 582, 360 x 450 | `wrap: FULLW` | full frame, but nothing left of x = 450 below y = 540 |
| `"pipT"` | 1512, 48, 360 x 450 | `wrap: FULLW` | full frame, but nothing right of x = 1470 above y = 540 |
| `"right"` | 1344, 206, 480 x 600 | default | x 96 to 1156 |
| `"left"` | 96, 206, 480 x 600 | `wrap: RIGHT` | x 752 to 1824 |
| `"corner"` | 1566, 538, 258 x 322 | `wrap: WIDE` | x 96 to 1824, but nothing right of x = 1500 below y = 500 |

- The wrap's origin is its left edge: in the default and WIDE wraps `left:0` is x = 96 on screen; in RIGHT it is x = 752.
- Over his screen or a full-frame graphic the window is a `pip`, placed by hard cut. Pick the corner that covers nothing he points at (`pipL` when the action is on the right, as with a tweak bar).
- Beside a stage scene, move the window at a scene change, starting about 0.2 s before it. Large for statements and questions, corner when a chart, document or prompt card needs the width. Do not move it more than about once every 8 s.
- **Every BIG join in the section must sit on a scene change or a face move, within 0.3 s,** so the jump in his face is covered. Small joins need nothing.
  No punch-in on his face at a join: he read the pilot's 1.1x punch-ins as "zoomed in a little too much". [Chase]
- A section starts with the window wherever the previous one left it. Start with your own `face(sectionStart - 0.25, place)` so the section is correct on its own.
- **When he says his face is zoomed in, he means the shot inside the window, not the window's size.** [Chase] Ask which before changing sizes. The shot can only be as wide as the camera file allows.

## What goes on screen

Start from the base: `shots()` over the whole chapter, his camera when he talks to the viewer and his screen when he shows something. Then, per idea:

- **No stretch of only his face over about 12 s without a reason.** [Chase] Give the idea a graphic made of something real: a still of the page he names, his own picks arriving as he lists them, the three tools as a stack, a before and after. A sentence or two to camera for emphasis stays as it is.
- **Never text over his full-frame face. No slow push on a screen recording while nothing else changes. No floating card on an empty stage.** [Chase] A zoom or a soft transition needs a reason he could name.
- **If his take shows a shot list or script on screen, build to it,** not to the transcript alone.
- **Every graphic goes on the storyboard before it is rendered,** with the on-screen words that are not his listed in its row (`build_kit/storyboard.py`).

On a stage scene, one idea per spoken sentence:

- **A chapter title** first: `ruleTitle(...)`. Two short typed lines (12 characters or fewer each is best) and a sub line. Its kicker reads `// rule 03 of 10`, from `tools/video.json` `series`.
- **A real docs pull** where he states what a source says: `docs(id, pullId, opts)` then `D.css`, `D.html`, `D.tl(t0, [highlightTimes])`, one highlight time per sentence. At most one docs pull per 20 s, never two in a row.
- **A prompt card** where he tells the viewer what to type: `promptCard(...)` with verbatim text from `facts.json`. Hand-wrap the lines: at 26 px a 1060-wide card fits about 62 characters per line, a 1380-wide one about 82.
  He may say "a prompt like the one you see on screen" without reading it, so it must be fully readable.
- **A small diagram** for behaviour: a file tree of steps, a selector, bars, a before/after table, a big number. Build it from the kit's classes: `.row .br .n` (tree rows), `.tb .tr` (dashed table), `.trk .bar` (bars), `.chip`, `.big` (150 px number), `selector(id, names)`.
- **A statement** (`.h` headline, 84 to 112 px, one `<em>` phrase in orange) for opinions and conclusions.
- A term he uses and never explains gets a one-line gloss on screen. Say in the handoff that the wording is ours.
- Numbers: only from `facts.json`. If he says a number that differs from the source, show the source's number and wording, and list the difference for him. Never invent a figure, a quote, a benchmark, or a file name with fake authority. Placeholder names in a schematic are named as placeholders in the handoff.
- Cite quietly: a `.src` line such as `system card §2.3.3`, or the docs tag, is enough.
- A sponsor or site card is a real capture of that page. Its on-screen claims are only what he says. Where his words and the page differ ("48 modules" against the page's "48 lessons"), follow his voice and flag it.

## Style rules

- Readability first. [Chase] Headlines 84 px or more, body mono 30 to 36 px, nothing under 24 px. At most about 10 words in a headline and 6 rows in a list.
- Headlines in Hanken Grotesk (`.h`), everything else in Geist Mono. Orange only for the one thing that matters in the scene. Square corners on cards, dashed hairlines.
- No banner or brand bar. No cute fake labels on anything. No emoji. No decorative icons. [Chase]
- No text that only repeats his sentence word for word: show the thing he is talking about. [Chase, from the shorts: a panel that only repeats his words is boring]
- Plain words on screen. No hype words, no exclamation marks.
- Vary the scenes inside a chapter. Do not use the same layout twice in a row.
- Background texture is judged at the size he watches, not at full size. [Chase: "I can't see anything on the ASCII horizon or the dots. It's that subtle."]
- An image shown larger than its page size needs a denser capture: at k times page size it needs 2k source pixels per page pixel for a 4K final. `capture_docs.mjs` already does this for the lifted excerpt.

## Check your work

From `P`:

```bash
node tools/build.mjs --sections=NN,NN
npx hyperframes check --json > check.json
npx hyperframes snapshot --at t1,t2,...
```

- `check`: fix every `error` in lint, runtime, layout and motion. Contrast and craft warnings about small labels, silence, or reading time can stay.
- `check` on the whole page wants the clip file of every footage scene: run `python tools/make_clips.py --all` once first, or check with `--sections=` on the designed sections only.
- Snapshot at least two moments per scene, mid-reveal and fully revealed, and look at the contact sheets. Fix overlaps, text running off the wrap or under the face window, reveals that are late or missing, and anything touching the ASCII strip. Snapshot again after fixes.
- A section writer does not render video and does not edit `kit.mjs`, `build.mjs` or another writer's sections. A helper only this video needs goes in `tools/local.mjs`.
