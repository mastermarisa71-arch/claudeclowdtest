import bpy, math, os, json
from mathutils import Vector, Matrix
OUT=r'C:\Users\kaka\Desktop\e002素材\月灯り_控室_v22'
os.makedirs(OUT,exist_ok=True)
col=bpy.data.collections.new('25_STAFF_Folding_stairs_v22');bpy.context.scene.collection.children.link(col)
ceils=bpy.data.collections.new('26_STAFF_Ceiling_toggle_v22');bpy.context.scene.collection.children.link(ceils)
def material(name,c,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
 b=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Roughness'].default_value=.6;b.inputs['Metallic'].default_value=metal;return m
wood=material('V22_STAIR_Wood',(.34,.23,.13));metal=material('V22_STAIR_Iron',(.16,.18,.17),.6);ceiling=material('V22_STAFF_Ceiling',(.55,.51,.43));red=material('V22_STAIR_Control',(.34,.13,.08))
def empty(name,loc=(0,0,0),parent=None):
 o=bpy.data.objects.new(name,None);col.objects.link(o);o.parent=parent;o.location=loc;return o
def box(name,loc,size,mat,parent=None,collection=col):
 bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name=name
 for c in list(o.users_collection):c.objects.unlink(o)
 collection.objects.link(o);o.parent=parent;o.location=loc;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 mod=o.modifiers.new('Soft edges','BEVEL');mod.width=.006;mod.segments=2;return o
def rod(name,a,b,r,mat,parent=None):
 a,b=Vector(a),Vector(b);d=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=r,depth=d.length);o=bpy.context.object;o.name=name
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.parent=parent;o.location=(a+b)/2;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.data.materials.append(mat);return o

# Move existing STAFF additions only, never bar furniture or shared room walls.
staff=bpy.data.collections['24_STAFF_Layout_v21']
def move_group(objects,old,new,angle):
 transform=Matrix.Translation(Vector(new))@Matrix.Rotation(angle,4,'Z')@Matrix.Translation(-Vector(old))
 for o in objects:o.matrix_world=transform@o.matrix_world
move_group([o for o in staff.objects if any(o.name.startswith('V21_STAFF_'+p) for p in ['Pantry_'])],(9.35,11.9,0),(8.90,11.45,0),math.pi/2)
tea_prefix=['Tea_storage','Tea_jar','Kettle','Snack','Tea_wall','Staff_mug','Notice_','Compact_fridge','Fridge_']
move_group([o for o in staff.objects if any(o.name.startswith('V21_STAFF_'+p) for p in tea_prefix)],(10.93,11.9,0),(13.51,6.52,0),-math.pi/2)
curtain_prefix=['Curtain_','Changing_stool','Changing_basket']
move_group([o for o in staff.objects if any(o.name.startswith('V21_STAFF_'+p) for p in curtain_prefix)],(0,0,0),(-1.50,0,0),0)
# Curtain vertices were built in world coordinates; their X-axis shape-key deformation survives translation.

# Ceiling and upper-storey floor are four strips around a genuine rectangular hole.
# Controls and stair head fit between x12.45..13.55 and y10.00..12.05.
for name,x0,x1,y0,y1 in [
 ('west',8.58,12.45,5.58,12.2),('east',13.55,13.86,5.58,12.2),
 ('south',12.45,13.55,5.58,10.00),('north',12.45,13.55,12.05,12.20)]:
 box('V22_STAFF_Ceiling_'+name,((x0+x1)/2,(y0+y1)/2,2.79),(x1-x0,y1-y0,.18),ceiling,collection=ceils)
for x in [12.425,13.575]:box('V22_STAIR_Hatch_side_frame',(x,11.025,2.79),(.05,2.15,.20),wood)
for y in [9.975,12.075]:box('V22_STAIR_Hatch_end_frame',(13.0,y,2.79),(1.20,.05,.20),wood)

master=empty('V22_STAIR_Control');master['stow']=0.0;master.id_properties_ui('stow').update(min=0,max=1,description='0 lowered / 1 folded and ceiling hatch closed; lower fold, upper fold, then hatch lift')
master['opening_metres']='1.10 x 2.05';master['stair_outer_width_metres']=.91
master['note']='Story blocking prototype: 2F room beyond landing, structure/counterbalance not finalized'
hinge=empty('V22_STAIR_Hatch_hinge',(13.0,12.02,2.78))
angle=math.radians(55);L=2.78/(3*math.sin(angle))
def driver(o,path,index,expr):
 d=o.driver_add(path,index).driver;d.expression=expr;v=d.variables.new();v.name='s';v.targets[0].id=master;v.targets[0].data_path='["stow"]'
lower='min(max(s/0.32,0),1)';middle='min(max((s-0.32)/0.33,0),1)';lift='min(max((s-0.65)/0.35,0),1)'
driver(hinge,'rotation_euler',0,'%s*(1-(%s))'%(angle,lift))
box('V22_STAIR_Hatch_solid_lid',(0,-1.0,-.06),(1.06,2.0,.04),ceiling,hinge)
rod('V22_STAIR_Lid_inside_grip',(-.17,-.9,-.09),(.17,-.9,-.09),.015,metal,hinge)
sections=[empty('V22_STAIR_Upper_section',(0,0,0),hinge)]
sections.append(empty('V22_STAIR_Middle_section',(0,-L,0),sections[0]))
sections.append(empty('V22_STAIR_Lower_section',(0,-L,0),sections[1]))
driver(sections[1],'rotation_euler',0,'-pi*(%s)'%middle)
driver(sections[2],'rotation_euler',0,'-pi*(%s)'%lower)
# Hinge spacing grows only while folded so stringers and treads stack rather than intersect.
driver(sections[1],'location',2,'.40*(%s)'%middle)
driver(sections[2],'location',2,'-.40*(%s)'%lower)
for i,section in enumerate(sections):
 for x in [-.42,.42]:
  box('V22_STAIR_Stringer_%d'%i,(x,-L/2,0),(.07,L,.075),wood,section)
  for y in [0,-L]:rod('V22_STAIR_Hinge_pin_%d'%i,(x-.055,y,0),(x+.055,y,0),.022,metal,section)
 for j in range(4):
  tread=box('V22_STAIR_Tread_%d_%d'%(i,j),(0,-(j+.5)*L/4,.09),(.77,.19,.035),wood,section)
  tread.rotation_euler.x=-angle
  # Fine nosing strips read as steps in both plan and perspective.
  strip=box('V22_STAIR_Tread_grip_%d_%d'%(i,j),(0,-.073,.020),(.72,.016,.006),metal,tread)
rod('V22_STAIR_Bottom_crossbar',(-.46,-L,0),(.46,-L,0),.025,metal,sections[2])
# Above-floor grab rails and a short 2F landing make the destination explicit.
box('V22_STAIR_Upper_landing',(13.0,13.10,2.80),(2.25,2.10,.20),wood)
for x in [12.32,13.68]:
 rod('V22_STAIR_Upper_grab_post',(x,12.15,2.90),(x,12.15,3.80),.025,metal)
 rod('V22_STAIR_Upper_grab_rail',(x,12.15,3.80),(x,13.50,3.80),.025,metal)
 rod('V22_STAIR_Upper_grab_post',(x,13.50,2.90),(x,13.50,3.80),.025,metal)
box('V22_STAIR_Upper_pull_latch',(13.0,12.19,2.94),(.18,.10,.07),red)

def camera(name,pos,target,lens=24,ortho=None):
 data=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,data);col.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();data.lens=lens
 if ortho:data.type='ORTHO';data.ortho_scale=ortho
 return o
camera('Camera_STAFF_stair_v22',(13.15,7.90,1.70),(13.0,11.05,1.50),22)
camera('Camera_STAFF_layout_v22',(11.22,8.89,14),(11.22,8.89,0),ortho=9.7)
camera('Camera_STAFF_stair_stowed_v22',(10.60,9.0,4.35),(13.0,11.25,3.0),28)
col['deployment_space']='Keep x12.35..13.60, y9.15..12.20 clear; bottom ends at y10.07. No furniture in sweep.'
col['stair_spec']=json.dumps({'incline_degrees':55,'ceiling_height':2.7,'floor2_height':2.9,'steps':12,'step_rise':round(L*math.sin(angle)/4,3),'section_length':round(L,3),'lowered_run':round(3*L*math.cos(angle),3)})
master.update_tag();bpy.context.scene.frame_set(bpy.context.scene.frame_current)
print(col['stair_spec'])
