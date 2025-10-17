# Check Docker Status
Write-Host "`nDocker Status Checker" -ForegroundColor Cyan
Write-Host "=" * 50

# Check if Docker Desktop process is running
$dockerProcess = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
if ($dockerProcess) {
    Write-Host "[OK] Docker Desktop is running" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Docker Desktop is not running" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again" -ForegroundColor Yellow
    exit 1
}

# Check if Docker daemon is responding
Write-Host "`nChecking Docker daemon..." -ForegroundColor Cyan
try {
    $dockerVersion = docker version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Docker daemon is responding" -ForegroundColor Green
        docker version --format "{{.Server.Version}}"
    } else {
        Write-Host "[WAITING] Docker is still starting up..." -ForegroundColor Yellow
        Write-Host "This can take 30-60 seconds. Please wait and try again." -ForegroundColor Yellow
        
        Write-Host "`nTroubleshooting steps:" -ForegroundColor Cyan
        Write-Host "1. Check Docker Desktop system tray icon" -ForegroundColor White
        Write-Host "2. Ensure WSL 2 is installed: wsl --update" -ForegroundColor White
        Write-Host "3. Restart Docker Desktop if it's stuck" -ForegroundColor White
        exit 1
    }
} catch {
    Write-Host "[ERROR] Cannot connect to Docker" -ForegroundColor Red
    exit 1
}

# Try to list containers
Write-Host "`nChecking container access..." -ForegroundColor Cyan
try {
    docker ps | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Docker is fully operational" -ForegroundColor Green
        
        # Check if Qdrant is running
        $qdrantRunning = docker ps --filter "name=qdrant" --format "{{.Names}}"
        if ($qdrantRunning) {
            Write-Host "[OK] Qdrant container is running" -ForegroundColor Green
        } else {
            Write-Host "[INFO] Qdrant is not running yet" -ForegroundColor Yellow
            Write-Host "Run: .\start_qdrant.ps1" -ForegroundColor Cyan
        }
        
        Write-Host "`n" + "=" * 50
        Write-Host "Docker is ready! You can now start Qdrant and the application." -ForegroundColor Green
        Write-Host "=" * 50
    }
} catch {
    Write-Host "[ERROR] Docker daemon error" -ForegroundColor Red
    exit 1
}

