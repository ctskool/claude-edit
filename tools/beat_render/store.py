"""Segment store: work/<id>/beat/. CONTRACT.md section 6.

A segment is built in tmp/, verified, and only then renamed to its key directory, so segment.json existing means complete. A crash leaves only tmp/, which the next run clears.
"""
import json, os, shutil, subprocess, sys, uuid
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import sound_mix
from common import sha

SCHEMA = 1
LIMIT_BYTES = 21474836480
ROOTS = ("segments", "refs", "plans", "audio", "stitched", "changes", "checks", "tmp")


def root_of(project):
    """Outside the project, so picture_rev and HyperFrames never see it."""
    return Path(project).resolve().parents[1] / "beat"


def write_json(path, value):
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(value, indent=1, ensure_ascii=False) + "\n", encoding="utf8", newline="\n")
    os.replace(tmp, path)


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf8"))
    except (OSError, ValueError):
        return default


def open_store(root):
    root = Path(root)
    for name in ROOTS:
        (root / name).mkdir(parents=True, exist_ok=True)
    if not (root / "store.json").exists():
        write_json(root / "store.json", {"limit_bytes": LIMIT_BYTES})
    return root


# ---- one run at a time


def alive(pid):
    if os.name == "nt":
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"], capture_output=True, text=True)
        return f'"{pid}"' in r.stdout
    try:
        os.kill(int(pid), 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def lock(root):
    """One run per store. A lock left by a dead run is taken over, and its tmp/ cleared.

    The pid is written first and the lock made by a hard link, which is atomic and fails if the name exists. So a lock file is never empty, and an empty one is never a live run's.
    """
    path = Path(root) / "run.lock"
    mine = path.with_name(f"run.lock.{uuid.uuid4().hex}")
    mine.write_text(json.dumps({"pid": os.getpid()}), encoding="utf8")
    try:
        for _ in range(2):
            try:
                os.link(mine, path)
            except FileExistsError:
                held = read_json(path, {})
                if held.get("pid") and alive(held["pid"]):
                    raise RuntimeError(f"another run holds {path}: pid {held['pid']}")
                path.unlink(missing_ok=True)
                continue
            clear_tmp(root)
            return path
        raise RuntimeError(f"could not take {path}")
    finally:
        mine.unlink(missing_ok=True)


def unlock(root):
    (Path(root) / "run.lock").unlink(missing_ok=True)


def clear_tmp(root):
    tmp = Path(root) / "tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)


def new_tmp(root):
    path = Path(root) / "tmp" / uuid.uuid4().hex
    path.mkdir(parents=True)
    return path


# ---- segments


def segment_dir(root, profile_hash, key):
    return Path(root) / "segments" / profile_hash[:16] / key


def find(root, profile_hash, key):
    """The record of a complete segment, or None. Reading it counts as use."""
    folder = segment_dir(root, profile_hash, key)
    record = read_json(folder / "segment.json")
    if not record or record.get("input_key") != key or record.get("profile_hash") != profile_hash:
        return None
    video = folder / record["file"]
    if not video.is_file() or video.stat().st_size != record["bytes"] or not (folder / "segment.framemd5").is_file():
        return None
    os.utime(folder / "segment.json")
    return record


def intact(root, profile_hash, key):
    """find, and its bytes and rows still hash to what was published. A flipped byte keeps the size, so find passes it, stitch refuses it, and nothing would ever repair it.
    This hashes the file, so it is for what a run is about to reuse, not for every lookup."""
    record = find(root, profile_hash, key)
    if record is None:
        return None
    folder = segment_dir(root, profile_hash, key)
    same_file = record.get("file_sha256") == sound_mix.file_hash(folder / record["file"])
    same_rows = record.get("decoded", {}).get("content_hash") == sha("\n".join(rows_of(root, profile_hash, key)))
    return record if same_file and same_rows else None


def rows_of(root, profile_hash, key):
    text = (segment_dir(root, profile_hash, key) / "segment.framemd5").read_text(encoding="utf8")
    return text.split()


def publish(root, built, profile_hash, key, force=False):
    """built holds segment.mp4, segment.framemd5 and segment.json. Only a forced render replaces a good segment a stitched picture names, because that picture stops validating."""
    target = segment_dir(root, profile_hash, key)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if not force and intact(root, profile_hash, key) and key in in_use(root):
            raise ValueError(f"segment {key[:16]} belongs to a stitched picture: only --force replaces it")
        old = Path(root) / "tmp" / ("replaced-" + uuid.uuid4().hex)
        os.replace(target, old)
        shutil.rmtree(old, ignore_errors=True)
    os.replace(built, target)
    return target


def refs_dir(root, profile_hash, key):
    return Path(root) / "refs" / profile_hash[:16] / key


def plan_dir(root, plan_key):
    return Path(root) / "plans" / plan_key[:16]


def prune_plans(root, keep=2):
    plans = [p for p in (Path(root) / "plans").iterdir() if p.is_dir() and len(p.name) == 16 and (p / "plan.json").is_file()]
    plans.sort(key=lambda p: (p / "plan.json").stat().st_mtime, reverse=True)
    for p in plans[keep:]:
        shutil.rmtree(p)


# ---- what a stitched picture still needs


def tree_bytes(path):
    return sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file())


def in_use(root):
    """Keys that current.json or any stitched/*/stitch.json still names."""
    root = Path(root)
    keys = set()
    current = read_json(root / "current.json", {})
    for entry in current.values():
        record = read_json(root / "stitched" / entry["stitched"] / "stitch.json", {})
        keys.update(b["key"] for b in record.get("beats", []))
    for path in (root / "stitched").glob("*/stitch.json"):
        keys.update(b["key"] for b in read_json(path, {}).get("beats", []))
    return keys


def evict(root):
    """Oldest last_used first, over segments/ and refs/, until under the limit. What a picture still names stays, even over the limit."""
    root = Path(root)
    limit = read_json(root / "store.json", {}).get("limit_bytes", LIMIT_BYTES)
    protected = in_use(root)
    entries = []
    for top in ("segments", "refs"):
        for folder in (root / top).glob("*/*"):
            stamp = folder / "segment.json"
            used = (stamp if stamp.exists() else folder).stat().st_mtime
            entries.append((used, top, folder, tree_bytes(folder)))
    total = sum(e[3] for e in entries)
    removed = []
    for used, top, folder, size in sorted(entries, key=lambda e: e[0]):
        if total <= limit:
            break
        if folder.name in protected:
            continue
        shutil.rmtree(folder)
        total -= size
        removed.append(folder.name)
    return {"bytes": total, "limit_bytes": limit, "removed": len(removed), "over_limit": total > limit}


# ---- the picture the next step reads


def set_current(root, profile, entry, status, finished=True):
    """A picture becomes current only once both checks ran to the end and neither failed. Any other goes in last_attempt.json, so nothing that reads current.json gets it.

    A review picture's best status is UNVERIFIED, so a check that never finished would read the same as a clean one. finished is what tells them apart.
    Written after the checks, never by the stitch. A later picture that does not fail clears its profile's last attempt.
    """
    root = Path(root)
    entry = {**entry, "status": status}
    attempts = read_json(root / "last_attempt.json", {})
    if status == "FAIL" or not finished:
        write_json(root / "last_attempt.json", {**attempts, profile: entry})
        return False
    current = read_json(root / "current.json", {})
    write_json(root / "current.json", {**current, profile: entry})
    if profile in attempts:
        del attempts[profile]
        write_json(root / "last_attempt.json", attempts)
    return True


def latest(root, profile):
    """The last picture stitched for this profile, failed or not. change diffs against it. Any key it lacks renders, so which picture this is costs time only."""
    root = Path(root)
    return read_json(root / "last_attempt.json", {}).get(profile) or read_json(root / "current.json", {}).get(profile)


# ---- change records


def next_change(root):
    numbers = [int(p.stem) for p in (Path(root) / "changes").glob("[0-9][0-9][0-9][0-9].json")]
    return (Path(root) / "changes") / f"{max(numbers, default=0) + 1:04d}.json"
