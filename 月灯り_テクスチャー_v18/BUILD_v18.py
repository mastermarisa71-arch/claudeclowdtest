import bpy,math,os,bmesh
from mathutils import Vector
s=bpy.context.scene
OUT=r'C:\Users\kaka\Desktop\e002素材\月灯り_テクスチャー_v18'
OLD=r'C:\Users\kaka\Desktop\e002素材\月灯り_テクスチャー_v17'
assert not bpy.data.objects.get('V18_Entry_door_details'),'Apply once only'
col=bpy.data.collections['19_BAR_Wall_decor_and_corner_posts']
hinge=bpy.data.objects['D01_West_entry_Hinge'];leaf=bpy.data.objects['D01_West_entry_Leaf']
def box(n,pos,size,parent,mat,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name=n;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.parent=parent;o.location=pos;o.data.materials.append(mat)
 if bevel:
  m=o.modifiers.new('Soft edges','BEVEL');m.width=bevel;m.segments=3
 return o
def make_mat(key,path,rough):
 m=bpy.data.materials.new('V18_'+key);m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
 uv=n.new('ShaderNodeTexCoord');uv.location=(-700,0)
 sep=n.new('ShaderNodeSeparateXYZ');sep.location=(-520,0);l.new(uv.outputs['UV'],sep.inputs[0])
 comb=n.new('ShaderNodeCombineXYZ');comb.location=(-150,0)
 for j in range(2):
  p=n.new('ShaderNodeMath');p.operation='PINGPONG';p.inputs[1].default_value=1;p.location=(-350,100-j*170);l.new(sep.outputs[j],p.inputs[0]);l.new(p.outputs[0],comb.inputs[j])
 tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(path,check_existing=True);tex.image.colorspace_settings.name='sRGB';tex.image.pack();tex.location=(40,0);l.new(comb.outputs[0],tex.inputs['Vector'])
 bs=n.new('ShaderNodeBsdfPrincipled');bs.location=(340,0);bs.inputs['Roughness'].default_value=rough;l.new(tex.outputs['Color'],bs.inputs['Base Color'])
 out=n.new('ShaderNodeOutputMaterial');out.location=(650,0);l.new(bs.outputs[0],out.inputs['Surface'])
 m['mapping']='Real metre UVs; mirrored repeat; no baked lighting. Image is albedo only.'
 return m
mats={}
for k,r in [('floor_oak',.55),('wall_plaster',.85),('table_oak',.38),('seat_green_fabric',.9)]:mats[k]=make_mat(k,os.path.join(OLD,k+'_albedo.png'),r)
for k,r in [('furniture_dark_walnut',.42),('ceiling_smoked_oak',.70),('door_rich_walnut',.43)]:mats[k]=make_mat(k,os.path.join(OUT,k+'_albedo.png'),r)
def uvmap(o,tile=1,grain=None,space='WORLD'):
 if o.data.users>1:o.data=o.data.copy()
 d=o.data;uv=d.uv_layers.get('V18_Metres') or d.uv_layers.new(name='V18_Metres');d.uv_layers.active=uv;uv.active_render=True
 matrix=o.matrix_world if space=='WORLD' else (o.parent.matrix_world.inverted()@o.matrix_world if o.parent else o.matrix_world)
 verts=[matrix@v.co for v in d.vertices]
 normalmat=matrix.to_3x3().inverted().transposed()
 for p in d.polygons:
  normal=normalmat@p.normal;axis=max(range(3),key=lambda a:abs(normal[a]));axes=[a for a in range(3) if a!=axis]
  vaxis=grain if grain in axes else axes[1];uaxis=next(a for a in axes if a!=vaxis)
  for li in p.loop_indices:
   co=verts[d.loops[li].vertex_index];uv.data[li].uv=(co[uaxis]/tile,co[vaxis]/tile)
 o['texture_tile_metres']=tile
def assign(o,key,tile=1,grain=None,space='WORLD'):
 o.data.materials.clear();o.data.materials.append(mats[key]);uvmap(o,tile,grain,space)
 for polygon in o.data.polygons:polygon.material_index=0
# Thicker completely opaque leaf, same opening width and hinge control.
for v in leaf.data.vertices:v.co.y*=.075/.045
leaf.data.update();leaf['solid_thickness_m']=.075;leaf['no_glass']=True
root=bpy.data.objects.new('V18_Entry_door_details',None);col.objects.link(root);root.parent=hinge
brass=bpy.data.materials['Door_handle_brass'];wood=mats['door_rich_walnut']
bpy.data.objects.remove(bpy.data.objects['D01_West_entry_Handle'],do_unlink=True)
# Real shallow carvings on both faces; never penetrate the leaf.
cutters=[]
def groove(points,y,r=.003):
 for a,b in zip(points[:-1],points[1:]):
  a=Vector((a[0],y,a[1]));b=Vector((b[0],y,b[1]))
  bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name='V18_Carving_cutter'
  o.dimensions=(2*r,.008,(b-a).length+.002)
  bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
  for c in list(o.users_collection):c.objects.unlink(o)
  col.objects.link(o);o.parent=hinge;o.location=(a+b)/2;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();cutters.append(o);o.select_set(False)
def chamfer_rect(x0,x1,z0,z1,c=.025):return [(x0+c,z0),(x1-c,z0),(x1,z0+c),(x1,z1-c),(x1-c,z1),(x0+c,z1),(x0,z1-c),(x0,z0+c),(x0+c,z0)]
for side in [-1,1]:
 y=side*.0375
 for inset in [0,.017]:
  groove(chamfer_rect(.09+inset,.79-inset,1.17+inset,1.94-inset),y)
  groove(chamfer_rect(.09+inset,.79-inset,.20+inset,.85-inset),y)
 # Restrained fan-and-stepped-lines motif in the upper panel.
 for j in range(7):
  dx=(j-3)*.055;groove([(.44,1.40),(.44+dx,1.77+(.07 if j==3 else .025 if j in [2,4] else 0))],y,.0025)
 groove([(.25,1.88),(.25,1.85),(.32,1.85),(.32,1.82),(.56,1.82),(.56,1.85),(.63,1.85),(.63,1.88)],y,.0025)
 groove([(.25,.50),(.44,.69),(.63,.50),(.44,.31),(.25,.50)],y,.0025)
for cutter in cutters:
 bm=bmesh.new();bm.from_mesh(cutter.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(cutter.data);bm.free()
 bpy.ops.object.select_all(action='DESELECT');leaf.select_set(True);bpy.context.view_layer.objects.active=leaf
 mod=leaf.modifiers.new('Shallow wood carving','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
mod=leaf.modifiers.new('Leaf edge rounding','BEVEL');mod.width=.0015;mod.segments=2
bm=bmesh.new();bm.from_mesh(leaf.data)
loose=[f for f in bm.faces if f.calc_area()<1e-9 and all(len(e.link_faces)==1 for e in f.edges)]
bmesh.ops.delete(bm,geom=loose,context='FACES_ONLY')
bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(leaf.data);bm.free();leaf.data.update()
assign(leaf,'door_rich_walnut',1,2,'PARENT')
def rod(n,a,b,r,parent,mat):
 a=Vector(a);b=Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=(b-a).length);o=bpy.context.object;o.name=n
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.parent=parent;o.location=(a+b)/2;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=True
 return o
for side in [-1,1]:
 box('V18_Handle_backplate',(.758,side*.041,1.015),(.060,.009,.29),root,brass,.007)
 for z in [.925,1.105]:rod('V18_Handle_mount',(.758,side*.044,z),(.758,side*.110,z),.012,root,brass)
 rod('V18_Hand_grip',(.758,side*.110,.925),(.758,side*.110,1.105),.014,root,brass)
 # Wooden continuous seal at bottom rotates with leaf, closes former floor gap.
 seal=box('V18_Door_bottom_seal',(.44,0,.012),(.88,.075,.024),root,wood,.002);assign(seal,'door_rich_walnut',1,2,'PARENT')
 break
# Handle outside face too.
side=1
box('V18_Handle_backplate',(.758,.041,1.015),(.060,.009,.29),root,brass,.007)
for z in [.925,1.105]:rod('V18_Handle_mount',(.758,.044,z),(.758,.110,z),.012,root,brass)
rod('V18_Hand_grip',(.758,.110,.925),(.758,.110,1.105),.014,root,brass)
# Fixed overlapping rebates on outside side of closed door. No glass or apertures.
for y in [9.342,10.232]:
 o=box('V18_Door_stop',(-.143,y,1.025),(.030,.032,2.05),None,wood,.002);assign(o,'door_rich_walnut',1,2)
o=box('V18_Door_stop_header',(-.143,9.79,2.05),(.030,.916,.030),None,wood,.002);assign(o,'door_rich_walnut',1,2)
for y in [9.292,10.282]:
 o=box('V18_Entry_architrave',(.025,y,1.075),(.050,.075,2.15),None,wood,.005);assign(o,'door_rich_walnut',1,2)
o=box('V18_Entry_architrave_header',(.025,9.787,2.12),(.050,1.065,.095),None,wood,.005);assign(o,'door_rich_walnut',1,1)
# Texture bar furnishings only, with different species/value for tabletops/carcasses/beams.
allowed={'10_Moonlight_furniture','16_Bar_service_and_tabletop_props','19_BAR_Wall_decor_and_corner_posts','18_BAR_Ceiling_toggle'}
counts={k:0 for k in mats}
for o in list(bpy.data.objects):
 if o.type!='MESH' or o.name.startswith('V18_') or o==leaf:continue
 names=[m.name for m in o.data.materials]
 isbar=any(c.name in allowed for c in o.users_collection) or o.name.startswith(('PIANO_','ROUND_','SECRET_','V12_Upper_shelf','V14_Radio'))
 key=None;tile=1;grain=None
 if o.name=='Floor_UL':key='floor_oak';tile=1.2;grain=1
 elif 'Wall_warm_plaster' in names and o.matrix_world.translation.y>=5.5 and o.matrix_world.translation.x<=8.6:key='wall_plaster'
 elif isbar:
  if o.name.startswith('V13_Ceiling_cross_beam'):key='ceiling_smoked_oak';tile=1.5;grain=0
  elif any(x in names for x in ['Sofa_dark_teal_fabric','Stool_teal_cushion']):key='seat_green_fabric';tile=.3
  elif 'Furniture_honey_oak' in names:key='table_oak'
  elif any(x in names for x in ['Furniture_dark_wood','V13_Trim_dark_walnut']):key='furniture_dark_walnut'
 if key:
  if key in ['table_oak','furniture_dark_walnut']:
   dims=o.dimensions;grain=2 if dims.z>.3 and dims.z>max(dims.x,dims.y)*.6 else (0 if dims.x>=dims.y else 1)
  assign(o,key,tile,grain);counts[key]+=1
hinge['opening_degrees']=0.;hinge.update_tag(refresh={'OBJECT'});s.frame_set(s.frame_current);bpy.context.view_layer.update()
root['description']='Opaque 75mm solid wooden leaf, paired brass hand grips, shallow 3D Art Deco carvings, overlapping jamb stops and bottom seal. Door opening_degrees control retained.'
def cam(n,pos,target,lens):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);bpy.data.collections['05_Cameras'].objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;o.hide_set(True)
cam('Camera_BAR_Entry_door_v18',(3.1,9.7,1.55),(-.06,9.78,1.06),26)
s['layout_version']='v18 differentiated wood materials and opaque carved entry door'
note='月灯り v18\n木材：床は板張りオーク、天板は蜂蜜色オーク、家具胴・棚・枠は濃いウォールナット、梁は灰茶のスモークオーク、入口扉は温かい濃茶のウォールナット。\n壁はアイボリーの塗り壁、ソファとカウンタースツールは深緑の布素材を適用。実寸UV、鏡像反復、原本画像をパック。木目は梁・天板の長手、扉と縦部材は縦方向。\n入口：厚さ75mmの不透明な木。ガラス・採光穴なし。両面に浅い彫刻と握れる真鍮の取っ手。枠の戸当たりと下端の遮光材を追加。開閉制御を維持し、保存時は閉じた状態。\n家具配置、客席数、ピアノの曲面形、ノート棚、隠蔽機構、天井の切替は維持。\n'
t=bpy.data.texts.new('README_v18');t.write(note);open(os.path.join(OUT,'変更内容_v18.txt'),'w',encoding='utf-8').write(note)
bpy.ops.object.select_all(action='DESELECT');s.camera=bpy.data.objects['Camera_BAR_Atmosphere_v13']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'月灯り_舞台設計_木材と彫刻扉_v18.blend'))
print('texture counts',counts,'leaf polygons',len(leaf.data.polygons),'saved',bpy.data.filepath)

