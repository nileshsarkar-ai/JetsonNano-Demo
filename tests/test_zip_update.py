import io
from pathlib import Path
import sys
import zipfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from update_zip import members

class ZipUpdateTests(unittest.TestCase):
    def archive(self, extra):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as z:
            z.writestr('JetsonNano-Demo-master/', '')
            z.writestr('JetsonNano-Demo-master/scripts/run_demo.sh', 'fixture')
            if extra:
                z.writestr(extra, 'fixture')
        return zipfile.ZipFile(buffer)

    def test_github_root_directory_accepted(self):
        with self.archive(None) as z:
            self.assertEqual(len(members(z)), 1)

    def test_traversal_and_model_overwrite_rejected(self):
        for path in ['JetsonNano-Demo-master/../bad', 'JetsonNano-Demo-master/models/model.gguf']:
            with self.archive(path) as z:
                with self.assertRaises(ValueError):
                    members(z)
