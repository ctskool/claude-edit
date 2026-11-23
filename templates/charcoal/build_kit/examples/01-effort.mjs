// EXAMPLE, read only: rule 1 of work/1109-fable, approved by Chase on 2026-11-09. Match how it is built.
// Its words, numbers and captures belong to that video: never copy them into another one.
// In a project this file sits in tools/sections/, which is why it imports ../kit.mjs.
import fs from "node:fs";
import { END, cue, r, r3, chars, selX, selector, scene, face, docs, blurIn, show, slideIn, type, blink, WIDE, RIGHT } from "../kit.mjs";

// RULE 1, 17.28 to 128.72 s: run it on high.
face(17.0, "right", 0.6);
face(23.85, "corner");
face(29.3, "right", 0.55);
face(31.95, "corner");
face(74.25, "left", 0.7);
face(109.85, "right", 0.75);
// b04 "Now, the first prompting rule change has to do with effort level."
scene("r1title", 17.283, 20.15, {
  css: `.box{position:absolute;left:0;top:156px;width:1120px;height:700px;display:flex;flex-direction:column;justify-content:center}
.h{margin-top:30px;font-size:164px;line-height:.98;letter-spacing:-0.04em}
.s{margin-top:40px;font-size:34px}`,
  html: `      <div class="box"><p class="k" id="r1title-k">// <b>rule 01</b> of 10</p>
      <h1 class="h">${chars("Run it")}<br />${chars("on high.")}<span class="cur" id="r1title-cur"></span></h1>
      <p class="s" id="r1title-s">The effort setting.</p></div>`,
  tl: (T) => [show("#r1title-k", 0.2, 0.2), type("#r1title-wrap .h .c", 0.4, 0.045), blink("#r1title-cur", 1.08, 1.9), blurIn("#r1title-s", T(cue("effort level", 17))) ].join("\n"),
});
// b05 "You should be using Fable 5.2 on a high effort setting."
{
  const tH = cue("high effort setting", 20);
  scene("dial", 20.15, 24.07, {
    css: `.h{position:absolute;left:0;top:250px}
.s{position:absolute;left:0;top:372px;margin:0}
.sel{position:absolute;left:0;top:476px}
.cap{position:absolute;left:0;top:602px;width:1060px;display:flex;justify-content:space-between;font:400 26px/1 "Geist Mono",monospace;color:#aaa69d}`,
    html: `      <h2 class="h" id="dial-h">Set effort to <em>high</em>.</h2>
      <p class="s" id="dial-s">fable 5.2 · effort level</p>
      ${selector("dial-sel")}
      <div class="cap" id="dial-cap"><span>less thinking</span><span>more thinking, time and tokens</span></div>`,
    tl: (T) => [blurIn("#dial-h", 0.08), show("#dial-s", 0.25, 0.2), blurIn("#dial-sel", 0.3, 0.3), show("#dial-cap", 0.6, 0.2),
      `    tl.fromTo("#dial-sel-mk", { x: ${selX(1)}, backgroundColor: "#66635d" }, { x: ${selX(2)}, backgroundColor: "#ff6a3d", duration: 0.45, ease: "expo.out" }, ${T(tH - 0.05)});`,
      `    tl.fromTo("#dial-sel-o1", { color: "#ebe8e0" }, { color: "#aaa69d", duration: 0.15, ease: "none" }, ${T(tH - 0.05)});`,
      `    tl.fromTo("#dial-sel-o2", { color: "#aaa69d" }, { color: "#0d0d0c", duration: 0.15, ease: "none" }, ${T(tH + 0.1)});`].join("\n"),
  });
}
// b06 "this is what it defaults to in the API, but in Claude Code, you will see it defaulting to medium."
{
  const D = docs("dflt", "r01-high", { withHeading: true, headY: 190, exY: 150, tag: "§ calibrate effort" });
  const tA = cue("defaults to in the API", 24), tC = cue("in Claude Code", 24), tM = cue("medium", tC);
  const y = 150 + D.EX.h + 44;
  scene("dflt", 24.07, 29.51, {
    wrap: WIDE,
    css: D.css + `
.cc{position:absolute;left:${r(D.EX.x - 96)}px;top:${r(y)}px;width:${r(D.EX.w)}px;height:84px;display:flex;align-items:center;gap:26px;font:500 34px/1 "Geist Mono",monospace;color:#ebe8e0;background:#1a1917;box-shadow:0 0 0 14px #1a1917}
.chip{background:#ff6a3d;color:#0d0d0c;font-weight:600;padding:12px 20px}
.cc .src{margin-left:auto}`,
    html: D.html + `
      <div class="cc" id="dflt-cc">Claude Code default <span class="mut">→</span> <span class="chip" id="dflt-chip">medium</span><span class="src">system card, fig. 6.5.2.B</span></div>`,
    tl: (T) => [D.tl(0.08, [T(Math.max(tA, 25.4))]), show("#dflt-cc", T(tC - 0.1), 0.2), `    tl.fromTo("#dflt-chip", { opacity: 0, scale: 1.2 }, { opacity: 1, scale: 1, duration: 0.35, ease: "expo.out" }, ${T(tM - 0.05)});`].join("\n"),
  });
}
// b07 "Now, why do I say that we should be on high?"
scene("why", 29.51, 32.167, {
  css: `.box{position:absolute;left:0;top:156px;width:1120px;height:700px;display:flex;flex-direction:column;justify-content:center}
.h{font-size:190px;letter-spacing:-0.04em}`,
  html: `      <div class="box"><h2 class="h">${chars("Why ")}<em>${chars("high")}</em>${chars("?")}</h2></div>`,
  tl: (T) => type("#why-wrap .h .c", T(cue("why do I say", 29) - 0.05), 0.05),
});
// b08-b09 "high is where we ... get the most bang for our buck" / "from medium to high ... biggest jump"
{
  const D = docs("gain", "r01-gain", { tag: "§ calibrate effort", headY: 300 });
  scene("gain", 32.167, 43.73, {
    wrap: WIDE,
    css: D.css,
    html: D.html,
    tl: (T) => D.tl(0.08, [T(cue("most bang for our buck", 32) - 0.2), T(cue("from medium to high", 38) - 0.2)]),
  });
}
// b10 "And this kind of plays out across a number of different benchmarks."
{
  const B = [["FrontierCode 2.0", "agentic coding"], ["CursorBench 4.0", "real-world coding"], ["HLE · WANDR", "knowledge work"]];
  scene("bench", 43.73, 48.29, {
    wrap: WIDE,
    css: `.h{position:absolute;left:0;top:210px;font-size:104px}
.s{position:absolute;left:0;top:330px;margin:0}
.list{position:absolute;left:0;top:420px;width:1200px}
.row{height:76px;font-size:38px}
.br{height:76px}.br::after{top:37px}.row.last .br::before{bottom:37px}
.row .mut{margin-left:auto;font-weight:400;font-size:30px}`,
    html: `      <h2 class="h" id="bench-h">It shows up in the benchmarks.</h2>
      <p class="s" id="bench-s">system-card/capabilities/</p>
      <div class="list">${B.map(([a, b], i) => `<div class="row${i === 2 ? " last" : ""}" id="bench-r${i}"><span class="br"></span><span id="bench-n${i}">${a}</span><span class="mut">${b}</span></div>`).join("")}</div>`,
    tl: (T) => [blurIn("#bench-h", 0.08), show("#bench-s", 0.3, 0.2), ...B.map((_, i) => show(`#bench-r${i}`, 0.6 + i * 0.3, 0.06)),
      `    tl.fromTo("#bench-n0", { color: "#ebe8e0" }, { color: "#ff7a50", duration: 0.2, ease: "none" }, ${T(48.29 - 0.9)});`].join("\n"),
  });
}
// b11-b16 the FrontierCode 2.0 chart, revealed in stages
{
  const box = { l: 150, r: 1400, t: 262, b: 756 };
  const X = (c) => box.l + ((Math.log10(c) - Math.log10(1.6)) / (Math.log10(60) - Math.log10(1.6))) * (box.r - box.l);
  const Y = (s) => box.b - ((s - 30) / (52 - 30)) * (box.b - box.t);
  const F = [["low", 2.1, 34.2], ["medium", 2.48, 37.6], ["high", 6.72, 45.3], ["xhigh", 14.19, 49.1], ["max", 44.7, 45.7]];
  const OX = [5.18, 43.4], OM = [12.82, 45.5];
  const pts = F.map(([, c, s]) => `${r(X(c))},${r(Y(s))}`).join(" ");
  const len = F.slice(1).reduce((a, [, c, s], i) => a + Math.hypot(X(c) - X(F[i][1]), Y(s) - Y(F[i][2])), 0);
  const tLine = cue("If we look at high", 52), t453 = cue("45.3", 52), tOx = cue("Opus 5.5 on extra high", 59), tOm = cue("on a max setting", 64), tCost = cue("$12.82", 68), tHalf = cue("about half that", 72);
  const lab = (id, x, y, html, cls = "") => `<div class="lab ${cls}" id="chart-${id}" style="left:${r(x)}px;top:${r(y)}px">${html}</div>`;
  scene("chart", 48.29, 74.48, {
    wrap: WIDE,
    css: `.h{position:absolute;left:0;top:96px;font-size:80px}
.s{position:absolute;left:0;top:186px;margin:0;font-size:28px}
svg{position:absolute;left:0;top:0;width:1728px;height:1080px;overflow:visible}
.ax{font:400 24px "Geist Mono",monospace;fill:#aaa69d}
.lab{position:absolute;white-space:nowrap;font:500 28px/1.25 "Geist Mono",monospace;color:#ebe8e0}
.lab small{display:block;font-size:24px;font-weight:400;color:#aaa69d}
.lab.o{color:#ff7a50}
.pill{background:#ff6a3d;color:#0d0d0c;font-weight:600;padding:8px 14px}
.leg{position:absolute;left:${box.l}px;top:${box.b + 70}px;display:flex;gap:44px;align-items:center;font:400 24px/1 "Geist Mono",monospace;color:#aaa69d}
.leg i{display:inline-block;width:16px;height:16px;border-radius:50%;margin-right:12px;vertical-align:-2px}`,
    html: `      <h2 class="h" id="chart-h">FrontierCode 2.0</h2>
      <p class="s" id="chart-s">agentic coding · score against cost per task</p>
      <svg viewBox="0 0 1728 1080" id="chart-svg">
        <g id="chart-axes">
          <line x1="${box.l}" y1="${box.b}" x2="${box.r}" y2="${box.b}" stroke="#66635d" stroke-width="2" />
          <line x1="${box.l}" y1="${box.t}" x2="${box.l}" y2="${box.b}" stroke="#66635d" stroke-width="2" />
          ${[35, 40, 45, 50].map((s) => `<line x1="${box.l}" y1="${r(Y(s))}" x2="${box.r}" y2="${r(Y(s))}" stroke="#34322e" stroke-width="1" stroke-dasharray="4 8" /><text class="ax" x="${box.l - 18}" y="${r(Y(s) + 8)}" text-anchor="end">${s}%</text>`).join("")}
          ${[2, 5, 10, 20, 40].map((c) => `<line x1="${r(X(c))}" y1="${box.b}" x2="${r(X(c))}" y2="${box.b + 10}" stroke="#66635d" stroke-width="2" /><text class="ax" x="${r(X(c))}" y="${box.b + 42}" text-anchor="middle">$${c}</text>`).join("")}
        </g>
        <polyline id="chart-line" points="${pts}" fill="none" stroke="#ebe8e0" stroke-width="4" stroke-linejoin="round" stroke-dasharray="${r(len)}" stroke-dashoffset="${r(len)}" />
        ${F.map(([n, c, s], i) => `<circle id="chart-p${i}" cx="${r(X(c))}" cy="${r(Y(s))}" r="9" fill="#ebe8e0" />`).join("")}
        <circle id="chart-ring" cx="${r(X(6.72))}" cy="${r(Y(45.3))}" r="20" fill="none" stroke="#ff6a3d" stroke-width="4" />
        <line id="chart-oline" x1="${r(X(OX[0]))}" y1="${r(Y(OX[1]))}" x2="${r(X(OM[0]))}" y2="${r(Y(OM[1]))}" stroke="#8a867d" stroke-width="3" stroke-dasharray="3 7" />
        <circle id="chart-ox" cx="${r(X(OX[0]))}" cy="${r(Y(OX[1]))}" r="9" fill="#1a1917" stroke="#aaa69d" stroke-width="3" />
        <circle id="chart-om" cx="${r(X(OM[0]))}" cy="${r(Y(OM[1]))}" r="9" fill="#1a1917" stroke="#aaa69d" stroke-width="3" />
        <line id="chart-dropf" x1="${r(X(6.72))}" y1="${r(Y(45.3) + 22)}" x2="${r(X(6.72))}" y2="${box.b}" stroke="#ff6a3d" stroke-width="2" stroke-dasharray="4 6" />
        <line id="chart-dropo" x1="${r(X(12.82))}" y1="${r(Y(45.5) + 12)}" x2="${r(X(12.82))}" y2="${box.b}" stroke="#aaa69d" stroke-width="2" stroke-dasharray="4 6" />
        <line id="chart-brk" x1="${r(X(6.72))}" y1="${box.b - 34}" x2="${r(X(12.82))}" y2="${box.b - 34}" stroke="#ff6a3d" stroke-width="4" />
      </svg>
      ${F.map(([n, c, s], i) => i === 2 ? "" : lab(`n${i}`, X(c) + (i === 4 ? -40 : 18), Y(s) + (i === 3 ? -52 : 14), n, "mut")).join("")}
      ${lab("high", X(6.72) - 330, Y(45.3) - 118, `<span class="pill">Fable 5.2 · high</span><small style="margin-top:12px;color:#ebe8e0;font-size:30px"><b id="chart-453">45.3%</b> at <b>$6.72</b></small>`)}
      ${lab("oxl", X(OX[0]) + 4, Y(OX[1]) + 22, `Opus 5.5 · xhigh<small>43.4%</small>`, "mut")}
      ${lab("oml", X(OM[0]) + 26, Y(OM[1]) + 16, `Opus 5.5 · max<small>45.5%</small>`, "mut")}
      ${lab("ocost", X(12.82) + 14, box.b - 92, `$12.82`, "mut")}
      ${lab("fcost", X(6.72) - 112, box.b - 92, `$6.72`, "o")}
      ${lab("half", (X(6.72) + X(12.82)) / 2 - 92, box.b - 150, `<span class="pill">about half</span>`)}
      <div class="leg" id="chart-leg"><span><i style="background:#ebe8e0"></i>Fable 5.2</span><span><i style="box-shadow:inset 0 0 0 3px #aaa69d"></i>Opus 5.5</span><span>source: system card §8.4 and launch page</span></div>`,
    tl: (T) => [blurIn("#chart-h", 0.08), show("#chart-s", 0.3, 0.2), show("#chart-axes", 0.5, 0.3), show("#chart-leg", 0.9, 0.3),
      `    tl.fromTo("#chart-line", { strokeDashoffset: ${r(len)} }, { strokeDashoffset: 0, duration: 1.3, ease: "power2.inOut" }, ${T(tLine - 0.6)});`,
      ...F.map((_, i) => `    tl.fromTo("#chart-p${i}", { opacity: 0 }, { opacity: 1, duration: 0.1, ease: "none" }, ${T(tLine - 0.6 + [0, 0.12, 0.62, 0.95, 1.3][i])});`),
      ...[0, 1, 3, 4].map((i) => show(`#chart-n${i}`, T(tLine + 0.75), 0.25)),
      `    tl.fromTo("#chart-ring", { opacity: 0, scale: 2.2, transformOrigin: "50% 50%" }, { opacity: 1, scale: 1, duration: 0.4, ease: "expo.out" }, ${T(tLine + 0.75)});`,
      `    tl.fromTo("#chart-p2", { fill: "#ebe8e0" }, { fill: "#ff6a3d", duration: 0.2, ease: "none", immediateRender: false }, ${T(tLine + 0.75)});`,
      blurIn("#chart-high", T(t453 - 0.5), 0.3),
      show("#chart-ox", T(tOx - 0.2), 0.15), slideIn("#chart-oxl", T(tOx - 0.1)),
      show("#chart-oline", T(tOm - 0.4), 0.3), show("#chart-om", T(tOm - 0.2), 0.15), slideIn("#chart-oml", T(tOm - 0.1)),
      show("#chart-dropo", T(tCost - 0.4), 0.3), slideIn("#chart-ocost", T(tCost - 0.15)),
      show("#chart-dropf", T(tHalf - 0.6), 0.3), slideIn("#chart-fcost", T(tHalf - 0.5)),
      `    tl.fromTo("#chart-brk", { scaleX: 0, transformOrigin: "0 50%" }, { scaleX: 1, duration: 0.4, ease: "expo.out" }, ${T(tHalf - 0.2)});`,
      `    tl.fromTo("#chart-half", { opacity: 0, scale: 1.2 }, { opacity: 1, scale: 1, duration: 0.35, ease: "expo.out" }, ${T(tHalf)});`].join("\n"),
  });
}
// b17 "So we're getting Opus 5.5 max performance at half the cost."
{
  const tP = cue("max performance", 74), tC = cue("half the cost", 74);
  scene("half", 74.48, 79.15, {
    wrap: RIGHT,
    css: `.h{position:absolute;left:0;top:176px;font-size:92px;line-height:1.03}
.tb{position:absolute;left:0;top:540px;width:1072px;border-top:1px dashed #423f3b}
.tr{display:flex;align-items:center;height:92px;border-bottom:1px dashed #423f3b;font:500 34px/1 "Geist Mono",monospace;color:#ebe8e0}
.tr span:nth-child(1){flex:1}
.tr span:nth-child(2){width:210px;text-align:right}
.tr span:nth-child(3){width:230px;text-align:right}`,
    html: `      <h2 class="h"><span id="half-a">Opus 5.5 max<br />performance.</span><br /><em><span id="half-b">Half the cost.</span></em></h2>
      <div class="tb" id="half-tb">
        <div class="tr" id="half-r0"><span>Fable 5.2 · high</span><span>45.3%</span><span class="o">$6.72</span></div>
        <div class="tr" id="half-r1"><span class="mut">Opus 5.5 · max</span><span class="mut">45.5%</span><span class="mut">$12.82</span></div>
      </div>`,
    tl: (T) => [blurIn("#half-a", T(Math.max(74.7, tP - 0.7))), blurIn("#half-b", T(tC - 0.15)), show("#half-tb", 0.6, 0.2), slideIn("#half-r0", 0.7), slideIn("#half-r1", 0.95)].join("\n"),
  });
}
// b18-b21 medium against high
{
  const t376 = cue("37.6%", 86), tV = cue("Versus", 88), tCost = cue("$2.48", 90);
  scene("medium", 79.15, 95.13, {
    wrap: RIGHT,
    css: `.h{position:absolute;left:0;top:150px;font-size:96px;line-height:1.02}
.s{position:absolute;left:0;top:372px;margin:0}
.rw{position:absolute;left:0;width:1072px}
.lb{display:flex;align-items:baseline;gap:22px;font:500 32px/1 "Geist Mono",monospace;color:#ebe8e0}
.chip{font:600 22px/1 "Geist Mono",monospace;color:#0d0d0c;background:#aaa69d;padding:7px 12px;transform:translateY(-4px)}
.num{margin-left:auto;font:600 84px/0.9 "Hanken Grotesk",sans-serif;letter-spacing:-0.04em}
.cost{width:250px;text-align:right;font:400 28px/1 "Geist Mono",monospace;color:#aaa69d}
.trk{margin-top:14px;height:40px;box-shadow:inset 0 0 0 1px #423f3b}
.bar{height:100%}`,
    html: `      <h2 class="h" id="medium-h">Medium gives up<br />a lot of score.</h2>
      <p class="s" id="medium-s">FrontierCode 2.0 · same benchmark</p>
      <div class="rw" style="top:470px" id="medium-r0"><div class="lb">medium <span class="chip">Claude Code default</span><span class="num" id="medium-n0">37.6%</span><span class="cost" id="medium-c0">$2.48 per task</span></div><div class="trk"><div class="bar" id="medium-b0" style="width:${r(37.6 / 52 * 100)}%;background:#aaa69d"></div></div></div>
      <div class="rw" style="top:640px" id="medium-r1"><div class="lb">high<span class="num o" id="medium-n1">45.3%</span><span class="cost" id="medium-c1">$6.72 per task</span></div><div class="trk"><div class="bar" id="medium-b1" style="width:${r(45.3 / 52 * 100)}%;background:#ff6a3d"></div></div></div>`,
    tl: (T) => [blurIn("#medium-h", 0.3), show("#medium-s", 0.6, 0.2), show("#medium-r0", T(cue("Medium", 79) - 0.1), 0.2), show("#medium-r1", T(cue("dropping significantly", 79) - 0.3), 0.2),
      `    tl.fromTo("#medium-b0", { scaleX: 0, transformOrigin: "0 50%" }, { scaleX: 1, duration: 0.8, ease: "power3.out" }, ${T(cue("Medium", 79))});`,
      `    tl.fromTo("#medium-b1", { scaleX: 0, transformOrigin: "0 50%" }, { scaleX: 1, duration: 0.8, ease: "power3.out" }, ${T(cue("dropping significantly", 79) - 0.2)});`,
      blurIn("#medium-n0", T(t376 - 0.1), 0.25), blurIn("#medium-n1", T(tV + 0.25), 0.25), slideIn("#medium-c0", T(tCost - 0.2)), slideIn("#medium-c1", T(tCost + 0.9))].join("\n"),
  });
}
// b22-b23 problems beyond Opus 5.5
{
  const tT = cue("technically challenging", 95), tL = cue("long-running", 95), tQ = cue("what's the point", 95), tO = cue("I could probably", 100);
  scene("scope", 95.13, 110.067, {
    wrap: RIGHT,
    css: `.h{position:absolute;left:0;top:170px;font-size:84px;line-height:1.04}
.list{position:absolute;left:0;top:384px}
.row{height:72px;font-size:36px}
.br{height:72px}.br::after{top:35px}.row.last .br::before{bottom:35px}
.q{position:absolute;left:-4px;top:600px;font:600 76px/1.04 "Hanken Grotesk",sans-serif;letter-spacing:-0.035em;color:#ebe8e0}
.q em{font-style:normal;color:#ff7a50}
.a{position:absolute;left:0;top:800px;font:400 32px/1 "Geist Mono",monospace;color:#aaa69d}`,
    html: `      <h2 class="h" id="scope-h">If the problem is<br />beyond Opus 5.5:</h2>
      <div class="list"><div class="row" id="scope-r0"><span class="br"></span>technically very hard</div><div class="row last" id="scope-r1"><span class="br"></span>long-running agentic work</div></div>
      <p class="q" id="scope-q">Why run Fable 5.2<br />on <em>medium or low</em>?</p>
      <p class="a" id="scope-a">→ Opus could do that job.</p>`,
    tl: (T) => [blurIn("#scope-h", 0.35), show("#scope-r0", T(tT - 0.1), 0.08), show("#scope-r1", T(tL - 0.1), 0.08), blurIn("#scope-q", T(tQ - 0.1), 0.3), slideIn("#scope-a", T(tO + 0.1))].join("\n"),
  });
}
// b24-b27 start at high, push to xhigh, avoid max
{
  const tS = cue("starting with a high setting", 110), tX = cue("push it to extra high", 114), tA = cue("stay away", 118), tM = cue("paying a ton of money", 121), tB = cue("below even extra high", 121);
  scene("pick", 110.067, 128.717, {
    css: `.h{position:absolute;left:0;top:150px}
.sel{position:absolute;left:0;top:300px}
.cap{position:absolute;left:0;top:420px;width:1060px;height:40px;font:500 28px/1 "Geist Mono",monospace;color:#aaa69d}
.cap span{position:absolute;top:0;white-space:nowrap}
.x{position:absolute;left:${selX(4)}px;top:300px;width:200px;height:96px}
.x .ln{position:absolute;left:14px;right:14px;top:46px;height:4px;transform:rotate(-24deg)}
.x i{position:absolute;inset:0;background:#ff6a3d}
.tb{position:absolute;left:0;top:520px;width:1060px;border-top:1px dashed #423f3b}
.tr{display:flex;align-items:center;height:92px;border-bottom:1px dashed #423f3b;font:500 34px/1 "Geist Mono",monospace;color:#ebe8e0}
.tr span:nth-child(1){flex:1}
.tr span:nth-child(2){width:200px;text-align:right}
.tr span:nth-child(3){width:360px;text-align:right;white-space:nowrap}
.note{position:absolute;left:0;top:738px;font:500 30px/1 "Geist Mono",monospace;color:#ff7a50}`,
    html: `      <h2 class="h" id="pick-h">Start at <em>high</em>.</h2>
      ${selector("pick-sel")}
      <div class="x" id="pick-x"><div class="ln"><i></i></div></div>
      <div class="cap"><span id="pick-c1" style="right:${1060 - selX(3) - 200}px">if high isn't enough ↑</span><span id="pick-c2" style="left:${selX(4) + 62}px;color:#ff7a50">avoid</span></div>
      <div class="tb" id="pick-tb">
        <div class="tr" id="pick-r0"><span>xhigh</span><span>49.1%</span><span>$14.19 per task</span></div>
        <div class="tr" id="pick-r1"><span>max</span><span class="o" id="pick-ms">45.7%</span><span class="o" id="pick-mc">$44.70 per task</span></div>
      </div>
      <p class="note" id="pick-note">lower score, about 3× the cost</p>`,
    tl: (T) => [blurIn("#pick-h", 0.35), blurIn("#pick-sel", 0.5, 0.3),
      `    tl.fromTo("#pick-sel-mk", { x: ${selX(2)}, opacity: 0 }, { x: ${selX(2)}, opacity: 1, duration: 0.25, ease: "power2.out" }, ${T(Math.max(110.9, tS - 0.3))});`,
      `    tl.fromTo("#pick-sel-o2", { color: "#aaa69d" }, { color: "#0d0d0c", duration: 0.15, ease: "none" }, ${T(Math.max(110.9, tS - 0.3) + 0.08)});`,
      `    tl.fromTo("#pick-sel-o3", { color: "#aaa69d", boxShadow: "inset 0 0 0 1.5px #423f3b" }, { color: "#ebe8e0", boxShadow: "inset 0 0 0 3px #ebe8e0", duration: 0.25, ease: "power2.out" }, ${T(tX + 0.3)});`,
      slideIn("#pick-c1", T(tX - 0.1)),
      `    tl.fromTo("#pick-x i", { scaleX: 0, transformOrigin: "0 50%" }, { scaleX: 1, duration: 0.3, ease: "expo.out" }, ${T(tA)});`,
      `    tl.fromTo("#pick-sel-o4", { opacity: 1 }, { opacity: 0.45, duration: 0.2, ease: "none" }, ${T(tA)});`,
      show("#pick-c2", T(tA + 0.15), 0.15), show("#pick-tb", T(tM - 0.5), 0.2), slideIn("#pick-r0", T(tM - 0.35)), slideIn("#pick-r1", T(tM)), blurIn("#pick-note", T(tB - 0.2), 0.3)].join("\n"),
  });
}

