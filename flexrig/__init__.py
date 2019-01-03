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

bl_info = {
    "name": "Flexrig",
    "author": "Nicolas Candia",
    "blender": (2, 73, 0),
    "version": (0, 1, 0),
    "location": "Tools > Flexrig",
    "description": "Various tools for working with motion capture animation",
    "warning": "",
    "support": 'TESTING',
    "category": "Animation",
}

if "bpy" in locals():
    import importlib
    importlib.reload(flexrig_ui)
else:
    import bpy
    from . import flexrig_ui

def register():
    bpy.utils.register_module(__name__)
    flexrig_ui.initSceneProperties()
    #flexrig_ui.register()
    print("Flexrig loaded.")

def unregister():
    bpy.utils.unregister_module(__name__)
    #flexrig_ui.unregister()
    print("Flexrig unloaded.")