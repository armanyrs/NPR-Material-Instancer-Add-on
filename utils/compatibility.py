"""
Compatibility layer for Blender 3.6 LTS, 4.x, and 5.x API differences.
Ensures seamless cross-version operation without deprecation crashes.
"""
import bpy

def get_blender_version():
    """Returns the Blender version tuple (major, minor, subminor)."""
    return bpy.app.version

def is_blender_4_or_newer():
    """True if Blender >= 4.0.0."""
    return bpy.app.version >= (4, 0, 0)

def is_blender_3_4_or_newer():
    """True if Blender >= 3.4.0 (MixRGB deprecated for ShaderNodeMix)."""
    return bpy.app.version >= (3, 4, 0)

def create_mix_color_node(nodes, name="Mix Color", location=(0, 0)):
    """
    Creates a Mix node for RGBA/Color operations compatible with
    Blender 3.3 (ShaderNodeMixRGB) and Blender 3.4+/4.x/5.x (ShaderNodeMix).
    
    Returns:
        (node, fac_socket, color1_socket, color2_socket, out_socket)
    """
    if is_blender_3_4_or_newer():
        node = nodes.new('ShaderNodeMix')
        node.name = name
        node.label = name
        node.data_type = 'RGBA'
        node.clamp_result = True
        node.location = location
        
        # In Blender 3.4+, inputs are 'Factor', 'A', 'B' and output is 'Result'
        fac_socket = node.inputs['Factor']
        col1_socket = node.inputs['A']
        col2_socket = node.inputs['B']
        out_socket = node.outputs['Result']
    else:
        node = nodes.new('ShaderNodeMixRGB')
        node.name = name
        node.label = name
        node.use_clamp = True
        node.location = location
        
        # In Blender <= 3.3, inputs are 'Fac', 'Color1', 'Color2' and output is 'Color'
        fac_socket = node.inputs['Fac']
        col1_socket = node.inputs['Color1']
        col2_socket = node.inputs['Color2']
        out_socket = node.outputs['Color']
        
    return node, fac_socket, col1_socket, col2_socket, out_socket

def get_socket_by_identifier_or_name(sockets, *names):
    """
    Finds a socket by matching identifier or name from a list of possible names.
    Provides robust socket lookup against localization changes.
    """
    for n in names:
        if n in sockets:
            return sockets[n]
    # Fallback: search case-insensitive identifier or name
    lower_names = [n.lower() for n in names]
    for sock in sockets:
        if sock.name.lower() in lower_names or sock.identifier.lower() in lower_names:
            return sock
    return None
