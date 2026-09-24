#!/usr/bin/env python3
"""Update a GitHub ZIP checkout, preserving local models, builds, config and logs."""
import argparse
import fcntl
import io
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import urllib.request
import zipfile

URL = 'https://codeload.github.com/nileshsarkar-ai/JetsonNano-Demo/zip/refs/heads/master'


def members(archive):
    result = []
    for item in archive.infolist():
        parts = PurePosixPath(item.filename).parts
        if item.is_dir() and parts == ('JetsonNano-Demo-master',):
            continue
        if len(parts) < 2 or parts[0] != 'JetsonNano-Demo-master' or '..' in parts:
            raise ValueError('Unexpected archive path: ' + item.filename)
        relative = Path(*parts[1:])
        if item.is_dir():
            continue
        if relative.parts[0] in ('.git', '.vendor', '.tools', 'models', 'runs'):
            raise ValueError('Archive contains a reserved local directory')
        if (item.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError('Archive contains a symlink')
        result.append((item, relative))
    if not any(str(p) == 'scripts/run_demo.sh' for _, p in result):
        raise ValueError('Archive does not contain the launcher')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    if not (root / 'scripts/run_demo.sh').is_file():
        raise SystemExit('Run this from an existing JetsonNano-Demo folder using --root "$PWD".')
    if (root / '.git').exists():
        raise SystemExit('This is a Git checkout. Use git pull --ff-only instead.')
    (root / 'runs').mkdir(exist_ok=True)
    with (root / 'runs/demo.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('Close the demo menu/setup before updating.')
        if shutil.disk_usage(str(root)).free < 256 * 1024 ** 2:
            raise SystemExit('Need 256 MiB free for update and source backups.')
        print('Downloading repository source ZIP; no model downloads.', flush=True)
        with urllib.request.urlopen(URL, timeout=120) as response:
            data = response.read(64 * 1024 ** 2 + 1)
        if len(data) > 64 * 1024 ** 2:
            raise ValueError('Repository ZIP exceeds 64 MiB limit')
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = members(archive)
            if sum(i.file_size for i, _ in entries) > 128 * 1024 ** 2:
                raise ValueError('Expanded archive exceeds 128 MiB limit')
            with tempfile.TemporaryDirectory(dir=str(root / 'runs'), prefix='update-stage-') as tmp:
                stage = Path(tmp)
                for item, relative in entries:
                    dest = root / relative
                    if not str(dest.resolve()).startswith(str(root) + os.sep):
                        raise ValueError('Destination escapes repository: ' + str(relative))
                    target = stage / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(item))
                backup = Path(tempfile.mkdtemp(prefix='source-backup-', dir=str(root / 'runs')))
                changed = []
                try:
                    for _, relative in entries:
                        dest = root / relative
                        if relative == Path('config.json') and dest.exists():
                            continue
                        if dest.is_file() and dest.read_bytes() == (stage / relative).read_bytes():
                            continue
                        existed = dest.exists()
                        if existed:
                            saved = backup / relative
                            saved.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(str(dest), str(saved))
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        changed.append((relative, existed))
                        os.replace(str(stage / relative), str(dest))
                except BaseException:
                    for relative, existed in reversed(changed):
                        if existed:
                            shutil.copy2(str(backup / relative), str(root / relative))
                        elif (root / relative).exists():
                            (root / relative).unlink()
                    raise
                print('Updated {} files. Previous changed source files: {}'.format(len(changed), backup))
                print('Models, builds, config and logs preserved. Old unlisted files were not deleted.')
                print('Run: bash scripts/run_demo.sh --setup-only')


if __name__ == '__main__':
    main()
