# sync-tools.ps1 - One-command sync from local tool repos to the hub
#
# Walks each subfolder in public/, looks for a matching ~/<name>/index.html,
# and copies it in. Commits + pushes if anything changed.
#
# Usage:
#   .\sync-tools.ps1                    # sync, commit, push
#   .\sync-tools.ps1 -DryRun            # show what would change, no commit
#   .\sync-tools.ps1 -NoPush            # commit but don't push (review locally first)
#   .\sync-tools.ps1 -Tools verse-vault # sync just one tool
#
# After running, Vercel auto-redeploys in ~30 sec.

param(
    [switch]$DryRun,
    [switch]$NoPush,
    [string[]]$Tools
)

$ErrorActionPreference = "Stop"
$HubRoot = $PSScriptRoot
$PublicDir = Join-Path $HubRoot "public"
$HomeRoot = "C:\Users\elija"

if (-not (Test-Path $PublicDir)) {
    Write-Host "ERROR: public/ not found at $PublicDir" -ForegroundColor Red
    exit 1
}

$NonToolDirs = @("icons", "assets", "static")

if ($Tools) {
    $toolList = $Tools
} else {
    $toolList = Get-ChildItem -Path $PublicDir -Directory | Where-Object { $_.Name -notin $NonToolDirs } | ForEach-Object { $_.Name }
}

$changed = 0
$skipped = 0
$missing = @()

foreach ($tool in $toolList) {
    $srcPath = Join-Path $HomeRoot "$tool\index.html"
    $dstPath = Join-Path $PublicDir "$tool\index.html"

    if (-not (Test-Path $srcPath)) {
        $missing += $tool
        continue
    }

    if (-not (Test-Path $dstPath)) {
        Write-Host "  NEW    $tool" -ForegroundColor Yellow
        if (-not $DryRun) {
            New-Item -ItemType Directory -Path (Split-Path $dstPath) -Force | Out-Null
            Copy-Item $srcPath $dstPath
        }
        $changed++
        continue
    }

    $srcHash = (Get-FileHash $srcPath).Hash
    $dstHash = (Get-FileHash $dstPath).Hash

    if ($srcHash -eq $dstHash) {
        $skipped++
        continue
    }

    $srcSize = (Get-Item $srcPath).Length
    $dstSize = (Get-Item $dstPath).Length
    $diff = $srcSize - $dstSize
    $diffStr = if ($diff -ge 0) { "+$diff" } else { "$diff" }
    Write-Host "  CHANGE $tool  ($diffStr bytes)" -ForegroundColor Green

    if (-not $DryRun) {
        Copy-Item $srcPath $dstPath -Force
    }
    $changed++
}

Write-Host ""
Write-Host "$changed changed - $skipped unchanged - $($missing.Count) missing source" -ForegroundColor Cyan

if ($missing.Count -gt 0 -and $missing.Count -lt 10) {
    Write-Host "  Missing source files for:" -ForegroundColor DarkGray
    $missing | ForEach-Object { Write-Host "    ~/$_/index.html" -ForegroundColor DarkGray }
}

if ($DryRun) {
    Write-Host "DRY RUN - no files written, no git operations." -ForegroundColor Yellow
    exit 0
}

if ($changed -eq 0) {
    Write-Host "Nothing to commit." -ForegroundColor Cyan
    exit 0
}

Push-Location $HubRoot
try {
    git add public/
    $msg = "Sync $changed tool(s) from local repos"
    git commit -q -m $msg
    Write-Host "Committed: $msg" -ForegroundColor Cyan

    if (-not $NoPush) {
        $pushExitCode = 0
        $pushOutput = git push 2>&1
        $pushExitCode = $LASTEXITCODE
        if ($pushExitCode -eq 0) {
            Write-Host "Pushed. Vercel will auto-redeploy in ~30 sec." -ForegroundColor Green
        } else {
            Write-Host "Push failed:" -ForegroundColor Red
            $pushOutput | Write-Host
        }
    } else {
        Write-Host "Skipped push (-NoPush flag)." -ForegroundColor Yellow
    }
} finally {
    Pop-Location
}
