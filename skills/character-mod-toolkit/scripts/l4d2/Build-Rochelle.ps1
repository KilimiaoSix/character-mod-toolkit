param(
    [Parameter(Mandatory = $true)]
    [string] $Workspace,
    [Parameter(Mandatory = $true)]
    [string] $GameRoot,
    [string] $FirstPersonQc,
    [switch] $Pack
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $Workspace).Path
$install = (Resolve-Path -LiteralPath $GameRoot).Path
$game = Join-Path $install 'left4dead2'
$compiler = Join-Path $install 'bin\studiomdl.exe'
$packer = Join-Path $install 'bin\vpk.exe'
$worldQc = Join-Path $root '04_compile\rochelle_world.qc'
$materialNamespace = 'materials\models\survivors\character_mod'
$materials = Join-Path (Join-Path $root 'addon') $materialNamespace
$materialManifest = Join-Path $root '02_material_input\manifest.json'

if (!(Test-Path -LiteralPath (Join-Path $game 'gameinfo.txt') -PathType Leaf)) {
    throw 'GameRoot must point to the Steam Left 4 Dead 2 installation directory.'
}
if (!(Test-Path -LiteralPath $compiler -PathType Leaf)) {
    throw 'studiomdl.exe was not found. Install Left 4 Dead 2 Authoring Tools in Steam.'
}
if ($Pack -and !(Test-Path -LiteralPath $packer -PathType Leaf)) {
    throw 'vpk.exe was not found in the game installation.'
}
if (!(Test-Path -LiteralPath $worldQc -PathType Leaf)) {
    throw "World-model QC was not found: $worldQc"
}
if ($Pack) {
    if (!(Test-Path -LiteralPath $materialManifest -PathType Leaf)) {
        throw "Generated material manifest was not found: $materialManifest"
    }
    $manifest = Get-Content -LiteralPath $materialManifest -Raw | ConvertFrom-Json
    $materialFiles = @(foreach ($property in $manifest.PSObject.Properties) {
        $stem = $property.Name
        if ($stem -cnotmatch '^[a-z][a-z0-9_]{0,62}$') { throw "Invalid material name: $stem" }
        foreach ($extension in @('vtf', 'vmt')) {
            $file = Join-Path $materials "$stem.$extension"
            if (!(Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing material: $file" }
            $file
        }
    })
    if (!$materialFiles.Count) { throw 'The generated material manifest is empty.' }
}
if ($FirstPersonQc) {
    $FirstPersonQc = (Resolve-Path -LiteralPath $FirstPersonQc).Path
    $armsText = Get-Content -LiteralPath $FirstPersonQc -Raw
    if ($armsText -notmatch '(?im)^\s*\$modelname\s+"weapons[/\\]arms[/\\]v_arms_producer_new\.mdl"') {
        throw 'FirstPersonQc must target weapons/arms/v_arms_producer_new.mdl.'
    }
}

$buildRoot = Join-Path $root 'build'
New-Item -ItemType Directory -Path $buildRoot -Force | Out-Null
$stage = Join-Path $buildRoot ([guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $stage | Out-Null
$searchPaths = foreach ($name in @('update', 'left4dead2_dlc3', 'left4dead2_dlc2', 'left4dead2_dlc1', 'left4dead2', 'platform')) {
    $folder = Join-Path $install $name
    if (Test-Path -LiteralPath $folder -PathType Container) {
        '            "Game" "' + $folder.Replace('\', '/') + '"'
    }
}
$sourceSearch = $searchPaths -join "`n"
$gameInfo = @"
"GameInfo"
{
    "game" "Rochelle character mod build"
    "type" "multiplayer_only"
    "FileSystem"
    {
        "SteamAppId" "550"
        "SearchPaths"
        {
            "Game" "|gameinfo_path|."
$sourceSearch
        }
    }
}
"@
[IO.File]::WriteAllText((Join-Path $stage 'gameinfo.txt'), $gameInfo, [Text.UTF8Encoding]::new($false))

function Invoke-ModelBuild {
    param([string] $Qc, [string] $ModelDir, [string] $Stem, [string] $LogName)

    $log = Join-Path $stage $LogName
    $oldPreference = $ErrorActionPreference
    Push-Location (Split-Path -Parent $Qc)
    try {
        $ErrorActionPreference = 'Continue'
        & $compiler -game $stage -nop4 $Qc 2>&1 | Tee-Object -FilePath $log | Out-Host
        $result = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $oldPreference
        Pop-Location
    }
    if ($result -ne 0 -or !(Test-Path -LiteralPath $log -PathType Leaf) -or
        (Select-String -LiteralPath $log -Pattern '^\s*ERROR:' -Quiet)) {
        throw "StudioMDL reported an error. Inspect $log."
    }

    foreach ($extension in @('mdl', 'vvd', 'dx90.vtx')) {
        $path = Join-Path $ModelDir "$Stem.$extension"
        $file = Join-Path $stage $path
        if (!(Test-Path -LiteralPath $file -PathType Leaf) -or (Get-Item -LiteralPath $file).Length -eq 0) {
            throw "Missing output: $path. Inspect $log."
        }
        $path
    }
    foreach ($extension in @('dx80.vtx', 'sw.vtx')) {
        $path = Join-Path $ModelDir "$Stem.$extension"
        if (Test-Path -LiteralPath (Join-Path $stage $path) -PathType Leaf) {
            $path
        }
    }
    Write-Host "Compile log: $log"
}

$models = @(Invoke-ModelBuild -Qc $worldQc -ModelDir 'models\survivors' -Stem 'survivor_producer' -LogName 'studiomdl.log')
if ($FirstPersonQc) {
    $models += @(Invoke-ModelBuild -Qc $FirstPersonQc -ModelDir 'models\weapons\arms' -Stem 'v_arms_producer_new' -LogName 'studiomdl-arms.log')
}
Write-Host "Compiled models: $stage"

if ($Pack) {
    $packDir = Join-Path $stage 'rochelle_character'
    New-Item -ItemType Directory -Path $packDir | Out-Null
    $addonInfo = Join-Path $root 'addon\addoninfo.txt'
    if (Test-Path -LiteralPath $addonInfo -PathType Leaf) {
        Copy-Item -LiteralPath $addonInfo -Destination $packDir
    } else {
        Set-Content -Encoding Ascii -LiteralPath (Join-Path $packDir 'addoninfo.txt') -Value @'
"AddonInfo"
{
    "addonTitle" "Rochelle Character Replacement"
    "addonVersion" "1.0"
    "addonDescription" "Cosmetic character replacement for Rochelle."
}
'@
    }
    $materialDest = Join-Path $packDir $materialNamespace
    New-Item -ItemType Directory -Path $materialDest -Force | Out-Null
    Copy-Item -LiteralPath $materialFiles -Destination $materialDest
    foreach ($model in $models) {
        $destination = Join-Path $packDir $model
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $stage $model) -Destination $destination
    }
    Push-Location $stage
    try {
        & $packer $packDir
        if ($LASTEXITCODE -ne 0) { throw 'vpk.exe returned an error.' }
    } finally {
        Pop-Location
    }
    $pack = "$packDir.vpk"
    if (!(Test-Path -LiteralPath $pack -PathType Leaf) -or (Get-Item -LiteralPath $pack).Length -eq 0) {
        throw 'vpk.exe did not produce the expected VPK.'
    }
    Write-Host "Packaged: $pack"
}
