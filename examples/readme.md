# HandoffCheck Examples

This directory contains example manifests for testing HandoffCheck.

## ready/

A manifest where all tasks are ready for review.

Contains a single "done" task with valid evidence.

## missing/

A manifest with missing evidence files.

Contains a "done" task referencing a non-existent evidence file.

## invalid/

A manifest with invalid schema.

Contains an empty tasks array, which is invalid.

## Usage

python handoffcheck.py examples/ready/manifest.json
python handoffcheck.py examples/missing/manifest.json
python handoffcheck.py examples/invalid/manifest.json
