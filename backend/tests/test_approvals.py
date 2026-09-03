from decimal import Decimal

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.brs import BRS
from app.models.check import CheckResult, CheckRun
from app.models.user import User, utc_now


def create_workflow(status: str = "pjk_review", finding_status: str = "resolved") -> tuple[str, dict[str, str]]:
    with SessionLocal() as db:
        users = {
            "pjk": User(
                nama="PJK Test", nik="pjk", user_level="pjk", fungsi="Distribusi",
                password_hash=get_password_hash("Pjk12345!"),
            ),
            "supervisor": User(
                nama="Supervisor Test", nik="supervisor", user_level="supervisor", fungsi="Distribusi",
                password_hash=get_password_hash("Supervisor123!"),
            ),
            "ka_bps": User(
                nama="Kepala BPS Test", nik="kabps", user_level="ka_bps", fungsi="Pimpinan",
                password_hash=get_password_hash("KaBPS123!"),
            ),
        }
        db.add_all(users.values())
        db.flush()
        brs = BRS(
            kode_brs=f"BRS-TEST-{status}", nama_brs="BRS Workflow Test",
            waktu_rilis=utc_now().date(), fungsi_pj="Statistik Distribusi",
            pjk_id=users["pjk"].id, supervisor_id=users["supervisor"].id, status=status,
        )
        db.add(brs)
        db.flush()
        run = CheckRun(
            brs_id=brs.id, status="completed", total_checks=1, passed_checks=0,
            error_count=1, warning_count=0, suggestion_count=0,
            data_consistency_score=Decimal("0"), cross_document_score=Decimal("100"),
            language_score=Decimal("100"), overall_score=Decimal("50"),
            initiated_by=users["pjk"].id, completed_at=utc_now(),
        )
        run.results.append(CheckResult(
            brs_id=brs.id, check_type="data_consistency", severity="error",
            message="Nilai berbeda.", status=finding_status,
        ))
        db.add(run)
        db.commit()
        return str(brs.id), {key: user.nik for key, user in users.items()}


def login(client, nik: str, password: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"nik": nik, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_complete_approval_workflow(client):
    brs_id, _ = create_workflow()
    pjk = login(client, "pjk", "Pjk12345!")
    supervisor = login(client, "supervisor", "Supervisor123!")
    ka_bps = login(client, "kabps", "KaBPS123!")

    submitted = client.post(
        f"/api/v1/brs/{brs_id}/submit-supervisor", headers=pjk,
        json={"note": "Seluruh temuan telah ditindaklanjuti."},
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["current_status"] == "pjk_submitted"

    started = client.post(f"/api/v1/brs/{brs_id}/supervisor/start-review", headers=supervisor)
    assert started.status_code == 200, started.text
    assert started.json()["current_status"] == "supervisor_review"

    approved = client.post(
        f"/api/v1/brs/{brs_id}/supervisor/approve", headers=supervisor,
        json={"note": "Dokumen telah sesuai."},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["current_status"] == "supervisor_approved"

    sent_to_head = client.post(
        f"/api/v1/brs/{brs_id}/submit-ka-bps", headers=pjk,
        json={"note": "Mohon persetujuan Kepala BPS."},
    )
    assert sent_to_head.status_code == 200, sent_to_head.text
    assert sent_to_head.json()["current_status"] == "ka_bps_review"

    release_ready = client.post(
        f"/api/v1/brs/{brs_id}/ka-bps/approve", headers=ka_bps,
        json={"note": "Disetujui untuk dirilis."},
    )
    assert release_ready.status_code == 200, release_ready.text
    assert release_ready.json()["current_status"] == "release_ready"
    assert len(release_ready.json()["events"]) == 5

    workflow = client.get(f"/api/v1/brs/{brs_id}/approval", headers=ka_bps)
    assert workflow.status_code == 200
    assert workflow.json()["latest_score"] == "50.00"
    assert workflow.json()["open_findings"] == 0


def test_open_finding_blocks_submission(client):
    brs_id, _ = create_workflow(finding_status="open")
    pjk = login(client, "pjk", "Pjk12345!")
    response = client.post(
        f"/api/v1/brs/{brs_id}/submit-supervisor", headers=pjk, json={"note": None},
    )
    assert response.status_code == 409
    assert "temuan" in response.json()["detail"]


def test_revision_requires_note_and_correct_role(client):
    brs_id, _ = create_workflow(status="supervisor_review")
    pjk = login(client, "pjk", "Pjk12345!")
    supervisor = login(client, "supervisor", "Supervisor123!")

    forbidden = client.post(
        f"/api/v1/brs/{brs_id}/supervisor/approve", headers=pjk, json={"note": None},
    )
    assert forbidden.status_code == 403

    missing_note = client.post(
        f"/api/v1/brs/{brs_id}/supervisor/revision", headers=supervisor, json={"note": ""},
    )
    assert missing_note.status_code == 422

    revision = client.post(
        f"/api/v1/brs/{brs_id}/supervisor/revision", headers=supervisor,
        json={"note": "Perbaiki angka pada Narasi Pimpinan."},
    )
    assert revision.status_code == 200
    assert revision.json()["current_status"] == "supervisor_revision"
    assert revision.json()["events"][0]["note"] == "Perbaiki angka pada Narasi Pimpinan."


def test_ka_bps_can_return_brs(client):
    brs_id, _ = create_workflow(status="ka_bps_review")
    ka_bps = login(client, "kabps", "KaBPS123!")
    response = client.post(
        f"/api/v1/brs/{brs_id}/ka-bps/revision", headers=ka_bps,
        json={"note": "Sesuaikan narasi kesimpulan."},
    )
    assert response.status_code == 200
    assert response.json()["current_status"] == "ka_bps_revision"
