"""Preparation routing tests; no camera, native import, model or installation executes."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import readiness as r
import demo_menu as m


class ReadinessTests(unittest.TestCase):
    def test_camera_skips_failed_device(self):
        with mock.patch.object(r, 'camera_candidates', return_value=['v4l2:///dev/video2', 'csi://0']):
            with mock.patch.object(r, 'probe_camera', side_effect=[False, True]):
                self.assertEqual(r.detect_camera(), 'csi://0')

    def test_probe_timeout_is_unavailable(self):
        with mock.patch.object(r.subprocess, 'run', side_effect=subprocess.TimeoutExpired('camera', 12)):
            self.assertFalse(r.probe_camera('csi://0'))

    def test_camera_bindings_use_system_python_fallback(self):
        with mock.patch.object(r.sys, 'executable', '/new/python'):
            with mock.patch.object(r.subprocess, 'run', side_effect=[mock.Mock(returncode=1), mock.Mock(returncode=0)]) as run:
                self.assertEqual(r.vision_python(), '/usr/bin/python3')
                self.assertEqual(run.call_count, 2)

    def test_stale_camera_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'runs').mkdir()
            model = root / 'model'
            model.write_bytes(b'123')
            (root / 'runs/vision-ready-detect.json').write_text(json.dumps({str(model): 3}))
            self.assertTrue(r.vision_ready('detect', root))
            model.write_bytes(b'1')
            self.assertFalse(r.vision_ready('detect', root))

    def test_missing_dependencies_offer_setup_before_demo(self):
        view = m.Menu(mock.Mock(config=json.loads((m.ROOT / 'config.json').read_text())))
        with mock.patch.object(m, 'core_missing', return_value=['model']), mock.patch('builtins.input', return_value='yes'):
            with mock.patch.object(view, 'setup') as setup, mock.patch.object(view, 'text_experiment') as run:
                view.action('29')
                setup.assert_called_once_with()
                run.assert_called_once_with('tutor')

    def test_missing_rag_index_built_before_retrieval(self):
        view = m.Menu(mock.Mock(config=json.loads((m.ROOT / 'config.json').read_text())))
        with mock.patch.object(m.Path, 'is_file', return_value=False), mock.patch('builtins.input', side_effect=['retrieve', 'opening time']):
            with mock.patch.object(view, 'py') as run:
                view.rag()
                self.assertEqual(run.call_args_list[0][0][1], 'index')
                self.assertEqual(run.call_args_list[1][0][1], 'ask')

class StorageTests(unittest.TestCase):
    def test_four_gib_blocks_setup_before_installs(self):
        view = m.Menu(mock.Mock(config=json.loads((m.ROOT / 'config.json').read_text())))
        with mock.patch.object(m, 'resource_check'), mock.patch.object(m.shutil, 'disk_usage', return_value=mock.Mock(free=4 * 1024 ** 3)):
            with self.assertRaisesRegex(m.DemoError, '--storage'):
                view.setup()
        view.s.run.assert_not_called()

    def test_storage_timeout_reports_partial_without_cleanup(self):
        import storage_report
        with mock.patch.object(storage_report.subprocess, 'run', side_effect=subprocess.TimeoutExpired('du', 45)) as run:
            storage_report.inspect(['du', '-x', '-h', '--max-depth=1', '/var'])
            self.assertEqual(run.call_count, 1)

class CompactTests(unittest.TestCase):
    def view(self):
        return m.CompactMenu(mock.Mock(config=json.loads((m.ROOT / 'config.json').read_text())))

    def test_compact_reuses_server_and_downloads_one_model(self):
        view = self.view()
        with mock.patch.object(m, 'resource_check'), mock.patch.object(m.os, 'access', return_value=True):
            with mock.patch.object(view, 'py') as py:
                view.setup_text()
                py.assert_called_once_with('scripts/download.py', 'smol360-q4', timeout=7200)
        view.s.run.assert_not_called()

    def test_compact_camera_prepares_only_detector(self):
        view = self.view()
        with mock.patch.object(m, 'resource_check'), mock.patch.object(m, 'vision_python', return_value='/usr/bin/python3'):
            with mock.patch.object(m.shutil, 'which', return_value='/usr/bin/tool'), mock.patch.object(m, 'vision_ready', return_value=False), mock.patch.object(m.shutil, 'disk_usage', return_value=mock.Mock(free=4 * 1024 ** 3)):
                view.prepare_vision()
        view.s.run.assert_called_once_with(['/usr/bin/python3', 'labs/vision.py', 'detect', '--prepare'], timeout=3600)

    def test_camera_failure_keeps_text_prepared(self):
        view = self.view()
        with mock.patch.object(view, 'setup_text') as text, mock.patch.object(view, 'prepare_vision', side_effect=m.DemoError('needs space')):
            view.setup()
            text.assert_called_once_with()

class InventoryTests(unittest.TestCase):
    def test_models_caches_and_code_classified(self):
        import storage_report as s
        self.assertEqual(s.category('/home/u/model.gguf'), 'AI model/checkpoint candidates')
        self.assertEqual(s.category('/home/u/.cache/pip/blob'), 'Caches')
        self.assertEqual(s.category('/home/u/repo/main.py'), 'Code and Git data')

    def test_inventory_reports_large_files_without_reading_contents(self):
        import storage_report as s
        import io
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'sample.gguf'
            path.write_bytes(b'fixture')
            output = io.StringIO()
            with mock.patch('sys.stdout', output):
                s.file_inventory(tmp, seconds=2)
            self.assertIn(str(path), output.getvalue())
            self.assertIn('1 unique files', output.getvalue())
