# Beat Review v2 (reskin)

The live player (`tools/beat_review/index.html`) with the mockup 29/30 look: cool grey ground, hairlines, small uppercase mono labels, orange only for what needs Chase (changed beats, FAIL, open counts). Light by default.

Layout, functions, keys and endpoints are the live player's. `index.html` is a copy of the live page with two changes:
- a skin block at the end of the `<style>` (marked `v2 skin`)
- the default theme is `light` instead of `dark`

To carry a live-player fix over, copy the live `index.html` again and re-append the skin block.

`server.py` reuses the live server's handler and only serves this page at `/`. Run it on port 4750:

```text
python -B tools/beat_review_v2/server.py work/beat-fixture/v2/editorial
```

`test_server.py` checks the routes against a fake API (no renders, no real-project writes).

`_sol-layout/` holds Sol's new-layout build from 2026-11-02. Chase preferred his original layout, so it is kept for reference only.
