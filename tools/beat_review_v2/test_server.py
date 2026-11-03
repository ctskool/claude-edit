"""Isolated HTTP contract tests. Fake API only; no render or real-project writes.
Run: python -B tools/beat_review_v2/test_server.py
"""
import sys
sys.dont_write_bytecode = True
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
spec = importlib.util.spec_from_file_location('beat_review_v2_server', HERE / 'server.py')
v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)

SHA = 'a' * 64
SHEET = 'b' * 64


class FakeAPI:
    def __init__(self, media, still):
        self.calls = []
        self.media, self.still = str(media), str(still)
        self.data = dict(picture=dict(file_sha256=SHA, status='PASS', source='current'),
                         beats=[dict(id='b01', start_frame=0, end_frame=60, layout='split', script='Fixture')],
                         fps=30, frames=60, notes=[], findings=[], unverified={}, rounds=[], head=None,
                         approval=dict(state='none'), sound=dict(present=True, identity=SHEET,
                         cues=[dict(index=0, t=0.5, name='pin', gain_db=0, event='event')]))

    def state(self, project):
        return copy.deepcopy(self.data)

    def approval_status(self, project):
        return dict(state='reconcile', regions=[dict(image=self.still)])

    def add_note(self, project, note):
        self.calls.append(('notes', note))
        return dict(note, id='fake-note', still=self.still, still_ready=True)

    def drop_note(self, project, note_id):
        self.calls.append(('drop_note', note_id))

    def waive(self, project, finding_id, why):
        self.calls.append(('waive', finding_id, why))

    def go_back(self, project, n):
        self.calls.append(('go_back', n))

    def approve(self, project, sha):
        self.calls.append(('approve', sha))

    def reconcile(self, project, sha, why):
        self.calls.append(('reconcile', sha, why))

    def close_sound(self, project, done, not_done):
        self.calls.append(('sound/close', done, not_done))
        return dict(done=done, not_done=not_done)

    def native_beat(self, project, beat_id):
        self.calls.append(('native', beat_id))
        return self.media

    def sound_preview(self, project, sha, identity):
        self.calls.append(('sound-preview', sha, identity))
        return self.media


class ContractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='fake-', dir=HERE)
        self.home = Path(self.temp.name)
        self.project = self.home / 'project' / 'v2' / 'editorial'
        self.project.mkdir(parents=True)
        folder = self.project.parents[1] / 'beat' / 'stitched' / ('review-' + SHA[:16])
        folder.mkdir(parents=True)
        media = folder / 'review.mp4'
        media.write_bytes(b'fake media bytes, never rendered')
        still = self.home / 'still.jpg'
        still.write_bytes(b'fake jpeg')
        self.api = FakeAPI(media, still)
        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), v2.make_handler(self.project, api=self.api))
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base = 'http://127.0.0.1:' + str(self.httpd.server_port)

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)
        self.temp.cleanup()

    def request(self, path, body=None, origin=True, headers=None):
        hdr = dict(headers or {})
        if origin:
            hdr['Origin'] = self.base
        if body is not None:
            hdr['Content-Type'] = 'application/json'
        req = Request(self.base + path, data=None if body is None else json.dumps(body).encode(), headers=hdr)
        try:
            with urlopen(req, timeout=5) as response:
                return response.status, response.read(), response.headers
        except HTTPError as error:
            return error.code, error.read(), error.headers

    def post(self, route, body):
        status, raw, _ = self.request('/api/' + route, body)
        self.assertEqual(status, 200, raw)
        return json.loads(raw)

    def test_page_and_live_get_routes(self):
        expected = (HERE / 'index.html').read_bytes()
        for path in ['/', '/index.html', '/index.html?cache=1']:
            status, data, _ = self.request(path)
            self.assertEqual((status, data), (200, expected))
        status, raw, _ = self.request('/api/state')
        data = json.loads(raw)
        self.assertEqual(status, 200)
        self.assertEqual(data['picture']['file_sha256'], SHA)
        self.assertEqual(data['video'], '/media/picture/' + SHA[:16] + '.mp4')
        self.assertEqual(json.loads(self.request('/api/approval')[1])['state'], 'reconcile')
        status, data, _ = self.request('/media/picture/' + SHA[:16] + '.mp4')
        self.assertEqual(status, 200)
        self.assertIn(b'fake media', data)
        status, data, _ = self.request('/media/picture/' + SHA[:16] + '.mp4', headers={'Range': 'bytes=0-3'})
        self.assertEqual((status, data), (206, b'fake'))
        self.assertEqual(self.request('/media/region/0')[0], 200)
        self.assertEqual(self.request('/api/unknown')[0], 404)
        self.assertEqual(self.api.calls, [])

    def test_note_scopes_and_exact_forwarding(self):
        for scope, frame in [('frame', 17), ('video', None), ('sound', 15)]:
            body = dict(text='Keep this', frame=frame, scope=scope, picture_sha=SHA)
            if scope == 'sound':
                body.update(cue_index=0, sheet_identity=SHEET, cue_time=0.5, cue_name='pin')
            self.post('notes', body)
            expected = {k: body.get(k) for k in ['text', 'frame', 'scope', 'picture_sha', 'cue_index', 'sheet_identity']}
            self.assertEqual(self.api.calls[-1], ('notes', expected))
        self.api.data['notes'] = [dict(id='still-note', still=self.api.still)]
        self.request('/api/state')
        self.assertEqual(self.request('/media/still/still-note')[0], 200)

    def test_click_actions_and_sound_outcomes(self):
        cases = [('drop_note', {'id': 'n1'}, ('drop_note', 'n1')),
                 ('waive', {'finding_id': 'f1', 'why': 'Fine'}, ('waive', 'f1', 'Fine')),
                 ('go_back', {'n': 2}, ('go_back', 2)),
                 ('approve', {'picture_sha': SHA}, ('approve', SHA)),
                 ('reconcile', {'picture_sha': SHA, 'why': 'Fine'}, ('reconcile', SHA, 'Fine')),
                 ('sound/close', {'done': ['s1'], 'not_done': {'s2': 'Waiting'}}, ('sound/close', ['s1'], {'s2': 'Waiting'}))]
        for route, body, expected in cases:
            self.post(route, body)
            self.assertEqual(self.api.calls[-1], expected)

    def test_origin_and_open_note_guards_are_inherited(self):
        for route, body in [('drop_note', {'id':'n'}), ('go_back', {'n':0}), ('waive', {'finding_id':'f','why':'why'}), ('approve', {'picture_sha':SHA}), ('reconcile', {'picture_sha':SHA,'why':'why'})]:
            self.assertEqual(self.request('/api/' + route, body, origin=False)[0], 403)
        self.assertEqual(self.api.calls, [])
        self.api.data['notes'] = [dict(scope='frame', closed=False, older_picture=False)]
        for route in ['approve', 'reconcile']:
            self.assertEqual(self.request('/api/' + route, dict(picture_sha=SHA, why='why'))[0], 400)
        self.assertEqual(self.api.calls, [])
        self.api.data['notes'] = [dict(scope='sound', closed=False)]
        self.post('approve', dict(picture_sha=SHA))
        self.assertEqual(self.api.calls[-1], ('approve', SHA))

    def test_render_routes_only_call_fake_methods(self):
        self.post('native', dict(beat_id='b01'))
        self.post('sound-preview', dict(picture_sha=SHA, sheet_identity=SHEET))
        for _ in range(100):
            data = json.loads(self.request('/api/state')[1])
            if data['native'].get('b01', {}).get('state') == 'done' and (data['sound_preview'] or {}).get('state') == 'done':
                break
            time.sleep(0.01)
        else:
            self.fail('fake jobs did not complete')
        for url in [data['native']['b01']['url'], data['sound_preview']['url']]:
            self.assertEqual(self.request(url)[0], 200)
        self.assertIn(('native', 'b01'), self.api.calls)
        self.assertIn(('sound-preview', SHA, SHEET), self.api.calls)
        self.assertEqual(self.request('/api/native', {'beat_id': '../bad'})[0], 400)
        self.assertEqual(self.request('/api/sound-preview', {'picture_sha': SHA, 'sheet_identity': 'stale'})[0], 400)


if __name__ == '__main__':
    unittest.main(verbosity=2)
