from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select

from app.api.deps import CurrentUser, DBSession, require_roles
from app.core.rbac import Role
from app.models import Employee, User
from app.schemas import EmployeeCreate, EmployeeRead, EmployeeUpdate
from app.services import write_audit_log

router = APIRouter()


@router.post(
    "",
    response_model=EmployeeRead,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.HR))],
)
def create_employee(payload: EmployeeCreate, db: DBSession, current_user: CurrentUser):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if db.scalar(select(Employee).where(Employee.user_id == payload.user_id)):
        raise HTTPException(status_code=409, detail="Employee profile already exists for user")
    if db.scalar(select(Employee).where(Employee.employee_code == payload.employee_code)):
        raise HTTPException(status_code=409, detail="Employee code already exists")

    employee = Employee(**payload.model_dump())
    db.add(employee)
    db.flush()
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="create_employee",
        entity="employee",
        entity_id=employee.id,
        metadata={"employee_code": employee.employee_code},
    )
    db.commit()
    db.refresh(employee)
    return employee


@router.get("", response_model=list[EmployeeRead])
def list_employees(
    db: DBSession,
    current_user: CurrentUser,
    query: str | None = Query(default=None, description="Search by name/code/job title"),
    department_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
):
    if current_user.role not in {Role.ADMIN, Role.HR, Role.MANAGER}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    stmt = select(Employee)
    if query:
        like = f"%{query}%"
        stmt = stmt.where(
            or_(
                Employee.first_name.ilike(like),
                Employee.last_name.ilike(like),
                Employee.employee_code.ilike(like),
                Employee.job_title.ilike(like),
            )
        )
    if department_id:
        stmt = stmt.where(Employee.department_id == department_id)

    stmt = stmt.order_by(Employee.id).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee(employee_id: int, db: DBSession, current_user: CurrentUser):
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if current_user.role == Role.EMPLOYEE and employee.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot access other employees")
    return employee


@router.get("/self/profile", response_model=EmployeeRead)
def my_profile(db: DBSession, current_user: CurrentUser):
    employee = db.scalar(select(Employee).where(Employee.user_id == current_user.id))
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return employee


@router.patch(
    "/{employee_id}",
    response_model=EmployeeRead,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.HR, Role.MANAGER))],
)
def update_employee(employee_id: int, payload: EmployeeUpdate, db: DBSession, current_user: CurrentUser):
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(employee, field, value)

    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="update_employee",
        entity="employee",
        entity_id=employee.id,
        metadata={"updated_fields": list(updates.keys())},
    )
    db.commit()
    db.refresh(employee)
    return employee
