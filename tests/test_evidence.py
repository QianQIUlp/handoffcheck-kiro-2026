from pathlib import Path
from tempfile import TemporaryDirectory

from handoffcheck_core import validate_evidence


def test_evidence_valid():
    with TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / 'f.txt').write_text('x')
        r = validate_evidence([('f.txt', Path('f.txt'))], Path(tmpdir))
        assert r['f.txt']['is_nonempty'] is True


def test_evidence_missing():
    with TemporaryDirectory() as tmpdir:
        r = validate_evidence([('missing.txt', Path('missing.txt'))], Path(tmpdir))
        assert r['missing.txt']['exists'] is False


def test_evidence_empty():
    with TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / 'empty.txt').write_text('')
        r = validate_evidence([('empty.txt', Path('empty.txt'))], Path(tmpdir))
        assert r['empty.txt']['is_nonempty'] is False


def test_evidence_directory():
    with TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / 'dir').mkdir()
        r = validate_evidence([('dir', Path('dir'))], Path(tmpdir))
        assert r['dir']['is_regular'] is False
