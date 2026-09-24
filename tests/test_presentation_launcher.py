import os
from pathlib import Path
import sys
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import open_presentation as p


class PresentationTests(unittest.TestCase):
    def test_headless_does_not_launch(self):
        with mock.patch.object(p.sys, 'platform', 'linux'), mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(p.subprocess, 'Popen') as launch:
                self.assertFalse(p.open_presentation())
                launch.assert_not_called()

    def test_libreoffice_slideshow(self):
        with mock.patch.object(p.sys, 'platform', 'linux'), mock.patch.dict(os.environ, {'DISPLAY': ':0'}):
            with mock.patch.object(p.shutil, 'which', return_value='/usr/bin/libreoffice'), mock.patch.object(p.subprocess, 'Popen') as launch:
                self.assertTrue(p.open_presentation())
                self.assertEqual(launch.call_args[0][0][:2], ['/usr/bin/libreoffice', '--show'])

    def test_missing_deck_reports_error(self):
        with mock.patch.object(p.Path, 'is_file', return_value=False):
            with self.assertRaisesRegex(RuntimeError, 'missing'):
                p.open_presentation()
