#!/usr/bin/env python3
"""Apply the approved WAM report blog style to report HTML pages."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


STYLE_RE = re.compile(r"<style\b[^>]*>.*?</style>", re.IGNORECASE | re.DOTALL)
BODY_RE = re.compile(r"(<body\b[^>]*>)(.*?)(</body>)", re.IGNORECASE | re.DOTALL)
MAIN_RE = re.compile(r"(<main\b[^>]*>)(.*)(</main>)", re.IGNORECASE | re.DOTALL)
NAV_RE = re.compile(r"<nav(?P<attrs>[^>]*)>(?P<content>.*?)</nav>", re.IGNORECASE | re.DOTALL)
TOC_ELEMENT_RE = re.compile(
    r"<(?P<tag>nav|div|section|ul|ol)(?P<attrs>[^>]class=[\"'][^\"']*\btoc\b[^>]*)>.*?</(?P=tag)>",
    re.IGNORECASE | re.DOTALL,
)
SECTION_RE = re.compile(
    r"<section\b(?P<attrs>[^>]*)>.*?<h2\b[^>]*>(?P<title>.*?)</h2>",
    re.IGNORECASE | re.DOTALL,
)
HEADER_RE = re.compile(r"(?P<header>\s*<header\b.*?</header>\s*)", re.IGNORECASE | re.DOTALL)
EMPTY_TOC_SECTION_RE = re.compile(
    r"\n?\s*<section\b[^>]*>\s*<h2\b[^>]*>\s*目录\s*</h2>\s*</section>\s*",
    re.IGNORECASE | re.DOTALL,
)
GOOGLE_FONT_RE = re.compile(
    r"\n?\s*<link\b[^>]*(?:fonts\.googleapis\.com|fonts\.gstatic\.com)[^>]*>\s*",
    re.IGNORECASE,
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def default_style_source() -> Path:
    return Path(__file__).resolve().parent.parent / "templates" / "wam-report-style.html"


def extract_style_payload(source_html: str) -> tuple[str, str]:
    style_match = STYLE_RE.search(source_html)
    if not style_match:
        raise ValueError("style source does not contain an inline <style> block")

    font_links = GOOGLE_FONT_RE.findall(source_html[: style_match.start()])
    if not font_links:
        raise ValueError("style source does not contain Google font links before <style>")

    normalized_links = "\n".join(link.strip() for link in font_links)
    return normalized_links, style_match.group(0)


def normalize_body_structure(html: str) -> str:
    body_match = BODY_RE.search(html)
    if not body_match:
        raise ValueError("target does not contain a <body> element")

    body_open, body_inner, body_close = body_match.groups()
    main_match = MAIN_RE.search(body_inner)

    if not main_match:
        normalized_inner = f"\n<main>\n{body_inner.strip()}\n</main>\n"
    else:
        before_main = body_inner[: main_match.start()]
        main_open, main_inner, main_close = main_match.groups()
        after_main = body_inner[main_match.end() :]

        if before_main.strip() or after_main.strip():
            normalized_inner = (
                f"\n{main_open}\n"
                f"{before_main.strip()}\n"
                f"{main_inner.strip()}\n"
                f"{after_main.strip()}\n"
                f"{main_close}\n"
            )
        else:
            return html

    return html[: body_match.start()] + body_open + normalized_inner + body_close + html[body_match.end() :]


def wrap_top_heading_in_header(html: str) -> str:
    body_match = BODY_RE.search(html)
    if not body_match:
        raise ValueError("target does not contain a <body> element")

    body_open, body_inner, body_close = body_match.groups()
    main_match = MAIN_RE.search(body_inner)
    if not main_match:
        return html

    main_open, main_inner, main_close = main_match.groups()
    if re.search(r"^\s*<header\b", main_inner, re.IGNORECASE):
        return html

    heading_meta = re.match(
        r"^(\s*)(<h1\b[^>]*>.*?</h1>\s*(?:<div\s+class=\"meta\"[^>]*>.*?</div>\s*)?)",
        main_inner,
        re.IGNORECASE | re.DOTALL,
    )
    if not heading_meta:
        return html

    indent = heading_meta.group(1)
    header_content = heading_meta.group(2).strip()
    rest = main_inner[heading_meta.end() :]
    new_main_inner = f"{indent}<header>\n{header_content}\n{indent}</header>\n{rest.lstrip()}"
    new_body_inner = body_inner[: main_match.start()] + main_open + new_main_inner + main_close + body_inner[main_match.end() :]
    return html[: body_match.start()] + body_open + new_body_inner + body_close + html[body_match.end() :]


def strip_tags(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def section_id(attrs: str) -> str | None:
    match = re.search(r"\bid=[\"']([^\"']+)[\"']", attrs, re.IGNORECASE)
    return match.group(1) if match else None


def insertion_point(main_inner: str) -> int:
    header_match = re.match(r"\s*<header\b.*?</header>\s*", main_inner, re.IGNORECASE | re.DOTALL)
    if header_match:
        return header_match.end()
    first_section = re.search(r"<section\b", main_inner, re.IGNORECASE)
    return first_section.start() if first_section else 0


def build_generated_toc(main_inner: str) -> str | None:
    items: list[str] = []
    for match in SECTION_RE.finditer(main_inner):
        target_id = section_id(match.group("attrs"))
        title = strip_tags(match.group("title"))
        if target_id and title:
            items.append(f'      <li><a href="#{target_id}">{title}</a></li>')
    if len(items) < 3:
        return None
    return "\n  <nav class=\"toc\">\n    <strong>目录</strong>\n    <ul>\n" + "\n".join(items) + "\n    </ul>\n  </nav>\n"


def clean_toc_separators(element: str) -> str:
    element = re.sub(r"(</a>)\s*(?:\||｜)\s*(<a\b)", r"\1\n    \2", element, flags=re.IGNORECASE)
    element = re.sub(r"(</a>)\s*(?:\||｜)\s*(\n?\s*</nav>)", r"\1\2", element, flags=re.IGNORECASE)
    return element


def canonicalize_toc_element(match: re.Match[str]) -> str:
    tag = match.group("tag").lower()
    element = match.group(0)
    if tag == "nav":
        element = re.sub(r"<nav\b[^>]*>", '<nav class="toc">', element, count=1, flags=re.IGNORECASE)
        return clean_toc_separators(element)
    if tag in {"div", "section"}:
        element = re.sub(rf"<{tag}\b[^>]*>", '<nav class="toc">', element, count=1, flags=re.IGNORECASE)
        element = re.sub(rf"</{tag}>", "</nav>", element, count=1, flags=re.IGNORECASE)
        return clean_toc_separators(element)
    if tag in {"ul", "ol"}:
        list_element = re.sub(
            rf"<{tag}\b[^>]*>",
            f"<{tag}>",
            element,
            count=1,
            flags=re.IGNORECASE,
        )
        return clean_toc_separators("\n  <nav class=\"toc\">\n    <strong>目录</strong>\n    " + list_element.strip() + "\n  </nav>\n")
    return clean_toc_separators(element)


def normalize_toc_structure(html: str) -> str:
    body_match = BODY_RE.search(html)
    if not body_match:
        raise ValueError("target does not contain a <body> element")

    body_open, body_inner, body_close = body_match.groups()
    main_match = MAIN_RE.search(body_inner)
    if not main_match:
        return html

    main_open, main_inner, main_close = main_match.groups()
    original_main_inner = main_inner
    main_inner = TOC_ELEMENT_RE.sub(canonicalize_toc_element, main_inner)
    main_inner = EMPTY_TOC_SECTION_RE.sub("\n", main_inner)

    header_match = HEADER_RE.match(main_inner)
    if header_match:
        header = header_match.group("header")
        header_toc = TOC_ELEMENT_RE.search(header)
        if header_toc:
            toc = canonicalize_toc_element(header_toc)
            new_header = header[: header_toc.start()] + header[header_toc.end() :]
            main_inner = new_header + "\n" + toc + "\n" + main_inner[header_match.end() :]

    def mark_nav(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        content = match.group("content")
        anchor_count = len(re.findall(r"href=[\"']#", content, re.IGNORECASE))
        if anchor_count < 3:
            return match.group(0)
        if re.search(r"class=[\"'][^\"']*\btoc\b", attrs, re.IGNORECASE):
            return clean_toc_separators(match.group(0))
        return clean_toc_separators(f'<nav class="toc">{content}</nav>')

    insert_at = insertion_point(main_inner)
    before_sections = main_inner[:insert_at]
    after_sections = main_inner[insert_at:]
    normalized_before = NAV_RE.sub(mark_nav, before_sections)

    if re.search(r"class=[\"'][^\"']*\btoc\b", normalized_before, re.IGNORECASE):
        if normalized_before == before_sections and main_inner == original_main_inner:
            return html
        new_main_inner = normalized_before + after_sections
    else:
        toc_match = TOC_ELEMENT_RE.search(after_sections)
        if toc_match:
            toc = toc_match.group(0)
            after_sections = after_sections[: toc_match.start()] + after_sections[toc_match.end() :]
            new_main_inner = normalized_before.rstrip() + "\n\n" + toc.strip() + "\n" + after_sections.lstrip()
        else:
            generated_toc = build_generated_toc(main_inner)
            if not generated_toc:
                if normalized_before == before_sections:
                    return html
                new_main_inner = normalized_before + after_sections
            else:
                new_main_inner = normalized_before + generated_toc + after_sections.lstrip()

    if new_main_inner == main_inner:
        return html

    new_body_inner = body_inner[: main_match.start()] + main_open + new_main_inner + main_close + body_inner[main_match.end() :]
    return html[: body_match.start()] + body_open + new_body_inner + body_close + html[body_match.end() :]


def apply_style(target_html: str, font_links: str, style_block: str) -> tuple[str, bool]:
    style_match = STYLE_RE.search(target_html)
    if not style_match:
        raise ValueError("target does not contain an inline <style> block")

    without_font_links = GOOGLE_FONT_RE.sub("\n", target_html)
    style_match = STYLE_RE.search(without_font_links)
    if not style_match:
        raise ValueError("target style block disappeared after font-link cleanup")

    replacement = f"{font_links}\n  {style_block.strip()}"
    updated = without_font_links[: style_match.start()] + replacement + without_font_links[style_match.end() :]
    updated = normalize_body_structure(updated)
    updated = wrap_top_heading_in_header(updated)
    updated = normalize_toc_structure(updated)
    updated = re.sub(r"\n{3,}", "\n\n", updated)
    return updated, updated != target_html


def collect_targets(repo: Path, all_reports: bool, explicit_targets: list[str]) -> list[Path]:
    targets: list[Path] = []

    if all_reports:
        targets.extend(sorted((repo / "report").glob("*/index.html")))

    for target in explicit_targets:
        path = Path(target)
        if not path.is_absolute():
            path = repo / path
        targets.append(path)

    deduped: list[Path] = []
    seen: set[Path] = set()
    for target in targets:
        resolved = target.resolve()
        if resolved not in seen:
            seen.add(resolved)
            deduped.append(target)
    return deduped


def ensure_report_target(repo: Path, target: Path) -> None:
    resolved_repo = repo.resolve()
    resolved_target = target.resolve()
    try:
        relative = resolved_target.relative_to(resolved_repo)
    except ValueError as exc:
        raise ValueError(f"target is outside repo: {target}") from exc

    parts = relative.parts
    if len(parts) != 3 or parts[0] != "report" or parts[2] != "index.html":
        raise ValueError(f"target is not report/*/index.html: {target}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="repository root")
    parser.add_argument(
        "--source",
        default=str(default_style_source()),
        help="style source HTML; defaults to the bundled WAM template; relative paths resolve from repo",
    )
    parser.add_argument("--target", action="append", default=[], help="target report index.html")
    parser.add_argument("--all", action="store_true", help="apply to all report/*/index.html files")
    parser.add_argument("--dry-run", action="store_true", help="show what would change without writing")
    parser.add_argument("--backup", action="store_true", help="write .bak files before editing")
    parser.add_argument("--include-source", action="store_true", help="allow editing the source file")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    source = Path(args.source)
    if not source.is_absolute():
        source = repo / source
    source = source.resolve()

    if not source.exists():
        raise FileNotFoundError(f"style source not found: {source}")

    targets = collect_targets(repo, args.all, args.target)
    if not targets:
        raise ValueError("no targets provided; use --target or --all")

    font_links, style_block = extract_style_payload(read_text(source))

    changed: list[Path] = []
    skipped: list[Path] = []
    failed: list[tuple[Path, str]] = []

    for target in targets:
        try:
            ensure_report_target(repo, target)
            resolved_target = target.resolve()
            if resolved_target == source and not args.include_source:
                skipped.append(target)
                continue
            if not target.exists():
                raise FileNotFoundError(f"target not found: {target}")

            updated, did_change = apply_style(read_text(target), font_links, style_block)
            if did_change:
                changed.append(target)
                if not args.dry_run:
                    if args.backup:
                        shutil.copy2(target, target.with_suffix(target.suffix + ".bak"))
                    write_text(target, updated)
            else:
                skipped.append(target)
        except Exception as exc:  # noqa: BLE001 - command-line tool should collect per-file errors.
            failed.append((target, str(exc)))

    action = "Would update" if args.dry_run else "Updated"
    for path in changed:
        print(f"{action}: {path}")
    for path in skipped:
        print(f"Skipped: {path}")
    for path, error in failed:
        print(f"Failed: {path}: {error}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
