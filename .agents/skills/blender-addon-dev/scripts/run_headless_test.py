"""
Clean Headless Blender Test Suite for Universal Material Instancer Add-on.
Tests registration, Convert to Parameter (Expose), parameter tweaking,
jump to Object Custom Properties, and clean unregistration.
"""
import sys
import os

def run_tests():
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    print("=" * 60)
    print(f"[TEST RUNNER] Python: {sys.version}")
    
    try:
        import bpy
        print(f"[TEST RUNNER] Blender: {bpy.app.version_string}")
        print("=" * 60)

        # 1. Test Package Registration
        print("\n[STEP 1] Testing Add-on Registration...")
        import importlib.util
        init_path = os.path.join(cwd, "__init__.py")
        spec = importlib.util.spec_from_file_location(
            "npr_material_instancer",
            init_path,
            submodule_search_locations=[cwd]
        )
        npr_addon = importlib.util.module_from_spec(spec)
        sys.modules["npr_material_instancer"] = npr_addon
        spec.loader.exec_module(npr_addon)
        
        npr_addon.register()
        print("  ✓ Add-on registered successfully.")

        # 2. Test Object Creation with a Material (3 Cubes Sharing Master Material)
        print("\n[STEP 2] Creating 3 Cubes Sharing Master Material...")
        cubes = []
        custom_mat = bpy.data.materials.new(name="PBR_Material")
        if hasattr(custom_mat, "use_nodes"):
            custom_mat.use_nodes = True

        for i in range(3):
            bpy.ops.mesh.primitive_cube_add(location=(i * 3, 0, 0))
            c = bpy.context.active_object
            c.name = f"Test_Cube_{i+1}"
            c.data.materials.append(custom_mat)
            cubes.append(c)

        print(f"  ✓ Created 3 cubes sharing material '{custom_mat.name}'.")

        # 3. Test Unreal-Style 'Convert to Parameter' (Right-Click Expose)
        print("\n[STEP 3] Testing 'Convert to Parameter' on Principled BSDF...")
        principled_node = None
        for n in custom_mat.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                principled_node = n
                break
        assert principled_node is not None, "Principled BSDF node must exist"
        custom_mat.node_tree.nodes.active = principled_node

        base_color_sock = principled_node.inputs.get("Base Color")
        assert base_color_sock is not None, "Base Color socket must exist"
        
        expose_res = bpy.ops.npr.expose_node_as_parameter(
            param_name="Base Color",
            property_key="mi_base_color",
            target_socket_id=base_color_sock.identifier
        )
        assert expose_res == {'FINISHED'}, f"Expose operator failed: {expose_res}"
        
        # Verify Attribute node was linked
        attr_found = False
        for n in custom_mat.node_tree.nodes:
            if n.type == 'ATTRIBUTE' and n.attribute_name == "mi_base_color":
                attr_found = True
                assert n.outputs['Color'].is_linked, "Attribute node Color output must be linked"
                break
        assert attr_found is True, "ShaderNodeAttribute for 'mi_base_color' must exist"
        
        for c in cubes:
            assert "mi_base_color" in c, f"Custom property 'mi_base_color' must exist on {c.name}"
        print("  ✓ 'Convert to Parameter' successfully exposed socket and initialized [mi_base_color] across ALL 3 cubes!")

        # 4. Test Live Parameter Tweaking on Objects
        print("\n[STEP 4] Testing Parameter Tweaking on Object Custom Property...")
        cubes[0]["mi_base_color"] = [1.0, 0.0, 0.0, 1.0] # Red
        cubes[1]["mi_base_color"] = [0.0, 1.0, 0.0, 1.0] # Green
        cubes[2]["mi_base_color"] = [0.0, 0.0, 1.0, 1.0] # Blue
        print("  ✓ Tweaked distinct color instances on all 3 cubes.")

        # 5. Test Shortcut to Object > Custom Properties
        print("\n[STEP 5] Testing 'Jump to Custom Properties' Operator...")
        jump_res = bpy.ops.npr.jump_to_custom_props()
        assert jump_res == {'FINISHED'}, "Jump to custom props operator failed"
        print("  ✓ 'Jump to Custom Properties' operator executed successfully.")

        # 6. Test Unexpose Parameter (Delete [X] from Panel N)
        print("\n[STEP 6] Testing 'Unexpose Parameter' (Clicking [X])...")
        unexpose_res = bpy.ops.npr.unexpose_parameter(property_key="mi_base_color")
        assert unexpose_res == {'FINISHED'}, f"Unexpose operator failed: {unexpose_res}"

        # Verify Attribute node is removed
        for n in custom_mat.node_tree.nodes:
            if n.type == 'ATTRIBUTE':
                assert n.attribute_name != "mi_base_color", "Attribute node must be removed"
        print("  ✓ Attribute node removed from shader graph.")

        # Verify property is removed from ALL 3 cubes
        for c in cubes:
            assert "mi_base_color" not in c, f"Custom property 'mi_base_color' must NOT be stuck on {c.name}"
        print("  ✓ Custom property [mi_base_color] cleanly deleted from ALL 3 cubes (bug fixed)!")

        # 7. Test Purging Dangling/Unused Properties
        print("\n[STEP 7] Testing Purge Dangling/Unused Properties Operator...")
        cubes[0]["mi_dangling_prop"] = 0.5
        cubes[1]["mi_dangling_prop"] = 0.7
        clean_res = bpy.ops.npr.clean_unused_properties()
        assert clean_res == {'FINISHED'}, f"Clean unused operator failed: {clean_res}"
        for c in cubes:
            assert "mi_dangling_prop" not in c, f"Dangling property must be purged from {c.name}"
        print("  ✓ Cleaned unused properties cleanly.")

        # 8. Test Clean Unregistration
        print("\n[STEP 8] Testing Clean Unregistration...")
        npr_addon.unregister()
        print("  ✓ Cleanly unregistered.")

        print("\n" + "=" * 60)
        print(">>> ALL VERIFICATION TESTS PASSED SUCCESSFULLY! (100% OK) <<<")
        print("=" * 60)

    except Exception as e:
        import traceback
        print(f"\n[FATAL ERROR] Test suite failed:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
