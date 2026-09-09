#!/usr/bin/env python3
"""Constrained JSON extraction. Syntax constraints do not guarantee accuracy."""
import argparse
import json
from common import ask, parse_json_result

SCHEMA = {'type': 'object', 'properties': {
    'names': {'type': 'array', 'maxItems': 2, 'items': {'type': 'string', 'maxLength': 48}},
    'dates': {'type': 'array', 'maxItems': 2, 'items': {'type': 'string', 'maxLength': 48}},
    'quantities': {'type': 'array', 'maxItems': 2, 'items': {'type': 'string', 'maxLength': 48}}},
    'required': ['names', 'dates', 'quantities'], 'additionalProperties': False}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('text')
    args = parser.parse_args()
    result = ask(args.text, system='Extract names, dates, and quantities exactly as written. Use empty arrays for absent fields. Return JSON only.', schema=SCHEMA, temperature=0, max_tokens=256)
    extracted = parse_json_result(result)
    print(json.dumps(extracted, ensure_ascii=False, indent=2))
    absent = [value for values in extracted.values() for value in values if value not in args.text]
    if absent:
        raise SystemExit('Grounding check failed. These generated values do not occur verbatim in the input: ' + repr(absent))
