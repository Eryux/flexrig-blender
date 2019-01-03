# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import mathutils

def get_context_mode():
    return bpy.context.active_object.mode if bpy.context.active_object is not None else 'OBJECT'

def switch_context_mode(target_mode):
    if get_context_mode() != target_mode:
        bpy.ops.object.mode_set(mode=target_mode)

class Flexrig:
    
    def __init__(self, arm_name):
        switch_context_mode('OBJECT')
        bpy.ops.object.armature_add(view_align=False, enter_editmode=False, location=(0.0,0.0,0.0),layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
        self.arm = bpy.context.object

        self.arm.name = arm_name
        self.arm.data.name = arm_name + ".amt"
        self.arm.show_x_ray = True

        self.bones = {}

    def create_chest(self, stomach_loc, chest_loc, neck_loc):
        self.bones["body"] = {}

        d_mode = get_context_mode()
        switch_context_mode('EDIT')

        # rib (first bone created so it's not needed to create again)
        b_stomach = self.arm.data.edit_bones[0]
        b_stomach.name = self.arm.name + ".rib"
        b_stomach.head = stomach_loc
        b_stomach.tail = chest_loc 

        self.bones["body"]["rib"] = b_stomach.name

        # Chest
        b_chest = self.add_bone(self.arm.name + ".chest", chest_loc, neck_loc, b_stomach)
        self.bones["body"]["chest"] = b_chest.name

        # Clear
        self.unselect_all_edit_bones()
        switch_context_mode(d_mode)

    def create_head(self, suffix, neck_loc, head_loc):
        if 'head' not in self.bones:
            self.bones["heads"] = []

        head_data = {}
        base_name = self.arm.name + ".head." + str(len(self.bones["heads"]))

        d_mode = get_context_mode()
        switch_context_mode('EDIT')

        # Neck
        b_chest = self.find_edit_bones_by_name(self.bones["body"]["chest"])[0]
        b_neck = self.add_bone(base_name + ".neck." + suffix, b_chest.tail, neck_loc, b_chest)
        head_data["neck"] = b_neck.name
        
        # Head
        b_head = self.add_bone(base_name + ".head." + suffix, b_neck.tail, head_loc, b_neck)
        head_data["head"] = b_head.name

        # Add to armature data
        self.bones["heads"].append(head_data)

        # Clear
        self.unselect_all_edit_bones()
        switch_context_mode(d_mode)

    def create_arm(self, suffix, uarm_loc, larm_loc, wrist_loc, shoulder=False, ik=False, hand_loc=None, thumb_loc=None):
        if 'arms' not in self.bones:
            self.bones["arms"] = []
        
        arm_data = {}
        base_name = self.arm.name + ".arm." + str(len(self.bones["arms"]))

        d_mode = get_context_mode()
        switch_context_mode('EDIT')

        # Shoulder
        b_shoulder = None
        if shoulder:
            b_rib = self.arm.data.edit_bones[self.bones["body"]["rib"]]
            b_shoulder = self.add_bone(base_name + ".shoulder." + suffix, b_rib.tail, uarm_loc, b_rib)
            arm_data["shoulder"] = b_shoulder.name

        # Upper arm
        b_upper = self.add_bone(base_name + ".upper_arm." + suffix, uarm_loc, larm_loc, b_shoulder)
        arm_data["upper_arm"] = b_upper.name

        # Lower arm
        b_lower = self.add_bone(base_name + ".lower_arm." + suffix, larm_loc, wrist_loc, b_upper)
        arm_data["lower_arm"] = b_lower.name

        # Hand & Thumb
        if hand_loc is not None:
            b_hand = self.add_bone(base_name + ".hand." + suffix, wrist_loc, hand_loc, b_lower)
            arm_data["hand"] = b_hand.name
        if thumb_loc is not None:
            b_thumb = self.add_bone(base_name + ".thumb." + suffix, wrist_loc, thumb_loc, b_lower)
            arm_data["thumb"] = b_thumb.name

        # IK
        if ik:
            # Elbow
            b_elbow = self.add_bone(base_name + ".elbow." + suffix, [larm_loc[0], larm_loc[1] - 1.5, larm_loc[2] - 0.2], [larm_loc[0], larm_loc[1] - 1.5, larm_loc[2] + 0.2])
            b_elbow.use_deform = False
            arm_data["elbow"] = b_elbow.name

            # Constraint
            b_ik = self.add_bone(base_name + ".ik." + suffix, wrist_loc, [wrist_loc[0], wrist_loc[1] + 0.5, wrist_loc[2]])
            b_ik.use_deform = False
            arm_data["ik"] = b_ik.name

            if hand_loc is not None:
                b_hand.use_connect = False
                b_hand.parent = b_ik
            if thumb_loc is not None:
                b_thumb.use_connect = False
                b_thumb.parent = b_ik

            self.add_ik(b_lower, b_upper, b_ik, b_elbow, 2)

        # Add to armature data
        self.bones["arms"].append(arm_data)

        # Clear
        self.unselect_all_edit_bones()
        switch_context_mode(d_mode)

    def create_leg(self, suffix, uleg_loc, lleg_loc, heel_loc, foot_loc, hip=False, ik=False):
        if 'legs' not in self.bones:
            self.bones["legs"] = []

        leg_data = {}
        base_name = self.arm.name + ".leg." + str(len(self.bones["legs"]))

        d_mode = get_context_mode()
        switch_context_mode('EDIT')

        # Hip
        b_hip = None
        if hip:
            b_rib = self.arm.data.edit_bones[self.bones["body"]["rib"]]
            b_hip = self.add_bone(base_name + ".hip." + suffix, b_rib.head, uleg_loc)
            b_hip.use_connect = False
            b_hip.parent = b_rib
            leg_data["hip"] = b_hip.name

        # Upper leg
        b_upper = self.add_bone(base_name + ".upper_leg." + suffix, uleg_loc, lleg_loc, b_hip)
        leg_data["upper_leg"] = b_upper.name

        # Lower leg
        b_lower = self.add_bone(base_name + ".lower_leg." + suffix, lleg_loc, heel_loc, b_upper)
        leg_data["lower_leg"] = b_lower.name

        # Foot
        b_foot = self.add_bone(base_name + ".foot." + suffix, heel_loc, foot_loc, b_lower)
        leg_data["foot"] = b_foot.name

        if ik:
            # Knee
            b_knee = self.add_bone(base_name + ".knee." + suffix, [lleg_loc[0], lleg_loc[1] - 1.5, lleg_loc[2] - 0.2], [lleg_loc[0], lleg_loc[1] - 1.5, lleg_loc[2] + 0.2])
            b_knee.use_deform = False
            leg_data["knee"] = b_knee.name

            # Constraint
            b_ik = self.add_bone(base_name + ".ik." + suffix, heel_loc, [heel_loc[0], heel_loc[1] + 0.5, heel_loc[2]])
            b_ik.use_deform = False
            leg_data["ik"] = b_ik.name

            b_foot.use_connect = False
            b_foot.parent = b_ik

            self.add_ik(b_lower, b_upper, b_ik, b_knee, 2)

        # Add to armature data
        self.bones["legs"].append(leg_data)

        # Clear
        self.unselect_all_edit_bones()
        switch_context_mode(d_mode)

    def create_ik_controller(self, g_control=False):
        d_mode = get_context_mode()
        switch_context_mode('EDIT')
        b_rib = self.arm.data.edit_bones[self.bones["body"]["rib"]]

        if "arms" in self.bones:
            for a in self.bones["arms"]:
                if 'shoulder' not in a:
                    self.arm.data.edit_bones[a["upper_arm"]].parent = b_rib
                    self.arm.data.edit_bones[a["upper_arm"]].use_connect = False

        if "legs" in self.bones:
            for a in self.bones["legs"]:
                if 'hip' not in a:
                    self.arm.data.edit_bones[a["upper_leg"]].parent = b_rib
                    self.arm.data.edit_bones[a["upper_leg"]].use_connect = False
        
        # Create global controller
        if g_control:
            b_control = self.add_bone(self.arm.name + ".control", [0,0,0], [0,-2.0,0])
            b_rib.parent = b_control
            b_rib.use_connect = False

            if "arms" in self.bones:
                for a in self.bones["arms"]:
                    if "ik" in a:
                        self.arm.data.edit_bones[a["ik"]].parent = b_control
                        self.arm.data.edit_bones[a["ik"]].use_connect = False
                        self.arm.data.edit_bones[a["elbow"]].parent = b_control
                        self.arm.data.edit_bones[a["elbow"]].use_connect = False

            if "legs" in self.bones:
                for a in self.bones["legs"]:
                    if "ik" in a:
                        self.arm.data.edit_bones[a["ik"]].parent = b_control
                        self.arm.data.edit_bones[a["ik"]].use_connect = False
                        self.arm.data.edit_bones[a["knee"]].parent = b_control
                        self.arm.data.edit_bones[a["knee"]].use_connect = False

        # Clear
        self.unselect_all_edit_bones()
        switch_context_mode(d_mode)

    @staticmethod
    def link_to_object(src_name, target_name):
        d_mode = get_context_mode()
        switch_context_mode('OBJECT')

        # Attach to model
        t_object = bpy.data.objects[target_name]
        src = bpy.data.objects[src_name]

        src.select = True
        t_object.select = True
        bpy.context.scene.objects.active = src

        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        t_object.select = False

        # Clear
        switch_context_mode(d_mode)

    def add_bone(self, name, head, tail, parent=None):
        d_mode = get_context_mode()
        switch_context_mode('EDIT')

        bone = self.arm.data.edit_bones.new(name)

        if parent is not None:
            bone.parent = parent
            bone.use_connect = True

        bone.head = head
        bone.tail = tail

        switch_context_mode(d_mode)
        return bone

    def add_ik(self, bone, base, target, pole_target, chain_len):
        d_mode = get_context_mode()
        switch_context_mode('EDIT')

        # Calculate pole angle (Jerryno way)
        # see : http://blender.stackexchange.com/questions/19754/how-to-set-calculate-pole-angle-of-ik-constraint-so-the-chain-does-not-move
        projected_pole_axis = (target.tail - base.head).cross(pole_target.matrix.translation - base.head).cross(base.tail - base.head)
        pole_angle_rad = base.x_axis.angle(projected_pole_axis) if base.x_axis.cross(projected_pole_axis).angle(base.tail - base.head) >= 1 else -(base.x_axis.angle(projected_pole_axis))

        target_name = target.name
        ptarget_name = pole_target.name

        switch_context_mode('POSE')
        pose_bone = self.arm.pose.bones[bone.name]

        ik_prop = pose_bone.constraints.new('IK')
        ik_prop.name = bone.name + ".ik"
        ik_prop.target = self.arm
        ik_prop.subtarget = target_name
        ik_prop.pole_target = self.arm
        ik_prop.pole_subtarget = ptarget_name
        ik_prop.chain_count = chain_len
        ik_prop.pole_angle = pole_angle_rad

        switch_context_mode(d_mode)

    def select_edit_bone(self, target, s_bone=True, s_head=False, s_tail=False):
        target.select = s_bone
        target.select_head = s_head
        target.select_tail = s_tail

    def find_edit_bones_by_name(self, name):
        return [b for b in self.arm.data.edit_bones if b.name == name]

    def unselect_all_edit_bones(self):
        for b in self.arm.data.edit_bones:
            self.select_edit_bone(b, False, False, False)


"""
TO DO :
+ (Digitigrade)
+ (tail)
"""