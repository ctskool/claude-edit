"""Render a charcoal (16:9 long-form) video slice by slice and join the slices: the software-only renderer (libx264),
kept as it was on 2026-11-11 when render_slices.py moved to the GPU. Use it on a machine without an NVIDIA card. Its slices
(work/<id>/slices/<res>) do not join with the GPU renderer's (slices/nv-<res>).

A slice is one scene (a long face/screen shot is divided into pieces of about 22 s by kit.mjs shots()). A full
`node tools/build.mjs` writes full/tools/slices.json with a key per slice that changes only when that slice's picture
changes. Rendered slices are kept in work/<id>/slices/<res>/<key>.mp4 and re-used by any later run, so after a note
only the slices it touched are rendered, and a timing change (tools/retime.json) re-uses every later slice as it is.

Two routes, chosen per slice:
  footage  a slice that is only his footage (camera full frame, or screen full frame with the face window still):
           built by ffmpeg straight from raw/cut.mp4 or raw/cam_cut.mp4, no browser. slices.json marks these `ff`.
           Measured 2026-11-11: about 137 fps at 1080p against 16-18 fps through HyperFrames, same picture
           (reports/2026-11-11-render-speed). The encoder settings are HyperFrames' own, so both kinds join by copy.
  page     everything else (designed scenes): `build.mjs --range` + `hyperframes render`, as before.

Usage (from the project root):
  python templates/charcoal/build_kit/render_slices_x264.py work/<id> --rev r2 [--workers 2] [--res 4k] [--dry] [--no-ff]

Writes work/<id>/out/<id>-<rev>.mp4 (slices stream-copied under the full voice track) and <id>-<rev>-chapters.txt.
--dry lists what would render and stops. --no-ff sends every slice through the page route. It takes tools/gpu_lock.py, so a second
render waits its turn. The project needs the slice build (slices.json), which every project made from this kit has.
"""
import argparse, json, os, queue, subprocess, sys, threading, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import gpu_lock, qos_watch

from render_slices import frames, run, worker_dir

HERE = Path(__file__).resolve().parent
# HyperFrames 0.9.13's encoder arguments (read from its running ffmpeg and the x264 options in a rendered slice).
# -video_track_timescale 15360 matters: with another timescale the joined file's timestamps are wrong.
X264 = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-bf', '0',
        '-x264-params', 'aq-mode=3:aq-strength=0.8:deblock=1,1:colorprim=bt709:transfer=bt709:colormatrix=bt709']
TAGS = ['-colorspace:v', 'bt709', '-color_primaries:v', 'bt709', '-color_trc:v', 'bt709', '-color_range', 'tv',
        '-video_track_timescale', '15360', '-pix_fmt', 'yuv420p', '-movflags', '+faststart']


def raw_time(t, holds):
    """A time of the project (with its added and removed stretches) -> the time of raw/cut.mp4 (as tools/make_clips.py)."""
    c = 0
    for at, d in sorted(holds):
        if t >= at + c + d - 1e-6: c += d
        elif t > at + c + min(d, 0): return at
        else: break
    return t - c


def facewin_stills(H, place, win, radius, K, edge=''):
    """The window's rings + shadow (full frame, transparent) and its rounded-corner mask, drawn once by headless Chrome."""
    d = H / 'slices' / '_facewin' / f'{K}x'
    ring, mask = d / f'ring-{place}.png', d / f'mask-{place}.png'
    if not (ring.exists() and mask.exists()):
        subprocess.run(['node', str(HERE / 'facewin_assets.mjs'), str(d), place, str(win['x']), str(win['y']), str(win['scale']), str(radius), str(K), edge],
                       check=True, capture_output=True)
    return ring, mask


def ff_slice(H, FULL, s, K, cfg, holds, out, log):
    """One footage slice with ffmpeg: the footage full frame; for a screen, the face window (assets/face.mp4) on top."""
    f = s['ff']; n = s['frames']
    cx, cy, cw, ch = f['crop']
    src = H / 'raw' / ('cut.mp4' if f['src'] == 'screen' else 'cam_cut.mp4')
    # tpad: the very last slice can want a frame more than the raw file holds; repeat its last frame rather than fail
    pre = 'fps=30,tpad=stop_mode=clone:stop_duration=1,' + ('' if (cx, cy, cw, ch) == (0, 0, 3840, 2160) else f'crop={cw}:{ch}:{cx}:{cy},')
    cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', f"{raw_time(f['t0'], holds):.3f}", '-i', str(src)]
    top = (1080 - f['h']) // 2
    base = pre + f"scale={1920 * K}:{f['h'] * K}:flags=lanczos" + (f",pad={1920 * K}:{1080 * K}:0:{top * K}:color=0x0d0d0c" if f['h'] != 1080 else '')
    if not f['win']:
        cmd += ['-vf', base + ',format=yuv420p']
    else:
        w, h = round(480 * f['win']['scale']), round(600 * f['win']['scale'])
        ring, mask = facewin_stills(H, f['place'], f['win'], cfg['face']['radius'], K, cfg['face'].get('ring', ''))
        # the page shows face frame (slice's first frame + n) on output frame n: seek face.mp4 to that exact frame
        cmd += ['-ss', f"{max(0, s['frame0'] / 30 - 0.008):.4f}", '-i', str(FULL / 'assets' / 'face.mp4'), '-loop', '1', '-i', str(ring), '-loop', '1', '-i', str(mask)]
        fc = (f"[0:v]{base}[bg0];"
              f"[2:v]scale={1920 * K}:{1080 * K}:flags=lanczos,format=yuva444p,scale=out_color_matrix=bt709:out_range=tv[ring];"
              f"[bg0][ring]overlay=0:0:format=yuv420:shortest=0[bg];"
              f"[1:v]setpts=PTS-STARTPTS,scale={w * K}:{h * K}:flags=lanczos,format=yuv444p[f0];"
              f"[3:v]scale={w * K}:{h * K}:flags=lanczos,format=gray[m];"
              f"[f0][m]alphamerge[face];"
              f"[bg][face]overlay={f['win']['x'] * K}:{f['win']['y'] * K}:format=yuv420,format=yuv420p[v]")
        cmd += ['-filter_complex', fc, '-map', '[v]']
    cmd += ['-frames:v', str(n), '-r', '30', '-an', *X264, '-threads', '16', *TAGS, str(out)]
    return run(cmd, FULL, log)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('run', help='work/<id>'); ap.add_argument('--rev', required=True); ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--res', default='', help='hyperframes --resolution preset, e.g. 4k'); ap.add_argument('--dry', action='store_true')
    ap.add_argument('--no-ff', action='store_true', help='send every slice through the page route')
    a = ap.parse_args()
    H = Path(a.run).resolve(); FULL = H / 'full'
    cfg = json.loads((FULL / 'tools' / 'video.json').read_text()); FPS = cfg.get('fps', 30)
    K = {'': 1, '4k': 2}[a.res]
    r = subprocess.run(['node', 'tools/build.mjs'], cwd=FULL, capture_output=True, text=True)
    if r.returncode:
        sys.exit('the full build failed, nothing rendered:\n' + (r.stderr or r.stdout)[-1500:])
    slices = json.loads((FULL / 'tools' / 'slices.json').read_text())
    hp = FULL / 'tools' / 'holds.json'
    holds = json.loads(hp.read_text()) if hp.exists() else []
    store = H / 'slices' / (a.res or '1080'); store.mkdir(parents=True, exist_ok=True)
    pages, footage = queue.Queue(), queue.Queue()
    for s in slices:
        s['mp4'] = store / f"{s['key']}.mp4"
        if frames(s['mp4']) != s['frames']:
            (footage if s.get('ff') and not a.no_ff and FPS == 30 else pages).put(s)
    todo = list(footage.queue) + list(pages.queue)
    print(f"{len(slices)} slices: {len(slices) - len(todo)} re-used, {footage.qsize()} footage + {pages.qsize()} page to render "
          f"({sum(s['frames'] for s in todo) / FPS:.0f} s of video)", flush=True)
    for s in todo:
        print(f"  {s['id']:10s} {s['start']:8.2f}-{s['end']:8.2f}  {'footage' if s.get('ff') and not a.no_ff else 'page'}", flush=True)
    if a.dry:
        return
    # The clips the page route needs (kit.mjs clipTag), at this render's size: every clip with --no-ff, else only designed scenes'.
    if (FULL / 'tools' / 'make_clips.py').exists() and json.loads((FULL / 'tools' / 'clips.json').read_text()):
        r = subprocess.run([sys.executable, 'tools/make_clips.py'] + (['--all'] if a.no_ff or FPS != 30 else []), cwd=FULL, capture_output=True, text=True,
                           env={**os.environ, 'CLIP_SCALE': '2' if a.res == '4k' else '1'})
        print('clips: ' + (r.stdout.strip().splitlines() or ['none'])[-1], flush=True)
        if r.returncode:
            sys.exit('make_clips.py failed, nothing rendered:\n' + (r.stdout + r.stderr)[-1500:])
    bad = []; t00 = time.time()
    qos_watch.start()               # keep Windows from parking the Chrome workers on the efficiency cores

    def done(s, tmp, rc, t0, route):
        got = frames(tmp)
        if rc == 0 and got == s['frames'] + 1:      # one frame over: drop it without re-encoding
            t2 = tmp.with_suffix('.trim.mp4')
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(tmp), '-frames:v', str(s['frames']), '-c', 'copy', str(t2)], check=True)
            os.replace(t2, tmp); got = frames(tmp)
        ok = rc == 0 and got == s['frames']
        if ok:
            os.replace(tmp, s['mp4'])
            seed = s['mp4'].with_suffix('.seed')
            if seed.exists(): seed.unlink()
        print(f"{s['id']:10s} {got}/{s['frames']} frames  {time.time() - t0:5.0f}s  {route:7s} {'ok' if ok else 'FAILED rc=' + str(rc)}", flush=True)
        if not ok: bad.append(s['id'])

    def footage_work():
        while True:
            try: s = footage.get_nowait()
            except queue.Empty: return
            log = store / f"{s['id']}.log"; t0 = time.time()
            if log.exists(): log.unlink()
            tmp = store / f"_{s['key']}.mp4"
            done(s, tmp, ff_slice(H, FULL, s, K, cfg, holds, tmp, log), t0, 'footage')

    def page_work(i):
        w = None
        while True:
            try: s = pages.get_nowait()
            except queue.Empty: return
            if w is None: w = worker_dir(H, FULL, i)
            log = store / f"{s['id']}.log"; t0 = time.time()
            if log.exists(): log.unlink()
            tmp = store / f"_{s['key']}.mp4"
            rc = run(['node', 'tools/build.mjs', f"--range={s['start']},{s['end']}"], w, log)
            if rc == 0:
                rc = run(f'npx hyperframes render --quiet{" --resolution " + a.res if a.res else ""} -o "{tmp}"', w, log)
            done(s, tmp, rc, t0, 'page')

    # footage first (ffmpeg, two at a time: more did not add speed), then the pages
    for group in ([threading.Thread(target=footage_work) for _ in range(min(2, footage.qsize()))],
                  [threading.Thread(target=page_work, args=(i + 1,)) for i in range(min(a.workers, pages.qsize()))]):
        [t.start() for t in group]; [t.join() for t in group]
    if bad:
        sys.exit('failed slices: ' + ', '.join(sorted(bad)))
    if todo:
        print(f'rendered {len(todo)} slices in {time.time() - t00:.0f}s', flush=True)
    lst = store / f'list-{a.rev}.txt'
    lst.write_text(''.join(f"file '{s['mp4'].name}'\n" for s in slices))
    out = H / 'out' / f'{H.name}-{a.rev}.mp4'; out.parent.mkdir(exist_ok=True)
    total = sum(s['frames'] for s in slices)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-i', str(FULL / 'assets' / 'voice.m4a'),
                    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'copy', '-t', f'{total / FPS:.4f}', '-movflags', '+faststart', str(out)], check=True)
    got = frames(out)
    print(f'joined {out}: {got} frames, expected {total}' + ('' if got == total else '  <-- FRAME COUNT MISMATCH'), flush=True)
    RETIME = json.loads((FULL / 'tools' / 'retime.json').read_text())
    mapt = lambda t: t + sum(add for at, add in RETIME if t > at + 1e-6)
    stamp = lambda t: f'{int(t) // 3600}:{int(t) % 3600 // 60:02d}:{int(t) % 60:02d}' if t >= 3600 else f'{int(t) // 60}:{int(t) % 60:02d}'
    secs = json.loads((FULL / 'tools' / 'sections.json').read_text())['sections']
    chapters = out.with_name(out.stem + '-chapters.txt')
    chapters.write_text(''.join(f"{stamp(mapt(s['start']))} {s['title']}\n" for s in secs), encoding='utf8')
    print(f'chapter list: {chapters}', flush=True)


if __name__ == '__main__':
    if '--dry' in sys.argv: main()
    else:
        with gpu_lock.held('long-form render ' + ' '.join(sys.argv[1:])[:60]): main()
