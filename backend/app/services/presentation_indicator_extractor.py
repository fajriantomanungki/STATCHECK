import hashlib
import re
import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.indicator import Indicator
from app.models.presentation_indicator import PresentationIndicator
from app.services.statcheck_engine import STRONG_INDICATOR_TERMS, _common_label, _mentions

DISPLAY_NAMES = {
    "ntp": "Nilai Tukar Petani (NTP)",
    "pdrb": "Produk Domestik Regional Bruto (PDRB)",
    "rlmt": "Rata-rata Lama Menginap Tamu (RLMT)",
    "tpk": "Tingkat Penghunian Kamar (TPK)",
    "wisman": "Wisatawan Mancanegara",
    "wisnus": "Wisatawan Nusantara",
}
UNIT_LABELS = {
    "percentage_point": "persen poin",
    "percent": "persen",
    "currency": "rupiah",
    "person": "orang/tamu",
    "trip": "perjalanan",
    "day": "hari",
    "room": "kamar",
    "index": "indeks",
    "ton": "ton",
}


def _normalized(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def _indicator_name(mention: object, masters: list[Indicator]) -> str:
    context = _normalized(getattr(mention, "context_text", ""))
    for master in sorted(masters, key=lambda item: len(item.nama_indikator), reverse=True):
        name = _normalized(master.nama_indikator)
        words = [word for word in name.split() if word not in {"dan", "di", "ke", "pada", "rata", "rata rata"}]
        acronym = "".join(word[0] for word in words)
        if name in context or (len(acronym) >= 2 and re.search(rf"\b{re.escape(acronym)}\b", context)):
            return master.nama_indikator
    keywords = tuple(getattr(mention, "keywords", ()))
    strong = next((word for word in keywords if word in STRONG_INDICATOR_TERMS), None)
    if strong:
        return DISPLAY_NAMES.get(strong, strong.upper())
    label = _common_label([mention]).split(" • ", 1)[0].strip()
    return label or "Indikator Statistik"


def _data_type(mention: object) -> str:
    if getattr(mention, "range_min", None) is not None:
        return "range"
    unit = getattr(mention, "unit", None)
    return {
        "percent": "percentage",
        "percentage_point": "percentage_point",
        "currency": "currency",
        "index": "index",
        "day": "duration",
        "person": "count",
        "trip": "count",
        "room": "count",
        "ton": "quantity",
    }.get(unit, "number")


def sync_presentation_indicators(
    db: Session,
    document: Document,
    created_by: uuid.UUID,
) -> list[PresentationIndicator]:
    """Ganti hasil ekstraksi Bahan Paparan dengan hasil versi aktif terbaru."""
    if document.document_type != "bahan_paparan":
        return []

    previous = list(db.scalars(
        select(PresentationIndicator).where(PresentationIndicator.brs_id == document.brs_id)
    ))
    annotations = {
        item.source_hash: (item.analysis, item.phenomenon)
        for item in previous
        if item.analysis or item.phenomenon
    }
    db.execute(delete(PresentationIndicator).where(PresentationIndicator.brs_id == document.brs_id))
    if document.extraction_status != "completed":
        return []

    rows: list[PresentationIndicator] = []
    masters = list(db.scalars(select(Indicator).where(Indicator.is_active.is_(True))))
    seen: set[str] = set()
    for mention in _mentions(document):
        normalized_context = re.sub(r"\s+", " ", mention.context_text).strip()
        identity = "|".join([
            str(mention.page_number), mention.raw, mention.period_key or "",
            mention.basis_key or "", mention.subject_key or "", mention.value_role,
            normalized_context,
        ])
        source_hash = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        if source_hash in seen:
            continue
        seen.add(source_hash)
        analysis, phenomenon = annotations.get(source_hash, (None, None))
        rows.append(PresentationIndicator(
            brs_id=document.brs_id,
            document_id=document.id,
            indicator_name=_indicator_name(mention, masters),
            value_text=mention.raw,
            numeric_value=mention.value,
            unit=UNIT_LABELS.get(mention.unit, mention.unit),
            period_label=mention.period_label,
            data_type=_data_type(mention),
            comparison_basis=mention.basis_label,
            value_role=mention.value_role,
            metadata_text=normalized_context,
            page_number=mention.page_number,
            source_hash=source_hash,
            analysis=analysis,
            phenomenon=phenomenon,
            created_by=created_by,
        ))
    db.add_all(rows)
    return rows
