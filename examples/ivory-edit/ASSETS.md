# Asset inventory for 1030-2 (paths relative to each style project: assets/...; sources in work/1030-2/shared)

Face cam + audio: `assets/face_half.mp4` 1280x1092 30fps (bottom split panel, cover-fit), `assets/face_wide.mp4` 1920x1080 30fps, `assets/voice.m4a` (the only voice track; videos are muted). Duration 57.65 s. `assets/face_full.mp4` exists but this run has allow_full_face false (source: template): do not use it.

Boxes below are CSS px relative to the plate's top-left. Multiply by the DPR given for image px. Every plate has a `.json` beside it. Layout of the read-size notes: 900 px is the widest a plate gets inside a white card on the 1080 frame.

## Rules that travel with these files
- Verified scope. `pricing-plans-*` and `pricing-compare-*` show "No 5-hour limit‡" with the ‡ note out of frame. Any beat showing that line also shows `pricing-footnote-*`, or carries the word verified in our own type (facts: five_hour_removed, pricing_footnote, flag_verified_scope). The mark on the page is a double dagger.
- His words stay exact. "no more five-hour limits" (15.0-17.6, 27.3-28.8) and "no more five-hour plans" (53.5-54.7) are flagged in facts.json, never corrected. Any graphic of ours says verified and limit.
- Sued line (44.3-49.5) is his hedged opinion. No lawsuit figure, case number, date or plate. Nothing in this inventory supports it, and no asset here belongs on those words as proof.
- 4x is only the figure he says people assumed. No plate shows it as a usage figure.
- Only numbers in facts.json go on screen. Left out for that reason: X post stats (views, likes, replies), the API credit lines, and Pro's "$200 billed up front". All of those remain in the raw captures under `work/1030-2/shots_full/`, which are not build assets. Do not pull from there.
- Codex: `codex-pricing-*` proves Pro only. His line names no plan, so show the whole sentence with "Pro plans" in it (facts: codex_pro_no_five_hour, unverifiable).
- Light plates read on the ivory card. Dark is on file where the site has one.

## Posts: rebuilt cards (tools/post_card.py via work/1030-2/post_build.py), DPR 2
Read in the signed-in in-app browser on 2026-11-01, navigation only, text taken from the post element only. Nothing of Chase's account is in these files. Specs: `work/1030-2/post_specs/`. No stats on any card. Dates are as the browser showed them (UTC-5): 12:29 PM is 17:29 UTC.

Source https://x.com/claudeai/status/2116220869479428500
- `assets/posts/claude-post-light.png`, `claude-post-dark.png` 1200x1574. Full post with the hero image. Text reads about 25 px at 900 wide, so use it whole or zoom, not for reading the paragraph.
  Boxes (CSS): header 16,16 568x44. "Max 5x → Max" 16,119 109x22. "Max 20x → Ultra" 16,142 123x22. Prices line 16,189 344x22. "We're also removing the 5-hour limit for verified Ultra accounts" 16,260 473x22. Newer accounts sentence 16,283 537x45. "Weekly limits remain unchanged." 16,377 247x22. Hero image 17,413 566x318.
- `assets/posts/claude-post-tight-light.png`, `claude-post-tight-dark.png` 920x1002. Same text, no image, narrow wrap, so it reads about 33 px at 900 wide. Taller than the 760 px panel: push to a box, do not fit it whole.
  Boxes (CSS): "Max 5x → Max" 16,119 109x22. "Max 20x → Ultra" 16,142 123x22. Prices 16,189 344x22. "We're also removing ... verified Ultra accounts" 16,260 402x45. Newer accounts 16,307 388x45. "Weekly limits remain unchanged." 16,400 247x22.

Source https://x.com/mboverell/status/2116221457252659275 (Mike Overell, leads product for Claude subscriptions)
It is a quote post of @claudeai. The rebuilt card leaves the quoted post and its image out.
- `assets/posts/overell-post-light.png`, `overell-post-dark.png` 1200x1096.
  Boxes (CSS): "it had a single limit: 5 hours." 364,142 210x22. "It gave you 20x Pro's limit, so we called it Max 20x." 16,166 378x22. "we set them to 10x Pro's (the 5-hour limit stayed at 20x)." 152,189 423x22 (wraps, last word on the next line, use y 189-234). "I get that some new users assumed 20x applied to both limits." 16,236 463x22. "The Ultra plan keeps the weekly limit (10x Pro)" 16,307 346x22. Temporary limit sentence 16,353 560x45.
- `assets/posts/overell-post-tight-light.png`, `overell-post-tight-dark.png` 920x1238. Reads about 33 px at 900 wide. Best for 37.9-42.6.
  Boxes (CSS): single limit 16,142 404x45. "It gave you 20x Pro's limit..." 16,166 398x45. "we set them to 10x Pro's (the 5-hour limit stayed at 20x)." 16,213 418x45 and one more line to y 260. "I get that some new users assumed..." 16,283 415x45. "The Ultra plan keeps the weekly limit (10x Pro)" 16,353 346x22. Temporary limit 16,447 369x45.

Post art, source https://pbs.twimg.com/media/HV5MwwNWAAA5hUI.jpg?name=orig
- `assets/posts/post-hero-image.jpg` 3840x2160. Clean original of the Free, Pro, Max, Ultra art on its green field. Names only, no numbers.
- `assets/posts/post-hero-cards.png` 3080x1250. Tight crop of the same art with a thin green margin. Use this one inside the white ivory card, never the green as a full panel.
  Image px: Free 50,215 to 590,1005. Pro 585,160 to 1200,1060. Max 1198,103 to 1890,1115. Ultra 1888,47 to 3030,1175. The cards overlap.

## Screenshots (headless, no sign-in, nothing clicked, checked 2026-11-01)
Source https://claude.com/pricing
- `assets/shots/pricing-plans-light.png`, `pricing-plans-dark.png` 2688x2108, DPR 4, CSS 672x527. Max and Ultra cards only, desktop layout. The cards run off the bottom edge, cut in the gutter above the Fable and API credit rows. Whole width is 21 px body text at 900 wide, so zoom one card (2.9x, about 46 px) for reading.
  Boxes (CSS): Max card x 13-322. Ultra card x 346-655. "Max" 45,143 69x25. "Ultra" 379,143 77x25. "Claude Code included" tags 126,146 140x22 and 468,146 140x22. "$100" 45,229 51x20. "$200" 379,229 56x20. "5x Pro usage every 5 hours and every week*" 77,475 189x39. "No 5-hour limit‡" 411,474 112x17. "10x Pro usage every week*" 411,508 189x15.
- `assets/shots/pricing-compare-light.png`, `pricing-compare-dark.png` 1224x796, DPR 3, CSS 408x265. Phone layout of the compare table: sticky plan names over the two limit rows. Best proof of "only double the 5X plan". Reads 31-40 px at 900 wide.
  Boxes (CSS, dark's week row sits 1 px lower): plan names row y 12-27 with Max x 239-271, Ultra x 339-375. "Limit every 5 hours" 17,63 133x15. Max 5x pill 239,119 32x22. Ultra No 5-hour limit‡ pill 322,107 69x46. "Limit every week" 17,185 136x14. Max 5x pill 239,229 32x22. Ultra 10x pill 338,229 37x22.
- `assets/shots/pricing-footnote-light.png`, `pricing-footnote-dark.png` 1176x108, DPR 4, CSS 294x27. "‡No 5-hour limit for verified accounts." Whole line, nothing else. "verified accounts" 152,10 123x13.

Source https://support.claude.com/en/articles/17728952-what-is-the-ultra-plan (page shows only "Updated this week"). The help site has no dark mode, so these are light only.
- `assets/shots/ultra-support.png` 1392x540, DPR 3, CSS 464x180. "What changed from Max 20x?" section, phone width. Reads about 31 px at 900 wide.
  Boxes (CSS): heading 8,16 318x22. "The Max 20x plan is now called the Ultra plan. Existing Max 20x subscribers move to Ultra automatically, with no price change." 8,57 441x38. "Ultra includes 10 times ... no five-hour limit, for verified accounts." 9,127 440x37, verified line 9,150 274x14.
- `assets/shots/ultra-verified.png` 1392x957, DPR 3, CSS 464x319. "What is a verified Ultra account?" section.
  Boxes (CSS): heading 8,16 338x17. Paragraph 1 8,57 433x59. Paragraph 2 (temporary limit, phone step) 8,150 442x85. Paragraph 3 (Settings > Usage) 9,266 414x39.

Source https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-max-or-ultra-plan
- `assets/shots/claude-code-support.png` 1392x819, DPR 3, CSS 464x273. First two paragraphs of "What happens when you hit usage limits". Fits the close about Claude Code pricing. Light only.
  Boxes (CSS): heading 8,16 427x22. "Pro and Max plans have a five-hour session limit ... verified Ultra accounts don't have a five-hour session limit." 9,58 428x58. "These limits are shared across Claude and Claude Code" 8,174 392x37.

Source https://learn.chatgpt.com/docs/pricing (redirect from https://developers.openai.com/codex/pricing)
- `assets/shots/codex-pricing-light.png`, `codex-pricing-dark.png` 812x360, DPR 2, CSS 406x180. The whole paragraph, phone width, element capture. No side padding, so the card supplies it. Reads about 35 px at 900 wide.
  Boxes (CSS): "Pro plans" 276,32 69x14, then "currently have no five-hour limit." 0,58 229x14. Highlight both parts or neither, so the Pro scope stays. "local messages per five-hour period for Plus and Standard Business" 0,6 397x40.

## Clips: Chase's own screen recording (his, from raw/cut.mp4; muted, 30 fps, keyframe every 15 frames)
Cut by `work/1030-2/clips_cut.py`. Each range was checked against raw/cuts.json: none spans a join (35.32, 36.62, 39.95, 44.18, 52.38). Crops stay inside the post column and above the seam (y 1916), so the X sidebars, trending list and his face are not in the files. Dark mode X, so these sit on black inside the card.

960x460, 1:1 source pixels, text about 46 px. Rows: header 39,20 378x109. "We're renaming our Max plans:" 40,185 643x45. "Max 5x → Max" 43,317 307x34. "Max 20x → Ultra" 43,380 350x36.
- `assets/clips/title-highlight.mp4` 2.20 s, cut 5.30-7.50. Title line goes blue at 0.95-1.70 local, on "renamed both of their plans".
- `assets/clips/ultra-highlight.mp4` 2.40 s, cut 14.90-17.30. "Ultr" of Ultra goes blue at 0.60-2.10 local. His selection stops short of the last letter.
- `assets/clips/max20x-highlight.mp4` 2.00 s, cut 31.00-33.00. "Max 20x" goes blue at 0.25-1.75 local.
- `assets/clips/drag-select-max5x.mp4` 2.07 s, cut 33.20-35.28. Drag starts at 1.05 local and has "Max 5x" selected by the end. It stops at the 35.32 join, so it is an excerpt of a longer drag.
- `assets/clips/rename-line-highlight.mp4` 2.67 s, cut 44.30-46.95. "Max 20x → Ultra" fills blue at 0.70-2.45 local. Real time here is his "name change" line, which sits beside the sued line. Use it for the rename only.

960x712, scaled 0.59 from source, text about 27 px, under the 31 px floor. Use for atmosphere or the whole-post view, and the rebuilt tight card for reading.
- `assets/clips/five-hour-cursor.mp4` 2.60 s, cut 26.40-29.00. Whole post text, cursor resting on "5-hour limit", verified on the same line. Almost static.
  Rows: "We're also removing the 5-hour limit for verified Ultra accounts, starting" 24,425 896x35. Whole paragraph y 425-576. "Weekly limits remain unchanged." 26,626 672x27.

Left out on purpose: the selected prices and verified paragraphs at 48.75-52.38. It sits under the sued and 4x lines, and the selected text backs neither.

## Logos (simple-icons SVG, single-colour paths; set fill via CSS or inline)
- `assets/logos/claude.svg`, `assets/logos/anthropic.svg` (copied from 1022-2)
- `assets/logos/claudecode.svg`, `assets/logos/x.svg` (simple-icons)
- No OpenAI or Codex mark exists in this simple-icons install (`openaigym` is a different mark, so it was not used). Set Codex in type.

## SFX (49 .wav, ivory library, `assets/sfx/<name>.wav`)
bell, bubble, camera-focus, camera-rec, camera-snap, camera, click-b, click, clock, deep-hit-2, deep-hit-3, deep-hit, film-burn, heartbeat, heavenly-choir, highlighter, impact, lighter, marker, metal-pop, paper-fast, paper-slow, phone-ring, pop-2, pop-hero, pop-soft, pop, sheet-slide, shutter, snip, sub-drop, switch, tap, typing-b, typing-c, typing-d, typing, ui-tick-a, ui-tick-b, ui-tick-c, whoosh-a, whoosh-b, whoosh-c, whoosh-d

## Fonts (woff2)
`assets/fonts/instrument-serif-latin-400-italic.woff2`, `instrument-serif-latin-400-normal.woff2`, `inter-latin-400-normal.woff2`, `inter-latin-500-normal.woff2`, `inter-latin-600-normal.woff2`, `inter-latin-700-normal.woff2`, `inter-tight-latin-500-normal.woff2`, `inter-tight-latin-600-italic.woff2`, `inter-tight-latin-600-normal.woff2`, `inter-tight-latin-700-italic.woff2`, `inter-tight-latin-700-normal.woff2`, `inter-tight-latin-800-italic.woff2`, `inter-tight-latin-800-normal.woff2`, `inter-tight-latin-900-italic.woff2`, `inter-tight-latin-900-normal.woff2`, `jetbrains-mono-latin-400-normal.woff2`, `jetbrains-mono-latin-500-normal.woff2`, `jetbrains-mono-latin-700-normal.woff2`, `newsreader-latin-400-italic.woff2`, `newsreader-latin-400-normal.woff2`, `newsreader-latin-500-italic.woff2`, `newsreader-latin-500-normal.woff2`, `space-grotesk-latin-500-normal.woff2`, `space-grotesk-latin-700-normal.woff2`

## Vendor
- `assets/vendor/gsap.min.js` (GSAP 3.13, load with <script src>; no CDN)

## How to remake these
`work/1030-2/shots.spec.json` with `tools/capture_shots.py` (raw output in `shots_full/capture_shots/`), then `shots_extra.py`, `shots_crop.py`, `post_build.py`, `clips_cut.py` in `work/1030-2/`.
