import fs from "node:fs";
import { cue, W } from "./kit.mjs";
const re = /(?:at|cue)\("([^"]+)",\s*([a-zA-Z0-9_.]+)\)/g;
for (const f of fs.readdirSync("tools/sections")) {
  const s = fs.readFileSync("tools/sections/" + f, "utf8"); let m;
  while ((m = re.exec(s))) { const after = Number(m[2]); try { const t = cue(m[1], isNaN(after) ? 0 : after); if (!isNaN(after) && t - after > 6) console.log(f, "FAR", m[1], after, t.toFixed(2)); } catch { const k = isNaN(after) ? 0 : after; console.log(f, "MISSING", m[1], "| near:", W.filter((w) => w[1] > k - 1 && w[1] < k + 5).map((w) => w[0]).join(" ")); } }
}
