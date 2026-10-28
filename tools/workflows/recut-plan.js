export const meta = {
  name: 'recut-plan',
  description: 'Motion-recut steps 2-3 for a new recording: verified facts, real screenshots + own-footage clips, style-agnostic beats.json, independent check',
  whenToUse: 'After tools/prep_source.py + words.json exist for work/<id>',
  phases: [
    { title: 'Research', detail: 'facts with sources + the on-screen story of the source recording' },
    { title: 'Assets', detail: 'screenshots (capture_shots.py), own-footage clips, logos, ASSETS.md' },
    { title: 'Plan', detail: 'beats.json (style-agnostic content plan)' },
    { title: 'Check', detail: 'independent plan check, then one revision pass' },
  ],
}

// args: { root: '<absolute repo root>', id: 'my-video', source: '<absolute path of the video>', hints: ['https://github.com/owner/repo', ...] }
const A = args || {}
if (!A.root) return { error: 'pass root: the absolute path of the claude-edit repo' }
const S = A.root.replace(/[\\/]+$/, '').replace(/\\/g, '/')
const W = `${S}/work/${A.id}`
const REF = `${S}/templates/editorial`

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

phase('Research')
const facts = await agent(`You are the researcher for a motion-graphics recut of the creator's short ${A.source} (work dir ${W}).
Transcript with word timings: ${W}/words.json. Read ${W}/metadata.json: layout "split" = the part of the source above face_top_px is the creator's own screen recording and the face cam is below it; layout "camera" = a plain talking-head take with no screen recording.
1) Split layout: watch the screen part - pull frames (ffmpeg -ss T -i "<source>" -frames:v 1 -vf "crop=iw:<face_top_px>:0:0,scale=540:-2") every ~1.5 s and describe what is on screen by time (source_story). Camera layout: source_story = what the speaker does / holds up, by time (often one entry).
2) Identify every product, repo, site and claim that is spoken or shown. Hints: ${JSON.stringify(A.hints || [])}.
3) Verify each claim on the live web (WebFetch / WebSearch; GitHub pages and APIs are fine): exact repo name/owner, license, stars/forks (say "as of <date>"), what it does (feature list in its own words), whether it really has an MCP server and a desktop app, what it is an alternative to, and any "fastest-growing" style claim (only count it verified if a page you can cite shows it, e.g. GitHub trending, a star-history or a 'repository of the day' badge in the README).
4) List the pages worth capturing as crisp plates (README hero, feature list, MCP section, app screenshots in the README, the alternative's own homepage hero) with a short name each.
Never invent numbers. Write nothing except ${W}/facts.json (the same object you return).`,
  { label: 'research', phase: 'Research', schema: FACTS })
if (!facts) return { error: 'research failed' }

phase('Assets')
const assets = await agent(`You are the asset wrangler for ${W}. Research result: ${JSON.stringify(facts)}
Follow ${S}/.claude/skills/claude-edit/SKILL.md section 3:
- mkdir ${W}/shared ; copy ${S}/assets/fonts, ${S}/assets/sfx and ${S}/assets/vendor into ${W}/shared/ as-is (setup.py fills them); logos: ${S}/node_modules/simple-icons/icons/<slug>.svg into ${W}/shared/logos (only real brand marks that exist there).
- Screenshots: write ${W}/shots.spec.json (format: ${REF}/shots.spec.json - name, url, theme light AND dark for GitHub pages, width 1280, height, optional element selector / full_page / hide) for every capture item, then run: python ${S}/tools/capture_shots.py ${W}/shared/shots ${W}/shots.spec.json . Re-check every PNG by reading it: crisp, no cookie banners/login walls, right content. Crop huge full-page captures to the needed region. Never screenshot Google/search UIs.
- Pick the source per asset as in SKILL.md "Pick the source per asset": public pages -> capture_shots.py; a shot it marks WALL (sign-in wall, e.g. X / LinkedIn) is never kept - posts behind a sign-in are read in the signed-in in-app browser (mcp__Claude_Browser__* tools, if you have them: text with emoji, time, avatar, media URLs, stats) and rebuilt with python ${S}/tools/post_card.py <spec.json> ${W}/shared/posts/<name>.png; without those tools use a frame of the creator's recording. Never show anything of the signed-in user's own account; drop post media that carries numbers facts.json rules out.
- Split layout only: the creator's own screen recording is real footage - cut 3-6 short clips (2-4 s each) of the most useful screen moments from the TOP part of ${A.source} (crop to the screen area only - above the seam/captions, check frames), re-encoded muted, 30 fps, -g 15, ~960 px wide, into ${W}/shared/clips/ with descriptive names.
- Write ${W}/ASSETS.md like ${REF}/ASSETS.md: every file with pixel size, what it shows and regions of interest (CSS px boxes for the lines/sections a beat will zoom or highlight - the capture tool writes per-shot box JSON you can use).
Return the list of files you wrote and notes (anything that failed or looks weak).`,
  { label: 'assets', phase: 'Assets', schema: DONE })

phase('Plan')
const planPrompt = (extra) => `You are the content planner (Claude) for the recut in ${W}. Write ${W}/beats.json - STYLE-AGNOSTIC (it is rendered through every style and format).
Follow ${S}/.claude/skills/claude-edit/SKILL.md section 2 exactly and copy the schema of the proven example ${REF}/beats.json (video, duration, topic, facts, beats[] with id, start, end, words [i0,i1], say, shape, anchor {word, t, what}, copy, assets, layout_hint, hint_why, emphasis?, note?).
Inputs: words ${W}/words.json (timings are truth), facts ${W}/facts.json, assets ${W}/ASSETS.md + ${W}/shared, metadata ${W}/metadata.json.
Rules: beats break on phrase boundaries, 1.1-3 s each, cover 0 to the end with no gaps; every spoken list item ("create voices, clone voices, voice editing") gets its own beat; the first frame is on-topic (no empty intro); anchors are the exact word index + its start time where the visual must land; copy uses only verified facts (facts.json) or the transcript - never invent numbers; give EVERY beat a layout_hint from what is being said - 'face' (the creator's opinion / emphasis, direct address, a rhetorical question, the payoff, the CTA, or covering a visible jump cut), 'takeover' (the visual IS the point and needs the whole frame: a name reveal, A vs B, a list of 3+, a big number, a before-after, a demo clip) or 'split' (the speaker explains or points at what is on screen; setup and connective lines) - plus a short hint_why quoting the trigger; switches only where a line earns them, no two within ~1.2 s, and if one hint holds past ~8 s look for a line that earns a break (never invent one); mark emphasis on the strongest face/takeover beats and the payoff line; every beat names the real asset(s) that carry it (prefer real plates and the creator's own clips over rebuilt mock UI).
Visuals: read ${S}/styles/VISUAL_MENU.md and give EVERY beat a visual {type, why} picked by its rules from what the line means (real_shot, own_clip, number, compare, diagram, list, scene, face, text; first rule that fits wins; why quotes the trigger words and says why higher-priority types do not fit). Abstract / metaphor lines with nothing real to show may get a scene block {idea, metaphor, prompt, overlay} - at most ${A.maxScenes ?? 3}, never two in a row, never replacing a fact's evidence; prompts follow the scene look in VISUAL_MENU.md and contain no logos, people or text.
${extra || ''}
${A.jumpcuts ? `Visible face-cam jump cuts on this timeline (seconds, from tools/rawcut.py times): ${JSON.stringify(A.jumpcuts)}. Each one must be hidden: a beat with layout_hint 'face' (punch-in) or 'takeover' must START exactly at that time (hint_why: "covers jump cut at <t>"), or the cut must fall inside a takeover that is already on screen.` : ''}
Validate the JSON parses. Return the files you wrote and notes.`
const plan1 = await agent(planPrompt(''), { label: 'plan', phase: 'Plan', schema: DONE })

phase('Check')
const check = await agent(`Independent check of the content plan ${W}/beats.json (you did not write it) against ${W}/words.json, ${W}/facts.json, ${W}/ASSETS.md and the rules in ${S}/.claude/skills/claude-edit/SKILL.md section 2 (compare with the proven ${REF}/beats.json).
Recompute: coverage 0..end with no gaps/overlaps, beat lengths 1.1-3 s, word ranges contiguous and matching 'say', anchor word index/time match words.json, every list item has its own beat, every beat has a layout_hint whose hint_why is really in the line (no quota - judge each switch on its trigger), first frame on-topic, every number/claim on screen is in facts.json (with a source) or spoken, every referenced asset file exists in ${W}/shared, 1-3 emphasis beats. Also judge as a motion director: would each beat's shape make a strong visual for that line?
Return ok + issues with absolute fixes. Do not edit files.`, { label: 'check', phase: 'Check', schema: ISSUES })
let plan2 = null
if (check && !check.ok && check.issues.length) {
  plan2 = await agent(planPrompt(`REVISION: an independent checker found these issues in the current ${W}/beats.json - fix every one: ${JSON.stringify(check.issues)}`),
    { label: 'plan-revise', phase: 'Check', schema: DONE })
}
return { facts, assets, plan: plan1, check, revision: plan2 }
