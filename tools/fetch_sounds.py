"""Download the sounds we may use but not pass on, then cut their slices.

  python tools/fetch_sounds.py [--template ivory] [--check]

Reads templates/<template>/sfx/fetch.json. Each file downloads into its "dir" unless it's already there, must match its sha256,
and then sound_mix.py cuts the slices that use it. --check only reports what's present, missing or changed, and downloads
nothing. The files and their slices stay on this machine: never commit, publish or share them.
"""
import argparse, hashlib, json, sys, urllib.request
from pathlib import Path

from paths import project_root
ROOT = project_root()
sys.path.insert(0, str(ROOT / "tools"))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--template", default="ivory")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    files = json.loads((ROOT / "templates" / a.template / "sfx" / "fetch.json").read_text(encoding="utf8"))["files"]
    ready, bad = [], 0
    for f in files:
        p = ROOT / f["dir"] / f["file"]
        if not p.exists():
            if a.check:
                print(f"missing  {f['file']}"); bad += 1; continue
            p.parent.mkdir(parents=True, exist_ok=True)
            req = urllib.request.Request(f["url"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                p.write_bytes(r.read())
            print(f"fetched  {f['file']}")
        if sha(p) != f["sha256"]:
            print(f"CHANGED  {f['file']}: not the file the slices were cut from. Check {f['page']}"); bad += 1; continue
        print(f"ok       {f['file']}")
        ready += f["sounds"]
    if ready and not a.check:
        import sound_mix
        sound_mix.slices(ready)
        print("sliced   " + ", ".join(ready))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
