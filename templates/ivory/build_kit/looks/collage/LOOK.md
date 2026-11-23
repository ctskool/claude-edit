# collage

A Vox-style paper collage. Chase approved it as a mock on the five-tools short on 2026-11-16 and asked for it as a real look. Set `"look": "collage"` (and `"look_source"`) in `plan.json`.

What it draws: a grey paper table with faint crosshair marks; cards as torn white sheets, taped, on torn yellow backing (a newspaper page on a full-screen title card); a coloured halftone scrap and a newspaper clipping behind every scene; a black-and-white magazine cut-out on scenes that name one; captions on torn paper strips in a heavy face with a yellow highlight word; the counter as a pinned paper strip; a torn paper edge along the seam over his footage. His footage itself is never touched.

## What is in this folder

| File | What it is |
|---|---|
| `look.css` | Laid over the kit's `style.css`. Kit classes and the look's own `cq-` / `cut-` classes only: no scene or element id of any one video |
| `look.json` | The colour remap for literals a scene or the timeline wrote |
| `motion.js` | Appended by `build.py` at the end of the timeline's function. Adds each scene's scrap, clipping and cut-out, the paper jitter, the entrances and the 12 fps stepping |
| `assets/vox/` | The images, copied into a project's `assets/vox/` by `new_project.py`. `cut/` holds the cut-outs, tape, pin and paperclip |
| `make_assets.py`, `src/` | The generator and the generated source images it reads. Rerun it after changing a source; it writes `assets/vox/` |

This is the first look that brings images and a script. Both are kit features now (`build_kit/README.md`, "Looks"): any look folder may hold `assets/` and `motion.js`.

## Using it on a project

A new project: nothing extra. `new_project.py` copies `assets/vox/`, and the kit's `build.py` reads the look.

A project made before 2026-11-16 has its own older copy of `build.py`, which knows nothing of a look's images or script:

```
cp templates/ivory/build_kit/tools_local/build.py work/<id>/v2/editorial/tools_local/build.py
python templates/ivory/build_kit/new_project.py <id>
```

The first line replaces the builder (it holds nothing of the project's own, unless the project is a 60 fps derivative, whose `FPS` line `final.py` edited). The second copies the images and keeps everything else. If the images are missing the build stops and says so.

## What a scene writes

Scenes are written as for any look. The look reads the kit's own classes (`scene`, `scene full`, `pc`, `plate`, `lbl`, `serif`, `num`, the chips, the counter). On top of that a scene may mark elements with these classes, beside the element's own class. They do nothing under another look.

| Class | On | What it becomes |
|---|---|---|
| `cq-title` | a scene's title line | White heavy type on a torn strip of black paper, centred on the frame whatever `left` it was given. Slides in on an entrance |
| `cq-num` | a big number in a box (`01`) | A torn yellow scrap, tilted, ringed in red marker. Stamps in on an entrance |
| `cq-stat` | the one big figure a card is about (`110k`) | A red marker arrow from it to whatever sits on its right |
| `cq-under` | a name | A red marker underline |
| `cq-tag` | a small label | Torn yellow paper, heavy type. With `cq-outline`: white paper ruled in ink |
| `cq-sheet`, `cq-slip` | a box that should be its own sheet (a node), a row | A torn white sheet; `cq-slip` is the strip shape |
| `cq-dark` | a code listing or other dark panel | Black paper, light type, a paperclip |
| `cq-mark` | line art drawn in the accent colour | Red marker instead of yellow, which is too faint on paper |
| `cq-paper`, `cq-yellow`, `cq-ink`, `cq-box`, `cq-redact`, `cq-dash`, `cq-over` | a project's own component | White paper, yellow paper, an ink block, an ink outline, a marker redaction bar, a dashed rule, lift above the cut-out |

The cut-out is the one piece a scene chooses. Name it on the scene's root:

```python
S.append(own("sc-hook", f'''<div id="sc-hook" class="scene cut-crt">
```

- Library: `cut-crt`, `cut-brush`, `cut-magnifier`, `cut-pointer`, `cut-camera`, `cut-megaphone` (`assets/vox/cut/<name>.png`). One per scene. A name outside the library throws when the page loads, so the source check stops on it.
- No `cut-` class, no cut-out.
- Half-screen seat: the card's lower right corner (x 850 to 1100, y 525 to 775), clear of the counter, which starts at y 780. Keep the card's text out of that corner, or name no cut-out.
- Full-screen seat: the right edge under the card (x 770 to 1090, y 1025 to 1345), clear of the counter at y 1350.
- `cut-top` (full screen only): beside the number at the top right (x 750 to 1050, y 190 to 490). It covers a `/ 05` beside the number, as it did in the approved mock.
- `cut-hero` (full screen only): 620 px, central, behind the type. For a title card that is only a number and a title.
- A new cut-out: add the generated source to `src/`, a line to `make_assets.py`, its name to `CUTS` in `motion.js` and a rule beside the others in `look.css`.

Nothing else is placed by hand. By the order scenes first play:

- the scrap's colour cycles teal, red, blue;
- the clipping cycles through the three;
- on a half-screen scene the scrap is lower left and the clipping upper right;
- full-screen title cards swap sides from one to the next (clipping upper right and scrap left, then clipping upper left and scrap right).

A scene written for charcoal can keep its `ground()` call: the band is hidden here.

## Motion (Chase's rules, 2026-11-16)

- **12 fps graphics, smooth footage.** Every tween on the timeline, the kit's and the scenes' included, moves 12 times a second, counted from its own start, and ends on its own last frame. Hard switches (`show`, `hide`, a caption swap, a layout switch) keep their exact frame, so words land where the plan put them. His footage is not on the timeline.
- **Jitter.** Every sheet, number scrap, scene piece, the counter and the captions shift a hair six times a second, counted from the last scene cut: full on a full-screen title card, about a third on a half-screen scene, the counter and the captions.
- **Entrances only on a layout switch.** The scrap, clipping, card, number, title and cut-out are laid down piece by piece only when a scene's window opens on a switch between half screen and full screen (read from the plan's layout runs). Any other window is a hard cut: a new scene inside one layout run, and a second window of the same scene (one scene across two beats).
- **Frame 0 is composed.** The first scene is fully laid out on the first frame; only its cut-out lands, at 0.3 s.

## Rules for anyone changing the look

- Never give a tilt or the jitter to an element a tween may transform. GSAP folds an element's own `rotate` and `translate` into its transform the first time it tweens it and writes `rotate: none` inline. Held with `!important` it is applied twice (the mock's centred title sat half its width to the left). So: the jitter is on pseudo-elements and on boxes nothing tweens; a fixed tilt is a plain `rotate`; the entrance ends the number scrap on the same -4 degrees the CSS gives it.
- No selector on the `style` attribute. GSAP rewrites inline style, so it stops matching, and HyperFrames refuses it.
- An entrance piece that starts late holds its start pose inside its ease (`held()` in `motion.js`). A `fromTo` with `immediateRender: false` shows its element at rest until the tween starts.
- Keep textures small and keep the pinned `Image` list in `motion.js`. Large textures fell out of the browser's decode cache for one step and left blank white sheets.
- The jitter is 15 tweens whose ease is the hash, not one `set()` per shift, and it is written on the pieces themselves, never on a scene's root.
- No `url()` inside a custom property. The bundler inlines images, and a variable holding one is substituted again on every restyle: one seek took 30 s, and a review render ran at a third of a second per frame.
- Do not "warm" the timeline by running it to the end and back at load. A rewind loses the transform origin the kit's `cutIn` sets (the kit's own quirk, under every look), and a card then sits 10 px off depending on how a frame was reached.
- Stepping counts from each tween's own start, not on one grid for the whole video. A cut on its exact frame followed one or two frames later by the first step of whatever arrives with it reads as a double cut, and output check O4 failed nine of them. Counted from the tween's start, the first step after a cut is three frames on. A tween shows half a step of progress on its first frame, so a line revealed by a tween is readable on its word's frame; the look's own entrance pieces hold their start pose for the first step instead (`data: "cq-hold"`), as the mock did. The jitter restarts its count at each scene cut for the same reason.
- `motion.js` must not name a scene's element id: `build.py` stops if the shell does.

## Not done

- **Font.** The heavy face is Arial Black, copied from `C:/Windows/Fonts/ariblk.ttf` to `assets/vox/ariblk.ttf`. It is a Windows font and cannot ship publicly. A free heavy face has to replace it (one `@font-face` line in `look.css`) before this look goes into the public repo.
- **Sound.** No cues of its own.
- **Popout bottom.** Not tried with this look.
