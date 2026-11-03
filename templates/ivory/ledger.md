# Ivory first-pass ledger

Build checklist: what a first render must not carry. One line each: the problem, then the fix.
In review, only "Chase's rules and rejections" and matches to `HOUSE.md`'s defect list count as defects.
Pruned 2026-11-02: 18 watch items went. Each repeated a rule kept elsewhere or was untested taste.
"(untested on ivory)" means ivory has not proven that line yet.
STYLE.md layout numbers here are at 1080x1920. Publish is 2160x3840, so double them there. Seam rows: `layout.md`.

## Chase's rules and rejections

- Sound repetitive, or the same file twice in a row -> one cue per event, rotate in class, no file over 25%. [Chase]
- A cue masking a stressed word -> soften it or drop it. [Chase]
- A long static opening split (27 s on the first finals) -> switch on what is said. [Chase]
- Switches added to hit a count -> no quota; past about 8 s look for a line that earns a break, never invent one. [Chase]
- Switches under about 1.2 s apart, or a mechanical S-G-S-G order -> space them and vary the order. [Chase]
- A top half that only repeats his words -> a real asset. [Chase]
- A full-face beat, or `face_full.mp4` in the composition, with `full_face` off -> split with a real asset on top; a jump cut gets a takeover or a punch-in inside the bottom half, about 1.08 scale. [Chase]
- With `full_face` on, full-face on setup or list lines -> face for opinion, emphasis, direct address, payoff, CTA, jump cuts. [Chase]
- A reveal, A vs B, list of 3+, big number or demo left small in split -> full-graphic takeover, 2-4 s. [Chase]
- A visible jump cut left bare -> cover it as `layout.md` sets out. [Chase]
- A black fade at the bottom of the frame -> run his body off the edge in real pixels; legibility comes from the chip. [Chase]
- Generated, stretched, mirrored or inpainted body pixels -> real crops and mattes only; if too tight, make him bigger or re-layout. [Chase]
- A cut-out or head breaking out of the panel -> plain split; not worth the squeeze. [Chase]
- A fake "test" slide -> a real artifact from the video. [Chase]
- A number not verified -> `facts.json` with source and date, or take it off the graphic and flag it. [Chase]
- Cut sounds too chopped -> keep the word tails; tail length is open below. [Chase]
- A device forced onto a video not built for it ("isn't really meant for tiers") -> use only what the script earns. [Chase]
- A Keep item drifted (ivory canvas, serif plus clay italic, rebuilt cards, seam chips, HUD, split face cam) -> restore it. The optional dark hook is flagged, not drift. [Chase]
- An image made anywhere but `codex exec`, or any generated person -> `codex exec` for images; no generated people. Without Codex, no generated images. [Chase]

## Our own defects

- A one-frame flash (box over the post card, 1023-test editorial v3, frame 129) -> flash scan every render. [Ours]
- A fixer slipping in a made-up price or counter -> re-check every number after every fix pass. [Ours]
- A beat over 1.5 s with nothing moving -> a real build keeps part of the panel moving, longest hold 2.5 s. Read text stays flat, with no rotation and no invented progress. [Ours]
- Face-cam judder on a 30 fps preview from a finished export -> `tools/face_retime.py` picks real frames. Check source cadence first. Never rate-convert the face layer in a 60 fps final. [Ours]
- Misheard names in the words -> correct them in `raw/corrections.json` before captions are built. [Ours]
- A chip off the composed seam, on his hair or below `HOUSE.md`'s y 1620 line -> measure each take; seam rows per `layout.md`. [Ours]
- A graphic outside y 120-880, x 60-1020 in split, or over his face -> keep it in the safe area. [Ours]
- A fade or border on the face cam, neon, glow, glassmorphism, non-flat gradients, word slams, emoji, shake, whip pans -> remove; hard edges and hard cuts. [Ours]
- Two italic clay words, green off a check mark, clay on over 10% of chips -> one italic word, green for checks only. [Ours]
- A sentence-case or animated caption -> mono uppercase chip, hard swap. [Ours]

## Open, Chase decides (not defects yet)

- Rebuilt cards stay the keep rule. Real captures versus rebuilt cards as ivory's default is flagged, not changed.
- Also open: whether isometric scenes stay, hook line moves, caption chunk length, tail padding, loudness target, the dark hook.
