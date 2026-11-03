# clip-card

Proven: 1 approved video(s). Variants: 3.

Use the closest variant and adapt it to the new beat. Slots use literal {{NAME}} substitution, never str.format: Python f-string braces and JS objects must survive.

Fill every slot in both snippets with the same value. ID prefixes end in '-'. Escape copy for its surrounding Python string and for HTML. Slots are authoring source fragments, not executable input. The examples reconstruct the approved source.

The Python scene statement belongs in scenes.py build(); any def helpers shown belong before its use. It depends on the ivory build-kit imports/helpers and the project's CSS. Compare custom helpers and CSS with the linked approved source. Namespace local variables/helpers if needed. Do not import or run the donor project.

Retiming is required: every timeline position and clip start/duration below is an example in donor seconds. Replace with the new plan's numeric times, retain A(t) alignment, and remeasure asset crops, geometry and highlight boxes. Copy no donor fact or figure without facts.json.

Add WINDOWS, EVENT_BINDS and COPY_BINDS in owners.py for the new scene and stable plan event_ids. Inspect EXTRA_ROOTS in the donor owners.py for external targets and their render cost. Rebuild from the kit and run the owner/source checks; these snippets alone are not a ready composition.

## Variant 1: sc-title

Used in 1030-2, beats b03.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: plateCard with his clip, vplate stills for the held first frame, HUD strip pop-in

For: 'renamed both of their plans' describes what he highlights on screen as he says it. real_shot does not fit first: the line names no post or page, it describes the rename he is marking. Form: real capture, his own recording. Local time = composition - 5.30, first frame held 0.133 s, 1x, no join in range.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-title",5.167,7.5]].


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-title | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | ti- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | clips/title-highlight.mp4 | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |
| ASSET_2 | held/title-highlight-first.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |

Python template:

```python
S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene"><div id="{{ID_PREFIX_1}}g" class="fill">
  {card("{{ID_PREFIX_1}}card", (72, 212, 936, 467))}
  {vplate("{{ID_PREFIX_1}}pl", [("{{ID_PREFIX_1}}h", "{{ASSET_2}}", "")], "{{ASSET_1}}", (0, 0, 960, 460), (90, 230, 900, 431), 5.30, 2.2, 0)}
</div></div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b03 his recording, first frame held 0.133 s
cutIn("#{{ID_PREFIX_1}}g", 5.167, 0);
```

## Variant 2: sc-max20

Used in 1030-2, beats b17.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: plateCard with his clip, vplate stills for the held first frame

For: 'Max 20X' is what he selects on screen at this line. His selection is the real action, the post card already carried the name. Form: real capture, his own recording. First frame held 0.10 s from 31.30, then local time = composition - 31.40, so the clip runs local 0-1.567, 0.40 s behind real time.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-max20",31.3,32.967]].


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-max20 | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | mx- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | clips/max20x-highlight.mp4 | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |
| ASSET_2 | held/max20x-highlight-first.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |

Python template:

```python
S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene"><div id="{{ID_PREFIX_1}}g" class="fill">
  {card("{{ID_PREFIX_1}}card", (72, 212, 936, 467))}
  {vplate("{{ID_PREFIX_1}}pl", [("{{ID_PREFIX_1}}h", "{{ASSET_2}}", "")], "{{ASSET_1}}", (0, 0, 960, 460), (90, 230, 900, 431), 31.40, 1.567, 0)}
</div></div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b17 his selection, first frame held 0.10 s
cutIn("#{{ID_PREFIX_1}}g", 31.3, 0);
```

## Variant 3: sc-q24

Used in 1030-2, beats b24.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: White ivory card framing his own muted rename selection clip; chip on the seam

For: Chase's note: replace the caption panel with his real rename selection. This shows the rename only; it does not prove his claimed cause.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-q24",44.183,46.7]].

External ownership: EXTRA_ROOTS = {"scene.sc-q24": ["#face"], "scene.sc-q27": ["#face"]}


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-q24 | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | q24- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | clips/rename-line-highlight.mp4 | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |

Python template:

```python
S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene">
  {card("{{ID_PREFIX_1}}card", (72, 212, 936, 467))}
  {vplate("{{ID_PREFIX_1}}pl", [], "{{ASSET_1}}", (0, 0, 960, 460), (90, 230, 900, 431), 44.183, 2.517, 0)}
</div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b24 his rename selection, within its 2.666667 s source
tl.set("#face", { scale: 1.08, transformOrigin: "50% 8%" }, A(44.183));
tl.to("#face", { scale: 1, duration: 0.16, ease: "power2.out" }, 46.5);
tl.set("#face", { scale: 1 }, A(46.667));
```

<!-- LIBRARY_DATA
{
  "schema": 1,
  "name": "clip-card",
  "variants": [
    {
      "family": "clip-card",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-title",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b03"
      ],
      "components": [
        "plateCard with his clip, vplate stills for the held first frame, HUD strip pop-in"
      ],
      "purpose": [
        "'renamed both of their plans' describes what he highlights on screen as he says it. real_shot does not fit first: the line names no post or page, it describes the rename he is marking. Form: real capture, his own recording. Local time = composition - 5.30, first frame held 0.133 s, 1x, no join in range."
      ],
      "windows": [
        [
          "#sc-title",
          5.167,
          7.5
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-09-at-6.4s.png",
      "python": "S.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene\"><div id=\"{{ID_PREFIX_1}}g\" class=\"fill\">\n  {card(\"{{ID_PREFIX_1}}card\", (72, 212, 936, 467))}\n  {vplate(\"{{ID_PREFIX_1}}pl\", [(\"{{ID_PREFIX_1}}h\", \"{{ASSET_2}}\", \"\")], \"{{ASSET_1}}\", (0, 0, 960, 460), (90, 230, 900, 431), 5.30, 2.2, 0)}\n</div></div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b03 his recording, first frame held 0.133 s\ncutIn(\"#{{ID_PREFIX_1}}g\", 5.167, 0);",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-title",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "ti-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "ASSET_1": {
          "kind": "asset",
          "example": "clips/title-highlight.mp4",
          "fill": "Asset path relative to assets/; use real media and remeasure crop/box coordinates."
        },
        "ASSET_2": {
          "kind": "asset",
          "example": "held/title-highlight-first.png",
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
      "family": "clip-card",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-max20",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b17"
      ],
      "components": [
        "plateCard with his clip, vplate stills for the held first frame"
      ],
      "purpose": [
        "'Max 20X' is what he selects on screen at this line. His selection is the real action, the post card already carried the name. Form: real capture, his own recording. First frame held 0.10 s from 31.30, then local time = composition - 31.40, so the clip runs local 0-1.567, 0.40 s behind real time."
      ],
      "windows": [
        [
          "#sc-max20",
          31.3,
          32.967
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-45-at-31.8s.png",
      "python": "S.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene\"><div id=\"{{ID_PREFIX_1}}g\" class=\"fill\">\n  {card(\"{{ID_PREFIX_1}}card\", (72, 212, 936, 467))}\n  {vplate(\"{{ID_PREFIX_1}}pl\", [(\"{{ID_PREFIX_1}}h\", \"{{ASSET_2}}\", \"\")], \"{{ASSET_1}}\", (0, 0, 960, 460), (90, 230, 900, 431), 31.40, 1.567, 0)}\n</div></div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b17 his selection, first frame held 0.10 s\ncutIn(\"#{{ID_PREFIX_1}}g\", 31.3, 0);",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-max20",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "mx-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "ASSET_1": {
          "kind": "asset",
          "example": "clips/max20x-highlight.mp4",
          "fill": "Asset path relative to assets/; use real media and remeasure crop/box coordinates."
        },
        "ASSET_2": {
          "kind": "asset",
          "example": "held/max20x-highlight-first.png",
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
      "family": "clip-card",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-q24",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b24"
      ],
      "components": [
        "White ivory card framing his own muted rename selection clip; chip on the seam"
      ],
      "purpose": [
        "Chase's note: replace the caption panel with his real rename selection. This shows the rename only; it does not prove his claimed cause."
      ],
      "windows": [
        [
          "#sc-q24",
          44.183,
          46.7
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-67-at-45.65s.png",
      "python": "S.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene\">\n  {card(\"{{ID_PREFIX_1}}card\", (72, 212, 936, 467))}\n  {vplate(\"{{ID_PREFIX_1}}pl\", [], \"{{ASSET_1}}\", (0, 0, 960, 460), (90, 230, 900, 431), 44.183, 2.517, 0)}\n</div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b24 his rename selection, within its 2.666667 s source\ntl.set(\"#face\", { scale: 1.08, transformOrigin: \"50% 8%\" }, A(44.183));\ntl.to(\"#face\", { scale: 1, duration: 0.16, ease: \"power2.out\" }, 46.5);\ntl.set(\"#face\", { scale: 1 }, A(46.667));",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-q24",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "q24-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "ASSET_1": {
          "kind": "asset",
          "example": "clips/rename-line-highlight.mp4",
          "fill": "Asset path relative to assets/; use real media and remeasure crop/box coordinates."
        }
      },
      "source_sha256": {
        "tools_local/scenes.py": "8b20b237d4a137031c119268ce8584c17be6de38637d2c90024b6df86263722c",
        "tools_local/timeline.js": "84e97597ea4c9312100888d21da2956b94401e60cdfff2e624f31bf3c14cb902",
        "tools_local/owners.py": "9ffa556677bd45f0835358433203da85bd7f3e8335e675a75f3f728be80ec313",
        "plan.json": "69ad69f35d42a5485ed26941f8117ced53bcc88b941e85d0d53474a65b1a90be"
      },
      "owner_notes": [
        "EXTRA_ROOTS = {\"scene.sc-q24\": [\"#face\"], \"scene.sc-q27\": [\"#face\"]}"
      ]
    }
  ]
}
LIBRARY_DATA -->
