# compare-table

Proven: 1 approved video(s). Variants: 1.

Use the closest variant and adapt it to the new beat. Slots use literal {{NAME}} substitution, never str.format: Python f-string braces and JS objects must survive.

Fill every slot in both snippets with the same value. ID prefixes end in '-'. Escape copy for its surrounding Python string and for HTML. Slots are authoring source fragments, not executable input. The examples reconstruct the approved source.

The Python scene statement belongs in scenes.py build(); any def helpers shown belong before its use. It depends on the ivory build-kit imports/helpers and the project's CSS. Compare custom helpers and CSS with the linked approved source. Namespace local variables/helpers if needed. Do not import or run the donor project.

Retiming is required: every timeline position and clip start/duration below is an example in donor seconds. Replace with the new plan's numeric times, retain A(t) alignment, and remeasure asset crops, geometry and highlight boxes. Copy no donor fact or figure without facts.json.

Add WINDOWS, EVENT_BINDS and COPY_BINDS in owners.py for the new scene and stable plan event_ids. Inspect EXTRA_ROOTS in the donor owners.py for external targets and their render cost. Rebuild from the kit and run the owner/source checks; these snippets alone are not a ready composition.

## Variant 1: sc-table

Used in 1030-2, beats b22.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: compare: real table plate + pill outlines + drawn bracket + footnote plate + source line

For: 'only double the 5X plan' sets 5x against 10x, a comparison line taking its row with the real table. 'not for the weekly' is under 1 s, so it rides this beat. Form: real capture of claude.com/pricing, 31-40 px at 900 wide, with the footnote plate because the table shows 'No 5-hour limit‡'.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-table",39.95,42.567]].


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-table | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | tb- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | shots/pricing-compare-light.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |
| ASSET_2 | shots/pricing-footnote-light.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |
| COPY_1 | double | Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS. |
| COPY_2 | Weekly limit, claude.com/pricing | Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS. |

Python template:

```python
FOOT = "{{ASSET_2}}"

S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene full">
  {card("{{ID_PREFIX_1}}card", (72, 292, 936, 793))}
  {plate("{{ID_PREFIX_1}}pl", "{{ASSET_1}}", (0, 0, 1224, 796), (90, 310, 900, 585), "w")}
  <div id="{{ID_PREFIX_1}}row" class="abs" style="left:90px;top:685.3px;width:900px;height:209.7px;background:rgba(217,119,87,.14);border-radius:0 0 12px 12px;transform-origin:0 50%;opacity:0"></div>
  {ol("{{ID_PREFIX_1}}o0", (612.8, 811.1, 79.4, 57.4), "bare")}
  {ol("{{ID_PREFIX_1}}o1", (831.2, 811.1, 90.4, 57.4), "bare")}
  <svg class="abs" style="left:0;top:0;width:1080px;height:1920px;overflow:visible"><path id="{{ID_PREFIX_1}}br" d="M652 874 V914 H876 V874" fill="none" stroke="#d97757" stroke-width="3" stroke-linejoin="round" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1"/></svg>
  <div id="{{ID_PREFIX_1}}dbl" class="t" style="left:564px;top:924px;width:400px;text-align:center;font-family:var(--serif);font-style:italic;font-weight:500;font-size:56px;color:var(--clay);opacity:0">{{COPY_1}}</div>
  {plate("{{ID_PREFIX_1}}fn", FOOT, (0, 0, 1176, 108), (140, 994, 800, 73), "w")}
  <div id="{{ID_PREFIX_1}}s" class="src" style="left:72px;top:1104px;width:936px;text-align:center;font-size:28px">{{COPY_2}}</div>
</div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b22 week row, then 5x and 10x with the bracket
tl.fromTo("#{{ID_PREFIX_1}}row", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 40.34);
on("#{{ID_PREFIX_1}}o0", 41.3, 0.25);
on("#{{ID_PREFIX_1}}o1", 41.3, 0.25);
drawPath("#{{ID_PREFIX_1}}br", 41.3, 0.3, 1);
word("#{{ID_PREFIX_1}}dbl", 41.3);
```

<!-- LIBRARY_DATA
{
  "schema": 1,
  "name": "compare-table",
  "variants": [
    {
      "family": "compare-table",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-table",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b22"
      ],
      "components": [
        "compare: real table plate + pill outlines + drawn bracket + footnote plate + source line"
      ],
      "purpose": [
        "'only double the 5X plan' sets 5x against 10x, a comparison line taking its row with the real table. 'not for the weekly' is under 1 s, so it rides this beat. Form: real capture of claude.com/pricing, 31-40 px at 900 wide, with the footnote plate because the table shows 'No 5-hour limit‡'."
      ],
      "windows": [
        [
          "#sc-table",
          39.95,
          42.567
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-60-at-41.35s.png",
      "python": "FOOT = \"{{ASSET_2}}\"\n\nS.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene full\">\n  {card(\"{{ID_PREFIX_1}}card\", (72, 292, 936, 793))}\n  {plate(\"{{ID_PREFIX_1}}pl\", \"{{ASSET_1}}\", (0, 0, 1224, 796), (90, 310, 900, 585), \"w\")}\n  <div id=\"{{ID_PREFIX_1}}row\" class=\"abs\" style=\"left:90px;top:685.3px;width:900px;height:209.7px;background:rgba(217,119,87,.14);border-radius:0 0 12px 12px;transform-origin:0 50%;opacity:0\"></div>\n  {ol(\"{{ID_PREFIX_1}}o0\", (612.8, 811.1, 79.4, 57.4), \"bare\")}\n  {ol(\"{{ID_PREFIX_1}}o1\", (831.2, 811.1, 90.4, 57.4), \"bare\")}\n  <svg class=\"abs\" style=\"left:0;top:0;width:1080px;height:1920px;overflow:visible\"><path id=\"{{ID_PREFIX_1}}br\" d=\"M652 874 V914 H876 V874\" fill=\"none\" stroke=\"#d97757\" stroke-width=\"3\" stroke-linejoin=\"round\" pathLength=\"1\" stroke-dasharray=\"1 1\" stroke-dashoffset=\"1\"/></svg>\n  <div id=\"{{ID_PREFIX_1}}dbl\" class=\"t\" style=\"left:564px;top:924px;width:400px;text-align:center;font-family:var(--serif);font-style:italic;font-weight:500;font-size:56px;color:var(--clay);opacity:0\">{{COPY_1}}</div>\n  {plate(\"{{ID_PREFIX_1}}fn\", FOOT, (0, 0, 1176, 108), (140, 994, 800, 73), \"w\")}\n  <div id=\"{{ID_PREFIX_1}}s\" class=\"src\" style=\"left:72px;top:1104px;width:936px;text-align:center;font-size:28px\">{{COPY_2}}</div>\n</div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b22 week row, then 5x and 10x with the bracket\ntl.fromTo(\"#{{ID_PREFIX_1}}row\", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: \"power2.out\", immediateRender: false }, 40.34);\non(\"#{{ID_PREFIX_1}}o0\", 41.3, 0.25);\non(\"#{{ID_PREFIX_1}}o1\", 41.3, 0.25);\ndrawPath(\"#{{ID_PREFIX_1}}br\", 41.3, 0.3, 1);\nword(\"#{{ID_PREFIX_1}}dbl\", 41.3);",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-table",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "tb-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "ASSET_1": {
          "kind": "asset",
          "example": "shots/pricing-compare-light.png",
          "fill": "Asset path relative to assets/; use real media and remeasure crop/box coordinates."
        },
        "ASSET_2": {
          "kind": "asset",
          "example": "shots/pricing-footnote-light.png",
          "fill": "Asset path relative to assets/; use real media and remeasure crop/box coordinates."
        },
        "COPY_1": {
          "kind": "copy",
          "example": "double",
          "fill": "Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS."
        },
        "COPY_2": {
          "kind": "copy",
          "example": "Weekly limit, claude.com/pricing",
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
