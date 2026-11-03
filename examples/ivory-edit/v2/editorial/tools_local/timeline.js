      (function () {
        const END = /*@END*/0, FPS = 30;
        const RUNS = /*@RUNS*/[];
        const WINDOWS = /*@WINDOWS*/[];
        const HUD = /*@HUD*/[];
        const PLUGS = /*@PLUGS*/[];
        const CAPS = /*@CAPS*/[];
        const tl = gsap.timeline({ paused: true });
        // marks the text for tools/beat_render/ownership.py and groups tweens at runtime for the owner audit
        const OWN = (window.__own = {}); let curOwn = null; const seen = new Set();
        function own(id) {
          const fresh = tl.getChildren(false, true, true).filter((c) => !seen.has(c));
          fresh.forEach((c) => seen.add(c));
          (OWN[curOwn || "shell"] = OWN[curOwn || "shell"] || []).push(...fresh);
          curOwn = id;
        }
        const $ = (s) => document.querySelector(s);
        const A = (t) => t - 0.004; // state switches land just before the frame boundary
        const el = (tag, cls, parent, style, html) => {
          const e = document.createElement(tag);
          if (cls) e.className = cls;
          if (style) e.setAttribute("style", style);
          if (html != null) e.innerHTML = html;
          parent.appendChild(e);
          return e;
        };
        const fIn = (t) => Math.ceil((t - 0.004) * FPS - 1e-6) / FPS; // same first visible frame as show() and frame_of()
        const use = (id, cls) => `<svg class="${cls || ""}"><use href="#${id}"/></svg>`;

        // ---------- shared motion helpers ----------
        function show(sel, t) { tl.set(sel, { opacity: 1 }, A(t)); }
        function hide(sel, t) { tl.set(sel, { opacity: 0 }, A(t)); }
        // STYLE pop: scale .6 -> 1 back.out(1.7), opacity over the first .1 s
        function pop(sel, t, dur) {
          tl.fromTo(sel, { scale: 0.6, transformOrigin: "50% 50%" }, { scale: 1, duration: dur || 0.26, ease: "back.out(1.7)", immediateRender: false }, t);
          tl.fromTo(sel, { opacity: 0 }, { opacity: 1, duration: 0.1, ease: "none", immediateRender: false }, t);
        }
        // a first element: opaque on its own first frame, the scale does the arrival
        function popFirst(sel, t) {
          show(sel, t);
          tl.fromTo(sel, { scale: 0.6, transformOrigin: "50% 50%" }, { scale: 1, duration: 0.26, ease: "back.out(1.7)", immediateRender: false }, A(t));
        }
        function slotPop(sel, t) {
          show(sel, t);
          tl.fromTo(sel, { scale: 0, y: -22 }, { scale: 1, y: 0, duration: 0.35, ease: "back.out(2)", immediateRender: false }, A(t));
        }
        // STYLE arrival, y + opacity
        function rise(sel, t, dy, d) {
          tl.fromTo(sel, { y: dy == null ? 12 : dy, opacity: 0 }, { y: 0, opacity: 1, duration: d || 0.2, ease: "power3.out", immediateRender: false }, t);
        }
        // card opaque on frame 1, then the slow push s(t) = 1 + k (t - t_in), bottom centre
        function cutIn(sel, t0, t1, origin) {
          const t = fIn(t0), o = origin || "50% 100%";
          tl.fromTo(sel, { y: 33, scale: 0.975, transformOrigin: o }, { y: 0, scale: 1, duration: 0.11, ease: "power2.out", immediateRender: false }, t);
          if (t1) tl.to(sel, { scale: 1 + 0.0052 * (t1 - t - 0.11), duration: t1 - t - 0.11, ease: "none" }, t + 0.11);
        }
        function on(sel, t, d) { tl.fromTo(sel, { opacity: 0 }, { opacity: 1, duration: d || 0.25, ease: "power1.out", immediateRender: false }, t); }
        function off(sel, t, d) { tl.to(sel, { opacity: 0, duration: d || 0.25, ease: "power1.in" }, t); }
        function drawRect(sel, t, d) {
          show(sel, t);
          tl.fromTo(sel + "-r", { attr: { "stroke-dashoffset": 1 } }, { attr: { "stroke-dashoffset": 0 }, duration: d, ease: "power2.inOut", immediateRender: false }, A(t));
        }
        function drawPath(sel, t, d, from) {
          tl.fromTo(sel, { attr: { "stroke-dashoffset": from } }, { attr: { "stroke-dashoffset": 0 }, duration: d, ease: "power2.out", immediateRender: false }, t);
        }
        // serif title word: fade + scale .9 -> 1 + rise 5 px, .2 s
        function word(sel, t) {
          tl.fromTo(sel, { opacity: 0, scale: 0.9, y: 5, transformOrigin: "50% 70%" }, { opacity: 1, scale: 1, y: 0, duration: 0.2, ease: "power2.out", immediateRender: false }, t);
        }

        // ---------- grid + layout runs ----------
        tl.fromTo("#grid", { x: -0.115, y: -0.105 }, { x: -0.115 + 1.166 * END, y: -0.105 + 7.5 * END, duration: END, ease: "none" }, 0);
        const HUD_G = 570; // strip y780 -> y1350
        RUNS.forEach(([a, , k], i) => {
          const t = i ? A(a) : 0;
          tl.set("#face-wrap", { opacity: k === "split" ? 1 : 0, immediateRender: !i }, t);
          tl.set("#hud", { y: k === "full-graphic" ? HUD_G : 0, opacity: k === "full-face" ? 0 : 1, immediateRender: !i }, t);
        });

        // ---------- scene windows: every outgoing scene is gone on the incoming scene's first frame ----------
        WINDOWS.forEach(([s, a, b]) => {
          if (a > 0) show(s, a); else tl.set(s, { opacity: 1, immediateRender: true }, 0);
          hide(s, b);
        });

        // ---------- scene blocks: one per scene group, opened by its marker line, in window order. Rules in build_kit/README.md ----------
        own("scene.sc-hook");
        // ---- b01-b02 hook. Slow push about the window centre, then one straight push, pin only, then the slow push about the centre again
        tl.fromTo("#hk-pl-p", { scale: 1, x: 0, y: 0 }, { scale: 1.01, x: -4.5, y: -1.685, duration: 0.32, ease: "none" }, 0);
        tl.to("#hk-pl-p", { scale: 2.3, x: -36, y: -468.67, duration: 0.6, ease: "power2.inOut" }, 0.32);
        tl.fromTo("#hk-s", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 1.76);
        tl.to("#hk-pl-p", { scale: 2.33549, x: -43.5, y: -478.5, duration: 2.967, ease: "none" }, 2.2);
        tl.fromTo("#hk-a", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 2.8);
        tl.fromTo("#hk-u", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 4.24);

        own("scene.sc-title");
        // ---- b03 his recording, first frame held 0.133 s
        cutIn("#ti-g", 5.167, 0);

        own("scene.sc-names");
        // ---- b04-b05 before-after
        tl.fromTo("#nm-sa", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 8.32);
        tl.fromTo("#nm-sb", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 9.2);
        tl.to("#nm-a", { x: -240, y: -195, scale: 0.65, duration: 0.24, ease: "power2.out" }, 9.9);
        tl.to("#nm-b", { x: 240, y: -415, scale: 0.65, duration: 0.24, ease: "power2.out" }, 9.9);
        show("#nm-art", 10.16);
        cutIn("#nm-art", 10.16, 0, "50% 50%");
        rise("#nm-u", 10.8, 24, 0.55);

        own("scene.sc-week");
        // ---- b06-b07 the post card returns on its lower strip, one straight push, then the marker
        cutIn("#wk-g", 11.5, 0);
        tl.to("#wk-pl-p", { scale: 1.7899, x: -28.02, y: -28.02, duration: 0.5, ease: "power2.inOut" }, 12.64);
        tl.fromTo("#wk-m", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 14.16);

        own("scene.sc-ultra");
        // ---- b08-b09 plan card, row, footnote with verified lit
        drawRect("#ul-o", 15.04, 0.3);
        tl.to("#ul-c1", { y: -197, duration: 0.3, ease: "power3.out" }, 16);
        rise("#ul-c2", 16, 40, 0.3);
        rise("#ul-c3", 16.64, 40, 0.3);
        tl.fromTo("#ul-m", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 17.2);

        own("scene.sc-q10");
        // ---- b10 quiet panel, his opinion
        tl.fromTo("#q10-g", { scale: 1, transformOrigin: "50% 50%" }, { scale: 1.01508, duration: 2.9, ease: "none", immediateRender: false }, A(18.367));
        drawRect("#q10-o", 19.76, 0.3);
        off("#q10-o", 21.0, 0.2);

        own("scene.sc-codex");
        // ---- b11-b12 the whole paragraph, both marker parts on one frame, source line on Codex
        tl.fromTo("#cx-g", { scale: 1.01508, transformOrigin: "50% 50%" }, { scale: 1.03085, duration: 3.033, ease: "none", immediateRender: false }, A(21.267));
        tl.fromTo(["#cx-m0", "#cx-m1"], { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 21.44);
        rise("#cx-s", 22.56, 12, 0.2);

        own("scene.sc-q13");
        // ---- b13 the Codex line holds, Claude's page lands on finally, its line lights on joined
        show("#q13-m0", 24.3);
        show("#q13-m1", 24.3);
        rise("#q13-b", 25.62, 18, 0.2);
        tl.fromTo(["#q13-m2", "#q13-m3"], { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, A(26.66));
        tl.fromTo("#q13-g", { scale: 1, transformOrigin: "50% 50%" }, { scale: 1.0156, duration: 3.0, ease: "none", immediateRender: false }, A(24.3));

        own("scene.sc-list");
        // ---- b14-b16 each recap row lands with its check; the HUD rings on the same words
        hide("#ls-b0", 27.94);
        rise("#ls-r0", 27.94, 12, 0.2);
        show("#ls-c0", 27.94);
        tl.fromTo("#ls-c0", { scale: 0, transformOrigin: "50% 50%" }, { scale: 1, duration: 0.35, ease: "back.out(2)", immediateRender: false }, A(27.94));
        hide("#ls-b1", 29.3);
        rise("#ls-r1", 29.3, 12, 0.2);
        show("#ls-c1", 29.3);
        tl.fromTo("#ls-c1", { scale: 0, transformOrigin: "50% 50%" }, { scale: 1, duration: 0.35, ease: "back.out(2)", immediateRender: false }, A(29.3));
        hide("#ls-b2", 30.58);
        rise("#ls-r2", 30.58, 12, 0.2);
        show("#ls-c2", 30.58);
        tl.fromTo("#ls-c2", { scale: 0, transformOrigin: "50% 50%" }, { scale: 1, duration: 0.35, ease: "back.out(2)", immediateRender: false }, A(30.58));

        own("scene.sc-max20");
        // ---- b17 his selection, first frame held 0.10 s
        cutIn("#mx-g", 31.3, 0);

        own("scene.sc-four");
        // ---- b18-b19 the assumed math struck, then his drag
        pop("#fr-row", 33.86);
        tl.fromTo("#fr-st", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.25, ease: "power2.out", immediateRender: false }, 34.3);
        tl.to("#fr-c", { scale: 0.72, y: -230, transformOrigin: "540px 360px", duration: 0.3, ease: "power3.out" }, 34.567);
        show("#fr-cg", 34.567);
        cutIn("#fr-cg", 34.567, 0, "50% 50%");

        own("scene.sc-over");
        // ---- b20-b21 Overell post, two markers. The second phrase wraps, so its two parts share a frame
        cutIn("#ov-g", 36.617, 0);
        tl.fromTo("#ov-pl-p", { scale: 1, transformOrigin: "50% 50%" }, { scale: 1.01733, duration: 3.333, ease: "none", immediateRender: false }, 36.617);
        tl.fromTo("#ov-m0", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 37.86);
        tl.fromTo(["#ov-m1", "#ov-m2"], { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 38.9);

        own("scene.sc-table");
        // ---- b22 week row, then 5x and 10x with the bracket
        tl.fromTo("#tb-row", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.3, ease: "power2.out", immediateRender: false }, 40.34);
        on("#tb-o0", 41.3, 0.25);
        on("#tb-o1", 41.3, 0.25);
        drawPath("#tb-br", 41.3, 0.3, 1);
        word("#tb-dbl", 41.3);

        own("scene.sc-q23");
        // ---- b23 Overell's admission; the marker lands on pissed
        tl.fromTo(["#q23-m0", "#q23-m1"], { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.2, ease: "power2.out", immediateRender: false }, A(43.62));

        own("scene.sc-q24");
        // ---- b24 his rename selection, within its 2.666667 s source
        tl.set("#face", { scale: 1.08, transformOrigin: "50% 8%" }, A(44.183));
        tl.to("#face", { scale: 1, duration: 0.16, ease: "power2.out" }, 46.5);
        tl.set("#face", { scale: 1 }, A(46.667));

        own("scene.sc-q25");
        // ---- b25 rename facts only; a small hedge tag on sure
        show("#q25-m", 46.7);
        word("#q25-tag", 47.62);

        own("scene.sc-q26");
        // ---- b26 the assumed 4x returns; strike starts on wasn't
        tl.fromTo("#q26-st", { opacity: 1, scaleX: 0 }, { opacity: 1, scaleX: 1, duration: 0.2, ease: "power2.out", immediateRender: false }, A(51.78));

        own("scene.sc-q27");
        // ---- b27 move into the Ultra card on Ultra; original punch-in stays
        tl.fromTo("#q27-pl-p", { x: 0, y: 0, scale: 1, transformOrigin: "0 0" }, { x: -1487.916, y: -354.641, scale: 2.697023, duration: 0.45, ease: "power3.inOut", immediateRender: false }, A(52.74));
        tl.set("#face", { scale: 1.08, transformOrigin: "50% 8%" }, A(52.383));
        tl.to("#face", { scale: 1, duration: 0.16, ease: "power2.out" }, 53.3);
        tl.set("#face", { scale: 1 }, A(53.467));

        own("scene.sc-q28");
        // ---- b28 early pricing rows, aligned with the untouched b29 rows

        own("scene.sc-close");
        // ---- b29 two real rows, tags lit, nothing exits before the final frame
        tl.fromTo("#cl-g", { scale: 1, transformOrigin: "50% 50%" }, { scale: 1.00823, duration: 1.583, ease: "none", immediateRender: false }, A(56.067));
        drawRect("#cl-o0", 56.82, 0.3);
        drawRect("#cl-o1", 56.82, 0.3);

        // @BLOCKS

        own(null);

        // ---------- HUD: power strip, one socket per seat row in owners.py, plugs seated, hard clay rings. No rows, no strip ----------
        if (HUD.length) {
          const at = (link) => HUD.find((r) => r[0] === link)[1];
          const SEAT = HUD.filter((r) => r[0].startsWith("seat")).map((r) => r[1]);
          const SX = SEAT.map((_, i) => 262 + 120 * i); // socket centres, strip-local
          const socks = $("#socks"), ringsHost = $("#rings"), plugsHost = $("#plugs");
          const plugs = [], rings = [], plugd = [];
          SX.forEach((cx, i) => {
            const s = el("div", "sock", socks, `left:${cx - 47}px`);
            el("div", "slot a", s); el("div", "slot b", s); el("div", "gnd", s);
            plugd.push(el("div", "plugd", socks, `left:${cx - 47}px`));
            rings.push(el("div", "ring", ringsHost, `left:${cx - 55}px`));
            plugs.push(el("div", "plug", plugsHost, `left:${cx - 36}px`, `<div class="neck"></div><div class="body"></div><div class="tile">${use(PLUGS[i][0], PLUGS[i][1])}</div>`));
          });
          show("#strip", at("strip"));
          tl.fromTo("#strip-pop", { scale: 0.9, transformOrigin: "50% 50%" }, { scale: 1, duration: 0.4, ease: "back.out(1.7)", immediateRender: false }, A(at("strip")));
          const CP = [[0, 1.5], [1, 1.3], [2, 1.3], [3, 1.15], [4, 1.07], [5, 1.0]];
          SEAT.forEach((t, i) => {
            show(plugd[i], t);
            slotPop(plugs[i], t);
            tl.set("#cn" + i, { display: "none" }, A(t));
            tl.set("#cn" + (i + 1), { display: "inline-block", scale: CP[0][1], transformOrigin: "50% 55%" }, A(t));
            for (let k = 1; k < CP.length; k++) tl.to("#cn" + (i + 1), { scale: CP[k][1], duration: 1 / 30, ease: "none" }, t + CP[k - 1][0] / 30);
            if (i < SEAT.length - 1) tl.set("#cn" + (i + 1), { display: "none" }, A(SEAT[i + 1]));
          });
          const last = SEAT.length;
          if (last) {
            tl.set("#cn" + last, { color: "#d97757" }, A(SEAT[last - 1]));
            show("#dot-on", SEAT[last - 1]);
          }
          const ring = (r, t) => { tl.set(r, { opacity: 1 }, A(t)); tl.to(r, { opacity: 0, duration: 0.2, ease: "power1.in" }, t + 0.5); };
          HUD.forEach(([name, t]) => { if (/^ring\d$/.test(name)) ring(rings[Number(name[4])], t); });
        }

        // ---------- captions: hard swap, height from the build ----------
        const caps = $("#caps");
        CAPS.forEach(([a, b, html, y, id]) => {
          const c = el("div", "chip", caps, `top:${y}px`);
          c.setAttribute("data-own", id);
          el("div", "in", c, "", html);
          if (a === 0) tl.set(c, { opacity: 1, immediateRender: true }, 0); else tl.set(c, { opacity: 1 }, A(a));
          if (b < END - 0.01) tl.set(c, { opacity: 0 }, A(b));
        });

        tl.set("#root", { opacity: 1 }, END - 0.001); // the timeline runs the full length
        own(null);
        window.__timelines = window.__timelines || {};
        window.__timelines["main"] = tl;
      })();
