// Builds the HyperFrames project for the whole video from tools/sections/*.mjs:
// one file per scene in compositions/, and index.html (stage, ASCII ground, face window, voice, scene hosts).
// Usage (from the project folder):  node tools/build.mjs            every section; also writes tools/sections.json
//                                   node tools/build.mjs --sections=02,03   only those (for working on a part)
//                                   node tools/build.mjs --range=128.717,184.833   one chapter of the video
//                                   node tools/build.mjs --partial     a pilot: the sections written so far, from 0
// A section file may `export const title = "Rule 2: make it prove its work"`. The full build writes
// tools/sections.json (file, title, start, end, in the times the sections were written with), which becomes the
// YouTube chapter list, and tools/slices.json: one render slice per scene, which render_slices.py renders and joins.
// A render keeps every frame of the face clip it covers on disk, and HyperFrames caps that at 2 GB, so the video is
// never rendered as one page. --range must start and end on scene boundaries.
import fs from "node:fs";
import { scenes, faces, cues, END, r3, mapT, CFG, clips, footage } from "./kit.mjs";

const want = (process.argv.find((a) => a.startsWith("--sections=")) || "").split("=")[1];
const range = (process.argv.find((a) => a.startsWith("--range=")) || "").split("=")[1];
// --reel=id,id,...  those scenes back to back in one page, each on whole frames, WITHOUT the face window and the voice:
// one HyperFrames call renders every designed slice, and render_slices.py cuts the result into slices and lays the
// face window over each with ffmpeg (as it does for footage slices). Only for slices whose window does not move.
const reel = (process.argv.find((a) => a.startsWith("--reel=")) || "").split("=")[1];
const noVoice = !!reel || process.argv.includes("--no-voice");   // slice renders never use the page's audio
// --range takes the times the sections were written with (as in tools/sections.json) and maps them to today's cut.
const [A0, B0] = range ? range.split(",").map(Number).map(mapT) : [0, END];
// A chapter's window is snapped to whole frames, so chapters join with no drift against the voice track.
const FPS = CFG.fps || 30;
// A scene that starts at t is first seen on frame ceil(t * FPS); every window (a slice, a chapter) is cut by that rule.
const TOTAL = Math.round(END * FPS), snapF = (x) => Math.min(Math.ceil(x * FPS - 1e-4), TOTAL);
const A = snapF(A0) / FPS, B = snapF(B0) / FPS;
const dir = new URL("./sections/", import.meta.url);
const files = fs.readdirSync(dir).filter((f) => f.endsWith(".mjs")).sort().filter((f) => !want || want.split(",").some((w) => f.startsWith(w)));
for (const f of fs.readdirSync("compositions")) if (f.endsWith(".html")) fs.unlinkSync(`compositions/${f}`);
const sections = [];
for (const f of files) {
  const n0 = scenes.length;
  const mod = await import(new URL(f, dir));
  const mine = scenes.slice(n0), stem = f.replace(/\.mjs$/, "");
  if (mine.length) sections.push({ file: stem, title: mod.title || stem, start: Math.min(...mine.map((s) => s.start0)), end: Math.max(...mine.map((s) => s.end0)) });
}

const ids = scenes.map((s) => s.id);
const dup = ids.filter((x, i) => ids.indexOf(x) !== i);
if (dup.length) throw new Error("duplicate scene ids: " + dup.join(", "));
scenes.sort((a, b) => a.start - b.start);
for (let i = 1; i < scenes.length; i++) if (scenes[i].start < scenes[i - 1].end - 0.001) throw new Error(`scenes overlap: ${scenes[i - 1].id} ends ${scenes[i - 1].end}, ${scenes[i].id} starts ${scenes[i].start}`);

const all = scenes.slice();
const inRange = scenes.filter((s) => s.start >= A0 - 0.002 && s.end <= B0 + 0.002);
if (range) {
  const cut = scenes.filter((s) => s.start < B0 - 0.002 && s.end > A0 + 0.002 && !inRange.includes(s));
  if (cut.length) throw new Error("--range cuts through scenes: " + cut.map((s) => s.id).join(", "));
  for (const s of all) if (!inRange.includes(s)) fs.unlinkSync(`compositions/${s.id}.html`);
}
let SEG = null, shown = inRange;
if (reel) {
  shown = reel.split(",").map((id) => { const s = all.find((x) => x.id === id); if (!s) throw new Error("--reel: no scene " + id); return s; });
  for (const s of all) if (!shown.includes(s)) fs.unlinkSync(`compositions/${s.id}.html`);
  // SEG: [first frame in the reel, first frame in the video, frames] per scene
  let R = 0; SEG = shown.map((s) => { const a = snapF(s.start), n = snapF(s.end) - a, g = [R, a, n]; R += n; return g; });
}
const LEN = reel ? Math.floor((SEG.reduce((a, g) => a + g[2], 0) / FPS) * 10000 + 1e-6) / 10000 : Math.floor((B - A) * 10000 + 1e-6) / 10000; // truncated, so it never rounds up to an extra frame
// a reel scene starts on its first frame (never a hair after it) and ends inside its last one
const hostAt = (s, i) => reel ? Math.floor((SEG[i][0] / FPS) * 1e5) / 1e5 : r3(Math.max(0, s.start - A));
const hostDur = (s, i) => r3(reel ? Math.min(s.end - s.start, Math.floor((SEG[i][2] / FPS) * 1000) / 1000) : s.end - s.start);

// The ASCII ground: a strip of characters, wider than the frame so it can drift for the whole video.
const DRIFT = Math.round((END / 30) * 200);
const COLS = Math.ceil((1920 + DRIFT + 60) / 13.2), ROWS = 9, SEED = 3;
function hash(i, j, s) { let h = (i * 374761393 + j * 668265263 + s * 1442695041) | 0; h = ((h ^ (h >>> 13)) * 1274126177) | 0; return ((h ^ (h >>> 16)) >>> 0) / 4294967295; }
let ground = "";
for (let j = 0; j < ROWS; j++) {
  let line = "";
  for (let i = 0; i < COLS; i++) {
    const u = i / 146, v = j / ROWS;
    const y0 = 0.36 + Math.sin(u * 5 + SEED) * 0.24 + Math.sin(u * 13 + SEED * 2) * 0.11 + Math.sin(u * 31 + SEED) * 0.05;
    const n = hash(i, j, SEED), dd = v - y0;
    line += dd > 0 && n > 0.1 ? (dd < 0.07 ? (n > 0.55 ? "." : ":") : dd < 0.2 ? "-" : dd < 0.36 ? "=" : dd < 0.56 ? "+" : "#") : " ";
  }
  ground += line + "\n";
}

// Face window: 480 x 600, a 4:5 crop of the camera file (video.json face.crop); corner radius from video.json face.radius.
// video.json face.ring (optional): the window's box-shadow, for a video with its own look (a pink edge on 1113-nod).
const PLACE = { stag: "{ x: 1400, y: 372, scale: 0.9833 }", pipT: "{ x: 1512, y: 48, scale: 0.75 }", pip: "{ x: 1512, y: 582, scale: 0.75 }", pipL: "{ x: 48, y: 582, scale: 0.75 }", inset: "{ x: 1424, y: 500, scale: 0.8333 }", cell: "{ x: 1428, y: 411, scale: 0.925 }", mid: "{ x: 1428, y: 305, scale: 0.925 }", right: "{ x: 1344, y: 206, scale: 1 }", corner: "{ x: 1566, y: 538, scale: 0.5375 }", left: "{ x: 96, y: 206, scale: 1 }" };
faces.sort((a, b) => a.t - b.t);
if (!faces.length) faces.push({ t: 0, place: "right", dur: 0 });
const moves = [];
let cur = faces[0].place === "off" ? "right" : faces[0].place, visible = faces[0].place !== "off";
for (const f of faces.slice(1)) {
  // dur 0 = a hard cut: the window is placed, shown or hidden on that frame.
  const cut = !f.dur;
  if (f.place === "off") { if (visible) moves.push(cut ? `      tl.set("#facewin", { opacity: 0 }, ${r3(f.t)});` : `      tl.fromTo("#facewin", { opacity: 1 }, { opacity: 0, duration: 0.25, ease: "power2.in", immediateRender: false }, ${r3(f.t)});`); visible = false; continue; }
  if (!visible) {
    moves.push(`      tl.set("#facewin", ${PLACE[f.place]}, ${r3(f.t)});`, cut ? `      tl.set("#facewin", { opacity: 1 }, ${r3(f.t)});` : `      tl.fromTo("#facewin", { opacity: 0 }, { opacity: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, ${r3(f.t)});`);
    visible = true; cur = f.place; continue;
  }
  if (f.place !== cur) moves.push(cut ? `      tl.set("#facewin", ${PLACE[f.place]}, ${r3(f.t)});` : `      tl.fromTo("#facewin", ${PLACE[cur]}, { ...${PLACE[f.place]}, duration: ${f.dur}, ease: "power3.inOut", immediateRender: false }, ${r3(f.t)});`);
  cur = f.place;
}
const first = faces[0].place === "off" ? "right" : faces[0].place;
if (!range && !want && !reel) {
  // The whole video must be covered with no gaps before chapters are cut from it.
  if (Math.abs(scenes[0].start) > 0.002) throw new Error(`the first scene starts at ${scenes[0].start}, not 0`);
  for (let i = 1; i < scenes.length; i++) if (scenes[i].start > scenes[i - 1].end + 0.002) throw new Error(`gap between ${scenes[i - 1].id} (ends ${scenes[i - 1].end}) and ${scenes[i].id} (starts ${scenes[i].start})`);
  // --partial: a pilot, where only the first sections exist yet. Everything else is still checked.
  if (!process.argv.includes("--partial") && Math.abs(scenes[scenes.length - 1].end - END) > 0.002) throw new Error(`the last scene ends at ${scenes[scenes.length - 1].end}, the cut is ${END} (pass --partial for a pilot of the first sections)`);
  sections.sort((a, b) => a.start - b.start);
  fs.writeFileSync(new URL("./sections.json", import.meta.url), JSON.stringify({ sections }, null, 1));
}
fs.writeFileSync(new URL("./clips.json", import.meta.url), JSON.stringify(clips, null, 1)); // tools/make_clips.py cuts these
if (!range && !want && !reel) {
  // tools/slices.json: one render slice per scene. `key` changes only when that scene's picture changes: its own page,
  // where the face window is during it, its length, the media revision (video.json media_rev: bump it after a re-cut),
  // or this file. A timing change earlier in the video leaves a later slice's key alone, so its render is re-used.
  const crypto = await import("node:crypto");
  // STAGE_REV: bump when this file changes what every frame looks like (the face window, the ground, the stage). The
  // places a slice uses are in its key by value, so adding or moving a place only re-renders the slices that use it.
  const STAGE_REV = 1;
  const sorted = faces.slice().sort((a, b) => a.t - b.t);
  const slices = all.map((s) => {
    const before = sorted.filter((f) => f.t <= s.start + 0.001).pop();
    const during = sorted.filter((f) => f.t > s.start + 0.001 && f.t < s.end - 0.001).map((f) => [r3(f.t - s.start), f.place, f.dur]);
    const frames = snapF(s.end) - snapF(s.start);
    // A clip's crop and source moment are not in the scene's page (the page only names the clip file), so they go in the
    // key by value: a changed crop on a screen shot, or a b-roll moved to another moment, renders again. [1116-plugins:
    // three crops were changed and every slice was re-used.] A scene with no clip keeps the key it had.
    const own = clips.filter((c) => c.id.startsWith(s.id + "-")).map((c) => [c.src, c.crop, Math.abs(c.start - s.start) > 0.01 ? c.start : 0]);
    const key = crypto.createHash("sha1").update(JSON.stringify([fs.readFileSync(`compositions/${s.id}.html`, "utf8"), before ? [before.place, PLACE[before.place]] : null, during.map((d) => [...d, PLACE[d[1]]]), frames, CFG.media_rev || 0, STAGE_REV, ...(CFG.face?.ring ? [CFG.face.ring] : []), ...(own.length ? [own] : [])])).digest("hex").slice(0, 16);
    // ff: this slice is plain footage and the face window does not change during it, so ffmpeg can build it.
    // t0 = the scene's start on today's cut (where its footage starts), unless the scene shows footage from another
    // moment (footage[id].t0, set by cardFootage's `from`); win = where the window sits, or null when it is off.
    // footage[id].card: his footage sits in a rounded rectangle on a still page, not full frame (render_slices.py card route).
    const place = before ? before.place : "off";
    const win = place === "off" ? null : Function("return " + PLACE[place])();
    const ff = footage[s.id] && !during.length ? { ...footage[s.id], t0: footage[s.id].t0 ?? r3(s.start), place, win } : null;
    // pg (designed slices): where the window sits for the whole slice, and `moves` when it moves, fades or is still
    // arriving during it. A slice with moves: false can be rendered without the window (--reel) and get it from ffmpeg.
    const arriving = before && before.dur && before.t + Math.max(before.dur, 0.3) > s.start + 0.001;
    // pkey: the scene's browser picture alone (no face window, no media_rev unless it shows clips of the cut). render_slices.py
    // keeps each reel's browser render and finds a scene in it by pkey, so after a re-cut (media_rev raised) or a moved
    // window only the ffmpeg window composite runs again for a scene whose page did not change [Chase, 2026-11-20].
    const pkey = crypto.createHash("sha1").update(JSON.stringify(["page", fs.readFileSync(`compositions/${s.id}.html`, "utf8"), frames, STAGE_REV, ...(own.length ? [own, CFG.media_rev || 0] : [])])).digest("hex").slice(0, 16);
    const pg = ff ? null : { place, win, moves: during.length > 0 || !!arriving, pkey };
    return { id: s.id, start: s.start0, end: s.end0, frame0: snapF(s.start), frames, key, ...(ff ? { ff } : { pg }) };
  });
  fs.writeFileSync(new URL("./slices.json", import.meta.url), JSON.stringify(slices, null, 1));
}
if (!range && !want && !reel) fs.writeFileSync("faces.json", JSON.stringify(faces.map((f) => ({ t: f.t, place: f.place })), null, 1)); // for the review player's layout lane

fs.writeFileSync("index.html", `<!doctype html>
<!-- Generated by tools/build.mjs. Edit tools/sections/*.mjs or tools/kit.mjs and re-run it. -->
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      @font-face { font-family: "Geist Mono"; font-weight: 500; src: url("assets/fonts/geist-mono-latin-500-normal.woff2") format("woff2"); }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #1a1917; }
      #root { position: relative; width: 1920px; height: 1080px; overflow: hidden; }
      #stage { position: absolute; inset: 0; z-index: 0; background: #1a1917; }
      #ground-clip { position: absolute; left: 0; top: 884px; width: 1920px; height: 216px; overflow: hidden; z-index: 1; }
      #ground { position: absolute; left: 0; top: 0; white-space: pre; font: 500 22px/24px "Geist Mono", monospace; color: #77736a; }
      #facewin { position: absolute; left: 0; top: 0; z-index: 3; width: 480px; height: 600px; overflow: hidden; border-radius: ${CFG.face?.radius ?? 0}px; background: #111; box-shadow: ${CFG.face?.ring || "0 0 0 4px #1a1917, 0 0 0 5px #423f3b, 0 30px 60px -20px rgba(0,0,0,.8)"}; }
      #face { position: absolute; left: 0; top: 0; width: 100%; height: 100%; object-fit: cover; }
      .scene { z-index: 2; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="${LEN}" data-width="1920" data-height="1080">
      <div id="stage"></div>
      <div id="ground-clip" data-layout-ignore><pre id="ground">${ground}</pre></div>

${shown.map((s, i) => `      <div id="${s.id}" class="scene" data-composition-id="${s.id}" data-composition-src="compositions/${s.id}.html" data-start="${hostAt(s, i)}" data-duration="${hostDur(s, i)}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>`).join("\n")}
${reel ? "" : `
      <div id="facewin">
        <video id="face" class="clip" src="assets/face.mp4" data-start="0" data-duration="${LEN}" data-media-start="${r3(A + 0.004)}" data-track-index="0" muted playsinline></video>
      </div>`}${noVoice ? "" : `
      <audio id="voice" src="assets/voice.m4a" data-start="0" data-duration="${LEN}" data-media-start="${r3(A)}" data-track-index="2" data-volume="1"></audio>`}
    </div>
    <script>
      // "tl" runs on the whole video's clock. The composition's own timeline ("main") drives it from second
      // ${r3(A)} to ${r3(B)}, so a chapter picks up the face window and the ground exactly where the video has them.
      const tl = gsap.timeline({ paused: true });
${reel ? "" : `      gsap.set("#facewin", { transformOrigin: "0 0", ...${PLACE[first]}${faces[0].place === "off" ? ", opacity: 0" : ""} });
`}      tl.fromTo("#ground", { x: 0 }, { x: -${DRIFT}, duration: ${END}, ease: "none" }, 0);
${reel ? "" : moves.join("\n")}
${reel ? `      const main = gsap.timeline({ paused: true });
      // a reel: each scene's frames show the second of the video they belong to (the ground is where the video has it)
      const SEG = ${JSON.stringify(SEG)}, FPS = ${FPS}, clock = { u: 0 };
      const sync = () => { const t = main.time(), f = Math.floor(t * FPS + 1e-4); let g = SEG[0]; for (const x of SEG) if (x[0] <= f) g = x; tl.time(g[1] / FPS + (t - g[0] / FPS), false); };
      main.fromTo(clock, { u: 0 }, { u: 1, duration: ${LEN}, ease: "none", onUpdate: sync }, 0);
      sync();` : `      const clock = { t: ${r3(A)} };
      const main = gsap.timeline({ paused: true });
      main.fromTo(clock, { t: ${r3(A)} }, { t: ${r3(B)}, duration: ${LEN}, ease: "none", onUpdate: () => tl.time(clock.t, false) }, 0);
      tl.time(${r3(A)}, false);`}
      window.__timelines = window.__timelines || {};
      window.__timelines["main"] = main;
      main.seek(0);
    </script>
  </body>
</html>
`);
console.log(`${shown.length} scenes from ${files.join(", ")}${range ? ` | chapter ${r3(A)}-${r3(B)} (${LEN} s, ${Math.round((B - A) * FPS)} frames)` : ""}`);
console.log(shown.map((s) => `${s.id} ${r3(s.start)}-${r3(s.end)}`).join(" | "));
if (process.argv.includes("--cues")) console.log(cues.map(([p, t]) => `${r3(t)} ${p}`).join("\n"));
