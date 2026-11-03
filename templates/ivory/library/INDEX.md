# Proven ivory components

Read this before directing an ivory video. Prefer a proven component that fits the spoken idea; adapt its closest variant before inventing a new one. House rules, the current facts and Chase's notes govern the adaptation.

Proven counts distinct approved video ids, not beats or repeat harvests. Each variant links its source, plan component, purpose, slots and an existing snapshot where available. The fixture is reference data, not automatically proven.

| Component | Proven videos | Variants | Used for |
| --- | ---: | ---: | --- |
| [art-card](art-card.md) | 1 | 1 | White ivory card containing the real post art, pushing into Ultra on Ultra, with a verified limit line; chip on the seam |
| [before-after](before-after.md) | 1 | 1 | compare before-state: two built pills (.pillw) + strike lines carried from b01 |
| [clip-card](clip-card.md) | 1 | 3 | plateCard with his clip, vplate stills for the held first frame, HUD strip pop-in |
| [compare-table](compare-table.md) | 1 | 1 | compare: real table plate + pill outlines + drawn bracket + footnote plate + source line |
| [docs-card](docs-card.md) | 1 | 3 | White ivory card with the real Codex doc, same box as b11; clay outline on 'better'; chip on the seam |
| [list-card](list-card.md) | 1 | 1 | list card: socket + check + real post crop per row |
| [number-card](number-card.md) | 1 | 2 | number card, built: equation pills + serif figure + strike (STYLE Strike / X) |
| [post-card](post-card.md) | 1 | 4 | post card plate (STYLE Card + plate()), rebuilt @claudeai post, strike line (STYLE Strike / X) |
| [stacked-capture](stacked-capture.md) | 1 | 4 | plateCard, one real plan card zoomed, drawn clay outline |

Run from the repository root:

```text
python tools/library.py list
python tools/library.py show post-card
python tools/library.py harvest work/<id>/v2/editorial --dry-run
python tools/library.py harvest work/<id>/v2/editorial
```

Harvest reads only: no project imports, builds, snapshots or renders. It requires an active PASS/RECONCILED record in the video's beat/approvals/, a matching composition/lock, and unchanged approved authoring hashes. --dry-run performs the same checks and extraction without writing. Repeating a harvest does not add a proven video.

Reuse: inspect a variant with show, fill every literal {{SLOT}}, retime timeline calls and media to the new plan, remeasure crops/highlights, carry the required CSS/helpers, then author new WINDOWS/EVENT_BINDS/COPY_BINDS and run the kit's checks. Existing snapshot links are references and may predate approval. No number, price or claim inherits verification from a component.
