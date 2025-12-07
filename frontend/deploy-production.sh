#!/bin/bash

# =============================================================================
# Vue.js SPA Production Deployment Script
# =============================================================================
# This script builds the Vue.js frontend and deploys it with proper SPA routing
# =============================================================================

set -e  # Exit on error

echo "🚀 Starting Vue.js SPA Deployment..."
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Clean previous build
echo -e "${YELLOW}📦 Cleaning previous build...${NC}"
rm -rf dist
echo -e "${GREEN}✓ Cleaned${NC}"

# Step 2: Install dependencies
echo -e "${YELLOW}📥 Installing dependencies...${NC}"
npm install
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 3: Build production version
echo -e "${YELLOW}🔨 Building production version...${NC}"
npm run build
echo -e "${GREEN}✓ Build completed${NC}"

# Step 4: Copy configuration files to dist
echo -e "${YELLOW}📋 Copying configuration files...${NC}"
cp .htaccess dist/.htaccess 2>/dev/null || echo "No .htaccess file found (OK if using nginx)"
cp web.config dist/web.config 2>/dev/null || echo "No web.config file found (OK if not using IIS)"
echo -e "${GREEN}✓ Configuration files copied${NC}"

# Step 5: Verify build output
echo -e "${YELLOW}🔍 Verifying build output...${NC}"
if [ ! -f "dist/index.html" ]; then
    echo -e "${RED}❌ Error: dist/index.html not found!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Build verification passed${NC}"

# Step 6: Display deployment options
echo ""
echo "======================================"
echo -e "${GREEN}✅ Build completed successfully!${NC}"
echo "======================================"
echo ""
echo "Choose your deployment method:"
echo ""
echo "1️⃣  NGINX Deployment:"
echo "   sudo cp -r dist/* /usr/share/nginx/html/"
echo "   sudo cp nginx.conf /etc/nginx/conf.d/default.conf"
echo "   sudo nginx -t && sudo systemctl reload nginx"
echo ""
echo "2️⃣  Apache Deployment:"
echo "   sudo cp -r dist/* /var/www/html/"
echo "   sudo systemctl restart apache2"
echo ""
echo "3️⃣  Django Deployment:"
echo "   # Files are ready in dist/ folder"
echo "   # Django will serve them via the catch-all route"
echo "   cd ../backend"
echo "   python manage.py collectstatic --noinput"
echo "   sudo systemctl restart gunicorn  # or your WSGI server"
echo ""
echo "4️⃣  IIS Deployment (Windows):"
echo "   Copy contents of dist/* to C:\\inetpub\\wwwroot"
echo "   Ensure web.config is present"
echo ""

# Step 7: Quick test option
echo "======================================"
echo "Test locally before deploying?"
echo "Run: npx serve -s dist -l 8080"
echo "Then visit: http://localhost:8080"
echo "======================================"

