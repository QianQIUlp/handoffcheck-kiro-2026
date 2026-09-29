# HandoffCheck

HandoffCheck is an offline, read-only check for AI task handoffs. It validates a JSON task manifest, checks that each listed evidence path points to a non-empty regular file, and identifies the first task that still needs work. **A file's presence does not prove its contents are correct or that the task was completed.** The examples contain synthetic data only.

## Try the examples

From the repository root, with Python 3 available:

```sh
python handoffcheck.py examples/ready/manifest.json
python handoffcheck.py examples/missing/manifest.json --format json
python handoffcheck.py examples/invalid/manifest.json --format json
```

| Example | Result | Exit code |
|---|---|---:|
| `ready` | `READY_TO_REVIEW` | 0 |
| `missing` | `NEEDS_WORK` | 1 |
| `invalid` | `INVALID_MANIFEST` | 2 |

Exit codes 1 and 2 are expected for their respective examples. The checker itself uses only the Python standard library and makes no network requests. Use `--root DIR` to set the evidence directory; otherwise it uses the manifest's directory. Use `--format json` for stable machine-readable output. Run `python handoffcheck.py --help` for the full CLI syntax.

## Manifest format

```json
{
  "schema_version": 1,
  "project": "sample-handoff",
  "tasks": [
    {
      "id": "T1",
      "title": "Prepare the report",
      "status": "done",
      "evidence": ["proofs/report.txt"]
    }
  ]
}
```

Each task needs a unique non-empty `id`, a non-empty `title`, a `pending` or `done` status, and an array of relative evidence paths. A `done` task needs at least one valid evidence file; every listed file must be non-empty. A `pending` task still needs work even if its evidence files exist. Paths use forward slashes and must stay within the evidence root; absolute paths, drive paths, backslashes, `..` traversal, an evidence file that is a symlink, and paths resolving outside the root are rejected. The checker reads the manifest and file metadata, but does not read evidence file contents or modify inputs.

## Run the tests

The optional test dependencies are pinned in [`requirements.txt`](requirements.txt). On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest tests -q
```

The tests include example-level checks and four Hypothesis properties in [`tests/test_properties.py`](tests/test_properties.py). The latest local run reported **36 passed, 1 skipped**; the Kiro IDE Correctness workflow has not yet been run. The project Hooks currently use the Windows `.venv\Scripts\python.exe` path.

For the optional MCP server, install [`requirements-mcp.txt`](requirements-mcp.txt) into the same virtual environment and start Kiro with that environment's `Scripts` directory first on `PATH`. The project [MCP configuration](.kiro/settings/mcp.json) runs `python -m handoffcheck_mcp`, so `python` must resolve to the environment containing the SDK.

## Kiro project files

- [Spec requirements](.kiro/specs/handoffcheck/requirements.md), [design](.kiro/specs/handoffcheck/design.md), and [tasks](.kiro/specs/handoffcheck/tasks.md) describe the Kiro-led implementation. The CLI entry point is [`handoffcheck.py`](handoffcheck.py); the reusable standard-library core is [`skills/check-handoff/scripts/handoffcheck_core.py`](skills/check-handoff/scripts/handoffcheck_core.py).
- [Steering](.kiro/steering/handoff-constraints.md) records the read-only and evidence limits. [CLI Hook](.kiro/hooks/cli-quick-tests.json) and [IDE save Hook](.kiro/hooks/save-quick-tests.json) configure quick tests. The CLI Hook has been observed running; the IDE save Hook has not.
- [`plugin.json`](plugin.json) and the [check-handoff skill](skills/check-handoff/SKILL.md) package a Kiro Power. A clean local copy of the package ran the ready example, but native Power installation and activation are pending.
- [MCP configuration](.kiro/settings/mcp.json) launches [`handoffcheck_mcp.py`](handoffcheck_mcp.py), whose single `inspect_example` tool accepts only `ready`, `missing`, or `invalid`. Its optional SDK dependency is pinned in [`requirements-mcp.txt`](requirements-mcp.txt). A real Kiro CLI MCP call and independent stdio checks have been observed; no IDE claim follows from that.
- The [read-only custom agent](.kiro/agents/handoff-reviewer.json) was invoked in Kiro CLI to review the Spec, source, and examples.

See the [evidence index](docs/evidence-index.md) for observed results and remaining verification. The project has not been publicly submitted, and no challenge credits are claimed here.
