# Editorial pack: measured reference analysis (6 reels)

Measured 2026-10-22 from `reference\`:

- **reference creator A** (`ref-A*`, 30 fps): ref-A1 "5 Claude skills", ref-A2 "3D dashboards", ref-A3 "Artlist ad campaigns"
- **reference creator B** (`ref-B*`, 25 fps, Italian): ref-B1 "Vibe coding / 4 plugin", ref-B2 "Reverse Engineer Anything", ref-B3 "Adobe ammazzato"

All positions are in px on the 1080x1920 frame. Method and error bars are in section 8. Raw data lives in the scratchpad
(`donor-measure\metrics.json`, `editorial_final.json`, `<reel>\layout10.json`, `<reel>\beats.json`).

Layout codes: **S** = split (ivory/dark graphic panel y 0-960 + face cam y 960-1920, hard edge exactly at
**y = 960** in all 6 reels), **G** = full-graphic (panel fills the frame, face hidden), **F** = full-face (camera fills the frame).

---

## 1. Per-reel tables

### reference creator A

| metric | ref-A1 | ref-A2 | ref-A3 | reference A (3 reels) |
|---|---|---|---|---|
| duration | 62.9 s | 63.2 s | 65.4 s | 191.5 s |
| split S | 53.1 % | 66.5 % | 67.4 % | **62.4 %** |
| full-graphic G | 40.2 % | 33.5 % | 29.2 % | **34.2 %** |
| full-face F | 6.7 % (end CTA 4.2 s) | 0 % | 3.4 % (one mid beat 2.2 s) | **3.4 %** |
| layout switches | 19 (9.1 per 30 s) | 10 (4.7 per 30 s) | 13 (6.0 per 30 s) | **6.6 per 30 s** (4.7-9.1) |
| G takeovers (count, lengths) | 9: 1.9-3.6 s | 5: 2.1, 3.6, 4.3, 7.0, 4.2 | 6: 2.8-3.6 s | 20, median **3.1 s**, max 7.0 |
| longest face absence | 3.6 s | **7.0 s** (41.9-48.9) | 3.6 s | 3.6-7.0 s |
| visible graphic changes | 51 in 58.7 s = 0.87/s | 50 in 63.2 s = 0.79/s | 53 in 63.2 s = 0.84/s | **0.83/s** |
| beat median / p90 / max | 1.0 / 2.1 / 3.7 s | 1.1 / 2.2 / 3.0 s | 1.0 / 1.9 / 3.6 s | **1.0 / 2.2 / 3.7 s** |
| beats > 1.5 s | 22 % | 32 % | 22 % | 25 % |
| element entrances / s (rough) | 2.0 (hand window 2.1) | 1.4 | 2.0 | **~1.8/s** |
| frame 0 content | dark hook panel: "Skills" title + small sphere | blank ivory panel | dark panel + Claude logo | n/a |
| first visual change | 0.10 s (badge + sphere scale-up) | 0.10 s (title + card) | 0.10 s (light beam + tiles fly in) | **0.10 s** |
| first caption | 0.03 s | 0.00 s (on frame 0) | ≤ 0.10 s | ≤ 0.10 s |
| caption chunks | 72 | 105 | 74 | 251 |
| words per chunk: 1 / 2 / 3 / 4 | 2 / 14 / 54 / 2 | 9 / 96 / 0 / 0 | 6 / 10 / 58 / 0 | **7 % / 48 % / 45 % / 1 %** |
| mean words per chunk | 2.78 | **1.91** (2-word style) | 2.70 | 2.39 |
| chunks with accent colour | 0 % | 0 % | 0 % | **0 %** |
| chunk duration median | 0.8 s | 0.5 s | 0.85 s | 0.7 s (p10 0.4, p90 1.2) |
| CTA | F, last 4.2 s: caption chip moves to y 635 + white follow pill (reference creator A [Follow]) at y ≈ 1500 | S: "DASHBOARD" typed into input, then a "Step-by-step guide" checklist card builds (59.5-63.2) | dark G hero (59.1-62.7), then S: serif "Comment Artlist" + comment input typing "Artlist" (62.7-65.4) | n/a |

### reference creator B

| metric | ref-B1 | ref-B2 | ref-B3 | reference B (3 reels) |
|---|---|---|---|---|
| duration | 51.4 s | 39.6 s | 40.3 s | 131.3 s |
| split S | 87.1 % | 81.8 % | 86.9 % | **85.4 %** |
| full-graphic G | 12.9 % | 11.9 % | 6.0 % | **10.5 %** |
| full-face F | 0 % | 6.3 % (2.5 s) | 7.2 % (2.1 s + 0.8 s) | **4.1 %** |
| layout switches | 4 (2.3 per 30 s) | 3 (2.3 per 30 s) | 6 (4.5 per 30 s) | **3.0 per 30 s** |
| G takeovers | 2: 2.5 s (19 agenti cubes), 4.1 s (DevTools browser) | 1: 4.7 s (DX-Ball game) | 1: 2.4 s (GitHub page) | 4, median **3.3 s**, max 4.7 |
| F beats | none | 1: 2.5 s, serif title "vecchi *programmi*" over the head | 2: 2.1 s ("Il software in abbonamento è *morto?*"), 0.8 s ("Roba da *matti.*") | F = punchline beat with serif title over the head |
| longest face absence | 4.1 s | 4.7 s | 2.4 s | 2.4-4.7 s |
| visible graphic changes | 62 in 51.4 s = 1.21/s | 44 in 37.1 s = 1.19/s | 47 in 37.4 s = 1.26/s | **1.22/s** |
| beat median / p90 / max | 0.75 / 1.3 / 1.7 s | 0.7 / 1.4 / 1.9 s | 0.7 / 1.1 / 1.8 s | **0.7 / 1.3 / 1.9 s** |
| beats > 1.5 s | 3 % | 7 % | 4 % | 5 % |
| element entrances / s (rough) | 2.0 (hand window 2.1) | 2.0 | 2.2 | **~2.1/s** |
| frame 0 content | HUD "CLAUDE CODE 0/4" already on | "Trending" card already on | clay cube + Adobe logo already on | graphics present at frame 0 |
| first visual change | 0.08 s (HUD status dot); first new element 0.88 s ("*Vibe* coding" fades in) | 0.08 s (card rows populate) | ≈ 0.8 s (cube lifts) | 0.08-0.9 s |
| first caption | 0.08 s | 0.08 s | 0.08 s | 0.08 s (frame 2) |
| caption chunks | 69 | 48 | 50 | 167 |
| words per chunk: 1 / 2 / 3 | 12 / 8 / 49 | 3 / 8 / 37 | 5 / 6 / 39 | **12 % / 13 % / 75 %** (no 4+) |
| mean words per chunk | 2.54 | 2.71 | 2.68 | **2.63** |
| chunks with accent colour | 10 % | 6 % | 6 % | **8 %** |
| chunk duration median | 0.7 s | 0.8 s | 0.8 s | 0.7 s (p10 0.4, p90 1.2) |
| CTA | S, last ≈ 3.8 s: Instagram-style "Commenti" sheet, "plugin" typed and posted, then a DM card | S, last 5.0 s: "repo" typed, then a DM card with the repo link + "Guida per installarlo" + progress | S, last 5.0 s: "LISTA" typed, then a DM card with app icon grid + link + "Come installarle" | always S; comment-then-DM mock |

### Combined editorial (6 reels, 322.9 s)

| metric | value |
|---|---|
| S / G / F | **71.8 % / 24.6 % / 3.7 %** |
| layout switches | 4.8 per 30 s (range 2.3-9.1) |
| G takeover length | median 3.1 s, range 1.9-7.0 s (n = 24) |
| beat median / p90 / max | **0.8 / 1.8 / 3.7 s** |
| visible changes per s | 0.99 |
| caption words per chunk 1 / 2 / 3 / 4 | 9 % / 34 % / 57 % / 0.5 % (mean 2.49) |
| accent chunks | 3 % (all from reference B) |
| caption chunk duration | median 0.7 s |

---

## 2. Layout strips, one character per 0.5 s

Legend: `S` split · `G` full-graphic (face hidden) · `F` full-face. Each line is 10 s, in two 5 s groups.

```
reference A ref-A1 (62.9 s)
  0.0s  SSSSSSSSSS SSSSSSSSSS      0-9.6 dark hook panel
 10.0s  SSSSGGGGGG SSSSGGGGSS
 20.0s  SSGGGGGGGS SSSGGGGSSS
 30.0s  SSGGGGGGSS SSGGGGGGSS
 40.0s  SSSGGGGGSS SSGGGGGSSS
 50.0s  SSSGGGGGGG GSSSSSSFFF
 60.0s  FFFFFF                    F 58.7-62.9 = CTA

reference A ref-A2 (63.2 s)
  0.0s  SSSSSSSSSS SSSSSSSSSS
 10.0s  SGGGGGSSSS SSSSGGGGGG
 20.0s  GSSSSSSSSS SSSSSSSSSS
 30.0s  SGGGGGGGGG SSSSSSSSSS
 40.0s  SSSSGGGGGG GGGGGGGGSS      7.0 s takeover 41.9-48.9
 50.0s  SSSSSGGGGG GGGSSSSSSS
 60.0s  SSSSSSS

reference A ref-A3 (65.4 s)
  0.0s  SSSSSSSSSS SSSSSSSSSS
 10.0s  SSGGGGGGSS SSSSSSSSSS
 20.0s  SSSSSSGGGG GGGFFFFSSS      F 26.5-28.7 (mid punchline)
 30.0s  SSGGGGGGSS SSSSSSSSSS
 40.0s  SGGGGGGSSS SSSSSSSSSS
 50.0s  SSSGGGGGGG SSSSSSSSGG
 60.0s  GGGGGSSSSS S

reference B ref-B1 (51.4 s)
  0.0s  SSSSSSSSSS SSSSSSSSSS
 10.0s  SSSSSSSSSS SSSSSSSSSS
 20.0s  SSSSSSSSSS SSSSGGGGGS      G 26.8-29.3 (19 agenti cubes)
 30.0s  SSSSSSSSSS SSSSSSSSSS
 40.0s  SGGGGGGGGS SSSSSSSSSS      G 40.5-44.6 (DevTools)
 50.0s  SSS

reference B ref-B2 (39.6 s)
  0.0s  SSSSSSSSSS SSSSSSSSSS
 10.0s  SSSSSSSSSS SFFFFFGGGG      F 15.6-18.1, G 18.1-22.8
 20.0s  GGGGGGSSSS SSSSSSSSSS
 30.0s  SSSSSSSSSS SSSSSSSSSS

reference B ref-B3 (40.3 s)
  0.0s  SSSSSSSSSS SSSSSSSSSS
 10.0s  SSSSSSSSSG GGGGSSSSSS      G 14.5-16.9
 20.0s  SSSSFFFFSS SSSSSFFSSS      F 21.8-23.9, F 27.6-28.4
 30.0s  SSSSSSSSSS SSSSSSSSSS
 40.0s  S
```

Exact runs (10 fps, boundaries ±0.1 s):

- Deg8: S 0-12.2 · G 12.2-15.1 · S -17.2 · G -19.1 · S -21.1 · G -24.6 · S -26.3 · G -28.6 · S -30.8 · G -34.2 · S -36.2 · G -38.9 · S -41.6 · G -44.1 · S -46.2 · G -48.7 · S -51.7 · G -55.3 · S -58.7 · F -62.9
- Deon: S 0-10.7 · G -12.8 · S -17.0 · G -20.6 · S -30.5 · G -34.8 · S -41.9 · G -48.9 · S -52.5 · G -56.7 · S -63.2
- Der9: S 0-11.1 · G -13.9 · S -22.9 · G -26.5 · F -28.7 · S -30.8 · G -33.8 · S -40.6 · G -43.4 · S -51.7 · G -55.0 · S -59.1 · G -62.7 · S -65.4
- DemE: S 0-26.8 · G -29.3 · S -40.5 · G -44.6 · S -51.4
- Detse: S 0-15.6 · F -18.1 · G -22.8 · S -39.6
- Deyz: S 0-14.5 · G -16.9 · S -21.8 · F -23.9 · S -27.6 · F -28.4 · S -40.3

**Pattern differences between the two creators:**

- **reference A** opens with a 10-12 s S block (hook plus "number one is...") and then alternates **S ≈ 2-4 s / G ≈ 2-4 s like a
  metronome**. Deg8 cuts to G for each skill demo and back to S for each skill title card. Full-face appears only as
  the CTA or one punchline. The S panel is ivory #EEEEE7. Deg8's hook uses a dark olive-black panel (#1B1D18), and
  about half of Der9 uses a near-black panel (#010303).
- **reference B** stays on S for 85 % of the reel. There are 1-2 full-graphic takeovers of 2.4-4.7 s for the biggest
  visual (agent swarm, browser DevTools, a game, a repo page). F is used for a spoken punchline, with a large serif
  title (one italic clay word) over the head and the chip on the chest. reference B's ivory is #EEECE8.

---

## 3. Captions (every chunk; see section 8)

| property | reference A | reference B |
|---|---|---|
| build | **hard swap**, frame-exact, no transition; no word-by-word build | **hard swap**, frame-exact; no word-by-word build |
| words per chunk | 1: 7 % · 2: 48 % · 3: 45 % · 4: 1 % (Deon is almost all 2-word; Deg8 and Der9 mostly 3-word) | 1: 12 % · 2: 13 % · 3: **75 %** |
| chunk duration | median 0.7 s (Deon 0.5 s) | median 0.7 s |
| case | ALL CAPS | ALL CAPS (Italian accents kept: È, PIÙ, SARÀ) |
| font (guess) | JetBrains Mono class, **Bold/ExtraBold** | JetBrains Mono class, **Medium/SemiBold** |
| size | cap height 41-42 px; advance 34.3 px/char → **≈ 57 px** | cap height 35 px; advance 27.5 px/char → **≈ 46 px** |
| text colour | #F8FAFA | #F3F5F5 |
| accent | none (0/251 chunks) | **8 % of chunks**: product or keyword in clay **≈ #E0907E** (anti-aliased mean #DE8F80, core #EF9F95). Usually clay from chunk start; in 2 of 13 cases it turns clay 0.1-0.25 s in, on the spoken word. CTA keyword is always clay ("COMMENTA *PLUGIN* E") |
| chip | ≈ #1C1E1B at ~90 % opacity (reads #101010 over the dark room), radius ≈ 14 px, **height ≈ 110 px**, side padding ≈ 30 px; width ≈ 34.3 × chars + 60 | ≈ #1D1D1A, radius ≈ 11 px, **height ≈ 78-82 px**, side padding ≈ 24 px; width ≈ 27.5 × chars + 48 |
| y (text centre), S | **961**: chip y 905-1015, centred on the seam at 960 | **960**: chip y ≈ 921-1003, centred on the seam |
| y, G | **1480** (chip 1423-1533) | **1560-1580** (chip ≈ 1541-1618) |
| y, F | 635 (CTA, upper third) / 1537 (mid punchline) | 1392 (chest) |
| horizontal | centred on x = 540 | centred on x = 540 |

---

## 4. Graphic band rhythm

- **reference B:** a visible change about every 0.7 s (1.22/s). Only 5 % of beats exceed 1.5 s and the max is 1.9 s.
  Changes are cards fading in, rows or check marks appearing, connector lines drawing, HUD slot fills, big numerals
  and strike-X marks. Element entrances ≈ 2.1/s.
- **reference A:** a visible change about every 1.0 s (0.83/s) with longer holds: 25 % of beats exceed 1.5 s and the max is
  3.7 s. reference A's long beats are not static. They are filled by typing in a command bar, progress bars filling, a
  rotating 3D city, or an orbiting tile cloud. Element entrances ≈ 1.8/s, often as staggered sets (5 agent cards
  0.2 s apart, 5 check marks, 5 diagram labels).
- **Both:** typing at roughly 15-25 chars/s is the main between-beat motion. HUDs persist (reference B DemE "CLAUDE CODE
  x/4" at y ≈ 806-885; reference A "SKILL n OF 5" + 5-step dots). Every layout change is a hard cut.

---

## 5. CTA treatments

- **reference B (all 3):** stays split. Over the last 3.8-5.0 s the top panel becomes an Instagram-style **comments
  sheet**. The keyword is typed into the comment field and posted. Then a **DM card from reference creator B** builds
  with the promised item (link, guide with progress bar, or app list with icons). The chip reads "COMMENTA
  *KEYWORD* E TI MANDO IN PRIVATO ...". The keyword is clay in both the chip and the field.
- **reference A:** varies by reel.
  - Deg8 ends **full-face** (4.2 s). The caption chip moves up to y 635 and a white rounded follow pill
    ("How to use these skills / reference creator A / [Follow]" with a clay button) sits at y ≈ 1500.
  - Deon stays split. "DASHBOARD" is typed into an input, then a "Step-by-step guide" checklist card builds.
  - Der9 shows a 3.6 s dark full-graphic brand hero, then split with a serif "Comment *Artlist*" title and a comment
    input that types "Artlist".
- The spoken CTA starts **2.6-5.0 s** before the end: reference B 4.0-5.0 s; reference A 4.1 s (Deg8), 3.7 s (Deon) and
  2.6 s (Der9, after a 3.6 s brand-hero outro).

---

## 6. Measured targets

The *default* target is the 6-reel blend. Where the two creators differ, the variant targets are given as
**J:** (reference A-like) and **M:** (reference B-like). Pick one variant per video and do not average within a video.

| metric | target | tolerance |
|---|---|---|
| Seam / face cam | hard edge at y = 960, face cam y 960-1920 | exact |
| Split (S) share | default 72 % · J: 62 % · M: 85 % | ±8 pp |
| Full-graphic (G) share | default 25 % · J: 34 % · M: 10.5 % | ±8 pp (J reels 29-40 %, M reels 6-13 %) |
| Full-face (F) share | default 4 % · J: 0-7 % (CTA or 1 punchline) · M: 0-7 % (punchline beats with serif title) | ≤ 8 % |
| Layout switches | default 4.8 per 30 s · J: 6.6 per 30 s · M: 3.0 per 30 s | J ±2, M ±1.5 |
| G takeover length | median 3.1 s | 1.9-4.7 s typical; one long takeover up to 7.0 s allowed |
| G takeovers per minute | J: 4.7-8.6 (mean 6.3) · M: 1.5-2.3 | ±1 |
| Longest face absence | J: 3.6 s (one 7.0 s) · M: 2.4-4.7 s | ≤ 7.0 s |
| Opening S block before the first cut | J: 10-12 s · M: 14-27 s (or straight to F at 15.6 s) | ±3 s |
| First visual change | ≤ 0.10 s (J), or graphics present at frame 0 with first new element ≤ 0.9 s (M) | frame 0 must not be an empty panel for M; J may start empty and fill by 0.1 s |
| First caption | 0.00-0.08 s | ≤ 0.1 s |
| Beat median (visible graphic change interval) | default 0.8 s · J: 1.0 s · M: 0.7 s | ±0.15 s |
| Beat p90 | J: 2.2 s · M: 1.3 s | ±0.3 s |
| Beat max | J: 3.7 s (with continuous motion inside) · M: 1.9 s | J ≤ 4 s, M ≤ 2.2 s |
| Beats longer than 1.5 s | J: 25 % · M: 5 % | ±8 pp |
| Visible graphic changes per s | J: 0.83 · M: 1.22 | ±0.15 |
| Element entrances per s | J: 1.8 · M: 2.1 | ±0.5 (rough metric) |
| Caption build | hard swap, no animation, no karaoke | exact |
| Words per caption chunk | J: 2: 48 % / 3: 45 % / 1: 7 % (or an all-2-word variant like Deon) · M: 3: 75 % / 2: 13 % / 1: 12 % | mean J 2.4 ±0.3, M 2.6 ±0.2; never > 4 |
| Caption chunk duration | median 0.7 s | p10 0.4 s, p90 1.2 s |
| Chunks with accent colour | J: 0 % · M: 8 % (product names + CTA keyword) | M ±4 pp |
| Caption case | ALL CAPS mono | exact |
| Caption chip font size | J: ≈ 57 px (cap 42) · M: ≈ 46 px (cap 35) | ±3 px |
| Caption chip height | J: 110 px · M: 80 px | ±6 px |
| Caption y (text centre) | S: 960 (chip centred on the seam) · G: J 1480, M 1560-1580 · F: M 1392, J 635 (CTA) | ±10 px S; ±20 px G/F |
| Accent colour (M) | clay ≈ #E0907E text on the dark chip | ±10 per channel |
| CTA | M: split comments sheet → typed keyword → DM card, last 3.8-5.0 s · J: comment/keyword card or follow pill, last 2.7-4.2 s | spoken CTA starts 2.6-5.0 s before the end (M 4.0-5.0, J 2.6-4.1) |

---

## 7. Composition notes measured along the way

- Ivory: reference A #EEEEE7, reference B #EEECE8 (reference B's lower full-graphic area shades to ≈ #E4E2DE).
- reference A's dark panels: Deg8 hook #1B1D18 (olive-black) with clay accents; Der9 near-black #010303 with gold/clay
  accents.
- reference B DemE's persistent HUD "CLAUDE CODE n/4" (4 slot tiles + connector "cables") sits at y ≈ 806-885, directly
  above the caption chip. Cards connect to slots with drawn lines when each plugin is named.
- reference B's F punchlines put a large serif headline at the top (y ≈ 160-210, one italic clay word) over the
  full-frame face, with the caption chip at y 1392.

---

## 8. Method and uncertainty

- **Layout:** OpenCV Haar face detection and a lower-frame texture test ran at 10 fps. Every 0.5 s cell was then
  checked visually on annotated contact sheets. The auto-labeller needed corrections in 5 places, all reference B
  takeovers or punchline F beats and two first frames. Boundaries are ±0.1 s.
- **Beats / visible changes:** an automatic detector measured new edge pixels plus newly saturated colour inside
  the graphic region. The region is y 0-890 (J) or 0-900 (M) in S, and the whole frame minus the caption-chip band
  in G; F is excluded. Changes were detected as peaks at 10 fps and merged within 0.35 s. I hand-annotated
  reference A Deg8 10-32 s and reference B DemE 0-22 s to check it: **precision and recall ≈ 90-95 % on both**. Hand medians
  were 1.0 s (J) and 0.7 s (M), matching the auto values. Treat medians as ±0.1 s and maxima as ±0.5 s.
- **Element entrances:** connected regions of new content per change. Calibrated against hand counts on the same
  windows (J: 46 in 22 s; M: 47 in 22 s; auto/hand factor 1.02 for J and 1.17 for M). Expect ±30 %.
- **Captions:** each chip band was OCR'd every 0.1 s (Windows OCR) and grouped into chunks. Word counts came from gaps
  between text glyphs (mono-space word spaces), which catches 1-letter words and numbers that OCR drops. All 57
  chunks where OCR and gap counts disagreed, and all 46 OCR-only chunks, were checked visually and fixed by hand.
  Apostrophes (YOU'RE, UN'APP) count as one word. Accent = clay text pixels inside the chip in ≥ 2 frames; one false
  positive (skin through the translucent chip in a reference A F beat) was removed. Residual chunk-count error ≈ ±3 %.
- **Font names** are visual guesses. Sizes come from measured cap height and character advance.
- **Note:** some measurements differ from the current `STYLE.md`: chip 52 px/92 px, "~80 % split, 1-3 takeovers of
  1.5-3 s", and accent words inside the chip. Measured: J chip 57 px/110 px with no accent, M chip 46 px/80 px with an
  8 % clay accent, J takeovers 5-9 per minute, M 1-2 per reel at 2.4-4.7 s. `STYLE.md` was not modified.
