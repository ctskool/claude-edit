# list-card

Proven: 1 approved video(s). Variants: 1.

Use the closest variant and adapt it to the new beat. Slots use literal {{NAME}} substitution, never str.format: Python f-string braces and JS objects must survive.

Fill every slot in both snippets with the same value. ID prefixes end in '-'. Escape copy for its surrounding Python string and for HTML. Slots are authoring source fragments, not executable input. The examples reconstruct the approved source.

The Python scene statement belongs in scenes.py build(); any def helpers shown belong before its use. It depends on the ivory build-kit imports/helpers and the project's CSS. Compare custom helpers and CSS with the linked approved source. Namespace local variables/helpers if needed. Do not import or run the donor project.

Retiming is required: every timeline position and clip start/duration below is an example in donor seconds. Replace with the new plan's numeric times, retain A(t) alignment, and remeasure asset crops, geometry and highlight boxes. Copy no donor fact or figure without facts.json.

Add WINDOWS, EVENT_BINDS and COPY_BINDS in owners.py for the new scene and stable plan event_ids. Inspect EXTRA_ROOTS in the donor owners.py for external targets and their render cost. Rebuild from the kit and run the owner/source checks; these snippets alone are not a ready composition.

## Variant 1: sc-list

Used in 1030-2, beats b14, b15, b16.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: list card: socket + check + real post crop per row; same list card, row 2; same list card, row 3

For: 'no more five-hour limits, same weekly limits, and no more confusion' names 3 items in a row, and that is what the line turns on, so the list row wins over the product name. Form: rebuilt card crops carried over from the post card, each with a check. 'same weekly limits' is list item 2 of 3, on its own beat. Form: rebuilt card crop, same as b07's line. 'no more confusion' is list item 3 of 3. The post's row 'Max 20x → Ultra' is the concrete thing that clears it, and 'because Max 20X' picks it up on the next line. Form: rebuilt card crop, one whole row, a marked verbatim excerpt of the post's two rename rows.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-list",27.3,31.3]].


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-list | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | ls- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | posts/claude-post-tight-light.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |

Python template:

```python
POST = "{{ASSET_1}}"

def row(i, y, rect, box):
        return (f'<div class="lsock" style="left:102px;top:{y - 42}px"></div>'
                f'<svg id="{{ID_PREFIX_1}}c{i}" class="abs" viewBox="0 0 84 84" style="left:102px;top:{y - 42}px;width:84px;height:84px;opacity:0"><path d="M23 44 L37 58 L62 28" fill="none" stroke="#2e9e5b" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
                f'<div id="{{ID_PREFIX_1}}b{i}" class="skel" style="left:206px;top:{y - 14}px;width:560px;height:28px"></div>'
                + plate(f"{{ID_PREFIX_1}}r{i}", POST, rect, box, "w", "border-radius:0;opacity:0"))

S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene full">
  {card("{{ID_PREFIX_1}}card", (72, 400, 936, 660))}
  <div class="abs" style="left:102px;top:620px;width:876px;height:1px;background:#e4e2da"></div>
  <div class="abs" style="left:102px;top:840px;width:876px;height:1px;background:#e4e2da"></div>
  {row(0, 510, (28, 524, 832, 92), (206, 466.7, 784.0, 86.7))}
  {row(1, 730, (28, 804, 500, 46), (206, 708.3, 471.2, 43.3))}
  {row(2, 950, (28, 284, 252, 44), (206, 929.3, 237.5, 41.5))}
</div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b14-b16 each recap row lands with its check; the HUD rings on the same words
hide("#{{ID_PREFIX_1}}b0", 27.94);
rise("#{{ID_PREFIX_1}}r0", 27.94, 12, 0.2);
show("#{{ID_PREFIX_1}}c0", 27.94);
tl.fromTo("#{{ID_PREFIX_1}}c0", { scale: 0, transformOrigin: "50% 50%" }, { scale: 1, duration: 0.35, ease: "back.out(2)", immediateRender: false }, A(27.94));
hide("#{{ID_PREFIX_1}}b1", 29.3);
rise("#{{ID_PREFIX_1}}r1", 29.3, 12, 0.2);
show("#{{ID_PREFIX_1}}c1", 29.3);
tl.fromTo("#{{ID_PREFIX_1}}c1", { scale: 0, transformOrigin: "50% 50%" }, { scale: 1, duration: 0.35, ease: "back.out(2)", immediateRender: false }, A(29.3));
hide("#{{ID_PREFIX_1}}b2", 30.58);
rise("#{{ID_PREFIX_1}}r2", 30.58, 12, 0.2);
show("#{{ID_PREFIX_1}}c2", 30.58);
tl.fromTo("#{{ID_PREFIX_1}}c2", { scale: 0, transformOrigin: "50% 50%" }, { scale: 1, duration: 0.35, ease: "back.out(2)", immediateRender: false }, A(30.58));
```

<!-- LIBRARY_DATA
{
  "schema": 1,
  "name": "list-card",
  "variants": [
    {
      "family": "list-card",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-list",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b14",
        "b15",
        "b16"
      ],
      "components": [
        "list card: socket + check + real post crop per row",
        "same list card, row 2",
        "same list card, row 3"
      ],
      "purpose": [
        "'no more five-hour limits, same weekly limits, and no more confusion' names 3 items in a row, and that is what the line turns on, so the list row wins over the product name. Form: rebuilt card crops carried over from the post card, each with a check.",
        "'same weekly limits' is list item 2 of 3, on its own beat. Form: rebuilt card crop, same as b07's line.",
        "'no more confusion' is list item 3 of 3. The post's row 'Max 20x → Ultra' is the concrete thing that clears it, and 'because Max 20X' picks it up on the next line. Form: rebuilt card crop, one whole row, a marked verbatim excerpt of the post's two rename rows."
      ],
      "windows": [
        [
          "#sc-list",
          27.3,
          31.3
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-42-at-29.35s.png",
      "python": "POST = \"{{ASSET_1}}\"\n\ndef row(i, y, rect, box):\n        return (f'<div class=\"lsock\" style=\"left:102px;top:{y - 42}px\"></div>'\n                f'<svg id=\"{{ID_PREFIX_1}}c{i}\" class=\"abs\" viewBox=\"0 0 84 84\" style=\"left:102px;top:{y - 42}px;width:84px;height:84px;opacity:0\"><path d=\"M23 44 L37 58 L62 28\" fill=\"none\" stroke=\"#2e9e5b\" stroke-width=\"5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>'\n                f'<div id=\"{{ID_PREFIX_1}}b{i}\" class=\"skel\" style=\"left:206px;top:{y - 14}px;width:560px;height:28px\"></div>'\n                + plate(f\"{{ID_PREFIX_1}}r{i}\", POST, rect, box, \"w\", \"border-radius:0;opacity:0\"))\n\nS.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene full\">\n  {card(\"{{ID_PREFIX_1}}card\", (72, 400, 936, 660))}\n  <div class=\"abs\" style=\"left:102px;top:620px;width:876px;height:1px;background:#e4e2da\"></div>\n  <div class=\"abs\" style=\"left:102px;top:840px;width:876px;height:1px;background:#e4e2da\"></div>\n  {row(0, 510, (28, 524, 832, 92), (206, 466.7, 784.0, 86.7))}\n  {row(1, 730, (28, 804, 500, 46), (206, 708.3, 471.2, 43.3))}\n  {row(2, 950, (28, 284, 252, 44), (206, 929.3, 237.5, 41.5))}\n</div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b14-b16 each recap row lands with its check; the HUD rings on the same words\nhide(\"#{{ID_PREFIX_1}}b0\", 27.94);\nrise(\"#{{ID_PREFIX_1}}r0\", 27.94, 12, 0.2);\nshow(\"#{{ID_PREFIX_1}}c0\", 27.94);\ntl.fromTo(\"#{{ID_PREFIX_1}}c0\", { scale: 0, transformOrigin: \"50% 50%\" }, { scale: 1, duration: 0.35, ease: \"back.out(2)\", immediateRender: false }, A(27.94));\nhide(\"#{{ID_PREFIX_1}}b1\", 29.3);\nrise(\"#{{ID_PREFIX_1}}r1\", 29.3, 12, 0.2);\nshow(\"#{{ID_PREFIX_1}}c1\", 29.3);\ntl.fromTo(\"#{{ID_PREFIX_1}}c1\", { scale: 0, transformOrigin: \"50% 50%\" }, { scale: 1, duration: 0.35, ease: \"back.out(2)\", immediateRender: false }, A(29.3));\nhide(\"#{{ID_PREFIX_1}}b2\", 30.58);\nrise(\"#{{ID_PREFIX_1}}r2\", 30.58, 12, 0.2);\nshow(\"#{{ID_PREFIX_1}}c2\", 30.58);\ntl.fromTo(\"#{{ID_PREFIX_1}}c2\", { scale: 0, transformOrigin: \"50% 50%\" }, { scale: 1, duration: 0.35, ease: \"back.out(2)\", immediateRender: false }, A(30.58));",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-list",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "ls-",
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
    }
  ]
}
LIBRARY_DATA -->
