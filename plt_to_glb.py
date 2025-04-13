import open3d as o3d
import numpy as np
from plyfile import PlyData # Import plyfile

# --- Parameters to potentially tune ---
# For normal estimation:
normal_radius = 0.05 # Adjust based on your point cloud's scale
normal_max_nn = 30 # Adjust based on density

# For Poisson reconstruction:
poisson_depth = 9 # Adjust for detail vs. performance

# For SH to RGB conversion (Standard constant for SH Degree 0)
SH_C0 = 0.2820947917

# !!! VERY IMPORTANT: Verify these property names in your PLY file header !!!
sh_dc_property_names = ['f_dc_0', 'f_dc_1', 'f_dc_2']
# !!! VERY IMPORTANT: Update the list above if your names differ !!!

# --- File Paths ---
input_ply_path = "model_gen_two/point_cloud/iteration_7000/point_cloud.ply"
output_glb_path = "output_reconstructed_sh_colors.glb" # Changed output name

# --- Main Script ---
try:
    print(f"Loading PLY data using plyfile from {input_ply_path}...")
    # 1. Load PLY data using plyfile to access custom properties
    plydata = PlyData.read(input_ply_path)
    vertex_element = plydata['vertex']

    # Extract positions
    positions = np.vstack([vertex_element['x'], vertex_element['y'], vertex_element['z']]).T

    # Extract SH DC coefficients (MAKE SURE NAMES ARE CORRECT)
    try:
        f_dc_0 = vertex_element[sh_dc_property_names[0]]
        f_dc_1 = vertex_element[sh_dc_property_names[1]]
        f_dc_2 = vertex_element[sh_dc_property_names[2]]
    except ValueError as e:
         print(f"Error: Could not find expected SH properties: {sh_dc_property_names}")
         print(f"Please check the property names in your PLY header and update the script.")
         print(f"Original error: {e}")
         exit()

    print(f"Loaded {len(positions)} points with SH data.")

    # 2. Convert SH DC coefficients to Linear RGB colors
    print("Calculating RGB colors from SH DC coefficients...")
    # Apply the formula: color = 0.5 + coeff * SH_C0
    colors_r = 0.5 + f_dc_0 * SH_C0
    colors_g = 0.5 + f_dc_1 * SH_C0
    colors_b = 0.5 + f_dc_2 * SH_C0
    # Combine into an Nx3 array
    original_point_colors = np.vstack([colors_r, colors_g, colors_b]).T
    # Clamp values to the valid [0, 1] range
    original_point_colors = np.clip(original_point_colors, 0.0, 1.0)
    print("RGB colors calculated.")

    print("Checking calculated RGB colors...")
    if original_point_colors.size > 0:
        print(f"  Sample calculated RGB colors (first 5):\n{original_point_colors[:5]}")
        print(f"  Color range (Min per channel): {np.min(original_point_colors, axis=0)}")
        print(f"  Color range (Max per channel): {np.max(original_point_colors, axis=0)}")
        print(f"  Color range (Mean per channel): {np.mean(original_point_colors, axis=0)}")
    else:
        print("  original_point_colors array is empty!")

    # 3. Create Open3D Point Cloud object manually
    print("Creating Open3D point cloud object...")
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(positions)
    # We store the calculated RGB colors here temporarily for potential visualization/use
    # Note: These colors aren't used by Poisson directly, only positions & normals are.
    pcd.colors = o3d.utility.Vector3dVector(original_point_colors)

    if not pcd.has_points():
        print("Error: Failed to create point cloud object.")
        exit()

    print("Estimating normals...")
    # 4. Estimate normals (Needed for Poisson)
    search_param = o3d.geometry.KDTreeSearchParamHybrid(radius=normal_radius, max_nn=normal_max_nn)
    pcd.estimate_normals(search_param=search_param)
    pcd.orient_normals_consistent_tangent_plane(k=normal_max_nn)
    print("Normals estimated.")

    if not pcd.has_normals():
         print("Error: Normal estimation failed.")
         exit()

    print(f"Reconstructing mesh using Poisson (depth={poisson_depth})...")
    # 5. Perform Poisson Surface Reconstruction
    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd, depth=poisson_depth, width=0, scale=1.1, linear_fit=False)
    print("Mesh reconstruction complete.")

    # Optional: Clean up mesh
    # print("Cleaning mesh...")
    # vertices_to_remove = densities < np.quantile(densities, 0.01)
    # mesh.remove_vertices_by_mask(vertices_to_remove)
    # print("Mesh cleaned.")
    print("Checking for invalid values before color transfer...")
    mesh_vertices = np.asarray(mesh.vertices)

    # --- DEBUGGING CHECKS ---
    invalid_positions = np.isnan(positions).any() or np.isinf(positions).any()
    invalid_mesh_vertices = np.isnan(mesh_vertices).any() or np.isinf(mesh_vertices).any()

    if invalid_positions:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("ERROR: Found NaN or Inf values in original point cloud positions!")
        print("Cannot build KDTree reliably. Please clean the input PLY data.")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # Optionally find and print offending indices:
        # nan_indices = np.where(np.isnan(positions).any(axis=1))[0]
        # inf_indices = np.where(np.isinf(positions).any(axis=1))[0]
        # print(f"NaN indices (example): {nan_indices[:10]}")
        # print(f"Inf indices (example): {inf_indices[:10]}")
        exit() # Stop execution

    if invalid_mesh_vertices:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("ERROR: Found NaN or Inf values in reconstructed mesh vertices!")
        print("KNN search might fail. This might indicate issues with reconstruction parameters.")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # Optionally find and print offending indices:
        # nan_indices = np.where(np.isnan(mesh_vertices).any(axis=1))[0]
        # inf_indices = np.where(np.isinf(mesh_vertices).any(axis=1))[0]
        # print(f"NaN indices (example): {nan_indices[:10]}")
        # print(f"Inf indices (example): {inf_indices[:10]}")
        # Consider stopping execution if this is unexpected, or proceed cautiously.
        # exit() # Optional: Stop execution

    if mesh_vertices.shape[0] == 0:
        print("ERROR: Reconstructed mesh has no vertices!")
        exit()

    if positions.shape[0] == 0:
        print("ERROR: Original point cloud data is empty!")
        exit()
    # --- END DEBUGGING CHECKS ---


    print("Transferring calculated colors to mesh vertices...")
    # Build a KDTree on the *original point positions* for fast search
    pcd_tree = o3d.geometry.KDTreeFlann(positions)

    mesh_vertex_colors = np.zeros_like(mesh_vertices) # Initialize with zeros
    errors_encountered = 0

    # For each vertex in the reconstructed mesh, find the nearest original point
    for i, vert in enumerate(mesh_vertices):
        try:
            # Find the index of the nearest point in 'pcd' to the mesh vertex 'vert'
            [k, idx, _] = pcd_tree.search_knn_vector_3d(vert, 1) # Find 1 nearest neighbor

            if k > 0:
                # Assign the pre-calculated RGB color of the nearest original point
                mesh_vertex_colors[i] = original_point_colors[idx[0], :]
            # else: # Optional: Handle cases where no neighbor is found (shouldn't happen with k=1 unless tree is empty)
            #    pass

        except RuntimeError as e:
            print(f"!!! Runtime Error during KNN search at mesh vertex index {i} !!!")
            print(f"    Vertex causing error: {vert}")
            print(f"    Error message: {e}")
            errors_encountered += 1
            if errors_encountered > 20: # Stop spamming after too many errors
                print("...too many errors, stopping loop printout.")
                # Consider breaking the loop or exiting if this happens frequently
                # break
            # Assign a default color (e.g., magenta) to indicate the error location
            mesh_vertex_colors[i] = [1.0, 0.0, 1.0] # Magenta
            # continue # Skip assigning color from original points for this vertex

    # Assign the calculated/default colors to the mesh object
    mesh.vertex_colors = o3d.utility.Vector3dVector(mesh_vertex_colors)

    if errors_encountered > 0:
        print(f"WARNING: Encountered {errors_encountered} errors during KNN search. Problematic vertices colored magenta.")
    else:
        print("Color transfer complete.")

    print("Reconstructed mesh has vertex colors:", mesh.has_vertex_colors())

    print(f"Saving reconstructed mesh with vertex colors to {output_glb_path}...")
    # 7. Save the reconstructed mesh with vertex colors
    o3d.io.write_triangle_mesh(output_glb_path, mesh, write_vertex_colors=True)
    print("Processing complete!")

except FileNotFoundError:
    print(f"Error: Input file not found at {input_ply_path}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    import traceback
    traceback.print_exc()