import bpy,os,shutil
from mathutils import Vector
O=r'C:\Users\kaka\Desktop\e002素材\月灯り_屋根裏_v31';s=bpy.context.scene;c=bpy.data.collections['42_ATTIC_Expanded_store_v31']
me=bpy.data.meshes.new('gable_transition');me.from_pydata([(7.1,14.15,4.55),(10.53,14.15,5.95),(7.1,14.15,5.25)],[],[(0,1,2)]);ob=bpy.data.objects.new('AT31_north_gable_transition',me);c.objects.link(ob);me.materials.append(bpy.data.materials['AT29_plaster']);md=ob.modifiers.new('thickness','SOLIDIFY');md.thickness=.08
s.camera=bpy.data.objects['Camera_AT31_storage'];bpy.ops.wm.save_as_mainfile(filepath=os.path.join(O,'月灯り_舞台設計_屋根裏_v31.blend'))
# Whole-building and ground floor cutaways are inspection renders, not saved visibility changes.
names=['43_ATTIC_Roof_toggle_v31','18_BAR_Ceiling_toggle','26_STAFF_Ceiling_toggle_v22']
states={n:bpy.data.collections[n].hide_render for n in names}
for n in names:bpy.data.collections[n].hide_render=True
beams=[o for o in c.objects if o.name.startswith(('AT31_rafter','AT31_ridge'))]
for o in beams:o.hide_render=True
ld=bpy.data.lights.new('inspection','AREA');lo=bpy.data.objects.new('inspection',ld);s.collection.objects.link(lo);lo.location=(7,7,18);ld.energy=3500;ld.size=12
s.camera=bpy.data.objects['Camera_AT31_building'];s.render.filepath=os.path.join(O,'建物全体_屋根裏の位置.png');bpy.ops.render.render(write_still=True)
up=['36_ATTIC_Wide_room_v29','38_ATTIC_Five_futons_toggle_v29','39_ATTIC_Moonlight_toggle_v29','41_ATTIC_American_storage_v30','42_ATTIC_Expanded_store_v31']
upstate={n:bpy.data.collections[n].hide_render for n in up}
for n in up:bpy.data.collections[n].hide_render=True
da=bpy.data.cameras.new('inspection_ground');ca=bpy.data.objects.new('inspection_ground',da);s.collection.objects.link(ca);ca.location=(7,7.2,22);ca.rotation_euler=(Vector((7,7.2,0))-ca.location).to_track_quat('-Z','Y').to_euler();da.type='ORTHO';da.ortho_scale=22
s.camera=ca;s.render.filepath=os.path.join(O,'1階_俯瞰.png');bpy.ops.render.render(write_still=True)
for n,v in states.items():bpy.data.collections[n].hide_render=v
for n,v in upstate.items():bpy.data.collections[n].hide_render=v
for o in beams:o.hide_render=False
shutil.copy2('attic_v31_finish.py',O)
