# WAM Survey Paper Reading Skill

> Start here: [OpenMOSS/WAM-survey](https://github.com/OpenMOSS/WAM-survey) is the main survey repository. This repository is a companion Codex skill built to support its paper-reading workflow.

If you are interested in world models, action models, and WAM-related research, please visit the WAM survey repository first for the full paper list, taxonomy, and survey materials:

[https://github.com/OpenMOSS/WAM-survey](https://github.com/OpenMOSS/WAM-survey)

This repository provides a supporting Codex skill for reading, organizing, and presenting papers. It helps generate, format, and maintain consistent paper-reading report pages for survey-related seminar preparation.Browse report examples generated with this skill in the [Library section of the Awesome-WAM website](https://openmoss.github.io/Awesome-WAM/#library). 

## Contents

- [Repository Layout](#repository-layout)
- [What This Skill Does](#what-this-skill-does)
- [Report Structure](#report-structure)
- [Install the Skill](#install-the-skill)
- [Quick Start](#quick-start)
- [Script Reference](#script-reference)
- [Advanced Tips](#advanced-tips)
- [Contributing](#contributing)

## Repository Layout

```text
Skill/
|-- SKILL.md
|-- agents/
|   `-- openai.yaml
|-- templates/
|   `-- wam-report-style.html
`-- scripts/
    |-- apply_report_style.py
    |-- build_bilingual_report_en.py
    `-- create_report_template.py
```

- [`Skill/SKILL.md`](./Skill/SKILL.md): the complete Codex workflow, report-writing contract, HTML rules, and validation checklist.
- [`Skill/agents/openai.yaml`](./Skill/agents/openai.yaml): the skill display name, description, and default invocation prompt.
- [`Skill/templates/wam-report-style.html`](./Skill/templates/wam-report-style.html): the bundled WAM report style template used by default.
- [`Skill/scripts/create_report_template.py`](./Skill/scripts/create_report_template.py): creates a canonical Chinese report scaffold for a new paper.
- [`Skill/scripts/apply_report_style.py`](./Skill/scripts/apply_report_style.py): normalizes existing report pages to the approved WAM survey visual language.
- [`Skill/scripts/build_bilingual_report_en.py`](./Skill/scripts/build_bilingual_report_en.py): generates static English peers for Chinese report pages and adds a language switch.

## What This Skill Does

`wam-report-blog-style` turns paper reading into a repeatable publishing workflow for the [WAM survey repository](https://github.com/OpenMOSS/WAM-survey). It helps Codex produce seminar-ready paper reports while keeping the report collection visually and structurally consistent.

| Workflow | Use it when you need to | Result |
| --- | --- | --- |
| Generate a report | Read a new arXiv paper, PDF, local source tree, or set of notes | `report/<paper_id>/index.html` with a structured Chinese reading report |
| Normalize report pages | Bring older reports into the approved WAM survey style | Consistent CSS, `<main>`, header, TOC, figures, and section structure |
| Build bilingual pages | Publish an English peer for an existing Chinese report | `index.en.html`, static language switching, and `hreflang` metadata |

The report format is designed for a junior PhD preparing a group meeting. A finished page should make it possible to explain the paper's motivation, method, equations, experiments, limitations, and reproducibility constraints without returning to scattered notes.

## Report Structure

Each generated report follows a seven-part reading framework:

1. **Paper quick read**: one-sentence summary, compact metadata, and contributions.
2. **Motivation**: problem setting, prior limitations, and the paper's high-level idea.
3. **Related work**: the paper's position in the surrounding research landscape.
4. **Method**: pipeline, modules, equations, implementation details, and important figures.
5. **Experiments**: datasets, baselines, metrics, results, ablations, and supplemental evidence.
6. **Discussion**: author-stated analysis, limitations, failure cases, and applicable boundaries.
7. **Reproducibility audit**: code, data, environment, hyperparameters, missing details, and concrete blockers.

The skill also instructs Codex to integrate useful appendix material into the relevant sections, preserve original technical terminology where appropriate, explain important equations symbol by symbol, and keep claims grounded in the paper.

## Install the Skill

To use the skill end to end, prepare:

- [Codex](https://github.com/openai/codex) with skill support.
- Python 3.10 or newer.
- A report workspace. Codex can create the `report/` directory when starting a new workspace.
- `requests`, `beautifulsoup4`, and `lxml` only when generating English pages.
- Network access only when Codex needs to fetch paper sources or when `build_bilingual_report_en.py` calls Google Translate.

The WAM report style is bundled with this skill. Generated pages are written under `report/<paper_id>/` in the workspace passed with `--repo`.

Install the optional translation dependencies with:

```bash
python -m pip install requests beautifulsoup4 lxml
```

Clone this repository, then copy the `Skill/` directory into your Codex skills directory under the skill name:

```bash
git clone https://github.com/279object/phd-paper-reading-skill.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R phd-paper-reading-skill/Skill \
  "${CODEX_HOME:-$HOME/.codex}/skills/wam-report-blog-style"
```

Start a new Codex session after installation. The skill is available as:

```text
$wam-report-blog-style
```

## Quick Start

Run Codex from the root of your report workspace. For normal work, invoke the skill with a natural-language request:

```text
Use $wam-report-blog-style to read arXiv:2401.00000 and generate a Chinese
paper-reading report under report/2401.00000/. Include useful appendix details,
extract important figures when available, and validate the final HTML.
```

Normalize existing pages:

```text
Use $wam-report-blog-style to dry-run the approved report style across all
report pages, summarize which files would change, and then apply the conversion.
```

Add English versions:

```text
Use $wam-report-blog-style to generate static English versions for
report/2401.00000 and report/2402.00000, then validate the bilingual pairs.
```

## Script Reference

You normally do not need to run these scripts manually. Codex invokes them as part of the skill workflow. The commands below are provided for maintainers, batch operations, and debugging. Run them from the root of your report workspace after installing the skill:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/wam-report-blog-style"
```

Create a report scaffold:

```bash
python "$SKILL_DIR/scripts/create_report_template.py" \
  --repo . \
  --paper-id 2401.00000 \
  --title "Paper Title" \
  --authors "A. Author; B. Author" \
  --venue "arXiv 2024"
```

The scaffold intentionally contains `TODO` placeholders. A report is not complete until Codex replaces all of them with source-grounded content.

Preview and apply style normalization:

```bash
python "$SKILL_DIR/scripts/apply_report_style.py" --repo . --all --dry-run
python "$SKILL_DIR/scripts/apply_report_style.py" --repo . --all --backup
```

Normalize a single report:

```bash
python "$SKILL_DIR/scripts/apply_report_style.py" \
  --repo . \
  --target report/2401.00000/index.html \
  --dry-run
```

Generate static English pages:

```bash
python "$SKILL_DIR/scripts/build_bilingual_report_en.py" \
  --repo . \
  --target report/2401.00000
```

Omit `--target` to process every `report/*/index.html`. The bilingual builder keeps Chinese pages as `index.html`, writes English pages as `index.en.html`, preserves local assets and technical fragments, and reuses a translation cache for repeatable batch runs.

## Advanced Tips

### Use the paper source, not only the abstract

For a substantive report, provide an arXiv ID or a local PDF and let Codex inspect the full source, including appendices. The skill is designed to integrate appendix findings into the main narrative with inline references such as `[Appendix A.3]`.

### Dry-run before batch changes

Start style migrations with `--dry-run`, inspect the affected files, and use `--backup` for a large conversion. The style normalizer can repair misplaced TOCs, wrap bare headings in a header, remove empty TOC sections, and generate a TOC for multi-section pages that do not have one.

### Keep figures local

Store extracted figures under `report/<paper_id>/figures/` and reference them with relative paths. This keeps report pages portable and allows the bilingual validator to detect broken local image, object, and video references.

### Override the canonical style source when needed

The bundled WAM template is the default. Both scaffold creation and style normalization also accept `--source` when you intentionally want a custom visual format. The custom HTML file must contain Google Fonts links before an inline `<style>` block:

```bash
python "$SKILL_DIR/scripts/apply_report_style.py" \
  --repo . \
  --source templates/my-report-style.html \
  --all \
  --dry-run
```

### Treat English generation as a publishing step

The English builder writes static HTML. It does not add browser-side translation JavaScript or runtime network dependencies. Review technical terminology after generation, especially for domain-specific method names, datasets, and compact table cells.

## Contributing

Contributions that improve the reading workflow, report quality, or validation coverage are welcome. If this skill or the WAM survey saves you a little time at a critical moment, consider starring this repository and the main [OpenMOSS/WAM-survey](https://github.com/OpenMOSS/WAM-survey) project. We will take each star as a small but very welcome sign that the late-night paper reading was worth it.
