from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.api.deps import DBSession, require_roles
from app.core.rbac import LeaveStatus, Role
from app.models import Employee, JobOpening, LeaveRequest, User
from app.schemas import DashboardStats

router = APIRouter()


@router.get(
    "/stats",
    response_model=DashboardStats,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.HR, Role.MANAGER))],
)
def get_dashboard_stats(db: DBSession):
    return DashboardStats(
        total_users=db.scalar(select(func.count(User.id))) or 0,
        total_employees=db.scalar(select(func.count(Employee.id))) or 0,
        active_employees=db.scalar(select(func.count(Employee.id)).where(Employee.is_active.is_(True))) or 0,
        open_positions=db.scalar(select(func.count(JobOpening.id)).where(JobOpening.is_open.is_(True))) or 0,
        pending_leave_requests=(
            db.scalar(select(func.count(LeaveRequest.id)).where(LeaveRequest.status == LeaveStatus.PENDING)) or 0
        ),
    )
