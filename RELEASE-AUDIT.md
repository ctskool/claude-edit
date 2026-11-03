# Release audit: claude-edit v2

Audited 2026-11-03 for the v2 commit, the first since the public v1 (2026-10-29). Nothing has been pushed.

## Decisions Chase made for this release

- **Everything taken from the outside editor package may ship** (Chase, 2026-11-02, after its author said so). That includes `tools/flash_scan.py` and `tools/ffmpeg_compat.py`, so the flash check runs again.
- **No credit or attribution to people anywhere** (Chase, 2026-11-03). Rule tags that named people were removed: 61 of one name, 15, 4 and 3 of three others. `[Chase]` and `[Ours]` remain. No names appear in docs, code headers, `sfx.json` sources or commit messages. The reference creators stay anonymous as "reference creator A/B/C", without post IDs or video titles. A style key named after a creator became `dense`.
- **Licence notices only where the law needs them**, in `licenses/` with no prose: the OFL texts for the three shipped fonts (Inter, JetBrains Mono, Newsreader) and GSAP's notice. `THIRD_PARTY.md` is gone.

## Settled before the push (Chase, 2026-11-03)

- **GSAP:** the short header notice in `licenses/GSAP.txt` is enough. Nothing was downloaded.
- **Five sound slices dropped** (phone lock, vine boom, japanese wow, cash register, censor beep): their wav files, palette entries, audition records, rule rows and example mentions are gone from this repo. 72 slices remain. They stay in Chase's working project.
- **Old history removed:** the repo is one fresh root commit, so no commit holds v1's credit files. Forks, clones and GitHub's cache of unreferenced commits can still hold the old history.
- **Commit author:** the repo's configured identity, already public before.

## What ships

| Path | What |
|---|---|
| `.claude/skills/claude-edit/SKILL.md` | The skill, portable copy |
| `templates/` | House rules, story rules, the ivory template: `build_kit/`, `library/`, `CANDIDATES.md`, `sfx/` (72 slices plus 28 earshot sources; the two Pixabay sounds excluded) |
| `styles/` | The measured look behind ivory and its replica kits, anonymous |
| `tools/` | Only what the skill calls (import closure plus a resolver over the copy), and the tests for it |
| `examples/ivory-edit/` | Text files of the approved 1030-2 edit, the workflows' worked example |
| `references/` | How to measure your own reels. No reels ship |
| `media/`, `docs/`, `scripts/` | Banner, player screenshot and capture, the Pages gallery and its builders, all from 1030-2 |
| `README.md`, `INSTALL.md`, `PLAN.md`, `LICENSE` (MIT), `licenses/` | Docs and notices |

v1's files are not in this repo or its history.

## Scrub checks

| Item | Result |
|---|---|
| `work/` | Not shipped (git-ignored). The only 1030-2 content is the text example and the showcase media |
| Other creators' clips, frames, transcripts | None. Reference folders not copied; names, handles, post IDs and titles removed |
| Pixabay sounds | Not shipped; `tools/fetch_sounds.py` downloads them on each machine |
| Other people's animation cards, old look packs | Not shipped |
| Image services other than Codex | No mention in shipped files |
| Personal data | No emails, tokens or keys in files. The player screenshot and capture show Chase's face and his real notes on 1030-2 |
| Absolute paths from Chase's machine | None: `python tools/doctor.py` reports "portable paths: PASS" |
| Credits to people | None. A case-insensitive grep for the removed names, handles and post IDs finds nothing |

`INSTALL.md` links the optional Robust Video Matting install to its GitHub page. That is an install link, not a credit.

## Portability changes (share copy only)

`C:\Users\Chase\shorts` was not edited: `work/1102-1` is mid note round there.

- **The 2026-11-02 portability audit:** 143 of its replacements applied by script; 143 target files that don't ship; 18 done by hand because their text had changed (SKILL.md intake and retry lines, every workflow path).
- **Workflows** require `root`, use forward slashes, and read `examples/ivory-edit` instead of the author's own past projects.
- **`ownership.py` IGNORED** gains the parallel build's inputs (`tools_local/chunks/`, `plan.parts/`, `plan.lead.json`).
- **The skill** says Chase means the user. It opens the v2 player on port 4750 in its default look, and documents face-only takes.
- **Doctor** checks the example project and the shipped sound slices, and flags absolute paths from the author's machine.
- **Tests:** fixture-only tests skip with a reason, workflow stubs pass `root`, and stale expectations were updated. The sound-step render stub recognises the Mac-safe npm call; before this fix it fell through to a real render attempt.
- **`.gitignore`** anchors `/vendor/`, so the kit's `gsap.min.js` ships. A fresh clone caught this.

## Things a stranger will notice

- Rule files mention the author's private `reports/...` as evidence. These are provenance only: nothing runs them.
- `examples/ivory-edit` and the library's records name `work/1030-2`, which exists only on Chase's machine.
- The player header shows the `chase_ai_` wordmark.
