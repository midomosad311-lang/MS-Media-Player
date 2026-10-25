# Build the standalone MS Media Player executable with PyInstaller.
#
# Usage (from anywhere):
#   powershell -ExecutionPolicy Bypass -File packaging\build_exe.ps1
#
# Optional parameters:
#   -DistPath <dir>  where the .exe is written (default: <project>\dist)
#   -WorkPath <dir>  PyInstaller scratch dir     (default: <project>\build)
#   -VlcDir   <dir>  VLC installation to bundle  (default: C:\Program Files\VideoLAN\VLC)
param(
    [string]$DistPath = "",
    [string]$WorkPath = "",
    [string]$VlcDir = "C:\Program Files\VideoLAN\VLC"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($DistPath)) { $DistPath = Join-Path $ProjectRoot "dist" }
if ([string]::IsNullOrWhiteSpace($WorkPath)) { $WorkPath = Join-Path $ProjectRoot "build" }

Write-Host "Project root : $ProjectRoot"
Write-Host "Dist path    : $DistPath"
Write-Host "Work path    : $WorkPath"
Write-Host "VLC dir      : $VlcDir"

if (-not (Test-Path (Join-Path $VlcDir "libvlc.dll"))) {
    Write-Warning "libvlc.dll not found under '$VlcDir'. The EXE will need a system VLC install to play media."
}

$env:MSMP_VLC_DIR = $VlcDir

Push-Location $ProjectRoot
try {
    python -m PyInstaller "packaging\ms_media_player.spec" `
        --noconfirm --clean `
        --distpath "$DistPath" `
        --workpath "$WorkPath"
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }
    Write-Host ""
    Write-Host "BUILD OK -> $DistPath\MSMediaPlayer.exe"
} finally {
    Pop-Location
}
