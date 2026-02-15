#!/bin/bash

set -e

echo "========================================="
echo "   MongoDB Fix Script"
echo "========================================="
echo ""

# Check CPU info
echo "Checking CPU capabilities..."
grep -o 'avx[^ ]*' /proc/cpuinfo | sort -u
echo ""

# Stop and remove MongoDB 7.0
echo "Removing MongoDB 7.0..."
sudo systemctl stop mongod || true
sudo apt-get remove -y mongodb-org mongodb-org-server mongodb-org-shell mongodb-org-mongos mongodb-org-tools
sudo rm -rf /var/lib/mongodb
sudo rm -rf /var/log/mongodb
sudo rm -f /etc/apt/sources.list.d/mongodb-org-7.0.list

# Install MongoDB 5.0 (better CPU compatibility)
echo "Installing MongoDB 5.0..."
curl -fsSL https://www.mongodb.org/static/pgp/server-5.0.asc | sudo gpg --dearmor -o /etc/apt/keyrings/mongodb-server-5.0.gpg
echo "deb [ arch=amd64,arm64 signed-by=/etc/apt/keyrings/mongodb-server-5.0.gpg ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/5.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-5.0.list

sudo apt-get update
sudo apt-get install -y mongodb-org

# Recreate data directory
sudo mkdir -p /var/lib/mongodb
sudo chown -R mongodb:mongodb /var/lib/mongodb
sudo mkdir -p /var/log/mongodb
sudo chown -R mongodb:mongodb /var/log/mongodb

# Start MongoDB
sudo systemctl daemon-reload
sudo systemctl enable mongod
sudo systemctl start mongod

echo ""
echo "Waiting for MongoDB to start..."
sleep 5

# Check status
if sudo systemctl is-active --quiet mongod; then
    echo "✓ MongoDB 5.0 is running successfully!"
else
    echo "✗ MongoDB failed to start. Checking logs..."
    sudo journalctl -u mongod -n 20
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
echo "MongoDB fix complete!"
echo "Try logging in now."
echo "========================================="
