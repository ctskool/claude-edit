"""Single-range media responses and ordered, compare-and-swap JSON saves."""
import json
import mimetypes
import re
import threading
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from tools.plan_page.common import atomic_json, read


class Conflict(ValueError):
    pass


class JsonStore:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.RLock()

    def save(self, expected, value):
        with self.lock:
            current = read(self.path) if self.path.exists() else {}
            revision = current.get('revision', 0)
            if type(expected) is not int or expected != revision:
                raise Conflict(f'revision conflict; current acknowledged revision is {revision}; reload before saving')
            value = {**value, 'revision': revision + 1}
            atomic_json(self.path, value)
            return value


class RangeHandler(SimpleHTTPRequestHandler):
    def json(self, value, status=200):
        body = json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def send_file(self, path, kind=None):
        path = Path(path)
        if not path.is_file():
            return self.send_error(404)
        size = path.stat().st_size
        start, end, status = 0, size - 1, 200
        value = self.headers.get('Range')
        if value:
            match = re.fullmatch(r'bytes=(\d*)-(\d*)', value)
            if not match or not any(match.groups()):
                return self.bad_range(size)
            a, b = match.groups()
            if a:
                start, end = int(a), min(int(b), size - 1) if b else size - 1
            else:
                start = max(0, size - int(b))
            if start > end or start >= size:
                return self.bad_range(size)
            status = 206
        self.send_response(status)
        self.send_header('Content-Type', kind or mimetypes.guess_type(str(path))[0] or 'application/octet-stream')
        self.send_header('Accept-Ranges', 'bytes')
        if status == 206:
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length', str(max(0, end - start + 1)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        if self.command == 'HEAD':
            return
        try:
            with path.open('rb') as f:
                f.seek(start)
                left = end - start + 1
                while left > 0:
                    chunk = f.read(min(left, 256 * 1024))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # browsers cancel a media request when seeking

    def bad_range(self, size):
        self.send_response(416)
        self.send_header('Content-Range', f'bytes */{size}')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    def send_head(self):
        # SimpleHTTPRequestHandler's normal static route also gets Range support.
        path = self.translate_path(self.path)
        if Path(path).is_file():
            self.send_file(path)
            return None
        return super().send_head()

    def body_json(self):
        # No cross-origin writes and no unbounded local request bodies.
        origin = self.headers.get('Origin')
        if origin and origin != 'http://' + self.headers.get('Host', ''):
            raise ValueError('cross-origin save refused')
        length = int(self.headers.get('Content-Length', 0))
        if not 0 < length <= 1024 * 1024:
            raise ValueError('JSON body required, maximum 1 MiB')
        return json.loads(self.rfile.read(length), parse_constant=lambda v: (_ for _ in ()).throw(ValueError('non-finite JSON')))
