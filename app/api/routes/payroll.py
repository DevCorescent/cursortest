from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession, require_roles
from app.core.rbac import Role
from app.models import Employee, PayrollRecord
from app.schemas import PayrollCreate, PayrollRead
from app.services import calculate_net_salary, write_audit_log

router = APIRouter()


@router.post(
    "",
    response_model=PayrollRead,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.HR))],
)
def create_payroll(payload: PayrollCreate, db: DBSession, current_user: CurrentUser):
    employee = db.get(Employee, payload.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    payroll = PayrollRecord(
        **payload.model_dump(),
        net_salary=calculate_net_salary(payload.basic_salary, payload.allowances, payload.deductions),
        created_by=current_user.id,
    )
    db.add(payroll)
    db.flush()
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="create_payroll",
        entity="payroll_record",
        entity_id=payroll.id,
        metadata={"employee_id": payload.employee_id},
    )
    db.commit()
    db.refresh(payroll)
    return payroll


@router.get("", response_model=list[PayrollRead])
def list_payroll(
    db: DBSession,
    current_user: CurrentUser,
    employee_id: int | None = None,
):
    stmt = select(PayrollRecord).order_by(PayrollRecord.created_at.desc())
    if current_user.role == Role.EMPLOYEE:
        employee = db.scalar(select(Employee).where(Employee.user_id == current_user.id))
        if not employee:
            raise HTTPException(status_code=404, detail="Employee profile not found")
        stmt = stmt.where(PayrollRecord.employee_id == employee.id)
    elif employee_id:
        stmt = stmt.where(PayrollRecord.employee_id == employee_id)

    return list(db.scalars(stmt).all())
