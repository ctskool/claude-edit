# Hook variants: hooks 1, 2 and 3 of one short

Read this when he asks for more than one hook for the same short ("do hooks 1, 2 and 3", "make the other hooks"). It does not run by itself. The variants come after hook 1 is approved, and only when he asks for them.

## The rule [Chase, 2026-11-16]

Each extra hook is its own trial reel. It reuses hook 1's body and gets three changes:

1. **Its own opener graphic**, built on that hook's own words. It can use hook 1's style. It has to match what he says, so it is never hook 1's graphic copied over.
2. **A different colour look for the whole video**, taken from the standard set below. Recolouring the body is automatic, so no body scene is rebuilt.
3. **A different caption font** from hook 1. The look's caption block sets it.

**Why:** Instagram flags a variant that shares hook 1's body as a duplicate, and those posts get no reach. We tested this on 1114-tools between 2026-11-14 and 2026-11-16:

| What the variant changed | Result |
|---|---|
| A new skin only | Flagged |
| A new spoken hook | Flagged |
| A new spoken hook and a fully redesigned opener | Flagged |
| A whole-video recolour and a new caption font, with a new spoken hook or a new opener | Not flagged, twice |

The last variant was not flagged even though its audio was identical to a live post. So the voice and body can be reused, but the look of the whole video has to change. Whether a recolour alone, with the same hook, would pass has not been tested. Don't rely on it.

## The standard set

He picked these on 2026-11-16 from `work/1114-tools/color_schemes_compare.jpg`. They live in `templates/ivory/build_kit/looks/`.

| Look | What it is |
|---|---|
| `charcoal` | The house look: dark warm grey with orange. Hook 1 normally gets this one. |
| `charcoal-light` | Charcoal reversed: warm off-white ground, near-black text, the same orange. |
| `inverse` | Orange ground with black and cream. |

- Hook 1 takes the short's own look.
- Hooks 2 and 3 take the other two. Rotate which hook gets which colour from video to video, so a colour never sits with the same hook position every time.
- `charcoal-light` keeps charcoal's caption font. When it is a variant, give it another font (Inter, Hanken Grotesk or Newsreader are in the kit) and say so in the report. This is Claude's call, not his yet, so flag it.
- `paper` (white and black) and `cobalt` (blue and yellow) exist too but are not in the set. Use them only if he names them.

## Steps, as run on 1114-tools

These scripts were written for 1114-tools and still carry that video's numbers. Copy one into the new run folder, change its numbers, and say so in `RUN.md`. Moving them into the kit is an open item.

1. **Project.** Make `work/<id>-h<N>` from the approved hook 1 project. Hook N's words go in first, then the body moves by the difference in hook length. `b01` is rebuilt on hook N's words.
   - Used then: `work/1114-tools/hook_version.py <N> words|plan|sources`.
   - It hard-codes the join, the delta and the hook text. A copy shares `raw/` and the face files by hard link and gets its own `meta.json` id.
2. **Look.**
   - Set `"look"` and `look_source` (his words) in the project's `plan_src.py`.
   - A new or changed recolour comes from `work/1114-tools/recolor_looks.py <name>`. It reads one project's `style.css` for the kit's literal colours, so point `KIT_CSS` at this video's.
3. **Build, then look at a still of every scene before rendering.** A recolour finds literals the look missed: a label going dark on dark, or a rendered frame losing its contrast. Fix it in the look generator, never in generated HTML.
   - A title card's small settle after a takeover cut can read as a double cut on a light look (output check O4). `landIn` in 1114-tools' `timeline.js` lands it composed.
4. **Review render,** then `jumps.py`.
5. **Sound.**
   - Copy hook 1's `sound.json` and hard-link its `assets/sfx/` files in, because the new project has none.
   - Then run `sound_mix.py rebind --why "..."`, `check` and `stale`.
6. **Approval.** In the player, or in chat when he says so. `review.approve` then starts the 4K final.
   - Before re-delivering an id, move that id's existing `out/` final and `out/preview/` file to `out/_superseded/`. `deliver.py` refuses to overwrite them.
7. **Post** with /trial-reels.
   - The same caption across the variants is fine.
   - Say how much each variant shares with what is already on the account.
   - Post only on his OK.

## A whole aesthetic instead of a colour

He raised whole aesthetics instead of colours on 2026-11-16. One is built: **`collage`**, a Vox-style paper collage (`templates/ivory/build_kit/looks/collage/LOOK.md`). It is not in the standard set. Use it for a variant only when he names it.

- **Using it.** Set `"look": "collage"` in step 2. The look places its own scraps, clippings and paper motion, so no body scene is rebuilt. A scene only marks its title, number and main stat with `cq-title`, `cq-num` and `cq-stat`, and names a cut-out. A project made before 2026-11-16 needs the kit's `build.py` copied in first; `LOOK.md` gives the two commands.
- **Checks.** `jumps.py` prints SPIKE lines on this look. They are its 12 fps stepping and title-card jitter. Report them and let him decide; don't chase them as defects.
- **The duplicate filter.** Passes [Chase reported it on 2026-11-17]. The collage version of hook 1 went out on 2026-11-16 with the same hook, voice and caption as the live post, and was not flagged. So a whole new aesthetic alone gets a shared body, hook and voice through, where a recolour alone has not been tested. One post so far.
- **Font.** Its captions and titles are Arial Black, a Windows font. Fine for his videos. It needs a free font (Archivo Black is the near match) before the look ships in the public repo.

A second one is built: **`neo-brutalist`** (`templates/ivory/build_kit/looks/neo-brutalist/LOOK.md`), made on 2026-11-17 from the trial he liked ("looks solid"). Cream ground with a dot grid, white cards with thick black outlines and hard offset shadows, yellow for the one thing that matters, pink and mint as second colours, Inter 800/900, captions as white outlined boxes with a yellow highlight word. He approved its stills on 2026-11-17 ("Approved", on the sheets in `work/brutal-look-test/compare/`). Like collage it is not in the standard set: use it only when he names it.

- **Using it.** Set `"look": "neo-brutalist"` in step 2. No scene is rebuilt, and it has no images or `motion.js`.
- **First render: `work/1117-audit-nb` (2026-11-18), delivered at 4K30 with all checks passing.** One thing came up, and it applies to any light look: a white card that settles (`cutIn`) on a jump-cut frame read as a double cut (output check O4, at 33.7 s). Land that card composed (a plain slow push from scale 1) as `work/1117-audit-nb`'s `timeline.js` does. No scene needed changing.
- **Known gaps** (its `LOOK.md` has the list): a few kit classes no project uses were styled unseen; thin inline SVG line art and inline hairlines stay thin; `build.py` remaps markup and JS but not a project's own `style.css`, so a project-only class with a literal colour keeps it.
- **The duplicate filter.** Not tested yet.

A third one is built, of a different kind: **`blueprint`** (`templates/ivory/build_kit/looks/blueprint/LOOK.md`), approved on 2026-11-19 from a full-length motion test on the rea short ("that's really good"). The short is one engineering drawing: the camera follows a red pen from region to region, each region drafts itself in, proof plates sit in blueprint duotone and the one that matters develops into colour, dimension lines, section cuts, detail circles, exploded views and redlines carry the story, and the ending pulls back to the whole drawing with a title-block call to action. Use it only when he names it.

- **Using it.** Not through `build.py` (it has no `look.css`, so the kit refuses it). Copy `looks/blueprint/examples/rea.py` and build the short by hand on the engine, as `LOOK.md` says. It writes a HyperFrames project and renders through HyperFrames; 4K30 took 16 minutes for 50 s.
- **The duplicate filter.** Not tested yet. The rea version went out as a trial on 2026-11-20, after the charcoal, collage and neo-brutalist versions of the same take on 2026-11-18. Ask him what Instagram did with it.

A fourth, also hand-built: **`sky`** (`templates/ivory/build_kit/looks/sky/LOOK.md`). The pixel Claude guide acts the short out on a bright pixel sky: titles in pixel clouds (Jersey 15), cream-framed cards, a grass-and-brick floor. Chase built the guide up with us over five rounds on the rea short and picked this look on 2026-11-19. The rule is act it out on the key word when the line names something he can do, and step back (a peek, or off screen) when the line needs proof. Use it only when he names it ("sky", "the pixel guide", "the Claude guy").

- **Using it.** Like blueprint: no `build.py`. Copy `looks/sky/examples/rea.py` and build on the engine as `LOOK.md` says. It writes a HyperFrames project and renders through HyperFrames. It was ported on 2026-11-20 and its frames match the approved test.
- **Skies.** A finished sky short can go out in several skies for trial-reel variants: `looks/sky/skies.py <OUT> set render` makes noir, storm, snow, sunset and vicepastel (20 skies in all). Each is a whole-video colour change, the kind of change that has passed the duplicate filter; run `distance` to see how far each sits from the original. `LOOK.md` section "Skies".
- **The duplicate filter.** Not tested yet. The rea version went out as a trial on 2026-11-20, the fifth look of the same take and caption, with its titles still at y 66 under the island (his call). Ask him what Instagram did with it.

Not built: glassmorphism. It would be a full look folder like these two: its own `look.css` over every component class, and its own images and `motion.js` if it needs them. That is days of work by hand, not the hour a recolour takes.

## The three-aesthetic test [Chase, 2026-11-17]

One take, three versions, in **charcoal**, **neo-brutalist** and **collage**, same words and same hook. Built and delivered at 4K30 on 2026-11-18 from `work/1117-audit` (the Cloudflare security-audit short): `out/1117-audit_editorial_final_4k30.mp4`, `out/1117-audit-nb_...` and `out/1117-audit-collage_...`. Not posted yet. What a collage copy of a charcoal-written short needed is listed in `work/1117-audit/RUN.md` ("Finals delivered"): mainly red marker in place of yellow accents on paper, and no flat background fill on takeovers. Once all three are posted and he reports what Instagram did, take this section out and record what passed in the table at the top.
