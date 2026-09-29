import pytest
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from handoffcheck_core import parse_manifest


def test_parse_valid_manifest():
    with TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / 'manifest.json'
        data = {'schema_version': 1, 'project': 'test', 'tasks': [{'id': 'T1', 'title': 'Test', 'status': 'done', 'evidence': []}]}
        manifest_path.write_text(json.dumps(data))
        result = parse_manifest(manifest_path)
        assert result is not None
        assert result['project'] == 'test'


def test_parse_invalid_json():
    with TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / 'm.json'
        p.write_text('{ invalid }')
        assert parse_manifest(p) is None


def test_parse_non_object_top():
    with TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / 'm.json'
        p.write_text('"just a string"')
        assert parse_manifest(p) is None


def test_parse_non_object_task():
    with TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / 'm.json'
        p.write_text(json.dumps({'schema_version': 1, 'project': 'x', 'tasks': ['not an object']}))
        assert parse_manifest(p) is None


def test_parse_bool_schema_version():
    with TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / 'm.json'
        # Bool is rejected even if tasks array has one otherwise-valid task
        p.write_text(json.dumps({'schema_version': True, 'project': 'x', 'tasks': [{'id': 'T1', 'title': 'Test', 'status': 'done', 'evidence': []}]}))
        assert parse_manifest(p) is None


def test_parse_empty_tasks():
    with TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / 'm.json'
        p.write_text(json.dumps({'schema_version': 1, 'project': 'x', 'tasks': []}))
        assert parse_manifest(p) is None


def test_parse_duplicate_ids():
    with TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / 'm.json'
        p.write_text(json.dumps({'schema_version': 1, 'project': 'x', 'tasks': [{'id': 'T1', 'title': 'a', 'status': 'done', 'evidence': []}, {'id': 'T1', 'title': 'b', 'status': 'done', 'evidence': []}]}))
        assert parse_manifest(p) is None


def test_parse_invalid_status():
    with TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / 'm.json'
        p.write_text(json.dumps({'schema_version': 1, 'project': 'x', 'tasks': [{'id': 'T1', 'title': 'a', 'status': 'bad', 'evidence': []}]}))
        assert parse_manifest(p) is None
