"""Beat review player for one project: python tools/beat_review/server.py work/<id>/v2/editorial. PORT defaults to 4744.

The page is the only thing that clicks waive, approve and go back, so those routes need the page's own Origin.
Everything about notes, rounds and approval lives in review.py. This file only serves it and the media.
"""
import argparse
import os
import re
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.plan_page.common import read
from tools.plan_page.http_utils import RangeHandler

SHA16, BEAT_ID = re.compile(r'[0-9a-f]{16}'), re.compile(r'[A-Za-z0-9_-]{1,32}')
LOCAL = {'localhost', '127.0.0.1', '[::1]'}


def stitched_dir(project):
    return Path(project).resolve().parents[1] / 'beat' / 'stitched'


def picture_folder(project, sha16):
    """review-<sha16> or review-<sha16>-<rev16>. Two compositions can share one file, and either holds its bytes."""
    if not SHA16.fullmatch(sha16):
        return None
    root = stitched_dir(project)
    folders = sorted(root.glob(f'review-{sha16}*')) if root.is_dir() else []
    return next((f for f in folders if (f / 'review.mp4').is_file()), None)


def before_picture(project, state):
    """What the changed flags compare against: the head round if a change has moved past it, otherwise its parent. With that picture's own beat ranges."""
    current = (state.get('picture') or {}).get('file_sha256')
    rounds = {r['n']: r for r in state.get('rounds') or []}
    head = rounds.get(state.get('head'))
    row = head if head and head['picture_sha'] != current else rounds.get(head.get('parent')) if head else None
    folder = picture_folder(project, row['picture_sha'][:16]) if row else None
    if not folder or row['picture_sha'] == current:
        return None
    lock = read(folder / 'beats.lock.json') if (folder / 'beats.lock.json').is_file() else {'beats': []}
    return {'n': row['n'], 'picture_sha': row['picture_sha'], 'url': f"/media/picture/{row['picture_sha'][:16]}.mp4",
            'beats': {b['beat_id']: [b['start_frame'], b['end_frame']] for b in lock['beats']}}


def approval_view(project, state):
    """review.py names the stage. The fresh render's published segments say how far through it is."""
    view, picture = dict(state.get('approval') or {}), state.get('picture') or {}
    if view.get('state') == 'running' and view.get('stage') == 'rendering':
        fresh = Path(project).resolve().parents[1] / 'beat-fresh' / picture['file_sha256'][:16] / 'segments'
        view.update(done=sum(1 for _ in fresh.glob('*/*/segment.json')), total=len(state.get('beats') or []))
    return view


def open_notes(state):
    """Notes a round still owes. A note on an older picture is flagged and no round picks it up, so it cannot hold approval forever."""
    return [n for n in state.get('notes') or [] if n.get('scope') != 'sound' and not n.get('closed') and not n.get('older_picture')]


class NativeJobs:
    """One native render at a time, because the store takes one run at a time. A job outlives a page reload."""
    def __init__(self, project, api):
        self.project, self.api, self.jobs, self.lock = project, api, {}, threading.Lock()

    def start(self, beat_id):
        with self.lock:
            if any(j['state'] == 'running' for j in self.jobs.values()):
                raise ValueError('Another beat is rendering. Try again when it finishes.')
            job = self.jobs[beat_id] = {'state': 'running', 'started': time.time()}
        threading.Thread(target=self.run, args=(beat_id, job), daemon=True).start()
        return self.view(beat_id, job)

    def run(self, beat_id, job):
        try:
            job['path'] = str(self.api.native_beat(self.project, beat_id))
            job['state'] = 'done'
        except Exception as e:  # shown on the page, whatever the renderer raised
            job['error'], job['state'] = str(e), 'failed'
        job['finished'] = time.time()

    def view(self, beat_id, job):
        out = {'state': job['state'], 'seconds': round(job.get('finished', time.time()) - job['started'], 1)}
        if job['state'] == 'done':
            out['url'] = f'/media/native/{beat_id}.mp4'
        if job['state'] == 'failed':
            out['error'] = job['error']
        return out

    def all(self):
        with self.lock:
            return {k: self.view(k, j) for k, j in self.jobs.items()}

    def path(self, beat_id):
        job = self.jobs.get(beat_id) or {}
        return job.get('path')


class SoundJobs:
    """Listening jobs are keyed by picture and sheet, entirely outside the picture ledger."""
    def __init__(self, project, api):
        self.project, self.api, self.jobs, self.lock = project, api, {}, threading.Lock()

    def key(self, picture_sha, identity):
        return f'{picture_sha[:16]}-{identity[:16]}'

    def start(self, picture_sha, identity):
        state = self.api.state(self.project)
        if not identity or identity != (state.get('sound') or {}).get('identity') or picture_sha != (state.get('picture') or {}).get('file_sha256'):
            raise ValueError('picture or sound sheet changed; reload before listening')
        key = self.key(picture_sha, identity)
        with self.lock:
            job = self.jobs.get(key)
            if not job or job['state'] == 'failed':
                job = self.jobs[key] = {'state': 'running', 'picture_sha': picture_sha, 'sheet_identity': identity}
                threading.Thread(target=self.run, args=(picture_sha, identity, job), daemon=True).start()
        return self.view(job)

    def run(self, picture_sha, identity, job):
        try:
            job['path'] = self.api.sound_preview(self.project, picture_sha, identity)
            job['state'] = 'done'
        except Exception as e:
            job['error'], job['state'] = str(e), 'failed'

    def view(self, job):
        result = job.copy()
        result.pop('path', None)
        if result['state'] == 'done':
            result['url'] = f"/media/sound-preview/{self.key(result['picture_sha'], result['sheet_identity'])}.mp4"
        return result

    def current(self, state):
        pic, sound = state.get('picture') or {}, state.get('sound') or {}
        if not pic.get('file_sha256') or not sound.get('identity'):
            return None
        job = self.jobs.get(self.key(pic['file_sha256'], sound['identity']))
        return self.view(job) if job else None

    def path(self, key):
        if not re.fullmatch(r'[0-9a-f]{16}-[0-9a-f]{16}', key):
            return None
        job = self.jobs.get(key) or {}
        return job.get('path') if job.get('state') == 'done' else None


def make_handler(project, api=None):
    """api is review.py, unless a test hands in a fake."""
    project = Path(project).resolve()
    if api is None:
        sys.path.insert(0, str(Path(__file__).parent))
        import review as api  # the same name approval.py imports it by, so there is one module and one write lock
    native = NativeJobs(project, api)
    sound = SoundJobs(project, api)
    stills = {}

    def payload():
        state = api.state(project)
        sha = (state.get('picture') or {}).get('file_sha256')
        stills.update({str(n.get('id')): n['still'] for n in state.get('notes') or [] if n.get('still')})
        return {**state, 'project': project.parents[1].name, 'native': native.all(), 'before': before_picture(project, state), 'approval': approval_view(project, state),
                'sound_preview': sound.current(state), 'video': f'/media/picture/{sha[:16]}.mp4' if sha else None}

    def region_image(index):
        rows = api.approval_status(project).get('regions') or []
        return rows[index].get('image') if index < len(rows) else None

    class Handler(RangeHandler):
        def log_message(self, *args):
            pass

        def handle_one_request(self):
            try:
                super().handle_one_request()
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                self.close_connection = True  # a browser drops a media request whenever it seeks

        def do_GET(self):
            route = unquote(urlsplit(self.path).path)
            try:
                if route in ('/', '/index.html'):
                    return self.send_file(Path(__file__).with_name('index.html'), 'text/html; charset=utf-8')
                if route == '/favicon.ico':
                    self.send_response(204); self.end_headers(); return
                if route == '/api/state':
                    return self.json(payload())
                if route == '/api/approval':
                    return self.json(api.approval_status(project))
                name = route.rsplit('/', 1)[-1]
                if route.startswith('/media/picture/') and name.endswith('.mp4'):
                    folder = picture_folder(project, name[:-4])
                    if folder:
                        return self.send_file(folder / 'review.mp4', 'video/mp4')
                if route.startswith('/media/native/') and name.endswith('.mp4') and native.path(name[:-4]):
                    return self.send_file(native.path(name[:-4]), 'video/mp4')
                if route.startswith('/media/sound-preview/') and name.endswith('.mp4') and sound.path(name[:-4]):
                    return self.send_file(sound.path(name[:-4]), 'video/mp4')
                if route.startswith('/media/still/') and name in stills:
                    return self.send_file(stills[name])
                if route.startswith('/media/region/') and name.isdigit() and region_image(int(name)):
                    return self.send_file(region_image(int(name)))
                self.send_error(404)
            except (ValueError, OSError, KeyError, TypeError) as e:
                self.json({'error': str(e)}, 400)

        def clicked(self):
            # A script on this machine can still forge this. It stops every other page and a bare curl.
            if self.headers.get('Origin') != 'http://' + self.headers.get('Host', ''):
                raise PermissionError('This needs a click on the page.')

        def do_POST(self):
            try:
                if self.headers.get('Host', '').rpartition(':')[0] not in LOCAL:
                    raise PermissionError('Local only.')
                body = self.body_json()
                if not isinstance(body, dict):
                    raise ValueError('body must be object')
                if self.path == '/api/notes':
                    note = {k: body.get(k) for k in ('text', 'frame', 'scope', 'picture_sha', 'cue_index', 'sheet_identity')}
                    return self.json(api.add_note(project, note))
                if self.path == '/api/sound-preview':
                    return self.json(sound.start(body.get('picture_sha'), body.get('sheet_identity')))
                if self.path == '/api/sound/close':
                    return self.json(api.close_sound(project, done=body.get('done', []), not_done=body.get('not_done', {})))
                if self.path == '/api/native':
                    if not BEAT_ID.fullmatch(str(body.get('beat_id'))):
                        raise ValueError('beat_id required')
                    return self.json(native.start(body['beat_id']))
                if self.path not in ('/api/waive', '/api/approve', '/api/reconcile', '/api/go_back', '/api/drop_note'):
                    return self.send_error(404)
                self.clicked()
                if self.path == '/api/waive':
                    return self.json(api.waive(project, body['finding_id'], body['why']) or {})
                if self.path == '/api/drop_note':
                    return self.json(api.drop_note(project, body['id']) or {})
                if self.path == '/api/go_back':
                    return self.json(api.go_back(project, body['n']) or {})
                left = len(open_notes(api.state(project)))
                if left:
                    raise ValueError(f'{left} note(s) still open')
                if self.path == '/api/approve':
                    return self.json(api.approve(project, body['picture_sha']) or {})
                return self.json(api.reconcile(project, body['picture_sha'], body['why']) or {})
            except PermissionError as e:
                return self.json({'error': str(e)}, 403)
            except RuntimeError as e:  # the store's run lock: a render is going
                return self.json({'error': str(e)}, 409)
            except (ValueError, OSError, KeyError, TypeError) as e:
                return self.json({'error': str(e)}, 400)
    return Handler


def serve(project, api=None, port=None):
    port = int(os.environ.get('PORT', '4744')) if port is None else port
    server = ThreadingHTTPServer(('127.0.0.1', port), make_handler(project, api))
    print(f'http://localhost:{server.server_address[1]} | {Path(project).resolve()}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('project')
    serve(ap.parse_args().project)
