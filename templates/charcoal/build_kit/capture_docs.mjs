// Captures every section of a real web page that the video quotes, and measures where the quoted sentences sit.
// Usage (from the project root):  node templates/charcoal/build_kit/capture_docs.mjs work/<id> [pull id ...]
//
// It reads work/<id>/pulls.json:
//   { "url": "https://...",                 the page
//     "ready": "h2",                        optional: a selector that must exist before capturing
//     "pulls": [ { "id": "r01-high",        file name; start it with the section it belongs to
//                  "heading": "calibrate-effort",   the id of the section's heading, or "top" for the page's opening
//                  "sentences": ["Start at high, the default on the Claude API."],   verbatim page text, in page order;
//                                                                                  the first one picks the paragraph shown
//                  "withHeading": false,    optional: the lifted excerpt keeps the section heading above the paragraph
//                  "above": 420 } ] }       optional: page px kept above the paragraph (default 900)
//
// For each pull it writes:
//   work/<id>/docs/<pull>.png + .json              the article column around the paragraph at 3x, and each sentence's
//                                                  line boxes relative to that image (what kit.mjs docs() reads)
//   work/<id>/full/assets/docs/<pull>.png          the same image, where the composition loads it
//   work/<id>/full/assets/docs/<pull>-ex.png/.json just the lifted excerpt at 5x: it is shown at 2.3x page size, so the
//                                                  3x page image would be soft in a 4K final
// A sentence the page no longer has is reported as MISSING and gets no highlight: fix pulls.json, never the image.
// Proven on platform.claude.com/docs only (1109-fable). Another site may need its own way to find the article column.
import puppeteer from "puppeteer-core";
import fs from "node:fs";
import path from "node:path";

const run = process.argv[2];
if (!run || !fs.existsSync(path.join(run, "pulls.json"))) { console.error("usage: node capture_docs.mjs work/<id> [pull id ...]   (needs work/<id>/pulls.json)"); process.exit(2); }
const want = process.argv.slice(3);
const { url: URL_, ready, pulls: PULLS } = JSON.parse(fs.readFileSync(path.join(run, "pulls.json"), "utf8"));
const DOCS = path.join(run, "docs"), ASSETS = path.join(run, "full", "assets", "docs");
fs.mkdirSync(DOCS, { recursive: true }); fs.mkdirSync(ASSETS, { recursive: true });
const ABOVE = 900, BELOW = 1100, PAD = 44;
const CHROME = process.env.CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe";

const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new", args: ["--hide-scrollbars"] });
let failed = 0;
// Two passes over the same layout: the page column at 3x, then only the excerpt at 5x.
for (const [SCALE, EX_ONLY] of [[3, false], [5, true]]) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1040, height: 1400, deviceScaleFactor: SCALE });
  await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "light" }]);
  await page.goto(URL_, { waitUntil: "networkidle2", timeout: 90000 });
  await page.waitForSelector(ready || "h2", { timeout: 30000 });
  await new Promise((r) => setTimeout(r, 1500));
  // Hide sticky bars and floating widgets without accepting anything.
  await page.evaluate(() => {
    for (const el of document.querySelectorAll("body *")) {
      const cs = getComputedStyle(el);
      if (cs.position === "fixed" || cs.position === "sticky") el.style.setProperty("display", "none", "important");
    }
  });

  for (const pull of PULLS) {
    if (want.length && !want.includes(pull.id)) continue;
    const info = await page.evaluate(
      ({ pull, ABOVE, BELOW, PAD }) => {
        const norm = (s) => s.replace(/[\u2018\u2019]/g, "'").replace(/\u00a0/g, " ");
        // heading "top" = the page's opening, before the first section.
        const top = pull.heading === "top";
        const h = top ? document.querySelector("h2") : document.getElementById(pull.heading);
        if (!h) return { error: "no heading " + pull.heading };
        let col = h.parentElement;
        while (col && col.querySelectorAll("h2").length < 3) col = col.parentElement;
        if (!col) return { error: "could not find the article column around " + pull.heading };
        // Every block between this heading and the next h2 (h3 sub-sections included); for "top", everything before the first h2.
        const blocks = [];
        const take = (el) => {
          if (el.tagName === "P" || el.tagName === "LI") blocks.push(el);
          else for (const b of el.querySelectorAll("p, li")) blocks.push(b);
        };
        if (top) { const before = []; for (let el = h.previousElementSibling; el; el = el.previousElementSibling) before.unshift(el); before.forEach(take); }
        else for (let el = h.nextElementSibling; el && el.tagName !== "H2"; el = el.nextElementSibling) take(el);
        const leaf = blocks.filter((b) => !b.querySelector("p, li"));
        const textOf = (b) => {
          const nodes = []; let full = "";
          const w = document.createTreeWalker(b, NodeFilter.SHOW_TEXT);
          for (let n = w.nextNode(); n; n = w.nextNode()) { nodes.push({ n, at: full.length }); full += n.data; }
          return { nodes, full };
        };
        const sx = window.scrollX, sy = window.scrollY;
        const found = [];
        for (const s of pull.sentences) {
          let hit = null;
          for (const b of leaf) {
            const { nodes, full } = textOf(b);
            const i = norm(full).indexOf(norm(s));
            if (i >= 0) { hit = { b, nodes, i, len: s.length }; break; }
          }
          found.push(hit);
        }
        if (!found[0]) return { error: "anchor sentence not found: " + pull.sentences[0] };
        const anchor = found[0].b;
        const ar = anchor.getBoundingClientRect(), cr = col.getBoundingClientRect();
        const above = pull.above ?? ABOVE;
        const clip = { x: Math.max(0, cr.left + sx - PAD), y: Math.max(0, ar.top + sy - above), width: cr.width + PAD * 2, height: above + BELOW };
        const rel = (r) => ({ x: r.left + sx - clip.x, y: r.top + sy - clip.y, w: r.width, h: r.height });
        const sentences = pull.sentences.map((s, k) => {
          const f = found[k];
          if (!f) return { text: s, missing: true };
          const locate = (i) => { let q = f.nodes.length - 1; while (f.nodes[q].at > i) q--; return [f.nodes[q].n, i - f.nodes[q].at]; };
          const range = document.createRange();
          range.setStart(...locate(f.i));
          const [en, eo] = locate(f.i + f.len - 1);
          range.setEnd(en, eo + 1);
          const lines = [];
          for (const r of range.getClientRects()) {
            if (r.width < 1) continue;
            const mid = r.top + r.height / 2;
            const line = lines.find((l) => mid > l.top && mid < l.bottom);
            if (line) { line.left = Math.min(line.left, r.left); line.right = Math.max(line.right, r.right); line.top = Math.min(line.top, r.top); line.bottom = Math.max(line.bottom, r.bottom); }
            else lines.push({ left: r.left, right: r.right, top: r.top, bottom: r.bottom });
          }
          return { text: s, sameBlock: f.b === anchor, block: rel(f.b.getBoundingClientRect()), lines: lines.map((l) => rel({ left: l.left, top: l.top, width: l.right - l.left, height: l.bottom - l.top })) };
        });
        return { clip, heading: rel(h.getBoundingClientRect()), headingText: h.innerText.trim(), block: rel(ar), blockText: anchor.innerText, sentences };
      },
      { pull, ABOVE, BELOW, PAD },
    );
    if (info.error) { console.log(pull.id, "ERROR", info.error); failed++; continue; }
    const withHeading = !!pull.withHeading;
    if (EX_ONLY) {
      // The region kit.mjs docs() lifts out (with or without the heading), snapped outward to whole pixels.
      const ey = withHeading ? info.heading.y - 18 : info.block.y - 14;
      const ax = Math.floor(info.clip.x + info.block.x - 20), ay = Math.floor(info.clip.y + ey);
      const aw = Math.ceil(info.block.w + 40) + 1, ah = Math.ceil(info.block.y + info.block.h + 13 - ey) + 1;
      await page.screenshot({ path: path.join(ASSETS, `${pull.id}-ex.png`), clip: { x: ax, y: ay, width: aw, height: ah }, captureBeyondViewport: true });
      fs.writeFileSync(path.join(ASSETS, `${pull.id}-ex.json`), JSON.stringify({ id: pull.id, scale: SCALE, ex: { x: ax - info.clip.x, y: ay - info.clip.y, w: aw, h: ah } }, null, 1));
    } else {
      await page.screenshot({ path: path.join(DOCS, `${pull.id}.png`), clip: info.clip, captureBeyondViewport: true });
      fs.writeFileSync(path.join(DOCS, `${pull.id}.json`), JSON.stringify({ id: pull.id, url: URL_ + (pull.heading === "top" ? "" : "#" + pull.heading), scale: SCALE, withHeading, captured: new Date().toISOString().slice(0, 10), ...info }, null, 1));
      fs.copyFileSync(path.join(DOCS, `${pull.id}.png`), path.join(ASSETS, `${pull.id}.png`));
    }
    const miss = info.sentences.filter((s) => s.missing).map((s) => s.text.slice(0, 40));
    if (miss.length) failed++;
    console.log(pull.id, EX_ONLY ? "excerpt 5x" : "page 3x", "block h", Math.round(info.block.h), "lines", info.sentences.map((s) => (s.lines || []).length).join("+"), miss.length ? "MISSING: " + miss.join(" | ") : "");
  }
  await page.close();
}
await browser.close();
if (failed) { console.error(`${failed} pull(s) with an ERROR or a MISSING sentence: fix pulls.json and run those ids again`); process.exit(1); }
