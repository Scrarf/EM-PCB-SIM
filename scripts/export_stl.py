#OPEN IN BLENDER ONLY

import bpy

# Get the Objects collection
objects_collection = bpy.data.collections.get("Objects")

if objects_collection is None:
    print("Collection 'Objects' not found!")
else:
    # Create new collection named "Objects_processed"
    objects_processed = bpy.data.collections.new("Objects_processed")
    bpy.context.scene.collection.children.link(objects_processed)
    
    # Get the auto_bounds object
    auto_bounds = bpy.data.objects.get("auto_bounds")
    
    if auto_bounds is None:
        print("Object 'auto_bounds' not found!")
    else:
        # Duplicate all objects from Objects collection
        for obj in objects_collection.objects:
            # Duplicate the object
            new_obj = obj.copy()
            new_obj.data = obj.data.copy()  # Also copy the mesh data
            
            # Link the new object to Objects_processed collection
            objects_processed.objects.link(new_obj)
        
        # Apply boolean modifier to each object in Objects_processed
        for obj in objects_processed.objects:
            # Add boolean modifier
            bool_mod = obj.modifiers.new(name="Boolean", type='BOOLEAN')
            bool_mod.object = auto_bounds
            bool_mod.operation = 'INTERSECT'
            
            # Apply the modifier
            # Set the object as active and deselect all first
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)
            
            print(f"{obj} boolean success.")
        
        print("Boolean operations completed successfully!")
        print(f"Created {len(objects_processed.objects)} objects in 'Objects_processed' collection")
        
        # Create stl directory if it doesn't exist
        import os
        
        # Get the directory where the blend file is saved
        blend_file_path = bpy.data.filepath
        if not blend_file_path:
            print("ERROR: Blend file is not saved. Please save your file first!")
        else:
            blend_dir = os.path.dirname(blend_file_path)
            stl_dir = os.path.join(blend_dir, "stl")
            
            if not os.path.exists(stl_dir):
                try:
                    os.makedirs(stl_dir)
                    print(f"Created directory: {stl_dir}")
                except PermissionError:
                    print(f"ERROR: Permission denied. Cannot create directory: {stl_dir}")
                    stl_dir = None
            else:
                print(f"Using existing directory: {stl_dir}")
            
            # Export each object as STL
            if stl_dir:
                for obj in objects_processed.objects:
                    # Deselect all and select only current object
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)
                    bpy.context.view_layer.objects.active = obj
                    
                    # Export as STL (using new Blender 5.0 operator)
                    stl_path = os.path.join(stl_dir, f"{obj.name}.stl")
                    try:
                        # Try new Blender 5.0 export operator first
                        bpy.ops.wm.stl_export(
                            filepath=stl_path,
                            export_selected_objects=True
                        )
                        print(f"Exported: {stl_path}")
                    except AttributeError:
                        # Fall back to older export method
                        bpy.ops.export_mesh.stl(
                            filepath=stl_path,
                            use_selection=True
                        )
                        print(f"Exported: {stl_path}")
                
                print(f"\nAll {len(objects_processed.objects)} objects exported to {stl_dir}/")
