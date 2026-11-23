"""The rea-video short in the sky look: the approved pixel-guide test (work/1119-pixel-guide-test), Chase's picks
2026-11-19 (sky with cloud titles, Jersey 15). Ported to HyperFrames 2026-11-20. Copy this file to start a new sky short.
  python templates/ivory/build_kit/looks/sky/examples/rea.py check | stills 3.9 18.8 | render 4k"""
import json, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from sky import blk, peek, frames, count, main  # noqa: E402
from sprites import CLIP, PART_C, PART_A, BOOK, KEYS  # noqa: E402

REPO = HERE.parents[5]
REA = REPO / "work/1118-rea"
NAME = "rea-sky"
OUT = REPO / "work/1119-pixel-guide-test/sky-hf"
IMG = REPO / "work/1119-pixel-guide-test/img"         # his real captures and the case video frames (local only)
WORDS = REA / "words.json"
FACE, FACE4K, VOICE = REA / "assets/face_half.mp4", REA / "assets/face_half_4k.mp4", REA / "assets/voice.m4a"
END = 49.2
BEATS = [0, 4.633, 7.6, 10.5, 12.867, 17.5, 19.6, 23.9, 30.367, 32.867, 36.4, 38.967, 41.1, 45.467]   # his cut's beat starts (the scene() times below): the player's beats
H1_TOP = 66            # as the rea test was approved; a new short leaves this out (titles start at 150, clear of the island)
NPV, NP2, NJ = count(IMG, "pv"), count(IMG, "pv2"), 131

POSES = ["idle", "walk", "point", "pointl", "up", "jump", "blink", "crouch", "lookr", "lookl", "lookur",
         "bladeup", "chop", "hold", "hamup", "hamdn", "pointup", "pointdn", "typea", "typeb", "run"]
POSES2 = ["idle", "up", "jump", "blink", "lookl", "crouch"]     # his copy under the remake (b13)

# caption chunks (word index ranges) for the first 55 words; the rest are set automatically
CHUNKS = [(0, 2), (3, 4), (5, 7), (8, 9), (10, 12), (13, 15), (16, 18), (19, 22), (23, 24), (25, 28), (29, 31), (32, 34),
          (35, 37), (38, 41), (42, 44), (45, 47), (48, 50), (51, 54)]

# few sounds, on what he does: vetted slices at the house levels (set against his voice by bp.mix)
SOUNDS = [
    (1.20, "es-swish-blade", "detail", "his first cut through the timeline (the next two are silent)"),
    (11.52, "es-knock-plastic", "detail", "he catches the video he is handed"),
    (13.12, "es-knock-wood", "main", "the hammer breaks the video block in two"),
    (18.80, "es-knock-snap", "main", "his ground-pound cracks the video into three"),
    (31.28, "es-swish-flick", "detail", "he starts flipping the ten shots as he runs (one sound for the run)"),
    (43.14, "es-pop-1", "detail", "his copy pops in under the remake on 'mimic'"),
]

TYPED = "break down this video: dual_role.mp4"
# real text from the case reports (shared/src/docs_cases_*_report_en.md)
PROMPT2 = ("Medium shot, slightly high angle, the young woman sits left of center. Having just looked at her phone, she looks up "
           "toward frame right, eyebrows raised and mouth open, and asks in surprise \"就被判九成扑街？\"; the phone in her hand moves "
           "slightly; ends on her surprised face. Locked-off camera.")
REMAKE7 = "Code render: rebuild in Remotion / HTML from the text tracks and layout, 100% controllable, no generative model needed"

CSS = """
#sC::before{content:'';position:absolute;left:-34px;top:0;width:34px;height:100%;background:#0d0c0b;border-right:2px solid #423f3b}
#sR .pc{display:inline-block}
#pt,#ct{white-space:pre-wrap}
#sf{color:#1d2b53 !important} #caret{background:#1d2b53 !important}
#s6 .chip{background:#1d2b53 !important;color:#fff !important;border-color:#1d2b53 !important;top:34px !important;left:46px !important}
#s6 h1{top:104px !important}
#s14 > div:nth-last-child(5){font-family:'Jersey 15' !important;color:#fff !important;text-shadow:0 5px #1d2b53;font-size:72px !important}
#s14 > div:nth-last-child(4){font-family:'Jersey 15' !important;font-weight:400 !important;font-size:140px !important;color:#1d2b53 !important;background:#fff;
  border-bottom:14px solid #cfe3ff;left:50% !important;right:auto !important;transform:translateX(-50%);padding:26px 52px 16px;top:316px !important;white-space:nowrap;clip-path:__STEP__}
#s14 span{color:#e8531e !important} #dsc{color:#1d2b53 !important;top:560px !important}
"""

SCENES = f"""
<!-- b01 HOOK -->
<div class="scn" id="sH">
 <h1>Reverse-engineer<br>any <span>viral video.</span></h1>
 <div class="cd" id="ph" style="left:60px;top:262px;width:248px;height:441px;border-width:3px">
  {frames('pv', 'pv', NPV, 'img/pv')}</div>
 <div class="cd" id="pr" style="left:340px;top:262px;width:680px;height:441px;padding:34px 38px;font:700 30px/1.6 'JetBrains Mono'">
  <span style="color:#5b6890">&gt;</span> break down this video<br>&nbsp; <span style="color:#ff6a3d">dual_role.mp4</span>
  <div style="position:absolute;left:38px;bottom:30px;color:#5b6890;font-size:28px">shots found</div>
  <div id="sf" style="position:absolute;right:44px;bottom:-6px;font:800 220px/1 'Hanken Grotesk';color:#1d2b53;letter-spacing:-.04em">1</div></div>
 {''.join(f'<div class="cd tile" id="t{i}" style="left:{60+i*240}px;top:840px;width:240px;height:80px;border-width:2px"><img src="img/dr_{sh}.jpg" style="width:100%;height:100%;object-fit:cover;display:block"></div>' for i, sh in enumerate(['0.7', '2.1', '3.3', '4.8']))}
 {''.join(f'<div class="cut" id="cut{k}" style="position:absolute;left:{300+240*k-6}px;top:830px;width:12px;height:100px;background:#ff6a3d;box-shadow:0 0 0 3px #1a1917;transform-origin:50% 0;z-index:3"></div>' for k in range(3))}
 {''.join(f'<div class="chip vd" id="v{i}" style="left:{70 + i*240}px;top:690px;opacity:0;{st}">{t}</div>' for i, (t, st) in enumerate([('#1 CODE', 'background:#ebe8e0;color:#1a1917'), ('#2 AI', 'background:#ff6a3d;color:#1a1917'), ('#3 AI', 'background:#ff6a3d;color:#1a1917'), ('#4 CODE', 'background:#ebe8e0;color:#1a1917')]))}
 <div class="floor"></div>
</div>

<!-- b02 NAME -->
<div class="scn" id="sN" style="visibility:hidden">
 <div style="position:absolute;left:730px;top:255px;width:210px;height:75px;overflow:hidden;z-index:1"><div id="pk" style="position:absolute;left:0;top:75px">{peek()}</div></div>
 <div class="cd" id="nm" style="left:100px;top:330px;width:880px;height:360px;padding:70px 64px;z-index:2">
  <div style="display:flex;align-items:center;gap:30px"><div style="width:96px;height:96px;background:#ff6a3d"></div>
  <div style="font:800 136px/1 'Hanken Grotesk';letter-spacing:-.04em">rea-video</div></div>
  <div class="mono" style="margin-top:40px;font-size:29px;color:#5b6890">reverse-engineer any video, shot by shot</div></div>
 <div class="chip" id="os" style="left:100px;top:740px;border:3px solid #ff6a3d;color:#ff6a3d;font-size:32px;padding:10px 20px;opacity:0">OPEN SOURCE · APACHE-2.0</div>
 <div class="floor"></div>
</div>

<!-- b03 STARS -->
<div class="scn" id="sS" style="visibility:hidden">
 <h1 id="h3a" style="opacity:0"><span>10,000</span> stars</h1>
 <h1 id="h3b" style="top:146px;opacity:0">in under three weeks.</h1>
 <div class="cd" id="ghc" style="left:60px;top:300px;width:960px;height:500px;background:#fff url(img/gh.jpg) -950px -208px/1900px 1484px no-repeat;transform-origin:860px 90px"></div>
 <div id="seamS" style="position:absolute;left:1058px;top:0;width:22px;height:998px;background:#ff6a3d;opacity:0;z-index:6"></div>
 <div id="hl" style="position:absolute;left:800px;top:356px;width:182px;height:72px;border:7px solid #ff6a3d;opacity:0;z-index:4"></div>
 <div class="floor"></div>
</div>

<!-- b04 HAND CLAUDE -->
<div class="scn" id="sC" style="visibility:hidden">
 <h1>Hand <span>Claude</span><br>a video.</h1>
 <div class="cd" style="left:60px;top:300px;width:960px;height:400px;padding:34px 40px;font:700 30px/1.6 'JetBrains Mono'">
  <div style="color:#ff6a3d">✻ Claude Code</div>
  <div style="margin-top:26px"><span style="color:#5b6890">&gt;</span> <span id="typed"></span><span id="caret" style="display:inline-block;width:16px;height:34px;background:#ebe8e0;vertical-align:-6px"></span></div>
  <div id="vchip" style="margin-top:34px;display:flex;align-items:center;gap:22px;opacity:0">
   <img id="vimg" src="img/dr_held.png" style="width:96px;height:170px;object-fit:cover;border:2px solid #423f3b">
   <div style="font-size:28px">dual_role.mp4<br><span style="color:#5b6890">19 s · 10 shots</span></div></div></div>
 <div id="clipC" style="position:absolute;left:0;top:0;width:108px;height:60px;z-index:29;opacity:0">{blk(CLIP)}</div>
 <div class="floor"></div>
</div>

<!-- b05 BREAKDOWN -->
<div class="scn" id="sR" style="visibility:hidden">
 <h1>Exactly how it<br>was <span>made.</span></h1>
 <div class="cd" style="left:60px;top:290px;width:960px;height:480px;padding:36px 44px">
  <div class="mono" style="font-size:26px;color:#5b6890">report · dual_role.mp4</div>
  <div style="margin-top:44px;font:700 54px/1.45 'Hanken Grotesk'"><div>code / template <span class="pc" style="color:#ff6a3d;opacity:0">59%</span></div><div>AI-generated video <span class="pc" style="color:#ff6a3d;opacity:0">41%</span></div></div>
  <div style="position:absolute;left:44px;right:44px;top:370px;height:64px;border:3px solid #423f3b;padding:6px"><div id="bar" style="display:flex;gap:6px;height:100%">
   <div id="bc" style="width:59%;height:100%;background:#ebe8e0;opacity:0"></div>
   <div id="ba" style="width:41%;height:100%;background:#ff6a3d;opacity:0"></div></div></div></div>
 <div id="clipR" style="position:absolute;left:343px;top:890px;width:108px;height:60px;z-index:8;transform-origin:50% 100%">{blk(CLIP)}</div>
 <div id="pc1" class="part" style="position:absolute;left:343px;top:890px;width:72px;height:60px;z-index:8;opacity:0">{blk(PART_C)}</div>
 <div id="pc2" class="part" style="position:absolute;left:403px;top:890px;width:48px;height:60px;z-index:8;opacity:0">{blk(PART_A)}</div>
 <div class="chip" id="yv" style="left:372px;top:884px;background:#ff6a3d;color:#1a1917;font-size:30px;opacity:0;transform-origin:0 100%">→ REMAKE YOUR OWN VERSION</div>
 <div class="floor"></div>
</div>

<!-- b06 HOW IT WORKS -->
<div class="scn" id="s6" style="visibility:hidden">
 <div class="chip" style="left:62px;top:70px;border:3px solid #ff6a3d;color:#ff6a3d;font-size:30px;padding:8px 18px">HOW IT WORKS</div>
 <h1 style="top:140px">It breaks a video.</h1>
 <div id="ph6" class="cd" style="left:560px;top:330px;width:300px;height:533px;border-width:3px">
  {''.join(f'<img class="p6" id="p6_{i}" src="img/pv2/{i+1:03d}.jpg" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:{'block' if i == 0 else 'none'}">' for i in range(NP2))}</div>
 {''.join(f'<div class="slab" id="sl{k}" style="position:absolute;left:560px;top:{330+k*177.67:.2f}px;width:300px;height:177.67px;overflow:hidden;border:3px solid #423f3b;opacity:0"><img src="img/pv2/039.jpg" style="position:absolute;left:-3px;top:{-3-k*177.67:.2f}px;width:300px;height:533px;object-fit:cover"></div>' for k in range(3))}
 <div class="floor"></div>
</div>

<!-- b07 LAYERS -->
<div class="scn" id="s7" style="visibility:hidden">
 <h1>Into all its<br><span>component pieces.</span></h1>
 <div class="lane" id="ln0" style="top:300px"><div class="lb">SOUND</div><div style="position:absolute;left:250px;right:24px;top:62px;height:40px;background:url(img/audio_en.png) -52px -12px/1060px 154px no-repeat"></div></div>
 <div class="lane" id="ln1" style="top:500px"><div class="lb">VOICE</div><div style="position:absolute;left:250px;right:24px;top:72px;height:18px;background:url(img/audio_en.png) -52px -48px/1060px 154px no-repeat"></div></div>
 <div class="lane" id="ln2" style="top:700px"><div class="lb">MOTION<br>GRAPHICS</div><div style="position:absolute;left:250px;right:24px;top:18px;bottom:18px;background:url(img/v10row.jpg) 0 0/auto 100% repeat-x"></div></div>
 <div class="floor"></div>
</div>

<!-- b08 DECIDES -->
<div class="scn" id="s8" style="visibility:hidden">
 <h1>Then it <span>decides.</span></h1>
 <div class="vc" style="left:60px;background-image:url(img/real.jpg)"></div>
 <div class="vc" style="left:395px;background-image:url(img/dr_s02.png)"></div>
 <div class="vc" style="left:730px;background-image:url(img/code7.jpg)"></div>
 <div class="chip vd8" id="vd0" style="left:60px;top:730px;background:#3a9d5d;color:#fff;opacity:0">REAL FOOTAGE</div>
 <div class="chip vd8" id="vd1" style="left:395px;top:730px;background:#c94fd6;color:#fff;opacity:0">AI</div>
 <div class="chip vd8" id="vd2" style="left:730px;top:730px;background:#ff6a3d;color:#1a1917;opacity:0">CODE</div>
 <div class="floor"></div>
</div>

<!-- b09 EVERY SINGLE PART -->
<div class="scn" id="s9" style="visibility:hidden">
 <h1 id="h9" style="top:60px;font-size:86px;opacity:0"><span class="serif">every single</span> part.</h1>
 {''.join(f'<div class="tl10" id="q{i}" style="left:{60 + (i % 5) * 197.5:.1f}px;top:{200 + (i // 5) * 305}px;background-image:url(img/dr_s{i+1:02d}.png)"><div class="bd" style="background:{"#c94fd6;color:#fff" if v == "AI" else "#ff6a3d"}">#{i+1} {v} {p}%</div></div>' for i, (v, p) in enumerate([("CODE",77),("AI",85),("AI",68),("CODE",79),("AI",88),("CODE",79),("AI",85),("CODE",77),("AI",88),("CODE",73)]))}
 <div class="floor"></div>
</div>

<!-- b10 AI PROMPT -->
<div class="scn" id="s10" style="visibility:hidden">
 <h1>If it's AI:<br>a <span>prompt.</span></h1>
 <div class="cd" style="left:60px;top:300px;width:300px;height:533px;background:url(img/dr_s02.png) center/cover"></div>
 <div class="chip" style="left:76px;top:316px;background:#c94fd6;color:#fff">AI VIDEO</div>
 <div class="cd" style="left:390px;top:300px;width:630px;height:533px;padding:32px 34px">
  <div class="mono" style="font-size:24px;color:#ff6a3d">PROMPT · SHOT 2</div>
  <div class="mono" id="pt" style="margin-top:22px;font-size:27px;line-height:1.5;font-weight:500;color:#1d2b53"></div></div>
 <div class="floor"></div>
</div>

<!-- b11 CODE -->
<div class="scn" id="s11" style="visibility:hidden">
 <h1>If it's code:<br>the <span>actual code.</span></h1>
 <div class="cd" style="left:60px;top:300px;width:960px;height:340px;background:url(img/code7.jpg) center/cover"></div>
 <div class="chip" style="left:76px;top:316px;background:#ff6a3d;color:#1a1917">CODE RENDER</div>
 <div class="cd" style="left:60px;top:660px;width:960px;height:150px;padding:20px 28px">
  <div class="mono" style="font-size:22px;color:#ff6a3d">REMAKE · SHOT 7</div>
  <div class="mono" id="ct" style="margin-top:10px;font-size:26px;line-height:1.45;font-weight:500"></div></div>
 <div class="floor"></div>
</div>

<!-- b12 RECIPE -->
<div class="scn" id="s12" style="visibility:hidden">
 <h1 id="h12" style="opacity:0">What you get: <span class="serif" style="color:#ff6a3d">a recipe.</span></h1>
 <div class="cd" id="sb" style="left:60px;top:190px;width:960px;height:657px;background:#fff url(img/storyboard.jpg) center/contain no-repeat"></div>
 <div class="floor"></div>
</div>

<!-- b13 MIMIC -->
<div class="scn" id="s13" style="visibility:hidden">
 <h1 style="top:60px">Edit it. <span>Mimic the style.</span></h1>
 <div class="cd" style="left:120px;top:230px;width:348px;height:570px">{''.join(f'<img class="jo" id="jo{i}" src="img/jo/{i+1:03d}.jpg" style="position:absolute;inset:0;display:{'block' if i == 0 else 'none'}">' for i in range(NJ))}</div>
 <div class="cd" style="left:612px;top:230px;width:348px;height:570px">{''.join(f'<img class="jr" id="jr{i}" src="img/jr/{i+1:03d}.jpg" style="position:absolute;inset:0;display:{'block' if i == 0 else 'none'}">' for i in range(NJ))}</div>
 <div class="chip" style="left:136px;top:246px;background:#ebe8e0;color:#1a1917">ORIGINAL</div>
 <div class="chip" id="rmk" style="left:628px;top:246px;background:#423f3b;color:#5b6890">REMAKE</div>
 <div class="floor"></div>
</div>

<!-- b14 CTA -->
<div class="scn" id="s14" style="visibility:hidden">
 <div style="position:absolute;left:0;right:0;top:230px;text-align:center;font:700 64px/1.1 'Hanken Grotesk';color:#5b6890">get the</div>
 <div style="position:absolute;left:0;right:0;top:310px;text-align:center;font:800 118px/1 'Hanken Grotesk';color:#ebe8e0;letter-spacing:-.04em">setup <span style="color:#ff6a3d">guide</span></div>
 <div id="dsc" style="position:absolute;left:0;right:0;top:500px;text-align:center;font:700 40px 'JetBrains Mono';color:#ebe8e0;opacity:0">check the description ↓</div>
 <div id="book" style="position:absolute;left:0;top:0;width:120px;height:84px;z-index:29;opacity:0">{blk(BOOK)}</div>
 <div class="floor"></div>
</div>
"""

STAGE = f'<div id="keys" style="position:absolute;left:640px;top:890px;width:168px;height:60px;z-index:31;visibility:hidden">{blk(KEYS)}</div>'

JS = f"""const TYPED = {json.dumps(TYPED)};
const PROMPT2 = {json.dumps(PROMPT2, ensure_ascii=False)};
const REMAKE7 = {json.dumps(REMAKE7)};
// start states the CSS used to hold (HyperFrames: GSAP owns these transforms)
tl.set('.cut', {{scaleY:0}}, 0); tl.set('.tl10 .bd', {{scaleY:0}}, 0);

// ── b01 HOOK (0 - 4.633) · ACT: "reverse engineers any viral video ... shot by shot". The case video plays,
//    its timeline sits on the floor as four clips. He walks the timeline, draws a blade on "reverse" and cuts it
//    at each shot change (engineers / any / video); the counter ticks. On "shot" the four clips fly up into the
//    shot tiles and the floor he stood on is gone: he drops to the real floor. ──
scene(0, '#sH');
for (let i = 1; i < {NPV}; i++) {{ const t = i / 30; if (t > 3.52) break;
  tl.set('#pv' + (i - 1), {{display:'none'}}, t); tl.set('#pv' + i, {{display:'block'}}, t); }}
const TOP = 840;                                         // the timeline's top edge: his first floor
tl.set('#g', {{x:-90, y:TOP}}, 0);
walk(0, 0.6); moveX(0, 0.6, 68, 8);
pose(0.6, 'lookr');
pose(0.86, 'bladeup');                                   // draws the blade on "reverse"
function chop(t, k, gx) {{
  pose(t - 0.08, 'bladeup');
  pose(t, 'chop');
  tl.to('#cut' + k, {{scaleY:1, duration:0.06, ease:S(3)}}, t);
  tl.set('#sf', {{textContent:String(k + 2)}}, t);
  tl.fromTo('#sf', {{scale:1.12}}, {{scale:1, duration:0.12, ease:S(3)}}, t);
  pose(t + 0.16, 'bladeup');
}}
chop(1.20, 0, 68);                                        // "engineers"
walk(1.40, 1.66); moveX(1.40, 0.26, 308, 4); pose(1.66, 'bladeup');
chop(1.76, 1, 308);                                       // "any"
walk(1.96, 2.30); moveX(1.96, 0.34, 548, 5); pose(2.30, 'bladeup');
chop(2.40, 2, 548);                                       // "video"
pose(2.62, 'idle'); blink(3.0); pose(3.2, 'lookl');
// "shot" 3.52: the clips rise out from under him and open into the four shots
tl.to('#pr', {{x:1100, duration:0.18, ease:'power3.in'}}, 3.34);
tl.to('#ph', {{x:-420, duration:0.18, ease:'power3.in'}}, 3.34);
tl.set('.cut', {{opacity:0}}, 3.52);
[0,1,2,3].forEach(i => {{
  tl.to('#t' + i, {{x:10, y:-540, width:210, height:374, rotation:[-2,1,-1,2][i], duration:0.32, ease:'power3.out'}}, 3.52 + i*0.04);   // left 70+i*240, top 300
  tl.fromTo('#v' + i, {{opacity:0, y:12}}, {{opacity:1, y:0, duration:0.1, ease:S(3)}}, 3.84 + i*0.08);
}});
pose(3.56, 'jump'); tl.to('#g', {{y:FL, duration:0.16, ease:S(4)}}, 3.6);
pose(3.76, 'crouch'); puffs(3.76, [[560,920],[760,920]]); pose(3.84, 'idle'); pose(4.1, 'lookl');

// ── JOIN 1 · hard cut on "It's called" ──
scene(4.633, '#sN'); tl.set('#g', {{x:-400}}, 4.633);

// ── b02 NAME (4.633 - 7.6) · STEP BACK: the name leads. Halfway through he pokes his head up over the card's
//    top edge, looks at the name, blinks, and ducks back down before the OPEN SOURCE chip ──
function ppose(t, q) {{ tl.set('#pk .pp', {{display:'none'}}, t); tl.set('#pk-' + q, {{display:'block'}}, t); }}
tl.to('#pk', {{y:-62, duration:0.12, ease:S(3)}}, 5.5);
ppose(5.75, 'lookl'); ppose(6.1, 'blink'); ppose(6.2, 'lookl');
tl.to('#pk', {{y:0, duration:0.1, ease:S(3)}}, 6.62);
ppose(6.75, 'idle');
tl.fromTo('#os', {{opacity:0, x:-30}}, {{opacity:1, x:0, duration:0.2, ease:'power3.out'}}, 6.96);

// ── JOIN 2 · hard cut on "it has over 10,000" ──
scene(7.6, '#sS');
tl.fromTo('#h3a', {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.25, ease:'power3.out'}}, 7.66);
tl.fromTo('#hl', {{opacity:0, scale:1.4}}, {{opacity:1, scale:1, duration:0.12, ease:S(3)}}, 7.94);
tl.fromTo('#h3b', {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.25, ease:'power3.out'}}, 9.28);
tl.to('#ghc', {{scale:1.035, duration:2.9, ease:'none'}}, 7.6);
// b03 · STEP BACK: the real page is the proof. On "GitHub stars" he leans in from the left edge of the frame,
// eyes up at the star count, blinks, and leans back out.
tl.set('#g', {{x:-215, y:FL}}, 7.6); pose(7.6, 'lookr');
tl.to('#g', {{x:-62, duration:0.12, ease:S(3)}}, 8.3);
pose(8.5, 'lookur'); pose(9.0, 'blink'); pose(9.1, 'lookur'); pose(9.4, 'lookr');
tl.to('#g', {{x:-215, duration:0.1, ease:S(3)}}, 9.62);

// ── JOIN 3 · hard cut on "and it allows you" ──
scene(10.5, '#sC');
tl.set('#g', {{x:720, y:FL}}, 10.5); pose(10.5, 'lookl');
// b04 · ACT: "hand Claude a video". He is Claude: the video drops in, he catches it, throws it into his prompt.
const typed = {{n:0}}; const TY = 'break down this video';
tl.to(typed, {{n:TY.length, duration:0.55, ease:'none', onUpdate:() => {{ document.getElementById('typed').textContent = TY.slice(0, Math.round(typed.n)); }}}}, 10.62);
pose(11.22, 'hold');                                      // arms up on "just"
const HX = 720 + 51, HY = FL - 150 - 60;                  // where the block sits in his hands
tl.set('#clipC', {{opacity:1, x:HX, y:-80}}, 11.3);
tl.to('#clipC', {{y:HY, duration:0.22, ease:S(5)}}, 11.3);           // caught on "Claude" 11.52
tl.to(['#g'], {{y:FL + 8, duration:0.03}}, 11.52); tl.to('#g', {{y:FL, duration:0.08, ease:S(2)}}, 11.58);
tl.to('#clipC', {{y:HY + 8, duration:0.03}}, 11.52); tl.to('#clipC', {{y:HY, duration:0.08, ease:S(2)}}, 11.58);
pose(11.78, 'crouch'); tl.to('#clipC', {{y:HY + 30, duration:0.04}}, 11.78);
pose(11.86, 'up');
const VR = {{x:100 + 1.5, y:300 + 1.5 + 34 + 48 + 26 + 48 + 34}};  // the attachment's image in the prompt
tl.to('#clipC', {{x:VR.x, y:VR.y, width:96, height:170, duration:0.2, ease:S(6)}}, 11.86);
tl.set('#clipC', {{opacity:0}}, 12.06);
tl.fromTo('#vchip', {{opacity:0}}, {{opacity:1, duration:0.01}}, 12.06);           // lands on "video"
tl.fromTo('#vchip', {{y:-6}}, {{y:0, duration:0.1, ease:S(2)}}, 12.06);
pose(12.1, 'idle'); pose(12.4, 'lookl');

// ── JOIN 4 · hard cut on "and get a breakdown": it opens on his wind-up ──
scene(12.867, '#sR');
tl.set('#g', {{x:120, y:FL}}, 12.867); pose(12.867, 'hamup');
// b05 · ACT: "breakdown" — he smashes the video block and it breaks into its two parts, sized 59 / 41
pose(13.12, 'hamdn');
tl.to('#clipR', {{scaleY:0.55, duration:0.03}}, 13.12);
puffs(13.14, [[320,925],[470,925]]);
tl.set('#clipR', {{opacity:0}}, 13.2);
tl.set(['#pc1','#pc2'], {{opacity:1}}, 13.2);
tl.to('#pc1', {{x:-46, y:-40, duration:0.12, ease:S(3)}}, 13.2); tl.to('#pc1', {{y:0, duration:0.12, ease:S(3)}}, 13.32);
tl.to('#pc2', {{x:60, y:-40, duration:0.12, ease:S(3)}}, 13.2);  tl.to('#pc2', {{y:0, duration:0.12, ease:S(3)}}, 13.32);
pose(13.3, 'idle'); pose(13.5, 'lookr');
// "exactly" 14.0: the two parts fly up into the report and become its split bar
const R = (id) => {{ const r = document.getElementById(id).getBoundingClientRect(); return r; }};
const rc = R('bc'), ra = R('ba'), p1 = R('pc1'), p2 = R('pc2');
tl.to('#pc1', {{x:rc.left - p1.left, y:rc.top - p1.top, width:rc.width, height:rc.height, duration:0.24, ease:S(6)}}, 13.86);
tl.to('#pc2', {{x:ra.left - p2.left, y:ra.top - p2.top, width:ra.width, height:ra.height, duration:0.24, ease:S(6)}}, 13.9);
tl.set(['#bc','#ba'], {{opacity:1}}, 14.14); tl.set(['#pc1','#pc2'], {{opacity:0}}, 14.14);
tl.fromTo('#sR .pc', {{opacity:0, scale:1.3}}, {{opacity:1, scale:1, duration:0.1, ease:S(3)}}, 14.14);
pose(14.0, 'up'); pose(14.3, 'idle');
blink(15.3);
// "make your own version": he raises the hammer again and knocks the new card into place on "make"
pose(16.3, 'hamup');
pose(16.56, 'hamdn');
tl.fromTo('#yv', {{opacity:0, scaleY:0.3}}, {{opacity:1, scaleY:1, duration:0.1, ease:S(3)}}, 16.56);
puffs(16.58, [[350,925],[880,925]]);
pose(16.8, 'idle'); pose(17.1, 'lookr');

// ════════ second half (17.5 - 49.2) ════════

// ── b06 HOW IT WORKS (17.5 - 19.6) · ACT "breaks": he drops onto the playing video and ground-pounds it on "breaks";
//    it cracks into three slabs (the three layers of the next beat) ──
scene(17.5, '#s6'); tl.set('#g', {{x:-400}}, 17.5); tl.set('#yv', {{opacity:0}}, 17.5);
for (let i = 1; i < {NP2}; i++) {{ const t = 17.5 + i / 30; if (t >= 18.8) break;
  tl.set('#p6_' + (i - 1), {{display:'none'}}, t); tl.set('#p6_' + i, {{display:'block'}}, t); }}
tl.set('#g', {{x:605, y:-40}}, 18.3); pose(18.3, 'jump');
tl.to('#g', {{y:330, duration:0.2, ease:S(5)}}, 18.3);
pose(18.5, 'crouch'); pose(18.56, 'idle');
pose(18.6, 'jump'); tl.to('#g', {{y:240, duration:0.1, ease:S(3)}}, 18.6); tl.to('#g', {{y:330, duration:0.1, ease:S(3)}}, 18.7);
pose(18.8, 'crouch');                                           // "breaks"
tl.set('#ph6', {{opacity:0}}, 18.8); tl.set('.slab', {{opacity:1}}, 18.8);
tl.to('#sl0', {{x:-10, y:-18, rotation:-2, duration:0.08, ease:S(2)}}, 18.8);
tl.to('#sl1', {{x:14, duration:0.08, ease:S(2)}}, 18.8);
tl.to('#sl2', {{x:-6, y:18, rotation:1.5, duration:0.08, ease:S(2)}}, 18.8);
tl.to('#g', {{x:595, y:312, duration:0.08, ease:S(2)}}, 18.8);
puffs(18.82, [[570,320],[820,320]]);
pose(18.9, 'idle'); pose(19.2, 'lookl');

// ── b07 LAYERS (19.6 - 23.9) · STEP BACK: the three real layers light on their words; he sits this out ──
scene(19.6, '#s7'); tl.set('#g', {{x:-400}}, 19.6);
[[21.70,0],[22.26,1],[22.74,2]].forEach(([t,k]) => {{
  tl.fromTo('#ln' + k, {{opacity:0.28, y:8}}, {{opacity:1, y:0, duration:0.1, ease:S(3)}}, t);
  tl.set('#ln' + k + ' .lb', {{color:'#ff6a3d'}}, t); }});

// ── b08 DECIDES (23.9 - 30.367) · ACT: he is the one deciding. Looks left, right; then hops under each shot
//    and points up at it as its verdict lands on "real" / "AI" / "code" ──
scene(23.9, '#s8'); tl.set('#g', {{x:435, y:FL}}, 23.9); pose(23.9, 'idle');
pose(24.26, 'lookl'); pose(24.55, 'lookr'); pose(24.8, 'lookl');
hopTo(24.98, 100); pose(25.22, 'pointup');
tl.fromTo('#vd0', {{opacity:0, y:14}}, {{opacity:1, y:0, duration:0.1, ease:S(3)}}, 25.22);
pose(25.7, 'idle');
hopTo(26.42, 435); pose(26.66, 'pointup');
tl.fromTo('#vd1', {{opacity:0, y:14}}, {{opacity:1, y:0, duration:0.1, ease:S(3)}}, 26.66);
pose(27.1, 'idle'); pose(27.6, 'lookr');
hopTo(28.34, 770); pose(28.58, 'pointup');
tl.fromTo('#vd2', {{opacity:0, y:14}}, {{opacity:1, y:0, duration:0.1, ease:S(3)}}, 28.58);
pose(29.1, 'idle'); blink(29.6); pose(30.0, 'lookl');

// ── b09 EVERY SINGLE PART (30.367 - 32.867) · ACT: the ten shots return; he dashes along the floor and each
//    shot flips to its verdict as he passes it ──
scene(30.367, '#s9'); tl.set('#g', {{x:-230, y:FL}}, 30.367);
const R0 = 31.0, RD = 1.4, X0 = -230, X1 = 1100;
tl.to('#g', {{x:X1, duration:RD, ease:S(21)}}, R0);
for (let t = R0, k = 0; t < R0 + RD; t += 0.067, k++) pose(t, k % 2 ? 'walk' : 'run');
[0,1,2,3,4].forEach(c => {{ const cx = 60 + c * 197.5 + 85;
  const t = R0 + RD * ((cx - 105) - X0) / (X1 - X0);
  [c, c + 5].forEach(i => {{
    tl.to('#q' + i + ' .bd', {{scaleY:1, duration:0.1, ease:S(3)}}, t);
    tl.to('#q' + i, {{y:-10, duration:0.05, ease:S(1)}}, t); tl.to('#q' + i, {{y:0, duration:0.08, ease:S(2)}}, t + 0.06); }}); }});
tl.fromTo('#h9', {{opacity:0, y:24}}, {{opacity:1, y:0, duration:0.22, ease:'power3.out'}}, 31.82);

// ── b10 AI PROMPT (32.867 - 36.4) · STEP BACK: the real prompt is the proof; he is not on screen ──
scene(32.867, '#s10'); tl.set('#g', {{x:-400}}, 32.867);
typeInto('pt', PROMPT2, 34.6, 1.4);

// ── b11 CODE (36.4 - 38.967) · ACT: "it gives you the actual code" — he types it out himself ──
scene(36.4, '#s11'); tl.set('#keys', {{visibility:'visible'}}, 36.4); tl.set('#keys', {{visibility:'hidden'}}, 38.967);
tl.set('#g', {{x:619, y:FL}}, 36.4); pose(36.4, 'lookl');
for (let t = 36.9, k = 0; t < 38.5; t += 0.08, k++) pose(t, k % 2 ? 'typeb' : 'typea');
typeInto('ct', REMAKE7, 36.9, 1.6);
pose(38.5, 'idle'); pose(38.7, 'lookr');

// ── b12 RECIPE (38.967 - 41.1) · STEP BACK: the real storyboard sheet; "a recipe" lands on "recipe" ──
scene(38.967, '#s12'); tl.set('#g', {{x:-400}}, 38.967);
tl.fromTo('#h12', {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.22, ease:'power3.out'}}, 40.1);
tl.fromTo('#sb', {{scale:1}}, {{scale:1.025, duration:2.1, ease:'none'}}, 38.967);

// ── b13 MIMIC (41.1 - 45.467) · ACT: original and remake play side by side; on "mimic" a copy of him pops in
//    under the remake and copies every move a beat late ──
scene(41.1, '#s13');
for (let i = 1; i < {NJ}; i++) {{ const t = 41.1 + i / 30;
  tl.set('#jo' + (i - 1), {{display:'none'}}, t); tl.set('#jo' + i, {{display:'block'}}, t);
  tl.set('#jr' + (i - 1), {{display:'none'}}, t); tl.set('#jr' + i, {{display:'block'}}, t); }}
tl.set('#g', {{x:189, y:FL}}, 41.1); pose(41.1, 'idle'); pose(41.5, 'lookr'); blink(42.2); pose(42.6, 'idle');
tl.set('#g2', {{x:681, y:FL}}, 41.1);
pose2(43.14, 'crouch'); pose2(43.2, 'idle'); puffs(43.14, [[700,925],[880,925]]);
tl.to('#rmk', {{backgroundColor:'#ff6a3d', color:'#1a1917', duration:0.01}}, 43.14);
const MV = [[43.45,'up'],[43.85,'idle'],[44.1,'jump'],[44.34,'idle'],[44.7,'lookr'],[45.05,'blink'],[45.15,'idle']];
MV.forEach(([t,p]) => {{ pose(t, p); pose2(t + 0.16, p == 'lookr' ? 'lookl' : p); }});
tl.to('#g', {{y:FL - 60, duration:0.12, ease:S(3)}}, 44.1); tl.to('#g', {{y:FL, duration:0.12, ease:S(3)}}, 44.22);
tl.to('#g2', {{y:FL - 60, duration:0.12, ease:S(3)}}, 44.26); tl.to('#g2', {{y:FL, duration:0.12, ease:S(3)}}, 44.38);
tl.set('#g2 .pose2', {{display:'none'}}, 45.467);

// ── b14 CTA (45.467 - 49.2) · ACT: "get your hands on the setup guide" — he holds it up; on "below" he points down ──
scene(45.467, '#s14'); tl.set('#g', {{x:435, y:FL}}, 45.467); pose(45.467, 'idle');
pose(46.0, 'hold');
const BX = 435 + 45, BY = FL - 150 - 84;
tl.set('#book', {{x:BX, y:BY - 50, opacity:1}}, 46.05);
tl.to('#book', {{y:BY, duration:0.12, ease:S(3)}}, 46.05);
tl.to('#g', {{y:FL + 6, duration:0.03}}, 46.17); tl.to('#g', {{y:FL, duration:0.08, ease:S(2)}}, 46.2);
tl.fromTo('#dsc', {{opacity:0, y:14}}, {{opacity:1, y:0, duration:0.2, ease:'power3.out'}}, 47.84);
tl.to('#book', {{x:BX + 170, y:FL - 84, duration:0.14, ease:S(3)}}, 48.12);
pose(48.12, 'idle');
pose(48.32, 'pointdn');                                     // "description below"
blink(48.9); pose(49.0, 'pointdn');
"""

if __name__ == "__main__":
    main(sys.modules[__name__], sys.argv[1:])
