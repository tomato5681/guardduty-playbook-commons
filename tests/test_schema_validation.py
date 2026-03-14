"""Tests for playbook schema validation."""

from pathlib import Path

import pytest
import yaml

from converter.loader import validate_playbook

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_playbook() -> dict:
    with open(FIXTURES / "sample_playbook.yaml") as f:
        return yaml.safe_load(f)


def test_valid_playbook_passes(sample_playbook: dict) -> None:
    errors = validate_playbook(sample_playbook)
    assert errors == []


def test_missing_id_fails(sample_playbook: dict) -> None:
    del sample_playbook["id"]
    errors = validate_playbook(sample_playbook)
    assert any("id" in e for e in errors)


def test_missing_version_fails(sample_playbook: dict) -> None:
    del sample_playbook["version"]
    errors = validate_playbook(sample_playbook)
    assert any("version" in e for e in errors)


def test_missing_finding_type_fails(sample_playbook: dict) -> None:
    del sample_playbook["finding_type"]
    errors = validate_playbook(sample_playbook)
    assert any("finding_type" in e for e in errors)


def test_invalid_severity_fails(sample_playbook: dict) -> None:
    sample_playbook["severity"] = ["INVALID"]
    errors = validate_playbook(sample_playbook)
    assert len(errors) > 0


def test_empty_triage_fails(sample_playbook: dict) -> None:
    sample_playbook["triage"] = []
    errors = validate_playbook(sample_playbook)
    assert len(errors) > 0


def test_missing_triage_fails(sample_playbook: dict) -> None:
    del sample_playbook["triage"]
    errors = validate_playbook(sample_playbook)
    assert any("triage" in e for e in errors)


def test_invalid_version_format_fails(sample_playbook: dict) -> None:
    sample_playbook["version"] = "not-semver"
    errors = validate_playbook(sample_playbook)
    assert len(errors) > 0


def test_missing_variables_fails(sample_playbook: dict) -> None:
    del sample_playbook["variables"]
    errors = validate_playbook(sample_playbook)
    assert any("variables" in e for e in errors)
