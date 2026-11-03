# Ivory sound rules

Chase wins any conflict. Tags: [Chase], [Ours].
"(untested on ivory)" means ivory has not proven that rule yet.

## Strategy [Chase, adopted 2026-11-01]

Chase, on the first 1030-2 sound: "haphazard". He asked for a real strategy, then heard this one on 1030-2 and approved it: "Good, rebuild final". Evidence: `reports/2026-11-01-sound-strategy/`.

**Sound points at what changed. The voice explains.** A sound marks the moment the viewer should notice. Being visible does not earn a cue. No study shows sound effects lift retention in this format, and in controlled learning tests extra effects can hurt, so a cue justifies itself.

**Pick the moments before the files, in this order:**
1. **Structure.** A switch that brings a graphic in takes its layout sound. Simultaneous pieces of it are one cue. A graphic leaving and a cut to the face stay silent.
2. **The main argument.** The central change, then the strongest proof or correction. Prefer that action over the generic card entrance around it.
3. **Helpful detail.** Only what helps follow the proof. Repeat page arrivals, recap rows and HUD steps usually stay silent.
4. **Reading time.** Faces, captions, words alone, cursor travel, scrolling, carets and reading holds get nothing.

**Budget.** Start a 45-60 s short with its required layout sounds plus 3 to 6 content moments, roughly 8 to 11 cues. This is neither a quota nor a cap: 1030-2 took 12. Explain each extra by what it tells the viewer.

**Write each cue's job in its `placement`:** main, structure or detail, the pictured action, and why sound beats silence.

**Choose a sound by how it sounds, never by its name.** Read `sfx/SOUNDS-LIKE.md`: it measures every default sound. Those notes are UNVERIFIED by ear until Chase fills his column, and his ear wins. A filename proves nothing: "whoosh" was rumble and "marker" is a scribble.

**No fitting sound means silence and a logged gap.** If the moment truly needs one, ask Chase to audition it. Never substitute, generate or import a sound.

**Opening and close.** Accent the hook's first real change, and don't force a sound onto an already composed first frame. The close takes the same test, and silence is never filled with a flourish. A summary or direct address isn't automatically a CTA: a close with no viewer request can take a cue, as 1030-2 did at 54.7 s.

## Library and classes

Chase, 2026-10-31, on the HyperFrames library at 0.18-0.3 gains: "super over the top", "doesn't really sound premium at all". [Chase]
That library, its risers, sub hits and cinematic whooshes are retired. He heard the replacement on 1030-1 v3 and called it "definitely better moving forward". [Chase]

Files: `templates/ivory/sfx/` (copied into the job's `shared/sfx/`). `sfx.json` there holds each sound's source, slice and level. `python tools/sound_mix.py slices` re-cuts them.
They are hand-vetted sounds, cut into slices. Pick the class from what is on screen.

He then auditioned a whole hand-vetted library on 2026-10-31. His picks are in `audition-picks.json`, and every yes is in `sfx.json`. [Chase]

| Event | Sounds |
|---|---|
| Layout switch, takeover in | whoosh-d and the earshot moves Chase passed on 2026-11-02 (`es-swish-*`, `es-swipe-*`, `es-whoosh-fast-*`). Rotate them, never the same one twice in a row. No paper sound unless paper moves on screen |
| Something flying or docking, a film-style transition | whoosh-d, the `es-` moves, film-burn |
| The graphic's main object landing | pop-hero |
| A sibling object landing | pop, pop-2, metal-pop, bubble (round objects), es-pop-0, es-pop-1, es-pop-3, es-pop-4, es-fit-pop-mouth-plop |
| A solid block or card set in place | es-knock-wood, es-knock-plastic, es-knock-snap |
| A later object, or a burst as one cue | pop-soft |
| A row ticking on in a list | lighter |
| A visible cursor press or release | click, click-b, es-click-snap, es-fit-click-floss-lid |
| Cursor travel, drag selection | nothing. Chase: a click "doesn't make sense" on a drag |
| A switch or toggle | switch |
| Typed text | typing, typing-b, typing-c, typing-d |
| One key press, a single word or a send | es-typing-key-clicky, es-typing-key-thock, es-fit-key-lubed, es-fit-key-medium |
| A phone tap or ring | tap, phone-ring |
| A snapshot or a recording starting | camera, shutter, camera-snap, camera-rec, camera-focus |
| One straight strike-through | pencil-a, pencil-b, alternating. Real pencil strokes Chase picked on 2026-11-02, after hearing pen, marker and earshot candidates on 1030-2's strike: "it should sound like a pencil" |
| One highlight wipe | highlighter. Trim `dur` to the stroke. Chase: no "scribbling sound" on a straight line |
| Repeated scribble or sketching | marker, only when the picture truly scribbles |
| Box trace, glow, annotation arrow | nothing by default |
| A hard snap | snip |
| Paper moving, and only real paper on screen | paper-fast (first 0.6 s, `dur` 0.6), paper-slow, sheet-slide. [Chase] 2026-11-02: "I don't like the paper fast at all for these unless it's like literally showing paper moving." |
| A system or status change | ui-tick-a, ui-tick-b, ui-tick-c |
| Time running | clock |
| Completion or verdict | bell |
| Any cut to the face, a graphic leaving (full-graphic to split), HUD steps | nothing |
| The CTA | nothing |

**Special sounds play only when Chase asks for one in a note or a plan:** impact, deep-hit, deep-hit-2, deep-hit-3, sub-drop, heartbeat, heavenly-choir.
Why: he approved these sounds, and he also called constant hits over the top. So they are available and never a default.

Only sounds in this section play. A new one joins after Chase has heard it, because the agent cannot hear.

## Levels [Chase note, measured on the references]

**Set each cue against the voice playing at that moment, by its job.** Measure 250 ms from the slice's attack against the voice over the same span. [Chase] approved this on 1030-2.

| Job | dB under the voice playing |
|---|---:|
| main | 9 |
| structure | 11 |
| detail | 13 |

Cap every cue's peak at -8 dBFS, so sharp sounds can't spike. Some land quieter than their target because of it, which is fine.
A whole-track LU figure can't show a short cue is audible, so never pull cues down to hit one. 1030-2 landed at 11.4 LU this way.
**Check where a sound's energy sits before raising it.** Small speakers play little below about 200 Hz, and exact limits vary by device. whoosh-a, b and c hold 69-96% of their energy there, so they stay in the library but are out of the layout default. pop, pop-soft and pop-hero sit inside the voice's range and can be covered by it. More gain fixes neither.
Listen on a phone speaker as well as headphones.


Levels come from `sfx.json`'s `target_db` as each slice's starting point against speech, not a shared gain. The job table above sets the final level. A gain tells nothing, because source files peak anywhere from -14 to 0 dBFS.
Why: at gain 0.22 the first 1030-1 cue track sat 5 LU under the voice.

| Same stem measurement (Demucs) | Hit vs speech, dB | Hits per 30 s | Quiet floor vs speech, dB | Bed |
|---|---|---|---|---|
| reference creator A, 3 reels | -29 to -35 | 2.4-5.0 | -45 | none |
| reference creator B, 3 reels | -29 to -32 | 4.5-7.6 | -29 to -34 | yes |
| reference creator C, 3 reels | -20 to -29 | 6-25 | -25 to -30 | yes |
| 1030-1 v2, retired | -14 | 12.6 | -42 | none |
| 1030-1 v3 | -29 | 2.5 | -44 | none |

Stems lose quiet sounds, so reference hit counts are a floor. Compare a candidate to the references only through the same stems: 1030-1 read reference A's numbers at these levels, 5 dB above the first try.
The check reads the cue track directly, which needs no stems. Its band was 18-26 LU, set around that 1030-1 mix, which read about 25 LU directly and about 37 LU on stems. It is not a reference reading. On 2026-11-01 Chase heard the 1030-2 mix at 11.4 LU and approved it, after calling 23.4 too quiet, so the floor is now 10 LU. The 5 LU mix he called over the top stays out. [Chase]

Met when: `python tools/sound_mix.py check-mix <project>` passes: the separate cue track sits 10-26 LU under the voice. Density above 8 cues per 30 s warns; Chase says it "just has to make sense".
`finish.py` can fall back to dynamic loudness, which moved this figure less than 1 LU on 1030-1, so it describes the mix before mastering.

## Variety

1. **One cue per event.** [Chase]
   Why: 27 cues from 7 files sounded "a little repetitive".
   Met when: each cue in the render names one event, and no event has two cues. A card landing on a switch is one event.
2. **Rotate within the class. The same file never plays twice in a row.** [Chase]
   Why: click-soft and pop carried 63% of the first finals. Editorial v12 used 15 sounds for 28 cues.
   Met when: `python tools/sound_mix.py check-sheet <project>` passes the back-to-back source-slice check.
3. **No file carries more than 25% of the cues.** [Chase]
   Why: one file over that share is what reads as repetitive.
   Slices of one source count as one file, so pop-hero, pop and pop-soft are one. Motionlint counts slice names and cannot see this.
   Met when: `check-sheet` passes the share by `sfx.json` source file, at most 25%. Under 8 cues it skips that cap with a note.
   Under 4 cues the cap cannot hold, and a class limit can break it too. Flag that, and never add a cue to meet it.
4. **Above 8 cues per 30 s is a warning; cues sit at least 1.2 s apart.** [Chase] 2026-10-31: it "just has to make sense".
   Why: sound marks events. Silence is fine where nothing happens. 49 cues in 107 s read as over the top.
   Met when: `check-sheet` passes spacing. `check-mix` warns on the whole-clip average and prints the busiest 30 s for information.
   The rate is a warning, never a target. Never add a cue to reach it.
5. **Never mask a stressed word.** [Chase]
   Why: the voice carries the short, and switches land on stressed words.
   Met when: rotation still picks the file, and a cue on a stressed word drops in level or is dropped. Masking stays UNVERIFIED until Chase listens.
6. **Layout switches that bring a graphic in rotate through whoosh-d and the `es-` moves, never one fixed sound. paper-fast is out of layouts.** [Chase]. Changed from the three-whoosh family on 2026-11-01, after 1030-2. The 14 `es-` moves joined on 2026-11-02 when he passed them in the earshot audition.
   Why: one sound for "the frame changed" teaches the ear, but identical repeats are what Chase rejected, and the old family was mostly rumble that small speakers lose.
   Those switches are split to full-graphic and, with `full_face` on, full-face to split and full-face to full-graphic, outside the CTA. A graphic leaving and any cut to the face are silent.
   Met when: each of those switches uses that pair, unless the 1.2 s spacing forces a logged silence, and no two in a row share a file.

## What gets a sound

7. **Sound the literal thing on screen, never the animation.** Abstract graphics may take an approved abstract accent, such as a pop on a comparison result. [Chase, 2026-11-01]
   A cursor press takes click. A card landing takes a pop. A toast or status change takes a ui-tick. The frame changing takes a whoosh.
   Why: a generic sound says "an animation happened". The literal one says what happened.
   Met when: each cue can name its on-screen object, and its class fits that object. A rendered press with no cursor is not a click.
   A literal pick never breaks rules 2 or 3.
8. **Every sound sits on a visible event.** [Chase], tightened by (untested on ivory)
   Why: under plain talking a sound only competes with the voice.
   Met when: the frame at each cue time shows the event starting or landing.
9. **The face and captions are silent.** (untested on ivory)
   No cue on a caption swap, a spoken word, a bare talking stretch, an element leaving or a cut to the face.
   A layout switch into a graphic stays an event. [Chase] With `full_face` on, the old full-face punch-in class is still gone after his 2026-10-31 note.
   With `full_face` off, a punch-in inside the bottom half is a cut to the face, so it is silent too. [Chase]
   Why: captions run the whole clip, so sounding them would sound every word. A hit on his face adds drama to a plain sentence.
   Met when: no cue's event is a caption, a word or an exit.
10. **The bell means completion.** (untested on ivory)
    `bell` plays on something finished or a verdict. A status that only turns on (connected, live, online) takes a ui-tick.
    Why: the bell rewards something finished. A status coming online is the system talking.
    Met when: no bell sits on a plain state change or a card landing.
11. **Nothing over proof audio.** This outranks the other rules here, never a [Chase] rule. (untested on ivory)
    While a played clip's voice or a product's own sound is the evidence, no cue plays until it ends.
    A [Chase] cue due inside that span, such as a layout switch, is flagged for him.
    Why: that audio is the proof, and a cue on top makes it feel produced.
    Met when: `check-sheet` finds no cue's audible span, tail included, overlapping a beat's `proof_span` carried into `plan.json`. A conflict stops the sound stage and is flagged for Chase.
12. **Sound actions, not every state change.** (untested on ivory) One beat may hold a required layout sound and a later, separate proof action if spacing and tails allow. [Chase, 2026-11-01]
    The panel moves about every 1 s, and most of that motion is silent: caret blinks, scrolls, small drifts, progress steps.
    Why: two accents on one beat is clutter. Tails count too: a sound that rings past a cut to the face breaks rule 9.
    Met when: each beat in `plan.json` carries one cue, or a layout sound plus one distinct proof action.
13. **A burst is one event.** (untested on ivory)
    Pills or slots landing closer than the 1.2 s spacing take one cue for the whole burst.
    Slots that land on their own spoken words stay separate events.
    Why: repetition reads as a pattern, and per-hit sounds would break rule 2.
    Met when: no burst has a cue per element.

## Timing

14. **Align the attack, not the clip start: about 0 to 0.08 s after the event.** (untested on ivory)
    That is his 0 to 2 frames on 24-30 fps timelines. The lead is per slice: `tools/sound_mix.py slices` prints each one.
    Why: an ear hears sync at the attack, and one offset for a whole class lands some files late.
    Met when: each cue starts its slice's attack before the event, plus up to 0.08 s. How it sounds stays UNVERIFIED until Chase listens.
15. **No build-ups or impacts unless Chase asks for one.** [Chase note, 2026-10-31]
    Why: risers and sub hits are trailer sounds. On a talking-head explainer they read as over the top. A riser goes in only on request, once in a piece.
    Met when: no cue uses a riser or a cinematic whoosh, and each special sound traces to his note or plan.
16. **Typing runs from the first letter to the last.** (untested on ivory)
    Cut a typing slice to the typed span with the cue's `dur`, and fade its last 0.05 s.
    Why: typing that starts late or runs on detaches from the words.
    Met when: the sound starts on the first letter and ends within about 0.04 s of the last.

## After the first pass

Sound is authored after picture approval in `work/<id>/v2/editorial/sound.json`, separate from `plan.json`. Every cue names an immutable plan `event_id`. The sheet binds to `picture_rev`, including the voice and referenced media contents. An empty sheet is valid; final delivery requires its `empty_reason`.
Run `check-sheet` for placement and revision, `check-mix` for separate-stem level and density, and `check-media <delivered.mp4>` for the mastered file's loudness, true peak, duration and audio stream. `check` remains an alias for the first two. These checks cannot hear masking or sound quality.

17. **A graphic added to a sounded edit is weighed for sound.** Silence is fine where nothing earns a cue. [Chase] (untested on ivory)
    Use that edit's files and levels. If a graphic moves, move its sound to the same event.
    Why: a sound with nothing under it reads as a mistake.
    Met when: a new graphic's cue passes the spacing, masking and event rules, and no cue lost its event.
18. *(Retired 2026-11-02: a CapCut-push detail. It belongs with the CapCut tool when that gets built.)*
19. **Chase's hand pass wins.** (untested on ivory)
    Never re-apply the planned cues over his CapCut changes. Diff first.
    If a graphic moves under one of his sounds, report the measured shift and let him move it.
    Why: his hand edit is the strongest taste evidence there is.
    Met when: every difference is logged as his note, and no rule changes without his yes.
20. **Report what nobody heard.** [Ours]
    Why: the agent cannot hear. Checks prove placement, not how it sounds.
    Met when: the handoff lists sound quality, stressed-word masking and phone-speaker audibility as UNVERIFIED until Chase listens.

21. **No music bed.** [Chase] 2026-10-31.
    Met when: the mix is the voice and the cues, nothing else.

## Open decisions (not settled here)

- **Loudness target.** Renders normalise to -14 LUFS today. Whether that stays is Chase's call.
