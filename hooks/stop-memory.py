"""Stop hook - triggers Cursor agent to distill session context into daily logs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from _cursor_utils import parse_hook_input, session_id_from

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
COMPILE_FLAG = SCRIPTS_DIR / "compile-pending.flag"
COMPILE_AFTER_HOUR = 18


def build_followup(session_id: str, context_file: Path) -> str:
    today = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    parts = [
        "Memory maintenance: Read the captured session context and today's daily log.",
        f"Context file: {context_file.as_posix()}",
        f"Daily log: daily/{today}.md",
        "Per AGENTS.md, append a structured session entry with these sections (only if they have content):",
        "Importance (Critical|Important|Useful|Temporary with expires date), Context, Key Exchanges,",
        "Decisions Made, Lessons Learned, Action Items.",
        "Score each session using AGENTS.md importance rules.",
        "Skip routine tool calls and trivial exchanges.",
        "Delete the context file when done.",
        "Do not modify unrelated files.",
    ]

    now = datetime.now(timezone.utc).astimezone()
    if now.hour >= COMPILE_AFTER_HOUR and COMPILE_FLAG.exists():
        parts.append(
            "Also compile today's daily log into knowledge/ per AGENTS.md. "
            "Delete scripts/compile-pending.flag when complete."
        )

    return " ".join(parts)


def main() -> None:
    try:
        hook_input = parse_hook_input()
    except (ValueError, TypeError):
        print("{}")
        return

    session_id = session_id_from(hook_input)
    context_file = SCRIPTS_DIR / f"flush-context-{session_id}.md"

    if not context_file.exists() or context_file.stat().st_size == 0:
        print("{}")
        return

    print(json.dumps({"followup_message": build_followup(session_id, context_file)}))


if __name__ == "__main__":
    main()
