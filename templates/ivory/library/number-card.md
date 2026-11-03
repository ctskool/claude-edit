# number-card

Proven: 1 approved video(s). Variants: 2.

Use the closest variant and adapt it to the new beat. Slots use literal {{NAME}} substitution, never str.format: Python f-string braces and JS objects must survive.

Fill every slot in both snippets with the same value. ID prefixes end in '-'. Escape copy for its surrounding Python string and for HTML. Slots are authoring source fragments, not executable input. The examples reconstruct the approved source.

The Python scene statement belongs in scenes.py build(); any def helpers shown belong before its use. It depends on the ivory build-kit imports/helpers and the project's CSS. Compare custom helpers and CSS with the linked approved source. Namespace local variables/helpers if needed. Do not import or run the donor project.

Retiming is required: every timeline position and clip start/duration below is an example in donor seconds. Replace with the new plan's numeric times, retain A(t) alignment, and remeasure asset crops, geometry and highlight boxes. Copy no donor fact or figure without facts.json.

Add WINDOWS, EVENT_BINDS and COPY_BINDS in owners.py for the new scene and stable plan event_ids. Inspect EXTRA_ROOTS in the donor owners.py for external targets and their render cost. Rebuild from the kit and run the owner/source checks; these snippets alone are not a ready composition.

## Variant 1: sc-four

Used in 1030-2, beats b18, b19.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: number card, built: equation pills + serif figure + strike (STYLE Strike / X); struck equation + plateCard with his clip

For: '4X' is the one figure the line turns on. No higher row fits: no real plate shows 4x, and ASSETS.md rules that out on purpose. Form: built graphic, arithmetic from the two plan names, labelled as the assumed math and struck so it never reads as a usage figure. 'Max 5X' is what he drags over on screen. real_shot would repeat the post card, and his action is the demo here. Form: real capture, his own recording, 1x, played from its first frame with local time = composition - 34.633, so the drag starts on 'Max' 35.54.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-four",32.967,36.617]].


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-four | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | fr- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | clips/drag-select-max5x.mp4 | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |
| ASSET_2 | held/drag-select-max5x-first.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |
| COPY_1 | Max 20x | Exact verified display copy; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS. |
| COPY_2 | Max 5x | Exact verified display copy; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS. |
| COPY_3 | THE ASSUMED MATH | Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS. |
| COPY_4 | ÷ | Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS. |
| COPY_5 | = | Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS. |
| COPY_6 | 4x | Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS. |
| COPY_7 | From the plan names, not a usage figure | Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS. |

Python template:

```python
def eqpill(id_, x, text):
        return f'<div id="{id_}" class="pillw" style="left:{x}px;top:470px;width:340px;height:120px;border-radius:18px;font-size:60px">{text}</div>'

S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene full">
  <div id="{{ID_PREFIX_1}}c" class="fill">
    {card("{{ID_PREFIX_1}}card", (72, 360, 936, 740))}
    <div id="{{ID_PREFIX_1}}l" class="t" style="left:72px;top:405px;width:936px;text-align:center;font-family:var(--mono);font-weight:500;font-size:30px;letter-spacing:.14em;color:var(--mut)">{{COPY_3}}</div>
    {eqpill("{{ID_PREFIX_1}}pa", 130, "{{COPY_1}}")}
    <div id="{{ID_PREFIX_1}}dv" class="t" style="left:470px;top:482px;width:140px;text-align:center;font-family:var(--serif);font-weight:500;font-size:96px">{{COPY_4}}</div>
    {eqpill("{{ID_PREFIX_1}}pb", 610, "{{COPY_2}}")}
    <div id="{{ID_PREFIX_1}}row" class="abs" style="left:72px;top:640px;width:936px;height:260px;display:flex;justify-content:center;align-items:baseline;gap:40px;font-family:var(--serif);font-weight:500;line-height:1;color:var(--ink);opacity:0">
      <span id="{{ID_PREFIX_1}}eq" style="position:relative;top:-34px;font-size:200px">{{COPY_5}}</span>
      <span id="{{ID_PREFIX_1}}fig" class="stw" style="font-size:260px;letter-spacing:-.02em">{{COPY_6}}<i id="{{ID_PREFIX_1}}st" class="sk" style="left:-24px;right:-24px;top:107px;height:8px"></i></span>
    </div>
    <div id="{{ID_PREFIX_1}}s" class="src" style="left:72px;top:990px;width:936px;text-align:center;font-size:28px">{{COPY_7}}</div>
  </div>
  <div id="{{ID_PREFIX_1}}cg" class="fill" style="opacity:0">
    {card("{{ID_PREFIX_1}}clc", (72, 690, 936, 467))}
    {vplate("{{ID_PREFIX_1}}pl", [("{{ID_PREFIX_1}}h", "{{ASSET_2}}", "")], "{{ASSET_1}}", (0, 0, 960, 460), (90, 708, 900, 431), 34.633, 1.984, 0)}
  </div>
</div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b18-b19 the assumed math struck, then his drag
pop("#{{ID_PREFIX_1}}row", 33.86);
tl.fromTo("#{{ID_PREFIX_1}}st", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.25, ease: "power2.out", immediateRender: false }, 34.3);
tl.to("#{{ID_PREFIX_1}}c", { scale: 0.72, y: -230, transformOrigin: "540px 360px", duration: 0.3, ease: "power3.out" }, 34.567);
show("#{{ID_PREFIX_1}}cg", 34.567);
cutIn("#{{ID_PREFIX_1}}cg", 34.567, 0, "50% 50%");
```

## Variant 2: sc-q26

Used in 1030-2, beats b26.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: White ivory card with the sc-four serif 4x callback and THE ASSUMED MATH label; clay strike on wasn't; chip on the seam

For: Chase's note: replace the caption panel with the large assumed 4x from sc-four and strike it on wasn't. The figure is an assumption, never weekly usage or lawsuit evidence.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-q26",49.433,52.067]].


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-q26 | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | q26- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| COPY_1 | THE ASSUMED MATH | Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS. |
| COPY_2 | 4x | Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS. |

Python template:

```python
S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene">
  {card("{{ID_PREFIX_1}}card", (72, 200, 936, 510))}
  <div id="{{ID_PREFIX_1}}l" class="t" style="left:72px;top:245px;width:936px;text-align:center;font-family:var(--mono);font-weight:500;font-size:30px;letter-spacing:.14em;color:var(--mut)">{{COPY_1}}</div>
  <div id="{{ID_PREFIX_1}}row" class="abs" style="left:72px;top:345px;width:936px;height:260px;display:flex;justify-content:center;align-items:baseline;font-family:var(--serif);font-weight:500;line-height:1;color:var(--ink)">
    <span id="{{ID_PREFIX_1}}fig" class="stw" style="font-size:260px;letter-spacing:-.02em">{{COPY_2}}<i id="{{ID_PREFIX_1}}st" class="sk" style="left:-24px;right:-24px;top:107px;height:8px"></i></span>
  </div>
</div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b26 the assumed 4x returns; strike starts on wasn't
tl.fromTo("#{{ID_PREFIX_1}}st", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.2, ease: "power2.out", immediateRender: false }, A(51.78));
```

<!-- LIBRARY_DATA
{
  "schema": 1,
  "name": "number-card",
  "variants": [
    {
      "family": "number-card",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-four",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b18",
        "b19"
      ],
      "components": [
        "number card, built: equation pills + serif figure + strike (STYLE Strike / X)",
        "struck equation + plateCard with his clip"
      ],
      "purpose": [
        "'4X' is the one figure the line turns on. No higher row fits: no real plate shows 4x, and ASSETS.md rules that out on purpose. Form: built graphic, arithmetic from the two plan names, labelled as the assumed math and struck so it never reads as a usage figure.",
        "'Max 5X' is what he drags over on screen. real_shot would repeat the post card, and his action is the demo here. Form: real capture, his own recording, 1x, played from its first frame with local time = composition - 34.633, so the drag starts on 'Max' 35.54."
      ],
      "windows": [
        [
          "#sc-four",
          32.967,
          36.617
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-50-at-34.7s.png",
      "python": "def eqpill(id_, x, text):\n        return f'<div id=\"{id_}\" class=\"pillw\" style=\"left:{x}px;top:470px;width:340px;height:120px;border-radius:18px;font-size:60px\">{text}</div>'\n\nS.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene full\">\n  <div id=\"{{ID_PREFIX_1}}c\" class=\"fill\">\n    {card(\"{{ID_PREFIX_1}}card\", (72, 360, 936, 740))}\n    <div id=\"{{ID_PREFIX_1}}l\" class=\"t\" style=\"left:72px;top:405px;width:936px;text-align:center;font-family:var(--mono);font-weight:500;font-size:30px;letter-spacing:.14em;color:var(--mut)\">{{COPY_3}}</div>\n    {eqpill(\"{{ID_PREFIX_1}}pa\", 130, \"{{COPY_1}}\")}\n    <div id=\"{{ID_PREFIX_1}}dv\" class=\"t\" style=\"left:470px;top:482px;width:140px;text-align:center;font-family:var(--serif);font-weight:500;font-size:96px\">{{COPY_4}}</div>\n    {eqpill(\"{{ID_PREFIX_1}}pb\", 610, \"{{COPY_2}}\")}\n    <div id=\"{{ID_PREFIX_1}}row\" class=\"abs\" style=\"left:72px;top:640px;width:936px;height:260px;display:flex;justify-content:center;align-items:baseline;gap:40px;font-family:var(--serif);font-weight:500;line-height:1;color:var(--ink);opacity:0\">\n      <span id=\"{{ID_PREFIX_1}}eq\" style=\"position:relative;top:-34px;font-size:200px\">{{COPY_5}}</span>\n      <span id=\"{{ID_PREFIX_1}}fig\" class=\"stw\" style=\"font-size:260px;letter-spacing:-.02em\">{{COPY_6}}<i id=\"{{ID_PREFIX_1}}st\" class=\"sk\" style=\"left:-24px;right:-24px;top:107px;height:8px\"></i></span>\n    </div>\n    <div id=\"{{ID_PREFIX_1}}s\" class=\"src\" style=\"left:72px;top:990px;width:936px;text-align:center;font-size:28px\">{{COPY_7}}</div>\n  </div>\n  <div id=\"{{ID_PREFIX_1}}cg\" class=\"fill\" style=\"opacity:0\">\n    {card(\"{{ID_PREFIX_1}}clc\", (72, 690, 936, 467))}\n    {vplate(\"{{ID_PREFIX_1}}pl\", [(\"{{ID_PREFIX_1}}h\", \"{{ASSET_2}}\", \"\")], \"{{ASSET_1}}\", (0, 0, 960, 460), (90, 708, 900, 431), 34.633, 1.984, 0)}\n  </div>\n</div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b18-b19 the assumed math struck, then his drag\npop(\"#{{ID_PREFIX_1}}row\", 33.86);\ntl.fromTo(\"#{{ID_PREFIX_1}}st\", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.25, ease: \"power2.out\", immediateRender: false }, 34.3);\ntl.to(\"#{{ID_PREFIX_1}}c\", { scale: 0.72, y: -230, transformOrigin: \"540px 360px\", duration: 0.3, ease: \"power3.out\" }, 34.567);\nshow(\"#{{ID_PREFIX_1}}cg\", 34.567);\ncutIn(\"#{{ID_PREFIX_1}}cg\", 34.567, 0, \"50% 50%\");",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-four",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "fr-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "ASSET_1": {
          "kind": "asset",
          "example": "clips/drag-select-max5x.mp4",
          "fill": "Asset path relative to assets/; use real media and remeasure crop/box coordinates."
        },
        "ASSET_2": {
          "kind": "asset",
          "example": "held/drag-select-max5x-first.png",
          "fill": "Asset path relative to assets/; use real media and remeasure crop/box coordinates."
        },
        "COPY_1": {
          "kind": "copy",
          "example": "Max 20x",
          "fill": "Exact verified display copy; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS."
        },
        "COPY_2": {
          "kind": "copy",
          "example": "Max 5x",
          "fill": "Exact verified display copy; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS."
        },
        "COPY_3": {
          "kind": "copy",
          "example": "THE ASSUMED MATH",
          "fill": "Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS."
        },
        "COPY_4": {
          "kind": "copy",
          "example": "÷",
          "fill": "Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS."
        },
        "COPY_5": {
          "kind": "copy",
          "example": "=",
          "fill": "Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS."
        },
        "COPY_6": {
          "kind": "copy",
          "example": "4x",
          "fill": "Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS."
        },
        "COPY_7": {
          "kind": "copy",
          "example": "From the plan names, not a usage figure",
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
      "family": "number-card",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-q26",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b26"
      ],
      "components": [
        "White ivory card with the sc-four serif 4x callback and THE ASSUMED MATH label; clay strike on wasn't; chip on the seam"
      ],
      "purpose": [
        "Chase's note: replace the caption panel with the large assumed 4x from sc-four and strike it on wasn't. The figure is an assumption, never weekly usage or lawsuit evidence."
      ],
      "windows": [
        [
          "#sc-q26",
          49.433,
          52.067
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-72-at-50.05s.png",
      "python": "S.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene\">\n  {card(\"{{ID_PREFIX_1}}card\", (72, 200, 936, 510))}\n  <div id=\"{{ID_PREFIX_1}}l\" class=\"t\" style=\"left:72px;top:245px;width:936px;text-align:center;font-family:var(--mono);font-weight:500;font-size:30px;letter-spacing:.14em;color:var(--mut)\">{{COPY_1}}</div>\n  <div id=\"{{ID_PREFIX_1}}row\" class=\"abs\" style=\"left:72px;top:345px;width:936px;height:260px;display:flex;justify-content:center;align-items:baseline;font-family:var(--serif);font-weight:500;line-height:1;color:var(--ink)\">\n    <span id=\"{{ID_PREFIX_1}}fig\" class=\"stw\" style=\"font-size:260px;letter-spacing:-.02em\">{{COPY_2}}<i id=\"{{ID_PREFIX_1}}st\" class=\"sk\" style=\"left:-24px;right:-24px;top:107px;height:8px\"></i></span>\n  </div>\n</div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b26 the assumed 4x returns; strike starts on wasn't\ntl.fromTo(\"#{{ID_PREFIX_1}}st\", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.2, ease: \"power2.out\", immediateRender: false }, A(51.78));",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-q26",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "q26-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "COPY_1": {
          "kind": "copy",
          "example": "THE ASSUMED MATH",
          "fill": "Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS."
        },
        "COPY_2": {
          "kind": "copy",
          "example": "4x",
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
    }
  ]
}
LIBRARY_DATA -->
