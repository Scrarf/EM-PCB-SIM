#OPEN IN BLENDER ONLY

import bpy

# Find the collection named "Ports"
ports_collection = bpy.data.collections.get("Ports")

if ports_collection is None:
    print("Collection 'Ports' not found!")
else:
    print(f"Found collection: {ports_collection.name}")
    print("-" * 60)
    
    # Iterate through each object in the collection
    i = 0
    for obj in ports_collection.objects:
        
        if obj.type == 'MESH':
            #print(f"\nObject: {obj.name}")
            
            # Get the mesh data
            mesh = obj.data
            
            if len(mesh.vertices) == 8: # is cube
                # Get vertex 3 and 4
                vert0 = mesh.vertices[0]
                vert7 = mesh.vertices[7]
                
                # Convert local coordinates to world coordinates
                world_coord_v0 = obj.matrix_world @ vert0.co
                world_coord_v7 = obj.matrix_world @ vert7.co
                
                print(f"""port[{i}] = fdtd.AddLumpedPort({i + 1}, z0,
                [{world_coord_v0.x:.6f}, {world_coord_v0.y:.6f}, {world_coord_v0.z:.6f}], 
                [{world_coord_v7.x:.6f}, {world_coord_v7.y:.6f}, {world_coord_v7.z:.6f}],
                'z', excite=0)""")
                i += 1
                
            else:
                print(f"  Warning: {obj.name} doesn't have enough vertices (needs at least 5)")
        else:
            print(f"\nSkipping {obj.name} - not a mesh object")
    
    print("\n" + "-" * 60)
    print("Done!")
    
