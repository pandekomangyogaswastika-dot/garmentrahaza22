# PT Rahaza ERP — Dokumentasi Use Case & Flow Sistem

> **Versi:** 1.0
> **Tanggal:** 23 April 2026
> **Target pembaca:** Manajemen, Supervisor, Akuntan, Operator, Tim IT
> **Tujuan:** Memberikan gambaran menyeluruh cara kerja sistem ERP Rahaza — dari login sampai tutup buku — sebagai referensi pelatihan, audit, maupun pengembangan lanjutan.

---

## Daftar Isi

1. [Arsitektur & Portal](#1-arsitektur--portal)
2. [Peran Pengguna (Roles)](#2-peran-pengguna-roles)
3. [Otentikasi & Sesi](#3-otentikasi--sesi)
4. [Use Case Portal Manajemen](#4-use-case-portal-manajemen)
5. [Use Case Portal Produksi](#5-use-case-portal-produksi)
6. [Use Case Portal Gudang](#6-use-case-portal-gudang)
7. [Use Case Portal Keuangan](#7-use-case-portal-keuangan)
8. [Use Case Portal SDM (HR)](#8-use-case-portal-sdm-hr)
9. [Flow Integrasi Antar Modul](#9-flow-integrasi-antar-modul)
10. [Flow Akuntansi Otomatis (Auto-posting)](#10-flow-akuntansi-otomatis-auto-posting)
11. [Flow Tutup Periode](#11-flow-tutup-periode)
12. [Seed Data & Reset Demo](#12-seed-data--reset-demo)
13. [FAQ Operasional](#13-faq-operasional)

---

## 1. Arsitektur & Portal

Sistem ERP Rahaza terdiri dari **5 Portal** yang dapat diakses sesuai peran pengguna. Setelah login, pengguna diarahkan ke halaman "Pilih Portal" untuk memilih area kerja.

| Portal | Icon | Deskripsi | Peran yang Dapat Akses |
|---|---|---|---|
| **Manajemen** | 📊 BarChart | Dashboard eksekutif, master produk/pelanggan, laporan, administrasi sistem | admin, owner |
| **Produksi** | 🏭 Factory | Lini rajut, WIP real-time, proses Rajut–Packing, rework | admin, owner, supervisor |
| **Gudang** | 📦 Warehouse | Multi-zona, penerimaan, put-away, stok benang/aksesoris, opname | admin, owner, supervisor |
| **Keuangan** | 🏛 Landmark | AR/AP, invoice, pembayaran, cost center, akuntansi penuh, HPP | admin, owner, accounting |
| **SDM (HR)** | 👤 UserCog | Karyawan, shift, absensi, penggajian multi-skema | admin, owner, hr |

**Arsitektur teknis:**
- **Frontend:** React SPA (Single Page App) dengan Tailwind CSS + Shadcn UI.
- **Backend:** FastAPI (Python) dengan Motor (MongoDB async).
- **Database:** MongoDB (semua koleksi memakai UUID, bukan ObjectId).
- **Auth:** JWT (JSON Web Token) dengan bcrypt.

---

## 2. Peran Pengguna (Roles)

| Role | Keterangan | Hak Akses Utama |
|---|---|---|
| `superadmin` | Akses tertinggi, bisa purge & seed | Semua portal + administrasi sistem |
| `admin` | Admin perusahaan | Semua portal |
| `owner` | Pemilik | Semua portal (view + action) |
| `supervisor` | Supervisor lantai produksi/gudang | Portal Produksi + Gudang |
| `accounting` | Tim keuangan/akuntan | Portal Keuangan |
| `hr` | Tim SDM | Portal SDM |

**Matriks hak akses detail** dikelola di `Portal Manajemen → Sistem → Matriks Hak Akses`. Setiap modul bisa dibatasi per role (view / edit / approve).

---

## 3. Otentikasi & Sesi

### 3.1 Login

1. Pengguna buka URL aplikasi.
2. Masukkan **email** dan **password** → klik **Masuk**.
3. Sistem memvalidasi kredensial:
   - Email di-normalisasi (lowercase, trim).
   - Password dihash bcrypt, dibandingkan dengan hash yang tersimpan.
4. Jika valid: JWT token dibuat (`exp = 24 jam`), user dikembalikan → arahkan ke halaman Pilih Portal.
5. Jika tidak valid: pesan error "Email atau password salah."

### 3.2 Logout

- Klik tombol logout di pojok kanan atas navbar → token dihapus dari localStorage → redirect ke login.

### 3.3 Kredensial Default (Demo)

```
Email    : admin@garment.com
Password : Admin@123
Role     : superadmin
```

> **Catatan keamanan:** Di produksi, wajib ganti password default & buat akun admin baru setelah setup awal.

---

## 4. Use Case Portal Manajemen

### 4.1 Dashboard Eksekutif

**Aktor:** admin, owner.

**Flow:**
1. Pilih Portal Manajemen → tampilan Dashboard Eksekutif.
2. Sistem menarik data real-time dari seluruh modul:
   - **Total Order** & **Order Aktif** (dari `rahaza_orders`).
   - **Job Aktif** (Work Orders `in_progress`).
   - **On-Time Rate** (% order selesai sebelum due_date).
   - **Pendapatan** (sum `total` AR invoices).
   - **Outstanding AR/AP** (piutang & hutang belum lunas).
   - **Shipment Tertunda**, **Total User**.
3. Grafik:
   - **Throughput Mingguan:** Total qty shipment 8 minggu terakhir.
   - **Status Job Produksi:** Distribusi WO per status (donut chart).
4. Panel **"Yang Perlu Ditindaklanjuti"**: alert otomatis — order overdue, invoice belum dibayar, dll.

**Tindakan:** Klik kartu KPI atau alert → drill-down ke modul terkait.

### 4.2 Master Data

- **Data Produk** (`rahaza_models`): Model produk — code, nama, HPP dasar, harga retail.
- **Data Pelanggan** (`rahaza_customers`): Pelanggan — code, nama, NPWP, payment_terms, kredit limit.

**Flow Tambah Produk Baru:**
1. Buka `Master Data → Data Produk → + Tambah`.
2. Isi code (unik), nama, kategori, HPP dasar, harga retail.
3. Simpan → sistem membuat dokumen baru di `rahaza_models` dengan UUID.

### 4.3 Sistem

- **Manajemen Pengguna** (`users`): CRUD user, aktivasi/nonaktif.
- **Manajemen Peran** (`roles`): Definisi role custom.
- **Matriks Hak Akses** (`permissions`): Mapping role → module + action.
- **Log Aktivitas** (`activity_logs`): Audit trail semua aksi user (login, create, update, delete, approve).
- **Pengaturan Perusahaan** (`company_settings`): Nama, alamat, NPWP, logo, format invoice.
- **Konfigurasi PDF**: Template PDF untuk invoice, PO, surat jalan.
- **Panduan Penggunaan**: User manual & tutorial.

---

## 5. Use Case Portal Produksi

### 5.1 Ringkasan

- **Dashboard Produksi:** KPI produksi real-time — WO aktif, bundle WIP, downtime, andon.
- **Papan Lini Produksi (Line Board):** Status tiap lini produksi per shift.
- **Penjadwalan APS (Gantt):** Advanced Planning & Scheduling dengan drag-and-drop Gantt chart.

### 5.2 Eksekusi

#### Order Produksi (`rahaza_orders`)
**Flow:**
1. Admin/sales membuat order baru → pilih customer, tambah line items (model × size × qty × harga).
2. Simpan → sistem generate `order_number` otomatis (format `ORD-YYYY-NNNN`).
3. Status order: `draft` → `confirmed` → `in_production` → `completed` → `closed`.

#### Work Order (`rahaza_work_orders`)
**Flow (dari Order):**
1. Order `confirmed` → klik **Generate Work Order** pada tiap line item.
2. Sistem membuat satu WO per item, mengadopsi BOM (Bill of Materials) model+size.
3. WO status: `draft` → `released` → `in_progress` → `completed`.
4. Saat WO dirilis:
   - Snapshot BOM dicatat di WO (freeze price & ratio).
   - Material reservation (opsional).
   - Event log dicatat di `rahaza_wip_events`.

#### Penelusuran Bundle (`rahaza_bundles`)
Bundle = unit produksi fisik. Satu WO bisa dipecah jadi beberapa bundle (misal WO 200 pcs → 4 bundle @ 50 pcs).

**Flow:**
1. Setelah rajut selesai, operator mencetak QR bundle → ditempel ke fisik bundle.
2. Scan QR di tiap proses (Linking, Sewing, QC, Steam, Packing) → status bundle auto-update.
3. Sistem mencatat timestamp & operator yang mengerjakan.
4. Closed-loop rework: bundle reject dari QC → kembali ke proses terkait dengan tracking.

#### Papan Rework
Menampilkan seluruh bundle yang sedang rework — termasuk SLA (berapa lama sudah dalam antrian rework).

#### Assign Lini Hari Ini
**Flow:**
1. Supervisor buka modul `Assign Lini Hari Ini`.
2. Pilih lini (LINE-A, LINE-B, LINE-C) + tanggal + shift.
3. Tetapkan operator yang bekerja di lini tersebut.
4. Tetapkan target qty harian.
5. Sistem akan membandingkan `actual_qty` vs `target_qty` untuk OEE calculation.

### 5.3 Monitoring

- **Dashboard OEE:** Overall Equipment Effectiveness — Availability × Performance × Quality per lini.
- **Analitik Rework:** Root cause analysis — jenis defect paling sering, operator/lini penyebab.
- **Pengaturan Alert:** Rule-based alert (mis. "bundle diam > 2 jam di proses X → alert ke supervisor").
- **Papan Andon:** Display besar untuk lantai produksi — line down, maintenance, dll.

### 5.4 Pengiriman

**Flow Buat Surat Jalan:**
1. WO `completed` → menu **Pengiriman → + Buat Surat Jalan**.
2. Pilih WO, masukkan qty kirim (bisa parsial), tanggal kirim.
3. Simpan → sistem:
   - Generate `shipment_number` (format `SJ-YYYYMM-NNNN`).
   - Trigger **auto-post JE COGS** (lihat §10).
   - Update status order jadi `completed` kalau semua WO sudah ship.

### 5.5 Mode TV (Lantai Produksi)

URL `/tv` — tampilan full-screen untuk monitor lantai produksi. Menampilkan status lini, alert aktif, target vs actual hari ini.

### 5.6 Eksekusi Proses (6 tahapan rajut + 2 rework)

```
 1. RAJUT    → 2. LINKING → 3. SEWING → 4. QC → 5. STEAM → 6. PACKING
                                  ↑
                                  └─ R. WASHER / R. SONTEK (rework path)
```

Tiap tahapan punya modul sendiri yang menampilkan antrian bundle, scan QR, dan catat qty reject.

### 5.7 Master Data Produksi

| Modul | Deskripsi |
|---|---|
| Gedung & Zona | Lokasi fisik (Gedung A/B, Zona Rajut/Linking/QC dst) |
| Proses Produksi | Definisi 6+2 proses |
| Shift Kerja | Shift Pagi (07:00–15:00), Malam (15:00–23:00), dst |
| Mesin Rajut | Master mesin (Shima Seiki, Stoll, dll) + gauge + kapasitas |
| Lini Produksi | LINE-A, LINE-B, LINE-C (mapped ke process + lokasi) |
| Karyawan & Operator | Master karyawan dengan skema upah |
| Model Produk | Model baju (Sweater Basic, Cardigan, dll) |
| Ukuran (Size) | S, M, L, XL |
| BOM Produk | Bill of Materials per model × size (benang + aksesoris + qty) |
| SOP Produksi | Standard Operating Procedure per proses |

---

## 6. Use Case Portal Gudang

### 6.1 Dashboard Gudang

- Total lokasi, total SKU, total stok.
- Penerimaan tertunda, alert stok di bawah minimum.
- Pergerakan stok terbaru.

### 6.2 Inventori

#### Master Material (`rahaza_materials`)
Benang, aksesoris, material bantuan.

**Field penting:** code, name, type (yarn/accessory), unit (kg/pcs), unit_cost, min_stock, max_stock.

#### Stok & Pergerakan (`rahaza_material_stock`, `rahaza_material_movements`)
- Stok per (material × location).
- Log movements: receive, issue, transfer, adjust.

#### Material Issue (WO) (`rahaza_material_issues`)
**Flow:**
1. Supervisor pilih WO yang akan diproduksi.
2. Sistem baca BOM snapshot WO → hitung kebutuhan material.
3. Operator gudang scan/pilih material → confirm issue qty per lokasi.
4. Simpan → sistem:
   - Kurangi `rahaza_material_stock`.
   - Catat `rahaza_material_movements` dengan `movement_type=issue`.
   - Auto-post JE (DR Biaya Bahan / CR Persediaan).

### 6.3 Operasional Gudang

#### Penerimaan Barang (`rahaza_material_movements` type=receive)
**Flow:**
1. Vendor kirim barang → staff gudang buka **Penerimaan Barang**.
2. Input: supplier, material, qty, unit_cost, lokasi penerimaan, PO reference.
3. Simpan → sistem:
   - Tambah ke `rahaza_material_stock`.
   - Catat movement.
   - Auto-post JE (DR Persediaan / CR Hutang Usaha).

#### Put-Away
Memindahkan stok dari **Receiving Bay** ke **Storage Bin** yang sesuai.

#### Stok Opname (`rahaza_material_stock_opname`)
**Flow:**
1. Buat sesi opname baru (per lokasi atau per kategori).
2. Print count sheet.
3. Staff lapangan hitung fisik → input `counted_qty`.
4. Sistem hitung variance = `counted_qty - system_qty`.
5. Supervisor approve → sistem buat `movement_type=adjust` untuk variance (auto-post JE ke akun Loss/Gain Inventory).

#### Lokasi / Bin (`rahaza_locations`)
Master lokasi fisik (Gedung A Zona Benang, Gedung B Zona FG, dll).

#### Aksesoris (`accessories`)
Master aksesoris garment — label, kancing, resleting, dll.

---

## 7. Use Case Portal Keuangan

### 7.1 Dashboard Keuangan

Menampilkan quick-link dikelompokkan:
- **Operasional:** Invoice AR, Hutang AP, Pembayaran, Kas & Bank.
- **Analisis & Rekap:** HPP/Costing, Rekap Keuangan.
- **Akuntansi:** CoA, Jurnal, Neraca Saldo, Laba Rugi, Arus Kas, Daftar Jurnal.

### 7.2 Piutang (AR)

#### Invoice Penjualan AR (`rahaza_ar_invoices`)
**Flow Buat Invoice Manual:**
1. **Piutang (AR) → Invoice Penjualan AR → + Buat**.
2. Pilih customer, order reference (opsional), tanggal, due_date.
3. Tambah line items (description, qty, unit, price).
4. Sistem hitung: subtotal + PPN 11% = total.
5. Simpan → status `sent` → **auto-post JE** (DR Piutang / CR Pendapatan / CR PPN Output).

**Flow Auto dari Order:**
1. Order `confirmed` → sistem membuat AR invoice draft otomatis.
2. Admin review → kirim ke customer (status `sent`).

**Status invoice:** `draft` → `sent` → `partial` → `paid` / `overdue`.

#### Daftar Piutang
Menampilkan semua AR invoice yang belum lunas, sortable by due_date, overdue highlight.

#### Rekap Invoice
Ringkasan: total issued, total paid, total outstanding per periode.

### 7.3 Hutang (AP)

#### Hutang Vendor (`rahaza_ap_invoices`)
Sama seperti AR tapi arah sebaliknya.

**Flow:**
1. Vendor kirim invoice → staff input di **Hutang Vendor → + Buat**.
2. Attach PDF scan (optional), isi detail.
3. Simpan → auto-post JE (DR Beban/Persediaan / CR Hutang Usaha / DR PPN Masukan).

#### Invoice Manual
Untuk invoice yang tidak linked ke PO — misal tagihan listrik, service.

#### Approval Invoice
**Flow approval multi-step:**
1. Invoice submitted oleh admin keuangan.
2. Supervisor review → `pending_approval`.
3. Owner/direksi approve → `approved` → siap dibayar.
4. Kalau reject → kembali ke `draft` dengan catatan.

### 7.4 Kas & Pembayaran

#### Kas & Bank (`rahaza_cash_accounts`)
Master akun kas/bank:
- CASH-BSR · Kas Besar
- BANK-BCA · Bank BCA
- BANK-MDR · Bank Mandiri

**Saldo otomatis** dihitung dari `opening_balance` + cash_movements.

#### Pembayaran (`rahaza_cash_movements`)
**Flow Bayar AR (terima pembayaran customer):**
1. Customer transfer → **Pembayaran → + Catat Pembayaran**.
2. Pilih invoice AR, akun penerima (BANK-BCA/dll), tanggal, jumlah.
3. Sistem:
   - Update `paid_amount` di invoice.
   - Jika lunas → status `paid`; kalau sebagian → `partial`.
   - Tambah ke `current_balance` cash account.
   - Auto-post JE (DR Bank / CR Piutang).

**Flow Bayar AP (bayar ke vendor):**
Sama tapi arah sebaliknya.

#### Pengeluaran (`rahaza_expenses`)
**Flow OPEX (contoh: listrik, ATK):**
1. **Pengeluaran → + Buat**.
2. Isi deskripsi, kategori, amount, cost center, akun GL debit, akun bayar.
3. Simpan → auto-post JE (DR Biaya / CR Bank).

### 7.5 Biaya & HPP

#### Cost Center (`rahaza_cost_centers`)
Pusat biaya untuk tracking: Produksi, Marketing, Admin, Keuangan.

#### HPP / Costing
**Flow hitung HPP per WO:**
1. Pilih WO `completed`.
2. Sistem agregat:
   - Material cost (dari material_issues WO terkait).
   - Labor cost (dari payslip × jam kerja di WO).
   - Overhead (allocated berdasarkan rule).
3. HPP per pcs = total cost / qty produced.
4. Snapshot ke `rahaza_hpp_snapshots` → jadi basis COGS di neraca.

#### Rekap Keuangan
Dashboard analitik margin, trend revenue, top customer, dll.

### 7.6 Akuntansi

Bagian ini dikelompokkan dalam **3 sub-header** di sidebar:

#### Master & Jurnal
- **Chart of Accounts (CoA)** (`rahaza_coa_accounts`): Struktur akun PSAK/SAK-ETAP. Format code: `1-1301` (aset-piutang-usaha).
- **Jurnal Umum**: Input jurnal manual double-entry (DR = CR).
- **Daftar Jurnal**: Semua JE terposting dengan filter tanggal, akun, reference.
- **Posting Profiles** (`rahaza_posting_profiles`): Mapping `event_type → CoA code`. Digunakan untuk auto-post.
- **Periode Akuntansi** (`rahaza_periods`): Periode bulanan dengan status `open` / `closed` / `locked`.

#### Laporan Keuangan
- **Neraca Saldo (TB)**: Trial balance — opening + period movement + ending.
- **Buku Besar (GL)**: Detail per akun dengan drill-down ke JE.
- **Laba Rugi (P&L)**: Revenue - Expenses = Net Profit (periodik).
- **Neraca**: Assets = Liabilities + Equity.

#### Arus Kas & Aging
- **Laporan Arus Kas**: Operating / Investing / Financing (direct method dari cash_movements).
- **Aging Hutang (AP)**: AP outstanding di-bucket umur (0-30, 31-60, 61-90, 90+).

---

## 8. Use Case Portal SDM (HR)

### 8.1 Dashboard SDM

Ringkasan karyawan aktif, absensi hari ini, payroll status.

### 8.2 Absensi Harian (`rahaza_attendance_events`)

**Flow catat absensi:**
1. **Absensi Harian → + Tambah** (atau upload CSV dari mesin finger-print).
2. Isi: tanggal, employee, shift, status (hadir/izin/sakit/absen), check-in, check-out.
3. Simpan → sistem hitung `hours_worked`, `overtime_hours`.

### 8.3 Profil Gaji Karyawan (`rahaza_payroll_profiles`)

Master skema upah per karyawan:
- `bulanan`: Gaji tetap bulanan.
- `mingguan`: Gaji mingguan (rekap 4× per bulan).
- `borongan_pcs`: Rp × pcs output (auto dari `rahaza_wip_events`).
- `borongan_jam`: Rp × jam kerja.

### 8.4 Penggajian & Slip (`rahaza_payroll_runs`, `rahaza_payslips`)

**Flow proses payroll bulanan:**
1. **Penggajian & Slip → + Run Baru**.
2. Pilih periode (from/to, biasanya 1 bulan).
3. Sistem agregat data per karyawan:
   - **Bulanan:** ambil `base_rate`.
   - **Mingguan:** `base_rate × jumlah minggu`.
   - **Borongan pcs:** jumlah pcs dari WIP events × rate.
   - **Borongan jam:** total jam absensi × rate.
4. Hitung deductions: BPJS 2%, PPh 21 (berdasarkan PTKP), kasbon.
5. Net = Gross - Deductions.
6. Review → **Finalize** → status `finalized`.
7. Auto-post JE (DR Beban Gaji / CR Hutang Gaji).
8. Slip gaji bisa dicetak PDF per karyawan.

---

## 9. Flow Integrasi Antar Modul

### 9.1 Dari Order ke Uang Masuk (AR Flow)

```
Order Dibuat (Mgmt/Sales)
   ↓
Work Orders Generated per item
   ↓
Material Issued ke WO (Warehouse)
   ↓  [auto-post JE: DR Biaya Bahan / CR Persediaan]
Production dimulai → Bundle dibuat
   ↓
Bundle selesai di Packing → WO completed
   ↓
Surat Jalan dibuat (Shipment)
   ↓  [auto-post JE: DR COGS / CR Persediaan FG]
AR Invoice dibuat (otomatis atau manual)
   ↓  [auto-post JE: DR Piutang / CR Pendapatan / CR PPN Output]
Customer bayar
   ↓  [auto-post JE: DR Bank / CR Piutang]
```

### 9.2 Dari PO ke Uang Keluar (AP Flow)

```
Penerimaan Barang dari Vendor (Warehouse)
   ↓  [auto-post JE: DR Persediaan / CR Hutang]
AP Invoice dari vendor masuk (dicocokkan dengan PO)
   ↓
Invoice di-approve
   ↓
Pembayaran ke vendor
   ↓  [auto-post JE: DR Hutang / CR Bank]
```

### 9.3 Dari Absensi ke Payroll

```
Absensi harian per karyawan (HR)
   +
WIP events (output pcs) dari Bundle execution (Produksi)
   ↓
Payroll Run bulanan
   ↓  [auto-post JE: DR Beban Gaji / CR Hutang Gaji Karyawan]
Pembayaran gaji (Finance → Pembayaran)
   ↓  [auto-post JE: DR Hutang Gaji / CR Bank]
```

### 9.4 HPP (Costing) Flow

```
Material Issues (kumpulan bahan baku untuk WO)
   +
Labor Cost (slip gaji operator yang kerja di WO)
   +
Overhead Allocation (% cost center Produksi)
   ↓
HPP Snapshot per WO → HPP per pcs
   ↓
Jadi basis COGS saat shipment
```

---

## 10. Flow Akuntansi Otomatis (Auto-posting)

Sistem mendukung **auto-posting journal entries** berdasarkan **Posting Profiles** yang mapping `event_type` ke akun CoA.

### 10.1 Event Types yang Di-auto-post

| Event Type | Trigger | DR Account | CR Account |
|---|---|---|---|
| `ar_invoice` | AR invoice issued | 1-1301 Piutang Usaha | 4-1100 Pendapatan + 2-1400 PPN Output |
| `ar_payment` | Pelunasan AR | 1-1201 Bank | 1-1301 Piutang |
| `ap_invoice` | AP invoice received | 5-1100 Biaya + 1-1501 PPN Masukan | 2-1100 Hutang Usaha |
| `ap_payment` | Bayar AP | 2-1100 Hutang | 1-1201 Bank |
| `expense` | Pengeluaran OPEX | 6-XXXX (sesuai kategori) | 1-1201 Bank |
| `payroll_finalize` | Payroll run finalize | 5-2100 Beban Gaji | 2-1200 Hutang Gaji |
| `inventory_receive` | Terima material | 1-1401 Persediaan | 2-1100 Hutang |
| `inventory_issue` | Material issued ke WO | 5-1200 Biaya Bahan WIP | 1-1401 Persediaan |
| `inventory_adjust` | Stock adjustment | 6-1900 Loss Inv | 1-1401 Persediaan |
| `cogs_shipment` | Surat Jalan dispatched | 5-1000 COGS | 1-1404 Persediaan FG |

### 10.2 Cara Kerja

1. Saat event transaksional terjadi (mis. AR invoice dikirim), sistem memanggil fungsi `post_ar_invoice()` di `rahaza_posting.py`.
2. Fungsi membaca mapping dari `rahaza_posting_profiles`.
3. Sistem membuat dokumen di `rahaza_journal_entries` + lines di `rahaza_journal_lines`.
4. JE di-stamp ke periode yang matching tanggal event. Kalau periode `locked`, posting ditolak.
5. Total debit = total credit (dipastikan oleh helper).
6. Kalau posting gagal (mis. CoA tidak ada), error disimpan di field `post_error` di dokumen sumber → admin bisa retry.

### 10.3 Manual Jurnal Umum

Kasus yang butuh JE manual:
- Koreksi / adjustment jurnal.
- Depreciation (belum di-automate).
- Opening balance migrasi.
- Reklas antar akun.

**Flow:**
1. **Jurnal Umum → + Buat**.
2. Pilih tanggal, description, reference.
3. Tambah lines: DR account + amount ATAU CR account + amount.
4. Sistem memastikan total DR = total CR sebelum simpan.
5. Simpan → masuk ke `rahaza_journal_entries` dengan `source_module = "manual"`.

---

## 11. Flow Tutup Periode

### 11.1 Prosedur Tutup Bulan

1. **Review** semua transaksi bulan berjalan:
   - Cek semua AR/AP invoice sudah ter-post.
   - Cek payroll run sudah finalized.
   - Cek material issues & receipts balanced.
2. **Stock Opname** (disarankan bulanan) — adjust variance.
3. **Tutup Periode**:
   - Buka **Periode Akuntansi → pilih bulan → Close**.
   - Sistem ubah status → `closed`.
   - Semua JE baru dengan tanggal di periode ini akan **ditolak** (kecuali adjusting entry oleh supervisor).
4. **Generate Laporan**:
   - Neraca Saldo akhir periode.
   - Laba Rugi bulan.
   - Neraca.
   - Arus Kas.
   - Export PDF/Excel untuk arsip.

### 11.2 Lock Periode

- Setelah audit internal, supervisor bisa set `locked: true` → bahkan adjustment tidak bisa lagi.
- Hanya superadmin yang bisa unlock (butuh alasan tertulis).

### 11.3 Tutup Tahun

- Tutup bulan Desember seperti biasa.
- Sistem otomatis:
  - Close semua akun Revenue & Expense ke Retained Earnings (akun 3-XXXX).
  - Reset saldo berjalan akun P&L.
- Generate laporan tahunan (Balance Sheet, P&L, Equity Changes, Cash Flow).

---

## 12. Seed Data & Reset Demo

Untuk keperluan testing/demo, tersedia endpoint admin:

### 12.1 Purge Demo Data

```bash
curl -X POST https://<host>/api/rahaza/admin/purge-demo-data \
  -H "Authorization: Bearer <superadmin_token>"
```

**Yang dihapus:** semua master data transaksional (orders, WO, bundles, journals, invoices, attendance, payroll, materials, dll).
**Yang DIPERTAHANKAN:** users, roles, permissions, company_settings.

### 12.2 Seed Demo Data (3 Bulan)

```bash
curl -X POST https://<host>/api/rahaza/admin/seed-demo-data \
  -H "Authorization: Bearer <superadmin_token>"
```

**Menghasilkan:**
- Master: 6 customers, 5 models, 4 sizes, 8 materials, 18 employees, 6 mesin, 3 line, 4 cost center, 3 cash account.
- 4 bulan akuntansi (periode open).
- 15 orders spread 3 bulan terakhir.
- 47 Work Orders.
- 120 bundles di berbagai stage.
- 15 AR invoices, 10 AP invoices.
- 18 expenses OPEX.
- Attendance harian per karyawan.
- 3 payroll runs bulanan.
- 15 shipments dispatched.
- 231 line assignments.
- ~52 Journal Entries (auto-posted).

**Setelah seed:**
- Trial Balance balanced.
- P&L, Neraca, Cash Flow siap di-drill.
- Dashboard KPI tampil penuh.

### 12.3 Reset & Seed (Convenience)

```bash
curl -X POST https://<host>/api/rahaza/admin/reset-and-seed \
  -H "Authorization: Bearer <superadmin_token>"
```

Sekali panggil → purge + seed langsung.

---

## 13. FAQ Operasional

### Q1: Saya lupa password, bagaimana?
A: Hubungi superadmin untuk reset via **Portal Manajemen → Manajemen Pengguna → [user] → Reset Password**.

### Q2: Kenapa Trial Balance tidak balance?
A: Kemungkinan ada JE manual yang DR ≠ CR. Cek di **Daftar Jurnal** filter `unbalanced: true` (atau manually cek yang terakhir diinput).

### Q3: Order tidak bisa di-close, kenapa?
A: Semua WO terkait order harus `completed` dulu, dan total qty shipped = total qty order. Cek di **Order → detail → tab Shipments**.

### Q4: Auto-post JE gagal, apa yang harus dicek?
A:
1. Cek apakah **Posting Profile** untuk event tersebut sudah di-configure dengan CoA code yang valid.
2. Cek apakah CoA code yang direferensi ada di `rahaza_coa_accounts`.
3. Cek apakah periode masih `open`.
4. Cek field `post_error` di dokumen sumber untuk detail error.
5. Retry dari **Posting Profiles → Retry Failed** (jika ada) atau manual input JE.

### Q5: HPP satu WO kok naik/turun drastis?
A: HPP dihitung dari material cost + labor cost + overhead. Cek:
- Apakah unit_cost material saat receive berubah (FIFO/AVG)?
- Apakah overhead allocation rate berubah?
- Apakah ada rework yang meningkatkan material/labor consumption?

### Q6: Bagaimana cara menambah role baru?
A: **Portal Manajemen → Sistem → Manajemen Peran → + Buat**. Lalu atur permission di **Matriks Hak Akses**.

### Q7: Data saya hilang setelah demo dihapus?
A: Endpoint `purge-demo-data` HANYA untuk environment demo/staging. Di produksi, endpoint ini harus **di-disable** atau dibatasi ke superadmin tertentu. Selalu backup MongoDB sebelum purge.

### Q8: Bisa integrasi dengan sistem lain (Accurate, SAP)?
A: Belum native. Roadmap Phase 20C (AI Layer) atau Phase Integrasi (belum dijadwalkan) akan menambahkan REST/CSV export ke format standar.

### Q9: Apakah mendukung multi-currency?
A: Saat ini single-currency (IDR). Multi-currency masuk backlog enhancement.

### Q10: Bagaimana audit trail?
A: Semua aksi (login, create, update, delete, approve) dicatat di `activity_logs`. Akses via **Portal Manajemen → Sistem → Log Aktivitas**.

---

## Referensi Cepat

| Kebutuhan | Menu |
|---|---|
| Cek KPI bisnis hari ini | Portal Manajemen → Dashboard Eksekutif |
| Bikin order baru | Portal Produksi → Order Produksi → + Tambah |
| Input invoice customer | Portal Keuangan → Piutang → Invoice Penjualan AR |
| Proses payroll bulanan | Portal SDM → Penggajian & Slip → + Run Baru |
| Terima barang dari vendor | Portal Gudang → Penerimaan Barang |
| Tutup bulan | Portal Keuangan → Periode Akuntansi → Close |
| Lihat neraca | Portal Keuangan → Akuntansi → Laporan Keuangan → Neraca |
| Reset demo data | `POST /api/rahaza/admin/reset-and-seed` |

---

**Dokumen ini akan diperbarui seiring penambahan fitur.** Untuk pertanyaan teknis, hubungi tim IT. Untuk pertanyaan bisnis / akuntansi, hubungi Controller/Finance Manager.

*— End of document —*
