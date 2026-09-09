#!/usr/bin/env python3
"""Whisper CPU transcription and a push-to-talk assistant with eSpeak NG output."""
import argparse
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from common import CONFIG, ROOT, ask


def require(command):
    if shutil.which(command) is None:
        raise SystemExit('Required executable not found: ' + command)


def transcribe(audio, model_path=None):
    require('ffmpeg')
    manifest = json.loads((ROOT / 'models.json').read_text())
    model = model_path or ROOT / 'models' / manifest[CONFIG['whisper_model']]['file']
    binary = ROOT / '.vendor/whisper.cpp/build/bin/main'
    if not audio.is_file() or not model.is_file() or not binary.is_file():
        raise FileNotFoundError('Require an audio file, downloaded Whisper model, and built whisper.cpp main')
    with tempfile.TemporaryDirectory(prefix='nano-audio-') as tmp:
        wav = Path(tmp) / 'audio.wav'
        prefix = Path(tmp) / 'transcript'
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', str(audio),
                        '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', str(wav)], check=True)
        subprocess.run([str(binary), '-m', str(model), '-f', str(wav), '-t', str(CONFIG['threads']),
                        '-l', 'en', '-ng', '-otxt', '-of', str(prefix)], check=True)
        return prefix.with_suffix('.txt').read_text(encoding='utf-8').strip()


def speak(text):
    require('espeak-ng')
    # stdin avoids interpreting model-generated text as command-line switches.
    subprocess.run(['espeak-ng', '-v', CONFIG['tts_voice'], '-s', str(CONFIG['tts_words_per_minute']), '--stdin'],
                   input=text, universal_newlines=True, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command')
    stt = sub.add_parser('transcribe')
    stt.add_argument('audio', type=Path)
    stt.add_argument('--output', type=Path)
    tts = sub.add_parser('say')
    tts.add_argument('text')
    voice = sub.add_parser('assistant')
    voice.add_argument('--device', default=CONFIG['audio_device'], help='ALSA capture device from arecord -L')
    voice.add_argument('--seconds', type=int, default=CONFIG['record_seconds'])
    args = parser.parse_args()
    if args.command == 'transcribe':
        result = transcribe(args.audio)
        print(result)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(result + '\n', encoding='utf-8')
    elif args.command == 'say':
        speak(args.text)
    elif args.command == 'assistant':
        require('arecord')
        require('espeak-ng')
        if not 1 <= args.seconds <= 30:
            raise ValueError('Choose a recording length between 1 and 30 seconds')
        while input('Enter to record, q to quit: ').lower() != 'q':
            with tempfile.TemporaryDirectory(prefix='nano-mic-') as tmp:
                wav = Path(tmp) / 'microphone.wav'
                subprocess.run(['arecord', '-q', '-D', args.device, '-f', 'S16_LE', '-r', '16000',
                                '-c', '1', '-d', str(args.seconds), str(wav)], check=True)
                start = time.monotonic()
                question = transcribe(wav)
                stt_time = time.monotonic() - start
            print('Heard:', question)
            if not question:
                continue
            start = time.monotonic()
            answer = ask(question, system='Answer in one short sentence.', max_tokens=64)['content'].strip()
            llm_time = time.monotonic() - start
            print('Nano:', answer)
            start = time.monotonic()
            speak(answer)
            print('Seconds: STT={:.2f}, LLM={:.2f}, speech playback={:.2f}'.format(stt_time, llm_time, time.monotonic() - start))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
