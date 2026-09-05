import hashlib
import re
import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.document import Document
from app.models.indicator import Indicator
from app.models.presentation_indicator import PresentationIndicator
from app.services.statcheck_engine import NumberMention, _mentions

INDICATOR_PATTERNS = (
    (re.compile(r"\b(?:tingkat\s+penghunian\s+kamar|tpk)\b", re.IGNORECASE), "Tingkat Penghunian Kamar (TPK)"),
    (re.compile(r"\b(?:rata[–—\s-]*rata\s+lama\s+menginap\s+tamu|rata[–—\s-]*rata\s+(?:setiap\s+)?tamu.{0,140}?\bmenginap|rlmt)\b", re.IGNORECASE), "Rata-rata Lama Menginap Tamu (RLMT)"),
    (re.compile(r"\b(?:nilai\s+tukar\s+petani|ntp)\b", re.IGNORECASE), "Nilai Tukar Petani (NTP)"),
    (re.compile(r"\b(?:produk\s+domestik\s+regional\s+bruto|pdrb)\b", re.IGNORECASE), "Produk Domestik Regional Bruto (PDRB)"),
    (re.compile(r"\b(?:perjalanan\s+)?(?:wisatawan\s+nusantara|wisnus)\b", re.IGNORECASE), "Perjalanan Wisatawan Nusantara"),
    (re.compile(r"\b(?:kunjungan\s+)?(?:wisatawan\s+mancanegara|wisman)\b", re.IGNORECASE), "Wisatawan Mancanegara"),
    (re.compile(r"\bjumlah\s+tamu(?:\s+yang)?\s+menginap\b", re.IGNORECASE), "Jumlah Tamu Menginap"),
    (re.compile(r"\b(?:tingkat\s+)?pengangguran(?:\s+terbuka)?\b", re.IGNORECASE), "Tingkat Pengangguran Terbuka"),
    (re.compile(r"\b(?:persentase\s+)?penduduk\s+miskin\b|\bkemiskinan\b", re.IGNORECASE), "Kemiskinan"),
    (re.compile(r"\bgini\s+ratio\b|\bketimpangan\b", re.IGNORECASE), "Gini Ratio"),
    (re.compile(r"\b(?:nilai\s+)?ekspor\b", re.IGNORECASE), "Ekspor"),
    (re.compile(r"\b(?:nilai\s+)?impor\b", re.IGNORECASE), "Impor"),
    (re.compile(r"\binflasi\b", re.IGNORECASE), "Inflasi"),
    (re.compile(r"\bdeflasi\b", re.IGNORECASE), "Deflasi"),
)
MEASUREMENT_CUE = re.compile(
    r"\b(?:tercatat|sebesar|sebanyak|mencapai|menjadi|berjumlah|senilai|"
    r"berada\s+pada|naik|turun|meningkat|menurun|bertambah|berkurang)\b",
    re.IGNORECASE,
)
NON_ACTUAL_CUE = re.compile(
    r"\b(?:target|sasaran|proyeksi|perkiraan|estimasi|simulasi|contoh|nomor|kode|slide|halaman)\b",
    re.IGNORECASE,
)
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
SOURCE_DOCUMENT_TYPES = {"bahan_paparan", "narasi_pimpinan"}
SOURCE_PRIORITY = {"bahan_paparan": 0, "narasi_pimpinan": 1}


@dataclass(frozen=True)
class SemanticIndicatorValue:
    indicator_name: str
    value_text: str
    numeric_value: Decimal
    unit: str | None
    period_label: str | None
    data_type: str
    comparison_basis: str | None
    value_role: str
    metadata_text: str
    page_number: int
    source_hash: str


def _normalized(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def _numeric_identity(value: Decimal | None) -> str:
    if value is None:
        return ""
    return format(value.normalize(), "f")


def _row_identity(
    indicator_name: str,
    numeric_value: Decimal | None,
    unit: str | None,
    period_label: str | None,
    data_type: str,
    comparison_basis: str | None,
    value_role: str,
) -> str:
    """Identitas data untuk menghapus duplikat yang sama persis antardokumen."""
    return "|".join((
        _normalized(indicator_name),
        _numeric_identity(numeric_value),
        _normalized(unit or ""),
        _normalized(period_label or ""),
        data_type,
        comparison_basis or "",
        value_role,
    ))


def _master_indicator_name(mention: NumberMention, masters: list[Indicator]) -> str | None:
    context = _normalized(mention.context_text)
    for master in sorted(masters, key=lambda item: len(item.nama_indikator), reverse=True):
        name = _normalized(master.nama_indikator)
        written_acronym = re.search(r"\(([A-Z]{2,8})\)", master.nama_indikator)
        if name in context or (
            written_acronym
            and re.search(rf"\b{re.escape(written_acronym.group(1).lower())}\b", context)
        ):
            return master.nama_indikator
    return None


def _base_indicator_name(mention: NumberMention, masters: list[Indicator]) -> str | None:
    master_name = _master_indicator_name(mention, masters)
    if master_name:
        return master_name
    for pattern, name in INDICATOR_PATTERNS:
        if pattern.search(mention.context_text):
            return name
    return None


def _nearby_qualifiers(mention: NumberMention) -> list[str]:
    before = mention.text[max(0, mention.start - 150):mention.start].lower()
    after = mention.text[mention.end:min(len(mention.text), mention.end + 100)].lower()
    sentence = mention.context_text.lower()
    qualifiers: list[str] = []

    if re.search(r"\bhotel\s+nonbintang\b|\bakomodasi\s+lainnya\b", sentence):
        qualifiers.append("Hotel Nonbintang")
    elif re.search(r"\bhotel\s+bintang\b", sentence):
        qualifiers.append("Hotel Bintang")

    if re.search(r"\bjumlah\s+tamu\b", before) and re.search(r"\bterdiri\s+dari\b", after[:45]):
        qualifiers.append("Total")
    elif re.search(r"\btamu\s+domestik\b|\bdomestik\b", after[:60]):
        qualifiers.append("Domestik")
    elif re.search(r"\btamu\s+mancanegara\b|\bmancanegara\b", after[:70]):
        qualifiers.append("Mancanegara")

    direction_window = f"{before[-80:]} {after[:40]}"
    if re.search(r"\btujuan\b", direction_window):
        qualifiers.append("Tujuan")
    elif re.search(r"\basal\b|\bberasal\b", direction_window):
        qualifiers.append("Asal")

    if mention.subject_label:
        qualifiers.append(mention.subject_label)
    return list(dict.fromkeys(qualifiers))


def _semantic_name(mention: NumberMention, masters: list[Indicator]) -> str | None:
    base = _base_indicator_name(mention, masters)
    if not base:
        return None
    qualifiers = _nearby_qualifiers(mention)
    if mention.value_role == "change":
        qualifiers.append("Perubahan")
    elif mention.value_role == "contribution":
        qualifiers.append("Andil")
    return " — ".join([base, *dict.fromkeys(qualifiers)])


def _has_clear_value_relation(mention: NumberMention) -> bool:
    local = mention.text[max(0, mention.start - 90):min(len(mention.text), mention.end + 65)]
    if NON_ACTUAL_CUE.search(mention.context_text):
        return False
    if mention.unit or mention.range_min is not None:
        return True
    return bool(MEASUREMENT_CUE.search(local))


def _data_type(mention: NumberMention) -> str:
    if mention.range_min is not None:
        return "range"
    unit = mention.unit
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


def extract_semantic_indicator_values(
    document: Document, masters: list[Indicator]
) -> list[SemanticIndicatorValue]:
    """Ekstrak hanya angka yang memiliki indikator dan relasi nilai yang jelas."""
    rows: list[SemanticIndicatorValue] = []
    seen: set[str] = set()
    for mention in _mentions(document):
        indicator_name = _semantic_name(mention, masters)
        if not indicator_name or not _has_clear_value_relation(mention):
            continue
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
        rows.append(SemanticIndicatorValue(
            indicator_name=indicator_name,
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
        ))
    return rows


def sync_presentation_indicators(
    db: Session,
    document: Document,
    created_by: uuid.UUID,
) -> list[PresentationIndicator]:
    """Gabungkan Bahan Paparan dan Narasi aktif, dengan Paparan sebagai prioritas."""
    if document.document_type not in SOURCE_DOCUMENT_TYPES:
        return []

    previous = list(db.scalars(
        select(PresentationIndicator).where(PresentationIndicator.brs_id == document.brs_id)
    ))
    annotations: dict[str, tuple[str | None, str | None]] = {}
    for item in previous:
        if not item.analysis and not item.phenomenon:
            continue
        identity = _row_identity(
            item.indicator_name, item.numeric_value, item.unit, item.period_label,
            item.data_type, item.comparison_basis, item.value_role,
        )
        annotations.setdefault(identity, (item.analysis, item.phenomenon))

    db.execute(delete(PresentationIndicator).where(PresentationIndicator.brs_id == document.brs_id))
    source_documents = list(db.scalars(
        select(Document)
        .options(selectinload(Document.contents))
        .where(
            Document.brs_id == document.brs_id,
            Document.document_type.in_(SOURCE_DOCUMENT_TYPES),
            Document.status == "active",
            Document.extraction_status == "completed",
        )
    ).unique())
    source_documents.sort(key=lambda item: SOURCE_PRIORITY[item.document_type])
    if not source_documents:
        return []

    rows: list[PresentationIndicator] = []
    seen: set[str] = set()
    masters = list(db.scalars(select(Indicator).where(Indicator.is_active.is_(True))))
    for source_document in source_documents:
        for extracted in extract_semantic_indicator_values(source_document, masters):
            identity = _row_identity(
                extracted.indicator_name, extracted.numeric_value, extracted.unit,
                extracted.period_label, extracted.data_type,
                extracted.comparison_basis, extracted.value_role,
            )
            if identity in seen:
                continue
            seen.add(identity)
            analysis, phenomenon = annotations.get(identity, (None, None))
            rows.append(PresentationIndicator(
                brs_id=document.brs_id,
                document_id=source_document.id,
                indicator_name=extracted.indicator_name,
                value_text=extracted.value_text,
                numeric_value=extracted.numeric_value,
                unit=extracted.unit,
                period_label=extracted.period_label,
                data_type=extracted.data_type,
                comparison_basis=extracted.comparison_basis,
                value_role=extracted.value_role,
                metadata_text=extracted.metadata_text,
                page_number=extracted.page_number,
                source_hash=extracted.source_hash,
                analysis=analysis,
                phenomenon=phenomenon,
                created_by=created_by,
            ))
    db.add_all(rows)
    return rows
