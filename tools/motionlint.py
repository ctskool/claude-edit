"""Static motion lint for a HyperFrames composition - run BEFORE rendering (complements `npx hyperframes lint`).

Usage: python motionlint.py <index.html> [--pack saraev|editorial|signal]
ERROR (exit 2): determinism breakers, CDN deps, CSS animations, layout-property tweens, background-clip:text.
WARN  (exit 1): tweens without explicit ease/duration, ease monoculture (>70% of >=6 tweens on one ease),
                will-change on scaled elements, pack bans, repetitive sound design (packs in SFX_RULES: the same SFX
                file back to back, one file on too many cues).
Patterns from 02ui motionlint/rhythm and the HyperFrames determinism rules.
"""
import argparse
import re
import sys
from collections import Counter

PACK_BANS = {
    "editorial": [(r"backdrop-filter", "glass/backdrop-filter is off-style for editorial"),
                  (r"text-shadow:\s*0 0 \d+px", "glow is off-style for editorial")],
    "saraev": [(r"radial-gradient\([^)]*(#ff|#f0|rgba\(255)", "bright radial blobs are off-style for saraev")],
    "signal": [(r"((?<!sans-)\bserif\b|Newsreader|Instrument Serif)", "serif type is off-style for signal")],
}
# Author feedback on the editorial finals (2026-10-23): "a little repetitive in terms of the sound design" - 27 cues
# from 7 files, click-soft + pop = 63%, 5 back-to-back repeats. Max share of one file; variety otherwise comes from
# rotating within event classes (styles/editorial/STYLE.md house rule 2), not from a quota.
SFX_RULES = {"editorial": 0.25}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--pack")
    a = ap.parse_args()
    src = open(a.html, encoding="utf-8").read()
    errors, warns = [], []
    # CSS-only checks look inside <style> blocks so JS comments like "// transition: wipe" don't trip them.
    css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", src, re.S))
    for pat, msg in [(r"(?<![-\w])transition:\s*(?!none)", "CSS transition (animate with the GSAP timeline)"),
                     (r"@keyframes|(?<![-\w])animation:\s*\w", "CSS keyframe animation (use the GSAP timeline)"),
                     (r"background-clip:\s*text", "background-clip:text renders invisible in headless capture")]:
        for _ in re.finditer(pat, css):
            errors.append(f"<style>: {msg}")

    for pat, msg in [(r"Math\.random\(", "Math.random (use a seeded PRNG)"), (r"Date\.now\(|performance\.now\(|new Date\(", "render-time clock"),
                     (r"setTimeout\(|setInterval\(|requestAnimationFrame\(", "timer/rAF-driven state"),
                     (r"<script[^>]+src=[\"']https?://", "CDN script (vendor it under assets/)"),
                     (r"@import\s+url\([\"']?https?://|<link[^>]+href=[\"']https?://fonts", "remote fonts (ship woff2 locally)"),
                     (r"gsap\.defaults\(", "gsap.defaults() hides per-tween eases")]:
        for m in re.finditer(pat, src):
            line = src[:m.start()].count("\n") + 1
            errors.append(f"L{line}: {msg}")

    tweens = list(re.finditer(r"\.(to|from|fromTo)\(([^;]*?)\)\s*[,;)\n]", src, re.S))
    eases = []
    for m in tweens:
        body = m.group(2)
        line = src[:m.start()].count("\n") + 1
        if re.search(r"\b(top|left|bottom|right|width|height)\s*:", body) and "clipPath" not in body:
            warns.append(f"L{line}: tween on a layout property (prefer x/y/scale/clipPath)")
        e = re.search(r"ease\s*:\s*[\"']([^\"']+)[\"']", body)
        if e:
            eases.append(e.group(1).split("(")[0])
        elif "ease" not in body and "duration" in body:
            warns.append(f"L{line}: tween without explicit ease")
    if len(eases) >= 6:
        top, n = Counter(eases).most_common(1)[0]
        if n / len(eases) > 0.7:
            warns.append(f"ease monoculture: {top} on {n}/{len(eases)} tweens (>70%) - vary arrive/exit/settle eases")
    if re.search(r"will-change:\s*transform", src):
        warns.append("will-change:transform on scaled elements blurs text in capture")
    for pat, msg in PACK_BANS.get(a.pack or "", []):
        if re.search(pat, src, re.I):
            warns.append(f"pack ban: {msg}")

    if a.pack in SFX_RULES:
        cues = []
        for tag in re.findall(r"<audio[^>]*>", src):
            m_src, m_t = re.search(r'src="([^"]+)"', tag), re.search(r'data-start="([0-9.]+)"', tag)
            if m_src and m_t and "voice" not in m_src.group(1).lower():
                cues.append((float(m_t.group(1)), m_src.group(1).split("/")[-1]))
        cues.sort()
        if cues:
            share = SFX_RULES[a.pack]
            files = Counter(f for _, f in cues)
            for (t0, f0), (t1, f1) in zip(cues, cues[1:]):
                if f0 == f1:
                    warns.append(f"sound: {f0} twice in a row ({t0:.2f}s, {t1:.2f}s) - rotate within its event class")
            top, n = files.most_common(1)[0]
            if len(cues) >= 8 and n / len(cues) > share:
                warns.append(f"sound: {top} on {n}/{len(cues)} cues (>{share:.0%}) - vary the palette")

    for e in errors:
        print("ERROR", e)
    for w in warns:
        print("WARN ", w)
    print(f"motionlint: {len(errors)} error(s), {len(warns)} warning(s); {len(tweens)} tweens, eases={dict(Counter(eases).most_common(6))}")
    sys.exit(2 if errors else (1 if warns else 0))


if __name__ == "__main__":
    main()
