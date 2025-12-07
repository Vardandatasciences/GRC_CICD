# ============================================================================
# PowerShell Deployment Script for Windows
# ============================================================================
# This script builds and prepares your frontend for deployment
# Run from: frontend directory
# ============================================================================

Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "🚀 Frontend Build & Deployment Prep" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Clean previous build
Write-Host "📦 Cleaning previous build..." -ForegroundColor Yellow
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
    Write-Host "✓ Cleaned" -ForegroundColor Green
} else {
    Write-Host "✓ No previous build found" -ForegroundColor Green
}

# Step 2: Install dependencies
Write-Host ""
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
npm install
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Step 3: Build production version
Write-Host ""
Write-Host "🔨 Building production version..." -ForegroundColor Yellow
npm run build
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Build completed" -ForegroundColor Green
} else {
    Write-Host "❌ Build failed" -ForegroundColor Red
    exit 1
}

# Step 4: Copy configuration files
Write-Host ""
Write-Host "📋 Copying configuration files..." -ForegroundColor Yellow
if (Test-Path ".htaccess") {
    Copy-Item ".htaccess" "dist\.htaccess"
    Write-Host "✓ Copied .htaccess" -ForegroundColor Green
}
if (Test-Path "web.config") {
    Copy-Item "web.config" "dist\web.config"
    Write-Host "✓ Copied web.config" -ForegroundColor Green
}
Copy-Item "nginx.conf" "dist\nginx.conf"
Write-Host "✓ Copied nginx.conf" -ForegroundColor Green

# Step 5: Verify build
Write-Host ""
Write-Host "🔍 Verifying build..." -ForegroundColor Yellow
if (Test-Path "dist\index.html") {
    Write-Host "✓ index.html found" -ForegroundColor Green
} else {
    Write-Host "❌ index.html not found - build may have failed" -ForegroundColor Red
    exit 1
}

# Step 6: Create deployment package
Write-Host ""
Write-Host "📦 Creating deployment package..." -ForegroundColor Yellow
$deployFile = "deploy-$(Get-Date -Format 'yyyyMMdd-HHmmss').zip"
Compress-Archive -Path "dist\*" -DestinationPath $deployFile -Force
Write-Host "✓ Created: $deployFile" -ForegroundColor Green

# Success
Write-Host ""
Write-Host "=======================================" -ForegroundColor Green
Write-Host "✅ Build Completed Successfully!" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""

Write-Host "Files are ready in the 'dist' folder" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1️⃣  Upload to Server (Choose ONE method):" -ForegroundColor White
Write-Host ""
Write-Host "   Method A: Using WinSCP" -ForegroundColor Cyan
Write-Host "   - Open WinSCP" -ForegroundColor White
Write-Host "   - Connect to: 13.201.54.231" -ForegroundColor White
Write-Host "   - Upload dist\* to: /usr/share/nginx/html/" -ForegroundColor White
Write-Host "   - Upload dist\nginx.conf to: /tmp/nginx.conf" -ForegroundColor White
Write-Host ""
Write-Host "   Method B: Using SCP (from PowerShell/Git Bash)" -ForegroundColor Cyan
Write-Host "   scp -r dist\* root@13.201.54.231:/usr/share/nginx/html/" -ForegroundColor White
Write-Host "   scp nginx.conf root@13.201.54.231:/tmp/nginx.conf" -ForegroundColor White
Write-Host ""
Write-Host "   Method C: Using ZIP package" -ForegroundColor Cyan
Write-Host "   - Upload: $deployFile" -ForegroundColor White
Write-Host "   - Extract on server to: /usr/share/nginx/html/" -ForegroundColor White
Write-Host ""

Write-Host "2️⃣  On Server (SSH into 13.201.54.231):" -ForegroundColor White
Write-Host ""
Write-Host "   sudo cp /tmp/nginx.conf /etc/nginx/conf.d/default.conf" -ForegroundColor White
Write-Host "   sudo nginx -t" -ForegroundColor White
Write-Host "   sudo systemctl reload nginx" -ForegroundColor White
Write-Host ""

Write-Host "3️⃣  Test:" -ForegroundColor White
Write-Host "   http://13.201.54.231/login" -ForegroundColor White
Write-Host "   http://13.201.54.231/integration/jira" -ForegroundColor White
Write-Host ""
Write-Host "=======================================" -ForegroundColor Cyan

# Open dist folder
Write-Host ""
$openFolder = Read-Host "Open dist folder now? (y/n)"
if ($openFolder -eq "y" -or $openFolder -eq "Y") {
    Invoke-Item "dist"
}

