import os
import sys
import json
import pytest

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from generate_vdb_format import generate_fluid_volume_data_json

def test_full_pipeline_runs_and_generates_output(
    valid_navier_stokes_path,
    valid_initial_data_path,
    tmp_path,
    load_json
):
    """
    Integration test: Run the entire processing pipeline on valid input
    and verify output file, structure, and content sanity.
    """
    output_path = tmp_path / "fluid_volume_data.json"

    generate_fluid_volume_data_json(valid_navier_stokes_path, valid_initial_data_path, str(output_path))

    assert output_path.exists(), "Output JSON was not created"

    result = load_json(output_path)

    # --- Basic structure checks ---
    assert "volume_name" in result
    assert result["volume_name"] == "FluidVolume"

    assert "grid_info" in result
    grid = result["grid_info"]
    for key in ["dimensions", "voxel_size", "origin"]:
        assert key in grid

    assert "time_steps" in result
    steps = result["time_steps"]
    assert isinstance(steps, list) and len(steps) >= 1

    for step in steps:
        assert "time" in step
        assert "frame" in step
        assert "density_data" in step
        assert "velocity_data" in step
        assert "temperature_data" in step

        num_voxels = len(step["density_data"])
        assert len(step["velocity_data"]) == num_voxels
        assert len(step["temperature_data"]) == num_voxels



