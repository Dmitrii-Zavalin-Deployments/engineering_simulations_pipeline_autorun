# tests/behavior/test_boot_sequence.py

import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch
from jsonschema import ValidationError
from src.core.bootloader import Bootloader

# Assuming your source is in the python path
from src.core.state_engine import OrchestrationState

@pytest.fixture
def fake_foundation(Path(fake_foundation["root"])):
    """Creates a temporary directory structure for nomadic testing."""
    d = Path(fake_foundation["root"]) / "project_root"
    d.mkdir()
    data_dir = d / "data"
    data_dir.mkdir()
    
    # Create a valid active_disk.json
    active_disk = d / "active_disk.json"
    manifest_data = {
        "project_id": "navier-stokes-test",
        "version": "1.0.0",
        "pipeline_steps": [
            {
                "step_name": "geometry_generation",
                "target_repo": "geometry-gen-repo",
                "timeout_hours": 2,
                "inputs": [],
                "outputs": ["geometry.msh"]
            }
        ]
    }
    active_disk.write_text(json.dumps(manifest_data))
    
    # Create a dummy audit file
    audit_file = d / "performance_audit.md"
    audit_file.write_text("# Performance Audit Log\n")
    
    return {
        "root": d,
        "active_disk": active_disk,
        "audit": audit_file,
        "manifest_content": manifest_data
    }

def test_clean_wakeup_hydration(fake_foundation):
    """
    Scenario: Clean Wake-Up
    Verifies that OrchestrationState hydrates and records the event.
    """
    with patch('src.core.bootloader.Bootloader.hydrate') as mock_fetch:
        # Simulate local disk pointing to a manifest
        mock_fetch.return_value = fake_foundation["manifest_content"]
        
        state = Bootloader.mount(str(Path(fake_foundation["root"]) / "missing.json"), str(fake_foundation["root"]))
        
        assert isinstance(state, OrchestrationState)
        assert state.project_id == "navier-stokes-test"
        
        # Verify Audit Log entry
        audit_content = fake_foundation["audit"].read_text()
        assert "📥 HYDRATION" in audit_content

def test_auto_wake_trigger(fake_foundation):
    """
    Scenario: Auto-Wake Trigger
    Verifies that a new timestamp on active_disk.json clears the dormant flag.
    """
    root = fake_foundation["root"]
    dormant_flag = root / "dormant.flag"
    dormant_flag.write_text("STATUS: DORMANT")
    
    os.utime(str(Path(fake_foundation["root"]) / "missing.json"), (os.path.getatime(dormant_flag) + 100,
                                             os.path.getmtime(dormant_flag) + 100))
    
    # Bootloader is static
    Bootloader.mount(str(Path(fake_foundation["root"]) / "missing.json"), str(fake_foundation["root"]))
    
    # Expectation: Flag is removed or set to ACTIVE
    assert not dormant_flag.exists() or "ACTIVE" in dormant_flag.read_text()

def test_poisoned_manifest_schema_enforcement(fake_foundation):
    """
    Scenario: Poisoned Manifest (Schema Enforcement)
    Verifies that missing mandatory keys trigger a Hard-Halt (ValidationError).
    """
    # Create invalid manifest (missing 'pipeline_steps')
    poisoned_data = {
        "project_id": "broken-project",
        "version": "1.0.0"
        # MISSING pipeline_steps
    }
    
    with patch('src.core.bootloader.Bootloader.hydrate') as mock_fetch:
        mock_fetch.return_value = poisoned_data
        
        
        # Expectation: jsonschema.validate (or your internal check) raises error
        with pytest.raises(ValidationError):
            Bootloader.mount(str(Path(fake_foundation["root"]) / "missing.json"), str(fake_foundation["root"]))

def test_missing_foundation_halt(fake_foundation):
    """
    Scenario: Missing Foundation
    Engine must crash if active_disk.json is not found.
    """
    
    # Bootloader is static
    
    with pytest.raises(FileNotFoundError):
        Bootloader.mount(str(Path(fake_foundation["root"]) / "missing.json"), str(fake_foundation["root"]))