#!/usr/bin/env python3
"""Check manuscript citation keys, BibTeX structure, and bibliography metadata."""

from __future__ import annotations

import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
TEX_FILES = [
    BOOK_DIR / "book.tex",
    BOOK_DIR / "book_zh.tex",
    BOOK_DIR / "preface.tex",
    BOOK_DIR / "ethics.tex",
    BOOK_DIR / "acronym.tex",
    BOOK_DIR / "glossary.tex",
    BOOK_DIR / "appendix.tex",
    *sorted((BOOK_DIR / "chapters").glob("*.tex")),
]
BIB_FILE = BOOK_DIR / "references.bib"

CITE_RE = re.compile(
    r"\\(?:cite|citep|citet|citealp|citeauthor|citeyear|nocite)"
    r"\s*(?:\[[^\]]*\]\s*){0,2}\{([^{}]+)\}",
    re.DOTALL,
)
BIB_KEY_RE = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.IGNORECASE)
FIELD_HEAD_RE = re.compile(r"\s*([A-Za-z]+)\s*=")
URL_RE = re.compile(r"^https?://\S+$", re.IGNORECASE)
DOI_RE = re.compile(r"^10\.\S+/\S+$", re.IGNORECASE)
DOI_URL_RE = re.compile(r"^https://doi\.org/(10\.\S+/\S+)$", re.IGNORECASE)
ARXIV_PREPRINT_RE = re.compile(r"arXiv preprint arXiv:([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)", re.IGNORECASE)
ARXIV_URL_RE = re.compile(r"^https://arxiv\.org/abs/([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)$", re.IGNORECASE)
HOWPUBLISHED_URL_RE = re.compile(r"\\url\{([^{}]+)\}")
ARXIV_ID_RE = re.compile(r"^([0-9]{2})([0-9]{2})\.[0-9]{4,5}(?:v[0-9]+)?$")
YEAR_RE = re.compile(r"^[0-9]{4}$")
MIN_PUBLICATION_YEAR = 1900
HTTP_URL_EXCEPTIONS = {
    "http://incompleteideas.net/book/the-book-2nd.html",
}
PROTECTED_TITLE_PATTERNS = (
    ("AI", r"AI"),
    ("API", r"API"),
    ("AWQ", r"AWQ"),
    ("BERT", r"BERT"),
    ("BioGPT", r"BioGPT"),
    ("BLIP", r"BLIP"),
    ("C2PA", r"C2PA"),
    ("ChatGPT", r"ChatGPT"),
    ("Chinchilla", r"Chinchilla"),
    ("CLIP", r"CLIP"),
    ("Claude", r"Claude"),
    ("DeepSeek", r"DeepSeek(?:-[A-Za-z0-9.]+)?"),
    ("DPO", r"DPO"),
    ("DROP", r"DROP"),
    ("FP8", r"FP8"),
    ("Flamingo", r"Flamingo"),
    ("FlashAttention", r"FlashAttention(?:-[0-9]+)?"),
    ("FSDP", r"FSDP"),
    ("GLU", r"GLU"),
    ("GPT", r"(?:[A-Za-z]*GPT[A-Za-z0-9]*)(?:-[A-Za-z0-9.]+)?"),
    ("GPTQ", r"GPTQ"),
    ("GPQA", r"GPQA"),
    ("GQA", r"GQA"),
    ("GRPO", r"GRPO"),
    ("HumanEval", r"HumanEval"),
    ("IO", r"IO"),
    ("KTO", r"KTO"),
    ("KV", r"KV"),
    ("LLaMA", r"LLaMA"),
    ("LLM", r"LLMs?"),
    ("LoRA", r"(?:Long)?LoRA"),
    ("Mamba", r"Mamba"),
    ("MATH", r"MATH"),
    ("Medusa", r"Medusa"),
    ("MGSM", r"MGSM"),
    ("MHA", r"MHA"),
    ("MLA", r"MLA"),
    ("MMLU", r"MMLU"),
    ("MoE", r"MoE"),
    ("MQA", r"MQA"),
    ("MT-Bench", r"MT-Bench"),
    ("NF4", r"NF4"),
    ("NIST", r"NIST"),
    ("NLG", r"NLG"),
    ("ORPO", r"ORPO"),
    ("PEFT", r"PEFT"),
    ("PPO", r"PPO"),
    ("QLoRA", r"QLoRA"),
    ("Qwen", r"Qwen[A-Za-z0-9.-]*"),
    ("RAG", r"RAG"),
    ("RAGAS", r"RAGAS"),
    ("RetNet", r"RetNet"),
    ("RLHF", r"RLHF"),
    ("RLAIF", r"RLAIF"),
    ("RLVR", r"RLVR"),
    ("RMSNorm", r"RMSNorm"),
    ("RoPE", r"RoPE"),
    ("SFT", r"SFT"),
    ("SimPO", r"SimPO"),
    ("SentencePiece", r"SentencePiece"),
    ("SSM", r"SSMs?"),
    ("StreamingLLM", r"StreamingLLM"),
    ("SwiGLU", r"SwiGLU"),
    ("Transformer", r"Transformers?"),
    ("vLLM", r"vLLM"),
    ("VLA", r"VLA"),
    ("VLM", r"VLM"),
    ("WebGPT", r"WebGPT"),
    ("ZeRO", r"ZeRO(?:[-+A-Za-z0-9]*)?"),
)


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


def cited_keys() -> set[str]:
    keys: set[str] = set()
    for path in TEX_FILES:
        text = strip_tex_comments(path.read_text(encoding="utf-8"))
        for match in CITE_RE.finditer(text):
            for key in match.group(1).split(","):
                key = key.strip()
                if key and key != "*":
                    keys.add(key)
    return keys


def is_blank_or_comment(text: str) -> bool:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("%"):
            return False
    return True


def find_entry_end(text: str, open_brace_index: int) -> int | None:
    depth = 0
    escaped = False
    for index in range(open_brace_index, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
            if depth < 0:
                return None
    return None


def find_balanced_value_end(text: str, start: int, open_char: str, close_char: str) -> int | None:
    depth = 0
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return index + 1
            if depth < 0:
                return None
    return None


def find_quoted_value_end(text: str, start: int) -> int | None:
    escaped = False
    for index in range(start + 1, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            return index + 1
    return None


def parse_fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    position = 0
    while position < len(body):
        while position < len(body) and body[position] in ", \t\r\n":
            position += 1

        match = FIELD_HEAD_RE.match(body, position)
        if not match:
            break

        name = match.group(1).lower()
        value_start = match.end()
        while value_start < len(body) and body[value_start].isspace():
            value_start += 1
        if value_start >= len(body):
            fields[name] = ""
            break

        if body[value_start] == "{":
            value_end = find_balanced_value_end(body, value_start, "{", "}")
            if value_end is None:
                fields[name] = body[value_start:].strip()
                break
            value = body[value_start + 1 : value_end - 1]
        elif body[value_start] == '"':
            value_end = find_quoted_value_end(body, value_start)
            if value_end is None:
                fields[name] = body[value_start:].strip()
                break
            value = body[value_start + 1 : value_end - 1]
        else:
            comma = body.find(",", value_start)
            value_end = comma if comma != -1 else len(body)
            value = body[value_start:value_end]

        fields[name] = re.sub(r"\s+", " ", value).strip()
        position = value_end + 1

    return fields


def bib_entries() -> tuple[dict[str, dict[str, str]], list[str], list[str]]:
    text = BIB_FILE.read_text(encoding="utf-8")
    entries: dict[str, dict[str, str]] = {}
    keys: list[str] = []
    errors: list[str] = []

    position = 0
    while position < len(text):
        match = BIB_KEY_RE.search(text, position)
        if not match:
            if not is_blank_or_comment(text[position:]):
                errors.append("Unexpected text after final bibliography entry")
            break

        if not is_blank_or_comment(text[position : match.start()]):
            errors.append(f"Unexpected text before bibliography key {match.group(2)}")

        open_brace = text.find("{", match.start(), match.end())
        if open_brace == -1:
            errors.append(f"Malformed bibliography entry header for {match.group(2)}")
            position = match.end()
            continue

        end = find_entry_end(text, open_brace)
        if end is None:
            errors.append(f"Unbalanced braces in bibliography entry {match.group(2)}")
            break

        key = match.group(2)
        keys.append(key)
        body = text[match.end() : end - 1]
        entries[key] = parse_fields(body)
        position = end

    duplicates = sorted(key for key, count in Counter(keys).items() if count > 1)
    return entries, duplicates, errors


def normalized_title(value: str) -> str:
    value = value.replace(r"\&", "and")
    value = re.sub(r"\\[A-Za-z]+", " ", value)
    value = re.sub(r"[^A-Za-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip().lower()


def normalized_url(value: str) -> str:
    return value.rstrip("/")


def bibliography_value_errors(entries: dict[str, dict[str, str]]) -> list[str]:
    errors: list[str] = []
    titles: dict[str, list[str]] = {}
    urls: dict[str, list[str]] = {}

    for key, fields in entries.items():
        title = normalized_title(fields.get("title", ""))
        if title:
            titles.setdefault(title, []).append(key)

        url_values = []
        if fields.get("url"):
            url_values.append(fields["url"])
        url_values.extend(HOWPUBLISHED_URL_RE.findall(fields.get("howpublished", "")))
        for url in url_values:
            if not URL_RE.match(url):
                errors.append(f"{key}: malformed URL value: {url}")
                continue
            if url.lower().startswith("http://") and url not in HTTP_URL_EXCEPTIONS:
                errors.append(f"{key}: insecure HTTP URL is not documented as an exception: {url}")
            doi_url = DOI_URL_RE.match(url)
            if doi_url:
                errors.append(f"{key}: store DOI resolver URL as doi field instead: {doi_url.group(1)}")
            urls.setdefault(normalized_url(url), []).append(key)

        doi = fields.get("doi")
        if doi and (doi.lower().startswith(("http://", "https://")) or not DOI_RE.match(doi)):
            errors.append(f"{key}: malformed DOI value: {doi}")

        journal = fields.get("journal", "")
        arxiv_preprint = ARXIV_PREPRINT_RE.search(journal)
        if arxiv_preprint:
            expected = arxiv_preprint.group(1)
            arxiv_locator = fields.get("eprint", "")
            url = fields.get("url", "")
            url_match = ARXIV_URL_RE.match(url)
            if not (arxiv_locator == expected or (url_match and url_match.group(1) == expected)):
                errors.append(f"{key}: arXiv preprint id {expected} does not match eprint/url fields")

        eprint = fields.get("eprint")
        archive = fields.get("archiveprefix", "")
        if eprint and archive.lower() == "arxiv" and not re.match(r"^[0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?$", eprint):
            errors.append(f"{key}: malformed arXiv eprint value: {eprint}")

    duplicate_titles = sorted((title, keys) for title, keys in titles.items() if len(keys) > 1)
    duplicate_urls = sorted((url, keys) for url, keys in urls.items() if len(keys) > 1)
    for title, keys in duplicate_titles:
        errors.append(f"Duplicate bibliography title across keys {', '.join(keys)}: {title}")
    for url, keys in duplicate_urls:
        errors.append(f"Duplicate bibliography URL across keys {', '.join(keys)}: {url}")

    return errors


def bibliography_value_counts(entries: dict[str, dict[str, str]]) -> tuple[int, int, int, int]:
    title_count = sum(1 for fields in entries.values() if fields.get("title"))
    url_count = 0
    doi_count = 0
    insecure_exception_count = 0
    for fields in entries.values():
        if fields.get("doi"):
            doi_count += 1
        if url := fields.get("url"):
            url_count += 1
            if url in HTTP_URL_EXCEPTIONS:
                insecure_exception_count += 1
        howpublished_urls = HOWPUBLISHED_URL_RE.findall(fields.get("howpublished", ""))
        url_count += len(howpublished_urls)
        insecure_exception_count += sum(1 for url in howpublished_urls if url in HTTP_URL_EXCEPTIONS)
    return title_count, url_count, doi_count, insecure_exception_count


def bibliography_year_errors(entries: dict[str, dict[str, str]], current_year: int) -> list[str]:
    errors: list[str] = []
    for key, fields in entries.items():
        year = fields.get("year", "")
        if not year:
            continue
        if not YEAR_RE.match(year):
            errors.append(f"{key}: malformed publication year value: {year}")
            continue
        numeric_year = int(year)
        if numeric_year < MIN_PUBLICATION_YEAR:
            errors.append(f"{key}: implausibly old publication year: {year}")
        if numeric_year > current_year:
            errors.append(f"{key}: future publication year beyond current year {current_year}: {year}")
    return errors


def bibliography_year_counts(entries: dict[str, dict[str, str]]) -> tuple[int, int | None, int | None]:
    years = [
        int(fields["year"])
        for fields in entries.values()
        if YEAR_RE.match(fields.get("year", ""))
    ]
    if not years:
        return 0, None, None
    return len(years), min(years), max(years)


def entry_arxiv_ids(fields: dict[str, str]) -> tuple[str, ...]:
    ids: set[str] = set()
    journal = fields.get("journal", "")
    if match := ARXIV_PREPRINT_RE.search(journal):
        ids.add(match.group(1))
    if match := ARXIV_URL_RE.match(fields.get("url", "")):
        ids.add(match.group(1))
    if fields.get("archiveprefix", "").lower() == "arxiv" and fields.get("eprint"):
        ids.add(fields["eprint"])
    return tuple(sorted(ids))


def arxiv_year_month(arxiv_id: str) -> tuple[int, int] | None:
    match = ARXIV_ID_RE.match(arxiv_id)
    if not match:
        return None
    year = 2000 + int(match.group(1))
    month = int(match.group(2))
    if not 1 <= month <= 12:
        return None
    return year, month


def bibliography_arxiv_errors(entries: dict[str, dict[str, str]], current_year: int, current_month: int) -> list[str]:
    errors: list[str] = []
    for key, fields in entries.items():
        for arxiv_id in entry_arxiv_ids(fields):
            year_month = arxiv_year_month(arxiv_id)
            if year_month is None:
                errors.append(f"{key}: malformed arXiv date prefix: {arxiv_id}")
                continue
            arxiv_year, arxiv_month = year_month
            if (arxiv_year, arxiv_month) > (current_year, current_month):
                errors.append(
                    f"{key}: future arXiv locator beyond current month "
                    f"{current_year:04d}-{current_month:02d}: {arxiv_id}"
                )
            bibliography_year = fields.get("year", "")
            if YEAR_RE.match(bibliography_year) and int(bibliography_year) < arxiv_year:
                errors.append(
                    f"{key}: arXiv locator year {arxiv_year} is later than "
                    f"bibliography year {bibliography_year}: {arxiv_id}"
                )
    return errors


def bibliography_arxiv_counts(entries: dict[str, dict[str, str]]) -> tuple[int, str | None, str | None]:
    months = [
        year_month
        for fields in entries.values()
        for arxiv_id in entry_arxiv_ids(fields)
        if (year_month := arxiv_year_month(arxiv_id)) is not None
    ]
    if not months:
        return 0, None, None
    labels = [f"{year:04d}-{month:02d}" for year, month in months]
    return len(months), min(labels), max(labels)


def is_inside_title_braces(title: str, position: int) -> bool:
    depth = 0
    escaped = False
    for index, char in enumerate(title):
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth = max(0, depth - 1)
        if index == position:
            return depth > 0
    return False


def title_capitalization_errors(entries: dict[str, dict[str, str]]) -> list[str]:
    errors: list[str] = []
    compiled = [
        (label, re.compile(r"(?<![A-Za-z0-9])" + pattern + r"(?![A-Za-z0-9])"))
        for label, pattern in PROTECTED_TITLE_PATTERNS
    ]
    for key, fields in entries.items():
        title = fields.get("title", "")
        unprotected: list[str] = []
        for label, pattern in compiled:
            for match in pattern.finditer(title):
                if not is_inside_title_braces(title, match.start()):
                    unprotected.append(label)
                    break
        if unprotected:
            errors.append(
                f"{key}: protect BibTeX title capitalization for "
                f"{', '.join(sorted(set(unprotected)))}"
            )
    return errors


def main() -> int:
    cites = cited_keys()
    entries, duplicates, parse_errors = bib_entries()
    bib_keys = set(entries)
    today = date.today()
    current_year = today.year
    current_month = today.month

    errors: list[str] = []
    errors.extend(parse_errors)
    missing = sorted(cites - bib_keys)
    if missing:
        errors.append("Missing bibliography keys: " + ", ".join(missing))
    if duplicates:
        errors.append("Duplicate bibliography keys: " + ", ".join(duplicates))

    missing_title = sorted(key for key, fields in entries.items() if "title" not in fields)
    missing_year = sorted(key for key, fields in entries.items() if "year" not in fields)
    missing_creator = sorted(
        key
        for key, fields in entries.items()
        if not ({"author", "editor", "organization", "institution"} & fields.keys())
    )
    missing_locator = sorted(
        key
        for key, fields in entries.items()
        if not ({"doi", "url", "eprint", "journal", "booktitle", "howpublished"} & fields.keys())
    )
    if missing_title:
        errors.append("Entries missing title: " + ", ".join(missing_title))
    if missing_year:
        errors.append("Entries missing year: " + ", ".join(missing_year))
    if missing_creator:
        errors.append("Entries missing author/editor/organization/institution: " + ", ".join(missing_creator))
    if missing_locator:
        errors.append("Entries missing locator field: " + ", ".join(missing_locator))
    errors.extend(bibliography_year_errors(entries, current_year))
    errors.extend(bibliography_arxiv_errors(entries, current_year, current_month))
    errors.extend(bibliography_value_errors(entries))
    errors.extend(title_capitalization_errors(entries))

    unused = sorted(bib_keys - cites)
    year_count, min_year, max_year = bibliography_year_counts(entries)
    arxiv_count, min_arxiv_month, max_arxiv_month = bibliography_arxiv_counts(entries)
    title_count, url_count, doi_count, insecure_exception_count = bibliography_value_counts(entries)
    print(f"cited keys: {len(cites)}")
    print(f"bibliography entries: {len(bib_keys)}")
    print(f"bibliography titles checked: {title_count}")
    print(f"bibliography year fields checked: {year_count}")
    if min_year is not None and max_year is not None:
        print(f"bibliography publication-year range: {min_year}--{max_year}")
    print(f"bibliography arXiv locators checked: {arxiv_count}")
    if min_arxiv_month is not None and max_arxiv_month is not None:
        print(f"bibliography arXiv month range: {min_arxiv_month}--{max_arxiv_month}")
    print(f"bibliography URLs checked: {url_count}")
    print(f"bibliography DOI fields checked: {doi_count}")
    print(f"documented HTTP URL exceptions: {insecure_exception_count}")
    print(f"unused bibliography entries: {len(unused)}")
    if unused:
        errors.append("Unused bibliography keys: " + ", ".join(unused))

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("citation and bibliography metadata checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
