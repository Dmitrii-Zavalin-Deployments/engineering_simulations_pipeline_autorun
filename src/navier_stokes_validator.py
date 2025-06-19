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
        # Ensure time_points is a list/array before converting
        if not isinstance(navier_stokes_data['time_points'], list):
            print("Error: 'time_points' in Navier-Stokes results must be a list.")
            return None
        time_points = np.array(navier_stokes_data['time_points'])
        if time_points.size == 0: # Using .size for numpy arrays
            print("Error: 'time_points' array is empty in Navier-Stokes results.")
            return None

        if 'mesh_info' not in navier_stokes_data:
            print("Error: 'mesh_info' key missing from Navier-Stokes results.")
            return None
        mesh_info = navier_stokes_data['mesh_info']
        if not isinstance(mesh_info, dict):
            print("Error: 'mesh_info' in Navier-Stokes results must be a dictionary.")
            return None

        required_mesh_keys = ['nodes_coords', 'grid_shape', 'dx', 'dy', 'dz']
        for key in required_mesh_keys:
            if key not in mesh_info:
                print(f"Error: '{key}' key missing from 'mesh_info' in Navier-Stokes results.")
                return None

        # Validate types for mesh_info elements before converting to numpy arrays
        if not isinstance(mesh_info['nodes_coords'], list):
            print("Error: 'nodes_coords' in 'mesh_info' must be a list.")
            return None
        nodes_coords = np.array(mesh_info['nodes_coords']) # (N, 3) array

        if not isinstance(mesh_info['grid_shape'], list):
            print("Error: 'grid_shape' in 'mesh_info' must be a list.")
            return None
        grid_shape = mesh_info['grid_shape']               # [Z, Y, X]

        dx = mesh_info['dx']
        dy = mesh_info['dy']
        dz = mesh_info['dz']

        if 'velocity_history' not in navier_stokes_data:
            print("Error: 'velocity_history' key missing from Navier-Stokes results.")
            return None
        if not isinstance(navier_stokes_data['velocity_history'], list):
            print("Error: 'velocity_history' in Navier-Stokes results must be a list.")
            return None
        velocity_history = navier_stokes_data['velocity_history'] # list of lists, each (N, 3)

        if 'pressure_history' not in navier_stokes_data:
            print("Error: 'pressure_history' key missing from Navier-Stokes results.")
            return None
        if not isinstance(navier_stokes_data['pressure_history'], list):
            print("Error: 'pressure_history' in Navier-Stokes results must be a list.")
            return None
        pressure_history = navier_stokes_data['pressure_history'] # list of lists, each (N,)

        # Validate dimensions consistency
        if not (len(velocity_history) == len(time_points) and len(pressure_history) == len(time_points)):
            print("Error: Inconsistent lengths of 'velocity_history', 'pressure_history', or 'time_points'.")
            return None
        
        # Check for empty velocity_history or pressure_history data for a time step
        # This check is crucial for the "empty_velocity_history.json" case
        if len(velocity_history) > 0 and (not isinstance(velocity_history[0], list) or not velocity_history[0]): # Check if list and non-empty
            print("Error: 'velocity_history' contains empty or malformed data for the first time point. Cannot process.")
            return None
        if len(pressure_history) > 0 and (not isinstance(pressure_history[0], list) or not pressure_history[0]): # Check if list and non-empty
            print("Error: 'pressure_history' contains empty or malformed data for the first time point. Cannot process.")
            return None

        # Validate grid dimensions
        if not (isinstance(grid_shape, list) and len(grid_shape) == 3 and all(isinstance(d, int) and d > 0 for d in grid_shape)):
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
        # Catches issues like np.array conversion of non-list, or reshape errors if data is malformed
        print(f"Error: Data value or shape error in Navier-Stokes data: {e}.")
        return None
    except Exception as e:
        print(f"Error: An unexpected error occurred during Navier-Stokes data validation: {e}")
        return None



