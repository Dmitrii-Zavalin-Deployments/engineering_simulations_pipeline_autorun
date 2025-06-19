import json
import numpy as np
import os

def generate_fluid_volume_data_json(
    navier_stokes_results_path,
    initial_data_path,
    output_volume_json_path="data/testing-input-output/fluid_volume_data.json"
):
    """
    Processes fluid simulation data to generate volumetric density, velocity,
    and temperature fields per time step and saves them into a structured JSON file.

    Args:
        navier_stokes_results_path (str): Path to the navier_stokes_results.json file.
        initial_data_path (str): Path to the initial_data.json file.
        output_volume_json_path (str): Path to save the generated fluid_volume_data.json file.
    """
    print(f"Loading data from {navier_stokes_results_path} and {initial_data_path}")

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_volume_json_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # Load input data
    try:
        with open(navier_stokes_results_path, 'r') as f:
            navier_stokes_data = json.load(f)
        with open(initial_data_path, 'r') as f:
            initial_data = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: Input file not found: {e}. Please ensure paths are correct and files exist.")
        return

    time_points = np.array(navier_stokes_data['time_points'])
    nodes_coords = np.array(navier_stokes_data['mesh_info']['nodes_coords'])  # (N, 3) array
    grid_shape = navier_stokes_data['mesh_info']['grid_shape']  # [Z, Y, X]
    dx = navier_stokes_data['mesh_info']['dx']
    dy = navier_stokes_data['mesh_info']['dy']
    dz = navier_stokes_data['mesh_info']['dz']
    
    velocity_history = navier_stokes_data['velocity_history']  # list of lists, each (N, 3)
    pressure_history = navier_stokes_data['pressure_history']  # list of lists, each (N,)

    # Fluid properties
    initial_density = initial_data['fluid_properties']['density']
    thermodynamics = initial_data['fluid_properties'].get('thermodynamics', {})
    thermo_model = thermodynamics.get('model', '').lower()

    if thermo_model == 'ideal_gas':
        R_specific_gas = thermodynamics.get('specific_gas_constant_J_per_kgK')
        gamma = thermodynamics.get('adiabatic_index_gamma')
        avg_initial_pressure = np.mean(pressure_history[0])
        initial_C = avg_initial_pressure / (initial_density ** gamma)
        print(f"Thermodynamics model: ideal_gas")
        print(f"Initial reference constant C (P/rho^gamma): {initial_C:.2f}")
    elif thermo_model == 'incompressible':
        R_specific_gas = None
        gamma = None
        initial_C = None
        print("Thermodynamics model: incompressible — using constant density and skipping temperature calculation.")
    else:
        print(f"Error: Unsupported thermodynamic model '{thermo_model}'.")
        return

    num_z, num_y, num_x = grid_shape
    grid_origin = nodes_coords[0].tolist()

    time_steps_data = []

    for t_idx, current_time in enumerate(time_points):
        current_velocities_flat = np.array(velocity_history[t_idx])
        current_pressures_flat = np.array(pressure_history[t_idx])

        current_velocities_grid = current_velocities_flat.reshape(num_z, num_y, num_x, 3)
        current_pressures_grid = current_pressures_flat.reshape(num_z, num_y, num_x)

        if thermo_model == 'ideal_gas':
            density_grid = (current_pressures_grid / initial_C) ** (1 / gamma)
            temperature_grid = np.where(
                density_grid > 1e-9,
                current_pressures_grid / (density_grid * R_specific_gas),
                0.0
            )
        elif thermo_model == 'incompressible':
            density_grid = np.full_like(current_pressures_grid, initial_density)
            temperature_grid = np.zeros_like(current_pressures_grid)

        density_data_flat = density_grid.flatten().tolist()
        velocity_data_flat = current_velocities_grid.reshape(-1, 3).tolist()
        temperature_data_flat = temperature_grid.flatten().tolist()

        time_steps_data.append({
            "time": float(current_time),
            "frame": t_idx,
            "density_data": density_data_flat,
            "velocity_data": velocity_data_flat,
            "temperature_data": temperature_data_flat,
        })

    output_data = {
        "volume_name": "FluidVolume",
        "grid_info": {
            "dimensions": [num_x, num_y, num_z],
            "voxel_size": [dx, dy, dz],
            "origin": grid_origin
        },
        "time_steps": time_steps_data
    }

    print(f"Saving volume data to {output_volume_json_path}")
    with open(output_volume_json_path, 'w') as f:
        json.dump(output_data, f, indent=4)
    print("Volume data JSON created successfully!")

# --- Main execution block ---
if __name__ == "__main__":
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    navier_stokes_file = os.path.join(current_script_dir, "../data/testing-input-output/navier_stokes_results.json")
    initial_data_file = os.path.join(current_script_dir, "../data/testing-input-output/initial_data.json")
    output_volume_json = os.path.join(current_script_dir, "../data/testing-input-output/fluid_volume_data.json")
    generate_fluid_volume_data_json(navier_stokes_file, initial_data_file, output_volume_json)



