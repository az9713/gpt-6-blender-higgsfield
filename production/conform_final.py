"""Conform four reviewed native shots to 108 frames each, with a final 12-frame hold."""
import json, subprocess, sys
from pathlib import Path
import cv2
import numpy as np

root=Path(__file__).resolve().parent
source=Path(sys.argv[1])
cuts=[int(x) for x in sys.argv[2].split(',')]
cap=cv2.VideoCapture(str(source))
count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
bounds=[0,*cuts,count]
assert len(bounds)==5 and all(a<b for a,b in zip(bounds,bounds[1:]))
indices=[]
for shot,(a,b) in enumerate(zip(bounds,bounds[1:])):
    moving=96 if shot==3 else 108
    indices.extend(np.rint(np.linspace(a,b-1,moving)).astype(int).tolist())
    if shot==3: indices.extend([b-1]*12)
assert len(indices)==432 and indices[-12:]==[count-1]*12
out=root/'perfume-final.mp4'
cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','bgr24','-video_size','1920x1080','-framerate','24','-i','pipe:0','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
cursor=-1
for index in indices:
    while cursor<index:
        ok,frame=cap.read()
        assert ok, f'Cannot decode frame {cursor+1}'
        cursor+=1
    assert frame.shape==(1080,1920,3)
    proc.stdin.write(frame.tobytes())
proc.stdin.close(); assert proc.wait()==0
cap.release()
metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(out)]))
s=metadata['streams']; assert len(s)==1
assert s[0]['codec_name']=='h264' and s[0]['nb_read_frames']=='432' and s[0]['r_frame_rate']=='24/1'
assert abs(float(metadata['format']['duration'])-18)<.001
(root/'final.metadata.json').write_text(json.dumps(metadata,indent=2))
(root/'timing-conform.json').write_text(json.dumps({'source':source.name,'source_frames':count,'source_shot_boundaries_zero_based':bounds,'output_cut_seconds':[4.5,9,13.5],'output_frames':432,'final_hold_frames':12,'method':'Nearest-frame per-shot resampling; no optical-flow synthesis. Last source frame held for final 12 frames.','source_frame_for_each_output':indices},indent=2))
print('Validated 432 frames, 18 seconds, 1080p24 H264, silent.')
