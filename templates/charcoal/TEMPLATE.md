# Charcoal template

Chase's long-form look: a 16:9 video for YouTube. The base is his camera full frame and his screen full frame with his face in a corner; designed graphics on a charcoal stage come in per idea, beside his real face in a window. [Chase]
Building one: `CARD.md` is the one page a builder works from. This page says what makes it charcoal and what is still open.
His words on the first video in it, 2026-11-09: "we did a really good job in terms of the sort of motion graphics we use, the general aesthetic style", "it gave it some character", "overall it was really solid". He asked for it to be kept in `/claude-edit`.
Layout numbers here and in `sections.md` are at 1920x1080. The final is the same page at twice the density, 3840x2160 at 30 fps. [Chase: "render all of this in 4K"]

## Status: DRAFT, proven on two videos

- **Two real videos went through it.** `work/1109-fable` (10m41s, a talk: graphics beside his face throughout) and `work/1110-slop` (16m18s, a screen demo: face and screen base, graphics per idea). Both approved, 4K finals rendered voice only. [Ours]
  Why: the second video changed the layout and the whole render path, and the kit caught up after it. Met when: a third video is started from `build_kit/` and finishes without editing the kit's copy in the project.
- **It is built by hand from the kit.** [Ours] `run.py`, the ownership map and the Approve click do not know this template. His approval is taken in chat.
  Met when: `/claude-edit` has a long-form path and the player loads a charcoal project without `to_player.py`.
- **The kit was proven on a copy, twice.** 2026-11-09: 1109-fable's sections built all 72 scenes byte for byte. 2026-11-11: 1110-slop's sections built all 62 scene pages and all 62 slice keys identical to the approved video's, and rendered through the GPU route. `CARD.md` lists what was and was not shown. [Ours]

## What makes it charcoal

- **The Keep list holds on every frame.** [Chase]
  Charcoal ground `#1a1917`. Text `#ebe8e0`, greys `#aaa69d` and `#77736a`. One orange, `#ff6a3d` as a fill and `#ff7a50` as text, only on the one thing that matters in the scene.
  Geist Mono for nearly everything, Hanken Grotesk for headlines. Square corners on cards, dashed hairlines `#423f3b`.
  An ASCII ground strip along the bottom 190 px (Geist Mono 22 px, `#77736a`), drifting slowly, never behind text.
  Why: he picked this from six style stills, then the texture from six more ("i love 4 its subtle enough"). Met when: a frame from any scene matches the kit's `COMMON` styles with no new colour or font.
- **The base is his face and his screen.** [Chase, 2026-11-11] "a lot of this should just be like my face and then the screen." Two shots with hard cuts: his camera full frame when he talks, his screen full frame when he shows something, his face in a corner window (360 x 450). Graphics "here and there where it makes sense".
  Why: on 1110-slop the talk layout (graphics on a stage, small corner face) was forced onto a demo; he called it "so much dead space" and nearly asked to restart. Met when: `kit.mjs` `shots()` carries every stretch that has no graphic.
- **No face-only stretch over about 12 s without a reason.** [Chase, 2026-11-11] Face-only stretches of 20 to 45 s with "no additional information" are a problem: "people want to see something". A sentence or two to camera for emphasis is fine.
  Met when: every longer stretch to camera has a graphic for its idea, or a reason in `RUN.md`.
- **Never text over his full-frame face. No slow push on a screen recording with nothing else changing. No floating card on an empty stage.** [Chase, 2026-11-11] "That looks terrible"; "I don't know why we have these subtle sort of zoom ins". Zooms and soft transitions are fine when they have a reason.
- **Beside a designed scene his face is in a window.** [Chase] A 4:5 crop of his real camera, 480 x 600 large (right or left) or 258 x 322 in the bottom-right corner. Rounded corners, radius 113.
  Why: he asked for "my face popping up" beside the graphics, and picked the rounded window ("B") on the pilot. Met when: `sections.md`'s layout table holds and nothing covers the window.
- **He hears the cut before graphics exist, sees stills before anything renders, and reviews by segment.** [Chase, 2026-11-11] He expected a note to cost minutes ("not make this a 5-hour process"). The cut listen takes his timing notes; the storyboard (`build_kit/storyboard.py`) is approved by number; the player shows one beat per named segment (one idea, 10 to 40 s); rendering is by slice.
  Met when: a note on one graphic re-renders one slice.
- **No label on his face, no banner, no brand bar.** [Chase] "id get rid of the corny chase came thing"; "no banner".
  Why: cute fake labels read as corny to him. Labels that carry real information (the rule number, the docs URL) stay. Met when: every label on screen names something real.
- **Readable first.** [Chase] "we really just want this to be readable", "easy for people to follow and watch".
  Met when: `sections.md`'s size floors hold: headlines 84 px or more, nothing under 24 px.
- **Real sources.** [Chase] He asked for "real pulls from the docs page". A docs pull is a real screenshot with the quoted sentence highlighted where it really sits. Numbers come only from `work/<id>/facts.json`.
  Why: `HOUSE.md`'s verified-facts rule. Met when: every figure and quote on screen traces to `facts.json` or a capture.
- **Every reveal lands on a spoken phrase.** [Ours] Nothing appears to fill time. Met when: each reveal in a section is timed through `cue("...")`.
- **A small set of scene kinds carries the designed parts.** [Ours] A typed chapter title, a real docs pull, a prompt card, a small diagram, a statement, and (since 1110-slop) his real screen or stills of it arranged as a graphic. `sections.md` says when each is used.
  Why: it is why a video reads as one piece. Met when: a new kind of scene is named in the handoff, not slipped in.
- **Voice only is an acceptable final.** [Chase] 2026-11-09: "with no sound effects, it's still just fine".
- **Full-frame face is a base shot here.** `template.json` sets `full_face` true. [Chase, 2026-11-11: picked "Full-frame hook + outro", then asked for face and screen as the base] Long-form only; shorts keep their own rule.

## Open decisions: flag them, never settle them here

- **Sound in long-form.** Parked by him on 1109-fable, to be worked on later "as a practice training thing". A rule 1 trial exists (`work/1109-fable/tools/sound_pass.py`, 18 cues, ivory's sound rules). When it resumes, cues go in the review player's cue lane (`sound.json`), never a side file: he asked "Why doesn't it show the cues in the editor? Why is it in a separate file?"
- **The window's corners with a clean camera.** Radius 113 was picked while the camera file had OBS's circle mask baked in. With an unmasked camera a wider or square window becomes possible. His call.
- **Shorts use this look too, as a second look on ivory's kit.** [Chase, 2026-11-10: "couldn't we say that's now one of our styles? Because it did a good job of that."] It lives in `templates/ivory/build_kit/looks/charcoal/`, on ivory's split layout, not this folder's 16:9 kit. Its chip, counter and ground-band placement are calls he has not ruled on.
- **Spoken lines that differ from the source.** On 1109-fable they were logged in `RUN.md` and he never answered. Proposed, not a rule: put them in the cut report so a retake is still cheap.

## Read order

| # | File | What it decides | Read by |
|---|---|---|---|
| 1 | `templates/HOUSE.md` | Standards for every template. Its 9:16 numbers do not apply here; its non-negotiables do | Everyone |
| 2 | `templates/story.md` | Which lines survive the cut | Spine only |
| 3 | `templates/charcoal/TEMPLATE.md` | This page | Everyone past the spine |
| 4 | `templates/charcoal/sections.md` | What goes on screen, layout, style, how a section file is written and checked | Director, section writers, reviewers |
| 5 | `templates/charcoal/CARD.md` | The one page: rules, flow, commands, the scene kit, rendering | Whoever builds or renders |
| 6 | `templates/charcoal/build_kit/README.md` | Reference for each kit script | When the card does not answer it |

- **Chase wins every conflict.** [Chase] Then `HOUSE.md`'s non-negotiables, then this page, then `sections.md`.
- **The look's numbers live in `build_kit/tools/kit.mjs` and `build.mjs`.** [Ours] If a rule file quotes a number and the kit differs, the kit wins and the gap gets flagged. Why: two copies drift.

## What charcoal owns

| Owned by charcoal | Owned by the spine, once per raw |
|---|---|
| Which visual each sentence gets | The cut, transcript and voice audio |
| Where the face window sits and when it moves | Word timings and BIG joins |
| How each capture is shown | Verified facts in `work/<id>/facts.json` |
| Chapter titles and the chapter list | The clean camera cut |

## The flow

`CARD.md` has the steps, the stops and the commands. In short: intake with a face check, the cut and his listen, facts and captures, a plan in named segments with a stills storyboard he approves, a pilot of the first chapter, the rest, review renders by slice with notes in the player, his approval in chat, the 4K final.

For the upload: `out/<id>-<rev>-chapters.txt` is the chapter list. Captions: `python tools/words_srt.py work/<id>/full/assets/words.json <out.srt>` after fixing the transcript's known slips. Titles and thumbnails: `/yt-package`.

## Where the details live

| Detail | Source |
|---|---|
| Palette, type, components, motion helpers | `build_kit/tools/kit.mjs` |
| Stage, ground strip, face window places, slices and their keys | `build_kit/tools/build.mjs` |
| Rendering, storyboard, player load, face track | `build_kit/render_slices.py`, `storyboard.py`, `to_player.py`, `face_track.py` |
| Two approved section files to match | `build_kit/examples/` (another video's content: read, never copy its facts) |
| The first video (a talk) | `work/1109-fable/full`, `work/1109-fable/RUN.md` |
| The second video (a screen demo; the current flow came from it) | `work/1110-slop/full`, `work/1110-slop/RUN.md` |
| The style stills he picked from | `work/fable-prompting/styles/out/` |
