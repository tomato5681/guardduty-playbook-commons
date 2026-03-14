"""Tests for Python runbook output."""

from pathlib import Path

import pytest
import yaml

from converter.targets.python_runbook import convert

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_playbook() -> dict:
    with open(FIXTURES / "sample_playbook.yaml") as f:
        return yaml.safe_load(f)


def test_output_is_valid_python(sample_playbook: dict) -> None:
    result = convert(sample_playbook)
    # Should compile without syntax errors
    compile(result, "<generated>", "exec")


def test_output_contains_argparse(sample_playbook: dict) -> None:
    result = convert(sample_playbook)
    assert "--finding-json" in result
    assert "--dry-run" in result
    assert "argparse" in result


def test_output_imports_boto3(sample_playbook: dict) -> None:
    result = convert(sample_playbook)
    assert "import boto3" in result


def test_output_contains_containment_function(sample_playbook: dict) -> None:
    result = convert(sample_playbook)
    assert "def test_action(" in result


def test_output_contains_triage_function(sample_playbook: dict) -> None:
    result = convert(sample_playbook)
    assert "def triage_step_1(" in result


def test_output_contains_main(sample_playbook: dict) -> None:
    result = convert(sample_playbook)
    assert "def main()" in result
    assert '__name__ == "__main__"' in result


def test_output_contains_variable_extraction(sample_playbook: dict) -> None:
    result = convert(sample_playbook)
    assert "def extract_variables(" in result
    assert "principal_id" in result
