// Sky engine: one paused GSAP timeline, registered for HyperFrames on window.__timelines[D.ID] once the fonts are in
// (a short may measure its finished layout while it builds). The guide's moves are stepped (steps(n)) so he moves like
// a sprite; graphics use smooth eases. The short's own choreography is pasted in at the marker below; it can use:
//   pose(t, p)        show pose p of #g at t           pose2(t, p)   the same for the copy #g2
//   walk(t0, t1)      walk cycle                        moveX(t, d, x, n)   stepped move to x
//   hop(t, x, feet, peak) / hopTo(t, x)                 stepped jump arc     blink(t)
//   puffs(t, [[x, y], ...])  dust on a landing          scene(t, '#id')  hard cut to that scene
//   typeInto(id, text, t0, d)  types real text in       FL  the floor line his feet stand on, S(n) a stepped ease
document.fonts.ready.then(() => {
const tl = gsap.timeline({paused: true});
const FL = 950;
const S = (n) => 'steps(' + n + ')';
const SCN = Array.from(document.querySelectorAll('.scn')).map(e => '#' + e.id);
function pose(t, p) { tl.set('#g .pose', {display: 'none'}, t); tl.set('#p-' + p, {display: 'block'}, t); }
function pose2(t, p) { tl.set('#g2 .pose2', {display: 'none'}, t); tl.set('#q-' + p, {display: 'block'}, t); }
function walk(t0, t1) { let k = 0; for (let t = t0; t < t1 - 0.001; t += 0.1) pose(t, (k++ % 2) ? 'idle' : 'walk'); pose(t1, 'idle'); }
function moveX(t, d, x, n) { tl.to('#g', {x: x, duration: d, ease: S(n || Math.max(2, Math.round(d * 30 / 2)))}, t); }
function hop(t, x, feet, peak) {
  pose(t, 'jump');
  tl.to('#g', {y: peak, duration: 0.12, ease: S(4)}, t);
  tl.to('#g', {x: x, duration: 0.24, ease: S(6)}, t);
  tl.to('#g', {y: feet, duration: 0.12, ease: S(4)}, t + 0.12);
  pose(t + 0.24, 'idle');
}
function hopTo(t, x) { hop(t, x, FL, FL - 90); }
function puffs(t, pts) { pts.forEach((p, i) => { const id = '#d' + (i % 4);
  tl.set(id, {x: p[0], y: p[1], opacity: 1}, t); tl.to(id, {x: p[0] + (i % 2 ? 24 : -24), opacity: 0, duration: 0.3, ease: S(3)}, t); }); }
function blink(t) { pose(t, 'blink'); pose(t + 0.1, 'idle'); }
function scene(t, id) { SCN.forEach(s => tl.set(s, {visibility: s == id ? 'visible' : 'hidden', x: 0}, t)); }
function typeInto(id, text, t0, d) { const o = {n: 0};
  tl.fromTo(o, {n: 0}, {n: text.length, duration: d, ease: 'none', immediateRender: false,
    onUpdate: () => { document.getElementById(id).textContent = text.slice(0, Math.round(o.n)); }}, t0); }

/*__SHORT__*/

// captions: 1-3 word chips on the seam
D.CAPS.forEach((c, i) => { tl.set('#c' + i, {opacity: 1}, c.t0); tl.set('#c' + i, {opacity: 0}, c.t1); });
tl.set({}, {}, D.END);
// the edge clouds drift sideways in steps for the whole short
document.querySelectorAll('.cloud').forEach(d => { const s = +d.dataset.s, i = +d.dataset.i;
  tl.fromTo(d, {x: 0}, {x: (i % 2 ? -1 : 1) * 36 * s, duration: D.END, ease: 'steps(' + Math.round(36 * s / 3) + ')'}, 0); });
window.__timelines[D.ID] = tl;
});
