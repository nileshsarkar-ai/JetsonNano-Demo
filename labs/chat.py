#!/usr/bin/env python3
"""Local chat, prompt experiments, and bounded conversation history."""
import argparse
from common import CONFIG, generate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prompt', help='Single request instead of interactive chat')
    parser.add_argument('--system', default='You are a helpful assistant. Answer briefly.')
    parser.add_argument('--temperature', type=float, default=CONFIG['temperature'])
    parser.add_argument('--max-tokens', type=int, default=CONFIG['max_tokens'])
    parser.add_argument('--seed', type=int, default=CONFIG['seed'])
    args = parser.parse_args()
    if args.prompt is not None and not args.prompt.strip():
        parser.error('--prompt must not be empty')
    messages = [{'role': 'system', 'content': args.system}]
    while True:
        question = args.prompt if args.prompt is not None else input('You (/quit, /reset): ')
        if args.prompt is None and question == '/quit':
            break
        if args.prompt is None and question == '/reset':
            messages = messages[:1]
            continue
        if not question.strip():
            continue
        messages.append({'role': 'user', 'content': question})
        result = generate(messages, temperature=args.temperature, max_tokens=args.max_tokens,
                          seed=args.seed, trim_history=True)
        print('\nNano:', result['content'].strip(), '\n')
        messages = result['messages_used'] + [{'role': 'assistant', 'content': result['content']}]
        if args.prompt is not None:
            break


if __name__ == '__main__':
    main()
