"""Approved perfume previz. Run with Blender; --render renders all frames."""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'production'
OUT.mkdir(exist_ok=True)
(OUT/'frames').mkdir(exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
s=bpy.context.scene
s.render.engine='CYCLES'
s.cycles.samples=8
s.cycles.use_denoising=True
s.cycles.denoiser='OPTIX'
s.render.use_persistent_data=True
s.render.resolution_x=1920; s.render.resolution_y=1080
s.render.resolution_percentage=100
s.render.fps=24; s.frame_start=1; s.frame_end=432
s.render.image_settings.file_format='PNG'; s.render.image_settings.color_mode='RGB'
s.world=bpy.data.worlds.new('Cool sky')
s.world.use_nodes=True
s.world.node_tree.nodes['Background'].inputs[0].default_value=(.36,.43,.55,1)
s.world.node_tree.nodes['Background'].inputs[1].default_value=.45
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences
 prefs.compute_device_type='OPTIX'; prefs.get_devices()
 for d in prefs.devices: d.use=d.type=='OPTIX'
 if any(d.use for d in prefs.devices): s.cycles.device='GPU'
except Exception: pass

def mat(name,color):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=.85
 return m
grey=mat('Matte grey',(.43,.43,.43)); red=mat('Front label red',(.65,.018,.012)); green=mat('Sides green',(.025,.32,.065)); black=mat('Back black',(.015,.015,.015))
def cube(name,loc,scale,material=grey,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.name=name; o.dimensions=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(material)
 if bevel:
  mod=o.modifiers.new('Rounded edges','BEVEL'); mod.width=bevel; mod.segments=4
  o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o
cube('Dry sand',(0,0,-.13),(100,100,.25))
cube('Driftwood plinth',(0,0,.16),(1.6,.85,.32),bevel=.10)
body=cube('Bottle body',(0,0,.82),(.82,.34,1.0),green,.16)
neck=cube('Bottle neck',(0,0,1.36),(.23,.20,.15),green,.06)
cap=cube('Oval gold-cap proxy',(0,0,1.52),(.44,.29,.20),green,.09)
front=cube('Front red label',(0,-.176,.82),(.48,.014,.48),red,.012)
back=cube('Black back',(0,.176,.82),(.48,.014,.48),black,.012)
product=[body,neck,cap,front,back]
for i in range(10):
 o=cube(f'Timber post {i+1:02}',((i-4.5)*.72,2.3,.67),(.14,.16,1.34),bevel=.025)
 o.rotation_euler[1]=math.radians((i%3-1)*3)
for i,(x,y,z) in enumerate([(-2,1,.22),(2.2,.8,.18),(-3,-1,.15),(3,3,.32),(-1.4,4,.2),(1.7,-.6,.12)]):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,y,z*.55)); o=bpy.context.object; o.name=f'Rock {i+1}'; o.scale=(z*1.8,z*1.3,z); o.data.materials.append(grey)
for i in range(7):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=((i-3)*6,12+math.sin(i)*1.2,-.35))
 o=bpy.context.object; o.name=f'Dune ridge {i}'; o.scale=(5,2.4,1.0+.2*math.sin(i)); o.data.materials.append(grey)
bpy.ops.object.light_add(type='SUN',location=(-8,-6,5)); sun=bpy.context.object; sun.name='Fixed golden-hour sun'
sun.rotation_euler=Vector((5,7,-2)).to_track_quat('-Z','Y').to_euler(); sun.data.energy=2.1; sun.data.angle=.10; sun.data.color=(1,.78,.52)
bpy.ops.object.empty_add(location=(0,0,.87)); target=bpy.context.object; target.name='Stationary camera target'

def smooth(t): return t*t*(3-2*t)
def azimuth(f):
 t=min(1,max(0,(f-1)/419))
 return math.radians(-135+45*smooth(t))
shots=[(1,108,7.8,6.8,.65,.80,38),(109,216,5.5,4.9,1.05,1.75,42),(217,324,6.2,5.7,2.5,4.0,40),(325,432,4.8,3.9,2.05,1.02,42)]
cameras=[]
for n,(start,end,r0,r1,z0,z1,lens) in enumerate(shots,1):
 bpy.ops.object.camera_add(); c=bpy.context.object; c.name=f'Shot {n}'; c.data.lens=lens; c.data.clip_start=.05; c.data.clip_end=200
 con=c.constraints.new('TRACK_TO'); con.target=target; con.track_axis='TRACK_NEGATIVE_Z'; con.up_axis='UP_Y'
 for f in range(start,end+1):
  t=(f-start)/((420 if n==4 else end)-start); t=min(1,t); u=smooth(t)
  a=azimuth(f); radius=r0+(r1-r0)*u
  c.location=(radius*math.cos(a),radius*math.sin(a),z0+(z1-z0)*u)
  c.keyframe_insert(data_path='location',frame=f)
 marker=s.timeline_markers.new(c.name,frame=start); marker.camera=c; cameras.append(c)
s.camera=cameras[0]
baseline={o.name:[list(row) for row in o.matrix_world] for o in product}
checks=[]; errors=[]
for f in range(1,433):
 s.frame_set(f); c=cameras[min((f-1)//108,3)]; s.camera=c
 deps=bpy.context.evaluated_depsgraph_get()
 bounds=[]
 for o in product:
  eo=o.evaluated_get(deps)
  assert [list(row) for row in o.matrix_world]==baseline[o.name],o.name
  bounds += [world_to_camera_view(s,c,eo.matrix_world@Vector(v)) for v in eo.bound_box]
 margin=min(min(v.x,1-v.x,v.y,1-v.y) for v in bounds)
 if margin<.05 or min(v.z for v in bounds)<=0: errors.append({'frame':f,'margin':margin})
 # Exact ray cast from camera to target detects intervening geometry.
 direction=target.location-c.location
 hit,loc,normal,face,obj,matrix=s.ray_cast(deps,c.location,direction.normalized(),distance=direction.length)
 if hit and obj.name not in [o.name for o in product]: errors.append({'frame':f,'occluder':obj.name})
 checks.append({'frame':f,'shot':c.name,'azimuth_deg':math.degrees(azimuth(f)),'margin':margin,'camera':list(c.location)})
(OUT/'camera-validation.json').write_text(json.dumps({'errors':errors,'frames':checks,'assumptions':'Bottle height 1.31 scene metres including cap; stylized product scale. Depth .34 inferred from a single front view.','engine':s.render.engine,'device':s.cycles.device},indent=2))
assert not errors,errors[:8]
s.frame_set(1); s.camera=cameras[0]
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'perfume-world.blend'))
if '--render' in sys.argv:
 s.render.filepath=str(OUT/'frames'/'frame_'); bpy.ops.render.render(animation=True)
else:
 for f in [1,108,109,216,217,324,325,420]:
  s.frame_set(f); s.camera=cameras[min((f-1)//108,3)]; s.render.resolution_percentage=40
  s.render.filepath=str(OUT/f'preview-{f:03}.png'); bpy.ops.render.render(write_still=True)
print('VALIDATED 432 FRAMES')

