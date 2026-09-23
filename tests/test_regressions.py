"""Hardware-free regression checks; runnable with Python 3.6 unittest."""
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'labs'))
import chat
import vision


class CommandTests(unittest.TestCase):
    def run_download(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'scripts/download.py')] + list(args),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True, timeout=5)

    def test_list_without_models(self):
        result = self.run_download('--list')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('smol135-q4', result.stdout)

    def test_unknown_model_rejected(self):
        result = self.run_download('unknown')
        self.assertEqual(result.returncode, 2)
        self.assertIn('Unknown models', result.stderr)

    def test_no_args_shows_help(self):
        self.assertEqual(self.run_download().returncode, 0)

    def test_empty_prompt_rejected(self):
        for text in ['', '   ']:
            with mock.patch.object(sys, 'argv', ['chat.py', '--prompt', text]):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        chat.main()
            self.assertEqual(raised.exception.code, 2)

    def test_single_prompt_commands_are_literal(self):
        for prompt in ['/reset', '/quit', 'hello']:
            def respond(messages, **kwargs):
                return {'content': 'answer', 'messages_used': messages}
            with mock.patch.object(sys, 'argv', ['chat.py', '--prompt', prompt]):
                with mock.patch.object(chat, 'generate', side_effect=respond) as generate:
                    with contextlib.redirect_stdout(io.StringIO()):
                        chat.main()
                    self.assertEqual(generate.call_count, 1)
                    self.assertEqual(generate.call_args[0][0][-1]['content'], prompt)


class VisionTests(unittest.TestCase):
    def test_lazy_open_and_end_of_stream(self):
        class Source:
            streaming = False
            captures = 0
            closed = False
            def IsStreaming(self): return self.streaming
            def Capture(self):
                self.captures += 1
                self.streaming = self.captures < 3
                return types.SimpleNamespace(width=640, height=480) if self.captures == 2 else None
            def Close(self): self.closed = True
        class Output:
            streaming = False
            renders = 0
            closed = False
            def IsStreaming(self): return self.streaming
            def Render(self, image):
                self.streaming = True
                self.renders += 1
            def SetStatus(self, text): pass
            def Close(self): self.closed = True
        source, output = Source(), Output()
        net = types.SimpleNamespace(Detect=lambda *a, **k: [], GetNetworkFPS=lambda: 1.0)
        inference = types.SimpleNamespace(**{name: lambda *a: net for name in
                                             ['detectNet', 'imageNet', 'poseNet', 'segNet']})
        utils = types.SimpleNamespace(videoSource=lambda *a, **k: source,
                                      videoOutput=lambda *a, **k: output,
                                      cudaAllocMapped=lambda **k: None)
        with mock.patch.dict(sys.modules, jetson_inference=inference, jetson_utils=utils):
            with mock.patch.object(sys, 'argv', ['vision.py', 'detect']):
                with contextlib.redirect_stdout(io.StringIO()):
                    vision.main()
        self.assertEqual(source.captures, 3)
        self.assertEqual(output.renders, 1)
        self.assertTrue(source.closed and output.closed)


class CheckoutTests(unittest.TestCase):
    def test_retry_and_preserve_modified_sources(self):
        def git(*args):
            return subprocess.check_output(['git'] + list(args), universal_newlines=True).strip()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            upstream = root / 'upstream'
            upstream.mkdir()
            git('init', '-q', str(upstream))
            (upstream / 'file.txt').write_text('original\n')
            git('-C', str(upstream), 'add', 'file.txt')
            git('-C', str(upstream), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                'commit', '-qm', 'fixture')
            revision = git('-C', str(upstream), 'rev-parse', 'HEAD')
            dest = root / '.vendor/example'
            dest.mkdir(parents=True)
            git('init', '-q', str(dest))  # Interrupted before origin/fetch.
            command = 'set -euo pipefail\nPROJECT_ROOT="$1"\nsource "$2"\ncheckout example "$3" "$4"'
            args = ['bash', '-c', command, 'test', str(root),
                    str(ROOT / 'scripts/checkout_source.sh'), upstream.as_uri(), revision]
            def run():
                return subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      universal_newlines=True, timeout=10)
            result = run()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(git('-C', str(dest), 'rev-parse', 'HEAD'), revision)
            self.assertEqual(run().returncode, 0)
            (dest / 'file.txt').write_text('user changes\n')
            self.assertNotEqual(run().returncode, 0)
            self.assertEqual((dest / 'file.txt').read_text(), 'user changes\n')


if __name__ == '__main__':
    unittest.main()
