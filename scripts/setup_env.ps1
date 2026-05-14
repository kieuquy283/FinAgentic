$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Run-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [string[]]$Args = @()
    )
    & $Command @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $Command $($Args -join ' ')"
    }
}

Write-Host "== Backend setup =="
if (-not (Test-Path ".venv")) {
    Run-Step "python" @("-m", "venv", ".venv")
}

& ".\.venv\Scripts\Activate.ps1"
Run-Step "python" @("-m", "pip", "install", "--upgrade", "pip")
Run-Step "python" @("-m", "pip", "install", "-r", "backend\requirements.txt")
Run-Step "python" @("backend\scripts\seed_data.py")
Run-Step "python" @("-m", "pytest", "-q", "backend\tests")

Write-Host "== Frontend setup =="
Push-Location "frontend"
Run-Step "npm" @("install")
Run-Step "npm" @("run", "build")
Pop-Location

Write-Host "Setup completed successfully."
