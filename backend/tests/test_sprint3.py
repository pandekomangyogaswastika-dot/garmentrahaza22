"""Sprint 3 backend tests: HR Reports, Payroll Attendance Validation, Low Stock Materials"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

@pytest.fixture(scope="module")
def admin_token():
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@garment.com",
        "password": "Admin@123"
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["token"]

@pytest.fixture(scope="module")
def hr_token():
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "hr@garment.com",
        "password": "Hr@123"
    })
    if resp.status_code == 200:
        return resp.json()["token"]
    pytest.skip("HR login failed")

@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture(scope="module")
def hr_headers(hr_token):
    return {"Authorization": f"Bearer {hr_token}"}


# ── Auth ──────────────────────────────────────────────────────────────────────

class TestAuth:
    """Authentication tests"""

    def test_admin_login(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@garment.com", "password": "Admin@123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["user"]["role"] in ("super_admin", "superadmin")

    def test_hr_login(self):
        """hr@garment.com may not be seeded — skip if absent"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "hr@garment.com", "password": "Hr@123"
        })
        if resp.status_code == 401:
            pytest.skip("hr@garment.com not seeded in this environment")
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data


# ── HR Reports ────────────────────────────────────────────────────────────────

class TestHRReports:
    """HR Reports endpoint tests"""

    def test_attendance_report(self, admin_headers):
        resp = requests.get(
            f"{BASE_URL}/api/rahaza/hr/reports/attendance-summary",
            params={"period_from": "2025-01-01", "period_to": "2025-01-31"},
            headers=admin_headers
        )
        assert resp.status_code == 200

    def test_overtime_report(self, admin_headers):
        resp = requests.get(
            f"{BASE_URL}/api/rahaza/hr/reports/overtime-summary",
            params={"period_from": "2025-01-01", "period_to": "2025-01-31"},
            headers=admin_headers
        )
        assert resp.status_code == 200

    def test_payroll_report(self, admin_headers):
        resp = requests.get(
            f"{BASE_URL}/api/rahaza/hr/reports/payroll-summary",
            params={"period_from": "2025-01-01", "period_to": "2025-01-31"},
            headers=admin_headers
        )
        assert resp.status_code == 200

    def test_turnover_report(self, admin_headers):
        resp = requests.get(
            f"{BASE_URL}/api/rahaza/hr/reports/turnover",
            params={"year": "2025"},
            headers=admin_headers
        )
        assert resp.status_code == 200


# ── Attendance Validation (Sprint 3.3) ────────────────────────────────────────

class TestAttendanceValidation:
    """Sprint 3.3: Attendance validation for payroll"""

    def test_attendance_validation_returns_200(self, admin_headers):
        resp = requests.get(
            f"{BASE_URL}/api/rahaza/hr/reports/attendance-validation",
            params={"period_from": "2025-01-01", "period_to": "2025-01-31"},
            headers=admin_headers
        )
        assert resp.status_code == 200

    def test_attendance_validation_response_structure(self, admin_headers):
        resp = requests.get(
            f"{BASE_URL}/api/rahaza/hr/reports/attendance-validation",
            params={"period_from": "2025-01-01", "period_to": "2025-01-31"},
            headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "warnings" in data
        assert "summary" in data
        assert isinstance(data["warnings"], list)
        assert "total_employees" in data["summary"]
        assert "total_warnings" in data["summary"]

    def test_attendance_validation_bad_date(self, admin_headers):
        resp = requests.get(
            f"{BASE_URL}/api/rahaza/hr/reports/attendance-validation",
            params={"period_from": "bad-date", "period_to": "2025-01-31"},
            headers=admin_headers
        )
        assert resp.status_code == 400

    def test_attendance_validation_hr_user(self, hr_headers):
        resp = requests.get(
            f"{BASE_URL}/api/rahaza/hr/reports/attendance-validation",
            params={"period_from": "2025-01-01", "period_to": "2025-01-31"},
            headers=hr_headers
        )
        assert resp.status_code == 200


# ── Materials / Low Stock (Sprint 3.4) ───────────────────────────────────────

class TestMaterials:
    """Sprint 3.4: Materials list with low_stock filter and search"""

    def test_list_materials(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/rahaza/materials", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (list, dict))

    def test_search_materials_yarn(self, admin_headers):
        resp = requests.get(
            f"{BASE_URL}/api/rahaza/materials",
            params={"search": "YRN"},
            headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        # Accept list or dict with items key
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        print(f"Search YRN returned {len(items)} items")

    def test_low_stock_filter(self, admin_headers):
        resp = requests.get(
            f"{BASE_URL}/api/rahaza/materials",
            params={"low_stock": "true"},
            headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"Low stock filter response: {str(data)[:200]}")

    def test_materials_search_and_lowstock_combined(self, admin_headers):
        resp = requests.get(
            f"{BASE_URL}/api/rahaza/materials",
            params={"search": "YRN", "low_stock": "true"},
            headers=admin_headers
        )
        assert resp.status_code == 200


# ── Payroll Runs ──────────────────────────────────────────────────────────────

class TestPayrollRuns:
    """Payroll run list endpoint"""

    def test_list_payroll_runs(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/rahaza/payroll-runs", headers=admin_headers)
        assert resp.status_code == 200
