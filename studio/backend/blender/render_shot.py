"""Blender の中で動かす背景レンダー。CLI から次の形で呼ばれる：

  blender -b <舞台.blend> --python studio/backend/blender/render_shot.py -- \
      --camera CAM_A --out <出力.png> [--lens 35] [--res 1920x1080] [--samples 32] [--hide 人物仮置き]

出力：背景 PNG と、同じ名前の .json（カメラ名・位置・向き・焦点距離・見えているオブジェクト）。
JSON はプロンプトに「どこから何を撮っているか」を書くための手がかりとして、テイクの params に入る。
"""
import json
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
opt = {argv[i].lstrip("-"): argv[i + 1] for i in range(0, len(argv) - 1, 2)}

scene = bpy.context.scene
cam = bpy.data.objects[opt["camera"]]
scene.camera = cam
if "lens" in opt:
    cam.data.lens = float(opt["lens"])
w, h = (int(x) for x in opt.get("res", "1920x1080").split("x"))
scene.render.resolution_x, scene.render.resolution_y = w, h
if scene.render.engine == "CYCLES" and "samples" in opt:
    scene.cycles.samples = int(opt["samples"])
for name in filter(None, opt.get("hide", "").split(",")):
    for o in bpy.data.objects:
        if o.name.startswith(name):
            o.hide_render = True

visible = []
for o in scene.objects:
    if o.type != "MESH" or o.hide_render:
        continue
    p = world_to_camera_view(scene, cam, o.matrix_world.translation)
    if 0 <= p.x <= 1 and 0 <= p.y <= 1 and p.z > 0:
        visible.append({"name": o.name, "screen_x": round(p.x, 3), "screen_y": round(1 - p.y, 3),
                        "distance": round(p.z, 2)})
visible.sort(key=lambda v: v["distance"])

scene.render.filepath = opt["out"]
bpy.ops.render.render(write_still=True)

meta = {"blend": bpy.data.filepath, "camera": cam.name, "lens_mm": cam.data.lens,
        "location": [round(v, 3) for v in cam.matrix_world.translation],
        "rotation_deg": [round(v * 57.2958, 1) for v in cam.matrix_world.to_euler()],
        "resolution": [w, h], "visible_objects": visible[:40]}
with open(opt["out"].rsplit(".", 1)[0] + ".json", "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=1)
print("RENDERED", opt["out"])
