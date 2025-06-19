import numpy as np

def validate_navier_stokes_data(navier_stokes_data):
    """
    Validates the structure and content of loaded Navier-Stokes data.

    Args:
        navier_stokes_data (dict): Loaded data from navier_stokes_results.json.

    Returns:
        tuple: (time_points, nodes_coords, grid_shape, dx, dy, dz,
                velocity_history, pressure_history, num_x, num_y, num_z)
               Or None if validation fails, printing errors.
    """
    try:
        if 'time_points' not in navier_stokes_data:
            print("Error: 'time_points' key missing from Navier-Stokes results.")
            return None
        time_points = np.array(navier_stokes_data['time_points'])
        if len(time_points) == 0:
            print("Error: 'time_points' array is empty in Navier-Stokes results.")
            return None

        if 'mesh_info' not in navier_stokes_data:
            print("Error: 'mesh_info' key missing from Navier-Stokes results.")
            return None
        mesh_info = navier_stokes_data['mesh_info']

        required_mesh_keys = ['nodes_coords', 'grid_shape', 'dx', 'dy', 'dz']
        for key in required_mesh_keys:
            if key not in mesh_info:
                print(f"Error: '{key}' key missing from 'mesh_info' in Navier-Stokes results.")
                return None

        nodes_coords = np.array(mesh_info['nodes_coords']) # (N, 3) array
        grid_shape = mesh_info['grid_shape']               # [Z, Y, X]
        dx = mesh_info['dx']
        dy = mesh_info['dy']
        dz = mesh_info['dz']

        if 'velocity_history' not in navier_stokes_data:
            print("Error: 'velocity_history' key missing from Navier-Stokes results.")
            return None
        velocity_history = navier_stokes_data['velocity_history'] # list of lists, each (N, 3)

        if 'pressure_history' not in navier_stokes_data:
            print("Error: 'pressure_history' key missing from Navier-Stokes results.")
            return None
        pressure_history = navier_stokes_data['pressure_history'] # list of lists, each (N,)

        # Validate dimensions consistency
        if not (len(velocity_history) == len(time_points) and len(pressure_history) == len(time_points)):
            print("Error: Inconsistent lengths of 'velocity_history', 'pressure_history', or 'time_points'.")
            return None
        
        # Check for empty velocity_history or pressure_history data for a time step
        if len(velocity_history) > 0 and (not isinstance(velocity_history[0], list) or len(velocity_history[0]) == 0):
            print("Error: 'velocity_history' contains empty or malformed data for the first time point. Cannot process.")
            return None
        if len(pressure_history) > 0 and (not isinstance(pressure_history[0], list) or len(pressure_history[0]) == 0):
            print("Error: 'pressure_history' contains empty or malformed data for the first time point. Cannot process.")
            return None

        # Validate grid dimensions
        if not (len(grid_shape) == 3 and all(d > 0 for d in grid_shape)):
            print(f"Error: Invalid 'grid_shape': {grid_shape}. Must be a list of 3 positive integers.")
            return None
        num_z, num_y, num_x = grid_shape
        
        # Validate voxel sizes
        if not (isinstance(dx, (int, float)) and dx > 0 and
                isinstance(dy, (int, float)) and dy > 0 and
                isinstance(dz, (int, float)) and dz > 0):
            print(f"Error: Invalid voxel sizes (dx:{dx}, dy:{dy}, dz:{dz}). Must be positive numbers.")
            return None
            
        # Validate nodes_coords shape
        expected_nodes = num_x * num_y * num_z
        if nodes_coords.shape[0] != expected_nodes:
             print(f"Error: Mismatch between number of nodes ({nodes_coords.shape[0]}) and grid_shape ({expected_nodes}).")
             return None
        if nodes_coords.shape[1] != 3:
             print(f"Error: 'nodes_coords' should have 3 columns (x, y, z). Found {nodes_coords.shape[1]}.")
             return

        return (time_points, nodes_coords, grid_shape, dx, dy, dz,
                velocity_history, pressure_history, num_x, num_y, num_z)

    except KeyError as e:
        print(f"Error: Missing expected key in Navier-Stokes data: {e}. Please check file structure.")
        return None
    except IndexError as e:
        print(f"Error: Data indexing error in Navier-Stokes data (e.g., empty lists or incorrect access): {e}.")
        return None
    except ValueError as e:
        print(f"Error: Data value or shape error in Navier-Stokes data: {e}.")
        return None
    except Exception as e:
        print(f"Error: An unexpected error occurred during Navier-Stokes data validation: {e}")
        return None

def validate_initial_data(initial_data, pressure_history):
    """
    Validates the structure and content of loaded initial data.

    Args:
        initial_data (dict): Loaded data from initial_data.json.
        pressure_history (list): The pressure history from Navier-Stokes data, needed for ideal gas initial_C calculation.

    Returns:
        tuple: (initial_density, R_specific_gas, gamma, initial_C, thermo_model)
               Or None if validation fails, printing errors.
    """
    initial_density = None
    R_specific_gas = None
    gamma = None
    initial_C = None
    thermo_model = None

    try:
        if 'fluid_properties' not in initial_data:
            print("Error: 'fluid_properties' key missing from initial data.")
            return None
        fluid_properties = initial_data['fluid_properties']

        if 'density' not in fluid_properties:
            print("Error: 'density' key missing from 'fluid_properties' in initial data.")
            return None
        initial_density = fluid_properties['density']
        if not isinstance(initial_density, (int, float)) or initial_density <= 0:
            print(f"Error: Invalid initial density: {initial_density}. Must be a positive number.")
            return None

        thermodynamics = fluid_properties.get('thermodynamics', {})
        thermo_model = thermodynamics.get('model', '').lower()

        if thermo_model == 'ideal_gas':
            required_thermo_keys = ['specific_gas_constant_J_per_kgK', 'adiabatic_index_gamma']
            for key in required_thermo_keys:
                if key not in thermodynamics:
                    print(f"Error: '{key}' key missing from 'thermodynamics' for ideal gas model.")
                    return None
            R_specific_gas = thermodynamics['specific_gas_constant_J_per_kgK']
            gamma = thermodynamics['adiabatic_index_gamma']

            if not (isinstance(R_specific_gas, (int, float)) and R_specific_gas > 0 and
                    isinstance(gamma, (int, float)) and gamma > 0):
                print(f"Error: Invalid R_specific_gas ({R_specific_gas}) or gamma ({gamma}). Must be positive numbers.")
                return None

            # Calculate initial_C
            if not pressure_history or len(pressure_history[0]) == 0:
                print("Error: Pressure history is empty, cannot calculate initial_C for ideal gas model.")
                return None
            
            first_time_step_pressures = np.array(pressure_history[0])
            if first_time_step_pressures.size == 0:
                print("Error: First time step in pressure history is empty. Cannot calculate initial_C for ideal gas model.")
                return None
            avg_initial_pressure = np.mean(first_time_step_pressures)
            
            if avg_initial_pressure <= 0:
                print(f"Error: Average initial pressure ({avg_initial_pressure}) is not positive. Cannot calculate initial_C.")
                return None

            initial_C = avg_initial_pressure / (initial_density ** gamma)
            print(f"Thermodynamics model: ideal_gas")
            print(f"Initial reference constant C (P/rho^gamma): {initial_C:.2f}")

        elif thermo_model == 'incompressible':
            print("Thermodynamics model: incompressible — using constant density and skipping temperature calculation.")
        else:
            print(f"Error: Unsupported thermodynamic model '{thermo_model}'. Only 'ideal_gas' and 'incompressible' are supported.")
            return None

    except KeyError as e:
        print(f"Error: Missing expected key in initial data: {e}. Please check file structure.")
        return None
    except IndexError as e:
        print(f"Error: Data indexing error in initial data (e.g., empty lists): {e}.")
        return None
    except ValueError as e:
        print(f"Error: Data value or type error in initial data: {e}.")
        return None
    except Exception as e:
        print(f"Error: An unexpected error occurred during initial data validation: {e}")
        return None

    return (initial_density, R_specific_gas, gamma, initial_C, thermo_model)


