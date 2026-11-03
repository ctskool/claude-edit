"""Decode every frame; exact hashes first, PSNR/SSIM on every frame if any differ.
python tools/beat_render/compare.py before.mp4 after.mp4 output-prefix [startA=0] [startB=0] [count]
"""
import sys,json,subprocess,pathlib,re,math
A,B,prefix=sys.argv[1:4]
sa=int(sys.argv[4]) if len(sys.argv)>4 else 0
sb=int(sys.argv[5]) if len(sys.argv)>5 else 0
count=int(sys.argv[6]) if len(sys.argv)>6 else None
out=pathlib.Path(prefix);out.parent.mkdir(parents=True,exist_ok=True)
def run(args,cwd=None):
 p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=cwd)
 if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace')[-6000:])
 return p.stdout
def probe(f):return json.loads(run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_frames,duration,start_time','-of','json',f]))['streams'][0]
def trim(start):return f'trim=start_frame={start}'+(f':end_frame={start+count}' if count is not None else '')+',setpts=PTS-STARTPTS'
pa,pb=probe(A),probe(B)
if (pa['width'],pa['height'])!=(pb['width'],pb['height']):raise RuntimeError('Comparison dimensions differ')
# Decode each input once for both frame hashes and both pixel metrics. Header frame
# counts are informational; actual comparison counts come from decoded framemd5 rows.
ps=out.name+'-psnr.txt';ss=out.name+'-ssim.txt';ah=out.name+'-a.framemd5';bh=out.name+'-b.framemd5'
graph=f'[0:v]{trim(sa)},format=yuv420p,split=3[ah][ap][ass];[1:v]{trim(sb)},format=yuv420p,split=3[bh][bp][bs];[ap][bp]psnr=stats_file={ps}:shortest=1[p];[ass][bs]ssim=stats_file={ss}:shortest=1[s]'
run(['ffmpeg','-v','error','-y','-threads','2','-i',str(pathlib.Path(A).resolve()),'-threads','2','-i',str(pathlib.Path(B).resolve()),'-filter_complex_threads','2','-filter_complex',graph,'-map','[ah]','-c:v','rawvideo','-threads:v','1','-f','framemd5',ah,'-map','[bh]','-c:v','rawvideo','-threads:v','1','-f','framemd5',bh,'-map','[p]','-map','[s]','-an','-f','null','-'],cwd=out.parent)
def hashes(label):return [l.split(',')[-1].strip() for l in pathlib.Path(prefix+f'-{label}.framemd5').read_text().splitlines() if not l.startswith('#')]
ha,hb=hashes('a'),hashes('b');diff=[i for i,(a,b) in enumerate(zip(ha,hb)) if a!=b]
r={'a':A,'b':B,'probe_a':pa,'probe_b':pb,'start_a':sa,'start_b':sb,'count_a':len(ha),'count_b':len(hb),'identical':len(ha)==len(hb) and not diff,'different_frames':len(diff),'first_different':diff[:20],'different_indices':diff}
worst=diff[0] if diff else 0
if diff and pa['width']==pb['width'] and pa['height']==pb['height']:
 pv=[float(x) for x in re.findall(r'psnr_avg:([\d.inf]+)',pathlib.Path(prefix+'-psnr.txt').read_text())]
 sv=[float(x) for x in re.findall(r'All:([\d.]+)',pathlib.Path(prefix+'-ssim.txt').read_text())]
 worst=min(range(len(pv)),key=pv.__getitem__)
 r.update(psnr_min=pv[worst],psnr_worst_frame=worst,psnr_worst_global_a=sa+worst,ssim_min=min(sv),ssim_worst_frame=min(range(len(sv)),key=sv.__getitem__),metrics_frames=len(pv))
r['extraction_hash_verified']={}
for f,start,label,expected in [(A,sa,'a',ha[worst]),(B,sb,'b',hb[worst])]:
 # Fast accurate seeking is accepted only when the selected decoded YUV hash
 # matches the already measured target frame. Otherwise fall back to decoding
 # from frame zero. This avoids minutes of redundant decoding for late beats.
 fps_text=(pa if label=='a' else pb)['r_frame_rate'];num,den=map(int,fps_text.split('/'));fps=num/den
 target=start+worst;seek_seconds=max(0,int(target//fps)-2) if den==1 else 0
 relative=target-int(seek_seconds*fps);verify=prefix+f'-worst-{label}-verify.framemd5';png=prefix+f'-worst-{label}.png'
 graph=f'[0:v]select=eq(n\\,{relative}),split=2[p][h]'
 run(['ffmpeg','-v','error','-y','-threads','2','-ss',str(seek_seconds),'-i',f,'-filter_complex_threads','1','-filter_complex',graph,'-map','[p]','-frames:v','1','-threads:v','1',png,'-map','[h]','-frames:v','1','-c:v','rawvideo','-threads:v','1','-pix_fmt','yuv420p','-f','framemd5',verify])
 verified=[line.split(',')[-1].strip() for line in pathlib.Path(verify).read_text().splitlines() if not line.startswith('#')]
 r['extraction_hash_verified'][label]=verified==[expected]
 if not r['extraction_hash_verified'][label]:
  run(['ffmpeg','-v','error','-threads','2','-i',f,'-vf',f'select=eq(n\\,{target})','-frames:v','1','-y',png])
r['extracted_frame_a']=sa+worst;r['extracted_frame_b']=sb+worst
pathlib.Path(prefix+'.json').write_text(json.dumps(r,indent=2))
print(json.dumps({k:v for k,v in r.items() if k!='different_indices'}))
