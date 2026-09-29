import json
import hypothesis.strategies as st
from hypothesis import given, settings
from pathlib import Path
from tempfile import TemporaryDirectory

from handoffcheck_core import parse_manifest, validate_paths, check_ready

non_empty = st.text(min_size=1, max_size=15)
path_kinds = st.sampled_from(['abs', 'backslash', 'dotdot', 'colon'])


@given(non_empty, non_empty)
@settings(max_examples=30)
def test_prop1_deterministic(project, task_id):
    m = {'schema_version': 1, 'project': project, 'tasks': [{'id': task_id, 'title': 'T', 'status': 'done', 'evidence': ['f.txt']}]}
    with TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / 'm.json'
        p.write_text(json.dumps(m))
        assert parse_manifest(p) == parse_manifest(p)


@given(non_empty)
@settings(max_examples=30)
def test_prop2_done_empty_evidence(task_id):
    m = {'tasks': [{'id': task_id, 'title': 'T', 'status': 'done', 'evidence': []}]}
    ready, _ = check_ready(m, {})
    assert ready is False


@given(non_empty)
@settings(max_examples=30)
def test_prop3_evidence_removed(task_id):
    m = {'tasks': [{'id': task_id, 'title': 'T', 'status': 'done', 'evidence': ['f.txt']}]}
    ready1, _ = check_ready(m, {'f.txt': {'exists': True, 'is_regular': True, 'is_nonempty': True, 'error': None}})
    assert ready1 is True
    ready2, _ = check_ready(m, {'f.txt': {'exists': False, 'is_regular': False, 'is_nonempty': False, 'error': 'gone'}})
    assert ready2 is False


@given(non_empty, path_kinds)
@settings(max_examples=30)
def test_prop4_invalid_paths(filename, kind):
    if kind == 'abs':
        path_str = '/' + filename
    elif kind == 'backslash':
        path_str = 'dir' + chr(92) + filename
    elif kind == 'dotdot':
        path_str = '..' + '/' + filename
    else:
        path_str = 'C:' + filename

    m = {'tasks': [{'id': 'T1', 'evidence': [path_str]}]}
    with TemporaryDirectory() as tmpdir:
        r = validate_paths(m, Path(tmpdir))
        assert r is None, f'Expected {path_str} to be rejected'
