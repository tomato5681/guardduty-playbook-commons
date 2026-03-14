"""Convert a playbook to Tines Story JSON."""

from __future__ import annotations

from typing import Any


def _make_action(
    action_id: int,
    name: str,
    action_type: str,
    description: str,
    *,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a Tines action definition."""
    action: dict[str, Any] = {
        "id": action_id,
        "name": name,
        "type": action_type,
        "description": description,
    }
    if options:
        action["options"] = options
    return action


def convert(playbook: dict[str, Any]) -> dict[str, Any]:
    """Convert a playbook dict to a Tines Story JSON structure."""
    actions: list[dict[str, Any]] = []
    links: list[dict[str, int]] = []
    action_id = 1

    # Triage steps → Send to Story (human review)
    for step in playbook.get("triage", []):
        actions.append(
            _make_action(
                action_id,
                f"Triage: {step['step']}",
                "Send to Story",
                step["how"],
                options={"message": step["how"]},
            )
        )
        if action_id > 1:
            links.append({"source": action_id - 1, "receiver": action_id})
        action_id += 1

    # Investigation queries → Event Transformation
    investigation = playbook.get("investigation", {})
    for query in investigation.get("queries", []):
        actions.append(
            _make_action(
                action_id,
                f"Investigate: {query['name']}",
                "Event Transformation",
                f"Query type: {query['type']}",
                options={"query_template": query["template"]},
            )
        )
        if action_id > 1:
            links.append({"source": action_id - 1, "receiver": action_id})
        action_id += 1

    # Containment actions
    containment = playbook.get("containment", {})
    automated = containment.get("automated", False)
    for action_def in containment.get("actions", []):
        is_manual = not automated or action_def.get("requires_confirmation", False)
        action_type = "Send to Story" if is_manual else "HTTP Request"

        options: dict[str, Any] = {"aws_cli": action_def["aws_cli"]}
        if not is_manual:
            options["method"] = "POST"
            options["url"] = "https://sts.amazonaws.com/"
            options["assumed_role"] = True

        actions.append(
            _make_action(
                action_id,
                f"Contain: {action_def['description']}",
                action_type,
                action_def["description"],
                options=options,
            )
        )
        if action_id > 1:
            links.append({"source": action_id - 1, "receiver": action_id})
        action_id += 1

    # Escalation → notification actions
    escalation = playbook.get("escalation", {})
    for notify in escalation.get("notify", []):
        options = {"message": notify["message"], "condition": notify["condition"]}
        if notify["channel"] == "slack":
            options["webhook_url"] = "<<SLACK_WEBHOOK_URL>>"
        actions.append(
            _make_action(
                action_id,
                f"Notify: {notify['channel']}",
                "HTTP Request",
                f"Send notification via {notify['channel']}",
                options=options,
            )
        )
        if action_id > 1:
            links.append({"source": action_id - 1, "receiver": action_id})
        action_id += 1

    # Map variables to event fields
    variable_mapping = {var["name"]: f"<<{var['name']}>>" for var in playbook.get("variables", [])}

    return {
        "name": f"GuardDuty: {playbook['id']}",
        "description": playbook.get("description", ""),
        "actions": actions,
        "links": links,
        "variables": variable_mapping,
    }
