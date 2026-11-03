// Dump every tween of a composition's root timeline, so a source refactor can be proven to keep the animation without a render.
// node tools/beat_check/tween_dump.mjs <project> <out.json>
// Two dumps are equal when every tween keeps its targets, start, duration and vars. Failure exits non-zero, never a partial file.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {hf} from '../beat_render/hf.mjs';
const [projectArg,outArg]=process.argv.slice(2);
if(!projectArg||!outArg)throw Error('Usage: tween_dump.mjs <project> <out.json>');
const project=path.resolve(projectArg),out=path.resolve(outArg);
const {bundleWithLocalizedFonts}=await hf('bundleWithLocalizedFonts');
const {serveStaticProjectHtml}=await hf('staticProjectServer');
const {openSettledCompositionPage}=await hf('captureCompositionFrame');
// Keys sorted at every depth, so two dumps compare as plain text.
const sorted=(v)=>Array.isArray(v)?v.map(sorted):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,sorted(v[k])])):v;
const html=await bundleWithLocalizedFonts(project),server=await serveStaticProjectHtml(project,html);
let browser,tweens;
const errors=[];
try{
 const opened=await openSettledCompositionPage(html,server.url,{renderReadyTimeoutMs:15000,renderReadyWarningSuffix:'tween dump cannot pass'});
 browser=opened.browser;
 opened.page.on('pageerror',e=>errors.push(e.message));
 if(opened.renderReadyTimedOut)throw Error('Composition runtime did not become ready');
 tweens=await opened.page.evaluate(()=>{
  const tl=window.__timelines&&window.__timelines.main;
  if(!tl)throw Error('window.__timelines.main is missing');
  // An element with no id is named by its path from the nearest ancestor with one, because runtime chips have none.
  const sig=(n)=>{
   if(!(n instanceof Element))return String(n);
   const parts=[];
   for(let e=n;e;e=e.parentElement){
    if(e.id){parts.unshift('#'+e.id);break}
    const i=e.parentElement?[...e.parentElement.children].indexOf(e):0;
    parts.unshift(`${e.tagName.toLowerCase()}.${e.getAttribute('class')||''}[${i}]`);
   }
   return parts.join('>');
  };
  const clean=(v,seen)=>{
   if(typeof v==='function')return 'fn:'+v.toString();
   if(v instanceof Element)return sig(v);
   if(!v||typeof v!=='object')return v;
   if(seen.has(v))return 'cycle';
   seen.add(v);
   if(Array.isArray(v))return v.map(x=>clean(x,seen));
   return Object.fromEntries(Object.entries(v).filter(([k])=>k!=='parent').map(([k,x])=>[k,clean(x,seen)]));
  };
  return tl.getChildren(true,true,false).map(t=>({targets:t.targets().map(sig),start:t.startTime(),duration:t.duration(),vars:clean(t.vars,new Set())}));
 });
}finally{
 if(browser)await browser.close();
 await server.close();
}
if(errors.length)throw Error('Page errors: '+errors.join('; '));
if(!tweens.length)throw Error('Timeline has no tweens');
const rows=tweens.map(sorted).map(t=>({key:[t.targets.join(','),JSON.stringify(t.vars)].join('|'),t}));
rows.sort((a,b)=>a.t.start-b.t.start||(a.key<b.key?-1:a.key>b.key?1:0));
const text=JSON.stringify(rows.map(r=>r.t),null,0).replaceAll('},{"duration"','},\n{"duration"')+'\n';
fs.mkdirSync(path.dirname(out),{recursive:true});
fs.writeFileSync(out+'.tmp',text);
fs.renameSync(out+'.tmp',out);
console.log(JSON.stringify({project:projectArg,tweens:rows.length,sha256:crypto.createHash('sha256').update(text).digest('hex')}));
