# 🗺️ PT Rahaza ERP — Development Roadmap Lanjutan

> **Versi:** 2.0  
> **Tanggal:** 23 April 2026  
> **Basis:** Production Flow Audit (`PRODUCTION_FLOW_AUDIT.md`) + status implementasi saat ini (Phase 15–F3 selesai).  
> **Tujuan dokumen ini:** Memberi peta jalan jelas tentang apa yang sudah dikerjakan, apa yang masih gap terhadap audit, dan opsi prioritas fase berikutnya.

---

## 1. Retrospektif — Audit vs Implementasi Saat Ini

Audit awal (April 2026) memberi **30 rekomendasi** dan skor awal **2.7/5**. Berikut status per-rekomendasi:

### 🚀 Quick Wins (10 items)

| # | Rekomendasi | Status | Phase |
|---|---|---|---|
| 1 | Empty-state CTA | ✅ Done | 16 |
| 2 | Setup Wizard | ✅ Done | 16 |
| 3 | Next-Action Widget | ✅ Done | 16 |
| 4 | Tooltip Kontekstual di Form | ⚠️ Partial (glossary static) | — |
| 5 | Sort & Filter default | ⚠️ Partial | — |
| 6 | Command Palette actions | ✅ Done (Cmd+K) | 16 |
| 7 | Bulk Material Issue | ❌ **BELUM** | — |
| 8 | Auto-assign template | ❌ **BELUM** | — |
| 9 | Toast alert on major events | ⚠️ NotificationBell saja | 18A |
| 10 | Defect Code dropdown | ❌ **BELUM** | — |

### 🎯 Strategic (15 items)

| # | Rekomendasi | Status | Phase |
|---|---|---|---|
| 11 | Bundle/Batch Tracking | ✅ Done | 17 |
| 12 | Barcode/QR Scanner | ✅ Done | 17 |
| 13 | Capacity & Scheduling Board (Gantt) | ✅ Done | 19 |
| 14 | Line Balancing (SAM) | ❌ **BELUM** | — |
| 15 | Material Reservation on WO release | ❌ **BELUM** | — |
| 16 | Andon Panel | ✅ Done | 18B |
| 17 | Shop Floor TV Mode | ✅ Done | 18C |
| 18 | Defect Pareto Dashboard | ❌ **BELUM** | — |
| 19 | First-Pass-Yield (FPY) | ❌ **BELUM** | — |
| 20 | OEE Dashboard | ✅ Done | 20A |
| 21 | Production Backlog view | ❌ **BELUM** | — |
| 22 | Forecast "Kapan order selesai?" | ❌ **BELUM** | — |
| 23 | Closed-loop Rework Enforcement | ✅ Done | 20B |
| 24 | Machine Breakdown & Downtime Log | ❌ **BELUM** | — |
| 25 | SOP Inline | ✅ Done | 18D |

### 🔧 Fill Gaps (5 items)

| # | Rekomendasi | Status | Phase |
|---|---|---|---|
| 26 | Replace native `<select>` dengan Shadcn | ⚠️ Partial | — |
| 27 | End-of-Shift Report auto PDF | ❌ **BELUM** | — |
| 28 | Production Calendar (libur, exception) | ❌ **BELUM** | — |
| 29 | Mobile PWA install | ❌ **BELUM** | — |
| 30 | WhatsApp Bot | ❌ **BELUM** | — |

### 🤖 AI Layer

| Item | Status | Phase |
|---|---|---|
| Natural-language report | ❌ **BELUM** | 20C (deferred) |
| Smart search (NL → filter) | ❌ **BELUM** | 20C |
| Root-cause assistant | ❌ **BELUM** | 20C |
| Predictive delay | ❌ **BELUM** | 20C |
| Chatbot supervisor | ❌ **BELUM** | 20C |

### Gap Industri Best-in-Class yang Belum Ditutup

| Item | Status |
|---|---|
| Style Master (foto, tech-pack) | ⚠️ Hanya code+name |
| BOM versioning + costing link | ⚠️ BOM ada, versioning belum |
| End-line QC + AQL sampling | ❌ |
| FG put-away by carton | ❌ |
| Shipment pack list + carton manifest | ❌ |
| Shift handover checklist | ❌ |

---

## 2. Skor Kesehatan Saat Ini (Estimasi)

| Dimensi | Skor Awal | Skor Saat Ini | Catatan |
|---|---|---|---|
| Data model & API coverage | 4/5 | **4/5** | Stabil, tidak perlu refactor |
| End-to-end functional | 4/5 | **4.5/5** | Bundle tracking + APS naik 0.5 |
| Guidance / next-action | 2/5 | **4/5** | Setup wizard + next-action widget |
| Decision support / analytics | 2/5 | **3.5/5** | OEE + APS naik, masih butuh Pareto/FPY/Forecast |
| Ease operator | 3/5 | **3.5/5** | SOP inline + QR scan naik |
| Ease supervisor/PPIC | 2/5 | **3/5** | APS Gantt + Line Board naik, masih butuh bulk-action/template |
| Proactive communication | 2/5 | **4/5** | Alert Bus + Andon + TV + Notifications |
| Traceability / genealogy | 2/5 | **4/5** | Bundle + closed-loop rework |
| Accessibility | 3/5 | **3/5** | Belum ada upgrade spesifik |

**Skor rata-rata saat ini: ~3.7/5** (naik dari 2.7/5). Masih butuh **0.8 poin** untuk mencapai "great" (4.5/5).

---

## 3. Gap yang Tersisa — Pengelompokan Tematik

### 🧩 Tema A — **Decision Support & Quality Metrics**
> *"Manager bisa review, tapi belum bisa decide."*

Items: 10 (Defect Code), 18 (Pareto), 19 (FPY), 21 (Backlog), 22 (Forecast), 24 (Machine Downtime)

### 🧩 Tema B — **Supervisor/PPIC Power Tools**
> *"Persona supervisor/PPIC paling kurang dilayani."*

Items: 7 (Bulk MI), 8 (Auto-assign template), 14 (Line Balancing/SAM), 15 (Material Reservation), 28 (Calendar)

### 🧩 Tema C — **AI-Assisted Intelligence** (Phase 20C)
> *"Sistem seharusnya belajar dari pola, bukan cuma kumpulkan data."*

AI layer: NL report, smart search, root-cause, predictive delay, chatbot

### 🧩 Tema D — **Channels & Mobility**
> *"Data harus sampai ke HP pekerja, tidak hanya dashboard kantor."*

Items: 27 (End-of-shift Report), 29 (PWA), 30 (WA Bot)

### 🧩 Tema E — **Buyer-Compliance & Tech Pack**
> *"B2B buyer internasional butuh spec sheet, photo reference, size chart."*

Items: Style Master, BOM versioning, AQL sampling, Pack list carton

### 🧩 Tema F — **Finance Depth**
> *"Akuntansi dasar sudah lengkap, tinggal enhancement."*

Items: Cash Flow indirect method, Tax module (PPN/PPh multi-rate), Multi-currency, Budgeting & variance analysis

### 🧩 Tema G — **UI Polish & Accessibility**
> *"Form lama masih pakai native `<select>`, kurang aksesibel."*

Items: 4 (tooltip kontekstual), 5 (smart default filter), 26 (Shadcn Select replacement)

---

## 4. Opsi Prioritas — Pilih Salah Satu untuk Phase Berikutnya

### 📌 **Opsi 1 — Phase 21: Decision Support & Quality Metrics** (Tema A)
**Estimasi:** 3–4 minggu
**Persona utama:** Manager Produksi, QC Head

#### Yang akan dibangun:
- **21A · Defect Code Master + QC v2**
  - Master data defect categories (15–20 kode standar knit: holes, broken-stitch, wrong-color, dirt, size-out, dll)
  - QC event di-extend dengan `defect_code_id[]` array
  - Modul input QC pakai dropdown Shadcn, bukan free-text notes
- **21B · Pareto Analysis Dashboard**
  - Top-10 defect kategori (bar chart)
  - Drill-down: per line / per operator / per model / per shift
  - Trend 7d / 30d / 90d
- **21C · First-Pass-Yield (FPY) Dashboard**
  - FPY per line / per model / per operator
  - Sparkline trend
  - Target vs actual
- **21D · Machine Downtime Log**
  - Event `machine_stop` dengan reason_code + duration + operator_id
  - Feeding ke OEE Availability
  - Dashboard breakdown: top-5 mesin downtime, top-5 reason
- **21E · Production Backlog View**
  - List WO belum selesai, sort by due-risk
  - Color-coded: hijau (on-track), kuning (at-risk), merah (overdue)
  - 1-click "Escalate" → notif ke PPIC
- **21F · Forecast Order Completion**
  - Linear projection: `(qty_remaining / avg_daily_output_per_line) + today`
  - Alert kalau melewati due_date
  - Displayed di Order detail + Backlog view

**Impact:** Skor "Decision Support" naik dari 3.5 → 4.5/5. Manager akhirnya bisa "decide" bukan sekadar "review".

---

### 📌 **Opsi 2 — Phase 22: Supervisor & PPIC Power Tools** (Tema B)
**Estimasi:** 3–4 minggu
**Persona utama:** Supervisor Lini, PPIC/Planner

#### Yang akan dibangun:
- **22A · Bulk Material Issue Generator**
  - "1-klik Draft MI semua WO released hari ini"
  - Preview material kebutuhan → approve batch → auto-create MI
- **22B · Auto-assign Template**
  - "Pakai assignment kemarin sebagai template hari ini"
  - Copy & bulk-edit mode
- **22C · Line Balancing (SAM-based)**
  - Master data `SAM` (Standard Allowed Minute) per `model × proses`
  - Kalkulator: `target_qty = line_operators × 60 × 480 / SAM` (untuk shift 8 jam)
  - Widget saran di form assignment
- **22D · Material Reservation pada WO Release**
  - Saat WO → `released`, cek stok BOM × qty
  - Kalau kurang: block + saran (PO mana, transfer lokasi mana, alternatif material)
  - Reserved stock field di `rahaza_material_stock`
- **22E · Production Calendar**
  - Master data hari libur nasional + custom exception (cuti massal, maintenance day)
  - APS Gantt respect calendar (tidak schedule di libur)
- **22F · Shift Handover Checklist**
  - End-of-shift: supervisor centang checklist (WIP count, mesin status, safety)
  - Otomatis kirim ringkasan ke shift berikutnya

**Impact:** Skor "Ease Supervisor/PPIC" naik dari 3 → 4.5/5. Persona yang paling kurang dilayani dapat tools yang layak.

---

### 📌 **Opsi 3 — Phase 20C: AI Layer** (Tema C)
**Estimasi:** 2–3 minggu (sekarang sudah siap karena data 3 bulan sudah ter-seed)
**Persona utama:** Manager, Supervisor, Owner

#### Prerequisite ✅
- Data historis 3 bulan sudah ada (seed).
- Finance sudah terintegrasi → context AI bisa kaya.

#### Integration yang perlu user konfirmasi:
- Provider LLM: **OpenAI GPT (GPT-5)** / **Gemini 2.5** / **Claude Sonnet 4.5** → pakai **Emergent Universal Key**

#### Yang akan dibangun:
- **20C.1 · Natural-Language Daily Report**
  - Endpoint `/api/rahaza/ai/daily-summary`
  - Output: ringkasan bahasa natural Indonesia ("Hari ini output 2.300 pcs, turun 12% dari kemarin karena...")
  - Jadwal: auto-generate jam 17:00 + kirim ke email/WA
- **20C.2 · Smart Search v2 (Natural Language)**
  - "order yang terlambat minggu ini untuk customer PT Matahari" → auto-filter
  - "WO terbesar bulan Maret" → hasil
  - Pakai LLM untuk parse intent + translate ke MongoDB query
- **20C.3 · Root-Cause Assistant**
  - "Kenapa QC fail rate tinggi hari ini di line 5?" 
  - LLM baca data defect + operator + shift → jawab dengan kausal analysis
- **20C.4 · Predictive Delay Warning**
  - Setiap WO dihitung prob delay (combo linear forecast + LLM context)
  - Alert proaktif "Order-0005 berisiko delay 2 hari karena line C kapasitas turun"
- **20C.5 · Chatbot Supervisor**
  - Floating chat di bottom-right
  - Q: "berapa output line 3 hari ini?" → A: "Line B-Rajut Reguler hari ini 285 pcs (target 300, 95%)."

**Impact:** Sistem berpindah dari "system-of-guidance" → "system-of-intelligence". Skor "Decision Support" loncat ke 5/5.

**Biaya:** Emergent LLM Key usage ~$10-30/bulan (tergantung volume).

---

### 📌 **Opsi 4 — Phase 23: Mobility & Channels** (Tema D)
**Estimasi:** 2–3 minggu
**Persona utama:** Operator Lantai, Supervisor (on-the-go)

#### Yang akan dibangun:
- **23A · Progressive Web App (PWA)**
  - Manifest.json + service worker
  - Operator bisa install di HP sebagai ikon native
  - Offline cache untuk Operator View (submit queued kalau offline)
- **23B · End-of-Shift Auto Report**
  - PDF auto-generate (line, operator, target, output, efisiensi, defect)
  - Kirim ke email supervisor + leader
- **23C · WhatsApp Bot (Read-Only Dulu)**
  - Integrasi dengan WA Business API atau Twilio
  - Command:
    - `/prod hari ini` → ringkasan output & KPI
    - `/line 3` → status line tertentu
    - `/alert` → active alerts saat ini
  - Supervisor bisa cek info tanpa buka aplikasi

**Impact:** Jangkauan ERP meluas ke mobile & chat. Adoption naik karena friction turun.

**Biaya:** WhatsApp Business API ~$5-15/bulan (Twilio) + $0.005 per message outbound.

---

### 📌 **Opsi 5 — Phase 24: Buyer Compliance & Tech Pack** (Tema E)
**Estimasi:** 4–5 minggu
**Persona utama:** Sales, Merchandiser, Export Manager

#### Yang akan dibangun:
- **24A · Style Master 2.0**
  - Model + foto (upload multi-photo per model)
  - Tech pack PDF attachment
  - Size chart table (measurement per size)
- **24B · BOM Versioning**
  - Snapshot BOM setiap ada perubahan
  - "Changelog" BOM → trace material replacement history
  - Costing link: BOM version × material cost saat itu = baseline HPP
- **24C · AQL Sampling Tool**
  - AQL level 1.0 / 1.5 / 2.5 configurable
  - Auto-hitung `sample_size` dari `lot_size` (MIL-STD-105E tabel)
  - QC inspector input major/minor/critical → pass/reject lot
- **24D · Carton & Pack List**
  - Pack items ke carton (barcode carton)
  - Generate pack list PDF (carton × items × qty)
  - Export ke format buyer (Macy's, H&M format)
- **24E · FG Put-Away by Carton**
  - Multi-zone FG warehouse
  - Lokasi per carton (bin aisle-rack-shelf)

**Impact:** Siap ekspor ke brand international. Compliance Macy's/H&M/Walmart.

---

### 📌 **Opsi 6 — Phase F4: Advanced Finance** (Tema F)
**Estimasi:** 2–3 minggu
**Persona utama:** Controller, Finance Manager

#### Yang akan dibangun:
- **F4.1 · Cash Flow Indirect Method (PSAK Standard)**
  - Saat ini Direct Method. Tambah Indirect (Net Income + adjustments non-cash)
  - Required untuk laporan resmi PSAK
- **F4.2 · Tax Module**
  - PPN multi-rate (11% standard, 0% ekspor, 1.1% PPN atas DP)
  - PPh 21 calculator (PTKP per tahun, progresif, BPJS integration)
  - PPh 22 & 23 tracking (witholding tax)
  - Laporan SPT Masa siap cetak
- **F4.3 · Budgeting & Variance Analysis**
  - Master budget per cost center × period
  - Actual vs Budget dashboard
  - Variance report (favorable/unfavorable)
- **F4.4 · Multi-Currency (Basic)**
  - Master exchange rate per tanggal
  - AR/AP bisa di mata uang USD/SGD
  - FX gain/loss auto-post saat payment

**Impact:** Finance naik dari "lengkap" → "professional-grade" siap audit eksternal.

---

### 📌 **Opsi 7 — UI Polish Menyeluruh** (Tema G)
**Estimasi:** 2 minggu
**Persona utama:** Semua

#### Yang akan dibangun:
- Replace semua native `<select>` dengan Shadcn `Select` / `Combobox` (10+ modul)
- Inline tooltip `?` icon di tiap field penting (+50 tooltips)
- Smart default filter (WO default: not-completed, sort by due_date asc)
- Keyboard shortcut per modul (? untuk shortcut list)
- Accessibility audit (ARIA labels, focus order, screen reader)
- Mobile responsive audit (1080p down to 360px)

**Impact:** Skor "Accessibility" naik 3 → 4.5/5. Adoption enterprise-grade.

---

## 5. Rekomendasi Prioritas

Berdasarkan ROI (Return on Investment) dan persona-gap terbesar:

### 🥇 **Opsi 1 (Phase 21: Decision Support)** — PRIORITY PALING TINGGI
Alasan:
- Skor "Decision Support" masih yang paling rendah (3.5/5) setelah Phase UI kemarin.
- Data sudah kaya (3 bulan seed) — langsung bisa dipakai untuk analytics.
- Defect code + Pareto + FPY + Downtime adalah **kebutuhan wajib** untuk pabrik knit serius.
- Manager & QC Head = decision maker utama, mereka butuh tools ini untuk **ambil keputusan**, bukan sekadar laporan.

### 🥈 **Opsi 3 (Phase 20C: AI Layer)** — QUICK WIN BESAR
Alasan:
- Prerequisite sudah terpenuhi (data 3 bulan + finance terintegrasi).
- Dengan Emergent LLM Key, cost rendah, impact tinggi.
- Natural language report + predictive delay = **game changer** persepsi "pintar"-nya sistem.
- Hanya 2-3 minggu.

### 🥉 **Opsi 2 (Phase 22: Supervisor Tools)**
Alasan:
- Supervisor masih persona paling kurang dilayani.
- Bulk MI + Auto-assign template = save 1-2 jam per supervisor per hari.
- Material reservation = cegah "WO released tapi material kurang" scenario.

### 🏅 **Kombo Rekomendasi: Phase 21 + 20C**
- **Minggu 1–3**: Phase 21 (Defect, Pareto, FPY, Downtime, Backlog, Forecast)
- **Minggu 4–6**: Phase 20C (AI Layer)
- Total: 6 minggu → skor kesehatan loncat dari 3.7 → ~4.5/5

---

## 6. Catatan Non-Teknis

- **Testing**: Setiap phase wajib call `testing_agent` setelah selesai.
- **Dokumentasi**: Update `USE_CASES.md` setiap phase selesai.
- **Rollback**: Setiap phase harus additive (tidak break existing features).
- **Data migration**: Saat ini seed deterministic, bisa di-reset kapanpun via `/api/rahaza/admin/reset-and-seed`.
- **User training**: Setelah Phase 21 selesai, tim Manager perlu training 30 menit cara baca Pareto/FPY.
- **Periodic review**: Setiap 2 phase selesai, re-score health index audit ulang.

---

## 7. Yang Harus User Putuskan Sekarang

1. **Pilih 1 opsi di atas** (atau kombinasi).
2. **Kalau pilih Phase 20C (AI)**: konfirmasi provider LLM (OpenAI GPT-5 / Gemini 2.5 / Claude 4.5).
3. **Konfirmasi timeline**: Sprint 2 minggu vs 4 minggu?
4. **Integrasi eksternal**: Kalau pilih Phase 23 WhatsApp → konfirmasi pakai Twilio atau WA Business API langsung?

---

*Dokumen ini akan di-update setiap phase selesai. Referensi utama:
- `/app/docs/PRODUCTION_FLOW_AUDIT.md` — audit awal
- `/app/docs/PRODUCTION_GUIDED_SYSTEM_ROADMAP.md` — roadmap asli
- `/app/docs/USE_CASES.md` — use case current-state
- `/app/plan.md` — live tracking plan*
