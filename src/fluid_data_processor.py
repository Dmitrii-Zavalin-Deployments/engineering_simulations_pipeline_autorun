import numpy as np
import datetime
import os # To get base filenames for metadata

# Import functions from the new validator and calculator modules
from data_validators import validate_navier_stokes_data, validate_initial_data
from fluid_calculators import calculate_fluid_properties_at_timestep

def process_fluid_data(navier_stokes_data, initial_data, navier_stokes_filename, initial_data_filename):
    """
    Orchestrates the validation, calculation, and structuring of fluid simulation data.

    Args:
        navier_stokes_data (dict): Loaded data from navier_stokes_results.json.
        initial_data (dict): Loaded data from initial_data.json.
        navier_stokes_filename (str): Base filename of the Navier-Stokes input for metadata.
        initial_data_filename (str): Base filename of the initial data input for metadata.

    Returns:
        dict: The structured output data ready for JSON serialization, or None if processing fails.
    """
    # 1. Validate Navier-Stokes Data
    navier_stokes_validated = validate_navier_stokes_data(navier_stokes_data)
    if navier_stokes_validated is None:
        return None # Error message already printed by validator

    (time_points, nodes_coords, grid_shape, dx, dy, dz,
     velocity_history, pressure_history, num_x, num_y, num_z) = navier_stokes_validated

    # 2. Validate Initial Data
    # Pass pressure_history for ideal gas initial_C calculation
    initial_validated = validate_initial_data(initial_data, pressure_history)
    if initial_validated is None:
        return None # Error message already printed by validator
    
    (initial_density, R_specific_gas, gamma, initial_C, thermo_model) = initial_validated

    # 3. Perform Calculations for Each Time Step
    time_steps_data = []
    for t_idx, current_time in enumerate(time_points):
        step_data = calculate_fluid_properties_at_timestep(
            t_idx, current_time, velocity_history, pressure_history,
            num_x, num_y, num_z, thermo_model, initial_density, R_specific_gas, gamma, initial_C
        )
        if step_data is None and t_idx < len(time_points): # Only print if it's a critical error, not just a skipped warning
            # The calculator prints specific warnings for empty steps,
            # but None indicates a fatal error for that step or overall.
            # We need to decide if a single step error should stop the whole process.
            # For now, if calculate_fluid_properties_at_timestep returns None, we stop.
            print(f"Critical error during calculation for time step {t_idx}. Aborting further processing.")
            return None
        elif step_data is not None:
            time_steps_data.append(step_data)
    
    if not time_steps_data and len(time_points) > 0:
        print("Error: No valid time step data was generated. Check input or calculation logic.")
        return None

    # 4. Construct Final Output Structure
    # Assuming grid_info and metadata fields are consistent
    grid_origin = nodes_coords[0].tolist() # Assuming origin is the first node's coordinates

    output_data = {
        "volume_name": "FluidVolume",
        "metadata": {
            "source_navier_stokes": navier_stokes_filename,
            "source_initial_data": initial_data_filename,
            "generated_timestamp": datetime.datetime.now().isoformat()
        },
        "grid_info": {
            "dimensions": [num_x, num_y, num_z], # Conventionally, dimensions are X, Y, Z
            "voxel_size": [dx, dy, dz],
            "origin": grid_origin
        },
        "time_steps": time_steps_data
    }
    return output_data



