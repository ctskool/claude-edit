// Builds a media plan, for tools/beat_render/run.py. Version-pinned, and no source timeline or media timing is shifted.
// HyperFrames 0.9 plans only as Plan v2, which leaves video frames for its chunk renderer to extract. This materializes the one chunk into
// the folder render.mjs reads, then extracts every frame of each video with the engine's own call, whole and at full size, as 0.8's plan did.
//   node tools/beat_render/worker.mjs plan PROJECT OUT FPS QUALITY CRF VIDEO_FRAME_FORMAT
import fs from 'node:fs';
import path from 'node:path';
import {producer} from './hf.mjs';
import {engine} from './render.mjs';
process.env.PRODUCER_MAX_WORKERS='1';
process.env.PRODUCER_MIN_PARALLEL_FRAMES='1000000000';
const [verb,project,out,fps='30',quality='standard',crf='0',videoFrameFormat='auto']=process.argv.slice(2);
if(verb!=='plan')throw Error('Expected plan');
const started=performance.now();
const producerConfig=producer.resolveConfig({concurrency:1,minParallelFrames:1000000000,forceScreenshot:true});
const v2=path.resolve(out)+'-v2';
fs.rmSync(v2,{recursive:true,force:true});
const result=await producer.planV2(path.resolve(project),{
 width:1080,height:1920,fps:+fps,format:'mp4',quality,crf:+crf,
 maxParallelChunks:1,planDirSizeLimitBytes:60*1024**3,producerConfig,
 rejectOnSystemFonts:false,videoFrameFormat
},v2);
if(result.chunkCount!==1)throw Error(`Plan has ${result.chunkCount} chunks, expected 1`);
producer.materializePlanV2Target(v2,{role:'chunk',chunkIndex:0},path.resolve(out));
fs.rmSync(v2,{recursive:true,force:true});
const metaFile=path.join(out,'meta/videos.json');
const videos=JSON.parse(fs.readFileSync(metaFile));
for(const v of videos.extracted){
 const r=v.deferredRange;
 if(!r)continue;
 const got=await engine.extractVideoFramesRange(path.join(out,...r.sourcePath.split('/')),v.videoId,r.startTime,r.durationSeconds,
  {fps:{num:v.fps,den:1},outputDir:path.join(out,'video-frames'),format:r.format},undefined,producerConfig);
 if(got.framePaths.size!==v.totalFrames)throw Error(`${v.videoId}: extracted ${got.framePaths.size} frames, the plan expects ${v.totalFrames}`);
 delete v.deferredRange;
}
fs.writeFileSync(metaFile,JSON.stringify(videos));
console.log('BEAT_RESULT '+JSON.stringify({verb,wallMs:performance.now()-started,result}));
