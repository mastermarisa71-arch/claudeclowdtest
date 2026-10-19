import bpy,os,random,math
from mathutils import Vector
random.seed(319)
O=r'C:\Users\kaka\Desktop\e002素材\月灯り_屋根裏_v31';c=bpy.data.collections['42_ATTIC_Expanded_store_v31'];s=bpy.context.scene;bpy.context.view_layer.update()
occupied=[]
for o in bpy.data.objects:
 if o.type!='MESH' or not o.name.startswith(('AT31_stock','AT31_case_board','AT31_stored_tabletop','AT31_old','AT31_antique')):continue
 pts=[o.matrix_world@Vector(p) for p in o.bound_box];mn=[min(p[i] for p in pts) for i in range(3)];mx=[max(p[i] for p in pts) for i in range(3)]
 if mn[1]<9.35 and mx[1]>6.3:occupied.append((mn[0],mx[0],mn[1],mx[1]))
wood=bpy.data.materials['AT30_walnut'];paper=bpy.data.materials['AT31_paper'];tape=bpy.data.materials['AT31_aged_enamel']
def cube(n,x,y,z,w,d,h,m):
 # Direct mesh creation avoids full-scene operator updates for each box.
 v=[(x+sx*w/2,y+sy*d/2,z+sz*h/2) for sx,sy,sz in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
 me=bpy.data.meshes.new(n);me.from_pydata(v,[],[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]);ob=bpy.data.objects.new(n,me);c.objects.link(ob);me.materials.append(m);return ob
placed=0
for attempt in range(3000):
 if placed>=38:break
 w=random.uniform(.40,.65);d=random.uniform(.37,.56);x=random.uniform(4.15,13.45);y=random.uniform(6.60,9.15)
 bb=(x-w/2,x+w/2,y-d/2,y+d/2)
 if any(bb[0]<b[1]+.018 and bb[1]>b[0]-.018 and bb[2]<b[3]+.018 and bb[3]>b[2]-.018 for b in occupied):continue
 occupied.append(bb);h=random.uniform(.48,.98)
 cube('AT31_packed_carton',x,y,2.9+h/2,w,d,h,paper if placed%3 else wood)
 cube('AT31_carton_tape',x,y,2.905+h,.045,d,.008,tape)
 if placed%2==0:
  hh=.26;cube('AT31_upper_carton',x+.02,y-.01,2.9+h+hh/2,w*.88,d*.88,hh,paper)
 placed+=1
print('extra packed boxes',placed)
s.camera=bpy.data.objects['Camera_AT31_storage'];bpy.ops.wm.save_as_mainfile(filepath=os.path.join(O,'月灯り_舞台設計_屋根裏_v31.blend'))
s.render.filepath=os.path.join(O,'屋根裏_物置の中の居場所.png');bpy.ops.render.render(write_still=True)
bpy.data.collections['43_ATTIC_Roof_toggle_v31'].hide_render=True
for o in c.objects:
 if o.name.startswith(('AT31_rafter','AT31_ridge')):o.hide_render=True
ld=bpy.data.lights.new('inspection','AREA');lo=bpy.data.objects.new('inspection',ld);s.collection.objects.link(lo);lo.location=(8,9,16);ld.energy=2800;ld.size=10
for n in ['18_BAR_Ceiling_toggle','26_STAFF_Ceiling_toggle_v22']:bpy.data.collections[n].hide_render=True
for ca,fn in [('Camera_AT31_top','屋根裏_俯瞰.png'),('Camera_AT31_building','建物全体_屋根裏の位置.png')]:
 s.camera=bpy.data.objects[ca];s.render.filepath=os.path.join(O,fn);bpy.ops.render.render(write_still=True)
