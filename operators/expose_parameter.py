"""
Operators & Context Menu for Unreal-Style 'Convert to Parameter' (Expose).
Allows right-clicking on any shader node in the Shader Editor to expose
its sockets as instance-driven parameters with clean, intuitive naming.
"""
import bpy
import re
from ..core.parameter_manager import (
    expose_socket_as_parameter,
    unexpose_parameter,
    get_socket_default_value,
    cleanup_custom_property_from_objects,
    purge_all_unused_properties,
    configure_custom_property_on_object,
)

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

def _format_property_key(name):
    """Formats param_name to mi_key with spaces converted to underscores, preserving mi_ prefix."""
    if not name or not name.strip():
        return ""
    clean = name.strip().replace(" ", "_")
    if not clean.lower().startswith("mi_"):
        clean = f"mi_{clean.lower()}"
    else:
        clean = clean.lower()
    return clean

_is_syncing_param_key = False

def _on_param_name_update(self, context):
    global _is_syncing_param_key
    if _is_syncing_param_key:
        return
    # Auto-sync property_key with mi_ prefix unless user has manually overridden it
    if not self.is_custom_key:
        _is_syncing_param_key = True
        try:
            self.property_key = _format_property_key(self.param_name)
        finally:
            _is_syncing_param_key = False

def _on_property_key_update(self, context):
    global _is_syncing_param_key
    if _is_syncing_param_key:
        return
    # Automatically convert any spaces in property_key to underscores
    if " " in self.property_key:
        _is_syncing_param_key = True
        try:
            self.property_key = self.property_key.replace(" ", "_")
        finally:
            _is_syncing_param_key = False

    auto_val = _format_property_key(self.param_name)
    # If the user clears the property_key or matches auto_val, resume auto-sync
    if not self.property_key or self.property_key == auto_val:
        self.is_custom_key = False
        if not self.property_key and self.param_name:
            _is_syncing_param_key = True
            try:
                self.property_key = auto_val
            finally:
                _is_syncing_param_key = False
    else:
        self.is_custom_key = True

def get_target_node_tree(context, node=None):
    """Finds the active shader node tree being edited."""
    sdata = getattr(context, "space_data", None)
    if sdata and getattr(sdata, "tree_type", "") == 'ShaderNodeTree' and getattr(sdata, "edit_tree", None):
        return sdata.edit_tree
    if node and hasattr(node, "id_data"):
        if isinstance(node.id_data, bpy.types.Material) and node.id_data.node_tree:
            return node.id_data.node_tree
        if hasattr(node.id_data, "node_tree"):
            return node.id_data.node_tree
    obj = getattr(context, "active_object", None)
    if obj and getattr(obj, "active_material", None) and obj.active_material.node_tree:
        return obj.active_material.node_tree
    mat = bpy.data.materials.get("M_Master_NPR") or bpy.data.materials.get("M_Master_Material")
    if mat and mat.node_tree:
        return mat.node_tree
    return None

def get_existing_parameters_in_tree(node_tree):
    """
    Returns (names, keys) sets of existing parameters in the given shader node tree.
    Names are taken from node.label or node.attribute_name.
    Keys are taken from node.attribute_name.
    """
    names = []
    keys = []
    if not node_tree or not hasattr(node_tree, "nodes"):
        return names, keys
    for n in node_tree.nodes:
        if n.type == 'ATTRIBUTE' and getattr(n, "attribute_type", "") == 'OBJECT':
            label = (n.label or n.attribute_name or "").strip()
            if label:
                names.append(label)
            k = getattr(n, "attribute_name", "").strip()
            if k:
                keys.append(k)
    return names, keys

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
        name="Param Name",
        description="Display name for the parameter in the Inspector",
        default="",
        options={'SKIP_SAVE'},
        update=_on_param_name_update
    )
    
    target_socket_id: bpy.props.EnumProperty(
        name="Target Socket",
        description="Select which input socket of this node to expose",
        items=get_node_input_sockets_enum
    )
    
    property_key: bpy.props.StringProperty(
        name="Property Key",
        description="Internal attribute identifier on objects (e.g., Base_Color or custom key)",
        default="",
        options={'SKIP_SAVE'},
        update=_on_property_key_update
    )

    is_custom_key: bpy.props.BoolProperty(
        name="Is Custom Key",
        default=False,
        options={'SKIP_SAVE'}
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

        # Reset fields so Param Name starts empty every time
        self.is_custom_key = False
        self.param_name = ""
        self.property_key = ""

        # Default to the first enabled socket if available
        for sock in node.inputs:
            if sock.enabled:
                self.target_socket_id = sock.identifier
                break

        return context.window_manager.invoke_props_dialog(self, width=380)

    def check(self, context):
        # Enable live redraw of the dialog as user types
        return True

    def draw(self, context):
        layout = self.layout
        node = get_active_shader_node(context)
        node_tree = get_target_node_tree(context, node)
        
        box = layout.box()
        box.label(text=f"Target Node: {node.name if node else 'None'}", icon='NODETREE')
        
        col = box.column(align=True)
        col.prop(self, "target_socket_id", text="Socket")
        col.separator()
        col.prop(self, "param_name", text="Param Name")
        col.prop(self, "property_key", text="Property Key")

        # Interactive live validation warning inside dialog
        param_clean = self.param_name.strip()
        if not param_clean:
            col.separator()
            alert_row = col.row()
            alert_row.alert = True
            alert_row.label(text="* Param Name is required (cannot be empty)!", icon='ERROR')
        elif node_tree:
            existing_names, existing_keys = get_existing_parameters_in_tree(node_tree)
            if any(param_clean.lower() == name.lower() for name in existing_names):
                col.separator()
                alert_row = col.row()
                alert_row.alert = True
                alert_row.label(text=f"* Param Name '{param_clean}' already exists in this material!", icon='ERROR')
            else:
                prop_key_clean = (self.property_key.strip() if self.property_key.strip() else _format_property_key(param_clean)).replace(" ", "_")
                if any(prop_key_clean.lower() == k.lower() for k in existing_keys):
                    col.separator()
                    alert_row = col.row()
                    alert_row.alert = True
                    alert_row.label(text=f"* Property Key '{prop_key_clean}' already exists in this material!", icon='ERROR')

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
        node_tree = get_target_node_tree(context, node)
        if not node_tree:
            self.report({'ERROR'}, "Could not determine active shader node tree.")
            return {'CANCELLED'}

        # 1. Validation: Param Name cannot be empty
        param_clean = self.param_name.strip()
        if not param_clean:
            self.report({'WARNING'}, "Param Name is required and cannot be empty!")
            return {'CANCELLED'}

        # 2. Validation: Param Name cannot be duplicate on the same material
        existing_names, existing_keys = get_existing_parameters_in_tree(node_tree)
        if any(param_clean.lower() == name.lower() for name in existing_names):
            self.report({'WARNING'}, f"Param Name '{param_clean}' already exists in this material! Please enter a unique name.")
            return {'CANCELLED'}

        # 3. Property Key: user override or auto-generated with mi_ prefix, spaces replaced with '_'
        prop_key_clean = (self.property_key.strip() if self.property_key.strip() else _format_property_key(param_clean)).replace(" ", "_")

        # 4. Validation: Property Key cannot be duplicate on the same material
        if any(prop_key_clean.lower() == k.lower() for k in existing_keys):
            self.report({'WARNING'}, f"Property Key '{prop_key_clean}' already exists in this material! Please use a unique property key.")
            return {'CANCELLED'}

        # Extract current initial value from socket BEFORE linking
        default_val = get_socket_default_value(target_sock)

        # Wire Attribute node
        attr_node, msg = expose_socket_as_parameter(
            node_tree=node_tree,
            target_node=node,
            target_socket=target_sock,
            param_name=param_clean,
            prop_key=prop_key_clean
        )

        # Configure custom property on target objects with exact initial value and UI metadata (default, min, max, subtype)
        target_objs = set()
        if context.active_object:
            target_objs.add(context.active_object)
        for sel in getattr(context, "selected_objects", []):
            target_objs.add(sel)
        for o in bpy.data.objects:
            if hasattr(o, "material_slots") and any(s.material and s.material.node_tree == node_tree for s in o.material_slots):
                target_objs.add(o)
            elif hasattr(o, "data") and hasattr(o.data, "materials") and any(m and m.node_tree == node_tree for m in o.data.materials):
                target_objs.add(o)

        for o in target_objs:
            configure_custom_property_on_object(
                obj=o,
                prop_key=prop_key_clean,
                val=default_val,
                socket=target_sock,
                description=f"Material Instance: {param_clean}"
            )

        # Force dependency graph, viewport renderer, and UI to evaluate the new custom property immediately
        for o in target_objs:
            try:
                o.update_tag(refresh={'DATA', 'OBJECT'})
            except TypeError:
                o.update_tag()

        if node_tree:
            node_tree.update_tag()
            if hasattr(node_tree, "id_data") and node_tree.id_data:
                node_tree.id_data.update_tag()

        if hasattr(context, "view_layer") and context.view_layer:
            context.view_layer.update()

        wm = getattr(context, "window_manager", None)
        if wm:
            for win in wm.windows:
                if win.screen:
                    for area in win.screen.areas:
                        if area.type in ('VIEW_3D', 'NODE_EDITOR', 'PROPERTIES'):
                            area.tag_redraw()

        # Add to scene registry of exposed parameters
        scene_props = getattr(context.scene, "npr_scene_props", None)
        if scene_props:
            entry = scene_props.exposed_params.add()
            entry.param_name = param_clean
            entry.property_key = prop_key_clean
            entry.param_type = 'COLOR' if target_sock.type in ('RGBA', 'VECTOR') else 'FLOAT'

        self.report({'INFO'}, f"Successfully exposed '{param_clean}' as parameter [{prop_key_clean}]!")
        return {'FINISHED'}

class NPR_OT_UnexposeParameter(bpy.types.Operator):
    """Removes an exposed attribute parameter from the Master Material and object custom properties"""
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

        # 1. Remove attribute node from shader node tree
        success, msg = unexpose_parameter(node_tree, self.property_key)

        # 2. Clean custom property from all objects sharing the material / scene
        cleaned_count = cleanup_custom_property_from_objects(node_tree, self.property_key, context)

        # 3. Clean scene registry entry if present
        scene_props = getattr(context.scene, "npr_scene_props", None)
        if scene_props:
            for idx, item in enumerate(scene_props.exposed_params):
                if item.property_key == self.property_key:
                    scene_props.exposed_params.remove(idx)
                    break

        if success or cleaned_count > 0:
            self.report({'INFO'}, f"Removed parameter '{self.property_key}' (Cleaned from {cleaned_count} object(s)).")
            return {'FINISHED'}

        self.report({'WARNING'}, msg)
        return {'CANCELLED'}

class NPR_OT_CleanUnusedProperties(bpy.types.Operator):
    """Purges Material Instancer custom properties (mi_*) not used by any assigned shader node"""
    bl_idname = "npr.clean_unused_properties"
    bl_label = "Clean Unused Properties"
    bl_options = {'REGISTER', 'UNDO'}

    property_key: bpy.props.StringProperty(name="Property Key", default="")

    def execute(self, context):
        if self.property_key:
            sdata = getattr(context, "space_data", None)
            node_tree = getattr(sdata, "edit_tree", None) if sdata else None
            if not node_tree and context.active_object and context.active_object.active_material:
                node_tree = context.active_object.active_material.node_tree
            count = cleanup_custom_property_from_objects(node_tree, self.property_key, context)
            self.report({'INFO'}, f"Cleaned unused property '{self.property_key}' from {count} object(s).")
        else:
            total = purge_all_unused_properties(context)
            self.report({'INFO'}, f"Purged {total} unused Material Instancer property/properties.")
        return {'FINISHED'}

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
