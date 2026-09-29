# Requirements Document

## Introduction

HandoffCheck is a command-line validation tool that validates handoff manifests and their associated evidence files. The tool ensures that manifests conform to a specified JSON schema, all referenced evidence files exist and are valid, and produces deterministic output indicating the validation status. This enables automated handoff validation in CI/CD pipelines and development workflows.

The tool reads a manifest file (manifest.json) from a root directory, validates its structure and content, checks all evidence files referenced by tasks, and outputs a validation result. Exit codes indicate the validation status: 0 for ready to review, 1 for needs work (pending/done tasks without valid evidence), and 2 for invalid manifest (missing file, invalid path, or schema violation).

## Glossary

- **HandoffCheck**: The CLI tool being specified
- **Manifest**: A UTF-8 encoded JSON file containing project metadata and a tasks array
- **Task**: A unit of work within a manifest, containing an id, title, status, and evidence array
- **Evidence**: A relative path reference to a file that provides supporting information for a task
- **Root Directory**: The base directory where manifest and evidence files are located; defaults to the directory containing the manifest file
- **POSIX Path**: A relative path using forward slashes as separators (no leading slash)
- **Next Task**: The first NOT-READY task in input order (pending status, or done with missing/empty/invalid evidence); null when READY
- **READY**: All tasks are done AND ALL listed evidence files are non-empty, regular, and accessible
- **NEEDS_WORK**: At least one task is pending OR at least one task has missing/empty/invalid evidence

## Requirements

### Requirement 1: Manifest Schema Validation

**User Story:** As a CI/CD pipeline operator, I want to validate that manifest files conform to the expected schema, so that malformed manifests are caught early.

#### Acceptance Criteria

1. WHEN a manifest file is provided, THE HandoffCheck SHALL validate that it is valid UTF-8 JSON
2. WHEN the JSON is valid, THE HandoffCheck SHALL validate that schema_version equals 1 (integer, not boolean)
3. WHEN schema_version equals 1, THE HandoffCheck SHALL validate that project is a non-empty string
4. WHEN project is valid, THE HandoffCheck SHALL validate that tasks is a non-empty array
5. IF the manifest is not valid UTF-8 JSON, THEN THE HandoffCheck SHALL exit with code 2
6. IF schema_version does not equal 1, THEN THE HandoffCheck SHALL exit with code 2
7. IF project is not a non-empty string, THEN THE HandoffCheck SHALL exit with code 2
8. IF tasks is not a non-empty array, THEN THE HandoffCheck SHALL exit with code 2

### Requirement 2: Task Structure Validation

**User Story:** As a developer, I want to validate that each task has the required structure with valid id, title, status, and evidence array.

#### Acceptance Criteria

1. FOR EACH task in the tasks array, THE HandoffCheck SHALL validate that id is a non-empty string and unique
2. FOR EACH task in the tasks array, THE HandoffCheck SHALL validate that title is a non-empty string
3. FOR EACH task in the tasks array, THE HandoffCheck SHALL validate that status is "pending" or "done" (not other values)
4. FOR EACH task in the tasks array, THE HandoffCheck SHALL validate that evidence is an array of non-empty strings
5. IF any task has duplicate id, THE HandoffCheck SHALL exit with code 2
6. IF any task has invalid structure, THE HandoffCheck SHALL exit with code 2

### Requirement 3: Evidence Path Validation

**User Story:** As a security-conscious developer, I want paths to be POSIX-only with no traversal or platform confusion.

#### Acceptance Criteria

1. FOR EACH evidence path, THE HandoffCheck SHALL reject absolute paths, Windows drive letters, UNC paths, backslashes, ".." segments
2. FOR EACH evidence path, THE HandoffCheck SHALL reject symlinks that resolve outside root
3. FOR EACH evidence path with dot segments like "." THE HandoffCheck SHALL normalize to canonical POSIX form
4. IF any path is invalid, THE HandoffCheck SHALL exit with code 2

### Requirement 4: Evidence File Validation

**User Story:** As a reviewer, I want to ensure all evidence files exist, are regular, and non-empty.

#### Acceptance Criteria

1. FOR EACH evidence path in all tasks, THE HandoffCheck SHALL check the file exists and is a regular file and is non-empty
2. IF any listed evidence file is missing, empty, or nonregular, THEN THE HandoffCheck SHALL exit with code 1 (NEEDS_WORK)
3. FOR ALL listed evidence files in a task, ALL must be valid for the task to be READY

### Requirement 5: Output Contracts

**User Story:** As a pipeline integrator, I want deterministic exit codes and output that clearly indicate the validation status.

#### Acceptance Criteria

1. IF all validations pass, all tasks are done, and ALL listed evidence is valid, THEN THE HandoffCheck SHALL output "READY_TO_REVIEW" and exit with code 0
2. IF any evidence is missing/empty/invalid OR any task is pending, THEN THE HandoffCheck SHALL output "NEEDS_WORK" and exit with code 1
3. IF manifest/path/schema/root is invalid, THEN THE HandoffCheck SHALL output "INVALID_MANIFEST" and exit with code 2
4. JSON output SHALL contain exactly: schema_version (1), project (string), result (READY_TO_REVIEW|NEEDS_WORK|INVALID_MANIFEST), task_results (array), next_task (object or null)
5. JSON SHALL output to stdout; diagnostic errors to stderr

### Requirement 6: Deterministic Output

**User Story:** As a developer, I want consistent output across runs with no timestamps or randomness.

#### Acceptance Criteria

1. THE HandoffCheck SHALL produce identical output for identical input
2. THE HandoffCheck SHALL NOT include timestamps, random identifiers, or non-deterministic elements
3. JSON keys SHALL be alphabetically sorted

### Requirement 7: Read-Only Behavior

**User Story:** As a cautious developer, I want the tool to never modify input files.

#### Acceptance Criteria

1. THE HandoffCheck SHALL NOT write, delete, or rename any manifest or evidence file
2. THE HandoffCheck SHALL only read files for validation

### Requirement 8: CLI Interface

**User Story:** As a command-line user, I want flexible options for directory and output format.

#### Acceptance Criteria

1. THE HandoffCheck SHALL accept a manifest path as positional argument
2. THE HandoffCheck SHALL accept --root to specify the evidence root directory (default: manifest file directory)
3. THE HandoffCheck SHALL accept --format with "text" (default) or "json"
4. IF --root is invalid (missing, not a directory, inaccessible), THEN THE HandoffCheck SHALL exit with code 2 BEFORE evidence checks

### Requirement 9: Error Handling and Diagnostics

**User Story:** As a developer debugging validation failures, I want clear error messages identifying the problem.

#### Acceptance Criteria

1. WHEN validation fails, THE HandoffCheck SHALL output human-readable diagnostics to stderr
2. FOR structured failures, JSON output SHALL include task_results with per-task reasons (pending, missing evidence, etc.)
3. THE HandoffCheck SHALL clearly indicate which evidence files failed and why

### Requirement 10: Python Standard Library Only

**User Story:** As a system administrator, I want minimal dependencies and easy deployment.

#### Acceptance Criteria

1. THE HandoffCheck SHALL use only Python standard library modules (json, pathlib, typing, argparse)
2. THE HandoffCheck SHALL NOT attempt to download or install packages at runtime
