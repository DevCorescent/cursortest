from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.core.rbac import EmploymentType, Role
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Department, Employee, JobOpening, User


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.email == "admin@company.com"))
        if not admin:
            admin = User(
                email="admin@company.com",
                hashed_password=hash_password("Admin@123"),
                role=Role.ADMIN,
                is_active=True,
            )
            db.add(admin)
            db.flush()

        hr = db.scalar(select(User).where(User.email == "hr@company.com"))
        if not hr:
            hr = User(
                email="hr@company.com",
                hashed_password=hash_password("HrPass@123"),
                role=Role.HR,
                is_active=True,
            )
            db.add(hr)
            db.flush()

        eng = db.scalar(select(Department).where(Department.name == "Engineering"))
        if not eng:
            eng = Department(name="Engineering", description="Product engineering function")
            db.add(eng)
            db.flush()

        manager_user = db.scalar(select(User).where(User.email == "manager@company.com"))
        if not manager_user:
            manager_user = User(
                email="manager@company.com",
                hashed_password=hash_password("Manager@123"),
                role=Role.MANAGER,
            )
            db.add(manager_user)
            db.flush()

        manager_emp = db.scalar(select(Employee).where(Employee.user_id == manager_user.id))
        if not manager_emp:
            manager_emp = Employee(
                user_id=manager_user.id,
                employee_code="MGR-001",
                first_name="Ava",
                last_name="Sharma",
                phone="+1555123456",
                job_title="Engineering Manager",
                department_id=eng.id,
                date_joined=date.today(),
                salary=Decimal("150000"),
                employment_type=EmploymentType.FULL_TIME,
            )
            db.add(manager_emp)
            db.flush()

        employee_user = db.scalar(select(User).where(User.email == "employee@company.com"))
        if not employee_user:
            employee_user = User(
                email="employee@company.com",
                hashed_password=hash_password("Employee@123"),
                role=Role.EMPLOYEE,
            )
            db.add(employee_user)
            db.flush()

        employee = db.scalar(select(Employee).where(Employee.user_id == employee_user.id))
        if not employee:
            employee = Employee(
                user_id=employee_user.id,
                employee_code="EMP-001",
                first_name="Rohan",
                last_name="Mehta",
                phone="+1555765432",
                job_title="Software Engineer",
                department_id=eng.id,
                manager_id=manager_emp.id,
                date_joined=date.today(),
                salary=Decimal("90000"),
                employment_type=EmploymentType.FULL_TIME,
            )
            db.add(employee)

        opening = db.scalar(select(JobOpening).where(JobOpening.title == "Senior Backend Engineer"))
        if not opening:
            db.add(
                JobOpening(
                    title="Senior Backend Engineer",
                    department_id=eng.id,
                    description="Build distributed services for global HRM platform.",
                    location="Bengaluru",
                    employment_type=EmploymentType.FULL_TIME,
                    is_open=True,
                    created_by=admin.id,
                )
            )

        db.commit()
        print("Seed data inserted successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
