# tests/test_main_engine.py

import pytest
import json
from unittest.mock import patch

from src.core.constants import OrchestrationStatus
from src.main_engine import run_engine

class TestMainEnginePhysical:
    """
    Physical Integration Suite for src/main_engine.py.
    Operates on a temporary real-disk structure to avoid stale mocking.
    """

    @pytest.fixture
    def nomadic_node(self, tmp_path, monkeypatch):
        """
        Constructs a complete physical filesystem for the Engine.
        Returns: (config_dir, data_dir, schema_dir)
        """
        config_dir = tmp_path / "config"
        data_dir = tmp_path / "data"
        schema_dir = tmp_path / "schema"
        
        for d in [config_dir, data_dir, schema_dir]:
            d.mkdir(parents=True)

        # 1. Patch Constants globally for this test session
        monkeypatch.setattr("src.core.constants.SystemPaths.CONFIG_DIR", str(config_dir))
        monkeypatch.setattr("src.core.constants.SystemPaths.DATA_DIR", str(data_dir))
        monkeypatch.setattr("src.core.constants.SystemPaths.SCHEMA_DIR", str(schema_dir))

        # 2. Seed minimal Schemas (Rule 4: Zero-Default)
        (schema_dir / "active_disk_schema.json").write_text(json.dumps({"type": "object"}))
        (schema_dir / "manifest_schema.json").write_text(json.dumps({"type": "object"}))

        return config_dir, data_dir, schema_dir

    def test_boot_halt_on_missing_config(self, nomadic_node):
        """Rule 4: Hard-Halt if active_disk.json is physically missing."""
        with pytest.raises(SystemExit) as e:
            run_engine()
        assert e.value.code == 1

    def test_physical_dormancy_hibernation(self, nomadic_node):
        """Rule 1: System must halt if the physical dormant.flag is set."""
        config_dir, _, _ = nomadic_node
        
        # 1. Create Physical Active Disk
        (config_dir / "active_disk.json").write_text(json.dumps({
            "project_id": "TEST-PROJ",
            "manifest_url": "https://raw.githubusercontent.com/dummy/manifest.json"
        }))

        # 2. Inject Physical Dormancy Flag
        (config_dir / "dormant.flag").write_text("STATUS: DORMANT")

        with patch("src.main_engine.logger") as mock_logger:
            # We must still mock hydrate because it hits the network (GitHub raw)
            # but we allow the rest of the engine to run physically.
            with patch("src.core.bootloader.Bootloader.hydrate") as mock_hydrate:
                mock_hydrate.return_value = {"steps": {}}
                run_engine()
                mock_logger.info.assert_any_call("✅ MISSION COMPLETE: All artifacts present. System entering hibernation.")

    def test_dispatch_loop_with_physical_artifacts(self, nomadic_node):
        """Verify dispatching works when 'input.csv' physically exists on disk."""
        config_dir, data_dir, _ = nomadic_node

        # 1. Setup Physical Config & Ledger
        (config_dir / "active_disk.json").write_text(json.dumps({
            "project_id": "TEST-PROJ",
            "manifest_url": "https://raw.githubusercontent.com/dummy/manifest.json"
        }))

        # 2. Physically create the 'requires' artifact
        (data_dir / "input.csv").write_text("artifact data")

        # 3. Simulate Hydrated Ledger Data
        hydrated_data = {
            "steps": {
                "alpha_solver": {
                    "status": OrchestrationStatus.WAITING.value,
                    "timeout_hours": 6,
                    "target_repo": "nomad/alpha-worker"
                }
            }
        }

        with patch("src.core.bootloader.Bootloader.hydrate", return_value=hydrated_data):
            # We mock the API trigger to avoid actual GitHub calls
            with patch("src.api.github_trigger.Dispatcher.trigger_worker", return_value=True) as mock_trigger:
                run_engine()
                
                # Verify trigger was pulled because 'input.csv' was physically detected
                mock_trigger.assert_called_once()
                assert "alpha_solver" in mock_trigger.call_args[0][1]["step"]

    def test_stale_ledger_overwritten_by_physical_sync(self, nomadic_node):
        """Rule 4: Memory-Disk Sync. Verify that Bootloader overrides a stale physical ledger."""
        config_dir, _, _ = nomadic_node
        ledger_path = config_dir / "orchestration_ledger.json"

        # 1. Write a 'STALE' ledger to disk
        (config_dir / "active_disk.json").write_text(json.dumps({"project_id": "P1", "manifest_url": "..."}))
        ledger_path.write_text(json.dumps({
            "metadata": {"project_id": "STALE", "manifest_id": "OLD"},
            "steps": {}
        }))

        # 2. Mock Hydrate returning NEW data
        new_data = {"metadata": {"project_id": "P1", "manifest_id": "NEW"}, "steps": {}}

        with patch("src.core.bootloader.Bootloader.hydrate", return_value=new_data):
            run_engine()
            
            # Verify the physical file was updated/overwritten by the engine
            updated_ledger = json.loads(ledger_path.read_text())
            assert updated_ledger["metadata"]["project_id"] == "P1"