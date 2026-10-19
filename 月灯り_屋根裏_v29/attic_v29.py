import bpy,math,os,shutil
from mathutils import Vector
O=r'C:\Users\kaka\Desktop\e002素材\月灯り_屋根裏_v29';os.makedirs(O,exist_ok=True)
for n in ['33_ATTIC_Room_and_balcony_v28','34_ATTIC_Roof_toggle_v28','35_ATTIC_Surrounding_roof_v28']:
 co=bpy.data.collections[n];co.hide_render=True;co.hide_viewport=True
c=bpy.data.collections.new('36_ATTIC_Wide_room_v29');bpy.context.scene.collection.children.link(c)
src=open('bakery_v26.py',encoding='utf8').read();exec(src[src.index('def link('):src.index('# North wall:')].replace('BK26_','AT29_'))
def coll(n):
 co=bpy.data.collections.new(n);bpy.context.scene.collection.children.link(co);return co
roofco=coll('37_ATTIC_Roof_toggle_v29');bedco=coll('38_ATTIC_Five_futons_toggle_v29');nightco=coll('39_ATTIC_Moonlight_toggle_v29')
def move(o,co):
 for cc in list(o.users_collection):cc.objects.unlink(o)
 co.objects.link(o);return o
timber=mat('beam',(.14,.075,.042));plaster=mat('plaster',(.48,.43,.35));slate=mat('roof',(.12,.15,.17));linen=mat('linen',(.80,.76,.65));cloths=[mat('quilt_'+str(i),cc) for i,cc in enumerate([(.49,.28,.30),(.25,.36,.42),(.49,.40,.24),(.29,.40,.34),(.38,.31,.42)])]
def beam(n,a,b,w=.07,m=None):
 o=box(n,(Vector(a)+Vector(b))/2,(w,w,(Vector(b)-Vector(a)).length),m or timber,.006);o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler();return o
def poly(n,v,co,m,thick=.08):
 me=bpy.data.meshes.new(n);me.from_pydata(v,[],[tuple(range(len(v)))]);me.update();ob=bpy.data.objects.new('AT29_'+n,me);co.objects.link(ob);me.materials.append(m)
 if thick:md=ob.modifiers.new('thickness','SOLIDIFY');md.thickness=thick
 return ob
def roof(n,x0,x1,y0,y1,z0,z1):return poly(n,[(x0,y0,z0),(x1,y0,z1),(x1,y1,z1),(x0,y1,z0)],roofco,slate)
# Expanded to west, maintaining original stair opening and floor level.
x0,x1,y0,y1=7.2,13.86,9.8,14.1;ridge=10.53
for n,xa,xb,ya,yb in [('main',x0,12.45,y0,y1),('east',13.55,x1,y0,y1),('foot',12.45,13.55,y0,10.0),('landing',12.45,13.55,12.05,y1)]:
 box('floor_'+n,((xa+xb)/2,(ya+yb)/2,2.82),(xb-xa,yb-ya,.16),wood,.001)
for i in range(28):
 x=7.25+i*.24
 for ya,yb in ([(9.82,14.08)] if x<12.45 or x>13.55 else [(12.06,14.08)]):box('floor_seam',(x,(ya+yb)/2,2.901),(.006,yb-ya,.002),timber,0)
box('west_wall',(7.15,11.95,3.725),(.10,4.4,1.65),plaster)
box('east_wall',(13.91,11.95,3.725),(.10,4.4,1.65),plaster)
box('south_wall',(ridge,9.75,3.725),(6.86,.10,1.65),plaster)
poly('south_gable',[(7.1,9.75,4.55),(13.96,9.75,4.55),(ridge,9.75,5.95)],c,plaster)
# North opening 3.6 m: 3 sliding panels stack at the right, leaving 2.4 m clear.
box('north_left',(7.75,14.15,3.975),(1.30,.10,2.15),plaster)
box('north_right',(12.98,14.15,3.975),(1.96,.10,2.15),plaster)
def rh(x):return 5.95-abs(x-ridge)*1.4/3.43
poly('north_left_top',[(7.1,14.15,5.05),(8.4,14.15,5.05),(8.4,14.15,rh(8.4)),(7.1,14.15,4.55)],c,plaster)
poly('north_right_top',[(12.0,14.15,5.05),(13.96,14.15,5.05),(13.96,14.15,4.55),(12.0,14.15,rh(12.0))],c,plaster)
poly('north_header',[(8.4,14.15,5.05),(12,14.15,5.05),(12,14.15,rh(12)),(ridge,14.15,5.95),(8.4,14.15,rh(8.4))],c,plaster)
for x in [8.38,12.02]:box('sliding_jamb',(x,14.12,3.99),(.075,.18,2.18),timber)
for z in [2.93,5.08]:box('sliding_header',(10.2,14.12,z),(3.74,.20,.07),timber)
control=bpy.data.objects.new('AT29_SlidingDoor_Control',None);c.objects.link(control);control['open']=1.0;control.id_properties_ui('open').update(min=0,max=1)
glass=bpy.data.materials.new('AT29_glass');glass.use_nodes=True;nt=glass.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');gs=nt.nodes.new('ShaderNodeBsdfGlass');gs.inputs['Color'].default_value=(.85,.95,1,1);gs.inputs['Roughness'].default_value=.06;gs.inputs['IOR'].default_value=1.45;nt.links.new(gs.outputs[0],out.inputs['Surface'])
for i in range(3):
 rt=bpy.data.objects.new('AT29_slider_'+str(i+1),None);c.objects.link(rt);rt.location=(9.0+1.2*i,14.07+i*.06,2.98)
 dr=rt.driver_add('location',0).driver;v=dr.variables.new();v.name='a';v.type='SINGLE_PROP';v.targets[0].id=control;v.targets[0].data_path='["open"]';dr.expression=str(9.0+1.2*i)+'+'+str(2.4-1.2*i)+'*a'
 for xx,zz,w,h in [(-.57,1,.045,2),(.57,1,.045,2),(0,.035,1.18,.07),(0,1.985,1.18,.06),(0,.65,1.18,.055)]:
  ob=box('slider_frame',(xx,0,zz),(w,.04,h),timber);ob.parent=rt
 ob=box('slider_glass',(0,0,1.03),(1.10,.008,1.89),glass,.001);ob.parent=rt
 ob=box('slider_pull',(-.49,-.043,.93),(.022,.022,.16),steel);ob.parent=rt
roof('roof_west',7.02,ridge,9.5,14.4,4.50,5.95);roof('roof_east',ridge,14.06,9.5,14.4,5.95,4.50)
for y in [10.0,11.95,13.90]:
 for a,b in [((7.21,y,4.53),(ridge,y,5.83)),((ridge,y,5.83),(13.85,y,4.53))]:beam('rafter',a,b,.11)
beam('ridge',(ridge,9.82,5.82),(ridge,14.08,5.82),.13)
# Opposite balcony, now north-facing.
box('balcony_deck',(10.20,14.94,2.81),(4.30,1.68,.18),wood)
for a,b in [((8.05,15.78,3.97),(12.35,15.78,3.97)),((8.05,14.1,3.97),(8.05,15.78,3.97)),((12.35,14.1,3.97),(12.35,15.78,3.97))]:beam('balcony_rail',a,b,.07)
for i in range(19):beam('balcony_front_post',(8.06+i*.238,15.78,2.93),(8.06+i*.238,15.78,3.95),.033)
for x in [8.06,12.34]:
 for j in range(7):beam('balcony_side_post',(x,14.16+j*.26,2.93),(x,14.16+j*.26,3.95),.033)
# Keep hatch guard and head landing free.
for x in [12.39,13.65]:
 beam('hatch_rail',(x,10.02,3.95),(x,12.04,3.95),.055)
 for y in [10.03,11.02,12.02]:beam('hatch_post',(x,y,2.90),(x,y,3.95),.055)
beam('hatch_end',(12.39,9.95,3.95),(13.65,9.95,3.95),.055)
# Five real-size bedding placeholders, heads toward moonlight.
for i in range(5):
 x=7.80+i*1.0
 ob=box('futon_'+str(i+1),(x,11.4,2.96),(.95,2.10,.12),linen,.045);move(ob,bedco)
 ob=box('quilt_'+str(i+1),(x,11.10,3.075),(.95,1.54,.16),cloths[i],.075);move(ob,bedco)
 ob=box('folded_quilt_lip',(x,11.83,3.16),(.94,.13,.10),linen,.035);move(ob,bedco)
 ob=box('pillow_'+str(i+1),(x,12.17,3.09),(.57,.33,.15),linen,.07);move(ob,bedco)
# Relocate stored belongings to foot-side wall, clear from sleeping layout.
for o in list(bpy.data.collections['33_ATTIC_Room_and_balcony_v28'].objects):
 if o.name.startswith(('AT28_old_stock','AT28_carton','AT28_keyboard_case','AT28_case_latch','AT28_case_handle')):
  dup=o.copy();dup.data=o.data.copy();c.objects.link(dup);dup.name=o.name.replace('AT28','AT29')
  if 'old_stock' in o.name or 'carton' in o.name:
   # Individual crate assemblies are relocated consistently by original cluster.
   if o.location.y>13:dup.location.y-=3.53
   elif o.location.y<11:dup.location.x-=1.3;dup.location.y= o.location.y- .50
   else:dup.location.x-=1.25;dup.location.y-=1.12
  else:dup.location.y=10.0;dup.location.x-=.7;dup.location.z+=.13
# Avoid any foot-side cargo poking into the bedding area: hide old irregular clusters,
# replacing with compact rows of trunks and boxes at y9.99.
for o in list(c.objects):
 if o.name.startswith(('AT29_old_stock','AT29_carton')):bpy.data.objects.remove(o,do_unlink=True)
for i,x in enumerate([7.63,8.30,9.04,9.78,10.56,11.34]):
 box('stored_trunk',(x,10.005,3.15),(.58,.34,.48),wood if i%2 else paper)
 for z in [2.97,3.33]:box('trunk_band',(x,10.181,z),(.58,.012,.035),timber)
 if i in [0,2,4]:box('stacked_carton',(x,10.005,3.58),(.49,.31,.35),paper)
# Rendering lights are independent of downstairs.
def light(n,p,t,power,col,size):
 da=bpy.data.lights.new(n,'AREA');ob=bpy.data.objects.new(n,da);nightco.objects.link(ob);ob.location=p;ob.rotation_euler=(Vector(t)-ob.location).to_track_quat('-Z','Y').to_euler();da.energy=power;da.color=col;da.size=size;return ob
light('AT29_moon_key',(8.9,17.5,6.4),(10.0,11.3,3),520,(.46,.64,1),1.0)
light('AT29_night_fill',(10.0,12.0,5.4),(10.0,11.5,3),85,(.45,.55,1),3)
light('AT29_warm_corner',(8.0,10.1,4.5),(9.6,11.1,3),25,(1,.62,.30),1)
moonmat=bpy.data.materials.new('AT29_moon_emission');moonmat.use_nodes=True;nn=moonmat.node_tree.nodes;pp=next(n for n in nn if n.type=='BSDF_PRINCIPLED');pp.inputs['Base Color'].default_value=(.8,.9,1,1);pp.inputs['Emission Color'].default_value=(.8,.9,1,1);pp.inputs['Emission Strength'].default_value=2
move(ball('moon',(9.0,30,6.2),(.64,.64,.64),moonmat),nightco)
def cam(n,p,t,lens=24,ortho=None):
 da=bpy.data.cameras.new(n);ob=bpy.data.objects.new(n,da);c.objects.link(ob);ob.location=p;ob.rotation_euler=(Vector(t)-ob.location).to_track_quat('-Z','Y').to_euler();da.lens=lens
 if ortho:da.type='ORTHO';da.ortho_scale=ortho
 return ob
ca=cam('Camera_AT29_sleepover',(7.55,10.25,4.43),(10.50,12.65,3.60),18)
cb=cam('Camera_AT29_from_stairs',(13.1,13.6,4.35),(9.45,12.0,3.6),19)
top=cam('Camera_AT29_plan',(10.5,12.7,13),(10.5,12.7,0),24,9.2)
s=bpy.context.scene;ff=s.frame_current;s.frame_set(ff+1);s.frame_set(ff);s.camera=ca;s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1400;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.use_freestyle=False
note='''屋根裏 v29：お泊り会向け。
約6.66×4.30m、床高2.90m。以前の部屋を西側へ広げ、収納階段の位置を維持。
布団95×210cmを5枚、間隔5cmで並列配置。枕側12.45～14.10mに約1.65mの通路。
ベランダはv28の反対側（北側・パン屋玄関と逆向き）、幅4.30m×奥行1.68m。
3枚引き戸は全幅3.6m、最大有効開口約2.4m。AT29_SlidingDoor_Controlのopen=0閉/1開。
38_ATTIC_Five_futons_toggle_v29を非表示にすると普段の屋根裏。37_ATTIC_Roof_toggle_v29は屋根。
39_ATTIC_Moonlight_toggle_v29に月と演出用照明。月は構図確認用の仮モデル。
荷物は足元側へ集約。布団横の階段穴は手すりで分け、枕側から回る。
人物を寝かせた芝居と衣服の広がりは未検証。布団5枚の実寸目安で床面を確認。
'''
open(os.path.join(O,'屋根裏_v29_変更点.txt'),'w',encoding='utf8').write(note);tx=bpy.data.texts.new('README_ATTIC_v29');tx.write(note)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(O,'月灯り_舞台設計_屋根裏_v29.blend'))
for camera,fn in [(ca,'屋根裏_月明かりと布団.png'),(cb,'屋根裏_階段側から.png')]:
 s.camera=camera;s.render.filepath=os.path.join(O,fn);bpy.ops.render.render(write_still=True)
roofco.hide_render=True;s.camera=top;s.render.filepath=os.path.join(O,'屋根裏_5人の配置.png');bpy.ops.render.render(write_still=True);roofco.hide_render=False
shutil.copy2('attic_v29.py',O)
print('DONE V29')
