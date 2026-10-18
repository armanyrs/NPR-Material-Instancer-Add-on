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
    Removes an exposed attribute node from the Master Material tree.
    """
    if not node_tree:
        return False, "Node tree is None."
        
    attr_node = find_attribute_node_by_name(node_tree, prop_key)
    if attr_node:
        node_tree.nodes.remove(attr_node)
        return True, f"Removed exposed parameter '{prop_key}'"
    return False, f"Attribute node for '{prop_key}' not found."
