import bpy,os,shutil
O=r'C:\Users\kaka\Desktop\e002素材\月灯り_屋根裏_v30'
for ob in bpy.data.objects:
 if ob.name.startswith('AT30_south_wainscot'):ob.location.y=9.275
s=bpy.context.scene;s.camera=bpy.data.objects['Camera_AT30_storage']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(O,'月灯り_舞台設計_屋根裏_v30.blend'))
for ca,fn in [('Camera_AT30_storage','屋根裏_雑多な収納.png'),('Camera_AT30_moon','屋根裏_布団と月明かり.png')]:
 s.camera=bpy.data.objects[ca];s.render.filepath=os.path.join(O,fn);bpy.ops.render.render(write_still=True)
shutil.copy2('attic_v30_finish.py',O)
