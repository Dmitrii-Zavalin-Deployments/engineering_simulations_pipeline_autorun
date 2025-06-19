# tests/test_io.py

import os
import json
import pytest
from src.generate_vdb_format import generate_fluid_volume_data_json

# Fixture to load JSON content (remains as is)
@pytest.fixture
def load_json():
    def _loader(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return _loader

# New fixtures for reliable pathing in tests
@pytest.fixture
def get_test_data_path():
    """Returns the absolute path to the 'tests/data' directory."""
    # This gets the directory of the current test file (tests/)
    current_test_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_test_dir, "data")

@pytest.fixture
def valid_navier_stokes_path(get_test_data_path):
    return os.path.join(get_test_data_path, "valid_input", "navier_stokes_results.json")

@pytest.fixture
def valid_initial_data_path(get_test_data_path):
    return os.path.join(get_test_data_path, "valid_input", "initial_data.json")


def test_output_json_structure(tmp_path, load_json, valid_navier_stokes_path, valid_initial_data_path):
    """Basic I/O test: Ensure that output JSON file is created and has expected keys."""
    # Paths are now correctly provided by fixtures
    navier_path = valid_navier_stokes_path
    initial_path = valid_initial_data_path
    output_path = tmp_path / "fluid_volume_data.json"

    # Run processing function
    generate_fluid_volume_data_json(navier_path, initial_path, str(output_path))

    # Confirm file exists
    assert output_path.exists(), "Expected output file not created."

    # Load output and check structure
    output_data = load_json(output_path)

    assert "volume_name" in output_data
    assert "metadata" in output_data
    assert "grid_info" in output_data
    assert "time_steps" in output_data

    # Check basic grid_info properties
    assert "dimensions" in output_data["grid_info"]
    assert "voxel_size" in output_data["grid_info"]
    assert "origin" in output_data["grid_info"]

    # Check basic time_steps properties
    assert isinstance(output_data["time_steps"], list)
    assert len(output_data["time_steps"]) > 0

    first_step = output_data["time_steps"][0]
    assert "time" in first_step
    assert "frame" in first_step
    assert "density_data" in first_step
    assert "velocity_data" in first_step
    assert "temperature_data" in first_step

    # Optional: Check data types or ranges more rigorously if needed
    assert isinstance(first_step["density_data"], list)
    assert isinstance(first_step["velocity_data"], list)
    assert isinstance(first_step["temperature_data"], list)

    # Example: Check that density/velocity/temperature data are not empty if there's actual mesh data
    assert len(first_step["density_data"]) > 0
    assert len(first_step["velocity_data"]) > 0
    assert len(first_step["temperature_data"]) > 0



