import bpy,math,os,random,shutil
from mathutils import Vector,Matrix
random.seed(32)
O=r'C:\Users\kaka\Desktop\e002素材\月灯り_屋根裏_v32';os.makedirs(O,exist_ok=True)
c=bpy.data.collections.new('44_ATTIC_Irregular_piles_v32');bpy.context.scene.collection.children.link(c)
for o in bpy.data.objects:
 if o.name.startswith(('AT31_stock_','AT31_packed_carton','AT31_upper_carton','AT31_carton_tape')):o.hide_render=True;o.hide_set(True)
def turn(objects,center,deg,dx=0,dy=0):
 p=Vector(center);M=Matrix.Translation(p+Vector((dx,dy,0)))@Matrix.Rotation(math.radians(deg),4,'Z')@Matrix.Translation(-p)
 names=set(objects)
 for ob in objects:
  if ob.parent not in names:ob.matrix_world=M@ob.matrix_world
# Break alignment of the large usable furniture as assemblies.
turn([o for o in bpy.data.objects if o.name.startswith(('AT31_old_sofa','AT31_sofa_','AT31_throw_hanging'))],(5.8,12.37,2.9),-19,-.05,-.23)
turn([o for o in bpy.data.objects if o.name.startswith(('AT31_antique_table','AT31_turned_table','AT31_table_apron','AT31_books_on_table','AT31_tea_mug'))],(5.88,10.74,2.9),27,-.10,.06)
turn([o for o in bpy.data.objects if o.name.startswith('AT30_settee')],(13.03,13.77,2.9),-9,-.03,-.18)
# Foot-side possessions become offset islands rather than a continuous straight frontage.
turn([o for o in bpy.data.objects if o.name.startswith(('AT30_bookcase_','AT30_old_book','AT30_sheet_music_stack'))],(10.24,9.48,2.9),-26,-.16,-.55)
turn([o for o in bpy.data.objects if o.name.startswith(('AT30_gramophone','AT30_turntable','AT30_record_label','AT30_record_player_lid','AT30_tonearm'))],(11.26,9.57,2.9),21,.08,-.30)
root=bpy.data.objects.get('AT30_record_chest_group')
if root:turn([root]+list(root.children_recursive),(11.26,9.57,2.9),21,.08,-.30)
for o in [o for o in bpy.data.objects if o.name.startswith('AT31_bookcase_group')]:
 turn([o]+list(o.children_recursive),o.location,24 if o.location.x<10 else -24,-.15,-.1)
# Linked copies of detailed trunks, crates and draped chairs, composed in irregular piles.
src=bpy.data.collections['41_ATTIC_American_storage_v30']
trunks=[o for o in src.objects if o.type=='EMPTY' and any(k in o.name for k in ['steamer_trunk_group','small_suitcase_group','hat_case_group'])]
crates=[o for o in src.objects if o.type=='EMPTY' and 'crate_group' in o.name]
chairs=[o for o in src.objects if o.type=='EMPTY' and 'spare_chair' in o.name]
def copygroup(proto,x,y,z,angle,scale=1):
 mp={}
 for old in [proto]+list(proto.children_recursive):
  ob=old.copy();c.objects.link(ob);ob.name='AT32_'+old.name;ob.hide_render=False;ob.hide_set(False);mp[old]=ob
 for old,new in mp.items():
  if old.parent in mp:new.parent=mp[old.parent]
 rt=mp[proto];rt.location=(x,y,z);rt.rotation_euler=(0,0,math.radians(angle));rt.scale=(scale,)*3
 return rt
# Different-sized clusters; deliberately neither common row centres nor shared angles.
layout=[
 (4.45,6.80,-24,1.0),(5.45,7.17,32,.95),(4.39,7.76,-39,.92),(5.40,8.13,17,.90),
 (6.71,6.81,-32,1.0),(7.68,6.62,19,.9),(7.55,7.68,-42,1.05),(8.45,7.19,33,.94),
 (9.49,6.62,-18,1.0),(10.52,7.04,40,1.08),(9.25,7.64,24,.9),(10.10,8.19,-31,.92),
 (12.0,6.75,-34,.96),(13.09,7.17,27,.9),(12.13,7.83,41,1.0),(13.00,8.49,-23,.91),
 (4.37,9.24,32,1.03),(5.08,9.34,-24,.9),(4.28,10.24,-35,.87),
 (4.37,13.44,24,1.0),(5.35,13.60,-31,.95),(6.37,13.58,36,.9),
 # Balcony side now contains storage on both sides of a narrow central access.
 (7.72,13.48,29,.88),(8.36,13.57,-22,.78),(11.55,13.56,31,.88),
 (8.51,14.84,-28,.85),(11.72,15.16,24,.82)]
for i,(x,y,a,sc) in enumerate(layout):
 p=trunks[i%len(trunks)] if i%3==0 else crates[i%len(crates)]
 base=copygroup(p,x,y,2.9,a,sc)
 # Measure each base's actual top before placing its next object.
 bpy.context.view_layer.update();pts=[ob.matrix_world@Vector(v) for ob in base.children_recursive if ob.type=='MESH' for v in ob.bound_box]
 top=max(v.z for v in pts)
 if i%3!=1:
  q=trunks[1%len(trunks)] if i%4==0 else crates[(i+1)%len(crates)]
  copygroup(q,x+.035,y-.025,top+.007,a+random.choice([-27,22,35]),sc*.70)
 if i in [1,8,14,19]:copygroup(chairs[i%len(chairs)],x+.02,y+.03,top+.01,a-28,.78)
# Offset the original crates too; retain bed clearance along y10.35.
for i,rt in enumerate([o for o in src.objects if o.type=='EMPTY' and 'crate_group' in o.name]):
 turn([rt]+list(rt.children_recursive),rt.location,(-17 if i%2 else 23),-.10,-.18)
# One leaning chair beside the antique table, a rug roll against the west piles.
copygroup(chairs[0],6.68,11.58,2.9,-32,.92)
# Add broad leaning boards and frames to disrupt box-only silhouettes.
wood=bpy.data.materials['AT30_walnut']
def board(n,p,size,rot):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=n;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.rotation_euler=rot
 for cc in list(o.users_collection):cc.objects.unlink(o)
 c.objects.link(o);o.data.materials.append(wood)
board('AT32_leaning_table_leaf',(4.08,8.79,3.73),(.06,.72,1.7),(0,.15,-.22))
board('AT32_old_sign_back',(12.85,6.49,3.62),(1.15,.05,1.4),(-.12,0,.29))
s=bpy.context.scene;s.camera=bpy.data.objects['Camera_AT31_storage']
note='''屋根裏 v32：格子配置を解消するため収納を島状に再配置。
箱だけでなく、ソファ・大型テーブル・本棚・レコード台を15～40度程度振り、位置の列も崩した。
ベランダ手前の左右とベランダ両隅にも収納を配置。中央の出入口、階段出口、5枚の布団の床面は確保。
積み上げ物は下の箱の上面を取得して置く仮配置。人物・扉を動かした詳細干渉確認は未実施。
44_ATTIC_Irregular_piles_v32が新しい収納群。以前の規則的な収納群は非表示。
'''
open(os.path.join(O,'屋根裏_v32_変更点.txt'),'w',encoding='utf8').write(note)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(O,'月灯り_舞台設計_屋根裏_v32.blend'))
s.render.filepath=os.path.join(O,'屋根裏_乱雑な家具配置.png');bpy.ops.render.render(write_still=True)
bpy.data.collections['43_ATTIC_Roof_toggle_v31'].hide_render=True
for o in bpy.data.collections['42_ATTIC_Expanded_store_v31'].objects:
 if o.name.startswith(('AT31_rafter','AT31_ridge')):o.hide_render=True
ld=bpy.data.lights.new('inspection','AREA');lo=bpy.data.objects.new('inspection',ld);s.collection.objects.link(lo);lo.location=(8,10,16);ld.energy=2300;ld.size=10
s.camera=bpy.data.objects['Camera_AT31_top'];s.render.filepath=os.path.join(O,'屋根裏_俯瞰.png');bpy.ops.render.render(write_still=True)
shutil.copy2('attic_v32.py',O)
print('DONE V32')
