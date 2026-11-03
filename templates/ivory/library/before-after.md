# before-after

Proven: 1 approved video(s). Variants: 1.

Use the closest variant and adapt it to the new beat. Slots use literal {{NAME}} substitution, never str.format: Python f-string braces and JS objects must survive.

Fill every slot in both snippets with the same value. ID prefixes end in '-'. Escape copy for its surrounding Python string and for HTML. Slots are authoring source fragments, not executable input. The examples reconstruct the approved source.

The Python scene statement belongs in scenes.py build(); any def helpers shown belong before its use. It depends on the ivory build-kit imports/helpers and the project's CSS. Compare custom helpers and CSS with the linked approved source. Namespace local variables/helpers if needed. Do not import or run the donor project.

Retiming is required: every timeline position and clip start/duration below is an example in donor seconds. Replace with the new plan's numeric times, retain A(t) alignment, and remeasure asset crops, geometry and highlight boxes. Copy no donor fact or figure without facts.json.

Add WINDOWS, EVENT_BINDS and COPY_BINDS in owners.py for the new scene and stable plan event_ids. Inspect EXTRA_ROOTS in the donor owners.py for external targets and their render cost. Rebuild from the kit and run the owner/source checks; these snippets alone are not a ready composition.

## Variant 1: sc-names

Used in 1030-2, beats b04, b05.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: compare before-state: two built pills (.pillw) + strike lines carried from b01; compare after-state: pill row + the post's own art in a white card, two windows of one image

For: 'no longer Max 5X and Max 20X' opens a before-after, and a comparison takes its own row even with product names in it, using the real post wording. Form: built pills, words verbatim from the post. 'just Max and Ultra' is the pivot of the same before-after, so it develops b04 and keeps its template. Form: real artifact, the post's own art, names only, no green field as a panel.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-names",7.5,11.5]].


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-names | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | nm- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | posts/post-hero-cards.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |
| COPY_1 | Max 5x | Exact verified display copy; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS. |
| COPY_2 | Max 20x | Exact verified display copy; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS. |

Python template:

```python
HERO = "{{ASSET_1}}"

def pill(id_, y, text, strike):
        return (f'<div id="{id_}" class="pillw" style="left:190px;top:{y}px;width:700px;height:160px;border-radius:22px;font-size:84px">'
                f'<span id="{id_}t" class="stw">{text}<i id="{strike}" class="sk" style="left:-12px;right:-12px;top:42px;height:6px"></i></span></div>')

S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene full">
  {pill("{{ID_PREFIX_1}}a", 530, "{{COPY_1}}", "{{ID_PREFIX_1}}sa")}
  {pill("{{ID_PREFIX_1}}b", 750, "{{COPY_2}}", "{{ID_PREFIX_1}}sb")}
  <div id="{{ID_PREFIX_1}}art" class="fill" style="opacity:0">
    {card("{{ID_PREFIX_1}}card", (72, 505, 936, 590))}
    {plate("{{ID_PREFIX_1}}m", HERO, (1198, 47, 692, 1128), (90, 523, 340, 554), "w", "border-radius:12px 0 0 12px")}
    {plate("{{ID_PREFIX_1}}u", HERO, (1888, 47, 1142, 1128), (429, 523, 561, 554), "w", "border-radius:0 12px 12px 0;opacity:0")}
  </div>
</div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b04-b05 before-after
tl.fromTo("#{{ID_PREFIX_1}}sa", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 8.32);
tl.fromTo("#{{ID_PREFIX_1}}sb", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 9.2);
tl.to("#{{ID_PREFIX_1}}a", { x: -240, y: -195, scale: 0.65, duration: 0.24, ease: "power2.out" }, 9.9);
tl.to("#{{ID_PREFIX_1}}b", { x: 240, y: -415, scale: 0.65, duration: 0.24, ease: "power2.out" }, 9.9);
show("#{{ID_PREFIX_1}}art", 10.16);
cutIn("#{{ID_PREFIX_1}}art", 10.16, 0, "50% 50%");
rise("#{{ID_PREFIX_1}}u", 10.8, 24, 0.55);
```

<!-- LIBRARY_DATA
{
  "schema": 1,
  "name": "before-after",
  "variants": [
    {
      "family": "before-after",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-names",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b04",
        "b05"
      ],
      "components": [
        "compare before-state: two built pills (.pillw) + strike lines carried from b01",
        "compare after-state: pill row + the post's own art in a white card, two windows of one image"
      ],
      "purpose": [
        "'no longer Max 5X and Max 20X' opens a before-after, and a comparison takes its own row even with product names in it, using the real post wording. Form: built pills, words verbatim from the post.",
        "'just Max and Ultra' is the pivot of the same before-after, so it develops b04 and keeps its template. Form: real artifact, the post's own art, names only, no green field as a panel."
      ],
      "windows": [
        [
          "#sc-names",
          7.5,
          11.5
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-13-at-9.3s.png",
      "python": "HERO = \"{{ASSET_1}}\"\n\ndef pill(id_, y, text, strike):\n        return (f'<div id=\"{id_}\" class=\"pillw\" style=\"left:190px;top:{y}px;width:700px;height:160px;border-radius:22px;font-size:84px\">'\n                f'<span id=\"{id_}t\" class=\"stw\">{text}<i id=\"{strike}\" class=\"sk\" style=\"left:-12px;right:-12px;top:42px;height:6px\"></i></span></div>')\n\nS.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene full\">\n  {pill(\"{{ID_PREFIX_1}}a\", 530, \"{{COPY_1}}\", \"{{ID_PREFIX_1}}sa\")}\n  {pill(\"{{ID_PREFIX_1}}b\", 750, \"{{COPY_2}}\", \"{{ID_PREFIX_1}}sb\")}\n  <div id=\"{{ID_PREFIX_1}}art\" class=\"fill\" style=\"opacity:0\">\n    {card(\"{{ID_PREFIX_1}}card\", (72, 505, 936, 590))}\n    {plate(\"{{ID_PREFIX_1}}m\", HERO, (1198, 47, 692, 1128), (90, 523, 340, 554), \"w\", \"border-radius:12px 0 0 12px\")}\n    {plate(\"{{ID_PREFIX_1}}u\", HERO, (1888, 47, 1142, 1128), (429, 523, 561, 554), \"w\", \"border-radius:0 12px 12px 0;opacity:0\")}\n  </div>\n</div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b04-b05 before-after\ntl.fromTo(\"#{{ID_PREFIX_1}}sa\", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: \"power2.out\", immediateRender: false }, 8.32);\ntl.fromTo(\"#{{ID_PREFIX_1}}sb\", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: \"power2.out\", immediateRender: false }, 9.2);\ntl.to(\"#{{ID_PREFIX_1}}a\", { x: -240, y: -195, scale: 0.65, duration: 0.24, ease: \"power2.out\" }, 9.9);\ntl.to(\"#{{ID_PREFIX_1}}b\", { x: 240, y: -415, scale: 0.65, duration: 0.24, ease: \"power2.out\" }, 9.9);\nshow(\"#{{ID_PREFIX_1}}art\", 10.16);\ncutIn(\"#{{ID_PREFIX_1}}art\", 10.16, 0, \"50% 50%\");\nrise(\"#{{ID_PREFIX_1}}u\", 10.8, 24, 0.55);",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-names",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "nm-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "ASSET_1": {
          "kind": "asset",
          "example": "posts/post-hero-cards.png",
          "fill": "Asset path relative to assets/; use real media and remeasure crop/box coordinates."
        },
        "COPY_1": {
          "kind": "copy",
          "example": "Max 5x",
          "fill": "Exact verified display copy; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS."
        },
        "COPY_2": {
          "kind": "copy",
          "example": "Max 20x",
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
