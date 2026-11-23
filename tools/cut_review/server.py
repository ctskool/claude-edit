"""Cut review page: Chase listens to the tight cut and moves joins by ear, before any picture is rendered.

  python tools/cut_review/server.py work/<id>/raw [--no-render]      (PORT, default 4765)

Needs rawcut.py session, transcribe and cut to have run in that folder. The page plays the cut's sound straight from
a48.wav through the current keeps, so a moved join is heard at once and nothing is encoded while he works. Approve
writes his keeps as the cut (core.apply) and starts `rawcut.py render`, which cuts the screen take and the camera
file from them in one pass. State and files: core.py.

While he listens, the server renders the machine's cut in the background (`rawcut.py render --draft --low`, log in
draft.log): cut.mp4 and cam_cut.mp4 as a draft, and the pieces they are joined from in _pieces. His Approve stops
that render if it is still going and starts the real one, which re-uses every piece his changes did not touch.
--no-draft turns the background render off.
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import core  # noqa: E402

HERE = Path(__file__).resolve().parent
RAWCUT = HERE.parent / "rawcut.py"


class Review:
    def __init__(self, d, render=True, draft=True):
        self.d = os.path.abspath(d); self.lock = threading.Lock(); self.v = 1; self.auto_render = render
        self.draft = None; self.draft_log = None
        self.st = core.load_state(self.d); self.A = core.open_audio(self.d)
        self.words = core.rawcut.load(self.d, "words.json", [])
        self.peaks = core.peaks(self.A)
        self.proc = None; self.render = {"state": "idle", "secs": 0, "note": ""}
        S = self.st["S"]; self.video = [dict(v, ready=False) for v in core.video_sources(S)]

        def make():                                                  # the small camera copies, kept between runs
            try:
                core.videos(self.d, S, lambda k: [v.update(ready=True) for v in self.video if v["vid"] == k])
            except Exception as e:
                print(f"camera copies failed: {e}", flush=True)
            if render and draft:                                      # after the copies, so the two do not fight for the encoder
                self.start_draft()
        threading.Thread(target=make, daemon=True).start()

    def start_draft(self):
        """The machine's cut, rendered while he listens: nothing to do when the files on disk already are this cut."""
        E = core.rawcut.load(self.d, "edl.json"); done = core.rawcut.load(self.d, "rendered.json")
        with self.lock:
            if self.proc or self.draft or (done and done.get("keeps") == E["keeps"]):
                return
            self.draft_log = open(os.path.join(self.d, "draft.log"), "w", encoding="utf-8")
            self.draft = subprocess.Popen([sys.executable, str(RAWCUT), "render", self.d, "--draft", "--low"],
                                          stdout=self.draft_log, stderr=subprocess.STDOUT)

    def stop_draft(self):
        p, self.draft = self.draft, None
        if p and p.poll() is None:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True) if os.name == "nt" else p.kill()
            p.wait()
        if self.draft_log:
            self.draft_log.close(); self.draft_log = None

    def state(self):
        st = self.st; S = st["S"]; kept = set(st["base_words"])
        return {"id": Path(self.d).parent.name, "fps": st["fps"], "sr": core.SR, "frames": S["frames"], "v": self.v,
                "files": [{"start_frame": f["start_frame"], "frames": f["frames"], "camera": "camera" in f} for f in S["files"]],
                "auto": st["auto"], "keeps": st["keeps"], "approved": st["approved"], "carried": st["carried"],
                "words": [[w[0], w[1], w[2], int(i in kept)] for i, w in enumerate(self.words)],
                "auto_joins": {k: {"big": c.get("big", False), "runon": bool(c.get("runon"))} for k, c in st["auto_joins"].items()},
                "notes": st["notes"], "general": st["general"], "auto_render": self.auto_render, "render": self.status(),
                "video": [{"ready": v["ready"], "lag": v["lag"], "vid": v["vid"], "first": v["first"], "delay": v.get("delay", 0)}
                          for v in self.video]}

    def put(self, body):
        with self.lock:
            st = self.st
            if "keeps" in body:
                keeps = core.norm(body["keeps"], st["S"])
                if not keeps:
                    raise ValueError("nothing kept")
                if keeps != st["keeps"]:
                    st["keeps"] = keeps; st["approved"] = None; self.v += 1
            if "notes" in body:
                st["notes"] = [{"f": int(n["f"]), "text": str(n["text"])[:2000]} for n in body["notes"]]
            if "general" in body:
                st["general"] = str(body["general"])[:8000]
            core.save_draft(self.d, st)
            return {"v": self.v, "keeps": st["keeps"]}

    def approve(self):
        with self.lock:
            r = core.apply(self.d, self.st); r["approved"] = self.st["approved"]
        if self.auto_render:
            self.start_render()
        return r

    def start_render(self):
        self.stop_draft(); self.stop_render()
        log = open(os.path.join(self.d, "render.log"), "w", encoding="utf-8")
        self.proc = subprocess.Popen([sys.executable, str(RAWCUT), "render", self.d], stdout=log, stderr=subprocess.STDOUT)
        self.render = {"state": "running", "t0": time.time(), "secs": 0, "note": ""}
        proc = self.proc

        def wait():
            rc = proc.wait(); log.close()
            if self.proc is not proc:                                 # replaced by a newer approval
                return
            tail = open(os.path.join(self.d, "render.log"), encoding="utf-8", errors="replace").read().strip().splitlines()[-3:]
            bad = rc != 0 or any("MISMATCH" in x for x in tail)
            self.render = {"state": "failed" if bad else "done", "secs": round(time.time() - self.render["t0"]),
                           "note": " | ".join(tail)}
        threading.Thread(target=wait, daemon=True).start()

    def stop_render(self):
        if self.proc and self.proc.poll() is None:                    # a second approval: the first render is stale
            p, self.proc = self.proc, None
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True) if os.name == "nt" else p.kill()

    def status(self):
        r = dict(self.render)
        if r["state"] == "running":
            r["secs"] = round(time.time() - r["t0"])
        r.pop("t0", None)
        return r


def make_handler(R):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, body, kind="application/json", code=200):
            if not isinstance(body, (bytes, bytearray)):
                body = json.dumps(body).encode()
            self.send_response(code); self.send_header("Content-Type", kind); self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(body)

        def send_range(self, path, kind):
            size = os.path.getsize(path); a, b = 0, size - 1; rng = self.headers.get("Range", "")
            if rng.startswith("bytes="):
                x, _, y = rng[6:].partition("-")
                a = int(x) if x else max(0, size - int(y)); b = min(size - 1, int(y)) if x and y else size - 1
            self.send_response(206 if rng else 200); self.send_header("Content-Type", kind); self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(b - a + 1))
            if rng:
                self.send_header("Content-Range", f"bytes {a}-{b}/{size}")
            self.end_headers()
            with open(path, "rb") as f:
                f.seek(a); left = b - a + 1
                while left > 0:
                    chunk = f.read(min(1 << 20, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk); left -= len(chunk)

        def do_GET(self):
            u = urlsplit(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}
            try:
                if u.path in ("/", "/index.html"):
                    return self.send((HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
                if u.path == "/state":
                    return self.send(R.state())
                if u.path == "/peaks":
                    return self.send(R.peaks, "application/octet-stream")
                if u.path == "/status":
                    return self.send({"render": R.status(), "approved": R.st["approved"], "video": [v["ready"] for v in R.video]})
                if u.path.startswith("/video/"):
                    k = int(u.path.rsplit("/", 1)[1])
                    if not R.video[k]["ready"]:
                        return self.send({"error": "not ready"}, code=404)
                    return self.send_range(core.video_path(R.d, k), "video/mp4")
                if u.path in ("/pcm", "/raw"):
                    a, n = max(0, int(q["from"])), max(0, min(int(q["n"]), core.SR * 30))
                    if u.path == "/raw":                              # the uncut session, to hear what a join removed
                        c = R.A[a:a + n]; body = c.tobytes() + bytes((n - len(c)) * 2 * R.A.shape[1])
                    else:
                        with R.lock:
                            if int(q.get("v", R.v)) != R.v:
                                return self.send({"error": "stale"}, code=409)
                            keeps = R.st["keeps"]
                        body = core.cut_pcm(R.A, keeps, R.st["fps"], a, n)
                    return self.send(body, "application/octet-stream")
                self.send({"error": "not found"}, code=404)
            except (ConnectionError, BrokenPipeError):
                pass
            except Exception as e:
                self.send({"error": str(e)}, code=400)

        def do_POST(self):
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0) or b"{}")
                if self.path == "/save":
                    return self.send(R.put(body))
                if self.path == "/approve":
                    R.put(body)
                    return self.send(R.approve())
                self.send({"error": "not found"}, code=404)
            except Exception as e:
                self.send({"error": str(e)}, code=400)
    return H


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dir"); ap.add_argument("--no-render", action="store_true", help="Approve writes the cut but does not start the render")
    ap.add_argument("--no-draft", action="store_true", help="do not render the machine's cut in the background while he listens")
    a = ap.parse_args()
    R = Review(a.dir, render=not a.no_render, draft=not a.no_draft)
    srv = ThreadingHTTPServer(("127.0.0.1", int(os.environ.get("PORT", "4765"))), make_handler(R))
    print(f"http://localhost:{srv.server_address[1]} | {R.d} | cut {core.cut_samples(R.st['keeps'], R.st['fps']) / core.SR:.1f}s, "
          f"{len(R.st['keeps']) - 1} joins", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        R.stop_draft(); R.stop_render(); srv.server_close()
