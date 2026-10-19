"""G03 failure-oriented tests; no native Windows execution claim."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile
import diagnostics as d
import session


class Diagnostics(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'experience-version.json').write_text(json.dumps({'revision': 'a'*40, 'username': 'Alice', 'wrapper_sha256': 'b'*64}))
        (self.root/'game').mkdir()
        (self.root/'player-displays.ini').write_text('[Diagnostics]\nLevel=DEVELOPMENT\n')

    def test_rotation_crash_and_bounds(self):
        with mock.patch.object(d, 'LIMIT', 512):
            for i in range(200):
                d.event(self.root, 'startup', {'code': i, 'path': 'C:\\Users\\Alice'})
            logs = list((self.root/'diagnostics').glob('events.jsonl*'))
            self.assertEqual(len(logs), 1)
            self.assertTrue(all(p.stat().st_size <= 512 for p in logs))
            self.assertLess(d.safe_events(self.root/'diagnostics/events.jsonl')[-1]['fields']['code'], 199)
            retained=logs[0].read_bytes()
            d.event(self.root,'startup',{'code':999})
            self.assertEqual(logs[0].read_bytes(),retained)
            self.assertNotIn(b'Alice', b''.join(p.read_bytes() for p in logs))
        with (self.root/'diagnostics/events.jsonl').open('ab') as stream:
            stream.write(b'{incomplete crash row')
        self.assertTrue(d.safe_events(self.root/'diagnostics/events.jsonl'))

    def test_export_privacy_and_assets(self):
        sensitive = 'C:\\Users\\Alice\\secret SERIAL-123 ghp_fake_token'
        (self.root/'game/v_on.exe').write_text(sensitive)
        (self.root/'game/von.avi').write_text(sensitive)
        (self.root/'game/v_on.ini').write_text('[Option]\n1P Device No.=4\nPassword='+sensitive+'\nUsername=Alice\n2P Device No.=SERIAL-123\n')
        (self.root/'game/player-displays.ini').write_text('[Players]\nPlayer1='+sensitive+'\n[Presentation]\nMode=2\n')
        (self.root/'movie-windows.log').write_text('WINDOW visible=1 title="'+sensitive+' code=777"\nPROCESS_END exit_code=0 samples=32\n')
        d.event(self.root, 'startup', {'code': 0, 'device': sensitive})
        # Even a user-edited event file cannot inject strings into the export.
        with (self.root/'diagnostics/events.jsonl').open('a') as f:
            f.write(json.dumps({'event': 'error', 'utc': sensitive, 'fields': {'code': sensitive}})+'\n')
        target = d.export(self.root)
        with zipfile.ZipFile(target) as z:
            self.assertEqual(set(z.namelist()), {'summary.json','events.json','configuration.json','module-logs.json','runtime-state.json'})
            data = b'\n'.join(z.read(n) for n in z.namelist())
            for secret in (b'Alice', b'SERIAL', b'ghp_', b'777', b'Password'):
                self.assertNotIn(secret, data)
            config = json.loads(z.read('configuration.json'))
            self.assertEqual(config['v_on.ini'], {'1p device no.': 4})
            self.assertEqual(config['player-displays.ini'], {'mode': 2})
            self.assertEqual(json.loads(z.read('module-logs.json'))['movie'][-1]['exit_code'], 0)

    def test_failed_export_preserves_evidence(self):
        d.event(self.root, 'startup'); target = d.export(self.root); previous = target.read_bytes()
        raw = self.root/'movie-windows.log'; raw.write_text('PROCESS_END exit_code=5\n')
        with mock.patch.object(d.zipfile, 'ZipFile', side_effect=OSError('disk unavailable')):
            with self.assertRaises(OSError):
                d.export(self.root)
        self.assertEqual(target.read_bytes(), previous)
        self.assertEqual(raw.read_text(), 'PROCESS_END exit_code=5\n')

    def test_missing_hardware_and_recovery(self):
        empty = {'controllers': [], 'displays': [], 'available': True}
        with mock.patch.object(session.discovery, 'snapshot', return_value=empty):
            prior = session.capture(self.root, None)
            before = (self.root/'diagnostics/events.jsonl').read_bytes()
            session.capture(self.root, prior)
            self.assertEqual(before, (self.root/'diagnostics/events.jsonl').read_bytes())
        rows = d.safe_events(self.root/'diagnostics/events.jsonl')
        self.assertTrue(any(e['event']=='recovery' for e in rows))
        with mock.patch.object(session.discovery, 'snapshot', return_value={'controllers':[{'vid':8015,'pid':36865}], 'displays':[{'width':2560,'height':1440}], 'available':True}):
            session.capture(self.root, prior)
        self.assertIn('2560', (self.root/'diagnostics/events.jsonl').read_text())

    def test_session_lifecycle_crash_and_retry(self):
        child = mock.Mock(returncode=0); child.poll.return_value = 0
        hardware = {'controllers': [], 'displays': [{'width':1920,'height':1080}], 'available':True}
        def launched(*args, **kwargs):
            (self.root/'movie-windows.log').write_text('PROCESS_END exit_code=123 samples=2\n')
            return child
        with mock.patch.object(session.prepare, 'prepare'), mock.patch.object(session.discovery, 'snapshot', return_value=hardware), mock.patch.object(session.subprocess, 'Popen', side_effect=launched):
            self.assertEqual(session.run_session(self.root, 'single', 'NORMAL'), 1)
        rows = d.safe_events(self.root/'diagnostics/events.jsonl')
        self.assertEqual(rows[0]['event'], 'startup')
        self.assertEqual(rows[-1]['event'], 'shutdown')
        self.assertTrue(any(e['event']=='error' and e['fields']['code']==123 for e in rows))
        self.assertFalse((self.root/'diagnostics/session-active').exists())
        with mock.patch.object(session.prepare, 'prepare', side_effect=OSError('failed')):
            with self.assertRaises(OSError):
                session.run_session(self.root, 'mirror', 'NORMAL')
        self.assertTrue((self.root/'diagnostics/session-active').exists())
        child.returncode = 0
        with mock.patch.object(session.prepare, 'prepare'), mock.patch.object(session.discovery, 'snapshot', return_value=hardware), mock.patch.object(session.subprocess, 'Popen', return_value=child):
            session.run_session(self.root, 'mirror', 'DEVELOPMENT')
        self.assertTrue(any(e['event']=='previous_session_incomplete' for e in d.safe_events(self.root/'diagnostics/events.jsonl')))
        self.assertTrue((self.root/'movie-windows.log.1').exists())

    def test_display_save_failure_projection(self):
        # Local resolved paths stay local; operation/error evidence is exportable.
        (self.root/'experience-version.json').write_text(json.dumps({'experience':'F01-P04-F01-private','display':'F01-P04'}))
        (self.root/'diagnostics').mkdir(exist_ok=True)
        (self.root/'diagnostics/display-save.log').write_text('config=C:\\Users\\Private Name\\Game\\player-displays.ini')
        d.event(self.root,'configuration',{'save_stage':10,'winerror':5,'mode':2,'result':0})
        archive=d.export(self.root,game_directory=self.root,return_name='RETURN-THIS-VO-PATCH-EX-F01-P04.zip')
        with zipfile.ZipFile(archive) as z:
            text=''.join(z.read(name).decode() for name in z.namelist())
            self.assertNotIn('Private Name',text)
            self.assertIn('F01-P04-F01-private',text)
            events=json.loads(z.read('events.json'))
            self.assertEqual(events[-1]['fields']['save_stage'],10)
            self.assertEqual(events[-1]['fields']['winerror'],5)

    def test_tail_and_schema(self):
        path = self.root/'large.log'; path.write_bytes(b'x'*(d.LIMIT*3)+b'\nPROCESS_END exit_code=99\n')
        text = d.read_bounded(path)
        self.assertLessEqual(len(text), d.LIMIT+1)
        self.assertEqual(d.project(text)[-1], {'exit_code':99})
        with self.assertRaises(ValueError):
            d.event(self.root, 'raw_input', {'code':1})
        self.assertEqual(d.numbers({'device':'012345', 'code':2**80, 'count':3}), {'count':3})


if __name__ == '__main__':
    unittest.main()
