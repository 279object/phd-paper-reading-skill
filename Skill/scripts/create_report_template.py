#!/usr/bin/env python3
"""Create a canonical WAM report HTML scaffold."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


STYLE_RE = re.compile(r"<style\b[^>]*>.*?</style>", re.IGNORECASE | re.DOTALL)
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
    return normalized_links, style_match.group(0).strip()


def split_authors(authors: str) -> str:
    values = [part.strip() for part in re.split(r";|,", authors) if part.strip()]
    return ", ".join(values) if values else "TODO"


def build_html(
    paper_id: str,
    title: str,
    authors: str,
    venue: str,
    font_links: str,
    style_block: str,
) -> str:
    escaped_id = html.escape(paper_id)
    escaped_title = html.escape(title)
    escaped_authors = html.escape(split_authors(authors))
    escaped_venue = html.escape(venue or "TODO")
    abs_url = f"https://arxiv.org/abs/{escaped_id}"
    pdf_url = f"https://arxiv.org/pdf/{escaped_id}"

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escaped_title} - 精读报告</title>
  <script>
    window.MathJax = {{
      tex: {{
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
      }},
      svg: {{ fontCache: 'global' }}
    }};
  </script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
  {font_links}
  {style_block}
</head>
<body>
<main>
  <header>
    <h1>{escaped_title}</h1>
    <div class="meta">
      <p><strong>作者：</strong>{escaped_authors}</p>
      <p><strong>发表：</strong>{escaped_venue}</p>
      <p><strong>链接：</strong><a href="{abs_url}">arXiv:{escaped_id}</a> | <a href="{pdf_url}">PDF</a></p>
    </div>
  </header>

  <nav class="toc">
    <strong>目录</strong>
    <ul>
      <li><a href="#overview">1. 论文速览</a></li>
      <li><a href="#motivation">2. 动机</a></li>
      <li><a href="#related">3. 相关工作脉络</a></li>
      <li><a href="#method">4. 方法详解</a></li>
      <li><a href="#experiments">5. 实验与结果</a></li>
      <li><a href="#discussion">6. 分析、局限与边界</a></li>
      <li><a href="#repro">7. 可复现性审计</a></li>
    </ul>
  </nav>

  <section id="overview">
    <h2>1. 论文速览</h2>
    <div class="tldr">
      <strong>一句话总结：</strong>TODO
    </div>
    <table>
      <thead>
        <tr><th>速览问题</th><th>简明回答</th></tr>
      </thead>
      <tbody>
        <tr><td>论文解决什么问题</td><td>TODO</td></tr>
        <tr><td>核心方法</td><td>TODO</td></tr>
        <tr><td>关键结果</td><td>TODO</td></tr>
        <tr><td>复现难点</td><td>TODO</td></tr>
      </tbody>
    </table>
    <h3>核心贡献</h3>
    <ul>
      <li>TODO</li>
    </ul>
  </section>

  <section id="motivation">
    <h2>2. 动机</h2>
    <h3>2.1 要解决的问题</h3>
    <p>TODO</p>
    <h3>2.2 已有方法的局限</h3>
    <p>TODO</p>
    <h3>2.3 本文的高层思路</h3>
    <p>TODO</p>
  </section>

  <section id="related">
    <h2>3. 相关工作脉络</h2>
    <p>TODO</p>
  </section>

  <section id="method">
    <h2>4. 方法详解</h2>
    <h3>4.1 总体框架</h3>
    <p>TODO</p>
    <h3>4.2 核心模块</h3>
    <p>TODO</p>
    <div class="formula-block">
      <p class="intuition">TODO: 用一句话解释关键公式在计算什么。</p>
      $$ TODO $$
      <table class="symbol-table">
        <tr><td>$x$</td><td>TODO</td></tr>
      </table>
    </div>
    <h3>4.3 实现要点</h3>
    <p>TODO</p>
  </section>

  <section id="experiments">
    <h2>5. 实验与结果</h2>
    <h3>5.1 实验设置</h3>
    <p>TODO</p>
    <h3>5.2 主要结果</h3>
    <p>TODO</p>
    <h3>5.3 消融与补充实验</h3>
    <p>TODO</p>
  </section>

  <section id="discussion">
    <h2>6. 分析、局限与边界</h2>
    <h3>6.1 论文中的结果分析</h3>
    <p>TODO</p>
    <h3>6.2 作者自述的局限</h3>
    <p>TODO</p>
    <h3>6.3 适用边界</h3>
    <p>TODO</p>
  </section>

  <section id="repro">
    <h2>7. 可复现性审计</h2>
    <div class="audit-card">
      <h3>7.1 代码、数据与环境</h3>
      <ul class="checklist">
        <li><span class="warn">TODO</span> 补充代码、数据、模型权重和环境信息。</li>
      </ul>
    </div>
    <div class="audit-card">
      <h3>7.2 复现阻碍</h3>
      <p>TODO</p>
    </div>
  </section>
</main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="repository root")
    parser.add_argument("--paper-id", required=True, help="paper id, usually an arXiv id")
    parser.add_argument("--title", required=True, help="paper title")
    parser.add_argument("--authors", default="TODO", help="authors separated by semicolon or comma")
    parser.add_argument("--venue", default="TODO", help="venue, year, or arXiv version")
    parser.add_argument("--output-root", default="report", help="output root relative to repo")
    parser.add_argument(
        "--source",
        default=str(default_style_source()),
        help="style source HTML; defaults to the bundled WAM template; relative paths resolve from repo",
    )
    parser.add_argument("--force", action="store_true", help="overwrite an existing index.html")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    source = Path(args.source)
    if not source.is_absolute():
        source = repo / source
    source = source.resolve()
    if not source.exists():
        raise FileNotFoundError(f"style source not found: {source}")

    output_root = Path(args.output_root)
    if not output_root.is_absolute():
        output_root = repo / output_root
    output_dir = output_root / args.paper_id
    output_file = output_dir / "index.html"
    figures_dir = output_dir / "figures"

    if output_file.exists() and not args.force:
        raise FileExistsError(f"refusing to overwrite existing file without --force: {output_file}")

    font_links, style_block = extract_style_payload(read_text(source))
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    write_text(
        output_file,
        build_html(args.paper_id, args.title, args.authors, args.venue, font_links, style_block),
    )
    print(f"Created: {output_file}")
    print(f"Figures directory: {figures_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
