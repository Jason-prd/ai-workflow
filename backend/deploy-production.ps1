# AI自动化工作流 - 生产环境部署脚本
# ========================================================
# 用途: 快速部署 AI自动化工作流 到生产环境
# 使用: .\deploy-production.ps1 -Domain "your-domain.com" [-Email "admin@example.com"]
# 要求: Docker, Docker Compose, 域名已解析到服务器
# ========================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$Domain,
    
    [Parameter(Mandatory=$false)]
    [string]$Email = "admin@$Domain",
    
    [Parameter(Mandatory=$false)]
    [switch]$UseLetsEncrypt,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = "Stop"
$BackendDir = $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI自动化工作流 - 生产环境部署" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 前置检查
Write-Host "[1/7] 前置检查..." -ForegroundColor Yellow

# 检查 Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker 未安装或未添加到 PATH"
    exit 1
}

# 检查 Docker Compose
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Error "Docker Compose 未安装或未添加到 PATH"
    exit 1
}

# 检查 .env 文件
$envFile = Join-Path $BackendDir ".env"
if (-not (Test-Path $envFile)) {
    $envExample = Join-Path $BackendDir ".env.production"
    if (Test-Path $envExample) {
        Write-Host "  复制 .env.production -> .env" -ForegroundColor Gray
        Copy-Item $envExample $envFile
        Write-Host "  ⚠️  请编辑 .env 文件，填写所有必填变量（SECRET_KEY, OPENAI_API_KEY, FEISHU_* 配置）" -ForegroundColor Red
    } else {
        Write-Error ".env 文件不存在，且找不到 .env.production 模板"
        exit 1
    }
}

# 2. SSL 证书处理
Write-Host "[2/7] SSL 证书配置..." -ForegroundColor Yellow

$sslDir = Join-Path $BackendDir "ssl"
if (-not (Test-Path $sslDir)) {
    New-Item -ItemType Directory -Path $sslDir | Out-Null
}

$certFile = Join-Path $sslDir "fullchain.pem"
$keyFile = Join-Path $sslDir "privkey.pem"

if ($UseLetsEncrypt) {
    Write-Host "  使用 Let's Encrypt 申请免费证书..." -ForegroundColor Gray
    
    # 检查 certbot
    if (-not (Get-Command certbot -ErrorAction SilentlyContinue)) {
        Write-Host "  安装 certbot..." -ForegroundColor Gray
        # Ubuntu/Debian: apt install certbot
        # CentOS/RHEL: yum install certbot
        Write-Host "  请先安装 certbot: apt install certbot python3-certbot-nginx" -ForegroundColor Red
        exit 1
    }
    
    # 申请证书
    Write-Host "  申请 Let's Encrypt 证书 (域名: $Domain)..." -ForegroundColor Gray
    certbot certonly --nginx -d $Domain -d www.$Domain --non-interactive --agree-tos -m $Email
    
    # 复制证书
    $letsencryptCert = "/etc/letsencrypt/live/$Domain/fullchain.pem"
    $letsencryptKey = "/etc/letsencrypt/live/$Domain/privkey.pem"
    
    if (Test-Path $letsencryptCert) {
        Copy-Item $letsencryptCert $certFile -Force
        Copy-Item $letsencryptKey $keyFile -Force
        Write-Host "  ✅ Let's Encrypt 证书已配置" -ForegroundColor Green
    } else {
        Write-Error "Let's Encrypt 证书申请失败"
        exit 1
    }
} else {
    # 使用自签名证书（仅用于测试）
    Write-Host "  ⚠️  使用自签名证书（仅用于测试，生产环境请使用 Let's Encrypt）" -ForegroundColor Red
    
    if (-not (Test-Path $certFile) -or -not (Test-Path $keyFile)) {
        Write-Host "  生成自签名证书..." -ForegroundColor Gray
        
        # 生成 OpenSSL 配置
        $opensslConf = @"
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
x509_extensions = v3_req

[dn]
C = CN
ST = State
L = City
O = AI Workflow
CN = $Domain

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = $Domain
DNS.2 = www.$Domain
DNS.3 = localhost
IP.1 = 127.0.0.1
"@
        
        $confFile = Join-Path $sslDir "openssl.cnf"
        $opensslConf | Out-File -FilePath $confFile -Encoding UTF8
        
        # 生成证书
        $certFileTemp = Join-Path $sslDir "certificate.crt"
        & openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
            -keyout $keyFile `
            -out $certFileTemp `
            -config $confFile `
            -extensions v3_req 2>$null
        
        # 合并证书链 (自签名只需证书本身)
        Copy-Item $certFileTemp $certFile -Force
        Remove-Item $certFileTemp -Force
        Remove-Item $confFile -Force -ErrorAction SilentlyContinue
        
        Write-Host "  ✅ 自签名证书已生成" -ForegroundColor Green
    } else {
        Write-Host "  证书已存在，跳过生成" -ForegroundColor Gray
    }
}

# 3. 前端构建
if (-not $SkipFrontendBuild) {
    Write-Host "[3/7] 前端构建..." -ForegroundColor Yellow
    
    $frontendDir = Join-Path $BackendDir "..\frontend"
    if (Test-Path $frontendDir) {
        Write-Host "  进入前端目录: $frontendDir" -ForegroundColor Gray
        Push-Location $frontendDir
        
        Write-Host "  安装依赖..." -ForegroundColor Gray
        npm install 2>&1 | Out-Null
        
        Write-Host "  执行构建..." -ForegroundColor Gray
        npm run build
        
        $distDir = Join-Path $frontendDir "dist"
        $frontendDist = Join-Path $BackendDir "frontend-dist"
        
        if (Test-Path $frontendDist) {
            Remove-Item $frontendDist -Recurse -Force
        }
        Copy-Item $distDir $frontendDist -Recurse -Force
        
        Pop-Location
        Write-Host "  ✅ 前端构建完成" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  前端目录不存在，跳过构建" -ForegroundColor Red
    }
} else {
    Write-Host "[3/7] 前端构建 (跳过)..." -ForegroundColor Gray
}

# 4. 更新 nginx.conf 域名
Write-Host "[4/7] 更新 Nginx 配置..." -ForegroundColor Yellow

$nginxConf = Join-Path $BackendDir "nginx.conf"
if (Test-Path $nginxConf) {
    $content = Get-Content $nginxConf -Raw
    $newContent = $content -replace "your-domain\.com", $Domain
    $newContent = $newContent -replace "www\.your-domain\.com", "www.$Domain"
    # 使用 .NET 写入避免 BOM（Set-Content 默认会加 BOM）
    [System.IO.File]::WriteAllText($nginxConf, $newContent, (New-Object System.Text.UTF8Encoding $false))
    Write-Host "  ✅ Nginx 配置已更新 (域名: $Domain)" -ForegroundColor Green
}

# 5. Docker 服务部署
Write-Host "[5/7] Docker 服务部署..." -ForegroundColor Yellow

Push-Location $BackendDir

Write-Host "  停止旧容器（如有）..." -ForegroundColor Gray
$null = docker compose down 2>$null  # 抑制 stderr 警告输出

Write-Host "  构建并启动服务..." -ForegroundColor Gray
docker compose up -d --build

Write-Host "  等待服务启动..." -ForegroundColor Gray
Start-Sleep -Seconds 10

Pop-Location

# 6. 健康检查
Write-Host "[6/7] 健康检查..." -ForegroundColor Yellow

$maxRetries = 30
$retryCount = 0
$healthOk = $false

while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $healthOk = $true
            break
        }
    } catch {}
    
    $retryCount++
    Write-Host "  等待服务启动... ($retryCount/$maxRetries)" -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if ($healthOk) {
    Write-Host "  ✅ API 服务健康检查通过" -ForegroundColor Green
} else {
    Write-Warning "  ⚠️  API 服务可能未正常启动，请检查: docker compose logs api"
}

# 7. 部署完成
Write-Host "[7/7] 部署完成!" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "部署完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "访问地址:" -ForegroundColor White
Write-Host "  HTTPS:  https://$Domain" -ForegroundColor Cyan
Write-Host "  API:    https://$Domain/api" -ForegroundColor Cyan
Write-Host "  Docs:   https://$Domain/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "管理命令:" -ForegroundColor White
Write-Host "  查看日志:    docker compose logs -f" -ForegroundColor Gray
Write-Host "  重启服务:    docker compose restart" -ForegroundColor Gray
Write-Host "  停止服务:    docker compose down" -ForegroundColor Gray
Write-Host ""
Write-Host "SSL 证书续期 (Let's Encrypt):" -ForegroundColor White
Write-Host "  certbot renew --nginx" -ForegroundColor Gray
Write-Host ""
