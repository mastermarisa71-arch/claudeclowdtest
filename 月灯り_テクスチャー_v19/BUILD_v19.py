import bpy, os, json, shutil
from mathutils import Vector

OUT = r'C:\Users\kaka\Desktop\e002素材\月灯り_テクスチャー_v19'
os.makedirs(OUT, exist_ok=True)
world = bpy.data.objects.get('V19_Material_world_metres')
if not world:
    world = bpy.data.objects.new('V19_Material_world_metres', None)
    bpy.context.scene.collection.objects.link(world)
world.hide_render = True
world.hide_viewport = True
world['purpose'] = 'World metre coordinates for consistent material height and repeat'

def load_image(name):
    im = bpy.data.images.load(os.path.join(OUT, name), check_existing=True)
    im.pack()
    im.filepath = '//' + name
    return im

brick_image = load_image('wall_old_brick_albedo.png')
ceiling_image = load_image('ceiling_warm_boards_albedo.png')

def new_math(nodes, links, operation, a, b=None):
    n = nodes.new('ShaderNodeMath'); n.operation = operation
    if isinstance(a, (int, float)): n.inputs[0].default_value = a
    else: links.new(a, n.inputs[0])
    if b is not None:
        if isinstance(b, (int, float)): n.inputs[1].default_value = b
        else: links.new(b, n.inputs[1])
    return n.outputs[0]

def wall_material(source):
    name = 'V19_Brick90cm_upper_tobacco_' + source.name
    if bpy.data.materials.get(name): return bpy.data.materials[name]
    m = source.copy(); m.name = name; m.use_nodes = True
    ns, ls = m.node_tree.nodes, m.node_tree.links
    bs = next(n for n in ns if n.type == 'BSDF_PRINCIPLED')
    color_input = bs.inputs['Base Color']
    if color_input.is_linked:
        old_color = color_input.links[0].from_socket
    else:
        old = ns.new('ShaderNodeRGB'); old.outputs[0].default_value = color_input.default_value
        old_color = old.outputs[0]
    tc = ns.new('ShaderNodeTexCoord'); tc.object = world
    sep = ns.new('ShaderNodeSeparateXYZ'); ls.new(tc.outputs['Object'], sep.inputs[0])
    checks = []
    for axis, lo, hi in [('X', -.015, 8.535), ('Y', 5.565, 14.305)]:
        checks.append(new_math(ns,ls,'GREATER_THAN',sep.outputs[axis],lo))
        checks.append(new_math(ns,ls,'LESS_THAN',sep.outputs[axis],hi))
    mask = checks[0]
    for check in checks[1:]: mask = new_math(ns,ls,'MULTIPLY',mask,check)
    low = new_math(ns,ls,'LESS_THAN',sep.outputs['Z'],.90)
    brick_mask = new_math(ns,ls,'MULTIPLY',mask,low)
    scale = ns.new('ShaderNodeVectorMath'); scale.operation='MULTIPLY'
    scale.inputs[1].default_value=(1/.69,1/.69,1/.825)
    ls.new(tc.outputs['Object'],scale.inputs[0])
    tex = ns.new('ShaderNodeTexImage'); tex.image=brick_image
    tex.projection='BOX'; tex.projection_blend=0; tex.extension='REPEAT'
    ls.new(scale.outputs['Vector'],tex.inputs['Vector'])
    upper = ns.new('ShaderNodeMixRGB'); upper.blend_type='MULTIPLY'
    upper.inputs[0].default_value=1
    ls.new(old_color,upper.inputs[1]);upper.inputs[2].default_value=(.48,.37,.26,1)
    mix = ns.new('ShaderNodeMixRGB');ls.new(low,mix.inputs[0])
    ls.new(upper.outputs[0],mix.inputs[1]);ls.new(tex.outputs['Color'],mix.inputs[2])
    scoped = ns.new('ShaderNodeMixRGB');ls.new(mask,scoped.inputs[0])
    ls.new(old_color,scoped.inputs[1]);ls.new(mix.outputs[0],scoped.inputs[2])
    ls.new(scoped.outputs[0],color_input)
    bump = ns.new('ShaderNodeBump'); bump.inputs['Distance'].default_value=.002
    ls.new(tex.outputs['Color'],bump.inputs['Height'])
    strength = new_math(ns,ls,'MULTIPLY',brick_mask,.18)
    ls.new(strength,bump.inputs['Strength']);ls.new(bump.outputs['Normal'],bs.inputs['Normal'])
    bs.inputs['Roughness'].default_value=.86
    m.diffuse_color=(.27,.18,.12,1)
    m['brick_top_metres']=.90
    m['brick_tile_metres']='0.69 horizontal / 0.825 vertical: actual generated image 3 bricks, 11 rows'
    m['upper_tint_linear']=[.48,.37,.26]
    return m

wall_targets=[]
for o in bpy.data.collections['02_Walls_editable'].objects:
    if o.type!='MESH': continue
    if o.name.startswith(('North_end','Divider_vertical','Divider_horizontal_left','V12_West_bar','V12_West_door','V12_West_above','V12_Window_end')):
        wall_targets.append(o)
for name in ['V16_Guest_niche_reveal','V16_Mirror_reveal','V16_Mirror_reveal.001','V16_Mirror_reveal.002']:
    if bpy.data.objects.get(name):wall_targets.append(bpy.data.objects[name])
for o in wall_targets:
    for i, mat in enumerate(o.data.materials):
        if mat and not mat.name.startswith('V19_'):
            o.data.materials[i]=wall_material(mat)

# World aligned wood boards: actual six boards per 1.2m tile, grain runs along Y.
m=bpy.data.materials.get('V19_Ceiling_warm_oak_boards') or bpy.data.materials.new('V19_Ceiling_warm_oak_boards')
m.use_nodes=True
ns,ls=m.node_tree.nodes,m.node_tree.links;ns.clear()
tc=ns.new('ShaderNodeTexCoord');tc.object=world
scale=ns.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=1/1.2
ls.new(tc.outputs['Object'],scale.inputs[0])
tex=ns.new('ShaderNodeTexImage');tex.image=ceiling_image;tex.projection='BOX';tex.extension='REPEAT'
ls.new(scale.outputs['Vector'],tex.inputs['Vector'])
bs=ns.new('ShaderNodeBsdfPrincipled');bs.inputs['Roughness'].default_value=.67
ls.new(tex.outputs['Color'],bs.inputs['Base Color'])
bump=ns.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.001
ls.new(tex.outputs['Color'],bump.inputs['Height']);ls.new(bump.outputs['Normal'],bs.inputs['Normal'])
out=ns.new('ShaderNodeOutputMaterial');ls.new(bs.outputs[0],out.inputs['Surface'])
m.diffuse_color=(.20,.09,.035,1);m['board_width_metres']=.2
ceilings=[]
for o in bpy.data.collections['18_BAR_Ceiling_toggle'].objects:
    if o.type=='MESH' and o.name.startswith(('V13_Ceiling_perimeter','V13_Ceiling_raised','V13_Ceiling_step')):
        o.data.materials.clear();o.data.materials.append(m);ceilings.append(o.name)

# Beams are visibly darker than the boards, preserving structural rhythm.
beam_source=bpy.data.materials['V18_ceiling_smoked_oak']
beam=bpy.data.materials.get('V19_Beam_dark_smoked_oak')
if not beam:
    beam=beam_source.copy();beam.name='V19_Beam_dark_smoked_oak'
    ns,ls=beam.node_tree.nodes,beam.node_tree.links
    bs=next(n for n in ns if n.type=='BSDF_PRINCIPLED')
    old=bs.inputs['Base Color'].links[0].from_socket
    tint=ns.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1
    tint.inputs[2].default_value=(.56,.43,.32,1)
    ls.new(old,tint.inputs[1]);ls.new(tint.outputs[0],bs.inputs['Base Color'])
    beam.diffuse_color=(.13,.075,.04,1)
for o in bpy.data.collections['18_BAR_Ceiling_toggle'].objects:
    if o.type=='MESH' and o.name.startswith('V13_Ceiling_cross_beam'):
        o.data.materials.clear();o.data.materials.append(beam)

# Thin timber transition strip, against each wall, broken at doorways.
collection=bpy.data.collections.get('23_BAR_Wall_finish_v19')
if not collection:
    collection=bpy.data.collections.new('23_BAR_Wall_finish_v19');bpy.context.scene.collection.children.link(collection)
def trim(name, loc, dims):
    if bpy.data.objects.get(name):return
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.name=name;o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for c in list(o.users_collection):c.objects.unlink(o)
    collection.objects.link(o)
    o.data.materials.append(bpy.data.materials['V18_furniture_dark_walnut'])
    bevel=o.modifiers.new('Soft small timber edge','BEVEL');bevel.width=.004;bevel.segments=2
    # Physical planar UVs for trim timber.
    uv=o.data.uv_layers.new(name='V19_Trim_metres');uv.active_render=True
    for p in o.data.polygons:
        axis=max(range(3),key=lambda a:abs(p.normal[a]));axes=[a for a in range(3) if a!=axis]
        for li in p.loop_indices:
            v=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv=(v[axes[0]],v[axes[1]])

trim('V19_North_brick_cap',(4.2,14.167,.915),(8.4,.026,.038))
for i,(a,b) in enumerate([(5.58,9.33),(10.23,14.18)]):
    trim('V19_West_brick_cap_'+str(i),(.012,(a+b)/2,.915),(.026,b-a,.038))
for i,(a,b) in enumerate([(5.58,10.05),(10.95,12.83),(13.73,14.18)]):
    trim('V19_East_brick_cap_'+str(i),(8.387,(a+b)/2,.915),(.026,b-a,.038))
for i,(a,b) in enumerate([(0,6.93),(7.83,8.4)]):
    trim('V19_South_brick_cap_'+str(i),((a+b)/2,5.592,.915),(b-a,.026,.038))

for im in bpy.data.images:
    if im.source=='FILE':
        if not im.packed_file:im.pack()
        basename=os.path.basename(bpy.path.abspath(im.filepath))
        previous=os.path.join(r'C:\Users\kaka\Desktop\e002素材\月灯り_テクスチャー_v18',basename)
        target=os.path.join(OUT,basename)
        if os.path.exists(previous) and not os.path.exists(target):shutil.copy2(previous,target)
        if os.path.exists(target):im.filepath='//'+basename

notes='''月灯り v19：壁・天井の仕上げ
壁：床から90cmまで古レンガ、上部はくすんだタバコ色の塗り壁。境に細い濃色木製見切り。
天井：幅20cmの木張り。梁は既存のスモークオークで区別。
レンガと天井の原画像はHamster GPT Image 2.5 Flare / high / 2K。
壁のレンガ高さはV19_Brick90cm_upper_tobacco_*内 LESS_THAN (0.90)で変更可能。
天井コレクション18_BAR_Ceiling_toggleは従来通り表示・非表示切替。
テクスチャ画像はblendに全て内包。家具配置・ドア・消灯・酒隠しの操作は保持。
'''
with open(os.path.join(OUT,'変更内容_v19.txt'),'w',encoding='utf-8-sig') as f:f.write(notes)
t=bpy.data.texts.get('README_v19') or bpy.data.texts.new('README_v19');t.clear();t.write(notes)
print(json.dumps({'wall_objects':len(wall_targets),'ceiling_panels':ceilings,'trim_objects':len(collection.objects)},ensure_ascii=False))
