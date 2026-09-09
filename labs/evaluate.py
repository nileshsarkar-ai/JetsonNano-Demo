#!/usr/bin/env python3
"""Evaluate real user-supplied prompts and save actual server timings to JSONL."""
import argparse
import datetime
import hashlib
import json
import platform
import time
from pathlib import Path
from common import CONFIG, ROOT, api, ask


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset', type=Path, help='JSONL with prompt and optional expected string')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--temperature', type=float, default=0)
    parser.add_argument('--max-tokens', type=int, default=128)
    args = parser.parse_args()
    lines = [json.loads(line) for line in args.dataset.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not lines or any(not isinstance(x.get('prompt'), str) for x in lines):
        raise ValueError('Dataset must contain nonempty JSONL records with a prompt string')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Never overwrite a previous experiment.
    with args.output.open('x', encoding='utf-8') as stream:
        metadata = {'kind': 'metadata', 'utc': datetime.datetime.utcnow().isoformat() + 'Z',
                    'python': platform.python_version(), 'platform': platform.platform(),
                    'config': CONFIG, 'temperature': args.temperature, 'max_tokens': args.max_tokens,
                    'dataset_sha256': hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
                    'server_props': api('/props'), 'server_models': api('/v1/models')}
        stream.write(json.dumps(metadata, ensure_ascii=False) + '\n')
        for i, record in enumerate(lines):
            start = time.monotonic()
            result = ask(record['prompt'], temperature=args.temperature, max_tokens=args.max_tokens)
            output = {'kind': 'result', 'index': i, 'prompt': record['prompt'],
                      'answer': result['content'].strip(), 'wall_seconds': time.monotonic() - start,
                      'timings': result.get('timings'), 'stop_type': result.get('stop_type'),
                      'input_tokens_counted': result['input_tokens_counted']}
            if 'expected' in record:
                if not isinstance(record['expected'], str):
                    raise ValueError('expected must be a string')
                output['expected'] = record['expected']
                output['exact_match'] = output['answer'].strip().casefold() == record['expected'].strip().casefold()
            stream.write(json.dumps(output, ensure_ascii=False) + '\n')
            stream.flush()
            print('{}/{}: {:.2f}s'.format(i + 1, len(lines), output['wall_seconds']))
    print('Saved:', args.output)


if __name__ == '__main__':
    main()
