#!/bin/bash

set -e

SCRIPT_VERSION="1.0.0"
INSTALL_DIR="/opt/media-basher"
SERVICE_NAME="media-basher"

echo "========================================="
echo "   MEDIA BASHER INSTALLER v${SCRIPT_VERSION}"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root"
    echo "Please run: sudo bash install.sh"
    exit 1
fi

# Check Ubuntu version
if [ ! -f /etc/lsb-release ]; then
    echo "Error: This script is designed for Ubuntu systems only"
    exit 1
fi

source /etc/lsb-release
if [ "$DISTRIB_ID" != "Ubuntu" ]; then
    echo "Error: This script requires Ubuntu"
    exit 1
fi

if [ "$DISTRIB_RELEASE" != "24.04" ]; then
    echo "Warning: This script is optimized for Ubuntu 24.04 LTS"
    echo "Current version: ${DISTRIB_RELEASE}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "[1/8] Checking system requirements..."
echo ""

# Check CPU cores
CPU_CORES=$(nproc)
echo "  CPU Cores: ${CPU_CORES}"
if [ "$CPU_CORES" -lt 2 ]; then
    echo "  Warning: Minimum 2 vCPU recommended"
fi

# Check RAM
TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
echo "  RAM: ${TOTAL_RAM_GB}GB"
if [ "$TOTAL_RAM_GB" -lt 4 ]; then
    echo "  Warning: Minimum 4GB RAM recommended"
fi

# Check disk space
DISK_SPACE_GB=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
echo "  Available Disk Space on /: ${DISK_SPACE_GB}GB"
if [ "$DISK_SPACE_GB" -lt 120 ]; then
    echo "  Warning: Root partition has less than 120GB available"
    echo "  Note: You can add additional storage pools after installation"
    echo "  Media Basher supports multiple storage locations"
fi

echo ""
echo "[2/8] Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

echo ""
echo "[3/8] Installing dependencies..."
apt-get install -y -qq \
    curl \
    wget \
    git \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

echo ""
echo "[4/8] Installing Docker..."
if ! command -v docker &> /dev/null; then
    # Add Docker's official GPG key
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # Add Docker repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    systemctl enable docker
    systemctl start docker
    echo "  Docker installed successfully"
else
    echo "  Docker already installed"
fi

echo ""
echo "[5/8] Installing Python 3.11..."
if ! command -v python3.11 &> /dev/null; then
    add-apt-repository ppa:deadsnakes/ppa -y
    apt-get update -qq
    apt-get install -y -qq python3.11 python3.11-venv python3.11-dev python3-pip
    echo "  Python 3.11 installed successfully"
else
    echo "  Python 3.11 already installed"
fi

echo ""
echo "[6/8] Installing Node.js and Yarn..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y -qq nodejs
    npm install -g yarn
    echo "  Node.js and Yarn installed successfully"
else
    echo "  Node.js already installed"
fi

echo ""
echo "[7/8] Installing MongoDB..."
if ! command -v mongod &> /dev/null; then
    curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /etc/apt/keyrings/mongodb-server-7.0.gpg
    echo "deb [ arch=amd64,arm64 signed-by=/etc/apt/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    apt-get update -qq
    apt-get install -y -qq mongodb-org
    systemctl enable mongod
    systemctl start mongod
    echo "  MongoDB installed successfully"
else
    echo "  MongoDB already installed"
fi

echo ""
echo "[8/8] Setting up Media Basher..."

# Create temporary directory for cloning
TEMP_DIR=$(mktemp -d)
echo "  Cloning Media Basher from GitHub..."

# Clone to temp directory first
git clone https://github.com/OfficialMikeJ/MEDIA-BASHER.git ${TEMP_DIR}/media-basher
if [ $? -ne 0 ]; then
    echo "  ERROR: Failed to clone repository"
    echo "  Please ensure the repository is public and accessible"
    rm -rf ${TEMP_DIR}
    exit 1
fi

echo "  Repository cloned successfully"

# Create installation directory structure
mkdir -p ${INSTALL_DIR}/media-basher
rm -rf ${INSTALL_DIR}/media-basher/*

# Copy files to installation directory
cp -r ${TEMP_DIR}/media-basher/* ${INSTALL_DIR}/media-basher/
rm -rf ${TEMP_DIR}

echo "  Files copied to ${INSTALL_DIR}/media-basher"

# Verify directory structure
if [ ! -d "${INSTALL_DIR}/media-basher/backend" ] || [ ! -d "${INSTALL_DIR}/media-basher/frontend" ]; then
    echo "  ERROR: Repository structure is incorrect"
    echo "  Expected backend/ and frontend/ directories"
    ls -la ${INSTALL_DIR}/media-basher
    exit 1
fi

# Setup backend
echo "  Setting up backend..."
cd ${INSTALL_DIR}/media-basher/backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip -qq
pip install -r requirements.txt -qq

# Create backend .env if not exists
if [ ! -f .env ]; then
    cat > .env << EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=media_basher
CORS_ORIGINS=*
JWT_SECRET=$(openssl rand -hex 32)
EOF
fi

deactivate

# Setup frontend
echo "  Setting up frontend..."
cd ${INSTALL_DIR}/media-basher/frontend
yarn install --silent

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

# Create frontend .env if not exists
if [ ! -f .env ]; then
    cat > .env << EOF
REACT_APP_BACKEND_URL=http://${SERVER_IP}:8001
WDS_SOCKET_PORT=3000
ENABLE_HEALTH_CHECK=false
EOF
fi

# Build frontend
yarn build

echo ""
echo "========================================="
echo "   INSTALLATION COMPLETE"
echo "========================================="
echo ""
echo "Create your admin account:"
echo ""

# User setup
read -p "Enter admin username: " ADMIN_USERNAME
while true; do
    read -s -p "Enter admin password: " ADMIN_PASSWORD
    echo
    read -s -p "Confirm admin password: " ADMIN_PASSWORD_CONFIRM
    echo
    if [ "$ADMIN_PASSWORD" = "$ADMIN_PASSWORD_CONFIRM" ]; then
        break
    else
        echo "Passwords do not match. Please try again."
    fi
done

read -p "Enter admin email (optional): " ADMIN_EMAIL

# Create user via API (will need to start server first)
echo ""
echo "Creating admin user..."

# Start services temporarily
cd ${INSTALL_DIR}/media-basher/backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001 > /dev/null 2>&1 &
BACKEND_PID=$!
sleep 5

# Create user
curl -s -X POST http://localhost:8001/api/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"${ADMIN_USERNAME}\", \"password\": \"${ADMIN_PASSWORD}\", \"email\": \"${ADMIN_EMAIL}\"}" > /dev/null

# Seed apps
curl -s -X POST http://localhost:8001/api/seed-apps > /dev/null

kill $BACKEND_PID
deactivate

echo ""
echo "========================================="
echo "   SETUP COMPLETE"
echo "========================================="
echo ""
echo "Access Media Basher at:"
echo ""
echo "  Frontend: http://${SERVER_IP}:3000"
echo "  Backend:  http://${SERVER_IP}:8001"
echo ""
echo "Login credentials:"
echo "  Username: ${ADMIN_USERNAME}"
echo "  Password: [as configured]"
echo ""
echo "IMPORTANT - Large Storage Setup:"
echo "========================================="
echo "If you have additional storage mounted (like your 3.5TiB pool),"
echo "you can add it in Media Basher:"
echo ""
echo "  1. Login to Media Basher"
echo "  2. Go to Storage → Add Storage Pool"
echo "  3. Enter your mount point (e.g., /mnt/storage, /data)"
echo "  4. Media Basher will detect the full size automatically"
echo ""
echo "To find your storage mount point, run:"
echo "  df -h | grep -E 'T|G' | grep -v tmpfs"
echo ""
echo "To start the services manually:"
echo "  Backend:  cd ${INSTALL_DIR}/media-basher/backend && source venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8001"
echo "  Frontend: cd ${INSTALL_DIR}/media-basher/frontend && yarn start"
echo ""
echo "To set up as a system service, create systemd unit files."
echo ""
echo "========================================="
