import os
import sys
import pytest
import json

# Add src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from generate_vdb_format import generate_fluid_volume_data_json

invalid_cases = [
    ("missing_fields_navier_stokes.json", "time_points"),
    ("malformed_initial_data.json", "decode"),  # JSONDecodeError
    ("unsupported_model_initial_data.json", "Unsupported"),
    ("negative_physical_values.json", None),  # Should compute but possibly flag unphysical values
    ("empty_velocity_history.json", None)  # Should likely trigger reshape error or handle gracefully
]

@pytest.mark.parametrize("filename,expected_error_fragment", invalid_cases)
def test_edge_case_inputs(filename, expected_error_fragment, invalid_input_dir, tmp_path, capsys):
    navier_path = os.path.join(invalid_input_dir, filename)
    
    # Reuse a valid initial_data file unless this case is itself the malformed initial data
    if "initial_data" in filename:
        initial_path = navier_path
        navier_path = os.path.join("tests", "valid_input", "navier_stokes_results.json")
    else:
        initial_path = os.path.join("tests", "valid_input", "initial_data.json")
    
    output_path = tmp_path / "output.json"

    # Run and capture output/errors
    generate_fluid_volume_data_json(navier_path, initial_path, str(output_path))
    captured = capsys.readouterr()
    
    if expected_error_fragment:
        assert expected_error_fragment.lower() in captured.out.lower() + captured.err.lower(), (
            f"Expected error message to contain '{expected_error_fragment}', but got:\n{captured.out}"
        )
    else:
        # Output file might or might not be created; just check it doesn't crash
        assert True



