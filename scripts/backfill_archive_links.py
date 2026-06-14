#!/usr/bin/env python3
"""Backfill minted Zenodo DOI and OSF links into publication files."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOI_RE = re.compile(r"^10\.5281/zenodo\.\d+$")
OSF_RE = re.compile(r"^https://osf\.io/[A-Za-z0-9_-]+/?$")


@dataclass(frozen=True)
class Replacement:
    path: Path
    before: str
    after: str


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def replace_or_append_doi_cff(text: str, doi: str) -> str:
    doi_line = f'doi: "{doi}"'
    if re.search(r'(?m)^doi:\s*".*"$', text):
        return re.sub(r'(?m)^doi:\s*".*"$', doi_line, text)
    return text.replace('date-released: "2026-06-14"\n', f'date-released: "2026-06-14"\n{doi_line}\n')


def replace_index(text: str, doi: str, osf_url: str | None) -> str:
    doi_url = f"https://doi.org/{doi}"
    normalized_osf = f"{osf_url.rstrip('/')}/" if osf_url else None
    text = re.sub(
        r"(?s)  url = \{http://yincheng429\.cn/LLM_Book/\}\n(?:  doi = \{[^}]+\}\n)?\}",
        f"  url = {{http://yincheng429.cn/LLM_Book/}}\n  doi = {{{doi}}}\n}}",
        text,
    )

    if osf_url:
        note = (
            "The archived release is available through "
            f'<a href="{doi_url}">Zenodo DOI {doi}</a> and the '
            f'<a href="{normalized_osf}">OSF mirror</a>.'
        )
    else:
        note = (
            "The archived release is available through "
            f'<a href="{doi_url}">Zenodo DOI {doi}</a>.'
        )

    text = re.sub(
        r"(?s)<p>\n\s*The Zenodo DOI and OSF mirror links should be added here after the\n\s*GitHub release archive has been published and registered\.\n\s*</p>",
        f"<p>\n            {note}\n          </p>",
        text,
    )
    text = re.sub(
        r"(?s)<p>\n\s*The archived release is available through .*?\n\s*</p>",
        f"<p>\n            {note}\n          </p>",
        text,
    )

    if "Zenodo DOI" not in text:
        raise ValueError("index.html DOI note was not updated")
    if normalized_osf:
        osf_button = f'          <a class="button secondary" href="{normalized_osf}">OSF mirror</a>\n'
        if osf_button not in text:
            text = re.sub(
                r'(          <a class="button secondary" href="https://doi\.org/[^"]+">Zenodo DOI</a>\n)',
                r"\1" + osf_button,
                text,
                count=1,
            )
        if normalized_osf not in text:
            raise ValueError("index.html OSF link was not updated")
    return text


def replace_release_notes(text: str, doi: str, osf_url: str | None) -> str:
    normalized_osf = f"{osf_url.rstrip('/')}/" if osf_url else None
    doi_line = f"- Zenodo DOI: `https://doi.org/{doi}`"
    osf_line = f"- OSF mirror: `{normalized_osf}`" if normalized_osf else "- OSF mirror: pending"
    archive_block = f"## Archive Links\n\n{doi_line}\n{osf_line}\n\n"

    if "## Archive Links" in text:
        text = re.sub(r"(?s)## Archive Links\n\n.*?\n\n## ", archive_block + "## ", text, count=1)
    else:
        text = text.replace("## Publication Path\n\n", archive_block + "## Publication Path\n\n")

    text = text.replace(
        "Zenodo DOI and OSF mirror links will be added after archive registration.",
        f"Zenodo DOI: https://doi.org/{doi}\n\nOSF mirror: {osf_url.rstrip('/') + '/' if osf_url else 'pending'}",
    )
    text = text.replace(
        "After Zenodo mints the DOI, update `CITATION.cff`, `index.html`, and this note with the DOI.",
        f"Zenodo DOI. Done: `https://doi.org/{doi}` is recorded in `CITATION.cff`, `index.html`, and this note.",
    )
    if osf_url:
        text = text.replace(
            "Create or update the OSF project, upload or link the release artifacts, add the Zenodo DOI, and make the OSF project public when ready.",
            f"OSF mirror. Done: `{normalized_osf}` records the release artifacts and DOI.",
        )
        text = re.sub(
            r"(?m)^OSF mirror: (?:pending|https://osf\.io/[A-Za-z0-9_-]+/?)$",
            f"OSF mirror: {normalized_osf}",
            text,
        )
    return text


def replace_handoff(text: str, doi: str, osf_url: str | None) -> str:
    text = text.replace("- Zenodo DOI: pending", f"- Zenodo DOI: `https://doi.org/{doi}`")
    if osf_url:
        text = text.replace("- OSF mirror: pending", f"- OSF mirror: `{osf_url.rstrip('/')}/`")

    text = text.replace(
        "- `CITATION.cff`: add a top-level `doi: \"10.5281/zenodo.<record>\"`",
        f"- `CITATION.cff`: top-level `doi: \"{doi}\"`",
    )
    text = text.replace(
        "- `index.html`: add the DOI and Zenodo link in the citation/publication area",
        f"- `index.html`: DOI and Zenodo link recorded as `https://doi.org/{doi}`",
    )
    text = text.replace(
        "- `notes/release_notes.md`: replace the pending DOI note with the minted DOI",
        f"- `notes/release_notes.md`: DOI recorded as `https://doi.org/{doi}`",
    )
    text = text.replace(
        "- `notes/publication_handoff.md`: replace the pending DOI note with the minted DOI",
        f"- `notes/publication_handoff.md`: DOI recorded as `https://doi.org/{doi}`",
    )

    if osf_url:
        normalized_osf = f"{osf_url.rstrip('/')}/"
        text = text.replace(
            "- `index.html`: add the OSF project URL once public",
            f"- `index.html`: OSF project URL recorded as `{normalized_osf}`",
        )
        text = text.replace(
            "- `notes/release_notes.md`: add the OSF project URL",
            f"- `notes/release_notes.md`: OSF project URL recorded as `{normalized_osf}`",
        )
        text = text.replace(
            "- `notes/publication_handoff.md`: replace the pending OSF status with the public project URL",
            f"- `notes/publication_handoff.md`: OSF project URL recorded as `{normalized_osf}`",
        )
    return text


def build_replacements(doi: str, osf_url: str | None) -> list[Replacement]:
    files = {
        "CITATION.cff": replace_or_append_doi_cff(read("CITATION.cff"), doi),
        "index.html": replace_index(read("index.html"), doi, osf_url),
        "notes/release_notes.md": replace_release_notes(read("notes/release_notes.md"), doi, osf_url),
        "notes/publication_handoff.md": replace_handoff(read("notes/publication_handoff.md"), doi, osf_url),
    }
    replacements: list[Replacement] = []
    for relative, after in files.items():
        path = ROOT / relative
        before = path.read_text(encoding="utf-8")
        if before != after:
            replacements.append(Replacement(path, before, after))
    return replacements


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doi", required=True, help="Zenodo version DOI, for example 10.5281/zenodo.1234567")
    parser.add_argument("--osf-url", help="Public OSF project URL, for example https://osf.io/abcde/")
    parser.add_argument("--write", action="store_true", help="write changes; otherwise only report planned updates")
    args = parser.parse_args(argv)

    if not DOI_RE.fullmatch(args.doi):
        print(f"invalid Zenodo DOI: {args.doi}", file=sys.stderr)
        return 1
    if args.osf_url and not OSF_RE.fullmatch(args.osf_url):
        print(f"invalid OSF URL: {args.osf_url}", file=sys.stderr)
        return 1

    try:
        replacements = build_replacements(args.doi, args.osf_url)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not replacements:
        print("archive links already up to date")
        return 0

    for replacement in replacements:
        print(f"{'WRITE' if args.write else 'DRY-RUN'}: {rel(replacement.path)}")
        if args.write:
            write(replacement.path, replacement.after)

    if not args.write:
        print("Re-run with --write to update files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
