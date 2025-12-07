#!/bin/bash

# =============================================================================
# AWS EC2 Deployment Script for Vue.js SPA
# =============================================================================
# Server IP: 15.207.108.158
# This script deploys to nginx on AWS EC2
# =============================================================================

set -e

echo "🚀 Deploying to AWS EC2 (15.207.108.158)..."
echo "============================================="

# Configuration
SERVER_IP="15.207.108.158"
NGINX_HTML_DIR="/usr/share/nginx/html"
NGINX_CONF_DIR="/etc/nginx/conf.d"
SSH_USER="ubuntu"  # Change this to your SSH user (ec2-user, ubuntu, etc.)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Step 1: Build locally
echo -e "${YELLOW}📦 Building production version locally...${NC}"
npm run build
echo -e "${GREEN}✓ Build completed${NC}"

# Step 2: Copy configuration files
echo -e "${YELLOW}📋 Preparing deployment files...${NC}"
cp nginx.conf dist/nginx.conf
echo -e "${GREEN}✓ Files prepared${NC}"

# Step 3: Create deployment archive
echo -e "${YELLOW}📦 Creating deployment archive...${NC}"
cd dist
tar -czf ../deploy.tar.gz .
cd ..
echo -e "${GREEN}✓ Archive created${NC}"

# Step 4: Upload to server
echo -e "${YELLOW}📤 Uploading to AWS server...${NC}"
echo "Note: You may need to provide SSH key with -i option"
echo "Example: Add -i /path/to/your-key.pem before ${SSH_USER}@${SERVER_IP}"
echo ""

scp deploy.tar.gz ${SSH_USER}@${SERVER_IP}:/tmp/
echo -e "${GREEN}✓ Upload completed${NC}"

# Step 5: Deploy on server
echo -e "${YELLOW}🚀 Deploying on server...${NC}"
ssh ${SSH_USER}@${SERVER_IP} << 'EOF'
    echo "Extracting files..."
    cd /tmp
    sudo tar -xzf deploy.tar.gz -C /usr/share/nginx/html/
    
    echo "Updating nginx configuration..."
    sudo cp /usr/share/nginx/html/nginx.conf /etc/nginx/conf.d/default.conf
    
    echo "Testing nginx configuration..."
    sudo nginx -t
    
    echo "Reloading nginx..."
    sudo systemctl reload nginx
    
    echo "Cleaning up..."
    rm -f /tmp/deploy.tar.gz
    
    echo "✅ Deployment completed!"
EOF

# Step 6: Cleanup local files
echo -e "${YELLOW}🧹 Cleaning up local files...${NC}"
rm -f deploy.tar.gz
echo -e "${GREEN}✓ Cleanup completed${NC}"

# Step 7: Success message
echo ""
echo "============================================="
echo -e "${GREEN}✅ Deployment Successful!${NC}"
echo "============================================="
echo ""
echo "Your application is now live at:"
echo "🌐 http://${SERVER_IP}"
echo ""
echo "Test the SPA routing:"
echo "1. Visit: http://${SERVER_IP}/login"
echo "2. Copy the URL and paste in a new tab"
echo "3. It should load correctly ✅"
echo ""
echo "If you encounter issues:"
echo "- Check nginx logs: sudo tail -f /var/log/nginx/error.log"
echo "- Verify nginx is running: sudo systemctl status nginx"
echo "- Test configuration: sudo nginx -t"
echo "============================================="

