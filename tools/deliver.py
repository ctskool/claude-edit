"""Deliver a voice-only picture preview or the approved picture with its final sound.

  python tools/deliver.py <project> <base> --mode picture-preview|final [--picture file]
  python tools/deliver.py <project> <base> --mode final --stitched <stitched.mp4> [--source-swap path ...]

Pictures carry a render manifest; adopting an old render is an explicit human assertion.
HyperFrames audio is always replaced before the unchanged finish.py mastering step.
A project with a beat map is a reviewed project. Its final takes only a stitched picture from tools/beat_review/final.py, which needs the approval record.
From there on the project is the frozen bundle that picture came from, sound included. The output check runs on the delivered file.
"""
import argparse, json, os, shutil, subprocess, sys, time, uuid
from fractions import Fraction
from pathlib import Path
import sound_mix as sound
from doctor import npm_command

from paths import project_root
ROOT = project_root()
TOOLS = ROOT / "tools"


def run(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n", encoding="utf8")


def write_once(path, value):
    """All of it or none, and never over an existing file: the rename is a hard link, which fails if the name exists."""
    path = Path(path)
    tmp = path.with_name(f"{path.name}.{uuid.uuid4().hex}")
    write_json(tmp, value)
    try:
        os.link(tmp, path)
    except FileExistsError:
        raise ValueError(f"render manifest already exists: {path}; choose a new base")
    finally:
        tmp.unlink()


def render(project, base, fps=None, resolution=None):
    picture = project / "renders" / (base + ".mp4")
    if picture.exists():
        raise ValueError(f"render already exists: {picture}; choose a new base")
    cmd = npm_command("npx", "--no-install", "hyperframes", "render", "--quality", "looks", "-o", f"renders/{base}.mp4")
    if cmd is None:
        raise RuntimeError("Node/npm/npx unavailable; run python tools/doctor.py --fix-hints")
    if fps:
        cmd += ["--fps", str(fps)]
    if resolution:
        cmd += ["--resolution", resolution]
    with open(project / "renders" / (base + ".log"), "w", encoding="utf8") as log:
        run(cmd, cwd=project, stdout=log, stderr=subprocess.STDOUT)
    return picture


def picture_info(picture):
    info = sound.probe(picture)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    return {"width": v["width"], "height": v["height"], "fps": float(Fraction(v["avg_frame_rate"])),
            "picture_duration": float(v.get("duration", info["format"]["duration"]))}


def bind_picture(project, picture, base, revision, adopted=False):
    m = {"picture": str(picture.resolve()), "picture_sha256": sound.file_hash(picture),
         "picture_rev": revision, **picture_info(picture), "adopted": adopted}
    path = project / "renders" / (base + ".render.json")
    if path.exists():
        raise ValueError(f"render manifest already exists: {path}; choose a new base")
    write_json(path, m)
    return path, m


def bind_stitched(project, accepted, base, revision):
    """Binds a stitched picture that final.accept has just read in full. Binding is one atomic write, so a picture is bound completely or not at all."""
    record, picture = accepted["record"], accepted["picture"]
    m = {"picture": str(picture), "picture_sha256": record["file_sha256"], "picture_rev": revision, **picture_info(picture), "adopted": False, "stitched": True,
         "composition_rev": record["composition_rev"], "lock_revision": record["lock_revision"], "profile": accepted["profile"], "profile_hash": record["profile_hash"], "engine_hash": record["engine_hash"],
         "decoded_frames": accepted["frames"], "segments": [{"beat_id": b["beat_id"], "key": b["key"], "content_hash": b["content_hash"]} for b in record["beats"]]}
    path = project / "renders" / (base + ".render.json")
    write_once(path, m)
    return path, m


def reuse_picture(project, picture, revision, fps=None, resolution=None):
    digest, info = sound.file_hash(picture), picture_info(picture)
    sizes = {"portrait": (1080, 1920), "portrait-4k": (2160, 3840), "landscape": (1920, 1080),
             "landscape-4k": (3840, 2160), "square": (1080, 1080), "square-4k": (2160, 2160)}
    for path in sorted((project / "renders").glob("*.render.json")):
        m = json.loads(path.read_text(encoding="utf8"))
        if m.get("picture_sha256") != digest or m.get("picture_rev") != revision:
            continue
        if any(m.get(k) != v for k, v in info.items()):
            continue
        if fps and abs(info["fps"] - fps) > 0.001:
            raise ValueError("--picture fps does not match --fps; reuse never renders")
        if resolution and (info["width"], info["height"]) != sizes.get(resolution):
            raise ValueError("--picture dimensions do not match --resolution; reuse never renders")
        return path, m
    raise ValueError("--picture has no matching render manifest for its SHA-256 and current picture_rev; render the current picture, or use --adopt-picture for an old render you have verified")


def deliver(a):
    project = Path(a.project).resolve()
    source_project = project
    stitched, swaps = getattr(a, "stitched", None), [s for group in a.source_swap for s in group]
    accepted = None
    if stitched and (a.picture or a.adopt_picture or a.fps or a.resolution):
        raise ValueError("--stitched takes the picture as it was validated: no --picture, --adopt-picture, --fps or --resolution")
    if a.mode == "final" and (project / "beats.lock.json").is_file() and not stitched:
        raise ValueError("a reviewed project's final needs --stitched, from tools/beat_review/final.py build, which needs the approval record")
    if swaps and not stitched:
        raise ValueError("listing a swap does not authorize it: a swap is a derivative revision, from tools/beat_review/final.py")
    if stitched:
        sys.path.insert(0, str(TOOLS / "beat_review"))
        import final as final_path
        accepted = final_path.accept(project, stitched, a.mode == "final", swaps)
        project = accepted["project"]
    selected_revision = None
    if (project / "selection.json").is_file():
        from plan_page.common import current_selection, read as read_plan, file_hash as plan_hash
        selected = current_selection(project)
        selected_revision = selected["selection_rev"]
        built = read_plan(project / "build.json")
        if built["selection_rev"] != selected["selection_rev"] or any(plan_hash(project / name) != digest for name, digest in built["files"].items()):
            raise ValueError("stale built picture; rebuild score.js from the current selection before delivery")
    def selection_unchanged():
        if selected_revision and current_selection(project)["selection_rev"] != selected_revision:
            raise ValueError("selection changed during delivery; rebuild the acknowledged selection")
    if Path(a.base).name != a.base or a.base in (".", ".."):
        raise ValueError("base must be a filename without directories")
    out = ROOT / "out"
    out.mkdir(exist_ok=True)
    renders = project / "renders"
    renders.mkdir(exist_ok=True)
    preview = out / "preview" / (a.base + "_preview.mp4")
    preview.parent.mkdir(exist_ok=True)
    video, manifest = out / (a.base + ".mp4"), out / (a.base + "-delivery.json")
    sheet_image, gates_path = out / (a.base + "-sheet.jpg"), out / (a.base + "-gates.json")
    mix_path, mux_path = renders / (a.base + ".mix.wav"), renders / (a.base + ".mux.mov")
    for path in (video, manifest, preview, sheet_image, gates_path, mix_path, mux_path):
        if path.exists():
            raise ValueError(f"refusing to overwrite {path}; choose a new base")
    revision = sound.picture_rev(project)
    checks = {}
    def check(name, *args):
        r = subprocess.run([sys.executable, str(TOOLS / "sound_mix.py"), name, *map(str, args)], capture_output=True, text=True)
        print(r.stdout, end="")
        checks[name] = {"exit_code": r.returncode, "output": r.stdout + r.stderr}
        if r.returncode:
            raise ValueError(f"{name} failed; delivery stopped")
    sheet_hash, sound_identity = None, None
    if a.mode == "final":
        sheet_path = project / "sound.json"
        if not sheet_path.is_file():
            raise ValueError("final requires sound.json; author a sheet, or migrate an old plan. Use picture-preview for picture notes")
        sheet_hash = sound.file_hash(sheet_path)
        sound_identity = sound.sound_identity(project)
        sheet = sound.sheet_of(project)
        if sheet.get("picture_rev") != revision:
            sound.stale(project)
            raise ValueError("final blocked by stale sound.json; review changed events and regenerate cues against this picture_rev")
        if not sheet.get("cues") and not str(sheet.get("empty_reason") or "").strip():
            raise ValueError("an explicitly empty final sheet requires empty_reason")
        check("check-sheet", project)
        check("check-mix", project)
    else:
        checks["sound"] = {"status": "not applicable", "reason": "picture-preview uses only the voice; sound.json is left alone"}
    def sound_unchanged():
        if sound_identity is None:
            return True
        return sound.sound_identity(project) == sound_identity and (not accepted or sound.sound_identity(source_project) == accepted["source_sound_identity"])
    if a.adopt_picture and not a.picture:
        raise ValueError("--adopt-picture requires --picture")
    render_seconds = 0.0
    if accepted:
        picture = accepted["picture"]
        render_manifest, bound = bind_stitched(project, accepted, a.base, revision)
    elif a.picture:
        picture = Path(a.picture).resolve()
        if a.adopt_picture:
            print("WARN adopting picture: this is a human assertion that the old render matches the current picture and media")
            bind_picture(project, picture, a.base, revision, adopted=True)
        render_manifest, bound = reuse_picture(project, picture, revision, a.fps, a.resolution)
    else:
        render_start = time.perf_counter()
        picture = render(project, a.base, a.fps, a.resolution)
        render_seconds = round(time.perf_counter() - render_start, 3)
        selection_unchanged()
        if sound.picture_rev(project) != revision:
            raise ValueError("picture inputs changed during render; no manifest or delivery can be trusted")
        render_manifest, bound = bind_picture(project, picture, a.base, revision)
    duration = float(sound.plan_of(project)["duration"])
    if abs(bound["picture_duration"] - duration) > max(0.1, 2 / bound["fps"]):
        raise ValueError("picture duration does not match plan.json")
    if sound.picture_rev(project) != revision or not sound_unchanged():
        raise ValueError("inputs changed after checks; rerun against stable inputs")
    sound.mix(project, str(mix_path), voice_only=a.mode == "picture-preview")
    run(["ffmpeg", "-v", "error", "-y", "-i", picture, "-i", mix_path, "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "pcm_s24le", "-t", str(duration), mux_path])
    # MOV carries the PCM mix to finish.py without an extra lossy audio encode.
    run([sys.executable, TOOLS / "finish.py", mux_path, video, "--sheet", sheet_image])
    gated = video
    if accepted and bound["width"] > 1080:  # gates.py's bands are 1080x1920 pixels
        gated = accepted["proxy"] = final_path.proxy_of(video, renders / (a.base + ".proxy-1080.mp4"))
    gate_cmd = [sys.executable, str(TOOLS / "gates.py"), str(gated), "--band", "0,0,1080,900", "--pack", "editorial", "--json", str(gates_path)]
    gate = subprocess.run(gate_cmd, capture_output=True, text=True)
    if gate.returncode not in (0, 1, 2) or not gates_path.is_file():
        raise ValueError(f"gates.py could not run: {gate.stderr}")
    g = json.loads(gates_path.read_text(encoding="utf8"))
    # HOUSE.md makes motion findings warn-only. Audio/black findings still block delivery.
    blocking = [f for f in g["findings"] if f["check"] in ("black", "audio", "loudness", "true-peak")]
    checks["gates"] = {"exit_code": gate.returncode, "report": str(gates_path), "verdict": g["verdict"], "findings": g["findings"], "blocking": blocking}
    report = {"mode": a.mode, "status": "checking", "picture": str(picture), "picture_sha256": bound["picture_sha256"],
              "hyperframes_invoked": not bool(a.picture or accepted), "render_elapsed_seconds": render_seconds,
              "picture_rev": revision, "render_manifest": str(render_manifest), "sound_sheet_sha256": sheet_hash,
              "sound_sheet": str(project / "sound.json") if sheet_hash else None, "sound_identity": sound_identity, "mix": str(mix_path),
              "output": str(video), "output_sha256": sound.file_hash(video), "duration": duration,
              "width": bound["width"], "height": bound["height"], "fps": bound["fps"],
              "source_swaps": swaps, "checks": checks}
    if accepted:
        approval = accepted.get("approval") or {}
        derivative = accepted["derivative"]
        report.update(composition_rev=accepted["record"]["composition_rev"], lock_revision=accepted["record"]["lock_revision"], profile=accepted["profile"], bundle=str(accepted["home"]), project=str(project),
                      approval={k: approval.get(k) for k in ("approved_file_sha256", "composition_rev", "lock_revision", "result", "created")} if approval else None,
                      derivative=None if not derivative else {k: derivative[k] for k in ("base_composition_rev", "source_edits", "swaps", "sound")},
                      frame_map=None if not derivative else {k: v for k, v in derivative["frame_map"].items() if k != "beats"},
                      sound_audition="UNVERIFIED until Chase listens")
    write_json(manifest, report)
    try:
        if blocking:
            raise ValueError(f"gates failed: {blocking}")
        for finding in g["findings"]:
            print(f"WARN gates {finding['check']}: {finding['msg']}")
        check("check-media", video, "--manifest", manifest)
        if accepted:
            output = final_path.check_delivered(accepted, video)
            checks["output"] = {"status": output["status"], "report": output.get("path"), "waived": output.get("waived", []), "coverage": output["checks"].get("O7"),
                                "statuses": {k: c["status"] for k, c in output["checks"].items()}}
            print(f"output check on the delivered file: {output['status']}")
            if output["status"] == "FAIL":
                raise ValueError(f"the output check failed on the delivered file: {output.get('path')}")
        selection_unchanged()
        if sound.picture_rev(project) != revision or sound.file_hash(picture) != bound["picture_sha256"] or not sound_unchanged():
            raise ValueError("inputs changed during delivery; rerun against stable inputs")
        phone = ["-vf", "scale=1080:1920:flags=area"] if bound["width"] > 1080 else []
        run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", video, *phone, "-c:v", "libx264", "-preset", "slow", "-b:v", "3800k", "-maxrate", "4500k", "-bufsize", "8000k",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", preview])
        report.update(status=checks["output"]["status"] if accepted else "PASS", preview=str(preview), preview_sha256=sound.file_hash(preview))
    except Exception as e:
        report.update(status="FAIL", error=str(e))
        raise
    finally:
        write_json(manifest, report)
    print(f"{report['status']} delivered {video}; manifest {manifest}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project")
    ap.add_argument("base")
    ap.add_argument("--mode", required=True, choices=["picture-preview", "final"])
    ap.add_argument("--picture")
    ap.add_argument("--adopt-picture", action="store_true")
    ap.add_argument("--stitched", help="a stitched.mp4 from tools/beat_review/final.py build")
    ap.add_argument("--fps", type=float)
    ap.add_argument("--resolution", choices=["portrait", "portrait-4k", "landscape", "landscape-4k", "square", "square-4k"])
    ap.add_argument("--source-swap", action="append", nargs="+", default=[])
    a = ap.parse_args()
    try:
        sys.exit(deliver(a))
    except (ValueError, KeyError, OSError, StopIteration, subprocess.CalledProcessError) as e:
        print(f"FAIL {e}", file=sys.stderr)
        sys.exit(1)
