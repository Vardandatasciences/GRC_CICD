#!/bin/bash

# =============================================================================
# URGENT NGINX FIX SCRIPT
# =============================================================================
# This script fixes your nginx configuration for SPA routing
# Run this on your server (13.201.54.231)
# =============================================================================

set -e

echo "🚨 URGENT NGINX FIX FOR SPA ROUTING"
echo "===================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Step 1: Backup current config
echo -e "${YELLOW}📦 Backing up current nginx config...${NC}"
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d-%H%M%S)
echo -e "${GREEN}✓ Backup created${NC}"

# Step 2: Create new nginx config
echo -e "${YELLOW}📝 Creating new nginx config...${NC}"
sudo tee /etc/nginx/nginx.conf > /dev/null << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /run/nginx.pid;

include /usr/share/nginx/modules/*.conf;

events {
    worker_connections 1024;
}

http {
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;
    types_hash_max_size 4096;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    include /etc/nginx/conf.d/*.conf;

    server {
        listen 80;
        listen [::]:80;
        server_name localhost 13.201.54.231 15.207.108.158 _;
        
        root /usr/share/nginx/html;
        index index.html;

        include /etc/nginx/default.d/*.conf;

        # Gzip compression
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_proxied any;
        gzip_comp_level 6;
        gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml+rss application/x-javascript;

        # API proxy to Django backend
        location /api/ {
            proxy_pass http://15.207.108.158:8000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }

        # Cache static assets
        location ~* \.(?:css|js)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            try_files $uri =404;
        }

        location ~* \.(?:jpg|jpeg|gif|png|svg|ico|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            try_files $uri =404;
        }

        # SPA routing - THE CRITICAL FIX
        location / {
            try_files $uri $uri/ /index.html;
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            add_header Expires "0";
        }

        # Error pages redirect to SPA
        error_page 404 /index.html;
        error_page 403 /index.html;
        error_page 500 502 503 504 /index.html;
    }
}
EOF

echo -e "${GREEN}✓ New config created${NC}"

# Step 3: Test nginx configuration
echo -e "${YELLOW}🧪 Testing nginx configuration...${NC}"
if sudo nginx -t; then
    echo -e "${GREEN}✓ Configuration test passed${NC}"
else
    echo -e "${RED}❌ Configuration test failed${NC}"
    echo -e "${YELLOW}Restoring backup...${NC}"
    sudo cp /etc/nginx/nginx.conf.backup.* /etc/nginx/nginx.conf
    echo -e "${RED}Backup restored. Please check the configuration manually.${NC}"
    exit 1
fi

# Step 4: Reload nginx
echo -e "${YELLOW}🔄 Reloading nginx...${NC}"
sudo systemctl reload nginx
echo -e "${GREEN}✓ Nginx reloaded${NC}"

# Step 5: Check nginx status
echo -e "${YELLOW}📊 Checking nginx status...${NC}"
if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx is running${NC}"
else
    echo -e "${RED}❌ Nginx is not running${NC}"
    sudo systemctl start nginx
    echo -e "${GREEN}✓ Nginx started${NC}"
fi

# Step 6: Verify index.html exists
echo -e "${YELLOW}🔍 Checking if index.html exists...${NC}"
if [ -f "/usr/share/nginx/html/index.html" ]; then
    echo -e "${GREEN}✓ index.html found${NC}"
else
    echo -e "${RED}❌ index.html not found!${NC}"
    echo -e "${YELLOW}You need to upload your frontend files to /usr/share/nginx/html/${NC}"
fi

# Success message
echo ""
echo "===================================="
echo -e "${GREEN}✅ NGINX CONFIGURATION FIXED!${NC}"
echo "===================================="
echo ""
echo "🧪 Test these URLs now:"
echo "   http://13.201.54.231/login"
echo "   http://13.201.54.231/integration/jira"
echo "   http://13.201.54.231/home"
echo ""
echo "For each URL:"
echo "   ✅ Click it → should load"
echo "   ✅ Refresh (F5) → should load (no 404!)"
echo "   ✅ Copy/paste in new tab → should load"
echo ""
echo "🔧 If you need to restore the old config:"
echo "   sudo cp /etc/nginx/nginx.conf.backup.* /etc/nginx/nginx.conf"
echo "   sudo systemctl reload nginx"
echo ""
echo "===================================="
