#!/usr/bin/env bash
# rah installer — put the single-file CLI on PATH. Re-run to upgrade.
#
#   curl -fsSL https://raw.githubusercontent.com/Hiaa1/rah/main/install.sh | bash
#
# or run it from a clone to install the local copy. Then: rah init claude
set -euo pipefail

color_enabled() {
  case "${RAH_COLOR:-auto}" in
    always) return 0 ;;
    never|0|false|False|FALSE|off|OFF|no|NO) return 1 ;;
    *) [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-}" != dumb ] ;;
  esac
}

if color_enabled; then
  C_RESET=$'\033[0m'
  C_BOLD=$'\033[1m'
  C_DIM=$'\033[2m'
  C_GREEN=$'\033[32m'
  C_YELLOW=$'\033[33m'
  C_BLUE=$'\033[34m'
  C_CYAN=$'\033[36m'
else
  C_RESET=""; C_BOLD=""; C_DIM=""; C_GREEN=""; C_YELLOW=""; C_BLUE=""; C_CYAN=""
fi

header() { printf '%b\n' "${C_BOLD}${C_BLUE}==> $*${C_RESET}"; }
ok() { printf '%b\n' "  ${C_GREEN}[ok]${C_RESET} $*"; }
warn() { printf '%b\n' "  ${C_YELLOW}[warn]${C_RESET} $*"; }
note() { printf '%b\n' "  ${C_DIM}$*${C_RESET}"; }
cmd() { printf '%b\n' "  ${C_CYAN}$*${C_RESET}"; }

RAH_REPO="${RAH_REPO:-Hiaa1/rah}"
RAH_RAW_URL="${RAH_RAW_URL:-https://raw.githubusercontent.com/$RAH_REPO/main/rah}"
BIN_DIR="${RAH_BIN_DIR:-$HOME/.local/bin}"
DEST="$BIN_DIR/rah"

header "Installing rah"
mkdir -p "$BIN_DIR"

src="${BASH_SOURCE[0]:-}"
if [ -n "$src" ] && [ -f "$src" ] && [ -f "$(dirname "$src")/rah" ]; then
  # Clone install: use the rah next to this script.
  install -m 0755 "$(dirname "$src")/rah" "$DEST"
  ok "installed local checkout"
  note "$(dirname "$src")/rah -> $DEST"
else
  # Remote install: download the single file.
  command -v curl >/dev/null 2>&1 || { echo "rah: curl is required" >&2; exit 1; }
  tmp="$(mktemp)"
  curl -fsSL "$RAH_RAW_URL" -o "$tmp" || { echo "rah: download failed" >&2; rm -f "$tmp"; exit 1; }
  head -1 "$tmp" | grep -q '^#!/usr/bin/env bash' || { echo "rah: bad download" >&2; rm -f "$tmp"; exit 1; }
  install -m 0755 "$tmp" "$DEST"; rm -f "$tmp"
  ok "installed $DEST"
  note "from $RAH_RAW_URL"
fi

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    warn "$BIN_DIR is not on PATH"
    cmd "export PATH=\"$BIN_DIR:\$PATH\""
    ;;
esac
header "Next"
cmd "rah setup"
