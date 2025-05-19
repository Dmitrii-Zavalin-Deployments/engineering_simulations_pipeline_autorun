import unittest
import os
import numpy as np

class TestBlenderConversionPipeline(unittest.TestCase):
    def test_binary_format_exists(self):
        """Ensure .npy binary format is generated for Blender"""
        assert os.path.exists("data/testing-input-output/fluid_simulation.npy"), "Binary file not found!"

    def test_binary_data_structure(self):
        """Ensure .npy file stores fluid simulation data correctly"""
        np_data = np.load("data/testing-input-output/fluid_simulation.npy")
        assert np_data.shape[0] > 0, "Invalid Blender data structure!"

if __name__ == "__main__":
    unittest.main()



