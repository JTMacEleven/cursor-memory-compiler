"""Shared helpers for Cursor-native memory hooks."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

MAX_TURNS = 30
MAX_CONTEXT_CHARS = 15_000

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"


def parse_hook_input() -> dict:
    """Read and parse JSON hook input from stdin."""
    raw_input = sys.stdin.read()
    try:
        return json.loads(raw_input)
    except json.JSONDecodeError:
        fixed_input = re.sub(r'(?<!\\)\\(?!["\\])', r'\\\\', raw_input)
        return json.loads(fixed_input)


def session_id_from(hook_input: dict) -> str:
    return hook_input.get("session_id") or hook_input.get("conversation_id", "unknown")


def transcript_path_from(hook_input: dict) -> Path | None:
    path_str = hook_input.get("transcript_path") or os.environ.get("CURSOR_TRANSCRIPT_PATH", "")
    if not path_str or not isinstance(path_str, str):
        return None
    path = Path(path_str)
    return path if path.exists() else None


def extract_conversation_context(transcript_path: Path) -> tuple[str, int]:
    """Read JSONL transcript and extract last conversation turns as markdown."""
    turns: list[str] = []

    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg = entry.get("message", {})
            if isinstance(msg, dict):
                role = entry.get("role") or msg.get("role", "")
                content = msg.get("content", entry.get("content", ""))
            else:
                role = entry.get("role", "")
                content = entry.get("content", "")

            if role not in ("user", "assistant"):
                continue

            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif isinstance(block, str):
                        text_parts.append(block)
                content = "\n".join(text_parts)

            if isinstance(content, str) and content.strip():
                label = "User" if role == "user" else "Assistant"
                turns.append(f"**{label}:** {content.strip()}\n")

    recent = turns[-MAX_TURNS:]
    context = "\n".join(recent)

    if len(context) > MAX_CONTEXT_CHARS:
        context = context[-MAX_CONTEXT_CHARS:]
        boundary = context.find("\n**")
        if boundary > 0:
            context = context[boundary + 1 :]

    return context, len(recent)


def write_flush_context(session_id: str, context: str) -> Path:
    """Write captured context for the stop hook to distill."""
    context_file = SCRIPTS_DIR / f"flush-context-{session_id}.md"
    context_file.write_text(context, encoding="utf-8")
    return context_file
