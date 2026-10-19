import bpy,os,math
from mathutils import Vector
O=r'C:\Users\kaka\Desktop\e002素材\月灯り_屋根裏_v28'
c=bpy.data.collections['33_ATTIC_Room_and_balcony_v28'];m=bpy.data.materials['AT28_warm_plaster']
for ob in bpy.data.objects:
 if ob.name.startswith(('AT28_covered_spare_furniture','AT28_spare_furniture_leg')):ob.location.x+=.35;ob.location.y+=3.10
for o in list(bpy.data.objects):
 if o.name.startswith(('AT28_front_wall','AT28_south_gable','AT28_balcony_lintel')):bpy.data.objects.remove(o,do_unlink=True)
def poly(n,xzs):
 me=bpy.data.meshes.new(n);me.from_pydata([(x,9.75,z) for x,z in xzs],[],[tuple(range(len(xzs)))]);ob=bpy.data.objects.new(n,me);c.objects.link(ob);me.materials.append(m);md=ob.modifiers.new('wall thickness','SOLIDIFY');md.thickness=.10
def slope(x):return 5.78-abs(x-11.73)*1.24/2.23
poly('AT28_front_left',[(9.50,2.90),(10.22,2.90),(10.22,slope(10.22)),(9.50,4.54)])
poly('AT28_front_right',[(11.42,2.90),(13.96,2.90),(13.96,4.54),(11.73,5.78),(11.42,slope(11.42))])
poly('AT28_front_overdoor',[(10.22,4.86),(11.42,4.86),(11.42,slope(11.42)),(10.22,slope(10.22))])
for o in bpy.data.objects:
 if o.name.startswith('AT28_door_jamb'):o.location.z=3.90;o.dimensions.z=2.0
 if o.name.startswith('AT28_door_top'):o.location.z=4.89
 if o.name.startswith('AT28_door_frame'):o.location.z*=1.2;o.scale.z*=1.2
# Export attic plus its original folding staircase and record merge requirements.
tx=bpy.data.texts.get('README_ATTIC_v28');tx.write('\nベランダ開口高は約1.96m。階段stow=0/1の状態で固定床との位置を確認。収納状態では折畳階段が床穴上に残るため、開口周囲の手すりを維持。\n統合時はV22_STAIR_Upper_landingとUpper_grab_rail/Upper_grab_postを子孫含め非表示にする。\n')
s=bpy.context.scene;ctl=bpy.data.objects['V22_STAIR_Control'];f=s.frame_current
for v in [1.,0.]:
 ctl['stow']=v;ctl.update_tag();s.frame_set(f+1);s.frame_set(f);bpy.context.view_layer.update()
 print('stow',v,'hinge rotation',list(bpy.data.objects['V22_STAIR_Hatch_hinge'].rotation_euler))
s.camera=bpy.data.objects['Camera_AT28_from_stairs']
if hasattr(s,'eevee'):
 prop=s.eevee.bl_rna.properties.get('shadow_pool_size')
 if prop:
  vals=[it.identifier for it in prop.enum_items]
  nums=[v for v in vals if v.isdigit()]
  if nums:s.eevee.shadow_pool_size=max(nums,key=int)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(O,'月灯り_舞台設計_屋根裏_v28.blend'))
ids={bpy.data.collections[n] for n in ['33_ATTIC_Room_and_balcony_v28','34_ATTIC_Roof_toggle_v28','35_ATTIC_Surrounding_roof_v28','25_STAFF_Folding_stairs_v22']};ids.add(tx)
bpy.data.libraries.write(os.path.join(O,'屋根裏と階段差分_v28.blend'),ids,path_remap='ABSOLUTE',compress=True,fake_user=True)
for ca,fn in [('Camera_AT28_from_stairs','屋根裏_階段から.png'),('Camera_AT28_from_balcony','屋根裏_ベランダから.png')]:
 s.camera=bpy.data.objects[ca];s.render.filepath=os.path.join(O,fn);bpy.ops.render.render(write_still=True)
print('FINAL')
