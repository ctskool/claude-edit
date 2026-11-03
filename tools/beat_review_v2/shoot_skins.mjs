/* Screenshots the v2 page in each skin. Reads only (GET), never saves a note or starts a render.
 * Needs the v2 server running on 4750 (e.g. the "beat-review-v2-fixture" launch config).
 * Run: node tools/beat_review_v2/shoot_skins.mjs [skin ...]   (no names = base + every skins/*.css)
 * Writes reports/player-skins/<skin>.png at 1600x900. */
import puppeteer from 'puppeteer-core';
import { existsSync, mkdirSync, readdirSync, rmSync, mkdtempSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const out = join(here, '..', '..', 'reports', 'player-skins');
mkdirSync(out, { recursive: true });
const names = process.argv.slice(2).length ? process.argv.slice(2)
  : ['base', ...readdirSync(join(here, 'skins')).filter(f => f.endsWith('.css')).map(f => f.slice(0, -4)).sort()];
const chrome = [process.env.CHROME_PATH, process.env.HYPERFRAMES_BROWSER_PATH,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge']
  .find(p => p && existsSync(p));
if (!chrome) throw Error('No Chrome/Edge found; set CHROME_PATH to the browser executable.');
const profile = mkdtempSync(join(tmpdir(), 'skin-shots-'));
const browser = await puppeteer.launch({ executablePath: chrome, headless: true, userDataDir: profile,
  args: ['--no-first-run', '--autoplay-policy=no-user-gesture-required'] });
try {
  for (const name of names) {
    const page = await browser.newPage();
    await page.setViewport({ width: 1600, height: 900 });
    // Forget the saved position and theme, so every skin is shot at the same frame in its own colours.
    await page.evaluateOnNewDocument(() => { try { localStorage.clear(); } catch {} });
    await page.setRequestInterception(true);
    page.on('request', r => ['GET', 'HEAD'].includes(r.method()) ? r.continue() : r.abort());
    await page.goto('http://localhost:4750/' + (name === 'base' ? '' : '?skin=' + name), { waitUntil: 'networkidle2' });
    await page.waitForSelector('.beat');
    await new Promise(r => setTimeout(r, 800));
    // Same moment in every shot: beat 17, picture on screen, the selected row showing its actions.
    for (let i = 0; i < 16; i++) { await page.keyboard.press('ArrowDown'); await new Promise(r => setTimeout(r, 120)); }
    await new Promise(r => setTimeout(r, 1500));
    await page.screenshot({ path: join(out, name + '.png') });
    console.log('shot', name);
    await page.close();
  }
} finally {
  await browser.close();
  rmSync(profile, { recursive: true, force: true });
}
