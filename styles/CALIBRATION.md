# Measured donor targets (tools/gates.py, graphics band y 0-900, 10 fps)

Measured 2026-10-22 on the reels in `reference/`. A "static" sample = mean frame-to-frame luma change < 0.35.

| reel | creator | dur s | static s / 30 s | longest hold s | LUFS | TP dBTP |
|---|---|---|---|---|---|---|
| ref-C1 | reference C | 29.9 | 1.50 | 0.6 | -14.3 | -0.5 |
| ref-C2 | reference C | 25.6 | 3.86 | 2.2 | -14.3 | -0.8 |
| ref-C3 | reference C | 34.0 | 4.76 | 1.3 | -14.3 | -0.8 |
| ref-A1 | reference creator A | 62.9 | 15.83 | 2.3 | -14.1 | -0.9 |
| ref-A2 | reference creator A | 63.2 | 13.19 | 2.7 | -14.0 | -0.1 |
| ref-A3 | reference creator A | 65.4 | 13.62 | 2.6 | -14.1 | -0.9 |
| ref-B1 | reference creator B | 51.4 | 6.89 | 0.6 | -14.1 | -0.8 |
| ref-B2 | reference creator B | 39.7 | 2.57 | 0.4 | -14.1 | -0.9 |
| ref-B3 | reference creator B | 40.3 | 3.50 | 0.6 | -14.1 | -0.8 |

## Gate targets per pack (render must meet these on the encoded MP4)
| pack | static s / 30 s (max) | longest hold s (max) | loudness |
|---|---|---|---|
| saraev | 3.5 | 1.5 | -14 +/-1 LUFS, TP <= -1.0 |
| editorial | 8.0 (reference B-like) - up to 14 allowed for reference A-like calm cards | 2.5 | same |
| signal | 3.0 | 1.2 | same |

Negative control: `work/1022-2/_skeleton/renders/skeleton-draft.mp4` (static title cards) -> 28.4 s static / 30 s, FAIL. The gate fires.

## Layout rhythm (tools/gates.py `layout`, cuts in the face band y 1010-1920, threshold 30)
Measured: reference A ref-A1 ~9.1 switches / 30 s, reference B ref-B1 2.3; our editorial finals 3.6-3.75 (27 s opening
split) - the author found them too static. No quota: editorial switches follow the content (house rule 1 in
styles/editorial/STYLE.md); gates.py only warns softly on one layout held over 8 s.
reference C v11 measured 10.6 for comparison.
