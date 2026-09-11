"""Read-only inspection inside Blender. Does not save, modify objects, or render."""
import bpy, json
s=bpy.context.scene
result={'blender':bpy.app.version_string,'file':bpy.data.filepath,
        'frames':[s.frame_start,s.frame_end],'fps':s.render.fps,
        'resolution':[s.render.resolution_x,s.render.resolution_y],
        'active_camera':s.camera.name if s.camera else None,
        'camera_markers':[{'frame':m.frame,'camera':m.camera.name} for m in s.timeline_markers if m.camera],
        'cameras':[o.name for o in s.objects if o.type=='CAMERA'],
        'meshes':sum(o.type=='MESH' for o in s.objects)}
assert result['frames']==[1,432] and len(result['cameras'])==4
print('LEARNING_INSPECTION='+json.dumps(result))
