import bpy
import unittest

class TestBlenderImportValidation(unittest.TestCase):
    def test_blender_particle_import(self):
        """Ensure Blender loads particle simulation data correctly"""
        bpy.ops.import_scene.json(filepath="data/testing-input-output/fluid_particles.json")
        assert len(bpy.context.scene.objects) > 0, "Blender failed to load particles!"
        assert bpy.context.scene.objects[0].particle_systems[0].count > 100, "Particle count mismatch!"

    def test_blender_mesh_structure(self):
        """Ensure Blender mesh contains expected attributes"""
        bpy.ops.import_mesh.alembic(filepath="data/testing-input-output/fluid_mesh.abc")
        assert len(bpy.context.active_object.data.vertices) > 0, "Mesh missing vertices!"

if __name__ == "__main__":
    unittest.main()



