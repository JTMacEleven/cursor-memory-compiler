"""Memory importance scoring for the knowledge base."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

from config import KNOWLEDGE_DIR

IMPORTANCE_LEVELS = ("critical", "important", "useful", "temporary", "expired")

IMPORTANCE_RANK = {
    "critical": 0,
    "important": 1,
    "useful": 2,
    "temporary": 3,
    "expired": 4,
}

IMPORTANCE_LABELS = {
    "critical": "Critical",
    "important": "Important",
    "useful": "Useful",
    "temporary": "Temporary",
    "expired": "Expired",
}

DEFAULT_INDEX_HEADER = (
    "# Knowledge Base Index\n\n"
    "| Article | Importance | Summary | Compiled From | Updated |\n"
    "|---------|------------|---------|---------------|---------|"
)


def parse_frontmatter(content: str) -> dict[str, str]:
    """Extract simple key: value pairs from YAML frontmatter."""
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    block = content[3:end].strip()
    result: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def get_article_importance(path: Path) -> str:
    meta = parse_frontmatter(path.read_text(encoding="utf-8"))
    level = meta.get("importance", "useful").lower()
    return level if level in IMPORTANCE_LEVELS else "useful"


def get_article_expires(path: Path) -> date | None:
    meta = parse_frontmatter(path.read_text(encoding="utf-8"))
    raw = meta.get("expires", "")
    if not raw:
        return None
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def effective_importance(path: Path, today: date | None = None) -> str:
    """Return importance, auto-downgrading past-due temporary to expired."""
    today = today or date.today()
    level = get_article_importance(path)
    if level == "temporary":
        expires = get_article_expires(path)
        if expires and expires < today:
            return "expired"
    return level


def sort_index_content(index_text: str, include_expired: bool = False) -> str:
    """Sort index table rows by importance (Critical first)."""
    lines = index_text.splitlines()
    if not lines:
        return DEFAULT_INDEX_HEADER

    header_end = 0
    for i, line in enumerate(lines):
        if line.startswith("|") and "---" in line and i > 0:
            header_end = i + 1
            break

    header = lines[:header_end]
    rows = [ln for ln in lines[header_end:] if ln.strip().startswith("|")]

    def row_rank(row: str) -> tuple[int, str]:
        cells = [c.strip() for c in row.strip("|").split("|")]
        importance = "useful"
        for cell in cells:
            lower = cell.lower()
            if lower in IMPORTANCE_LEVELS:
                importance = lower
                break
        if not include_expired and importance == "expired":
            return (99, row)
        return (IMPORTANCE_RANK.get(importance, 2), row)

    sorted_rows = sorted(rows, key=row_rank)
    if not include_expired:
        sorted_rows = [r for r in sorted_rows if row_rank(r)[0] < 99]

    return "\n".join(header + sorted_rows)


def build_importance_summary(articles: list[Path], today: date | None = None) -> str:
    """Grouped article list from frontmatter for session injection."""
    today = today or date.today()
    buckets: dict[str, list[str]] = {k: [] for k in IMPORTANCE_LEVELS}

    for path in articles:
        rel = path.relative_to(KNOWLEDGE_DIR).as_posix().replace(".md", "")
        level = effective_importance(path, today)
        buckets[level].append(f"[[{rel}]]")

    lines = ["## Knowledge by Importance", ""]
    for level in IMPORTANCE_LEVELS:
        if level == "expired":
            continue
        items = buckets[level]
        if items:
            lines.append(f"### {IMPORTANCE_LABELS[level]} ({len(items)})")
            lines.extend(f"- {item}" for item in items)
            lines.append("")

    expired = buckets["expired"]
    if expired:
        lines.append(f"### Expired ({len(expired)}) — archived, not injected by default")
        lines.extend(f"- {item}" for item in expired[:5])
        if len(expired) > 5:
            lines.append(f"- ... and {len(expired) - 5} more")
        lines.append("")

    return "\n".join(lines)


def parse_daily_importance(text: str) -> str | None:
    """Extract **Importance:** line from daily log session entry."""
    match = re.search(r"\*\*Importance:\*\*\s*(\w+)", text, re.IGNORECASE)
    if match:
        level = match.group(1).lower()
        if level in IMPORTANCE_LEVELS:
            return level
    return None
