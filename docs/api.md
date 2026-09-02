# API STATCHECK — Phase 3

Base URL: `/api/v1`

| Method | Endpoint | Fungsi | Akses |
|---|---|---|---|
| GET | `/health` | Status layanan | Publik |
| POST | `/auth/login` | Login NIK dan password | Publik |
| GET | `/auth/me` | Profil pengguna aktif | Bearer token |
| POST | `/auth/logout` | Menutup sesi pada client | Bearer token |
| GET | `/users/options` | Pilihan pengguna aktif | Bearer token |
| GET/POST | `/indicators` | Daftar/tambah master indikator | Bearer token/Admin |
| PUT | `/indicators/{id}` | Perbarui master indikator | Admin |
| GET/POST | `/brs` | Daftar/registrasi BRS | Bearer token/PJK |
| GET/PUT/DELETE | `/brs/{id}` | Detail/perbarui/hapus BRS draft | Sesuai akses BRS |
| GET/POST | `/brs/{id}/data` | Daftar/tambah data indikator | Sesuai akses BRS |
| PUT/DELETE | `/brs/{id}/data/{data_id}` | Perbarui/hapus data indikator | PJK/Admin |
| GET | `/dashboard/summary` | Ringkasan BRS, data, dan dokumen | Bearer token |
| GET | `/brs/{id}/documents` | Dokumen aktif/riwayat versi BRS | Sesuai akses BRS |
| POST | `/brs/{id}/documents` | Upload dan ekstraksi dokumen | PJK/Admin |
| GET | `/documents/{id}` | Metadata dan teks hasil ekstraksi | Sesuai akses BRS |
| GET | `/documents/{id}/download` | Unduh file asli | Sesuai akses BRS |
| POST | `/documents/{id}/reextract` | Jalankan ulang ekstraksi teks | PJK/Admin |

Dokumentasi interaktif tersedia pada `/docs` ketika environment bukan production.

Upload menggunakan `multipart/form-data` dengan field `document_type` dan `file`.
Nilai `document_type` yang valid: `bahan_publikasi`, `bahan_paparan`, dan
`narasi_pimpinan`.
