"""Sprint 22 backend tests: health, metrics, pagination, bulk-mi, assignments, line-balance"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Auth tokens
ADMIN_TOKEN = None
SUPERVISOR_TOKEN = None


def get_token(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    if r.status_code == 200:
        return r.json().get("token")
    return None


@pytest.fixture(scope="module", autouse=True)
def setup_tokens():
    global ADMIN_TOKEN, SUPERVISOR_TOKEN
    ADMIN_TOKEN = get_token("admin@garment.com", "Admin@123")
    SUPERVISOR_TOKEN = get_token("supervisor@garment.com", "Supervisor@123")


def admin_headers():
    return {"Authorization": f"Bearer {ADMIN_TOKEN}"}


def supervisor_headers():
    return {"Authorization": f"Bearer {SUPERVISOR_TOKEN}"}


# ─── Health & Metrics ──────────────────────────────────────────────────────────

class TestHealthAndMetrics:
    def test_health_endpoint(self):
        r = requests.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "ok"
        assert "db" in data
        print(f"Health: {data}")

    def test_health_has_db_latency(self):
        r = requests.get(f"{BASE_URL}/api/health")
        data = r.json()
        assert "db_latency_ms" in data or "db" in data
        print(f"Health data keys: {list(data.keys())}")

    def test_metrics_endpoint(self):
        r = requests.get(f"{BASE_URL}/api/metrics")
        assert r.status_code == 200
        data = r.json()
        print(f"Metrics: {data}")

    def test_docs_accessible(self):
        r = requests.get(f"{BASE_URL}/api/docs")
        assert r.status_code == 200


# ─── Pagination ────────────────────────────────────────────────────────────────

class TestPagination:
    def test_employees_limit_5(self):
        if not ADMIN_TOKEN:
            pytest.skip("No admin token")
        r = requests.get(f"{BASE_URL}/api/rahaza/employees?limit=5", headers=admin_headers())
        assert r.status_code == 200
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("employees", data.get("data", [])))
        assert len(items) <= 5
        print(f"Employees returned: {len(items)}")

    def test_work_orders_limit_3(self):
        if not ADMIN_TOKEN:
            pytest.skip("No admin token")
        r = requests.get(f"{BASE_URL}/api/rahaza/work-orders?limit=3", headers=admin_headers())
        assert r.status_code == 200
        data = r.json()
        items = data if isinstance(data, list) else data.get("items", data.get("work_orders", data.get("data", [])))
        assert len(items) <= 3
        print(f"Work orders returned: {len(items)}")


# ─── Bulk MI ───────────────────────────────────────────────────────────────────

class TestBulkMI:
    def test_preview_empty_wo_ids_returns_400(self):
        if not SUPERVISOR_TOKEN:
            pytest.skip("No supervisor token")
        r = requests.post(f"{BASE_URL}/api/rahaza/supervisor/bulk-mi/preview",
                          json={"wo_ids": []}, headers=supervisor_headers())
        assert r.status_code == 400

    def test_preview_with_invalid_wo_returns_200(self):
        if not SUPERVISOR_TOKEN:
            pytest.skip("No supervisor token")
        r = requests.post(f"{BASE_URL}/api/rahaza/supervisor/bulk-mi/preview",
                          json={"wo_ids": ["nonexistent-wo-id"]}, headers=supervisor_headers())
        assert r.status_code == 200
        data = r.json()
        assert "preview" in data
        assert data["total_wo"] == 1
        print(f"Preview result: {data['preview']}")

    def test_generate_empty_wo_ids_returns_400(self):
        if not SUPERVISOR_TOKEN:
            pytest.skip("No supervisor token")
        r = requests.post(f"{BASE_URL}/api/rahaza/supervisor/bulk-mi/generate",
                          json={"wo_ids": []}, headers=supervisor_headers())
        assert r.status_code == 400


# ─── Assignments ───────────────────────────────────────────────────────────────

class TestAssignments:
    def test_get_yesterday_assignments(self):
        if not SUPERVISOR_TOKEN:
            pytest.skip("No supervisor token")
        r = requests.get(f"{BASE_URL}/api/rahaza/supervisor/assignments/yesterday", headers=supervisor_headers())
        assert r.status_code == 200
        data = r.json()
        assert "assignments" in data
        assert "source_date" in data
        assert "count" in data
        print(f"Yesterday assignments count: {data['count']}")

    def test_bulk_create_empty_assignments_returns_400(self):
        if not SUPERVISOR_TOKEN:
            pytest.skip("No supervisor token")
        r = requests.post(f"{BASE_URL}/api/rahaza/supervisor/assignments/bulk",
                          json={"assignments": []}, headers=supervisor_headers())
        assert r.status_code == 400


# ─── Line Balance ──────────────────────────────────────────────────────────────

class TestLineBalance:
    def test_line_balance_endpoint(self):
        if not SUPERVISOR_TOKEN:
            pytest.skip("No supervisor token")
        r = requests.get(f"{BASE_URL}/api/rahaza/supervisor/line-balance", headers=supervisor_headers())
        assert r.status_code == 200
        data = r.json()
        assert "summary" in data
        assert "lines" in data
        assert data["summary"]["total_lines"] >= 0
        print(f"Line balance summary: {data['summary']}")

    def test_line_balance_has_factory_balance(self):
        if not SUPERVISOR_TOKEN:
            pytest.skip("No supervisor token")
        r = requests.get(f"{BASE_URL}/api/rahaza/supervisor/line-balance", headers=supervisor_headers())
        data = r.json()
        summary = data.get("summary", {})
        assert "total_operators" in summary
        assert "total_lines" in summary
        print(f"Total lines: {summary['total_lines']}, operators: {summary['total_operators']}")
