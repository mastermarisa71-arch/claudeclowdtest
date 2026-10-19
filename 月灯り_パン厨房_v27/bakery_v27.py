import bpy, math, os, shutil
from mathutils import Vector
O=r'C:\Users\kaka\Desktop\e002素材\月灯り_パン厨房_v27'
os.makedirs(O,exist_ok=True)
c=bpy.data.collections.new('32_BAKERY_Lived_in_shelves_v27');bpy.context.scene.collection.children.link(c)
src=open('bakery_v26.py',encoding='utf8').read()
exec(src[src.index('def link('):src.index('# North wall:')].replace('BK26_','BK27_'))
def loop(n,p,r,m,axis='Z'):
 bpy.ops.mesh.primitive_torus_add(major_segments=28,minor_segments=8,location=p,major_radius=r,minor_radius=.006)
 o=link(bpy.context.object,n,m)
 if axis=='Y':o.rotation_euler.x=math.pi/2
 if axis=='X':o.rotation_euler.y=math.pi/2
 return o
def tin(n,x,y,z,w=.22,d=.13,h=.09):
 box(n+'_bottom',(x,y,z+.006),(w,d,.012),steel,.003)
 for dx in [-w/2,w/2]:box(n+'_side',(x+dx,y,z+h/2),(.009,d,h),steel,.003)
 for dy in [-d/2,d/2]:box(n+'_side',(x,y+dy,z+h/2),(w,.009,h),steel,.003)
# South: existing flour bins remain accessible underneath a shallow wooden hutch.
for x in [8.83,10.83]:box('hutch_post',(x,.23,.97),(.045,.38,1.94),wood)
for z in [.86,1.26,1.74]:box('hutch_shelf',(9.83,.24,z),(2.05,.40,.035),wood)
box('hutch_back_rail',(9.83,.045,1.88),(2.04,.035,.13),wood)
for x in [9.40,10.15]:box('hutch_divider',(x,.23,1.505),(.025,.37,.455),wood)
# Reachable jars: restrained labels, unequal sizes and spacing.
for i,(x,r,h,label) in enumerate([(9.04,.09,.22,'レーズン'),(9.30,.075,.18,'くるみ'),(9.59,.09,.24,'砂糖'),(9.87,.075,.19,'塩')]):
 cyl('ingredient_canister',(x,.24,1.278+h/2),r,h,cream);cyl('canister_lid',(x,.24,1.282+h),r+.006,.018,green)
 box('canister_label',(x,.24+r+.004,1.278+h*.55),(.12,.006,.065),paper,.002)
 txt('jar_text',label,(x,.24+r+.009,1.278+h*.48),.025,(math.pi/2,0,math.pi))
for j in range(3):tin('stacked_loaf_tin',10.43,.24,1.279+j*.025,.31,.20,.10)
# Lower shelf: measuring jug, wrapped ingredients and old notebooks.
for x in [9.0,9.3]:
 cyl('measuring_jug',(x,.24,1.0),.085,.245,cream);loop('jug_handle',(x+.10,.24,1.0),.053,steel,'Y')
for i in range(3):box('ingredient_packet',(9.65+i*.18,.24,.985),(.14,.19,.215),paper)
for i in range(4):box('recipe_spine',(10.36+i*.045,.23,.995),(.036,.22,.235),green if i%2 else wood)
# Upper shelf is light bakeware, rather than heavy food stocks.
for x in [9.0,9.27,9.56]:
 for j in range(2):tin('spare_mould',x,.24,1.759+j*.022,.21,.19,.095)
for x in [10.0,10.40]:
 box('paper_bag_bundle',(x,.22,1.865),(.25,.19,.20),paper)
 rod('bundle_string',(x-.13,.22,1.968),(x+.13,.22,1.968),.004,wood)
# Upright tray slot beside cold counter, above floor storage only.
for i in range(4):
 ob=box('stored_baking_sheet',(11.22+i*.075,.095,1.26),(.055,.035,.50),steel,.003)
 # broad vertical sheet, leaning on the south wall
 ob.dimensions=(.055,.38,.50);ob.rotation_euler.x=math.radians(-8)
box('tray_slot_shelf',(11.34,.24,.995),(.50,.46,.035),wood)
for x in [11.10,11.58]:box('tray_slot_end',(x,.24,1.20),(.02,.40,.40),wood)
# East wall: utensils silhouette against wall at conversational framing height.
rod('utensil_rail',(13.73,1.87,1.48),(13.73,2.82,1.48),.014,steel)
for i,y in enumerate([1.98,2.24,2.52,2.73]):
 loop('tool_hook',(13.70,y,1.47),.025,steel,'Y')
 rod('tool_handle',(13.70,y,1.42),(13.70,y,1.23),.014,wood)
 if i==0:box('spatula',(13.70,y,1.15),(.025,.09,.15),wood)
 elif i==1:
  for a in range(4):
   ang=a*math.pi/4
   rod('whisk_wire',(13.70,y,1.24),(13.70+.045*math.cos(ang),y+.045*math.sin(ang),1.10),.003,steel)
   rod('whisk_wire',(13.70+.045*math.cos(ang),y+.045*math.sin(ang),1.10),(13.70,y,1.05),.003,steel)
 elif i==2:ball('ladle',(13.68,y,1.15),(.035,.065,.065),steel)
 else:box('pastry_brush',(13.70,y,1.15),(.027,.065,.10),paper)
# Above mixer: bowls and dough tubs, shelf kept shallow and clear of machine head.
box('mixer_wall_shelf',(13.69,3.69,1.62),(.27,1.05,.035),wood)
for y in [3.38,3.75]:
 for j in range(3):
  cyl('nested_bowl',(13.67,y,1.66+j*.025),.12,.042,steel)
  loop('bowl_lip',(13.67,y,1.68+j*.025),.12,steel)
box('tub_above_mixer',(13.67,4.02,1.73),(.21,.21,.18),cream)
# West: bakery packaging / small order slips, clear of doorway at y3..3.9.
box('packing_wall_shelf',(8.73,1.86,1.34),(.28,1.45,.035),wood)
for y in [1.40,1.69]:box('paper_bags',(8.73,y,1.475),(.18,.20,.235),paper)
for j in range(5):box('bag_stack',(8.73,2.15,1.36+j*.009),(.20,.34,.008),paper,.001)
rod('order_clip_rail',(8.62,1.37,1.86),(8.62,2.34,1.86),.01,steel)
for y in [1.50,1.85,2.18]:
 box('order_slip',(8.63,y,1.72),(.008,.22,.24),paper,.002)
 box('order_clip',(8.65,y,1.845),(.02,.035,.04),dark,.002)
# towel at packing bench; short shelf brackets make fittings legible.
rod('towel_bar',(9.26,1.61,.65),(9.26,1.96,.65),.012,steel)
box('used_towel',(9.275,1.8,.51),(.02,.22,.29),cream)
for y in [1.25,2.45]:rod('packing_bracket',(8.60,y,1.12),(8.86,y,1.32),.011,steel)
for y in [3.3,4.08]:rod('mixer_bracket',(13.82,y,1.39),(13.57,y,1.60),.012,steel)
# eye-level review cameras
def cam(n,p,t,lens):
 da=bpy.data.cameras.new(n);ob=bpy.data.objects.new(n,da);c.objects.link(ob);ob.location=p;ob.rotation_euler=(Vector(t)-ob.location).to_track_quat('-Z','Y').to_euler();da.lens=lens;return ob
eye=cam('Camera_BK27_eye145',(11.75,3.40,1.34),(9.94,.30,1.20),25)
reverse=cam('Camera_BK27_eye_east',(10.00,2.80,1.45),(13.40,2.40,1.20),26)
s=bpy.context.scene;s.camera=eye;s.render.resolution_x=1400;s.render.resolution_y=1000
note='''パン厨房 v27：目線の高さに仕事道具を追加。
南の原料ボックス上に浅い木棚。日用品は86cm・126cmの棚、上段174cmには軽い予備の型や紙袋。
東に泡立て器・へら・レードル・刷毛の吊りレール、ミキサー上の小棚。
西の袋詰め台に紙袋、注文票、布巾。中央の成形台と通路を維持。
145cmの人物を想定したカメラ高134cmでも、保存瓶・型・道具が背景に入るように確認。
上段は日々の出し入れを想定しない。棚高は仮で、人物モデルによるリーチ確認は未実施。
元のv26を保持。32_BAKERY_Lived_in_shelves_v27が今回追加分。
'''
open(os.path.join(O,'厨房_v27_変更点.txt'),'w',encoding='utf8').write(note)
tx=bpy.data.texts.new('README_BK27');tx.write(note)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(O,'月灯り_舞台設計_パン厨房_v27.blend'))
for ca,fn in [(eye,'厨房_おばあの目線.png'),(reverse,'厨房_道具のある壁.png'),(bpy.data.objects['Camera_BK26_inside'],'厨房_全景.png')]:
 s.camera=ca;s.render.filepath=os.path.join(O,fn);bpy.ops.render.render(write_still=True)
shutil.copy2('bakery_v27.py',O)
print('DONE v27')
