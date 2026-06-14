#!/usr/bin/env python3
"""Check that release documentation matches current audit targets and PDFs."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = ROOT / "Makefile"
README = ROOT / "README.md"
REFERENCE_AUDIT = ROOT / "notes" / "reference_audit.md"
PUBLICATION_AUDIT = ROOT / "notes" / "publication_quality_audit.md"
ACCEPTANCE_RUBRIC = ROOT / "notes" / "manuscript_acceptance_rubric.md"
PROVENANCE_REGISTER = ROOT / "notes" / "provenance_register.md"
SOURCE_INVENTORY = ROOT / "notes" / "source_inventory.md"
PROFESSOR_REVIEW = ROOT / "notes" / "professor_review.md"
VISUAL_AUDIT = ROOT / "notes" / "visual_audit.md"
TOC_REVIEW = ROOT / "notes" / "toc_review.md"
FRONTIER_GAP_REVIEW = ROOT / "notes" / "frontier_gap_review.md"
INDEX_AUDIT = ROOT / "notes" / "index_audit.md"
CHKTEX_TRIAGE = ROOT / "notes" / "chktex_triage.md"
PROOFING_PLAN = ROOT / "notes" / "proofing_plan.md"
BILINGUAL_COVERAGE = ROOT / "notes" / "bilingual_coverage.md"
BILINGUAL_PRINT_PLAN = ROOT / "notes" / "bilingual_print_plan.md"
BILINGUAL_ALIGNMENT_MANIFEST = ROOT / "notes" / "bilingual_alignment_manifest.md"
BOOK_DIR = ROOT / "book"
CITATION_CHECK = ROOT / "scripts" / "check_citations.py"
RELEASE_INVENTORY_CHECK = ROOT / "scripts" / "check_release_inventory.py"
SOURCE_INVENTORY_CHECK = ROOT / "scripts" / "check_source_inventory.py"
AUDIT_SCRIPT_CHECK = ROOT / "scripts" / "check_audit_scripts.py"
MAKEFILE_CONSISTENCY_CHECK = ROOT / "scripts" / "check_makefile_consistency.py"
REVIEWER_CHECK = ROOT / "scripts" / "check_reviewer_blockers.py"
PROVENANCE_CHECK = ROOT / "scripts" / "check_provenance_boundaries.py"
TOC_REVIEW_CHECK = ROOT / "scripts" / "check_toc_review.py"
FRONTMATTER_QUALITY_CHECK = ROOT / "scripts" / "check_frontmatter_quality.py"
ABSTRACT_QUALITY_CHECK = ROOT / "scripts" / "check_abstract_quality.py"
CHAPTER_CONTRACT_CHECK = ROOT / "scripts" / "check_chapter_contracts.py"
HEADING_QUALITY_CHECK = ROOT / "scripts" / "check_heading_quality.py"
FRONTIER_COVERAGE_CHECK = ROOT / "scripts" / "check_frontier_coverage.py"
BILINGUAL_COVERAGE_CHECK = ROOT / "scripts" / "check_bilingual_coverage.py"
BILINGUAL_ALIGNMENT_CHECK = ROOT / "scripts" / "check_bilingual_alignment_manifest.py"
INDEX_QUALITY_CHECK = ROOT / "scripts" / "check_index_quality.py"
RENDERED_INDEX_CHECK = ROOT / "scripts" / "check_rendered_index.py"
CHKTEX_TRIAGE_CHECK = ROOT / "scripts" / "check_chktex_triage.py"
CHKTEX_BUDGET_CHECK = ROOT / "scripts" / "check_chktex_budget.py"
VISUAL_AUDIT_PLAN_CHECK = ROOT / "scripts" / "check_visual_audit_plan.py"
PROOFING_PLAN_CHECK = ROOT / "scripts" / "check_proofing_plan.py"
CAPTION_QUALITY_CHECK = ROOT / "scripts" / "check_caption_quality.py"
TERM_CONSISTENCY_CHECK = ROOT / "scripts" / "check_term_consistency.py"
BACKMATTER_QUALITY_CHECK = ROOT / "scripts" / "check_backmatter_quality.py"
PROSE_QUALITY_CHECK = ROOT / "scripts" / "check_prose_quality.py"
CHINESE_PROSE_QUALITY_CHECK = ROOT / "scripts" / "check_chinese_prose_quality.py"
DUPLICATE_PROSE_CHECK = ROOT / "scripts" / "check_duplicate_prose.py"
PARAGRAPH_LENGTH_CHECK = ROOT / "scripts" / "check_paragraph_length.py"
EXERCISE_QUALITY_CHECK = ROOT / "scripts" / "check_exercise_quality.py"
REPRODUCIBILITY_CHECK = ROOT / "scripts" / "check_reproducibility_records.py"
PDF_TEXT_CHECK = ROOT / "scripts" / "check_pdf_text.py"
PDFINFO = os.environ.get("PDFINFO", "pdfinfo")


def parse_manuscript_audit_targets() -> list[str]:
    text = MAKEFILE.read_text(encoding="utf-8")
    match = re.search(r"^manuscript-audit:\s*(.+)$", text, re.MULTILINE)
    if not match:
        raise RuntimeError("Makefile is missing the manuscript-audit target")
    return [target for target in match.group(1).split() if target]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require_snippet(path: Path, snippet: str, errors: list[str]) -> None:
    if snippet not in read(path):
        errors.append(f"{path.relative_to(ROOT).as_posix()}: missing documentation snippet {snippet!r}")


def run_pdfinfo(path: Path) -> dict[str, str]:
    result = subprocess.run(
        [PDFINFO, str(path)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"pdfinfo failed for {path}")

    fields: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def run_python_check(script: Path, label: str) -> str:
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"{label} failed")
    return result.stdout


def run_citation_check() -> dict[str, int]:
    output = run_python_check(CITATION_CHECK, "citation check")

    patterns = {
        "cited": r"^cited keys:\s+(\d+)$",
        "entries": r"^bibliography entries:\s+(\d+)$",
        "titles": r"^bibliography titles checked:\s+(\d+)$",
        "years": r"^bibliography year fields checked:\s+(\d+)$",
        "year_range": r"^bibliography publication-year range:\s+(\d+)--(\d+)$",
        "arxiv": r"^bibliography arXiv locators checked:\s+(\d+)$",
        "arxiv_range": r"^bibliography arXiv month range:\s+([0-9]{4}-[0-9]{2})--([0-9]{4}-[0-9]{2})$",
        "urls": r"^bibliography URLs checked:\s+(\d+)$",
        "doi": r"^bibliography DOI fields checked:\s+(\d+)$",
        "http_exceptions": r"^documented HTTP URL exceptions:\s+(\d+)$",
        "unused": r"^unused bibliography entries:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from citation output")
        if name == "year_range":
            stats["min_year"] = int(match.group(1))
            stats["max_year"] = int(match.group(2))
        elif name == "arxiv_range":
            stats["min_arxiv_month"] = match.group(1)
            stats["max_arxiv_month"] = match.group(2)
        else:
            stats[name] = int(match.group(1))
    return stats


def run_provenance_check() -> dict[str, int]:
    output = run_python_check(PROVENANCE_CHECK, "provenance check")

    patterns = {
        "files": r"^manuscript TeX files checked:\s+(\d+)$",
        "sources": r"^external source text files scanned:\s+(\d+)$",
        "shingles": r"^manuscript (\d+)-word shingles:\s+(\d+)$",
        "cjk_shingles": r"^manuscript (\d+)-Han-character shingles:\s+(\d+)$",
        "hits": r"^long exact source-overlap hits:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from provenance output")
        if name == "shingles":
            stats["ngram_words"] = int(match.group(1))
            stats["shingles"] = int(match.group(2))
        elif name == "cjk_shingles":
            stats["cjk_chars"] = int(match.group(1))
            stats["cjk_shingles"] = int(match.group(2))
        else:
            stats[name] = int(match.group(1))
    return stats


def run_release_inventory_check() -> dict[str, int]:
    output = run_python_check(RELEASE_INVENTORY_CHECK, "release inventory check")

    patterns = {
        "files": r"^release files inventoried:\s+(\d+)$",
        "ignored": r"^build/private files ignored:\s+(\d+)$",
        "categories": r"^inventory categories checked:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from release inventory output")
        stats[name] = int(match.group(1))
    return stats


def run_source_inventory_check() -> dict[str, int]:
    output = run_python_check(SOURCE_INVENTORY_CHECK, "source inventory check")

    stats: dict[str, int] = {}
    patterns = {
        "files": r"^source-root regular files inventoried:\s+(\d+)$",
        "readable": r"^provenance-readable text/code files:\s+(\d+)$",
        "oversize": r"^oversize readable source files skipped by provenance:\s+(\d+)$",
    }
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from source inventory output")
        stats[name] = int(match.group(1))

    counts = re.search(
        r"^source inventory counts:\s+"
        r"mp4=(\d+)\s+pdf=(\d+)\s+pptx=(\d+)\s+py=(\d+)\s+"
        r"ipynb=(\d+)\s+md=(\d+)\s+txt=(\d+)$",
        output,
        re.MULTILINE,
    )
    if not counts:
        raise RuntimeError("could not parse suffix counts from source inventory output")
    for name, value in zip(("mp4", "pdf", "pptx", "py", "ipynb", "md", "txt"), counts.groups(), strict=True):
        stats[name] = int(value)
    return stats


def run_audit_script_check() -> dict[str, int]:
    output = run_python_check(AUDIT_SCRIPT_CHECK, "audit script check")

    patterns = {
        "scripts": r"^audit Python scripts checked:\s+(\d+)$",
        "referenced": r"^audit check scripts referenced by Makefile:\s+(\d+)$",
        "errors": r"^audit script compile/header errors:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from audit script output")
        stats[name] = int(match.group(1))
    return stats


def run_makefile_consistency_check() -> dict[str, int]:
    output = run_python_check(MAKEFILE_CONSISTENCY_CHECK, "Makefile consistency check")

    patterns = {
        "phony": r"^Makefile phony targets checked:\s+(\d+)$",
        "defined": r"^Makefile targets defined:\s+(\d+)$",
        "audit_deps": r"^manuscript-audit dependencies checked:\s+(\d+)$",
        "release_steps": r"^release-candidate recipe steps checked:\s+(\d+)$",
        "errors": r"^Makefile consistency errors:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from Makefile consistency output")
        stats[name] = int(match.group(1))
    return stats


def run_frontier_coverage_check() -> dict[str, int]:
    output = run_python_check(FRONTIER_COVERAGE_CHECK, "frontier coverage check")
    patterns = {
        "keys": r"^frontier bibliography keys checked:\s+(\d+)$",
        "english_citations": r"^English frontier citation hits:\s+(\d+)\s+/\s+(\d+)$",
        "chinese_citations": r"^Chinese frontier citation hits:\s+(\d+)\s+/\s+(\d+)$",
        "english_topics": r"^English frontier topic markers:\s+(\d+)\s+/\s+(\d+)$",
        "chinese_topics": r"^Chinese frontier topic markers:\s+(\d+)\s+/\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from frontier coverage output")
        if len(match.groups()) == 1:
            stats[name] = int(match.group(1))
        else:
            stats[name] = int(match.group(1))
            stats[f"{name}_total"] = int(match.group(2))
    return stats


def run_bilingual_coverage_check() -> dict[str, int | str]:
    output = run_python_check(BILINGUAL_COVERAGE_CHECK, "bilingual coverage check")
    patterns = {
        "pairs": r"^bilingual chapter pairs checked:\s+(\d+)$",
        "english_words": r"^English controlling body words:\s+(\d+)$",
        "chinese_han": r"^Chinese readable Han characters:\s+(\d+)$",
        "min_ratio": r"^minimum Chinese-to-English coverage ratio:\s+([0-9]+\.[0-9]+)\s+/\s+([0-9]+\.[0-9]+)$",
        "weakest_chapter": r"^weakest bilingual chapter:\s+(.+)$",
        "total_ratio": r"^total Chinese-to-English coverage ratio:\s+([0-9]+\.[0-9]+)\s+/\s+([0-9]+\.[0-9]+)$",
        "below_floor": r"^chapters below coverage floor:\s+(\d+)$",
    }
    stats: dict[str, int | str] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from bilingual coverage output")
        if name in {"min_ratio", "total_ratio"}:
            stats[name] = match.group(1)
            stats[f"{name}_floor"] = match.group(2)
        elif name == "weakest_chapter":
            stats[name] = match.group(1)
        else:
            stats[name] = int(match.group(1))
    return stats


def run_bilingual_alignment_check() -> dict[str, int]:
    output = run_python_check(BILINGUAL_ALIGNMENT_CHECK, "bilingual alignment check")
    patterns = {
        "source_units": r"^bilingual alignment source units available:\s+(\d+)$",
        "rows": r"^bilingual alignment manifest rows:\s+(\d+)$",
        "aligned": r"^bilingual alignment aligned units:\s+(\d+)$",
        "proofed": r"^bilingual alignment proofed units:\s+(\d+)$",
        "open": r"^bilingual alignment open units:\s+(\d+)$",
        "errors": r"^bilingual alignment manifest errors:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from bilingual alignment output")
        stats[name] = int(match.group(1))
    return stats


def run_toc_review_check() -> dict[str, int]:
    output = run_python_check(TOC_REVIEW_CHECK, "TOC review check")
    patterns = {
        "documented": r"^TOC review documented chapters:\s+(\d+)$",
        "matched": r"^English manuscript chapters matched:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from TOC review output")
        stats[name] = int(match.group(1))
    return stats


def run_abstract_quality_check() -> dict[str, int]:
    output = run_python_check(ABSTRACT_QUALITY_CHECK, "abstract quality check")
    patterns = {
        "abstracts": r"^English chapter abstracts checked:\s+(\d+)$",
        "min_words": r"^minimum abstract words:\s+(\d+)\s+/\s+(\d+)$",
        "max_words": r"^maximum abstract words:\s+(\d+)\s+/\s+(\d+)$",
        "duplicates": r"^duplicate abstracts:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from abstract quality output")
        stats[name] = int(match.group(1))
        if len(match.groups()) > 1:
            stats[f"{name}_floor" if name == "min_words" else f"{name}_ceiling"] = int(match.group(2))
    return stats


def run_chapter_contract_check() -> dict[str, int]:
    output = run_python_check(CHAPTER_CONTRACT_CHECK, "chapter contract check")
    patterns = {
        "contracts": r"^English chapter contracts checked:\s+(\d+)$",
        "min_words": r"^minimum contract words:\s+(\d+)\s+/\s+(\d+)$",
        "max_words": r"^maximum contract words:\s+(\d+)\s+/\s+(\d+)$",
        "marker_hits": r"^chapter contract marker hits:\s+(\d+)\s+/\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from chapter contract output")
        stats[name] = int(match.group(1))
        if len(match.groups()) > 1:
            stats[f"{name}_floor" if name == "min_words" else f"{name}_ceiling" if name == "max_words" else f"{name}_total"] = int(match.group(2))
    return stats


def run_frontmatter_quality_check() -> dict[str, int]:
    output = run_python_check(FRONTMATTER_QUALITY_CHECK, "front-matter quality check")
    patterns = {
        "en_preface_words": r"^English preface words:\s+(\d+)\s+/\s+(\d+)$",
        "en_ethics_words": r"^English ethics words:\s+(\d+)\s+/\s+(\d+)$",
        "zh_preface_han": r"^Chinese preface Han characters:\s+(\d+)\s+/\s+(\d+)$",
        "zh_ethics_han": r"^Chinese ethics Han characters:\s+(\d+)\s+/\s+(\d+)$",
        "marker_hits": r"^front-matter marker hits:\s+(\d+)\s+/\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from front-matter quality output")
        stats[name] = int(match.group(1))
        stats[f"{name}_floor" if name != "marker_hits" else f"{name}_total"] = int(match.group(2))
    return stats


def run_heading_quality_check() -> dict[str, int]:
    output = run_python_check(HEADING_QUALITY_CHECK, "heading quality check")
    patterns = {
        "files": r"^English chapter heading files checked:\s+(\d+)$",
        "headings": r"^English headings checked:\s+(\d+)$",
        "max_words": r"^maximum heading words:\s+(\d+)\s+/\s+(\d+)$",
        "duplicates": r"^duplicate headings within chapters:\s+(\d+)$",
        "chinese_files": r"^Chinese heading files checked:\s+(\d+)$",
        "chinese_headings": r"^Chinese headings checked:\s+(\d+)$",
        "max_chinese_units": r"^maximum Chinese heading text units:\s+(\d+)\s+/\s+(\d+)$",
        "chinese_duplicates": r"^duplicate Chinese headings within chapters:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from heading quality output")
        stats[name] = int(match.group(1))
        if len(match.groups()) > 1:
            stats[f"{name}_ceiling"] = int(match.group(2))
    return stats


def run_index_quality_check() -> dict[str, int]:
    output = run_python_check(INDEX_QUALITY_CHECK, "index quality check")
    patterns = {
        "entries": r"^source index entries:\s+(\d+)$",
        "main_terms": r"^main terms:\s+(\d+)$",
        "see_aliases": r"^see aliases:\s+(\d+)$",
        "required_paths": r"^required index topic paths:\s+(\d+)\s+/\s+(\d+)$",
        "parent_groups": r"^required parent subentry groups:\s+(\d+)\s+/\s+(\d+)$",
        "max_repeated_path": r"^maximum repeated source index path:\s+(\d+)\s+/\s+(\d+)$",
        "repeat_budget_errors": r"^source index paths over repeat budget:\s+(\d+)$",
        "style_errors": r"^index style errors:\s+(\d+)$",
        "chapter_min": r"^chapter minimum entries:\s+(\d+)$",
        "accepted": r"^makeindex accepted entries:\s+(\d+)$",
        "rejected": r"^makeindex rejected entries:\s+(\d+)$",
        "warnings": r"^makeindex warnings:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from index quality output")
        if len(match.groups()) == 1:
            stats[name] = int(match.group(1))
        else:
            stats[name] = int(match.group(1))
            stats[f"{name}_total"] = int(match.group(2))
    return stats


def run_rendered_index_check() -> dict[str, int]:
    output = run_python_check(RENDERED_INDEX_CHECK, "rendered index check")
    patterns = {
        "pages": r"^rendered index pages:\s+(\d+)$",
        "body_lines": r"^rendered index nonempty body lines:\s+(\d+)$",
        "required_terms": r"^rendered index required terms:\s+(\d+)\s+/\s+(\d+)$",
        "see_aliases": r"^rendered index see aliases:\s+(\d+)\s+/\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from rendered index output")
        stats[name] = int(match.group(1))
        if len(match.groups()) > 1:
            stats[f"{name}_total"] = int(match.group(2))
    return stats


def run_chktex_triage_check() -> dict[str, int]:
    output = run_python_check(CHKTEX_TRIAGE_CHECK, "ChkTeX triage check")
    patterns = {
        "classes": r"^ChkTeX triaged warning classes:\s+(\d+)$",
        "hits": r"^ChkTeX documented warning hits:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from ChkTeX triage output")
        stats[name] = int(match.group(1))
    return stats


def run_chktex_budget_check() -> dict[str, tuple[int, int]]:
    output = run_python_check(CHKTEX_BUDGET_CHECK, "ChkTeX budget check")
    matches = re.findall(r"^ChkTeX warning (\d+):\s+(\d+)\s+/\s+(\d+)$", output, re.MULTILINE)
    if not matches:
        raise RuntimeError("could not parse ChkTeX warning counts from budget output")
    return {warning: (int(count), int(budget)) for warning, count, budget in matches}


def run_visual_audit_plan_check() -> dict[str, int | str]:
    output = run_python_check(VISUAL_AUDIT_PLAN_CHECK, "visual-audit plan check")
    patterns = {
        "ranges": r"^visual-audit page ranges:\s+(\d+)$",
        "pngs": r"^visual-audit PNGs:\s+(\d+)$",
        "blanks": r"^expected blank visual pages:\s+(\d+)$",
        "english_text_sha256": r"^English visual-audit text SHA-256:\s+([0-9a-f]{64})$",
        "chinese_text_sha256": r"^Chinese visual-audit text SHA-256:\s+([0-9a-f]{64})$",
    }
    stats: dict[str, int | str] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from visual-audit plan output")
        if name in {"english_text_sha256", "chinese_text_sha256"}:
            stats[name] = match.group(1)
        else:
            stats[name] = int(match.group(1))
    return stats


def run_caption_quality_check() -> dict[str, int]:
    output = run_python_check(CAPTION_QUALITY_CHECK, "caption quality check")
    patterns = {
        "captions": r"^captions checked:\s+(\d+)$",
        "min_units": r"^minimum caption text units:\s+(\d+)\s+/\s+(\d+)$",
        "max_units": r"^maximum caption text units:\s+(\d+)\s+/\s+(\d+)$",
        "duplicates": r"^duplicate captions:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from caption quality output")
        stats[name] = int(match.group(1))
        if len(match.groups()) > 1:
            stats[f"{name}_floor" if name == "min_units" else f"{name}_ceiling"] = int(match.group(2))
    return stats


def run_backmatter_quality_check() -> dict[str, int]:
    output = run_python_check(BACKMATTER_QUALITY_CHECK, "back-matter quality check")
    patterns = {
        "en_sections": r"^English appendix sections:\s+(\d+)\s+/\s+(\d+)$",
        "en_markers": r"^English appendix marker hits:\s+(\d+)\s+/\s+(\d+)$",
        "acronyms": r"^acronym entries:\s+(\d+)$",
        "glossary": r"^glossary entries:\s+(\d+)$",
        "zh_sections": r"^Chinese appendix sections:\s+(\d+)\s+/\s+(\d+)$",
        "zh_markers": r"^Chinese appendix marker hits:\s+(\d+)\s+/\s+(\d+)$",
        "zh_glossary": r"^Chinese appendix glossary entries:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from back-matter quality output")
        stats[name] = int(match.group(1))
        if len(match.groups()) > 1:
            stats[f"{name}_total"] = int(match.group(2))
    return stats


def run_term_consistency_check() -> dict[str, int]:
    output = run_python_check(TERM_CONSISTENCY_CHECK, "term consistency check")
    patterns = {
        "acronyms": r"^acronym entries:\s+(\d+)$",
        "indexed_acronyms": r"^indexed acronym entries:\s+(\d+)$",
        "glossary": r"^glossary entries:\s+(\d+)$",
        "key_terms": r"^chapter key-term entries:\s+(\d+)$",
        "zh_chapters": r"^Chinese chapter key-term chapters:\s+(\d+)\s+/\s+(\d+)$",
        "zh_key_terms": r"^Chinese chapter key-term entries:\s+(\d+)$",
        "zh_min_terms": r"^Chinese minimum key-term entries per chapter:\s+(\d+)\s+/\s+(\d+)$",
        "zh_min_units": r"^Chinese minimum key-term text units:\s+(\d+)\s+/\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from term consistency output")
        stats[name] = int(match.group(1))
        if len(match.groups()) > 1:
            stats[f"{name}_total" if name == "zh_chapters" else f"{name}_floor"] = int(match.group(2))
    return stats


def run_exercise_quality_check() -> dict[str, int]:
    output = run_python_check(EXERCISE_QUALITY_CHECK, "exercise quality check")
    patterns = {
        "en_chapters": r"^English exercise chapters checked:\s+(\d+)\s+/\s+(\d+)$",
        "en_items": r"^English exercise items checked:\s+(\d+)$",
        "en_min_items": r"^English minimum exercise items per chapter:\s+(\d+)\s+/\s+(\d+)$",
        "en_min_words": r"^English minimum exercise-section words:\s+(\d+)\s+/\s+(\d+)$",
        "zh_chapters": r"^Chinese exercise chapters checked:\s+(\d+)\s+/\s+(\d+)$",
        "zh_items": r"^Chinese exercise items checked:\s+(\d+)$",
        "zh_min_items": r"^Chinese minimum exercise items per chapter:\s+(\d+)\s+/\s+(\d+)$",
        "zh_min_units": r"^Chinese minimum exercise-section text units:\s+(\d+)\s+/\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from exercise quality output")
        stats[name] = int(match.group(1))
        if len(match.groups()) > 1:
            stats[f"{name}_total" if name.endswith("chapters") else f"{name}_floor"] = int(match.group(2))
    return stats


def run_reproducibility_check() -> dict[str, int]:
    output = run_python_check(REPRODUCIBILITY_CHECK, "reproducibility check")
    patterns = {
        "en_fields": r"^English reproducibility fields checked:\s+(\d+)\s+/\s+(\d+)$",
        "zh_fields": r"^Chinese reproducibility fields checked:\s+(\d+)\s+/\s+(\d+)$",
        "errors": r"^reproducibility record errors:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from reproducibility output")
        stats[name] = int(match.group(1))
        if len(match.groups()) > 1:
            stats[f"{name}_total"] = int(match.group(2))
    return stats


def run_prose_quality_check() -> dict[str, int]:
    output = run_python_check(PROSE_QUALITY_CHECK, "prose quality check")
    patterns = {
        "files": r"^prose files checked:\s+(\d+)$",
        "lines": r"^prose lines checked:\s+(\d+)$",
        "words": r"^prose words checked:\s+(\d+)$",
        "findings": r"^copy-editing artifacts:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from prose quality output")
        stats[name] = int(match.group(1))
    return stats


def run_chinese_prose_quality_check() -> dict[str, int]:
    output = run_python_check(CHINESE_PROSE_QUALITY_CHECK, "Chinese prose quality check")
    patterns = {
        "lines": r"^Chinese prose lines checked:\s+(\d+)$",
        "han": r"^Chinese Han characters checked:\s+(\d+)$",
        "findings": r"^Chinese punctuation artifacts:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from Chinese prose quality output")
        stats[name] = int(match.group(1))
    return stats


def run_duplicate_prose_check() -> dict[str, int]:
    output = run_python_check(DUPLICATE_PROSE_CHECK, "duplicate prose check")
    patterns = {
        "files": r"^prose files checked:\s+(\d+)$",
        "paragraphs": r"^paragraphs checked:\s+(\d+)$",
        "sentences": r"^sentences checked:\s+(\d+)$",
        "findings": r"^duplicate long prose findings:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from duplicate prose output")
        stats[name] = int(match.group(1))
    return stats


def run_paragraph_length_check() -> dict[str, int]:
    output = run_python_check(PARAGRAPH_LENGTH_CHECK, "paragraph length check")
    patterns = {
        "files": r"^prose files checked:\s+(\d+)$",
        "paragraphs": r"^ordinary prose paragraphs checked:\s+(\d+)$",
        "max_english": r"^max English ordinary paragraph:\s+(\d+) words at .+$",
        "max_chinese": r"^max Chinese ordinary paragraph:\s+(\d+) Han characters at .+$",
        "findings": r"^overlength ordinary paragraphs:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from paragraph length output")
        stats[name] = int(match.group(1))
    return stats


def run_pdf_text_check() -> dict[str, int]:
    output = run_python_check(PDF_TEXT_CHECK, "PDF text check")
    stats: dict[str, int] = {}
    patterns = {
        "english_markers": r"^English PDF:\s+(\d+) markers checked,",
        "english_hits": r"^English PDF:\s+\d+ markers checked,\s+(\d+) marker hits,",
        "english_leaks": r"^English PDF:.*,\s+(\d+) source-leak hits$",
        "chinese_markers": r"^Chinese PDF:\s+(\d+) markers checked,",
        "chinese_hits": r"^Chinese PDF:\s+\d+ markers checked,\s+(\d+) marker hits,",
        "chinese_leaks": r"^Chinese PDF:.*,\s+(\d+) source-leak hits$",
    }
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from PDF text output")
        stats[name] = int(match.group(1))
    return stats


def run_proofing_plan_check() -> dict[str, int | str]:
    output = run_python_check(PROOFING_PLAN_CHECK, "proofing plan check")
    patterns = {
        "batches": r"^proofing batches checked:\s+(\d+)$",
        "english_pages": r"^English proofing pages covered:\s+(\d+)\s+/\s+(\d+)$",
        "chinese_pages": r"^Chinese proofing pages covered:\s+(\d+)\s+/\s+(\d+)$",
        "reviewed_batches": r"^reviewed proofing batches:\s+(\d+)\s+/\s+(\d+)$",
        "status": r"^full proofread status:\s+(.+)$",
        "english_text_sha256": r"^English proofing text SHA-256:\s+([0-9a-f]{64})$",
        "chinese_text_sha256": r"^Chinese proofing text SHA-256:\s+([0-9a-f]{64})$",
    }
    stats: dict[str, int | str] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from proofing plan output")
        if name in {"status", "english_text_sha256", "chinese_text_sha256"}:
            stats[name] = match.group(1)
        else:
            stats[name] = int(match.group(1))
            if len(match.groups()) > 1:
                stats[f"{name}_total"] = int(match.group(2))
    return stats


def run_reviewer_check() -> dict[str, int]:
    output = run_python_check(REVIEWER_CHECK, "reviewer blocker check")
    patterns = {
        "review_rows": r"^chapter review rows checked:\s+(\d+)$",
        "fingerprints": r"^chapter source fingerprints checked:\s+(\d+)$",
        "open_blockers": r"^open P0/P1 blockers:\s+(\d+)$",
        "closed_blockers": r"^closed P0/P1 blockers recorded:\s+(\d+)$",
    }
    stats: dict[str, int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise RuntimeError(f"could not parse {name} from reviewer blocker output")
        stats[name] = int(match.group(1))
    return stats


def check_audit_target_documentation(targets: list[str], errors: list[str]) -> None:
    for target in targets:
        require_snippet(README, f"make {target}", errors)
        require_snippet(REFERENCE_AUDIT, f"make {target}", errors)

    for snippet in ("make manuscript-audit", "make clean", "make clean-check"):
        require_snippet(README, snippet, errors)
        require_snippet(REFERENCE_AUDIT, snippet, errors)

    for path in (README, REFERENCE_AUDIT, PUBLICATION_AUDIT, ACCEPTANCE_RUBRIC):
        require_snippet(path, "make release-candidate", errors)

    for snippet in (
        "toolchain",
        "repository-hygiene",
        "release-inventory",
        "source-inventory",
        "audit-script",
        "makefile-consistency",
        "reviewer-blocker",
        "front-matter",
        "abstract-quality",
        "chapter-contract",
        "heading-quality",
        "TOC-review",
        "chapter-coverage",
        "edition-alignment",
        "bilingual-coverage",
        "frontier-coverage",
        "table-quality",
        "caption-quality",
        "DOI resolver URLs",
        "undocumented insecure HTTP URLs",
        "publication-year",
        "arXiv",
        "figure descriptions",
        "rendered PDF fonts",
        "rendered PDF metadata",
        "rendered PDF reference locators",
        "rendered bibliography labels",
        "rendered PDF outline",
        "rendered PDF page integrity",
        "rendered-page visual smoke",
        "all-page low-resolution visual",
        "visual-audit plan",
        "proofing-plan",
        "back-matter",
        "prose-quality",
        "Chinese prose-quality",
        "duplicate-prose",
        "paragraph-length",
        "exercise-quality",
        "reproducibility",
        "ChkTeX triage",
        "log-quality",
        "clean-check",
        "CJK-character long overlap",
    ):
        require_snippet(ACCEPTANCE_RUBRIC, snippet, errors)

    require_snippet(PROVENANCE_REGISTER, "make provenance-check", errors)
    require_snippet(PROVENANCE_REGISTER, "60-Han-character exact CJK overlap", errors)
    require_snippet(PROVENANCE_REGISTER, "make source-inventory-check", errors)
    require_snippet(PROVENANCE_REGISTER, "make release-inventory-check", errors)
    require_snippet(SOURCE_INVENTORY, "make source-inventory-check", errors)
    require_snippet(TOC_REVIEW, "make toc-review-check", errors)
    require_snippet(PUBLICATION_AUDIT, "Release-inventory gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Source-inventory gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Audit-script gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Makefile-consistency gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Toolchain gate", errors)
    require_snippet(PUBLICATION_AUDIT, "release inventory", errors)
    require_snippet(PUBLICATION_AUDIT, "Reviewer-blocker gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Open/Reopened P0/P1 blockers", errors)
    require_snippet(PUBLICATION_AUDIT, "Front-matter quality gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Abstract-quality gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Chapter-contract gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Heading-quality gate", errors)
    require_snippet(PUBLICATION_AUDIT, "TOC-review gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Edition-alignment gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Bilingual-coverage gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Bilingual-alignment gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Table-quality gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Caption-quality gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Back-matter quality gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Prose-quality gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Chinese prose-quality gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Duplicate-prose gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Paragraph-length gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Exercise-quality gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Reproducibility-record gate", errors)
    require_snippet(PUBLICATION_AUDIT, "ChkTeX triage gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Log-quality gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Visual-audit plan gate", errors)
    require_snippet(PUBLICATION_AUDIT, "Proofing-plan gate", errors)
    require_snippet(PROFESSOR_REVIEW, "Open P0/P1 blockers: 0", errors)
    require_snippet(PROFESSOR_REVIEW, "make manuscript-audit", errors)
    require_snippet(PROFESSOR_REVIEW, "make visual-audit", errors)
    require_snippet(PROFESSOR_REVIEW, "Current Chapter Source Fingerprints", errors)

    for path in (README, REFERENCE_AUDIT, ACCEPTANCE_RUBRIC):
        require_snippet(path, "DOI resolver URLs", errors)
        require_snippet(path, "undocumented insecure HTTP URLs", errors)
        require_snippet(path, "publication-year", errors)
        require_snippet(path, "arXiv", errors)
    require_snippet(PUBLICATION_AUDIT, "DOI field normalization", errors)
    require_snippet(PUBLICATION_AUDIT, "documented insecure-HTTP exceptions", errors)
    require_snippet(PUBLICATION_AUDIT, "publication-year", errors)
    require_snippet(PUBLICATION_AUDIT, "arXiv", errors)
    for path in (README, REFERENCE_AUDIT, PUBLICATION_AUDIT):
        require_snippet(path, "rendered PDF reference", errors)
    for path in (README, REFERENCE_AUDIT, PUBLICATION_AUDIT, ACCEPTANCE_RUBRIC):
        require_snippet(path, "rendered bibliography", errors)
    for path in (README, REFERENCE_AUDIT, PUBLICATION_AUDIT, ACCEPTANCE_RUBRIC):
        require_snippet(path, "source-leak", errors)
    for path in (README, REFERENCE_AUDIT, PUBLICATION_AUDIT, ACCEPTANCE_RUBRIC):
        require_snippet(path, "low-text page", errors)
    for path in (README, REFERENCE_AUDIT, PUBLICATION_AUDIT, ACCEPTANCE_RUBRIC):
        require_snippet(path, "blank-page", errors)
    for path in (README, REFERENCE_AUDIT, PUBLICATION_AUDIT, ACCEPTANCE_RUBRIC):
        require_snippet(path, "DescriptionTexts.txt", errors)
    for path in (README, REFERENCE_AUDIT, PUBLICATION_AUDIT, ACCEPTANCE_RUBRIC):
        require_snippet(path, "current file-size range", errors)
    for path in (README, REFERENCE_AUDIT, PUBLICATION_AUDIT, ACCEPTANCE_RUBRIC):
        require_snippet(path, "exact current page", errors)
    for path in (README, REFERENCE_AUDIT, PUBLICATION_AUDIT, VISUAL_AUDIT):
        require_snippet(path, "360 PNG", errors)
        require_snippet(path, "expected blank visual pages", errors)
    require_snippet(VISUAL_AUDIT, "English pages 38, 76, and 178", errors)
    for path in (README, REFERENCE_AUDIT, PUBLICATION_AUDIT, VISUAL_AUDIT):
        require_snippet(path, "make visual-full-check", errors)
        require_snippet(path, "all-page", errors)
    for path in (README, REFERENCE_AUDIT, PUBLICATION_AUDIT, PROOFING_PLAN):
        require_snippet(path, "make proofing-plan-check", errors)
        require_snippet(path, "full human proofread", errors)
    for path in (README, REFERENCE_AUDIT, PUBLICATION_AUDIT, ACCEPTANCE_RUBRIC, BILINGUAL_COVERAGE):
        require_snippet(path, "make bilingual-coverage-check", errors)
        require_snippet(path, "Chinese readable edition", errors)
    for path in (BILINGUAL_COVERAGE, FRONTIER_GAP_REVIEW, PROFESSOR_REVIEW):
        require_snippet(path, "paragraph-for-paragraph", errors)


def check_audit_target_count_note(targets: list[str], errors: list[str]) -> None:
    expected = f"confirmed that {len(targets)} `make manuscript-audit` targets are documented"
    if expected not in read(REFERENCE_AUDIT):
        errors.append(
            f"{REFERENCE_AUDIT.relative_to(ROOT).as_posix()}: "
            f"expected current audit-target count note {expected!r}"
        )


def check_pdf_metadata_notes(errors: list[str]) -> None:
    audit_text = read(PUBLICATION_AUDIT)
    expectations = [
        ("English", BOOK_DIR / "book.pdf"),
        ("Chinese", BOOK_DIR / "book_zh.pdf"),
    ]

    for label, path in expectations:
        fields = run_pdfinfo(path)
        pages = fields.get("Pages", "").split()[0]
        version = fields.get("PDF version", "")
        expected = f"{label} PDF metadata: {pages} pages, PDF {version}."
        if expected not in audit_text:
            errors.append(
                f"{PUBLICATION_AUDIT.relative_to(ROOT).as_posix()}: "
                f"expected current PDF page/version metadata line {expected!r}"
            )


def parse_size_token(value: str) -> int:
    return int(value.replace(",", ""))


def check_pdf_file_size_notes(errors: list[str]) -> None:
    audit_text = read(PUBLICATION_AUDIT)
    expectations = [
        ("English", BOOK_DIR / "book.pdf"),
        ("Chinese", BOOK_DIR / "book_zh.pdf"),
    ]

    for label, path in expectations:
        fields = run_pdfinfo(path)
        size_value = fields.get("File size", "").split()[0]
        if not size_value:
            errors.append(f"pdfinfo output for {path.relative_to(ROOT)} is missing File size")
            continue
        current_size = parse_size_token(size_value)
        pattern = re.compile(
            rf"Latest {label} PDF file size observed(?: across current clean builds)?: "
            rf"([0-9,]+)(?:--([0-9,]+))? bytes\."
        )
        match = pattern.search(audit_text)
        if not match:
            errors.append(
                f"{PUBLICATION_AUDIT.relative_to(ROOT).as_posix()}: "
                f"missing latest {label.lower()} PDF file-size note"
            )
            continue

        lower = parse_size_token(match.group(1))
        upper = parse_size_token(match.group(2)) if match.group(2) else lower
        if not lower <= current_size <= upper:
            expected = f"Latest {label} PDF file size observed: {current_size} bytes."
            errors.append(
                f"{PUBLICATION_AUDIT.relative_to(ROOT).as_posix()}: "
                f"current {label.lower()} PDF file size {current_size} is outside documented range "
                f"{lower}--{upper}; expected line like {expected!r}"
            )


def check_provenance_count_notes(errors: list[str]) -> None:
    stats = run_provenance_check()
    expected_snippets = (
        f"{stats['files']} manuscript TeX files",
        f"{stats['sources']} external",
        f"{stats['shingles']:,} manuscript",
        f"{stats['cjk_shingles']:,} manuscript {stats['cjk_chars']}-Han-character shingles",
        f"{stats['hits']} long exact source-overlap hits",
    )
    for path in (PROVENANCE_REGISTER, REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current provenance-count snippet {snippet!r}"
                )


def check_release_inventory_count_notes(errors: list[str]) -> None:
    stats = run_release_inventory_check()
    expected_snippets = (
        f"{stats['files']} release files",
        f"{stats['categories']} documented file classes",
        "ignored build/private files",
    )
    for path in (REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current release-inventory-count snippet {snippet!r}"
                )


def check_audit_script_count_notes(errors: list[str]) -> None:
    stats = run_audit_script_check()
    expected_snippets = (
        f"{stats['scripts']} audit Python scripts",
        f"{stats['referenced']} audit check scripts referenced by Makefile",
        f"{stats['errors']} audit script compile/header errors",
    )
    for path in (REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current audit-script-count snippet {snippet!r}"
                )


def check_makefile_consistency_count_notes(errors: list[str]) -> None:
    stats = run_makefile_consistency_check()
    expected_snippets = (
        f"{stats['phony']} Makefile phony targets",
        f"{stats['defined']} Makefile target definitions",
        f"{stats['audit_deps']} manuscript-audit dependencies",
        f"{stats['release_steps']} release-candidate recipe steps",
        f"{stats['errors']} Makefile consistency errors",
    )
    for path in (REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current Makefile-consistency-count snippet {snippet!r}"
                )


def check_citation_count_notes(errors: list[str]) -> None:
    stats = run_citation_check()
    expected_snippets = (
        f"{stats['cited']} unique cited keys",
        f"{stats['entries']} bibliography entries",
        f"{stats['titles']} checked bibliography titles",
        f"{stats['years']} checked bibliography years",
        f"{stats['min_year']}--{stats['max_year']} publication-year range",
        f"{stats['arxiv']} checked arXiv locators",
        f"{stats['min_arxiv_month']}--{stats['max_arxiv_month']} arXiv month range",
        f"{stats['urls']} checked bibliography URLs",
        f"{stats['doi']} checked DOI field",
        f"{stats['http_exceptions']} documented HTTP URL exception",
        f"{stats['unused']} unused bibliography entries",
    )
    for path in (REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current citation-count snippet {snippet!r}"
                )


def check_source_inventory_count_notes(errors: list[str]) -> None:
    stats = run_source_inventory_check()
    expected_snippets = (
        f"{stats['files']:,} regular source-root files",
        f"{stats['mp4']} MP4 files",
        f"{stats['pdf']} PDF files",
        f"{stats['pptx']} PPTX slide decks",
        f"{stats['py']} Python files",
        f"{stats['ipynb']} notebooks",
        f"{stats['md']} Markdown files",
        f"{stats['txt']} text files",
        f"{stats['readable']} provenance-readable text/code files",
        f"{stats['oversize']} readable files",
    )
    for path in (SOURCE_INVENTORY, REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current source-inventory-count snippet {snippet!r}"
                )


def check_frontier_coverage_count_notes(errors: list[str]) -> None:
    stats = run_frontier_coverage_check()
    expected_snippets = (
        f"{stats['keys']} required frontier bibliography keys",
        f"{stats['english_citations']}/{stats['english_citations_total']} English frontier citation hits",
        f"{stats['chinese_citations']}/{stats['chinese_citations_total']} Chinese frontier citation hits",
        f"{stats['english_topics']}/{stats['english_topics_total']} English frontier topic markers",
        f"{stats['chinese_topics']}/{stats['chinese_topics_total']} Chinese frontier topic markers",
    )
    for path in (FRONTIER_GAP_REVIEW, REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current frontier-coverage-count snippet {snippet!r}"
                )


def check_bilingual_coverage_count_notes(errors: list[str]) -> None:
    stats = run_bilingual_coverage_check()
    expected_snippets = (
        f"{stats['pairs']} bilingual chapter pairs",
        f"{stats['english_words']} English controlling body words",
        f"{stats['chinese_han']} Chinese readable Han characters",
        f"{stats['min_ratio']} minimum Chinese-to-English coverage ratio",
        f"weakest bilingual chapter: {stats['weakest_chapter']}",
        f"{stats['total_ratio']} total Chinese-to-English coverage ratio",
        f"{stats['below_floor']} chapters below coverage floor",
    )
    for path in (BILINGUAL_COVERAGE, REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current bilingual-coverage-count snippet {snippet!r}"
                )


def check_bilingual_alignment_count_notes(errors: list[str]) -> None:
    stats = run_bilingual_alignment_check()
    expected_snippets = (
        f"{stats['source_units']} source units",
        f"{stats['rows']} manifest rows",
        f"{stats['aligned']} aligned units",
        f"{stats['proofed']} proofed units",
        f"{stats['open']} open units",
        f"{stats['errors']} manifest errors",
    )
    for path in (
        README,
        BILINGUAL_COVERAGE,
        BILINGUAL_PRINT_PLAN,
        BILINGUAL_ALIGNMENT_MANIFEST,
        REFERENCE_AUDIT,
        PUBLICATION_AUDIT,
    ):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current bilingual-alignment-count snippet {snippet!r}"
                )


def check_toc_review_count_notes(errors: list[str]) -> None:
    stats = run_toc_review_check()
    expected_snippets = (
        f"{stats['documented']} documented TOC chapters",
        f"{stats['matched']} manuscript chapters",
    )
    for path in (TOC_REVIEW, REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current TOC-review-count snippet {snippet!r}"
                )


def check_abstract_quality_count_notes(errors: list[str]) -> None:
    stats = run_abstract_quality_check()
    expected_snippets = (
        f"{stats['abstracts']} English chapter abstracts",
        f"{stats['min_words']} minimum abstract words",
        f"{stats['max_words']} maximum abstract words",
        f"{stats['duplicates']} duplicate abstracts",
    )
    for path in (REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current abstract-quality-count snippet {snippet!r}"
                )


def check_chapter_contract_count_notes(errors: list[str]) -> None:
    stats = run_chapter_contract_check()
    expected_snippets = (
        f"{stats['contracts']} English chapter contracts",
        f"{stats['min_words']} minimum contract words",
        f"{stats['max_words']} maximum contract words",
        f"{stats['marker_hits']}/{stats['marker_hits_total']} chapter contract marker hits",
    )
    for path in (REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current chapter-contract-count snippet {snippet!r}"
                )


def check_frontmatter_quality_count_notes(errors: list[str]) -> None:
    stats = run_frontmatter_quality_check()
    expected_snippets = (
        f"{stats['en_preface_words']} English preface words",
        f"{stats['en_ethics_words']} English ethics words",
        f"{stats['zh_preface_han']} Chinese preface Han characters",
        f"{stats['zh_ethics_han']} Chinese ethics Han characters",
        f"{stats['marker_hits']}/{stats['marker_hits_total']} front-matter marker hits",
    )
    for path in (REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current front-matter-quality-count snippet {snippet!r}"
                )


def check_heading_quality_count_notes(errors: list[str]) -> None:
    stats = run_heading_quality_check()
    chinese_file_label = "Chinese heading file" if stats["chinese_files"] == 1 else "Chinese heading files"
    expected_snippets = (
        f"{stats['files']} English chapter heading files",
        f"{stats['headings']} English headings",
        f"{stats['max_words']} maximum heading words",
        f"{stats['duplicates']} duplicate headings within chapters",
        f"{stats['chinese_files']} {chinese_file_label}",
        f"{stats['chinese_headings']} Chinese headings",
        f"{stats['max_chinese_units']} maximum Chinese heading text units",
        f"{stats['chinese_duplicates']} duplicate Chinese headings within chapters",
    )
    for path in (REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current heading-quality-count snippet {snippet!r}"
                )


def check_index_quality_count_notes(errors: list[str]) -> None:
    stats = run_index_quality_check()
    rendered_stats = run_rendered_index_check()
    common_snippets = (
        f"{stats['entries']} source index entries",
        f"{stats['main_terms']} main terms",
        f"{stats['see_aliases']} `see` aliases",
        f"{stats['required_paths']}/{stats['required_paths_total']} required index topic paths",
        f"{stats['parent_groups']}/{stats['parent_groups_total']} required parent subentry groups",
        f"{stats['max_repeated_path']}/{stats['max_repeated_path_total']} maximum repeated source index path",
        f"{stats['repeat_budget_errors']} source index paths over repeat budget",
        f"{stats['style_errors']} index style errors",
        f"{stats['accepted']} accepted entries",
        f"{stats['rejected']} rejected entries",
        f"{stats['warnings']} warnings",
        f"{rendered_stats['pages']} rendered index pages",
        f"{rendered_stats['body_lines']} nonempty rendered index body lines",
        f"{rendered_stats['required_terms']}/{rendered_stats['required_terms_total']} rendered index required terms",
        f"{rendered_stats['see_aliases']}/{rendered_stats['see_aliases_total']} rendered index see aliases",
    )
    for path in (INDEX_AUDIT, REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in common_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current index-quality-count snippet {snippet!r}"
                )

    chapter_min_snippet = f"minimum of {stats['chapter_min']} entries"
    text = read(INDEX_AUDIT)
    if chapter_min_snippet not in text:
        errors.append(
            f"{INDEX_AUDIT.relative_to(ROOT).as_posix()}: "
            f"missing current index-quality-count snippet {chapter_min_snippet!r}"
        )


def check_chktex_triage_count_notes(errors: list[str]) -> None:
    stats = run_chktex_triage_check()
    counts = run_chktex_budget_check()
    expected_snippets = [
        f"{stats['classes']} ChkTeX triaged warning classes",
        f"{stats['hits']} current ChkTeX warning hits",
    ]
    expected_snippets.extend(
        f"{warning}:{count}/{budget}"
        for warning, (count, budget) in sorted(counts.items(), key=lambda item: int(item[0]))
    )
    for path in (CHKTEX_TRIAGE, REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current ChkTeX-triage-count snippet {snippet!r}"
                )


def check_visual_audit_plan_count_notes(errors: list[str]) -> None:
    stats = run_visual_audit_plan_check()
    expected_snippets = (
        f"{stats['ranges']} visual-audit page ranges",
        f"{stats['pngs']} visual-audit PNGs",
        f"{stats['blanks']} expected blank visual pages",
        f"English visual-audit text SHA-256: {stats['english_text_sha256']}",
        f"Chinese visual-audit text SHA-256: {stats['chinese_text_sha256']}",
    )
    for path in (VISUAL_AUDIT, REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current visual-audit-plan-count snippet {snippet!r}"
                )


def check_reviewer_count_notes(errors: list[str]) -> None:
    stats = run_reviewer_check()
    expected_snippets = (
        f"{stats['review_rows']} passing chapter review rows",
        f"{stats['fingerprints']} chapter source fingerprints",
        f"{stats['open_blockers']} Open/Reopened P0/P1 blockers",
        f"{stats['closed_blockers']} closed P0/P1 blockers",
    )
    for path in (PROFESSOR_REVIEW, REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current reviewer-count snippet {snippet!r}"
                )


def check_proofing_plan_count_notes(errors: list[str]) -> None:
    stats = run_proofing_plan_check()
    expected_snippets = (
        f"{stats['batches']} proofing batches",
        f"{stats['english_pages']}/{stats['english_pages_total']} English proofing pages",
        f"{stats['chinese_pages']}/{stats['chinese_pages_total']} Chinese proofing pages",
        f"{stats['reviewed_batches']}/{stats['reviewed_batches_total']} reviewed proofing batches",
        f"{stats['status']} proofread status",
        f"English proofing text SHA-256: {stats['english_text_sha256']}",
        f"Chinese proofing text SHA-256: {stats['chinese_text_sha256']}",
    )
    for path in (PROOFING_PLAN, REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current proofing-plan-count snippet {snippet!r}"
                )


def check_caption_quality_count_notes(errors: list[str]) -> None:
    stats = run_caption_quality_check()
    expected_snippets = (
        f"{stats['captions']} captions",
        f"{stats['min_units']} minimum caption text units",
        f"{stats['max_units']} maximum caption text units",
        f"{stats['duplicates']} duplicate captions",
    )
    for path in (REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current caption-quality-count snippet {snippet!r}"
                )


def check_backmatter_quality_count_notes(errors: list[str]) -> None:
    stats = run_backmatter_quality_check()
    expected_snippets = (
        f"{stats['en_sections']}/{stats['en_sections_total']} English appendix sections",
        f"{stats['en_markers']}/{stats['en_markers_total']} English appendix marker hits",
        f"{stats['acronyms']} acronym entries",
        f"{stats['glossary']} glossary entries",
        f"{stats['zh_sections']}/{stats['zh_sections_total']} Chinese appendix sections",
        f"{stats['zh_markers']}/{stats['zh_markers_total']} Chinese appendix marker hits",
        f"{stats['zh_glossary']} Chinese appendix glossary entries",
    )
    for path in (REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current back-matter-quality-count snippet {snippet!r}"
                )


def check_term_consistency_count_notes(errors: list[str]) -> None:
    stats = run_term_consistency_check()
    expected_snippets = (
        f"{stats['acronyms']} acronym entries",
        f"{stats['indexed_acronyms']} indexed acronym entries",
        f"{stats['glossary']} glossary entries",
        f"{stats['key_terms']} chapter key-term entries",
        f"{stats['zh_chapters']}/{stats['zh_chapters_total']} Chinese chapter key-term chapters",
        f"{stats['zh_key_terms']} Chinese chapter key-term entries",
        f"{stats['zh_min_terms']}/{stats['zh_min_terms_floor']} Chinese minimum key-term entries per chapter",
        f"{stats['zh_min_units']} Chinese minimum key-term text units",
    )
    for path in (REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current term-consistency-count snippet {snippet!r}"
                )


def check_exercise_quality_count_notes(errors: list[str]) -> None:
    stats = run_exercise_quality_check()
    expected_snippets = (
        f"{stats['en_chapters']}/{stats['en_chapters_total']} English exercise chapters",
        f"{stats['en_items']} English exercise items",
        f"{stats['en_min_items']}/{stats['en_min_items_floor']} English minimum exercise items per chapter",
        f"{stats['en_min_words']} English minimum exercise-section words",
        f"{stats['zh_chapters']}/{stats['zh_chapters_total']} Chinese exercise chapters",
        f"{stats['zh_items']} Chinese exercise items",
        f"{stats['zh_min_items']}/{stats['zh_min_items_floor']} Chinese minimum exercise items per chapter",
        f"{stats['zh_min_units']} Chinese minimum exercise-section text units",
    )
    for path in (REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current exercise-quality-count snippet {snippet!r}"
                )


def check_reproducibility_count_notes(errors: list[str]) -> None:
    stats = run_reproducibility_check()
    expected_snippets = (
        f"{stats['en_fields']}/{stats['en_fields_total']} English reproducibility fields",
        f"{stats['zh_fields']}/{stats['zh_fields_total']} Chinese reproducibility fields",
        f"{stats['errors']} reproducibility-record errors",
    )
    for path in (REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current reproducibility-count snippet {snippet!r}"
                )


def check_prose_quality_count_notes(errors: list[str]) -> None:
    stats = run_prose_quality_check()
    expected_snippets = (
        f"{stats['files']} English manuscript files",
        f"{stats['lines']:,} source prose lines",
        f"{stats['words']:,} words",
        f"{stats['findings']} copy-editing artifacts",
    )
    for path in (REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current prose-quality-count snippet {snippet!r}"
                )


def check_chinese_prose_quality_count_notes(errors: list[str]) -> None:
    stats = run_chinese_prose_quality_check()
    expected_snippets = (
        f"{stats['lines']} Chinese prose lines",
        f"{stats['han']:,} Han characters",
        f"{stats['findings']} punctuation artifacts",
    )
    for path in (REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current Chinese-prose-quality-count snippet {snippet!r}"
                )


def check_duplicate_prose_count_notes(errors: list[str]) -> None:
    stats = run_duplicate_prose_check()
    expected_snippets = (
        f"{stats['files']} prose files",
        f"{stats['paragraphs']:,} paragraphs",
        f"{stats['sentences']:,} sentences",
        f"{stats['findings']} duplicate long prose findings",
    )
    for path in (REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current duplicate-prose-count snippet {snippet!r}"
                )


def check_paragraph_length_count_notes(errors: list[str]) -> None:
    stats = run_paragraph_length_check()
    expected_snippets = (
        f"{stats['files']} prose files",
        f"{stats['paragraphs']:,} ordinary prose paragraphs",
        f"{stats['max_english']} words",
        f"{stats['max_chinese']} Han characters",
        f"{stats['findings']} overlength ordinary paragraphs",
    )
    for path in (REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current paragraph-length-count snippet {snippet!r}"
                )


def check_pdf_text_count_notes(errors: list[str]) -> None:
    stats = run_pdf_text_check()
    expected_snippets = (
        f"{stats['english_markers']} marker classes",
        f"{stats['english_hits']} marker hits in the English PDF",
        f"{stats['chinese_markers']} marker classes",
        f"{stats['chinese_hits']} marker hits in the Chinese PDF",
        f"{stats['english_leaks']} rendered source-leak hits",
    )
    for path in (REFERENCE_AUDIT, PUBLICATION_AUDIT):
        text = read(path)
        for snippet in expected_snippets:
            if snippet not in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"missing current PDF-text-count snippet {snippet!r}"
                )


def main() -> int:
    errors: list[str] = []

    try:
        targets = parse_manuscript_audit_targets()
        check_audit_target_documentation(targets, errors)
        check_audit_target_count_note(targets, errors)
        check_pdf_metadata_notes(errors)
        check_pdf_file_size_notes(errors)
        check_citation_count_notes(errors)
        check_release_inventory_count_notes(errors)
        check_source_inventory_count_notes(errors)
        check_audit_script_count_notes(errors)
        check_makefile_consistency_count_notes(errors)
        check_reviewer_count_notes(errors)
        check_provenance_count_notes(errors)
        check_frontmatter_quality_count_notes(errors)
        check_abstract_quality_count_notes(errors)
        check_chapter_contract_count_notes(errors)
        check_heading_quality_count_notes(errors)
        check_toc_review_count_notes(errors)
        check_bilingual_coverage_count_notes(errors)
        check_bilingual_alignment_count_notes(errors)
        check_frontier_coverage_count_notes(errors)
        check_index_quality_count_notes(errors)
        check_chktex_triage_count_notes(errors)
        check_visual_audit_plan_count_notes(errors)
        check_proofing_plan_count_notes(errors)
        check_caption_quality_count_notes(errors)
        check_term_consistency_count_notes(errors)
        check_backmatter_quality_count_notes(errors)
        check_exercise_quality_count_notes(errors)
        check_reproducibility_count_notes(errors)
        check_prose_quality_count_notes(errors)
        check_chinese_prose_quality_count_notes(errors)
        check_duplicate_prose_count_notes(errors)
        check_paragraph_length_count_notes(errors)
        check_pdf_text_count_notes(errors)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"manuscript-audit targets documented: {len(targets)}")
    print("citation documentation counts matched current run")
    print("release inventory documentation counts matched current run")
    print("source inventory documentation counts matched current run")
    print("audit script documentation counts matched current run")
    print("Makefile consistency documentation counts matched current run")
    print("reviewer documentation counts matched current run")
    print("provenance documentation counts matched current run")
    print("front-matter, abstract, chapter-contract, heading, TOC, bilingual-coverage, bilingual-alignment, frontier, index, ChkTeX, visual-audit, proofing-plan, caption, term, back-matter, exercise, and reproducibility documentation counts matched current run")
    print("prose and rendered-text documentation counts matched current run")
    print("release documentation consistency checks passed" if not errors else "release documentation consistency failures")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
