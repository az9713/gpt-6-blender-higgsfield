import bpy, json
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parent
s=bpy.context.scene
boxes=[]
for o in s.objects:
 if o.type!='MESH': continue
 eo=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
 points=[eo.matrix_world@Vector(v) for v in eo.bound_box]
 boxes.append((o.name,[min(v[i] for v in points) for i in range(3)],[max(v[i] for v in points) for i in range(3)]))
minimum=1e9
for f in range(1,433):
 s.frame_set(f); c=bpy.data.objects[f'Shot {min((f-1)//108,3)+1}']
 for name,lo,hi in boxes:
  distance=sum(max(lo[i]-c.location[i],0,c.location[i]-hi[i])**2 for i in range(3))**.5
  assert distance>.10,(f,name,distance)
  minimum=min(minimum,distance)
x=json.loads((p/'blender-validation-summary.json').read_text())
x['minimum_camera_to_object_aabb_clearance']=minimum
x['validation_limits']='All 432 camera positions are at least 0.10 scene metres outside every mesh world AABB. Product bounds, fixed transforms and sightline checks passed. Exact screen-space velocity matching is not numerically certified.'
(p/'blender-validation-summary.json').write_text(json.dumps(x,indent=2))
print('CAMERA CLEARANCE PASS',minimum)
