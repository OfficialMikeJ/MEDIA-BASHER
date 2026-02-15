# Media Basher

A powerful server management dashboard for managing Docker containers, media servers, and storage pools. Built as a modern alternative to swizzin with enhanced features and a sleek dark UI.

![Media Basher](https://img.shields.io/badge/version-1.0.0-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## Features

### Core Functionality
- **Docker Container Management** - Full control over Docker containers with start/stop/remove operations
- **Application Marketplace** - Official and custom app templates for easy installation
- **System Monitoring** - Real-time CPU, RAM, storage, and GPU metrics
- **Storage Pool Management** - Add and manage local, remote, and network storage
- **DDNS Support** - Built-in No-IP integration for dynamic DNS
- **SSL/TLS** - Automatic Let's Encrypt certificate management
- **User Authentication** - Secure JWT-based authentication system

### System Requirements

#### Minimum
- 2 vCPU
- 4GB RAM
- 120GB Storage
- Ubuntu Server LTS 24.04 64-bit

#### Recommended
- 6 vCPU
- 32GB RAM
- 1TB Storage
- Ubuntu Server LTS 24.04 64-bit

## Installation

### Quick Install

```bash
wget https://raw.githubusercontent.com/OfficialMikeJ/MEDIA-BASHER/main/install.sh
sudo bash install.sh
```

### Manual Installation

1. **Clone the repository**
```bash
git clone https://github.com/OfficialMikeJ/MEDIA-BASHER.git
cd MEDIA-BASHER
```

2. **Run the installer**
```bash
sudo bash install.sh
```

3. **Follow the prompts** to create your admin account

4. **Access the dashboard**
```
http://YOUR_SERVER_IP:3000
```

## What the Installer Does

The `install.sh` script automatically:

1. ✅ Checks system requirements
2. ✅ Installs Docker & Docker Compose
3. ✅ Installs Python 3.11 with required packages
4. ✅ Installs Node.js 20 and Yarn
5. ✅ Installs MongoDB 7.0
6. ✅ Sets up backend with virtual environment
7. ✅ Builds frontend React application
8. ✅ Creates initial admin user
9. ✅ Seeds official application templates

## Supported Applications

### Official Apps (Pre-configured)
- **Jellyfin** - Free Software Media System
- **Jellyseerr** - Request management and media discovery
- **Transmission** - BitTorrent client
- **Sonarr** - TV show management
- **Radarr** - Movie management
- **Plex** - Media streaming platform
- **Portainer** - Container management UI

### Custom Apps
Add any Docker-based application through the custom app interface.

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **MongoDB** - Document database
- **Docker SDK** - Container management
- **psutil** - System monitoring
- **PyNVML** - GPU monitoring
- **JWT** - Authentication

### Frontend
- **React 19** - UI framework
- **Tailwind CSS** - Styling
- **Shadcn/UI** - Component library
- **Recharts** - Data visualization
- **Axios** - HTTP client

## Usage

### Starting Services

**Backend:**
```bash
cd /opt/media-basher/backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001
```

**Frontend:**
```bash
cd /opt/media-basher/frontend
yarn start
```

### Installing Applications

1. Navigate to **Applications** page
2. Browse official or custom apps
3. Click **Install** on desired application
4. Application will be pulled from Docker Hub and started automatically

### Managing Containers

1. Navigate to **Containers** page
2. View all running and stopped containers
3. Start, stop, or remove containers as needed

### Adding Storage Pools

1. Navigate to **Storage** page
2. Click **Add Storage**
3. Provide mount point and pool details
4. Monitor storage usage in real-time

### Configuring DDNS and SSL

1. Navigate to **Settings** page
2. Enable DDNS and configure No-IP credentials
3. Enable SSL and provide email for Let's Encrypt
4. Save settings

## API Documentation

Once the backend is running, access the interactive API documentation at:
- Swagger UI: `http://YOUR_SERVER_IP:8001/docs`
- ReDoc: `http://YOUR_SERVER_IP:8001/redoc`

## Security

- JWT-based authentication with secure password hashing (bcrypt)
- Environment variables for sensitive configuration
- CORS protection
- First-login system requirements popup
- No support provided (use at your own risk)

## Contributing

Media Basher is designed to be extensible:

1. **Adding Custom Apps**: Use the UI to add any Docker-based application
2. **Third-Party App Store**: Upload custom app templates via FTP or terminal
3. **No Official Support**: This is a community-driven project

## Roadmap

- [ ] Android monitoring application
- [ ] Advanced GPU monitoring and allocation
- [ ] RAM caching for faster file transfers
- [ ] Automated backup systems
- [ ] Multi-user support with permissions
- [ ] Docker Compose file upload support
- [ ] Real-time log viewing
- [ ] Container resource limits configuration

## License

MIT License - Use at your own risk. No support provided.

## Credits

Inspired by [swizzin](https://swizzin.ltd) with a modern twist.

---

**Note**: This software is provided as-is with no warranty or support. Users are responsible for their own server security and management.