export const meta = {
  name: 'gauntlet-panel',
  description: 'Panel critique+fix round per style: 3 lens critics on the encoded MP4, consolidation, adversarial verify, fix, independent regression check',
  whenToUse: 'One improvement round per style after renders exist in out/ with evidence packs (render happens outside, sequentially)',
  phases: [
    { title: 'Critique', detail: '3 independent critics per style (donor fidelity, motion+sync, phone viewer)' },
    { title: 'Consolidate', detail: 'lead director merges, dedupes and ranks the panel findings' },
    { title: 'Verify', detail: 'one skeptic per P0/P1 finding checks it against the frames (default: refuted)' },
    { title: 'Fix', detail: 'fixer applies verified findings, lint + motionlint + snapshot QA' },
    { title: 'Check', detail: 'independent checker confirms each fix landed and nothing regressed; one re-fix pass if not' },
  ],
}

// args: { root: '<absolute repo root>', video: 'my-video', prev: 'v1', next: 'v2', styles: ['editorial'], notes: {style: 'extra guidance'} }
// Reference reels are optional: drop 2-4 reels whose editing you want to match in reference/<style>/ (and run
// python tools/evidence.py on each into reference/<style>/evidence/<name>/); without them the critics judge against STYLE.md
// and the proven template.
const A = args || {}
if (!A.root) return { error: 'pass root: the absolute path of the claude-edit repo' }
if (!A.video) return { error: 'pass video: the work/<id> id' }
const VID = A.video
const S = A.root.replace(/[\\/]+$/, '').replace(/\\/g, '/')
const W = `${S}/work/${VID}`
const EXEMPLARS = {
  editorial: `${S}/styles/editorial/kit/editorial-chiefofstaff and editorial-vibecoding (measured component replicas) and the proven project ${S}/templates/editorial`,
}

const SCORES = { type: 'object', description: '1-10 vs the style spec and its reference reels (10 = indistinguishable from a top editor in this style)', properties: {
  style_fidelity: { type: 'number' }, layout_scale: { type: 'number' }, typography: { type: 'number' }, motion_feel: { type: 'number' },
  pacing_density: { type: 'number' }, transcript_sync: { type: 'number' }, polish: { type: 'number' }, overall: { type: 'number' } },
  required: ['style_fidelity', 'layout_scale', 'typography', 'motion_feel', 'pacing_density', 'transcript_sync', 'polish', 'overall'] }
const FINDING = { type: 'object', properties: {
  id: { type: 'string' }, severity: { type: 'string', enum: ['P0', 'P1', 'P2'] }, time: { type: 'string' }, frame: { type: 'number' },
  region: { type: 'string' }, defect: { type: 'string' }, evidence: { type: 'string', description: 'which files/frames show it, with measured numbers' },
  fix: { type: 'string', description: 'absolute target: px, s, hex, ease - never relative' } },
  required: ['severity', 'time', 'defect', 'fix'] }
const CRIT = { type: 'object', properties: {
  scores: SCORES, verdict: { type: 'string', enum: ['SHIP', 'ONE MORE PASS'] },
  findings: { type: 'array', items: FINDING }, biggest_gap_to_donor: { type: 'string' } },
  required: ['scores', 'verdict', 'findings', 'biggest_gap_to_donor'] }
const CONS = { type: 'object', properties: {
  findings: { type: 'array', items: FINDING, description: 'merged, deduped, ranked; ids F1..Fn' },
  conflicts: { type: 'array', items: { type: 'string' } }, biggest_gap_to_donor: { type: 'string' } },
  required: ['findings', 'biggest_gap_to_donor'] }
const VERDICT = { type: 'object', properties: {
  real: { type: 'boolean' }, measured: { type: 'string', description: 'what you actually saw/measured in the frames' },
  corrected_fix: { type: 'string', description: 'a better absolute fix if the proposed one is wrong or would break something; empty otherwise' } },
  required: ['real', 'measured'] }
const FIXED = { type: 'object', properties: {
  applied: { type: 'array', items: { type: 'string' } }, skipped: { type: 'array', items: { type: 'string' } },
  lint_errors: { type: 'number' }, motionlint: { type: 'string' }, snaps_dir: { type: 'string' } },
  required: ['applied', 'skipped', 'lint_errors', 'motionlint'] }
const CHECK = { type: 'object', properties: {
  landed: { type: 'array', items: { type: 'string' } },
  problems: { type: 'array', items: { type: 'object', properties: {
    time: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' } }, required: ['time', 'problem', 'fix'] } } },
  required: ['landed', 'problems'] }

const ours = (s) => `${S}/out/${VID}_${s}_${A.prev}.mp4`
const common = (s) => `OURS: ${ours(s)} (encoded render, 30 fps) ; evidence pack ${S}/out/evidence/${VID}_${s}_${A.prev}/ (INDEX.md, overview.jpg 1 fps, dense_*.jpg 5 fps, strip_*.jpg 10-frame strips at the biggest changes) ; gates ${S}/out/${VID}_${s}_${A.prev}-gates.json.
DONORS (the reference reels for this style): whatever is in ${S}/reference/${s}/ (reels + evidence/<name>/ packs) if that folder exists; otherwise the measured numbers in the spec and the proven template ${S}/templates/${s} stand in for the donor.
SPEC: ${S}/styles/${s}/STYLE.md (+ REFERENCE-ANALYSIS.md if present) and ${S}/styles/CALIBRATION.md. Content plan + facts: ${W}/beats.json ; words: ${W}/words.json.
Pull frames BY INDEX (ffmpeg -i X -vf "select='eq(n,N)'" -fps_mode vfr f.png), never by -ss guesses, and compare with the donor side by side at full res. Measure, don't eyeball: px sizes, hex colours, frame counts.
If STYLE.md has a "house rules" section, it OVERRIDES the donor numbers (e.g. more layout switching, varied sound design): judge those aspects against the house rules, not the donor.`

const LENSES = [
  { key: 'fidelity', brief: `LENS: DONOR FIDELITY. Would the donor's own editor sign this off as theirs? Compare layout shares, card scale/geometry, type (family, size, weight, tracking), palette, caption system, screen-content quality (crisp, purposeful, framed on the spoken line), signature devices and how often they appear. Name what the donor does that we don't, and what we do that the donor never would.` },
  { key: 'motion', brief: `LENS: MOTION + SYNC. Study the 10-frame strips and pull your own strips around every cut and entrance: easing curves, overshoot, blur, entry/exit choreography, cut placement vs the spoken word (words.json), caption timing (no strobe chunks < 9 frames), static holds and freezes (gates), dead frames, double-exposed transitions, jitter. Compare with donor strips frame by frame.` },
  { key: 'viewer', brief: `LENS: FIRST-TIME PHONE VIEWER + QA. Downscale to 360 px wide and watch it as a scroller would: is every on-screen word legible, is anything cluttered, clipped, colliding, unreadable or ugly, does the face ever look fake (matte edges, halos, smears), are screenshots soft/upscaled, are there typos or invented numbers not in beats.json facts/transcript, does the hook stop the scroll, is the ending CTA strong? Then audit polish frame by frame at full res.` },
]

const styles = A.styles || ['editorial']
const results = await pipeline(
  styles,
  // 1. three independent lens critics
  (s) => parallel(LENSES.map((L) => () => agent(`You are a harsh, independent motion director. You did NOT build this. Judge the ${s} version of this short against the donor (reference reels or, without them, the spec + proven template).
${common(s)}
${L.brief}
Return scores (10 = indistinguishable from the donor's editor), verdict, and at most 12 findings ranked P0/P1/P2, each with time, frame index, region, evidence (files + measured numbers) and an ABSOLUTE fix target. Do not edit files.`,
    { label: `critic:${s}:${L.key}`, phase: 'Critique', schema: CRIT }))).then((cs) => cs.filter(Boolean)),
  // 2. consolidate
  (crits, s) => {
    if (!crits || !crits.length) return null
    const overall = crits.map((c) => c.scores.overall)
    const mean = Math.round((overall.reduce((a, b) => a + b, 0) / overall.length) * 100) / 100
    return agent(`You are the lead director for the ${s} version. Three independent critics (lenses: ${crits.length === 3 ? 'donor fidelity, motion+sync, phone viewer' : 'mixed'}) judged ${ours(s)}.
Their reports: ${JSON.stringify(crits)}
Merge them into ONE ranked list (at most 14): dedupe findings that name the same defect (keep the most precise evidence and fix), resolve conflicting fixes by checking the donor evidence and the spec (${S}/styles/${s}/STYLE.md), re-rank severity (P0 = broken/wrong, P1 = clearly below the donor, P2 = polish). Give ids F1..Fn. Every fix must be an absolute target. You may pull frames to settle a conflict. Do not edit files.`,
      { label: `lead:${s}`, phase: 'Consolidate', schema: CONS }).then((cons) => cons && { style: s, crits, mean, cons })
  },
  // 3. adversarial verify of every P0/P1 (P2 pass through unverified)
  (r, s) => {
    if (!r) return null
    const hi = r.cons.findings.filter((f) => f.severity !== 'P2')
    return parallel(hi.map((f) => () => agent(`Skeptic check for the ${s} render ${ours(s)}. A critic claims:
${JSON.stringify(f)}
Pull the exact frames by index (ffmpeg select eq(n,N), plus neighbours) and the donor evidence it cites, and decide whether the defect is REAL as stated. Default to real=false if you cannot see it in the frames. Also judge the proposed fix: if it is wrong, would break another beat, or contradicts ${S}/styles/${s}/STYLE.md, give a corrected absolute fix. Do not edit files.`,
      { label: `verify:${s}:${f.id || f.time}`, phase: 'Verify', schema: VERDICT }).then((v) => ({ ...f, verdict: v }))))
      .then((vs) => {
        const verified = vs.filter(Boolean).filter((f) => f.verdict && f.verdict.real)
          .map((f) => ({ ...f, fix: (f.verdict.corrected_fix && f.verdict.corrected_fix.trim()) || f.fix }))
        const refuted = vs.filter(Boolean).filter((f) => !(f.verdict && f.verdict.real))
        const p2 = r.cons.findings.filter((f) => f.severity === 'P2')
        log(`${s}: panel mean ${r.mean}; ${verified.length} verified P0/P1, ${refuted.length} refuted, ${p2.length} P2 unverified`)
        return { ...r, verified, refuted, p2 }
      })
  },
  // 4. fix
  (r, s) => {
    if (!r) return null
    return agent(`You are the motion designer who owns ${W}/v2/${s} (HyperFrames project; if tools_local/build.py exists, index.html is GENERATED from tools_local/template.html + plan.json - edit those sources and rerun python tools_local/build.py).
A 3-critic panel judged the ${A.prev} render; the lead consolidated it and skeptics verified each P0/P1 against the frames.
VERIFIED (apply ALL, highest first): ${JSON.stringify(r.verified)}
P2 polish (apply the cheap ones that are clearly right): ${JSON.stringify(r.p2)}
Biggest gap to the donor: ${r.cons.biggest_gap_to_donor}
${(A.notes && A.notes[s]) || ''}
Change only what each finding names; keep what already matches. Keep everything HyperFrames-safe (one paused timeline registered last, explicit ease+duration on every tween, fromTo, no visibility tweens on clips, media ids, full-face video with data-media-start = data-start). Never put a number on screen that is not in beats.json facts or the transcript.
Style law: ${S}/styles/${s}/STYLE.md; proven component code: ${EXEMPLARS[s] || `${S}/templates/${s}`}.
QA: npx hyperframes lint (0 errors) ; python ${S}/tools/motionlint.py index.html --pack ${s} (0 errors) ; npx hyperframes snapshot --at <every time named in the findings + 15 more spread over the video> --describe false -o snaps_${A.next}
then Read the contact sheet and the frames for every fix to confirm it. Do NOT render, no preview servers, no network. Write only inside ${W}/v2/${s}.`,
      { label: `fix:${s}:${A.next}`, phase: 'Fix', schema: FIXED }).then((fixed) => ({ ...r, fixed }))
  },
  // 5. independent regression check (+ one re-fix pass)
  (r, s) => {
    if (!r || !r.fixed) return r
    return agent(`Independent QA for ${W}/v2/${s} after a fix pass (you did not make it). The fixer reports: ${JSON.stringify(r.fixed)}
The findings it was asked to fix: ${JSON.stringify(r.verified.map((f) => ({ id: f.id, time: f.time, fix: f.fix })))}
Take fresh snapshots (npx hyperframes snapshot --at <each finding time + 12 times spread over the whole video> --describe false -o snaps_${A.next}_qa) and compare against the previous render at the same times (frames by index from ${ours(s)}).
For each finding say whether the fix landed as specified (measure). List any NEW problem (regressions: overlaps, clipped text, empty frames, broken timing, lint/motionlint errors) with an absolute fix. Do not edit files.`,
      { label: `check:${s}`, phase: 'Check', schema: CHECK }).then((check) => {
      if (!check || !check.problems.length) return { ...r, check }
      return agent(`You own ${W}/v2/${s}. Independent QA found these problems after the last fix pass: ${JSON.stringify(check.problems)}
Fix each (same rules: edit tools_local sources + rerun build.py if it exists; HyperFrames-safe; lint 0 errors; motionlint --pack ${s} 0 errors; snapshot the affected times into snaps_${A.next}_refix and Read them to confirm). Do NOT render. Write only inside ${W}/v2/${s}.`,
        { label: `refix:${s}`, phase: 'Check', schema: FIXED }).then((refix) => ({ ...r, check, refix }))
    })
  },
)
return results.filter(Boolean).map((r) => ({
  style: r.style, panel_scores: r.crits.map((c) => c.scores), mean_overall: r.mean,
  verdicts: r.crits.map((c) => c.verdict), biggest_gap: r.cons.biggest_gap_to_donor,
  verified: r.verified.map((f) => `${f.severity} ${f.time}: ${f.defect}`), refuted: r.refuted.map((f) => `${f.severity} ${f.time}: ${f.defect} | ${f.verdict && f.verdict.measured}`),
  fixed: r.fixed, check: r.check, refix: r.refix,
}))
