# STATCHECK

Sistem terintegrasi untuk mengelola, memeriksa, mengendalikan persetujuan, dan mendukung pelaksanaan rilis Berita Resmi Statistik.

## Struktur awal

- `frontend/` — Next.js + TypeScript + Tailwind CSS
- `backend/` — FastAPI + SQLAlchemy + Alembic
- `database/` — migrasi dan seed database
- `docs/` — dokumentasi arsitektur, database, dan API

## Phase 1 — Foundation

Phase 1 menyediakan:

- PostgreSQL dan Docker Compose
- FastAPI, SQLAlchemy, Alembic, serta dokumentasi OpenAPI
- Autentikasi JWT (`login`, `me`, dan `logout`)
- Next.js, TypeScript, Tailwind CSS
- Halaman login dan dashboard foundation
- Seed akun administrator dan pengujian API

### Menjalankan dengan Docker

```bash
cp .env.example .env
docker compose up --build
```

Frontend tersedia di `http://localhost:3000` dan dokumentasi API di
`http://localhost:8000/docs`.

Akun development awal mengikuti nilai `INITIAL_ADMIN_NIK` dan
`INITIAL_ADMIN_PASSWORD` pada `.env`. Ganti seluruh secret sebelum deployment.

## Phase 2 — BRS dan Master Indikator

Phase 2 menyediakan:

- Master indikator beserta kategori, satuan, fungsi, dan status aktif
- Registrasi dan perubahan identitas BRS
- Penetapan PJK, supervisor, serta tim penyusun
- Input, perubahan, dan penghapusan data indikator BRS
- Kolom analisis dan fenomena untuk setiap nilai indikator
- Ringkasan jumlah BRS, draft, indikator, dan data pada dashboard
- Pembatasan akses berdasarkan PJK, supervisor, tim, dan level pengguna

Akun development supervisor tersedia menggunakan nilai
`INITIAL_SUPERVISOR_NIK` dan `INITIAL_SUPERVISOR_PASSWORD` pada `.env.example`.

## Phase 3 — Dokumen dan Ekstraksi Teks

Phase 3 menyediakan:

- Upload Bahan Publikasi, Bahan Paparan, dan Narasi Pimpinan
- Dukungan file PDF, PPTX, dan DOCX hingga 25 MB
- Penyimpanan file lokal pada `backend/uploads/`
- Ekstraksi teks per halaman PDF, per slide PPTX, dan isi DOCX
- Status dan pesan kegagalan ekstraksi
- Versioning dokumen tanpa menghapus versi sebelumnya
- Pratinjau hasil ekstraksi dan unduh file dari halaman Dokumen BRS

Setiap perubahan dependency backend memerlukan pembangunan ulang container:

```bash
docker compose down
docker compose up --build
```

Ekstraksi Phase 3 membaca teks yang memang tertanam di dokumen. OCR untuk PDF
hasil scan dan pembacaan angka dari grafik akan ditambahkan pada tahap pemeriksaan
lanjutan bila dibutuhkan.
