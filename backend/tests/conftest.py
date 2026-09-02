import os
import shutil
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_statcheck.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-with-at-least-32-characters"
os.environ["UPLOAD_DIR"] = "./test_uploads"

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.main import app
from app.models.user import User


@pytest.fixture(autouse=True)
def database():
    upload_dir = Path("./test_uploads")
    if upload_dir.exists():
        shutil.rmtree(upload_dir)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        db.add(User(
            nama="Admin Test", nik="admin", user_level="admin", fungsi="Test",
            password_hash=get_password_hash("Admin123!"),
        ))
        db.commit()
    yield
    Base.metadata.drop_all(bind=engine)
    if upload_dir.exists():
        shutil.rmtree(upload_dir)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
