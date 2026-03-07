#!/usr/bin/env bash
# postmortem installer
# Installs postmortem into an isolated virtualenv at ~/.postmortem
# and symlinks the binary into ~/.local/bin so it's on your $PATH.
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/phlx0/postmortem/main/install.sh | bash
#   or
#   ./install.sh

set -euo pipefail

INSTALL_DIR="${POSTMORTEM_HOME:-$HOME/.postmortem}"
BIN_DIR="${POSTMORTEM_BIN:-$HOME/.local/bin}"
REPO_URL="https://github.com/phlx0/postmortem"
PYPI_NAME="postmortem"

# ── colours ──────────────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
  RED="\033[31m"; GREEN="\033[32m"; YELLOW="\033[33m"
  CYAN="\033[36m"; BOLD="\033[1m"; RESET="\033[0m"
else
  RED="" GREEN="" YELLOW="" CYAN="" BOLD="" RESET=""
fi

info()    { echo -e "${CYAN}${BOLD}→${RESET} $*"; }
success() { echo -e "${GREEN}${BOLD}✓${RESET} $*"; }
warn()    { echo -e "${YELLOW}${BOLD}!${RESET} $*"; }
die()     { echo -e "${RED}${BOLD}✗${RESET} $*" >&2; exit 1; }

# ── checks ────────────────────────────────────────────────────────────────────
check_python() {
  for py in python3.12 python3.11 python3; do
    if command -v "$py" &>/dev/null; then
      version=$("$py" -c 'import sys; print(sys.version_info[:2])')
      if "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null; then
        PYTHON="$py"
        return
      fi
    fi
  done
  die "Python 3.11+ is required. Please install it from https://python.org"
}

check_git() {
  command -v git &>/dev/null || die "git is required but not installed."
}

# ── install ───────────────────────────────────────────────────────────────────
do_install() {
  info "Installing postmortem into ${INSTALL_DIR} …"

  # Create virtualenv
  "$PYTHON" -m venv "$INSTALL_DIR"
  success "Created virtualenv at $INSTALL_DIR"

  # If we're running from a local clone (dev mode), install editable
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [[ -f "$SCRIPT_DIR/pyproject.toml" ]]; then
    info "Local source detected — installing in editable mode"
    "$INSTALL_DIR/bin/pip" install --quiet --upgrade pip
    "$INSTALL_DIR/bin/pip" install --quiet -e "$SCRIPT_DIR"
    success "Installed in editable mode (changes apply instantly)"
  else
    info "Installing from PyPI …"
    "$INSTALL_DIR/bin/pip" install --quiet --upgrade pip
    "$INSTALL_DIR/bin/pip" install --quiet "$PYPI_NAME"
    success "Installed $PYPI_NAME from PyPI"
  fi

  # Symlink binary
  mkdir -p "$BIN_DIR"
  ln -sf "$INSTALL_DIR/bin/postmortem" "$BIN_DIR/postmortem"
  success "Symlinked postmortem → $BIN_DIR/postmortem"
}

# ── PATH check ────────────────────────────────────────────────────────────────
check_path() {
  if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    warn "$BIN_DIR is not in your \$PATH."
    echo ""
    echo "  Add this to your shell config (~/.bashrc, ~/.zshrc, etc.):"
    echo ""
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "  Then restart your shell or run: source ~/.bashrc"
    echo ""
  else
    success "$BIN_DIR is already in your \$PATH — you're ready!"
  fi
}

# ── uninstall helper ──────────────────────────────────────────────────────────
do_uninstall() {
  info "Removing postmortem …"
  rm -rf "$INSTALL_DIR"
  rm -f "$BIN_DIR/postmortem"
  success "postmortem uninstalled."
}

# ── main ──────────────────────────────────────────────────────────────────────
main() {
  if [[ "${1:-}" == "--uninstall" ]]; then
    do_uninstall
    exit 0
  fi

  echo ""
  echo -e "${BOLD}  postmortem — incident timeline builder${RESET}"
  echo -e "${CYAN}  ${REPO_URL}${RESET}"
  echo ""

  check_python
  check_git
  do_install
  check_path

  echo ""
  success "Done! Try it:"
  echo -e "   ${BOLD}postmortem --since 2h${RESET}"
  echo ""
}

main "$@"
