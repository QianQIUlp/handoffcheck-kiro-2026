import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

EXIT_READY = 0
EXIT_NEEDS_WORK = 1
EXIT_INVALID_MANIFEST = 2

RESULT_READY = "READY_TO_REVIEW"
RESULT_NEEDS_WORK = "NEEDS_WORK"
RESULT_INVALID_MANIFEST = "INVALID_MANIFEST"


def parse_manifest(manifest_path: Path) -> Optional[Dict[str, Any]]:
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return None

    if not isinstance(data, dict):
        return None

    schema_version = data.get('schema_version')
    if type(schema_version) is not int or schema_version != 1:
        return None

    project = data.get('project')
    if not isinstance(project, str) or not project:
        return None

    tasks = data.get('tasks')
    if not isinstance(tasks, list) or len(tasks) == 0:
        return None

    seen_ids = set()
    for task in tasks:
        if not isinstance(task, dict):
            return None

        if not isinstance(task.get('id'), str) or not task.get('id'):
            return None
        if task['id'] in seen_ids:
            return None
        seen_ids.add(task['id'])

        if not isinstance(task.get('title'), str) or not task.get('title'):
            return None

        status = task.get('status')
        if status not in ('pending', 'done'):
            return None

        evidence = task.get('evidence')
        if not isinstance(evidence, list):
            return None
        for e in evidence:
            if not isinstance(e, str) or not e:
                return None

    return data


def validate_paths(manifest_data: Dict[str, Any], root_dir: Path) -> Optional[List[tuple]]:
    validated = []
    root_resolved = root_dir.resolve()

    for task in manifest_data['tasks']:
        for evidence_path_str in task['evidence']:
            if not evidence_path_str:
                return None

            if chr(92) in evidence_path_str:
                return None

            try:
                evidence_path = Path(evidence_path_str)
            except Exception:
                return None

            if evidence_path.is_absolute():
                return None

            if evidence_path_str.startswith(chr(92) + chr(92)):
                return None

            if ':' in evidence_path_str.split('/')[0]:
                return None

            if '..' in evidence_path.parts:
                return None

            # Normalize the path (resolve . and /)
            normalized = Path(*evidence_path.parts)
            normalized_key = normalized.as_posix()

            full_path = root_dir / evidence_path
            if full_path.is_symlink():
                return None

            try:
                resolved = full_path.resolve()
                resolved.relative_to(root_resolved)
            except ValueError:
                return None

            # Return tuple of (normalized_key, original_path)
            validated.append((normalized_key, evidence_path))

    return validated


def validate_evidence(paths: List[tuple], root_dir: Path) -> Dict[str, Any]:
    evidence_results = {}

    for normalized_key, path in paths:
        full_path = root_dir / path

        result = {'exists': False, 'is_regular': False, 'is_nonempty': False, 'error': None}

        try:
            if not full_path.exists():
                result['error'] = 'file does not exist'
            elif full_path.is_symlink():
                result['error'] = 'file is a symlink'
            elif not full_path.is_file():
                result['error'] = 'file is not a regular file'
            else:
                result['exists'] = True
                result['is_regular'] = True
                if full_path.stat().st_size == 0:
                    result['error'] = 'file is empty'
                else:
                    result['is_nonempty'] = True
        except OSError as e:
            result['error'] = str(e)

        evidence_results[normalized_key] = result

    return evidence_results


def check_ready(manifest_data: Dict[str, Any], evidence_results: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
    for task in manifest_data['tasks']:
        task_id = task['id']
        status = task['status']
        evidence = task['evidence']

        # Normalize evidence keys for lookup
        normalized_evidence = []
        for e in evidence:
            normalized = Path(*Path(e).parts).as_posix()
            normalized_evidence.append(normalized)

        reason = None
        if status == 'pending':
            reason = 'task is pending'
        elif not evidence:
            reason = 'no evidence listed'
        else:
            all_valid = all(evidence_results.get(e, {}).get('is_nonempty', False) for e in normalized_evidence)
            if not all_valid:
                missing = [e for e in normalized_evidence if not evidence_results.get(e, {}).get('is_nonempty', False)]
                reason = 'missing evidence: ' + ', '.join(missing)

        if reason:
            return False, {'id': task_id, 'title': task['title'], 'status': status, 'reason': reason}

    return True, None


def format_output(result_data: Dict[str, Any], format_type: str) -> str:
    if format_type == 'json':
        return json.dumps(result_data, indent=2, sort_keys=True)
    else:
        return format_text_output(result_data)


def format_text_output(result_data: Dict[str, Any]) -> str:
    lines = []
    lines.append('Project: ' + result_data['project'])
    lines.append('Result: ' + result_data['result'])
    lines.append('Schema Version: ' + str(result_data['schema_version']))
    lines.append('')

    if result_data.get('task_results'):
        lines.append('Task Results:')
        for tr in result_data['task_results']:
            lines.append('  Task ' + tr['id'] + ': ' + tr['status'])
            if tr.get('reason'):
                lines.append('    Reason: ' + tr['reason'])
            lines.append('    Evidence:')
            for path, info in tr.get('evidence', {}).items():
                status_parts = []
                if info.get('exists'): status_parts.append('exists')
                if info.get('is_regular'): status_parts.append('regular')
                if info.get('is_nonempty'): status_parts.append('non-empty')
                if info.get('error'): status_parts.append('error: ' + info['error'])
                lines.append('      ' + path + ': ' + ', '.join(status_parts))
            lines.append('')

    if result_data.get('next_task'):
        nt = result_data['next_task']
        lines.append('Next Task: ' + nt['id'] + ' - ' + nt['title'])
        lines.append('  Status: ' + nt['status'])
        lines.append('  Reason: ' + nt['reason'])

    return '\n'.join(lines)
