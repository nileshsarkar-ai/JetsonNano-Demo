#!/usr/bin/env python3
"""Start the pinned llama.cpp CPU server. Keep this terminal running."""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def main():
    config = json.loads((ROOT / 'config.json').read_text())
    manifest = json.loads((ROOT / 'models.json').read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', default=config['model'], choices=[k for k, v in manifest.items() if v['file'].endswith('.gguf')])
    parser.add_argument('--model-file', type=Path, help='Use a locally exported GGUF instead of the manifest model')
    args = parser.parse_args()
    model = args.model_file or ROOT / 'models' / manifest[args.model]['file']
    binary = ROOT / '.vendor/llama.cpp/build/bin/llama-server'
    if not binary.is_file() or not model.is_file():
        raise SystemExit('Build runtimes and download the model first. Missing binary or model.')
    endpoint = urlparse(config['server_url'])
    if endpoint.scheme != 'http' or endpoint.hostname != '127.0.0.1' or endpoint.path not in ('', '/'):
        raise ValueError('The starter server expects http://127.0.0.1:PORT in config.json')
    command = [str(binary), '-m', str(model.resolve()), '--host', endpoint.hostname,
               '--port', str(endpoint.port or 80), '-c', str(config['context']),
               '-t', str(config['threads']), '-tb', str(config['threads']),
               '-b', str(config['batch']), '-ub', str(config['batch']),
               '-np', '1', '-ngl', '0', '--no-context-shift']
    print('Model:', model, '\nCPU only. Context:', config['context'], flush=True)
    os.execv(str(binary), command)


if __name__ == '__main__':
    main()
