"""Structured compositional Vietnamese geometry clause analysis with exact source-span provenance (AXO HYBRID /12 P3).

Pipeline stage:
  Original Input
    -> Source-preserving Normalization (with exact char_orig_start / char_orig_end maps)
    -> Controlled 1-1 Diacritic Projection (guarded against out-of-domain decoys & ambiguous words)
    -> Clause Segmentation & Compositional Nested-Declaration / Trailing-Goal Splitting
    -> 8 Clause Role Classifications (preserving negation & conditional scoping)
    -> Intent / Entity Binding & 11-field SourceSpanProvenanceRecord construction
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
import unicodedata
from typing import Any

COMPOSITIONAL_CLAUSE_ANALYZER_VERSION = "compositional-clause-analyzer/1"

# Canonical 8 clause roles (§8)
ROLE_OBJECT_DECLARATION = "OBJECT_DECLARATION"
ROLE_GEOMETRIC_CONSTRAINT = "GEOMETRIC_CONSTRAINT"
ROLE_SIMULATION_REQUEST = "SIMULATION_REQUEST"
ROLE_MEASUREMENT_REQUEST = "MEASUREMENT_REQUEST"
ROLE_VISUALIZATION_REQUEST = "VISUALIZATION_REQUEST"
ROLE_CONDITIONAL_PREMISE = "CONDITIONAL_PREMISE"
ROLE_NEGATED_REQUEST = "NEGATED_REQUEST"
ROLE_CONTEXT_HEADER = "CONTEXT_HEADER"

_PT = r"[A-Z][0-9]*'?"
_PTS2 = rf"{_PT}{_PT}"
_PTS3_6 = rf"(?:{_PT}){{3,6}}"

# Simulation lead-in verbs that can embed object declarations ("Vẽ hình chóp ... có ...")
SIMULATION_LEAD_VERB_RE = re.compile(
    r"^\s*(?:(?:(?:em|mình|tớ|bạn)\s+)?(?:muốn\s+xem|cần\s+xem|(?:hãy\s+)?(?:chỉ\s+cần\s+)?(?:vẽ|dựng|mô\s+phỏng|minh\s+ho[ạa]|biểu\s+diễn|hiển\s+thị|cho\s+(?:mình|em|tôi|tớ)\s+xem))(?:\s+giúp(?:\s+(?:mình|em|tôi|tớ))?|\s+lại)?)\s+",
    re.IGNORECASE | re.UNICODE,
)

# Standalone trailing simulation clause ("... Hãy mô phỏng hình chóp đó.")
STANDALONE_SIM_CLAUSE_RE = re.compile(
    r"^\s*(?:(?:em|mình|tớ|bạn)\s+)?(?:(?:muốn|cần)\s+xem|(?:hãy\s+)?(?:chỉ\s+cần\s+)?(?:vẽ|dựng|mô\s+phỏng|minh\s+ho[ạa]|biểu\s+diễn|hiển\s+thị|cho\s+(?:mình|em|tôi|tớ)\s+xem))\b",
    re.IGNORECASE | re.UNICODE,
)

# Solid head noun phrases allowed right after a simulation lead-in verb when declaring the solid inline
_EMBEDDED_SOLID_HEAD_RE = re.compile(
    rf"^(?:(?:(?:3D|hình\s+3D)\s+(?:của\s+)?)?(?:hình|khối)\s+)?"
    rf"(?P<head>(?:chóp(?:\s+(?:đều|tam\s+giác(?:\s+đều)?|tứ\s+giác(?:\s+đều)?))?|"
    rf"lăng\s+trụ(?:\s+(?:đứng|đều|xiên|tam\s+giác(?:\s+đều)?|tứ\s+giác(?:\s+đều)?))?|"
    rf"hộp(?:\s+chữ\s+nhật)?|lập\s+phương|tứ\s+diện(?:\s+đều)?)"
    rf"(?:\s+(?P<lbl>(?:{_PT})+(?:\.(?:{_PT})+)?))?(?![\w'])(?:\s+(?:đều|đứng))?)"
    rf"(?:\s+(?:có|với|biết(?:\s+rằng)?|sao\s+cho|trong\s+đó|cạnh|mà|về|,|:|\n|$)|\s*$)",
    re.IGNORECASE | re.UNICODE,
)

# Trailing goal split inside a sentence: ", rồi tính ...", " và tính ...", "; tìm ...", " sau đó xác định ..."
_TRAILING_GOAL_SPLIT_RE = re.compile(
    r"(?:,\s*(?:rồi|sau\s+đó|đồng\s+thời|và)?\s*|\s+(?:rồi|và|sau\s+đó|đồng\s+thời|để)\s+|;\s*)"
    r"(?=(?:hãy\s+)?(?:tính|tìm|xác\s+định)\s+(?:thể\s+tích|diện\s+tích|khoảng\s+cách|k/c|độ\s+dài|góc|chiều\s+cao|đường\s+cao|bán\s+kính|tỉ\s+số|tỷ\s+số)\b)",
    re.IGNORECASE | re.UNICODE,
)

# Meta "no calculation needed" phrases (must NOT be turned into contra / missing goal or negated command)
META_NO_CALC_RE = re.compile(
    r"^\s*(?:(?:chỉ\s+cần\s+vẽ\s+hình\s*,?\s*)?(?:và\s+)?(?:không|chưa)\s+cần\s+"
    r"(?:tính(?:\s+toán|\s+gì(?:\s+thêm)?)?|làm\s+gì\s+thêm)"
    r"|chỉ\s+(?:vẽ|dựng)(?:\s+hình)?\s*,\s*không\s+tính(?:\s+toán)?"
    r"|(?:(?:em|mình|tôi)\s+)?chỉ\s+cần\s+hình\s+vẽ\s+thôi)\s*[:,.;!]*\s*$",
    re.IGNORECASE | re.UNICODE,
)
INLINE_LEADING_META_RE = re.compile(
    r"^\s*(?:(?:chỉ\s+cần\s+(?:vẽ|dựng|mô\s+phỏng)\s+hình\s*,?\s*)?(?:và\s+)?(?:không|chưa)\s+cần\s+tính(?:\s+toán|\s+gì(?:\s+thêm)?)?\s*(?:[:,;]\s*|,\s*(?=(?:hãy\s+)?(?:vẽ|dựng|mô\s+phỏng|biểu\s+diễn|hiển\s+thị)\b)))",
    re.IGNORECASE | re.UNICODE,
)
INLINE_TRAILING_META_RE = re.compile(
    r"(?:\s*(?:,|;|\.|và)?\s*(?:không|chưa)\s+cần\s+tính(?:\s+toán|\s+gì(?:\s+thêm)?)?\s*[.!]*)\s*$",
    re.IGNORECASE | re.UNICODE,
)

CONTEXT_HEADER_RE = re.compile(
    r"^\s*(?:(?:Câu|Bài)\s+\d+(?:\s*\(\s*\d+(?:[.,]\d+)?\s*điểm\s*\))?\s*[.:;]*|\(\s*\d+(?:[.,]\d+)?\s*điểm\s*\)\s*[.:;]*)\s*$",
    re.IGNORECASE | re.UNICODE,
)
INLINE_EXAM_HEADER_PREFIX_RE = re.compile(
    r"^\s*(?:(?:Câu|Bài)\s+\d+(?:\s*\(\s*(?:\d+(?:[.,]\d+)?\s*điểm|VD|VDC|TH|NB)\s*\))?\s*[.:;]+\s*)",
    re.IGNORECASE | re.UNICODE,
)

# Negation & Conditional detectors
NEGATED_COMMAND_RE = re.compile(
    r"^\s*(?:không(?:\s+(?:được|nên|cần|vẽ|dựng|mô\s+phỏng|biểu\s+diễn|hiển\s+thị))?|đừng|chớ)\s+"
    r"(?:vẽ|dựng|mô\s+phỏng|minh\s+ho[ạa]|biểu\s+diễn|hiển\s+thị|tính|tạo)\b",
    re.IGNORECASE | re.UNICODE,
)
NEGATED_PREMISE_RE = re.compile(
    r"(?:\bkhông\s+(?:vuông\s+góc|song\s+song|cắt|đồng\s+phẳng|thẳng\s+hàng|trùng|chứa|nằm\s+trong|cân|đều|phải)\b"
    r"|\bkhông\s+có\s+(?:[A-Z][0-9']*){2,}\s*(?:vuông\s+góc|song\s+song|=|⊥|∥))",
    re.IGNORECASE | re.UNICODE,
)
# Careful: "muốn xem" is NOT a conditional; only genuine conditional markers are flagged.
CONDITIONAL_MARKER_RE = re.compile(
    r"(?:^\s*(?:nếu|giả\s+sử|khi\s+nào)\b|\bnếu\b.+\bthì\b|\bgiả\s+sử\b)",
    re.IGNORECASE | re.UNICODE,
)

MEASUREMENT_VERB_RE = re.compile(
    r"\b(?:tính|tìm|xác\s+định|hỏi|bao\s+nhiêu|mấy|cho\s+biết)\b|\?",
    re.IGNORECASE | re.UNICODE,
)

# Ambiguous "biểu diễn khoảng cách / góc ..." without a calculation verb (§15, A3)
VISUALIZATION_METRIC_NOUN_RE = re.compile(
    r"\b(?:biểu\s+diễn|vẽ|hiển\s+thị|minh\s+ho[ạa])\s+"
    r"(?P<target>khoảng\s+cách|góc\s+(?:giữa|tạo\s+bởi|hợp\s+bởi))\b",
    re.IGNORECASE | re.UNICODE,
)
NAMED_VISUALIZATION_OBJ_RE = re.compile(
    rf"\b(?:biểu\s+diễn|hiển\s+thị)\s+(?:thêm\s+)?"
    rf"(?:đường\s+cao\s+{_PTS2}|đoạn(?:\s+thẳng)?\s+{_PTS2}|điểm\s+{_PT}|mặt\s+phẳng\s+\([^)]+\))\b",
    re.IGNORECASE | re.UNICODE,
)


@dataclass(frozen=True)
class SpanMappedText:
    """Normalized text paired with exact per-character index mapping back into `original_text`."""

    original_text: str
    normalized_text: str
    char_orig_start: tuple[int, ...]
    char_orig_end: tuple[int, ...]
    diacritic_projected: bool = False
    ambiguous_diacritic_blocked: bool = False

    def orig_span(self, norm_start: int, norm_end: int) -> tuple[int, int]:
        """Map `[norm_start, norm_end)` in `normalized_text` to exact `[orig_start, orig_end)` in `original_text`."""
        n = len(self.normalized_text)
        if n == 0 or norm_start >= norm_end:
            return (0, 0)
        a = max(0, min(norm_start, n - 1))
        b = max(a + 1, min(norm_end, n))
        return (self.char_orig_start[a], self.char_orig_end[b - 1])

    def orig_quote(self, norm_start: int, norm_end: int) -> str:
        """Slice an exact verbatim substring from `original_text` (never synthesizes quotes)."""
        oa, ob = self.orig_span(norm_start, norm_end)
        while oa < ob and self.original_text[oa] in " \t\r\n,.;:?!":
            oa += 1
        while ob > oa and self.original_text[ob - 1] in " \t\r\n,.;:?!":
            ob -= 1
        return self.original_text[oa:ob]


@dataclass(frozen=True)
class CompositionalClause:
    """Single segmented clause with role, subkind, original/normalized spans, and provenance metadata."""

    clause_id: int
    role: str
    subkind: str
    norm_text: str
    norm_start: int
    norm_end: int
    orig_text: str
    orig_start: int
    orig_end: int
    parent_sentence_id: int
    embedded_simulation_lead: str | None = None
    ambiguity_reason: str | None = None
    entity_hints: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompositionalAnalysisResult:
    """Full structured clause analysis of an input problem with intent composition."""

    analyzer_version: str
    mapped: SpanMappedText
    clauses: tuple[CompositionalClause, ...]
    has_simulation_request: bool
    has_measurement_request: bool
    has_negated_command: bool
    has_negated_premise: bool
    has_conditional_premise: bool
    has_meta_no_calc: bool
    ambiguous_visualization_clauses: tuple[CompositionalClause, ...]
    is_simulation_only_intent: bool
    is_mixed_simulation_and_query: bool
    entity_bindings: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SourceSpanProvenanceRecord:
    """11-field traceability record required by §10."""

    original_text: str
    original_offsets: tuple[int, int]
    normalized_text: str
    normalized_offsets: tuple[int, int]
    clause_boundaries: tuple[int, int]
    clause_role: str
    quoted_source_span: str
    entity_binding: dict[str, Any]
    extracted_fact: dict[str, Any]
    grounding_verdict: str
    subkind: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "original_text": self.original_text,
            "original_offsets": list(self.original_offsets),
            "normalized_text": self.normalized_text,
            "normalized_offsets": list(self.normalized_offsets),
            "clause_boundaries": list(self.clause_boundaries),
            "clause_role": self.clause_role,
            "quoted_source_span": self.quoted_source_span,
            "entity_binding": self.entity_binding,
            "extracted_fact": self.extracted_fact,
            "grounding_verdict": self.grounding_verdict,
            "subkind": self.subkind,
        }


# ── Span-preserving Normalization & Controlled 1-1 Diacritic Projection ─────────────────────────────────────────────

_NON_GEOMETRY_ASCII_DECOY_RE = re.compile(
    r"\b(?:mang\s+hinh|con\s+lac|lo\s+xo|do\s+thi|cay\s+khung|thuat\s+toan|kruskal|dijkstra|"
    r"phuong\s+trinh|dao\s+dong|bien\s+do|toc\s+do|van\s+toc|gia\s+toc|luong\s+giac|ham\s+so|"
    r"tich\s+phan|dao\s+ham|duong\s+tron\s+pha|chu\s+vi\s+hinh\s+tron|code|python|sql|html)\b",
    re.IGNORECASE,
)

# Context-safe 1-1 ASCII -> Vietnamese accented geometry lexicon (lowercase words only; uppercase labels untouched!)
_DIACRITIC_PHRASE_MAP: tuple[tuple[str, str], ...] = (
    ("hinh chop", "hình chóp"),
    ("khoi chop", "khối chóp"),
    ("chop deu", "chóp đều"),
    ("tu giac deu", "tứ giác đều"),
    ("tam giac deu", "tam giác đều"),
    ("tam giac vuong can", "tam giác vuông cân"),
    ("tam giac vuong", "tam giác vuông"),
    ("tam giac can", "tam giác cân"),
    ("tam giac", "tam giác"),
    ("lang tru dung", "lăng trụ đứng"),
    ("lang tru deu", "lăng trụ đều"),
    ("lang tru", "lăng trụ"),
    ("hinh lap phuong", "hình lập phương"),
    ("khoi lap phuong", "khối lập phương"),
    ("lap phuong", "lập phương"),
    ("hinh hop chu nhat", "hình hộp chữ nhật"),
    ("khoi hop chu nhat", "khối hộp chữ nhật"),
    ("hop chu nhat", "hộp chữ nhật"),
    ("tu dien deu", "tứ diện đều"),
    ("tu dien", "tứ diện"),
    ("hinh vuong", "hình vuông"),
    ("hinh chu nhat", "hình chữ nhật"),
    ("hinh thoi", "hình thoi"),
    ("hinh binh hanh", "hình bình hành"),
    ("vuong goc", "vuông góc"),
    ("song song", "song song"),
    ("doi mot", "đôi một"),
    ("mat phang day", "mặt phẳng đáy"),
    ("mat day", "mặt đáy"),
    ("hai mat phang", "hai mặt phẳng"),
    ("mat phang", "mặt phẳng"),
    ("hai mat ben", "hai mặt bên"),
    ("mat ben", "mặt bên"),
    ("cung vuong goc", "cùng vuông góc"),
    ("duong thang", "đường thẳng"),
    ("duong cheo", "đường chéo"),
    ("duong cao", "đường cao"),
    ("chiều cao", "chiều cao"),
    ("chieu cao", "chiều cao"),
    ("canh ben", "cạnh bên"),
    ("canh day", "cạnh đáy"),
    ("tat ca cac canh", "tất cả các cạnh"),
    ("deu bang", "đều bằng"),
    ("trung diem", "trung điểm"),
    ("trong tam", "trọng tâm"),
    ("hinh chieu", "hình chiếu"),
    ("giao diem", "giao điểm"),
    ("mo phong", "mô phỏng"),
    ("bieu dien", "biểu diễn"),
    ("hien thi", "hiển thị"),
    ("khong can tinh", "không cần tính"),
    ("khong vuong goc", "không vuông góc"),
    ("khong song song", "không song song"),
    ("khong ve", "không vẽ"),
    ("khong mo phong", "không mô phỏng"),
    ("tinh the tich", "tính thể tích"),
    ("the tich", "thể tích"),
    ("tinh dien tich", "tính diện tích"),
    ("dien tich", "diện tích"),
    ("tinh khoang cach", "tính khoảng cách"),
    ("khoang cach", "khoảng cách"),
    ("tinh do dai", "tính độ dài"),
    ("do dai", "độ dài"),
    ("tinh goc", "tính góc"),
    ("giua", "giữa"),
    ("khoi chop", "khối chóp"),
    ("khoi lang tru", "khối lăng trụ"),
    ("khoi lap phuong", "khối lập phương"),
    ("khoi tu dien", "khối tứ diện"),
    ("khoi hop", "khối hộp"),
    ("da cho", "đã cho"),
    ("hinh nay", "hình này"),
    ("hinh do", "hình đó"),
    ("giup em", "giúp em"),
)

_DIACRITIC_TOKEN_MAP: dict[str, str] = {
    "cho": "cho",
    "hinh": "hình",
    "khoi": "khối",
    "chop": "chóp",
    "day": "đáy",
    "co": "có",
    "la": "là",
    "canh": "cạnh",
    "goc": "góc",
    "voi": "với",
    "biet": "biết",
    "rang": "rằng",
    "tai": "tại",
    "va": "và",
    "roi": "rồi",
    "de": "để",
    "hay": "hãy",
    "ve": "vẽ",
    "dung": "dựng",  # overridden to "đứng" right after "lang tru" via phrase map above!
    "tinh": "tính",
    "tim": "tìm",
    "den": "đến",
    "toi": "tới",
    "bang": "bằng",
    "goi": "gọi",
    "cua": "của",
    "doan": "đoạn",
    "diem": "điểm",
    "nam": "nằm",
    "tren": "trên",
    "trong": "trong",
    "cung": "cùng",
    "neu": "nếu",
    "thi": "thì",
    "khong": "không",
    "gi": "gì",
    "them": "thêm",
    "xem": "xem",
    "em": "em",
    "nay": "này",
    "cau": "câu",
    "bai": "bài",
}


def _has_vietnamese_diacritics(text: str) -> bool:
    for ch in unicodedata.normalize("NFC", text):
        if ord(ch) > 127 and ch.isalpha():
            return True
    return False


def _looks_like_diacritic_free_geometry(text: str) -> tuple[bool, bool]:
    """Return `(should_project, decoy_blocked)` conservatively."""
    if not text or _has_vietnamese_diacritics(text):
        return (False, False)
    low = " " + re.sub(r"\s+", " ", text.lower()) + " "
    if _NON_GEOMETRY_ASCII_DECOY_RE.search(low):
        return (False, True)
    solid_cues = (
        "hinh chop", "khoi chop", "tu dien", "lang tru", "lap phuong",
        "hop chu nhat", "tu giac", "tam giac", "hinh vuong", "hinh chu nhat",
    )
    rel_cues = ("vuong goc", "song song", "doi mot", "trung diem", "trong tam", "canh day", "mat day", "the tich", "khoang cach")
    has_tuple = bool(re.search(r"(?<![A-Z])[A-Z][0-9']*(?:\.[A-Z][0-9']*|[A-Z]{2,4})(?![a-z])", text))
    has_solid = any(re.search(rf"(?<!\w){re.escape(c)}(?!\w)", low) for c in solid_cues)
    has_rel = any(re.search(rf"(?<!\w){re.escape(c)}(?!\w)", low) for c in rel_cues)
    if (has_solid and (has_tuple or has_rel)) or (has_rel and has_tuple):
        return (True, False)
    return (False, False)


def _apply_span_preserving_char_norm(raw_text: str) -> SpanMappedText:
    """Normalize `\r\n`, NFC Unicode, primes, degrees, and whitespace while keeping 100% exact `[orig_a, orig_b)` spans."""
    out_chars: list[str] = []
    starts: list[int] = []
    ends: list[int] = []
    raw_len = len(raw_text)
    i = 0
    while i < raw_len:
        ch = raw_text[i]
        # Collapse CRLF to '\n' with full original span [i, i+2)
        if ch == "\r" and i + 1 < raw_len and raw_text[i + 1] == "\n":
            out_chars.append("\n")
            starts.append(i)
            ends.append(i + 2)
            i += 2
            continue
        if ch == "\r":
            out_chars.append("\n")
            starts.append(i)
            ends.append(i + 1)
            i += 1
            continue
        # Combine base char + combining diacritic marks cleanly if input was NFD
        j = i + 1
        while j < raw_len and unicodedata.category(raw_text[j]) == "Mn":
            j += 1
        chunk = raw_text[i:j]
        nfc = unicodedata.normalize("NFC", chunk).replace("\u2032", "'")
        if ch == "º" and out_chars and out_chars[-1].isdigit():
            nfc = "°"
        # Collapse runs of spaces/tabs (preserving newlines!)
        if ch in " \t\u00a0":
            k = j
            while k < raw_len and raw_text[k] in " \t\u00a0":
                k += 1
            out_chars.append(" ")
            starts.append(i)
            ends.append(k)
            i = k
            continue
        for c in nfc:
            out_chars.append(c)
            starts.append(i)
            ends.append(j)
        i = j

    norm_str = "".join(out_chars).strip()
    # Trim matching edge slots so leading/trailing strip stays span-accurate
    ltrim = 0
    while ltrim < len(out_chars) and out_chars[ltrim] in " \n":
        ltrim += 1
    rtrim = len(out_chars)
    while rtrim > ltrim and out_chars[rtrim - 1] in " \n":
        rtrim -= 1
    norm_str = "".join(out_chars[ltrim:rtrim])
    starts = starts[ltrim:rtrim]
    ends = ends[ltrim:rtrim]

    # Normalize Unicode deltas: ΔABC / ∆ABC -> tam giác ABC (updating span arrays atomically)
    def replace_range(s_list: list[str], st_list: list[int], en_list: list[int], a: int, b: int, rep: str) -> None:
        if a >= b:
            return
        oa, ob = st_list[a], en_list[b - 1]
        s_list[a:b] = list(rep)
        st_list[a:b] = [oa] * len(rep)
        en_list[a:b] = [ob] * len(rep)

    cur_chars = list(norm_str)
    cur_starts = list(starts)
    cur_ends = list(ends)
    for m in reversed(list(re.finditer(r"[Δ∆△]\s*(?=[A-Z]{3}\b)", "".join(cur_chars)))):
        replace_range(cur_chars, cur_starts, cur_ends, m.start(), m.end(), "tam giác ")

    norm_final = "".join(cur_chars)
    return SpanMappedText(
        original_text=raw_text,
        normalized_text=norm_final,
        char_orig_start=tuple(cur_starts),
        char_orig_end=tuple(cur_ends),
    )


def _project_diacritic_free(mapped: SpanMappedText) -> SpanMappedText:
    """Project unambiguous lowercase ASCII geometry tokens -> accented Vietnamese while keeping exact orig offsets."""
    should_proj, decoy_blocked = _looks_like_diacritic_free_geometry(mapped.normalized_text)
    if not should_proj:
        if decoy_blocked and not mapped.ambiguous_diacritic_blocked:
            return SpanMappedText(
                original_text=mapped.original_text,
                normalized_text=mapped.normalized_text,
                char_orig_start=mapped.char_orig_start,
                char_orig_end=mapped.char_orig_end,
                diacritic_projected=False,
                ambiguous_diacritic_blocked=True,
            )
        return mapped

    chars = list(mapped.normalized_text)
    starts = list(mapped.char_orig_start)
    ends = list(mapped.char_orig_end)

    def apply_case(src: str, target: str) -> str:
        if not src:
            return target
        if src.isupper() and len(src) > 1:
            return src  # never touch uppercase geometry identifiers!
        if src[0].isupper():
            return target[0].upper() + target[1:]
        return target

    # 1. Apply longer unambiguous multi-word geometry phrases first (right-to-left)
    text_now = "".join(chars)
    low_now = text_now.lower()
    claimed = [False] * len(chars)
    replacements: list[tuple[int, int, str]] = []
    for ascii_p, vi_p in _DIACRITIC_PHRASE_MAP:
        pat = re.compile(rf"(?<![a-zA-Z0-9']){re.escape(ascii_p)}(?![a-zA-Z0-9'])")
        for m in pat.finditer(low_now):
            a, b = m.start(), m.end()
            if any(claimed[k] for k in range(a, b)):
                continue
            orig_seg = text_now[a:b]
            # If the whole match has any standalone all-caps label (unlikely here since pattern is lowercase words), skip
            rep = vi_p
            if orig_seg and orig_seg[0].isupper():
                rep = vi_p[0].upper() + vi_p[1:]
            replacements.append((a, b, rep))
            for k in range(a, b):
                claimed[k] = True

    for a, b, rep in sorted(replacements, key=lambda x: x[0], reverse=True):
        oa, ob = starts[a], ends[b - 1]
        chars[a:b] = list(rep)
        starts[a:b] = [oa] * len(rep)
        ends[a:b] = [ob] * len(rep)
        claimed[a:b] = [True] * len(rep)

    # 2. Disambiguate remaining single lowercase tokens (`tu` -> `từ` vs `tứ`; single-word tokens)
    text_now = "".join(chars)
    token_reps: list[tuple[int, int, str]] = []
    for m in re.finditer(r"\b([a-zA-Z]+)\b", text_now):
        tok = m.group(1)
        if tok.isupper():
            continue  # geometry vertex/segment/letter variable (`S`, `A`, `AB`, `O`, ...)
        if len(tok) == 1 and tok.lower() in ("a", "b", "c", "h", "k", "r", "x"):
            continue
        a, b = m.start(1), m.end(1)
        if any(claimed[k] for k in range(a, b)):
            continue
        low_tok = tok.lower()
        if low_tok == "tu":
            # "tu A den ..." or "tu diem ..." -> "từ"
            after = text_now[b : b + 35]
            if re.match(r"^\s+(?:[A-Z][0-9']*|\([^)]+\)|diem|điểm|duong|đường)\b", after):
                vi_tok = "từ"
            else:
                vi_tok = "từ" if re.search(r"\b(?:den|đến|toi|tới)\b", after, re.IGNORECASE) else "tứ"
        elif low_tok in _DIACRITIC_TOKEN_MAP:
            vi_tok = _DIACRITIC_TOKEN_MAP[low_tok]
        else:
            continue
        rep = apply_case(tok, vi_tok)
        if rep != tok:
            token_reps.append((a, b, rep))

    for a, b, rep in sorted(token_reps, key=lambda x: x[0], reverse=True):
        oa, ob = starts[a], ends[b - 1]
        chars[a:b] = list(rep)
        starts[a:b] = [oa] * len(rep)
        ends[a:b] = [ob] * len(rep)

    return SpanMappedText(
        original_text=mapped.original_text,
        normalized_text="".join(chars),
        char_orig_start=tuple(starts),
        char_orig_end=tuple(ends),
        diacritic_projected=True,
        ambiguous_diacritic_blocked=False,
    )


def normalize_with_spans(problem_text: str, *, project_diacritic_free: bool = True) -> SpanMappedText:
    """Normalize `problem_text` with full character-level origin mapping (never alters original quotes)."""
    mapped = _apply_span_preserving_char_norm(problem_text or "")
    if project_diacritic_free:
        mapped = _project_diacritic_free(mapped)
    return mapped


# ── Sentence & Compositional Clause Segmentation ────────────────────────────────────────────────────────────────────

def _split_top_sentences(text: str) -> list[tuple[int, int]]:
    """Split `text` into sentence boundaries (`.`, `;`, `?`, `!`, `\n`), protecting `S.ABCD`, decimals, and `;` lists."""
    bounds = [0]
    n = len(text)
    depth = 0
    for i, ch in enumerate(text):
        if ch in "([{":
            depth += 1
        elif ch in ")]}" and depth > 0:
            depth -= 1
        if depth > 0 and ch != "\n":
            continue
        if ch in "?!\n":
            bounds.append(i + 1)
        elif ch == ";":
            if re.search(r"(?<![a-zà-ỹ])(?:[A-Z][0-9']*)+$", text[:i].rstrip()) and re.match(
                r"^\s*(?:[A-Z][0-9']*)+(?:\s*(?:[,;.]|\b(?i:và|lần\s+lượt)\b)|\s*$)",
                text[i + 1 :],
            ):
                continue
            bounds.append(i + 1)
        elif ch == ".":
            prev_ch = text[i - 1] if i > 0 else ""
            next_ch = text[i + 1] if i + 1 < n else ""
            if (prev_ch.isupper() or prev_ch in "0123456789'") and next_ch.isupper():
                continue
            if prev_ch.isdigit() and next_ch.isdigit():
                continue
            bounds.append(i + 1)
    bounds.append(n)
    bounds = sorted(set(bounds))
    out: list[tuple[int, int]] = []
    for a, b in zip(bounds, bounds[1:]):
        while a < b and text[a].isspace():
            a += 1
        while b > a and (text[b - 1].isspace() or text[b - 1] in ".;?!"):
            b -= 1
        if a < b:
            out.append((a, b))
    return out


def _trim_span(text: str, a: int, b: int) -> tuple[int, int]:
    while a < b and text[a] in " \t\n,.;:?!":
        a += 1
    while b > a and text[b - 1] in " \t\n,.;:?!":
        b -= 1
    return a, b


def _classify_atomic_clause(seg_text: str) -> tuple[str, str, str | None]:
    """Classify a single atomic (non-nested) clause into one of the 8 compositional roles."""
    s = seg_text.strip()
    if CONTEXT_HEADER_RE.fullmatch(s):
        return (ROLE_CONTEXT_HEADER, "exam_header", None)
    if META_NO_CALC_RE.fullmatch(s):
        return (ROLE_NEGATED_REQUEST, "meta_no_calc", None)
    if NEGATED_COMMAND_RE.search(s):
        return (ROLE_NEGATED_REQUEST, "negated_command", None)
    if NEGATED_PREMISE_RE.search(s):
        return (ROLE_NEGATED_REQUEST, "negated_premise", None)
    if CONDITIONAL_MARKER_RE.search(s):
        return (ROLE_CONDITIONAL_PREMISE, "conditional", None)

    m_ambig = VISUALIZATION_METRIC_NOUN_RE.search(s)
    if m_ambig and not MEASUREMENT_VERB_RE.search(s):
        return (ROLE_VISUALIZATION_REQUEST, "ambiguous_metric_visualization", "AMBIGUOUS_DISTANCE_OR_ANGLE_VISUALIZATION")

    if MEASUREMENT_VERB_RE.search(s):
        return (ROLE_MEASUREMENT_REQUEST, "measurement", None)

    if NAMED_VISUALIZATION_OBJ_RE.search(s) and not SIMULATION_LEAD_VERB_RE.match(s + " "):
        return (ROLE_VISUALIZATION_REQUEST, "named_object_visualization", None)

    if STANDALONE_SIM_CLAUSE_RE.match(s):
        return (ROLE_SIMULATION_REQUEST, "standalone_simulation", None)

    if re.search(r"\b(?:cho|gọi|biết|hình|khối|lăng\s+trụ|tứ\s+diện|lập\s+phương|hộp)\b", s, re.IGNORECASE):
        if re.search(r"[=⊥∥]|\b(?:vuông|song\s+song|trung\s+điểm|trọng\s+tâm|đều|cân|cạnh|góc|chiều\s+cao|độ\s+dài)\b", s, re.IGNORECASE):
            return (ROLE_OBJECT_DECLARATION, "declaration_with_constraints", None)
        return (ROLE_OBJECT_DECLARATION, "declaration", None)

    return (ROLE_GEOMETRIC_CONSTRAINT, "constraint", None)


def analyze_compositional_geometry(problem_text: str) -> CompositionalAnalysisResult:
    """Analyze a Vietnamese geometry problem into span-preserved compositional clauses & intent summary."""
    mapped = normalize_with_spans(problem_text, project_diacritic_free=True)
    ntext = mapped.normalized_text
    raw_sents = _split_top_sentences(ntext)
    clauses: list[CompositionalClause] = []
    cid = 0

    def push(role: str, subkind: str, a: int, b: int, sent_idx: int, *, lead: str | None = None, ambig: str | None = None) -> None:
        nonlocal cid
        ta, tb = _trim_span(ntext, a, b)
        if ta >= tb:
            return
        oa, ob = mapped.orig_span(ta, tb)
        ents = tuple(dict.fromkeys(re.findall(r"(?<![A-Za-zÀ-ỹ0-9_'])[A-Z][0-9']*(?![a-zà-ỹ])", ntext[ta:tb])))
        clauses.append(
            CompositionalClause(
                clause_id=cid,
                role=role,
                subkind=subkind,
                norm_text=ntext[ta:tb],
                norm_start=ta,
                norm_end=tb,
                orig_text=mapped.original_text[oa:ob],
                orig_start=oa,
                orig_end=ob,
                parent_sentence_id=sent_idx,
                embedded_simulation_lead=lead,
                ambiguity_reason=ambig,
                entity_hints=ents,
            )
        )
        cid += 1

    for sent_idx, (sa, sb) in enumerate(raw_sents):
        cur_a, cur_b = sa, sb
        seg = ntext[cur_a:cur_b]

        # 1. Strip inline exam header ("Câu 2 (2 điểm). ...")
        m_hdr = INLINE_EXAM_HEADER_PREFIX_RE.match(seg)
        if m_hdr and seg[m_hdr.end() :].strip():
            push(ROLE_CONTEXT_HEADER, "exam_header", cur_a, cur_a + m_hdr.end(), sent_idx)
            cur_a += m_hdr.end()
            seg = ntext[cur_a:cur_b]

        # 2. Strip inline leading meta ("Chỉ cần vẽ hình, không cần tính toán: ...")
        m_lmeta = INLINE_LEADING_META_RE.match(seg)
        if m_lmeta and seg[m_lmeta.end() :].strip():
            push(ROLE_NEGATED_REQUEST, "meta_no_calc", cur_a, cur_a + m_lmeta.end(), sent_idx)
            cur_a += m_lmeta.end()
            seg = ntext[cur_a:cur_b]

        # 3. Strip inline trailing meta ("... Không cần tính gì thêm.")
        m_tmeta = INLINE_TRAILING_META_RE.search(seg)
        if m_tmeta and seg[: m_tmeta.start()].strip():
            meta_a = cur_a + m_tmeta.start()
            meta_b = cur_a + m_tmeta.end()
            cur_b = meta_a
            seg = ntext[cur_a:cur_b]
        else:
            meta_a = meta_b = -1

        # 4. Check benign meta ("Không cần tính gì thêm"), then negated command or conditional
        if META_NO_CALC_RE.fullmatch(seg):
            push(ROLE_NEGATED_REQUEST, "meta_no_calc", cur_a, cur_b, sent_idx)
            if meta_a >= 0:
                push(ROLE_NEGATED_REQUEST, "meta_no_calc", meta_a, meta_b, sent_idx)
            continue

        if NEGATED_COMMAND_RE.search(seg):
            push(ROLE_NEGATED_REQUEST, "negated_command", cur_a, cur_b, sent_idx)
            if meta_a >= 0:
                push(ROLE_NEGATED_REQUEST, "meta_no_calc", meta_a, meta_b, sent_idx)
            continue

        if NEGATED_PREMISE_RE.search(seg):
            push(ROLE_NEGATED_REQUEST, "negated_premise", cur_a, cur_b, sent_idx)
            if meta_a >= 0:
                push(ROLE_NEGATED_REQUEST, "meta_no_calc", meta_a, meta_b, sent_idx)
            continue

        if CONDITIONAL_MARKER_RE.search(seg):
            push(ROLE_CONDITIONAL_PREMISE, "conditional", cur_a, cur_b, sent_idx)
            if meta_a >= 0:
                push(ROLE_NEGATED_REQUEST, "meta_no_calc", meta_a, meta_b, sent_idx)
            continue

        # 5. Split trailing measurement goal inside sentence ("Vẽ hình ... và tính thể tích ...")
        m_goal = _TRAILING_GOAL_SPLIT_RE.search(seg)
        goal_a = cur_a + m_goal.end() if m_goal else -1
        goal_b = cur_b if m_goal else -1
        body_a = cur_a
        body_b = cur_a + m_goal.start() if m_goal else cur_b
        body = ntext[body_a:body_b]

        # 6. Check for nested simulation declaration inside `body`
        m_sim = SIMULATION_LEAD_VERB_RE.match(body)
        if m_sim:
            after_verb = body[m_sim.end() :]
            m_solid = _EMBEDDED_SOLID_HEAD_RE.match(after_verb)
            m_ambig = VISUALIZATION_METRIC_NOUN_RE.search(body)
            if m_ambig and goal_a < 0:
                push(
                    ROLE_VISUALIZATION_REQUEST,
                    "ambiguous_metric_visualization",
                    body_a,
                    body_b,
                    sent_idx,
                    ambig="AMBIGUOUS_DISTANCE_OR_ANGLE_VISUALIZATION",
                )
            elif m_solid:
                decl_start = body_a + m_sim.end()
                sim_end = decl_start + m_solid.end("head")
                # Check if extra simulation words or premise tail follow the solid head
                has_trailing_premises = bool(ntext[sim_end:body_b].strip(" ,.:;"))
                if has_trailing_premises:
                    push(ROLE_SIMULATION_REQUEST, "nested_lead_simulation", body_a, sim_end, sent_idx, lead=body[: m_sim.end()].strip())
                    push(ROLE_OBJECT_DECLARATION, "embedded_declaration", decl_start, body_b, sent_idx)
                else:
                    push(ROLE_SIMULATION_REQUEST, "standalone_simulation", body_a, body_b, sent_idx, lead=body[: m_sim.end()].strip())
            else:
                role, subkind, ambig = _classify_atomic_clause(body)
                push(role, subkind, body_a, body_b, sent_idx, ambig=ambig)
        else:
            role, subkind, ambig = _classify_atomic_clause(body)
            push(role, subkind, body_a, body_b, sent_idx, ambig=ambig)

        if goal_a >= 0:
            push(ROLE_MEASUREMENT_REQUEST, "measurement", goal_a, goal_b, sent_idx)
        if meta_a >= 0:
            push(ROLE_NEGATED_REQUEST, "meta_no_calc", meta_a, meta_b, sent_idx)

    has_sim = any(
        c.role == ROLE_SIMULATION_REQUEST
        or (c.role == ROLE_VISUALIZATION_REQUEST and c.subkind == "named_object_visualization")
        or (c.role == ROLE_NEGATED_REQUEST and c.subkind == "meta_no_calc" and bool(re.search(r"\b(?:vẽ|dựng|mô\s+phỏng|biểu\s+diễn|hiển\s+thị)\b", c.norm_text, re.IGNORECASE)))
        for c in clauses
    )
    has_meas = any(c.role == ROLE_MEASUREMENT_REQUEST for c in clauses)
    has_neg_cmd = any(c.role == ROLE_NEGATED_REQUEST and c.subkind == "negated_command" for c in clauses)
    has_neg_prem = any(c.role == ROLE_NEGATED_REQUEST and c.subkind == "negated_premise" for c in clauses)
    has_cond = any(c.role == ROLE_CONDITIONAL_PREMISE for c in clauses)
    has_meta = any(c.role == ROLE_NEGATED_REQUEST and c.subkind == "meta_no_calc" for c in clauses)
    ambig_vis = tuple(c for c in clauses if c.ambiguity_reason is not None)

    return CompositionalAnalysisResult(
        analyzer_version=COMPOSITIONAL_CLAUSE_ANALYZER_VERSION,
        mapped=mapped,
        clauses=tuple(clauses),
        has_simulation_request=has_sim,
        has_measurement_request=has_meas,
        has_negated_command=has_neg_cmd,
        has_negated_premise=has_neg_prem,
        has_conditional_premise=has_cond,
        has_meta_no_calc=has_meta,
        ambiguous_visualization_clauses=ambig_vis,
        is_simulation_only_intent=(has_sim and not has_meas and not has_neg_cmd and not has_neg_prem and not has_cond and not ambig_vis),
        is_mixed_simulation_and_query=(has_sim and has_meas and not has_neg_cmd and not has_neg_prem and not has_cond),
        entity_bindings={
            "all_entity_tokens": tuple(dict.fromkeys(tok for c in clauses for tok in c.entity_hints)),
            "diacritic_projected": mapped.diacritic_projected,
            "ambiguous_diacritic_blocked": mapped.ambiguous_diacritic_blocked,
        },
    )


def build_source_span_provenance_records(
    analysis: CompositionalAnalysisResult,
    *,
    payload: dict[str, Any] | None = None,
    grounding_verdict: str = "VERIFIED",
) -> list[SourceSpanProvenanceRecord]:
    """Build 11-field SourceSpanProvenanceRecord items linking parsed facts to exact source spans."""
    records: list[SourceSpanProvenanceRecord] = []
    premises = list((payload or {}).get("premises") or ())
    solids = list((payload or {}).get("solids") or ())
    mgoals = list((payload or {}).get("math_goals") or ())
    sgoals = list((payload or {}).get("simulation_goals") or ())

    def find_quote_match(clause: CompositionalClause) -> tuple[dict[str, Any], dict[str, Any]]:
        for s in solids:
            if s.get("quote") and (s["quote"] in clause.orig_text or clause.orig_text in s["quote"]):
                return ({"solid_id": s.get("solid_id"), "notation": s.get("notation")}, {"item_type": "solid", **s})
        for p in premises:
            if p.get("quote") and (p["quote"] in clause.orig_text or clause.orig_text in p["quote"]):
                return ({"entities": clause.entity_hints}, {"item_type": "premise", **p})
        for g in mgoals:
            if g.get("quote") and (g["quote"] in clause.orig_text or clause.orig_text in g["quote"]):
                return ({"entities": clause.entity_hints}, {"item_type": "math_goal", **g})
        for sg in sgoals:
            if sg.get("quote") and (sg["quote"] in clause.orig_text or clause.orig_text in sg["quote"]):
                return ({"solid_id": sg.get("target_solid_id")}, {"item_type": "simulation_goal", **sg})
        return ({"entities": clause.entity_hints}, {})

    for cl in analysis.clauses:
        ebind, efact = find_quote_match(cl)
        verdict = (
            "REJECTED_AMBIGUOUS"
            if cl.ambiguity_reason
            else ("BLOCKED_NEGATION_OR_CONDITION" if cl.role in (ROLE_CONDITIONAL_PREMISE, ROLE_NEGATED_REQUEST) and cl.subkind != "meta_no_calc" else grounding_verdict)
        )
        records.append(
            SourceSpanProvenanceRecord(
                original_text=analysis.mapped.original_text,
                original_offsets=(cl.orig_start, cl.orig_end),
                normalized_text=analysis.mapped.normalized_text,
                normalized_offsets=(cl.norm_start, cl.norm_end),
                clause_boundaries=(cl.orig_start, cl.orig_end),
                clause_role=cl.role,
                quoted_source_span=cl.orig_text,
                entity_binding=ebind,
                extracted_fact=efact,
                grounding_verdict=verdict,
                subkind=cl.subkind,
            )
        )
    return records
