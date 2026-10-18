"""Utility packages for NPR Material Instancer."""
from .compatibility import create_mix_color_node, get_socket_by_identifier_or_name, is_blender_4_or_newer
from .node_helpers import (
    find_node_by_type,
    find_nodes_by_type,
    find_attribute_node_by_name,
    create_attribute_node,
    safe_link,
    organize_into_frame
)

__all__ = [
    "create_mix_color_node",
    "get_socket_by_identifier_or_name",
    "is_blender_4_or_newer",
    "find_node_by_type",
    "find_nodes_by_type",
    "find_attribute_node_by_name",
    "create_attribute_node",
    "safe_link",
    "organize_into_frame"
]
