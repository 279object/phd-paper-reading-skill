#!/usr/bin/env python3
"""Generate static English peers for WAM report blog pages.

The script keeps report/<paper_id>/index.html as the Chinese source and writes
report/<paper_id>/index.en.html. It also ensures both pages contain language
switch links and alternate hreflang metadata.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import time
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup, NavigableString


CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
STYLE_RE = re.compile(r"(<style\b[^>]*>)(.*?)(</style>)", re.IGNORECASE | re.DOTALL)
LANG_SWITCH_RE = re.compile(
    r"\s*<div\s+class=[\"']language-switch[\"'][\s\S]*?</div>\s*",
    re.IGNORECASE,
)
ALTERNATE_RE = re.compile(
    r"\s*<link\s+rel=[\"']alternate[\"']\s+hreflang=[\"'](?:zh-CN|en)[\"'][^>]*>\s*",
    re.IGNORECASE,
)
SKIP_PARENTS = {"script", "style", "code", "pre", "kbd", "samp", "var", "svg", "math", "textarea"}
LOCAL_ASSET_ATTRS = {
    "img": ["src"],
    "object": ["data"],
    "source": ["src", "srcset"],
    "video": ["src", "poster"],
}

LANGUAGE_CSS = """
    .language-switch {
      display: inline-flex;
      align-items: center;
      gap: 0.2rem;
      width: fit-content;
      margin: 0 0 1rem;
      padding: 0.18rem;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(255, 254, 251, 0.74);
      box-shadow: 0 10px 28px rgba(55, 63, 48, 0.08);
    }
    .language-switch a,
    .language-switch span {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 1.55rem;
      padding: 0.18rem 0.55rem;
      border-radius: 999px;
      color: var(--muted);
      font-family: var(--font-mono);
      font-size: 0.68rem;
      font-weight: 650;
      line-height: 1;
      text-transform: uppercase;
    }
    .language-switch a:hover {
      background: var(--state-soft);
      color: var(--state);
      text-decoration: none;
    }
    .language-switch .active {
      background: var(--ink);
      color: var(--paper);
    }
"""


class GoogleTranslator:
    def __init__(self, delay: float = 0.05, retries: int = 4) -> None:
        self.session = requests.Session()
        self.delay = delay
        self.retries = retries
        self.endpoint = "https://translate.googleapis.com/translate_a/single"

    def translate(self, text: str) -> str:
        params = {"client": "gtx", "sl": "zh-CN", "tl": "en", "dt": "t", "q": text}
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                response = self.session.get(self.endpoint, params=params, timeout=30)
                if not response.ok:
                    raise RuntimeError(f"HTTP {response.status_code}: {response.text[:160]}")
                payload = response.json()
                translated = "".join(part[0] for part in payload[0] if part and part[0])
                time.sleep(self.delay)
                return translated
            except Exception as exc:  # noqa: BLE001 - CLI should retry transient translation failures.
                last_error = exc
                time.sleep(min(2.0, 0.35 * (attempt + 1)))
        raise RuntimeError(f"translation failed after {self.retries} attempts: {last_error}") from last_error


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def default_cache_path() -> Path:
    return Path(__file__).resolve().parent / ".translation_cache.zh-en.json"


def load_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(read_text(path))


def save_cache(path: Path, cache: dict[str, str]) -> None:
    write_text(path, json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True))


def report_targets(repo: Path, targets: list[str]) -> list[Path]:
    if not targets:
        return sorted((repo / "report").glob("*/index.html"))
    resolved: list[Path] = []
    for target in targets:
        path = Path(target)
        if not path.is_absolute():
            path = repo / path
        if path.is_dir():
            path = path / "index.html"
        resolved.append(path)
    return resolved


def ensure_language_css(text: str) -> str:
    if ".language-switch" in text:
        return text

    def replace(match: re.Match[str]) -> str:
        return f"{match.group(1)}{match.group(2).rstrip()}\n{LANGUAGE_CSS}{match.group(3)}"

    updated, count = STYLE_RE.subn(replace, text, count=1)
    if count != 1:
        raise ValueError("HTML does not contain an inline style block")
    return updated


def ensure_alternates(text: str, current_lang: str) -> str:
    text = ALTERNATE_RE.sub("", text)
    zh = '<link rel="alternate" hreflang="zh-CN" href="./index.html">'
    en = '<link rel="alternate" hreflang="en" href="./index.en.html">'
    links = f"  {zh}\n  {en}" if current_lang == "zh-CN" else f"  {en}\n  {zh}"
    return re.sub(r"\s*</head>", f"\n{links}\n</head>", text, count=1, flags=re.IGNORECASE)


def switch_markup(current_lang: str) -> str:
    if current_lang == "en":
        return (
            '    <div class="language-switch" aria-label="Language switch">\n'
            '      <span class="active" aria-current="page">EN</span>\n'
            '      <a href="./index.html" lang="zh-CN">中文</a>\n'
            "    </div>\n"
        )
    return (
        '    <div class="language-switch" aria-label="语言切换">\n'
        '      <span class="active" aria-current="page">中文</span>\n'
        '      <a href="./index.en.html" lang="en">EN</a>\n'
        "    </div>\n"
    )


def ensure_language_switch(text: str, current_lang: str) -> str:
    text = LANG_SWITCH_RE.sub("\n", text)
    updated, count = re.subn(
        r"(<header\b[^>]*>\s*)",
        lambda match: match.group(1) + switch_markup(current_lang),
        text,
        count=1,
        flags=re.IGNORECASE,
    )
    if count != 1:
        raise ValueError("HTML does not contain a report header")
    return updated


def prepare_chinese_page(text: str) -> str:
    text = re.sub(r"<html\b([^>]*)\blang=[\"'][^\"']+[\"']", r'<html\1lang="zh-CN"', text, count=1, flags=re.IGNORECASE)
    text = ensure_language_css(text)
    text = ensure_alternates(text, "zh-CN")
    text = ensure_language_switch(text, "zh-CN")
    return re.sub(r"\n{3,}", "\n\n", text)


def protect_fragments(text: str) -> tuple[str, dict[str, str]]:
    patterns = [
        r"\$\$[\s\S]*?\$\$",
        r"\$[^$\n]{1,240}\$",
        r"\\\([\s\S]*?\\\)",
        r"\\\[[\s\S]*?\\\]",
        r"https?://[^\s<>()]+",
        r"\b(?:arXiv|NeurIPS|ICLR|CVPR|CoRL|RSS|ICRA|IROS|VLA|WAM)\b",
    ]
    protected: dict[str, str] = {}
    combined = re.compile("|".join(f"({pattern})" for pattern in patterns))

    def replace(match: re.Match[str]) -> str:
        key = f"ZXQ{len(protected):04d}QXZ"
        protected[key] = match.group(0)
        return key

    return combined.sub(replace, text), protected


def restore_fragments(text: str, protected: dict[str, str]) -> str:
    for key, value in protected.items():
        text = text.replace(key, value)
    return text


def normalize_translation(text: str) -> str:
    text = html.unescape(text)
    replacements = {
        "Directory": "Contents",
        "Table of contents": "Contents",
        "Chinese Reading Report": "Reading Report",
        "Chinese Intensive Reading Report": "Reading Report",
        "Intensive Reading Report": "Reading Report",
        "One sentence summary": "One-sentence summary",
        "author:": "Authors:",
        "mechanism:": "Affiliations:",
        "Organization:": "Affiliations:",
        "Posted by:": "Publication:",
        "Motive": "Motivation",
        "Boundary conditions": "Boundary Conditions",
        "Group meeting question and answer preparation": "Group Meeting Q&A Preparation",
    }
    for source, target in replacements.items():
        text = re.sub(re.escape(source), target, text, flags=re.IGNORECASE)
    punct = {
        "；": "; ",
        "：": ": ",
        "，": ", ",
        "。": ". ",
        "、": ", ",
        "（": "(",
        "）": ")",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
    }
    for source, target in punct.items():
        text = text.replace(source, target)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r"([,.;:])(?=\S)", r"\1 ", text)
    text = re.sub(r" {2,}", " ", text)
    return text


def should_translate_text(node: NavigableString) -> bool:
    value = str(node)
    if not value.strip() or not CJK_RE.search(value):
        return False
    parent = node.parent
    while parent is not None and getattr(parent, "name", None):
        if parent.name.lower() in SKIP_PARENTS:
            return False
        if "language-switch" in (parent.get("class") or []):
            return False
        parent = parent.parent
    return True


def translate_text(text: str, translator: GoogleTranslator, cache: dict[str, str]) -> str:
    leading = re.match(r"^\s*", text).group(0)
    trailing = re.search(r"\s*$", text).group(0)
    core = text.strip()
    if not core:
        return text
    if core in cache:
        return leading + cache[core] + trailing
    protected_text, protected = protect_fragments(core)
    translated = translator.translate(protected_text)
    translated = restore_fragments(normalize_translation(translated), protected)
    cache[core] = translated
    return leading + translated + trailing


def translate_remaining_cjk(soup: BeautifulSoup, translator: GoogleTranslator, cache: dict[str, str]) -> None:
    for node in list(soup.find_all(string=True)):
        if should_translate_text(node):
            node.replace_with(translate_text(str(node), translator, cache))


def make_english_html(source_text: str, translator: GoogleTranslator, cache: dict[str, str]) -> str:
    source_text = prepare_chinese_page(source_text)
    source_text = re.sub(r"<html\b([^>]*)\blang=[\"'][^\"']+[\"']", r'<html\1lang="en"', source_text, count=1, flags=re.IGNORECASE)
    source_text = ensure_alternates(source_text, "en")
    source_text = ensure_language_switch(source_text, "en")

    soup = BeautifulSoup(source_text, "lxml")
    if soup.html:
        soup.html["lang"] = "en"
    translate_remaining_cjk(soup, translator, cache)
    translate_remaining_cjk(soup, translator, cache)
    if soup.title and soup.title.string:
        soup.title.string.replace_with(soup.title.get_text().replace("精读报告", "Reading Report"))

    rendered = str(soup)
    if not rendered.lstrip().lower().startswith("<!doctype"):
        rendered = "<!DOCTYPE html>\n" + rendered
    rendered = re.sub(r"^<!DOCTYPE[^>]*>", "<!DOCTYPE html>", rendered, count=1, flags=re.IGNORECASE)
    return rendered


def validate_pair(zh_path: Path, en_path: Path) -> list[str]:
    errors: list[str] = []
    zh = read_text(zh_path)
    en = read_text(en_path)
    if 'href="./index.en.html"' not in zh:
        errors.append(f"{zh_path}: missing link to index.en.html")
    if 'href="./index.html"' not in en:
        errors.append(f"{en_path}: missing link to index.html")
    if '<html lang="en"' not in en:
        errors.append(f"{en_path}: missing html lang=en")
    if en.lower().count("<main") != 1:
        errors.append(f"{en_path}: expected exactly one <main>")

    zh_soup = BeautifulSoup(zh, "lxml")
    en_soup = BeautifulSoup(en, "lxml")
    if [tag.get("id") for tag in zh_soup.select("section[id]")] != [tag.get("id") for tag in en_soup.select("section[id]")]:
        errors.append(f"{en_path}: section IDs differ from Chinese source")

    for tag_name, attrs in LOCAL_ASSET_ATTRS.items():
        for tag in en_soup.find_all(tag_name):
            for attr in attrs:
                value = tag.get(attr)
                if not value or value.startswith(("#", "http://", "https://", "mailto:", "data:")):
                    continue
                local = value.split("#", 1)[0].split("?", 1)[0]
                if local and not (en_path.parent / local).exists():
                    errors.append(f"{en_path}: broken local {attr}={value}")
    for node in en_soup.find_all(string=True):
        parent = node.parent
        skip = False
        while parent is not None and getattr(parent, "name", None):
            if parent.name.lower() in SKIP_PARENTS or "language-switch" in (parent.get("class") or []):
                skip = True
                break
            parent = parent.parent
        if not skip and CJK_RE.search(str(node)):
            errors.append(f"{en_path}: untranslated Chinese text remains: {str(node).strip()[:80]}")
            break
    return errors


def build(repo: Path, targets: Iterable[Path], cache_path: Path, dry_run: bool) -> int:
    translator = GoogleTranslator()
    cache = load_cache(cache_path)
    errors: list[str] = []
    changed = 0

    for zh_path in targets:
        en_path = zh_path.with_name("index.en.html")
        source = read_text(zh_path)
        zh_updated = prepare_chinese_page(source)
        en_updated = make_english_html(source, translator, cache)
        if dry_run:
            print(f"Would build: {en_path}")
            continue
        if zh_updated != source:
            write_text(zh_path, zh_updated)
            changed += 1
        if not en_path.exists() or read_text(en_path) != en_updated:
            write_text(en_path, en_updated)
            changed += 1
        errors.extend(validate_pair(zh_path, en_path))
        save_cache(cache_path, cache)
        print(f"Built: {en_path}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Changed files: {changed}")
    print(f"Translation cache entries: {len(cache)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="repository root")
    parser.add_argument("--target", action="append", default=[], help="report dir or report/<id>/index.html")
    parser.add_argument("--cache", default=str(default_cache_path()), help="translation cache path")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    cache_path = Path(args.cache)
    if not cache_path.is_absolute():
        cache_path = repo / cache_path
    return build(repo, report_targets(repo, args.target), cache_path, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
