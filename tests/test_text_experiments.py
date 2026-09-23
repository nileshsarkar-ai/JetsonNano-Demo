import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'labs'))
import text_experiments as lab


class TextExperimentTests(unittest.TestCase):
    def test_conversation_preserves_actual_previous_response(self):
        output = io.StringIO()
        with mock.patch.object(lab, 'bounded_input', side_effect=['floating', 'It is less dense.', '/quit']):
            with mock.patch.object(lab, 'generate', side_effect=[{'content': 'What affects floating?'}, {'content': 'How could you test that?'}]) as generate:
                lab.Experiment(output).run('tutor', None)
        self.assertIn({'role': 'assistant', 'content': 'What affects floating?'}, generate.call_args[0][0])
        self.assertTrue(generate.call_args[1]['trim_history'])
        self.assertEqual(len(output.getvalue().splitlines()), 2)

    def test_mystery_guess_scored_by_code_not_model(self):
        output = io.StringIO()
        with mock.patch.object(lab, 'bounded_input', return_value='/guess botanist'):
            with mock.patch.object(lab, 'generate', return_value={'content': 'I study leaves.'}) as generate:
                lab.Experiment(output).run('mystery', None)
        self.assertEqual(generate.call_count, 1)
        self.assertTrue(json.loads(output.getvalue().splitlines()[-1])['correct'])

    def test_conversation_stops_after_six_model_replies(self):
        with mock.patch.object(lab, 'bounded_input', return_value='student reply'):
            with mock.patch.object(lab, 'generate', return_value={'content': 'guiding question'}) as generate:
                lab.Experiment(io.StringIO()).run('tutor', None)
        self.assertEqual(generate.call_count, 6)

    def test_memory_persists_and_replaces_explicit_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'facts.json'
            lab.remember(path, 'subject', 'space')
            lab.remember(path, 'subject', 'ocean')
            self.assertEqual(json.loads(path.read_text()), {'subject': 'ocean'})

    def test_memory_limit_does_not_overwrite_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'facts.json'
            for i in range(12): lab.remember(path, str(i), 'fact')
            before = path.read_bytes()
            with self.assertRaises(ValueError): lab.remember(path, 'extra', 'fact')
            self.assertEqual(path.read_bytes(), before)

    def test_sampling_changes_seeds_and_temperature(self):
        with mock.patch.object(lab, 'bounded_input', return_value='fixture'), mock.patch.object(lab, 'ask', return_value={'content': 'model fixture'}) as ask:
            lab.Experiment(io.StringIO()).run('sampling', None)
        self.assertEqual([c[1]['temperature'] for c in ask.call_args_list], [0, .9, .9])
        self.assertEqual([c[1]['seed'] for c in ask.call_args_list], [42, 42, 7])

    def test_triage_invalid_output_is_rejected(self):
        with mock.patch.object(lab, 'bounded_input', return_value='fixture'), mock.patch.object(lab, 'ask', return_value={'content': '{"category":"shell", "reason":"bad"}'}):
            with self.assertRaises(ValueError): lab.Experiment(io.StringIO()).run('triage', None)

    def test_model_failure_never_becomes_fake_output(self):
        output = io.StringIO()
        with mock.patch.object(lab, 'ask', side_effect=RuntimeError('offline')):
            with self.assertRaises(RuntimeError): lab.Experiment(output).run('abstain', None)
        self.assertEqual(output.getvalue(), '')

    def test_summary_critique_receives_actual_generated_summary(self):
        with mock.patch.object(lab, 'bounded_input', return_value='source text'), mock.patch.object(lab, 'ask', side_effect=[{'content': 'actual summary'}, {'content': 'critique'}]) as ask:
            lab.Experiment(io.StringIO()).run('summary', None)
        self.assertIn('source text', ask.call_args[0][0])
        self.assertIn('actual summary', ask.call_args[0][0])

    def test_all_bounded_conditions_log_each_real_response(self):
        for mode, count in [('prompts', 2), ('fewshot', 2), ('injection', 2), ('abstain', 2), ('context', 3)]:
            output = io.StringIO()
            with mock.patch.object(lab, 'bounded_input', return_value='fixture'), mock.patch.object(lab, 'ask', return_value={'content': 'response'}):
                lab.Experiment(output).run(mode, None)
            self.assertEqual(len(output.getvalue().splitlines()), count)

if __name__ == '__main__': unittest.main()
