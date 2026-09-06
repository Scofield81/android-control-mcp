#requires -version 5.1
<#
.SYNOPSIS
    Android Control MCP - Windows telepito (per-user, admin jog nelkul).

.DESCRIPTION
    1. Ellenorzi a fuggosegeket (Python, ADB, scrcpy) - csak akkor telepit,
       ha TENYLEG hianyzik, es csak hivatalos forrasokbol (winget:
       Python.Python.3.12 / Google.PlatformTools / Genymobile.scrcpy).
    2. Letrehoz egy sajat, izolalt konyvtarat (alap: %LOCALAPPDATA%\AndroidControlMCP),
       benne sajat venv-vel - NEM piszkitja a felhasznalo mas Python projektjeit.
    3. Letoltoti/hasznalja a repo forraskodjat, telepiti a csomagot a venv-be.
    4. Vegul futtatja a 'doctor' ellenorzest.

    Semmilyen ponton nem nyul Android eszkozhoz, nem kapcsol be ADB-t, nem
    modosit telefon-beallitast.

.PARAMETER InstallDir
    Celkonyvtar. Ha nincs megadva es a szkript interaktivan fut, megkerdezi.

.PARAMETER RepoUrl
    A GitHub repo URL-je (git clone-hoz). Alap: a hivatalos Scofield81/android-control-mcp.

.PARAMETER SkipDependencyInstall
    Ha be van kapcsolva, csak ELLENORZI a fuggosegeket, de sosem telepit hianyzokat -
    ehelyett egyertelmu utmutatast ad, mit kell kezzel telepiteni.

.PARAMETER NonInteractive
    Nem ker interaktiv megerositest - csak akkor hasznald, ha tudod, mit teszel
    (pl. AI-agent scriptelt telepitesnel, ahol a felhasznalo mar elore jovahagyta).

.EXAMPLE
    .\scripts\install_windows.ps1

.EXAMPLE
    .\scripts\install_windows.ps1 -InstallDir "D:\Programok\AndroidControlMCP"
#>
param(
    [string]$InstallDir,
    [string]$RepoUrl = "https://github.com/Scofield81/android-control-mcp.git",
    [switch]$SkipDependencyInstall,
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "    OK: $msg" -ForegroundColor Green }
function Write-Warn2($msg) { Write-Host "    FIGYELEM: $msg" -ForegroundColor Yellow }
function Write-Err2($msg) { Write-Host "    HIBA: $msg" -ForegroundColor Red }

function Confirm-Action($question) {
    if ($NonInteractive) { return $true }
    $answer = Read-Host "$question (i/n)"
    return $answer -match '^[iIyY]'
}

# --- 1. Telepitesi konyvtar ---------------------------------------------
if (-not $InstallDir) {
    $defaultDir = Join-Path $env:LOCALAPPDATA "AndroidControlMCP"
    if ($NonInteractive) {
        $InstallDir = $defaultDir
    } else {
        $answer = Read-Host "Telepitesi mappa [$defaultDir]"
        $InstallDir = if ([string]::IsNullOrWhiteSpace($answer)) { $defaultDir } else { $answer }
    }
}
Write-Step "Telepitesi mappa: $InstallDir"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
$AppDir = Join-Path $InstallDir "app"
$VenvDir = Join-Path $InstallDir "venv"
$ConfigDir = Join-Path $InstallDir "config"
$LogsDir = Join-Path $InstallDir "logs"
New-Item -ItemType Directory -Force -Path $ConfigDir, $LogsDir | Out-Null

# --- 2. Fuggosegek ellenorzese -------------------------------------------
Write-Step "Fuggosegek ellenorzese"

$hasWinget = $null -ne (Get-Command winget -ErrorAction SilentlyContinue)
if (-not $hasWinget) {
    Write-Warn2 "A 'winget' nem talalhato - automatikus fuggoseg-telepites nem lesz elerheto. " `
        "Windows 11-en / friss Windows 10-en altalaban elore telepitve van (App Installer)."
}

# Python
$pythonExe = $null
foreach ($cand in @("python", "python3")) {
    $cmd = Get-Command $cand -ErrorAction SilentlyContinue
    if ($cmd) {
        $verOut = & $cmd.Source --version 2>&1
        if ($verOut -match '(\d+)\.(\d+)\.(\d+)') {
            $maj = [int]$Matches[1]; $min = [int]$Matches[2]
            if ($maj -eq 3 -and $min -ge 10) { $pythonExe = $cmd.Source; break }
        }
    }
}
if ($pythonExe) {
    Write-Ok "Python mar telepitve: $pythonExe"
} else {
    Write-Warn2 "Nem talalhato megfelelo Python (3.10+) a PATH-on."
    if (-not $SkipDependencyInstall -and $hasWinget) {
        if (Confirm-Action "Telepitsem a hivatalos Python 3.12-t winget-tel (Python.Python.3.12, per-user, admin jog nelkul)?") {
            winget install --id Python.Python.3.12 --source winget --scope user `
                --accept-package-agreements --accept-source-agreements
            Write-Warn2 "Uj terminal/PowerShell-ablak (vagy a PATH ujratoltese) szukseges lehet a telepites utan."
            $cmd = Get-Command python -ErrorAction SilentlyContinue
            if ($cmd) { $pythonExe = $cmd.Source }
        }
    }
    if (-not $pythonExe) {
        Write-Err2 "Python nelkul a telepites nem folytathato. Toltsd le innen: https://www.python.org/downloads/ " `
            "(vagy futtasd ujra ezt a szkriptet egy uj terminalban a Python telepitese utan)."
        exit 1
    }
}

# ADB
$adbCmd = Get-Command adb -ErrorAction SilentlyContinue
if ($adbCmd) {
    Write-Ok "ADB mar telepitve: $($adbCmd.Source)"
} else {
    Write-Warn2 "Az 'adb' nem talalhato a PATH-on."
    if (-not $SkipDependencyInstall -and $hasWinget) {
        if (Confirm-Action "Telepitsem a hivatalos Android SDK Platform-Tools csomagot winget-tel (Google.PlatformTools)?") {
            winget install --id Google.PlatformTools --source winget `
                --accept-package-agreements --accept-source-agreements
        }
    } else {
        Write-Warn2 "Kezi telepites: https://developer.android.com/tools/releases/platform-tools"
    }
}

# scrcpy (opcionalis - csak a Rescue/tukrozes funkciohoz kell)
$scrcpyCmd = Get-Command scrcpy -ErrorAction SilentlyContinue
if ($scrcpyCmd) {
    Write-Ok "scrcpy mar telepitve: $($scrcpyCmd.Source)"
} else {
    Write-Warn2 "A 'scrcpy' nem talalhato - ez OPCIONALIS (csak a kepernyo-tukrozes/Rescue mod funkciohoz kell, " `
        "a tobbi ADB-alapu automatizalas nelkule is mukodik)."
    if (-not $SkipDependencyInstall -and $hasWinget) {
        if (Confirm-Action "Telepitsem a hivatalos scrcpy-t winget-tel (Genymobile.scrcpy)?") {
            winget install --id Genymobile.scrcpy --source winget `
                --accept-package-agreements --accept-source-agreements
        }
    }
}

# --- 3. Forraskod beszerzese ----------------------------------------------
Write-Step "Forraskod"
$scriptRoot = Split-Path -Parent $PSScriptRoot
$looksLikeRepo = Test-Path (Join-Path $scriptRoot "pyproject.toml")

if ($looksLikeRepo -and ($scriptRoot -ne $AppDir)) {
    Write-Ok "A szkript egy meglevo repo-bol fut ($scriptRoot) - ezt masoljuk be a telepitesi mappaba " `
        "(fejlesztoi mellektermekek: .venv/.git/cache-ok NELKUL)."
    if (Test-Path $AppDir) { Remove-Item -Recurse -Force $AppDir }
    New-Item -ItemType Directory -Force -Path $AppDir | Out-Null
    # robocopy /MIR tukrozi a forrast, /XD kizarja a fejlesztoi mellektermek-mappakat -
    # igy a masolat nem hurcolja magaval a fejlesztoi venv-et/git-torteneteket/cache-eket.
    robocopy $scriptRoot $AppDir /MIR /NFL /NDL /NJH /NJS `
        /XD ".venv" ".git" ".pytest_cache" ".ruff_cache" "__pycache__" | Out-Null
} elseif (Test-Path (Join-Path $AppDir ".git")) {
    Write-Ok "Mar letezo telepites talalhato itt: $AppDir - frissites (git pull)."
    Push-Location $AppDir
    git pull --ff-only
    Pop-Location
} else {
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if (-not $gitCmd) {
        Write-Err2 "A 'git' nem talalhato, es a szkript sem repo-bol fut. Telepitsd a git-et " `
            "(hivatalos: https://git-scm.com/downloads), vagy toltsd le kezzel a repo ZIP-jet ide: $AppDir"
        exit 1
    }
    Write-Step "Klonozas: $RepoUrl -> $AppDir"
    git clone $RepoUrl $AppDir
}

# --- 4. Sajat, izolalt venv -----------------------------------------------
Write-Step "Python virtualis kornyezet: $VenvDir"
if (-not (Test-Path $VenvDir)) {
    & $pythonExe -m venv $VenvDir
    Write-Ok "venv letrehozva."
} else {
    Write-Ok "venv mar letezik, ujrahasznositva."
}
$venvPython = Join-Path $VenvDir "Scripts\python.exe"

Write-Step "Android Control MCP telepitese a venv-be"
& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install $AppDir --quiet
Write-Ok "Telepitve."

# --- 5. Telepitesi allapot elmentese (a configure/doctor szamara) --------
$installInfo = @{
    install_dir  = $InstallDir
    app_dir      = $AppDir
    venv_python  = $venvPython
    installed_at = (Get-Date).ToString("o")
}
$installInfo | ConvertTo-Json | Set-Content -Path (Join-Path $ConfigDir "install_info.json") -Encoding utf8

# --- 6. Doctor ellenorzes --------------------------------------------------
Write-Step "Diagnosztika (doctor)"
& $venvPython -m android_control_mcp doctor

Write-Host ""
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host " Telepites kesz: $InstallDir" -ForegroundColor Cyan
Write-Host " Szerver inditasa kezzel:" -ForegroundColor Cyan
Write-Host "   `"$venvPython`" -m android_control_mcp" -ForegroundColor Cyan
Write-Host " MCP kliens beallitasahoz:" -ForegroundColor Cyan
Write-Host "   `"$venvPython`" -m android_control_mcp configure" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
