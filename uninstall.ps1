[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$SkillTarget = Join-Path $HOME ".agents\skills\codex-quota-router"
$AgentTarget = Join-Path $HOME ".codex\agents"
$GlobalAgentsFile = Join-Path $HOME ".codex\AGENTS.md"

if (Test-Path $SkillTarget) {
    Remove-Item $SkillTarget -Recurse -Force
}

@(
    "luna-fast.toml",
    "luna-worker.toml",
    "luna-deep.toml",
    "terra-resolver.toml",
    "terra-guard.toml",
    "sol-architect.toml"
) | ForEach-Object {
    $path = Join-Path $AgentTarget $_
    if (Test-Path $path) { Remove-Item $path -Force }
}

if (Test-Path $GlobalAgentsFile) {
    $begin = '<!-- BEGIN CODEX_LUNA_FIRST_ROUTER -->'
    $end = '<!-- END CODEX_LUNA_FIRST_ROUTER -->'
    $content = Get-Content $GlobalAgentsFile -Raw
    $pattern = "(?s)\s*" + [regex]::Escape($begin) + ".*?" + [regex]::Escape($end) + "\s*"
    $updated = [regex]::Replace($content, $pattern, "`r`n`r`n").Trim()
    Set-Content -Path $GlobalAgentsFile -Value ($updated + "`r`n") -Encoding UTF8
}

Write-Host "Removed codex-quota-router and its managed agent profiles."
