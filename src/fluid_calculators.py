import numpy as np

def calculate_fluid_properties_at_timestep(
    t_idx, current_time, velocity_history, pressure_history,
    num_x, num_y, num_z, thermo_model, initial_density, R_specific_gas, gamma, initial_C
):
    """
    Calculates density, velocity, and temperature for a given time step.

    Args:
        t_idx (int): Current time step index.
        current_time (float): Current simulation time.
        velocity_history (list): Full velocity history data.
        pressure_history (list): Full pressure history data.
        num_x, num_y, num_z (int): Grid dimensions.
        thermo_model (str): Thermodynamic model ('ideal_gas' or 'incompressible').
        initial_density (float): Initial reference density.
        R_specific_gas (float): Specific gas constant (for ideal_gas).
        gamma (float): Adiabatic index (for ideal_gas).
        initial_C (float): Initial constant C (P/rho^gamma) (for ideal_gas).

    Returns:
        dict: Dictionary containing 'time', 'frame', 'density_data', 'velocity_data', 'temperature_data'
              for the current time step, or None if a critical error occurs.
    """
    try:
        if t_idx >= len(velocity_history) or t_idx >= len(pressure_history):
            print(f"Warning: Data for time step {t_idx} is missing. Skipping this time step.")
            return None # Indicate to skip this step

        current_velocities_flat = np.array(velocity_history[t_idx])
        current_pressures_flat = np.array(pressure_history[t_idx])

        if current_velocities_flat.size == 0 or current_pressures_flat.size == 0:
            print(f"Warning: Empty velocity or pressure data for time step {t_idx}. Skipping calculations for this step.")
            # Return empty data for this step
            return {
                "time": float(current_time),
                "frame": t_idx,
                "density_data": [],
                "velocity_data": [],
                "temperature_data": [],
            }

        try:
            current_velocities_grid = current_velocities_flat.reshape(num_z, num_y, num_x, 3)
            current_pressures_grid = current_pressures_flat.reshape(num_z, num_y, num_x)
        except ValueError as e:
            print(f"Error: Could not reshape velocity/pressure data for time step {t_idx}. Mismatch in dimensions or data length: {e}")
            return None # Critical error, cannot proceed

        density_grid = None
        temperature_grid = None

        if thermo_model == 'ideal_gas':
            if initial_C is None or initial_C == 0:
                print("Error: initial_C is invalid for ideal gas calculation. Cannot compute density/temperature.")
                return None
            if gamma is None or gamma == 0:
                print("Error: Adiabatic index gamma is invalid. Cannot compute density.")
                return None
            if R_specific_gas is None or R_specific_gas == 0:
                print("Error: Specific gas constant R is invalid. Cannot compute temperature.")
                return None

            with np.errstate(divide='ignore', invalid='ignore'):
                clamped_pressures = np.maximum(current_pressures_grid, 1e-9) # Clamp to small positive
                density_grid = (clamped_pressures / initial_C) ** (1 / gamma)
                density_grid[np.isnan(density_grid)] = 0.0
                density_grid[np.isinf(density_grid)] = 0.0
                density_grid[density_grid < 0] = 0.0

            epsilon = 1e-9
            temperature_grid = np.where(
                density_grid > epsilon,
                clamped_pressures / (density_grid * R_specific_gas),
                0.0
            )
            temperature_grid[np.isnan(temperature_grid)] = 0.0
            temperature_grid[np.isinf(temperature_grid)] = 0.0
            temperature_grid[temperature_grid < 0] = 0.0

        elif thermo_model == 'incompressible':
            density_grid = np.full_like(current_pressures_grid, initial_density)
            temperature_grid = np.zeros_like(current_pressures_grid)
        # No 'else' needed here, as unsupported models are caught during validation

        density_data_flat = density_grid.flatten().tolist()
        velocity_data_flat = current_velocities_grid.reshape(-1, 3).tolist()
        temperature_data_flat = temperature_grid.flatten().tolist()

        return {
            "time": float(current_time),
            "frame": t_idx,
            "density_data": density_data_flat,
            "velocity_data": velocity_data_flat,
            "temperature_data": temperature_data_flat,
        }
    except Exception as e:
        print(f"Error during calculation for time step {t_idx}: {e}")
        return None # Critical error, stop processing this time step



