import bpy,math,os,random,shutil
from mathutils import Vector
O=r'C:\Users\kaka\Desktop\e002素材\月灯り_屋根裏_v28';os.makedirs(O,exist_ok=True)
c=bpy.data.collections.new('33_ATTIC_Room_and_balcony_v28');bpy.context.scene.collection.children.link(c)
src=open('bakery_v26.py',encoding='utf8').read();exec(src[src.index('def link('):src.index('# North wall:')].replace('BK26_','AT28_'))
roofcol=bpy.data.collections.new('34_ATTIC_Roof_toggle_v28');bpy.context.scene.collection.children.link(roofcol)
fillcol=bpy.data.collections.new('35_ATTIC_Surrounding_roof_v28');bpy.context.scene.collection.children.link(fillcol)
roofmat=mat('roof_slate',(.15,.18,.19));plaster=mat('warm_plaster',(.49,.42,.32));oldwood=mat('old_beams',(.19,.10,.055));canvas=mat('dust_cloth',(.40,.39,.31))
def mesh(n,verts,faces,m,col=None):
 me=bpy.data.meshes.new(n);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('AT28_'+n,me);(col or c).objects.link(o);me.materials.append(m);return o
def roof(n,x0,x1,y0,y1,z0,z1,col):
 o=mesh(n,[(x0,y0,z0),(x1,y0,z1),(x1,y1,z1),(x0,y1,z0)],[(0,1,2,3)],roofmat,col);md=o.modifiers.new('roof thickness','SOLIDIFY');md.thickness=.10;return o
def beam(n,a,b,w=.09,m=None):
 o=box(n,(Vector(a)+Vector(b))/2,(w,w,(Vector(b)-Vector(a)).length),m or oldwood,.005);o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler();return o
# Remove obsolete oversize landing and rails; keep original folding stair mechanism.
for o in bpy.data.objects:
 if o.name.startswith('V22_STAIR_Upper_landing') or o.name.startswith('V22_STAIR_Upper_grab_rail') or o.name.startswith('V22_STAIR_Upper_grab_post'):
  o.hide_render=True;o.hide_set(True)
ctl=bpy.data.objects['V22_STAIR_Control'];ctl['stow']=0.0;ctl.update_tag();s=bpy.context.scene;f=s.frame_current;s.frame_set(f+1);s.frame_set(f)
# Floor: 4.26 x 4.30, upper surface 2.90; genuine hole matches existing hatch.
for n,x0,x1,y0,y1 in [('west',9.6,12.45,9.8,14.1),('east',13.55,13.86,9.8,14.1),('south',12.45,13.55,9.8,10.0),('landing',12.45,13.55,12.05,14.1)]:
 box('floor_'+n,((x0+x1)/2,(y0+y1)/2,2.82),(x1-x0,y1-y0,.16),wood,.001)
# Board seams follow floor pieces rather than closing the stair opening.
for i in range(18):
 x=9.65+i*.24
 intervals=[(9.82,14.08)] if x<12.45 or x>13.55 else [(12.06,14.08)]
 for ya,yb in intervals:box('floor_seam',(x,(ya+yb)/2,2.901),(.007,yb-ya,.002),oldwood,0)
# Knee walls: full gables, sloping roof sides. South opening gives direct balcony view.
box('west_knee_wall',(9.55,11.95,3.72),(.10,4.4,1.64),plaster)
box('east_knee_wall',(13.91,11.95,3.72),(.10,4.4,1.64),plaster)
box('north_wall',(11.73,14.15,3.72),(4.46,.10,1.64),plaster)
mesh('north_gable',[(9.5,14.15,4.54),(13.96,14.15,4.54),(11.73,14.15,5.78)],[(0,1,2)],plaster)
for x,w in [(9.91,.62),(12.64,2.44)]:box('front_wall',(x,9.75,3.72),(w,.10,1.64),plaster)
box('balcony_lintel',(10.82,9.75,5.01),(1.20,.10,.94),plaster)
mesh('south_gable',[(9.5,9.75,4.54),(13.96,9.75,4.54),(11.73,9.75,5.78)],[(0,1,2)],plaster)
# Door gap x10.22..11.42, z2.9..4.54; glazed double leaves remain open inward.
for x in [10.20,11.44]:box('door_jamb',(x,9.73,3.74),(.07,.15,1.72),oldwood)
box('door_top',(10.82,9.73,4.58),(1.31,.15,.08),oldwood)
for x,sign in [(10.23,1),(11.41,-1)]:
 root=bpy.data.objects.new('AT28_balcony_door_hinge',None);c.objects.link(root);root.location=(x,9.75,2.91);root.rotation_euler.z=sign*math.radians(78)
 for xx,zz,dx,dz in [(sign*.29,.055,.58,.11),(sign*.29,1.57,.58,.075),(sign*.02,.81,.045,1.58),(sign*.56,.81,.045,1.58),(sign*.29,.73,.58,.07)]:
  ob=box('door_frame',(xx,0,zz),(dx,.045,dz),oldwood);ob.parent=root
# Roof and beams; ceiling independently removable for shooting.
roof('west_roof',9.40,11.73,9.50,14.38,4.49,5.78,roofcol);roof('east_roof',11.73,14.06,9.50,14.38,5.78,4.49,roofcol)
for y in [10.05,11.90,13.85]:
 for a,b in [((9.61,y,4.49),(11.73,y,5.67)),((11.73,y,5.67),(13.85,y,4.49))]:beam('exposed_rafter',a,b,.11)
beam('ridge',(11.73,9.82,5.66),(11.73,14.08,5.66),.13)
# Balcony toward bakery entrance (negative Y), inset on the rear part of roof.
box('balcony_deck',(10.82,9.02,2.81),(2.70,1.55,.18),wood)
for i in range(11):box('deck_seam',(9.52+i*.25,9.02,2.902),(.01,1.54,.004),oldwood,0)
for a,b in [((9.49,8.24,3.98),(12.15,8.24,3.98)),((9.49,8.24,3.98),(9.49,9.76,3.98)),((12.15,8.24,3.98),(12.15,9.76,3.98))]:beam('balcony_handrail',a,b,.07)
for i in range(12):beam('front_baluster',(9.50+i*.24,8.25,2.94),(9.50+i*.24,8.25,3.96),.033)
for x in [9.5,12.14]:
 for y in [8.52,8.82,9.12,9.42,9.70]:beam('side_baluster',(x,y,2.94),(x,y,3.96),.033)
# Guard around stair opening; north remains the step-off into room.
for x in [12.36,13.65]:
 beam('hatch_side_rail',(x,10.02,3.95),(x,12.04,3.95),.055)
 for y in [10.03,11.02,12.02]:beam('hatch_post',(x,y,2.90),(x,y,3.95),.055)
beam('hatch_end_rail',(12.36,9.94,3.95),(13.65,9.94,3.95),.055)
# Remaining building is low roof void, not a second suite of rooms.
roof('west_void_outer',-.20,4.60,-.20,14.38,2.85,3.80,fillcol)
roof('west_void_inner',4.60,9.40,-.20,14.38,3.80,3.02,fillcol)
roof('front_void_left',9.40,11.73,-.20,8.22,3.02,3.58,fillcol)
roof('front_void_right',11.73,14.06,-.20,8.22,3.58,3.02,fillcol)
roof('balcony_east_filler',12.18,14.06,8.22,9.5,3.02,3.02,fillcol)
# Stored belongings: clustered under eaves, no additional bedrooms.
def crate(n,x,y,z,w,d,h):
 box(n,(x,y,z+h/2),(w,d,h),wood)
 for zz in [z+.06,z+h-.06]:box(n+'_strap',(x,y-d/2-.008,zz),(w,.018,.045),oldwood)
 for xx in [x-w*.34,x+w*.34]:box(n+'_batten',(xx,y-d/2-.017,z+h/2),(.045,.025,h),oldwood)
def carton(x,y,z,w,d,h):
 box('carton',(x,y,z+h/2),(w,d,h),paper)
 box('packing_tape',(x,y,z+h+.003),(.055,d,.006),cream)
for p in [(9.96,10.48,2.9,.53,.64,.47),(9.96,11.19,2.9,.53,.59,.50),(10.02,11.20,3.4,.43,.48,.32),(9.96,13.68,2.9,.57,.57,.49),(10.55,13.70,2.9,.55,.55,.38),(10.53,13.70,3.28,.49,.48,.33)]:crate('old_stock',*p)
for p in [(9.95,10.48,3.37,.48,.55,.31),(11.18,13.72,2.9,.55,.54,.41),(11.17,13.71,3.31,.48,.48,.35),(11.71,13.72,2.9,.42,.51,.49)]:carton(*p)
# Low west shelving with old bakeware, records and baskets.
for z in [3.13,3.65,4.17]:box('storage_shelf',(9.91,12.25,z),(.55,1.22,.04),oldwood)
for y in [11.64,12.86]:box('shelf_upright',(9.68,y,3.56),(.055,.055,1.32),oldwood)
for i in range(5):box('old_music_books',(9.95,11.84+i*.105,3.89),(.34,.08,.44),green if i%2 else wood)
for y in [11.96,12.48]:box('bread_basket',(9.94,y,3.32),(.38,.38,.31),wood)
# Instrument cases and stacked stools along north wall.
box('keyboard_case',(10.83,14.00,4.00),(1.20,.16,.42),dark)
for x in [10.43,11.23]:box('case_latch',(x,13.91,4.02),(.07,.02,.04),steel)
rod('case_handle',(10.70,13.88,4.08),(10.96,13.88,4.08),.014,steel)
for j in range(3):
 z=2.9+j*.12;cyl('stacked_stool_seat',(12.00,13.65,z+.43),.22,.055,wood)
 for dx,dy in [(-.14,-.14),(.14,-.14),(-.14,.14),(.14,.14)]:rod('stool_leg',(12+dx,13.65+dy,z),(12+dx,13.65+dy,z+.40),.018,oldwood)
# cloth-covered spare table, visible legs, against left/front eave.
box('covered_spare_furniture',(10.15,10.00,3.40),(.85,.32,.09),canvas)
for x in [9.80,10.50]:box('spare_furniture_leg',(x,10.00,3.15),(.05,.08,.50),oldwood)
# Pendants and practical warm light.
rod('lamp_cord',(11.60,12.10,5.58),(11.60,12.10,4.94),.008,dark)
box('lamp_shade',(11.60,12.10,4.87),(.30,.30,.12),cream)
ld=bpy.data.lights.new('AT28_warm_bulb','AREA');lo=bpy.data.objects.new('AT28_warm_bulb',ld);c.objects.link(lo);lo.location=(11.6,12.0,4.74);ld.energy=160;ld.color=(1,.79,.55);ld.shape='DISK';ld.size=2
ld=bpy.data.lights.new('AT28_balcony_daylight','AREA');lo=bpy.data.objects.new('AT28_balcony_daylight',ld);c.objects.link(lo);lo.location=(10.8,8.3,4.3);lo.rotation_euler=(Vector((11.2,12,3.4))-lo.location).to_track_quat('-Z','Y').to_euler();ld.energy=350;ld.size=2
def cam(n,p,t,lens=24,ortho=None):
 da=bpy.data.cameras.new(n);ob=bpy.data.objects.new(n,da);c.objects.link(ob);ob.location=p;ob.rotation_euler=(Vector(t)-ob.location).to_track_quat('-Z','Y').to_euler();da.lens=lens
 if ortho:da.type='ORTHO';da.ortho_scale=ortho
 return ob
inside=cam('Camera_AT28_from_stairs',(13.12,13.52,4.30),(10.77,10.85,3.88),19)
rev=cam('Camera_AT28_from_balcony',(10.84,9.45,4.28),(11.66,12.85,3.65),20)
top=cam('Camera_AT28_plan',(11.70,11.1,12),(11.70,11.1,0),24,8.8)
s.camera=inside;s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1400;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.use_freestyle=False
note='''屋根裏 v28：既存収納階段と一室を接続。床高2.90m、室内約4.26×4.30m（階段穴・荷物部分を含む）。
ベランダ約2.7×1.55m、パン屋の玄関と同じ南向き。位置は建物の奥寄りで、玄関の真上ではありません。
建物全体を二階室内にせず、余白を低い屋根で覆う演出用の構成。
階段は既存のstow制御。通常0=下ろす、1=収納。床には元の1.10×2.05mの穴を確保。
33_ATTIC_Room_and_balcony_v28：部屋・荷物。34_ATTIC_Roof_toggle_v28：部屋の屋根。35_ATTIC_Surrounding_roof_v28：周囲の低い屋根。
不要家具、楽器ケース、譜面・古い型などを軒下に寄せ、階段出口から左折してベランダへ進む中央動線を残す。
寸法・屋根形状は舞台仮設計。実在建築の構造計算は行っていません。
'''
open(os.path.join(O,'屋根裏_設計メモ.txt'),'w',encoding='utf8').write(note);tx=bpy.data.texts.new('README_ATTIC_v28');tx.write(note)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(O,'月灯り_舞台設計_屋根裏_v28.blend'))
for ca,fn in [(inside,'屋根裏_階段から.png'),(rev,'屋根裏_ベランダから.png')]:
 s.camera=ca;s.render.filepath=os.path.join(O,fn);bpy.ops.render.render(write_still=True)
roofcol.hide_render=True
s.camera=top;s.render.filepath=os.path.join(O,'屋根裏_配置.png');bpy.ops.render.render(write_still=True)
roofcol.hide_render=False
shutil.copy2('attic_v28.py',O)
print('DONE ATTIC')
