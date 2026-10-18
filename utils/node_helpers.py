"""
Utility functions for querying, creating, and connecting Shader Nodes cleanly.
Adheres strictly to the rule: Query by node.type instead of localized names.
"""
import bpy

def find_nodes_by_type(node_tree, node_type):
    """Returns a list of all nodes matching the given node_type string."""
    if not node_tree or not hasattr(node_tree, "nodes"):
        return []
    return [n for n in node_tree.nodes if n.type == node_type]

def find_node_by_type(node_tree, node_type):
    """Returns the first node matching node_type, or None if not found."""
    nodes = find_nodes_by_type(node_tree, node_type)
    return nodes[0] if nodes else None

def find_attribute_node_by_name(node_tree, attribute_name):
    """Finds a ShaderNodeAttribute node configured with a specific attribute_name."""
    if not node_tree or not hasattr(node_tree, "nodes"):
        return None
    for node in node_tree.nodes:
        if node.type == 'ATTRIBUTE' and getattr(node, "attribute_name", "") == attribute_name:
            return node
    return None

def create_attribute_node(nodes, attribute_name, attribute_type='OBJECT', location=(0, 0), label=None):
    """
    Creates and configures a ShaderNodeAttribute node.
    
    Args:
        nodes: bpy.types.Nodes collection
        attribute_name: Custom property name to read from Object
        attribute_type: 'OBJECT', 'GEOMETRY', or 'INSTANCER'
        location: (x, y) tuple for node placement
        label: Human-readable label for the node
    """
    attr_node = nodes.new('ShaderNodeAttribute')
    attr_node.attribute_type = attribute_type
    attr_node.attribute_name = attribute_name
    attr_node.location = location
    attr_node.label = label if label else f"Attr: {attribute_name}"
    return attr_node

def safe_link(links, from_socket, to_socket):
    """Safely links two sockets if both are valid and not None."""
    if from_socket and to_socket:
        return links.new(from_socket, to_socket)
    return None

def organize_into_frame(node_tree, label, nodes_list, location=(0, 0), color=None):
    """Creates a frame node grouping a set of nodes visually for clean graphs."""
    frame = node_tree.nodes.new('NodeFrame')
    frame.label = label
    frame.name = f"Frame_{label.replace(' ', '_')}"
    frame.location = location
    if color:
        frame.use_custom_color = True
        frame.color = color
    for n in nodes_list:
        n.parent = frame
    return frame
