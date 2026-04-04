# tests/test_main_engine.py

import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch

from src.core.constants import OrchestrationStatus, SystemPaths
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

        # 3. Secure Environment (Rule 4: Explicit or Error)
        monkeypatch.setenv("GH_PAT", "mock_access_token_for_testing")

        return config_dir, data_dir, schema_dir

    def test_boot_halt_on_missing_config(self, nomadic_node):
        """Rule 4: Hard-Halt if active_disk.json is physically missing."""
        with pytest.raises(SystemExit) as e:
            run_engine()
        assert e.value.code == 1

    def test_physical_dormancy_hibernation(self, nomadic_node):
        """Rule 1: Verify hibernation signal when artifacts are satisfied."""
        config_dir, data_dir, _ = nomadic_node
        
        # 1. Create Physical Active Disk
        (config_dir / "active_disk.json").write_text(json.dumps({
            "project_id": "TEST-PROJ",
            "manifest_url": "https://raw.githubusercontent.com/dummy/manifest.json"
        }))

        # 2. Inject Physical Dormancy Flag
        (config_dir / "dormant.flag").write_text("STATUS: DORMANT")

        with patch("src.main_engine.logger") as mock_logger:
            with patch("src.core.bootloader.Bootloader.hydrate") as mock_hydrate:
                # SIDE EFFECT: Physically unlock the state object & simulate completed artifact
                def hydrate_side_effect(state_obj):
                    (data_dir / "final_output.csv").write_text("artifact_present")
                    state_obj.hydrate_manifest({
                        "manifest_id": "TEST-MID",
                        "project_id": "TEST-PROJ",
                        "pipeline_steps": [{
                            "name": "final_step",
                            "requires": [],
                            "produces": ["final_output.csv"]
                        }]
                    })
                    return {"steps": {"final_step": {"status": "COMPLETED"}}}
                
                mock_hydrate.side_effect = hydrate_side_effect
                run_engine()
                mock_logger.info.assert_any_call("✅ MISSION COMPLETE: All artifacts present. System entering hibernation.")

    def test_dispatch_loop_with_physical_artifacts(self, nomadic_node):
        """Verify dispatching works when 'input.csv' physically exists on disk."""
        config_dir, data_dir, _ = nomadic_node

        # 1. Setup Physical Config
        (config_dir / "active_disk.json").write_text(json.dumps({
            "project_id": "TEST-PROJ",
            "manifest_url": "https://raw.githubusercontent.com/dummy/manifest.json"
        }))

        # 2. Physically create the 'requires' artifact
        (data_dir / "input.csv").write_text("artifact data")

        with patch("src.core.bootloader.Bootloader.hydrate") as mock_hydrate:
            def dispatch_side_effect(state_obj):
                # Populate the manifest with the required step definition
                state_obj.hydrate_manifest({
                    "manifest_id": "TEST-MID",
                    "project_id": "TEST-PROJ",
                    "pipeline_steps": [{
                        "name": "alpha_solver",
                        "requires": ["input.csv"],
                        "produces": ["output.csv"],
                        "timeout_hours": 6,
                        "target_repo": "nomad/alpha-worker"
                    }]
                })
                return {
                    "steps": {
                        "alpha_solver": {
                            "status": OrchestrationStatus.WAITING.value,
                            "timeout_hours": 6,
                            "target_repo": "nomad/alpha-worker"
                        }
                    }
                }
            
            mock_hydrate.side_effect = dispatch_side_effect
            
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

        with patch("src.core.bootloader.Bootloader.hydrate") as mock_hydrate:
            def sync_side_effect(state_obj):
                state_obj.hydrate_manifest({
                    "manifest_id": "NEW",
                    "project_id": "P1",
                    "pipeline_steps": []
                })
                return {"metadata": {"project_id": "P1", "manifest_id": "NEW"}, "steps": {}}
            
            mock_hydrate.side_effect = sync_side_effect
            run_engine()
            
            # Verify the physical file was updated/overwritten by the engine logic
            updated_ledger = json.loads(ledger_path.read_text())
            assert updated_ledger["metadata"]["project_id"] == "P1"