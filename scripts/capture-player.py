"""Record the review player with a note being left, and screenshot its default look, for the README and gallery.

  python scripts/capture-player.py http://localhost:4761 [--beat b08] [--note "..."]

Point it at a player serving a SCRATCH copy of an edit: leaving the note writes that project's notes.jsonl.
Writes renders/player-note.mp4 (the gallery source) and media/player.png. Needs ffmpeg and Playwright's Chromium.
"""
import argparse
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SIZE = {"width": 1440, "height": 900}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--beat", default="b08")
    ap.add_argument("--note", default="Zoom into the Ultra card here, the limit line is too small to read")
    a = ap.parse_args()
    (ROOT / "renders").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        browser = pw.chromium.launch()
        # The player's default look is light; pin it so the capture never follows this machine's dark mode.
        context = browser.new_context(viewport=SIZE, color_scheme="light", device_scale_factor=1,
                                      record_video_dir=tmp, record_video_size=SIZE)
        page = context.new_page()
        opened = time.monotonic()  # the recording starts with the page; the load before the action is cut
        page.goto(a.url, wait_until="networkidle")
        page.wait_for_selector("#readout")
        page.wait_for_timeout(1500)
        page.screenshot(path=str(ROOT / "media" / "player.png"))
        start = max(0.0, time.monotonic() - opened - 0.6)
        page.locator(f"text=/^{a.beat}$/ >> visible=true").first.click()
        page.wait_for_timeout(900)
        page.keyboard.press("Space")
        page.wait_for_timeout(1600)
        page.keyboard.press("Space")
        page.wait_for_timeout(700)
        page.keyboard.press("n")
        page.wait_for_selector("#composer:not([hidden])")
        page.wait_for_timeout(400)
        page.keyboard.type(a.note, delay=38)
        page.wait_for_timeout(500)
        page.keyboard.press("Enter")
        page.wait_for_timeout(900)
        page.locator("text=/^Notes/i >> visible=true").first.click()
        page.wait_for_timeout(2200)
        video = page.video.path()
        context.close()
        browser.close()
        out = ROOT / "renders" / "player-note.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.2f}", "-i", video, "-vf", "fps=30", "-c:v", "libx264", "-crf", "20",
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)], check=True)
    print(out, "and", ROOT / "media" / "player.png")


if __name__ == "__main__":
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is not on PATH")
    main()
