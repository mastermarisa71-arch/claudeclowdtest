import bpy,math,os,shutil
from mathutils import Vector
O=r'C:\Users\kaka\Desktop\e002素材\月灯り_パン屋内装_v34';os.makedirs(O,exist_ok=True)
c=bpy.data.collections.new('46_BAKERY_Sales_floor_v34');bpy.context.scene.collection.children.link(c)
src=open('bakery_v26.py',encoding='utf8').read();exec(src[src.index('def link('):src.index('# North wall:')].replace('BK26_','BS34_'))
for o in bpy.data.objects:
 if o.name.startswith('BAKERY_') and 'Pendant' not in o.name:o.hide_render=True;o.hide_set(True)
blue=mat('bluegrey_paint',(.19,.27,.29));oak=mat('honey_oak',(.47,.29,.14));crust=mat('golden_crust',(.58,.27,.075));score=mat('bread_score',(.85,.61,.30));chalk=mat('chalk',(.86,.83,.69));board=mat('chalkboard',(.035,.075,.066));brass=mat('brass',(.48,.32,.12),.65)
def label(n,t,p,size=.07,rot=(math.pi/2,0,0),m=None):
 o=txt(n,t,p,size,rot)
 if m:o.data.materials.clear();o.data.materials.append(m)
 return o
def cabinet(n,x,y,w,d,h=.84):
 box(n+'_base',(x,y,h/2),(w,d,h),blue,.018);box(n+'_oak_top',(x,y,h+.025),(w+.045,d+.04,.05),oak,.018)
 count=max(1,round(w/.72))
 for i in range(count):
  xx=x-w/2+(i+.5)*w/count
  box(n+'_inset',(xx,y-d/2-.009,h*.49),(w/count-.10,.025,h-.17),blue,.008)
 return h+.05
def breadtray(n,x,y,z,kind=0,w=.55,d=.35):
 box(n+'_tray',(x,y,z+.012),(w,d,.024),oak,.008)
 for xx in [x-w/2,x+w/2]:box(n+'_rim',(xx,y,z+.04),(.018,d,.06),oak,.004)
 for yy in [y-d/2,y+d/2]:box(n+'_rim',(x,yy,z+.04),(w,.018,.06),oak,.004)
 for i in range(3):
  for j in range(2):
   xx=x+(i-1)*w*.27;yy=y+(j-.5)*d*.43
   if kind%3==0:
    ball(n+'_roll',(xx,yy,z+.078),(.068,.067,.055),crust)
    rod(n+'_cut',(xx-.034,yy,z+.126),(xx+.034,yy,z+.126),.004,score)
   elif kind%3==1:
    box(n+'_loaf',(xx,yy,z+.08),(.12,.11,.12),crust,.035)
    ball(n+'_loaf_crown',(xx,yy,z+.132),(.06,.055,.035),score)
   else:
    ball(n+'_oval',(xx,yy,z+.075),(.07,.051,.05),bread)
    for dx in [-.025,.025]:rod(n+'_slash',(xx+dx-.008,yy-.02,z+.118),(xx+dx+.008,yy+.02,z+.118),.004,score)
 box(n+'_pricecard',(x,y-d/2-.012,z+.075),(.18,.012,.10),paper,.002)
 label(n+'_price',['バターロール','食パン','くるみパン'][kind%3],(x,y-d/2-.021,z+.06),.023)
# One continuous service counter, with right end open to the kitchen route.
z=cabinet('service_counter',3.80,3.36,4.90,.62,.82)
box('register_base',(2.02,3.37,z+.065),(.40,.30,.13),dark)
box('register_display',(2.02,3.47,z+.25),(.33,.06,.23),dark)
box('cash_tray',(2.55,3.16,z+.022),(.24,.18,.025),brass)
label('pay_here','お会計',(2.59,3.04,1.04),.06)
# Bagging station and supplies on staff side, keeping the central counter clear.
for i in range(5):box('paper_bag',(4.90+i*.045,3.47,z+.16),(.036,.15,.30),paper,.003)
box('wrap_stack',(4.23,3.40,z+.025),(.40,.30,.045),paper,.004)
rod('twine_holder',(5.43,3.46,z+.02),(5.43,3.46,z+.15),.045,wood)
box('packed_order',(5.72,3.40,z+.095),(.38,.25,.18),paper,.005)
# Staff-side low work surface, 1.23 m clear behind main counter.
cabinet('back_workbench',3.58,5.12,6.30,.44,.76)
for x in [.47,2.02,3.57,5.12,6.68]:box('back_shelf_post',(x,5.13,1.45),(.045,.43,1.30),blue)
box('back_shelf_back',(3.58,5.33,1.44),(6.28,.035,1.28),blue)
for zz in [1.13,1.53,1.95]:box('back_shelf',(3.58,5.12,zz),(6.28,.45,.035),oak)
for i,x in enumerate([.83,1.52,2.37,3.06,3.90,4.59,5.43,6.12]):
 for j,zz in enumerate([1.15,1.55]):breadtray('back_bread',x,5.11,zz,(i+j)%3)
for i in range(7):
 x=.88+i*.75
 cyl('preserve_jar',(x,5.12,2.06),.055,.18,green);cyl('jar_lid',(x,5.12,2.16),.058,.025,brass)
# Left customer shelf: chest-height selections and cupboard storage below.
cabinet('left_low',.31,2.07,.46,2.30,.64)
for y in [.92,3.22]:box('left_post',(.31,y,1.12),(.43,.045,1.03),blue)
for zz in [.70,1.14]:box('left_shelf',(.31,2.07,zz),(.48,2.30,.03),oak)
for i,y in enumerate([1.25,1.94,2.63]):
 for zz in [.72,1.16]:breadtray('left_bread',.32,y,zz,i,.36,.56)
# Low island: generous entrance area and clear circulation on each side.
z=cabinet('island',4.55,1.55,1.45,.72,.76)
for i,x in enumerate([4.19,4.89]):breadtray('island_bread',x,1.55,z,i,.60,.50)
label('island_tag','焼きたて',(4.55,1.17,1.02),.065)
# Window displays leave the 3.4 m doorway and its outward swing clear.
for x in [1.22,7.17]:
 z=cabinet('window_display',x,.36,1.56,.48,.70)
 for i,dx in enumerate([-.40,.30]):breadtray('window_bread',x+dx,.36,z,i,.56,.35)
# Tray/tongs pickup to the right of entry, away from door swing and kitchen exit.
z=cabinet('tray_station',7.64,1.55,.66,.60,.78)
for i in range(8):box('customer_trays',(7.64,1.55,z+i*.018),(.49,.36,.016),oak,.008)
for i in range(3):
 x=7.48+i*.12;rod('tongs',(x,1.36,z+.18),(x+.025,1.67,z+.18),.008,steel);rod('tongs',(x+.055,1.36,z+.18),(x+.025,1.67,z+.18),.008,steel)
label('tray_sign','トレー・トング',(7.64,1.22,1.12),.055)
# Small wall menu above a clear working surface, not a new obstacle.
box('menu_frame',(7.18,5.36,1.71),(.70,.045,.81),oak)
box('menu_board',(7.18,5.328,1.71),(.61,.018,.72),board)
label('menu','本日のパン\n\nバターロール\nくるみパン\n食パン',(7.18,5.314,1.93),.062,m=chalk)
# Outdoor A-board on the fixed-glass side, outside both opening arcs.
for x in [.93,1.71]:
 rod('sign_front_leg',(x,-1.03,.02),(x,-.75,1.25),.028,oak)
 rod('sign_back_leg',(x,-.43,.02),(x,-.75,1.25),.028,oak)
box('outdoor_sign_frame',(1.32,-.90,.78),(.84,.065,.91),oak)
box('outdoor_sign_board',(1.32,-.939,.78),(.72,.018,.79),board)
label('outdoor_title','焼きたてパン',(1.32,-.953,1.04),.075,m=chalk)
label('outdoor_menu','本日のおすすめ\n\nバターロール\nくるみパン\n\n食パンあります',(1.32,-.953,.87),.052,m=chalk)
rod('sign_brace',(.95,-1.01,.36),(1.69,-1.01,.36),.015,brass)
# Warm shop wall plaque; placeholder name, not invented canon.
box('front_plaque',(7.25,-.22,2.55),(1.65,.09,.23),blue)
label('front_name','BAKERY',(7.25,-.272,2.48),.15,m=chalk)
# Flowers at window, jars and clock give the shop a cared-for daily life.
for x in [.75,7.73]:
 cyl('vase',(x,.36,.90),.075,.25,green)
 for i in range(5):
  a=i*math.tau/5;xx=x+.11*math.cos(a);yy=.36+.08*math.sin(a)
  rod('flower_stem',(x,.36,.98),(xx,yy,1.21),.004,green);ball('flower',(xx,yy,1.22),(.045,.04,.025),paper)
cl=cyl('wall_clock',(3.55,5.37,2.28),.18,.035,oak);cl.rotation_euler.x=math.pi/2
cl=cyl('clock_face',(3.55,5.345,2.28),.157,.012,paper);cl.rotation_euler.x=math.pi/2
rod('clock_hand',(3.55,5.332,2.28),(3.55,5.332,2.39),.006,dark);rod('clock_hand',(3.55,5.331,2.28),(3.63,5.331,2.25),.007,dark)
# Cameras and daylight only for the bakery.
def camera(n,p,t,lens=25,ortho=None):
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);c.objects.link(o);o.location=p;o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens
 if ortho:d.type='ORTHO';d.ortho_scale=ortho
 return o
eye=camera('Camera_BS34_entrance',(4.32,.15,1.62),(3.95,4.0,1.05),21)
top=camera('Camera_BS34_plan',(4.2,2.3,15),(4.2,2.3,0),ortho=10.4)
ext=camera('Camera_BS34_exterior',(10,-9,3.5),(4.0,1.5,1.15),31)
for n,p,energy,size in [('daylight',(4.2,1.9,2.6),500,5),('counter',(3.6,4.0,2.55),180,3)]:
 d=bpy.data.lights.new('BS34_'+n,'AREA');o=bpy.data.objects.new('BS34_'+n,d);c.objects.link(o);o.location=p;d.energy=energy;d.shape='DISK';d.size=size;d.color=(1,.88,.71)
s=bpy.context.scene;s.camera=eye;s.render.resolution_x=1500;s.render.resolution_y=1000;s.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(O,'月灯り_舞台設計_パン屋_v34.blend'))
s.render.filepath=os.path.join(O,'パン屋_入口から.png');bpy.ops.render.render(write_still=True)
s.camera=ext;s.render.filepath=os.path.join(O,'パン屋_外の看板.png');bpy.ops.render.render(write_still=True)
# Hide upper storey only for plan inspection; do not save this display state.
for col in bpy.data.collections:
 if 'ATTIC' in col.name:col.hide_render=True
s.camera=top;s.render.filepath=os.path.join(O,'パン屋_俯瞰.png');bpy.ops.render.render(write_still=True)
open(os.path.join(O,'パン屋_v34_設計メモ.txt'),'w',encoding='utf8').write('売場 v34\nカウンター幅4.90m、天板高さ0.87m。背後作業通路1.23m。\n右端6.25mから厨房側8.4mまで2.15mの接続帯（既存ドアの開閉範囲を含む）。\n低い陳列島と会計前の間1.14m。入口の中央3.4mを維持。\n会計、中央の受渡し、右の袋詰めを連続配置。奥の作業天板は0.81m。\n背の高い棚は店員用の陳列・保管。145cmのおばあの日常作業は低い天板で行う想定。\n外看板は固定ガラス側に置き、開き戸の可動範囲を避けた。看板の商品名は仮。\n寸法はモデル上の計画値。人物を用いた動作・複数人のすれ違いは未検証。\n旧売場オブジェクトは非表示で保存。屋根裏v33、厨房v27などを引き継ぎ。')
shutil.copy2(__file__,O)
print('DONE SHOP34')
