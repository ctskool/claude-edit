# Editorial kit: `editorial-chiefofstaff`

Reusable components for the **editorial** style (Claude design language: ivory panel, clay accent, serif titles,
rebuilt white UI cards, mono caption chips on the seam). Distilled from the frame-matched replica of
**reference creator A "5 Claude skills", seconds 9.5-20.5 (skill 1: Chief of Staff)**:
`work\replica\editorial-chiefofstaff` (index.html + SPEC.md).

Every number here was **measured on the 1080x1920 / 30 fps reference**. Numbers marked *(unmeasured)* are defaults
for content the reference did not show. They follow the same system, but no reference frame checks them.

| file | what |
|---|---|
| `kit.css` | `@font-face` (assets/fonts), tokens on `:root`, component classes (`k-` prefix), opt-in `.k-contrast` |
| `kit.js` | `window.KIT`: DOM builders + their measured GSAP animation, caption tools, icon sprite |
| `demo.html` | the whole reference window (11.008 s) rebuilt **only** from kit calls; doubles as the regression test |

**Fidelity (verified 2026-10-22, `kit-test`):** the demo renders **pixel-identical** to the hand-built replica at 43
timestamps, including mid-motion frames. Mean SSIM is 0.99999, and the largest difference is 17/255 on a few
antialiased edge pixels. Against the reference video (graphics band y 0-960, 43 frames) it scores mean SSIM **0.966** with colour
error 2.31, the same as the replica (0.967 on its 27 keyframes). Lint shows 0 errors. Runtime, layout and motion are clean.

---

## 0. Setup (read first)

1. Copy `kit.css` and `kit.js` into the **project root**, next to `index.html`. The project's `assets/` folder must
   sit beside them. CSS `url()` resolves relative to the stylesheet, so the fonts load from `assets/fonts/…`.
   The kit needs these assets, all in the shared set that `tools/scaffold_styles.sh` copies from
   `work/<id>/shared/` into `assets/`: `assets/vendor/gsap.min.js`, `assets/fonts/inter-latin-{400,500,600,700}-normal.woff2`,
   `newsreader-latin-{400,500}-{normal,italic}.woff2`, `jetbrains-mono-latin-{500,700}-normal.woff2`.
2. `<head>` order: `gsap.min.js` → `<link rel="stylesheet" href="kit.css">` → `<script src="kit.js">`.
3. The root gets `class="k-root"`, which sets the Inter/ink defaults, `svg {stroke-width:2}` and `will-change: transform`.
   The last one forces grayscale text AA, as in the reference; Chrome on Windows otherwise draws LCD colour fringes.
4. **Clips stay static HTML.** Every scene is an empty `<section class="clip k-scene …" data-start data-duration>` in
   `index.html`, and the kit fills it from your inline script. Never create clips from JS.
5. Build everything synchronously, then `window.__timelines["<composition-id>"] = tl` (one paused timeline).
6. All kit animation is `fromTo` / `set` on children of clips. Clips never get visibility, display or autoAlpha tweens.

```html
<head>
  <script src="assets/vendor/gsap.min.js"></script>
  <link rel="stylesheet" href="kit.css" />
  <script src="kit.js"></script>
</head>
<body>
  <div id="root" class="k-root" data-composition-id="main" data-start="0" data-duration="48" data-width="1080" data-height="1920" data-fps="30">
    <div class="k-face-wrap">
      <video id="face" class="k-face" src="assets/face_half.mp4" muted playsinline data-start="0" data-duration="48" data-media-start="0.01"></video>
    </div>
    <audio id="voice" src="assets/voice.m4a" data-start="0" data-duration="48"></audio>
    <section id="s1" class="clip k-scene"        data-start="0.0833" data-duration="2.5667"></section>  <!-- split -->
    <section id="s2" class="clip k-scene k-full" data-start="2.65"   data-duration="2.8667"></section>  <!-- takeover -->
    <div id="hud" class="clip k-hud" data-start="2.65" data-duration="6.9333"></div>
    <div id="caps" class="k-caps"></div>
  </div>
  <script>
    const $ = (id) => document.getElementById(id);
    const tl = gsap.timeline({ paused: true });
    /* ...KIT calls... */
    window.__timelines["main"] = tl;
  </script>
</body>
```

## 1. Conventions shared by every component

- **Coordinates** are absolute canvas px, measured on the reference, and every builder defaults to them. A scene
  section is 1080x960 (split) or 1080x1920 (full) at 0,0, so scene px equal canvas px. Card-internal offsets are
  relative to the card's padding box, inside its border.
- **Signature:** `KIT.thing(tl, parent, opts, t)` builds DOM inside `parent`, adds tweens at time `t` (seconds, root
  timeline) and returns the created nodes. Static builders omit `tl`/`t`.
- **Frames:** HyperFrames floors `t*30`. Author clip windows and hard sets at **mid-frame**: `KIT.at(k) = (k-0.5)/30`,
  `KIT.clip(k0,k1)` → `{start, duration}` for frames k0..k1-1. Example: `KIT.clip(3,80)` = 0.0833 / 2.5667.
- **Video media-start 0.01:** give the face `<video>` `data-media-start="0.01"`. Exact frame times such as 5.5333 would
  otherwise floor to the previous video frame.
- **GSAP ease names:** `powerN` is degree N+1, so `power2` is cubic. Every fit below is stated in GSAP names.
- **Mono hyphens** in the reference are en-dash-width glyphs. The kit converts `-` → U+2013 in typed commands and the HUD slug.

### Motion primitives: `KIT.pop`, `KIT.rise`, `KIT.hideAt`

**What it is:** the reference has one "pop" for everything that appears in place, and one "rise" family for cards
that arrive with a cut.

| preset | scale | ease | duration | opacity (linear) | used by |
|---|---|---|---|---|---|
| `POP.std` | 0.6 → 1 | `back.out(1.7)` (peak ≈1.04 at 58 %) | 0.26 s | 0 → 1 over 0.10 s | active step, NEW cell, Claude chip |
| `POP.tile` | 0.6 → 1 | back.out(1.7) | 0.30 s | 0.12 s | skill icon tile |
| `POP.node` | 0.6 → 1 | back.out(1.7) | 0.235 s | 0.12 s, starts 0.008 s early | org-tree node |
| `POP.agent` | 0.6 → 1 | back.out(1.7) | 0.235 s | 0.09 s | agent cards |
| `POP.check` | 0.6 → 1 | back.out(1.7) | 0.235 s | 0.085 s | row checks |
| `POP.goal` | 0.6 → 1 | back.out(1.7) | 0.303 s | 0.125 s | big goal card |

| preset | y | move | fade | used by |
|---|---|---|---|---|
| `RISE.card` | +60 → 0 | 0.30 s `power3.out` | 0.12 s `power1.inOut` from +0.005 s | skill card (measured +30 @0.053 s, +14 @0.087, +6 @0.12) |
| `RISE.panel` | +36 → 0 | 0.25 s `power2.out` | 0.09 s linear from +0.005 s, **with blur 6 → 0 px** | calendar card |
| `RISE.row` | +30 → 0 | 0.20 s `power2.out` | 0.065 s linear | compact goal card, list rows |

```js
KIT.pop(tl, node, 3.01);              // std
KIT.pop(tl, node, 6.064, "agent");
KIT.rise(tl, card, 7.655, "row");
KIT.hideAt(tl, placeholderSvg, 4.56); // hard opacity 0
```

---

## 2. Layout: split, full takeover, dark hook

**What it is:** three stacked layers with hard cuts and no transitions. The face cam is z 1, scenes z 2, the HUD z 3
and captions z 5.

- **Split** (`.k-scene`): ivory `#EEEEE7` panel y 0-960 with a hard edge at y 960. `.k-face-wrap` holds the face cam
  at y 960-1920 (`object-fit: cover`, `object-position: 50% 0%`).
- **Full takeover** (`.k-scene.k-full`): an ivory scene 1920 tall that covers the face, which keeps playing underneath.
  The caption rail drops to y 1423.
- **Dark hook** (`.k-scene.k-dark`): `#1B1D18` panel for the opening title card.

**When:** in reference A's cadence a split section of about 2-4 s alternates with a takeover of about 2-4 s. Each deep
dive (calendar, goal, progress) is a takeover; the "who does it" beat (agent tree) is split. See
`../../REFERENCE-ANALYSIS.md` for the measured S/G/F shares per creator.

```html
<section id="s2" class="clip k-scene k-full" data-start="2.65" data-duration="2.8667"></section>
```
```js
KIT.takeover(tl, $("caps"), 80, 166);   // caption rail -> 1423 at frame 80, back to 904 at 166
```

## 3. Captions: `KIT.captions`, `KIT.chunkWords`, `KIT.captionRail`, `KIT.takeover`, `KIT.captionChip`

**What it is:** a dark mono chip with a **hard swap** (no fade, no karaoke, no accent colour in reference A's variant).

**When:** always, from frame 0 to the end. Every visible frame carries a chip except brief gaps between sentences.

**Measured:** JetBrains Mono 700, 55 px, tracking 2.25 px, UPPERCASE, white on `rgba(15,17,17,0.94)`. Height 111,
r 14, padding `4px 33px 0`, centred on x 540. Chip top is **904** in split (centred on the seam) and **1423** in a full
takeover. Chunks hold up to 3 words, and a sentence end closes a chip early. The swap lands on `floor(word.start*30)`
±1 frame.

**Parameters:**
- `KIT.chunkWords(words, {max:3, lead:0, gap:0.6, hold:0.15, offset:0})`: `words` is `[{text,start,end}]` (words.json),
  and the result is `[{text,k0,k1}]`. Each chip stays on until the next chip's frame. If the silence exceeds `gap`,
  it goes off at `floor((end+hold)*30)`. On this reference it reproduces the editor's chunk boundaries for all 15
  chips. Every swap is within ±1 frame except two where the editor ran 5-6 frames late, plus the first chip, which
  was held over from the previous segment. Chip text comes from the transcript, so a misheard word stays misheard
  (`THE ANATOMIST` where the editor typed `THE ANATOMY SKILL`). Fix the text, or pass explicit chunks.
- `KIT.captions(tl, rail, chunks)`: chunks are `{text,k0,k1}` (frames) or `{text,start,end}` (seconds, floored).
- `KIT.captionRail(tl, rail, [[frame,"full"|"split"],...])` and `KIT.takeover(tl, rail, k0, k1)` move the rail.

```js
const chunks = KIT.chunkWords(transcript.words);
KIT.captions(tl, $("caps"), chunks);
KIT.captionRail(tl, $("caps"), []);           // start at 904
KIT.takeover(tl, $("caps"), 80, 166);
```

## 4. Skill card: `KIT.skillCard(tl, scene, o, t)`

**What it is:** the "SKILL n OF N" beat. It has a tracked grey label, a white card holding a clay icon tile, a serif
title and a dark command bar that types the skill's slug, and the 5-dot stepper below.

**When:** at the cut that opens each list item ("Number one is…"), in split layout, held about 2.5 s while the slug types.

**Parameters:** `{n, total(5), label?, title, titleScaleX(.93), icon("users"|"layers"|any lucide), command,
typeAt(t+.3533), typeStep(.05), stepAt(t+.23)}`. `t` is when the card arrives (0.003 s before the clip start).

**Measured:**
- **Label:** Inter 700 25 px, tracking .152em, `#82827A`, centred, cap height 242-260 (top 239).
- **Card:** 90,290, 900x400, r 30, border 3 `#DEDED6`, fill `#FAFCFB`, shadow `0 10 26 rgba(70,70,50,.07)`.
- **Tile:** card +44,+44, 150x150, r 34, clay `#CB6D55`, shadow `0 12 26 rgba(203,109,85,.28)`. The users glyph is
  custom (stroke 5.2). Lucide glyphs sit at 84 px, offset 32,31, stroke 1.55.
- **Title:** Newsreader 400, 93 px, card +231,+81, tracking -0.01em, `scaleX(.93)` ("Chief of Staff") or `.969`
  ("Anatomy"). See §15.
- **Command bar:** card +44,+236, 812x120, r 26, `#1B1D18`. Clay chevron `#C9705D` 12x20 at +44,+48. Text JetBrains
  Mono 700 44 px white at +87,+34.5 (advance 26.4 px per char).
- **Motion:** RISE.card at t, then POP.tile at t+0.099, then the active step's POP.std at t+0.23. Typing starts at
  t+0.3533. Cadence was **0.05 s/char** (20 cps) for skill 1 and **0.10 s/char** for skill 2; the reel varies it per skill.

```js
KIT.skillCard(tl, $("s1"), { n: 1, total: 5, title: "Chief of Staff", icon: "users", command: "chief-of-staff" }, 0.08);
KIT.skillCard(tl, $("s5"), { n: 2, title: "Anatomy", titleScaleX: 0.969, icon: "layers", command: "anatomy",
  typeAt: 9.9333, typeStep: 0.1, stepAt: 9.79 }, 9.563);
```

## 5. Stepper: `KIT.stepper(tl, parent, o, t)` (used by skillCard)

**What it is:** numbered progress dots on a rail. Earlier steps are done (clay outline and digit, clay rail segment),
the current step is a filled clay disc with a halo, and later steps are grey outlines.

**When:** under every skill card. It shows where we are in the list.

**Parameters:** `{count(5), active(1), pitch(160), x0(auto: 188 for 5), top(758)}`. The active step pops at `t`.

**Measured:** circles 70 px, border 4 `#D5D6CA`, fill card. Centres sit at x 222.5+160n, y 792.5. Rail 6 px
`#D5D6CA` at y 790 from x 222 to 862. Active: clay fill, white digit 33 px, halo `0 0 0 10px rgba(203,109,85,.15)`.
Digits are Inter 600 34 px `#ADAEA4`. The outline-step digit sits +4 x / +2.5 y off centre, as in the reference.
Done steps: clay border and digit, clay rail segment from step 1 to the active step.

```js
KIT.stepper(tl, scene, { count: 3, active: 2 }, 1.3);   // 3-step variant, centred at x 543 (unmeasured count)
```

## 6. Typing: `KIT.typeText(tl, node, text, t, step, {enDash})` (alias `KIT.terminalType`)

**What it is:** characters appear one by one by hard opacity set (no caret, no fade), at `t + step*i - 0.012`.

**When:** any command bar or input. Typing was the main motion filling long holds; reference A beats of 2-3.7 s are never static.

**Measured:** 0.05 or 0.10 s per char. Returns the time of the last character.

```js
const end = KIT.typeText(tl, myMonoDiv, "npm run build", 2.0, 0.05);
```

## 7. HUD: `KIT.hud(tl, host, o)` and `KIT.hudFill(tl, hud, i, t)`

**What it is:** a persistent header for a skill's deep dive. A dark pill reads `1/5  chief-of-staff` (counter in
clay, slug in white) and N progress dashes sit at the right.

**When:** from the first takeover of a skill to its last beat, on its own clip (`.clip.k-hud`, z 3) so it survives the
scene cuts underneath. In the reference it spans S2-S4 (2.65-9.58 s) and appears with the cut, without animating in.

**Parameters:** `{index(1), total(5), slug, pillW?, fill:"upto"|"only"}`.

**Measured:**
- **Pill:** 90,226, 311x46, r 9, `#1B1D18`. Text JetBrains Mono 700 24 px at top +9: counter at +19 (clay), slug at
  +91 (white). Auto width = 109.4 + 14.4 x slug chars.
- **Dashes:** 50x10, r 5, at y 244, pitch 60, right-aligned so the last one ends at x 990 (x 700…940 for 5). The
  current one is clay, the others `#D5D6CA`.
- Only index 1 was observed. Filling dashes 1..index for later skills is *(unmeasured)*.

```js
const hud = KIT.hud(tl, $("hud"), { index: 1, total: 5, slug: "chief-of-staff" });
```

## 8. Calendar card: `KIT.calendarCard(tl, parent, o, t)`

**What it is:** a two-row week strip, LAST WEEK and THIS WEEK, with seven day cells each. One cell is a clay "NEW" chip.

**When:** for "it came out last week" or any time or recency beat. It opens a takeover and arrives with the cut.

**Parameters:** `{x(90), y(300), days[7], rows:[{label, tone:"l"|"n", dim}], newCell:{row,col,text}|null, newAt}`.

**Measured:**
- **Card:** 900x255, r 30, border 3 `#DEDED6`, shadow card.
- **Labels:** Inter 700 22 px, .14em, at +36,+70 and +36,+166; `#111313` and dim `#ACACA8`.
- **Cells:** 80x80, r 16, at x +237+92i, y +40 / +136. Last week is `#EBEADF` with text `#9F9E92` and inset
  `0 -2 4 rgba(0,0,0,.025)`. This week is `#F2F2ED` with text `#C4C4BC`. Inter 600 23 px.
- **NEW:** clay, white Inter 700 22 px with .02em tracking, 6 px bottom padding, halo 6 px. It pops (std) 0.375 s after the card.
- **Motion:** RISE.panel at t (blur 6 → 0 over 0.09 s). Measured label offsets: +25 @+0.032 s, +14 @+0.065 s, +7 @+0.098 s.

```js
KIT.calendarCard(tl, $("s2"), { newCell: { row: 0, col: 3, text: "NEW" }, newAt: 3.01 }, 2.635);
```

## 9. Dashed placeholder: `KIT.placeholder(parent, {x,y,w,h,r,inset})` (alias `KIT.outlineBox`)

**What it is:** a dashed outline that reserves a slot before its card lands. Hide it with `KIT.hideAt` once the card is solid.

**When:** a takeover that will build downward (the goal slot under the calendar), or a row of agent slots under a
tree. It shows the viewer that something is coming.

**Measured:** stroke `#CECFC7` 4 px, dash 8.5 / gap 4. Goal slot is 900x470, r 38, stroke centred on the box edge
(`inset:false`), hidden 0.11 s after the card's pop starts. Agent slots are 164x250, r 23, stroke inside the box
(`inset:true`), each hidden 0.09 s after its card's pop starts.

```js
const slot = KIT.placeholder($("s2"), { x: 90, y: 640, w: 900, h: 470, r: 38 });
KIT.hideAt(tl, slot, 4.56);
```

## 10. Goal card (hero): `KIT.goalCard(tl, parent, o, t)`

**What it is:** the big clay-outlined hero card. It holds a clay target disc, a clay eyebrow and a large serif statement.

**When:** for the one key noun or claim of a section ("ONE BIG GOAL / Launch Course"), in a takeover. It pops about
0.19 s **before** the phrase is spoken.

**Parameters:** `{x(90), y(640), icon("target" | lucide), eyebrow, words:[{text,left,scaleX}] | title, size(115.5), titleTop(291)}`.

**Measured:**
- **Card:** 900x470, r 40, border 4 clay, fill card, shadow `0 0 0 12px rgba(203,109,85,.15), 0 14px 30px rgba(203,109,85,.16)`.
- **Disc:** 150 px clay at +372,+46, with a white custom target glyph (rings r 31/19, dot 5.5, stroke 5.5). A lucide
  icon on the disc is 72 px with stroke 2.2 *(unmeasured)*.
- **Eyebrow:** Inter 700 27 px, .096em, clay, centred, top +229.
- **Title:** Newsreader 400 115.5 px, -0.009em, top +291. Measured words: "Launch" at +84 with scaleX .98, "Course"
  at +465 with scaleX 1.012. A `title` string is centred with scaleX .996.
- **Motion:** POP.goal. The left edge reads 86 @+0.117 s, 72 @+0.183 s (peak) and 90 @+0.317 s.

```js
KIT.goalCard(tl, $("s2"), { eyebrow: "ONE BIG GOAL", title: "Ship v2" }, 4.45);
```

## 11. Connector: `KIT.connector(tl, parent, {x,y,w,h,dur}, t)`

**What it is:** a clay line that draws downward from a card to the next element.

**When:** for cause and effect, e.g. goal → Claude, right after the hero settles (+0.35 s).

**Measured:** 6x88 at 537,1112, r 3, clay. It grows by scaleY 0 → 1 from the top over 0.22 s `power1.out` (bottom
1135 @+0.033 s, 1171 @+0.1 s, 1196 @+0.2 s).

```js
KIT.connector(tl, $("s2"), {}, 4.8);
```

## 12. Claude chip: `KIT.claudeChip(tl, parent, {x,y,text}, t)`

**What it is:** a red Claude lockup, with the white spark and a black Newsreader 500 "Claude" wordmark.

**When:** it ends a "Claude does X" chain, 0.22 s after the connector starts.

**Measured:** 284x84 at 398,1200, r 16, `#CF5850`, shadow `0 8 18 rgba(207,88,80,.18)`. Spark 55 px at +10,+14.
Wordmark 62 px at +72,+15 with scaleX 1.1. POP.std.

```js
KIT.claudeChip(tl, $("s2"), {}, 5.02);
```

## 13. Org tree: `KIT.agentTree(tl, parent, o, times)` (+ `treeNode`, `treeLines`, `agentCard`)

**What it is:** one dark "orchestrator" node fans out through grey lines to a row of agent cards. Each agent card has
a pink icon disc, a name, an "AGENT" tag and a small static progress bar.

**When:** for "it runs a whole team of AI agents" or any one-to-many beat, in split layout. Agents pop one per 0.2 s
while the team is named.

**Parameters:** `{node:{label, icon}, agents:[{name, icon, pct, sub}], x0(90), pitch(184), y(560)}`.
`times = {node, lines(node+.317), agents(node+.541), stagger(.2)}`.

**Measured:**
- **Node:** 420x110 at 330,300, r 29, `#1B1D18`, shadow `0 14 28 rgba(30,30,20,.16)`. Clay disc 70 at +22,+20 with
  the users glyph at 69 px. Label Inter 700 35 px white, -0.01em, at +113,+37. POP.node: scale .87 @+0.044 s,
  1.04 @+0.144 s, 1.0 @+0.21 s.
- **Lines:** `#AFAFA6`, 4 px. Trunk x 538, y 409-481. Bar y 478, x 170-910. Drops at each card centre down to y 562.
  They fade in over 0.07 s linear at node+0.317.
- **Agent cards:** 164x250 at x 90+184n, y 560, r 25, border 3, shadow `0 8 20 rgba(70,70,50,.06)`.
  - Pink `#F5EAE4` disc 86 at +38,+29, with a clay lucide icon 40 px, stroke 1.8.
  - Name Inter 700 28.2 px, centred, top +137.5.
  - "AGENT" Inter 600 19 px, .175em, `#7E807C`, top +174.
  - Track 102x8 `#E7E6DB` at +28,+216, with a clay fill of `pct`. The reference values were 58/33/46/20/37 %.
  - POP.agent at node+0.541+0.2n; each slot hides 0.09 s later.
- Other counts are centred by passing `x0`. Four cards use `x0: 182` *(unmeasured)*.

```js
KIT.agentTree(tl, $("s3"), {
  node: { label: "Chief of Staff", icon: "users" },
  agents: [{ name: "Research", icon: "search", pct: .58 }, { name: "Writing", icon: "pen", pct: .33 }]
}, { node: 5.523 });
```

## 14. Goal progress and check rows: `KIT.goalProgress`, `KIT.sectionLabel`, `KIT.checkRows`

**What it is:** the payoff beat. A compact goal card's bar fills and gets a check, while a list of agent rows each
fill a bar and tick in sequence under the grey label "RUNNING IN THE BACKGROUND".

**When:** for "…to get it done", in a takeover. Rows rise on the cut, bars fill, checks land one per ~0.15 s, and the
goal check lands just before the word "done".

**`goalProgress(tl, parent, o, t)`**

Parameters: `{eyebrow("THE GOAL"), words|title, pct(1), barAt(t+.145), barDur(1.15), checkAt(t+1.29)}`.

Measured:
- **Card:** 900x260 at 90,300, r 40, border 4 clay, with the goal halo.
- **Eyebrow:** Inter 700 23 px, .165em, clay, at +44,+42.
- **Serif title:** 73.4 px, -0.01em, at +44,+83. "Launch" scaleX .933, "Course" at +275 with scaleX .97.
- **Bar:** 680x18, r 9, track `#E6E7DB`, at +44,+190. Width 0 → pct over 1.15 s `power2.out`.
- **Check:** 96 px clay disc at +770,+60 with a white check (48 px, stroke 3). Scale .5 → 1 over 0.15 s `power1.out`,
  opacity over 0.125 s.
- **Entrance:** RISE.row at t.

**`sectionLabel(parent, text, {x(92), y(628)})`**

Inter 700 26 px, .124em, `#82827A`, cap height 632-650. Static; it appears with the cut.

**`checkRows(tl, parent, o, t)`**

Parameters: `{rows:[{name, icon, sub("agent"), pct(1)}], y0(680), pitch(134), checkAt[]}`. `t` is when the first row rises.

Measured:
- **Row:** 900x112 at x 90, r 28, border 3, shadow `0 6 16 rgba(70,70,50,.05)`.
- **Contents:**
  - Pink disc 76 at +22,+20, with a clay icon 37 px, stroke 1.7.
  - Name Inter 700 33 px, -0.01em, at +123,+27.
  - "agent" Inter 500 23 px `#7E807C` at +123,+70.
  - Bar 440x12, r 6, `#E8E6E0`, at +330,+51.
  - Check disc 56 at +810,+29 (icon 28, stroke 3).
- **Motion, row n:**
  - Rise (RISE.row) at t+0.0375n.
  - Bar 0 → full at t+0.052+0.06n, over 0.5+0.09n s `power2.out` (fits the reference within 1-2 px every frame).
  - Check POP.check at t+0.61+0.1485n. The exact reference offsets are +0.610/0.752/0.904/1.052/1.204; pass `checkAt`
    to set them, or `null` to leave a row unchecked.

```js
KIT.goalProgress(tl, $("s4"), { title: "Launch Course" }, 7.655);
KIT.sectionLabel($("s4"), "RUNNING IN THE BACKGROUND");
KIT.checkRows(tl, $("s4"), { rows: [{ name: "Research", icon: "search" }, { name: "Writing", icon: "pen" }] }, 7.648);
```

## 15. Serif titles: `KIT.serif(parent, {words|title, size, top, ls, scaleX, width, align, color, italic, html})`

**What it is:** Newsreader set the way the reference's display cut looks. The local Newsreader is the text optical
size, which is wider with heavier hairlines, so each word gets a horizontal squeeze.

**When:** every serif headline (skill titles, goal statements, the hook title).

**Measured:** sizes come from the ascender-to-baseline height and the squeeze from the measured ink width.

| element | size | tracking | scaleX per word |
|---|---|---|---|
| skill title | 93 | -0.01em | .93 (Chief of Staff), .969 (Anatomy) |
| hero goal | 115.5 | -0.009em | .98 / 1.012 |
| compact goal | 73.4 | -0.01em | .933 / .97 |
| hook | 101 | -0.014em | .89 / .986 / 1.01 |

For new text with no measurement, use a single centred line at `scaleX(.95)`. For the style's "one italic clay word"
(STYLE.md), pass `html: 'Vibe <i style="color:#CB6D55">coding</i>'`; Newsreader italic is declared
*(not in this reference)*.

## 16. Dark hook title card: `KIT.titleCard(tl, scene, o)`

**What it is:** the dark opening card. It has a clay "Claude" badge, a white serif title, a grey tracked subtitle,
and a row of clay 3D number cubes.

**When:** for the hook or list intro, on a `.k-scene.k-dark` (`#1B1D18`).

**Parameters:** `{badge("Claude"|false), words|title, size(101), titleTop(285), subtitle, cubes[], cubeX[], cubeY[]}`.

**Measured:**
- **Badge:** 164x48 at 458,222, r 8, `#D9614D`, glow `0 0 18 rgba(217,97,77,.35)`. Spark 29 px, "Claude" Newsreader
  500 36 px `#141414`.
- **Title:** baseline 359.
- **Subtitle:** Inter 600 25 px, .158em, `#A6A69F`, top 395.
- **Cubes:** 151x150. Front face 118x118 at +32 (`#CB6D55`, Newsreader 66 px white numeral), top face 33 deep
  (`#E09685`), side face (`#AB553D`). x 92/278/464/650/836, tops 577/572/568/570/574, a float wave frozen in frame.
- **Static only:** just 3 frames of this card were in the measured window. Its entrance and float motion are
  **not measured**, so the kit adds no motion here. The dotted particle sphere behind the cubes is approximated by a
  faint radial glow.

## 17. Icons: `KIT.icon(name, css, cls)` and `KIT.addIcon(name, viewBox, inner)`

**What it is:** an SVG `<symbol>` sprite, injected once at the start of `<body>`. `color` drives `currentColor`.

- **Measured or refit:** `claude` (spark), `users` (custom 150 grid), `target` (custom 150 grid), `chev`, and the
  lucide glyphs `layers`, `search`, `pen`, `layout`, `code`, `check`. The pen and layout glyphs are 1-3 px larger than
  the reference's.
- **Extra lucide** *(standard paths, not checked against a reference)*: `mail`, `calendar`, `file`, `globe`,
  `database`, `zap`, `terminal`, `folder`, `message`, `clock`, `chart`, `link`, `bot`, `user`, `play`.

## 18. Tokens (`kit.css :root`, mirrored in `KIT.C`)

| token | value | role |
|---|---|---|
| `--k-ivory` | `#EEEEE7` | panel / takeover background |
| `--k-card` | `#FAFCFB` | card fill |
| `--k-edge` | `#DEDED6` | card border (3 px) |
| `--k-ink` | `#151716` | titles / names |
| `--k-clay` | `#CB6D55` | the only accent |
| `--k-dark` | `#1B1D18` | bars, pill, node, hook |
| `--k-grey` | `#82827A` | tracked labels |
| `--k-step-grey` | `#ADAEA4` | inactive step digits |
| `--k-sub-grey` | `#7E807C` | "agent" tags |
| `--k-rail` | `#D5D6CA` | rails, inactive dashes |
| `--k-line` | `#AFAFA6` | tree lines |
| `--k-dash` | `#CECFC7` | placeholders |
| `--k-pink` | `#F5EAE4` | icon discs |
| `--k-track*` | `#E7E6DB` / `#E8E6E0` / `#E6E7DB` | progress tracks |
| `--k-claude-red` | `#CF5850` | Claude chip |
| `--k-cap-bg` | `rgba(15,17,17,.94)` | caption chip |

Shadows and halos (`--k-shadow-card/tile/goal/node/agent/row/chip`, `--k-halo-10/6`) and radii (`--k-r-*`) are listed
there too. Only Inter, Newsreader and JetBrains Mono are used, always written literally so lint can match their `@font-face`.

## 19. `.k-contrast` (opt-in)

The reference's muted greys fail the `hyperframes check` contrast gate (14 errors, 12 warnings on the demo). Adding
`k-contrast` to the root darkens only the flagged elements to the minimum passing values:

| element | default | `.k-contrast` |
|---|---|---|
| inactive step digit | `#ADAEA4` | `#919189` |
| "THIS WEEK" label | `#ACACA8` | `#90908D` |
| last-week cell text | `#9F9E92` | `#696861` |
| this-week cell text | `#C4C4BC` | `#6D6D69` |
| "agent" tags | `#7E807C` | `#727470` |

With it, the demo's check reports contrast 0 errors (2 warnings: the white digit on the clay active step is measured
against the card background). It deviates from the reference, so leave it off for frame-matching.

---

## 20. Beat recipe: one list item, as the reference cut it

All offsets are relative to the cut that starts the beat (seconds) and come from the demo. Reveals lead their word
by 0.03-0.2 s. Cuts land 0-0.23 s after the first word of a phrase starts.

| beat | layout | length | contents (kit calls) | sync to voice |
|---|---|---|---|---|
| A. skill title | split | 2.57 s | `skillCard` (+ stepper, typing) | cut 0.08 s after "Number one is"; card on the cut |
| B. what it is | **full** | 2.87 s | `hud`, `calendarCard` on the cut (NEW +0.36), `placeholder`, `goalCard` +1.80, `connector` +2.15, `claudeChip` +2.37 | cut 0.23 s after "It came out"; NEW 0.07 s before "last week"; goal 0.19 s before "one big goal" |
| C. how it works | split | 2.13 s | `agentTree`: node on the cut, lines +0.32, agents +0.55 + 0.2n | cut 0.04 s after "and it runs"; first agent 0.02 s after "a whole team" |
| D. payoff | **full** | 1.93 s | `goalProgress`, `sectionLabel`, `checkRows` (rows on the cut, bars +0.05, checks +0.61 + 0.15n, goal check +1.30) | cut 0.01 s after "in the background"; goal check 0.035 s before "done" |
| E. next item | split | n/a | `skillCard` with `n+1` (step n is done) | cut 0.18 s after "Number two is" |

The HUD clip spans B-D. The caption rail is at 904 in A, C and E, and at 1423 in B and D.

## 21. Not in this reference

These are not in this reference, so the kit does not fake them:

- **Animated title builds** (word-by-word or line-by-line), **stat count-ups**, **highlight sweeps**, **accent boxes**,
  **karaoke captions**: none occur in this window. reference A's captions are hard swaps with 0 % accent words.
- **Browser or screenshot cards:** banned in the editorial style (STYLE.md). That is the reference C look.
- **HUD slot cables / plug-in strip** (reference B's "CLAUDE CODE 0/4"), **terminal pipeline panel**, **chip grid**,
  **strike-X**, **3D cube takeover motion**: these belong to other editorial references. Look for a sibling kit such
  as `../editorial-vibecoding/` before inventing them.
- **SFX:** the reference mix already contains them (`voice.m4a` is the full mix), so no SFX timings were measured.

## 22. Known gaps (inherited from the replica)

- **Serif glyph shapes:** only the text optical size of Newsreader is local. Ink boxes land within 1-4 px, but the
  letterforms are slightly wider with heavier hairlines. This is the main remaining SSIM loss.
- **Lucide icons:** pen and layout are 1-3 px larger than the reference's; the users glyph is hand-refit.
- **Dark hook:** flat-shaded cubes, and a glow instead of the dotted sphere.
- **Lint warning:** `timeline_track_too_dense` (6 scenes in one file) is the only lint finding on the demo, and it
  is kept because the demo is one standalone file. **Untested:** using the kit inside `<template>` sub-compositions.
  The assembler drops a templated sub-comp's own `<head>` scripts but hoists `<link>`, so load `kit.js` from the host
  page (or inside the template) and build into ids prefixed with the sub-comp id.

## 23. Re-verifying the kit

```bash
# test project: work\replica\editorial-chiefofstaff\kit-test (index.html = demo.html, assets = junction to ..\assets)
cp demo.html <kit-test>/index.html; cp kit.css kit.js <kit-test>/
cd <kit-test> && npx hyperframes@0.8.184 lint                        # expect 0 errors
npx hyperframes@0.8.184 snapshot . --at 0.2,2.7,4.55,6.15,8.3 --no-end -o snaps
python tools\score_replica.py snaps ..\ref\ref.mp4 score --region 0,0,1080,960   # ~0.966
```
