# neo-brutalist

Neo-brutalism for the ivory kit. Chase liked a stills-only trial of it on the five-tools short on 2026-11-16 ("looks solid", `a mock that does not ship`) and asked for it as a real look on 2026-11-17. Set `"look": "neo-brutalist"` (and `"look_source"` with his words) in `plan.json`.

Everything in `templates/ivory/LIGHT.md` still holds: the hard rules, the three layouts, the frame bands, the chip's timing, the defect list. Only the look below changes.

What it draws: a cream ground with a still dot grid; white cards in a thick black outline with a hard black shadow down and to the right; flat yellow, pink and mint blocks; heavy tight grotesk type with heavy mono labels; captions as white boxes in the same outline and shadow, the accent word on a yellow block; the counter as a white strip of cream seats that fill yellow; one black rule along the seam. His footage itself is never touched.

## What is in this folder

| File | What it is |
|---|---|
| `look.css` | Laid over the kit's `style.css`. Hand-kept. Kit classes, component classes projects have carried, and the look's own `nb-` classes: no scene or element id |
| `look.json` | The colour remap for ivory's and charcoal's literals where a scene or the timeline wrote one |
| `fonts/` | Inter 800 and 900, JetBrains Mono 800 (SIL OFL 1.1, `FONTS-LICENSE.txt`). The other cuts are the kit's own. Safe to ship publicly |

No `motion.js` and no `assets/`. A project made before 2026-11-17 needs `python templates/ivory/build_kit/new_project.py <id>` once, which copies the three fonts and keeps everything else.

## The look

- **Ground** `#fdf3dc`, dots `#111` at 15 %, 44 px apart, not drifting. **Ink** `#111`, secondary `#333`, labels `#55514a`.
- **Outline**, always `#111`, always square: 3 px small parts, 4 px boxes inside a card, 5 px cards and rows, 7 px the one hero block.
- **Shadow**, hard, no blur, down and right: 6 px small boxes, 8 px the caption, 10 px cards and rows, 14 px the hero block. A capture written straight after its card casts none.
- **Colour.** Yellow `#ffd400` is the one thing that matters: the number box, a lit state, the highlight word, a filled seat. Pink `#ff5c8a` is the working accent: tags, flags, outlines on a capture, bars. As type the accent is deep pink `#d6246e`. Mint `#7df9c1` is the quiet second tag. No gradients, no tints of the three.
- **Type.** Inter 800 and 900 for headlines, numbers and labels, tracking -0.03 to -0.06em. JetBrains Mono 500 to 800 for everything the kit sets in mono. The look's two families remap weight (a scene's 600 or 700 comes out 800), and draw Inter at 92 % so a heavy line is as wide as charcoal's Hanken Grotesk.
- **Headline accent word** (`title()`): black on a yellow block.
- **Captures** keep their own colours inside a 4 px black frame.
- **Caption chip**: white, 5 px outline, 8 px shadow, Inter 900 caps at 56 px. Accent word: yellow block, black text.
- **Counter**: white strip, cream seats, a seat fills yellow with its black icon; the finished count turns pink.
- **Seam**: a 6 px black rule on the top edge of his footage.

## What a scene may add

Scenes are written as for any look. These classes go beside an element's own and do nothing under another look.

| Class | What it does |
|---|---|
| `nb-box` | A white box in the 4 px outline, for a project's own component. With `nb-lift`: the 6 px shadow |
| `nb-yellow`, `nb-pink`, `nb-mint` | The three fills, black text |
| `nb-dark` | A black panel (a code listing). Inside it `var(--ink)` is white and the accent is yellow |
| `nb-flat`, `nb-lift` | `nb-flat` on a card or a capture drops its shadow. `nb-lift` on a capture forces it |
| `nb-ground` | Cream with the dot grid, for a full-screen scene's own backing fill |

## What to watch

- **Shadows need room.** A card casts 10 px right and below. Keep a card's right edge at or left of x 1010, and on a split scene its bottom at or above y 765, or the shadow meets the counter (y 780). A tag that hangs over its card's edge runs its shadow into the card's outline.
- **Write colours through the variables.** Accent type is `var(--clayd)`. On the kit's text classes `var(--clay)` also comes out deep pink, because pink type is too pale on white.
- **No white type on an accent.** The kit's two cases (a lit node's label, a clay stage's text) are held black. A scene's own white-on-clay text has to change.
- **A dark panel takes `nb-dark`.** `background:var(--dark)` with `color:var(--ink)` is black on black here, as it is in ivory.
- **A full-screen scene's own `background:var(--iv)` fill hides the dot grid.** Give that fill `nb-ground`.
- **Content goes beside a card, not inside it.** `card()` has a real 5 px border, so anything nested in a `.pc` element sits 4 px in from where ivory puts it.
- **Run `geometry.py`.** A scene sized for charcoal fits. A serif line sized to the edge for ivory's narrower Newsreader may not.
- **Never draw this look, or any look, as a choice the viewer can pick unless it ships.**

## Proof

`work/brutal-look-test`: the five-tools short (81 s) built with this look, stills of every scene, and a static sheet of the kit components that short does not use (`components/`). Stills only. On that build: owner audit PASS, `conform.py --all` no FAIL, lint 0 errors, `geometry.py` 0 FAIL and 2 WARN (the same two CTA lines warn under charcoal).

## Not done

- **Motion.** The kit's own calm motion plays as it is. A neo-brutalist entrance (hard cuts, snap-ins, stepped moves) would be a `motion.js`.
- **A rendered video.** Nothing has been rendered in this look: stills only, at 1080x1920. The 4K final is unchecked.
- **A real edit with captures.** `plate()`, `title()`, doors, nodes, pills, stages and the model rows are proven on the static sheet, not in a built short.
- **Sound.** No cues of its own.
- **Popout bottom and full-face (`full_face` on).** Not tried with this look. The seam rule is drawn on `#face-wrap`.
