"""Core parameter exposure logic for Material Instancer."""
from .parameter_manager import (
    get_exposed_parameters_from_tree,
    expose_socket_as_parameter,
    unexpose_parameter,
    get_socket_default_value,
    cleanup_custom_property_from_objects,
    purge_all_unused_properties,
)

__all__ = [
    "get_exposed_parameters_from_tree",
    "expose_socket_as_parameter",
    "unexpose_parameter",
    "get_socket_default_value",
    "cleanup_custom_property_from_objects",
    "purge_all_unused_properties",
]
