import re
import uuid
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from itertools import combinations

from app.models.document import Document


DOCUMENT_LABELS = {
    "bahan_publikasi": "BRS / Bahan Publikasi",
    "bahan_paparan": "Bahan Paparan",
    "narasi_pimpinan": "Narasi Pimpinan",
}
DOCUMENT_ORDER = {document_type: index for index, document_type in enumerate(DOCUMENT_LABELS)}
NUMBER_PATTERN = re.compile(
    r"(?<![\w])[-+]?(?:\d{1,3}(?:[.\s]\d{3})+(?:,\d+)?|\d+\.\d+|\d+(?:,\d+)?)(?![\w])"
)
WORD_PATTERN = re.compile(r"[a-zA-ZÀ-ÿ]{3,}")
YEAR_MIN = 1900
YEAR_MAX = 2100
CONTEXT_RADIUS = 190
MAX_LANGUAGE_FINDINGS_PER_RULE = 20
SEGMENT_BOUNDARY_PATTERN = re.compile(
    r"[\n\r\u2022\u25aa\u25a0\u25a1\uf0b7\ufffd]+|(?<=[!?])\s+|(?<=\.)\s+(?=[A-ZÀ-Ý])"
)
MONTH_NAMES = (
    "januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|"
    "november|desember"
)
MONTH_NUMBER = {
    "januari": "01", "februari": "02", "maret": "03", "april": "04",
    "mei": "05", "juni": "06", "juli": "07", "agustus": "08",
    "september": "09", "oktober": "10", "november": "11", "desember": "12",
}
PERIOD_PATTERN = re.compile(
    rf"\b(?P<month>{MONTH_NAMES})(?:\s+(?P<year>(?:19|20)\d{{2}}))?\b",
    re.IGNORECASE,
)
METADATA_PREFIX_PATTERN = re.compile(
    r"(?:\bno(?:mor)?|\bbrs|\bhalaman|\bpage|\bslide|\btabel|\bgambar|\bbab|"
    r"\blampiran|\bvolume|\bvol|\bedisi|\bpukul)\.?\s*$",
    re.IGNORECASE,
)
STRONG_INDICATOR_TERMS = {
    "deflasi", "ekspor", "gini", "impor", "inflasi", "kemiskinan", "ketimpangan",
    "ntp", "pdrb", "pengangguran", "rlmt", "tpk", "wisman", "wisnus",
}
STATISTICAL_CUES = STRONG_INDICATOR_TERMS | {
    "akomodasi", "andil", "domestik", "harga", "hotel", "indeks", "kamar", "kunjungan",
    "mancanegara", "menginap", "penduduk", "penghunian", "perjalanan", "pertumbuhan",
    "produksi", "tamu", "wisatawan",
}

# Kata umum yang tidak membantu membedakan konteks indikator.
STOP_WORDS = {
    "adalah", "akan", "antara", "atau", "bagi", "bahwa", "bulan", "dalam", "dan",
    "dari", "data", "dengan", "dibanding", "dibandingkan", "dua", "jumlah", "lebih",
    "menjadi", "mencapai", "naik", "nilai", "pada", "persen", "periode", "ribu",
    "sebesar", "sebanyak", "sedangkan", "selama", "tahun", "telah", "tercatat",
    "terhadap", "turun", "untuk", "yang", "januari", "februari", "maret", "april",
    "mei", "juni", "juli", "agustus", "september", "oktober", "november", "desember",
    "provinsi", "sulawesi", "tengah",
}


@dataclass(frozen=True)
class NumberMention:
    key: str
    raw: str
    value: Decimal
    page_number: int
    section_label: str
    text: str
    start: int
    end: int
    context_text: str
    keywords: tuple[str, ...]
    unit: str | None
    period_key: str | None
    period_label: str | None


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
    comparison_values: dict[str, dict[str, str | int | None]] | None = None


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
class MentionPair:
    left_document: Document
    left: NumberMention
    right_document: Document
    right: NumberMention
    context_score: Decimal


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


def _unit(text: str, start: int, end: int) -> str | None:
    window_start = max(0, start - 35)
    nearby = text[window_start:min(len(text), end + 55)].lower()
    unit_patterns = (
        ("percentage_point", r"\bpersen\s+poin\b|\bpercentage\s+point"),
        ("percent", r"%|\bpersen(?:tase)?\b|\bpersentase\b"),
        ("currency", r"\brp\.?\s*|\brupiah\b"),
        ("person", r"\borang\b|\btamu\b"),
        ("trip", r"\bperjalanan\b|\bkunjungan\b"),
        ("day", r"\bhari\b"),
        ("room", r"\bkamar\b|\broom\b"),
        ("index", r"\bindeks\b|\bindex\b"),
        ("ton", r"\bton\b"),
    )
    candidates: list[tuple[int, int, str]] = []
    number_center = ((start + end) // 2) - window_start
    for priority, (name, pattern) in enumerate(unit_patterns):
        for match in re.finditer(pattern, nearby):
            unit_center = (match.start() + match.end()) // 2
            candidates.append((abs(unit_center - number_center), priority, name))
    return min(candidates)[2] if candidates else None


def _segment_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    segment_start = 0
    segment_end = len(text)
    for boundary in SEGMENT_BOUNDARY_PATTERN.finditer(text):
        if boundary.end() <= start:
            segment_start = boundary.end()
            continue
        if boundary.start() >= end:
            segment_end = boundary.start()
            break
    return segment_start, segment_end


def _segment(text: str, start: int, end: int) -> str:
    segment_start, segment_end = _segment_bounds(text, start, end)
    if segment_end - segment_start > CONTEXT_RADIUS * 2:
        segment_start = max(segment_start, start - CONTEXT_RADIUS)
        segment_end = min(segment_end, end + CONTEXT_RADIUS)
    return " ".join(text[segment_start:segment_end].split())


def _keywords(context: str) -> tuple[str, ...]:
    words = [word.lower() for word in WORD_PATTERN.findall(context)]
    filtered = [word for word in words if word not in STOP_WORDS]
    lowered = context.lower()
    aliases = {
        "wisnus": ("wisatawan nusantara", "perjalanan nusantara"),
        "wisman": ("wisatawan mancanegara",),
        "tpk": ("tingkat penghunian kamar",),
        "rlmt": ("rata-rata lama menginap", "rata rata lama menginap"),
        "ntp": ("nilai tukar petani",),
    }
    for alias, phrases in aliases.items():
        if any(phrase in lowered for phrase in phrases):
            filtered.append(alias)
    return tuple(dict.fromkeys(filtered))


def _is_year(raw: str, value: Decimal) -> bool:
    return value == value.to_integral_value() and YEAR_MIN <= int(value) <= YEAR_MAX and len(raw.strip()) == 4


def _is_metadata_number(text: str, start: int, end: int, value: Decimal) -> bool:
    before = text[max(0, start - 28):start]
    after = text[end:min(len(text), end + 28)]
    if (start > 0 and text[start - 1] in "/\\") or (end < len(text) and text[end] in "/\\"):
        return True
    if METADATA_PREFIX_PATTERN.search(before):
        return True
    if value == value.to_integral_value() and 1 <= int(value) <= 31:
        if re.match(rf"\s*(?:{MONTH_NAMES})\b", after, re.IGNORECASE):
            return True
    if re.search(r"(?:tanggal|rilis)\s*$", before, re.IGNORECASE):
        return True
    return False


def _is_statistical_number(context: str, unit: str | None, keywords: tuple[str, ...]) -> bool:
    if unit:
        return True
    words = set(keywords)
    if words & STATISTICAL_CUES:
        return True
    return bool(re.search(r"\b(?:total|rata-rata|rasio|laju|kontribusi)\b", context, re.IGNORECASE))


def _period(text: str, start: int, end: int) -> tuple[str | None, str | None]:
    """Return the closest reporting month (and year, when stated) to a number."""
    segment_start, segment_end = _segment_bounds(text, start, end)
    window_start = max(segment_start, start - 150)
    window_end = min(segment_end, end + 100)
    window = text[window_start:window_end]
    number_center = ((start + end) // 2) - window_start
    candidates: list[tuple[int, int, re.Match[str]]] = []
    for match in PERIOD_PATTERN.finditer(window):
        month_center = (match.start() + match.end()) // 2
        prefix = window[max(0, match.start() - 20):match.start()]
        comparison_penalty = 80 if re.search(r"\bdibanding(?:kan)?\s*$", prefix, re.IGNORECASE) else 0
        # Bila jaraknya sama, periode sebelum angka lebih mungkin merupakan periode nilai utama.
        position_penalty = 0 if match.end() <= number_center else 2
        candidates.append((abs(month_center - number_center) + comparison_penalty, position_penalty, match))
    if not candidates:
        return None, None
    _, _, closest = min(candidates, key=lambda item: (item[0], item[1]))
    month = closest.group("month").lower()
    year = closest.group("year")
    key = f"{MONTH_NUMBER[month]}:{year or ''}"
    label = f"{month.title()}{f' {year}' if year else ''}"
    return key, label


def _mentions(document: Document) -> list[NumberMention]:
    result: list[NumberMention] = []
    for content in document.contents:
        for ordinal, match in enumerate(NUMBER_PATTERN.finditer(content.text_content)):
            value = parse_localized_number(match.group())
            if (
                value is None
                or _is_year(match.group(), value)
                or _is_metadata_number(content.text_content, match.start(), match.end(), value)
            ):
                continue
            context = _segment(content.text_content, match.start(), match.end())
            keywords = _keywords(context)
            unit = _unit(content.text_content, match.start(), match.end())
            period_key, period_label = _period(
                content.text_content, match.start(), match.end()
            )
            if not keywords or not _is_statistical_number(context, unit, keywords):
                continue
            result.append(NumberMention(
                key=f"{document.id}:{content.page_number}:{ordinal}", raw=match.group(), value=value,
                page_number=content.page_number, section_label=content.section_label,
                text=content.text_content, start=match.start(), end=match.end(), context_text=context,
                keywords=keywords, unit=unit, period_key=period_key, period_label=period_label,
            ))
    return result


def _context(mention: NumberMention, radius: int = 95) -> str:
    del radius
    return mention.context_text


def _units_compatible(left: NumberMention, right: NumberMention) -> bool:
    return not left.unit or not right.unit or left.unit == right.unit


def _periods_compatible(left: NumberMention, right: NumberMention) -> bool:
    if not left.period_key or not right.period_key:
        return True
    left_month, left_year = left.period_key.split(":", 1)
    right_month, right_year = right.period_key.split(":", 1)
    if left_month != right_month:
        return False
    return not left_year or not right_year or left_year == right_year


def _candidate_score(
    left: NumberMention,
    right: NumberMention,
) -> Decimal | None:
    if not _units_compatible(left, right) or not _periods_compatible(left, right):
        return None
    left_words = set(left.keywords)
    right_words = set(right.keywords)
    common = left_words & right_words
    overlap = Decimal(len(common)) / Decimal(max(1, min(len(left_words), len(right_words))))
    exact_bonus = Decimal("0.30") if left.value == right.value else Decimal("0")
    unit_bonus = Decimal("0.10") if left.unit and left.unit == right.unit else Decimal("0")
    period_bonus = Decimal("0.45") if left.period_key and right.period_key else Decimal("0")

    if len(common) >= 2 and overlap >= Decimal("0.20"):
        return overlap + exact_bonus + unit_bonus + period_bonus
    if common & STRONG_INDICATOR_TERMS:
        return overlap + Decimal("0.35") + exact_bonus + unit_bonus + period_bonus
    if len(common) == 1 and left.value == right.value and overlap >= Decimal("0.20"):
        return overlap + exact_bonus + unit_bonus + period_bonus
    return None


def _match_pair(
    left_document: Document,
    left_mentions: list[NumberMention],
    right_document: Document,
    right_mentions: list[NumberMention],
) -> list[MentionPair]:
    candidates: list[tuple[Decimal, int, int]] = []
    for left_index, left in enumerate(left_mentions):
        for right_index, right in enumerate(right_mentions):
            score = _candidate_score(left, right)
            if score is not None:
                candidates.append((score, left_index, right_index))
    candidates.sort(
        key=lambda item: (item[0], left_mentions[item[1]].value == right_mentions[item[2]].value),
        reverse=True,
    )

    pairs: list[MentionPair] = []
    used_left: set[int] = set()
    used_right: set[int] = set()
    for score, left_index, right_index in candidates:
        if left_index in used_left or right_index in used_right:
            continue
        used_left.add(left_index)
        used_right.add(right_index)
        pairs.append(MentionPair(
            left_document=left_document, left=left_mentions[left_index],
            right_document=right_document, right=right_mentions[right_index], context_score=score,
        ))
    return pairs


def _common_label(mentions: list[NumberMention]) -> str:
    if not mentions:
        return "Angka pada konteks serupa"
    common = set(mentions[0].keywords)
    for mention in mentions[1:]:
        common &= set(mention.keywords)
    ordered = [word for word in mentions[0].keywords if word in common]
    if not ordered:
        ordered = list(mentions[0].keywords)
    strong = [word for word in ordered if word in STRONG_INDICATOR_TERMS]
    if strong:
        display = {
            "ntp": "NTP", "pdrb": "PDRB", "rlmt": "RLMT", "tpk": "TPK",
            "wisman": "Wisman", "wisnus": "Wisnus",
        }
        label = display.get(strong[0], strong[0].title())
    else:
        label = " ".join(ordered[:7]).strip().title()
    period_mentions = [mention for mention in mentions if mention.period_key]
    if period_mentions and all(
        _periods_compatible(period_mentions[0], mention)
        for mention in period_mentions[1:]
    ):
        period_label = max(
            (mention.period_label for mention in period_mentions if mention.period_label),
            key=len,
            default=None,
        )
        if period_label:
            label = f"{label or 'Indikator'} • {period_label}"
    return label or "Angka pada konteks serupa"


def _score(total: int, findings: list[Finding]) -> Decimal:
    if total <= 0:
        return Decimal("100.00")
    weights = {"error": Decimal("1"), "warning": Decimal("0.5"), "suggestion": Decimal("0.2")}
    penalty = sum((weights[item.severity] for item in findings), Decimal("0"))
    score = max(Decimal("0"), Decimal("100") * (Decimal("1") - penalty / Decimal(total)))
    return score.quantize(Decimal("0.01"))


def _comparison_values(
    mentions_by_type: dict[str, tuple[Document, NumberMention]],
) -> dict[str, dict[str, str | int | None]]:
    values: dict[str, dict[str, str | int | None]] = {}
    for document_type, label in DOCUMENT_LABELS.items():
        item = mentions_by_type.get(document_type)
        if not item:
            continue
        document, mention = item
        values[document_type] = {
            "label": label,
            "value": mention.raw,
            "page_number": mention.page_number,
            "section_label": mention.section_label,
            "context": _context(mention),
            "document_id": str(document.id),
        }
    return values


def _document_comparison(documents: list[Document]) -> tuple[list[Finding], list[Finding], int, int, int]:
    documents = sorted(documents, key=lambda item: DOCUMENT_ORDER[item.document_type])
    mentions_by_document = {document.id: _mentions(document) for document in documents}
    all_pairs: list[MentionPair] = []
    for left_document, right_document in combinations(documents, 2):
        all_pairs.extend(_match_pair(
            left_document, mentions_by_document[left_document.id],
            right_document, mentions_by_document[right_document.id],
        ))

    parent: dict[str, str] = {}
    mention_lookup: dict[str, tuple[Document, NumberMention]] = {}

    def find(key: str) -> str:
        parent.setdefault(key, key)
        if parent[key] != key:
            parent[key] = find(parent[key])
        return parent[key]

    def union(left_key: str, right_key: str) -> None:
        left_root, right_root = find(left_key), find(right_key)
        if left_root != right_root:
            parent[right_root] = left_root

    for pair in all_pairs:
        mention_lookup[pair.left.key] = (pair.left_document, pair.left)
        mention_lookup[pair.right.key] = (pair.right_document, pair.right)
        union(pair.left.key, pair.right.key)

    clusters: dict[str, list[tuple[Document, NumberMention]]] = defaultdict(list)
    for key, item in mention_lookup.items():
        clusters[find(key)].append(item)

    comparison_findings: list[Finding] = []
    comparison_passed = 0
    for cluster in clusters.values():
        mentions_by_type: dict[str, tuple[Document, NumberMention]] = {}
        for document, mention in cluster:
            mentions_by_type.setdefault(document.document_type, (document, mention))
        if len(mentions_by_type) < 2:
            continue
        values = _comparison_values(mentions_by_type)
        mentions = [mention for _, mention in mentions_by_type.values()]
        normalized_values = {mention.value for mention in mentions}
        if len(normalized_values) == 1:
            comparison_passed += 1
            continue

        value_groups: dict[Decimal, list[tuple[Document, NumberMention]]] = defaultdict(list)
        for document, mention in mentions_by_type.values():
            value_groups[mention.value].append((document, mention))
        consensus = max(value_groups.values(), key=len)
        _, reference_mention = consensus[0]
        outliers = [
            (document, mention)
            for document, mention in mentions_by_type.values()
            if mention.value != reference_mention.value
        ]
        if len(consensus) == 1:
            reference_type = next(
                document_type for document_type in DOCUMENT_LABELS
                if document_type in mentions_by_type
            )
            _, reference_mention = mentions_by_type[reference_type]
            outliers = [
                (document, mention)
                for document, mention in mentions_by_type.values()
                if document.document_type != reference_type
            ]
        target_document, target_mention = outliers[0]
        actual = " | ".join(
            f"{DOCUMENT_LABELS[document.document_type]}: {mention.raw}"
            for document, mention in outliers
        )
        evidence = " || ".join(
            f"{DOCUMENT_LABELS[document.document_type]} ({mention.section_label}): {_context(mention)}"
            for document, mention in mentions_by_type.values()
        )
        comparison_findings.append(Finding(
            check_type="cross_document", severity="error", document_id=target_document.id,
            field_name=_common_label(mentions), expected_value=reference_mention.raw,
            actual_value=actual,
            message=(
                f"Nilai indikator dan periode yang sama berbeda pada "
                f"{len(mentions_by_type)} dokumen."
            ),
            suggestion="Periksa sumber yang dibandingkan, tentukan angka yang benar, lalu samakan dokumennya.",
            page_number=target_mention.page_number, context_text=evidence,
            comparison_values=values,
        ))

    # Kelengkapan file sudah divalidasi sebelum mesin berjalan. Indikator yang
    # hanya muncul pada satu dokumen sengaja tidak dihitung dan tidak ditampilkan.
    return [], comparison_findings, 1, 1, comparison_passed


def _check_language(documents: list[Document]) -> tuple[list[Finding], int, int]:
    findings: list[Finding] = []
    total = 0
    passed = 0
    for document in documents:
        label = DOCUMENT_LABELS.get(document.document_type, document.document_type)
        for content in document.contents:
            for rule in LANGUAGE_RULES:
                matches = list(rule.pattern.finditer(content.text_content))[:MAX_LANGUAGE_FINDINGS_PER_RULE]
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


def run_statcheck(documents: list[Document]) -> EngineResult:
    coverage_findings, comparison_findings, coverage_total, coverage_passed, comparison_passed = _document_comparison(documents)
    language_findings, language_total, language_passed = _check_language(documents)
    comparison_total = comparison_passed + len(comparison_findings)
    findings = coverage_findings + comparison_findings + language_findings
    total = coverage_total + comparison_total + language_total
    passed = coverage_passed + comparison_passed + language_passed
    return EngineResult(
        findings=findings, total_checks=total, passed_checks=passed,
        # Nama kolom dipertahankan agar database lama tetap kompatibel. Mulai
        # Mulai rules-v2.2-indicator-periods nilainya adalah skor kelengkapan file.
        data_consistency_score=_score(coverage_total, coverage_findings),
        cross_document_score=_score(comparison_total, comparison_findings),
        language_score=_score(language_total, language_findings),
        overall_score=_score(total, findings),
    )
