#!/bin/bash

echo "========================================="
echo "   MongoDB Docker Fix"
echo "========================================="
echo ""

# Stop and remove broken MongoDB
echo "Stopping existing MongoDB..."
sudo systemctl stop mongod || true
sudo systemctl disable mongod || true

# Remove MongoDB packages
sudo apt-get purge -y mongodb-org* || true
sudo apt-get autoremove -y

# Remove MongoDB data (we'll recreate it)
sudo rm -rf /var/lib/mongodb_backup
sudo mv /var/lib/mongodb /var/lib/mongodb_backup 2>/dev/null || true

# Stop and remove any existing MongoDB container
echo "Setting up MongoDB in Docker..."
sudo docker stop mongodb 2>/dev/null || true
sudo docker rm mongodb 2>/dev/null || true

# Create MongoDB data directory
sudo mkdir -p /opt/media-basher/mongodb-data
sudo chmod 777 /opt/media-basher/mongodb-data

# Run MongoDB in Docker (version 5.0 for broader CPU compatibility)
sudo docker run -d \
  --name mongodb \
  --restart always \
  -p 127.0.0.1:27017:27017 \
  -v /opt/media-basher/mongodb-data:/data/db \
  mongo:5.0

echo ""
echo "Waiting for MongoDB to start..."
sleep 10

# Check if MongoDB is running
if sudo docker ps | grep -q mongodb; then
    echo "✓ MongoDB is running in Docker!"
else
    echo "✗ MongoDB failed to start. Checking logs..."
    sudo docker logs mongodb
    exit 1
fi

# Test MongoDB connection
echo "Testing MongoDB connection..."
if sudo docker exec mongodb mongosh --eval "db.version()" 2>/dev/null; then
    echo "✓ MongoDB connection successful!"
else
    echo "Trying legacy mongo shell..."
    sudo docker exec mongodb mongo --eval "db.version()"
fi

echo ""
echo "Restarting Media Basher backend..."
sudo systemctl restart media-basher-backend

sleep 3

if sudo systemctl is-active --quiet media-basher-backend; then
    echo "✓ Backend is running!"
else
    echo "✗ Backend failed. Check logs with: sudo journalctl -u media-basher-backend -n 50"
fi

echo ""
echo "========================================="
echo "MongoDB Docker Setup Complete!"
echo ""
echo "MongoDB is now running in Docker and will"
echo "automatically start when the system reboots."
echo ""
echo "Useful commands:"
echo "  Check status: sudo docker ps | grep mongodb"
echo "  View logs:    sudo docker logs mongodb"
echo "  Restart:      sudo docker restart mongodb"
echo "========================================="
