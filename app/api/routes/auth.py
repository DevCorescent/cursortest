from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DBSession, require_roles
from app.core.config import get_settings
from app.core.rbac import Role
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas import MessageResponse, TokenResponse, UserCreate, UserLogin, UserRead
from app.services import write_audit_log

router = APIRouter()


@router.post("/bootstrap-admin", response_model=MessageResponse)
def bootstrap_admin(db: DBSession):
    existing = db.scalar(select(User.id).limit(1))
    if existing:
        raise HTTPException(status_code=400, detail="Users already exist. Bootstrap disabled.")

    settings = get_settings()
    admin = User(
        email=settings.admin_email,
        hashed_password=hash_password(settings.admin_password),
        role=Role.ADMIN,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    return MessageResponse(message="Admin user created successfully")


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: DBSession):
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

    token = create_access_token(subject=str(user.id), role=user.role.value)
    return TokenResponse(access_token=token)


@router.post(
    "/users",
    response_model=UserRead,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.HR))],
)
def create_user(payload: UserCreate, db: DBSession, current_user: CurrentUser):
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="create_user",
        entity="user",
        entity_id=user.id,
        metadata={"email": payload.email, "role": payload.role.value},
    )
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserRead)
def get_me(current_user: CurrentUser):
    return current_user
