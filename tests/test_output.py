import json
from handoffcheck_core import format_output


def test_json_output_structure():
    d = {'schema_version': 1, 'project': 'p', 'result': 'READY_TO_REVIEW', 'task_results': [], 'next_task': None}
    out = format_output(d, 'json')
    parsed = json.loads(out)
    assert parsed['schema_version'] == 1
    assert parsed['project'] == 'p'
    assert parsed['result'] == 'READY_TO_REVIEW'


def test_text_output_contains():
    d = {'schema_version': 1, 'project': 'p', 'result': 'READY_TO_REVIEW', 'task_results': [], 'next_task': None}
    out = format_output(d, 'text')
    assert 'Project: p' in out
    assert 'READY_TO_REVIEW' in out


def test_text_with_next_task():
    d = {'schema_version': 1, 'project': 'p', 'result': 'NEEDS_WORK', 'task_results': [], 'next_task': {'id': 'T1', 'title': 'Task', 'status': 'pending', 'reason': 'task is pending'}}
    out = format_output(d, 'text')
    assert 'Next Task: T1' in out
    assert 'task is pending' in out
