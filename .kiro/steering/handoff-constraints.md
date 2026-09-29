---
inclusion: always
---
# HandoffCheck Project Constraints

- **Read-only**: Inputs/evidence treated as references only
- **Not factual correctness**: File presence or hook output does not imply correctness
- **Synthetic examples**: Example manifests are synthetic; adapt to real use
- **Core CLI dependencies**: No network or external runtime dependencies; the optional MCP adapter uses the pinned SDK in the project venv
- **Explicit errors**: All error conditions must have explicit handling
- **Shared core**: Use `skills/check-handoff/scripts/handoffcheck_core.py`

## Validation Rules

- ALL evidence must be non-empty, regular, and accessible
- schema_version must be integer (reject bool true/false)
- Task statuses: `done`, `pending`
- Evidence paths: POSIX after normalization (handle dot segments)

## Exit Codes

- 0: READY_TO_REVIEW
- 1: NEEDS_WORK
- 2: INVALID_MANIFEST (JSON on stdout with --format json)
