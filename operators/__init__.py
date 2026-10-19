"""Operators for Material Instancer."""
import bpy
from .expose_parameter import (
    NPR_OT_ExposeNodeAsParameter,
    NPR_OT_UnexposeParameter,
    NPR_OT_CleanUnusedProperties,
    draw_npr_node_context_menu,
)
from .jump_to_custom_props import (
    MATERIAL_OT_JumpToCustomProps,
)

classes = (
    NPR_OT_ExposeNodeAsParameter,
    NPR_OT_UnexposeParameter,
    NPR_OT_CleanUnusedProperties,
    MATERIAL_OT_JumpToCustomProps,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    if hasattr(bpy.types, "NODE_MT_context_menu"):
        bpy.types.NODE_MT_context_menu.append(draw_npr_node_context_menu)

def unregister():
    if hasattr(bpy.types, "NODE_MT_context_menu"):
        try:
            bpy.types.NODE_MT_context_menu.remove(draw_npr_node_context_menu)
        except (ValueError, Exception):
            pass
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except (RuntimeError, ValueError):
            pass
