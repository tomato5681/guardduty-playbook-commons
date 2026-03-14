# Playbook Schema Reference

GuardDuty playbooks are defined in YAML and validated against `schema/playbook.schema.json` (JSON Schema draft-07).

## Metadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique playbook identifier (e.g. `IAMUser-AnomalousBehavior`) |
| `version` | string | Yes | Semantic version (`X.Y.Z`) |
| `finding_type` | string | Yes | Exact GuardDuty finding type (e.g. `IAMUser/AnomalousBehavior`) |
| `severity` | array | Yes | Severity levels that trigger this playbook: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `description` | string | Yes | Human-readable description |
| `references` | array of URIs | No | Links to relevant documentation |

## Triage

The `triage` section is a required array of steps for initial assessment.

```yaml
triage:
  - step: "What to check"
    how: "How to check it (CLI command, console link, etc.)"
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `step` | string | Yes | What to do |
| `how` | string | Yes | How to do it |

## Investigation

Optional investigation queries for deeper analysis.

```yaml
investigation:
  queries:
    - name: "Query description"
      type: athena
      template: |
        SELECT ... WHERE user = '{principal_id}'
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Query name |
| `type` | enum | Yes | `cloudtrail_insights`, `cloudwatch_logs`, or `athena` |
| `template` | string | Yes | Query template with `{variable}` placeholders |

## Containment

Actions to limit blast radius.

```yaml
containment:
  automated: false
  actions:
    - id: disable_user
      description: "Disable the IAM user"
      aws_cli: "aws iam ..."
      requires_confirmation: true
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `automated` | boolean | No | `true` = auto-execute; `false` = confirm first |
| `actions[].id` | string | Yes | Unique action identifier |
| `actions[].description` | string | Yes | What the action does |
| `actions[].aws_cli` | string | Yes | AWS CLI command |
| `actions[].requires_confirmation` | boolean | No | Override for individual action confirmation |

## Escalation

Notification and paging rules.

```yaml
escalation:
  notify:
    - channel: slack
      condition: "severity == CRITICAL"
      message: "Alert: {finding_type} on {principal_id}"
  page:
    condition: "severity == CRITICAL and automated == false"
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `notify[].channel` | string | Yes | Notification channel (e.g. `slack`, `email`, `pagerduty`) |
| `notify[].condition` | string | Yes | Condition expression |
| `notify[].message` | string | Yes | Message template |
| `page.condition` | string | No | Condition to trigger on-call paging |

## Variables

Required array of variables extracted from the GuardDuty finding JSON.

```yaml
variables:
  - name: principal_id
    source: finding.resource.accessKeyDetails.userName
  - name: account_id
    source: finding.accountId
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Variable name used in `{variable}` placeholders |
| `source` | string | Yes | Dot-notation path in the GuardDuty finding JSON |
