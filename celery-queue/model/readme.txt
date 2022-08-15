data_raw.bvh : original TWH data
data_30.bvh : processed TWH data with retargeted motion w.r.t. a T-pose (used to verify motion quality remains the same as the raw data)
take_1, 2, 3.bvh : example BVH files taken from the training set at GENEA 2022 (same as data_30, but root-normalized)
*_fixed_half.mb : Maya scene file with the fixed weights (right arm only)
*_fixed.mb : Maya scene file with the fixed weights (mirrored)
*_fixed.fbx : the models with fixed weights
*_playground.fbx : files with BVH motion, the avatars, and retargeting (for quality inspection)
"textures/" : folder containing all textures for all models
"images/" : folder with demo images of weight-related problems and observations, as well as before/after photos

----------------

**Observations**

- images taken from "take_2.bvh"
- "scap" bone does not rotate, has no weights, so it is fine to move weights to "shoulder" bone
- "arm" bone controls arm movement except twist, has rotation, has weights on the arm
- "arm_twist" bone controls arm twist only, has rotation, has no weights on arm, so does not affect the mesh

**Problem**

- when "arm_twist" rotates (expected) the mesh will not be affected (no weights)
 - solution: move "arm" weights to "arm_twist" weights, as rotation to "arm" bone will affect the "arm_twist" bone as well
- crease around elbow when forearm is flexed
 - solution: better blend the weights between "arm_twist" and "forearm" bones around the arm/elbow
 - solution: dual quaternion should help with mesh losing volume (done on the animation level, not the modelling level)

**Fix Procedure**

1. Import "Final" model
1. Initialize ngSkinTools
1. ~~Cut "arm" weights, paste to "arm_twist"~~
1. Set to pose below this list
1. Set camera to cam settings below this list
1. Save to "*_init.mb"
1. Make "before" photo with camera, then disable cam
1. Cleanup shoulder weights for "arm" bone
1. Cleanup elbow weights for "arm_twist" bone
1. Cleanup forearm/wrist weights for "wrist_twist" bone
1. Save to "*_fixed_half.mb"
1. Make "after" photo
1. Mirror bone weights using " \*\_r\_\* > \*\_l\_\* "
1. Save to "*_fixed.mb"
1. Export all to "*_fixed.fbx"

When cleaning up, set the following pose:

- Take 2 : 1455 @24
- r_shoulder
 - -7.65
 - -8.62
 - -3.20
- r_arm
 - 71.91
 - 16.50
 - 88.59
- r_arm_twist
 - 54.67
 - 0.68
 - 1.91
- r_forearm
 - -7.95
 - 12.11
 - -78.10
- r_wrist_twist
 - -67.77
 - -3.22
 - 5.69
- r_wrist
 - 11.49
 - 8.42
 - 3.91

Cam

- pos : -91 | 152 | 103
- rot : -13 | -42 | 1