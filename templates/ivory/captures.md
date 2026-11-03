# Ivory captures

How ivory gets its assets and how it shows them. Chase wins any conflict.
Layout numbers are at 1080x1920. The 2160x3840 publish frame is exactly double.

## The current rule on rebuilt and real

This stands as written until Chase changes it. The question is under Open decisions.
- Ivory keeps "rebuilt vector UI cards" and "real artifacts (never fake 'test' slides)". [Chase]
- Browser-window screenshot cards are banned as the main device. Small real logos and plates inside cards are OK. [Ours]
- The source says what proves the line. The form says how ivory shows it. A rebuilt card shows what a page says, not that an action ran. [Ours]

## Route each asset [Ours]

Pick the source per asset, never one route for a whole short.

| The beat needs | Source | Tool and place |
|---|---|---|
| What Chase showed or did on screen | A still or clip of his recording | ffmpeg on `raw/cut.mp4`, above the seam; `shared/clips` |
| A public page: repo, README section, docs, blog, pricing | Live capture, light and dark | `tools/capture_shots.py`; `shared/shots/` |
| A post behind a sign-in: X, Threads, LinkedIn | Read in the signed-in in-app browser, then rebuilt crisp | `tools/post_card.py`; `shared/posts/` |
| Another signed-in page: dashboard, profile grid | In-app browser screenshot, cropped to the content | Capped near 800 px, so small cards only |
| A number or claim with no good page | A built graphic, labelled with its source | Ivory's card parts. No kit base is chosen until Phase 2 |
| An abstract line, only if scenes stay | A generated scene, only with Codex | `codex exec`, see Scene images |
| A logo | The official icon | `node_modules/simple-icons/icons/<slug>.svg` |

- **Re-route a walled plate.** Rebuild Google and search UIs too, never screenshot them. [Ours]
  Why: they show a login or a session, not the page. Met: no `login_wall: true` plate reaches the build.
- **Record every source URL in `ASSETS.md`.** [Ours]
  Why: a rebuilt card is honest only if its words trace back. Met: every asset in the build has a line there.

## Make it real

- **Real means his.** If the line is about something Chase made or did, show his own, never another creator's page, another job's recording or stock. (untested on ivory)
  Why: anything else proves nothing about him. Met: `ASSETS.md` marks that asset as his, and every clip comes from this raw or was captured for this job.
- **Chase does every sign-in, and confirms anything that posts, sends or spends for real.** Claude asks, then continues. (untested on ivory)
  Why: credentials and side effects are his. Met: the handoff lists what a take created and how to undo it.
- **Cards carry real content.** Each word and figure comes from a real source or the transcript. [Ours]
  Why: fakes get spotted at once. Met: figures pass `HOUSE.md`'s fact test, other words trace to `ASSETS.md` or `raw/cut_words.json`.

## Make it read: whole, flat, big

- **What the viewer reads is whole, flat and big.** No crop through a row, icon or title bar, no tilt or perspective, and text near 36-40 px on the 1080 frame, never under 31. When unsure, go bigger. (untested on ivory)
  Why: a clipped, tilted or small capture proves nothing on a phone. Met: judged by eye on a rendered frame, until a tool exists. STYLE's rebuilt card sizes stand.
- **A capture sits on ivory.** A plate goes in the STYLE.md card: white, radius 22px, 1px #E4E2DA border. [Chase]
  Why: ivory stays ivory. Met: the ivory canvas surrounds the card; the panel is not the page's own colour.
- **Choose light or dark by what reads on ivory.** Capture both. [Ours]
  Why: one mode can fight the panel. Met: the build uses one chosen mode per asset, with both on file.

## Keep recordings whole

- **Chase's 2-4 s: pick one complete action that fits.** [Chase]
  Why: a partial action must not imply the whole workflow. Met: if none fits, say so at plan time and use a marked excerpt in split, or another treatment.
- **A clip of his screen never spans a join.** (untested on ivory)
  Why: `raw/cut.mp4` carries his cuts, so a clip across one jumps. Met: no join time from `raw/cuts.json` falls inside its range.
- **Every frame shows one shot.** The outgoing shot is gone on the cut frame. [Ours]
  Why: a one-frame overlap reached a render, a scene box over a post card. Met: step each cut frame by eye. Then run `tools/flash_scan.py` on the render.

## Privacy and signed-in pages

- **Nothing of Chase's account shows from the signed-in browser.** No sidebar, notifications or handle. [Ours]
  Why: his thing can show, his account chrome cannot. Met: frames read at source resolution across the whole span. Authorship shown on purpose is fine.
- **Never interact.** No like, follow or reply. One agent in the signed-in browser at a time. [Ours]
  Why: reading must leave no trace on his account. Met: nothing was clicked but navigation.
- **When a post's media disagrees with `facts.json`, reconcile date, version, units and scope first.** [Ours]
  Why: either can be stale. Met: a stale figure gets cropped and noted. One that contradicts the claim is flagged, never cropped away.
- **Credentials, keys and sign-in cards never show, and never go in records.** Cut them out of the asset file itself, not just the frame. (untested on ivory)
  Why: they do not come back once posted, and a push or crop change reveals what was only framed out. Met: read by eye at source resolution; no chat, `RUN.md`, log or file name holds the string.
- **His dashboards and panels he filmed can show. Name sensitive text for him, never hide it on Claude's own call.** [Chase] 2026-10-30.
  Why: they are his to show. Met: the handoff lists each revenue, inbox or calendar figure on screen with its time.
- **Public pages go through `capture_shots.py` or a private window.** (untested on ivory)
  Why: a window of his main profile can show his email in a corner. Met: no signed-in chrome on a public page.

## Scene images, only if scenes stay

- **Scenes need Codex.** On plain Claude Code (`codex` false in `RUN.md`) no beat is a scene: an abstract line takes the next type in `picker.md` that fits. [Ours]
  Why: the skill assumes Claude Code alone. Met: a run with `codex` false has no `shared/scenes/` images.
- **Scene images go through `codex exec`.** [Chase]
  `codex exec --skip-git-repo-check -s workspace-write -c service_tier="priority" -c model_reasoning_effort="high" "<what to make>. Save it as <path>."`
  If the file is not there, it is in `~/.codex/generated_images/`.
  Why: that is his image route. Met: `ASSETS.md` lists each prompt with `codex exec` as its route.
- **One look:** isometric 3D miniature, matte clay, ivory ground #EEEEE7, clay #C96442 accents, charcoal #1F1E1D details,
  soft daylight top-left, one centred subject, square 1:1. No text, logos or people in the image. [Ours]
  Why: all scenes belong to one world. Met: real text and logos are overlaid by the build.

## Trial ideas, off until Chase says yes

- Reading means show the source, explaining means show him. The source stays up through its last matched word, our stand-in for his gaze. (untested on ivory)
- A highlight wipe timed to reading, proven on a real capture first, with a before-and-after. (untested on ivory)
- Claude records screen B-roll itself, for moments he never filmed, with permitted actions and confirmation points set first. (untested on ivory)

## Open decisions

- **Real captures versus rebuilt cards as ivory's default.** STYLE.md lines 5, 66 and 129 favour rebuilt cards.
  `VISUAL_MENU.md` ("Proof beats illustration") and `WRITEUP.md` favour real material. 13 of 24 beats on 1023-test are already real shots.
- **Whether isometric scenes stay at all.**
- **The reading rule.** The game plan lists it as unproven and also as a Phase 5 build item, so it stays a trial until Chase says.
