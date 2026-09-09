#!/usr/bin/env python3
"""Run the upstream inference benchmark for a downloaded model. Stop the server first."""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    config = json.loads((ROOT / 'config.json').read_text())
    manifest = json.loads((ROOT / 'models.json').read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', default=config['model'], choices=[k for k,v in manifest.items() if v['file'].endswith('.gguf')])
    parser.add_argument('--prompt-tokens', type=int, default=64)
    parser.add_argument('--generated-tokens', type=int, default=32)
    parser.add_argument('--repetitions', type=int, default=3)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if min(args.prompt_tokens, args.generated_tokens, args.repetitions) < 1:
        raise ValueError('Token counts and repetitions must be positive')
    binary = ROOT / '.vendor/llama.cpp/build/bin/llama-bench'
    model = ROOT / 'models' / manifest[args.model]['file']
    if not binary.is_file() or not model.is_file():
        raise FileNotFoundError('Build llama-bench and download the model first')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as output:
        subprocess.run([str(binary), '-m', str(model), '-t', str(config['threads']), '-ngl', '0',
                        '-p', str(args.prompt_tokens), '-n', str(args.generated_tokens),
                        '-b', str(config['batch']), '-ub', str(config['batch']),
                        '-r', str(args.repetitions), '-o', 'json'], stdout=output, check=True)
    print('Actual benchmark saved:', args.output)
