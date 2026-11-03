# Example: one approved ivory edit, text only

These are the text files from one real `/claude-edit` run (Chase's short on the Claude Max and Ultra rename, 2026-10-30). That edit went the whole way: cut listen, first edit, four note rounds, approval, sound and a delivered final. It is the before/after video in the README.

The workflows read this folder as a worked example of the file formats. They copy its shape, never its words or facts.

| File | What it shows |
|---|---|
| `beats.json` | The content plan: every beat's words, timing, anchor word, layout hint and assets |
| `facts.json` | Every number and claim that may go on screen, each with its source |
| `ASSETS.md` | The asset inventory: each file, its pixel size and the boxes a beat may zoom to |
| `shots.spec.json` | The screenshot list `tools/capture_cache.py` reads |
| `v2/editorial/plan.json`, `STORYBOARD.md` | The director's plan for the ivory build |
| `v2/editorial/tools_local/` | The scenes, timeline, owners and style the builders wrote from `templates/ivory/build_kit` |

No media ships: the footage, captures, clips and renders stay on Chase's machine. Paths inside these files (`work/1030-2/...`) name that original project and do not exist in this repo.
