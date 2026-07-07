#Requires -Version 5.1
param([string]$Repo = "yanmuuuu/SiglusSceneScriptUtility-GUI")

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$desktop = [Environment]::GetFolderPath("Desktop")
$installDir = Join-Path $desktop "SiglusSSU-GUI"
$zipPath = Join-Path $env:TEMP "SiglusSSU-GUI-portable.zip"

Write-Host "正在下载最新 SiglusSSU-GUI…" -ForegroundColor Cyan
$release = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest" -Headers @{ "User-Agent" = "SiglusSSU-GUI" }
$asset = $release.assets | Where-Object { $_.name -eq "SiglusSSU-GUI-portable.zip" } | Select-Object -First 1
if (-not $asset) { throw "未找到发布包 SiglusSSU-GUI-portable.zip" }
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zipPath -UseBasicParsing

if (Test-Path $installDir) { Remove-Item -Recurse -Force $installDir }
Expand-Archive -Path $zipPath -DestinationPath $desktop -Force

$exe = Join-Path $installDir "SiglusSSU-GUI.exe"
$lnk = Join-Path $desktop "SiglusSSU-GUI.lnk"
$wsh = New-Object -ComObject WScript.Shell
$s = $wsh.CreateShortcut($lnk)
$s.TargetPath = $exe
$s.WorkingDirectory = $installDir
$s.Save()

Write-Host "已更新到桌面：$installDir" -ForegroundColor Green
Start-Process $exe
