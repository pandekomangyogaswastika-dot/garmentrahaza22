"""Sprint 26 backend tests:
- End-of-Shift PDF Report (GET /api/rahaza/shift-handovers/{id}/pdf)
- LKP PDF without/with production photos
- Section L 'FOTO PRODUKSI & QC' rendering with multiple photos (regression for empty-cell padding fix)
"""
import io
import os
import re
import pytest
import requests
import pdfplumber
from PIL import Image

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://rahaza-preview-2.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@garment.com"
ADMIN_PASSWORD = "Admin@123"


# ─── fixtures ──────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    tok = data.get("token") or data.get("access_token")
    assert tok, f"No token in login response: {data}"
    return tok


@pytest.fixture(scope="module")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def jpeg_image_bytes():
    """Generate a small JPEG in-memory."""
    img = Image.new("RGB", (200, 150), color=(120, 180, 220))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70)
    buf.seek(0)
    return buf.getvalue()


# ─── Shift Handover PDF tests ───────────────────────────────────────────
class TestShiftHandoverPDF:
    @pytest.fixture(scope="class")
    def handover_id(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/rahaza/shift-handovers", headers=auth_headers, timeout=15)
        assert r.status_code == 200, f"List handovers failed: {r.status_code}"
        items = r.json() if isinstance(r.json(), list) else r.json().get("items") or r.json().get("data") or []
        if not items:
            pytest.skip("No shift handovers exist; skipping PDF tests")
        return items[0]["id"]

    def test_pdf_unauthorized(self, handover_id):
        r = requests.get(f"{BASE_URL}/api/rahaza/shift-handovers/{handover_id}/pdf", timeout=15)
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"

    def test_pdf_404_for_nonexistent(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/rahaza/shift-handovers/non-existent-id-xyz/pdf",
                         headers=auth_headers, timeout=15)
        assert r.status_code == 404

    def test_pdf_download_ok(self, auth_headers, handover_id):
        r = requests.get(f"{BASE_URL}/api/rahaza/shift-handovers/{handover_id}/pdf",
                         headers=auth_headers, timeout=30)
        assert r.status_code == 200, f"Body: {r.text[:300]}"
        assert "application/pdf" in r.headers.get("Content-Type", "")
        assert r.content[:4] == b"%PDF", f"Not a PDF, starts with {r.content[:8]}"
        assert len(r.content) > 1024, f"PDF suspiciously small ({len(r.content)} bytes)"


# ─── LKP PDF tests ──────────────────────────────────────────────────────
class TestLKPPdf:
    @pytest.fixture(scope="class")
    def wo_id(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/rahaza/work-orders", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        rows = r.json() if isinstance(r.json(), list) else r.json().get("items") or []
        if not rows:
            pytest.skip("No work orders exist")
        # prefer one with status released/in_progress
        for w in rows:
            if w.get("status") in ("released", "in_progress"):
                return w["id"]
        return rows[0]["id"]

    @pytest.fixture(scope="class")
    def lkp_id(self, auth_headers, wo_id):
        body = {"tech_pack": {"color": "Navy"}, "sop_steps": [], "qc": {}, "packing": {}, "special_notes": "TEST_LKP"}
        r = requests.post(f"{BASE_URL}/api/rahaza/work-orders/{wo_id}/lkp",
                          headers=auth_headers, json=body, timeout=30)
        assert r.status_code in (200, 201), f"Create LKP failed: {r.status_code} {r.text[:300]}"
        return r.json()["id"]

    def test_lkp_pdf_no_photos(self, auth_headers, lkp_id):
        r = requests.get(f"{BASE_URL}/api/rahaza/lkp/{lkp_id}/pdf",
                         headers=auth_headers, timeout=30)
        assert r.status_code == 200, f"Body: {r.text[:300]}"
        assert r.content[:4] == b"%PDF"
        assert "application/pdf" in r.headers.get("Content-Type", "")
        # Section L should NOT appear if no photos
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            text = "\n".join((p.extract_text() or "") for p in pdf.pages)
        assert "L. FOTO PRODUKSI" not in text, "Section L should be absent when no photos"
        # Save baseline size for next test
        TestLKPPdf._baseline_size = len(r.content)

    def test_upload_photo_returns_path_and_id(self, auth_headers, lkp_id, jpeg_image_bytes):
        files = {"file": ("photo1.jpg", jpeg_image_bytes, "image/jpeg")}
        data = {"caption": "TEST_QC_Check_Photo_One", "type": "qc_check"}
        r = requests.post(f"{BASE_URL}/api/rahaza/lkp/{lkp_id}/photos",
                          headers=auth_headers, files=files, data=data, timeout=30)
        assert r.status_code in (200, 201), f"Upload failed: {r.status_code} {r.text[:300]}"
        body = r.json()
        assert "id" in body
        assert "storage_path" in body
        TestLKPPdf._photo1_caption = "TEST_QC_Check_Photo_One"

    def test_lkp_pdf_with_one_photo(self, auth_headers, lkp_id):
        r = requests.get(f"{BASE_URL}/api/rahaza/lkp/{lkp_id}/pdf",
                         headers=auth_headers, timeout=60)
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"
        new_size = len(r.content)
        baseline = getattr(TestLKPPdf, "_baseline_size", 0)
        # PDF size should grow once an embedded image is present
        assert new_size > baseline, f"PDF size did not grow ({baseline} -> {new_size})"
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            text = "\n".join((p.extract_text() or "") for p in pdf.pages)
            n_images = sum(len(p.images or []) for p in pdf.pages)
        assert "L. FOTO PRODUKSI" in text, "Section L header missing"
        assert "TEST_QC_Check_Photo_One" in text, "Caption missing in PDF"
        assert n_images >= 1, f"Expected >=1 image stream, got {n_images}"

    def test_lkp_pdf_with_multiple_photos_no_crash(self, auth_headers, lkp_id, jpeg_image_bytes):
        # Upload 2 more photos => 3 total → triggers row padding code path
        for i in (2, 3):
            files = {"file": (f"photo{i}.jpg", jpeg_image_bytes, "image/jpeg")}
            data = {"caption": f"TEST_Photo_{i}", "type": "qc_check"}
            r = requests.post(f"{BASE_URL}/api/rahaza/lkp/{lkp_id}/photos",
                              headers=auth_headers, files=files, data=data, timeout=30)
            assert r.status_code in (200, 201), f"Upload photo{i} failed: {r.text[:200]}"
        # Re-download — must NOT 500 on padding
        r = requests.get(f"{BASE_URL}/api/rahaza/lkp/{lkp_id}/pdf",
                         headers=auth_headers, timeout=60)
        assert r.status_code == 200, f"PDF regen with 3 photos failed: {r.status_code} {r.text[:300]}"
        assert r.content[:4] == b"%PDF"
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            text = "\n".join((p.extract_text() or "") for p in pdf.pages)
            n_images = sum(len(p.images or []) for p in pdf.pages)
        assert "L. FOTO PRODUKSI" in text
        assert n_images >= 3, f"Expected >=3 image streams, got {n_images}"
        # All captions present
        for cap in ("TEST_QC_Check_Photo_One", "TEST_Photo_2", "TEST_Photo_3"):
            assert cap in text, f"Caption '{cap}' missing"
