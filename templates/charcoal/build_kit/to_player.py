"""Load one rendered charcoal (16:9) mp4 into the beat review player (tools/beat_review_v2, ?skin=wide).

The player was built for vertical shorts rendered beat by beat. It only needs a few files, so this writes them:
  work/<id>/beat/stitched/review-<sha16>/review.mp4   (hard link or copy of the render)
  .../beats.lock.json and stitch.json                  (beats as contiguous frame ranges, one per kept sentence)
  work/<id>/beat/current.json                          (which picture is current)
  work/<id>/v2/editorial/plan.json                     (the spoken line of each beat)
Notes then land in work/<id>/notes.jsonl, bound to the nearest word of raw/cut_words.json.

This is a stand-in until the player has a real long-form path. It deliberately writes no ownership.json, check
reports or sound.json, so Approve stays disabled and no final render can start from this load: his approval is
taken in chat, and the final is render_slices.py --res 4k. Sound cues do not show in the player from this load.

Usage (from the project root):
  python templates/charcoal/build_kit/to_player.py work/<id> work/<id>/out/<id>-r1.mp4 --rev r1 [--until 128.72]
--until loads only the first seconds (a pilot of one section); leave it out for the whole video.
Serve it with a .claude/launch.json entry like 1109-fable's (python -B tools/beat_review_v2/server.py
work/<id>/v2/editorial, its own PORT) and open http://localhost:<port>/?skin=wide.
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path

# Where the face window is over time (written by a full `node tools/build.mjs`): a beat spoken while it is in the
# corner is marked full-graphic, otherwise split.
FACES = []


def corner_at(t):
    place = FACES[0]['place']
    for f in FACES:
        if f['t'] <= t + 0.3: place = f['place']
    return place == 'corner'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run', help='work/<id>'); ap.add_argument('mp4'); ap.add_argument('--rev', required=True)
    ap.add_argument('--until', type=float, default=1e9)
    ap.add_argument('--sentences', action='store_true', help='one beat per sentence even if full/tools/segments.json exists')
    ap.add_argument('--no-retime', action='store_true', help="raw/edit.txt is already today's cut (he re-cut in the cut review page and --refresh-media --keep wrote retime.json from cut0): do not shift its times again")
    a = ap.parse_args()
    H = Path(a.run).resolve(); P = H / 'v2' / 'editorial'; S = H / 'beat'
    FACES.extend(json.loads((H / 'full' / 'faces.json').read_text()))
    mp4 = Path(a.mp4).resolve()
    probe = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries',
                                       'stream=nb_read_packets,r_frame_rate', '-of', 'json', str(mp4)], capture_output=True, text=True, check=True).stdout)['streams'][0]
    num, den = map(int, probe['r_frame_rate'].split('/')); fps = num / den
    total = int(probe['nb_read_packets'])
    if abs(fps - round(fps)) > 1e-6:
        sys.exit(f'player needs a whole frame rate, got {fps}')
    fps = int(round(fps))

    # One beat per kept sentence of the cut, up to --until.
    lines = []
    for ln in (H / 'raw' / 'edit.txt').read_text(encoding='utf8').splitlines():
        m = re.match(r'\[\s*([\d.]+)\]\s*(.*)', ln)
        if not m:
            if lines: break
            continue
        t = float(m.group(1))
        if t >= a.until: break
        lines.append((t, m.group(2).replace('|| ', '').replace('||', '').strip()))
    # The cut's own times -> today's (full/tools/retime.json: pauses added after the sections were written).
    rt = H / 'full' / 'tools' / 'retime.json'
    RETIME = json.loads(rt.read_text()) if rt.exists() and not a.no_retime else []
    mapt = lambda t: t + sum(add for at, add in RETIME if t > at + 1e-6)
    # full/tools/segments.json ([[start, title], ...], starts being sentence starts of raw/edit.txt): one beat per
    # segment (one idea, 10 to 40 s) instead of one per sentence. Sentences are too fine a unit for long-form notes;
    # a note still binds to the exact word under the playhead. --sentences keeps the old list.
    sg = H / 'full' / 'tools' / 'segments.json'
    if sg.exists() and not a.sentences:
        # an entry may carry its own text as a third item (a segment that starts mid-sentence after a removal)
        segs = [(e[0], e[1], e[2] if len(e) > 2 else None) for e in json.loads(sg.read_text(encoding='utf8')) if e[0] < a.until]
        gone = [(at + add, at) for at, add in RETIME if add < 0]                      # stretches removed from the cut
        lines = [(lt, say) for lt, say in lines if not any(g0 - 1e-6 <= lt < g1 for g0, g1 in gone)]
        grouped = []
        assert segs[0][0] - 0.01 <= lines[0][0], 'the first segment must start on the first sentence'
        for i, (t, title, own) in enumerate(segs):
            stop = segs[i + 1][0] if i + 1 < len(segs) else 1e9
            text = own or ' '.join(say for lt, say in lines if t - 0.01 <= lt < stop - 0.01)
            assert text, f'segment {title!r} at {t} starts on no sentence of edit.txt'
            grouped.append((t, f"{title.upper()}  |  {text[:260]}{'...' if len(text) > 260 else ''}"))
        lines = grouped
    lines = [(mapt(t), say) for t, say in lines]
    beats = []
    for i, (t, say) in enumerate(lines):
        start = 0 if i == 0 else round(max(0, t - 0.06) * fps)
        beats.append({'beat_id': f'b{i + 1:02d}', 'start_frame': start, 'say': say,
                      'layout': 'full-graphic' if corner_at(t) else 'split'})
    for b, nxt in zip(beats, beats[1:] + [{'start_frame': total}]):
        b['end_frame'] = nxt['start_frame']
    assert all(b['end_frame'] > b['start_frame'] for b in beats) and beats[-1]['end_frame'] == total

    sha = hashlib.sha256(mp4.read_bytes()).hexdigest()
    folder = S / 'stitched' / f'review-{sha[:16]}'
    folder.mkdir(parents=True, exist_ok=True); P.mkdir(parents=True, exist_ok=True)
    dst = folder / 'review.mp4'
    if not dst.exists():
        try: os.link(mp4, dst)
        except OSError: shutil.copy2(mp4, dst)
    rev = a.rev
    (folder / 'beats.lock.json').write_text(json.dumps({'schema': 1, 'fps': fps, 'total_frames': total, 'duration': round(total / fps, 3),
        'beats': [{'beat_id': b['beat_id'], 'start_frame': b['start_frame'], 'end_frame': b['end_frame'],
                   'plan_start': round(b['start_frame'] / fps, 3), 'plan_end': round(b['end_frame'] / fps, 3), 'layout': b['layout']} for b in beats]}, indent=1), encoding='utf8')
    (folder / 'stitch.json').write_text(json.dumps({'file': 'review.mp4', 'file_sha256': sha, 'composition_rev': rev, 'lock_revision': rev,
        'beats': [{'beat_id': b['beat_id'], 'key': f"{rev}-{b['beat_id']}", 'start_frame': b['start_frame'], 'end_frame': b['end_frame']} for b in beats]}, indent=1), encoding='utf8')
    (S / 'current.json').write_text(json.dumps({'review': {'stitched': folder.name, 'file_sha256': sha, 'composition_rev': rev, 'lock_revision': rev, 'status': 'UNVERIFIED'}}, indent=1), encoding='utf8')
    last = S / 'last_attempt.json'
    if last.exists(): last.unlink()
    (P / 'plan.json').write_text(json.dumps({'beats': [{'id': b['beat_id'], 'say': b['say']} for b in beats]}, indent=1, ensure_ascii=False), encoding='utf8')
    for forbidden in (P / 'ownership.json', P / 'sound.json'):
        assert not forbidden.exists(), f'{forbidden} would arm Approve; remove it'
    print(f'{len(beats)} beats, {total} frames at {fps} fps, picture {sha[:16]} -> {folder}')


if __name__ == '__main__':
    main()
