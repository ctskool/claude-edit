#!/usr/bin/env node
// Rebuilds everything that shows the editor off: the gallery page, its clips and posters, and the moving cards in the README.
// It reads docs/catalog.json. Clips are cut from your own project folder, which never ships:
//   node scripts/build-gallery.mjs --from "C:/path/to/your/project"   everything
//   node scripts/build-gallery.mjs --page                              only the page and the README, when just the wording changed
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DOCS = path.join(ROOT, "docs");
const CARDS = path.join(ROOT, "media", "cards");
const PER_ROW = 3;
const argv = process.argv.slice(2);
const pageOnly = argv.includes("--page");
const fromAt = argv.indexOf("--from");
const FROM = fromAt >= 0 ? path.resolve(argv[fromAt + 1]) : null;
if (!pageOnly && !FROM) throw new Error("pass --from <your project folder>, or --page");

const catalog = JSON.parse(fs.readFileSync(path.join(DOCS, "catalog.json"), "utf8"));
const items = catalog.groups.flatMap((group) => group.items);

const ffmpeg = (...args) => execFileSync("ffmpeg", ["-y", "-v", "error", ...args], { stdio: "inherit" });
const seconds = (file) =>
  Number(execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", file], { encoding: "utf8" }));
// A source is in your project folder, or in this repo's renders/ when the item says local (the player capture).
const source = (rel, local = false) => {
  const file = path.join(local ? ROOT : FROM, rel);
  if (!fs.existsSync(file)) throw new Error(`missing source: ${file}`);
  return file;
};
const H264 = ["-c:v", "libx264", "-crf", "24", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart"];

function makeMedia(item) {
  const clip = path.join(DOCS, "clips", `${item.slug}.mp4`);
  if (item.kind === "before-after") {
    // Raw take on the left, the edit on the right, on the same timeline, with the edit's sound.
    const graph = "[0:v]scale=540:960,setsar=1[a];[1:v]scale=540:960,setsar=1[b];[a][b]hstack=inputs=2,fps=30[v]";
    ffmpeg("-i", source(item.before), "-i", source(item.after), "-filter_complex", graph, "-map", "[v]", "-map", "1:a",
      ...H264, "-c:a", "aac", "-b:a", "128k", "-shortest", clip);
  } else {
    const span = item.to !== undefined ? ["-ss", String(item.from), "-t", String(item.to - item.from)] : [];
    const width = item.aspect && item.aspect !== "9/16" ? 1280 : 540;
    ffmpeg(...span, "-i", source(item.source, item.local), "-vf", `scale=${width}:-2,fps=30`, ...H264, "-an", clip);
  }
  const length = seconds(clip);
  ffmpeg("-ss", String(Math.min(length * 0.5, (item.cardFrom ?? 0) + 2)), "-i", clip, "-frames:v", "1", "-vf", "scale=540:-2", "-q:v", "3",
    path.join(DOCS, "posters", `${item.slug}.jpg`));
  // A README card loops a few seconds: the whole thing for a short component, the named span for a long one.
  const start = item.cardFrom ?? 0;
  const span = Math.min((item.cardTo ?? length) - start, length - start, 6);
  const cardWidth = item.kind === "before-after" ? 480 : item.aspect === "16/10" ? 560 : 270;
  ffmpeg("-ss", String(start), "-t", String(span), "-i", clip, "-vf", `fps=12,scale=${cardWidth}:-2:flags=lanczos`,
    "-c:v", "libwebp_anim", "-quality", "70", "-compression_level", "6", "-loop", "0", "-an", path.join(CARDS, `${item.slug}.webp`));
}

function writePage() {
  const data = catalog.groups.map((group) => ({
    name: group.name,
    note: group.note ?? "",
    items: group.items.map(({ source: _s, before: _b, after: _a, ...item }) => {
      const clip = path.join(DOCS, "clips", `${item.slug}.mp4`);
      return { ...item, secs: !item.pending && fs.existsSync(clip) ? Math.round(seconds(clip) * 10) / 10 : null };
    }),
  }));
  const template = fs.readFileSync(path.join(ROOT, "scripts", "gallery-template.html"), "utf8");
  fs.writeFileSync(path.join(DOCS, "index.html"), template.replace("/*DATA*/null", JSON.stringify(data)));
}

const escape = (text) => text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const GALLERY = "https://ctskool.github.io/claude-edit/";

function card(item, width) {
  const image = item.pending
    ? `<sub><i>${escape(item.key)}</i></sub>`
    : `<a href="${GALLERY}"><img src="media/cards/${item.slug}.webp" width="100%" alt="${escape(`${item.name}: ${item.does}`)}"></a>`;
  return [`<td width="${width}%" align="center" valign="top">`, image, `<br><b>${escape(item.name)}</b><br><sub>${escape(item.does)}</sub>`, `</td>`].join("\n");
}

// The README holds the components between its gallery markers; the flow section has its own hand-placed media.
function writeCards() {
  const file = path.join(ROOT, "README.md");
  let readme = fs.readFileSync(file, "utf8");
  const lines = [];
  for (const group of catalog.groups.filter((g) => g.name !== "The whole flow")) {
    lines.push(`### ${group.name}`, "");
    if (group.note) lines.push(group.note, "");
    lines.push("<table>");
    for (let i = 0; i < group.items.length; i += PER_ROW) {
      lines.push("<tr>", ...group.items.slice(i, i + PER_ROW).map((item) => card(item, Math.floor(100 / PER_ROW))), "</tr>");
    }
    lines.push("</table>", "");
  }
  const block = /(<!-- gallery:start -->\r?\n)[\s\S]*?(<!-- gallery:end -->)/;
  if (!block.test(readme)) throw new Error("README.md has lost its gallery markers");
  fs.writeFileSync(file, readme.replace(block, `$1\n${lines.join("\n")}\n$2`));
}

if (!pageOnly) {
  for (const folder of [path.join(DOCS, "clips"), path.join(DOCS, "posters"), CARDS]) {
    fs.rmSync(folder, { recursive: true, force: true });
    fs.mkdirSync(folder, { recursive: true });
  }
  const ready = items.filter((item) => !item.pending);
  ready.forEach((item, i) => {
    console.log(`${String(i + 1).padStart(2)}/${ready.length} ${item.slug}`);
    makeMedia(item);
  });
}
writePage();
if (fs.existsSync(path.join(ROOT, "README.md"))) writeCards();

const size = (folder) => fs.readdirSync(folder).reduce((sum, name) => sum + fs.statSync(path.join(folder, name)).size, 0) / 1048576;
console.log(`${items.length} items. Clips ${size(path.join(DOCS, "clips")).toFixed(1)} MB, cards ${size(CARDS).toFixed(1)} MB.`);
