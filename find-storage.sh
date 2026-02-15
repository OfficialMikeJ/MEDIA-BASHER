#!/bin/bash

echo "========================================="
echo "   MEDIA BASHER - Storage Finder"
echo "========================================="
echo ""

echo "All mounted filesystems:"
echo "---"
df -h | grep -v tmpfs | grep -v devtmpfs | grep -v loop

echo ""
echo "All block devices:"
echo "---"
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT | grep -v loop

echo ""
echo "Large storage devices (>100GB):"
echo "---"
df -h | awk '$2 ~ /[GT]/ && $2+0 > 100 {print $0}' | grep -v tmpfs

echo ""
echo "========================================="
echo "To add storage to Media Basher:"
echo "========================================="
echo ""
echo "1. Note the MOUNTPOINT from above (e.g., /mnt/storage)"
echo "2. Login to Media Basher at http://YOUR_IP:3000"
echo "3. Go to: Storage → Add Storage Pool"
echo "4. Enter the mount point path"
echo "5. Choose type: local/remote/network"
echo "6. Save - Media Basher will auto-detect the size"
echo ""
echo "Your storage pools will then be available for:"
echo "  - Docker volumes"
echo "  - Media file storage"
echo "  - Application data"
echo "  - Backups"
echo ""
