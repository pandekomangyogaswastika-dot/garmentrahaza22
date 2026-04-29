# 🔎 AUDIT MENYELURUH — Portal Gudang & Inventory PT Rahaza ERP

**Tanggal audit:** 29 April 2026
**Cakupan:** 11 modul Portal Gudang + integrasi cross-portal (Inventory, PO, Receiving, Reservasi)
**Metode:** Static code review + live API testing + data verification

---

## 1. EXECUTIVE SUMMARY

Portal Gudang adalah modul **paling kompleks** di PT Rahaza ERP karena menjadi tulang punggung data stok yang dikonsumsi oleh Produksi (BOM), Keuangan (inventory accounting), dan SDM (asset). Audit menemukan:

| Status | Jumlah |
|---|---|
| ✅ **Strengths** (yang sudah baik) | 8 area |
| 🟥 **Critical bugs (P0)** — data integrity | **5 bugs** |
| 🟧 **High priority (P1)** — functional broken | **6 bugs** |
| 🟨 **Medium (P2)** — UX/consistency | **8 issues** |
| 🟦 **Architecture debt** — major refactor needed | **3 area** |

**Verdict:** Portal Gudang **functionally complete tapi data integrity-nya rapuh**. Banyak fitur yang "ada di UI" tetapi backend silently broken (mis: reservasi material, opname). Critical untuk fix sebelum production go-live serius.

---

## 2. MODULE INVENTORY

| # | Module ID | File Frontend | Backend Endpoint | Status |
|---|---|---|---|---|
| 1 | `warehouse-dashboard` | WarehouseDashboard.jsx | `/api/warehouse/dashboard` | 🟨 OK tapi limited |
| 2 | `wh-materials` | RahazaMaterialsModule.jsx | `/api/rahaza/materials` | 🟧 Bugs di filter |
| 3 | `wh-stock` | RahazaStockModule.jsx | `/api/rahaza/material-stock*` | 🟥 Data inconsistent |
| 4 | `wh-material-issue` | RahazaMaterialIssueModule.jsx | `/api/rahaza/material-issues` | 🟥 Bisa fail karena stok kosong |
| 5 | `wh-purchase-orders` | PurchaseOrderModule.jsx | `/api/rahaza/purchase-orders` | 🟧 Race condition di nomor PO |
| 6 | `wh-receiving` | ReceivingModule.jsx | `/api/warehouse/receiving` | 🟨 OK, ada quirk |
| 7 | `wh-putaway` | PutAwayModule.jsx | `/api/warehouse/putaway` | 🟥 Tidak sync ke material_stock |
| 8 | `wh-opname` | OpnameModule.jsx | `/api/warehouse/opname` | 🟥 **Frontend↔Backend field mismatch — broken!** |
| 9 | `wh-bin` | LocationsModule.jsx | `/api/warehouse/locations` | 🟧 Dual location collection |
| 10 | `wh-accessory` | AccessoryModule.jsx | `/api/rahaza/materials?type=accessory` | ✅ OK (Sprint 3.2 sudah merge) |
| 11 | `wh-material-reservation` | RahazaMaterialReservationModule.jsx | `/api/rahaza/materials/...` | 🟥 **stock_qty field tidak ada** |

---

## 3. ARCHITECTURE DEBT (🟦)

### 🟦 A1. Triple Stock Ledger
Tiga sumber data stok yang **tidak konsisten satu sama lain**:

| Ledger | Field | Update by | Read by |
|---|---|---|---|
| `rahaza_materials.stock_qty` | `stock_qty` | Demo seed only | **Reservation** + WO release |
| `rahaza_material_stock` | `qty` | Receiving (sync), Issue, Adjust, Transfer | Material Issue, Stock Module |
| `warehouse_stock` | `quantity`, `available` | Receiving, Putaway, Opname | Dashboard, Putaway, Opname |

**Akibat data drift**:
- Setelah seed: hanya `materials.stock_qty` ada — Stock Module kosong, Issue gagal
- Setelah Receiving: `warehouse_stock` & `rahaza_material_stock` terupdate, tapi `materials.stock_qty` **stale** → reservasi pakai data lama
- Setelah Material Issue: hanya `rahaza_material_stock` berkurang → `warehouse_stock` jadi over-count
- Setelah Putaway: hanya `warehouse_stock` pindah → `rahaza_material_stock` tidak tahu

**Fix needed:** Konsolidasi ke 1 source-of-truth (rekomendasi: `rahaza_material_stock` sebagai canonical, drop `materials.stock_qty` & migrasi `warehouse_stock` ke sync-only).

### 🟦 A2. Dual Location Collection
- `warehouse_locations` (untuk receiving, putaway, opname) — dipakai di Portal Gudang
- `rahaza_locations` (untuk lini produksi, employee, machine) — dipakai di Portal Produksi/SDM

Keduanya menyimpan struktur "tempat fisik" tapi **tidak terhubung**. UX bingung: lokasi gudang muncul beda dari lokasi produksi padahal mungkin gedung sama.

**Fix needed:** Merge ke `rahaza_locations` dengan `type` field (warehouse/production/office).

### 🟦 A3. Duplikat PO System
- `rahaza_purchase-orders` (NEW, modern, dengan approval workflow) — dipakai Warehouse PO
- `production_pos` + `po_items` + `po_accessories` (LEGACY) — dipakai Order Produksi

Concept berbeda (Warehouse PO = pembelian ke supplier, Production PO = order dari customer/buyer) tapi naming-nya membingungkan. Dokumentasi & UI label perlu eksplisit.

---

## 4. CRITICAL BUGS (P0 — DATA INTEGRITY) 🟥

### 🟥 B1. Reservation Membaca Field Tidak Ada
**File:** `routes/rahaza_material_reservation.py:53`, `routes/rahaza_work_orders.py:130`

```python
stock_qty = material.get("stock_qty", 0)   # ❌ field ini hanya ada di seed data
```

**Bug:** `rahaza_materials` document **tidak punya field `stock_qty` secara resmi**. Yang ada di seed adalah artifact dari `rahaza_demo_seed.py:61-70`. Untuk material yang dibuat lewat UI (POST `/materials`), field ini tidak di-set sama sekali (lihat `create_material()` line 205-216 — tidak ada `stock_qty`).

**Akibat:**
1. Material baru via UI → `stock_qty = None` → reservasi selalu "insufficient"
2. Material dari seed → `stock_qty = 5000` → reservasi pakai data **stale** (tidak update saat receiving/issue)
3. WO release log warning palsu / spam

**Fix:**
```python
# Aggregate across all locations
stocks = await db.rahaza_material_stock.find({"material_id": material_id}, {"_id": 0}).to_list(None)
stock_qty = sum(float(s.get("qty") or 0) for s in stocks)
```

### 🟥 B2. Low-Stock Filter Menggunakan Field Salah
**File:** `routes/rahaza_inventory.py:159`

```python
stock_by_mat[mid] = stock_by_mat.get(mid, 0) + float(s.get("quantity") or 0)  # ❌ "quantity"
# Harusnya:
stock_by_mat[mid] = stock_by_mat.get(mid, 0) + float(s.get("qty") or 0)       # ✅ "qty"
```

`rahaza_material_stock` menggunakan field `qty`. Akibat: filter `?low_stock=true` selalu return list kosong (atau sangat salah).

### 🟥 B3. Opname Frontend ↔ Backend Field Mismatch
**File:** `OpnameModule.jsx:11-16, 50-58` vs `routes/warehouse.py:564-573, 590-630`

| Frontend pakai | Backend pakai |
|---|---|
| `physical_qty` | `counted_qty` |
| `discrepancy` | `variance` |
| Status: `counting/review/approved/adjusted` | Status: `draft/completed` |

**Akibat:** Opname yang dibuat user tidak akan tersimpan dengan benar — input physical_qty tidak nyampe ke backend, status badge tidak pernah match.

### 🟥 B4. Putaway Tidak Sync ke Material Stock
**File:** `routes/warehouse.py:457-514`

Putaway move stok antar lokasi di `warehouse_stock`, tapi **tidak update** `rahaza_material_stock`. Akibat: setelah putaway, Stock Module menampilkan stok di lokasi LAMA (karena snapshot di rahaza_material_stock tidak ikut pindah).

**Fix:** Tambahkan `_sync_to_material_stock` calls (negative untuk source, positive untuk target).

### 🟥 B5. Seed Data Membuat Stock Rows dengan NULL
**Verified live:**
```bash
$ curl /api/rahaza/material-stock
[{"material_id": "...", "location_id": null, "qty": null}, ...]  # 10 rows!
```

`rahaza_demo_seed.py` membuat 10 entry di `rahaza_material_stock` dengan `location_id=None, qty=None`. Akibat:
- Stock summary `total_qty = 0` (karena None)
- Stock list error di frontend (location lookup gagal)
- Material Issue tidak bisa pull dari "default location"

**Fix:** Seed harus pilih location_id default (mis: WH-MAIN) dan set qty dari `stock_qty` di material data.

---

## 5. HIGH PRIORITY BUGS (P1 — FUNCTIONAL) 🟧

### 🟧 B6. Movement Field Inconsistency (`timestamp` vs `created_at`)
- `rahaza_inventory._log_movement` → `timestamp` field
- `warehouse._record_material_movement` → `created_at` field
- `list_movements()` sort by `"timestamp"` only

**Akibat:** Movements dari Receiving (created_at-based) muncul di urutan random/bottom di list. Audit trail jadi kacau.

**Fix:** Standarisasi ke `created_at` di kedua sisi.

### 🟧 B7. Atomic PO Number Race Condition
**File:** `routes/rahaza_po.py:67-72`

```python
count = await db.rahaza_purchase_orders.count_documents({"po_number": {"$regex": f"^{prefix}"}})
return f"{prefix}-{count+1:03d}"
```

`count_documents` + `count+1` **bukan atomic**. 2 user create PO simultan → keduanya dapat nomor sama.

**Fix:** Pakai pattern dari `warehouse.py:534-540` (`find_one_and_update` dengan `$inc` + `upsert`).

### 🟧 B8. Materials List Tidak Filter `active`
**File:** `routes/rahaza_inventory.py:138-149`

`list_materials` tidak default-filter `active=True`. Akibat: dropdown di Receiving, Material Issue, Reservasi menampilkan material yang sudah deactivate. User bingung & berpotensi pilih yang salah.

**Fix:** `q["active"] = True` (kecuali query param `include_inactive=true`).

### 🟧 B9. Material Type "packaging" Tidak Valid
**File:** `routes/rahaza_inventory.py:52` vs `rahaza_demo_seed.py:70`

```python
MATERIAL_TYPES = ["yarn", "accessory", "fg"]  # backend validation
```

Tapi seed buat material dengan `type="packaging"` → bisa lolos saat insert tapi gagal saat update via PUT `/materials/{id}`. Filter `?type=packaging` juga reject 400.

**Fix:** Tambah `"packaging"` ke `MATERIAL_TYPES` ATAU ubah seed.

### 🟧 B10. Receiving Pakai `warehouse_locations`, Movement Lookup Pakai `rahaza_locations`
ReceivingModule fetch dari `/api/warehouse/locations`, lalu submit dengan `location_id` dari sana. Material movement menyimpan ID itu. Lalu `list_movements` enrich pakai `db.rahaza_locations.find_one({"id": ...})` → tidak ketemu → `from_location_name = None`.

**Fix:** Pilih satu collection, atau fallback lookup di kedua tempat.

### 🟧 B11. Material Issue Confirm Bisa Bikin Stok Negatif
**File:** `routes/rahaza_inventory.py:438-467` (material-adjust **does** check negative tapi material-issue confirm logic perlu di-verify)

Sudah saya validate `material-adjust` block negative. Tapi `material-issue confirm` perlu check serupa untuk semua items + **lock per row** (agar tidak race).

---

## 6. MEDIUM ISSUES (P2 — UX & CONSISTENCY) 🟨

### 🟨 U1. WarehouseDashboard Sangat Minimalis
Hanya 4 KPI tile + recent movements. Tidak ada:
- Pareto stock value (top 10)
- Aging report (stok lama tidak bergerak)
- Reorder suggestions (yang mendekati min_stock)
- Coverage days (stok habis dalam berapa hari pada laju issue saat ini)

### 🟨 U2. Tidak Ada Bulk Actions
- Receiving: tidak ada bulk approve / bulk reject
- PO: tidak ada bulk approve untuk sekian PO sekaligus
- Material Issue: hanya 1-WO-at-a-time (Bulk MI ada di Production portal, namun mestinya juga muncul di Gudang)

### 🟨 U3. Tidak Ada Excel Import/Export untuk Master Data
Material list bisa ratusan SKU. UI hanya support 1-by-1 input. Tidak ada:
- Import CSV/Excel untuk bulk add material
- Export Excel untuk audit
- Template Excel download

### 🟨 U4. Tidak Ada Search/Filter di Stock Module
RahazaStockModule menampilkan semua stock baris tanpa search bar atau filter. Untuk pabrik real (1000+ SKU × 5+ lokasi = 5000+ rows) tidak usable.

### 🟨 U5. Reservasi UI Hanya Read-only Tampak
RahazaMaterialReservationModule perlu review apakah bisa manual reserve / release dengan baik dari UI.

### 🟨 U6. Receiving Tanpa Reject Workflow
Jika barang datang cacat, harus partial-receive. UI saat ini ada `rejected_qty` tapi tidak ada workflow eskalasi (kembali ke supplier, klaim, dll).

### 🟨 U7. Putaway Tidak Punya Multi-target
Hanya 1 target lokasi per putaway. Untuk receiving 100kg → split ke 2 rak (50/50), butuh 2 putaway terpisah.

### 🟨 U8. Tidak Ada Barcode/QR Scanning
Receiving, Putaway, Opname idealnya pakai barcode scanner di gudang. UI saat ini full keyboard input.

---

## 7. STRENGTHS (✅) — Yang Sudah Baik

1. ✅ **Sync bridge Receiving → rahaza_material_stock** sudah ada (Sprint 1, line 34-55) dengan logging audit
2. ✅ **Atomic counter** untuk receipt_number, opname_number (warehouse.py)
3. ✅ **PO ↔ Receiving 3-way matching** (Sprint 2.1) — pre-fill items, supplier, ada visual sync indicator
4. ✅ **Auto-posting ke GL** untuk Inventory Receive, Issue, Adjust (rahaza_posting integration)
5. ✅ **Low-stock notification** via publish_notification dengan dedup_key (Phase 12.2)
6. ✅ **Material types & units terstandardisasi** (yarn/accessory/fg, kg/pcs/m/set/pair/gram)
7. ✅ **Workflow PO lengkap** (draft → pending → approved → received) dengan reject & re-submit
8. ✅ **Audit trail** via `log_activity` di hampir semua mutating operation

---

## 8. RECOMMENDATIONS / PROPOSED ROADMAP

### 🔥 Sprint Q1 (1-2 minggu) — STABILIZE DATA
1. **Fix B1, B2** — reservasi & low-stock filter pakai canonical stock (rahaza_material_stock)
2. **Fix B3** — opname field naming alignment (frontend ↔ backend)
3. **Fix B4** — putaway sync ke rahaza_material_stock
4. **Fix B5** — seed dengan location_id valid + qty proper
5. **Fix B6** — movement timestamp field standardisasi
6. **Fix B7** — atomic PO counter
7. **Fix B8, B9** — active filter + tambah "packaging" type

### 🚀 Sprint Q2 (1-2 minggu) — UX UPLIFT
1. WarehouseDashboard: tambah Pareto, Aging, Reorder, Coverage
2. Stock Module: search bar + filter type/location + pagination
3. Bulk Actions: GR approve, PO approve, Material Issue
4. Reservasi Module review & polish

### 🌟 Sprint Q3 (2-3 minggu) — MAJOR REFACTOR
1. **Konsolidasi Stock Ledger** (A1) — migrasi ke single source-of-truth `rahaza_material_stock`
2. **Merge Locations** (A2) — single `rahaza_locations` dengan type field
3. Excel import/export semua master + transaksi
4. Barcode/QR scanning untuk Receiving, Putaway, Opname (mobile-friendly)

### 🧙 Backlog
- AQL Sampling untuk QC inbound (cek mutu material datang)
- Multi-currency (untuk imported material)
- Vendor performance scorecard (on-time delivery, quality)
- Predictive reorder (ML-based, bukan hanya min_stock)

---

## 9. RINGKASAN VISUAL

```
                Portal Gudang & Inventory
                        │
        ┌───────────────┼───────────────┐
        │               │               │
   RINGKASAN       INVENTORI       OPERASIONAL
        │               │               │
   Dashboard ✅   Materials 🟧    PO 🟧
                  Stock 🟥        Receiving 🟨
                  Issue 🟥        Putaway 🟥
                                  Opname 🟥
                                  Locations 🟧
                                  Accessory ✅
                                  Reservation 🟥

              ↓ Data flow ke ↓

        Produksi (BOM)  │  Keuangan (GL)
              │               │
         WO Release      Auto-posting
         Material Issue  Inventory accounts
         Reservasi       Adjustment expense
```

---

**Action item utama:** Saya rekomendasikan **fix Sprint Q1 (7 critical/high bugs) terlebih dulu** sebelum tambah feature baru. Tanpa data integrity yang solid, semua feature di atasnya rapuh.

**Tinggal beri tahu** kalau Anda mau saya:
- (a) Mulai implementasi fix Sprint Q1 (urutan: B1 → B2 → B3 → B4 → B5 → B6 → B7 → B8 → B9)
- (b) Pilih bug spesifik yang paling critical untuk fix dulu
- (c) Lanjut audit Portal lain (Keuangan, SDM, Manajemen)
