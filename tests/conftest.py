import pytest
import os
import json

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

@pytest.fixture
def valid_navier_stokes_path():
    return os.path.join(TEST_DATA_DIR, "valid_input", "navier_stokes_results.json")

@pytest.fixture
def valid_initial_data_path():
    return os.path.join(TEST_DATA_DIR, "valid_input", "initial_data.json")

@pytest.fixture
def invalid_input_dir():
    return os.path.join(TEST_DATA_DIR, "invalid_input")

@pytest.fixture
def load_json():
    def _loader(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return _loader



