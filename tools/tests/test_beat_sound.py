"""Sound review safety and real listening media. Only temporary projects are written."""
import argparse
import contextlib
import io
import json
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_beat_review as r
import test_beat_player as player
import test_beat_final as f


def ff(*args):
    return subprocess.run(['ffmpeg', '-v', 'error', '-y', *map(str, args)], capture_output=True, check=True).stdout


class SoundProject(r.Base):
    def setUp(self):
        super().setUp()
        assets = self.project / 'assets'
        assets.mkdir()
        ff('-f', 'lavfi', '-i', 'sine=frequency=300:duration=2', assets / 'voice.wav')
        ff('-f', 'lavfi', '-i', 'sine=frequency=1400:duration=0.15', assets / 'pop-2.wav')
        ff('-f', 'lavfi', '-i', 'sine=frequency=900:duration=0.15', assets / 'whoosh-a.wav')
        self.p.build('<audio id="voice" src="assets/voice.wav"></audio>')
        self.plan = {'duration': 2, 'beats': [{'id': 'b01', 'start': 0, 'anchor': {'event_id': 'a', 't': .4}},
                                              {'id': 'b02', 'start': 1, 'anchor': {'event_id': 'b', 't': 1.4}}]}
        r.store.write_json(self.project / 'plan.json', self.plan)
        self.h = self.p.picture()
        self.sheet = {'version': 1, 'picture_rev': r.sound_mix.picture_rev(self.project), 'cues': [
            {'file': 'assets/pop-2.wav', 't': .4, 'at': .35, 'dur': .15, 'gain': .1, 'event_id': 'a', 'event': 'card lands'},
            {'file': 'assets/whoosh-a.wav', 't': 1.4, 'at': 1.35, 'dur': .15, 'gain': .2, 'event_id': 'b', 'event': 'row leaves'}]}
        self.save_sheet()
        self.still_patch = patch.object(r.review, 'start_still')
        self.still_patch.start()
        self.addCleanup(self.still_patch.stop)

    def save_sheet(self):
        r.store.write_json(self.project / 'sound.json', self.sheet)

    def note(self, **extra):
        return r.review.add_note(self.project, {'scope': 'sound', 'text': 'softer', 'frame': 17, 'picture_sha': self.h,
            'cue_index': 0, 'sheet_identity': r.review.sound_view(self.project)['identity'], **extra})

    def approve(self):
        pic = r.review.picture(self.project)
        record = r.approval.record_of(pic, 'f' * 64, {'frames_compared': 60, 'worst_psnr': 45, 'worst_block': 1,
            'worst_fine': 1, 'worst_chroma': 1, 'identical': 60}, 'PASS')
        r.approval.write_once(r.approval.approvals(self.p.root) / f'{self.h[:16]}.json', record)
        self.assertEqual(r.review.approve(self.project, self.h)['state'], 'approved')

class SoundReview(SoundProject):
    def test_real_sheet_lane_data_uses_t_and_stale_matches_sound_mix(self):
        sound = r.review.state(self.project)['sound']
        self.assertEqual([(c['name'], c['t'], c['gain_db'], c['event']) for c in sound['cues']],
                         [('pop-2', .4, -20, 'card lands'), ('whoosh-a', 1.4, -14, 'row leaves')])
        self.assertFalse(any(c['stale'] for c in sound['cues']))
        self.plan['beats'][0]['anchor']['t'] = .6
        r.store.write_json(self.project / 'plan.json', self.plan)
        self.sheet['picture_rev'] = r.sound_mix.picture_rev(self.project)
        self.save_sheet()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            r.sound_mix.stale(self.project)
        self.assertIn('moved event a', output.getvalue())
        self.assertEqual([c['stale'] for c in r.review.sound_view(self.project)['cues']], [True, False])

    def test_missing_sheet_has_no_cues_and_preview_refuses(self):
        (self.project / 'sound.json').unlink()
        self.assertEqual(r.review.sound_view(self.project), {'present': False, 'identity': None, 'cues': []})
        with self.assertRaisesRegex(ValueError, 'missing sound.json'):
            r.review.sound_preview(self.project, self.h, 'x' * 64)

    def test_note_pins_frame_cue_picture_and_sheet_and_keeps_approval(self):
        self.approve()
        active = (self.p.root / 'approvals/active.json').read_bytes()
        n = self.note()
        self.assertEqual((n['frame'], n['time'], n['cue_index'], n['cue_time'], n['cue_name'], n['picture_sha']),
                         (17, .567, 0, .4, 'pop-2', self.h))
        self.assertEqual(n['sheet_identity'], r.review.sound_view(self.project)['identity'])
        self.assertEqual((self.p.root / 'approvals/active.json').read_bytes(), active)
        self.assertEqual(r.review.approve(self.project, self.h)['state'], 'approved')

    def test_sound_notes_never_freeze_flag_or_enter_close_round(self):
        n = self.note()
        frozen = r.review.freeze(self.project)
        self.assertEqual((frozen['notes'], frozen['flagged']), ([], []))
        with self.assertRaisesRegex(ValueError, 'unknown or closed'):
            r.review.freeze(self.project, adopt=[n['id']])
        with self.assertRaisesRegex(ValueError, 'frozen'):
            r.review.close_round(self.project, done=[n['id']])
        with self.assertRaisesRegex(ValueError, 'frozen'):
            r.review.close_round(self.project, not_done={n['id']: 'later'})
        row = r.review.close_round(self.project)
        record = r.store.read_json(self.p.root / 'rounds' / f"{row['n']:04d}.json")
        self.assertEqual((record['note_ids'], record['not_done']), ([], {}))
        self.assertEqual(r.review.open_notes(self.project, self.p.root, r.review.picture(self.project)), [])

    def test_sound_outcomes_only_change_named_ids_no_picture_round_or_snapshot(self):
        a, b, c = self.note(), self.note(text='later'), self.note(text='unlisted')
        rounds = {p.name: p.read_bytes() for p in (self.p.root / 'rounds').rglob('*') if p.is_file()}
        r.review.close_sound(self.project, done=[a['id']], not_done={b['id']: 'need a quieter cue'})
        open_notes = {n['id']: n for n in r.review.sound_notes(self.project)}
        self.assertEqual(set(open_notes), {b['id'], c['id']})
        self.assertEqual(open_notes[b['id']]['not_done'], 'need a quieter cue')
        self.assertIsNone(open_notes[c['id']]['not_done'])
        self.assertEqual({p.name: p.read_bytes() for p in (self.p.root / 'rounds').rglob('*') if p.is_file()}, rounds)
        with self.assertRaises(ValueError):
            r.review.close_sound(self.project, done=[b['id']], not_done={b['id']: 'why'})
        with self.assertRaises(ValueError):
            r.review.close_sound(self.project, not_done={c['id']: ' '})
        r.review.close_sound(self.project, done=[b['id']])
        self.assertEqual([n['id'] for n in r.review.sound_notes(self.project)], [c['id']])

    def test_drop_sound_note_is_chases_action(self):
        n = self.note()
        served = player.Served(self.project, r.review)
        self.addCleanup(served.close)
        self.assertEqual(player.request(served.base, '/api/drop_note', {'id': n['id']})[0], 403)
        self.assertEqual(player.request(served.base, '/api/drop_note', {'id': n['id']}, {'Origin': served.base})[0], 200)
        self.assertEqual(r.review.sound_notes(self.project), [])
        self.assertEqual(r.store.read_json(self.p.home / 'dropped_notes.json')[0]['by'], 'chase')

    def test_older_picture_and_sheet_stay_open_even_when_not_done(self):
        n = self.note()
        r.review.close_sound(self.project, not_done={n['id']: 'later'})
        self.sheet['cues'][0]['gain'] = .08
        self.save_sheet()
        self.p.picture()
        old = r.review.sound_notes(self.project)[0]
        self.assertTrue(old['older_picture'])
        self.assertTrue(old['older_sheet'])
        self.assertFalse(old['closed'])
        self.assertEqual(old['not_done'], 'later')
        frozen = r.review.freeze(self.project)
        self.assertEqual((frozen['notes'], frozen['flagged']), ([], []))

    def test_old_frame_and_video_jsonl_rows_load_unchanged(self):
        frame = r.review.add_note(self.project, {'text': 'picture', 'scope': 'frame', 'frame': 4, 'picture_sha': self.h})
        video = r.review.add_note(self.project, {'text': 'whole', 'scope': 'video', 'picture_sha': self.h})
        before = (self.p.home / 'notes.jsonl').read_bytes()
        notes = r.review.state(self.project)['notes']
        self.assertEqual([n['id'] for n in notes], [frame['id'], video['id']])
        self.assertEqual([n['scope'] for n in r.review.freeze(self.project)['notes']], ['frame', 'video'])
        self.assertEqual((self.p.home / 'notes.jsonl').read_bytes(), before)
        self.assertEqual(r.review.sound_notes(self.project), [])

    def test_refuse_wrong_cue_sheet_or_picture(self):
        for kw in ({'cue_index': -1}, {'cue_index': True}, {'sheet_identity': 'old'}, {'picture_sha': 'a' * 64}):
            with self.assertRaises(ValueError):
                self.note(**kw)
        self.assertEqual(r.review.read_notes(self.project), [])

    def test_missing_cue_media_still_shows_the_sheet(self):
        (self.project / 'assets/pop-2.wav').unlink()
        sound = r.review.sound_view(self.project)
        self.assertEqual([c['name'] for c in sound['cues']], ['pop-2', 'whoosh-a'])
        self.assertIsNone(sound['identity'])
        self.assertIn('missing cue media', sound['error'])

    def test_sound_close_api_and_picture_note_refusal(self):
        n = self.note()
        frame = r.review.add_note(self.project, {'text': 'picture', 'scope': 'frame', 'frame': 4, 'picture_sha': self.h})
        served = player.Served(self.project, r.review)
        self.addCleanup(served.close)
        self.assertEqual(player.request(served.base, '/api/sound/close', {'done': [frame['id']]})[0], 400)
        self.assertEqual(player.request(served.base, '/api/sound/close', {'not_done': {n['id']: 'later'}})[0], 200)
        self.assertEqual(r.review.sound_notes(self.project)[0]['not_done'], 'later')
        self.assertEqual(player.request(served.base, '/api/sound/close', {'done': [n['id']]})[0], 200)
        self.assertEqual(r.review.sound_notes(self.project), [])

    def preview(self):
        identity = r.review.sound_view(self.project)['identity']
        return Path(r.review.sound_preview(self.project, self.h, identity))

    def test_preview_is_stream_copy_same_frames_and_never_changes_picture_or_approval(self):
        self.approve()
        self.note()
        before = {p.relative_to(self.p.root): p.read_bytes() for p in self.p.root.rglob('*') if p.is_file()}
        pic = r.review.picture(self.project)
        with patch.object(r.sound_mix, 'mix', wraps=r.sound_mix.mix) as mix:
            preview = self.preview()
        mix.assert_called_once()
        self.assertEqual(preview.parent, self.p.root / 'sound-preview')
        self.assertEqual(preview.name, f"{self.h[:16]}-{r.review.sound_view(self.project)['identity'][:16]}.mp4")
        for rel, data in before.items():
            self.assertEqual((self.p.root / rel).read_bytes(), data, str(rel))
        new_files = set(p.relative_to(self.p.root) for p in self.p.root.rglob('*') if p.is_file()) - set(before)
        self.assertEqual(new_files, {preview.relative_to(self.p.root)})
        self.assertEqual(r.review.picture(self.project), pic)
        self.assertEqual(r.review.approve(self.project, self.h)['state'], 'approved')
        def stream(path):
            return ff('-i', path, '-map', '0:v:0', '-c:v', 'copy', '-f', 'h264', '-')
        self.assertEqual(stream(preview), stream(pic['file']))
        for path in (preview, pic['file']):
            probe = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', str(path)], capture_output=True, text=True, check=True)
            self.assertEqual(int(probe.stdout), 60)
        with patch.object(r.sound_mix, 'mix') as mix:
            self.assertEqual(self.preview(), preview)
            mix.assert_not_called()
        self.sheet['cues'][0]['gain'] = .05
        self.save_sheet()
        self.assertNotEqual(self.preview(), preview)
        old_sheet_preview = self.preview()
        ff('-f', 'lavfi', '-i', 'sine=frequency=1800:duration=0.15', self.project / 'assets/pop-2.wav')
        self.assertNotEqual(self.preview(), old_sheet_preview)
        self.h = self.p.picture()
        self.assertNotEqual(self.preview(), preview)

    def test_preview_rejects_inputs_changed_during_mix(self):
        real_mix = r.sound_mix.mix
        def moved(*args):
            real_mix(*args)
            self.sheet['cues'][0]['gain'] = .03
            self.save_sheet()
        with patch.object(r.sound_mix, 'mix', side_effect=moved), self.assertRaisesRegex(ValueError, 'changed during'):
            self.preview()
        self.assertEqual(list((self.p.root / 'sound-preview').glob('*.mp4')), [])

    def test_preview_route_background_range_failure_and_picture_bound_approve_reconcile(self):
        served = player.Served(self.project, r.review)
        self.addCleanup(served.close)
        origin = {'Origin': served.base}
        n = self.note()
        args = {'picture_sha': self.h, 'sheet_identity': n['sheet_identity']}
        self.assertEqual(player.request(served.base, '/api/sound-preview', {**args, 'picture_sha': 'wrong'})[0], 400)
        real = r.review.sound_preview
        def slow(*args):
            time.sleep(.2)
            return real(*args)
        with patch.object(r.review, 'sound_preview', side_effect=slow):
            status, _, body = player.request(served.base, '/api/sound-preview', args)
            self.assertEqual((status, json.loads(body)['state']), (200, 'running'))
            for _ in range(100):
                job = json.loads(player.request(served.base, '/api/state')[2])['sound_preview']
                if job['state'] != 'running':
                    break
                time.sleep(.05)
        self.assertEqual(job['state'], 'done', job)
        status, _, body = player.request(served.base, job['url'], headers={'Range': 'bytes=0-99'})
        self.assertEqual((status, body), (206, self.preview().read_bytes()[:100]))
        for url in ('/media/sound-preview/../current.json', '/media/sound-preview/aaaa.mp4'):
            self.assertEqual(player.request(served.base, url)[0], 404)
        self.assertEqual(json.loads(player.request(served.base, '/api/state')[2])['video'], f'/media/picture/{self.h[:16]}.mp4')
        for path, name in (('/api/approve', 'approve'), ('/api/reconcile', 'reconcile')):
            with patch.object(r.review, name, return_value={}) as call:
                self.assertEqual(player.request(served.base, path, {'picture_sha': self.h, 'why': 'noise'}, origin)[0], 200)
                self.assertEqual(call.call_args.args[1], self.h)
        self.sheet['cues'][0]['gain'] = .01
        self.save_sheet()
        args['sheet_identity'] = r.review.sound_view(self.project)['identity']
        with patch.object(r.review, 'sound_preview', side_effect=RuntimeError('mixer unavailable')):
            player.request(served.base, '/api/sound-preview', args)
            time.sleep(.1)
            failed = json.loads(player.request(served.base, '/api/state')[2])['sound_preview']
        self.assertEqual((failed['state'], failed['error']), ('failed', 'mixer unavailable'))


@unittest.skipIf(not player.chrome_path(), 'needs Chrome')
class SoundBrowser(SoundProject):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(channel='chrome', headless=True, args=['--autoplay-policy=no-user-gesture-required'])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        super().setUp()
        self.served = player.Served(self.project, r.review)
        self.addCleanup(self.served.close)
        self.context = self.browser.new_context(viewport={'width': 900, 'height': 700})
        self.addCleanup(self.context.close)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.goto(self.served.base)
        self.page.wait_for_function("document.querySelector('#v').readyState >= 2")

    def tearDown(self):
        self.assertEqual(self.errors, [])
        super().tearDown()

    def seek(self, frame):
        self.page.evaluate(f'beatReview.seek({frame})')
        self.page.wait_for_function(f'beatReview.frame() === {frame}')

    def test_lane_tab_nearest_composer_outcome_and_drop(self):
        page = self.page
        self.assertEqual(page.locator('#cue-lane .cue').count(), 2)
        self.assertIn('pop-2', page.locator('#cue-lane .cue').first.get_attribute('title'))
        lefts = page.evaluate('[...document.querySelectorAll("#cue-lane .cue")].map(c => c.getBoundingClientRect().left)')
        self.assertGreater(lefts[1], lefts[0] + 1)  # each cue sits at its own time, not stacked at the start
        page.locator('#cue-lane .cue').nth(1).click()
        page.wait_for_function('beatReview.frame() === 42')
        page.locator('.tabs [data-tab="sound"]').click()
        self.assertIn('card lands', page.locator('#sound-list').inner_text())
        self.assertIn('-20.0 dB', page.locator('#sound-list').inner_text())
        self.seek(17)
        page.locator('#sound-list .sound-row').nth(1).get_by_role('button', name='Note', exact=True).click()
        self.assertIn('whoosh-a', page.locator('#at').inner_text())
        page.keyboard.type('softer tail')
        page.keyboard.press('Enter')
        page.wait_for_function("document.querySelector('#saved').textContent === 'Saved'")
        n = r.review.read_notes(self.project)[0]
        self.assertEqual((n['scope'], n['cue_index'], n['frame'], n['picture_sha']), ('sound', 1, 17, self.h))
        self.assertEqual(page.locator('#cue-lane .cue i').count(), 1)
        page.keyboard.press('n')
        self.assertIn('pop-2', page.locator('#at').inner_text())
        page.keyboard.press('Escape')
        r.review.close_sound(self.project, not_done={n['id']: 'need another cue'})
        page.reload()
        page.wait_for_function("document.querySelector('#v').readyState >= 2")
        page.locator('.tabs [data-tab="notes"]').click()
        page.wait_for_function("document.querySelector('#note-list').textContent.includes('need another cue')")
        self.assertIn('sound', page.locator('#note-list').inner_text())
        self.assertNotIn('open note', page.locator('#why').inner_text())
        page.locator('#note-list').get_by_role('button', name='Drop', exact=True).click()
        page.locator('#note-list').get_by_role('button', name='Drop it?', exact=True).click()
        page.wait_for_function("document.querySelector('#note-list').textContent.includes('dropped')")
        self.assertEqual(r.review.sound_notes(self.project), [])

    def test_toggle_keeps_frame_play_state_identity_and_shortcuts(self):
        page = self.page
        self.approve()
        self.seek(15)
        page.keyboard.press('s')
        page.wait_for_function("document.querySelector('#sound-btn').getAttribute('aria-pressed') === 'true'")
        page.wait_for_function('beatReview.frame() === 15')
        self.assertTrue(page.locator('#v').evaluate('(v) => v.paused'))
        self.assertIn('/media/sound-preview/', page.locator('#v').get_attribute('src'))
        self.assertEqual(r.review.picture(self.project)['file_sha256'], self.h)
        page.keyboard.press('ArrowRight')
        page.wait_for_function('beatReview.frame() === 16')
        page.keyboard.press('ArrowLeft')
        page.wait_for_function('beatReview.frame() === 15')
        page.keyboard.press('ArrowDown')
        page.wait_for_function('beatReview.frame() === 30')
        page.keyboard.press('ArrowUp')
        page.wait_for_function('beatReview.frame() === 0')
        page.keyboard.press('n')
        self.assertTrue(page.locator('#composer').is_visible())
        page.keyboard.press('Escape')
        page.keyboard.press('Shift+N')
        self.assertEqual(page.locator('#at').inner_text(), 'Whole video')
        page.keyboard.press('Escape')
        page.keyboard.press('Space')
        page.wait_for_function("!document.querySelector('#v').paused")
        before = page.locator('#v').evaluate('(v) => v.currentTime')
        page.keyboard.press('S')
        page.wait_for_function("document.querySelector('#v').getAttribute('src').includes('/media/picture/') && !document.querySelector('#v').paused")
        after = page.locator('#v').evaluate('(v) => v.currentTime')
        self.assertGreaterEqual(after, before)
        self.assertLess(after - before, .5)
        page.keyboard.press('Space')
        self.assertTrue(page.locator('#v').evaluate('(v) => v.paused'))
        self.assertEqual(r.review.approval_status(self.project)['state'], 'approved')

    def test_seek_during_source_load_and_new_picture_waiting_keep_the_real_identity(self):
        page = self.page
        page.keyboard.press('s')
        page.wait_for_function("document.querySelector('#sound-btn').getAttribute('aria-pressed') === 'true'")
        # Intentionally seek immediately, before the new source necessarily has metadata.
        self.seek(17)
        page.locator('#v').evaluate('(v) => v.loop = true')
        page.keyboard.press('Space')
        page.wait_for_function("!document.querySelector('#v').paused")
        new = self.p.picture()
        self.assertNotEqual(new, self.h)
        page.wait_for_function("!document.querySelector('#banner').hidden", timeout=10000)
        self.assertIn(self.h[:16], page.locator('#v').get_attribute('src'))
        self.assertIn('a new picture is waiting', page.locator('#why').inner_text())
        self.assertTrue(page.locator('#approve').is_disabled())

    def test_missing_sheet_and_visible_build_failure(self):
        page = self.page
        (self.project / 'sound.json').unlink()
        page.reload()
        page.locator('.tabs [data-tab="sound"]').click()
        self.assertIn('after the picture is approved', page.locator('#sound-list').inner_text())
        self.assertEqual(page.locator('#cue-lane .cue').count(), 0)
        self.assertTrue(page.locator('#sound-btn').is_disabled())
        self.save_sheet()
        page.reload()
        page.wait_for_function("!document.querySelector('#sound-btn').disabled")
        released = threading.Event()
        def failure(*args):
            released.wait(10)
            raise ValueError('cannot mix this cue')
        with patch.object(r.review, 'sound_preview', side_effect=failure):
            try:
                page.locator('#sound-btn').click()
                page.wait_for_function("document.querySelector('#sound-status').textContent.includes('Building')")
            finally:
                released.set()
            page.wait_for_function("document.querySelector('#sound-status').textContent.includes('cannot mix this cue')")
        self.assertIn('/media/picture/', page.locator('#v').get_attribute('src'))

    def test_themes_contrast_and_narrow_layout(self):
        page = self.page
        self.assertEqual(page.locator('h1').inner_text(), 'chase_ai_')
        self.assertEqual(page.title(), 'Beat Review')
        self.assertEqual(page.locator('html').get_attribute('data-theme'), 'dark')
        def luminance(h):
            if len(h) == 4:
                h = '#' + ''.join(c * 2 for c in h[1:])
            v = [int(h[i:i+2], 16) / 255 for i in (1, 3, 5)]
            v = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in v]
            return sum(x * w for x, w in zip(v, (.2126, .7152, .0722)))
        for theme in ('light', 'dark'):
            page.locator('#theme').select_option(theme)
            tokens = page.evaluate("Object.fromEntries(['bg','panel','ink','mute','mute2','accent','on','warn','bad'].map(k => [k,getComputedStyle(document.documentElement).getPropertyValue('--'+k).trim()]))")
            for fg, bg in [('ink','bg'), ('ink','panel'), ('mute','panel'), ('mute2','panel'), ('warn','panel'), ('bad','panel'), ('accent','on'), ('accent','panel')]:
                a, b = sorted([luminance(tokens[fg]), luminance(tokens[bg])])
                self.assertGreaterEqual((b + .05) / (a + .05), 4.5, (theme, fg, bg))
        page.locator('#theme').select_option('auto')
        for scheme, expected in (('light', '#ebe8e0'), ('dark', '#0d0d0c')):
            page.emulate_media(color_scheme=scheme)
            self.assertEqual(page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()"), expected)
        for width, height in ((375,812), (618,322), (900,700), (1280,800), (1000,420)):
            page.set_viewport_size({'width': width, 'height': height})
            page.wait_for_timeout(100)
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width)
            self.assertEqual(page.locator('#cue-lane .cue').count(), 2)


class SoundApproval(SoundProject):
    fresh = r.Approval.fresh
    judged = r.Approval.judged

    def setUp(self):
        super().setUp()
        self.folder = r.approval.approvals(self.p.root)
        self.tag = self.h[:16]

    def test_open_sound_note_does_not_stop_reconcile(self):
        self.note()
        self.assertEqual(self.judged(8)['state'], 'reconcile')
        self.assertEqual(r.review.reconcile(self.project, self.h, 'clean noise')['state'], 'approved')
        self.assertEqual(len(r.review.sound_notes(self.project)), 1)

    def test_open_sound_note_does_not_stop_a_clean_check(self):
        self.note()
        self.assertEqual(self.judged(3)['state'], 'approved')


class SoundFinal(f.Base):
    def test_open_sound_note_does_not_block_final_or_delivery(self):
        active = r.store.read_json(self.root / 'approvals/active.json')
        folder = next(self.root.glob(f"stitched/review-{active['file_sha256'][:16]}-*"))
        r.store.write_json(self.root / 'current.json', {'review': {**active, 'stitched': folder.name,
            'status': 'UNVERIFIED', 'file': str(folder / 'review.mp4')}})
        n = {'id': 'sound1', 'scope': 'sound', 'text': 'quieter', 'frame': 6, 'time': .2, 'picture_sha': active['file_sha256'],
             'cue_index': 0, 'cue_time': .2, 'cue_name': 'pop', 'sheet_identity': 'old', 'older_picture': False}
        path = self.home / 'notes.jsonl'
        path.write_text(json.dumps({**n, 'scope': 'frame'}) + '\n', encoding='utf8')
        with self.assertRaisesRegex(ValueError, 'notes still open'):
            f.final.approval_of(self.project, self.m['composition_rev'], self.lock['revision'])
        path.write_text(json.dumps(n) + '\n', encoding='utf8')
        self.assertEqual(f.final.approval_of(self.project, self.m['composition_rev'], self.lock['revision'])['approved_file_sha256'], active['file_sha256'])
        bundle = f.final.freeze(self.project)
        picture = self.stitched(bundle)
        args = argparse.Namespace(project=str(self.project), base='sound-note', mode='final', stitched=str(picture), picture=None,
                                  adopt_picture=False, fps=None, resolution=None, source_swap=[])
        with patch.object(f.deliver, 'ROOT', self.work), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(f.deliver.deliver(args), 0)
        self.assertTrue((self.work / 'out/sound-note.mp4').is_file())
        self.assertEqual(r.review.read_notes(self.project), [n])


if __name__ == '__main__':
    unittest.main(verbosity=1)
