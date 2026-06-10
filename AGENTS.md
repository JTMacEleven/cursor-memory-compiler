# AGENTS.md - Personal Knowledge Base Schema

> **cursor-memory-compiler** — Cursor-native fork of [claude-memory-compiler](https://github.com/coleam00/claude-memory-compiler).
> Adapted from [Andrej Karpathy's LLM Knowledge Base](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
> Compiles knowledge from your Cursor AI conversations (hooks + agent, no external API).

## The Compiler Analogy

```
daily/          = source code    (your conversations - the raw material)
LLM             = compiler       (extracts and organizes knowledge)
knowledge/      = executable     (structured, queryable knowledge base)
lint            = test suite     (health checks for consistency)
queries         = runtime        (using the knowledge)
```

You don't manually organize your knowledge. You have conversations, and the LLM handles the synthesis, cross-referencing, and maintenance.

---

## Architecture

### Layer 1: `daily/` - Conversation Logs (Immutable Source)

Daily logs capture what happened in your AI coding sessions. These are the "raw sources" - append-only, never edited after the fact.

```
daily/
├── 2026-04-01.md
├── 2026-04-02.md
├── ...
```

Each file follows this format:

```markdown
# Daily Log: YYYY-MM-DD

## Sessions

### Session (HH:MM) - Brief Title

**Importance:** Critical | Important | Useful | Temporary (expires YYYY-MM-DD)

**Context:** What the user was working on.

**Key Exchanges:**
- User asked about X, assistant explained Y
- Decided to use Z approach because...
- Discovered that W doesn't work when...

**Decisions Made:**
- Chose library X over Y because...
- Architecture: went with pattern Z

**Lessons Learned:**
- Always do X before Y to avoid...
- The gotcha with Z is that...

**Action Items:**
- [ ] Follow up on X
- [ ] Refactor Y when time permits
```

### Layer 2: `knowledge/` - Compiled Knowledge (LLM-Owned)

The LLM owns this directory entirely. Humans read it but rarely edit it directly.

```
knowledge/
├── index.md              # Master catalog - every article with one-line summary
├── log.md                # Append-only chronological build log
├── concepts/             # Atomic knowledge articles
├── connections/          # Cross-cutting insights linking 2+ concepts
└── qa/                   # Filed query answers (compounding knowledge)
```

### Layer 3: This File (AGENTS.md)

The schema that tells the LLM how to compile and maintain the knowledge base. This is the "compiler specification."

---

## Structural Files

### `knowledge/index.md` - Master Catalog

A table listing every knowledge article. This is the primary retrieval mechanism - the LLM reads this FIRST when answering any query, then selects relevant articles to read in full.

Format:

```markdown
# Knowledge Base Index

| Article | Importance | Summary | Compiled From | Updated |
|---------|------------|---------|---------------|---------|
| [[concepts/supabase-auth]] | Critical | Row-level security patterns and JWT gotchas | daily/2026-04-02.md | 2026-04-02 |
| [[connections/auth-and-webhooks]] | Important | Token verification patterns shared across auth and webhooks | daily/2026-04-02.md, daily/2026-04-04.md | 2026-04-04 |
```

### `knowledge/log.md` - Build Log

Append-only chronological record of every compile, query, and lint operation.

Format:

```markdown
# Build Log

## [2026-04-01T14:30:00] compile | Daily Log 2026-04-01
- Source: daily/2026-04-01.md
- Articles created: [[concepts/nextjs-project-structure]], [[concepts/tailwind-setup]]
- Articles updated: (none)

## [2026-04-02T09:00:00] query | "How do I handle auth redirects?"
- Consulted: [[concepts/supabase-auth]], [[concepts/nextjs-middleware]]
- Filed to: [[qa/auth-redirect-handling]]
```

---

## Memory Importance Scoring

Every session entry and knowledge article must have an importance level. This controls retrieval priority — `sessionStart` injects Critical and Important memories first and excludes Expired articles from context.

### Levels

| Level | When to use | Examples | Retention |
|-------|-------------|----------|-----------|
| **Critical** | Breaking constraints, security, core architecture — wrong info causes real harm | Auth model, deployment invariants, data schema contracts | Permanent |
| **Important** | Project conventions and durable decisions | Stack choices, naming patterns, CI/CD setup, API design | Permanent |
| **Useful** | Helpful context, tips, non-obvious lessons | Debugging tricks, tool quirks, workflow preferences | Long-lived (default) |
| **Temporary** | Valid now but will age out | Sprint context, WIP decisions, time-bound workarounds | Set `expires: YYYY-MM-DD` |
| **Expired** | Superseded, wrong, or past expiry — kept for audit only | Old approach replaced, temporary past deadline | Archived |

### Scoring rules

1. **Default to Useful** when uncertain.
2. **Critical** sparingly — only for knowledge that must never be forgotten or violated.
3. **Temporary** must include `expires` in article frontmatter or `(expires YYYY-MM-DD)` in daily log Importance line.
4. When a Temporary article passes its expiry date, recompile as **Expired** (or delete if truly worthless).
5. When updating an article with contradictory info, mark the old version **Expired** and create/update the replacement at Critical/Important/Useful as appropriate.
6. Index table must include the Importance column for every article.

### Daily log format

```markdown
**Importance:** Important

**Context:** ...
```

For temporary session knowledge:

```markdown
**Importance:** Temporary (expires 2026-07-01)
```

### Article frontmatter

Add `importance` to every article:

```yaml
---
title: "Concept Name"
importance: important
expires: 2026-07-01   # required only when importance is temporary
---
```

Valid values: `critical`, `important`, `useful`, `temporary`, `expired`

---

## Article Formats

### Concept Articles (`knowledge/concepts/`)

One article per atomic piece of knowledge. These are facts, patterns, decisions, preferences, and lessons extracted from your conversations.

```markdown
---
title: "Concept Name"
importance: useful
aliases: [alternate-name, abbreviation]
tags: [domain, topic]
sources:
  - "daily/2026-04-01.md"
  - "daily/2026-04-03.md"
created: 2026-04-01
updated: 2026-04-03
---

# Concept Name

[2-4 sentence core explanation]

## Key Points

- [Bullet points, each self-contained]

## Details

[Deeper explanation, encyclopedia-style paragraphs]

## Related Concepts

- [[concepts/related-concept]] - How it connects

## Sources

- [[daily/2026-04-01.md]] - Initial discovery during project setup
- [[daily/2026-04-03.md]] - Updated after debugging session
```

### Connection Articles (`knowledge/connections/`)

Cross-cutting synthesis linking 2+ concepts. Created when a conversation reveals a non-obvious relationship.

```markdown
---
title: "Connection: X and Y"
connects:
  - "concepts/concept-x"
  - "concepts/concept-y"
sources:
  - "daily/2026-04-04.md"
created: 2026-04-04
updated: 2026-04-04
---

# Connection: X and Y

## The Connection

[What links these concepts]

## Key Insight

[The non-obvious relationship discovered]

## Evidence

[Specific examples from conversations]

## Related Concepts

- [[concepts/concept-x]]
- [[concepts/concept-y]]
```

### Q&A Articles (`knowledge/qa/`)

Filed answers from queries. Every complex question answered by the system can be permanently stored, making future queries smarter.

```markdown
---
title: "Q: Original Question"
question: "The exact question asked"
consulted:
  - "concepts/article-1"
  - "concepts/article-2"
filed: 2026-04-05
---

# Q: Original Question

## Answer

[The synthesized answer with [[wikilinks]] to sources]

## Sources Consulted

- [[concepts/article-1]] - Relevant because...
- [[concepts/article-2]] - Provided context on...

## Follow-Up Questions

- What about edge case X?
- How does this change if Y?
```

---

## Core Operations

### 1. Compile (daily/ -> knowledge/)

When processing a daily log:

1. Read the daily log file
2. Read `knowledge/index.md` to understand current knowledge state
3. Read existing articles that may need updating
4. For each piece of knowledge found in the log:
   - If an existing concept article covers this topic: UPDATE it with new information, add the daily log as a source
   - If it's a new topic: CREATE a new `concepts/` article
5. If the log reveals a non-obvious connection between 2+ existing concepts: CREATE a `connections/` article
6. UPDATE `knowledge/index.md` with new/modified entries
7. APPEND to `knowledge/log.md`

**Important guidelines:**
- A single daily log may touch 3-10 knowledge articles
- Prefer updating existing articles over creating near-duplicates
- Use Obsidian-style `[[wikilinks]]` with full relative paths from knowledge/
- Write in encyclopedia style - factual, concise, self-contained
- Every article must have YAML frontmatter
- Every article must link back to its source daily logs

### 2. Query (Ask the Knowledge Base)

1. Read `knowledge/index.md` (the master catalog)
2. Based on the question, identify 3-10 relevant articles from the index
3. Read those articles in full
4. Synthesize an answer with `[[wikilink]]` citations
5. If `--file-back` is specified: create a `knowledge/qa/` article and update index.md and log.md

**Why this works without RAG:** At personal knowledge base scale (50-500 articles), the LLM reading a structured index outperforms cosine similarity. The LLM understands what the question is really asking and selects pages accordingly. Embeddings find similar words; the LLM finds relevant concepts.

### 3. Lint (Health Checks)

Seven checks, run periodically:

1. **Broken links** - `[[wikilinks]]` pointing to non-existent articles
2. **Orphan pages** - Articles with zero inbound links from other articles
3. **Orphan sources** - Daily logs that haven't been compiled yet
4. **Stale articles** - Source daily log changed since article was last compiled
5. **Contradictions** - Conflicting claims across articles (requires LLM judgment)
6. **Missing backlinks** - A links to B but B doesn't link back to A
7. **Sparse articles** - Below 200 words, likely incomplete

Output: a markdown report with severity levels (error, warning, suggestion).

---

## Conventions

- **Wikilinks:** Use Obsidian-style `[[path/to/article]]` without `.md` extension
- **Writing style:** Encyclopedia-style, factual, third-person where appropriate
- **Dates:** ISO 8601 (YYYY-MM-DD for dates, full ISO for timestamps in log.md)
- **File naming:** lowercase, hyphens for spaces (e.g., `supabase-row-level-security.md`)
- **Frontmatter:** Every article must have YAML frontmatter with at minimum: title, importance, sources, created, updated
- **Sources:** Always link back to the daily log(s) that contributed to an article

---

## Full Project Structure

```
cursor-memory-compiler/
|-- .cursor/
|   |-- hooks.json                   # Cursor hook wiring
|   |-- rules/knowledge-base.mdc     # Always-on agent instructions
|-- AGENTS.md                        # This file - schema + technical reference
|-- README.md
|-- howToUse.md
|-- pyproject.toml
|-- install.ps1 / install.sh         # Install into existing projects
|-- daily/                           # Conversation logs (immutable)
|-- knowledge/                       # Compiled knowledge (agent-owned)
|   |-- index.md
|   |-- log.md
|   |-- concepts/
|   |-- connections/
|   |-- qa/
|-- hooks/                           # Cursor hook scripts
|   |-- session-start.py
|   |-- session-end.py
|   |-- pre-compact.py
|   |-- stop-memory.py
|-- scripts/
|   |-- lint.py
|   |-- config.py
|   |-- utils.py
|-- reports/
```

---

## Cursor Hook System (Automatic Capture)

Hooks are configured in `.cursor/hooks.json` and fire during Cursor Agent chat.

### `.cursor/hooks.json`

```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [{ "command": "python -m uv run python hooks/session-start.py", "timeout": 15 }],
    "sessionEnd": [{ "command": "python -m uv run python hooks/session-end.py", "timeout": 10 }],
    "preCompact": [{ "command": "python -m uv run python hooks/pre-compact.py", "timeout": 10 }],
    "stop": [{ "command": "python -m uv run python hooks/stop-memory.py", "loop_limit": 1, "timeout": 5 }]
  }
}
```

### Hook flow

| Hook | Role |
|------|------|
| `sessionStart` | Injects `knowledge/index.md` + recent daily log (`additional_context`) |
| `sessionEnd` | Parses Cursor JSONL transcript → `scripts/flush-context-{session_id}.md` |
| `preCompact` | Same capture before context window compaction |
| `stop` | Returns `followup_message` — agent distills context into `daily/` |

**No background API calls.** Memory flush and compile use the Cursor agent in-session.

### Cursor JSONL transcript format

```json
{"role":"user","message":{"content":[{"type":"text","text":"..."}]}}
```

Role is at the top level; content is nested in `message`.

---

## Agent-Driven Operations

### Compile (daily/ → knowledge/)

Ask in chat: *"Compile today's daily log per AGENTS.md"*

The agent reads the daily log, updates/creates concept articles, updates `index.md` and `log.md`, and records hashes in `scripts/state.json`:

```json
"ingested": {
  "2026-06-10.md": { "hash": "abc123...", "compiled_at": "2026-06-10T18:00:00" }
}
```

### Query

Ask naturally. Agent reads `knowledge/index.md`, selects articles, synthesizes answer with wikilinks.

### lint.py — Structural health checks

```bash
python -m uv run python scripts/lint.py --structural-only
```

| Check | Catches |
|-------|---------|
| Broken links | `[[wikilinks]]` to missing articles |
| Orphan pages | Zero inbound links |
| Orphan sources | Uncompiled daily logs |
| Stale articles | Daily log changed since compile |
| Missing backlinks | Asymmetric links |
| Sparse articles | Under 200 words |

Contradiction checks: ask the agent to review `knowledge/` for conflicts.

---

## State Tracking

`scripts/state.json` tracks `ingested` (daily log hashes), `query_count`, `last_lint`.

---

## Dependencies

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (`pip install uv`)
- Cursor with hooks enabled

No API keys. Uses your Cursor subscription for agent-driven compile/flush.

---

## Customization

### Additional Article Types

Add directories like `people/`, `projects/`, `tools/` to `knowledge/`. Define the article format in this file (AGENTS.md) and update `utils.py`'s `list_wiki_articles()` to include them.

### Obsidian Integration

The knowledge base is pure markdown with `[[wikilinks]]` - works natively in Obsidian. Point a vault at `knowledge/` for graph view, backlinks, and search.

### Scaling Beyond Index-Guided Retrieval

At ~2,000+ articles / ~2M+ tokens, the index becomes too large for the context window. At that point, add hybrid RAG (keyword + semantic search) as a retrieval layer before the LLM. See Karpathy's recommendation of `qmd` by Tobi Lutke for search at scale.
