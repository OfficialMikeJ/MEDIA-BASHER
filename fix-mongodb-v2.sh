#!/bin/bash

echo "========================================="
echo "   MongoDB Alternative Fix"
echo "========================================="
echo ""

# Stop and remove the failing container
sudo docker stop mongodb 2>/dev/null || true
sudo docker rm mongodb 2>/dev/null || true

# Check the logs from the failed container
echo "Checking what went wrong..."
sudo docker logs mongodb 2>&1 | tail -20 || echo "No logs available"

echo ""
echo "Trying MongoDB 4.4 (better compatibility for older CPUs)..."

# Try MongoDB 4.4 which has the best CPU compatibility
sudo docker run -d \
  --name mongodb \
  --restart always \
  -p 127.0.0.1:27017:27017 \
  -v /opt/media-basher/mongodb-data:/data/db \
  mongo:4.4

echo ""
echo "Waiting for MongoDB to start..."
sleep 10

# Check if MongoDB is running
if sudo docker ps | grep -q mongodb; then
    echo "✓ MongoDB 4.4 is running!"
    
    # Test connection
    sudo docker exec mongodb mongo --eval "db.version()"
    
    echo ""
    echo "Restarting Media Basher backend..."
    sudo systemctl restart media-basher-backend
    sleep 3
    
    if sudo systemctl is-active --quiet media-basher-backend; then
        echo "✓ Backend is running!"
        echo ""
        echo "Try logging in now!"
    fi
else
    echo "✗ MongoDB 4.4 also failed."
    echo ""
    echo "Checking CPU info..."
    lscpu | grep -i flags
    echo ""
    echo "Container logs:"
    sudo docker logs mongodb 2>&1 | tail -30
fi

echo ""
echo "========================================="
