"""Small stdlib client for the pinned llama.cpp server. Python 3.6+."""
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'config.json').read_text())


def api(endpoint, payload=None):
    body = None if payload is None else json.dumps(payload).encode('utf-8')
    request = urllib.request.Request(CONFIG['server_url'].rstrip('/') + endpoint,
                                     data=body, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=CONFIG['timeout_seconds']) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError('Server HTTP {}: {}'.format(error.code, error.read().decode('utf-8', errors='replace'))) from error
    except urllib.error.URLError as error:
        raise RuntimeError('Start scripts/serve.py in another terminal. ' + str(error.reason)) from error


def token_ids(text):
    return api('/tokenize', {'content': text, 'add_special': True})['tokens']


def generate(messages, temperature=None, max_tokens=None, seed=None, schema=None, trim_history=False):
    messages = list(messages)
    limit = CONFIG['max_tokens'] if max_tokens is None else max_tokens
    if not 1 <= limit < CONFIG['context']:
        raise ValueError('max_tokens must be positive and smaller than context')
    while True:
        prompt = api('/apply-template', {'messages': messages})['prompt']
        tokens = token_ids(prompt)
        if len(tokens) + limit + 16 <= CONFIG['context']:
            break
        if trim_history and len(messages) > 2:
            del messages[1:3]  # remove the oldest complete user/assistant pair
        else:
            raise ValueError('Prompt exceeds the context budget. Shorten the text or retrieved passages.')
    payload = {'prompt': prompt, 'n_predict': limit, 'stream': False, 'cache_prompt': False,
               'temperature': CONFIG['temperature'] if temperature is None else temperature,
               'top_p': CONFIG['top_p'], 'top_k': CONFIG['top_k'],
               'seed': CONFIG['seed'] if seed is None else seed,
               'stop': ['<|im_end|>', '<|endoftext|>']}
    if schema is not None:
        payload['json_schema'] = schema
    result = api('/completion', payload)
    result['messages_used'] = messages
    result['input_tokens_counted'] = len(tokens)
    return result


def ask(question, system='Answer briefly and accurately.', **kwargs):
    return generate([{'role': 'system', 'content': system}, {'role': 'user', 'content': question}], **kwargs)


def parse_json_result(result):
    try:
        return json.loads(result['content'])
    except json.JSONDecodeError as error:
        raise ValueError('Model did not finish valid JSON (stop_type={}). Increase the output budget or simplify the input. Partial output: {}'.format(result.get('stop_type'), result['content'])) from error
