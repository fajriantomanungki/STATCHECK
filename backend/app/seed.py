from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.user import User


def seed_admin() -> None:
    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.nik == settings.initial_admin_nik))
        if existing:
            return
        db.add(User(
            nama=settings.initial_admin_name,
            nik=settings.initial_admin_nik,
            user_level="admin",
            fungsi="Administrator Sistem",
            password_hash=get_password_hash(settings.initial_admin_password),
        ))
        db.commit()


if __name__ == "__main__":
    seed_admin()
