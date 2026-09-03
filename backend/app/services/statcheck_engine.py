import re
import uuid
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from itertools import combinations

from app.models.brs import BRSData
from app.models.document import Document, DocumentContent


DOCUMENT_LABELS = {
    "bahan_publikasi": "Bahan Publikasi",
    "bahan_paparan": "Bahan Paparan",
    "narasi_pimpinan": "Narasi Pimpinan",
}
NUMBER_PATTERN = re.compile(
    r"(?<![\w])[-+]?(?:\d{1,3}(?:[.\s]\d{3})+(?:,\d+)?|\d+\.\d+|\d+(?:,\d+)?)(?![\w])"
)
WORD_PATTERN = re.compile(r"[a-zA-ZÀ-ÿ]{3,}")
STOP_WORDS = {
    "dan", "yang", "dari", "pada", "untuk", "dengan", "atau", "sebesar", "jumlah",
    "periode", "data", "provinsi", "sulawesi", "tengah",
}


@dataclass(frozen=True)
class NumberMention:
    raw: str
    value: Decimal
    page_number: int
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class Finding:
    check_type: str
    severity: str
    message: str
    document_id: uuid.UUID | None = None
    brs_data_id: uuid.UUID | None = None
    field_name: str | None = None
    expected_value: str | None = None
    actual_value: str | None = None
    suggestion: str | None = None
    page_number: int | None = None
    context_text: str | None = None


@dataclass(frozen=True)
class EngineResult:
    findings: list[Finding]
    total_checks: int
    passed_checks: int
    data_consistency_score: Decimal
    cross_document_score: Decimal
    language_score: Decimal
    overall_score: Decimal


@dataclass(frozen=True)
class ResolvedValue:
    mention: NumberMention | None
    exact: bool


@dataclass(frozen=True)
class LanguageRule:
    code: str
    pattern: re.Pattern[str]
    severity: str
    message: str
    suggestion: str


LANGUAGE_RULES = (
    LanguageRule("double_space", re.compile(r"[ \t]{2,}"), "warning", "Terdapat spasi ganda.", "Gunakan satu spasi antar kata."),
    LanguageRule("space_before_punctuation", re.compile(r"\s+[,;:]"), "warning", "Terdapat spasi sebelum tanda baca.", "Hapus spasi sebelum tanda baca."),
    LanguageRule("percent_symbol", re.compile(r"(?<!\w)\d+(?:[.,]\d+)?\s*%"), "suggestion", "Format persen menggunakan simbol %.", "Dalam narasi resmi, pertimbangkan menulis kata 'persen'."),
    LanguageRule("naik_turun_sebesar", re.compile(r"\b(?:naik|turun)\s+sebesar\b", re.IGNORECASE), "suggestion", "Frasa dapat dibuat lebih efektif.", "Gunakan 'naik' atau 'turun' langsung diikuti nilai."),
    LanguageRule("dibanding", re.compile(r"\bdibanding\b(?!kan)", re.IGNORECASE), "suggestion", "Penggunaan kata 'dibanding' kurang baku dalam konteks ini.", "Gunakan 'dibandingkan'."),
    LanguageRule("duplicate_word", re.compile(r"\b([a-zA-ZÀ-ÿ]{3,})\s+\1\b", re.IGNORECASE), "warning", "Terdapat kata yang berulang.", "Hapus salah satu kata yang berulang."),
    LanguageRule("lowercase_month", re.compile(r"\b(?:januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\b"), "suggestion", "Nama bulan ditulis dengan huruf kecil.", "Gunakan huruf kapital pada nama bulan."),
)


def parse_localized_number(raw: str) -> Decimal | None:
    value = raw.strip().replace(" ", "")
    if not value:
        return None
    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    elif value.count(".") == 1:
        before, after = value.split(".")
        before_digits = before.lstrip("+-")
        if len(after) == 3 and 1 <= len(before_digits) <= 3:
            value = before + after
    elif value.count(".") > 1:
        value = value.replace(".", "")
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def format_decimal_id(value: Decimal) -> str:
    plain = format(value, "f")
    if "." in plain:
        plain = plain.rstrip("0").rstrip(".")
    integer, _, fraction = plain.partition(".")
    sign = "-" if integer.startswith("-") else ""
    grouped = f"{int(integer or '0'):,}".replace(",", ".")
    if sign and not grouped.startswith("-"):
        grouped = sign + grouped
    return f"{grouped},{fraction}" if fraction else grouped


def _mentions(content: DocumentContent) -> list[NumberMention]:
    result: list[NumberMention] = []
    for match in NUMBER_PATTERN.finditer(content.text_content):
        value = parse_localized_number(match.group())
        if value is not None:
            result.append(NumberMention(match.group(), value, content.page_number, content.text_content, match.start(), match.end()))
    return result


def _field_name(item: BRSData) -> str:
    return " — ".join(filter(None, (item.indicator.nama_indikator, item.sub_indikator)))


def _keywords(item: BRSData) -> set[str]:
    source = " ".join(filter(None, (item.indicator.nama_indikator, item.sub_indikator, item.deskripsi_periode)))
    return {word.lower() for word in WORD_PATTERN.findall(source) if word.lower() not in STOP_WORDS}


def _context(mention: NumberMention) -> str:
    start = max(0, mention.start - 90)
    end = min(len(mention.text), mention.end + 90)
    return " ".join(mention.text[start:end].split())


def resolve_document_value(document: Document, item: BRSData) -> ResolvedValue:
    expected = Decimal(item.nilai_data)
    mentions = [mention for content in document.contents for mention in _mentions(content)]
    keywords = _keywords(item)

    def keyword_score(mention: NumberMention) -> int:
        nearby = mention.text[max(0, mention.start - 180):min(len(mention.text), mention.end + 180)].lower()
        return sum(word in nearby for word in keywords)

    exact = [mention for mention in mentions if mention.value == expected]
    anchored_exact = [(keyword_score(mention), mention) for mention in exact]
    anchored_exact.sort(key=lambda candidate: candidate[0], reverse=True)
    if anchored_exact and (anchored_exact[0][0] > 0 or len(mentions) == 1):
        return ResolvedValue(anchored_exact[0][1], True)

    candidates: list[tuple[int, Decimal, NumberMention]] = []
    for mention in mentions:
        score = keyword_score(mention)
        if score:
            distance = abs(mention.value - expected) / max(abs(expected), Decimal("1"))
            candidates.append((score, -distance, mention))
    if not candidates:
        return ResolvedValue(None, False)
    candidates.sort(key=lambda candidate: (candidate[0], candidate[1]), reverse=True)
    return ResolvedValue(candidates[0][2], False)


def _score(total: int, findings: list[Finding]) -> Decimal:
    if total <= 0:
        return Decimal("100.00")
    weights = {"error": Decimal("1"), "warning": Decimal("0.5"), "suggestion": Decimal("0.2")}
    penalty = sum((weights[item.severity] for item in findings), Decimal("0"))
    score = max(Decimal("0"), Decimal("100") * (Decimal("1") - penalty / Decimal(total)))
    return score.quantize(Decimal("0.01"))


def _check_data_consistency(data_items: list[BRSData], documents: list[Document]) -> tuple[list[Finding], int, int, dict[tuple[uuid.UUID, uuid.UUID], ResolvedValue]]:
    findings: list[Finding] = []
    passed = 0
    resolved: dict[tuple[uuid.UUID, uuid.UUID], ResolvedValue] = {}
    for item in data_items:
        expected = format_decimal_id(Decimal(item.nilai_data))
        for document in documents:
            value = resolve_document_value(document, item)
            resolved[(item.id, document.id)] = value
            label = DOCUMENT_LABELS.get(document.document_type, document.document_type)
            if value.exact:
                passed += 1
            elif value.mention:
                findings.append(Finding(
                    check_type="data_consistency", severity="error", document_id=document.id,
                    brs_data_id=item.id, field_name=_field_name(item), expected_value=expected,
                    actual_value=value.mention.raw,
                    message=f"Nilai {_field_name(item)} pada {label} berbeda dengan Data BRS.",
                    suggestion="Periksa dan samakan angka dengan data yang telah divalidasi.",
                    page_number=value.mention.page_number, context_text=_context(value.mention),
                ))
            else:
                findings.append(Finding(
                    check_type="data_consistency", severity="warning", document_id=document.id,
                    brs_data_id=item.id, field_name=_field_name(item), expected_value=expected,
                    message=f"Nilai {_field_name(item)} tidak ditemukan pada {label}.",
                    suggestion="Pastikan indikator dan nilainya tercantum atau periksa hasil ekstraksi teks.",
                ))
    return findings, len(data_items) * len(documents), passed, resolved


def _check_cross_document(data_items: list[BRSData], documents: list[Document], resolved: dict[tuple[uuid.UUID, uuid.UUID], ResolvedValue]) -> tuple[list[Finding], int, int]:
    findings: list[Finding] = []
    total = 0
    passed = 0
    for item in data_items:
        for left, right in combinations(documents, 2):
            total += 1
            left_value = resolved[(item.id, left.id)].mention
            right_value = resolved[(item.id, right.id)].mention
            left_label = DOCUMENT_LABELS.get(left.document_type, left.document_type)
            right_label = DOCUMENT_LABELS.get(right.document_type, right.document_type)
            if left_value and right_value and left_value.value == right_value.value:
                passed += 1
            elif left_value and right_value:
                findings.append(Finding(
                    check_type="cross_document", severity="error", brs_data_id=item.id,
                    field_name=_field_name(item), expected_value=left_value.raw,
                    actual_value=right_value.raw,
                    message=f"Nilai {_field_name(item)} berbeda antara {left_label} dan {right_label}.",
                    suggestion="Tentukan nilai yang benar lalu perbarui dokumen yang tidak sesuai.",
                    context_text=f"{left_label}: {left_value.raw} | {right_label}: {right_value.raw}",
                ))
            else:
                missing = [label for label, value in ((left_label, left_value), (right_label, right_value)) if value is None]
                findings.append(Finding(
                    check_type="cross_document", severity="warning", brs_data_id=item.id,
                    field_name=_field_name(item),
                    message=f"Perbandingan {_field_name(item)} belum lengkap; nilai tidak ditemukan pada {', '.join(missing)}.",
                    suggestion="Periksa kelengkapan indikator pada kedua dokumen.",
                ))
    return findings, total, passed


def _check_language(documents: list[Document]) -> tuple[list[Finding], int, int]:
    findings: list[Finding] = []
    total = 0
    passed = 0
    for document in documents:
        label = DOCUMENT_LABELS.get(document.document_type, document.document_type)
        for content in document.contents:
            for rule in LANGUAGE_RULES:
                matches = list(rule.pattern.finditer(content.text_content))[:20]
                total += max(1, len(matches))
                if not matches:
                    passed += 1
                    continue
                for match in matches:
                    start = max(0, match.start() - 70)
                    end = min(len(content.text_content), match.end() + 70)
                    findings.append(Finding(
                        check_type="language", severity=rule.severity, document_id=document.id,
                        field_name=rule.code, actual_value=match.group(),
                        message=f"{rule.message} ({label}, {content.section_label})",
                        suggestion=rule.suggestion, page_number=content.page_number,
                        context_text=" ".join(content.text_content[start:end].split()),
                    ))
    return findings, total, passed


def run_statcheck(data_items: list[BRSData], documents: list[Document]) -> EngineResult:
    data_findings, data_total, data_passed, resolved = _check_data_consistency(data_items, documents)
    cross_findings, cross_total, cross_passed = _check_cross_document(data_items, documents, resolved)
    language_findings, language_total, language_passed = _check_language(documents)
    findings = data_findings + cross_findings + language_findings
    total = data_total + cross_total + language_total
    passed = data_passed + cross_passed + language_passed
    return EngineResult(
        findings=findings, total_checks=total, passed_checks=passed,
        data_consistency_score=_score(data_total, data_findings),
        cross_document_score=_score(cross_total, cross_findings),
        language_score=_score(language_total, language_findings),
        overall_score=_score(total, findings),
    )
