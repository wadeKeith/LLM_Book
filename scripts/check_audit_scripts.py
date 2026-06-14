#!/usr/bin/env python3
"""Check release audit Python scripts for compile and Makefile coverage."""

from __future__ import annotations

import ast
import py_compile
import re
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
MAKEFILE = ROOT / "Makefile"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def script_paths() -> list[Path]:
    return sorted(path for path in SCRIPTS_DIR.glob("*.py") if path.is_file())


def check_script_header(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "#!/usr/bin/env python3":
        errors.append(f"{rel(path)}: missing python3 shebang")

    try:
        module = ast.parse(text, filename=rel(path))
    except SyntaxError as exc:
        errors.append(f"{rel(path)}: syntax parse failed: {exc}")
        return

    if not ast.get_docstring(module):
        errors.append(f"{rel(path)}: missing module docstring")

    future_import = "from __future__ import annotations"
    if future_import not in text:
        errors.append(f"{rel(path)}: missing {future_import!r}")


def check_compiles(path: Path, errors: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="llm-book-pycompile-") as cache_dir:
        target = Path(cache_dir) / (path.stem + ".pyc")
        try:
            py_compile.compile(str(path), cfile=str(target), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"{rel(path)}: py_compile failed: {exc.msg}")


def check_makefile_coverage(paths: list[Path], errors: list[str]) -> int:
    text = MAKEFILE.read_text(encoding="utf-8")
    referenced = 0
    for path in paths:
        if not path.name.startswith("check_"):
            continue
        if rel(path) not in text:
            errors.append(f"{rel(path)}: not referenced by Makefile")
            continue
        referenced += 1

    audit_targets = re.search(r"^manuscript-audit:\s*(.+)$", text, re.MULTILINE)
    if not audit_targets:
        errors.append("Makefile: missing manuscript-audit target")
    elif "audit-script-check" not in audit_targets.group(1).split():
        errors.append("Makefile: manuscript-audit does not include audit-script-check")

    if not re.search(r"^audit-script-check:\s*$", text, re.MULTILINE):
        errors.append("Makefile: missing audit-script-check target")

    return referenced


def main() -> int:
    errors: list[str] = []
    paths = script_paths()

    for path in paths:
        check_script_header(path, errors)
        check_compiles(path, errors)

    referenced_check_scripts = check_makefile_coverage(paths, errors)

    print(f"audit Python scripts checked: {len(paths)}")
    print(f"audit check scripts referenced by Makefile: {referenced_check_scripts}")
    print(f"audit script compile/header errors: {len(errors)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("audit script checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
