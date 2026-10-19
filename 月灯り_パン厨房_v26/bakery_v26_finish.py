import bpy,os,shutil
O=r'C:\Users\kaka\Desktop\e002素材\月灯り_パン厨房_v26'
for o in list(bpy.data.objects):
 if o.name.startswith('BK26_landing_cart'):bpy.data.objects.remove(o,do_unlink=True)
s=bpy.context.scene
bpy.data.objects['Camera_BK26_plan'].data.ortho_scale=8.5
s.camera=bpy.data.objects['Camera_BK26_inside']
note=open('bakery_v26_notes.txt',encoding='utf8').read()
t=bpy.data.texts.new('README_パン厨房_v26');t.write(note)
with open(os.path.join(O,'厨房_設計メモ.txt'),'w',encoding='utf8') as f:f.write(note)
for fn in ['bakery_v26.py','bakery_v26_finish.py']:shutil.copy2(fn,os.path.join(O,fn))
# Keep startup view focused on the revised kitchen.
from mathutils import Vector
for sc in bpy.data.screens:
 for a in sc.areas:
  if a.type=='VIEW_3D':
   a.spaces.active.region_3d.view_location=Vector((11.22,2.7,.7));a.spaces.active.region_3d.view_distance=8
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(O,'月灯り_舞台設計_パン厨房_v26.blend'))
bpy.data.libraries.write(os.path.join(O,'パン厨房差分_v26.blend'),{bpy.data.collections['31_BAKERY_Workshop_v26'],t},path_remap='ABSOLUTE',fake_user=True,compress=True)
for cam,fn in [('Camera_BK26_inside','厨房_全景.png'),('Camera_BK26_plan','厨房_配置図.png')]:
 s.camera=bpy.data.objects[cam];s.render.filepath=os.path.join(O,fn);bpy.ops.render.render(write_still=True)
print('FINAL SAVED')
