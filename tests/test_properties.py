import json
import subprocess
import sys
import hypothesis.strategies as st
from hypothesis import given, settings
from pathlib import Path
from tempfile import TemporaryDirectory

from handoffcheck_core import parse_manifest, validate_paths, check_ready, EXIT_INVALID_MANIFEST

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


# Property 5: Done Task Needs Evidence
# Generate varied done tasks with empty, missing, empty-file, or nonregular evidence;
# assert they never become READY_TO_REVIEW
@st.composite
def valid_filename(draw):
    """Generate valid POSIX-style filenames that won't cause normalization issues."""
    name = draw(non_empty)
    # Ensure it doesn't contain problematic characters like backslash
    name = name.replace(chr(92), 'b')  # replace backslash with 'b'
    name = name.replace('/', 's')  # replace forward slash with 's'
    return name

@given(non_empty, valid_filename())
@settings(max_examples=100)
def test_prop5_done_task_needs_evidence(task_id, filename):
    """Property 5: Done Task Needs Evidence - Validates Requirements 4.1, 4.2, 4.3

    For any task with status 'done' that has an empty evidence array or
    missing/empty/nonregular evidence files, check_ready() shall return False
    for readiness.
    """
    m = {'tasks': [{'id': task_id, 'title': 'T', 'status': 'done', 'evidence': [filename]}]}

    # Normalize the key to match check_ready's behavior
    normalized_key = Path(*Path(filename).parts).as_posix()

    # Test 1: Missing file evidence
    ready1, _ = check_ready(m, {normalized_key: {'exists': False, 'is_regular': False, 'is_nonempty': False, 'error': 'file does not exist'}})
    assert ready1 is False, f"Done task with missing evidence should not be READY"

    # Test 2: Empty file evidence
    ready2, _ = check_ready(m, {normalized_key: {'exists': True, 'is_regular': True, 'is_nonempty': False, 'error': 'file is empty'}})
    assert ready2 is False, f"Done task with empty file should not be READY"

    # Test 3: Non-regular file (directory) evidence
    ready3, _ = check_ready(m, {normalized_key: {'exists': True, 'is_regular': False, 'is_nonempty': False, 'error': 'file is not a regular file'}})
    assert ready3 is False, f"Done task with non-regular file should not be READY"

    # Test 4: Valid file (this should be ready)
    ready4, _ = check_ready(m, {normalized_key: {'exists': True, 'is_regular': True, 'is_nonempty': True, 'error': None}})
    assert ready4 is True, f"Done task with valid evidence should be READY"

    # Test 5: Empty evidence list (no evidence listed)
    m_empty = {'tasks': [{'id': task_id, 'title': 'T', 'status': 'done', 'evidence': []}]}
    ready5, reason5 = check_ready(m_empty, {})
    assert ready5 is False, f"Done task with empty evidence list should not be READY"
    assert reason5['reason'] == 'no evidence listed', f"Expected 'no evidence listed' reason, got {reason5['reason']}"


# Task 8.1 / design Property 2: Path Containment Security.
# The Kiro-generated test name uses 6 as its sequence number in this file.
# Generate varied invalid evidence paths; assert that the real validator rejects each with INVALID_MANIFEST/exit 2
@st.composite
def invalid_path_strategy(draw):
    """Generate varied invalid evidence paths that should be rejected."""
    filename = draw(non_empty)
    path_type = draw(st.sampled_from([
        'absolute', 'dotdot', 'windows_drive', 'unc_path', 'backslash', 'backslash_in_path'
    ]))

    if path_type == 'absolute':
        return ('/' + filename, 'absolute path')
    elif path_type == 'dotdot':
        return ('..' + '/' + filename, 'path traversal (..)')
    elif path_type == 'windows_drive':
        return ('C:' + filename, 'Windows drive letter')
    elif path_type == 'unc_path':
        return ('//' + filename, 'UNC path')
    elif path_type == 'backslash':
        return (chr(92) + filename, 'backslash at start')
    else:
        # backslash in path
        return ('dir' + chr(92) + filename, 'backslash in path')


@given(invalid_path_strategy())
@settings(max_examples=100, deadline=None)
def test_prop6_path_containment_security(path_data):
    """Design Property 2: Path Containment Security - Validates Requirements 3.1, 3.4

    Generate varied invalid evidence paths; assert that the real validator rejects
    each with INVALID_MANIFEST/exit 2.

    Tests paths that should be rejected:
    - Absolute paths
    - Paths with ".." segments
    - Windows paths (drive letters)
    - UNC paths
    - Paths with backslashes
    """
    invalid_path, description = path_data
    project_name = 'test-project'
    task_id = 'task-1'

    m = {
        'schema_version': 1,
        'project': project_name,
        'tasks': [{'id': task_id, 'title': 'Test Task', 'status': 'done', 'evidence': [invalid_path]}]
    }

    with TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / 'manifest.json'
        manifest_path.write_text(json.dumps(m))

        # Get absolute path to handoffcheck.py
        script_path = str(Path(__file__).parent.parent / 'handoffcheck.py')

        # Run the CLI and check exit code
        result = subprocess.run(
            [sys.executable, script_path, str(manifest_path)],
            cwd=Path(tmpdir),
            capture_output=True,
            text=True
        )

        assert result.returncode == EXIT_INVALID_MANIFEST, \
            f"Expected exit code {EXIT_INVALID_MANIFEST} for invalid path '{invalid_path}' ({description}), got {result.returncode}. Stderr: {result.stderr}"

        # Verify the output contains INVALID_MANIFEST in stdout or error message in stderr for genuine validation failure
        assert "INVALID_MANIFEST" in result.stdout or "Invalid evidence path" in result.stderr, \
            f"Expected 'INVALID_MANIFEST' in stdout or 'Invalid evidence path' in stderr for invalid path '{invalid_path}' ({description}). Stdout: {result.stdout}, Stderr: {result.stderr}"
