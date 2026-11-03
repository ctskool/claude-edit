# stacked-capture

Proven: 1 approved video(s). Variants: 4.

Use the closest variant and adapt it to the new beat. Slots use literal {{NAME}} substitution, never str.format: Python f-string braces and JS objects must survive.

Fill every slot in both snippets with the same value. ID prefixes end in '-'. Escape copy for its surrounding Python string and for HTML. Slots are authoring source fragments, not executable input. The examples reconstruct the approved source.

The Python scene statement belongs in scenes.py build(); any def helpers shown belong before its use. It depends on the ivory build-kit imports/helpers and the project's CSS. Compare custom helpers and CSS with the linked approved source. Namespace local variables/helpers if needed. Do not import or run the donor project.

Retiming is required: every timeline position and clip start/duration below is an example in donor seconds. Replace with the new plan's numeric times, retain A(t) alignment, and remeasure asset crops, geometry and highlight boxes. Copy no donor fact or figure without facts.json.

Add WINDOWS, EVENT_BINDS and COPY_BINDS in owners.py for the new scene and stable plan event_ids. Inspect EXTRA_ROOTS in the donor owners.py for external targets and their render cost. Rebuild from the kit and run the owner/source checks; these snippets alone are not a ready composition.

## Variant 1: sc-ultra

Used in 1030-2, beats b08, b09.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: plateCard, one real plan card zoomed, drawn clay outline; plateCard stack: real row + real footnote, tint on the scope words

For: 'the Ultra plan' names a specific plan with a real page. Top row. Form: real capture of claude.com/pricing in the white card, zoomed to one card at about 2.9x so body text reads about 46 px. 'no more five-hour limits' is the plan page's own row, and a real row beats a drawn timer. 'which is great' is under 1 s, so it rides this beat. Form: real capture. The footnote is required: the row alone drops the verified scope.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-ultra",14.567,18.367]].


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-ultra | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | ul- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | shots/pricing-footnote-light.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |
| ASSET_2 | shots/pricing-plans-light.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |

Python template:

```python
def inpin(box, tx, ty, s, f):
    """A frame-px box at rest, as a box inside a pin pushed by (tx, ty, s) with origin 0 0"""
    return [round((f[0] - box[0] - tx) / s, 2), round((f[1] - box[1] - ty) / s, 2), round(f[2] / s, 2), round(f[3] / s, 2)]

def mark(id_, b, cls="mkr", extra=""):
    """A marker tint or a strike line. Starts hidden, wipes on from the left"""
    return f'<div id="{id_}" class="{cls}" style="{boxstyle(b)};{extra}"></div>'

PLANS = "{{ASSET_2}}"

FOOT = "{{ASSET_1}}"

UB = (90, 1222, 900, 83)

S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene full">
  <div id="{{ID_PREFIX_1}}c1" class="fill">
    {card("{{ID_PREFIX_1}}card", (72, 327, 936, 806))}
    {plate("{{ID_PREFIX_1}}pl", PLANS, (1396, 160, 1216, 1040), (90, 345, 900, 770), "w")}
    {drawn("{{ID_PREFIX_1}}o", (167.0, 638.2, 251.6, 97.7), 12)}
  </div>
  <div id="{{ID_PREFIX_1}}c2" class="fill" style="opacity:0">
    {card("{{ID_PREFIX_1}}card2", (72, 956, 936, 234))}
    {plate("{{ID_PREFIX_1}}p2", PLANS, (1396, 1720, 1216, 268), (90, 974, 900, 198), "w")}
  </div>
  <div id="{{ID_PREFIX_1}}c3" class="fill" style="opacity:0">
    {card("{{ID_PREFIX_1}}card3", (72, 1204, 936, 119))}
    {plate("{{ID_PREFIX_1}}p3", FOOT, (0, 0, 1176, 108), UB, "w", extra=mark("{{ID_PREFIX_1}}m", inpin(UB, 0, 0, 1, (552.2, 1243.5, 381.1, 52.3)), extra="border-radius:6px"))}
  </div>
</div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b08-b09 plan card, row, footnote with verified lit
drawRect("#{{ID_PREFIX_1}}o", 15.04, 0.3);
tl.to("#{{ID_PREFIX_1}}c1", { y: -197, duration: 0.3, ease: "power3.out" }, 16);
rise("#{{ID_PREFIX_1}}c2", 16, 40, 0.3);
rise("#{{ID_PREFIX_1}}c3", 16.64, 40, 0.3);
tl.fromTo("#{{ID_PREFIX_1}}m", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 17.2);
```

## Variant 2: sc-q13

Used in 1030-2, beats b13.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: Two white ivory cards with real doc captures and highlights; chip on the seam

For: Chase's note: replace the repeating text panel. The Codex line from b11-b12 stays up and Claude's own help page lands under it, so 'joined them' is shown with both real docs. Scope stays visible: 'Pro plans' lit on Codex, 'verified Ultra accounts' lit on Claude.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-q13",24.3,27.3]].


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-q13 | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | q13- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | shots/claude-code-support.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |
| ASSET_2 | shots/codex-pricing-light.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |
| COPY_1 | Codex pricing doc | Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS. |
| COPY_2 | Claude Code help page | Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS. |

Python template:

```python
def inpin(box, tx, ty, s, f):
    """A frame-px box at rest, as a box inside a pin pushed by (tx, ty, s) with origin 0 0"""
    return [round((f[0] - box[0] - tx) / s, 2), round((f[1] - box[1] - ty) / s, 2), round(f[2] / s, 2), round(f[3] / s, 2)]

def mark(id_, b, cls="mkr", extra=""):
    """A marker tint or a strike line. Starts hidden, wipes on from the left"""
    return f'<div id="{id_}" class="{cls}" style="{boxstyle(b)};{extra}"></div>'

AR, AB = (0, 46, 812, 120), (90, 200, 900, 133)

BR, BB = (20, 160, 1330, 205), (90, 442, 900, 139)

S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene"><div id="{{ID_PREFIX_1}}g" class="fill">
  {card("{{ID_PREFIX_1}}card-a", (72, 140, 936, 218))}
  <div id="{{ID_PREFIX_1}}la" class="src" style="left:90px;top:158px;font-size:26px">{{COPY_1}}</div>
  {plate("{{ID_PREFIX_1}}pa", "{{ASSET_2}}", AR, AB, "w", extra=mark("{{ID_PREFIX_1}}m0", inpin(AB, 0, 0, 1, map_box(AR, AB, (556, 60, 137, 38))), extra="border-radius:6px") + mark("{{ID_PREFIX_1}}m1", inpin(AB, 0, 0, 1, map_box(AR, AB, (0, 112, 462, 38))), extra="border-radius:6px"))}
  <div id="{{ID_PREFIX_1}}b" class="fill" style="opacity:0">
    {card("{{ID_PREFIX_1}}card-b", (72, 382, 936, 230))}
    <div id="{{ID_PREFIX_1}}lb" class="src" style="left:90px;top:400px;font-size:26px">{{COPY_2}}</div>
    {plate("{{ID_PREFIX_1}}pb", "{{ASSET_1}}", BR, BB, "w", extra=mark("{{ID_PREFIX_1}}m2", inpin(BB, 0, 0, 1, map_box(BR, BB, (875, 236, 285, 50))), extra="border-radius:6px") + mark("{{ID_PREFIX_1}}m3", inpin(BB, 0, 0, 1, map_box(BR, BB, (22, 305, 945, 50))), extra="border-radius:6px"))}
  </div>
</div></div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b13 the Codex line holds, Claude's page lands on finally, its line lights on joined
show("#{{ID_PREFIX_1}}m0", 24.3);
show("#{{ID_PREFIX_1}}m1", 24.3);
rise("#{{ID_PREFIX_1}}b", 25.62, 18, 0.2);
tl.fromTo(["#{{ID_PREFIX_1}}m2", "#{{ID_PREFIX_1}}m3"], { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, A(26.66));
tl.fromTo("#{{ID_PREFIX_1}}g", { scale: 1, transformOrigin: "50% 50%" }, { scale: 1.0156, duration: 3.0, ease: "none", immediateRender: false }, A(24.3));
```

## Variant 3: sc-q28

Used in 1030-2, beats b28.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: White ivory card with the pricing page Max and Ultra name rows already in b29 positions; chip on the seam

For: Chase's note: replace the repeating caption panel with pricing arriving early, using the same name rows and positions as the untouched b29. Cropped above the limit line.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-q28",54.7,56.067]].


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-q28 | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | q28- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | shots/pricing-plans-light.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |

Python template:

```python
PLANS = "{{ASSET_1}}"

S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene">
  {card("{{ID_PREFIX_1}}card", (72, 254, 936, 396))}
  {plate("{{ID_PREFIX_1}}p0", PLANS, (64, 500, 1216, 200), (90, 272, 900, 148), "w")}
  <div class="abs" style="left:90px;top:452px;width:900px;height:1px;background:#e4e2da"></div>
  {plate("{{ID_PREFIX_1}}p1", PLANS, (1396, 500, 1216, 200), (90, 484, 900, 148), "w")}
</div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b28 early pricing rows, aligned with the untouched b29 rows
```

## Variant 4: sc-close

Used in 1030-2, beats b29.

Approval: PASS; composition 7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e.

Plan component: plateCard, two real name rows stacked, drawn outlines

For: 'your Claude Code pricing' names a specific price page that exists, and this clause is not opinion or payoff, so the row applies. Form: real capture of claude.com/pricing, cropped to the name rows at about 2.9x; the tag reads about 43 px.

Source: [scenes.py](../../../examples/ivory-edit/v2/editorial/tools_local/scenes.py), [owners.py](../../../examples/ivory-edit/v2/editorial/tools_local/owners.py).

Window examples: [["#sc-close",56.067,57.65]].


| Slot | Example | Fill with |
| --- | --- | --- |
| SCENE_ID | sc-close | Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds. |
| ID_PREFIX_1 | cl- | Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds. |
| ASSET_1 | shots/pricing-plans-light.png | Asset path relative to assets/; use real media and remeasure crop/box coordinates. |

Python template:

```python
PLANS = "{{ASSET_1}}"

S.append(own("{{SCENE_ID}}", f"""<div id="{{SCENE_ID}}" class="scene"><div id="{{ID_PREFIX_1}}g" class="fill">
  {card("{{ID_PREFIX_1}}card", (72, 254, 936, 396))}
  {plate("{{ID_PREFIX_1}}p0", PLANS, (64, 500, 1216, 200), (90, 272, 900, 148), "w")}
  <div class="abs" style="left:90px;top:452px;width:900px;height:1px;background:#e4e2da"></div>
  {plate("{{ID_PREFIX_1}}p1", PLANS, (1396, 500, 1216, 200), (90, 484, 900, 148), "w")}
  {drawn("{{ID_PREFIX_1}}o0", (409.7, 328.2, 426.3, 77.0), 12)}
  {drawn("{{ID_PREFIX_1}}o1", (436.4, 540.2, 426.3, 77.0), 12)}
</div></div>"""))
```

Timeline template:

```javascript
own("scene.{{SCENE_ID}}");
// ---- b29 two real rows, tags lit, nothing exits before the final frame
tl.fromTo("#{{ID_PREFIX_1}}g", { scale: 1, transformOrigin: "50% 50%" }, { scale: 1.00823, duration: 1.583, ease: "none", immediateRender: false }, A(56.067));
drawRect("#{{ID_PREFIX_1}}o0", 56.82, 0.3);
drawRect("#{{ID_PREFIX_1}}o1", 56.82, 0.3);
```

<!-- LIBRARY_DATA
{
  "schema": 1,
  "name": "stacked-capture",
  "variants": [
    {
      "family": "stacked-capture",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-ultra",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b08",
        "b09"
      ],
      "components": [
        "plateCard, one real plan card zoomed, drawn clay outline",
        "plateCard stack: real row + real footnote, tint on the scope words"
      ],
      "purpose": [
        "'the Ultra plan' names a specific plan with a real page. Top row. Form: real capture of claude.com/pricing in the white card, zoomed to one card at about 2.9x so body text reads about 46 px.",
        "'no more five-hour limits' is the plan page's own row, and a real row beats a drawn timer. 'which is great' is under 1 s, so it rides this beat. Form: real capture. The footnote is required: the row alone drops the verified scope."
      ],
      "windows": [
        [
          "#sc-ultra",
          14.567,
          18.367
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-27-at-16.7s.png",
      "python": "def inpin(box, tx, ty, s, f):\n    \"\"\"A frame-px box at rest, as a box inside a pin pushed by (tx, ty, s) with origin 0 0\"\"\"\n    return [round((f[0] - box[0] - tx) / s, 2), round((f[1] - box[1] - ty) / s, 2), round(f[2] / s, 2), round(f[3] / s, 2)]\n\ndef mark(id_, b, cls=\"mkr\", extra=\"\"):\n    \"\"\"A marker tint or a strike line. Starts hidden, wipes on from the left\"\"\"\n    return f'<div id=\"{id_}\" class=\"{cls}\" style=\"{boxstyle(b)};{extra}\"></div>'\n\nPLANS = \"{{ASSET_2}}\"\n\nFOOT = \"{{ASSET_1}}\"\n\nUB = (90, 1222, 900, 83)\n\nS.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene full\">\n  <div id=\"{{ID_PREFIX_1}}c1\" class=\"fill\">\n    {card(\"{{ID_PREFIX_1}}card\", (72, 327, 936, 806))}\n    {plate(\"{{ID_PREFIX_1}}pl\", PLANS, (1396, 160, 1216, 1040), (90, 345, 900, 770), \"w\")}\n    {drawn(\"{{ID_PREFIX_1}}o\", (167.0, 638.2, 251.6, 97.7), 12)}\n  </div>\n  <div id=\"{{ID_PREFIX_1}}c2\" class=\"fill\" style=\"opacity:0\">\n    {card(\"{{ID_PREFIX_1}}card2\", (72, 956, 936, 234))}\n    {plate(\"{{ID_PREFIX_1}}p2\", PLANS, (1396, 1720, 1216, 268), (90, 974, 900, 198), \"w\")}\n  </div>\n  <div id=\"{{ID_PREFIX_1}}c3\" class=\"fill\" style=\"opacity:0\">\n    {card(\"{{ID_PREFIX_1}}card3\", (72, 1204, 936, 119))}\n    {plate(\"{{ID_PREFIX_1}}p3\", FOOT, (0, 0, 1176, 108), UB, \"w\", extra=mark(\"{{ID_PREFIX_1}}m\", inpin(UB, 0, 0, 1, (552.2, 1243.5, 381.1, 52.3)), extra=\"border-radius:6px\"))}\n  </div>\n</div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b08-b09 plan card, row, footnote with verified lit\ndrawRect(\"#{{ID_PREFIX_1}}o\", 15.04, 0.3);\ntl.to(\"#{{ID_PREFIX_1}}c1\", { y: -197, duration: 0.3, ease: \"power3.out\" }, 16);\nrise(\"#{{ID_PREFIX_1}}c2\", 16, 40, 0.3);\nrise(\"#{{ID_PREFIX_1}}c3\", 16.64, 40, 0.3);\ntl.fromTo(\"#{{ID_PREFIX_1}}m\", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: \"power2.out\", immediateRender: false }, 17.2);",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-ultra",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "ul-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "ASSET_1": {
          "kind": "asset",
          "example": "shots/pricing-footnote-light.png",
          "fill": "Asset path relative to assets/; use real media and remeasure crop/box coordinates."
        },
        "ASSET_2": {
          "kind": "asset",
          "example": "shots/pricing-plans-light.png",
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
      "family": "stacked-capture",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-q13",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b13"
      ],
      "components": [
        "Two white ivory cards with real doc captures and highlights; chip on the seam"
      ],
      "purpose": [
        "Chase's note: replace the repeating text panel. The Codex line from b11-b12 stays up and Claude's own help page lands under it, so 'joined them' is shown with both real docs. Scope stays visible: 'Pro plans' lit on Codex, 'verified Ultra accounts' lit on Claude."
      ],
      "windows": [
        [
          "#sc-q13",
          24.3,
          27.3
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-38-at-25.7s.png",
      "python": "def inpin(box, tx, ty, s, f):\n    \"\"\"A frame-px box at rest, as a box inside a pin pushed by (tx, ty, s) with origin 0 0\"\"\"\n    return [round((f[0] - box[0] - tx) / s, 2), round((f[1] - box[1] - ty) / s, 2), round(f[2] / s, 2), round(f[3] / s, 2)]\n\ndef mark(id_, b, cls=\"mkr\", extra=\"\"):\n    \"\"\"A marker tint or a strike line. Starts hidden, wipes on from the left\"\"\"\n    return f'<div id=\"{id_}\" class=\"{cls}\" style=\"{boxstyle(b)};{extra}\"></div>'\n\nAR, AB = (0, 46, 812, 120), (90, 200, 900, 133)\n\nBR, BB = (20, 160, 1330, 205), (90, 442, 900, 139)\n\nS.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene\"><div id=\"{{ID_PREFIX_1}}g\" class=\"fill\">\n  {card(\"{{ID_PREFIX_1}}card-a\", (72, 140, 936, 218))}\n  <div id=\"{{ID_PREFIX_1}}la\" class=\"src\" style=\"left:90px;top:158px;font-size:26px\">{{COPY_1}}</div>\n  {plate(\"{{ID_PREFIX_1}}pa\", \"{{ASSET_2}}\", AR, AB, \"w\", extra=mark(\"{{ID_PREFIX_1}}m0\", inpin(AB, 0, 0, 1, map_box(AR, AB, (556, 60, 137, 38))), extra=\"border-radius:6px\") + mark(\"{{ID_PREFIX_1}}m1\", inpin(AB, 0, 0, 1, map_box(AR, AB, (0, 112, 462, 38))), extra=\"border-radius:6px\"))}\n  <div id=\"{{ID_PREFIX_1}}b\" class=\"fill\" style=\"opacity:0\">\n    {card(\"{{ID_PREFIX_1}}card-b\", (72, 382, 936, 230))}\n    <div id=\"{{ID_PREFIX_1}}lb\" class=\"src\" style=\"left:90px;top:400px;font-size:26px\">{{COPY_2}}</div>\n    {plate(\"{{ID_PREFIX_1}}pb\", \"{{ASSET_1}}\", BR, BB, \"w\", extra=mark(\"{{ID_PREFIX_1}}m2\", inpin(BB, 0, 0, 1, map_box(BR, BB, (875, 236, 285, 50))), extra=\"border-radius:6px\") + mark(\"{{ID_PREFIX_1}}m3\", inpin(BB, 0, 0, 1, map_box(BR, BB, (22, 305, 945, 50))), extra=\"border-radius:6px\"))}\n  </div>\n</div></div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b13 the Codex line holds, Claude's page lands on finally, its line lights on joined\nshow(\"#{{ID_PREFIX_1}}m0\", 24.3);\nshow(\"#{{ID_PREFIX_1}}m1\", 24.3);\nrise(\"#{{ID_PREFIX_1}}b\", 25.62, 18, 0.2);\ntl.fromTo([\"#{{ID_PREFIX_1}}m2\", \"#{{ID_PREFIX_1}}m3\"], { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: \"power2.out\", immediateRender: false }, A(26.66));\ntl.fromTo(\"#{{ID_PREFIX_1}}g\", { scale: 1, transformOrigin: \"50% 50%\" }, { scale: 1.0156, duration: 3.0, ease: \"none\", immediateRender: false }, A(24.3));",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-q13",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "q13-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "ASSET_1": {
          "kind": "asset",
          "example": "shots/claude-code-support.png",
          "fill": "Asset path relative to assets/; use real media and remeasure crop/box coordinates."
        },
        "ASSET_2": {
          "kind": "asset",
          "example": "shots/codex-pricing-light.png",
          "fill": "Asset path relative to assets/; use real media and remeasure crop/box coordinates."
        },
        "COPY_1": {
          "kind": "copy",
          "example": "Codex pricing doc",
          "fill": "Exact verified HTML text; escape for the surrounding Python string and HTML. Update beats.json and COPY_BINDS."
        },
        "COPY_2": {
          "kind": "copy",
          "example": "Claude Code help page",
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
      "family": "stacked-capture",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-q28",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b28"
      ],
      "components": [
        "White ivory card with the pricing page Max and Ultra name rows already in b29 positions; chip on the seam"
      ],
      "purpose": [
        "Chase's note: replace the repeating caption panel with pricing arriving early, using the same name rows and positions as the untouched b29. Cropped above the limit line."
      ],
      "windows": [
        [
          "#sc-q28",
          54.7,
          56.067
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-78-at-55.2s.png",
      "python": "PLANS = \"{{ASSET_1}}\"\n\nS.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene\">\n  {card(\"{{ID_PREFIX_1}}card\", (72, 254, 936, 396))}\n  {plate(\"{{ID_PREFIX_1}}p0\", PLANS, (64, 500, 1216, 200), (90, 272, 900, 148), \"w\")}\n  <div class=\"abs\" style=\"left:90px;top:452px;width:900px;height:1px;background:#e4e2da\"></div>\n  {plate(\"{{ID_PREFIX_1}}p1\", PLANS, (1396, 500, 1216, 200), (90, 484, 900, 148), \"w\")}\n</div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b28 early pricing rows, aligned with the untouched b29 rows",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-q28",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "q28-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "ASSET_1": {
          "kind": "asset",
          "example": "shots/pricing-plans-light.png",
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
      "family": "stacked-capture",
      "project": "1030-2",
      "project_path": "work/1030-2",
      "scene": "sc-close",
      "revision": "7e9b1c77b0b7a7b38bcbed49781038a64101d67e4b9b07e58c2b695bec248f4e",
      "approval": "work/1030-2/beat/approvals/6d91e9d35d6bbf44.json",
      "approval_result": "PASS",
      "beats": [
        "b29"
      ],
      "components": [
        "plateCard, two real name rows stacked, drawn outlines"
      ],
      "purpose": [
        "'your Claude Code pricing' names a specific price page that exists, and this clause is not opinion or payoff, so the row applies. Form: real capture of claude.com/pricing, cropped to the name rows at about 2.9x; the tag reads about 43 px."
      ],
      "windows": [
        [
          "#sc-close",
          56.067,
          57.65
        ]
      ],
      "snapshot": "work/1030-2/v2/editorial/snaps_build/frame-80-at-56.9s.png",
      "python": "PLANS = \"{{ASSET_1}}\"\n\nS.append(own(\"{{SCENE_ID}}\", f\"\"\"<div id=\"{{SCENE_ID}}\" class=\"scene\"><div id=\"{{ID_PREFIX_1}}g\" class=\"fill\">\n  {card(\"{{ID_PREFIX_1}}card\", (72, 254, 936, 396))}\n  {plate(\"{{ID_PREFIX_1}}p0\", PLANS, (64, 500, 1216, 200), (90, 272, 900, 148), \"w\")}\n  <div class=\"abs\" style=\"left:90px;top:452px;width:900px;height:1px;background:#e4e2da\"></div>\n  {plate(\"{{ID_PREFIX_1}}p1\", PLANS, (1396, 500, 1216, 200), (90, 484, 900, 148), \"w\")}\n  {drawn(\"{{ID_PREFIX_1}}o0\", (409.7, 328.2, 426.3, 77.0), 12)}\n  {drawn(\"{{ID_PREFIX_1}}o1\", (436.4, 540.2, 426.3, 77.0), 12)}\n</div></div>\"\"\"))",
      "javascript": "own(\"scene.{{SCENE_ID}}\");\n// ---- b29 two real rows, tags lit, nothing exits before the final frame\ntl.fromTo(\"#{{ID_PREFIX_1}}g\", { scale: 1, transformOrigin: \"50% 50%\" }, { scale: 1.00823, duration: 1.583, ease: \"none\", immediateRender: false }, A(56.067));\ndrawRect(\"#{{ID_PREFIX_1}}o0\", 56.82, 0.3);\ndrawRect(\"#{{ID_PREFIX_1}}o1\", 56.82, 0.3);",
      "slots": {
        "SCENE_ID": {
          "kind": "scene",
          "example": "sc-close",
          "fill": "Unique scene root, e.g. sc-proof; use in WINDOWS and all owner binds."
        },
        "ID_PREFIX_1": {
          "kind": "id_prefix",
          "example": "cl-",
          "fill": "Unique DOM prefix ending in '-'; replace consistently in markup, selectors and binds."
        },
        "ASSET_1": {
          "kind": "asset",
          "example": "shots/pricing-plans-light.png",
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
