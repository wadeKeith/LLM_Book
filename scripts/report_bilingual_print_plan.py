#!/usr/bin/env python3
"""Report and render source units for a paragraph-level bilingual print edition."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"
ALIGNMENT_MANIFEST = ROOT / "notes" / "bilingual_alignment_manifest.md"

INCLUDE_RE = re.compile(r"\\include\{chapters/([^{}]+)\}")
CHAPTER_RE = re.compile(r"\\chapter\{([^{}]+)\}")
SECTION_RE = re.compile(r"\\section\{([^{}]+)\}")
ITEM_RE = re.compile(
    r"(?:^|\n)\s*\\item(?:\[[^\]]+\])?\s*(.+?)"
    r"(?=(?:\n\s*\\item)|(?:\n\s*\\end\{(?:description|enumerate)\}))",
    re.DOTALL,
)
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'-]*")
ALIGNMENT_STATUS_RE = re.compile(r"^\|\s*([a-z0-9-]+)\s*\|\s*([^|]+?)\s*\|", re.MULTILINE)
CONTRACT_RE = re.compile(
    r"\\paragraph\{Chapter contract\.\}\s*(.+?)(?=\n\s*\n|\\section\{)",
    re.DOTALL,
)
INLINE_COMMAND_RE = re.compile(
    r"\\(?:texttt|emph|textbf|textit|textsc|mathrm|mathbf|mathcal|operatorname)\{([^{}]*)\}"
)
CITE_RE = re.compile(
    r"\\(?:cite|citep|citet|citealp|citeauthor|citeyear)(?:\[[^\]]*\])?\{([^{}]+)\}"
)
REF_RE = re.compile(r"\\(?:ref|pageref|autoref|eqref)\{([^{}]+)\}")
UNRESOLVED_RE = re.compile(r"\b(?:TODO|FIXME|TBD|XXX)\b|\?\?\?|待补|[Cc]itation needed|[Cc]ite needed")
SOURCE_LEAK_RE = re.compile(r"\\(?:cite|ref|index|label|Description)\b")


@dataclass(frozen=True)
class ChapterUnits:
    number: int
    stem: str
    title: str
    abstract: int
    contract: int
    prose: int
    captions: int
    key_terms: int
    exercises: int

    @property
    def total(self) -> int:
        return self.abstract + self.contract + self.prose + self.captions + self.key_terms + self.exercises


@dataclass(frozen=True)
class BackMatterUnits:
    name: str
    units: int


@dataclass(frozen=True)
class SourceUnit:
    unit_id: str
    scope: str
    kind: str
    source: str


@dataclass(frozen=True)
class AlignmentRecord:
    unit_id: str
    status: str
    proofing: str
    chinese: str


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


def remove_envs(text: str, envs: list[str]) -> str:
    for env in envs:
        text = re.sub(
            rf"\\begin\{{{re.escape(env)}\}}.*?\\end\{{{re.escape(env)}\}}",
            "\n\n",
            text,
            flags=re.DOTALL,
        )
    return text


def braced_command_argument(text: str, command: str) -> str:
    matches = braced_command_arguments(text, command)
    return matches[0] if matches else ""


def braced_command_arguments(text: str, command: str) -> list[str]:
    marker = rf"\{command}"
    arguments: list[str] = []
    search_start = 0

    while True:
        start = text.find(marker, search_start)
        if start == -1:
            break

        brace_start = text.find("{", start + len(marker))
        if brace_start == -1:
            break

        depth = 0
        end = -1
        for index in range(brace_start, len(text)):
            char = text[index]
            if char == "{" and (index == 0 or text[index - 1] != "\\"):
                depth += 1
            elif char == "}" and (index == 0 or text[index - 1] != "\\"):
                depth -= 1
                if depth == 0:
                    end = index
                    break

        if end == -1:
            break
        arguments.append(text[brace_start + 1 : end].strip())
        search_start = end + 1

    return arguments


def remove_braced_commands(text: str, commands: tuple[str, ...]) -> str:
    for command in commands:
        marker = rf"\{command}"
        search_start = 0
        while True:
            start = text.find(marker, search_start)
            if start == -1:
                break

            brace_start = text.find("{", start + len(marker))
            if brace_start == -1:
                search_start = start + len(marker)
                continue

            depth = 0
            end = -1
            for index in range(brace_start, len(text)):
                char = text[index]
                if char == "{" and (index == 0 or text[index - 1] != "\\"):
                    depth += 1
                elif char == "}" and (index == 0 or text[index - 1] != "\\"):
                    depth -= 1
                    if depth == 0:
                        end = index
                        break

            if end == -1:
                break
            text = text[:start] + " " + text[end + 1 :]
            search_start = start + 1
    return text


def chapter_contract(text: str) -> str:
    match = CONTRACT_RE.search(text)
    return match.group(1).strip() if match else ""


def plain_text(text: str) -> str:
    text = re.sub(r"\\(?:index|label|Description)\{[^{}]*\}", " ", text)
    text = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?", " ", text)
    return text.replace("``", " ").replace("''", " ")


def word_count(text: str) -> int:
    return len(WORD_RE.findall(plain_text(text)))


def prose_paragraphs(text: str) -> list[str]:
    text = remove_envs(
        text,
        [
            "equation",
            "equation*",
            "align",
            "align*",
            "table",
            "figure",
            "tikzpicture",
            "description",
            "enumerate",
            "center",
            "tabular",
        ],
    )
    text = re.sub(r"\\(?:chapter|section|subsection|subsubsection|paragraph)\*?\{[^{}]+\}", "\n\n", text)
    text = re.sub(r"\\index\{(?:[^{}]|\{[^{}]*\})*\}", "\n\n", text)
    text = re.sub(r"\\(?:addcontentsline|phantomsection|label)\{[^{}]*\}(?:\{[^{}]*\})?(?:\{[^{}]*\})?", "\n\n", text)
    text = re.sub(r"\\phantomsection\b", "\n\n", text)

    paragraphs: list[str] = []
    for raw in re.split(r"\n\s*\n", text):
        candidate = raw.strip()
        if not candidate or candidate.startswith("\\"):
            continue
        if word_count(candidate) >= 12:
            paragraphs.append(candidate)
    return paragraphs


def section_block(text: str, title: str) -> str:
    match = re.search(rf"\\section\{{{re.escape(title)}\}}", text)
    if not match:
        return ""
    next_section = SECTION_RE.search(text, match.end())
    return text[match.end() : next_section.start() if next_section else len(text)]


def english_chapter_stems() -> list[str]:
    root_text = strip_tex_comments((BOOK_DIR / "book.tex").read_text(encoding="utf-8"))
    return INCLUDE_RE.findall(root_text)


def chapter_units() -> list[ChapterUnits]:
    rows: list[ChapterUnits] = []
    for number, stem in enumerate(english_chapter_stems(), start=1):
        path = CHAPTER_DIR / f"{stem}.tex"
        text = strip_tex_comments(path.read_text(encoding="utf-8"))
        title_match = CHAPTER_RE.search(text)
        title = title_match.group(1) if title_match else f"<missing title: {stem}>"
        key_terms_start = text.find(r"\section{Key Terms}")
        first_section = SECTION_RE.search(text)
        body_start = first_section.start() if first_section else 0
        body_end = key_terms_start if key_terms_start != -1 else len(text)
        body = text[body_start:body_end]
        abstract_text = braced_command_argument(text, "abstract")
        contract_text = chapter_contract(text)

        rows.append(
            ChapterUnits(
                number=number,
                stem=stem,
                title=title,
                abstract=1 if abstract_text else 0,
                contract=1 if contract_text else 0,
                prose=len(prose_paragraphs(body)),
                captions=len(braced_command_arguments(text, "caption")),
                key_terms=len(ITEM_RE.findall(section_block(text, "Key Terms"))),
                exercises=len(ITEM_RE.findall(section_block(text, "Exercises"))),
            )
        )
    return rows


def chapter_source_units() -> list[SourceUnit]:
    units: list[SourceUnit] = []
    for number, stem in enumerate(english_chapter_stems(), start=1):
        path = CHAPTER_DIR / f"{stem}.tex"
        text = strip_tex_comments(path.read_text(encoding="utf-8"))
        scope = f"ch{number:02d}"
        title_match = CHAPTER_RE.search(text)
        title = title_match.group(1) if title_match else stem
        abstract_text = braced_command_argument(text, "abstract")
        contract_text = chapter_contract(text)

        if abstract_text:
            units.append(SourceUnit(f"{scope}-abstract", title, "abstract", abstract_text))
        if contract_text:
            units.append(SourceUnit(f"{scope}-contract", title, "contract", contract_text))

        key_terms_start = text.find(r"\section{Key Terms}")
        first_section = SECTION_RE.search(text)
        body_start = first_section.start() if first_section else 0
        body_end = key_terms_start if key_terms_start != -1 else len(text)
        for index, paragraph in enumerate(prose_paragraphs(text[body_start:body_end]), start=1):
            units.append(SourceUnit(f"{scope}-prose-{index:03d}", title, "prose", paragraph))

        for index, caption in enumerate(braced_command_arguments(text, "caption"), start=1):
            units.append(SourceUnit(f"{scope}-caption-{index:03d}", title, "caption", caption))

        for index, item in enumerate(ITEM_RE.findall(section_block(text, "Key Terms")), start=1):
            units.append(SourceUnit(f"{scope}-key-term-{index:03d}", title, "key-term", item))

        for index, item in enumerate(ITEM_RE.findall(section_block(text, "Exercises")), start=1):
            units.append(SourceUnit(f"{scope}-exercise-{index:03d}", title, "exercise", item))
    return units


def back_matter_units() -> list[BackMatterUnits]:
    prose_sources = [
        ("Preface", BOOK_DIR / "preface.tex"),
        ("Responsible use", BOOK_DIR / "ethics.tex"),
        ("Appendix prose", BOOK_DIR / "appendix.tex"),
    ]
    item_sources = [
        ("Acronym entries", BOOK_DIR / "acronym.tex"),
        ("Glossary entries", BOOK_DIR / "glossary.tex"),
    ]

    rows = [
        BackMatterUnits(name, len(prose_paragraphs(strip_tex_comments(path.read_text(encoding="utf-8")))))
        for name, path in prose_sources
    ]
    rows.extend(
        BackMatterUnits(name, len(ITEM_RE.findall(strip_tex_comments(path.read_text(encoding="utf-8")))))
        for name, path in item_sources
    )
    return rows


def back_matter_source_units() -> list[SourceUnit]:
    units: list[SourceUnit] = []
    prose_sources = [
        ("front-preface", "Preface", BOOK_DIR / "preface.tex"),
        ("front-responsible-use", "Responsible use", BOOK_DIR / "ethics.tex"),
        ("back-appendix", "Appendix prose", BOOK_DIR / "appendix.tex"),
    ]
    item_sources = [
        ("back-acronym", "Acronym entries", BOOK_DIR / "acronym.tex"),
        ("back-glossary", "Glossary entries", BOOK_DIR / "glossary.tex"),
    ]

    for prefix, scope, path in prose_sources:
        text = strip_tex_comments(path.read_text(encoding="utf-8"))
        for index, paragraph in enumerate(prose_paragraphs(text), start=1):
            units.append(SourceUnit(f"{prefix}-prose-{index:03d}", scope, "prose", paragraph))

    for prefix, scope, path in item_sources:
        text = strip_tex_comments(path.read_text(encoding="utf-8"))
        for index, item in enumerate(ITEM_RE.findall(text), start=1):
            units.append(SourceUnit(f"{prefix}-{index:03d}", scope, "entry", item))
    return units


def all_source_units() -> list[SourceUnit]:
    return chapter_source_units() + back_matter_source_units()


def alignment_counts() -> tuple[int, int]:
    if not ALIGNMENT_MANIFEST.exists():
        return 0, 0
    text = ALIGNMENT_MANIFEST.read_text(encoding="utf-8")
    aligned = 0
    proofed = 0
    for unit_id, status in ALIGNMENT_STATUS_RE.findall(text):
        if not unit_id.startswith(("ch", "front-", "back-")):
            continue
        normalized = status.strip()
        if normalized in {"Aligned", "Proofed"}:
            aligned += 1
        if normalized == "Proofed":
            proofed += 1
    return aligned, proofed


def markdown_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def alignment_records() -> dict[str, AlignmentRecord]:
    if not ALIGNMENT_MANIFEST.exists():
        return {}

    records: dict[str, AlignmentRecord] = {}
    text = ALIGNMENT_MANIFEST.read_text(encoding="utf-8")
    for cells in markdown_rows(text):
        if len(cells) != 4 or cells[0] == "Unit ID":
            continue
        unit_id, status, proofing, chinese = cells
        if not unit_id.startswith(("ch", "front-", "back-")):
            continue
        records[unit_id] = AlignmentRecord(unit_id, status, proofing, chinese)
    return records


MACRO_REPLACEMENTS = (
    (r"\transformers", "Transformers"),
    (r"\transformer", "Transformer"),
    (r"\Transformer", "Transformer"),
    (r"\llms", "LLMs"),
    (r"\llm", "LLM"),
    (r"\rlhf", "RLHF"),
    (r"\rag", "RAG"),
)


def display_text(text: str) -> str:
    text = text.strip()
    text = remove_braced_commands(text, ("index", "label", "Description"))
    text = CITE_RE.sub(r"[cite: \1]", text)
    text = REF_RE.sub(r"[ref: \1]", text)

    for macro, replacement in MACRO_REPLACEMENTS:
        text = re.sub(re.escape(macro) + r"(?![A-Za-z])", replacement, text)

    for _ in range(8):
        updated = INLINE_COMMAND_RE.sub(r"\1", text)
        if updated == text:
            break
        text = updated

    text = re.sub(r"\\(?:begin|end)\{[^{}]+\}", " ", text)
    text = text.replace(r"\%", "%")
    text = text.replace(r"\&", "&")
    text = text.replace(r"\_", "_")
    text = text.replace(r"\#", "#")
    text = text.replace(r"\{", "{")
    text = text.replace(r"\}", "}")
    text = text.replace("``", '"').replace("''", '"')
    text = text.replace("~", " ")
    return re.sub(r"\s+", " ", text).strip()


def latex_escape(text: str) -> str:
    escaped: list[str] = []
    for char in text:
        if char == "\\":
            escaped.append(r"\textbackslash{}")
        elif char == "{":
            escaped.append(r"\{")
        elif char == "}":
            escaped.append(r"\}")
        elif char == "&":
            escaped.append(r"\&")
        elif char == "%":
            escaped.append(r"\%")
        elif char == "$":
            escaped.append(r"\$")
        elif char == "#":
            escaped.append(r"\#")
        elif char == "_":
            escaped.append(r"\_")
        elif char == "^":
            escaped.append(r"\textasciicircum{}")
        elif char == "~":
            escaped.append(r"\textasciitilde{}")
        else:
            escaped.append(char)
    return "".join(escaped)


def tex_text(text: str) -> str:
    return latex_escape(display_text(text))


def render_bilingual_tex(output_path: Path) -> None:
    units = all_source_units()
    records = alignment_records()
    missing = [unit.unit_id for unit in units if unit.unit_id not in records]
    if missing:
        raise RuntimeError(f"missing alignment records for {len(missing)} units; first missing unit: {missing[0]}")

    aligned = sum(1 for unit in units if records[unit.unit_id].status in {"Aligned", "Proofed"})
    proofed = sum(1 for unit in units if records[unit.unit_id].status == "Proofed")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        r"\documentclass[UTF8,zihao=-4,openany]{ctexbook}",
        r"\usepackage{geometry}",
        r"\usepackage{array}",
        r"\usepackage{xcolor}",
        r"\usepackage[hidelinks,pdfpagelabels,plainpages=false,hypertexnames=false]{hyperref}",
        r"\geometry{letterpaper,margin=0.85in}",
        r"\setlength{\parindent}{0pt}",
        r"\setlength{\parskip}{0.45em}",
        r"\definecolor{UnitRule}{gray}{0.70}",
        r"\definecolor{UnitShade}{gray}{0.96}",
        r"\newcommand{\UnitMeta}[3]{\par\noindent\colorbox{UnitShade}{\parbox{\dimexpr\linewidth-2\fboxsep\relax}{\texttt{#1}\hfill #2\hfill #3}}\par}",
        r"\newcommand{\LangLabel}[1]{\par\noindent\textbf{#1}\par}",
        r"\newcommand{\UnitRuleLine}{\par\noindent\textcolor{UnitRule}{\rule{\linewidth}{0.4pt}}\par}",
        r"\hypersetup{pdftitle={Bilingual Print Proofing Draft},pdfauthor={Cheng Yin},pdfsubject={Paragraph-level bilingual proofing draft}}",
        r"\begin{document}",
        r"\frontmatter",
        r"\chapter*{Bilingual Print Proofing Draft}",
        rf"This generated proofing draft contains {len(units)} source units, {aligned} source-level aligned units, and {proofed} proofed units.",
        r"It is generated from the current English source inventory and \texttt{notes/bilingual\_alignment\_manifest.md}. It is a paragraph-level proofing aid, not a release-ready replacement for the English or Chinese monograph roots.",
        r"\tableofcontents",
        r"\mainmatter",
    ]

    current_group = ""
    for unit in units:
        group = unit.unit_id[:4] if unit.unit_id.startswith("ch") else unit.scope
        if group != current_group:
            current_group = group
            if unit.unit_id.startswith("ch"):
                chapter_number = int(unit.unit_id[2:4])
                title = f"Chapter {chapter_number:02d}: {unit.scope}"
            else:
                title = unit.scope
            lines.extend(["", rf"\chapter{{{tex_text(title)}}}"])

        record = records[unit.unit_id]
        lines.extend(
            [
                "",
                rf"\section*{{{tex_text(unit.unit_id)}}}",
                rf"\addcontentsline{{toc}}{{section}}{{{tex_text(unit.unit_id)}}}",
                rf"\UnitMeta{{{tex_text(unit.unit_id)}}}{{{tex_text(unit.kind)}}}{{{tex_text(record.status + '; ' + record.proofing)}}}",
                r"\LangLabel{English source unit}",
                tex_text(unit.source),
                r"\LangLabel{Chinese counterpart}",
                tex_text(record.chinese),
                r"\UnitRuleLine",
            ]
        )

    lines.append(r"\end{document}")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_pdf(tex_path: Path, latexmk: str) -> None:
    result = subprocess.run(
        [latexmk, "-xelatex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
        cwd=tex_path.parent,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"latexmk failed for {tex_path}")


def command_output(command: list[str]) -> str:
    result = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no diagnostic output"
        raise RuntimeError(f"{command[0]} failed: {detail}")
    return result.stdout


def pdf_page_count(pdf_path: Path, pdfinfo: str) -> int:
    output = command_output([pdfinfo, str(pdf_path)])
    for line in output.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise RuntimeError(f"could not parse page count from {pdf_path}")


def rendered_pdf_text(pdf_path: Path, pdftotext: str) -> str:
    return command_output([pdftotext, "-layout", str(pdf_path), "-"])


def check_bilingual_artifact(tex_path: Path, pdfinfo: str, pdftotext: str) -> None:
    pdf_path = tex_path.with_suffix(".pdf")
    if not tex_path.exists():
        raise RuntimeError(f"missing bilingual print TeX artifact: {tex_path}")
    if not pdf_path.exists():
        raise RuntimeError(f"missing bilingual print PDF artifact: {pdf_path}")

    units = all_source_units()
    records = alignment_records()
    errors: list[str] = []
    if len(records) != len(units):
        errors.append(f"manifest rows {len(records)} do not match source units {len(units)}")

    aligned = sum(1 for unit in units if records.get(unit.unit_id) and records[unit.unit_id].status in {"Aligned", "Proofed"})
    proofed = sum(1 for unit in units if records.get(unit.unit_id) and records[unit.unit_id].status == "Proofed")
    if aligned != len(units):
        errors.append(f"aligned units {aligned} do not match source units {len(units)}")

    tex_text_value = tex_path.read_text(encoding="utf-8")
    pages = pdf_page_count(pdf_path, pdfinfo)
    rendered_text = rendered_pdf_text(pdf_path, pdftotext)
    fingerprint = hashlib.sha256(rendered_text.encode("utf-8")).hexdigest()

    if pages < 1:
        errors.append("rendered bilingual print PDF has no pages")
    if "Bilingual Print Proofing Draft" not in rendered_text:
        errors.append("rendered bilingual print PDF is missing its title marker")

    missing_ids = [unit.unit_id for unit in units if unit.unit_id not in rendered_text]
    if missing_ids:
        errors.append(f"rendered bilingual print PDF is missing {len(missing_ids)} unit ids; first missing unit: {missing_ids[0]}")

    for label, text in (("TeX artifact", tex_text_value), ("rendered text", rendered_text)):
        if "chapter abstract" in text or "Chapter contract paragraph" in text:
            errors.append(f"{label} still contains old abstract/contract placeholder text")
        if UNRESOLVED_RE.search(text):
            errors.append(f"{label} contains unresolved editorial markers")
        if SOURCE_LEAK_RE.search(text):
            errors.append(f"{label} contains raw TeX source commands")

    print(f"bilingual print artifact source units: {len(units)}")
    print(f"bilingual print artifact aligned units: {aligned}")
    print(f"bilingual print artifact proofed units: {proofed}")
    print(f"bilingual print artifact pages: {pages}")
    print(f"bilingual print artifact unit ids in rendered text: {len(units) - len(missing_ids)} / {len(units)}")
    print(f"bilingual print artifact text SHA-256: {fingerprint}")
    print(f"bilingual print artifact errors: {len(errors)}")

    if errors:
        raise RuntimeError("\n".join(errors))

    print("bilingual print artifact checks passed")


def print_report() -> None:
    chapter_rows = chapter_units()
    back_rows = back_matter_units()
    chapter_total = sum(row.total for row in chapter_rows)
    front_back_total = sum(row.units for row in back_rows)
    total = chapter_total + front_back_total
    aligned_units, proofed_units = alignment_counts()

    print(f"bilingual print chapter source units: {chapter_total}")
    print(f"bilingual print front/back source units: {front_back_total}")
    print(f"bilingual print total source units: {total}")
    print(f"bilingual print explicit aligned units: {aligned_units}")
    print(f"bilingual print proofed units: {proofed_units}")
    print(f"bilingual print open source units: {total - aligned_units}")
    print()
    print("| Chapter | English title | Abstract | Contract | Prose | Captions | Key terms | Exercises | Units |")
    print("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in chapter_rows:
        print(
            f"| {row.number:02d} | {row.title} | {row.abstract} | {row.contract} | {row.prose} | "
            f"{row.captions} | {row.key_terms} | {row.exercises} | {row.total} |"
        )
    print()
    print("| Front/back matter | Units |")
    print("| --- | ---: |")
    for row in back_rows:
        print(f"| {row.name} | {row.units} |")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--render-tex",
        type=Path,
        help="write a paragraph-level bilingual proofing TeX draft to this path",
    )
    parser.add_argument(
        "--build-pdf",
        action="store_true",
        help="build the rendered TeX draft with latexmk -xelatex",
    )
    parser.add_argument(
        "--check-artifact",
        action="store_true",
        help="check the rendered bilingual proofing TeX/PDF artifacts",
    )
    parser.add_argument(
        "--latexmk",
        default="latexmk",
        help="latexmk executable to use with --build-pdf",
    )
    parser.add_argument(
        "--pdfinfo",
        default="pdfinfo",
        help="pdfinfo executable to use with --check-artifact",
    )
    parser.add_argument(
        "--pdftotext",
        default="pdftotext",
        help="pdftotext executable to use with --check-artifact",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.render_tex:
        try:
            render_bilingual_tex(args.render_tex)
            print(f"bilingual print TeX proofing draft: {args.render_tex}")
            if args.build_pdf:
                build_pdf(args.render_tex, args.latexmk)
                print(f"bilingual print PDF proofing draft: {args.render_tex.with_suffix('.pdf')}")
            if args.check_artifact:
                check_bilingual_artifact(args.render_tex, args.pdfinfo, args.pdftotext)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        return 0

    if args.check_artifact:
        print("--check-artifact requires --render-tex", file=sys.stderr)
        return 2

    print_report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
