#!/bin/bash

echo "========================================="
echo "   Media Basher Complete Fix"
echo "========================================="
echo ""

cd /opt/media-basher/backend

echo "Backing up current files..."
cp server.py server_backup_$(date +%s).py 2>/dev/null || true
cp auth_utils.py auth_utils_backup_$(date +%s).py 2>/dev/null || true

echo "Downloading updated files..."
wget -q https://raw.githubusercontent.com/OfficialMikeJ/MEDIA-BASHER/main/backend/server.py -O server.py
wget -q https://raw.githubusercontent.com/OfficialMikeJ/MEDIA-BASHER/main/backend/auth_utils.py -O auth_utils.py

echo "Verifying files were downloaded..."
if grep -q "auth/me" server.py; then
    echo "✓ server.py updated successfully"
else
    echo "✗ server.py update failed"
    exit 1
fi

if grep -q "PostgreSQL" auth_utils.py; then
    echo "✓ auth_utils.py updated successfully"
else
    echo "✗ auth_utils.py update failed"
    exit 1
fi

echo ""
echo "Restarting backend service..."
sudo systemctl restart media-basher-backend

sleep 3

echo ""
echo "Checking service status..."
if sudo systemctl is-active --quiet media-basher-backend; then
    echo "✓ Backend is running"
else
    echo "✗ Backend failed to start"
    echo "Logs:"
    sudo journalctl -u media-basher-backend -n 20 --no-pager
    exit 1
fi

echo ""
echo "Testing endpoints..."
echo "1. Testing /api/auth/register..."
REGISTER_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user","password":"test123"}')

if [ "$REGISTER_RESPONSE" = "200" ] || [ "$REGISTER_RESPONSE" = "400" ]; then
    echo "✓ Register endpoint working (HTTP $REGISTER_RESPONSE)"
else
    echo "✗ Register endpoint failed (HTTP $REGISTER_RESPONSE)"
fi

echo ""
echo "2. Testing /api/auth/login..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"mike","password":"test123"}')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo "✓ Login successful, token received"
    
    echo ""
    echo "3. Testing /api/auth/me..."
    ME_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X GET http://localhost:8001/api/auth/me \
      -H "Authorization: Bearer $TOKEN")
    
    if [ "$ME_RESPONSE" = "200" ]; then
        echo "✓ /api/auth/me working (HTTP $ME_RESPONSE)"
    else
        echo "✗ /api/auth/me failed (HTTP $ME_RESPONSE)"
    fi
    
    echo ""
    echo "4. Testing /api/containers/list..."
    CONTAINERS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X GET http://localhost:8001/api/containers/list \
      -H "Authorization: Bearer $TOKEN")
    
    if [ "$CONTAINERS_RESPONSE" = "200" ]; then
        echo "✓ /api/containers/list working (HTTP $CONTAINERS_RESPONSE)"
    else
        echo "✗ /api/containers/list failed (HTTP $CONTAINERS_RESPONSE)"
    fi
else
    echo "✗ Login failed, no token received"
    echo "Response: $LOGIN_RESPONSE"
fi

echo ""
echo "========================================="
echo "Fix script complete!"
echo ""
echo "Try logging in to Media Basher now:"
echo "http://$(hostname -I | awk '{print $1}'):3000"
echo "========================================="
