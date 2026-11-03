"""Beat review player. Run: python tools/tests/test_beat_player.py, or --quick for the server only.

The server tests use a fake review module, because they test this page's routes and not Track 1's logic.
The browser tests drive real Chrome on the fixture's real picture, in a temp copy of the picture and nothing else.
RealReviewTests run Track 1's review.py on a temp copy of what it reads, so the fixture's own notes stay empty.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.beat_review.server import make_handler, picture_folder

FIXTURE = ROOT / 'work/beat-fixture'
NEW = 'review-2e1e9635fb59ee27-7f7de72113916c27'
OLD = 'review-e568318adb1fc604'
QUICK = '--quick' in sys.argv


class FakeReview:
    """The agreement in tools/beat_review/, in memory. Beats and findings copy the fixture's shape."""
    def __init__(self, project, sha_new='2e1e9635fb59ee27' + '0' * 48, sha_old=None):
        lock = json.loads((FIXTURE / 'v2/editorial/beats.lock.json').read_text(encoding='utf8'))
        say = {b['id']: b['say'] for b in json.loads((FIXTURE / 'beats.json').read_text(encoding='utf8'))['beats']}
        self.project, self.lock = project, lock
        self.notes, self.waived, self.calls, self.native_delay = [], {}, [], 0.2
        self.sha_new, self.sha_old = sha_new, sha_old or 'e568318adb1fc604' + '0' * 48
        self.picture_sha = sha_new
        self.beats = [{'id': b['beat_id'], 'start_frame': b['start_frame'], 'end_frame': b['end_frame'], 'start': b['plan_start'], 'end': b['plan_end'],
                       'script': say.get(b['beat_id'], ''), 'layout': b['layout'], 'changed': b['beat_id'] in ('b12', 'b46')} for b in lock['beats']]
        self.native_path = None
        self.approval = {'state': 'none', 'record': None}

    def state(self, project):
        return {'picture': {'file': 'review.mp4', 'file_sha256': self.picture_sha, 'composition_rev': '7f7de721', 'lock_revision': self.lock.get('revision', ''),
                            'status': 'FAIL', 'source': 'last_attempt'},
                'findings': [{'id': 'O4:1611', 'check': 'O4', 'message': 'flash_scan double cut, frames 1611 and 1612', 'frames': [1611, 1612], 'waived': 'O4:1611' in self.waived, 'waivable': True}],
                'unverified': {'action': 148, 'sub_anchor': 11, 'anchor': 11},
                'fps': 30, 'frames': 3214, 'beats': self.beats,
                'rounds': [{'n': 0, 'parent': None, 'picture_sha': self.sha_old, 'changed_beats': [], 'notes_rev': None},
                           {'n': 1, 'parent': 0, 'picture_sha': self.sha_new, 'changed_beats': ['b12', 'b46'], 'notes_rev': 'abc'}],
                'head': 1 if self.picture_sha == self.sha_new else 0, 'approvable': not self.blocked(),
                'notes': list(self.notes), 'approval': self.approval}

    def blocked(self):
        return 'O4:1611' not in self.waived

    def add_note(self, project, note):
        saved = {**note, 'id': f'n{len(self.notes) + 1}', 'still': None, 'still_ready': False, 'closed': False, 'older_picture': note.get('picture_sha') != self.picture_sha}
        self.notes.append(saved)
        return saved

    def approval_status(self, project):
        return self.approval

    def waive(self, project, finding_id, why):
        self.waived[finding_id] = why
        self.calls.append(('waive', finding_id, why))
        return {'ok': True}

    def approve(self, project, picture_sha):
        self.calls.append(('approve', picture_sha))
        self.approval = {'state': 'running', 'stage': 'rendering', 'started': '2026-11-01T09:00:00', 'record': None}
        return {'ok': True}

    def reconcile(self, project, picture_sha, why):
        self.calls.append(('reconcile', why))
        return {'ok': True}

    def drop_note(self, project, note_id):
        self.calls.append(('drop_note', note_id))
        for n in self.notes:
            if n['id'] == note_id:
                n.update(closed=True, dropped=True, not_done=None)
        return {'id': note_id, 'dropped': True}

    def go_back(self, project, n):
        self.calls.append(('go_back', n))
        self.picture_sha = self.sha_old
        return {'ok': True}

    def native_beat(self, project, beat_id):
        time.sleep(self.native_delay)
        self.calls.append(('native', beat_id))
        return self.native_path


def request(base, path, body=None, headers=None, method=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, method=method, headers={'Content-Type': 'application/json', **(headers or {})})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


class Served:
    def __init__(self, project, api):
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(project, api))
        self.base = f'http://127.0.0.1:{self.server.server_address[1]}'
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@unittest.skipUnless((FIXTURE / 'v2/editorial/beats.lock.json').is_file(), "needs work/beat-fixture, the author's 107 s test edit, which does not ship")
class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.project = root / 'v2/editorial'
        self.project.mkdir(parents=True)
        self.bytes = bytes(range(256)) * 400
        for name in (NEW, OLD):
            folder = root / 'beat/stitched' / name
            folder.mkdir(parents=True)
            (folder / 'review.mp4').write_bytes(self.bytes)
        (root / 'beat/stitched' / NEW / 'beats.lock.json').write_text(json.dumps({'beats': [{'beat_id': 'b12', 'start_frame': 5, 'end_frame': 9}]}))
        (root / 'beat/stitched' / OLD / 'beats.lock.json').write_text(json.dumps({'beats': [{'beat_id': 'b12', 'start_frame': 6, 'end_frame': 11}]}))
        native = root / 'native.mp4'
        native.write_bytes(b'native')
        self.api = FakeReview(self.project)
        self.api.native_path = native
        self.served = Served(self.project, self.api)
        self.addCleanup(self.served.close)
        self.base = self.served.base
        self.origin = {'Origin': self.base}

    def test_page_and_state(self):
        status, headers, body = request(self.base, '/')
        self.assertEqual(status, 200)
        self.assertIn('text/html', headers['Content-Type'])
        status, _, body = request(self.base, '/api/state')
        state = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(state['video'], '/media/picture/2e1e9635fb59ee27.mp4')
        self.assertEqual(state['before']['n'], 0)
        self.assertEqual(state['before']['beats']['b12'], [6, 11])
        self.assertEqual(len(state['beats']), 56)

    def test_range_is_exact(self):
        url = '/media/picture/2e1e9635fb59ee27.mp4'
        status, headers, body = request(self.base, url, headers={'Range': 'bytes=1000-1099'})
        self.assertEqual(status, 206)
        self.assertEqual(body, self.bytes[1000:1100])
        self.assertEqual(headers['Content-Range'], f'bytes 1000-1099/{len(self.bytes)}')
        self.assertEqual(headers['Accept-Ranges'], 'bytes')
        status, _, body = request(self.base, url, headers={'Range': 'bytes=-5'})
        self.assertEqual((status, body), (206, self.bytes[-5:]))
        self.assertEqual(request(self.base, url, headers={'Range': 'bytes=999999999-'})[0], 416)
        self.assertEqual(request(self.base, url, method='HEAD')[0], 200)

    def test_only_pictures_are_served(self):
        for bad in ('/media/picture/..%2f..%2fsecret.mp4', '/media/picture/zzzz.mp4', '/media/picture/2e1e9635fb59ee2.mp4', '/media/native/b01.mp4',
                    '/media/still/n1', '/beats.json', '/server.py'):
            self.assertEqual(request(self.base, bad)[0], 404, bad)
        self.assertIsNone(picture_folder(self.project, '../..'))

    def test_note_round_trip(self):
        note = {'text': 'Move this up', 'frame': 1611, 'scope': 'frame', 'picture_sha': self.api.sha_new, 'stray': 'x'}
        status, _, body = request(self.base, '/api/notes', note, self.origin)
        self.assertEqual(status, 200)
        self.assertNotIn('stray', self.api.notes[0])
        state = json.loads(request(self.base, '/api/state')[2])
        self.assertEqual(state['notes'][0]['text'], 'Move this up')
        self.assertEqual(json.loads(body)['id'], 'n1')

    def test_approve_refuses_an_open_note_but_not_an_older_one(self):
        self.api.notes.append({'id': 'n1', 'text': 'x', 'closed': False, 'older_picture': False})
        status, _, body = request(self.base, '/api/approve', {'picture_sha': self.api.sha_new}, self.origin)
        self.assertEqual(status, 400)
        self.assertIn('open', json.loads(body)['error'])
        self.api.notes[0]['older_picture'] = True
        self.assertEqual(request(self.base, '/api/approve', {'picture_sha': self.api.sha_new}, self.origin)[0], 200)

    def test_reconcile_refuses_an_open_note(self):
        self.api.notes.append({'id': 'a', 'picture_sha': self.api.picture_sha, 'closed': False, 'older_picture': False})
        status, _, body = request(self.base, '/api/reconcile', {'picture_sha': self.api.picture_sha, 'why': 'noise'}, self.origin)
        self.assertEqual(status, 400)
        self.assertIn('still open', json.loads(body)['error'])
        self.assertEqual(self.api.calls, [])

    def test_go_back_during_a_render_answers_with_its_reason(self):
        self.api.go_back = lambda project, n: (_ for _ in ()).throw(RuntimeError('another run holds run.lock'))
        status, _, body = request(self.base, '/api/go_back', {'n': 0}, self.origin)
        self.assertEqual((status, json.loads(body)['error']), (409, 'another run holds run.lock'))

    def test_clicks_need_the_page(self):
        for path, body in (('/api/waive', {'finding_id': 'O4:1611', 'why': 'x'}), ('/api/approve', {'picture_sha': 'a'}), ('/api/reconcile', {'picture_sha': 'a', 'why': 'x'}), ('/api/go_back', {'n': 1}), ('/api/drop_note', {'id': 'n1'})):
            self.assertEqual(request(self.base, path, body)[0], 403, path)
            self.assertEqual(request(self.base, path, body, {'Origin': 'http://evil.test'})[0], 400, path)
        self.assertEqual(self.api.calls, [])
        self.assertEqual(request(self.base, '/api/waive', {'finding_id': 'O4:1611', 'why': 'smooth rise'}, self.origin)[0], 200)
        self.assertEqual(request(self.base, '/api/go_back', {'n': 0}, self.origin)[0], 200)
        self.assertEqual(self.api.calls, [('waive', 'O4:1611', 'smooth rise'), ('go_back', 0)])

    def test_a_rebound_host_is_refused(self):
        self.assertEqual(request(self.base, '/api/notes', {'text': 'x'}, {'Host': 'evil.test:80', 'Origin': 'http://evil.test:80'})[0], 403)

    def test_native_job(self):
        self.api.native_delay = 0.3
        self.assertEqual(request(self.base, '/api/native', {'beat_id': '../x'}, self.origin)[0], 400)
        status, _, body = request(self.base, '/api/native', {'beat_id': 'b12'}, self.origin)
        self.assertEqual((status, json.loads(body)['state']), (200, 'running'))
        # The store takes one run at a time, so a second beat waits its turn.
        self.assertEqual(request(self.base, '/api/native', {'beat_id': 'b13'}, self.origin)[0], 400)
        for _ in range(50):
            job = json.loads(request(self.base, '/api/state')[2])['native']['b12']
            if job['state'] != 'running':
                break
            time.sleep(0.05)
        self.assertEqual(job['state'], 'done')
        self.assertEqual(request(self.base, job['url'])[2], b'native')

    def test_a_stopped_check_serves_its_region_image(self):
        image = Path(self.tmp.name) / 'region.png'
        image.write_bytes(b'png')
        self.api.approval = {'state': 'failed', 'record': None, 'regions': [{'worst_frame': 5, 'image': str(image)}]}
        self.assertEqual(request(self.base, '/media/region/0')[2], b'png')
        self.assertEqual(request(self.base, '/media/region/1')[0], 404)

    def test_a_failed_native_says_why(self):
        def broken(project, beat_id):
            raise RuntimeError('store is busy')
        self.api.native_beat = broken
        request(self.base, '/api/native', {'beat_id': 'b12'}, self.origin)
        for _ in range(50):
            job = json.loads(request(self.base, '/api/state')[2])['native']['b12']
            if job['state'] != 'running':
                break
            time.sleep(0.02)
        self.assertEqual((job['state'], job['error']), ('failed', 'store is busy'))


def fixture_picture():
    return FIXTURE / 'beat/stitched' / NEW / 'review.mp4'


def chrome_path():
    from tools.doctor import browser_candidates
    return next((Path(p) for p in browser_candidates() if Path(p).is_file()), None)


@unittest.skipIf(QUICK or not fixture_picture().is_file() or not chrome_path(), 'needs the fixture picture and Chrome')
class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.project = root / 'v2/editorial'
        cls.project.mkdir(parents=True)
        for name in (NEW, OLD):
            folder = root / 'beat/stitched' / name
            folder.mkdir(parents=True)
            shutil.copy(FIXTURE / 'beat/stitched' / name / 'review.mp4', folder)
            if (FIXTURE / 'beat/stitched' / name / 'beats.lock.json').is_file():
                shutil.copy(FIXTURE / 'beat/stitched' / name / 'beats.lock.json', folder)
        cls.api = FakeReview(cls.project)
        cls.api.native_path = root / 'beat/stitched' / NEW / 'review.mp4'
        cls.served = Served(cls.project, cls.api)
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(channel='chrome', headless=True, args=['--autoplay-policy=no-user-gesture-required'])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.served.close()
        cls.tmp.cleanup()

    def setUp(self):
        self.api.notes.clear(); self.api.waived.clear(); self.api.calls.clear()
        self.api.picture_sha = self.api.sha_new
        self.api.approval = {'state': 'none', 'record': None}
        self.context = self.browser.new_context(viewport={'width': 1280, 'height': 800})
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.on('console', lambda m: self.errors.append(m.text) if m.type == 'error' else None)
        self.page.goto(self.served.base)
        self.page.wait_for_function("document.querySelector('#v').readyState >= 2")
        self.addCleanup(self.context.close)

    def tearDown(self):
        self.assertEqual([e for e in self.errors if 'favicon' not in e and '404' not in e], [])

    def frame(self):
        shown = self.page.locator('#readout').inner_text()
        frame = self.page.evaluate('beatReview.frame()')
        self.assertIn(f'frame {frame}', shown)
        return frame

    def wait_frame(self, n):
        self.page.wait_for_function(f'beatReview.frame() === {n}', timeout=10000)

    def seek_to(self, frame):
        self.page.evaluate(f'beatReview.seek({frame})')
        self.wait_frame(frame)

    def click_timeline(self, frame):
        box = self.page.locator('#tl').bounding_box()
        self.page.mouse.click(box['x'] + box['width'] * (frame + 0.5) / 3214, box['y'] + 25)
        self.page.wait_for_timeout(250)

    def test_keys_note_reload_jump(self):
        page = self.page
        page.locator('#play').click()
        page.wait_for_function("!document.querySelector('#v').paused && document.querySelector('#v').currentTime > 0.5")
        # Space on a focused button plays and pauses. It never clicks the button as well.
        page.keyboard.press('Space')
        page.wait_for_timeout(100)
        page.wait_for_function("document.querySelector('#v').paused")
        page.wait_for_timeout(250)
        at = self.frame()
        self.assertGreater(at, 5)
        page.keyboard.press('ArrowRight'); self.wait_frame(at + 1)
        page.keyboard.press('ArrowRight'); self.wait_frame(at + 2)
        page.keyboard.press('ArrowLeft'); self.wait_frame(at + 1)
        at += 1
        # N opens, and the n is not typed into the field. Every key then belongs to the field.
        page.keyboard.press('n')
        self.assertTrue(page.locator('#text').is_visible())
        self.assertEqual(page.input_value('#text'), '')
        page.keyboard.type('nudge this left n')
        page.keyboard.press('Space')
        page.keyboard.press('ArrowLeft')
        self.assertEqual(self.frame(), at)
        self.assertTrue(page.evaluate("document.querySelector('#v').paused"))
        self.assertEqual(page.input_value('#text'), 'nudge this left n ')
        page.keyboard.press('Enter')
        self.assertFalse(page.locator('#composer').is_visible())
        self.assertIn('nudge this left n', page.locator('#note-list').inner_text())
        page.wait_for_function("document.querySelector('#saved').textContent === 'Saved'")
        self.assertEqual(self.api.notes[0]['frame'], at)
        self.assertEqual(self.api.notes[0]['picture_sha'], self.api.sha_new)
        # With the field closed, keys go back to the player.
        page.keyboard.press('ArrowRight'); self.wait_frame(at + 1)
        page.wait_for_timeout(200)
        page.reload()
        page.wait_for_function("document.querySelector('#v').readyState >= 2")
        self.wait_frame(at + 1)
        self.assertIn('nudge this left n', page.locator('#note-list').inner_text())
        self.click_timeline(2000)
        self.assertAlmostEqual(self.frame(), 2000, delta=4)
        page.locator('#note-list .when button').first.click()
        self.wait_frame(at)

    def test_shown_frame_is_the_decoded_frame(self):
        """The page says frame N, the canvas holds what the video shows, and that picture is decoded frame N and not a neighbour."""
        import io
        import numpy as np
        from PIL import Image
        page = self.page
        picture = fixture_picture()

        def decoded(n):
            out = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(picture), '-vf', f'select=eq(n\\,{n})', '-vsync', '0', '-frames:v', '1', '-f', 'image2pipe', '-c:v', 'png', '-'],
                                 capture_output=True, check=True).stdout
            return np.asarray(Image.open(io.BytesIO(out)).convert('RGB'), dtype=float)

        def shown():
            data = page.evaluate("""() => { const v = document.querySelector('#v'), c = document.createElement('canvas');
                c.width = v.videoWidth; c.height = v.videoHeight; c.getContext('2d').drawImage(v, 0, 0); return c.toDataURL('image/png'); }""")
            import base64
            return np.asarray(Image.open(io.BytesIO(base64.b64decode(data.split(',')[1]))).convert('RGB'), dtype=float)

        checked = 0
        for frame in (1609, 1611, 1612, 1613, 66, 121, 2213):
            self.seek_to(frame)
            page.wait_for_timeout(120)
            here = shown()
            near = {n: float(np.mean(np.abs(here - decoded(n)))) for n in range(frame - 2, frame + 3)}
            self.assertEqual(min(near, key=near.get), frame, near)
            self.assertLess(near[frame], 3.0, near)
            checked += 1
        # A pause during playback, in motion: whatever frame the page reports is the one on screen.
        for start in (1600, 1590, 300, 2450, 870):
            self.seek_to(start)
            page.keyboard.press('Space')
            page.wait_for_timeout(450)
            page.keyboard.press('Space')
            page.wait_for_function("document.querySelector('#v').paused")
            page.wait_for_timeout(300)
            frame = self.frame()
            here = shown()
            near = {n: float(np.mean(np.abs(here - decoded(n)))) for n in range(frame - 2, frame + 3)}
            self.assertEqual(min(near, key=near.get), frame, near)
            checked += 1
        self.assertEqual(checked, 12)

    def test_step_and_composer_are_quick(self):
        page = self.page
        self.seek_to(1000)
        steps = page.evaluate("""async () => { const out = [];
            for (let i = 0; i < 20; i++) { const want = beatReview.frame() + 1, t = performance.now();
                document.dispatchEvent(new KeyboardEvent('keydown', {key: 'ArrowRight', bubbles: true}));
                while (beatReview.frame() !== want) await new Promise(requestAnimationFrame);
                out.push(performance.now() - t); }
            return out.sort((a, b) => a - b); }""")
        print(f'\nframe step: median {steps[10]:.0f} ms, worst {steps[-1]:.0f} ms')
        opened = page.evaluate("""() => { const t = performance.now();
            document.dispatchEvent(new KeyboardEvent('keydown', {key: 'n', bubbles: true}));
            const shown = !document.querySelector('#composer').hidden && document.activeElement.id === 'text';
            return [shown, performance.now() - t]; }""")
        print(f'N to a focused field: {opened[1]:.1f} ms')
        self.assertTrue(opened[0])
        self.assertLess(opened[1], 16)
        page.keyboard.type('quick one')
        saved = page.evaluate("""() => { const t = performance.now(), box = document.querySelector('#text');
            box.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true}));
            return [document.querySelector('#composer').hidden, document.querySelector('#note-list').textContent.includes('quick one'), performance.now() - t]; }""")
        print(f'Enter to closed and in the list: {saved[2]:.1f} ms')
        self.assertEqual(saved[:2], [True, True])
        self.assertLess(saved[2], 16)

    def test_range_seek_lands_on_the_frame_at_both_ends(self):
        for frame in (0, 3213):
            self.seek_to(frame)
            self.assertEqual(self.frame(), frame)

    def test_composer_keys_held_while_a_field_is_open(self):
        page = self.page
        page.locator('[data-tab="checks"]').count()
        page.locator('.finding button', has_text='Waive').first.click()
        input_box = page.locator('.ask input')
        self.assertTrue(input_box.is_visible())
        before = self.frame()
        page.keyboard.type('n a ')
        page.keyboard.press('ArrowRight')
        self.assertEqual(input_box.input_value(), 'n a ')
        self.assertEqual(self.frame(), before)
        self.assertFalse(page.locator('#composer').is_visible())
        page.keyboard.type('smooth rise, not a cut')
        page.keyboard.press('Enter')
        page.wait_for_function("document.querySelector('#finding-list').textContent.includes('waived')")
        self.assertEqual(self.api.calls[0][0], 'waive')

    def test_whole_video_note_and_approve_gate(self):
        page = self.page
        self.assertTrue(page.locator('#approve').is_disabled())
        self.assertIn('1 failed check', page.locator('#why').inner_text())
        page.keyboard.press('Shift+N')
        page.keyboard.type('Everything a touch slower')
        page.keyboard.press('Enter')
        page.wait_for_function("document.querySelector('#saved').textContent === 'Saved'")
        self.assertEqual((self.api.notes[0]['scope'], self.api.notes[0]['frame']), ('video', None))
        self.assertIn('Whole video', page.locator('#note-list').inner_text())
        self.assertIn('1 open note', page.locator('#why').inner_text())
        self.assertTrue(page.locator('#go-line').is_visible())
        self.api.notes.clear(); self.api.waived['O4:1611'] = True
        page.wait_for_function("!document.querySelector('#approve').disabled", timeout=8000)
        page.locator('#approve').click()
        page.wait_for_function("document.querySelector('#approve').textContent === 'Checking'")
        region = {'first': 1611, 'last': 1612, 'frames': 2, 'worst_frame': 1611, 'beat': 'b28', 'block': 14.2, 'fine': 20.1, 'chroma': 3.0, 'y': 100, 'x': 20, 'score': 2.0}
        self.api.approval = {'state': 'failed', 'regions': [region], 'record': {'approved_file_sha256': self.api.sha_new, 'result': 'FAIL', 'frames_compared': 3214, 'worst_psnr': 31.2, 'worst_block': 14.2, 'why': 'a region is over the line'}}
        page.wait_for_function("document.querySelector('#approval').textContent.includes('FAIL')", timeout=8000)
        page.locator('#approval button').first.click()
        self.wait_frame(1611)
        self.assertEqual(page.locator('#regions i').count(), 1)

    def test_an_unsent_draft_survives_a_reload(self):
        page = self.page
        self.seek_to(700)
        page.keyboard.press('n')
        page.keyboard.type('half a thought')
        page.reload()
        page.wait_for_function("document.querySelector('#text').value === 'half a thought'", timeout=10000)
        self.wait_frame(700)
        self.assertTrue(page.locator('#composer').is_visible())
        page.keyboard.press('Escape')
        self.assertFalse(page.locator('#composer').is_visible())
        page.reload()
        page.wait_for_function("document.querySelector('#v').readyState >= 2")
        self.assertFalse(page.locator('#composer').is_visible())

    def test_a_note_typed_as_a_new_picture_arrives_stays_on_the_picture_on_screen(self):
        page = self.page
        self.seek_to(100)
        page.keyboard.press('n')
        page.keyboard.type('still the old one')
        self.api.picture_sha = self.api.sha_old  # run.py change moved the state under the composer
        page.wait_for_function("!document.querySelector('#banner').hidden", timeout=8000)
        self.assertIn('frame 100', page.locator('#at').inner_text())
        self.assertEqual(page.input_value('#text'), 'still the old one')
        page.keyboard.press('Enter')
        page.wait_for_function("document.querySelector('#saved').textContent === 'Saved'", timeout=8000)
        saved = self.api.notes[-1]
        self.assertEqual((saved['picture_sha'], saved['frame'], saved['older_picture']), (self.api.sha_new, 100, True))

    def test_load_it_rebinds_the_composer_before_a_new_frame_is_saved(self):
        page = self.page
        self.seek_to(100)
        page.keyboard.press('n')
        page.keyboard.type('on the picture I loaded')
        self.api.picture_sha = self.api.sha_old
        page.wait_for_function("!document.querySelector('#banner').hidden", timeout=8000)
        page.locator('#banner button').click()
        page.wait_for_function("document.querySelector('#v').readyState >= 2")
        self.seek_to(200)
        page.locator('#text').press('Enter')
        page.wait_for_function("document.querySelector('#saved').textContent === 'Saved'", timeout=8000)
        self.assertEqual((self.api.notes[-1]['picture_sha'], self.api.notes[-1]['frame']), (self.api.sha_old, 200))

    def test_comparison_waits_until_the_picture_and_beat_frames_match(self):
        page = self.page
        self.api.picture_sha = self.api.sha_old
        page.reload()
        page.wait_for_function("document.querySelector('#v').readyState >= 2")
        page.locator('#play').click()
        page.wait_for_function("!document.querySelector('#v').paused")
        self.api.picture_sha = self.api.sha_new
        page.wait_for_function("!document.querySelector('#banner').hidden", timeout=8000)
        compare = page.locator('.beat[data-id="b12"] button', has_text='Before / after')
        self.assertTrue(compare.is_disabled())
        self.assertFalse(page.locator('#compare').evaluate('(e) => e.open'))

    def test_approve_holds_while_a_new_picture_waits_behind_the_banner(self):
        page = self.page
        self.seek_to(100)
        page.keyboard.press('n')
        page.keyboard.type('still the old one')
        self.api.picture_sha = self.api.sha_old
        page.wait_for_function("!document.querySelector('#banner').hidden", timeout=8000)
        page.wait_for_function("document.querySelector('#why').textContent.includes('a new picture is waiting')", timeout=8000)
        self.assertTrue(page.locator('#approve').is_disabled())

    def test_a_draft_held_across_a_new_picture_and_a_reload_keeps_its_picture(self):
        page = self.page
        self.seek_to(120)
        page.keyboard.press('n')
        page.keyboard.type('draft on the old one')
        self.api.picture_sha = self.api.sha_old
        page.wait_for_function("!document.querySelector('#banner').hidden", timeout=8000)
        page.wait_for_timeout(100)
        page.reload()
        page.wait_for_function("document.querySelector('#text').value === 'draft on the old one'", timeout=10000)
        self.assertIn('older picture', page.locator('#at').inner_text())
        page.keyboard.press('Enter')
        page.wait_for_function("document.querySelector('#saved').textContent === 'Saved'", timeout=8000)
        self.assertEqual((self.api.notes[-1]['picture_sha'], self.api.notes[-1]['older_picture']), (self.api.sha_new, True))

    def test_a_click_on_the_picture_while_typing_changes_nothing(self):
        page = self.page
        self.seek_to(200)
        page.keyboard.press('n')
        page.keyboard.type('hold on')
        page.locator('#v').click()
        page.wait_for_timeout(300)
        self.assertEqual(page.evaluate('document.activeElement.id'), 'text')
        self.assertTrue(page.evaluate("document.querySelector('#v').paused"))
        self.assertEqual(self.frame(), 200)
        page.keyboard.press('Escape')
        self.assertFalse(page.locator('#composer').is_visible())

    def test_a_note_label_keeps_its_row_before_a_still_arrives(self):
        page = self.page
        page.keyboard.press('Shift+N')
        page.keyboard.type('whole video')
        page.keyboard.press('Enter')
        page.wait_for_function("document.querySelector('#saved').textContent === 'Saved'", timeout=8000)
        when, text = page.evaluate("[...document.querySelectorAll('.note')].pop() && ['.when', '.text'].map((s) => { const r = document.querySelector('.note ' + s).getBoundingClientRect(); return [r.width, r.top, r.bottom]; })")
        self.assertGreater(when[0], 100)
        self.assertLessEqual(when[2], text[1] + 1)

    def test_a_note_left_undone_shows_why_and_can_be_dropped(self):
        self.api.notes.append({'id': 'n1', 'text': 'new shirt', 'frame': 300, 'scope': 'frame', 'picture_sha': self.api.sha_new, 'closed': False, 'older_picture': False, 'still_ready': False, 'not_done': 'that needs body pixels we do not have'})
        page = self.page
        page.reload()
        page.wait_for_function("document.querySelector('#note-list').textContent.includes('body pixels')")
        self.assertIn('not done', page.locator('#note-list').inner_text())
        self.assertIn('1 open note', page.locator('#why').inner_text())
        page.locator('#note-list button', has_text='Drop').click()
        self.assertEqual(self.api.calls, [])
        page.locator('#note-list button', has_text='Drop it?').click()
        page.wait_for_function("document.querySelector('#note-list').textContent.includes('dropped')", timeout=8000)
        self.assertEqual(self.api.calls, [('drop_note', 'n1')])

    def test_a_note_go_back_undid_says_so(self):
        self.api.notes.append({'id': 'n1', 'text': 'was done', 'frame': 300, 'scope': 'frame', 'picture_sha': self.api.sha_new, 'closed': False, 'older_picture': True, 'still_ready': False, 'undone': True})
        self.page.reload()
        self.page.wait_for_function("document.querySelector('#note-list').textContent.includes('undone by go back')")

    def test_note_from_an_older_picture_is_marked(self):
        self.api.notes.append({'id': 'n1', 'text': 'old one', 'frame': 300, 'scope': 'frame', 'picture_sha': self.api.sha_old, 'closed': False, 'older_picture': True, 'still_ready': False})
        self.page.reload()
        self.page.wait_for_function("document.querySelector('#note-list').textContent.includes('older picture')")

    def test_a_refused_outage_keeps_the_note(self):
        page = self.page
        page.route('**/api/notes', lambda route: route.abort())
        page.keyboard.press('n')
        page.keyboard.type('saved while the server is away')
        page.keyboard.press('Enter')
        self.assertIn('saved while the server is away', page.locator('#note-list').inner_text())
        page.wait_for_function("document.querySelector('#saved').classList.contains('bad')")
        self.assertEqual(self.api.notes, [])
        self.errors.clear()
        page.unroute('**/api/notes')
        page.reload()
        page.wait_for_function("document.querySelector('#saved').textContent === 'Saved'")
        self.assertEqual(len(self.api.notes), 1)
        self.errors.clear()

    def test_compare_runs_in_step(self):
        page = self.page
        page.locator('#changed-line button').first.click()
        page.wait_for_function("document.querySelector('#compare').open && document.querySelector('#cmp-a').readyState >= 2 && document.querySelector('#cmp-z').readyState >= 2")
        page.wait_for_timeout(300)
        offsets = page.evaluate("[document.querySelector('#cmp-a').currentTime, document.querySelector('#cmp-z').currentTime]")
        self.assertAlmostEqual(offsets[0], offsets[1], places=3)
        page.keyboard.press('ArrowRight')
        page.wait_for_timeout(200)
        later = page.evaluate("[document.querySelector('#cmp-a').currentTime, document.querySelector('#cmp-z').currentTime]")
        self.assertAlmostEqual(later[0] - offsets[0], 1 / 30, places=3)
        self.assertAlmostEqual(later[1] - offsets[1], 1 / 30, places=3)
        page.keyboard.press('Space')
        page.wait_for_timeout(500)
        playing = page.evaluate("[document.querySelector('#cmp-a').currentTime, document.querySelector('#cmp-z').currentTime, document.querySelector('#cmp-a').paused]")
        self.assertFalse(playing[2])
        self.assertLess(abs(playing[0] - playing[1]), 3 / 30)
        page.keyboard.press('Escape')
        self.assertFalse(page.evaluate("document.querySelector('#compare').open"))

    def test_native_button_shows_progress_then_opens(self):
        page = self.page
        self.api.native_delay = 1.5
        self.seek_to(600)
        row = page.locator('.beat.cur')
        row.locator('button', has_text='Native size').click()
        page.wait_for_function("document.querySelector('.beat.busy .job')?.textContent.includes('Rendering')", timeout=4000)
        page.wait_for_function("[...document.querySelectorAll('.beat.cur button')].some(b => b.textContent === 'Open native')", timeout=8000)
        page.locator('.beat.cur button', has_text='Open native').click()
        page.wait_for_function("document.querySelector('#native').open && document.querySelector('#nat-v').readyState >= 2")
        page.wait_for_timeout(200)
        before = page.evaluate("document.querySelector('#nat-v').currentTime")
        page.keyboard.press('ArrowRight')
        page.wait_for_timeout(200)
        self.assertAlmostEqual(page.evaluate("document.querySelector('#nat-v').currentTime") - before, 1 / 30, places=3)
        page.keyboard.press('Space')
        page.wait_for_function("!document.querySelector('#nat-v').paused")
        page.locator('#nat-close').click()
        self.assertFalse(page.evaluate("document.querySelector('#native').open"))

    def test_go_back_asks_then_restores(self):
        page = self.page
        button = page.locator('.round button', has_text='Go back')
        button.click()
        self.assertEqual(self.api.calls, [])
        page.locator('.round button', has_text='Restore it?').click()
        page.wait_for_function("document.querySelector('#v').src.includes('e568318adb1fc604')", timeout=8000)
        self.assertEqual(self.api.calls, [('go_back', 0)])

    def test_phone_width_has_no_side_scroll(self):
        page = self.page
        for width, height in ((375, 812), (1280, 800), (900, 700), (618, 322), (1000, 420)):
            page.set_viewport_size({'width': width, 'height': height})
            page.wait_for_timeout(100)
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width)


def copy_review_project(root):
    """What review.py reads, from the fixture, into a temp folder: the picture, its checks, the map of beats. Nothing here can write to the fixture."""
    entries = {}
    for name in ('current.json', 'last_attempt.json'):
        path = FIXTURE / 'beat' / name
        entries.update(json.loads(path.read_text(encoding='utf8')) if path.is_file() else {})
    entry = entries['review']
    (root / 'beat/stitched').mkdir(parents=True)
    (root / 'beat/checks').mkdir()
    (root / 'v2/editorial').mkdir(parents=True)
    for name in ('current.json', 'last_attempt.json', 'store.json'):
        if (FIXTURE / 'beat' / name).is_file():
            shutil.copy(FIXTURE / 'beat' / name, root / 'beat')
    shutil.copytree(FIXTURE / 'beat/stitched' / entry['stitched'], root / 'beat/stitched' / entry['stitched'])
    shutil.copytree(FIXTURE / 'beat/checks' / entry['composition_rev'][:16], root / 'beat/checks' / entry['composition_rev'][:16])
    shutil.copytree(FIXTURE / 'raw', root / 'raw')
    for name in ('fixture.json', 'waivers.json'):
        if (FIXTURE / name).is_file():
            shutil.copy(FIXTURE / name, root)
    for name in ('plan.json', 'beats.lock.json'):
        shutil.copy(FIXTURE / 'v2/editorial' / name, root / 'v2/editorial')
    (root / 'notes.jsonl').write_text('', encoding='utf8')
    return root / 'v2/editorial', entry


@unittest.skipIf(QUICK or not fixture_picture().parent.parent.is_dir() or not chrome_path(), 'needs the fixture and Chrome')
class RealReviewTests(unittest.TestCase):
    """Track 1's real review.py behind the real server and a real page."""
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.project, cls.entry = copy_review_project(cls.root)
        cls.served = Served(cls.project, None)
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.served.close()
        cls.tmp.cleanup()

    def test_state_is_the_real_fixture_picture(self):
        state = json.loads(request(self.served.base, '/api/state')[2])
        self.assertEqual(state['picture']['file_sha256'], self.entry['file_sha256'])
        self.assertEqual((state['frames'], state['fps'], len(state['beats'])), (3214, 30, 56))
        self.assertTrue(all(b['script'] for b in state['beats']))
        self.assertEqual(request(self.served.base, state['video'], headers={'Range': 'bytes=0-99'})[0], 206)

    def test_note_through_the_page_lands_on_the_frame(self):
        context = self.browser.new_context(viewport={'width': 1280, 'height': 800})
        self.addCleanup(context.close)
        page = context.new_page()
        page.goto(self.served.base)
        page.wait_for_function("document.querySelector('#v').readyState >= 2")
        page.evaluate('beatReview.seek(871)')
        page.wait_for_function('beatReview.frame() === 871', timeout=10000)
        page.keyboard.press('ArrowRight')
        page.wait_for_function('beatReview.frame() === 872', timeout=10000)
        page.keyboard.press('n')
        page.keyboard.type('real note')
        page.keyboard.press('Enter')
        page.wait_for_function("document.querySelector('#saved').textContent === 'Saved'")
        rows = [json.loads(line) for line in (self.root / 'notes.jsonl').read_text(encoding='utf8').splitlines()]
        self.assertEqual((rows[-1]['frame'], rows[-1]['beat_id'], rows[-1]['picture_sha']), (872, 'b16', self.entry['file_sha256']))
        page.wait_for_selector('#note-list img', timeout=15000)
        page.reload()
        page.wait_for_function("document.querySelector('#note-list').textContent.includes('real note')")
        page.wait_for_function('beatReview.frame() === 872', timeout=10000)
        self.assertTrue(page.locator('#go-line').is_visible())
        self.assertTrue(page.locator('#approve').is_disabled())

    def test_a_note_is_quick_through_the_real_server(self):
        rows = self.root / 'notes.jsonl'
        kept = rows.read_bytes()
        self.addCleanup(rows.write_bytes, kept)
        times = []
        for i in range(12):
            t = time.perf_counter()
            status = request(self.served.base, '/api/notes', {'text': f'timing {i}', 'frame': 100 + i, 'scope': 'frame', 'picture_sha': self.entry['file_sha256']})[0]
            times.append((time.perf_counter() - t) * 1000)
            self.assertEqual(status, 200)
        times.sort()
        print(f'note POST through the server: median {times[6]:.0f} ms, worst {times[-1]:.0f} ms')
        self.assertLess(times[6], 500)

    def test_a_refused_click_comes_back_with_its_reason(self):
        context = self.browser.new_context()
        self.addCleanup(context.close)
        page = context.new_page()
        page.goto(self.served.base)
        status = page.evaluate("""fetch('/api/waive', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({finding_id: 'nope', why: 'x'})})
            .then(async r => [r.status, (await r.json()).error])""")
        self.assertEqual(status[0], 400)
        self.assertIn('no finding nope', status[1])

    def test_waive_click_writes_one_waiver_and_lifts_the_block(self):
        """A failed sample planted in this copy's output report, so review.py itself reports a FAIL with a frame."""
        report = self.root / 'beat/checks' / self.entry['composition_rev'][:16] / f"output-{self.entry['file_sha256'][:16]}.json"
        kept = report.read_bytes()
        waivers = self.root / 'waivers.json'
        kept_waivers = waivers.read_bytes() if waivers.is_file() else None
        doc = json.loads(kept)
        doc['checks']['O5']['failed'] = [{'frame': 900, 'whole': 20.0}]
        report.write_text(json.dumps(doc), encoding='utf8')
        rows = self.root / 'notes.jsonl'
        kept_notes = rows.read_bytes()
        rows.write_text('', encoding='utf8')

        def restore():
            report.write_bytes(kept)
            rows.write_bytes(kept_notes)
            waivers.unlink(missing_ok=True)
            if kept_waivers is not None:
                waivers.write_bytes(kept_waivers)
        self.addCleanup(restore)
        context = self.browser.new_context(viewport={'width': 1280, 'height': 800})
        self.addCleanup(context.close)
        page = context.new_page()
        page.goto(self.served.base)
        page.wait_for_function("document.querySelector('#finding-list').textContent.includes('O5.sample')", timeout=10000)
        self.assertIn('1 failed check', page.locator('#why').inner_text())
        self.assertTrue(page.locator('#approve').is_disabled())
        row = page.locator('.finding', has_text='O5.sample')
        row.locator('button', has_text='0:30.00').click()
        page.wait_for_function('beatReview.frame() === 900', timeout=10000)
        row.locator('button', has_text='Waive').click()
        page.keyboard.type('looked at it, fine')
        page.keyboard.press('Enter')
        page.wait_for_function("!document.querySelector('#why').textContent.includes('failed check')", timeout=10000)
        written = json.loads(waivers.read_text(encoding='utf8'))
        self.assertEqual((written[-1]['check'], written[-1]['frames'], written[-1]['by'], written[-1]['why']), ('O5.sample', [900], 'chase', 'looked at it, fine'))


if __name__ == '__main__':
    unittest.main(argv=[a for a in sys.argv if a != '--quick'], verbosity=1)
