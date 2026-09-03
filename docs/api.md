# API STATCHECK — Phase 6

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
| POST | `/brs/{id}/check` | Jalankan pemeriksaan otomatis | PJK/Admin |
| GET | `/brs/{id}/checks` | Riwayat pemeriksaan BRS | Sesuai akses BRS |
| GET | `/brs/{id}/checks/latest` | Hasil pemeriksaan terbaru | Sesuai akses BRS |
| GET | `/check-runs/{id}` | Detail satu pemeriksaan | Sesuai akses BRS |
| GET | `/checks/{id}` | Detail satu temuan | Sesuai akses BRS |
| POST | `/checks/{id}/review` | Simpan tindak lanjut PJK | PJK/Admin |
| GET | `/brs/{id}/approval` | Ringkasan dan audit trail persetujuan | Sesuai akses BRS |
| POST | `/brs/{id}/submit-supervisor` | PJK mengirim BRS ke Supervisor | PJK/Admin |
| POST | `/brs/{id}/supervisor/start-review` | Mulai pemeriksaan Supervisor | Supervisor/Admin |
| POST | `/brs/{id}/supervisor/approve` | Setujui BRS pada level Supervisor | Supervisor/Admin |
| POST | `/brs/{id}/supervisor/revision` | Kembalikan BRS untuk revisi | Supervisor/Admin |
| POST | `/brs/{id}/submit-ka-bps` | Kirim BRS yang disetujui ke Kepala BPS | PJK/Supervisor/Admin |
| POST | `/brs/{id}/ka-bps/approve` | Setujui BRS menjadi siap rilis | Kepala BPS/Admin |
| POST | `/brs/{id}/ka-bps/revision` | Kembalikan BRS untuk revisi | Kepala BPS/Admin |
| GET | `/releases/eligible-brs?tanggal_rilis=YYYY-MM-DD` | BRS siap rilis yang belum dijadwalkan | Bearer token |
| GET/POST | `/releases` | Daftar/registrasi kegiatan rilis | Bearer token/Humas/Admin |
| GET/PUT/DELETE | `/releases/{id}` | Detail/perbarui/hapus kegiatan draft | Bearer token/Humas/Admin |
| POST | `/releases/{id}/brs` | Tambah BRS siap rilis | Humas/Admin |
| DELETE | `/releases/{id}/brs/{brs_id}` | Keluarkan BRS dari kegiatan draft | Humas/Admin |
| POST | `/releases/{id}/start` | Mulai kegiatan rilis | Humas/Admin |
| POST | `/releases/{id}/complete` | Selesaikan kegiatan dan tandai BRS dirilis | Humas/Admin |
| GET/POST | `/releases/{id}/guests` | Daftar/tambah peserta | Bearer token/Humas/Admin |
| PUT/DELETE | `/releases/guests/{guest_id}` | Perbarui/hapus peserta | Humas/Admin |

Dokumentasi interaktif tersedia pada `/docs` ketika environment bukan production.

Upload menggunakan `multipart/form-data` dengan field `document_type` dan `file`.
Nilai `document_type` yang valid: `bahan_publikasi`, `bahan_paparan`, dan
`narasi_pimpinan`.

Review temuan menerima JSON dengan `action` bernilai `fixed`,
`confirmed_correct`, atau `ignored`, serta `note` opsional.

Endpoint keputusan menerima JSON `{"note": "..."}`. Catatan bersifat opsional
untuk pengiriman dan persetujuan, tetapi wajib untuk aksi `revision`. Setiap
endpoint hanya menerima status asal yang tepat agar tahapan tidak dapat dilompati.

Registrasi kegiatan menerima `tanggal_rilis`, `waktu_rilis`, `tempat`,
`judul_rilis`, dan array `brs_ids`. Semua BRS harus berstatus `release_ready`,
memiliki jadwal tanggal yang sama, dan belum terhubung ke kegiatan rilis lain.

Daftar peserta dapat diperbarui ketika kegiatan berstatus `draft` atau `ongoing`.
Setelah endpoint `complete` berhasil, kegiatan dan daftar peserta dikunci serta
status seluruh BRS di dalamnya berubah menjadi `released`.
