#!/bin/bash

# AWS Deployment Script for Vue.js GRC Application
# This script builds and deploys your Vue.js application

set -e  # Exit on any error

echo "🚀 Starting deployment process..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ Error: package.json not found. Are you in the frontend directory?${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Step 1: Installing dependencies...${NC}"
npm install

echo ""
echo -e "${BLUE}🔧 Step 2: Building production bundle...${NC}"
npm run build

if [ ! -d "dist" ]; then
    echo -e "${RED}❌ Error: dist directory not created. Build failed!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Build completed successfully!${NC}"
echo ""
echo -e "${BLUE}📦 Build artifacts are in the 'dist' folder${NC}"
echo ""

# Optional: Uncomment the section below that matches your deployment method

# ========================================
# OPTION 1: Deploy to AWS S3
# ========================================
# echo -e "${BLUE}📤 Step 3: Deploying to S3...${NC}"
# S3_BUCKET="your-bucket-name"
# aws s3 sync dist/ s3://$S3_BUCKET/ --delete
# echo -e "${GREEN}✅ Uploaded to S3${NC}"
# 
# # Invalidate CloudFront cache (if using CloudFront)
# CLOUDFRONT_DISTRIBUTION_ID="YOUR_DISTRIBUTION_ID"
# echo -e "${BLUE}🔄 Invalidating CloudFront cache...${NC}"
# aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_DISTRIBUTION_ID --paths "/*"
# echo -e "${GREEN}✅ CloudFront cache invalidated${NC}"

# ========================================
# OPTION 2: Deploy to EC2 with SCP
# ========================================
# echo -e "${BLUE}📤 Step 3: Deploying to EC2...${NC}"
# EC2_HOST="your-ec2-ip"
# EC2_USER="ubuntu"
# EC2_PATH="/var/www/html"
# PEM_FILE="path/to/your-key.pem"
# 
# scp -i $PEM_FILE -r dist/* $EC2_USER@$EC2_HOST:$EC2_PATH/
# echo -e "${GREEN}✅ Deployed to EC2${NC}"

# ========================================
# OPTION 3: Deploy to Elastic Beanstalk
# ========================================
# echo -e "${BLUE}📤 Step 3: Deploying to Elastic Beanstalk...${NC}"
# eb deploy
# echo -e "${GREEN}✅ Deployed to Elastic Beanstalk${NC}"

echo ""
echo -e "${GREEN}🎉 Deployment process completed!${NC}"
echo ""
echo "📋 Next steps:"
echo "  1. Choose your deployment method (uncomment in this script)"
echo "  2. Or manually upload the 'dist' folder to your server"
echo "  3. Make sure server configuration (.htaccess or nginx.conf) is in place"
echo "  4. Test your deployment:"
echo "     - Login to your app"
echo "     - Navigate to different pages"
echo "     - Refresh the page - sidebar should stay visible"
echo ""
echo "📖 For detailed instructions, see AWS_DEPLOYMENT_GUIDE.md"
echo ""

