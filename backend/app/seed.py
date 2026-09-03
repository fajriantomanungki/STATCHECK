from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.indicator import Indicator
from app.models.user import User

DEFAULT_INDICATORS = [
    ("Inflasi", "Harga", "persen", "Statistik Distribusi"),
    ("Tingkat Penghunian Kamar", "Pariwisata", "persen", "Statistik Distribusi"),
    ("Perjalanan Wisatawan Nusantara", "Pariwisata", "ribu perjalanan", "Statistik Distribusi"),
    ("Nilai Tukar Petani", "Pertanian", "indeks", "Statistik Produksi"),
]


def seed_admin() -> None:
    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.nik == settings.initial_admin_nik))
        if not existing:
            db.add(User(
                nama=settings.initial_admin_name,
                nik=settings.initial_admin_nik,
                user_level="admin",
                fungsi="Administrator Sistem",
                password_hash=get_password_hash(settings.initial_admin_password),
            ))
        supervisor = db.scalar(select(User).where(User.nik == settings.initial_supervisor_nik))
        if not supervisor:
            db.add(User(
                nama=settings.initial_supervisor_name,
                nik=settings.initial_supervisor_nik,
                user_level="supervisor",
                fungsi="Pemeriksa BRS",
                password_hash=get_password_hash(settings.initial_supervisor_password),
            ))
        ka_bps = db.scalar(select(User).where(User.nik == settings.initial_ka_bps_nik))
        if not ka_bps:
            db.add(User(
                nama=settings.initial_ka_bps_name,
                nik=settings.initial_ka_bps_nik,
                user_level="ka_bps",
                fungsi="Pimpinan",
                password_hash=get_password_hash(settings.initial_ka_bps_password),
            ))
        humas = db.scalar(select(User).where(User.nik == settings.initial_humas_nik))
        if not humas:
            db.add(User(
                nama=settings.initial_humas_name,
                nik=settings.initial_humas_nik,
                user_level="humas",
                fungsi="Diseminasi dan Layanan Statistik",
                password_hash=get_password_hash(settings.initial_humas_password),
            ))
        for nama, kategori, satuan, fungsi in DEFAULT_INDICATORS:
            indicator = db.scalar(select(Indicator).where(Indicator.nama_indikator == nama))
            if not indicator:
                db.add(Indicator(
                    nama_indikator=nama,
                    kategori=kategori,
                    satuan_default=satuan,
                    fungsi=fungsi,
                ))
        db.commit()


if __name__ == "__main__":
    seed_admin()
