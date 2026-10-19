import bpy, math, os
from mathutils import Vector
O=r'C:\Users\kaka\Desktop\e002素材\月灯り_パン厨房_v26'
os.makedirs(O,exist_ok=True)
for o in bpy.data.objects:
 if o.name.startswith('KITCHEN_') and 'Pendant' not in o.name:
  o.hide_render=True;o.hide_set(True)
c=bpy.data.collections.new('31_BAKERY_Workshop_v26');bpy.context.scene.collection.children.link(c)
def link(o,n,m):
 o.name='BK26_'+n
 for a in list(o.users_collection):a.objects.unlink(o)
 c.objects.link(o)
 if m:o.data.materials.append(m)
 return o
def mat(n,col,metal=0):
 m=bpy.data.materials.new('BK26_'+n);m.diffuse_color=(*col,1);m.use_nodes=True
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.4 if metal else .65
 return m
steel=mat('brushed_steel',(.48,.52,.53),.7);cream=mat('aged_enamel',(.66,.64,.51));dark=mat('dark',(.045,.055,.054));wood=mat('maple',(.46,.29,.13));dough=mat('dough',(.73,.56,.32));bread=mat('baked',(.49,.23,.07));paper=mat('paper',(.8,.75,.59));green=mat('sage',(.23,.34,.28));red=mat('red',(.5,.08,.04))
def box(n,p,d,m,b=.012):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=link(bpy.context.object,n,m);o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if b:mod=o.modifiers.new('soft edges','BEVEL');mod.width=b;mod.segments=3;o.modifiers.new('normals','WEIGHTED_NORMAL')
 return o
def cyl(n,p,r,h,m):
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=h,location=p);return link(bpy.context.object,n,m)
def rod(n,a,b,r,m):
 o=cyl(n,(Vector(a)+Vector(b))/2,r,(Vector(b)-Vector(a)).length,m);o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler();return o
def ball(n,p,d,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=p);o=link(bpy.context.object,n,m);o.scale=d;return o
font=bpy.data.fonts.load(r'C:\Windows\Fonts\meiryo.ttc')
def txt(n,text,p,size=.075,rot=(math.pi/2,0,0)):
 cu=bpy.data.curves.new(n,'FONT');cu.body=text;cu.font=font;cu.size=size;cu.align_x='CENTER';cu.extrude=.0004
 o=bpy.data.objects.new('BK26_'+n,cu);c.objects.link(o);o.location=p;o.rotation_euler=rot;cu.materials.append(dark);return o
def table(n,x,y,w,d,h=.78,m=steel):
 box(n+'_top',(x,y,h-.025),(w,d,.05),m)
 for dx in [-w/2+.07,w/2-.07]:
  for dy in [-d/2+.07,d/2-.07]:box(n+'_leg',(x+dx,y+dy,(h-.05)/2),(.045,.045,h-.05),steel)
 box(n+'_shelf',(x,y,.22),(w-.12,d-.12,.035),steel)
def tray(n,x,y,z,w=.4,d=.6):
 box(n,(x,y,z),(w,d,.018),steel,.005)
 for dx in [-w/2,w/2]:box(n+'_rim',(x+dx,y,z+.014),(.014,d,.032),steel,.003)
def cabinet(n,x,y,w,d,h,front='south'):
 box(n,(x,y,h/2+.06),(w,d,h-.12),cream)
 for dx in [-w/2+.06,w/2-.06]:
  for dy in [-d/2+.06,d/2-.06]:cyl(n+'_foot',(x+dx,y+dy,.06),.03,.12,steel)
 box(n+'_top',(x,y,h),(w+.02,d+.02,.035),steel)
 return y-d/2-.015
# North wall: low oven, adjacent fermentation cabinet and cooling rack.
fy=cabinet('two_deck_oven',10.17,4.83,1.35,.96,1.39)
for z in [.76,1.12]:
 box('oven_door',(10.05,fy-.013,z),(1.02,.055,.29),steel)
 box('oven_view',(10.05,fy-.045,z),( .77,.018,.16),dark)
 rod('oven_handle',(9.63,fy-.11,z+.11),(10.47,fy-.11,z+.11),.018,steel)
 cylob=cyl('oven_dial',(10.76,fy-.055,z),.045,.025,dark);cylob.rotation_euler.x=math.pi/2
 txt('oven_temp','180',(10.75,fy-.072,z+.10),.042)
txt('oven_label','焼成 / 2段窯',(10.17,fy-.025,1.315),.062)
box('oven_hood',(10.17,4.82,2.02),(1.50,1.03,.20),steel)
box('hood_duct',(10.17,5.09,2.40),(.36,.35,.56),steel)
fy=cabinet('proofer',11.38,4.88,.76,.86,1.42)
box('proofer_door',(11.38,fy-.025,.75),(.68,.055,1.10),green)
box('proofer_window',(11.33,fy-.058,.76),(.43,.012,.81),dark)
for z in [.43,.59,.75,.91,1.07]:box('proofer_tray_visible',(11.33,fy-.068,z),(.40,.014,.018),steel)
rod('proofer_handle',(11.64,fy-.105,.60),(11.64,fy-.105,1.0),.018,steel)
txt('proofer_label','発酵器',(11.38,fy-.055,1.30),.075)
def rack(x,y):
 for dx in [-.25,.25]:
  for dy in [-.34,.34]:
   rod('rack_post',(x+dx,y+dy,.12),(x+dx,y+dy,1.37),.018,steel)
   wh=cyl('rack_caster',(x+dx,y+dy,.075),.055,.04,dark);wh.rotation_euler.x=math.pi/2
 for i in range(7):
  z=.26+i*.16;tray('cooling_tray',x,y,z,.48,.66)
  if i in [3,5]:
   for dx in [-.12,.12]:
    for dy in [-.18,0,.18]:ball('cooling_roll',(x+dx,y+dy,z+.05),(.08,.085,.05),bread)
rack(9.16,4.90)
# Island at grandma's working height, open on all four sides.
table('shaping_island',10.75,2.40,1.05,1.70,.78,wood)
tray('dough_tray',10.75,2.9,.795,.43,.48)
for dx in [-.11,.11]:
 for dy in [-.1,.1]:ball('dough_piece',(10.75+dx,2.9+dy,.835),(.075,.075,.04),dough)
rod('rolling_pin',(10.44,2.03,.81),(10.99,2.03,.81),.026,wood)
box('scraper',(10.48,2.36,.791),(.13,.085,.014),steel)
box('recipe_book',(10.76,1.79,.80),(.31,.22,.025),paper)
txt('recipe','いつもの生地',(10.76,1.76,.814),.038,(0,0,0))
for y in [2.1,2.6]:box('covered_dough_tub',(10.75,y,.40),(.55,.36,.30),cream);box('tub_lid',(10.75,y,.56),(.57,.38,.025),green)
# East: mixer / weighing, wash station, low storage. No objects near north door swing.
table('mixer_bench',13.40,3.70,.70,1.12,.77)
box('mixer_base',(13.39,3.76,.81),(.43,.48,.07),green)
box('mixer_column',(13.60,3.77,1.06),(.13,.21,.49),green)
box('mixer_head',(13.41,3.77,1.30),(.49,.23,.15),green)
# Hollow bowl with revolved profile.
verts=[];faces=[];profile=[(.02,.84),(.12,.85),(.20,.96),(.21,1.10),(.19,1.10),(.18,.97),(.10,.88),(.02,.875)]
for r,z in profile:
 for i in range(40):a=i*math.tau/40;verts.append((13.30+r*math.cos(a),3.76+r*math.sin(a),z))
for j in range(len(profile)-1):
 for i in range(40):a=j*40+i;b=j*40+(i+1)%40;faces.append((a,b,b+40,a+40))
me=bpy.data.meshes.new('bowl');me.from_pydata(verts,[],faces);ob=bpy.data.objects.new('BK26_mixer_bowl',me);c.objects.link(ob);me.materials.append(steel)
rod('mixer_spindle',(13.30,3.76,1.26),(13.30,3.76,1.0),.015,steel)
for i in range(7):rod('mixer_guard',(13.11+i*.052,3.59,1.08),(13.11+i*.052,3.90,1.08),.004,steel)
txt('mixer_tag','生地ミキサー',(13.03,3.74,.83),.04,(math.pi/2,0,-math.pi/2))
# Sink recessed into an open frame, not a slab covering its bowl.
table('sink_frame',13.40,2.32,.70,1.28,.80)
bpy.data.objects['BK26_sink_frame_top'].hide_render=True;bpy.data.objects['BK26_sink_frame_top'].hide_set(True)
for y in [1.85,2.79]:box('sink_drainer',(13.4,y,.785),(.70,.34,.03),steel)
for x in [13.10,13.70]:box('sink_rim',(x,2.32,.785),(.10,.62,.03),steel)
box('sink_bottom',(13.4,2.32,.57),(.50,.58,.025),steel)
for x in [13.145,13.655]:box('sink_side',(x,2.32,.68),(.02,.60,.22),steel)
for y in [2.02,2.62]:box('sink_side',(13.4,y,.68),(.53,.02,.22),steel)
rod('tap_up',(13.68,2.58,.81),(13.68,2.58,1.08),.019,steel);rod('tap_spout',(13.68,2.58,1.08),(13.38,2.58,1.08),.019,steel)
box('soap',(13.42,1.84,.88),(.075,.07,.15),green)
table('weigh_bench',13.4,1.04,.70,1.05,.78)
box('scale_body',(13.39,1.06,.84),(.31,.33,.10),cream);box('scale_pan',(13.39,1.06,.90),(.32,.30,.018),steel)
box('scale_display',(13.22,.884,.848),(.12,.015,.04),dark)
# South cold and dry storage; fridge front faces north.
cabinet('undercounter_fridge',12.25,.41,1.62,.72,.80)
for x in [11.86,12.65]:
 box('fridge_leaf',(x,.787,.43),(.75,.045,.60),steel)
 rod('fridge_pull',(x-.22,.83,.67),(x+.22,.83,.67),.014,dark)
txt('cold_label','冷蔵 / バター・卵',(12.25,.819,.74),.055,(math.pi/2,0,math.pi))
for x in [9.2,9.8,10.4]:
 box('ingredient_bin',(x,.42,.32),(.49,.54,.48),cream);box('bin_lid',(x,.42,.575),(.51,.56,.03),green)
 for dx in [-.16,.16]:cyl('bin_wheel',(x+dx,.42,.05),.045,.05,dark)
txt('flour_label','小麦粉',(9.2,.701,.37),.065,(math.pi/2,0,math.pi));txt('sugar_label','砂糖',(9.8,.701,.37),.065,(math.pi/2,0,math.pi))
# West packing bench below bakery doorway y3..3.9.
table('packing',8.95,1.86,.64,1.55,.80,wood)
for i in range(6):box('bread_bag',(8.95,1.48,.83+i*.005),(.34,.24,.004),paper,.001)
tray('finished_bread',8.95,2.14,.82,.42,.55)
for y in [1.98,2.15,2.32]:ball('loaf',(8.95,y,.90),(.16,.065,.075),bread)
# Practical shallow shelves, tools and a worn recipe board.
box('ingredient_wall_shelf',(13.68,1.03,1.28),(.25,1.0,.035),wood)
for y in [.70,.96,1.22]:cyl('ingredient_jar',(13.65,y,1.39),.085,.19,cream);cyl('jar_lid',(13.65,y,1.49),.088,.025,green)
box('recipe_board',(9.18,5.36,1.75),(.65,.035,.40),wood)
box('recipe_sheet',(9.18,5.335,1.75),(.53,.012,.29),paper)
txt('schedule','朝の仕込み\n計量 → 成形 → 発酵',(9.18,5.325,1.77),.044)
for x in [9.75,10.02]:
 rod('wall_hook',(x,5.30,1.65),(x,5.15,1.65),.01,steel)
 ball('oven_mitt',(x,5.14,1.48),(.075,.035,.13),green)
table('landing_cart',11.93,2.40,.50,.75,.78)
# Cart is parked east of island leaving 0.40 gap: move to south end of island instead.
for ob in list(c.objects):
 if ob.name.startswith('BK26_landing_cart'):ob.location.x-=1.18;ob.location.y-=1.43
# cameras and local light
def camera(n,p,target,lens=24,ortho=None):
 da=bpy.data.cameras.new(n);ob=bpy.data.objects.new(n,da);c.objects.link(ob);ob.location=p;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();da.lens=lens
 if ortho:da.type='ORTHO';da.ortho_scale=ortho
 return ob
cam=camera('Camera_BK26_inside',(9.0,3.72,2.36),(11.35,2.65,.70),18)
cam2=camera('Camera_BK26_oven',(11.84,2.82,1.57),(10.42,4.86,.92),24)
top=camera('Camera_BK26_plan',(11.22,2.70,11),(11.22,2.70,0),35,6.4)
ld=bpy.data.lights.new('BK26_softbox','AREA');lo=bpy.data.objects.new('BK26_softbox',ld);c.objects.link(lo);lo.location=(11.2,2.5,2.62);ld.energy=350;ld.shape='DISK';ld.size=4.0
s=bpy.context.scene;s.camera=cam;s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1400;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.use_freestyle=False
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(O,'月灯り_舞台設計_パン厨房_v26.blend'))
for ca,fn in [(cam,'厨房_全景.png'),(cam2,'厨房_発酵と焼成.png'),(top,'厨房_配置図.png')]:
 s.camera=ca;s.render.filepath=os.path.join(O,fn);bpy.ops.render.render(write_still=True)
print('DONE')
