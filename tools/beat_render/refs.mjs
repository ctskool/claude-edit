// Reference captures for tools/beat_render/sentinel.py. Fresh sessions only, used for a few frames each, in the render
// profile's own capture format, so a clean comparison measures the encoder and nothing else. A reference counts only if
// the same page's DOM probe passes: the fault it guards against must not be able to validate itself.
// A page can keep what a frame it landed on did, so each beat's references reach their frames as its render does: one
// session, stepping every frame from the beat's first, with only the samples photographed. Sessions turn over between beats.
//   node tools/beat_render/refs.mjs JOB.json
import fs from 'node:fs';
import path from 'node:path';
import {engine,openContext,openSession,closeSession,closeContext} from './render.mjs';

const job=JSON.parse(fs.readFileSync(process.argv[2]));

// want: {layout, chips: [owner ids], face: element id or null}. Runs in the page on the frame just captured.
function probe(W,H,want){
 const problems=[];
 const box=e=>{const r=e.getBoundingClientRect();return [r.left,r.top,r.width,r.height].map(Math.round)};
 const shown=e=>{const s=getComputedStyle(e);return s.display!=='none'&&s.visibility!=='hidden'&&+s.opacity>0};
 if(innerWidth!==W||innerHeight!==H)problems.push(`viewport ${innerWidth}x${innerHeight}`);
 const root=box(document.querySelector('[data-composition-id]'));
 if(root.join()!==[0,0,W,H].join())problems.push(`root at ${root}`);
 for(const frame of document.querySelectorAll('.__render_frame__')){
  const b=box(frame);
  if(shown(frame)&&b[2]===800&&b[3]===600)problems.push(`${frame.id} stuck at 800x600`);
 }
 if(want.layout==='split'){
  const wrap=box(document.getElementById('face-wrap'));
  if(wrap.join()!==[0,H/2,W,H/2].join())problems.push(`face layer at ${wrap}`);
 }
 if(want.face){
  const el=document.getElementById(want.face);
  if(!el)problems.push(`${want.face} missing`);
  else{
   const b=box(el);
   if(b[2]<W||b[3]<H/2)problems.push(`${want.face} at ${b}`);
  }
 }
 for(const id of want.chips){
  const chip=document.querySelector(`[data-own="${id}"]`);
  if(!chip)problems.push(`${id} missing`);
  else{
   const b=box(chip);
   if(!shown(chip)||b[2]<=0||b[3]<=0||!chip.textContent.trim())problems.push(`${id} not visible at ${b}`);
  }
 }
 return problems;
}

const ctx=await openContext(job),quality=ctx.profile.capture.quality;
let session=null,used=0,beat=null,next=0;
try{
 for(const r of job.frames){
  if(r.beat!==beat){
   if(session&&used>=job.page_frames){await closeSession(session);session=null;}
   beat=r.beat;next=r.from;
  }
  if(!session){session=await openSession(ctx,ctx.profile.capture.format,quality);used=0;}
  const between=[];
  for(let f=next;f<r.frame;f++)between.push(f/ctx.fps);
  if(between.length)await session.page.evaluate(times=>{for(const t of times)window.__hf.seek(t)},between);
  next=r.frame+1;
  const {buffer}=await engine.captureFrameToBuffer(session,r.frame,r.frame/ctx.fps);
  const problems=await session.page.evaluate(probe,ctx.width,ctx.height,r.want);
  if(ctx.errors.length)problems.push('page errors: '+ctx.errors.join('; '));
  used++;
  // A reference with its receipt, or neither. Python treats a file with no receipt as absent.
  fs.mkdirSync(path.dirname(r.out),{recursive:true});
  fs.writeFileSync(r.out+'.tmp',buffer);fs.renameSync(r.out+'.tmp',r.out);
  fs.writeFileSync(r.out+'.json.tmp',JSON.stringify({frame:r.frame,want:r.want,problems,stepped_from:r.from}));fs.renameSync(r.out+'.json.tmp',r.out+'.json');
 }
 console.log('REFS_RESULT',job.frames.length,ctx.boots,Math.round(ctx.bootMs));
}finally{
 if(session)await closeSession(session).catch(e=>console.error('CLOSE_FAILED',e));
 closeContext(ctx);
}
process.exit(0);
