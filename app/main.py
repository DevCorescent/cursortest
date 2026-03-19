from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.router import api_router
from app.core.config import get_settings
from app.core.rbac import Role
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import User


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)

    settings = get_settings()
    db = SessionLocal()
    try:
        admin_exists = db.scalar(select(User).where(User.role == Role.ADMIN))
        if not admin_exists:
            db.add(
                User(
                    email=settings.admin_email,
                    hashed_password=hash_password(settings.admin_password),
                    role=Role.ADMIN,
                    is_active=True,
                )
            )
            db.commit()
    finally:
        db.close()
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Enterprise-ready HRM backend for MNC-grade organizations.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}
