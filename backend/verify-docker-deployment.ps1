# AI自动化工作流 - Docker Compose 部署验证脚本
# 用法: .\verify-docker-deployment.ps1

param(
    [switch]$SkipBuild,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
$ProjectRoot = "D:\openclaw_ground\PROJECTS\AI自动化工作流\backend"
$BackendDir = $ProjectRoot
$FrontendDir = "D:\openclaw_ground\PROJECTS\AI自动化工作流\frontend"
$ComposeFile = Join-Path $BackendDir "docker-compose.yml"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI自动化工作流 - Docker Compose 部署验证" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============ 前置检查 ============
Write-Host "[1/6] 检查前置条件..." -ForegroundColor Yellow

# 检查 Docker 是否运行
$dockerStatus = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [错误] Docker 未运行或未正确安装" -ForegroundColor Red
    Write-Host "  请启动 Docker Desktop 后重试" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] Docker 运行正常" -ForegroundColor Green

# 检查 docker-compose 文件
if (-not (Test-Path $ComposeFile)) {
    Write-Host "  [错误] docker-compose.yml 不存在: $ComposeFile" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] docker-compose.yml 存在" -ForegroundColor Green

# 检查 Dockerfile
$dockerfile = Join-Path $BackendDir "Dockerfile"
if (-not (Test-Path $dockerfile)) {
    Write-Host "  [错误] Dockerfile 不存在: $dockerfile" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] Dockerfile 存在" -ForegroundColor Green

# 检查前端构建产物
$frontendDist = Join-Path $FrontendDir "dist"
if (-not (Test-Path $frontendDist)) {
    Write-Host "  [错误] 前端未构建，请先运行: cd $FrontendDir; npm run build" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] 前端构建产物存在" -ForegroundColor Green

# 检查/创建 frontend-dist 链接
$symlink = Join-Path $BackendDir "frontend-dist"
if (-not (Test-Path $symlink)) {
    Write-Host "  [提示] 创建 frontend-dist 目录链接..." -ForegroundColor Yellow
    cmd /c "mklink /J `"$symlink`" `"$frontendDist`"" 2>$null
}
if ((Get-Item $symlink).Target -eq $frontendDist -or (Test-Path (Join-Path $symlink "index.html"))) {
    Write-Host "  [OK] frontend-dist 链接正常" -ForegroundColor Green
} else {
    Write-Host "  [警告] frontend-dist 链接可能有问题" -ForegroundColor Yellow
}

# 检查/创建 data 目录
$dataDir = Join-Path $BackendDir "data"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
}
Write-Host "  [OK] data 目录就绪" -ForegroundColor Green

# 检查/创建 ssl 目录（空目录，nginx 不加载时不会出错）
$sslDir = Join-Path $BackendDir "ssl"
if (-not (Test-Path $sslDir)) {
    New-Item -ItemType Directory -Force -Path $sslDir | Out-Null
}
Write-Host "  [OK] ssl 目录就绪" -ForegroundColor Green

# 检查 .env 文件
$envFile = Join-Path $BackendDir ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "  [警告] .env 文件不存在，使用 .env.example 或默认值" -ForegroundColor Yellow
    Write-Host "  提示: 复制 .env.production 为 .env 并填写实际配置" -ForegroundColor Yellow
}
Write-Host ""

# ============ 停止旧容器 ============
Write-Host "[2/6] 停止旧容器（如有）..." -ForegroundColor Yellow
Set-Location $BackendDir
docker-compose down 2>&1 | Out-Null
Write-Host "  [OK] 已停止旧容器" -ForegroundColor Green

# ============ 构建并启动 ============
if (-not $SkipBuild) {
    Write-Host "[3/6] 构建并启动容器..." -ForegroundColor Yellow
    $buildOutput = docker-compose build --parallel 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [错误] 镜像构建失败" -ForegroundColor Red
        Write-Host $buildOutput -ForegroundColor Red
        exit 1
    }
    Write-Host "  [OK] 镜像构建成功" -ForegroundColor Green
    
    Write-Host "  启动容器..." -ForegroundColor Yellow
    $upOutput = docker-compose up -d 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [错误] 容器启动失败" -ForegroundColor Red
        Write-Host $upOutput -ForegroundColor Red
        exit 1
    }
    Write-Host "  [OK] 容器启动成功" -ForegroundColor Green
} else {
    Write-Host "[3/6] 跳过构建，仅启动容器..." -ForegroundColor Yellow
    docker-compose up -d 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [错误] 容器启动失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "  [OK] 容器启动成功" -ForegroundColor Green
}

# ============ 等待服务就绪 ============
Write-Host "[4/6] 等待服务就绪..." -ForegroundColor Yellow
$maxWait = 60
$waited = 0
$apiHealthy = $false
$nginxRunning = $false

while ($waited -lt $maxWait) {
    Start-Sleep 2
    $waited += 2
    
    # 检查 API 健康状态
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 3 -UseBasicParsing 2>$null
        if ($response.StatusCode -eq 200) {
            $apiHealthy = $true
        }
    } catch {}
    
    # 检查 nginx 是否运行
    $nginxContainer = docker ps --filter "name=ai-workflow-nginx" --format "{{.Names}}" 2>$null
    if ($nginxContainer -eq "ai-workflow-nginx") {
        $nginxRunning = $true
    }
    
    if ($apiHealthy -and $nginxRunning) {
        Write-Host "  [OK] API 健康检查通过" -ForegroundColor Green
        Write-Host "  [OK] Nginx 运行正常" -ForegroundColor Green
        break
    }
    
    if ($waited % 10 -eq 0) {
        Write-Host "  等待中... ($waited/$maxWait 秒)" -ForegroundColor Gray
    }
}

if (-not $apiHealthy) {
    Write-Host "  [警告] API 健康检查未通过，请检查容器日志" -ForegroundColor Yellow
}

if (-not $nginxRunning) {
    Write-Host "  [警告] Nginx 未运行，请检查容器日志" -ForegroundColor Yellow
}

Write-Host ""

# ============ 验证服务 ============
Write-Host "[5/6] 验证服务功能..." -ForegroundColor Yellow

# 测试 1: API 根路径
Write-Host "  测试 1: API 根路径..." -ForegroundColor Gray
try {
    $root = Invoke-WebRequest -Uri "http://localhost:8000/" -TimeoutSec 5 -UseBasicParsing 2>$null
    if ($root.StatusCode -eq 200) {
        Write-Host "    [OK] GET / -> 200" -ForegroundColor Green
    } else {
        Write-Host "    [警告] GET / -> $($root.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "    [错误] GET / 失败: $_" -ForegroundColor Red
}

# 测试 2: API 健康检查
Write-Host "  测试 2: API 健康检查..." -ForegroundColor Gray
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -UseBasicParsing 2>$null
    if ($health.StatusCode -eq 200) {
        Write-Host "    [OK] GET /api/health -> 200" -ForegroundColor Green
    } else {
        Write-Host "    [警告] GET /api/health -> $($health.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "    [错误] GET /api/health 失败: $_" -ForegroundColor Red
}

# 测试 3: Nginx 前端访问
Write-Host "  测试 3: Nginx 前端页面..." -ForegroundColor Gray
try {
    $frontend = Invoke-WebRequest -Uri "http://localhost/" -TimeoutSec 5 -UseBasicParsing 2>$null
    if ($frontend.StatusCode -eq 200 -and $frontend.Content -match "index.html") {
        Write-Host "    [OK] GET / -> 200 (前端页面正常)" -ForegroundColor Green
    } else {
        Write-Host "    [警告] GET / 返回异常内容" -ForegroundColor Yellow
    }
} catch {
    Write-Host "    [错误] GET / 失败: $_" -ForegroundColor Red
}

# 测试 4: Nginx API 代理
Write-Host "  测试 4: Nginx API 代理..." -ForegroundColor Gray
try {
    $proxied = Invoke-WebRequest -Uri "http://localhost/api/health" -TimeoutSec 5 -UseBasicParsing 2>$null
    if ($proxied.StatusCode -eq 200) {
        Write-Host "    [OK] GET /api/health (via Nginx) -> 200" -ForegroundColor Green
    } else {
        Write-Host "    [警告] GET /api/health (via Nginx) -> $($proxied.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "    [错误] GET /api/health (via Nginx) 失败: $_" -ForegroundColor Red
}

# 测试 5: OpenAPI 文档
Write-Host "  测试 5: OpenAPI 文档..." -ForegroundColor Gray
try {
    $docs = Invoke-WebRequest -Uri "http://localhost/docs" -TimeoutSec 5 -UseBasicParsing 2>$null
    if ($docs.StatusCode -eq 200) {
        Write-Host "    [OK] GET /docs -> 200" -ForegroundColor Green
    } else {
        Write-Host "    [警告] GET /docs -> $($docs.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "    [错误] GET /docs 失败: $_" -ForegroundColor Red
}

Write-Host ""

# ============ 容器状态 ============
Write-Host "[6/6] 容器状态..." -ForegroundColor Yellow
docker ps --filter "name=ai-workflow" --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}" 2>$null

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "部署验证完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "访问地址:" -ForegroundColor White
Write-Host "  前端: http://localhost/" -ForegroundColor Cyan
Write-Host "  API:  http://localhost:8000/" -ForegroundColor Cyan
Write-Host "  API:  http://localhost/api/ (通过 Nginx)" -ForegroundColor Cyan
Write-Host "  文档: http://localhost/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "常用命令:" -ForegroundColor White
Write-Host "  查看日志: docker-compose logs -f" -ForegroundColor Gray
Write-Host "  停止服务: docker-compose down" -ForegroundColor Gray
Write-Host "  重启服务: docker-compose restart" -ForegroundColor Gray
Write-Host "  重新构建: docker-compose build --no-cache" -ForegroundColor Gray
Write-Host ""

# 输出到文件
$logFile = Join-Path $BackendDir "deployment-verify.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"$timestamp - 部署验证完成" | Out-File -FilePath $logFile -Append
