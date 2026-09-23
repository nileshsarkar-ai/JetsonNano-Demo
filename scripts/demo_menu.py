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
from demo_runtime import DemoError, ROOT, Supervisor, available_memory, resource_check, temperature


def prompt(label, default=None):
    value = input(label + (' [{}]'.format(default) if default is not None else '') + ': ').strip()
    value = value or default
    if not value:
        raise DemoError('No value entered. Returning to menu.')
    return value


def file_prompt(label):
    path = Path(prompt(label)).expanduser().resolve()
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
        for field in ('model', 'whisper_model'):
            if self.s.config.get(field) not in self.manifest:
                raise DemoError('config.json {} must name a model in models.json.'.format(field))
        required = ('audio_device', 'tts_voice', 'tts_words_per_minute', 'record_seconds',
                    'max_tokens', 'temperature', 'top_p', 'top_k', 'seed', 'timeout_seconds',
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
            raise DemoError('Setup requires at least 6 GiB free disk headroom. Free space and retry.')
        jobs = os.environ.get('JOBS', '1')
        if jobs not in ('1', '2'):
            raise DemoError('Use JOBS=1 (recommended) or JOBS=2 on this board.')
        print('Preparation needs Internet and sudo. It can take a long time; do this before the event.')
        self.s.run(['bash', 'scripts/install_system.sh'], monitor=False, terminal=True)
        self.s.run(['env', 'JOBS=' + jobs, 'bash', 'scripts/build_runtimes.sh'], timeout=14400)
        self.py('scripts/download.py', self.s.config['model'], self.s.config['whisper_model'],
                'stories15m', 'smol360-q4', timeout=7200)
        print('Core preparation completed. Select 2, then S > tour. Optional camera setup is under U > 13 > install.')

    def status(self):
        self.py('scripts/check_board.py', '--strict', monitor=False)
        print('Available RAM: {} MiB; highest reported temperature: {} C'.format(available_memory(), temperature()))
        print('Free disk: {:.1f} GiB'.format(shutil.disk_usage(str(ROOT)).free / 1024 ** 3))
        for key in (self.s.config['model'], 'smol360-q4', self.s.config['whisper_model'], 'stories15m'):
            path = ROOT / 'models' / self.manifest[key]['file']
            print('{}: {}'.format(key, 'present (hash checked before use)' if path.is_file() else 'MISSING'))
        for relative in ('.vendor/llama.cpp/build/bin/llama-server', '.vendor/llama.cpp/build/bin/llama-bench',
                         '.vendor/llama2.c/run', '.vendor/whisper.cpp/build/bin/main'):
            print('{}: {}'.format(relative, 'ready' if os.access(str(ROOT / relative), os.X_OK) else 'MISSING'))
        for name in ('ffmpeg', 'arecord', 'espeak-ng'):
            print('{}: {}'.format(name, shutil.which(name) or 'MISSING'))
        for module in ('jetson_inference', 'jetson_utils', 'torch'):
            print('{}: {}'.format(module, 'installed (not hardware-validated)' if importlib.util.find_spec(module) else 'optional / missing'))
        print('Logs:', self.s.session)
        print('Power, camera, microphone, thermals and model quality still need an on-board rehearsal.')

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
                raise DemoError('Index your notes first using RAG > index.')
            question = prompt('Question')
            if mode == 'ask':
                self.llm()
            args = [] if mode == 'ask' else ['--retrieve-only']
            self.py('labs/rag.py', 'ask', question, *args)
        else:
            raise DemoError('Unknown RAG mode.')

    def speech(self):
        mode = prompt('Speech: say / transcribe / assistant', 'say')
        if mode == 'say':
            if not shutil.which('espeak-ng'):
                raise DemoError('eSpeak NG missing. Run core setup.')
            self.py('labs/speech.py', 'say', prompt('Text', 'Hello from the Jetson Nano.'))
        elif mode in ('transcribe', 'assistant'):
            self.need_binary('.vendor/whisper.cpp/build/bin/main')
            self.model(self.s.config['whisper_model'])
            if not shutil.which('ffmpeg'):
                raise DemoError('ffmpeg missing. Run core setup.')
            if mode == 'transcribe':
                audio = file_prompt('Audio file')
                self.py('labs/speech.py', 'transcribe', audio)
            else:
                if not shutil.which('arecord'):
                    raise DemoError('arecord missing. Run core setup.')
                self.s.run(['arecord', '-L'], monitor=False)
                device = prompt('ALSA capture device', self.s.config['audio_device'])
                self.llm()
                self.py('labs/speech.py', 'assistant', '--device', device, '--seconds', '5', timeout=0)
        else:
            raise DemoError('Unknown speech mode.')

    def vision(self):
        mode = prompt('Vision: install / detect / classify / pose / segment', 'detect')
        if mode == 'install':
            print('Optional TensorRT setup needs Internet, sudo, and substantial build time.')
            resource_check(start=True)
            if shutil.disk_usage(str(ROOT)).free < 6 * 1024 ** 3:
                raise DemoError('Vision setup needs at least 6 GiB free disk headroom.')
            self.s.run(['env', 'JOBS=1', 'bash', 'scripts/build_vision.sh'], monitor=False, terminal=True)
            return
        if mode not in ('detect', 'classify', 'pose', 'segment'):
            raise DemoError('Unknown vision mode.')
        if any(importlib.util.find_spec(x) is None for x in ('jetson_inference', 'jetson_utils')):
            raise DemoError('Install optional vision bindings first: Vision > install.')
        source = prompt('Camera URI or video path', 'v4l2:///dev/video0')
        if source.startswith('v4l2://') and not Path(source[len('v4l2://'):]).exists():
            raise DemoError('Camera device does not exist. Check connection and camera URI.')
        output = prompt('Output URI (use a file path on headless boards)', 'display://0' if os.environ.get('DISPLAY') else str(self.s.session / ('vision-{}.mp4'.format(self.s.counter + 1))))
        frames = number('Maximum frames', 300, 1, 3000)
        args = ['--frames', frames]
        if mode == 'detect' and prompt('Speak detected labels? y/n', 'n') == 'y':
            args.append('--speak')
        print('First model load may download weights and compile a TensorRT engine. Rehearse beforehand.')
        self.py('labs/vision.py', mode, source, output, *args, timeout=1800)

    def training(self):
        if importlib.util.find_spec('torch') is None:
            raise DemoError('Optional matching JetPack PyTorch wheel required. See docs/TRAINING.md; do not pip-upgrade Python.')
        mode = prompt('Tiny LoRA: base / adapt / generate', 'generate')
        args = []
        if mode not in ('base', 'adapt', 'generate'):
            raise DemoError('Unknown training mode.')
        if mode != 'base':
            print('Load only a trusted checkpoint you created.')
            args += ['--checkpoint', file_prompt('Checkpoint')]
        if mode == 'generate':
            args += ['--prompt', prompt('Prompt (characters must exist in the base vocabulary)'), '--tokens', '64']
        else:
            args += ['--text', file_prompt('UTF-8 corpus'), '--steps', number('Steps', 50, 1, 500),
                     '--batch-size', '1', '--output', str(self.s.session / ('tiny-{}.pt'.format(self.s.counter + 1)))]
        self.py('training/tiny_lora.py', mode, '--device', 'cpu', *args, timeout=1800)

    def capture_snapshot(self, source):
        if any(importlib.util.find_spec(x) is None for x in ('jetson_inference', 'jetson_utils')):
            raise DemoError('Vision unavailable. Prepare it using Utilities > 13 > install; text projects still work.')
        if source.startswith('v4l2://') and not Path(source[len('v4l2://'):]).exists():
            raise DemoError('Camera device unavailable; skipping camera project.')
        # Every call finishes and releases TensorRT before the next LLM load.
        output = 'display://0' if os.environ.get('DISPLAY') else str(self.s.session / ('sample-{}.mp4'.format(self.s.counter + 1)))
        self.py('labs/vision.py', 'detect', source, output, '--frames', '5', '--interval', '0.4', timeout=120)
        snapshot = summarize_frames(records_from_log(self.s.session / '{:03d}.log'.format(self.s.counter)))
        path = self.s.session / ('snapshot-{}.json'.format(self.s.counter))
        path.write_text(json.dumps(snapshot, indent=2))
        print('Stable multi-frame observation:', json.dumps(snapshot['objects']), flush=True)
        return snapshot

    def camera_projects(self, automatic=False):
        print('\nCAMERA PROJECTS: memory / hunt / journal')
        print('memory: compare before/after; hunt: AI-planned visual challenge; journal: a three-observation scene history.')
        print('Keep the camera fixed. Prepare a cup, bottle, book or phone; no face identification is used.')
        mode = 'journal' if automatic else prompt('Camera project', 'memory').lower()
        if mode not in ('memory', 'hunt', 'journal'):
            raise DemoError('Choose memory, hunt or journal.')
        source = 'v4l2:///dev/video0' if automatic else prompt('Camera URI', 'v4l2:///dev/video0')
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
            print('No stable changes observed. History saved; no invented explanation or unnecessary LLM load.')
            return
        self.llm('smol360-q4')
        self.py('labs/camera_tasks.py', 'explain', str(path))

    def showcase(self):
        print('\nSHOWCASE PROJECTS — small local LLM, no cloud calls after preparation\n tour       Automatic tour: multi-tool agent -> document detective -> story director (+ optional camera)\n agent      Mission control: an LLM plans tools, executes them, and combines evidence\n detective  Ask the bundled fictional exhibit brief, with visible evidence\n story      Interactive story director: choose a scene and add a twist\n camera     Scene-memory detective, AI scavenger hunt, workspace change journal\n')
        project = prompt('Choose project', 'tour').lower()
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
            if (Path('/dev/video0').exists() and
                    all(importlib.util.find_spec(x) is not None for x in ('jetson_inference', 'jetson_utils'))):
                try:
                    self.camera_projects(automatic=True)
                except (DemoError, OSError, ValueError) as error:
                    print('Optional camera skipped: {}'.format(error))
                finally:
                    self.s.stop_server()
            else:
                print('Optional camera skipped: no prepared /dev/video0 camera and vision bindings.')
            print('Tour complete. Text outputs came from the local model; skipped stages were reported.')
        else:
            args = []
            if project in ('agent', 'detective'):
                question = prompt('Your request', 'Read the exhibit brief and current board memory, then give a guide briefing.' if project == 'agent' else 'What does the Ocean Watch exhibit measure?')
                args = ['--question', question]
            self.py('labs/projects.py', project, *args, timeout=0 if project == 'story' else 900)

    def action(self, choice):
        if choice.lower() in ('s', 'c', 't', 'u') or choice in [str(x) for x in range(3, 15)]:
            self.s.require_free_port()
        if choice.lower() == 'c': self.camera_projects()
        elif choice.lower() == 'u':
            print('3 chat; 4 question; 5 tokens; 6 extraction; 7 calculator; 8 RAG; 9 speech; 10 stories; 11 benchmark; 12 evaluation; 13 vision setup; 14 tiny LoRA')
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
        elif choice == '9': self.speech()
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
            dataset = file_prompt('Evaluation JSONL file')
            self.llm()
            self.py('labs/evaluate.py', dataset, '--output', str(self.s.session / ('evaluation-{}.jsonl'.format(self.s.counter + 1))), timeout=3600)
        elif choice == '13': self.vision()
        elif choice == '14': self.training()
        else: raise DemoError('Choose a number or letter shown in the menu.')


MENU = '''
JETSON NANO — OFFLINE AI PROJECTS
 1  Prepare models and core dependencies (before the event)
 2  Board / dependency / resource report
 S  Offline AI projects + automatic tour
 C  Camera projects: scene memory, visual quests, change journal
 U  Developer utilities / optional vision and PyTorch labs
 0  Exit
Ctrl+C cancels a project and returns here. Projects run sequentially.
Use S -> tour for the prepared automatic sequence; camera is optional.
'''



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--setup-only', action='store_true', help='Prepare core dependencies and exit')
    parser.add_argument('--check', action='store_true', help='Read-only board report, no demos')
    args = parser.parse_args()
    if sys.version_info < (3, 6):
        raise SystemExit('Python 3.6 or newer is required; keep JetPack system Python.')
    os.chdir(str(ROOT))
    subprocess.run([sys.executable, 'scripts/check_board.py', '--strict'], check=True)
    if args.check:
        print('Available RAM (MiB):', available_memory(), 'Temperature (C):', temperature())
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
        menu = Menu(supervisor)
        signal.signal(signal.SIGTERM, lambda *args: sys.exit(143))
        print('Session logs:', supervisor.session)
        try:
            if args.setup_only:
                menu.setup()
                return
            while True:
                try:
                    print(MENU)
                    choice = input('Select demo: ').strip()
                    if choice == '0':
                        break
                    menu.action(choice)
                except KeyboardInterrupt:
                    print('\nCancelled. Returning to menu.')
                except EOFError:
                    break
                except (DemoError, OSError, ValueError, subprocess.SubprocessError) as error:
                    print('\nDemo stopped: {}\nFix the issue and select again; the menu remains open.'.format(error))
                finally:
                    supervisor.stop_server()
        finally:
            supervisor.stop_server()


if __name__ == '__main__':
    try:
        main()
    except (DemoError, OSError, ValueError, subprocess.SubprocessError) as error:
        print('Cannot start: {}'.format(error), file=sys.stderr)
        sys.exit(1)
