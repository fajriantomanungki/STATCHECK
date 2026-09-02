# Arsitektur STATCHECK — Phase 3

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

Phase 3 menambahkan pengelolaan dokumen:

```text
Upload PDF/PPTX/DOCX → Local Storage
         │
         └──> Text Extractor → documents + document_contents
```

File asli disimpan pada `backend/uploads/`. Metadata dan teks hasil ekstraksi
disimpan di PostgreSQL. Pemisahan ini memungkinkan file tetap dapat diunduh dan
teks digunakan oleh mesin STATCHECK pada Phase 4.
