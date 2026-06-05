#!/usr/bin/env bash
# Symlink `rah` onto PATH so the routing hook (`rah hook` -> `rah run`) is resolvable
# inside the agent's Bash environment.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$HOME/.local/bin"
mkdir -p "$BIN"
ln -sf "$ROOT/rah" "$BIN/rah"
chmod +x "$ROOT/rah"
echo "rah: linked $BIN/rah -> $ROOT/rah"

case ":$PATH:" in
  *":$BIN:"*) ;;
  *) echo "rah: add ~/.local/bin to your PATH, e.g.  export PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
esac
