import fitz

from app.services.statcheck_engine import parse_localized_number


def auth_headers(client):
    response = client.post("/api/v1/auth/login", json={"nik": "admin", "password": "Admin123!"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_textbox(fitz.Rect(50, 50, 550, 790), text, fontsize=11)
    content = document.tobytes()
    document.close()
    return content


def prepare_brs(client, headers) -> str:
    brs = client.post(
        "/api/v1/brs",
        headers=headers,
        json={
            "nama_brs": "Perkembangan Pariwisata Juli 2026",
            "waktu_rilis": "2026-09-01",
            "fungsi_pj": "Statistik Distribusi",
            "supervisor_id": None,
            "team_user_ids": [],
        },
    ).json()
    documents = {
        "bahan_publikasi": (
            "Perjalanan Wisnus asal Sulawesi Tengah Juli 2026 sebanyak 1.007,74 ribu perjalanan.\n"
            "Tingkat Penghunian Kamar hotel bintang sebesar 51,95 persen."
        ),
        "bahan_paparan": (
            "Perjalanan Wisnus asal Sulawesi Tengah Juli 2026: 1.007,74 ribu perjalanan.\n"
            "Tingkat Penghunian Kamar hotel bintang: 51,95 persen."
        ),
        "narasi_pimpinan": (
            "Perjalanan Wisnus asal Sulawesi Tengah Juli 2026 sebanyak 1.007,47 ribu perjalanan, "
            "turun sebesar 0,90 persen dibanding Juni 2026.\n"
            "Tingkat Penghunian Kamar hotel bintang sebesar 51,95 persen."
        ),
    }
    for document_type, text in documents.items():
        response = client.post(
            f"/api/v1/brs/{brs['id']}/documents",
            headers=headers,
            data={"document_type": document_type},
            files={"file": (f"{document_type}.pdf", pdf_bytes(text), "application/pdf")},
        )
        assert response.status_code == 201, response.text
    return brs["id"]


def test_localized_number_parser():
    assert parse_localized_number("1.007,74") == parse_localized_number("1007.74")
    assert parse_localized_number("52,31") == parse_localized_number("52.31")
    assert parse_localized_number("27.073") == 27073


def test_check_requires_three_documents_but_not_input_data(client):
    headers = auth_headers(client)
    brs = client.post(
        "/api/v1/brs",
        headers=headers,
        json={
            "nama_brs": "BRS Belum Lengkap", "waktu_rilis": "2026-10-01",
            "fungsi_pj": "Statistik Distribusi", "supervisor_id": None, "team_user_ids": [],
        },
    ).json()
    response = client.post(f"/api/v1/brs/{brs['id']}/check", headers=headers)
    assert response.status_code == 409
    assert "dokumen" in response.json()["detail"].lower()


def test_automatic_check_and_pjk_review(client):
    headers = auth_headers(client)
    brs_id = prepare_brs(client, headers)

    checked = client.post(f"/api/v1/brs/{brs_id}/check", headers=headers)
    assert checked.status_code == 201, checked.text
    result = checked.json()
    assert result["status"] == "completed"
    assert result["engine_version"] == "rules-v2.1-indicators"
    assert result["total_checks"] > 0
    assert result["error_count"] >= 1
    assert result["suggestion_count"] >= 2
    assert float(result["overall_score"]) < 100
    assert any(
        finding["check_type"] == "cross_document"
        and finding["comparison_values"]["narasi_pimpinan"]["value"] == "1.007,47"
        for finding in result["results"]
    )
    assert any(finding["check_type"] == "cross_document" for finding in result["results"])
    assert all(finding["check_type"] != "data_consistency" for finding in result["results"])
    assert all(finding["brs_data_id"] is None for finding in result["results"])
    assert any(finding["check_type"] == "language" for finding in result["results"])

    brs = client.get(f"/api/v1/brs/{brs_id}", headers=headers)
    assert brs.json()["status"] == "pjk_review"

    finding = next(item for item in result["results"] if item["severity"] == "error")
    reviewed = client.post(
        f"/api/v1/checks/{finding['id']}/review",
        headers=headers,
        json={"action": "fixed", "note": "Angka pada dokumen sudah diperbaiki."},
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["status"] == "resolved"
    assert reviewed.json()["reviews"][0]["action"] == "fixed"

    latest = client.get(f"/api/v1/brs/{brs_id}/checks/latest", headers=headers)
    assert latest.status_code == 200
    latest_finding = next(item for item in latest.json()["results"] if item["id"] == finding["id"])
    assert latest_finding["status"] == "resolved"

    rerun = client.post(f"/api/v1/brs/{brs_id}/check", headers=headers)
    assert rerun.status_code == 201
    assert rerun.json()["id"] != result["id"]

    history = client.get(f"/api/v1/brs/{brs_id}/checks", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) == 2


def test_check_warns_when_context_is_present_in_only_two_documents(client):
    headers = auth_headers(client)
    brs = client.post(
        "/api/v1/brs",
        headers=headers,
        json={
            "nama_brs": "Perkembangan Inflasi Agustus 2026",
            "waktu_rilis": "2026-09-01",
            "fungsi_pj": "Statistik Distribusi",
            "supervisor_id": None,
            "team_user_ids": [],
        },
    ).json()
    texts = {
        "bahan_publikasi": "Inflasi bulanan Kota Palu tercatat 0,31 persen.",
        "bahan_paparan": "Inflasi bulanan Kota Palu tercatat 0,31 persen.",
        "narasi_pimpinan": "Perkembangan harga konsumen telah disampaikan.",
    }
    for document_type, text in texts.items():
        response = client.post(
            f"/api/v1/brs/{brs['id']}/documents",
            headers=headers,
            data={"document_type": document_type},
            files={"file": (f"{document_type}.pdf", pdf_bytes(text), "application/pdf")},
        )
        assert response.status_code == 201, response.text

    checked = client.post(f"/api/v1/brs/{brs['id']}/check", headers=headers)
    assert checked.status_code == 201, checked.text
    coverage = [
        finding for finding in checked.json()["results"]
        if finding["check_type"] == "document_coverage"
    ]
    assert len(coverage) == 1
    assert "Narasi Pimpinan" in coverage[0]["message"]
    assert coverage[0]["brs_data_id"] is None
    assert coverage[0]["comparison_values"]["narasi_pimpinan"]["value"] is None


def test_check_does_not_report_perfect_score_when_no_numbers_can_be_compared(client):
    headers = auth_headers(client)
    brs = client.post(
        "/api/v1/brs",
        headers=headers,
        json={
            "nama_brs": "BRS Tanpa Angka Terbaca",
            "waktu_rilis": "2026-09-01",
            "fungsi_pj": "Statistik Distribusi",
            "supervisor_id": None,
            "team_user_ids": [],
        },
    ).json()
    for document_type in ("bahan_publikasi", "bahan_paparan", "narasi_pimpinan"):
        response = client.post(
            f"/api/v1/brs/{brs['id']}/documents",
            headers=headers,
            data={"document_type": document_type},
            files={
                "file": (
                    f"{document_type}.pdf",
                    pdf_bytes("Dokumen statistik tanpa angka yang dapat diperiksa."),
                    "application/pdf",
                )
            },
        )
        assert response.status_code == 201, response.text

    checked = client.post(f"/api/v1/brs/{brs['id']}/check", headers=headers)
    assert checked.status_code == 201, checked.text
    result = checked.json()
    assert result["warning_count"] >= 1
    assert float(result["data_consistency_score"]) < 100
    assert any("Tidak ada angka" in item["message"] for item in result["results"])


def test_document_number_and_release_date_are_not_treated_as_indicators(client):
    headers = auth_headers(client)
    brs = client.post(
        "/api/v1/brs",
        headers=headers,
        json={
            "nama_brs": "Perkembangan Pariwisata Juni 2026",
            "waktu_rilis": "2026-08-03",
            "fungsi_pj": "Statistik Distribusi",
            "supervisor_id": None,
            "team_user_ids": [],
        },
    ).json()
    texts = {
        "bahan_publikasi": (
            "BADAN PUSAT STATISTIK PROVINSI SULAWESI TENGAH No. 49/08/72/Th. XXIX, "
            "03 Agustus 2026 □ Pada Juni 2026, perjalanan wisatawan nusantara (wisnus) "
            "sebanyak 1.007,74 ribu perjalanan."
        ),
        "bahan_paparan": (
            "Rilis BRS 03 Agustus 2026 PARIWISATA PROVINSI SULAWESI TENGAH "
            "BRS No. 49/08/72/Th. XXIX □ Perjalanan wisnus pada Juni 2026 mencapai "
            "1.007,74 ribu perjalanan."
        ),
        "narasi_pimpinan": (
            "Perjalanan wisatawan nusantara atau wisnus pada Juni 2026 mencapai "
            "1.007,47 ribu perjalanan."
        ),
    }
    for document_type, text in texts.items():
        response = client.post(
            f"/api/v1/brs/{brs['id']}/documents",
            headers=headers,
            data={"document_type": document_type},
            files={"file": (f"{document_type}.pdf", pdf_bytes(text), "application/pdf")},
        )
        assert response.status_code == 201, response.text

    checked = client.post(f"/api/v1/brs/{brs['id']}/check", headers=headers)
    assert checked.status_code == 201, checked.text
    results = checked.json()["results"]
    cross_document = [item for item in results if item["check_type"] == "cross_document"]
    assert len(cross_document) == 1
    comparison = cross_document[0]["comparison_values"]
    assert comparison["bahan_publikasi"]["value"] == "1.007,74"
    assert comparison["bahan_paparan"]["value"] == "1.007,74"
    assert comparison["narasi_pimpinan"]["value"] == "1.007,47"
    assert not any(
        item["check_type"] == "document_coverage" and item["expected_value"] == "49"
        for item in results
    )
    assert not any(item["field_name"] == "Xxix" for item in results)


def test_multiple_indicators_are_matched_by_context_not_document_order(client):
    headers = auth_headers(client)
    brs = client.post(
        "/api/v1/brs",
        headers=headers,
        json={
            "nama_brs": "Perkembangan Hotel Bintang",
            "waktu_rilis": "2026-09-01",
            "fungsi_pj": "Statistik Distribusi",
            "supervisor_id": None,
            "team_user_ids": [],
        },
    ).json()
    texts = {
        "bahan_publikasi": (
            "Tingkat Penghunian Kamar (TPK) hotel bintang sebesar 51,95 persen.\n"
            "Rata-rata lama menginap tamu (RLMT) hotel bintang sebesar 1,67 hari."
        ),
        "bahan_paparan": (
            "RLMT tamu hotel bintang mencapai 1,67 hari.\n"
            "TPK hotel bintang mencapai 51,95 persen."
        ),
        "narasi_pimpinan": (
            "Tingkat Penghunian Kamar atau TPK hotel bintang sebesar 51,59 persen.\n"
            "Rata-rata lama menginap tamu atau RLMT hotel bintang sebesar 1,67 hari."
        ),
    }
    for document_type, text in texts.items():
        response = client.post(
            f"/api/v1/brs/{brs['id']}/documents",
            headers=headers,
            data={"document_type": document_type},
            files={"file": (f"{document_type}.pdf", pdf_bytes(text), "application/pdf")},
        )
        assert response.status_code == 201, response.text

    checked = client.post(f"/api/v1/brs/{brs['id']}/check", headers=headers)
    assert checked.status_code == 201, checked.text
    errors = [
        item for item in checked.json()["results"]
        if item["check_type"] == "cross_document" and item["severity"] == "error"
    ]
    assert len(errors) == 1
    comparison = errors[0]["comparison_values"]
    assert comparison["bahan_publikasi"]["value"] == "51,95"
    assert comparison["bahan_paparan"]["value"] == "51,95"
    assert comparison["narasi_pimpinan"]["value"] == "51,59"
    assert "Tpk" in errors[0]["field_name"]
