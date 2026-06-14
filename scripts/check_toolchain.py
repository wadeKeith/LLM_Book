#!/usr/bin/env python3
"""Verify that the local publication toolchain is available."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


MIN_PYTHON = (3, 10)


@dataclass(frozen=True)
class ToolSpec:
    label: str
    env_name: str
    default: str
    version_args: tuple[str, ...]


TOOLS = (
    ToolSpec("latexmk", "LATEXMK", "latexmk", ("--version",)),
    ToolSpec("rg", "RG", "rg", ("--version",)),
    ToolSpec("pdfinfo", "PDFINFO", "pdfinfo", ("-v",)),
    ToolSpec("pdffonts", "PDFFONTS", "pdffonts", ("-v",)),
    ToolSpec("pdftotext", "PDFTOTEXT", "pdftotext", ("-v",)),
    ToolSpec("pdftoppm", "PDFTOPPM", "pdftoppm", ("-v",)),
    ToolSpec("chktex", "CHKTEX", "chktex", ("--version",)),
)


def first_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return "<no version output>"


def resolve_command(spec: ToolSpec) -> tuple[list[str] | None, str | None]:
    raw_value = os.environ.get(spec.env_name, spec.default)
    try:
        tokens = shlex.split(raw_value)
    except ValueError as exc:
        return None, f"{spec.env_name}={raw_value!r} is not shell-parseable: {exc}"

    if not tokens:
        return None, f"{spec.env_name} is empty"

    executable = tokens[0]
    if os.path.sep in executable:
        path = Path(executable)
        if not path.is_file():
            return None, f"{spec.label}: executable {executable!r} does not exist"
        resolved = str(path)
    else:
        found = shutil.which(executable)
        if found is None:
            return None, f"{spec.label}: executable {executable!r} was not found on PATH"
        resolved = found

    return [resolved, *tokens[1:]], None


def probe_version(spec: ToolSpec) -> tuple[str | None, str | None]:
    command, error = resolve_command(spec)
    if error:
        return None, error
    assert command is not None

    result = subprocess.run(
        [*command, *spec.version_args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    if result.returncode != 0:
        detail = first_line(output)
        return None, f"{spec.label}: version probe failed with exit {result.returncode}: {detail}"
    return first_line(output), None


def check_python(errors: list[str]) -> None:
    version = sys.version_info
    print(f"Python runtime: {version.major}.{version.minor}.{version.micro}")
    if version < MIN_PYTHON:
        required = ".".join(str(part) for part in MIN_PYTHON)
        errors.append(f"Python runtime must be {required}+")


def main() -> int:
    errors: list[str] = []
    check_python(errors)

    for spec in TOOLS:
        summary, error = probe_version(spec)
        if error:
            errors.append(error)
            continue
        print(f"{spec.label}: {summary}")

    print("toolchain checks passed" if not errors else "toolchain check failures")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
