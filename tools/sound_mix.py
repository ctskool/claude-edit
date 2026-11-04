"""Sound for an edit: cut the palette, level cues against the voice, mix, and check the result.

  python tools/sound_mix.py slices                         cut templates/ivory/sfx/sfx.json into wavs
  python tools/sound_mix.py mix <project_dir> <out.wav>    voice + sound.json (old plans still work)
  python tools/sound_mix.py check <project_dir>            check-sheet + check-mix
  python tools/sound_mix.py migrate|stale <project_dir>    move old cues / report stale events
  python tools/sound_mix.py rebind <project_dir> --why W   move a sheet to this picture_rev, only if no cue's event moved
  python tools/sound_mix.py check-media <file.mp4>         delivered audio + manifest duration

The check runs on the cue track itself, so it needs no stem separation. Reference numbers are in
templates/ivory/sound.md.
"""
import argparse, hashlib, html, json, math, os, re, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
from urllib.parse import unquote
import numpy as np

from paths import project_root
ROOT = str(project_root())
SFX = os.path.join(ROOT, "templates", "ivory", "sfx")
SR = 48000
UNDER_MIN, UNDER_MAX = 10.0, 26.0  # LU of the cue track under the voice, read directly. See sound.md
HITS_MAX = 8.0  # cues per 30 s, whole-clip average


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<f4")


def db(x):
    return 20 * np.log10(x + 1e-9)


def voice_ref(path):
    x = decode(path)
    n = int(SR * 0.02)
    k = len(x) // n
    lv = db(np.sqrt((x[: k * n].reshape(k, n) ** 2).mean(1)))
    return float(np.percentile(lv[lv > -60], 90))


def attack(x):
    """Seconds to the first point within 12 dB of the slice's 5 ms peak."""
    n = int(SR * 0.005)
    k = len(x) // n
    lv = db(np.sqrt((x[: k * n].reshape(k, n) ** 2).mean(1)))
    return int(np.argmax(lv >= lv.max() - 12)) * 0.005


def level(x):
    a = int(attack(x) * SR)
    seg = x[a : a + int(SR * 0.25)]
    return float(db(np.sqrt((seg**2).mean())))


def lufs(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=framelog=quiet", "-f", "null", "-"], capture_output=True, text=True, check=True).stderr
    return float(re.findall(r"I:\s+(-?(?:[\d.]+|inf)) LUFS", err)[-1])


def palette():
    return json.loads((Path(SFX) / "sfx.json").read_text(encoding="utf8"))


def slices(names=None):
    p = palette()
    for name, s in p["sounds"].items():
        if names and name not in names:
            continue
        src = os.path.join(ROOT, s.get("source_dir", p["source_dir"]), s["file"])
        dur = s["to"] - s["from"]
        fade = s.get("fade", min(0.03, dur / 4))
        af = f"afade=t=in:d=0.002,afade=t=out:st={dur - fade:.3f}:d={fade}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(s["from"]), "-t", str(dur), "-i", src, "-af", af, "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le", os.path.join(SFX, name + ".wav")], check=True)
        x = decode(os.path.join(SFX, name + ".wav"))
        print(f"{name:10} attack {attack(x):.3f} s, level {level(x):.1f} dB")


def cue_graph(cues, root, voice=None):
    args, parts = [], []
    if not cues and not voice:
        return ["-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=stereo"], "[0:a]anull[m]"
    if voice:
        args += ["-i", voice]
    off = 1 if voice else 0
    for i, c in enumerate(cues):
        args += ["-i", os.path.join(root, c["file"])]
        start, dur = c.get("media_start") or 0, c.get("dur") or 30
        parts.append(f"[{i + off}:a]atrim=start={start}:duration={dur},asetpts=PTS-STARTPTS,aresample={SR},aformat=channel_layouts=stereo,volume={c['gain']},adelay={int(round(c['at'] * 1000))}:all=1[a{i}]")
    labels = "".join(f"[a{i}]" for i in range(len(cues)))
    if voice:
        parts.append(f"[0:a]aresample={SR},aformat=channel_layouts=stereo[v]")
        labels = "[v]" + labels
    parts.append(f"{labels}amix=inputs={len(cues) + off}:normalize=0:dropout_transition=0[m]")
    return args, ";".join(parts)


def plan_of(root):
    return json.loads((Path(root) / "plan.json").read_text(encoding="utf8"))


def sheet_of(root):
    path = Path(root) / "sound.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf8"))
    return {"version": 1, "cues": [dict(c, event_id=f"legacy.{c['t']}") for c in plan_of(root).get("sfx_timeline", [])]}


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sound_identity(root):
    """The sheet and every cue's bytes. Missing media is no sound revision, even if its sheet has not changed."""
    root = Path(root).resolve()
    sheet = root / "sound.json"
    if not sheet.is_file():
        raise ValueError("missing sound.json")
    files = {}
    for cue in sheet_of(root)["cues"]:
        rel = cue["file"]
        path = (root / rel).resolve()
        if not path.is_relative_to(root) or Path(rel).is_absolute() or path == sheet:
            raise ValueError(f"cue media must be inside the project: {rel}")
        if not path.is_file():
            raise ValueError(f"missing cue media: {rel}")
        files[rel] = file_hash(path)
    return {"sheet_sha256": file_hash(sheet), "cue_files": files}


def attrs(tag):
    return {k.lower(): html.unescape(v) for k, _, v in re.findall(r'([\w-]+)\s*=\s*([\"\'])(.*?)\2', tag, re.S)}


def picture_html(root):
    text = (Path(root) / "index.html").read_text(encoding="utf8")
    def strip_cue(m):
        a = attrs(m[0])
        return m[0] if a.get("id") == "voice" or Path(a.get("src", "")).stem == "voice" else ""
    text = re.sub(r'<audio\b[^>]*>.*?</audio>[ \t]*(?:<!--.*?-->)?', strip_cue, text, flags=re.S | re.I)
    return re.sub(r'(?m)^[ \t]*\r?\n', '', text)


def voice_of(root):
    for tag in re.findall(r'<audio\b[^>]*>', picture_html(root), re.I):
        a = attrs(tag)
        if "src" in a:
            return str(Path(root) / unquote(a["src"]))
    return str(Path(root) / "assets" / "voice.m4a")


MEDIA_EXT = r'(?:mp4|mov|mkv|webm|m4a|mp3|wav|aiff|ogg|flac|png|jpe?g|webp|gif|svg|avif|woff2?|ttf|otf)'
MODULE = re.compile(r'["\'(]([^"\'()<>\s]+\.(?:m?js|css))(?:\?[^"\']*)?["\')]', re.I)
DYNAMIC = re.compile(r'assets/(?![\w./-]+\.\w+)')  # as ownership.py: a path the page builds at runtime names no one file
NOT_AUTHORING = {"__pycache__", "_bak"}


def media_refs(value):
    if re.fullmatch(rf'[^\n<>"|]+\.{MEDIA_EXT}', value, re.I):
        yield value
    yield from re.findall(rf'(?:[\w.-]+[/\\])+[^\s"\'<>;,)]+\.{MEDIA_EXT}\b', value, re.I)
    yield from re.findall(rf'["\']([^"\'<>]+\.{MEDIA_EXT})(?:\?[^"\']*)?["\']', value, re.I)
    yield from re.findall(rf'url\(\s*["\']?([^"\'()]+\.{MEDIA_EXT})["\']?\s*\)', value, re.I)


def authoring_files(root):
    """Everything that writes the generated HTML, listed in the plan or not."""
    folder = Path(root) / "tools_local"
    if not folder.is_dir():
        return []
    return sorted(p.relative_to(root).as_posix() for p in folder.rglob("*") if p.is_file() and not set(p.parts) & NOT_AUTHORING)


def reachable_modules(root, text, listed):
    """The listed files, plus every local script and stylesheet the page or those files name, followed to the end. What they reference is picture input, though index.html never mentions it."""
    root = Path(root).resolve()
    seen, todo = set(), list(listed)
    def follow(source, base):
        for ref in MODULE.findall(source):
            ref = unquote(html.unescape(ref))
            if re.match(r'[a-z]+:|//', ref, re.I):
                continue
            path = (base / ref).resolve()
            path = path if path.is_file() else (root / ref).resolve()
            if path.is_file() and path.is_relative_to(root):
                todo.append(path.relative_to(root).as_posix())
    follow(text, root)
    while todo:
        rel = todo.pop()
        if rel not in seen:
            seen.add(rel)
            follow((root / rel).read_text(encoding="utf8", errors="replace"), (root / rel).parent)
    return sorted(seen)


def picture_rev(root):
    """Hash picture inputs by content, including same-path media replacements, never cues.
    A render profile is not an input, so a new profile leaves sound bound. The generated HTML is bound to what wrote it, and assets only a module names are covered."""
    root = Path(root)
    p = plan_of(root)
    p.pop("sfx_timeline", None)
    text = picture_html(root)
    h = hashlib.sha256()
    def add(name, data):
        h.update(name.encode("utf8") + b"\0" + str(len(data)).encode() + b"\0" + data)
    add("index.html", text.encode("utf8"))
    add("plan.json", json.dumps(p, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf8"))
    # Relay builds its picture in external modules. The HTML shell alone cannot
    # identify a changed score or kit; bind the explicit compiler file list too.
    listed = sorted(p.get("composition_files", []))
    for name in listed:
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError(f"missing or unsafe composition file: {name}")
        add(name, file_hash(path).encode())
    modules = reachable_modules(root, text, [*listed, *authoring_files(root)])
    for name in modules:
        if name not in listed:
            add(name, file_hash(root / name).encode())
    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for v in value.values():
                yield from strings(v)
        elif isinstance(value, list):
            for v in value:
                yield from strings(v)
    refs = {ref for value in [text, *strings(p)] for ref in media_refs(value)}
    sources = [(root / name).read_text(encoding="utf8", errors="replace") for name in modules]
    # A cue sound a module names is still a cue, and never picture.
    refs.update(ref for source in sources for ref in media_refs(source) if not ref.replace("\\", "/").startswith("assets/sfx/"))
    if any(DYNAMIC.search(source) for source in [text, *sources]) and (root / "assets").is_dir():
        refs.update(q.relative_to(root).as_posix() for q in (root / "assets").rglob("*") if q.is_file() and "sfx" not in q.relative_to(root).parts)
    refs.add(os.path.relpath(voice_of(root), root).replace("\\", "/"))
    for ref in sorted(refs):
        ref = unquote(html.unescape(ref)).replace("\\", "/")
        if re.match(r'https?://|data:', ref):
            raise ValueError(f"picture media must be local to hash it: {ref}")
        path = root / ref
        if not path.is_file() and (Path(ROOT) / ref).is_file():
            path = Path(ROOT) / ref
        add(ref, file_hash(path).encode() if path.is_file() else b"MISSING")
    return h.hexdigest()


def events_of(p):
    events = {}
    def walk(value):
        if isinstance(value, dict):
            if "event_id" in value:
                events[value["event_id"]] = value.get("t", value.get("time", value.get("start")))
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)
    walk({k: v for k, v in p.items() if k != "sfx_timeline"})
    return events


def migrate(root):
    path = Path(root) / "sound.json"
    if path.exists():
        raise ValueError(f"{path} already exists; migration never overwrites a sheet")
    sheet = sheet_of(root)
    sheet["picture_rev"] = picture_rev(root)
    if not sheet["cues"]:
        sheet["empty_reason"] = "Old plan has no sound cues."
    path.write_text(json.dumps(sheet, indent=2) + "\n", encoding="utf8")
    print(f"PASS migrated {len(sheet['cues'])} cues to {path}; WARN legacy event anchors are unverified")


def stale(root):
    if not (Path(root) / "sound.json").exists():
        print("FAIL missing sound.json; run migrate for an old plan or author a sheet")
        return 1
    sheet, p = sheet_of(root), plan_of(root)
    changed = sheet.get("picture_rev") != picture_rev(root)
    print(f"{'FAIL stale' if changed else 'PASS current'} picture_rev")
    events = events_of(p)
    for c in sheet["cues"]:
        eid = c.get("event_id", "missing")
        if eid not in events or events[eid] is None:
            print(f"WARN {eid}: event existence and timing cannot be confirmed")
        elif abs(float(events[eid]) - c["t"]) > 0.001:
            print(f"WARN moved event {eid}: cue {c['t']:.3f}s -> event {events[eid]:.3f}s")
    if changed:
        print("WARN placement, proof/CTA spans, media, tails and word masking cannot be confirmed; review cues before updating picture_rev")
    return int(changed)


def rebind(root, why, base_events=None):
    """Moves a sheet to the current picture_rev, and says so in the sheet. Only for a change that moves no cue: a new hash, a sharper source, a fps map.
    An event that moved, or one this cannot confirm, stops it, because those cues need review.
    base_events: the approved picture's events. Then a cue is held to its event not moving between the two pictures, so an offset
    the approved sheet already had (and Chase heard) carries over instead of refusing a re-render of the same picture."""
    if not str(why or "").strip():
        raise ValueError("rebind needs a reason")
    path = Path(root) / "sound.json"
    sheet, events = sheet_of(root), events_of(plan_of(root))
    cues = [c for c in sheet.get("cues", []) if not str(c.get("event_id")).startswith("legacy.")]  # a legacy cue has no event to move with, and check-sheet warns on it
    def moved_(c):
        now = events.get(c.get("event_id"))
        if now is None:
            return True
        if base_events is not None:
            was = base_events.get(c["event_id"])
            return was is None or abs(float(now) - float(was)) > 0.001
        return abs(float(now) - c["t"]) > 0.001
    moved = [c.get("event_id") for c in cues if moved_(c)]
    if moved:
        raise ValueError(f"rebind refused, these cues' events moved or cannot be confirmed: {moved[:8]}")
    new = picture_rev(root)
    sheet["rebound"] = [*sheet.get("rebound", []), {"from": sheet.get("picture_rev"), "to": new, "why": why}]
    sheet["picture_rev"] = new
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(sheet, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    os.replace(tmp, path)
    return new


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def check_sheet(root):
    p, sheet = plan_of(root), sheet_of(root)
    cues, sounds, events = sheet.get("cues"), palette()["sounds"], events_of(p)
    failed = False
    def line(status, msg):
        nonlocal failed
        print(f"{status} {msg}")
        failed |= status == "FAIL"
    modern = (Path(root) / "sound.json").exists()
    if sheet.get("version") != 1 or not isinstance(cues, list):
        line("FAIL", "sound sheet requires version 1 and cues array")
        return 1
    if modern:
        current = sheet.get("picture_rev") == picture_rev(root)
        line("PASS" if current else "FAIL", "picture_rev matches current picture" if current else "stale picture_rev; review sound.json against the current picture")
    else:
        line("WARN", "old plan fallback; picture revision is UNVERIFIED (run migrate)")
    if not events:
        line("WARN", "old plan has no event_id anchors; event coverage is UNVERIFIED")
    if p.get("cta_start") is None:
        line("WARN", "CTA span UNVERIFIED: plan.json has no cta_start")
    if not cues:
        line("PASS", "zero cues; explicitly silent cue track")
    sources, slices_used, times, seen = [], [], [], set()
    spans = []
    for beat in p.get("beats", []):
        span = beat.get("proof_span")
        if span:
            if isinstance(span, dict):
                span = [span["start"], span["end"]]
            spans.append(span)
    cuts = [b["start"] for b in p.get("beats", []) if b.get("layout") == "full-face"]
    cuts += [c["t"] for c in p.get("render_checks", {}).get("cut_frames", []) if c.get("to") == "full-face"]
    for i, c in enumerate(cues):
        label = f"cue {i + 1}"
        if not isinstance(c, dict) or any(not isinstance(c.get(k), (int, float)) or isinstance(c.get(k), bool) or not math.isfinite(c[k]) for k in ("t", "at", "gain", "dur")):
            line("FAIL", f"{label}: t, at, gain and dur must be finite numbers")
            continue
        if not 0 <= c["t"] < p["duration"] or c["at"] < 0 or c["gain"] < 0 or c["dur"] <= 0 or not isinstance(c.get("media_start", 0), (int, float)) or not math.isfinite(c.get("media_start", 0)) or c.get("media_start", 0) < 0:
            line("FAIL", f"{label}: invalid cue time, gain or media span")
            continue
        times.append(c["t"])
        name = Path(c.get("file", "")).stem
        s = sounds.get(name) if Path(c.get("file", "")).suffix.lower() == ".wav" else None
        if not s:
            line("FAIL", f"{label}: sound {c.get('file')} is not in sfx.json")
        else:
            sources.append(s["file"])
            slices_used.append((c["t"], (s["file"], s["from"], s["to"])))
            if s.get("tier") == "special" and not str(c.get("requested_by") or "").strip():
                line("FAIL", f"{label}: special sound needs requested_by naming Chase's note")
        media = Path(root) / c.get("file", "")
        if not media.is_file():
            line("FAIL", f"{label}: missing cue media {media}")
            continue
        media_dur = float(probe(media)["format"]["duration"])
        start = c.get("media_start", 0)
        if start >= media_dur:
            line("FAIL", f"{label}: media_start is past end of source")
        end = c["at"] + min(c["dur"], max(0, media_dur - start))
        eid = c.get("event_id", "")
        if str(eid).startswith("legacy."):
            line("WARN", f"{label}: {eid} event coverage UNVERIFIED")
        elif eid not in events:
            line("FAIL", f"{label}: event_id {eid!r} is missing from plan.json")
        elif events[eid] is None:
            line("FAIL", f"{label}: event_id {eid} has no time in plan.json")
        if eid in seen:
            line("FAIL", f"{label}: more than one cue on event_id {eid}")
        seen.add(eid)
        if p.get("cta_start") is not None and (c["t"] >= p["cta_start"] or (c["gain"] > 0 and end > p["cta_start"])):
            line("FAIL", f"{label}: cue in CTA span starting {p['cta_start']}s")
        if c["gain"] > 0:
            for a, b in spans:
                if c["at"] < b and end > a:
                    line("FAIL", f"{label}: audible span overlaps proof_span {a}-{b}s")
            for cut in sorted(set(cuts)):
                if c["at"] < cut < end:
                    line("WARN", f"{label}: audible tail past cut to full-face at {cut}s (full_face on)")
    for a, b in zip(sorted(times), sorted(times)[1:]):
        if b - a < 1.2 - 1e-9:
            line("FAIL", f"cue spacing {b-a:.3f}s at {a}/{b}s; minimum 1.2s")
    ordered = sorted(slices_used)
    for a, b in zip(ordered, ordered[1:]):
        if a[1] == b[1]:
            line("FAIL", f"back-to-back source slice at {a[0]}/{b[0]}s")
    if len(cues) < 8:
        line("WARN", "source-file share skipped under 8 cues; never add cues to meet a share")
    else:
        for source, count in Counter(sources).items():
            if count / len(cues) > 0.25:
                line("FAIL", f"source-file share {source}: {count}/{len(cues)} exceeds 25%")
    if not failed:
        line("PASS", "check-sheet")
    return int(failed)


def mix(root, out, voice_only=False):
    p = plan_of(root)
    args, fc = cue_graph([] if voice_only else sheet_of(root)["cues"], root, voice_of(root))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", fc, "-map", "[m]", "-t", str(p["duration"]), "-c:a", "pcm_s24le", out], check=True)


def check_mix(root):
    p = plan_of(root)
    cues = sheet_of(root)["cues"]
    if not cues:
        print("PASS zero cues: no cue track; level check not applicable; busiest 30 s: 0 cues")
        return 0
    with tempfile.TemporaryDirectory() as d:
        tmp = os.path.join(d, "cues.wav")
        args, fc = cue_graph(cues, root)
        subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", fc, "-map", "[m]", "-t", str(p["duration"]), tmp], check=True)
        under = lufs(voice_of(root)) - lufs(tmp)
    hits = len(cues) / p["duration"] * 30
    ok_level = UNDER_MIN <= under <= UNDER_MAX
    ok_rate = hits <= HITS_MAX
    print(f"{'PASS' if ok_level else 'FAIL'} cue track {under:.1f} LU under the voice (band {UNDER_MIN:.0f}-{UNDER_MAX:.0f})")
    print(f"{'PASS' if ok_rate else 'WARN'} {len(cues)} cues, {hits:.1f} per 30 s (warning above {HITS_MAX:.0f})")
    ts = sorted(c["t"] for c in cues)
    busiest = max(ts, key=lambda t: sum(t <= x < t + 30 for x in ts))
    print(f"PASS busiest 30 s: {sum(busiest <= x < busiest + 30 for x in ts)} cues in {busiest:.3f}-{busiest+30:.3f}s (information only)")
    print("WARN how it sounds and stressed-word masking: UNVERIFIED until Chase listens")
    return int(not ok_level)


def check(root):
    a, b = check_sheet(root), check_mix(root)
    return max(a, b)


def check_media(path, manifest=None):
    path = Path(path)
    manifest = Path(manifest) if manifest else path.with_name(path.stem + "-delivery.json")
    failed = False
    def line(ok, msg):
        nonlocal failed
        print(f"{'PASS' if ok else 'FAIL'} {msg}")
        failed |= not ok
    info = probe(path)
    audio = [s for s in info["streams"] if s["codec_type"] == "audio"]
    line(bool(audio), "delivered audio stream present")
    if audio:
        err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True, check=True).stderr
        integrated = float(re.findall(r"I:\s+(-?(?:[\d.]+|inf)) LUFS", err)[-1])
        peak = float(re.findall(r"Peak:\s+(-?(?:[\d.]+|inf)) dBFS", err)[-1])
        line(abs(integrated + 14) <= 1, f"delivered loudness {integrated:.1f} LUFS (target -14 +/-1)")
        line(peak <= -1.5, f"delivered true peak {peak:.1f} dBTP (max -1.5)")
    if not manifest.is_file():
        line(False, f"missing delivery manifest {manifest}; duration UNVERIFIED")
    else:
        m = json.loads(manifest.read_text(encoding="utf8"))
        line(m.get("output_sha256") == file_hash(path), "delivery manifest binds this exact output file")
        duration = float(info["format"]["duration"])
        expected = float(m["duration"])
        line(abs(duration - expected) <= max(0.1, 2 / float(m["fps"])), f"duration {duration:.3f}s against manifest {expected:.3f}s")
    return int(failed)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["slices", "mix", "migrate", "stale", "rebind", "revision", "check", "check-sheet", "check-mix", "check-media"])
    ap.add_argument("project", nargs="?")
    ap.add_argument("output", nargs="?")
    ap.add_argument("--manifest")
    ap.add_argument("--why")
    a = ap.parse_args()
    try:
        if a.command == "slices":
            slices()
        elif a.command == "mix":
            mix(a.project, a.output)
        elif a.command == "migrate":
            migrate(a.project)
        elif a.command == "rebind":
            print(f"PASS rebound to {rebind(a.project, a.why)}")
        elif a.command == "revision":
            print(picture_rev(a.project))
        elif a.command == "check-media":
            sys.exit(check_media(a.project, a.manifest))
        else:
            sys.exit({"check": check, "check-sheet": check_sheet, "check-mix": check_mix, "stale": stale}[a.command](a.project))
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as e:
        print(f"FAIL {e}")
        sys.exit(1)
