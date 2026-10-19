import bpy,math,os,json
from mathutils import Matrix,Vector
OUT=r'C:\Users\kaka\Desktop\e002素材\月灯り_控室_v23';os.makedirs(OUT,exist_ok=True)
staff=bpy.data.collections['24_STAFF_Layout_v21']
# Put the pantry against the back wall; the entry wall and its sightline stay free.
transform=Matrix.Translation(Vector((10.0,11.9,0)))@Matrix.Rotation(-math.pi/2,4,'Z')@Matrix.Translation(Vector((-8.9,-11.45,0)))
for o in staff.objects:
 if o.name.startswith('V21_STAFF_Pantry_'):o.matrix_world=transform@o.matrix_world

# Compact changing bay: 1.25m x 1.25m, anchored beside the stair with a separate entrance.
old=Vector((10.28,10.10,0));new=Vector((10.91,10.80,0))
scale=Matrix.Diagonal((1.25/1.88,1.25/1.95,1,1))
mapping=Matrix.Translation(new)@scale@Matrix.Translation(-old)
for o in staff.objects:
 if o.name.startswith('V21_STAFF_Curtain_'):o.matrix_world=mapping@o.matrix_world
 if o.name.startswith(('V21_STAFF_Changing_stool','V21_STAFF_Changing_basket')):
  o.matrix_world.translation=mapping@o.matrix_world.translation
# Compress the right panel only in its open shape; preserve the closing shape and driver.
right=bpy.data.objects['V21_STAFF_Curtain_front_right']
basis=right.data.shape_keys.key_blocks['Basis']
for v in basis.data:v.co.x=13.66+(v.co.x-13.66)*(.225/(.66*1.25/1.88))

col=bpy.data.collections.new('27_STAFF_Laundry_v23');bpy.context.scene.collection.children.link(col)
def material(name,color,metal=0,rough=.55):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
 b=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal;return m
enamel=material('V23_Laundry_Enamel',(.62,.60,.51));rubber=material('V23_Laundry_Rubber',(.04,.055,.052));steel=material('V23_Laundry_Metal',(.38,.41,.40),.65,.3)
window=material('V23_Laundry_Door_glass',(.07,.13,.14),.3,.18);wood=bpy.data.materials['V21_STAFF_Oak']
def link(o):
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o)
def box(name,loc,size,mat,bevel=.012):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);link(o);o.data.materials.append(mat)
 if bevel:
  mod=o.modifiers.new('Rounded enamel edge','BEVEL');mod.width=bevel;mod.segments=3
 return o
def disc(name,loc,r,depth,mat):
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=depth,location=loc,rotation=(0,math.pi/2,0));o=bpy.context.object;o.name=name;link(o);o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=True
 return o
box('V23_STAFF_Washer_body',(13.50,9.05,.45),(.62,.62,.84),enamel,.025)
box('V23_STAFF_Washer_top',(13.50,9.05,.89),(.65,.65,.04),enamel)
box('V23_STAFF_Washer_plinth',(13.50,9.05,.05),(.54,.54,.08),rubber)
disc('V23_STAFF_Washer_door_gasket',(13.175,9.05,.46),.225,.026,rubber)
disc('V23_STAFF_Washer_door_rim',(13.153,9.05,.46),.213,.028,steel)
disc('V23_STAFF_Washer_round_window',(13.135,9.05,.46),.178,.018,window)
box('V23_STAFF_Washer_door_pull',(13.116,8.865,.46),(.035,.026,.14),enamel)
box('V23_STAFF_Washer_control_panel',(13.181,9.05,.765),(.021,.55,.10),enamel)
box('V23_STAFF_Washer_detergent_drawer',(13.163,9.245,.77),(.020,.135,.070),steel)
disc('V23_STAFF_Washer_dial',(13.148,9.00,.77),.034,.025,rubber)
box('V23_STAFF_Washer_display',(13.156,8.875,.77),(.012,.085,.040),rubber)
for z in [.14,.16,.18]:box('V23_STAFF_Washer_lower_vent',(13.181,9.05,z),(.011,.23,.008),rubber,.003)
# Small laundry props make the machine's use legible, without another tall shelf.
box('V23_STAFF_Folded_towel_1',(13.50,9.06,.95),(.35,.38,.065),bpy.data.materials['V21_STAFF_Curtain'])
box('V23_STAFF_Folded_towel_2',(13.50,9.06,1.014),(.33,.36,.05),enamel)
box('V23_STAFF_Laundry_wall_tap',(13.815,9.18,1.08),(.05,.08,.08),steel)
cu=bpy.data.curves.new('V23_Laundry_supply_hose','CURVE');cu.dimensions='3D';cu.bevel_depth=.011;cu.bevel_resolution=3
sp=cu.splines.new('POLY');points=[(13.795,9.18,1.08),(13.775,9.18,.94),(13.775,9.18,.72)];sp.points.add(2)
for p,co in zip(sp.points,points):p.co=(*co,1)
o=bpy.data.objects.new('V23_STAFF_Laundry_supply_hose',cu);col.objects.link(o);cu.materials.append(rubber)
def camera(name,loc,target,lens=24):
 data=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,data);col.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();data.lens=lens;return o
camera('Camera_STAFF_v23',(13.2,5.9,1.73),(10.7,10.60,1.1),22)
camera('Camera_STAFF_wet_area_v23',(11.3,8.0,1.60),(13.52,8.25,1.0),23)
camera('Camera_STAFF_entry_clear_v23',(12.25,9.5,1.65),(8.65,10.55,1.1),27)
print(json.dumps({'curtain_footprint':[1.25,1.25],'curtain_open_width':round(1.25-.4*1.25/1.88-.225,3),'washer_footprint':[.62,.62],'washer_to_stair_bottom_m':round(10.07-(9.05+.325),3),'pantry_front_Y':11.635},ensure_ascii=False))
