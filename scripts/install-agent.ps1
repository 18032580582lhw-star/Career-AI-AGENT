[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoUrl,

    [string]$InstallRoot = (Get-Location).Path,

    [string]$CheckoutDir = "",

    [switch]$Update,

    [switch]$SkipEval
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message"
}

function Get-RepoName {
    param([string]$Url)
    $trimmed = $Url.TrimEnd("/")
    $leaf = $trimmed.Split("/")[-1]
    if ($leaf.EndsWith(".git", [System.StringComparison]::OrdinalIgnoreCase)) {
        return $leaf.Substring(0, $leaf.Length - 4)
    }
    return $leaf
}

function Test-CommandAvailable {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Invoke-Native {
    param(
        [string]$Command,
        [string[]]$Arguments,
        [switch]$Quiet
    )
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        if ($Quiet) {
            & $Command @Arguments *> $null
        }
        else {
            & $Command @Arguments
        }
        $script:InstallAgentLastNativeExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

function Find-Python {
    if (Test-CommandAvailable "py") {
        Invoke-Native -Command "py" -Arguments @("-3.12", "--version") -Quiet
        if ($script:InstallAgentLastNativeExitCode -eq 0) {
            return @{ Command = "py"; PrefixArgs = @("-3.12") }
        }
    }
    foreach ($candidate in @("python3.12", "python", "python3")) {
        if (-not (Test-CommandAvailable $candidate)) {
            continue
        }
        Invoke-Native -Command $candidate -Arguments @("--version") -Quiet
        if ($script:InstallAgentLastNativeExitCode -eq 0) {
            return @{ Command = $candidate; PrefixArgs = @() }
        }
    }
    throw "Python 3.12 was not found. Install Python >=3.12 and rerun this script."
}

function Invoke-Python {
    param(
        [hashtable]$Python,
        [string[]]$Arguments
    )
    Invoke-Native -Command $Python.Command -Arguments @($Python.PrefixArgs + $Arguments)
    if ($script:InstallAgentLastNativeExitCode -ne 0) {
        throw "Python command failed: $($Arguments -join ' ')"
    }
}

function Invoke-Checked {
    param(
        [string]$Command,
        [string[]]$Arguments
    )
    Invoke-Native -Command $Command -Arguments $Arguments
    if ($script:InstallAgentLastNativeExitCode -ne 0) {
        throw "Command failed: $Command $($Arguments -join ' ')"
    }
}

if (-not (Test-CommandAvailable "git")) {
    throw "Git was not found. Install Git and rerun this script."
}

$repoName = if ($CheckoutDir) { $CheckoutDir } else { Get-RepoName -Url $RepoUrl }
if (-not $repoName) {
    throw "Could not derive checkout directory from RepoUrl. Pass -CheckoutDir explicitly."
}

$rootPath = [System.IO.Path]::GetFullPath($InstallRoot)
$projectPath = [System.IO.Path]::GetFullPath((Join-Path $rootPath $repoName))
$venvPath = Join-Path $projectPath ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$cliPath = Join-Path $venvPath "Scripts\career-ai-agent.exe"

Write-Step "Preparing install root"
New-Item -ItemType Directory -Force -Path $rootPath | Out-Null

if (Test-Path -LiteralPath $projectPath) {
    if (-not (Test-Path -LiteralPath (Join-Path $projectPath ".git"))) {
        throw "Checkout path exists but is not a Git repository: $projectPath"
    }
    Write-Step "Using existing checkout: $projectPath"
    if ($Update) {
        Invoke-Checked -Command "git" -Arguments @("-C", $projectPath, "pull", "--ff-only")
    }
}
else {
    Write-Step "Cloning repository"
    Invoke-Checked -Command "git" -Arguments @("clone", $RepoUrl, $projectPath)
}

$python = Find-Python
if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Step "Creating virtual environment"
    Invoke-Python -Python $python -Arguments @("-m", "venv", $venvPath)
}

Write-Step "Installing package"
Invoke-Checked -Command $venvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip")
Push-Location -LiteralPath $projectPath
try {
    Invoke-Checked -Command $venvPython -Arguments @("-m", "pip", "install", "-e", ".")
}
finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $cliPath)) {
    throw "career-ai-agent executable was not created: $cliPath"
}

Write-Step "Running doctor"
Invoke-Checked -Command $cliPath -Arguments @("doctor")

Write-Step "Installing host Skill adapters"
$initOutput = & $cliPath init --workspace $projectPath --agent all
if ($LASTEXITCODE -ne 0) {
    throw "Command failed: $cliPath init --workspace $projectPath --agent all"
}
$initResult = ($initOutput -join "`n") | ConvertFrom-Json
$installations = @($initResult.installations)
$installedAgents = @($installations.agent | Sort-Object -Unique)
if (
    $installations.Count -ne 2 -or
    $installedAgents.Count -ne 2 -or
    $installedAgents[0] -ne "claude" -or
    $installedAgents[1] -ne "codex"
) {
    throw "init did not report exactly one Codex Skill and one Claude Skill installation."
}
$expectedTargets = @{
    codex = [System.IO.Path]::GetFullPath(
        (Join-Path $projectPath ".agents\skills\career-resume-tailor")
    )
    claude = [System.IO.Path]::GetFullPath(
        (Join-Path $projectPath ".claude\skills\career-resume-tailor")
    )
}
foreach ($installation in $installations) {
    if ([System.IO.Path]::GetFullPath($installation.target) -ne $expectedTargets[$installation.agent]) {
        throw "init reported an unexpected $($installation.agent) Skill target: $($installation.target)"
    }
}
$initOutput | Write-Host

if (-not $SkipEval) {
    Write-Step "Running eval"
    Invoke-Checked -Command $cliPath -Arguments @(
        "eval",
        "--case-dir",
        (Join-Path $projectPath "evals\career_cases"),
        "--prompt-dir",
        (Join-Path $projectPath "prompts")
    )

    Write-Step "Running eval-matrix"
    Invoke-Checked -Command $cliPath -Arguments @(
        "eval-matrix",
        "--case-dir",
        (Join-Path $projectPath "evals\career_cases"),
        "--prompt-dir",
        (Join-Path $projectPath "prompts")
    )
}

Write-Step "Installed"
Write-Host "Project: $projectPath"
Write-Host "CLI: $cliPath"
Write-Host "Codex Skill: $(Join-Path $projectPath '.agents\skills\career-resume-tailor')"
Write-Host "Claude Skill: $(Join-Path $projectPath '.claude\skills\career-resume-tailor')"
