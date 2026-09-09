#!/usr/bin/env python3
"""A narrow tool call with constrained arguments and application validation."""
import argparse
import json
import math
import operator
from common import ask, parse_json_result

SCHEMA = {'type': 'object', 'properties': {
    'operation': {'type': 'string', 'enum': ['add', 'subtract', 'multiply', 'divide']},
    'a': {'type': 'number'}, 'b': {'type': 'number'}},
    'required': ['operation', 'a', 'b'], 'additionalProperties': False}
OPERATIONS = {'add': operator.add, 'subtract': operator.sub,
              'multiply': operator.mul, 'divide': operator.truediv}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('question', help='One binary arithmetic operation')
    args = parser.parse_args()
    call = parse_json_result(ask(args.question, system='Convert one arithmetic request into a JSON calculator call. Supported operations: add, subtract, multiply, divide.', schema=SCHEMA, temperature=0))
    if set(call) != {'operation', 'a', 'b'} or call['operation'] not in OPERATIONS:
        raise ValueError('Invalid tool call')
    for key in ('a', 'b'):
        if type(call[key]) not in (int, float) or not math.isfinite(call[key]) or abs(call[key]) > 1e12:
            raise ValueError('Arguments must be finite numbers with magnitude <= 1e12')
    if call['operation'] == 'divide' and call['b'] == 0:
        raise ValueError('Division by zero')
    print('Proposed call:', json.dumps(call))
    print('Calculator result:', OPERATIONS[call['operation']](call['a'], call['b']))
