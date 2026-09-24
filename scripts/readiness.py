"""Dependency and camera checks without importing native bindings into the menu."""
import glob
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from download import sha256

ROOT = Path(__file__).resolve().parents[1]
RUNTIMES = ['.vendor/llama.cpp/build/bin/llama-server',
            '.vendor/llama.cpp/build/bin/llama-bench', '.vendor/llama2.c/run']
VISION_MODES = ('detect', 'classify', 'pose', 'segment')


def vision_python():
    # JetPack's native extension ABI may differ from the menu's newer Python.
    for executable in dict.fromkeys([sys.executable, '/usr/bin/python3']):
        try:
            result = subprocess.run([executable, '-c', 'import jetson_inference, jetson_utils'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
            if result.returncode == 0:
                return executable
        except (OSError, subprocess.TimeoutExpired):
            pass
    return None


def core_missing(root=ROOT, verify=False, compact=False):
    config = json.loads((root / 'config.json').read_text())
    manifest = json.loads((root / 'models.json').read_text())
    missing = [p for p in (RUNTIMES[:1] if compact else RUNTIMES) if not os.access(str(root / p), os.X_OK)]
    for key in (['smol360-q4'] if compact else set([config['model'], 'smol360-q4', 'stories15m'])):
        item = manifest[key]
        path = root / 'models' / item['file']
        if not path.is_file() or path.stat().st_size != item['bytes']:
            missing.append('model: ' + key)
        elif verify and sha256(path) != item['sha256']:
            missing.append('checksum: ' + key)
    for name in (() if compact else ('ffmpeg', 'gst-launch-1.0', 'v4l2-ctl')):
        if not shutil.which(name):
            missing.append('command: ' + name)
    return sorted(missing)


def camera_candidates():
    candidates = []
    for device in sorted(glob.glob('/dev/video*')):
        try:
            result = subprocess.run(['v4l2-ctl', '-d', device, '--all'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    universal_newlines=True, timeout=5)
            if result.returncode == 0 and 'Video Capture' in result.stdout:
                # CSI sensors use Argus rather than the USB V4L2 capture pipeline.
                if any(x in result.stdout.lower() for x in ('tegra', 'vi-output')):
                    if 'csi://0' not in candidates:
                        candidates.append('csi://0')
                else:
                    candidates.append('v4l2://' + device)
        except (OSError, subprocess.TimeoutExpired):
            continue
    return candidates


def probe_camera(uri):
    if uri.startswith('v4l2://'):
        pipeline = ['v4l2src', 'device=' + uri[len('v4l2://'):], 'num-buffers=1']
    elif uri.startswith('csi://') and uri[6:].isdigit():
        pipeline = ['nvarguscamerasrc', 'sensor-id=' + uri[6:], 'num-buffers=1']
    else:
        return False
    try:
        result = subprocess.run(['gst-launch-1.0', '-q'] + pipeline + ['!', 'fakesink'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def detect_camera():
    for uri in camera_candidates():
        if probe_camera(uri):
            return uri
    return None


def vision_ready(mode, root=ROOT):
    receipt = root / 'runs' / ('vision-ready-' + mode + '.json')
    try:
        entries = json.loads(receipt.read_text())
        return bool(entries) and all(Path(p).is_file() and Path(p).stat().st_size == size
                                     for p, size in entries.items())
    except (OSError, ValueError, TypeError, AttributeError):
        return False
