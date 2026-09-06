#requires -version 5.1
<#
.SYNOPSIS
    Android Control MCP - Windows eltavolito.

.DESCRIPTION
    Eltavolitja a sajat telepitesi konyvtarat (app/venv/config/logs), amit az
    install_windows.ps1 hozott letre.

    NEM tavolitja el a rendszerszinten telepitett fuggosegeket (Python, ADB,
    scrcpy) - ezeket mas alkalmazasok is hasznalhatjak. Ezekre csak FELAJANLJA
    a kulon eltavolitast, sose torli automatikusan.

.PARAMETER InstallDir
    A telepitesi mappa (amit az install_windows.ps1-nek is megadtal, vagy az
    alapertelmezett %LOCALAPPDATA%\AndroidControlMCP).
#>
param(
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA "AndroidControlMCP")
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }

if (-not (Test-Path $InstallDir)) {
    Write-Host "Nincs mit eltavolitani - a mappa nem letezik: $InstallDir" -ForegroundColor Yellow
    exit 0
}

Write-Step "Android Control MCP eltavolitasa: $InstallDir"
Write-Host "Ez torli:"
Write-Host "  - $InstallDir\app"
Write-Host "  - $InstallDir\venv"
Write-Host "  - $InstallDir\config"
Write-Host "  - $InstallDir\logs"
$answer = Read-Host "Biztosan folytatod? (i/n)"
if ($answer -notmatch '^[iIyY]') {
    Write-Host "Megszakitva."
    exit 0
}

Remove-Item -Recurse -Force $InstallDir
Write-Host "Eltavolitva: $InstallDir" -ForegroundColor Green

Write-Host ""
Write-Host "MEGJEGYZES: a rendszerszinten telepitett fuggosegeket (Python, ADB, scrcpy) " `
    "EZ A SZKRIPT SZANDEKOSAN NEM tavolitotta el, mert mas alkalmazasok is hasznalhatjak oket."
Write-Host "Ha ezeket is el szeretned tavolitani, kezzel teheted meg (pl.):"
Write-Host "  winget uninstall Genymobile.scrcpy"
Write-Host "  winget uninstall Google.PlatformTools"
Write-Host "  winget uninstall Python.Python.3.12"
Write-Host ""
Write-Host "Az MCP kliens-konfiguraciodbol (VS Code .vscode/mcp.json, 'claude mcp remove android-control' " `
    "stb.) az 'android-control' bejegyzest kulon, kezzel kell eltavolitanod - ezt a szkript NEM erinti, " `
    "mert az a te projekt-/felhasznaloi konfiguraciod, nem az install konyvtar resze."
