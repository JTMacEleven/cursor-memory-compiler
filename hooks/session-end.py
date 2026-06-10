"""SessionEnd hook - captures Cursor transcript for memory extraction."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
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
    format="%(asctime)s %(levelname)s [session-end] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

MIN_TURNS_TO_FLUSH = 1


def main() -> None:
    try:
        hook_input = parse_hook_input()
    except (ValueError, TypeError) as e:
        logging.error("Failed to parse stdin: %s", e)
        return

    session_id = session_id_from(hook_input)
    logging.info("SessionEnd fired: session=%s", session_id)

    transcript_path = transcript_path_from(hook_input)
    if not transcript_path:
        logging.info("SKIP: no transcript path")
        return

    try:
        context, turn_count = extract_conversation_context(transcript_path)
    except Exception as e:
        logging.error("Context extraction failed: %s", e)
        return

    if not context.strip() or turn_count < MIN_TURNS_TO_FLUSH:
        logging.info("SKIP: empty or too few turns")
        return

    context_file = write_flush_context(session_id, context)
    logging.info("Wrote %s (%d turns)", context_file.name, turn_count)

    if datetime.now(timezone.utc).astimezone().hour >= 18:
        (SCRIPTS_DIR / "compile-pending.flag").touch()


if __name__ == "__main__":
    main()
