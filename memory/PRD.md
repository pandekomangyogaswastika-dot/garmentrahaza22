# PRD — PT Rahaza ERP (Garment Manufacturing System)

**Last Updated**: 2026-04-29
**Version**: Sprint Bugfix — Warehouse Audit (29 April 2026)

---

## Problem Statement
Membangun sistem ERP terpadu untuk PT Rahaza Global Indonesia — pabrik garment rajut. Sistem mencakup 5 portal utama: Manajemen, Produksi, Gudang, Keuangan, dan SDM.

---

## Architecture
- **Frontend**: React 18 + CRACO + Tailwind + Shadcn/ui
- **Backend**: FastAPI (Python 3.11) + Motor async MongoDB
- **Database**: MongoDB (local `test_database`)
- **Auth**: JWT (HS256), bcrypt password hashing
- **Storage**: Emergent Object Storage (via EMERGENT_LLM_KEY)
- **PDF**: ReportLab (LKP, End-of-Shift)
- **Async images**: aiohttp (production photos in LKP PDF)
- **Deployment**: Supervisor-managed, port 3000 (FE) + 8001 (BE)

---

## User Personas
- **Admin / Superadmin**: Full access, all portals
- **Supervisor**: Produksi + SDM, shift handover, LKP management
- **Operator**: Self-service portal
- **Finance Staff**: Keuangan portal
- **Warehouse Staff**: Gudang portal

---

## Core Requirements

### 5 Portals:
1. **Manajemen**: Dashboard, Style Master, Order Management, Analytics, **Panduan Penggunaan ERP**
2. **Produksi**: Work Orders, Bundles, APS Gantt, Line Assignments, Bulk MI, LKP, SOP, BOM, Shift Handover (+ End-of-Shift PDF), Material Reservation, Production Calendar, Line Balancing, Rework Board, OEE Dashboard
3. **Gudang**: Materials, Inventory, Purchase Orders, Receiving, Putaway, Stockopname, Material Reservation
4. **Keuangan**: CoA, Journal, Payroll, Finance Reports
5. **SDM**: Employees, Attendance, HR Reports

---

## What's Been Implemented

### Sprint 1 (Base Foundation)
- Auth system (JWT + bcrypt), user management, 5-portal structure
- Master data, Work Orders CRUD, Bundle generation/tracking
- Material management, Inventory (FIFO), Dashboard, Employee/Attendance

### Sprint 2 (Production Depth)
- APS Gantt scheduler, BOM, SOP management
- LKP: PDF generation, versioning, audit trail, photo upload, security hardening
- Rework Board, defect codes
- Finance: CoA, Journal, Payroll
- Warehouse: PO, Receiving, Put-Away, Stockopname

### Sprint 22 (Supervisor Power Tools) — 2026-04
- Bulk MI Generator, Auto-assign Template, Line Balancing SAM-based

### Sprint 23 — 2026-04
- APS Gantt + Line Balance integration, SOP SAM/Target fields
- Health/Metrics/Docs endpoints

### Sprint 3.x (HR + Inventory Depth) — 2026-04
- HR Reports + Excel export, Accessory module, Payroll Validation, Low Stock indicators

### Sprint 24 (Phase 22B) — 2026-04-28
- Demo Seed Data, LKP Bulk Print, Shift Handover frontend, Material Reservation UI
- Production Calendar, PWA manifest+sw, Admin material-reservation list

### Sprint 25 (P1/P2 Backlog) — 2026-04-29
- WO Release auto-reservation
- APS Gantt + Production Calendar holiday overlay
- Shift Handover sign-off flow
- Service Worker (full PWA)
- OEE Dashboard

### Sprint 26 (P0/P2 Final) — 2026-04-29
- **End-of-Shift PDF Report**: `utils/shift_report_pdf.py` + GET `/api/rahaza/shift-handovers/{id}/pdf`
- **LKP Foto Otomatis**: `utils/lkp_pdf.py` Section L "FOTO PRODUKSI & QC" rendered from `rahaza_lkp_photos`. Async fetch via aiohttp + Emergent Storage. Cache invalidated by `pdf_stale` flag on photo upload (regen+re-cache).
- **Panduan Penggunaan ERP**: `RahazaUserGuideModule.jsx` (707 lines) — search bar, 8 test scenarios (S1–S8 incl. defect→rework, mesin breakdown, shift malam, hari libur, etc.), 5 portal sections w/ accordion, Test Scenarios & Use Cases, Tips/FAQ/Troubleshooting. Routed via `mgmt-help` (replaces legacy HelpGuideModule).
- **Frontend Shift PDF download**: `RahazaShiftHandoverModule.jsx` `downloadHandoverPdf` (Bearer auth via fetch+blob, replaces broken `<a href>`)

### Sprint 27 — User Guide Visual Refresh — 2026-04-29
- **Refactor Panduan Penggunaan menjadi rich-visual** (mengganti markdown text-only):
  - `userGuide/guideData.js` — structured data (PORTAL_META, OVERVIEW, PORTALS_GUIDE, SCENARIOS dengan **prerequisite eksplisit per skenario**, TIPS).
  - `userGuide/UserGuideContent.jsx` — visual layout: sidebar tabs + content area, search global, color-coded portal chips, difficulty badges (Pemula/Menengah/Lanjut), estimasi waktu, persona indicator.
  - **Skenario** dirender sebagai card detail dengan: header gradient, **Pre-Requisite box prominent (numbered list)**, langkah-langkah dengan portal-colored numbered circles + connecting lines + portal chips per step, expected results card.
  - **Per-portal menus** sebagai card grid dengan: icon, breadcrumb path (font-mono), bullet checklist, callout tips/warning.
  - `userGuide/UserGuideDialog.jsx` — modal full-screen wrapper (max-w-6xl) untuk dipakai di mana saja.
  - `RahazaUserGuideModule.jsx` (page wrapper for `mgmt-help`) — refactored ke ~30 lines, render `UserGuideContent`.
- **Tombol "Panduan Penggunaan" di PortalSelector top-bar** — sejajar dengan ThemeToggle & "Keluar". Klik buka `UserGuideDialog`. data-testid: `portal-selector-guide-btn`.
- **Lokasi dual**: tombol global di Portal Selector (untuk semua user) + page module via Manajemen › Sistem › Panduan (mgmt-help).

### Sprint 28 — Module Help System (Drawer + Tour + Screenshots) — 2026-04-29
- **Per-modul Help Drawer + Interactive Tour + Real Screenshots** untuk semua 16 modul Portal Produksi:
  - `userGuide/moduleHelpData.js` — konten help per `moduleId` (purpose, sections, buttons + icons + "kapan dipakai", tips, warnings, related scenarios, **tour steps**).
  - `userGuide/Illustrations.jsx` — 3 SVG diagram konsep abstrak: **WO Flow** (Draft→Released→In Progress→Completed), **OEE Formula** (A × P × Q), **Material Flow** (PO→Receiving→Stock→Reserved→Issued→Production).
  - `userGuide/ModuleHelpDrawer.jsx` — slide-in panel kanan (Sheet) dengan: header context, CTA "Mulai Tour Interaktif", Tujuan, **Screenshot real dari halaman** (`/guide/screenshots/{moduleId}.png`), Diagram Konsep (kalau ada), Bagian Halaman, Tombol & Aksi, Tips (amber), Warnings (red), Skenario Terkait (cyan).
  - `userGuide/ModuleTour.jsx` — lightweight overlay tour (custom, no external lib): dim background + ring highlight di element target + tooltip auto-positioned + Prev/Next/Skip + progress dots + ESC/arrow-key navigation. Try-catch untuk invalid CSS selector.
- **PortalShell.jsx**: tombol **Help (?)** ungu prominent di topbar (selalu visible) + tombol **BookOpen** untuk full guide modal. State: `helpOpen`, `tourSteps`, `guideOpen`. Render: `ModuleHelpDrawer`, `ModuleTour`, `UserGuideDialog`.
- **Real screenshots** semua 16 modul Portal Produksi captured via Playwright + system Chromium → pngquant compress → tersimpan di `/app/frontend/public/guide/screenshots/` (~2.2MB total). Modul: production-dashboard, prod-line-board, prod-aps-gantt, prod-orders, prod-work-orders, prod-bundles, prod-rework-board, prod-assignments, prod-bulk-mi, prod-shift-handover, prod-material-reservation, prod-oee, prod-line-balance, prod-rework-analytics, prod-alert-settings, prod-andon-board.
- **Tour data** sudah ditulis untuk 4 modul kunci dengan testid yang ada: `prod-work-orders` (4 step), `prod-bulk-mi` (2 step), `prod-shift-handover` (2 step), `prod-material-reservation` (2 step).
- **Backend**: `JWT_SECRET` di-set di `.env`, demo data di-seed (5 lines, 10 machines, 15 employees, 5 models, 5 WO, dll).

---

## Test Credentials
- **Admin**: admin@garment.com / Admin@123 (see `/app/memory/test_credentials.md`)

---

## Prioritized Backlog

### P0 — All Done ✅
- [x] LKP foto otomatis muncul di PDF (Sprint 26)

### P1 — All Done ✅
- [x] Production Calendar ↔ APS integration
- [x] Material Reservation auto-trigger saat WO release
- [x] Shift Handover sign-off flow
- [x] OEE Dashboard
- [ ] OEE data seeding / event log from actual WIP recording

### P2 (Medium)
- [x] End-of-Shift PDF Report (Sprint 26)
- [ ] WhatsApp/Telegram notification (low stock, WO due date)
- [ ] Style Master 2.0 (design image management)
- [ ] AQL Sampling Tool (inline QC)

### P3 (Polish / Future)
- [ ] Replace native select → Shadcn Combobox
- [ ] Tooltip for all icon-only buttons
- [ ] Accessibility improvements (ARIA)
- [ ] Advanced Finance: Cash Flow, Tax module, Multi-currency, Budgeting
- [ ] Mobile app wrapper (Capacitor/Expo)

---

## Next Recommended Tasks
1. **P0 Completed**: Warehouse Portal Bug Fixes (29 April 2026) — B1-B11 all fixed + tested
2. **P1 Upcoming**: OEE event-log auto-seeding from WIP recording
3. **P1 Upcoming**: WhatsApp/Telegram notification stack
4. **P2 Upcoming**: Style Master 2.0 (design images, version control)
5. **P2 Upcoming**: AQL Sampling Tool inline QC
6. **P2 Upcoming**: P2 UX improvements from Warehouse Audit (U1-U8):
   - U1: Dashboard card "Stok Kritis" (low-stock count at a glance)
   - U2: Bulk PO creation (CSV upload)
   - U3: Material Issue barcode scan to auto-fill
   - U4: Opname sheet Excel export
   - U5: Search/filter by location in Stock Module
   - U6: Visual stock heatmap by warehouse zone
   - U7: Expiry date tracking per lot
   - U8: Reorder point alert config per material

---

## Known APIs (Sprint 26)
- `GET /api/rahaza/lkp/{id}/pdf` — generate or fetch cached LKP PDF (auto-includes photos)
- `POST /api/rahaza/lkp/{id}/photos` — upload QC/production photo (sets pdf_stale=True)
- `GET /api/rahaza/shift-handovers/{id}/pdf` — End-of-Shift PDF Report
- `POST /api/rahaza/shift-handovers/{id}/sign-off` — supervisor acknowledgement

---

## Critical Files
- `/app/backend/utils/lkp_pdf.py` — LKP PDF builder (sections A–L)
- `/app/backend/utils/shift_report_pdf.py` — End-of-Shift PDF builder (sections A–G)
- `/app/backend/routes/rahaza_lkp.py` — `_generate_pdf_bytes` (aiohttp), pdf_stale-aware download cache
- `/app/backend/routes/rahaza_shift_handover.py` — `download_shift_report_pdf` endpoint
- `/app/frontend/src/components/erp/userGuide/guideData.js` — structured data panduan (Sprint 27)
- `/app/frontend/src/components/erp/userGuide/UserGuideContent.jsx` — main rich-visual renderer (Sprint 27)
- `/app/frontend/src/components/erp/userGuide/UserGuideDialog.jsx` — modal wrapper untuk PortalSelector (Sprint 27)
- `/app/frontend/src/components/erp/RahazaUserGuideModule.jsx` — page wrapper (Sprint 27, refactored)
- `/app/frontend/src/components/erp/PortalSelector.jsx` — tombol Panduan di top-bar (Sprint 27)
- `/app/frontend/src/components/erp/moduleRegistry.js` — `mgmt-help → RahazaUserGuideModule`
- `/app/frontend/src/components/erp/RahazaShiftHandoverModule.jsx` — `downloadHandoverPdf`

---

## Warehouse Portal Bug Fixes — Sprint Bugfix (29 April 2026)

### P0 Critical Fixes (5 bugs — Data Integrity)
- **B1**: Reservation/availability now reads from `rahaza_material_stock` (not stale `stock_qty` in materials doc) — `rahaza_material_reservation.py`, `rahaza_work_orders.py`
- **B2**: Low-stock filter fixed (`s.get("qty")` not `s.get("quantity")`) — `rahaza_inventory.py:159`
- **B3**: Opname FE↔BE field mismatch fixed — backend now accepts `physical_qty`→`counted_qty`, `adjusted/approved` triggers completion — `warehouse.py`
- **B4**: Putaway now syncs to `rahaza_material_stock` (source decremented, target incremented) — `warehouse.py`; Receiving also sets `material_id` on `warehouse_stock` rows
- **B5**: Seed now uses `qty` field (not `quantity`), gets default warehouse location; `_migrate_material_stock_nulls` with DuplicateKeyError-safe merge — `rahaza_demo_seed.py`

### P1 High Priority Fixes (6 bugs)
- **B6**: Movements use `created_at` (canonical) + `timestamp` (compat), sorted by `created_at` — `rahaza_inventory.py`
- **B7**: PO number generation is now atomic via MongoDB `$inc` counter — `rahaza_po.py`
- **B8**: `GET /materials` defaults to `active=True` filter; `?include_inactive=true` to bypass — `rahaza_inventory.py`
- **B9**: `"packaging"` added to valid `MATERIAL_TYPES` — `rahaza_inventory.py`
- **B10**: Movement location enrichment falls back to `warehouse_locations` if not found in `rahaza_locations` — `rahaza_inventory.py`
- **B11**: Material Issue confirm uses atomic conditional `$gte` decrement to prevent negative stock race condition — `rahaza_inventory.py`

### Frontend Fix
- Fixed `html-webpack-plugin` child compilation error blocking React app from rendering.
  Root cause: `resolveLoader.alias` needed for `html-webpack-plugin/lib/loader.js`.
  Fix: added `resolveLoader.alias` in `craco.config.js`.

### Test Coverage
- Created: `/app/backend/tests/test_warehouse_bug_fixes.py` (27 tests, all passing)
