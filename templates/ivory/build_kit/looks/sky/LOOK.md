# sky

The **pixel Claude guide** acting the short out on a bright pixel sky. Chase built it up with us on 2026-11-19 on the rea short: the guide itself (five motion rounds, `work/1119-pixel-guide-test/RUN.md`), then picked this look from the stills ("sky", title in a pixel cloud, headline font Jersey 15). It was ported to HyperFrames on 2026-11-20; the HyperFrames frames match the approved test video (`work/1119-pixel-guide-test/out/pixel-guide-sky.mp4`) to within compression noise (about 1-3/255 per pixel across 20 sampled frames).

**This is not a `build.py` look.** There is no `look.css`, so `"look": "sky"` in an ivory `plan.json` stops the kit build. A sky short is hand-built on this folder's engine after the cut is approved, like blueprint. It is still reviewed in the player and approved by his click: "Review in the player" below. Record `look: sky` and his words in `RUN.md`. His real face and voice sit underneath in the normal split; the top half (1080 x 998) is the sky stage.

## What is in this folder

| File | What it is |
|---|---|
| `sky.py` | The engine's Python side: the guide's SVG poses, pixel props (`blk`), image sequences (`frames`), edge clouds, caption chunks, the HyperFrames project it writes, and `check` / `stills` / `render` through HyperFrames 0.9.13. The sound mix and the HyperFrames runner come from `../blueprint/bp.py` (same house levels) |
| `engine.js` | The timeline helpers (`pose`, `walk`, `moveX`, `hop`/`hopTo`, `blink`, `puffs`, `scene`, `typeInto`, `pose2`), captions, the cloud drift; the short's choreography is pasted in at `/*__SHORT__*/`. Registered on `window.__timelines["sky"]` after the fonts load |
| `sprites.py` | The guide: pose grids (one character a pixel, 15 px), props (blade, hammer, video block, book, keyboard), the palette |
| `sky.css` | The stage and the theme: stepped sky gradient, cream-framed cards with a navy outline, grass-and-brick floor, titles in a pixel cloud |
| `fonts/` | Jersey 15, Hanken Grotesk 600/700/800, JetBrains Mono 500/700/800 (SIL OFL 1.1, licences beside them) |
| `examples/rea.py` | The approved rea short, complete. Copy it to start a new one |

Run a short (from the repo root):

- `python templates/ivory/build_kit/looks/sky/examples/<id>.py check`: the HyperFrames check. Lint and runtime must be clean. The rea short also gets `line_unread` warnings (word-paced captions and fast beats, the approved pacing), a clipped-text note on the hook's big counter, and contrast flags on orange text on cream. Those are the approved design.
- `... stills 3.9,18.8`: HyperFrames snapshots in `<OUT>/checks`.
- `... render 4k`: `hyperframes render --resolution portrait-4k`, then `tools/finish.py` to -14 LUFS: `<OUT>/<NAME>_4k30.mp4`. The rea short took 3 minutes at 4K on the RTX 5090. Run it in the background.

## The system

- **Act it out / step back** [Chase, 2026-11-19]. When the line names something he can physically do, he does it, on the key word (cuts the video with a blade, catches the video he is handed, smashes it into its parts, ground-pounds it, types the code, holds up the guide). When the line needs proof on screen, he steps back: a peek over a card's edge, a lean in from the frame edge, or off screen while the real capture carries it.
- **Every join is a hard cut** (`scene(t, '#id')`). Not every transition is him pulling a screen; Chase disliked the iris and the tow (v4 notes).
- **The guide moves like a sprite**: stepped eases (`S(n)`) for him and his props, smooth eases for graphics. Poses swap by `display`. He stands on the floor line `FL = 950`.
- **Real material only**: the case video plays in a card as an image sequence (`frames()`), real screenshots, the report's real text typed in (`typeInto`).
- **Sky**: a four-band stepped blue gradient, white pixel clouds at the frame edges drifting sideways in steps, a different set per scene. **Titles** sit in a white pixel cloud (stepped corners, light-blue underside), Jersey 15 in navy `#1d2b53`, the key word in orange `#e8531e`. **Cards**: cream `#fffaf0` with a 6 px cream frame, a 4 px navy outline and a hard navy shadow; text on cards is navy, soft text `#5b6890`. **Captions**: cream chips on the seam, JetBrains Mono 700, 1-3 words.

## Writing a new short

1. Copy `examples/rea.py` to `work/<id>/v2/sky/short.py` (the path lines at the top change: see `work/1118-rea-sky/v2/sky/short.py`). Set `NAME`, `OUT`, `BEATS`, `IMG`, `WORDS`, `FACE`/`FACE4K`, `VOICE`, `END`, `SOUNDS`, and `CHUNKS` if some captions need hand-set breaks.
2. `SCENES`: one `<div class="scn" id="...">` per beat (the first visible, the rest `visibility:hidden`), each with a `<div class="floor">`. Start the titles at y 150, which `h1` does by default, so they clear the phone's status bar and Dynamic Island [Chase, 2026-11-20]. Drop rea's `H1_TOP = 66`: that keeps the rea test as it was approved. Lay cards out under a title that starts at 150.
3. `JS`: the choreography, beat by beat, with the engine helpers. Put the start state of anything GSAP will transform in the timeline (`tl.set(sel, {scaleY:0}, 0)`), not in CSS.
4. `STAGE`: props that live above the scenes (rea's keyboard). `POSES2` only if his copy appears.
5. Sounds: few, on his actions only (rea has six), vetted slices from `templates/ivory/sfx` at the house levels.
6. `stills` across the whole timeline, look at them, then `player`.

## Review in the player

A sky short is reviewed like a kit short [Chase, 2026-11-22]: the beat review player, notes at exact seconds, rounds, and his Approve click starting the 4K final. `tools/look_player.py` is the bridge; both hand-built looks use it.

- **Where the short lives.** `work/<id>/v2/sky/short.py`, with `OUT` = that folder (`HERE` in the worked copy `work/1118-rea-sky/v2/sky/short.py`). The player needs that layout, and a spec inside the project is snapshotted by every round, so Go back restores it. `BEATS` (the second each beat of his cut starts, the first 0) is what the player shows as beats.
- **First picture.** `python work/<id>/v2/sky/short.py player`: the 1080 review render (waits its turn on `gpu_lock`), then loaded into the player. Serve it with `python -B tools/beat_review_v2/server.py work/<id>/v2/sky` and give him the handoff as SKILL.md section 6 says.
- **A note round** (he says go in chat): `review.freeze(project)`, the smallest change in `short.py`, `player` again, `review.close_round(project, done=[...], not_done={...})`. The whole short re-renders each round (about 2 minutes for the 49 s rea short on a quiet machine, up to three times that when it is busy); beats whose frames changed are marked in the player.
- **Approval.** His click in the player. It runs `short.py final <rev>` through `autofinal.py`: rebuild, refuse unless that is the composition he approved, 4K30 at -14 LUFS, delivered as `out/<id>_sky_final_4k30.mp4`. The few cues are already in the review picture, so there is no separate sound stop.
- **What it does not have.** No per-beat render in use: `player --partial b04` films only the named beats and checks the rest with stills, but measured on 2026-11-22 it is slower than the whole render (HyperFrames' ranged render pays about 1 min 50 s of start-up per stretch, in software capture), so rounds use the whole render until that is solved. Also no native-size beat button, and none of the kit's automatic checks (motion lint, flashes, copy, geometry): the only automatic check is the render's length and that it has sound. Look at stills across the whole timeline yourself before the handoff.

## Rules learned porting it

- HyperFrames refuses CSS selectors that read the inline `style` attribute (`[style*=...]`) and tweens on `left`/`top`: write the sky colours inline, and move with `x`/`y`.
- No CSS transform under a GSAP tween on the same element: the clouds scale on an inner div and drift on the outer one.
- A `.serif` or any font family the page names needs an `@font-face` here, or HyperFrames fetches it from Google at compile time.

## Known gaps

- The rea titles sit at y 66, under the phone's island (as blueprint's did before 2026-11-20). Chase had it posted that way as a trial on 2026-11-20 (https://www.instagram.com/reel/Df-1Qd7klNW/). New sky shorts start titles at 150.
- The worked example's images live in `work/1119-pixel-guide-test/img`, which is local only.
- Not in the public repo yet.
