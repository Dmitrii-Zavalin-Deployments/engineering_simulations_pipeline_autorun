import bpy
import unittest

class TestBlenderAdvancedValidation(unittest.TestCase):
    def test_blender_particle_animation(self):
        """Ensure imported Blender particles contain correct animation-linked transformations"""
        bpy.ops.import_scene.json(filepath="data/testing-input-output/fluid_particles.json")
        assert bpy.context.scene.frame_end > bpy.context.scene.frame_start, "Animation data missing!"
        assert bpy.context.scene.objects[0].particle_systems[0].settings.use_keyed, "Missing animation-linked particle transformations!"

    def test_blender_mesh_material_integrity(self):
        """Validate imported Blender mesh contains expected materials"""
        bpy.ops.import_mesh.alembic(filepath="data/testing-input-output/fluid_mesh.abc")
        assert len(bpy.context.active_object.material_slots) > 0, "Material slots missing on imported fluid mesh!"

if __name__ == "__main__":
    unittest.main()



