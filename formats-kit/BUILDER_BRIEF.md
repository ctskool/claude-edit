# Format builder brief (template)

Send one of these per format to a background builder agent (Agent tool, general-purpose) after
`python tools/formats.py media <id>` and `python tools/formats.py new <id> <format>`. Fill every `{...}` (`{root}` = the
absolute path of this repo; `{creator}`, `{handle}`, `{brand}` from config/profile.json). Add format-specific notes from
`formats/README.md`.

---

You are building ONE short-form reel in the "{format}" format for {creator} ({handle}, "{brand}"), on {os}, in `{root}`.
Work ONLY inside `{root}/work/{id}/formats/{format}/`. Do not edit anything under `{root}/formats/` or `{root}/tools/`
(engine bug? work around it in your project and report it).

READ FIRST: `{root}/formats/README.md` (library, contract, port notes, framing constraint, engine quirks, the asset
routing). The format's rules: `{root}/formats/{skill}/SKILL.md` (the look, layout numbers, captions, plan, build, review
checklist) - IGNORE its Step 0 setup gate and its transcribe / cut / crop / scaffold / render steps (done by the
pipeline; the coordinating session renders). Engine / script API: {engine files or script} and the skill's `examples/`
(structure only, never their wording or assets).

ALREADY IN THE PROJECT: {what `formats.py new` put there - media files, words.json, captions draft, project.json}.
Run python with `PYTHONUTF8=1` and `CREATOR_PROFILE_DIR={root}/formats/profile` (tools/formats.py sets both).

THE VIDEO ({topic}, {duration} s): text in `{root}/work/{id}/words.json`. Visible jump cuts (hide each one with a mode
switch / punch-in / takeover): {big_cuts from _media/media.json}.

FACTS: `{root}/work/{id}/facts.json` is the ONLY source for numbers and claims in graphics; its `unverifiable` list says
what never goes on screen. Captions stay verbatim (what the creator says); fix only misheard words.

ASSETS: `{root}/work/{id}/shared/` (shots, clips, logos, posts) described in `ASSETS.md`. Pick the source per asset as in
the claude-edit SKILL.md routing table: what the creator showed -> their recording; public pages ->
`tools/capture_shots.py`; posts behind a sign-in -> the signed-in in-app browser + `tools/post_card.py`; never image
search for other people's pictures unless the creator has allowed it. Copy what you use into the project. Record every
source.

FRAMING: measure the creator's head box from stills before placing captions or graphics; captions never cover the mouth
and stay in the safe zone (y 270-1500; headings below ~290).

CHECK: build, `npx hyperframes check` (or the script's `sheet` mode), `npx hyperframes snapshot --at ...`; Read every
image; fix what is wrong; iterate until clean. DO NOT render the final.

RETURN: the plan (time, mode / layout, graphic, assets + sources), anything invented, WARN / check lines left, caption
position and why, open issues, snapshot / sheet paths.
