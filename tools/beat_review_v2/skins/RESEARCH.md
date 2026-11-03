# Chase video review player: ten skins

Research and implementation: 2 November 2026.

All deliverables are in `tools/beat_review_v2/skins/`. Each CSS file is independent and loads over the existing player with `?skin=<filename-without-css>`. No shared stylesheet, JavaScript, generated image or extra asset is required.

## Research and direction

Read the complete `index.html`, including the final v2 skin, responsive rules, markup and rendering code, before implementation. Read all 46 entries in `the local taste-vault gallery.json research snapshot`; visually inspected Stillpage, DRONE Mapping OS, Monolith, Journey ASCII, Nightlife Refined and Sails Collage.

The strongest transferable ideas were processed material, factual marginalia, extreme typographic roles and a restrained ground. Here the existing video supplies the monumental image. Processing that image would defeat true-colour review, so texture is carried by the surrounding chrome instead. The existing beats, times, frames and cue names supply real marginalia without fabricated telemetry.

The first five are deliberately grounded. The last five are separate worlds: an oscilloscope, a blueprint sheet, a risograph shop, an impact-printer log and an optical poster. Their colour and material systems carry the risk while transcript fields stay calm.

The fixed structure for every direction is:

```text
masthead / picture identity / appearance / approve
picture stage | transcript | notes / checks / rounds / sound
transport / composer
beat timeline / cue lane / legend
```

No grid, visibility rule, main-panel dimensions or picture rendering is redefined.

### Web references found

These are design references, not code or image assets copied into the player. Historical examples are identified as such.

- [OFFF Forum, live site](https://www.offforum.com/) — expressive serif identity paired with factual grotesk information. A current reference discovered through [Dokle's 17 October 2026 review](https://dokle.design/awards/offf-forum-serif-for-the-mood-grotesk-for-the-facts); the review reports its Awwwards recognition. Applied as type-role separation, not a layout clone.
- [Huy Phan, live portfolio](https://huyml.co/) — personal typographic identity and restrained project metadata. [Dokle's 15 October 2026 review](https://dokle.design/awards/huy-phan-portfolio-typography-one-red-serif) describes its display serif and pale oversized numerals. The player borrows the hierarchy, not the red decorative colour, which is reserved here for attention.
- [Teenage Engineering TP–7](https://teenage.engineering/products/tp-7) — compact dedicated recording hardware. Material hierarchy, quiet labels and positive physical controls informed Alloy.
- [DaVinci Resolve panels](https://www.blackmagicdesign.com/products/davinciresolve/panels) — professional editing/colour hardware. A reference for sustained-use legibility, restrained dark surfaces and control differentiation.
- [Actual Source: The Art of Computer Designing](https://actualsource.org/products/the-art-of-computer-designing) — Osamu Sato's historical black-and-white computer graphics, originally published in 1993 and reissued. Informed Carbon's dither and Punch's machine-output vocabulary.
- [Actual Source: Greed Specimen](https://actualsource.org/products/greed-specimen) — contemporary type specimen as expressive printed object. Informed Optik's typographic confidence.
- [Actual Source: Weingart, My Way to Typography](https://actualsource.org/products/typography-my-way-to-typography) — historical Swiss typographic experimentation. A research counterweight to treating every Swiss reference as a neutral grid.
- [Science Museum: Tektronix 555 dual-beam oscilloscope](https://collection.sciencemuseumgroup.org.uk/objects/co424239/dual-beam-oscilloscope) — historical instrument reference for graticules, panel marking and phosphor display language.
- [Computer History Museum / Bitsavers: IBM 3270 series reference](https://bitsavers.computerhistory.org/pdf/ibm/3270/950-I048-3270_1985.pdf) — historical terminal reference for dense machine-readable information.
- [Cyanotype UK: process](https://cyanotype.co.uk/cyanotype-process) — material/process reference for Blueprint's deep blue and white-paper marks.
- [Stencil Wiki](https://stencil.wiki/wiki/Main_Page) and [RISOGURA](https://www.stencil.wiki/wiki/RISOGURA) — current stencil-print community and limited-ink printing practice. Informed Overprint's two decorative inks and deliberately offset edges.
- [Cooper Hewitt: Jazz Typography](https://www.cooperhewitt.org/2015/05/27/jazz-typography/) — historical Niklaus Troxler posters, expressive letterforms and visual rhythm.
- [Cooper Hewitt: All Torn Up](https://www.cooperhewitt.org/2014/10/15/all-torn-up/) — historical Felix Pfäffli/Weltformat poster, simulated printed layers and patterned surfaces. Informed Overprint and Optik.

Research limits: the Awwwards typography category timed out; Godly redirected to recent.design, which the web tool could not fetch. Those galleries are not presented as inspected references. The live sites, recent review articles, hardware pages and museum/process sources above supplied the usable evidence. Reported award dates come from the linked reviews rather than an independently fetched Awwwards award record.

## The skins

### 01 — Folio (light)

File: [01-folio.css](01-folio.css) · [Open in player](http://localhost:4750/?skin=01-folio)

**An archival editing ledger: warm stock, serif masthead, measured ink rules.**

Palette: ground `#eeece4`, panel `#faf9f4`, ink `#242722`, muted `#54594f`, navigation `#343f35`, attention `#ad390b`.

Type: Fraunces masthead; Hanken Grotesk reading; IBM Plex Mono data.

References and borrowing: [OFFF Forum](https://www.offforum.com/) and the vault's **Stillpage / Sails Collage**. Borrows the split between expressive identity and factual labels, archival stock, quiet rules and print texture. The transcript remains the primary reading surface.

Within the rules: No processed hero image: the existing video remains the sole monumental image. The print treatment lives in the surrounding ground.

### 02 — Alloy (dark)

File: [02-alloy.css](02-alloy.css) · [Open in player](http://localhost:4750/?skin=02-alloy)

**A machined graphite console with silver keycaps and recessed timecode.**

Palette: ground `#212322`, panel `#2c302e`, ink `#f0f2eb`, muted `#bec5bb`, navigation `#d4e6c4`, attention `#ff995d`.

Type: IBM Plex Sans reading; IBM Plex Sans Condensed masthead; IBM Plex Mono data.

References and borrowing: [Teenage Engineering TP–7](https://teenage.engineering/products/tp-7) and [DaVinci Resolve panels](https://www.blackmagicdesign.com/products/davinciresolve/panels). Borrows hardware material hierarchy, a recessed readout and pale keycaps. These make playback feel like a dedicated physical tool.

Within the rules: No new knobs, meters or control groups; those would change the layout and imply controls the player does not have.

### 03 — Survey (light)

File: [03-survey.css](03-survey.css) · [Open in player](http://localhost:4750/?skin=03-survey)

**A pale sage field instrument with plotting ticks and precise geometric type.**

Palette: ground `#e6ebe2`, panel `#f3f6ef`, ink `#1c3028`, muted `#4b5f52`, navigation `#245547`, attention `#a8390b`.

Type: Space Grotesk reading and masthead; Space Mono data.

References and borrowing: [Tektronix 555](https://collection.sciencemuseumgroup.org.uk/objects/co424239/dual-beam-oscilloscope) and the vault's **DRONE Mapping OS / Spade**. Borrows instrument graticules, plotting ticks, sage plates and precise geometric lettering. Actual beat IDs and timestamps provide the marginalia.

Within the rules: No invented coordinates or sensor readings; no grid or crosshair is placed over the picture.

### 04 — Edition (light)

File: [04-edition.css](04-edition.css) · [Open in player](http://localhost:4750/?skin=04-edition)

**A film journal at the cutting desk: serif transcript, cold white paper and black folios.**

Palette: ground `#f4f4f0`, panel `#ffffff`, ink `#242525`, muted `#595c5a`, navigation `#242525`, attention `#b2370c`.

Type: Newsreader masthead and transcript; Barlow supporting text; DM Mono data.

References and borrowing: [OFFF Forum](https://www.offforum.com/), [Huy Phan](https://huyml.co/), and the vault's **Asterisk / Ambientica**. Borrows the deliberate separation of display identity and factual metadata. A serif transcript makes the edit feel like a film journal.

Within the rules: No oversized headline or editorial reflow: masthead and transcript retain their existing line boxes.

### 05 — Carbon (dark)

File: [05-carbon.css](05-carbon.css) · [Open in player](http://localhost:4750/?skin=05-carbon)

**A one-bit proofing suite: bone-white ink, restrained dither, and film-perforation rhythm.**

Palette: ground `#181818`, panel `#252525`, ink `#f1f0e9`, muted `#c0beb4`, navigation `#e0dfc9`, attention `#ff9a66`.

Type: Hanken Grotesk reading and masthead; JetBrains Mono data.

References and borrowing: [Osamu Sato, The Art of Computer Designing](https://actualsource.org/products/the-art-of-computer-designing), and the vault's **Monolith / Castle / Journey ASCII**. Borrows one-bit rhythm, tonal restraint and a pale masthead over a dark proofing field. Small dither fills give the timeline a printed texture.

Within the rules: The video and review thumbnails are not dithered. FAIL and error text in the pale header receive a dark backing so the same orange works throughout the skin.

### 06 — Phosphor (dark, second pass)

File: [06-phosphor.css](06-phosphor.css) · [Open in player](http://localhost:4750/?skin=06-phosphor)

**A static CRT instrument: luminous green glass, visible raster, a burning playhead beam.**

Unmistakable now: an 84px cropped PHOSPHOR impression in the masthead, glowing VT323 identity, hard luminous gutter graduations, scanlines across the transcript/rail/dock surfaces, recessed keycaps and a beam with a triangular head. Timeline layouts have separate raster, dotted and diagonal fills. Reading glyphs remain sharp: transcript has no text-shadow; stronger glow belongs to display labels and the playhead. No flicker or moving scan.

Type: VT323 display; IBM Plex Sans transcript; IBM Plex Mono data. Attention: peach `#ffab70`, separate from decorative green.

### 07 — Blueprint (dark, second pass)

File: [07-blueprint.css](07-blueprint.css) · [Open in player](http://localhost:4750/?skin=07-blueprint)

**A full cyanotype working drawing, complete with dimension rails and a drafting-pin cursor.**

Unmistakable now: a visible 96px major / 16px minor grid across the sheet, not just the stage; white ticked dimension rails down both picture gutters; cropped 68px BLUEPRINT lettering; double drafting rules, stencilled control plates and a circular crosshair playhead. Timeline layouts use vertical ruling, dots and crosshatch. Near-opaque blue reading beds sit above the sheet grid to protect transcript and rail copy.

Type: Space Mono display; Barlow transcript; Azeret Mono data. Attention: peach `#ffb775`, never used for drafting furniture.

### 08 — Overprint (light, second pass)

File: [08-overprint.css](08-overprint.css) · [Open in player](http://localhost:4750/?skin=08-overprint)

**A rough two-ink print proof: navy impressions visibly slipping against pink.**

Unmistakable now: pink masthead and dock, cropped OVERPRINT/RISO display impressions, 3–5px second-ink offsets, dense staggered navy/pink halftone around the picture, registration crosses inside the gutters, stamped chips and an offset ink needle. A self-contained SVG feTurbulence paper texture lives behind dock controls. Pink is now a full decorative ink, not a faint border. Transcript and timestamps have no misregistration or grain overlay.

Type: Rubik Mono One display; Work Sans transcript; Space Mono data. Attention: burnt orange `#ad3507`, separate from decorative pink `#ad2970`.

### 09 — Punch (light, second pass)

File: [09-punch.css](09-punch.css) · [Open in player](http://localhost:4750/?skin=09-punch)

**An impact-printer fanfold log, with conspicuous tractor perforations and broad green bars.**

Unmistakable now: alternating ivory/green transcript rows, 8px dark feed holes at 25px intervals on both picture gutters, perforation seams, giant CONTINUOUS FEED/PUNCH / FEED impressions, Doto matrix display lettering and dashed paper-label controls. The timeline reads as a punched/ribbon-printed strip; its cursor is a solid feed tab. Holes stay within existing gutters and add no margin.

Type: Doto display (DotGothic16 fallback); Atkinson Hyperlegible transcript; Courier Prime data. Attention: dark rust `#7f2607`, darkened to remain readable on the selected green row.

### 10 — Optik (light, second pass)

File: [10-optik.css](10-optik.css) · [Open in player](http://localhost:4750/?skin=10-optik)

**An acid-yellow optical poster converted into a static review instrument.**

Unmistakable now: concentric black/yellow rings around the picture intersect a second striped gutter field, huge cropped OPTIK impressions occupy masthead and dock, a black transcript heading reverses out of the paper, and thick printed rules hold the sheet together. Layout cells use ruling, dense dots and intersecting diagonal screens; the playhead is a bullseye. Optical fields are static and kept off reading beds.

Type: Unbounded display; Barlow transcript; DM Mono data. Attention: burnt orange `#a53608`; yellow and black are decorative/navigation only.

## Second-pass implementation boundaries

- Rewrote only 06–10 and this document. No extra asset files were needed. 01–05, index.html, server.py and review state were not edited.
- All colour/font tokens remain under `:root[data-theme]`. Each skin retains its own palette across Light, Dark and System.
- No grid-template, display/visibility, main-container width/height, padding or margin overrides. Existing responsive layout and hidden controls remain inherited. Fonts can still change text wrapping; browser geometry was not rechecked this pass.
- No selector targets video, .frame or #regions. No ancestor filter, opacity, blend or mask is introduced. Stage pseudo-elements occupy only the existing side gutters (12–14px, inside the inherited 16px sides); stage backgrounds paint behind the frame. Masthead and dock pseudo-elements use isolated negative stacking, and every new pseudo-element is pointer-events:none.
- Cropped large words are decorative material names, not fabricated status or telemetry. Solid backgrounds beneath live masthead/transport/composer/footer labels preserve their contrast when content expands.
- One attention colour per skin is shared by changed labels/cell edges, FAIL, failing checks, open counts, ready-state summaries and open cue-note markers. Decorative ink, playhead and normal cue pins use --key/ink instead. Count detection retains the original non-nested :has() rules; an attention-selected tab gets a light/dark reading bed suited to its palette.
- No new animation. Transcript/body text sizes are inherited; display headings increase without intentionally changing their line-box height. No new processing is applied to any video.

## Second-pass verification and limits

Completed in this pass:

- Parsed all five rewritten stylesheets with PostCSS. Static audit found no protected-media selectors, forbidden ancestor effects, grid-template/display/visibility changes or main-container dimension/padding/margin declarations.
- Compared source declarations and confirmed the attention rules are after every decorative rule, with --accent equal to --bad in all five skins. Checked every new pseudo-element for pointer-events:none and its placement/stacking boundary.
- Calculated WCAG sRGB contrast for solid reading grounds, selection colours, inverted controls and darkest/lightest timeline pattern extrema. Corrected Blueprint's brightest dots and darkened Punch's attention ink after this check. Conservative minima for ordinary reading text and attention are below; the timeline figure includes pattern extrema rather than only base fills.
- Ran Impeccable's mechanical detector once. Its findings were thick inset rules and tiled line fields. Those are deliberate parts of this brief's CRT/drafting/print/optical worlds; they were retained. This was a design-advisory run, not browser verification.

| Skin | Ink incl. timeline pattern extrema | Muted reading text | Attention reading text |
|---|---:|---:|---:|
| Phosphor | ≥5.34:1 | ≥7.58:1 | ≥6.52:1 |
| Blueprint | ≥5.18:1 | ≥6.17:1 | ≥4.69:1 |
| Overprint | ≥5.32:1 | ≥6.10:1 | ≥4.64:1 |
| Punch | ≥5.97:1 | ≥4.61:1 | ≥5.13:1 |
| Optik | ≥6.30:1 | ≥7.56:1 | ≥5.42:1 |

**Could not render or check:** Fresh screenshots, browser-computed geometry, responsive overflow, actual font loading/appearance, grain rendering, stacking and live review-state colours. Chrome launch timed out through both its normal connection and a pipe; Edge launch also timed out. The computer-use browser host reported unavailable; the native Chrome fallback was denied with “Computer Use was not approved to use Google Chrome”. These second-pass sheets have therefore received source/contrast verification, not a successful visual browser pass. The attached 1600×900 images and earlier verification records describe the first pass, not these rewritten files.

Google Fonts imports are configured, with local/system fallbacks, but this pass could not verify successful downloads. No hours-long fatigue study, Safari/Firefox pass, real-device touch test or pixel-level colourimetric measurement was performed. No notes, approvals, native renders or sound-preview mutations were exercised. Existing screenshots in reports/player-skins were left untouched.
