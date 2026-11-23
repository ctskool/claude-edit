// Blueprint engine: one paused GSAP timeline over one big drawing, registered for HyperFrames on
// window.__timelines[D.ID] once the fonts are in (BP_PRE measures the finished layout). Generic for any short; the
// short's own moves come in through two hooks the page defines before this script: BP_PRE(tl) (measure the finished
// layout before anything is hidden) and BP_KEYED(tl) (its keyed moves). D (from bp.py) carries the layout and times.
document.fonts.ready.then(() => {
const tl = gsap.timeline({paused: true});
const sheet = document.getElementById('sheet');
if (window.BP_PRE) BP_PRE(tl);

// ── camera: a view centre + zoom, so moves and the pull-back interpolate cleanly ──
const cam = {x: D.ORIG[0][0] + D.W / 2, y: D.ORIG[0][1] + D.H / 2, z: 1};
const applyCam = () => { sheet.style.transform = `translate(540px, 499px) scale(${cam.z}) translate(${-cam.x}px, ${-cam.y}px)`; };
const centre = i => ({x: D.ORIG[i][0] + D.W / 2, y: D.ORIG[i][1] + D.H / 2, z: 1});
tl.set(cam, {...centre(0), onUpdate: applyCam}, 0);
const OVZ = Math.min(1080 / D.SW, 998 / D.SH) * 0.98;
// the pen draws the camera's path into the next region while the camera follows (0.7 s, centred just before the cut)
const nib = document.getElementById('nib');
for (let i = 1; i < D.ARR.length; i++) {
  const t = D.ARR[i]; if (D.PULL_AT != null && t >= D.PULL_AT) break;
  const p = document.getElementById('pen' + (i - 1)), L = p.getTotalLength(), o = {f: 0};
  tl.set(p, {opacity: 1}, t - 0.42);
  tl.to(o, {f: 1, duration: 0.62, ease: 'power2.inOut', onUpdate: () => {
      p.style.strokeDashoffset = 1 - o.f; const q = p.getPointAtLength(o.f * L);
      nib.setAttribute('transform', `translate(${q.x},${q.y})`); }}, t - 0.42);
  tl.set(nib, {opacity: 1}, t - 0.42); tl.set(nib, {opacity: 0}, t + 0.22);
  tl.to(cam, {...centre(i), duration: 0.7, ease: 'power3.inOut', onUpdate: applyCam}, t - 0.4);
}
if (D.PULL_AT != null) {   // the ending: pull back to the whole drawing
  tl.to(cam, {x: D.SW / 2, y: D.SH / 2, z: OVZ, duration: 1.15, ease: 'power2.inOut', onUpdate: applyCam}, D.PULL_AT);
  tl.to('#hud', {opacity: 0, duration: 0.3}, D.PULL_AT);
}

// ── every region drafts itself in as the camera arrives; anything inside a data-t draws on that word ──
// never place a tween before 0: GSAP would shift the whole timeline later
const tOf = (el, dflt) => { const k = el.closest('[data-t]'); return k ? +k.dataset.t : dflt; };
document.querySelectorAll('.reg').forEach(reg => {
  const t0 = Math.max(0, +reg.dataset.arr - 0.12);
  let k = 0;
  reg.querySelectorAll('.cn').forEach(el => tl.fromTo(el, {opacity: 0}, {opacity: 1, duration: 0.4}, Math.max(0, t0 - 0.1)));
  reg.querySelectorAll('svg.ink [pathLength]').forEach(el => {
    if (el.closest('.bp-late') && !el.closest('[data-t]')) return;
    const tt = tOf(el, t0 + Math.min(1.0, (k++) * 0.03)), d = +(el.dataset.d || 0.42);
    if (!el.getAttribute('stroke-dasharray')) tl.fromTo(el, {strokeDasharray: '1 1', strokeDashoffset: 1}, {strokeDashoffset: 0, duration: d, ease: 'power2.out'}, tt);
    else tl.fromTo(el, {opacity: 0}, {opacity: 1, duration: 0.25}, tt);
    tl.fromTo(el, {opacity: 0}, {opacity: 1, duration: 0.04}, tt);
  });
  reg.querySelectorAll('svg.ink text, svg.ink circle:not([pathLength])').forEach(el => {
    tl.fromTo(el, {opacity: 0}, {opacity: 1, duration: 0.25}, tOf(el, t0 + 0.3) + 0.12);
  });
  let j = 0;
  reg.querySelectorAll(':scope > div, :scope > table').forEach(el => {
    if (el.classList.contains('bp-keyed')) return;          // the short's keyed code shows it
    const tt = tOf(el, t0 + (j++) * 0.08);
    if (el.classList.contains('plate')) {
      tl.fromTo(el, {clipPath: 'inset(0% 0% 100% 0%)'}, {clipPath: 'inset(0% 0% 0% 0%)', duration: 0.5, ease: 'power2.out'}, tt);
    } else if (el.classList.contains('h1')) {
      tl.fromTo(el, {clipPath: 'inset(0% 100% 0% 0%)'}, {clipPath: 'inset(0% 0% 0% 0%)', duration: 0.5, ease: 'power1.inOut'}, tt);
      if (!el.classList.contains('outline')) tl.fromTo(el, {color: 'rgba(234,243,255,0)', webkitTextStroke: '2px #eaf3ff'}, {color: '#eaf3ff', webkitTextStroke: '0px #eaf3ff', duration: 0.3}, tt + 0.42);
      el.querySelectorAll('b.red').forEach(b => tl.fromTo(b, {color: 'rgba(255,122,69,0)'}, {color: '#ff7a45', duration: 0.3}, tt + 0.42));
    } else {
      tl.fromTo(el, {opacity: 0, y: 14}, {opacity: 1, y: 0, duration: 0.35, ease: 'power2.out'}, tt);
    }
    el.querySelectorAll('[data-t]').forEach(s => tl.fromTo(s, {opacity: 0}, {opacity: 1, duration: 0.2}, +s.dataset.t));
  });
});
// typing: <span class="ty" data-text data-t0 data-t1>
document.querySelectorAll('.ty').forEach(el => { const txt = el.dataset.text, o = {n: 0};
  tl.to(o, {n: txt.length, duration: +el.dataset.t1 - +el.dataset.t0, ease: 'none', onUpdate: () => { el.textContent = txt.slice(0, Math.round(o.n)); }}, +el.dataset.t0); });
// developing plates: blueprint duotone -> colour, a bright scan line leads the wipe
document.querySelectorAll('img.dev').forEach(im => { const t0 = +im.dataset.t0, d = +im.dataset.t1 - t0, sc = im.nextElementSibling;
  tl.fromTo(im, {clipPath: 'inset(0% 100% 0% 0%)'}, {clipPath: 'inset(0% 0% 0% 0%)', duration: d, ease: 'power1.inOut'}, t0);
  tl.fromTo(sc, {x: 0, opacity: 1}, {x: im.parentElement.clientWidth, duration: d, ease: 'power1.inOut'}, t0); tl.to(sc, {opacity: 0, duration: 0.15}, t0 + d); });

if (window.BP_KEYED) BP_KEYED(tl);

// HUD sheet number per beat, captions per chunk, grain that flickers at 12 fps
D.BEATS.forEach((b, k) => { tl.set('#hn' + k, {opacity: 1}, b); if (k + 1 < D.BEATS.length) tl.set('#hn' + k, {opacity: 0}, D.BEATS[k + 1]); });
D.CAPS.forEach(([s, e, _], k) => { const nx = k + 1 < D.CAPS.length ? D.CAPS[k + 1][0] : D.END;
  tl.set('#c' + k, {opacity: 1}, s); tl.set('#c' + k, {opacity: 0}, Math.min(nx, e + 0.5)); });
let seed = 1119;                                 // seeded, so every render draws the same grain (HyperFrames determinism)
const rnd = () => { seed = (seed * 1664525 + 1013904223) % 4294967296; return seed / 4294967296; };
for (let t = 0; t < D.END; t += 1 / 12) tl.set('#grain', {backgroundPosition: `${Math.round(rnd() * 300)}px ${Math.round(rnd() * 300)}px`}, t);
tl.set({}, {}, D.END);
window.__timelines[D.ID] = tl;
});
