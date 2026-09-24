#!/usr/bin/env python3
"""Read-only Linux storage inventory. Never removes files or invokes sudo."""
import os
from pathlib import Path
import shutil
import subprocess
import heapq
import time
import collections

ROOT = Path(__file__).resolve().parents[1]


def inspect(command, timeout=45):
    print('\n$ ' + ' '.join(command), flush=True)
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True, timeout=timeout)
        output = result.stdout.strip()
        if command[0] == 'du':
            rows = []
            for line in output.splitlines():
                size, separator, path = line.partition('\t')
                if separator and size.isdigit():
                    rows.append((int(size), path))
            output = '\n'.join('{:8.2f} GiB  {}'.format(size / 1024 ** 2, path)
                               for size, path in sorted(rows, reverse=True))
        print(output)
        if result.returncode:
            print('Incomplete (permissions or command unavailable): ' + result.stderr.strip()[:500])
    except (OSError, subprocess.TimeoutExpired) as error:
        print('Inspection incomplete: ' + str(error))


def category(path):
    name = path.lower()
    suffix = Path(name).suffix
    if suffix in ('.gguf', '.safetensors', '.onnx', '.engine', '.pt', '.pth', '.ckpt'):
        return 'AI model/checkpoint candidates'
    if '/.cache/' in name or '/var/cache/' in name:
        return 'Caches'
    if '/var/log/' in name or suffix == '.log':
        return 'Logs'
    if '/.git/' in name or suffix in ('.py', '.cpp', '.c', '.h', '.js', '.ts', '.ipynb', '.sh'):
        return 'Code and Git data'
    if name.startswith(('/usr/', '/opt/', '/lib/', '/bin/', '/sbin/')):
        return 'Installed software and libraries'
    if suffix in ('.mp4', '.mkv', '.avi', '.png', '.jpg', '.jpeg', '.wav', '.mp3'):
        return 'Media'
    if suffix in ('.zip', '.gz', '.xz', '.tar', '.deb'):
        return 'Archives and installers'
    return 'Other files/data'


def file_inventory(root='/', seconds=60, limit=30):
    """Bounded metadata-only scan on one filesystem; count hardlinks once."""
    print('\nFile inventory (allocated disk space; maximum {} seconds):'.format(seconds), flush=True)
    started = time.monotonic()
    device = os.stat(root).st_dev
    seen = set()
    totals = collections.Counter()
    largest = []
    skipped = [0]
    complete = True
    def denied(error):
        skipped[0] += 1
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=denied):
        if time.monotonic() - started > seconds:
            complete = False
            break
        allowed = []
        for name in dirs:
            path = os.path.join(directory, name)
            try:
                if path in ('/proc', '/sys', '/dev', '/run') or os.path.islink(path):
                    continue
                if os.stat(path).st_dev == device:
                    allowed.append(name)
            except OSError:
                skipped[0] += 1
        dirs[:] = sorted(allowed)
        for name in files:
            if time.monotonic() - started > seconds:
                complete = False
                break
            path = os.path.join(directory, name)
            try:
                stat = os.lstat(path)
                import stat as stat_module
                if not stat_module.S_ISREG(stat.st_mode) or stat.st_dev != device:
                    continue
                identity = (stat.st_dev, stat.st_ino)
                if identity in seen:
                    continue
                seen.add(identity)
                size = stat.st_blocks * 512
                totals[category(path)] += size
                row = (size, path)
                if len(largest) < limit:
                    heapq.heappush(largest, row)
                elif row > largest[0]:
                    heapq.heapreplace(largest, row)
            except OSError:
                skipped[0] += 1
    print('\nSpace by category (heuristics; model extensions are candidates):')
    for label, size in totals.most_common():
        print('{:9.3f} GiB  {}'.format(size / 1024 ** 3, label))
    print('\nLargest individual files:')
    for size, path in sorted(largest, reverse=True):
        print('{:9.1f} MiB  {}  [{}]'.format(size / 1024 ** 2, path, category(path)))
    print('Scanned {} unique files; {} inaccessible entries; {}.'.format(
        len(seen), skipped[0], 'time limit reached (partial)' if not complete else 'scan finished'))
    print('Totals exclude unreadable paths, other mounts, filesystem metadata and deleted-but-open files.')


def package_inventory():
    print('\nLargest installed system packages (package metadata; not additional to file totals):', flush=True)
    try:
        result = subprocess.run(['dpkg-query', '-W', '-f=${Installed-Size}\t${Package}\t${Status}\n'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True, timeout=15)
        rows = []
        for line in result.stdout.splitlines():
            fields = line.split('\t')
            if len(fields) == 3 and fields[0].isdigit() and fields[2] == 'install ok installed':
                rows.append((int(fields[0]), fields[1]))
        for size, name in sorted(rows, reverse=True)[:30]:
            print('{:9.1f} MiB  {}'.format(size / 1024, name))
        if result.returncode:
            print('Package inventory incomplete:', result.stderr.strip()[:300])
    except (OSError, subprocess.TimeoutExpired) as error:
        print('Package inventory unavailable:', error)


def main():
    disk = shutil.disk_usage(str(ROOT))
    print('Read-only storage report. No files will be deleted.')
    print('Repository filesystem: {:.1f} GiB used, {:.1f} GiB free / {:.1f} GiB total'.format(
        disk.used / 1024 ** 3, disk.free / 1024 ** 3, disk.total / 1024 ** 3))
    print('A marketed 32 GB card is about 29.8 GiB before partition/filesystem overhead.')
    if disk.free < 6 * 1024 ** 3:
        print('Full setup blocked: requires at least 6 GiB free working space; more is preferable.')
    inspect(['df', '-h', str(ROOT), '/'])
    inspect(['df', '-i', str(ROOT)])
    inspect(['lsblk', '-o', 'NAME,SIZE,FSTYPE,MOUNTPOINT'])
    # Depth-one, same-filesystem scans; no access to other users' private data.
    for path in (str(ROOT), str(Path.home()), '/home', '/var', '/usr', '/opt'):
        if os.path.isdir(path):
            inspect(['du', '-x', '-k', '--max-depth=1', path])
    package_inventory()
    file_inventory()
    print('\nExisting model candidates (paths only; not loaded or modified):')
    inspect(['find', str(Path.home()), str(ROOT), '-xdev', '-type', 'f', '(',
             '-iname', '*.gguf', '-o', '-iname', '*.onnx', '-o', '-iname', '*.engine',
             '-o', '-iname', '*.safetensors', ')', '-print'])
    print('\nReview large directories before cleanup. Permission-denied entries mean the report is partial.')
    print('Do not delete CUDA, TensorRT, system Python, or other users\' files.')


if __name__ == '__main__':
    main()
