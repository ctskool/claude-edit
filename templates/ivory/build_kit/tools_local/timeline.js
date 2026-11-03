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
