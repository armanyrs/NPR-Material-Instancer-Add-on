"""
Operator to switch the Properties editor directly to the Object tab (Custom Properties).
"""
import bpy

class MATERIAL_OT_JumpToCustomProps(bpy.types.Operator):
    """Switches the Properties editor to the Object tab to view and manage Custom Properties"""
    bl_idname = "npr.jump_to_custom_props"
    bl_label = "Open Object Custom Properties"
    bl_description = "Switches the Properties editor to the Object tab to view and manage Custom Properties"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        found = False
        if context.screen:
            for area in context.screen.areas:
                if area.type == 'PROPERTIES':
                    for space in area.spaces:
                        if space.type == 'PROPERTIES':
                            space.context = 'OBJECT'
                            found = True
                            
        if found:
            self.report({'INFO'}, "Switched Properties Editor to Object > Custom Properties.")
        else:
            self.report({'INFO'}, "Object Custom Properties are active on selected object.")
        return {'FINISHED'}
