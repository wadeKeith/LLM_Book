BOOK_DIR := book
SCRIPTS_DIR := scripts
LATEXMK := latexmk
RG := rg
PDFINFO := pdfinfo
PDFFONTS := pdffonts
CHKTEX := chktex
PDFTOPPM := pdftoppm
PDFTOTEXT := pdftotext
PYTHON ?= python3
GIT ?= git
LATEXMK_RUN := $(PYTHON) $(SCRIPTS_DIR)/run_latexmk_locked.py $(BOOK_DIR) $(LATEXMK)

LOG_HARD_CHECK := undefined|Citation .* undefined|There were undefined references|LaTeX Error|Package .* Error|Fatal error|Font Warning|Warning--
LOG_LAYOUT_CHECK := Overfull \\\\hbox|Package pgf Warning|Returning node center|pdfTeX warning|xdvipdfmx:warning|rerunfilecheck Warning|has been referenced but does not exist|duplicate ignored|destination with the same identifier|Object @page\.[0-9]+ already defined
CHKTEX_FILES := book.tex preface.tex ethics.tex acronym.tex glossary.tex appendix.tex chapters/*.tex
CHKTEX_REVIEW_MUTES := -n1 -n2 -n12 -n13 -n24 -n38
PLACEHOLDER_CHECK := TODO|FIXME|TBD|XXX|\?\?\?|待补|lorem|dummy|citation needed|cite needed
VISUAL_AUDIT_DIR ?= /tmp/llm_book_visual_audit
VISUAL_AUDIT_DPI ?= 130
VISUAL_AUDIT_EXPECTED_PNGS ?= 360
BILINGUAL_PRINT_DIR ?= /tmp/llm_book_bilingual_print
BILINGUAL_PRINT_TEX := $(BILINGUAL_PRINT_DIR)/book_bilingual_print.tex

.PHONY: all english zh check toolchain-check repo-hygiene-check release-inventory-check source-inventory-check audit-script-check makefile-consistency-check citation-check structure-check frontmatter-quality-check abstract-quality-check chapter-contract-check heading-quality-check toc-review-check coverage-check edition-alignment-check bilingual-coverage-check bilingual-alignment-check bilingual-print-artifact-check bilingual-print-proofing-check frontier-coverage-check crossref-check table-quality-check caption-quality-check figure-description-check snmono-policy-check provenance-check term-check backmatter-quality-check prose-quality-check chinese-prose-quality-check duplicate-prose-check paragraph-length-check exercise-quality-check reproducibility-check index-check reviewer-check pdf-metadata-check pdf-font-check pdf-text-check pdf-reference-check pdf-outline-check pdf-page-integrity-check visual-smoke-check visual-full-check visual-audit-plan-check proofing-plan-check documentation-check placeholder-check chktex-triage-check chktex-budget-check chktex-focused-check log-quality-check manuscript-audit release-candidate bilingual-print-plan chktex-review visual-audit clean clean-check

all: english zh check

manuscript-audit: toolchain-check repo-hygiene-check release-inventory-check source-inventory-check audit-script-check makefile-consistency-check citation-check structure-check frontmatter-quality-check abstract-quality-check chapter-contract-check heading-quality-check toc-review-check coverage-check edition-alignment-check bilingual-coverage-check bilingual-alignment-check bilingual-print-artifact-check bilingual-print-proofing-check frontier-coverage-check crossref-check table-quality-check caption-quality-check figure-description-check snmono-policy-check provenance-check term-check backmatter-quality-check prose-quality-check chinese-prose-quality-check duplicate-prose-check paragraph-length-check exercise-quality-check reproducibility-check placeholder-check chktex-triage-check chktex-budget-check chktex-focused-check log-quality-check index-check reviewer-check pdf-metadata-check pdf-font-check pdf-text-check pdf-reference-check pdf-outline-check pdf-page-integrity-check visual-smoke-check visual-full-check visual-audit-plan-check proofing-plan-check documentation-check

release-candidate: manuscript-audit
	$(MAKE) clean
	$(MAKE) clean-check
	$(GIT) diff --check
	$(MAKE) release-inventory-check

bilingual-print-plan:
	$(PYTHON) scripts/report_bilingual_print_plan.py

bilingual-alignment-check:
	$(PYTHON) scripts/check_bilingual_alignment_manifest.py

bilingual-print-artifact-check:
	rm -rf "$(BILINGUAL_PRINT_DIR)"
	$(PYTHON) scripts/report_bilingual_print_plan.py --render-tex "$(BILINGUAL_PRINT_TEX)" --build-pdf --check-artifact --latexmk "$(LATEXMK)" --pdfinfo "$(PDFINFO)" --pdftotext "$(PDFTOTEXT)"

bilingual-print-proofing-check: bilingual-print-artifact-check
	BILINGUAL_PRINT_TEX="$(BILINGUAL_PRINT_TEX)" PDFINFO="$(PDFINFO)" PDFTOTEXT="$(PDFTOTEXT)" $(PYTHON) scripts/check_bilingual_print_proofing.py

english:
	$(LATEXMK_RUN) -pdf -interaction=nonstopmode -halt-on-error book.tex

zh:
	$(LATEXMK_RUN) -xelatex -interaction=nonstopmode -halt-on-error book_zh.tex

check: english zh
	cd $(BOOK_DIR) && if $(RG) -n "$(LOG_HARD_CHECK)" book.log book_zh.log; then exit 1; fi
	cd $(BOOK_DIR) && if $(RG) -n "$(LOG_LAYOUT_CHECK)" book.log book_zh.log; then exit 1; fi
	PDFINFO="$(PDFINFO)" $(PYTHON) scripts/check_pdf_metadata.py

toolchain-check:
	LATEXMK="$(LATEXMK)" RG="$(RG)" PDFINFO="$(PDFINFO)" PDFFONTS="$(PDFFONTS)" CHKTEX="$(CHKTEX)" PDFTOPPM="$(PDFTOPPM)" PDFTOTEXT="$(PDFTOTEXT)" $(PYTHON) scripts/check_toolchain.py

repo-hygiene-check:
	$(PYTHON) scripts/check_repo_hygiene.py

release-inventory-check:
	$(PYTHON) scripts/check_release_inventory.py

source-inventory-check:
	$(PYTHON) scripts/check_source_inventory.py

audit-script-check:
	$(PYTHON) scripts/check_audit_scripts.py

makefile-consistency-check:
	$(PYTHON) scripts/check_makefile_consistency.py

citation-check:
	$(PYTHON) scripts/check_citations.py

structure-check:
	$(PYTHON) scripts/check_manuscript_structure.py

frontmatter-quality-check:
	$(PYTHON) scripts/check_frontmatter_quality.py

abstract-quality-check:
	$(PYTHON) scripts/check_abstract_quality.py

chapter-contract-check:
	$(PYTHON) scripts/check_chapter_contracts.py

heading-quality-check:
	$(PYTHON) scripts/check_heading_quality.py

toc-review-check:
	$(PYTHON) scripts/check_toc_review.py

coverage-check:
	$(PYTHON) scripts/check_chapter_coverage.py

edition-alignment-check:
	$(PYTHON) scripts/check_edition_alignment.py

bilingual-coverage-check:
	$(PYTHON) scripts/check_bilingual_coverage.py

frontier-coverage-check:
	$(PYTHON) scripts/check_frontier_coverage.py

crossref-check:
	$(PYTHON) scripts/check_crossrefs.py

table-quality-check:
	$(PYTHON) scripts/check_table_quality.py

caption-quality-check:
	$(PYTHON) scripts/check_caption_quality.py

figure-description-check: english
	$(PYTHON) scripts/check_figure_descriptions.py

snmono-policy-check:
	$(PYTHON) scripts/check_snmono_policy.py

provenance-check:
	$(PYTHON) scripts/check_provenance_boundaries.py

term-check:
	$(PYTHON) scripts/check_term_consistency.py

backmatter-quality-check:
	$(PYTHON) scripts/check_backmatter_quality.py

prose-quality-check:
	$(PYTHON) scripts/check_prose_quality.py

chinese-prose-quality-check:
	$(PYTHON) scripts/check_chinese_prose_quality.py

duplicate-prose-check:
	$(PYTHON) scripts/check_duplicate_prose.py

paragraph-length-check:
	$(PYTHON) scripts/check_paragraph_length.py

exercise-quality-check:
	$(PYTHON) scripts/check_exercise_quality.py

reproducibility-check:
	$(PYTHON) scripts/check_reproducibility_records.py

index-check: all
	$(PYTHON) scripts/check_index_quality.py
	PDFTOTEXT="$(PDFTOTEXT)" $(PYTHON) scripts/check_rendered_index.py

reviewer-check:
	$(PYTHON) scripts/check_reviewer_blockers.py

pdf-metadata-check: all
	PDFINFO="$(PDFINFO)" $(PYTHON) scripts/check_pdf_metadata.py

pdf-font-check: all
	PDFFONTS="$(PDFFONTS)" $(PYTHON) scripts/check_pdf_fonts.py

pdf-text-check: all
	PDFTOTEXT="$(PDFTOTEXT)" $(PYTHON) scripts/check_pdf_text.py

pdf-reference-check: all
	PDFTOTEXT="$(PDFTOTEXT)" $(PYTHON) scripts/check_pdf_reference_locators.py

pdf-outline-check: all
	$(PYTHON) scripts/check_pdf_outline.py

pdf-page-integrity-check: all
	PDFINFO="$(PDFINFO)" PDFTOTEXT="$(PDFTOTEXT)" $(PYTHON) scripts/check_pdf_page_integrity.py

visual-smoke-check: all
	PDFINFO="$(PDFINFO)" PDFTOPPM="$(PDFTOPPM)" $(PYTHON) scripts/check_visual_smoke.py

visual-full-check: all
	PDFINFO="$(PDFINFO)" PDFTOPPM="$(PDFTOPPM)" $(PYTHON) scripts/check_visual_all_pages.py

visual-audit-plan-check: all
	PDFTOTEXT="$(PDFTOTEXT)" $(PYTHON) scripts/check_visual_audit_plan.py

proofing-plan-check: all
	PDFTOTEXT="$(PDFTOTEXT)" $(PYTHON) scripts/check_proofing_plan.py

documentation-check: all
	PDFINFO="$(PDFINFO)" $(PYTHON) scripts/check_documentation_consistency.py

placeholder-check:
	cd $(BOOK_DIR) && if $(RG) -n '$(PLACEHOLDER_CHECK)' $(CHKTEX_FILES) book_zh.tex; then exit 1; fi

chktex-focused-check:
	cd $(BOOK_DIR) && $(CHKTEX) -q -I0 -v0 $(CHKTEX_REVIEW_MUTES) $(CHKTEX_FILES)

chktex-triage-check:
	CHKTEX="$(CHKTEX)" $(PYTHON) scripts/check_chktex_triage.py

log-quality-check: all
	$(PYTHON) scripts/check_log_quality.py

chktex-budget-check:
	CHKTEX="$(CHKTEX)" $(PYTHON) scripts/check_chktex_budget.py

chktex-review:
	cd $(BOOK_DIR) && $(CHKTEX) -q -I0 -v0 $(CHKTEX_REVIEW_MUTES) $(CHKTEX_FILES) || true

visual-audit: all
	rm -rf "$(VISUAL_AUDIT_DIR)"
	mkdir -p "$(VISUAL_AUDIT_DIR)"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 1 -l 1 book.pdf "$(VISUAL_AUDIT_DIR)/en_title"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 9 -l 12 book.pdf "$(VISUAL_AUDIT_DIR)/en_toc"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 37 -l 45 book.pdf "$(VISUAL_AUDIT_DIR)/en_architecture"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 75 -l 83 book.pdf "$(VISUAL_AUDIT_DIR)/en_serving"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 173 -l 181 book.pdf "$(VISUAL_AUDIT_DIR)/en_multimodal"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 217 -l 238 book.pdf "$(VISUAL_AUDIT_DIR)/en_backmatter"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 1 -l 1 book_zh.pdf "$(VISUAL_AUDIT_DIR)/zh_title"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 3 -l 16 book_zh.pdf "$(VISUAL_AUDIT_DIR)/zh_toc"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 20 -l 42 book_zh.pdf "$(VISUAL_AUDIT_DIR)/zh_data"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 43 -l 53 book_zh.pdf "$(VISUAL_AUDIT_DIR)/zh_transformer"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 54 -l 65 book_zh.pdf "$(VISUAL_AUDIT_DIR)/zh_gpt"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 66 -l 81 book_zh.pdf "$(VISUAL_AUDIT_DIR)/zh_llama"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 82 -l 96 book_zh.pdf "$(VISUAL_AUDIT_DIR)/zh_optimization"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 97 -l 119 book_zh.pdf "$(VISUAL_AUDIT_DIR)/zh_distributed"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 120 -l 139 book_zh.pdf "$(VISUAL_AUDIT_DIR)/zh_serving"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 140 -l 153 book_zh.pdf "$(VISUAL_AUDIT_DIR)/zh_sft"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 154 -l 170 book_zh.pdf "$(VISUAL_AUDIT_DIR)/zh_peft"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 171 -l 183 book_zh.pdf "$(VISUAL_AUDIT_DIR)/zh_domain"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 184 -l 235 book_zh.pdf "$(VISUAL_AUDIT_DIR)/zh_alignment"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 236 -l 253 book_zh.pdf "$(VISUAL_AUDIT_DIR)/zh_multimodal"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 254 -l 268 book_zh.pdf "$(VISUAL_AUDIT_DIR)/zh_evaluation"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 279 -l 280 book_zh.pdf "$(VISUAL_AUDIT_DIR)/zh_appendix"
	cd $(BOOK_DIR) && $(PDFTOPPM) -png -r $(VISUAL_AUDIT_DPI) -f 269 -l 308 book_zh.pdf "$(VISUAL_AUDIT_DIR)/zh_backmatter"
	actual="$$(find "$(VISUAL_AUDIT_DIR)" -maxdepth 1 -type f -name '*.png' | wc -l | tr -d ' ')"; \
	if [ "$$actual" != "$(VISUAL_AUDIT_EXPECTED_PNGS)" ]; then \
		echo "visual audit PNG count $$actual, expected $(VISUAL_AUDIT_EXPECTED_PNGS)" >&2; \
		exit 1; \
	fi; \
	echo "visual audit PNG files: $$actual"
	VISUAL_AUDIT_DIR="$(VISUAL_AUDIT_DIR)" VISUAL_AUDIT_EXPECTED_PNGS="$(VISUAL_AUDIT_EXPECTED_PNGS)" VISUAL_AUDIT_DPI="$(VISUAL_AUDIT_DPI)" $(PYTHON) scripts/check_visual_audit_images.py
	find "$(VISUAL_AUDIT_DIR)" -maxdepth 1 -type f -name '*.png' | sort

clean:
	$(LATEXMK_RUN) -c book.tex
	$(LATEXMK_RUN) -c book_zh.tex
	find $(BOOK_DIR) \( -name '*.aux' -o -name '*.bbl' -o -name '*.blg' -o -name '*.fdb_latexmk' -o -name '*.fls' -o -name '*.idx' -o -name '*.ilg' -o -name '*.ind' -o -name '*.lof' -o -name '*.log' -o -name '*.lot' -o -name '*.out' -o -name '*.synctex.gz' -o -name '*.toc' -o -name '*.xdv' -o -name 'DescriptionTexts.txt' \) -exec rm -f {} +
	find $(SCRIPTS_DIR) -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -name '.DS_Store' -exec rm -f {} +

clean-check:
	$(PYTHON) scripts/check_clean_artifacts.py
