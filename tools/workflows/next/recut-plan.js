export const meta = {
  name: 'recut-plan-next',
  description: '/claude-edit copy of recut-plan.js: same steps, but every agent also reads templates/HOUSE.md and templates/ivory/, and the plan check reports defects only',
  whenToUse: 'After tools/prep_source.py + words.json exist for work/<id>; runs while tools/face_pipeline.sh grinds in the background',
  phases: [
    { title: 'Research', detail: 'facts with sources + the on-screen story of the source recording' },
    { title: 'Assets', detail: 'screenshots (capture_cache.py), own-footage clips, logos, ASSETS.md' },
    { title: 'Plan', detail: 'beats.json (style-agnostic content plan)' },
    { title: 'Check', detail: 'independent plan check, then one revision pass' },
  ],
}

// args: { id: '1021-1', source: '<root>/work/<id>/raw/cut.mp4', hints: ['https://github.com/debpalash/VoiceStudio', ...], allowFullFace: false, allowFullFaceSource: 'template', codex: false, stage: 'all', words: '' }
// stage 'research' runs research and assets only, while Chase does the cut listen (words: raw/cut_words.json, since words.json comes after his answer).
// stage 'beats' then skips both and plans from the facts.json and ASSETS.md they wrote. 'all' (default) runs everything in one go.
// A workflow has no file access, so the skill resolves allowFullFace (default false) and its source (template or Chase's exact words) and passes both.
const A = args || {}
// The skill passes root (the project folder, absolute); a workflow cannot find it itself.
if (!A.root) throw new Error('pass root: the project folder as an absolute path (SKILL.md, intake)')
const S = String(A.root).replaceAll('\\', '/').replace(/\/+$/, '')
const ROOT = S
const W = `${ROOT}/work/${A.id}`
// No private prior-edit dependency: assets come from the ivory kit and this raw.
const T = `${ROOT}/templates`
// The example's text files only: beats.json, ASSETS.md, shots.spec.json. Its media does not ship.
const REF = `${ROOT}/examples/ivory-edit`
const NOTE = `In these prompts and rules, Chase (he, his) means the creator of this video, who runs this skill; a [Chase] tag records where a rule came from. Chase's intake notes (keep these through every stage): ${JSON.stringify(A.note || '')}`
const SPANS = `Sound boundaries come from the actual cut and sound.md: cta_start is the start of the first CTA word in words.json, or null only when there is no CTA. Record cta_start_source with that word index and exact quote, or the no-CTA reason. Each beat has proof_span [start, end] in composition seconds only while audible product/demo sound is the evidence, otherwise null. Record proof_span_source with the clip path and its composition interval, or the reason there is no proof audio (muted screen footage under narration is not proof audio). Never default these fields without reading the transcript and chosen media.`
// Full-face gate: only the Boolean true turns it on.
const FF = A.allowFullFace === true
// Image route. A generated scene needs Codex's image tool, so on plain Claude Code (the default) no beat is a scene.
const CODEX = A.codex === true
const SCENE_RULE = CODEX
  ? `Abstract / metaphor lines with nothing real to show may get a scene block {idea, metaphor, prompt, overlay} - at most ${A.maxScenes ?? 3}, never two in a row, never replacing a fact's evidence; prompts follow the scene look in captures.md and contain no logos, people or text.`
  : `This run has no image tool (Codex is not installed), so never pick scene: an abstract line with nothing real to show takes the next type in picker.md that fits (text, list, diagram or a built card).`
const FF_SOURCE = String(A.allowFullFaceSource || (FF ? 'not stated' : 'template'))
const FF_FIELDS = `allow_full_face to ${FF} (a JSON Boolean) and allow_full_face_source to ${JSON.stringify(FF_SOURCE)}`
const FF_RULE = FF
  ? `This run has allow_full_face true (source: ${JSON.stringify(FF_SOURCE)}): rules marked full_face on apply, and they win over any line saying a full-screen face is off or never.`
  : `This run has allow_full_face false (source: ${JSON.stringify(FF_SOURCE)}): every rule marked full_face on does not apply, so plan nothing from it. Only split and full-graphic takeover layouts exist, and Chase's face only ever sits in the bottom half.`
const LAYOUT_HINTS = FF
  ? `'takeover' (the visual IS the point and needs the whole frame: a name reveal, A vs B, a list of 3+, a big number, a before-after, a demo clip), 'face' (his opinion or emphasis, direct address, a rhetorical question, the payoff, the CTA or a visible jump cut, by the full-face rows in layout.md: a 1-2.5 s punch-in on assets/face_full.mp4) or 'split' (the default: he explains or points at what is on screen, setup and connective lines)`
  : `'takeover' (the visual IS the point and needs the whole frame: a name reveal, A vs B, a list of 3+, a big number, a before-after, a demo clip) or 'split' (the default: he explains or points at what is on screen, setup and connective lines, and also his opinions, direct address, rhetorical questions, the payoff and the CTA, on a quiet top panel with one big serif line) - NEVER 'face': a full-screen face is off for this run, Chase's face only ever sits in the bottom half`
const FACE_VISUAL = FF
  ? `Visual type face on a 'face' hint is the full-face layout; layout.md's full-face rows win over VISUAL_MENU.md's "never full screen".`
  : `Visual type face stays split with Chase in the bottom half, and its top half takes a real asset: a capture, his clip, the post, a returning graphic. Never only his words in big type, and never two quiet panels in a row. Only a CTA or a pure opinion hook may take a quiet panel. Nothing shown may read as proof of a claim no source supports.`
const JUMP_COVER = FF
  ? `a beat with layout_hint 'face' (a full-face punch-in) or 'takeover' must START exactly at that time (hint_why: "covers jump cut at <t>"), or the cut must fall inside a takeover that is already on screen. A cut inside a full-face hold is not covered.`
  : `a beat with layout_hint 'takeover' must START exactly at that time (hint_why: "covers jump cut at <t>"), or the cut must fall inside a takeover that is already on screen, or a split beat must start there with a quick punch-in inside the bottom half only (scale about 1.08), with hint_why "covers jump cut at <t> with a bottom-half punch-in".`
const HINT_CHECK = FF
  ? `'split', 'takeover' or 'face'`
  : `'split' or 'takeover' (a 'face' hint or any beat on assets/face_full.mp4 is a full-face beat and a defect)`
const rules = (...files) => `RULES, read these before you start: ${T}/HOUSE.md, ${files.map((f) => `${T}/ivory/${f}`).join(', ')} and ${ROOT}/styles/editorial/STYLE.md (layout numbers at 1080x1920). They win any conflict with SKILL.md, VISUAL_MENU.md or this prompt, and every [Chase] rule wins over the rest. Sections named "Trial ideas" are off. Open decisions stay open: keep current behaviour and flag them, never settle them. ${FF_RULE}`

const FACTS = { type: 'object', properties: {
  topic: { type: 'string' },
  facts: { type: 'object', additionalProperties: { type: 'string' }, description: 'key -> one verified claim with its source URL and the plate that shows it' },
  capture: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, url: { type: 'string' }, why: { type: 'string' } }, required: ['name', 'url', 'why'] } },
  source_story: { type: 'array', items: { type: 'object', properties: { t0: { type: 'number' }, t1: { type: 'number' }, shows: { type: 'string' } }, required: ['t0', 't1', 'shows'] }, description: 'what the screen half of the source recording shows, by time' },
  unverifiable: { type: 'array', items: { type: 'string' }, description: 'spoken claims that could not be verified - never put numbers for these on screen' } },
  required: ['topic', 'facts', 'capture', 'source_story', 'unverifiable'] }
const DONE = { type: 'object', properties: { files: { type: 'array', items: { type: 'string' } }, notes: { type: 'string' } }, required: ['files', 'notes'] }
const ISSUES = { type: 'object', properties: {
  ok: { type: 'boolean' },
  issues: { type: 'array', items: { type: 'object', properties: { beat: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' } }, required: ['beat', 'problem', 'fix'] } } },
  required: ['ok', 'issues'] }

const STAGE = ['research', 'beats'].includes(A.stage) ? A.stage : 'all'
const WORDS = A.words || `${W}/words.json`
let facts = { from: `${W}/facts.json` }, assets = { files: [], notes: `research stage ran earlier: read ${W}/ASSETS.md` }
if (STAGE !== 'beats') {
phase('Research')
facts = await agent(`You are the researcher for a motion-graphics recut of Chase's split-screen short ${A.source} (work dir ${W}).
${NOTE}
${rules('captures.md')}
Transcript with word timings: ${WORDS}. The top ~52% of the source is Chase's own screen recording; the bottom is his face cam with burned-in captions.
1) Watch the screen half: pull frames (ffmpeg -ss T -i "<source>" -frames:v 1 -vf "crop=iw:ih*0.52:0:0,scale=540:-2") every ~1.5 s and describe what is on screen by time (source_story).
2) Identify every product, repo, site and claim that is spoken or shown. Hints: ${JSON.stringify(A.hints || [])}.
3) Verify each claim on the live web (WebFetch / WebSearch; GitHub pages and APIs are fine): exact repo name/owner, license, stars/forks (say "as of <date>"), what it does (feature list in its own words), whether it really has an MCP server and a desktop app, what it is an alternative to, and any "fastest-growing" style claim (only count it verified if a page you can cite shows it, e.g. GitHub trending, a star-history or a 'repository of the day' badge in the README).
4) List the pages worth capturing as crisp plates (README hero, feature list, MCP section, app screenshots in the README, the alternative's own homepage hero) with a short name each.
Never invent numbers. Write nothing except ${W}/facts.json (the same object you return).`,
  { label: 'research', phase: 'Research', schema: FACTS })
if (!facts) return { error: 'research failed' }

phase('Assets')
assets = await agent(`You are the asset wrangler for ${W}. Research result: ${JSON.stringify(facts)}
${NOTE}
${rules('captures.md')}
Follow ${ROOT}/.claude/skills/claude-edit/SKILL.md section 3 and prepare this edit’s shared assets from the portable ivory kit:
- Create ${W}/shared/{fonts,vendor,sfx,logos}. Copy fonts and vendor from ${ROOT}/templates/ivory/build_kit/assets. Copy licensed prepared wavs from ${ROOT}/templates/ivory/sfx into shared/sfx. Logos come from ${ROOT}/node_modules/simple-icons/icons/<slug>.svg only when relevant to verified facts; do not copy a prior edit’s content.
- Screenshots: write ${W}/shots.spec.json (format: ${REF}/shots.spec.json - name, url, theme light AND dark for GitHub pages, width 1280, height, optional element selector / full_page / hide) for every capture item, then run: python ${S}/tools/capture_cache.py ${W}/shared/shots ${W}/shots.spec.json --max-age-days 7 (it reuses a matching capture younger than 7 days and captures the rest; for every CHECK line it prints, check the numbers on that plate against facts.json and record the result in ASSETS.md). Re-check every PNG by reading it: crisp, no cookie banners/login walls, right content. Crop huge full-page captures to the needed region. Never screenshot Google/search UIs.
- Pick the source per asset as in SKILL.md "Pick the source per asset": public pages -> capture_cache.py; a shot it marks WALL (sign-in wall, e.g. X / LinkedIn) is never kept - posts behind a sign-in are read in the signed-in in-app browser (mcp__Claude_Browser__* tools, if you have them: text with emoji, time, avatar, media URLs, stats) and rebuilt with python ${S}/tools/post_card.py <spec.json> ${W}/shared/posts/<name>.png; without those tools use a frame of Chase's recording. Never show anything of Chase's own account; drop post media that carries numbers facts.json rules out.
- Chase's own screen recording is real footage: cut 3-6 short clips (2-4 s each) of the most useful screen moments from the TOP part of ${A.source} (crop to the screen area only - above the seam/captions, check frames), re-encoded muted, 30 fps, -g 15, ~960 px wide, into ${W}/shared/clips/ with descriptive names.
- Write ${W}/ASSETS.md with every file with pixel size, what it shows and regions of interest (CSS px boxes for the lines/sections a beat will zoom or highlight - the capture tool writes per-shot box JSON you can use).
Return the list of files you wrote and notes (anything that failed or looks weak).`,
  { label: 'assets', phase: 'Assets', schema: DONE })
if (!assets) return { facts, assets, error: 'assets failed' }
if (STAGE === 'research') return { facts, assets, stage: 'research' }
}

phase('Plan')
const planPrompt = (extra) => `You are the content planner (Claude) for the recut in ${W}. Write ${W}/beats.json - content only (ivory's look lives in the rules below).
${NOTE}
${rules('picker.md', 'layout.md', 'captures.md', 'ledger.md')}
Follow ${ROOT}/.claude/skills/claude-edit/SKILL.md section 2 exactly, with ${REF}/beats.json as a worked example (another video's content: copy its shape, never its words), using this schema (video, duration, topic, facts, allow_full_face, allow_full_face_source, beats[] with id, start, end, words [i0,i1], say, shape, anchor {word, t, what}, copy, assets, layout_hint, hint_why, emphasis?, note?). In beats.json set ${FF_FIELDS}.
Inputs: words ${W}/words.json (timings are truth), facts ${W}/facts.json, assets ${W}/ASSETS.md + ${W}/shared, metadata ${W}/metadata.json.
Read ${T}/ivory/sound.md. ${SPANS}
Rules: beats break on phrase boundaries, 1.1-3 s each, cover 0 to the end with no gaps; every spoken list item ("create voices, clone voices, voice editing") gets its own beat; the first frame is on-topic (no empty intro); anchors are the exact word index + its start time where the visual must land; figures on graphics come only from facts.json and his quoted words only from the transcript - never invent numbers; give EVERY beat a layout_hint from what is being said - ${LAYOUT_HINTS} - plus a short hint_why quoting the trigger; switches only where a line earns them, no two within ~1.2 s, and if one hint holds past ~8 s look for a line that earns a break (never invent one); mark emphasis on the strongest ${FF ? 'face/takeover' : 'quiet-panel/takeover'} beats and the payoff line; every beat names the real asset(s) that carry it, and visual.why says which form it used (real capture or rebuilt card; which form is ivory's default is an open decision).
Visuals: read ${ROOT}/styles/VISUAL_MENU.md, the base of picker.md, and give EVERY beat a visual {type, why} picked by picker.md from what the line means (real_shot, own_clip, number, compare, diagram, list, scene, face, text; first rule that fits wins; why quotes the trigger words and says why higher-priority types do not fit). ${FACE_VISUAL} ${SCENE_RULE}
${extra || ''}
${A.jumpcuts ? `Visible face-cam jump cuts on this timeline (seconds, from tools/rawcut.py times): ${JSON.stringify(A.jumpcuts)}. Each one must be hidden: ${JUMP_COVER}` : ''}
Validate the JSON parses. Return the files you wrote and notes.`
const plan1 = await agent(planPrompt(''), { label: 'plan', phase: 'Plan', schema: DONE })
if (!plan1) return { facts, assets, plan: plan1, error: 'plan failed' }

phase('Check')
const check = await agent(`Independent check of the content plan ${W}/beats.json (you did not write it) against ${W}/words.json, ${W}/facts.json, ${W}/ASSETS.md and the rules in ${ROOT}/.claude/skills/claude-edit/SKILL.md section 2 (check every required schema field above).
${NOTE}
Verify the cta_start and proof_span fields and their sources against words.json, the chosen clips and ${T}/ivory/sound.md. ${SPANS}
${rules('picker.md', 'layout.md', 'captures.md', 'ledger.md')}
Recompute: beats.json sets ${FF_FIELDS}, coverage 0..end with no gaps/overlaps, beat lengths 1.1-3 s, word ranges contiguous and matching 'say', anchor word index/time match words.json, every list item has its own beat, every beat has a layout_hint of ${HINT_CHECK} whose hint_why is really in the line (no quota - judge each switch on its trigger), first frame on-topic, every figure on a graphic is in facts.json with a source and date and any quoted words are in words.json, every referenced asset file exists in ${W}/shared, 1-3 emphasis beats.${A.jumpcuts ? ` Every jump cut in ${JSON.stringify(A.jumpcuts)} has a cover: ${JUMP_COVER}` : ''} Defects only: HOUSE.md's defect list and banned findings apply, so report no taste, redesign or "could be better" findings.
Return ok + issues with absolute fixes. Do not edit files.`, { label: 'check', phase: 'Check', schema: ISSUES })
if (!check || typeof check.ok !== 'boolean' || !Array.isArray(check.issues)) return { facts, assets, plan: plan1, check, error: 'check failed or returned an invalid result' }
let plan2 = null
if (check.issues.length) {
  plan2 = await agent(planPrompt(`REVISION: an independent checker found these issues in the current ${W}/beats.json - fix every one: ${JSON.stringify(check.issues)}`),
    { label: 'plan-revise', phase: 'Check', schema: DONE })
  if (!plan2) return { facts, assets, plan: plan1, check, revision: plan2, error: 'plan revision failed' }
}
if (!check.ok && !check.issues.length) return { facts, assets, plan: plan1, check, error: 'check did not pass and gave no issues' }
return { facts, assets, plan: plan1, check, revision: plan2 }
