/* =====================================================================================================
   EDITORIAL KIT - kit.js  (v1.0, plain script, no modules; everything hangs off window.KIT)
   Distilled from the frame-matched replica of reference creator A "5 Claude skills", skill 1 (Chief of Staff).
   Each builder creates its DOM inside a parent you pass (normally a static `.clip.k-scene` section) and adds
   its MEASURED animation to the GSAP timeline you pass, at the time you pass.

   HyperFrames rules this file follows:
     - deterministic: no Date, no Math.random, no async; build everything before window.__timelines[...] = tl
     - only fromTo / set tweens on children of clips (never visibility/display/autoAlpha on a .clip)
     - DOM is built synchronously; clip sections (data-start/data-duration) stay static in index.html
   Load order in <head>:  assets/vendor/gsap.min.js  ->  kit.css (link)  ->  kit.js
   ===================================================================================================== */
(function (root) {
  "use strict";

  var KIT = (root.KIT = root.KIT || {});
  KIT.version = "1.0.0";

  /* ------------------------------------------------------------------ time helpers */
  var FPS = 30;
  KIT.FPS = FPS;
  KIT.F = 1 / FPS;
  /** Mid-frame time for frame k: a set/clip placed here is in place from frame k onward (no float misses). */
  KIT.at = function (k) { return (k - 0.5) / FPS; };
  /** Frame index that a time falls on (HyperFrames floors t*30). */
  KIT.frame = function (t) { return Math.floor(t * FPS + 1e-6); };
  /** data-start / data-duration for a clip that shows frames k0 .. k1-1 (use when authoring the static HTML). */
  KIT.clip = function (k0, k1) {
    return { start: +((k0 - 0.5) / FPS).toFixed(4), duration: +((k1 - k0) / FPS).toFixed(4) };
  };

  /* ------------------------------------------------------------------ tokens (mirror of kit.css :root) */
  KIT.C = {
    ivory: "#EEEEE7", card: "#FAFCFB", edge: "#DEDED6", dark: "#1B1D18", pink: "#F5EAE4",
    ink: "#151716", grey: "#82827A", stepGrey: "#ADAEA4", subGrey: "#7E807C",
    clay: "#CB6D55", clayChev: "#C9705D", claudeRed: "#CF5850", badge: "#D9614D",
    rail: "#D5D6CA", line: "#AFAFA6", dash: "#CECFC7",
    calLabel: "#111313", calLabelDim: "#ACACA8", hookSub: "#A6A69F"
  };
  KIT.CAP_TOP = { split: 904, full: 1423 };

  /* ------------------------------------------------------------------ motion presets (measured) */
  /** One pop is shared by every element that pops into place in this edit: scale 0.6 -> 1 on back.out(1.7)
   *  (peak ~1.04 at 58 % of the duration) + a short LINEAR opacity ramp. `lead` starts the fade earlier. */
  KIT.POP = {
    std:   { from: 0.6, dur: 0.26,  fade: 0.1,   lead: 0 },      // steps, NEW cell, Claude chip
    tile:  { from: 0.6, dur: 0.30,  fade: 0.12,  lead: 0 },      // skill-card icon tile
    node:  { from: 0.6, dur: 0.235, fade: 0.12,  lead: 0.008 },  // org-tree node
    agent: { from: 0.6, dur: 0.235, fade: 0.09,  lead: 0 },      // agent cards
    check: { from: 0.6, dur: 0.235, fade: 0.085, lead: 0 },      // row check discs
    goal:  { from: 0.6, dur: 0.303, fade: 0.125, lead: 0 }       // big goal card
  };
  /** Arrivals that rise into place (y offset -> 0) while fading in. fadeDelay is relative to the move start. */
  KIT.RISE = {
    card:  { y: 60, dur: 0.30, ease: "power3.out", fade: 0.12,  fadeEase: "power1.inOut", fadeDelay: 0.005 },  // skill card
    panel: { y: 36, dur: 0.25, ease: "power2.out", fade: 0.09,  fadeEase: "none", fadeDelay: 0.005, blur: 6 }, // calendar
    row:   { y: 30, dur: 0.20, ease: "power2.out", fade: 0.065, fadeEase: "none", fadeDelay: 0 }               // goal2, list rows
  };

  KIT.pop = function (tl, node, t, preset) {
    var p = typeof preset === "object" && preset ? preset : KIT.POP[preset || "std"];
    tl.fromTo(node, { scale: p.from }, { scale: 1, duration: p.dur, ease: "back.out(1.7)" }, t);
    tl.fromTo(node, { opacity: 0 }, { opacity: 1, duration: p.fade, ease: "none" }, t - (p.lead || 0));
    return t + p.dur;
  };

  KIT.rise = function (tl, node, t, preset) {
    var p = typeof preset === "object" && preset ? preset : KIT.RISE[preset || "row"];
    var from = { opacity: 0 }, to = { opacity: 1, duration: p.fade, ease: p.fadeEase };
    if (p.blur) { from.filter = "blur(" + p.blur + "px)"; to.filter = "blur(0px)"; }
    tl.fromTo(node, from, to, t + (p.fadeDelay || 0));
    tl.fromTo(node, { y: p.y }, { y: 0, duration: p.dur, ease: p.ease }, t);
    return t + p.dur;
  };

  /** Hard hide (placeholders when their card lands, etc.). */
  KIT.hideAt = function (tl, node, t) { tl.set(node, { opacity: 0 }, t); };
  KIT.showAt = function (tl, node, t) { tl.set(node, { opacity: 1 }, t); };

  /* ------------------------------------------------------------------ DOM helpers */
  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function mk(tag, cls, css, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (css) e.style.cssText = css;
    if (html != null) e.innerHTML = html;
    return e;
  }
  function put(parent, node) { parent.appendChild(node); return node; }
  function lt(x, y) { return "left:" + x + "px;top:" + y + "px;"; }
  function wh(w, h) { return (w != null ? "width:" + w + "px;" : "") + (h != null ? "height:" + h + "px;" : ""); }
  function pick(v, d) { return v == null ? d : v; }
  KIT.esc = esc;
  KIT.el = mk;
  /** Mono hyphens in the reference are en-dash-width glyphs: type U+2013 instead of "-". */
  KIT.dashes = function (s) { return String(s).replace(/-/g, "–"); };

  /* ------------------------------------------------------------------ icons (SVG sprite, injected once) */
  var LUC = 'fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"';
  var ICONS = {
    // --- measured / refit on the reference ---
    claude: ["0 0 24 24", 'fill="currentColor"', '<path d="m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z"/>'],
    users: ["0 0 150 150", 'fill="none" stroke="currentColor" stroke-width="5.2" stroke-linecap="round"',
      '<circle cx="64" cy="61.5" r="13.3"/><circle cx="96.5" cy="63" r="9.8"/><path d="M41 106 A22.8 22.8 0 0 1 86.6 106"/><path d="M95 83.5 A17 17 0 0 1 110.5 104.5"/>'],
    target: ["0 0 150 150", 'fill="none" stroke="currentColor" stroke-width="5.5"',
      '<circle cx="75" cy="75" r="31"/><circle cx="75" cy="75" r="19"/><circle cx="75" cy="75" r="5.5" fill="currentColor" stroke="none"/>'],
    chev: ["0 0 12 20", 'fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"', '<path d="M3 3l6 7-6 7"/>'],
    layers: ["0 0 24 24", LUC, '<polygon points="12 2.5 2.5 7.5 12 12.5 21.5 7.5 12 2.5"/><polyline points="2.5 16.5 12 21.5 21.5 16.5"/><polyline points="2.5 12 12 17 21.5 12"/>'],
    search: ["0 0 24 24", LUC, '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>'],
    pen: ["0 0 24 24", LUC, '<path d="M21.17 6.81a1 1 0 0 0-3.99-3.99L3.84 16.17a2 2 0 0 0-.5.83l-1.32 4.35a.5.5 0 0 0 .62.62l4.35-1.32a2 2 0 0 0 .83-.5z"/><path d="m15 5 4 4"/>'],
    layout: ["0 0 24 24", LUC, '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>'],
    code: ["0 0 24 24", LUC, '<path d="m16 18 6-6-6-6"/><path d="m8 6-6 6 6 6"/>'],
    check: ["0 0 24 24", LUC, '<path d="M20 6 9 17l-5-5"/>'],
    // --- extra lucide glyphs for new videos (standard lucide paths, NOT measured against a reference) ---
    mail: ["0 0 24 24", LUC, '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>'],
    calendar: ["0 0 24 24", LUC, '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>'],
    file: ["0 0 24 24", LUC, '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>'],
    globe: ["0 0 24 24", LUC, '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>'],
    database: ["0 0 24 24", LUC, '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/>'],
    zap: ["0 0 24 24", LUC, '<path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>'],
    terminal: ["0 0 24 24", LUC, '<polyline points="4 17 10 11 4 5"/><line x1="12" x2="20" y1="19" y2="19"/>'],
    folder: ["0 0 24 24", LUC, '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>'],
    message: ["0 0 24 24", LUC, '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'],
    clock: ["0 0 24 24", LUC, '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>'],
    chart: ["0 0 24 24", LUC, '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>'],
    link: ["0 0 24 24", LUC, '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>'],
    bot: ["0 0 24 24", LUC, '<path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/>'],
    user: ["0 0 24 24", LUC, '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'],
    play: ["0 0 24 24", LUC, '<polygon points="6 3 20 12 6 21 6 3"/>']
  };
  KIT.ICONS = Object.keys(ICONS);
  /** Register a custom symbol: KIT.addIcon("rocket", "0 0 24 24", '<path d="..."/>') (lucide stroke attrs by default). */
  KIT.addIcon = function (name, viewBox, inner, attrs) {
    ICONS[name] = [viewBox, attrs || LUC, inner];
    KIT.ICONS = Object.keys(ICONS);
    var sp = document.getElementById("k-sprite");
    if (sp) sp.querySelector("defs").insertAdjacentHTML("beforeend", symbol(name));
  };
  function symbol(n) { var d = ICONS[n]; return '<symbol id="k-i-' + n + '" viewBox="' + d[0] + '" ' + d[1] + ">" + d[2] + "</symbol>"; }
  function ensureSprite() {
    if (document.getElementById("k-sprite")) return;
    var s = '<svg id="k-sprite" width="0" height="0" style="position:absolute" aria-hidden="true"><defs>';
    for (var n in ICONS) if (Object.prototype.hasOwnProperty.call(ICONS, n)) s += symbol(n);
    document.body.insertAdjacentHTML("afterbegin", s + "</defs></svg>");
  }
  KIT.installIcons = ensureSprite;
  /** SVG markup referencing a sprite symbol. css sets size/position/colour (color drives currentColor). */
  KIT.icon = function (name, css, cls) {
    ensureSprite();
    if (!ICONS[name]) throw new Error("KIT.icon: unknown icon '" + name + "'. Known: " + KIT.ICONS.join(", "));
    return '<svg' + (cls ? ' class="' + cls + '"' : "") + ' style="' + (css || "") + '"><use href="#k-i-' + name + '"/></svg>';
  };
  // icon geometry inside discs/tiles: the custom 150-grid glyphs fill the box, 24-grid lucide glyphs are inset
  function tileIcon(name) {
    if (name === "users") return KIT.icon("users", "color:#fff");
    return KIT.icon(name, "left:32px;top:31px;width:84px;height:84px;color:#fff;stroke-width:1.55", "k-abs");  // measured on "layers"
  }

  /* ------------------------------------------------------------------ serif text (display-cut emulation) */
  /** Newsreader here is the TEXT optical size; the reference is the display cut (narrower). Words are placed one
   *  by one: {text, left, scaleX} at a shared size/top/letter-spacing. Without measured lefts, pass {title} and
   *  the whole line is centred in `width` with one scaleX (default 0.95, the mean of the measured words). */
  KIT.serif = function (parent, o) {
    var size = o.size, ls = pick(o.ls, -0.01), top = o.top, color = o.color ? "color:" + o.color + ";" : "";
    var out = [];
    if (o.words) {
      o.words.forEach(function (w) {
        out.push(put(parent, mk("div", "k-t k-serif",
          "left:" + w.left + "px;top:" + top + "px;font-size:" + size + "px;letter-spacing:" + ls + "em;" + color +
          "transform:scaleX(" + pick(w.scaleX, 1) + ");", esc(w.text))));
      });
    } else {
      var css = "top:" + top + "px;font-size:" + size + "px;letter-spacing:" + ls + "em;" + color + "transform:scaleX(" + pick(o.scaleX, 0.95) + ");";
      if (o.align === "left") css += "left:" + o.left + "px;";
      else css += "left:" + pick(o.left, 0) + "px;width:" + o.width + "px;text-align:center;transform-origin:50% 50%;";
      if (o.italic) css += "font-style:italic;";
      out.push(put(parent, mk("div", "k-t k-serif", css, o.html != null ? o.html : esc(o.title))));
    }
    return out;
  };

  /* ------------------------------------------------------------------ typing (command bar / terminal) */
  /** Characters appear one by one (hard set, no fade) at t + step*i. Measured cadences: 0.05 s/char (20 cps,
   *  "chief-of-staff") and 0.10 s/char ("anatomy"). Hyphens become en-dashes unless o.enDash === false.
   *  Returns the time the last character lands. */
  KIT.typeText = function (tl, node, text, t, step, o) {
    o = o || {};
    var s = o.enDash === false ? String(text) : KIT.dashes(text);
    var chars = Array.from(s);
    node.innerHTML = chars.map(function (c) { return "<span>" + esc(c) + "</span>"; }).join("");
    var spans = node.querySelectorAll("span");
    for (var i = 0; i < spans.length; i++) tl.set(spans[i], { opacity: 1 }, t + step * i - 0.012);
    return t + step * Math.max(0, chars.length - 1);
  };
  KIT.terminalType = KIT.typeText;

  /* ------------------------------------------------------------------ stepper (5-dot progress) */
  /** Rail + numbered circles. Steps < active are "done" (clay outline + clay rail segment), the active one is
   *  clay with a 10 px halo and pops at t. Measured: circles 70 px / border 4, pitch 160, centre y 792.5,
   *  rail 6 px at y 790, first circle left 188 (5 steps). */
  KIT.stepper = function (tl, parent, o, t) {
    o = o || {};
    var count = pick(o.count, 5), active = pick(o.active, 1), pitch = pick(o.pitch, 160);
    var x0 = pick(o.x0, Math.round(543 - pitch * (count - 1) / 2 - 35)), top = pick(o.top, 758);
    var r = { steps: [] };
    r.rail = put(parent, mk("div", "k-abs k-rail", lt(x0 + 34, top + 32) + wh(pitch * (count - 1))));
    if (active > 1) r.railOn = put(parent, mk("div", "k-abs k-rail-on", lt(x0 + 34, top + 32) + wh(pitch * (active - 1))));
    for (var i = 1; i <= count; i++) {
      if (i === active) continue;
      r.steps[i - 1] = put(parent, mk("div", "k-abs k-step" + (i < active ? " k-done" : ""), lt(x0 + pitch * (i - 1), top), "<b>" + i + "</b>"));
    }
    r.active = r.steps[active - 1] = put(parent, mk("div", "k-abs k-step k-on", lt(x0 + pitch * (active - 1), top), "<b>" + active + "</b>"));
    if (t != null) KIT.pop(tl, r.active, t, "std");
    return r;
  };

  /* ------------------------------------------------------------------ skill card (label + stepper + card) */
  /** The "SKILL n OF N" beat (split layout). t = card arrival.
   *  Measured (S1): card opacity 0->1 over t+.005..+.125 (power1.inOut), y +60 -> 0 in 0.30 s power3.out;
   *  tile pops at t+0.099 (0.30 s); active step pops at t+0.23; typing starts t+0.3533 at 0.05 s/char.
   *  o: {n, total, label, title, titleScaleX(.93), icon("users"), command, typeAt, typeStep(.05), stepAt} */
  KIT.skillCard = function (tl, scene, o, t) {
    o = o || {};
    var n = pick(o.n, 1), total = pick(o.total, 5), r = {};
    r.label = put(scene, mk("div", "k-t k-sk-label", "", esc(o.label || "SKILL " + n + " OF " + total)));
    r.stepper = KIT.stepper(tl, scene, { count: total, active: n }, pick(o.stepAt, t + 0.23));
    var card = (r.card = put(scene, mk("div", "k-abs k-sk-card")));
    r.title = put(card, mk("div", "k-t k-serif k-sk-title", "transform:scaleX(" + pick(o.titleScaleX, 0.93) + ")", esc(o.title || "")));
    var bar = (r.bar = put(card, mk("div", "k-abs k-sk-bar", "", KIT.icon("chev", "color:" + KIT.C.clayChev, "k-abs k-sk-chev"))));
    r.cmd = put(bar, mk("div", "k-t k-cmd"));
    r.tile = put(card, mk("div", "k-abs k-sk-tile", "", tileIcon(o.icon || "users")));
    KIT.rise(tl, card, t, "card");
    KIT.pop(tl, r.tile, t + 0.099, "tile");
    r.typedAt = KIT.typeText(tl, r.cmd, o.command || "", pick(o.typeAt, t + 0.3533), pick(o.typeStep, 0.05));
    return r;
  };

  /* ------------------------------------------------------------------ HUD (deep-dive header) */
  /** Static header shown through a skill's deep dive (its own clip, z 3): dark pill "1/5  slug" + N progress
   *  dashes right-aligned to x 990. Pill width = 109.4 + 14.4 px per slug char (311 for "chief-of-staff").
   *  Dashes 1..index are clay (only index 1 was measured; "upto" fill is the assumed progression). */
  KIT.hud = function (tl, host, o) {
    o = o || {};
    var idx = pick(o.index, 1), total = pick(o.total, 5), slug = KIT.dashes(o.slug || "");
    var counter = idx + "/" + total, n = Array.from(slug).length;
    var r = { dashes: [] };
    r.pill = put(host, mk("div", "k-abs k-pill", o.pillW ? wh(o.pillW) : wh(Math.round(109.4 + 14.4 * n))));
    r.pill.innerHTML = '<div class="k-t" style="left:19px;color:' + KIT.C.clay + ';">' + esc(counter) + "</div>" +
      '<div class="k-t" style="left:' + Math.round(19 + 14.4 * (counter.length + 2)) + 'px;color:#fff;">' + esc(slug) + "</div>";
    for (var i = 0; i < total; i++) {
      var on = o.fill === "only" ? i === idx - 1 : i < idx;
      r.dashes.push(put(host, mk("div", "k-abs k-dash" + (on ? " k-on" : ""), "left:" + (990 - 50 - 60 * (total - 1 - i)) + "px")));
    }
    return r;
  };
  /** Turn dash i (0-based) clay at t (hard set). Unmeasured progression helper. */
  KIT.hudFill = function (tl, hud, i, t) { tl.set(hud.dashes[i], { backgroundColor: KIT.C.clay }, t); };

  /* ------------------------------------------------------------------ calendar card */
  /** Two-row week calendar (900x255 at 90,300). Arrival: opacity + blur 6->0 over 0.09 s linear (from t+.005),
   *  y +36 -> 0 in 0.25 s power2.out. The NEW cell pops at o.newAt (std pop).
   *  o: {x, y, days[7], rows:[{label, tone:"l"|"n", dim:bool, color?}], newCell:{row, col, text} | null, newAt} */
  KIT.calendarCard = function (tl, parent, o, t) {
    o = o || {};
    var r = { cells: [] };
    var card = (r.card = put(parent, mk("div", "k-abs k-cal", o.x != null ? lt(o.x, o.y) : "")));
    var rows = o.rows || [{ label: "LAST WEEK", tone: "l" }, { label: "THIS WEEK", tone: "n", dim: true }];
    var days = o.days || ["M", "T", "W", "T", "F", "S", "S"];
    var nc = o.newCell === undefined ? { row: 0, col: 3, text: "NEW" } : o.newCell;
    rows.forEach(function (row, ri) {
      put(card, mk("div", "k-t k-cal-l" + (row.dim ? " k-dim" : ""), lt(36, 70 + 96 * ri) + (row.color ? "color:" + row.color + ";" : ""), esc(row.label)));
    });
    var cells = put(card, mk("div"));
    days.forEach(function (d, i) {
      rows.forEach(function (row, ri) {
        var isNew = nc && nc.row === ri && nc.col === i;
        var c = put(cells, mk("div", "k-abs k-cell " + (isNew ? "k-new" : "k-" + row.tone), lt(237 + 92 * i, 40 + 96 * ri), esc(isNew ? nc.text || "NEW" : d)));
        (r.cells[ri] = r.cells[ri] || [])[i] = c;
        if (isNew) r.newCell = c;
      });
    });
    KIT.rise(tl, card, t, "panel");
    if (r.newCell && o.newAt != null) KIT.pop(tl, r.newCell, o.newAt, "std");
    return r;
  };

  /* ------------------------------------------------------------------ dashed placeholder ("outline box") */
  /** Dashed outline that holds a card's slot until the card lands (then KIT.hideAt). Stroke #CECFC7 4 px,
   *  dash 8.5 / gap 4. inset:false centres the stroke on the box edge (big goal slot, r 38);
   *  inset:true keeps it inside the box (agent slots, r 23). */
  KIT.placeholder = function (parent, o) {
    var x = o.x, y = o.y, w = o.w, h = o.h, rr = pick(o.r, 38);
    var sx = o.inset ? x : x - 2, sy = o.inset ? y : y - 2, sw = o.inset ? w : w + 4, shh = o.inset ? h : h + 4;
    var rw = o.inset ? w - 4 : w, rh = o.inset ? h - 4 : h;
    parent.insertAdjacentHTML("beforeend",
      '<svg class="k-abs" style="' + lt(sx, sy) + wh(sw, shh) + 'overflow:visible"><rect x="2" y="2" width="' + rw + '" height="' + rh +
      '" rx="' + rr + '" fill="none" stroke="' + KIT.C.dash + '" stroke-width="4" stroke-dasharray="8.5 4"/></svg>');
    return parent.lastElementChild;
  };
  KIT.outlineBox = KIT.placeholder;

  /* ------------------------------------------------------------------ goal card (big hero) */
  /** Clay-bordered hero card (900x470 at 90,640, r 40, 4 px clay border + 12 px halo). Target disc 150 px,
   *  eyebrow 27 px clay, serif title 115.5 px. Pops at t (0.303 s, fade 0.125 s).
   *  o: {x, y, icon("target"), eyebrow, words:[{text,left,scaleX}] | title, size(115.5), titleTop(291)} */
  KIT.goalCard = function (tl, parent, o, t) {
    o = o || {};
    var r = {};
    var card = (r.card = put(parent, mk("div", "k-abs k-goal", o.x != null ? lt(o.x, o.y) : "")));
    var ic = !o.icon || o.icon === "target" ? KIT.icon("target", "left:0;top:0;width:150px;height:150px;color:#fff", "k-abs")
      : KIT.icon(o.icon, "left:39px;top:39px;width:72px;height:72px;color:#fff;stroke-width:2.2", "k-abs");  // lucide on disc: unmeasured
    r.disc = put(card, mk("div", "k-abs k-target", "", ic));
    r.eyebrow = put(card, mk("div", "k-t k-eyebrow",
      "left:0;width:892px;top:229px;text-align:center;font-size:27px;letter-spacing:0.096em;padding-left:0.096em;", esc(o.eyebrow || "ONE BIG GOAL")));
    r.title = KIT.serif(card, { words: o.words, title: o.title, size: pick(o.size, 115.5), ls: -0.009, top: pick(o.titleTop, 291), width: 892, scaleX: pick(o.titleScaleX, 0.996) });
    KIT.pop(tl, card, t, "goal");
    return r;
  };

  /** Vertical clay connector that draws downward (scaleY 0->1 from the top, 0.22 s power1.out).
   *  Measured: 6x88 at 537,1112 (goal card -> Claude chip). */
  KIT.connector = function (tl, parent, o, t) {
    o = o || {};
    var c = put(parent, mk("div", "k-abs k-conn", (o.x != null ? lt(o.x, o.y) : "") + wh(o.w, o.h)));
    tl.fromTo(c, { scaleY: 0 }, { scaleY: 1, duration: pick(o.dur, 0.22), ease: "power1.out" }, t);
    return c;
  };

  /** The red "Claude" chip (spark + serif wordmark, 284x84 at 398,1200). Std pop at t. */
  KIT.claudeChip = function (tl, parent, o, t) {
    o = o || {};
    var c = put(parent, mk("div", "k-abs k-cchip", o.x != null ? lt(o.x, o.y) : ""));
    c.innerHTML = KIT.icon("claude", "left:10px;top:14px;width:55px;height:55px;color:#fff", "k-abs") +
      '<div class="k-t" style="left:72px;top:15px;font-family:\'Newsreader\',serif;font-weight:500;font-size:62px;color:#141414;letter-spacing:-0.005em;transform:scaleX(1.1);transform-origin:0 50%;">' +
      esc(o.text || "Claude") + "</div>";
    KIT.pop(tl, c, t, "std");
    return c;
  };

  /* ------------------------------------------------------------------ org tree */
  /** Dark node (420x110 at 330,300, r 29) with a clay icon disc and a white 35 px label. Node pop at t
   *  (scale 0.235 s from t, opacity 0.12 s from t-0.008). */
  KIT.treeNode = function (tl, parent, o, t) {
    o = o || {};
    var n = put(parent, mk("div", "k-abs k-node", (o.x != null ? lt(o.x, o.y) : "") + wh(o.w)));
    var ic = !o.icon || o.icon === "users" ? KIT.icon("users", "left:0.5px;top:0.5px;width:69px;height:69px;color:#fff", "k-abs")
      : KIT.icon(o.icon, "left:17px;top:17px;width:36px;height:36px;color:#fff;stroke-width:2.2", "k-abs");   // lucide: unmeasured
    n.innerHTML = '<div class="k-abs k-ic">' + ic + "</div>" +
      '<div class="k-t" style="left:113px;top:37px;font-weight:700;font-size:35px;color:#fff;letter-spacing:-0.01em;">' + esc(o.label || "") + "</div>";
    if (t != null) KIT.pop(tl, n, t, "node");
    return n;
  };

  /** Grey tree lines (4 px #AFAFA6): trunk from the node, a bar, one drop per card. Fade-in 0.07 s linear at t.
   *  o: {cx(540), nodeBottom(410), barY(478), dropTo(562), centers:[card centre x...]} */
  KIT.treeLines = function (tl, parent, o, t) {
    o = o || {};
    var cx = pick(o.cx, 540), nb = pick(o.nodeBottom, 410), by = pick(o.barY, 478), dt = pick(o.dropTo, 562), cs = o.centers;
    var g = put(parent, mk("div"));
    put(g, mk("div", "k-abs k-ln", lt(cx - 2, nb - 1) + wh(4, by + 3 - (nb - 1))));
    put(g, mk("div", "k-abs k-ln", lt(cs[0] - 2, by) + wh(cs[cs.length - 1] + 2 - (cs[0] - 2), 4)));
    var drops = put(g, mk("div"));
    cs.forEach(function (c) { put(drops, mk("div", "k-abs k-ln", lt(c - 2, by) + wh(4, dt - by))); });
    if (t != null) tl.fromTo(g, { opacity: 0 }, { opacity: 1, duration: 0.07, ease: "none" }, t);
    return g;
  };

  /** One agent card (164x250, r 25): pink disc 86 + clay lucide icon 40 (stroke 1.8), name 28.2 px, "AGENT"
   *  19 px tracked .175em, static progress (102x8 track, fill = pct). Pops at t (0.235 s, fade 0.09 s). */
  KIT.agentCard = function (tl, parent, a, x, y, t) {
    var c = put(parent, mk("div", "k-abs k-agent", "left:" + x + "px;" + (y != null ? "top:" + y + "px;" : "")));
    c.innerHTML = '<div class="k-abs k-ic">' + KIT.icon(a.icon || "bot", "color:" + KIT.C.clay) + "</div>" +
      '<div class="k-t k-nm">' + esc(a.name) + '</div><div class="k-t k-ag">' + esc(a.sub || "AGENT") + "</div>" +
      '<div class="k-abs k-tr"><i style="width:' + Math.round(pick(a.pct, 0.5) * 102) + 'px"></i></div>';
    if (t != null) KIT.pop(tl, c, t, "agent");
    return c;
  };

  /** Whole org-tree beat (split): dashed slots, lines, node, agent cards in that z-order.
   *  times: {node, lines, agents, stagger(0.2)}; each slot hides 0.09 s after its card's pop starts.
   *  Measured: node 5.523, lines 5.84, agents 6.064 + 0.2 n (=> node+0.317, node+0.541 + 0.2 n). */
  KIT.agentTree = function (tl, parent, o, times) {
    o = o || {};
    times = times || {};
    var agents = o.agents || [], x0 = pick(o.x0, 90), pitch = pick(o.pitch, 184), y = pick(o.y, 560);
    var tn = times.node, tLines = pick(times.lines, tn + 0.317), tA = pick(times.agents, tn + 0.541), st = pick(times.stagger, 0.2);
    var r = { slots: [], cards: [] };
    agents.forEach(function (a, i) { r.slots.push(KIT.placeholder(parent, { x: x0 + pitch * i, y: y, w: 164, h: 250, r: 23, inset: true })); });
    r.lines = KIT.treeLines(tl, parent, { centers: agents.map(function (a, i) { return x0 + pitch * i + 82; }), dropTo: y + 2 }, tLines);
    r.node = KIT.treeNode(tl, parent, o.node || {}, tn);
    agents.forEach(function (a, i) {
      var t = tA + st * i;
      r.cards.push(KIT.agentCard(tl, parent, a, x0 + pitch * i, y === 560 ? null : y, t));
      KIT.hideAt(tl, r.slots[i], t + 0.09);
    });
    return r;
  };

  /* ------------------------------------------------------------------ goal progress card */
  /** Compact goal card (900x260 at 90,300): eyebrow "THE GOAL" 23 px, serif 73.4 px, 680x18 bar that fills,
   *  96 px check disc. Arrival: opacity 0.065 s + y +30 -> 0 0.2 s power2.out at t.
   *  Bar 0 -> pct over 1.15 s power2.out at t+0.145; check scale 0.5 -> 1 (0.15 s power1.out) + fade 0.125 s at t+1.29.
   *  o: {eyebrow, words | title, pct(1), barAt, barDur, checkAt} */
  KIT.goalProgress = function (tl, parent, o, t) {
    o = o || {};
    var r = {};
    var card = (r.card = put(parent, mk("div", "k-abs k-goal2", o.x != null ? lt(o.x, o.y) : "")));
    r.eyebrow = put(card, mk("div", "k-t k-eyebrow", "left:44px;top:42px;font-size:23px;letter-spacing:0.165em;", esc(o.eyebrow || "THE GOAL")));
    r.title = KIT.serif(card, { words: o.words, title: o.title, align: "left", left: 44, size: 73.4, top: 83, scaleX: pick(o.titleScaleX, 0.95) });
    var w = Math.round(680 * pick(o.pct, 1));
    var bar = put(card, mk("div", "k-abs k-gbar"));
    r.fill = put(bar, mk("i", "", "width:" + w + "px"));
    r.check = put(card, mk("div", "k-abs k-gchk", "", KIT.icon("check", "left:24px;top:24px;width:48px;height:48px;color:#fff;stroke-width:3", "k-abs")));
    KIT.rise(tl, card, t, "row");
    tl.fromTo(r.fill, { width: 0 }, { width: w, duration: pick(o.barDur, 1.15), ease: "power2.out" }, pick(o.barAt, t + 0.145));
    var ct = pick(o.checkAt, t + 1.29);
    tl.fromTo(r.check, { scale: 0.5 }, { scale: 1, duration: 0.15, ease: "power1.out" }, ct);
    tl.fromTo(r.check, { opacity: 0 }, { opacity: 1, duration: 0.125, ease: "none" }, ct);
    return r;
  };

  /** Grey tracked section label, e.g. "RUNNING IN THE BACKGROUND" (700 26 px .124em at 92,628). Static. */
  KIT.sectionLabel = function (parent, text, o) {
    o = o || {};
    return put(parent, mk("div", "k-t k-label", lt(pick(o.x, 92), pick(o.y, 628)), esc(text)));
  };

  /* ------------------------------------------------------------------ check rows (list of agents running) */
  /** Rows 900x112 at y0 + 134 n (r 28): pink disc 76 + icon 37, name 33 px, sub 23 px, 440x12 bar, 56 px check.
   *  Measured from t (= first row): row n rises at t + 0.0375 n (fade 0.065 s, y 30 0.2 s power2.out);
   *  bar n fills at t + 0.052 + 0.06 n over 0.5 + 0.09 n s (power2.out); check n pops at t + 0.61 + 0.1485 n
   *  (exact ref: +0.610 / 0.752 / 0.904 / 1.052 / 1.204; pass o.checkAt to override, null to skip a check).
   *  o: {rows:[{name, icon, sub("agent"), pct(1)}], y0(680), pitch(134), checkAt:[abs times]} */
  KIT.checkRows = function (tl, parent, o, t) {
    o = o || {};
    var rows = o.rows || [], y0 = pick(o.y0, 680), pitch = pick(o.pitch, 134), r = { rows: [], fills: [], checks: [] };
    rows.forEach(function (row, i) {
      var w = Math.round(440 * pick(row.pct, 1));
      var el = put(parent, mk("div", "k-abs k-row", "top:" + (y0 + pitch * i) + "px"));
      el.innerHTML = '<div class="k-abs k-ic">' + KIT.icon(row.icon || "bot", "color:" + KIT.C.clay) + "</div>" +
        '<div class="k-t k-nm">' + esc(row.name) + '</div><div class="k-t k-ag">' + esc(row.sub || "agent") + "</div>" +
        '<div class="k-abs k-rbar"><i style="width:' + w + 'px"></i></div>' +
        '<div class="k-abs k-rchk">' + KIT.icon("check", "left:14px;top:14px;width:28px;height:28px;color:#fff;stroke-width:3", "k-abs") + "</div>";
      var fill = el.querySelector(".k-rbar i"), chk = el.querySelector(".k-rchk");
      var tr = t + 0.0375 * i;
      KIT.rise(tl, el, tr, "row");
      tl.fromTo(fill, { width: 0 }, { width: w, duration: 0.5 + 0.09 * i, ease: "power2.out" }, t + 0.052 + 0.06 * i);
      var ct = o.checkAt ? o.checkAt[i] : t + 0.61 + 0.1485 * i;
      if (ct != null) KIT.pop(tl, chk, ct, "check"); else chk.style.opacity = "0";
      r.rows.push(el); r.fills.push(fill); r.checks.push(chk);
    });
    return r;
  };
  KIT.checkRow = KIT.checkRows;

  /* ------------------------------------------------------------------ dark hook title card */
  /** Dark panel hook (static layout; only a 3-frame tail was in the measured window, so no motion is claimed):
   *  Claude badge 164x48 at 458,222; serif title 101 px white at top 285; subtitle Inter 600 25 px .158em grey;
   *  five clay 3D cubes 151x150 (front 118, depth 33) on a frozen float wave (tops 577/572/568/570/574).
   *  o: {badge("Claude"), words | title, subtitle, cubes:["1".."5"], cubeX[], cubeY[]} */
  KIT.titleCard = function (tl, scene, o) {
    o = o || {};
    var r = { cubes: [] };
    put(scene, mk("div", "k-abs", "left:300px;top:430px;width:480px;height:440px;border-radius:50%;" +
      "background:radial-gradient(circle, rgba(255,255,255,0.045) 0%, rgba(255,255,255,0.03) 55%, rgba(255,255,255,0) 72%);"));
    if (o.badge !== false) {
      r.badge = put(scene, mk("div", "k-abs k-badge", "", KIT.icon("claude", "left:9px;top:10px;width:29px;height:29px;color:#fff", "k-abs") +
        '<div class="k-t" style="left:44px;top:12.5px;font-family:\'Newsreader\',serif;font-weight:500;font-size:36px;color:#141414;letter-spacing:-0.01em;">' +
        esc(o.badge || "Claude") + "</div>"));
    }
    r.title = KIT.serif(scene, { words: o.words, title: o.title, size: pick(o.size, 101), ls: -0.014, top: pick(o.titleTop, 285), color: "#fff", width: 1080, scaleX: pick(o.titleScaleX, 0.97) });
    if (o.subtitle) {
      r.subtitle = put(scene, mk("div", "k-t", "left:0;width:1080px;top:395px;text-align:center;font-weight:600;font-size:25px;letter-spacing:0.158em;padding-left:0.158em;color:" + KIT.C.hookSub + ";", esc(o.subtitle)));
    }
    put(scene, mk("div", "k-abs", "left:250px;top:750px;width:32px;height:32px;border-radius:5px;background:#CB6D55;opacity:0.55;filter:blur(1.5px);"));
    var labels = o.cubes || ["1", "2", "3", "4", "5"], cx = o.cubeX || [92, 278, 464, 650, 836], cy = o.cubeY || [577, 572, 568, 570, 574];
    labels.forEach(function (lab, i) {
      r.cubes.push(put(scene, mk("div", "k-abs k-cube", lt(cx[i], cy[i]), '<div class="k-abs k-tp"></div><div class="k-abs k-sd"></div><div class="k-abs k-f">' + esc(lab) + "</div>")));
    });
    return r;
  };

  /* ------------------------------------------------------------------ captions (mono chips, HARD swap) */
  /** Group transcript words into chips the way the editor did: up to 3 words, a sentence end closes a chip early,
   *  punctuation stripped, UPPERCASE. A chip is on from floor(start*30) - lead until the next chip's frame; if the
   *  gap to the next word exceeds o.gap (0.6 s) it goes off at floor((end + o.hold)*30). words: [{text,start,end}] */
  KIT.chunkWords = function (words, o) {
    o = o || {};
    var max = pick(o.max, 3), lead = pick(o.lead, 0), gap = pick(o.gap, 0.6), hold = pick(o.hold, 0.15), off = pick(o.offset, 0);
    var groups = [], cur = [];
    words.forEach(function (w, i) {
      cur.push(w);
      if (cur.length >= max || /[.!?]["')\]]*$/.test(w.text) || i === words.length - 1) { groups.push(cur); cur = []; }
    });
    return groups.map(function (g, i) {
      var last = g[g.length - 1], next = groups[i + 1];
      var k0 = Math.max(0, KIT.frame(g[0].start + off) - lead);
      var k1 = next && next[0].start - last.end <= gap ? Math.max(0, KIT.frame(next[0].start + off) - lead) : KIT.frame(last.end + off + hold);
      var text = g.map(function (w) { return w.text; }).join(" ").replace(/[.,!?;:"]+(?=\s|$)/g, "").toUpperCase();
      return { text: text, k0: k0, k1: k1 };
    });
  };

  /** Hard-swap caption chips inside a `.k-caps` rail. chunks: [{text, k0, k1}] (frames, shown k0..k1-1)
   *  or [{text, start, end}] (seconds, floored to frames). Chip: JetBrains Mono 700 55 px, tracking 2.25 px,
   *  111 px tall, r 14, padding 33 px, rgba(15,17,17,.94), white. No animation, no karaoke. */
  KIT.captions = function (tl, rail, chunks) {
    return chunks.map(function (c) {
      var k0 = c.k0 != null ? c.k0 : KIT.frame(c.start), k1 = c.k1 != null ? c.k1 : KIT.frame(c.end);
      var node = put(rail, mk("div", "k-cap"));
      node.textContent = String(c.text).toUpperCase();
      tl.set(node, { opacity: 1 }, k0 <= 0 ? 0 : KIT.at(k0));
      tl.set(node, { opacity: 0 }, KIT.at(k1));
      return node;
    });
  };
  KIT.captionChip = function (tl, rail, text, k0, k1) { return KIT.captions(tl, rail, [{ text: text, k0: k0, k1: k1 }])[0]; };

  /** Caption rail position per layout: top 904 (split, chip centred on the seam) or 1423 (full takeover).
   *  cuts: [[frame, "full"|"split"], ...]; the rail starts at `start` ("split") at t = 0. */
  KIT.captionRail = function (tl, rail, cuts, start) {
    tl.set(rail, { top: KIT.CAP_TOP[start || "split"] }, 0);
    (cuts || []).forEach(function (c) { tl.set(rail, { top: KIT.CAP_TOP[c[1]] }, KIT.at(c[0])); });
  };
  /** A full takeover from frame k0 to k1 (exclusive): moves the caption rail down and back. The takeover scene
   *  itself is a static `<section class="clip k-scene k-full">` with data-start/duration = KIT.clip(k0, k1). */
  KIT.takeover = function (tl, rail, k0, k1) {
    tl.set(rail, { top: KIT.CAP_TOP.full }, KIT.at(k0));
    if (k1 != null) tl.set(rail, { top: KIT.CAP_TOP.split }, KIT.at(k1));
  };
})(window);
