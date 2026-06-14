#!/usr/bin/env python3
"""Check bilingual reproducibility-record fields in the appendices."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = ROOT / "book"
EN_APPENDIX = BOOK_DIR / "appendix.tex"
ZH_ROOT = BOOK_DIR / "book_zh.tex"


@dataclass(frozen=True)
class FieldRequirement:
    label: str
    markers: tuple[str, ...]


EN_REQUIREMENTS = (
    FieldRequirement("code version", ("code version",)),
    FieldRequirement("data version", ("data version",)),
    FieldRequirement("license or provenance", ("license", "provenance")),
    FieldRequirement("tokenizer", ("tokenizer",)),
    FieldRequirement("chat template", ("chat template",)),
    FieldRequirement("model configuration", ("model configuration",)),
    FieldRequirement("random seed policy", ("random seed",)),
    FieldRequirement("optimizer", ("optimizer",)),
    FieldRequirement("learning rate", ("learning rate",)),
    FieldRequirement("batch size", ("batch size",)),
    FieldRequirement("precision", ("precision",)),
    FieldRequirement("hardware", ("hardware",)),
    FieldRequirement("expected runtime", ("expected runtime",)),
    FieldRequirement("checkpoint", ("checkpoint",)),
    FieldRequirement("validation", ("validation",)),
    FieldRequirement("primary metric", ("primary metric",)),
    FieldRequirement("failure modes", ("failure modes", "failed examples")),
    FieldRequirement("conclusion", ("conclusion",)),
)

ZH_REQUIREMENTS = (
    FieldRequirement("code version", ("代码版本",)),
    FieldRequirement("data version", ("数据版本",)),
    FieldRequirement("license or provenance", ("数据许可证", "来源说明")),
    FieldRequirement("tokenizer", ("tokenizer",)),
    FieldRequirement("chat template", ("聊天模板",)),
    FieldRequirement("model configuration", ("模型配置",)),
    FieldRequirement("random seed policy", ("随机种子",)),
    FieldRequirement("optimizer", ("优化器",)),
    FieldRequirement("learning rate", ("学习率",)),
    FieldRequirement("batch size", ("batch",)),
    FieldRequirement("precision", ("精度",)),
    FieldRequirement("hardware", ("硬件",)),
    FieldRequirement("expected runtime", ("预计运行时间",)),
    FieldRequirement("checkpoint", ("checkpoint",)),
    FieldRequirement("validation", ("验证集",)),
    FieldRequirement("primary metric", ("主要指标",)),
    FieldRequirement("failure modes", ("失败样例", "失败模式")),
    FieldRequirement("conclusion", ("结论",)),
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


def section_body(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"\\section\{{{re.escape(heading)}\}}(.*?)(?=\\section\{{|\\chapter\{{|\\backmatter|\\end\{{document\}}|\Z)",
        re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1) if match else ""


def normalize_english(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\\[a-z]+\*?(?:\[[^\]]*\])?", " ", text)
    text = re.sub(r"[{}$~]", " ", text)
    return re.sub(r"\s+", " ", text)


def check_fields(
    body: str,
    requirements: tuple[FieldRequirement, ...],
    rel: str,
    errors: list[str],
    *,
    normalize: bool = False,
) -> int:
    haystack = normalize_english(body) if normalize else body
    found = 0
    for requirement in requirements:
        markers = tuple(marker.lower() for marker in requirement.markers) if normalize else requirement.markers
        if any(marker in haystack for marker in markers):
            found += 1
        else:
            errors.append(f"{rel}: Experiment Records section is missing {requirement.label}")
    return found


def main() -> int:
    errors: list[str] = []
    en_text = strip_tex_comments(EN_APPENDIX.read_text(encoding="utf-8"))
    zh_text = strip_tex_comments(ZH_ROOT.read_text(encoding="utf-8"))

    en_body = section_body(en_text, "Experiment Records")
    zh_body = section_body(zh_text, "实验记录清单")

    if not en_body:
        errors.append("book/appendix.tex: missing Experiment Records section")
    if not zh_body:
        errors.append("book/book_zh.tex: missing 实验记录清单 section")

    if r"\label{tab:run-card-template}" not in en_body:
        errors.append("book/appendix.tex: Experiment Records section is missing tab:run-card-template")
    if r"Table~\ref{tab:run-card-template}" not in en_body:
        errors.append("book/appendix.tex: Experiment Records section does not reference tab:run-card-template")

    en_found = check_fields(en_body, EN_REQUIREMENTS, "book/appendix.tex", errors, normalize=True) if en_body else 0
    zh_found = check_fields(zh_body, ZH_REQUIREMENTS, "book/book_zh.tex", errors) if zh_body else 0

    print(f"English reproducibility fields checked: {en_found} / {len(EN_REQUIREMENTS)}")
    print(f"Chinese reproducibility fields checked: {zh_found} / {len(ZH_REQUIREMENTS)}")
    print(f"reproducibility record errors: {len(errors)}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("reproducibility record checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
