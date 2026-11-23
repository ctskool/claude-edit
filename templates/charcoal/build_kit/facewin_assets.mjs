// Makes the two still images the ffmpeg-only path needs for the face window, with the same CSS build.mjs gives #facewin,
// drawn once by headless Chrome (no video, no render):
//   <out>/ring-<place>.png   1920x1080 RGBA: the window's rings and drop shadow, transparent inside the window and elsewhere
//   <out>/mask-<place>.png   <w>x<h> grey: the rounded-corner alpha of the window itself (white inside)
// Usage: node facewin_assets.mjs <outdir> <place> <x> <y> <scale> <radius> [density] [ring]   (ring: video.json face.ring, a box-shadow)
import puppeteer from "puppeteer-core";
import path from "node:path";
import os from "node:os";
import fs from "node:fs";
const [out, place, x, y, scale, radius, density = "1", ring = ""] = process.argv.slice(2);
function hfChrome() {  // HF_CHROME, or the newest headless shell HyperFrames has downloaded for this user
  if (process.env.HF_CHROME) return process.env.HF_CHROME;
  const root = path.join(os.homedir(), ".cache", "hyperframes", "chrome", "chrome-headless-shell");
  const found = [];
  const walk = (dir) => { for (const e of fs.existsSync(dir) ? fs.readdirSync(dir, { withFileTypes: true }) : []) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) walk(full); else if (/^chrome-headless-shell(\.exe)?$/.test(e.name)) found.push(full); } };
  walk(root);
  if (!found.length) throw new Error(`no headless Chrome under ${root}: run any hyperframes render once, or set HF_CHROME`);
  return found.sort().at(-1);
}
const EXE = hfChrome();
const css = (inner, shadow) => `<!doctype html><style>*{margin:0;padding:0;box-sizing:border-box}html,body{width:1920px;height:1080px;overflow:hidden;background:transparent}
#facewin{position:absolute;left:0;top:0;width:480px;height:600px;overflow:hidden;border-radius:${radius}px;background:${inner};transform-origin:0 0;transform:translate(${x}px,${y}px) scale(${scale});
${shadow ? `box-shadow:${ring || "0 0 0 4px #1a1917,0 0 0 5px #423f3b,0 30px 60px -20px rgba(0,0,0,.8)"};` : ""}}</style><div id="facewin"></div>`;
const b = await puppeteer.launch({ executablePath: EXE, headless: "shell", args: ["--hide-scrollbars"] });
const p = await b.newPage();
await p.setViewport({ width: 1920, height: 1080, deviceScaleFactor: Number(density) });
fs.mkdirSync(out, { recursive: true });
await p.setContent(css("transparent", true));
await p.screenshot({ path: `${out}/ring-${place}.png`, omitBackground: true });
await p.setContent(css("#fff", false).replace("background:transparent}", "background:#000}"));
const w = Math.round(480 * scale), h = Math.round(600 * scale);
await p.screenshot({ path: `${out}/mask-${place}.png`, clip: { x: Number(x), y: Number(y), width: w, height: h } });
await b.close();
console.log("wrote", `${out}/ring-${place}.png`, `${out}/mask-${place}.png`, `${w}x${h}`);
