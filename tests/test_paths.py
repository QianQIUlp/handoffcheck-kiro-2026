import pytest
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from handoffcheck_core import validate_paths


def test_validate_valid():
    with TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / 'proof').mkdir()
        (Path(tmpdir) / 'proof' / 'f.txt').write_text('x')
        m = {'tasks': [{'id': 'T1', 'evidence': ['proof/f.txt']}]}
        r = validate_paths(m, Path(tmpdir))
        assert r is not None and len(r) == 1


def test_validate_absolute():
    m = {'tasks': [{'id': 'T1', 'evidence': ['/abs/path']}]}
    with TemporaryDirectory() as tmpdir:
        assert validate_paths(m, Path(tmpdir)) is None


def test_validate_backslash():
    m = {'tasks': [{'id': 'T1', 'evidence': ['path\\file']}]}
    with TemporaryDirectory() as tmpdir:
        assert validate_paths(m, Path(tmpdir)) is None


def test_validate_dotdot():
    m = {'tasks': [{'id': 'T1', 'evidence': ['../escape']}]}
    with TemporaryDirectory() as tmpdir:
        assert validate_paths(m, Path(tmpdir)) is None


def test_validate_symlink_rejected():
    with TemporaryDirectory() as tmpdir:
        actual = Path(tmpdir) / 'actual.txt'
        actual.write_text('x')
        link = Path(tmpdir) / 'link.txt'
        try:
            link.symlink_to(actual)
        except (OSError, NotImplementedError):
            pytest.skip('symlinks not supported')
        m = {'tasks': [{'id': 'T1', 'evidence': ['link.txt']}]}
        assert validate_paths(m, Path(tmpdir)) is None


def test_validate_escape_root():
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / 'root'
        root.mkdir()
        (Path(tmpdir) / 'outside.txt').write_text('x')
        m = {'tasks': [{'id': 'T1', 'evidence': ['../outside.txt']}]}
        assert validate_paths(m, root) is None
