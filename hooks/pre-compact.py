"""PreCompact hook - captures transcript before Cursor context compaction."""

from __future__ import annotations

import logging
from pathlib import Path

from _cursor_utils import (
    extract_conversation_context,
    parse_hook_input,
    session_id_from,
    transcript_path_from,
    write_flush_context,
)

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"

logging.basicConfig(
    filename=str(SCRIPTS_DIR / "flush.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [pre-compact] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

MIN_TURNS_TO_FLUSH = 5


def main() -> None:
    try:
        hook_input = parse_hook_input()
    except (ValueError, TypeError) as e:
        logging.error("Failed to parse stdin: %s", e)
        return

    session_id = session_id_from(hook_input)
    transcript_path = transcript_path_from(hook_input)
    if not transcript_path:
        return

    try:
        context, turn_count = extract_conversation_context(transcript_path)
    except Exception:
        return

    if context.strip() and turn_count >= MIN_TURNS_TO_FLUSH:
        write_flush_context(session_id, context)


if __name__ == "__main__":
    main()
