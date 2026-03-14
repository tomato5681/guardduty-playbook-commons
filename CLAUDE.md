# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

guardduty-playbook-commons defines AWS GuardDuty finding remediation playbooks in a vendor-neutral YAML schema and compiles them to multiple automation targets (Tines Stories, Python runbooks, AWS Step Functions). The converter is a Python CLI tool (`gdpc`).

## Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Validate all playbooks against JSON Schema
gdpc validate playbooks/

# Convert playbooks
gdpc convert playbooks/ --target tines --output out/
gdpc convert playbooks/ --target python --output out/
gdpc convert playbooks/ --target stepfunctions --output out/

# Run tests
pytest -v
pytest tests/test_schema_validation.py::test_valid_playbook_passes  # single test

# Lint and format
ruff check .
ruff format --check .
ruff format .  # auto-fix
```

## Architecture

- **`schema/playbook.schema.json`** — JSON Schema (draft-07) that defines the playbook YAML structure. All playbooks are validated against this.
- **`playbooks/<category>/*.yaml`** — Seed playbooks organized by AWS service (iam, s3, ec2, lambda, malware). Each defines triage, investigation, containment, and escalation steps for a specific GuardDuty finding type.
- **`converter/loader.py`** — Loads YAML playbooks and validates them against the schema using `jsonschema`. Entry points: `load_playbook()`, `validate_playbook()`, `load_all_playbooks()`.
- **`converter/targets/`** — Each module has a `convert(playbook: dict)` function:
  - `tines.py` → Tines Story JSON (actions linked sequentially, manual steps as "Send to Story")
  - `python_runbook.py` → Self-contained Python script string with argparse (`--finding-json`, `--dry-run`)
  - `stepfunctions.py` → AWS Step Functions ASL JSON with Lambda ARN placeholders
- **`converter/cli.py`** — Click CLI exposing `gdpc validate` and `gdpc convert` commands. Both accept a file or directory path.

## Key Conventions

- Playbook variables use `{variable_name}` placeholders, sourced from GuardDuty finding JSON via dot-notation paths (e.g. `finding.resource.accessKeyDetails.userName`)
- No hardcoded AWS account IDs, regions, or credentials anywhere
- The converter itself never requires AWS credentials — only generated Python runbooks need them at execution time
- All converter modules must have type hints
- Tests use pytest (no unittest); test fixtures live in `tests/fixtures/`
- Python 3.11+ required; dependencies managed via pyproject.toml only (no setup.py/requirements.txt)
