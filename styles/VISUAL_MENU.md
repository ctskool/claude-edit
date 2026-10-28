# Visual menu: what each line gets on screen

The content planner picks ONE visual type per beat from what the line MEANS, then the style (editorial, business, ...)
decides how that type looks. Nothing on screen is a default or a gimmick: every pick names its trigger in the line.
Written into `beats.json` as `visual: {type, why, ...}` next to the older `shape` (the shape is the one-line art brief).

## The menu, in priority order (first rule that fits wins)

| type | pick it when the line... | what goes on screen | source |
|---|---|---|---|
| `real_shot` | names or points at a specific product, repo, post, page, price table or chart that exists | the real screenshot, zoomed / highlighted on the exact part said | `shared/shots`, `shared/posts` (capture routing in SKILL.md) |
| `own_clip` | describes something you showed or did in your screen recording | a 2-4 s clip of your own recording | `shared/clips` |
| `number` | turns on one figure (a price, a %, a multiplier, a date) | one big number + its unit + source line | `facts.json` only |
| `compare` | sets two things against each other (A vs B, before / after, cheaper / faster) | side by side, bars or an equation; the winner lit | `facts.json` + real shots |
| `diagram` | describes a process, a flow, steps, a structure, how parts connect | boxes / arrows / steps that build on each word | the transcript |
| `list` | names 3+ items in a row | one item per beat, each landing on its word | the transcript |
| `scene` | is abstract, a metaphor, a feeling about the world, a "big idea" with nothing real to show ("open weight", "neck and neck", "the moat is gone", "your data lives in silos") | a GENERATED illustration of the idea in the style's scene look (see below), with real text / logos overlaid by the build, never painted into the image | generated per video (`shared/scenes/`) |
| `face` | is opinion, emotion, direct address, a rhetorical question, the payoff, the CTA, or covers a visible jump cut | you full frame; at most a small kicker or chips | his camera |
| `text` | is a short punchy phrase that IS the message (a claim, a verdict) and none of the above fits | the words themselves, set big | the transcript |

Rules:
- **Proof beats illustration.** If a real asset can show the line, use it. A `scene` never replaces a fact's evidence; it can
  sit behind or beside it (e.g. the race scene with the two real scores floating over it).
- **Scenes are rare and earned:** at most 1 per ~15 s (a 45 s short gets 2-3), only on abstract / metaphor lines, never two
  in a row. Each one carries a `scene` block: `{idea, metaphor, prompt, overlay}` - `overlay` lists the REAL text, numbers
  and logo files the build puts on top. No brand logos, real people or readable text inside the generated image.
- A scene's metaphor must be literal to the spoken words where possible ("neck and neck" -> two racers side by side at the
  line), so the viewer gets it in under a second. Facts rules still apply to anything the metaphor implies (do not show one
  racer winning when the numbers are a tie).
- `why` quotes the trigger words from the line and says why the higher-priority types do not fit.

## Scene look (per style)

Every style that uses `scene` defines one scene look in its `STYLE.md` so all scenes in a video belong to one world:

- editorial: isometric 3D miniature, soft matte clay materials, warm ivory ground (#EEEEE7) and background, Claude-clay
  accents (#C96442) with charcoal details, soft daylight from top-left, gentle shadows, lots of empty space around a single
  centred subject, no text, no logos, square 1:1.
- business: same isometric miniature, near-black ground (#0A0B0D), signal red (#FF3B30) accents, rim light, glossy.

Generation: Higgsfield `generate_image` (one image per scene, 1:1, the cheapest model that renders clean isometric
miniatures; check the credit cost first and keep it to the 2-3 scenes the plan asks for). Save to `shared/scenes/<beat>.png`
and list the prompt + model in ASSETS.md.
