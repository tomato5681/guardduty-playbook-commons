"""Load and validate GuardDuty playbook YAML files against the JSON Schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "playbook.schema.json"


def _load_schema() -> dict[str, Any]:
    """Load the playbook JSON Schema from disk."""
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def validate_playbook(data: dict[str, Any]) -> list[str]:
    """Validate a playbook dict against the schema.

    Returns a list of validation error messages (empty if valid).
    """
    schema = _load_schema()
    validator = jsonschema.Draft7Validator(schema)
    return [e.message for e in sorted(validator.iter_errors(data), key=lambda e: list(e.path))]


def load_playbook(path: Path) -> dict[str, Any]:
    """Load a single playbook YAML file and validate it.

    Raises ValueError if the playbook fails schema validation.
    """
    with open(path) as f:
        data = yaml.safe_load(f)

    errors = validate_playbook(data)
    if errors:
        error_list = "\n  - ".join(errors)
        raise ValueError(f"Playbook {path} failed validation:\n  - {error_list}")

    return data


def load_all_playbooks(directory: Path) -> list[dict[str, Any]]:
    """Recursively load all .yaml playbook files from a directory.

    Raises ValueError if any playbook fails validation.
    """
    playbooks = []
    for yaml_file in sorted(directory.rglob("*.yaml")):
        playbooks.append(load_playbook(yaml_file))
    return playbooks
