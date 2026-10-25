# Install the built setup silently, verify the installed files + shortcut, run
# the installed application's self-test and report the result.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File packaging\test_installer.ps1 `
#       -Setup "packaging\Output\MSMediaPlayer_Setup_1.0.0.exe" [-KeepInstalled]
param(
    [Parameter(Mandatory = $true)][string]$Setup,
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA 'Programs\MS Media Player'),
    [string]$Lang = "arabic",
    [switch]$KeepInstalled,
    [switch]$SkipUninstall
)

$ErrorActionPreference = 'Stop'

$installLog = Join-Path $env:TEMP 'msmp_install_test\install.log'
$selfTestLog = Join-Path $env:TEMP 'msmp_install_test\selftest.log'
New-Item -ItemType Directory -Force -Path (Split-Path $installLog) | Out-Null

Write-Host "== Installing the built setup silently =="
Write-Host "Setup      : $Setup"
Write-Host "InstallDir : $InstallDir"
$proc = Start-Process -FilePath $Setup -PassThru -Wait -ArgumentList @(
    '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', "/LANG=$Lang",
    '/MERGETASKS=desktopicon',
    "/DIR=`"$InstallDir`"", "/LOG=`"$installLog`""
)
Write-Host "Installer exit code: $($proc.ExitCode)"

$exe = Join-Path $InstallDir 'MSMediaPlayer.exe'
if (-not (Test-Path $exe)) { throw "Installed executable not found: $exe" }
Write-Host "Installed exe       : $exe ($([math]::Round((Get-Item $exe).Length/1MB,1)) MB)"

$eula = Join-Path $InstallDir 'EULA.txt'
Write-Host "Installed EULA.txt  : $(Test-Path $eula)"

$desktop = [Environment]::GetFolderPath('Desktop')
$shortcuts = @(Get-ChildItem -Path $desktop -Filter '*.lnk' -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like '*Media Player*' }
Write-Host "Desktop shortcut    : $($shortcuts.Count) found"
$shortcuts | ForEach-Object { Write-Host "    $($_.Name)" }

$uninstaller = Join-Path $InstallDir 'unins000.exe'
Write-Host "Uninstaller present : $(Test-Path $uninstaller)"

Write-Host "== Running the installed application self-test =="
$logFile = Join-Path $env:TEMP 'msmp_install_test\selftest.log'
Remove-Item $logFile -ErrorAction SilentlyContinue
$test = Start-Process -FilePath $exe -Wait -PassThru `
    -ArgumentList @('--selftest', '--selftest-log', $logFile)
Write-Host "Self-test exit code : $($test.ExitCode)"

if (Test-Path $logFile) {
    Write-Host '---- self-test log ----'
    Get-Content $logFile
    Write-Host '-----------------------'
} else {
    throw "Self-test produced no log file"
}

if (-not $KeepInstalled -and -not $SkipUninstall) {
    if (Test-Path $uninstaller) {
        Write-Host "== Uninstalling =="
        Start-Process -FilePath $uninstaller -Wait -ArgumentList @(
            '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'
        ) | Out-Null
        Write-Host "Uninstalled. Files left behind: $(Test-Path $exe)"
    }
}

if ($test.ExitCode -ne 0) { throw "SELF-TEST FAILED (exit $($test.ExitCode))" }
Write-Host "ALL GOOD: installed application passed its self-test."
