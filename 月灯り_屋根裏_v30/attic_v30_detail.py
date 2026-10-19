import bpy,os,math,shutil
from mathutils import Vector
O=r'C:\Users\kaka\Desktop\e002素材\月灯り_屋根裏_v30'
c=bpy.data.collections['41_ATTIC_American_storage_v30']
wood=bpy.data.materials['AT30_walnut'];metal=bpy.data.materials['AT30_aged_brass'];cloth=bpy.data.materials['AT30_dust_sheets']
def rod(n,a,b,r,m):
 d=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=r,depth=d.length,location=(Vector(a)+Vector(b))/2);o=bpy.context.object;o.name=n;o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
 for cc in list(o.users_collection):cc.objects.unlink(o)
 c.objects.link(o);o.data.materials.append(m);return o
rod('AT30_old_clothes_rail',(7.33,10.55,4.42),(7.33,11.96,4.42),.014,metal)
for yy in [10.63,11.83]:rod('AT30_clothes_bracket',(7.19,yy,4.43),(7.36,yy,4.43),.012,metal)
for i,y in enumerate([10.85,11.30,11.73]):
 rod('AT30_hanger',(7.34,y-.19,4.27),(7.34,y,4.40),.009,wood);rod('AT30_hanger',(7.34,y,4.40),(7.34,y+.19,4.27),.009,wood)
 # Shirt / dust coat outline, including sleeves, not a rectangular sheet.
 yz=[(-.055,4.33),(-.20,4.27),(-.28,4.04),(-.18,4.00),(-.13,4.13),(-.13,3.75),(.14,3.72),(.13,4.13),(.18,4.00),(.28,4.05),(.19,4.28),(.055,4.33),(.035,4.25),(-.035,4.25)]
 me=bpy.data.meshes.new('coat');me.from_pydata([(7.37,y+v,z) for v,z in yz],[],[tuple(range(len(yz)))]);ob=bpy.data.objects.new('AT30_stored_coat',me);c.objects.link(ob);me.materials.append(cloth);md=ob.modifiers.new('fabric thickness','SOLIDIFY');md.thickness=.015
 for j in range(4):rod('AT30_coat_button',(7.382,y,4.13-j*.085),(7.390,y,4.13-j*.085),.008,metal)
# Slightly angled empty frames behind the settee.
for x,z,w,h,ang in [(12.66,4.48,.38,.51,-.09),(13.23,4.39,.43,.38,.07)]:
 root=bpy.data.objects.new('AT30_kept_wall_frame',None);c.objects.link(root);root.location=(x,14.055,z);root.rotation_euler.y=ang
 for a,b in [((-w/2,0,-h/2),(w/2,0,-h/2)),((-w/2,0,h/2),(w/2,0,h/2)),((-w/2,0,-h/2),(-w/2,0,h/2)),((w/2,0,-h/2),(w/2,0,h/2))]:
  ob=rod('AT30_frame',a,b,.018,wood);ob.parent=root
s=bpy.context.scene;s.camera=bpy.data.objects['Camera_AT30_storage'];bpy.ops.wm.save_as_mainfile(filepath=os.path.join(O,'月灯り_舞台設計_屋根裏_v30.blend'))
for ca,fn in [('Camera_AT30_storage','屋根裏_雑多な収納.png'),('Camera_AT30_moon','屋根裏_布団と月明かり.png')]:
 s.camera=bpy.data.objects[ca];s.render.filepath=os.path.join(O,fn);bpy.ops.render.render(write_still=True)
shutil.copy2('attic_v30_detail.py',O)
