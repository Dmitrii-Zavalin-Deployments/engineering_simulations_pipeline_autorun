# tests/test_main_engine.py

import pytest
from pathlib import Path
from unittest.mock import patch

from src.core.constants import OrchestrationStatus, SystemPaths
from src.main_engine import run_engine
from tests.helpers.state_engine_dummy import StateEngineDummy

class TestMainEngine:
    """
    Forensic Test Suite for src/main_engine.py.
    Covers: Boot Failure, Dormancy Hibernation, and Worker Dispatch.
    """

    @pytest.fixture
    def mock_env(self, tmp_path, monkeypatch):
        """Creates a nomadic node and redirects SystemPaths to tmp_path."""
        # Setup physical mock environment
        state, data_dir = StateEngineDummy.create(tmp_path)
        
        # Patch SystemPaths to use the temporary directory
        monkeypatch.setattr(SystemPaths, "CONFIG_DIR", str(tmp_path / "config"))
        monkeypatch.setattr(SystemPaths, "DATA_DIR", str(tmp_path / "data"))
        monkeypatch.setattr(SystemPaths, "SCHEMA_DIR", str(tmp_path / "schema"))
        
        return state, data_dir

    def test_boot_failure_halts_system(self, mock_env):
        """Rule 4: System must sys.exit(1) if Bootloader cannot find active_disk.json."""
        state, _ = mock_env
        config_file = Path(SystemPaths.CONFIG_DIR) / SystemPaths.ACTIVE_DISK
        config_file.unlink()  # Force boot failure

        with pytest.raises(SystemExit) as e:
            run_engine()
        
        assert e.value.code == 1

    @patch("src.core.bootloader.Bootloader.hydrate")
    @patch("src.core.update_ledger.LedgerManager.evaluate_dormancy_state")
    def test_dormancy_gate_prevents_execution(self, mock_dormancy, mock_hydrate, mock_env):
        """Rule 1: If all artifacts are present, system enters hibernation immediately."""
        state, _ = mock_env
        
        # Mocking hydration and forcing dormancy
        mock_hydrate.return_value = {"steps": {}}
        state.hydrate_manifest({"manifest_id": "TEST-MID", "project_id": "TEST-PID", "pipeline_steps": []})
        mock_dormancy.return_value = "STATUS: DORMANT"

        with patch("src.main_engine.logger") as mock_logger:
            run_engine()
            mock_logger.info.assert_any_call("✅ MISSION COMPLETE: All artifacts present. System entering hibernation.")

    @patch("src.api.github_trigger.Dispatcher.trigger_worker")
    def test_successful_dispatch_cycle(self, mock_trigger, mock_env):
        """Tests the full loop: Identify ready tasks -> Trigger GitHub -> Log Dispatch."""
        state, data_dir = mock_env
        schema_dir = data_dir.parent / "schema"
        schema_dir.mkdir(parents=True, exist_ok=True)
        (schema_dir / "active_disk_schema.json").write_text("{\"type\":\"object\"}")
        (schema_dir / "manifest_schema.json").write_text("{\"type\":\"object\"}")
        
        # 1. Prepare input artifact to make 'alpha_solver' READY
        (data_dir / "input.csv").write_text("dummy data")
        
        # 2. Mock GitHub Success
        mock_trigger.return_value = True

        with patch("src.main_engine.logger") as mock_logger:
            run_engine()
            
            # Verify Trigger was called with correct payload (Rule 4 check)
            mock_trigger.assert_called_once()
            args, kwargs = mock_trigger.call_args
            assert args[0] == "nomad/alpha-worker"
            assert args[1]["step"] == "alpha_solver"
            
            mock_logger.info.assert_any_call("🏁 Cycle Complete: All identified ready-tasks dispatched.")

    @patch("src.api.github_trigger.Dispatcher.trigger_worker")
    def test_in_flight_pulse_idle(self, mock_trigger, mock_env):
        """Verifies system remains IDLE if workers are currently processing."""
        state, _ = mock_env
        
        # Simulate state where step is already IN_PROGRESS
        steps = {
            "alpha_solver": {
                "name": "alpha_solver",
                "status": OrchestrationStatus.IN_PROGRESS.value,
                "requires": ["input.csv"],
                "produces": ["output.csv"],
                "target_repo": "nomad/alpha-worker",
                "timeout_hours": 6
            }
        }

        with patch("src.core.bootloader.Bootloader.hydrate") as mock_hydrate:
            mock_hydrate.return_value = {"steps": steps}
            state.hydrate_manifest({"manifest_id": "TEST-MID", "project_id": "TEST-PID", "pipeline_steps": []})
            with patch("src.main_engine.logger") as mock_logger:
                run_engine()
                mock_logger.info.assert_any_call("⏳ PULSE IDLE: Workers are currently in-flight. Awaiting arrival.")

    def test_protocol_breach_missing_manifest_key(self, mock_env):
        """Rule 4: Missing mandatory keys in manifest data must trigger Hard-Halt."""
        state, _ = mock_env
        
        # Corrupt manifest data inside hydration
        bad_hydration = {"steps": {}} # Missing 'manifest_id' at top level
        
        with patch("src.core.bootloader.Bootloader.hydrate", return_value=bad_hydration):
            with pytest.raises(SystemExit) as e:
                run_engine()
            assert e.value.code == 1