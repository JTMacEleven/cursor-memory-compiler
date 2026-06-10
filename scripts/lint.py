"""
Lint the knowledge base for structural health.

Usage:
    python -m uv run python scripts/lint.py
    python -m uv run python scripts/lint.py --structural-only
"""

from __future__ import annotations

import argparse
from pathlib import Path

from config import KNOWLEDGE_DIR, REPORTS_DIR, now_iso, today_iso
from importance import (
    IMPORTANCE_LEVELS,
    effective_importance,
    get_article_expires,
    get_article_importance,
    parse_frontmatter,
)
from utils import (
    count_inbound_links,
    extract_wikilinks,
    file_hash,
    get_article_word_count,
    list_raw_files,
    list_wiki_articles,
    load_state,
    save_state,
    wiki_article_exists,
)

ROOT_DIR = Path(__file__).resolve().parent.parent


def check_broken_links() -> list[dict]:
    issues = []
    for article in list_wiki_articles():
        content = article.read_text(encoding="utf-8")
        rel = article.relative_to(KNOWLEDGE_DIR)
        for link in extract_wikilinks(content):
            if link.startswith("daily/"):
                continue
            if not wiki_article_exists(link):
                issues.append({
                    "severity": "error",
                    "check": "broken_link",
                    "file": str(rel),
                    "detail": f"Broken link: [[{link}]]",
                })
    return issues


def check_orphan_pages() -> list[dict]:
    issues = []
    for article in list_wiki_articles():
        rel = article.relative_to(KNOWLEDGE_DIR)
        link_target = str(rel).replace(".md", "").replace("\\", "/")
        if count_inbound_links(link_target) == 0:
            issues.append({
                "severity": "warning",
                "check": "orphan_page",
                "file": str(rel),
                "detail": f"Orphan page: [[{link_target}]]",
            })
    return issues


def check_orphan_sources() -> list[dict]:
    state = load_state()
    ingested = state.get("ingested", {})
    issues = []
    for log_path in list_raw_files():
        if log_path.name not in ingested:
            issues.append({
                "severity": "warning",
                "check": "orphan_source",
                "file": f"daily/{log_path.name}",
                "detail": f"Uncompiled: {log_path.name}",
            })
    return issues


def check_stale_articles() -> list[dict]:
    state = load_state()
    ingested = state.get("ingested", {})
    issues = []
    for log_path in list_raw_files():
        if log_path.name in ingested:
            if ingested[log_path.name].get("hash", "") != file_hash(log_path):
                issues.append({
                    "severity": "warning",
                    "check": "stale_article",
                    "file": f"daily/{log_path.name}",
                    "detail": f"Stale: {log_path.name} changed since compile",
                })
    return issues


def check_missing_backlinks() -> list[dict]:
    issues = []
    for article in list_wiki_articles():
        content = article.read_text(encoding="utf-8")
        rel = article.relative_to(KNOWLEDGE_DIR)
        source_link = str(rel).replace(".md", "").replace("\\", "/")
        for link in extract_wikilinks(content):
            if link.startswith("daily/"):
                continue
            target_path = KNOWLEDGE_DIR / f"{link}.md"
            if target_path.exists():
                if f"[[{source_link}]]" not in target_path.read_text(encoding="utf-8"):
                    issues.append({
                        "severity": "suggestion",
                        "check": "missing_backlink",
                        "file": str(rel),
                        "detail": f"[[{source_link}]] → [[{link}]] (no backlink)",
                    })
    return issues


def check_missing_importance() -> list[dict]:
    issues = []
    for article in list_wiki_articles():
        meta = parse_frontmatter(article.read_text(encoding="utf-8"))
        if "importance" not in meta:
            rel = article.relative_to(KNOWLEDGE_DIR)
            issues.append({
                "severity": "warning",
                "check": "missing_importance",
                "file": str(rel),
                "detail": "Missing importance frontmatter (default: useful)",
            })
    return issues


def check_invalid_importance() -> list[dict]:
    issues = []
    for article in list_wiki_articles():
        level = get_article_importance(article)
        meta = parse_frontmatter(article.read_text(encoding="utf-8"))
        if "importance" in meta and meta["importance"].lower() not in IMPORTANCE_LEVELS:
            rel = article.relative_to(KNOWLEDGE_DIR)
            issues.append({
                "severity": "error",
                "check": "invalid_importance",
                "file": str(rel),
                "detail": f"Invalid importance: {meta['importance']}",
            })
    return issues


def check_temporary_expiry() -> list[dict]:
    issues = []
    for article in list_wiki_articles():
        level = get_article_importance(article)
        rel = article.relative_to(KNOWLEDGE_DIR)
        if level == "temporary" and not get_article_expires(article):
            issues.append({
                "severity": "warning",
                "check": "temporary_no_expires",
                "file": str(rel),
                "detail": "Temporary article missing expires: YYYY-MM-DD",
            })
        effective = effective_importance(article)
        if level == "temporary" and effective == "expired":
            issues.append({
                "severity": "warning",
                "check": "temporary_expired",
                "file": str(rel),
                "detail": "Past expiry — recompile as importance: expired",
            })
    return issues


def check_sparse_articles() -> list[dict]:
    issues = []
    for article in list_wiki_articles():
        word_count = get_article_word_count(article)
        if word_count < 200:
            rel = article.relative_to(KNOWLEDGE_DIR)
            issues.append({
                "severity": "suggestion",
                "check": "sparse_article",
                "file": str(rel),
                "detail": f"Sparse: {word_count} words (min 200)",
            })
    return issues


def generate_report(all_issues: list[dict]) -> str:
    errors = [i for i in all_issues if i["severity"] == "error"]
    warnings = [i for i in all_issues if i["severity"] == "warning"]
    suggestions = [i for i in all_issues if i["severity"] == "suggestion"]

    lines = [
        f"# Lint Report - {today_iso()}",
        "",
        f"**Total:** {len(all_issues)} ({len(errors)} errors, {len(warnings)} warnings, {len(suggestions)} suggestions)",
        "",
    ]

    for label, issues in [("Errors", errors), ("Warnings", warnings), ("Suggestions", suggestions)]:
        if issues:
            lines.append(f"## {label}\n")
            for issue in issues:
                lines.append(f"- `{issue['file']}` — {issue['detail']}")
            lines.append("")

    if not all_issues:
        lines.append("All checks passed.")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Lint the knowledge base")
    parser.add_argument("--structural-only", action="store_true", help="Structural checks only (default)")
    parser.add_argument("--agent-contradictions", action="store_true", help="Print prompt for agent contradiction check")
    args = parser.parse_args()

    print("Running knowledge base lint checks...")
    all_issues: list[dict] = []

    for name, fn in [
        ("Broken links", check_broken_links),
        ("Missing importance", check_missing_importance),
        ("Invalid importance", check_invalid_importance),
        ("Temporary expiry", check_temporary_expiry),
        ("Orphan pages", check_orphan_pages),
        ("Orphan sources", check_orphan_sources),
        ("Stale articles", check_stale_articles),
        ("Missing backlinks", check_missing_backlinks),
        ("Sparse articles", check_sparse_articles),
    ]:
        print(f"  Checking: {name}...")
        issues = fn()
        all_issues.extend(issues)
        print(f"    Found {len(issues)} issue(s)")

    if args.agent_contradictions:
        print("\nAsk the Cursor agent: 'Review knowledge/ for contradictions per AGENTS.md'")

    report = generate_report(all_issues)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"lint-{today_iso()}.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved to: {report_path}")

    state = load_state()
    state["last_lint"] = now_iso()
    save_state(state)

    errors = sum(1 for i in all_issues if i["severity"] == "error")
    print(f"\nResults: {errors} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
