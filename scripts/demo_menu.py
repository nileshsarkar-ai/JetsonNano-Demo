#!/usr/bin/env python3
"""Sequential, supervised demo menu for original Jetson Nano / Python 3.6."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'labs'))
from camera_tasks import summarize_frames, records_from_log, compare, quest_score
from readiness import core_missing, vision_python, detect_camera, vision_ready, VISION_MODES
from demo_runtime import DemoError, ROOT, Supervisor, available_memory, resource_check, temperature


def prompt(label, default=None):
    value = input(label + (' [{}]'.format(default) if default is not None else '') + ': ').strip()
    value = value or default
    if not value:
        raise DemoError('No value entered. Returning to menu.')
    return value


def file_prompt(label, default=None):
    path = Path(prompt(label, default)).expanduser().resolve()
    if not path.is_file():
        raise DemoError('File not found: {}'.format(path))
    if path.stat().st_size > 64 * 1024 ** 2:
        raise DemoError('For this demo menu, input files must be at most 64 MiB. Use a smaller rehearsal input.')
    return str(path)


def number(label, default, minimum, maximum):
    try:
        result = int(prompt(label, str(default)))
    except ValueError:
        raise DemoError('Enter a whole number.')
    if not minimum <= result <= maximum:
        raise DemoError('Choose a value from {} to {}.'.format(minimum, maximum))
    return str(result)


class Menu:
    def __init__(self, supervisor):
        self.s = supervisor
        self.manifest = json.loads((ROOT / 'models.json').read_text())
        for field in ('model',):
            if self.s.config.get(field) not in self.manifest:
                raise DemoError('config.json {} must name a model in models.json.'.format(field))
        required = ('max_tokens', 'temperature', 'top_p', 'top_k', 'seed', 'timeout_seconds',
                    'context', 'batch', 'threads')
        missing = [key for key in required if key not in self.s.config]
        if missing:
            raise DemoError('Missing config fields: ' + ', '.join(missing))
        limit = self.s.config['max_tokens']
        if type(limit) is not int or not 1 <= limit < self.s.config['context']:
            raise DemoError('max_tokens must be positive and smaller than context.')

    def py(self, script, *args, **kwargs):
        self.s.run([sys.executable, script] + list(args), **kwargs)

    def need_binary(self, relative):
        path = ROOT / relative
        if not path.is_file() or not os.access(str(path), os.X_OK):
            raise DemoError('Runtime missing. Select 1: Prepare / repair core setup.')

    def model(self, key):
        path = ROOT / 'models' / self.manifest[key]['file']
        if not path.is_file():
            raise DemoError('Model {} missing. Select 1 to prepare models before the presentation.'.format(key))
        needed = path.stat().st_size * 2 / 1024 ** 2 + 512
        available = available_memory()
        if available is None or available < needed:
            raise DemoError('Need approximately {:.0f} MiB available RAM for this model with headroom. Close other programs.'.format(needed))
        # The downloader verifies cached files without Internet access.
        self.py('scripts/download.py', key, timeout=300, monitor=False)

    def llm(self, model=None):
        self.need_binary('.vendor/llama.cpp/build/bin/llama-server')
        self.model(model or self.s.config['model'])
        self.s.start_server(model=model)

    def setup(self):
        resource_check(start=True)
        if shutil.disk_usage(str(ROOT)).free < 6 * 1024 ** 3:
            raise DemoError('Setup requires at least 6 GiB free disk headroom. Run bash scripts/run_demo.sh --storage to inspect usage; nothing has been installed.')
        jobs = os.environ.get('JOBS', '1')
        if jobs not in ('1', '2'):
            raise DemoError('Use JOBS=1 (recommended) or JOBS=2 on this board.')
        print('Preparation needs Internet and sudo. It can take a long time; do this before the event.')
        self.s.run(['bash', 'scripts/install_system.sh'], monitor=False, terminal=True)
        self.s.run(['env', 'JOBS=' + jobs, 'bash', 'scripts/build_runtimes.sh'], timeout=14400)
        self.py('scripts/download.py', self.s.config['model'],
                'stories15m', 'smol360-q4', timeout=7200)
        self.py('labs/rag.py', 'index', '--notes', str(ROOT / 'data/notes'))
        self.prepare_vision()
        missing = core_missing(verify=True)
        if missing:
            raise DemoError('Preparation incomplete: ' + ', '.join(missing))
        print('Core preparation verified. Camera:', detect_camera() or 'not detected; text demos remain available.')

    def prepare_vision(self):
        resource_check(start=True)
        if shutil.disk_usage(str(ROOT)).free < 6 * 1024 ** 3:
            raise DemoError('Vision preparation needs 6 GiB free disk space.')
        if not vision_python():
            self.s.run(['env', 'JOBS=1', 'bash', 'scripts/build_vision.sh'], monitor=False, terminal=True)
        executable = vision_python()
        if not executable:
            raise DemoError('Native camera bindings cannot import in either Python. Check the JetPack installation.')
        for mode in VISION_MODES:
            self.s.run([executable, 'labs/vision.py', mode, '--prepare'], timeout=3600)
        print('Camera models prepared. Camera:', detect_camera() or 'not detected')

    def camera_source(self, automatic=False):
        detected = detect_camera()
        if detected:
            print('Detected working camera:', detected)
        if automatic:
            if not detected:
                raise DemoError('No working camera detected; camera stage skipped.')
            return detected
        return prompt('Camera URI (or video path)', detected)

    def ensure_vision(self, mode):
        executable = vision_python()
        if not executable or not vision_ready(mode):
            if prompt('Camera software/model needs preparation. Prepare now? yes / no', 'yes').lower() != 'yes':
                raise DemoError('Camera stage skipped.')
            self.prepare_vision()
            executable = vision_python()
        return executable

    def status(self):
        self.py('scripts/check_board.py', '--strict', monitor=False)
        print('Available RAM: {} MiB; highest reported temperature: {} C'.format(available_memory(), temperature()))
        print('Free disk: {:.1f} GiB'.format(shutil.disk_usage(str(ROOT)).free / 1024 ** 3))
        for key in (self.s.config['model'], 'smol360-q4', 'stories15m'):
            path = ROOT / 'models' / self.manifest[key]['file']
            print('{}: {}'.format(key, 'present (hash checked before use)' if path.is_file() else 'MISSING'))
        for relative in ('.vendor/llama.cpp/build/bin/llama-server', '.vendor/llama.cpp/build/bin/llama-bench',
                         '.vendor/llama2.c/run'):
            print('{}: {}'.format(relative, 'ready' if os.access(str(ROOT / relative), os.X_OK) else 'MISSING'))
        for name in ('ffmpeg',):
            print('{}: {}'.format(name, shutil.which(name) or 'MISSING'))
        for module in ('jetson_inference', 'jetson_utils'):
            print('{}: {}'.format(module, 'installed' if importlib.util.find_spec(module) else 'optional / missing'))
        print('Menu Python:', sys.version.split()[0], sys.executable)
        print('Camera Python:', vision_python() or 'not installed')
        print('Camera:', detect_camera() or 'none responding')
        print('Core missing/corrupt:', ', '.join(core_missing(verify=True)) or 'none')
        for mode in VISION_MODES:
            print('Camera {}: {}'.format(mode, 'prepared' if vision_ready(mode) else 'needs preparation'))
        print('Logs:', self.s.session)
        print('Select a named experiment to begin.')

    def rag(self):
        mode = prompt('RAG: index / retrieve / ask', 'retrieve')
        if mode == 'index':
            directory = Path(prompt('Notes directory', str(ROOT / 'data/notes'))).expanduser()
            if not directory.is_dir():
                raise DemoError('Notes directory does not exist.')
            if sum(p.stat().st_size for p in directory.rglob('*') if p.is_file() and p.suffix.lower() in ('.txt', '.md')) > 5 * 1024 ** 2:
                raise DemoError('Use at most 5 MiB of notes for the demo index.')
            self.py('labs/rag.py', 'index', '--notes', str(directory))
        elif mode in ('retrieve', 'ask'):
            if not (ROOT / 'runs/rag-index.json').is_file():
                self.py('labs/rag.py', 'index', '--notes', str(ROOT / 'data/notes'))
            question = prompt('Question')
            if mode == 'ask':
                self.llm()
            args = [] if mode == 'ask' else ['--retrieve-only']
            self.py('labs/rag.py', 'ask', question, *args)
        else:
            raise DemoError('Unknown RAG mode.')

    def vision(self):
        mode = prompt('Vision: install / detect / classify / pose / segment', 'detect')
        if mode == 'install':
            self.prepare_vision()
            return
        if mode not in ('detect', 'classify', 'pose', 'segment'):
            raise DemoError('Unknown vision mode.')
        executable = self.ensure_vision(mode)
        source = self.camera_source()
        if source.startswith('v4l2://') and not Path(source[len('v4l2://'):]).exists():
            raise DemoError('Camera device does not exist. Check connection and camera URI.')
        output = prompt('Output URI (use a file path on headless boards)', 'display://0' if os.environ.get('DISPLAY') else str(self.s.session / ('vision-{}.mp4'.format(self.s.counter + 1))))
        frames = number('Maximum frames', 300, 1, 3000)
        args = ['--frames', frames]
        self.s.run([executable, 'labs/vision.py', mode, source, output] + args, timeout=1800)

    def capture_snapshot(self, source):
        executable = self.ensure_vision('detect')
        if source.startswith('v4l2://') and not Path(source[len('v4l2://'):]).exists():
            raise DemoError('Camera device unavailable; skipping camera project.')
        # Every call finishes and releases TensorRT before the next LLM load.
        output = 'display://0' if os.environ.get('DISPLAY') else str(self.s.session / ('sample-{}.mp4'.format(self.s.counter + 1)))
        self.s.run([executable, 'labs/vision.py', 'detect', source, output, '--frames', '5', '--interval', '0.4'], timeout=120)
        snapshot = summarize_frames(records_from_log(self.s.session / '{:03d}.log'.format(self.s.counter)))
        path = self.s.session / ('snapshot-{}.json'.format(self.s.counter))
        path.write_text(json.dumps(snapshot, indent=2))
        print('Stable multi-frame observation:', json.dumps(snapshot['objects']), flush=True)
        return snapshot

    def camera_projects(self, automatic=False, mode=None):
        print('\nCAMERA PROJECTS: memory / hunt / journal')
        print('memory: compare before/after; hunt: AI-planned visual challenge; journal: a three-observation scene history.')
        print('Keep the camera fixed. Prepare a cup, bottle, book or phone; no face identification is used.')
        mode = mode or ('journal' if automatic else prompt('Camera project', 'memory').lower())
        if mode not in ('memory', 'hunt', 'journal'):
            raise DemoError('Choose memory, hunt or journal.')
        source = self.camera_source(automatic)
        history = []
        # Establish camera viability before asking the model to create a quest.
        history.append(self.capture_snapshot(source))
        if mode == 'hunt':
            self.llm('smol360-q4')
            path = self.s.session / ('quest-{}.json'.format(self.s.counter + 1))
            self.py('labs/camera_tasks.py', 'plan', '--output', str(path))
            self.s.stop_server()
            plan = json.loads(path.read_text())
            observations = []
            for round_id in range(3):
                input('Arrange the quest objects in view, then Enter to scan (Ctrl+C cancels): ')
                observations.append(self.capture_snapshot(source))
                score = quest_score(plan, observations)
                print('QUEST SCORE:', json.dumps(score), flush=True)
                (self.s.session / ('quest-score-{}.json'.format(self.s.counter))).write_text(json.dumps(score, indent=2))
                if score['complete']:
                    print('All targets observed across this quest. Completion uses detector evidence, not model judgment.')
                    break
            return
        captures = 2 if mode == 'memory' else 3
        for index in range(1, captures):
            if automatic:
                print('Move, add or remove a tabletop object now. Next observation in 5 seconds.', flush=True)
                time.sleep(5)
            else:
                input('Move, add or remove an object, keep the camera fixed, then Enter: ')
            history.append(self.capture_snapshot(source))
            print('Changes:', json.dumps(compare(history[-2], history[-1])), flush=True)
        path = self.s.session / ('scene-history-{}.json'.format(self.s.counter))
        path.write_text(json.dumps(history, indent=2))
        if not any(any(value for value in compare(a, b).values()) for a, b in zip(history, history[1:])):
            print('No stable changes observed. Scene history saved.')
            return
        self.llm('smol360-q4')
        self.py('labs/camera_tasks.py', 'explain', str(path))

    def showcase(self, project=None):
        if project is None:
            print('Choose agent (Mission Control), detective (Document Detective), story (Story Director), camera, or tour (prepared sequence).')
        else:
            print('Starting:', {'agent': 'Mission Control: Tool-Planning Assistant',
                  'detective': 'Document Detective: Answers with Evidence',
                  'story': 'Story Director: Audience-Controlled Fiction',
                  'tour': 'Prepared Student Demonstrations'}.get(project, project))
        project = project or prompt('Choose project', 'tour').lower()
        if project == 'camera':
            self.camera_projects()
            return
        if project not in ('tour', 'agent', 'detective', 'story'):
            raise DemoError('Choose a showcase name shown above.')
        self.llm('smol360-q4')
        if project == 'tour':
            for name in ('agent', 'detective'):
                print('\n=== ' + name.upper() + ' ===', flush=True)
                self.py('labs/projects.py', name)
            print('\n=== STORY DIRECTOR ===', flush=True)
            self.py('labs/projects.py', 'story', '--auto')
            self.s.stop_server()
            if detect_camera() and vision_python() and vision_ready('detect'):
                try:
                    self.camera_projects(automatic=True)
                except (DemoError, OSError, ValueError) as error:
                    print('Optional camera skipped: {}'.format(error))
                finally:
                    self.s.stop_server()
            else:
                print('Optional camera skipped: no working camera or prepared vision model.')
            print('Tour complete. Text outputs came from the local model; skipped stages were reported.')
        else:
            args = []
            if project in ('agent', 'detective'):
                question = prompt('Your request', 'Read the exhibit brief and current board memory, then give a guide briefing.' if project == 'agent' else 'What does the Ocean Watch exhibit measure?')
                args = ['--question', question]
            self.py('labs/projects.py', project, *args, timeout=0 if project == 'story' else 900)

    def text_experiment(self, mode):
        self.llm('smol360-q4')
        self.py('labs/text_experiments.py', mode, '--output',
                str(self.s.session / ('text-experiment-{}.jsonl'.format(self.s.counter + 1))), timeout=1200)

    def action(self, choice):
        if choice.isdigit() and 3 <= int(choice) <= 30 and choice != '13':
            missing = core_missing()
            if missing:
                print('Missing dependencies:', ', '.join(missing))
                if prompt('Run setup now? yes / no', 'yes').lower() != 'yes':
                    raise DemoError('Selection cancelled; setup is available as menu 1.')
                self.setup()
        text_modes = {'9': 'memory', '14': 'sampling', '22': 'prompts', '23': 'fewshot',
                      '24': 'triage', '25': 'summary', '26': 'injection', '27': 'abstain', '28': 'context', '29': 'tutor', '30': 'mystery'}
        if choice in text_modes:
            self.s.require_free_port()
            self.text_experiment(text_modes[choice])
            return
        if choice in ('15', '16', '17', '18', '19', '20', '21'):
            self.s.require_free_port()
            if choice in ('18', '19', '20'):
                self.camera_projects(mode={'18': 'memory', '19': 'hunt', '20': 'journal'}[choice])
            else:
                self.showcase(project={'15': 'agent', '16': 'detective', '17': 'story', '21': 'tour'}[choice])
            return
        if choice.lower() in ('s', 'c', 'u') or choice in [str(x) for x in range(3, 15)]:
            self.s.require_free_port()
        if choice.lower() == 'c': self.camera_projects()
        elif choice.lower() == 'u':
            print('3 chat; 4 question; 5 tokens; 6 extraction; 7 calculator; 8 RAG; 9 persistent memory; 10 stories; 11 benchmark; 12 evaluation; 13 vision setup; 14 sampling')
            self.action(number('Utility', 13, 3, 14))
        elif choice.lower() == 's': self.showcase()
        elif choice == '1': self.setup()
        elif choice == '2': self.status()
        elif choice == '3':
            self.llm()
            self.py('labs/chat.py', timeout=0)
        elif choice in ('4', '5', '6', '7'):
            text = prompt({'4': 'Question', '5': 'Text to tokenize', '6': 'Text to extract from', '7': 'Arithmetic question'}[choice])
            self.llm()
            if choice == '4': self.py('labs/chat.py', '--prompt', text, '--max-tokens', '64')
            else: self.py({'5': 'labs/inspect_tokens.py', '6': 'labs/extract.py', '7': 'labs/calculator.py'}[choice], text)
        elif choice == '8': self.rag()
        elif choice == '10':
            self.need_binary('.vendor/llama2.c/run')
            self.model('stories15m')
            self.py('labs/stories.py', '--model', 'stories15m', '--prompt', prompt('Story opening', 'Once upon a time'), '--tokens', '128')
        elif choice == '11':
            self.need_binary('.vendor/llama.cpp/build/bin/llama-bench')
            self.model(self.s.config['model'])
            self.py('scripts/benchmark.py', '--model', self.s.config['model'], '--repetitions', '1',
                    '--output', str(self.s.session / ('benchmark-{}.json'.format(self.s.counter + 1))), timeout=1800)
        elif choice == '12':
            dataset = file_prompt('Evaluation JSONL file', str(ROOT / 'data/evaluation.jsonl'))
            self.llm()
            self.py('labs/evaluate.py', dataset, '--output', str(self.s.session / ('evaluation-{}.jsonl'.format(self.s.counter + 1))), timeout=3600)
        elif choice == '13': self.vision()
        else: raise DemoError('Choose a number or letter shown in the menu.')


COMPACT_MENU = """
JETSON NANO
 1  Prepare selected models
 2  Board and dependency report
 3  Text Conversation
 4  Camera Object Detection
 5  Camera-Guided Object Hunt
 6  Storage Analyzer
 7  Open Presentation
 0  Exit
Ctrl+C cancels and returns here.
"""


class CompactMenu(Menu):
    """Three demos sharing one text model and one detector."""
    def setup_text(self):
        resource_check(start=True)
        runtime = ROOT / '.vendor/llama.cpp/build/bin/llama-server'
        if not os.access(str(runtime), os.X_OK):
            if shutil.disk_usage(str(ROOT)).free < 6 * 1024 ** 3:
                raise DemoError('Text runtime needs building. Free at least 6 GiB first; use --storage. Existing working runtimes need no rebuild.')
            self.s.run(['bash', 'scripts/install_system.sh'], monitor=False, terminal=True)
            self.s.run(['env', 'JOBS=1', 'BUILD_MINIMAL=1', 'bash', 'scripts/build_runtimes.sh'], timeout=14400)
        else:
            print('[READY] Text runtime exists; skipping build.')
        print('[CHECK] Text model checksum (cached files need no download).')
        self.py('scripts/download.py', 'smol360-q4', timeout=7200)
        print('[READY] Text model ready: SmolLM2-360M Q4 (258 MiB).')

    def prepare_vision(self):
        resource_check(start=True)
        executable = vision_python()
        if not executable:
            if shutil.disk_usage(str(ROOT)).free < 6 * 1024 ** 3:
                raise DemoError('Camera libraries need building. Free at least 6 GiB first; text remains available.')
            self.s.run(['env', 'JOBS=1', 'bash', 'scripts/build_vision.sh'], monitor=False, terminal=True)
            executable = vision_python()
        if not executable:
            raise DemoError('Camera bindings unavailable in installed Python interpreters.')
        if any(not shutil.which(name) for name in ('v4l2-ctl', 'gst-launch-1.0')):
            if shutil.disk_usage(str(ROOT)).free < 1024 ** 3:
                raise DemoError('Camera discovery tools need free disk headroom before installation.')
            self.s.run(['bash', 'scripts/install_camera_tools.sh'], monitor=False, terminal=True)
        if not vision_ready('detect'):
            if shutil.disk_usage(str(ROOT)).free < 1024 ** 3:
                raise DemoError('Camera model preparation needs at least 1 GiB free headroom.')
            self.s.run([executable, 'labs/vision.py', 'detect', '--prepare'], timeout=3600)
        else:
            print('[READY] Detector preparation receipt and cached files match; skipping model preparation.')
        print('[READY] Object detector prepared.')

    def setup(self):
        print('Setup checklist: verify existing files, prepare only missing steps.')
        self.setup_text()
        try:
            self.prepare_vision()
            camera = detect_camera()
            print('[READY] Camera: ' + camera if camera else '[PENDING] No responding camera; text is ready.')
        except DemoError as error:
            print('[PENDING] Text ready; camera preparation incomplete:', error)

    def action(self, choice):
        if choice == '1':
            self.setup()
        elif choice == '2':
            self.py('scripts/check_board.py', monitor=False)
            print('Camera Python:', vision_python() or 'missing')
            print('Camera:', detect_camera() or 'not detected')
            print('Use --storage for disk usage and existing model locations.')
        elif choice == '3':
            self.setup_text()
            self.llm('smol360-q4')
            self.py('labs/chat.py', timeout=0)
        elif choice == '4':
            executable = self.ensure_vision('detect')
            source = self.camera_source()
            output = 'display://0' if os.environ.get('DISPLAY') else str(self.s.session / 'detection.mp4')
            self.s.run([executable, 'labs/vision.py', 'detect', source, output, '--frames', '300'], timeout=1800)
        elif choice == '7':
            from open_presentation import open_presentation
            open_presentation()
        elif choice == '6':
            self.py('scripts/storage_report.py', timeout=600, monitor=False)
        elif choice == '5':
            self.setup_text()
            self.camera_projects(mode='hunt')
        else:
            raise DemoError('Choose 0–7 from this menu.')


MENU = '''
LOCAL AI ON JETSON NANO
SETUP
 1  Prepare dependencies, models and sample data
 2  Board health and dependency report
LANGUAGE AND ASSISTANTS
 3  Offline Conversation Assistant
 4  Ask the Local Language Model
 5  Tokenization Microscope
 6  Structured Information Extraction
 7  Calculator Tool Assistant
 8  Class Notes Retrieval and Grounded Answers
 9  Persistent Memory Assistant
10  TinyStories Generator
11  Language Model Performance Benchmark
12  Reproducible Prompt Evaluation
13  Camera Perception Lab and Installation
14  Sampling Playground: Predictability versus Creativity
15  Mission Control: Tool-Planning Assistant
16  Document Detective: Answers with Evidence
17  Story Director: Audience-Controlled Fiction
18  Scene Memory Detective
19  AI Visual Scavenger Hunt
20  Camera Change Journal
21  Run Prepared Student Demonstrations Sequentially
22  Prompt Design Studio
23  Few-Shot Pattern Learner
24  Message Triage Desk: Validated JSON Routing
25  Summary Fact Checker
26  Prompt Injection Defense Lab
27  Answer or Abstain: Hallucination Challenge
28  Context Memory Challenge
29  Socratic Study Partner
30  Mystery Character Interview
 0  Exit
Enter the experiment number. Ctrl+C cancels and returns here.
'''



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ppt', action='store_true', help='Open the bundled presentation')
    parser.add_argument('--all', action='store_true', help='Open the full experiment catalogue')
    parser.add_argument('--storage', action='store_true', help='Read-only disk and directory usage report')
    parser.add_argument('--list', action='store_true', help='List named experiments without starting hardware or models')
    parser.add_argument('--setup-only', action='store_true', help='Prepare core dependencies and exit')
    parser.add_argument('--check', action='store_true', help='Read-only board report, no demos')
    args = parser.parse_args()
    if args.ppt:
        from open_presentation import open_presentation
        open_presentation()
        return
    if args.storage:
        from storage_report import main as storage_main
        storage_main()
        return
    if args.list:
        print(MENU if args.all else COMPACT_MENU)
        return
    if sys.version_info < (3, 6):
        raise SystemExit('Python 3.6 or newer is required; keep JetPack system Python.')
    os.chdir(str(ROOT))
    subprocess.run([sys.executable, 'scripts/check_board.py'] + ([] if args.check else ['--strict']), check=True)
    if args.check:
        print('Available RAM (MiB):', available_memory(), 'Temperature (C):', temperature())
        print('Core missing/corrupt:', ', '.join(core_missing(verify=True, compact=not args.all)) or 'none')
        print('Camera Python:', vision_python() or 'not installed')
        print('Camera:', detect_camera() or 'none responding')
        for mode in (VISION_MODES if args.all else ('detect',)):
            print('Camera {}: {}'.format(mode, 'prepared' if vision_ready(mode) else 'needs preparation'))
        return
    if not args.setup_only and not sys.stdin.isatty():
        raise SystemExit('The menu needs an interactive terminal. Use --setup-only for preparation.')
    # Linux flock is released even after a crash; stale lock files are harmless.
    (ROOT / 'runs').mkdir(exist_ok=True)
    with (ROOT / 'runs/demo.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('Another demo menu is running. Exit that menu first.')
        supervisor = Supervisor()
        menu = Menu(supervisor) if args.all else CompactMenu(supervisor)
        signal.signal(signal.SIGTERM, lambda *args: sys.exit(143))
        print('Session logs:', supervisor.session)
        try:
            if args.setup_only:
                menu.setup()
                return
            while True:
                try:
                    print(MENU if args.all else COMPACT_MENU)
                    choice = input('Select demo: ').strip()
                    if choice == '0':
                        break
                    menu.action(choice)
                except KeyboardInterrupt:
                    print('\nCancelled. Returning to menu.')
                except EOFError:
                    break
                except (DemoError, OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                    print('\nDemo stopped: {}\nFix the issue and select again; the menu remains open.'.format(error))
                finally:
                    supervisor.stop_server()
        finally:
            supervisor.stop_server()


if __name__ == '__main__':
    try:
        main()
    except (DemoError, OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print('Cannot start: {}'.format(error), file=sys.stderr)
        sys.exit(1)
