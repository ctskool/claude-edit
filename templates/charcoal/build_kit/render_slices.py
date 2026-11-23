"""Render a charcoal (16:9 long-form) video slice by slice on the GPU and join the slices.

A slice is one scene (a long face/screen shot is divided into pieces of about 22 s by kit.mjs shots()). A full
`node tools/build.mjs` writes full/tools/slices.json with a key per slice that changes only when that slice's picture
changes. Rendered slices are kept in work/<id>/slices/nv-<res>/<key>.mp4 and re-used by any later run, so after a note
only the slices it touched are rendered, and a timing change (tools/retime.json) re-uses every later slice as it is.

Every slice is written by the same ffmpeg + NVENC command line, so all of them join by stream copy:
  footage  a slice that is only his footage (slices.json `ff`: camera full frame, or screen full frame with the face
           window still). Decoded and cropped on the GPU (NVDEC) straight from raw/cut.mp4 or raw/cam_cut.mp4, encoded
           by NVENC. A slice that needs scaling or the face window comes back to system memory once in between, for the
           same software lanczos and window composite as before; a 4K camera slice never leaves the card. No browser.
  reel     every designed slice whose face window does not move (slices.json `pg`, moves: false): ONE HyperFrames call
           renders them back to back without the window (`build.mjs --reel=`), then each is cut out of that file and
           gets its window from ffmpeg, as a footage slice does. One start-up for all of them instead of one each.
  page     a designed slice whose window moves or fades during it, or any designed slice of a project whose build.mjs
           has no reel mode yet: `build.mjs --range` + `hyperframes render` as before, then through the same encoder.
If the GPU decode stalls, fails or comes up short (it has hung on camera files before), the slice is built again with
software decode, still encoded by NVENC, so the format never changes. Footage runs first, then the browser.

Usage (from the project root):
  python templates/charcoal/build_kit/render_slices.py work/<id> --rev r2 [--res 4k] [--dry] [--jobs N] [--no-reel] [--background]
  python templates/charcoal/build_kit/render_slices.py work/<id> --rev pilot --partial     # a pilot: the sections written so far

Writes work/<id>/out/<id>-<rev>.mp4 (slices stream-copied under the full voice track) and <id>-<rev>-chapters.txt.
--dry lists what would render and stops. --no-reel sends every designed slice through the page route. --background is
for when he is recording: idle priority and one ffmpeg job (a normal run cost a 60 fps NVENC capture 13% of its frames).
It takes tools/gpu_lock.py, so a second render (or a transcription) waits its turn. Before rendering it runs the project's tools/make_clips.py for the clips designed scenes show. A project made before
2026-11-11 whose build.mjs has no reel mode still renders, one HyperFrames call per designed slice. The software-only
renderer (no NVIDIA card, or a project with x264 slices already rendered) is render_slices_x264.py; its slices live in
slices/<res> and do not join with these (slices/nv-<res>).
"""
import argparse, hashlib, json, math, os, queue, shutil, subprocess, sys, threading, time
from pathlib import Path

KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools'))
import gpu_lock, qos_watch

PRIO = 0        # Windows process priority for every ffmpeg and HyperFrames call (--background sets idle)


def run(cmd, cwd, log):
    with open(log, 'ab') as f:
        return subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, shell=isinstance(cmd, str), creationflags=PRIO).returncode

# One encoder for every slice (reports/2026-11-11-render-speed/part-2-gpu.md says how it was chosen): NVENC H.264, preset p4
# with an 8-frame look-ahead, constant quality. cq 19 for screen and designed slices, 17 for his camera full frame: each
# is at least as close to the source as libx264 crf 16 was (mean and worst-frame PSNR and SSIM, 1080p and 4K). The level
# and the rate ceiling are fixed per size: left alone, NVENC caps 1080p at its default level's bitrate, and a header that
# differs between slices would break the stream-copy join. Nothing else here may differ between slices.
def nvenc(K, cq=19):
    return ['-c:v', 'h264_nvenc', '-preset', 'p4', '-tune', 'hq', '-profile:v', 'high', '-rc', 'vbr', '-cq', str(cq), '-b:v', '0',
            '-rc-lookahead', '8', '-bf', '0', '-g', '250', *(['-level', '4.2', '-maxrate', '60M', '-bufsize', '120M'] if K == 1 else
                                                              ['-level', '5.1', '-maxrate', '240M', '-bufsize', '480M'])]


CQ_CAMERA = 17
TAGS = ['-colorspace:v', 'bt709', '-color_primaries:v', 'bt709', '-color_trc:v', 'bt709', '-color_range', 'tv',
        '-video_track_timescale', '15360', '-movflags', '+faststart']
# The reel is only an intermediate: encoded by NVENC so the CPU stays on frame capture, at a quality well above the slices'.
REEL_ARGS = '--gpu --crf 10'
REEL_FRAMES = 9000          # frames per HyperFrames call at most (5 min of designed slices): keeps a failed call affordable


def jsround(x): return math.floor(x + 0.5)


def frames(p):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries', 'stream=nb_read_packets',
                          '-of', 'csv=p=0', str(p)], capture_output=True, text=True).stdout.strip()
    return int(out) if out.isdigit() else -1


def worker_dir(H, FULL, i):
    """A copy of the project for the browser to render from (work/<id>/w<i>): its tools, and its media by hard link."""
    w = H / f'w{i}'
    if w.exists():
        shutil.rmtree(w)
    (w / 'compositions').mkdir(parents=True)
    for f in ('hyperframes.json', 'package.json', 'meta.json'):
        shutil.copy2(FULL / f, w / f)
    shutil.copytree(FULL / 'tools', w / 'tools')
    for src in (FULL / 'assets').rglob('*'):           # hard-link the media, it is large
        dst = w / 'assets' / src.relative_to(FULL / 'assets')
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            try: os.link(src, dst)
            except OSError: shutil.copy2(src, dst)
    return w


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
    tag = '-' + hashlib.sha1(edge.encode()).hexdigest()[:8] if edge else ''   # a changed face.ring draws new stills
    d = H / 'slices' / '_facewin' / f'{K}x{tag}'
    ring, mask = d / f'ring-{place}.png', d / f'mask-{place}.png'
    if not (ring.exists() and mask.exists()):
        subprocess.run(['node', str(KIT / 'facewin_assets.mjs'), str(d), place, str(win['x']), str(win['y']), str(win['scale']), str(radius), str(K), edge],
                       check=True, capture_output=True)
    return ring, mask


def card_stills(H, FULL, card, K):
    """A card slice's page (everything but his footage) and the rounded mask of the footage, drawn once by headless Chrome."""
    page = FULL / card['html']
    name = hashlib.sha1(page.read_bytes() + json.dumps([card[k] for k in ('x', 'y', 'w', 'h', 'r')]).encode()).hexdigest()[:12]
    d = H / 'slices' / '_cards' / f'{K}x'
    bg, mask = d / f'bg-{name}.png', d / f'mask-{name}.png'
    if not (bg.exists() and mask.exists()):
        subprocess.run(['node', str(KIT / 'card_assets.mjs'), str(page), str(d), name, *(str(card[k]) for k in ('x', 'y', 'w', 'h', 'r')), str(K)],
                       check=True, capture_output=True)
    return bg, mask


def slice_cmd(H, FULL, base, win, place, frame0, n, K, cfg, out, gpu, enc=None):
    """One slice. base = dict(file, ss, fps60, crop, h, size, codec): the picture under the window (footage, or a stretch
    of a rendered page). win = where the face window (assets/face.mp4, from frame `frame0`) goes on top, or None.
    gpu: decode, crop and scale on the card. The window itself is laid on in system memory either way (see below)."""
    W, Hh = 1920 * K, base['h'] * K
    card = base.get('card')            # his footage sits in a rounded rectangle on a still page (card_stills), not full frame
    if card: W, Hh = card['w'] * K, card['h'] * K            # the footage is scaled to the card, then laid on the page
    sw, sh = base['size']
    cmd = ['ffmpeg', '-v', 'error', '-y', '-nostats', '-progress', 'pipe:1']
    # a stretch cut out of a rendered page starts on its first frame's own time: without this ffmpeg repeats that frame
    chain = ['fps=30'] if base['fps60'] else ['setpts=PTS-STARTPTS']
    if gpu:
        cmd += ['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda']
        if base['crop']:
            # The crop is done by the decoder (NVDEC): `crop` on hardware frames + scale_cuda gave a wrong region in ffmpeg
            # 8.0.1. Even numbers, as the software crop filter rounds them for 4:2:0.
            x, y, w, h = base['crop']; x, y = x // 2 * 2, y // 2 * 2
            cmd += ['-c:v', base.get('codec', 'h264') + '_cuvid', '-crop', f'{y}x{sh - y - h}x{x}x{sw - x - w}']
    elif base['crop']:
        chain.append('crop={2}:{3}:{0}:{1}'.format(*base['crop']))
    cmd += ['-ss', f"{base['ss']:.4f}", '-i', str(base['file'])]
    scaled = bool(base['crop']) or (sw, sh) != (W, Hh)
    oncard = gpu          # are the frames still on the card at this point of the chain?
    if scaled:
        # Scaling is done by the same software lanczos as before, also on the GPU route: scale_cuda is not as faithful
        # (4K screen slice against the source: 43.9 dB with its best mode, 45.9 dB with software lanczos; its lanczos and
        # bicubic also speckle small text when shrinking). So a slice that needs scaling leaves the card after decode + crop.
        if gpu: chain += ['hwdownload', 'format=nv12']; oncard = False
        chain += [f'scale={W}:{Hh}:flags=lanczos', 'setsar=1']
    if base['h'] != 1080:
        if oncard: chain += ['hwdownload', 'format=nv12']; oncard = False
        chain.append(f"pad={W}:{1080 * K}:0:{(1080 - base['h']) // 2 * K}:color=0x0d0d0c")
    if not oncard: chain.append('tpad=stop_mode=clone:stop_duration=1')  # a source that ends a frame early holds its last frame
    pre, nin = '', 1                    # filters that make [0:v]'s chain into the full frame; next free input index
    if card:
        bgf, cmask = card_stills(H, FULL, card, K)
        cmd += ['-loop', '1', '-framerate', '30', '-i', str(bgf), '-i', str(cmask)]
        if oncard: chain += ['hwdownload', 'format=nv12']; oncard = False
        pre = (f"[0:v]{','.join(chain + ['format=yuv444p'])}[c0];"
               f"[2:v]scale={W}:{Hh}:flags=lanczos,format=gray[cm];[c0][cm]alphamerge=eof_action=repeat[cv];"
               f"[1:v]scale={1920 * K}:{1080 * K}:flags=lanczos:out_color_matrix=bt709:out_range=tv,format=yuv420p[pg];"
               f"[pg][cv]overlay={card['x'] * K}:{card['y'] * K}:format=yuv420:eof_action=repeat[cbase];")
        nin, W = 3, 1920 * K
    sysmem = not oncard or bool(win)                             # does the encoder get its frames from system memory?
    if card and not win:
        cmd += ['-filter_complex', pre + '[cbase]format=yuv420p[v]', '-map', '[v]']
    elif not win:
        if sysmem: chain.append('format=yuv420p')
        if chain: cmd += ['-vf', ','.join(chain)]
    else:
        # The window is laid on in system memory, on the window's own rectangle only. overlay_cuda (ffmpeg 8.0.1) cannot be
        # trusted with it: now and then it blends a window frame that is already being overwritten (a ghost window for one
        # frame, measured), and it hands the encoder frames padded to 1088 / 2176 rows. So a GPU slice comes back from the
        # card once, finished except for the window (hwdownload); measured cost at 4K: none.
        w, h = jsround(480 * win['scale']) * K, jsround(600 * win['scale']) * K
        x, y = jsround(win['x'] * K), jsround(win['y'] * K)
        ring, mask = facewin_stills(H, place, win, cfg['face']['radius'], K, cfg['face'].get('ring', ''))
        # the ring still is the whole frame; only the box around the window holds anything (rings 5 px, shadow under 100 px)
        m = math.ceil(120 * win['scale'] * K)
        bx, by = max(0, (x - m) // 2 * 2), max(0, (y - m) // 2 * 2)
        bw, bh = min(W, (x + w + m + 1) // 2 * 2) - bx, min(1080 * K, (y + h + m + 1) // 2 * 2) - by
        # the page shows face frame (slice's first frame + k) on output frame k: seek face.mp4 to that exact frame
        cmd += ['-ss', f"{max(0, frame0 / 30 - 0.008):.4f}", '-i', str(FULL / 'assets' / 'face.mp4'), '-i', str(ring), '-i', str(mask)]
        if oncard: chain += ['hwdownload', 'format=nv12']
        head = pre + '[cbase]format=yuv420p[bg0];' if card else f"[0:v]{','.join(chain + ['format=yuv420p'])}[bg0];"
        fc = (head +
              # ring and mask are single frames: decoded once, repeated by the filters that use them
              f"[{nin + 1}:v]scale={W}:{1080 * K}:flags=lanczos,crop={bw}:{bh}:{bx}:{by},format=yuva444p,scale=out_color_matrix=bt709:out_range=tv[ring];"
              f"[bg0][ring]overlay={bx}:{by}:format=yuv420:eof_action=repeat[bg];"
              f"[{nin}:v]setpts=PTS-STARTPTS,scale={w}:{h}:flags=lanczos,format=yuv444p[f0];"
              f"[{nin + 2}:v]scale={w}:{h}:flags=lanczos,format=gray[m];"
              f"[f0][m]alphamerge=eof_action=repeat[face];"
              f"[bg][face]overlay={x}:{y}:format=yuv420:eof_action=pass,format=yuv420p[v]")
        cmd += ['-filter_complex', fc, '-map', '[v]']
    return cmd + ['-frames:v', str(n), '-r', '30', '-an', *(enc or nvenc(K, base.get('cq', 19))), *TAGS] + (['-pix_fmt', 'yuv420p'] if sysmem else []) + [str(out)]


def footage_base(H, f, holds):
    src = H / 'raw' / ('cut.mp4' if f['src'] == 'screen' else 'cam_cut.mp4')
    return dict(file=src, ss=raw_time(f['t0'], holds), fps60=True, crop=None if tuple(f['crop']) == (0, 0, 3840, 2160) else f['crop'],
                h=f['h'], size=(3840, 2160), codec='h264', cq=CQ_CAMERA if f['src'] == 'cam' else 19, card=f.get('card'))


def run_watched(cmd, cwd, log, stall=25, first=60):
    """Run ffmpeg (-progress pipe:1); kill it when no new frame arrives for `stall` s (`first` s before the first one).
    Returns the exit code, -9 when it was killed for stalling."""
    with open(log, 'ab') as lf:
        lf.write((' '.join(map(str, cmd)) + '\n').encode()); lf.flush()
        p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=lf, creationflags=PRIO)
        st = {'n': 0, 't': time.time()}

        def reader():
            for line in p.stdout:
                if line.startswith(b'frame='):
                    try: k = int(line[6:])
                    except ValueError: continue
                    if k > st['n']: st['n'], st['t'] = k, time.time()
        th = threading.Thread(target=reader, daemon=True); th.start()
        while p.poll() is None:
            time.sleep(0.2)
            if time.time() - st['t'] > (stall if st['n'] else first):
                p.kill(); p.wait(); lf.write(b'STALLED: no new frame, killed\n'); return -9
        th.join(timeout=2)
        return p.returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('run', help='work/<id>'); ap.add_argument('--rev', required=True)
    ap.add_argument('--res', default='', help='hyperframes --resolution preset, e.g. 4k'); ap.add_argument('--dry', action='store_true')
    ap.add_argument('--jobs', type=int, default=0, help='ffmpeg slices at once (default: 2 at 1080p, 3 at 4K, the measured best)')
    ap.add_argument('--no-reel', action='store_true', help='render every designed slice on its own (the page route)')
    ap.add_argument('--no-gpu-decode', action='store_true', help='software decode and filters for every slice (still NVENC)')
    ap.add_argument('--background', action='store_true', help='he is recording: idle priority and one ffmpeg job (slower; see the report)')
    ap.add_argument('--partial', action='store_true', help='a pilot: only the first sections exist yet (joined under the start of the voice)')
    ap.add_argument('--workers', type=int, help="accepted and ignored: the old renderer's option (one HyperFrames call renders the reel)")
    a = ap.parse_args()
    if a.background:
        global PRIO
        PRIO = 0x40 if os.name == 'nt' else 0; a.jobs = a.jobs or 1
    H = Path(a.run).resolve(); FULL = H / 'full'
    cfg = json.loads((FULL / 'tools' / 'video.json').read_text()); FPS = cfg.get('fps', 30)
    if 'h264_nvenc' not in subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], capture_output=True, text=True).stdout:
        # No NVIDIA encoder on this machine: the software renderer does the same job, slower, and takes run, --rev, --res and --dry.
        print('no NVIDIA encoder here: rendering in software with render_slices_x264.py', flush=True)
        soft = [sys.executable, str(Path(__file__).with_name('render_slices_x264.py')), a.run, '--rev', a.rev] + (['--res', a.res] if a.res else []) + (['--dry'] if a.dry else [])
        sys.exit(subprocess.run(soft).returncode)
    if FPS != 30: sys.exit('this renderer is for 30 fps projects; use render_slices_x264.py --no-ff')
    K = {'': 1, '4k': 2}[a.res]
    if not a.jobs: a.jobs = 2 if K == 1 else 3
    r = subprocess.run(['node', 'tools/build.mjs'] + (['--partial'] if a.partial else []), cwd=FULL, capture_output=True, text=True)
    if r.returncode:
        sys.exit('the full build failed, nothing rendered:\n' + (r.stderr or r.stdout)[-1500:])
    slices = json.loads((FULL / 'tools' / 'slices.json').read_text())
    hp = FULL / 'tools' / 'holds.json'
    holds = json.loads(hp.read_text()) if hp.exists() else []
    store = H / 'slices' / f"nv-{a.res or '1080'}"; store.mkdir(parents=True, exist_ok=True)
    kind = lambda s: 'footage' if s.get('ff') else 'reel' if s.get('pg') and not s['pg']['moves'] and not a.no_reel else 'page'
    # Kept browser renders (reels/), found by the scene's pkey: {pkey: [reel file name, first frame, frames]}. A reel scene
    # whose page is here skips the browser and only gets its face window again (a re-cut, a moved window, a new ring).
    reels = store / 'reels'; reels.mkdir(exist_ok=True); pidx_p = store / 'pages.json'
    pidx = json.loads(pidx_p.read_text()) if pidx_p.exists() else {}
    rframes = {}
    def cached(pkey, n):
        e = pidx.get(pkey)
        if not e or e[2] != n: return None
        f = reels / e[0]
        if f.name not in rframes: rframes[f.name] = frames(f) if f.exists() else -1
        return (f, e[1]) if rframes[f.name] >= e[1] + n else None
    todo = []
    for s in slices:
        s['mp4'] = store / f"{s['key']}.mp4"; s['kind'] = kind(s)
        if frames(s['mp4']) == s['frames']: continue
        if s['kind'] == 'reel' and s['pg'].get('pkey'):
            s['cached'] = cached(s['pg']['pkey'], s['frames'])
            if s['cached']: s['kind'] = 'kept'
        todo.append(s)
    count = lambda k: sum(s['kind'] == k for s in todo)
    print(f"{len(slices)} slices: {len(slices) - len(todo)} re-used, {count('footage')} footage + {count('reel')} reel + {count('page')} page to render, {count('kept')} from kept browser renders "
          f"({sum(s['frames'] for s in todo) / FPS:.0f} s of video)", flush=True)
    for s in todo:
        print(f"  {s['id']:10s} {s['start']:8.2f}-{s['end']:8.2f}  {s['kind']}", flush=True)
    if a.dry:
        return
    # The clips designed scenes show (kit.mjs clipTag), at this render's size. Before the worker copy links the media.
    if (FULL / 'tools' / 'make_clips.py').exists() and json.loads((FULL / 'tools' / 'clips.json').read_text()):
        r = subprocess.run([sys.executable, 'tools/make_clips.py'], cwd=FULL, capture_output=True, text=True, env={**os.environ, 'CLIP_SCALE': str(K)})
        print('clips: ' + (r.stdout.strip().splitlines() or ['none'])[-1], flush=True)
        if r.returncode:
            sys.exit('make_clips.py failed, nothing rendered:\n' + (r.stdout + r.stderr)[-1500:])
    bad = []; t00 = time.time(); spent = {'footage': 0.0, 'capture': 0.0, 'cut': 0.0}
    # Windows can park a background app's helpers on the efficiency cores (HyperFrames' Chrome workers then take 2-3x as
    # long): mark this render's processes as not to be throttled. Not with --background, which is meant to give way.
    unthrottle = (lambda: None) if a.background else qos_watch.start()
    tasks = queue.Queue()           # (slice, base, win, place, route name): one ffmpeg each, a.jobs at a time
    lock = threading.Lock()

    def encode(s, base, win, place, route):
        log = store / f"{s['id']}.log"; tmp = store / f"_{s['key']}.mp4"; t0 = time.time()
        how = 'gpu'; rc = -1
        if not a.no_gpu_decode:
            rc = run_watched(slice_cmd(H, FULL, base, win, place, s['frame0'], s['frames'], K, cfg, tmp, True), FULL, log)
        if rc != 0 or frames(tmp) != s['frames']:       # stalled, failed, or short: software decode and filters
            how = 'cpu decode' if a.no_gpu_decode else 'cpu decode (gpu route: rc %d, %d frames)' % (rc, frames(tmp))
            rc = run_watched(slice_cmd(H, FULL, base, win, place, s['frame0'], s['frames'], K, cfg, tmp, False), FULL, log, stall=90, first=120)
        got = frames(tmp); ok = rc == 0 and got == s['frames']
        if ok: os.replace(tmp, s['mp4'])
        dt = time.time() - t0
        with lock:
            spent['footage' if route == 'footage' else 'cut'] += dt
            if not ok: bad.append(s['id'])
        print(f"{s['id']:10s} {got}/{s['frames']} frames  {dt:5.1f}s  {route:7s} {how:4s} {'ok' if ok else 'FAILED rc=' + str(rc)}", flush=True)

    def gpu_work():
        while True:
            t = tasks.get()
            try:
                if t is None: return
                encode(*t)
            finally:
                tasks.task_done()

    def page_base(file, first_frame, size):
        return dict(file=file, ss=max(0, (first_frame - 0.5) / 30), fps60=False, crop=None, h=1080, size=size)

    def browser_work():
        """The designed slices: reels first (one HyperFrames call per REEL_FRAMES of video), then any moving-window slice."""
        res = f' --resolution {a.res}' if a.res else ''
        reel = [s for s in todo if s['kind'] == 'reel']; pages = [s for s in todo if s['kind'] == 'page']
        w = worker_dir(H, FULL, 1) if reel or pages else None
        chunks, cur = [], []
        for s in reel:
            if cur and sum(x['frames'] for x in cur) + s['frames'] > REEL_FRAMES: chunks.append(cur); cur = []
            cur.append(s)
        if cur: chunks.append(cur)
        for i, ch in enumerate(chunks):
            log = store / f'reel-{i}.log'; out = store / f'_reel-{i}.mp4'; t0 = time.time(); want = sum(s['frames'] for s in ch)
            if log.exists(): log.unlink()
            rc = run(['node', 'tools/build.mjs', '--reel=' + ','.join(s['id'] for s in ch)], w, log)
            if rc == 0: rc = run(f'npx hyperframes render --quiet{res} {REEL_ARGS} -o "{out}"', w, log)
            got = frames(out); dt = time.time() - t0; spent['capture'] += dt
            print(f"reel {i + 1}/{len(chunks)}: {len(ch)} slices, {got}/{want} frames  {dt:5.0f}s  {'ok' if rc == 0 and got in (want, want + 1) else 'FAILED rc=' + str(rc)}", flush=True)
            if rc or got not in (want, want + 1):
                with lock: bad.extend(s['id'] for s in ch)
                continue
            # Keep the browser render: a later run finds each scene in it by pkey (see `cached` above).
            kept = reels / (hashlib.sha1(','.join(s['pg'].get('pkey') or s['key'] for s in ch).encode()).hexdigest()[:16] + '.mp4')
            os.replace(out, kept); out = kept
            R = 0
            for s in ch:
                pg = s['pg']
                if pg.get('pkey'):
                    with lock: pidx[pg['pkey']] = [kept.name, R, s['frames']]
                tasks.put((s, page_base(out, R, (1920 * K, 1080 * K)), pg['win'], pg['place'], 'reel')); R += s['frames']
            with lock: pidx_p.write_text(json.dumps(pidx, indent=0))
        for s in pages:
            log = store / f"{s['id']}.log"; out = store / f"_page-{s['key']}.mp4"; t0 = time.time()
            if log.exists(): log.unlink()
            rc = run(['node', 'tools/build.mjs', f"--range={s['start']},{s['end']}", '--no-voice'], w, log)
            if rc == 0: rc = run(f'npx hyperframes render --quiet{res} {REEL_ARGS} -o "{out}"', w, log)
            spent['capture'] += time.time() - t0
            if rc or frames(out) not in (s['frames'], s['frames'] + 1):
                with lock: bad.append(s['id'])
                print(f"{s['id']:10s} page render FAILED rc={rc}", flush=True); continue
            tasks.put((s, page_base(out, 0, (1920 * K, 1080 * K)), None, None, 'page'))

    for s in todo:
        if s['kind'] != 'footage': continue
        f = s['ff']
        base = footage_base(H, f, holds)
        log = store / f"{s['id']}.log"
        if log.exists(): log.unlink()
        tasks.put((s, base, f['win'], f['place'], 'footage'))
    for s in todo:
        if s['kind'] != 'kept': continue
        log = store / f"{s['id']}.log"
        if log.exists(): log.unlink()
        tasks.put((s, page_base(s['cached'][0], s['cached'][1], (1920 * K, 1080 * K)), s['pg']['win'], s['pg']['place'], 'kept'))
    # Footage first, then the browser: run together they fight for the CPU and the card and both crawl (measured at
    # 1080p: the reel took 609 s beside the footage jobs, 169 s on its own).
    gts = [threading.Thread(target=gpu_work) for _ in range(max(1, a.jobs))]
    [t.start() for t in gts]
    tasks.join()
    browser_work()
    [tasks.put(None) for _ in gts]; [t.join() for t in gts]
    unthrottle()
    for f in store.glob('_reel-*.mp4'): f.unlink()
    for f in store.glob('_page-*.mp4'): f.unlink()
    # Kept browser renders no scene of today's build uses any more are deleted (a 4K reel is several GB).
    if not bad and not a.partial:
        live = {s['pg']['pkey'] for s in slices if s.get('pg') and s['pg'].get('pkey')}
        pidx = {k: v for k, v in pidx.items() if k in live and (reels / v[0]).exists()}
        pidx_p.write_text(json.dumps(pidx, indent=0))
        used = {v[0] for v in pidx.values()}
        for f in reels.glob('*.mp4'):
            if f.name not in used: f.unlink()
    if bad:
        sys.exit('failed slices: ' + ', '.join(sorted(bad)))
    if todo:
        print(f"rendered {len(todo)} slices in {time.time() - t00:.0f}s (browser capture {spent['capture']:.0f}s; ffmpeg job-seconds: "
              f"footage {spent['footage']:.0f}, cutting designed slices {spent['cut']:.0f})", flush=True)
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
    if got != total: sys.exit(1)


if __name__ == '__main__':
    if '--dry' in sys.argv: main()
    else:
        with gpu_lock.held('long-form render ' + ' '.join(sys.argv[1:])[:60]): main()
