# tests/architecture/test_deterministic_init.py

import ast
import os
import pytest
from pathlib import Path

# Rule 4: Zero-Default Policy Enforcement
# This test ensures no core logic uses .get(key, default) for mandatory data.
# The engine must "Hard-Halt" on missing keys rather than falling back to defaults.

SRC_DIR = Path(__file__).parent.parent.parent / "src"

def get_python_files(directory):
    """Recursively find all python files in the source directory."""
    return list(directory.rglob("*.py"))

class GetCallVisitor(ast.NodeVisitor):
    """AST Visitor to detect .get() calls with more than one argument."""
    def __init__(self, filename):
        self.filename = filename
        self.violations = []

    def visit_Call(self, node):
        # Target: object.get(arg1, arg2)
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'get':
            # Rule 4 Violation: Providing a second argument (the default)
            if len(node.args) > 1:
                self.violations.append(
                    f"{self.filename}:{node.lineno} - Forbidden .get() with default fallback."
                )
        self.generic_visit(node)

@pytest.mark.parametrize("file_path", get_python_files(SRC_DIR))
def test_enforce_zero_default_policy(file_path):
    """
    Scans src/ files for .get(key, default) patterns.
    Rule 4 Mandate: Missing data must trigger an error, not a silent fallback.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    
    visitor = GetCallVisitor(file_path.name)
    visitor.visit(tree)
    
    # If violations are found, the test fails, blocking the Phase C deployment.
    assert not visitor.violations, (
        f"Rule 4 Violation in {file_path}:\n" + "\n".join(visitor.violations)
    )

def test_enforce_slots_in_core_classes():
    """
    Scans core orchestrator files for __slots__ definition.
    Rule 0 Mandate: Mandatory Architecture for memory optimization.
    """
    core_files = [
        SRC_DIR / "api" / "github_trigger.py",
        SRC_DIR / "core" / "update_ledger.py"
    ]
    
    for file_path in core_files:
        if not file_path.exists():
            continue
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Basic string check for __slots__ presence
            assert "__slots__ =" in content, (
                f"Rule 0 Violation: {file_path.name} is missing mandatory __slots__."
            )