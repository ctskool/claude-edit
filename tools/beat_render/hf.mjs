// The one door to HyperFrames internals. An upgrade is a re-qualification, so anything but the pin fails closed.
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const require=createRequire(import.meta.url);
export const PINNED='0.9.13';
export const dist=path.join(path.dirname(require.resolve('hyperframes/package.json')),'dist');
if(require('hyperframes/package.json').version!==PINNED)throw Error(`Beat rendering requires HyperFrames ${PINNED}`);
export async function hf(prefix){
 const files=fs.readdirSync(dist).filter(n=>n.startsWith(prefix+'-')&&n.endsWith('.js'));
 if(files.length!==1)throw Error(`Ambiguous/missing internal entry ${prefix}: ${files}`);
 return import(pathToFileURL(path.join(dist,files[0])));
}
export const producer=await (await hf('producer')).loadProducer();
