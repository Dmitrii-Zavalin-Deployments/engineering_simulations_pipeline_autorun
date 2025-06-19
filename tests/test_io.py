import os
import sys
import json
import pytest

# Add src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from generate_vdb_format import generate_fluid_volume_data_json

def test_output_json_structure(tmp_path, load_json):
    """Basic I/O test: Ensure that output JSON file is created and has expected keys."""
    # Paths
    navier_path = os.path.join("tests", "valid_input", "navier_stokes_results.json")
    initial_path = os.path.join("tests", "valid_input", "initial_data.json")
    output_path = tmp_path / "fluid_volume_data.json"

    # Run processing function
    generate_fluid_volume_data_json(navier_path, initial_path, str(output_path))

    # Confirm file exists
    assert output_path.exists(), "Expected output file not created."

    # Load and inspect structure
    data = load_json(output_path)

    assert "volume_name" in data
    assert "grid_info" in data
    assert "time_steps" in data
    assert isinstance(data["time_steps"], list)
    assert len(data["time_steps"]) > 0

    # Check inner fields in first frame
    step = data["time_steps"][0]
    assert "density_data" in step
    assert "velocity_data" in step
    assert "temperature_data" in step
    assert "time" in step
    assert "frame" in step



