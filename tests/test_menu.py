"""Launcher regression tests with dummy children; never runs models or installs packages."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import demo_runtime as runtime
import demo_menu as menu


class ResourceTests(unittest.TestCase):
    def test_low_memory_and_missing_sensor_rejected(self):
        for amount in [None, 100, 767]:
            with mock.patch.object(runtime, 'available_memory', return_value=amount):
                with self.assertRaises(runtime.DemoError):
                    runtime.resource_check(start=True)

    def test_critical_memory_and_heat(self):
        with mock.patch.object(runtime, 'available_memory', return_value=255):
            with self.assertRaises(runtime.DemoError):
                runtime.resource_check()
        with mock.patch.object(runtime, 'available_memory', return_value=1500):
            with mock.patch.object(runtime, 'temperature', return_value=86):
                with self.assertRaises(runtime.DemoError):
                    runtime.resource_check()
            with mock.patch.object(runtime, 'temperature', return_value=50):
                runtime.resource_check(start=True)


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'config.json').write_text(json.dumps({'server_url': 'http://127.0.0.1:8080'}))
        self.supervisor = runtime.Supervisor(self.root)
        self.supervisor.http = mock.Mock()
        self.supervisor.http.open.side_effect = runtime.urllib.error.URLError('fixture: no server')
        self.resources = mock.patch.object(runtime, 'resource_check')
        self.resources.start()

    def tearDown(self):
        self.supervisor.stop_server()
        self.resources.stop()
        self.tmp.cleanup()

    def test_success_and_nonzero_recorded(self):
        self.supervisor.run([sys.executable, '-c', 'print("fixture")'])
        with self.assertRaises(runtime.DemoError):
            self.supervisor.run([sys.executable, '-c', 'raise SystemExit(7)'])
        events = [json.loads(line) for line in (self.supervisor.session / 'events.jsonl').read_text().splitlines()]
        self.assertEqual([x['status'] for x in events if x['event'] == 'finish'], [0, 7])

    def test_timeout_kills_child(self):
        with self.assertRaisesRegex(runtime.DemoError, 'Time limit'):
            self.supervisor.run([sys.executable, '-c', 'import time; time.sleep(30)'], timeout=0.01)

    def test_low_memory_during_child_stops_it(self):
        with mock.patch.object(runtime, 'resource_check', side_effect=[None, runtime.DemoError('low RAM')]):
            with self.assertRaisesRegex(runtime.DemoError, 'low RAM'):
                self.supervisor.run([sys.executable, '-c', 'import time; time.sleep(30)'])

    def test_keyboard_interrupt_stops_child(self):
        with mock.patch.object(runtime, 'resource_check', side_effect=[None, KeyboardInterrupt()]):
            with self.assertRaises(KeyboardInterrupt):
                self.supervisor.run([sys.executable, '-c', 'import time; time.sleep(30)'])

    def test_server_ready_then_stopped(self):
        (self.root / 'scripts').mkdir()
        (self.root / 'scripts/serve.py').write_text('import time; time.sleep(30)')
        response = mock.MagicMock()
        response.__enter__.return_value.status = 200
        self.supervisor.http.open.side_effect = None
        self.supervisor.http.open.return_value = response
        with mock.patch.object(self.supervisor, 'require_free_port'):
            self.supervisor.start_server()
        process = self.supervisor.server
        self.assertIsNone(process.poll())
        self.supervisor.stop_server()
        self.assertIsNotNone(process.poll())

    def test_memory_failure_during_server_load_cleans_up(self):
        (self.root / 'scripts').mkdir()
        (self.root / 'scripts/serve.py').write_text('import time; time.sleep(30)')
        with mock.patch.object(self.supervisor, 'require_free_port'):
            with mock.patch.object(runtime, 'resource_check', side_effect=[None, runtime.DemoError('low RAM')]):
                with self.assertRaisesRegex(runtime.DemoError, 'low RAM'):
                    self.supervisor.start_server()
        self.assertIsNone(self.supervisor.server)

    def test_wrong_endpoint_rejected(self):
        (self.root / 'config.json').write_text(json.dumps({'server_url': 'http://example.com:8080'}))
        with self.assertRaises(runtime.DemoError):
            runtime.Supervisor(self.root)

    def test_existing_server_not_killed(self):
        with mock.patch.object(runtime.socket, 'socket') as socket:
            socket.return_value.__enter__.return_value.connect_ex.return_value = 0
            with self.assertRaisesRegex(runtime.DemoError, 'occupied'):
                self.supervisor.start_server()
        self.assertIsNone(self.supervisor.server)

    def test_server_start_failure_cleanup(self):
        with mock.patch.object(runtime.socket, 'socket') as socket:
            socket.return_value.__enter__.return_value.connect_ex.return_value = 1
            # Real dummy Python child exits because fixture has no scripts/serve.py.
            with self.assertRaisesRegex(runtime.DemoError, 'failed to start'):
                self.supervisor.start_server()
        self.assertIsNone(self.supervisor.server)
        self.assertIsNone(self.supervisor.server_stream)


class MenuTests(unittest.TestCase):
    def test_unknown_choice(self):
        with self.assertRaises(runtime.DemoError):
            menu.Menu(mock.Mock(config=json.loads((ROOT / 'config.json').read_text()))).action('99')

    def test_missing_input_before_server(self):
        supervisor = mock.Mock(config=json.loads((ROOT / 'config.json').read_text()))
        with mock.patch('builtins.input', return_value='/does/not/exist'), mock.patch.object(menu, 'core_missing', return_value=[]):
            with self.assertRaises(runtime.DemoError):
                menu.Menu(supervisor).action('12')
        supervisor.start_server.assert_not_called()

    def test_input_cancel_and_bounds(self):
        with mock.patch('builtins.input', return_value=''):
            with self.assertRaises(runtime.DemoError): menu.prompt('Question')
        for text in ['9999', '-1', 'oops']:
            with mock.patch('builtins.input', return_value=text):
                with self.assertRaises(runtime.DemoError): menu.number('Frames', 300, 1, 3000)

    def test_launcher_help_does_not_install(self):
        result = subprocess.run(['bash', str(ROOT / 'scripts/run_demo.sh'), '--help'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--setup-only', result.stdout)


class MenuLoopTests(unittest.TestCase):
    def test_failed_selection_returns_to_menu_and_cleans_server(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(menu, 'ROOT', Path(tmp)), mock.patch.object(menu.os, 'chdir'):
                with mock.patch.object(menu.subprocess, 'run'), mock.patch.object(menu.sys, 'argv', ['demo_menu.py', '--all']):
                    with mock.patch.object(menu.sys.stdin, 'isatty', return_value=True):
                        with mock.patch.object(menu, 'Supervisor') as supervisor, mock.patch.object(menu, 'Menu') as view:
                            view.return_value.action.side_effect = [runtime.DemoError('fixture failure'), None]
                            with mock.patch('builtins.input', side_effect=['3', '2', '0']):
                                menu.main()
                            self.assertEqual(view.return_value.action.call_count, 2)
                            self.assertGreaterEqual(supervisor.return_value.stop_server.call_count, 3)

    def test_installers_keep_controlling_terminal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'config.json').write_text('{"server_url":"http://127.0.0.1:8080"}')
            supervisor = runtime.Supervisor(root)
            with mock.patch.object(runtime.subprocess, 'run') as run:
                run.return_value.returncode = 0
                supervisor.run(['bash', 'scripts/install_system.sh'], terminal=True)
                self.assertNotIn('start_new_session', run.call_args[1])
                self.assertNotIn('stdout', run.call_args[1])


class DownloadTests(unittest.TestCase):
    def test_network_retry_then_hash_verified(self):
        import hashlib
        import download
        payload = b'verified fixture bytes'
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'model.bin'
            with mock.patch.object(download.urllib.request, 'urlopen', side_effect=[
                    download.urllib.error.URLError('offline'), io.BytesIO(payload)]) as request:
                with mock.patch.object(download.time, 'sleep'):
                    download.download('https://example.invalid/model', dest, hashlib.sha256(payload).hexdigest())
            self.assertEqual(request.call_count, 2)
            self.assertEqual(dest.read_bytes(), payload)

    def test_checksum_failure_does_not_publish(self):
        import download
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'model.bin'
            with mock.patch.object(download.urllib.request, 'urlopen', return_value=io.BytesIO(b'bad')):
                with self.assertRaisesRegex(ValueError, 'SHA-256'):
                    download.download('https://example.invalid/model', dest, '0' * 64)
            self.assertFalse(dest.exists())


class InteractiveTests(unittest.TestCase):
    def test_child_input_then_return_to_parent_terminal(self):
        import pty
        import select
        import time
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'config.json').write_text('{"server_url":"http://127.0.0.1:8080"}')
            code = ("import sys; sys.path.insert(0, {scripts!r}); import demo_runtime as r; "
                    "r.resource_check=lambda **kw: None; s=r.Supervisor({root!r}); "
                    "s.run([sys.executable, '-c', {child!r}]); "
                    "print('BACK', flush=True); assert input() == 'finish'").format(
                        scripts=str(ROOT / 'scripts'), root=str(root), child="print(input('Name?'), flush=True)")
            master, slave = pty.openpty()
            process = subprocess.Popen([sys.executable, '-c', code], stdin=slave, stdout=slave, stderr=slave)
            os.close(slave)
            data = b''
            sent_name = sent_finish = False
            deadline = time.monotonic() + 8
            try:
                while process.poll() is None and time.monotonic() < deadline:
                    readable, _, _ = select.select([master], [], [], 0.1)
                    if readable:
                        try:
                            block = os.read(master, 4096)
                        except OSError:
                            break
                        data += block
                    if b'Name?' in data and not sent_name:
                        os.write(master, b'hello\n')
                        sent_name = True
                    if b'BACK' in data and not sent_finish:
                        os.write(master, b'finish\n')
                        sent_finish = True
                process.wait(timeout=2)
                self.assertEqual(process.returncode, 0, data)
                self.assertTrue(sent_name and sent_finish, data)
            finally:
                if process.poll() is None:
                    process.kill()
                process.wait()
                os.close(master)


if __name__ == '__main__':
    unittest.main()
