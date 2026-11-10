// Capture worker for tools/beat_render/run.py. Absolute frames over the pinned HyperFrames engine: seek, media
// injector, screenshot API. The composition's dimensions, timeline and media timing stay unchanged.
//   node tools/beat_render/render.mjs prepare JOB.json   compile the page, check it against the plan, report the browser
//   node tools/beat_render/render.mjs capture JOB.json   render ranges to separate closed-GOP files
// --inject-fault is for tests only: it changes what a page shows, and a run that used it says so.
import fs from 'node:fs';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import crypto from 'node:crypto';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {hf,producer,dist,PINNED} from './hf.mjs';
import {buildVirtualTimeShim} from './virtual-time.mjs';

// run.py samples what it needs. Avoid a second per-browser sampler inside a timed run.
process.env.HF_CHROME_MEMORY_SAMPLER='false';

// Discover the engine entry by its public capture API rather than a hashed filename.
const engineFiles=fs.readdirSync(dist).filter(n=>/^src-.*\.js$/.test(n)&&fs.readFileSync(path.join(dist,n),'utf8').includes('createFrameLookupTable,')&&fs.readFileSync(path.join(dist,n),'utf8').includes('captureFrameToBuffer,'));
if(engineFiles.length!==1)throw Error('Engine entry discovery failed: '+engineFiles);
export const engine=await import(pathToFileURL(path.join(dist,engineFiles[0])));

const digest=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const writeJson=(file,value)=>{fs.writeFileSync(file+'.tmp',JSON.stringify(value,null,1));fs.renameSync(file+'.tmp',file);};

export function loadPlan(planDir){
 const plan=path.resolve(planDir);
 const p=JSON.parse(fs.readFileSync(path.join(plan,'plan.json')));
 if(p.dimensions.fpsDen!==1||!Number.isInteger(p.dimensions.fpsNum)||p.dimensions.fpsNum<1)throw Error('Only integer frame rates are qualified');
 const videos=JSON.parse(fs.readFileSync(path.join(plan,'meta/videos.json')));
 if(videos.extracted.some(v=>v.deferredRange))throw Error('Deferred video extraction is not qualified');
 const extracted=videos.extracted.map(v=>{
  const dir=path.join(plan,'video-frames',v.videoId);
  const files=fs.readdirSync(dir).filter(n=>/\.(png|jpg)$/.test(n)).sort((a,b)=>+a.match(/\d+/)[0]-+b.match(/\d+/)[0]);
  return {...v,outputDir:dir,framePaths:new Map(files.map((n,i)=>[i,path.join(dir,n)])),ownedByLookup:false};
 });
 return {plan,p,videos,lookup:engine.createFrameLookupTable(videos.videos,extracted,p.dimensions.fpsNum)};
}

// The compiled page may differ from the plan's only in what the plan does not fix. Timing or media changes need a new plan.
async function compilePage(project,planned,compiledDir){
 const {bundleWithLocalizedFonts}=await hf('bundleWithLocalizedFonts');
 const html=await bundleWithLocalizedFonts(project);
 // Compare authored metadata to the immutable authored snapshot, not the normalized extraction schedule.
 const authored=engine.parseVideoElements(html);
 const previous=engine.parseVideoElements(fs.readFileSync(path.join(planned.plan,'compiled/index.html'),'utf8'));
 if(JSON.stringify(authored)!==JSON.stringify(previous))throw Error('Media metadata changed; rebuild plan');
 for(const src of new Set(planned.videos.videos.map(v=>v.src))){
  if(/^[a-z]+:/i.test(src))throw Error('Remote media is not qualified');
  if(digest(path.join(project,src))!==digest(path.join(planned.plan,'compiled',src)))throw Error('Video asset changed; rebuild extraction plan: '+src);
 }
 fs.mkdirSync(compiledDir,{recursive:true});
 fs.writeFileSync(path.join(compiledDir,'index.html'),html);
}

export async function openContext(job){
 const planned=loadPlan(job.plan),{p}=planned,profile=job.profile,fps=profile.fps;
 if(fps!==p.dimensions.fpsNum)throw Error(`Profile fps ${fps} is not the plan's ${p.dimensions.fpsNum}`);
 const project=path.resolve(job.project),compiledDir=path.resolve(job.compiled);
 const scratch=path.resolve(job.scratch);
 const cfg=engine.resolveConfig({browserGpuMode:profile.capture.gpu,forceScreenshot:true,useDrawElement:false,enableBrowserPool:false,concurrency:1});
 const server=await producer.createFileServer({projectDir:project,compiledDir,port:0,fps:{num:fps,den:1},preHeadScripts:[buildVirtualTimeShim({seedRandomFromFrame:true})]});
 // Producer's server closes owned keep-alive sockets on shutdown, which the engine's lighter server does not.
 const frameServer=await producer.createFileServer({projectDir:planned.plan,port:0});
 return {...planned,profile,fps,scratch,cfg,server,frameServer,errors:[],boots:0,bootMs:0,width:p.dimensions.width,height:p.dimensions.height};
}

export async function openSession(ctx,format,quality){
 const started=performance.now();
 // The injector remembers what this page shows, so it never outlives its page.
 const injector=engine.createVideoFrameInjector(ctx.lookup,{frameSrcResolver:file=>ctx.frameServer.url+'/'+path.relative(ctx.plan,file).replaceAll('\\','/')});
 const session=await engine.createCaptureSession(ctx.server.url,ctx.scratch,{width:ctx.width,height:ctx.height,fps:{num:ctx.fps,den:1},format,quality,deviceScaleFactor:ctx.profile.dpr,lockWarmupTicks:true},injector,ctx.cfg);
 session.page.on('pageerror',e=>ctx.errors.push(e.message));
 await engine.initializeSession(session);
 const bounds=await session.page.evaluate(()=>{const r=document.querySelector('[data-composition-id]');return {width:+r.getAttribute('data-width'),height:+r.getAttribute('data-height'),fps:+r.getAttribute('data-fps'),duration:+r.getAttribute('data-duration')}});
 if(bounds.width!==ctx.width||bounds.height!==ctx.height||bounds.fps!==ctx.fps||Math.abs(bounds.duration-ctx.p.duration)>1e-6)throw Error('Composition bounds changed; rebuild plan and frame partitions');
 ctx.boots++;ctx.bootMs+=performance.now()-started;
 return session;
}

export const closeSession=session=>engine.closeCaptureSession(session);
export const closeContext=ctx=>{ctx.server.close();ctx.frameServer.close();};
export const viewportOf=page=>page.evaluate(()=>[window.innerWidth,window.innerHeight]);

// Shows the observed whole-render fault, or stops the worker, partway through a range.
const FAULT_CSS='#face,.ffull,.__render_frame__{position:fixed!important;left:0!important;top:0!important;width:800px!important;height:600px!important;object-fit:none!important;object-position:50% 50%!important;z-index:9!important}#face-wrap{overflow:visible!important}#caps{display:none!important}';
async function applyFault(ctx,session,kind){
 console.log('INJECT_FAULT',kind);
 if(kind==='viewport'||kind==='clear'){
  const client=await session.page.createCDPSession();
  if(kind==='viewport')await client.send('Emulation.setDeviceMetricsOverride',{width:800,height:600,deviceScaleFactor:ctx.profile.dpr,mobile:false});
  else await client.send('Emulation.clearDeviceMetricsOverride');
 }else if(kind==='dom')await session.page.addStyleTag({content:FAULT_CSS});
 else if(kind==='gpu'){const client=await session.browser.target().createCDPSession();await client.send('Browser.crashGpuProcess').catch(()=>{});}
 else if(kind==='crash')session.browser.process()?.kill('SIGKILL');
 else throw Error('Unknown fault: '+kind);
}

async function rotate(ctx,state){
 await closeSession(state.session);
 state.session=await openSession(ctx,'jpeg',ctx.profile.capture.quality);
 state.pageFrames=0;
}

async function captureRange(ctx,state,range,job){
 const {profile,fps}=ctx,enc=profile.encoder,threads=profile.threads,count=range.end-range.start,file=path.resolve(range.path);
 const args=engine.buildEncoderArgs({fps:{num:fps,den:1},width:Math.round(ctx.width*profile.dpr),height:Math.round(ctx.height*profile.dpr),codec:'h264',preset:enc.preset,quality:enc.crf,pixelFormat:enc.pix_fmt,lockGopForChunkConcat:true,gopSize:count},['-v','error','-filter_threads',String(threads.filter),'-threads',String(threads.decoder),'-f','image2pipe','-vcodec','mjpeg','-framerate',String(fps),'-i','pipe:0','-threads',String(threads.encoder)],file);
 // 0.9 appends x264's thread count as the machine's core count, after ours, so it wins and changes the bits. Drop it: the profile's count holds, as on 0.8.
 const extra=args.indexOf('-threads',args.indexOf('-c:v'));
 if(extra<0)throw Error('Expected the engine to set its own x264 thread count');
 args.splice(extra,2);
 const encoder=spawn('ffmpeg',args,{stdio:['pipe','ignore','pipe'],windowsHide:true});
 state.encoder=encoder;
 let stderr='',broken=null;encoder.stderr.on('data',x=>stderr+=x);
 encoder.stdin.on('error',e=>broken=e);
 const completed=new Promise((res,rej)=>{encoder.on('error',rej);encoder.on('exit',code=>code===0?res():rej(Error('Encoder failed: '+stderr)))});
 completed.catch(()=>{});
 const before=state.pageFrames,started=performance.now();
 const fault=range.inject,faultFrame=fault?range.start+(fault.offset??Math.floor(count/2)):-1;
 // Rotation lands on a beat boundary. This cap only matters to a beat longer than twice the rotation.
 const cap=job.page_rotate_frames*2;
 for(let frame=range.start;frame<range.end;frame++){
  if(cap>0&&state.pageFrames>=cap)await rotate(ctx,state);
  if(frame===faultFrame)await applyFault(ctx,state.session,fault.kind);
  const {buffer}=await engine.captureFrameToBuffer(state.session,frame,frame/fps);
  if(broken)throw broken;
  if(!encoder.stdin.write(buffer))await once(encoder.stdin,'drain');
  state.pageFrames++;
  if((frame-range.start+1)%120===0)console.log('CAPTURE_PROGRESS',range.id,frame-range.start+1,count,Math.round(performance.now()-started));
 }
 const captureMs=performance.now()-started,viewport=await viewportOf(state.session.page);
 encoder.stdin.end();await completed;state.encoder=null;
 if(ctx.errors.length)throw Error('Browser errors: '+ctx.errors.join('; '));
 if(!fault&&(viewport[0]!==ctx.width||viewport[1]!==ctx.height))throw Error(`Viewport changed during capture: ${viewport}`);
 writeJson(file+'.json',{id:range.id,start:range.start,end:range.end,frames:count,page_frames_before:before,page_frames_after:state.pageFrames,viewport,capture_ms:Math.round(captureMs),injected:fault?.kind??null});
 console.log('BEAT_RESULT',range.id,count,Math.round(captureMs));
}

async function capture(job){
 const ctx=await openContext(job),state={session:null,pageFrames:0,encoder:null},rotateAt=job.page_rotate_frames;
 const started=performance.now();
 let current=null;
 try{
  for(const range of job.ranges){
   current=range;
   if(state.session&&(job.fresh||(rotateAt>0&&state.pageFrames>=rotateAt))){await closeSession(state.session);state.session=null;}
   if(!state.session){state.session=await openSession(ctx,'jpeg',ctx.profile.capture.quality);state.pageFrames=0;}
   await captureRange(ctx,state,range,job);
  }
  writeJson(job.result,{wall_ms:Math.round(performance.now()-started),boots:ctx.boots,boot_ms:Math.round(ctx.bootMs)});
 }catch(error){
  if(current)writeJson(path.resolve(current.path)+'.error.json',{id:current.id,error:String(error)});
  console.error('WORKER_FAILED',current?.id,error);
  process.exitCode=1;
 }finally{
  if(state.encoder&&!state.encoder.killed)state.encoder.kill();
  if(state.session)await closeSession(state.session).catch(e=>console.error('CLOSE_FAILED',e));
  closeContext(ctx);
 }
}

async function prepare(job){
 const planned=loadPlan(job.plan);
 await compilePage(path.resolve(job.project),planned,path.resolve(job.compiled));
 const ctx=await openContext(job);
 const session=await engine.createCaptureSession(ctx.server.url,ctx.scratch,{width:ctx.width,height:ctx.height,fps:{num:ctx.fps,den:1},format:'jpeg',quality:80,deviceScaleFactor:job.profile.dpr},null,ctx.cfg);
 const chrome=await session.browser.version();
 await closeSession(session);closeContext(ctx);
 writeJson(job.result,{hyperframes:PINNED,chrome,compiled_sha256:digest(path.join(job.compiled,'index.html'))});
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const [verb,jobFile]=process.argv.slice(2);
 const job=JSON.parse(fs.readFileSync(jobFile));
 if(verb==='prepare')await prepare(job);
 else if(verb==='capture')await capture(job);
 else throw Error('Expected prepare or capture');
 process.exit(process.exitCode??0);
}
