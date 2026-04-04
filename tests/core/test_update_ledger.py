# tests/core/test_update_ledger.py

import os
import json
import pytest
from unittest.mock import patch, mock_open
from src.core.update_ledger import LedgerManager

class TestLedgerForensics:
    
    @pytest.fixture
    def manager(self, tmp_path):
        """Provides a manager with temp paths to avoid polluting the workspace."""
        log_file = tmp_path / "audit.md"
        # Mock SystemPaths to point to our temp directory
        with patch("src.core.update_ledger.SystemPaths") as mock_paths:
            mock_paths.CONFIG_DIR = str(tmp_path)
            mock_paths.LEDGER = "ledger.json"
            mock_paths.DORMANT_FLAG = "dormant.flag"
            yield LedgerManager(log_path=str(log_file))

    # --- SECTION 1: PERFORMANCE AUDIT (MARKDOWN) COVERAGE ---

    def test_record_event_read_failure_recovery(self, manager):
        """Covers Lines 53-55: Ensures 'existing_content' resets to empty on read error."""
        # 1. Create the file physically so the 'if os.path.exists' check passes
        with open(manager.log_path, "w") as f:
            f.write("Initial Content")
        
        # 2. Mock: First open (read) fails, Second open (write) succeeds
        m = mock_open()
        m.side_effect = [IOError("Read Denied"), m.return_value]

        with patch("builtins.open", m):
            manager.record_event("RECOVERY_TEST", "Message")
            
        # 3. FIX: The final file should contain the NEW entry but NOT the OLD one
        # because Line 55 reset existing_content to "" after the read failure.
        with open(manager.log_path, "r") as f:
            content = f.read()
            assert "RECOVERY_TEST" in content
            assert "Initial Content" not in content

    def test_record_event_critical_write_failure(self, manager):
        """Covers Lines 60-62: Specifically targets the WRITE IOError."""
        # Rule 5 Compliance: Sequential Mocking for Atomic Audit Trail
        m = mock_open()
        
        # 1st call (Line 50: read) returns valid mock handle to pass first try-block
        # 2nd call (Line 58: write) raises IOError to trigger critical failure path
        m.side_effect = [m.return_value, IOError("Disk Full")]

        with patch("builtins.open", m):
            with pytest.raises(RuntimeError, match="Could not update performance audit"):
                # Execution Trace: 
                # 1. open(log, "r") -> Success (Line 50)
                # 2. open(log, "w") -> IOError -> logger.critical (Line 58)
                manager.record_event("FAIL", "This should crash")

    # --- SECTION 2: ORCHESTRATION MEMORY (JSON) COVERAGE ---

    def test_load_state_missing_file(self, manager):
        """Covers Lines 71-73: Returns fresh structure if file is missing."""
        if os.path.exists(manager.orchestration_path):
            os.remove(manager.orchestration_path)
        
        state = manager.load_orchestration_state()
        assert state == {"metadata": {}, "steps": {}}

    def test_load_state_schema_violation(self, manager, tmp_path):
        """Covers Lines 79-81 & 82-84: Handles missing root keys or corrupt JSON."""
        # Scenario A: Valid JSON but missing 'steps' key
        with open(manager.orchestration_path, "w") as f:
            json.dump({"metadata": {}}, f)
        
        state = manager.load_orchestration_state()
        assert state == {"metadata": {}, "steps": {}} # Reset triggered

        # Scenario B: Mangled JSON
        with open(manager.orchestration_path, "w") as f:
            f.write("{ invalid json... ")
        
        state = manager.load_orchestration_state()
        assert state == {"metadata": {}, "steps": {}} # Reset triggered

    def test_update_job_status_io_failure(self, manager):
        """Covers Lines 111-113: Critical failure if ledger cannot be saved."""
        # Create a valid state first
        with open(manager.orchestration_path, "w") as f:
            json.dump({"metadata": {}, "steps": {}}, f)
            
        with patch("builtins.open", side_effect=[mock_open().return_value, IOError("No Space")]):
            with pytest.raises(RuntimeError, match="Ledger sync failed"):
                manager.update_job_status("job1", "ACTIVE", {"timeout_hours": 1, "target": "repo"})

    # --- SECTION 3: DORMANCY COVERAGE ---

    def test_evaluate_dormancy_io_failure(self, manager):
        """Covers Lines 138-140: Returns ACTIVE if flag cannot be written."""
        with patch("builtins.open", side_effect=IOError("Permission Denied")):
            result = manager.evaluate_dormancy_state({"step1": {"status": "COMPLETED"}})
            assert result == "STATUS: ACTIVE"

    # --- SECTION 4: WRAPPER COVERAGE ---

    def test_log_scan_integration(self, manager):
        """Covers Lines 145-151: Verifies the forensic scan wrapper."""
        manager.log_scan("P-101", "Integrity Check Passed")
        
        with open(manager.log_path, "r") as f:
            content = f.read()
            assert "FORENSIC_SCAN" in content
            assert "P-101" in content