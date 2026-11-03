# What the default palette may sound like — UNVERIFIED by ear

All 37 default-tier entries in `templates/ivory/sfx/sfx.json` are measured here from the **existing cut WAVs**, not the whole source recordings. Every interpretation below is **UNVERIFIED by ear**. Chase’s source-file yes/maybe does not validate every slice/event pairing. No library file or gain was changed. Blank “Chase’s ear” cells are intentionally reserved for his comments.

## How to read the numbers

Length is decoded sample count / 48,000. Attack is the existing tool’s first 5ms RMS window within 12dB of the slice’s maximum 5ms RMS, with 5ms resolution. It is an operational sync estimate, not a heard attack or a physical 10–90% rise time. The peak-envelope time is separately retained in [palette-measurements.json](palette-measurements.json).

Core span is time between 5% and 95% cumulative squared-sample energy. Brightness is the power-weighted spectral centroid from 2048-sample Hann frames (50% overlap; discard frames more than 40dB below the loudest). HF is the power fraction above 4kHz. Both describe spectral distribution, not pleasantness or perceptual loudness. Peak count uses 5ms RMS envelope peaks with >=6dB prominence, >=40ms separation and within 18dB of the largest peak. It does not count heard strokes, words or clicks. Stereo was downmixed to mono consistently.

`target_db` in the JSON remains the old 250ms cue-versus-voice reference target. It is not the same as integrated cue-track LU under voice. `reports/2026-11-01-sound-strategy/LEVELS.md` explains why the distinction matters.

## Measured catalogue

Every description and fit suggestion in this table is **UNVERIFIED by ear**.

| Sound | Length / attack (s) | Core span (s); peaks | Brightness Hz; HF% | What the numbers suggest — UNVERIFIED | Fits / does not fit — UNVERIFIED | Chase’s ear |
|---|---:|---|---:|---|---|---|
| whoosh-a | 0.693 / 0.140 | 0.147–0.241; 2 | 75; 0.1 | bass-weighted; 2 separated envelope peaks; short gesture | Fits: required layout entry; low body accent. Avoid: cursor, line or airy swish assumed from name. | |
| whoosh-b | 0.467 / 0.030 | 0.053–0.165; 1 | 142; 0.0 | bass-weighted; one dominant envelope peak; short gesture | Fits: required layout entry only if Chase keeps his maybe. Avoid: tiny interaction or transparent air assumed from name. | |
| whoosh-c | 0.312 / 0.005 | 0.012–0.202; 3 | 85; 0.0 | bass-weighted; 3 separated envelope peaks; short gesture | Fits: required layout entry, alternate to a. Avoid: bright swipe or click. | |
| pop-hero | 0.250 / 0.090 | 0.094–0.108; 1 | 1022; 2.7 | mid-weighted; one dominant envelope peak; compact energy packet | Fits: one principal object arriving. Avoid: every headline word or completion. | |
| pop | 0.250 / 0.020 | 0.021–0.036; 1 | 882; 1.1 | mid-weighted; one dominant envelope peak; compact energy packet | Fits: one secondary object arriving. Avoid: continuous movement or typed text. | |
| pop-soft | 0.200 / 0.040 | 0.042–0.052; 1 | 836; 1.1 | mid-weighted; one dominant envelope peak; compact energy packet | Fits: quiet object/burst accent. Avoid: a sustained bed; soft is a role, not proof of timbre. | |
| click | 0.460 / 0.085 | 0.089–0.203; 2 | 8575; 73.3 | very bright; 2 separated envelope peaks; short gesture | Fits: visible desktop press/release after checking both impulses. Avoid: cursor movement, drag-selection, phone tap. | |
| bell | 1.460 / 0.225 | 0.236–0.710; 1 | 4863; 71.4 | bright; one dominant envelope peak; extended gesture/tail | Fits: visible completed task or explicit verdict. Avoid: online status, ordinary green check, proof of an unverified claim. | |
| whoosh-d | 0.790 / 0.185 | 0.191–0.267; 1 | 551; 1.1 | low/mid-weighted; one dominant envelope peak; short gesture | Fits: clear object travel/docking, if duration fits. Avoid: a static card or finger click. | |
| film-burn | 2.000 / 0.510 | 0.511–0.659; 2 | 2084; 15.6 | mid-weighted; 2 separated envelope peaks; short gesture | Fits: an actual film-style transition. Avoid: ordinary UI transition; name is not permission for cinematic treatment. | |
| pop-2 | 0.400 / 0.110 | 0.113–0.119; 1 | 1473; 1.7 | mid-weighted; one dominant envelope peak; compact energy packet | Fits: alternate object landing; very brief main transient. Avoid: continuous rise or sustained text write. | |
| bubble | 0.209 / 0.050 | 0.051–0.072; 1 | 603; 0.0 | low/mid-weighted; one dominant envelope peak; compact energy packet | Fits: round object arriving, after contextual audition. Avoid: all cards merely because it is a pop. | |
| metal-pop | 0.330 / 0.040 | 0.041–0.065; 1 | 945; 4.4 | mid-weighted; one dominant envelope peak; compact energy packet | Fits: hard object contact when pictured. Avoid: ordinary web page arrival or the word sued. | |
| click-b | 0.310 / 0.035 | 0.036–0.196; 2 | 7310; 78.5 | very bright; 2 separated envelope peaks; short gesture | Fits: visible desktop click; two impulses need context. Avoid: drag-selection or cursor travel. | |
| switch | 2.280 / 0.320 | 0.324–0.418; 3 | 2264; 16.1 | mid-weighted; 3 separated envelope peaks; short gesture | Fits: a visible physical/device toggle; compensate 320ms preroll. Avoid: instant button touch or continuous drag. | |
| lighter | 0.240 / 0.075 | 0.075–0.100; 1 | 6260; 62.6 | very bright; one dominant envelope peak; compact energy packet | Fits: one meaningful row/check activation. Avoid: every list row by default or completion chime. | |
| typing | 6.000 / 0.130 | 0.131–5.391; 66 | 2471; 10.5 | mid-weighted; 66 separated envelope peaks; sustained or repeated texture | Fits: actual typed span, cut first key to last. Avoid: text already visible, whole word landing. | |
| typing-b | 6.000 / 1.090 | 1.140–5.481; 16 | 1178; 11.0 | mid-weighted; 16 separated envelope peaks; sustained or repeated texture | Fits: actual keyboard run after locating first key. Avoid: short burst using the untrimmed 1.09s lead. | |
| typing-c | 6.000 / 0.400 | 0.858–5.899; 40 | 2759; 19.9 | mid-weighted; 40 separated envelope peaks; sustained or repeated texture | Fits: actual keyboard run with measured first key. Avoid: word pop or type that begins at clip start without trim. | |
| typing-d | 6.000 / 0.620 | 0.754–5.887; 38 | 1187; 5.5 | mid-weighted; 38 separated envelope peaks; sustained or repeated texture | Fits: actual laptop typing with measured first key. Avoid: touchscreen digits; short onset using 620ms silence. | |
| tap | 0.166 / 0.120 | 0.121–0.123; 1 | 1831; 0.7 | mid-weighted; one dominant envelope peak; compact energy packet | Fits: a visible phone touch, with attack aligned. Avoid: desktop selection or continuous drag. | |
| camera | 0.334 / 0.045 | 0.054–0.231; 4 | 5457; 52.5 | bright; 4 separated envelope peaks; short gesture | Fits: snapshot/recording affordance actually shown. Avoid: arbitrary cut between source pages. | |
| shutter | 0.648 / 0.080 | 0.082–0.227; 3 | 5436; 56.2 | bright; 3 separated envelope peaks; short gesture | Fits: a camera capture, after multi-part gesture review. Avoid: ordinary text landing or mouse action. | |
| camera-snap | 2.000 / 0.245 | 0.248–1.104; 2 | 7716; 86.7 | very bright; 2 separated envelope peaks; extended gesture/tail | Fits: analogue capture action long enough for the sequence. Avoid: tiny snap implied by the short alias. | |
| camera-rec | 0.420 / 0.090 | 0.093–0.209; 3 | 5550; 50.9 | bright; 3 separated envelope peaks; short gesture | Fits: recording starts and a matching device action is visible. Avoid: any camera screenshot or status turning green. | |
| camera-focus | 3.000 / 0.030 | 0.030–0.752; 1 | 6999; 65.7 | very bright; one dominant envelope peak; extended gesture/tail | Fits: focusing action only after Chase selects a precise slice. Avoid: automatic use: manifest says slice not yet chosen. | |
| snip | 0.292 / 0.125 | 0.126–0.128; 1 | 9555; 94.8 | very bright; one dominant envelope peak; compact energy packet | Fits: a genuinely hard snap using the approved gesture. Avoid: every caption or a line drawing. | |
| marker | 0.751 / 0.010 | 0.065–0.611; 11 | 4337; 37.9 | bright; 11 separated envelope peaks; extended gesture/tail | Fits: a visibly repeated/sketched hand gesture, if Chase agrees. Avoid: one straight strike, highlight wipe, selection drag. | |
| highlighter | 0.380 / 0.080 | 0.110–0.310; 2 | 8517; 93.5 | very bright; 2 separated envelope peaks; short gesture | Fits: a single short straight annotation wipe or strike. Avoid: scribbling, clockwise box tracing, cursor drag sound by default. | |
| paper-fast | 1.980 / 0.095 | 0.130–1.824; 5 | 3319; 25.8 | bright; 5 separated envelope peaks; sustained or repeated texture | Fits: a paper surface turning over an appropriate span. Avoid: digital card merely sliding. | |
| paper-slow | 3.120 / 0.075 | 0.252–2.842; 10 | 2658; 19.1 | mid-weighted; 10 separated envelope peaks; sustained or repeated texture | Fits: a visibly slower paper turn, cut to action. Avoid: instant UI card landing. | |
| sheet-slide | 2.005 / 0.190 | 0.212–1.315; 7 | 4521; 42.8 | bright; 7 separated envelope peaks; sustained or repeated texture | Fits: a physical paper sheet sliding. Avoid: every software panel slide. | |
| ui-tick-a | 0.720 / 0.020 | 0.046–0.388; 2 | 443; 0.4 | low/mid-weighted; 2 separated envelope peaks; extended gesture/tail | Fits: meaningful system state transition, after matching the two-part shape. Avoid: a literal mouse tick assumed from alias. | |
| ui-tick-b | 0.380 / 0.115 | 0.130–0.257; 1 | 417; 0.0 | low/mid-weighted; one dominant envelope peak; short gesture | Fits: brief meaningful state feedback. Avoid: cursor movement or bright mechanical tick. | |
| ui-tick-c | 0.477 / 0.080 | 0.113–0.289; 1 | 314; 0.0 | low/mid-weighted; one dominant envelope peak; short gesture | Fits: brief meaningful state feedback, lower-frequency alternate. Avoid: high-frequency click assumed from tick. | |
| phone-ring | 3.012 / 0.090 | 0.166–1.514; 28 | 460; 0.0 | low/mid-weighted; 28 separated envelope peaks; sustained or repeated texture | Fits: literal phone ringing, stop at answer. Avoid: generic waiting or urgency beneath speech. | |
| clock | 3.000 / 0.145 | 0.153–2.658; 18 | 5126; 77.0 | bright; 18 separated envelope peaks; sustained or repeated texture | Fits: visible time-running gesture, precisely bounded. Avoid: a long bed throughout the short. | |

## Names and readiness flags

- **whoosh-a:** LOW-FREQUENCY: 75 Hz centroid; “whoosh” does not imply airy brightness. **UNVERIFIED by ear.**
- **whoosh-b:** MAYBE approved; 142 Hz centroid; replace this option first, per current rule. **UNVERIFIED by ear.**
- **whoosh-c:** LOW-FREQUENCY: 85 Hz centroid; three peaks, not necessarily a single air sweep. **UNVERIFIED by ear.**
- **pop-hero:** “Hero” and “soft” describe assigned roles; identical source file as pop/pop-soft. **UNVERIFIED by ear.**
- **pop-soft:** “Soft” is not independent taste evidence; gains and slice determine prominence. **UNVERIFIED by ear.**
- **click:** Two envelope peaks 110ms apart: could represent press/release. Not one proven single tick. **UNVERIFIED by ear.**
- **click-b:** Two peaks: do not infer one isolated impulse from “1 Click Mouse”. **UNVERIFIED by ear.**
- **switch:** 2.28s container, 320ms attack, 94ms core energy; alias hides long lead/tail. **UNVERIFIED by ear.**
- **lighter:** Literal lighter file repurposed as a row accent; not a software authenticity claim. **UNVERIFIED by ear.**
- **typing-b:** 1.09s threshold attack; file name alone would produce a late key onset. **UNVERIFIED by ear.**
- **camera-snap:** 2s container and 856ms energy span; “snap” hides a sequence/tail. **UNVERIFIED by ear.**
- **camera-focus:** Manifest explicitly says slice not yet chosen: default tier does not make it ready. **UNVERIFIED by ear.**
- **marker:** MISLEADING for a single line: 11 peaks over a 751ms slice. **UNVERIFIED by ear.**
- **highlighter:** Very bright (93.5% energy above 4kHz); not proved smooth or audible on a phone. **UNVERIFIED by ear.**
- **ui-tick-a:** “Tick” suggests a sharp click; measured core lasts 342ms at 443Hz centroid. **UNVERIFIED by ear.**
- **ui-tick-b:** 417Hz centroid, 127ms core; could be tonal feedback rather than a bright tick. **UNVERIFIED by ear.**
- **ui-tick-c:** 314Hz centroid, 177ms core; alias hides low-frequency feedback. **UNVERIFIED by ear.**

## Marker versus the straight line at 1.76s

The pictured action `b01.e5` takes 0.300s. Current `marker` starts at 1.770s and runs 0.751s, through 2.521s: its file lasts 2.50 times the drawing span and crosses the next beat at 2.200s. Its 5–95% energy span alone is 0.546s. The envelope has peaks at 0.010, 0.065, 0.155, 0.240, 0.320, 0.405, 0.470, 0.545, 0.590, 0.665 and 0.725s. These repeated energy surges are consistent with Chase’s “scribbling” description. The waveform does **not** independently prove a pen or the number of strokes.

`highlighter` lasts 0.380s, with core energy at 0.110–0.310s and two detected peaks at 0.165 and 0.290s. Its 8,517Hz centroid is almost twice marker’s 4,337Hz; it is not simply a shorter recording of the same measured texture. For a cue attack at event+0.020s, start it at 1.700s. Its file ends at 2.080s, before the next beat. This is a better **measured gesture-duration candidate**, matching Chase’s requested straight-highlighter vocabulary; it still requires his ear. Do not declare “smooth” from the name or these numbers.

No new sounds are proposed for automatic use. If neither approved slice fits, leave the event silent and request one straight 0.2–0.4s highlighter swipe for Chase to audition. A software selection drag remains a separate event class; adding a highlighter noise there would need contextual approval, not just a colour resemblance.

## Reproduction

`python reports/2026-11-01-sound-strategy/analyze.py palette` writes the measurements and this folder’s temporary analysis directory only. Then `python reports/2026-11-01-sound-strategy/write_palette.py` builds this document. Raw source/slice identities, all peak times, crest factors and low-frequency fractions are retained in the JSON. This report makes no claim about phone audibility, timbral pleasantness, exact source identity beyond the manifest, or word masking without listening.

## Earshot sounds Chase said yes to, 2026-11-02

28 code-made sounds from the earshot bank (`_ext/earshot`, MIT), out of 95 he heard. Every one is a yes **by his ear, heard alone at a fair level**. Where each works against his voice is still unheard. The four `fit` sounds are earshot's code copies of CC0 recordings; credits are in each one's note. Measurements come from `tools/sfx_audition/add_earshot_picks.py`: brightness is the power-weighted centroid over the whole slice and HF is power above 4 kHz, close to but not the same method as the table above. Before the audition, anything with over half its energy under 200 Hz was dropped, so none of these is a rumble like whoosh-a, b and c.

Each source can be re-rendered at an exact length or with its peak on a set time through earshot's `dur` and `apex` knobs (`earshot sfx render <id> --dur 0.6 --apex 0.3`). Today's slices are the stock takes.

| Sound | earshot id | Length / attack (s) | Brightness Hz; HF% | earshot's note | Chase's ear |
|---|---|---|---:|---|---|
| es-swipe-cloth | `swipe/cloth` | 0.676 / 0.100 | 561; 2.0 | | yes |
| es-swipe-flick | `swipe/flick` | 0.568 / 0.105 | 615; 1.2 | | yes |
| es-swish-blade | `swish/blade` | 0.368 / 0.035 | 902; 0.9 | | yes |
| es-swish-cane | `swish/cane` | 0.700 / 0.055 | 461; 0.2 | | yes |
| es-swish-flick | `swish/flick` | 0.320 / 0.085 | 4266; 50.6 | a high flick that rises and stops dead, wide | yes |
| es-swish-soft | `swish/soft` | 0.883 / 0.060 | 679; 0.5 | | yes |
| es-swish-zing | `swish/zing` | 0.535 / 0.045 | 598; 0.1 | | yes |
| es-swish-stick | `swish/stick` | 0.527 / 0.075 | 392; 0.2 | | yes |
| es-whoosh-fast-heavy | `whoosh_fast/heavy` | 0.765 / 0.100 | 381; 0.4 | | yes |
| es-whoosh-fast-crisp | `whoosh_fast/crisp` | 1.056 / 0.100 | 498; 0.8 | | yes |
| es-whoosh-fast-tight | `whoosh_fast/tight` | 0.536 / 0.120 | 749; 0.5 | | yes |
| es-whoosh-fast-sleeve | `whoosh_fast/sleeve` | 1.090 / 0.115 | 616; 0.4 | | yes |
| es-whoosh-fast-reverse | `whoosh_fast/reverse` | 0.768 / 0.230 | 461; 0.3 | | yes |
| es-whoosh-fast-whistle | `whoosh_fast/whistle` | 0.997 / 0.145 | 573; 0.2 | | yes |
| es-pop-0 | `pop/0` | 0.200 / 0.000 | 716; 0.0 | | yes |
| es-pop-1 | `pop/1` | 0.150 / 0.000 | 1333; 0.0 | | yes |
| es-pop-3 | `pop/3` | 0.160 / 0.000 | 836; 0.1 | | yes |
| es-pop-4 | `pop/4` | 0.220 / 0.000 | 500; 0.1 | | yes |
| es-fit-pop-mouth-plop | `fit/pop/mouth_plop` | 0.281 / 0.010 | 815; 0.0 | a soft mouth plop (CC0, CapsLok) | yes |
| es-knock-wood | `knock/wood` | 0.154 / 0.010 | 783; 0.1 | a mid-band wooden knock | yes |
| es-knock-plastic | `knock/plastic` | 0.153 / 0.050 | 2412; 1.1 | a plastic click that bounces back 18 ms later | yes |
| es-knock-snap | `knock/snap` | 0.134 / 0.040 | 2983; 11.0 | a soft contact, then a bright plastic snap with a bounce | yes |
| es-click-snap | `click/snap` | 0.062 / 0.000 | 3487; 40.7 | | yes |
| es-fit-click-floss-lid | `fit/click/floss_lid` | 0.132 / 0.005 | 4884; 47.6 | a small plastic click (CC0, qubodup) | yes |
| es-typing-key-clicky | `typing_key/clicky` | 0.194 / 0.010 | 4235; 31.7 | | yes |
| es-typing-key-thock | `typing_key/thock` | 0.337 / 0.010 | 3425; 41.1 | | yes |
| es-fit-key-lubed | `fit/key/lubed` | 0.424 / 0.070 | 1818; 3.5 | one mechanical key press (CC0, zrrion) | yes |
| es-fit-key-medium | `fit/key/medium` | 0.426 / 0.100 | 2204; 9.4 | one mechanical key, press and release (CC0, bigmonmulgrew) | yes |

Most of the swishes and whooshes sit at 400 to 900 Hz, close to whoosh-d (551 Hz), which he could hear. `es-swish-flick` is the bright one. The pops all start on their first sample, so a cue lands on its event with no lead.

## Pencil strokes for strike-throughs, Chase picked 2026-11-02

He heard 16 real pencil strokes on 1030-2's first strike, at the main level against his voice, and said yes to two (`pencil-picks.json`). Earlier the same day he turned down the highlighter, 8 pen strokes from a Pencils & Markers recording and 8 earshot swishes for this job ("it should sound like a pencil"). Source: Pixabay, floraphonic's Pencil Foley Write set, local only (`work/sfx-sources/pixabay-pencil/SOURCE.md`).

| Sound | Source | Length / attack (s) | Chase's ear |
|---|---|---|---|
| pencil-a | Write 1, stroke at 0.70 s | 0.33 / 0.025 | yes, for a strike-through |
| pencil-b | Write 5, stroke at 0.62 s | 0.22 / 0.065 | yes, for a strike-through |

Both are shorter than most of the palette and roughly match a 0.3 s strike line. Alternate them. The highlighter stays on highlight wipes.
