# Contributing to guardduty-playbook-commons

## Adding a New Playbook

1. **Identify the GuardDuty finding type** from the [AWS docs](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_finding-types-active.html). Use the exact finding type string (e.g. `IAMUser/AnomalousBehavior`).

2. **Create the YAML file** in the appropriate `playbooks/<category>/` directory:
   ```
   playbooks/
   ├── iam/        # IAM-related findings
   ├── s3/         # S3-related findings
   ├── ec2/        # EC2-related findings
   ├── lambda/     # Lambda-related findings
   └── malware/    # Malware protection findings
   ```
   Name the file after the finding (e.g. `IAMUser-AnomalousBehavior.yaml`).

3. **Define the playbook** following the schema. At minimum you need:
   - `id`, `version`, `finding_type`, `severity`, `description`
   - At least one `triage` step
   - At least one entry in `variables`

4. **Write useful content** — use real AWS CLI commands, actual CloudTrail field names, and practical remediation steps. Avoid placeholder text.

5. **Validate** your playbook:
   ```bash
   gdpc validate playbooks/your-category/YourPlaybook.yaml
   ```

6. **Test** the converter outputs:
   ```bash
   gdpc convert playbooks/your-category/YourPlaybook.yaml --target python --output /tmp/test/
   gdpc convert playbooks/your-category/YourPlaybook.yaml --target tines --output /tmp/test/
   ```

## Schema Field Reference

See [docs/schema.md](docs/schema.md) for the complete field reference.

## Testing Locally

```bash
# Clone and install in development mode
git clone https://github.com/pfrederiksen/guardduty-playbook-commons.git
cd guardduty-playbook-commons
pip install -e ".[dev]"

# Validate all playbooks
gdpc validate playbooks/

# Run tests
pytest -v

# Check formatting
ruff check .
ruff format --check .
```

## PR Checklist

- [ ] Playbook YAML passes `gdpc validate`
- [ ] Finding type matches an actual GuardDuty finding type
- [ ] Triage steps include real CLI commands or console instructions
- [ ] Containment actions use valid AWS CLI syntax
- [ ] Variables use correct GuardDuty finding JSON paths
- [ ] No hardcoded AWS account IDs, regions, or credentials
- [ ] All three converter targets produce valid output
- [ ] Tests pass (`pytest -v`)
- [ ] Code passes linting (`ruff check .`)
