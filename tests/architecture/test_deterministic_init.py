# tests/architecture/test_deterministic_init.py

import ast
import pytest
from pathlib import Path

# --- Constants & Configuration ---
# Alignment: Using the project-relative pathing
BASE_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = BASE_DIR / "src"

# Define core files that MUST have __slots__ (Rule 0)
MANDATORY_SLOTS_FILES = [
    SRC_DIR / "core" / "state_engine.py",
    SRC_DIR / "core" / "update_ledger.py",
    SRC_DIR / "api" / "github_trigger.py",
    SRC_DIR / "io" / "download_from_dropbox.py"
]

def get_python_files(directory):
    """Recursively finds all Python files in src/ for static analysis."""
    return list(directory.rglob("*.py"))

class ZeroDefaultVisitor(ast.NodeVisitor):
    """
    AST Visitor to detect .get(key, default) violations.
    Rule 4: Zero-Default Policy.
    """
    def __init__(self, filename):
        self.filename = filename
        self.violations = []

    def visit_Call(self, node):
        # We are looking for calls to '.get()'
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'get':
            # A .get() with 2 or more arguments means a default fallback was provided.
            # Example: data.get("key", "default_value") -> VIOLATION
            if len(node.args) > 1:
                self.violations.append(
                    f"Ln {node.lineno}: Forbidden .get() with default fallback."
                )
        self.generic_visit(node)

@pytest.mark.parametrize("file_path", get_python_files(SRC_DIR))
def test_rule_4_zero_default_enforcement(file_path):
    """
    STATIC ANALYSIS: Scans for .get(key, default) patterns.
    The engine must 'Hard-Halt' on missing keys rather than falling back.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            pytest.fail(f"Syntax Error in {file_path}")

    visitor = ZeroDefaultVisitor(file_path.name)
    visitor.visit(tree)
    
    error_msg = (
        f"❌ Rule 4 Violation in [{file_path.relative_to(BASE_DIR)}]:\n"
        "Missing data must trigger an error, not a silent fallback.\n"
        "Replace .get(key, default) with direct access [key] or .get(key) with a manual check."
    )
    
    assert not visitor.violations, f"{error_msg}\n" + "\n".join(visitor.violations)

def test_rule_0_slots_memory_optimization():
    """
    STATIC ANALYSIS: Verifies __slots__ in performance-critical core classes.
    Rule 0: Mandatory Architecture for high-frequency nomadic operations.
    """
    missing_slots = []
    
    for file_path in MANDATORY_SLOTS_FILES:
        if not file_path.exists():
            # If the file hasn't been created yet, we skip but log it.
            continue
            
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
            
        # Check every class definition in the file
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Look for an assignment to __slots__ inside the class body
                has_slots = any(
                    isinstance(stmt, ast.Assign) and 
                    any(isinstance(target, ast.Name) and target.id == "__slots__" for target in stmt.targets)
                    for stmt in node.body
                )
                
                if not has_slots:
                    missing_slots.append(f"{file_path.name} -> class {node.name}")

    error_msg = (
        "❌ Rule 0 Violation: Mandatory __slots__ missing in core classes.\n"
        "Core objects must be memory-optimized for asset-only models."
    )
    
    assert not missing_slots, f"{error_msg}\nMissing in: " + ", ".join(missing_slots)

def test_rule_5_operational_hygiene_no_print():
    """
    STATIC ANALYSIS: Ensures no 'print()' statements exist in production src/.
    Rule 5: All output must go through structured logging for audit integrity.
    """
    all_files = get_python_files(SRC_DIR)
    print_violations = []

    for file_path in all_files:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
            
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
                print_violations.append(f"{file_path.name}:{node.lineno}")

    assert not print_violations, (
        "❌ Rule 5 Violation: 'print()' found in source code.\n"
        "Use 'logging' or 'manager.record_event()' for audit trail compliance.\n"
        "Violations: " + ", ".join(print_violations)
    )