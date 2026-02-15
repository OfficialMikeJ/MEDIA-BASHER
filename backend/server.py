from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import docker
import psutil
import pynvml
import shutil
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# PostgreSQL connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://mediabasher:mediabasher123@localhost/media_basher')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    username = Column(String, primary_key=True, index=True)
    hashed_password = Column(String, nullable=False)
    email = Column(String, nullable=True)
    first_login = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AppTemplate(Base):
    __tablename__ = "app_templates"
    
    name = Column(String, primary_key=True, index=True)
    logo = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    repository = Column(String, nullable=True)

class StoragePool(Base):
    __tablename__ = "storage_pools"
    
    name = Column(String, primary_key=True, index=True)
    path = Column(String, nullable=False)
    size = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

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

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============ MODELS ============

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class StoragePoolCreate(BaseModel):
    name: str
    path: str

# ============ AUTH FUNCTIONS ============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(username: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": username,
        "exp": expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> str:
    username = verify_jwt_token(credentials.credentials)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return username

# ============ ROUTES ============

@api_router.post("/auth/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    new_user = User(
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        email=user_data.email,
        first_login=True
    )
    db.add(new_user)
    db.commit()
    
    token = create_jwt_token(user_data.username)
    return {"message": "User created successfully", "token": token}

@api_router.post("/auth/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(credentials.username)
    return {
        "token": token,
        "username": user.username,
        "first_login": user.first_login
    }

@api_router.get("/auth/me")
def get_me(username: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "username": user.username,
        "email": user.email,
        "first_login": user.first_login
    }
        "username": user.username,
        "email": user.email,
        "first_login": user.first_login
    }

@api_router.get("/system/metrics")
def get_system_metrics(username: str = Depends(get_current_user)):
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    gpu_info = None
    try:
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_name = pynvml.nvmlDeviceGetName(handle)
        gpu_mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        gpu_info = {
            "name": gpu_name,
            "memory_used": gpu_mem.used,
            "memory_total": gpu_mem.total
        }
    except:
        pass
    
    return {
        "cpu": cpu_percent,
        "memory": {
            "used": memory.used,
            "total": memory.total,
            "percent": memory.percent
        },
        "disk": {
            "used": disk.used,
            "total": disk.total,
            "percent": disk.percent
        },
        "gpu": gpu_info
    }

@api_router.get("/containers")
def get_containers(username: str = Depends(get_current_user)):
    if not docker_client:
        return []
    
    try:
        containers = docker_client.containers.list(all=True)
        return [{
            "id": c.id[:12],
            "name": c.name,
            "status": c.status,
            "image": c.image.tags[0] if c.image.tags else "unknown"
        } for c in containers]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/containers/list")
def get_containers_list(username: str = Depends(get_current_user)):
    if not docker_client:
        return []
    
    try:
        containers = docker_client.containers.list(all=True)
        return [{
            "id": c.id[:12],
            "name": c.name,
            "status": c.status,
            "image": c.image.tags[0] if c.image.tags else "unknown"
        } for c in containers]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/storage/pools")
def add_storage_pool(pool: StoragePoolCreate, username: str = Depends(get_current_user), db: Session = Depends(get_db)):
    # Validate path exists
    if not os.path.exists(pool.path):
        raise HTTPException(status_code=400, detail=f"Path '{pool.path}' does not exist")
    
    existing = db.query(StoragePool).filter(StoragePool.name == pool.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Storage pool already exists")
    
    try:
        disk_usage = shutil.disk_usage(pool.path)
        size = f"{disk_usage.total / (1024**3):.2f} GB"
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Unable to access path: {str(e)}")
    
    new_pool = StoragePool(
        name=pool.name,
        path=pool.path,
        size=size
    )
    db.add(new_pool)
    db.commit()
    
    return {"message": "Storage pool added", "name": pool.name, "size": size}

@api_router.get("/storage/pools")
def get_storage_pools(username: str = Depends(get_current_user), db: Session = Depends(get_db)):
    pools = db.query(StoragePool).all()
    return [{
        "name": p.name,
        "path": p.path,
        "size": p.size
    } for p in pools]

@api_router.get("/applications")
def get_applications(username: str = Depends(get_current_user), db: Session = Depends(get_db)):
    apps = db.query(AppTemplate).all()
    return [{
        "name": app.name,
        "logo": app.logo,
        "description": app.description,
        "repository": app.repository
    } for app in apps]

@api_router.post("/seed-apps")
def seed_apps(db: Session = Depends(get_db)):
    apps = [
        {"name": "Jellyfin", "logo": "🎬", "description": "Free Software Media System", "repository": "jellyfin/jellyfin"},
        {"name": "Jellyseerr", "logo": "🎭", "description": "Request management", "repository": "fallenbagel/jellyseerr"},
        {"name": "Transmission", "logo": "📥", "description": "BitTorrent client", "repository": "linuxserver/transmission"},
        {"name": "Sonarr", "logo": "📺", "description": "TV show management", "repository": "linuxserver/sonarr"},
        {"name": "Radarr", "logo": "🎥", "description": "Movie management", "repository": "linuxserver/radarr"},
        {"name": "Plex", "logo": "▶️", "description": "Media streaming", "repository": "plexinc/pms-docker"},
        {"name": "Portainer", "logo": "🐳", "description": "Container management", "repository": "portainer/portainer-ce"}
    ]
    
    for app_data in apps:
        existing = db.query(AppTemplate).filter(AppTemplate.name == app_data["name"]).first()
        if not existing:
            app = AppTemplate(**app_data)
            db.add(app)
    
    db.commit()
    return {"message": "Apps seeded successfully"}

# Import advanced routes
# from server_advanced import advanced_router
# api_router.include_router(advanced_router)

# Add routers
app.include_router(api_router)

# CORS - Must be added AFTER routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.get("/")
def root():
    return {"message": "Media Basher API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
