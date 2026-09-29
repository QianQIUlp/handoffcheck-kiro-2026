import subprocess
import sys
import json
from pathlib import Path
from tempfile import TemporaryDirectory


def run_hc(manifest_path, root=None, fmt='text'):
    cmd = [sys.executable, 'handoffcheck.py', str(manifest_path)]
    if root:
        cmd.extend(['--root', str(root)])
    cmd.extend(['--format', fmt])
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
    return result


def test_ready_example():
    r = run_hc(Path('examples/ready/manifest.json'))
    assert r.returncode == 0
    assert 'READY_TO_REVIEW' in r.stdout


def test_missing_example():
    r = run_hc(Path('examples/missing/manifest.json'))
    assert r.returncode == 1
    assert 'NEEDS_WORK' in r.stdout


def test_invalid_example():
    r = run_hc(Path('examples/invalid/manifest.json'))
    assert r.returncode == 2


def test_json_output():
    r = run_hc(Path('examples/ready/manifest.json'), fmt='json')
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data['schema_version'] == 1
    assert data['result'] == 'READY_TO_REVIEW'


def test_pending_task_with_valid_evidence():
    with TemporaryDirectory() as tmpdir:
        manifest = Path(tmpdir) / 'm.json'
        manifest.write_text(json.dumps({
            'schema_version': 1,
            'project': 'test',
            'tasks': [{'id': 'T1', 'title': 'Task', 'status': 'pending', 'evidence': ['file.txt']}]
        }))
        (Path(tmpdir) / 'file.txt').write_text('content')
        r = run_hc(manifest, root=tmpdir)
        assert r.returncode == 1
        assert 'NEEDS_WORK' in r.stdout
        assert 'pending' in r.stdout.lower()


def test_invalid_root():
    r = run_hc(Path('examples/ready/manifest.json'), root='/nonexistent')
    assert r.returncode == 2


def test_explicit_reasons():
    with TemporaryDirectory() as tmpdir:
        manifest = Path(tmpdir) / 'm.json'
        manifest.write_text(json.dumps({
            'schema_version': 1,
            'project': 'test',
            'tasks': [{'id': 'T1', 'title': 'Task', 'status': 'done', 'evidence': ['missing.txt']}]
        }))
        r = run_hc(manifest, root=tmpdir, fmt='json')
        assert r.returncode == 1
        data = json.loads(r.stdout)
        assert data['task_results'][0]['reason'] is not None
        assert 'missing' in data['task_results'][0]['reason'].lower()
