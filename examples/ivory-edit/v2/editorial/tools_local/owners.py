"""Ownership tables for this project: scene windows, HUD rows, chains, extra roots and binds. CONTRACT.md section 3.

Declarations only. tools/beat_render/ownership.py reads the generated page for frames and hashes, and anything not declared here is shell, which touches everything.
tools/beat_check/events.py turns the binds at the end of this file into events.json. Row shapes and examples: templates/ivory/build_kit/README.md.
"""

# Scene windows: ["#<scene root>", start, end] in seconds, in order. A scene can hold several windows. Any change here is timing: everything, plus a new media plan.
WINDOWS = [["#sc-hook", 0.0, 5.167], ["#sc-title", 5.167, 7.5], ["#sc-names", 7.5, 11.5], ["#sc-week", 11.5, 14.567], ["#sc-ultra", 14.567, 18.367],
           ["#sc-q10", 18.367, 21.267], ["#sc-codex", 21.267, 24.3], ["#sc-q13", 24.3, 27.3], ["#sc-list", 27.3, 31.3], ["#sc-max20", 31.3, 32.967],
           ["#sc-four", 32.967, 36.617], ["#sc-over", 36.617, 39.95], ["#sc-table", 39.95, 42.567], ["#sc-q23", 42.567, 44.183], ["#sc-q24", 44.183, 46.7],
           ["#sc-q25", 46.7, 49.433], ["#sc-q26", 49.433, 52.067], ["#sc-q27", 52.067, 54.7], ["#sc-q28", 54.7, 56.067], ["#sc-close", 56.067, 57.65]]

# Names in assets/logos/ this page uses as <symbol id="logo-<name>">.
LOGOS = ["claude"]

# HUD states in the order they play, each ["<name>", t]: "strip" first, then "seat0" up to "seat4", and "ring0" up to "ring4" to flash a socket. Empty means no strip.
# What it counts on a new short is an open decision in layout.md. Here, the three things he recaps at 27.3-31.3, seated where each is first said. No number shows: #count is hidden in style.css.
HUD = [["strip", 5.44], ["seat0", 5.92], ["seat1", 14.16], ["seat2", 16.64], ["ring2", 27.94], ["ring1", 29.3], ["ring0", 30.58]]
HUD_LABEL = "THE RENAME"
HUD_PLUGS = [["logo-claude", "mk"], ["i-calendar", "ic"], ["i-slash", "ic"]]  # one [symbol id, "ic" or "mk"] per seat row
HUD_BINDS = {"strip": "#strip", "seat0": "#plugs .plug:nth-child(1)", "seat1": "#plugs .plug:nth-child(2)", "seat2": "#plugs .plug:nth-child(3)",
             "ring2": "#rings .ring:nth-child(3)", "ring1": "#rings .ring:nth-child(2)", "ring0": "#rings .ring:nth-child(1)"}

# The strip stays on screen and each state builds on the last. No resets are declared here, so each link runs to the last frame.
CHAINS = [{"id": "hud",
           "objects": ["#strip", "#strip-pop", "#socks", "#plugs", "#rings", "#count", "#dot-on"],
           "carries": ["opacity", "scale", "y", "display", "color"],
           "links": ["hud." + name for name, _ in HUD],
           "resets": []}] if HUD else []

# A scene that animates a node outside its own root names it here, and then reaches the last frame. Bottom-half punch-in recipe and cost: build_kit/README.md.
EXTRA_ROOTS = {"scene.sc-q24": ["#face"], "scene.sc-q27": ["#face"]}

# Stills reach the page only through an src or url() in the generated page, so one the page does not name is not in the picture.
LIBRARY = ["assets/stills/", "assets/shots/", "assets/held/", "assets/scenes/", "assets/posts/", "assets/clips/", "assets/logos/"]

# Shell helpers a confined block may call: name to the arguments it needs before it has a time. Each writes only through tl to the selector it is given,
# so the owner audit sees what it does. A block calling anything else goes back in the shell, which touches everything. Never list $, el or own here.
BLOCK_HELPERS = {"A": 1, "show": 2, "hide": 2, "pop": 2, "popFirst": 2, "slotPop": 2, "rise": 2, "cutIn": 2, "on": 2, "off": 2, "drawRect": 2, "drawPath": 2, "word": 2}

HOOK, TITLE, NAMES, WEEK, ULTRA = "scene.sc-hook", "scene.sc-title", "scene.sc-names", "scene.sc-week", "scene.sc-ultra"
CODEX, LIST, MAX20, FOUR, OVER, TABLE, CLOSE = "scene.sc-codex", "scene.sc-list", "scene.sc-max20", "scene.sc-four", "scene.sc-over", "scene.sc-table", "scene.sc-close"
Q10, Q13, Q23, Q24, Q25, Q26, Q27, Q28 = ("scene.sc-q" + n for n in ("10", "13", "23", "24", "25", "26", "27", "28"))

# What each plan event must do in the page. An event with no row here is UNVERIFIED in the source check, never skipped and never PASS.
# event_id: (owner, target, expect, copy, hold_frames, lead_frames). expect is appear, change or present. hold_frames None takes the default in events.py. lead_frames names a designed lead.
# The target is the thing the plan says happens on the word, not whichever element happens to tween then. A clip's own content cannot be measured,
# so a beat whose anchor sits inside a clip binds its plate as present.
EVENT_BINDS = {
    "b01.e1": (HOOK, "#hk-s", "appear", None, None),
    "b01.e2": (HOOK, "#hk-pl-p", "change", None, None),
    "b01.e3": (HOOK, "#hk-pl", "appear", None, None),
    "b01.e4": (HOOK, "#hk-pl-p", "change", None, None),
    "b01.e5": (HOOK, "#hk-s", "appear", None, None),
    "b02.e1": (HOOK, "#hk-u", "appear", None, None),
    "b02.e2": (HOOK, "#hk-pl-p", "change", None, None),
    "b02.e3": (HOOK, "#hk-a", "appear", None, None),
    "b02.e4": (HOOK, "#hk-u", "appear", None, None),
    "b03.e1": (TITLE, "#ti-pl", "present", None, None),
    "b03.e2": (TITLE, "#ti-card", "appear", None, None),
    "b03.e3": (TITLE, "#ti-pl-v", "appear", None, None),
    "b03.e4": ("hud.strip", "#strip", "appear", None, None),
    "b03.e5": ("hud.seat0", "#plugs .plug:nth-child(1)", "appear", None, None),
    "b03.e6": (TITLE, "#ti-pl", "present", None, None),
    "b03.e7": (TITLE, "#ti-pl", "present", None, None),
    "b04.e1": (NAMES, "#nm-sb", "appear", None, None),
    "b04.e2": (NAMES, "#nm-sa", "appear", None, None),
    "b04.e3": (NAMES, "#nm-at", "appear", "Max 5x", None),
    "b04.e4": (NAMES, "#nm-sa", "appear", None, None),
    "b04.e5": (NAMES, "#nm-sb", "appear", None, None),
    "b05.e1": (NAMES, "#nm-u", "appear", None, None),
    "b05.e2": (NAMES, "#nm-a", "change", None, None),
    "b05.e3": (NAMES, "#nm-card", "appear", None, None),
    "b05.e4": (NAMES, "#nm-u", "appear", None, None),
    "b05.e5": (NAMES, "#nm-u", "change", None, None),
    "b06.e1": (WEEK, "#wk-pl-p", "change", None, None),
    "b06.e2": (WEEK, "#wk-card", "appear", None, None),
    "b06.e3": (WEEK, "#wk-pl-p", "change", None, None),
    "b07.e1": (WEEK, "#wk-m", "appear", None, None),
    "b07.e2": (WEEK, "#wk-pl", "present", None, None),
    "b07.e3": (WEEK, "#wk-m", "appear", None, None),
    "b07.e4": ("hud.seat1", "#plugs .plug:nth-child(2)", "appear", None, None),
    "b08.e1": (ULTRA, "#ul-o", "appear", None, None),
    "b08.e2": (ULTRA, "#ul-card", "appear", None, None),
    "b08.e3": (ULTRA, "#ul-o", "appear", None, None),
    "b09.e1": (ULTRA, "#ul-c2", "appear", None, None),
    "b09.e2": (ULTRA, "#ul-c2", "appear", None, None),
    "b09.e3": (ULTRA, "#ul-c3", "appear", None, None),
    "b09.e4": (ULTRA, "#ul-m", "appear", None, None),
    "b10.e1": (Q10, "#q10-o", "appear", None, None),
    "b10.e2": (Q10, "#q10-pl", "appear", None, None),
    "b10.e4": (Q10, "#q10-o", "appear", None, None),
    "b11.e1": (CODEX, "#cx-m1", "appear", None, None),
    "b11.e2": (CODEX, "#cx-card", "appear", None, None),
    "b11.e3": (CODEX, "#cx-m0", "appear", None, None),
    "b12.e1": (CODEX, "#cx-s", "appear", "Codex pricing doc, learn.chatgpt.com/docs/pricing", None),
    "b12.e2": (CODEX, "#cx-pl", "present", None, None),
    "b12.e3": (CODEX, "#cx-s", "appear", "Codex pricing doc, learn.chatgpt.com/docs/pricing", None),
    "b13.e1": (Q13, "#q13-b", "appear", None, None),
    "b13.e2": (Q13, "#q13-pa", "appear", None, None),
    "b13.e3": (Q13, "#q13-b", "appear", None, None),
    "b13.e4": (Q13, "#q13-m3", "appear", None, None),
    "b14.e1": (LIST, "#ls-c0", "appear", None, None),
    "b14.e2": (LIST, "#ls-card", "appear", None, None),
    "b14.e3": (LIST, "#ls-r0", "appear", None, None),
    "b15.e1": (LIST, "#ls-c1", "appear", None, None),
    "b15.e2": (LIST, "#ls-r1", "appear", None, None),
    "b16.e1": (LIST, "#ls-c2", "appear", None, None),
    "b16.e2": (LIST, "#ls-r2", "appear", None, None),
    "b17.e1": (MAX20, "#mx-pl", "present", None, None),
    "b17.e2": (MAX20, "#mx-card", "appear", None, None),
    "b17.e3": (MAX20, "#mx-pl-v", "appear", None, None),
    "b17.e4": (MAX20, "#mx-pl", "present", None, None),
    "b18.e1": (FOUR, "#fr-row", "appear", "4x", None),
    "b18.e2": (FOUR, "#fr-card", "appear", None, None),
    "b18.e3": (FOUR, "#fr-row", "appear", "4x", None),
    "b18.e4": (FOUR, "#fr-st", "appear", None, None),
    "b19.e1": (FOUR, "#fr-pl", "present", None, None),
    "b19.e2": (FOUR, "#fr-clc", "appear", None, None),
    "b19.e3": (FOUR, "#fr-pl-v", "appear", None, None),
    "b19.e4": (FOUR, "#fr-pl", "present", None, None),
    "b19.e5": (FOUR, "#fr-pl", "present", None, None),
    "b20.e1": (OVER, "#ov-m0", "appear", None, None),
    "b20.e2": (OVER, "#ov-card", "appear", None, None),
    "b20.e3": (OVER, "#ov-m0", "appear", None, None),
    "b21.e1": (OVER, "#ov-m2", "appear", None, None),
    "b21.e2": (OVER, "#ov-m1", "appear", None, None),
    "b22.e1": (TABLE, "#tb-dbl", "appear", "double", None),
    "b22.e2": (TABLE, "#tb-card", "appear", None, None),
    "b22.e3": (TABLE, "#tb-row", "appear", None, None),
    "b22.e4": (TABLE, "#tb-o0", "appear", None, None),
    "b23.e1": (Q23, "#q23-m0", "appear", None, None),
    "b23.e2": (Q23, "#q23-card", "appear", None, None),
    "b24.e1": (Q24, "#q24-pl", "present", None, 20),
    "b24.e2": (Q24, "#q24-card", "appear", None, 30),
    "b24.e7": (Q24, "#face", "change", None, 69),
    "b25.e1": (Q25, "#q25-tag", "appear", "I'm pretty sure", None),
    "b25.e2": (Q25, "#q25-card", "appear", None, None),
    "b26.e1": (Q26, "#q26-st", "appear", None, 8),
    "b26.e2": (Q26, "#q26-card", "appear", None, None),
    "b27.e1": (Q27, "#q27-pl-p", "change", None, 30),
    "b27.e2": (Q27, "#q27-card", "appear", None, 30),
    "b27.e4": (Q27, "#face", "change", None, 27),
    "b28.e1": (Q28, "#q28-p0", "present", None, None),
    "b28.e2": (Q28, "#q28-card", "appear", None, None),
    "b29.e1": (CLOSE, "#cl-p0", "present", None, None),
    "b29.e2": (CLOSE, "#cl-card", "appear", None, None),
    "b29.e3": (CLOSE, "#cl-o0", "appear", None, None),
}

POST = {"image": "assets/posts/claude-post-tight-light.png"}
HERO = {"image": "assets/posts/post-hero-cards.png"}
PLANS = {"image": "assets/shots/pricing-plans-light.png"}

# Every line of beats.json copy: (beat, line, owner, target, t, extra). t is a moment the plan says the line is up. extra symbol: a mark, not text.
# extra image: text inside a real capture. The source check sees the image and cannot read it, so that row stays UNVERIFIED.
COPY_BINDS = [
    ("b01", "Max 20x", HOOK, "#hk-pl", 2.1, POST),
    ("b02", "Ultra", HOOK, "#hk-pl", 5.1, POST),
    ("b04", "Max 5x", NAMES, "#nm-at", 9.8),
    ("b04", "Max 20x", NAMES, "#nm-bt", 9.8),
    ("b05", "Max", NAMES, "#nm-m", 11.4, HERO),
    ("b05", "Ultra", NAMES, "#nm-u", 11.4, HERO),
    ("b06", "Weekly limits remain unchanged.", WEEK, "#wk-pl", 13.3, POST),
    ("b07", "Weekly limits remain unchanged.", WEEK, "#wk-pl", 14.5, POST),
    ("b08", "Ultra", ULTRA, "#ul-pl", 15.6, PLANS),
    ("b09", "verified accounts", ULTRA, "#ul-p3", 18.3, {"image": "assets/shots/pricing-footnote-light.png"}),
    ("b10", "The estimates below show local messages per five-hour", Q10, "#q10-pl", 21.2, {"image": "assets/shots/codex-pricing-light.png"}),
    ("b11", "Pro plans", CODEX, "#cx-pl", 22.3, {"image": "assets/shots/codex-pricing-light.png"}),
    ("b11", "currently have no five-hour limit.", CODEX, "#cx-pl", 22.3, {"image": "assets/shots/codex-pricing-light.png"}),
    ("b12", "Codex pricing doc, learn.chatgpt.com/docs/pricing", CODEX, "#cx-s", 24.2),
    ("b13", "Codex pricing doc", Q13, "#q13-la", 27.2),
    ("b13", "Claude Code help page", Q13, "#q13-lb", 27.2),
    ("b13", "Pro plans", Q13, "#q13-pa", 27.2, {"image": "assets/shots/codex-pricing-light.png"}),
    ("b13", "currently have no five-hour limit.", Q13, "#q13-pa", 27.2, {"image": "assets/shots/codex-pricing-light.png"}),
    ("b13", "verified Ultra accounts don't have a five-hour session limit.", Q13, "#q13-pb", 27.2, {"image": "assets/shots/claude-code-support.png"}),
    ("b14", "We’re also removing the 5-hour limit for verified Ultra accounts, starting today with most existing subscribers.", LIST, "#ls-r0", 28.8, POST),
    ("b15", "Weekly limits remain unchanged.", LIST, "#ls-r1", 30.1, POST),
    ("b16", "Max 20x → Ultra", LIST, "#ls-r2", 31.2, POST),
    ("b18", "Max 20x", FOUR, "#fr-pa", 34.5),
    ("b18", "÷", FOUR, "#fr-dv", 34.5),
    ("b18", "Max 5x", FOUR, "#fr-pb", 34.5),
    ("b18", "=", FOUR, "#fr-row", 34.5),
    ("b18", "4x", FOUR, "#fr-row", 34.5),
    ("b18", "THE ASSUMED MATH", FOUR, "#fr-l", 34.5),
    ("b18", "From the plan names, not a usage figure", FOUR, "#fr-s", 34.5),
    ("b20", "It gave you 20x Pro's limit", OVER, "#ov-pl", 38.5, {"image": "assets/posts/overell-post-tight-light.png"}),
    ("b21", "a single limit: 5 hours.", OVER, "#ov-pl", 39.8, {"image": "assets/posts/overell-post-tight-light.png"}),
    ("b22", "double", TABLE, "#tb-dbl", 42.5),
    ("b22", "Weekly limit, claude.com/pricing", TABLE, "#tb-s", 42.5),
    ("b23", "I get that some new users assumed 20x applied to both limits.", Q23, "#q23-pl", 44.1, {'image': 'assets/posts/overell-post-tight-light.png'}),
    ("b23", "We could have done better here, and I'm sorry.", Q23, "#q23-pl", 44.1, {'image': 'assets/posts/overell-post-tight-light.png'}),
    ("b24", "Max 20x → Ultra", Q24, "#q24-pl", 46.5, {'image': 'assets/clips/rename-line-highlight.mp4'}),
    ("b25", "What changed from Max 20x?", Q25, "#q25-pl", 49.3, {'image': 'assets/shots/ultra-support.png'}),
    ("b25", "The Max 20x plan is now called the Ultra plan.", Q25, "#q25-pl", 49.3, {'image': 'assets/shots/ultra-support.png'}),
    ("b25", "Existing Max 20x subscribers move to Ultra automatically, with no price change.", Q25, "#q25-pl", 49.3, {'image': 'assets/shots/ultra-support.png'}),
    ("b25", "I'm pretty sure", Q25, "#q25-tag", 49.3),
    ("b26", "THE ASSUMED MATH", Q26, "#q26-l", 52.0),
    ("b26", "4x", Q26, "#q26-fig", 52.0),
    ("b27", "Free", Q27, "#q27-pl", 52.2, {'image': 'assets/posts/post-hero-cards.png'}),
    ("b27", "Pro", Q27, "#q27-pl", 52.2, {'image': 'assets/posts/post-hero-cards.png'}),
    ("b27", "Max", Q27, "#q27-pl", 52.2, {'image': 'assets/posts/post-hero-cards.png'}),
    ("b27", "Ultra", Q27, "#q27-pl", 52.2, {'image': 'assets/posts/post-hero-cards.png'}),
    ("b27", "No 5-hour limit, verified", Q27, "#q27-verified", 54.6),
    ("b28", "Max", Q28, "#q28-p0", 56.0, {'image': 'assets/shots/pricing-plans-light.png'}),
    ("b28", "Ultra", Q28, "#q28-p1", 56.0, {'image': 'assets/shots/pricing-plans-light.png'}),
    ("b28", "Claude Code included", Q28, "#q28-p0", 56.0, {'image': 'assets/shots/pricing-plans-light.png'}),
    ("b29", "Max", CLOSE, "#cl-p0", 57.5, PLANS),
    ("b29", "Ultra", CLOSE, "#cl-p1", 57.5, PLANS),
    ("b29", "Claude Code included", CLOSE, "#cl-p0", 57.5, PLANS),
]
