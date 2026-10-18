---
name: blender-addon-dev
description: Procedures and best practices for developing, testing, debugging, and packaging Blender add-ons using Python (bpy), including headless CLI validation and Blender MCP integration.
---

# Blender Add-on Development Skill (`bpy`)

This skill provides comprehensive workflows, architecture patterns, and testing guidelines for developing production-grade Blender add-ons, with special focus on shader nodes, dynamic parameter exposure, and material instancing.

---

## 1. Add-on Architecture & Lifecycle

### `bl_info` Definition
Every add-on must declare metadata at its entrypoint (`__init__.py` or single script):
```python
bl_info = {
    "name": "NPR Material Instancer",
    "author": "Armany Saputra",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar (N-Panel) > NPR Tools",
    "description": "Unreal-style Master Material and Material Instance manager for real-time viewport",
    "category": "Material",
    "doc_url": "",
    "tracker_url": "",
}
```

### Clean Registration & Teardown
Always unregister classes in reverse order. Remove pointer properties from built-in types upon unregistration to avoid stale references:
```python
classes = (
    MyPropertyGroup,
    MY_OT_Operator,
    MY_PT_Panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.my_custom_props = bpy.props.PointerProperty(type=MyPropertyGroup)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Object, "my_custom_props"):
        del bpy.types.Object.my_custom_props
```

---

## 2. Material Instancing Pattern in Blender

### Why Traditional Duplication Fails
* Assigning a duplicate material (`mat.copy()`) creates a new shader evaluation graph in EEVEE/Cycles, triggering shader recompilation and viewport stutters.
* In NPR (Cel-shading) with dozens of characters/props, this degrades frame rates and bloats `.blend` file sizes.

### The Zero-Recompile Instancing Architecture
1. **Master Material (`M_Master_NPR`)**:
   * Stored once in `bpy.data.materials`.
   * Assigned to all instanced mesh objects (`obj.data.materials[0] = master_mat`).
2. **Dynamic Attribute Injection**:
   * When a parameter (e.g., `base_color`, `shadow_tint`, `line_thickness`) is exposed:
   * Create an **Attribute Node** in the Master Material:
     ```python
     attr_node = nodes.new('ShaderNodeAttribute')
     attr_node.attribute_type = 'OBJECT'
     attr_node.attribute_name = "npr_base_color"
     ```
   * Link `attr_node.outputs['Color']` (or `Fac` / `Vector`) to the target node socket.
3. **Per-Object Custom Property**:
   * Set on the object:
     ```python
     obj["npr_base_color"] = (0.8, 0.2, 0.2, 1.0)
     ```
   * Any change to `obj["npr_base_color"]` updates the viewport immediately with **0ms shader recompilation**.

---

## 3. Dynamic UI & Parameter Inspector

### Rendering Custom Properties Dynamically
To create an Unreal Engine-style parameter list:
```python
class NPR_PT_InstanceInspector(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'NPR Tools'
    bl_label = "Material Instance Parameters"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            layout.label(text="Select a Mesh Object", icon='INFO')
            return

        props = getattr(obj, "npr_props", None)
        if not props or not props.is_initialized:
            layout.operator("object.init_npr_instance", text="Initialize Instance", icon='MATERIAL')
            return

        box = layout.box()
        box.label(text=f"Instance: {obj.name}", icon='OBJECT_DATAMODE')
        
        # Draw exposed parameters
        col = box.column(align=True)
        col.prop(props, "base_color", text="Base Color")
        col.prop(props, "shadow_color", text="Shadow Color")
```

---

## 4. Testing Procedures

### A. Live Testing via Blender MCP
When Blender is running with the Blender MCP add-on:
1. Verify status:
   Use `call_mcp_tool(ServerName="blender-mcp", ToolName="get_addon_status", Arguments={})`.
2. Inspect scene:
   Use `call_mcp_tool(ServerName="blender-mcp", ToolName="get_scene_info", Arguments={})`.
3. Execute code live:
   Use `call_mcp_tool(ServerName="blender-mcp", ToolName="execute_blender_code", Arguments={"code": "...bpy code..."})`.
4. Visual verification:
   Use `call_mcp_tool(ServerName="blender-mcp", ToolName="look", Arguments={})` to capture the current viewport / camera render.

### B. Headless CLI Testing (Automated Syntax & Execution Check)
Use the installed Blender binary to run unit tests and verify script execution without GUI:
```powershell
& "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe" -b --python-expr "import script; script.register(); print('Add-on loaded successfully!')"
```

---

## 5. API Compatibility Rules (Blender 3.x vs 4.x vs 5.x)
* **Mix Node**:
  * Blender <= 3.3: `ShaderNodeMixRGB` (`inputs['Color1']`, `inputs['Color2']`, `inputs['Fac']`).
  * Blender >= 3.4 / 4.x / 5.x: `ShaderNodeMix` with `data_type='RGBA'`, (`inputs['A']`, `inputs['B']`, `inputs['Factor']`).
  * Rule: Implement a helper `create_mix_color_node(nodes)` to abstract version differences.
* **Context Overrides**:
  * Old: `bpy.ops.something({'selected_objects': ...})`
  * Blender 3.2+: `with context.temp_override(selected_objects=...): bpy.ops.something()`
* **Shader Socket Types**:
  * Access sockets by identifier or index rather than localized name when possible, or check `socket.name` and fallback to `socket.identifier`.
