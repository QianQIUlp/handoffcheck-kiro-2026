---
name: check-handoff
description: Validate handoff manifests and evidence files for AI task交接
---

This skill is loaded automatically by Kiro when the HandoffCheck Power is activated. It provides the `handoffcheck` command for validating task交接 packages.

## Finding the checker

The HandoffCheck Power installs a bundled `handoffcheck.py` checker. Its location depends on how Kiro was invoked:

- **Via CLI V3 (native Power)**: The Power is installed at `~/.kiro/powers/installed/handoffcheck` on Windows (using your user profile), or `~/.kiro/powers/installed/handoffcheck` on Unix-like systems.
- **In a source checkout**: Use the repository root, where `plugin.json` and `handoffcheck.py` reside. This `SKILL.md` is under `skills/check-handoff/`.

Verify the checker exists at the expected location by checking for `plugin.json` (the Power manifest) and `handoffcheck.py` in the same directory.

## Usage

Run the checker's `handoffcheck.py` against a manifest file in your workspace:

```bash
python /path/to/handoffcheck.py <manifest> [--root <dir>] [--format text|json]
```

### Arguments

- `<manifest>`: Path to the manifest.json file (required). This can be any manifest file in your workspace.
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

## Example invocations

Assuming the Power is installed at `~/.kiro/powers/installed/handoffcheck` and your workspace manifest is at `examples/ready/manifest.json`:

```bash
# Using a relative path to the installed Power (portable across users)
python ~/.kiro/powers/installed/handoffcheck/handoffcheck.py examples/ready/manifest.json

# With explicit root directory
python ~/.kiro/powers/installed/handoffcheck/handoffcheck.py examples/ready/manifest.json --root .

# In JSON output mode
python ~/.kiro/powers/installed/handoffcheck/handoffcheck.py examples/ready/manifest.json --format json
```

On Windows PowerShell, use the user profile environment variable:

```powershell
# PowerShell example
python "$env:USERPROFILE\.kiro\powers\installed\handoffcheck\handoffcheck.py" examples/ready/manifest.json
```
