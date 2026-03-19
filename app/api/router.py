from fastapi import APIRouter

from app.api.routes import attendance, auth, dashboards, departments, employees, leaves, payroll, performance, recruitment

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(departments.router, prefix="/departments", tags=["departments"])
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(leaves.router, prefix="/leaves", tags=["leaves"])
api_router.include_router(payroll.router, prefix="/payroll", tags=["payroll"])
api_router.include_router(recruitment.router, prefix="/recruitment", tags=["recruitment"])
api_router.include_router(performance.router, prefix="/performance", tags=["performance"])
api_router.include_router(dashboards.router, prefix="/dashboard", tags=["dashboard"])
