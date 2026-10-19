import bpy,math,os,random,shutil
from mathutils import Vector
random.seed(30)
O=r'C:\Users\kaka\Desktop\e002素材\月灯り_屋根裏_v30';os.makedirs(O,exist_ok=True)
c=bpy.data.collections.new('41_ATTIC_American_storage_v30');bpy.context.scene.collection.children.link(c)
src=open('bakery_v26.py',encoding='utf8').read();exec(src[src.index('def link('):src.index('# North wall:')].replace('BK26_','AT30_'))
brass=mat('aged_brass',(.36,.25,.095),.65);leather=mat('oxblood_leather',(.18,.055,.032));canvas=mat('dust_sheets',(.45,.42,.34));walnut=mat('walnut',(.20,.095,.04));wine=mat('old_upholstery',(.17,.10,.085));black=mat('records',(.018,.022,.021));ivory=mat('aged_paper',(.54,.48,.34))
def woodgrain(m):
 nt=m.node_tree;p=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=4;tex.inputs['Detail'].default_value=2
 co=nt.nodes.new('ShaderNodeTexCoord');mapping=nt.nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(4,40,3);nt.links.new(co.outputs['Generated'],mapping.inputs[0]);nt.links.new(mapping.outputs[0],tex.inputs['Vector'])
 ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.07,.028,.012,1);ramp.color_ramp.elements[1].color=(.30,.15,.065,1);nt.links.new(tex.outputs['Fac'],ramp.inputs[0]);nt.links.new(ramp.outputs[0],p.inputs['Base Color'])
woodgrain(walnut)
for o in bpy.data.objects:
 if o.name.startswith(('AT29_floor_','AT29_balcony_deck')):
  o.data.materials.clear();o.data.materials.append(walnut)
# A 55 cm storage recess keeps all five futons and the head-side circulation unchanged.
for name in ['AT29_south_wall','AT29_south_gable']:bpy.data.objects[name].location.y-=.55
box('recess_floor',(10.53,9.525,2.82),(6.66,.55,.16),walnut,.002)
for x in [7.15,13.91]:box('recess_side',(x,9.525,3.725),(.10,.55,1.65),plaster if 'plaster' in globals() else cream)
for o in bpy.data.objects:
 if o.name.startswith('AT29_roof_') and o.type=='MESH':
  for v in o.data.vertices:
   if abs(v.co.y-9.5)<.001:v.co.y=8.95 if o.name in ['AT29_roof_west','AT29_roof_east'] else 9.15
for o in list(bpy.data.objects):
 if o.name.startswith(('AT29_stored_trunk','AT29_trunk_band','AT29_stacked_carton','AT29_keyboard_case','AT29_case_latch','AT29_case_handle')):o.hide_render=True;o.hide_set(True)
def trunk(n,x,y,z,w,d,h,angle=0):
 root=bpy.data.objects.new('AT30_'+n+'_group',None);c.objects.link(root);root.location=(x,y,z);root.rotation_euler.z=angle
 def part(nn,p,di,ma,b=.012):
  ob=box(nn,p,di,ma,b);ob.parent=root;return ob
 part(n+'_body',(0,0,h/2),(w,d,h),leather)
 part(n+'_lid',(0,0,h-.045),(w+.01,d+.01,.09),walnut)
 for xx in [-w*.32,w*.32]:
  part(n+'_strap',(xx,0,h+.004),(.035,d,.014),brass,.003)
  part(n+'_strapfront',(xx,d/2+.007,h/2),(.035,.018,h),brass,.002)
  part(n+'_latch',(xx,d/2+.018,h*.73),(.06,.025,.06),brass,.005)
 part(n+'_handle',(0,d/2+.05,h*.52),(.16,.035,.04),dark)
 return root
def crate(x,y,z,w,d,h,ang=0):
 root=bpy.data.objects.new('AT30_crate_group',None);c.objects.link(root);root.location=(x,y,z);root.rotation_euler.z=ang
 for i in range(4):
  for yy in [-d/2,d/2]:
   ob=box('crate_slats',(0,yy,(i+.5)*h/4),(w,.025,h/4-.012),wood);ob.parent=root
 for xx in [-w/2,w/2]:
  ob=box('crate_end',(xx,0,h/2),(.025,d,h),walnut);ob.parent=root
 return root
trunk('steamer_trunk',7.90,9.64,2.90,1.08,.55,.53,.025)
trunk('small_suitcase',8.03,9.63,3.45,.72,.42,.22,-.10)
crate(8.90,9.61,2.90,.58,.56,.61,-.04);crate(8.84,9.60,3.53,.51,.48,.41,.08)
trunk('hat_case',9.45,9.59,2.90,.50,.48,.38,-.10)
# A mismatched bookcase rises behind floor cargo, books lean in clusters.
for z in [3.08,3.66,4.24]:box('bookcase_shelf',(10.24,9.48,z),(1.0,.36,.035),walnut)
for x in [9.74,10.74]:box('bookcase_side',(x,9.48,3.76),(.035,.36,1.43),walnut)
for i in range(12):
 h=random.uniform(.26,.40);ob=box('old_book',(9.82+i*.072,9.47,3.685+h/2),(.06,.23,h),[green,leather,ivory,wood][i%4],.002);ob.rotation_euler.y=random.uniform(-.07,.07)
for i in range(5):box('sheet_music_stack',(10.35,9.48,4.27+i*.022),(.47,.25,.017),ivory,.001)
crate(10.26,9.59,2.90,.83,.48,.59,.01)
# Old record player, clearly a lid and turntable, on a low chest.
trunk('record_chest',11.26,9.57,2.90,.81,.48,.66,-.018)
box('gramophone_base',(11.26,9.57,3.64),(.55,.39,.07),walnut)
cyl('turntable',(11.23,9.57,3.687),.155,.012,black);cyl('record_label',(11.23,9.57,3.695),.04,.005,ivory)
lid=box('record_player_lid',(11.26,9.37,3.91),(.55,.025,.47),walnut);lid.rotation_euler.x=math.radians(-12)
rod('tonearm',(11.48,9.41,3.72),(11.33,9.64,3.72),.008,brass)
for i in range(7):
 ob=box('record_sleeve',(11.86+i*.032,9.58,3.10),(.026,.33,.38),[ivory,green,leather][i%3]);ob.rotation_euler.y=.12
# Cloth-covered chair silhouettes and leaning frames at the east end.
def chair(x,y,z,angle):
 root=bpy.data.objects.new('AT30_spare_chair',None);c.objects.link(root);root.location=(x,y,z);root.rotation_euler.z=angle
 for xx in [-.18,.18]:
  for yy in [-.18,.18]:
   ob=box('chair_leg',(xx,yy,.23),(.035,.035,.46),walnut);ob.parent=root
 for p,di in [((0,0,.47),(.46,.44,.06)),((0,-.19,.75),(.44,.035,.49))]:
  ob=box('chair_wood',p,di,walnut);ob.parent=root
 # drape as an irregular mesh rather than a rectangular cap
 vv=[(-.27,-.24,.99),(.27,-.24,.96),(-.26,-.15,.49),(.25,-.12,.51),(-.29,.26,.47),(.28,.26,.43),(-.24,.27,.12),(.27,.26,.16)]
 me=bpy.data.meshes.new('cloth');me.from_pydata(vv,[],[(0,1,3,2),(2,3,5,4),(4,5,7,6)]);ob=bpy.data.objects.new('AT30_draped_sheet',me);c.objects.link(ob);ob.parent=root;me.materials.append(canvas);md=ob.modifiers.new('cloth thickness','SOLIDIFY');md.thickness=.005
chair(12.56,9.61,2.90,.14);chair(13.14,9.60,2.90,-.11)
def frame(n,x,y,z,w,h,ang=0):
 rt=bpy.data.objects.new('AT30_'+n,None);c.objects.link(rt);rt.location=(x,y,z);rt.rotation_euler=(math.radians(-8),0,ang)
 for p,di in [((0,0,-h/2),(w,.045,.04)),((0,0,h/2),(w,.045,.04)),((-w/2,0,0),(.04,.045,h)),((w/2,0,0),(.04,.045,h))]:
  ob=box('picture_frame',p,di,walnut);ob.parent=rt
 ob=box('faded_picture',(0,-.008,0),(w-.05,.012,h-.05),ivory);ob.parent=rt
 # faint silhouettes in lieu of invented photographs
 for xx in [-w*.15,w*.13]:
  ob=ball('portrait_silhouette',(xx,.008,.04),(.045,.005,.07),wood);ob.parent=rt
frame('leaning_portrait',13.60,9.57,3.36,.40,.79,-.07)
frame('family_frame',10.02,9.44,4.51,.31,.43,.025)
# Brass lamp and bottles bring recognisable small-scale details.
rod('lamp_stem',(8.04,9.60,3.69),(8.04,9.60,4.09),.018,brass);cyl('lamp_foot',(8.04,9.60,3.69),.11,.028,brass)
bpy.ops.mesh.primitive_cone_add(vertices=40,radius1=.18,radius2=.09,depth=.21,location=(8.04,9.60,4.13));link(bpy.context.object,'fabric_lampshade',ivory)
for i in range(3):
 x=8.74+i*.105;cyl('old_bottle',(x,9.62,4.075),.043,.23,green);cyl('bottle_neck',(x,9.62,4.23),.018,.09,green)
# Bench by the balcony: a small American-style upholstered settee, away from the hatch exit.
box('settee_seat',(13.03,13.77,3.35),(1.21,.48,.16),wine,.065)
box('settee_back',(13.03,14.015,3.68),(1.25,.12,.72),wine,.06)
for x in [12.40,13.66]:box('settee_arm',(x,13.77,3.53),(.12,.49,.19),walnut,.05)
for x in [12.51,13.55]:
 for y in [13.62,13.92]:rod('settee_leg',(x,y,2.91),(x,y,3.28),.025,walnut)
for x in [12.75,13.25]:box('settee_cushion',(x,13.79,3.53),(.39,.30,.15),canvas,.055)
# Sparse planking and nails give the attic a timber interior rather than plain plaster.
for i in range(17):
 x=7.25+i*.41;box('south_wainscot',(x,9.19,3.63),(.39,.035,1.44),walnut,.003)
for x in [7.22,13.84]:box('corner_post',(x,11.90,3.73),(.07,4.20,.07),walnut)
# Warm practical to complement the existing blue moonlight.
ld=bpy.data.lights.new('AT30_table_lamp','POINT');lo=bpy.data.objects.new('AT30_table_lamp',ld);c.objects.link(lo);lo.location=(8.04,9.65,4.08);ld.energy=25;ld.color=(1,.66,.32);ld.shadow_soft_size=.16
def cam(n,p,t,lens):
 da=bpy.data.cameras.new(n);ob=bpy.data.objects.new(n,da);c.objects.link(ob);ob.location=p;ob.rotation_euler=(Vector(t)-ob.location).to_track_quat('-Z','Y').to_euler();da.lens=lens;return ob
ca=cam('Camera_AT30_storage',(12.95,12.82,4.35),(10.10,9.63,3.79),21)
cb=cam('Camera_AT30_moon',(7.60,10.33,4.35),(10.6,13.03,3.66),18)
s=bpy.context.scene;s.camera=ca;s.render.resolution_x=1400;s.render.resolution_y=1000
note='''屋根裏 v30：指定の月明かり屋根裏部屋.pngを参照。
足元側に55cmの収納用のくぼみを追加し、布団5枚と枕側通路を維持。
トランク、木箱、譜面、本、古いレコードプレーヤー、布をかけた予備椅子、額縁、真鍮ランプを重ねる配置。
板張りと深い木色、小さな洋風長椅子でアメリカの古い店の屋根裏の方向へ。
布団と引き戸はv29の仕様。人物の動作確認は未実施。小物・写真は仮形状。
41_ATTIC_American_storage_v30が今回追加分。屋根と布団の表示切替はv29と同じ。
'''
open(os.path.join(O,'屋根裏_v30_変更点.txt'),'w',encoding='utf8').write(note);tx=bpy.data.texts.new('README_ATTIC_v30');tx.write(note)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(O,'月灯り_舞台設計_屋根裏_v30.blend'))
for camera,fn in [(ca,'屋根裏_雑多な収納.png'),(cb,'屋根裏_布団と月明かり.png')]:
 s.camera=camera;s.render.filepath=os.path.join(O,fn);bpy.ops.render.render(write_still=True)
shutil.copy2('attic_v30.py',O)
print('DONE V30')
