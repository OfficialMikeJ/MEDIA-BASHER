# Media Basher - Installation & Deployment Guide

## Quick Setup

### For Ubuntu 24.04 LTS

```bash
# Download and run installer
wget https://raw.githubusercontent.com/OfficialMikeJ/media-basher/main/install.sh
sudo bash install.sh
```

The installer will:
1. Check system requirements
2. Install Docker, Docker Compose, Python 3.11, Node.js 20, MongoDB
3. Set up backend and frontend
4. Create admin user account
5. Seed official application templates

## Manual Installation

### Prerequisites
- Ubuntu 24.04 LTS (64-bit)
- Minimum: 2 vCPU, 4GB RAM, 120GB Storage
- Recommended: 6 vCPU, 32GB RAM, 1TB Storage

### Step 1: System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y curl wget git build-essential
```

### Step 2: Install Docker

```bash
# Add Docker repository
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start Docker
sudo systemctl enable docker
sudo systemctl start docker
```

### Step 3: Install Python 3.11

```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
```

### Step 4: Install Node.js 20

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt install -y nodejs
sudo npm install -g yarn
```

### Step 5: Install MongoDB

```bash
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | sudo gpg --dearmor -o /etc/apt/keyrings/mongodb-server-7.0.gpg
echo "deb [ arch=amd64,arm64 signed-by=/etc/apt/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl enable mongod
sudo systemctl start mongod
```

### Step 6: Setup Media Basher

```bash
# Clone repository
git clone https://github.com/yourusername/media-basher.git
cd media-basher

# Setup backend
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create backend .env
cat > .env << EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=media_basher
CORS_ORIGINS=*
JWT_SECRET=$(openssl rand -hex 32)
EOF

# Setup frontend
cd ../frontend
yarn install

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

# Create frontend .env
cat > .env << EOF
REACT_APP_BACKEND_URL=http://${SERVER_IP}:8001
WDS_SOCKET_PORT=3000
ENABLE_HEALTH_CHECK=false
EOF

# Build frontend
yarn build
```

### Step 7: Start Services

**Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001
```

**Frontend (in another terminal):**
```bash
cd frontend
yarn start
```

### Step 8: Create Admin User

```bash
# Register admin user via API
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your_secure_password",
    "email": "admin@example.com"
  }'

# Seed official apps
curl -X POST http://localhost:8001/api/seed-apps
```

## Production Deployment

### Using systemd Services

Create backend service:
```bash
sudo nano /etc/systemd/system/media-basher-backend.service
```

```ini
[Unit]
Description=Media Basher Backend
After=network.target mongod.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/media-basher/backend
Environment="PATH=/opt/media-basher/backend/venv/bin"
ExecStart=/opt/media-basher/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

Create frontend service:
```bash
sudo nano /etc/systemd/system/media-basher-frontend.service
```

```ini
[Unit]
Description=Media Basher Frontend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/media-basher/frontend
ExecStart=/usr/bin/yarn start
Restart=always
Environment="PORT=3000"

[Install]
WantedBy=multi-user.target
```

Enable and start services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable media-basher-backend
sudo systemctl enable media-basher-frontend
sudo systemctl start media-basher-backend
sudo systemctl start media-basher-frontend
```

### Nginx Reverse Proxy (Optional)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Configuration

### Environment Variables

**Backend (.env):**
- `MONGO_URL` - MongoDB connection string (default: mongodb://localhost:27017)
- `DB_NAME` - Database name (default: media_basher)
- `CORS_ORIGINS` - Allowed CORS origins (default: *)
- `JWT_SECRET` - Secret key for JWT tokens (generate with `openssl rand -hex 32`)

**Frontend (.env):**
- `REACT_APP_BACKEND_URL` - Backend API URL
- `WDS_SOCKET_PORT` - Webpack dev server port
- `ENABLE_HEALTH_CHECK` - Health check enabled (default: false)

### Security Recommendations

1. **Change Default Credentials**: Immediately change the admin password after first login
2. **Use Strong JWT Secret**: Generate a secure random string for JWT_SECRET
3. **Enable Firewall**: Only expose necessary ports (80, 443, 3000, 8001)
4. **SSL/TLS**: Use Let's Encrypt for HTTPS in production
5. **Database Security**: Enable MongoDB authentication in production
6. **Regular Updates**: Keep Docker, Node.js, Python, and system packages updated

### Port Configuration

- Frontend: 3000 (React development server)
- Backend: 8001 (FastAPI)
- MongoDB: 27017 (internal)
- Docker: 2375/2376 (Docker API)

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
journalctl -u media-basher-backend -n 50

# Verify MongoDB is running
sudo systemctl status mongod

# Check port availability
sudo netstat -tulpn | grep 8001
```

### Frontend Build Errors

```bash
# Clear cache and rebuild
cd frontend
rm -rf node_modules package-lock.json yarn.lock
yarn install
yarn build
```

### Docker Connection Issues

```bash
# Verify Docker is running
sudo systemctl status docker

# Test Docker connectivity
docker ps

# Add user to docker group
sudo usermod -aG docker $USER
```

### Database Connection Errors

```bash
# Check MongoDB status
sudo systemctl status mongod

# View MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# Restart MongoDB
sudo systemctl restart mongod
```

## Updating Media Basher

```bash
# Pull latest changes
cd /opt/media-basher
git pull

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
deactivate

# Update frontend
cd ../frontend
yarn install
yarn build

# Restart services
sudo systemctl restart media-basher-backend
sudo systemctl restart media-basher-frontend
```

## Backup & Recovery

### Backup Database

```bash
# Create MongoDB backup
mongodump --db media_basher --out /backup/media-basher-$(date +%Y%m%d)

# Compress backup
tar -czf /backup/media-basher-$(date +%Y%m%d).tar.gz /backup/media-basher-$(date +%Y%m%d)
```

### Restore Database

```bash
# Extract backup
tar -xzf /backup/media-basher-YYYYMMDD.tar.gz

# Restore MongoDB
mongorestore --db media_basher /backup/media-basher-YYYYMMDD/media_basher
```

## Support

- **Documentation**: See README.md for feature documentation
- **Issues**: This is a community project with no official support
- **Custom Apps**: Add via the third-party app store interface

## License

MIT License - Use at your own risk with no warranty or support.
