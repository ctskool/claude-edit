# Editorial kit: `editorial-vibecoding`

Reusable components for the **editorial** style, reference B variant: an ivory panel with a drifting grid, a serif title
with one italic clay word, a persistent **power-strip HUD** ("CLAUDE CODE 0/4") that physically receives each item, white
product cards rebuilt in HTML that resolve from skeleton to real, and mono caption chips on the seam. Distilled from
the frame-matched replica of **reference creator B "4 plugin" (Italian), seconds 0-14.5**:
`work\replica\editorial-vibecoding` (index.html + SPEC.md).

Every number here was **measured on the 1080x1920 / 30 fps reference**. The source is 25 fps material upscaled from
540p, so output frames n = 3 (mod 6) repeat the frame before. Numbers marked *(unmeasured)* are defaults for content the
reference did not show. They follow the same system, but no reference frame checks them.

| file | what |
|---|---|
| `kit.css` | `@font-face` (assets/fonts), tokens on `:root`, component classes (`kv-` prefix) |
| `kit.js` | `window.KIT` (also `window.KITVC`): DOM builders, each adding its measured GSAP animation |
| `demo.html` | the whole reference window (14.53 s) rebuilt **only** from kit calls; doubles as the regression test |

**Fidelity (verified 2026-10-23, `kit-test`):**
- **Identical to the replica.** `demo.html` renders pixel-identical to the hand-built replica above the seam on all
  436 frames (difference 0) and on the 30 official `hyperframes snapshot` keyframes.
- **Score against the reference video.** Over the graphics band y 0-960 it scores mean SSIM **0.9736** with colour
  error **1.94**, the same as the replica. The replica's headline 0.9737 / 2.08 is measured over y 0-1016, which also
  includes a static wall band from the footage.
- **Time-shift test.** The demo rebuilt with every time moved +30 frames matches the original frame for frame (146/146
  identical). Every component therefore places exactly wherever you anchor it.
- **Checks.** Lint reports 0 errors and 0 warnings. `hyperframes check` passes: runtime, layout and motion are clean,
  and contrast is 165/165. A second test page builds a new English video from defaults only (`kit-test/variants/generic.html`)
  and passes check too (92/92).

---

## 0. Setup (read first)

1. **Files.** Copy `kit.css` and `kit.js` into the **project root**, next to `index.html`. The project's `assets/`
   folder must sit beside them, because CSS `url()` resolves relative to the stylesheet. The kit needs
   `assets/vendor/gsap.min.js` plus these fonts in `assets/fonts/`, all in the shared set that
   `tools/scaffold_styles.sh` copies:
   - `newsreader-latin-{400,500}-{normal,italic}`
   - `instrument-serif-latin-400-{normal,italic}`
   - `inter-latin-{400,500}-normal`
   - `inter-tight-latin-{500,600,700}-normal`
   - `jetbrains-mono-latin-{400,500,700}-normal`
2. **`<head>` order:** `gsap.min.js` → `<link rel="stylesheet" href="kit.css">` → `<script src="kit.js">`.
3. **Root markup.** The root gets `class="kv-root"`. Inside it, put the face cam and then one graphics wrapper,
   `<div id="gfx" class="kv-gfx kv-soft"></div>`. `kv-soft` is the 0.6 px blur that matches reference B's 540p-upscaled
   export; drop it for a crisp native-1080 look. `KIT.grid` inserts the background as the root's first child.
4. **Build order is z-order.** Builders append to the wrapper you pass, so call them **bottom to top**: title →
   numeral → `cableLayer` → cards → `powerStrip` → `plug` → `captionRail`. Animation-only calls (`stripIntro`,
   `plugIn`, ...) can come in any order.
5. **One paused timeline.** Build everything synchronously, then set `window.__timelines["<composition-id>"] = tl`.
6. **Tween rules.** All kit animation is `set` / `to` / `fromTo` on elements inside the wrapper. Typed characters
   toggle `display` on their own spans. Nothing the kit animates is a `.clip`, so there are no visibility or display
   tweens on clips.
7. **Coexisting with `editorial-chiefofstaff`.** Both kits use `window.KIT`. Load that kit first and keep it as
   `const KITJ = window.KIT;`, then load this one: `window.KIT` and `window.KITVC` now point here. CSS prefixes differ
   (`k-` vs `kv-`), so both stylesheets can coexist.

```html
<head>
  <script src="assets/vendor/gsap.min.js"></script>
  <link rel="stylesheet" href="kit.css" />
  <script src="kit.js"></script>
</head>
<body>
  <div id="root" class="kv-root" data-composition-id="main" data-start="0" data-duration="30" data-width="1080" data-height="1920" data-fps="30">
    <video class="kv-face" src="assets/face_half.mp4" muted playsinline data-start="0" data-duration="30"></video>
    <audio src="assets/voice.m4a" data-start="0" data-duration="30"></audio>
    <div id="gfx" class="kv-gfx kv-soft"></div>
  </div>
  <script>
    const tl = gsap.timeline({ paused: true }), F = KIT.F, gfx = document.getElementById("gfx");
    KIT.grid(tl, document.getElementById("root"), { dur: 30 });
    /* ...builders bottom -> top, then animation calls... */
    window.__timelines = window.__timelines || {};
    window.__timelines["main"] = tl;
  </script>
</body>
```

## 1. Conventions shared by every component

- **Coordinates.** All coordinates are absolute canvas px measured on the reference, and every builder defaults to
  them. Card-internal offsets are relative to the card (940x519 at 70,170). Power-strip internals are in **strip-local**
  px at its phase-2 rest (scale 1).
- **Signature.** The pattern is `KIT.thing(tl, parent, opts, t)`: it builds DOM inside `parent`, adds tweens at `t`
  and returns handles. Pure builders (`powerStrip`, `plug`, `cableLayer`, `captionRail`, `database`, `dashedBox`)
  take no `tl`.
- **Anchors.** Each animated component is measured relative to one **key event**, its anchor, and `t` is when that
  event happens in your video. The kit snaps `t` to the nearest output frame and replays the measured per-frame
  tables from there, so every motion lands on the same frames relative to its anchor. Secondary events (badge pop,
  typing, connect, exit) default to their measured offsets from the anchor, and each one can be overridden.
  The anchor of each component is listed in its section.
- **Time helpers:**
  - `KIT.F(n)` = n/30.
  - `KIT.at(n)` = n/30 − 0.004. This is the replica's "hard set in place from frame n" convention.
  - `KIT.frame(t)` floors a time to its frame.
  - `KIT.clip(k0, k1)` gives `{start, duration}` for a clip.
- **Cadence.** `KIT.cadence = "source"` (the default) keeps the 25 fps holds of reference B's export inside the fast
  per-frame tables. `"smooth"` drops held rows so those motions run at a clean 30 fps. Set it **before** building.
  It is recommended for new videos and only changes the fast motions.
- **Low level.** `KIT.anchor(t, refFrame)`, `KIT.lin` (linear per-frame table) and `KIT.steps` (hard per-frame sets)
  are exposed. `KIT.TABLES` holds every measured table, and `KIT.C` the colours.
- **GSAP ease names.** `powerN` is degree N+1, so `power2` is cubic.

---

## 2. Stage: ivory panel, drifting grid, soft wrapper

**What it is:** a flat ivory `#eeece8` panel (no vignette) with a 60 px grid that drifts slowly for the whole video,
plus the face cam below a hard seam at y 960.

**When:** always, as the base layer.

**Measured:**
- **Grid lines.** A 4 px triangular gradient peaking at `rgba(0,0,0,.021)`, about 5 grey levels below the background,
  with `background-position -1.25px`. Pitch is 60 px on both axes.
- **Drift.** Constant for the whole clip: x(t) = −0.115 + 1.166 t and y(t) = −0.105 + 7.50 t px. Least-squares fit
  over 44 frames, residual under 0.35 px.
- **Soft wrapper.** Every editor graphic, captions included, sits in one wrapper with `blur(0.6px)`. That measured
  +0.002-0.003 SSIM on every frame type, with sigma 0.6-0.9 the optimum. The grid stays outside the wrapper.
- **Face cam.** y 960-1920. In reference B's crop the face starts at 1016 with a 56 px static wall band above it.

**Parameters:** `KIT.grid(tl, root, {dur, vx(1.166), vy(7.5), x0(-0.115), y0(-0.105)})`. Videos long enough that the
offset would leave the 60 px tile margin wrap it automatically (the grid is periodic).

```js
KIT.grid(tl, document.getElementById("root"), { dur: 30 });
```

## 3. Serif title: `KIT.serifTitle(tl, host, o, t)` (alias `titleBuild`)

**What it is:** the opening headline. A serif title has one italic clay word ("*Vibe* coding") over a grey subline
("con Claude Code"). It blurs in, then both lines share one slow push-in, then they hard-cut out when the HUD docks.

**When:** for the hook, on the topic words. It enters **0.05 s after the italic word is spoken** ("vibe" 0.78 s →
title 0.83 s), and the subline follows 1.07 s later on the last word of the phrase.

**Anchor `t`:** entrance start, reference frame 25 (0.833 s).

**Parameters:** `{text:"*Vibe* coding" | svg, sub:"con Claude Code" | subSvg, top(190), subTop(314), titleY(-12),
subAt(t+1.067), pushAt(t+0.817), pushRate(0.0078/s), out(t+3.5; null = never), originX(546.5), originY(281)}`.
`svg` / `subSvg` take traced `<path>` markup for a 1080x130 / 1080x40 box; `demo.html` shows them.

**Measured:**
- **Ink boxes at 3.0 s:**

  | element | x | y | colour |
  |---|---|---|---|
  | "Vibe" | 292-469 | 188-269 | clay `#c9532d` |
  | "coding" | 495-803 | 189-292 (baseline 268) | ink `#151513` |
  | subline | 424-655 | 318-340 | `#56524d` traced, `#7b7772` in Inter |

- **Entrance, per frame** (opacity / scale / y / blur px), origin 50.6% 94%:

  | frame | opacity | scale | y | blur |
  |---|---|---|---|---|
  | 25 | 0 | .85 | 9 | 2.5 |
  | 26-27 (25 fps hold) | .22 | .857 | 8.4 | 2 |
  | 28 | .5 | .92 | 5 | .6 |
  | 29 | .8 | .963 | 2.2 | 0 |
  | 30 | .95 | .985 | .8 | |
  | 31 | 1 | 1 | −.5 | |
  | 33 | | 1.008 | −1.5 | |
  | 36 | | 1.003 | −1 | |
  | 40 | | 1 | 0 | |

- **Subline, per frame** (opacity / y), from reference frame 57:

  | frame | 57 | 58 | 59 | 60 | 61 | 62 | 66 |
  |---|---|---|---|---|---|---|---|
  | opacity | 0 | .12 | .51 | .7 | .9 | .97 | 1 |
  | y | 10 | 9 | 5.5 | 3.2 | 1.6 | .5 | 0 |

- **Push-in:** title and subline scale about (546.5, 281) from 1.65 s at +0.78 %/s. Ink width goes from 507.5 to
  518 px by 4.3 s. Hard cut at 4.333 s.
- **Font build (`text`):** neither local serif is the reference's display serif, so word mode is a calibrated
  stand-in.
  - Italic word: Instrument Serif italic 108 px, tracking 6.5 px, +0.8 px stroke.
  - Other words: Newsreader 400 107 px, tracking 0.6 px, +0.5 px stroke.
  - Subline: Inter 400 30.3 px, tracking −1 px.
  - Result: every ink box lands within 1 px of the reference. Title-crop SSIM is 0.70, against 0.93 for the traced
    outlines; the remaining gap is letterform shape.

```js
KIT.serifTitle(tl, gfx, { text: "*Ship* faster", sub: "with Claude Code" }, F(25));
```

## 4. Power-strip HUD: `KIT.powerStrip(host, o)` (alias `hud`)

**What it is:** the signature device of this reference. A white power strip carries the Claude spark, a "CLAUDE CODE"
label, an n/N counter, a status dot and N sockets. It is the list's progress bar made physical: each item named
becomes a plug that drops into the next socket.

**When:** from frame 0 for a "N tools / plugins / steps" video. It sits **big and high** while the hook talks about
the list, **docks** to the bottom of the panel when item 1 starts, and receives one plug per item.

**Parameters:** `{label("CLAUDE CODE"), sockets(4), total(sockets), count(0), x(centred), y(783)}`. It returns
`S = {el, pop, pill, count, nums[], dots{gray,red,green}, socks, sockets[{sock,outl,qbox,cx}], value}`. Other socket
counts widen the strip by 120 px per socket *(unmeasured)*.

**Measured (strip-local px, rest scale 1):**
- **Body:** 696x114 at (192, 783), r 22, white. Top hairline 1.6 px `#dcdad6`, sides 1 px `#e6e4e0`. Shadow
  `0 30px 40px rgba(0,0,0,.10), 0 2px 12px rgba(0,0,0,.045)`, fitted to the reference column below the body.
- **Sockets:** 94x86, r 16, `#f0eeea`, 1.5 px `#dad8d4`, with an inset shadow from the top. Centres sit at local
  262 + 120 i. Slots are 9.4x30 `#393735` at +27.3 / +55.4, y +27.5. The ground dot is 9.6 px `#d1cec8` at
  (40.7, 67.7).
- **Label and spark:** label JetBrains Mono 700 16.4 px, tracking 1.4, `#4a423c`, at (61, 27.9). Claude spark 23 px
  `#c45f3b` at (25.5, 24.5).
- **Counter:** JetBrains Mono 500 42 px + 0.5 px stroke at (27.4, 59). The empty "0" is `#7b7a78`; lit digits and
  "/4" are `#121213`.
- **Status dot:** 16 px at (150, 72).
  - grey `#d0cec9`
  - red: radial `#ad1f2e`, 2.6 px `#efc3c4` halo
  - green: `#2f9a68` with a 3.5 px halo

### 4a. `KIT.stripIntro(tl, S, o, t)`: phase 1 + pop-in. Anchor: first frame (0 in the reference).
- **Phase 1:** centre y 668 (`lift −172`), scale 1.355 growing 0.0099/s until the dock.
- **Pop-in:** width ratio per frame.

  | frame | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 9 | 12 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | ratio | .906 | .94 | .966 | .967 | .986 | .998 | 1.006 | 1.0099 | 1.008 | 1 |

### 4b. `KIT.stripBlink(tl, S, [[on, off], ...])`: red dot. Pass frame pairs.
On "Non" the reference blinks on frames 5-9 and 11-15. The last 2 frames of each blink sit at 0.75.

### 4c. `KIT.stripNo(tl, S, t, {scale:1.38})`: the "no" head-shake. Anchor: reference frame 70.
On the second "non" the counter shakes like a head saying no, while the red dot double-blinks.

| frame | 71 | 72 | 73 | 74 | 75 | 76 | 77 | 78 | 79 | 80 | 81 | 82 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| counter x (frame px) | −4.2 | −11.1 | +4.9 | +11 | +11 | −5 | −5.9 | +4.2 | +1.3 | −.5 | | 0 |
| red dot opacity | .65 | 1 | 1 | .9 | .9 | 0 | .3 | 1 | 1 | .93 | .93 | 0 |

The x offsets are divided by the strip scale. Use it for any "not yet / don't" word.

### 4d. `KIT.stripPill(tl, S, tOn, tOff)` (alias `highlightPill`): label highlight.
A clay pill (`#f9ddd2`, 2.2 px `#d39a8e` border, 2.5 px ring) behind spark and label. It fades in linearly over
0.09 s, **0.11 s after "Claude" is spoken**. At `tOff` (the dock) it reads .45 for one frame, then it is gone.

### 4e. `KIT.questionBoxes(tl, S, o, t)`: dashed "?" placeholders. Anchor: reference frame 84 (2.8 s).
On "installato questi 4 plugin", one dashed box per socket floats above it.
- **Box:** 102x147 frame px at rest, top 392. The body has a white 50 % fill and a `#d6937f` 2.95 stroke, dash
  5.82/2.95, offset 4.3. The handle is a separate unfilled bracket (dash offset 5.2). The "?" is Newsreader 400 47 px
  `#9c4a35`, and the whole box has a 0.35 px blur.
- **Pop:** stepped per frame, origin 50% 10%, first visible on frames 85 / 86 / 89 / 90. Each goes .7 → .9-.98 → a
  1.03-1.045 peak → 1, about 11 frames.
- **Float and dip:** the box tops drift up 13 px (392 → 379) over frames 99-118. On the end of "plugin" a dip wave
  runs +52 px (379 → 432 → 384) over 7 frames, one 25 fps frame later per box. Then a 3-frame fade (.85, .12, 0).
- **Options:** `{floatAt, outAt, tops[]}`.

### 4f. `KIT.socketOutlines(tl, S, o, t)`: dashed outlines lock onto the sockets. Anchor: reference frame 108 (3.6 s), on "4 plugin".
- **Outline:** rect 105.2x95.9, r 20, `#ad5d4a` 2.9, dash 5.72/2.96, offset −2.5, white 1.5 px halo. **Dash phase
  matters more than 1 px of geometry:** matching it raised the 4.0 s keyframe from 0.942 to 0.958.
- **Onset:** pale first, then solid.

  | socket | onset frames (opacity) |
  |---|---|
  | 1 | 108 .3 → 109 1 |
  | 2 | 110 .3 → 112 .6 → 113 1 |
  | 3 | 113 .25 → 114 .6 → 115 1 |
  | 4 | 115 .1 → 116 .35 → 118 1 |

- **Size:** all four share one table. They start at 1.06 and settle to 1.0 by frame 119, then swell back to 1.06
  over frames 124-128, just before the dock. Exit: .3, then 0.

### 4g. `KIT.stripDock(tl, S, o, t)`: phase 1 → rest. Anchor: reference frame 131 (4.367 s), 0.13 s after "Il primo".
The strip flies down to y 783 at scale 1 in 13 frames.

| frame | 132 | 133 | 134 | 135 | 136 | 137 | 138 | 139 | 140 | 141 | 142 | 143 | 144 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| progress | .014 | .057 | .129 | .129 | .254 | .44 | .656 | .81 | .91 | .91 | .968 | .989 | 1 |

### 4h. `KIT.socketWait(tl, S, i, t, until)`: the next free socket breathes.
- **Outline:** rect 106x96, r 20, `#ab5b47`, dash 6.2/2.5, offset −2.85. It fades in over 0.08 s at `t` (4.64 s,
  right after the dock).
- **Breathing:** scale 1 → 1.056 and stroke 2.45 → 3.05 px on a 20.5-frame period.
- **End:** hidden from `until` on; pass the seat frame + 1.

```js
const strip = KIT.powerStrip(gfx, { label: "CLAUDE CODE", sockets: 4 });
KIT.stripIntro(tl, strip, {}, 0);
KIT.stripBlink(tl, strip, [[5, 10], [11, 16]]);
KIT.stripNo(tl, strip, F(70));
KIT.stripPill(tl, strip, 1.73, F(132));
KIT.questionBoxes(tl, strip, {}, F(84));
KIT.socketOutlines(tl, strip, {}, F(108));
KIT.stripDock(tl, strip, {}, F(131));
KIT.socketWait(tl, strip, 0, 4.64, F(200));
```

## 5. Plug-in: `KIT.cableLayer`, `KIT.plug`, `KIT.plugIn(tl, S, P, layer, o, t)` (alias `cablePlug`), `KIT.statPop`

**What it is:** the item "connects". A black plug carrying the product's mark descends on a cable from the card above,
bobs, drops and seats with squash. The strip jolts, a clay ring and an expanding ping mark the socket, the counter
digit pops (0/4 → 1/4) and the status dot turns green.

**When:** on the verb of connection ("che **collega** Claude"). The seat lands mid-word, and the card's progress line
fills into the same frame. Use one plug per item, into sockets 0, 1, 2 and so on.

**Anchor `t`:** the SEAT frame, reference frame 199 (6.633 s).

**Build:**
- `KIT.cableLayer(gfx)` **before** the cards, because the cable runs under them.
- `KIT.plug(gfx, {socket, icon, iconColor})` **after** the strip.

**Parameters:** `plugIn` takes `{count(S.value+1), green(true), seatY(775), fromX(462), fromY(694), cableAt, anchorAt,
ringOut}`. For a second plug in the same video, pass `green:false`.

**Measured:**
- **Plug:**
  - body 72x87, r 11, `#212121`, with shadow
  - neck 27x17
  - white tile 50 px (r 11) holding the 28x30 mark
  - two prongs 6x13 `#9b9893`, hidden at the seat
  - seated top y 775; x 416-488 for socket 1, +120 px per socket
- **Ghost** (opacity / scale, origin at the body bottom):

  | frame | 180 | 181 | 182-183 | 184 | 185 | 186 | 187-189 | 190 |
  |---|---|---|---|---|---|---|---|---|
  | opacity | 0 | .25 | .72 | 1 | | | | |
  | scale | .7 | .75 | .86-.87 | .97 | 1.03 | 1.055 | 1.03 | 1 |

- **Vertical path** (y offset from the seat / scaleY):
  1. From −0.613 s it hovers at −118 to −121 with a small bob.
  2. Drop: −97 (−0.167 s), −79 (1.03), −53 (1.035), −20.5 (1.04, frame 198).
  3. Frame 199 seat: +3 at .96, then two frames at +1 / .89 (squash).
  4. Bounce: −3 / .92, 0 / .97, +2 / 1.02, −1 / .99, rest by frame 206.
- **Cable:** 7.5 px `#222`. It starts from a 30.5x12.1 anchor block `#2c2c2c` on the card's bottom edge at (462, 694).
  The bezier control points sit at 45 % of the drop. Visible from seat −0.183 s.
- **Ring:** 112x101.5, r 22, 3.2 px `#b4583d` with glow. Opacity .25 / .55 / .7 / .85 / 1 over frames 199-206. It
  fades over 0.26 s `power1.in` from seat +0.687 s.
- **Ping:** 110x100, 2 px `rgba(225,120,95,.55)`. Opacity/scale go .5/1.0 → .55/1.08 → .45/1.2 → .3/1.32 →
  .12/1.4 → 0/1.44 over frames 199-208.
- **Counter digit (`KIT.statPop`):** the new digit shows on the seat frame at scale 1.5, then 1.3, 1.3, 1.15, 1.07,
  1 per frame, origin 50% 55%.
- **Green dot:** 1-frame fade at seat +2.33 frames.
- **Strip jolt:** strip y per frame is +3, +2, +2, −2, +1, +2, 0, then +1 and 0 at frames 208-209.

```js
const cables = KIT.cableLayer(gfx);          // before the cards
/* ...cards, strip... */
const plug = KIT.plug(gfx, { socket: 0 });   // after the strip
KIT.plugIn(tl, strip, plug, cables, {}, F(199));
```

## 6. Big pale numeral: `KIT.bigNumeral(tl, host, {n, outAt}, t)` (alias `statNumeral`)

**What it is:** a huge thin serif numeral in pale clay `#e1bfaf`, with a light rim, behind where the next card lands.
It announces "item n".

**When:** on "Il **primo**", one frame after the dock starts. The card covers it 0.5 s later.

**Anchor `t`:** reference frame 132 (4.4 s).

**Measured:**
- **The "1":** a traced SVG path, box x 446-647, y 97-480, with a 2.5 px light rim on the right.
- **Entrance** (opacity / scale / y about (561, 479)):

  | frame | 132 | 133 | 134 | 135 | 136 | 137 | 138 | 139-141 | 142 | 144 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | opacity | .1 | .3 | .65 | .66 | .88 | .95 | 1 | | | |
  | scale | .9 | .93 | .95 | .96 | .976 | .99 | 1.008 | 1.01 | 1.005 | 1 |
  | y | 18 | 14 | 10 | 8 | 5 | 1 | 0 | | | |

- **Fade:** .75 / .1 / 0 over frames 148-150.
- **Other digits:** any other `n` is set in Newsreader 400 560 px in the same box *(unmeasured)*.

```js
KIT.bigNumeral(tl, gfx, { n: 1 }, F(132));
```

## 7. Plugin card: `KIT.pluginCard(tl, host, o, t)` (alias `skillCard`)

**What it is:** the item's card. A white card holds a skeleton (dashed "?" tile, grey bars) that resolves into the
real product:
- the logo tile pops in tilted, and the name types
- an "ufficiale" badge pops and a marketplace pill rises
- an inner row "Claude Code ---- in attesa" shows the connection; its progress line fills while the plug drops and
  the status flips to "collegato" on the seat frame
- the content then lifts out for the diagram (section 8)

**When:**
- the card arrives on the item name ("il **plugin** ufficiale", +0.04 s after the word)
- the badge lands on "ufficiale"
- the logo pops 0.07 s after the product name starts
- the connection completes on the connect verb

**Anchor `t`:** card arrival, reference frame 147 (4.9 s).

**Parameters:** `{label("PLUGIN"), name("Supabase"), icon{path,color,bg}, badge("ufficiale"), badgeW,
market("Marketplace di Anthropic"), marketW, marketLogo, rowName("Claude Code"), status["in attesa","collegato"],
typeStep(.04), x, y, badgeAt, marketAt, iconAt, typeAt, connectAt(=seat), exitAt, growAt, until, outAt}`.
Pill widths are auto-estimated from the text length when the text differs from the reference *(unmeasured)*.

**Measured (card-local px):**
- **Card:** 940x519 at (70, 170), r 24, `#fff`. Shadow `0 16px 36px rgba(70,55,40,.09), 0 2px 6px rgba(70,55,40,.06)`.
  It grows +0.52 %/s about its bottom edge from 5.1 s until the cut.
- **Arrival:** opacity per frame .33 / .53 / .68 / .82 / .97 / 1 (frames 148-153), while rising 30 → 25 → 17.5 → 11.5
  → 6.5 → 3 → 3 → 1.8 → .8 → 0 px.
- **Eyebrow:** "PLUGIN" Inter Tight 600 23.4 px, tracking 1.4, `#6e6b66`, at (44.6, 41.8).
- **Skeleton:**
  - tile 176x177, r 38, `#f3f2ef`, dashed `#c9c6c1` 2.4 (6.2/2.45), "?" Newsreader 500 110 px `#cfccc7`
  - title bar 299x34 `#d0d1c3`, darkening from `#d9d8cd` over 5.07-5.2 s
  - sub bar 179x22 `#e5e1dc`
  - text bars 518 and 379 x 12 `#e2deda`
- **Logo tile:** 175 px, r 39.5, `#1a1a1a`, shadow `0 8px 16px rgba(0,0,0,.2)`, mark 91x97.6.
  Pop per frame (opacity / scale / rotation):

  | frame | 173 | 174 | 175 | 176-177 | 178 | 179 | 180-181 | 182-183 | 184 | 185 | 186 | 187 |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|
  | opacity | 0 | .45 | .7 | .88 | 1 | | | | | | | |
  | scale | .7 | .8 | .867 | .95 | 1 | 1.036 | 1.05 | 1.04 | 1.027 | 1.011 | 1.006 | 1 |
  | rotation | −14° | −12° | −4.7° | −1.9° | 0 | +1° | +1.5° | +1.2° | +.8° | 0 | | |

- **Name:** Inter Tight 700 66 px, tracking −1.1, at (250.5, 102.9). It types at **0.04 s/char**, one character per
  25 fps frame, from 5.825 s.
- **Badge:** pill 113x35.6, 2 px `#bd9b95`, text `#a2583b` 600. Pop per frame (opacity / scale):
  frame 158 .55/.92 (held one frame), 160 1/1, 161-163 1.03, 165 1.01, 166 1.
- **Marketplace pill:** 299x40.6 at (600.8, 29), `#f2f0ed`, Anthropic mark. It rises 8 px while fading in:

  | frame | 162 | 163 | 164-165 | 166 | 168 | 171 | 175 |
  |---|---|---|---|---|---|---|---|
  | opacity | .3 | .6 | .85 | .93 | .97 | .99 | 1 |
  | rise (px) | 7 | 5.5 | 4 | 2.5 | 1.2 | .5 | 0 |

- **Inner row:** 852.3x129.1, r 18, `#f7f5f2`, 1.2 px `#e8e5e0`. Claude tile 56 px `#da6a43`. "Claude Code" 28.65 px
  700. A grey dashed line (`#cbc8c3`, 10.7/9.46) runs under a clay progress line, 363x3.4 `#bd5f3e`.
- **Progress:** fills per frame .016 .082 .172 .262 .376 .376 .488 .681 .877 1, ending on the seat frame.
- **Status:** "in attesa" (120x37.7, `#d4d3cf` border) is replaced on the seat frame by "collegato" (127.8x38.6,
  `#b6c6b9` border, text `#2e5a46`, fill `#f6fef9`). The new pill shows at scaleX .94 anchored right, then .97, then 1.
- **Content exit** (opacity / y) over frames 208-212: .94/−1.5, .79/−5.5, .5/−13, .06/−20, 0/−22.

```js
const card = KIT.pluginCard(tl, gfx, { name: "GitHub", icon: { path: GITHUB_PATH, color: "#fff", bg: "#181717" },
  badge: "official", market: "Anthropic Marketplace", status: ["waiting", "connected"] }, F(147));
```

## 8. Flow diagram: `KIT.flowDiagram(tl, C, o, t)` + `KIT.database(layer, o)`

**What it is:** "Claude talks to your database", built inside the plugin card once its content has lifted out.
- a real-3D clay cube carries the Claude spark and slowly yaws
- a clay line grows right, and five diamond packets travel along it
- a dashed database placeholder turns solid, growing from its base, with the product mark and "il tuo database"

**When:** right after the connection, on the phrase that names the relationship ("direttamente al tuo
**database**"). The solid database lands on "database", +0.01 s.

**Anchor `t`:** cube appears, reference frame 212 (7.067 s). `C` is the plugin card handle.

**Parameters:** `{label("Claude"), labelAt, lineAt(t+0.333), packets([21,29,36,41,47] frames after t), dbAt(t+0.6),
dbSolidAt(t+1.2), dbLabelAt, until(card cut), db{label, icon, iconColor}}`.

**Measured (card-local px):**
- **Cube:** fitted per frame to 7 visible vertices (rms 0.3-1 px).
  - Projection: orthographic with weak perspective 0.019, pitch 24°.
  - Yaw: linear, −45.3° → −21.7° (+0.4533°/frame).
  - Size: 70.7 frame px.
  - Faces: top `#e6927b`, front `#d45d3f`, side `#ae462c`. The spark sits on the front face via that face's affine
    matrix.
  - Pop (size multiplier) per frame:

    | frame | 212-213 | 214 | 215 | 216 | 217 | 218 | 219 | 220 | 221 | 222 | 223 | 224 |
    |---|---|---|---|---|---|---|---|---|---|---|---|---|
    | size | .70 | .86 | .96 | 1.025 | 1.045 | 1.053 | 1.04 | 1.03 | 1.02 | 1.012 | 1.006 | 1.002 |

    Opacity goes .45 / .75 / .92 / 1, and the cube rises about 15 px while it grows.
- **Label:** "Claude" Inter Tight 500 25 px `#55524e`, rising 5 px over 0.15 s from 7.19 s.
- **Line:** 3 px `#ae5c48` with rounded caps. It grows from a dot to 284.5 px over 11 frames:
  .035 .09 .09 .212 .424 .681 .847 .941 .941 .983 1.
- **Packets:** diamonds 15.6 px `#d65a37` with a 4 px halo. They travel 286 px on the **25 fps content clock**, with
  progress per content frame .003 .007 .028 .069 .135 .231 .369 .545 .703 .82 .9 .952 .983 .997 1. Packets 2-5
  pre-show at 40 % one frame early.
- **Database:**
  - cylinder: cx 740.2, rx 90.2, ry 30.4, top 140, bottom 309.6; 3.2 px `#de9a80`, top fill `#faf8f4`; bands at
    196.5 and 253.2
  - dashed placeholder: silhouette `#bf8f88` 2.5 (5.6/3.27), opacity .35 → .8 → 1 while scaling .97 → 1
  - solid: grows from its base (740.8, 341): .35/.6 → .6/.75 → 1/.9 → .975 → 1.02 → 1.04 (2 frames) → 1.02 → 1
  - bolt 50x52
  - label Inter Tight 500 25.4 px `#55534f`, rising 3.5 px from 8.42 s

```js
KIT.flowDiagram(tl, card, { label: "Claude", db: { label: "your repo", icon: GITHUB_PATH, iconColor: "#181717" } }, F(212));
```

## 9. Tools card: `KIT.toolsCard(tl, host, o, t)` + `KIT.toolRow(tl, B, T, i, tIn)` (alias `checkRow`)

**What it is:** "what you can do with it". A card cuts in with a header (mark, product name, green "collegato" pill,
tracked "STRUMENTI") and the solid database on the right. N tool rows enter as skeletons, then each activates in turn:
1. clay border and pink icon tile
2. mono name typed
3. description typed with a caret, or popped in for short results
4. a connector drawn to the database
5. a packet travelling DB → row
6. a green check

**When:** the card arrives on the next sentence ("**Così** puoi lanciare...", +0.013 s). Each row activates
**0.08-0.21 s after its verb** ("query", "scrivere", "generarti", "controlli"), about one row per 1.2 s.

**Anchor `t`:** card cut-in (8.833 s; the card appears complete with its database).

**Parameters:**
- **card:** `{name, icon, status("collegato"), section("STRUMENTI"), pillX, sectionX, rows[], rowsAt(t−0.008),
  stagger(0.072), headerAt(t+0.122), until, outAt, db}`
- **row:** `{name, desc, icon, badge("TS"), mode("type"|"pop"), at, swapAt, nameAt, nameStep(.016) | nameFrames,
  descAt(at+.3), descStep(.024) | descFrames, caretAt, popAt(at+.55), pop("a"|"b"|rows), connAt(at+.18),
  connDur(.09), connEase, bend, packetAt(at+.3), packetHold(.07), checkAt(desc end+.05), bars}`

**Measured (card-local px):**
- **Card:** grows +0.45 %/s, y +0.8.
- **Header:** mark 31 px at (36.4, 29). Name Inter Tight 700 28.5 px. Pill 115.7x32.5, 2 px `#9cc0b4`, text `#1a5240`
  500 19.5 px. Section word 600 22.4 px, tracking 2.3, `#5c5954`. It fades in over 0.15 s `power1.out` at t+0.122.
- **Rows:** 540x91, r 14, at x 30, y 86 + 104 i.
  - **Entrance:** blur 6 → 0 and opacity over 0.26 s `power1.out`, y 25 → 0 over 0.28 s `power2.out`, staggered
    0.072 s.
  - **Skeleton:** `#f8f7f5`, 2 px `#ebe8e3`. Bars `#d0cfc3` (19 px) and `#e2deda` (14 px); tile `#e3ded9`.
  - **Active:** white, 2 px `#d99a84` border, shadow `0 6px 14px rgba(235,169,144,.18)`. The pink tile is `#fde0d5`
    with a 2.2 px `#934b38` icon. Bars and tile cross-fade over about 2.5 frames.
- **Name:** JetBrains Mono 700 23.03 px `#121212` at (91.5, 19). Measured typing runs about 0.013-0.018 s/char
  (`execute_sql` over frames 293-298).
- **Description:**
  - typed: JetBrains Mono 400 18.9 px `#55524e` at 0.024 s/char, with a clay caret (2.5 px `#d9663f`, 4 px gap) that
    stays 0.46 s after the last character
  - popped (short results such as "types.ts generato"): scale .76-.8 → 1 while rising 5-6 px over 5 frames (tables
    `a` and `b`)
  - the TS badge is 19.6x20.5 `#2f6db6`
- **Connector:** 3.2 px `#d99786`, drawn with its real path length. Bezier from the row's right edge (570, centre) to
  the database edge (649; y 177.6 / 213.5 / 249.5 / 285.2). Rows 3-4 bend up 5 and 9 px.
- **Packet:** circle r 3 → 7 `#d9603b` with a soft halo, at `packetAt`. It travels DB → row over 0.24 s
  (`power1.inOut` in 12 linear steps) after a 0.13 s pause, then hides 0.07 s later.
- **Check:** 39.5 px disc `#3d996a` with a white tick (stroke 3), replacing a dashed `#cfccc7` circle. Scale and
  opacity per half-frame:

  | half-frame | 0 | .5 | 1 | 1.5 | 2.5 | 3.5-5.5 | 6.5 | 7.5 | 8.5 |
  |---|---|---|---|---|---|---|---|---|---|
  | scale | .5 | .63 | .85 | 1.0 | 1.1 | 1.15 | 1.1 | 1.05 | 1 |
  | opacity | 0 | .5 | .8 | 1 | | | | | |

```js
KIT.toolsCard(tl, gfx, { name: "GitHub", status: "connected", section: "TOOLS", outAt: KIT.at(431), rows: [
  { name: "create_pull_request", desc: "feat: login page", icon: "zap", at: 9.73 },
  { name: "search_code", desc: "3 matches in src/", icon: "file", mode: "pop", at: 11.9 }
] }, 8.833);
```

## 10. Browser card: `KIT.browserCard(tl, host, o, t)`

**What it is:** the next beat's rebuilt product UI: a browser mock with traffic lights, a URL bar with the product mark
and typed URL, a sidebar, a table and a green CTA ("Apri"). It is a **hard cut-in, not a fade**, and it sits above the
cable anchor.

**When:** the sentence after the tool list. It cuts 0.19 s after the previous sentence ends.

**Anchor `t`:** reference frame 431 (14.367 s).

**Parameters:** `{url("sup"), urlFrames([[2,1],[3,3]]), urlStep(1 frame/char after the measured ones, unmeasured),
button("Apri"), rows(5), icon}`.

**Measured:**
- **Box:** (72.8, 176.2), 935.5x518.
- **Entrance** (y / scale per frame): 431 24/.981, 432 12.3/.991, 433 5/.998, 434 0/1.
- **URL typing:** "s" on frame 433, "sup" on frame 434.
- **Interior:**
  - URL bar 615x35, r 18, `#f0eeeb`
  - sidebar 83 px `#f7f5f1` with five 32 px squares
  - table 781x337 with a `#f6f4f1` header and 5 rows at a 56 px pitch
  - CTA 85x42, r 8, `#3ecf8e`, text `#0f3d27` 700 22 px

## 11. Captions: `KIT.captionRail`, `KIT.captions`, `KIT.captionChip`, `KIT.chunkWords`

**What it is:** a dark mono chip on the seam with a **hard swap plus a tiny pop**. One word per sentence can carry the
clay accent, which turns on 0.1 s after the chip appears.

**When:** always, with a chip on every frame and no gaps in this window. Create the rail **last** inside the wrapper,
so it sits on top.

**Measured:**
- **Chip:**
  - JetBrains Mono 700 46 px, tracking 0.45, UPPERCASE, `#fafcfc` on `#1c1d1c`
  - 78.15 px tall at y 921.05-999.2 (centred on the seam), r 9, padding 25.3 / 26.3, centred on x 540
  - shadow `0 0 3px 14px rgba(0,0,0,.022), 0 8px 16px rgba(0,0,0,.09)`
  - `will-change: transform` forces grayscale AA (caption chroma drops from 125 to 3)
- **Pop:** the first frame is at .94-.976 of the final width (sometimes held 2 frames by the 25 fps cadence), the
  next is .99, then 1. The default is `[0.945, 0.99]`.
- **Accent:** `*SUPABASE*` turns `#ec987f` 3 frames after the chip.
- **Chunking:** up to **3 words**. **Any** punctuation closes a chip (". , ?"). Swaps land on average +0.12 s after
  Whisper's word start.
  - On this transcript `chunkWords` reproduces the editor's chunk boundaries for the first 15 chips. Its swap frames
    land within ±5 frames of the editor's (mean 2.2), about the precision of Whisper's word starts.
  - The last three chips shift because Whisper dropped "i" in "generarti **i** tipi", and the editor spelled "4" as
    "QUATTRO". Fix transcript errors before chunking, or pass explicit chips as `demo.html` does.

**Parameters:**
- `captions(tl, rail, [{text, k | t, pop, k1}], {end, hotColor, hotDelay(3), pop})`: a chip stays until the next one,
  and the last chip stays to `end`.
- `chunkWords(words, {max:3, offset:0.12})` returns `[{text, k}]`.

```js
const rail = KIT.captionRail(gfx);
const chips = KIT.chunkWords(words);                                  // words.json [{text,start,end}]
chips[8].text = "DI *SUPABASE*";                                       // one accent word per sentence, at most
KIT.captions(tl, rail, chips, { end: 30 });
```

## 12. Dashed outline: `KIT.dashedBox(parent, o)` (alias `outlineBox`) + `KIT.DASH` presets

**What it is:** this reference's core motif. Every "not there yet" state is a dashed outline: sockets waiting, "?"
boxes, skeleton tiles, the database placeholder, empty check circles. Use it to build new placeholder beats in the
same language.

**Parameters:** `{x, y, w, h, preset, stroke, width, dash, offset, r, fill, opacity}`. With `h <= 2*width` it draws a
dashed line.

**Measured presets:**

| preset | stroke | width | dash / gap | offset | r |
|---|---|---|---|---|---|
| `socket` | `#ad5d4a` | 2.9 | 5.72 / 2.96 | −2.5 | 20 |
| `wait` | `#ab5b47` | 2.7 | 6.2 / 2.5 | −2.85 | 20 |
| `box` | `#d6937f` | 2.95 | 5.82 / 2.95 | 4.3 | 13.3 (white 50 % fill) |
| `skeleton` | `#c9c6c1` | 2.4 | 6.2 / 2.45 | | 38 (`#f3f2ef` fill) |
| `db` | `#bf8f88` | 2.5 | 5.6 / 3.27 | | |
| `line` | `#cbc8c3` | 3 | 10.7 / 9.46 | | |
| `check` | `#cfccc7` | 1.6 | 4 / 3.2 | | circle |

**Note:** match the dash phase (`offset`) when a box must sit on reference geometry. In this reference that mattered
more than 1 px of position.

## 13. Helpers

- `KIT.typeChars(tl, node, text, t, step)` (alias `terminalType`): one span per character, switched on at
  t + i·step. It returns the time of the last character. The reference cadence is 0.04 s/char for a product name and
  0.024 s/char for mono descriptions.
- `KIT.cut(tl, node, t)`: a hard cut. Cards swap this way: card A goes out at 8.833 and card B is in at 8.833.
- `KIT.statPop(tl, digitNode, t)`: the counter digit pop from section 5.
- `KIT.defs()`: installs the shared Claude spark (`<defs><path id="kv-claude">`, used through `<use>`). Builders call
  it themselves.
- `KIT.PATHS` holds `claude`, `bolt` (Supabase) and `anthropic`. `KIT.TOOL_ICONS` holds the four measured line icons
  `terminal`, `layers`, `braces` and `shield`, which are hand-drawn approximations. It also holds six lucide icons:
  `database`, `key`, `search`, `file`, `globe` and `zap` *(unmeasured)*.

---

## 14. Tokens (`kit.css :root`, mirrored in `KIT.C`)

| token | value | role |
|---|---|---|
| `--kv-bg` | `#eeece8` | ivory panel (reference B; reference A's is `#EEEEE7`) |
| `--kv-card` | `#ffffff` | every card |
| `--kv-ink` / `--kv-ink-title` | `#1e1d1b` / `#151513` | text / serif title ink word |
| `--kv-ink-sub` | `#56524d` | subline (traced) |
| `--kv-ink-label` / `--kv-ink-desc` | `#6e6b66` / `#55524e` | eyebrows / descriptions and diagram labels |
| `--kv-clay-title` | `#c9532d` | the italic clay word |
| `--kv-clay-spark` / `--kv-clay-tile` / `--kv-clay-line` | `#c45f3b` / `#da6a43` / `#bd5f3e` | spark, Claude tile, progress |
| `--kv-clay-hot` | `#ec987f` | caption accent word |
| `--kv-numeral` | `#e1bfaf` | big pale numeral |
| `--kv-pill` / `--kv-pill-edge` | `#f9ddd2` / `#d39a8e` | strip label highlight |
| `--kv-red` / `--kv-green` | `#ad1f2e` / `#2f9a68` | strip status dot |
| `--kv-supabase` / `--kv-check` | `#3ecf8e` / `#3d996a` | product green / check discs |
| `--kv-dash-*` | see §12 | dashed outlines |
| `--kv-cap-bg` / `--kv-cap-text` | `#1c1d1c` / `#fafcfc` | caption chip |
| `--kv-shadow-card/strip/chip/icon/row` | see kit.css | shadows |
| `--kv-r-card/strip/sock/row/inner/cap` | 24 / 22 / 16 / 14 / 18 / 9 px | radii |

Fonts are always written literally so lint can match their `@font-face`:
- Inter Tight (UI)
- JetBrains Mono (HUD, rows, captions)
- Newsreader and Instrument Serif (titles, "?", numerals)
- Inter (font-built subline)

---

## 15. Beat recipe: one list item, as reference B cut it

Offsets are relative to the spoken word (Whisper timings, `words.json`). Reveals land **0-0.2 s after** their word,
never before it. reference B stays in split layout for this whole window; there is no full takeover.

| beat | contents (kit calls) | sync to voice (measured) |
|---|---|---|
| A. Hook (0-4.3 s) | `powerStrip` + `stripIntro` big and high from frame 0. `stripBlink` on "Non"; `serifTitle` on the topic words; `stripPill` on the tool name; `stripNo` on the 2nd "non". | Title +0.05 s after "vibe"; pill +0.11 s after "Claude"; shake starts 0.13 s before Whisper's "non" |
| B. "these N items" | `questionBoxes` on "installato questi"; `socketOutlines` on "N plugin"; the dip wave on the end of "plugin" | Boxes +0.08 s after "installato"; outlines on "plugin" (−0.02 s) |
| C. Item n named (4.37 s) | `stripDock` + `bigNumeral` + `socketWait`; the title cuts out | Dock +0.13 s after "Il primo" |
| D. Item card (4.9 s) | `pluginCard` (badge, marketplace, logo pop, typing) | Card +0.04 s after "plugin"; badge on "ufficiale"; logo +0.07 s after the name |
| E. Connect (6.0-6.9 s) | `plugIn` (ghost 0.6 s before the seat); progress and status flip on the seat | Seat in the middle of "collega" |
| F. What it does (6.9-8.8 s) | card content exits; `flowDiagram` (cube, line, packets, database) | Solid database +0.01 s after "database" |
| G. Capabilities (8.8-14.4 s) | `cut` card A + `toolsCard`; one `toolRow` per verb, about 1.2 s apart | Card +0.013 s after "Così"; rows +0.08-0.21 s after each verb |
| H. Next beat (14.37 s) | `cut` card B + `browserCard` | Cut +0.19 s after the sentence ends |

Pace: something changes every 0.7 s or so. Long holds always carry motion: the strip's push, the socket breathing,
the cube's yaw, the cards' growth, the grid drift. For items 2..N repeat C-G with `socket: n-1` and the next count;
a second plug passes `green:false`.

## 16. Not in this reference

These are not in this reference, so the kit does not fake them:
- **Caption treatments:** no karaoke and no highlight sweep. Captions are hard swaps with a pop and one accent word.
  The nearest "highlight" is the strip's label pill (`stripPill`).
- **Accent boxes, steppers, skill cards with command bars, calendars, goal cards, org trees, full takeovers, dark
  hooks:** these are in the sibling kit `../editorial-chiefofstaff/`.
- **Terminal pipeline panel, chip grid, strike-X, comments-sheet CTA, full-face punchline title:** these are in
  other reference B reels (see `../../REFERENCE-ANALYSIS.md`) but not in this 14.5 s window.
- **SFX:** `voice.m4a` already contains the mix (it correlates 0.9993 with the reference audio), so no SFX timings
  were measured.

## 17. Known gaps (inherited from the replica)

- **Title type:** no local font matches reference B's display serif.
  - The demo uses outlines traced from the reference (`demo.html` → `TRACED`), which are rebuilt vectors animated in
    GSAP, not pasted frames.
  - New text uses the calibrated font build, which is box-exact but has different letterforms (§3).
  - The "?" glyphs are Newsreader, not the reference's display "?".
- **Tool rows:** the icons are hand-drawn approximations. The mono descriptions carry about 8-10 % more ink with
  lighter cores than the reference. These tool-card frames are the worst-scoring keyframes, 0.964-0.967.
- **Dash phase:** dashed curves are phase-matched only on straight sides. Rounded corners, the database arcs and the
  skeleton tile border are not.
- **Card A text weights:** "ufficiale" and "Marketplace di Anthropic" are slightly off, because Inter Tight 400 is not
  in the asset set.
- **Phase-2 strip:** its top edge sits 1 px low. Raising it was tested and cost 0.003-0.005 SSIM on the sockets.
- **Tools-row entrance:** about half a frame off (motion frames at 9.0 and 9.1 s score 0.968).
- **25 fps cadence:** reproduced only through the per-frame tables of the fast motions. Slow tweens are continuous.
  Use `KIT.cadence = "smooth"` to drop the holds in new videos.
- **Unmeasured parts:**
  - socket counts other than 4
  - numerals other than "1"
  - URL typing beyond "sup"
  - auto pill widths
  - the six extra lucide icons

## 18. Re-verifying the kit

```bash
# test project: work\replica\editorial-vibecoding\kit-test
#   index.html = demo.html, kit.css + kit.js copied, assets = junction to ..\assets (keep ONLY one root composition here)
#   variants\shift.html = demo with every time +30 frames, variants\title.html = font-built title,
#   variants\generic.html = a new video from defaults (generic-project\ = the same page as a project, for `check`)
cp demo.html <kit-test>/index.html; cp kit.css kit.js <kit-test>/
cd <kit-test> && npx hyperframes@0.8.184 lint          # 0 errors, 0 warnings
npx hyperframes@0.8.184 check                           # passes (contrast 165/165)
npx hyperframes@0.8.184 snapshot --at 0,0.5,1,...,14.5 --describe false --no-end -o snaps
python tools\score_replica.py snaps ..\ref\ref.mp4 score --region 0,0,1080,960   # 0.9736 / 1.94
# identity vs the replica: compare these snaps with ..\snaps above y 960 (expect 0 differing pixels)
```
