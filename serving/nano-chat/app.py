"""Public browser demo; inference uses a server-side hosted API."""
import json
import os
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CONFIG = json.loads(Path(os.environ.get('DEMO_CONFIG', '/home/nano-demo/access.json')).read_text())
PAGE = Path(__file__).with_name('index.html').read_bytes()
SLOTS = threading.BoundedSemaphore(3)

class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body, kind='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != '/': return self.reply(404, b'{}')
        self.reply(200, PAGE, 'text/html; charset=utf-8')

    def do_POST(self):
        if self.path != '/chat': return self.reply(404, b'{}')
        origin = self.headers.get('Origin')
        if origin and origin != 'https://' + self.headers.get('Host', ''):
            return self.reply(403, b'{}')
        if not SLOTS.acquire(blocking=False):
            return self.reply(429, b'{"error":"Busy; please try again shortly."}')
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 40000: raise ValueError()
            supplied = json.loads(self.rfile.read(size))['messages']
            if not isinstance(supplied, list): raise ValueError()
            messages = [{'role':'system','content':'You are a helpful assistant for an engaging student AI demonstration. Be concise, clear and accurate. Never claim to run on local hardware; this is a hosted demonstration. You cannot see a camera or control hardware.'}]
            for msg in supplied[-12:]:
                if msg.get('role') not in ('user','assistant') or not isinstance(msg.get('content'),str): raise ValueError()
                messages.append({'role':msg['role'],'content':msg['content'][:6000]})
            payload = {'model':'glm-5.3-flash','messages':messages,'max_tokens':4096,'reasoning_effort':'low','stream':False}
            req = urllib.request.Request('https://models.jarvislabs.net/v1/chat/completions', data=json.dumps(payload).encode(), headers={'Authorization':'Bearer '+CONFIG['api_key'],'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.load(response)
            answer = result['choices'][0]['message'].get('content')
            if not answer: raise RuntimeError('Empty answer')
            self.reply(200, json.dumps({'answer':answer}).encode())
        except (ValueError, KeyError, TypeError):
            self.reply(400, b'{"error":"Please enter a shorter message and try again."}')
        except Exception as error:
            print('Chat failed:', type(error).__name__, flush=True)
            self.reply(502, b'{"error":"The response could not finish. Please try again."}')
        finally:
            SLOTS.release()

if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', int(os.environ.get('PORT','6006'))), Handler).serve_forever()
