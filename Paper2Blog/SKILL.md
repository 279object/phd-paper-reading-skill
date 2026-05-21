---
name: wam-report-blog-style
description: Restyle or generate WAM-survey paper report/blog HTML pages under report/*/index.html to match the project homepage visual language. Use when Codex is asked to convert existing WAM report blogs, batch-apply the approved style, keep future report pages consistent with report/2302.00111/index.html, or generate a new Chinese paper-reading report HTML for an arXiv paper in the approved report blog format.
---

# WAM Report Blog Style

## Overview

Use this skill for three related tasks:

1. Restyle existing `report/*/index.html` pages so they match the approved homepage-aligned sample at `report/2302.00111/index.html`.
2. Generate a new paper-reading report page directly in that same approved format.
3. Generate static English peers for Chinese report pages and add bilingual switching.

The approved format uses one Chinese HTML file per paper under `report/<paper_id>/index.html`, optional local figures under `report/<paper_id>/figures/`, one `<main>` wrapper, a top `<header>`, a sidebar/table-of-contents `<nav class="toc">`, and content sections styled by the canonical CSS from `report/2302.00111/index.html`. When an English version exists, it lives next to the Chinese page as `report/<paper_id>/index.en.html`.

## Existing-Page Conversion

Use `scripts/apply_report_style.py`.

Dry run first:

```powershell
python C:\Users\26232\.codex\skills\wam-report-blog-style\scripts\apply_report_style.py --repo . --all --dry-run
```

Single target:

```powershell
python C:\Users\26232\.codex\skills\wam-report-blog-style\scripts\apply_report_style.py --repo . --target report\2401.00000\index.html
```

All report blogs:

```powershell
python C:\Users\26232\.codex\skills\wam-report-blog-style\scripts\apply_report_style.py --repo . --all
```

By default the script skips the source file itself. Use `--include-source` only when intentionally normalizing the source page too.

Conversion rules:

- Preserve report text, tables, figures, MathJax config, and scripts.
- Replace the first inline `<style>...</style>` block with the approved source style.
- Insert approved Google font links before the style block.
- Ensure exactly one `<main>...</main>`.
- Wrap a top bare `<h1>` plus optional `.meta` in `<header>...</header>`.
- Canonicalize TOC containers to `<nav class="toc">`.
- Move early/misplaced TOCs after the page header.
- Generate a TOC from `section[id] > h2` when a multi-section page has none.
- Remove literal `|` separators between TOC links.
- Remove empty sections that only contain a `目录` heading.
- Keep `.pdf-frame` and figures constrained to the canonical image sizing.

## New Report Generation

Use this workflow when the user asks to generate a new paper report/blog from an arXiv ID, local paper source, PDF, or paper notes.

1. Confirm the repository root contains `index.html`, `styles.css`, and `report/`.
2. Determine the output directory. Default to `report/<arxiv_id>/`.
3. If the output directory already exists, do not overwrite it without explicit user approval.
4. Create a canonical HTML scaffold with `scripts/create_report_template.py`.
5. Gather paper content from the available source:
   - Prefer arXiv source (`https://arxiv.org/e-print/<id>`) when the user requested an arXiv report and network is available.
   - Use the paper PDF or local source files when provided.
   - Read appendix material when available; integrate it into the relevant body sections instead of creating a separate appendix dump.
6. Copy extracted figures into `figures/` and reference them with relative paths.
7. Fill the scaffold with the report content.
8. Run `apply_report_style.py` on the new page to normalize structure and style.
9. Validate the final HTML before reporting completion.

Create scaffold:

```powershell
python C:\Users\26232\.codex\skills\wam-report-blog-style\scripts\create_report_template.py --repo . --paper-id 2401.00000 --title "Paper Title"
```

Optional fields:

```powershell
python C:\Users\26232\.codex\skills\wam-report-blog-style\scripts\create_report_template.py --repo . --paper-id 2401.00000 --title "Paper Title" --authors "A. Author; B. Author" --venue "arXiv 2024"
```

The scaffold intentionally contains placeholder content. Replace every `TODO` before considering the report done.

## English Version Generation

Use `scripts/build_bilingual_report_en.py` when the user asks to translate existing report blogs into English or add page-level Chinese/English switching.

Single target:

```powershell
python .local-skills\wam-report-blog-style\scripts\build_bilingual_report_en.py --repo . --target report\2401.00000
```

Multiple targets:

```powershell
python .local-skills\wam-report-blog-style\scripts\build_bilingual_report_en.py --repo . --target report\2401.00000 --target report\2402.00000
```

All report blogs:

```powershell
python .local-skills\wam-report-blog-style\scripts\build_bilingual_report_en.py --repo .
```

The script performs build-time translation and writes static HTML only. It should not add runtime translation JavaScript or browser-side network dependencies.

English-generation rules:

- Keep `index.html` as the Chinese source and write/update `index.en.html` beside it.
- Preserve HTML structure, section IDs, figures, tables, local asset paths, MathJax configuration, formulas, code snippets, URLs, citations, model names, dataset names, method names, and paper terminology.
- Translate visible Chinese text into faithful academic English without shortening the report or adding unsupported claims.
- Add a compact language switch in the page header:
  - Chinese page: active `中文`, link `EN` to `./index.en.html`.
  - English page: active `EN`, link `中文` to `./index.html`.
- Add alternate links in both pages:
  - `<link rel="alternate" hreflang="zh-CN" href="./index.html">`
  - `<link rel="alternate" hreflang="en" href="./index.en.html">`
- Do not translate text inside `script`, `style`, `code`, `pre`, SVG, MathJax formulas, URLs, or the language switch labels.
- Use the script's translation cache for repeatability during a batch run. The cache lives under the skill script directory by default and is not part of the report output.

## Report Content Contract

Write the report in Chinese, while preserving original English method names, dataset names, symbols, and paper terminology where useful.

Target reader: a junior PhD preparing a group-meeting presentation. The report should let the reader explain the motivation, reproduce the method at a conceptual and implementation level, understand key equations, and answer technical questions about experiments.

Required sections:

1. `overview` - Paper quick read: one-sentence summary, compact metadata table, contributions.
2. `motivation` - Problem setting, limitations of prior work, and the paper's high-level idea.
3. `related` - Related-work positioning based primarily on the paper's own Introduction and Related Work.
4. `method` - Detailed method explanation, pipeline, modules, equations, implementation details, and important figures.
5. `experiments` - Datasets, baselines, metrics, training/evaluation setup, main results, ablations, and supplemental experiments.
6. `discussion` - Only the paper's own analysis, limitations, failure cases, applicable boundaries, and future-work statements.
7. `repro` - Reproducibility audit: code/data availability, missing details, environment/hyperparameters, and concrete blockers.

If a paper naturally needs additional sections, add them, but keep the TOC and section IDs consistent.

## Content Rules

- Be objective and source-grounded. Do not add unsupported opinions, recommendations, or speculative evaluation.
- Integrate appendix information into the relevant sections. Mark it inline as `[Appendix A.3]` or the paper's actual appendix label.
- Before writing the final HTML, make an internal coverage map from paper sections to report sections. Do not include that map in the final page.
- Explain important equations in three parts: intuition, formal expression, and symbol-by-symbol explanation.
- Include implementation-oriented details when the paper provides them: tensor shapes, training tricks, model inputs/outputs, hyperparameters, and data preprocessing.
- Recreate important tables in HTML when possible. If a figure cannot be extracted, explain what it contains and why it is missing.
- Do not create a generic landing page or marketing page. The first screen must be the report.
- Do not add roleplay, dialogue, "next actions", or generic academic filler.

## HTML Format Rules

- Use `<!DOCTYPE html>` and `<html lang="zh-CN">`.
- Include the MathJax config when formulas are present.
- Use the canonical font links and CSS from `report/2302.00111/index.html`; prefer the scaffold script instead of hand-copying CSS.
- Body shape must be:

```html
<body>
<main>
  <header>...</header>
  <nav class="toc">...</nav>
  <section id="overview">...</section>
  ...
</main>
</body>
```

- Use `<figure>` or `<div class="figure">` with `<img>`/`<object class="pdf-frame">` and captions for figures.
- Use `.tldr`, `.note`, `.audit-card`, `.formula-block`, `.grid`, `.card`, `.danger`, `.appendix-ref`, and `.small` when they match existing report patterns.
- TOC links must not contain literal separator bars. Use one anchor per line or a `<ul>`.

## Validation

After generating or converting:

```powershell
python C:\Users\26232\.codex\skills\wam-report-blog-style\scripts\apply_report_style.py --repo . --target report\<paper_id>\index.html --dry-run
git diff -- report\<paper_id>\index.html
git status --short
```

For batch work, run:

```powershell
python C:\Users\26232\.codex\skills\wam-report-blog-style\scripts\apply_report_style.py --repo . --all --dry-run
```

Check manually or with search that:

- The page has one `<main>` and one `</main>`.
- A multi-section page has exactly one visible TOC before the first content section.
- There is no empty section with only `目录`.
- TOC anchors do not contain `|` separators.
- All images use relative paths and render from the report folder.
- No `TODO` placeholders remain.

For English pages, additionally check that:

- Every target directory has both `index.html` and `index.en.html`.
- English pages have `<html lang="en">`, exactly one `<main>`, and a language switch linking back to `./index.html`.
- Chinese pages link to `./index.en.html`.
- English and Chinese pages have the same `section[id]` sequence.
- Local figure/object/video references in `index.en.html` resolve from the report folder.
- No translation placeholders such as `ZXQBOUNDARY` or `ZXQ0000QXZ` remain.
- There is no visible Chinese text in the English body except the `中文` language-switch label.

For visual checks, let the user inspect the local HTML unless they ask for screenshots.
