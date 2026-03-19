from datetime import date


def login(client, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_auth_rbac_and_leave_approval_flow(client):
    admin_token = login(client, "admin@company.com", "Admin@123")

    dep_resp = client.post(
        "/api/v1/departments",
        json={"name": "Engineering", "description": "Engineering org"},
        headers=auth_headers(admin_token),
    )
    assert dep_resp.status_code == 200, dep_resp.text
    department_id = dep_resp.json()["id"]

    manager_user_resp = client.post(
        "/api/v1/auth/users",
        json={"email": "manager@test.com", "password": "Manager@123", "role": "manager"},
        headers=auth_headers(admin_token),
    )
    assert manager_user_resp.status_code == 200, manager_user_resp.text
    manager_user_id = manager_user_resp.json()["id"]

    manager_emp_resp = client.post(
        "/api/v1/employees",
        json={
            "user_id": manager_user_id,
            "employee_code": "MGR-100",
            "first_name": "Manager",
            "last_name": "User",
            "job_title": "Engineering Manager",
            "department_id": department_id,
            "date_joined": str(date.today()),
            "salary": "150000.00",
            "employment_type": "full_time",
        },
        headers=auth_headers(admin_token),
    )
    assert manager_emp_resp.status_code == 200, manager_emp_resp.text
    manager_employee_id = manager_emp_resp.json()["id"]

    employee_user_resp = client.post(
        "/api/v1/auth/users",
        json={"email": "employee@test.com", "password": "Employee@123", "role": "employee"},
        headers=auth_headers(admin_token),
    )
    assert employee_user_resp.status_code == 200, employee_user_resp.text
    employee_user_id = employee_user_resp.json()["id"]

    employee_resp = client.post(
        "/api/v1/employees",
        json={
            "user_id": employee_user_id,
            "employee_code": "EMP-100",
            "first_name": "Employee",
            "last_name": "User",
            "job_title": "Software Engineer",
            "department_id": department_id,
            "manager_id": manager_employee_id,
            "date_joined": str(date.today()),
            "salary": "90000.00",
            "employment_type": "full_time",
        },
        headers=auth_headers(admin_token),
    )
    assert employee_resp.status_code == 200, employee_resp.text
    employee_id = employee_resp.json()["id"]

    employee_token = login(client, "employee@test.com", "Employee@123")
    leave_resp = client.post(
        "/api/v1/leaves",
        json={
            "employee_id": employee_id,
            "start_date": str(date.today()),
            "end_date": str(date.today()),
            "leave_type": "sick",
            "reason": "Flu symptoms",
        },
        headers=auth_headers(employee_token),
    )
    assert leave_resp.status_code == 200, leave_resp.text
    leave_id = leave_resp.json()["id"]
    assert leave_resp.json()["status"] == "pending"

    manager_token = login(client, "manager@test.com", "Manager@123")
    review_resp = client.patch(
        f"/api/v1/leaves/{leave_id}/review",
        json={"status": "approved"},
        headers=auth_headers(manager_token),
    )
    assert review_resp.status_code == 200, review_resp.text
    assert review_resp.json()["status"] == "approved"
