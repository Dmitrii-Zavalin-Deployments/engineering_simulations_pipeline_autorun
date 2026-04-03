# tests/behavior/test_ledger_integrity.py

import pytest
import json
from unittest.mock import patch, MagicMock

# Internal Core Imports
from src.core.update_ledger import LedgerManager
from src.core.bootloader import Bootloader
from src.core.constants import SystemPaths
from tests.helpers.state_engine_dummy import StateEngineDummy

@pytest.fixture
def nomadic_env(tmp_path):
    """
    Physical Node Fixture.
    Creates a real folder structure. All I/O happens on real disk.
    """
    # 1. Setup Physical Root
    root = tmp_path / "engine_node"
    config_dir = root / SystemPaths.CONFIG_DIR
    config_dir.mkdir(parents=True)
    
    ledger_path = config_dir / SystemPaths.LEDGER
    audit_path = root / "performance_audit.md"
    
    # 2. Seed Initial Physical State
    initial_ledger = {
        "metadata": {
            "project_id": "INIT-PROJ",
            "manifest_id": "MANIFEST-V1"
        },
        "steps": {}
    }
    ledger_path.write_text(json.dumps(initial_ledger), encoding="utf-8")
    
    return {
        "root": root, 
        "ledger": ledger_path,
        "audit": audit_path,
        "init_pid": "INIT-PROJ",
        "init_mid": "MANIFEST-V1"
    }

def test_metadata_handshake_dispatch_REAL_IO(nomadic_env):
    """
    Scenario: Verify log_dispatch updates physical global identity.
    NO MOCKS: Tests real LedgerManager writing to real files.
    """
    manager = LedgerManager(log_path=str(nomadic_env["audit"]))
    manager.orchestration_path = nomadic_env["ledger"]
    
    manager.log_dispatch(
        project_id="NEW-PROJECT-ID",
        manifest_id="NEW-MANIFEST-ID",
        step_name="geometry_gen",
        target_repo="org/geom",
        timeout_hours=2
    )
    
    # Direct physical disk check
    data = json.loads(nomadic_env["ledger"].read_text(encoding="utf-8"))
    
    assert data["metadata"]["project_id"] == "NEW-PROJECT-ID"
    assert data["metadata"]["manifest_id"] == "NEW-MANIFEST-ID"

def test_audit_trail_atomic_prepending_REAL_IO(nomadic_env):
    """Scenario: Verify Audit Log physical prepending on a real file."""
    manager = LedgerManager(log_path=str(nomadic_env["audit"]))
    
    manager.record_event("EVENT_ALPHA", "Message One")
    manager.record_event("EVENT_BETA", "Message Two")
    
    content = nomadic_env["audit"].read_text()
    
    # Verification of physical byte-order (Newest First)
    assert content.find("Message Two") < content.find("Message One")

@pytest.mark.parametrize("new_pid, new_mid", [
    ("DIFFERENT-PID", "MANIFEST-V1"),
    ("INIT-PROJ", "DIFFERENT-MID"),
    ("NEW-PID", "NEW-MID"),
])
def test_identity_mismatch_forensic_reset_HYBRID(nomadic_env, new_pid, new_mid):
    """
    Scenario: Identity Shift -> Atomic Wipe.
    BOUNDARY MOCK: Only the requests.get call is mocked.
    INTERNAL REALITY: The disk wipe and file rewrite are REAL.
    """
    # 1. Setup State and Data
    state, _ = StateEngineDummy.create(nomadic_env["root"])
    state.ledger_path = nomadic_env["ledger"]

    # Write 'Poison' data to the real ledger file
    initial_data = {
        "metadata": {"project_id": nomadic_env["init_pid"], "manifest_id": nomadic_env["init_mid"]},
        "steps": {"poison_step": {"status": "COMPLETED"}}
    }
    nomadic_env["ledger"].write_text(json.dumps(initial_data))

    # 2. Mock only the "Out of Instance" Boundary (Requests)
    with patch("src.core.bootloader.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "project_id": new_pid,
            "manifest_id": new_mid,
            "pipeline_steps": [
                {"name": "fresh_start", "target_repo": "org/new", "timeout_hours": 24}
            ]
        }
        mock_get.return_value = mock_response

        # 3. Execution (The core logic runs on real files)
        Bootloader.hydrate(state)

    # 4. Physical Verification
    updated = json.loads(nomadic_env["ledger"].read_text())
    
    # If this passes, it proves the code physically wiped the file on disk
    assert "poison_step" not in updated["steps"], "Logic error: Poison step survived on disk."
    assert updated["metadata"]["project_id"] == new_pid
    assert "fresh_start" in updated["steps"]