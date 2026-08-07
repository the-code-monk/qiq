# ====================================================
# Activate Python environment
# ====================================================

# Directory where Python is installed
$env:QIQ_PYTHON_DIR = "XXXXX"

# Check if python.exe exists
if (-not (Test-Path "$env:QIQ_PYTHON_DIR\python.exe")) {
    Write-Host "python.exe not found in $env:QIQ_PYTHON_DIR"
    exit 1
}

# Save original environment variables if not already saved
if (-not $env:ORIG_PATH) {
    $env:ORIG_PATH = $env:PATH
}

if (-not $env:ORIG_PROMPT) {
    $env:ORIG_PROMPT = (Get-Item function:prompt).ScriptBlock.ToString()
}

# Update PATH
$env:PATH = "$env:QIQ_PYTHON_DIR;$env:QIQ_PYTHON_DIR\Scripts;$($env:PATH)"

# Extract major & minor version from folder name for prompt
$env:PYTHON_PROMPT = if ($env:QIQ_PYTHON_DIR -match '(\d+\.\d+)') { "python-" + $matches[1] } else { $env:QIQ_PYTHON_DIR }

# Change PowerShell prompt
function prompt {
    $esc = [char]27

    $app = "${esc}[1;32m(QiQ)${esc}[0m"

    $py = ""
    if ($env:PYTHON_PROMPT) {
        $py = "${esc}[1;34m($env:PYTHON_PROMPT)${esc}[0m"
    }

    $user = $env:USERNAME
    $hostname = $env:COMPUTERNAME
    $path = (Get-Location).Path

    #"$app $py ${user}@${hostname}:$path`$ "
    "$app $py $path>"
}

Write-Host "Python environment configured"
Write-Host "Python location: $env:QIQ_PYTHON_DIR"

# Show Python version
python --version