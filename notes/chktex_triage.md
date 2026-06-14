# ChkTeX Triage

Date: 2026-05-25

## Scope

This triage covers the English controlling manuscript:

```bash
chktex -q -I0 -v0 book/book.tex book/preface.tex book/ethics.tex book/acronym.tex book/glossary.tex book/appendix.tex book/chapters/*.tex
```

The Chinese readable edition is excluded from this automated pass because mixed Chinese prose, English technical terms, `ctexbook`, and XeLaTeX font handling make `chktex` output low-signal there. Chinese layout quality is tracked through XeLaTeX logs and rendered PDF inspection.

## Current Distribution After Fixes

```text
1     45   Command terminated with space.
2     278  Non-breaking space (`~') should have been used.
12    4    Interword spacing (`\ ') should perhaps be used.
13    17   Intersentence spacing (`\@') should perhaps be used.
24    366  Delete this space to maintain correct pagereferences.
38    9    You should not use punctuation in front of quotes.
44    0    User Regex: use booktabs rules.
```

## Disposition

- `1`: Do not gate. Most hits are intentional `xspace` macros such as `\llms` and `\transformers`.
- `2`: Review opportunistically. Non-breaking spaces after citations and references improve typography but are too numerous for a hard gate at this stage.
- `3`: Gate. The focused pass now has 0 remaining mathematical grouping warnings.
- `12`: Do not gate. This is a sentence-spacing preference around abbreviations and macros.
- `13`: Do not gate. This is a sentence-spacing preference around abbreviations and macros.
- `24`: Do not gate. The index is intentionally expanded with standalone `\index{...}` commands. `makeindex` accepts the entries with 0 rejected and 0 warnings, and rendered index pages have been inspected.
- `36`: Gate. The focused pass now has 0 remaining code-fragment spacing warnings.
- `38`: Do not gate. The house style now follows American quote punctuation in ordinary prose, so commas and periods stay inside closing quotation marks. See `notes/style_guide.md`.
- `44`: Gate at zero. Tables already use `booktabs`, and the current manuscript has 0 hits, so future bundled-regex table-rule warnings should fail both the budget and focused checks.

## Repeatable Review Command

Use the budget and focused Make targets for repeatable review:

```bash
make chktex-budget-check
make chktex-focused-check
make chktex-review
```

`make chktex-budget-check` runs full ChkTeX and fails if any untriaged warning class appears or if a triaged class exceeds its current budget. The current budgets are `1:45`, `2:278`, `12:4`, `13:17`, `24:366`, `38:9`, and `44:0`. The focused targets mute the positive-budget high-volume non-gating classes (`1`, `2`, `12`, `13`, `24`, and `38`) while leaving warning `44` as a zero-tolerance focused check. `make chktex-budget-check` and `make chktex-focused-check` are part of `make manuscript-audit`; `make chktex-review` prints the focused warning set without failing, which is useful during editing.

The latest `make chktex-budget-check`, `make chktex-focused-check`, and `make chktex-review` runs produce no budget or focused-warning failures after the house-style mutes.

The latest `make chktex-triage-check` run confirmed 7 ChkTeX triaged warning classes and 719 current ChkTeX warning hits: `1:45/45`, `2:278/278`, `12:4/4`, `13:17/17`, `24:366/366`, `38:9/9`, and `44:0/0`.
