// EXAMPLE, read only: the intro of work/1109-fable, approved by Chase on 2026-11-09. Match how it is built.
// Its words, numbers and captures belong to that video: never copy them into another one.
// In a project this file sits in tools/sections/, which is why it imports ../kit.mjs.
import fs from "node:fs";
import { END, cue, r, r3, chars, selX, selector, scene, face, docs, blurIn, show, slideIn, type, blink, WIDE, RIGHT } from "../kit.mjs";

// INTRO, 0 to 17.28 s: the hook, "Anthropic changed the rules", the ten rules.
face(0, "right");
face(9.0, "corner");
// b01 "You're prompting Fable 5.2 wrong."
{
  const words = [["You're", "You're"], ["prompting", "prompting"], ["Fable", "Fable"], ["5.2", "5.2"], ["wrong", "wrong."]];
  const t = words.map(([w]) => cue(w, 0));
  scene("hook", 0, 2.95, {
    css: `.box{position:absolute;left:0;top:156px;width:1140px;height:700px;display:flex;flex-direction:column;justify-content:center}
.h{font-size:150px;line-height:1.0}`,
    html: `      <div class="box"><h1 class="h"><span id="hook-w0">You're</span> <span id="hook-w1">prompting</span><br /><span id="hook-w2">Fable</span> <span id="hook-w3">5.2</span> <em><span id="hook-w4">wrong.</span></em><span class="cur" id="hook-cur"></span></h1></div>`,
    tl: (T) => [...t.map((x, i) => `    tl.fromTo("#hook-w${i}", { opacity: 0 }, { opacity: 1, duration: 0.01, ease: "none" }, ${T(Math.max(0.02, x - 0.03))});`), blink("#hook-cur", T(t[4] + 0.05), T(2.6))].join("\n"),
  });
}
// b02 "Anthropic has changed the rules, whether it's what effort level ... or how we approach sub-agents."
{
  const d = JSON.parse(fs.readFileSync("../docs/r00-top.json", "utf8"));
  const cw = 800, sp = cw / d.clip.width, ch = 880;
  const hl = d.sentences.map((s) => s.lines[0]);
  const tE = cue("effort level", 2.9), tS = cue("sub-agents", 2.9);
  scene("changed", 2.95, 9.27, {
    css: `.tag{position:absolute;left:110px;top:54px;display:flex;align-items:center;gap:22px;font:500 28px/1 "Geist Mono",monospace;color:#aaa69d}
.tag b{font-weight:500;color:#ff7a50}.tag i{display:block;width:12px;height:12px;background:#aaa69d}
.page{position:absolute;left:110px;top:110px;width:${cw}px;height:${ch}px;overflow:hidden;background:#fcfbf8;box-shadow:0 0 0 1px #423f3b}
.pimg{position:absolute;left:0;top:0;width:${cw}px;height:${r(d.clip.height * sp)}px}
.pimg img{display:block;width:100%;height:100%}
.hl{position:absolute;display:block;background:rgba(255,106,61,.5);mix-blend-mode:multiply}`,
    html: `      <div class="tag" id="changed-tag"><i></i><b>platform.claude.com/docs</b><span>the official prompting guide</span></div>
      <div class="page" id="changed-page"><div class="pimg" id="changed-img" data-layout-allow-overflow><img src="assets/docs/r00-top.png" alt="" />
        ${hl.map((l, i) => `<i class="hl" id="changed-hl${i}" style="left:${r((l.x - 3) * sp)}px;top:${r((l.y - 2) * sp)}px;width:${r((l.w + 6) * sp)}px;height:${r((l.h + 4) * sp)}px"></i>`).join("")}
      </div></div>`,
    tl: (T) => [
      `    tl.fromTo("#changed-page", { opacity: 0, y: 36, filter: "blur(12px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.45, ease: "expo.out" }, 0.08);`,
      show("#changed-tag", 0.4, 0.2),
      `    tl.fromTo("#changed-img", { y: 0 }, { y: -150, duration: 1.3, ease: "power2.inOut" }, ${T(tE - 1.5)});`,
      `    tl.fromTo("#changed-hl0", { scaleX: 0, transformOrigin: "0 50%" }, { scaleX: 1, duration: 0.5, ease: "power2.inOut" }, ${T(tE - 0.1)});`,
      `    tl.fromTo("#changed-hl1", { scaleX: 0, transformOrigin: "0 50%" }, { scaleX: 1, duration: 0.5, ease: "power2.inOut" }, ${T(tS - 0.1)});`,
    ].join("\n"),
  });
}
// b03 "So today ... the 10 biggest prompting rule changes ..."
{
  const RULES = ["Run it on high", "Make it prove its work", "Tell it to finish the job", "Clean up your old prompts", "You can't stop it thinking", "Don't ask for its reasoning", "Say who owns the code", "Don't push it to delegate", "Ask for updates", "Prompt for length and tone"];
  const t10 = cue("10 biggest", 9);
  scene("ten", 9.27, 17.283, {
    wrap: WIDE,
    css: `.h{position:absolute;left:0;top:120px;font-size:112px}
.s{position:absolute;left:0;top:236px;margin:0}
.col{position:absolute;top:340px;width:680px}`,
    html: `      <h2 class="h" id="ten-h">The <em>10</em> biggest rule changes.</h2>
      <p class="s" id="ten-s">fable-5.2/prompting-rules/</p>
      ${[0, 1].map((c) => `<div class="col" style="left:${c * 720}px">${RULES.slice(c * 5, c * 5 + 5).map((n, i) => `<div class="row${i === 4 ? " last" : ""}" id="ten-r${c * 5 + i}"><span class="br"></span><span class="n">${String(c * 5 + i + 1).padStart(2, "0")}</span>${n}</div>`).join("")}</div>`).join("\n      ")}`,
    tl: (T) => [blurIn("#ten-h", 0.1), show("#ten-s", 0.45, 0.2), ...RULES.map((_, i) => show(`#ten-r${i}`, T(t10 + 0.2 + i * 0.33), 0.06))].join("\n"),
  });
}

