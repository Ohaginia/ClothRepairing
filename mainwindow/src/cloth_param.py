from enum import Enum


class ConstParam(Enum):
    human_face = 10000
    cloth_face = 15000
    start_frame = 68
    middle_frame = 20
    human_scale = 0.4
    render_resolution = 1080
    camera_rotation = [90, 0, 0]
    camera_location = [0, -4, 0.8]
    render_file_format = "FFMPEG"
    render_format = "MPEG4"
    target = "Armature"
    subtarget = "mixamorig:Spine"
    track_axis = "TRACK_NEGATIVE_Z"
    lock_axis = "LOCK_Y"
    background_color = (1, 1, 1, 1)


class ClothParam(Enum):
    quality = 12
    mass = 1
    tension_stiffness = 40
    compression_stiffness = 40
    shear_stiffness = 40
    bending_stiffness = 10
    tension_damping = 25
    compression_damping = 25
    shear_damping = 25
    use_dynamic_mesh = True
    distance_min = 0.001
    # shrink_min = 0.2
    shrink_min = 0.05
    # shrink_min = -0.1
    group = "Group"
    group_shrink_max = 0.1
    compression_stiffness_max = 1000
    shear_stiffness_max = 1000
    bending_stiffness_max = 1000
    tension_stiffness_max = 1000


cloth_map = {"neck": "mixamorig:Neck",
             "hip": "mixamorig:Spine",
             "sholder_r": "mixamorig:RightShoulder",
             "sholder_l": "mixamorig:LeftShoulder",
             "hand_l": "mixamorig:LeftHand",
             "hand_r": "mixamorig:RightHand",
             "ankle_l": "mixamorig:LeftFoot",
             "ankle_r": "mixamorig:RightFoot",
             "knee_l": "mixamorig:LeftUpLeg",
             "knee_r": "mixamorig:RightUpLeg",
             "elbow_l": "mixamorig:LeftForeArm",
             "elbow_r": "mixamorig:RightForeArm",
             }

ignore_bone_list = ["mixamorig:LeftHandIndex1", "mixamorig:LeftHandIndex2",
                    "mixamorig:LeftHandIndex3", "mixamorig:LeftHandIndex4",
                    "mixamorig:LeftHandMiddle1", "mixamorig:LeftHandMiddle2",
                    "mixamorig:LeftHandMiddle3", "mixamorig:LeftHandMiddle4",
                    "mixamorig:LeftHandPinky1", "mixamorig:LeftHandPinky2",
                    "mixamorig:LeftHandPinky3", "mixamorig:LeftHandPinky4",
                    "mixamorig:LeftHandRing1", "mixamorig:LeftHandRing2",
                    "mixamorig:LeftHandRing3", "mixamorig:LeftHandRing4",
                    "mixamorig:LeftHandThumb1", "mixamorig:LeftHandThumb2",
                    "mixamorig:LeftHandThumb3", "mixamorig:LeftHandThumb4",
                    "mixamorig:RightHandIndex1", "mixamorig:RightHandIndex2",
                    "mixamorig:RightHandIndex3", "mixamorig:RightHandIndex4",
                    "mixamorig:RightHandMiddle1", "mixamorig:RightHandMiddle2",
                    "mixamorig:RightHandMiddle3", "mixamorig:RightHandMiddle4",
                    "mixamorig:RightHandPinky1", "mixamorig:RightHandPinky2",
                    "mixamorig:RightHandPinky3", "mixamorig:RightHandPinky4",
                    "mixamorig:RightHandRing1", "mixamorig:RightHandRing2",
                    "mixamorig:RightHandRing3", "mixamorig:RightHandRing4",
                    "mixamorig:RightHandThumb1", "mixamorig:RightHandThumb2",
                    "mixamorig:RightHandThumb3", "mixamorig:RightHandThumb4",
                    "mixamorig:LeftToeBase", "mixamorig:RightToeBase",
                    "mixamorig:LeftToeBase_end", "mixamorig:RightToeBase_end"
                    "mixamorig:LeftToeBase_end_end", "mixamorig:RightToeBase_end_end"]
cloth_type = ["shirt", "skirt", "pants", "onepiece_short", "onepiece_long"]
