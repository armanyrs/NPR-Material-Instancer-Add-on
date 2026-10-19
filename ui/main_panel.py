"""
Shader Editor Sidebar (N-Panel > 'Material Instancer').
Simple, clean inspector to view exposed material parameters and jump to Object Custom Properties.
"""
import bpy
from ..core.parameter_manager import get_exposed_parameters_from_tree

class MI_PT_MainPanel(bpy.types.Panel):
    """Simple Sidebar Panel for Material Instancer in the Shader Editor"""
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Material Instancer'
    bl_label = "Material Instancer"

    @classmethod
    def poll(cls, context):
        sdata = getattr(context, "space_data", None)
        return sdata and getattr(sdata, "tree_type", "") == 'ShaderNodeTree'

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        if not obj or obj.type != 'MESH':
            layout.label(text="Select a Mesh Object", icon='OBJECT_DATA')
            return

        mat = obj.active_material
        if not mat or not mat.node_tree:
            layout.label(text=f"Object: {obj.name}", icon='OBJECT_DATAMODE')
            layout.label(text="No material on this object.", icon='INFO')
            return

        # Material Header
        box_mat = layout.box()
        box_mat.label(text=f"Material: {mat.name}", icon='MATERIAL')

        # Exposed Parameters List
        exposed = get_exposed_parameters_from_tree(mat.node_tree)

        box_params = layout.box()
        box_params.label(text=f"Exposed Parameters ({len(exposed)})", icon='PROPERTIES')

        if not exposed:
            col_tip = box_params.column(align=True)
            col_tip.label(text="Right-click any node >", icon='MOUSE_RMB')
            col_tip.label(text="'Convert to Parameter' to expose.", icon='PINNED')
        else:
            col_p = box_params.column(align=True)
            for attr_key, info in exposed.items():
                row = col_p.row(align=True)
                if attr_key in obj:
                    row.prop(obj, f'["{attr_key}"]', text=info['label'])
                else:
                    row.label(text=f"{info['label']} (Not on object)")
                # Quick unexpose button
                op_del = row.operator("npr.unexpose_parameter", text="", icon='X')
                op_del.property_key = attr_key

        # Unused / Dangling Custom Properties (if any)
        dangling_keys = [k for k in obj.keys() if k.startswith("mi_") and k not in exposed]
        if dangling_keys:
            layout.separator()
            box_unused = layout.box()
            row_u = box_unused.row(align=True)
            row_u.label(text=f"Unused Properties ({len(dangling_keys)})", icon='INFO')
            op_clean_all = row_u.operator("npr.clean_unused_properties", text="Clean All", icon='TRASH')
            op_clean_all.property_key = ""

            col_u = box_unused.column(align=True)
            for dk in dangling_keys:
                row_dk = col_u.row(align=True)
                row_dk.label(text=dk, icon='DOT')
                op_dk = row_dk.operator("npr.clean_unused_properties", text="", icon='X')
                op_dk.property_key = dk

        layout.separator()

        # Direct button to jump to Object > Custom Properties
        box_jump = layout.box()
        row_jump = box_jump.row(align=True)
        row_jump.scale_y = 1.3
        row_jump.operator("npr.jump_to_custom_props", text="Open Object > Custom Properties", icon='PROPERTIES')
