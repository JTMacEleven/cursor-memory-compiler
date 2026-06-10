# How to Use the Knowledge Base

Cursor-native personal knowledge base. Conversations capture automatically; compile into articles on demand.

See [AGENTS.md](AGENTS.md) for the full schema.

---

## Install

**New project (use repo as root):**
```powershell
git clone https://github.com/JTMacEleven/cursor-memory-compiler.git my-project
cd my-project
pip install uv
python -m uv sync
```

**Existing project:**
```powershell
git clone https://github.com/JTMacEleven/cursor-memory-compiler.git _cmc
.\_cmc\install.ps1 -Target .
Remove-Item _cmc -Recurse -Force
```

Open in Cursor → **Settings → Hooks** → confirm 4 hooks.

---

## Automatic

| Hook | What happens |
|------|----------------|
| `sessionStart` | Injects `knowledge/index.md` into every new Agent chat |
| `sessionEnd` | Captures transcript when chat ends |
| `preCompact` | Captures before long chats get summarized |
| `stop` | Agent appends structured entry to `daily/YYYY-MM-DD.md` |

Work normally in Agent chat. No manual capture needed.

---

## Manual commands (in chat)

**Compile:**
> Compile today's daily log into the knowledge base per AGENTS.md

**Query:**
> What patterns have we established for deployment?

**Lint (terminal):**
```bash
python -m uv run python scripts/lint.py --structural-only
```

---

## Folders

| Path | Purpose |
|------|---------|
| `daily/` | Raw session logs |
| `knowledge/index.md` | Master catalog — read first |
| `knowledge/concepts/` | Atomic knowledge articles |
| `knowledge/connections/` | Cross-cutting insights |
| `knowledge/qa/` | Filed Q&A |

---

## Obsidian

Open this folder as an Obsidian vault. `[[wikilinks]]` work natively for graph view and backlinks.

---

## Troubleshooting

- **0 hooks configured** — `.cursor/hooks.json` must be at your Cursor **workspace root**
- **Nested project?** — Run `install.ps1 -Target . -KbSubdir my-subfolder` or reopen workspace at KB root
- **Empty knowledge/** — Normal until you compile; `daily/` fills first
- **Hook errors** — Check Settings → Hooks execution log and `scripts/flush.log`
