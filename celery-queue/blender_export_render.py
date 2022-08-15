import sys
import os
import bpy
import math
import random
from mathutils import Vector
import time
import datetime
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

def setup_scene(cam_pos, cam_rot):
    # Camera
    bpy.ops.object.camera_add(enter_editmode=False, location=cam_pos, rotation=cam_rot)
    cam = bpy.data.objects['Camera']
    cam.scale = [20, 20, 20]
    bpy.context.scene.camera = cam # add cam so it's rendered
    
    # Floor Plane
    bpy.ops.mesh.primitive_plane_add(size=20, location=[0, 0, 0], rotation=[0, 0, 0])
    plane_obj = bpy.data.objects['Plane']
    plane_obj.name = 'Floor'
    plane_obj.scale = [100, 100, 100]
    mat = bpy.data.materials['FloorColor'] #set new material to variable
    plane_obj.data.materials.append(mat) #add the material to the object
    
    # Back Wall
    bpy.ops.mesh.primitive_plane_add(size=20, location=[0, 1, 0], rotation=[0, math.radians(90), math.radians(90)])
    plane1_obj = bpy.data.objects['Plane']
    plane1_obj.name = 'Wall_Back'
    plane1_obj.scale = [100, 100, 100]
    plane1_obj.data.materials.append(mat) #add the material to the object

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

def add_materials(work_dir, model):
    mat = bpy.data.materials.new('gray')
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
#    texImage.image = bpy.data.images.load(os.path.join(work_dir, 'model', "LowP_03_Texture_ColAO_grey5.jpg"))
    mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])

    if model == 'Lea':
        obj = bpy.data.objects['Lea1']
        obj.modifiers['Armature'].use_deform_preserve_volume=True
    elif model == 'Harold':
        obj = bpy.data.objects['remesh_7_combined_Remeshed3']
        obj.modifiers['Armature'].use_deform_preserve_volume=True
    elif model == 'Leffe':
        obj = bpy.data.objects['Leif_NyMesh']
        obj.modifiers['Armature'].use_deform_preserve_volume=True
    elif model == 'Majken':
        obj = bpy.data.objects['highres6']
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
    
########################
#     Render Video     #
########################   
def render_video(output_dir, picture, video, bvh_fname, render_frame_start, render_frame_length, res_x, res_y):
    bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
    bpy.context.scene.display.shading.light = 'MATCAP'
    bpy.context.scene.display.render_aa = 'FXAA'
    bpy.context.scene.render.resolution_x=int(res_x)
    bpy.context.scene.render.resolution_y=int(res_y)
    bpy.context.scene.render.fps = 30
    bpy.context.scene.frame_start = render_frame_start
    bpy.context.scene.frame_set(render_frame_start)
    if render_frame_length > 0:
        bpy.context.scene.frame_end = render_frame_start + render_frame_length
    
    if picture:
        bpy.context.scene.render.image_settings.file_format='PNG'
        bpy.context.scene.render.filepath=os.path.join(output_dir, '{}.png'.format(bvh_fname))
        bpy.ops.render.render(write_still=True)
        
    if video:
        print(f"total_frames {render_frame_length}", flush=True)
        bpy.context.scene.render.image_settings.file_format='FFMPEG'
        bpy.context.scene.render.ffmpeg.format='MPEG4'
        bpy.context.scene.render.ffmpeg.codec = "H264"
        bpy.context.scene.render.ffmpeg.ffmpeg_preset='REALTIME'
        bpy.context.scene.render.ffmpeg.constant_rate_factor='HIGH'
        bpy.context.scene.render.ffmpeg.audio_codec='MP3'
        bpy.context.scene.render.ffmpeg.gopsize = 30
        bpy.context.scene.render.filepath=os.path.join(output_dir, '{}_'.format(bvh_fname))
        bpy.ops.render.render(animation=True, write_still=True)

########################
# Retarget Method No.1 #
########################
def retarget_keemap(testing, start_frame, duration):
    
    mapping_file_folder = "S:\\Work\\WIP\\WARA_Media_and_Language\\genea_visualizer\\celery-queue\\configs\\config_1.json"
    bpy.data.scenes["Scene"].keemap_settings.bone_mapping_file = mapping_file_folder
    bpy.ops.wm.keemap_read_file()
    
#    If you want to change the settings manually
    bpy.data.scenes["Scene"].keemap_settings.source_rig_name = 'Quentin_Tarantino_44kHz'
#    bpy.data.scenes["Scene"].keemap_settings.destination_rig_name = 'Armature'
#    
    bpy.data.scenes["Scene"].keemap_settings.start_frame_to_apply = start_frame
    bpy.data.scenes["Scene"].keemap_settings.number_of_frames_to_apply = duration
    bpy.data.scenes["Scene"].keemap_settings.keyframe_every_n_frames = 1
    
    bpy.data.scenes["Scene"].keemap_settings.keyframe_test = True
    
    bpy.ops.wm.test_all_bones()
    if testing == False:
        bpy.ops.wm.perform_animation_transfer()
    
#    start_frame = bpy.data.scenes["Scene"].keemap_settings.start_frame_to_apply
#    bone_file = bpy.data.scenes["Scene"].keemap_bone_mapping_list
#    bone_index = bpy.data.scenes["Scene"].keemap_bone_mapping_list_index
#    end_frame = bpy.data.scenes["Scene"].keemap_settings.number_of_frames_to_apply
#    source = bpy.data.scenes["Scene"].keemap_settings.source_rig_name
#    destination = bpy.data.scenes["Scene"].keemap_settings.destination_rig_name

########################
# Retarget Method No.2 #
########################
def retarget_retarget(filepath):
    bpy.ops.object.select_all(action='DESELECT')
    obj_avatar = bpy.data.objects['Armature']
    bpy.context.view_layer.objects.active = obj_avatar
    bpy.context.object.animation_retarget_state.target = obj_avatar
    obj_gt = bpy.data.objects['output']
#    bpy.context.view_layer.objects.active = obj_gt
    bpy.context.object.animation_retarget_state.selected_source = obj_gt
    bpy.ops.retarget.load(filepath=str(filepath) + "\\configs\\retarget_config_1.rtconf")
#    bpy.context.object.animation_retarget_state.disable_drivers = True

########################
#     GENERATE FBX     #
########################
def create_fbx(output_dir, model):
    fbx_output = "\\output"
    bpy.ops.object.select_all(action='DESELECT')
    obj = bpy.data.objects['Armature']
#    obj_mesh = bpy.data.objects['LowP_01']
    if model == 'Lea':
        obj_mesh = bpy.data.objects['Lea1']
    elif model == 'Harold':
        obj_mesh = bpy.data.objects['remesh_7_combined_Remeshed3']
    elif model == 'Leffe':
        obj_mesh = bpy.data.objects['Leif_NyMesh']
    elif model == 'Majken':
        obj_mesh = bpy.data.objects['highres6']
    obj.select_set(True)
    obj_mesh.select_set(True)
    output_dir = str(output_dir) + fbx_output
    print(str(output_dir))
    cur_time = datetime.datetime.now()
#    arm_output = bpy.data.armatures['output']
#    bpy.data.armatures.remove(arm_output)
    arm_action = bpy.data.actions['Quentin_Tarantino_44kHz']
    bpy.data.actions.remove(arm_action)
    bpy.ops.export_scene.fbx(filepath=str(output_dir) + '\\output_{}_{}-{}_{}-{}.fbx'.format(model, cur_time.day, 
                                cur_time.month, cur_time.hour, cur_time.minute), use_selection=True, 
                                primary_bone_axis='X', secondary_bone_axis='-Y', axis_forward='-Y', axis_up='Z', 
                                bake_anim_use_all_actions=True)

########################
#      CMD INPUT       #
########################
def parse_args():
    parser = argparse.ArgumentParser(description="Some description.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', help='Input file name of the BVH to render.', type=Path, required=True)
    parser.add_argument('-o', '--output_dir', help='Output directory where the rendered video files will be saved to. Will use "<script directory/output/" if not specified.', type=Path)
    parser.add_argument('-s', '--start', help='Which frame to start rendering from.', type=int, default=0)
    parser.add_argument('-d', '--duration', help='How many consecutive frames to render.', type=int, default=3600)
    parser.add_argument('-mo', '--model', help='This is the model for the character.', type=str, default='Lea')
    parser.add_argument('-ma', '--market', help='This is a scenery of a marketplace.', action='store_true')
    parser.add_argument('-st', '--street', help='This is a scenery of a street.', action='store_true')
    parser.add_argument('-ro', '--room', help='This is a scenery of a room.', action='store_true')
    # Load .blend file with specific scene
    # Give options to configure parts of that loaded scene
    # Export and import to Unreal Engine
    #### ROOM ####
    parser.add_argument('-ro_bw-c', '--room_backwall_material', help='This is a scenery of a marketplace.', type=str, default='green')
    parser.add_argument('-ro_c-c', '--room_ceiling_material', help='This is a scenery of a street.', type=str, default='wood.tga')
    parser.add_argument('-ro_g-c', '--room_ground_material', help='This is a scenery of a room.', type=str, default='wood.tga')
    #### IDEAS ####
    # time of day for the scenes
    # different options for the market scene
    # different material for the room scene
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
        ARG_BVH_PATHNAME = SCRIPT_DIR / 'input/Quentin_Tarantino_44kHz.bvh'
        ARG_AUDIO_FILE_NAME = SCRIPT_DIR / 'input/Quentin_Tarantino_44kHz.wav' # set to None for no audio
        ARG_IMAGE = True
        ARG_VIDEO = False
        ARG_START_FRAME = 0
        ARG_DURATION_IN_FRAMES = 785
        ARG_MODEL = 'Lea'
        ARG_ROTATE = 'default'
        ARG_RESOLUTION_X = 1024
        ARG_RESOLUTION_Y = 768
        ARG_MODE = 'full_body'
        ARG_OUTPUT_DIR = SCRIPT_DIR
        print(ARG_OUTPUT_DIR)
        ARG_TESTING = True
        ARG_TESTING_TYPE = 'keemap'
    else:
        print('[INFO] Script is running from command line.')
        SCRIPT_DIR = Path(os.path.realpath(__file__)).parents[0]
        # process arguments
        args = parse_args()
        #have to fix input path changed output.bvh to 'input' folder 
        ARG_BVH_PATHNAME = args['input']
        ARG_START_FRAME = args['start']
        ARG_DURATION_IN_FRAMES = args['duration']
        ARG_MODEL = args['model']
        ARG_OUTPUT_DIR = args['output_dir'].resolve() if args['output_dir'] else ARG_BVH_PATHNAME.parents[0]
        ARG_TESTING = True
        ARG_TESTING_TYPE = 'keemap'
        if args['room'] == True:
            ROOM_BACKWALL_MATERIAL = args['room_backwall_material']
            ROOM_CEILING_MATERIAL = args['room_ceiling_material']
            ROOM_GROUND_MATERIAL = args['room_ground_material']
    
    # FBX file
    if ARG_MODEL not in ['Lea', 'Leffe', 'Majken', 'Harold']:
        raise NotImplementedError("This character is not supported ({})!".format(ARG_MODEL))
    else:
        FBX_MODEL = os.path.join(SCRIPT_DIR, 'model', "{}_fixed.fbx".format(ARG_MODEL))
    BVH_NAME = os.path.basename(ARG_BVH_PATHNAME).replace('.bvh','')

    if ARG_MODE not in ["full_body", "upper_body"]:
        raise NotImplementedError("This visualization mode is not supported ({})!".format(ARG_MODE))

    start = time.time()
    
    clear_scene()
    load_fbx(FBX_MODEL)
    add_materials(SCRIPT_DIR, ARG_MODEL)
    load_bvh(str(ARG_BVH_PATHNAME))
    #Use retargeting plugin to transfer animation to new avatar
    constraintBoneTargets(rig = BVH_NAME, mode = ARG_MODE)
    
    if ARG_MODE == "full_body": 	CAM_POS = [0, -3, 1.1]
    elif ARG_MODE == "upper_body":  CAM_POS = [0, -2.45, 1.3]
    CAM_ROT = [math.radians(90), 0, 0]
    setup_scene(CAM_POS, CAM_ROT)
    
    if not os.path.exists(str(ARG_OUTPUT_DIR)):
        os.mkdir(str(ARG_OUTPUT_DIR))
        
    total_frames = bpy.data.objects[BVH_NAME].animation_data.action.frame_range.y
    render_video(str(ARG_OUTPUT_DIR), ARG_IMAGE, ARG_VIDEO, BVH_NAME, ARG_START_FRAME, min(ARG_DURATION_IN_FRAMES, total_frames), ARG_RESOLUTION_X, ARG_RESOLUTION_Y)
#    if ARG_TESTING_TYPE == 'keemap':
#        retarget_keemap(ARG_TESTING, ARG_START_FRAME, ARG_DURATION_IN_FRAMES)
#    elif ARG_TESTING_TYPE == 'retarget':
#        retarget_retarget(ARG_OUTPUT_DIR)
    
#    if ARG_TESTING == False: 
#        create_fbx(ARG_OUTPUT_DIR, ARG_MODEL)
    
    end = time.time()
    all_time = end - start
    print("output_file", str(list(ARG_OUTPUT_DIR.glob("*"))[0]), flush=True)
    
#Code line
main()
