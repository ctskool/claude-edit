"""The face track (assets/face.mp4): built with the GPU, and repaired by splice instead of a rebuild.

The track is 960x1200 at 30 fps: frame b shows the camera cut (raw/cam_cut.mp4, 60 fps) at b/30 s, cropped and scaled
(software lanczos, as before). It is written with a keyframe on every 30th frame exactly and no B-frames, so it can be
cut on any whole second by copy.

  base    (once per cut, about 3 min)  raw/cam_cut.mp4 -> assets/face.cut.mp4. NVDEC decode, NVENC encode.
  splice  (seconds)                    assets/face.cut.mp4 + a list of repairs -> assets/face.mp4. Whole seconds the
                                       repairs do not touch are copied; only the second each repair lands in (and the
                                       frames it puts back) is encoded again, from the camera footage itself, so every
                                       frame is first generation.

A repair (as work/<id>/tools/apply_pauses.py OPS): at = a join in frames of raw/cut.mp4 (60 fps); n > 0 puts n source
frames back before it (read from the camera recording: cam = dict(path, lag, seek_off), src = source frame after them);
n < 0 trims -n frames off the end of the keep before it. n must be even (whole 30 fps frames).

As a module: build_base(cam_cut, crop, out), splice(base, cam_cut, crop, ops, out). Never writes in place: x.new, then replace.
  python face_track.py base <cam_cut.mp4> <crop W:H:X:Y> <out.mp4>
  python face_track.py splice <base.mp4> <cam_cut.mp4> <crop> <ops.json> <out.mp4>
"""
import json, math, os, subprocess, sys, tempfile, threading, time
from pathlib import Path

W, H, FPS, GOP = 960, 1200, 30, 30
# A keyframe on frames 0, 30, 60, ... and nowhere else (strict GOP, no scene-cut keyframes), no B-frames. The same line
# encodes the base and every patch, so their headers are identical and they join by copy.
ENC = ['-c:v', 'h264_nvenc', '-preset', 'p4', '-tune', 'hq', '-profile:v', 'high', '-level', '4.2', '-rc', 'vbr', '-cq', '19', '-b:v', '0',
       '-maxrate', '60M', '-bufsize', '120M', '-bf', '0', '-g', str(GOP), '-strict_gop', '1', '-no-scenecut', '1', '-forced-idr', '1']
OUT = ['-an', '-pix_fmt', 'yuv420p', '-colorspace:v', 'bt709', '-color_primaries:v', 'bt709', '-color_trc:v', 'bt709', '-color_range', 'tv',
       '-video_track_timescale', '15360']


def frames(p):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries', 'stream=nb_read_packets',
                          '-of', 'csv=p=0', str(p)], capture_output=True, text=True).stdout.strip()
    return int(out) if out.isdigit() else -1


def watched(cmd, stall=30, first=90):
    """ffmpeg with -progress pipe:1; killed when no new frame arrives for `stall` s. Returns (rc, stderr tail); rc -9 = stalled."""
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    st = {'n': 0, 't': time.time(), 'err': b''}

    def out():
        for line in p.stdout:
            if line.startswith(b'frame='):
                try: k = int(line[6:])
                except ValueError: continue
                if k > st['n']: st['n'], st['t'] = k, time.time()

    def err(): st['err'] = p.stderr.read()
    ts = [threading.Thread(target=f, daemon=True) for f in (out, err)]; [t.start() for t in ts]
    while p.poll() is None:
        time.sleep(0.25)
        if time.time() - st['t'] > (stall if st['n'] else first):
            p.kill(); p.wait(); return -9, 'no new frame for %d s (killed)' % (stall if st['n'] else first)
    [t.join(timeout=2) for t in ts]
    return p.returncode, st['err'].decode(errors='replace')[-800:]


def build_base(cam_cut, crop, out, log=print):
    """The whole track from the camera cut. NVDEC decode first; software decode if that stalls or fails (it has hung on
    camera files before). Scaling is software lanczos either way, so both give the same picture."""
    out = Path(out); tmp = out.with_name(out.stem + '.new.mp4')
    head = ['ffmpeg', '-v', 'error', '-y', '-nostats', '-progress', 'pipe:1']
    vf = f'crop={crop},scale={W}:{H}:flags=lanczos,setsar=1,format=yuv420p'
    gpu = head + ['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda', '-i', str(cam_cut), '-vf', f'fps={FPS},hwdownload,format=nv12,{vf}', *ENC, *OUT, str(tmp)]
    cpu = head + ['-i', str(cam_cut), '-vf', f'fps={FPS},{vf}', *ENC, *OUT, str(tmp)]
    t0 = time.time()
    rc, e = watched(gpu); route = 'GPU decode'
    if rc:
        log(f'face track: GPU decode failed ({e.strip()[-200:]}); software decode instead')
        rc, e = watched(cpu, stall=120, first=180); route = 'software decode'
        if rc: sys.exit('face track failed: ' + e)
    os.replace(tmp, out)
    log(f'face track {out.name}: {frames(out)} frames, {route}, {time.time() - t0:.0f} s')
    return out


def plan(ops, total):
    """ops + the base track's frame count -> the new track as pieces, in order:
    ('base', b0, b1) base frames b0..b1-1, or ('ins', op, m0, count): frames m0, m0+2, ... of the op's n source frames."""
    for o in ops:
        if o['n'] % 2: sys.exit('whole frames at 30 fps only: every n must be even')
    ops = sorted(ops, key=lambda o: o['at'])
    pieces, off, start = [], 0, 0          # off = frames added so far (60 fps), start = where this stretch of the cut begins
    for o in ops:
        end = o['at'] + min(o['n'], 0)
        b0, b1 = math.ceil(start / 2), math.ceil(end / 2)
        if b1 > b0: pieces.append(('base', b0, b1))
        if o['n'] > 0:
            p0 = o['at'] + off                              # position of the insert in the new 60 fps stream
            j0, j1 = math.ceil(p0 / 2), math.ceil((p0 + o['n']) / 2)
            if j1 > j0: pieces.append(('ins', o, 2 * j0 - p0, j1 - j0))
        off += o['n']; start = o['at']
    pieces.append(('base', math.ceil(start / 2), total))
    return pieces


def splice(base, cam_cut, crop, ops, out, log=print):
    """base track + repairs -> out. Returns the new frame count."""
    base, out = Path(base), Path(out)
    total = frames(base); t0 = time.time()
    pieces = plan(ops, total)
    # Split every base piece into: frames to encode again (up to the next whole second), whole seconds to copy, frames to
    # encode again (after the last whole second). The end of the track is copied to its last frame.
    parts = []                                   # ('copy', c0, c1) | ('enc', [segments]) where a segment is a base or ins piece
    def enc(seg):
        if parts and parts[-1][0] == 'enc': parts[-1][1].append(seg)
        else: parts.append(('enc', [seg]))
    for p in pieces:
        if p[0] == 'ins': enc(p); continue
        _, b0, b1 = p
        c0 = -(-b0 // GOP) * GOP
        c1 = b1 if b1 == total else b1 // GOP * GOP
        if c1 <= c0: enc(p); continue
        if c0 > b0: enc(('base', b0, c0))
        parts.append(('copy', c0, c1))
        if b1 > c1: enc(('base', c1, b1))
    tmpd = Path(tempfile.mkdtemp(prefix='facesplice-', dir=str(out.parent)))
    try:
        lines, want = ['ffconcat version 1.0'], 0
        for k, part in enumerate(parts):
            if part[0] == 'copy':
                _, c0, c1 = part
                lines += [f"file '{base.resolve().as_posix()}'", f'inpoint {c0 // GOP}']
                if c1 != total: lines.append(f'outpoint {c1 // GOP}')
                lines.append(f'duration {(c1 - c0) / FPS:.6f}'); want += c1 - c0
                continue
            # -copyts: the camera cut keeps its own timestamps, so `fps` picks the frame for each 1/30 s exactly as the
            # base build did (the cut's timestamps are not perfectly regular; counting frames would drift from it).
            cmd, g, order, n_out = ['ffmpeg', '-v', 'error', '-y', '-copyts'], [], [], 0
            for i, seg in enumerate(part[1]):
                if seg[0] == 'base':
                    _, b0, b1 = seg
                    cmd += ['-ss', f'{max(0, b0 / FPS - 0.2):.6f}', '-i', str(cam_cut)]
                    g.append(f"[{i}:v]fps={FPS}:start_time={max(0, b0 - 4) / FPS:.6f},trim=start_pts={b0}:end_pts={b1},"
                             f"setpts=PTS-STARTPTS,format=yuv420p[s{i}]"); n_out += b1 - b0
                else:
                    _, o, m0, cnt = seg; cam = o['cam']
                    cmd += ['-ss', f"{(o['src'] - o['n'] - cam['lag'] - 0.5) / 60 + cam['seek_off']:.6f}", '-i', cam['path']]
                    g.append(f"[{i}:v]setpts=N/60/TB,trim=end_frame={o['n']},select='eq(mod(n\\,2)\\,{m0})',setpts=N/{FPS}/TB,format=yuv420p[s{i}]"); n_out += cnt
                order.append(f'[s{i}]')
            g.append(''.join(order) + (f'concat=n={len(order)}:v=1:a=0,' if len(order) > 1 else '') +
                     f'crop={crop},scale={W}:{H}:flags=lanczos,setsar=1[v]')
            pf = tmpd / f'p{k}.mp4'
            r = subprocess.run(cmd + ['-filter_complex', ';'.join(g), '-map', '[v]', '-r', str(FPS), '-frames:v', str(n_out), *ENC, *OUT, str(pf)],
                               capture_output=True, text=True)
            if r.returncode or frames(pf) != n_out:
                sys.exit(f'face splice: a patch failed ({frames(pf)} of {n_out} frames)\n' + r.stderr[-600:])
            lines += [f"file '{pf.resolve().as_posix()}'", f'duration {n_out / FPS:.6f}']; want += n_out
        lst = tmpd / 'list.txt'; lst.write_text('\n'.join(lines) + '\n')
        tmp = out.with_name(out.stem + '.new.mp4')
        r = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', '-an',
                            '-video_track_timescale', '15360', str(tmp)], capture_output=True, text=True)
        got = frames(tmp)
        if r.returncode or got != want:
            sys.exit(f'face splice: joined {got} frames, expected {want}\n' + r.stderr[-600:])
        os.replace(tmp, out)
    finally:
        for f in tmpd.iterdir(): f.unlink()
        tmpd.rmdir()
    enc_frames = sum(sum((s[2] - s[1]) if s[0] == 'base' else s[3] for s in p[1]) for p in parts if p[0] == 'enc')
    log(f'face track {out.name}: {want} frames, {enc_frames} encoded again in {sum(p[0] == "enc" for p in parts)} patches, rest copied, {time.time() - t0:.1f} s')
    return want


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'base' and len(a) == 4:
        build_base(a[1], a[2], a[3])
    elif a and a[0] == 'splice' and len(a) == 6:
        splice(a[1], a[2], a[3], json.loads(Path(a[4]).read_text()), a[5])
    else:
        sys.exit(__doc__)
