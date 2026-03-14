"""Convert a playbook to AWS Step Functions ASL JSON."""

from __future__ import annotations

from typing import Any


def convert(playbook: dict[str, Any]) -> dict[str, Any]:
    """Convert a playbook dict to an AWS Step Functions ASL definition."""
    states: dict[str, Any] = {}
    state_order: list[str] = []

    # Triage steps → Pass states with instructions
    for i, step in enumerate(playbook.get("triage", []), 1):
        state_name = f"Triage_{i}"
        states[state_name] = {
            "Type": "Pass",
            "Comment": step["step"],
            "Result": {
                "step": step["step"],
                "instructions": step["how"],
            },
            "ResultPath": f"$.triage.step_{i}",
        }
        state_order.append(state_name)

    # Investigation queries → Task states calling Athena/CloudWatch Lambda
    investigation = playbook.get("investigation", {})
    for i, query in enumerate(investigation.get("queries", []), 1):
        state_name = f"Investigate_{i}"
        states[state_name] = {
            "Type": "Task",
            "Comment": query["name"],
            "Resource": "arn:aws:lambda:{region}:{account}:function:gdpc-query-executor",
            "Parameters": {
                "query_name": query["name"],
                "query_type": query["type"],
                "query_template": query["template"],
                "variables.$": "$.variables",
            },
            "ResultPath": f"$.investigation.query_{i}",
            "Retry": [
                {
                    "ErrorEquals": ["States.TaskFailed"],
                    "IntervalSeconds": 5,
                    "MaxAttempts": 2,
                    "BackoffRate": 2.0,
                }
            ],
        }
        state_order.append(state_name)

    # Containment actions → Task or Wait states
    containment = playbook.get("containment", {})
    automated = containment.get("automated", False)
    for action in containment.get("actions", []):
        state_name = f"Contain_{action['id']}"
        is_manual = not automated or action.get("requires_confirmation", False)

        if is_manual:
            # Manual → Wait with TaskToken callback pattern
            states[state_name] = {
                "Type": "Task",
                "Comment": f"[MANUAL] {action['description']}",
                "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
                "Parameters": {
                    "FunctionName": (
                        f"arn:aws:lambda:{{{{region}}}}:{{{{account}}}}"
                        f":function:gdpc-{action['id']}"
                    ),
                    "Payload": {
                        "action_id": action["id"],
                        "description": action["description"],
                        "aws_cli": action["aws_cli"],
                        "requires_confirmation": True,
                        "task_token.$": "$$.Task.Token",
                        "variables.$": "$.variables",
                    },
                },
                "ResultPath": f"$.containment.{action['id']}",
            }
        else:
            # Automated → direct Task invocation
            states[state_name] = {
                "Type": "Task",
                "Comment": f"[AUTO] {action['description']}",
                "Resource": (
                    f"arn:aws:lambda:{{{{region}}}}:{{{{account}}}}:function:gdpc-{action['id']}"
                ),
                "Parameters": {
                    "action_id": action["id"],
                    "aws_cli": action["aws_cli"],
                    "variables.$": "$.variables",
                },
                "ResultPath": f"$.containment.{action['id']}",
                "Retry": [
                    {
                        "ErrorEquals": ["States.TaskFailed"],
                        "IntervalSeconds": 5,
                        "MaxAttempts": 2,
                        "BackoffRate": 2.0,
                    }
                ],
            }
        state_order.append(state_name)

    # Escalation → notification Task state
    escalation = playbook.get("escalation", {})
    for i, notify in enumerate(escalation.get("notify", []), 1):
        state_name = f"Notify_{notify['channel']}_{i}"
        states[state_name] = {
            "Type": "Task",
            "Comment": f"Notify via {notify['channel']}",
            "Resource": (
                f"arn:aws:lambda:{{{{region}}}}:{{{{account}}}}"
                f":function:gdpc-notify-{notify['channel']}"
            ),
            "Parameters": {
                "channel": notify["channel"],
                "condition": notify["condition"],
                "message": notify["message"],
                "variables.$": "$.variables",
            },
            "ResultPath": f"$.escalation.notify_{i}",
        }
        state_order.append(state_name)

    # Link states with Next and set End on last
    for i, name in enumerate(state_order):
        if i < len(state_order) - 1:
            states[name]["Next"] = state_order[i + 1]
        else:
            states[name]["End"] = True

    # Build required Lambda functions list
    lambda_functions = [
        "gdpc-query-executor: Executes investigation queries (Athena/CloudWatch Logs)",
    ]
    for action in containment.get("actions", []):
        lambda_functions.append(f"gdpc-{action['id']}: {action['description']}")
    for notify in escalation.get("notify", []):
        lambda_functions.append(
            f"gdpc-notify-{notify['channel']}: Sends notifications via {notify['channel']}"
        )

    return {
        "_comment": (
            f"Step Functions state machine for GuardDuty playbook: {playbook['id']}. "
            f"Required Lambda functions: {'; '.join(lambda_functions)}"
        ),
        "Comment": playbook.get("description", ""),
        "StartAt": state_order[0] if state_order else "NoOp",
        "States": states,
    }
