#!/usr/bin/env python3
"""Read-only Linux storage inventory. Never removes files or invokes sudo."""
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def inspect(command, timeout=45):
    print('\n$ ' + ' '.join(command), flush=True)
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True, timeout=timeout)
        print(result.stdout.strip())
        if result.returncode:
            print('Incomplete (permissions or command unavailable): ' + result.stderr.strip()[:500])
    except (OSError, subprocess.TimeoutExpired) as error:
        print('Inspection incomplete: ' + str(error))


def main():
    disk = shutil.disk_usage(str(ROOT))
    print('Read-only storage report. No files will be deleted.')
    print('Repository filesystem: {:.1f} GiB free / {:.1f} GiB total'.format(
        disk.free / 1024 ** 3, disk.total / 1024 ** 3))
    if disk.free < 6 * 1024 ** 3:
        print('Full setup blocked: requires at least 6 GiB free working space; more is preferable.')
    inspect(['df', '-h', str(ROOT), '/'])
    inspect(['df', '-i', str(ROOT)])
    inspect(['lsblk', '-o', 'NAME,SIZE,FSTYPE,MOUNTPOINT'])
    # Depth-one, same-filesystem scans; no access to other users' private data.
    for path in (str(ROOT), str(Path.home()), '/var', '/usr/local', '/opt'):
        if os.path.isdir(path):
            inspect(['du', '-x', '-h', '--max-depth=1', path])
    print('\nExisting model candidates (paths only; not loaded or modified):')
    inspect(['find', str(Path.home()), str(ROOT), '-xdev', '-type', 'f', '(',
             '-iname', '*.gguf', '-o', '-iname', '*.onnx', '-o', '-iname', '*.engine',
             '-o', '-iname', '*.safetensors', ')', '-print'])
    print('\nReview large directories before cleanup. Permission-denied entries mean the report is partial.')
    print('Do not delete CUDA, TensorRT, system Python, or other users\' files.')


if __name__ == '__main__':
    main()
