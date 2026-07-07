#Requires -Version 5.1
<#
.SYNOPSIS
  下载 SiglusSSU-GUI 便携版到桌面并创建快捷方式。

.PARAMETER Local
  使用本仓库 dist\SiglusSSU-GUI-portable.zip（开发者本地打包）。

.PARAMETER Repo
  GitHub 仓库 owner/name，默认 yanmuuuu/SiglusSceneScriptUtility-GUI
#>
param(
    [switch]$Local,
    [string]$Repo = "yanmuuuu/SiglusSceneScriptUtility-GUI"
)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$desktop = [Environment]::GetFolderPath("Desktop")
$installDir = Join-Path $desktop "SiglusSSU-GUI"
$zipPath = Join-Path $env:TEMP "SiglusSSU-GUI-portable.zip"
$scriptRoot = Split-Path -Parent $PSScriptRoot

function Write-Step([string]$msg) {
    Write-Host ""
    Write-Host ">> $msg" -ForegroundColor Cyan
}

Write-Step "SiglusSceneScriptUtility GUI 一键安装"
Write-Host "目标：$installDir"

if ($Local) {
    $localZip = Join-Path $scriptRoot "dist\SiglusSSU-GUI-portable.zip"
    if (-not (Test-Path $localZip)) {
        throw "未找到本地包：$localZip`n请先在项目根目录运行 scripts\build_portable.bat"
    }
    Copy-Item $localZip $zipPath -Force
    Write-Step "使用本地打包：$localZip"
} else {
    Write-Step "正在查询 GitHub 最新发布…"
  $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest" -Headers @{ "User-Agent" = "SiglusSSU-GUI-Installer" }
    $asset = $release.assets | Where-Object { $_.name -eq "SiglusSSU-GUI-portable.zip" } | Select-Object -First 1
    if (-not $asset) {
        throw "发布页未找到 SiglusSSU-GUI-portable.zip。`n请从 GitHub Releases 手动下载，或在仓库根目录双击「下载 SiglusSSU-GUI.bat」并加参数 -Local（需先本地打包）。"
    }
    Write-Step "下载 $($asset.name) …"
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zipPath -UseBasicParsing
}

if (Test-Path $installDir) {
    Write-Step "删除旧版本…"
    Remove-Item -Recurse -Force $installDir
}

Write-Step "解压到桌面…"
Expand-Archive -Path $zipPath -DestinationPath $desktop -Force

$exePath = Join-Path $installDir "SiglusSSU-GUI.exe"
if (-not (Test-Path $exePath)) {
    throw "解压后未找到 $exePath"
}

$shortcutPath = Join-Path $desktop "SiglusSSU-GUI.lnk"
Write-Step "创建桌面快捷方式…"
$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = $installDir
$shortcut.Description = "SiglusSceneScriptUtility 图形工具"
$shortcut.Save()

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  文件夹：$installDir"
Write-Host "  快捷方式：$shortcutPath"
Write-Host ""
Write-Host "  双击桌面上的「SiglusSSU-GUI」即可使用（无需安装 Python）。"
Write-Host "  首次使用请在程序内运行一次「初始化」。"
Write-Host ""

$open = Read-Host "是否现在启动？(Y/n)"
if ($open -eq "" -or $open -match "^[Yy]") {
    Start-Process $exePath
}
