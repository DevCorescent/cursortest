from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession, require_roles
from app.core.rbac import Role
from app.models import Department
from app.schemas import DepartmentCreate, DepartmentRead, MessageResponse
from app.services import write_audit_log

router = APIRouter()


@router.post(
    "",
    response_model=DepartmentRead,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.HR))],
)
def create_department(payload: DepartmentCreate, db: DBSession, current_user: CurrentUser):
    existing = db.scalar(select(Department).where(Department.name == payload.name))
    if existing:
        raise HTTPException(status_code=409, detail="Department already exists")
    department = Department(name=payload.name, description=payload.description)
    db.add(department)
    db.flush()
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="create_department",
        entity="department",
        entity_id=department.id,
        metadata={"name": department.name},
    )
    db.commit()
    db.refresh(department)
    return department


@router.get("", response_model=list[DepartmentRead])
def list_departments(db: DBSession):
    return list(db.scalars(select(Department).order_by(Department.name)).all())


@router.delete(
    "/{department_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.HR))],
)
def delete_department(department_id: int, db: DBSession, current_user: CurrentUser):
    department = db.get(Department, department_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    db.delete(department)
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="delete_department",
        entity="department",
        entity_id=department_id,
    )
    db.commit()
    return MessageResponse(message="Department deleted")
