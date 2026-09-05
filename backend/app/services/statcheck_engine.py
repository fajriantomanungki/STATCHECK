import re
import uuid
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from itertools import combinations
from typing import Callable

from app.models.document import Document


DOCUMENT_LABELS = {
    "bahan_publikasi": "BRS / Bahan Publikasi",
    "bahan_paparan": "Bahan Paparan",
    "narasi_pimpinan": "Narasi Pimpinan",
}
DOCUMENT_ORDER = {document_type: index for index, document_type in enumerate(DOCUMENT_LABELS)}
NUMBER_BODY = r"[-+]?(?:\d{1,3}(?:[.\s]\d{3})+(?:,\d+)?|\d+\.\d+|\d+(?:,\d+)?)"
NUMBER_PATTERN = re.compile(rf"(?<![\w]){NUMBER_BODY}(?![\w])")
RANGE_PATTERN = re.compile(
    rf"(?P<low>{NUMBER_BODY})\s*(?:hingga|sampai|s\.d\.?|[-–—])\s*(?P<high>{NUMBER_BODY})",
    re.IGNORECASE,
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
BASIS_PATTERNS = {
    "yoy": re.compile(
        r"\b(?:year[\s–—-]*on[\s–—-]*year|y[\s–—-]*o[\s–—-]*y|yoy|tahun\s+sebelumnya|tahunan)\b",
        re.IGNORECASE,
    ),
    "mtm": re.compile(
        r"\b(?:month[\s–—-]*to[\s–—-]*month|m[\s–—-]*t[\s–—-]*m|mtm|bulan\s+sebelumnya|bulanan)\b",
        re.IGNORECASE,
    ),
    "ytd": re.compile(
        r"\b(?:year[\s–—-]*to[\s–—-]*date|y[\s–—-]*t[\s–—-]*d|ytd|tahun\s+kalender|sejak\s+awal\s+tahun)\b",
        re.IGNORECASE,
    ),
    "qtq": re.compile(
        r"\b(?:quarter[\s–—-]*to[\s–—-]*quarter|q[\s–—-]*t[\s–—-]*q|qtq|triwulan\s+sebelumnya)\b",
        re.IGNORECASE,
    ),
}
BASIS_LABELS = {"yoy": "YoY", "mtm": "MtM", "ytd": "YtD", "qtq": "QtQ"}
GEOGRAPHY_PATTERN = re.compile(
    r"\b(?P<kind>Kabupaten|Kab\.?|Kota|Provinsi)\s+"
    r"(?P<name>[A-Za-zÀ-ÿ'’-]+(?:\s+[A-Za-zÀ-ÿ'’-]+){0,3})",
    re.IGNORECASE,
)
ENTITY_STOP_WORDS = {
    "adalah", "berada", "berikut", "dibandingkan", "mencapai", "naik", "pada",
    "sebesar", "sebanyak", "tercatat", "turun", "yaitu",
}
REGION_ALIASES = (
    ("provinsi:sulawesi-tengah", "Provinsi Sulawesi Tengah", re.compile(
        r"\b(?:provinsi\s+)?sulawesi\s+tengah\b|\bsulteng\b", re.IGNORECASE,
    )),
    ("kabupaten:banggai-kepulauan", "Kabupaten Banggai Kepulauan", re.compile(
        r"\b(?:(?:kabupaten|kab\.?)\s+)?banggai\s+kepulauan\b", re.IGNORECASE,
    )),
    ("kabupaten:banggai-laut", "Kabupaten Banggai Laut", re.compile(
        r"\b(?:(?:kabupaten|kab\.?)\s+)?banggai\s+laut\b", re.IGNORECASE,
    )),
    ("kabupaten:morowali-utara", "Kabupaten Morowali Utara", re.compile(
        r"\b(?:(?:kabupaten|kab\.?)\s+)?morowali\s+utara\b", re.IGNORECASE,
    )),
    ("kabupaten:parigi-moutong", "Kabupaten Parigi Moutong", re.compile(
        r"\b(?:(?:kabupaten|kab\.?)\s+)?parigi\s+moutong\b", re.IGNORECASE,
    )),
    ("kabupaten:tojo-una-una", "Kabupaten Tojo Una-Una", re.compile(
        r"\b(?:(?:kabupaten|kab\.?)\s+)?tojo\s+una[\s-]+una\b", re.IGNORECASE,
    )),
    ("kabupaten:banggai", "Kabupaten Banggai", re.compile(
        r"\b(?:(?:kabupaten|kab\.?)\s+)?banggai\b(?!\s+(?:kepulauan|laut))", re.IGNORECASE,
    )),
    ("kabupaten:buol", "Kabupaten Buol", re.compile(
        r"\b(?:(?:kabupaten|kab\.?)\s+)?buol\b", re.IGNORECASE,
    )),
    ("kabupaten:donggala", "Kabupaten Donggala", re.compile(
        r"\b(?:(?:kabupaten|kab\.?)\s+)?donggala\b", re.IGNORECASE,
    )),
    ("kabupaten:morowali", "Kabupaten Morowali", re.compile(
        r"\b(?:(?:kabupaten|kab\.?)\s+)?morowali\b(?!\s+utara)", re.IGNORECASE,
    )),
    ("kabupaten:poso", "Kabupaten Poso", re.compile(
        r"\b(?:(?:kabupaten|kab\.?)\s+)?poso\b", re.IGNORECASE,
    )),
    ("kabupaten:sigi", "Kabupaten Sigi", re.compile(
        r"\b(?:(?:kabupaten|kab\.?)\s+)?sigi\b", re.IGNORECASE,
    )),
    ("kabupaten:tolitoli", "Kabupaten Tolitoli", re.compile(
        r"\b(?:(?:kabupaten|kab\.?)\s+)?toli[\s-]?toli\b", re.IGNORECASE,
    )),
    ("kota:palu", "Kota Palu", re.compile(
        r"\b(?:kota\s+)?palu\b", re.IGNORECASE,
    )),
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

# Penanda kategori yang mengubah makna sebuah indikator. Dua angka tidak boleh
# dianggap mewakili data yang sama bila keduanya menyebut kategori yang saling
# berlawanan, walaupun nama indikator dan nilainya kebetulan sama.
QUALIFIER_PATTERNS = {
    "accommodation": (
        ("nonbintang", "Hotel nonbintang", re.compile(
            r"\b(?:hotel|akomodasi)\s+non[\s-]?bintang\b|\bakomodasi\s+lainnya\b",
            re.IGNORECASE,
        )),
        ("bintang", "Hotel bintang", re.compile(
            r"\b(?:hotel|akomodasi)\s+bintang\b", re.IGNORECASE,
        )),
    ),
    "guest": (
        ("mancanegara", "Tamu mancanegara", re.compile(
            r"\b(?:tamu|wisatawan)\s+mancanegara\b|\bwisman\b", re.IGNORECASE,
        )),
        ("domestik", "Tamu domestik", re.compile(
            r"\b(?:tamu\s+domestik|wisatawan\s+nusantara|wisnus)\b", re.IGNORECASE,
        )),
    ),
    "direction": (
        ("origin", "Asal", re.compile(r"\b(?:asal|berasal(?:\s+dari)?)\b", re.IGNORECASE)),
        ("destination", "Tujuan", re.compile(r"\b(?:tujuan|menuju)\b", re.IGNORECASE)),
    ),
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
    range_min: Decimal | None
    range_max: Decimal | None
    basis_key: str | None
    basis_label: str | None
    subject_key: str | None
    subject_label: str | None
    qualifiers: tuple[tuple[str, str], ...]
    value_role: str


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
    title: str
    message: str
    suggestion: str
    replacement: str | Callable[[re.Match[str]], str]


NONSTANDARD_WORDS = {
    "aktifitas": "aktivitas",
    "analisa": "analisis",
    "antri": "antre",
    "apotik": "apotek",
    "azas": "asas",
    "detil": "detail",
    "efektifitas": "efektivitas",
    "frekwensi": "frekuensi",
    "hakekat": "hakikat",
    "hirarki": "hierarki",
    "ijin": "izin",
    "jadual": "jadwal",
    "karir": "karier",
    "kongkrit": "konkret",
    "kwalitas": "kualitas",
    "kwantitas": "kuantitas",
    "merubah": "mengubah",
    "metoda": "metode",
    "obyek": "objek",
    "praktek": "praktik",
    "prosentase": "persentase",
    "resiko": "risiko",
    "sekedar": "sekadar",
    "sistim": "sistem",
    "subyek": "subjek",
    "survey": "survei",
    "tehnik": "teknik",
    "trampil": "terampil",
    "jaman": "zaman",
}

# Daftar ini sengaja terbatas pada salah ketik yang jelas, bukan pilihan gaya
# bahasa. Tujuannya agar hasil koreksi tetap ringkas dan dapat ditindaklanjuti.
COMMON_TYPOS = {
    "akomodsi": "akomodasi",
    "dibandigkan": "dibandingkan",
    "domestk": "domestik",
    "kenaikkan": "kenaikan",
    "mancanegra": "mancanegara",
    "mengalamai": "mengalami",
    "penghuniaan": "penghunian",
    "perjalananan": "perjalanan",
    "persenatse": "persentase",
    "presentase": "persentase",
    "sebsar": "sebesar",
    "statitik": "statistik",
    "statistk": "statistik",
    "terdapt": "terdapat",
}


def _preserve_case(source: str, replacement: str) -> str:
    if source.isupper():
        return replacement.upper()
    if source[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def _fixed_replacement(value: str) -> Callable[[re.Match[str]], str]:
    return lambda match: _preserve_case(match.group(), value)


LANGUAGE_RULES = (
    LanguageRule(
        "duplicate_word", re.compile(r"\b([a-zA-ZÀ-ÿ]{3,})\s+\1\b", re.IGNORECASE),
        "warning", "Kata berulang", "Terdapat kata yang ditulis dua kali berturut-turut.",
        "Hapus salah satu kata yang berulang.", lambda match: match.group(1),
    ),
    LanguageRule(
        "lowercase_month", re.compile(rf"\b(?:{MONTH_NAMES})\b"), "warning",
        "Huruf kapital nama bulan", "Nama bulan harus diawali huruf kapital.",
        "Gunakan huruf kapital pada nama bulan.", lambda match: match.group().title(),
    ),
    LanguageRule(
        "joined_di_preposition",
        re.compile(r"\bdi(?:atas|bawah|dalam|luar|antara|samping|depan|belakang|tengah|sini|sana|mana)\b", re.IGNORECASE),
        "warning", "Penulisan kata depan 'di'", "Kata depan 'di' harus ditulis terpisah.",
        "Pisahkan kata depan 'di' dari kata yang mengikutinya.",
        lambda match: _preserve_case(match.group(), f"di {match.group()[2:]}"),
    ),
    LanguageRule(
        "joined_ke_preposition",
        re.compile(r"\bke(?:atas|bawah|dalam|samping|depan|belakang|tengah|sini|sana|mana)\b", re.IGNORECASE),
        "warning", "Penulisan kata depan 'ke'", "Kata depan 'ke' harus ditulis terpisah.",
        "Pisahkan kata depan 'ke' dari kata yang mengikutinya.",
        lambda match: _preserve_case(match.group(), f"ke {match.group()[2:]}"),
    ),
    LanguageRule(
        "separated_di_prefix",
        re.compile(
            r"\bdi\s+(?:banding(?:kan)?|catat|dominasi|hitung|ikuti|jelaskan|kelompokkan|"
            r"kumpulkan|lakukan|lengkapi|olah|peroleh|publikasikan|rinci|rilis|sajikan|"
            r"sampaikan|sebutkan|temukan|tampilkan|tunjukkan|ukur|gunakan|hasilkan)\b",
            re.IGNORECASE,
        ),
        "warning", "Penulisan awalan 'di-'", "Awalan 'di-' pada kata kerja harus ditulis serangkai.",
        "Gabungkan awalan 'di-' dengan kata kerja yang mengikutinya.",
        lambda match: _preserve_case(match.group(), match.group().replace(" ", "", 1)),
    ),
) + tuple(
    LanguageRule(
        f"typo_{wrong}", re.compile(rf"\b{re.escape(wrong)}\b", re.IGNORECASE),
        "warning", "Typo", f"Kata '{wrong}' terindikasi salah ketik.",
        f"Gunakan penulisan '{correct}'.", _fixed_replacement(correct),
    )
    for wrong, correct in COMMON_TYPOS.items()
) + tuple(
    LanguageRule(
        f"nonstandard_{wrong}", re.compile(rf"\b{re.escape(wrong)}\b", re.IGNORECASE),
        "warning", "Kata tidak baku", f"Kata '{wrong}' tidak baku.",
        f"Gunakan bentuk baku '{correct}'.", _fixed_replacement(correct),
    )
    for wrong, correct in NONSTANDARD_WORDS.items()
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
    if value == value.to_integral_value() and re.match(
        r"\.\s+(?:Kabupaten|Kota|Provinsi|[A-ZÀ-Ý])", after
    ):
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


def _comparison_basis(text: str, start: int, end: int) -> tuple[str | None, str | None]:
    segment_start, segment_end = _segment_bounds(text, start, end)
    search_start = max(0, min(segment_start, start - 450))
    search_end = min(len(text), max(segment_end, end + 120))
    window = text[search_start:search_end]
    number_center = ((start + end) // 2) - search_start
    candidates: list[tuple[int, str]] = []
    for basis, pattern in BASIS_PATTERNS.items():
        for match in pattern.finditer(window):
            match_center = (match.start() + match.end()) // 2
            candidates.append((abs(match_center - number_center), basis))
    if not candidates:
        return None, None
    _, basis = min(candidates, key=lambda item: item[0])
    return basis, BASIS_LABELS[basis]


def _subject(text: str, start: int, end: int) -> tuple[str | None, str | None]:
    segment_start, segment_end = _segment_bounds(text, start, end)
    window_start = max(segment_start, start - 180)
    window_end = min(segment_end, end + 120)
    window = text[window_start:window_end]
    number_center = ((start + end) // 2) - window_start
    candidates: list[tuple[int, int, str, str]] = []

    for key, label, pattern in REGION_ALIASES:
        for match in pattern.finditer(window):
            match_center = (match.start() + match.end()) // 2
            after_penalty = 15 if match.start() >= number_center else 0
            candidates.append((
                abs(match_center - number_center) + after_penalty,
                -len(match.group()), key, label,
            ))

    # Gunakan kamus wilayah terlebih dahulu agar "Provinsi Sulawesi Tengah"
    # dan "Sulteng" menghasilkan kunci identitas yang sama.
    if candidates:
        _, _, key, label = min(candidates, key=lambda item: (item[0], item[1]))
        return key, label

    for match in GEOGRAPHY_PATTERN.finditer(window):
        kind = match.group("kind").rstrip(".").title()
        if kind == "Kab":
            kind = "Kabupaten"
        name_parts: list[str] = []
        for part in match.group("name").split():
            if part.lower() in ENTITY_STOP_WORDS:
                break
            name_parts.append(part)
        if not name_parts:
            continue
        label = f"{kind} {' '.join(name_parts).title()}"
        match_center = (match.start() + match.end()) // 2
        after_penalty = 15 if match.start() >= number_center else 0
        candidates.append((
            abs(match_center - number_center) + after_penalty,
            -len(match.group()), label.lower(), label,
        ))
    if not candidates:
        return None, None
    _, _, key, label = min(candidates, key=lambda item: (item[0], item[1]))
    return key, label


def _qualifiers(text: str, start: int, end: int) -> tuple[tuple[str, str], ...]:
    """Ambil kategori pembeda dari kalimat yang memuat angka."""
    segment_start, segment_end = _segment_bounds(text, start, end)
    window_start = max(segment_start, start - 140)
    window_end = min(segment_end, end + 90)
    context = text[window_start:window_end]
    number_center = ((start + end) // 2) - window_start
    result: list[tuple[str, str]] = []
    for group, variants in QUALIFIER_PATTERNS.items():
        candidates: list[tuple[int, str]] = []
        for key, label, pattern in variants:
            del label
            for match in pattern.finditer(context):
                match_center = (match.start() + match.end()) // 2
                candidates.append((abs(match_center - number_center), key))
        if candidates:
            _, key = min(candidates, key=lambda item: item[0])
            result.append((group, key))
    return tuple(result)


def _value_role(text: str, start: int, end: int) -> str:
    before = text[max(0, start - 75):start].lower()
    nearby = text[max(0, start - 75):min(len(text), end + 45)].lower()
    if re.search(r"\b(?:andil|kontribusi|sumbangan)\b", nearby):
        return "contribution"
    if re.search(r"\b(?:naik|turun|meningkat|menurun|bertambah|berkurang)(?:\s+sebesar)?\s*$", before):
        return "change"
    if re.search(r"\b(?:selisih|perubahan)\b", nearby):
        return "change"
    return "level"


def _values_equivalent(left: NumberMention, right: NumberMention) -> bool:
    left_min = left.range_min if left.range_min is not None else left.value
    left_max = left.range_max if left.range_max is not None else left.value
    right_min = right.range_min if right.range_min is not None else right.value
    right_max = right.range_max if right.range_max is not None else right.value
    return max(left_min, right_min) <= min(left_max, right_max)


def _mentions(document: Document) -> list[NumberMention]:
    result: list[NumberMention] = []
    for content in document.contents:
        ranges = list(RANGE_PATTERN.finditer(content.text_content))
        for ordinal, match in enumerate(NUMBER_PATTERN.finditer(content.text_content)):
            range_match = next(
                (
                    item for item in ranges
                    if item.start() <= match.start() and match.end() <= item.end()
                ),
                None,
            )
            if range_match and match.start() != range_match.start("low"):
                continue
            raw = range_match.group() if range_match else match.group()
            mention_start = range_match.start() if range_match else match.start()
            mention_end = range_match.end() if range_match else match.end()
            range_min = parse_localized_number(range_match.group("low")) if range_match else None
            range_max = parse_localized_number(range_match.group("high")) if range_match else None
            value = range_min if range_match else parse_localized_number(raw)
            if (
                value is None
                or (range_match and (range_max is None or range_min is None))
                or (range_match and _is_year(range_match.group("low"), range_min))
                or (range_match and _is_year(range_match.group("high"), range_max))
                or (not range_match and _is_year(raw, value))
                or _is_metadata_number(content.text_content, mention_start, mention_end, value)
            ):
                continue
            if range_min is not None and range_max is not None and range_min > range_max:
                range_min, range_max = range_max, range_min
            context = _segment(content.text_content, mention_start, mention_end)
            keywords = _keywords(context)
            unit = _unit(content.text_content, mention_start, mention_end)
            period_key, period_label = _period(
                content.text_content, mention_start, mention_end
            )
            basis_key, basis_label = _comparison_basis(
                content.text_content, mention_start, mention_end
            )
            subject_key, subject_label = _subject(
                content.text_content, mention_start, mention_end
            )
            qualifiers = _qualifiers(content.text_content, mention_start, mention_end)
            if not keywords or not _is_statistical_number(context, unit, keywords):
                continue
            result.append(NumberMention(
                key=f"{document.id}:{content.page_number}:{ordinal}", raw=raw, value=value,
                page_number=content.page_number, section_label=content.section_label,
                text=content.text_content, start=mention_start, end=mention_end, context_text=context,
                keywords=keywords, unit=unit, period_key=period_key, period_label=period_label,
                range_min=range_min, range_max=range_max,
                basis_key=basis_key, basis_label=basis_label,
                subject_key=subject_key, subject_label=subject_label,
                qualifiers=qualifiers,
                value_role=_value_role(content.text_content, mention_start, mention_end),
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


def _qualifiers_compatible(left: NumberMention, right: NumberMention) -> bool:
    left_by_group = dict(left.qualifiers)
    right_by_group = dict(right.qualifiers)
    return all(
        group not in right_by_group or right_by_group[group] == value
        for group, value in left_by_group.items()
    )


def _has_period_conflict(mentions: list[NumberMention]) -> bool:
    explicit = [mention for mention in mentions if mention.period_key]
    return any(
        not _periods_compatible(left, right)
        for left, right in combinations(explicit, 2)
    )


def _candidate_score(
    left: NumberMention,
    right: NumberMention,
) -> Decimal | None:
    if not _units_compatible(left, right) or not _qualifiers_compatible(left, right):
        return None
    if left.basis_key and right.basis_key and left.basis_key != right.basis_key:
        return None
    if left.subject_key and right.subject_key and left.subject_key != right.subject_key:
        return None
    if left.value_role != right.value_role:
        return None
    left_words = set(left.keywords)
    right_words = set(right.keywords)
    common = left_words & right_words
    overlap = Decimal(len(common)) / Decimal(max(1, min(len(left_words), len(right_words))))
    strong_identity = bool(common & STRONG_INDICATOR_TERMS)
    descriptive_identity = len(common) >= 2 and overlap >= Decimal("0.30")
    if not strong_identity and not descriptive_identity:
        return None

    periods_compatible = _periods_compatible(left, right)
    # Periode berbeda hanya boleh dipasangkan bila identitas indikator benar-benar
    # kuat. Nilai yang sama menambah keyakinan, tetapi bukan satu-satunya dasar.
    if not periods_compatible and not (
        strong_identity or (len(common) >= 3 and overlap >= Decimal("0.45"))
    ):
        return None
    exact_bonus = Decimal("0.30") if _values_equivalent(left, right) else Decimal("0")
    unit_bonus = Decimal("0.10") if left.unit and left.unit == right.unit else Decimal("0")
    period_bonus = Decimal("0.45") if (
        periods_compatible and left.period_key and right.period_key
    ) else Decimal("0")
    basis_bonus = Decimal("0.40") if left.basis_key and left.basis_key == right.basis_key else Decimal("0")
    subject_bonus = Decimal("0.40") if left.subject_key and left.subject_key == right.subject_key else Decimal("0")
    semantic_bonus = basis_bonus + subject_bonus

    if descriptive_identity:
        return overlap + exact_bonus + unit_bonus + period_bonus + semantic_bonus
    if strong_identity:
        return overlap + Decimal("0.35") + exact_bonus + unit_bonus + period_bonus + semantic_bonus
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
    basis_keys = {mention.basis_key for mention in mentions if mention.basis_key}
    if len(basis_keys) == 1:
        basis = next(iter(basis_keys))
        label = f"{label or 'Indikator'} • {BASIS_LABELS[basis]}"
    subject_keys = {mention.subject_key for mention in mentions if mention.subject_key}
    if len(subject_keys) == 1:
        subject_label = next(
            (mention.subject_label for mention in mentions if mention.subject_label),
            None,
        )
        if subject_label:
            label = f"{label or 'Indikator'} • {subject_label}"
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
            "value_kind": "range" if mention.range_min is not None else "point",
            "period": mention.period_label,
            "basis": mention.basis_label,
            "subject": mention.subject_label,
            "role": mention.value_role,
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
        mentions = [mention for _, mention in mentions_by_type.values()]
        if _has_period_conflict(mentions):
            mention_items = list(mentions_by_type.values())
            consensus: list[tuple[Document, NumberMention]] = []
            outliers: list[tuple[Document, NumberMention]] = []
            if len(mention_items) == 3:
                for candidate in mention_items:
                    others = [item for item in mention_items if item is not candidate]
                    if (
                        _periods_compatible(others[0][1], others[1][1])
                        and all(
                            not _periods_compatible(candidate[1], other[1])
                            for other in others
                        )
                    ):
                        consensus = others
                        outliers = [candidate]
                        break
            unique_outlier = len(consensus) == 2 and len(outliers) == 1
            if unique_outlier:
                reference_mention = consensus[0][1]
                target_document, target_mention = outliers[0]
            else:
                reference_mention = mention_items[0][1]
                target_document, target_mention = mention_items[0]

            values = _comparison_values(mentions_by_type)
            for document_type, value in values.items():
                document, _ = mentions_by_type[document_type]
                value["issue"] = "period"
                if unique_outlier:
                    value["status"] = "different" if document.id == target_document.id else "match"
                else:
                    value["status"] = "needs_verification"
            actual_periods = " | ".join(
                f"{DOCUMENT_LABELS[document.document_type]}: {mention.period_label or 'periode tidak disebutkan'}"
                for document, mention in mention_items
            )
            evidence = " || ".join(
                f"{DOCUMENT_LABELS[document.document_type]} ({mention.section_label}): {_context(mention)}"
                for document, mention in mention_items
            )
            comparison_findings.append(Finding(
                check_type="cross_document", severity="error",
                document_id=target_document.id if unique_outlier else None,
                field_name=_common_label(mentions),
                expected_value=reference_mention.period_label if unique_outlier else None,
                actual_value=actual_periods,
                message=(
                    f"Periode indikator pada {DOCUMENT_LABELS[target_document.document_type]} "
                    "berbeda dari dua dokumen lainnya."
                    if unique_outlier
                    else f"Indikator dengan makna yang sama menggunakan periode berbeda pada "
                    f"{len(mentions_by_type)} dokumen."
                ),
                suggestion=(
                    f"Periksa bulan/tahun pada {DOCUMENT_LABELS[target_document.document_type]} "
                    "dan samakan dengan periode sumber yang benar."
                    if unique_outlier
                    else "Verifikasi bulan/tahun data pada sumber resmi, lalu samakan periode antar dokumen."
                ),
                page_number=target_mention.page_number if unique_outlier else None,
                context_text=evidence,
                comparison_values=values,
            ))
            # Angka lintas periode tidak dinilai sebagai selisih nilai karena
            # keduanya belum terbukti merujuk ke periode data yang sama.
            continue
        if all(_values_equivalent(left, right) for left, right in combinations(mentions, 2)):
            comparison_passed += 1
            continue

        mention_items = list(mentions_by_type.values())
        consensus: list[tuple[Document, NumberMention]] = []
        outliers: list[tuple[Document, NumberMention]] = []
        if len(mention_items) == 3:
            for left_item, right_item in combinations(mention_items, 2):
                other_item = next(
                    item for item in mention_items
                    if item is not left_item and item is not right_item
                )
                if (
                    _values_equivalent(left_item[1], right_item[1])
                    and not _values_equivalent(left_item[1], other_item[1])
                    and not _values_equivalent(right_item[1], other_item[1])
                ):
                    consensus = [left_item, right_item]
                    outliers = [other_item]
                    break
        unique_outlier = len(consensus) == 2 and len(outliers) == 1
        reference_mention = consensus[0][1] if unique_outlier else mention_items[0][1]
        if not unique_outlier:
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
        values = _comparison_values(mentions_by_type)
        for document_type, value in values.items():
            document, mention = mentions_by_type[document_type]
            if unique_outlier:
                value["status"] = "different" if document.id == target_document.id else "match"
            else:
                value["status"] = "needs_verification"
        actual = " | ".join(
            f"{DOCUMENT_LABELS[document.document_type]}: {mention.raw}"
            for document, mention in (outliers if unique_outlier else mentions_by_type.values())
        )
        evidence = " || ".join(
            f"{DOCUMENT_LABELS[document.document_type]} ({mention.section_label}): {_context(mention)}"
            for document, mention in mentions_by_type.values()
        )
        comparison_findings.append(Finding(
            check_type="cross_document", severity="error",
            document_id=target_document.id if unique_outlier else None,
            field_name=_common_label(mentions),
            expected_value=reference_mention.raw if unique_outlier else None,
            actual_value=actual,
            message=(
                f"Nilai pada {DOCUMENT_LABELS[target_document.document_type]} berbeda dari "
                f"dua dokumen lainnya."
                if unique_outlier
                else f"Nilai indikator dan periode yang sama berbeda pada {len(mentions_by_type)} "
                "dokumen; dokumen yang benar belum dapat ditentukan."
            ),
            suggestion=(
                f"Periksa nilai pada {DOCUMENT_LABELS[target_document.document_type]} lalu samakan "
                "dengan sumber yang telah terkonfirmasi."
                if unique_outlier
                else "Verifikasi sumber resmi untuk menentukan nilai yang benar sebelum menyamakan dokumen."
            ),
            page_number=target_mention.page_number if unique_outlier else None,
            context_text=evidence,
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
        for content in document.contents:
            for rule in LANGUAGE_RULES:
                matches = list(rule.pattern.finditer(content.text_content))[:MAX_LANGUAGE_FINDINGS_PER_RULE]
                total += max(1, len(matches))
                if not matches:
                    passed += 1
                    continue
                for match in matches:
                    replacement = (
                        rule.replacement(match)
                        if callable(rule.replacement)
                        else rule.replacement
                    )
                    findings.append(Finding(
                        check_type="language", severity=rule.severity, document_id=document.id,
                        field_name=rule.title, expected_value=replacement,
                        actual_value=match.group(), message=rule.message,
                        suggestion=rule.suggestion, page_number=content.page_number,
                        context_text=_segment(content.text_content, match.start(), match.end()),
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
        # Nama kolom dipertahankan agar database lama tetap kompatibel.
        # Mulai rules-v2.4-semantic-eyd nilainya adalah skor kelengkapan file.
        data_consistency_score=_score(coverage_total, coverage_findings),
        cross_document_score=_score(comparison_total, comparison_findings),
        language_score=_score(language_total, language_findings),
        overall_score=_score(total, findings),
    )
