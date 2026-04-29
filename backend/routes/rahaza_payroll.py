"""
PT Rahaza — Payroll (Fase 8b + 8c)

Fase 8b — Payroll Profiles per Pegawai:
  - /payroll-profiles               (GET list, POST upsert by employee_id)
  - /payroll-profiles/{employee_id} (GET one, PUT, DELETE)

Fase 8c — Payroll Run & Payslip:
  - /payroll-runs                     (GET list, POST create + auto-generate payslips)
  - /payroll-runs/{id}                (GET detail, DELETE [draft only])
  - /payroll-runs/{id}/finalize       (POST lock)
  - /payroll-runs/{id}/export         (GET CSV)
  - /payslips?run_id=&employee_id=   (GET list)
  - /payslips/{id}                   (GET, PUT [edit deductions/notes; draft only])

Schemes (4):
  - pcs      : borongan per pcs — qty × rate (by process or default)
  - hourly   : borongan per jam — jam_kerja × rate
  - weekly   : mingguan — jumlah minggu × rate
  - monthly  : bulanan — 1 × rate (periode diset 1 bulan oleh user)

Aturan khusus (keputusan user):
  - Rework pcs dibayar 2x: hitung SEMUA event_type='output' per operator
    (operator Rajut dapat output awal, operator Washer/Sontek dapat output rework terpisah)
  - Overtime selalu manual input dari attendance.overtime_hours × overtime_rate
  - Deductions configurable per slip (array items label+amount)
  - Periode payroll configurable per-pegawai via profile, tapi run window menetapkan [period_from, period_to]
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from database import get_db
from auth import require_auth, serialize_doc, log_activity
import uuid
import io
import csv
import logging
from datetime import datetime, timezone, date, timedelta
from typing import Optional

from routes.rahaza_posting import post_payroll_run

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rahaza", tags=["rahaza-payroll"])

VALID_SCHEMES = ["pcs", "hourly", "weekly", "monthly"]
VALID_PERIOD_TYPES = ["weekly", "monthly"]
VALID_RUN_STATUS = ["draft", "finalized", "cancelled"]


def _uid(): return str(uuid.uuid4())
def _now(): return datetime.now(timezone.utc)


async def _require_hr(request: Request):
    user = await require_auth(request)
    role = (user.get("role") or "").lower()
    if role in ("superadmin", "admin", "owner", "hr", "manager"):
        return user
    perms = user.get("_permissions") or []
    if "*" in perms or "hr.manage" in perms or "payroll.manage" in perms:
        return user
    raise HTTPException(403, "Forbidden: butuh permission HR/payroll.")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ FASE 8b — PAYROLL PROFILES                                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@router.get("/payroll-profiles")
async def list_profiles(request: Request, employee_id: Optional[str] = None, active_only: bool = True):
    await require_auth(request)
    db = get_db()
    q = {}
    if active_only:
        q["active"] = True
    if employee_id:
        q["employee_id"] = employee_id
    rows = await db.rahaza_payroll_profiles.find(q, {"_id": 0}).to_list(None)
    # Enrich with employee info
    emp_ids = list({r.get("employee_id") for r in rows if r.get("employee_id")})
    emps = await db.rahaza_employees.find({"id": {"$in": emp_ids}}, {"_id": 0}).to_list(None) if emp_ids else []
    e_map = {e["id"]: e for e in emps}
    for r in rows:
        e = e_map.get(r.get("employee_id")) or {}
        r["employee_code"] = e.get("employee_code")
        r["employee_name"] = e.get("name")
    rows.sort(key=lambda r: r.get("employee_code") or "")
    return serialize_doc(rows)


@router.get("/payroll-profiles/{employee_id}")
async def get_profile(employee_id: str, request: Request):
    await require_auth(request)
    db = get_db()
    row = await db.rahaza_payroll_profiles.find_one({"employee_id": employee_id, "active": True}, {"_id": 0})
    if not row:
        raise HTTPException(404, "Profile payroll belum dibuat untuk pegawai ini.")
    emp = await db.rahaza_employees.find_one({"id": employee_id}, {"_id": 0}) or {}
    row["employee_code"] = emp.get("employee_code")
    row["employee_name"] = emp.get("name")
    return serialize_doc(row)


def _normalize_profile(body: dict) -> dict:
    pay_scheme = (body.get("pay_scheme") or "monthly").lower()
    period_type = (body.get("period_type") or "monthly").lower()
    if pay_scheme not in VALID_SCHEMES:
        raise HTTPException(400, f"pay_scheme harus salah satu: {VALID_SCHEMES}")
    if period_type not in VALID_PERIOD_TYPES:
        raise HTTPException(400, f"period_type harus salah satu: {VALID_PERIOD_TYPES}")
    cutoff = body.get("cutoff_config") or {}
    # Defaults
    if period_type == "weekly" and "week_start_day" not in cutoff:
        cutoff["week_start_day"] = 1  # Monday
    if period_type == "monthly" and "start_day" not in cutoff:
        cutoff["start_day"] = 1  # 1st of month
    # Validate ranges
    wsd = cutoff.get("week_start_day")
    if wsd is not None and (not isinstance(wsd, int) or not (0 <= wsd <= 6)):
        raise HTTPException(400, "week_start_day harus 0..6 (0=Senin..6=Minggu)")
    sd = cutoff.get("start_day")
    if sd is not None and (not isinstance(sd, int) or not (1 <= sd <= 28)):
        raise HTTPException(400, "start_day harus 1..28")
    pcs_rates = body.get("pcs_process_rates") or []
    norm_pcs_rates = []
    for r in pcs_rates:
        if not r.get("process_id"):
            continue
        norm_pcs_rates.append({
            "process_id": r["process_id"],
            "process_code": (r.get("process_code") or "").upper(),
            "rate": float(r.get("rate") or 0),
        })
    return {
        "employee_id": body.get("employee_id"),
        "pay_scheme": pay_scheme,
        "period_type": period_type,
        "cutoff_config": cutoff,
        "base_rate": float(body.get("base_rate") or 0),
        "overtime_rate": float(body.get("overtime_rate") or 0),
        "pcs_process_rates": norm_pcs_rates,
        "notes": body.get("notes") or "",
    }


@router.post("/payroll-profiles")
async def upsert_profile(request: Request):
    user = await _require_hr(request)
    db = get_db()
    body = await request.json()
    emp_id = body.get("employee_id")
    if not emp_id:
        raise HTTPException(400, "employee_id wajib.")
    emp = await db.rahaza_employees.find_one({"id": emp_id}, {"_id": 0})
    if not emp:
        raise HTTPException(404, f"Pegawai dengan id={emp_id} tidak ditemukan.")
    doc = _normalize_profile(body)
    existing = await db.rahaza_payroll_profiles.find_one({"employee_id": emp_id, "active": True}, {"_id": 0})
    now = _now()
    doc.update({
        "active": True,
        "updated_at": now,
        "updated_by": user["id"],
        "updated_by_name": user.get("name", ""),
    })
    if existing:
        await db.rahaza_payroll_profiles.update_one({"id": existing["id"]}, {"$set": doc})
        out = await db.rahaza_payroll_profiles.find_one({"id": existing["id"]}, {"_id": 0})
    else:
        doc["id"] = _uid()
        doc["created_at"] = now
        doc["created_by"] = user["id"]
        doc["created_by_name"] = user.get("name", "")
        await db.rahaza_payroll_profiles.insert_one(doc)
        out = await db.rahaza_payroll_profiles.find_one({"id": doc["id"]}, {"_id": 0})
    await log_activity(user["id"], user.get("name", ""), "upsert", "rahaza.payroll_profile", emp_id)
    out["employee_code"] = emp.get("employee_code")
    out["employee_name"] = emp.get("name")
    return serialize_doc(out)


@router.put("/payroll-profiles/{pid}")
async def update_profile(pid: str, request: Request):
    user = await _require_hr(request)
    db = get_db()
    existing = await db.rahaza_payroll_profiles.find_one({"id": pid}, {"_id": 0})
    if not existing:
        raise HTTPException(404, "Profile tidak ditemukan.")
    body = await request.json()
    body["employee_id"] = existing["employee_id"]  # cannot change
    doc = _normalize_profile(body)
    doc.update({
        "updated_at": _now(),
        "updated_by": user["id"],
        "updated_by_name": user.get("name", ""),
    })
    await db.rahaza_payroll_profiles.update_one({"id": pid}, {"$set": doc})
    out = await db.rahaza_payroll_profiles.find_one({"id": pid}, {"_id": 0})
    return serialize_doc(out)


@router.delete("/payroll-profiles/{pid}")
async def delete_profile(pid: str, request: Request):
    user = await _require_hr(request)
    db = get_db()
    res = await db.rahaza_payroll_profiles.update_one({"id": pid, "active": True}, {"$set": {"active": False, "updated_at": _now(), "updated_by": user["id"]}})
    if res.matched_count == 0:
        raise HTTPException(404, "Profile tidak ditemukan atau sudah nonaktif.")
    return {"status": "deleted"}


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ FASE 8c — PAYROLL RUN & PAYSLIP                                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def _to_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _date_range_filter(from_iso: str, to_iso: str) -> dict:
    return {"$gte": from_iso, "$lte": to_iso}


async def _generate_run_number(db) -> str:
    today = date.today().strftime("%Y%m%d")
    prefix = f"PR-{today}-"
    count = await db.rahaza_payroll_runs.count_documents({"run_number": {"$regex": f"^{prefix}"}})
    return f"{prefix}{count+1:03d}"


async def _compute_payslip_for_employee(db, profile: dict, period_from: str, period_to: str, emp: dict) -> dict:
    """Hitung slip payroll untuk 1 pegawai berdasarkan profile + window."""
    scheme = profile["pay_scheme"]
    base_rate = float(profile.get("base_rate") or 0)
    ot_rate = float(profile.get("overtime_rate") or 0)
    emp_id = profile["employee_id"]

    earnings = []
    source_refs = {"wip_event_count": 0, "attendance_event_count": 0, "process_breakdown": {}}

    # Query attendance untuk periode
    att_rows = await db.rahaza_attendance_events.find({
        "employee_id": emp_id,
        "date": _date_range_filter(period_from, period_to),
    }, {"_id": 0}).to_list(None)
    source_refs["attendance_event_count"] = len(att_rows)
    total_hours = sum(float(r.get("hours_worked") or 0) for r in att_rows)
    total_ot = sum(float(r.get("overtime_hours") or 0) for r in att_rows)
    days_hadir = sum(1 for r in att_rows if r.get("status") == "hadir")

    if scheme == "pcs":
        # Sum WIP events output oleh operator ini dalam periode
        # Event date bisa dicompare via string ISO karena format ISO cocok lexicographic
        wip_rows = await db.rahaza_wip_events.find({
            "operator_id": emp_id,
            "event_type": "output",
            "event_date": _date_range_filter(period_from, period_to),
        }, {"_id": 0}).to_list(None)
        source_refs["wip_event_count"] = len(wip_rows)
        # Group by process_id
        proc_map = {}
        for ev in wip_rows:
            pid = ev.get("process_id") or "unknown"
            if pid not in proc_map:
                proc_map[pid] = {"qty": 0, "events": 0, "process_code": ev.get("process_code") or ""}
            proc_map[pid]["qty"] += int(ev.get("qty") or 0)
            proc_map[pid]["events"] += 1
            if ev.get("process_code"):
                proc_map[pid]["process_code"] = ev["process_code"]
        # Cari rate per process (override) atau base_rate
        rate_overrides = {r["process_id"]: r["rate"] for r in (profile.get("pcs_process_rates") or [])}
        for pid, info in proc_map.items():
            rate = float(rate_overrides.get(pid, base_rate))
            amount = round(info["qty"] * rate)
            label = f"Borongan pcs · {info.get('process_code') or 'Proses'}"
            earnings.append({
                "label": label,
                "qty": info["qty"],
                "unit": "pcs",
                "rate": rate,
                "amount": amount,
            })
            source_refs["process_breakdown"][info.get("process_code") or pid] = {
                "qty": info["qty"],
                "rate": rate,
                "amount": amount,
            }
    elif scheme == "hourly":
        amount = round(total_hours * base_rate)
        earnings.append({
            "label": "Borongan jam",
            "qty": round(total_hours, 2),
            "unit": "jam",
            "rate": base_rate,
            "amount": amount,
        })
    elif scheme == "weekly":
        try:
            d_from = _to_date(period_from)
            d_to = _to_date(period_to)
            days = (d_to - d_from).days + 1
            weeks = max(1, round(days / 7))
        except Exception:
            weeks = 1
        amount = round(weeks * base_rate)
        earnings.append({
            "label": "Gaji mingguan",
            "qty": weeks,
            "unit": "minggu",
            "rate": base_rate,
            "amount": amount,
        })
    elif scheme == "monthly":
        amount = round(base_rate)
        earnings.append({
            "label": "Gaji bulanan",
            "qty": 1,
            "unit": "bulan",
            "rate": base_rate,
            "amount": amount,
        })

    earnings_total = sum(e["amount"] for e in earnings)
    overtime_amount = round(total_ot * ot_rate)
    gross = earnings_total + overtime_amount

    payslip = {
        "id": _uid(),
        "employee_id": emp_id,
        "employee_code": emp.get("employee_code"),
        "employee_name": emp.get("name"),
        "pay_scheme": scheme,
        "period_from": period_from,
        "period_to": period_to,
        "earnings": earnings,
        "earnings_total": earnings_total,
        "overtime_hours": round(total_ot, 2),
        "overtime_rate": ot_rate,
        "overtime_amount": overtime_amount,
        "total_hours_worked": round(total_hours, 2),
        "days_hadir": days_hadir,
        "gross_pay": gross,
        "deductions": [],
        "deductions_total": 0,
        "net_pay": gross,
        "source_refs": source_refs,
        "notes": "",
    }
    return payslip


@router.get("/payroll-runs")
async def list_runs(request: Request, status: Optional[str] = None, limit: int = 50, skip: int = 0):
    await require_auth(request)
    db = get_db()
    q = {}
    if status:
        q["status"] = status
    rows = await db.rahaza_payroll_runs.find(q, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(None)
    return serialize_doc(rows)


@router.post("/payroll-runs")
async def create_run(request: Request):
    user = await _require_hr(request)
    db = get_db()
    body = await request.json()
    period_from = (body.get("period_from") or "").strip()
    period_to = (body.get("period_to") or "").strip()
    if not (period_from and period_to):
        raise HTTPException(400, "period_from & period_to wajib (YYYY-MM-DD).")
    try:
        _to_date(period_from); _to_date(period_to)
    except Exception:
        raise HTTPException(400, "Format tanggal harus YYYY-MM-DD.")
    if period_from > period_to:
        raise HTTPException(400, "period_from tidak boleh > period_to.")

    # Ambil profile aktif
    employee_ids = body.get("employee_ids") or []
    q = {"active": True}
    if employee_ids:
        q["employee_id"] = {"$in": employee_ids}
    profiles = await db.rahaza_payroll_profiles.find(q, {"_id": 0}).to_list(None)
    if not profiles:
        raise HTTPException(400, "Tidak ada payroll profile aktif untuk diproses. Buat profile dulu di menu Payroll Profiles.")

    emp_ids = [p["employee_id"] for p in profiles]
    emps = await db.rahaza_employees.find({"id": {"$in": emp_ids}}, {"_id": 0}).to_list(None)
    e_map = {e["id"]: e for e in emps}

    # Create run header
    run_number = await _generate_run_number(db)
    run_id = _uid()
    now = _now()

    # Generate payslips
    payslips = []
    for p in profiles:
        emp = e_map.get(p["employee_id"])
        if not emp:
            continue
        slip = await _compute_payslip_for_employee(db, p, period_from, period_to, emp)
        slip.update({
            "run_id": run_id,
            "run_number": run_number,
            "created_at": now,
            "updated_at": now,
        })
        payslips.append(slip)

    if payslips:
        await db.rahaza_payslips.insert_many(payslips)

    total_gross = sum(s["gross_pay"] for s in payslips)
    total_ded = sum(s["deductions_total"] for s in payslips)
    total_net = sum(s["net_pay"] for s in payslips)

    run_doc = {
        "id": run_id,
        "run_number": run_number,
        "period_from": period_from,
        "period_to": period_to,
        "status": "draft",
        "total_employees": len(payslips),
        "total_gross": total_gross,
        "total_deductions": total_ded,
        "total_net": total_net,
        "notes": body.get("notes") or "",
        "created_at": now,
        "created_by": user["id"],
        "created_by_name": user.get("name", ""),
        "updated_at": now,
    }
    await db.rahaza_payroll_runs.insert_one(run_doc)
    await log_activity(user["id"], user.get("name", ""), "create", "rahaza.payroll_run", run_number)
    out = await db.rahaza_payroll_runs.find_one({"id": run_id}, {"_id": 0})
    return serialize_doc(out)


@router.get("/payroll-runs/{run_id}")
async def get_run(run_id: str, request: Request):
    await require_auth(request)
    db = get_db()
    run = await db.rahaza_payroll_runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(404, "Payroll run tidak ditemukan.")
    payslips = await db.rahaza_payslips.find({"run_id": run_id}, {"_id": 0}).sort("employee_code", 1).to_list(None)
    return serialize_doc({"run": run, "payslips": payslips})


@router.post("/payroll-runs/{run_id}/finalize")
async def finalize_run(run_id: str, request: Request):
    user = await _require_hr(request)
    db = get_db()
    run = await db.rahaza_payroll_runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(404, "Payroll run tidak ditemukan.")
    if run.get("status") != "draft":
        raise HTTPException(400, f"Run sudah ber-status '{run.get('status')}', tidak bisa finalize.")
    # Recalc totals dari payslips (in case deductions diubah)
    payslips = await db.rahaza_payslips.find({"run_id": run_id}, {"_id": 0}).to_list(None)
    total_gross = sum(s.get("gross_pay", 0) for s in payslips)
    total_ded = sum(s.get("deductions_total", 0) for s in payslips)
    total_net = sum(s.get("net_pay", 0) for s in payslips)
    await db.rahaza_payroll_runs.update_one({"id": run_id}, {"$set": {
        "status": "finalized",
        "total_gross": total_gross,
        "total_deductions": total_ded,
        "total_net": total_net,
        "finalized_at": _now(),
        "finalized_by": user["id"],
        "finalized_by_name": user.get("name", ""),
        "updated_at": _now(),
    }})
    await log_activity(user["id"], user.get("name", ""), "finalize", "rahaza.payroll_run", run.get("run_number"))
    out = await db.rahaza_payroll_runs.find_one({"id": run_id}, {"_id": 0})

    # ── F3 Auto-post Payroll JE
    posting_result = None
    try:
        posting_result = await post_payroll_run(db, out, user)
    except Exception as e:
        log.exception("Payroll auto-post failed")
        posting_result = {"ok": False, "error": str(e)}
    out = await db.rahaza_payroll_runs.find_one({"id": run_id}, {"_id": 0})
    out["_posting_result"] = posting_result
    return serialize_doc(out)


@router.post("/payroll-runs/{run_id}/post-to-gl")
async def retry_post_payroll(run_id: str, request: Request):
    """F3: manual retry post payroll run to GL (idempotent)."""
    user = await _require_hr(request)
    db = get_db()
    run = await db.rahaza_payroll_runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(404, "Payroll run tidak ditemukan.")
    if run.get("status") != "finalized":
        raise HTTPException(400, "Hanya run yang sudah finalized yang bisa di-post.")
    result = await post_payroll_run(db, run, user)
    out = await db.rahaza_payroll_runs.find_one({"id": run_id}, {"_id": 0})
    out["_posting_result"] = result
    return serialize_doc(out)


@router.delete("/payroll-runs/{run_id}")
async def delete_run(run_id: str, request: Request):
    user = await _require_hr(request)
    db = get_db()
    run = await db.rahaza_payroll_runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(404, "Payroll run tidak ditemukan.")
    if run.get("status") == "finalized":
        raise HTTPException(400, "Run yang sudah finalized tidak bisa dihapus. Gunakan cancel atau buat run baru.")
    await db.rahaza_payslips.delete_many({"run_id": run_id})
    await db.rahaza_payroll_runs.delete_one({"id": run_id})
    return {"status": "deleted"}


@router.get("/payroll-runs/{run_id}/export")
async def export_run_csv(run_id: str, request: Request):
    await require_auth(request)
    db = get_db()
    run = await db.rahaza_payroll_runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(404, "Payroll run tidak ditemukan.")
    payslips = await db.rahaza_payslips.find({"run_id": run_id}, {"_id": 0}).sort("employee_code", 1).to_list(None)

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow([
        "run_number", "period_from", "period_to",
        "employee_code", "employee_name", "pay_scheme",
        "earnings_total", "overtime_hours", "overtime_amount",
        "gross_pay", "deductions_total", "net_pay",
        "days_hadir", "total_hours_worked",
    ])
    for s in payslips:
        w.writerow([
            run.get("run_number"), run.get("period_from"), run.get("period_to"),
            s.get("employee_code"), s.get("employee_name"), s.get("pay_scheme"),
            s.get("earnings_total", 0), s.get("overtime_hours", 0), s.get("overtime_amount", 0),
            s.get("gross_pay", 0), s.get("deductions_total", 0), s.get("net_pay", 0),
            s.get("days_hadir", 0), s.get("total_hours_worked", 0),
        ])
    buf.seek(0)
    filename = f"payroll_{run.get('run_number')}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── PDF helpers ────────────────────────────────────────────────────────────────

def _idr(n):
    """Format angka ke Rupiah Indonesia, contoh: 1500000 → Rp 1.500.000"""
    try:
        n = int(round(float(n or 0)))
    except Exception:
        n = 0
    return f"Rp {n:,}".replace(",", ".")


def _build_payslip_pdf(slip: dict, run: dict) -> io.BytesIO:
    """
    Generate satu halaman slip gaji (A5) untuk satu karyawan.
    Mengembalikan BytesIO berisi PDF.
    """
    from reportlab.lib.pagesizes import A5
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether,
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A5,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    W = A5[0] - 24 * mm  # usable width

    # ── styles ────────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()
    NAVY   = colors.HexColor("#1a2a4a")
    TEAL   = colors.HexColor("#0f6b8e")
    LIGHT  = colors.HexColor("#f0f6fa")
    GREY   = colors.HexColor("#6b7280")
    BLACK  = colors.black
    WHITE  = colors.white
    GREEN  = colors.HexColor("#1a7a4a")
    RED    = colors.HexColor("#b91c1c")

    h1  = ParagraphStyle("h1",  fontSize=13, fontName="Helvetica-Bold",  textColor=NAVY,  leading=16)
    h2  = ParagraphStyle("h2",  fontSize=9,  fontName="Helvetica",       textColor=TEAL,  leading=12)
    h3  = ParagraphStyle("h3",  fontSize=7,  fontName="Helvetica",       textColor=GREY,  leading=9)
    lbl = ParagraphStyle("lbl", fontSize=7.5, fontName="Helvetica-Bold", textColor=NAVY,  leading=10)
    val = ParagraphStyle("val", fontSize=7.5, fontName="Helvetica",      textColor=BLACK, leading=10)
    mono= ParagraphStyle("mono",fontSize=7.5, fontName="Courier",        textColor=BLACK, leading=10)
    rgt = ParagraphStyle("rgt", fontSize=7.5, fontName="Helvetica",      textColor=BLACK, leading=10, alignment=TA_RIGHT)
    net_style = ParagraphStyle("net", fontSize=11, fontName="Helvetica-Bold", textColor=WHITE, alignment=TA_RIGHT, leading=14)
    net_lbl   = ParagraphStyle("netl",fontSize=9,  fontName="Helvetica-Bold", textColor=WHITE, leading=12)

    # ── header: company logo + slip info ─────────────────────────────────────
    company_tbl = Table(
        [[
            Paragraph("<b>PT RAHAZA</b>", h1),
            Paragraph(f"<b>SLIP GAJI</b><br/><font size='7' color='#6b7280'>{run.get('run_number', '')}</font>", ParagraphStyle("sr", fontSize=9, fontName="Helvetica-Bold", textColor=TEAL, alignment=TA_RIGHT, leading=12)),
        ]],
        colWidths=[W * 0.6, W * 0.4],
    )
    company_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    sub_tbl = Table(
        [[
            Paragraph("Industri Garmen · Jl. Industri No. 1, Indonesia", h3),
            Paragraph(
                f"Periode: {slip.get('period_from', '')} s/d {slip.get('period_to', '')}",
                ParagraphStyle("pd", fontSize=7, fontName="Helvetica", textColor=GREY, alignment=TA_RIGHT, leading=9)
            ),
        ]],
        colWidths=[W * 0.6, W * 0.4],
    )
    sub_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    # ── employee info box ──────────────────────────────────────────────────────
    scheme_labels = {"pcs": "Borongan Pcs", "hourly": "Borongan Jam", "weekly": "Mingguan", "monthly": "Bulanan"}
    scheme = scheme_labels.get(slip.get("pay_scheme", ""), slip.get("pay_scheme", "-"))
    emp_rows = [
        ["Nama Karyawan", slip.get("employee_name", "-"), "Kode", slip.get("employee_code", "-")],
        ["Skema Gaji",    scheme,                          "Hadir", f"{slip.get('days_hadir', 0)} hari"],
        ["Jam Kerja",     f"{slip.get('total_hours_worked', 0)} jam", "Lembur", f"{slip.get('overtime_hours', 0)} jam"],
    ]
    emp_tbl = Table(
        [
            [Paragraph(r[0], lbl), Paragraph(str(r[1]), val), Paragraph(r[2], lbl), Paragraph(str(r[3]), val)]
            for r in emp_rows
        ],
        colWidths=[W * 0.22, W * 0.33, W * 0.16, W * 0.29],
    )
    emp_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), LIGHT),
        ("ROWBACKGROUND",(0, 0), (-1, 0),  colors.HexColor("#dbeaf4")),
        ("BOX",          (0, 0), (-1, -1), 0.5, TEAL),
        ("GRID",         (0, 0), (-1, -1), 0.3, colors.HexColor("#c0d8e8")),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))

    # ── earnings table ──────────────────────────────────────────────────────────
    earn_header = [
        Paragraph("Uraian Pendapatan", lbl),
        Paragraph("Qty", ParagraphStyle("lbl_c", fontSize=7.5, fontName="Helvetica-Bold", textColor=NAVY, alignment=TA_RIGHT, leading=10)),
        Paragraph("Satuan", ParagraphStyle("lbl_c2", fontSize=7.5, fontName="Helvetica-Bold", textColor=NAVY, alignment=TA_RIGHT, leading=10)),
        Paragraph("Jumlah", ParagraphStyle("lbl_r", fontSize=7.5, fontName="Helvetica-Bold", textColor=NAVY, alignment=TA_RIGHT, leading=10)),
    ]
    earn_rows = [earn_header]
    for e in (slip.get("earnings") or []):
        earn_rows.append([
            Paragraph(e.get("label", ""), val),
            Paragraph(str(e.get("qty", "")), mono),
            Paragraph(str(e.get("unit", "")), mono),
            Paragraph(_idr(e.get("amount", 0)), ParagraphStyle("am_r", fontSize=7.5, fontName="Courier", textColor=BLACK, alignment=TA_RIGHT, leading=10)),
        ])
    # overtime row
    if slip.get("overtime_amount", 0) > 0:
        earn_rows.append([
            Paragraph(f"Uang Lembur ({slip.get('overtime_hours', 0)} jam × {_idr(slip.get('overtime_rate', 0))})", val),
            Paragraph("", val),
            Paragraph("", val),
            Paragraph(_idr(slip.get("overtime_amount", 0)), ParagraphStyle("am_r2", fontSize=7.5, fontName="Courier", textColor=BLACK, alignment=TA_RIGHT, leading=10)),
        ])
    earn_tbl = Table(earn_rows, colWidths=[W * 0.47, W * 0.13, W * 0.14, W * 0.26])
    earn_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  TEAL),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  WHITE),
        ("ROWBACKGROUND",(0, 1), (-1, -1), None),
        ("ROWBACKGROUND",(0, 1), (-1, -1), LIGHT),
        ("ROWBACKGROUND",(0, 2), (-1, -2), WHITE),
        ("BOX",          (0, 0), (-1, -1), 0.5, TEAL),
        ("LINEBELOW",    (0, 0), (-1, 0),  0.5, TEAL),
        ("GRID",         (0, 1), (-1, -1), 0.2, colors.HexColor("#d1e4ed")),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))

    # earnings subtotal row
    earn_sub = Table(
        [[
            Paragraph("Total Pendapatan", ParagraphStyle("sub_l", fontSize=8, fontName="Helvetica-Bold", textColor=TEAL, leading=10)),
            Paragraph(_idr(slip.get("gross_pay", 0)), ParagraphStyle("sub_r", fontSize=8, fontName="Courier-Bold", textColor=TEAL, alignment=TA_RIGHT, leading=10)),
        ]],
        colWidths=[W * 0.74, W * 0.26],
    )
    earn_sub.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), colors.HexColor("#dbeaf4")),
        ("BOX",          (0, 0), (-1, -1), 0.5, TEAL),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))

    # ── deductions table ────────────────────────────────────────────────────────
    ded_rows_data = slip.get("deductions") or []
    ded_elements = []
    if ded_rows_data:
        ded_header = [
            Paragraph("Potongan", ParagraphStyle("dh_l", fontSize=7.5, fontName="Helvetica-Bold", textColor=WHITE, leading=10)),
            Paragraph("Jumlah", ParagraphStyle("dh_r", fontSize=7.5, fontName="Helvetica-Bold", textColor=WHITE, alignment=TA_RIGHT, leading=10)),
        ]
        ded_rows = [ded_header]
        for d in ded_rows_data:
            ded_rows.append([
                Paragraph(d.get("label", ""), val),
                Paragraph(_idr(d.get("amount", 0)), ParagraphStyle("dr_r", fontSize=7.5, fontName="Courier", textColor=RED, alignment=TA_RIGHT, leading=10)),
            ])
        ded_tbl = Table(ded_rows, colWidths=[W * 0.74, W * 0.26])
        ded_tbl.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#c0392b")),
            ("ROWBACKGROUND",(0, 1), (-1, -1), colors.HexColor("#fff5f5")),
            ("BOX",          (0, 0), (-1, -1), 0.5, colors.HexColor("#c0392b")),
            ("GRID",         (0, 1), (-1, -1), 0.2, colors.HexColor("#fcc")),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",   (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
            ("LEFTPADDING",  (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        ded_elements = [Spacer(1, 3 * mm), ded_tbl]

    # ── net pay box ─────────────────────────────────────────────────────────────
    net_tbl = Table(
        [[
            Paragraph("GAJI BERSIH", net_lbl),
            Paragraph(_idr(slip.get("net_pay", 0)), net_style),
        ]],
        colWidths=[W * 0.45, W * 0.55],
    )
    net_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), NAVY),
        ("BOX",          (0, 0), (-1, -1), 0,   NAVY),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [3]),
    ]))

    # ── attendance summary bar ──────────────────────────────────────────────────
    att_cells = [
        [Paragraph("Hadir", h3), Paragraph(str(slip.get("days_hadir", 0)), lbl)],
        [Paragraph("Jam Kerja", h3), Paragraph(f"{slip.get('total_hours_worked', 0)} j", lbl)],
        [Paragraph("Lembur", h3), Paragraph(f"{slip.get('overtime_hours', 0)} j", lbl)],
    ]
    att_bar = Table(
        [list(sum(att_cells, []))],
        colWidths=[W / 6] * 6,
    )
    att_bar.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), colors.HexColor("#f0f6fa")),
        ("BOX",          (0, 0), (-1, -1), 0.3, TEAL),
        ("GRID",         (0, 0), (-1, -1), 0.2, colors.HexColor("#c0d8e8")),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))

    # ── notes ───────────────────────────────────────────────────────────────────
    notes_el = []
    if slip.get("notes"):
        notes_el = [
            Spacer(1, 2 * mm),
            Paragraph(f"<i>Catatan: {slip['notes']}</i>", h3),
        ]

    # ── signature section ───────────────────────────────────────────────────────
    sig_tbl = Table(
        [[
            Paragraph("Disetujui oleh,", h3),
            Paragraph("Diterima oleh,", h3),
        ],
        [Spacer(1, 12 * mm), Spacer(1, 12 * mm)],
        [
            Paragraph("(________________)<br/><font size='6'>Manager / HRD</font>", ParagraphStyle("sig_l", fontSize=7, fontName="Helvetica", textColor=GREY, alignment=TA_CENTER, leading=9)),
            Paragraph(f"({slip.get('employee_name', '________________')})<br/><font size='6'>Karyawan</font>", ParagraphStyle("sig_r", fontSize=7, fontName="Helvetica", textColor=GREY, alignment=TA_CENTER, leading=9)),
        ]],
        colWidths=[W / 2, W / 2],
    )
    sig_tbl.setStyle(TableStyle([
        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
    ]))

    # ── assemble ────────────────────────────────────────────────────────────────
    story = [
        company_tbl,
        sub_tbl,
        HRFlowable(width="100%", thickness=1.5, color=TEAL, spaceAfter=4),
        emp_tbl,
        Spacer(1, 3 * mm),
        earn_tbl,
        earn_sub,
        *ded_elements,
        Spacer(1, 3 * mm),
        net_tbl,
        Spacer(1, 3 * mm),
        att_bar,
        *notes_el,
        Spacer(1, 5 * mm),
        HRFlowable(width="100%", thickness=0.5, color=GREY, spaceAfter=4),
        sig_tbl,
        Spacer(1, 2 * mm),
        Paragraph(
            f"<i>Slip ini dicetak secara otomatis oleh sistem ERP PT Rahaza · {_now().strftime('%d/%m/%Y %H:%M')}</i>",
            ParagraphStyle("foot", fontSize=5.5, fontName="Helvetica-Oblique", textColor=GREY, alignment=TA_CENTER, leading=7)
        ),
    ]
    doc.build(story)
    buf.seek(0)
    return buf


@router.get("/payslips/{pid}/pdf")
async def export_payslip_pdf(pid: str, request: Request):
    """Download PDF untuk satu slip gaji."""
    await require_auth(request)
    db = get_db()
    slip = await db.rahaza_payslips.find_one({"id": pid}, {"_id": 0})
    if not slip:
        raise HTTPException(404, "Payslip tidak ditemukan.")
    run = await db.rahaza_payroll_runs.find_one({"id": slip.get("run_id", "")}, {"_id": 0}) or {}
    try:
        buf = _build_payslip_pdf(dict(slip), dict(run))
    except Exception as e:
        log.error(f"PDF generation error: {e}", exc_info=True)
        raise HTTPException(500, f"Gagal generate PDF: {e}")
    fname = f"slip_{slip.get('employee_code', 'EMP')}_{slip.get('period_from', '')}_{slip.get('period_to', '')}.pdf"
    fname = fname.replace(" ", "_")
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.get("/payroll-runs/{run_id}/pdf")
async def export_run_pdf(run_id: str, request: Request):
    """Download PDF bundle berisi SEMUA slip gaji dalam satu run (1 halaman per karyawan)."""
    await require_auth(request)
    db = get_db()
    run = await db.rahaza_payroll_runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(404, "Payroll run tidak ditemukan.")
    payslips = await db.rahaza_payslips.find(
        {"run_id": run_id}, {"_id": 0}
    ).sort("employee_code", 1).to_list(None)
    if not payslips:
        raise HTTPException(404, "Tidak ada payslip dalam run ini.")

    try:
        from PyPDF2 import PdfWriter, PdfReader
        writer = PdfWriter()
        for slip in payslips:
            single_buf = _build_payslip_pdf(dict(slip), dict(run))
            reader = PdfReader(single_buf)
            for page in reader.pages:
                writer.add_page(page)
        out_buf = io.BytesIO()
        writer.write(out_buf)
        out_buf.seek(0)
    except ImportError:
        # Fallback: merge via concatenation into one buffer per-slip
        # Generate each slip separately and concatenate raw PDF bytes as ZIP
        import zipfile
        out_buf = io.BytesIO()
        with zipfile.ZipFile(out_buf, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
            for slip in payslips:
                single_buf = _build_payslip_pdf(dict(slip), dict(run))
                fname = f"slip_{slip.get('employee_code', 'EMP')}.pdf"
                zf.writestr(fname, single_buf.read())
        out_buf.seek(0)
        run_num = run.get("run_number", run_id[:8])
        return StreamingResponse(
            out_buf,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="payroll_{run_num}_slips.zip"'},
        )

    run_num = run.get("run_number", run_id[:8])
    fname = f"payroll_{run_num}_all_slips.pdf"
    return StreamingResponse(
        out_buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


# ── PAYSLIPS ──────────────────────────────────────────────────────────────────
@router.get("/payslips")
async def list_payslips(request: Request, run_id: Optional[str] = None, employee_id: Optional[str] = None):
    await require_auth(request)
    db = get_db()
    q = {}
    if run_id: q["run_id"] = run_id
    if employee_id: q["employee_id"] = employee_id
    rows = await db.rahaza_payslips.find(q, {"_id": 0}).sort("employee_code", 1).to_list(None)
    return serialize_doc(rows)


@router.get("/payslips/{pid}")
async def get_payslip(pid: str, request: Request):
    await require_auth(request)
    db = get_db()
    row = await db.rahaza_payslips.find_one({"id": pid}, {"_id": 0})
    if not row:
        raise HTTPException(404, "Payslip tidak ditemukan.")
    return serialize_doc(row)


@router.put("/payslips/{pid}")
async def update_payslip(pid: str, request: Request):
    """Update deductions & notes saja (untuk adjust manual). Hanya jika run masih draft."""
    user = await _require_hr(request)
    db = get_db()
    slip = await db.rahaza_payslips.find_one({"id": pid}, {"_id": 0})
    if not slip:
        raise HTTPException(404, "Payslip tidak ditemukan.")
    run = await db.rahaza_payroll_runs.find_one({"id": slip["run_id"]}, {"_id": 0})
    if not run:
        raise HTTPException(404, "Run induk tidak ditemukan.")
    if run.get("status") != "draft":
        raise HTTPException(400, "Run sudah di-finalize — slip tidak bisa diubah.")

    body = await request.json()
    deductions = body.get("deductions") or []
    norm_ded = []
    for d in deductions:
        label = (d.get("label") or "").strip()
        amount = float(d.get("amount") or 0)
        if not label or amount <= 0:
            continue
        norm_ded.append({"label": label, "amount": round(amount)})
    ded_total = sum(d["amount"] for d in norm_ded)
    gross = slip.get("gross_pay", 0)
    net = max(0, gross - ded_total)
    await db.rahaza_payslips.update_one({"id": pid}, {"$set": {
        "deductions": norm_ded,
        "deductions_total": ded_total,
        "net_pay": net,
        "notes": body.get("notes") or slip.get("notes", ""),
        "updated_at": _now(),
        "updated_by": user["id"],
        "updated_by_name": user.get("name", ""),
    }})
    out = await db.rahaza_payslips.find_one({"id": pid}, {"_id": 0})
    return serialize_doc(out)
