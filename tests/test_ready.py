from pathlib import Path
from tempfile import TemporaryDirectory

from handoffcheck_core import check_ready


def test_all_ready():
    m = {'tasks': [{'id': 'T1', 'title': 'Task', 'status': 'done', 'evidence': ['f.txt']}]}
    e = {'f.txt': {'exists': True, 'is_regular': True, 'is_nonempty': True, 'error': None}}
    ready, next_t = check_ready(m, e)
    assert ready is True
    assert next_t is None


def test_pending_not_ready():
    m = {'tasks': [{'id': 'T1', 'title': 'Task', 'status': 'pending', 'evidence': ['f.txt']}]}
    e = {'f.txt': {'exists': True, 'is_regular': True, 'is_nonempty': True, 'error': None}}
    ready, next_t = check_ready(m, e)
    assert ready is False
    assert next_t is not None
    assert next_t['status'] == 'pending'


def test_done_no_evidence():
    m = {'tasks': [{'id': 'T1', 'title': 'Task', 'status': 'done', 'evidence': []}]}
    e = {}
    ready, next_t = check_ready(m, e)
    assert ready is False
    assert next_t['reason'] == 'no evidence listed'


def test_one_evidence_missing():
    m = {'tasks': [{'id': 'T1', 'title': 'Task', 'status': 'done', 'evidence': ['a.txt', 'b.txt']}]}
    e = {'a.txt': {'exists': True, 'is_regular': True, 'is_nonempty': True, 'error': None}, 'b.txt': {'exists': False, 'is_regular': False, 'is_nonempty': False, 'error': 'missing'}}
    ready, next_t = check_ready(m, e)
    assert ready is False


def test_first_not_ready_in_order():
    m = {'tasks': [
        {'id': 'T1', 'title': 'T1', 'status': 'done', 'evidence': ['f.txt']},
        {'id': 'T2', 'title': 'T2', 'status': 'pending', 'evidence': []},
        {'id': 'T3', 'title': 'T3', 'status': 'done', 'evidence': []}
    ]}
    e = {'f.txt': {'exists': True, 'is_regular': True, 'is_nonempty': True, 'error': None}}
    ready, next_t = check_ready(m, e)
    assert ready is False
    assert next_t['id'] == 'T2'
