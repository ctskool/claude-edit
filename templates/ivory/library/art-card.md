# art-card

Proven: 1 approved video(s). Variants: 1.

Use the closest variant and adapt it to the new beat. Slots use literal {{NAME}} substitution, never str.format: Python f-string braces and JS objects must survive.

Fill every slot in both snippets with the same value. ID prefixes end in '-'. Escape copy for its surrounding Python string and for HTML. Slots are authoring source fragments, not executable input. The examples reconstruct the approved source.

The Python scene statement belongs in scenes.py build(); any def helpers shown belong before its use. It depends on the ivory build-kit imports/helpers and the project's CSS. Compare custom helpers and CSS with the linked approved source. Namespace local variables/helpers if needed. Do not import or run the donor project.

Retiming is required: every timeline position and clip start/duration below is an example in donor seconds. Replace with the new plan's numeric times, retain A(t) alignment, and remeasure asset crops, geometry and highlight boxes. Copy no donor fact or figure without facts.json.

Add WINDOWS, EVENT_BINDS and COPY_BINDS in owners.py for the new scene and stable plan event_ids. Inspect EXTRA_ROOTS in the donor owners.py for external targets and their render cost. Rebuild from the kit and run the owner/source checks; these snippets alone are not a ready composition.

## Variant 1: sc-q27

Used in 1030-2, beats b27.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: White ivory card containing the real post art, pushing into Ultra on Ultra, with a verified limit line; chip on the seam

For: Chase's note: replace the caption panel with the post's real plan art, moving into Ultra on its word. The graphic explicitly says limit and verified.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-q27",52.067,54.7]].

External ownership: EXTRA_ROOTS = {"scene.sc-q24": ["#face"], "scene.sc-q27": ["#face"]}


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-q27 | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | q27- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | posts/post-hero-cards.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |
| COPY_1 | No 5-hour limit, verified | Exact verified display copy; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS. |

Python template:

```python
HERO = "{{ASSET_1}}"

S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene">
  {card("{{ID_PREFIX_1}}card", (72, 162, 936, 530))}
  {plate("{{ID_PREFIX_1}}pl", HERO, (0, 0, 3080, 1250), (90, 180, 900, 365.26), "o0 w")}
  {lbl("{{ID_PREFIX_1}}verified", 116, 615, "{{COPY_1}}", 34)}
</div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b27 move into the Ultra card on Ultra; original punch-in stays
tl.fromTo("#{{ID_PREFIX_1}}pl-p", { x: 0, y: 0, scale: 1, transformOrigin: "0 0" }, { x: -1487.916, y: -354.641, scale: 2.697023, duration: 0.45, ease: "power3.inOut", immediateRender: false }, A(52.74));
tl.set("#face", { scale: 1.08, transformOrigin: "50% 8%" }, A(52.383));
tl.to("#face", { scale: 1, duration: 0.16, ease: "power2.out" }, 53.3);
tl.set("#face", { scale: 1 }, A(53.467));
```

<!-- LIBRARY_DATA
{
  "schema": 1,
  "name": "art-card",
  "variants": [
    {
      "family": "art-card",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-q27",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b27"
      ],
      "components": [
        "White ivory card containing the real post art, pushing into Ultra on Ultra, with a verified limit line; chip on the seam"
      ],
      "purpose": [
        "Chase's note: replace the caption panel with the post's real plan art, moving into Ultra on its word. The graphic explicitly says limit and verified."
      ],
      "windows": [
        [
          "#sc-q27",
          52.067,
          54.7
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-76-at-53.48s.png",
      "python": "HERO = \"{{ASSET_1}}\"\n\nS.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene\">\n  {card(\"{{ID_PREFIX_1}}card\", (72, 162, 936, 530))}\n  {plate(\"{{ID_PREFIX_1}}pl\", HERO, (0, 0, 3080, 1250), (90, 180, 900, 365.26), \"o0 w\")}\n  {lbl(\"{{ID_PREFIX_1}}verified\", 116, 615, \"{{COPY_1}}\", 34)}\n</div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b27 move into the Ultra card on Ultra; original punch-in stays\ntl.fromTo(\"#{{ID_PREFIX_1}}pl-p\", { x: 0, y: 0, scale: 1, transformOrigin: \"0 0\" }, { x: -1487.916, y: -354.641, scale: 2.697023, duration: 0.45, ease: \"power3.inOut\", immediateRender: false }, A(52.74));\ntl.set(\"#face\", { scale: 1.08, transformOrigin: \"50% 8%\" }, A(52.383));\ntl.to(\"#face\", { scale: 1, duration: 0.16, ease: \"power2.out\" }, 53.3);\ntl.set(\"#face\", { scale: 1 }, A(53.467));",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-q27",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "q27-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "ASSET_1": {
          "kind": "asset",
          "example": "posts/post-hero-cards.png",
          "fill": "Asset path relative to assets/; use real media and remeasure crop/box coordinates."
        },
        "COPY_1": {
          "kind": "copy",
          "example": "No 5-hour limit, verified",
          "fill": "Exact verified display copy; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS."
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
