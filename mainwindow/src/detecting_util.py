import bpy
import bmesh
from mathutils import Vector
import mathutils
import shutil
import os
from collections import defaultdict
from math import isclose, radians, tan
from mathutils.bvhtree import BVHTree
from cloth_util import make_camera
from collections import deque
from subprocess import Popen
import subprocess
import numpy as np
import csv

def save_to_csv(data, filename):
    with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',')
        for row in data:
            csv_writer.writerow(row)

def merge_overlapping_groups(edge_group):
    merged_groups = []
    for group in edge_group:
        found_overlap = False
        for merged_group in merged_groups:
            if set(group) & set(merged_group):
                merged_group.extend(x for x in group if x not in merged_group)
                found_overlap = True
                break
        if not found_overlap:
            merged_groups.append(group)
    return merged_groups

def set_camera_position_and_direction(camera, obj):
    bbox = obj.bound_box
    bbox_center = obj.matrix_world @ sum((Vector(v) for v in bbox), Vector()) / 8
    max_dim = max([Vector(p).length for p in bbox])
    
    distance = max_dim / (2 * tan(camera.data.angle_y * 0.5)) - 1.5
    print("distance: ", distance)
    camera.location = bbox_center + Vector((0, -distance, 0))
    camera.rotation_euler = (radians(90), 0, 0)

def render_and_save_elements(obj, output_path, camera):
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 1.5

    if obj.type != 'MESH':
        print("Error: Object must be of type 'MESH'")
        return

    linked_faces_list = get_linked_faces(obj)
    bpy.context.scene.render.film_transparent = True
    for i, face_indices in enumerate(linked_faces_list):
        print("len(face_indices): ", len(face_indices))
        if(len(face_indices) < 50):
            continue
        # オブジェクトのコピーを作成
        obj_copy = obj.copy()
        obj_copy.data = obj.data.copy()
        bpy.context.collection.objects.link(obj_copy)

        # カメラの位置と向きを設定
        set_camera_position_and_direction(camera, obj_copy)

        # その要素以外のすべての面を削除
        bpy.context.view_layer.objects.active = obj_copy
        bpy.ops.object.mode_set(mode='EDIT')
        mesh = obj_copy.data
        bm = bmesh.from_edit_mesh(mesh)

        faces_to_remove = [face for face in bm.faces if face.index not in face_indices]
        bmesh.ops.delete(bm, geom=faces_to_remove, context='FACES')

        bmesh.update_edit_mesh(mesh)
        bpy.ops.object.mode_set(mode='OBJECT')
        # レンダリングして保存
        obj.hide_render = True
        bpy.context.scene.render.filepath = os.path.join(output_path, f'element_{i:03d}.png')
        bpy.ops.render.render(write_still=True)
        obj.hide_render = False
        # コピーを削除
        bpy.data.objects.remove(obj_copy)

def merge_overlapping_groups(edge_group):
    merged_groups = []
    for group in edge_group:
        found_overlap = False
        for merged_group in merged_groups:
            if set(group) & set(merged_group):
                merged_group.extend(x for x in group if x not in merged_group)
                found_overlap = True
                break
        if not found_overlap:
            merged_groups.append(group)
    return merged_groups

def delete_except_largest_linked_face(obj):
    if obj.type != 'MESH':
        print("Error: Object must be of type 'MESH'")
        return

    bpy.ops.object.mode_set(mode='EDIT')
    
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    
    linked_faces_list = get_linked_faces(obj)
    
    # 最大のリンクされた面を見つける
    largest_face = None
    largest_area = 0
    for faces in linked_faces_list:
        for face in faces:
            if face.calc_area() > largest_area:
                largest_area = face.calc_area()
                largest_face = face
    
    # 最大の面以外を削除する
    faces_to_remove = [face for face in bm.faces if face != largest_face]
    bmesh.ops.delete(bm, geom=faces_to_remove, context='FACES')

    bmesh.update_edit_mesh(mesh)
    bpy.ops.object.mode_set(mode='OBJECT')


def get_linked_faces(obj):
    if obj.type != 'MESH':
        print("Error: Object must be of type 'MESH'")
        return

    bpy.ops.object.mode_set(mode='EDIT')
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)

    def find_linked_faces(face, visited_faces):
        linked_faces = []
        face_queue = deque([face])

        while face_queue:
            current_face = face_queue.popleft()
            if current_face not in visited_faces:
                linked_faces.append(current_face)
                visited_faces.add(current_face)

                for edge in current_face.edges:
                    for linked_face in edge.link_faces:
                        if linked_face not in visited_faces:
                            face_queue.append(linked_face)

        return linked_faces

    linked_faces_list = []
    visited_faces = set()
    for face in bm.faces:
        if face not in visited_faces:
            linked_faces = find_linked_faces(face, visited_faces)
            linked_faces_list.append([f.index for f in linked_faces])

    bpy.ops.object.mode_set(mode='OBJECT')
    print(len(linked_faces_list))
    print(len(linked_faces_list[0]))

    return linked_faces_list

def get_object_centroid(obj):
    if obj.type != 'MESH':
        print("Error: Object must be of type 'MESH'")
        return None
    # Calculate the bounding box center
    bounding_box_center = sum((obj.matrix_world @ Vector(corner) for corner in obj.bound_box), Vector()) / 8
    return bounding_box_center

def obj_rendering(obj, output_path):
    if obj.type != 'MESH':
        print("Error: Object must be of type 'MESH'")
        return

    # 1. Color management settings
    scene = bpy.context.scene
    # scene.view_settings.view_transform = 'Standard'
    # scene.view_settings.look = 'None'
    # scene.view_settings.exposure = 4.0
    # scene.view_settings.gamma = 1.0
    # scene.render.film_transparent = True

    # 2. Create RenderCamera
    location = [0, 0, 0]
    rotation = [90, 0, 0]
    render_camera = make_camera("RenderCamera", location, rotation)
    render_camera.data.type = 'ORTHO'
    focus_distance = render_camera.data.lens*1.0e-3
    bound_y = obj.dimensions.y
    bound_z = obj.dimensions.z
    render_camera.data.ortho_scale = bound_z
    bpy.ops.object.mode_set(mode='EDIT')
    centroid = get_object_centroid(obj)
    location[0] = centroid.x
    location[1] = centroid.y - 1.0
    location[2] = centroid.z 
    render_camera.location = location

    # 3. Set resolution
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1080

    # 8. Add keyframes for rotation to obj_tmp
    obj_tmp = obj.copy()
    obj_tmp.data = obj.data.copy()
    bpy.context.collection.objects.link(obj_tmp)
    obj_tmp.rotation_mode = 'XYZ'
    obj_tmp.keyframe_insert(data_path="rotation_euler", frame=1)
    obj_tmp.rotation_euler.z = radians(360)
    obj_tmp.keyframe_insert(data_path="rotation_euler", frame=31)
    bpy.context.scene.frame_end = 1
    bpy.context.scene.frame_end = 31

    # 9. Hide obj
    obj.hide_set(True)
    obj.hide_render = True

    # 10. Set scene camera
    scene.camera = render_camera

    # 11. Render transparent PNG sequence
    # tmp_output_path = os.path.join(output_path, "tmp")
    # os.makedirs(tmp_output_path, exist_ok=True)
    # scene.render.image_settings.file_format = 'PNG'
    # scene.render.image_settings.color_mode = 'RGBA'
    # scene.render.filepath = tmp_output_path + "/frame_"
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.use_file_extension = False
    scene.render.filepath = output_path
    bpy.ops.render.render(animation=True)

    # 12. Convert PNG sequence to GIF using FFmpeg
    # cmd = f"ffmpeg -y -i {tmp_output_path}/frame_%04d.png -vf format=rgba {output_path}/output.gif"
    # popen = Popen( cmd , shell=True)
    # popen.wait()

    # convert_images_to_gif(f"{tmp_output_path}/frame_*.png", f"{output_path}/output.gif")
    # # 13. Delete tmp directory
    # shutil.rmtree(tmp_output_path)
    bpy.ops.object.mode_set(mode='OBJECT')

    # 14. Delete obj_tmp and show obj
    bpy.ops.object.select_all(action='DESELECT')
    obj_tmp.select_set(True)
    bpy.ops.object.delete()
    obj.hide_set(False)
    obj.hide_render = False

# メッシュを取得する
def get_mesh_by_name(mesh_name):
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.name == mesh_name:
            return obj.data
    return None

def get_view_vector(camera):
    if camera.type != 'CAMERA':
        print("Error: Object must be of type 'CAMERA'")
        return None

    # カメラの回転モードを確認
    rotation_mode = camera.rotation_mode
    print(f"rotation_mode: {rotation_mode}")
    # 回転モードに基づいて、camera_rotationを取得
    if rotation_mode == 'QUATERNION':
        camera_rotation = camera.rotation_quaternion
    elif rotation_mode == 'AXIS_ANGLE':
        camera_rotation = camera.rotation_axis_angle.to_quaternion()
    else:  # 'XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX'
        camera_rotation = camera.rotation_euler.to_quaternion()

    view_vector = Vector((0.0, 0.0, -1.0))
    view_vector.rotate(camera_rotation)

    return view_vector.normalized()

# 内積の計算
def dot_product(v1, v2):
    return v1.dot(v2)

def get_connected_edges(vertex, edge_indices):
    return [edge for edge in vertex.link_edges if edge.index in edge_indices]

def find_loops(edges):
    loops = []
    vertex_to_edge_map = defaultdict(set)

    for edge in edges:
        for vertex in edge.verts:
            vertex_to_edge_map[vertex].add(edge)

    def find_loop(start_edge, vertex_to_edge_map):
        loop = []
        loop_edges = set()
        loop_length = 0.0

        current_edge = start_edge
        current_vertex = start_edge.verts[0]
        while True:
            loop.append(current_vertex)
            loop_edges.add(current_edge)
            loop_length += current_edge.calc_length()

            next_edges = vertex_to_edge_map[current_vertex] - loop_edges
            if not next_edges:
                break

            next_edge = next_edges.pop()
            next_vertex = next_edge.other_vert(current_vertex)

            current_edge = next_edge
            current_vertex = next_vertex

        return loop, loop_edges, loop_length

    while vertex_to_edge_map:
        start_edge = next(iter(vertex_to_edge_map.values()))
        if not start_edge:
            break
        start_edge = start_edge.pop()
        loop, loop_edges, loop_length = find_loop(start_edge, vertex_to_edge_map)

        if len(loop) > 2:
            loops.append((loop, loop_edges, loop_length))

        for vertex in loop:
            vertex_to_edge_map[vertex] -= loop_edges
            if not vertex_to_edge_map[vertex]:
                del vertex_to_edge_map[vertex]

    return loops

def calculate_loop_length(loop, mesh):
    length = 0
    for i in range(len(loop)):
        vert1 = mesh.vertices[loop[i]]
        vert2 = mesh.vertices[loop[i - 1]]
        length += (vert1.co - vert2.co).length
    return length

def select_edges(obj, edges):
    # オブジェクトが選択されていることを確認
    if not obj.select_get():
        obj.select_set(True)

    # アクティブなオブジェクトを設定
    bpy.context.view_layer.objects.active = obj

    # 現在のモードを保存しておく
    prev_mode = obj.mode

    # 編集モードに切り替える
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')

    # 全てのエッジの選択を解除
    bpy.ops.mesh.select_all(action='DESELECT')

    # エッジリストにあるエッジを選択
    bpy.ops.object.mode_set(mode='OBJECT')
    for edge in edges:
        obj.data.edges[edge.index].select = True

    # 編集モードに戻す
    bpy.ops.object.mode_set(mode='EDIT')


def find_optimized_loop(loop_edges):
    from collections import defaultdict

    vertex_to_edge_map = defaultdict(set)

    for edge in loop_edges:
        for vertex in edge.verts:
            vertex_to_edge_map[vertex].add(edge)

    def find_largest_loop(start_vertex, vertex_to_edge_map):
        visited_vertices = set()
        largest_loop = []
        stack = [(start_vertex, [])]

        while stack:
            current_vertex, current_path = stack.pop()

            if current_vertex not in visited_vertices:
                visited_vertices.add(current_vertex)
                current_path = current_path + [current_vertex]

                if len(current_path) > len(largest_loop):
                    largest_loop = current_path

                for edge in vertex_to_edge_map[current_vertex]:
                    next_vertex = edge.other_vert(current_vertex)
                    if next_vertex != start_vertex or len(current_path) > 2:
                        stack.append((next_vertex, current_path))

        return largest_loop

    if not vertex_to_edge_map:
        return [], []

    largest_loop = find_largest_loop(next(iter(vertex_to_edge_map)), vertex_to_edge_map)

    optimized_edges = []
    for i in range(len(largest_loop)):
        v1 = largest_loop[i]
        v2 = largest_loop[(i + 1) % len(largest_loop)]

        for edge in loop_edges:
            if set(edge.verts) == {v1, v2}:
                optimized_edges.append(edge)
                break

    return optimized_edges, largest_loop


def is_valid_loop(edge_list):
    # エッジから頂点のリストを作成
    vertex_list = []
    for edge in edge_list:
        vertex_list.append(edge.verts[0])
        vertex_list.append(edge.verts[1])

    # 頂点が2回だけ出現するかどうかをチェック
    for vertex in set(vertex_list):
        if vertex_list.count(vertex) != 2:
            return False

    # 頂点リストに含まれる各頂点が、エッジリスト内の2つのエッジに属しているかどうかを確認
    for vertex in set(vertex_list):
        connected_edges = [edge for edge in edge_list if vertex in edge.verts]
        if len(connected_edges) != 2:
            return False

    return True

def delete_selected_edges(obj):
    if obj.type != 'MESH':
        print("Error: Object must be of type 'MESH'")
        return

    bpy.ops.object.mode_set(mode='EDIT')
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)

    # 選択されているエッジを見つける
    selected_edges = [edge for edge in bm.edges if edge.select]

    # 選択されているエッジに隣接する面を見つける
    adjacent_faces = set()
    for edge in selected_edges:
        for face in edge.link_faces:
            adjacent_faces.add(face)

    # 選択されているエッジに隣接する面を削除
    bmesh.ops.delete(bm, geom=list(adjacent_faces), context='FACES')

    bmesh.update_edit_mesh(mesh)
    bpy.ops.object.mode_set(mode='OBJECT')

from collections import deque


def can_split_object(edge_list, obj, bm):
    bm_copy = bm.copy()
    bm_copy.verts.ensure_lookup_table()
    bm_copy.edges.ensure_lookup_table()
    bm_copy.faces.ensure_lookup_table()

    for face in bm_copy.faces:
        face.tag = False

    def flood_fill(start_face, forbidden_edges):
        face_queue = deque([start_face])

        while face_queue:
            current_face = face_queue.popleft()
            current_face.tag = True

            for loop in current_face.loops:
                if loop.edge.index not in forbidden_edges:
                    linked_faces = [lf for lf in loop.edge.link_faces if lf != current_face and loop.edge.index not in forbidden_edges]  # Apply forbidden_edges constraint in linked_faces list generation
                    for lf in linked_faces:
                        if not lf.tag:
                            lf.tag = True
                            face_queue.append(lf)

    edge_indices = {edge.index for edge in edge_list}
    first_edge = edge_list[0]
    linked_faces = first_edge.link_faces

    if len(linked_faces) != 2:
        bm_copy.free()
        return False

    start_face1 = linked_faces[0]
    start_face2 = linked_faces[1]

    flood_fill(start_face1, edge_indices)

    is_split_possible = not start_face2.tag

    bm_copy.free()

    return is_split_possible
from collections import deque

def can_split_object2(edge_list, bm, direction):
    bm_copy = bm.copy()
    bm_copy.verts.ensure_lookup_table()
    bm_copy.edges.ensure_lookup_table()
    bm_copy.faces.ensure_lookup_table()

    def flood_fill(start_face, forbidden_edges):
        visited_faces = set()
        face_queue = deque([start_face])

        while face_queue:
            current_face = face_queue.popleft()
            visited_faces.add(current_face)

            for loop in current_face.loops:
                if loop.edge not in forbidden_edges:
                    linked_faces = loop.edge.link_faces
                    for lf in linked_faces:
                        if lf not in visited_faces and loop.edge not in forbidden_edges:
                            visited_faces.add(lf)
                            face_queue.append(lf)
        return visited_faces

    edge_list = list(edge_list)
    first_edge = edge_list[0]
    linked_faces = first_edge.link_faces

    if len(linked_faces) != 2:
        bm_copy.free()
        return False

    start_face1 = linked_faces[0]
    start_face2 = linked_faces[1]

    visited_faces = flood_fill(start_face1, edge_list)

    is_split_possible = start_face2 not in visited_faces

    bm_copy.free()

    return is_split_possible


def find_largest_loop(obj, edge_list):
    # エッジリスト内のエッジから頂点を取得し、リスト内での出現回数をカウント
    vert_count = {}
    for edge in edge_list:
        for vert in edge.verts:
            if vert not in vert_count:
                vert_count[vert] = 0
            vert_count[vert] += 1

    # 輪っかを構成する頂点を抽出 (各頂点はちょうど2回出現する)
    loop_verts = [vert for vert in vert_count if vert_count[vert] == 2]

    # 輪っかを構成しないエッジを削除
    loop_edges = [edge for edge in edge_list if all(vert in loop_verts for vert in edge.verts)]

    # 輪っかを構成するエッジが存在しない場合、空のリストを返す
    if not loop_edges:
        return []

    # 輪っかを構成するエッジを順番通りに並べ替える
    ordered_loop_edges = [loop_edges.pop(0)]
    while loop_edges:
        current_edge = ordered_loop_edges[-1]
        for i, edge in enumerate(loop_edges):
            if current_edge.verts[1] == edge.verts[0]:
                ordered_loop_edges.append(loop_edges.pop(i))
                break
            elif current_edge.verts[1] == edge.verts[1]:
                edge.verts.reverse()
                ordered_loop_edges.append(loop_edges.pop(i))
                break
        else:
            break

    return ordered_loop_edges

def highlight_edges(mesh_object, edge_indices, color=(1, 0, 0), width=3):
    bpy.context.view_layer.objects.active = mesh_object
    mesh_object.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    for edge_index in edge_indices:
        mesh_object.data.edges[edge_index].select = True

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.mark_freestyle_edge()
    bpy.ops.object.mode_set(mode='OBJECT')

    active_view_layer = bpy.context.view_layer
    lineset = active_view_layer.freestyle_settings.linesets.new("HighlightedEdges")
    lineset.linestyle.color = color
    lineset.linestyle.thickness = width
    lineset.select_by_visibility = False
    lineset.select_by_edge_types = True  # Changed to the correct attribute name
    # lineset.edge_mark = True
    # lineset.select_by_edge_marks = True





def render_image(output_filepath, resolution_x=1920, resolution_y=1080, samples=128):
    scene = bpy.context.scene
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = output_filepath
    scene.render.resolution_x = resolution_x
    scene.render.resolution_y = resolution_y
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples
    scene.view_layers["View Layer"].use_pass_freestyle = True
    scene.render.use_freestyle = True
    bpy.ops.render.render(write_still=True)


def create_camera_auto(mesh_object, edge_indices, camera_name="Camera"):
    # 1. Compute the center of the selected edges
    edge_centers = [(mesh_object.vertices[mesh_object.edges[edge_index].vertices[0]].co + mesh_object.vertices[mesh_object.edges[edge_index].vertices[1]].co) / 2 for edge_index in edge_indices]  # Fixed line
    center = np.mean(np.array(edge_centers), axis=0)

    # 2. Calculate the bounding box of the selected edges
    min_coords = np.min(edge_centers, axis=0)
    max_coords = np.max(edge_centers, axis=0)
    size = max_coords - min_coords

    # Compute camera position and distance
    max_size = max(size)
    distance = max_size / (2 * np.tan(np.radians(45 / 2)))

    camera_data = bpy.data.cameras.new(name=camera_name)
    camera = bpy.data.objects.new(camera_name, camera_data)
    bpy.context.collection.objects.link(camera)

    # Set camera location and rotation
    camera.location = center + mathutils.Vector((0, -distance, 0))
    camera.rotation_euler = (np.pi / 2, 0, 0)

    return camera
