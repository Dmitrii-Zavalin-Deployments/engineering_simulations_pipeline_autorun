import json
import numpy as np
from scipy.interpolate import griddata
import bpy # This module is only available when running inside Blender
import os

def convert_fluid_data_to_blender_vdb(
    navier_stokes_results_path,
    initial_data_path,
    output_blend_path="fluid_volume_animation.blend",
    specific_gas_constant_R=287.058 # J/(kg·K) for dry air, if not in initial_data.json
):
    """
    Converts fluid simulation data from JSON files into Blender Volume objects
    and saves them in a .blend file. This script must be run inside Blender.

    Args:
        navier_stokes_results_path (str): Path to the navier_stokes_results.json file.
        initial_data_path (str): Path to the initial_data.json file.
        output_blend_path (str): Path to save the generated .blend file.
        specific_gas_constant_R (float): Specific gas constant for the fluid.
                                         Used for ideal gas law calculations.
    """
    print(f"Loading data from {navier_stokes_results_path} and {initial_data_path}")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_blend_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # 1. Load Input Data
    try:
        with open(navier_stokes_results_path, 'r') as f:
            navier_stokes_data = json.load(f)

        with open(initial_data_path, 'r') as f:
            initial_data = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: Input file not found: {e}. Please ensure paths are correct.")
        return

    # Extract relevant data
    time_points = np.array(navier_stokes_data['time_points'])
    velocity_history = np.array(navier_stokes_data['velocity_history'])
    pressure_history = np.array(navier_stokes_data['pressure_history'])
    nodes_coords = np.array(navier_stokes_data['mesh_info']['nodes_coords'])
    grid_shape = navier_stokes_data['mesh_info']['grid_shape'] # [z, y, x] from the JSON example's structure
    dx = navier_stokes_data['mesh_info']['dx']
    dy = navier_stokes_data['mesh_info']['dy']
    dz = navier_stokes_data['mesh_info']['dz']

    initial_density = initial_data['fluid_properties']['density']
    
    print(f"Grid shape (Z, Y, X): {grid_shape}")
    print(f"Voxel sizes: dx={dx}, dy={dy}, dz={dz}")
    print(f"Initial fluid density: {initial_density} kg/m^3")
    print(f"Specific Gas Constant (R): {specific_gas_constant_R} J/(kg·K)")

    # Define the coordinates for the centers of our target voxels
    min_x, min_y, min_z = np.min(nodes_coords, axis=0)
    max_x, max_y, max_z = np.max(nodes_coords, axis=0)

    num_x_voxels = grid_shape[2]
    num_y_voxels = grid_shape[1]
    num_z_voxels = grid_shape[0]

    target_x = np.linspace(min_x + 0.5 * dx, min_x + (num_x_voxels - 0.5) * dx, num_x_voxels)
    target_y = np.linspace(min_y + 0.5 * dy, min_y + (num_y_voxels - 0.5) * dy, num_y_voxels)
    target_z = np.linspace(min_z + 0.5 * dz, min_z + (num_z_voxels - 0.5) * dz, num_z_voxels)

    # Create an array of all target voxel points for interpolation
    # Ensure this order matches Blender's expected VDB indexing if direct assignment is used.
    # Blender VDB expects (X, Y, Z) order for its internal voxel data.
    TX_grid, TY_grid, TZ_grid = np.meshgrid(target_x, target_y, target_z, indexing='ij') # Y, X, Z arrays
    target_points_for_interp = np.vstack([TX_grid.ravel(), TY_grid.ravel(), TZ_grid.ravel()]).T # (N_voxels, 3) where columns are X, Y, Z
    
    source_points = nodes_coords # (N_nodes, 3) where columns are X, Y, Z (assuming consistent order)

    print(f"Created target grid with {len(target_points_for_interp)} voxels for interpolation.")

    # Thermodynamic constants and base state
    adiabatic_index_gamma = 1.4 # For dry air
    P_inlet_ref = initial_data['boundary_conditions']['inlet']['pressure']
    base_pressure = P_inlet_ref
    base_density = initial_density
    T_base_implied = base_pressure / (base_density * specific_gas_constant_R)
    print(f"Implied base temperature for initial density at inlet pressure: {T_base_implied:.2f} K")

    # --- Blender Setup ---
    # Clear existing scene data to start fresh (optional, but good for headless runs)
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Create a new Empty object to hold the Volume object
    # This empty will be the parent of our volume object and will have the object-level transform.
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    volume_parent_obj = bpy.context.object
    volume_parent_obj.name = "Fluid_Volume_Parent"

    # Set Blender's animation start/end frames
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = len(time_points) - 1

    # --- Process Each Time Step ---
    for t_idx, current_time in enumerate(time_points):
        print(f"\nProcessing time step {t_idx+1}/{len(time_points)} (Time: {current_time:.2f}s)")

        current_velocities = velocity_history[t_idx]
        current_pressures = pressure_history[t_idx]

        # 2. Voxelize Velocity Field (Trilinear Interpolation)
        # Interpolate each component (U, V, W) separately
        interp_vx = griddata(source_points, current_velocities[:, 0], target_points_for_interp, method='linear')
        interp_vy = griddata(source_points, current_velocities[:, 1], target_points_for_interp, method='linear')
        interp_vz = griddata(source_points, current_velocities[:, 2], target_points_for_interp, method='linear')
        voxel_velocities_frame = np.column_stack([interp_vx, interp_vy, interp_vz])
        voxel_velocities_frame = np.nan_to_num(voxel_velocities_frame, nan=0.0)

        # 3. Compute Density and Temperature Fields (Adiabatic Ideal Gas Model)
        interp_pressure_frame = griddata(source_points, current_pressures, target_points_for_interp, method='linear')
        interp_pressure_frame = np.nan_to_num(interp_pressure_frame, nan=initial_data['boundary_conditions']['outlet']['pressure'])

        voxel_densities_frame = base_density * (interp_pressure_frame / base_pressure)**(1/adiabatic_index_gamma)
        voxel_temperatures_frame = T_base_implied * (interp_pressure_frame / base_pressure)**((adiabatic_index_gamma-1)/adiabatic_index_gamma)
        
        # Ensure values are non-negative
        voxel_densities_frame[voxel_densities_frame < 0] = 0
        voxel_temperatures_frame[voxel_temperatures_frame < 0] = 0

        # Reshape the 1D interpolated data back into a 3D grid for Blender's volume grid.
        # Blender's volume grid data is typically accessed in (X, Y, Z) order.
        # If your grid_shape is [Z, Y, X], reshape accordingly.
        # The meshgrid was created with 'ij' indexing, which yields (Y, X, Z) for 1D arrays
        # if the input was (x, y, z).
        # Let's verify the reshape order:
        # target_x, target_y, target_z order in meshgrid leads to (X, Y, Z) for internal loop.
        # So, reshape to (num_z_voxels, num_y_voxels, num_x_voxels) based on original grid_shape.
        
        # When populating Blender's VDB grid, we need to iterate (x, y, z)
        # The reshaped data should be (num_x_voxels, num_y_voxels, num_z_voxels) for direct assignment.
        # Transpose to (X, Y, Z) order for Blender's `grid.point_set`
        
        # Correct reshaping:
        reshaped_density = voxel_densities_frame.reshape(num_z_voxels, num_y_voxels, num_x_voxels)
        reshaped_velocity_x = voxel_velocities_frame[:, 0].reshape(num_z_voxels, num_y_voxels, num_x_voxels)
        reshaped_velocity_y = voxel_velocities_frame[:, 1].reshape(num_z_voxels, num_y_voxels, num_x_voxels)
        reshaped_velocity_z = voxel_velocities_frame[:, 2].reshape(num_z_voxels, num_y_voxels, num_x_voxels)
        reshaped_temperature = voxel_temperatures_frame.reshape(num_z_voxels, num_y_voxels, num_x_voxels)

        # Transpose to (X, Y, Z) for Blender's typical internal representation
        # Assuming grid_shape is [Z, Y, X] -> transpose to (X, Y, Z)
        final_density_grid_data = np.transpose(reshaped_density, (2, 1, 0)) # (X, Y, Z)
        final_velocity_x_grid_data = np.transpose(reshaped_velocity_x, (2, 1, 0))
        final_velocity_y_grid_data = np.transpose(reshaped_velocity_y, (2, 1, 0))
        final_velocity_z_grid_data = np.transpose(reshaped_velocity_z, (2, 1, 0))
        final_temperature_grid_data = np.transpose(reshaped_temperature, (2, 1, 0))

        # Create/Get Blender Volume object for this frame
        # Blender's Volume object is tied to an object in the scene.
        # We'll create one Volume object and update its grids per frame.
        if t_idx == 0:
            # Create a new Volume data block
            volume_data = bpy.data.volumes.new(name="Fluid_Volume_Data", type='VDB')
            
            # Create a new object for the volume and link the data
            volume_obj = bpy.data.objects.new(name="Fluid_Volume", object_data=volume_data)
            bpy.context.collection.objects.link(volume_obj)
            volume_obj.parent = volume_parent_obj # Link to parent for scene transform
            volume_obj.location = (min_x, min_y, min_z) # Set object origin to min corner of fluid domain
            
            # Set object scale (voxel size)
            volume_obj.scale = (dx, dy, dz)
            
            # Make sure it's the active object for context operations later if needed
            bpy.context.view_layer.objects.active = volume_obj
            volume_obj.select_set(True)
        else:
            # For subsequent frames, get the existing volume object
            volume_obj = bpy.data.objects['Fluid_Volume']
            volume_data = volume_obj.data

        # Add/update grids for the current frame
        # Blender's volume grids have `points` attribute for setting voxel values
        # They expect (X, Y, Z) indices and values.
        
        # Density Grid
        # Check if 'density' grid exists, if not, create it
        if 'density' not in volume_data.grids:
            density_grid = volume_data.grids.new(name="density", type='FLOAT')
            density_grid.dimensions = (num_x_voxels, num_y_voxels, num_z_voxels)
        else:
            density_grid = volume_data.grids['density']
        
        # Populate the grid. This is the heavy part.
        # Blender's grid.points.set() expects a flat list of floats.
        # So we flatten our (X, Y, Z) NumPy array.
        density_grid.points.as_pointer().contents.type = 'FLOAT' # Ensure type is float
        density_grid.points.foreach_set('value', final_density_grid_data.ravel().astype(np.float32))
        
        # Insert keyframe for density grid
        density_grid.keyframe_insert(data_path="points", frame=t_idx)

        # Velocity Grid (Requires 3 float grids or a custom vector type if supported)
        # Blender typically represents vector fields as separate X, Y, Z float grids
        # Or sometimes a single Vec3f grid depending on version/context.
        # For broader compatibility, let's create X, Y, Z components.
        
        # Grid X
        if 'velocity.X' not in volume_data.grids:
            vel_x_grid = volume_data.grids.new(name="velocity.X", type='FLOAT')
            vel_x_grid.dimensions = (num_x_voxels, num_y_voxels, num_z_voxels)
        else:
            vel_x_grid = volume_data.grids['velocity.X']
        vel_x_grid.points.foreach_set('value', final_velocity_x_grid_data.ravel().astype(np.float32))
        vel_x_grid.keyframe_insert(data_path="points", frame=t_idx)

        # Grid Y
        if 'velocity.Y' not in volume_data.grids:
            vel_y_grid = volume_data.grids.new(name="velocity.Y", type='FLOAT')
            vel_y_grid.dimensions = (num_x_voxels, num_y_voxels, num_z_voxels)
        else:
            vel_y_grid = volume_data.grids['velocity.Y']
        vel_y_grid.points.foreach_set('value', final_velocity_y_grid_data.ravel().astype(np.float32))
        vel_y_grid.keyframe_insert(data_path="points", frame=t_idx)

        # Grid Z
        if 'velocity.Z' not in volume_data.grids:
            vel_z_grid = volume_data.grids.new(name="velocity.Z", type='FLOAT')
            vel_z_grid.dimensions = (num_x_voxels, num_y_voxels, num_z_voxels)
        else:
            vel_z_grid = volume_data.grids['velocity.Z']
        vel_z_grid.points.foreach_set('value', final_velocity_z_grid_data.ravel().astype(np.float32))
        vel_z_grid.keyframe_insert(data_path="points", frame=t_idx)

        # Temperature Grid
        if 'temperature' not in volume_data.grids:
            temperature_grid = volume_data.grids.new(name="temperature", type='FLOAT')
            temperature_grid.dimensions = (num_x_voxels, num_y_voxels, num_z_voxels)
        else:
            temperature_grid = volume_data.grids['temperature']
        temperature_grid.points.foreach_set('value', final_temperature_grid_data.ravel().astype(np.float32))
        temperature_grid.keyframe_insert(data_path="points", frame=t_idx)

        # Set current frame for keyframing
        bpy.context.scene.frame_current = t_idx
        
    # --- Save the .blend file ---
    bpy.ops.wm.save_as_mainfile(filepath=output_blend_path)
    print(f"\nSuccessfully created and saved Blender file with VDB animation: '{output_blend_path}'")

    # --- Optional: Export VDB sequence (Adds complexity for GitHub Actions) ---
    # If you absolutely need .vdb files on disk, Blender can export them.
    # This involves setting up export paths and possibly iterating over frames.
    # This adds significant complexity to the GitHub Actions workflow as it means
    # Blender also needs to handle writing external files, and path management.
    # For now, let's stick to saving the .blend. If needed, this section can be added.
    # Example (pseudocode):
    # output_vdb_sequence_dir = os.path.join(output_dir, "vdb_export_sequence")
    # os.makedirs(output_vdb_sequence_dir, exist_ok=True)
    # bpy.context.scene.render.filepath = os.path.join(output_vdb_sequence_dir, "fluid_volume_")
    # bpy.context.scene.render.image_settings.file_format = 'OPENEXR_MULTILAYER' # Or VDB
    # bpy.context.scene.render.exr_data.use_volume_grids = True # For OpenEXR that can store VDB
    # bpy.ops.render.render(animation=True) # This will render frames/VDBs if setup correctly


# --- Main execution when run directly by Blender's Python ---
# Note: When run with `blender --background --python script.py`, the script
# will be executed as if it were an addon or a text editor script.
# `__name__ == "__main__"` might not always be true in that context,
# but it's good practice.

if __name__ == "__main__":
    # Get current script directory for relative paths (important for Blender headless)
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    
    navier_stokes_file = os.path.join(current_script_dir, "data/testing-input-output/navier_stokes_results.json")
    initial_data_file = os.path.join(current_script_dir, "data/testing-input-output/initial_data.json")
    output_blend_file = os.path.join(current_script_dir, "fluid_volume_animation.blend")

    # Create dummy files for demonstration if they don't exist
    # (This part would typically be done by your test setup before Blender runs)
    json_data_dir = os.path.join(current_script_dir, "data/testing-input-output")
    os.makedirs(json_data_dir, exist_ok=True)

    if not os.path.exists(navier_stokes_file):
        # Create dummy data for testing purposes
        dummy_navier_stokes_data = {
            "time_points": [0.01, 0.02, 0.03],
            "velocity_history": [
                [[0.1, 0.0, 0.0], [0.11, 0.01, 0.0], [0.12, 0.02, 0.0]] * 208, # 624 nodes
                [[0.15, 0.0, 0.0], [0.16, 0.01, 0.0], [0.17, 0.02, 0.0]] * 208,
                [[0.2, 0.0, 0.0], [0.21, 0.01, 0.0], [0.22, 0.02, 0.0]] * 208
            ],
            "pressure_history": [
                [101325.0, 101320.0, 101315.0] * 208,
                [101400.0, 101395.0, 101390.0] * 208,
                [101500.0, 101495.0, 101490.0] * 208
            ],
            "mesh_info": {
                "nodes": 624,
                "nodes_coords": [[x, y, z] for z in np.linspace(0, 1, 6) for y in np.linspace(0, 1, 8) for x in np.linspace(0, 1, 13)][:624],
                "grid_shape": [6, 8, 13], # Z, Y, X
                "dx": 1.0 / 12.0, # (1 - 0) / (13 - 1)
                "dy": 1.0 / 7.0,  # (1 - 0) / (8 - 1)
                "dz": 1.0 / 5.0   # (1 - 0) / (6 - 1)
            }
        }
        with open(navier_stokes_file, 'w') as f:
            json.dump(dummy_navier_stokes_data, f, indent=4)
        print(f"Created dummy '{navier_stokes_file}'")

    if not os.path.exists(initial_data_file):
        dummy_initial_data = {
            "boundary_conditions": {
                "inlet": {
                    "velocity": [1.0, 0.0, 0.0],
                    "pressure": 101325.0
                },
                "outlet": {
                    "pressure": 101000.0
                },
                "wall": {
                    "no_slip": True
                }
            },
            "fluid_properties": {
                "density": 1.225,
                "viscosity": 1.81e-5
            },
            "simulation_parameters": {
                "time_step": 0.01,
                "total_time": 5.0,
                "solver": "explicit"
            }
        }
        with open(initial_data_file, 'w') as f:
            json.dump(dummy_initial_data, f, indent=4)
        print(f"Created dummy '{initial_data_file}'")

    convert_fluid_data_to_blender_vdb(navier_stokes_file, initial_data_file)
