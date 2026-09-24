"""Exercise Bash interpreter selection with simulated installations."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LauncherPythonTests(unittest.TestCase):
    def launch(self, versions, override=None):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ('python3.11', 'python', 'python3'):
                path = Path(tmp) / name
                version_status = 0 if versions.get(name) == '3.11' else 1
                path.write_text('#!/bin/bash\nif [[ "$1" == "-c" ]]; then\n'
                                ' if [[ "$2" == *"!= (3, 11)"* ]]; then exit ' + str(version_status) + '; fi\n'
                                ' exit 0\nfi\nprintf "selected:' + name + '\\n"\n')
                path.chmod(0o755)
            env = dict(os.environ, PATH=tmp + ':/usr/bin:/bin')
            env.pop('DEMO_PYTHON', None)
            if override:
                env['DEMO_PYTHON'] = override
            return subprocess.check_output(['/bin/bash', str(ROOT / 'scripts/run_demo.sh'), '--list'],
                                           env=env, universal_newlines=True).strip()

    def test_python_alias_executable_311_preferred_over_system_36(self):
        self.assertEqual(self.launch({'python': '3.11', 'python3': '3.6'}), 'selected:python')

    def test_versioned_311_preferred(self):
        self.assertEqual(self.launch({'python3.11': '3.11', 'python': '3.11'}), 'selected:python3.11')

    def test_fallback_to_system_python(self):
        self.assertEqual(self.launch({'python': '2.7', 'python3': '3.6'}), 'selected:python3')

    def test_explicit_override_preserved(self):
        self.assertEqual(self.launch({'python': '3.11'}, 'python3'), 'selected:python3')
