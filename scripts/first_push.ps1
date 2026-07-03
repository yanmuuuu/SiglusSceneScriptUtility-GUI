# 首次 push 辅助脚本：先完成 GitHub 登录，再推送 main 分支
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$env:HTTP_PROXY = "http://127.0.0.1:7892"
$env:HTTPS_PROXY = "http://127.0.0.1:7892"
git config --local http.proxy $env:HTTP_PROXY
git config --local https.proxy $env:HTTPS_PROXY
git config --local http.sslBackend openssl

$Gh = Join-Path $Root "tools\gh\bin\gh.exe"
if (-not (Test-Path $Gh)) {
    Write-Host "未找到便携版 gh，请先保持 QingyunLite 代理开启（端口 7892）。" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "=== 步骤 1/2：GitHub 登录 ===" -ForegroundColor Cyan
Write-Host "浏览器会打开，按提示输入一次性验证码完成授权。"
& $Gh auth login --hostname github.com --git-protocol https --web
& $Gh auth setup-git

Write-Host "`n=== 步骤 2/2：推送到 origin/main ===" -ForegroundColor Cyan
Write-Host "远程仓库目前只有 Initial commit，将使用 --force-with-lease 覆盖为本地完整代码。"
git push -u origin main --force-with-lease

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n推送成功！仓库: https://github.com/yanmuuuu/SiglusSceneScriptUtility-GUI" -ForegroundColor Green
} else {
    Write-Host "`n推送失败，请确认 QingyunLite 已开启且已登录 GitHub。" -ForegroundColor Red
}
pause
