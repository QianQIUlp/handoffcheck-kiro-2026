#!/usr/bin/env python3
"""MCP server for HandoffCheck - read-only inspection of example manifests."""

import json
import sys
from pathlib import Path

# Add the project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'skills' / 'check-handoff' / 'scripts'))

from handoffcheck_core import (
    parse_manifest, validate_paths, validate_evidence,
    check_ready,
    EXIT_READY, EXIT_NEEDS_WORK, EXIT_INVALID_MANIFEST,
    RESULT_READY, RESULT_NEEDS_WORK, RESULT_INVALID_MANIFEST
)
from mcp.server import MCPServer

# Get examples directory relative to this file
EXAMPLES_DIR = project_root / 'examples'

# Supported examples
SUPPORTED_EXAMPLES = {'ready', 'missing', 'invalid'}


def normalize_path(p: str) -> str:
    """Normalize evidence path for lookup."""
    return Path(*Path(p).parts).as_posix()


async def _inspect_example(name: str) -> str:
    """Core implementation of example inspection."""
    if name not in SUPPORTED_EXAMPLES:
        return json.dumps({
            'error': f"Invalid example name '{name}'. Must be one of: {', '.join(sorted(SUPPORTED_EXAMPLES))}"
        })

    manifest_path = EXAMPLES_DIR / name / 'manifest.json'

    if not manifest_path.exists():
        return json.dumps({
            'error': f"Manifest file not found: {manifest_path}"
        })

    # Parse manifest
    manifest_data = parse_manifest(manifest_path)
    if manifest_data is None:
        result_data = {
            'schema_version': 1,
            'project': 'unknown',
            'result': RESULT_INVALID_MANIFEST,
            'task_results': [],
            'next_task': None
        }
        return json.dumps({
            **result_data,
            'manifest_path': str(manifest_path.relative_to(project_root)),
            'exit_code': EXIT_INVALID_MANIFEST
        }, indent=2, sort_keys=True)

    # Validate paths
    root_dir = manifest_path.parent
    validated_paths = validate_paths(manifest_data, root_dir)
    if validated_paths is None:
        result_data = {
            'schema_version': 1,
            'project': manifest_data.get('project', 'unknown'),
            'result': RESULT_INVALID_MANIFEST,
            'task_results': [],
            'next_task': None
        }
        return json.dumps({
            **result_data,
            'manifest_path': str(manifest_path.relative_to(project_root)),
            'exit_code': EXIT_INVALID_MANIFEST
        }, indent=2, sort_keys=True)

    # Validate evidence files
    evidence_results = validate_evidence(validated_paths, root_dir)
    is_ready, next_task = check_ready(manifest_data, evidence_results)

    # Build result data
    task_results = []
    for task in manifest_data['tasks']:
        task_id = task['id']
        status = task['status']
        evidence = task['evidence']

        task_evidence = {}
        for e in evidence:
            normalized_key = normalize_path(e)
            task_evidence[e] = evidence_results.get(normalized_key, {'exists': False, 'is_regular': False, 'is_nonempty': False, 'error': 'not found'})

        reason = None
        if status == 'pending':
            reason = 'task is pending'
        elif not evidence:
            reason = 'no evidence listed'
        else:
            all_valid = all(evidence_results.get(normalize_path(e), {}).get('is_nonempty', False) for e in evidence)
            if not all_valid:
                missing = [normalize_path(e) for e in evidence if not evidence_results.get(normalize_path(e), {}).get('is_nonempty', False)]
                reason = 'missing evidence: ' + ', '.join(missing)

        task_results.append({
            'id': task_id,
            'status': status,
            'evidence': task_evidence,
            'reason': reason
        })

    result_data = {
        'schema_version': 1,
        'project': manifest_data['project'],
        'result': RESULT_READY if is_ready else RESULT_NEEDS_WORK,
        'task_results': task_results,
        'next_task': next_task
    }

    # Get exit code
    if result_data['result'] == RESULT_INVALID_MANIFEST:
        exit_code = EXIT_INVALID_MANIFEST
    elif is_ready:
        exit_code = EXIT_READY
    else:
        exit_code = EXIT_NEEDS_WORK

    # Build explanation for each evidence path
    evidence_explanation = []
    for normalized_key, path_info in evidence_results.items():
        evidence_explanation.append({
            'path': normalized_key,
            'exists': path_info['exists'],
            'is_regular': path_info['is_regular'],
            'is_nonempty': path_info['is_nonempty'],
            'error': path_info.get('error')
        })

    return json.dumps({
        'example': name,
        'manifest_path': str(manifest_path.relative_to(project_root)),
        **result_data,
        'exit_code': exit_code,
        'is_ready': is_ready,
        'evidence_explanation': evidence_explanation
    }, indent=2, sort_keys=True)


def main():
    """Run the MCP server."""
    mcp = MCPServer("handoffcheck-mcp")

    @mcp.tool()
    async def inspect_example(name: str) -> str:
        """Inspect a HandoffCheck example manifest and evidence files.

        Args:
            name: Example name - must be 'ready', 'missing', or 'invalid'

        Returns:
            JSON string with validation result, exit code, task results, and evidence-path explanation
        """
        return await _inspect_example(name)

    mcp.run()


if __name__ == "__main__":
    main()
