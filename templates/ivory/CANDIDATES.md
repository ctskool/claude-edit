# Candidates from Chase's notes

Proposals, not active rules. Only Chase marks keep or strike. An agent drafts from
`work/<id>/taste-digest.md`; the digest does not draft or approve anything.
Follow `references/HOW.md` and the numbered keep/strike list in
`references/<reference-slug>/taste.md`. Use ideas, not one video's wording.

## Format

Copy this block below `## Candidates`, replace the placeholders, and number each
candidate. Keep each field on one line. Quote his exact words as a JSON string
(escape embedded quotes as `\"`). Repeat the notes tag for every supporting note.
`Seen in` counts distinct video ids in the tags, never notes or beats. One video
is a candidate, not a rule; two or three videos make repeated taste visible.
Do not inflate the count or turn a dropped/undone note into an approved outcome.

```markdown
1. **When X, do Y.** [notes <id>: <beat>, "<exact note quote>"]
   Target: `templates/ivory/layout.md`
   Seen in: 1 video
   Why: <why this choice helps, grounded in the notes>
   Met when: <how a reviewer can tell it held>
   - [ ] keep [ ] strike
```

Use `video` for a note with no beat. Allowed targets: `templates/ivory/layout.md`,
`templates/ivory/captures.md`, `templates/ivory/captions.md`,
`templates/ivory/picker.md`, `templates/ivory/sound.md`, or `templates/HOUSE.md`.
Chase can edit the bold rule before keeping it. Mark `[x] keep` or `[x] strike`,
never both. `[seen]` and `[measured]` describe reference evidence; they never
approve a note candidate. `[Chase]` is added on promotion, with its date and the
original `[notes ...]` quotes. Only his keep promotes, even with one video's
evidence; the evidence count remains on the promoted rule.

After he marks: `python tools/taste_from_notes.py promote`. It moves kept entries
under `## From his notes` in their targets and removes struck entries. Unmarked
entries stay here and never reach an edit. A malformed list stops promotion.

## Candidates

