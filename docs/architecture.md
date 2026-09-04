# Arsitektur STATCHECK — Phase 7

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
teks digunakan oleh mesin STATCHECK pada Phase 8.

Phase 8 menjalankan dua jalur pemeriksaan lokal:

```text
BRS/Bahan Publikasi ↔ Bahan Paparan ↔ Narasi Pimpinan
                         │
                         ├──> Pencocokan konteks + perbandingan angka
Teks Tiap Halaman ──────┴──> Aturan Bahasa
                                      │
                                      └──> Skor + Temuan + Review PJK
```

Mesin pemeriksaan tidak menggunakan tabel data input sebagai nilai acuan dan
tidak memanggil layanan AI eksternal. Nomor dokumen dan tanggal disaring sebelum
angka dikelompokkan berdasarkan konteks indikator dan periode terdekat. Hanya
kelompok yang muncul pada minimal dua dokumen yang dibandingkan; indikator yang
hanya muncul sekali diabaikan. Setiap temuan menyimpan nilai dan kutipan dari dua
atau tiga dokumen yang benar-benar dibandingkan. Normalisasi angka, pencocokan
konteks/periode, dan aturan EYD dibuat deterministik agar hasil dapat diuji dan
dijelaskan. Untuk perbedaan pada tiga dokumen, nilai mayoritas menjadi acuan dan
dokumen penyimpang ditandai. Jika hanya dua dokumen memiliki nilai berbeda,
keduanya ditandai perlu verifikasi karena sumber yang benar belum dapat ditentukan.

Phase 5 menambahkan state machine persetujuan:

```text
PJK Review → Supervisor Review → Kepala BPS Review → Release Ready
                    │                    │
                    └─ Revisi ke PJK ────┘
```

Perubahan status hanya dilakukan melalui endpoint aksi yang spesifik. Backend
memvalidasi role, pengguna yang ditetapkan pada BRS, status asal, kelengkapan
tindak lanjut temuan, serta kewajiban catatan revisi. Setiap transisi disimpan
ke tabel `approvals` sebelum ditampilkan pada timeline frontend.

Phase 6 menambahkan agregasi kegiatan rilis:

```text
BRS release_ready → Kegiatan Rilis → Daftar Peserta
                           │
                    Mulai → Selesai
                           │
                    BRS menjadi released
```

Humas/Admin menjadi pemilik operasi perubahan, sementara pengguna terautentikasi
lain dapat melihat agenda dan peserta. Q&A dan notulen memiliki struktur database
sejak Phase 6 agar Phase 7 dapat menambahkan proses AI tanpa migrasi ulang pada
entitas inti kegiatan.

Phase 7 menggunakan retrieval sederhana dan transparan:

```text
Pertanyaan → Data/Analisis/Fenomena + Dokumen Relevan
           → Konteks Terbatas → Responses API → Saran AI
           → Supervisor/PJK → Final Answer Manusia
```

Pencarian konteks dilakukan lokal dengan pencocokan token pertanyaan. Data input
terstruktur selalu diprioritaskan, sedangkan halaman/slide dokumen dirangking
berdasarkan relevansi dan dibatasi panjangnya sebelum dikirim. Daftar sumber
disimpan bersama jawaban agar operator dapat melakukan verifikasi.

Generator notulen menggabungkan metadata rilis, BRS, peserta, isi lembar kerja,
dan hanya Q&A yang sudah memiliki `final_answer`. DOCX dibuat dengan
`python-docx`, sementara PDF dibuat dengan PyMuPDF yang sudah digunakan pada
Phase 3.
