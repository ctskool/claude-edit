"""Geometry in settled event holds of the built page, without rendering video.

  python tools/beat_check/geometry.py <project> [--beats b01,b02] [--json out.json]

Uses conform.py's pinned browser and exact-time seek at 1080x1920. Writes only
temporary browser jobs and the requested JSON report. Exit 0: no FAIL (read
UNVERIFIED too), 1: FAIL, 4: page could not be measured completely.

On an event, geometry = {kind, target_box: [x,y,w,h]} gives frame-pixel targets.
target_selector names the thing marked, separate from EVENT_BINDS' marker.
Beat targets[event_id] accepts the same object. Optional fields: mark_selector,
tolerance_px (default 3, max 20), padding_px, gap_px (underlines), target_text.
Image targets: asset + rect_src (image pixels), optional plate_selector naming
the img/video. Legacy prose is UNVERIFIED, never guessed into coordinates.
Beat text_containers = {"#text": "#card"} associates sibling cards; ancestor
.card/.pc elements are automatic. Split scene paint must stay in y0..960. Text ink excess <=4 px passes,
<=20 px warns. Interior parent clipping is intentional; card/scene clipping
is still checked. Moving elements without a hold are UNVERIFIED. Findings
combine each check/element across states, retaining worst and sampled frames.

Crops use asset, rect_src, box_frame from the kit. <asset>.json or <stem>.json
can supply text_boxes (image pixels) or capture boxes [{tag,text,x,y,w,h}] with
dpr (local CSS pixels). units can be image/css, origin local/page; page requires
crop_css. ASSETS.md accepts fenced JSON {assets: {"assets/shot.png":
{text_boxes: [...]}}}. Prose ROIs are not presumed measured text. No OCR.
"""
import argparse, ast, hashlib, json, math, re, subprocess, sys, tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import project_root
ROOT = project_root()
PASS, WARN, FAIL, UNVERIFIED = "PASS", "WARN", "FAIL", "UNVERIFIED"
EPS = 0.5  # integer scroll metrics and CSS subpixel rounding
MARK = re.compile(r"\b(outline|underline|circle|zoom(?: box)?|highlight|lasso)\b", re.I)


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def box(value):
    """A finite x,y,width,height box, or None."""
    if isinstance(value, dict):
        value = [value.get(k) for k in ("x", "y", "w", "h")]
    if not isinstance(value, (list, tuple)) or len(value) != 4 or not all(finite(v) for v in value):
        return None
    return list(value) if value[2] > 0 and value[3] >= 0 else None


def edges(rect):
    x, y, w, h = rect
    return x, y, x+w, y+h


def outside(rect, region):
    a, b, c, d = edges(rect)
    x, y, r, s = edges(region)
    return max(0, x-a, y-b, c-r, d-s)


def worst(statuses):
    statuses = list(statuses)
    return next((s for s in (FAIL, UNVERIFIED, WARN) if s in statuses), PASS if statuses else UNVERIFIED)


def finding(status, beat, element, check, message, px=None, frame=None, **evidence):
    return dict(status=status, beat_id=beat, element=element, check=check,
                message=message, px=round(px, 3) if px is not None else None, frame=frame, **evidence)


def judge_mark(actual, expected, kind="outline", tolerance=3, padding=0, gap=0, different=False):
    """Largest edge error in frame pixels; underline top is target bottom + gap."""
    x, y, w, h = expected
    got, want = edges(actual), edges([x-padding, y-padding, w+2*padding, h+2*padding])
    error = max(abs(got[i]-want[i]) for i in (0, 2))
    if kind == "underline":
        error = max(error, abs(got[1]-(want[3]+gap)))
    else:
        error = max(error, abs(got[1]-want[1]), abs(got[3]-want[3]))
    return (FAIL if different or error > 20 else PASS if error <= tolerance else WARN), error


def crop_cuts(crop, text):
    """(edge, depth) for crop edges crossing text. Merely touching is fine."""
    l, t, r, b = edges(crop)
    x, y, u, v = edges(text)
    cuts = []
    if min(b, v) > max(t, y):
        for name, edge in (("left", l), ("right", r)):
            if x < edge < u:
                cuts.append((name, min(edge-x, u-edge)))
    if min(r, u) > max(l, x):
        for name, edge in (("top", t), ("bottom", b)):
            if y < edge < v:
                cuts.append((name, min(edge-y, v-edge)))
    return cuts


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf8")).hexdigest()


def safe_asset(project, relative):
    if not isinstance(relative, str):
        raise ValueError("asset path is not a string")
    path = (project / relative).resolve()
    if not path.is_relative_to(Path(project).resolve()):
        raise ValueError("asset path leaves project")
    return path


def literal_binds(project):
    """Read declarations; never execute a project's owners.py."""
    path = project / "tools_local" / "owners.py"
    if not path.exists():
        return None
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "EVENT_BINDS" for t in node.targets):
            return ast.literal_eval(node.value)
    return None


def sources(beat):
    return ([beat["anchor"]] if isinstance(beat.get("anchor"), dict) else []) + beat.get("sub_anchors", []) + beat.get("actions", [])


def jobs_of(plan, doc, beats=None):
    """Missing events.json rows must not erase plan events from coverage."""
    table = {e["event_id"]: e for e in doc["events"]}
    jobs, used = [], set()
    for beat in plan["beats"]:
        if beats is not None and beat["id"] not in beats:
            continue
        for source in sources(beat):
            id_ = source["event_id"]
            event = dict(table.get(id_, {}), event_id=id_, beat_id=beat["id"])
            geom = source.get("geometry")
            if not isinstance(geom, dict):
                geom = beat.get("targets", {}).get(id_, {})
            geom = dict(geom)
            for k in ("target_box", "target_selector", "rect_src", "asset", "plate_selector", "mark_selector"):
                if k in source:
                    geom.setdefault(k, source[k])
            event.update(geometry=geom, what=source.get("what", ""), layout=beat.get("layout"),
                         text_containers=beat.get("text_containers", {}), crops=beat.get("crops", []),
                         beat_start=beat.get("start"), beat_end=beat.get("end"))
            t, fps = source.get("t"), doc.get("fps")
            expected_frame = (0 if t == 0 else math.ceil((t-0.004)*fps-1e-6)) if finite(t) and t >= 0 and finite(fps) and fps > 0 else None
            if expected_frame is None or event.get("frame") != expected_frame:
                event["frame_problem"] = "events.json frame differs from plan time, or event has no measured frame; rebuild"
                event.pop("frame", None)
            used.add(id_)
            jobs.append(event)
    for e in doc["events"]:
        if e["event_id"] in used or (beats is not None and e.get("beat_id") not in beats):
            continue
        beat = next((b for b in plan["beats"] if b["id"] == e.get("beat_id")), {})
        jobs.append(dict(e, geometry={}, layout=beat.get("layout"), text_containers=beat.get("text_containers", {}),
                         crops=beat.get("crops", []), beat_start=beat.get("start"), beat_end=beat.get("end")))
    # Captions may lead their assigned beat. Select the region from the picture's
    # actual frame, using the same just-before-boundary convention as the build.
    fps = doc.get("fps")
    if finite(fps) and fps > 0:
        def boundary(t):
            return 0 if t == 0 else math.ceil((t-0.004)*fps-1e-6)
        for e in jobs:
            f = e.get("frame")
            if not isinstance(f, int):
                continue
            active = next((b for b in plan["beats"] if finite(b.get("start")) and finite(b.get("end"))
                           and boundary(b["start"]) <= f < boundary(b["end"])), None)
            if active:
                e.update(layout=active.get("layout"), fit_beat_id=active["id"],
                         beat_start=active["start"], beat_end=boundary(active["end"])/fps,
                         text_containers=active.get("text_containers", {}))
    return jobs


def text_boxes(meta):
    """Normalize capture metadata to image pixels; ignore non-text boxes."""
    rows = meta.get("text_boxes", meta.get("boxes"))
    if not isinstance(rows, list):
        raise ValueError("no measured text_boxes or boxes list")
    units = meta.get("units", "css" if "dpr" in meta else "image")
    if units not in ("css", "image"):
        raise ValueError("unknown text box units")
    scale = meta.get("dpr", 1) if units == "css" else 1
    if not finite(scale) or scale <= 0:
        raise ValueError("invalid dpr")
    origin = meta.get("origin", "local")
    if origin not in ("local", "page"):
        raise ValueError("unknown text box origin")
    offset = [0, 0]
    if origin == "page":
        offset = box(meta.get("crop_css"))
        if offset is None or units != "css":
            raise ValueError("page boxes need CSS units and crop_css")
    out = []
    for row in rows:
        if isinstance(row, dict) and "text_boxes" not in meta:
            if not row.get("text", "").strip() or row.get("tag", "").lower() in ("img", "svg", "button", "video", "canvas"):
                continue
        rect = box(row.get("box", row) if isinstance(row, dict) else row)
        if rect is None:
            raise ValueError("invalid measured text box")
        x, y, w, h = rect
        out.append({"box": [(x-offset[0])*scale, (y-offset[1])*scale, w*scale, h*scale],
                    "text": row.get("text", "") if isinstance(row, dict) else ""})
    if not out:
        raise ValueError("no measured text boxes (not an OCR assertion of no text)")
    return out


def asset_text(project, asset):
    path = safe_asset(project, asset)
    if not path.is_file():
        raise ValueError("asset missing")
    for sidecar in (path.with_name(path.name+".json"), path.with_suffix(".json")):
        if sidecar.is_file():
            return text_boxes(read_json(sidecar)), str(sidecar)
    for inventory in (project / "ASSETS.md", project.parents[1] / "ASSETS.md"):
        if not inventory.is_file():
            continue
        for block in re.findall(r"\x60{3}json\s*\n(.*?)\x60{3}", inventory.read_text(encoding="utf-8-sig"), re.S):
            meta = json.loads(block).get("assets", {}).get(asset)
            if meta is not None:
                return text_boxes(meta), str(inventory)
    raise ValueError("no text-box sidecar or ASSETS.md measured JSON; prose is not text measurement")


# Embedded to keep permanent additions to the two requested files.
BROWSER = r'''
import fs from 'node:fs';
const job=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const {hf,PINNED}=await import(job.loader);
const {bundleWithLocalizedFonts}=await hf('bundleWithLocalizedFonts');
const {serveStaticProjectHtml}=await hf('staticProjectServer');
const {openSettledCompositionPage,seekCompositionTimeline,DENSE_GEOMETRY_SEEK_OPTIONS}=await hf('captureCompositionFrame');

// Read the authored GSAP schedule, including ancestors and nested timelines.
// A continuous move with no hold stays unverified; it is never a bad fit.
function motion(args){
 const timelines=[...new Set(Object.values(window.__timelines||{}))];
 const spans=[],seen=new Set();
 const focus=(args.targets||[]).flatMap(s=>{try{return [...document.querySelectorAll(s)]}catch{return []}});
 const related=targets=>!focus.length||targets.some(t=>focus.some(n=>t===n||t.contains(n)||n.contains(t)));
 let limit=args.limit;
 for(const root of timelines){
  if(typeof root.getChildren!=='function')continue;
  const origin=root.globalTime(0);
  for(const tween of root.getChildren(true,true,false)){
   if(seen.has(tween))continue;
   seen.add(tween);
   const vars={...tween.vars,...tween.vars.css};
   const targets=tween.targets().filter(n=>n instanceof Element);
   const start=tween.globalTime(0)-origin,end=tween.globalTime(tween.totalDuration())-origin;
   if(start>args.time+1e-7&&(Number(vars.opacity)===0||Number(vars.autoAlpha)===0||vars.display==='none'||vars.visibility==='hidden')
      &&targets.some(t=>focus.some(n=>t===n||t.contains(n))))limit=Math.min(limit,start);
   if(!tween.duration())continue;
   if(!Object.keys(vars).some(k=>/^(x|y|z|xPercent|yPercent|scale.*|rotation.*|skew.*|transform.*|translate.*|perspective|top|left|right|bottom|width|height|fontSize|lineHeight|letterSpacing|padding.*|margin.*|opacity|autoAlpha|clipPath|attr)$/.test(k)))continue;
   if(!targets.length)continue;
   spans.push({start,end,targets});
  }
 }
 // Event frames can precede raw tween time by the build's 4 ms offset.
 const active=spans.filter(s=>s.start<=args.time+1/args.fps+1e-7&&s.end>args.time+1e-7);
 const visible=n=>{
  // Ignore self opacity for an entrance just starting at zero.
  for(let p=n;p instanceof Element;p=p.parentElement){
   const style=getComputedStyle(p);
   if(style.display==='none'||(p!==n&&Number(style.opacity)<=.05))return false;
  }
  return true;
 };
 const ends=active.filter(s=>related(s.targets)&&s.targets.some(visible)&&s.end<limit-1/args.fps).map(s=>s.end);
 const moving=[];
 const name=n=>n.id?'#'+n.id:(n.getAttribute('data-own')?'[data-own='+JSON.stringify(n.getAttribute('data-own'))+']':
  n.parentElement?name(n.parentElement)+' > '+n.tagName.toLowerCase()+':nth-child('+([...n.parentElement.children].indexOf(n)+1)+')':n.tagName.toLowerCase());
 for(const n of document.querySelectorAll('body *')){
  if(active.some(s=>s.targets.some(t=>t===n||t.contains(n)))){
   moving.push(name(n));
  }
 }
 // CSS/WAAPI animations are not necessarily driven by the composition seek.
 for(const a of document.getAnimations()){
  if(a.playState==='running'&&a.effect?.target instanceof Element){
   const n=a.effect.target;
   for(const el of [n,...n.querySelectorAll('*')])moving.push(name(el));
  }
 }
 return {next:ends.length?Math.max(...ends):null,moving,verified:timelines.length>0};
}

function measure(args){
 const rect=n=>{const b=n.getBoundingClientRect();return [b.x,b.y,b.width,b.height]};
 const intersect=(a,b)=>{const x=Math.max(a[0],b[0]),y=Math.max(a[1],b[1]);return [x,y,Math.max(0,Math.min(a[0]+a[2],b[0]+b[2])-x),Math.max(0,Math.min(a[1]+a[3],b[1]+b[3])-y)]};
 const name=n=>n.id?'#'+n.id:(n.getAttribute('data-own')?'[data-own='+JSON.stringify(n.getAttribute('data-own'))+']':
  n.parentElement?name(n.parentElement)+' > '+n.tagName.toLowerCase()+':nth-child('+([...n.parentElement.children].indexOf(n)+1)+')':n.tagName.toLowerCase());
 const painted=n=>{
  if(['hidden','collapse'].includes(getComputedStyle(n).visibility))return false;
  let opacity=1;
  for(let p=n;p instanceof Element;p=p.parentElement){
   const s=getComputedStyle(p);opacity*=Number(s.opacity);
   if(s.display==='none')return false;
   if(p.matches('defs,symbol,clipPath,mask'))return false;
  }
  return opacity>.05;
 };
 const unsupported=n=>{
  for(let p=n;p instanceof Element;p=p.parentElement){
   const s=getComputedStyle(p);
   if(s.clipPath!=='none'||s.maskImage!=='none')return 'clip-path or mask needs shape-aware geometry';
   if(s.transform!=='none'){
    const m=new DOMMatrixReadOnly(s.transform);
    if(!m.is2D||Math.abs(m.b)>.00001||Math.abs(m.c)>.00001||m.a<=0||m.d<=0)return 'rotation, skew, perspective or reflection';
   }
  }
  return null;
 };
 const solid=c=>c&&c!=='none'&&c!=='transparent'&&!/rgba\([^)]*,\s*0(?:\.0+)?\)$/.test(c);
 const markerPaint=n=>{
  const s=getComputedStyle(n);
  if(!painted(n))return false;
  if(n.matches('img,video'))return true;
  if(n instanceof SVGGeometryElement){
   if(s.strokeDasharray!=='none'&&Math.abs(parseFloat(s.strokeDashoffset))>.01)return false;
   return solid(s.fill)||(solid(s.stroke)&&parseFloat(s.strokeWidth)>0);
  }
  if(solid(s.backgroundColor)||['Top','Right','Bottom','Left'].some(k=>parseFloat(s['border'+k+'Width'])>0&&!['none','hidden'].includes(s['border'+k+'Style'])&&solid(s['border'+k+'Color'])))return true;
  return false;
 };
 const ownText=n=>[...n.childNodes].some(c=>c.nodeType===Node.TEXT_NODE&&c.textContent.trim());
 const skip=n=>n.matches('script,style,link,meta,br,defs,defs *,symbol,symbol *,clipPath,clipPath *,mask,mask *');
 const scene=n=>n.closest('.scene')||args.roots.map(s=>document.querySelector(s)).find(r=>r&&r.contains(n));
 const clips=(n,b)=>{
  // Interior windows crop oversized media. Scene/frame/card bounds stay raw.
  for(let p=n.parentElement;p&&p!==scene(n)&&p!==document.body&&!p.matches('[data-composition-id]');p=p.parentElement){
   const s=getComputedStyle(p);
   if(/hidden|clip|scroll|auto/.test(s.overflowX+s.overflowY)&&!p.matches('.card,.pc,[data-card]')){
    const r=rect(p),wide=/hidden|clip|scroll|auto/.test(s.overflowX),high=/hidden|clip|scroll|auto/.test(s.overflowY);
    b=intersect(b,[wide?r[0]:-1e7,high?r[1]:-1e7,wide?r[2]:2e7,high?r[3]:2e7]);
   }
  }
  return b;
 };
 const select=s=>{try{return {nodes:[...document.querySelectorAll(s)]}}catch(e){return {nodes:[],error:String(e)}}};
 const nodeInfo=n=>{
  const b=rect(n),s=getComputedStyle(n),natural=[n.naturalWidth||n.videoWidth||0,n.naturalHeight||n.videoHeight||0];
  const clip=clips(n,b),sx=natural[0]/b[2],sy=natural[1]/b[3];
  const seen=intersect(clip,[0,0,1080,1920]);
  return {selector:name(n),box:b,visible:painted(n)&&seen[2]>0&&(seen[3]>0||b[3]===0),
   unsupported:unsupported(n),markPaint:markerPaint(n)||[...n.querySelectorAll('*')].some(markerPaint),text:n.textContent?.trim()||'',
   src:n.getAttribute('src'),natural,fit:s.objectFit,position:s.objectPosition,
   imageInsets:['paddingLeft','paddingRight','paddingTop','paddingBottom','borderLeftWidth','borderRightWidth','borderTopWidth','borderBottomWidth'].some(k=>parseFloat(s[k])>0),
   source_crop:natural.every(v=>v>0)&&b[2]>0&&b[3]>0?[(clip[0]-b[0])*sx,(clip[1]-b[1])*sy,clip[2]*sx,clip[3]*sy]:null,
   loaded:n.tagName!=='IMG'||(n.complete&&n.naturalWidth>0)};
 };
 const selected={};
 for(const sel of args.selectors){
  const result=select(sel);selected[sel]={error:result.error,count:result.nodes.length,nodes:result.nodes.map(nodeInfo)};
 }
 const elements=[],texts=[],unknown=[],roots=args.roots.map(s=>document.querySelector(s)).filter(Boolean);
 const moving=new Set(args.moving||[]);
 const all=[...document.querySelectorAll('body *')];
 for(const n of all){
  if(skip(n)||!painted(n))continue;
  const b=rect(n),sc=scene(n),hasText=ownText(n);
  const isScene=n.matches('.scene')||roots.includes(n);
  // Unpainted wrappers have layout bounds, not a painted footprint.
  // Keep empty leaves so a misplaced authored box still gets checked.
  const footprint=hasText||markerPaint(n)||!n.children.length;
  if((sc||isScene||hasText||markerPaint(n))&&footprint&&b[2]>0&&b[3]>0){
   const effective=clips(n,b);
   if(effective[2]>0&&effective[3]>0)elements.push({selector:name(n),box:effective,scene:sc?rect(sc):null,unsupported:unsupported(n),moving:args.timing_verified===false||moving.has(name(n))});
  }
  if(n.matches('canvas,iframe')&&sc)unknown.push({selector:name(n),reason:'canvas/iframe content is not DOM text'});
  if(!hasText)continue;
  let ink=[];
  for(const c of n.childNodes){
   if(c.nodeType!==Node.TEXT_NODE||!c.textContent.trim())continue;
   const r=document.createRange();r.selectNodeContents(c);
   ink.push(...[...r.getClientRects()].map(b=>clips(n,[b.x,b.y,b.width,b.height])).filter(b=>b[2]>0&&b[3]>0));
  }
  if(!ink.length)continue;
  let card=n.parentElement?.closest('.card,.pc,[data-card]'),cardError=null;
  for(const [textSel,cardSel] of Object.entries(args.text_containers||{})){
   try{if(n.matches(textSel)||n.closest(textSel)){const r=select(cardSel);if(r.nodes.length===1)card=r.nodes[0];else cardError='card selector missing or ambiguous: '+cardSel}}catch(e){cardError=String(e)}
  }
  const containers=[];
  for(let p=n.parentElement;p&&p!==sc&&p!==document.body;p=p.parentElement){
   const r=rect(p);if(r[2]>0&&r[3]>0&&getComputedStyle(p).display!=='inline')containers.push(r);
  }
  texts.push({selector:name(n),box:b,ink,containers,cardUnverified:!card&&!!sc?.querySelector('.card,.pc,[data-card]'),scene:sc?rect(sc):null,card:card?rect(card):null,cardError,
   unsupported:unsupported(n),moving:args.timing_verified===false||moving.has(name(n)),
   inline:getComputedStyle(n).display==='inline',text:n.textContent.trim()});
 }
 const media=all.filter(n=>n.matches('img,video')&&painted(n)).map(nodeInfo);
 return {viewport:[innerWidth,innerHeight],elements,texts,selected,media,unknown};
}

let browser,server;
const errors=[],frames={};
try{
 const html=await bundleWithLocalizedFonts(job.project);
 server=await serveStaticProjectHtml(job.project,html);
 const opened=await openSettledCompositionPage(html,server.url,{
  renderReadyTimeoutMs:15000,renderReadyWarningSuffix:'geometry is UNVERIFIED',
  beforeNavigate:async p=>{
   await p.setViewport({width:1080,height:1920,deviceScaleFactor:1});
   p.on('pageerror',e=>errors.push(e.message));
   p.on('response',r=>{if(r.status()>=400&&!/favicon/.test(r.url()))errors.push(r.status()+' '+new URL(r.url()).pathname)});
  }});
 browser=opened.browser;
 if(opened.renderReadyTimedOut)throw Error('composition runtime not ready');
 const page=opened.page;
 await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(n=>n.decode().catch(()=>{})))});
 const ready=await page.evaluate(()=>!!(window.__player||window.__hf?.seek||Object.values(window.__timelines||{}).some(t=>typeof t.seek==='function')));
 if(!ready)throw Error('no seekable composition timeline');
 for(const [f,args] of Object.entries(job.frames).sort((a,b)=>Number(a[0])-Number(b[0]))){
  await seekCompositionTimeline(page,Number(f)/job.fps,{...DENSE_GEOMETRY_SEEK_OPTIONS,exactTime:true});
  // Highlights keep event-time evidence; fit checks use a separate settled hold.
  const atEvent=await page.evaluate(measure,args);
  let settled=Number(f),timing;
  for(let attempt=0;attempt<32;attempt++){
   timing=await page.evaluate(motion,{time:settled/job.fps,limit:args.limit,fps:job.fps,targets:args.targets});
   if(timing.next===null)break;
   const next=Math.ceil(timing.next*job.fps-1e-7);
   if(next<=settled||next/job.fps>=args.limit)break;
   settled=next;
   await seekCompositionTimeline(page,settled/job.fps,{...DENSE_GEOMETRY_SEEK_OPTIONS,exactTime:true});
  }
  timing=await page.evaluate(motion,{time:settled/job.fps,limit:args.limit,fps:job.fps,targets:args.targets});
  const hold=await page.evaluate(measure,{...args,moving:timing.moving,timing_verified:timing.verified});
  hold.frame=settled;
  hold.timing_verified=timing.verified;
  frames[f]={...atEvent,settled:hold};
 }
 fs.writeFileSync(job.out,JSON.stringify({hyperframes:PINNED,frames,errors}));
}finally{
 if(browser)await browser.close();
 if(server)await server.close();
}
'''


def run_measure(project, fps, jobs, ownership):
    frames = {}
    roots = [o["roots"][0] for o in ownership.get("owners", []) if o.get("kind") == "scene" and o.get("roots")]
    for e in jobs:
        f = e.get("frame")
        if not isinstance(f, int) or isinstance(f, bool) or not 0 <= f < ownership["total_frames"]:
            continue
        limit = e.get("beat_end")
        if not finite(limit) or limit <= f/fps:
            limit = min(ownership["total_frames"]/fps, (f+1)/fps)
        row = frames.setdefault(str(f), {"roots": roots, "selectors": [], "targets": [], "text_containers": {}, "limit": limit})
        row["limit"] = min(row["limit"], limit)
        if isinstance(e.get("target"), str):
            row["targets"] = sorted(set(row["targets"] + [e["target"]]))
        g = e["geometry"]
        row["selectors"] += [s for s in (e.get("target"), g.get("target_selector"), g.get("mark_selector"), g.get("plate_selector")) if isinstance(s, str)]
        row["selectors"] += [c["plate_selector"] for c in e.get("crops", [])
                             if isinstance(c, dict) and isinstance(c.get("plate_selector"), str)]
        row["selectors"] = sorted(set(row["selectors"]))
        row["text_containers"].update(e["text_containers"])
    if not frames:
        raise ValueError("no valid event frames to measure")
    with tempfile.TemporaryDirectory(prefix="beat-geometry-") as tmp:
        temp = Path(tmp)
        job = dict(project=str(project), loader=(ROOT / "tools/beat_render/hf.mjs").as_uri(),
                   fps=fps, frames=frames, out=str(temp / "measured.json"))
        (temp / "geometry.mjs").write_text(BROWSER, encoding="utf8")
        (temp / "job.json").write_text(json.dumps(job), encoding="utf8")
        try:
            subprocess.run(["node", str(temp / "geometry.mjs"), str(temp / "job.json")], cwd=ROOT,
                           check=True, timeout=900, capture_output=True, text=True, encoding="utf8", errors="replace")
        except subprocess.CalledProcessError as e:
            raise ValueError((e.stderr or e.stdout or str(e))[-1800:]) from e
        return read_json(temp / "measured.json")


def selected_node(snapshot, selector):
    row = snapshot["selected"].get(selector, {})
    if row.get("error"):
        raise ValueError("invalid selector: "+row["error"])
    if row.get("count") != 1:
        raise ValueError(f"selector {selector!r} matched {row.get('count', 0)} elements, expected one")
    node = row["nodes"][0]
    if node.get("src") and not node.get("loaded"):
        raise ValueError(f"{selector} image has not loaded")
    if not node["visible"]:
        raise ValueError(f"{selector} hidden or has no box at this event frame")
    if node.get("unsupported"):
        raise ValueError(f"{selector}: {node['unsupported']}")
    return node


def same_asset(src, asset):
    """The page reports a resolved URL ("http://127.0.0.1:port/assets/x.png"); the plan names "assets/x.png" or "x.png"."""
    if not isinstance(src, str) or not isinstance(asset, str):
        return False
    path = unquote(urlsplit(src).path) if "://" in src else src
    path, asset = path.replace("\\", "/").lstrip("./"), asset.replace("\\", "/").lstrip("./")
    return path == asset or path.endswith("/" + asset)


def image_node(snapshot, asset, selector=None):
    # HyperFrames inlines images as data: URIs, so a selector the plan names is trusted over the src.
    nodes = [selected_node(snapshot, selector)] if selector else [n for n in snapshot["media"] if same_asset(n.get("src"), asset) and n["visible"]]
    inlined = selector and str(nodes[0].get("src") or "").startswith("data:")
    if len(nodes) != 1 or not (inlined or same_asset(nodes[0].get("src"), asset)):
        raise ValueError(f"{asset}: missing/ambiguous image instance; supply plate_selector naming img/video")
    n = nodes[0]
    if n.get("unsupported") or n.get("imageInsets") or not n.get("loaded") or not all(n["natural"]):
        raise ValueError("image unloaded or unsupported geometry")
    if n.get("fit") not in ("fill", None):
        raise ValueError("source mapping needs object-fit:fill (cover/contain not measured)")
    return n


def image_box(snapshot, asset, source, selector=None):
    """Map source pixels through the actual built image, never a planned scale."""
    n = image_node(snapshot, asset, selector)
    x, y, w, h = n["box"]
    sx, sy = w/n["natural"][0], h/n["natural"][1]
    return [x+source[0]*sx, y+source[1]*sy, source[2]*sx, source[3]*sy]


def node_verdict(n, layout, check):
    """Judge one measured state; no scroll metrics or event-specific evidence."""
    if n.get("moving"):
        return [(UNVERIFIED, check, "transform/entrance has no settled hold at sample", None)]
    if n.get("unsupported") or n.get("cardError"):
        return [(UNVERIFIED, check, n.get("unsupported") or n["cardError"], None)]
    regions = [[0, 0, 1080, 1920]]
    if n.get("scene"):
        regions.append(n["scene"])
        if layout == "split":
            regions.append([0, 0, 1080, 960])
    if check == "off_canvas":
        error = max(outside(n["box"], r) for r in regions)
        return [(FAIL if error > EPS else PASS, check,
                 "outside frame, scene root or layout region" if error > EPS else "inside measured region", error)]
    regions += n.get("containers", [])
    if n.get("card"):
        regions.append(n["card"])
    # Inline spans have no useful client box; their Range ink must fit ancestors.
    if not n.get("inline") and n["box"][2] > 0 and n["box"][3] > 0:
        regions.append(n["box"])
    error = max([0] + [outside(ink, r) for ink in n["ink"] for r in regions])
    rows = [(FAIL if error > 20 else WARN if error > 4 else PASS, check,
             "text ink exceeds box/card/scene" if error > 4 else "observed ink fits measured boundaries", error)]
    if n.get("cardUnverified"):
        rows.append((UNVERIFIED, "text_card", "sibling card association unspecified; add beat text_containers", None))
    return rows


def judge_snapshot(e, snapshot, cache=None):
    beat, frame, out = e.get("beat_id"), e["frame"], []
    cache = {} if cache is None else cache

    def add(status, element, check, message, px=None, **kw):
        out.append(finding(status, beat, element, check, message, px, frame, event_id=e["event_id"], **kw))

    for collection, check in (("elements", "off_canvas"), ("texts", "text_overflow")):
        for n in snapshot[collection]:
            key = digest([check, e.get("layout"), n])
            if key not in cache:
                cache[key] = node_verdict(n, e.get("layout"), check)
            for status, kind, message, error in cache[key]:
                add(status, n["selector"], kind, message, error, state=key,
                    actual=n["box"], **({"ink": n["ink"]} if collection == "texts" else {}))
    for n in snapshot.get("unknown", []):
        add(UNVERIFIED, n["selector"], "text_overflow", n["reason"])
    for collection, check in (("elements", "off_canvas"), ("texts", "text_overflow")):
        if not snapshot[collection]:
            add(UNVERIFIED, e["event_id"], check, "no visible DOM geometry at settled frame")
    if e.get("layout") not in ("split", "full-graphic", "full-face"):
        add(UNVERIFIED, e["event_id"], "layout", "unknown layout; only frame and scene bounds checked")
    return out


def combine_findings(rows):
    """One finding per check/element, retaining worst evidence and state coverage."""
    groups = {}
    rank = {PASS: 0, WARN: 1, UNVERIFIED: 2, FAIL: 3}
    for row in rows:
        # Crops use beat-local indices; give them a project-wide identity.
        element = row["element"]
        if row["check"].startswith("crop_"):
            element = str(row["beat_id"])+":"+element
        groups.setdefault((row["check"], element), []).append(row)
    out = []
    for (_, element), group in groups.items():
        worst_row = max(group, key=lambda r: (rank[r["status"]], r["px"] if r["px"] is not None else -1))
        result = dict(worst_row, element=element)
        frames = sorted({r["frame"] for r in group if r["frame"] is not None})
        result.update(frames=frames, frame_span=[frames[0], frames[-1]] if frames else None,
                      beat_ids=sorted({r["beat_id"] for r in group if r["beat_id"]}),
                      event_ids=sorted({r["event_id"] for r in group if r.get("event_id")}),
                      worst_px=max((r["px"] for r in group if r["px"] is not None), default=None))
        # Keep non-contiguous states separate: a repeated shell state is judged once.
        states = {}
        for r in group:
            if r.get("state"):
                state = states.setdefault(r["state"], dict(status=r["status"], px=r["px"], frames=[]))
                if r["frame"] is not None:
                    state["frames"].append(r["frame"])
        result["states"] = [dict(state=key, **dict(value, frames=sorted(set(value["frames"])))) for key, value in states.items()]
        out.append(result)
    return out


def judge_highlight(e, snapshot):
    g = e["geometry"]
    if not g and not MARK.search(e.get("what") or ""):
        return []
    id_, beat, f = e["event_id"], e.get("beat_id"), e.get("frame")
    make = lambda status, message, px=None, **kw: [finding(status, beat, id_, "highlight", message, px, f, **kw)]
    try:
        if not e.get("target"):
            raise ValueError("no EVENT_BINDS target in events.json")
        if g.get("mark_selector") and g["mark_selector"] != e["target"]:
            return make(FAIL, "EVENT_BINDS names a different element than mark_selector")
        actual = selected_node(snapshot, e["target"])
        if not actual.get("markPaint"):
            raise ValueError("bound element has no measured marker paint (or SVG stroke is still drawing)")
        kind = g.get("kind", "underline" if re.search(r"\bunderline\b", e.get("what", ""), re.I) else "outline")
        if kind not in ("outline", "underline", "circle", "zoom", "zoom box", "highlight", "lasso"):
            raise ValueError("unsupported mark kind: "+str(kind))
        tolerance, padding, gap = g.get("tolerance_px", 3), g.get("padding_px", 0), g.get("gap_px", 0)
        if not all(finite(v) for v in (tolerance, padding, gap)) or not 0 <= tolerance <= 20:
            raise ValueError("invalid tolerance/padding/gap; tolerance must be 0..20 px")
        expected, target = box(g.get("target_box")), None
        if g.get("target_selector"):
            if g["target_selector"] == e["target"]:
                raise ValueError("marker cannot vouch for its own intended target")
            target = selected_node(snapshot, g["target_selector"])
            expected = target["box"]
            if g.get("target_text") and g["target_text"] not in target["text"]:
                return make(FAIL, "target_selector names a different text element")
        elif g.get("asset") and box(g.get("rect_src")):
            source = box(g["rect_src"])
            expected = image_box(snapshot, g["asset"], source, g.get("plate_selector"))
            image = image_node(snapshot, g["asset"], g.get("plate_selector"))
            if not box(image.get("source_crop")) or outside(source, image["source_crop"]) > EPS:
                raise ValueError("intended source target is clipped out of the built plate")
        if expected is None:
            raise ValueError("no target_box, target_selector or asset + rect_src; legacy prose is not measured")
        different = False
        if target:
            for other in snapshot["elements"]:
                if other["selector"] in (actual["selector"], target["selector"]) or other.get("unsupported"):
                    continue
                _, neighbour_error = judge_mark(actual["box"], other["box"], kind, tolerance, padding, gap)
                _, intended_error = judge_mark(actual["box"], expected, kind, tolerance, padding, gap)
                if neighbour_error <= EPS and intended_error > max(tolerance, EPS):
                    different = True
                    break
        status, error = judge_mark(actual["box"], expected, kind, tolerance, padding, gap, different)
        return make(status, "marks a different element" if different else "largest target edge error", error,
                    actual=actual["box"], expected=expected, tolerance_px=tolerance, target=e["target"])
    except (ValueError, TypeError, KeyError) as exc:
        return make(UNVERIFIED, str(exc))


def judge_crops(project, beat, snapshot, frame):
    rows = []
    for i, crop in enumerate(beat.get("crops", [])):
        name = f"crop[{i}]"
        asset = crop.get("asset") if isinstance(crop, dict) else None
        try:
            if not isinstance(asset, str) or not box(crop.get("rect_src")):
                raise ValueError("crop needs asset and numeric rect_src")
            image = image_node(snapshot, asset, crop.get("plate_selector"))
            actual = box(image.get("source_crop"))
            if actual is None:
                raise ValueError("no measured crop window")
            texts, source = asset_text(project, asset)
            hits = [(text, edge, depth) for text in texts for edge, depth in crop_cuts(actual, text["box"])]
            _, drift = judge_mark(actual, crop["rect_src"])
            if drift > 1:
                rows.append(finding(WARN, beat["id"], name, "crop_plan", "built crop differs from planned rect_src (source px); checking built crop",
                                    drift, frame, actual=actual, expected=crop["rect_src"], asset=asset))
            for text, edge, depth in hits:
                rows.append(finding(WARN, beat["id"], name, "crop_text", f"{edge} crop edge slices measured text (source px): {text['text'][:80]}",
                                    depth, frame, asset=asset, text_box=text["box"], metadata=source))
            if not hits:
                rows.append(finding(PASS, beat["id"], name, "crop_text",
                                    f"no built crop edge crosses {len(texts)} supplied text boxes; unlisted text unverified", 0, frame, asset=asset, metadata=source))
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            rows.append(finding(UNVERIFIED, beat["id"], name, "crop_text", str(exc), frame=frame, asset=asset))
    return rows


def geometry(project, beats=None):
    project = Path(project).resolve()
    report = dict(schema=1, check="geometry", project=str(project), scope="all" if beats is None else sorted(beats),
                  findings=[], events=[], frames_measured=0, measured=False)
    rows, jobs = report["findings"], []
    try:
        plan, doc, own = [read_json(project / name) for name in ("plan.json", "events.json", "ownership.json")]
        html_sha = hashlib.sha256((project / "index.html").read_bytes()).hexdigest()
        report.update(html_sha256=html_sha, plan_sha256=digest(plan), composition_rev=own.get("composition_rev"))
        body = {k: v for k, v in own.items() if k not in ("composition_rev", "authoring")}
        if own.get("schema") != 1 or own.get("html_sha256") != html_sha or own.get("composition_rev") != digest(body):
            raise ValueError("ownership.json missing, damaged or stale for index.html; rebuild")
        if doc.get("schema") != 1 or doc.get("composition_rev") != own["composition_rev"] or doc.get("html_sha256") != html_sha:
            raise ValueError("events.json is not of this page; rebuild")
        if doc.get("lock_revision") != own.get("lock_revision"):
            raise ValueError("events.json and ownership.json name different beat locks")
        fps = doc["fps"]
        if not finite(fps) or fps <= 0 or fps != own["fps"] or doc["total_frames"] != own["total_frames"]:
            raise ValueError("invalid or conflicting fps/total_frames")
        known = {b["id"] for b in plan["beats"]}
        if beats is not None and set(beats)-known:
            rows.append(finding(FAIL, None, "scope", "scope", f"unknown beats: {sorted(set(beats)-known)}"))
        jobs = jobs_of(plan, doc, beats)
        binds = None
        try:
            binds = literal_binds(project)
        except (OSError, ValueError, SyntaxError) as exc:
            rows.append(finding(UNVERIFIED, None, "EVENT_BINDS", "bind", "cannot read literal EVENT_BINDS: "+str(exc)))
        if binds is not None:
            for e in jobs:
                bind = binds.get(e["event_id"])
                if bind and (bind[0], bind[1]) != (e.get("owner"), e.get("target")):
                    rows.append(finding(UNVERIFIED, e.get("beat_id"), e["event_id"], "bind", "events.json differs from EVENT_BINDS; rebuild", frame=e.get("frame")))
                    e["target"] = None
        measured = run_measure(project, fps, jobs, own)
        report["hyperframes"] = measured.get("hyperframes")
        report["event_frames_measured"] = len(measured["frames"])
        report["settled_frames_measured"] = len({s.get("settled", {}).get("frame", int(f)) for f, s in measured["frames"].items()})
        report["frames_measured"] = len({int(f) for f in measured["frames"]} |
                                        {s.get("settled", {}).get("frame", int(f)) for f, s in measured["frames"].items()})
        for error in measured.get("errors", []):
            rows.append(finding(UNVERIFIED, None, "page", "runtime", error))
        complete = True
        state_cache = {}
        for e in jobs:
            snapshot = measured["frames"].get(str(e.get("frame")))
            if snapshot is None or snapshot.get("viewport") != [1080, 1920]:
                complete = False
                rows.append(finding(UNVERIFIED, e.get("beat_id"), e["event_id"], "measurement", e.get("frame_problem", "event frame not measured at 1080x1920"), frame=e.get("frame")))
                continue
            checks = []
            if not e.get("target"):
                checks.append(finding(UNVERIFIED, e.get("beat_id"), e["event_id"], "bind", "no EVENT_BINDS target; visible scene geometry still inspected", frame=e["frame"]))
            else:
                try:
                    selected_node(snapshot, e["target"])
                except ValueError as exc:
                    checks.append(finding(UNVERIFIED, e.get("beat_id"), e["event_id"], "bind", str(exc), frame=e["frame"]))
            hold = snapshot.get("settled", snapshot)
            settled_frame = hold.get("frame", e["frame"])
            if hold.get("viewport") != [1080, 1920]:
                complete = False
                checks.append(finding(UNVERIFIED, e.get("beat_id"), e["event_id"], "measurement", "settled frame not measured", frame=settled_frame))
            else:
                checks += judge_snapshot(dict(e, frame=settled_frame, beat_id=e.get("fit_beat_id", e.get("beat_id"))), hold, state_cache)
            if hold.get("timing_verified") is False:
                checks.append(finding(UNVERIFIED, e.get("beat_id"), e["event_id"], "timing", "no inspectable GSAP schedule; rest unverified", frame=settled_frame))
            checks += judge_highlight(e, snapshot)
            beat = next((b for b in plan["beats"] if b["id"] == e.get("beat_id")), None)
            if beat:
                checks += judge_crops(project, beat, snapshot, e["frame"])
            rows.extend(checks)
            report["events"].append(dict(event_id=e["event_id"], beat_id=e.get("beat_id"), frame=e["frame"], settled_frame=settled_frame, status=worst(r["status"] for r in checks)))
        report["measured"] = complete and bool(jobs)
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, OverflowError, subprocess.TimeoutExpired) as exc:
        rows.append(finding(UNVERIFIED, None, "page", "measurement", str(exc)))
    reported = {e["event_id"] for e in report["events"]}
    for e in jobs:
        if e["event_id"] not in reported:
            report["events"].append(dict(event_id=e["event_id"], beat_id=e.get("beat_id"), frame=e.get("frame"), status=UNVERIFIED))
            rows.append(finding(UNVERIFIED, e.get("beat_id"), e["event_id"], "measurement", e.get("frame_problem", "event frame not measured"), frame=e.get("frame")))
    report["findings"] = combine_findings(rows)
    report["counts"] = {s: sum(r["status"] == s for r in report["findings"]) for s in (PASS, WARN, FAIL, UNVERIFIED)}
    report["status"] = worst(r["status"] for r in report["findings"])
    return report


def exit_code(report):
    if any(r["status"] == FAIL for r in report["findings"]):
        return 1
    return 0 if report["measured"] else 4


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project")
    ap.add_argument("--beats", help="comma-separated beats; default all")
    ap.add_argument("--json", dest="out", help="write report here; no default project writes")
    a = ap.parse_args(argv)
    report = geometry(a.project, None if a.beats is None else [b.strip() for b in a.beats.split(",") if b.strip()])
    for r in report["findings"]:
        pixels = "n/a px" if r["px"] is None else f"{r['px']:.2f} px"
        print(f"{r['status']} {r['beat_id'] or '-'} {r['element']} frame {r['frame'] if r['frame'] is not None else '-'} {r['check']}: {' '.join(r['message'].split())} ({pixels})")
    print(report["status"], "geometry", report["counts"], f"{report['frames_measured']} frames measured")
    if a.out:
        path = Path(a.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=1, ensure_ascii=False)+"\n", encoding="utf8")
    return exit_code(report)


if __name__ == "__main__":
    sys.exit(main())
