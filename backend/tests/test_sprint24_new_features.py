"""
Sprint 24: Test new features - Demo Seed, LKP Bulk Print, Shift Handover, Material Reservation, Production Calendar
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    def test_login_admin(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@garment.com", "password": "Admin@123"})
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        print(f"Login OK, token: {data['token'][:20]}...")

@pytest.fixture(scope="module")
def token():
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@garment.com", "password": "Admin@123"})
    assert resp.status_code == 200
    return resp.json()["token"]

@pytest.fixture(scope="module")
def auth(token):
    return {"Authorization": f"Bearer {token}"}

class TestDemoSeed:
    def test_materials_exist(self, auth):
        resp = requests.get(f"{BASE_URL}/api/rahaza/materials", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        assert len(items) > 0, f"No materials found: {data}"
        print(f"Materials count: {len(items)}")

    def test_work_orders_exist(self, auth):
        resp = requests.get(f"{BASE_URL}/api/rahaza/work-orders", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        assert len(items) > 0, f"No WOs found: {data}"
        print(f"WOs count: {len(items)}")

    def test_employees_exist(self, auth):
        resp = requests.get(f"{BASE_URL}/api/rahaza/employees", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        assert len(items) > 0, f"No employees found: {data}"
        print(f"Employees count: {len(items)}")

class TestLKPBulkToday:
    def test_lkp_bulk_today(self, auth):
        resp = requests.get(f"{BASE_URL}/api/rahaza/lkp-bulk-today", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got: {type(data)}"
        print(f"LKP bulk today items: {len(data)}")

class TestShiftHandover:
    def test_get_shift_handovers(self, auth):
        resp = requests.get(f"{BASE_URL}/api/rahaza/shift-handovers", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        print(f"Shift handovers: {data}")

    def test_create_shift_handover(self, auth):
        payload = {
            "shift": "Pagi",
            "tanggal": "2026-02-10",
            "line": "Line 1",
            "supervisor": "Test Supervisor",
            "checklist": {"mesin_ok": True, "bahan_ok": True},
            "issues": "Test issue",
            "pending_tasks": "Test pending"
        }
        resp = requests.post(f"{BASE_URL}/api/rahaza/shift-handovers", json=payload, headers=auth)
        assert resp.status_code in [200, 201], f"Status: {resp.status_code}, Body: {resp.text}"
        data = resp.json()
        print(f"Created handover: {data.get('id', data)}")

class TestMaterialReservation:
    def test_get_material_reservations(self, auth):
        resp = requests.get(f"{BASE_URL}/api/rahaza/material-reservations", headers=auth)
        assert resp.status_code == 200
        print(f"Reservations: {resp.json()}")

    def test_get_materials_for_reservation(self, auth):
        resp = requests.get(f"{BASE_URL}/api/rahaza/materials", headers=auth)
        assert resp.status_code == 200

class TestProductionCalendar:
    def test_get_calendar(self, auth):
        resp = requests.get(f"{BASE_URL}/api/rahaza/production-calendar", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        print(f"Calendar entries: {len(data) if isinstance(data, list) else data}")

    def test_seed_national_holidays(self, auth):
        resp = requests.post(f"{BASE_URL}/api/rahaza/production-calendar/seed-national", headers=auth)
        assert resp.status_code in [200, 201], f"Status: {resp.status_code}, Body: {resp.text}"
        data = resp.json()
        print(f"Seeded: {data}")

    def test_get_calendar_after_seed(self, auth):
        resp = requests.get(f"{BASE_URL}/api/rahaza/production-calendar", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        items = data if isinstance(data, list) else data.get("items", [])
        print(f"Calendar entries after seed: {len(items)}")

    def test_working_days_calculator(self, auth):
        resp = requests.get(f"{BASE_URL}/api/rahaza/production-calendar/working-days", 
                           params={"from_date": "2026-01-01", "to_date": "2026-01-31"},
                           headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        print(f"Working days: {data}")

class TestPWA:
    def test_manifest_accessible(self):
        frontend_url = os.environ.get('REACT_APP_BACKEND_URL', '').replace('/api', '')
        # Manifest is served by React frontend
        resp = requests.get(f"{BASE_URL.replace('/api','')}/manifest.json")
        print(f"Manifest status: {resp.status_code}")
        # Just check it's accessible
        assert resp.status_code in [200, 301, 302]
