# Ivory captions

The chip: how it looks, what it says, when it shows, where it sits. Chase wins any conflict.
Layout numbers are at 1080x1920. The 2160x3840 publish frame is exactly double.
Full-face rows and rules here apply only with `full_face` on, per `layout.md`. With it off, every beat is split or takeover. [Chase]

## The look

| Property | Value | Source |
|---|---|---|
| Type | JetBrains Mono 500, UPPERCASE, tracking .04em | [Ours] |
| Colour | Text #F5F4EE on #1B1D1D | [Ours] |
| Shape | Radius 10px | [Ours] |
| Size | ~52 px text, ~96 px chip | [Ours] |
| Words | 2-3 per chunk, until the chunk decision below is made | [Ours] |
| Accent | On <= 10% of chunks. The measured accent is clay #E0907E on the dark chip | [Ours] |
| Motion | Hard swap, no animation | [Ours] |

- **Mono chips on the seam stay.** They are on Chase's Keep list. [Chase]
  Why: they are part of what makes it ivory. Met: no other caption style appears on a split beat.
- **The accent marks a product name or keyword, nothing else.** [Ours]
  Why: at this rate it still reads as a signal. Met: accent chunks counted, each one names a product or keyword.
- **The chip alone carries legibility.** No outline, glow or fade behind it. [Chase]
  Why: he rejected dark fades, and ivory bans glow. Met: the chip sits on untouched picture.
- **The whole chip swaps on and off.** No word pop, karaoke, box grow or fade. [Ours]
  Why: the graphics carry the motion. Met: each chip looks the same on its first and last frame.

## What it says

- **Captions equal the corrected transcript, word for word, and every spoken word gets a chip.** Mishears are fixed in `raw/corrections.json`, never in the caption layer. A very short word joins a neighbouring chip, never disappears. (untested on ivory)
  Why: a dropped word is invisible in review, a hand fix is lost on rebuild, and a gap reads as a bug with the sound off.
  Met: every kept word maps to exactly one chip, apart from a listed title-only span. The check ignores case, punctuation and number format.
  With `full_face` off there is no planned gap: quiet-panel beats keep the chip on the seam. [Chase]
  With `full_face` on, the one planned gap is a title-only span: a full-face beat using a serif title in place of the chip. [Chase]
- **Captions stay verbatim where the facts rules differ.** Those rules apply to graphics only. [Ours]
  Why: the chip is what he said. Met: a loose phrase he spoke stays on the chip, with the exact fact on the graphic. A claim shown wrong goes to Chase as a cut flag.
- **A spoken unit stays whole.** A time, a number with its unit, a brand name, a decimal. (untested on ivory)
  Why: Whisper splits "5" ".5", and two of our engines printed 5.5 as 55. Met: "5.5" reads 5.5 on one chip.

## When it shows

- **A chip shows about 0.07 s ahead of its first word.** STYLE's measured "2 frames before its first word", at 30 fps. [Ours]
  Why: it is the measured value, and Chase has not ruled on it. Met: each chip's first frame sits that far ahead, snapped once to the output grid.
- **A chip never crosses a layout switch or a join.** It ends before the incoming shot, and a first word just after a cut opens on the cut frame. (untested on ivory)
  Why: a stale chip on a new shot reads as late, and a bare new shot reads as a gap. Met: no chip is lit on a shot it does not belong to. Joins come from `raw/cuts.json`.
  A card or scene swap inside one layout does not break a chip while speech runs on. Nor does a build inside a card. [Ours]
  Caption building never moves a cut, switch or word. [Ours]

## Where it sits

| Layout | Placement | Source |
|---|---|---|
| Split | Centred on the seam, vertical centre y 960 | [Chase] |
| Full-graphic takeover | Drops to y ~1480-1570 | [Ours] |
| Full-face, `full_face` on only | On the shirt, below the chin, measured per take | [Chase] |

- **The seam here is the composed seam, never the raw seam.** The two rows are defined in `layout.md`. [Ours]
  Why: a check on the wrong row reads a false result. Met: split chips measure centred on STYLE's y 960.
- **The chip holds, the graphic gives way.** On split the chip never leaves the seam, and it sits above every other layer. If a graphic crowds it, move the graphic. (untested on ivory)
  Why: the eye already rests there, and a chip that shifts to make room splits the eye. Met: graphics stay inside y 120-880, and the chip is lit on takeovers too.
- **With `full_face` on, measure the shirt spot on stills. Never copy a donor height, and never move the chip onto his face.** [Ours]
  Why: his framing is tight, with the chin at 1575-1680 of a 9:16 crop, and donor defaults land on his mouth.
  Met: the chip clears the mouth and chin on stills from every full-face beat. A spot too low is flagged, not hidden.
- **The chip stays inside x 60-1020.** [Ours]
  Why: that is ivory's safe width. Met: the widest chip in the table fits.

## Build and check

No caption tool or `.srt` writer exists yet. Each check below reports UNVERIFIED until Phase 7, and the handoff lists `.srt` as not built. [Ours]

- **Emit a line table with every render.** Start, end, text and y for every chip, tied to its caption inputs. [Ours]
  Why: the checks read it, and a stale table proves nothing. Met: the table matches this exact render, spot-checked against rendered frames.
- **Baked layer as the look, `.srt` always.** Native text only if hand diffs show he edits captions. [Ours]
  Why: the look has to survive into CapCut. Met: both files ship with the draft.
- **Build the final on the publish grid and re-run every caption check on that file.** [Ours]
  Why: frame snaps at 30 fps prove nothing at 60 fps. Met: the checks name the exact publish file.

## Trial ideas, off until Chase says yes

- A short black title box at the top of the upper panel, with chips staying on the seam. (untested on ivory)
  Copy the form, not the wording he first rejected.

## Open decisions

- **Caption chunk length.** Chase's habit is roughly 2 s. The donor is 0.7 s, the median in STYLE.md.
  Whichever he picks sets words per chip. The look table above still follows the donor side.

## Flags for Chase

- STYLE.md's measured 2-frame lead stays active. The game plan's Phase 7 proposes no early chip, which is his call.
- With `full_face` on: STYLE.md says full-face gets a "serif title or chip". Until he rules it is one or the other. If both can sit together, the planned gap goes away.
