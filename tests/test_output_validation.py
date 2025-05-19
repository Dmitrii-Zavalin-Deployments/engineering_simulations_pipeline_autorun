import json
import unittest

class TestOutputValidation(unittest.TestCase):
    def setUp(self):
        """Load output JSON"""
        with open("data/testing-input-output/fluid_simulation_blender.json") as f:
            self.output_data = json.load(f)

    def test_blender_format_types(self):
        """Ensure Blender-compatible formats are correctly defined"""
        supported_formats = ["JSON Particles", "Alembic Mesh", "VDB Volume"]
        assert self.output_data["simulation_info"]["blender_animation_format"] in supported_formats, "Unsupported Blender format detected!"

    def test_physical_consistency(self):
        """Ensure fluid properties remain unchanged post-conversion"""
        assert self.output_data["global_parameters"]["density"]["value"] == 1000, "Density mismatch detected!"
        assert self.output_data["global_parameters"]["turbulence_intensity"]["value"] > 0, "Invalid turbulence intensity!"

if __name__ == "__main__":
    unittest.main()



