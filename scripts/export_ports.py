#OPEN IN BLENDER ONLY
import bpy
import os

def get_all_objects_recursive(collection):
    objects = []
    
    objects.extend(collection.objects)
    
    for child_collection in collection.children:
        objects.extend(get_all_objects_recursive(child_collection))
    
    return objects

ports_collection = bpy.data.collections.get("Ports")

if ports_collection is None:
    print("Collection 'Ports' not found!")
else:
    print(f"Found collection: {ports_collection.name}")
    
    all_objects = get_all_objects_recursive(ports_collection)
    
    blend_file_path = bpy.data.filepath
    if blend_file_path:
        output_dir = os.path.dirname(blend_file_path)
        output_file = os.path.join(output_dir, "scripts/ports.py")
    else:
        print("Warning: Blend file not saved. Using current working directory.")
        output_file = "ports.py"
    
    # Open file for writing
    with open(output_file, 'w') as f:
        f.write("#auto-generated port positions\n\n")
        f.write("port_pos = {}\n\n")
        
        # Iterate through each object in the collection and subcollections
        i = 0
        warnings = []
        
        for obj in all_objects:
            if obj.type == 'MESH':
                mesh = obj.data
                
                if len(mesh.vertices) == 8:  # is cube
                    # Get vertex 0 and 7
                    vert0 = mesh.vertices[0]
                    vert7 = mesh.vertices[7]
                    
                    # Convert local coordinates to world coordinates
                    world_coord_v0 = obj.matrix_world @ vert0.co
                    world_coord_v7 = obj.matrix_world @ vert7.co
                    
                    f.write(f"port_pos[{i}] = [[{world_coord_v0.x:.6f}, {world_coord_v0.y:.6f}, {world_coord_v0.z:.6f}], [{world_coord_v7.x:.6f}, {world_coord_v7.y:.6f}, {world_coord_v7.z:.6f}]]\n")
                    i += 1
                else:
                    warnings.append(f"Warning: {obj.name} doesn't have enough vertices (needs 8, has {len(mesh.vertices)})")
            else:
                warnings.append(f"Skipping {obj.name} - not a mesh object")
        
        # Write warnings as comments at the end
        if warnings:
            f.write("\n# Warnings:\n")
            for warning in warnings:
                f.write(f"# {warning}\n")
    
    print(f"Successfully wrote {i} port(s) to: {output_file}")
    print(f"Processed {len(all_objects)} total object(s)")