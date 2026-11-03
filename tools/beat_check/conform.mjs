// Measures a composition for tools/beat_check/conform.py, with the same bundler, browser and exact-time seek as hyperframes snapshot.
// No selection.json. The job names frames and selectors, this reports what the page shows there, and the verdicts are conform.py's.
//   node tools/beat_check/conform.mjs JOB.json
// Failure exits non-zero and writes nothing, which conform.py reports as UNVERIFIED.
import fs from 'node:fs';
import path from 'node:path';
import {hf,PINNED} from '../beat_render/hf.mjs';

const job=JSON.parse(fs.readFileSync(process.argv[2]));
const project=path.resolve(job.project);
const {bundleWithLocalizedFonts}=await hf('bundleWithLocalizedFonts');
const {serveStaticProjectHtml}=await hf('staticProjectServer');
const {openSettledCompositionPage,seekCompositionTimeline,DENSE_GEOMETRY_SEEK_OPTIONS}=await hf('captureCompositionFrame');

// measure.mjs's visible() and own-text rule. A word counts only through the element that holds its text node, so a sized parent cannot vouch for a hidden child.
function install(){
 const seen=new WeakMap();let next=1;
 const serial=n=>{if(!seen.has(n))seen.set(n,next++);return seen.get(n)};
 function visible(n){
  let opacity=1,p=n;const b=n.getBoundingClientRect();
  let left=Math.max(0,b.left),top=Math.max(0,b.top),right=Math.min(innerWidth,b.right),bottom=Math.min(innerHeight,b.bottom);
  while(p&&p instanceof Element){
   const s=getComputedStyle(p);opacity*=Number(s.opacity);
   if(s.display==='none'||s.visibility==='hidden')return false;
   if(/hidden|clip/.test(s.overflow+s.overflowX+s.overflowY)){const r=p.getBoundingClientRect();left=Math.max(left,r.left);top=Math.max(top,r.top);right=Math.min(right,r.right);bottom=Math.min(bottom,r.bottom)}
   p=p.parentElement;
  }
  return opacity>.05&&right-left>1&&bottom-top>1;
 }
 function ownText(root){
  const words=[],walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
  while(walker.nextNode()){const c=walker.currentNode;if(c.nodeValue.trim()&&visible(c.parentElement))words.push(c.nodeValue)}
  return words.join(' ').replace(/\s+/g,' ').trim();
 }
 function state(n){
  const s=getComputedStyle(n),attr=k=>n.getAttribute(k);
  return [s.opacity,s.display,s.visibility,s.transform,s.color,s.backgroundColor,s.borderTopColor,s.clipPath,s.width,s.height,attr('stroke-dashoffset'),attr('opacity')].join('|');
 }
 const symbols=n=>[...n.querySelectorAll('use')].map(u=>(u.getAttribute('href')||'').slice(1));
 window.__measure=selectors=>Object.fromEntries(selectors.map(sel=>{
  const n=document.querySelector(sel);
  return [sel,n?{visible:visible(n),text:ownText(n),state:state(n),node:serial(n),symbols:symbols(n)}:null];
 }));
}

// Runs in the page once. Each tween a block made must write inside that block's declared roots, and a write into an extra root must stay in the owner's own window.
// A scene root is off limits to its own block: its opacity is what the window table controls, so a write there shows on beats that do not depend on this owner.
function audit(owners){
 const own=window.__own;
 if(!own)return {missing:true,problems:[],tweens:0};
 const problems=[],declared=new Set(owners.map(o=>o.id));
 const main=Object.values(window.__timelines||{});
 if(!window.__positionsWatched)problems.push({owner:'timeline',problem:'positions were not watched while the page built its timeline'});
 for(const [timeline,call,at] of window.__unplaced||[])if(main.includes(timeline))problems.push({owner:'timeline',problem:`tl.${call}() placed by ${at}, not a number`});
 const scenes=owners.map(o=>document.querySelector(o.roots[0])).filter(Boolean);
 let tweens=0;
 const flat=t=>t.getChildren?t.getChildren(true,true,false):[t];
 const name=e=>e instanceof Element?(e.id?'#'+e.id:e.tagName.toLowerCase()+'.'+(e.getAttribute('class')||'')):String(e);
 for(const id of Object.keys(own))if(id!=='shell'&&!declared.has(id))problems.push({owner:id,problem:'a tween group with no declared owner'});
 for(const o of owners){
  const roots=o.roots.map(s=>document.querySelector(s)),extra=roots.slice(1);
  roots.forEach((r,i)=>{if(!r)problems.push({owner:o.id,problem:'root not in the page: '+o.roots[i]})});
  for(const t of (own[o.id]||[]).flatMap(flat)){
   tweens++;
   const targets=t.targets();
   if(!targets.length)problems.push({owner:o.id,problem:`tween at ${t.startTime().toFixed(3)} s has no target`});
   for(const e of targets){
    if(e instanceof Element&&scenes.some(r=>e.contains(r))){problems.push({owner:o.id,problem:`writes a scene root: ${name(e)} at ${t.startTime().toFixed(3)} s`});continue}
    if(!(e instanceof Element)||!roots.some(r=>r&&r.contains(e))){problems.push({owner:o.id,problem:`writes outside its roots: ${name(e)} at ${t.startTime().toFixed(3)} s`});continue}
    if(extra.some(r=>r&&r.contains(e))){
     const start=t.startTime(),end=t.endTime(),inside=o.windows.some(([a,b])=>start>=a-.004-1e-6&&end<=b+1e-6);
     if(!inside)problems.push({owner:o.id,problem:`writes ${name(e)} at ${start.toFixed(3)}-${end.toFixed(3)} s, outside its window`});
    }
   }
  }
 }
 return {missing:false,problems,tweens};
}

// Runs before the page's own scripts. A position that is not a number lands relative to the last tween, which can be text in another block, so no hash covers it.
// build's reader is text. This is what actually ran, whoever called it and however, shell included.
function watchPositions(){
 const unplaced=window.__unplaced=[];
 let installed;
 const wrap=g=>{
  const proto=g&&g.core&&g.core.Timeline&&g.core.Timeline.prototype;
  if(!proto||window.__positionsWatched)return;
  window.__positionsWatched=true;
  for(const [call,at] of [['to',2],['from',2],['set',2],['fromTo',3]]){
   const real=proto[call];
   proto[call]=function(...args){if(!Number.isFinite(args[at]))unplaced.push([this,call,String(args[at])]);return real.apply(this,args)};
  }
 };
 Object.defineProperty(window,'gsap',{configurable:true,enumerable:true,get:()=>installed,set(g){installed=g;wrap(g)}});
}

// The selectors that are not hidden on this frame. Runs on frames where each of them should be.
function shownRoots(selectors){
 const hidden=n=>{
  if(getComputedStyle(n).display==='contents')return false; // it has no box of its own, so its opacity hides nothing
  for(let p=n;p instanceof Element;p=p.parentElement){
   const s=getComputedStyle(p);
   if(s.display==='none'||s.visibility==='hidden'||Number(s.opacity)===0)return true;
  }
  return false;
 };
 return selectors.filter(s=>{const n=document.querySelector(s);return n&&!hidden(n)});
}

async function images(roots){
 const all=[...document.images].filter(i=>!i.complete);
 await Promise.all(all.map(i=>new Promise(res=>{i.addEventListener('load',res,{once:true});i.addEventListener('error',res,{once:true})})));
 return Object.fromEntries(Object.entries(roots).map(([id,sels])=>{
  const list=sels.flatMap(s=>[...(document.querySelector(s)?.querySelectorAll('img')||[])]);
  return [id,{count:list.length,broken:list.filter(i=>!i.complete||!i.naturalWidth).map(i=>i.getAttribute('src'))}];
 }));
}

// Values at a declared reset. Runs on that frame.
function values(rows){
 const camel=p=>p.replace(/-./g,x=>x[1].toUpperCase());
 return rows.map(([sel,prop])=>{
  const n=document.querySelector(sel);
  if(!n)return null;
  return ['display','color'].includes(prop)?getComputedStyle(n)[camel(prop)]:gsap.getProperty(n,prop);
 });
}

const html=await bundleWithLocalizedFonts(project),server=await serveStaticProjectHtml(project,html);
const errors=[],failed=[];
let browser,result;
try{
 const opened=await openSettledCompositionPage(html,server.url,{renderReadyTimeoutMs:15000,renderReadyWarningSuffix:'source conformance cannot pass',
  beforeNavigate:async page=>{
   await page.evaluateOnNewDocument(watchPositions);
   page.on('pageerror',e=>errors.push(e.message));
   page.on('response',r=>{if(r.status()>=400&&!/favicon/.test(r.url()))failed.push(`${r.status()} ${new URL(r.url()).pathname}`)});
  }});
 browser=opened.browser;
 if(opened.renderReadyTimedOut)throw Error('Composition runtime did not become ready');
 const page=opened.page;
 page.setDefaultTimeout?.(60000);
 await page.evaluate(install);
 const auditResult=await page.evaluate(audit,job.owners);
 const imageResult=await page.evaluate(images,job.image_roots);
 const started=performance.now();
 const frames={},resets={},roots={};
 const wanted=new Set([...Object.keys(job.frames),...Object.keys(job.root_frames)].map(Number));
 // In time order on one page, so the node serials cover every frame the run saw.
 for(const frame of [...wanted].sort((a,b)=>a-b)){
  await seekCompositionTimeline(page,frame/job.fps,{...DENSE_GEOMETRY_SEEK_OPTIONS,exactTime:true});
  if(job.frames[frame])frames[frame]=await page.evaluate(sels=>window.__measure(sels),job.frames[frame]);
  if(job.resets?.[frame])resets[frame]=await page.evaluate(values,job.resets[frame]);
  if(job.root_frames[frame])roots[frame]=await page.evaluate(shownRoots,job.root_frames[frame]);
 }
 result={hyperframes:PINNED,errors,failed_requests:failed,audit:auditResult,images:imageResult,frames,resets,roots_shown:roots,seek_ms:Math.round(performance.now()-started)};
}finally{
 if(browser)await browser.close();
 await server.close();
}
fs.writeFileSync(job.out+'.tmp',JSON.stringify(result));
fs.renameSync(job.out+'.tmp',job.out);
process.exit(0);
