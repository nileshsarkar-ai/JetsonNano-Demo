#!/usr/bin/env python3
"""Run the pinned TinyStories C model without Python ML dependencies."""
import argparse
import json
import os
from common import ROOT

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', choices=['stories15m', 'stories42m', 'stories110m'], default='stories15m')
    parser.add_argument('--prompt', default='Once upon a time')
    parser.add_argument('--tokens', type=int, default=128)
    parser.add_argument('--temperature', type=float, default=0.8)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'models.json').read_text())
    binary = ROOT / '.vendor/llama2.c/run'
    tokenizer = ROOT / '.vendor/llama2.c/tokenizer.bin'
    model = ROOT / 'models' / manifest[args.model]['file']
    if not all(p.is_file() for p in [binary, tokenizer, model]):
        raise SystemExit('Build llama2.c and download the selected stories model first.')
    if args.tokens < 1 or args.temperature < 0:
        raise ValueError('Use positive token count and nonnegative temperature')
    command = [str(binary), str(model), '-z', str(tokenizer), '-i', args.prompt,
               '-n', str(args.tokens), '-t', str(args.temperature), '-s', str(args.seed)]
    os.execv(str(binary), command)
