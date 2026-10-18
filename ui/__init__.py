"""UI Panels for Material Instancer."""
import bpy
from .main_panel import MI_PT_MainPanel

classes = (
    MI_PT_MainPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except (RuntimeError, ValueError):
            pass
