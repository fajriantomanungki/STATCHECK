# Arsitektur STATCHECK — Phase 1

```text
Browser → Next.js (3000) → FastAPI (8000) → PostgreSQL (5432)
                              │
                              └── JWT Authentication
```

Semua komponen dijalankan sebagai satu monorepo melalui Docker Compose.

Phase 2 menambahkan lapisan domain berikut:

```text
Users ──> BRS ──> BRS Data ──> Master Indikator
           │
           └──> Tim Penyusun dan Supervisor
```
