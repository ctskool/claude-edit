# Charcoal, for shorts

A second look for the ivory kit. [Chase, 2026-11-10: "couldn't we say that's now one of our styles? Because it did a good job of that."] It is his long-form YouTube look, adapted to the split-screen short. Proven on one take, built twice by hand before this folder existed, then once through this folder.

Everything in `templates/ivory/LIGHT.md` still holds: the hard rules, the three layouts, the frame bands, the chip's timing, the defect list. Only the look below changes. LIGHT's "no near-black" line does not apply to this look.

## Turn it on

`plan.json`: `"look": "charcoal"`, and `"look_source"` with his words. `build.py` lays `look.css` over the kit's styles and swaps ivory's literal colours wherever a scene or the timeline wrote one (`look.json` `remap`). Nothing else in the project changes, and a project with no `look` builds exactly as before.

## The look

- **Ground** `#1a1917`, no grid. **Text** `#ebe8e0`, secondary and labels `#aaa69d`, faint `#77736a`.
- **One orange**: `#ff6a3d` as a fill, `#ff7a50` as text. Only on the one thing that matters in the scene.
- **Type**: Hanken Grotesk 600 for headlines and big numbers, upright, with the one accent word in orange. Geist Mono for everything else.
- **Shapes**: square corners on everything. Cards are `#141312` with a 1.5 px hairline `#423f3b`, no shadow. Captures keep their own light background inside a hairline.
- **Caption chip**: light (`#ebe8e0`) with dark text, square, Geist Mono 600. An accent word is an orange block with near-black text.
- **Counter**: the same strip, as a row of square boxes that fill orange.
- **Ground band**: an ASCII terrain strip. In each scene, `{ground("<prefix>")}` as the root's first child on a split scene, `{ground("<prefix>", True)}` on a takeover, and one line in that scene's block so it drifts on the video's clock:

```js
tl.fromTo("#<prefix>-gr", { x: -(start * 6.667) }, { x: -(end * 6.667), duration: end - start, ease: "none", immediateRender: false }, A(start));
```

  Write the two x values and the duration as plain numbers.

## What to watch

- **Geist Mono is wider than Inter.** A label sized for ivory can overflow its card. Run `geometry.py` and fix every text overflow; on the test two labels had to shrink (52 to 42 px, 40 to 34 px).
- **Write colours through the variables** (`var(--clay)`, `var(--ink)`, `var(--card)`). The remap catches ivory's own literals; it cannot catch a new one.
- **Captures stay light.** That matches how the long-form shows a docs pull.
- **Never draw this look, or any look, as a choice the viewer can pick unless it ships.**

## His calls still open

- The light chip (the long-form has no captions to copy).
- The counter's shape.
- Where the ground band sits in split.
