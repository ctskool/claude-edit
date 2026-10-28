# Asset inventory for 1022-2 (paths relative to each style project: assets/...)

Face cam + audio: `assets/face_half.mp4` 1280x967 30fps (bottom split panel, cover-fit), `assets/face_full.mp4` 1080x1920 30fps (full-frame punch-ins; set data-media-start = data-start so it stays in sync), `assets/voice.m4a` (the only voice track; videos are muted). Duration 48.05s.

## Screenshots (DPR 2: the matching .json boxes are CSS px -> multiply by 2 for image px)
- `assets/shots/claude-motion-article-top.png` 2560x2000 (crop of the top; boxes json = claude-motion-article.json)  source: https://claude.com/resources/articles/dashboards-and-motion
- `assets/shots/claude-pricing-individual.png` 2880x1800 (Free/Pro/Max plan cards, Individual tab; a 'Latest news' popup overlaps the Max card)
- `assets/shots/claude-pricing-team.png` 2880x2000 (Team & Enterprise tab: Team card + Enterprise card)  source: https://claude.com/pricing
- `assets/shots/huashu-readme-dark-top.png` 1722x5400 (crop of README top; boxes json = huashu-readme-dark.json)  source: https://github.com/alchaincyf/huashu-motion/blob/main/README.en.md
- `assets/shots/huashu-readme-light-top.png` 1722x5400 (crop of README top; boxes json = huashu-readme-light.json)  source: https://github.com/alchaincyf/huashu-motion/blob/main/README.en.md
- `assets/shots/huashu-repo-top-dark.png` 2560x1640  source: https://github.com/alchaincyf/huashu-motion
- `assets/shots/huashu-repo-top-light.png` 2560x1640  source: https://github.com/alchaincyf/huashu-motion
- `assets/shots/hyperframes-repo-top-dark.png` 2560x1640  source: https://github.com/heygen-com/hyperframes
- `assets/shots/hyperframes-repo-top-light.png` 2560x1640  source: https://github.com/heygen-com/hyperframes

Key regions (CSS px, x2 for image px): huashu-readme-*: hero image y40-524, h1 'huashu-motion' y554, install `pre` y855, 'Point at the frame' h3 y1146 + image y1187-1672, 'Score first, then the picture' h3 y1878 + image y1919-2405, 'Twenty films in a day' y2522. huashu-repo-top-*: repo name at (64,192); About sidebar (MIT license, 1.4k stars, topics) at x~1220-1560 image px, y~330-930 image px. claude-motion-article: headline y~290-400 CSS, quote paragraph 'Claude Motion is in beta on Team and Enterprise.' inside paragraph at y~640-790 CSS. Always READ a plate image before using it so the framing is right.

## Clips (muted, 30fps, keyframe every 15 frames)
- `assets/clips/huashu-film.mp4` 960,540, 23.600000
- `assets/clips/hyperframes-film.mp4` 960,540 25.000000
- `assets/clips/readme-agentabc.mp4` 720,406 9.166667
- `assets/clips/readme-ctypingagent.mp4` 840,472 13.900000
- `assets/clips/readme-huashu-motion.mp4` 720,404 8.400000
- `assets/clips/readme-sixteen-cuts.mp4` 720,404 8.000000
  - huashu-film.mp4 / hyperframes-film.mp4: Chase's REAL head-to-head test renders (same brief, 16:9).
  - readme-*.mp4: the huashu-motion README demo GIFs (huashu-motion = wall-of-films hero, ctypingagent = point-at-the-frame editor, agentabc = score-first music staff, sixteen-cuts = 16 shots cut on the beat).

## Logos (simple-icons SVG, single-colour paths; set fill via CSS or inline)
- `assets/logos/anthropic.svg`
- `assets/logos/bytedance.svg`
- `assets/logos/claude.svg`
- `assets/logos/github.svg`
- `assets/logos/google.svg`
- `assets/logos/javascript.svg`
- `assets/logos/kuaishou.svg`
  (kuaishou = Kling's maker, bytedance = Seedance's maker; there is no official Kling/Seedance mark here - use wordmarks in type + these maker logos small)

## SFX
`assets/sfx/chime.mp3`, `assets/sfx/click-soft.mp3`, `assets/sfx/click.mp3`, `assets/sfx/error.mp3`, `assets/sfx/glitch-1.mp3`, `assets/sfx/glitch-2.mp3`, `assets/sfx/glitch-3.mp3`, `assets/sfx/impact-bass-1.mp3`, `assets/sfx/impact-bass-2.mp3`, `assets/sfx/key-press.mp3`, `assets/sfx/notification.mp3`, `assets/sfx/ping.mp3`, `assets/sfx/pop.mp3`, `assets/sfx/riser.mp3`, `assets/sfx/sparkle.mp3`, `assets/sfx/typing.mp3`, `assets/sfx/whoosh-cinematic.mp3`, `assets/sfx/whoosh-short.mp3`, `assets/sfx/whoosh.mp3`

## Fonts (woff2)
`assets/fonts/instrument-serif-latin-400-italic.woff2`, `assets/fonts/instrument-serif-latin-400-normal.woff2`, `assets/fonts/inter-latin-400-normal.woff2`, `assets/fonts/inter-latin-500-normal.woff2`, `assets/fonts/inter-latin-600-normal.woff2`, `assets/fonts/inter-latin-700-normal.woff2`, `assets/fonts/inter-tight-latin-500-normal.woff2`, `assets/fonts/inter-tight-latin-600-italic.woff2`, `assets/fonts/inter-tight-latin-600-normal.woff2`, `assets/fonts/inter-tight-latin-700-italic.woff2`, `assets/fonts/inter-tight-latin-700-normal.woff2`, `assets/fonts/inter-tight-latin-800-italic.woff2`, `assets/fonts/inter-tight-latin-800-normal.woff2`, `assets/fonts/inter-tight-latin-900-italic.woff2`, `assets/fonts/inter-tight-latin-900-normal.woff2`, `assets/fonts/jetbrains-mono-latin-400-normal.woff2`, `assets/fonts/jetbrains-mono-latin-500-normal.woff2`, `assets/fonts/jetbrains-mono-latin-700-normal.woff2`, `assets/fonts/newsreader-latin-400-italic.woff2`, `assets/fonts/newsreader-latin-400-normal.woff2`, `assets/fonts/newsreader-latin-500-italic.woff2`, `assets/fonts/newsreader-latin-500-normal.woff2`, `assets/fonts/space-grotesk-latin-500-normal.woff2`, `assets/fonts/space-grotesk-latin-700-normal.woff2`

## Vendor
- `assets/vendor/gsap.min.js` (GSAP 3.13, load with <script src>; no CDN)
