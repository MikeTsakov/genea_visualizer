import sys
import os
import bpy
import math
import random
from mathutils import Vector
import time
import argparse
import tempfile
from pathlib import Path

# cleans up the scene and memory
def clear_scene():
    for block in bpy.data.meshes:       bpy.data.meshes.remove(block)
    for block in bpy.data.materials:    bpy.data.materials.remove(block)
    for block in bpy.data.textures:     bpy.data.textures.remove(block)
    for block in bpy.data.images:       bpy.data.images.remove(block)  
    for block in bpy.data.curves:       bpy.data.curves.remove(block)
    for block in bpy.data.cameras:      bpy.data.cameras.remove(block)
    for block in bpy.data.lights:       bpy.data.lights.remove(block)
    for block in bpy.data.sounds:       bpy.data.sounds.remove(block)
    for block in bpy.data.armatures:    bpy.data.armatures.remove(block)
    for block in bpy.data.objects:      bpy.data.objects.remove(block)
    for block in bpy.data.actions:      bpy.data.actions.remove(block)
            
    if bpy.context.object == None:          bpy.ops.object.delete()
    elif bpy.context.object.mode == 'EDIT': bpy.ops.object.mode_set(mode='OBJECT')
    elif bpy.context.object.mode == 'POSE': bpy.ops.object.mode_set(mode='OBJECT')
        
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    bpy.ops.sequencer.select_all(action='SELECT')
    bpy.ops.sequencer.delete()

def remove_bone(armature, bone_name):
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in armature.data.edit_bones: # deselect the other bones
        if bone.name == bone_name:
            armature.data.edit_bones.remove(bone)
    bpy.ops.object.mode_set(mode='OBJECT')
    
def load_fbx(fbx_path):
    bpy.ops.import_scene.fbx(filepath=fbx_path, ignore_leaf_bones=True, 
    force_connect_children=True, automatic_bone_orientation=False)
    remove_bone(bpy.data.objects['Armature'], 'b_r_foot_End')
        
def load_bvh(filepath):
    bpy.ops.import_anim.bvh(filepath=filepath, use_fps_scale=False,
    update_scene_fps=True, update_scene_duration=True, global_scale=0.01)

def add_materials(work_dir):
    mat = bpy.data.materials.new('gray')
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texImage.image = bpy.data.images.load(os.path.join(work_dir, 'model', "LowP_03_Texture_ColAO_grey5.jpg"))
    mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])

    obj = bpy.data.objects['LowP_01']
    obj.modifiers['Armature'].use_deform_preserve_volume=True
    # Assign it to object
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    
    # set new material to variable
    mat = bpy.data.materials.new(name="FloorColor")
    mat.diffuse_color = (0.15, 0.4, 0.25, 1)
    
def constraintBoneTargets(armature = 'Armature', rig = 'None', mode = 'full_body'):
    armobj = bpy.data.objects[armature]
    for ob in bpy.context.scene.objects: ob.select_set(False)
    bpy.context.view_layer.objects.active = armobj
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    for bone in bpy.context.selected_pose_bones:
        # Delete all other constraints
        for c in bone.constraints:
            bone.constraints.remove( c )
        # Create body_world location to fix floating legs
        if bone.name == 'body_world' and mode == 'full_body':
            constraint = bone.constraints.new('COPY_LOCATION')
            constraint.target = bpy.context.scene.objects[rig]
            temp = bone.name.replace('BVH:','')
            constraint.subtarget = temp
        # Create all rotations
        if bpy.context.scene.objects[armature].data.bones.get(bone.name) is not None:
            constraint = bone.constraints.new('COPY_ROTATION')
            constraint.target = bpy.context.scene.objects[rig]
            temp = bone.name.replace('BVH:','')
            constraint.subtarget = temp
    if mode == 'upper_body':
        bpy.context.object.pose.bones["b_root"].constraints["Copy Rotation"].mute = True
        bpy.context.object.pose.bones["b_r_upleg"].constraints["Copy Rotation"].mute = True
        bpy.context.object.pose.bones["b_r_leg"].constraints["Copy Rotation"].mute = True
        bpy.context.object.pose.bones["b_l_upleg"].constraints["Copy Rotation"].mute = True
        bpy.context.object.pose.bones["b_l_leg"].constraints["Copy Rotation"].mute = True
    bpy.ops.object.mode_set(mode='OBJECT')
    
def load_audio(filepath):
    bpy.context.scene.sequence_editor_create()
    bpy.context.scene.sequence_editor.sequences.new_sound(
        name='AudioClip',
        filepath=filepath,
        channel=1,
        frame_start=0
    )
    
def create_fbx(output_dir):
    fbx_output = "\\output"
    bpy.ops.object.select_all(action='DESELECT')
    obj = bpy.data.objects['Armature']
    obj_mesh = bpy.data.objects['LowP_01']
    obj.select_set(True)
    obj_mesh.select_set(True)
    output_dir = str(output_dir) + fbx_output
    print(str(output_dir))
    bpy.ops.export_scene.fbx(filepath=str(output_dir) + '\\output.fbx', use_selection=True)

########################
# Retarget Method No.1 #
########################
def retarget_keemap(testing):
    
    mapping_file_folder = "S:\\Work\\WIP\\WARA_Media_and_Language\\Unreal_setup\\configs\\config_1.json"
    
    bpy.data.scenes["Scene"].keemap_settings.source_rig_name = 'session30_take5_hasFingers_shallow26_scale_local_30fps_3.6k'
    bpy.data.scenes["Scene"].keemap_settings.destination_rig_name = 'Armature'
    bpy.data.scenes["Scene"].keemap_settings.bone_mapping_file = mapping_file_folder
    
    bpy.data.scenes["Scene"].keemap_settings.start_frame_to_apply = 1
    bpy.data.scenes["Scene"].keemap_settings.number_of_frames_to_apply = 1200
    bpy.data.scenes["Scene"].keemap_settings.keyframe_every_n_frames = 1
    
    bpy.data.scenes["Scene"].keemap_settings.keyframe_test = True
    
    bpy.ops.wm.keemap_read_file()
    bpy.ops.wm.test_all_bones()
    if testing == False:
        bpy.ops.wm.perform_animation_transfer()
    
#    start_frame = bpy.data.scenes["Scene"].keemap_settings.start_frame_to_apply
#    bone_file = bpy.data.scenes["Scene"].keemap_bone_mapping_list
#    bone_index = bpy.data.scenes["Scene"].keemap_bone_mapping_list_index
#    end_frame = bpy.data.scenes["Scene"].keemap_settings.number_of_frames_to_apply
#    source = bpy.data.scenes["Scene"].keemap_settings.source_rig_name
#    destination = bpy.data.scenes["Scene"].keemap_settings.destination_rig_name
    
    mapping_file_folder = "D:\\Utrecht University\\Thesis\\blender\\retarget_pred_1.json"
    
    bpy.data.scenes["Scene"].keemap_settings.source_rig_name = 'pred'
    bpy.data.scenes["Scene"].keemap_settings.destination_rig_name = 'mixamorig:root.001'
    bpy.data.scenes["Scene"].keemap_settings.bone_mapping_file = mapping_file_folder
    
    bpy.data.scenes["Scene"].keemap_settings.keyframe_test = True
    
    bpy.ops.wm.keemap_read_file()
    bpy.ops.wm.test_all_bones()
    if testing == False:
        bpy.ops.wm.perform_animation_transfer()

########################
# Retarget Method No.2 #
########################
def retarget_retarget(fp, bot_fp, load_bots, version):
    bpy.ops.object.select_all(action='DESELECT')
    if version == 0:
        load_bot(bot_fp, load_bots, version)
        obj_gt = bpy.data.objects['gt']
        bpy.context.object.animation_retarget_state['source'] = obj_gt
        obj_bot = bpy.data.objects['mixamorig:root']
        bpy.context.object.animation_retarget_state['target'] = obj_bot
        bpy.ops.retarget.load(filepath=fp + "retarget_gt_full.rtconf")
#        bpy.context.object.animation_retarget_state.disable_drivers = True
    elif version == 1:
        load_bot(bot_fp, load_bots, version)
        obj_pred = bpy.data.objects['pred']
        bpy.context.object.animation_retarget_state['source'] = obj_pred
        obj_bot = bpy.data.objects['mixamorig:root.001']
        bpy.context.object.animation_retarget_state['target'] = obj_bot
        bpy.ops.retarget.load(filepath=fp + "retarget_pred_full.rtconf")
#        bpy.context.object.animation_retarget_state.disable_drivers = True

def parse_args():
    parser = argparse.ArgumentParser(description="Some description.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', help='Input file name of the BVH to render.', type=Path, required=True)
    parser.add_argument('-o', '--output_dir', help='Output directory where the rendered video files will be saved to. Will use "<script directory/output/" if not specified.', type=Path)
    parser.add_argument('-s', '--start', help='Which frame to start rendering from.', type=int, default=0)
    parser.add_argument('-d', '--duration', help='How many consecutive frames to render.', type=int, default=3600) 
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :]
    return vars(parser.parse_args(args=argv))

def main():
    IS_SERVER = "GENEA_SERVER" in os.environ
    if IS_SERVER:
        print('[INFO] Script is running inside a GENEA Docker environment.')
        
    if bpy.ops.text.run_script.poll():
        print('[INFO] Script is running in Blender UI.')
        SCRIPT_DIR = Path(bpy.context.space_data.text.filepath).parents[0]
        ##################################
        ##### SET ARGUMENTS MANUALLY #####
        ##### IF RUNNING BLENDER GUI #####
        ##################################
        ARG_BVH_PATHNAME = SCRIPT_DIR / 'session30_take5_hasFingers_shallow26_scale_local_30fps_3.6k.bvh'
        ARG_START_FRAME = 0
        ARG_DURATION_IN_FRAMES = 3600
        ARG_OUTPUT_DIR = ARG_BVH_PATHNAME.parents[0]
    else:
        print('[INFO] Script is running from command line.')
        SCRIPT_DIR = Path(os.path.realpath(__file__)).parents[0]
        # process arguments
        args = parse_args()
        ARG_BVH_PATHNAME = args['input']
        ARG_START_FRAME = args['start']
        ARG_DURATION_IN_FRAMES = args['duration']
        ARG_OUTPUT_DIR = args['output_dir'].resolve() if args['output_dir'] else ARG_BVH_PATHNAME.parents[0]
    
    # FBX file
    FBX_MODEL = os.path.join(SCRIPT_DIR, 'model', "GenevaModel_v2_Tpose_Final.fbx")
    BVH_NAME = os.path.basename(ARG_BVH_PATHNAME).replace('.bvh','')

    start = time.time()
    
    clear_scene()
    load_fbx(FBX_MODEL)
    add_materials(SCRIPT_DIR)
    load_bvh(str(ARG_BVH_PATHNAME))
    #Use retargeting plugin to transfer animation to new avatar
    #constraintBoneTargets(rig = BVH_NAME, mode = ARG_MODE)
    
    if not os.path.exists(str(ARG_OUTPUT_DIR)):
        os.mkdir(str(ARG_OUTPUT_DIR))
        
    total_frames = bpy.data.objects[BVH_NAME].animation_data.action.frame_range.y
    #render_video(str(ARG_OUTPUT_DIR), ARG_IMAGE, ARG_VIDEO, BVH_NAME, ARG_START_FRAME, min(ARG_DURATION_IN_FRAMES, total_frames), ARG_RESOLUTION_X, ARG_RESOLUTION_Y)
    create_fbx(ARG_OUTPUT_DIR)
    
    end = time.time()
    all_time = end - start
    print("output_file", str(list(ARG_OUTPUT_DIR.glob("*"))[0]), flush=True)
    
#Code line
main()
