"""Encode a completed PNG range; validate decoded frame count and duration."""
import json, subprocess, sys, time
from pathlib import Path

root=Path(__file__).resolve().parent
pilot='--pilot' in sys.argv
start,count=(49,120) if pilot else (1,432)
output=root/('blender-pilot.mp4' if pilot else 'blender-guide.mp4')
deadline=time.monotonic()+1200
last=root/'frames'/f'frame_{start+count-1:04}.png'
while not last.exists():
 if time.monotonic()>deadline: raise TimeoutError(str(last))
 time.sleep(3)
time.sleep(2)
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','24','-start_number',str(start),'-i',str(root/'frames'/'frame_%04d.png'),'-frames:v',str(count),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True)
raw=subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_entries','stream=codec_name,width,height,r_frame_rate,nb_read_frames:format=duration','-of','json',str(output)])
data=json.loads(raw); stream=data['streams'][0]
assert int(stream['nb_read_frames'])==count
assert stream['width']==1920 and stream['height']==1080 and stream['r_frame_rate']=='24/1'
assert abs(float(data['format']['duration'])-count/24)<.001
output.with_suffix('.metadata.json').write_text(json.dumps(data,indent=2))
print('VALIDATED',output.name,count,'frames',count/24,'seconds',flush=True)
