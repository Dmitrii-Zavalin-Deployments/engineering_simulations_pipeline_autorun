# tests/core/test_bootloader.py

import pytest
import json
import responses
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.core.bootloader import Bootloader
from src.core.constants import SystemPaths, OrchestrationStatus

class TestBootloaderForensics:

    @pytest.fixture
    def mock_env(self, tmp_path, monkeypatch):
        """Sets up a physical mock environment for the Bootloader."""
        config_dir = tmp_path / "config"
        schema_dir = tmp_path / "schema"
        config_dir.mkdir()
        schema_dir.mkdir()

        # Patch system constants to point to tmp paths
        monkeypatch.setattr("src.core.constants.SystemPaths.CONFIG_DIR", str(config_dir))
        monkeypatch.setattr("src.core.constants.SystemPaths.SCHEMA_DIR", str(schema_dir))

        # Create dummy schemas
        (schema_dir / SystemPaths.ACTIVE_DISK_SCHEMA).write_text(json.dumps({"type": "object"}))
        (schema_dir / SystemPaths.MANIFEST_SCHEMA).write_text(json.dumps({"type": "object"}))

        return {"config": config_dir, "schema": schema_dir}

    def test_validate_integrity_failure(self, mock_env):
        """Line 30-35: Verify hard-halt on schema breach."""
        bad_data = {"unexpected": "field"}
        # Overwrite schema with one that requires a specific field
        (mock_env["schema"] / "test.json").write_text(json.dumps({"required": ["id"]}))
        
        with pytest.raises(RuntimeError, match="SCHEMA BREACH"):
            Bootloader._validate_integrity(bad_data, "test.json")

    def test_mount_dormancy_reset_oserror(self, mock_env, monkeypatch):
        """Line 51-54: Catch OSError when failing to reset dormant flag."""
        dormant_flag = Path(SystemPaths.CONFIG_DIR) / SystemPaths.DORMANT_FLAG
        config_file = Path(mock_env["config"]) / "active.json"
        
        # Create files such that config is newer than flag
        dormant_flag.write_text("STATUS: DORMANT")
        config_file.write_text(json.dumps({"project_id": "P1", "manifest_url": "..."}))
        
        # Ensure mtime logic triggers reset
        # Use a patch on Path.write_text to raise OSError
        with patch.object(Path, "write_text", side_effect=OSError("Disk Read Only")):
            with patch("src.core.bootloader.logger") as mock_logger:
                # We expect the OrchestrationState init to fail because it's not fully mocked, 
                # but we only care about the log check before that.
                try:
                    Bootloader.mount(str(config_file), "/tmp", "/tmp/ledger.json")
                except Exception:
                    pass
                mock_logger.error.assert_any_call("Failed to reset dormancy flag: Disk Read Only")

    @responses.activate
    def test_hydrate_project_pivot_reset(self, mock_env):
        """Line 85-122: Verify ledger reset when project_id shifts."""
        # 1. Setup local 'Active Disk'
        active_disk = Path(SystemPaths.CONFIG_DIR) / SystemPaths.ACTIVE_DISK
        active_disk.write_text(json.dumps({"project_id": "OLD_PROJ"}))

        # 2. Setup existing Ledger with OLD_PROJ
        ledger_path = mock_env["config"] / "ledger.json"
        ledger_path.write_text(json.dumps({
            "metadata": {"project_id": "OLD_PROJ", "manifest_id": "M1"},
            "steps": {}
        }))

        # 3. Mock Remote Manifest with NEW_PROJ
        manifest_url = "http://api.nomad.com/manifest"
        new_manifest = {
            "project_id": "NEW_PROJ",
            "manifest_id": "M2",
            "pipeline_steps": [
                {"name": "step1", "timeout_hours": 5, "target_repo": "repo1"}
            ]
        }
        responses.add(responses.GET, manifest_url, json=new_manifest, status=200)

        # 4. Mock State Engine
        mock_state = MagicMock()
        mock_state.manifest_url = manifest_url
        mock_state.ledger_path = str(ledger_path)
        mock_state.project_id = "OLD_PROJ"

        # Execution
        ledger_content = Bootloader.hydrate(mock_state)

        # Validation
        assert ledger_content["metadata"]["project_id"] == "NEW_PROJ"
        assert "step1" in ledger_content["steps"]
        assert ledger_content["steps"]["step1"]["status"] == OrchestrationStatus.WAITING.value
        
        # Verify physical persistence
        saved_ledger = json.loads(ledger_path.read_text())
        assert saved_ledger["metadata"]["project_id"] == "NEW_PROJ"

    def test_hydrate_critical_failure_catch(self, mock_env):
        """Line 130-133: Catch-all for hydration exceptions."""
        mock_state = MagicMock()
        mock_state.ledger_path = "/non/existent/path/ledger.json"
        
        # This will fail at step 1 (Active Disk read)
        with pytest.raises(RuntimeError, match="CRITICAL: Hydration failure"):
            Bootloader.hydrate(mock_state)