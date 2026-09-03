from datetime import date, time
from decimal import Decimal

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.brs import BRS, BRSData
from app.models.indicator import Indicator
from app.models.release import Guest, Release, ReleaseBRS
from app.models.user import User


def prepare_session() -> tuple[str, str]:
    with SessionLocal() as db:
        users = {
            "pjk": User(
                nama="PJK QNA", nik="pjk-qna", user_level="pjk", fungsi="Distribusi",
                password_hash=get_password_hash("PjkQna123!"),
            ),
            "supervisor": User(
                nama="Supervisor QNA", nik="supervisor-qna", user_level="supervisor", fungsi="Distribusi",
                password_hash=get_password_hash("SupervisorQna123!"),
            ),
            "humas": User(
                nama="Humas QNA", nik="humas-qna", user_level="humas", fungsi="Diseminasi",
                password_hash=get_password_hash("HumasQna123!"),
            ),
        }
        db.add_all(users.values())
        db.flush()
        indicator = Indicator(
            nama_indikator="Perjalanan Wisatawan Nusantara", kategori="Pariwisata",
            satuan_default="ribu perjalanan", fungsi="Distribusi",
        )
        db.add(indicator)
        db.flush()
        brs = BRS(
            kode_brs="BRS-QNA", nama_brs="Perkembangan Pariwisata Juli 2026",
            waktu_rilis=date(2026, 9, 5), fungsi_pj="Distribusi",
            pjk_id=users["pjk"].id, supervisor_id=users["supervisor"].id,
            status="release_ready",
        )
        db.add(brs)
        db.flush()
        db.add(BRSData(
            brs_id=brs.id, indicator_id=indicator.id, sub_indikator="Asal Sulawesi Tengah",
            periode_data=date(2026, 7, 1), deskripsi_periode="Juli 2026",
            nilai_data=Decimal("1007.74"), satuan="ribu perjalanan",
            analisis="Turun 0,90 persen dibandingkan Juni 2026.",
            fenomena="Normalisasi mobilitas setelah periode liburan.", created_by=users["pjk"].id,
        ))
        release = Release(
            kode_rilis="RLS-QNA", tanggal_rilis=date(2026, 9, 5), waktu_rilis=time(9, 0),
            tempat="Aula BPS", judul_rilis="Rilis BRS September 2026",
            status="ongoing", created_by=users["humas"].id,
        )
        release.brs_links.append(ReleaseBRS(brs_id=brs.id))
        guest = Guest(nama="Andi", instansi="TVRI", jabatan="Jurnalis")
        release.guests.append(guest)
        db.add(release)
        db.commit()
        return str(release.id), str(guest.id)


def login(client, nik: str, password: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"nik": nik, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_grounded_qna_human_review_and_completion(client, monkeypatch):
    release_id, guest_id = prepare_session()
    humas = login(client, "humas-qna", "HumasQna123!")
    supervisor = login(client, "supervisor-qna", "SupervisorQna123!")
    pjk = login(client, "pjk-qna", "PjkQna123!")

    created = client.post(
        f"/api/v1/releases/{release_id}/qna", headers=humas,
        json={"guest_id": guest_id, "question": "Mengapa perjalanan wisnus turun pada Juli 2026?"},
    )
    assert created.status_code == 201, created.text
    qna_id = created.json()["id"]

    unavailable = client.post(f"/api/v1/qna/{qna_id}/generate-answer", headers=humas)
    assert unavailable.status_code == 503

    monkeypatch.setattr(
        "app.api.routes.qna.generate_grounded_answer",
        lambda question, context: ("Penurunan berkaitan dengan normalisasi mobilitas setelah liburan.", "test-model"),
    )
    generated = client.post(f"/api/v1/qna/{qna_id}/generate-answer", headers=humas)
    assert generated.status_code == 200, generated.text
    assert generated.json()["ai_model"] == "test-model"
    assert any("Data Input" in source for source in generated.json()["ai_sources"])

    supervisor_answer = client.put(
        f"/api/v1/qna/{qna_id}", headers=supervisor,
        json={"supervisor_answer": "Mobilitas kembali normal setelah liburan."},
    )
    assert supervisor_answer.status_code == 200
    pjk_answer = client.put(
        f"/api/v1/qna/{qna_id}", headers=pjk,
        json={"pjk_answer": "Data menunjukkan penurunan 0,90 persen."},
    )
    assert pjk_answer.status_code == 200

    blocked = client.post(f"/api/v1/releases/{release_id}/complete", headers=humas)
    assert blocked.status_code == 409
    assert "jawaban final" in blocked.json()["detail"]

    finalized = client.post(
        f"/api/v1/qna/{qna_id}/finalize", headers=humas,
        json={"final_answer": "Perjalanan turun 0,90 persen seiring normalisasi mobilitas setelah liburan."},
    )
    assert finalized.status_code == 200
    assert finalized.json()["finalizer"]["nama"] == "Humas QNA"

    completed = client.post(f"/api/v1/releases/{release_id}/complete", headers=humas)
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"


def test_minutes_generate_and_download(client):
    release_id, _ = prepare_session()
    humas = login(client, "humas-qna", "HumasQna123!")
    payload = {
        "opening": "Kegiatan dibuka oleh Kepala BPS.",
        "discussion": "Pemaparan perkembangan pariwisata.",
        "notes": "Seluruh materi telah disampaikan.",
        "conclusion": "Kegiatan berjalan dengan baik.",
    }
    saved = client.put(f"/api/v1/releases/{release_id}/minutes", headers=humas, json=payload)
    assert saved.status_code == 200, saved.text
    assert saved.json()["docx_ready"] is False

    generated = client.post(f"/api/v1/releases/{release_id}/minutes/generate", headers=humas)
    assert generated.status_code == 200, generated.text
    assert generated.json()["docx_ready"] is True
    assert "Perkembangan Pariwisata" in generated.json()["content"]

    docx = client.get(f"/api/v1/releases/{release_id}/minutes/download?format=docx", headers=humas)
    assert docx.status_code == 200
    assert docx.content.startswith(b"PK")
    pdf = client.get(f"/api/v1/releases/{release_id}/minutes/download?format=pdf", headers=humas)
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")


def test_qna_role_protection(client):
    release_id, guest_id = prepare_session()
    humas = login(client, "humas-qna", "HumasQna123!")
    created = client.post(
        f"/api/v1/releases/{release_id}/qna", headers=humas,
        json={"guest_id": guest_id, "question": "Berapa nilai perjalanan wisnus?"},
    ).json()
    forbidden = client.put(
        f"/api/v1/qna/{created['id']}", headers=humas,
        json={"supervisor_answer": "Jawaban yang tidak berwenang."},
    )
    assert forbidden.status_code == 403

