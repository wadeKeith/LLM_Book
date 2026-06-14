#!/usr/bin/env python3
"""Check English index coverage, alias consistency, and makeindex output."""

from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"
INDEX_LOG = BOOK_DIR / "book.ilg"

CHAPTER_FILES = sorted(CHAPTER_DIR.glob("ch*.tex"))
OTHER_INDEX_FILES = [
    BOOK_DIR / "preface.tex",
    BOOK_DIR / "ethics.tex",
    BOOK_DIR / "acronym.tex",
    BOOK_DIR / "glossary.tex",
    BOOK_DIR / "appendix.tex",
]
SOURCE_FILES = [*CHAPTER_FILES, *OTHER_INDEX_FILES]

MIN_TOTAL_INDEX_ENTRIES = 550
MIN_CHAPTER_INDEX_ENTRIES = 20
MAX_INDEX_DEPTH = 3
MAX_REPEATED_INDEX_ENTRY_COUNT = 4
TERMINAL_INDEX_COMPONENT_RE = re.compile(r"[.;:!?]\s*$")
REQUIRED_SEE_ENTRIES = {
    ("agents", "agent"),
    ("BPE", "byte pair encoding"),
    ("CoT", "chain-of-thought prompting"),
    ("DPO", "direct preference optimization"),
    ("embeddings", "embedding model"),
    ("FFN", "feed-forward network"),
    ("fine-tuning", "parameter-efficient adaptation"),
    ("FSDP", "fully sharded data parallel"),
    ("GQA", "grouped-query attention"),
    ("GRPO", "group relative policy optimization"),
    ("human feedback", "RLHF"),
    ("KV", "KV cache"),
    ("LLM", "large language model"),
    ("long context", "context window"),
    ("MHA", "multi-head attention"),
    ("MLA", "multi-head latent attention"),
    ("model judge", "LLM-as-judge"),
    ("MoE", "mixture of experts"),
    ("MQA", "multi-query attention"),
    ("PEFT", "parameter-efficient adaptation"),
    ("PPO", "proximal policy optimization"),
    ("RAG", "retrieval-augmented generation"),
    ("red team", "red teaming"),
    ("reinforcement learning from human feedback", "RLHF"),
    ("reinforcement learning with verifiable rewards", "RLVR"),
    ("RoPE", "rotary position embedding"),
    ("SFT", "supervised instruction tuning"),
    ("supervised fine tuning", "instruction tuning"),
    ("tools", "tool use"),
    ("vector database", "vector index"),
    ("VLM", "vision-language model"),
}
REQUIRED_INDEX_PATHS = {
    "attention!FlashAttention",
    "data!provenance",
    "distributed training!pipeline parallelism",
    "distributed training!tensor parallelism",
    "evaluation!benchmark contamination",
    "governance!risk management",
    "inference serving!continuous batching",
    "KV cache!paged attention",
    "mixture of experts!routing",
    "multimodal model!unified generation",
    "parameter-efficient adaptation!full fine-tuning",
    "preference objective!direct preference optimization",
    "retrieval-augmented generation!prompt injection",
    "safety!red teaming",
    "test-time compute!verification",
    "tokenization!coverage",
    "Transformer!decoder-only",
}
REQUIRED_PARENT_SUBENTRY_COUNTS = {
    "alignment": 3,
    "data": 3,
    "evaluation": 4,
    "governance": 3,
    "safety": 3,
    "tokenization": 3,
    "Transformer": 3,
}
ACRONYMS_THAT_SHOULD_BE_SEE_ALIASES = {
    "BPE",
    "CoT",
    "DPO",
    "FFN",
    "FSDP",
    "GQA",
    "GRPO",
    "KV",
    "LLM",
    "MHA",
    "MLA",
    "MoE",
    "MQA",
    "PEFT",
    "PPO",
    "RAG",
    "RoPE",
    "SFT",
    "VLM",
}


@dataclass(frozen=True)
class IndexEntry:
    raw: str
    path: Path
    line: int


def strip_tex_comments(text: str) -> str:
    stripped: list[str] = []
    for line in text.splitlines():
        escaped = False
        kept: list[str] = []
        for char in line:
            if char == "%" and not escaped:
                break
            kept.append(char)
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
        stripped.append("".join(kept))
    return "\n".join(stripped)


def find_braced_argument(text: str, open_brace: int) -> tuple[str, int] | None:
    depth = 0
    escaped = False
    for index in range(open_brace, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "{":
            depth += 1
            if depth == 1:
                start = index + 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index], index + 1
            if depth < 0:
                return None
    return None


def index_entries(path: Path) -> list[IndexEntry]:
    text = strip_tex_comments(path.read_text(encoding="utf-8"))
    entries: list[IndexEntry] = []
    position = 0
    marker = r"\index{"

    while True:
        start = text.find(marker, position)
        if start == -1:
            break
        open_brace = start + len(r"\index")
        parsed = find_braced_argument(text, open_brace)
        if parsed is None:
            line = text.count("\n", 0, start) + 1
            entries.append(IndexEntry("<malformed>", path, line))
            position = start + len(marker)
            continue
        raw, end = parsed
        line = text.count("\n", 0, start) + 1
        entries.append(IndexEntry(raw.strip(), path, line))
        position = end

    return entries


def see_entry(entry: str) -> tuple[str, str] | None:
    match = re.fullmatch(r"(.+?)\|see\{(.+)\}", entry)
    if not match:
        return None
    return match.group(1).strip(), match.group(2).strip()


def main_term(entry: str) -> str:
    return re.split(r"[!|]", entry, maxsplit=1)[0].strip()


def index_path_components(entry: str) -> list[str]:
    return [component.strip() for component in entry.split("|", 1)[0].split("!")]


def style_components(entry: str) -> list[str]:
    see = see_entry(entry)
    if see:
        alias, target = see
        return [alias, target]
    return index_path_components(entry)


def normalized_style_component(component: str) -> str:
    return re.sub(r"\s+", " ", component).strip().casefold()


def check_index_style(entries: list[IndexEntry], errors: list[str]) -> None:
    component_case: dict[str, set[str]] = {}

    for entry in entries:
        if entry.raw == "<malformed>":
            continue

        path = entry.path.relative_to(ROOT).as_posix()
        base = entry.raw.split("|", 1)[0]
        raw_components = base.split("!")

        if len(raw_components) > MAX_INDEX_DEPTH:
            errors.append(f"{path}:{entry.line}: index entry has too many levels: {entry.raw}")

        for component in raw_components:
            if not component.strip():
                errors.append(f"{path}:{entry.line}: index entry has an empty component: {entry.raw}")
            if component != component.strip():
                errors.append(f"{path}:{entry.line}: trim whitespace around index component: {entry.raw}")

        for component in style_components(entry.raw):
            if not component:
                continue
            if TERMINAL_INDEX_COMPONENT_RE.search(component):
                errors.append(f"{path}:{entry.line}: remove terminal punctuation from index component: {entry.raw}")
            normalized = normalized_style_component(component)
            component_case.setdefault(normalized, set()).add(component)

    for normalized, variants in sorted(component_case.items()):
        if len(variants) > 1:
            errors.append(
                "Index component capitalization is inconsistent for "
                f"{normalized!r}: {', '.join(sorted(variants))}"
            )


def parse_makeindex_log(errors: list[str]) -> tuple[int | None, int | None, int | None]:
    if not INDEX_LOG.exists():
        errors.append(f"Missing makeindex log: {INDEX_LOG.relative_to(ROOT).as_posix()}")
        return None, None, None

    text = INDEX_LOG.read_text(encoding="utf-8", errors="replace")
    accepted = rejected = warnings = None

    accepted_match = re.search(r"(\d+)\s+entries accepted,\s+(\d+)\s+rejected", text)
    if accepted_match:
        accepted = int(accepted_match.group(1))
        rejected = int(accepted_match.group(2))
    else:
        errors.append("Could not parse accepted/rejected counts from makeindex log")

    warning_match = re.search(r"(\d+)\s+warnings?", text)
    if warning_match:
        warnings = int(warning_match.group(1))
    else:
        errors.append("Could not parse warning count from makeindex log")

    if "!! Input index error" in text:
        errors.append("makeindex log contains input index errors")
    if rejected not in (None, 0):
        errors.append(f"makeindex rejected {rejected} entries")
    if warnings not in (None, 0):
        errors.append(f"makeindex reported {warnings} warnings")

    return accepted, rejected, warnings


def main() -> int:
    entries: list[IndexEntry] = []
    for path in SOURCE_FILES:
        entries.extend(index_entries(path))

    errors: list[str] = []
    malformed = [entry for entry in entries if entry.raw == "<malformed>"]
    for entry in malformed:
        errors.append(f"Malformed index entry: {entry.path.relative_to(ROOT).as_posix()}:{entry.line}")

    if len(entries) < MIN_TOTAL_INDEX_ENTRIES:
        errors.append(f"Only {len(entries)} source index entries; expected at least {MIN_TOTAL_INDEX_ENTRIES}")

    chapter_counts = Counter(entry.path for entry in entries if entry.path in CHAPTER_FILES)
    for path in CHAPTER_FILES:
        count = chapter_counts[path]
        if count < MIN_CHAPTER_INDEX_ENTRIES:
            errors.append(
                f"{path.relative_to(ROOT).as_posix()}: only {count} index entries; "
                f"expected at least {MIN_CHAPTER_INDEX_ENTRIES}"
            )

    see_entries = {see for entry in entries if (see := see_entry(entry.raw))}
    missing_see = sorted(REQUIRED_SEE_ENTRIES - see_entries)
    for alias, target in missing_see:
        errors.append(f"Missing index see entry: {alias}|see{{{target}}}")

    raw_entries = {entry.raw for entry in entries}
    missing_required_paths = sorted(REQUIRED_INDEX_PATHS - raw_entries)
    for required_path in missing_required_paths:
        errors.append(f"Missing required index topic path: {required_path}")

    parent_subentries: dict[str, set[str]] = {}
    for entry in entries:
        if entry.raw == "<malformed>" or see_entry(entry.raw):
            continue
        components = index_path_components(entry.raw)
        if len(components) >= 2:
            parent_subentries.setdefault(components[0], set()).add(components[1])

    for parent, minimum in sorted(REQUIRED_PARENT_SUBENTRY_COUNTS.items()):
        count = len(parent_subentries.get(parent, set()))
        if count < minimum:
            errors.append(
                f"Index parent {parent!r} has {count} subentries; expected at least {minimum}"
            )

    main_terms = {main_term(entry.raw) for entry in entries}
    for alias, target in sorted(see_entries):
        if target not in main_terms:
            errors.append(f"Index see entry {alias}|see{{{target}}} points to a missing main term")

    repeated_path_counts = Counter(
        entry.raw
        for entry in entries
        if entry.raw != "<malformed>" and not see_entry(entry.raw)
    )
    over_repeat_budget = sorted(
        (raw, count)
        for raw, count in repeated_path_counts.items()
        if count > MAX_REPEATED_INDEX_ENTRY_COUNT
    )
    for raw, count in over_repeat_budget:
        errors.append(
            f"Index entry {raw!r} appears {count} times; "
            f"maximum is {MAX_REPEATED_INDEX_ENTRY_COUNT}"
        )

    for entry in entries:
        if entry.raw in ACRONYMS_THAT_SHOULD_BE_SEE_ALIASES:
            errors.append(
                f"{entry.path.relative_to(ROOT).as_posix()}:{entry.line}: "
                f"use a full canonical index term instead of standalone {entry.raw}"
            )

    style_error_start = len(errors)
    check_index_style(entries, errors)
    style_errors = len(errors) - style_error_start

    accepted, rejected, warnings = parse_makeindex_log(errors)

    print(f"source index entries: {len(entries)}")
    print(f"main terms: {len(main_terms)}")
    print(f"see aliases: {len(see_entries)}")
    print(f"required index topic paths: {len(REQUIRED_INDEX_PATHS) - len(missing_required_paths)} / {len(REQUIRED_INDEX_PATHS)}")
    print(
        "required parent subentry groups: "
        f"{sum(1 for parent, minimum in REQUIRED_PARENT_SUBENTRY_COUNTS.items() if len(parent_subentries.get(parent, set())) >= minimum)} / "
        f"{len(REQUIRED_PARENT_SUBENTRY_COUNTS)}"
    )
    print(
        "maximum repeated source index path: "
        f"{max(repeated_path_counts.values(), default=0)} / {MAX_REPEATED_INDEX_ENTRY_COUNT}"
    )
    print(f"source index paths over repeat budget: {len(over_repeat_budget)}")
    print(f"index style errors: {style_errors}")
    print(f"chapter minimum entries: {min(chapter_counts.values()) if chapter_counts else 0}")
    if accepted is not None:
        print(f"makeindex accepted entries: {accepted}")
    if rejected is not None:
        print(f"makeindex rejected entries: {rejected}")
    if warnings is not None:
        print(f"makeindex warnings: {warnings}")

    if accepted is not None and accepted != len(entries):
        errors.append(f"makeindex accepted {accepted} entries, but source scan found {len(entries)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("index quality checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
