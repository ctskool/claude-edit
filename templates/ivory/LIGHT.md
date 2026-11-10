# Ivory, one page (light path)

What one builder needs to plan and build an ivory short. Numbers are at 1080x1920; double them at 4K. Chase wins every conflict. The full rule files (`HOUSE.md`, `layout.md`, `captions.md`, `STYLE.md`) stay the source; open one only when this page does not answer the question, and log that you did.

## Hard rules (Chase)

1. **Real footage only.** Crop, scale, move, mask or matte his real pixels. Never generate, stretch, inpaint or extend him or his background. No generated people.
2. **No bottom fade.** No dark fade, gradient or scrim under him. His body runs off the bottom edge in real pixels.
3. **No full-screen face unless `full_face` is turned on.** On only when `template.json` says so or Chase asks in words for this edit; record his words in `RUN.md`, `beats.json` and `plan.json`. Off means his face stays in the bottom half and `face_full.mp4` is not used.
4. **Verified facts only.** Every number, name, price and quote on a graphic has a `facts.json` entry with source and date. His quoted words trace to `raw/cut_words.json`. A spoken figure nobody verified stays in the caption, off the graphic. No fake "test" slides.
5. **Safe zones.** All graphic ink inside y 120-880, x 60-1020, main content centred near y 470. Warn only: nothing key above y 200 or below y 1620.
6. **Switch on what is said, never on a quota.** Each layout switch cites its line.
7. **A top half that only repeats his words is banned.** Show something real: a capture, his own clip, the thing discussed, a returning graphic. A quiet one-line serif panel is the rare exception (CTA, pure opinion hook), never two in a row.
8. **Images through `codex exec` only.** Without Codex, no generated images.
9. **No donor looks, unless the look is one Chase asked for from a reference:** no near-black grid, glow, neon, grain, glassmorphism, gradients, kinetic word slams, emoji, sentence-case captions, browser-window screenshot cards as the main device, CTA buttons or arrows.

## Layouts

| Layout | Use when the line... | Length | Frame |
|---|---|---|---|
| split (default) | explains or points at the thing, setup, connective lines; with `full_face` off also opinion, payoff, CTA | break past ~8 s only if a line earns it | panel y 0-960, face cam y 960-1920 |
| full-graphic | needs the whole frame: name reveal, A vs B, list of 3+, big number, before-after, demo clip | 2-4 s | face hidden, chip at y ~1480-1570 |
| full-face (only when `full_face` is on) | opinion, direct address, payoff, CTA, a visible jump cut | 1-2.5 s | `face_full.mp4`, title or chip on the shirt, never on the face |

- Switches are hard cuts, on the stressed word or a sentence boundary, 0-0.08 s early, never late. No two within ~1.2 s. Vary the order.
- A switch beside a cut goes on the cut frame (within 0.08 s reads as a double cut). Check the join frame in the face clip, not just the cut's time.
- Every BIG join is covered: a takeover starting on it, a join inside a takeover already up, a split punch-in inside the bottom half (scale ~1.08, cut in, eased out), or with `full_face` on, a full-face punch-in.
- The graphic is up on the switch frame: no empty panel, no gap, no overlap. Frame 0 shows the hook's visual.
- A scene never spans a beat edge: each beat renders on its own, and a card that crosses one jumps at the join. A picture that holds across two lines is one beat.
- A payoff (a number, a name, a list's last row) stays up at least one second. If the cut is close, land it a stressed word earlier.
- Before building, check the plan against every line of the intake notes.
- The CTA shows only his words, starts clean, holds to the last frame. No sound on the CTA hold.

## The frame

- Panel y 0-960: ivory `#EEEEE7`, opaque every frame. Optional faint grid, 40 px cells, `rgba(0,0,0,.035)`.
- Face cam y 960-1920: `assets/face_half.mp4`, object-fit cover, hard edge, no border.
- Composed seam is y 960. The raw seam (~y 996 in his split composites) only sets the face crop.
- Nothing sits on his face or hair. The chip holds; a graphic that crowds it moves.

## Look

- **Palette:** ivory `#EEEEE7`, card `#FFFFFF`, card border `#E4E2DA`, hairline `#D9D6CC`, ink `#1F1E1D`, secondary `#5E5D59`, muted `#8A887F`, clay `#D97757` (deep `#C15F3C`, tint `#F6E3DA`), dark panel `#1F1E1C` with text `#EDEBE4`, green `#2E9E5B` for check marks only.
- **Type:** Newsreader 400/500 headlines 120-150 px, tracking -0.02em, ONE italic clay word. Sub-line Inter 500 30 px `#5E5D59`. UI Inter 500-700, 26-40 px. Labels JetBrains Mono 22 px, tracking .14em, `#8A887F`.
- **Card:** white, radius 22, 1 px `#E4E2DA`, shadow `0 12px 32px rgba(40,30,20,.07)`. Real captures and clips sit inside cards; rebuilt vector UI is the default device.
- **Motion:** calm. Arrive y +24 to 0 with opacity, 0.55 s `power3.out`, 70 ms staggers. Something progresses about every second; a beat over 1.5 s is never static (slow push 1.00 to ~1.04, typing, a check, a count). Checks `back.out(2)` 0.35 s. No blur, glow, shake or whip.
- **A beat that holds the last beat's picture gets no entrance**, only the push, continuing from the last scale.
- **HUD** (optional strip, y ~783-897): only when the video counts something. Once on, it carries across layouts and never resets.

## Caption chip

- JetBrains Mono 500, UPPERCASE, tracking .04em, `#F5F4EE` on `#1B1D1D`, radius 10, ~52 px text, ~96 px chip, inside x 60-1020.
- 2-3 words a chunk. Clay accent `#E0907E` on at most 10% of chunks, product names and keywords only.
- Hard swap: no fade, pop or karaoke. Opens ~2 frames before its first word (the build refuses more than 5 early or 2 late).
- Every spoken word gets a chip, verbatim from the corrected transcript. A number with its unit, a brand or a decimal stays on one chip.
- Sits on the seam (centre y 960) in split, y ~1480-1570 on a takeover, on the shirt in full-face (`full_face` on). Never crosses a layout switch or a join.

## Defects to check on the render (everything else is taste)

A broken hard rule. A typo, clipped text, content outside its card. A wrong, dropped or uncaptioned word. A graphic off its word, or held too short to read. A one-frame flash, black frame, frozen video, double cut, a state snapping at a join. A visual that does not show its line, a half-loaded screen, an annotation off target. A payoff before its proof.

Each finding names the item, the frame or time, what was expected and what is there. A reviewer never reports: redesigns, "this could be better", different copy phrasing, motion-feel opinions, more or fewer graphics.

## Build

Follow `templates/ivory/build_kit/README.md` for `plan.json` and caption-chunk fields, `owners.py`, `scenes.py`, `timeline.js` and the QA order.
- A full-face beat (`full_face` on) has no scene. Bind its anchor to its own chip: owner `cap.wNNNN-NNNN` (the chunk's first and last word), target `[data-own='cap.wNNNN-NNNN']`, expect `present`. Put the anchor on a word that starts inside the beat.
- An element already up on the switch frame, a frame ahead of its word, takes `lead_frames` 1 as its bind's sixth field.
- After the review render, run `python tools/beat_check/jumps.py <project>` and look at what it names. Reuse a proven scene from `templates/ivory/library/INDEX.md` before writing a new one.
