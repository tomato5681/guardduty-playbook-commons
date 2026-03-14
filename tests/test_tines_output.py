"""Tests for Tines Story JSON output."""

from pathlib import Path

import pytest
import yaml

from converter.targets.tines import convert

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_playbook() -> dict:
    with open(FIXTURES / "sample_playbook.yaml") as f:
        return yaml.safe_load(f)


def test_output_is_valid_structure(sample_playbook: dict) -> None:
    result = convert(sample_playbook)
    assert "name" in result
    assert "actions" in result
    assert "links" in result
    assert isinstance(result["actions"], list)
    assert isinstance(result["links"], list)


def test_story_name_includes_playbook_id(sample_playbook: dict) -> None:
    result = convert(sample_playbook)
    assert "Test-Playbook" in result["name"]


def test_action_count_matches_steps(sample_playbook: dict) -> None:
    result = convert(sample_playbook)
    # 1 triage + 1 investigation + 1 containment + 1 escalation = 4
    expected = (
        len(sample_playbook["triage"])
        + len(sample_playbook["investigation"]["queries"])
        + len(sample_playbook["containment"]["actions"])
        + len(sample_playbook["escalation"]["notify"])
    )
    assert len(result["actions"]) == expected


def test_manual_steps_are_send_to_story(sample_playbook: dict) -> None:
    result = convert(sample_playbook)
    # Triage steps should be "Send to Story"
    triage_actions = [a for a in result["actions"] if a["name"].startswith("Triage:")]
    for action in triage_actions:
        assert action["type"] == "Send to Story"


def test_manual_containment_is_send_to_story(sample_playbook: dict) -> None:
    result = convert(sample_playbook)
    containment_actions = [a for a in result["actions"] if a["name"].startswith("Contain:")]
    # automated=false + requires_confirmation=true → Send to Story
    for action in containment_actions:
        assert action["type"] == "Send to Story"


def test_variables_are_mapped(sample_playbook: dict) -> None:
    result = convert(sample_playbook)
    assert "variables" in result
    assert "principal_id" in result["variables"]
    assert "account_id" in result["variables"]
