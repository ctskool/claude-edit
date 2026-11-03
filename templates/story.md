# Story and cut

The spine applies these rules to Chase's raw before any template runs. They decide which lines survive, never how they look.
Settle the story before the graphics. [Ours] (untested on ivory)
His tight cut is block selection, not splicing, so most decisions are word ranges in `drops.json`.
Tags name each rule's source. House standards in `templates/HOUSE.md` apply here too.
Pruned 2026-11-02: proof-before-conclusion (his news hooks open on the conclusion), the hook-take picker (Claude can't hear a read), and two rules that repeated 1 and 6 went.

## Words from `tools/rawcut.py`

- **Take:** one OBS file. **Session:** all takes back to back on one timeline.
- **`words.txt`:** every word with its index and session time.
- **Hints:** `filler`, `repeat` and `restart?`, printed by `transcribe`. A hint is a prompt, never a kill.
- **`drops.json`:** what you write. `{"words": [[i, j]], "secs": [[a, b]]}`, inclusive word ranges and session-second ranges.
- **`edit.txt`:** the kept script from `cut`. `||` marks a big jump. **Keeps:** kept frame ranges, always in session order.
- **Joins:** printed by `times`. BIG means a visible face-cam jump. Every dropped range makes one.
- `cut` already removes pauses, breaths, head and tail. Short pauses stay by default, like his own edits. Do not drop those by hand.

## The rules

1. **Relevant is not necessary.** A line survives only if the viewer needs it now. (untested on ivory)
   Why: good-to-know lines are how a short gets long.
   Met when: each sentence in `edit.txt` passes "does the viewer need this now?" Runtime is what that leaves, never a target.

2. **Every early promise is paid.** (untested on ivory)
   Why: an unpaid promise reads as clickbait.
   Met when: each promise in the first 8 s is listed with the line that pays it. An unpaid one is flagged, never covered by a graphic.

3. **Filmed order by default. A move is a named proposal.** [Ours] (untested on ivory)
   Why: moves orphan connectives and break continuity of energy. `drops.json` can only remove, so a move also needs a tool change.
   Met when: keeps run in session order, and any move sits in the report with its exact lines.

4. **Keep the last complete take of a line, unless an earlier one is clearly better.** [Ours]
   Why: this matched his take choices on both test raws. Claude can't hear a read, so a hook take that sounds different stays for his ear.
   Met when: each dropped range names its reason: a failed take, false start, repeat, aside, or the numbered rule here. Every `restart?` was read, since some are deliberate.

5. **No surgery for a wording nit.** A filler inside a flowing phrase stays. (untested on ivory)
   Why: every drop makes a BIG join the template must cover, and the join is the bigger defect.
   Met when: no one-word drop sits inside a phrase. `filler` hints at a line's edge may go.

6. **Keep the strongest statement of each claim.** Echoes go, and the weaker line before a stronger one goes first. (untested on ivory)
   Why: a second statement adds runtime, not value. A second demo that shows nothing new is an echo too.
   Met when: no claim repeats, except a landing line that closes an argument or a deliberate back-to-back repeat.

7. **Recaps, optional asides and hype lines are listed as optional trims.** [Ours] (untested on ivory)
   Why: they pass a first read, then come out in review. The base cut stays fixed, and a template takes trims before graphics.
   Met when: each sentence that only says where we are, offers a side road, or urges with nothing new is listed with its exact line. The filmed close is never listed.

8. **Every connective and pointer still lands.** (untested on ivory)
   Why: a "because", "but" or "this" whose line was dropped hangs off nothing.
   Met when: each sentence's first words in `edit.txt` point at a line that survived. Read the next kept line before any drop.

9. **Endings land.** Never end a kept line on a rising comma. Keep the filmed close. Never build a sign-off. [Ours] (untested on ivory)
   Why: a rising end sounds cut off, and an assembled sign-off is audible.
   Met when: a list tail said in the same breath stays to where the voice falls.
   Only a pause of 200 ms or more, after a falling word, lets it go. Claude cannot hear a fall, so each case is flagged for his ear.

## The story read-through

Runs once per raw, from `session` through `render`. No separate retention re-cut. [Ours] (untested on ivory)
Why: a requested retention pass removed one video's conclusion and hurt its coherence.

1. Run `session`, then `transcribe`. Read the full script and Chase's notes. Write the hook and the takeaway in one line.
2. Map each beat he asked for or scripted to a take. A beat with no take is a pickup: flag it, never invent it.
3. Write `drops.json` and run `cut`.
4. Give one fresh reader, a new subagent with no other context, the prose block of `edit.txt` and these rules. Findings quote exact lines. (untested on ivory)
5. Judge each finding against the rules. Change `drops.json`, or file a named proposal.
6. List spoken claims the footage can show: a time, price, count or version. Check the frames. (untested on ivory)
   If they disagree, reconcile date, version, units and scope first. Still disagreeing: flag it for Chase, never hide it. [Ours]
7. Run `cut`, then `verify`. Read its printed lines, since it exits 0 either way. There is no second round. [Ours]
   MISSING, EXTRA and PAUSE get fixed in `drops.json` or flagged. A CHANGED that is only a name or spelling mishear is logged with both spellings and does not block.
8. Run `render`, then `times`.
9. Pending his answer: stop after `cut.mp4` for a one-minute phone listen until ivory and the spine lock. [Ours]
10. Hand BIG joins to the template, whose layout rule sets the cover. BIG joins too close to cover come back here as a named problem, before graphics. [Ours]

## What the cut report names

Met when: he can correct a wrong read in one word, before graphics spend anything. (untested on ivory)
- The hook and takeaway Claude read, and which take opens the video.
- Each cut sentence he may want back, and borderline keeps as a list.
- Each early promise and its payoff, plus any pickups and proposed moves.
- Joins and BIG joins, with the amount removed at each.
- Listening: UNVERIFIED until Chase listens to the takes, joins and tails. `verify` proves words are present, not how they sound.
- Each optional trim, with its exact line, and every `verify` mishear with both spellings.

## Trial ideas, off until Chase says yes

- A join recipe: waveform plus transcript, whole words, a very short audio crossfade. Compare with `rawcut.py`. (untested on ivory)
- End a shot before the eyes drop. (untested on ivory)
- Spoken notes left in a raw as a free brief. (untested on ivory)

## Open decisions, never decide these

- Tail padding: he compares 0.13 and 0.23 by ear. `--pad-out` is the only tail flag, and `cut` keeps its 0.10 default until he rules.
  How 0.13 and 0.23 map to that flag is not traced yet. Tighter join limits stay out until then.
- Hook line moves: rule 3 stands. A hook move stays a named proposal, and the question stays open.
- The one-minute cut listen: step 9 waits on his answer.
- Optional trims: whether recaps and asides stay in the base cut as listed trims, or get dropped.
