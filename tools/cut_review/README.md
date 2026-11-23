# Cut review

Chase watches and listens to the tight cut and fixes it by hand before anything is rendered. Laid out like CapCut on purpose [Chase, 2026-11-12: "very simplistic", picture up top, "very easy to look at bars" at the bottom]. Standing step since 2026-11-12: after its first real video he said it replaces the phone-copy listen of the cut.

While the page is open the server renders the machine's cut in the background at low priority (`draft.log`): `cut.mp4` and `cam_cut.mp4` as a draft, joined from pieces of 20 s at most kept in `raw/_pieces`. Approve stops that render if it is still going and starts the real one, which re-makes only the pieces his changes touched. `--no-draft` turns the background render off. `_pieces` holds a second copy of the cut's picture; delete it when the video is delivered.

```
python tools/cut_review/core.py work/<id>/raw --video   # right after `rawcut.py session`, in the background
python tools/cut_review/server.py work/<id>/raw         # after `cut` and `verify`, in place of `render` (PORT, default 4765)
```

The first line makes a small copy of each take's camera (540 px, about 10x real time on the GPU) so the picture is ready by the time the cut is. The server makes it itself if it is missing; sound and trimming work while it does. Add a `.claude/launch.json` entry per video so the page opens in the Browser pane.

## The page

- **Top:** his camera, following the sound.
- **Bottom:** one row of clips, one per kept stretch, with the waveform inside and his words under it. An amber edge is one he moved.
- **Trim:** drag a clip's edge. Dragging outward pulls back what the cut removed. The picture shows the frame at the edge while he drags, and the playhead is left a second before the join so Space plays it.
- **Q / W:** trim the clip's start / end to the playhead, as in CapCut. **S** (or Ctrl+B) splits at the playhead. Click a clip and press **Del** to remove it.
- **Space** plays, arrows move a second, scroll moves the timeline, Ctrl+scroll zooms. Ctrl+Z undoes.
- **Approve cut** writes his clips as the cut and starts `rawcut.py render`, which cuts the screen take and the camera file from them in one pass. The button shows when both files are done. `--no-render` only writes the cut.

The sound is read from `a48.wav` through the current clips with the same 8 ms fades `render` writes, so what he hears is what the render will sound like. The picture is a preview: it lands a few frames late at a join.

No side panels and no notes box: what he cannot fix on the page (a different take, a moved line) he says in chat.

## Files in `raw/`

| File | What it is |
|---|---|
| `cut_review.json` | His review: the machine cut it started from, his clips, when he approved. Saved on every change |
| `edl.json` | The cut `render` uses. Carries `"reviewed": true` after an approval |
| `edl.auto.json`, `cut_words.auto.json`, `cuts.auto.json` | The machine's cut, kept beside his |
| `review_cam_<n>.mp4` | The small camera copy for take n. Safe to delete |
| `render.log` | The render his Approve click started |

Approve also rewrites `cut_words.json`, `cuts.json` and `edit.txt` to match. A join he did not touch keeps its kind, BIG flag and RUN-ON warning; one he made is kind `hand`.

## After a re-cut

A new `rawcut.py cut` writes a fresh `edl.json` without his changes. Opening the page again, or `python tools/cut_review/core.py work/<id>/raw`, carries them over: what he added is added, what he removed is removed. `render` refuses to run until one of the two has happened. Where the new cut moved an edge he had also moved, the carried join can come out wrong, so the page tells him to listen to his amber edges once more.

## Not built

- Choosing a different take or moving a line: he says it in chat, then `drops.json` and a new `cut`.
- A camera that was mounted sideways (1102-1) shows sideways. Recent camera files are upright.
- The screen recording is not shown. It is cut on the same frames at Approve.
