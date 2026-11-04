"""From Chase's Approve click to the delivered file, with nothing in between for him to do.

  python tools/beat_review/autofinal.py start <project>                      the approved picture's final, in its own process (Claude, once he is happy with the sound)
  python tools/beat_review/autofinal.py run <project> --picture <sha256>     the same, in this process

approval.start starts it on his click when the sound is ready: sound.json written for this picture and no sound note open. Otherwise the click waits for sound (SKILL.md section 9), and
Claude runs `start` when he says the sound is good.

A 4K30 final when prep made assets/face_half_4k.mp4, swapped in for the review face clip; 1080p30 otherwise (a project prepped before it existed: SKILL.md section 10 has the recipe).
The build waits its turn on gpu_lock, then deliver.py and check-media, the same commands section 10 lists. The file is out/<id>_<style>_final_4k30.mp4 (or _final.mp4 at 1080p30).
beat/approvals/final-<file_sha16>.json says how far it got, and the player shows it.
"""
import argparse, os, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import project_root
ROOT = project_root()
sys.path[:0] = [str(HERE), str(ROOT / "tools" / "beat_render"), str(ROOT / "tools")]
import review
import sound_mix
import store

FACE, FACE_4K = "assets/face_half.mp4", "assets/face_half_4k.mp4"
WORKERS = 6
RULE = "Approve goes straight to the final"


def state_file(project, picture_sha):
    folder = review.root_of(project) / "approvals"
    folder.mkdir(exist_ok=True)
    return folder / f"final-{picture_sha[:16]}.json"


def sound_ready(project):
    """Why the sound holds the final, or None. The final freezes sound.json with the picture, so it waits for a sheet of this picture with every sound note closed."""
    if not (Path(project) / "sound.json").is_file():
        return "no sound.json yet: section 9 first"
    if sound_mix.sheet_of(project).get("picture_rev") != sound_mix.picture_rev(project):
        return "sound.json is stale against this picture: review it first"
    left = review.sound_notes(project)
    if left:
        return f"{len(left)} sound note(s) still open"
    return None


def status(project, picture_sha):
    s = store.read_json(state_file(project, picture_sha))
    if s and s.get("stage") not in ("done", "error", "after sound") and not store.alive(s.get("pid")):
        return {**s, "stage": "error", "why": "the final stopped with no result"}
    return s


def start(project, picture_sha=None):
    """Starts the final in its own process, unless one is already running or done for this picture, or the sound is not ready (then it says so and waits)."""
    if picture_sha is None:
        active = store.read_json(review.root_of(project) / "approvals" / "active.json")
        if not active:
            raise ValueError("no approved picture: he approves in the player first")
        picture_sha = active["file_sha256"]
    s = status(project, picture_sha)
    if s and s["stage"] not in ("error", "after sound"):
        return s
    held = sound_ready(project)
    if held:
        s = {"stage": "after sound", "why": held, "started": review.now()}
        store.write_json(state_file(project, picture_sha), s)
        return s
    home = review.home_of(project)
    log = open(home / f"final-{picture_sha[:16]}.log", "a", encoding="utf8")
    p = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()), "run", str(project), "--picture", picture_sha], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                         creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0))
    log.close()
    s = {"pid": p.pid, "stage": "waiting", "started": review.now()}
    store.write_json(state_file(project, picture_sha), s)
    return s


def step(cmd, what):
    print(review.now(), what, " ".join(str(c) for c in cmd), flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=ROOT, capture_output=True, text=True, encoding="utf8", errors="replace")
    print(r.stdout[-4000:], r.stderr[-2000:], flush=True)
    if r.returncode:
        raise RuntimeError(f"{what} exited {r.returncode}: {(r.stdout + r.stderr).strip().splitlines()[-1:] or ''}")
    return r.stdout


def run(project, picture_sha):
    project = Path(project).resolve()
    home = review.home_of(project)
    path = state_file(project, picture_sha)
    held = {"pid": os.getpid(), "started": review.now()}

    def stage(name, **fields):
        held.update(stage=name, **fields)
        store.write_json(path, held)

    try:
        four_k = (home / FACE_4K).is_file()
        spec = "4k30" if four_k else "1080p30"
        cmd = [sys.executable, "-B", ROOT / "tools/beat_review/final.py", "build", project, "--spec", spec, "--workers", WORKERS]
        if four_k:
            swaps = home / "swaps-4k30.json"
            store.write_json(swaps, {"swaps": [{"path": FACE, "file": str(home / FACE_4K), "source": "prep_source.py face_half_4k: the face rows of raw/cut.mp4 at full width, on the review clip's frame map",
                                                "why": "4K30 final: real 4K camera pixels for the bottom half instead of the 1280-wide review clip",
                                                "authorized_by": f"Chase's Approve click on picture {picture_sha[:16]} at {review.now()}, under the standing rule {RULE}"}]})
            cmd += ["--swaps", swaps]
        stage("waiting", spec=spec)
        lock = [sys.executable, ROOT / "tools/gpu_lock.py", "run", "--who", f"{spec} final {home.name}", "--"]
        stage("building", spec=spec, building=review.now())
        out = step(lock + cmd, "build")
        built = re.search(r"^built \S+: (.+)$", out, re.M)
        if not built:
            raise RuntimeError("the build printed no file")
        base = f"{home.name}_{project.name}_final" + ("_4k30" if four_k else "")
        stage("delivering", spec=spec)
        step([sys.executable, ROOT / "tools/deliver.py", project, base, "--mode", "final", "--stitched", built.group(1).strip()] + (["--source-swap", FACE] if four_k else []), "deliver")
        file = ROOT / "out" / f"{base}.mp4"
        step([sys.executable, ROOT / "tools/sound_mix.py", "check-media", file], "check-media")
        stage("done", spec=spec, file=str(file), finished=review.now())
    except Exception as e:
        stage("error", why=str(e)[:600])
        raise


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["start", "run"])
    ap.add_argument("project")
    ap.add_argument("--picture")
    a = ap.parse_args(argv)
    if a.command == "start":
        print(start(Path(a.project).resolve(), a.picture))
        return 0
    if not a.picture:
        ap.error("run needs --picture")
    run(a.project, a.picture)
    return 0


if __name__ == "__main__":
    sys.exit(main())
