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
    assert result["engine_version"] == "rules-v2.5-period-typo"
    assert result["total_checks"] > 0
    assert result["error_count"] >= 1
    assert float(result["overall_score"]) < 100
    assert any(
        finding["check_type"] == "cross_document"
        and finding["comparison_values"]["narasi_pimpinan"]["value"] == "1.007,47"
        and finding["comparison_values"]["narasi_pimpinan"]["status"] == "different"
        and finding["document_type"] == "narasi_pimpinan"
        for finding in result["results"]
    )
    assert any(finding["check_type"] == "cross_document" for finding in result["results"])
    assert all(finding["check_type"] != "data_consistency" for finding in result["results"])
    assert all(finding["brs_data_id"] is None for finding in result["results"])

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


def test_equal_indicator_in_two_documents_does_not_require_third_document(client):
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
    comparison_findings = [
        finding for finding in checked.json()["results"]
        if finding["check_type"] in {"document_coverage", "cross_document"}
    ]
    assert comparison_findings == []


def test_check_ignores_documents_without_comparable_indicator_numbers(client):
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
    assert not any(
        item["check_type"] in {"document_coverage", "cross_document"}
        for item in result["results"]
    )
    assert float(result["data_consistency_score"]) == 100


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
    assert "TPK" in errors[0]["field_name"]


def test_indicator_is_matched_by_name_and_same_period(client):
    headers = auth_headers(client)
    brs = client.post(
        "/api/v1/brs",
        headers=headers,
        json={
            "nama_brs": "TPK Januari dan Februari 2026",
            "waktu_rilis": "2026-03-01",
            "fungsi_pj": "Statistik Distribusi",
            "supervisor_id": None,
            "team_user_ids": [],
        },
    ).json()
    texts = {
        "bahan_publikasi": (
            "TPK hotel bintang bulan Januari 2026 adalah 15 persen.\n"
            "TPK hotel bintang bulan Februari 2026 adalah 20 persen.\n"
            "Inflasi Januari 2026 sebesar 0,25 persen."
        ),
        "bahan_paparan": (
            "TPK Februari 2026 tercatat 20 persen.\n"
            "TPK Januari 2026 tercatat 18 persen."
        ),
        "narasi_pimpinan": (
            "Pada Februari 2026, TPK hotel bintang sebesar 20 persen."
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
        if item["check_type"] == "cross_document"
    ]
    assert len(errors) == 1
    january = errors[0]
    assert january["field_name"] == "TPK • Januari 2026"
    assert set(january["comparison_values"]) == {"bahan_publikasi", "bahan_paparan"}
    assert january["comparison_values"]["bahan_publikasi"]["value"] == "15"
    assert january["comparison_values"]["bahan_paparan"]["value"] == "18"
    assert january["document_type"] is None
    assert {
        january["comparison_values"]["bahan_publikasi"]["status"],
        january["comparison_values"]["bahan_paparan"]["status"],
    } == {"needs_verification"}
    assert "TPK hotel bintang bulan Januari 2026" in january["comparison_values"]["bahan_publikasi"]["context"]
    assert "TPK Januari 2026" in january["comparison_values"]["bahan_paparan"]["context"]
    assert all("Inflasi" not in item.get("field_name", "") for item in errors)


def test_eyd_finding_identifies_document_location_and_standard_word(client):
    headers = auth_headers(client)
    brs = client.post(
        "/api/v1/brs",
        headers=headers,
        json={
            "nama_brs": "Uji EYD Dokumen",
            "waktu_rilis": "2026-09-01",
            "fungsi_pj": "Statistik Distribusi",
            "supervisor_id": None,
            "team_user_ids": [],
        },
    ).json()
    texts = {
        "bahan_publikasi": "Aktivitas survei meningkat. TPK Juli 2026 sebesar 15 persen.",
        "bahan_paparan": "Aktifitas survey meningkat. TPK Juli 2026 sebesar 15 persen.",
        "narasi_pimpinan": "Aktivitas survei meningkat. TPK Juli 2026 sebesar 15 persen.",
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
    word_findings = [
        item for item in checked.json()["results"]
        if item["check_type"] == "language" and item["field_name"] == "Kata tidak baku"
    ]
    assert {(item["actual_value"].lower(), item["expected_value"].lower()) for item in word_findings} == {
        ("aktifitas", "aktivitas"),
        ("survey", "survei"),
    }
    assert all(item["document_type"] == "bahan_paparan" for item in word_findings)
    assert all(item["document_name"] == "bahan_paparan.pdf" for item in word_findings)
    assert all(item["page_number"] == 1 for item in word_findings)
    assert all(item["context_text"] for item in word_findings)


def test_point_value_is_consistent_with_descriptive_range(client):
    headers = auth_headers(client)
    brs = client.post(
        "/api/v1/brs",
        headers=headers,
        json={
            "nama_brs": "RLMT Juli 2026",
            "waktu_rilis": "2026-09-01",
            "fungsi_pj": "Statistik Distribusi",
            "supervisor_id": None,
            "team_user_ids": [],
        },
    ).json()
    texts = {
        "bahan_publikasi": (
            "Rata-rata Lama Menginap Tamu (RLMT) hotel bintang pada Juli 2026 "
            "tercatat 1,67 hari."
        ),
        "bahan_paparan": (
            "Rata-rata setiap tamu menghabiskan waktu sekitar 1 hingga 2 hari untuk menginap."
        ),
        "narasi_pimpinan": (
            "RLMT hotel bintang pada Juli 2026 mencapai 1,67 hari."
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
    assert not any(
        item["check_type"] == "cross_document"
        for item in checked.json()["results"]
    )


def test_yoy_value_is_not_compared_with_mtm_value_for_same_city(client):
    headers = auth_headers(client)
    brs = client.post(
        "/api/v1/brs",
        headers=headers,
        json={
            "nama_brs": "Inflasi Menurut Wilayah",
            "waktu_rilis": "2026-09-01",
            "fungsi_pj": "Statistik Distribusi",
            "supervisor_id": None,
            "team_user_ids": [],
        },
    ).json()
    texts = {
        "bahan_publikasi": (
            "Inflasi tahun sebelumnya (year-on-year) yaitu Kabupaten Banggai Laut "
            "sebesar 45,08 persen, disusul Kota Palu sebesar 30,56 persen."
        ),
        "bahan_paparan": "MONTH-TO-MONTH (MtM)\n1. Kota Palu : 7,33 %",
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
    assert not any(
        item["check_type"] == "cross_document"
        for item in checked.json()["results"]
    )


def test_di_prefix_and_preposition_are_checked_without_spacing_rules(client):
    headers = auth_headers(client)
    brs = client.post(
        "/api/v1/brs",
        headers=headers,
        json={
            "nama_brs": "Uji Penulisan Di",
            "waktu_rilis": "2026-09-01",
            "fungsi_pj": "Statistik Distribusi",
            "supervisor_id": None,
            "team_user_ids": [],
        },
    ).json()
    texts = {
        "bahan_publikasi": "Data  di catat oleh petugas diatas meja.",
        "bahan_paparan": "Data dicatat oleh petugas di atas meja.",
        "narasi_pimpinan": "Data naik sebesar 1% dan terdiri dari dua kelompok.",
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
    language = [
        item for item in checked.json()["results"]
        if item["check_type"] == "language"
    ]
    corrections = {(item["actual_value"].lower(), item["expected_value"].lower()) for item in language}
    assert ("di catat", "dicatat") in corrections
    assert ("diatas", "di atas") in corrections
    assert not any("spasi" in (item["field_name"] or "").lower() for item in language)
    assert not any(item["actual_value"] in {"naik sebesar", "1%", "terdiri dari"} for item in language)


def test_same_indicator_and_value_with_different_month_is_an_error(client):
    headers = auth_headers(client)
    brs = client.post(
        "/api/v1/brs",
        headers=headers,
        json={
            "nama_brs": "TPK Juli 2026",
            "waktu_rilis": "2026-09-01",
            "fungsi_pj": "Statistik Distribusi",
            "supervisor_id": None,
            "team_user_ids": [],
        },
    ).json()
    texts = {
        "bahan_publikasi": (
            "Tingkat Penghunian Kamar (TPK) hotel bintang pada Juli 2026 "
            "tercatat 51,50 persen."
        ),
        "bahan_paparan": (
            "TPK hotel bintang pada Juni 2026 tercatat 51,50 persen."
        ),
        "narasi_pimpinan": (
            "Pada Juli 2026, TPK hotel bintang mencapai 51,50 persen."
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
        if item["check_type"] == "cross_document"
    ]
    assert len(errors) == 1
    finding = errors[0]
    assert finding["document_type"] == "bahan_paparan"
    assert "Periode indikator" in finding["message"]
    comparison = finding["comparison_values"]
    assert comparison["bahan_publikasi"]["period"] == "Juli 2026"
    assert comparison["bahan_paparan"]["period"] == "Juni 2026"
    assert comparison["narasi_pimpinan"]["period"] == "Juli 2026"
    assert comparison["bahan_paparan"]["status"] == "different"
    assert all(item["value"] == "51,50" for item in comparison.values())
    assert all(item["issue"] == "period" for item in comparison.values())


def test_equal_number_with_different_indicator_meaning_is_not_compared(client):
    headers = auth_headers(client)
    brs = client.post(
        "/api/v1/brs",
        headers=headers,
        json={
            "nama_brs": "TPK Menurut Kategori Hotel",
            "waktu_rilis": "2026-09-01",
            "fungsi_pj": "Statistik Distribusi",
            "supervisor_id": None,
            "team_user_ids": [],
        },
    ).json()
    texts = {
        "bahan_publikasi": (
            "TPK hotel bintang pada Juli 2026 tercatat 51,50 persen."
        ),
        "bahan_paparan": (
            "TPK hotel nonbintang pada Juni 2026 tercatat 51,50 persen."
        ),
        "narasi_pimpinan": "Perkembangan usaha akomodasi telah disampaikan.",
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
    assert not any(
        item["check_type"] == "cross_document"
        for item in checked.json()["results"]
    )


def test_typo_check_identifies_document_and_suggested_correction(client):
    headers = auth_headers(client)
    brs = client.post(
        "/api/v1/brs",
        headers=headers,
        json={
            "nama_brs": "Uji Typo",
            "waktu_rilis": "2026-09-01",
            "fungsi_pj": "Statistik Distribusi",
            "supervisor_id": None,
            "team_user_ids": [],
        },
    ).json()
    texts = {
        "bahan_publikasi": "Dokumen statistik membahas perkembangan akomodasi.",
        "bahan_paparan": "Dokumen statitik memuat persenatse usaha akomodsi.",
        "narasi_pimpinan": "Dokumen statistik membahas perkembangan akomodasi.",
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
    typo_findings = [
        item for item in checked.json()["results"]
        if item["check_type"] == "language" and item["field_name"] == "Typo"
    ]
    assert {
        (item["actual_value"].lower(), item["expected_value"].lower())
        for item in typo_findings
    } == {
        ("statitik", "statistik"),
        ("persenatse", "persentase"),
        ("akomodsi", "akomodasi"),
    }
    assert all(item["document_type"] == "bahan_paparan" for item in typo_findings)
