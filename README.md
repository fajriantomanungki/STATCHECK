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
