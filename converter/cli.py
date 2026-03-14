"""CLI for guardduty-playbook-commons: validate and convert playbooks."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import click
import yaml

from converter.loader import load_playbook, validate_playbook
from converter.targets import python_runbook, stepfunctions, tines

_SAFE_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")

TARGETS: dict[str, Any] = {
    "tines": (tines, ".json"),
    "python": (python_runbook, ".py"),
    "stepfunctions": (stepfunctions, ".json"),
}


def _collect_yaml_files(path: Path) -> list[Path]:
    """Collect YAML files from a path (file or directory)."""
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(path.rglob("*.yaml"))
    raise click.BadParameter(f"Path does not exist: {path}")


@click.group()
def cli() -> None:
    """gdpc — GuardDuty Playbook Commons converter CLI."""


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--target",
    "-t",
    required=True,
    type=click.Choice(["tines", "python", "stepfunctions"]),
    help="Output target format",
)
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(path_type=Path),
    help="Output directory",
)
def convert(path: Path, target: str, output: Path) -> None:
    """Convert playbook YAML(s) to a target format."""
    output.mkdir(parents=True, exist_ok=True)
    yaml_files = _collect_yaml_files(path)

    if not yaml_files:
        click.echo(click.style("No YAML files found.", fg="yellow"))
        return

    module, ext = TARGETS[target]
    success_count = 0
    error_count = 0

    for yaml_file in yaml_files:
        try:
            playbook = load_playbook(yaml_file)
            result = module.convert(playbook)

            playbook_id = playbook["id"]
            if not _SAFE_ID_RE.match(playbook_id):
                raise ValueError(f"Playbook ID '{playbook_id}' contains unsafe characters")
            out_file = output / f"{playbook_id}{ext}"
            if not out_file.resolve().is_relative_to(output.resolve()):
                raise ValueError(
                    f"Playbook ID '{playbook_id}' would write outside output directory"
                )
            if isinstance(result, str):
                out_file.write_text(result)
            else:
                out_file.write_text(json.dumps(result, indent=2) + "\n")

            click.echo(click.style("  OK ", fg="green") + f"{yaml_file.name} → {out_file}")
            success_count += 1
        except Exception as e:
            click.echo(click.style("  FAIL ", fg="red") + f"{yaml_file.name}: {e}")
            error_count += 1

    click.echo(f"\n{success_count} converted, {error_count} failed (target: {target})")
    if error_count:
        raise SystemExit(1)


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def validate(path: Path) -> None:
    """Validate playbook YAML(s) against the schema."""
    yaml_files = _collect_yaml_files(path)

    if not yaml_files:
        click.echo(click.style("No YAML files found.", fg="yellow"))
        return

    valid_count = 0
    error_count = 0

    for yaml_file in yaml_files:
        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)

            errors = validate_playbook(data)
            if errors:
                click.echo(click.style("  FAIL ", fg="red") + str(yaml_file))
                for err in errors:
                    click.echo(f"       - {err}")
                error_count += 1
            else:
                click.echo(click.style("  OK ", fg="green") + str(yaml_file))
                valid_count += 1
        except Exception as e:
            click.echo(click.style("  FAIL ", fg="red") + f"{yaml_file}: {e}")
            error_count += 1

    click.echo(f"\n{valid_count} valid, {error_count} invalid")
    if error_count:
        raise SystemExit(1)
