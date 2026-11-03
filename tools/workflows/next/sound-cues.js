export const meta = {
  name: 'sound-cues-next',
  description: 'Write the final cue sheet after picture approval, then check its placement. Sound rules only; no art direction.',
  whenToUse: 'The picture in work/<id>/v2/editorial is approved, or Chase gave a sound-only note',
  phases: [
    { title: 'Sound', detail: 'sound.json against the approved plan and palette, then check-sheet' },
  ],
}

// args: { id: '1030-1', style: 'editorial', note: "Chase's sound note, if any" }
const A = args || {}
// The skill passes root (the project folder, absolute); a workflow cannot find it itself.
if (!A.root) throw new Error('pass root: the project folder as an absolute path (SKILL.md, intake)')
const S = String(A.root).replaceAll('\\', '/').replace(/\/+$/, '')
const ROOT = S
const W = `${ROOT}/work/${A.id}/v2/${A.style || 'editorial'}`
const T = `${ROOT}/templates/ivory`
const RULES = `In these prompts and rules, Chase (he, his) means the creator of this video, who runs this skill; a [Chase] tag records where a rule came from. RULES, read before you start: ${T}/sound.md, ${T}/sfx/sfx.json and ${T}/sfx/SOUNDS-LIKE.md. Start from the Strategy section: choose moments by attention job first, sounds second. Chase wins every conflict. These are the only art direction for this stage. No music. Special sounds require Chase's explicit request, traced in requested_by. The 8-per-30-s rate is a warning: it "just has to make sense". Do not add cues to meet a share or density target.`
const DONE = { type: 'object', properties: {
  files: { type: 'array', items: { type: 'string' } }, check_sheet: { type: 'string' }, notes: { type: 'string' },
}, required: ['files', 'check_sheet', 'notes'] }

return await agent(`Write ${W}/sound.json for the approved picture. Read ${W}/plan.json and any existing sound.json first. ${RULES}
${A.note ? `Chase's note: ${A.note}` : 'No special sound has been requested for this pass.'}
The sheet is {version: 1, picture_rev: "...", cues: [...], empty_reason: optional}. Get picture_rev by running python ${ROOT}/tools/sound_mix.py revision ${W}; never invent it. Each cue carries t, file, gain, event, stressed_word, at, media_start, dur, placement and event_id from an anchor or action in plan.json. Event times are composition seconds. requested_by is required for a special sound and quotes or identifies his request. If no event earns sound, write cues: [] and a concrete empty_reason.
Use only the palette's sliced wavs already available in ${W}/assets/sfx. Match levels per sound.md and sfx.json: tools/sound_mix.py voice_ref, level and attack measure the voice and slices; do not guess a common gain. Count source-file shares through sfx.json, not slice names. Respect CTA and proof spans, including audible tails. Preserve event_ids; never change the picture or plan to make sound pass.
Run python ${ROOT}/tools/sound_mix.py check-sheet ${W}. Fix sheet failures and re-run until PASS; return the actual output and every WARN/UNVERIFIED item. A missing event, missing media or a picture changing during this pass stops the stage and is reported. Do not render, mix, master or deliver; the skill runs check-mix and delivery after this stage. Write only sound.json.`,
  { label: 'sound-cues', phase: 'Sound', schema: DONE })
