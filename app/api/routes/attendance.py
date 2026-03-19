from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession, require_roles
from app.core.rbac import AttendanceStatus, Role
from app.models import AttendanceRecord, Employee
from app.schemas import AttendanceClock, AttendanceCreate, AttendanceRead, MessageResponse
from app.services import write_audit_log

router = APIRouter()


def _employee_for_user(db: DBSession, user_id: int) -> Employee | None:
    return db.scalar(select(Employee).where(Employee.user_id == user_id))


@router.post(
    "",
    response_model=AttendanceRead,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.HR, Role.MANAGER))],
)
def create_attendance(payload: AttendanceCreate, db: DBSession, current_user: CurrentUser):
    existing = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.employee_id == payload.employee_id,
            AttendanceRecord.attendance_date == payload.attendance_date,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Attendance already recorded for date")
    attendance = AttendanceRecord(**payload.model_dump())
    db.add(attendance)
    db.flush()
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="create_attendance",
        entity="attendance",
        entity_id=attendance.id,
        metadata={"employee_id": payload.employee_id},
    )
    db.commit()
    db.refresh(attendance)
    return attendance


@router.post("/clock-in", response_model=AttendanceRead)
def clock_in(payload: AttendanceClock, db: DBSession, current_user: CurrentUser):
    if current_user.role == Role.EMPLOYEE:
        employee = _employee_for_user(db, current_user.id)
        if not employee or employee.id != payload.employee_id:
            raise HTTPException(status_code=403, detail="Cannot clock in for other employees")

    record = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.employee_id == payload.employee_id,
            AttendanceRecord.attendance_date == payload.attendance_date,
        )
    )
    if record and record.check_in:
        raise HTTPException(status_code=409, detail="Already clocked in")
    if not record:
        record = AttendanceRecord(
            employee_id=payload.employee_id,
            attendance_date=payload.attendance_date,
            status=AttendanceStatus.PRESENT,
        )
        db.add(record)

    record.check_in = datetime.now(timezone.utc)
    record.notes = payload.notes
    db.commit()
    db.refresh(record)
    return record


@router.post("/clock-out", response_model=AttendanceRead)
def clock_out(payload: AttendanceClock, db: DBSession, current_user: CurrentUser):
    if current_user.role == Role.EMPLOYEE:
        employee = _employee_for_user(db, current_user.id)
        if not employee or employee.id != payload.employee_id:
            raise HTTPException(status_code=403, detail="Cannot clock out for other employees")

    record = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.employee_id == payload.employee_id,
            AttendanceRecord.attendance_date == payload.attendance_date,
        )
    )
    if not record or not record.check_in:
        raise HTTPException(status_code=404, detail="Clock in not found for this date")

    record.check_out = datetime.now(timezone.utc)
    if payload.notes:
        record.notes = payload.notes
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[AttendanceRead])
def list_attendance(
    db: DBSession,
    current_user: CurrentUser,
    employee_id: int | None = None,
):
    stmt = select(AttendanceRecord).order_by(AttendanceRecord.attendance_date.desc())
    if current_user.role == Role.EMPLOYEE:
        employee = _employee_for_user(db, current_user.id)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee profile not found")
        stmt = stmt.where(AttendanceRecord.employee_id == employee.id)
    elif employee_id:
        stmt = stmt.where(AttendanceRecord.employee_id == employee_id)

    return list(db.scalars(stmt).all())


@router.delete(
    "/{attendance_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.HR))],
)
def delete_attendance(attendance_id: int, db: DBSession, current_user: CurrentUser):
    attendance = db.get(AttendanceRecord, attendance_id)
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    db.delete(attendance)
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="delete_attendance",
        entity="attendance",
        entity_id=attendance_id,
    )
    db.commit()
    return MessageResponse(message="Attendance record deleted")
