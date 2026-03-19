from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession, require_roles
from app.core.rbac import Role
from app.models import Employee, PerformanceReview
from app.schemas import PerformanceReviewCreate, PerformanceReviewRead
from app.services import write_audit_log

router = APIRouter()


@router.post(
    "",
    response_model=PerformanceReviewRead,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.HR, Role.MANAGER))],
)
def create_performance_review(payload: PerformanceReviewCreate, db: DBSession, current_user: CurrentUser):
    employee = db.get(Employee, payload.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if current_user.role == Role.MANAGER:
        manager = db.scalar(select(Employee).where(Employee.user_id == current_user.id))
        if not manager or employee.manager_id != manager.id:
            raise HTTPException(status_code=403, detail="Managers can review only direct reports")

    review = PerformanceReview(**payload.model_dump(), reviewer_id=current_user.id)
    db.add(review)
    db.flush()
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="create_performance_review",
        entity="performance_review",
        entity_id=review.id,
        metadata={"employee_id": payload.employee_id, "score": str(payload.score)},
    )
    db.commit()
    db.refresh(review)
    return review


@router.get("", response_model=list[PerformanceReviewRead])
def list_reviews(db: DBSession, current_user: CurrentUser, employee_id: int | None = None):
    stmt = select(PerformanceReview).order_by(PerformanceReview.created_at.desc())
    if current_user.role == Role.EMPLOYEE:
        employee = db.scalar(select(Employee).where(Employee.user_id == current_user.id))
        if not employee:
            raise HTTPException(status_code=404, detail="Employee profile not found")
        stmt = stmt.where(PerformanceReview.employee_id == employee.id)
    elif employee_id:
        stmt = stmt.where(PerformanceReview.employee_id == employee_id)

    return list(db.scalars(stmt).all())
