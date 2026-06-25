bl_info = {
    "name": "NPR Material Instancer",
    "author": "Armany Saputra",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > N-Panel > NPR Tools",
    "description": "Auto-generate and instance NPR Materials for Real-Time Production",
    "category": "Material",
}

import bpy

def update_base_color(self, context):
    # Menyimpan nilai warna dari UI ke dalam Custom Property objek
    context.active_object["npr_base_color"] = self.base_color

def update_shadow_color(self, context):
    context.active_object["npr_shadow_color"] = self.shadow_color

class NPR_InstanceProps(bpy.types.PropertyGroup):
    is_initialized: bpy.props.BoolProperty(
        name="Initialized",
        default=False
    )
    base_color: bpy.props.FloatVectorProperty(
        name="Base Color",
        subtype='COLOR',
        size=4,
        default=(0.8, 0.8, 0.8, 1.0),
        min=0.0, max=1.0,
        update=update_base_color
    )
    shadow_color: bpy.props.FloatVectorProperty(
        name="Shadow Color",
        subtype='COLOR',
        size=4,
        default=(0.2, 0.2, 0.5, 1.0),
        min=0.0, max=1.0,
        update=update_shadow_color
    )

def create_master_npr_shader():
    mat_name = "Master_NPR_Shader"
    mat = bpy.data.materials.get(mat_name)
    
    # Sesuai Flowchart B: Cek apakah Master Material sudah ada?
    if mat is None:
        # Jika tidak ada, buat material baru
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        # Bersihkan node default
        nodes.clear()
        
        # Buat Node Output
        out_node = nodes.new('ShaderNodeOutputMaterial')
        out_node.location = (800, 0)
        
        # Buat Node MixRGB untuk menggabungkan warna terang & bayangan
        mix_node = nodes.new('ShaderNodeMixRGB')
        mix_node.location = (600, 0)
        
        # Attribute Node: Mengambil Base Color dari Objek (Instancing)
        attr_base = nodes.new('ShaderNodeAttribute')
        attr_base.attribute_type = 'OBJECT'
        attr_base.attribute_name = 'npr_base_color'
        attr_base.location = (200, 200)
        
        # Attribute Node: Mengambil Shadow Color dari Objek (Instancing)
        attr_shadow = nodes.new('ShaderNodeAttribute')
        attr_shadow.attribute_type = 'OBJECT'
        attr_shadow.attribute_name = 'npr_shadow_color'
        attr_shadow.location = (200, -200)
        
        # Logika Pencahayaan Cel-Shading (Hanya jalan di EEVEE)
        diffuse = nodes.new('ShaderNodeBsdfDiffuse')
        diffuse.location = (-200, 0)
        
        s2rgb = nodes.new('ShaderNodeShaderToRGB')
        s2rgb.location = (0, 0)
        
        # ColorRamp untuk membuat transisi bayangan jadi tajam (Constant)
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.interpolation = 'CONSTANT'
        ramp.color_ramp.elements[0].position = 0.45 # Titik bayangan
        ramp.color_ramp.elements[1].position = 0.5  # Titik terang
        ramp.location = (200, 0)
        
        # Sambungkan logika cahaya
        links.new(diffuse.outputs['BSDF'], s2rgb.inputs['Shader'])
        links.new(s2rgb.outputs['Color'], ramp.inputs['Fac'])
        
        # Sambungkan ke Mix Node
        links.new(ramp.outputs['Color'], mix_node.inputs['Fac'])
        links.new(attr_shadow.outputs['Color'], mix_node.inputs['Color1']) # Jika gelap, pakai shadow color
        links.new(attr_base.outputs['Color'], mix_node.inputs['Color2'])   # Jika terang, pakai base color
        
        # Output akhir
        links.new(mix_node.outputs['Color'], out_node.inputs['Surface'])
        
    return mat

class OBJECT_OT_init_npr(bpy.types.Operator):
    """Initialize NPR Material Instance for selected object"""
    bl_idname = "object.init_npr_instance"
    bl_label = "Initialize NPR Instance"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "Select a Mesh Object first!")
            return {'CANCELLED'}
        
        # 1. Panggil pembuat Master Material
        master_mat = create_master_npr_shader()
        
        # 2. Pasang material ke objek (TIDAK DIDUPLIKASI)
        if len(obj.data.materials) == 0:
            obj.data.materials.append(master_mat)
        else:
            obj.data.materials[0] = master_mat
            
        # 3. Inisialisasi Custom Properties di Objek
        obj["npr_base_color"] = (0.8, 0.8, 0.8, 1.0)
        obj["npr_shadow_color"] = (0.2, 0.2, 0.5, 1.0)
        
        # 4. Tandai bahwa objek ini sudah punya instance
        obj.npr_props.is_initialized = True
        
        self.report({'INFO'}, f"NPR Instance applied to {obj.name}")
        return {'FINISHED'}

class VIEW3D_PT_npr_panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'NPR Tools'
    bl_label = "NPR Instancer Panel"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        if obj and obj.type == 'MESH':
            props = obj.npr_props
            
            if not props.is_initialized:
                layout.operator("object.init_npr_instance", icon='SHADING_RENDERED')
            else:
                box = layout.box()
                box.label(text=f"Instance: {obj.name}", icon='MATERIAL')
                
                # Menampilkan Color Picker di UI
                col = box.column(align=True)
                col.prop(props, "base_color")
                col.prop(props, "shadow_color")
                
                layout.separator()
                layout.label(text="Only 1 Material in Memory!", icon='INFO')
        else:
            layout.label(text="Select a Mesh Object")

classes = (
    NPR_InstanceProps,
    OBJECT_OT_init_npr,
    VIEW3D_PT_npr_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.npr_props = bpy.props.PointerProperty(type=NPR_InstanceProps)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Object.npr_props

if __name__ == "__main__":
    register()
