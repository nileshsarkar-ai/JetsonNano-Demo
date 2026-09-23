"""Python 3.6 process supervision for the interactive Nano demonstrations."""
import json
import http.client
import os
from pathlib import Path
import signal
import socket
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MIB = 1024 * 1024


class DemoError(Exception):
    pass


def available_memory():
    """Linux MemAvailable includes reclaimable cache; do not use MemFree."""
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemAvailable:'):
                return int(line.split()[1]) / 1024.0
    except (OSError, ValueError):
        pass
    return None


def temperature():
    values = []
    for path in Path('/sys/class/thermal').glob('thermal_zone*/temp'):
        try:
            value = float(path.read_text()) / 1000.0
            if 0 < value < 150:
                values.append(value)
        except (OSError, ValueError):
            pass
    return max(values) if values else None


def resource_check(start=False):
    if shutil.disk_usage(str(ROOT)).free < 256 * MIB:
        raise DemoError('Less than 256 MiB disk space remains. Free space before continuing.')
    memory = available_memory()
    if memory is None:
        raise DemoError('Cannot read MemAvailable. Resource protection is unavailable.')
    minimum = 768 if start else 256
    if memory < minimum:
        raise DemoError('Only {:.0f} MiB RAM available (minimum {} MiB). '
                        'Close other programs before retrying.'.format(memory, minimum))
    heat = temperature()
    if heat is not None and heat >= 85:
        raise DemoError('Board temperature is {:.1f} C. Let it cool; check the fan.'.format(heat))


def stop_process(process):
    """Terminate only a process group created by this launcher, with bounded wait."""
    if process is None:
        return
    # Even when the leader has exited, its children may still hold the group.
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=3)


class Supervisor:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        runs = self.root / 'runs'
        runs.mkdir(exist_ok=True)
        self.session = Path(tempfile.mkdtemp(prefix='demo-', dir=str(runs)))
        self.server = None
        self.server_stream = None
        self.counter = 0
        self.config = json.loads((self.root / 'config.json').read_text())
        if not isinstance(self.config, dict) or not isinstance(self.config.get('server_url'), str):
            raise DemoError('config.json needs an object with a server_url string.')
        for key, default, maximum in [('context', 1024, 1024), ('batch', 64, 64), ('threads', 4, 4)]:
            value = self.config.get(key, default)
            if type(value) is not int or not 1 <= value <= maximum:
                raise DemoError('For this demo menu, config {} must be from 1 to {}.'.format(key, maximum))
        endpoint = urlparse(self.config['server_url'])
        if (endpoint.scheme != 'http' or endpoint.hostname != '127.0.0.1'
                or endpoint.path not in ('', '/') or endpoint.query or endpoint.fragment
                or endpoint.username or endpoint.password):
            raise DemoError('config.json must use http://127.0.0.1:PORT')
        self.port = endpoint.port or 80
        self.base_url = 'http://127.0.0.1:{}'.format(self.port)
        # Avoid proxy configuration redirecting localhost health checks.
        self.http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        (self.session / 'config.json').write_text(json.dumps(self.config, indent=2))

    def event(self, **record):
        record['time'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
        with (self.session / 'events.jsonl').open('a') as stream:
            stream.write(json.dumps(record) + '\n')

    def run(self, command, timeout=900, monitor=True, terminal=False):
        if terminal:
            # Installers need the controlling TTY for sudo. Do not detach them or
            # record password prompts, and do not interrupt apt on a RAM threshold.
            print('Installer uses your terminal directly; enter sudo password if asked.')
            self.event(event='installer-start', command=[str(x) for x in command])
            try:
                result = subprocess.run(command, cwd=str(self.root), check=True)
                self.event(event='installer-finish', status=result.returncode)
            except BaseException as error:
                self.event(event='installer-finish', reason=str(error) or type(error).__name__)
                raise
            return
        if monitor:
            resource_check(start=True)
        self.counter += 1
        log = self.session / '{:03d}.log'.format(self.counter)
        print('\nRunning: {}\nLog: {}'.format(' '.join(str(x) for x in command), log), flush=True)
        process = None
        started = time.monotonic()
        result = None
        reason = None
        self.event(event='start', command=[str(x) for x in command], log=str(log))
        try:
            with log.open('wb') as stream:
                process = subprocess.Popen([str(x) for x in command], cwd=str(self.root),
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                           start_new_session=True, env=dict(os.environ, PYTHONUNBUFFERED='1'))
                # Forward prompts even without newlines. Bound disk log size to 20 MiB.
                def forward():
                    written = 0
                    try:
                        while True:
                            block = os.read(process.stdout.fileno(), 4096)
                            if not block:
                                break
                            if written < 20 * MIB:
                                stream.write(block[:20 * MIB - written])
                                stream.flush()
                                written += len(block)
                            try:
                                sys.stdout.buffer.write(block)
                                sys.stdout.buffer.flush()
                            except (BrokenPipeError, AttributeError):
                                pass
                    except (OSError, ValueError):
                        pass
                thread = threading.Thread(target=forward)
                thread.daemon = True
                thread.start()
                try:
                    while process.poll() is None:
                        if monitor:
                            resource_check()
                        if self.server is not None and self.server.poll() is not None:
                            raise DemoError('Model server stopped unexpectedly. See server.log; retry the demo.')
                        if timeout and time.monotonic() - started > timeout:
                            raise DemoError('Time limit reached; the demo was stopped.')
                        time.sleep(0.25)
                    result = process.returncode
                    if result:
                        raise DemoError('Command exited with status {}. Details: {}'.format(result, log))
                finally:
                    stop_process(process)
                    thread.join(timeout=3)
                    process.stdout.close()
        except BaseException as error:
            reason = str(error) or type(error).__name__
            raise
        finally:
            self.event(event='finish', status=result, reason=reason, log=str(log))

    def require_free_port(self):
        with socket.socket() as sock:
            sock.settimeout(1)
            if sock.connect_ex(('127.0.0.1', self.port)) == 0:
                raise DemoError('Port {} is occupied. Stop your other server first; it will not be killed.'.format(self.port))

    def start_server(self):
        resource_check(start=True)
        self.require_free_port()
        self.server_stream = (self.session / 'server.log').open('ab')
        try:
            self.server = subprocess.Popen([sys.executable, 'scripts/serve.py'], cwd=str(self.root),
                                           stdout=self.server_stream, stderr=subprocess.STDOUT,
                                           start_new_session=True)
            deadline = time.monotonic() + 600
            print('Loading model (up to 10 minutes). Ctrl+C cancels.', flush=True)
            while time.monotonic() < deadline:
                resource_check()
                if self.server.poll() is not None:
                    raise DemoError('Server failed to start. Inspect {}'.format(self.session / 'server.log'))
                try:
                    with self.http.open(self.base_url + '/health', timeout=2) as response:
                        if response.status == 200:
                            return
                except (urllib.error.URLError, OSError, http.client.HTTPException):
                    pass
                time.sleep(1)
            raise DemoError('Server startup timed out. Inspect server.log.')
        except BaseException:
            self.stop_server()
            raise

    def stop_server(self):
        try:
            stop_process(self.server)
        finally:
            self.server = None
            if self.server_stream:
                self.server_stream.close()
                self.server_stream = None
