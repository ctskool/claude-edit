export const meta = {
  name: 'gate-fix',
  description: 'Clear gate failures (static graphics-band holds / freezes) in rendered style projects without redesigning them',
  whenToUse: 'A render fails or warns on tools/gates.py static/freeze checks and only motion needs adding',
  phases: [{ title: 'Fix', detail: 'one agent per project: add on-word motion through every frozen window, QA' }],
}

// args: { root: '<absolute repo root>', items: [{ id: 'my-video', style: 'editorial', tag: 'v2' }, ...] }
const A = args || {}
if (!A.root) return { error: 'pass root: the absolute path of the claude-edit repo' }
const S = A.root.replace(/[\\/]+$/, '').replace(/\\/g, '/')
const DONE = { type: 'object', properties: { applied: { type: 'array', items: { type: 'string' } }, lint_errors: { type: 'number' }, motionlint: { type: 'string' } }, required: ['applied', 'lint_errors', 'motionlint'] }
const items = (args && args.items) || []
const out = await parallel(items.map((it) => () => {
  const P = `${S}/work/${it.id}/v2/${it.style}`
  return agent(`The render ${S}/out/${it.id}_${it.style}_${it.tag}.mp4 fails or warns on the static-band gate: read ${S}/out/${it.id}_${it.style}_${it.tag}-gates.json (frozen windows, static seconds per 30 s vs the pack target, longest hold) and look at the frames in those windows (ffmpeg select by frame index, or ${S}/out/evidence/${it.id}_${it.style}_${it.tag}).
In ${P} (HyperFrames; if tools_local/build.py exists edit tools_local sources and rerun it), make something visible move or land at least every 0.6 s through each frozen window, in the style's own vocabulary (${S}/styles/${it.style}/STYLE.md): e.g. a slow camera push/drift on the plate, a highlight sweep or outline on the line being spoken (words in ${S}/work/${it.id}/words.json), a cursor glide + click, a scroll to the next relevant line. Small-amplitude changes like typing a few characters do not count - the gate measures band-level change. Change nothing else.
QA: npx hyperframes lint (0 errors); python ${S}/tools/motionlint.py index.html --pack ${it.style} (0 errors); npx hyperframes snapshot --at <several times inside each window> --describe false -o snaps_gatefix ; Read them. Do NOT render. Write only inside ${P}.`,
    { label: `gatefix:${it.id}:${it.style}`, phase: 'Fix', schema: DONE }).then((r) => ({ ...it, r }))
}))
return out.filter(Boolean)
