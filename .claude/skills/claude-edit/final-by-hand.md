Read this only when `autofinal.py` failed or cannot be used, he asks for 4K or for 60 fps on a project prepped before `face_half_4k.mp4` existed, or the sound sheet changes after a final. Otherwise his Approve click builds and delivers the 1080p30 final by itself, or the 4K30 one when he asked for 4K (`short-finish.md`, section 10).

It holds the by-hand part of section 10, moved here unchanged from `SKILL.md`. The final is built fresh from a frozen copy of the approved composition, never from the review picture, and never two renders at once.

## 1080p30 and 4K30

**1080p30 is the default final** [Chase, 2026-11-24: no platform plays a short above 1080p]. Its commands are below the 4K ones.

**4K30 only when he asks for it on this short** (a master to keep, a crop for long-form). From his Approve click: write `<work>/final.json` `{"spec": "4k30"}` before he approves, or run `autofinal.py start $P --spec 4k30` after. The final renders the same composition at 2160x3840. Prep already wrote `assets/face_half_4k.mp4` (the same frames as `face_half.mp4` at the source's full size), so nothing is re-cut. By hand: write `<work>/swaps-4k30.json` (`<work>` is `work/<id>`) pointing `assets/face_half.mp4` at it, with his approval words in `authorized_by`.
```bash
# {"swaps": [{"path": "assets/face_half.mp4", "file": "<work>/assets/face_half_4k.mp4", "source": "prep_source.py face_half_4k (same frame map)", "why": "4K30 final", "authorized_by": "<his approval, verbatim>"}]}
python tools/beat_review/final.py build $P --spec 4k30 --workers 6 --swaps <work>/swaps-4k30.json
python tools/deliver.py $P <base>_4k30 --mode final --stitched <file that build printed> --source-swap assets/face_half.mp4
python tools/sound_mix.py check-media out/<base>_4k30.mp4
```
On 1102-1 (85 s) the 4K30 build took 11 minutes at 6 workers (1080p30: about 3.5), and delivering it about 10 more. A project prepped before face_half_4k existed: make it with `tools/face_retime.py raw/cut.mp4 --map face_map.json --reuse --crop <metadata face crop> --scale <crop width>x-2 --out assets/face_half_4k.mp4`, never a plain `fps=30` (the swap check refuses frames a tick off). Clips from other skills keep their own size: a /vfx clip stays 1080x1920 and is scaled up. Don't swap in a `/vfx --4k` render: a full-frame 2160x3840 clip inside the composition renders with held frames (about half its frames repeated, found 2026-11-04), while the 1080 clip plays every frame. **1080p30**, the default (and the fallback if a 4K check fails):
```bash
python tools/beat_review/final.py build $P --spec 1080p30 --workers 4
python tools/deliver.py $P <base> --mode final --stitched <file that build printed>
python tools/sound_mix.py check-media out/<base>.mp4
```
`deliver.py` takes `$P`, never the bundle: approvals live in `$P`'s store. `build` freezes sources, plan, sound and assets to `work/<id>-final-<rev16>/` and proves the copy rebuilds byte for byte. `deliver.py` refuses a reviewed final without `--stitched`, and refuses a missing or stale sheet. It runs the output check on the delivered, mastered file. `check-media` checks only that file. The delivery manifest links the checks, picture and sheet hashes.
**A new sound sheet after a final.** Run `build` again. A bundle is never changed, so it makes `work/<id>-final-<rev16>-sound-<hash8>/`, the same picture by hard link with the new sheet, cue files and waiver lists, and renders 0 beats. Deliver the file it prints, under a new `<base>`. `deliver.py` refuses a picture from a bundle whose sheet or cue bytes are not `$P`'s, so the old sound cannot go out by accident.

After any final: send him a phone copy of the sounded file and wait for final approval (`short-finish.md`, section 10).

## 4K60

**4K60, only if he asks for 60 fps.** Say plainly first: no whole short from a raw has been built this way (4K30 has: 1102-1, 2026-11-03). It is a derivative revision with its own bundle, and `derivative.json` says exactly what changed. Same cut, audio and plan as approved.
```bash
# Rebuild face_half at 60 fps with ffmpeg from raw/cam_cut.mp4 (metadata.json camera_crops half) or,
# with no CAMERA file, raw/cut.mp4 (face_top_px, face_region). Real pixels only.
# Only when RUN.md has allow_full_face true: rebuild face_full the same way (camera_crops full), scaled to 2160x3840.
# With bottom popout: python tools/popout.py make $P --final writes both popout clips at 2x and work/<id>/swaps-popout.json.
#   Merge its rows into swaps.json and use them instead of face_half (popout pages don't use face_half).
# List each in swaps.json: {"swaps": [{path, file, source, why, authorized_by}]}. A swap needs his words in authorized_by.
python tools/beat_review/final.py build $P --spec 4k60 --workers 6 --swaps swaps.json
python tools/deliver.py $P <base>_4k60 --mode final --stitched <file that build printed> --source-swap <each swapped path, e.g. assets/face_half.mp4>
python tools/sound_mix.py check-media out/<base>_4k60.mp4
```
`--source-swap` lists the same paths as `swaps.json`, so leave it out only if that file lists none. It states what is expected and authorizes nothing. A new sound sheet at 4K60 is a whole 4K render, because rebinding makes the derivative's sheet its own.
- Screen clips and plates keep their preview size. With `allow_full_face` true, full-face punch-ins are real camera pixels scaled up about 1.9x. Tell him what applies.
- **If the render fails, or a check does not pass: say "the 4K60 final cannot be done yet". His approved file stays the 4K30 (or 1080p) final.** Never hand over a guess.
