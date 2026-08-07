# ====================================================
# Deactivate Python environment
# ====================================================

# Check if ORIG_PATH exists
if (-not $env:ORIG_PATH) {
    Write-Host "No Python environment is active."
    return
}

# Restore original PATH
$env:PATH = $env:ORIG_PATH

# Restore original prompt
if ($env:ORIG_PROMPT) {
    Invoke-Expression "function prompt { $($env:ORIG_PROMPT) }"
}

# Unset Python-related variables
Remove-Item Env:QIQ_PYTHON_DIR -ErrorAction SilentlyContinue
Remove-Item Env:PYTHON_PROMPT -ErrorAction SilentlyContinue
Remove-Item Env:ORIG_PATH -ErrorAction SilentlyContinue
Remove-Item Env:ORIG_PROMPT -ErrorAction SilentlyContinue

Write-Host "Python environment deactivated."