#!/usr/bin/env python3
"""Read-only platform report. Does not claim runtime or model validation."""
import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def read(path):
    p = Path(path)
    return p.read_text().replace('\x00', '').strip() if p.exists() else None


def command_output(command):
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                universal_newlines=True, timeout=10)
        return {'status': result.returncode, 'output': result.stdout.strip()[:4000]}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'unavailable': str(error)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--strict', action='store_true', help='Require original Nano and L4T R32')
    args = parser.parse_args()
    model = read('/proc/device-tree/model') or ''
    release = read('/etc/nv_tegra_release') or ''
    mem = read('/proc/meminfo') or ''
    report = {'model': model, 'architecture': platform.machine(),
              'os': read('/etc/os-release'), 'l4t': release,
              'python': platform.python_version(), 'python_executable': sys.executable,
              'python_commands': {name: {'path': shutil.which(name), 'version': command_output([name, '--version'])}
                                  for name in ('python', 'python3', 'python3.11')},
              'power_mode': command_output(['nvpmodel', '-q']),
              'swap': command_output(['swapon', '--show']),
              'jetpack_packages': command_output(['dpkg-query', '-W', 'nvidia-l4t-core', 'libnvinfer*', 'cuda-cudart*']),
              'disk_free_gib': round(shutil.disk_usage(str(Path(__file__).resolve().parents[1])).free / 1024 ** 3, 2),
              'memory': [x for x in mem.splitlines() if x.startswith(('MemTotal:', 'MemAvailable:', 'SwapTotal:'))],
              'executables': {x: shutil.which(x) for x in ['gcc-8', 'g++-8', 'cmake', 'git', 'ffmpeg', 'arecord', 'espeak-ng', 'tegrastats']}}
    if Path('/usr/local/cuda/bin/nvcc').exists():
        report['cuda'] = command_output(['/usr/local/cuda/bin/nvcc', '--version'])
    print(json.dumps(report, indent=2))
    if args.strict and not ('jetson nano' in model.lower() and 'orin' not in model.lower()
                            and platform.machine() == 'aarch64' and release.startswith('# R32')):
        raise SystemExit('Expected original Jetson Nano on JetPack 4 / L4T R32. No changes made.')


if __name__ == '__main__':
    main()
