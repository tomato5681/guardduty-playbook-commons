[![CI](https://github.com/pfrederiksen/guardduty-playbook-commons/actions/workflows/ci.yml/badge.svg)](https://github.com/pfrederiksen/guardduty-playbook-commons/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/guardduty-playbook-commons)](https://pypi.org/project/guardduty-playbook-commons/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

# guardduty-playbook-commons

Security teams rebuild the same GuardDuty response logic repeatedly — one team writes Tines workflows, another builds Step Functions, a third maintains Python scripts — all encoding identical remediation knowledge in proprietary formats. **guardduty-playbook-commons** defines playbook logic once in a vendor-neutral YAML schema and compiles it to multiple automation targets. Think "Sigma Rules but for incident response."

## Installation

```bash
# Install from PyPI
pip install guardduty-playbook-commons

# Or install from source (for development or to get the playbook YAML files)
git clone https://github.com/pfrederiksen/guardduty-playbook-commons.git
cd guardduty-playbook-commons
pip install -e ".[dev]"
```

To run the generated Python runbooks, also install boto3:

```bash
pip install guardduty-playbook-commons[runbook]
```

## Quick Start

```bash
# Convert a single playbook to a Python runbook
gdpc convert playbooks/iam/IAMUser-AnomalousBehavior.yaml --target python --output out/

# Convert all playbooks to Tines Stories
gdpc convert playbooks/ --target tines --output out/

# Convert all playbooks to Step Functions ASL
gdpc convert playbooks/ --target stepfunctions --output out/

# Validate all playbooks against the schema
gdpc validate playbooks/
```

## Use Cases

### SOC / Incident Response Teams
Define your GuardDuty response runbooks in a shared, version-controlled format. New analysts can follow consistent triage → investigation → containment steps instead of tribal knowledge. Convert to Python runbooks for ad-hoc incident handling with `--dry-run` for training.

### SOAR Platform Engineers
Convert community playbooks directly into your automation platform. Tines teams get importable Story JSON; Step Functions teams get ASL definitions with Lambda placeholders they can deploy alongside their existing infrastructure.

### Security Consultancies
Deliver standardized incident response playbooks to clients in whatever automation format they use. Maintain one source of truth and compile per engagement.

### Red Team / Purple Team Exercises
Use the playbooks as a baseline for testing detection-response coverage. Run `gdpc convert --target python` to get executable runbooks that validate whether containment actions actually fire during simulated attacks.

### Community Knowledge Sharing
Contribute playbooks with real-world investigation queries and containment steps. Unlike blog posts, these playbooks are machine-readable and immediately usable.

## Schema Overview

Each playbook is a YAML file defining triage, investigation, containment, and escalation steps for a specific GuardDuty finding type:

```yaml
id: IAMUser-AnomalousBehavior
version: "1.0.0"
finding_type: "IAMUser/AnomalousBehavior"
severity: [MEDIUM, HIGH, CRITICAL]
description: "Respond to anomalous IAM user behavior"

triage:
  - step: "Check if the IAM user is human or service account"
    how: "aws iam get-user --user-name {principal_id}"

investigation:
  queries:
    - name: "Recent API calls by this principal"
      type: athena
      template: |
        SELECT eventTime, eventName, sourceIPAddress, errorCode
        FROM cloudtrail_logs
        WHERE userIdentity.userName = '{principal_id}'
        AND eventTime > DATE_ADD('hour', -24, NOW())

containment:
  automated: false
  actions:
    - id: deny_all_access
      description: "Attach DenyAll inline policy"
      aws_cli: "aws iam put-user-policy --user-name {principal_id} ..."
      requires_confirmation: true

escalation:
  notify:
    - channel: slack
      condition: "severity == CRITICAL"
      message: "GuardDuty CRITICAL: {finding_type} on {principal_id}"

variables:
  - name: principal_id
    source: finding.resource.accessKeyDetails.userName
  - name: account_id
    source: finding.accountId
```

See [docs/schema.md](docs/schema.md) for the full schema reference.

## Supported Output Targets

| Target | Flag | Output | Description |
|--------|------|--------|-------------|
| Tines | `--target tines` | JSON | Tines Story with actions per step |
| Python Runbook | `--target python` | .py | Standalone boto3 script with `--dry-run` support |
| Step Functions | `--target stepfunctions` | JSON | AWS Step Functions ASL with Lambda placeholders |

## Output Examples

### Python Runbook

```bash
gdpc convert playbooks/iam/IAMUser-AnomalousBehavior.yaml --target python --output out/
```

Generates a self-contained script with argparse, variable extraction from a real GuardDuty finding JSON, and interactive containment steps:

```python
def extract_variables(finding: dict) -> dict:
    """Extract playbook variables from a GuardDuty finding."""
    principal_id = finding.get("resource", {}).get("accessKeyDetails", {}).get("userName", "UNKNOWN")
    account_id = finding.get("accountId", "UNKNOWN")
    region = finding.get("region", "UNKNOWN")
    return {"principal_id": principal_id, "account_id": account_id, "region": region}

def attach_deny_all_policy(variables: dict, dry_run: bool = False) -> None:
    """Attach an inline DenyAll policy to the IAM user to block all API access"""
    print(f"\n[CONTAINMENT] Attach DenyAll policy")
    cmd = f"""aws iam put-user-policy --user-name {variables['principal_id']} ..."""
    if dry_run:
        print(f"  [DRY RUN] Skipping execution.")
        return
    confirm = input("  Execute this action? (yes/no): ")
    ...
```

Run it against a real finding:
```bash
python out/iam-user-anomalous-behavior.py --finding-json finding.json --dry-run
```

### Tines Story JSON

```bash
gdpc convert playbooks/iam/IAMUser-AnomalousBehavior.yaml --target tines --output out/
```

Generates an importable Tines Story with linked actions:

```json
{
  "name": "GuardDuty: iam-user-anomalous-behavior",
  "actions": [
    {
      "id": 1,
      "name": "Triage: Determine if the principal is a human user or a service account",
      "type": "Send to Story",
      "description": "Check the userName and userType in the finding's accessKeyDetails..."
    },
    {
      "id": 4,
      "name": "Investigate: Recent API calls by the principal (last 24h)",
      "type": "Event Transformation",
      "options": { "query_template": "SELECT eventTime, eventSource, eventName ..." }
    },
    {
      "id": 6,
      "name": "Contain: Attach an inline DenyAll policy",
      "type": "Send to Story"
    }
  ],
  "links": [
    { "source": 1, "receiver": 2 },
    { "source": 2, "receiver": 3 }
  ]
}
```

### Step Functions ASL

```bash
gdpc convert playbooks/iam/IAMUser-AnomalousBehavior.yaml --target stepfunctions --output out/
```

Generates ASL with Lambda ARN placeholders and a `_comment` listing required Lambda deployments:

```json
{
  "_comment": "Required Lambda functions: gdpc-query-executor; gdpc-attach-deny-all-policy; gdpc-notify-slack",
  "StartAt": "Triage_1",
  "States": {
    "Triage_1": {
      "Type": "Pass",
      "Comment": "Determine if the principal is a human user or a service account",
      "Result": { "step": "...", "instructions": "..." },
      "Next": "Triage_2"
    },
    "Contain_attach-deny-all-policy": {
      "Type": "Task",
      "Comment": "[MANUAL] Attach DenyAll policy",
      "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
      "Parameters": { "task_token.$": "$$.Task.Token", "variables.$": "$.variables" }
    }
  }
}
```

## Playbook Coverage

| Finding Type | Severity | Automated |
|-------------|----------|-----------|
| IAMUser/AnomalousBehavior | MEDIUM, HIGH, CRITICAL | No |
| IAMUser/InstanceCredentialExfiltration.OutsideAWS | HIGH, CRITICAL | No |
| Policy/S3BucketPublicAccessGranted | HIGH, CRITICAL | No |
| UnauthorizedAccess/S3MaliciousIPCaller.Custom | MEDIUM, HIGH, CRITICAL | No |
| CryptoCurrency/EC2BitcoinTool.B!DNS | HIGH | No |
| UnauthorizedAccess/EC2TorClient | HIGH | No |
| Backdoor/Lambda.NetworkPortProbing | MEDIUM, HIGH | No |
| Execution/Malware.EC2MaliciousFile | HIGH, CRITICAL | No |

## Contributing

We welcome contributions! The most impactful ways to help:

### Add New Playbooks
GuardDuty has [100+ finding types](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_finding-types-active.html) — we've covered 8. High-value additions include:
- **RDS findings**: `CredentialAccess/RDS.AnomalousBehavior.SuccessfulLogin`
- **EKS findings**: `PrivilegeEscalation/Kubernetes.PrivilegedContainer`
- **Runtime Monitoring**: `Execution/Runtime.ReverseShell`
- **DNS findings**: `Trojan/EC2.DNSDataExfiltration`

### Add New Output Targets
The converter is modular — each target is a single Python module with a `convert(playbook: dict)` function. Good candidates:
- **XSOAR (Cortex)** playbook YAML
- **Splunk SOAR** (Phantom) app JSON
- **Terraform** for deploying Step Functions + Lambda stubs
- **Markdown runbook** for wiki/Confluence publishing

### Improve Existing Playbooks
- Add more specific investigation queries (VPC Flow Logs, DNS logs, S3 access logs)
- Include Athena table creation DDL for common log sources
- Add conditional logic for multi-account/org environments

See [CONTRIBUTING.md](CONTRIBUTING.md) for the step-by-step guide, schema reference, and PR checklist.

## License

Apache 2.0 — see [LICENSE](LICENSE).
