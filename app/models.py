from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.rbac import (
    ApplicationStatus,
    AttendanceStatus,
    EmploymentType,
    LeaveStatus,
    Role,
)
from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False, default=Role.EMPLOYEE)
    is_active: Mapped[bool] = mapped_column(default=True)

    employee_profile: Mapped["Employee | None"] = relationship(back_populates="user", uselist=False)


class Department(TimestampMixin, Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text())

    employees: Mapped[list["Employee"]] = relationship(back_populates="department")


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"
    __table_args__ = (UniqueConstraint("employee_code", name="uq_employee_employee_code"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    employee_code: Mapped[str] = mapped_column(String(40), index=True)
    first_name: Mapped[str] = mapped_column(String(120))
    last_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(Text())
    job_title: Mapped[str] = mapped_column(String(120))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), index=True)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), index=True)
    date_joined: Mapped[date] = mapped_column(default=date.today)
    salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType), default=EmploymentType.FULL_TIME
    )
    is_active: Mapped[bool] = mapped_column(default=True)

    user: Mapped[User] = relationship(back_populates="employee_profile")
    department: Mapped[Department | None] = relationship(back_populates="employees")
    manager: Mapped["Employee | None"] = relationship(remote_side="Employee.id")
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(back_populates="employee")
    leave_requests: Mapped[list["LeaveRequest"]] = relationship(back_populates="employee")
    payroll_records: Mapped[list["PayrollRecord"]] = relationship(back_populates="employee")
    performance_reviews: Mapped[list["PerformanceReview"]] = relationship(
        back_populates="employee", foreign_keys="PerformanceReview.employee_id"
    )


class AttendanceRecord(TimestampMixin, Base):
    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint("employee_id", "attendance_date", name="uq_employee_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), index=True)
    attendance_date: Mapped[date] = mapped_column(index=True)
    check_in: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    check_out: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[AttendanceStatus] = mapped_column(Enum(AttendanceStatus), default=AttendanceStatus.PRESENT)
    notes: Mapped[str | None] = mapped_column(Text())

    employee: Mapped[Employee] = relationship(back_populates="attendance_records")


class LeaveRequest(TimestampMixin, Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), index=True)
    start_date: Mapped[date]
    end_date: Mapped[date]
    leave_type: Mapped[str] = mapped_column(String(60))
    reason: Mapped[str | None] = mapped_column(Text())
    status: Mapped[LeaveStatus] = mapped_column(Enum(LeaveStatus), default=LeaveStatus.PENDING, index=True)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    employee: Mapped[Employee] = relationship(back_populates="leave_requests")


class PayrollRecord(TimestampMixin, Base):
    __tablename__ = "payroll_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), index=True)
    period_start: Mapped[date]
    period_end: Mapped[date]
    basic_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    allowances: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    deductions: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    net_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    payment_date: Mapped[date | None]
    status: Mapped[str] = mapped_column(String(40), default="draft", index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))

    employee: Mapped[Employee] = relationship(back_populates="payroll_records")


class JobOpening(TimestampMixin, Base):
    __tablename__ = "job_openings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(120))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), index=True)
    description: Mapped[str] = mapped_column(Text())
    location: Mapped[str] = mapped_column(String(120))
    employment_type: Mapped[EmploymentType] = mapped_column(Enum(EmploymentType), default=EmploymentType.FULL_TIME)
    is_open: Mapped[bool] = mapped_column(default=True, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))


class CandidateApplication(TimestampMixin, Base):
    __tablename__ = "candidate_applications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_opening_id: Mapped[int] = mapped_column(ForeignKey("job_openings.id"), index=True)
    candidate_name: Mapped[str] = mapped_column(String(120), index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(30))
    resume_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[ApplicationStatus] = mapped_column(Enum(ApplicationStatus), default=ApplicationStatus.APPLIED)
    notes: Mapped[str | None] = mapped_column(Text())
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))


class PerformanceReview(TimestampMixin, Base):
    __tablename__ = "performance_reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), index=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    review_period: Mapped[str] = mapped_column(String(60), index=True)
    score: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("0.00"))
    strengths: Mapped[str | None] = mapped_column(Text())
    improvement_areas: Mapped[str | None] = mapped_column(Text())
    goals: Mapped[str | None] = mapped_column(Text())

    employee: Mapped[Employee] = relationship(
        back_populates="performance_reviews",
        foreign_keys=[employee_id],
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity: Mapped[str] = mapped_column(String(80), index=True)
    entity_id: Mapped[int | None] = mapped_column(index=True)
    metadata_json: Mapped[str | None] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
