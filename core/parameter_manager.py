"""
Parameter Exposure & Excavation Manager.
Allows users to dynamically pick any shader socket in the Master Material,
convert it into an exposed instance parameter, and drive it per-object.
"""
import bpy
from ..utils.node_helpers import create_attribute_node, safe_link, find_attribute_node_by_name

def get_socket_default_value(socket):
    """Extracts a serializable default value from a NodeSocket."""
    if hasattr(socket, "default_value"):
        val = socket.default_value
        if isinstance(val, (float, int, bool)):
            return val
        if hasattr(val, "__iter__"):
            return list(val)
    if socket.type in ('RGBA', 'VECTOR'):
        return [1.0, 1.0, 1.0, 1.0]
    return 1.0

def get_exposed_parameters_from_tree(node_tree):
    """
    Scans a shader node tree for all ShaderNodeAttribute nodes of type 'OBJECT'.
    Returns a dictionary of attribute names and their connected nodes.
    """
    if not node_tree or not hasattr(node_tree, "nodes"):
        return {}
    
    attributes = {}
    for node in node_tree.nodes:
        if node.type == 'ATTRIBUTE' and node.attribute_type == 'OBJECT':
            attr_name = node.attribute_name
            if attr_name:
                attributes[attr_name] = {
                    "node": node,
                    "label": node.label or attr_name,
                    "outputs": [sock.name for sock in node.outputs if sock.is_linked]
                }
    return attributes

def expose_socket_as_parameter(node_tree, target_node, target_socket, param_name, prop_key):
    """
    Exposes an arbitrary input socket in the Master Material by inserting
    an Attribute Node wired into that socket.
    """
    if not node_tree or not target_node or not target_socket:
        return None, "Invalid target node or socket."
    
    # Remove any existing link on target_socket
    for link in list(node_tree.links):
        if link.to_socket == target_socket:
            node_tree.links.remove(link)
    
    # Calculate position slightly to the left of the target node
    loc_x = target_node.location.x - 240
    loc_y = target_node.location.y
    
    # Create attribute node
    attr_node = create_attribute_node(
        node_tree.nodes,
        attribute_name=prop_key,
        attribute_type='OBJECT',
        location=(loc_x, loc_y),
        label=param_name
    )
    
    # Link output: Color if vector/color, Fac if float
    if target_socket.type in ('RGBA', 'VECTOR'):
        safe_link(node_tree.links, attr_node.outputs['Color'], target_socket)
    else:
        safe_link(node_tree.links, attr_node.outputs['Fac'], target_socket)
        
    return attr_node, f"Exposed '{param_name}' via attribute '{prop_key}'"

def unexpose_parameter(node_tree, prop_key):
    """
    Removes all exposed attribute nodes with prop_key from the Master Material tree.
    """
    if not node_tree or not hasattr(node_tree, "nodes"):
        return False, "Node tree is None."

    removed_nodes = [
        node for node in node_tree.nodes
        if node.type == 'ATTRIBUTE' and getattr(node, "attribute_name", "") == prop_key
    ]
    for node in removed_nodes:
        node_tree.nodes.remove(node)

    if removed_nodes:
        return True, f"Removed {len(removed_nodes)} exposed attribute node(s) for '{prop_key}'"
    return False, f"Attribute node for '{prop_key}' not found."

def object_has_active_attribute(obj, prop_key):
    """Checks if any material currently assigned to obj uses an Attribute node for prop_key."""
    materials = []
    if hasattr(obj, "material_slots"):
        materials.extend([s.material for s in obj.material_slots if s.material])
    elif hasattr(obj, "data") and hasattr(obj.data, "materials"):
        materials.extend([m for m in obj.data.materials if m])

    for mat in materials:
        if mat and mat.node_tree and hasattr(mat.node_tree, "nodes"):
            for n in mat.node_tree.nodes:
                if n.type == 'ATTRIBUTE' and getattr(n, "attribute_name", "") == prop_key:
                    return True
    return False

def cleanup_custom_property_from_objects(node_tree, prop_key, context=None):
    """
    Removes custom property `prop_key` from all objects in bpy.data.objects
    that no longer have any active material requiring it.
    """
    cleaned_count = 0
    for obj in bpy.data.objects:
        if prop_key in obj:
            if not object_has_active_attribute(obj, prop_key):
                try:
                    del obj[prop_key]
                    cleaned_count += 1
                except (KeyError, RuntimeError):
                    pass
                if "_RNA_UI" in obj and prop_key in obj["_RNA_UI"]:
                    try:
                        del obj["_RNA_UI"][prop_key]
                    except (KeyError, RuntimeError):
                        pass

    # Tag redraw on relevant editors
    wm = getattr(context, "window_manager", None) if context else getattr(bpy.context, "window_manager", None)
    if wm:
        for win in wm.windows:
            if win.screen:
                for area in win.screen.areas:
                    if area.type in ('PROPERTIES', 'NODE_EDITOR', 'VIEW_3D'):
                        area.tag_redraw()

    return cleaned_count

def purge_all_unused_properties(context=None):
    """
    Purges all custom properties starting with 'mi_' across all objects
    that are not actively used by any assigned shader node.
    """
    cleaned_total = 0
    for obj in bpy.data.objects:
        mi_keys = [k for k in obj.keys() if k.startswith("mi_")]
        for key in mi_keys:
            if not object_has_active_attribute(obj, key):
                try:
                    del obj[key]
                    cleaned_total += 1
                except (KeyError, RuntimeError):
                    pass
                if "_RNA_UI" in obj and key in obj["_RNA_UI"]:
                    try:
                        del obj["_RNA_UI"][key]
                    except (KeyError, RuntimeError):
                        pass

    wm = getattr(context, "window_manager", None) if context else getattr(bpy.context, "window_manager", None)
    if wm:
        for win in wm.windows:
            if win.screen:
                for area in win.screen.areas:
                    if area.type in ('PROPERTIES', 'NODE_EDITOR', 'VIEW_3D'):
                        area.tag_redraw()

    return cleaned_total

