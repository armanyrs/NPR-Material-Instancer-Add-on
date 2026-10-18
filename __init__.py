"""
Universal Material Instancer Add-on for Blender.
Simple, focused tool:
1. Right-click any shader node socket > 'Convert to Parameter (Expose)'
2. Edit parameters live in Shader Editor sidebar or jump to Object > Custom Properties
"""

bl_info = {
    "name": "Universal Material Instancer",
    "author": "Armany Saputra",
    "version": (1, 3, 0),
    "blender": (3, 6, 0),
    "location": "Shader Editor > Sidebar (N-Panel) > Material Instancer",
    "description": "Expose any shader node socket as an object custom property with 0ms compilation",
    "category": "Material",
    "doc_url": "https://github.com/armanyrs/NPR-Material-Instancer-Add-on",
    "tracker_url": "https://github.com/armanyrs/NPR-Material-Instancer-Add-on/issues",
}

import bpy

if "properties" in locals():
    import importlib
    importlib.reload(utils)
    importlib.reload(core)
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(ui)
else:
    from . import utils
    from . import core
    from . import properties
    from . import operators
    from . import ui

def register():
    properties.register()
    operators.register()
    ui.register()

def unregister():
    ui.unregister()
    operators.unregister()
    properties.unregister()

if __name__ == "__main__":
    register()
