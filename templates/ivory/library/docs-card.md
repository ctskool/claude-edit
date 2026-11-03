# docs-card

Proven: 1 approved video(s). Variants: 3.

Use the closest variant and adapt it to the new beat. Slots use literal {{NAME}} substitution, never str.format: Python f-string braces and JS objects must survive.

Fill every slot in both snippets with the same value. ID prefixes end in '-'. Escape copy for its surrounding Python string and for HTML. Slots are authoring source fragments, not executable input. The examples reconstruct the approved source.

The Python scene statement belongs in scenes.py build(); any def helpers shown belong before its use. It depends on the ivory build-kit imports/helpers and the project's CSS. Compare custom helpers and CSS with the linked approved source. Namespace local variables/helpers if needed. Do not import or run the donor project.

Retiming is required: every timeline position and clip start/duration below is an example in donor seconds. Replace with the new plan's numeric times, retain A(t) alignment, and remeasure asset crops, geometry and highlight boxes. Copy no donor fact or figure without facts.json.

Add WINDOWS, EVENT_BINDS and COPY_BINDS in owners.py for the new scene and stable plan event_ids. Inspect EXTRA_ROOTS in the donor owners.py for external targets and their render cost. Rebuild from the kit and run the owner/source checks; these snippets alone are not a ready composition.

## Variant 1: sc-q10

Used in 1030-2, beats b10.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: White ivory card with the real Codex doc, same box as b11; clay outline on 'better'; chip on the seam

For: Chase's note: replace the last repeating text panel. OpenAI's doc arrives early so the Codex side is on screen as he names it. The line stays his opinion: no winner is lit, and the doc only speaks to limits in b11-b12.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-q10",18.367,21.267]].


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-q10 | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | q10- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | shots/codex-pricing-light.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |

Python template:

```python
CB = (90, 218, 900, 399)

S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene"><div id="{{ID_PREFIX_1}}g" class="fill">
  {card("{{ID_PREFIX_1}}card", (72, 200, 936, 435))}
  {plate("{{ID_PREFIX_1}}pl", "{{ASSET_1}}", (0, 0, 812, 360), CB, "w")}
  {drawn("{{ID_PREFIX_1}}o", (72, 200, 936, 435), 22)}
</div></div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b10 quiet panel, his opinion
tl.fromTo("#{{ID_PREFIX_1}}g", { scale: 1, transformOrigin: "50% 50%" }, { scale: 1.01508, duration: 2.9, ease: "none", immediateRender: false }, A(18.367));
drawRect("#{{ID_PREFIX_1}}o", 19.76, 0.3);
off("#{{ID_PREFIX_1}}o", 21.0, 0.2);
```

## Variant 2: sc-codex

Used in 1030-2, beats b11, b12.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: plateCard, whole docs paragraph, two-part marker; same card, mono source label in type (no Codex mark exists)

For: 'no limits' points at a specific public doc line. Top row. Form: real capture of OpenAI's page in the white card, whole paragraph at about 35 px. Connective clause of the same doc line, so no new visual. 'Codex side' names the source. Form: real capture.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-codex",21.267,24.3]].


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-codex | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | cx- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | shots/codex-pricing-light.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |
| COPY_1 | Codex pricing doc, learn.chatgpt.com/docs/pricing | Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS. |

Python template:

```python
def inpin(box, tx, ty, s, f):
    """A frame-px box at rest, as a box inside a pin pushed by (tx, ty, s) with origin 0 0"""
    return [round((f[0] - box[0] - tx) / s, 2), round((f[1] - box[1] - ty) / s, 2), round(f[2] / s, 2), round(f[3] / s, 2)]

def mark(id_, b, cls="mkr", extra=""):
    """A marker tint or a strike line. Starts hidden, wipes on from the left"""
    return f'<div id="{id_}" class="{cls}" style="{boxstyle(b)};{extra}"></div>'

CB = (90, 218, 900, 399)

S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene"><div id="{{ID_PREFIX_1}}g" class="fill">
  {card("{{ID_PREFIX_1}}card", (72, 200, 936, 435))}
  {plate("{{ID_PREFIX_1}}pl", "{{ASSET_1}}", (0, 0, 812, 360), CB, "w", extra=mark("{{ID_PREFIX_1}}m0", inpin(CB, 0, 0, 1, (706.3, 284.5, 151.8, 42.1)), extra="border-radius:6px") + mark("{{ID_PREFIX_1}}m1", inpin(CB, 0, 0, 1, (90.0, 342.1, 512.1, 42.1)), extra="border-radius:6px"))}
  <div id="{{ID_PREFIX_1}}s" class="src" style="left:72px;top:655px;width:936px;text-align:center;font-size:26px;opacity:0">{{COPY_1}}</div>
</div></div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b11-b12 the whole paragraph, both marker parts on one frame, source line on Codex
tl.fromTo("#{{ID_PREFIX_1}}g", { scale: 1.01508, transformOrigin: "50% 50%" }, { scale: 1.03085, duration: 3.033, ease: "none", immediateRender: false }, A(21.267));
tl.fromTo(["#{{ID_PREFIX_1}}m0", "#{{ID_PREFIX_1}}m1"], { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 21.44);
rise("#{{ID_PREFIX_1}}s", 22.56, 12, 0.2);
```

## Variant 3: sc-q25

Used in 1030-2, beats b25.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: White ivory card with the real support-page rename section and highlight; small hedge tag on sure; chip on the seam

For: Chase's note: replace the repeating text panel with the support page's rename facts and a small hedge tag. The capture provides no evidence for his lawsuit opinion.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-q25",46.7,49.433]].


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-q25 | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | q25- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | shots/ultra-support.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |
| COPY_1 | I'm pretty sure | Exact verified display copy; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS. |

Python template:

```python
def inpin(box, tx, ty, s, f):
    """A frame-px box at rest, as a box inside a pin pushed by (tx, ty, s) with origin 0 0"""
    return [round((f[0] - box[0] - tx) / s, 2), round((f[1] - box[1] - ty) / s, 2), round(f[2] / s, 2), round(f[3] / s, 2)]

def mark(id_, b, cls="mkr", extra=""):
    """A marker tint or a strike line. Starts hidden, wipes on from the left"""
    return f'<div id="{id_}" class="{cls}" style="{boxstyle(b)};{extra}"></div>'

SB = (90, 240, 900, 194)

SR = (0, 0, 1392, 300)

S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene">
  {card("{{ID_PREFIX_1}}card", (72, 222, 936, 373))}
  {plate("{{ID_PREFIX_1}}pl", "{{ASSET_1}}", SR, SB, "w", extra=mark("{{ID_PREFIX_1}}m", inpin(SB, 0, 0, 1, map_box(SR, SB, (24, 158, 956, 58)))))}
  {lbl("{{ID_PREFIX_1}}tag", 116, 512, "{{COPY_1}}", 34, "padding:14px 18px;background:#f6e3da;border-radius:10px;opacity:0")}
</div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b25 rename facts only; a small hedge tag on sure
show("#{{ID_PREFIX_1}}m", 46.7);
word("#{{ID_PREFIX_1}}tag", 47.62);
```

<!-- LIBRARY_DATA
{
  "schema": 1,
  "name": "docs-card",
  "variants": [
    {
      "family": "docs-card",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-q10",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b10"
      ],
      "components": [
        "White ivory card with the real Codex doc, same box as b11; clay outline on 'better'; chip on the seam"
      ],
      "purpose": [
        "Chase's note: replace the last repeating text panel. OpenAI's doc arrives early so the Codex side is on screen as he names it. The line stays his opinion: no winner is lit, and the doc only speaks to limits in b11-b12."
      ],
      "windows": [
        [
          "#sc-q10",
          18.367,
          21.267
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-32-at-19.8s.png",
      "python": "CB = (90, 218, 900, 399)\n\nS.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene\"><div id=\"{{ID_PREFIX_1}}g\" class=\"fill\">\n  {card(\"{{ID_PREFIX_1}}card\", (72, 200, 936, 435))}\n  {plate(\"{{ID_PREFIX_1}}pl\", \"{{ASSET_1}}\", (0, 0, 812, 360), CB, \"w\")}\n  {drawn(\"{{ID_PREFIX_1}}o\", (72, 200, 936, 435), 22)}\n</div></div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b10 quiet panel, his opinion\ntl.fromTo(\"#{{ID_PREFIX_1}}g\", { scale: 1, transformOrigin: \"50% 50%\" }, { scale: 1.01508, duration: 2.9, ease: \"none\", immediateRender: false }, A(18.367));\ndrawRect(\"#{{ID_PREFIX_1}}o\", 19.76, 0.3);\noff(\"#{{ID_PREFIX_1}}o\", 21.0, 0.2);",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-q10",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "q10-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "ASSET_1": {
          "kind": "asset",
          "example": "shots/codex-pricing-light.png",
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
      "family": "docs-card",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-codex",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b11",
        "b12"
      ],
      "components": [
        "plateCard, whole docs paragraph, two-part marker",
        "same card, mono source label in type (no Codex mark exists)"
      ],
      "purpose": [
        "'no limits' points at a specific public doc line. Top row. Form: real capture of OpenAI's page in the white card, whole paragraph at about 35 px.",
        "Connective clause of the same doc line, so no new visual. 'Codex side' names the source. Form: real capture."
      ],
      "windows": [
        [
          "#sc-codex",
          21.267,
          24.3
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-35-at-22.6s.png",
      "python": "def inpin(box, tx, ty, s, f):\n    \"\"\"A frame-px box at rest, as a box inside a pin pushed by (tx, ty, s) with origin 0 0\"\"\"\n    return [round((f[0] - box[0] - tx) / s, 2), round((f[1] - box[1] - ty) / s, 2), round(f[2] / s, 2), round(f[3] / s, 2)]\n\ndef mark(id_, b, cls=\"mkr\", extra=\"\"):\n    \"\"\"A marker tint or a strike line. Starts hidden, wipes on from the left\"\"\"\n    return f'<div id=\"{id_}\" class=\"{cls}\" style=\"{boxstyle(b)};{extra}\"></div>'\n\nCB = (90, 218, 900, 399)\n\nS.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene\"><div id=\"{{ID_PREFIX_1}}g\" class=\"fill\">\n  {card(\"{{ID_PREFIX_1}}card\", (72, 200, 936, 435))}\n  {plate(\"{{ID_PREFIX_1}}pl\", \"{{ASSET_1}}\", (0, 0, 812, 360), CB, \"w\", extra=mark(\"{{ID_PREFIX_1}}m0\", inpin(CB, 0, 0, 1, (706.3, 284.5, 151.8, 42.1)), extra=\"border-radius:6px\") + mark(\"{{ID_PREFIX_1}}m1\", inpin(CB, 0, 0, 1, (90.0, 342.1, 512.1, 42.1)), extra=\"border-radius:6px\"))}\n  <div id=\"{{ID_PREFIX_1}}s\" class=\"src\" style=\"left:72px;top:655px;width:936px;text-align:center;font-size:26px;opacity:0\">{{COPY_1}}</div>\n</div></div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b11-b12 the whole paragraph, both marker parts on one frame, source line on Codex\ntl.fromTo(\"#{{ID_PREFIX_1}}g\", { scale: 1.01508, transformOrigin: \"50% 50%\" }, { scale: 1.03085, duration: 3.033, ease: \"none\", immediateRender: false }, A(21.267));\ntl.fromTo([\"#{{ID_PREFIX_1}}m0\", \"#{{ID_PREFIX_1}}m1\"], { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: \"power2.out\", immediateRender: false }, 21.44);\nrise(\"#{{ID_PREFIX_1}}s\", 22.56, 12, 0.2);",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-codex",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "cx-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "ASSET_1": {
          "kind": "asset",
          "example": "shots/codex-pricing-light.png",
          "fill": "Asset path relative to assets/; use real media and remeasure crop/box coordinates."
        },
        "COPY_1": {
          "kind": "copy",
          "example": "Codex pricing doc, learn.chatgpt.com/docs/pricing",
          "fill": "Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS."
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
      "family": "docs-card",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-q25",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b25"
      ],
      "components": [
        "White ivory card with the real support-page rename section and highlight; small hedge tag on sure; chip on the seam"
      ],
      "purpose": [
        "Chase's note: replace the repeating text panel with the support page's rename facts and a small hedge tag. The capture provides no evidence for his lawsuit opinion."
      ],
      "windows": [
        [
          "#sc-q25",
          46.7,
          49.433
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-70-at-47.65s.png",
      "python": "def inpin(box, tx, ty, s, f):\n    \"\"\"A frame-px box at rest, as a box inside a pin pushed by (tx, ty, s) with origin 0 0\"\"\"\n    return [round((f[0] - box[0] - tx) / s, 2), round((f[1] - box[1] - ty) / s, 2), round(f[2] / s, 2), round(f[3] / s, 2)]\n\ndef mark(id_, b, cls=\"mkr\", extra=\"\"):\n    \"\"\"A marker tint or a strike line. Starts hidden, wipes on from the left\"\"\"\n    return f'<div id=\"{id_}\" class=\"{cls}\" style=\"{boxstyle(b)};{extra}\"></div>'\n\nSB = (90, 240, 900, 194)\n\nSR = (0, 0, 1392, 300)\n\nS.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene\">\n  {card(\"{{ID_PREFIX_1}}card\", (72, 222, 936, 373))}\n  {plate(\"{{ID_PREFIX_1}}pl\", \"{{ASSET_1}}\", SR, SB, \"w\", extra=mark(\"{{ID_PREFIX_1}}m\", inpin(SB, 0, 0, 1, map_box(SR, SB, (24, 158, 956, 58)))))}\n  {lbl(\"{{ID_PREFIX_1}}tag\", 116, 512, \"{{COPY_1}}\", 34, \"padding:14px 18px;background:#f6e3da;border-radius:10px;opacity:0\")}\n</div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b25 rename facts only; a small hedge tag on sure\nshow(\"#{{ID_PREFIX_1}}m\", 46.7);\nword(\"#{{ID_PREFIX_1}}tag\", 47.62);",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-q25",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "q25-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "ASSET_1": {
          "kind": "asset",
          "example": "shots/ultra-support.png",
          "fill": "Asset path relative to assets/; use real media and remeasure crop/box coordinates."
        },
        "COPY_1": {
          "kind": "copy",
          "example": "I'm pretty sure",
          "fill": "Exact verified display copy; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS."
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
