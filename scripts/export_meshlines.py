#OPEN IN BLENDER ONLY
import bpy

# Get the main collection
mesh_lines = bpy.data.collections.get("mesh_lines")

if mesh_lines:
    # Iterate through child collections (x, y, z)
    for child_collection in mesh_lines.children:
        collection_name = child_collection.name.lower()
        
        # Determine which axis to extract based on collection name
        if collection_name in ['x', 'y', 'z']:
            coords = []
            
            # Iterate through all objects in this collection
            for obj in child_collection.objects:
                # Get world location
                world_location = obj.matrix_world.translation
                
                # Extract the appropriate coordinate
                if collection_name == 'x':
                    coord = world_location.x
                elif collection_name == 'y':
                    coord = world_location.y
                else:  # z
                    coord = world_location.z
                
                coords.append(round(coord, 8))
            
            # Format output with line breaks every 8 values
            print(f"mesh_lines_{collection_name} = [")
            for i in range(0, len(coords), 8):
                chunk = coords[i:i+8]
                formatted_chunk = ", ".join(f"{val:.8f}" for val in chunk)
                if i + 8 < len(coords):
                    print(f"    {formatted_chunk},")
                else:
                    print(f"    {formatted_chunk}")
            print("]")
            print()
else:
    print("Collection 'mesh_lines' not found!")