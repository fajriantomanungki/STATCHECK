# API STATCHECK — Phase 1

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
| GET | `/dashboard/summary` | Ringkasan Phase 2 | Bearer token |

Dokumentasi interaktif tersedia pada `/docs` ketika environment bukan production.
