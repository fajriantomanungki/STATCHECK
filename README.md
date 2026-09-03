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

## Phase 4 — Automatic Check dan PJK Review (ditingkatkan pada Phase 8)

Mesin pemeriksaan Phase 8 menyediakan:

- Pemeriksaan langsung terhadap tiga dokumen aktif tanpa menjadikan data input sebagai acuan
- Normalisasi angka Indonesia seperti `1.007,74`, `52,31`, dan `27.073`
- Penyaringan nomor BRS, kode dokumen, tanggal rilis, nomor halaman, dan metadata lain
- Pencocokan angka berdasarkan kemiripan konteks indikator dan satuan
- Perbandingan BRS/Bahan Publikasi ↔ Bahan Paparan, BRS/Bahan Publikasi ↔ Narasi
  Pimpinan, serta Bahan Paparan ↔ Narasi Pimpinan
- Peringatan apabila satu konteks angka ditemukan pada dua dokumen tetapi tidak
  memperoleh pasangan pada dokumen ketiga
- Satu temuan indikator menampilkan nilai dari ketiga dokumen secara berdampingan
- Pemeriksaan bahasa berbasis aturan untuk spasi, tanda baca, kata berulang,
  format persen, nama bulan, serta beberapa frasa tidak efektif
- Skor kelengkapan tiga dokumen, konsistensi angka, bahasa, dan skor keseluruhan
- Klasifikasi temuan `error`, `warning`, dan `suggestion`
- Tindak lanjut PJK: sudah diperbaiki, data dikonfirmasi benar, atau diabaikan
- Riwayat pemeriksaan dan audit trail review

Mesin `rules-v2.1-indicators` bekerja sepenuhnya lokal. Hasilnya merupakan alat bantu quality
control; keputusan akhir tetap dilakukan PJK.

## Phase 5 — Approval Workflow

Phase 5 menyediakan:

- Pengiriman hasil pemeriksaan PJK ke Supervisor
- Pemeriksaan, persetujuan, atau pengembalian revisi oleh Supervisor
- Persetujuan akhir atau pengembalian revisi oleh Kepala BPS
- Validasi role dan status pada setiap perubahan workflow
- Catatan wajib untuk setiap keputusan revisi
- Audit trail lengkap berisi pengguna, keputusan, status asal/tujuan, dan waktu
- Status akhir `release_ready` untuk BRS yang telah disetujui Kepala BPS

Akun development Kepala BPS tersedia menggunakan nilai
`INITIAL_KA_BPS_NIK` dan `INITIAL_KA_BPS_PASSWORD` pada `.env.example`.

Temuan STATCHECK harus seluruhnya ditindaklanjuti sebelum PJK dapat mengirim BRS
ke Supervisor. Setelah BRS dikembalikan, PJK memperbaiki data/dokumen dan
menjalankan ulang STATCHECK untuk memulai kembali alur persetujuan.

## Phase 6 — Release Center

Phase 6 menyediakan:

- Registrasi kegiatan berdasarkan tanggal, waktu, tempat, dan judul rilis
- Pemilihan beberapa BRS berstatus `release_ready` dengan jadwal yang sama
- Pencegahan satu BRS terdaftar pada lebih dari satu kegiatan rilis
- Pengelolaan daftar undangan: nama, instansi, jabatan, nomor HP, dan email
- Workflow kegiatan `draft` → `ongoing` → `completed`
- Perubahan otomatis status seluruh BRS menjadi `released` ketika kegiatan selesai
- Ringkasan BRS siap rilis, BRS dirilis, dan kegiatan rilis pada dashboard
- Fondasi tabel Q&A dan notulen untuk Phase 7

Pengelolaan Release Center dibatasi untuk Humas dan administrator. Akun
development Humas mengikuti `INITIAL_HUMAS_NIK` dan
`INITIAL_HUMAS_PASSWORD` pada `.env.example`.

## Phase 7 — Grounded AI Q&A dan Notulen

Phase 7 menyediakan:

- Layar operator Q&A dengan pilihan penanya dari daftar peserta
- Saran jawaban AI yang dibatasi pada Data Input, analisis, fenomena, dan teks
  dokumen resmi BRS dalam kegiatan
- Retrieval lokal berbasis relevansi pertanyaan dan pencatatan daftar sumber
- Kolom jawaban terpisah untuk AI, Supervisor, PJK, dan jawaban final
- Human review wajib; AI tidak pernah menetapkan jawaban resmi secara otomatis
- Pencegahan penyelesaian kegiatan jika masih ada pertanyaan tanpa jawaban final
- Editor pembukaan, pembahasan, catatan, dan kesimpulan notulen
- Penggabungan otomatis agenda, daftar BRS, peserta, serta Q&A final
- Generate dan download notulen dalam format DOCX dan PDF

Q&A manual dan notulen tetap berjalan tanpa layanan AI. Untuk mengaktifkan tombol
**Jawab dengan AI**, isi konfigurasi berikut pada `.env`, lalu restart backend:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.6-luna
```

Kunci API hanya dibaca backend dan tidak dikirim ke browser. Penggunaan OpenAI
API ditagihkan terpisah dari langganan ChatGPT.
