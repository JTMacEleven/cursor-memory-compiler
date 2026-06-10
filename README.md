# Cursor Memory Compiler

Give **Cursor AI** a memory that evolves with your codebase. Hooks automatically capture sessions, the agent distills key decisions and lessons into daily logs, and you compile everything into structured, cross-referenced knowledge articles.

Adapted from [coleam00/claude-memory-compiler](https://github.com/coleam00/claude-memory-compiler) and [Karpathy's LLM Knowledge Base](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — rebuilt for **Cursor hooks** (no Claude Code CLI, no Claude Agent SDK, no API keys).

## Quick start

Tell your Cursor agent:

> Clone or copy [cursor-memory-compiler](https://github.com/JTMacEleven/cursor-memory-compiler) into this project and run the install script. Read AGENTS.md and howToUse.md.

Or install manually:

```powershell
# Option A: use this repo as your project root (simplest)
git clone https://github.com/JTMacEleven/cursor-memory-compiler.git my-project
cd my-project
python -m pip install uv
python -m uv sync

# Option B: add to an existing project
git clone https://github.com/JTMacEleven/cursor-memory-compiler.git _cmc
.\_cmc\install.ps1 -Target .
Remove-Item _cmc -Recurse -Force
```

Then open the project in Cursor and confirm **Settings → Hooks** shows 4 hooks.

## How it works

```
Cursor Agent chat
  → sessionEnd / preCompact capture transcript
  → stop hook distills session → daily/YYYY-MM-DD.md
  → you compile daily logs → knowledge/ articles
  → sessionStart injects knowledge/index.md into next chat
```

| Layer | Folder | Role |
|-------|--------|------|
| Source | `daily/` | Immutable conversation logs |
| Compiler | Cursor Agent + AGENTS.md | Extracts and organizes knowledge |
| Executable | `knowledge/` | Structured, queryable articles |
| Lint | `scripts/lint.py` | Structural health checks (free) |

## Key commands

```bash
python -m uv run python scripts/lint.py --structural-only
```

Ask in chat:

- *"Compile today's daily log into the knowledge base per AGENTS.md"*
- *"What deployment patterns have we decided on?"*

## Docs

- [howToUse.md](howToUse.md) — practical guide
- [AGENTS.md](AGENTS.md) — full schema and technical reference

## Requirements

- [Cursor](https://cursor.com) with hooks enabled
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (`pip install uv`)

## License

MIT — see [LICENSE](LICENSE). Inspired by [claude-memory-compiler](https://github.com/coleam00/claude-memory-compiler).
