[CmdletBinding()]
param(
    [switch]$SkipGlobalAutoRouting,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillTarget = Join-Path $HOME ".agents\skills\codex-quota-router"
$AgentTarget = Join-Path $HOME ".codex\agents"
$CodexHome = Join-Path $HOME ".codex"
$GlobalAgentsFile = Join-Path $CodexHome "AGENTS.md"

function Copy-DirectoryClean {
    param([string]$Source, [string]$Destination)
    if ([System.IO.Path]::GetFullPath($Source).TrimEnd('\') -eq [System.IO.Path]::GetFullPath($Destination).TrimEnd('\')) {
        Write-Host "Skill already at canonical path; preserving in-place checkout"
        return
    }
    if (Test-Path $Destination) {
        if (-not $Force) {
            $backup = "$Destination.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
            Copy-Item $Destination $backup -Recurse -Force
            Write-Host "Backed up existing skill to $backup"
        }
        Remove-Item $Destination -Recurse -Force
    }
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    Copy-Item (Join-Path $Source "*") $Destination -Recurse -Force
}

New-Item -ItemType Directory -Path (Split-Path $SkillTarget -Parent) -Force | Out-Null
New-Item -ItemType Directory -Path $AgentTarget -Force | Out-Null
New-Item -ItemType Directory -Path $CodexHome -Force | Out-Null

Copy-DirectoryClean -Source $SourceRoot -Destination $SkillTarget
Copy-Item (Join-Path $SourceRoot "agents\*.toml") $AgentTarget -Force
@("terra-resolver.toml", "terra-guard.toml") | ForEach-Object {
    $legacy = Join-Path $AgentTarget $_
    if (Test-Path $legacy) { Remove-Item $legacy -Force }
}

if (-not $SkipGlobalAutoRouting) {
    $begin = '<!-- BEGIN CODEX_QUOTA_ROUTER -->'
    $end = '<!-- END CODEX_QUOTA_ROUTER -->'
    $block = Get-Content (Join-Path $SourceRoot "snippets\AGENTS.global.md") -Raw
    $existing = if (Test-Path $GlobalAgentsFile) { Get-Content $GlobalAgentsFile -Raw } else { "" }

    if (Test-Path $GlobalAgentsFile) {
        Copy-Item $GlobalAgentsFile "$GlobalAgentsFile.backup.$(Get-Date -Format 'yyyyMMddHHmmss')" -Force
    }

    $pattern = '(?s)<!-- BEGIN CODEX_(?:LUNA_FIRST_ROUTER|QUOTA_ROUTER) -->.*?<!-- END CODEX_(?:LUNA_FIRST_ROUTER|QUOTA_ROUTER) -->'
    if ($existing -match $pattern) {
        $updated = [regex]::Replace($existing, $pattern, $block.Trim())
    } else {
        $separator = if ([string]::IsNullOrWhiteSpace($existing)) { "" } else { "`r`n`r`n" }
        $updated = $existing.TrimEnd() + $separator + $block.Trim() + "`r`n"
    }
    Set-Content -Path $GlobalAgentsFile -Value $updated -Encoding UTF8
}

Write-Host "Installed skill: $SkillTarget"
Write-Host "Installed custom agents: $AgentTarget"
if (-not $SkipGlobalAutoRouting) {
    Write-Host "Enabled global auto-routing in: $GlobalAgentsFile"
}
Write-Host "Restart Codex if the skill or agents do not appear immediately."
Write-Host "Test with: `$codex-quota-router route this task before execution"
