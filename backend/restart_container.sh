#!/bin/bash

# Script to restart the Django container after DNS fix

echo "Restarting Docker container to apply DNS changes..."
echo ""

# Find the container name/ID
CONTAINER_NAME="grc_backend"

# Check if container exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Found container: ${CONTAINER_NAME}"
    echo "Restarting container..."
    docker restart ${CONTAINER_NAME}
    
    echo ""
    echo "Waiting for container to be ready..."
    sleep 5
    
    echo ""
    echo "Testing DNS resolution from inside container..."
    docker exec ${CONTAINER_NAME} python3 -c "import socket; print('✅ DNS working:', socket.gethostbyname('smtp.gmail.com'))"
    
    echo ""
    echo "✅ Container restarted successfully!"
    echo "The application should now be able to send emails."
else
    echo "❌ Container '${CONTAINER_NAME}' not found."
    echo "Available containers:"
    docker ps -a --format 'table {{.Names}}\t{{.Status}}'
fi

