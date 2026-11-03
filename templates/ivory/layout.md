# Ivory layout

Two layouts: split, full-graphic. A third, full-face, exists only when `full_face` is on. Chase's rules win every conflict.
Format: rule, why, then Met (how to tell it held). "(untested on ivory)" means ivory has not proven it.
All STYLE.md layout numbers here are at 1080x1920. Publish is 2160x3840 at 60 fps.

## The `full_face` setting

- **Full-screen shots of just his face are off by default.** `allow_full_face = template.full_face OR Chase's request for this edit`. Ivory's `template.json` says false. [Chase]
  Why: "unless I specifically say a template or tell it to do a full screen edit, I don't want full screen edits where it's just my face."
  Met: `RUN.md` and `plan.json` carry the result and its source, the template or his exact words.
- **Skipping a page or running auto or lock mode grants nothing.** [Chase] Why: only a template or his words turn it on.
  Met: with no opt-in and no words from him, it reads false.
- **With `full_face` off, only split and full-graphic exist.** Every row or rule here marked `full_face` on does not apply. Plan nothing from it. [Chase]
  Why: his face stays in the bottom half, and only the explainer takes the whole frame.
  Met: no beat has `layout_hint` `face`, and `assets/face_full.mp4` is not in the composition. `tools/motionlint.py --pack editorial` errors on it.
- **With `full_face` on, the full-face rows and rules apply as written.** [Chase] Why: he did not ban them, and a template that opts in needs them.
  Met: each full-face beat sits on a trigger in the table below.

## The layouts

| layout | use it when the line... | length | on screen | tag |
|---|---|---|---|---|
| split (default) | explains or points at the thing on screen ("this", "here", "it lets you..."), setup lines, connective tissue. With `full_face` off, also his opinion or emphasis, direct address, a rhetorical question, the payoff and the CTA | the soft 8 s guardrail below | panel y 0-960, face cam y 960-1920 | [Chase] |
| full-graphic | needs the whole frame: a name reveal, A vs B, a list of 3+, a big number or stat, a before-after, a demo clip | 2-4 s | face hidden, chip at y ~1480-1570 | [Chase] |
| full-face, `full_face` on only | is his opinion or emphasis ("honestly", "definitely", "this is the one"), direct address, a rhetorical question, the payoff, the CTA, or any visible jump cut | 1-2.5 s | plain `assets/face_full.mp4` punch-in, serif title or chip on the shirt | [Chase] |

- **With `full_face` off, opinion, payoff and CTA stay split.** [Chase] Why: a full-screen face rarely looks good.
- **A top half that only repeats his words is banned.** [Chase] 2026-11-01, on b10, b13 and b23-b28 of 1030-2: "literally anything is better than just essentially relaying captions as the split screen." The caption already says the words. An opinion, payoff or reaction line stays split, and its top half shows something real: a capture, his own clip, the post being discussed, or a returning graphic.
  Met: no beat's top half is only his words in big type, and no two quiet panels ever run back to back.
  A quiet panel is the rare exception: a CTA, or a pure opinion hook with nothing to show. Nothing on screen may read as proof of a claim no source supports. A hedged legal or factual claim shows the neutral thing it is about, keeps its hedge visible, and leaves the claim in the caption.
  Met: the panel holds that one line and no content graphic. The HUD keeps running and the chip stays on the seam.
- **Layout math is new for ivory.** [Ours] Why: his raw is a split composite.
  Met: the panel comes from the build and the face comes from a crop of his real footage.

## Switching

- **Switch on what is said, never on a quota. More switching than reference B, every switch earned by its line.** [Chase] Why: he called the first finals too static.
  Met: each switch names its line in `layout_hint`.
- **No two switches within about 1.2 s.** [Chase] Why: closer reads as a flicker.
  Met: the switch list has no gap under ~1.2 s. With `full_face` on, this sets a full-face's real floor, since in and out are two switches.
- **Soft 8 s guardrail.** [Chase] Why: a 27 s opening split read as too static.
  Met: past ~8 s, look for a line that earns a break (a reveal, a list item, an opinion). Do not invent one.
  `tools/gates.py --pack editorial` warns only, and its layout and band reads hold on a 1080x1920 file only.
- **Vary the order.** [Chase] Why: a fixed pattern reads as a machine. Met: never mechanically split, graphic, split, graphic.
- **Layout switches are hard cuts.** [Chase] Why: the switch is the move. Met: no dissolve, zoom ramp, slide or whip between layouts.

## Where a switch lands

Priority: Chase's two landing spots first. The timing rules after them only fine-tune a switch on those spots.
If one would move a switch off his spots, leave the switch and flag it. A BIG join is the one exception, since his jump-cut rule covers it. [Ours]

- **On the stressed word or a sentence boundary.** [Chase] Why: picture and word arrive together.
  Met: every switch sits on one of those two places. The stressed word is the one the line's point turns on: a read from the words, not a measurement. [Ours]
- **With `full_face` off, every visible jump cut gets a takeover or a punch-in inside the bottom half only, about 1.08 scale.** [Chase] Why: it hides the jump and his face stays in the bottom half.
  Met: `times` lists no BIG join left bare. Each is a takeover starting on the join, a join inside a takeover already up, or a split beat starting on the join with a quick punch-in on `assets/face_half.mp4`, as `styles/editorial/STYLE.md` describes.
- **With `full_face` on, every visible jump cut gets a full-face punch-in starting on the join.** [Chase] Why: it hides the jump.
  Met: `times` lists no BIG join left bare, and frames either side of it show a framing change. A join inside a full-face hold is not covered.
  Today's route also accepts a takeover starting on the join, or a join inside a takeover already up, since his face is hidden. [Ours] Flagged for Chase.
- **BIG joins whose covers would each need their own layout switch or punch-in inside ~1.2 s go back to the spine as a named problem, before graphics.** [Ours] Why: covers that close read as a flicker.
  Met: no such pair reaches the plan unnamed. Joins inside a takeover already up need neither, so they stay.
- **Early or on time, never late.** (untested on ivory) Why: a late switch feels laggy.
  Met: about 0-0.08 s before the landing word's onset, snapped once to the output grid.
- **A switch beside a cut goes on the cut.** (untested on ivory) Why: just off it reads as a double cut.
  Met: no layout edge sits within about 0.08 s of a cut.
- **The graphic is there on the switch frame. No empty panel, no gap, no overlap.** (untested on ivory) Why: one frame off shows a bare panel or a panel over his face.
  Met: frame-step every switch. The first element is visible on the graphic's own first frame.

## Frame bands, 1080x1920

| band | where | rule | tag |
|---|---|---|---|
| panel | y 0-960 | ivory #EEEEE7, opaque on every frame, apart from the optional dark hook below | [Ours] |
| graphic safe area | y 120-880, x 60-1020 | all graphic ink, main content centred around y 470 | [Ours] |
| caption chip | centred on the seam, y 960 in split | default ~96 px chip | [Ours] |
| face cam | y 960-1920 | `assets/face_half.mp4` (1280x967), object-fit cover, HARD edge, no fade, no border | [Ours] |
| takeover chip | y ~1480-1570 | on full-graphic only | [Ours] |

- **Real footage and no bottom fade:** `HOUSE.md`. [Chase] Platform bands warn only: `HOUSE.md`.
- **Face files are preview size today.** [Ours] Why: `prep_source.py` makes 1280-wide and 1080x1920 clips at 30 fps, and doubling a number adds no pixels.
  Met: the size STYLE quotes comes from a finished export. No tool yet builds a 2160x3840 60 fps face layer: only a hand route exists, proven on 3 s.

## The seam: two different rows

- **Composed seam: y 960 of 1920, so y 1920 of 3840.** [Ours] Source: STYLE.md. Ivory draws the panel edge and chip here.
- **Raw seam: near y 996 of 1920 in his split composites.** Measured per take. [Ours] It only sets the face crop (`--face-top 0.52`).
- **Keep the two apart.** [Ours] Why: a check on the wrong row reads a false result, and a wrong seam misplaces the chip and every band.
  Met: chips measure on the composed seam, crops on the raw seam. Chase sees the 4K seam on a fixture take before it counts as settled.

## Nothing on the face or hair

- **Nothing sits on his face or hair.** `HOUSE.md`. Hair top is measured per shoot, tallest pose included, and the gap to the chip's bottom edge is logged. [Ours]
- **With `full_face` on, the full-face title or chip sits on the shirt.** [Chase] Why: never over the eyes or mouth.
  Met: it does not touch his face. Re-measure each shoot. If the spot falls below y 1620, his rule wins and the band warning is logged. One or the other, until he rules.

## The HUD

- **The chip holds, the graphic gives way:** `captions.md`.
- **The HUD carries across layouts.** [Chase] Why: HUD continuity is a Keep rule.
  Met: after a switch back, the HUD returns in its running state, never reset. With `full_face` on, 1022-2 took it off the frame on full-face [Ours].

## Hook frame

- **The hook opens split, its visual on frame 0.** (untested on ivory) Why: it shows him and the thing at once.
  Met: frame 0 is split with its first element up, unless the `full_face` on rule below applies.
- **With `full_face` off, a pure opinion hook opens split on a quiet top panel.** [Chase] Why: his face stays in the bottom half.
  Met: a first line of opinion or direct address with nothing to show has one big serif line up on frame 0.
- **With `full_face` on, a pure opinion hook follows Chase's rule.** [Chase] Why: his switching rule wins.
  Met: a first line of opinion or direct address with nothing to show may open full-face with a serif title.
- **The dark hook is STYLE's option (#141413, first 2-3 s), unused by default.** [Ours] Why: it sits close to a banned look, so Chase rules on it.
  Met: if he asks for it, the rest stays ivory and no faint grid sits on it.

## CTA

- **With `full_face` off, the CTA stays split.** [Chase] Why: his face stays in the bottom half, and a quiet panel leaves the CTA alone.
  Met: the CTA plays on `assets/face_half.mp4` under a quiet top panel with one big serif line in his own words, with the chip on the seam.
- **With `full_face` on, the CTA is full-face.** [Chase] Why: his rule lists it there.
  Met: the CTA plays on `assets/face_full.mp4`, with a serif title or chip on the shirt.
- **No CTA components.** [Ours] Why: they are not ivory. Met: no thread, button, arrow or click card.
- **The CTA shows only his words, starts clean and holds to the last frame.** (untested on ivory) Why: anything added is a promise he never made, a leftover graphic fights it, and the last frame is what a paused or looping viewer sees.
  Met: every word on screen in the CTA is his, the last content graphic ends by the CTA's first word, and nothing exits before the final frame. With `full_face` on, a CTA over 2.5 s: his full-face length wins, so flag it.
- **No sound on the CTA hold.** [Chase] Why: nothing should compete with the CTA. Met: the cue list has none there.

## Trial ideas, off until Chase says yes

- **End a shot before his eyes drop.** (untested on ivory)
- **Short black title box at the top of the upper panel, chips on the seam.** (untested on ivory) Copy the form, not his wording.
- **Use the empty space at the top of split.** (untested on ivory) (source unconfirmed)
- **Hook-height check.** (untested on ivory) His hook sat too high.
- **A caption doc matching the CTA word.** (untested on ivory) (source unconfirmed)

## Not settled, never decide here

- HUD height: STYLE says top of panel, its scene notes clear a strip at y >= ~780, and 1022-2's strip sits at y 783-897.
- HUD on a new short: what it counts, when it first appears, and whether every short needs one.
- With `full_face` on: whether a takeover also counts as a jump-cut cover, and whether title and chip can share a full-face beat. The dark hook. Full open list: `HOUSE.md`.
