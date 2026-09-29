# HandoffCheck evidence index

This index links the project artifacts to the Kiro University Challenge lesson fields in the [requirement map](challenge-map.md). It separates files that a reader can inspect from local Kiro actions observed during development. The [native-use evidence page](native-evidence.md) gives concise, source-checked observations. The organizer has not confirmed any credits as of 2026-09-29.

## Reproducible product checks

From the repository root, run the commands in the [README](../README.md#try-the-examples). The three synthetic manifests are [ready](../examples/ready/manifest.json), [missing](../examples/missing/manifest.json), and [invalid](../examples/invalid/manifest.json). Their expected results and exit codes are `READY_TO_REVIEW`/0, `NEEDS_WORK`/1, and `INVALID_MANIFEST`/2. The missing case reports `proofs/missing-file.txt` and selects its first task for follow-up.

The [CLI](../handoffcheck.py) calls the shared [core](../skills/check-handoff/scripts/handoffcheck_core.py). The [tests](../tests/) include six generated-input properties in [test_properties.py](../tests/test_properties.py). The latest observed local test run was **38 passed, 1 skipped**. The checker validates evidence presence and size, not factual correctness.

## Lesson evidence and limits

The [recorded demo](demo.webm) runs the real CLI against synthetic examples and shows the relevant project files. Its Kiro scenes are labeled as previously observed use; the video does not replay a Kiro session. The [native-use evidence page](native-evidence.md) records those observations.

| Final form item | Inspectable project artifact | Locally observed use |
|---|---|---|
| 1. Spec-driven development | [Requirements](../.kiro/specs/handoffcheck/requirements.md), [design](../.kiro/specs/handoffcheck/design.md), [tasks](../.kiro/specs/handoffcheck/tasks.md), [CLI](../handoffcheck.py), and [core](../skills/check-handoff/scripts/handoffcheck_core.py) | Kiro CLI generated the Spec and main implementation; independent product checks passed locally. |
| 2. Steering | [Project steering](../.kiro/steering/handoff-constraints.md) | Kiro CLI `/context` displayed the steering file as active, and Kiro referenced its constraints. |
| 3. Hooks | [CLI prompt Hook](../.kiro/hooks/cli-quick-tests.json) and [IDE save Hook](../.kiro/hooks/save-quick-tests.json) | A native Kiro CLI `UserPromptSubmit` trigger completed and supplied a pytest summary of 36 passed, 1 skipped to Kiro's context. The IDE `PostFileSave` trigger has not been observed. |
| 4. Property-based testing | [Six Hypothesis properties](../tests/test_properties.py), [native Spec tasks](../.kiro/specs/handoffcheck/tasks.md), [native PBT results](../.kiro/specs/handoffcheck/tasks.meta.json), and [pinned test dependencies](../requirements.txt) | Kiro IDE Spec tasks 8.1 and 8.2 each ran 100 examples and updated native `pbtResults` to `passed`. Independent QA found an exit-code false positive in the first path test; Kiro repaired its CLI path and output assertion, added the missing empty-evidence case, reran both properties, and updated their native results. Codex then ran the final suite: 38 passed, 1 skipped. |
| 5. Powers | [Power manifest](../plugin.json), [skill](../skills/check-handoff/SKILL.md), and [bundled core](../skills/check-handoff/scripts/handoffcheck_core.py) | The official Kiro CLI installed a clean local export at user level. In a fresh synthetic workspace, Kiro activated the Power, read its skill, and ran the installed checker; stdout showed `READY_TO_REVIEW` and exit code 0. |
| 6. MCP | [Server](../handoffcheck_mcp.py), [project MCP configuration](../.kiro/settings/mcp.json), and [pinned SDK](../requirements-mcp.txt) | Kiro CLI reported the server running with one tool and invoked `inspect_example(name=missing)`. It returned `NEEDS_WORK` and the missing evidence path. An independent stdio client checked four cases. |
| 7. Custom agents | [Read-only `handoff-reviewer` configuration](../.kiro/agents/handoff-reviewer.json) | The agent ran in Kiro CLI with only the read tool and inspected the Spec, core, examples, and CLI. Its final review corrected an initial misread of the CLI location. |
| Free Bonus 2. Package a Kiro power | [Power manifest](../plugin.json), [skill](../skills/check-handoff/SKILL.md), [bundled CLI](../handoffcheck.py), and [core](../skills/check-handoff/scripts/handoffcheck_core.py) | The package structure and clean official CLI installation were checked; Kiro activated and ran its bundled checker on a fresh synthetic case. Installation from the public GitHub URL remains to be checked after release. |

The all-seven completion award depends on organizer acceptance of every lesson. Local checks, Kiro observations, and the recorded demo cannot establish that award or any redemption.
