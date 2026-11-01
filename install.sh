#!/bin/sh
# Install (or remove with --uninstall) the orchestra skill into the current user's Claude Code setup.
#   ~/.claude/skills/orchestra/SKILL.md     the /orchestra skill
#   ~/.claude/orchestra/{row.py,ctx.py,worker-rules.md,board.html,board_sync.py}
#   ~/.local/bin/orch                       launcher for a fresh herdr tab
# Existing files that differ are backed up as <file>.bak-<timestamp> before being replaced.
set -eu

SRC=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
SKILL_DIR="$CLAUDE_DIR/skills/orchestra"
PART_DIR="$CLAUDE_DIR/orchestra"
BIN_DIR="${ORCH_BIN_DIR:-$HOME/.local/bin}"
PARTS="row.py ctx.py worker-rules.md board.html board_sync.py"

if [ "${1:-}" = "--uninstall" ]; then
  rm -f "$SKILL_DIR/SKILL.md" "$BIN_DIR/orch"
  for f in $PARTS; do rm -f "$PART_DIR/$f"; done
  rmdir "$SKILL_DIR" 2>/dev/null || true
  echo "removed. Generated files (registry-*.md, worker-rules.<name>.md, inbox-*.json) were left in $PART_DIR"
  exit 0
fi

stamp=$(date +%Y%m%d%H%M%S)
put() {  # put <src> <dst>
  if [ -f "$2" ] && ! cmp -s "$1" "$2"; then
    cp -p "$2" "$2.bak-$stamp"
    echo "backed up $2 -> $2.bak-$stamp"
  fi
  cp "$1" "$2"
}

mkdir -p "$SKILL_DIR" "$PART_DIR" "$BIN_DIR"
put "$SRC/skills/orchestra/SKILL.md" "$SKILL_DIR/SKILL.md"
for f in $PARTS; do put "$SRC/orchestra/$f" "$PART_DIR/$f"; done
put "$SRC/bin/orch" "$BIN_DIR/orch"
chmod +x "$PART_DIR/row.py" "$PART_DIR/ctx.py" "$PART_DIR/board_sync.py" "$BIN_DIR/orch"

echo "installed:"
echo "  $SKILL_DIR/SKILL.md"
echo "  $PART_DIR/{row.py,ctx.py,worker-rules.md,board.html,board_sync.py}"
echo "  $BIN_DIR/orch"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "note: $BIN_DIR is not on PATH; add it or run the launcher by full path" ;;
esac
echo "next: open a fresh herdr tab and run: orch"
