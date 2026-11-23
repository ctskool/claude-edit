        // ---- collage look (templates/ivory/build_kit/looks/collage/LOOK.md). build.py puts this last in the timeline's function, so END, RUNS, WINDOWS, tl, $, el and A are the shell's.
        // Chase's motion rules, 2026-11-16: graphics step at 12 fps and his footage stays smooth; the paper jitters, full on a title card and a third on a half-screen scene;
        // a scene is laid down piece by piece only when the layout changes between half screen and full screen; any other change is a hard cut; frame 0 is composed.
        {
          const CUTS = ["crt", "brush", "magnifier", "pointer", "camera", "megaphone"]; // assets/vox/cut/<name>.png, and a rule each in look.css
          const SEATS = ["cut-top", "cut-hero"];
          const SCRAPS = ["cq-teal", "cq-red", "cq-blue"], CLIPS = ["cq-n1", "cq-n2", "cq-n3"];
          const STEP = 12, BOIL = 6, LAND = 5 / 12; // the cut-out lands on the entrance's fifth step
          // the paper textures stay decoded for the whole render: a texture dropped from the decode cache left one step with blank white sheets
          const keep = ["whitepaper", "yellowpaper", "darkpaper", "greypaper", "scrap-teal", "scrap-red", "scrap-blue", "scrap-yellow", "scrap-yellow-sq", "clip-1", "clip-2", "clip-3", "clip-wide"];
          const hash = (i, k) => { const v = Math.sin(i * 127.1 + k * 311.7) * 43758.5453; return (v - Math.floor(v)) * 2 - 1; };
          const piece = (scene, cls, rot) => {
            const box = el("div", "cq-piece " + cls, scene, "--rot:" + rot + "deg");
            box.setAttribute("data-layout-allow-overflow", "true");
            return el("i", "", box);
          };

          // ---- dressing, by rule. Scenes in the order they first play: the scrap's colour and the clipping cycle through three; on a half-screen scene the scrap is lower left and
          // the clipping upper right; full-screen title cards swap sides from one to the next. A cut-out only where the scene's root names one: class="scene cut-crt"
          const order = [];
          WINDOWS.forEach(([sel]) => { if (!order.includes(sel)) order.push(sel); });
          const parts = {};
          let fulls = 0;
          order.forEach((sel, n) => {
            const scene = $(sel), full = scene.classList.contains("full");
            const flip = full && fulls++ % 2 === 1; // every second title card: clipping upper left, scrap on the right
            const p = (parts[sel] = { full });
            p.clip = piece(scene, "cq-clip " + CLIPS[(n + Math.floor(n / 3)) % 3] + (flip ? " cq-l" : ""), (flip ? -1 : 1) * (11 + (n * 2) % 5));
            p.scrap = piece(scene, "cq-scrap " + SCRAPS[n % 3] + (flip ? " cq-r" : ""), (flip ? 1 : -1) * (7 + n % 3));
            const named = [...scene.classList].filter((c) => c.startsWith("cut-") && !SEATS.includes(c)).map((c) => c.slice(4));
            if (named.length > 1 || (named.length && !CUTS.includes(named[0]))) throw new Error("collage look: " + sel + " names cut-out " + named.join(" and ") + ". One of: " + CUTS.join(", "));
            if (named.length) { p.cut = piece(scene, "cq-cut " + named[0], [9, -12, 10, -14, 8][n % 5]); keep.push("cut/" + named[0]); }
          });
          window.__cqKeep = keep.map((n) => {
            const im = new Image(); im.decoding = "sync"; im.src = "assets/vox/" + n + ".png"; im.style.cssText = "position:absolute;left:-9999px;top:0;width:8px;height:8px";
            im.setAttribute("data-layout-allow-overflow", "true"); $("#root").appendChild(im); return im;
          });

          // ---- entrances: only on a window that opens on a layout switch (RUNS, from the plan's beats). A scene's second window, or a new scene inside one layout run, is a hard cut.
          // Everything starts on the scene's own first frame, A(t0), and a later piece holds its start pose inside its ease: a tween that started late would show its piece at rest first
          const switches = RUNS.slice(1).map((r) => r[0]);
          const has = (sel, q) => !!$(sel).querySelector(q);
          const held = (h, name) => { const e = gsap.parseEase(name); return (v) => (v <= h ? 0 : e((v - h) / (1 - h))); }; // stays on its start pose for the first h of the tween
          WINDOWS.forEach(([sel, t0], n) => {
            const p = parts[sel], t = A(t0);
            if (t0 < 0.01) { // the first frame of the video is the finished layout; only the cut-out lands, a beat later
              if (p.cut) { tl.set(p.cut, { opacity: 0, immediateRender: true }, 0); tl.set(p.cut, { opacity: 1 }, 0.3); tl.fromTo(p.cut, { scale: 1.5, rotation: -14 }, { scale: 1, rotation: 0, duration: 0.24, ease: "power3.out", immediateRender: false, data: "cq-hold" }, 0.3); }
              return;
            }
            if (!switches.some((s) => Math.abs(s - t0) < 0.02)) { if (p.cut) tl.set(p.cut, { opacity: 1 }, t); return; }
            const side = n % 2 ? -1 : 1;
            tl.fromTo(p.clip, { x: 420, y: -320, rotation: 16 }, { x: 0, y: 0, rotation: 0, duration: 0.4, ease: "power3.out", immediateRender: false, data: "cq-hold" }, t);
            tl.fromTo(p.scrap, { x: -560 * side, y: 180, rotation: -14 * side }, { x: 0, y: 0, rotation: 0, duration: 0.46, ease: "power3.out", immediateRender: false, data: "cq-hold" }, t);
            if (has(sel, ".pc")) tl.fromTo(sel + " .pc", { rotation: -7 * side, y: -110 }, { rotation: 0, y: 0, duration: 0.41, ease: held(0.05 / 0.41, "back.out(1.5)"), immediateRender: false, data: "cq-hold" }, t);
            // look.css tilts the number scrap -4deg; GSAP takes that over when it tweens the element, so the tween ends on the same -4
            if (has(sel, ".cq-num")) tl.fromTo(sel + " .cq-num", { scale: 1.7, rotation: 7, transformOrigin: "50% 50%" }, { scale: 1, rotation: -4, duration: 0.24, ease: held(0.02 / 0.24, "power3.out"), immediateRender: false, data: "cq-hold" }, t);
            if (has(sel, ".cq-title")) tl.fromTo(sel + " .cq-title", { x: -760 * side }, { x: 0, duration: 0.5, ease: held(0.4, "power3.out"), immediateRender: false, data: "cq-hold" }, t);
            if (p.cut) {
              tl.set(p.cut, { opacity: 0 }, t);
              tl.set(p.cut, { opacity: 1 }, t + LAND);
              tl.fromTo(p.cut, { scale: 1.55, rotation: -16 * side }, { scale: 1, rotation: 0, duration: 0.24, ease: "power3.out", immediateRender: false, data: "cq-hold" }, t + LAND);
            }
          });

          // ---- 12 fps: every tween on the graphics, the kit's and the scenes' included, moves 12 times a second, counted from its own start, and ends on its own last frame.
          // Hard switches (show, hide, a caption swap) keep their exact frame, so words still land where the plan put them. His footage is not on this timeline and stays smooth.
          // Why from its own start and not one grid for the whole video: a cut on its exact frame followed one or two frames later by the first step of whatever
          // arrives with it reads as a double cut (output check O4 failed nine of them). This way the first step after any cut is three frames on.
          // A tween shows half a step of progress on its first frame, so a line that is revealed by a tween is readable on its word's frame (conform.py allows 2 frames).
          // The look's own entrance pieces hold their start pose for the first step instead (data: "cq-hold"), as the approved mock did
          tl.getChildren(true, true, false).forEach((tw) => {
            const d = tw.duration();
            if (!d) return;
            const base = gsap.parseEase(tw.vars.ease || (tw.vars.keyframes ? "none" : "power1.out")); // power1.out is GSAP's own default, which the kit never changes
            const lead = tw.vars.data === "cq-hold" ? 0 : 0.5;
            const stepped = (v) => {
              if (v >= 1) return base(1);
              const q = (Math.floor(v * d * STEP + 1e-6) + lead) / (d * STEP);
              return base(q < 1 ? q : 1);
            };
            tw.vars.ease = stepped;
            if (tw._ease) tw._ease = stepped; // one that already rendered (an immediateRender at 0) has read its ease
          });

          // ---- jitter: every piece shifts a hair six times a second, as if re-placed by hand between shots. Custom properties, so GSAP's transforms stay free; look.css scales them by --amp.
          // One tween per property whose ease is the hash itself: HyperFrames and the checks walk every tween at load, and one set() per shift (2,400 of them) stalled the page.
          // They are written on the pieces themselves, never on a scene's root: a property changed there restyles the whole scene, and every tween that first reads its
          // start values in the same pass pays for that (a seek to the end took minutes). Do not "warm" the timeline by running it to END and back instead: a rewind
          // loses the transform origin the kit's cutIn sets, and a card then sits 10 px off depending on how a frame was reached.
          // The six-a-second count restarts at every scene cut, so the first shift after a cut is five frames on and never reads as a second cut
          const cuts = [...new Set(WINDOWS.map((w) => Math.ceil(A(w[1]) * FPS - 1e-6) / FPS))].sort((a, b) => a - b); // each window's first frame, as show() lands it
          const since = (t) => { let c = 0; for (const x of cuts) { if (x <= t + 1e-6) c = x; else break; } return c; };
          [".pc", ".cq-num", "#strip-body", ".chip .in", ".cq-piece"].forEach((sel, k) => {
            if (!document.querySelector(sel)) return;
            const boil = (salt) => (v) => { const t = v * END, c = since(t), i = Math.floor((t - c) * BOIL + 1e-6); return t < 1 / BOIL ? 0 : hash(Math.round(c * 30) + i, k + salt); }; // nothing has moved on the first sixth of a second
            tl.fromTo(sel, { "--br": "0deg" }, { "--br": "0.42deg", duration: END, ease: boil(0), immediateRender: false }, 0);
            tl.fromTo(sel, { "--bx": "0px" }, { "--bx": "1.8px", duration: END, ease: boil(9), immediateRender: false }, 0);
            tl.fromTo(sel, { "--by": "0px" }, { "--by": "1.6px", duration: END, ease: boil(17), immediateRender: false }, 0);
          });
        }
