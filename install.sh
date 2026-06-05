#!/usr/bin/env bash
# rah installer — put the single-file CLI on PATH. Re-run to upgrade.
#
#   curl -fsSL https://raw.githubusercontent.com/Hiaa1/rah/main/install.sh | bash
#
# or run it from a clone to install the local copy. Then: rah init claude
set -euo pipefail

RAH_REPO="${RAH_REPO:-Hiaa1/rah}"
RAH_RAW_URL="${RAH_RAW_URL:-https://raw.githubusercontent.com/$RAH_REPO/main/rah}"
BIN_DIR="${RAH_BIN_DIR:-$HOME/.local/bin}"
DEST="$BIN_DIR/rah"

mkdir -p "$BIN_DIR"

src="${BASH_SOURCE[0]:-}"
if [ -n "$src" ] && [ -f "$src" ] && [ -f "$(dirname "$src")/rah" ]; then
  # Clone install: use the rah next to this script.
  install -m 0755 "$(dirname "$src")/rah" "$DEST"
  echo "rah: installed $(dirname "$src")/rah -> $DEST"
else
  # Remote install: download the single file.
  command -v curl >/dev/null 2>&1 || { echo "rah: curl is required" >&2; exit 1; }
  tmp="$(mktemp)"
  curl -fsSL "$RAH_RAW_URL" -o "$tmp" || { echo "rah: download failed" >&2; rm -f "$tmp"; exit 1; }
  head -1 "$tmp" | grep -q '^#!/usr/bin/env bash' || { echo "rah: bad download" >&2; rm -f "$tmp"; exit 1; }
  install -m 0755 "$tmp" "$DEST"; rm -f "$tmp"
  echo "rah: installed $DEST (from $RAH_RAW_URL)"
fi

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "rah: add $BIN_DIR to PATH ->  export PATH=\"$BIN_DIR:\$PATH\"" ;;
esac
echo "next:  rah doctor   &&   rah init claude   &&   rah mount user@host:/abs/path"
