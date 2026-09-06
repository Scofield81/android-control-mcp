#requires -version 5.1
<#
.SYNOPSIS
    Android Control MCP - Windows telepito (per-user, admin jog nelkul).

.DESCRIPTION
    1. Ellenorzi a fuggosegeket (Python, ADB, scrcpy) - csak akkor telepit,
       ha TENYLEG hianyzik, es csak hivatalos forrasokbol (winget:
       Python.Python.3.12 / Google.PlatformTools / Genymobile.scrcpy).
    2. VESZELYES CELUTVONALAKAT VISSZAUTASIT (drive root, rendszer-/profil-
       konyvtar, a forras-repository gyokere/tartalmazasa) - lasd InstallCommon.ps1.
    3. Letrehoz egy sajat, izolalt konyvtarat, benne sajat venv-vel - NEM
       piszkitja a felhasznalo mas Python projektjeit.
    4. Fejlesztoi repo-bol inditva KIZAROLAG a git altal TRACKELT fajlokat
       masolja at (privat *.local.md/.env fajlok SOSE keruljenek at).
    5. Minden natic parancs (winget/git/pip/venv) exit code-jat ellenorzi -
       hiba eseten AZONNAL leall, nem jelent hamis sikert.
    6. Ir egy telepitesi MARKER fajlt (.android-control-mcp-install.json),
       amit az uninstaller validal, mielott barmit torolne.
    7. Vegul futtatja a 'doctor' ellenorzest.

    Semmilyen ponton nem nyul Android eszkozhoz, nem kapcsol be ADB-t, nem
    modosit telefon-beallitast.

.PARAMETER InstallDir
    Celkonyvtar. Ha nincs megadva es a szkript interaktivan fut, megkerdezi.
    Veszelyes celutvonalak (drive root, rendszerkonyvtar, a forras-repo gyokere/
    tartalmazasa) VISSZAUTASITASRA kerulnek, meg NonInteractive modban is.

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
. "$PSScriptRoot\InstallCommon.ps1"

function Confirm-Action($question) {
    if ($NonInteractive) { return $true }
    $answer = Read-Host "$question (i/n)"
    return $answer -match '^[iIyY]'
}

# --- 0. Forras-repository gyokere (veszelyes-cel-ellenorzeshez kell) -------
$scriptRoot = Split-Path -Parent $PSScriptRoot
$looksLikeRepo = Test-Path (Join-Path $scriptRoot "pyproject.toml")
$repoRootForGuard = if ($looksLikeRepo) { $scriptRoot } else { $null }

# --- 1. Telepitesi konyvtar: bekerdezes + VESZELYES-CEL ELLENORZES ---------
$defaultDir = Join-Path $env:LOCALAPPDATA "AndroidControlMCP"

if (-not $InstallDir) {
    if ($NonInteractive) {
        $InstallDir = $defaultDir
    } else {
        $answer = Read-Host "Telepitesi mappa [$defaultDir]"
        $InstallDir = if ([string]::IsNullOrWhiteSpace($answer)) { $defaultDir } else { $answer }
    }
}

$maxAttempts = 5
$attempt = 0
$canonicalInstallDir = $null
while ($true) {
    $attempt++
    $canonicalInstallDir = Get-CanonicalPath $InstallDir
    $dangerReason = Test-DangerousInstallPath -CanonicalPath $canonicalInstallDir -RepoRoot $repoRootForGuard

    if (-not $dangerReason) { break }

    Write-Err2 "Nem biztonsagos telepitesi cel: $dangerReason"
    if ($NonInteractive -or $attempt -ge $maxAttempts) {
        Write-Err2 "Telepites megszakitva - nem sikerult biztonsagos celutvonalat megallapitani."
        exit 1
    }
    $answer = Read-Host "Adj meg egy MASIK telepitesi mappat (alap: $defaultDir)"
    $InstallDir = if ([string]::IsNullOrWhiteSpace($answer)) { $defaultDir } else { $answer }
}

$InstallDir = $canonicalInstallDir
Write-Step "Telepitesi mappa: $InstallDir"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
$AppDir = Get-CanonicalPath (Join-Path $InstallDir "app")
$VenvDir = Get-CanonicalPath (Join-Path $InstallDir "venv")
$ConfigDir = Join-Path $InstallDir "config"
$LogsDir = Join-Path $InstallDir "logs"
New-Item -ItemType Directory -Force -Path $ConfigDir, $LogsDir | Out-Null

# Az AppDir-re is fuss le meg egyszer a veszelyes-cel ellenorzes (a forras-repo
# tartalmazasa kulon problemas lehet appDir szintjen is, pl. ha valaki kezzel
# manipulalta volna az InstallDir-t appDir=repoRoot-ra).
$appDirDanger = Test-DangerousInstallPath -CanonicalPath $AppDir -RepoRoot $repoRootForGuard
if ($appDirDanger) {
    Write-Err2 "Nem biztonsagos app-konyvtar: $appDirDanger"
    exit 1
}

# --- 2. Fuggosegek ellenorzese -------------------------------------------
Write-Step "Fuggosegek ellenorzese"

$hasWinget = $null -ne (Get-Command winget -ErrorAction SilentlyContinue)
if (-not $hasWinget) {
    Write-Warn2 "A 'winget' nem talalhato - automatikus fuggoseg-telepites nem lesz elerheto. " `
        "Windows 11-en / friss Windows 10-en altalaban elore telepitve van (App Installer)."
}

# Python
$pythonExe = Find-PythonExecutable
if ($pythonExe) {
    Write-Ok "Python mar telepitve: $pythonExe"
} else {
    Write-Warn2 "Nem talalhato megfelelo Python (3.10+) a PATH-on/ismert helyeken."
    if (-not $SkipDependencyInstall -and $hasWinget) {
        if (Confirm-Action "Telepitsem a hivatalos Python 3.12-t winget-tel (Python.Python.3.12, per-user, admin jog nelkul)?") {
            Invoke-NativeChecked -Description "winget install Python.Python.3.12" -ScriptBlock {
                winget install --id Python.Python.3.12 --exact --source winget --scope user `
                    --accept-package-agreements --accept-source-agreements
            }
            # Robusztus ujra-felderites: NEM csak a PATH-ra tamaszkodunk (friss telepites
            # utan ugyanabban a sessionben ez gyakran meg nem frissul).
            $pythonExe = Find-PythonExecutable
            if (-not $pythonExe) {
                Write-Warn2 "A Python latszolag telepult, de ebben a sessionben meg nem talalhato " `
                    "(PATH/registry/ismert hely alapjan sem). Probald ujraindaitani ezt a szkriptet " `
                    "egy UJ PowerShell-ablakban."
            }
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
            Invoke-NativeChecked -Description "winget install Google.PlatformTools" -ScriptBlock {
                winget install --id Google.PlatformTools --exact --source winget `
                    --accept-package-agreements --accept-source-agreements
            }
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
            Invoke-NativeChecked -Description "winget install Genymobile.scrcpy" -ScriptBlock {
                winget install --id Genymobile.scrcpy --exact --source winget `
                    --accept-package-agreements --accept-source-agreements
            }
        }
    }
}

# --- 3. Forraskod beszerzese (KIZAROLAG git-tracked fajlok fejlesztoi repobol) ---
Write-Step "Forraskod"

if ($looksLikeRepo -and ($scriptRoot -ne $AppDir)) {
    Write-Ok "A szkript egy meglevo repo-bol fut ($scriptRoot) - atmasolas a telepitesi mappaba."
    Copy-TrackedRepoFiles -Source $scriptRoot -Destination $AppDir
} elseif (Test-Path (Join-Path $AppDir ".git")) {
    Write-Ok "Mar letezo telepites talalhato itt: $AppDir - frissites (git pull)."
    Push-Location $AppDir
    try {
        Invoke-NativeChecked -Description "git pull --ff-only" -ScriptBlock {
            git pull --ff-only
        }
    } finally {
        Pop-Location
    }
} else {
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if (-not $gitCmd) {
        Write-Err2 "A 'git' nem talalhato, es a szkript sem repo-bol fut. Telepitsd a git-et " `
            "(hivatalos: https://git-scm.com/downloads), vagy toltsd le kezzel a repo ZIP-jet ide: $AppDir"
        exit 1
    }
    Write-Step "Klonozas: $RepoUrl -> $AppDir"
    Invoke-NativeChecked -Description "git clone $RepoUrl" -ScriptBlock {
        git clone $RepoUrl $AppDir
    }
}

# --- 4. Sajat, izolalt venv -----------------------------------------------
Write-Step "Python virtualis kornyezet: $VenvDir"
if (-not (Test-Path $VenvDir)) {
    Invoke-NativeChecked -Description "python -m venv" -ScriptBlock {
        & $pythonExe -m venv $VenvDir
    }
    Write-Ok "venv letrehozva."
} else {
    Write-Ok "venv mar letezik, ujrahasznositva."
}
$venvPython = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "A venv Python futtathato nem talalhato a vart helyen: $venvPython"
}

Write-Step "Android Control MCP telepitese a venv-be"
Invoke-NativeChecked -Description "pip install --upgrade pip" -ScriptBlock {
    & $venvPython -m pip install --upgrade pip --quiet
}
Invoke-NativeChecked -Description "pip install $AppDir" -ScriptBlock {
    & $venvPython -m pip install $AppDir --quiet
}
Write-Ok "Telepitve."

# --- 5. Telepitesi allapot + MARKER elmentese --------------------------------
$installInfo = @{
    install_dir  = $InstallDir
    app_dir      = $AppDir
    venv_python  = $venvPython
    installed_at = (Get-Date).ToString("o")
}
$installInfo | ConvertTo-Json | Set-Content -Path (Join-Path $ConfigDir "install_info.json") -Encoding utf8

$markerPath = Write-InstallMarker -InstallDir $InstallDir -AppDir $AppDir -VenvDir $VenvDir
Write-Ok "Telepitesi marker irva: $markerPath (ezt validalja az uninstaller, mielott barmit torolne)."

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
Write-Host " Eltavolitas:" -ForegroundColor Cyan
Write-Host "   .\scripts\uninstall_windows.ps1 -InstallDir `"$InstallDir`"" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
