#requires -version 5.1
<#
.SYNOPSIS
    Android Control MCP - Windows eltavolito (marker-vedett).

.DESCRIPTION
    Eltavolitja a sajat telepitesi konyvtarat (app/venv/config/logs), amit az
    install_windows.ps1 hozott letre.

    BIZTONSAGI VEDELEM (mindket alabbi ellenorzesnek at kell mennie, KULONBEN
    A SZKRIPT MEGTAGADJA A TORLEST - meg kifejezett felhasznaloi megerositessel is):

    1. Veszelyes-cel ellenorzes: drive root, rendszer-/profil-konyvtar, a
       forras-repository gyokere/tartalmazasa SOSE torolheto, meg akkor sem,
       ha egyebkent letezne benne (hibasan/kezzel odarakott) marker fajl.
    2. Telepitesi MARKER validacio: a celkonyvtarban lennie kell egy
       '.android-control-mcp-install.json' fajlnak, aminek 'product_id' mezoje
       PONTOSAN 'android-control-mcp', es 'install_dir' mezoje EGYEZIK a
       tenyleges, canonicalizalt celutvonallal. Ha a marker hianyzik, serult,
       vagy nem egyezik - REFUSE TO DELETE.

    NEM tavolitja el a rendszerszinten telepitett fuggosegeket (Python, ADB,
    scrcpy) - ezeket mas alkalmazasok is hasznalhatjak. Ezekre csak FELAJANLJA
    a kulon eltavolitast, sose torli automatikusan.

.PARAMETER InstallDir
    A telepitesi mappa (amit az install_windows.ps1-nek is megadtal, vagy az
    alapertelmezett %LOCALAPPDATA%\AndroidControlMCP).

.PARAMETER Force
    Csak a megerosito Read-Host promptot hagyja ki - a marker-validaciot ES a
    veszelyes-cel ellenorzest EZ SEM kerulheti meg.
#>
param(
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA "AndroidControlMCP"),
    [switch]$Force
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\InstallCommon.ps1"

$scriptRoot = Split-Path -Parent $PSScriptRoot
$looksLikeRepo = Test-Path (Join-Path $scriptRoot "pyproject.toml")
$repoRootForGuard = if ($looksLikeRepo) { $scriptRoot } else { $null }

# --- 1. Veszelyes-cel ellenorzes (torles ELOTT, marker-ellenorzestol fuggetlenul) ---
$canonicalInstallDir = Get-CanonicalPath $InstallDir
$dangerReason = Test-DangerousInstallPath -CanonicalPath $canonicalInstallDir -RepoRoot $repoRootForGuard
if ($dangerReason) {
    Write-Err2 "REFUSE TO DELETE - nem biztonsagos cel: $dangerReason"
    exit 1
}
$InstallDir = $canonicalInstallDir

if (-not (Test-Path $InstallDir)) {
    Write-Host "Nincs mit eltavolitani - a mappa nem letezik: $InstallDir" -ForegroundColor Yellow
    exit 0
}

# --- 2. Telepitesi MARKER validacio ------------------------------------------
$markerCheck = Test-InstallMarker -CanonicalInstallDir $InstallDir
if (-not $markerCheck.Ok) {
    Write-Err2 "REFUSE TO DELETE - $($markerCheck.Reason)"
    Write-Host ""
    Write-Host "Ez a vedelem azert van, hogy a szkript SOHA ne torolhessen olyan mappat," -ForegroundColor Yellow
    Write-Host "amit nem az install_windows.ps1 hozott letre (pl. veletlenul megadott" -ForegroundColor Yellow
    Write-Host "rossz -InstallDir eseten). Ha biztosan tudod, hogy ez a mappa tenyleg" -ForegroundColor Yellow
    Write-Host "az Android Control MCP telepitese, torold kezzel, vagy telepitsd ujra" -ForegroundColor Yellow
    Write-Host "ugyanide (ez ujra letrehozza a marker fajlt)." -ForegroundColor Yellow
    exit 1
}

Write-Step "Android Control MCP eltavolitasa: $InstallDir"
Write-Ok "Telepitesi marker ervenyes (product_id='$($markerCheck.Marker.product_id)', " `
    "telepitve: $($markerCheck.Marker.installed_at))."

# --- 2b. Sajat MCP kliens-regisztraciok felajanlasa (CSAK amit biztonsagosan tudunk) ---
$regPath = Join-Path $InstallDir "config\mcp_registrations.json"
if (Test-Path $regPath -PathType Leaf) {
    $regData = $null
    try { $regData = Get-Content -Path $regPath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { }
    if ($regData -and $regData.registrations) {
        Write-Step "Sajat MCP kliens-regisztraciok (amiket a 'configure' korabban letrehozott)"
        foreach ($reg in $regData.registrations) {
            $detail = $reg.detail
            if ($detail -and $detail.auto_removable -eq $true -and $detail.config_path -and (Test-Path $detail.config_path -PathType Leaf)) {
                Write-Host "  $($reg.kind)/$($reg.scope) -> $($detail.config_path)"
                $remove = $false
                if (-not $Force) {
                    $ans = Read-Host "  Eltavolitsam az Android Control MCP sajat 'android-control' bejegyzeset ebbol a fajlbol? (i/n)"
                    $remove = $ans -match '^[iIyY]'
                }
                if ($remove) {
                    try {
                        $cfgObj = Get-Content -Path $detail.config_path -Raw -Encoding UTF8 | ConvertFrom-Json
                        if ($cfgObj.servers -and ($cfgObj.servers.PSObject.Properties.Name -contains "android-control")) {
                            $stamp = Get-Date -Format "yyyyMMddTHHmmssZ"
                            $backupPath = "$($detail.config_path).backup-uninstall-$stamp"
                            Copy-Item -Path $detail.config_path -Destination $backupPath -Force
                            $cfgObj.servers.PSObject.Properties.Remove("android-control")
                            ($cfgObj | ConvertTo-Json -Depth 10) | Set-Content -Path $detail.config_path -Encoding utf8
                            Write-Ok "Eltavolitva (biztonsagi mentes: $backupPath)."
                        } else {
                            Write-Ok "Az 'android-control' bejegyzes mar nem talalhato ebben a fajlban - nincs teendo."
                        }
                    } catch {
                        Write-Warn2 "Nem sikerult automatikusan eltavolitani ($($_.Exception.Message)) - " `
                            "torold kezzel az 'android-control' bejegyzest innen: $($detail.config_path)"
                    }
                }
            } elseif ($detail -and $detail.manual_note) {
                Write-Host "  $($reg.kind)/$($reg.scope): kezi eltavolitas szukseges - $($detail.manual_note)" -ForegroundColor Yellow
            }
        }
    }
}

Write-Host "Ez torli:"
Write-Host "  - $InstallDir\app"
Write-Host "  - $InstallDir\venv"
Write-Host "  - $InstallDir\config"
Write-Host "  - $InstallDir\logs"
Write-Host "  - $InstallDir\.android-control-mcp-install.json (marker)"

if (-not $Force) {
    $answer = Read-Host "Biztosan folytatod? (i/n)"
    if ($answer -notmatch '^[iIyY]') {
        Write-Host "Megszakitva."
        exit 0
    }
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
Write-Host "Az MCP kliens-konfiguraciodbol a sajat 'android-control' bejegyzest KULON," -ForegroundColor Yellow
Write-Host "kezzel kell eltavolitanod - ezt a szkript NEM erinti automatikusan (biztonsagi" -ForegroundColor Yellow
Write-Host "okbol: nem kutat at veletlenszeruen mas konfiguraciokat/MCP-szervereket)." -ForegroundColor Yellow
Write-Host "  VS Code:      nyisd meg a '.vscode\mcp.json'-t (vagy a user-config-ot), es" -ForegroundColor Yellow
Write-Host "                torold onnan az 'android-control' bejegyzest." -ForegroundColor Yellow
Write-Host "  Claude Code:  claude mcp remove android-control" -ForegroundColor Yellow
