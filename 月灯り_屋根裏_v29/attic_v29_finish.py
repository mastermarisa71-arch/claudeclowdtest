import bpy,os,math,shutil
from mathutils import Vector
O=r'C:\Users\kaka\Desktop\e002素材\月灯り_屋根裏_v29'
c=bpy.data.collections['36_ATTIC_Wide_room_v29'];roofco=bpy.data.collections['37_ATTIC_Roof_toggle_v29'];m=bpy.data.materials['AT29_plaster'];slate=bpy.data.materials['AT29_roof']
for name in ['AT29_north_left','AT29_north_right']:
 ob=bpy.data.objects[name];ob.location.z=3.725;ob.dimensions.z=1.65
for name in ['AT29_north_left_top','AT29_north_right_top']:
 ob=bpy.data.objects[name]
 for v in ob.data.vertices:
  if abs(v.co.z-5.05)<.001:v.co.z=4.55
bpy.data.objects['AT29_moon'].location.x=14.0
fill=bpy.data.collections.new('40_ATTIC_Surrounding_roof_v29');bpy.context.scene.collection.children.link(fill)
def roof(n,x0,x1,y0,y1,z0,z1):
 me=bpy.data.meshes.new(n);me.from_pydata([(x0,y0,z0),(x1,y0,z1),(x1,y1,z1),(x0,y1,z0)],[],[(0,1,2,3)]);ob=bpy.data.objects.new(n,me);fill.objects.link(ob);me.materials.append(slate);md=ob.modifiers.new('thickness','SOLIDIFY');md.thickness=.08
roof('AT29_roof_void_west',-.20,3.4,-.2,14.38,2.85,3.65);roof('AT29_roof_void_west_inner',3.4,7.02,-.2,14.38,3.65,3.0)
roof('AT29_roof_void_south1',7.02,10.53,-.2,9.5,3.0,3.65);roof('AT29_roof_void_south2',10.53,14.06,-.2,9.5,3.65,3.0)
s=bpy.context.scene;ctl=bpy.data.objects['AT29_SlidingDoor_Control'];f=s.frame_current
for val in [0.,1.]:
 ctl['open']=val;ctl.update_tag();s.frame_set(f+1);s.frame_set(f);bpy.context.view_layer.update();print('SLIDING',val,[round(bpy.data.objects['AT29_slider_'+str(i)].location.x,3) for i in range(1,4)])
s.camera=bpy.data.objects['Camera_AT29_sleepover']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(O,'月灯り_舞台設計_屋根裏_v29.blend'))
for ca,fn in [('Camera_AT29_sleepover','屋根裏_月明かりと布団.png'),('Camera_AT29_from_stairs','屋根裏_階段側から.png')]:
 s.camera=bpy.data.objects[ca];s.render.filepath=os.path.join(O,fn);bpy.ops.render.render(write_still=True)
# Plan uses a brighter inspection light; only the render is affected.
roofco.hide_render=True
old=[(o,o.hide_render) for o in c.objects if o.name.startswith(('AT29_rafter','AT29_ridge'))]
for o,_ in old:o.hide_render=True
ld=bpy.data.lights.new('inspection','AREA');lo=bpy.data.objects.new('inspection',ld);s.collection.objects.link(lo);lo.location=(10.5,12,8);ld.energy=500;ld.size=5
s.camera=bpy.data.objects['Camera_AT29_plan'];s.render.filepath=os.path.join(O,'屋根裏_5人の配置.png');bpy.ops.render.render(write_still=True)
bpy.data.objects.remove(lo,do_unlink=True)
for o,h in old:o.hide_render=h
roofco.hide_render=False
shutil.copy2('attic_v29_finish.py',O)
print('FINAL V29')
