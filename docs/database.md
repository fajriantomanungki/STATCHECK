# Database STATCHECK — Phase 7

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

## Tabel Phase 3

- `documents`: metadata file, jenis dokumen, versi, checksum, status, hasil
  ekstraksi, jumlah halaman, dan pengunggah.
- `document_contents`: teks hasil ekstraksi yang dipisahkan per halaman atau
  slide agar dapat ditelusuri kembali saat pemeriksaan.

Satu BRS memiliki maksimal satu dokumen aktif untuk setiap jenis. Ketika versi
baru diunggah, versi aktif sebelumnya berubah menjadi `archived`; file dan
metadata lama tetap tersedia sebagai audit trail.

## Tabel Phase 4

- `check_runs`: satu eksekusi pemeriksaan, ringkasan jumlah hasil, dan empat skor.
- `check_results`: detail temuan, nilai acuan/aktual, dokumen, halaman, konteks,
  saran, tingkat keparahan, dan status tindak lanjut.
- `check_reviews`: audit trail tindakan, catatan, pengguna, dan waktu review PJK.

Pemeriksaan ulang membuat `check_runs` baru sehingga hasil sebelumnya tidak
ditimpa dan tetap dapat digunakan sebagai riwayat.

## Tabel Phase 5

- `approvals`: audit trail keputusan PJK, Supervisor, dan Kepala BPS.

Setiap baris menyimpan `brs_id`, pengguna, level persetujuan, aksi, status asal,
status tujuan, catatan, dan waktu keputusan. Riwayat tidak ditimpa ketika BRS
dikembalikan atau dikirim ulang.

Status workflow Phase 5:

1. `pjk_review`
2. `pjk_submitted`
3. `supervisor_review`
4. `supervisor_approved` atau `supervisor_revision`
5. `ka_bps_review`
6. `release_ready` atau `ka_bps_revision`

## Tabel Phase 6

- `releases`: identitas, jadwal, lokasi, status, pembuat, dan waktu pelaksanaan.
- `release_brs`: relasi banyak BRS ke satu kegiatan rilis; `brs_id` unik.
- `guests`: daftar peserta dan informasi kontak kegiatan rilis.
- `qna`: fondasi pertanyaan serta jawaban AI, Supervisor, PJK, dan jawaban final.
- `minutes`: fondasi isi notulen dan lokasi file hasil generate.

Satu kegiatan dapat memiliki banyak BRS dan peserta. Satu BRS hanya boleh berada
pada satu kegiatan agar riwayat publikasi tidak ganda. Menghapus kegiatan yang
masih `draft` akan menghapus relasi dan peserta, tetapi tidak menghapus BRS.

## Perluasan Phase 7

Tabel `qna` ditambah metadata berikut:

- `ai_model`, `ai_sources`, dan `generated_at` untuk keterlacakan jawaban AI.
- `finalized_by` dan `finalized_at` untuk audit jawaban final manusia.

Tabel `minutes` ditambah `opening`, `discussion`, `notes`, `conclusion`,
`docx_file_path`, dan `pdf_file_path`. File hasil generate disimpan di local
storage, sedangkan isi dan metadata tetap tersimpan pada PostgreSQL.
