#!/usr/bin/env bash

# ====================================================
# Activate Python environment
# ====================================================

set -e

# Current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect user's login shell
SHELL_NAME="$(basename "${SHELL:-}")"

case "$SHELL_NAME" in
  bash)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        SHELL_RC="$HOME/.bash_profile"
    else
        SHELL_RC="$HOME/.bashrc"
    fi
    ;;
  zsh)
    SHELL_RC="$HOME/.zshrc"
    ;;
  fish)
    SHELL_RC="$HOME/.config/fish/config.fish"
    ;;
  *)
    echo "Unsupported shell: $SHELL_NAME"
    exit 1
    ;;
esac

# Ensure rc file exists
touch "$SHELL_RC"

# Define PATH line
PATH_LINE="export PATH=\"$SCRIPT_DIR:\$PATH\""

# Check if already added (exact match safer)
if grep -Fq "$SCRIPT_DIR" "$SHELL_RC"; then
    echo "Path already exists in $SHELL_RC"
else
    {
        echo ""
        echo "# Added by install.sh"
        echo "$PATH_LINE"
    } >> "$SHELL_RC"

    echo "Added PATH to $SHELL_RC"
fi

# Optional: ensure bash loads .bashrc on macOS
if [[ "$SHELL_NAME" == "bash" && "$OSTYPE" == "darwin"* ]]; then
    if ! grep -q ".bashrc" "$HOME/.bash_profile" 2>/dev/null; then
        echo '[[ -f ~/.bashrc ]] && source ~/.bashrc' >> "$HOME/.bash_profile"
    fi
fi

# Converts CRLF → LF
sed -i 's/\r$//' qiq
# Make qiq executable
chmod +x qiq

# Done
echo "Installation complete."
echo "Run: source $SHELL_RC or restart your terminal to apply changes."