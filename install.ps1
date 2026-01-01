# UltraDL Pro (cross-platform) installer for Windows
# Requires: Python 3.9+ and pipx (recommended)

$ErrorActionPreference = "Stop"

Write-Host "Installing UltraDL Pro (Python CLI: ultradl-pro)..."

# Ensure pipx exists
$pipx = Get-Command pipx -ErrorAction SilentlyContinue
if (-not $pipx) {
  Write-Host "pipx not found. Installing pipx for current user..."
  python -m pip install --user -U pipx
  python -m pipx ensurepath
  $env:Path = [System.Environment]::GetEnvironmentVariable('Path','User') + ';' + [System.Environment]::GetEnvironmentVariable('Path','Machine')
}

# Install from this folder
pipx install . --force

Write-Host "Done. Open a new terminal and run: ultradl-pro --help"
