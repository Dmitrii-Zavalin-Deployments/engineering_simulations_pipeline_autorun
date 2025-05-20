import unittest
import os
import json
import numpy as np
from jsonschema import validate

# Try to import pyopenvdb for deeper VDB validation (skip if unavailable)
try:
    import pyopenvdb as vdb
    vdb_available = True
except ImportError:
    vdb_available = False
    print("Warning: pyopenvdb not installed. VDB content tests will be limited.")


class TestVolumetricVDBConversion(unittest.TestCase):

    def setUp(self):
        """Define paths for input simulation data and VDB output"""
        self.input_json_path = "data/testing-input-output/fluid_simulation.json"
        self.binary_npy_path = "data/testing-input-output/fluid_simulation.npy"
        self.output_vdb_path = "data/testing-input-output/fluid_volume.vdb"

        with open(self.input_json_path) as f:
            self.input_data = json.load(f)

    ### JSON VALIDATION ###

    def test_json_schema(self):
        """Ensure input file follows defined JSON schema"""
        schema = {
            "type": "object",
            "properties": {
                "simulation_info": {"type": "object"},
                "global_parameters": {"type": "object"},
                "data_points": {"type": "array"}
            },
            "required": ["simulation_info", "global_parameters", "data_points"]
        }
        validate(instance=self.input_data, schema=schema)

    def test_physical_consistency(self):
        """Ensure extracted fluid properties remain realistic"""
        assert 1000 <= self.input_data["global_parameters"]["density"]["value"] <= 1200, "Density out of bounds!"
        assert 101000 <= self.input_data["global_parameters"]["pressure"]["value"] <= 102000, "Pressure out of bounds!"
        assert self.input_data["global_parameters"]["turbulence_intensity"]["value"] >= 0, "Turbulence intensity invalid!"

    ### BINARY DATA VALIDATION ###

    def test_binary_output_exists(self):
        """Ensure .npy binary format is correctly generated"""
        assert os.path.exists(self.binary_npy_path), f"Binary file missing at {self.binary_npy_path}!"

    def test_binary_data_integrity(self):
        """Ensure structured .npy file stores correct numerical fields"""
        assert os.path.exists(self.binary_npy_path), "Binary file missing, cannot test integrity."
        np_data = np.load(self.binary_npy_path)
        assert np_data.shape[0] > 0, "Binary data structure appears empty!"
        assert "density" in np_data.dtype.names, "Missing density field!"
        assert "pressure" in np_data.dtype.names, "Missing pressure field!"
        assert "turbulence_intensity" in np_data.dtype.names, "Missing turbulence field!"

    ### VDB FILE VALIDATION ###

    def test_vdb_output_exists(self):
        """Ensure the fluid_volume.vdb file is created"""
        assert os.path.exists(self.output_vdb_path), f"VDB output file not found at {self.output_vdb_path}!"

    def test_vdb_data_integrity(self):
        """Ensure VDB file contains expected volumetric density attributes"""
        assert os.path.getsize(self.output_vdb_path) > 0, "VDB file appears empty!"

    @unittest.skipUnless(vdb_available, "pyopenvdb is not installed")
    def test_vdb_grid_count(self):
        """Check if the VDB file contains at least one grid (for density)"""
        if os.path.exists(self.output_vdb_path):
            try:
                grid = vdb.read(self.output_vdb_path)
                self.assertGreater(len(grid), 0, "VDB file does not contain any grids.")
            except Exception as e:
                self.fail(f"Failed to read VDB file: {e}")
        else:
            self.fail("VDB file does not exist, cannot test grid count.")

    @unittest.skipUnless(vdb_available, "pyopenvdb is not installed")
    def test_vdb_grid_type(self):
        """Check if the first grid in the VDB is a FloatGrid (expected for density)"""
        if os.path.exists(self.output_vdb_path):
            try:
                grid = vdb.read(self.output_vdb_path)
                if grid:
                    self.assertIsInstance(grid.grids()[0], vdb.FloatGrid, "The first grid in the VDB should be a FloatGrid (for density).")
            except Exception as e:
                self.fail(f"Failed to read VDB file: {e}")
        else:
            self.fail("VDB file does not exist, cannot test grid type.")

    # More advanced tests could be added here depending on VDB specifics:
    # @unittest.skipUnless(vdb_available, "pyopenvdb is not installed")
    # def test_vdb_voxel_count(self):
    #     """Check if the VDB volume contains a reasonable number of voxels."""
    #     if os.path.exists(self.output_vdb_path):
    #         grid = vdb.read(self.output_vdb_path)
    #         if grid and grid.grids():
    #             active_voxel_count = grid.grids()[0].activeVoxelCount()
    #             self.assertGreater(active_voxel_count, 0, "The VDB volume should contain active voxels.")

if __name__ == "__main__":
    unittest.main()



