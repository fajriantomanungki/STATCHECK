from pathlib import Path

import fitz

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.user import User


def auth_headers(client):
    response = client.post("/api/v1/auth/login", json={"nik": "admin", "password": "Admin123!"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_supervisor() -> str:
    with SessionLocal() as db:
        user = User(
            nama="Supervisor Test",
            nik="supervisor",
            user_level="supervisor",
            fungsi="Statistik Distribusi",
            password_hash=get_password_hash("Supervisor123!"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return str(user.id)


def test_indicator_crud(client):
    headers = auth_headers(client)
    created = client.post(
        "/api/v1/indicators",
        headers=headers,
        json={
            "nama_indikator": "Inflasi",
            "kategori": "Harga",
            "satuan_default": "persen",
            "fungsi": "Statistik Distribusi",
        },
    )
    assert created.status_code == 201
    indicator_id = created.json()["id"]

    updated = client.put(
        f"/api/v1/indicators/{indicator_id}",
        headers=headers,
        json={
            "nama_indikator": "Inflasi Umum",
            "kategori": "Harga",
            "satuan_default": "persen",
            "fungsi": "Statistik Distribusi",
            "is_active": True,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["nama_indikator"] == "Inflasi Umum"


def test_brs_registration_and_data_entry(client):
    headers = auth_headers(client)
    supervisor_id = create_supervisor()
    indicator = client.post(
        "/api/v1/indicators",
        headers=headers,
        json={
            "nama_indikator": "Tingkat Penghunian Kamar",
            "kategori": "Pariwisata",
            "satuan_default": "persen",
            "fungsi": "Statistik Distribusi",
        },
    ).json()

    created = client.post(
        "/api/v1/brs",
        headers=headers,
        json={
            "nama_brs": "Perkembangan Pariwisata Juli 2026",
            "waktu_rilis": "2026-09-01",
            "fungsi_pj": "Statistik Distribusi",
            "supervisor_id": supervisor_id,
            "team_user_ids": [],
        },
    )
    assert created.status_code == 201
    assert created.json()["status"] == "draft"
    brs_id = created.json()["id"]

    data = client.post(
        f"/api/v1/brs/{brs_id}/data",
        headers=headers,
        json={
            "indicator_id": indicator["id"],
            "sub_indikator": "Hotel Bintang",
            "periode_data": "2026-07-01",
            "deskripsi_periode": "Juli 2026",
            "nilai_data": "51.95",
            "satuan": "persen",
            "analisis": "Naik 0,48 persen poin dibandingkan Juni 2026.",
            "fenomena": "Peningkatan aktivitas perjalanan pada periode liburan.",
        },
    )
    assert data.status_code == 201
    assert data.json()["indicator"]["nama_indikator"] == "Tingkat Penghunian Kamar"

    detail = client.get(f"/api/v1/brs/{brs_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["jumlah_data"] == 1

    summary = client.get("/api/v1/dashboard/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json() == {
        "total_brs": 1,
        "draft_brs": 1,
        "total_indicators": 1,
        "total_brs_data": 1,
        "total_documents": 0,
        "ready_brs": 0,
        "released_brs": 0,
        "total_releases": 0,
    }


def test_brs_requires_authentication(client):
    assert client.get("/api/v1/brs").status_code == 401


def test_delete_brs_removes_record_and_uploaded_files(client):
    headers = auth_headers(client)
    created = client.post(
        "/api/v1/brs",
        headers=headers,
        json={
            "nama_brs": "BRS yang Akan Dihapus",
            "waktu_rilis": "2026-09-01",
            "fungsi_pj": "Statistik Distribusi",
            "supervisor_id": None,
            "team_user_ids": [],
        },
    )
    assert created.status_code == 201
    brs_id = created.json()["id"]

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "TPK Januari 2026 sebesar 15 persen.")
    pdf_content = pdf.tobytes()
    pdf.close()
    uploaded = client.post(
        f"/api/v1/brs/{brs_id}/documents",
        headers=headers,
        data={"document_type": "bahan_publikasi"},
        files={"file": ("brs.pdf", pdf_content, "application/pdf")},
    )
    assert uploaded.status_code == 201, uploaded.text
    assert any(path.is_file() for path in Path("test_uploads").rglob("*"))

    deleted = client.delete(f"/api/v1/brs/{brs_id}", headers=headers)
    assert deleted.status_code == 204, deleted.text
    assert client.get(f"/api/v1/brs/{brs_id}", headers=headers).status_code == 404
    assert not any(path.is_file() for path in Path("test_uploads").rglob("*"))
