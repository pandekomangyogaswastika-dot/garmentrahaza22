# 📋 PLAN: PRODUCTION AUTOMATION + BOM CONFIGURATION ENHANCEMENTS
## PT Rahaza ERP — Minim Klik Harian (tanpa mengurangi fitur) + Master Data BOM Multi-Version

**Created:** 2026-04-29  
**Last Updated:** 2026-04-29  
**Status:** ✅ Phase 4 (Production Automation) — DONE · ✅ Phase 5b (BOM Configuration UI) — DONE  
**Goal:**
- **Produksi:** mempercepat flow eksekusi & administrasi produksi (minim klik, tetap lengkap).
- **BOM:** menyediakan konfigurasi BOM yang **multi-version + per-size**, bisa **edit versi aktif**, terintegrasi dengan **master material**, serta menyediakan **preview kebutuhan material** untuk quantity tertentu.

---

## 🎯 OBJECTIVES

### Primary Goals — Production (Phase 4)
1. **Kurangi klik harian (Supervisor/PPIC/Operator):** target -30% sampai -60% tanpa menghapus fitur.
2. **Pisahkan Rework dari proses utama:** Rework menjadi sub-proses terpisah, tidak mengganggu 6 proses utama.
3. **Percepat aktivitas lintas portal:** optimasi klik di Management/Production/Warehouse/Finance/HR/Self-Service.

### Primary Goals — BOM (Phase 5b)
4. **Workflow BOM cepat & jelas:** **Model → Size → Materials → Save**.
5. **Multi-version BOM per Model+Size:** buat versi baru, edit, aktivasi/nonaktif, dan histori revisi.
6. **Material master integration:** user bisa **pilih material existing** atau **buat material baru** langsung dari form BOM.
7. **Preview kebutuhan material:** kalkulasi kebutuhan untuk **X pcs** (WO/produksi), tampilkan subtotal benang & aksesoris, dan ringkasan.

### Secondary Goals
8. **Audit-friendly:** perubahan BOM tercatat (timestamp + activity log).
9. **Konsistensi UX:** mengikuti glassmorphism + shadcn/ui + Bahasa Indonesia, tanpa React Router.
10. **Minim friction:** bulk actions, copy antar size, dan default state yang membantu input cepat.

### Success Metrics
- ✅ Phase 4: Rework terpisah dari proses utama dan eksekusi tetap stabil.
- ✅ Click optimizations berjalan pada portal-portal utama (tanpa regresi).
- ✅ Payslip PDF export tersedia untuk single & bulk.
- ✅ Phase 5b:
  - [x] Setiap model+size punya daftar versi BOM dan **1 versi aktif**.
  - [x] User bisa **edit versi aktif** atau **buat versi baru**.
  - [x] User bisa memilih material dari master atau membuat baru inline.
  - [x] Preview kebutuhan material untuk X pcs akurat dan cepat dipindai.

---

## 📌 CURRENT STATUS (Baseline)

### Completed (from earlier phases)
- ✅ Navigation Refinement Phase 1 + Phase 2 (state-based; tanpa React Router).
- ✅ API Key Config System (DB-first/env fallback).

### Completed — Phase 4 (Production Automation)
- ✅ Phase 4 Production Automation: routing PortalShell, Production Wizard dialog fix, Calendar date picker pada Assignment Template.
- ✅ Rework dipisahkan dari alur proses utama (sub-proses `prod-exec-rework`).
- ✅ Click Optimization lintas portal:
  - Attendance: “Salin Kemarin”
  - Leaves: Bulk Approve
  - AR Invoices: 1-click Pay
  - Payroll: “Salin Bulan Lalu”
  - Warehouse: inline stock adjustments
  - Sidebar: Recent Modules footer

### Completed — Payroll
- ✅ Payslip PDF Export (single + bulk) menggunakan `reportlab` + `PyPDF2`.

### In Progress — Phase 5b (BOM Configuration)
**Yang sudah ada saat ini:**
- ✅ Backend BOM baseline: `/app/backend/routes/rahaza_bom.py` (matrix per size, CRUD, copy-to-sizes)
- ✅ Frontend BOM baseline: `/app/frontend/src/components/erp/RahazaBOMModule.jsx` (matrix + editor sederhana)

**Gap vs requirement baru:**
- 🔴 Backend masih **single-version** (field `version` dan multi-versi belum ada).
- 🔴 Belum ada endpoint & UI untuk **aktivasi versi** dan **histori**.
- 🔴 Belum ada **material master integration** (picker + inline create).
- 🔴 Belum ada **preview kebutuhan material** untuk quantity tertentu.

**Catatan testing:** Session timeout pada pengujian panjang adalah perilaku JWT expiry yang wajar (bukan bug produk).

---

## 🧩 SCOPE

### Phase 4 — Production Automation (DONE)
1. Rework separation
2. Wizard/dialog fixes
3. Click minimization lintas portal

### Phase 5b — BOM Configuration Enhancement (P0)
1. **Multi-version BOM** per Model+Size
2. **Version management UI**: create, edit aktif, activate/deactivate, (optional) compare
3. **Material master integration**: pilih existing atau tambah baru inline
4. **Requirements preview**: kalkulasi material untuk X pcs
5. **Copy-to-sizes** tetap tersedia (upgrade UX, tetap pakai endpoint existing)

---

## 🗓️ IMPLEMENTATION PHASES

### PHASE 5bA: Backend Multi-Version + Requirements Preview
**Goal:** menambah dukungan versi BOM + endpoint untuk preview kebutuhan material.  
**Effort:** 2–4 hari  
**Risk:** Medium (migrasi data lama + aturan versi aktif)

Deliverables:
- Skema BOM mendukung: `version`, `is_active` (atau `active_version` rule), `created_at`, `updated_at`
- Endpoint list versions per model+size
- Endpoint activate/deactivate versi
- Endpoint preview kebutuhan material untuk X pcs

### PHASE 5bB: Frontend UI BOM Komprehensif
**Goal:** UI sesuai design guidelines (tabs + version rail + editable tables + picker) + minim klik.  
**Effort:** 3–6 hari  
**Risk:** Medium (kompleksitas state + validasi input)

Deliverables:
- Matriks BOM tetap ada, namun “Buka Editor” membawa user ke tab Editor/Versi
- Editor BOM dengan tabel editable (Benang/Aksesoris)
- VersionRail: pilih versi, activate/deactivate, create version
- InlineMaterialPicker: select existing + create new
- Preview kebutuhan material: input qty pcs + tabel hasil

### PHASE 5bC: Testing + Polish
**Goal:** memastikan endpoint & UI stabil dan konsisten dengan portal lain.

Deliverables:
- testing agent (backend + frontend)
- manual spot-check (karena kendala JWT deep frontend test)
- perbaikan edge case & UX polish

---

## 📝 PHASE 5b TASKS (Priority: P0)

### Task 5b.1 (P0): Upgrade Schema BOM untuk Multi-Version
**Estimated Time:** 1–2 hari

#### Database Rules
- Tambah field:
  - `version`: integer (mulai dari 1)
  - `is_active`: boolean (hanya 1 aktif per model_id+size_id)
  - `status`: optional (`draft/active/inactive`) bila diperlukan
- Migrasi data existing:
  - Semua dokumen BOM existing menjadi `version: 1` dan `is_active: true`

#### Backend Changes (`/app/backend/routes/rahaza_bom.py`)
- Update schema docstring dan validasi.
- Revisi endpoint:
  - `GET /api/rahaza/models/{model_id}/bom` -> tampilkan status **versi aktif** per size + `active_version`.
  - `POST /api/rahaza/boms`:
    - default: create **versi baru** untuk model+size (bukan blok duplicate), atau sediakan `mode=upsert`.
    - jika requirement tetap: user boleh edit versi aktif → gunakan `PUT /boms/{id}`.
- Tambah endpoint baru:
  - `GET /api/rahaza/boms/versions?model_id=...&size_id=...` (list versi)
  - `POST /api/rahaza/boms/{id}/activate` (aktifkan versi dan nonaktifkan versi lain pada model+size)
  - `POST /api/rahaza/boms/{id}/deactivate` (opsional; atau deactivate via activate versi lain)

#### Testing Checklist
- [ ] BOM existing tetap terbaca.
- [ ] Hanya 1 versi aktif per model+size.
- [ ] Edit versi aktif via PUT tetap bisa.

---

### Task 5b.2 (P0): Material Master Integration (Select Existing + Create Inline)
**Estimated Time:** 1–3 hari

#### Backend
- Identifikasi endpoint master material yang sudah ada (atau tambahkan minimal):
  - `GET /api/rahaza/materials?query=...&type=yarn|accessory` (untuk picker)
  - `POST /api/rahaza/materials` (create material baru)
- Pastikan BOM menyimpan:
  - `material_id` (jika dipilih dari master)
  - tetap menyimpan `name/code` snapshot untuk audit

#### Frontend
- Buat komponen composite sesuai design guidelines:
  - `InlineMaterialPicker` (Popover+Command) + action “Tambah material baru” (Dialog/Drawer)
- Integrasikan picker pada row Benang/Aksesoris.

#### Testing Checklist
- [ ] Cari material existing dan pilih → row terisi (kode/nama/default unit).
- [ ] Buat material baru inline → otomatis terpilih pada row.

---

### Task 5b.3 (P0): BOM Editor Multi-Version + VersionRail UI
**Estimated Time:** 2–4 hari

#### Frontend (`/app/frontend/src/components/erp/RahazaBOMModule.jsx` + modul pendukung)
- Ubah dari modal editor tunggal menjadi layout bertab:
  - Tab: Matriks · Editor · Versi · Preview
- Tambah state:
  - `selectedSizeId`, `selectedVersionId`, `activeTab`, `isDirty`
- Implement VersionRail:
  - list versi + badge aktif
  - tombol: Create Version, Activate
  - (opsional) Compare
- Edit aktif diperbolehkan:
  - tombol “Simpan Perubahan” (PUT)
  - tombol “Simpan sebagai Versi Baru” (POST create versi baru)

#### Click Optimizations (BOM)
- Default memilih model pertama (sudah ada) dan size terakhir yang dibuka (persist di localStorage).
- “Duplikasi baris material” untuk percepat input.
- “Copy ke size lain” tetap 1 modal.

#### Testing Checklist
- [ ] Create versi baru berhasil.
- [ ] Activate versi mengubah versi aktif di matriks.
- [ ] Edit versi aktif tersimpan dan audit log tercatat.

---

### Task 5b.4 (P0): Requirements Preview (Kebutuhan Material untuk X pcs)
**Estimated Time:** 1–2 hari

#### Backend
- Tambah endpoint:
  - `POST /api/rahaza/boms/{id}/requirements-preview` body: `{ qty_pcs: number, rounding?: 'none'|'ceil'|'floor' }`
- Output:
  - `yarns`: qty_total_kg per material
  - `accessories`: qty_total per material
  - subtotal per kategori

#### Frontend
- Implement `RequirementsPreviewCard`:
  - input qty pcs
  - tampilkan hasil tabel ringkas (mono numbers)
  - (opsional) export CSV

#### Testing Checklist
- [ ] Kalkulasi sesuai: qty_total = qty_per_pcs * qty_pcs.
- [ ] Benang tampil dalam KG, aksesoris sesuai unit.

---

## 🎨 UI/UX REQUIREMENTS (Design Guidelines Integration)

Mengikuti `/app/design_guidelines.md` (BOM-specific + general rules):
- Bahasa UI: **id-ID**.
- Komponen utama: **shadcn/ui** + existing Glass components (`GlassCard`, `GlassPanel`, `GlassInput`).
- Pola IA BOM: **Tabs + VersionRail + Editable tables + Preview**.
- Semua elemen interaktif wajib `data-testid` (kebab-case).
- Dilarang `transition: all`.
- Tidak ada React Router.

---

## 🧪 TESTING STRATEGY

### Automated / API tests
- [ ] Multi-version: create/list/activate/edit.
- [ ] Requirements preview calculation.
- [ ] Copy-to-sizes tetap berjalan.

### UI Smoke tests
- [ ] Matrix → buka editor → pilih versi → simpan.
- [ ] InlineMaterialPicker: pilih existing + create baru.
- [ ] Preview kebutuhan material untuk X pcs.

### Required tool
- Setelah perubahan signifikan Phase 5b: jalankan **testing agent** untuk backend+frontend.
- Jika testing agent terkena JWT timeout pada deep UI test, lakukan **manual verification** (screenshot) untuk view utama.

---

## 📊 ROLLOUT PLAN

1. Deploy Phase 5b ke staging.
2. UAT internal (PPIC/Produksi/Admin) 2–3 hari:
   - kecepatan input BOM
   - konsistensi versi aktif
   - akurasi preview kebutuhan
3. Deploy ke produksi setelah sign-off.

---

## 🚨 RISKS & MITIGATION

### Risk 1: Migrasi data BOM lama mengganggu operasi
**Mitigasi:** migrasi non-destruktif (set version=1, is_active=true), endpoint lama tetap kompatibel.

### Risk 2: Konflik versi aktif (lebih dari 1 aktif)
**Mitigasi:** enforce di backend saat activate: updateMany set is_active=false lalu set true pada target.

### Risk 3: Master material belum tersedia endpoint-nya
**Mitigasi:** sediakan endpoint minimal materials untuk search+create, lalu iterasi integrasi.

### Risk 4: UI BOM terlalu kompleks
**Mitigasi:** gunakan Tabs jelas + VersionRail sebagai “single source of truth”; minim modal bertingkat.

---

## 📚 DOCUMENTATION UPDATES
- [ ] Panduan: “Cara membuat versi BOM baru”
- [ ] Panduan: “Aktifkan versi BOM per size”
- [ ] Panduan: “Preview kebutuhan material untuk X pcs”

---

## ✅ SIGN-OFF CHECKLIST

### Phase 4 (DONE)
- ✅ Rework terpisah dari proses utama.
- ✅ Optimasi klik lintas portal.
- ✅ PDF slip gaji (single & bulk).

### Phase 5b (Target)
- [ ] Multi-version BOM per model+size berjalan.
- [ ] Edit versi aktif berjalan.
- [ ] Material master integration (select + create) berjalan.
- [ ] Preview kebutuhan material untuk X pcs akurat.
- [ ] Copy-to-sizes tetap berjalan.
- [ ] testing report hijau atau issue sudah ditangani.

---

**Prepared by:** Neo AI Agent  
**Date:** 2026-04-29  
**Version:** 3.0
