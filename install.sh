#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-.}"
KB_SUBDIR="${2:-}"
SOURCE="$(cd "$(dirname "$0")" && pwd)"
TARGET="$(cd "$TARGET" && pwd)"

if [ -n "$KB_SUBDIR" ]; then
  KB_ROOT="$TARGET/$KB_SUBDIR"
  mkdir -p "$KB_ROOT"
else
  KB_ROOT="$TARGET"
fi

echo "Installing cursor-memory-compiler into: $KB_ROOT"

mkdir -p "$KB_ROOT"/{hooks,scripts,daily,knowledge/{concepts,connections,qa},reports}

cp "$SOURCE"/{AGENTS.md,howToUse.md,pyproject.toml,.gitignore} "$KB_ROOT/"
cp -r "$SOURCE"/hooks/* "$KB_ROOT/hooks/"
cp -r "$SOURCE"/scripts/* "$KB_ROOT/scripts/"

[ -f "$KB_ROOT/knowledge/index.md" ] || cp "$SOURCE/knowledge/index.md" "$KB_ROOT/knowledge/"
[ -f "$KB_ROOT/knowledge/log.md" ] || cp "$SOURCE/knowledge/log.md" "$KB_ROOT/knowledge/"

mkdir -p "$TARGET/.cursor/rules"

if [ -n "$KB_SUBDIR" ]; then
  mkdir -p "$TARGET/.cursor/hooks"
  cat > "$TARGET/.cursor/hooks/run-hook.sh" <<EOF
#!/usr/bin/env bash
cd "\$(dirname "\$0")/../../$KB_SUBDIR"
python -m uv run python "hooks/\$1"
EOF
  chmod +x "$TARGET/.cursor/hooks/run-hook.sh"

  cat > "$TARGET/.cursor/hooks.json" <<'EOF'
{
  "version": 1,
  "hooks": {
    "sessionStart": [{ "command": ".cursor/hooks/run-hook.sh session-start.py", "timeout": 15 }],
    "sessionEnd": [{ "command": ".cursor/hooks/run-hook.sh session-end.py", "timeout": 10 }],
    "preCompact": [{ "command": ".cursor/hooks/run-hook.sh pre-compact.py", "timeout": 10 }],
    "stop": [{ "command": ".cursor/hooks/run-hook.sh stop-memory.py", "loop_limit": 1, "timeout": 5 }]
  }
}
EOF
  cp "$SOURCE/.cursor/rules/knowledge-base.mdc" "$TARGET/.cursor/rules/"
else
  cp "$SOURCE/.cursor/hooks.json" "$TARGET/.cursor/"
  cp "$SOURCE/.cursor/rules/knowledge-base.mdc" "$TARGET/.cursor/rules/"
fi

cd "$KB_ROOT"
pip install uv -q 2>/dev/null || true
python -m uv sync

echo "Done. Open $TARGET in Cursor and check Settings -> Hooks."
