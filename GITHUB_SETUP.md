# Media Basher - Push to GitHub Instructions

## Step 1: Create Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `media-basher`
3. Description: `Enterprise server management dashboard - A modern alternative to swizzin`
4. Choose Public or Private
5. **DO NOT** initialize with README (we already have one)
6. Click "Create repository"

## Step 2: Push Code to GitHub

Run these commands from your `/app` directory:

```bash
cd /app

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit - Media Basher v1.0.0"

# Add your GitHub repository as remote
git remote add origin https://github.com/OfficialMikeJ/media-basher.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Verify Upload

After pushing, verify these files are on GitHub:
- README.md
- INSTALL.md
- install.sh
- backend/ directory
- frontend/ directory

## Step 4: Test Installation Command

Once pushed, users can install with:

```bash
wget https://raw.githubusercontent.com/OfficialMikeJ/media-basher/main/install.sh
sudo bash install.sh
```

## Alternative: GitHub CLI

If you have GitHub CLI installed:

```bash
cd /app
gh repo create OfficialMikeJ/media-basher --public --source=. --remote=origin --push
```

## Files Ready to Push

All files in `/app/` including:
- Complete backend with 50+ API endpoints
- Full React frontend with 13 pages
- Installation script
- Documentation (README.md, INSTALL.md)
- Database models and utilities

Total: ~120+ files ready for deployment!
