from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.rbac import (
    ApplicationStatus,
    AttendanceStatus,
    EmploymentType,
    LeaveStatus,
    Role,
)


class MessageResponse(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: Role
    is_active: bool
    created_at: datetime


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None


class DepartmentRead(DepartmentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class EmployeeCreate(BaseModel):
    user_id: int
    employee_code: str = Field(min_length=2, max_length=40)
    first_name: str
    last_name: str
    phone: str | None = None
    address: str | None = None
    job_title: str
    department_id: int | None = None
    manager_id: int | None = None
    date_joined: date
    salary: Decimal = Field(default=Decimal("0.00"), ge=0)
    employment_type: EmploymentType = EmploymentType.FULL_TIME


class EmployeeUpdate(BaseModel):
    phone: str | None = None
    address: str | None = None
    job_title: str | None = None
    department_id: int | None = None
    manager_id: int | None = None
    salary: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    employee_code: str
    first_name: str
    last_name: str
    phone: str | None
    address: str | None
    job_title: str
    department_id: int | None
    manager_id: int | None
    date_joined: date
    salary: Decimal
    employment_type: EmploymentType
    is_active: bool
    created_at: datetime


class AttendanceCreate(BaseModel):
    employee_id: int
    attendance_date: date
    check_in: datetime | None = None
    check_out: datetime | None = None
    status: AttendanceStatus = AttendanceStatus.PRESENT
    notes: str | None = None


class AttendanceClock(BaseModel):
    employee_id: int
    attendance_date: date
    notes: str | None = None


class AttendanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    attendance_date: date
    check_in: datetime | None
    check_out: datetime | None
    status: AttendanceStatus
    notes: str | None
    created_at: datetime


class LeaveRequestCreate(BaseModel):
    employee_id: int
    start_date: date
    end_date: date
    leave_type: str = Field(min_length=2, max_length=60)
    reason: str | None = None


class LeaveReview(BaseModel):
    status: LeaveStatus


class LeaveRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    start_date: date
    end_date: date
    leave_type: str
    reason: str | None
    status: LeaveStatus
    reviewed_by_user_id: int | None
    reviewed_at: datetime | None
    created_at: datetime


class PayrollCreate(BaseModel):
    employee_id: int
    period_start: date
    period_end: date
    basic_salary: Decimal = Field(default=Decimal("0.00"), ge=0)
    allowances: Decimal = Field(default=Decimal("0.00"), ge=0)
    deductions: Decimal = Field(default=Decimal("0.00"), ge=0)
    payment_date: date | None = None
    status: str = "draft"


class PayrollRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    period_start: date
    period_end: date
    basic_salary: Decimal
    allowances: Decimal
    deductions: Decimal
    net_salary: Decimal
    payment_date: date | None
    status: str
    created_at: datetime


class JobOpeningCreate(BaseModel):
    title: str
    department_id: int | None = None
    description: str
    location: str
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    is_open: bool = True


class JobOpeningRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    department_id: int | None
    description: str
    location: str
    employment_type: EmploymentType
    is_open: bool
    created_by: int
    created_at: datetime


class CandidateApplicationCreate(BaseModel):
    job_opening_id: int
    candidate_name: str
    email: EmailStr
    phone: str | None = None
    resume_url: str | None = None
    notes: str | None = None


class CandidateApplicationUpdate(BaseModel):
    status: ApplicationStatus
    notes: str | None = None


class CandidateApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_opening_id: int
    candidate_name: str
    email: EmailStr
    phone: str | None
    resume_url: str | None
    status: ApplicationStatus
    notes: str | None
    reviewed_by: int | None
    created_at: datetime


class PerformanceReviewCreate(BaseModel):
    employee_id: int
    review_period: str
    score: Decimal = Field(ge=0, le=5)
    strengths: str | None = None
    improvement_areas: str | None = None
    goals: str | None = None


class PerformanceReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    reviewer_id: int
    review_period: str
    score: Decimal
    strengths: str | None
    improvement_areas: str | None
    goals: str | None
    created_at: datetime


class DashboardStats(BaseModel):
    total_users: int
    total_employees: int
    active_employees: int
    open_positions: int
    pending_leave_requests: int
