"""Ownership tables for this project: scene windows, HUD rows, chains, extra roots and binds. CONTRACT.md section 3.

Declarations only. tools/beat_render/ownership.py reads the generated page for frames and hashes, and anything not declared here is shell, which touches everything.
tools/beat_check/events.py turns the binds at the end of this file into events.json. Row shapes and examples: templates/ivory/build_kit/README.md.
"""

# Scene windows: ["#<scene root>", start, end] in seconds, in order. A scene can hold several windows. Any change here is timing: everything, plus a new media plan.
WINDOWS = []

# Names in assets/logos/ this page uses as <symbol id="logo-<name>">.
LOGOS = []

# HUD states in the order they play, each ["<name>", t]: "strip" first, then "seat0" up to "seat4", and "ring0" up to "ring4" to flash a socket. Empty means no strip.
HUD = []
HUD_LABEL = ""
HUD_PLUGS = []  # one [symbol id, "ic" or "mk"] per seat row
HUD_BINDS = {}  # HUD row name to the node it changes. Plugs and rings have no id, so they are named by place: "#plugs .plug:nth-child(1)"

# The strip stays on screen and each state builds on the last. No resets are declared here, so each link runs to the last frame.
CHAINS = [{"id": "hud",
           "objects": ["#strip", "#strip-pop", "#socks", "#plugs", "#rings", "#count", "#dot-on"],
           "carries": ["opacity", "scale", "y", "display", "color"],
           "links": ["hud." + name for name, _ in HUD],
           "resets": []}] if HUD else []

# A scene that animates a node outside its own root names it here, and then reaches the last frame. Bottom-half punch-in recipe and cost: build_kit/README.md.
EXTRA_ROOTS = {}

# Stills reach the page only through an src or url() in the generated page, so one the page does not name is not in the picture.
LIBRARY = ["assets/stills/", "assets/shots/", "assets/held/", "assets/scenes/", "assets/posts/", "assets/clips/", "assets/logos/"]

# Shell helpers a confined block may call: name to the arguments it needs before it has a time. Each writes only through tl to the selector it is given,
# so the owner audit sees what it does. A block calling anything else goes back in the shell, which touches everything. Never list $, el or own here.
BLOCK_HELPERS = {"A": 1, "show": 2, "hide": 2, "pop": 2, "popFirst": 2, "slotPop": 2, "rise": 2, "cutIn": 2, "on": 2, "off": 2, "drawRect": 2, "drawPath": 2, "word": 2}

# What each plan event must do in the page. An event with no row here is UNVERIFIED in the source check, never skipped and never PASS.
# event_id: (owner, target, expect, copy, hold_frames, lead_frames). expect is appear, change or present. hold_frames None takes the default in events.py. lead_frames names a designed lead.
# The target is the thing the plan says happens on the word, not whichever element happens to tween then. A clip's own content cannot be measured,
# so a beat whose anchor sits inside a clip binds its plate as present.
EVENT_BINDS = {}

# Every line of beats.json copy: (beat, line, owner, target, t, extra). t is a moment the plan says the line is up. extra symbol: a mark, not text.
# extra image: text inside a real capture. The source check sees the image and cannot read it, so that row stays UNVERIFIED.
COPY_BINDS = []
