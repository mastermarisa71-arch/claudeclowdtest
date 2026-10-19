import bpy,math,random,os,shutil
from mathutils import Vector
random.seed(1232);s=bpy.context.scene;bpy.context.view_layer.update()
O=r'C:\Users\kaka\Desktop\e002素材\月灯り_屋根裏_v32';c=bpy.data.collections['44_ATTIC_Irregular_piles_v32'];paper=bpy.data.materials['AT31_paper'];wood=bpy.data.materials['AT30_walnut'];tape=bpy.data.materials['AT30_aged_brass']
occ=[]
for o in bpy.data.objects:
 if o.type!='MESH' or o.hide_render or not o.visible_get() or not o.name.startswith(('AT32_','AT30_','AT31_')):continue
 pp=[o.matrix_world@Vector(v) for v in o.bound_box];mn=[min(p[i] for p in pp) for i in range(3)];mx=[max(p[i] for p in pp) for i in range(3)]
 if mx[0]-mn[0]>2.2 or mx[1]-mn[1]>2.2 or mx[2]<2.93:continue
 occ.append((mn[0],mx[0],mn[1],mx[1]))
def meshbox(n,p,w,d,h,a,m):
 x,y,z=p;co=math.cos(a);si=math.sin(a);vs=[]
 for xx,yy,zz in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]:
  u=xx*w/2;v=yy*d/2;vs.append((x+u*co-v*si,y+u*si+v*co,z+zz*h/2))
 me=bpy.data.meshes.new(n);me.from_pydata(vs,[],[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]);o=bpy.data.objects.new(n,me);c.objects.link(o);me.materials.append(m)
count=0
for _ in range(6000):
 if count>=28:break
 zone=random.choice([0,0,0,1,2])
 if zone==0:x=random.uniform(4.1,13.5);y=random.uniform(6.5,9.2)
 elif zone==1:x=random.uniform(7.55,8.60);y=random.uniform(13.05,13.65)
 else:x=random.uniform(11.25,11.95);y=random.uniform(13.35,13.7)
 w=random.uniform(.38,.65);d=random.uniform(.34,.55);a=math.radians(random.choice([-39,-26,22,36]));ex=(abs(w*math.cos(a))+abs(d*math.sin(a)))/2;ey=(abs(w*math.sin(a))+abs(d*math.cos(a)))/2;bb=(x-ex,x+ex,y-ey,y+ey)
 if bb[0]<3.85 or bb[1]>13.8 or bb[3]>14.02:continue
 if any(bb[0]<b[1]+.01 and bb[1]>b[0]-.01 and bb[2]<b[3]+.01 and bb[3]>b[2]-.01 for b in occ):continue
 occ.append(bb);h=random.uniform(.50,1.05);meshbox('AT32_misc_carton',(x,y,2.9+h/2),w,d,h,a,paper if count%2 else wood);meshbox('AT32_misc_strap',(x,y,2.905+h),.045,d,.007,a,tape)
 if count%3==0:meshbox('AT32_top_box',(x+.02,y-.01,3.025+h),w*.78,d*.78,.24,a+.20,paper)
 count+=1
print('added infill',count)
s.camera=bpy.data.objects['Camera_AT31_storage'];bpy.ops.wm.save_as_mainfile(filepath=os.path.join(O,'月灯り_舞台設計_屋根裏_v32.blend'))
s.render.filepath=os.path.join(O,'屋根裏_乱雑な家具配置.png');bpy.ops.render.render(write_still=True)
bpy.data.collections['43_ATTIC_Roof_toggle_v31'].hide_render=True
for o in bpy.data.collections['42_ATTIC_Expanded_store_v31'].objects:
 if o.name.startswith(('AT31_rafter','AT31_ridge')):o.hide_render=True
ld=bpy.data.lights.new('inspection','AREA');lo=bpy.data.objects.new('inspection',ld);s.collection.objects.link(lo);lo.location=(8,10,16);ld.energy=2300;ld.size=10
s.camera=bpy.data.objects['Camera_AT31_top'];s.render.filepath=os.path.join(O,'屋根裏_俯瞰.png');bpy.ops.render.render(write_still=True)
shutil.copy2('attic_v32_fill.py',O)
