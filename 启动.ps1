<#
  回声 Echo 一键启动
    1. 服务已在跑  -> 直接用 Edge 打开
    2. 按顺序试 py -3.12 / py -3.13 / py / python，谁能加载依赖就用谁
    3. 起服务 -> 等 /api/health 通过 -> 用 Edge 打开
  用法：双击 start.bat
#>
param(
  [switch]$NoBrowser
)

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$app = Join-Path $root "应用"
$logDir = Join-Path $app "logs"
$url = "http://127.0.0.1:8771"

function Test-EchoUp {
  try { return (Invoke-WebRequest -Uri "$url/api/health" -TimeoutSec 2 -UseBasicParsing).StatusCode -eq 200 }
  catch { return $false }
}

function Open-Browser {
  if ($NoBrowser) { Write-Host "  (跳过打开浏览器)"; return }
  $edge = @(
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
  ) | Where-Object { Test-Path $_ } | Select-Object -First 1
  if ($edge) { Start-Process -FilePath $edge -ArgumentList $url } else { Start-Process $url }
  Write-Host "  已用 Edge 打开：$url" -ForegroundColor Green
}

function Pause-IfInteractive {
  if (-not $NoBrowser) { Read-Host "按回车退出" | Out-Null }
}

Write-Host ""
Write-Host "  回声 Echo · 会追问的 AI 小先生" -ForegroundColor DarkGreen
Write-Host "  ----------------------------------------" -ForegroundColor DarkGray

if (Test-EchoUp) {
  Write-Host "  服务已经在运行了。" -ForegroundColor Yellow
  Open-Browser
  Start-Sleep -Seconds 2
  exit 0
}

$probe = "import sys,os;sys.path.insert(0,os.path.join(os.getcwd(),'vendor'));import fastapi,uvicorn;print('OK')"

$runners = @(
  @{ exe = "py"; args = @("-3.12") },
  @{ exe = "py"; args = @("-3.13") },
  @{ exe = "py"; args = @() },
  @{ exe = "python"; args = @() }
)

$pick = $null
foreach ($r in $runners) {
  if (-not (Get-Command $r.exe -ErrorAction SilentlyContinue)) { continue }
  Push-Location $app
  try {
    if ($r.args.Count -gt 0) { $out = & $r.exe @($r.args) -c $probe 2>$null }
    else { $out = & $r.exe -c $probe 2>$null }
    $code = $LASTEXITCODE
  } catch { $code = 1; $out = "" }
  Pop-Location
  if ($code -eq 0 -and "$out" -match "OK") { $pick = $r; break }
}

if (-not $pick) {
  Write-Host "  没找到能加载依赖的 Python。" -ForegroundColor Red
  Write-Host "  请先执行（推荐 3.12）：" -ForegroundColor Yellow
  Write-Host "    py -3.12 -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple"
  Pause-IfInteractive
  exit 1
}

$label = ($pick.exe + " " + ($pick.args -join " ")).Trim()
Write-Host "  使用：$label" -ForegroundColor DarkGray

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$outLog = Join-Path $logDir "server.out.log"
$errLog = Join-Path $logDir "server.err.log"
Remove-Item $outLog, $errLog -Force -ErrorAction SilentlyContinue

Write-Host "  正在启动服务…" -ForegroundColor DarkGray
if ($pick.args.Count -gt 0) {
  $proc = Start-Process -FilePath $pick.exe -ArgumentList (@($pick.args) + "run.py") -WorkingDirectory $app `
    -RedirectStandardOutput $outLog -RedirectStandardError $errLog -WindowStyle Hidden -PassThru
} else {
  $proc = Start-Process -FilePath $pick.exe -ArgumentList "run.py" -WorkingDirectory $app `
    -RedirectStandardOutput $outLog -RedirectStandardError $errLog -WindowStyle Hidden -PassThru
}

for ($i = 0; $i -lt 50; $i++) {
  Start-Sleep -Milliseconds 400
  if (Test-EchoUp) { break }
  if ($proc.HasExited) { break }
}

if (Test-EchoUp) {
  Open-Browser
  Write-Host "  服务已在后台运行（PID $($proc.Id)），日志在 应用\logs" -ForegroundColor DarkGray
  Write-Host "  需要停止：运行 stop.bat" -ForegroundColor DarkGray
  Start-Sleep -Seconds 2
  exit 0
}

Write-Host "  启动失败。最后几行日志：" -ForegroundColor Red
foreach ($f in @($errLog, $outLog)) {
  if (Test-Path $f) { Get-Content $f -Tail 12 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray } }
}
Pause-IfInteractive
exit 1
