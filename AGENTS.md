# Project Rules & Guidelines: Universal Material Instancer Add-on

## 1. Project Overview & Vision
**Universal Material Instancer** adalah add-on Blender yang mengadopsi konsep **Master Material & Material Instance** seperti di Unreal Engine, mendukung **segala jenis shader** di Blender (PBR, Principled BSDF, NPR/Cel-shading, Glass, Car Paint, Procedural, dll.) untuk EEVEE & Cycles.

### Core Solution Architecture
* **Universal Shader Support**: Setiap material yang sudah ada pada objek bisa langsung dijadikan Master Material.
* **Single Master Material in GPU Memory**: Satu node network shader utama yang di-compile sekali.
* **Per-Object Attribute Driving**: Nilai parameter (warna, float, vector, roughness, switch, dll.) disimpan pada level Object Custom Properties dan dibaca secara real-time oleh `ShaderNodeAttribute` (Domain: `OBJECT`).
* **Unreal-Style Context Menu & Inspector**:
  * **Klik Kanan pada Node di Shader Editor**: Opsi *"Convert to Parameter (Expose)"* untuk mengubah socket input apapun menjadi instance parameter secara instan.
  * **N-Panel Shader Editor ('Material Instancer')**: Terletak rapi di tab Shading bawaan Blender, menampilkan parameter aktif yang terhubung ke objek.
  * **Shortcut Object > Custom Properties**: Tombol satu-klik untuk langsung membuka dan mengedit custom properties di Properties Editor.
  * **0ms Shader Recompilation**: Pergantian parameter di viewport terjadi seketika tanpa render freeze / stutter.

---

## 2. Technical Stack & Environment
* **Platform**: Blender 3.6 LTS, Blender 4.x, dan 5.x.
* **Core API**: `bpy` (Python 3.10+ / 3.11+ / 3.13+).
* **Render Engines**: Blender EEVEE (EEVEE Next di Blender 4.2+) & Cycles.
* **UI Location**: `NODE_EDITOR` > Sidebar (`UI`) > Category: `Material Instancer`.
* **Testing & Tooling**:
  * Headless Blender CLI (`blender.exe -b -P <test_script.py>`)
  * Blender MCP Integration (`execute_blender_code`, `get_scene_info`, `look`)

---

## 3. Modular Add-on Architecture

```text
NPR-Material-Instancer-Add-on/
├── __init__.py                  # bl_info metadata & register/unregister orchestration
├── core/
│   ├── master_material.py       # Pembangun Master Material serbaguna
│   ├── parameter_manager.py     # Logika ekskavasi & binding custom property ke ShaderNodeAttribute
│   └── instance_manager.py      # Operasi assign instance, batch copy, reset, & baking
├── properties/
│   ├── master_props.py          # Definisi RNA PropertyGroup untuk registry parameter
│   └── instance_props.py        # Definisi RNA PropertyGroup untuk instance flag
├── operators/
│   ├── init_instance.py         # Operator inisialisasi instance pada active/selected objects
│   ├── expose_parameter.py      # Operator klik kanan "Convert to Parameter" & NODE_MT_context_menu hook
│   ├── jump_to_custom_props.py  # Operator navigasi langsung ke Object > Custom Properties
│   └── floating_inspector.py    # Dialog pop-up floating inspector
├── ui/
│   ├── main_panel.py            # Sidebar N-Panel Shader Editor ('Material Instancer')
│   ├── parameter_inspector.py   # Registry daftar exposed attributes & tombol shortcut
│   └── preview_widget.py        # Widget monitoring performa GPU instancing & memory
└── utils/
    ├── node_helpers.py          # Helper manipulasi socket & pencarian node berdasarkan type
    └── compatibility.py         # Abstraksi perbedaan API Blender 3.x vs 4.x vs 5.x
```

---

## 4. Coding Rules & Best Practices

1. **Pencarian Node Berdasarkan `type`, Bukan `name`**:
   * Nama node (`node.name` atau `node.label`) dapat berubah karena lokalisasi atau penamaan user.
   * Selalu gunakan `node.type` (misal: `BSDF_PRINCIPLED`, `ATTRIBUTE`, `VALTORGB`, `MIX`).
2. **Universal Shader Compatibility**:
   * Jangan batasi add-on hanya pada shader NPR. Add-on harus dapat membaca dan mengekspos socket node apapun di dalam node tree.
3. **Fail-Safe Registration/Unregistration**:
   * Bungkus setiap panggilan `unregister_class` dalam blok `try ... except (RuntimeError, ValueError): pass` agar terhindar dari crash jika add-on di-reload atau di-disable oleh user.
4. **Hindari Komputasi Berat di `draw()` Panel**:
   * Traversal node tree di N-Panel hanya membaca atribut `ShaderNodeAttribute` yang ada tanpa merekonstruksi node tree.
5. **Undo/Redo Integrity**:
   * Semua operator yang mengubah state blender data harus memiliki flag:
     `bl_options = {'REGISTER', 'UNDO'}`.
