from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession, require_roles
from app.core.rbac import LeaveStatus, Role
from app.models import Employee, LeaveRequest
from app.schemas import LeaveRequestCreate, LeaveRequestRead, LeaveReview
from app.services import write_audit_log

router = APIRouter()


def _employee_for_user(db: DBSession, user_id: int) -> Employee | None:
    return db.scalar(select(Employee).where(Employee.user_id == user_id))


@router.post("", response_model=LeaveRequestRead)
def create_leave_request(payload: LeaveRequestCreate, db: DBSession, current_user: CurrentUser):
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="end_date cannot be earlier than start_date")

    if current_user.role == Role.EMPLOYEE:
        employee = _employee_for_user(db, current_user.id)
        if not employee or employee.id != payload.employee_id:
            raise HTTPException(status_code=403, detail="Cannot create leave for other employees")

    leave = LeaveRequest(**payload.model_dump(), status=LeaveStatus.PENDING)
    db.add(leave)
    db.flush()
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="create_leave_request",
        entity="leave_request",
        entity_id=leave.id,
        metadata={"employee_id": payload.employee_id},
    )
    db.commit()
    db.refresh(leave)
    return leave


@router.get("", response_model=list[LeaveRequestRead])
def list_leave_requests(db: DBSession, current_user: CurrentUser, status: LeaveStatus | None = None):
    stmt = select(LeaveRequest).order_by(LeaveRequest.created_at.desc())
    if status:
        stmt = stmt.where(LeaveRequest.status == status)

    if current_user.role == Role.EMPLOYEE:
        employee = _employee_for_user(db, current_user.id)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee profile not found")
        stmt = stmt.where(LeaveRequest.employee_id == employee.id)

    return list(db.scalars(stmt).all())


@router.patch(
    "/{leave_id}/review",
    response_model=LeaveRequestRead,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.HR, Role.MANAGER))],
)
def review_leave_request(leave_id: int, payload: LeaveReview, db: DBSession, current_user: CurrentUser):
    if payload.status not in {LeaveStatus.APPROVED, LeaveStatus.REJECTED}:
        raise HTTPException(status_code=400, detail="Only approved/rejected are valid review statuses")

    leave = db.get(LeaveRequest, leave_id)
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if leave.status != LeaveStatus.PENDING:
        raise HTTPException(status_code=409, detail="Leave already reviewed")

    employee = db.get(Employee, leave.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if current_user.role == Role.MANAGER:
        manager_profile = _employee_for_user(db, current_user.id)
        if not manager_profile or employee.manager_id != manager_profile.id:
            raise HTTPException(status_code=403, detail="Managers can review only direct reports")

    leave.status = payload.status
    leave.reviewed_by_user_id = current_user.id
    leave.reviewed_at = datetime.now(timezone.utc)
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="review_leave_request",
        entity="leave_request",
        entity_id=leave.id,
        metadata={"status": payload.status.value},
    )
    db.commit()
    db.refresh(leave)
    return leave
