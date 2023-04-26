#!/usr/bin/env python
# coding: utf-8
import time
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
    argv = sys.argv
    argv = argv[argv.index("--") + 1:]
    if len(argv) != 1:
        exit(1)
    cloth_name = argv[0]
    current_dir = os.getcwd()
    output_dir = current_dir +  "./../output/" + cloth_name + "/data/"
    bpy.context.scene.render.resolution_x = ConstParam.render_resolution.value
    bpy.context.scene.render.resolution_y = ConstParam.render_resolution.value
    data = load_json_data(json_path)
    delete_all()
    cloth_path = data["cloth_path"] + "/" + cloth_name + ".obj"
    # cloth_path = "testCloth/MJA00002543.obj"
    cloth_name = os.path.basename(cloth_path).replace('.obj', '')
    print(f"target_obj: {cloth_name}")
    bpy.ops.import_scene.obj(filepath = cloth_path)
    donattu_obj = bpy.data.objects[cloth_name]
    donattu_obj.rotation_euler[0] = 0
    donattu_mesh = None
    donattu_mesh = get_mesh_by_name(cloth_name)
    bpy.context.view_layer.objects.active = donattu_obj
    camera_obj = make_camera("Camera", [0.0, -3.0, 1.0], [90.0, 0.0, 90.0])
    
    bpy.context.scene.camera = camera_obj
    bpy.ops.object.mode_set(mode='EDIT')
    # linked_faces_list = get_linked_faces(donattu_obj)
    # max_len = max(len(faces) for faces in linked_faces_list)
    linked_face_path = os.path.join(output_dir, "linked_faces")
    os.makedirs(linked_face_path, exist_ok= True)
    linked_faces_list=render_and_save_elements(donattu_obj, linked_face_path, camera_obj)
    csv_face_path = output_dir + "face.csv"
    save_to_csv(linked_faces_list, csv_face_path)
    # progress_data = {"progress": progress}
    # update_json_data(json_path, progress_data)

    # print(linked_faces_list)
    # donattu_mesh = get_mesh_by_name(cloth_name)

    #meshの取得
    if donattu_mesh == None:
        exit()
        
    # BMeshオブジェクトを作成
    bm = bmesh.new()
    bm.from_mesh(donattu_mesh)
    bm.transform(donattu_obj.matrix_world)

    #複数カメラ視点からの穴を格納するリスト
    hole_edges_from_cameras = []

    vetors = []
    n = 10
    for i in range(n):
        vetors.append(Vector((math.sin(3.1415/n*i),math.cos(3.1415/n*i),0.1)))
    for i in range(n):
        vetors.append(Vector((math.sin(3.1415/n*i),math.cos(3.1415/n*i),-0.1)))
    start_time = time.time()
    for view_vector in vetors:
        # オブジェクトを取得
        donattu_obj = bpy.data.objects[cloth_name]
        print(f"view_vector: {view_vector}")
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
                if dot1 * dot2 < 0:
                    shared_edges.append(edge)
        # 共有エッジを使って、ループを見つける
        loops = find_loops(shared_edges)
        print("len loops: ", len(loops))


        hole_edges = []
        valid_loops = []
        edge_groups = []
        loop_edge_index =[]
        progress = 30
        # progress_data = {"progress": progress}
        # update_json_data(json_path, progress_data)
        loop_size = len(loops)
        old_progress = progress
        for i, (loop, loop_edges, loop_length) in enumerate(loops):
            progress = int(((i+1)/loop_size)*100)*(100-old_progress)+old_progress
            # progress_data = {"progress": progress}
            # update_json_data(json_path, progress_data)
            if not is_valid_loop(loop_edges) or loop_edges == None:
                continue

            # loop_edges = find_largest_loop(donattu_obj,loop_edges)
            if len(loop_edges) > 4 and len(loop_edges) < 100:
                result      = can_split_object2(loop_edges, bm, True)
                
                # for e in loop_edges:
                #     hole_edges.append(e)
                if not result:
                    valid_loops.append((loop, loop_edges, loop_length))
                    for e in loop_edges:
                        hole_edges.append(e)
                        loop_edge_index.append(e.index)
                    edge_groups.append(loop_edge_index)
                    # loop_edges_indices = [edge.index for edge in loop_edges]
                    # highlight_edges(donattu_obj, loop_edges_indices)
                    # camera = create_camera_auto(donattu_mesh, loop_edges_indices)
                    # output_filepath = "image.png"
                    # render_image(output_filepath)
        print("edge_groups: ", edge_groups)
        result = merge_overlapping_groups(edge_groups)
        print("result: ", result)
        csv_edge_path = output_dir + "edge.csv"
        save_to_csv(result, csv_edge_path)
        print("find hole end")
        # success_data = {"success": True}
        # update_json_data(json_path, success_data)
        hole_edges_from_cameras = hole_edges_from_cameras + hole_edges

    # 最終的に穴と認識されたエッジを選択
    if len(hole_edges_from_cameras) > 0 :
        # print(hole_edges_from_cameras)
        print("hole_detect")
        select_edges(donattu_obj, hole_edges_from_cameras)
    else:
        print("no hole")

    bm.free()
    end_time = time.time()

    print(f"elapsed_time: {end_time - start_time}")
