// Builds a media plan, for tools/beat_render/run.py. Version-pinned, and no source timeline or media timing is shifted.
//   node tools/beat_render/worker.mjs plan PROJECT OUT FPS QUALITY CRF VIDEO_FRAME_FORMAT
import path from 'node:path';
import {producer} from './hf.mjs';
process.env.PRODUCER_MAX_WORKERS='1';
process.env.PRODUCER_MIN_PARALLEL_FRAMES='1000000000';
const [verb,project,out,fps='30',quality='standard',crf='0',videoFrameFormat='auto']=process.argv.slice(2);
if(verb!=='plan')throw Error('Expected plan');
const started=performance.now();
const result=await producer.plan(path.resolve(project),{
 width:1080,height:1920,fps:+fps,format:'mp4',quality,crf:+crf,
 maxParallelChunks:1,planDirSizeLimitBytes:60*1024**3,
 producerConfig:producer.resolveConfig({concurrency:1,minParallelFrames:1000000000,forceScreenshot:true}),
 rejectOnSystemFonts:false,videoFrameFormat
},path.resolve(out));
console.log('BEAT_RESULT '+JSON.stringify({verb,wallMs:performance.now()-started,result}));
