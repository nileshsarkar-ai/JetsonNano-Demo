"""Showcase logic tests. Model answers are test doubles, not claimed inference."""
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'labs'))
sys.path.insert(0, str(ROOT / 'scripts'))
import projects
import demo_menu


class ProjectTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(demo_menu, 'core_missing', return_value=[])
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_named_project_numbers_dispatch_directly(self):
        supervisor = mock.Mock(config=json.loads((ROOT / 'config.json').read_text()))
        menu = demo_menu.Menu(supervisor)
        with mock.patch.object(menu, 'showcase') as show, mock.patch.object(menu, 'camera_projects') as camera:
            for choice, project in [('15', 'agent'), ('16', 'detective'), ('17', 'story'), ('21', 'tour')]:
                menu.action(choice)
                show.assert_called_with(project=project)
            for choice, mode in [('18', 'memory'), ('19', 'hunt'), ('20', 'journal')]:
                menu.action(choice)
                camera.assert_called_with(mode=mode)
        self.assertEqual(supervisor.require_free_port.call_count, 7)

    def test_local_text_routes_exclude_audio_and_training(self):
        supervisor = mock.Mock(config=json.loads((ROOT / 'config.json').read_text()))
        menu = demo_menu.Menu(supervisor)
        modes = {'9': 'memory', '14': 'sampling', '22': 'prompts', '23': 'fewshot',
                 '24': 'triage', '25': 'summary', '26': 'injection', '27': 'abstain', '28': 'context', '29': 'tutor', '30': 'mystery'}
        with mock.patch.object(menu, 'text_experiment') as run:
            for choice, mode in modes.items():
                menu.action(choice)
                run.assert_called_with(mode)
        self.assertNotIn('Speech', demo_menu.MENU)
        self.assertNotIn('LoRA', demo_menu.MENU)

    def test_list_command_needs_no_hardware_or_models(self):
        result = subprocess.run(['bash', str(ROOT / 'scripts/run_demo.sh'), '--list'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('28  Context Memory Challenge', result.stdout)
        self.assertNotIn('Voice Assistant', result.stdout)

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
                with mock.patch.object(demo_menu, 'detect_camera', return_value=None):
                    with mock.patch.object(menu, 'camera_projects') as camera:
                        menu.showcase()
                        camera.assert_not_called()
        self.assertEqual([call[0][1] for call in run.call_args_list], ['agent', 'detective', 'story'])

    def test_tour_survives_camera_failure(self):
        supervisor = mock.Mock(config=json.loads((ROOT / 'config.json').read_text()))
        menu = demo_menu.Menu(supervisor)
        with mock.patch.object(demo_menu, 'prompt', return_value='tour'):
            with mock.patch.object(menu, 'llm'), mock.patch.object(menu, 'py'):
                with mock.patch.object(demo_menu, 'detect_camera', return_value='csi://0'):
                    with mock.patch.object(demo_menu, 'vision_python', return_value='/usr/bin/python3'), mock.patch.object(demo_menu, 'vision_ready', return_value=True):
                        with mock.patch.object(menu, 'camera_projects', side_effect=demo_menu.DemoError('camera unavailable')) as camera:
                            menu.showcase()
                            camera.assert_called_once()
        self.assertGreaterEqual(supervisor.stop_server.call_count, 2)


if __name__ == '__main__':
    unittest.main()
