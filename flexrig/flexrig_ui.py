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
from . import flexrig
import json
import os

# Utils -----------------------------------------

def set_flexrig_profile_list(data):
    bpy.types.Scene.flexrig_active = bpy.props.EnumProperty(name="Profile", items=data)
    
def find_flexrig_active_profile(scene):
    profile_name = scene.flexrig_active
    for p in scene.flexrig_profiles:
        if p.name == profile_name:
            return p
    return None

def add_set_position_operator(row, mtype, mprop, mid = 0):
    cursor = row.operator("flexrig.set_position", icon="CURSOR", text="")
    cursor.member_id = mid
    cursor.member_type = mtype
    cursor.member_property = mprop

def add_del_member_operator(row, mtype, mid):
    op = row.operator("flexrig.del_member", icon="PANEL_CLOSE", emboss=False, text="")
    op.member_id = mid
    op.member_type = mtype

def add_mirror_member_operator(row, mtype, mid):
    op = row.operator("flexrig.mirror_position", text="Apply", icon="MOD_MIRROR")
    op.member_id = mid
    op.member_type = mtype

def add_reset_member_operator(row, mtype, mid = 0):
    op = row.operator("flexrig.reset_position", text="Reset position")
    op.member_id = mid
    op.member_type = mtype

def add_copy_member_operator(row, mtype, mid = 0):
    op = row.operator("flexrig.copy_member", icon="ORTHO", text="Duplicate")
    op.member_id = mid
    op.member_type = mtype

def on_profile_name_change(self, context):
    enum_data = []
    for d in context.scene.flexrig_profiles:
        enum_data.append((d["name"], d["name"], "Select " + d["name"] + "profile"))
        set_flexrig_profile_list(enum_data)
    context.scene.flexrig_active = self.name

# JSON Loader -----------------------------------

class FlexrigProfileIE:
    def __init__(self):
        script_path = bpy.utils.script_paths()
        
        for p in script_path:
            if os.path.isdir(p + "/addons/flexrig"):
                self.path = p + "/addons/flexrig/"
    
    def load(self, scene):
        filename = "flexrig_profiles.json"

        work = False
        try:
            raw_data = []

            with open(self.path + filename, 'r') as f:
                raw_data = json.load(f)
            
            self.to_blender(raw_data, scene)
            work = True
        except IOError:
            print("FlexRig : Could not open setting file in " + self.path)

        return work

    def save(self, scene):
        filename = "flexrig_profiles.json"
        bck_name = ".~" + filename

        if os.path.isfile(self.path + filename):
            os.rename(self.path + filename, self.path + bck_name)
        
        work = False
        try:
            if os.path.isfile(self.path + filename):
                os.remove(self.path + filename)

            with open(self.path + filename, 'w') as f:
                f.write(json.dumps(self.to_serializable(scene)))
            
            os.remove(self.path + bck_name)
            work = True
        except IOError:
            print("FlexRig : Could not save setting file in " + self.path)

            if os.path.isfile(self.path + bck_name):
                os.rename(self.path + bck_name, self.path + filename)

        return work

    def to_serializable(self, scene):
        out_data = []

        for profile in scene.flexrig_profiles:
            out_profile = {}

            out_profile["name"] = profile.name
            out_profile["chest"] = profile.chest.to_tuple()
            out_profile["rib"] = profile.rib.to_tuple()
            out_profile["tchest"] = profile.tchest.to_tuple()
            out_profile["control"] = profile.control

            out_profile["heads"] = []
            for h in profile.heads:
                out_profile["heads"].append({'suffix':h.suffix, 'neck':h.neck.to_tuple(), 'head':h.head.to_tuple()})

            out_profile["arms"] = []
            for h in profile.arms:
                out_profile["arms"].append({'suffix':h.suffix,
                    'upper':h.upper.to_tuple(), 'lower':h.lower.to_tuple(), 'wrist':h.wrist.to_tuple(),
                    'thumb':h.thumb.to_tuple(), 'hand':h.hand.to_tuple(), 'shoulder':h.shoulder, 'ik':h.ik
                })

            out_profile["legs"] = []
            for h in profile.legs:
                out_profile["legs"].append({'suffix':h.suffix,
                    'upper':h.upper.to_tuple(), 'lower':h.lower.to_tuple(), 'knee':h.knee.to_tuple(), 
                    'foot':h.foot.to_tuple(), 'hip':h.hip, 'ik':h.ik
                })

            out_data.append(out_profile)

        return out_data

    def to_blender(self, data, scene):
        profiles = scene.flexrig_profiles
        profiles.clear()

        enum_data = []

        for d in data:
            prop = profiles.add()
            prop.name = d["name"]
            prop.control = d["control"]
            prop.chest = d["chest"]
            prop.tchest = d["tchest"]
            prop.rib = d["rib"]

            for head in d["heads"]:
                h = prop.heads.add()
                h.suffix = head["suffix"]
                h.neck = mathutils.Vector(head["neck"])
                h.head = mathutils.Vector(head["head"])

            for arm in d["arms"]:
                a = prop.arms.add()
                a.suffix = arm["suffix"]
                a.upper = mathutils.Vector(arm["upper"])
                a.lower = mathutils.Vector(arm["lower"])
                a.wrist = mathutils.Vector(arm["wrist"])
                a.hand = mathutils.Vector(arm["hand"])
                a.thumb = mathutils.Vector(arm["thumb"])
                a.shoulder = arm["shoulder"]
                a.ik = arm["ik"]

            for leg in d["legs"]:
                lg = prop.legs.add()
                lg.suffix = leg["suffix"]
                lg.upper = mathutils.Vector(leg["upper"])
                lg.lower = mathutils.Vector(leg["lower"])
                lg.knee = mathutils.Vector(leg["knee"])
                lg.foot = mathutils.Vector(leg["foot"])
                lg.hip = leg["hip"]
                lg.ik = leg["ik"]

            enum_data.append((d["name"], d["name"], "Select " + d["name"] + "profile"))

        set_flexrig_profile_list(enum_data)

# Panels ----------------------------------------

class FlexrigPanel(bpy.types.Panel):
    bl_label = "FlexRig"
    bl_idname = "FLEXRIG_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "FlexRig"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        profile = find_flexrig_active_profile(scene)
        
        row = layout.row(align=True)
        row.prop(scene, "flexrig_active")
        row.operator("flexrig.del_profile", icon='ZOOMOUT', text="")
        row.operator("flexrig.add_profile", icon='ZOOMIN', text="")
        row.separator()

        if profile is not None:
            row = layout.row()
            row.prop(profile, "name", text="")
            row = layout.row()
            row.operator("flexrig.save_profile", icon="DISK_DRIVE", text="Save profile")

        row = layout.row()
        row.operator("flexrig.reset_profile", icon="PARTICLES", text="Reset to default")

class FlexrigLinkPanel(bpy.types.Panel):
    bl_label = "FlexRig Link"
    bl_idname = "FLEXRIG_LINK_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "FlexRig"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        
        row = layout.row()
        row.prop_search(scene.flexrig_link, "target_object", scene, "objects", icon='OBJECT_DATA', text="Object")
        row = layout.row()
        row.prop_search(scene.flexrig_link, "armature_object", scene, "objects", icon='ARMATURE_DATA', text="Armature")

        row = layout.row()
        row.operator("flexrig.link_to", text="Link armature to object", icon="LINK_AREA")

class FlexrigAmtPanel(bpy.types.Panel):
    bl_label = "FlexRig Armature"
    bl_idname = "FLEXRIG_AMT_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "FlexRig"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        profile = find_flexrig_active_profile(scene)
        
        row = layout.row(align=True)
        row.prop(scene, "flexrig_amt")
        row.separator()

        if profile is not None:
            row = layout.row()
            row.prop(profile, "control", text="Create control handle", toggle=True)

        row = layout.row()
        row.operator("flexrig.create_amt", icon="OUTLINER_OB_ARMATURE", text="Create armature")

class FlexrigHeadPanel(bpy.types.Panel):
    bl_label = "FlexRig Head(s)"
    bl_idname = "FLEXRIG_HEAD_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "FlexRig"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        profile = find_flexrig_active_profile(scene)
        head_id = 0

        if profile is None:
            return
            
        for head in profile.heads:
            box = layout.box()
            
            # Header
            icon_expand = 'TRIA_DOWN' if head.expand else 'TRIA_RIGHT'
            row = box.row()
            row.prop(head, "expand", icon=icon_expand, text="", emboss=False)
            subrow = row.split(percentage=0.2)
            subrow.label(text="Head.")
            subrow.prop(head, "suffix", text="")
            add_del_member_operator(row, 'heads', head_id)

            if head.expand:
                # Location
                box.separator()
                row = box.row(align=True)
                row.prop(head, "head", text="Head")
                add_set_position_operator(row, 'heads', 'head', head_id)
                row = box.row(align=True)
                row.prop(head, "neck", text="Neck")
                add_set_position_operator(row, 'heads', 'neck', head_id)

                # Command
                box.separator()
                row = box.row(align=True)
                row.prop(head, "mirror", toggle=True)
                add_mirror_member_operator(row, 'heads', head_id)
                row = box.row()
                add_reset_member_operator(row, 'heads', head_id)
                add_copy_member_operator(row, 'heads', head_id)

            head_id += 1

        row = layout.row()
        row.operator("flexrig.add_head", icon="ZOOMIN", text="Add head")

class FlexrigBodyPanel(bpy.types.Panel):
    bl_label = "FlexRig Body"
    bl_idname = "FLEXRIG_BODY_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "FlexRig"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        profile = find_flexrig_active_profile(scene)

        if profile is None:
            return

        box = layout.box()
        
        # Location
        row = box.row(align=True)
        row.prop(profile, "rib", text="Rib")
        add_set_position_operator(row, 'body', 'rib')

        row = box.row(align=True)
        row.prop(profile, "chest", text="Chest")
        add_set_position_operator(row, 'body', 'chest')

        row = box.row(align=True)
        row.prop(profile, "tchest", text="Top Chest")
        add_set_position_operator(row, 'body', 'tchest')

        # Command
        box.separator()
        row = box.row()
        add_reset_member_operator(row, 'body')

class FlexrigArmPanel(bpy.types.Panel):
    bl_label = "FlexRig Arm(s)"
    bl_idname = "FLEXRIG_ARM_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "FlexRig"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        profile = find_flexrig_active_profile(scene)
        arm_id = 0

        if profile is None:
            return

        for arm in profile.arms:
            box = layout.box()
            
            # Header
            icon_expand = 'TRIA_DOWN' if arm.expand else 'TRIA_RIGHT'
            row = box.row()
            row.prop(arm, "expand", icon=icon_expand, text="", emboss=False)
            subrow = row.split(percentage=0.2)
            subrow.label(text="Arm.")
            subrow.prop(arm, "suffix", text="")
            add_del_member_operator(row, 'arms', arm_id)

            if arm.expand:
                # Location
                box.separator()
                row = box.row(align=True)
                row.prop(arm, "upper", text="Upper Arm")
                add_set_position_operator(row, 'arms', 'upper', arm_id)
                row = box.row(align=True)
                row.prop(arm, "lower", text="(Lower Arm)")
                add_set_position_operator(row, 'arms', 'lower', arm_id)
                row = box.row(align=True)
                row.prop(arm, "wrist", text="Wrist")
                add_set_position_operator(row, 'arms', 'wrist', arm_id)
                row = box.row(align=True)
                row.prop(arm, "hand", text="(Hand)")
                add_set_position_operator(row, 'arms', 'hand', arm_id)
                row = box.row(align=True)
                row.prop(arm, "thumb", text="(Thumb)")
                add_set_position_operator(row, 'arms', 'thumb', arm_id)

                # Other
                box.separator()
                row = box.row()
                row.prop(arm, "shoulder", text="Create shoulder", toggle=True)
                row.prop(arm, "ik", text="Create IK", toggle=True)

                # Command
                box.separator()
                row = box.row(align=True)
                row.prop(arm, "mirror", toggle=True)
                add_mirror_member_operator(row, 'arms', arm_id)
                row = box.row()
                add_reset_member_operator(row, 'arms', arm_id)
                add_copy_member_operator(row, 'arms', arm_id)

            arm_id += 1

        row = layout.row()
        row.operator("flexrig.add_arm", icon="ZOOMIN", text="Add arm")

class FlexrigLegPanel(bpy.types.Panel):
    bl_label = "FlexRig Leg(s)"
    bl_idname = "FLEXRIG_LEG_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "FlexRig"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        profile = find_flexrig_active_profile(scene)
        leg_id = 0

        if profile is None:
            return

        for leg in profile.legs:
            box = layout.box()
            
            # Header
            icon_expand = 'TRIA_DOWN' if leg.expand else 'TRIA_RIGHT'
            row = box.row()
            row.prop(leg, "expand", icon=icon_expand, text="", emboss=False)
            subrow = row.split(percentage=0.2)
            subrow.label(text="Leg.")
            subrow.prop(leg, "suffix", text="")
            add_del_member_operator(row, 'legs', leg_id)

            if leg.expand:
                # Location
                box.separator()
                row = box.row(align=True)
                row.prop(leg, "upper", text="Upper Leg")
                add_set_position_operator(row, 'legs', 'upper', leg_id)
                row = box.row(align=True)
                row.prop(leg, "lower", text="Lower Leg")
                add_set_position_operator(row, 'legs', 'lower', leg_id)
                row = box.row(align=True)
                row.prop(leg, "knee", text="Heel")
                add_set_position_operator(row, 'legs', 'knee', leg_id)
                row = box.row(align=True)
                row.prop(leg, "foot", text="Foot")
                add_set_position_operator(row, 'legs', 'foot', leg_id)

                # Other
                box.separator()
                row = box.row()
                row.prop(leg, "hip", text="Create hip", toggle=True)
                row.prop(leg, "ik", text="Create IK", toggle=True)

                # Command
                box.separator()
                row = box.row(align=True)
                row.prop(leg, "mirror", toggle=True)
                add_mirror_member_operator(row, 'legs', leg_id)
                row = box.row()
                add_reset_member_operator(row, 'legs', leg_id)
                add_copy_member_operator(row, 'legs', leg_id)

            leg_id += 1

        row = layout.row()
        row.operator("flexrig.add_leg", icon="ZOOMIN", text="Add leg")

# Properties ------------------------------------

class FlexrigArmProperty(bpy.types.PropertyGroup):
    suffix = bpy.props.StringProperty(name="Arm suffix")

    upper = bpy.props.FloatVectorProperty(name="Upper arm", subtype='XYZ', size=3)
    lower = bpy.props.FloatVectorProperty(name="Lower arm", subtype='XYZ', size=3)
    wrist = bpy.props.FloatVectorProperty(name="Wrist", subtype='XYZ', size=3)
    thumb = bpy.props.FloatVectorProperty(name="Thumb", subtype='XYZ', size=3)
    hand = bpy.props.FloatVectorProperty(name="Hand", subtype='XYZ', size=3)

    shoulder = bpy.props.BoolProperty(name="Shoulder", default=True)
    ik = bpy.props.BoolProperty(name="Ik", default=False)

    mirror = bpy.props.BoolVectorProperty(name="Symmetry", subtype='XYZ')
    expand = bpy.props.BoolProperty(name="expand", default=False)

class FlexrigLegProperty(bpy.types.PropertyGroup):
    suffix = bpy.props.StringProperty(name="Leg suffix")

    upper = bpy.props.FloatVectorProperty(name="Upper leg", subtype='XYZ', size=3)
    lower = bpy.props.FloatVectorProperty(name="Lower leg", subtype='XYZ', size=3)
    knee = bpy.props.FloatVectorProperty(name="Knee", subtype='XYZ', size=3)
    foot = bpy.props.FloatVectorProperty(name="Foot", subtype='XYZ', size=3)

    hip = bpy.props.BoolProperty(name="hip", default=True)
    ik = bpy.props.BoolProperty(name="Ik", default=False)

    mirror = bpy.props.BoolVectorProperty(name="Symmetry", subtype='XYZ')
    expand = bpy.props.BoolProperty(name="expand", default=False)

class FlexrigHeadProperty(bpy.types.PropertyGroup):
    suffix = bpy.props.StringProperty(name="Head suffix")

    neck = bpy.props.FloatVectorProperty(name="Neck", subtype='XYZ', size=3)
    head = bpy.props.FloatVectorProperty(name="Head", subtype='XYZ', size=3)

    mirror = bpy.props.BoolVectorProperty(name="Symmetry", subtype='XYZ')
    expand = bpy.props.BoolProperty(name="expand", default=False)

class FlexrigProfileProperty(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name="Profile name", update=on_profile_name_change)

    rib = bpy.props.FloatVectorProperty(name="Rib", subtype='XYZ', size=3)
    chest = bpy.props.FloatVectorProperty(name="Chest", subtype='XYZ', size=3)
    tchest = bpy.props.FloatVectorProperty(name="Top chest", subtype='XYZ', size=3)
    control = bpy.props.BoolProperty(name="Controller", default=True)

    heads = bpy.props.CollectionProperty(type=FlexrigHeadProperty)
    arms = bpy.props.CollectionProperty(type=FlexrigArmProperty)
    legs = bpy.props.CollectionProperty(type=FlexrigLegProperty)

class FlexrigLinkProperty(bpy.types.PropertyGroup):
    armature_object = bpy.props.StringProperty(name="Armature object name")
    target_object = bpy.props.StringProperty(name="Target object name")

# Operators -------------------------------------

class FLEXRIG_OT_add_profile(bpy.types.Operator):
    bl_idname = "flexrig.add_profile"
    bl_label = "Add Flexrig profile"

    def execute(self, context):
        # Define name that not already existing
        i = 0
        is_exists = True
        while is_exists is True:
            profile_name = "New."  + str(i)
            is_exists = False
            for d in context.scene.flexrig_profiles:
                if d["name"] == profile_name:
                    is_exists = True
                    break
            i += 1

        # Add profile
        p = context.scene.flexrig_profiles.add()
        p.name = profile_name

        # Reload profile list
        enum_data = []
        for d in context.scene.flexrig_profiles:
            enum_data.append((d["name"], d["name"], "Select " + d["name"] + "profile"))
        set_flexrig_profile_list(enum_data)
        context.scene.flexrig_active = profile_name
        return {'FINISHED'}

class FLEXRIG_OT_del_profile(bpy.types.Operator):
    bl_idname = "flexrig.del_profile"
    bl_label = "Delete current Flexrig profile"

    def execute(self, context):
        # Remove profile
        i = 0
        if len(context.scene.flexrig_profiles) > 1:
            while i < len(context.scene.flexrig_profiles):
                if context.scene.flexrig_profiles[i].name == context.scene.flexrig_active:
                    context.scene.flexrig_profiles.remove(i)
                    break
                i += 1

            # Reload profile list
            enum_data = []
            for d in context.scene.flexrig_profiles:
                enum_data.append((d["name"], d["name"], "Select " + d["name"] + "profile"))
            set_flexrig_profile_list(enum_data)
            context.scene.flexrig_active = context.scene.flexrig_profiles[len(context.scene.flexrig_profiles) - 1].name
        return {'FINISHED'}

class FLEXRIG_OT_save_profile(bpy.types.Operator):
    bl_idname = "flexrig.save_profile"
    bl_label = "Save Flexrig profile"

    def execute(self, context):
        active_profile = context.scene.flexrig_active
        profileIE = FlexrigProfileIE()
        profileIE.save(context.scene)

        # Reload profile list
        enum_data = []
        for d in context.scene.flexrig_profiles:
            enum_data.append((d["name"], d["name"], "Select " + d["name"] + "profile"))
        set_flexrig_profile_list(enum_data)
        context.scene.flexrig_active = active_profile
        return {'FINISHED'}

class FLEXRIG_OT_reset_profile(bpy.types.Operator):
    bl_idname = "flexrig.reset_profile"
    bl_label = "Reset Flexrig profile to default"

    def execute(self, context):
        profileIE = FlexrigProfileIE()
        profileIE.load(context.scene)
        return {'FINISHED'}

class FLEXRIG_OT_set_profile_name(bpy.types.Operator):
    bl_idname = "flexrig.set_profile_name"
    bl_label = "Change Flexrig profile name"

    def execute(self, context):
        enum_data = []
        for d in context.scene.flexrig_profiles:
            enum_data.append((d["name"], d["name"], "Select " + d["name"] + "profile"))
        set_flexrig_profile_list(enum_data)
        return {'FINISHED'}

class FLEXRIG_OT_add_head(bpy.types.Operator):
    bl_idname = "flexrig.add_head"
    bl_label = "Add head to Flexrig"

    def execute(self, context):
        profile = find_flexrig_active_profile(context.scene)
        if profile is not None:
            profile.heads.add()
        return {'FINISHED'}

class FLEXRIG_OT_add_arm(bpy.types.Operator):
    bl_idname = "flexrig.add_arm"
    bl_label = "Add arm to Flexrig"

    def execute(self, context):
        profile = find_flexrig_active_profile(context.scene)
        if profile is not None:
            profile.arms.add()
        return {'FINISHED'}

class FLEXRIG_OT_add_leg(bpy.types.Operator):
    bl_idname = "flexrig.add_leg"
    bl_label = "Add leg to Flexrig"

    def execute(self, context):
        profile = find_flexrig_active_profile(context.scene)
        if profile is not None:
            profile.legs.add()
        return {'FINISHED'}

class FLEXRIG_OT_del_member(bpy.types.Operator):
    bl_idname = "flexrig.del_member"
    bl_label = "Remove flexrig member"

    member_type = bpy.props.StringProperty(default="body")
    member_id = bpy.props.IntProperty(default=0)

    def execute(self, context):
        profile = find_flexrig_active_profile(context.scene)
        members_list = getattr(profile, self.member_type)
        if members_list is not None:
            members_list.remove(self.member_id)
        return {'FINISHED'}

class FLEXRIG_OT_set_position(bpy.types.Operator):
    bl_idname = "flexrig.set_position"
    bl_label = "Set position with 3D cursor"

    member_type = bpy.props.StringProperty(default="body")
    member_id = bpy.props.IntProperty(default=0)
    member_property = bpy.props.StringProperty(default="rib")

    def execute(self, context):
        profile = find_flexrig_active_profile(context.scene)

        if self.member_type == 'body':
            position_to_update = getattr(profile, self.member_property)
        else:
            position_to_update = getattr(getattr(profile, self.member_type)[self.member_id], self.member_property)

        view3D = None
        for area in context.screen.areas: 
            if area.type == 'VIEW_3D':
                view3D = area.spaces[0]

        position_to_update.x = view3D.cursor_location.x
        position_to_update.y = view3D.cursor_location.y
        position_to_update.z = view3D.cursor_location.z

        return {'FINISHED'}

class FLEXRIG_OT_mirror_position(bpy.types.Operator):
    bl_idname = "flexrig.mirror_position"
    bl_label = "Mirror position of member in axis"

    member_type = bpy.props.StringProperty(default="body")
    member_id = bpy.props.IntProperty(default=0)

    def execute(self, context):
        profile = find_flexrig_active_profile(context.scene)
        member = getattr(profile, self.member_type)[self.member_id]

        x_factor = -1 if member.mirror[0] is True else 1
        y_factor = -1 if member.mirror[1] is True else 1
        z_factor = -1 if member.mirror[2] is True else 1

        if self.member_type == 'heads':
            self.calc_symmetry(member.head, x_factor, y_factor, z_factor)
            self.calc_symmetry(member.neck, x_factor, y_factor, z_factor)
        elif self.member_type == 'arms':
            self.calc_symmetry(member.upper, x_factor, y_factor, z_factor)
            self.calc_symmetry(member.lower, x_factor, y_factor, z_factor)
            self.calc_symmetry(member.wrist, x_factor, y_factor, z_factor)
            self.calc_symmetry(member.hand, x_factor, y_factor, z_factor)
            self.calc_symmetry(member.thumb, x_factor, y_factor, z_factor)
        elif self.member_type == 'legs':
            self.calc_symmetry(member.upper, x_factor, y_factor, z_factor)
            self.calc_symmetry(member.lower, x_factor, y_factor, z_factor)
            self.calc_symmetry(member.knee, x_factor, y_factor, z_factor)
            self.calc_symmetry(member.foot, x_factor, y_factor, z_factor)

        member.mirror = [False, False, False]
        return {'FINISHED'}

    def calc_symmetry(self, vector, x_factor, y_factor, z_factor):
        vector.x *= x_factor
        vector.y *= y_factor
        vector.z *= z_factor

class FLEXRIG_OT_reset_position(bpy.types.Operator):
    bl_idname = "flexrig.reset_position"
    bl_label = "Reset position of member to origin"

    member_type = bpy.props.StringProperty(default="body")
    member_id = bpy.props.IntProperty(default=0)

    def execute(self, context):
        profile = find_flexrig_active_profile(context.scene)

        if self.member_type != 'body':
            member = getattr(profile, self.member_type)[self.member_id]

        if self.member_type == 'heads':
            self.reset_position(member.head)
            self.reset_position(member.neck)
        elif self.member_type == 'arms':
            self.reset_position(member.upper)
            self.reset_position(member.lower)
            self.reset_position(member.wrist)
            self.reset_position(member.hand)
            self.reset_position(member.thumb)
        elif self.member_type == 'legs':
            self.reset_position(member.upper)
            self.reset_position(member.lower)
            self.reset_position(member.knee)
            self.reset_position(member.foot)
        elif self.member_type == 'body':
            self.reset_position(profile.rib)
            self.reset_position(profile.chest)
            self.reset_position(profile.tchest)

        return {'FINISHED'}

    def reset_position(self, vector):
        vector.x = 0
        vector.y = 0
        vector.z = 0

class FLEXRIG_OT_copy_member(bpy.types.Operator):
    bl_idname = "flexrig.copy_member"
    bl_label = "Duplicate member"

    member_type = bpy.props.StringProperty(default="body")
    member_id = bpy.props.IntProperty(default=0)

    def execute(self, context):
        profile = find_flexrig_active_profile(context.scene)

        members_list = getattr(profile, self.member_type)
        new_member = members_list.add()
        member = members_list[self.member_id]

        if self.member_type == 'heads':
            new_member.head = member.head.copy()
            new_member.neck = member.neck.copy()
        elif self.member_type == 'arms':
            new_member.upper = member.upper.copy()
            new_member.lower = member.lower.copy()
            new_member.wrist = member.wrist.copy()
            new_member.hand = member.hand.copy()
            new_member.thumb = member.thumb.copy()
            new_member.shoulder = member.shoulder
            new_member.ik = member.ik
        elif self.member_type == 'legs':
            new_member.upper = member.upper.copy()
            new_member.lower = member.lower.copy()
            new_member.knee = member.knee.copy()
            new_member.foot = member.foot.copy()
            new_member.hip = member.hip
            new_member.ik = member.ik

        new_member.expand = True
        new_member.suffix = member.suffix
        return {'FINISHED'}

class FLEXRIG_OT_link_to(bpy.types.Operator):
    bl_idname = "flexrig.link_to"
    bl_label = "Link armature to object"

    def execute(self, context):
        if context.scene.flexrig_link.armature_object not in bpy.data.objects:
            return {'CANCELED'}
        if context.scene.flexrig_link.target_object not in bpy.data.objects:
            return {'CANCELED'}

        flexrig.Flexrig.link_to_object(context.scene.flexrig_link.armature_object, context.scene.flexrig_link.target_object)
        return {'FINISHED'}

class FLEXRIG_OT_create_amt(bpy.types.Operator):
    bl_idname = "flexrig.create_amt"
    bl_label = "Create flexrig armature"

    def execute(self, context):
        profile = find_flexrig_active_profile(context.scene)
        amt = flexrig.Flexrig(context.scene.flexrig_amt)
        amt.create_chest(profile.rib, profile.chest, profile.tchest)

        for head in profile.heads:
            amt.create_head(head.suffix, head.neck, head.head)
        for arm in profile.arms:
            hand = arm.hand if arm.hand.x != 0.0 or arm.hand.y != 0.0 or arm.hand.z != 0.0 else None
            thumb = arm.thumb if hand is not None and (arm.thumb.x != 0.0 or arm.thumb.y != 0.0 or arm.thumb.z != 0.0) else None
            amt.create_arm(arm.suffix, arm.upper, arm.lower, arm.wrist, arm.shoulder, arm.ik, hand, thumb)
        for leg in profile.legs:
            amt.create_leg(leg.suffix, leg.upper, leg.lower, leg.knee, leg.foot, leg.hip, leg.ik)

        amt.create_ik_controller(profile.control)
        return {'FINISHED'}

class FLEXRIG_OT_init(bpy.types.Operator):
    bl_idname = "flexrig.init_opt"
    bl_label = "Initialize Flexrig"

    def __init__(self):
        print("Flexrig : Plugin is loaded ... loading profile")

    def __del__(self):
        print("Flexrig : done")

    def excute(self, context):
        p_loader = FlexrigProfileIE()

        # If profile file isn't loaded create profile to not let empty enum
        if p_loader.load(context.scene) is False:
            bpy.ops.flexrig.add_profile()

        return {'FINISHED'}

    def invoke(self, context, event):
        self.execute()
        return {'FINISHED'}

# Initialization --------------------------------

def initSceneProperties():
    scene = bpy.types.Scene
    scene.flexrig_active = bpy.props.EnumProperty(name="Profile", items={})
    scene.flexrig_link = bpy.props.PointerProperty(type=FlexrigLinkProperty)
    scene.flexrig_amt = bpy.props.StringProperty(name="Armature name", default="Flexrig.Armature")
    scene.flexrig_profiles = bpy.props.CollectionProperty(type=FlexrigProfileProperty)

    # bpy.ops.flexrig.init_opt('INVOKE_DEFAULT')

"""def register():
    # Properties
    bpy.utils.register_class(FlexrigArmProperty)
    bpy.utils.register_class(FlexrigLegProperty)
    bpy.utils.register_class(FlexrigHeadProperty)
    bpy.utils.register_class(FlexrigProfileProperty)
    bpy.utils.register_class(FlexrigLinkProperty)

    # Panels
    bpy.utils.register_class(FlexrigPanel)
    bpy.utils.register_class(FlexrigLinkPanel)
    bpy.utils.register_class(FlexrigAmtPanel)
    bpy.utils.register_class(FlexrigHeadPanel)
    bpy.utils.register_class(FlexrigBodyPanel)
    bpy.utils.register_class(FlexrigArmPanel)
    bpy.utils.register_class(FlexrigLegPanel)

    # Operator
    bpy.utils.register_class(FLEXRIG_OT_add_profile)
    bpy.utils.register_class(FLEXRIG_OT_del_profile)
    bpy.utils.register_class(FLEXRIG_OT_save_profile)
    bpy.utils.register_class(FLEXRIG_OT_reset_profile)
    bpy.utils.register_class(FLEXRIG_OT_set_profile_name)
    bpy.utils.register_class(FLEXRIG_OT_add_head)
    bpy.utils.register_class(FLEXRIG_OT_add_arm)
    bpy.utils.register_class(FLEXRIG_OT_add_leg)
    bpy.utils.register_class(FLEXRIG_OT_del_member)
    bpy.utils.register_class(FLEXRIG_OT_set_position)
    bpy.utils.register_class(FLEXRIG_OT_del_member)
    bpy.utils.register_class(FLEXRIG_OT_mirror_position)
    bpy.utils.register_class(FLEXRIG_OT_reset_position)
    bpy.utils.register_class(FLEXRIG_OT_copy_member)
    bpy.utils.register_class(FLEXRIG_OT_del_member)
    bpy.utils.register_class(FLEXRIG_OT_link_to)
    bpy.utils.register_class(FLEXRIG_OT_create_amt)
    bpy.utils.register_class(FLEXRIG_OT_init)

    initSceneProperties()

def unregister():
    # Properties
    bpy.utils.unregister_class(FlexrigArmProperty)
    bpy.utils.unregister_class(FlexrigLegProperty)
    bpy.utils.unregister_class(FlexrigHeadProperty)
    bpy.utils.unregister_class(FlexrigProfileProperty)
    bpy.utils.unregister_class(FlexrigLinkProperty)

    # Panels
    bpy.utils.unregister_class(FlexrigPanel)
    bpy.utils.unregister_class(FlexrigLinkPanel)
    bpy.utils.unregister_class(FlexrigAmtPanel)
    bpy.utils.unregister_class(FlexrigHeadPanel)
    bpy.utils.unregister_class(FlexrigBodyPanel)
    bpy.utils.unregister_class(FlexrigArmPanel)
    bpy.utils.unregister_class(FlexrigLegPanel)

    # Operator
    bpy.utils.unregister_class(FLEXRIG_OT_add_profile)
    bpy.utils.unregister_class(FLEXRIG_OT_del_profile)
    bpy.utils.unregister_class(FLEXRIG_OT_save_profile)
    bpy.utils.unregister_class(FLEXRIG_OT_reset_profile)
    bpy.utils.unregister_class(FLEXRIG_OT_set_profile_name)
    bpy.utils.unregister_class(FLEXRIG_OT_add_head)
    bpy.utils.unregister_class(FLEXRIG_OT_add_arm)
    bpy.utils.unregister_class(FLEXRIG_OT_add_leg)
    bpy.utils.unregister_class(FLEXRIG_OT_del_member)
    bpy.utils.unregister_class(FLEXRIG_OT_set_position)
    bpy.utils.unregister_class(FLEXRIG_OT_del_member)
    bpy.utils.unregister_class(FLEXRIG_OT_mirror_position)
    bpy.utils.unregister_class(FLEXRIG_OT_reset_position)
    bpy.utils.unregister_class(FLEXRIG_OT_copy_member)
    bpy.utils.unregister_class(FLEXRIG_OT_del_member)
    bpy.utils.unregister_class(FLEXRIG_OT_link_to)
    bpy.utils.unregister_class(FLEXRIG_OT_create_amt)
    bpy.utils.unregister_class(FLEXRIG_OT_init)
"""