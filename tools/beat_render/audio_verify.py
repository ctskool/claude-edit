import sys,json,subprocess,hashlib,pathlib
import numpy as np
a,b,prefix=sys.argv[1:4]
def run(args):return subprocess.check_output(args,stderr=subprocess.PIPE)
def pcm(file):return run(['ffmpeg','-v','error','-i',file,'-map','0:a:0','-ac','1','-ar','48000','-f','s16le','-'])
def probe(file):return json.loads(run(['ffprobe','-v','error','-show_entries','stream=index,codec_type,start_time,duration,time_base,sample_rate,channels,nb_frames,has_b_frames','-of','json',file]))
def audio_packets(file):return json.loads(run(['ffprobe','-v','error','-select_streams','a:0','-show_entries','packet=data_hash','-show_data_hash','sha256','-of','json',file]))['packets']
pa,pb=pcm(a),pcm(b);xa=np.frombuffer(pa,dtype='<i2');xb=np.frombuffer(pb,dtype='<i2');n=min(len(xa),len(xb))
qa,qb=probe(a),probe(b)
if any(s.get('has_b_frames',0) for s in qb['streams'] if s['codec_type']=='video'):raise RuntimeError('PTS audit requires the spike no-B-frame profile')
frames=json.loads(run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','packet=pts_time,dts_time','-of','json',b]))['packets']
pts=np.array([float(f['pts_time']) for f in frames]);delta=np.diff(pts)
r={'a':a,'b':b,'probe_a':qa,'probe_b':qb,'pcm_md5_a':hashlib.md5(pa).hexdigest(),'pcm_md5_b':hashlib.md5(pb).hexdigest(),'pcm_identical':pa==pb,'samples_a':len(xa),'samples_b':len(xb),'different_samples_common':int(np.count_nonzero(xa[:n]!=xb[:n])),'video_frames':len(frames),'video_pts_source':'packet PTS; no B-frames, decoded coverage separately verified by compare.py','first_video_pts':float(pts[0]),'last_video_pts':float(pts[-1]),'min_frame_delta':float(delta.min()),'max_frame_delta':float(delta.max()),'non_increasing_pts':int(np.count_nonzero(delta<=0))}
# FFT cross-correlation over a speaking window measures source-to-output lag.
N=min(144000,n);xx=xa[:N].astype(float);yy=xb[:N].astype(float);size=1<<(2*N-1).bit_length()
c=np.fft.irfft(np.fft.rfft(yy,size)*np.conj(np.fft.rfft(xx,size)),size)
lags=np.arange(-2400,2401);values=c[lags%size];lag=int(lags[np.argmax(values)])
r['best_audio_lag_samples']=lag;r['best_audio_lag_ms']=lag/48
ap,bp=audio_packets(a),audio_packets(b)
r['audio_packet_count_a']=len(ap);r['audio_packet_count_b']=len(bp)
r['audio_payloads_identical']=bool(ap) and all('data_hash' in x for x in ap+bp) and [x['data_hash'] for x in ap]==[x['data_hash'] for x in bp]
r['window_lags']=[]
for start in sorted(set([0,max(0,n//4-N//2),max(0,n//2-N//2),max(0,3*n//4-N//2),max(0,n-N)])):
 xx=xa[start:start+N].astype(float);yy=xb[start:start+N].astype(float)
 corr=np.fft.irfft(np.fft.rfft(yy,size)*np.conj(np.fft.rfft(xx,size)),size)
 local_lag=int(lags[np.argmax(corr[lags%size])])
 r['window_lags'].append({'start_seconds':start/48000,'samples':len(xx),'lag_samples':local_lag,'lag_ms':local_lag/48})
pathlib.Path(prefix+'.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
