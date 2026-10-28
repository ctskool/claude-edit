---
name: claude-edit-versus
description: Shortcut for /claude-edit that makes only the "versus" (Raw vs Claude) short. From one 16:9 take in which you ask for edits out loud ("give me captions", "make it warmer", "pull the camera closer", "bring in some music"), it stacks two panels in 9:16 - the edited take on top with each edit landing on the word that names it, the raw take (dead space cut only) below - with an edit log, sound on change and a synth music bed.
argument-hint: <16:9 take (.mkv/.mp4/.mov)> [more takes of the same short]
disable-model-invocation: true
---

# /claude-edit-versus (Raw vs Claude)

Read `.claude/skills/claude-edit/SKILL.md` (in this repo) for the shared rules (first run, intake, step 0b), then run
this for: $ARGUMENTS

## What the take should be
One continuous 16:9 talking-head take (camera only, no screen recording), ~30-60 s. The speaker introduces the idea
("these two videos are exactly the same, except one was edited by Claude"), then asks for edits one by one, out loud,
and ends with a line that lands it. Edits work best in this order (each builds on the last): captions -> key words ->
colour -> a title behind the head -> an edit log panel -> sound on change -> camera punch in / out -> music -> music
quieter -> background blur -> a new caption font. Anything else they ask for becomes a `custom` edit.

## Steps
1. **Tight cut** (main skill step 0b) -> `work/<id>/raw/cut.mp4` + `raw/cut_words.json`. Dead space only: drop failed
   takes and false starts, never the edit requests.
2. **Prep**: `python tools/versus.py prep <id>` -> `work/<id>/versus/`: `assets/cam_1080.mp4` (top), `assets/cam_raw.mp4`
   (bottom, same frames), `voice.m4a`, `words.json` + `words.txt` (cut clock), the cut-out `assets/cam_fg.webm`
   (needed for title_behind and bg_blur; NVIDIA ~40 s, Apple Silicon a few minutes, CPU much longer - say so), and a
   draft `edits.json` with auto-chunked captions.
3. **Find every spoken edit instruction** in `versus/words.txt` and write `versus/edits.json` (schema in the docstring
   of `tools/versus.py`):
   - one entry per instruction: `{op, t, word, label, ...params}`. `t` = the START of the word that names the effect
     ("captions", "pop", "warmer", "title", "panel", "sound", "closer", "originally", "music", "quieter", "softening",
     "font") and `word` = its index in words.txt - the edit lands as that word is said. `label` = the row in the edit
     log (short: "Warm grade", "Punch in"); `updates: "<op>"` rewrites an earlier row instead ("Punch in -> out",
     "Music, quieter").
   - op library: `captions`, `keywords`, `caption_font {font: serif|mono|grotesk}`, `grade {look: warm|cool|bw|punchy}`,
     `title_behind {words: [[w, t], ...] as spoken, italic_from, out}`, `edit_log {show?, out?}` (backfills what was done
     before it appears), `sfx_on_change` (one cue per edit from then on), `punch_in {scale ~1.3-1.4}`, `punch_out`,
     `music_in`, `music_level {db, e.g. -5}`, `bg_blur {px ~9}`, `text_pop {text, out}`, `lower_third {name, role, out}`,
     `custom {js}` (GSAP for anything else: `tl`, `$`, `el`, `E`, `t` are in scope; keep it seek-safe: tl.to / fromTo
     / set at absolute times only).
   - `header`: two lines of words with the time each is said (line 1 short and plain, line 2 italic clay, e.g. "Same
     take, twice." / "One edited by Claude."); `labels.pulse` = when "Claude" is said in the intro.
   - `captions`: keep the auto chunks unless a chunk splits a phrase badly; add key words as `[index in chunk, time]`
     (the words that carry the line; only shown after the `keywords` edit). Captions appear from the `captions` edit.
   - `end_card.t` = where the closing line starts. Ask the user before inventing anything they did not say.
4. `python tools/versus.py music <id>` (if there is a `music_in`) -> numpy synth bed (no samples, nothing to license),
   level drops baked in at each `music_level`. `--bpm` / `--seed` change the feel.
5. `python tools/versus.py build <id>` -> validates edits.json (unknown ops, times off their word, edits that need the
   cut-out) and writes `versus/index.html` + `edits.js`; fix every error and re-run until lint is clean.
6. Check frames before rendering: `cd work/<id>/versus && npx hyperframes snapshot --at <each edit t + 0.5> --describe false -o snaps`
   and Read them (caption not over the mouth, title behind the head, log readable, nothing clipped).
7. `python tools/versus.py render <id> --draft`, then `python tools/versus.py render <id>` -> `out/<id>_versus.mp4`
   (+ `-sheet.jpg`, gates). ~2 min for 48 s on an RTX 5090.

## Layout (short-form safe)
1080x1920: header at y 140 / 224 (below the app's top tabs), label + top panel y 316-925, label + bottom panel
y 939-1548, end strip at y 1572, nothing important below ~1550 (caption + buttons zone). Panels are 16:9 at 1000x563.

- Looks like: two copies of the same take stacked; the top one changes on every word you name, the bottom stays raw.
- Use it when: showing what Claude can edit, live; a hook / demo post.
- Known issues: edits that need the cut-out (title behind the head, background blur) are slow without a GPU.
- Gallery: `docs/index.html` (published as the repo's GitHub Pages site).
