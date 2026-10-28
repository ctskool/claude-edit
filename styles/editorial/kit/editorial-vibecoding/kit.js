/* =====================================================================================================
   EDITORIAL KIT "vibecoding" - kit.js  (v1.0, plain script, no modules; everything hangs off window.KIT,
   also exposed as window.KITVC so it can coexist with the editorial-chiefofstaff kit).
   Distilled from the frame-matched replica of reference creator B "4 plugin" (IT), seconds 0-14.5
   (work/replica/editorial-vibecoding, mean SSIM 0.9737 / colour error 2.08 against the reference).

   Every builder creates its DOM inside a parent you pass and adds its MEASURED animation to the GSAP timeline
   you pass, at the time you pass. Defaults reproduce the reference exactly; times are anchored on the event
   the measurement was keyed to (see COMPONENTS.md, "anchor" of each component).

   HyperFrames rules this file follows:
     - deterministic: no Date, no Math.random, no async; build everything before window.__timelines[...] = tl
     - only set / to / fromTo tweens on children of clips; never visibility/display/autoAlpha on a .clip
       (typed characters use display on their own <span>s, which are never clips)
     - the DOM is built synchronously at load
   Load order in <head>:  assets/vendor/gsap.min.js  ->  kit.css (link)  ->  kit.js
   ===================================================================================================== */
(function (root) {
  "use strict";

  var KIT = {};
  root.KIT = KIT;
  root.KITVC = KIT;
  KIT.version = "1.0.0";
  KIT.id = "editorial-vibecoding";

  /* ------------------------------------------------------------------ time helpers */
  var FPS = 30;
  var F = function (n) { return n / FPS; };
  KIT.FPS = FPS;
  /** Seconds of output frame n (n / 30). */
  KIT.F = F;
  /** Time for a HARD set that must be in place from output frame n on (the replica's F(n) - 0.004 convention). */
  KIT.at = function (n) { return n / FPS - 0.004; };
  /** Output frame a time falls on (HyperFrames floors t*30). */
  KIT.frame = function (t) { return Math.floor(t * FPS + 1e-6); };
  /** data-start / data-duration for a clip that shows frames k0 .. k1-1. */
  KIT.clip = function (k0, k1) {
    return { start: +((k0 - 0.5) / FPS).toFixed(4), duration: +((k1 - k0) / FPS).toFixed(4) };
  };
  /** "source": per-frame tables keep the 25 fps holds of reference B's export (output frames n = 3 mod 6 repeat).
   *  "smooth": linear tables drop those held rows (cleaner motion for new videos). Set BEFORE building. */
  KIT.cadence = "source";

  /** Anchor: a component measured with reference frame `ref` at its key event is placed at time t (snapped to
   *  the nearest output frame A). f(refFrame) -> time, s(refSeconds) -> time, n(refFrame) -> output frame.
   *  When t falls on `ref` itself every time is bit-identical to the replica. */
  function anchor(t, ref) {
    var A = Math.round(t * FPS);
    return {
      A: A, ref: ref, t: t,
      n: function (f) { return A === ref ? f : A + (f - ref); },
      f: function (f) { return A === ref ? F(f) : F(A + (f - ref)); },
      s: function (sec) { return A === ref ? sec : sec + (A - ref) / FPS; }
    };
  }
  KIT.anchor = anchor;

  /* drop 25 fps holds (row n = 3 mod 6 equal to row n-1) when KIT.cadence === "smooth" */
  function cad(rows, R) {
    if (KIT.cadence !== "smooth") return rows;
    return rows.filter(function (r, k) {
      if (k === 0 || k === rows.length - 1) return true;
      var p = rows[k - 1];
      if (r[0] - p[0] !== 1) return true;
      var n = R.n(r[0]);
      if (((n % 6) + 6) % 6 !== 3) return true;
      for (var j = 1; j < r.length; j++) if (r[j] !== p[j]) return true;
      return false;
    });
  }

  function assign(a) {
    for (var i = 1; i < arguments.length; i++) { var b = arguments[i]; if (b) for (var k in b) a[k] = b[k]; }
    return a;
  }
  /** Per-frame LINEAR table: an immediateRender set of row 0 at time 0 (unless init === false), then one linear
   *  `to` per segment. rows: [[refFrame, ...values]], map(row) -> props. */
  function lin(tl, target, rows, R, map, init) {
    rows = cad(rows, R);
    if (init !== false) tl.set(target, assign(map(rows[0]), init || {}, { immediateRender: true }), 0);
    for (var k = 1; k < rows.length; k++)
      tl.to(target, assign(map(rows[k]), { duration: F(rows[k][0] - rows[k - 1][0]), ease: "none" }), R.f(rows[k - 1][0]));
  }
  /** Per-frame STEP table: hard sets (from frame n on). init: immediateRender set of row 0 at time 0. */
  function steps(tl, target, rows, R, map, init) {
    var k0 = 0;
    if (init !== false && init != null) { tl.set(target, assign(map(rows[0]), init, { immediateRender: true }), 0); k0 = 1; }
    for (var k = k0; k < rows.length; k++) tl.set(target, map(rows[k]), R.f(rows[k][0]) - 0.004);
  }
  KIT.lin = lin;
  KIT.steps = steps;

  /* ------------------------------------------------------------------ DOM helpers */
  var SVGNS = "http://www.w3.org/2000/svg";
  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function mk(tag, cls, css, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (css) e.setAttribute("style", css);
    if (html != null) e.innerHTML = html;
    return e;
  }
  function put(parent, node) { parent.appendChild(node); return node; }
  function svgEl(tag, attrs, parent) {
    var e = document.createElementNS(SVGNS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function pick(v, d) { return v == null ? d : v; }
  KIT.esc = esc;
  KIT.el = mk;
  KIT.svgEl = svgEl;

  /* ------------------------------------------------------------------ colours (mirror of kit.css :root) */
  KIT.C = {
    bg: "#eeece8", card: "#ffffff", ink: "#1e1d1b", inkTitle: "#151513", inkSub: "#56524d", label: "#6e6b66",
    desc: "#55524e", clay: "#d05a33", clayTitle: "#c9532d", claySpark: "#c45f3b", clayTile: "#da6a43",
    clayLine: "#bd5f3e", hot: "#ec987f", numeral: "#e1bfaf", red: "#ad1f2e", green: "#2f9a68",
    supabase: "#3ecf8e", check: "#3d996a", capBg: "#1c1d1c", capText: "#fafcfc"
  };

  /* ------------------------------------------------------------------ glyphs */
  var CLAUDE = "m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246-1.4147-2.1675-1.1414-1.9428-.1397.0789-.6739 7.2526-.3157.3703-.7286.2794-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z";
  var BOLT = "M11.9 1.036c-.015-.986-1.26-1.41-1.874-.637L.764 12.05C-.33 13.427.65 15.455 2.409 15.455h9.579l.113 7.51c.014.985 1.259 1.408 1.873.636l9.262-11.653c1.093-1.375.113-3.403-1.645-3.403h-9.642z";
  var ANTHROPIC = "M17.3041 3.541h-3.6718l6.696 16.918H24Zm-10.6082 0L0 20.459h3.7442l1.3693-3.5527h7.0052l1.3693 3.5528h3.7442L10.5363 3.5409Zm-.3712 10.2232 2.2914-5.9456 2.2914 5.9456Z";
  /** 24-unit glyph paths (fill). claude = spark, bolt = Supabase mark, anthropic = A mark. */
  KIT.PATHS = { claude: CLAUDE, bolt: BOLT, anthropic: ANTHROPIC };
  /** Tool-row line icons (24 grid, stroke 2.2, hand-drawn approximations of the reference icons). */
  KIT.TOOL_ICONS = {
    terminal: '<path d="M5 8l4 4-4 4"/><path d="M12 17h7"/>',
    layers: '<path d="M12 4l8 4.5-8 4.5-8-4.5z"/><path d="M4 13l8 4.5 8-4.5"/>',
    braces: '<path d="M9 4c-2 0-3 1-3 3v2c0 1.5-1 3-2.5 3C5 12 6 13.5 6 15v2c0 2 1 3 3 3"/><path d="M15 4c2 0 3 1 3 3v2c0 1.5 1 3 2.5 3-1.5 0-2.5 1.5-2.5 3v2c0 2-1 3-3 3"/>',
    shield: '<path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z"/><path d="M9.5 12l2 2 3.5-3.5"/>',
    // extra (standard lucide, unmeasured)
    database: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.66 3.58 3 8 3s8-1.34 8-3V5"/><path d="M4 12c0 1.66 3.58 3 8 3s8-1.34 8-3"/>',
    key: '<circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6"/><path d="m15.5 7.5 3 3L22 7l-3-3"/>',
    search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    file: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/>',
    globe: '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    zap: '<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>'
  };
  /** Install the shared <defs> (Claude spark referenced by <use href="#kv-claude">) once, at the end of the
   *  composition root. Builders that need it call this themselves. */
  KIT.defs = function (rootEl) {
    if (document.getElementById("kv-claude")) return;
    rootEl = rootEl || document.querySelector(".kv-root") || document.querySelector("[data-composition-id]") || document.body;
    var s = mk("div", "", "", '<svg width="0" height="0" style="position:absolute"><defs><path id="kv-claude" d="' + CLAUDE + '"/></defs></svg>');
    rootEl.appendChild(s.firstChild);
  };
  function useClaude() { return '<use href="#kv-claude"/>'; }

  /** Typing helper: one <span style="display:none"> per character inside `node`, each switched to
   *  display:inline at t + i*step. Returns the time of the last character. (alias KIT.terminalType) */
  KIT.typeChars = function (tl, node, text, t, step) {
    String(text).split("").forEach(function (ch, i) {
      var s = put(node, mk("span", "", "display:none", ch === " " ? "&nbsp;" : esc(ch)));
      tl.set(s, { display: "inline" }, t + i * step);
    });
    return t + (String(text).length - 1) * step;
  };
  KIT.terminalType = KIT.typeChars;

  /** Hard cut: element gone from time t on (cards swap this way in the reference). */
  KIT.cut = function (tl, node, t) { tl.set(node, { opacity: 0 }, t); };

  /* ================================================================== 0. DASHED OUTLINE (the reference's core motif) */
  /** Measured dash presets: every "not yet there" state in this reference is a dashed outline whose dash PHASE was
   *  matched per edge (phase mattered more than 1 px of geometry). */
  KIT.DASH = {
    socket:   { stroke: "#ad5d4a", width: 2.9, dash: "5.72 2.96", offset: -2.5, r: 20 },    // phase-1 socket outline
    wait:     { stroke: "#ab5b47", width: 2.7, dash: "6.2 2.5", offset: -2.85, r: 20 },     // phase-2 waiting socket
    box:      { stroke: "#d6937f", width: 2.95, dash: "5.82 2.95", offset: 4.3, r: 13.3, fill: "rgba(255,255,255,0.5)" }, // "?" box
    skeleton: { stroke: "#c9c6c1", width: 2.4, dash: "6.2 2.45", offset: 0, r: 38, fill: "#f3f2ef" },  // skeleton icon tile
    db:       { stroke: "#bf8f88", width: 2.5, dash: "5.6 3.27", offset: 0, r: 0 },         // database placeholder
    line:     { stroke: "#cbc8c3", width: 3, dash: "10.7 9.46", offset: 0, r: 0 },          // grey dashed connector line
    check:    { stroke: "#cfccc7", width: 1.6, dash: "4 3.2", offset: 0, r: 999 }           // empty check circle
  };
  /** A dashed rounded rectangle (or circle with r >= min(w,h)/2) at x,y (w x h), stroke centred inside the box.
   *  o: {x, y, w, h, preset("skeleton"), stroke, width, dash, offset, r, fill, opacity} -> the <svg> */
  KIT.dashedBox = function (parent, o) {
    var p = assign({}, KIT.DASH[o.preset || "skeleton"], o), sw = p.width;
    var svg = svgEl("svg", { class: "kv-abs", width: p.w, height: p.h, style: "left:" + p.x + "px;top:" + p.y + "px;overflow:visible" + (p.opacity != null ? ";opacity:" + p.opacity : "") }, parent);
    if (p.h <= 2 * sw) svgEl("line", { x1: 0, y1: p.h / 2, x2: p.w, y2: p.h / 2, stroke: p.stroke, "stroke-width": sw, "stroke-dasharray": p.dash, "stroke-dashoffset": p.offset || 0 }, svg);
    else svgEl("rect", { x: sw / 2, y: sw / 2, width: p.w - sw, height: p.h - sw, rx: Math.min(p.r, (Math.min(p.w, p.h) - sw) / 2), fill: p.fill || "none", stroke: p.stroke, "stroke-width": sw, "stroke-dasharray": p.dash, "stroke-dashoffset": p.offset || 0 }, svg);
    return svg;
  };
  KIT.outlineBox = KIT.dashedBox;

  /* ================================================================== 1. BACKGROUND GRID */
  /** Ivory panel + 60 px grid that drifts at a constant (+1.166, +7.5) px/s for the whole video.
   *  Inserted as the FIRST child of the composition root (under the face cam and every graphic).
   *  o: {dur (seconds, required for drift), vx, vy, x0, y0} */
  KIT.grid = function (tl, rootEl, o) {
    o = o || {};
    var bg = mk("div", "kv-bg"), g = mk("div", "kv-grid");
    bg.setAttribute("data-layout-allow-overflow", "true");
    g.setAttribute("data-layout-allow-overflow", "true");
    bg.appendChild(g);
    rootEl.insertBefore(bg, rootEl.firstChild);
    var dur = o.dur, x0 = pick(o.x0, -0.115), y0 = pick(o.y0, -0.105), vx = pick(o.vx, 1.166), vy = pick(o.vy, 7.5);
    if (dur) {
      var to = { x: x0 + vx * dur, y: y0 + vy * dur, ease: "none", duration: dur };
      // long videos: wrap the (periodic) offset so the grid never runs out of tiles
      if (Math.abs(vx * dur) > 50 || Math.abs(vy * dur) > 100)
        to.modifiers = { x: gsap.utils.unitize(function (v) { return v % 60; }), y: gsap.utils.unitize(function (v) { return v % 60; }) };
      tl.fromTo(g, { x: x0, y: y0 }, to, 0);
    }
    return { bg: bg, grid: g };
  };

  /* ================================================================== 2. SERIF TITLE + SUBLINE */
  var TITLE_IN = [[25, 0, 0.85, 9, 2.5], [26, 0.22, 0.857, 8.4, 2], [27, 0.22, 0.857, 8.4, 2], [28, 0.5, 0.92, 5, 0.6], [29, 0.8, 0.963, 2.2, 0],
    [30, 0.95, 0.985, 0.8, 0], [31, 1, 1.0, -0.5, 0], [33, 1, 1.008, -1.5, 0], [36, 1, 1.003, -1, 0], [40, 1, 1, 0, 0]];
  var SUB_IN = [[57, 0, 10], [58, 0.12, 9], [59, 0.51, 5.5], [60, 0.7, 3.2], [61, 0.9, 1.6], [62, 0.97, 0.5], [66, 1, 0]];
  /* "*Vibe* coding" -> spans; *word* is the italic clay word */
  function titleWordsHTML(text) {
    var parts = String(text).split(/(\*[^*]+\*)/).filter(function (p) { return p.length; });
    return '<div class="kv-title-line">' + parts.map(function (p) {
      var it = /^\*.*\*$/.test(p);
      var s = it ? p.slice(1, -1) : p;
      return s.split(/(\s+)/).map(function (w) {
        if (!w.length) return "";
        if (/^\s+$/.test(w)) return " ";
        return '<span class="kv-tw' + (it ? " kv-it" : "") + '">' + esc(w) + "</span>";
      }).join("");
    }).join("") + "</div>";
  }
  /** The opening headline: serif title (one italic clay word) + grey subline, blur-in entrance, shared slow
   *  push-in, hard cut out. t = entrance anchor (reference frame 25 = 0.833 s; title is fully in by +0.5 s).
   *  o: {text:"*Vibe* coding" | svg (traced <path>s for a 1080x130 box), sub:"con Claude Code" | subSvg,
   *      top(190), subTop(314), titleY(top offset of the font line, 2), subY(0), subAt(t+1.067), pushAt(t+0.817),
   *      pushRate(0.0078/s), out(t+3.5, hard cut; null = stays), originX(546.5), originY(281)} */
  KIT.serifTitle = function (tl, host, o, t) {
    o = o || {};
    var R = anchor(t, 25);
    var top = pick(o.top, 190), subTop = pick(o.subTop, 314), ox = pick(o.originX, 546.5), oy = pick(o.originY, 281);
    var wrap = put(host, mk("div", "kv-center", "top:" + top + "px;height:106px"));
    var title = put(wrap, mk("div", "kv-title"));
    if (o.svg) title.innerHTML = '<svg width="1080" height="130" viewBox="0 0 1080 130" style="position:absolute;left:0;top:0;overflow:visible">' + o.svg + "</svg>";
    else { title.innerHTML = titleWordsHTML(o.text || "*Vibe* coding"); title.firstChild.style.top = pick(o.titleY, -12) + "px"; }
    var subWrap = null, sub = null;
    if (o.subSvg || o.sub) {
      subWrap = put(host, mk("div", "kv-center", "top:" + subTop + "px;height:30px"));
      sub = put(subWrap, mk("div", "kv-sub"));
      if (o.subSvg) sub.innerHTML = '<svg width="1080" height="40" viewBox="0 0 1080 40" style="position:absolute;left:0;top:0.8px;overflow:visible">' + o.subSvg + "</svg>";
      else { sub.innerHTML = '<div class="kv-sub-line">' + esc(o.sub) + "</div>"; sub.firstChild.style.top = pick(o.subY, 0) + "px"; }
    }
    lin(tl, title, TITLE_IN, R, function (r) { return { opacity: r[1], scale: r[2], y: r[3], filter: "blur(" + r[4] + "px)" }; }, { transformOrigin: "50.6% 94%" });
    var pushAt = pick(o.pushAt, R.s(1.65)), out = o.out === null ? null : pick(o.out, R.s(4.333)), rate = pick(o.pushRate, 0.0078);
    var pushEnd = pick(o.pushUntil, out != null ? out : pushAt + 2.683);
    tl.fromTo(wrap, { scale: 1, transformOrigin: ox + "px " + (oy - top) + "px" }, { scale: 1 + rate * (pushEnd - pushAt), ease: "none", duration: pushEnd - pushAt }, pushAt);
    if (sub) {
      var RS = anchor(pick(o.subAt, R.f(57)), 57);
      lin(tl, sub, SUB_IN, RS, function (r) { return { opacity: r[1], y: r[2] }; }, {});
      tl.fromTo(subWrap, { scale: 1, transformOrigin: ox + "px " + (oy - subTop) + "px" }, { scale: 1 + rate * (pushEnd - pushAt), ease: "none", duration: pushEnd - pushAt }, pushAt);
    }
    if (out != null) tl.set(subWrap ? [wrap, subWrap] : wrap, { opacity: 0 }, out);
    return { wrap: wrap, title: title, subWrap: subWrap, sub: sub };
  };
  KIT.titleBuild = KIT.serifTitle;

  /* ================================================================== 3. POWER-STRIP HUD ("CLAUDE CODE 0/4") */
  var SOCK_X0 = 262, SOCK_PITCH = 120;
  /** Build the strip (no animation). Local units = phase-2 rest (scale 1, bottom of the panel).
   *  o: {label("CLAUDE CODE"), sockets(4), total(sockets), count(0), x(auto centred), y(783)}
   *  Returns S = {el, pop, body, pill, spark, lbl, count, nums[], dots{gray,red,green}, socks, sockets[{sock,outl,qbox,cx}], value} */
  KIT.powerStrip = function (host, o) {
    o = o || {};
    KIT.defs();
    var N = pick(o.sockets, 4), total = pick(o.total, N), value = pick(o.count, 0), label = pick(o.label, "CLAUDE CODE");
    var w = 696 + SOCK_PITCH * (N - 4), x = pick(o.x, 540 - w / 2), y = pick(o.y, 783);
    var S = { N: N, total: total, value: value, sockets: [], plugged: [], w: w, x: x, y: y };
    S.el = put(host, mk("div", "kv-strip", "left:" + x + "px;top:" + y + "px;width:" + w + "px"));
    S.pop = put(S.el, mk("div", "kv-strip-pop"));
    S.body = put(S.pop, mk("div", "kv-strip-body"));
    S.pill = put(S.pop, mk("div", "kv-pill", label === "CLAUDE CODE" ? "" : "width:" + Math.round(56.4 + 11.24 * label.length) + "px"));
    S.spark = svgEl("svg", { class: "kv-spark", viewBox: "0 0 24 24" }, S.pop);
    S.spark.innerHTML = useClaude();
    S.lbl = put(S.pop, mk("div", "kv-lbl", "", esc(label)));
    S.count = put(S.pop, mk("div", "kv-count"));
    S.nums = [];
    for (var k = 0; k <= total; k++) S.nums.push(put(S.count, mk("span", k === 0 ? "n" : "n1", k === value ? "" : "display:none", String(k))));
    S.count.appendChild(document.createTextNode("/" + total));
    S.dots = { gray: put(S.pop, mk("div", "kv-dot gray")), red: put(S.pop, mk("div", "kv-dot red")), green: put(S.pop, mk("div", "kv-dot green")) };
    S.socks = put(S.pop, mk("div", "kv-socks"));
    S.socks.setAttribute("data-layout-allow-overflow", "true");
    for (var i = 0; i < N; i++) {
      var cx = SOCK_X0 + SOCK_PITCH * i;
      var s = put(S.socks, mk("div", "kv-sock", "left:" + (cx - 47) + "px"));
      put(s, mk("div", "kv-slot a")); put(s, mk("div", "kv-slot b")); put(s, mk("div", "kv-gnd"));
      // phase-1 dashed outline (dash phase matched per edge: 5.72/2.96, offset -2.5)
      var ol = svgEl("svg", { class: "kv-outl", width: 110, height: 102, style: "left:" + (cx - 56.6) + "px" }, S.socks);
      svgEl("rect", { x: 2.2, y: 2.85, width: 105.2, height: 95.9, rx: 20, fill: "none", stroke: "#ad5d4a", "stroke-width": 2.9, "stroke-dasharray": "5.72 2.96", "stroke-dashoffset": -2.5, style: "filter: blur(0.3px) drop-shadow(0 0 1.5px rgba(255,255,255,0.9))" }, ol);
      // "?" placeholder box floating above the socket: body + separate unfilled handle bracket
      var b = put(S.socks, mk("div", "kv-qbox", "left:" + (cx - 2.5 - 36.7 + i * 0.45 - 0.15) + "px"));
      var bs = svgEl("svg", { width: 74, height: 107, style: "position:absolute;left:0;top:0;overflow:visible" }, b);
      svgEl("rect", { x: 2.05, y: 17.25, width: 69.3, height: 85.8, rx: 13.3, fill: "rgba(255,255,255,0.5)", stroke: "#d6937f", "stroke-width": 2.95, "stroke-dasharray": "5.82 2.95", "stroke-dashoffset": 4.3 }, bs);
      svgEl("path", { d: "M 24.25 17.25 L 24.25 6.15 Q 24.25 2.15 28.25 2.15 L 51.55 2.15 Q 55.55 2.15 55.55 6.15 L 55.55 17.25", fill: "none", stroke: "#d6937f", "stroke-width": 2.95, "stroke-dasharray": "5.75 2.9", "stroke-dashoffset": 5.2 }, bs);
      put(b, mk("div", "kv-q", "", esc(o.qMark || "?")));
      S.sockets.push({ sock: s, outl: ol, qbox: b, cx: cx });
    }
    return S;
  };
  KIT.hud = KIT.powerStrip;

  var STRIP_POP = [[0, 0.906], [1, 0.94], [2, 0.966], [3, 0.967], [4, 0.986], [5, 0.998], [6, 1.006], [7, 1.0099], [9, 1.008], [12, 1.0]];
  /** Phase 1: the strip is big and high (centre y 668, scale 1.355 growing 0.0099/s) and pops in
   *  (0.906 -> 1.0099 at +7 f -> 1 at +12 f). t = first frame (0 in the reference).
   *  o: {scale(1.355), push(0.0099), lift(-172), dockAt(t+4.367; the push runs until the dock)} */
  KIT.stripIntro = function (tl, S, o, t) {
    o = o || {}; t = t || 0;
    var R = anchor(t, 0);
    var S0 = pick(o.scale, 1.355), SK = pick(o.push, 0.0099), lift = pick(o.lift, -172), dock = pick(o.dockAt, R.f(131));
    var T = dock - t;
    tl.fromTo(S.el, { y: lift, scaleX: S0, scaleY: S0 }, { scaleX: S0 + SK * T, scaleY: S0 + SK * T, ease: "none", duration: T }, t);
    var P = cad(STRIP_POP, R);
    tl.fromTo(S.pop, { scale: P[0][1] }, { scale: P[1][1], duration: F(P[1][0] - P[0][0]), ease: "none" }, R.f(P[0][0]));
    for (var k = 2; k < P.length; k++) tl.to(S.pop, { scale: P[k][1], duration: F(P[k][0] - P[k - 1][0]), ease: "none" }, R.f(P[k - 1][0]));
    S.phase1 = { S0: S0, SK: SK, t: t, lift: lift };
  };

  /** Red status-dot blinks (on "Non"): frame pairs [[on, off], ...]; the last 2 frames of each blink sit at 0.75. */
  KIT.stripBlink = function (tl, S, pairs) {
    pairs.forEach(function (p) {
      tl.set(S.dots.red, { opacity: 1 }, F(p[0]) - 0.004);
      tl.set(S.dots.red, { opacity: 0.75 }, F(p[1] - 2) - 0.004);
      tl.set(S.dots.red, { opacity: 0 }, F(p[1]) - 0.004);
    });
  };

  var NO_DOT = [[71, 0.65], [72, 1], [74, 0.9], [76, 0], [77, 0.3], [78, 1], [80, 0.93], [82, 0]];
  var NO_SHAKE = [[70, 0], [71, -4.2], [72, -11.1], [73, 4.9], [74, 11], [75, 11], [76, -5], [77, -5.9], [78, 4.2], [79, 1.3], [80, -0.5], [82, 0]];
  /** "No" gesture on the second "non": the count shakes its head (frame px -11 .. +11 over 12 frames) while the
   *  red dot double-blinks. t = start (reference frame 70). o: {scale (strip scale at that moment, 1.38)} */
  KIT.stripNo = function (tl, S, t, o) {
    var R = anchor(t, 70), sc = (o && o.scale) || 1.38;
    NO_DOT.forEach(function (r) { tl.set(S.dots.red, { opacity: r[1] }, R.f(r[0]) - 0.004); });
    NO_SHAKE.forEach(function (r) { tl.set(S.count, { x: r[1] / sc }, R.f(r[0]) - 0.004); });
  };

  /** Clay highlight pill behind the label (on the word "Claude"): 0.09 s linear fade in at tOn; at tOff it reads
   *  0.45 for one frame, then gone. */
  KIT.stripPill = function (tl, S, tOn, tOff) {
    tl.fromTo(S.pill, { opacity: 0 }, { opacity: 1, duration: 0.09, ease: "none" }, tOn);
    if (tOff != null) {
      var n = Math.round(tOff * FPS);
      tl.set(S.pill, { opacity: 0.45 }, F(n) - 0.004);
      tl.set(S.pill, { opacity: 0 }, F(n + 1) - 0.004);
    }
  };
  KIT.highlightPill = KIT.stripPill;

  var QPOP = [
    [[84, 0.7, 0], [85, 0.9, 0.6], [86, 0.98, 1], [87, 0.98, 1], [88, 1.03, 1], [89, 1.04, 1], [90, 1.04, 1], [91, 1.03, 1], [92, 1.01, 1], [93, 1.01, 1], [94, 0.995, 1], [95, 1, 1]],
    [[85, 0.7, 0], [86, 0.8, 0.35], [87, 0.8, 0.35], [88, 0.93, 0.9], [89, 1.01, 1], [90, 1.035, 1], [91, 1.045, 1], [92, 1.035, 1], [93, 1.035, 1], [94, 1.02, 1], [95, 1.01, 1], [96, 1, 1]],
    [[88, 0.7, 0], [89, 0.84, 0.4], [90, 0.955, 0.9], [91, 1.015, 1], [92, 1.035, 1], [93, 1.035, 1], [94, 1.045, 1], [95, 1.035, 1], [96, 1.03, 1], [97, 1.015, 1], [98, 1.005, 1], [99, 1.005, 1], [100, 1, 1]],
    [[89, 0.6, 0], [90, 0.6, 0.1], [91, 0.88, 0.6], [92, 0.965, 1], [93, 0.965, 1], [94, 1.025, 1], [95, 1.045, 1], [96, 1.045, 1], [97, 1.035, 1], [98, 1.015, 1], [99, 1.015, 1], [100, 1, 1]]
  ];
  /* box tops (frame px, f99..f131): idle float up 13 px, then the dip wave on "plugin" (+52 px, 1 content frame per box) */
  var QTOPS = [
    [392, 390, 390, 388, 388, 387, 387, 386, 385, 384, 384, 382, 382, 381, 380, 380, 379, 379, 379, 379, 380, 386, 401, 432, 432, 407, 391, 384, 382, 384, 384, 387, 390],
    [392, 391, 390, 390, 389, 388, 388, 387, 386, 385, 384, 384, 384, 383, 382, 381, 380, 380, 380, 379, 379, 380, 385, 401, 401, 432, 407, 391, 384, 382, 382, 384, 388],
    [392, 391, 391, 390, 390, 389, 389, 388, 387, 386, 385, 384, 384, 384, 383, 382, 380, 380, 380, 380, 379, 379, 380, 385, 385, 401, 432, 406, 391, 384, 384, 383, 384],
    [392, 392, 392, 391, 391, 390, 390, 389, 389, 388, 387, 386, 386, 384, 383, 383, 381, 380, 380, 380, 379, 379, 379, 380, 380, 385, 401, 432, 407, 391, 391, 384, 384]
  ];
  /** Dashed "?" placeholder boxes over the sockets ("these 4 plugins"): staggered pop (0.6-0.7 -> 1.045 -> 1,
   *  origin 50% 10%), idle float + one dip wave, 3-frame fade. t = first box (reference frame 84 = 2.8 s).
   *  o: {floatAt(t+0.5), outAt(t+1.533; fade .85/.12/0 over 3 frames), scale(strip scale 1.396), tops (override)} */
  KIT.questionBoxes = function (tl, S, o, t) {
    o = o || {};
    var R = anchor(t, 84), RF = anchor(pick(o.floatAt, R.f(99)), 99), RO = anchor(pick(o.outAt, R.f(130)), 130);
    var QS = pick(o.scale, 1.396), QREST = 392;
    S.sockets.forEach(function (s, i) {
      var b = s.qbox, j = Math.min(i, 3), sh = 2 * (i - j);
      var QP = QPOP[j].map(function (r) { return [r[0] + sh, r[1], r[2]]; });
      tl.set(b, { opacity: 0, scale: QP[0][1], transformOrigin: "50% 10%", immediateRender: true }, 0);
      for (var k = 1; k < QP.length; k++) tl.set(b, { scale: QP[k][1], opacity: QP[k][2] }, R.f(QP[k][0]) - 0.004);
      var tops = (o.tops && o.tops[i]) || QTOPS[j];
      tl.set(b, { y: 0, immediateRender: true }, 0);
      for (k = 1; k < tops.length; k++) tl.to(b, { y: (tops[k] + 0.6 - QREST) / QS, duration: F(1), ease: "none" }, RF.f(99 + k - 1));
      tl.to(b, { opacity: 0.85, duration: F(1), ease: "none" }, RO.f(130));
      tl.to(b, { opacity: 0.12, duration: F(1), ease: "none" }, RO.f(131));
      tl.to(b, { opacity: 0, duration: F(1), ease: "none" }, RO.f(132));
    });
  };

  var OUT_ON = [[[108, 0.3], [109, 1]], [[110, 0.3], [112, 0.6], [113, 1]], [[113, 0.25], [114, 0.6], [115, 1]], [[115, 0.1], [116, 0.35], [118, 1]]];
  var OUT_SIZE = [[109, 1.06], [112, 1.056], [113, 1.053], [114, 1.04], [115, 1.027], [116, 1.013], [118, 1.006], [119, 1.0], [123, 1.0],
    [124, 1.013], [125, 1.026], [126, 1.04], [127, 1.047], [128, 1.06], [131, 1.06]];
  /** Dashed clay outlines lock onto each socket in turn (pale 1-3 frames, then solid), shrink 1.06 -> 1 together and
   *  swell back to 1.06 just before the dock. t = first outline (reference frame 108 = 3.6 s). o: {outAt(t+0.8)} */
  KIT.socketOutlines = function (tl, S, o, t) {
    o = o || {};
    var R = anchor(t, 108), n = Math.round(pick(o.outAt, R.f(132)) * FPS);
    var OS = cad(OUT_SIZE, R);
    S.sockets.forEach(function (s, i) {
      var ol = s.outl, j = Math.min(i, 3), sh = 2 * (i - j);
      OUT_ON[j].forEach(function (r) { tl.set(ol, { opacity: r[1] }, R.f(r[0] + sh) - 0.004); });
      tl.set(ol, { scale: OS[0][1] }, 0);
      for (var k = 1; k < OS.length; k++) tl.to(ol, { scale: OS[k][1], duration: F(OS[k][0] - OS[k - 1][0]), ease: "none" }, R.f(OS[k - 1][0]));
      tl.set(ol, { opacity: 0.3 }, F(n) - 0.004);
      tl.set(ol, { opacity: 0 }, F(n + 1) - 0.004);
    });
  };

  var DOCK = [[131, 0], [132, 0.014], [133, 0.057], [134, 0.129], [135, 0.129], [136, 0.254], [137, 0.44], [138, 0.656], [139, 0.81],
    [140, 0.91], [141, 0.91], [142, 0.968], [143, 0.989], [144, 1]];
  /** Dock: the strip flies from phase 1 (big, high) to its rest at the bottom of the panel in 13 frames
   *  (progress .014 .057 .129 .254 .44 .656 .81 .91 .968 .989 1). t = start (reference frame 131 = 4.367 s).
   *  o: {countNudge(true): the count's measured +0.9/-0.5 px drift} */
  KIT.stripDock = function (tl, S, o, t) {
    o = o || {};
    var R = anchor(t, 131), P = S.phase1 || { S0: 1, SK: 0, t: t, lift: 0 };
    var Send = P.S0 + P.SK * (t - P.t), lift = P.lift;
    var rows = cad(DOCK, R);
    for (var k = 1; k < rows.length; k++) {
      var p = rows[k][1];
      tl.to(S.el, { y: lift * (1 - p), scaleX: Send + (1 - Send) * p, scaleY: Send + (1 - Send) * p, duration: F(rows[k][0] - rows[k - 1][0]), ease: "none" }, R.f(rows[k - 1][0]));
    }
    if (o.countNudge !== false) tl.fromTo(S.count, { x: 0, y: 0 }, { x: 0.9, y: -0.5, duration: 0.43, ease: "none", immediateRender: false }, pick(o.countAt, R.s(4.37)));
  };

  /** Waiting outline on socket i (phase 2): fades in over 0.08 s at t, then BREATHES (scale 1 -> 1.056, stroke
   *  2.45 -> 3.05, period 20.5 frames) until `until` (the frame the plug seats; hidden from that frame on). */
  KIT.socketWait = function (tl, S, i, t, until) {
    var cx = SOCK_X0 + SOCK_PITCH * i;
    var svg = svgEl("svg", { class: "kv-outl kv-wait", width: 110, height: 102, style: "left:" + (cx - 55) + "px" }, S.socks);
    var r = svgEl("rect", { x: -0.5, y: 1.5, width: 106, height: 96, rx: 20, fill: "none", stroke: "#ab5b47", "stroke-width": 2.7, "stroke-dasharray": "6.2 2.5", "stroke-dashoffset": -2.85, style: "filter: drop-shadow(0 0 1.5px rgba(255,255,255,0.8))" }, svg);
    tl.fromTo(svg, { opacity: 0 }, { opacity: 1, duration: 0.08, ease: "none" }, t);
    tl.set(svg, { scale: 1, transformOrigin: "52.5px 49.5px", immediateRender: true }, 0);
    var b0 = Math.ceil(t * FPS - 1e-6), nU = Math.round(until * FPS);
    for (var f = b0; f < nU - 1; f++) {
      var ph = (1 - Math.cos((2 * Math.PI * (f + 1 - (b0 + 3))) / 20.5)) / 2;
      tl.to(svg, { scale: 1 + 0.056 * ph, duration: F(1), ease: "none" }, F(f));
      tl.to(r, { attr: { "stroke-width": (2.45 + 0.6 * ph) * Math.min(1, 0.55 + (0.45 * (f + 1 - b0)) / 9) }, duration: F(1), ease: "none" }, F(f));
    }
    tl.set(svg, { opacity: 0 }, F(nU) - 0.004);
    return svg;
  };

  /* ================================================================== 4. BIG PALE NUMERAL */
  var ONE_PATH = "M 576 99 L 578.5 461 Q 579 469 606 470.5 L 647 474 L 647 479.5 L 468 479.5 L 468 475.5 L 500 471 Q 543 468.5 544 461 L 544 142.5 L 455 175.5 Q 446 177 446.5 171 L 448 168.5 L 570 99.5 Q 573 98 576 99 Z";
  var ONE_IN = [[131.5, 0, 0.88, 20], [132, 0.1, 0.9, 18], [133, 0.3, 0.93, 14], [134, 0.65, 0.95, 10], [135, 0.66, 0.96, 8], [136, 0.88, 0.976, 5],
    [137, 0.95, 0.99, 1], [138, 1, 1.008, 0], [139, 1, 1.01, 0], [141, 1, 1.01, 0], [142, 1, 1.005, 0], [144, 1, 1, 0], [147, 1, 1, 0],
    [148, 0.75, 1, 0], [149, 0.1, 1, 0], [150, 0, 1, 0]];
  /** Huge pale clay numeral ("Il primo", item 1 of N) behind the next card: rises 20 px and scales .88 -> 1.01 -> 1
   *  in 12 frames, 3-frame fade when the card covers it. t = reference frame 132 (4.4 s).
   *  o: {n: 1 (traced "1") | any string (Newsreader 560 px, unmeasured), outAt(t+0.5)} */
  KIT.bigNumeral = function (tl, host, o, t) {
    o = o || {};
    var n = String(pick(o.n, 1)), node;
    if (n === "1") {
      node = svgEl("svg", { class: "kv-abs", width: 1080, height: 600, viewBox: "0 0 1080 600", style: "left:0;top:0;opacity:0;overflow:visible;filter:drop-shadow(2.5px 0 1px rgba(255,236,226,0.9))" }, host);
      svgEl("path", { d: ONE_PATH, fill: "#e1bfaf" }, node);
    } else {
      node = put(host, mk("div", "kv-numeral", "top:" + pick(o.top, 60) + "px;opacity:0;filter:drop-shadow(2.5px 0 1px rgba(255,236,226,0.9))", esc(n)));
    }
    var R = anchor(t, 132), RO = anchor(pick(o.outAt, R.f(147)), 147);
    var T = { f: function (f) { return f >= 147 ? RO.f(f) : R.f(f); }, n: R.n };
    var rows = cad(ONE_IN, R);
    tl.set(node, { opacity: 0, scale: rows[0][2], y: rows[0][3], transformOrigin: "561px 479px", immediateRender: true }, 0);
    for (var k = 1; k < rows.length; k++) {
      var a = rows[k - 1][0], b = rows[k][0];
      var d = (a >= 147) === (b >= 147) || RO.A - R.A === 15 ? F(b - a) : T.f(b) - T.f(a);
      tl.to(node, { opacity: rows[k][1], scale: rows[k][2], y: rows[k][3], duration: d, ease: "none" }, T.f(a));
    }
    return node;
  };
  KIT.statNumeral = KIT.bigNumeral;

  /* ================================================================== 5. PLUG + CABLE */
  /** Cable layer: must be created BEFORE the cards (the cable runs under them). */
  KIT.cableLayer = function (host) { return { svg: svgEl("svg", { class: "kv-cables" }, host) }; };
  /** Plug parts for socket i (anchor on the card's bottom edge, ping, ring, plug). Create AFTER the strip.
   *  o: {socket(0), icon(path, default Supabase bolt), iconColor} */
  KIT.plug = function (host, o) {
    o = o || {};
    var i = pick(o.socket, 0), dx = SOCK_PITCH * i;
    var P = { socket: i, dx: dx };
    P.anchor = put(host, mk("div", "kv-anchor", o.anchorX != null ? "left:" + o.anchorX + "px" : ""));
    P.ping = put(host, mk("div", "kv-ping", dx ? "left:" + (397 + dx) + "px" : ""));
    P.ring = put(host, mk("div", "kv-ring", dx ? "left:" + (396 + dx) + "px" : ""));
    P.el = put(host, mk("div", "kv-plug", dx ? "left:" + (416 + dx) + "px" : ""));
    P.el.innerHTML = '<div class="neck"></div><div class="prong" style="left:24px"></div><div class="prong" style="left:42px"></div><div class="body"></div>' +
      '<div class="tile"><svg viewBox="0 0 24 24"' + (o.iconColor ? ' style="fill:' + o.iconColor + '"' : "") + '><path d="' + (o.icon || BOLT) + '"/></svg></div>';
    return P;
  };

  var PLUG_GHOST = [[180, 0, 0.7], [181, 0.25, 0.75], [182, 0.72, 0.86], [183, 0.72, 0.87], [184, 1, 0.97], [185, 1, 1.03], [186, 1, 1.055], [187, 1, 1.03], [189, 1, 1.03], [190, 1, 1]];
  var PLUG_Y = [[6.02, -118, 1], [6.133, -119, 1], [6.2, -121, 1], [6.267, -120, 1], [6.333, -117, 1], [6.367, -114, 1], [6.4, -111, 1], [6.433, -108, 1], [6.467, -97, 1], [6.5, -96, 1], [6.533, -79, 1.03], [6.567, -53, 1.035],
    [F(198), -20.5, 1.04], [F(199), 3, 0.96], [F(200), 1, 0.89], [F(201), 1, 0.89], [F(202), -3, 0.92], [F(203), 0, 0.97], [F(204), 2, 1.02], [F(205), -1, 0.99], [F(206), 0, 1]];
  var RING_ON = [[199, 0.25], [200, 0.55], [202, 0.7], [204, 0.85], [206, 1]];
  var PING = [[199, 0.5, 1.0], [200, 0.55, 1.08], [202, 0.45, 1.2], [204, 0.3, 1.32], [206, 0.12, 1.4], [208, 0, 1.44]];
  var COUNT_POP = [[199, 1.5], [200, 1.3], [201, 1.3], [202, 1.15], [203, 1.07], [204, 1.0]];
  var JOLT = [[198, 0], [199, 3], [200, 2], [201, 2], [202, -2], [203, 1], [204, 2], [205, 0], [208, 1], [209, 0]];
  /** The plug-in: ghost appears hovering 119 px above the socket (0.6 s before), bobs, drops with stretch, seats
   *  with squash (.89) and a 3 px bounce; the strip jolts, a clay ring + expanding ping mark the socket, the count
   *  digit pops 1.5 -> 1, the status dot turns green. t = SEAT frame (reference 199 = 6.633 s).
   *  P from KIT.plug, layer from KIT.cableLayer. o: {count(S.value+1), green(true), seatY(775), fromX(462), fromY(694),
   *  cableAt(t-0.183), anchorAt(t-0.133), ringOut(t+0.687)} */
  KIT.plugIn = function (tl, S, P, layer, o, t) {
    o = o || {};
    var R = anchor(t, 199);
    lin(tl, P.el, PLUG_GHOST, R, function (r) { return { opacity: r[1], scale: r[2] }; }, { transformOrigin: "36px 101px" });
    var seat = pick(o.seatY, 775), ax = pick(o.fromX, 462), ay = pick(o.fromY, 694), cax = ax - 1, cx1 = 450 + P.dx, x1 = 452 + P.dx;
    var cableD = function (dy, sy) {
      if (sy === undefined) sy = 1;
      var yt = seat + dy + 101 * (1 - sy), ya = ay, k = Math.max(8, (yt - ya) * 0.45);
      return "M " + ax + " " + ya + " C " + cax + " " + (ya + k) + ", " + cx1 + " " + (yt - k) + ", " + x1 + " " + yt;
    };
    tl.set(P.el, { y: PLUG_Y[0][1], immediateRender: true }, 0);
    var cable = svgEl("path", { d: "", fill: "none", stroke: "#222", "stroke-width": 7.5, "stroke-linecap": "round" }, layer.svg);
    tl.set(cable, { attr: { d: cableD(PLUG_Y[0][1]) }, opacity: 0, immediateRender: true }, 0);
    tl.set(cable, { opacity: 1 }, pick(o.cableAt, R.s(6.45)));
    for (var k = 1; k < PLUG_Y.length; k++) {
      var dt = PLUG_Y[k][0] - PLUG_Y[k - 1][0];
      tl.to(P.el, { y: PLUG_Y[k][1], scaleY: PLUG_Y[k][2], duration: dt, ease: "none" }, R.s(PLUG_Y[k - 1][0]));
      tl.to(cable, { attr: { d: cableD(PLUG_Y[k][1], PLUG_Y[k][2]) }, duration: dt, ease: "none" }, R.s(PLUG_Y[k - 1][0]));
    }
    tl.set(P.el.querySelectorAll(".prong"), { opacity: 0 }, R.s(6.62));
    tl.set(P.anchor, { opacity: 1 }, pick(o.anchorAt, R.s(6.5)));
    var pl = S.plugged[P.socket] || (S.plugged[P.socket] = put(S.pop, mk("div", "kv-plugged", "left:" + (215 + SOCK_PITCH * P.socket) + "px")));
    tl.set(pl, { opacity: 1 }, R.s(6.62));
    RING_ON.forEach(function (r) { tl.set(P.ring, { opacity: r[1] }, R.f(r[0]) - 0.004); });
    tl.to(P.ring, { opacity: 0, duration: 0.26, ease: "power1.in" }, pick(o.ringOut, R.s(7.32)));
    tl.set(P.ping, { opacity: 0, scale: 1, immediateRender: true }, 0);
    tl.set(P.ping, { opacity: PING[0][1], scale: PING[0][2] }, R.f(199) - 0.004);
    for (k = 1; k < PING.length; k++) tl.to(P.ping, { opacity: PING[k][1], scale: PING[k][2], duration: F(PING[k][0] - PING[k - 1][0]), ease: "none" }, R.f(PING[k - 1][0]));
    var cur = S.value, next = pick(o.count, cur + 1);
    if (S.nums[cur] && S.nums[next]) {
      tl.set(S.nums[cur], { display: "none" }, R.f(199) - 0.004);
      tl.set(S.nums[next], { display: "inline-block" }, R.f(199) - 0.004);
      KIT.statPop(tl, S.nums[next], R.f(199) - 0.004);
      S.value = next;
    }
    if (o.green !== false) tl.fromTo(S.dots.green, { opacity: 0 }, { opacity: 1, duration: F(1), ease: "none" }, R.f(201.33));
    JOLT.forEach(function (r) { tl.set(S.pop, { y: r[1] }, R.f(r[0]) - 0.004); });
    return { cable: cable, plugged: pl };
  };
  KIT.cablePlug = KIT.plugIn;

  /** Stat digit pop (the 0/4 -> 1/4 count): scale 1.5 -> 1.3 -> 1.15 -> 1.07 -> 1 over 5 frames, origin 50% 55%.
   *  t = the hard set that shows the new digit. */
  KIT.statPop = function (tl, node, t) {
    var n = Math.round((t + 0.004) * FPS), R = anchor(F(n), 199);
    tl.set(node, { scale: COUNT_POP[0][1], transformOrigin: "50% 55%" }, t);
    for (var k = 1; k < COUNT_POP.length; k++) tl.to(node, { scale: COUNT_POP[k][1], duration: F(1), ease: "none" }, R.f(COUNT_POP[k - 1][0]));
  };

  /* ================================================================== 6. PLUGIN CARD (card A) */
  var CARD_IN_OP = [[147, 0], [148, 0.33], [149, 0.53], [150, 0.68], [151, 0.82], [152, 0.97], [153, 1]];
  var CARD_IN_Y = [[147, 30], [148, 25], [149, 17.5], [150, 11.5], [151, 6.5], [152, 3], [153, 3], [154, 1.8], [155, 0.8], [156, 0]];
  var BADGE_POP = [[157, 0, 0.85], [158, 0.55, 0.92], [160, 1, 1.0], [161, 1, 1.03], [163, 1, 1.03], [165, 1, 1.01], [166, 1, 1]];
  var MARKET_IN = [[161, 0, 8], [162, 0.3, 7], [163, 0.6, 5.5], [164, 0.85, 4], [165, 0.85, 4], [166, 0.93, 2.5], [168, 0.97, 1.2], [171, 0.99, 0.5], [175, 1, 0]];
  var ICON_POP = [[173, 0, 0.7, -14], [174, 0.45, 0.8, -12], [175, 0.7, 0.867, -4.7], [176, 0.88, 0.95, -1.9], [177, 0.88, 0.95, -1.9], [178, 1, 1, 0],
    [179, 1, 1.036, 1.0], [180, 1, 1.05, 1.5], [181, 1, 1.05, 1.5], [182, 1, 1.04, 1.2], [183, 1, 1.04, 1.2], [184, 1, 1.027, 0.8], [185, 1, 1.011, 0], [186, 1, 1.006, 0], [187, 1, 1, 0]];
  var PROGRESS = [[189, 0], [190, 0.016], [191, 0.082], [192, 0.172], [193, 0.262], [194, 0.376], [195, 0.376], [196, 0.488], [197, 0.681], [198, 0.877], [199, 1]];
  var STATUS_SWAP = [[199, 0, 0.94, 0.85], [200, 0.6, 0.94, 0], [201, 0.6, 0.94, 0], [202, 0.85, 0.97, 0], [203, 1, 1, 0]];
  var CONTENT_OUT = [[207, 1, 0], [208, 0.94, -1.5], [209, 0.79, -5.5], [210, 0.5, -13], [211, 0.06, -20], [212, 0, -22]];
  /** The plugin card: white card 940x519 (r 24) rises 30 px and fades in over 6 frames, grows 0.52 %/s about its
   *  bottom edge; skeleton icon + bars resolve into the real product (icon pops in tilted -14 deg, name types at
   *  0.04 s/char), "ufficiale" badge and marketplace pill pop, then an inner "Claude Code" row whose progress line
   *  fills while the plug drops; status "in attesa" -> "collegato" on the seat frame. Content lifts out after.
   *  t = card arrival (reference frame 147 = 4.9 s).
   *  o: {label, name, icon{path,color,bg}, badge, badgeW, market, marketW, marketLogo, rowName, status[2],
   *      typeStep(.04), badgeAt, marketAt, iconAt, typeAt, connectAt(t+1.733 = seat), exitAt(t+2), growAt, until, outAt} */
  KIT.pluginCard = function (tl, host, o, t) {
    o = o || {};
    KIT.defs();
    var R = anchor(t, 147);
    var x = pick(o.x, 70), y = pick(o.y, 170), w = 940, h = 519;
    var card = put(host, mk("div", "kv-card", x === 70 && y === 170 ? "" : "left:" + x + "px;top:" + y + "px"));
    var icon = o.icon || {}, st = o.status || ["in attesa", "collegato"];
    var badge = pick(o.badge, "ufficiale"), market = pick(o.market, "Marketplace di Anthropic");
    // pill widths: measured for the reference texts, estimated from the character count otherwise
    var badgeW = pick(o.badgeW, badge === "ufficiale" ? 113 : Math.round(18 + 10.5 * badge.length));
    var marketW = pick(o.marketW, market === "Marketplace di Anthropic" ? null : Math.round(49 + 10.4 * market.length));
    var attW = st[0] === "in attesa" ? null : Math.round(21 + 11 * st[0].length), colW = st[1] === "collegato" ? null : Math.round(21 + 11.3 * st[1].length);
    var pc = put(card, mk("div", "kv-layer"));
    pc.innerHTML =
      '<div class="kv-t" style="left:44.6px;top:41.8px;font-weight:600;font-size:23.4px;letter-spacing:1.4px;color:#6e6b66">' + esc(pick(o.label, "PLUGIN")) + "</div>" +
      '<div class="kv-abs" style="left:43.6px;top:95.6px;width:176px;height:177px">' +
        '<svg width="176" height="177" style="position:absolute;left:0;top:0;overflow:visible"><rect x="1" y="1" width="174" height="175" rx="38" fill="#f3f2ef" stroke="#c9c6c1" stroke-width="2.4" stroke-dasharray="6.2 2.45"/></svg>' +
        '<div class="kv-t" style="left:0;top:38px;width:176px;text-align:center;font-family:Newsreader,serif;font-weight:500;font-size:110px;color:#cfccc7">?</div>' +
      "</div>" +
      '<div class="kv-bar" style="left:252px;top:116px;width:299px;height:34px;border-radius:8px;background:#d0d1c3"></div>' +
      '<div class="kv-bar" style="left:252px;top:172px;width:179px;height:22px;background:#e5e1dc"></div>' +
      '<div class="kv-bar" style="left:252.6px;top:251px;width:518px;height:12px;background:#e2deda"></div>' +
      '<div class="kv-bar" style="left:252.6px;top:278.8px;width:379px;height:12px;background:#e2deda"></div>' +
      '<div class="kv-abs" style="left:43.8px;top:95.85px;width:175px;height:175px;border-radius:39.5px;background:' + (icon.bg || "#1a1a1a") + ';box-shadow:0 8px 16px rgba(0,0,0,0.2);opacity:0">' +
        '<svg viewBox="0 0 24 24" style="position:absolute;left:42.5px;top:38.7px;width:91px;height:97.6px;fill:' + (icon.color || "#3ecf8e") + '"><path d="' + (icon.path || BOLT) + '"/></svg>' +
      "</div>" +
      '<div class="kv-t" style="left:250.5px;top:102.9px;font-weight:700;font-size:66px;letter-spacing:-1.1px;color:#1a1a1a"></div>' +
      '<div class="kv-pillx" style="left:252.4px;top:186.7px;width:' + badgeW + 'px;height:35.6px;border:2px solid #bd9b95;color:#a2583b;font-weight:600;opacity:0">' + esc(badge) + "</div>" +
      '<div class="kv-pillx" style="left:' + (marketW != null ? 899.8 - marketW : 600.8) + 'px;top:29px;width:' + pick(marketW, 299) + 'px;height:40.6px;padding-right:4px;background:#f2f0ed;color:#3d3b39;font-size:21.8px;opacity:0">' +
        '<svg viewBox="0 0 24 24" style="width:22px;height:22px;fill:#111;margin-right:9px"><path d="' + (o.marketLogo || ANTHROPIC) + '"/></svg>' + esc(market) +
      "</div>" +
      '<div class="kv-abs" style="left:44.6px;top:341.3px;width:852.3px;height:129.1px;border-radius:18px;background:#f7f5f2;border:1.2px solid #e8e5e0"></div>' +
      '<div class="kv-abs" style="left:71.6px;top:380.2px;width:56px;height:56px;border-radius:11.3px;background:#da6a43">' +
        '<svg viewBox="0 0 24 24" style="position:absolute;left:10.9px;top:10.9px;width:34.2px;height:34.2px;fill:#fff">' + useClaude() + "</svg>" +
      "</div>" +
      '<div class="kv-t" style="left:145.6px;top:392.5px;font-weight:700;font-size:28.65px;color:#141312">' + esc(pick(o.rowName, "Claude Code")) + "</div>" +
      '<svg class="kv-abs" style="left:347.9px;top:406.4px;width:368px;height:3px;overflow:visible"><line x1="0" y1="1.5" x2="368" y2="1.5" stroke="#cbc8c3" stroke-width="3" stroke-dasharray="10.7 9.46"/></svg>' +
      '<div class="kv-abs" style="left:348.9px;top:406.1px;width:363px;height:3.4px;background:#bd5f3e;border-radius:2px;transform-origin:0 50%"></div>' +
      '<div class="kv-pillx" style="left:' + (attW ? 867.3 - attW : 747.3) + 'px;top:387.6px;width:' + (attW || 120) + 'px;height:37.7px;border:2px solid #d4d3cf;background:#fcfbf9;color:#5e5b57;font-size:22.4px;padding-top:3px">' + esc(st[0]) + "</div>" +
      '<div class="kv-pillx" style="left:' + (colW ? 867.9 - colW : 740.1) + 'px;top:386.7px;width:' + (colW || 127.8) + 'px;height:38.6px;border:2px solid #b6c6b9;color:#2e5a46;background:#f6fef9;font-size:22.7px;padding-top:3px;opacity:0">' + esc(st[1]) + "</div>";
    var c = pc.children;
    var C = { el: card, pc: pc, x: x, y: y, w: w, h: h, phIcon: c[1], skTitle: c[2], skSub: c[3], icon: c[6], name: c[7], badge: c[8], market: c[9],
      prog: c[14], att: c[15], col: c[16] };
    var growAt = pick(o.growAt, R.s(5.1)), until = pick(o.until, R.s(8.833));
    C.grow = { at: growAt, rate: 0.0052 };
    C.outAt = o.outAt === null ? null : pick(o.outAt, until);
    // arrival: 6-frame fade + 30 px rise (25 fps hold at f153)
    tl.set(card, { opacity: 0, immediateRender: true }, 0);
    for (var k = 1; k < CARD_IN_OP.length; k++) tl.to(card, { opacity: CARD_IN_OP[k][1], duration: F(1), ease: "none" }, R.f(CARD_IN_OP[k - 1][0]));
    lin(tl, card, CARD_IN_Y, R, function (r) { return { y: r[1] }; }, {});
    tl.fromTo(card, { scale: 1 }, { scale: 1 + 0.0052 * (until - growAt), duration: until - growAt, ease: "none" }, growAt);
    tl.fromTo(C.skTitle, { backgroundColor: "#d9d8cd" }, { backgroundColor: "#d0d1c3", duration: 0.13, ease: "none" }, pick(o.skAt, R.s(5.07)));
    // "ufficiale" badge pop
    var RB = anchor(pick(o.badgeAt, R.f(157)), 157);
    BADGE_POP.forEach(function (r, i) { tl.set(C.badge, { opacity: r[1], scale: r[2], immediateRender: i === 0 }, i === 0 ? 0 : RB.f(r[0]) - 0.004); });
    // marketplace pill: fades in rising 8 px
    var RM = anchor(pick(o.marketAt, R.f(161)), 161);
    lin(tl, C.market, MARKET_IN, RM, function (r) { return { opacity: r[1], y: r[2] }; }, {});
    // skeleton icon -> real icon (tilted pop), skeleton bars out, name typed
    var RI = anchor(pick(o.iconAt, R.f(173)), 173);
    tl.to(C.phIcon, { opacity: 0, duration: 0.07, ease: "none" }, RI.s(5.82));
    steps(tl, C.icon, ICON_POP, RI, function (r) { return { opacity: r[1], scale: r[2], rotation: r[3] }; }, {});
    tl.to([C.skTitle, C.skSub], { opacity: 0, duration: 0.03, ease: "none" }, RI.s(5.81));
    KIT.typeChars(tl, C.name, pick(o.name, "Supabase"), pick(o.typeAt, RI.s(5.825)), pick(o.typeStep, 0.04));
    // connect: progress line fills 10 frames into the seat frame; status swaps on the seat frame
    var RC = anchor(pick(o.connectAt, R.f(199)), 199);
    lin(tl, C.prog, PROGRESS, RC, function (r) { return { scaleX: r[1] }; }, {});
    tl.set(C.col, { opacity: 0, scaleX: 0.94, transformOrigin: "100% 50%", immediateRender: true }, 0);
    STATUS_SWAP.forEach(function (r) {
      tl.set(C.col, { opacity: r[1], scaleX: r[2] }, RC.f(r[0]) - 0.004);
      tl.set(C.att, { opacity: r[3] }, RC.f(r[0]) - 0.004);
    });
    // content lifts out (5 frames) to make room for the diagram
    if (o.exitAt !== null) {
      var RE = anchor(pick(o.exitAt, R.f(207)), 207);
      lin(tl, pc, CONTENT_OUT, RE, function (r) { return { opacity: r[1], y: r[2] }; }, false);
    }
    if (C.outAt != null) KIT.cut(tl, card, C.outAt);
    return C;
  };
  KIT.skillCard = KIT.pluginCard;

  /* ================================================================== 7. DATABASE CYLINDER */
  /** Clay-outlined database cylinder with the product bolt and a label, built hidden (dash / solid / bolt / lbl).
   *  Card-local px (cx 740.2, rx 90.2, top 140, bottom 309.6). o: {label("il tuo database"), icon, iconColor} */
  KIT.database = function (layer, o) {
    o = o || {};
    var svg = svgEl("svg", { width: 940, height: 519, style: "position:absolute;left:0;top:0;overflow:visible" }, layer);
    var cx = 740.2, rx = 90.2, ry = 30.4, top = 140, bot = 309.6;
    var dashed = svgEl("g", { opacity: 0 }, svg);
    svgEl("path", { d: "M 641.1 122.6 A 98.6 24.7 0 0 1 838.3 122.6 L 838.3 340.4 A 98.6 24.7 0 0 1 641.1 340.4 Z", fill: "none", stroke: "#bf8f88", "stroke-width": 2.5, "stroke-dasharray": "5.6 3.27" }, dashed);
    var solid = svgEl("g", { opacity: 0 }, svg);
    svgEl("path", { d: "M " + (cx - rx) + " " + top + " L " + (cx - rx) + " " + bot + " A " + rx + " " + ry + " 0 0 0 " + (cx + rx) + " " + bot + " L " + (cx + rx) + " " + top, fill: "#fff", stroke: "#de9a80", "stroke-width": 3.2 }, solid);
    svgEl("ellipse", { cx: cx, cy: top, rx: rx, ry: ry, fill: "#faf8f4", stroke: "#de9a80", "stroke-width": 3.2 }, solid);
    svgEl("path", { d: "M " + (cx - rx) + " 196.5 A " + rx + " " + ry + " 0 0 0 " + (cx + rx) + " 196.5", fill: "none", stroke: "#de9a80", "stroke-width": 3.2 }, solid);
    svgEl("path", { d: "M " + (cx - rx) + " 253.2 A " + rx + " " + ry + " 0 0 0 " + (cx + rx) + " 253.2", fill: "none", stroke: "#de9a80", "stroke-width": 3.2 }, solid);
    var boltG = svgEl("g", { opacity: 0 }, svg);
    var bolt = svgEl("svg", { x: cx - 25, y: 222.3, width: 50, height: 52, viewBox: "0 0 24 24", fill: o.iconColor || "#3ecf8e" }, boltG);
    svgEl("path", { d: o.icon || BOLT }, bolt);
    var lbl = put(layer, mk("div", "kv-t", "left:640px;top:392px;width:200px;text-align:center;font-weight:500;font-size:25.4px;color:#55534f;opacity:0", esc(pick(o.label, "il tuo database"))));
    return { svg: svg, dash: dashed, solid: solid, bolt: boltG, lbl: lbl };
  };

  /* ================================================================== 8. FLOW DIAGRAM (inside the plugin card) */
  var CUBE_POP = { 212: 0.70, 213: 0.70, 214: 0.86, 215: 0.96, 216: 1.025, 217: 1.045, 218: 1.053, 219: 1.04, 220: 1.03, 221: 1.02, 222: 1.012, 223: 1.006, 224: 1.002 };
  var CUBE_CY = [[212, 398.7], [214, 392], [215, 387], [216, 384.4], [218, 382.3], [219, 383.2], [225, 385.1], [234, 384.5], [240, 384], [252, 384.1], [261, 383.4], [266, 382.6]];
  var CUBE_OP = [[212, 0.45], [214, 0.75], [215, 0.92], [216, 1]];
  var LINE_GROW = [[222, 0.0], [223, 0.035], [224, 0.09], [225, 0.09], [226, 0.212], [227, 0.424], [228, 0.681], [229, 0.847], [230, 0.941], [231, 0.941], [232, 0.983], [233, 1]];
  var PACKET = [0.003, 0.007, 0.028, 0.069, 0.135, 0.231, 0.369, 0.545, 0.703, 0.82, 0.9, 0.952, 0.983, 0.997, 1];
  var DB_DASH = [[230, 0, 0.96], [231, 0.35, 0.97], [232, 0.8, 0.985], [233, 1, 0.994], [234, 1, 1], [250, 1, 1], [251, 0.25, 1], [252, 0, 1]];
  var DB_SOLID = [[248, 0, 0.55], [249, 0.35, 0.6], [250, 0.6, 0.75], [251, 1, 0.9], [252, 1, 0.975], [253, 1, 1.02], [254, 1, 1.04], [256, 1, 1.04], [258, 1, 1.02], [260, 1, 1.0]];
  var CF = function (n) { return Math.floor((5 * n + 2) / 6); };   // 25 fps content frame of output frame n
  function lerpT(T, f) {
    for (var k = 1; k < T.length; k++) if (f <= T[k][0]) { var u = (f - T[k - 1][0]) / (T[k][0] - T[k - 1][0]); return T[k - 1][1] + u * (T[k][1] - T[k - 1][1]); }
    return T[T.length - 1][1];
  }
  /** "Claude -> your database": a real-3D clay cube with the Claude spark (yaw turns +0.4533 deg/frame), its label,
   *  a clay line that grows to the right, five diamond packets on the 25 fps content clock, and a dashed database
   *  placeholder that turns solid (grows from its base, peak 1.04) with the bolt and "il tuo database".
   *  C from KIT.pluginCard (the diagram lives inside that card). t = cube appears (reference frame 212 = 7.067 s).
   *  o: {label("Claude"), lineAt(t+0.333), packets([21,29,36,41,47] frames after t), dbAt(t+0.6), dbSolidAt(t+1.2),
   *      dbLabelAt(t+1.353), until(card cut), db{label,icon}} */
  KIT.flowDiagram = function (tl, C, o, t) {
    o = o || {};
    KIT.defs();
    var R = anchor(t, 212);
    var dg = put(C.el, mk("div", "kv-layer"));
    var cube = svgEl("svg", { class: "kv-abs", style: "left:0;top:0;width:940px;height:519px;overflow:visible;opacity:0" }, dg);
    var fTop = svgEl("polygon", { points: "0,0 0,0 0,0", fill: "#e6927b", stroke: "#e6927b", "stroke-width": 0.6, "stroke-linejoin": "round" }, cube);
    var fFront = svgEl("polygon", { points: "0,0 0,0 0,0", fill: "#d45d3f", stroke: "#d45d3f", "stroke-width": 0.6, "stroke-linejoin": "round" }, cube);
    var fSide = svgEl("polygon", { points: "0,0 0,0 0,0", fill: "#ae462c", stroke: "#ae462c", "stroke-width": 0.6, "stroke-linejoin": "round" }, cube);
    var ast = svgEl("g", { fill: "#fff8f2" }, cube);
    ast.innerHTML = useClaude();
    var lbl = put(dg, mk("div", "kv-t", "left:120px;top:358px;width:200px;text-align:center;font-weight:500;font-size:25px;color:#55524e;opacity:0", esc(pick(o.label, "Claude"))));
    var line = put(dg, mk("div", "kv-abs", "left:338.5px;top:233.6px;width:3px;height:3px;border-radius:1.5px;background:#ae5c48;opacity:0"));
    var dots = put(dg, mk("div"));
    var dbL = put(C.el, mk("div", "kv-layer"));
    var db = KIT.database(dbL, o.db);

    // --- cube: per-frame orthographic + weak-perspective projection (fitted rms 0.3-1 px) ---
    var g = C.grow, SA = function (tt) { return 1 + g.rate * (tt - g.at); };
    var ox = C.x + C.w / 2, oy = C.y + C.h, hw = C.w / 2, hh = C.h, dxC = C.x - 70, dyC = C.y - 170;
    var toL = function (X, Y, S) { return [(X - ox) / S + hw, (Y - oy) / S + hh]; };
    var V = { A: [-1, 1, 1], B: [1, 1, 1], C: [1, 1, -1], D: [-1, 1, -1], E: [-1, -1, 1], F: [1, -1, 1], G: [1, -1, -1] };
    var ph = (24 * Math.PI) / 180, PERSP = 0.019;
    var projector = function (cx, cy, s, th) {
      return function (x, y, z) {
        var x1 = x * Math.cos(th) + z * Math.sin(th), z1 = -x * Math.sin(th) + z * Math.cos(th);
        var y2 = y * Math.cos(ph) - z1 * Math.sin(ph), z2 = y * Math.sin(ph) + z1 * Math.cos(ph);
        var w = 1 / (1 - PERSP * z2);
        return [cx + s * x1 * w, cy - s * y2 * w];
      };
    };
    var pts = function (arr) { return arr.map(function (p) { return p[0].toFixed(2) + "," + p[1].toFixed(2); }).join(" "); };
    var until = pick(o.until, C.outAt != null ? C.outAt : R.s(8.833));
    var nLast = R.A + (Math.round(until * FPS) - R.A);
    for (var n = R.A; n <= nLast; n++) {
      var f = 212 + (n - R.A), tt = F(n), S = SA(tt);
      var th = ((-42.1 + 0.4533 * (f - 219)) * Math.PI) / 180;
      var pop = CUBE_POP[f] != null ? CUBE_POP[f] : 1;
      var s = 70.7 * (S / SA(F(R.A + 13))) * pop;
      var cx = (f <= 225 ? 286.2 : 286.2 - (1.9 * (f - 225)) / 39) + dxC;
      var P = projector(cx, lerpT(CUBE_CY, f) + 1.6 + dyC, s, th);
      var L = {};
      for (var key in V) { var q = P(V[key][0], V[key][1], V[key][2]); L[key] = toL(q[0], q[1], S); }
      var at = F(n) - 0.004;
      tl.set(fTop, { attr: { points: pts([L.A, L.B, L.C, L.D]) } }, at);
      tl.set(fFront, { attr: { points: pts([L.A, L.B, L.F, L.E]) } }, at);
      tl.set(fSide, { attr: { points: pts([L.B, L.C, L.G, L.F]) } }, at);
      // spark on the front face (affine map of face coords; glyph spans 1.04 face units)
      var q0 = P(0, 0, 1), qx = P(1, 0, 1), qy = P(0, 1, 1);
      var O = toL(q0[0], q0[1], S), Ux = toL(qx[0], qx[1], S), Vy = toL(qy[0], qy[1], S);
      var kk = 1.04 / 24, ex = [Ux[0] - O[0], Ux[1] - O[1]], ey = [Vy[0] - O[0], Vy[1] - O[1]];
      var a = ex[0] * kk, b = ex[1] * kk, c = -ey[0] * kk, d = -ey[1] * kk;
      var e = O[0] - 12 * (a + c) - 1.5 * a, ff = O[1] - 12 * (b + d) + 2 * d;
      tl.set(ast, { attr: { transform: "matrix(" + a.toFixed(4) + " " + b.toFixed(4) + " " + c.toFixed(4) + " " + d.toFixed(4) + " " + e.toFixed(2) + " " + ff.toFixed(2) + ")" } }, at);
    }
    tl.set(cube, { opacity: 0, immediateRender: true }, 0);
    steps(tl, cube, CUBE_OP, R, function (r) { return { opacity: r[1] }; }, null);
    tl.fromTo(lbl, { opacity: 0, y: 5 }, { opacity: 1, y: 0, duration: 0.15, ease: "power1.out" }, pick(o.labelAt, R.s(7.19)));
    // --- clay line grows right (dot -> 284.5 px) ---
    var RL = anchor(pick(o.lineAt, R.f(222)), 222), LG = cad(LINE_GROW, RL);
    tl.set(line, { opacity: 1, width: 3 }, RL.f(222) - 0.004);
    for (var k = 1; k < LG.length; k++) tl.to(line, { width: 3 + LG[k][1] * 281.5, duration: F(LG[k][0] - LG[k - 1][0]), ease: "none" }, RL.f(LG[k - 1][0]));
    // --- packets: progress per 25 fps content frame (smooth cadence: per output frame) ---
    (o.packets || [21, 29, 36, 41, 47]).forEach(function (rel, i) {
      var dEl = put(dots, mk("div", "", "position:absolute;left:329px;top:228.2px;width:15.6px;height:15.6px;border-radius:2.5px;background:#d65a37;box-shadow:0 0 0 4px rgba(219,106,69,0.17);opacity:0;transform:rotate(45deg)"));
      tl.set(dEl, { x: 0, opacity: 0, immediateRender: true }, 0);
      var n0 = R.A + rel;
      if (i > 0) tl.set(dEl, { opacity: 0.4 }, F(n0 - 1) - 0.004);
      for (var nn = n0; nn <= n0 + 17; nn++) {
        var kc, prog;
        if (KIT.cadence === "smooth") { kc = ((nn - n0) * 25) / 30; var i0 = Math.min(Math.floor(kc), PACKET.length - 1), i1 = Math.min(i0 + 1, PACKET.length - 1); prog = PACKET[i0] + (kc - Math.floor(kc)) * (PACKET[i1] - PACKET[i0]); }
        else { kc = CF(nn) - CF(n0); prog = PACKET[Math.min(kc, PACKET.length - 1)]; }
        tl.set(dEl, { opacity: kc < PACKET.length ? 1 : 0, x: prog * 286 }, F(nn) - 0.004);
      }
    });
    // --- database: dashed placeholder (f230) -> solid grows from its base (f248) -> label ---
    var RD = anchor(pick(o.dbAt, R.f(230)), 230), RS = anchor(pick(o.dbSolidAt, R.f(248)), 248);
    var T2 = function (f) { return f >= 250 ? RS.f(f + 0) : RD.f(f); };
    var DD = cad(DB_DASH, RD);
    tl.set(db.dash, { opacity: 0, scale: DD[0][2], svgOrigin: "739.7 231.5", immediateRender: true }, 0);
    for (k = 1; k < DD.length; k++) {
      var fa = DD[k - 1][0], fb = DD[k][0];
      var dur = (fa >= 250) === (fb >= 250) || RS.A - RD.A === 18 ? F(fb - fa) : T2(fb) - T2(fa);
      tl.to(db.dash, { opacity: DD[k][1], scale: DD[k][2], duration: dur, ease: "none" }, T2(fa));
    }
    var DS = cad(DB_SOLID, RS);
    tl.set([db.solid, db.bolt], { opacity: 0, scale: DS[0][2], svgOrigin: "740.8 341", immediateRender: true }, 0);
    for (k = 1; k < DS.length; k++) tl.to([db.solid, db.bolt], { opacity: DS[k][1], scale: DS[k][2], duration: F(DS[k][0] - DS[k - 1][0]), ease: "none" }, RS.f(DS[k - 1][0]));
    tl.fromTo(db.lbl, { opacity: 0, y: 3.5 }, { opacity: 1, y: 0, duration: 0.13, ease: "power1.out" }, pick(o.dbLabelAt, RS.s(8.42)));
    return { layer: dg, cube: cube, label: lbl, line: line, db: db };
  };

  /* ================================================================== 9. TOOLS CARD (card B) + TOOL ROWS */
  var CHECK_POP = [[0, 0.5, 0], [0.5, 0.63, 0.5], [1, 0.85, 0.8], [1.5, 1.0, 1], [2.5, 1.1, 1], [3.5, 1.15, 1], [5.5, 1.15, 1], [6.5, 1.1, 1], [7.5, 1.05, 1], [8.5, 1.0, 1]];
  var DB_Y = [177.6, 213.5, 249.5, 285.2];
  var DESC_POP = {
    a: [[0, 0, 0.76, 6], [1, 0.23, 0.82, 5], [2, 0.66, 0.925, 2.5], [3, 0.95, 0.98, 1], [5, 1, 1, 0]],
    b: [[0, 0.02, 0.8, 5], [1, 0.44, 0.88, 4], [2, 0.86, 0.95, 1.5], [3, 1, 0.99, 0.3], [5, 1, 1, 0]]
  };
  var BAR_W = [[189.6, 260], [229.6, 219], [300, 149], [169.6, 300]];
  /** The tools card: header (bolt + product + green "collegato" pill + tracked section word), N tool rows that
   *  enter blurred and staggered, and the solid database on the right that each row talks to.
   *  t = card cut-in (8.833 in the reference; the card appears complete with its database).
   *  o: {name("Supabase"), status("collegato"), section("STRUMENTI"), pillX(auto), sectionX(760), rows[], rowsAt(t-0.008),
   *      stagger(0.072), headerAt(t+0.122), until(growth end), outAt(hard cut), db{label}} */
  KIT.toolsCard = function (tl, host, o, t) {
    o = o || {};
    var R = anchor(t, 265);
    var name = pick(o.name, "Supabase");
    var card = put(host, mk("div", "kv-card"));
    var hdr = put(card, mk("div", "kv-layer", "opacity:0"));
    hdr.innerHTML =
      '<svg viewBox="0 0 24 24" class="kv-abs" style="left:36.4px;top:29px;width:31px;height:31px;fill:#3ecf8e"><path d="' + (o.icon || BOLT) + '"/></svg>' +
      '<div class="kv-t" style="left:80.5px;top:31px;font-weight:700;font-size:28.5px;letter-spacing:-0.2px;color:#1a1a1a">' + esc(name) + "</div>" +
      '<div class="kv-pillx" style="left:' + pick(o.pillX, name === "Supabase" ? 224.6 : 96.5 + 16 * name.length) + 'px;top:28.8px;width:' + (pick(o.status, "collegato") === "collegato" ? 115.7 : Math.round(18 + 10.9 * o.status.length)) + 'px;height:32.5px;border:2px solid #9cc0b4;color:#1a5240;font-weight:500;font-size:19.5px">' + esc(pick(o.status, "collegato")) + "</div>" +
      '<div class="kv-t" style="left:' + pick(o.sectionX, pick(o.section, "STRUMENTI") === "STRUMENTI" ? 760 : Math.round(918 - 17.6 * o.section.length)) + 'px;top:35px;font-weight:600;font-size:22.4px;letter-spacing:2.3px;color:#5c5954">' + esc(pick(o.section, "STRUMENTI")) + "</div>";
    var conns = svgEl("svg", { class: "kv-abs", style: "left:0;top:0;width:940px;height:519px;overflow:visible" }, card);
    var rowsL = put(card, mk("div", "kv-layer"));
    var dbL = put(card, mk("div", "kv-layer"));
    var db = KIT.database(dbL, o.db);
    var B = { el: card, hdr: hdr, conns: conns, rowsL: rowsL, db: db, rows: [] };
    var until = pick(o.until, R.s(14.367));
    tl.set(card, { opacity: 1 }, t);
    tl.set([db.solid, db.bolt, db.lbl], { opacity: 1 }, t);
    tl.fromTo(card, { scale: 1, y: 0.8 }, { scale: 1 + 0.0045 * (until - t), y: 0.8, duration: until - t, ease: "none" }, t);
    tl.fromTo(hdr, { opacity: 0 }, { opacity: 1, duration: 0.15, ease: "power1.out" }, pick(o.headerAt, R.s(8.955)));
    var rowsAt = pick(o.rowsAt, R.s(8.825)), stagger = pick(o.stagger, 0.072);
    (o.rows || []).forEach(function (T, i) { B.rows.push(KIT.toolRow(tl, B, T, i, rowsAt + i * stagger)); });
    if (o.outAt != null) KIT.cut(tl, card, o.outAt);
    return B;
  };

  /** One tool row (inside KIT.toolsCard; can be called directly with the card handle B and row index i).
   *  Skeleton row -> active (clay border, pink icon tile), mono name typed, description typed with a caret (or popped
   *  in for short results), connector drawn from the row to the database, a packet travels DB -> row, green check
   *  pops (0.5 -> 1.15 -> 1 over 8.5 frames). tIn = row entrance (blur 6 -> 0, y 25 -> 0).
   *  T: {name, desc, icon('terminal'|'layers'|'braces'|'shield'|svg inner), badge('TS'), mode('type'|'pop'),
   *      at (activation), swapAt(at+0.01), nameAt(at+0.02), nameStep(0.016) | nameFrames[[frame,chars]],
   *      descAt(at+0.3), descStep(0.024) | descFrames, caretAt(descAt), popAt(at+0.55), pop('a'|'b'|rows),
   *      connAt(at+0.18), connDur(0.09), connEase, bend(0), packetAt(at+0.3), packetHold(0.07), checkAt(desc end+0.05), bars[b1,b2]} */
  KIT.toolRow = function (tl, B, T, i, tIn) {
    var top = 86 + 104 * i, at = T.at, mode = T.mode || (T.fade ? "pop" : "type");
    var icon = KIT.TOOL_ICONS[T.icon] || T.icon || KIT.TOOL_ICONS[["terminal", "layers", "braces", "shield"][i % 4]];
    var bars = T.bars || BAR_W[i % 4];
    var r = put(B.rowsL, mk("div", "kv-row", "top:" + top + "px"));
    put(r, mk("div", "bgs"));
    var bga = put(r, mk("div", "bga"));
    put(r, mk("div", "tile"));
    var tilea = put(r, mk("div", "tilea", "", '<svg viewBox="0 0 24 24">' + icon + "</svg>"));
    var b1 = put(r, mk("div", "b1", "width:" + bars[0] + "px")), b2 = put(r, mk("div", "b2", "width:" + bars[1] + "px"));
    var dc = svgEl("svg", { class: "dc", width: 39, height: 39 }, r);
    svgEl("circle", { cx: 19.5, cy: 19.5, r: 18.5, fill: "none", stroke: "#cfccc7", "stroke-width": 1.6, "stroke-dasharray": "4 3.2" }, dc);
    var ck = put(r, mk("div", "ck", "", '<svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'));
    var name = put(r, mk("div", "name")), desc = put(r, mk("div", "desc"));
    // entrance + activation
    tl.fromTo(r, { opacity: 0, filter: "blur(6px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.26, ease: "power1.out" }, tIn);
    tl.fromTo(r, { y: 25 }, { y: 0, duration: 0.28, ease: "power2.out" }, tIn);
    tl.to(bga, { opacity: 1, duration: 0.07, ease: "none" }, at);
    var swapAt = pick(T.swapAt, at + F(0.3));
    tl.to(tilea, { opacity: 1, duration: F(2.5), ease: "none" }, swapAt);
    tl.to([b1, b2], { opacity: 0, duration: F(2.3), ease: "none" }, swapAt);
    // name typed (per measured output frame, or at nameStep s/char)
    var firstF = function (tab, k) { for (var j = 0; j < tab.length; j++) if (tab[j][1] > k) return tab[j][0]; return tab[tab.length - 1][0]; };
    var nm = String(T.name), nn = nm.length, nameAt = pick(T.nameAt, at + 0.02), nameDur = pick(T.nameDur, pick(T.nameStep, 0.016) * nn);
    nm.split("").forEach(function (ch, k) {
      var s = put(name, mk("span", "", "", esc(ch)));
      tl.set(s, { display: "inline" }, T.nameFrames ? F(firstF(T.nameFrames, k)) - 0.004 : nameAt + (nameDur * k) / nn);
    });
    // description
    var ds = String(T.desc), m = ds.length;
    var descAt = pick(T.descAt, at + 0.3), descDur = pick(T.descDur, pick(T.descStep, 0.024) * m), descEnd;
    if (T.badge) put(desc, mk("span", "kv-ts", "display:none", esc(T.badge)));
    var caret = put(desc, mk("span", "kv-caret"));
    if (mode === "pop") {
      desc.innerHTML = (T.badge ? '<span class="kv-ts">' + esc(T.badge) + "</span>" : "") + "<span>" + esc(ds) + "</span>";
      desc.style.fontSize = T.badge ? "19.0px" : "19.28px";
      if (!T.badge) desc.style.left = "90.5px";
      var DP = Array.isArray(T.pop) ? T.pop : DESC_POP[T.pop || "a"];
      var popAt = pick(T.popAt, at + 0.55), RP = anchor(popAt, 0);
      tl.set(desc, { opacity: 0, scale: DP[0][2], y: DP[0][3], transformOrigin: "50% 50%", immediateRender: true }, 0);
      tl.set(desc, { opacity: DP[0][1] }, RP.f(DP[0][0]) - 0.004);
      for (var k = 1; k < DP.length; k++) tl.to(desc, { opacity: DP[k][1], scale: DP[k][2], y: DP[k][3], duration: F(DP[k][0] - DP[k - 1][0]), ease: "none" }, RP.f(DP[k - 1][0]));
      descEnd = RP.f(DP[DP.length - 1][0]);
    } else {
      var tsEl = desc.querySelector(".kv-ts");
      if (tsEl) tl.set(tsEl, { display: "inline-block" }, descAt - 0.03);
      var chars = ds.split("").map(function (ch) { return put(desc, mk("span", "c", "", ch === " " ? "&nbsp;" : esc(ch))); });
      desc.appendChild(caret);
      chars.forEach(function (s, k) { tl.set(s, { display: "inline" }, T.descFrames ? F(firstF(T.descFrames, k)) - 0.004 : descAt + (descDur * k) / m); });
      tl.set(caret, { opacity: 1 }, pick(T.caretAt, descAt));
      tl.set(caret, { opacity: 0 }, descAt + descDur + 0.46);
      descEnd = T.descFrames ? F(T.descFrames[T.descFrames.length - 1][0]) : descAt + descDur;
    }
    // connector row -> database (drawn with the real path length)
    var x0 = 570, y0 = top + 45.5, x1 = 649, y1 = i < DB_Y.length ? DB_Y[i] : DB_Y[3] + 35.9 * (i - 3), bend = T.bend || 0;
    var dPath = "M " + x0 + " " + y0 + " C " + (x0 + 40) + " " + (y0 + bend) + ", " + (x1 - 40) + " " + (y1 + bend) + ", " + x1 + " " + y1;
    var p = svgEl("path", { d: dPath, fill: "none", stroke: "#d99786", "stroke-width": 3.2 }, B.conns);
    var Lp = Math.ceil(p.getTotalLength()) + 2;
    p.setAttribute("stroke-dasharray", Lp);
    p.setAttribute("stroke-dashoffset", Lp);
    tl.to(p, { attr: { "stroke-dashoffset": 0 }, duration: pick(T.connDur, 0.09), ease: T.connEase || "none" }, pick(T.connAt, at + 0.18));
    // packet DB -> row along the bezier (12 linear steps of a power1.inOut ease)
    var pd = svgEl("circle", { r: 6, fill: "#d9603b", stroke: "rgba(219,106,69,0.22)", "stroke-width": 7, "paint-order": "stroke", opacity: 0 }, B.conns);
    var bez = function (u) {
      var v = 1 - u;
      return [v * v * v * x1 + 3 * v * v * u * (x1 - 40) + 3 * v * u * u * (x0 + 40) + u * u * u * x0, v * v * v * y1 + 3 * v * v * u * (y1 + bend) + 3 * v * u * u * (y0 + bend) + u * u * u * y0];
    };
    var packetAt = pick(T.packetAt, at + 0.3), stepsN = 12, dur = 0.24, t0 = packetAt + 0.13;
    tl.set(pd, { attr: { cx: x1, cy: y1, r: 3 }, opacity: 1 }, packetAt);
    tl.to(pd, { attr: { r: 7 }, duration: 0.08, ease: "power2.out" }, packetAt);
    var ease = gsap.parseEase("power1.inOut");
    for (var q = 1; q <= stepsN; q++) { var pt = bez(ease(q / stepsN)); tl.to(pd, { attr: { cx: pt[0], cy: pt[1] }, duration: dur / stepsN, ease: "none" }, t0 + (dur * (q - 1)) / stepsN); }
    tl.set(pd, { opacity: 0 }, t0 + dur + pick(T.packetHold, 0.07));
    // check
    var checkAt = pick(T.checkAt, descEnd + 0.05);
    tl.to(dc, { opacity: 0, duration: 0.05, ease: "none" }, checkAt);
    tl.set(ck, { opacity: 0, scale: CHECK_POP[0][1], immediateRender: true }, 0);
    for (var c = 1; c < CHECK_POP.length; c++) tl.to(ck, { scale: CHECK_POP[c][1], opacity: CHECK_POP[c][2], duration: F(CHECK_POP[c][0] - CHECK_POP[c - 1][0]), ease: "none" }, checkAt + F(CHECK_POP[c - 1][0]));
    return { el: r, name: name, desc: desc, check: ck, connector: p, packet: pd };
  };
  KIT.checkRow = KIT.toolRow;

  /* ================================================================== 10. BROWSER CARD (card C) */
  var BROWSER_IN = [[431, 24, 0.981, 20], [432, 12.3, 0.991, 8], [433, 5, 0.998, 3], [434, 0, 1, 0], [435, 0, 1, 0]];
  /** Rebuilt product dashboard in a browser mock (traffic lights, URL bar typing, sidebar, table, green CTA).
   *  Cuts in (no fade) from y +24 / scale .981 to rest in 3 frames. Sits above the cable anchor (z-index 2).
   *  t = cut frame (reference frame 431 = 14.367 s). o: {url("sup"), urlFrames([[2,1],[3,3]] frames after t:chars),
   *  urlStep(1 frame/char after the measured ones), button("Apri"), rows(5), icon} */
  KIT.browserCard = function (tl, host, o, t) {
    o = o || {};
    var R = anchor(t, 431);
    var card = put(host, mk("div", "kv-card kv-browser", "left:72.8px;top:176.2px;width:935.5px;height:518px;background:#ffffff;z-index:2"));
    var url = pick(o.url, "sup");
    var h = "";
    [21.7, 44, 66.3].forEach(function (x) { h += '<div class="kv-abs" style="left:' + x + 'px;top:23px;width:12px;height:12px;border-radius:50%;background:#dcdad6"></div>'; });
    h += '<div class="kv-abs" style="left:113px;top:11px;width:615px;height:35px;border-radius:18px;background:#f0eeeb"></div>';
    h += '<svg viewBox="0 0 24 24" class="kv-abs" style="left:128px;top:17px;width:24px;height:24px;fill:#3ecf8e"><path d="' + (o.icon || BOLT) + '"/></svg>';
    h += '<div class="kv-t" style="left:162px;top:18px;font-weight:500;font-size:21px;color:#55524e">' + url.split("").map(function (ch) { return "<span>" + esc(ch) + "</span>"; }).join("") + "</div>";
    h += '<div class="kv-abs" style="left:0;top:58px;width:935px;height:1.5px;background:#eeece8"></div>';
    h += '<div class="kv-abs" style="left:0;top:59px;width:83px;height:458px;background:#f7f5f1;border-radius:0 0 0 24px"></div>';
    [85, 148, 211, 274, 337].forEach(function (y, i) { h += '<div class="kv-abs" style="left:25px;top:' + y + 'px;width:32px;height:32px;border-radius:7px;background:' + (i ? "#e6ded5" : "#d0cfc3") + '"></div>'; });
    h += '<div class="kv-bar" style="left:119px;top:93px;width:259px;height:20px;border-radius:10px;background:#d0cec5"></div>';
    h += '<div class="kv-pillx" style="left:815px;top:85px;width:85px;height:42px;border-radius:8px;background:#3ecf8e;color:#0f3d27;font-weight:700;font-size:22px">' + esc(pick(o.button, "Apri")) + "</div>";
    h += '<div class="kv-abs" style="left:119px;top:150px;width:781px;height:337px;border-radius:8px;background:#fff;border:1.5px solid #efedea"></div>';
    h += '<div class="kv-abs" style="left:120px;top:151px;width:779px;height:55px;border-radius:8px 8px 0 0;background:#f6f4f1"></div>';
    h += '<div class="kv-layer"></div>';
    card.innerHTML = h;
    var ct = card.lastChild;
    var COLS = [[143, 40], [268, 90], [477, 70], [656, 120]], CW = [68, 149, 119, 199], NR = pick(o.rows, 5);
    COLS.forEach(function (cw) { put(ct, mk("div", "kv-bar", "left:" + cw[0] + "px;top:173px;width:" + cw[1] + "px;height:12px;background:#d0cec8")); });
    for (var rI = 0; rI < NR; rI++) {
      var yy = 229 + rI * 56;
      COLS.forEach(function (cw, c) { put(ct, mk("div", "kv-bar", "left:" + cw[0] + "px;top:" + yy + "px;width:" + CW[c] + "px;height:12px;background:#e1dfdb")); });
      if (rI < NR - 1) put(ct, mk("div", "kv-abs", "left:120px;top:" + (yy + 34) + "px;width:779px;height:1px;background:#efedea"));
    }
    tl.set(card, { opacity: 1, y: BROWSER_IN[0][1], scale: BROWSER_IN[0][2], transformOrigin: "50% 50%" }, R.f(431) - 0.004);
    for (var k = 1; k < BROWSER_IN.length; k++) tl.to(card, { y: BROWSER_IN[k][1], scale: BROWSER_IN[k][2], duration: F(1), ease: "none" }, R.f(BROWSER_IN[k - 1][0]));
    var spans = card.children[5].children;
    tl.set(spans, { opacity: 0, immediateRender: true }, 0);
    var uf = o.urlFrames || [[2, 1], [3, 3]], shown = 0;
    uf.forEach(function (r) { for (var j = shown; j < Math.min(r[1], spans.length); j++) tl.set(spans[j], { opacity: 1 }, R.f(431 + r[0]) - 0.004); shown = Math.max(shown, r[1]); });
    var last = uf[uf.length - 1][0], stepF = pick(o.urlStep, 1);
    for (var j2 = shown; j2 < spans.length; j2++) tl.set(spans[j2], { opacity: 1 }, R.f(431 + last + stepF * (j2 - shown + 1)) - 0.004);
    return { el: card, url: card.children[5], table: ct };
  };

  /** Every measured per-frame table, keyed by name (rows are [reference frame, values...]). Read-only reference. */
  KIT.TABLES = { TITLE_IN: TITLE_IN, SUB_IN: SUB_IN, STRIP_POP: STRIP_POP, NO_DOT: NO_DOT, NO_SHAKE: NO_SHAKE, QPOP: QPOP, QTOPS: QTOPS,
    OUT_ON: OUT_ON, OUT_SIZE: OUT_SIZE, DOCK: DOCK, ONE_IN: ONE_IN, PLUG_GHOST: PLUG_GHOST, PLUG_Y: PLUG_Y, RING_ON: RING_ON, PING: PING,
    COUNT_POP: COUNT_POP, JOLT: JOLT, CARD_IN_OP: CARD_IN_OP, CARD_IN_Y: CARD_IN_Y, BADGE_POP: BADGE_POP, MARKET_IN: MARKET_IN,
    ICON_POP: ICON_POP, PROGRESS: PROGRESS, STATUS_SWAP: STATUS_SWAP, CONTENT_OUT: CONTENT_OUT, CUBE_POP: CUBE_POP, CUBE_CY: CUBE_CY,
    CUBE_OP: CUBE_OP, LINE_GROW: LINE_GROW, PACKET: PACKET, DB_DASH: DB_DASH, DB_SOLID: DB_SOLID, CHECK_POP: CHECK_POP, DESC_POP: DESC_POP,
    BROWSER_IN: BROWSER_IN };

  /* ================================================================== 11. CAPTIONS */
  /** Caption rail (y 921-998, chip centred on the seam). Create it LAST inside the graphics wrapper. */
  KIT.captionRail = function (host) { return put(host, mk("div", "kv-caps")); };

  /** Hard-swap caption chips with reference B's tiny pop (first frame ~0.94-0.98 of final width, then 1).
   *  chips: [{text ("DI *SUPABASE*": *word* = accent), k (frame) | t (seconds), pop:[scales per frame], k1 (optional off frame)}]
   *  A chip stays until the next chip. o: {end (composition end: the last chip is never hidden), hotColor(#ec987f),
   *  hotDelay(3 frames: the accent word turns clay 0.1 s after the chip), pop([0.945, 0.99] default)} */
  KIT.captions = function (tl, rail, chips, o) {
    o = o || {};
    var END = pick(o.end, Infinity), hotColor = pick(o.hotColor, "#ec987f"), hotDelay = pick(o.hotDelay, 3), defPop = o.pop || [0.945, 0.99];
    var frameOf = function (c) { return c.k != null ? c.k : Math.round(c.t * FPS); };
    return chips.map(function (c, i) {
      var f0 = frameOf(c), t0 = F(f0);
      var html = esc(String(c.text).toUpperCase()).replace(/\*([^*]+)\*/g, '<span class="kv-hot">$1</span>');
      var node = put(rail, mk("div", "kv-chip"));
      var inn = put(node, mk("div", "in", "", html));
      var next = chips[i + 1];
      var t1 = c.k1 != null ? F(c.k1) : next ? F(frameOf(next)) : END + 1;
      tl.set(node, { opacity: 1 }, t0 - 0.004);
      var pops = c.pop || defPop;
      pops.concat([1]).forEach(function (v, k) { tl.set(inn, { scale: v, immediateRender: k === 0 ? false : undefined }, F(f0 + k) - 0.004); });
      if (t1 < END) tl.set(node, { opacity: 0 }, t1 - 0.004);
      var hot = inn.querySelectorAll(".kv-hot");
      if (hot.length) tl.set(hot, { color: hotColor }, F(f0 + hotDelay));
      return node;
    });
  };
  KIT.captionChip = function (tl, rail, text, k, k1, o) { return KIT.captions(tl, rail, [{ text: text, k: k, k1: k1 }], o)[0]; };

  /** Group transcript words into reference B's chips: up to 3 words, any punctuation closes a chip, UPPERCASE,
   *  punctuation stripped; chip frame = floor((start + offset) * 30) with offset 0.12 s (median editor lag).
   *  words: [{text,start,end}]. Fix misheard / missing words and spelled-out digits before or after. */
  KIT.chunkWords = function (words, o) {
    o = o || {};
    var max = pick(o.max, 3), off = pick(o.offset, 0.12), groups = [], cur = [];
    words.forEach(function (w, i) {
      cur.push(w);
      if (cur.length >= max || /[.,!?;:]["')\]]*$/.test(w.text) || i === words.length - 1) { groups.push(cur); cur = []; }
    });
    var last = -1;
    return groups.map(function (g) {
      var k = Math.max(last + 1, Math.floor((g[0].start + off) * FPS + 1e-6));
      last = k;
      return { text: g.map(function (w) { return w.text; }).join(" ").replace(/[.,!?;:"]+(?=\s|$)/g, "").toUpperCase(), k: k };
    });
  };
})(window);
