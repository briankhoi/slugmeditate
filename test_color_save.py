import open3d as o3d
import numpy as np

print(f"Testing simple mesh save with Open3D version: {o3d.__version__}")

# Create a simple cube mesh
mesh = o3d.geometry.TriangleMesh.create_box()
mesh.compute_vertex_normals()

# Assign vertex colors (based on position)
vertices = np.asarray(mesh.vertices)
# Normalize position to range [0, 1] for color
min_b = vertices.min(axis=0)
max_b = vertices.max(axis=0)
if (max_b - min_b).any() != 0 : # Avoid division by zero if box has zero size in any dim
    colors = (vertices - min_b) / (max_b - min_b)
else:
    colors = np.zeros_like(vertices) # Default to black if size is zero
    colors[:,0] = 1.0 # Make it red instead of black just to be visible

mesh.vertex_colors = o3d.utility.Vector3dVector(colors)
print("Assigned vertex colors to simple cube.")
print("Mesh has vertex colors flag:", mesh.has_vertex_colors())

# --- SAVE AS OBJ ---
output_simple_path_obj = "output_TEST_simple_cube_colors.obj"
print(f"Saving simple cube with vertex colors to {output_simple_path_obj}...")
success_obj = o3d.io.write_triangle_mesh(output_simple_path_obj, mesh, write_vertex_colors=True) # OBJ export

if success_obj:
    print("Simple cube saved successfully as OBJ.")
    print("Please view this OBJ file in MeshLab or Blender.")
else:
    print("ERROR: Failed to save the simple cube file as OBJ!")

# --- Optional: Also save as GLB for comparison ---
output_simple_path_glb = "output_TEST_simple_cube_colors.glb"
print(f"Saving simple cube with vertex colors to {output_simple_path_glb}...")
success_glb = o3d.io.write_triangle_mesh(output_simple_path_glb, mesh, write_vertex_colors=True) # GLB export
if not success_glb:
     print("ERROR: Failed to save the simple cube file as GLB!")