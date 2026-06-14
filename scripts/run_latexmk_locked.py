#!/usr/bin/env python3
"""Run latexmk under a repository-scoped lock.

The manuscript build writes shared side files in ``book/``. Serializing
latexmk calls prevents concurrent release checks from corrupting PDFs or logs.
"""

from __future__ import annotations

import fcntl
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_SOURCE_DATE_EPOCH = "1781395200"


def lock_path() -> Path:
    digest = hashlib.sha256(str(ROOT).encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"llm_book_latexmk_{digest}.lock"


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(
            "usage: run_latexmk_locked.py WORKDIR LATEXMK [LATEXMK_ARGS ...]",
            file=sys.stderr,
        )
        return 2

    workdir = Path(argv[1])
    command = argv[2:]
    env = os.environ.copy()
    env.setdefault("SOURCE_DATE_EPOCH", RELEASE_SOURCE_DATE_EPOCH)
    env.setdefault("FORCE_SOURCE_DATE", "1")
    env.setdefault("SOURCE_DATE_EPOCH_TEX_PRIMITIVES", "1")
    env.setdefault("TZ", "UTC")

    with lock_path().open("w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        return subprocess.run(command, cwd=workdir, env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
