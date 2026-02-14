from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import docker
import psutil
import pynvml
import shutil

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Docker client
try:
    docker_client = docker.from_env()
except Exception as e:
    logging.warning(f"Docker not available: {e}")
    docker_client = None

# JWT settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'media-basher-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ============ MODELS ============

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    first_login: bool = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

class SystemMetrics(BaseModel):
    cpu_percent: float
    cpu_count: int
    ram_total: int
    ram_used: int
    ram_percent: float
    storage_total: int
    storage_used: int
    storage_percent: float
    gpu_info: Optional[Dict[str, Any]] = None

class DockerContainer(BaseModel):
    id: str
    name: str
    image: str
    status: str
    ports: Optional[Dict[str, Any]] = None
    created: str

class AppTemplate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    icon: Optional[str] = None
    category: str
    docker_image: str
    docker_compose: Optional[Dict[str, Any]] = None
    github_repo: Optional[str] = None
    ports: Optional[List[int]] = None
    environment: Optional[Dict[str, str]] = None
    volumes: Optional[List[str]] = None
    official: bool = True

class StoragePoolCreate(BaseModel):
    name: str
    mount_point: str
    pool_type: str  # local, remote, network

class StoragePool(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    mount_point: str
    pool_type: str  # local, remote, network
    total_space: int
    used_space: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SystemSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ddns_enabled: bool = False
    ddns_provider: Optional[str] = "noip"
    ddns_hostname: Optional[str] = None
    ddns_username: Optional[str] = None
    ddns_password: Optional[str] = None
    ssl_enabled: bool = False
    ssl_email: Optional[str] = None
    ssl_domains: Optional[List[str]] = None

# ============ AUTH HELPERS ============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============ SYSTEM MONITORING ============

def get_gpu_info():
    try:
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        if device_count == 0:
            return {"installed": False, "message": "No GPU detected"}
        
        gpu_data = []
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle)
            memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            
            gpu_data.append({
                "name": name,
                "memory_total": memory.total,
                "memory_used": memory.used,
                "memory_free": memory.free,
                "utilization": utilization.gpu
            })
        
        pynvml.nvmlShutdown()
        return {"installed": True, "gpus": gpu_data}
    except Exception as e:
        return {"installed": False, "message": str(e)}

# ============ AUTH ROUTES ============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing_user = await db.users.find_one({"username": user_data.username}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_pw = hash_password(user_data.password)
    user = User(username=user_data.username, email=user_data.email)
    
    user_dict = user.model_dump()
    user_dict['password'] = hashed_pw
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    token = create_token(user.id)
    return TokenResponse(access_token=token, user=user)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"username": credentials.username}, {"_id": 0})
    if not user or not verify_password(credentials.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user['id'])
    user_obj = User(**{k: v for k, v in user.items() if k != 'password'})
    return TokenResponse(access_token=token, user=user_obj)

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: Dict = Depends(get_current_user)):
    return User(**current_user)

@api_router.post("/auth/mark-onboarded")
async def mark_onboarded(current_user: Dict = Depends(get_current_user)):
    await db.users.update_one({"id": current_user['id']}, {"$set": {"first_login": False}})
    return {"success": True}

# ============ SYSTEM ROUTES ============

@api_router.get("/system/metrics", response_model=SystemMetrics)
async def get_system_metrics(current_user: Dict = Depends(get_current_user)):
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    
    ram = psutil.virtual_memory()
    
    disk = psutil.disk_usage('/')
    
    gpu_info = get_gpu_info()
    
    return SystemMetrics(
        cpu_percent=cpu_percent,
        cpu_count=cpu_count,
        ram_total=ram.total,
        ram_used=ram.used,
        ram_percent=ram.percent,
        storage_total=disk.total,
        storage_used=disk.used,
        storage_percent=disk.percent,
        gpu_info=gpu_info
    )

# ============ DOCKER/CONTAINER ROUTES ============

@api_router.get("/containers/list", response_model=List[DockerContainer])
async def list_containers(current_user: Dict = Depends(get_current_user)):
    if not docker_client:
        return []
    
    containers = docker_client.containers.list(all=True)
    result = []
    for container in containers:
        result.append(DockerContainer(
            id=container.id[:12],
            name=container.name,
            image=container.image.tags[0] if container.image.tags else "unknown",
            status=container.status,
            ports=container.ports,
            created=container.attrs['Created']
        ))
    return result

@api_router.post("/containers/{container_id}/start")
async def start_container(container_id: str, current_user: Dict = Depends(get_current_user)):
    if not docker_client:
        raise HTTPException(status_code=503, detail="Docker not available")
    
    try:
        container = docker_client.containers.get(container_id)
        container.start()
        return {"success": True, "message": "Container started"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/containers/{container_id}/stop")
async def stop_container(container_id: str, current_user: Dict = Depends(get_current_user)):
    if not docker_client:
        raise HTTPException(status_code=503, detail="Docker not available")
    
    try:
        container = docker_client.containers.get(container_id)
        container.stop()
        return {"success": True, "message": "Container stopped"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.delete("/containers/{container_id}")
async def remove_container(container_id: str, current_user: Dict = Depends(get_current_user)):
    if not docker_client:
        raise HTTPException(status_code=503, detail="Docker not available")
    
    try:
        container = docker_client.containers.get(container_id)
        container.remove(force=True)
        return {"success": True, "message": "Container removed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============ APP TEMPLATE ROUTES ============

@api_router.get("/apps/templates", response_model=List[AppTemplate])
async def get_app_templates(current_user: Dict = Depends(get_current_user)):
    templates = await db.app_templates.find({}, {"_id": 0}).to_list(1000)
    return templates

@api_router.post("/apps/templates", response_model=AppTemplate)
async def create_app_template(template: AppTemplate, current_user: Dict = Depends(get_current_user)):
    template_dict = template.model_dump()
    await db.app_templates.insert_one(template_dict)
    return template

@api_router.post("/apps/install/{template_id}")
async def install_app(template_id: str, current_user: Dict = Depends(get_current_user)):
    if not docker_client:
        raise HTTPException(status_code=503, detail="Docker not available")
    
    template = await db.app_templates.find_one({"id": template_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        # Pull the image
        docker_client.images.pull(template['docker_image'])
        
        # Create container
        container = docker_client.containers.run(
            template['docker_image'],
            name=f"{template['name'].lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}",
            detach=True,
            environment=template.get('environment', {}),
            ports=template.get('ports', {}),
            volumes=template.get('volumes', [])
        )
        
        return {"success": True, "container_id": container.id, "message": f"{template['name']} installed successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============ STORAGE ROUTES ============

@api_router.get("/storage/pools", response_model=List[StoragePool])
async def get_storage_pools(current_user: Dict = Depends(get_current_user)):
    pools = await db.storage_pools.find({}, {"_id": 0}).to_list(1000)
    return pools

@api_router.post("/storage/pools", response_model=StoragePool)
async def add_storage_pool(pool_input: StoragePoolCreate, current_user: Dict = Depends(get_current_user)):
    # Check if mount point exists
    if not os.path.exists(pool_input.mount_point):
        raise HTTPException(status_code=400, detail="Mount point does not exist")
    
    # Get disk usage
    try:
        usage = shutil.disk_usage(pool_input.mount_point)
        pool = StoragePool(
            name=pool_input.name,
            mount_point=pool_input.mount_point,
            pool_type=pool_input.pool_type,
            total_space=usage.total,
            used_space=usage.used
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot access mount point: {str(e)}")
    
    pool_dict = pool.model_dump()
    pool_dict['created_at'] = pool_dict['created_at'].isoformat()
    await db.storage_pools.insert_one(pool_dict)
    return pool

@api_router.delete("/storage/pools/{pool_id}")
async def remove_storage_pool(pool_id: str, current_user: Dict = Depends(get_current_user)):
    result = await db.storage_pools.delete_one({"id": pool_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Storage pool not found")
    return {"success": True}

# ============ SETTINGS ROUTES ============

@api_router.get("/settings", response_model=SystemSettings)
async def get_settings(current_user: Dict = Depends(get_current_user)):
    settings = await db.system_settings.find_one({}, {"_id": 0})
    if not settings:
        # Create default settings
        default_settings = SystemSettings()
        await db.system_settings.insert_one(default_settings.model_dump())
        return default_settings
    return SystemSettings(**settings)

@api_router.put("/settings")
async def update_settings(settings: SystemSettings, current_user: Dict = Depends(get_current_user)):
    await db.system_settings.update_one(
        {},
        {"$set": settings.model_dump()},
        upsert=True
    )
    return {"success": True}

# ============ SEED DATA ============

@api_router.post("/seed-apps")
async def seed_app_templates():
    # Check if already seeded
    count = await db.app_templates.count_documents({})
    if count > 0:
        return {"message": "Apps already seeded"}
    
    templates = [
        {
            "id": str(uuid.uuid4()),
            "name": "Jellyfin",
            "description": "Free Software Media System",
            "category": "Media Server",
            "docker_image": "jellyfin/jellyfin:latest",
            "github_repo": "https://github.com/jellyfin/jellyfin",
            "ports": [8096],
            "official": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Jellyseerr",
            "description": "Request management and media discovery tool",
            "category": "Media Management",
            "docker_image": "fallenbagel/jellyseerr:latest",
            "github_repo": "https://github.com/Fallenbagel/jellyseerr",
            "ports": [5055],
            "official": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Transmission",
            "description": "Fast, easy, and free BitTorrent client",
            "category": "Download",
            "docker_image": "linuxserver/transmission:latest",
            "github_repo": "https://github.com/transmission/transmission",
            "ports": [9091],
            "official": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Sonarr",
            "description": "Smart PVR for newsgroup and bittorrent users",
            "category": "Media Management",
            "docker_image": "linuxserver/sonarr:latest",
            "github_repo": "https://github.com/Sonarr/Sonarr",
            "ports": [8989],
            "official": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Radarr",
            "description": "Movie collection manager for Usenet and BitTorrent users",
            "category": "Media Management",
            "docker_image": "linuxserver/radarr:latest",
            "github_repo": "https://github.com/Radarr/Radarr",
            "ports": [7878],
            "official": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Plex",
            "description": "Stream Movies & TV Shows",
            "category": "Media Server",
            "docker_image": "plexinc/pms-docker:latest",
            "github_repo": "https://github.com/plexinc/pms-docker",
            "ports": [32400],
            "official": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Portainer",
            "description": "Container management platform",
            "category": "Management",
            "docker_image": "portainer/portainer-ce:latest",
            "github_repo": "https://github.com/portainer/portainer",
            "ports": [9000],
            "official": True
        }
    ]
    
    await db.app_templates.insert_many(templates)
    return {"message": f"Seeded {len(templates)} app templates"}

app.include_router(api_router)

# Include advanced features router
try:
    from server_advanced import advanced_router
    app.include_router(advanced_router)
except ImportError:
    pass

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()