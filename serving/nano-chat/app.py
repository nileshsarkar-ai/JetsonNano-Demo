"""Authenticated browser demo; inference uses a server-side hosted API."""
import base64
import hmac
import hashlib
from http.cookies import SimpleCookie
from urllib.parse import parse_qs
import json
import os
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CONFIG = json.loads(Path(os.environ.get('DEMO_CONFIG', '/home/nano-demo/access.json')).read_text())
SESSION = hmac.new(CONFIG['password'].encode(), b'nano-demo-session', hashlib.sha256).hexdigest()
LOGIN = b'''<!doctype html><meta name=viewport content="width=device-width,initial-scale=1"><title>Jetson Nano Demo</title><body style="background:#f4f7f2;font:18px system-ui;padding:10vh 10vw;color:#18241a"><h1>Jetson Nano Demo</h1><form method=post action=/login><label>Demo password <input name=password type=password required autofocus style="padding:12px;border-radius:8px"></label><button style="padding:12px;background:#76b900;border:0;border-radius:8px">Open demo</button></form></body>'''
PAGE = Path(__file__).with_name('index.html').read_bytes()
SLOTS = threading.BoundedSemaphore(3)

class Handler(BaseHTTPRequestHandler):
    def authenticated(self):
        expected = 'Basic ' + base64.b64encode(('demo:' + CONFIG['password']).encode()).decode()
        cookies = SimpleCookie()
        try: cookies.load(self.headers.get('Cookie', ''))
        except Exception: pass
        token = cookies.get('demo_session')
        return hmac.compare_digest(self.headers.get('Authorization', ''), expected) or (token is not None and hmac.compare_digest(token.value, SESSION))

    def reply(self, status, body, kind='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def gate(self):
        if self.authenticated(): return True
        self.reply(401, b'{"error":"Please refresh and sign in again."}')
        return False

    def do_GET(self):
        if not self.authenticated(): return self.reply(200, LOGIN, 'text/html; charset=utf-8')
        if self.path != '/': return self.reply(404, b'{}')
        self.reply(200, PAGE, 'text/html; charset=utf-8')

    def do_POST(self):
        if self.path == '/login':
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 1024: raise ValueError()
                password = parse_qs(self.rfile.read(size).decode()).get('password', [''])[0]
                if not hmac.compare_digest(password, CONFIG['password']):
                    return self.reply(403, LOGIN + b'<p>Incorrect password. Please try again.</p>', 'text/html; charset=utf-8')
                self.send_response(303)
                self.send_header('Set-Cookie', 'demo_session=' + SESSION + '; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=43200')
                self.send_header('Location', '/')
                self.end_headers()
            except (ValueError, UnicodeError): self.reply(400, b'{}')
            return
        if not self.gate(): return
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
