#!/usr/bin/env python
# coding: utf-8
import bpy
import bmesh
from mathutils import Vector
import sys
import glob, os
current_dir = os.getcwd().replace(os.sep,'/')
sys.path.append(current_dir)
from collections import defaultdict
from math import isclose, radians
# from mathutils.bvhtree import BVHTree
from collections import deque
from json_operater import load_json_data, update_json_data
from cloth_util import *
from detecting_util import *
from cloth_param import *

json_path = "./parameter.json"
if __name__ == '__main__':
#target_obj = "Donattu"
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 1.5

    data = load_json_data(json_path)
    delete_all()
    cloth_path = data["cloth_path"]
    cloth_name = os.path.basename(cloth_path).replace('.obj', '')
    print(f"target_obj: {cloth_name}")
    bpy.ops.import_scene.obj(filepath = cloth_path)
    donattu_obj = bpy.data.objects[cloth_name]
    donattu_obj.rotation_euler[0] = 0
    donattu_mesh = None
    donattu_mesh = get_mesh_by_name(cloth_name)
    bpy.context.scene.render.resolution_x = ConstParam.render_resolution.value
    bpy.context.scene.render.resolution_y = ConstParam.render_resolution.value
    bpy.context.view_layer.objects.active = donattu_obj
    output_path = os.getcwd() + "/init.mp4"
    obj_rendering(donattu_obj, output_path)