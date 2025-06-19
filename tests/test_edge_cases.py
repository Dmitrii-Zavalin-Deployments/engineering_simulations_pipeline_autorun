import os
import sys
import pytest
import json

# Add src directory to Python path for module discovery
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from generate_vdb_format import generate_fluid_volume_data_json

# List of known edge case files + expected error message fragment (or None if flexible)
invalid_cases = [
    ("missing_fields_navier_stokes.json", "time_points"),
    ("malformed_initial_data.json", "decode"),
    ("unsupported_model_initial_data.json", "Unsupported"),
    ("negative_physical_values.json", None),
    ("empty_velocity_history.json", None)
]

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
    else:
        # Optional refinement: check that the file was created (or at least didn't crash)
        assert True  # Flexible case: script should not raise or terminate unexpectedly



