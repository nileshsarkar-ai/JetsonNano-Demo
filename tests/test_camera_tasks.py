"""Camera project invariants using synthetic detector records, no camera/model runs."""
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'labs'))
import camera_tasks as tasks


def frame(label=None, x=10):
    detections = [] if label is None else [{'label': label, 'confidence': 0.9, 'box': [x, 10, x+10, 20]}]
    return {'width': 100, 'height': 100, 'detections': detections}


class CameraTasksTests(unittest.TestCase):
    def test_one_frame_flicker_ignored(self):
        result = tasks.summarize_frames([frame('cup'), frame(), frame(), frame(), frame()])
        self.assertEqual(result['objects'], {})

    def test_majority_required(self):
        result = tasks.summarize_frames([frame('cup'), frame('cup'), frame('cup'), frame(), frame()])
        self.assertEqual(result['objects']['cup']['count'], 1)
        self.assertEqual(result['objects']['cup']['seen_frames'], 3)

    def test_incomplete_capture_rejected(self):
        with self.assertRaises(ValueError): tasks.summarize_frames([frame(), frame()])

    def test_position_change_from_evidence(self):
        before = tasks.summarize_frames([frame('cup', 10)] * 5)
        after = tasks.summarize_frames([frame('cup', 50)] * 5)
        self.assertEqual(tasks.compare(before, after)['position_changes'], [{'label': 'cup', 'direction': 'right'}])

    def test_small_jitter_ignored(self):
        before = tasks.summarize_frames([frame('cup', 10)] * 5)
        after = tasks.summarize_frames([frame('cup', 12)] * 5)
        self.assertEqual(tasks.compare(before, after)['position_changes'], [])

    def test_appear_and_disappear(self):
        before = tasks.summarize_frames([frame('cup')] * 5)
        after = tasks.summarize_frames([frame('book')] * 5)
        change = tasks.compare(before, after)
        self.assertEqual(change['appeared'], ['book'])
        self.assertEqual(change['disappeared'], ['cup'])

    def test_invalid_quest_rejected(self):
        for targets in [['cup', 'cup'], ['dragon', 'book'], ['cup']]:
            with self.assertRaises(ValueError): tasks.validate_plan({'title': 'Quest', 'targets': targets})

    def test_quest_completion_is_not_model_judgment(self):
        plan = {'title': 'Desk quest', 'targets': ['cup', 'book']}
        a = tasks.summarize_frames([frame('cup')] * 5)
        b = tasks.summarize_frames([frame('book')] * 5)
        self.assertFalse(tasks.quest_score(plan, [a])['complete'])
        self.assertTrue(tasks.quest_score(plan, [a, b])['complete'])

    def test_no_changes_no_fabricated_narration(self):
        snapshot = tasks.summarize_frames([frame('cup')] * 5)
        with mock.patch.object(tasks, 'ask') as ask:
            tasks.narrate([snapshot, snapshot])
            ask.assert_not_called()


if __name__ == '__main__':
    unittest.main()
