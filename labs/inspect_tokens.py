#!/usr/bin/env python3
"""Inspect actual tokens from the loaded GGUF tokenizer."""
import argparse
import json
from common import api

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('text')
    args = parser.parse_args()
    result = api('/tokenize', {'content': args.text, 'add_special': False, 'with_pieces': True})
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print('Token count:', len(result['tokens']))
