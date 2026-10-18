"""
Operators & Context Menu for Unreal-Style 'Convert to Parameter' (Expose).
Allows right-clicking on any shader node in the Shader Editor to expose
its sockets as instance-driven parameters with clean, intuitive naming.
"""
import bpy
import re
from ..core.parameter_manager import expose_socket_as_parameter, unexpose_parameter, get_socket_default_value

def _clean_socket_name(sock_name, node):
    """Generates an intuitive parameter name without unnecessary node type clutter."""
    if not sock_name:
        return node.label or node.name

    s = sock_name.strip()
    
    # Common self-explanatory sockets across PBR and shading nodes
    common_descriptive = {
        'Base Color', 'Roughness', 'Metallic', 'Specular IOR Level', 'Specular Tint',
        'Anisotropic', 'Anisotropic Rotation', 'Sheen', 'Sheen Tint', 'Clearcoat',
        'Clearcoat Roughness', 'IOR', 'Transmission Weight', 'Alpha', 'Normal',
        'Emission Color', 'Emission Strength', 'Subsurface Weight', 'Subsurface Radius',
        'Subsurface Scale', 'Displacement', 'Weight', 'Fac', 'Color'
    }

    # If the user gave the node a custom label, prioritize it
    if node.label and node.label.strip():
        if s in ('Color', 'Fac', 'Value', 'Vector'):
            return node.label.strip()
        return f"{node.label.strip()} {s}"

    # If socket name is already descriptive, use it directly
    if s in common_descriptive and s not in ('Color', 'Fac', 'Value', 'Vector'):
        return s

    # Handle procedural/texture nodes cleanly
    node_type_clean = node.type.replace('TEX_', '').replace('BSDF_', '').replace('_', ' ').title()
    if any(tex_name in node_type_clean for tex_name in ('Noise', 'Voronoi', 'Musgrave', 'Wave', 'Gradient', 'Magic', 'Checker')):
        if s in ('Scale', 'Detail', 'Roughness', 'Distortion', 'Lacunarity', 'Dimension'):
            return f"{node_type_clean} {s}"
        if s in ('Color', 'Fac'):
            return f"{node_type_clean} Color" if s == 'Color' else f"{node_type_clean} Fac"

    # Default fallback: socket name
    return s if s not in ('Fac', 'Value') else f"{node_type_clean} Factor"

def _sanitize_key(name):
    """Sanitizes name to mi_key without hardcoded npr_ prefix or node duplication."""
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower().strip())
    clean = clean.strip('_')
    clean = re.sub(r'_+', '_', clean)
    if not clean.startswith("mi_"):
        clean = f"mi_{clean}"
    return clean

def get_active_shader_node(context):
    """Finds the currently active node in Shader Editor or active material."""
    node = getattr(context, "active_node", None)
    if node:
        return node
    sdata = getattr(context, "space_data", None)
    if sdata and hasattr(sdata, "edit_tree") and sdata.edit_tree:
        return sdata.edit_tree.nodes.active
    # Fallback to active material on active object
    obj = getattr(context, "active_object", None)
    if obj and getattr(obj, "active_material", None) and obj.active_material.node_tree:
        return obj.active_material.node_tree.nodes.active
    # Fallback to Master Material
    mat = bpy.data.materials.get("M_Master_NPR") or bpy.data.materials.get("M_Master_Material")
    if mat and mat.node_tree:
        return mat.node_tree.nodes.active
    return None

def get_node_input_sockets_enum(self, context):
    """Dynamic EnumProperty callback listing all input sockets of the active node."""
    node = get_active_shader_node(context)
    items = []
    if node and hasattr(node, "inputs"):
        for i, sock in enumerate(node.inputs):
            if sock.enabled:
                icon = 'COLOR' if sock.type in ('RGBA', 'VECTOR') else 'VALUE'
                label = f"{sock.name} ({sock.type})"
                items.append((sock.identifier, label, f"Expose socket: {sock.name}", icon, i))
    if not items:
        items.append(("NONE", "No inputs available", "", 'CANCEL', 0))
    return items

class NPR_OT_ExposeNodeAsParameter(bpy.types.Operator):
    """Exposes an input socket of this node as an Unreal-style Material Instance parameter"""
    bl_idname = "npr.expose_node_as_parameter"
    bl_label = "Convert to Parameter (Expose)"
    bl_description = "Exposes an input socket of this shader node as an Unreal-style Material Instance parameter"
    bl_options = {'REGISTER', 'UNDO'}

    param_name: bpy.props.StringProperty(
        name="Parameter Name",
        description="Display name for the parameter in the Inspector",
        default="New Parameter"
    )
    
    target_socket_id: bpy.props.EnumProperty(
        name="Target Socket",
        description="Select which input socket of this node to expose",
        items=get_node_input_sockets_enum
    )
    
    property_key: bpy.props.StringProperty(
        name="Custom Property Key",
        description="Internal attribute identifier on objects (e.g., mi_base_color)",
        default="mi_param"
    )

    @classmethod
    def poll(cls, context):
        node = get_active_shader_node(context)
        return node is not None and hasattr(node, "inputs") and len(node.inputs) > 0

    def invoke(self, context, event):
        node = get_active_shader_node(context)
        if not node:
            self.report({'WARNING'}, "No active node selected.")
            return {'CANCELLED'}

        # Auto-suggest clean parameter name
        first_sock = node.inputs[0] if len(node.inputs) > 0 else None
        sock_name = first_sock.name if first_sock else ""
        suggested_name = _clean_socket_name(sock_name, node)
            
        self.param_name = suggested_name
        self.property_key = _sanitize_key(suggested_name)

        return context.window_manager.invoke_props_dialog(self, width=380)

    def draw(self, context):
        layout = self.layout
        node = get_active_shader_node(context)
        
        box = layout.box()
        box.label(text=f"Target Node: {node.name if node else 'None'}", icon='NODETREE')
        
        col = box.column(align=True)
        col.prop(self, "target_socket_id", text="Socket")
        col.separator()
        col.prop(self, "param_name", text="Param Name")
        col.prop(self, "property_key", text="Property Key")

    def execute(self, context):
        node = get_active_shader_node(context)
        if not node:
            self.report({'ERROR'}, "No active node found.")
            return {'CANCELLED'}

        # Find target socket by identifier or name
        target_sock = None
        for sock in node.inputs:
            if sock.identifier == self.target_socket_id or sock.name == self.target_socket_id:
                target_sock = sock
                break
        if not target_sock and len(node.inputs) > 0:
            target_sock = node.inputs[0]

        if not target_sock:
            self.report({'ERROR'}, "Selected socket is invalid.")
            return {'CANCELLED'}

        # Determine node tree
        sdata = getattr(context, "space_data", None)
        node_tree = getattr(sdata, "edit_tree", None) if sdata else None
        if not node_tree:
            obj = getattr(context, "active_object", None)
            if obj and getattr(obj, "active_material", None) and obj.active_material.node_tree:
                node_tree = obj.active_material.node_tree
            elif hasattr(node, "id_data") and hasattr(node.id_data, "node_tree"):
                node_tree = node.id_data.node_tree

        if not node_tree:
            self.report({'ERROR'}, "Could not determine active shader node tree.")
            return {'CANCELLED'}

        # Ensure property key starts with mi_
        prop_key = _sanitize_key(self.property_key or self.param_name)

        # Extract current default value from socket
        default_val = get_socket_default_value(target_sock)

        # Wire Attribute node
        attr_node, msg = expose_socket_as_parameter(
            node_tree=node_tree,
            target_node=node,
            target_socket=target_sock,
            param_name=self.param_name,
            prop_key=prop_key
        )

        # Invalidate / set object custom property so viewport reflects the value immediately
        if context.active_object:
            context.active_object[prop_key] = default_val

        # Add to scene registry of exposed parameters
        scene_props = getattr(context.scene, "npr_scene_props", None)
        if scene_props:
            entry = scene_props.exposed_params.add()
            entry.param_name = self.param_name
            entry.property_key = prop_key
            entry.param_type = 'COLOR' if target_sock.type in ('RGBA', 'VECTOR') else 'FLOAT'

        self.report({'INFO'}, f"Successfully exposed '{self.param_name}' as parameter [{prop_key}]!")
        return {'FINISHED'}

class NPR_OT_UnexposeParameter(bpy.types.Operator):
    """Removes an exposed attribute parameter from the Master Material"""
    bl_idname = "npr.unexpose_parameter"
    bl_label = "Unexpose Parameter"
    bl_options = {'REGISTER', 'UNDO'}

    property_key: bpy.props.StringProperty(name="Property Key")

    def execute(self, context):
        sdata = getattr(context, "space_data", None)
        node_tree = getattr(sdata, "edit_tree", None) if sdata else None
        if not node_tree and context.active_object and context.active_object.active_material:
            node_tree = context.active_object.active_material.node_tree

        if not node_tree:
            self.report({'ERROR'}, "Active node tree not found.")
            return {'CANCELLED'}

        success, msg = unexpose_parameter(node_tree, self.property_key)
        if success:
            scene_props = getattr(context.scene, "npr_scene_props", None)
            if scene_props:
                for idx, item in enumerate(scene_props.exposed_params):
                    if item.property_key == self.property_key:
                        scene_props.exposed_params.remove(idx)
                        break

            self.report({'INFO'}, msg)
            return {'FINISHED'}
        self.report({'WARNING'}, msg)
        return {'CANCELLED'}

def draw_npr_node_context_menu(self, context):
    """Draws 'Convert to Parameter' inside Shader Editor's right-click context menu."""
    sdata = getattr(context, "space_data", None)
    if not sdata or getattr(sdata, "tree_type", "") != 'ShaderNodeTree':
        return

    node = get_active_shader_node(context)
    if not node or not hasattr(node, "inputs") or len(node.inputs) == 0:
        return

    layout = self.layout
    layout.separator()
    layout.operator_context = 'INVOKE_DEFAULT'
    layout.operator(
        "npr.expose_node_as_parameter",
        text="Convert to Parameter (Expose)",
        icon='PINNED'
    )
