#!/bin/bash

echo "================================================"
echo "   Push Media Basher to GitHub"
echo "================================================"
echo ""

# Check if we're in /app
if [ ! -f "/app/install.sh" ]; then
    echo "Error: This script must be run from the system with /app/ directory"
    exit 1
fi

cd /app

# Initialize git if needed
if [ ! -d ".git" ]; then
    git init
    git config user.name "Media Basher Bot"
    git config user.email "bot@mediabasher.com"
fi

# Add all files
echo "Adding all files..."
git add -A

# Create commit
echo "Creating commit..."
git commit -m "Complete Media Basher codebase - v1.0.0

- 50+ API endpoints (FastAPI + MongoDB)
- 18 React pages with dark theme
- Docker container management
- Real-time monitoring & alerts
- Backup & restore system
- Network management
- Storage pools
- And 50+ enterprise features"

# Set remote
git remote remove origin 2>/dev/null
git remote add origin https://github.com/OfficialMikeJ/MEDIA-BASHER.git

echo ""
echo "Ready to push!"
echo ""
echo "To push to GitHub, you need a Personal Access Token:"
echo "1. Go to: https://github.com/settings/tokens"
echo "2. Generate new token (classic)"
echo "3. Select 'repo' scope"
echo "4. Copy the token"
echo ""
echo "Then run:"
echo "  git push https://YOUR_TOKEN@github.com/OfficialMikeJ/MEDIA-BASHER.git main --force"
echo ""
echo "Or set up SSH keys and use:"
echo "  git push origin main --force"
echo ""
