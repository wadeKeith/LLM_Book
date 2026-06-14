#!/usr/bin/env python3
"""Publish the prepared GitHub release only after Zenodo integration is verified."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = "wadeKeith/LLM_Book"
TAG = "v2026.06.14"
EXPECTED_ASSETS = {
    "book.pdf": "sha256:4e0204492b461f06b9c0c6bf72e0b125ac836a9acfc522fbf730399f1b71c92a",
    "book_zh.pdf": "sha256:68909d699cb9ab1a31f1c5eed796294e7d0da474e26f2f563bd0752b7d0b4fff",
}


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def run(command: list[str]) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return CommandResult(completed.returncode, completed.stdout.strip(), completed.stderr.strip())


def load_json(command: list[str]) -> object:
    completed = run(command)
    if completed.returncode != 0:
        detail = completed.stderr or completed.stdout or "command failed"
        raise RuntimeError(f"{' '.join(command)}: {detail}")
    return json.loads(completed.stdout)


def zenodo_hook_visible() -> tuple[bool, str]:
    hooks = load_json(["gh", "api", f"repos/{REPO}/hooks"])
    if not isinstance(hooks, list):
        raise RuntimeError("GitHub hooks API returned an unexpected payload")

    visible = []
    for hook in hooks:
        if not isinstance(hook, dict):
            continue
        config = hook.get("config") or {}
        haystack = " ".join(
            str(part)
            for part in (
                hook.get("name", ""),
                config.get("url", ""),
                config.get("content_type", ""),
            )
        ).lower()
        if "zenodo" in haystack:
            visible.append(str(hook.get("id", "unknown")))

    if visible:
        return True, "Zenodo hook visible: " + ", ".join(visible)
    return False, f"No Zenodo hook visible through GitHub hooks API; hooks visible={len(hooks)}"


def release_payload() -> dict[str, object]:
    payload = load_json(
        [
            "gh",
            "release",
            "view",
            TAG,
            "--repo",
            REPO,
            "--json",
            "tagName,isDraft,isPrerelease,url,assets",
        ]
    )
    if not isinstance(payload, dict):
        raise RuntimeError("GitHub release API returned an unexpected payload")
    return payload


def check_release(payload: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if payload.get("tagName") != TAG:
        errors.append(f"release tag is {payload.get('tagName')!r}, expected {TAG!r}")
    if payload.get("isDraft") is not True:
        errors.append("release is not a draft")
    if payload.get("isPrerelease") is True:
        errors.append("release is marked as prerelease")

    assets = payload.get("assets")
    if not isinstance(assets, list):
        errors.append("release assets are missing")
        return errors

    digests_by_name = {}
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = asset.get("name")
        if isinstance(name, str):
            digests_by_name[name] = asset.get("digest")

    for asset_name, expected_digest in EXPECTED_ASSETS.items():
        actual_digest = digests_by_name.get(asset_name)
        if actual_digest != expected_digest:
            errors.append(
                f"{asset_name} digest is {actual_digest!r}, expected {expected_digest!r}"
            )

    return errors


def publish_release() -> None:
    completed = run(["gh", "release", "edit", TAG, "--repo", REPO, "--draft=false", "--latest"])
    if completed.returncode != 0:
        detail = completed.stderr or completed.stdout or "release publish failed"
        raise RuntimeError(detail)
    print(completed.stdout or f"published {TAG}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--publish",
        action="store_true",
        help="publish the draft release after all preconditions pass",
    )
    parser.add_argument(
        "--zenodo-dashboard-verified",
        action="store_true",
        help="allow publishing when the Zenodo dashboard shows the repository is enabled but no hook is visible",
    )
    args = parser.parse_args(argv)

    try:
        hook_ok, hook_detail = zenodo_hook_visible()
        if hook_ok:
            print(f"READY: {hook_detail}")
        elif args.zenodo_dashboard_verified:
            print(f"READY: Zenodo dashboard verification override used. {hook_detail}")
        else:
            print(f"PENDING: {hook_detail}")
            print("Refusing to publish until Zenodo integration is verified.")
            return 1

        payload = release_payload()
        release_errors = check_release(payload)
        if release_errors:
            print("\n".join(f"MISSING: {error}" for error in release_errors))
            return 1

        print(
            "READY: draft release "
            f"{payload.get('tagName')} with expected PDF assets at {payload.get('url')}"
        )

        if not args.publish:
            print("Dry run only. Re-run with --publish to publish the release.")
            return 0

        publish_release()
        return 0
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
