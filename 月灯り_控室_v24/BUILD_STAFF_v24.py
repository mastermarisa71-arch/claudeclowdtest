import bpy,math,os,json
from mathutils import Vector
OUT=r'C:\Users\kaka\Desktop\e002素材\月灯り_控室_v24';os.makedirs(OUT,exist_ok=True)
root=bpy.data.collections.new('28_STAFF_Daily_life_v24');bpy.context.scene.collection.children.link(root)
def collection(name):
 c=bpy.data.collections.new(name);root.children.link(c);return c
always=collection('28a_STAFF_Personal_and_shared_props')
meal=collection('28b_STAFF_Break_meal_toggle')
work=collection('28c_STAFF_Closing_paperwork_toggle')
def mat(name,c,metal=0,rough=.6):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1)
 b=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough;return m
silver=mat('V24_STAFF_Silver_lockers',(.55,.58,.59),.48,.43)
silvertrim=mat('V24_STAFF_Silver_trim',(.32,.36,.38),.65,.38)
paper=mat('V24_STAFF_Paper',(.82,.77,.63));white=mat('V24_STAFF_Porcelain',(.77,.77,.70),0,.35)
ink=mat('V24_STAFF_Ink',(.025,.037,.045));kraft=mat('V24_STAFF_Kraft',(.42,.29,.16));black=mat('V24_STAFF_Black',(.03,.035,.04))
pink=mat('V24_STAFF_Akane_pink',(.57,.29,.34));gold=mat('V24_STAFF_Mahiru_honey',(.66,.45,.18));blue=mat('V24_STAFF_Kairi_indigo',(.17,.20,.35));gray=mat('V24_STAFF_Sakuna_bluegray',(.28,.38,.42))
wood=bpy.data.materials['V21_STAFF_Oak'];green=bpy.data.materials['V21_STAFF_Sage']
rice=mat('V24_STAFF_Rice',(.79,.75,.61));veg=mat('V24_STAFF_Vegetables',(.20,.36,.14));food=mat('V24_STAFF_Meal',(.55,.28,.10))
def link(o,c):
 for prev in list(o.users_collection):prev.objects.unlink(o)
 c.objects.link(o)
def box(name,loc,dims,material,c=always,bevel=.006):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name='V24_STAFF_'+name;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);link(o,c);o.data.materials.append(material)
 if bevel:
  mod=o.modifiers.new('Small soft edge','BEVEL');mod.width=bevel;mod.segments=3
 return o
def disc(name,loc,r,depth,material,c=always,axis='Z'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name='V24_STAFF_'+name
 if axis=='X':o.rotation_euler.y=math.pi/2
 link(o,c);o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 return o
def pipe(name,points,r,material,c=always):
 cu=bpy.data.curves.new('V24_'+name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=3
 sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
 for p,co in zip(sp.points,points):p.co=(*co,1)
 o=bpy.data.objects.new('V24_STAFF_'+name,cu);c.objects.link(o);cu.materials.append(material);return o
font=bpy.data.fonts.load(r'C:\Windows\Fonts\meiryo.ttc',check_existing=True)
def text(name,body,loc,size,material=ink,c=always,rot=(math.pi/2,0,0)):
 cu=bpy.data.curves.new('V24_'+name,'FONT');cu.body=body;cu.size=size;cu.align_x='CENTER';cu.align_y='CENTER';cu.font=font;cu.extrude=.0002
 o=bpy.data.objects.new('V24_STAFF_'+name,cu);c.objects.link(o);o.location=loc;o.rotation_euler=rot;cu.materials.append(material);return o

# Silver remains the common base: personality comes from small labels, not door colors.
names=['あかね','朔奈','まひる','海凪'];colors=[pink,gray,gold,blue];ys=[6.25,6.9,7.55,8.2]
for i,(name,color,y) in enumerate(zip(names,colors,ys),1):
 for suffix in ['body','door','top']:
  o=bpy.data.objects['V21_STAFF_Locker_%d_%s'%(i,suffix)];o.data.materials.clear();o.data.materials.append(silver)
 plate=bpy.data.objects['V21_STAFF_Locker_%d_number_plate'%i];plate.data.materials.clear();plate.data.materials.append(silvertrim)
 old=bpy.data.objects['V21_STAFF_Locker_%d_number'%i];old.hide_render=True;old.hide_set(True)
 box('Locker_%d_name_card'%i,(9.281,y,1.60),(.007,.18,.075),paper)
 text('Locker_%d_name'%i,name,(9.286,y,1.60),.038,ink,rot=(math.pi/2,0,math.pi/2))
 box('Locker_%d_small_marker'%i,(9.285,y+.065,1.61),(.008,.009,.059),color)
 if i==1:
  disc('Akane_cat_sticker',(9.270,y+.085,1.34),.045,.004,pink,axis='X')
  disc('Akane_cat_face',(9.274,y+.085,1.345),.027,.004,black,axis='X')
  # Two triangular ears sit in the plane of the door.
  verts=[];faces=[]
  for offset in [-.018,.018]:
   start=len(verts);verts.extend([(9.278,y+.085+offset-.009,1.36),(9.278,y+.085+offset+.009,1.36),(9.278,y+.085+offset,1.385)]);faces.append((start,start+1,start+2))
  me=bpy.data.meshes.new('V24_Cat_ears');me.from_pydata(verts,[],faces);o=bpy.data.objects.new('V24_STAFF_Akane_cat_ears',me);always.objects.link(o);me.materials.append(black)
  for dy in [-.009,.009]:disc('Akane_cat_eye',(9.280,y+.085+dy,1.35),.003,.002,gold,axis='X')
 elif i==3:
  for j,(dy,z) in enumerate([(-.10,1.36),(.10,1.25)]):
   disc('Mahiru_cookie_sticker',(9.274,y+dy,z),.034,.003,gold,axis='X')
   for a in range(5):disc('Cookie_chip',(9.278,y+dy+.017*math.cos(a*1.25),z+.017*math.sin(a*1.25)),.003,.002,kraft,axis='X')
 elif i==4:
  text('Kairi_music_sticker','♪',(9.277,y+.08,1.34),.087,blue,rot=(math.pi/2,0,math.pi/2))

# Store daily paperwork by the back wall, outside the door silhouette and the stair sweep.
for j,label in enumerate(['経費','仕入れ','ノート']):
 z=1.62-j*.23;box('Document_pocket_back_'+label,(8.93,12.163,z),(.48,.025,.20),wood)
 box('Document_pocket_base_'+label,(8.93,12.106,z-.095),(.48,.13,.019),wood)
 box('Document_pocket_front_'+label,(8.93,12.047,z-.035),(.48,.014,.12),green)
 for x in [8.70,9.16]:box('Document_pocket_side',(x,12.10,z-.015),(.02,.12,.16),wood)
 text('Document_pocket_label_'+label,label,(8.93,12.034,z-.035),.045,paper)
 if label!='ノート':
  box('Folder_'+label,(8.94,12.10,z+.03),(.36,.012,.21),kraft)
  box('Folder_tab_'+label,(8.82,12.10,z+.15),(.10,.012,.035),paper)
 else:
  box('Akane_stored_notebook',(8.94,12.10,z+.025),(.23,.045,.25),pink,meal)
  text('Akane_stored_notebook_name','あかね',(8.94,12.073,z+.09),.028,paper,meal)

# Four mugs live by tea preparation when not in use; replace the solid placeholder cylinders.
for o in list(bpy.data.objects):
 if o.name.startswith(('STAFF_Mug','V21_STAFF_Staff_mug')):o.hide_render=True;o.hide_set(True)
def mug(name,x,y,z,color,c):
 disc(name+'_body',(x,y,z+.048),.044,.095,color,c)
 disc(name+'_rim',(x,y,z+.096),.043,.008,white,c)
 disc(name+'_tea',(x,y,z+.101),.035,.003,kraft,c)
 points=[(x+.038+.030*math.sin(t),y,z+.049+.030*math.cos(t)) for t in [a*math.pi/12 for a in range(13)]]
 pipe(name+'_handle',points,.006,color,c)
for i,(y,color) in enumerate(zip([5.98,6.22,6.46,6.70],colors)):
 mug('Shelf_mug_'+names[i],13.63,y,1.49,color,work)

# Oral care: shallow wall shelf beside the mirror, individual holders and toothbrushes.
box('Oral_care_shelf',(13.74,8.72,1.29),(.20,.48,.025),wood)
for i,color in enumerate(colors):
 y=8.52+i*.071
 disc('Brush_cup_'+names[i],(13.73,y,1.34),.029,.08,color)
 pipe('Toothbrush_'+names[i],[(13.73,y,1.34),(13.73,y,1.53)],.006,color)
 box('Toothbrush_head_'+names[i],(13.73,y,1.54),(.025,.012,.032),white)
box('Toothpaste_tube',(13.73,8.84,1.3925),(.025,.035,.18),paper)
box('Toothpaste_cap',(13.73,8.84,1.4925),(.028,.038,.026),gray)
box('Rinsing_cup',(13.71,8.90,1.34),(.065,.065,.075),white)

# Break table: food stays on trays. The table middle remains free for hands and acting.
for o in [bpy.data.objects.get('STAFF_Notebook_on_table')]:
 if o:o.hide_render=True;o.hide_set(True)
for i,(x,y) in enumerate([(10.63,7.76),(11.81,7.76),(10.63,8.32),(11.81,8.32)]):
 box('Meal_tray_'+names[i],(x,y,.755),(.38,.29,.025),wood,meal)
 box('Meal_box_'+names[i],(x,y,.797),(.28,.18,.062),colors[i],meal)
 box('Meal_rice_'+names[i],(x-.060,y,.829),(.11,.14,.020),rice,meal)
 for j in range(3):disc('Meal_side_'+names[i],(x+.05,y-.045+j*.045,.84),.025,.030,food if j<2 else veg,meal)
 for dx in [-.11,-.10]:pipe('Chopsticks_'+names[i],[(x+dx,y-.125,.778),(x+dx+.18,y-.125,.778)],.0023,wood,meal)
 mug('Table_mug_'+names[i],x+(.31 if i%2==0 else -.31),y,.742,colors[i],meal)
box('Shared_tissue_box',(11.22,8.39,.79),(.19,.12,.085),kraft)
box('Tissue_sheet',(11.22,8.39,.846),(.10,.025,.06),paper)

# Closing table state: Akane's record and the manager's accounts occupy distinct places.
def notebook(x,y,z,c):
 box('Akane_open_note_cover',(x,y,z),(.39,.27,.014),pink,c)
 for dx in [-.099,.099]:box('Akane_open_note_pages',(x+dx,y,z+.015),(.187,.25,.021),paper,c)
 pipe('Akane_note_binding',[(x,y-.12,z+.03),(x,y+.12,z+.03)],.002,kraft,c)
 text('Akane_note_heading','あかねのノート',(x-.095,y+.08,z+.027),.018,ink,c,rot=(0,0,0))
 for dx in [-.097,.097]:
  for j in range(6):box('Notebook_rule',(x+dx,y+.048-j*.025,z+.027),(.15,.0012,.0006),gray,c,0)
notebook(11.78,8.22,.754,work)
pipe('Akane_pen',[(11.56,8.07,.762),(11.56,8.28,.762)],.004,ink,work)
box('Accounts_clipboard',(10.65,8.18,.758),(.33,.25,.018),wood,work)
box('Accounts_sheet',(10.65,8.18,.772),(.30,.23,.004),paper,work)
text('Accounts_title','経費・仕入れ',(10.65,8.25,.775),.026,ink,work,rot=(0,0,0))
for j in range(5):box('Accounts_rule',(10.65,8.21-j*.027,.775),(.25,.001,.0008),gray,work,0)
box('Clipboard_clip',(10.65,8.295,.79),(.10,.022,.02),silvertrim,work)
box('Calculator',(10.73,7.81,.775),(.11,.16,.037),gray,work)
box('Calculator_screen',(10.73,7.86,.795),(.080,.037,.005),ink,work)
for a in range(3):
 for b in range(3):box('Calculator_key',(10.701+a*.028,7.82-b*.027,.797),(.019,.018,.007),white,work)
for j in range(4):box('Receipt_slip',(11.03+j*.003,8.26-j*.012,.756+j*.004),(.095,.14,.002),paper,work,.001)
box('Receipt_envelope',(11.20,8.35,.755),(.24,.15,.006),kraft,work)
text('Receipt_envelope_label','レシート',(11.20,8.35,.759),.026,ink,work,rot=(0,0,0))
box('Closing_pen_cup',(11.25,8.08,.79),(.065,.065,.08),gray,work)
for dx in [-.018,0,.018]:pipe('Closing_pencil',[(11.25+dx,8.08,.79),(11.25+dx,8.08,.90)],.003,wood,work)

# Everyday return-home items, kept compact and out of the stair area.
box('Staff_key_tray',(8.95,9.12,.50),(.22,.14,.028),wood)
for i,color in enumerate(colors):
 disc('Key_tag_'+names[i],(8.89+i*.040,9.13,.52),.014,.006,color)
 box('Key_shaft',(8.89+i*.040,9.092,.520),(.009,.055,.005),silvertrim)
# Lightweight laundry basket in the bay; no spare furniture or instrument storage downstairs.
old=bpy.data.objects['V21_STAFF_Changing_basket'];old.data.materials.clear();old.data.materials.append(kraft)
for i in range(3):box('Laundry_fold',(old.location.x,old.location.y,.385+i*.025),(.27,.27,.026),white if i%2 else gray)

# The hall worker also cares for Stella: small bowls sit under the bench, away from traffic.
for y,material in [(8.99,gray),(9.23,pink)]:
 disc('Stella_bowl',(8.88,y,.044),.075,.045,material)
 disc('Stella_bowl_inset',(8.88,y,.068),.059,.007,kraft if material==pink else blue)
# A compact paper bin belongs below the shallow document pockets.
box('Paper_bin',(8.93,11.99,.20),(.27,.27,.38),gray)
box('Paper_bin_dark_opening',(8.93,11.99,.397),(.22,.22,.012),ink)

# A small drain tray and two clean plates explain everyday washing at the basin.
box('Staff_drain_tray',(13.48,8.47,.886),(.40,.25,.014),silvertrim)
for j in range(6):pipe('Drain_rack_bar',[(13.31,8.375+j*.033,.903),(13.65,8.375+j*.033,.903)],.003,silvertrim)
for j in range(2):
 plate=disc('Clean_staff_plate',(13.48,8.44+j*.055,.984),.072,.009,white)
 plate.rotation_euler.x=math.pi/2

meal.hide_render=False;meal.hide_viewport=False;work.hide_render=True;work.hide_viewport=True
root['default_time']='営業前のまかない休憩（仮）'
root['design_status']='Character locker stickers and color allocation are proposals, not finalized canon.'
root['day_flow']='Arrival: keys/lockers/change. Break: meals/tea/toothbrushing. Close: notebook/accounts/laundry. Return to nearby homes. Large furniture and unused instruments upstairs.'
def cam(name,pos,target,lens):
 data=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,data);always.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();data.lens=lens
cam('Camera_STAFF_life_v24',(13.2,5.94,1.74),(10.95,9.35,1.05),24)
cam('Camera_STAFF_lockers_v24',(12.65,9.15,1.64),(8.94,7.27,1.25),28)
cam('Camera_STAFF_table_v24',(12.54,6.92,1.81),(11.18,8.1,.78),34)
print(json.dumps({'personal_names':names,'daily_props':sum(len(c.objects) for c in root.children),'large_furniture_added':0,'default':'break'},ensure_ascii=False))
