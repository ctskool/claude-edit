# post-card

Proven: 1 approved video(s). Variants: 4.

Use the closest variant and adapt it to the new beat. Slots use literal {{NAME}} substitution, never str.format: Python f-string braces and JS objects must survive.

Fill every slot in both snippets with the same value. ID prefixes end in '-'. Escape copy for its surrounding Python string and for HTML. Slots are authoring source fragments, not executable input. The examples reconstruct the approved source.

The Python scene statement belongs in scenes.py build(); any def helpers shown belong before its use. It depends on the ivory build-kit imports/helpers and the project's CSS. Compare custom helpers and CSS with the linked approved source. Namespace local variables/helpers if needed. Do not import or run the donor project.

Retiming is required: every timeline position and clip start/duration below is an example in donor seconds. Replace with the new plan's numeric times, retain A(t) alignment, and remeasure asset crops, geometry and highlight boxes. Copy no donor fact or figure without facts.json.

Add WINDOWS, EVENT_BINDS and COPY_BINDS in owners.py for the new scene and stable plan event_ids. Inspect EXTRA_ROOTS in the donor owners.py for external targets and their render cost. Rebuild from the kit and run the owner/source checks; these snippets alone are not a ready composition.

## Variant 1: sc-hook

Used in 1030-2, beats b01, b02.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: post card plate (STYLE Card + plate()), rebuilt @claudeai post, strike line (STYLE Strike / X); same post card continues: arrow tint, 'Ultra' tint

For: Hook choice 1, visual hook: 'the Max 20X plan' names a specific plan and the post that retires it exists, so the card fills the panel. Top row, so no lower row applies; a proof hook or lockup would come after it. Form: rebuilt card (post_card.py), not his dark recording, because it reads better on ivory and is the same text. 'the Ultra plan' names the same post row, so the hook card keeps going instead of a new device. Form: rebuilt card.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-hook",0,5.167]].


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-hook | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | hk- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | posts/claude-post-tight-light.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |

Python template:

```python
def inpin(box, tx, ty, s, f):
    """A frame-px box at rest, as a box inside a pin pushed by (tx, ty, s) with origin 0 0"""
    return [round((f[0] - box[0] - tx) / s, 2), round((f[1] - box[1] - ty) / s, 2), round(f[2] / s, 2), round(f[3] / s, 2)]

def mark(id_, b, cls="mkr", extra=""):
    """A marker tint or a strike line. Starts hidden, wipes on from the left"""
    return f'<div id="{id_}" class="{cls}" style="{boxstyle(b)};{extra}"></div>'

POST = "{{ASSET_1}}"

HB = (90, 286, 900, 337)

HP = (-36, -468.67, 2.3)

hk = (mark("{{ID_PREFIX_1}}s", inpin(HB, *HP, (121.5, 505.5, 297.0, 6.0)), "sk") + mark("{{ID_PREFIX_1}}a", inpin(HB, *HP, (427.5, 470.2, 69.8, 76.4)), extra="border-radius:2.6px")
          + mark("{{ID_PREFIX_1}}u", inpin(HB, *HP, (513.0, 465.7, 168.8, 85.4)), extra="border-radius:2.6px"))

S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene">
  {card("{{ID_PREFIX_1}}card", (72, 268, 936, 372))}
  {plate("{{ID_PREFIX_1}}pl", POST, (0, 0, 920, 344), HB, "o0 w", extra=hk)}
</div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b01-b02 hook. Slow push about the window centre, then one straight push, pin only, then the slow push about the centre again
tl.fromTo("#{{ID_PREFIX_1}}pl-p", { scale: 1, x: 0, y: 0 }, { scale: 1.01, x: -4.5, y: -1.685, duration: 0.32, ease: "none" }, 0);
tl.to("#{{ID_PREFIX_1}}pl-p", { scale: 2.3, x: -36, y: -468.67, duration: 0.6, ease: "power2.inOut" }, 0.32);
tl.fromTo("#{{ID_PREFIX_1}}s", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 1.76);
tl.to("#{{ID_PREFIX_1}}pl-p", { scale: 2.33549, x: -43.5, y: -478.5, duration: 2.967, ease: "none" }, 2.2);
tl.fromTo("#{{ID_PREFIX_1}}a", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 2.8);
tl.fromTo("#{{ID_PREFIX_1}}u", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 4.24);
```

## Variant 2: sc-week

Used in 1030-2, beats b06, b07.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: same post card rebuilt on its lower strip (STYLE Card + plate()); same card, marker over the post's own sentence, HUD seat

For: 'the actual limits' points at the post's limit line, a specific post that exists. Form: rebuilt card. The same card returns because a later visual of something shown is built from it. 'haven't changed at all' is the post's own line 'Weekly limits remain unchanged.', quoted verbatim in the shape it lives in. Form: rebuilt card.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-week",11.5,14.567]].


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-week | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | wk- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | posts/claude-post-tight-light.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |

Python template:

```python
def inpin(box, tx, ty, s, f):
    """A frame-px box at rest, as a box inside a pin pushed by (tx, ty, s) with origin 0 0"""
    return [round((f[0] - box[0] - tx) / s, 2), round((f[1] - box[1] - ty) / s, 2), round(f[2] / s, 2), round(f[3] / s, 2)]

def mark(id_, b, cls="mkr", extra=""):
    """A marker tint or a strike line. Starts hidden, wipes on from the left"""
    return f'<div id="{id_}" class="{cls}" style="{boxstyle(b)};{extra}"></div>'

POST = "{{ASSET_1}}"

WB = (90, 377, 900, 137)

WP = (-28.02, -28.02, 1.7899)

S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene"><div id="{{ID_PREFIX_1}}g" class="fill">
  {card("{{ID_PREFIX_1}}card", (72, 359, 936, 173))}
  {plate("{{ID_PREFIX_1}}pl", POST, (0, 760, 920, 140), WB, "o0 w", extra=mark("{{ID_PREFIX_1}}m", inpin(WB, *WP, (112.8, 429.6, 873.7, 73.6)), extra="border-radius:3.35px"))}
</div></div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b06-b07 the post card returns on its lower strip, one straight push, then the marker
cutIn("#{{ID_PREFIX_1}}g", 11.5, 0);
tl.to("#{{ID_PREFIX_1}}pl-p", { scale: 1.7899, x: -28.02, y: -28.02, duration: 0.5, ease: "power2.inOut" }, 12.64);
tl.fromTo("#{{ID_PREFIX_1}}m", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 14.16);
```

## Variant 3: sc-over

Used in 1030-2, beats b20, b21.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: post card plate, rebuilt @mboverell post, marker; same card, second marker

For: 'it gave you 20X usage' is what this post says word for word, and it exists. Top row. Form: rebuilt card (post_card.py), about 33 px at 900 wide. 'five-hour limit' is the same post's line 'it had a single limit: 5 hours.', so the card extends. Form: rebuilt card.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-over",36.617,39.95]].


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-over | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | ov- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | posts/overell-post-tight-light.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |

Python template:

```python
def inpin(box, tx, ty, s, f):
    """A frame-px box at rest, as a box inside a pin pushed by (tx, ty, s) with origin 0 0"""
    return [round((f[0] - box[0] - tx) / s, 2), round((f[1] - box[1] - ty) / s, 2), round(f[2] / s, 2), round(f[3] / s, 2)]

def mark(id_, b, cls="mkr", extra=""):
    """A marker tint or a strike line. Starts hidden, wipes on from the left"""
    return f'<div id="{id_}" class="{cls}" style="{boxstyle(b)};{extra}"></div>'

OVER = "{{ASSET_1}}"

OB = (90, 168, 900, 513)

def okm(id_, f):
        return mark(id_, inpin(OB, 0, 0, 1, f), extra="border-radius:6px")

S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene"><div id="{{ID_PREFIX_1}}g" class="fill">
  {card("{{ID_PREFIX_1}}card", (72, 150, 936, 549))}
  {plate("{{ID_PREFIX_1}}pl", OVER, (0, 0, 920, 524), OB, "w", extra=okm("{{ID_PREFIX_1}}m0", (422.6, 498.9, 376.6, 41.1)) + okm("{{ID_PREFIX_1}}m1", (893.2, 451.9, 21.5, 41.1)) + okm("{{ID_PREFIX_1}}m2", (119.3, 498.9, 296.4, 41.1)))}
</div></div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b20-b21 Overell post, two markers. The second phrase wraps, so its two parts share a frame
cutIn("#{{ID_PREFIX_1}}g", 36.617, 0);
tl.fromTo("#{{ID_PREFIX_1}}pl-p", { scale: 1, transformOrigin: "50% 50%" }, { scale: 1.01733, duration: 3.333, ease: "none", immediateRender: false }, 36.617);
tl.fromTo("#{{ID_PREFIX_1}}m0", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 37.86);
tl.fromTo(["#{{ID_PREFIX_1}}m1", "#{{ID_PREFIX_1}}m2"], { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 38.9);
```

## Variant 4: sc-q23

Used in 1030-2, beats b23.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: White ivory card with a tight Overell post crop; two-part clay highlight on the admission; chip on the seam

For: Chase's note: replace the repeating caption panel with Overell's admission, pushed in for phone reading and highlighted on pissed. No reaction count.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-q23",42.567,44.183]].


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-q23 | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | q23- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | posts/overell-post-tight-light.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |

Python template:

```python
def inpin(box, tx, ty, s, f):
    """A frame-px box at rest, as a box inside a pin pushed by (tx, ty, s) with origin 0 0"""
    return [round((f[0] - box[0] - tx) / s, 2), round((f[1] - box[1] - ty) / s, 2), round(f[2] / s, 2), round(f[3] / s, 2)]

def mark(id_, b, cls="mkr", extra=""):
    """A marker tint or a strike line. Starts hidden, wipes on from the left"""
    return f'<div id="{id_}" class="{cls}" style="{boxstyle(b)};{extra}"></div>'

OVER = "{{ASSET_1}}"

QB = (90, 318, 900, 144)

QR = (16, 548, 880, 140.8)

S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene">
  {card("{{ID_PREFIX_1}}card", (72, 300, 936, 180))}
  {plate("{{ID_PREFIX_1}}pl", OVER, QR, QB, "w", extra=mark("{{ID_PREFIX_1}}m0", inpin(QB, 0, 0, 1, map_box(QR, QB, (32, 566, 830, 45)))) + mark("{{ID_PREFIX_1}}m1", inpin(QB, 0, 0, 1, map_box(QR, QB, (32, 613, 88, 45)))))}
</div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b23 Overell's admission; the marker lands on pissed
tl.fromTo(["#{{ID_PREFIX_1}}m0", "#{{ID_PREFIX_1}}m1"], { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.2, ease: "power2.out", immediateRender: false }, A(43.62));
```

<!-- LIBRARY_DATA
{
  "schema": 1,
  "name": "post-card",
  "variants": [
    {
      "family": "post-card",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-hook",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b01",
        "b02"
      ],
      "components": [
        "post card plate (STYLE Card + plate()), rebuilt @claudeai post, strike line (STYLE Strike / X)",
        "same post card continues: arrow tint, 'Ultra' tint"
      ],
      "purpose": [
        "Hook choice 1, visual hook: 'the Max 20X plan' names a specific plan and the post that retires it exists, so the card fills the panel. Top row, so no lower row applies; a proof hook or lockup would come after it. Form: rebuilt card (post_card.py), not his dark recording, because it reads better on ivory and is the same text.",
        "'the Ultra plan' names the same post row, so the hook card keeps going instead of a new device. Form: rebuilt card."
      ],
      "windows": [
        [
          "#sc-hook",
          0,
          5.167
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-04-at-2.9s.png",
      "python": "def inpin(box, tx, ty, s, f):\n    \"\"\"A frame-px box at rest, as a box inside a pin pushed by (tx, ty, s) with origin 0 0\"\"\"\n    return [round((f[0] - box[0] - tx) / s, 2), round((f[1] - box[1] - ty) / s, 2), round(f[2] / s, 2), round(f[3] / s, 2)]\n\ndef mark(id_, b, cls=\"mkr\", extra=\"\"):\n    \"\"\"A marker tint or a strike line. Starts hidden, wipes on from the left\"\"\"\n    return f'<div id=\"{id_}\" class=\"{cls}\" style=\"{boxstyle(b)};{extra}\"></div>'\n\nPOST = \"{{ASSET_1}}\"\n\nHB = (90, 286, 900, 337)\n\nHP = (-36, -468.67, 2.3)\n\nhk = (mark(\"{{ID_PREFIX_1}}s\", inpin(HB, *HP, (121.5, 505.5, 297.0, 6.0)), \"sk\") + mark(\"{{ID_PREFIX_1}}a\", inpin(HB, *HP, (427.5, 470.2, 69.8, 76.4)), extra=\"border-radius:2.6px\")\n          + mark(\"{{ID_PREFIX_1}}u\", inpin(HB, *HP, (513.0, 465.7, 168.8, 85.4)), extra=\"border-radius:2.6px\"))\n\nS.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene\">\n  {card(\"{{ID_PREFIX_1}}card\", (72, 268, 936, 372))}\n  {plate(\"{{ID_PREFIX_1}}pl\", POST, (0, 0, 920, 344), HB, \"o0 w\", extra=hk)}\n</div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b01-b02 hook. Slow push about the window centre, then one straight push, pin only, then the slow push about the centre again\ntl.fromTo(\"#{{ID_PREFIX_1}}pl-p\", { scale: 1, x: 0, y: 0 }, { scale: 1.01, x: -4.5, y: -1.685, duration: 0.32, ease: \"none\" }, 0);\ntl.to(\"#{{ID_PREFIX_1}}pl-p\", { scale: 2.3, x: -36, y: -468.67, duration: 0.6, ease: \"power2.inOut\" }, 0.32);\ntl.fromTo(\"#{{ID_PREFIX_1}}s\", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: \"power2.out\", immediateRender: false }, 1.76);\ntl.to(\"#{{ID_PREFIX_1}}pl-p\", { scale: 2.33549, x: -43.5, y: -478.5, duration: 2.967, ease: \"none\" }, 2.2);\ntl.fromTo(\"#{{ID_PREFIX_1}}a\", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: \"power2.out\", immediateRender: false }, 2.8);\ntl.fromTo(\"#{{ID_PREFIX_1}}u\", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: \"power2.out\", immediateRender: false }, 4.24);",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-hook",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "hk-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "ASSET_1": {
          "kind": "asset",
          "example": "posts/claude-post-tight-light.png",
          "fill": "Asset path relative to assets/; use real media and remeasure crop/box coordinates."
        }
      },
      "source_sha256": {
        "tools_local/scenes.py": "8b20b237d4a137031c119268ce8584c17be6de38637d2c90024b6df86263722c",
        "tools_local/timeline.js": "84e97597ea4c9312100888d21da2956b94401e60cdfff2e624f31bf3c14cb902",
        "tools_local/owners.py": "9ffa556677bd45f0835358433203da85bd7f3e8335e675a75f3f728be80ec313",
        "plan.json": "69ad69f35d42a5485ed26941f8117ced53bcc88b941e85d0d53474a65b1a90be"
      },
      "owner_notes": []
    },
    {
      "family": "post-card",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-week",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b06",
        "b07"
      ],
      "components": [
        "same post card rebuilt on its lower strip (STYLE Card + plate())",
        "same card, marker over the post's own sentence, HUD seat"
      ],
      "purpose": [
        "'the actual limits' points at the post's limit line, a specific post that exists. Form: rebuilt card. The same card returns because a later visual of something shown is built from it.",
        "'haven't changed at all' is the post's own line 'Weekly limits remain unchanged.', quoted verbatim in the shape it lives in. Form: rebuilt card."
      ],
      "windows": [
        [
          "#sc-week",
          11.5,
          14.567
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-21-at-13.2s.png",
      "python": "def inpin(box, tx, ty, s, f):\n    \"\"\"A frame-px box at rest, as a box inside a pin pushed by (tx, ty, s) with origin 0 0\"\"\"\n    return [round((f[0] - box[0] - tx) / s, 2), round((f[1] - box[1] - ty) / s, 2), round(f[2] / s, 2), round(f[3] / s, 2)]\n\ndef mark(id_, b, cls=\"mkr\", extra=\"\"):\n    \"\"\"A marker tint or a strike line. Starts hidden, wipes on from the left\"\"\"\n    return f'<div id=\"{id_}\" class=\"{cls}\" style=\"{boxstyle(b)};{extra}\"></div>'\n\nPOST = \"{{ASSET_1}}\"\n\nWB = (90, 377, 900, 137)\n\nWP = (-28.02, -28.02, 1.7899)\n\nS.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene\"><div id=\"{{ID_PREFIX_1}}g\" class=\"fill\">\n  {card(\"{{ID_PREFIX_1}}card\", (72, 359, 936, 173))}\n  {plate(\"{{ID_PREFIX_1}}pl\", POST, (0, 760, 920, 140), WB, \"o0 w\", extra=mark(\"{{ID_PREFIX_1}}m\", inpin(WB, *WP, (112.8, 429.6, 873.7, 73.6)), extra=\"border-radius:3.35px\"))}\n</div></div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b06-b07 the post card returns on its lower strip, one straight push, then the marker\ncutIn(\"#{{ID_PREFIX_1}}g\", 11.5, 0);\ntl.to(\"#{{ID_PREFIX_1}}pl-p\", { scale: 1.7899, x: -28.02, y: -28.02, duration: 0.5, ease: \"power2.inOut\" }, 12.64);\ntl.fromTo(\"#{{ID_PREFIX_1}}m\", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: \"power2.out\", immediateRender: false }, 14.16);",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-week",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "wk-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "ASSET_1": {
          "kind": "asset",
          "example": "posts/claude-post-tight-light.png",
          "fill": "Asset path relative to assets/; use real media and remeasure crop/box coordinates."
        }
      },
      "source_sha256": {
        "tools_local/scenes.py": "8b20b237d4a137031c119268ce8584c17be6de38637d2c90024b6df86263722c",
        "tools_local/timeline.js": "84e97597ea4c9312100888d21da2956b94401e60cdfff2e624f31bf3c14cb902",
        "tools_local/owners.py": "9ffa556677bd45f0835358433203da85bd7f3e8335e675a75f3f728be80ec313",
        "plan.json": "69ad69f35d42a5485ed26941f8117ced53bcc88b941e85d0d53474a65b1a90be"
      },
      "owner_notes": []
    },
    {
      "family": "post-card",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-over",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b20",
        "b21"
      ],
      "components": [
        "post card plate, rebuilt @mboverell post, marker",
        "same card, second marker"
      ],
      "purpose": [
        "'it gave you 20X usage' is what this post says word for word, and it exists. Top row. Form: rebuilt card (post_card.py), about 33 px at 900 wide.",
        "'five-hour limit' is the same post's line 'it had a single limit: 5 hours.', so the card extends. Form: rebuilt card."
      ],
      "windows": [
        [
          "#sc-over",
          36.617,
          39.95
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-55-at-37.9s.png",
      "python": "def inpin(box, tx, ty, s, f):\n    \"\"\"A frame-px box at rest, as a box inside a pin pushed by (tx, ty, s) with origin 0 0\"\"\"\n    return [round((f[0] - box[0] - tx) / s, 2), round((f[1] - box[1] - ty) / s, 2), round(f[2] / s, 2), round(f[3] / s, 2)]\n\ndef mark(id_, b, cls=\"mkr\", extra=\"\"):\n    \"\"\"A marker tint or a strike line. Starts hidden, wipes on from the left\"\"\"\n    return f'<div id=\"{id_}\" class=\"{cls}\" style=\"{boxstyle(b)};{extra}\"></div>'\n\nOVER = \"{{ASSET_1}}\"\n\nOB = (90, 168, 900, 513)\n\ndef okm(id_, f):\n        return mark(id_, inpin(OB, 0, 0, 1, f), extra=\"border-radius:6px\")\n\nS.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene\"><div id=\"{{ID_PREFIX_1}}g\" class=\"fill\">\n  {card(\"{{ID_PREFIX_1}}card\", (72, 150, 936, 549))}\n  {plate(\"{{ID_PREFIX_1}}pl\", OVER, (0, 0, 920, 524), OB, \"w\", extra=okm(\"{{ID_PREFIX_1}}m0\", (422.6, 498.9, 376.6, 41.1)) + okm(\"{{ID_PREFIX_1}}m1\", (893.2, 451.9, 21.5, 41.1)) + okm(\"{{ID_PREFIX_1}}m2\", (119.3, 498.9, 296.4, 41.1)))}\n</div></div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b20-b21 Overell post, two markers. The second phrase wraps, so its two parts share a frame\ncutIn(\"#{{ID_PREFIX_1}}g\", 36.617, 0);\ntl.fromTo(\"#{{ID_PREFIX_1}}pl-p\", { scale: 1, transformOrigin: \"50% 50%\" }, { scale: 1.01733, duration: 3.333, ease: \"none\", immediateRender: false }, 36.617);\ntl.fromTo(\"#{{ID_PREFIX_1}}m0\", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: \"power2.out\", immediateRender: false }, 37.86);\ntl.fromTo([\"#{{ID_PREFIX_1}}m1\", \"#{{ID_PREFIX_1}}m2\"], { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: \"power2.out\", immediateRender: false }, 38.9);",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-over",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "ov-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "ASSET_1": {
          "kind": "asset",
          "example": "posts/overell-post-tight-light.png",
          "fill": "Asset path relative to assets/; use real media and remeasure crop/box coordinates."
        }
      },
      "source_sha256": {
        "tools_local/scenes.py": "8b20b237d4a137031c119268ce8584c17be6de38637d2c90024b6df86263722c",
        "tools_local/timeline.js": "84e97597ea4c9312100888d21da2956b94401e60cdfff2e624f31bf3c14cb902",
        "tools_local/owners.py": "9ffa556677bd45f0835358433203da85bd7f3e8335e675a75f3f728be80ec313",
        "plan.json": "69ad69f35d42a5485ed26941f8117ced53bcc88b941e85d0d53474a65b1a90be"
      },
      "owner_notes": []
    },
    {
      "family": "post-card",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-q23",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b23"
      ],
      "components": [
        "White ivory card with a tight Overell post crop; two-part clay highlight on the admission; chip on the seam"
      ],
      "purpose": [
        "Chase's note: replace the repeating caption panel with Overell's admission, pushed in for phone reading and highlighted on pissed. No reaction count."
      ],
      "windows": [
        [
          "#sc-q23",
          42.567,
          44.183
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-63-at-43.2s.png",
      "python": "def inpin(box, tx, ty, s, f):\n    \"\"\"A frame-px box at rest, as a box inside a pin pushed by (tx, ty, s) with origin 0 0\"\"\"\n    return [round((f[0] - box[0] - tx) / s, 2), round((f[1] - box[1] - ty) / s, 2), round(f[2] / s, 2), round(f[3] / s, 2)]\n\ndef mark(id_, b, cls=\"mkr\", extra=\"\"):\n    \"\"\"A marker tint or a strike line. Starts hidden, wipes on from the left\"\"\"\n    return f'<div id=\"{id_}\" class=\"{cls}\" style=\"{boxstyle(b)};{extra}\"></div>'\n\nOVER = \"{{ASSET_1}}\"\n\nQB = (90, 318, 900, 144)\n\nQR = (16, 548, 880, 140.8)\n\nS.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene\">\n  {card(\"{{ID_PREFIX_1}}card\", (72, 300, 936, 180))}\n  {plate(\"{{ID_PREFIX_1}}pl\", OVER, QR, QB, \"w\", extra=mark(\"{{ID_PREFIX_1}}m0\", inpin(QB, 0, 0, 1, map_box(QR, QB, (32, 566, 830, 45)))) + mark(\"{{ID_PREFIX_1}}m1\", inpin(QB, 0, 0, 1, map_box(QR, QB, (32, 613, 88, 45)))))}\n</div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b23 Overell's admission; the marker lands on pissed\ntl.fromTo([\"#{{ID_PREFIX_1}}m0\", \"#{{ID_PREFIX_1}}m1\"], { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.2, ease: \"power2.out\", immediateRender: false }, A(43.62));",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-q23",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "q23-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "ASSET_1": {
          "kind": "asset",
          "example": "posts/overell-post-tight-light.png",
          "fill": "Asset path relative to assets/; use real media and remeasure crop/box coordinates."
        }
      },
      "source_sha256": {
        "tools_local/scenes.py": "8b20b237d4a137031c119268ce8584c17be6de38637d2c90024b6df86263722c",
        "tools_local/timeline.js": "84e97597ea4c9312100888d21da2956b94401e60cdfff2e624f31bf3c14cb902",
        "tools_local/owners.py": "9ffa556677bd45f0835358433203da85bd7f3e8335e675a75f3f728be80ec313",
        "plan.json": "69ad69f35d42a5485ed26941f8117ced53bcc88b941e85d0d53474a65b1a90be"
      },
      "owner_notes": []
    }
  ]
}
LIBRARY_DATA -->
