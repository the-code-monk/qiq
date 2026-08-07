#!/bin/bash
# ====================================================
# Deactivate Python environment
# ====================================================

# Check if ORIG_PATH exists
if [ -z "$ORIG_PATH" ]; then
    echo "No Python environment is active."
    return 0 2>/dev/null || exit 0
fi

# Restore original PATH
export PATH="$ORIG_PATH"

# Restore original prompt
if [ -n "$ORIG_PROMPT" ]; then
    export PS1="$ORIG_PROMPT"
fi

# Unset Python-related variables
unset QIQ_PYTHON_DIR
unset PYTHON_EXE
unset PYTHON_PROMPT
unset ORIG_PATH
unset ORIG_PROMPT

echo "Python environment deactivated."