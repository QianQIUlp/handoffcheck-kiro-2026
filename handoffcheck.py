import argparse
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'skills' / 'check-handoff' / 'scripts'))

from handoffcheck_core import (
    parse_manifest, validate_paths, validate_evidence,
    check_ready, format_output,
    EXIT_READY, EXIT_NEEDS_WORK, EXIT_INVALID_MANIFEST,
    RESULT_READY, RESULT_NEEDS_WORK, RESULT_INVALID_MANIFEST
)


def normalize_path(p: str) -> str:
    return Path(*Path(p).parts).as_posix()


def build_result_data(manifest_data: dict, evidence_results: dict, is_ready: bool, next_task: dict) -> dict:
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

    return {
        'schema_version': 1,
        'project': manifest_data['project'],
        'result': RESULT_READY if is_ready else RESULT_NEEDS_WORK,
        'task_results': task_results,
        'next_task': next_task
    }


def build_error_result_data(project: str = 'unknown') -> dict:
    return {
        'schema_version': 1,
        'project': project,
        'result': RESULT_INVALID_MANIFEST,
        'task_results': [],
        'next_task': None
    }


def main():
    parser = argparse.ArgumentParser(description='Validate handoff manifests and evidence files')
    parser.add_argument('manifest', type=Path, help='Path to manifest.json file')
    parser.add_argument('--root', type=Path, default=None, help='Root directory (default: manifest dir)')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')

    args = parser.parse_args()
    root_dir = args.root if args.root else args.manifest.parent

    # Validate --root
    if not root_dir.exists():
        print('Error: --root directory does not exist: ' + str(root_dir), file=sys.stderr)
        if args.format == 'json':
            print(json.dumps(build_error_result_data(), indent=2, sort_keys=True))
        sys.exit(EXIT_INVALID_MANIFEST)
    if not root_dir.is_dir():
        print('Error: --root is not a directory: ' + str(root_dir), file=sys.stderr)
        if args.format == 'json':
            print(json.dumps(build_error_result_data(), indent=2, sort_keys=True))
        sys.exit(EXIT_INVALID_MANIFEST)
    if not root_dir.is_absolute():
        root_dir = root_dir.resolve()

    # Parse manifest
    manifest_data = parse_manifest(args.manifest)
    if manifest_data is None:
        print('Error: Invalid or missing manifest: ' + str(args.manifest), file=sys.stderr)
        if args.format == 'json':
            print(json.dumps(build_error_result_data(), indent=2, sort_keys=True))
        sys.exit(EXIT_INVALID_MANIFEST)

    # Validate paths
    validated_paths = validate_paths(manifest_data, root_dir)
    if validated_paths is None:
        print('Error: Invalid evidence path in manifest', file=sys.stderr)
        if args.format == 'json':
            print(json.dumps(build_error_result_data(manifest_data.get('project', 'unknown')), indent=2, sort_keys=True))
        sys.exit(EXIT_INVALID_MANIFEST)

    evidence_results = validate_evidence(validated_paths, root_dir)
    is_ready, next_task = check_ready(manifest_data, evidence_results)

    result_data = build_result_data(manifest_data, evidence_results, is_ready, next_task)
    output = format_output(result_data, args.format)
    print(output)
    sys.exit(EXIT_READY if is_ready else EXIT_NEEDS_WORK)


if __name__ == '__main__':
    main()
