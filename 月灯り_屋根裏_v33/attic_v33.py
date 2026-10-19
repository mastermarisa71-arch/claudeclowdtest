import bpy,math,os,shutil
from mathutils import Vector,Matrix
O=r'C:\Users\kaka\Desktop\e002素材\月灯り_屋根裏_v33';os.makedirs(O,exist_ok=True)
c=bpy.data.collections.new('45_ATTIC_Accumulated_storage_v33');bpy.context.scene.collection.children.link(c)
src=open('bakery_v26.py',encoding='utf8').read();exec(src[src.index('def link('):src.index('# North wall:')].replace('BK26_','AT33_'))
walnut=bpy.data.materials['AT30_walnut'];brass=bpy.data.materials['AT30_aged_brass'];linen=bpy.data.materials['AT30_dust_sheets'];leather=bpy.data.materials['AT30_oxblood_leather'];ivory=bpy.data.materials['AT30_aged_paper']
def select(prefix):return [o for o in bpy.data.objects if o.name.startswith(prefix)]
def turn(obs,center,deg,dx=0,dy=0,inverse=False):
 p=Vector(center);M=Matrix.Translation(p+Vector((dx,dy,0)))@Matrix.Rotation(math.radians(deg),4,'Z')@Matrix.Translation(-p)
 if inverse:M=M.inverted()
 ss=set(obs)
 for o in obs:
  if o.parent not in ss:o.matrix_world=M@o.matrix_world
sofa=select(('AT31_old_sofa','AT31_sofa_','AT31_throw_hanging'));turn(sofa,(5.8,12.37,2.9),-19,-.05,-.23,True);turn(sofa,(5.8,12.37,2.9),-3)
tableobs=select(('AT31_antique_table','AT31_turned_table','AT31_table_apron','AT31_books_on_table','AT31_tea_mug'));turn(tableobs,(5.88,10.74,2.9),27,-.10,.06,True);turn(tableobs,(5.88,10.74,2.9),2)
settee=select('AT30_settee');turn(settee,(13.03,13.77,2.9),-9,-.03,-.18,True)
# Remove deliberate scatter; retain architecture, bed arrangement and usable furniture.
bpy.data.collections['44_ATTIC_Irregular_piles_v32'].hide_render=True;bpy.data.collections['44_ATTIC_Irregular_piles_v32'].hide_viewport=True
source=bpy.data.collections['41_ATTIC_American_storage_v30']
for o in source.objects:
 if not o.name.startswith(('AT30_recess_floor','AT30_settee')):o.hide_render=True;o.hide_set(True)
for o in bpy.data.collections['42_ATTIC_Expanded_store_v31'].objects:
 if o.name.startswith(('AT31_bookcase_group','AT31_case_board','AT31_stock_book','AT31_stored_tabletop','AT31_rolled_rug')):o.hide_render=True;o.hide_set(True)
roots=[o for o in source.objects if o.type=='EMPTY']
trunks=[o for o in roots if any(k in o.name for k in ['steamer_trunk_group','small_suitcase_group','hat_case_group'])]
crates=[o for o in roots if 'crate_group' in o.name];chairs=[o for o in roots if 'spare_chair' in o.name]
def group(proto,x,y,z,deg=0,scale=1):
 mp={}
 for old in [proto]+list(proto.children_recursive):
  ob=old.copy();c.objects.link(ob);ob.name='AT33_'+old.name;ob.hide_render=False;ob.hide_set(False);mp[old]=ob
 for old,new in mp.items():
  if old.parent in mp:new.parent=mp[old.parent]
 rt=mp[proto];rt.location=(x,y,z);rt.rotation_euler=(0,0,math.radians(deg));rt.scale=(scale,)*3
 bpy.context.view_layer.update();pts=[ob.matrix_world@Vector(v) for ob in rt.children_recursive if ob.type=='MESH' for v in ob.bound_box]
 return rt,max(p.z for p in pts)
def stack(p,x,y,scale=1,angle=0,upper=True):
 rt,z=group(p,x,y,2.9,angle,scale)
 if upper:group(crates[0],x+.025,y-.015,z+.006,angle+4,scale*.75)
 return rt
def shelf(n,x,y,w,d,h,angle=0):
 rt=bpy.data.objects.new('AT33_'+n,None);c.objects.link(rt);rt.location=(x,y,2.9);rt.rotation_euler.z=math.radians(angle)
 for pos,dim in [((-w/2,0,h/2),(.045,d,h)),((w/2,0,h/2),(.045,d,h)),((0,-d/2,h/2),(w,.025,h))]+[((0,0,z),(w,d,.035)) for z in [.07,.53,1.0,h]]:
  ob=box(n+'_board',pos,dim,walnut);ob.parent=rt
 return rt
# South-west: old furniture, stacked for space rather than displayed separately.
for x,y,deg in [(4.25,6.72,0),(4.83,6.74,0),(5.40,6.70,2)]:
 rt,z=group(chairs[0],x,y,2.9,deg,.97);group(chairs[1%len(chairs)],x+.01,y,z+.01,deg+180,.87)
for x,y,deg in [(4.35,7.54,0),(5.07,7.57,0),(5.67,7.57,3)]:stack(crates[0],x,y,.98,deg)
for x,y,deg in [(4.30,8.32,0),(4.94,8.33,0),(5.63,8.30,-2)]:stack(trunks[0],x,y,.60,deg)
# One chair has been pulled out to reach something behind it.
group(chairs[0],5.88,9.10,2.9,12,.94)
ob=box('spare_table_leaf',(4.03,9.04,3.67),(.065,.85,1.52),walnut);ob.rotation_euler.y=.12
for i in range(3):
 ob=cyl('stored_rug',(4.16+i*.27,9.75,3.56),.12,1.30,linen);ob.rotation_euler.y=.05
# South centre: bakery overflow, shelf against wall, containers gathered below.
shelf('bakery_storage',7.70,6.47,2.10,.43,1.43)
for row,z in enumerate([3.47,3.94]):
 for i in range(5):
  x=6.87+i*.39
  box('baking_tin',(x,6.48,z),(.28,.27,.12),steel,.004)
  if row==1:box('tin_stack_lip',(x,6.48,z+.073),(.29,.28,.018),steel,.003)
for x,y in [(6.90,7.15),(7.55,7.16),(8.21,7.13)]:stack(crates[0],x,y,1.03,0)
for x,y,deg in [(7.0,7.92,0),(7.68,7.94,0),(8.36,7.90,-4)]:stack(crates[1%len(crates)],x,y,.98,deg)
for i,x in enumerate([6.92,7.55,8.17]):
 box('baking_carton',(x,8.62,3.22),(.53,.50,.64),paper)
 box('carton_tape',(x,8.62,3.545),(.04,.50,.009),wood)
# A just-delivered carton rests at the accessible edge, not in a random gap.
ob=box('recent_delivery',(8.60,9.06,3.13),(.58,.44,.46),paper);ob.rotation_euler.z=math.radians(7)
# South-east: instruments and records, forming one storage bay.
shelf('music_storage',11.31,6.49,2.50,.44,1.43)
for i in range(17):
 h=.29+(.04 if i%3==0 else 0);ob=box('sheet_music',(10.23+i*.13,6.48,3.48+h/2),(.10,.28,h),[ivory,green,wood][i%3],.002)
 if i in [5,6]:ob.rotation_euler.y=.06
for i in range(5):box('paper_music_stack',(10.44,6.49,3.94+i*.021),(.51,.29,.017),ivory,.002)
case=box('long_instrument_case',(11.65,6.48,4.08),(1.12,.32,.30),dark)
for x in [11.29,12.0]:box('case_clasp',(x,6.65,4.10),(.055,.025,.05),brass)
for x,y,deg in [(10.10,7.18,0),(11.18,7.18,0),(12.26,7.18,0),(10.09,7.92,0),(11.18,7.94,2)]:stack(trunks[0],x,y,.92,deg)
for x,y,deg in [(12.50,8.17,-3),(12.95,8.89,0)]:stack(crates[0],x,y,1.0,deg)
# Record player is kept on a chest in the music corner and can be used there.
ch,z=group(bpy.data.objects['AT30_record_chest_group'],12.96,9.55,2.9,90,1)
box('record_player',(12.96,9.55,z+.055),(.40,.55,.09),walnut)
cyl('record',(12.96,9.53,z+.106),.16,.012,dark);cyl('label',(12.96,9.53,z+.115),.04,.005,ivory)
# Bed clearing: low possessions are pushed together at the foot, leaving a retrieval side.
for x,y,deg in [(9.35,9.82,0),(10.42,9.82,0),(11.50,9.79,3)]:stack(trunks[0],x,y,.90,deg,False)
group(crates[0],9.38,9.82,3.39,4,.64)
# Window side: bedding storage, rather than arbitrary boxes on every free tile.
rt,top=group(trunks[0],7.94,13.57,2.9,0,.93)
for i in range(3):box('folded_blanket',(7.94,13.57,top+.04+i*.065),(.63,.36,.06),linen if i%2 else green,.025)
box('linen_basket',(8.59,13.56,3.13),(.40,.43,.46),wood)
for x in [8.48,8.68]:ball('spare_pillow',(x,13.57,3.40),(.12,.17,.085),cream)
group(trunks[1%len(trunks)],11.72,13.62,2.9,0,.98)
group(chairs[0],11.91,13.61,3.14,180,.71)
# Balcony corner holds an old wooden crate and empty pots used outside.
rt,z=group(crates[0],8.48,15.20,2.9,0,.94)
for x in [8.34,8.60]:
 cyl('empty_pot',(x,15.20,z+.085),.085,.17,wood);cyl('pot_dark_inside',(x,15.20,z+.173),.068,.003,dark)
# Furniture by sofa: one spare chair pulled over to the table.
group(chairs[0],6.71,11.22,2.9,-8,.92)
# A warm lamp on a real small crate next to the sofa.
rt,z=group(crates[0],4.46,12.58,2.9,0,.82)
rod('lamp_stem',(4.46,12.58,z+.02),(4.46,12.58,z+.35),.016,brass)
bpy.ops.mesh.primitive_cone_add(vertices=32,radius1=.17,radius2=.08,depth=.20,location=(4.46,12.58,z+.40));link(bpy.context.object,'lamp_shade',ivory)
ld=bpy.data.lights.new('AT33_lamp','POINT');lo=bpy.data.objects.new('AT33_lamp',ld);c.objects.link(lo);lo.location=(4.46,12.58,z+.35);ld.energy=24;ld.color=(1,.7,.4);ld.shadow_soft_size=.15
s=bpy.context.scene;s.camera=bpy.data.objects['Camera_AT31_storage']
note='''屋根裏 v33：無作為な角度・散在をやめ、用途と置いた経緯で再配置。
南西＝古い家具、南中央＝パン屋の予備道具、南東＝楽器・譜面・レコード。
ソファ・大テーブルは壁の方向へ戻す。通常収納はほぼ揃え、引き出した椅子・後置きの箱・積み直した上段だけ小さくずらす。
布団の足元は今夜のために寄せた荷物。窓側は予備寝具、ベランダ隅は外で使う空き鉢。
5枚の布団、階段出口、ベランダへの中央動線を維持。人物動作は未検証。
45_ATTIC_Accumulated_storage_v33が新規配置。v32のランダム群は非表示。
'''
open(os.path.join(O,'屋根裏_v33_変更点.txt'),'w',encoding='utf8').write(note)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(O,'月灯り_舞台設計_屋根裏_v33.blend'))
s.render.filepath=os.path.join(O,'屋根裏_使われてきた物置.png');bpy.ops.render.render(write_still=True)
bpy.data.collections['43_ATTIC_Roof_toggle_v31'].hide_render=True
for o in bpy.data.collections['42_ATTIC_Expanded_store_v31'].objects:
 if o.name.startswith(('AT31_rafter','AT31_ridge')):o.hide_render=True
ld=bpy.data.lights.new('inspection','AREA');lo=bpy.data.objects.new('inspection',ld);s.collection.objects.link(lo);lo.location=(8,10,16);ld.energy=2300;ld.size=10
s.camera=bpy.data.objects['Camera_AT31_top'];s.render.filepath=os.path.join(O,'屋根裏_俯瞰.png');bpy.ops.render.render(write_still=True)
shutil.copy2('attic_v33.py',O)
print('DONE V33')
