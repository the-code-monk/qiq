#!/bin/bash
# ====================================================
# Activate Python environment
# ====================================================

# Directory where Python is installed
export QIQ_PYTHON_DIR="XXXXX"

# Check if python exists
if [ ! -f "$QIQ_PYTHON_DIR/bin/pythonYYYYY" ]; then
    echo "python not found in $QIQ_PYTHON_DIR"
    unset QIQ_PYTHON_DIR
    return 0
fi

# Save original environment variables if not already saved
if [ -z "$ORIG_PATH" ]; then
    export ORIG_PATH="$PATH"
fi

if [ -z "$ORIG_PROMPT" ]; then
    export ORIG_PROMPT="$PS1"
fi

# Set Python Executable
export PYTHON_EXE="pythonYYYYY"

export PATH="$QIQ_PYTHON_DIR/bin:$PATH"

PYTHON_PROMPT="python-YYYYY"
# Change prompt
unset PROMPT_COMMAND

# Detect user's login shell (portable)
SHELL_NAME="$(basename "$SHELL")"

if [[ "$SHELL_NAME" == "zsh" ]]; then
    export PS1="%F{green}(QiQ)%f%F{blue}(${PYTHON_PROMPT})%f %n@%m:%~%# "
else
    export PS1="\[\033[1;32m\](QiQ)\[\033[0m\]\[\033[1;34m\](${PYTHON_PROMPT})\[\033[0m\] \u@\h:\w\$ "
fi

echo "Python environment configured"
echo "Python location: $QIQ_PYTHON_DIR"

$QIQ_PYTHON_DIR/bin/pythonYYYYY --version

# Create an alias to access pythonx.xx as python
alias python=pythonYYYYY