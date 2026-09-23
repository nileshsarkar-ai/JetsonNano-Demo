#!/usr/bin/env python3
"""Multi-frame camera evidence, scene memory and model-planned visual quests."""
import argparse
import collections
import json
import math
from pathlib import Path
import statistics
from common import ask, parse_json_result

# COCO labels for common objects a presenter can prepare on a table.
TARGETS = ['bottle', 'cup', 'book', 'cell phone', 'chair', 'person']
PLAN_SCHEMA = {'type': 'object', 'properties': {
    'title': {'type': 'string', 'maxLength': 60},
    'targets': {'type': 'array', 'minItems': 2, 'maxItems': 3,
                'items': {'type': 'string', 'enum': TARGETS}}},
    'required': ['title', 'targets'], 'additionalProperties': False}


def records_from_log(path):
    records = []
    for line in path.read_text(errors='replace').splitlines():
        try:
            record = json.loads(line)
            if isinstance(record, dict) and isinstance(record.get('detections'), list):
                records.append(record)
        except ValueError:
            pass
    return records


def summarize_frames(records):
    """Strict majority consensus; movement only for singleton classes, not identity tracking."""
    if len(records) < 3:
        raise ValueError('Need at least three captured detection frames; camera sample is incomplete.')
    counts = []
    positions = collections.defaultdict(list)
    for record in records:
        frame = collections.defaultdict(list)
        width, height = record.get('width', 0), record.get('height', 0)
        if width <= 0 or height <= 0:
            raise ValueError('Capture lacks image dimensions. Update labs/vision.py.')
        for d in record['detections']:
            label = d.get('label')
            box = d.get('box', [])
            confidence = d.get('confidence', 0)
            if (not isinstance(label, str) or len(box) != 4 or
                    not all(isinstance(v, (int, float)) and math.isfinite(v) for v in box) or
                    not isinstance(confidence, (int, float)) or not 0.5 <= confidence <= 1):
                continue
            left, top, right, bottom = box
            if not 0 <= left <= right <= width or not 0 <= top <= bottom <= height:
                continue
            frame[label].append([(left + right) / (2 * width), (top + bottom) / (2 * height)])
        counts.append({label: len(boxes) for label, boxes in frame.items()})
        for label, boxes in frame.items():
            if len(boxes) == 1:
                positions[label].append(boxes[0])
    labels = sorted(set(label for frame in counts for label in frame))
    objects = {}
    for label in labels:
        seen = sum(frame.get(label, 0) > 0 for frame in counts)
        if seen <= len(records) // 2:
            continue
        count = int(statistics.median([frame.get(label, 0) for frame in counts]))
        center = None
        if count == 1 and len(positions[label]) > len(records) // 2:
            center = [statistics.median([p[axis] for p in positions[label]]) for axis in (0, 1)]
        objects[label] = {'count': count, 'seen_frames': seen, 'center': center}
    return {'frames': len(records), 'objects': objects,
            'note': 'Detector estimates, not guaranteed ground truth. Camera must remain fixed.'}


def compare(before, after):
    old, new = before['objects'], after['objects']
    result = {'appeared': sorted(set(new) - set(old)), 'disappeared': sorted(set(old) - set(new)),
              'count_changes': [], 'position_changes': []}
    for label in sorted(set(old) & set(new)):
        a, b = old[label], new[label]
        if a['count'] != b['count']:
            result['count_changes'].append({'label': label, 'before': a['count'], 'after': b['count']})
        if a['count'] == b['count'] == 1 and a['center'] and b['center']:
            dx, dy = b['center'][0] - a['center'][0], b['center'][1] - a['center'][1]
            if math.hypot(dx, dy) >= 0.15:
                result['position_changes'].append({'label': label, 'direction':
                    ('right' if dx > 0 else 'left') if abs(dx) >= abs(dy) else ('down' if dy > 0 else 'up')})
    return result


def validate_plan(plan):
    if not isinstance(plan, dict) or set(plan) != {'title', 'targets'}:
        raise ValueError('Invalid quest plan.')
    targets = plan['targets']
    if (not isinstance(plan['title'], str) or not plan['title'].strip() or len(plan['title']) > 60 or
            not isinstance(targets, list) or not 2 <= len(targets) <= 3 or
            any(not isinstance(x, str) or x not in TARGETS for x in targets) or
            len(set(targets)) != len(targets)):
        raise ValueError('Quest must contain two or three different supported targets.')
    return plan


def quest_score(plan, observations):
    validate_plan(plan)
    seen = set()
    for observation in observations:
        seen.update(observation['objects'])
    return {'found': [x for x in plan['targets'] if x in seen],
            'remaining': [x for x in plan['targets'] if x not in seen],
            'complete': all(x in seen for x in plan['targets'])}


def narrate(history):
    changes = [compare(a, b) for a, b in zip(history, history[1:])]
    print('Measured scene changes:\n' + json.dumps(changes, indent=2), flush=True)
    # A model is never allowed to invent an event when measurements show none.
    if not any(any(value for value in change.values()) for change in changes):
        print('No stable changes detected. No story about an unseen event was generated.')
        return
    evidence = json.dumps(changes)
    if len(evidence) > 1800:
        raise ValueError('Too many changes for the small-model context. Use a simpler tabletop scene.')
    result = ask('Ordered observed changes: ' + evidence,
                 system='Explain these camera detector estimates in three short sentences. '
                        'Use only the supplied changes. Do not invent causes, identities, actions or intent.',
                 max_tokens=96, temperature=0)
    print('Local AI explanation:', result['content'].strip(), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='mode')
    plan = sub.add_parser('plan')
    plan.add_argument('--output', type=Path, required=True)
    explain = sub.add_parser('explain')
    explain.add_argument('history', type=Path)
    args = p.parse_args()
    if args.mode == 'plan':
        for attempt in range(2):
            try:
                proposal = parse_json_result(ask(
                    'Create a fun desk scavenger hunt using two or three distinct objects from: ' + ', '.join(TARGETS),
                    system='Return a JSON object with a short title and targets. Use only supported labels.',
                    schema=PLAN_SCHEMA, max_tokens=96, temperature=0.5))
                validate_plan(proposal)
                break
            except ValueError:
                if attempt:
                    raise
                print('Invalid generated quest; retrying once. No targets substituted.', flush=True)
        with args.output.open('x') as stream:
            json.dump(proposal, stream, indent=2)
        print('AI-created quest:', json.dumps(proposal), flush=True)
    elif args.mode == 'explain':
        narrate(json.loads(args.history.read_text()))
    else:
        p.print_help()


if __name__ == '__main__':
    main()
