---
name: check-handoff
description: Validate handoff manifests and evidence files for AI task交接
---

This skill is loaded automatically by Kiro when the HandoffCheck Power is activated. It provides the `handoffcheck` command for validating task交接 packages.

## Usage

Run the package-root `handoffcheck.py` against a user-specified local manifest:

```bash
python handoffcheck.py <manifest> [--root <dir>] [--format text|json]
```

### Arguments

- `<manifest>`: Path to the manifest.json file (required)
- `--root`: Root directory for evidence files (optional, defaults to manifest directory)
- `--format`: Output format - `text` (human-readable) or `json` (machine-readable, default: `text`)

## Exit Codes

| Code | Result | Meaning |
|------|--------|---------|
| 0 | READY_TO_REVIEW | All tasks are done AND all listed evidence files are non-empty and accessible |
| 1 | NEEDS_WORK | Manifest is valid but tasks are not ready (pending tasks, missing evidence, or empty files) |
| 2 | INVALID_MANIFEST | JSON/structure invalid (bad JSON, duplicate IDs, illegal status/path, or root directory error) |

## Constraints

- **Read-only**: Evidence files are only checked for existence/size, not read or modified
- **No network**: No external dependencies or network access
- **Explicit errors**: All error conditions produce clear diagnostics to stderr
- **Evidence presence does not prove correctness**: File checks only verify non-empty regular files; content validity is not assessed

## Core Modules

- `skills/check-handoff/scripts/handoffcheck_core.py`: Validation logic (reusable, no writes/network)
- `handoffcheck.py`: CLI entry point (imports from core module)
