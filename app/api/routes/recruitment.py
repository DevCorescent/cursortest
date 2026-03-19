from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession, require_roles
from app.core.rbac import Role
from app.models import CandidateApplication, JobOpening
from app.schemas import (
    CandidateApplicationCreate,
    CandidateApplicationRead,
    CandidateApplicationUpdate,
    JobOpeningCreate,
    JobOpeningRead,
)
from app.services import write_audit_log

router = APIRouter()


@router.post(
    "/jobs",
    response_model=JobOpeningRead,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.HR))],
)
def create_job(payload: JobOpeningCreate, db: DBSession, current_user: CurrentUser):
    job = JobOpening(**payload.model_dump(), created_by=current_user.id)
    db.add(job)
    db.flush()
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="create_job_opening",
        entity="job_opening",
        entity_id=job.id,
    )
    db.commit()
    db.refresh(job)
    return job


@router.get("/jobs", response_model=list[JobOpeningRead])
def list_jobs(db: DBSession, is_open: bool | None = None):
    stmt = select(JobOpening).order_by(JobOpening.created_at.desc())
    if is_open is not None:
        stmt = stmt.where(JobOpening.is_open == is_open)
    return list(db.scalars(stmt).all())


@router.post("/applications", response_model=CandidateApplicationRead)
def create_application(payload: CandidateApplicationCreate, db: DBSession):
    job = db.get(JobOpening, payload.job_opening_id)
    if not job or not job.is_open:
        raise HTTPException(status_code=404, detail="Open job opening not found")
    application = CandidateApplication(**payload.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get(
    "/applications",
    response_model=list[CandidateApplicationRead],
    dependencies=[Depends(require_roles(Role.ADMIN, Role.HR, Role.MANAGER))],
)
def list_applications(db: DBSession):
    return list(db.scalars(select(CandidateApplication).order_by(CandidateApplication.created_at.desc())).all())


@router.patch(
    "/applications/{application_id}",
    response_model=CandidateApplicationRead,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.HR))],
)
def update_application(
    application_id: int,
    payload: CandidateApplicationUpdate,
    db: DBSession,
    current_user: CurrentUser,
):
    application = db.get(CandidateApplication, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    application.status = payload.status
    application.notes = payload.notes
    application.reviewed_by = current_user.id
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="update_application_status",
        entity="candidate_application",
        entity_id=application.id,
        metadata={"status": payload.status.value},
    )
    db.commit()
    db.refresh(application)
    return application
