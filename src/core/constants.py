# src/core/constants.py

from enum import Enum

class OrchestrationStatus(Enum):
    """
    The Operational Truth for Nomadic Workflows.
    Logic is driven by physical artifact presence in 'data/testing-input-output/'.
    """
    WAITING = "WAITING"         # Input artifacts missing; blocked by upstream
    PENDING = "PENDING"         # Inputs present; ready for dispatch
    IN_PROGRESS = "IN_PROGRESS" # Triggered; awaiting output artifact
    COMPLETED = "COMPLETED"     # Output artifact verified on disk
    FAILED = "FAILED"           # Timeout exceeded; requires automated reset

class SystemPaths:
    """Standardized internal relative paths for the nomadic engine."""
    CONFIG_DIR = "config"
    DATA_DIR = "data/testing-input-output"
    ACTIVE_DISK = "active_disk.json"
    LEDGER = "orchestration_ledger.json"
    DORMANT_FLAG = "dormant.flag"