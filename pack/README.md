# pack/: three Creator Skill Pack formats

These three skills come from the **Creator Skill Pack**. They are redistributed here with the permission of the
pack's author. They are **not** covered by this repo's MIT licence: please don't republish them on their own.

| menu name | key | skill |
|---|---|---|
| rotation | `business` | `business-short-form-reels/` |
| frost | `glass` | `glass-explainer-reel/` |
| popout | `panel` | `explainer-panel-reel/` |

`setup.py` (or `python tools/import_formats.py`) copies them into `formats/`, applies the Windows /
macOS port rules, and fills their `@@PLACEHOLDERS@@` with your brand from `config/profile.json`. Edit your brand there,
not here; the files in `pack/` stay as the pack ships them.

The pack's other layout formats are not included.

## Changes from the pack

- `business-short-form-reels/examples/`: the three `*-final` worked reels were removed (another creator's videos). In
  the two kept examples (`scene-library-source`, `overlay-source`) and `assets/brand.css`, the original reel's title was
  replaced with a neutral one; `SKILL.md`, `README.md` and `templates/build.py` point at the kept examples.
- Nothing else is changed. The fonts in `*/assets/fonts/` (Playfair Display, Caveat) are SIL OFL 1.1
  ([licenses/OFL-1.1.txt](../licenses/OFL-1.1.txt)).
