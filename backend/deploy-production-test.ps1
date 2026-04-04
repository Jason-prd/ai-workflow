# AI鑷姩鍖栧伐浣滄祦 - 鐢熶骇鐜閮ㄧ讲鑴氭湰
# ========================================================
# 鐢ㄩ€? 蹇€熼儴缃?AI鑷姩鍖栧伐浣滄祦 鍒扮敓浜х幆澧?# 浣跨敤: .\deploy-production.ps1 -Domain "your-domain.com" [-Email "admin@example.com"]
# 瑕佹眰: Docker, Docker Compose, 鍩熷悕宸茶В鏋愬埌鏈嶅姟鍣?# ========================================================

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
Write-Host "AI鑷姩鍖栧伐浣滄祦 - 鐢熶骇鐜閮ㄧ讲" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 鍓嶇疆妫€鏌?Write-Host "[1/7] 鍓嶇疆妫€鏌?.." -ForegroundColor Yellow

# 妫€鏌?Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker 鏈畨瑁呮垨鏈坊鍔犲埌 PATH"
    exit 1
}

# 妫€鏌?Docker Compose
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Error "Docker Compose 鏈畨瑁呮垨鏈坊鍔犲埌 PATH"
    exit 1
}

# 妫€鏌?.env 鏂囦欢
$envFile = Join-Path $BackendDir ".env"
if (-not (Test-Path $envFile)) {
    $envExample = Join-Path $BackendDir ".env.production"
    if (Test-Path $envExample) {
        Write-Host "  澶嶅埗 .env.production -> .env" -ForegroundColor Gray
        Copy-Item $envExample $envFile
        Write-Host "  鈿狅笍  璇风紪杈?.env 鏂囦欢锛屽～鍐欐墍鏈夊繀濉彉閲忥紙SECRET_KEY, OPENAI_API_KEY, FEISHU_* 閰嶇疆锛? -ForegroundColor Red
    } else {
        Write-Error ".env 鏂囦欢涓嶅瓨鍦紝涓旀壘涓嶅埌 .env.production 妯℃澘"
        exit 1
    }
}

# 2. SSL 璇佷功澶勭悊
Write-Host "[2/7] SSL 璇佷功閰嶇疆..." -ForegroundColor Yellow

$sslDir = Join-Path $BackendDir "ssl"
if (-not (Test-Path $sslDir)) {
    New-Item -ItemType Directory -Path $sslDir | Out-Null
}

$certFile = Join-Path $sslDir "fullchain.pem"
$keyFile = Join-Path $sslDir "privkey.pem"

if ($UseLetsEncrypt) {
    Write-Host "  浣跨敤 Let's Encrypt 鐢宠鍏嶈垂璇佷功..." -ForegroundColor Gray
    
    # 妫€鏌?certbot
    if (-not (Get-Command certbot -ErrorAction SilentlyContinue)) {
        Write-Host "  瀹夎 certbot..." -ForegroundColor Gray
        # Ubuntu/Debian: apt install certbot
        # CentOS/RHEL: yum install certbot
        Write-Host "  璇峰厛瀹夎 certbot: apt install certbot python3-certbot-nginx" -ForegroundColor Red
        exit 1
    }
    
    # 鐢宠璇佷功
    Write-Host "  鐢宠 Let's Encrypt 璇佷功 (鍩熷悕: $Domain)..." -ForegroundColor Gray
    certbot certonly --nginx -d $Domain -d www.$Domain --non-interactive --agree-tos -m $Email
    
    # 澶嶅埗璇佷功
    $letsencryptCert = "/etc/letsencrypt/live/$Domain/fullchain.pem"
    $letsencryptKey = "/etc/letsencrypt/live/$Domain/privkey.pem"
    
    if (Test-Path $letsencryptCert) {
        Copy-Item $letsencryptCert $certFile -Force
        Copy-Item $letsencryptKey $keyFile -Force
        Write-Host "  鉁?Let's Encrypt 璇佷功宸查厤缃? -ForegroundColor Green
    } else {
        Write-Error "Let's Encrypt 璇佷功鐢宠澶辫触"
        exit 1
    }
} else {
    # 浣跨敤鑷鍚嶈瘉涔︼紙浠呯敤浜庢祴璇曪級
    Write-Host "  鈿狅笍  浣跨敤鑷鍚嶈瘉涔︼紙浠呯敤浜庢祴璇曪紝鐢熶骇鐜璇蜂娇鐢?Let's Encrypt锛? -ForegroundColor Red
    
    if (-not (Test-Path $certFile) -or -not (Test-Path $keyFile)) {
        Write-Host "  鐢熸垚鑷鍚嶈瘉涔?.." -ForegroundColor Gray
        
        # 鐢熸垚 OpenSSL 閰嶇疆
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
        
        # 鐢熸垚璇佷功
        $certFileTemp = Join-Path $sslDir "certificate.crt"
        & openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
            -keyout $keyFile `
            -out $certFileTemp `
            -config $confFile `
            -extensions v3_req 2>$null
        
        # 鍚堝苟璇佷功閾?(鑷鍚嶅彧闇€璇佷功鏈韩)
        Copy-Item $certFileTemp $certFile -Force
        Remove-Item $certFileTemp -Force
        Remove-Item $confFile -Force -ErrorAction SilentlyContinue
        
        Write-Host "  鉁?鑷鍚嶈瘉涔﹀凡鐢熸垚" -ForegroundColor Green
    } else {
        Write-Host "  璇佷功宸插瓨鍦紝璺宠繃鐢熸垚" -ForegroundColor Gray
    }
}

# 3. 鍓嶇鏋勫缓
if (-not $SkipFrontendBuild) {
    Write-Host "[3/7] 鍓嶇鏋勫缓..." -ForegroundColor Yellow
    
    $frontendDir = Join-Path $BackendDir "..\frontend"
    if (Test-Path $frontendDir) {
        Write-Host "  杩涘叆鍓嶇鐩綍: $frontendDir" -ForegroundColor Gray
        Push-Location $frontendDir
        
        Write-Host "  瀹夎渚濊禆..." -ForegroundColor Gray
        npm install 2>&1 | Out-Null
        
        Write-Host "  鎵ц鏋勫缓..." -ForegroundColor Gray
        npm run build
        
        $distDir = Join-Path $frontendDir "dist"
        $frontendDist = Join-Path $BackendDir "frontend-dist"
        
        if (Test-Path $frontendDist) {
            Remove-Item $frontendDist -Recurse -Force
        }
        Copy-Item $distDir $frontendDist -Recurse -Force
        
        Pop-Location
        Write-Host "  鉁?鍓嶇鏋勫缓瀹屾垚" -ForegroundColor Green
    } else {
        Write-Host "  鈿狅笍  鍓嶇鐩綍涓嶅瓨鍦紝璺宠繃鏋勫缓" -ForegroundColor Red
    }
} else {
    Write-Host "[3/7] 鍓嶇鏋勫缓 (璺宠繃)..." -ForegroundColor Gray
}

# 4. 鏇存柊 nginx.conf 鍩熷悕
Write-Host "[4/7] 鏇存柊 Nginx 閰嶇疆..." -ForegroundColor Yellow

$nginxConf = Join-Path $BackendDir "nginx.conf"
if (Test-Path $nginxConf) {
    $content = Get-Content $nginxConf -Raw
    $newContent = $content -replace "your-domain\.com", $Domain
    $newContent = $newContent -replace "www\.your-domain\.com", "www.$Domain"
    Set-Content -Path $nginxConf -Value $newContent -NoNewline -Encoding UTF8
    Write-Host "  鉁?Nginx 閰嶇疆宸叉洿鏂?(鍩熷悕: $Domain)" -ForegroundColor Green
}

# 5. Docker 鏈嶅姟閮ㄧ讲
Write-Host "[5/7] Docker 鏈嶅姟閮ㄧ讲..." -ForegroundColor Yellow

Push-Location $BackendDir

Write-Host "  鍋滄鏃у鍣紙濡傛湁锛?.." -ForegroundColor Gray
docker compose down 2>&1 | Out-Null

Write-Host "  鏋勫缓骞跺惎鍔ㄦ湇鍔?.." -ForegroundColor Gray
docker compose up -d --build

Write-Host "  绛夊緟鏈嶅姟鍚姩..." -ForegroundColor Gray
Start-Sleep -Seconds 10

Pop-Location

# 6. 鍋ュ悍妫€鏌?Write-Host "[6/7] 鍋ュ悍妫€鏌?.." -ForegroundColor Yellow

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
    Write-Host "  绛夊緟鏈嶅姟鍚姩... ($retryCount/$maxRetries)" -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if ($healthOk) {
    Write-Host "  鉁?API 鏈嶅姟鍋ュ悍妫€鏌ラ€氳繃" -ForegroundColor Green
} else {
    Write-Warning "  鈿狅笍  API 鏈嶅姟鍙兘鏈甯稿惎鍔紝璇锋鏌? docker compose logs api"
}

# 7. 閮ㄧ讲瀹屾垚
Write-Host "[7/7] 閮ㄧ讲瀹屾垚!" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "閮ㄧ讲瀹屾垚锛? -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "璁块棶鍦板潃:" -ForegroundColor White
Write-Host "  HTTPS:  https://$Domain" -ForegroundColor Cyan
Write-Host "  API:    https://$Domain/api" -ForegroundColor Cyan
Write-Host "  Docs:   https://$Domain/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "绠＄悊鍛戒护:" -ForegroundColor White
Write-Host "  鏌ョ湅鏃ュ織:    docker compose logs -f" -ForegroundColor Gray
Write-Host "  閲嶅惎鏈嶅姟:    docker compose restart" -ForegroundColor Gray
Write-Host "  鍋滄鏈嶅姟:    docker compose down" -ForegroundColor Gray
Write-Host ""
Write-Host "SSL 璇佷功缁湡 (Let's Encrypt):" -ForegroundColor White
Write-Host "  certbot renew --nginx" -ForegroundColor Gray
Write-Host ""

