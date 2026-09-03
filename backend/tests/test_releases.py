from datetime import date
import uuid

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.brs import BRS
from app.models.user import User


def prepare_release_data() -> tuple[str, str, str]:
    with SessionLocal() as db:
        admin = db.query(User).filter(User.nik == "admin").one()
        humas = User(
            nama="Humas Test", nik="humas", user_level="humas", fungsi="Diseminasi",
            password_hash=get_password_hash("Humas123!"),
        )
        viewer = User(
            nama="PJK Test", nik="pjk-release", user_level="pjk", fungsi="Distribusi",
            password_hash=get_password_hash("PjkRelease123!"),
        )
        db.add_all([humas, viewer])
        db.flush()
        ready = BRS(
            kode_brs="BRS-READY", nama_brs="Pariwisata Juli", waktu_rilis=date(2026, 9, 5),
            fungsi_pj="Distribusi", pjk_id=admin.id, status="release_ready",
        )
        draft = BRS(
            kode_brs="BRS-DRAFT", nama_brs="Inflasi Agustus", waktu_rilis=date(2026, 9, 5),
            fungsi_pj="Distribusi", pjk_id=admin.id, status="pjk_review",
        )
        other_date = BRS(
            kode_brs="BRS-OTHER", nama_brs="NTP Agustus", waktu_rilis=date(2026, 10, 1),
            fungsi_pj="Produksi", pjk_id=admin.id, status="release_ready",
        )
        db.add_all([ready, draft, other_date])
        db.commit()
        return str(ready.id), str(draft.id), str(other_date.id)


def login(client, nik: str, password: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"nik": nik, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def release_payload(brs_id: str) -> dict:
    return {
        "tanggal_rilis": "2026-09-05", "waktu_rilis": "09:00:00",
        "tempat": "Aula BPS Provinsi Sulawesi Tengah",
        "judul_rilis": "Rilis Berita Resmi Statistik September 2026",
        "brs_ids": [brs_id],
    }


def test_complete_release_marks_brs_released(client):
    ready_id, _, _ = prepare_release_data()
    humas = login(client, "humas", "Humas123!")

    eligible = client.get(
        "/api/v1/releases/eligible-brs?tanggal_rilis=2026-09-05", headers=humas,
    )
    assert eligible.status_code == 200
    assert [item["id"] for item in eligible.json()] == [ready_id]

    created = client.post("/api/v1/releases", headers=humas, json=release_payload(ready_id))
    assert created.status_code == 201, created.text
    release_id = created.json()["id"]
    assert created.json()["jumlah_brs"] == 1
    assert created.json()["status"] == "draft"

    started = client.post(f"/api/v1/releases/{release_id}/start", headers=humas)
    assert started.status_code == 200
    assert started.json()["status"] == "ongoing"

    completed = client.post(f"/api/v1/releases/{release_id}/complete", headers=humas)
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert completed.json()["brs"][0]["status"] == "released"

    with SessionLocal() as db:
        assert db.get(BRS, uuid.UUID(ready_id)).status == "released"


def test_release_rejects_unready_wrong_date_and_duplicate_brs(client):
    ready_id, draft_id, other_date_id = prepare_release_data()
    admin = login(client, "admin", "Admin123!")

    unready = client.post("/api/v1/releases", headers=admin, json=release_payload(draft_id))
    assert unready.status_code == 409
    assert "Siap Rilis" in unready.json()["detail"]

    wrong_date = client.post("/api/v1/releases", headers=admin, json=release_payload(other_date_id))
    assert wrong_date.status_code == 409
    assert "Tanggal" in wrong_date.json()["detail"]

    first = client.post("/api/v1/releases", headers=admin, json=release_payload(ready_id))
    assert first.status_code == 201
    duplicate = client.post("/api/v1/releases", headers=admin, json=release_payload(ready_id))
    assert duplicate.status_code == 409
    assert "kegiatan rilis lain" in duplicate.json()["detail"]


def test_guest_crud_and_role_protection(client):
    ready_id, _, _ = prepare_release_data()
    humas = login(client, "humas", "Humas123!")
    pjk = login(client, "pjk-release", "PjkRelease123!")
    release = client.post("/api/v1/releases", headers=humas, json=release_payload(ready_id)).json()
    guest_payload = {
        "nama": "Andi", "instansi": "TVRI Sulawesi Tengah", "jabatan": "Jurnalis",
        "nomor_hp": "081234567890", "email": "andi@example.com",
    }

    forbidden = client.post(f"/api/v1/releases/{release['id']}/guests", headers=pjk, json=guest_payload)
    assert forbidden.status_code == 403

    created = client.post(f"/api/v1/releases/{release['id']}/guests", headers=humas, json=guest_payload)
    assert created.status_code == 201, created.text
    guest_id = created.json()["id"]

    guest_payload["jabatan"] = "Reporter"
    updated = client.put(f"/api/v1/releases/guests/{guest_id}", headers=humas, json=guest_payload)
    assert updated.status_code == 200
    assert updated.json()["jabatan"] == "Reporter"

    guests = client.get(f"/api/v1/releases/{release['id']}/guests", headers=pjk)
    assert guests.status_code == 200
    assert len(guests.json()) == 1

    deleted = client.delete(f"/api/v1/releases/guests/{guest_id}", headers=humas)
    assert deleted.status_code == 204
