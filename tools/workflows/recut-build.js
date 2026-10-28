export const meta = {
  name: 'recut-build',
  description: 'claude-edit step 4 for a new recording: per style, direct (plan vs the style targets), build from the proven template + kits, QA, independent art-director pass, apply',
  whenToUse: 'After recut-plan (beats.json, facts.json, ASSETS.md, shared/) and tools/prep_source.py (assets/face_*) are done for work/<id>',
  phases: [
    { title: 'Direct', detail: 'plan.json + STORYBOARD.md against the measured style targets, independently re-checked' },
    { title: 'Build', detail: 'compose index.html from the proven template + kits; lint, motionlint, snapshot QA' },
    { title: 'Review', detail: 'independent art director scores snapshots vs the template / reference frames; builder applies the fixes' },
  ],
}

// args: { root: '<absolute repo root>', id: 'my-video', styles: ['editorial'] }
// Reference reels are optional: reels whose editing you want to match go in reference/<style>/ (evidence packs from
// python tools/evidence.py in reference/<style>/evidence/<name>/). Without them the template is the target.
const A = args || {}
if (!A.root) return { error: 'pass root: the absolute path of the claude-edit repo' }
const S = A.root.replace(/[\\/]+$/, '').replace(/\\/g, '/')
const W = `${S}/work/${A.id}`
const T = (s) => `${S}/templates/${s}`
const KITS = {
  editorial: `${S}/styles/editorial/kit/editorial-chiefofstaff and editorial-vibecoding (measured replica components)`,
}
const refs = (s) => `reference reels for this style, if the user added any: ${S}/reference/${s}/ (evidence packs in its evidence/ folder); otherwise the proven template ${T(s)} is the visual target`

const DONE = { type: 'object', properties: { files: { type: 'array', items: { type: 'string' } }, notes: { type: 'string' } }, required: ['files', 'notes'] }
const PCHECK = { type: 'object', properties: { ok: { type: 'boolean' }, issues: { type: 'array', items: { type: 'string' } } }, required: ['ok', 'issues'] }
const BUILT = { type: 'object', properties: {
  lint_errors: { type: 'number' }, motionlint: { type: 'string' }, snaps_dir: { type: 'string' },
  self_review: { type: 'string', description: 'what you checked in the contact sheets and what still looks weak' } },
  required: ['lint_errors', 'motionlint', 'snaps_dir', 'self_review'] }
const AD = { type: 'object', properties: {
  scores: { type: 'object', properties: { fidelity: { type: 'number' }, polish: { type: 'number' }, overall: { type: 'number' } }, required: ['fidelity', 'polish', 'overall'] },
  fixes: { type: 'array', items: { type: 'object', properties: { time: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' } }, required: ['time', 'problem', 'fix'] } } },
  required: ['scores', 'fixes'] }

const inputs = (s) => `Content plan (truth for timing + copy): ${W}/beats.json (each beat's visual {type, why} is the picked visual - build that type; scene beats use the generated image ${W}/shared/scenes/<beat>.png with their scene.overlay laid on top, per the style's Scene component; generate any missing scene image first as in ${S}/styles/VISUAL_MENU.md) ; words ${W}/words.json ; verified facts ${W}/facts.json ; assets ${W}/ASSETS.md (+ ${W}/shared/shots, clips, logos, fonts, sfx, vendor) ;
face footage in ${W}/assets: face_half.mp4 (the face cam for the bottom half - SPLIT SCREEN in every style, no person cut-out / head break-out), face_full.mp4 (1080x1920 plain crop for full-face beats, data-media-start = data-start), voice.m4a.
Brand: ${S}/config/profile.json (falls back to ${S}/config/profile.example.json) - the style keeps its own palette unless the profile sets style_overrides.${s}.
Style law: ${S}/styles/${s}/STYLE.md (+ REFERENCE-ANALYSIS.md) and ${S}/styles/CALIBRATION.md (measured targets). Donor: ${refs(s)}.
PROVEN TEMPLATE (8 critic rounds, the best code we have for this style - reuse its CSS, components, helpers, caption system, layout runs; only the content changes): ${T(s)} (index.html; its STORYBOARD.md / plan.json / beats.json show how a plan maps to code; its media are not shipped, so it does not render as-is). Measured components: ${KITS[s] || 'see STYLE.md'}.`

const styles = A.styles || ['editorial']
const out = await pipeline(
  styles,
  // 1. direct
  (s) => agent(`You are the director for the ${s} version of the recut in ${W}. ${inputs(s)}
Write ${W}/v2/${s}/plan.json and STORYBOARD.md in the format of ${T(s)}/plan.json / STORYBOARD.md: for every beat of beats.json the layout (split / full-graphic / full-face), the component, the exact asset + crop/zoom target (CSS px boxes from ASSETS.md), the landing word + time, the caption treatment, transitions. Hit the measured layout shares, beat lengths, face-absence limits and static-band target for ${s} (compute them from your plan and print the totals at the end of STORYBOARD.md). Use real plates and the creator's own clips; never invent numbers (facts.json only). Do not write index.html yet.`,
    { label: `direct:${s}`, phase: 'Direct', schema: DONE }),
  (d, s) => agent(`Independently re-check the ${s} plan ${W}/v2/${s}/plan.json + STORYBOARD.md (you did not write it) against ${W}/beats.json timings, ${S}/styles/${s}/STYLE.md and ${S}/styles/CALIBRATION.md: recompute layout shares, longest face absence, beat lengths, static risk, that every asset exists, every on-screen number is in ${W}/facts.json. Return ok + issues (absolute fixes). Do not edit files.`,
    { label: `plancheck:${s}`, phase: 'Direct', schema: PCHECK }).then((c) => ({ d, c })),
  // 2. build
  (r, s) => agent(`You are the motion designer building ${W}/v2/${s} (HyperFrames). ${inputs(s)}
Plan: ${W}/v2/${s}/plan.json + STORYBOARD.md. Plan-check issues to resolve while building: ${JSON.stringify(r.c ? r.c.issues : [])}
Setup: copy ${T(s)}/{hyperframes.json, package.json, CLAUDE.md} and write meta.json {"id": "${A.id}-${s}", "name": "${A.id}-${s}"}. Populate ${W}/v2/${s}/assets by hard-linking (os.link; fall back to a copy) from ${W}/shared/* and ${W}/assets/* - assets/sfx, assets/fonts, assets/vendor, assets/shots, assets/clips, assets/logos, assets/face_*.mp4, assets/voice.m4a (the paths the template's index.html uses).
Build the composition from the plan, reusing the template's code wherever the same component appears. HyperFrames contract: root data-composition-id="main", one paused timeline registered last on window.__timelines["main"], explicit ease+duration on every tween, fromTo, clips are elements with data-start + class="clip", never tween visibility on clips, media need ids and no crossorigin, full-face videos with data-media-start = data-start, voice from assets/voice.m4a, duration = ${W}/metadata.json duration.
QA loop (2-4 rounds): npx hyperframes lint (0 errors) ; python ${S}/tools/motionlint.py index.html --pack ${s} (0 errors) ; npx hyperframes snapshot --at <~30 times: every beat anchor + mid-beat> --describe false -o snaps_build ; Read the contact sheets + key frames, compare with the donor, fix. Do NOT render, no preview servers. Write only inside ${W}/v2/${s}.`,
    { label: `build:${s}`, phase: 'Build', schema: BUILT }).then((b) => ({ ...r, b })),
  // 3. independent art director + apply
  (r, s) => agent(`You are an independent art director (you did not build this). Judge ${W}/v2/${s} for the ${s} style: take fresh snapshots (npx hyperframes snapshot --at <30 times spread over the video + every beat anchor in ${W}/v2/${s}/plan.json> --describe false -o snaps_ad) and compare with the donor (${refs(s)}) for type, scale, layout, colour, screen-content quality, caption system, empty space, collisions, legibility at 360 px wide, invented numbers (${W}/facts.json only).
Return scores (1-10) and at most 14 fixes with absolute targets. Do not edit files.`,
    { label: `ad:${s}`, phase: 'Review', schema: AD }).then((ad) => {
    if (!ad || !ad.fixes.length) return { ...r, ad }
    return agent(`You own ${W}/v2/${s}. An independent art director scored it ${JSON.stringify(ad.scores)} and asks for: ${JSON.stringify(ad.fixes)}
Apply every fix (HyperFrames-safe; lint 0 errors; motionlint --pack ${s} 0 errors; snapshot the affected times into snaps_ad_fix and Read them to confirm). Do NOT render. Write only inside ${W}/v2/${s}.`,
      { label: `apply:${s}`, phase: 'Review', schema: BUILT }).then((applied) => ({ ...r, ad, applied }))
  }),
)
return out.map((r, i) => r && ({ style: styles[i], plan_check: r.c, build: r.b, ad: r.ad, applied: r.applied })).filter(Boolean)
