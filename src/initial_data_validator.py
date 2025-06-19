import numpy as np

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
        if not isinstance(initial_data['fluid_properties'], dict):
            print("Error: 'fluid_properties' in initial data must be a dictionary.")
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
        if not isinstance(thermodynamics, dict):
            print("Error: 'thermodynamics' in initial data must be a dictionary.")
            return None
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
            if not pressure_history or not isinstance(pressure_history, list) or len(pressure_history) == 0:
                print("Error: Pressure history is empty or malformed, cannot calculate initial_C for ideal gas model.")
                return None
            
            # This handles cases where pressure_history[0] might be an empty list or not a list of numbers
            if not isinstance(pressure_history[0], list) or not pressure_history[0]:
                 print("Error: First time step in pressure history is empty or malformed. Cannot calculate initial_C for ideal gas model.")
                 return None

            first_time_step_pressures = np.array(pressure_history[0])
            if first_time_step_pressures.size == 0:
                print("Error: First time step in pressure history is empty. Cannot calculate initial_C for ideal gas model.")
                return None
            
            # Ensure pressures are numeric before calculating mean
            if not np.issubdtype(first_time_step_pressures.dtype, np.number):
                print("Error: Pressure data contains non-numeric values. Cannot calculate initial_C.")
                return None

            avg_initial_pressure = np.mean(first_time_step_pressures)
            
            if avg_initial_pressure <= 0:
                print(f"Error: Average initial pressure ({avg_initial_pressure}) is not positive. Cannot calculate initial_C.")
                return None

            # Avoid ZeroDivisionError if initial_density is 0, though already checked for > 0
            if initial_density == 0:
                print("Error: Initial density is zero, cannot calculate initial_C.")
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



