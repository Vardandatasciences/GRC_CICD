# Docker Deployment Script for GRC Backend (PowerShell)
# This script rebuilds and restarts the Docker container with the latest code

Write-Host "🚀 Starting Docker deployment..." -ForegroundColor Green

# Navigate to backend directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Stop existing containers
Write-Host "⏹️  Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Rebuild the image
Write-Host "🔨 Rebuilding Docker image..." -ForegroundColor Yellow
docker-compose build --no-cache

# Start the containers
Write-Host "▶️  Starting containers..." -ForegroundColor Yellow
docker-compose up -d

# Wait a moment for the container to start
Start-Sleep -Seconds 3

# Check container status
Write-Host "📊 Container status:" -ForegroundColor Cyan
docker-compose ps

# Show recent logs
Write-Host "📋 Recent logs:" -ForegroundColor Cyan
docker-compose logs --tail=50 backend

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "🔍 Monitor logs with: docker-compose logs -f backend" -ForegroundColor Cyan




