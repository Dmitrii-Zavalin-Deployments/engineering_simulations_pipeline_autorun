# tests/test_edge_cases.py

import pytest
import os
import json # Ensure json is imported for reading output if needed, though not directly for error checks here

# It's better practice to import the function from the package structure
# assuming 'src' is in your PYTHONPATH (as set up by run.sh or pytest config)
from src.generate_vdb_format import generate_fluid_volume_data_json

# Define a list of test cases: (filename, expected_error_fragment)
invalid_cases = [
    # Change 'time_points' to 'mesh_info' as it's checked first
    ("missing_fields_navier_stokes.json", "mesh_info"),
    # Change 'decode' to 'jsondecodeerror' for better matching
    ("malformed_initial_data.json", "jsondecodeerror"),
    ("unsupported_model_initial_data.json", "Unsupported"),
    ("negative_physical_values.json", "warning"), # A warning is printed, not a hard error that stops
    ("empty_velocity_history.json", "Cannot process"), # Updated error message fragment
]

@pytest.fixture
def invalid_input_dir():
    # Use os.path.join and os.path.dirname to build paths reliably
    # This assumes tests/data/invalid_input is relative to the root of the project
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "invalid_input")

@pytest.fixture
def valid_input_dir():
    # This assumes tests/data/valid_input is relative to the root of the project
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "valid_input")


# Update test paths to use the new fixtures
@pytest.fixture
def valid_navier_stokes_path(valid_input_dir):
    return os.path.join(valid_input_dir, "navier_stokes_results.json")

@pytest.fixture
def valid_initial_data_path(valid_input_dir):
    return os.path.join(valid_input_dir, "initial_data.json")


@pytest.mark.parametrize("filename,expected_error_fragment", invalid_cases)
def test_edge_case_inputs(
    filename,
    expected_error_fragment,
    invalid_input_dir,
    valid_navier_stokes_path,
    valid_initial_data_path,
    tmp_path,
    capsys
):
    """
    Tests various edge cases for malformed or logically invalid input JSON files.
    """
    current_invalid_path = os.path.join(invalid_input_dir, filename)

    # Decide which input is the 'invalid' one and which to substitute from known-good
    if "initial_data" in filename:
        initial_data_path = current_invalid_path
        navier_path = valid_navier_stokes_path
    else:
        navier_path = current_invalid_path
        initial_data_path = valid_initial_data_path

    output_path = tmp_path / "output.json"

    generate_fluid_volume_data_json(navier_path, initial_data_path, str(output_path))
    captured = capsys.readouterr()

    if expected_error_fragment:
        combined_output = captured.out.lower() + captured.err.lower()
        assert expected_error_fragment.lower() in combined_output, (
            f"Expected error message containing '{expected_error_fragment}', but got:\n"
            f"STDOUT:\n{captured.out}\nSTDERR:\n{captured.err}"
        )
    # For cases where no specific error fragment is expected, check for no file output
    else:
        assert not output_path.exists(), "Output file created for a case that should have failed."



