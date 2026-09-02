# Database STATCHECK — Phase 1

Phase 1 memiliki tabel `users` sebagai fondasi autentikasi.

| Kolom | Tipe | Keterangan |
|---|---|---|
| id | UUID | Primary key |
| nama | VARCHAR(150) | Nama pengguna |
| nik | VARCHAR(50) | Identitas login unik |
| user_level | VARCHAR(30) | Role pengguna |
| fungsi | VARCHAR(150) | Fungsi/unit kerja |
| password_hash | VARCHAR(255) | Hash Argon2 |
| is_active | BOOLEAN | Status akun |
| created_at | TIMESTAMPTZ | Waktu dibuat |
| updated_at | TIMESTAMPTZ | Waktu diperbarui |

## Tabel Phase 2

- `indicators`: master indikator, kategori, satuan default, fungsi, dan status.
- `brs`: registrasi BRS, jadwal rilis, PJK, supervisor, dan status workflow.
- `brs_team`: anggota tim penyusun pada setiap BRS.
- `brs_data`: nilai indikator, periode, satuan, analisis, dan fenomena.
