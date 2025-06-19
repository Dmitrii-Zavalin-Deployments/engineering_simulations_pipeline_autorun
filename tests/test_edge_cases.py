# tests/test_edge_cases.py

import pytest
import os
import json

# Import the main function from src.generate_vdb_format
from src.generate_vdb_format import generate_fluid_volume_data_json


# Define a list of test cases: (filename, expected_error_fragment)
invalid_cases = [
    ("missing_fields_navier_stokes.json", "mesh_info"),
    ("malformed_initial_data.json", "malformed initial data json"),
    ("unsupported_model_initial_data.json", "Unsupported"),
    # This was updated previously; it should now correctly hit the "invalid voxel sizes" error
    ("negative_physical_values.json", "invalid voxel sizes"), # Or "must be positive numbers"
    # UPDATED: Changed expected_error_fragment for empty_velocity_history.json
    ("empty_velocity_history.json", "empty or malformed data for the first time point"),
]

@pytest.fixture
def invalid_input_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "invalid_input")

@pytest.fixture
def valid_input_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "valid_input")

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
    else:
        assert not output_path.exists(), "Output file created for a case that should have failed."



