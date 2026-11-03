"""Isolated v2 page; all review and media routes belong to the live server."""
import argparse
import os
import re
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.dont_write_bytecode = True
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.beat_review.server import make_handler as live_make_handler

SKINS = Path(__file__).with_name('skins')


def make_handler(project, api=None):
    class Handler(live_make_handler(project, api=api)):
        def do_GET(self):
            route = unquote(urlsplit(self.path).path)
            if route in ('/', '/index.html'):
                return self.send_file(Path(__file__).with_name('index.html'), 'text/html; charset=utf-8')
            # Skins are plain stylesheets in skins/, picked with ?skin=<name>.
            skin = re.fullmatch(r'/skins/([a-z0-9-]+\.(?:css|svg|png|woff2))', route)
            if skin and (SKINS / skin.group(1)).is_file():
                kind = {'css': 'text/css; charset=utf-8', 'svg': 'image/svg+xml', 'png': 'image/png', 'woff2': 'font/woff2'}
                return self.send_file(SKINS / skin.group(1), kind[skin.group(1).rsplit('.', 1)[1]])
            return super().do_GET()
    return Handler


def serve(project, api=None, port=None):
    port = int(os.environ.get('PORT', '4750')) if port is None else port
    if port in (4744, 4745):
        raise ValueError('Ports 4744 and 4745 belong to the live player; use 4750.')
    server = ThreadingHTTPServer(('127.0.0.1', port), make_handler(project, api=api))
    print(f'http://localhost:{server.server_address[1]} | {Path(project).resolve()}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project')
    serve(parser.parse_args().project)
