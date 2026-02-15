from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from datetime import datetime, timezone, timedelta
from typing import Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# JWT settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'media-basher-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"

security = HTTPBearer()

# PostgreSQL connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://mediabasher:mediabasher123@localhost/media_basher')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> str:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")
