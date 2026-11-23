// The charcoal kit: everything a section needs to put scenes on the cut's timeline in the template's look.
// A section file imports from here and calls scene() and face(); tools/build.mjs then writes index.html.
// Run builds from the project folder (work/<id>/full), so "assets/..." and "../docs/..." resolve.
// This file is copied into each project by templates/charcoal/build_kit/new_project.py. The look in it is the
// template's: change it for one video only when Chase asks, and say so in RUN.md. A helper only this video needs
// goes in tools/local.mjs, never here: a change made here that the next video would want is made in the kit as well.
import fs from "node:fs";
import crypto from "node:crypto";

// tools/video.json is this video's own settings, written by new_project.py:
// { id, end0, fps, series: { label, count }, docs_site, face: { crop, radius } }
export const CFG = JSON.parse(fs.readFileSync(new URL("./video.json", import.meta.url), "utf8"));

// Retime: when the cut changes after the sections were written (a note restores or removes footage), the
// section files keep the times they were written with and tools/retime.json lists what moved:
// [[atSecond, addedSeconds], ...] on the ORIGINAL timeline, in whole frames. mapT() turns an original time into
// today's time; cue() answers in original time, so everything inside a section stays consistent.
export const RETIME = JSON.parse(fs.readFileSync(new URL("./retime.json", import.meta.url), "utf8"));
export const mapT = (t) => t + RETIME.reduce((a, [at, add]) => a + (t > at + 1e-6 ? add : 0), 0);
const unmapT = (t) => { let o = t; for (const [at, add] of RETIME) if (o > at + add - 1e-6) o -= add; else if (o > at) o = at; return o; };
export const END0 = CFG.end0; // length of the cut the sections were written against
export const END = mapT(END0); // length of the cut today
export const W = JSON.parse(fs.readFileSync("assets/words.json", "utf8")); // [word, start, end, index]
export const norm = (s) => s.toLowerCase().replace(/[^a-z0-9$%.]/g, "").replace(/\.$/, "");
export const cues = [];
export function cue(phrase, after = 0) {
  const toks = phrase.split(/\s+/).map(norm);
  for (let i = 0; i < W.length; i++) {
    const at = unmapT(W[i][1]);
    if (at < after) continue;
    if (toks.every((t, j) => W[i + j] && norm(W[i + j][0]) === t)) { cues.push([phrase, at]); return at; }
  }
  throw new Error("cue not found: " + phrase);
}
// ---- where a scene starts ([Chase] 2026-11-13, 1113-nod: "frames 10565 to 10570 are showing the desktop background and
// not the correct camera": a scene that started on his first word, 6 frames after the join where his screen changed) ----
// JOINS: every join of the cut the sections are written against (tools/cut0.json), in seconds of that cut.
// at("spoken phrase", after): the second a scene starts for a sentence: ON the join when the cut has one within 0.35 s
// of the sentence's first word (his screen and camera change on the join, not on the word), else 0.05 s before the word.
// A join's time is rounded down, so the frame the join lands on already belongs to the new scene.
// joinNear(t): the join nearest second t, for a shot whose first word cue() cannot match.
const CUT0 = fs.existsSync(new URL("./cut0.json", import.meta.url)) ? JSON.parse(fs.readFileSync(new URL("./cut0.json", import.meta.url), "utf8")) : { keeps: [], fps: 60 };
export const JOINS = CUT0.keeps.slice(0, -1).reduce((a, [s, e]) => { a.push((a.length ? a[a.length - 1] : 0) + (e - s) / CUT0.fps); return a; }, []);
const onJoin = (j) => Math.floor(j * 1000 + 1e-6) / 1000;
export const at = (phrase, after = 0) => {
  const t = cue(phrase, after) - 0.05, j = JOINS.filter((x) => Math.abs(x - t) <= 0.35).sort((p, q) => Math.abs(p - t) - Math.abs(q - t))[0];
  return j === undefined ? Math.round(t * 1000) / 1000 : onJoin(j);
};
export const joinNear = (t) => onJoin(JOINS.slice().sort((p, q) => Math.abs(p - t) - Math.abs(q - t))[0]);
export const r = (n) => Math.round(n * 10) / 10;
export const r3 = (n) => Math.round(n * 1000) / 1000;

// ---------- shared look ----------
export const FONTS = `
    @font-face { font-family: "Geist Mono"; font-weight: 400; src: url("assets/fonts/geist-mono-latin-400-normal.woff2") format("woff2"); }
    @font-face { font-family: "Geist Mono"; font-weight: 500; src: url("assets/fonts/geist-mono-latin-500-normal.woff2") format("woff2"); }
    @font-face { font-family: "Geist Mono"; font-weight: 600; src: url("assets/fonts/geist-mono-latin-600-normal.woff2") format("woff2"); }
    @font-face { font-family: "Hanken Grotesk"; font-weight: 600; src: url("assets/fonts/hanken-grotesk-latin-600-normal.woff2") format("woff2"); }`;
export const COMMON = `
.wrap{position:absolute}
.k{font:500 30px/1 "Geist Mono",monospace;color:#aaa69d}
.k b{font-weight:500;color:#ff7a50}
.h{font:600 100px/1 "Hanken Grotesk",sans-serif;letter-spacing:-0.035em;color:#ebe8e0;margin-left:-4px}
.h em{font-style:normal;color:#ff7a50}
.h span{display:inline-block;white-space:pre}
.cur{display:inline-block;width:.13em;height:.74em;margin-left:.08em;background:#ff6a3d;vertical-align:-.04em}
.s{margin-top:22px;font:400 32px/1.3 "Geist Mono",monospace;color:#aaa69d}
.m{font:500 32px/1 "Geist Mono",monospace;color:#ebe8e0}
.mut{color:#aaa69d}
.o{color:#ff7a50}
.row{position:relative;display:flex;align-items:center;height:62px;font:500 32px/1 "Geist Mono",monospace;color:#ebe8e0;white-space:nowrap}
.br{position:relative;width:86px;height:62px;flex:none}
.br::before{content:"";position:absolute;left:9px;top:0;bottom:0;width:2px;background:#66635d}
.br::after{content:"";position:absolute;left:9px;top:30px;width:48px;height:2px;background:#66635d}
.row.last .br::before{bottom:30px}
.n{width:66px;color:#aaa69d;flex:none}
.sel{position:relative;width:1060px;height:96px}
.sel .mk{position:absolute;left:0;top:0;width:200px;height:96px;background:#ff6a3d}
.sel .op{position:absolute;top:0;width:200px;height:96px;display:flex;align-items:center;justify-content:center;box-shadow:inset 0 0 0 1.5px #423f3b;font:500 32px/1 "Geist Mono",monospace;color:#aaa69d}
.src{font:400 24px/1 "Geist Mono",monospace;color:#aaa69d}
.tb{position:absolute;left:0;border-top:1px dashed #423f3b}
.tr{display:flex;align-items:center;height:92px;border-bottom:1px dashed #423f3b;font:500 34px/1 "Geist Mono",monospace;color:#ebe8e0;white-space:nowrap}
.tr span:nth-child(1){flex:1}
.chip{display:inline-block;background:#ff6a3d;color:#0d0d0c;font:600 26px/1 "Geist Mono",monospace;padding:10px 16px}
.big{font:600 150px/0.9 "Hanken Grotesk",sans-serif;letter-spacing:-0.045em;color:#ebe8e0}
.trk{height:44px;box-shadow:inset 0 0 0 1px #423f3b}
.bar{height:100%;background:#ff6a3d}
`;
// Prefix every rule with the scene's wrapper so scenes cannot restyle each other.
export const scope = (css, id) => css.split("}").map((rule) => {
  const [sel, body] = rule.split("{");
  if (!body) return "";
  return sel.split(",").map((s) => `#${id}-wrap ${s.trim()}`.replace(`#${id}-wrap .wrap`, `#${id}-wrap`)).join(",") + "{" + body + "}";
}).join("\n    ");

export const chars = (text, cls = "c") => [...text].map((ch) => `<span class="${cls}">${ch === " " ? " " : ch}</span>`).join("");
// A row of options with one orange marker that moves between them (move "#<id>-mk" to x = selX(i)).
// Five options fit the default 1060 wrap. The default names are the Fable video's effort levels; pass your own.
export const SEL = ["low", "medium", "high", "xhigh", "max"];
export const selX = (i) => i * 215;
export const selector = (id, names = SEL) => `<div class="sel" id="${id}"><div class="mk" id="${id}-mk"></div>${names.map((n, i) => `<div class="op" id="${id}-o${i}" style="left:${selX(i)}px">${n}</div>`).join("")}</div>`;
export const OUT = "blur(10px)";

export const scenes = [];
export function scene(id, start, end, { css = "", html, tl, wrap = "left:96px;top:0;width:1060px;height:1080px", exit: doExit = true }) {
  const T = (g) => r3(mapT(g) - mapT(start)); // a second of the video (original time) -> this scene's clock today
  const body = typeof html === "function" ? html(T) : html;
  const code = tl(T);
  const exit = doExit && end < END0 - 0.001 ? `\n    tl.fromTo("#${id}-wrap", { opacity: 1, filter: "blur(0px)" }, { opacity: 0, filter: "${OUT}", duration: 0.22, ease: "power2.in", immediateRender: false }, ${r3(mapT(end) - mapT(start) - 0.26)});` : "";
  fs.writeFileSync(`compositions/${id}.html`, `<!-- Generated by tools/build.mjs. Edit the generator and re-run it. -->
<template>
  <style>${FONTS}
    #root { position: absolute; inset: 0; }
    ${scope(COMMON + css, id)}
  </style>
  <div id="root" data-composition-id="${id}" data-width="1920" data-height="1080">
    <div id="${id}-wrap" class="wrap" style="${wrap}">
${body}
    </div>
  </div>
  <script>
    const tl = gsap.timeline({ paused: true });
${code}${exit}
    window.__timelines = window.__timelines || {};
    window.__timelines["${id}"] = tl;
  </script>
</template>
`);
  scenes.push({ id, start: mapT(start), end: mapT(end), start0: start, end0: end });
}
// Small helpers that return timeline lines.
export const blurIn = (sel, at, d = 0.26) => `    tl.fromTo("${sel}", { opacity: 0, filter: "blur(10px)" }, { opacity: 1, filter: "blur(0px)", duration: ${d}, ease: "power3.out" }, ${r3(at)});`;
export const show = (sel, at, d = 0.12) => `    tl.fromTo("${sel}", { opacity: 0 }, { opacity: 1, duration: ${d}, ease: "none" }, ${r3(at)});`;
export const slideIn = (sel, at) => `    tl.fromTo("${sel}", { opacity: 0, x: -14 }, { opacity: 1, x: 0, duration: 0.24, ease: "power3.out" }, ${r3(at)});`;
export const type = (sel, at, per = 0.04) => `    tl.fromTo("${sel}", { opacity: 0 }, { opacity: 1, duration: 0.01, ease: "none", stagger: ${per} }, ${r3(at)});`;
export const blink = (sel, on, off) => `    tl.fromTo("${sel}", { opacity: 0 }, { opacity: 1, duration: 0.01, ease: "none" }, ${r3(on)});\n    tl.fromTo("${sel}", { opacity: 1 }, { opacity: 0, duration: 0.01, ease: "none", immediateRender: false }, ${r3(off)});`;

// The real docs page in a card, with an excerpt lifted out of it and highlights swept over measured sentences.
export function docs(id, pullId, { cardX = 475, cardY = 70, cardW = 640, cardH = 820, headY = 250, exY = 316, withHeading, Z = 2.3, tag, site }) {
  const d = JSON.parse(fs.readFileSync(`../docs/${pullId}.json`, "utf8"));
  withHeading = withHeading ?? !!d.withHeading; // pulls.json can say the excerpt keeps its heading
  site = site ?? CFG.docs_site ?? new URL(d.url).host;
  const sp = cardW / d.clip.width;
  const reg = { x: d.block.x - 20, y: (withHeading ? d.heading.y - 18 : d.block.y - 14) };
  reg.w = d.block.w + 40;
  reg.h = d.block.y + d.block.h + 13 - reg.y;
  const EX = { w: reg.w * Z, h: reg.h * Z, y: exY };
  EX.x = cardX + cardW / 2 - EX.w / 2;
  const scroll = -((withHeading ? d.heading.y : d.block.y) * sp - headY);
  const from = { x: cardX + reg.x * sp - EX.x, y: cardY + reg.y * sp + scroll - EX.y, scale: sp / Z };
  // The lifted excerpt is shown at Z times page size, so it uses its own 5x capture of just that region when there is one
  // (assets/docs/<id>-ex.png, written by capture_docs.mjs); otherwise the 3x page image.
  const exFile = `assets/docs/${pullId}-ex.json`;
  const X = fs.existsSync(exFile) ? JSON.parse(fs.readFileSync(exFile, "utf8")).ex : null;
  const covers = X && X.x <= reg.x + 1e-6 && X.y <= reg.y + 1e-6 && X.x + X.w >= reg.x + reg.w - 1e-6 && X.y + X.h >= reg.y + reg.h - 1e-6;
  const eimg = covers
    ? `left:${r((X.x - reg.x) * Z)}px;top:${r((X.y - reg.y) * Z)}px;width:${r(X.w * Z)}px;height:${r(X.h * Z)}px;background:url("assets/docs/${pullId}-ex.png") 0 0/100% 100% no-repeat`
    : `left:${r(-reg.x * Z)}px;top:${r(-reg.y * Z)}px;width:${r(d.clip.width * Z)}px;height:${r(d.clip.height * Z)}px;background:url("assets/docs/${pullId}.png") 0 0/100% 100% no-repeat`;
  const marks = [], ids = [];
  d.sentences.forEach((s, si) => s.lines.forEach((l, li) => {
    ids.push({ id: `${id}-hl-${si}-${li}`, si, li, w: l.w });
    marks.push(`<i class="hl" id="${id}-hl-${si}-${li}" style="left:${r((l.x - reg.x - 2) * Z)}px;top:${r((l.y - reg.y - 1.5) * Z)}px;width:${r((l.w + 4) * Z)}px;height:${r((l.h + 3) * Z)}px"></i>`);
  }));
  const css = `
.page{position:absolute;left:${cardX - 96}px;top:${cardY}px;width:${cardW}px;height:${cardH}px;overflow:hidden;background:#fcfbf8;box-shadow:0 0 0 1px #423f3b}
.pimg{position:absolute;left:0;top:${r(scroll)}px;width:${cardW}px;height:${r(d.clip.height * sp)}px}
.pimg img{display:block;width:100%;height:100%}
.dim{position:absolute;inset:0;background:#1a1917}
.ex{position:absolute;left:${r(EX.x - 96)}px;top:${EX.y}px;width:${r(EX.w)}px;height:${r(EX.h)}px}
.exc{position:absolute;inset:0;overflow:hidden;background:#fcfbf8;box-shadow:0 0 0 3px #ff6a3d,0 40px 80px -30px rgba(0,0,0,.7)}
.eimg{position:absolute;${eimg}}
.hl{position:absolute;display:block;background:rgba(255,106,61,.5);mix-blend-mode:multiply}
.tag{position:absolute;left:0;top:-58px;height:46px;padding-right:18px;display:flex;align-items:center;gap:34px;background:#1a1917;font:500 28px/1 "Geist Mono",monospace;color:#aaa69d;white-space:nowrap}
.tag b{font-weight:500;color:#ff7a50}
.tag i{display:block;width:12px;height:12px;background:#aaa69d;margin-right:-20px}`;
  const html = `      <div class="page" id="${id}-page"><div class="pimg" data-layout-allow-overflow><img src="assets/docs/${pullId}.png" alt="" /></div><div class="dim" id="${id}-dim"></div></div>
      <div class="ex" id="${id}-ex" data-layout-allow-overflow>
        <div class="tag" id="${id}-tag"><i></i><b>${site}</b><span>${tag}</span></div>
        <div class="exc"><div class="eimg"></div>${marks.join("")}</div>
      </div>`;
  // arrive at local t0, lift at t0 + 0.55; highlights at the given local times (one per sentence).
  const tl = (t0, hlTimes) => {
    const lines = [
      `    tl.fromTo("#${id}-page", { opacity: 0, y: 36, filter: "blur(12px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.42, ease: "expo.out" }, ${r3(t0)});`,
      `    tl.fromTo("#${id}-dim", { opacity: 0 }, { opacity: 0.6, duration: 0.35, ease: "power2.out" }, ${r3(t0 + 0.5)});`,
      `    tl.fromTo("#${id}-ex", { opacity: 0 }, { opacity: 1, duration: 0.1, ease: "none" }, ${r3(t0 + 0.5)});`,
      `    tl.fromTo("#${id}-ex", { x: ${r(from.x)}, y: ${r(from.y)}, scale: ${r3(from.scale)}, transformOrigin: "0 0" }, { x: 0, y: 0, scale: 1, duration: 0.6, ease: "expo.out" }, ${r3(t0 + 0.5)});`,
      `    tl.fromTo("#${id}-tag", { opacity: 0 }, { opacity: 1, duration: 0.2, ease: "none" }, ${r3(t0 + 1.0)});`,
    ];
    d.sentences.forEach((s, si) => {
      let t = hlTimes[si];
      ids.filter((x) => x.si === si).forEach((x) => {
        const dur = Math.max(0.16, x.w / 620);
        lines.push(`    tl.fromTo("#${x.id}", { scaleX: 0, transformOrigin: "0 50%" }, { scaleX: 1, duration: ${r3(dur)}, ease: "${x.li === 0 ? "power2.in" : "power2.out"}" }, ${r3(t)});`);
        t += dur;
      });
    });
    return lines.join("\n");
  };
  return { css, html, tl, EX };
}
export const WIDE = "left:96px;top:0;width:1728px;height:1080px"; // when the face is in the corner
export const RIGHT = "left:752px;top:0;width:1072px;height:1080px"; // when the face is large on the left


// ---------- the face window ----------
// face(t, place, dur): from second t the window moves to "right" (large, right side), "left" (large, left side)
// or "corner" (small, bottom right), taking dur seconds. "off" fades it out; any place after that fades it back in.
// Content must stay clear of it: with "right" use the default wrap (x 96 to 1156), with "left" use RIGHT
// (x 752 to 1824), with "corner" use WIDE but keep out of x > 1470 below y = 500.
export const faces = [];
export function face(t, place, dur = 0.65) { faces.push({ t: mapT(t), place, dur }); }

// ---------- reusable pieces (each returns { css, html } or timeline lines) ----------
// A chapter's title scene: "// rule NN of 10" (label and count from video.json `series`), a typed two-line title,
// and a sub line that lands on a spoken phrase.
export function ruleTitle(id, n, start, end, line1, line2, sub, subAt) {
  scene(id, start, end, {
    css: `.box{position:absolute;left:0;top:156px;width:1120px;height:700px;display:flex;flex-direction:column;justify-content:center}
.h{margin-top:30px;font-size:${Math.max(line1.length, line2.length) > 12 ? 128 : 164}px;line-height:.98;letter-spacing:-0.04em}
.s{margin-top:40px;font-size:34px}`,
    html: `      <div class="box"><p class="k" id="${id}-k">// <b>${CFG.series.label} ${String(n).padStart(2, "0")}</b> of ${CFG.series.count}</p>
      <h1 class="h">${chars(line1)}<br />${chars(line2)}<span class="cur" id="${id}-cur"></span></h1>
      <p class="s" id="${id}-s">${sub}</p></div>`,
    tl: (T) => {
      const done = 0.4 + (line1.length + line2.length) * 0.045;
      return [show(`#${id}-k`, 0.2, 0.2), type(`#${id}-wrap .h .c`, 0.4, 0.045), blink(`#${id}-cur`, done + 0.05, Math.min(end - start - 0.4, done + 0.9)), blurIn(`#${id}-s`, Math.max(done + 0.1, T(subAt)))].join("\n");
    },
  });
}
// A dark card holding prompt text in mono, like a file. Give `text` with real line breaks (keep lines under
// `cols` characters) and wrap the words to highlight in <mark id="...">. Returns css + html; reveal paragraphs
// with wipe() and highlight with sweep().
export function promptCard(id, { file, right = "", text, x = 0, y, w = 1060, size = 26 }) {
  const css = `
.pc{position:absolute;left:${x}px;top:${y}px;width:${w}px;background:#0d0d0c;box-shadow:0 0 0 1px #423f3b;overflow:hidden}
.pcb{display:flex;align-items:center;justify-content:space-between;height:56px;padding:0 30px;border-bottom:1px dashed #423f3b;font:500 22px/1 "Geist Mono",monospace;color:#aaa69d}
.pcb b{font-weight:500;color:#ebe8e0}
.pct{padding:26px 30px 30px;font:400 ${size}px/${Math.round(size * 1.54)}px "Geist Mono",monospace;color:#dcd8ce;white-space:pre}
.pct .p{display:block}
.pct .gap{display:block;height:${Math.round(size * 0.77)}px}
.pct .t{color:#ff7a50;font-weight:500}
.pct mark{color:#dcd8ce;background:linear-gradient(#ff6a3d,#ff6a3d) no-repeat 0 50%/0% 88%}`;
  const html = `      <div class="pc" id="${id}"><div class="pcb"><b>${file}</b><span>${right}</span></div><div class="pct">${text}</div></div>`;
  return { css, html };
}
// Reveal a block top-down in n line steps (a paste landing line by line).
export const wipe = (sel, at, n) => `    tl.fromTo("${sel}", { clipPath: "inset(0% 0% 100% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: ${r3(Math.max(0.08, n * 0.085))}, ease: "steps(${n})" }, ${r3(at)});`;
// Sweep the orange band across a <mark> (works across line breaks) and turn its text dark.
export const sweep = (sel, at, d = 0.5) => `    tl.fromTo("${sel}", { backgroundSize: "0% 88%", color: "#dcd8ce" }, { backgroundSize: "100% 88%", color: "#0d0d0c", duration: ${d}, ease: "power2.inOut" }, ${r3(at)});`;
// Grow a bar from the left.
export const grow = (sel, at, d = 0.8) => `    tl.fromTo("${sel}", { scaleX: 0, transformOrigin: "0 50%" }, { scaleX: 1, duration: ${d}, ease: "power3.out" }, ${r3(at)});`;
// Pop a chip or pill in.
export const pop = (sel, at) => `    tl.fromTo("${sel}", { opacity: 0, scale: 1.2 }, { opacity: 1, scale: 1, duration: 0.35, ease: "expo.out" }, ${r3(at)});`;
// Count a number up in an element (integers).
export const count = (sel, at, to, d = 0.9) => `    { const o = { v: 0 }, el = document.querySelector("${sel}"); tl.fromTo(o, { v: 0 }, { v: ${to}, duration: ${d}, ease: "power2.out", onUpdate: () => { el.textContent = Math.round(o.v); } }, ${r3(at)}); }`;

// ---------- his own footage inside the video (first used on 1110-slop) ----------
// clipTag(id, {src, crop, w, h, start, end}): a piece of this cut's own footage inside a scene, on exactly the scene's frames.
// src "screen" = raw/cut.mp4 (his screen), "cam" = raw/cam_cut.mp4 (his camera). crop = [x, y, w, h] in the 3840x2160 source.
// w x h = its size on the 1920 stage; tools/make_clips.py cuts the file from tools/clips.json (render_slices.py runs it,
// at twice the size for a 4K render). `footage`: the scene this clip is the whole picture of (fullFace, screenFull): its
// slice is built by ffmpeg straight from the cut, so the clip file is only made when asked for (make_clips.py --all).
// Animate a wrapper around it, never the video itself.
export const clips = [];
export function clipTag(id, { src = "screen", crop = [0, 0, 3840, 2160], w, h, start, end, style = "", footage: whole }) {
  const file = `assets/clips/${id}.mp4`;
  clips.push({ id, src, crop, w, h, start: r3(mapT(start)), end: r3(mapT(end)), file, ...(whole ? { footage: whole } : {}) });
  return `<video id="${id}" class="clip" src="${file}" data-start="0" data-duration="${r3(mapT(end) - mapT(start))}" data-media-start="0" data-track-index="0" muted playsinline style="position:absolute;left:0;top:0;width:${w}px;height:${h}px;${style}"></video>`;
}
// A real screen in a dark card: a thin top bar naming the real site, and the footage (a clip or a still) under it.
export const SCREEN_CSS = `
.sc{position:absolute;background:#0d0d0c;box-shadow:0 0 0 1px #423f3b,0 40px 80px -30px rgba(0,0,0,.7);overflow:hidden}
.scb{position:absolute;left:0;top:0;right:0;height:44px;display:flex;align-items:center;gap:14px;padding:0 20px;border-bottom:1px dashed #423f3b;font:500 22px/1 "Geist Mono",monospace;color:#aaa69d;white-space:nowrap}
.scb i{display:block;width:10px;height:10px;background:#66635d}
.scb b{font-weight:500;color:#ebe8e0}
.scv{position:absolute;left:0;top:44px;overflow:hidden}
.scz{position:absolute;left:0;top:0}
.scz img{display:block;width:100%;height:100%}`;
// screenCard(id, start, end, opts) -> { css, html, tl(T) } for a scene: a real screen (clip of the cut, or a still) in a card.
//   src: "screen" (clip of raw/cut.mp4 on this scene's seconds) or an image path; crop: source box for a clip;
//   x, y: card position inside the wrap; w, h: the footage's size on stage (the card adds a 44 px bar on top);
//   bar: the bar's text (name the real site); push: [originX%, originY%, endScale] a slow move over the scene;
//   enter: false when the previous scene showed the same card (a cut, no entrance).
export const CROP = { chrome: [0, 180, 3800, 1900], pane: [0, 304, 3840, 1740] };
export function screenCard(id, start, end, { src = "screen", crop = CROP.chrome, x = 0, y = 40, w = 1400, h = 700, bar = "", push = [50, 50, 1.04], enter = true }) {
  const media = src === "screen" ? clipTag(`${id}-v`, { src: "screen", crop, w, h, start, end }) : `<img src="${src}" alt="" style="display:block;width:${w}px;height:${h}px" />`;
  const html = `      <div class="sc" id="${id}-card" style="left:${x}px;top:${y}px;width:${w}px;height:${h + 44}px"><div class="scb"><i></i>${bar}</div><div class="scv" style="width:${w}px;height:${h}px"><div class="scz" id="${id}-z" style="width:${w}px;height:${h}px">${media}</div></div></div>`;
  const tl = (T) => [
    enter ? `    tl.fromTo("#${id}-card", { opacity: 0, y: 36, filter: "blur(12px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.42, ease: "expo.out" }, 0.04);` : "",
    `    tl.fromTo("#${id}-z", { scale: 1, transformOrigin: "${push[0]}% ${push[1]}%" }, { scale: ${push[2]}, duration: ${r3(mapT(end) - mapT(start))}, ease: "none" }, 0);`,
  ].filter(Boolean).join("\n");
  return { css: SCREEN_CSS, html, tl };
}
// The whole stage is his camera: use with face(start, "off") and bring the window back after.
// footage[id]: scenes that are only his footage (plus, for a screen, the face window). build.mjs passes this to
// tools/slices.json so render_slices.py can build such a slice with ffmpeg on the GPU instead of the browser.
export const footage = {};
export function fullFace(id, start, end) {
  footage[id] = { src: "cam", crop: [0, 0, 3840, 2160], h: 1080 };
  scene(id, start, end, { wrap: "left:0;top:0;width:1920px;height:1080px", css: "", html: "      " + clipTag(`${id}-v`, { src: "cam", crop: [0, 0, 3840, 2160], w: 1920, h: 1080, start, end, footage: id }), tl: () => "", exit: false });
}

// ---------- a still layout with his footage in it: the fast route for a designed scene ([Chase] 2026-11-13) ----------
// "in those scenarios where it's just a still, we totally should be using this faster GPU". A scene in which nothing
// moves except his footage inside one rounded rectangle (1113-nod: the Nod app in a card on n8n's page) is built by
// ffmpeg on the GPU, not by the browser: 65 s against 403 s on that video. Two calls beside the scene() itself:
//   const page = cardPage(css, html)     the scene's page WITHOUT his footage, written once to cards/<hash>.html. Give it
//                                        the same css and html the scene has (unscoped), with the card's box left empty.
//   cardFootage(id, a, { crop, page, x, y, w, h, r, from })   marks scene `id` as footage in that card: crop = the box
//                                        of the recording, x/y/w/h/r = the card on the 1920x1080 stage and its corner
//                                        radius, from = the second of the cut its footage starts at (default: a).
// The scene must still exist (scene(), with clipTag(..., { footage: id }) in the card) for stills, the storyboard and
// `hyperframes check`. Rules: no timeline lines in that scene, the face window must not move during it, and w:h must
// equal the crop's. Anything that animates stays a normal scene and goes through the browser.
// Face place "stag" (1400, 372, 472 x 590) is the large raised window that overlaps such a card's right edge.
export function cardPage(css, html) {
  const doc = `<!doctype html><meta charset="utf8"><base href="../"><style>*{margin:0;padding:0;box-sizing:border-box}html,body{width:1920px;height:1080px;overflow:hidden}${FONTS}${css}</style>${html}`;
  const file = `cards/${crypto.createHash("sha1").update(doc).digest("hex").slice(0, 10)}.html`;
  fs.mkdirSync("cards", { recursive: true });
  if (!fs.existsSync(file)) fs.writeFileSync(file, doc);
  return file;
}
export function cardFootage(id, a, { src = "screen", crop, page, x, y, w, h, r = 0, from = a }) {
  footage[id] = { src, crop, h: 1080, card: { html: page, x, y, w, h, r }, ...(from !== a ? { t0: r3(mapT(from)) } : {}) };
}

// ---------- the base of a long-form video ([Chase] 2026-11-11: "a lot of this should just be like my face and then the screen") ----------
// Two base shots with hard cuts, no moves: his camera full frame, and his screen full frame with his face in a corner.
export const FULLW = "left:0;top:0;width:1920px;height:1080px";
export const SCR = [121, 68, 3598, 2024];          // a 16:9 window of the recorded screen: fills the frame, no bands
export const SCR_R = [242, 68, 3598, 2024];        // the same, kept flush to the right edge (the tweak bar lives there)
// screenFull: the screen fills the frame (1920 wide, 4 px bands top and bottom on near-black). crop is static.
export function screenFull(id, start, end, { crop = SCR } = {}) {
  const h = Math.round(1920 * crop[3] / crop[2] / 2) * 2, y = Math.round((1080 - h) / 2);
  footage[id] = { src: "screen", crop, h };
  scene(id, start, end, { wrap: FULLW, exit: false,
    css: `.bg{position:absolute;left:0;top:0;width:1920px;height:1080px;background:#0d0d0c}
.v{position:absolute;left:0;top:${y}px;width:1920px;height:${h}px;overflow:hidden}`,
    html: `      <div class="bg"></div><div class="v">${clipTag(`${id}-v`, { src: "screen", crop, w: 1920, h, start, end, footage: id })}</div>`, tl: () => "" });
}
// shots(prefix, end, [[start, kind, opts], ...]): tiles [first start, end] with base shots and sets the face window for each.
//   "face"   his camera full frame, window off
//   "screen" his screen full frame, window in a corner (opts.face: "pip" bottom right, "pipL" bottom left; opts.crop)
//   "skip"   a graphic scene written by hand covers this stretch (it sets its own face place)
// A long shot is divided into pieces of SLICE seconds at most, on tenths of a second (same footage on both sides, so
// the division cannot be seen): each scene is one render slice, and a short slice is what makes a note cheap.
// Shot scenes are named by their start time in tenths of a second, so adding a shot never renames the ones after it.
const SLICE = 22;
export function shots(prefix, end, list) {
  list.forEach(([start, kind, opts = {}], i) => {
    const stop = i + 1 < list.length ? list[i + 1][0] : end;
    if (kind !== "face" && kind !== "screen") return;
    const n = Math.ceil((stop - start) / SLICE);
    const cuts = [start, ...Array.from({ length: n - 1 }, (_, j) => Math.round((start + ((j + 1) * (stop - start)) / n) * 10) / 10), stop];
    for (let k = 0; k + 1 < cuts.length; k++) {
      const a = cuts[k], b = cuts[k + 1], id = `${prefix}-${Math.round(a * 10)}`;
      if (kind === "face") { face(a, "off", 0); fullFace(id, a, b); }
      else { face(a, opts.face || "pip", 0); screenFull(id, a, b, opts); }
    }
  });
}
