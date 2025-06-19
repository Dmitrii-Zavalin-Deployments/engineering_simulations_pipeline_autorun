import numpy as np
import pytest
import os
import sys
import json

# Add src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from generate_vdb_format import generate_fluid_volume_data_json

@pytest.fixture
def synthetic_input(tmp_path):
    """Creates synthetic valid inputs to isolate physics calculations."""
    # Create navier_stokes_results.json
    navier_data = {
        "time_points": [0.01],
        "velocity_history": [
            [[0.0, 0.0, 0.0],
             [0.0, 0.0, 0.0],
             [0.0, 0.0, 0.0]]
        ],
        "pressure_history": [
            [101325.0, 202650.0, 405300.0]
        ],
        "mesh_info": {
            "nodes": 3,
            "nodes_coords": [
                [0.0, 0.0, 0.0],
                [0.1, 0.0, 0.0],
                [0.2, 0.0, 0.0]
            ],
            "grid_shape": [1, 1, 3],
            "dx": 1.0,
            "dy": 1.0,
            "dz": 1.0
        }
    }

    # Create initial_data.json
    initial_data = {
        "fluid_properties": {
            "density": 1.225,
            "viscosity": 1.81e-5,
            "thermodynamics": {
                "model": "ideal_gas",
                "specific_gas_constant_J_per_kgK": 287.0,
                "adiabatic_index_gamma": 1.4
            }
        },
        "boundary_conditions": {},
        "simulation_parameters": {
            "time_step": 0.01,
            "total_time": 1.0,
            "solver": "explicit"
        }
    }

    navier_path = tmp_path / "navier_stokes_results.json"
    initial_path = tmp_path / "initial_data.json"
    output_path = tmp_path / "output.json"

    with open(navier_path, "w") as f:
        json.dump(navier_data, f, indent=4)
    with open(initial_path, "w") as f:
        json.dump(initial_data, f, indent=4)

    return str(navier_path), str(initial_path), str(output_path)

def test_ideal_gas_density_and_temperature(synthetic_input):
    navier_path, initial_path, output_path = synthetic_input

    generate_fluid_volume_data_json(navier_path, initial_path, output_path)

    with open(output_path, "r") as f:
        result = json.load(f)

    gamma = 1.4
    R = 287.0
    initial_density = 1.225
    pressures = [101325.0, 202650.0, 405300.0]
    initial_C = pressures[0] / (initial_density ** gamma)

    expected_densities = [(P / initial_C) ** (1 / gamma) for P in pressures]
    expected_temperatures = [
        P / (rho * R) for P, rho in zip(pressures, expected_densities)
    ]

    out_density = result["time_steps"][0]["density_data"]
    out_temperature = result["time_steps"][0]["temperature_data"]

    assert np.allclose(out_density, expected_densities, rtol=1e-5), "Density mismatch"
    assert np.allclose(out_temperature, expected_temperatures, rtol=1e-5), "Temperature mismatch"



