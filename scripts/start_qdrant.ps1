# Start Qdrant using Docker Compose
Write-Host "Starting Qdrant Vector Database..." -ForegroundColor Green

# Check if Docker is running
try {
    docker ps 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker is running" -ForegroundColor Green
    }
} catch {
    Write-Host "Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop first" -ForegroundColor Yellow
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Start Qdrant
Write-Host "Starting Qdrant container..." -ForegroundColor Cyan
docker-compose --profile cpu up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nQdrant started successfully!" -ForegroundColor Green
    Write-Host "Qdrant UI: http://localhost:6333/dashboard" -ForegroundColor Cyan
    Write-Host "Waiting for Qdrant to be ready..." -ForegroundColor Yellow
    
    # Wait for Qdrant to be ready
    $maxAttempts = 30
    $attempt = 0
    while ($attempt -lt $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:6333" -TimeoutSec 1 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host "Qdrant is ready!" -ForegroundColor Green
                break
            }
        } catch {
            # Still waiting
        }
        $attempt++
        Start-Sleep -Seconds 1
        Write-Host "." -NoNewline
    }
    
    if ($attempt -eq $maxAttempts) {
        Write-Host "`nWarning: Qdrant may still be starting up" -ForegroundColor Yellow
    }
} else {
    Write-Host "`nFailed to start Qdrant" -ForegroundColor Red
    exit 1
}

Write-Host "`nYou can now run: .venv\Scripts\python.exe start_app.py" -ForegroundColor Cyan

