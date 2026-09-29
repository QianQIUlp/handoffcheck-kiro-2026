# Design Document: HandoffCheck CLI Tool

## Overview

HandoffCheck is a command-line validation tool that validates handoff manifests and their associated evidence files. The tool ensures manifests conform to a specified JSON schema, validates all referenced evidence files exist and are valid, and produces deterministic output indicating the validation status.

**Revised Architecture (per steering feedback):**
- **Single stdlib core** at `skills/check-handoff/scripts/` for Power distribution
- **Thin root CLI** (`handoffcheck.py`) as a simple importer/entry point
- **Python Hypothesis** for property-based testing (native IDE Correctness compatible)
- **Explicit reasons** in all task_results (pending, done with zero/invalid evidence)
- **Validate --root first** before evidence checks (INVALID_MANIFEST exit 2)
- **Preserve task order** for next_task determination

## Architecture

### File Layout

```
handoffcheck/
├── handoffcheck.py              # Thin CLI: argparse + import from core
├── skills/
│   └── check-handoff/
│       └── scripts/
│           └── handoffcheck_core.py  # Single stdlib core module
├── tests/
│   ├── test_manifest.py         # Unit tests
│   ├── test_paths.py
│   ├── test_evidence.py
│   ├── test_ready.py
│   ├── test_output.py
│   ├── test_integration.py
│   └── properties.py            # Hypothesis property tests
├── examples/
│   ├── ready/manifest.json
│   ├── missing/manifest.json
│   └── invalid/manifest.json
└── pyproject.toml               # pytest + hypothesis only
```

### Core Module Structure (`skills/check-handoff/scripts/handoffcheck_core.py`)

The core module is a single stdlib Python file with pure functions for all validation logic:

| Function | Purpose | Input | Output |
|----------|---------|-------|--------|
| `parse_manifest(manifest_path)` | Parse and validate JSON manifest | Path to manifest file | Dict with manifest data or None on error |
| `validate_paths(manifest_data, root_dir)` | Validate evidence paths for security | Manifest data, root directory | List of validated paths or None on error |
| `validate_evidence(paths)` | Check evidence files exist and are valid | List of Path objects | Dict with per-file validation results |
| `check_ready(manifest_data, evidence_results)` | Determine overall readiness status | Manifest data, evidence results | Tuple of (is_ready, next_task_with_reason) |
| `format_output(result_data, format_type)` | Format output as text or JSON | Result data, format type | String output |

### CLI Wrapper Structure (`handoffcheck.py`)

The CLI layer is a thin importer:
- `argparse` argument parsing
- Import core functions from `skills.check-handoff.scripts.handoffcheck_core`
- Call core functions and print output
- Exit with appropriate code

## Components and Interfaces

### Core Module: `skills/check-handoff/scripts/handoffcheck_core.py`

```python
# skills/check-handoff/scripts/handoffcheck_core.py
# Single stdlib Python module for Power distribution

from pathlib import Path
from typing import Dict, List, Optional, Any

# Exit codes
EXIT_READY = 0
EXIT_NEEDS_WORK = 1
EXIT_INVALID_MANIFEST = 2

# Result constants
RESULT_READY = "READY_TO_REVIEW"
RESULT_NEEDS_WORK = "NEEDS_WORK"
RESULT_INVALID_MANIFEST = "INVALID_MANIFEST"

def parse_manifest(manifest_path: Path) -> Optional[Dict[str, Any]]:
    """Parse and validate JSON manifest.

    Returns dict or None on error (exit code 2).
    """
    pass

def validate_paths(manifest_data: Dict[str, Any], root_dir: Path) -> Optional[List[Path]]:
    """Validate evidence paths for security.

    Rejects: absolute paths, Windows drive letters, UNC paths, backslashes, ".." segments,
    symlinks, paths escaping root. Returns list of Path objects or None (exit code 2).
    """
    pass

def validate_evidence(paths: List[Path]) -> Dict[str, Any]:
    """Check evidence files exist and are valid.

    Returns dict with per-file results: exists, is_regular, is_nonempty, error.
    """
    pass

def check_ready(manifest_data: Dict[str, Any], evidence_results: Dict[str, Any]) -> tuple:
    """Determine READY_TO_REVIEW vs NEEDS_WORK status.

    Returns (is_ready, next_task_with_reason) where next_task_with_reason includes
    explicit reason for NOT-READY status (pending, missing evidence, etc.).
    """
    pass

def format_output(result_data: Dict[str, Any], format_type: str) -> str:
    """Format output as text or JSON.

    format_type: "text" or "json"
    Returns formatted string.
    """
    pass
```

### CLI Module: `handoffcheck.py`

```python
# handoffcheck.py - Thin CLI importer
import argparse
import sys
from pathlib import Path

# Import from skills/check-handoff/scripts (Power distribution)
from skills.check_handoff.scripts.handoffcheck_core import (
    parse_manifest, validate_paths, validate_evidence,
    check_ready, format_output,
    EXIT_READY, EXIT_NEEDS_WORK, EXIT_INVALID_MANIFEST,
    RESULT_READY, RESULT_NEEDS_WORK, RESULT_INVALID_MANIFEST
)

def main():
    parser = argparse.ArgumentParser(
        description="Validate handoff manifests and evidence files"
    )
    parser.add_argument(
        "manifest",
        type=Path,
        help="Path to manifest.json file (any positional JSON filename accepted)"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Root directory for evidence files (default: manifest file's directory)"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )

    args = parser.parse_args()

    # Determine root directory: use --root if provided, else manifest file's directory
    root_dir = args.root if args.root else args.manifest.parent

    # Validate --root BEFORE any evidence checks (exit 2 if invalid)
    if not root_dir.exists():
        print(f"Error: --root directory does not exist: {root_dir}", file=sys.stderr)
        sys.exit(EXIT_INVALID_MANIFEST)
    if not root_dir.is_dir():
        print(f"Error: --root is not a directory: {root_dir}", file=sys.stderr)
        sys.exit(EXIT_INVALID_MANIFEST)

    # Call core validation functions
    manifest_data = parse_manifest(args.manifest)
    if manifest_data is None:
        sys.exit(EXIT_INVALID_MANIFEST)

    validated_paths = validate_paths(manifest_data, root_dir)
    if validated_paths is None:
        sys.exit(EXIT_INVALID_MANIFEST)

    evidence_results = validate_evidence(validated_paths)
    is_ready, next_task = check_ready(manifest_data, evidence_results)

    # Build result data with explicit reasons in task_results
    result_data = build_result_data(manifest_data, evidence_results, is_ready, next_task)

    output = format_output(result_data, args.format)
    print(output)
    sys.exit(EXIT_READY if is_ready else EXIT_NEEDS_WORK)

if __name__ == "__main__":
    main()
```

### Output Data Structure

```python
{
    "schema_version": 1,
    "project": "project-name",  # same as manifest
    "result": "READY_TO_REVIEW" or "NEEDS_WORK" or "INVALID_MANIFEST",
    "task_results": [
        {
            "id": "T1",
            "status": "done",
            "evidence": {
                "path/to/file.txt": {
                    "exists": True,
                    "is_regular": True,
                    "is_nonempty": True,
                    "error": None
                }
            },
            "reason": None  # or string explaining why NOT-READY (e.g., "pending", "no evidence", "missing: file.txt")
        }
    ],
    "next_task": {
        "id": "T2",
        "title": "Task Title",
        "status": "pending",
        "reason": "task is pending"  # or "missing evidence: file.txt", etc.
    } or null  # null when all tasks are READY
}
```

## Data Models

### Manifest Schema (schema_version=1)

```python
{
    "schema_version": 1,
    "project": "project-name",  # non-empty string
    "tasks": [
        {
            "id": "T1",  # non-empty string, unique
            "title": "Task Title",  # non-empty string
            "status": "pending" or "done",  # one of: "pending", "done"
            "evidence": ["path/to/file.txt"]  # array of non-empty strings (POSIX paths)
        }
    ]
}
```

### Path Containment Validation

```python
# Security check for path containment (reject symlinks for simplicity)
def is_path_contained(path: Path, root: Path) -> bool:
    """Check if path is contained within root directory, rejecting symlinks."""
    # Reject symlinks
    if path.is_symlink():
        return False

    try:
        resolved_path = path.resolve()
        resolved_root = root.resolve()
        return str(resolved_path).startswith(str(resolved_root) + os.sep) or resolved_path == resolved_root
    except (OSError, ValueError):
        return False
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Manifest Validation Round Trip

*For any* valid manifest file that passes `parse_manifest()`, re-parsing the same file with identical content and structure SHALL produce identical results.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8**

### Property 2: Path Containment Security

*For any* evidence path in any manifest and *for any* root directory, if the path contains ".." segments, absolute paths, Windows drive letters, UNC paths, or backslashes, then `validate_paths()` SHALL reject it with exit code 2.

**Validates: Requirements 3.1, 3.4**

### Property 3: Symlink Escape Prevention

*For any* evidence path that is a symlink, `validate_paths()` SHALL reject it with exit code 2 (rejecting all symlinks for simplicity, as stated and tested consistently).

**Validates: Requirements 3.7, 3.8**

### Property 4: Pending Task Always Needs Work

*For any* manifest with at least one task having status "pending", `check_ready()` SHALL return `False` for readiness and exit with code 1, regardless of evidence file status.

**Validates: Requirements 4.4**

### Property 5: Done Task Needs Evidence

*For any* task with status "done" that has an empty evidence array or missing/empty/nonregular evidence files, `check_ready()` SHALL return `False` for readiness and exit with code 1.

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 6: Deterministic Output Order

*For any* valid manifest and *for any* execution environment, the output produced by `format_output()` SHALL be identical across multiple runs (ignoring non-deterministic elements like timestamps or random identifiers).

**Validates: Requirement 6.1, 6.2, 6.3**

### Property 7: Read-Only Behavior

*For any* manifest or evidence file processed by HandoffCheck, the file content SHALL remain unchanged after execution completes, and the tool SHALL NOT write, delete, or rename any input files.

**Validates: Requirements 7.1, 7.2, 7.3**

### Property 8: Next Task Order Preservation

*For any* manifest with NOT-READY tasks, the `next_task` field in the output SHALL be the first NOT-READY task in the original input order of the tasks array.

**Validates: Requirements 5.9**

### Property 9: JSON Output Structure

*For any* JSON output from `format_output()` with format="json", the output SHALL contain exactly the fields: schema_version, project, result, task_results, next_task, with the project field matching the manifest value.

**Validates: Requirements 5.7, 5.8, 5.14**

### Property 10: --root Validation

*For any* invalid --root (missing, file, inaccessible), `handoffcheck.py` SHALL exit with code 2 BEFORE any evidence file checks.

**Validates: Requirements 8.6**

### Property 11: Explicit Task Reasons

*For any* task_result in output, the result SHALL include an explicit reason field explaining why the task is NOT-READY (including "pending" for pending tasks, or specific evidence issues).

**Validates: Requirements 5.10, 5.11, 5.12**

### Property 12: All Evidence Required

*For any* task with status "done", ALL listed evidence files MUST be valid (exists, regular, non-empty) for the task to be READY.

**Validates: Requirements 4.1, 4.2, 4.3**

## Testing Strategy

### Testing Approach

- **Python Hypothesis** for property-based tests in `tests/properties.py`
- **pytest unit tests** in dedicated test files for specific examples and edge cases
- **Integration tests** in `tests/test_integration.py` for end-to-end scenarios
- **No pytest-cov** - only meaningful test coverage

### Property-Based Tests (Hypothesis)

Each property is tested with Hypothesis, running minimum 100 iterations with randomly generated inputs.

**Property Tests to Implement:**

1. **Property 1: Manifest Validation Round Trip**
   - Generate valid manifest JSON files
   - Parse twice and verify identical results
   - Test in `tests/properties.py`

2. **Property 2: Path Containment Security**
   - Generate paths with "..", absolute paths, Windows paths
   - Verify all are rejected with exit code 2
   - Test in `tests/properties.py`

3. **Property 3: Symlink Escape Prevention**
   - Generate symlinks as evidence paths
   - Verify all are rejected with exit code 2
   - Test in `tests/properties.py`

4. **Property 4: Pending Task Always Needs Work**
   - Generate manifests with pending tasks
   - Verify readiness is always False with exit code 1
   - Test in `tests/properties.py`

5. **Property 5: Done Task Needs Evidence**
   - Generate done tasks with empty/missing evidence
   - Verify readiness is always False with exit code 1
   - Test in `tests/properties.py`

6. **Property 6: Deterministic Output Order**
   - Generate same manifest content twice
   - Verify identical output across runs
   - Test in `tests/properties.py`

7. **Property 7: Read-Only Behavior**
   - Generate manifest files, run tool
   - Verify file content unchanged after execution
   - Test in `tests/properties.py`

8. **Property 8: Next Task Order Preservation**
   - Generate manifests with NOT-READY tasks
   - Verify next_task is first in input order
   - Test in `tests/properties.py`

9. **Property 9: JSON Output Structure**
   - Generate valid manifests
   - Verify JSON output contains required fields
   - Test in `tests/properties.py`

10. **Property 10: --root Validation**
    - Generate invalid --root paths (missing, file, inaccessible)
    - Verify exit code 2 before evidence checks
    - Test in `tests/properties.py`

11. **Property 11: Explicit Task Reasons**
    - Generate various NOT-READY scenarios
    - Verify task_results includes explicit reason
    - Test in `tests/properties.py`

12. **Property 12: All Evidence Required**
    - Generate done tasks with all evidence valid vs missing one
    - Verify all evidence must be valid for READY
    - Test in `tests/properties.py`

### Unit Testing

Unit tests verify specific examples, edge cases, and error conditions:

**Test Categories:**

1. **Manifest Parsing Tests** (`tests/test_manifest.py`):
   - Valid manifest with single task
   - Valid manifest with multiple tasks
   - Invalid JSON (syntax errors)
   - Missing required fields
   - Empty project string
   - Empty tasks array

2. **Task Validation Tests** (in `tests/test_manifest.py`):
   - Valid task structure
   - Duplicate task IDs
   - Invalid status values
   - Empty evidence arrays

3. **Path Validation Tests** (`tests/test_paths.py`):
   - Valid POSIX relative paths
   - Absolute paths (should fail)
   - Paths with ".." (should fail)
   - Windows paths (should fail)
   - Paths with backslashes (should fail)

4. **Evidence File Tests** (`tests/test_evidence.py`):
   - Valid non-empty file
   - Missing file (should fail)
   - Empty file (should fail)
   - Directory (should fail)
   - Symlink (should fail - we reject symlinks)

5. **Ready Check Tests** (`tests/test_ready.py`):
   - All tasks ready
   - One pending task
   - One done task with missing evidence
   - Multiple done tasks, one with missing evidence
   - Explicit reason in output

6. **Output Formatting Tests** (`tests/test_output.py`):
   - Text format output
   - JSON format output
   - JSON structure validation
   - Explicit reasons in output

### Integration Testing

Integration tests verify the complete tool flow (`tests/test_integration.py`):

1. **Ready Scenario:** Complete manifest with all evidence files → exit 0
2. **Needs Work Scenario:** Manifest with pending task → exit 1
3. **Invalid Manifest Scenario:** Invalid JSON → exit 2
4. **Missing Evidence Scenario:** Done task with missing file → exit 1
5. **Path Traversal Scenario:** Path with ".." → exit 2
6. **Symlink Scenario:** Symlink evidence file → exit 2
7. **Invalid --root Scenario:** Missing/invalid --root → exit 2
8. **Explicit Reasons Scenario:** Verify task_results includes reasons

### Test File Structure

```
tests/
├── test_manifest.py      # Manifest parsing and task validation
├── test_paths.py         # Path validation
├️ test_evidence.py       # Evidence file validation
├── test_ready.py         # Ready check with explicit reasons
├── test_output.py        # Output formatting
├── test_integration.py   # End-to-end integration tests
└── properties.py         # Hypothesis property tests
```

### Testing Commands

```bash
# Run all tests
pytest tests/

# Run property-based tests only
pytest tests/properties.py

# Run unit tests only
pytest tests/ -k "not property"

# Run integration tests only
pytest tests/test_integration.py
```

## Examples Directory Structure

```
examples/
├── ready/                # All tasks ready
│   ├── manifest.json     # Valid manifest with all done tasks
│   └── proofs/
│       └── test-report.txt  # Non-empty evidence file
├── missing/              # Missing evidence files
│   ├── manifest.json     # Valid manifest with missing evidence
│   └── proofs/
├── invalid/              # Invalid manifest
│   └── manifest.json     # Invalid JSON or schema
└── readme.md             # Usage instructions
```

### Example Manifests

**examples/ready/manifest.json:**
```json
{
  "schema_version": 1,
  "project": "ready-demo",
  "tasks": [
    {
      "id": "T1",
      "title": "Task with valid evidence",
      "status": "done",
      "evidence": ["proofs/test-report.txt"]
    }
  ]
}
```

**examples/missing/manifest.json:**
```json
{
  "schema_version": 1,
  "project": "missing-demo",
  "tasks": [
    {
      "id": "T1",
      "title": "Task with missing evidence",
      "status": "done",
      "evidence": ["proofs/missing-file.txt"]
    }
  ]
}
```

**examples/invalid/manifest.json:**
```json
{
  "schema_version": 1,
  "project": "invalid-demo",
  "tasks": []
}
```

[STEERING steer-2acbc380-3e50-4c6a-be81-940f84b69155: Revised the design to use a single stdlib core at skills/check-handoff/scripts/, thin root handoffcheck.py importer, Python Hypothesis for property tests, explicit reasons in task_results, validate --root before evidence checks, and reject symlinks for simplicity. All corrections from steer-2acbc380-3e50-4c6a-be81-940f84b69155 have been incorporated.]
