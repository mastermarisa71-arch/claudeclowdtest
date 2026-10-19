import bpy,math,os,random,shutil
from mathutils import Vector
random.seed(31)
O=r'C:\Users\kaka\Desktop\e002素材\月灯り_屋根裏_v31';os.makedirs(O,exist_ok=True)
c=bpy.data.collections.new('42_ATTIC_Expanded_store_v31');bpy.context.scene.collection.children.link(c)
src=open('bakery_v26.py',encoding='utf8').read();exec(src[src.index('def link('):src.index('# North wall:')].replace('BK26_','AT31_'))
walnut=bpy.data.materials['AT30_walnut'];cloth=bpy.data.materials['AT30_dust_sheets'];uphol=bpy.data.materials['AT30_old_upholstery'];brass=bpy.data.materials['AT30_aged_brass'];plaster=bpy.data.materials['AT29_plaster'];slate=bpy.data.materials['AT29_roof']
# Keep northern living nook, five futons, balcony and original stair positions.
hideprefix=('AT29_west_wall','AT29_south_wall','AT29_south_gable','AT29_rafter','AT29_ridge','AT30_recess_side','AT30_south_wainscot','AT30_corner_post','AT30_old_clothes_rail','AT30_clothes_bracket','AT30_hanger','AT30_stored_coat','AT30_coat_button')
for o in bpy.data.objects:
 if o.name.startswith(hideprefix):o.hide_render=True;o.hide_set(True)
bpy.data.collections['37_ATTIC_Roof_toggle_v29'].hide_render=True;bpy.data.collections['37_ATTIC_Roof_toggle_v29'].hide_viewport=True
bpy.data.collections['40_ATTIC_Surrounding_roof_v29'].hide_render=True;bpy.data.collections['40_ATTIC_Surrounding_roof_v29'].hide_viewport=True
roofco=bpy.data.collections.new('43_ATTIC_Roof_toggle_v31');bpy.context.scene.collection.children.link(roofco)
def poly(n,pts,co,m,th=.08):
 me=bpy.data.meshes.new(n);me.from_pydata(pts,[],[tuple(range(len(pts)))]);me.update();o=bpy.data.objects.new('AT31_'+n,me);co.objects.link(o);me.materials.append(m)
 if th:mod=o.modifiers.new('thickness','SOLIDIFY');mod.thickness=th
 return o
def beam(n,a,b,w=.1):
 o=box(n,(Vector(a)+Vector(b))/2,(w,w,(Vector(b)-Vector(a)).length),walnut);o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler();return o
# Approx. 10.06 x 7.9 =79.5 sqm: sleeping / staying area remains around 24 sqm.
box('floor_south',(8.83,7.725,2.82),(10.06,3.05,.16),walnut,.001)
box('floor_west',(5.50,11.675,2.82),(3.40,4.85,.16),walnut,.001)
box('west_wall',(3.75,10.15,3.725),(.10,8.0,1.65),plaster)
box('south_wall',(8.83,6.15,3.725),(10.26,.10,1.65),plaster)
box('east_extension',(13.91,7.725,3.725),(.10,3.05,1.65),plaster)
box('north_extension',(5.45,14.15,3.725),(3.5,.10,1.65),plaster)
# Existing high north gable stays at balcony; transition roof over expanded storage.
poly('south_gable',[(3.7,6.15,4.55),(13.96,6.15,4.55),(10.53,6.15,5.95)],c,plaster)
poly('north_storage_gable',[(3.7,14.15,4.55),(7.10,14.15,4.55),(7.10,14.15,5.25)],c,plaster)
poly('west_roof',[(3.55,5.95,4.50),(10.53,5.95,5.95),(10.53,14.4,5.95),(3.55,14.4,4.50)],roofco,slate)
poly('east_roof',[(10.53,5.95,5.95),(14.06,5.95,4.50),(14.06,14.4,4.50),(10.53,14.4,5.95)],roofco,slate)
for y in [6.55,9.05,11.65,13.88]:
 beam('rafter',(3.8,y,4.50),(10.53,y,5.83));beam('rafter',(10.53,y,5.83),(13.84,y,4.50))
beam('ridge',(10.53,6.2,5.83),(10.53,14.1,5.83),.13)
# Reuse detailed props as stored clusters, linked meshes keep scene manageable.
protos=[o for o in bpy.data.collections['41_ATTIC_American_storage_v30'].objects if o.type=='EMPTY' and ('group' in o.name or 'spare_chair' in o.name)]
def duplicate_group(root,x,y,z,angle,scale=1):
 mapping={}
 for old in [root]+list(root.children_recursive):
  ob=old.copy();c.objects.link(ob);ob.name='AT31_stock_'+old.name;mapping[old]=ob
 for old,new in mapping.items():
  if old.parent in mapping:new.parent=mapping[old.parent]
 rt=mapping[root];rt.location=(x,y,z);rt.rotation_euler.z=angle;rt.scale=(scale,scale,scale)
 return rt
trunks=[o for o in protos if 'trunk' in o.name or 'suitcase' in o.name or 'hat_case' in o.name]
crates=[o for o in protos if 'crate' in o.name]
chairs=[o for o in protos if 'spare_chair' in o.name]
for i,(x,y) in enumerate([(4.4,6.85),(5.5,6.8),(6.6,6.8),(7.8,6.9),(9.0,6.75),(10.2,6.9),(11.6,6.8),(13.0,6.8),(4.4,8.0),(5.5,8.2),(7.3,8.0),(8.5,8.2),(10.0,8.0),(11.2,8.1),(12.8,8.1),(4.35,9.6),(4.4,10.6),(4.3,13.45),(5.4,13.6),(6.6,13.55)]):
 rt=duplicate_group(trunks[i%len(trunks)] if i%3==0 else crates[i%len(crates)],x,y,2.90,random.uniform(-.18,.18),random.uniform(.85,1.20))
 if i%3!=1:
  duplicate_group(crates[(i+1)%len(crates)],x+.06,y-.04,3.48,random.uniform(-.25,.25),.83)
 if i in [1,5,9,13,17]:duplicate_group(chairs[i%len(chairs)],x,y,3.98,random.uniform(-.22,.22),.90)
# Tall stored shelving, perpendicular to walls, blocks long empty sightlines.
def bookcase(x,y,w,d,h,angle=0):
 root=bpy.data.objects.new('AT31_bookcase_group',None);c.objects.link(root);root.location=(x,y,2.9);root.rotation_euler.z=angle
 for p,di in [((-w/2,0,h/2),(.055,d,h)),((w/2,0,h/2),(.055,d,h)),((0,-d/2,h/2),(w,.025,h))]+[((0,0,z),(w,d,.035)) for z in [.08,h*.34,h*.67,h]]:
  ob=box('case_board',p,di,walnut);ob.parent=root
 for j in range(3):
  for i in range(7):
   hh=random.uniform(.22,.34);ob=box('stock_book',(-w*.40+i*w*.12,0,.11+j*h*.33+hh/2),(.07,d*.70,hh),[green,ivory if 'ivory' in globals() else paper,wood][i%3]);ob.parent=root;ob.rotation_euler.y=random.uniform(-.1,.1)
bookcase(6.27,8.42,1.55,.38,1.47,.07);bookcase(12.98,9.05,1.35,.34,1.48,-.10)
# Large antique table kept and casually used in storage-side nook.
table('antique_table',5.88,10.74,1.90,.89,.77,walnut)
# Existing helper builds ground-level furniture; raise all parts to attic floor.
for o in c.objects:
 if o.name.startswith('AT31_antique_table'):o.location.z+=2.90
for x in [5.02,6.74]:
 for y in [10.40,11.08]:
  for z,r in [(3.08,.065),(3.35,.052),(3.56,.07)]:cyl('turned_table_leg',(x,y,z),r,.10,walnut)
box('table_apron',(5.88,10.74,3.56),(1.80,.79,.17),walnut)
for i in range(4):box('books_on_table',(5.50,10.68,3.70+i*.035),(.36,.26,.03),paper)
cyl('tea_mug',(6.15,10.78,3.77),.045,.13,cream)
# Used old sofa, retaining a gap towards the central sleeping area.
box('old_sofa_base',(5.80,12.37,3.16),(2.10,.86,.36),walnut,.06)
box('old_sofa_back',(5.80,12.74,3.67),(2.12,.20,.87),uphol,.10)
for x in [4.77,6.83]:box('old_sofa_arm',(x,12.33,3.48),(.24,.84,.50),uphol,.09)
for x in [5.25,5.80,6.35]:box('sofa_cushion',(x,12.27,3.43),(.52,.66,.18),uphol,.07)
for x in [5.23,6.38]:
 ob=box('sofa_pillow',(x,12.53,3.69),(.40,.17,.36),cloth,.06);ob.rotation_euler.y=.1
box('sofa_throw',(6.5,12.20,3.56),(.42,.73,.055),cloth,.025)
box('throw_hanging',(6.5,11.85,3.34),(.42,.025,.46),cloth,.015)
# Rolled rug, large leaning tabletop and mixed chair stack lend broad silhouettes.
ob=cyl('rolled_rug',(4.04,11.70,3.56),.14,1.20,cloth);ob.rotation_euler.y=.15
ob=box('stored_tabletop',(11.85,7.0,3.92),(1.0,.09,1.80),walnut);ob.rotation_euler.x=-.12
for x,y,a in [(9.8,8.9,.2),(10.8,8.9,-.25),(4.2,9.0,.12)]:duplicate_group(chairs[0],x,y,2.9,a)
# Surrounding lower roof fills the building remainder.
poly('low_roof_front',[(3.55,-.2,2.85),(14.06,-.2,2.85),(14.06,5.95,3.1),(3.55,5.95,3.1)],roofco,slate)
poly('low_roof_west',[(-.2,-.2,2.85),(3.55,-.2,3.1),(3.55,14.38,3.1),(-.2,14.38,2.85)],roofco,slate)
# Additional dim attic light for layout readability.
ld=bpy.data.lights.new('AT31_storage_softlight','AREA');lo=bpy.data.objects.new('AT31_storage_softlight',ld);c.objects.link(lo);lo.location=(8.4,8,5.6);ld.energy=110;ld.color=(1,.76,.50);ld.size=4
def cam(n,p,t,lens=22,ortho=None):
 da=bpy.data.cameras.new(n);ob=bpy.data.objects.new(n,da);c.objects.link(ob);ob.location=p;ob.rotation_euler=(Vector(t)-ob.location).to_track_quat('-Z','Y').to_euler();da.lens=lens
 if ortho:da.type='ORTHO';da.ortho_scale=ortho
 return ob
ca=cam('Camera_AT31_storage',(12.15,11.9,4.42),(6.1,9.15,3.80),20)
top=cam('Camera_AT31_top',(8.8,10.5,19),(8.8,10.5,0),24,14.6)
whole=cam('Camera_AT31_building',(23,-11,23),(7,7,1.8),35,24)
s=bpy.context.scene;s.camera=ca;s.render.resolution_x=1500;s.render.resolution_y=1100
note='''屋根裏 v31：物置が主、人が入る空間が従という構成へ拡張。
室内約10.06×7.90m（約79.5m2）。収納域約7割・滞在域約3割を目標にしたゾーニング。物体投影面積の厳密な70%計算ではありません。
南側と西側に収納群を増設。収納の間の隙間も物置域に含む。北東側の5枚の布団と階段・引き戸・ベランダは維持。
西北側には古いソファと大型テーブルを置き、保管家具を仮使用する場所に。
俯瞰画像：屋根裏内部の全景、建物全体から見た接続位置。
43_ATTIC_Roof_toggle_v31で屋根を切替。42_ATTIC_Expanded_store_v31が増設分。38_ATTIC_Five_futons_toggle_v29で布団切替。
当初の小さな屋根裏より大きくなっています。今回の7:3と5人の布団・家具を両立するための拡張案です。
'''
open(os.path.join(O,'屋根裏_v31_設計メモ.txt'),'w',encoding='utf8').write(note);tx=bpy.data.texts.new('README_ATTIC_v31');tx.write(note)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(O,'月灯り_舞台設計_屋根裏_v31.blend'))
s.render.filepath=os.path.join(O,'屋根裏_物置の中の居場所.png');bpy.ops.render.render(write_still=True)
roofco.hide_render=True
hidden=[]
for o in c.objects:
 if o.name.startswith(('AT31_rafter','AT31_ridge')):hidden.append(o);o.hide_render=True
ld=bpy.data.lights.new('inspection','AREA');lo=bpy.data.objects.new('inspection',ld);s.collection.objects.link(lo);lo.location=(8.8,10,14);ld.energy=1800;ld.size=8
for cc,fn in [(top,'屋根裏_俯瞰.png'),(whole,'建物全体_屋根裏の位置.png')]:
 s.camera=cc;s.render.filepath=os.path.join(O,fn);bpy.ops.render.render(write_still=True)
bpy.data.objects.remove(lo,do_unlink=True)
roofco.hide_render=False
for o in hidden:o.hide_render=False
shutil.copy2('attic_v31.py',O)
print('DONE V31')
