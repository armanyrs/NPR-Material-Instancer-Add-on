# Universal Material Instancer for Blender 🎨⚡

[![Blender Version](https://img.shields.io/badge/Blender-3.6%20LTS%20%7C%204.x%20%7C%205.x-orange.svg)](https://www.blender.org/)
[![Render Engines](https://img.shields.io/badge/Engines-EEVEE%20%7C%20EEVEE%20Next%20%7C%20Cycles-blue.svg)](https://www.blender.org/)
[![Performance](https://img.shields.io/badge/Shader%20Recompilation-0ms%20Instant-brightgreen.svg)](#features)
[![Release](https://img.shields.io/badge/Release-v1.0.0-blue.svg)](https://github.com/armanyrs/NPR-Material-Instancer-Add-on/releases)
[![License](https://img.shields.io/badge/License-GPLv3-green.svg)](LICENSE)

Bring **Unreal Engine's Master Material & Material Instancing** workflow directly into Blender!

Stop duplicating materials (`Material.001`, `Material.002`, `Material.003`) just to change a single color, roughness, or texture value. **Universal Material Instancer** lets you use **one single Master Material** in GPU memory while driving per-object variations via Object Custom Properties with **0ms shader recompilation lag**.

---

## 🌟 Why Use Universal Material Instancer?

| Traditional Blender Workflow | Universal Material Instancer Workflow |
| :--- | :--- |
| ❌ Duplicate materials for every slight color/roughness tweak | ✅ **1 Master Material** shared across all mesh instances |
| ❌ Cluttered `.blend` file with dozens of duplicate materials | ✅ Clean, organized project with zero duplicate bloat |
| ❌ Changing a master node requires editing every duplicate manually | ✅ Edit the Master Material once; all instances update instantly |
| ❌ Viewport freezes while Blender compiles shaders for every new material | ✅ **0ms Recompilation**: values update in real-time on GPU attributes |

---

## ✨ Features

- **🖱️ Unreal-Style Right-Click Expose**:
  Right-click on any input socket in the Shader Editor (Base Color, Roughness, Metallic, Normal Strength, etc.) and choose **"Convert to Parameter (Expose)"**.
- **⚡ 0ms Viewport Latency**:
  Driven by Blender's native `ShaderNodeAttribute` (Domain: `OBJECT`). Modifying parameters updates the viewport instantaneously without triggering shader re-compilations.
- **🎛️ Clean N-Panel Inspector**:
  Access all active instance parameters directly inside the **Shader Editor > Sidebar (N-Panel) > 'Material Instancer'** tab.
- **🚀 1-Click Jump to Object Custom Properties**:
  Jump directly to `Properties Editor > Object Properties > Custom Properties` with one click for detailed control, animation keyframing, and driver setups.
- **🧹 Clean & Foolproof Garbage Collection**:
  - Unexposing a parameter (`[X]`) automatically removes the custom property from **all mesh objects** using that material.
  - Built-in **"Clean All"** button detects and purges any dangling or unused `mi_*` properties from your scene.
- **🌐 Universal Shader Compatibility**:
  Works with **any shader node network** — Principled BSDF, Stylized / NPR Cel-Shading, Glass, Car Paint, Emission, or Procedural textures.

---

## 🚀 Quick Start Guide

### 1. Installation
1. Download the latest `universal_material_instancer_v1.0.0.zip` from the [Releases](https://github.com/armanyrs/NPR-Material-Instancer-Add-on/releases) page.
2. In Blender, navigate to:
   - **Blender 4.2+**: `Edit > Preferences > Get Extensions > Install from Disk...` (top right dropdown)
   - **Blender 3.6 - 4.1**: `Edit > Preferences > Add-ons > Install...`
3. Select the `.zip` file and enable **"Universal Material Instancer"**.

### 2. How to Use
1. **Assign your Master Material** to one or more mesh objects.
2. In the **Shader Editor**, right-click any node socket (e.g. `Base Color` on Principled BSDF) and click:
   > **Convert to Parameter (Expose)**
3. Give your parameter a clean name (e.g. `Base Color`) $\rightarrow$ Click **OK**.
4. Press `N` in the Shader Editor to open the sidebar, click the **Material Instancer** tab:
   - Tweak the color/value for the selected object.
   - Select another object sharing the same material — each object now has its own unique, independent values!
5. To jump to Blender's standard Custom Properties UI, click **"Open Object > Custom Properties"**.
6. To delete/unexpose a parameter, click the `[X]` button in the N-panel. The custom property will be automatically cleaned up across all objects.

---

## 💻 System Compatibility

- **Blender Versions**: 3.6 LTS, 4.0, 4.1, 4.2 LTS, 4.5 LTS, 5.0, 5.2+
- **Render Engines**:
  - Blender EEVEE & EEVEE Next
  - Blender Cycles
- **Operating Systems**: Windows, macOS, Linux

---

## 🛠️ Building & Packaging the Add-on (.zip)

If you are developing or cloning the repository directly:

1. Clone the repository:
   ```bash
   git clone https://github.com/armanyrs/NPR-Material-Instancer-Add-on.git
   ```
2. Create a zip archive containing the add-on folder:
   ```bash
   # From the repository root (PowerShell)
   Compress-Archive -Path __init__.py, core, operators, properties, ui, utils -DestinationPath universal_material_instancer_v1.0.0.zip
   ```
3. Install the resulting `.zip` in Blender.

---

## 🤝 Contributing & Feedback

Contributions, feature suggestions, and bug reports are welcome!
Feel free to open an issue or pull request on [GitHub Issues](https://github.com/armanyrs/NPR-Material-Instancer-Add-on/issues).

---

## 📄 License & Credits

- **Author**: Armany Saputra ([@armanyrs](https://github.com/armanyrs))
- **License**: GNU General Public License v3.0 (GPLv3)
