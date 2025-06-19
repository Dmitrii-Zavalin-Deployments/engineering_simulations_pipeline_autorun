import json
import os
import sys
# datetime is not directly used here anymore, can be removed if only used by fluid_data_processor

# Add src directory to the Python path for relative imports within src
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Only import the main orchestration function from the updated fluid_data_processor
from fluid_data_processor import process_fluid_data

def generate_fluid_volume_data_json(
    navier_stokes_results_path,
    initial_data_path,
    output_volume_json_path="data/testing-input-output/fluid_volume_data.json"
):
    """
    Processes fluid simulation data to generate volumetric density, velocity,
    and temperature fields per time step and saves them into a structured JSON file.

    Handles file loading/saving and orchestrates the data processing.

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

    navier_stokes_data = None
    initial_data = None

    # Load input data with robust error handling
    try:
        with open(navier_stokes_results_path, 'r') as f:
            navier_stokes_data = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: Navier-Stokes results file not found: {e}. Please ensure path is correct and file exists.")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Malformed Navier-Stokes results JSON: {e}. Please check file syntax.")
        return
    except Exception as e:
        print(f"Error: An unexpected error occurred while loading Navier-Stokes data: {e}")
        return

    try:
        with open(initial_data_path, 'r') as f:
            initial_data = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: Initial data file not found: {e}. Please ensure path is correct and file exists.")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Malformed initial data JSON: {e}. Please check file syntax.")
        return
    except Exception as e:
        print(f"Error: An unexpected error occurred while loading initial data: {e}")
        return

    # Extract original filenames for metadata (before passing to processor)
    navier_stokes_filename = os.path.basename(navier_stokes_results_path)
    initial_data_filename = os.path.basename(initial_data_path)

    # Process the loaded data using the orchestrated function
    output_data = process_fluid_data(navier_stokes_data, initial_data,
                                     navier_stokes_filename, initial_data_filename)
    
    if output_data is None:
        print("Final data processing failed. Aborting saving.")
        return # Return early if processing failed (error message already printed by sub-modules)

    # Save output data
    try:
        print(f"Saving volume data to {output_volume_json_path}")
        with open(output_volume_json_path, 'w') as f:
            json.dump(output_data, f, indent=4)
        print("Volume data JSON created successfully!")
    except Exception as e:
        print(f"Error: Failed to save output JSON file: {e}")
        return

# --- Main execution block for direct script run ---
if __name__ == "__main__":
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    navier_stokes_file = os.path.join(current_script_dir, "../tests/data/valid_input/navier_stokes_results.json")
    initial_data_file = os.path.join(current_script_dir, "../tests/data/valid_input/initial_data.json")
    output_volume_json = os.path.join(current_script_dir, "../data/testing-input-output/fluid_volume_data.json")

    main_output_dir = os.path.dirname(output_volume_json)
    if main_output_dir and not os.path.exists(main_output_dir):
        os.makedirs(main_output_dir)
        print(f"Created main output directory for direct run: {main_output_dir}")

    generate_fluid_volume_data_json(navier_stokes_file, initial_data_file, output_volume_json)



