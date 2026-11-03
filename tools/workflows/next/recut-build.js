export const meta = {
  name: 'recut-build-next',
  description: '/claude-edit copy of recut-build.js: direct, re-check and build read templates/HOUSE.md and templates/ivory/ as well as STYLE.md. The project starts from templates/ivory/build_kit, so its first build writes beats.lock.json, ownership.json and events.json and tools/beat_render/run.py accepts it. A plan check that does not pass refuses the build. The art-director scoring stage is removed: the one defects-only round runs after render, from the skill. No gauntlet.',
  whenToUse: 'After recut-plan (beats.json, facts.json, ASSETS.md, shared/) and tools/face_pipeline.sh (assets/face_*) are done for work/<id>',
  phases: [
    { title: 'Direct', detail: 'plan.json + STORYBOARD.md against the measured donor targets, independently re-checked' },
    { title: 'Build', detail: 'write the sources in the kit; build, owner audit, lint, motionlint, snapshot QA' },
  ],
}

// args: { id: '1021-1', styles: ['editorial'], note: '', planIssues: [], skipDirect: false, allowFullFace: false, allowFullFaceSource: 'template', codex: false }
// A workflow has no file access, so the skill resolves allowFullFace (default false) and its source (template or Chase's exact words) and passes both.
const A = args || {}
// The skill passes root (the project folder, absolute); a workflow cannot find it itself.
if (!A.root) throw new Error('pass root: the project folder as an absolute path (SKILL.md, intake)')
const S = String(A.root).replaceAll('\\', '/').replace(/\/+$/, '')
const ROOT = S
const W = `${ROOT}/work/${A.id}`
const T = `${ROOT}/templates`
const KIT = `${T}/ivory/build_kit`
const NOTE = `In these prompts and rules, Chase (he, his) means the creator of this video, who runs this skill; a [Chase] tag records where a rule came from. Chase's intake notes (keep these through every stage): ${JSON.stringify(A.note || '')}`
// A real ivory edit on the current sources. Read it for how a plan becomes code. It is another video's content, so nothing from it is copied in.
const REF = `${ROOT}/examples/ivory-edit/v2/editorial`
// Image route. Scene images need Codex's image tool; plain Claude Code (the default) plans no scenes.
const CODEX = A.codex === true
const IMAGE_RULE = CODEX
  ? `You own scene images before the plan check and Setup: generate any missing scene image into ${W}/shared/scenes/<beat>.png as in captures.md, through Codex's built-in image tool (from Claude Code, hand it to codex exec). Add every image's exact prompt, path and dimensions to ${W}/ASSETS.md. A missing or failed image stops direction; report it instead of handing an incomplete plan to the builder.`
  : `This run has no image tool (Codex is not installed): plan no scene images. A beat that beats.json marks scene gets text, a list, a diagram or a built card from the ivory components instead; say which in STORYBOARD.md.`
// Full-face gate: only the Boolean true turns it on.
const FF = A.allowFullFace === true
const FF_SOURCE = String(A.allowFullFaceSource || (FF ? 'not stated' : 'template'))
const FF_FIELDS = `allow_full_face to ${FF} (a JSON Boolean) and allow_full_face_source to ${JSON.stringify(FF_SOURCE)}`
const FF_RULE = FF
  ? `This run has allow_full_face true (source: ${JSON.stringify(FF_SOURCE)}): rules marked full_face on apply, and they win over any line saying a full-screen face is off or never.`
  : `This run has allow_full_face false (source: ${JSON.stringify(FF_SOURCE)}): every rule marked full_face on does not apply, so plan nothing from it. Only split and full-graphic takeover layouts exist, and Chase's face only ever sits in the bottom half.`
const FACE_FOOTAGE = FF
  ? `face_half.mp4 (the face cam for the bottom half, no person cut-out / head break-out), face_full.mp4 (full-frame face, only on full-face beats by the full-face rules in layout.md), voice.m4a.`
  : `face_half.mp4 (the face cam for the bottom half - SPLIT SCREEN in every style, no person cut-out / head break-out), voice.m4a. NEVER use face_full.mp4: no full-screen face beats, Chase's face stays in the bottom half and only the explainer may go full screen.`
// With full-face off, the planner marks a bottom-half punch-in in hint_why, since this workflow gets no jump-cut list.
const JUMP_PUNCH = FF
  ? ''
  : ` A split beat whose hint_why says "covers jump cut at <t> with a bottom-half punch-in" gets a quick punch-in on face_half.mp4 starting on that join, inside the bottom half only (scale about 1.08), as STYLE.md describes. Record it as an actions row with stable event_id, t at the join, what bottom-half punch-in, scale 1.08 and end. Use the build kit README's EXTRA_ROOTS recipe and reset inside the scene window; report its WHOLE RENDER cost.`
const FF_CHECK = FF
  ? `plan.json and beats.json must both set ${FF_FIELDS}. Full-face beats are allowed on the triggers layout.md lists.`
  : `plan.json and beats.json must both set ${FF_FIELDS}. A full-face beat or any use of face_full.mp4 is a defect. A split beat marked as a bottom-half punch-in jump cover with no punch-in in plan.json is a defect.`
const RULES = `RULES, read these before you start: ${T}/HOUSE.md, then ${['TEMPLATE.md', 'picker.md', 'layout.md', 'captures.md', 'captions.md', 'sound.md', 'ledger.md'].map((f) => `${T}/ivory/${f}`).join(', ')}. STYLE.md still holds the look's numbers (layout numbers at 1080x1920). These rules win any conflict with SKILL.md, VISUAL_MENU.md, donor targets or this prompt, and every [Chase] rule wins over the rest. Sections named "Trial ideas" are off. Open decisions stay open: keep current behaviour and flag them, never settle them. ${FF_RULE}`
const KITS = {
  editorial: `${ROOT}/styles/editorial/kit/editorial-chiefofstaff and editorial-vibecoding (replica components of two reference creators' looks)`,
}
// What the build tooling reads. The director writes these fields, and build.py stops in words if one is missing.
const PLAN_FIELDS = `plan.json fields the build reads, each one required: duration (a number equal to ${W}/metadata.json duration); beats[] with id, start, end, say (the beat's transcript text), layout, anchor, sub_anchors (a list, even if empty), actions (a list), proof_span ([start, end] or null), assets and crops; each anchor, sub-anchor and action has event_id, t, what and, when it lands on a word, word_i; captions.chunks[] with beat, text, words (word indexes), on, off, position (seam, takeover or fullface), accent, accent_words; cta_start; composition_files exactly ["tools_local/build.py","tools_local/scenes.py","tools_local/timeline.js","tools_local/style.css","tools_local/owners.py"]. Beats touch end to start with no gap, the first starts at 0, the last ends on ${W}/metadata.json duration exactly, and no beat is empty at 30 fps.`
// What stops a build, from tools/beat_render/confine.py and ownership.py. A builder that breaks one is told by the build, in these words.
const BUILD_RULES = `WHAT YOU WRITE (${KIT}/README.md has the shapes, read it first). Real sources only: plan.json and tools_local/{owners.py,scenes.py,timeline.js}, style.css if a component needs it. index.html, beats.lock.json, ownership.json and events.json are generated: never edit them.
- Regions: one scene group is one call in scenes.py build() where # @SCENES sits: S.append(own("sc-x", <markup>)). The markup is one balanced element whose id is the scene's root, class scene, or scene full on a full-graphic layout. The root's style holds nothing but opacity. A scene spanning beats is one region with several windows.
- Clips: a clip window must fit the media length remaining after media_start, or use vplate's stills argument to hold its last real frame underneath through the rest of the scene. From the project: mkdir assets/held; ffmpeg -sseof -0.04 -i assets/clips/name.mp4 -frames:v 1 -update 1 assets/held/name.png. Pass [("sc-x-held", "held/name.png", "")] as stills, and keep the video's dur within the media. Never let a plate turn black when a short clip ends. See the README recipe.
- Blocks: each scene has exactly one block in timeline.js where // @BLOCKS sits, opened by its marker line own("scene.sc-x"); alone on a line, in window order. The last block stays closed by the own(null); line after it. Never write that call in a comment.
- Owners, in owners.py: WINDOWS (["#sc-x", start, end] for each time it is up), LOGOS, HUD rows with HUD_LABEL, HUD_PLUGS and HUD_BINDS (leave HUD empty and flag it if the plan has nothing to count: what it counts on a new short is an open decision), EXTRA_ROOTS, and BLOCK_HELPERS as it stands.
- Binds, in owners.py: EVENT_BINDS, a row for every plan anchor, sub-anchor and action that does something on screen: event_id to (owner, target, expect, copy, hold_frames). COPY_BINDS, a row for every line of ${W}/beats.json copy: (beat, line, owner, target, t). A line must match beats.json character for character. An event with no bind reads UNVERIFIED, and a bind naming nothing stops the build.
- Tween positions are numbers. Every tl.to, tl.set, tl.from and tl.fromTo, and every helper call (A, show, hide, pop, popFirst, slotPop, rise, cutIn, on, off, drawRect, drawPath, word), takes a time that can be shown to be a number: a literal, arithmetic on literals, or a name in the block that only ever holds those. No labels, no relative "<" or "+=", no omitted position, no chaining one tween off another.
THESE STOP THE BUILD with BUILD STOPPED and no ownership.json, which run.py refuses: a region that is not one balanced element whose id is its owner's root; a region defining an id the shell holds or looks up; a position or helper time that is not a number; a label; a tween chained off another call; tl or a helper used other than by a direct call; a constant or function declared at the top of a block and read outside it; two regions sharing an id; a scene with no window or a window with no scene; a bind naming no owner or no line. Read the message, fix the source it names, build again. Never work round one by editing index.html or ownership.json.
THESE COST A WHOLE RENDER, and the build prints WHOLE RENDER with the reason: a block that reads anything but its own names, the helpers, tl and Math; a block that writes a member, sets .style, or uses a template literal, a regular expression or a callback; a tag off confine.py's short list (div, span, p, b, i, em, strong, br, img, video and plain svg shapes) or an attribute off it; an id another owner points at. The owner stays in the shell, so any later note on it re-renders every beat. Fix each one unless the plan truly needs it, and list what is left in your result.`

const DONE = { type: 'object', properties: { files: { type: 'array', items: { type: 'string' } }, notes: { type: 'string' } }, required: ['files', 'notes'] }
const PCHECK = { type: 'object', properties: { ok: { type: 'boolean' }, issues: { type: 'array', items: { type: 'string' } }, warnings: { type: 'array', items: { type: 'string' } } }, required: ['ok', 'issues', 'warnings'] }
const BUILT = { type: 'object', properties: {
  lint_errors: { type: 'number' }, motionlint: { type: 'string' }, snaps_dir: { type: 'string' },
  owner_audit: { type: 'string', description: 'the last line of conform.py --audit, which must start PASS' },
  source_check: { type: 'string', description: 'actual conform.py --all exit code and summary; before rendering exit 3 is expected, with no FAIL lines' },
  geometry_check: { type: 'string', description: 'geometry.py exit code and PASS/WARN/FAIL/UNVERIFIED counts (advisory): which FAILs you fixed, and which you left as false with their frames' },
  whole_render: { type: 'array', items: { type: 'string' }, description: 'every WHOLE RENDER line the last build printed, with why it stayed' },
  self_review: { type: 'string', description: 'what you checked in the contact sheets and what still looks weak' } },
  required: ['lint_errors', 'motionlint', 'snaps_dir', 'owner_audit', 'source_check', 'geometry_check', 'whole_render', 'self_review'] }

// An ok with issues still listed counts as failed, because the builder no longer sees issues.
const planPassed = (r) => !!r && !!r.c && r.c.ok === true && Array.isArray(r.c.issues) && r.c.issues.length === 0

const inputs = (s) => `${NOTE}
Content plan (truth for timing + copy): ${W}/beats.json (each beat's visual {type, why} is the picked visual - build that type; scene beats use the generated image ${W}/shared/scenes/<beat>.png with their scene.overlay laid on top, per the style's Scene component) ;words ${W}/words.json ; verified facts ${W}/facts.json ; assets ${W}/ASSETS.md (+ ${W}/shared/shots, clips, logos, fonts, sfx, vendor) ;
face footage in ${W}/assets: ${FACE_FOOTAGE}${JUMP_PUNCH}
${RULES}
Style law: ${ROOT}/styles/${s}/STYLE.md (+ REFERENCE-ANALYSIS.md) and ${ROOT}/styles/CALIBRATION.md (measured donor targets). No donor footage ships with this repo: CALIBRATION.md holds the measured targets.
HOW A PLAN BECOMES CODE: ${KIT}/README.md, and ${REF} (a real, approved ivory edit, text only with no media: its tools_local/ and plan.json show components, helpers, the caption system and layout runs in use). Read it only: its content is another video's. Measured components: ${KITS[s]}.
Proven ivory library: ${S}/templates/ivory/library/INDEX.md. Read it in one pass before choosing components. Prefer a proven component that fits the beat: run python ${S}/tools/library.py show <name> and adapt its closest variant before inventing one, and name the library component and variant in the beat's component field. The current facts, assets, timings and binds govern; its figures and copy are examples from another video.`

const styles = A.styles || ['editorial']
// Only ivory has a build kit, and run.py refuses a project built without one.
if (styles.some((s) => !KITS[s])) return styles.map((s) => ({ style: s, refused: true, reason: KITS[s] ? 'another style in this run has no build kit' : `${s} has no build kit: only ivory (editorial) does` }))
const out = await pipeline(
  styles,
  // 1. direct
  (s) => A.skipDirect === true && !A.planIssues?.length ? { skipped: true } : agent(`You are the director for the ${s} version of the recut in ${W}. ${inputs(s)}
${A.planIssues?.length ? `Plan-check issues: ${JSON.stringify(A.planIssues)}. Read and revise the existing plan.json and STORYBOARD.md to fix these issues; keep every event_id, including unchanged events. Do not replace the plan from scratch.` : ''}
${IMAGE_RULE}
Write ${W}/v2/${s}/plan.json and STORYBOARD.md in the format of ${REF}/plan.json / STORYBOARD.md: for every beat of beats.json the layout (${FF ? 'split / full-graphic / full-face' : 'split / full-graphic'}), the component, the exact asset + crop/zoom target (CSS px boxes from ASSETS.md), the landing word + time, the caption treatment, transitions. Each beat's anchor and every action must be an object with its own immutable event_id (for example b12.e1), t in composition seconds, and a separate editable description. Preserve existing event_ids through revisions; never renumber them when a description or time changes. Carry cta_start and each beat's proof_span [start, end] in composition seconds from beats.json into plan.json, with cta_start_source and proof_span_source. For older beats.json without those fields, derive them from words.json and sound.md: cta_start is the first CTA word's start (null with a reason only if no CTA); proof_span covers only audible product/demo evidence, null with a reason when absent. Record word indexes or clip path plus composition interval as the source. Muted screen footage under narration is not proof audio. The independent check must verify these derivations. ${PLAN_FIELDS} Do not author sfx_timeline, per-beat cues or sound.json: sound is a separate stage after picture approval. Compute the measured layout shares, beat lengths, face absence and static band from your plan and print the totals at the end of STORYBOARD.md: read-outs, never targets, since switching follows what is said. Use real plates and Chase's own clips; never invent numbers (facts.json only). In plan.json set ${FF_FIELDS}: motionlint reads it. Do not write index.html yet.`,
    { label: `direct:${s}`, phase: 'Direct', schema: DONE }),
  (d, s) => !d ? { d, c: null } : agent(`Independently re-check the ${s} plan ${W}/v2/${s}/plan.json + STORYBOARD.md (you did not write it) against ${W}/beats.json timings, ${ROOT}/styles/${s}/STYLE.md, ${ROOT}/styles/CALIBRATION.md and these rules. ${RULES}
${NOTE}
List only findings that would change a pixel, a sound, a timing or a fact. Wording in notes, reasons and flags is never a finding.
Sort them into two lists. issues are blockers only, the things that make the edit wrong: an on-screen number or claim not in facts.json; an asset that does not exist; a highlight, outline, underline, zoom or crop aimed at the wrong thing (a different element or line, not a few pixels off its target); beat timing that breaks the rules (gaps, overlaps, duration, cta_start or proof_span derivations); a layout or full-face rule broken; text placed over the content it points at so that content is hidden; a required plan field missing. warnings are everything else: easing, spacing, a hold or snap-back that looks a little off. Do not judge pixel placement, overflow, crop edges or alignment at all: geometry.py measures those on the built page. Warnings never block the build: the builder fixes them while building where cheap, and the review render shows the rest. When unsure which list, warn. Recompute duration against metadata.json, cta_start and proof_span against their word/clip sources and sound.md, layout shares, longest face absence, beat lengths, static risk, that every asset exists, every on-screen number is in ${W}/facts.json. ${FF_CHECK} Defects only: HOUSE.md's defect list and banned findings apply, so report no taste, redesign or "could be better" findings. Return ok (true only when issues is empty), issues and warnings, each an absolute fix. Do not edit files.`,
    { label: `plancheck:${s}`, phase: 'Direct', schema: PCHECK }).then((c) => ({ d, c })),
  // 2. build. A failed, missing or unclear plan check refuses here: issues go back to the planner, never to the builder.
  (r, s) => !planPassed(r) ? { ...r, refused: true } : agent(`You are the motion designer building ${W}/v2/${s} (HyperFrames). ${inputs(s)}
Plan: ${W}/v2/${s}/plan.json + STORYBOARD.md.${A.note ? `\n${A.note}` : ''}${r.c?.warnings?.length ? `\nPlan-check warnings, not blockers: ${JSON.stringify(r.c.warnings)}. Fix each while you build where it is cheap, and name any you left in self_review.` : ''}
Setup: python ${KIT}/new_project.py ${A.id}${FF ? ' --full-face' : ''}. It makes ${W}/v2/${s} from the kit: tools_local/ with the kit's build.py, hyperframes.json, package.json, meta.json, CLAUDE.md, fonts, GSAP, and hard links to ${W}/shared/* and the face and voice files.${FF ? '' : ' Leave face_full.mp4 out.'} On a retry Setup keeps all existing sources and links newly added shared assets; run it again after an asset is added. The kit's builder emits no cue <audio> tags and never reads sfx_timeline; the only audio element is the voice (id="voice", src="assets/voice.m4a"). Leave sound.json alone. Preserve all plan event_ids.
${BUILD_RULES}
HyperFrames contract: root data-composition-id="main", one paused timeline registered last on window.__timelines["main"], explicit ease+duration on every tween, fromTo, clips are elements with data-start + class="clip", never tween visibility on clips, media need ids and no crossorigin, voice from assets/voice.m4a, duration = ${W}/metadata.json duration.
QA loop (2-4 rounds, from the project folder): python tools_local/build.py (exit 0, and no WHOLE RENDER line you could fix) ; python ${S}/tools/beat_check/conform.py ${W}/v2/${s} --audit (exit 0: anything else and run.py renders nothing) ; python ${S}/tools/beat_check/conform.py ${W}/v2/${s} --all (before a render, exit 3 is expected for missing rendered references, with no FAIL lines; exit 0 is also valid. Fix every FAIL. Exit 4 means it never measured the page and stops this stage) ; python ${S}/tools/beat_check/geometry.py ${W}/v2/${s} (text overflow, elements off the frame, highlights off their target, crops slicing text, measured on the built page. ADVISORY for now (Chase, 2026-11-02, until it proves itself on two new builds): it never blocks the build and never earns an extra QA round. Fix a FAIL in the sources when you look at the frame and agree it is real; a FAIL you judge false (motion, an intentional bleed, a clipped counter), leave as built and name it with its frame in self_review. Record the exit code and counts in geometry_check, and list every FAIL you left, plus the WARN and UNVERIFIED findings, in self_review) ; npx hyperframes lint (0 errors) ; python ${S}/tools/motionlint.py index.html --pack ${s} (0 errors) ; npx hyperframes snapshot --at <~30 times: every beat anchor + mid-beat> --describe false -o snaps_build ; Read the contact sheets + key frames, compare with the donor evidence, fix. Do NOT render, no preview servers. Write only inside ${W}/v2/${s}.`,
    { label: `build:${s}`, phase: 'Build', schema: BUILT }).then((b) => ({ ...r, b })),
)
return out.map((r, i) => r && ({ style: styles[i], plan_check: r.c, build: r.b, refused: r.refused === true })).filter(Boolean)
