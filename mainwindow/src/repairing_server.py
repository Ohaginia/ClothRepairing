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
    bpy.context.scene.render.resolution_x = ConstParam.render_resolution.value
    bpy.context.scene.render.resolution_y = ConstParam.render_resolution.value
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
    bpy.context.view_layer.objects.active = donattu_obj
    camera_obj = make_camera("Camera", [-0.354822, -1.21612 ,0.330571], [90.0, 0.0, 0.0])
    bpy.context.scene.camera = camera_obj
    bpy.ops.object.mode_set(mode='EDIT')
    # linked_faces_list = get_linked_faces(donattu_obj)
    # max_len = max(len(faces) for faces in linked_faces_list)
    linked_face_path=os.getcwd()+ "/tmp/"
    linked_face_path_data = {"linked_face_path": linked_face_path}
    update_json_data(json_path, linked_face_path_data)
    render_and_save_elements(donattu_obj, linked_face_path, camera_obj)
    progress_data = {"progress": 10}
    update_json_data(json_path, progress_data)

    # print(linked_faces_list)
    # donattu_mesh = get_mesh_by_name(cloth_name)
    if donattu_mesh != None:
        print(f"メッシュ名: {donattu_mesh.name}")
    else:
        print("Donattuという名前のメッシュが見つかりませんでした")
        
    if donattu_mesh:
        # オブジェクトを取得
        donattu_obj = bpy.data.objects[cloth_name]

        # カメラオブジェクトを取得
        camera = bpy.data.objects["Camera"]
        # 視線ベクトルを取得
        view_vector = get_view_vector(camera)
        print(f"view_vector: {view_vector}")

        # BMeshオブジェクトを作成
        bm = bmesh.new()
        bm.from_mesh(donattu_mesh)
        bm.transform(donattu_obj.matrix_world)

        print("dot calc")
        # 法線ベクトルと内積のリストを作成
        face_normal_dot_products = {}

        for face in bm.faces:
            face_normal = face.normal
            dot = dot_product(face_normal, view_vector)
            face_normal_dot_products[face.index] = dot
            # print(f"face index: {face.index}, dot: {dot}")

        # 内積の符号が異なる隣接面を見つけ、共有エッジを出力する
        shared_edges = []
        for edge in bm.edges:
            faces = edge.link_faces
            if len(faces) == 2:
                face1, face2 = faces
                dot1 = face_normal_dot_products[face1.index]
                dot2 = face_normal_dot_products[face2.index]
                if (dot1 < 0 and dot2 > 0) or (dot1 > 0 and dot2 < 0):
                    shared_edges.append(edge)
        print("len shared_edges: ", len(shared_edges))
        loops = find_loops(shared_edges)
        print("len loops: ", len(loops))
        hole_edges = []
        valid_loops = []
        for i, (loop, loop_edges, loop_length) in enumerate(loops):
            if not is_valid_loop(loop_edges):
                continue
            if len(loop_edges) > 4 or len(loop_edges) > 50:
                result = can_split_object(loop_edges, donattu_obj, bm)
                if result:
                    valid_loops.append((loop, loop_edges, loop_length))
                    for e in loop_edges:
                        hole_edges.append(e)
        #         print(f"環 {i}:")
        #         print(f"  長さ:  {len(loop_edges)} ")
        #             print("オブジェクトは2つの面に分割できません")
        #             for e in loop_edges:
        #                 hole_edges.append(e)
        if len(hole_edges) > 0 :
            print("hole_detect")
            select_edges(donattu_obj, hole_edges)
            # delete_selected_edges(donattu_obj)
        else:
            print("no hole")
    #        print(f"  エッジリスト: {', '.join(str(edge.index) for edge in loop_edges)}")
        # BMeshオブジェクトを破棄
        bm.free()
        # bpy.ops.object.mode_set(mode='EDIT')

    #    print(edges)
        print("find hole end")
        success_data = {"success": True}
        update_json_data(json_path, success_data)
    else:
        print("{target_obj}という名前のメッシュが見つかりませんでした")
        success_data = {"success": False}
        update_json_data(json_path, success_data)