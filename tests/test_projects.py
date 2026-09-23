"""Showcase logic tests. Model answers are test doubles, not claimed inference."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'labs'))
sys.path.insert(0, str(ROOT / 'scripts'))
import projects
import demo_menu


class ProjectTests(unittest.TestCase):
    def test_unknown_tool_not_executed(self):
        with self.assertRaises(ValueError):
            projects.call_tool('run_shell')

    def test_invalid_model_plan_cannot_call_tool(self):
        with mock.patch.object(projects, 'ask', return_value={'content': '{"tools":["run_shell"]}'}):
            with mock.patch.object(projects, 'call_tool') as call:
                with self.assertRaises(ValueError):
                    projects.agent('Read board memory')
                call.assert_not_called()

    def test_valid_plan_passes_actual_tool_result(self):
        with mock.patch.object(projects, 'ask', side_effect=[{'content': '{"tools":["board_status"]}'}, {'content': 'fixture answer'}]) as ask:
            with mock.patch.object(projects, 'board_status', return_value={'memory': 'fixture 123'}):
                projects.agent('Read board memory')
        self.assertIn('fixture 123', ask.call_args[0][0])

    def test_empty_detection_does_not_invent_caption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'detections.json'
            path.write_text('{"detections":[]}')
            with mock.patch.object(projects, 'ask') as ask:
                projects.camera_caption(path)
                ask.assert_not_called()

    def test_auto_story_has_no_input(self):
        with mock.patch.object(projects, 'ask', return_value={'content': 'fixture story'}):
            with mock.patch('builtins.input', side_effect=AssertionError('Unexpected prompt')):
                projects.story(automatic=True)

    def test_tour_skips_unavailable_camera(self):
        supervisor = mock.Mock(config=json.loads((ROOT / 'config.json').read_text()))
        menu = demo_menu.Menu(supervisor)
        with mock.patch.object(demo_menu, 'prompt', return_value='tour'):
            with mock.patch.object(menu, 'llm'), mock.patch.object(menu, 'py') as run:
                with mock.patch.object(demo_menu.importlib.util, 'find_spec', return_value=None):
                    with mock.patch.object(menu, 'camera_projects') as camera:
                        menu.showcase()
                        camera.assert_not_called()
        self.assertEqual([call[0][1] for call in run.call_args_list], ['agent', 'detective', 'story'])

    def test_tour_survives_camera_failure(self):
        supervisor = mock.Mock(config=json.loads((ROOT / 'config.json').read_text()))
        menu = demo_menu.Menu(supervisor)
        with mock.patch.object(demo_menu, 'prompt', return_value='tour'):
            with mock.patch.object(menu, 'llm'), mock.patch.object(menu, 'py'):
                with mock.patch.object(Path, 'exists', return_value=True):
                    with mock.patch.object(demo_menu.importlib.util, 'find_spec', return_value=object()):
                        with mock.patch.object(menu, 'camera_projects', side_effect=demo_menu.DemoError('camera unavailable')) as camera:
                            menu.showcase()
                            camera.assert_called_once()
        self.assertGreaterEqual(supervisor.stop_server.call_count, 2)


if __name__ == '__main__':
    unittest.main()
