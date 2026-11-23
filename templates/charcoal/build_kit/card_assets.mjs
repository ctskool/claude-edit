// Makes the two still images the ffmpeg-only path needs for a "card" slice: a designed scene in which nothing moves
// except his footage inside one rounded rectangle (1113-nod: the Nod app in a card on n8n's page). Drawn once by
// headless Chrome (no video, no render):
//   <out>/bg-<name>.png     1920x1080 (x density): the scene's page with the card's frame and an empty card
//   <out>/mask-<name>.png   <w>x<h> grey: the rounded-corner alpha of the footage inside the card (white inside)
// Usage: node card_assets.mjs <page.html> <outdir> <name> <x> <y> <w> <h> <radius> [density]
import puppeteer from "puppeteer-core";
import os from "node:os";
import fs from "node:fs";
import path from "node:path";
const [html, out, name, x, y, w, h, radius, density = "1"] = process.argv.slice(2);
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
const b = await puppeteer.launch({ executablePath: EXE, headless: "shell", args: ["--hide-scrollbars", "--allow-file-access-from-files"] });
const p = await b.newPage();
await p.setViewport({ width: 1920, height: 1080, deviceScaleFactor: Number(density) });
fs.mkdirSync(out, { recursive: true });
await p.goto("file:///" + path.resolve(html).split(path.sep).join("/"), { waitUntil: "networkidle0" });
await p.evaluate(() => document.fonts.ready);
await p.screenshot({ path: `${out}/bg-${name}.png` });
await p.setContent(`<!doctype html><style>*{margin:0;padding:0}html,body{width:1920px;height:1080px;overflow:hidden;background:#000}
#c{position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;border-radius:${radius}px;background:#fff}</style><div id="c"></div>`);
await p.screenshot({ path: `${out}/mask-${name}.png`, clip: { x: Number(x), y: Number(y), width: Number(w), height: Number(h) } });
await b.close();
console.log("wrote", `${out}/bg-${name}.png`, `${out}/mask-${name}.png`);
