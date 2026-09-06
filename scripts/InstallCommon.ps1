#requires -version 5.1
<#
.SYNOPSIS
    Kozos segedfuggvenyek az Android Control MCP telepito/eltavolito szkriptjeihez.
    Dot-source-olva hasznalando: . "$PSScriptRoot\InstallCommon.ps1"

.DESCRIPTION
    - Ut-canonicalizacio es veszelyes-cel-felismeres (drive root, rendszerkonyvtarak,
      felhasznaloi profil gyoker, forras-repository gyoker/tartalmazas).
    - Telepitesi marker/sentinel iras es olvasas+validalas (uninstall-vedelem).
    - Natic parancsok exit code-jainak ellenorzese (winget/git/pip/venv/doctor).
    - Robocopy kulon exit-code-kezelese (0-7 = siker, >=8 = valodi hiba).
    - Csak GIT-TRACKELT fajlok masolasa fejlesztoi repo-bol telepitett app-konyvtarba,
      hogy privat/gitignore-olt (*.local.md stb.) fajlok SOSE keruljenek az install-ba.
#>

$MARKER_FILE_NAME = ".android-control-mcp-install.json"
$PRODUCT_ID = "android-control-mcp"
$INSTALL_SCHEMA_VERSION = 1

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "    OK: $msg" -ForegroundColor Green }
function Write-Warn2($msg) { Write-Host "    FIGYELEM: $msg" -ForegroundColor Yellow }
function Write-Err2($msg) { Write-Host "    HIBA: $msg" -ForegroundColor Red }

# --- Ut-canonicalizacio es veszelyes-cel-felismeres ------------------------

function Get-CanonicalPath {
    <#
    .SYNOPSIS
        Abszolut, trailing-backslash-mentes utvonalla alakit - LETEZES NELKUL is
        (mukodik meg-nem-letezo telepitesi celra is), hogy a veszelyes-utvonal
        ellenorzes a konyvtar letrehozasa ELOTT is lefuthasson.
    #>
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return $null }
    try {
        $full = [System.IO.Path]::GetFullPath($Path)
    } catch {
        return $null
    }
    $trimmed = $full.TrimEnd('\')
    if ($trimmed.Length -eq 2 -and $trimmed[1] -eq ':') {
        # "C:" marad (drive root), NE valjon uressse
        return $trimmed
    }
    return $trimmed
}

function Test-DangerousInstallPath {
    <#
    .SYNOPSIS
        Visszaad egy hiba-szoveget, ha a megadott (mar canonicalizalt) utvonal
        veszelyes telepitesi/torlesi cel lenne. $null-t ad vissza, ha biztonsagos.
    .PARAMETER CanonicalPath
        Mar Get-CanonicalPath-on atfuttatott utvonal.
    .PARAMETER RepoRoot
        A forras-repository gyokere (ha ismert) - a canonicalizalas ITT is megtortenik.
    #>
    param(
        [string]$CanonicalPath,
        [string]$RepoRoot
    )

    if (-not $CanonicalPath) {
        return "Az utvonal ures vagy nem ertelmezheto."
    }

    # Drive root: "C:", "D:" stb.
    if ($CanonicalPath -match '^[A-Za-z]:$') {
        return "Meghajto-gyoker ('$CanonicalPath') nem lehet telepitesi/torlesi cel."
    }

    # Ismert vedett rendszer-/profil-gyokerek - CSAK a pontos gyoker, nem minden alkonyvtaruk
    # (pl. "Program Files\AndroidControlMCP" nem tiltott, csak maga a "Program Files" gyoker).
    $protectedRoots = New-Object System.Collections.Generic.List[string]
    foreach ($envVal in @($env:SystemRoot, $env:ProgramFiles, ${env:ProgramFiles(x86)}, `
                          $env:USERPROFILE, $env:LOCALAPPDATA, $env:APPDATA, $env:windir)) {
        if ($envVal) {
            $c = Get-CanonicalPath $envVal
            if ($c) { $protectedRoots.Add($c) }
        }
    }
    if ($env:HOMEDRIVE -and $env:HOMEPATH) {
        $c = Get-CanonicalPath ("$env:HOMEDRIVE$env:HOMEPATH")
        if ($c) { $protectedRoots.Add($c) }
    }

    foreach ($root in $protectedRoots) {
        if ($CanonicalPath -ieq $root) {
            return "A cel megegyezik egy vedett rendszer-/profil-konyvtarral: '$root'. " `
                + "Valassz egy sajat alkonyvtart (pl. '$root\AndroidControlMCP')."
        }
    }

    # Forras-repository gyokerevel/tartalmazasaval kapcsolatos vedelem.
    if ($RepoRoot) {
        $canonRepo = Get-CanonicalPath $RepoRoot
        if ($canonRepo) {
            if ($CanonicalPath -ieq $canonRepo) {
                return "A telepitesi cel nem lehet maga a forras-repository gyokere ('$canonRepo')."
            }
            if ($CanonicalPath.StartsWith($canonRepo + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
                return "A telepitesi cel nem lehet a forras-repository BELSEJEBEN ('$canonRepo') - " `
                    + "ez onmagara-masolo/rekurziv problemat okozna."
            }
            if ($canonRepo.StartsWith($CanonicalPath + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
                return "A telepitesi cel nem tartalmazhatja a forras-repository gyokeret ('$canonRepo')."
            }
        }
    }

    return $null
}

# --- Natic parancsok exit code ellenorzese ---------------------------------

function Invoke-NativeChecked {
    <#
    .SYNOPSIS
        Lefuttat egy natic parancsot (winget/git/pip/venv/stb.), es a $LASTEXITCODE
        alapjan ellenorzi a sikeresseget - a sima $ErrorActionPreference="Stop" ezt
        NEM kezeli natic exe-knel automatikusan.
    .PARAMETER Description
        Ember szamara ertheto leiras a hibauzenethez.
    .PARAMETER ScriptBlock
        A tenylegesen futtatando natic parancs.
    #>
    param(
        [Parameter(Mandatory)][string]$Description,
        [Parameter(Mandatory)][scriptblock]$ScriptBlock
    )
    Write-Host "    -> $Description" -ForegroundColor DarkGray
    & $ScriptBlock
    $exitCode = $LASTEXITCODE
    if ($null -ne $exitCode -and $exitCode -ne 0) {
        throw "'$Description' sikertelen (exit code: $exitCode)."
    }
}

function Invoke-RobocopyChecked {
    <#
    .SYNOPSIS
        robocopy futtatasa a helyes exit-code-ertelmezessel: 0-7 = siker
        (fajlok masolva/nincs valtozas), >=8 = VALODI hiba.
    #>
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$Destination,
        [string[]]$ExcludeDirs = @(),
        [string[]]$ExcludeFiles = @()
    )
    $roboArgs = @($Source, $Destination, "/MIR", "/NFL", "/NDL", "/NJH", "/NJS")
    if ($ExcludeDirs.Count -gt 0) { $roboArgs += "/XD"; $roboArgs += $ExcludeDirs }
    if ($ExcludeFiles.Count -gt 0) { $roboArgs += "/XF"; $roboArgs += $ExcludeFiles }
    robocopy @roboArgs | Out-Null
    $exitCode = $LASTEXITCODE
    if ($exitCode -ge 8) {
        throw "robocopy sikertelen (exit code: $exitCode) - $Source -> $Destination"
    }
}

# --- Csak git-tracked fajlok masolasa ---------------------------------------

function Copy-TrackedRepoFiles {
    <#
    .SYNOPSIS
        A forras konyvtar tartalmat masolja a celba, de KIZAROLAG a git altal
        TRACKELT fajlokat (git ls-files) - igy privat/gitignore-olt fajlok
        (pl. *.local.md, .env) SOSE keruljenek at a telepitett app-konyvtarba,
        akkor sem, ha a fejlesztoi working tree-ben jelen vannak.

        Ha nincs git/.git a forrasban, biztonsagi FALLBACK-kent szurt robocopy-t
        hasznal, ami explicit kizarja a fejlesztoi mellektermekeket ES minden
        ismert privat/local-state mintat.
    #>
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$Destination
    )

    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    $isGitRepo = $gitCmd -and (Test-Path (Join-Path $Source ".git"))

    if (Test-Path $Destination) { Remove-Item -Recurse -Force $Destination }
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null

    if ($isGitRepo) {
        Write-Ok "Git-repo eszlelve - kizarolag a git altal TRACKELT fajlokat masoljuk " `
            "(privat *.local.md/.env/stb. fajlok garantaltan KIMARADNAK)."
        Push-Location $Source
        try {
            $trackedFiles = git ls-files
            if ($LASTEXITCODE -ne 0) {
                throw "'git ls-files' sikertelen (exit code: $LASTEXITCODE)."
            }
        } finally {
            Pop-Location
        }
        if (-not $trackedFiles) {
            throw "A 'git ls-files' ures listat adott - a forras nem tunik ervenyes git repo-nak."
        }
        $count = 0
        foreach ($rel in $trackedFiles) {
            $srcFile = Join-Path $Source $rel
            if (-not (Test-Path $srcFile -PathType Leaf)) { continue }
            $dstFile = Join-Path $Destination $rel
            $dstDir = Split-Path -Parent $dstFile
            if ($dstDir -and -not (Test-Path $dstDir)) {
                New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
            }
            Copy-Item -Path $srcFile -Destination $dstFile -Force
            $count++
        }
        Write-Ok "$count tracked fajl atmasolva (privat/gitignore-olt fajlok nelkul)."
    } else {
        Write-Warn2 "Nem talalhato git/.git a forrasban - szurt (nem tracked-alapu) masolas " `
            "robocopy-val, explicit privat-fajl-kizarassal."
        Invoke-RobocopyChecked -Source $Source -Destination $Destination `
            -ExcludeDirs @(".venv", ".git", ".pytest_cache", ".ruff_cache", "__pycache__") `
            -ExcludeFiles @("*.local.md", ".env", ".env.*", "*.key", "*.pem")
        Write-Ok "Szurt masolas kesz."
    }
}

# --- Telepitesi marker/sentinel ---------------------------------------------

function Write-InstallMarker {
    param(
        [Parameter(Mandatory)][string]$InstallDir,
        [Parameter(Mandatory)][string]$AppDir,
        [Parameter(Mandatory)][string]$VenvDir
    )
    $marker = [ordered]@{
        product_id             = $PRODUCT_ID
        install_schema_version = $INSTALL_SCHEMA_VERSION
        install_dir             = $InstallDir
        app_dir                 = $AppDir
        venv_dir                 = $VenvDir
        installed_at             = (Get-Date).ToString("o")
    }
    $markerPath = Join-Path $InstallDir $MARKER_FILE_NAME
    ($marker | ConvertTo-Json) | Set-Content -Path $markerPath -Encoding utf8
    return $markerPath
}

function Test-InstallMarker {
    <#
    .SYNOPSIS
        Beolvassa es validalja a telepitesi markert egy CANONICALIZALT
        celutvonalon. Visszaad egy hashtable-t: @{ Ok = $true/$false; Reason = "...";
        Marker = <object|$null> }. Minden nem-egyezes REFUSE-t eredmenyez.
    #>
    param([Parameter(Mandatory)][string]$CanonicalInstallDir)

    $markerPath = Join-Path $CanonicalInstallDir $MARKER_FILE_NAME
    if (-not (Test-Path $markerPath -PathType Leaf)) {
        return @{ Ok = $false; Reason = "Nem talalhato telepitesi marker fajl: $markerPath"; Marker = $null }
    }

    try {
        $marker = Get-Content -Path $markerPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        return @{ Ok = $false; Reason = "A marker fajl nem ervenyes JSON: $markerPath"; Marker = $null }
    }

    if (-not $marker.product_id -or $marker.product_id -ne $PRODUCT_ID) {
        return @{ Ok = $false;
            Reason = "A marker 'product_id' mezoje nem '$PRODUCT_ID' (talalt: '$($marker.product_id)')."
            Marker = $marker }
    }

    $markerInstallDir = Get-CanonicalPath $marker.install_dir
    if (-not $markerInstallDir -or $markerInstallDir -ne $CanonicalInstallDir) {
        return @{ Ok = $false;
            Reason = "A markerben tarolt install_dir ('$($marker.install_dir)') nem egyezik " `
                + "a tenyleges, canonicalizalt celutvonallal ('$CanonicalInstallDir')."
            Marker = $marker }
    }

    return @{ Ok = $true; Reason = $null; Marker = $marker }
}

# --- Python ujra-felderites winget-telepites utan ---------------------------

function Find-PythonExecutable {
    <#
    .SYNOPSIS
        Robusztusan megkeresi a telepitett (3.10+) Python futtathatot - nem csak
        a friss PATH-frissitesre tamaszkodva. Sorrend: PATH -> 'py' launcher ->
        Windows registry (py launcher sajat PythonCore bejegyzesei, HKCU) ->
        ismert, LOCALAPPDATA-relativ per-user winget/python.org telepitesi minta.
        Sehol nincs felhasznalonev/abszolut path hardcode-olva.
    #>
    foreach ($cand in @("python", "python3")) {
        $cmd = Get-Command $cand -ErrorAction SilentlyContinue
        if ($cmd) {
            $verOut = & $cmd.Source --version 2>&1
            if ($verOut -match '(\d+)\.(\d+)\.(\d+)') {
                if ([int]$Matches[1] -eq 3 -and [int]$Matches[2] -ge 10) { return $cmd.Source }
            }
        }
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        foreach ($minor in @("3.13", "3.12", "3.11", "3.10")) {
            try {
                $exe = & $pyLauncher.Source "-$minor" -c "import sys; print(sys.executable)" 2>$null
                if ($LASTEXITCODE -eq 0 -and $exe -and (Test-Path $exe)) { return $exe.Trim() }
            } catch { }
        }
    }

    try {
        $regRoot = "HKCU:\Software\Python\PythonCore"
        if (Test-Path $regRoot) {
            $versions = Get-ChildItem $regRoot -ErrorAction SilentlyContinue |
                Sort-Object Name -Descending
            foreach ($v in $versions) {
                $installPathKey = Join-Path $v.PSPath "InstallPath"
                if (Test-Path $installPathKey) {
                    $installDir = (Get-ItemProperty -Path $installPathKey -ErrorAction SilentlyContinue).'(default)'
                    if ($installDir) {
                        $exe = Join-Path $installDir "python.exe"
                        if (Test-Path $exe) { return $exe }
                    }
                }
            }
        }
    } catch { }

    if ($env:LOCALAPPDATA) {
        $pattern = Join-Path $env:LOCALAPPDATA "Programs\Python\Python31*\python.exe"
        $found = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending | Select-Object -First 1
        if ($found) { return $found.FullName }
    }

    return $null
}
