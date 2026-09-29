# Tasks Document: HandoffCheck CLI Tool

## Implementation Tasks

### Task 1: Core Module ✅
- [x] Single stdlib core at `skills/check-handoff/scripts/handoffcheck_core.py`
- [x] Functions: parse_manifest, validate_paths, validate_evidence, check_ready, format_output
- [x] Exit codes: 0=READY, 1=NEEDS_WORK, 2=INVALID_MANIFEST

### Task 2: CLI Wrapper ✅
- [x] Root `handoffcheck.py` imports core from skills/check-handoff/scripts
- [x] argparse with manifest positional, --root, --format options
- [x] Default root to manifest file directory
- [x] Validate --root before evidence checks (exit 2 if invalid)

### Task 3: Examples ✅
- [x] `examples/ready/manifest.json` + `proofs/test-report.txt` (READY_TO_REVIEW)
- [x] `examples/missing/manifest.json` (missing evidence → NEEDS_WORK)
- [x] `examples/invalid/manifest.json` (empty tasks → INVALID_MANIFEST)

### Task 4: Unit Tests ✅
- [x] test_manifest.py: JSON parsing, schema validation
- [x] test_paths.py: path security (absolute, backslash, .., symlinks)
- [x] test_evidence.py: file existence, empty, directory
- [x] test_ready.py: readiness logic with explicit reasons
- [x] test_output.py: text/JSON formatting

### Task 5: Integration Tests ✅
- [x] test_integration.py: end-to-end CLI scenarios
- [x] Verify exit codes, output format, explicit reasons

### Task 6: Property Tests (Hypothesis) ✅
- [x] test_properties.py: 4 properties from brief
- [x] Property 1: Deterministic output (same input = same output)
- [x] Property 2: Done task without evidence → not READY
- [x] Property 3: Removing only evidence → not READY
- [x] Property 4: Invalid paths rejected

### Task 7: Validation ✅
- [x] Run pytest tests (36 passed, 1 skipped)
- [x] Run CLI examples: ready, missing, invalid
- [x] MCP inspect_example validated (missing example → NEEDS_WORK)

## Not Implemented (IDE-only)
- [ ] Native IDE Correctness property workflow
