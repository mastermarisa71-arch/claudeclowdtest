import bpy,math,os,json
from mathutils import Vector
OUT=r'C:\Users\kaka\Desktop\e002素材\月灯り_控室_v25';os.makedirs(OUT,exist_ok=True)
cat=bpy.data.collections.new('29_STAFF_Stella_corner_v25');bpy.context.scene.collection.children.link(cat)
fridge=bpy.data.collections.new('30_STAFF_Compact_fridge_v25');bpy.context.scene.collection.children.link(fridge)
def mat(name,c,metal=0,rough=.6):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1)
 b=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough;return m
cream=mat('V25_Porcelain_cream',(.75,.73,.63),0,.35);cloth=mat('V25_Stella_soft_cushion',(.31,.39,.37),0,.92);rope=mat('V25_Stella_sisal',(.49,.36,.22),0,.9)
blue=mat('V25_Stella_ball_blue',(.25,.33,.43));red=mat('V25_Stella_toy_red',(.45,.23,.25));food=mat('V25_Stella_food',(.25,.16,.075));water=mat('V25_Stella_water',(.18,.31,.36),.25,.15)
white=mat('V25_Fridge_enamel',(.72,.72,.66),0,.32);inside=mat('V25_Fridge_inside',(.68,.70,.66));metal=bpy.data.materials['V24_STAFF_Silver_trim'];dark=bpy.data.materials['V24_STAFF_Ink'];wood=bpy.data.materials['V21_STAFF_Oak'];paper=bpy.data.materials['V24_STAFF_Paper']
def link(o,c):
 for old in list(o.users_collection):old.objects.unlink(o)
 c.objects.link(o)
def box(name,loc,size,material,c=cat,parent=None,bevel=.008):
 bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name='V25_'+name;link(o,c);o.parent=parent;o.location=loc;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
 if bevel:
  m=o.modifiers.new('Soft edges','BEVEL');m.width=bevel;m.segments=3
 return o
def cylinder(name,loc,r,depth,material,c=cat,parent=None):
 bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=r,depth=depth);o=bpy.context.object;o.name='V25_'+name;link(o,c);o.parent=parent;o.location=loc;o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 return o
def ball(name,loc,scale,material,c=cat,parent=None):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16);o=bpy.context.object;o.name='V25_'+name;link(o,c);o.parent=parent;o.location=loc;o.scale=scale;o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 return o
def pipe(name,points,r,material,c=cat,parent=None):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=3;sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
 for p,co in zip(sp.points,points):p.co=(*co,1)
 o=bpy.data.objects.new('V25_'+name,cu);c.objects.link(o);o.parent=parent;cu.materials.append(material);return o
font=bpy.data.fonts.load(r'C:\Windows\Fonts\meiryo.ttc',check_existing=True)
def text(name,body,loc,size,material=dark,c=cat,parent=None,rot=(math.pi/2,0,math.pi)):
 cu=bpy.data.curves.new(name,'FONT');cu.font=font;cu.body=body;cu.size=size;cu.align_x='CENTER';cu.align_y='CENTER';cu.extrude=.0002
 o=bpy.data.objects.new('V25_'+name,cu);c.objects.link(o);o.parent=parent;o.location=loc;o.rotation_euler=rot;cu.materials.append(material);return o

# Retire the small bowls under the bench: one consistent place to feed Stella.
for o in bpy.data.objects:
 if o.name.startswith('V24_STAFF_Stella_bowl'):o.hide_render=True;o.hide_set(True)

# Low open den with a soft upper bed; no tower that dominates the room.
x,y=10.02,5.86
box('Stella_den_floor',(x,y,.07),(.76,.48,.04),wood)
box('Stella_den_back',(x,5.63,.255),(.76,.035,.41),wood)
for sx in [x-.365,x+.365]:box('Stella_den_side',(sx,y,.255),(.030,.48,.41),wood)
box('Stella_den_top',(x,y,.455),(.80,.51,.035),wood)
ball('Stella_den_inner_pad',(x,y,.12),(.335,.205,.043),cloth)
ball('Stella_upper_bed_pad',(x,y,.51),(.35,.21,.057),cloth)
rimpoints=[(x+.347*math.cos(t),y+.207*math.sin(t),.545) for t in [i*math.tau/80 for i in range(81)]]
pipe('Stella_bed_soft_rim',rimpoints,.031,cloth)
# A modest wall perch, reachable from the low bed.
box('Stella_wall_perch',(10.02,5.75,1.00),(.67,.30,.035),wood)
ball('Stella_wall_perch_pad',(10.02,5.76,1.029),(.29,.12,.021),cloth)
for sx in [9.80,10.24]:pipe('Stella_perch_bracket',[(sx,5.61,.78),(sx,5.86,.98),(sx,5.61,.98)],.018,metal)
box('Stella_name_plate',(10.02,5.608,1.30),(.38,.025,.10),wood)
text('Stella_name','ステラ',(10.02,5.625,1.30),.053,paper)

# Food and water on a washable mat, low and readily reached by Akane.
box('Stella_food_mat',(11.02,5.85,.017),(.71,.39,.020),cloth)
box('Stella_feeder_base',(11.02,5.84,.073),(.61,.30,.076),wood)
def bowl(name,x,y,contents):
 # Revolved cup profile creates an actual concave bowl, not a filled cylinder.
 profile=[(0,.116),(.061,.116),(.080,.13),(.095,.18),(.099,.18),(.100,.16),(.091,.098),(0,.098)]
 vs=[];n=48
 for r,z in profile:
  for j in range(n):vs.append((x+r*math.cos(j*math.tau/n),y+r*math.sin(j*math.tau/n),z))
 fs=[]
 for i in range(len(profile)-1):
  for j in range(n):fs.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('V25_'+name,me);cat.objects.link(o);me.materials.append(cream)
 for p in me.polygons:p.use_smooth=True
 cylinder(name+'_contents',(x,y,.123),.060,.005,contents)
 return o
bowl('Stella_food_bowl',10.85,5.84,food);bowl('Stella_water_bowl',11.19,5.84,water)
for i in range(16):
 a=i*2.4;r=.039*math.sqrt((i+.5)/16)
 ball('Stella_kibble',(10.85+r*math.cos(a),5.84+r*math.sin(a),.129),(.007,.005,.004),food)
box('Stella_food_shelf',(11.04,5.69,.61),(.44,.20,.025),wood)
cylinder('Stella_sealed_food_tin',(11.03,5.68,.725),.070,.20,cream)
cylinder('Stella_food_tin_lid',(11.03,5.68,.834),.074,.020,wood)
text('Stella_food_label','フード',(11.03,5.754,.725),.027,dark)
pipe('Stella_food_scoop_handle',[(11.18,5.70,.626),(11.26,5.70,.626)],.008,metal)
ball('Stella_food_scoop',(11.16,5.70,.629),(.025,.018,.006),metal)

# Scratching post and contained toys: no loose objects in the exit route.
box('Stella_scratch_base',(9.43,5.85,.025),(.27,.30,.05),wood)
cylinder('Stella_scratching_post',(9.43,5.85,.325),.052,.56,rope)
for i in range(55):
 z=.05+i*.010
 points=[(9.43+.054*math.cos(t),5.85+.054*math.sin(t),z) for t in [j*math.tau/24 for j in range(25)]]
 pipe('Stella_sisal_wrap',points,.0025,rope)
cylinder('Stella_post_cap',(9.43,5.85,.615),.061,.035,wood)
box('Stella_toy_box_bottom',(11.78,5.82,.034),(.28,.25,.034),wood)
for sx in [11.645,11.915]:box('Stella_toy_box_side',(sx,5.82,.115),(.016,.25,.18),wood)
for sy in [5.703,5.937]:box('Stella_toy_box_side',(11.78,sy,.115),(.28,.016,.18),wood)
ball('Stella_toy_ball',(11.72,5.82,.087),(.04,.04,.04),blue)
ball('Stella_mouse_toy',(11.82,5.81,.08),(.05,.025,.024),cloth)
for sx in [11.81,11.83]:ball('Stella_mouse_ear',(sx,5.80,.103),(.009,.004,.009),red)
pipe('Stella_mouse_tail',[(11.865,5.81,.08),(11.895,5.84,.068),(11.88,5.87,.065)],.003,rope)
pipe('Stella_wand',[(11.85,5.625,.35),(11.85,5.625,.96)],.009,wood)
pipe('Stella_wand_string',[(11.85,5.625,.96),(11.70,5.64,.80),(11.70,5.64,.58)],.0015,rope)
ball('Stella_wand_feather',(11.70,5.64,.545),(.017,.009,.051),red)
text('Stella_toy_box_label','おもちゃ',(11.78,5.949,.13),.034,paper)
cat['purpose']='Stella home base on south wall: care by Akane, no stair/door traffic. No cat mesh added.'
cat['extent']='X9.295..11.955, Y5.61..6.115; chair rear edge Y6.915: 0.80m clear strip'

# Make the already planned refrigerator legible; retain the tea counter footprint.
for name in ['V21_STAFF_Compact_fridge_door','V21_STAFF_Fridge_base_vent','V21_STAFF_Fridge_label','V21_STAFF_Tea_storage_pull','V21_STAFF_Tea_storage_body']:
 o=bpy.data.objects.get(name)
 if o:o.hide_render=True;o.hide_set(True)
box('Tea_remaining_storage_body',(13.51,6.12,.44),(.50,.75,.88),bpy.data.materials['V21_STAFF_Warm_cream'],fridge)
# Five-sided cabinet; front is open when the door swings out.
box('Fridge_back',(13.755,6.92,.465),(.035,.72,.81),white,fridge)
for sy in [6.57,7.27]:box('Fridge_side',(13.51,sy,.465),(.51,.025,.81),white,fridge)
for z in [.075,.855]:box('Fridge_case_horizontal',(13.51,6.92,z),(.51,.72,.035),white,fridge)
box('Fridge_inner_back',(13.728,6.92,.465),(.012,.66,.73),inside,fridge)
for z in [.25,.46,.65]:box('Fridge_shelf',(13.51,6.92,z),(.42,.65,.018),inside,fridge)
box('Fridge_crisper',(13.50,6.92,.17),(.39,.60,.13),inside,fridge)
box('Fridge_milk_carton',(13.51,6.76,.56),(.09,.09,.18),cream,fridge)
box('Fridge_leftover_box',(13.52,7.05,.30),(.20,.19,.075),bpy.data.materials['V21_STAFF_Sage'],fridge)

hinge=bpy.data.objects.new('V25_Fridge_door_hinge',None);fridge.objects.link(hinge);hinge.location=(13.22,6.56,0);hinge['open_degrees']=0.0;hinge.id_properties_ui('open_degrees').update(min=0,max=95,description='Small fridge door opens into room; 0 closed')
d=hinge.driver_add('rotation_euler',2).driver;d.expression='a*pi/180';v=d.variables.new();v.name='a';v.targets[0].id=hinge;v.targets[0].data_path='["open_degrees"]'
box('Fridge_door',(0,.36,.465),(.052,.68,.75),white,fridge,hinge,.023)
for sy in [.037,.683]:box('Fridge_gasket_side',(.031,sy,.465),(.010,.012,.71),dark,fridge,hinge)
for z in [.11,.82]:box('Fridge_gasket_end',(.031,.36,z),(.010,.65,.012),dark,fridge,hinge)
pipe('Fridge_vertical_handle',[(-.074,.605,.39),(-.074,.605,.64)],.014,metal,fridge,hinge)
for z in [.39,.64]:pipe('Fridge_handle_support',[(-.026,.605,z),(-.074,.605,z)],.009,metal,fridge,hinge)
box('Fridge_small_badge',(-.030,.35,.76),(.008,.16,.045),metal,fridge,hinge)
text('Fridge_badge_text','冷蔵',(-.035,.35,.76),.029,paper,fridge,hinge,rot=(math.pi/2,0,-math.pi/2))
box('Fridge_grocery_note',(-.032,.18,.60),(.009,.12,.13),paper,fridge,hinge)
text('Fridge_grocery_note_text','牛乳\nまかない',(-.039,.18,.60),.019,dark,fridge,hinge,rot=(math.pi/2,0,-math.pi/2))
box('Fridge_note_magnet',(-.040,.18,.665),(.012,.026,.013),blue,fridge,hinge)
for z in [.095,.11,.125]:box('Fridge_lower_vent',(13.236,6.92,z),(.013,.23,.006),dark,fridge)
fridge['purpose']='One under-counter fridge, not an extra duplicate appliance; same footprint as previous placeholder.'

def camera(name,pos,target,lens,c=cat):
 data=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,data);c.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();data.lens=lens
camera('Camera_STAFF_Stella_v25',(11.47,7.14,1.28),(10.57,5.82,.58),26)
camera('Camera_STAFF_Stella_context_v25',(12.00,9.2,1.70),(10.38,5.88,.72),24)
camera('Camera_STAFF_fridge_v25',(11.99,6.61,1.25),(13.50,6.78,.70),28,fridge)
print(json.dumps({'Stella_corner':'south wall','cat_front_Y':6.115,'chair_rear_Y':6.915,'clear_strip_metres':.80,'fridge_door_control':hinge.name},ensure_ascii=False))
