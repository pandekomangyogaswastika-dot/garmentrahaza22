"""
Backend tests for Lembar Kerja Produksi (LKP) feature.

Covers:
- Model image upload/delete (multipart, content-type, size, max-3 enforcement)
- LKP create (POST /work-orders/{wid}/lkp) with PDF generation, versioning
- LKP list (per WO and cross-WO with limit+filter)
- LKP detail (content_snapshot + audit_log)
- LKP PDF download (Authorization header AND ?auth= query param)
- LKP regenerate
- LKP soft-delete (status=revoked)
- Audit trail completeness
- BOM resolution from unified materials array
"""
import io
import os
import time
import pytest
import requests

def _read_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
        try:
            with open("/app/frontend/.env") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        url = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except Exception:
            pass
    if not url:
        raise RuntimeError("REACT_APP_BACKEND_URL not set")
    return url.rstrip("/")


BASE_URL = _read_backend_url()
ADMIN_EMAIL = "admin@garment.com"
ADMIN_PASSWORD = "Admin@123"


# ─── Fixtures ─────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def token(api):
    r = api.post(f"{BASE_URL}/api/auth/login",
                 json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if r.status_code != 200:
        pytest.skip(f"Login failed: {r.status_code} {r.text}")
    data = r.json()
    tok = data.get("token") or data.get("access_token")
    assert tok, f"no token in {data}"
    return tok


@pytest.fixture(scope="session")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def work_order(api, auth_headers):
    """Pick first WO for testing."""
    r = api.get(f"{BASE_URL}/api/rahaza/work-orders", headers=auth_headers)
    assert r.status_code == 200, r.text
    rows = r.json()
    assert isinstance(rows, list) and rows, "no WOs seeded"
    return rows[0]


@pytest.fixture(scope="session")
def model(api, auth_headers):
    r = api.get(f"{BASE_URL}/api/rahaza/models", headers=auth_headers)
    assert r.status_code == 200
    rows = r.json()
    assert rows, "no models seeded"
    return rows[0]


def _tiny_png() -> bytes:
    # 1x1 transparent PNG
    return (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00"
            b"\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9c"
            b"c\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01]\xcc\x86\xeb\x00\x00\x00"
            b"\x00IEND\xaeB`\x82")


# ─── 1. Health / auth sanity ──────────────────────────────────────────────
class TestSanity:
    def test_login(self, token):
        assert isinstance(token, str) and len(token) > 10

    def test_list_wos(self, work_order):
        assert work_order.get("id")
        assert work_order.get("wo_number")


# ─── 2. Model image upload ────────────────────────────────────────────────
class TestModelImages:
    uploaded_paths = []

    def test_clear_existing_images(self, api, auth_headers, model):
        """Delete any existing images so we have a clean slate for max-3 test."""
        for p in list(model.get("image_paths") or []):
            api.delete(
                f"{BASE_URL}/api/rahaza/models/{model['id']}/images",
                headers=auth_headers, json={"storage_path": p},
            )

    def test_reject_non_image(self, api, auth_headers, model):
        files = {"file": ("a.txt", b"hello", "text/plain")}
        r = requests.post(
            f"{BASE_URL}/api/rahaza/models/{model['id']}/images",
            headers={"Authorization": auth_headers["Authorization"]},
            files=files,
        )
        assert r.status_code == 400, r.text
        assert "gambar" in r.text.lower() or "image" in r.text.lower()

    def test_upload_image_ok(self, auth_headers, model):
        files = {"file": ("test.png", _tiny_png(), "image/png")}
        r = requests.post(
            f"{BASE_URL}/api/rahaza/models/{model['id']}/images",
            headers={"Authorization": auth_headers["Authorization"]},
            files=files,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "image_paths" in body and "added" in body
        TestModelImages.uploaded_paths.append(body["added"])
        assert body["added"] in body["image_paths"]

    def test_max_three_images(self, auth_headers, model):
        # already have 1; add 2 more
        for i in range(2):
            files = {"file": (f"t{i}.png", _tiny_png(), "image/png")}
            r = requests.post(
                f"{BASE_URL}/api/rahaza/models/{model['id']}/images",
                headers={"Authorization": auth_headers["Authorization"]},
                files=files,
            )
            assert r.status_code == 200, r.text
            TestModelImages.uploaded_paths.append(r.json()["added"])
        # 4th should fail
        files = {"file": ("t4.png", _tiny_png(), "image/png")}
        r = requests.post(
            f"{BASE_URL}/api/rahaza/models/{model['id']}/images",
            headers={"Authorization": auth_headers["Authorization"]},
            files=files,
        )
        assert r.status_code == 400, r.text
        assert "3" in r.text or "Maksimal" in r.text

    def test_delete_image_ok(self, api, auth_headers, model):
        if not TestModelImages.uploaded_paths:
            pytest.skip("no upload to delete")
        target = TestModelImages.uploaded_paths.pop()
        r = api.delete(
            f"{BASE_URL}/api/rahaza/models/{model['id']}/images",
            headers=auth_headers, json={"storage_path": target},
        )
        assert r.status_code == 200, r.text
        assert target not in r.json().get("image_paths", [])

    def test_delete_image_missing_body(self, api, auth_headers, model):
        r = api.delete(
            f"{BASE_URL}/api/rahaza/models/{model['id']}/images",
            headers=auth_headers, json={},
        )
        assert r.status_code == 400


# ─── 3. LKP CRUD lifecycle ────────────────────────────────────────────────
class TestLkpLifecycle:
    created = {}

    def test_list_lkp_for_wo(self, api, auth_headers, work_order):
        r = api.get(
            f"{BASE_URL}/api/rahaza/work-orders/{work_order['id']}/lkp",
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        TestLkpLifecycle.created["initial_count"] = len(r.json())

    def test_create_lkp_v1(self, api, auth_headers, work_order):
        body = {
            "tech_pack": {"color": "Navy", "gauge": "12g", "weight_per_pcs": "350g"},
            "sop_steps": [
                {
                    "process_name": "Rajut",
                    "tools": ["Mesin Shima Seiki", "Cone benang"],
                    "safety": ["Pakai sarung tangan", "Periksa tegangan benang"],
                    "steps": ["Set program", "Load benang", "Start mesin", "Cek hasil"],
                    "acceptance_criteria": "Tidak ada hole / drop stitch",
                    "common_defects": ["hole", "stitch loose"],
                }
            ],
            "qc": {"aql_level": "2.5", "checkpoints": ["Periksa knit", "Periksa size"]},
            "packing": {"qty_per_carton": 24, "fold_method": "Standard fold"},
            "special_notes": "TEST_LKP - automated test run",
        }
        r = api.post(
            f"{BASE_URL}/api/rahaza/work-orders/{work_order['id']}/lkp",
            headers=auth_headers, json=body,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("id") and d.get("lkp_number", "").startswith("LKP-")
        assert d.get("version") >= 1
        assert d.get("status") == "released"
        assert d.get("download_count") == 0
        assert isinstance(d.get("audit_log"), list) and len(d["audit_log"]) >= 1
        assert d["audit_log"][0]["action"] == "created"
        assert d["audit_log"][0]["version"] == d["version"]
        TestLkpLifecycle.created["lkp_v1"] = d

    def test_versioning_v2(self, api, auth_headers, work_order):
        prev = TestLkpLifecycle.created["lkp_v1"]
        r = api.post(
            f"{BASE_URL}/api/rahaza/work-orders/{work_order['id']}/lkp",
            headers=auth_headers, json={"special_notes": "v2"},
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["version"] == prev["version"] + 1, f"expected v{prev['version']+1} got v{d['version']}"
        TestLkpLifecycle.created["lkp_v2"] = d

    def test_get_detail(self, api, auth_headers):
        lkp = TestLkpLifecycle.created["lkp_v1"]
        r = api.get(f"{BASE_URL}/api/rahaza/lkp/{lkp['id']}", headers=auth_headers)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["id"] == lkp["id"]
        assert "content_snapshot" in d
        cs = d["content_snapshot"]
        # BOM resolution check — should have been built (yarn or accessory should be resolved)
        bom = cs.get("bom_snapshot") or {}
        assert "yarn_materials" in bom or "accessory_materials" in bom
        # process_flow filled from masters
        assert isinstance(cs.get("process_flow"), list)
        assert "audit_log" in d

    def test_list_per_wo_after_create(self, api, auth_headers, work_order):
        r = api.get(
            f"{BASE_URL}/api/rahaza/work-orders/{work_order['id']}/lkp",
            headers=auth_headers,
        )
        assert r.status_code == 200
        rows = r.json()
        # latest first
        assert rows and rows[0]["version"] >= rows[-1]["version"]
        # content_snapshot excluded from list
        assert "content_snapshot" not in rows[0]

    def test_cross_wo_list(self, api, auth_headers, work_order):
        r = api.get(
            f"{BASE_URL}/api/rahaza/lkp?limit=10&work_order_id={work_order['id']}",
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        rows = r.json()
        assert isinstance(rows, list) and rows
        assert all(r.get("work_order_id") == work_order["id"] for r in rows)

    def test_cross_wo_list_default(self, api, auth_headers):
        r = api.get(f"{BASE_URL}/api/rahaza/lkp?limit=5", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) <= 5


# ─── 4. PDF download (header + query token) + audit trail ─────────────────
class TestLkpPdf:
    def test_download_pdf_header_auth(self, api, auth_headers):
        lkp = TestLkpLifecycle.created["lkp_v1"]
        r = api.get(
            f"{BASE_URL}/api/rahaza/lkp/{lkp['id']}/pdf",
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        assert r.headers.get("content-type", "").startswith("application/pdf"), r.headers
        assert r.content[:4] == b"%PDF", f"not a PDF: {r.content[:20]}"
        assert len(r.content) > 1000, "PDF unexpectedly small"

    def test_download_pdf_query_auth(self, token):
        lkp = TestLkpLifecycle.created["lkp_v1"]
        r = requests.get(
            f"{BASE_URL}/api/rahaza/lkp/{lkp['id']}/pdf?auth={token}",
        )
        assert r.status_code == 200, r.text
        assert r.content[:4] == b"%PDF"

    def test_download_no_auth(self):
        lkp = TestLkpLifecycle.created["lkp_v1"]
        r = requests.get(f"{BASE_URL}/api/rahaza/lkp/{lkp['id']}/pdf")
        assert r.status_code == 401

    def test_download_count_and_audit(self, api, auth_headers):
        lkp = TestLkpLifecycle.created["lkp_v1"]
        r = api.get(f"{BASE_URL}/api/rahaza/lkp/{lkp['id']}", headers=auth_headers)
        d = r.json()
        # we downloaded twice above (header + query)
        assert d.get("download_count", 0) >= 2, f"download_count={d.get('download_count')}"
        actions = [e.get("action") for e in d.get("audit_log") or []]
        assert actions.count("downloaded") >= 2, actions


# ─── 5. Regenerate ────────────────────────────────────────────────────────
class TestLkpRegenerate:
    def test_regenerate_ok(self, api, auth_headers):
        lkp = TestLkpLifecycle.created["lkp_v1"]
        r = api.post(
            f"{BASE_URL}/api/rahaza/lkp/{lkp['id']}/regenerate",
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("ok") is True
        # audit log should append "regenerated"
        d = api.get(f"{BASE_URL}/api/rahaza/lkp/{lkp['id']}", headers=auth_headers).json()
        actions = [e.get("action") for e in d.get("audit_log") or []]
        assert "regenerated" in actions

    def test_regenerate_404(self, api, auth_headers):
        r = api.post(
            f"{BASE_URL}/api/rahaza/lkp/nonexistent-id/regenerate",
            headers=auth_headers,
        )
        assert r.status_code == 404


# ─── 6. Soft-delete ───────────────────────────────────────────────────────
class TestLkpDelete:
    def test_soft_delete(self, api, auth_headers):
        lkp = TestLkpLifecycle.created["lkp_v2"]
        r = api.delete(f"{BASE_URL}/api/rahaza/lkp/{lkp['id']}", headers=auth_headers)
        assert r.status_code == 200, r.text
        d = api.get(f"{BASE_URL}/api/rahaza/lkp/{lkp['id']}", headers=auth_headers).json()
        assert d.get("status") == "revoked"
        actions = [e.get("action") for e in d.get("audit_log") or []]
        assert "revoked" in actions

    def test_delete_404(self, api, auth_headers):
        r = api.delete(f"{BASE_URL}/api/rahaza/lkp/nonexistent", headers=auth_headers)
        assert r.status_code == 404


# ─── 7. 404 paths ─────────────────────────────────────────────────────────
class TestErrors:
    def test_create_lkp_invalid_wo(self, api, auth_headers):
        r = api.post(
            f"{BASE_URL}/api/rahaza/work-orders/nonexistent/lkp",
            headers=auth_headers, json={},
        )
        assert r.status_code == 404

    def test_get_invalid_lkp(self, api, auth_headers):
        r = api.get(f"{BASE_URL}/api/rahaza/lkp/nonexistent", headers=auth_headers)
        assert r.status_code == 404

    def test_pdf_invalid_lkp(self, api, auth_headers):
        r = api.get(f"{BASE_URL}/api/rahaza/lkp/nonexistent/pdf", headers=auth_headers)
        assert r.status_code == 404
