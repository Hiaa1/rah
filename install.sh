#!/usr/bin/env bash
# rah installer — put the single-file CLI on PATH. Re-run to upgrade.
#
#   curl -fsSL https://raw.githubusercontent.com/Hiaa1/rah/main/install.sh | bash
#
# or run it from a clone to install the local copy. Then: rah setup
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

is_macos() { [ "$(uname -s 2>/dev/null || echo unknown)" = Darwin ]; }

interactive() { ( : >/dev/tty ) 2>/dev/null; }

confirm() {
  [ "${RAH_YES:-0}" = 1 ] && return 0
  interactive || return 1
  local ans=""
  printf '%s [Y/n] ' "$1" >/dev/tty
  IFS= read -r ans </dev/tty || true
  case "$ans" in [nN]*) return 1 ;; *) return 0 ;; esac
}

path_profile() {
  case "$(basename "${SHELL:-}")" in
    zsh)  printf '%s\n' "$HOME/.zshrc" ;;
    bash)
      if is_macos; then printf '%s\n' "$HOME/.bash_profile"; else printf '%s\n' "$HOME/.bashrc"; fi ;;
    *)    printf '%s\n' "$HOME/.profile" ;;
  esac
}

ensure_path() {
  case ":$PATH:" in
    *":$BIN_DIR:"*) return 0 ;;
  esac

  warn "$BIN_DIR is not on PATH"
  cmd "export PATH=\"$BIN_DIR:\$PATH\""

  local profile line
  profile="$(path_profile)"
  line="export PATH=\"$BIN_DIR:\$PATH\""
  if [ "${RAH_UPDATE_PROFILE:-ask}" != never ] && confirm "add $BIN_DIR to PATH in $profile?"; then
    mkdir -p "$(dirname "$profile")"
    touch "$profile"
    if grep -F "$BIN_DIR" "$profile" >/dev/null 2>&1; then
      ok "$profile already mentions $BIN_DIR"
    else
      {
        printf '\n# rah\n'
        printf '%s\n' "$line"
      } >> "$profile"
      ok "updated $profile"
      note "Open a new terminal, or run:"
      cmd "source \"$profile\""
    fi
  fi
}

macos_sshfs_note() {
  local method="${1:-manual}" tool="${2:-}"
  header "macOS sshfs dependency"
  warn "sshfs is not installed"
  case "$method" in
    brew)
      cmd "$tool install --cask sshfs-mac"
      note "sshfs-mac installs the macFUSE-backed SSHFS runtime." ;;
    macports)
      cmd "sudo $tool install sshfs"
      note "MacPorts installs SSHFS and its macFUSE dependency." ;;
    *)
      cmd "open https://macfuse.github.io/"
      cmd "open https://github.com/macfuse/macfuse/wiki/File-Systems-%E2%80%90-SSHFS"
      note "Install macFUSE first, then install the signed SSHFS package for macFUSE." ;;
  esac
  note "macFUSE may require approval in System Settings before the first mount works."
}

find_brew() {
  command -v brew 2>/dev/null && return 0
  [ -x /opt/homebrew/bin/brew ] && { printf '%s\n' /opt/homebrew/bin/brew; return 0; }
  [ -x /usr/local/bin/brew ] && { printf '%s\n' /usr/local/bin/brew; return 0; }
  return 1
}

find_port() {
  command -v port 2>/dev/null && return 0
  [ -x /opt/local/bin/port ] && { printf '%s\n' /opt/local/bin/port; return 0; }
  return 1
}

find_sshfs() {
  command -v sshfs 2>/dev/null && return 0
  [ -x /opt/homebrew/bin/sshfs ] && { printf '%s\n' /opt/homebrew/bin/sshfs; return 0; }
  [ -x /usr/local/bin/sshfs ] && { printf '%s\n' /usr/local/bin/sshfs; return 0; }
  [ -x /opt/local/bin/sshfs ] && { printf '%s\n' /opt/local/bin/sshfs; return 0; }
  return 1
}

macos_installer_choice() {
  local want="${RAH_MACOS_SSHFS_INSTALLER:-auto}" brew="" port=""
  case "$want" in
    brew|homebrew)
      if brew="$(find_brew 2>/dev/null)"; then
        printf 'brew:%s\n' "$brew"
      else
        printf 'manual:\n'
      fi ;;
    port|macports)
      if port="$(find_port 2>/dev/null)"; then
        printf 'macports:%s\n' "$port"
      else
        printf 'manual:\n'
      fi ;;
    skip|manual|none)
      printf 'manual:\n' ;;
    auto|"")
      if brew="$(find_brew 2>/dev/null)"; then
        printf 'brew:%s\n' "$brew"
      elif port="$(find_port 2>/dev/null)"; then
        printf 'macports:%s\n' "$port"
      else
        printf 'manual:\n'
      fi ;;
    *)
      printf 'manual:\n' ;;
  esac
}

maybe_install_macos_sshfs() {
  is_macos || return 0
  command -v sshfs >/dev/null 2>&1 && { ok "macOS sshfs dependency present"; return 0; }

  local sshfs_path choice method tool want
  if sshfs_path="$(find_sshfs 2>/dev/null)"; then
    warn "sshfs exists but is not on PATH"
    cmd "export PATH=\"$(dirname "$sshfs_path"):\$PATH\""
    note "Run rah doctor after updating PATH."
    return 0
  fi

  choice="$(macos_installer_choice)"
  method="${choice%%:*}"
  tool="${choice#*:}"
  want="${RAH_MACOS_SSHFS_INSTALLER:-auto}"
  case "$want:$method" in
    brew:manual|homebrew:manual) warn "Homebrew was requested but is not installed" ;;
    port:manual|macports:manual) warn "MacPorts was requested but is not installed" ;;
    auto:*|manual:*|skip:*|none:*) ;;
    *) [ "$method" = manual ] && warn "unknown RAH_MACOS_SSHFS_INSTALLER=$want; use auto, brew, macports, or manual" ;;
  esac
  macos_sshfs_note "$method" "$tool"
  case "$method" in
    brew)
      if confirm "install sshfs-mac now with Homebrew?"; then
        "$tool" install --cask sshfs-mac
      fi ;;
    macports)
      if confirm "install sshfs now with MacPorts?"; then
        sudo "$tool" install sshfs
      fi ;;
    *)
      case "$want" in
        manual|skip|none) note "Use the manual macFUSE + SSHFS installers above." ;;
        *)                note "No supported package manager found; use the manual macFUSE + SSHFS installers above." ;;
      esac ;;
  esac

  if command -v sshfs >/dev/null 2>&1; then
    ok "sshfs installed"
  else
    warn "sshfs is still not ready; finish any install/approval/PATH steps, then run: rah doctor"
  fi
}

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
  *) ensure_path ;;
esac

maybe_install_macos_sshfs

header "Next"
if command -v rah >/dev/null 2>&1; then
  cmd "rah setup"
else
  cmd "$DEST setup"
fi
note "On Ubuntu/Debian/WSL2, rah setup can offer apt installs; on macOS it checks Homebrew, MacPorts, or manual sshfs/macFUSE paths."
