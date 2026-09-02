# API STATCHECK — Phase 1

Base URL: `/api/v1`

| Method | Endpoint | Fungsi | Akses |
|---|---|---|---|
| GET | `/health` | Status layanan | Publik |
| POST | `/auth/login` | Login NIK dan password | Publik |
| GET | `/auth/me` | Profil pengguna aktif | Bearer token |
| POST | `/auth/logout` | Menutup sesi pada client | Bearer token |

Dokumentasi interaktif tersedia pada `/docs` ketika environment bukan production.
