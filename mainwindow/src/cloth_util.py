import bpy
import math
import numpy as np
from mathutils import Vector, Matrix
from cloth_param import ClothParam

def normalize(v):
    norm = np.linalg.norm(v)
    norm = np.sqrt(sum(v**2))
    if norm==0:
        return v
    return v / norm
def get_quaternion_from_euler(roll, pitch, yaw):
    qx = np.sin(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) - np.cos(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
    qy = np.cos(roll/2) * np.sin(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.cos(pitch/2) * np.sin(yaw/2)
    qz = np.cos(roll/2) * np.cos(pitch/2) * np.sin(yaw/2) - np.sin(roll/2) * np.sin(pitch/2) * np.cos(yaw/2)
    qw = np.cos(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)  
    return [qw, qx, qy, qz]
    
def delete_all():
#     bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.data.objects:
        obj.hide_set(False)
        obj.hide_select = False
        obj.hide_viewport = False
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

def make_empty(name, location, size, display_type, disp_front=False, disp_name=True):
    empty_obj = bpy.data.objects.new( "empty", None, )
    empty_obj.name = name
    empty_obj.empty_display_size = size 
    empty_obj.empty_display_type = display_type
    empty_obj.location = location
    if len(bpy.data.collections) > 0:
        bpy.data.collections[0].objects.link(empty_obj)
    else :
        bpy.context.scene.collection.objects.link(empty_obj)        
    empty_obj.show_in_front = disp_front
    empty_obj.show_name = disp_name
    return empty_obj

def make_camera(name, location, rotation_euler ):
    camera_data = bpy.data.cameras.new(name = name )
    camera_object = bpy.data.objects.new(name, camera_data)
    bpy.context.scene.collection.objects.link(camera_object)
    camera_object.name = name
    camera_object.location = location
    camera_object.rotation_euler =  [math.radians(rotation_euler[0]),math.radians(rotation_euler[1]),math.radians(rotation_euler[2])]
    return camera_object

def set_decimate(obj, ratio):
    bpy.context.view_layer.objects.active=obj
    obj.modifiers.new(name='Decimate', type='DECIMATE')
    decimate = obj.modifiers['Decimate']
    decimate.ratio = ratio
    bpy.ops.object.modifier_apply(modifier="Decimate")

def set_cloth(obj, edge_stiffness = False):
    cloth_mod = obj.modifiers.new(name='Cloth', type='CLOTH')
    cloth_mod.settings.quality = ClothParam.quality.value
    cloth_mod.settings.mass = ClothParam.mass.value
    cloth_mod.settings.tension_stiffness = ClothParam.tension_stiffness.value
    cloth_mod.settings.compression_stiffness = ClothParam.compression_stiffness.value
    cloth_mod.settings.shear_stiffness = ClothParam.shear_stiffness.value
    cloth_mod.settings.bending_stiffness = ClothParam.bending_stiffness.value
    cloth_mod.settings.tension_damping = ClothParam.tension_damping.value
    cloth_mod.settings.compression_damping = ClothParam.compression_damping.value
    cloth_mod.settings.shear_damping = ClothParam.shear_damping.value
    cloth_mod.settings.shrink_min = ClothParam.shrink_min.value
    cloth_mod.settings.use_dynamic_mesh = ClothParam.use_dynamic_mesh.value
    cloth_mod.collision_settings.distance_min = ClothParam.distance_min.value
    cloth_mod.point_cache.frame_start = 0
    cloth_mod.point_cache.frame_end = bpy.context.scene.frame_end
    if edge_stiffness:
        cloth_mod.settings.vertex_group_structural_stiffness = ClothParam.group.value
        cloth_mod.settings.vertex_group_shear_stiffness = ClothParam.group.value
        cloth_mod.settings.vertex_group_bending = ClothParam.group.value
        cloth_mod.settings.vertex_group_shrink = ClothParam.group.value
        cloth_mod.settings.tension_stiffness_max = ClothParam.tension_stiffness_max.value
        cloth_mod.settings.compression_stiffness_max = ClothParam.compression_stiffness_max.value
        cloth_mod.settings.shear_stiffness_max = ClothParam.shear_stiffness_max.value
        cloth_mod.settings.bending_stiffness_max = ClothParam.bending_stiffness_max.value
    return cloth_mod

def export_fbx(fp):
    bpy.ops.export_scene.fbx(filepath=fp,
                        check_existing=True,
                        filter_glob='*.fbx',
                        use_selection=False,
                        # use_visible=False,
                        use_active_collection=False,
                        global_scale=1.0,
                        apply_unit_scale=True,
                        apply_scale_options='FBX_SCALE_NONE',
                        use_space_transform=True,
                        bake_space_transform=False,
                        object_types={'ARMATURE','MESH'},
                        use_mesh_modifiers=True,
                        use_mesh_modifiers_render=True,
                        mesh_smooth_type='OFF',
                        use_subsurf=False,
                        use_mesh_edges=False,
                        use_tspace=False,
                        # use_triangles=False,
                        use_custom_props=False,
                        add_leaf_bones=False,
                        primary_bone_axis='Y',
                        secondary_bone_axis='X',
                        use_armature_deform_only=False,
                        armature_nodetype='NULL',
                        bake_anim=True,
                        bake_anim_use_all_bones=True,
                        bake_anim_use_nla_strips=False,
                        bake_anim_use_all_actions=False,
                        bake_anim_force_startend_keying=False,
                        bake_anim_step=1.0,
                        bake_anim_simplify_factor=1.0,
                        path_mode='COPY',
                        embed_textures=True,
                        batch_mode='OFF',
                        use_batch_own_dir=True,
                        use_metadata=True,
                        axis_forward='-Z',
                        axis_up='Y')
    
def export_fbx2(fp):
    bpy.ops.export_scene.fbx(filepath=fp,
                        check_existing=True,
                        filter_glob='*.fbx',
                        use_selection=False,
                        # use_visible=False,
                        use_active_collection=False,
                        global_scale=1.0,
                        apply_unit_scale=True,
                        apply_scale_options='FBX_SCALE_NONE',
                        use_space_transform=True,
                        bake_space_transform=False,
                        object_types={'ARMATURE','MESH', 'EMPTY'},
                        use_mesh_modifiers=True,
                        use_mesh_modifiers_render=True,
                        mesh_smooth_type='OFF',
                        use_subsurf=False,
                        use_mesh_edges=False,
                        use_tspace=False,
                        # use_triangles=False,
                        use_custom_props=False,
                        add_leaf_bones=False,
                        primary_bone_axis='Y',
                        secondary_bone_axis='X',
                        use_armature_deform_only=False,
                        armature_nodetype='NULL',
                        bake_anim=True,
                        bake_anim_use_all_bones=True,
                        bake_anim_use_nla_strips=False,
                        bake_anim_use_all_actions=False,
                        bake_anim_force_startend_keying=False,
                        bake_anim_step=1.0,
                        bake_anim_simplify_factor=1.0,
                        path_mode='COPY',
                        embed_textures=True,
                        batch_mode='OFF',
                        use_batch_own_dir=True,
                        use_metadata=True,
                        axis_forward='-Z',
                        axis_up='Y')