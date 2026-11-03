# House standards

Every template reads this one file and may add to it, for `/claude-edit`. (untested on ivory) Chase wins any conflict. [Chase]
His sources: STYLE.md "Chase's house rules" and his saved notes. A source tag is not an approval.
Only Trial ideas are off. "(untested on ivory)" rules are active here, but yield to every [Chase] rule and measured STYLE.md number.
Layout numbers here and in STYLE.md are at 1080x1920. Double them on the 2160x3840 canvas. Seam rows: `ivory/layout.md`.
Restate any frame count in seconds, then snap once to the output grid. [Ours]

## The product
- **Raw in, finished edit out, repeatable on a new raw.** Ivory is the baseline. [Chase]
  Why: he wants dependable output, not a design exploration. Met when: a new raw needs no polish rounds.
- **The spine runs once per raw. Each template owns its assets and edit style.** [Chase]
  Why: facts and the cut must match across versions. Met when: a second template re-runs no transcript, cut or audio step.
- **A template may override pacing.** [Chase] Today it does so by taking listed trims before graphics, one template per output. [Ours]
  "Never re-cut from raw" is a proposal waiting on his yes. Why: a blend cannot pass a lock. Met when: the run names one template version and its trims.
- **Publish 4K60 (2160x3840, 60 fps). Review an MP4 with chat notes. CapCut draft after approve. Finish last.** [Chase]
  Why: he cannot review what was not rendered, and notes must stay cheap. Met when: no notes round runs through CapCut.

## Build path, today's tools [Ours]
Ivory is `editorial` to the tools: spec `styles/editorial/STYLE.md`, flag `--pack editorial`.
1. Cut with `tools/rawcut.py` (`story.md`), then `python tools/prep_source.py <raw>/cut.mp4 work/<id> --face-top 0.52`.
2. Plan in `work/<id>/beats.json`: `layout_hint`, `hint_why`, `visual {type, why}`. Before render, each beat's words, layout, asset, fact, hold and join cover must agree. The built `plan.json` gives each anchor and action an immutable `event_id` and carries `cta_start` and beat `proof_span` times.
3. Picture preview: `python tools/deliver.py work/<id>/v2/editorial <id>_editorial_<vN> --mode picture-preview`. Voice only; never two renders at once.
4. After picture approval: `tools/workflows/next/sound-cues.js` writes `sound.json`, then `deliver.py --mode final --picture <approved-render>` reuses the bound picture. Missing or stale sheets stop finals. Cue-only notes never call HyperFrames.
Preview: 1080x1920 at 30 fps. `deliver.py` also accepts `--resolution portrait-4k --fps 60`; preparing the 4K sources is still a hand route, proven only on 3 s, slow and unmeasured on a whole short.
Stand-ins until built: `work/<id>/raw/corrections.json` (wrong -> right), hand-written `notes.jsonl`, `RUN.md`, `LOCK.md`, and a `raw/cut_words.json` index as word ID.

## Non-negotiables
- **Real footage only.** Crop, scale, move, mask or matte his real pixels. Never generate, stretch, mirror-tile, inpaint or extend him or his background. [Chase]
  No generated people, AI cold open or lip-sync. Why: fabricated pixels look fake. Met when: every face or body layer traces to `raw/cut.mp4` or `raw/cam_cut.mp4`.
- **No bottom fade.** No dark fade, floor gradient or scrim. His body runs off the bottom edge in real pixels at every scale. Too tight? Make him bigger or re-layout. [Chase]
  Why: a fade reads as a floating head in a void. Met when: the bottom edge shows camera pixels wherever he is on screen.
- **No full-screen shot of just his face unless a template or Chase turns it on.** For each run, `allow_full_face = template.full_face OR his request for this edit`, default false. Skipping a page or running auto or lock mode grants nothing. [Chase]
  A template opts in through `templates/<name>/template.json`. Ivory does not. Why: he wants them only in certain templates, or when he asks. Met when: `RUN.md` and `plan.json` record the result and its source, and with it off no beat uses `assets/face_full.mp4`.
- **Verified facts only.** Every number, name, price and quote on a graphic traces to a source. No fake "test" slides. [Chase]
  One test everywhere: a figure needs a `facts.json` entry with source and date. His quoted words trace to `raw/cut_words.json`. [Ours]
  The transcript proves only what he said, so an unverified spoken figure stays off graphics and gets flagged. [Ours] Why: one wrong figure breaks the proof. Met when: each fact passes.
- **Safe zones for 9:16.** Ivory: graphics in y 120-880, x 60-1020. Chip on the seam at y 960 in split, y ~1480-1570 on takeovers. [Ours]
  Why: this is STYLE's measured area. Met when: measured on the render, on every entrance's first frame and every hold.
- **Switch on what is said, never on a quota.** Every sound marks an event and rotates. [Chase]
  Why: he rejected hard quotas and repetitive sound. Met when: each switch cites its line, and no sound plays twice in a row.
- **Images go through `codex exec`. Without Codex, no generated images at all.** [Chase] Why: his standing route, and the skill assumes plain Claude Code. Met when: every image came from `codex exec`, and a run with `codex` false has no scene beats.
- **Donor rules may pass in. Donor looks may not:** no near-black grid, 12 fps stepping, bloom, grain, glow, scan lines or CTA components. [Ours]
  Why: copying a donor's process must not change the look. Met when: none of these appear in any composition.

## Popout bottom, any template [Chase]

- **Popout is a bottom option every template can offer, not a template of its own.** [Chase] 2026-11-02: "every one of them could have the pop out version of it." Split beats put him in a rounded card that runs off the frame's bottom edge, with his real cut-out rising above the card's top. Full-graphic beats, and full-face beats when `full_face` allows them, don't change.
  Why: a different look on rules he already trusts, without a new routine. Met when: the template's `template.json` has a `popout` block and `plan.json` records `bottom` and `bottom_source`.
- **Per edit, `bottom` is `split` unless Chase asks for popout.** His exact words go in `bottom_source`. A note can switch it later, and that re-renders the whole video.
- **The shared part is `tools/popout.py`.** It measures where his head sits across the whole video, crops the clean camera around it, and makes the cut-out with `tools/matte.py`. It picks the largest size whose highest head position still clears the template's `clear_y`, and puts the card edge 65 px under the top of his head. Every template uses the same tool and math.
- **A template gives only its own parts.** In its `template.json` `popout` block: `card_x`, `card_w`, `clear_y` (the lowest edge of its seam caption plus a margin, which his head never crosses), `radius` and `card_css` (its card look). Its build kit swaps in `popout.css`, `popout.markup`, `popout.twin` and `popout.roots` when `plan.json` says `bottom: popout`.
- **Faces stay out of the platforms' caption block.** TikTok and Reels cover roughly the bottom quarter and a right-hand button column. `popout.py` warns when his face centre falls below y 1440. Why: Chase, on the first small popout: "you'd barely be able to see me."
- **A bad cut-out means split for that video.** A halo, flicker or missing fingers on the edge: use split, never ship the edge. `popout.py` flags cut-out area jumps between sampled frames. Check them by eye.
- Proof: `work/1030-2-popout/POPOUT.md`. Chase picked the size from four mocks (variant 2).

## Warn only, until Chase rules
Active but untested. A miss is logged as a warning and never resets a lock, unless the defect list below names it. [Ours]
- **Platform bands.** No key content in the top 200 px or bottom 300 px, so y 200-1620. His body may run past it. (untested on ivory)
  Why: platform UI covers those bands. Met when: ink above y 200 or below y 1620 is logged. STYLE's safe area stays the hard rule.
- **Face and caption stay clear.** No ink on his face, hair or the caption band. The graphic gives way first. No room in a tight take: flag it. (untested on ivory)
  With `full_face` on, his title or chip on the shirt stands. [Chase] Why: a card on the hair reads as a mistake. Met when: no sampled frame shows ink on either.
- **Readable means whole, big and flat.** The words being read hold still. Past 1.5 s something else keeps moving (STYLE.md). (untested on ivory)
  Why: a clipped or tilted screen proves nothing. Met when: at phone size, nothing the viewer must read is cut off.
- **On the word, measured on the render.** Picture, caption and sound land on their word. A designed lead gets named. (untested on ivory)
  Why: a clock error can pass every still. Met when: render-pixel events match word times. No such check yet means UNVERIFIED.

## Defects versus taste
- **A defect is provable from evidence. Everything else is taste.** (untested on ivory)
  Why: defects are finite, and taste never converges. Met when: every defect names a frame or timestamp, expected and actual.
- **Claude finds the defects. Chase's pass is taste. He has final say on which is which.** [Ours] (untested on ivory)
  Why: each defect he spots costs him a watch and a message. Met when: each defect note he gives adds a check or a named gap.
- **Measurable defects get checks, not more written rules.** [Ours] (untested on ivory)
  Why: a written rule does not stop a defect. Met when: each new check shows red on an old render before it is trusted.
Only these are defects:
- A broken non-negotiable, or anything under "Chase's rules and rejections" in a template's ledger, shown by a frame or a count.
- Copy: a typo, clipped text, wording that differs from the plan, or content outside its card.
- Caption: a wrong, dropped or uncaptioned word. Timing: a graphic off its word, or a readable graphic held too short to read.
- Render: a one-frame flash, black frame, frozen video, double cut, or a state snapping back at a clip join.
- Depiction: a visual that does not show its line, a half-loaded screen, or an annotation off target. Story order: a payoff before its proof.
- Coverage: a request line or template requirement with no evidence.

## Review contract
Runs before Chase sees anything: checks first, then one round, defects only. A declared lock attempt also shows him the untouched first render. [Ours]
- **Required checks end PASS, FAIL or UNVERIFIED. Missing evidence is never green. FAIL blocks handoff.** [Ours]
  A deviation is a logged waiver, never a sentence in a report. Lock runs allow none. (untested on ivory)
  Why: green checks can give false confidence. Met when: each result is tied to its inputs and the exact file.
  - Black frames, audio stream, loudness: `tools/gates.py`. Read its findings, not its verdict.
    `black`, `audio`, `loudness` and `true-peak` count. `frozen-band`, `hold`, `freeze` and `layout-run` only warn, and need a 1080x1920 file.
  - Kept words: `rawcut.py verify`, read as `story.md` says. Picture structure and the full_face setting: `tools/motionlint.py <index.html> --pack editorial`.
  - Flash scan: `tools/flash_scan.py`, with every planned switch and card swap as expected cuts.
  - After picture approval, sound placement, palette, rotation, source-file share, event coverage, CTA/proof spans and revision: `python tools/sound_mix.py check-sheet <project>`.
  - Separate cue/voice stems: `python tools/sound_mix.py check-mix <project>`; 18-26 LU under speech is required, density over 8 per 30 s only warns ("just has to make sense"). Zero cues passes.
  - Delivered sound and duration: `python tools/sound_mix.py check-media out/<base>.mp4`, bound by `out/<base>-delivery.json`. `deliver.py` runs all three for finals and preserves the unchanged `finish.py` mastering step.
  - Final-audio re-transcribe, caption checks: UNVERIFIED until built, so step every cut frame by eye. How it sounds: UNVERIFIED until Chase listens.
- **One discovery round, never a second. Re-checking a repair is not a round.** Unfixed findings go open in the handoff. (untested on ivory)
  Why: a repeat round oscillates. Chase's taste rounds are a separate loop and stay unlimited. Met when: the run logs one round.
- **Fresh eyes: two reviewers on contact sheets. One Claude, and one Sol through `codex exec` when Codex is installed, otherwise a second Claude with a different reading order.** [Ours] (untested on ivory)
  Sol, prompt on stdin: `codex exec -m gpt-6.1-sol --sandbox read-only --skip-git-repo-check -i <sheet> -`. Fallback model: gpt-5.6-sol.
  `finish.py`'s sheet stops at 48 s, so cut extra sheets past that. Sheets cover composition and copy, never audio. Step cuts and motion on the render.
  Why: the builder grading its own work ships flaws. Met when: each reviewer signs off only what it saw, and an unseen stretch reports UNVERIFIED.
- **A finding carries evidence, and one cheap skeptic tries to refute it. What a check proved is off limits.** (untested on ivory)
  A frame showing the check wrong becomes a check bug. [Ours] Why: an imagined defect burns a render. Met when: each kept finding has item, frame, expected, actual.
- **Banned findings, discarded unjudged:** redesigns, "this could be better", another template, different copy phrasing, motion-feel opinions,
  more or fewer graphics unless a required item is missing, and any redesign of the template's own spec. (untested on ivory)
  A spec conflict is not banned: two lines that cannot both hold, or a rule breaking a [Chase] rule, goes out with the exact lines. [Ours]

## Chase's notes
- **Log each note in `notes.jsonl` with class, scope, word ID and revision. It re-runs its stage and whatever depends on that stage.** [Ours]
  Why: seconds shift after a fix, and revision is where the cost sits. Met when: a graphic note re-renders one graphic, and nothing stale ships.
- **"Slightly" is one notch, about 15 to 20%, on placement or size. "Go back" means the approved version exactly.** (untested on ivory)
  Why: a placement note is never a redesign. Met when: a revert is proven identical. A note covers what he named, nothing more. [Ours]
- **After approve, build the final fresh at publish spec and re-check that file.** Unlocked templates get one new CapCut draft. [Ours]
  Same cut, audio and plan as approved. A material change goes back to him. Never quit CapCut or restore over his hand edits. [Ours] (untested on ivory)
  Why: an approval names one exact file. Met when: his diff returns as hand notes plus opened, reviewed and finished status.

## Handoff report
Short enough to read before watching. Claim only evidence gathered: what changed and the file, each required check as PASS, FAIL or UNVERIFIED for this exact file, and what is still open (unfixed findings, waivers, placeholders, anything a take created). [Ours] Why: he must see what is proven.

## What becomes a rule, and locks
- **Only Chase's yes writes a rule, with his note attached.** Hand edits outrank approvals, which outrank Claude's calls. [Ours] (untested on ivory)
  Why: the final state wins, and an early choice he corrected is an anti-pattern. Met when: each new rule cites its note.
- **Never a rule:** per-shoot measurements (face, seam, framing, fills), brands, keywords, delivery names, a device seen once. (untested on ivory)
  Why: counts, timestamps and shares are outcomes, never targets. Met when: each job re-measures its own shoot.
- **A lock names one exact template and spine version, frozen before raw 1, over three new raws in a stated scope.** [Chase] [Ours]
  Why: it is scoped evidence, not a promise. Met when: `LOCK.md` records raws, versions, date and scope.
- **On a declared lock attempt, a raw counts only on its untouched first render. Repairs wait for his verdict.** [Ours]
  An adopted output change restarts at zero. Per-raw content, measurements and assets are not output changes. [Ours]
  Met when: required checks are green with no waiver or UNVERIFIED, zero cut and defect notes, publishable yes, hand status closed.

## Trial ideas, off until Chase says yes
- A handoff part listing what no reviewer was shown, opening with "Nobody listened to the audio". (untested on ivory)
- Reading means show the source, explaining means show him. Matching words stands in for his gaze. (untested on ivory)
- A highlight wipe timed to reading, proven first on a real capture. (untested on ivory)
- A short black title box at the top of the upper panel, captions staying on the seam. Copy the form only. (untested on ivory)

## Open decisions: Chase owns each one, so keep current behaviour and flag it
- Loudness target. Caption chunk length. Tail padding. Hook line moves. Whether isometric scenes stay.
- Real captures versus rebuilt cards as ivory's default. Current rule stands: rebuilt vector UI cards, real artifacts, verified numbers only.
- Also unanswered: the one-minute cut listen. Safe-zone top: ivory's y 120 sits inside the y 200 band, and STYLE.md stands until he rules.
- A spoken, unverified figure on a graphic. Review at preview size or on the publish grid. "Never re-cut from raw". Each file's own flags.
