"""One heavy job at a time across sessions and agents: transcription, cut-outs, renders (long-form, 4K finals, and since
2026-11-16 every review render from tools/beat_render/run.py; `--no-queue` skips it for the player's native-size beat).

  python tools/gpu_lock.py run --who "hook2 review render" -- python tools/beat_review/review.py ...
  python tools/gpu_lock.py status
  python tools/gpu_lock.py hold --who "..."     # take it with no command (release with: release)
  python tools/gpu_lock.py release

The lock is a folder (mkdir is atomic on every OS) holding owner.json. A holder whose process is gone is stale and is
cleared, so a crashed job never blocks the queue. `run` waits, checking every 5 s, and says who it is waiting for.
A renderer takes it in-process with `with gpu_lock.held(who):` (the long-form renderers do).
"""
import argparse, contextlib, json, os, subprocess, sys, time
from pathlib import Path

LOCK = Path(__file__).resolve().parents[1] / "work" / ".gpu-lock"
ENV = "CLAUDE_EDIT_GPU_LOCK"  # set for everything that runs under the lock, so a renderer started by `run` does not wait for its own parent


def alive(pid):
    if not pid:
        return False
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def owner():
    try:
        return json.loads((LOCK / "owner.json").read_text(encoding="utf8"))
    except (OSError, ValueError):
        return None


def take(who, pid):
    waited = 0
    while True:
        try:
            LOCK.mkdir(parents=True)
            (LOCK / "owner.json").write_text(json.dumps({"who": who, "pid": pid, "since": time.strftime("%H:%M:%S")}), encoding="utf8")
            return
        except FileExistsError:
            o = owner()
            if o and not alive(o.get("pid")):
                print(f"gpu_lock: clearing a stale lock from {o.get('who')!r}", file=sys.stderr)
                release()
                continue
            if waited % 300 == 0:
                print(f"gpu_lock: waiting for {o.get('who') if o else 'another job'} (since {o.get('since') if o else '?'})", file=sys.stderr)
            time.sleep(5)
            waited += 5


def release():
    (LOCK / "owner.json").unlink(missing_ok=True)
    try:
        LOCK.rmdir()
    except OSError:
        pass


@contextlib.contextmanager
def held(who):
    """For a renderer to take the lock itself: `with gpu_lock.held("long-form render 1110-slop"): ...`.
    Passes straight through when this process already runs under the lock (`gpu_lock.py run`, or an outer held())."""
    if os.environ.get(ENV):
        yield
        return
    take(who, os.getpid())
    os.environ[ENV] = str(os.getpid())
    try:
        yield
    finally:
        os.environ.pop(ENV, None)
        release()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["run", "status", "hold", "release"])
    ap.add_argument("--who", default="")
    ap.add_argument("--pid", type=int, help="hold: the process the lock belongs to (default: this shell's parent)")
    argv = sys.argv[1:]
    cut = argv.index("--") if "--" in argv else len(argv)
    a = ap.parse_args(argv[:cut])
    a.cmd = argv[cut + 1:]
    if a.action == "status":
        o = owner()
        print(f"held by {o['who']!r} since {o['since']} (pid {o['pid']}, {'running' if alive(o['pid']) else 'gone'})" if o else "free")
        return 0
    if a.action == "release":
        release()
        return 0
    if a.action == "hold":
        take(a.who or "held by hand", a.pid or os.getppid())
        print("held")
        return 0
    cmd = a.cmd
    if not cmd:
        sys.exit("run needs a command after --")
    take(a.who or " ".join(cmd)[:80], os.getpid())
    try:
        return subprocess.run(cmd, env={**os.environ, ENV: str(os.getpid())}).returncode
    finally:
        release()


if __name__ == "__main__":
    sys.exit(main())
