#!/bin/bash

# Configuration
CONTAINER_NAME="grc_backend"
IMAGE=""480940871468.dkr.ecr.ap-south-1.amazonaws.com/grc_backend:latest"  
# Update with your actual image name

# Check if container exists and remove it
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "⏹️  Stopping and removing existing container..."
    docker stop $CONTAINER_NAME || true
    docker rm $CONTAINER_NAME || true
fi

echo "⬇️ Pulling latest backend image..."
docker pull $IMAGE || echo "⚠️  Using existing image"

echo "🚀 Starting new backend container..."

docker run -d \
    --name $CONTAINER_NAME \
    --restart unless-stopped \
    --env-file ~/config.env \
    -p 8000:8000 \
    -v ~/MEDIA_ROOT:/app/MEDIA_ROOT \
    -v ~/Reports:/app/Reports \
    --dns=8.8.8.8 \
    --dns=8.8.4.4 \
    --dns=1.1.1.1 \
    --user 1000:1000 \
    $IMAGE

echo "----------------------------------------"
echo "✅ Deployment Completed Successfully"
echo "----------------------------------------"
docker ps
