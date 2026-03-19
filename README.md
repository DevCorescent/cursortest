# MNC-Grade HRM Software (FastAPI)

Enterprise-ready Human Resource Management (HRM) backend platform with modular APIs, role-based access control, and core HR workflows.

## Highlights

- JWT authentication and secure password hashing
- Role-based access control (Admin, HR, Manager, Employee)
- Employee lifecycle management
- Department management
- Attendance tracking (clock in/out + manual records)
- Leave management with approval workflow
- Payroll processing with net salary calculation
- Recruitment module (job openings + candidate applications)
- Performance review module
- Dashboard metrics endpoint
- Audit logging for critical actions
- Test suite for authentication + leave approval flow

## Tech Stack

- **Python**
- **FastAPI**
- **SQLAlchemy (ORM)**
- **SQLite** (default, swappable via `DATABASE_URL`)
- **PyJWT**
- **Pytest**

## Project Structure

```text
app/
  api/
    deps.py
    router.py
    routes/
      auth.py
      departments.py
      employees.py
      attendance.py
      leaves.py
      payroll.py
      recruitment.py
      performance.py
      dashboards.py
  core/
    config.py
    rbac.py
    security.py
  db/
    base.py
    session.py
  main.py
  models.py
  schemas.py
  services.py
scripts/
  seed.py
tests/
  conftest.py
  test_auth_and_leave.py
```

## Quick Start

### 1) Create environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment

```bash
cp .env.example .env
```

Set secure values in `.env` for production, especially:

- `SECRET_KEY`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`

### 3) Run API server

```bash
uvicorn app.main:app --reload
```

The application creates the database schema and ensures an admin user exists at startup.

### 4) Seed sample data (optional)

```bash
python scripts/seed.py
```

## API Documentation

After starting the server:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health: `http://127.0.0.1:8000/health`

## Core API Flows

1. **Login**
   - `POST /api/v1/auth/login`
2. **Create users (admin/hr)**
   - `POST /api/v1/auth/users`
3. **Create employee profiles (admin/hr)**
   - `POST /api/v1/employees`
4. **Employees submit leave requests**
   - `POST /api/v1/leaves`
5. **Manager/HR/Admin approve or reject leave**
   - `PATCH /api/v1/leaves/{leave_id}/review`
6. **Create payroll entries (admin/hr)**
   - `POST /api/v1/payroll`
7. **Recruitment operations**
   - Jobs: `POST/GET /api/v1/recruitment/jobs`
   - Applications: `POST/GET/PATCH /api/v1/recruitment/applications`

## Running Tests

```bash
pytest -q
```

## Production Hardening Recommendations

For enterprise deployment, consider these additions:

- PostgreSQL + Alembic migrations
- Redis-backed task queues (notifications, payroll jobs)
- SSO integration (SAML/OIDC)
- Fine-grained policy engine for RBAC/ABAC
- Immutable audit trails + SIEM integration
- API rate limiting + WAF + zero-trust network policy
- Containerization and CI/CD pipelines with security scanning

## License

This project is provided as an implementation starter for enterprise HRM platforms.
