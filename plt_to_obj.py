# Saturday, April 12, 2025
# Script using Ball Pivoting Algorithm for reconstruction

import open3d as o3d
import numpy as np
from plyfile import PlyData # Import plyfile

# --- Parameters ---
# For SH to RGB conversion (Standard constant for SH Degree 0)
SH_C0 = 0.2820947917

# !!! VERY IMPORTANT: Verify these property names match your PLY file header !!!
# These matched your previously posted header.
sh_dc_property_names = ['f_dc_0', 'f_dc_1', 'f_dc_2']

# --- File Paths ---
input_ply_path = "model_gen_two/point_cloud/iteration_7000/point_cloud.ply"
# --- Define output path for the OBJ file ---
output_obj_path = "output_reconstructed_BPA_sh_colors.obj" # New name for BPA output

# --- Ball Pivoting Parameters ---
# !!! --- CRITICAL: TUNE THESE RADII --- !!!
# You MUST determine appropriate radii based on the spacing of points in your cloud.
# 1. Measure approximate average/minimum point spacing in MeshLab/CloudCompare.
# 2. Start with radii around that minimum spacing and increase progressively.
# Example values (REPLACE these based on your data inspection!):
# If points are spaced ~0.05 units apart, maybe try: [0.05, 0.1, 0.2, 0.4]
# If points are spaced ~1.0 units apart, maybe try: [1.0, 2.0, 4.0, 8.0]
guessed_radii = [0.1, 0.2, 0.4, 0.8] # <--- !!! REPLACE THESE EXAMPLE VALUES !!!


# --- Main Script ---
try:
    # Print Open3D version - useful for debugging
    print(f"Using Open3D version: {o3d.__version__}")

    print(f"Loading PLY data using plyfile from {input_ply_path}...")
    # 1. Load PLY data using plyfile to access custom properties
    plydata = PlyData.read(input_ply_path)
    vertex_element = plydata['vertex']

    # Extract positions
    positions = np.vstack([vertex_element['x'], vertex_element['y'], vertex_element['z']]).T

    # Extract SH DC coefficients (or assign default color if missing)
    try:
        f_dc_0 = vertex_element[sh_dc_property_names[0]]
        f_dc_1 = vertex_element[sh_dc_property_names[1]]
        f_dc_2 = vertex_element[sh_dc_property_names[2]]
        has_sh_data = True
    except ValueError as e:
        print(f"Warning: Could not find expected SH properties: {sh_dc_property_names}. Using default gray.")
        has_sh_data = False
        original_point_colors = np.ones_like(positions) * 0.8 # Default light gray

    if has_sh_data:
        print(f"Loaded {len(positions)} points with SH data.")
        # 2. Convert SH DC coefficients to Linear RGB colors
        print("Calculating RGB colors from SH DC coefficients...")
        colors_r = 0.5 + f_dc_0 * SH_C0
        colors_g = 0.5 + f_dc_1 * SH_C0
        colors_b = 0.5 + f_dc_2 * SH_C0
        original_point_colors = np.vstack([colors_r, colors_g, colors_b]).T
        original_point_colors = np.clip(original_point_colors, 0.0, 1.0)
        print("RGB colors calculated.")

    # 3. Create Open3D Point Cloud object (mainly for BPA function input)
    # BPA doesn't strictly need normals estimated beforehand on the point cloud
    print("Creating Open3D point cloud object...")
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(positions)

    if not pcd.has_points():
        print("Error: Failed to create point cloud object.")
        exit()

    # --- ADD NORMAL ESTIMATION BACK IN ---
    print("Estimating normals (required for Ball Pivoting)...")
    # Use parameters defined at the top of the script
    normal_radius = 0.05 # Adjust if needed
    normal_max_nn = 30 # Adjust if needed
    search_param = o3d.geometry.KDTreeSearchParamHybrid(radius=normal_radius, max_nn=normal_max_nn)
    pcd.estimate_normals(search_param=search_param)
    # Optional: Orient normals consistently - can sometimes help BPA
    pcd.orient_normals_consistent_tangent_plane(k=normal_max_nn)
    print("Normals estimated.")

    if not pcd.has_normals():
        print("Error: Normal estimation failed.")
        exit()
    # --- END OF ADDED NORMAL ESTIMATION ---

    # 4. Perform Ball Pivoting Reconstruction
    print(f"Reconstructing mesh using Ball Pivoting with radii: {guessed_radii}...")
    radii = o3d.utility.DoubleVector(guessed_radii)
    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(pcd, radii)

    if not mesh.has_triangles():
        print("ERROR: Ball Pivoting reconstruction failed or produced empty mesh.")
        print("Try adjusting the radii list significantly (smaller or larger values).")
        exit()
    else:
        print(f"Mesh reconstruction complete. Generated {len(mesh.triangles)} triangles.")


    # 5. Check Alignment (Optional but Recommended)
    print("Checking for invalid values and comparing bounds before color transfer...")
    mesh_vertices = np.asarray(mesh.vertices)

    if np.isnan(positions).any() or np.isinf(positions).any():
        print("ERROR: Found NaN/Inf in original positions! Aborting.")
        exit()
    if np.isnan(mesh_vertices).any() or np.isinf(mesh_vertices).any():
        print("ERROR: Found NaN/Inf in mesh vertices! Reconstruction likely unstable. Aborting color transfer.")
        mesh.vertex_colors = o3d.utility.Vector3dVector(np.tile([1.0,0.0,1.0], (len(mesh_vertices),1))) # Color magenta
    elif mesh_vertices.shape[0] == 0:
        print("ERROR: Reconstructed mesh has no vertices!")
        exit()
    elif positions.shape[0] == 0:
        print("ERROR: Original point cloud data is empty!")
        exit()
    else:
        # Compare Bounds
        print("--- Comparing Bounds Before KNN ---")
        pos_min = positions.min(axis=0); pos_max = positions.max(axis=0)
        print(f"Original Points Min/Max: {pos_min} / {pos_max}")
        mesh_min = mesh_vertices.min(axis=0); mesh_max = mesh_vertices.max(axis=0)
        print(f"Mesh Vertices Min/Max: {mesh_min} / {mesh_max}")
        print("--- End Bound Comparison ---")

        # 6. Perform KNN Color Transfer (only if mesh vertices are valid and we have SH data)
        if has_sh_data:
            print("Transferring calculated colors to mesh vertices...")
            pcd_tree = o3d.geometry.KDTreeFlann(positions) # KDTree on original positions
            mesh_vertex_colors = np.zeros_like(mesh_vertices) # Initialize black
            errors_encountered = 0

            for i, vert in enumerate(mesh_vertices):
                try:
                    [k, idx, _] = pcd_tree.search_knn_vector_3d(vert, 1)
                    if k > 0:
                        mesh_vertex_colors[i] = original_point_colors[idx[0], :]
                    else:
                        mesh_vertex_colors[i] = [0.0, 1.0, 0.0] # Green if no neighbor found
                except RuntimeError as e:
                    if errors_encountered == 0: print("!!! Runtime Error during KNN search. Problematic vertices colored magenta. !!!")
                    errors_encountered += 1
                    mesh_vertex_colors[i] = [1.0, 0.0, 1.0] # Magenta on error

            mesh.vertex_colors = o3d.utility.Vector3dVector(mesh_vertex_colors)
            if errors_encountered > 0: print(f"WARNING: Encountered {errors_encountered} errors during KNN search.")
            else: print("Color transfer complete.")
        else:
            print("Assigning default gray color as original PLY lacked SH data.")
            mesh.vertex_colors = o3d.utility.Vector3dVector(np.tile([0.8, 0.8, 0.8], (len(mesh_vertices), 1)))

    print("Reconstructed mesh has vertex colors flag:", mesh.has_vertex_colors())

    # 7. Compute and Normalize Normals for the final mesh (Good Practice)
    if mesh.has_vertices():
        print("Computing and normalizing mesh normals...")
        mesh.compute_vertex_normals()
        mesh.normalize_normals()

    # 8. Save the final mesh as OBJ
    print(f"Saving reconstructed mesh with vertex colors to {output_obj_path}...")
    success = o3d.io.write_triangle_mesh(output_obj_path, mesh, write_vertex_colors=True)

    if success:
        print("Mesh successfully saved as OBJ.")
    else:
        print("ERROR: Failed to save the mesh file as OBJ!")

    print("Processing complete!")

except FileNotFoundError:
    print(f"Error: Input file not found at {input_ply_path}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    import traceback
    traceback.print_exc()