"""Synthetic observations do not establish actual Windows decoding or skip paths."""
import json
import tempfile
import unittest
from pathlib import Path
import runtime_checkpoint as r
import crash_evidence as c
import diagnostics as d

class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.cfg=self.root/'player-displays.ini'
        self.cfg.write_text('[Diagnostics]\nLevel=DEVELOPMENT\n')
    def test_off_and_disable(self):
        self.cfg.unlink();s=r.Checkpoints(self.root,42);s.windows(1,1);s.exited(0)
        self.assertFalse((self.root/'diagnostics').exists())
        self.cfg.write_text('[Diagnostics]\nLevel=DEVELOPMENT\n');s=r.Checkpoints(self.root,42)
        before=r.exported(self.root);self.cfg.unlink();s.windows(1,1);s.exited(1)
        self.assertEqual(before,r.exported(self.root))
    def test_natural_skip_and_early_close_are_unknown(self):
        for cause in ('natural completion','manual skip','early disappearance'):
            with self.subTest(cause=cause):
                s=r.Checkpoints(self.root,42);s.windows(1,1);s.windows(0,0,True)
                self.assertEqual(s.row['movie_result'],'WINDOW_CLOSED_UNKNOWN')
                self.assertNotEqual(s.row['movie_result'],'NATURAL_COMPLETION')
                self.assertNotEqual(s.row['movie_result'],'MANUAL_SKIP_CONFIRMED')
    def test_exit_in_each_phase_and_missing_shutdown(self):
        for windows in ((1,1,False),(0,0,False),(0,0,True)):
            s=r.Checkpoints(self.root,42);s.windows(*windows);s.exited(0xc0000005)
            self.assertEqual(s.row['termination'],'PROCESS_EXITED_UNKNOWN')
            self.assertTrue(r.read(s.folder/'last-completed.json')['complete'])
        s=r.Checkpoints(self.root,43);s.windows(1,1)
        newer=r.Checkpoints(self.root,44)
        self.assertEqual(r.read(newer.folder/'last-incomplete.json')['termination'],'INCOMPLETE_SESSION')
        self.assertEqual(r.read(newer.folder/'last-incomplete.json')['process_id'],43)
    def test_durable_bounded_and_privacy(self):
        ticks=[0];s=r.Checkpoints(self.root,42,clock=lambda:ticks[0])
        for i in range(200):ticks[0]+=6;s.windows(i%2,i%2)
        self.assertLessEqual(len(list(s.folder.iterdir())),4)
        self.assertLess(sum(f.stat().st_size for f in s.folder.iterdir()),32768)
        self.assertEqual(r.read(s.folder/'current.json'),s.row)
        self.assertNotEqual(r.read(s.folder/'previous.json'),s.row)
        (s.folder/'current.json').write_text(json.dumps(dict(s.row,path='C:/Users/Secret',raw_input='key',module='private')))
        self.assertNotIn('Secret',json.dumps(r.exported(self.root)))
        self.assertEqual(r.sanitize({'state':'C:/Users/Secret'}),{'evidence':'OBSERVED'})
    def test_confirmed_windows_exception(self):
        xml='<Event><System><Provider Name="Application Error"/><TimeCreated SystemTime="2026-10-18T12:00:00Z"/></System><EventData>'
        for k,v in {'ProcessId':'0x2a','AppName':'v_on.exe','ExceptionCode':'c0000005','FaultingOffset':'1234','ModuleName':'ddraw.dll','AppPath':'C:/Users/Private/v_on.exe'}.items():
            xml+=f'<Data Name="{k}">{v}</Data>'
        xml+='</EventData></Event>'
        evidence=c.parse(xml,42,0);self.assertEqual(evidence['exception_code'],0xc0000005)
        self.assertIsNone(c.parse(xml,43,0));self.assertIsNone(c.parse(xml,42,9999999999999))
        s=r.Checkpoints(self.root,42);s.exited(1,evidence)
        self.assertEqual(s.row['termination'],'SOFTWARE_EXCEPTION_CONFIRMED')
        self.assertNotIn('Private',json.dumps(s.row))
    def test_windows_wait_exit_after_visible_movie(self):
        from unittest.mock import patch
        import normal_lifecycle as n
        class Function:
            def __init__(self, callback): self.callback=callback
            def __call__(self,*args): return self.callback(*args)
        class Kernel: pass
        kernel=Kernel();waits=iter((258,0))
        def exit_code(handle, pointer): pointer._obj.value=7;return 1
        for name,callback in {'OpenProcess':lambda *a:1,'OpenEventW':lambda *a:2,
                'SetEvent':lambda *a:1,'WaitForSingleObject':lambda *a:next(waits),
                'GetExitCodeProcess':exit_code,'CloseHandle':lambda *a:1}.items():
            setattr(kernel,name,Function(callback))
        with patch.object(n.ctypes,'WinDLL',return_value=kernel,create=True), \
             patch.object(n,'movie_state',return_value=(1,1,((0,0,2560,1440),),True)), \
             patch.object(n.movie_geometry,'evidence',return_value={'geometry_fallback':True}), \
             patch.object(n.crash_evidence,'collect',return_value=None), \
             patch.object(n.discovery,'snapshot',return_value={'controllers':[],'displays':[],'available':False}):
            n.attach(self.root,42,'Local\\VOEX-test')
        row=r.read(self.root/'diagnostics/runtime-state/current.json')
        self.assertEqual(row['exit_code'],7)
        self.assertEqual(row['termination'],'PROCESS_EXITED_UNKNOWN')
        self.assertFalse((self.root/'diagnostics/session-active').exists())

    def test_export_excludes_dumps(self):
        s=r.Checkpoints(self.root,42);s.windows(1,1);d.event(self.root,'startup')
        (self.root/'diagnostics/memory.dmp').write_bytes(b'secret memory')
        import zipfile
        with zipfile.ZipFile(d.export(self.root)) as z:
            self.assertIn('runtime-state.json',z.namelist())
            self.assertFalse(any(n.endswith('.dmp') for n in z.namelist()))
            self.assertNotIn(b'secret memory',b''.join(z.read(n) for n in z.namelist()))

if __name__=='__main__':unittest.main()
