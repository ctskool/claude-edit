"""Reuse capture_shots plates and boxes; keep every generation unless --prune."""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from urllib.parse import urlsplit

from paths import project_root
ROOT = project_root()
CACHE = ROOT / "library" / "captures"
CAPTURE = ROOT / "tools" / "capture_shots.py"
PNG = b"\x89PNG\r\n\x1a\n"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(item):
    """Names are destinations; every other option participates in identity."""
    if not isinstance(item, dict):
        raise ValueError("each spec item must be an object")
    options = item.get("options", {})
    if not isinstance(options, dict):
        raise ValueError("options must be an object")
    out = dict(options)
    for k, value in item.items():
        if k in ("name", "options"):
            continue
        if k in out and out[k] != value:
            raise ValueError("conflicting option: " + k)
        out[k] = value
    selector = out.pop("selector", None)
    if selector is not None:
        if "element" in out and out["element"] != selector:
            raise ValueError("selector and element disagree")
        out["element"] = selector
    out.setdefault("theme", "light")
    out.setdefault("width", 1280)
    out.setdefault("height", 800)
    out.setdefault("full_page", False)
    out.setdefault("hide", [])
    if out.get("element") in (None, ""):
        out.pop("element", None)
    if not isinstance(out.get("url"), str) or urlsplit(out["url"]).scheme not in ("http", "https"):
        raise ValueError("url must be http(s)")
    if out["theme"] not in ("light", "dark"):
        raise ValueError("theme must be light or dark")
    for field in ("width", "height"):
        if type(out[field]) is not int or out[field] <= 0:
            raise ValueError(field + " must be a positive integer")
    if type(out["full_page"]) is not bool:
        raise ValueError("full_page must be Boolean")
    if not isinstance(out["hide"], list) or any(not isinstance(s, str) for s in out["hide"]):
        raise ValueError("hide must be a list of selectors")
    if "element" in out and not isinstance(out["element"], str):
        raise ValueError("element must be a selector string")
    # Sorting hide is unnecessary: the complete options, including future options,
    # remain in the key even if the underlying capture tool does not support them.
    json.dumps(out, allow_nan=False)
    return out


def capture_key(item, tool=CAPTURE):
    payload = {"schema": 1, "spec": canonical(item), "capture_tool_sha256": digest(tool)}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def timestamp(value):
    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    # Old hand-written metadata may use local time. It is ambiguous: miss it.
    if value.tzinfo is None:
        raise ValueError("captured_at needs a timezone")
    return value.astimezone(timezone.utc)


def numbers(item, boxes):
    """Conservative flags: a plate is evidence, never a source of verified figures."""
    host = urlsplit(item["url"]).hostname or ""
    text = json.dumps(boxes, ensure_ascii=False)
    reasons = []
    if host == "github.com" or host.endswith(".github.com"):
        reasons.append("GitHub stars/forks may change")
    if re.search(r"pric|billing|/plans(?:/|$)", item["url"], re.I):
        reasons.append("prices may change")
    if re.search(r"stars?\b|forks?\b|watchers?\b|prices?\b|[$€£¥]\s*\d|\d[\d,.]*\s*(USD|EUR|GBP)\b", text, re.I):
        reasons.append("boxes contain counters or prices")
    if item.get("changing_numbers") or item.get("options", {}).get("changing_numbers"):
        reasons.append("source spec marks changing numbers")
    return reasons


def artifacts(folder):
    return [folder / n for n in ("capture.png", "capture.json", "meta.json")]


def read_entry(folder, key, expected):
    try:
        paths = artifacts(folder)
        if folder.is_symlink() or any(p.is_symlink() for p in paths):
            return None
        meta = json.loads(paths[2].read_text(encoding="utf-8"))
        if meta["key"] != key or meta["canonical_spec"] != expected:
            return None
        if any(digest(p) != meta["sha256"][p.name] for p in paths[:2]):
            return None
        if not paths[0].read_bytes().startswith(PNG):
            return None
        boxes = json.loads(paths[1].read_text(encoding="utf-8"))
        if boxes.get("login_wall") is not False or boxes.get("url") != expected["url"]:
            return None
        return meta, boxes
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


def generations(folder):
    if folder.is_symlink() or not folder.is_dir():
        return []
    return [folder] + sorted(p for p in folder.glob("v-*") if p.is_dir() and not p.is_symlink())


def find_hit(cache, key, spec, now, max_age_days):
    found = []
    for folder in generations(cache / key):
        entry = read_entry(folder, key, spec)
        if entry:
            try:
                at = timestamp(entry[0]["captured_at"])
            except (ValueError, KeyError, TypeError, AttributeError):
                continue
            if timedelta(0) <= now - at < timedelta(days=max_age_days):
                found.append((at, folder, entry))
    return max(found, key=lambda row: row[0]) if found else None


def copy_pair(folder, output, name):
    for source, suffix in (("capture.png", ".png"), ("capture.json", ".json")):
        target = output / (name + suffix)
        if target.is_symlink():
            raise ValueError("refusing output symlink: " + str(target))
        shutil.copyfile(folder / source, target)


def publish(cache, key, source, spec, now):
    """Refreshes append a generation; old PNGs, boxes and metadata stay intact."""
    parent = cache / key
    if parent.is_symlink():
        raise ValueError("refusing cache symlink: " + str(parent))
    try:
        parent.mkdir(parents=True)
        folder = parent
    except FileExistsError:
        folder = parent / ("v-" + now.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex)
        folder.mkdir()
    png = source / (spec["name"] + ".png")
    box = source / (spec["name"] + ".json")
    boxes = json.loads(box.read_text(encoding="utf-8"))
    if not png.read_bytes().startswith(PNG) or boxes.get("url") != spec["url"] or not isinstance(boxes.get("boxes"), list):
        raise ValueError("invalid capture output: " + spec["name"])
    if boxes.get("login_wall") is not False:
        raise ValueError("sign-in wall: " + spec["name"])
    shutil.copyfile(png, folder / "capture.png")
    shutil.copyfile(box, folder / "capture.json")
    meta = {"schema": 1, "key": key, "url": spec["url"], "captured_at": now.isoformat(),
            "source_spec": spec, "canonical_spec": canonical(spec), "number_checks": numbers(spec, boxes),
            "sha256": {p.name: digest(p) for p in artifacts(folder)[:2]}}
    # Metadata is written last; an interrupted generation cannot become a hit.
    (folder / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return folder, boxes


def prune(cache, now, max_age_days):
    """Only remove expired, recognized cache triplets, never arbitrary directories."""
    count = 0
    if not cache.exists():
        return count
    for parent in sorted(cache.iterdir()):
        if not re.fullmatch(r"[0-9a-f]{64}", parent.name):
            continue
        # Children first, then the triplet in the key directory.
        for folder in reversed(generations(parent)):
            try:
                meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
                if meta["key"] != parent.name or now - timestamp(meta["captured_at"]) < timedelta(days=max_age_days):
                    continue
                paths = artifacts(folder)
                if any(p.is_symlink() for p in paths):
                    continue
                for p in paths:
                    p.unlink(missing_ok=True)
                if not any(folder.iterdir()):
                    folder.rmdir()
                count += 1
            except (OSError, ValueError, KeyError, TypeError, AttributeError):
                continue
    print("PRUNED", count, "expired generations")
    return count


def capture(out_dir, spec, max_age_days=7, cache=CACHE, tool=CAPTURE, runner=None, now=None, do_prune=False):
    if not math.isfinite(max_age_days) or max_age_days < 0:
        raise ValueError("max-age-days must be finite and nonnegative (0 forces refresh)")
    if not isinstance(spec, list):
        raise ValueError("spec must be a list")
    output, cache, tool = Path(out_dir).resolve(), Path(cache).absolute(), Path(tool).resolve()
    if cache.is_symlink():
        raise ValueError("refusing cache symlink")
    cache = cache.resolve()
    if output == cache or cache in output.parents or output in cache.parents:
        raise ValueError("output and cache must be separate directories")
    fixed_clock = now is not None
    now = now or datetime.now(timezone.utc)
    names, prepared = set(), []
    for item in spec:
        norm = canonical(item)
        name = item.get("name", "")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name) or name.endswith("."):
            raise ValueError("name must be a simple filename stem")
        if name.casefold() in names:
            raise ValueError("duplicate name: " + name)
        names.add(name.casefold())
        prepared.append((item, norm, capture_key(item, tool)))
    output.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    misses, hits = {}, 0
    for item, norm, key in prepared:
        hit = find_hit(cache, key, norm, now, max_age_days)
        if hit:
            _, folder, (_, boxes) = hit
            copy_pair(folder, output, item["name"])
            print("HIT", item["name"], key[:12])
            warn_numbers(item, boxes)
            hits += 1
        else:
            print("MISS", item["name"], key[:12])
            misses.setdefault(key, []).append(item)
    failures = 0
    if misses:
        # Capture a batch of unique misses. Never import Playwright on a cache hit.
        with tempfile.TemporaryDirectory(prefix="capture-cache-") as tmp:
            stage = Path(tmp)
            requests = [{**canonical(items[0]), "name": items[0]["name"]} for items in misses.values()]
            spec_path = stage / "spec.json"
            spec_path.write_text(json.dumps(requests, ensure_ascii=False), encoding="utf-8")
            command = [sys.executable, str(tool), str(stage), str(spec_path)]
            result = (runner or subprocess.run)(command, check=False)
            if result.returncode:
                print("ERROR capture_shots.py exited", result.returncode)
                return result.returncode
            captured_at = now if fixed_clock else datetime.now(timezone.utc)
            for key, items in misses.items():
                try:
                    folder, boxes = publish(cache, key, stage, items[0], captured_at)
                    for item in items:
                        copy_pair(folder, output, item["name"])
                        warn_numbers(item, boxes)
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    failures += 1
                    print("ERROR", str(exc))
    print("HITS", hits, "MISSES", len(prepared) - hits, "CAPTURED", len(misses) - failures)
    if do_prune:
        prune(cache, now, max_age_days)
    return 1 if failures else 0


def warn_numbers(item, boxes):
    reasons = numbers(item, boxes)
    if reasons:
        print("CHECK", item["name"] + ": check the numbers against facts.json (" + "; ".join(reasons) + ")")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_dir")
    parser.add_argument("spec")
    parser.add_argument("--max-age-days", type=float, default=7)
    parser.add_argument("--prune", action="store_true", help="remove expired cache generations after this run")
    args = parser.parse_args(argv)
    try:
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8-sig"))
        return capture(args.out_dir, spec, args.max_age_days, do_prune=args.prune)
    except (OSError, ValueError, TypeError) as exc:
        print("ERROR", str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())
