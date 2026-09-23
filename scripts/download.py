#!/usr/bin/env python3
"""Download pinned model files with SHA-256 verification. Python 3.6+."""
import argparse
import hashlib
import json
import os
import shutil
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def download(url, dest, expected_hash, size=0):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if sha256(dest) != expected_hash:
            raise ValueError('Hash mismatch in existing file: ' + str(dest))
        print('Verified existing file:', dest)
        return
    partial = dest.with_name(dest.name + '.part')
    if shutil.disk_usage(str(dest.parent)).free < size + 64 * 1024 ** 2:
        raise OSError('Insufficient free disk space for ' + str(dest))
    print('Downloading:', url, flush=True)
    # Restart a partial transfer, but never retry a checksum mismatch or disk error.
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=120) as response, partial.open('wb') as output:
                shutil.copyfileobj(response, output, length=1024 * 1024)
            break
        except urllib.error.HTTPError as error:
            if error.code not in (408, 429, 500, 502, 503, 504) or attempt == 2:
                raise
        except (urllib.error.URLError, socket.timeout, ConnectionError):
            if attempt == 2:
                raise
        print('Network transfer interrupted. Retrying ({}/3)...'.format(attempt + 2), flush=True)
        time.sleep(2 ** (attempt + 1))
    if sha256(partial) != expected_hash:
        raise ValueError('SHA-256 mismatch. Incomplete file retained at ' + str(partial))
    os.replace(str(partial), str(dest))
    print('Verified:', dest)


def main():
    manifest = json.loads((ROOT / 'models.json').read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('models', nargs='*', metavar='MODEL')
    parser.add_argument('--list', action='store_true')
    args = parser.parse_args()
    unknown = sorted(set(args.models) - set(manifest))
    if unknown:
        parser.error('Unknown models: {}. Choose from: {}'.format(
            ', '.join(unknown), ', '.join(sorted(manifest))))
    if args.list:
        for key, item in sorted(manifest.items()):
            print('{:<18} {:7.1f} MiB  {}'.format(key, item['bytes'] / 1024 ** 2, item['file']))
    for key in args.models:
        item = manifest[key]
        url = 'https://huggingface.co/{}/resolve/{}/{}'.format(item['repo'], item['revision'], item['file'])
        download(url, ROOT / 'models' / item['file'], item['sha256'], item['bytes'])
    if not (args.list or args.models):
        parser.print_help()


if __name__ == '__main__':
    main()
