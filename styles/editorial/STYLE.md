# Style: EDITORIAL ("Claude Editorial")

Recreation of the look used by reference creator A and reference creator B (Oct 2026) - almost certainly Claude Motion /
Claude-authored HTML in Anthropic's own design language: warm ivory canvas, Claude clay accent, elegant serif
headlines with one italic clay word, crisp white UI cards rebuilt (not screenshots) that animate like a product
demo, monospace labels, and a persistent progress HUD that tracks the argument. Captions are monospace uppercase
chips sitting exactly on the seam.

## Measured numbers
REFERENCE-ANALYSIS.md (this folder) and ../CALIBRATION.md hold the measured donor numbers; where they differ from prose below, the measured numbers win.

## Reference frames (READ THESE IMAGES before designing)
- `reference\full\josh_b.png` skill card + command input + 5-step progress + caption chip
- `...\full\josh_machine.png`, `josh_d.png` interactive diagram with sliders; "50+ psychology principles" chip grid
- `...\full\josh_takeover.png` full-graphic takeover (face hidden)
- `...\full\mich_a.png`, `mich_b.png` serif title with italic clay word; the "CLAUDE CODE 0/4" power-strip HUD; Supabase tool card
- `...\full\mich_terminal.png` dark terminal panel with build->deploy->live pipeline; `mich_cubes.png` 3D clay cubes takeover
- `...\full\mich_icons.png`, `mich_fullface_title.png` icon rows; full-face with big serif title over the head
- `...\full\josh_intro_dark.png`, `josh_dark_hero.png` dark variant (near-black + clay/gold) used for the hook
- Contact sheets: `reference\sheets\ref-A*_1fps.jpg` (reference A), `ref-B*_1fps.jpg` (reference B)

## Canvas and layout (1080x1920)
- Top graphic panel y 0-960, ivory #EEEEE7; optional faint grid (40px cells, 1px lines rgba(0,0,0,.035)).
- Face cam `assets/face_half.mp4` (1280x967) in y 960-1920, object-fit cover, HARD edge (no fade, no border).
- Caption chip centred ON the seam (vertical centre y 960).
- Graphic safe area: y 120-880, x 60-1020. Main content centred around y 470.
- Layout mix (MEASURED, REFERENCE-ANALYSIS.md): reference A 62% split / 34% full-graphic / 3% full-face (5-9 takeovers
  per minute, median 3.1 s, max 7 s, ~6.6 layout switches per 30 s); reference B 85 / 10.5 / 4 (1-2 takeovers of 2.4-4.7 s).
  Default for this pack: see "house rules" below - they OVERRIDE these donor numbers (content-driven switching,
  more than reference B). Optional dark hook (#141413) for the first 2-3 s. Hard cuts.
- Pace: visible change every 0.7-1.0 s median (p90 1.3-2.2 s); beats over 1.5 s are never static (typing, progress
  bars, rotation keep moving). Static band <= 8 s per 30 s, longest hold <= 2.5 s (styles/CALIBRATION.md).

## house rules (2026-10-23) - THESE WIN over every donor number in this file
Editorial (menu name ivory) is the lead style. The author's notes on the first finals, codified:

1. **Layout rhythm: switch on what is being said, not on a quota.** More switching than reference B, but every switch
   must be earned by the line. Read each beat's `layout_hint` in beats.json (set by the planner from the content):
   - **full-face** (plain `assets/face_full.mp4` punch-in, 1-2.5 s, serif title or chip on the shirt): the speaker's opinion or
     emphasis ("honestly", "definitely", "this is the one"), direct address to the viewer, a rhetorical question, the
     payoff line, the CTA - and any visible jump cut in his footage (it hides it).
   - **full-graphic takeover** (face hidden, 2-4 s): the visual IS the point and needs the whole frame - a name reveal,
     A vs B, a list of 3+, a big number / stat, a before-after, a demo clip.
   - **split** (default): he explains or points at the thing on screen ("this", "here", "it lets you..."), setup lines,
     connective tissue between moments.
   - Spacing: cut as a hard cut on the stressed word or a sentence boundary; no two switches within ~1.2 s; vary the
     order (never mechanically S-G-S-G). Soft guardrail: if one layout holds past ~8 s, look for a line that earns a
     break (a reveal, a list item, an opinion) - don't invent one.
   - The switch count just falls out of the script. For reference only: reference A ~9 switches / 30 s, reference B ~2.3, our
     first finals 3.6-3.75 with a 27 s opening split (the author: too static). `tools/gates.py --pack editorial` reports the
     count and warns only on a layout run over 8 s.
2. **Sound design: vary it - every sound marks an event, and it rotates.** One cue per meaningful event, chosen from
   that event's class and rotated, so the same sound never plays twice in a row and no single sound carries the mix.
   (The first finals used click-soft + pop for 63% of 27 cues - "a little repetitive".) Library: `shared/sfx/` (chime,
   click, click-soft, error, glitch-1..3, impact-bass-1/2, key-press, notification, ping, pop, riser, sparkle, typing,
   whoosh, whoosh-cinematic, whoosh-short) + `.claude/skills/media-use/audio/assets/sfx/`. Event classes:
   - layout switch / takeover in: whoosh-short, whoosh, whoosh-cinematic (the soft one at 0.2-0.25)
   - card / chip / slot pop: pop, sparkle, notification
   - check, tick, HUD fill: click-soft, click, ping
   - typing / editor: typing, key-press
   - stat lands / verdict / reveal: chime, ping, impact-bass-1 (low, 0.2)
   - into a full-face punch-in: short riser (0.15-0.2) or impact-bass-2; nothing on the CTA hold
   Silence is fine where nothing happens; never mask a stressed word; at most ~1 cue per 1.2 s.
   `tools/motionlint.py --pack editorial` warns on back-to-back repeats and on one file carrying > 25% of the cues.
3. **Keep:** the ivory canvas, serif headline with the italic clay word, rebuilt vector UI cards, mono chips on the seam,
   the HUD continuity device, real artifacts (never fake "test" slides), split face cam (no cut-out), verified numbers only.

## Palette
- Ivory #EEEEE7 (panel), card white #FFFFFF, card border #E4E2DA, hairline #D9D6CC.
- Ink #1F1E1D, secondary #5E5D59, muted label #8A887F.
- Clay accent #D97757 (fills, italic words, active states); clay deep #C15F3C (pressed); clay tint #F6E3DA.
- Dark panel / terminal #1F1E1C, terminal text #EDEBE4, terminal muted #8E8B82.
- Success green #2E9E5B (checks), only for check marks.

## Typography (local files in assets/fonts, declare @font-face for each)
- Display serif: Newsreader 400/500 (+ 400/500 italic). Headlines 120-150px, letter-spacing -0.02em, ink;
  ONE italic word in clay ("*Vibe* coding", "*19* agenti"). Sub-line: Inter 500 30px #5E5D59.
- UI sans: Inter 500/600/700, 26-40px.
- Mono: JetBrains Mono 400/500/700 for labels ("SKILL 1 OF 5" 22px, tracking .14em, #8A887F), code and commands.
- Caption chip (MEASURED): JetBrains Mono 500 UPPERCASE, tracking .04em, text #F5F4EE on #1B1D1D, radius 10px.
  reference A variant: ~57 px text, chip ~110 px tall, NO accent colour, 2-3 words (48% / 45%).
  reference B variant: ~46 px text, chip ~80 px tall, accent clay #E0907E on ~8% of chunks, mostly 3 words (75%).
  Default for this pack: ~52 px text, ~96 px chip, accent on <= 10% of chunks, 2-3 words. HARD SWAP (no animation),
  chunk median 0.7 s, shown 2 frames before its first word. Chip centred on the seam (y 960) in split; on
  full-graphic takeovers the caption drops to y ~1480-1570.

## Components (build as reusable JS helpers)
1. **Card**: white, radius 22px, 1px #E4E2DA border, shadow 0 12px 32px rgba(40,30,20,.07). Title rows in Inter 600.
2. **Icon tile**: 104px clay square radius 24px with a white line icon (inline SVG, 2.5px strokes).
3. **Command input**: dark rounded bar (#1F1E1C, radius 14px) with clay ">" prompt + JetBrains Mono typing
   (~22 chars/s, caret blink via deterministic tween) - josh_b.png.
4. **Step progress**: N circles (44px) joined by a line; active = clay fill + white number; done = clay outline.
5. **HUD** (persistent through the video, top of panel): for this video a "feature strip": mono label
   "HUASHU-MOTION" + counter "0/4" + 4 slots (rounded squares) that fill with icons as features are named:
   code (27.7s), transitions (29.1s), music (30.3s), editor (32.8s). Mirrors reference B's "CLAUDE CODE 0/4" power strip
   (mich_b.png). Show it from the moment huashu is introduced; slots pop in with back.out(2) + soft click.
6. **Terminal panel**: #1F1E1C, radius 18px, window dots, mono 30px; pipeline pills (build -> deploy -> live) with
   green check dots (mich_terminal.png).
7. **Chip grid**: rounded pills (white, 1px border, Inter 600 26px), active ones clay outline + clay text (josh_d.png).
8. **3D clay cube** with the Claude spark (CSS 3D: preserve-3d, 3 visible faces in clay shades #D97757/#C15F3C/#E9906F,
   white spark logo from `assets/logos/claude.svg` on the front face), used for a takeover (mich_cubes.png).
9. **Strike / X**: thin clay 6px line drawn across (scaleX 0->1, 0.3s) for "not Kling / not Seedance".
10. **Connector lines**: SVG paths drawn with stroke-dashoffset (cables from HUD slots, tool -> database etc.).
11. **Scene** (beats with `visual.type == "scene"`, see `styles/VISUAL_MENU.md`): the generated illustration
    (`shared/scenes/<beat>.png`, copy to `assets/scenes/`) as an <img> with a radial edge mask (`closest-side, #000 72%,
    transparent`) so it melts into the ivory grid - no card, no border. Split: ~620 px centred in the top half (y 64-684),
    the scene's real overlay (a crop of the real post line / page) as a dark or white pill under it, a mono source line
    under that, all clear of the HUD strip (y >= ~780). Full graphic: ~980 px at y ~270 under the serif title, real
    labels (logo tile + name + clay value, count-up) pinned to the subjects they name, a source line under the board.
    Motion: the scene enters with the card settle (y +40, scale .95 -> 1, 0.45-0.5 s power3.out) as the previous card lifts
    out, then a slow push-in (scale 1 -> 1.06-1.07 over the beat, ease none) plus one directional drift where the metaphor
    moves (racers slide toward the line); a soft light / glow element can swell on the stressed word. Overlays land on
    their words (pop / stepper). Proven on work/1023-test/v2/editorial (b03 crate, b10 race, 2026-10-25).
    Scene look for this style: isometric 3D miniature, matte clay, ivory ground #EEEEE7, clay #C96442 accents, charcoal
    #1F1E1D details, soft daylight top-left, one centred subject, no text / logos / people.

## Motion vocabulary
- Calm and precise. Arrivals: y +24 -> 0, opacity 0->1, 0.55s power3.out, staggers 70ms.
- Typing, checking, filling and drawing are the main "action" - something in the panel progresses every ~1s.
- Scene change: previous elements fade/drift up (y -16, opacity 0, 0.25s), next arrive; or a card morphs into the
  HUD slot (scale + move) - this "continuity" is the signature of the style.
- Checks: back.out(2) scale 0->1, 0.35s. Numbers count up with snap to integers.
- No blur-heavy effects, no glow, no shake, no whip pans.

## Sound
Light, but never repetitive (see house rule 2). Volumes 0.2-0.35 under the voice; typing beds at 0.2-0.25.

## Banned
Browser-window screenshot cards as the main device (that's the reference C style - small real logos/plates are OK inside
cards), neon, glow, glassmorphism, gradients other than flat, kinetic word slams, emoji, captions in sentence case.
