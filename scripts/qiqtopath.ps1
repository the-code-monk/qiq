# ====================================================
# Add QiQ path to environment
# ====================================================

param (
    [string]$AddPath = "C:\qiq"
)

# Check if running as administrator
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# Decide scope
if ($IsAdmin) {
    $Scope = "Machine"  # system-wide
} else {
    $Scope = "User"     # current user only
}

# Read current PATH
$CurrentPath = [Environment]::GetEnvironmentVariable("Path", $Scope)

# Add only if not already present
if ($CurrentPath -notlike "*$AddPath*") {
    $NewPath = "$CurrentPath;$AddPath"
    [Environment]::SetEnvironmentVariable("Path", $NewPath, $Scope)
    Write-Host "Added '$AddPath' to $Scope PATH."
} else {
    Write-Host "'$AddPath' already exists in $Scope PATH."
}