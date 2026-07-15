[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoUrl,

    [string]$InstallRoot = (Get-Location).Path,

    [ValidateSet("codex", "claude", "opencode", "all")]
    [string]$Agent = "all",

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

function Find-Python {
    if (Test-CommandAvailable "py") {
        try {
            & py -3.12 --version | Out-Null
            if ($LASTEXITCODE -eq 0) {
                return @{ Command = "py"; PrefixArgs = @("-3.12") }
            }
        }
        catch {
        }
    }
    foreach ($candidate in @("python3.12", "python", "python3")) {
        if (-not (Test-CommandAvailable $candidate)) {
            continue
        }
        try {
            & $candidate --version | Out-Null
            if ($LASTEXITCODE -eq 0) {
                return @{ Command = $candidate; PrefixArgs = @() }
            }
        }
        catch {
        }
    }
    throw "Python 3.12 was not found. Install Python >=3.12 and rerun this script."
}

function Invoke-Python {
    param(
        [hashtable]$Python,
        [string[]]$Arguments
    )
    & $Python.Command @($Python.PrefixArgs + $Arguments)
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed: $($Arguments -join ' ')"
    }
}

function Invoke-Checked {
    param(
        [string]$Command,
        [string[]]$Arguments
    )
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
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
Invoke-Checked -Command $cliPath -Arguments @("init", "--workspace", $projectPath, "--agent", $Agent)

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
Write-Host "Codex/OpenCode Skill: $(Join-Path $projectPath '.agents\skills\career-resume-tailor')"
Write-Host "Claude Skill: $(Join-Path $projectPath '.claude\plugins\career-resume-tailor')"
