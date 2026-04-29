# 🏭 PT Rahaza ERP — Production User Flow Excellence Roadmap

> **Versi:** 1.0  
> **Tanggal:** 23 April 2026  
> **Scope:** Modul Produksi saja (skip Finance & AI untuk fase ini)  
> **Tujuan:** Memudahkan user flow di produksi — operator, supervisor, PPIC, manager — sehingga sistem benar-benar membantu pekerjaan harian, bukan sekadar tempat input data.

---

## 0. Filosofi & Prinsip

**Goal eksekutif:** Turunkan **friksi kerja per persona** sehingga setiap user "tahu apa yang harus dilakukan, kapan, dan bagaimana — tanpa harus tanya".

**Prinsip yang akan dipegang:**
- **P1 · Flow > Form** — kurangi jumlah klik untuk task harian (target 50% reduction).
- **P2 · Bulk > One-by-one** — operasi yang berulang harus bulk-able (mass-create, mass-assign).
- **P3 · Auto-suggest > Manual entry** — sistem isi default cerdas (target dari kapasitas+SAM, bukan tebakan).
- **P4 · Visual > Textual** — drag-drop, color-coded, photo reference.
- **P5 · Mobile-first di lantai** — operator pakai HP, semua form harus mobile-friendly.
- **P6 · Real-time feedback** — alert proaktif, jangan tunggu user inspect manual.

**Yang TIDAK akan dilakukan di scope ini:**
- ❌ Finance enhancement (Cash Flow indirect, Tax module, Budgeting) → Phase F4 nanti
- ❌ AI Layer (Phase 20C) → tunggu data lebih kaya
- ❌ Mobile PWA full offline → Phase 23 nanti
- ❌ WhatsApp Bot → Phase 23 nanti

---

## 1. Persona Pain-Point yang Akan Dibenahi

Berdasarkan audit, persona berikut masih punya gap besar **khusus di flow produksi**:

| Persona | Skor Saat Ini | Target | Pain Point Utama yang Tersisa |
|---|---|---|---|
| **Supervisor / Line Leader** | 3/5 | **4.5/5** | Bulk action belum ada, drag-drop assign belum, alert real-time belum, eskalasi otomatis belum |
| **PPIC / Planner** | 3/5 | **4.5/5** | Kapasitas vs demand view belum, SAM-based target belum, forecast belum, calendar belum |
| **Manager Produksi** | 3/5 | **4.5/5** | Pareto defect belum, FPY belum, machine downtime log belum, backlog risk view belum |
| **Operator Lantai** | 3.5/5 | **4.5/5** | Foto referensi belum, defect code belum, prioritas tidak jelas, take-home estimator belum |

---

## 2. Roadmap — 4 Phase Berurutan (Total ~10–12 minggu)

Saya susun **4 phase** yang masing-masing **1.5–3 minggu**, **incremental**, dan saling **build-on**. User bisa pilih jalan:
- **Jalur cepat**: Phase 21 saja (1.5–2 minggu)
- **Jalur lengkap**: Phase 21 → 22 → 23 → 24 (3 bulan)
- **Custom**: pilih subset items

---

## 🟢 Phase 21 — Operator Daily Flow (Quick Wins)
**Estimasi:** 1.5–2 minggu  
**Persona utama:** Operator Lantai  
**Filosofi:** Buat operator merasa sistem **membantu**, bukan **menambah pekerjaan**.

### 21.1 · Defect Code Master + QC v2 (3–4 hari)
**Masalah saat ini:** QC fail input via free-text notes → tidak terstandardisasi → analitik defect lemah.

**Yang dibangun:**
- Master data `rahaza_defect_codes` (15–20 kode standar knit garment):
  - `DC-HOLE` Lubang/Holes
  - `DC-BSTITCH` Broken Stitch
  - `DC-SKIPSTITCH` Skipped Stitch
  - `DC-COLOR` Salah Warna
  - `DC-DIRT` Kotor/Stain
  - `DC-SIZE` Size Out of Tolerance
  - `DC-FUZZ` Fuzzy/Pilling
  - `DC-LINKING` Cacat Linking
  - `DC-MISMATCH` Pattern Mismatch
  - dll (CRUD + soft-delete)
- Field baru di `wip_events` (saat QC fail): `defect_codes: [{code, qty, severity}]`
- UI input QC pakai **Shadcn MultiSelect** (replace free text), tetap bisa tambah notes.
- Backward compat: data lama yang notes-only tetap bisa dilihat.

### 21.2 · Today's Task Priority Order untuk Operator (1–2 hari)
**Masalah saat ini:** Operator buka `OperatorView`, tampil daftar assignment hari ini, tapi **urutan tidak jelas**.

**Yang dibangun:**
- Endpoint `/api/rahaza/operator/{employee_id}/today` return assignments yang sudah di-rank by:
  1. Priority WO (urgent > high > normal)
  2. Due date order terdekat
  3. Bundle yang sudah parsial (lanjut dulu) > bundle baru
- Frontend: badge "1️⃣ Kerjakan Dulu" pada item paling atas, "2️⃣", "3️⃣" dst.
- Tooltip: "kenapa ini didahulukan?" → "Order ini due 2 hari lagi"

### 21.3 · Photo Reference per Model (2–3 hari)
**Masalah saat ini:** Operator harus tanya leader / lihat sample fisik untuk model yang baru.

**Yang dibangun:**
- Field `photos: []` di `rahaza_models` (max 5 foto per model).
- Upload via `Master Data → Model Produk → Edit → Upload Foto` (drag-drop multi).
- Foto disimpan ke `/uploads/model-photos/<uuid>.jpg` (atau base64 di Mongo untuk simplicity).
- Operator View: thumbnail foto model di card assignment + tap untuk full-screen.
- API: `/api/rahaza/models/{id}/photos` (POST upload, GET list, DELETE).

### 21.4 · Take-Home Estimator (Borongan PCS) (1–2 hari)
**Masalah saat ini:** Operator borongan tidak tahu hari ini sudah dapat berapa rupiah.

**Yang dibangun:**
- Widget di Operator View pojok atas: "Estimasi Take-Home Hari Ini: **Rp 145.000** (29 pcs × Rp 5.000)"
- Real-time update saat operator submit qty.
- Hitung dari: `output_today × payroll_profile.base_rate` (kalau scheme=borongan_pcs).
- Bonus indicator: "Lebih 8 pcs dari target = bonus Rp 40.000"

### 21.5 · Explicit "Tandai Selesai" Button (1 hari)
**Masalah saat ini:** Tidak ada tombol "saya sudah selesaikan WO ini" eksplisit.

**Yang dibangun:**
- Tombol "Selesaikan Pekerjaan" di Operator View untuk tiap bundle/WO yang qty produced ≥ target.
- Confirmation modal: "Anda yakin? Bundle akan masuk ke proses selanjutnya."
- Backend update bundle status → `complete` + log event.

### 21.6 · Replace Native `<select>` di Form Produksi (2–3 hari)
**Masalah saat ini:** Form `RahazaOrders`, `RahazaBOM`, `RahazaWorkOrders`, `RahazaLineAssignments` masih pakai native `<select>` → search lambat & kurang aksesibel.

**Yang dibangun:**
- Replace dengan Shadcn `Select` / `Combobox` di 6+ modul produksi.
- Search-as-you-type, keyboard nav.

### Success Criteria Phase 21
- ✅ QC input punya defect code, semua kategori terstandardisasi.
- ✅ Operator buka view → tahu urutan kerjaan #1, #2, #3.
- ✅ Foto model bisa di-upload & dilihat operator.
- ✅ Operator borongan tahu take-home real-time.
- ✅ Form produksi pakai Shadcn (no native select).

---

## 🟡 Phase 22 — Supervisor Cockpit
**Estimasi:** 2.5–3 minggu  
**Persona utama:** Supervisor / Line Leader  
**Filosofi:** Sistem **menjaga punggung** supervisor, bukan minta dia jadi data entry.

### 22.1 · "My Line" Filter Mode (1 hari)
**Masalah saat ini:** Line Board tampil semua line. Leader harus scroll cari line-nya.

**Yang dibangun:**
- Setting di user profile: `default_line_ids: []`
- Toggle di Line Board: "Tampilkan: [Semua | Line Saya]"
- Auto-pilih saat login kalau user role=supervisor.

### 22.2 · Auto-Assign Template "Pakai Kemarin" (2 hari)
**Masalah saat ini:** Setiap pagi supervisor input ulang `LineAssignment` 1-by-1.

**Yang dibangun:**
- Endpoint `/api/rahaza/line-assignments/copy-from-yesterday`
- Tombol di `LineAssignmentsModule`: "📋 Salin Assignment Kemarin"
- Modal preview: tabel hasil → edit per row → confirm → bulk insert.
- Smart adjustment: kalau operator absen hari ini, auto-replace dengan suggestion.

### 22.3 · Bulk Material Issue Generator (2–3 hari)
**Masalah saat ini:** Material Issue dibuat 1-1 per WO. Capai 8-10 WO per hari = 8-10 form fill.

**Yang dibangun:**
- Endpoint `/api/rahaza/material-issues/bulk-draft-from-released-wos?date=...`
- UI: `MaterialIssueModule` → tombol "🚀 Draft MI Hari Ini"
- Sistem:
  1. Cari semua WO status=`released` belum punya MI aktif
  2. Hitung kebutuhan material dari BOM × qty WO
  3. Tampilkan preview: list WO + material aggregated
  4. Operator gudang konfirmasi → bulk create draft MIs
- Saat issue confirmed: stock decrement seperti biasa.

### 22.4 · Drag-Drop Re-assign di Line Board (3–4 hari)
**Masalah saat ini:** Line Board read-only. Re-assign harus buka form lain.

**Yang dibangun:**
- Drag bundle dari satu line ke line lain → auto-update `current_line_id` + log event.
- Drag dari satu proses ke proses berikutnya (manual override flow).
- Library: `dnd-kit` (lightweight, accessible).
- Konfirmasi modal kalau move backward (anti-mistake).

### 22.5 · Real-time "Line Behind Target" Alert (2–3 hari)
**Masalah saat ini:** Backend punya threshold (70%) tapi alert tidak push ke supervisor.

**Yang dibangun:**
- Background job per 15 menit: check tiap line yang assigned hari ini.
- Kalau `(actual / projected_pace) < 70%` → kirim notification ke `NotificationBell`.
- Toast popup di top-right: "⚠️ Line A behind 35% — klik untuk detail"
- Eskalasi tier: 30 menit no action → notif ke manager.

### 22.6 · Line Stop / Idle Reason Log (2 hari)
**Masalah saat ini:** Tidak ada log "kenapa line ini berhenti?" → analytics produktivitas lemah.

**Yang dibangun:**
- Modul baru `LineStopModule` (under Produksi → Monitoring).
- Form: line, start_time, end_time, reason_code (mesin rusak, listrik, material habis, briefing, dll), notes.
- Reason codes: master data sederhana (10–12 kode).
- Feed ke OEE Availability calculation (sudah ada hooks di Phase 20A).

### 22.7 · End-of-Shift Auto Summary PDF (3–4 hari)
**Masalah saat ini:** Supervisor harus bikin laporan harian manual.

**Yang dibangun:**
- Endpoint `/api/rahaza/reports/end-of-shift?date=...&line_id=...`
- Generate PDF dengan reportlab (sudah terinstal):
  - Header: tanggal, shift, line, supervisor
  - Table operator: nama, target, output, %, defect, downtime
  - KPI summary: total output, FPY, on-target ratio
  - Notes/issues hari ini
- Auto-generate jam 17:00 tiap hari → simpan ke `/api/files` + email/WA (kalau ada channel).
- UI: `ReportsModule → End-of-Shift History` (list PDF history).

### Success Criteria Phase 22
- ✅ Supervisor bisa lihat line-nya saja dengan 1 klik.
- ✅ Assignment hari ini bisa salin dari kemarin (1 tombol).
- ✅ MI bisa di-bulk-draft (1 tombol untuk semua WO released).
- ✅ Line Board mendukung drag-drop re-assign bundle.
- ✅ Alert real-time saat line behind target.
- ✅ Line stop dengan reason code tercatat.
- ✅ End-of-shift PDF auto-generate.

---

## 🟠 Phase 23 — PPIC Planning Suite
**Estimasi:** 3 minggu  
**Persona utama:** PPIC / Planner  
**Filosofi:** Beri planner **cockpit perencanaan** sehingga tidak balik ke Excel.

### 23.1 · Capacity vs Demand View (3–4 hari)
**Masalah saat ini:** Planner harus buka Excel sendiri untuk hitung kapasitas.

**Yang dibangun:**
- Modul baru `CapacityViewModule` (Production → Penjadwalan).
- Layout: tabel/grid 30 hari ke depan × per line.
- Per cell: `capacity_pcs` (dari line.capacity_per_hour × shift hours × workdays) vs `assigned_pcs` (dari APS schedule).
- Color: hijau (<70%), kuning (70-90%), merah (>90% over-capacity).
- Klik cell → list WO yang sudah di-schedule di line+tanggal tersebut.

### 23.2 · Material Reservation Pre-Check on WO Release (3–4 hari)
**Masalah saat ini:** Material baru di-cek saat MI confirm. Sudah telat.

**Yang dibangun:**
- Saat WO status mau berubah → `released`:
  - Hitung kebutuhan material (BOM × qty)
  - Cek `rahaza_material_stock` per lokasi
  - Kalau cukup → reserve qty (field `reserved_qty` di stock)
  - Kalau kurang → BLOCK release + tampilkan modal:
    - List material yang short
    - Saran: "Buat PO ke supplier X" / "Transfer dari Gedung B"
    - Override (force release dengan persetujuan supervisor)

### 23.3 · SAM Master + Line Balancing Calculator (3–4 hari)
**Masalah saat ini:** Target line di-input bebas, sering over/under-target.

**Yang dibangun:**
- Master data baru `rahaza_sam` (SAM = Standard Allowed Minute):
  - `model_id × process_id → minutes_per_pc`
- Calculator widget di `LineAssignment` form:
  - Input: model, size, jumlah operator, shift duration (default 480 menit)
  - Output: `target_pcs = (operators × 480) / SAM_per_pc × efficiency_factor (default 0.85)`
- Bisa override target manual, tapi saran tetap muncul.
- Endpoint `/api/rahaza/sam/calculate`

### 23.4 · Forecast Order Completion (2–3 hari)
**Masalah saat ini:** Tidak ada estimasi "Order X akan selesai tanggal berapa".

**Yang dibangun:**
- Setiap WO dihitung `forecast_completion_date`:
  - Linear: `(qty_remaining / avg_daily_output_in_last_7_days_for_this_line) + today`
- Setiap Order = `MAX(forecast_completion_date)` dari semua WO-nya.
- Dashboard tile baru di Order: badge "🔵 Forecast: 2026-05-12" (hijau if before due, merah if after).
- Order detail page: timeline visual order_date → today → forecast → due_date.

### 23.5 · Production Calendar (Libur & Exception) (2 hari)
**Masalah saat ini:** APS Gantt schedule WO di hari Minggu / libur nasional.

**Yang dibangun:**
- Master data `rahaza_calendar_exceptions`:
  - `date, type (holiday|maintenance|special_shift), description, affected_lines: []`
- Auto-seed libur nasional Indonesia (tahun berjalan).
- APS engine: skip exception days saat scheduling.
- View: kalender bulanan dengan highlight (red=libur, kuning=maintenance).

### 23.6 · Drag-Drop Re-prioritize Queue per Line (2 hari)
**Masalah saat ini:** Field `priority` ada (normal/high/urgent), tapi tidak auto-reorder.

**Yang dibangun:**
- Production Queue view per line: list WO scheduled for next 7 days.
- Drag-drop reorder → update `sequence_num` field.
- Operator View ambil dari sequence_num order.

### Success Criteria Phase 23
- ✅ Planner lihat kapasitas vs demand 30 hari ke depan dengan color-coded grid.
- ✅ WO release di-block kalau material short (dengan saran).
- ✅ Target line auto-calculated dari SAM master.
- ✅ Forecast completion date tampil per WO/Order.
- ✅ Calendar exception respected oleh APS.
- ✅ Queue line bisa di-reorder dengan drag-drop.

---

## 🔴 Phase 24 — Quality & Performance Metrics
**Estimasi:** 2.5–3 minggu  
**Persona utama:** Manager Produksi, QC Head  
**Filosofi:** Beri manager **drill-down decision tools**, bukan sekadar dashboard pasif.

### 24.1 · Defect Pareto Dashboard (2–3 hari)
**Prerequisite:** Phase 21.1 (Defect Code Master) sudah selesai.

**Yang dibangun:**
- Modul baru `DefectParetoModule` (Production → Monitoring).
- Bar chart: top-15 defect kategori, sorted by frequency.
- Line chart cumulative %: "80% defect berasal dari 3 kategori teratas".
- Filter: tanggal range, line, model, operator, shift.
- Drill-down: klik bar → list bundle/event yang punya defect tersebut.
- Trend mini-chart per defect: 7d / 30d.

### 24.2 · First-Pass-Yield (FPY) Dashboard (2–3 hari)
**Yang dibangun:**
- Definition: `FPY = (qty_pass_first_inspection / qty_inspected_total)`
- Dashboard tile: FPY hari ini, week-to-date, month-to-date.
- Breakdown:
  - FPY per Line (bar chart)
  - FPY per Model (top-10 bar)
  - FPY per Operator (leaderboard)
  - FPY per Shift (S1 vs S2)
- Sparkline trend 30 hari per dimensi.
- Alert: "FPY Line C turun 8% minggu ini" (auto-detect anomaly).

### 24.3 · Machine Downtime Log + OEE Availability Deep (3–4 hari)
**Yang dibangun:**
- Master `rahaza_downtime_reasons` (10–12 kode: breakdown, planned maintenance, no operator, no material, changeover, dll).
- Modul `MachineDowntimeModule`:
  - Form input: machine, start_at, end_at, reason_code, notes
  - Calculator duration auto.
  - Filter & list view per machine.
- Feed ke OEE Availability: `Availability = (planned_runtime - downtime) / planned_runtime`
- Top-5 mesin downtime, top-5 reason — di OEE Dashboard.

### 24.4 · Production Backlog with Due-Risk View (2–3 hari)
**Yang dibangun:**
- Modul baru `ProductionBacklogModule` (Production → Eksekusi).
- List semua WO belum selesai (status≠completed).
- Sort by `due_risk_score`:
  - `due_risk = max(0, (forecast_completion_date - due_date).days)`
  - `due_risk = 0` → on-track (hijau)
  - `due_risk = 1-3` → at-risk (kuning)
  - `due_risk > 3` → critical (merah)
- 1-click "Eskalasi ke PPIC" → kirim notification dengan list affected WOs.
- Bulk action: "Re-prioritize selected", "Re-assign to faster line".

### 24.5 · Period Comparison Dashboard (2 hari)
**Yang dibangun:**
- Toggle di Production Dashboard: "Periode: Hari Ini | This Week | Compare WoW | MoM"
- Saat compare mode aktif: tampilkan delta % di setiap KPI dengan icon 📈/📉.
- Available metrics: Output, FPY, Downtime, On-Time Rate.

### Success Criteria Phase 24
- ✅ Manager bisa identifikasi 3 defect kategori penyumbang 80% issue.
- ✅ FPY visible per line/model/operator dengan trend.
- ✅ Machine downtime tercatat dengan reason → OEE Availability akurat.
- ✅ Backlog view sortir by due-risk → eskalasi 1-klik.
- ✅ Period-over-period comparison di dashboard.

---

## 3. Summary Table

| Phase | Estimasi | Items | Persona Utama | Pain Points yang Dibenahi |
|---|---|---|---|---|
| **21 — Operator Daily Flow** | 1.5–2 minggu | 6 items | Operator | Defect code, prioritas tugas, foto model, take-home, mark-done, form polish |
| **22 — Supervisor Cockpit** | 2.5–3 minggu | 7 items | Supervisor | My-line filter, auto-assign, bulk MI, drag-drop, alert real-time, line stop log, EOS report |
| **23 — PPIC Planning Suite** | 3 minggu | 6 items | PPIC | Capacity view, material reservation, SAM, forecast, calendar, queue reorder |
| **24 — Quality & Metrics** | 2.5–3 minggu | 5 items | Manager/QC | Pareto, FPY, downtime, backlog risk, period compare |
| **TOTAL** | **9.5–11 minggu** | **24 items** | All production | Significant flow improvement |

---

## 4. Pilihan Strategi Eksekusi

### 🥇 **Strategi A — Sequential (Direkomendasikan)**
Phase 21 → 22 → 23 → 24 berurutan. Setiap phase di-test & di-confirm user sebelum lanjut.

**Pro:** Aman, ada checkpoint per phase, bisa stop kapan saja kalau ROI sudah tercapai.
**Con:** Total 10+ minggu. User harus sabar.

### 🥈 **Strategi B — Pick Top 3**
Pilih 3 phase paling impactful saja:
- Phase 22 (Supervisor) — persona paling kurang dilayani
- Phase 23 (PPIC) — modul yang efectively non-existent
- Phase 24 (Manager Metrics) — decision support gap

Total: ~8–9 minggu, skip Phase 21 (operator polish) — yang sudah decent.

### 🥉 **Strategi C — Quick Hit**
Hanya Phase 21 (Operator Daily Flow) — 2 minggu — focus pada friksi operator harian.

**Pro:** Cepat. Visible dampak ke operator dalam 1-2 minggu.
**Con:** Supervisor/PPIC masih harus tunggu.

### 🎯 **Strategi D — Custom Combo (User Pilih)**
User sebut item-item spesifik dari 24 items, saya bundling. Contoh: "21.1 + 22.3 + 22.7 + 24.1 + 24.4" → ~3 minggu.

---

## 5. Rekomendasi Pribadi

**Saya rekomendasikan Strategi A (Sequential) DENGAN urutan modifikasi:**

```
Phase 22 (Supervisor) → Phase 21 (Operator) → Phase 23 (PPIC) → Phase 24 (Metrics)
   ↑ start dengan persona paling kurang dilayani
```

**Alasan:**
1. **Supervisor adalah leverage point** — kalau supervisor terbantu, mereka akan "menjual" sistem ke operator & PPIC. Mereka ada di tengah.
2. **Operator polish** lebih impactful kalau supervisor flow sudah mulus (e.g., Phase 22.2 auto-assign feeds Phase 21.2 priority order).
3. **PPIC** butuh data history yang stabil, datang setelah operasional lancar.
4. **Metrics** datang terakhir karena base data harus rapih dulu.

**Jadwal tentative:**
- **Minggu 1–3:** Phase 22 Supervisor Cockpit
- **Minggu 4–5:** Phase 21 Operator Daily Flow
- **Minggu 6–8:** Phase 23 PPIC Planning Suite
- **Minggu 9–11:** Phase 24 Quality & Metrics

---

## 6. Yang Perlu User Putuskan

1. **Pilih Strategi**: A (Sequential), B (Top 3), C (Quick Hit), atau D (Custom Combo)?
2. **Kalau A**: Pakai urutan default (21→22→23→24) atau urutan rekomendasi saya (22→21→23→24)?
3. **Kalau D**: Sebut item spesifik yang mau (gunakan kode 21.1, 22.3, dll).
4. **Sprint length**: 1 minggu, 2 minggu, atau 3 minggu per phase? (default: 2 minggu, ada checkpoint user).
5. **Testing**: Setiap phase testing-agent atau hanya manual user-test?

---

*Roadmap ini fokus produksi saja. Finance enhancement (F4) & AI Layer (20C) akan dipertimbangkan setelah produksi solid.*
