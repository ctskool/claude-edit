# Ivory picker

Which visual a line gets. Base: `styles/VISUAL_MENU.md`. Chase's rules win every conflict. Full-face applies only with `full_face` on, per `layout.md`.
Format: rule, why, then Met (how to tell it held). "(untested on ivory)" means ivory has not proven it.
Pruned 2026-11-02: the per-line-kind recipes, big-type and hook rankings went. They made every video pick the same moves. Taste comes from Chase's notes and the references (`references/HOW.md`).

## Laws

- **Enact the line. The chip carries the words.** (untested on ivory) Why: the chip says every word, so the panel must add what audio cannot.
  Met: with chips hidden, the panel still shows the thing doing what he says, on the word he says it.
- **Every pick names its trigger.** [Ours] Why: nothing on screen is a default or a gimmick.
  Met: `why` quotes the trigger words and says why the higher rows do not fit.
- **Proof beats illustration.** [Ours] Why: a real asset is evidence, a drawing only explains.
  Met: no `scene` replaces a fact's evidence. It may sit behind or beside it.
- **Verified numbers only. Real artifacts, never fake "test" slides.** [Chase] **A built visual never invents evidence, and a quoted artifact is verbatim.** (untested on ivory)
  Why: it illustrates, it does not testify. Met: every figure passes `HOUSE.md`'s fact test, no name or date appears that he did not say, and quoted text matches its source.
- **Layout comes first.** With `full_face` on, a full-face trigger in `layout.md` takes `face`. With it off, an opinion, payoff or CTA line takes `face`. A BIG join takes its cover. All of this comes before any menu row. [Chase] [Ours]
  Why: a CTA naming a product or a payoff on a figure must not skip his rule. Met: no such line got a menu row instead.
  With `full_face` off, `face` stays split and its top half takes a real asset, never only his words. See `layout.md`. With it on, `face` is the full-face layout. [Chase]

## The menu: after that, the first row that fits wins

| type | pick it when the line... | on screen | tag |
|---|---|---|---|
| `real_shot` | names or points at a specific product, repo, post, page, price table or chart that exists | the real thing in either form, rebuilt card or capture, zoomed or highlighted on the exact part said | [Ours] |
| `own_clip` | describes something Chase showed or did in his screen recording | a 2-4 s clip of his own recording, from `shared/clips` | [Ours] |
| `number` | turns on one figure (a price, a %, a multiplier, a date) | one big number, its unit, a source line, from `facts.json` only | [Ours] |
| `compare` | sets two things against each other | side by side, bars or an equation, the winner lit | [Ours] |
| `diagram` | describes a process, flow, steps, a structure, how parts connect | boxes, arrows or steps that build on each word | [Ours] |
| `list` | names 3+ items in a row | one item per beat, each landing on its word | [Ours] |
| `scene` (open, see below) | is abstract, a metaphor, a "big idea" with nothing real to show | a generated illustration, real text and logos added by the build | [Ours] |
| `face` | is opinion, emotion, direct address, a rhetorical question, the payoff, the CTA, or with `full_face` on covers a visible jump cut | `full_face` off: split, a real asset on top, chip on the seam. A quiet panel only for a CTA or a pure opinion hook. `full_face` on: Chase full frame, serif title or chip on the shirt | [Chase] |
| `text` | is a short punchy phrase that IS the message and nothing above fits | the words, set big, used rarely | [Ours] |

- **Rebuilt cards, current rule.** [Chase] STYLE keeps "rebuilt vector UI cards" and "real artifacts". It bans browser-window screenshot cards as the main device.
  Why: `real_shot` names the evidence, not the form, so which form is ivory's default stays open. Met: `why` says which form each beat used.
- **A row names the device, and a real asset can supply it.** [Ours] Why: a product name must not beat what the line turns on. Met: a comparison or figure line takes that row, using real shots.
- **Scenes are rare and earned.** [Ours] Why: all scenes belong to one world and must not stand in for proof.
  Met: at most 1 per ~15 s (a 45 s short gets 2-3), only on abstract or metaphor lines, never two in a row. Image route and look: `captures.md`.
- **No visual shorter than about 1 s.** (untested on ivory) Why: a visual that short only flashes. Met: a clause that short rides its neighbour.

## Big type and hook

- **The serif headline is ivory's big type.** [Chase] Why: it is a Keep rule. Met: big type is the serif with one italic clay word.
- **Hook visuals are real or rebuilt.** [Ours] Why: no stock clips, generated people or AI cold open. Met: every hook source is listed in ASSETS.md.
- **The chip keeps the seam.** [Chase] Why: mono chips on the seam are a Keep rule. Met: on a split hook, any title sits in the panel, never replacing the chip.
- **The hook pick sets the visual, not the line.** [Ours] Why: hook line moves are open. Met: the picker changes no cut.

## Trial ideas, off until Chase says yes

- **Reading shows the source, explaining shows him.** (untested on ivory) His cue is gaze. Ours: the source stays up through its last matched word.

## Open decisions, never settle here

- Real captures or rebuilt cards as ivory's default. 13 of 24 beats on 1023-test are already real shots.
- Whether isometric scenes stay. Hook line moves. Full list: `HOUSE.md`.
