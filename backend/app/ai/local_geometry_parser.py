# -*- coding: utf-8 -*-
"""Deterministic local Vietnamese 3D geometry parser (`local-geometry-parser/1`).

Implements the 8-stage local-first pipeline required by Phase 1 (Section IV):
    Problem Text
      -> Stage 1: Normalization (span-preserving NFC + symbol canonicalization)
      -> Stage 2: Lexer / Tokenizer (geometric entities, numbers/radicals, operators)
      -> Stage 3: Clause & Sentence Splitter
      -> Stage 4: Grammar / Rule-Based Semantic Parser
      -> Stage 5: Typed Semantic AST
      -> Stage 6: Semantic Validation & Lowering to `TypedFactNextPayloadV2`
      -> Stage 7: Source-Span Coverage Check (`MAPPED_FACT`, `MAPPED_GOAL`, `BENIGN_DISCOURSE`,
                  `UNPARSED_FACT_CANDIDATE`, `UNPARSED_GOAL_CANDIDATE`, `UNRESOLVED_REFERENCE`)
      -> Stage 8: Contract & Source-Gate Verification (`typed-fact-next/2` + `bridge_v2` + `kiem_nguon`)

Design invariants:
- Zero AI/network calls (`0` Gemini calls).
- Zero hardcoded case IDs, coordinates, or expected answers.
- Every `quote` in the emitted `TypedFactNextPayloadV2` is an exact substring slice of `problem_text`.
- Fail-closed: if any clause containing geometric facts/goals cannot be parsed, `status` is downgraded
  to `LOCAL_PARSE_PARTIAL` or `LOCAL_PARSE_UNSUPPORTED` (never `LOCAL_PARSE_COMPLETE`), enabling
  `AdaptiveInputRouter` to invoke the verified Gemini `TypedFactNext` fallback when live AI is enabled.
"""
from __future__ import annotations

from collections import OrderedDict
import copy
from dataclasses import dataclass, field
from fractions import Fraction
import re
import time
from typing import Any
import unicodedata

from ..simulation.geometry_functions import TuChoi, planner, registry
from ..simulation.geometry_functions.typed_fact_next import (
    TypedFactNextPayloadV2,
    TypedFactNextValidationError,
    parse_typed_fact_next_v2,
)
from ..simulation.geometry_functions.typed_fact_next_bridge import bridge_v2
from ..simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC, detect_domain

LOCAL_GEOMETRY_PARSER_VERSION = "local-geometry-parser/1"

LOCAL_PARSE_COMPLETE = "LOCAL_PARSE_COMPLETE"
LOCAL_PARSE_PARTIAL = "LOCAL_PARSE_PARTIAL"
LOCAL_PARSE_AMBIGUOUS = "LOCAL_PARSE_AMBIGUOUS"
LOCAL_PARSE_UNSUPPORTED = "LOCAL_PARSE_UNSUPPORTED"

CLAUSE_MAPPED_FACT = "MAPPED_FACT"
CLAUSE_MAPPED_GOAL = "MAPPED_GOAL"
CLAUSE_BENIGN_DISCOURSE = "BENIGN_DISCOURSE"
CLAUSE_UNPARSED_FACT_CANDIDATE = "UNPARSED_FACT_CANDIDATE"
CLAUSE_UNPARSED_GOAL_CANDIDATE = "UNPARSED_GOAL_CANDIDATE"
CLAUSE_UNRESOLVED_REFERENCE = "UNRESOLVED_REFERENCE"


# ── Dataclasses for Tokenizer, Clause Splitter, AST, Coverage & Parse Result ─────────────────────────────────────────

@dataclass(frozen=True)
class GeoToken:
    kind: str
    text: str
    start: int
    end: int


@dataclass
class ClauseSpan:
    index: int
    start: int
    end: int
    text: str
    classification: str = CLAUSE_BENIGN_DISCOURSE
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SourceCoverageReport:
    total_clauses: int
    mapped_fact_clauses: int
    mapped_goal_clauses: int
    benign_discourse_clauses: int
    unparsed_fact_candidates: tuple[str, ...]
    unparsed_goal_candidates: tuple[str, ...]
    unresolved_references: tuple[str, ...]
    clauses: tuple[dict[str, Any], ...]
    coverage_complete: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_clauses": self.total_clauses,
            "mapped_fact_clauses": self.mapped_fact_clauses,
            "mapped_goal_clauses": self.mapped_goal_clauses,
            "benign_discourse_clauses": self.benign_discourse_clauses,
            "unparsed_fact_candidates": list(self.unparsed_fact_candidates),
            "unparsed_goal_candidates": list(self.unparsed_goal_candidates),
            "unresolved_references": list(self.unresolved_references),
            "clauses": list(self.clauses),
            "coverage_complete": self.coverage_complete,
        }


@dataclass(frozen=True)
class LocalParseResult:
    parser_version: str
    status: str
    payload: dict[str, Any] | None
    parsed_contract: TypedFactNextPayloadV2 | None
    ast: dict[str, Any]
    source_coverage: SourceCoverageReport
    reason_code: str | None = None
    fallback_reason: str | None = None
    parse_latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "parser_version": self.parser_version,
            "status": self.status,
            "reason_code": self.reason_code,
            "fallback_reason": self.fallback_reason,
            "parse_latency_ms": round(self.parse_latency_ms, 3),
            "source_coverage": self.source_coverage.to_dict(),
            "has_payload": self.payload is not None,
        }


# ── Lexical Patterns (General over arbitrary vertex names & values) ──────────────────────────────────────────────────

_PT = r"[A-Z][0-9]*'?"
_PTS2 = rf"(?:{_PT}){{2}}"
_PTS3 = rf"(?:{_PT}){{3}}"
_PTS4 = rf"(?:{_PT}){{4}}"
_PTS3_6 = rf"(?:{_PT}){{3,6}}"
_VAL = r"(?:\d+(?:√\d+)?(?:/\d+)?|\d*√\d+a(?:/\d+)?|√\d+(?:/\d+)?|\d*a(?:√\d+)?(?:/\d+)?|a√\d+(?:/\d+)?)(?![.,]\d|[A-Za-z0-9_'′²³₁₂₃°~√/])"


def _canon_val(v: str) -> str:
    """Canonicalize textbook `√3a` / `2√3a` into `ExactNumber` (`a√3` / `2a√3`)."""
    s = v.strip()
    m = re.fullmatch(r"(?P<k>\d*)√(?P<r>\d+)a(?P<d>/\d+)?", s)
    if m:
        return f"{m.group('k')}a√{m.group('r')}{m.group('d') or ''}"
    return s

_TOKEN_RE = re.compile(
    rf"(?P<solid>{_PT}\.{_PTS3_6}|{_PTS3_6}\.{_PTS3_6})"
    rf"|(?P<plane>\((?:{_PTS3_6}|{_PT}|[α-ω]'?)\))"
    rf"|(?P<value>{_VAL})"
    rf"|(?P<op>[⊥∥=])"
    rf"|(?P<label>{_PT}(?:{_PT})*)"
    rf"|(?P<word>[^\s,.;:?!()]+)",
    re.UNICODE,
)


def _split_pts(s: str) -> list[str]:
    return re.findall(_PT, s.replace("′", "'"))


def _clean_quote(raw_text: str, start: int, end: int) -> str:
    """Return an exact verbatim substring of `raw_text` with leading/trailing punctuation/whitespace trimmed."""
    while start < end and raw_text[start] in " \t\r\n,.;:?!":
        start += 1
    while end > start and raw_text[end - 1] in " \t\r\n,.;:?!":
        end -= 1
    return raw_text[start:end]


def _find_verbatim_span(raw_text: str, start_hint: int, end_hint: int) -> str:
    return _clean_quote(raw_text, start_hint, end_hint)


# ── Stage 1 & 2: Normalization and Tokenization ──────────────────────────────────────────────────────────────────────

def normalize_problem_text(problem_text: str) -> str:
    """Unicode NFC normalization preserving character alignment for standard Vietnamese text."""
    return unicodedata.normalize("NFC", problem_text or "").replace("\u2032", "'")


def tokenize_problem_text(text: str) -> list[GeoToken]:
    tokens: list[GeoToken] = []
    for m in _TOKEN_RE.finditer(text):
        kind = m.lastgroup or "word"
        tokens.append(GeoToken(kind=kind, text=m.group(0), start=m.start(), end=m.end()))
    return tokens


# ── Stage 3: Clause & Sentence Splitter ──────────────────────────────────────────────────────────────────────────────

def split_into_Sentences(text: str) -> list[tuple[int, int, str]]:
    """Split text on sentence boundaries (`.` not inside `S.ABCD` or decimals, `;`, `?`, `!`, `\n`)."""
    bounds = [0]
    n = len(text)
    for i, ch in enumerate(text):
        if ch in "?!\n":
            bounds.append(i + 1)
        elif ch == ";":
            # Do not split inside uppercase point/segment lists like "Gọi M; N; P lần lượt là trung điểm của SA; SB; SC"
            if re.search(r"(?<![a-zà-ỹ])(?:[A-Z][0-9']*)+$", text[:i].rstrip()) and re.match(
                r"^\s*(?:[A-Z][0-9']*)+(?:\s*(?:[,;.]|\b(?i:và|lần\s+lượt)\b)|\s*$)",
                text[i + 1 :],
            ):
                continue
            bounds.append(i + 1)
        elif ch == ".":
            prev_ch = text[i - 1] if i > 0 else ""
            next_ch = text[i + 1] if i + 1 < n else ""
            # Do not split inside solid notation like S.ABCD or ABC.A'B'C' or decimal 1.5
            if (prev_ch.isupper() or prev_ch in "0123456789'") and next_ch.isupper():
                continue
            if prev_ch.isdigit() and next_ch.isdigit():
                continue
            bounds.append(i + 1)
    bounds.append(n)
    out: list[tuple[int, int, str]] = []
    for a, b in zip(bounds, bounds[1:]):
        while a < b and text[a].isspace():
            a += 1
        while b > a and (text[b - 1].isspace() or text[b - 1] in ".;?!"):
            b -= 1
        if a < b:
            out.append((a, b, text[a:b]))
    return out


def split_into_clauses(text: str) -> list[ClauseSpan]:
    """Split sentences into fine-grained semantic clauses while preserving exact spans into `text`."""
    sents = split_into_Sentences(text)
    clauses: list[ClauseSpan] = []
    idx = 0
    for sa, sb, _st in sents:
        clauses.append(ClauseSpan(index=idx, start=sa, end=sb, text=text[sa:sb]))
        idx += 1
    return clauses


# ── Stage 4 & 5: Grammar / Rule-Based Semantic Parser -> Typed Semantic AST ──────────────────────────────────────────

_QUESTION_STARTER_RE = re.compile(
    r"(?:^|\b)(?:tính|tìm|xác\s+định|hỏi|dựng|vẽ|mô\s+phỏng|cho\s+mình\s+xem|chứng\s+minh|bao\s+nhiêu|mấy)\b|\?|(?<!\w)(?:bằng|là)\s*:?\s*$",
    re.IGNORECASE | re.UNICODE,
)

_FACT_INDICATOR_RE = re.compile(
    r"\b(?:cho|hình\s+chóp|hình\s+lăng\s+trụ|lăng\s+trụ|tứ\s+diện|hình\s+lập\s+phương|hình\s+hộp|"
    r"mặt\s+cầu|khối\s+cầu|hình\s+trụ|hình\s+nón|đáy|vuông\s+góc|song\s+song|trung\s+điểm|trọng\s+tâm|"
    r"hình\s+chiếu|giao\s+điểm|mặt\s+phẳng|cạnh|chiều\s+cao|đường\s+cao|đường\s+sinh|bán\s+kính|gọi|biết)\b|[⊥∥=]",
    re.IGNORECASE | re.UNICODE,
)

# Inline described-point patterns (supports depth-1 and depth-2 nesting)
_DESC_LEAF_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "midpoint",
        re.compile(
            rf"(?:trung\s+điểm(?:\s+của)?(?:\s+cạnh|\s+đoạn(?:\s+thẳng)?)?\s+(?P<seg>{_PTS2})"
            rf"|điểm\s+chính\s+giữa(?:\s+của)?(?:\s+cạnh|\s+đoạn(?:\s+thẳng)?)?\s+(?P<seg2>{_PTS2}))(?![\w'])",
            re.IGNORECASE | re.UNICODE,
        ),
    ),
    (
        "centroid",
        re.compile(
            rf"trọng\s+tâm(?:\s+của)?\s+tam\s+giác\s+(?P<poly>{_PTS3})(?![\w'])",
            re.IGNORECASE | re.UNICODE,
        ),
    ),
    (
        "orthocenter",
        re.compile(
            rf"trực\s+tâm(?:\s+của)?\s+tam\s+giác\s+(?P<poly>{_PTS3})(?![\w'])",
            re.IGNORECASE | re.UNICODE,
        ),
    ),
    (
        "circumcenter",
        re.compile(
            rf"tâm\s+đường\s+tròn\s+ngoại\s+tiếp(?:\s+của)?\s+tam\s+giác\s+(?P<poly>{_PTS3})(?![\w'])",
            re.IGNORECASE | re.UNICODE,
        ),
    ),
    (
        "intersect_line_line",
        re.compile(
            rf"giao\s+điểm\s+của(?:\s+hai\s+đường\s+thẳng)?\s+(?P<l1>{_PTS2})\s+và\s+(?P<l2>{_PTS2})(?![\w'])",
            re.IGNORECASE | re.UNICODE,
        ),
    ),
    (
        "intersect_line_plane",
        re.compile(
            rf"giao\s+điểm\s+của(?:\s+đường\s+thẳng)?\s+(?P<line>{_PTS2})\s+và\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<plane>{_PTS3_6})\)",
            re.IGNORECASE | re.UNICODE,
        ),
    ),
    (
        "orthogonal_projection_line",
        re.compile(
            rf"hình\s+chiếu\s+vuông\s+góc\s+của(?:\s+điểm)?\s+(?P<pt>{_PT})\s+(?:lên|trên)\s+(?:đường\s+thẳng\s+|cạnh\s+)?(?P<line>{_PTS2})(?![\w')])",
            re.IGNORECASE | re.UNICODE,
        ),
    ),
    (
        "orthogonal_projection",
        re.compile(
            rf"hình\s+chiếu\s+vuông\s+góc\s+của(?:\s+điểm)?\s+(?P<pt>{_PT})\s+(?:lên|trên)\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<plane>{_PTS3_6})\)",
            re.IGNORECASE | re.UNICODE,
        ),
    ),
)

_NESTED_PROJ_PLANE_RE = re.compile(
    rf"hình\s+chiếu\s+vuông\s+góc\s+của\s+(?P<inner>(?:trung\s+điểm|trọng\s+tâm|trực\s+tâm|tâm\s+đường\s+tròn\s+ngoại\s+tiếp|giao\s+điểm).*?)\s+(?:lên|trên)\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<plane>{_PTS3_6})\)",
    re.IGNORECASE | re.UNICODE,
)


class _AstBuilder:
    def __init__(self, raw_text: str) -> None:
        self.raw_text = raw_text
        self.solids: list[dict[str, Any]] = []
        self.premises: list[dict[str, Any]] = []
        self.described_points: list[dict[str, Any]] = []
        self.derived_sections: list[dict[str, Any]] = []
        self.relations: list[dict[str, Any]] = []
        self.simulation_goals: list[dict[str, Any]] = []
        self.math_goals: list[dict[str, Any]] = []
        self.unresolved: list[dict[str, Any]] = []
        self._desc_by_key: dict[tuple[Any, ...], str] = {}
        self._desc_counters: dict[str, int] = {}
        self._base_vertices: list[str] = []
        self._primary_solid_id: str = "s1"
        self._primary_solid_type: str | None = None
        self._primary_notation: str | None = None
        self._section_by_plane_name: dict[str, str] = {}
        self._last_section_id: str | None = None
        self._sphere_by_notation: dict[str, str] = {}
        self._sphere_center_map: dict[str, str] = {}

    def _alloc_desc_id(self, kind: str) -> str:
        prefix = {
            "midpoint": "m",
            "centroid": "g",
            "orthocenter": "h",
            "circumcenter": "o",
            "orthogonal_projection": "h",
            "orthogonal_projection_line": "h",
            "intersect_line_line": "i",
            "intersect_line_plane": "i",
        }.get(kind, "p")
        n = self._desc_counters.get(prefix, 0) + 1
        self._desc_counters[prefix] = n
        return f"{prefix}{n}"

    def _register_described_point(self, spec: dict[str, Any]) -> str:
        key = (
            spec["kind"],
            tuple(spec.get("segment") or ()),
            tuple(spec.get("polygon") or ()),
            spec.get("point"),
            tuple(spec.get("line") or ()),
            tuple(spec.get("plane") or ()),
            tuple(spec.get("line1") or ()),
            tuple(spec.get("line2") or ()),
        )
        if key in self._desc_by_key:
            return f"@{self._desc_by_key[key]}"
        did = self._alloc_desc_id(spec["kind"])
        full = {"described_id": did, **spec}
        self.described_points.append(full)
        self._desc_by_key[key] = did
        return f"@{did}"

    def parse_point_or_described(self, phrase: str, phrase_start_in_raw: int) -> str | None:
        """Resolve either a single vertex label (e.g. `A` or `điểm A`) or an inline described point (`@m1`)."""
        s = phrase.strip()
        m_pt = re.fullmatch(rf"(?:điểm\s+)?(?P<p>{_PT})", s, re.IGNORECASE | re.UNICODE)
        if m_pt:
            return m_pt.group("p").replace("′", "'")

        # Check depth-2 nested orthogonal projection onto plane
        m_nest = _NESTED_PROJ_PLANE_RE.fullmatch(s)
        if m_nest:
            inner_str = m_nest.group("inner")
            inner_offset = phrase.find(inner_str)
            inner_ref = self.parse_point_or_described(
                inner_str, phrase_start_in_raw + (inner_offset if inner_offset >= 0 else 0)
            )
            if inner_ref:
                q_outer = _clean_quote(self.raw_text, phrase_start_in_raw, phrase_start_in_raw + len(phrase))
                return self._register_described_point(
                    {
                        "kind": "orthogonal_projection",
                        "point": inner_ref,
                        "plane": _split_pts(m_nest.group("plane")),
                        "quote": q_outer,
                    }
                )

        # Check depth-1 leaf described point
        for kind, pat in _DESC_LEAF_PATTERNS:
            m = pat.fullmatch(s)
            if m:
                q = _clean_quote(self.raw_text, phrase_start_in_raw, phrase_start_in_raw + len(phrase))
                if kind == "midpoint":
                    seg_str = m.group("seg") or m.group("seg2")
                    return self._register_described_point(
                        {"kind": "midpoint", "segment": _split_pts(seg_str), "quote": q}
                    )
                if kind in ("centroid", "orthocenter", "circumcenter"):
                    return self._register_described_point(
                        {"kind": kind, "polygon": _split_pts(m.group("poly")), "quote": q}
                    )
                if kind == "intersect_line_line":
                    return self._register_described_point(
                        {
                            "kind": "intersect_line_line",
                            "line1": _split_pts(m.group("l1")),
                            "line2": _split_pts(m.group("l2")),
                            "quote": q,
                        }
                    )
                if kind == "intersect_line_plane":
                    return self._register_described_point(
                        {
                            "kind": "intersect_line_plane",
                            "line": _split_pts(m.group("line")),
                            "plane": _split_pts(m.group("plane")),
                            "quote": q,
                        }
                    )
                if kind == "orthogonal_projection_line":
                    return self._register_described_point(
                        {
                            "kind": "orthogonal_projection_line",
                            "point": m.group("pt").replace("′", "'"),
                            "line": _split_pts(m.group("line")),
                            "quote": q,
                        }
                    )
                if kind == "orthogonal_projection":
                    return self._register_described_point(
                        {
                            "kind": "orthogonal_projection",
                            "point": m.group("pt").replace("′", "'"),
                            "plane": _split_pts(m.group("plane")),
                            "quote": q,
                        }
                    )
        return None


def _detect_length_unit(raw_text: str) -> str:
    # Check if symbolic unit `a` is used in length assignments (e.g. `cạnh a`, `= a`, `= 2a`, `= a√3`, `= √3a`)
    if re.search(
        r"(?:\bcạnh(?:\s+đáy|\s+bên)?(?:\s+bằng)?\s+|\=\s*)(?:\d*a(?:√\d+)?(?:/\d+)?|\d*√\d+a(?:/\d+)?)\b",
        raw_text,
    ):
        return "a"
    return "1"


_EXAM_HEADER_PREFIX_RE = re.compile(
    r"^(?:\s*(?:(?:Câu|Bài(?:\s+tập)?|Ví\s+dụ)\s*(?:\d+|[a-d])\s*[:.)]?|(?:\d+|[a-d])\s*\)|\(\s*\d+(?:[.,]\d+)?\s*điểm\s*\))\s*)+",
    re.IGNORECASE | re.UNICODE,
)
_FIG_REF_SUFFIX_RE = re.compile(
    r"\s*\(\s*(?:(?:hình\s+)?minh\s+h[ọo]a(?:\s+như)?|tham\s+khảo|như|xem)\s+hình(?:\s+vẽ)?(?:\s+bên(?:\s+dưới|\s+trên)?)?\s*\)\s*$",
    re.IGNORECASE | re.UNICODE,
)


def _parse_clause_into_ast(builder: _AstBuilder, clause: ClauseSpan) -> None:
    raw = builder.raw_text
    ca, cb = clause.start, clause.end
    ctext = raw[ca:cb]
    ctext_norm = ctext.replace("′", "'")
    m_hdr = _EXAM_HEADER_PREFIX_RE.match(ctext_norm)
    if m_hdr and ctext_norm[m_hdr.end() :].strip():
        ca += m_hdr.end()
        ctext = raw[ca:cb]
        ctext_norm = ctext.replace("′", "'")
    m_fig_ref = _FIG_REF_SUFFIX_RE.search(ctext_norm)
    if m_fig_ref and ctext_norm[: m_fig_ref.start()].strip():
        cb = ca + m_fig_ref.start()
        ctext = raw[ca:cb]
        ctext_norm = ctext.replace("′", "'")

    mapped_fact = False
    mapped_goal = False
    clause_solid_not_span: tuple[int, int] | None = None
    angle_spans: list[tuple[int, int]] = []
    pre_premises_len = len(builder.premises)
    pre_sections_len = len(builder.derived_sections)
    pre_goals_len = len(builder.math_goals)
    pre_solids_len = len(builder.solids)

    # ── 0. Explicit unsupported / out-of-scope or clarification triggers ─────────────────────────────────────────
    # Conditional premise ("Nếu mặt phẳng ... thì ...") -> leave as unparsed or let Source Gate refuse?
    # Wait: if we parse conditional clauses as normal sections/premises, Source Gate (`kiem_nguon`) deterministically
    # refuses with `CONDITIONAL_CLAUSE`! Same for negated clauses (`không song song`, `không vuông góc`) -> `NEGATED_CLAUSE`!
    # Let's check explicit unsupported constructs that need `unresolved: [{"kind": "unsupported", ...}]`:
    m_unsup = re.search(
        r"(?P<q>Trong\s+không\s+gian\s+Oxyz"
        r"|hình\s+chóp\s+cụt(?:\s+đều)?(?:\s+[A-Z0-9'.]+)?"
        r"|Tìm\s+giá\s+trị\s+(?:lớn\s+nhất|nhỏ\s+nhất).*"
        r"|Hỏi\s+sau\s+bao\s+nhiêu\s+phút.*"
        r"|Tìm\s+tập\s+hợp\s+các\s+điểm.*"
        r"|Dựng\s+ảnh\s+của\s+.*qua\s+phép\s+tịnh\s+tiến.*"
        r"|điểm\s+đối\s+xứng\s+với\s+[A-Z0-9']+\s+qua\s+[A-Z0-9']+"
        r"|Chứng\s+minh(?:\s+rằng)?.*)",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_unsup:
        q = _clean_quote(raw, ca + m_unsup.start("q"), ca + m_unsup.end("q"))
        builder.unresolved.append(
            {
                "unresolved_id": f"u{len(builder.unresolved) + 1}",
                "kind": "unsupported",
                "quote": q,
                "missing_roles": [],
                "candidate_relations": [],
            }
        )
        clause.classification = CLAUSE_MAPPED_GOAL
        return

    # Check explicit clarification / ambiguous constructs (`S2-C`, `K-E`, `R1-E`, `N4`, `HB41`)
    m_goc_chieu = re.search(
        rf"(?P<p>{_PT})\s+là\s+góc\s+chiếu\s+của\s+hình\s+lăng\s+trụ(?:\s+xiên)?",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_goc_chieu:
        q = _clean_quote(raw, ca + m_goc_chieu.start(), ca + m_goc_chieu.end())
        builder.unresolved.append(
            {
                "unresolved_id": f"u{len(builder.unresolved) + 1}",
                "kind": "ambiguous",
                "quote": q,
                "missing_roles": ["source_point", "target_line_or_plane"],
                "candidate_relations": ["orthogonal_projection"],
                "subject_ref": m_goc_chieu.group("p"),
            }
        )
        clause.classification = CLAUSE_MAPPED_FACT
        return

    m_proj_missing = re.search(
        rf"Gọi\s+(?P<h>{_PT})\s+là\s+hình\s+chiếu(?:\s+vuông\s+góc)?\s+của\s+(?P<s>{_PT})\s*$",
        ctext_norm.strip(),
        re.IGNORECASE | re.UNICODE,
    )
    if m_proj_missing:
        q = _clean_quote(raw, ca, cb)
        builder.unresolved.append(
            {
                "unresolved_id": f"u{len(builder.unresolved) + 1}",
                "kind": "missing_operand",
                "quote": q,
                "missing_roles": ["target_line_or_plane"],
                "candidate_relations": ["orthogonal_projection"],
                "subject_ref": m_proj_missing.group("h"),
            }
        )
        clause.classification = CLAUSE_MAPPED_FACT
        return

    if re.fullmatch(r"(?:Mô\s+phỏng|Vẽ|Cho)\s+hình\s+(?:lăng\s+trụ|chóp|hộp)", ctext_norm.strip(), re.IGNORECASE):
        q = _clean_quote(raw, ca, cb)
        builder.unresolved.append(
            {
                "unresolved_id": f"u{len(builder.unresolved) + 1}",
                "kind": "missing_operand",
                "quote": q,
                "missing_roles": ["solid_notation", "dimension"],
                "candidate_relations": [],
            }
        )
        clause.classification = CLAUSE_MAPPED_GOAL
        return

    m_ambig_desc = re.search(
        r"(?P<q>trung\s+điểm\s+của\s+một\s+cạnh(?:\s+bên|\s+đáy)?|trực\s+tâm\s+của\s+một\s+tam\s+giác[^.?!]*?đến|hình\s+chiếu\s+vuông\s+góc\s+của\s+[A-Z0-9']+\s+đến\b)",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_ambig_desc:
        q_raw = m_ambig_desc.group("q")
        if q_raw.lower().endswith("đến"):
            q_end = ca + m_ambig_desc.end("q") - 3
            q = _clean_quote(raw, ca + m_ambig_desc.start("q"), q_end)
            builder.unresolved.append(
                {
                    "unresolved_id": f"u{len(builder.unresolved) + 1}",
                    "kind": "ambiguous",
                    "quote": q,
                    "missing_roles": ["goal_object"],
                    "candidate_relations": [],
                }
            )
        elif "hình chiếu" in q_raw.lower():
            m_hc = re.search(r"hình\s+chiếu\s+vuông\s+góc\s+của\s+[A-Z0-9']+", ctext_norm, re.IGNORECASE)
            q = _clean_quote(raw, ca + m_hc.start(), ca + m_hc.end()) if m_hc else _clean_quote(raw, ca, cb)
            builder.unresolved.append(
                {
                    "unresolved_id": f"u{len(builder.unresolved) + 1}",
                    "kind": "missing_operand",
                    "quote": q,
                    "missing_roles": ["target_line_or_plane"],
                    "candidate_relations": ["orthogonal_projection"],
                }
            )
        else:
            q = _clean_quote(raw, ca + m_ambig_desc.start("q"), ca + m_ambig_desc.end("q"))
            builder.unresolved.append(
                {
                    "unresolved_id": f"u{len(builder.unresolved) + 1}",
                    "kind": "ambiguous",
                    "quote": q,
                    "missing_roles": ["source_point"],
                    "candidate_relations": ["midpoint"],
                }
            )
        clause.classification = CLAUSE_MAPPED_GOAL
        return

    # ── 1. Solid declarations ────────────────────────────────────────────────────────────────────────────────────
    # 1a. Shared-base two pyramids: "Hai hình chóp S.ABCD và T.ABCD có mặt chung ABCD"
    m_two_pyr = re.search(
        rf"Hai\s+hình\s+chóp\s+(?P<s1>{_PT}\.{_PTS3_6})\s+và\s+(?P<s2>{_PT}\.{_PTS3_6})\s+có\s+mặt\s+chung\s+\(?(?P<face>{_PTS3_6})\)?",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_two_pyr:
        q_full = _clean_quote(raw, ca, cb)
        n1, n2 = m_two_pyr.group("s1"), m_two_pyr.group("s2")
        face_pts = _split_pts(m_two_pyr.group("face"))
        builder._base_vertices = face_pts
        builder.solids.append(
            {
                "solid_id": "s1",
                "solid_type": "pyramid",
                "notation": n1,
                "coordinate_frame_id": "root",
                "quote": q_full,
            }
        )
        builder.solids.append(
            {
                "solid_id": "s2",
                "solid_type": "pyramid",
                "notation": n2,
                "coordinate_frame_id": "root",
                "quote": q_full,
            }
        )
        builder.relations.extend(
            [
                {
                    "relation_id": "r_shared",
                    "kind": "shared_faces",
                    "solid_a": "s1",
                    "solid_b": "s2",
                    "face_a": face_pts,
                    "face_b": face_pts,
                    "quote": q_full,
                },
                {
                    "relation_id": "r_f1",
                    "kind": "coordinate_frame",
                    "solid_id": "s1",
                    "frame_id": "root",
                    "quote": q_full,
                },
                {
                    "relation_id": "r_f2",
                    "kind": "coordinate_frame",
                    "solid_id": "s2",
                    "frame_id": "root",
                    "quote": q_full,
                },
            ]
        )
        builder._primary_solid_id = "s1"
        builder._primary_solid_type = "pyramid"
        builder._primary_notation = n1
        if not builder.simulation_goals:
            builder.simulation_goals.append(
                {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": q_full}
            )
        mapped_fact = True

    # 1b. Regular pyramid: "(Cho )?(Hình|Khối) chóp (tứ giác|tam giác|lục giác)? đều S.ABCD có cạnh đáy bằng 6..."
    m_reg_pyr = re.search(
        rf"(?P<lead>(?:Cho|Vẽ|Mô\s+phỏng|Cho\s+mình\s+xem)\s+)?(?P<core>(?:hình|khối)\s+chóp(?:\s+(?:tứ\s+giác|tam\s+giác|lục\s+giác))?\s+đều\s+(?P<not>{_PT}\.{_PTS3_6}))",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_reg_pyr:
        clause_solid_not_span = (m_reg_pyr.start("not"), m_reg_pyr.end("not"))
        not_str = m_reg_pyr.group("not")
        apex_s, base_s = not_str.split(".", 1)
        base_pts = _split_pts(base_s)
        builder._base_vertices = base_pts
        q_core = _clean_quote(
            raw,
            ca + (m_reg_pyr.start("lead") if m_reg_pyr.group("lead") else m_reg_pyr.start("core")),
            ca + m_reg_pyr.end("core"),
        )
        existing_s1 = next((s for s in builder.solids if s["notation"] == not_str), None)
        if existing_s1 is not None:
            existing_s1["quote"] = q_core
            sid = existing_s1["solid_id"]
        else:
            sid = "s1"
            builder.solids.append(
                {"solid_id": sid, "solid_type": "pyramid", "notation": not_str, "quote": q_core}
            )
            builder._primary_solid_id = sid
            builder._primary_solid_type = "pyramid"
            builder._primary_notation = not_str
        if not any(sg.get("target_solid_id") == sid for sg in builder.simulation_goals):
            builder.simulation_goals.append(
                {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": sid, "quote": q_core}
            )
        builder.premises.append(
            {
                "kind": "regular_pyramid",
                "args": {"apex": apex_s, "base": base_pts},
                "quote": q_core,
                "solid_id": sid,
            }
        )
        m_side = re.search(
            rf"có\s+cạnh\s+đáy\s+(?:bằng\s+)?(?P<val>{_VAL})",
            ctext_norm[m_reg_pyr.end("core") :],
            re.IGNORECASE | re.UNICODE,
        )
        if m_side:
            q_side = _clean_quote(
                raw,
                ca + (m_reg_pyr.start("lead") if m_reg_pyr.group("lead") else m_reg_pyr.start("core")),
                ca + m_reg_pyr.end("core") + m_side.end(),
            )
            builder.premises.append(
                {
                    "kind": "regular_polygon",
                    "args": {"vertices": base_pts, "side": _canon_val(m_side.group("val"))},
                    "quote": q_side,
                    "solid_id": sid,
                }
            )
            m_lat = re.match(
                rf"\s*(?:,\s*|\s+và\s+|\s+có\s+)cạnh\s+bên\s+(?:bằng\s+|=\s*)?(?P<lat>{_VAL})",
                ctext_norm[m_reg_pyr.end("core") + m_side.end() :],
                re.IGNORECASE | re.UNICODE,
            )
            if m_lat:
                q_lat = _clean_quote(
                    raw,
                    ca + (m_reg_pyr.start("lead") if m_reg_pyr.group("lead") else m_reg_pyr.start("core")),
                    ca + m_reg_pyr.end("core") + m_side.end() + m_lat.end(),
                )
                builder.premises.append(
                    {
                        "kind": "segment_length",
                        "args": {"segment": [apex_s, base_pts[0]], "value": _canon_val(m_lat.group("lat"))},
                        "quote": q_lat,
                        "solid_id": sid,
                    }
                )
        m_h = re.search(
            rf"chiều\s+cao(?:\s+của\s+(?:hình|khối)\s+chóp(?:\s+{re.escape(not_str)})?)?\s*(?:bằng\s+|=\s*)(?P<h>{_VAL})",
            ctext_norm,
            re.IGNORECASE | re.UNICODE,
        )
        if m_h:
            q_h = _clean_quote(raw, ca, cb)
            builder.premises.append(
                {
                    "kind": "height",
                    "args": {"solid": sid, "value": _canon_val(m_h.group("h"))},
                    "quote": q_h,
                    "solid_id": sid,
                }
            )
        mapped_fact = True

    # 1c. Standard pyramid: "(Cho|Vẽ|Mô phỏng|Cho mình xem) (hình|khối) chóp S.ABCD"
    if not m_reg_pyr and not m_two_pyr:
        m_pyr = re.search(
            rf"(?P<lead>(?:Cho\s+mình\s+xem|Mô\s+phỏng|Vẽ|Cho)\s+)?(?P<core>(?:hình|khối)\s+ch[oó]p\s+(?P<not>{_PT}\.{_PTS3_6}))",
            ctext_norm,
            re.IGNORECASE | re.UNICODE,
        )
        if m_pyr:
            clause_solid_not_span = (m_pyr.start("not"), m_pyr.end("not"))
            not_str = m_pyr.group("not")
            _ap, base_s = not_str.split(".", 1)
            base_pts = _split_pts(base_s)
            lead_txt = (m_pyr.group("lead") or "").strip().lower()
            # If the sentence is a trailing simulation request ("Vẽ hình chóp S.ABCD.") when s1 already exists:
            if builder.solids and builder._primary_notation == not_str and lead_txt in ("vẽ", "mô phỏng", "cho mình xem"):
                q_sim = _clean_quote(raw, ca + m_pyr.start(), ca + m_pyr.end())
                builder.simulation_goals = [
                    {
                        "goal_id": "sg1",
                        "kind": "construct_object",
                        "target_solid_id": builder._primary_solid_id,
                        "quote": q_sim,
                    }
                ]
                mapped_goal = True
            elif not builder.solids:
                builder._base_vertices = base_pts
                q_solid = (
                    _clean_quote(raw, ca + m_pyr.start("core"), ca + m_pyr.end("core"))
                    if lead_txt in ("vẽ", "mô phỏng", "cho mình xem")
                    else _clean_quote(raw, ca + m_pyr.start(), ca + m_pyr.end())
                )
                q_sim = _clean_quote(raw, ca + m_pyr.start(), ca + m_pyr.end())
                sid = "s1"
                builder.solids.append(
                    {"solid_id": sid, "solid_type": "pyramid", "notation": not_str, "quote": q_solid}
                )
                builder.simulation_goals.append(
                    {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": sid, "quote": q_sim}
                )
                builder._primary_solid_id = sid
                builder._primary_solid_type = "pyramid"
                builder._primary_notation = not_str
                mapped_fact = True

    # 1d. Tetrahedron: "Cho tứ diện (đều )?OABC" or "Cho tứ diện ABCD"
    m_tet = re.search(
        rf"(?P<lead>(?:Cho|Vẽ|Mô\s+phỏng)\s+)?(?P<core>tứ\s+diện(?:\s+(?P<reg>đều))?\s+(?P<pts>{_PTS4}))(?![\w'.])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_tet and not builder.solids:
        pts = _split_pts(m_tet.group("pts"))
        not_str = f"{pts[0]}.{''.join(pts[1:])}"
        builder._base_vertices = pts[1:]
        q_solid = _clean_quote(raw, ca + m_tet.start(), ca + m_tet.end())
        sid = "s1"
        builder.solids.append(
            {"solid_id": sid, "solid_type": "pyramid", "notation": not_str, "quote": q_solid}
        )
        builder.simulation_goals.append(
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": sid, "quote": q_solid}
        )
        builder._primary_solid_id = sid
        builder._primary_solid_type = "pyramid"
        builder._primary_notation = not_str
        if m_tet.group("reg"):
            m_side = re.search(rf"cạnh\s+(?:bằng\s+)?(?P<val>{_VAL})", ctext_norm, re.IGNORECASE | re.UNICODE)
            q_full = _clean_quote(raw, ca, cb)
            builder.premises.append(
                {"kind": "regular_pyramid", "args": {"apex": pts[0], "base": pts[1:]}, "quote": q_full, "solid_id": sid}
            )
            if m_side:
                val = m_side.group("val")
                builder.premises.append(
                    {"kind": "regular_polygon", "args": {"vertices": pts[1:], "side": val}, "quote": q_full, "solid_id": sid}
                )
                builder.premises.append(
                    {"kind": "segment_length", "args": {"segment": [pts[0], pts[1]], "value": val}, "quote": q_full, "solid_id": sid}
                )
        mapped_fact = True

    # 1e. Cube: "Cho hình lập phương ABCD.A'B'C'D' (có cạnh bằng 2)?"
    m_cube = re.search(
        rf"(?P<lead>(?:Cho|Vẽ|Mô\s+phỏng)\s+)?hình\s+lập\s+phương\s+(?P<not>{_PTS4}\.{_PTS4})(?P<tail>\s+(?:có\s+)?cạnh\s+(?:bằng\s+)?(?P<val>{_VAL}))?",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_cube and not builder.solids:
        not_str = m_cube.group("not")
        b_str, t_str = not_str.split(".", 1)
        base_pts, top_pts = _split_pts(b_str), _split_pts(t_str)
        builder._base_vertices = base_pts
        sid = "s1"
        if m_cube.group("val"):
            q_cube = _clean_quote(raw, ca + m_cube.start(), ca + m_cube.end())
            val = m_cube.group("val")
            builder.solids.append({"solid_id": sid, "solid_type": "prism", "notation": not_str, "quote": q_cube})
            builder.simulation_goals.append({"goal_id": "sg1", "kind": "construct_object", "target_solid_id": sid, "quote": q_cube})
            builder.premises.extend(
                [
                    {"kind": "right_prism", "args": {"base": base_pts, "top": top_pts}, "quote": q_cube, "solid_id": sid},
                    {"kind": "regular_polygon", "args": {"vertices": base_pts, "side": val}, "quote": q_cube, "solid_id": sid},
                    {"kind": "segment_length", "args": {"segment": [base_pts[0], top_pts[0]], "value": val}, "quote": q_cube, "solid_id": sid},
                ]
            )
        else:
            q_cube = _clean_quote(raw, ca + m_cube.start(), ca + m_cube.end("not"))
            builder.solids.append({"solid_id": sid, "solid_type": "prism", "notation": not_str, "quote": q_cube})
            builder.simulation_goals.append({"goal_id": "sg1", "kind": "construct_object", "target_solid_id": sid, "quote": q_cube})
            builder.premises.append(
                {"kind": "right_prism", "args": {"base": base_pts, "top": top_pts}, "quote": q_cube, "solid_id": sid}
            )
        builder._primary_solid_id = sid
        builder._primary_solid_type = "prism"
        builder._primary_notation = not_str
        mapped_fact = True

    # 1e-2. Rectangular box (cuboid): "Cho hình hộp chữ nhật ABCD.A'B'C'D'"
    m_cuboid = re.search(
        rf"(?P<lead>(?:Cho|Vẽ|Mô\s+phỏng)\s+)?hình\s+hộp\s+chữ\s+nhật\s+(?P<not>{_PTS4}\.{_PTS4})",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_cuboid and not builder.solids:
        not_str = m_cuboid.group("not")
        b_str, t_str = not_str.split(".", 1)
        base_pts, top_pts = _split_pts(b_str), _split_pts(t_str)
        builder._base_vertices = base_pts
        sid = "s1"
        q_cuboid = _clean_quote(raw, ca + m_cuboid.start(), ca + m_cuboid.end("not"))
        builder.solids.append({"solid_id": sid, "solid_type": "prism", "notation": not_str, "quote": q_cuboid})
        builder.simulation_goals.append(
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": sid, "quote": q_cuboid}
        )
        builder.premises.extend(
            [
                {"kind": "right_prism", "args": {"base": base_pts, "top": top_pts}, "quote": q_cuboid, "solid_id": sid},
                {"kind": "rectangle", "args": {"vertices": base_pts}, "quote": q_cuboid, "solid_id": sid},
            ]
        )
        builder._primary_solid_id = sid
        builder._primary_solid_type = "prism"
        builder._primary_notation = not_str
        mapped_fact = True

    # 1f. Prism (right, regular, or oblique): "Cho (hình |khối )?lăng trụ (đứng|đều|xiên)? ABC.A'B'C'"
    m_prism = re.search(
        rf"(?P<lead>(?:Cho|Vẽ|Mô\s+phỏng)\s+)?(?:(?:hình|khối)\s+)?lăng\s+trụ(?:\s+(?P<mod>đứng|đều|tam\s+giác\s+đều|tứ\s+giác\s+đều|xiên))?\s+(?P<not>{_PTS3_6}\.{_PTS3_6})",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_prism and not builder.solids:
        clause_solid_not_span = (m_prism.start("not"), m_prism.end("not"))
        not_str = m_prism.group("not")
        b_str, t_str = not_str.split(".", 1)
        base_pts, top_pts = _split_pts(b_str), _split_pts(t_str)
        builder._base_vertices = base_pts
        q_prism = _clean_quote(raw, ca + m_prism.start(), ca + m_prism.end())
        sid = "s1"
        builder.solids.append({"solid_id": sid, "solid_type": "prism", "notation": not_str, "quote": q_prism})
        builder.simulation_goals.append(
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": sid, "quote": q_prism}
        )
        mod = (m_prism.group("mod") or "").lower()
        if "đứng" in mod or "đều" in mod:
            builder.premises.append(
                {"kind": "right_prism", "args": {"base": base_pts, "top": top_pts}, "quote": q_prism, "solid_id": sid}
            )
        builder._primary_solid_id = sid
        builder._primary_solid_type = "prism"
        builder._primary_notation = not_str
        mapped_fact = True

    # 1g. Standalone Curved Solids (Sphere, Cylinder, Cone)
    m_sph_stand = re.search(
        rf"Cho\s+mặt\s+cầu\s+tâm\s+(?P<c>{_PT})\s*,\s*điểm\s+(?P<r>{_PT})\s+thuộc\s+mặt\s+cầu\s*,\s*bán\s+kính\s+(?:bằng\s+)?(?P<rad>{_VAL})",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_sph_stand:
        q_s = _clean_quote(raw, ca + m_sph_stand.start(), ca + m_sph_stand.end())
        builder.solids.append(
            {
                "solid_id": "k",
                "solid_type": "sphere",
                "notation": m_sph_stand.group("c"),
                "center": m_sph_stand.group("c"),
                "rim_point": m_sph_stand.group("r"),
                "radius": m_sph_stand.group("rad"),
                "quote": q_s,
            }
        )
        builder.simulation_goals.append(
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "k", "quote": q_s}
        )
        builder._primary_solid_id = "k"
        builder._primary_solid_type = "sphere"
        mapped_fact = True

    m_cyl_stand = re.search(
        rf"Cho\s+hình\s+trụ\s+có\s+tâm\s+hai\s+đáy\s+là\s+(?P<c>{_PT})\s+và\s+(?P<t>{_PT})\s*,\s*điểm\s+(?P<r>{_PT})\s+thuộc\s+đường\s+tròn\s+đáy\s+tâm\s+(?P=c)\s*,\s*bán\s+kính\s+đáy\s+(?:bằng\s+)?(?P<rad>{_VAL})(?:\s+và\s+chiều\s+cao\s+(?:bằng\s+)?(?P<h>{_VAL}))?",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_cyl_stand:
        q_c = _clean_quote(raw, ca + m_cyl_stand.start(), ca + m_cyl_stand.end())
        not_c = f"{m_cyl_stand.group('c')}.{m_cyl_stand.group('t')}"
        spec_c: dict[str, Any] = {
            "solid_id": "k",
            "solid_type": "cylinder",
            "notation": not_c,
            "center": m_cyl_stand.group("c"),
            "apex_or_top": m_cyl_stand.group("t"),
            "rim_point": m_cyl_stand.group("r"),
            "radius": m_cyl_stand.group("rad"),
            "quote": q_c,
        }
        if m_cyl_stand.group("h"):
            spec_c["height"] = m_cyl_stand.group("h")
        builder.solids.append(spec_c)
        builder.simulation_goals.append(
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "k", "quote": q_c}
        )
        builder._primary_solid_id = "k"
        builder._primary_solid_type = "cylinder"
        builder._primary_notation = not_c
        mapped_fact = True

    m_cone_stand = re.search(
        rf"Cho\s+hình\s+nón\s+đỉnh\s+(?P<ap>{_PT})\s*,\s*đáy\s+là\s+đường\s+tròn\s+tâm\s+(?P<c>{_PT})\s*,\s*điểm\s+(?P<r>{_PT})\s+thuộc\s+đường\s+tròn\s+đáy\s*,\s*bán\s+kính\s+đáy\s+(?:bằng\s+)?(?P<rad>{_VAL})(?:\s+và\s+chiều\s+cao\s+(?:bằng\s+)?(?P<h>{_VAL}))?",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_cone_stand:
        q_cn = _clean_quote(raw, ca + m_cone_stand.start(), ca + m_cone_stand.end())
        not_cn = f"{m_cone_stand.group('ap')}.{m_cone_stand.group('c')}"
        spec_cn: dict[str, Any] = {
            "solid_id": "k",
            "solid_type": "cone",
            "notation": not_cn,
            "center": m_cone_stand.group("c"),
            "apex_or_top": m_cone_stand.group("ap"),
            "rim_point": m_cone_stand.group("r"),
            "radius": m_cone_stand.group("rad"),
            "quote": q_cn,
        }
        if m_cone_stand.group("h"):
            spec_cn["height"] = m_cone_stand.group("h")
        builder.solids.append(spec_cn)
        builder.simulation_goals.append(
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "k", "quote": q_cn}
        )
        builder._primary_solid_id = "k"
        builder._primary_solid_type = "cone"
        builder._primary_notation = not_cn
        mapped_fact = True

    # 1h. Inscribed / Circumscribed Spheres (`Gọi (S) là mặt cầu ...`, `Gọi I là tâm mặt cầu nội tiếp ...`)
    for m_sph_rel in re.finditer(
        rf"Gọi\s+\((?P<name>{_PT})\)\s+là\s+mặt\s+cầu(?:\s+có\s+tâm\s+(?P<center>{_PT}))?\s+(?P<rel>ngoại\s+tiếp|nội\s+tiếp)\s+(?:hình\s+chóp|khối\s+chóp|hình\s+lập\s+phương|khối\s+lập\s+phương|hình\s+lăng\s+trụ|lăng\s+trụ)\s+(?P<target>{_PT}\.{_PTS3_6}|{_PTS3_6}\.{_PTS3_6})",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        q_sr = _clean_quote(raw, ca, cb)
        sname = f"({m_sph_rel.group('name')})"
        rel_kind = "circumscribes" if "ngoại" in m_sph_rel.group("rel").lower() else "inscribed_in"
        target_not = m_sph_rel.group("target")
        target_sid = next((s["solid_id"] for s in builder.solids if s["notation"] == target_not), builder._primary_solid_id)
        sph_sid = f"sph_{len(builder.solids)}"
        sph_spec: dict[str, Any] = {
            "solid_id": sph_sid,
            "solid_type": "sphere",
            "notation": sname,
            rel_kind: target_sid,
            "quote": q_sr,
        }
        if m_sph_rel.group("center"):
            sph_spec["center"] = m_sph_rel.group("center")
            builder._sphere_center_map[m_sph_rel.group("center")] = sph_sid
        builder.solids.append(sph_spec)
        builder._sphere_by_notation[sname] = sph_sid
        mapped_fact = True

    for m_sph_ctr in re.finditer(
        rf"Gọi\s+(?P<center>{_PT})\s+là\s+tâm\s+mặt\s+cầu\s+(?P<rel>ngoại\s+tiếp|nội\s+tiếp)\s+(?:hình\s+chóp|khối\s+chóp|hình\s+lập\s+phương|hình\s+lăng\s+trụ|lăng\s+trụ)\s+(?P<target>{_PT}\.{_PTS3_6}|{_PTS3_6}\.{_PTS3_6})",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        q_sc = _clean_quote(raw, ca, cb)
        cname = m_sph_ctr.group("center")
        rel_kind = "circumscribes" if "ngoại" in m_sph_ctr.group("rel").lower() else "inscribed_in"
        target_not = m_sph_ctr.group("target")
        target_sid = next((s["solid_id"] for s in builder.solids if s["notation"] == target_not), builder._primary_solid_id)
        sph_sid = f"sph_{len(builder.solids)}"
        builder.solids.append(
            {
                "solid_id": sph_sid,
                "solid_type": "sphere",
                "notation": cname,
                "center": cname,
                rel_kind: target_sid,
                "quote": q_sc,
            }
        )
        builder._sphere_by_notation[cname] = sph_sid
        builder._sphere_center_map[cname] = sph_sid
        mapped_fact = True

    # Sphere tangent plane: "Mặt cầu (S) tiếp xúc với mặt phẳng (SBC) tại T"
    for m_tang in re.finditer(
        rf"Mặt\s+cầu\s+\((?P<sname>{_PT})\)\s+tiếp\s+xúc\s+với\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<plane>{_PTS3_6})\)\s+tại\s+(?P<pt>{_PT})",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        q_t = _clean_quote(raw, ca, cb)
        sname = f"({m_tang.group('sname')})"
        sph_sid = builder._sphere_by_notation.get(sname, "sph")
        builder.relations.append(
            {
                "relation_id": f"r_tan_{len(builder.relations) + 1}",
                "kind": "tangent_to",
                "solid_a": sph_sid,
                "solid_b": builder._primary_solid_id,
                "entity_b": _split_pts(m_tang.group("plane")),
                "contact_ref": m_tang.group("pt"),
                "quote": q_t,
            }
        )
        mapped_fact = True

    # ── 2. Base & Polygon Shape Premises ─────────────────────────────────────────────────────────────────────────
    # 2a. Square or equilateral triangle base: "đáy (ABCD )?là (hình vuông|tam giác đều|lục giác đều)( cạnh (bằng )?2)?"
    for m_reg_base in re.finditer(
        rf"(?P<full>đáy(?:\s+(?P<verts>{_PTS3_6}))?\s+là\s+(?P<shape>hình\s+vuông|tam\s+giác\s+đều|lục\s+giác\s+đều)(?:\s+cạnh\s+(?:bằng\s+)?(?P<side>{_VAL}))?)",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        verts = _split_pts(m_reg_base.group("verts")) if m_reg_base.group("verts") else list(builder._base_vertices)
        rb_start = m_reg_base.start("full")
        if (
            not m_reg_base.group("verts")
            and clause_solid_not_span is not None
            and clause_solid_not_span[1] <= rb_start
            and re.fullmatch(
                r"\s*(?:[.,]\s*)?(?:có\s+)?(?:chung\s+)?(?:mặt\s+)?",
                ctext_norm[clause_solid_not_span[1] : rb_start],
                re.IGNORECASE,
            )
        ):
            rb_start = clause_solid_not_span[0]
        q_rb = _clean_quote(raw, ca + rb_start, ca + m_reg_base.end("full"))
        side = m_reg_base.group("side")
        args_rb: dict[str, Any] = {"vertices": verts}
        if side is not None:
            args_rb["side"] = _canon_val(side)
        else:
            builder.unresolved.append(
                {
                    "unresolved_id": f"u{len(builder.unresolved) + 1}",
                    "kind": "missing_operand",
                    "quote": q_rb,
                    "missing_roles": ["dimension"],
                    "candidate_relations": [],
                }
            )
        builder.premises.append(
            {"kind": "regular_polygon", "args": args_rb, "quote": q_rb, "solid_id": builder._primary_solid_id}
        )
        mapped_fact = True

    # 2b. Rectangle base: "đáy (ABCD )?là hình chữ nhật"
    for m_rect in re.finditer(
        rf"(?P<full>đáy(?:\s+(?P<verts>{_PTS4}))?\s+là\s+hình\s+chữ\s+nhật)",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        verts = _split_pts(m_rect.group("verts")) if m_rect.group("verts") else list(builder._base_vertices)
        rc_start = m_rect.start("full")
        if (
            not m_rect.group("verts")
            and clause_solid_not_span is not None
            and clause_solid_not_span[1] <= rc_start
            and re.fullmatch(
                r"\s*(?:[.,]\s*)?(?:có\s+)?(?:chung\s+)?(?:mặt\s+)?",
                ctext_norm[clause_solid_not_span[1] : rc_start],
                re.IGNORECASE,
            )
        ):
            rc_start = clause_solid_not_span[0]
        q_rc = _clean_quote(raw, ca + rc_start, ca + m_rect.end("full"))
        builder.premises.append(
            {"kind": "rectangle", "args": {"vertices": verts}, "quote": q_rc, "solid_id": builder._primary_solid_id}
        )
        mapped_fact = True

    # 2c. Right (or right-isosceles) triangle base / named triangle:
    # "(có )?đáy (ABC )?(là tam giác (ABC )?)?vuông (cân )?tại A" or standalone "tam giác ABC vuông (cân )?tại A"
    for m_rt in re.finditer(
        rf"(?P<full>(?:(?:có\s+)?đáy(?:\s+(?P<verts>{_PTS3}))?\s+(?:là\s+tam\s+giác\s+(?:(?P<verts2>{_PTS3})\s+)?)?|tam\s+giác\s+(?P<verts3>{_PTS3})\s+)vuông(?:\s+(?P<iso>cân))?\s+tại\s+(?P<v>{_PT}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        explicit_v = m_rt.group("verts") or m_rt.group("verts2") or m_rt.group("verts3")
        verts = _split_pts(explicit_v) if explicit_v else list(builder._base_vertices)
        v = m_rt.group("v")
        rays = [p for p in verts if p != v]
        if len(rays) == 2:
            s_off = m_rt.start("full")
            if m_rt.group("verts2"):
                # "có đáy là tam giác ABC vuông tại B" -> quote "tam giác ABC vuông tại B"
                m_sub = re.search(rf"tam\s+giác\s+{re.escape(m_rt.group('verts2'))}\b", m_rt.group("full"), re.IGNORECASE)
                if m_sub:
                    s_off += m_sub.start()
            elif not explicit_v and clause_solid_not_span is not None and clause_solid_not_span[1] <= s_off:
                if re.fullmatch(
                    r"\s*(?:[.,]\s*)?(?:có\s+)?(?:chung\s+)?(?:mặt\s+)?",
                    ctext_norm[clause_solid_not_span[1] : s_off],
                    re.IGNORECASE,
                ):
                    s_off = clause_solid_not_span[0]
            elif ctext_norm[s_off : s_off + 3].lower() == "có " and "là tam giác" in m_rt.group("full").lower():
                s_off += 3
            q_rt = _clean_quote(raw, ca + s_off, ca + m_rt.end("full"))
            builder.premises.append(
                {
                    "kind": "right_angle",
                    "args": {"vertex": v, "rays": rays},
                    "quote": q_rt,
                    "solid_id": builder._primary_solid_id,
                }
            )
            if m_rt.group("iso"):
                builder.premises.append(
                    {
                        "kind": "equal_length",
                        "args": {"segment_a": [v, rays[0]], "segment_b": [v, rays[1]]},
                        "quote": q_rt,
                        "solid_id": builder._primary_solid_id,
                    }
                )
            mapped_fact = True

    # 2d. Unnamed vertex angle ambiguity ("có một góc bằng 60°") -> explicit clarification
    m_ambig_vang = re.search(
        rf"(?P<full>có\s+một\s+góc\s*(?:bằng|là|=)\s*(?P<aval>\d+(?:/\d+)?)\s*(?:°|độ\b))",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_ambig_vang:
        q_av = _clean_quote(raw, ca + m_ambig_vang.start("full"), ca + m_ambig_vang.end("full"))
        builder.unresolved.append(
            {
                "unresolved_id": f"u{len(builder.unresolved) + 1}",
                "kind": "ambiguous",
                "quote": q_av,
                "missing_roles": ["source_point"],
                "candidate_relations": ["angle"],
            }
        )
        clause.classification = CLAUSE_MAPPED_FACT
        return

    # 2e. FAMILY-1 Right trapezoid: "đáy (ABCD )?là hình thang vuông tại A và B"
    for m_rtrap in re.finditer(
        rf"(?P<full>đáy(?:\s+(?P<verts>{_PTS4}))?\s+là\s+hình\s+thang\s+vuông\s+(?:tại|ở)\s+(?P<v1>{_PT})\s*(?:và|,\s*)\s*(?P<v2>{_PT}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        verts = _split_pts(m_rtrap.group("verts")) if m_rtrap.group("verts") else list(builder._base_vertices)
        v1, v2 = m_rtrap.group("v1"), m_rtrap.group("v2")
        if len(verts) == 4 and v1 in verts and v2 in verts and v1 != v2:
            rt_start = m_rtrap.start("full")
            if (
                not m_rtrap.group("verts")
                and clause_solid_not_span is not None
                and clause_solid_not_span[1] <= rt_start
                and re.fullmatch(
                    r"\s*(?:[.,]\s*)?(?:có\s+)?(?:chung\s+)?(?:mặt\s+)?",
                    ctext_norm[clause_solid_not_span[1] : rt_start],
                    re.IGNORECASE,
                )
            ):
                rt_start = clause_solid_not_span[0]
            q_rtrap = _clean_quote(raw, ca + rt_start, ca + m_rtrap.end("full"))
            for vx in (v1, v2):
                idx_v = verts.index(vx)
                rays_v = [verts[(idx_v - 1) % 4], verts[(idx_v + 1) % 4]]
                builder.premises.append(
                    {
                        "kind": "right_angle",
                        "args": {"vertex": vx, "rays": rays_v},
                        "quote": q_rtrap,
                        "solid_id": builder._primary_solid_id,
                    }
                )
            mapped_fact = True

    # 2f. FAMILY-1 Isosceles trapezoid & general parallel-base trapezoid
    for m_trap in re.finditer(
        rf"(?P<full>đáy(?:\s+(?P<verts>{_PTS4}))?\s+là\s+hình\s+thang(?:\s+(?P<iso>cân))?\s+(?:(?:với|có)\s+hai\s+đáy(?:\s+là)?\s+(?P<ba1>{_PTS2})\s*(?:và|,\s*)\s*(?P<bb1>{_PTS2})|(?:có\s+)?(?P<ba2>{_PTS2})\s*(?:song\s+song(?:\s+với)?|//|∥)\s*(?P<bb2>{_PTS2})))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        verts = _split_pts(m_trap.group("verts")) if m_trap.group("verts") else list(builder._base_vertices)
        ba = _split_pts(m_trap.group("ba1") or m_trap.group("ba2"))
        bb = _split_pts(m_trap.group("bb1") or m_trap.group("bb2"))
        if len(verts) == 4 and len(ba) == 2 and len(bb) == 2:
            tr_start = m_trap.start("full")
            if (
                not m_trap.group("verts")
                and clause_solid_not_span is not None
                and clause_solid_not_span[1] <= tr_start
                and re.fullmatch(
                    r"\s*(?:[.,]\s*)?(?:có\s+)?(?:chung\s+)?(?:mặt\s+)?",
                    ctext_norm[clause_solid_not_span[1] : tr_start],
                    re.IGNORECASE,
                )
            ):
                tr_start = clause_solid_not_span[0]
            q_trap = _clean_quote(raw, ca + tr_start, ca + m_trap.end("full"))
            builder.premises.append(
                {
                    "kind": "isosceles_trapezoid" if m_trap.group("iso") else "trapezoid",
                    "args": {"vertices": verts, "base_a": ba, "base_b": bb},
                    "quote": q_trap,
                    "solid_id": builder._primary_solid_id,
                }
            )
            mapped_fact = True

    # 2g. FAMILY-1 Isosceles triangle ("đáy (ABC )?là tam giác cân tại A" / "tam giác ABC cân tại A")
    for m_iso_tri in re.finditer(
        rf"(?P<full>(?:(?:có\s+)?đáy(?:\s+(?P<verts>{_PTS3}))?\s+(?:là\s+tam\s+giác\s+(?:(?P<verts2>{_PTS3})\s+)?)?|tam\s+giác\s+(?P<verts3>{_PTS3})\s+)(?<!vuông\s)cân\s+(?:tại|ở)\s+(?P<v>{_PT}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        explicit_v = m_iso_tri.group("verts") or m_iso_tri.group("verts2") or m_iso_tri.group("verts3")
        verts = _split_pts(explicit_v) if explicit_v else list(builder._base_vertices)
        v = m_iso_tri.group("v")
        rays = [p for p in verts if p != v]
        if len(rays) == 2:
            s_off = m_iso_tri.start("full")
            if m_iso_tri.group("verts2"):
                m_sub = re.search(rf"tam\s+giác\s+{re.escape(m_iso_tri.group('verts2'))}\b", m_iso_tri.group("full"), re.IGNORECASE)
                if m_sub:
                    s_off += m_sub.start()
            elif not explicit_v and clause_solid_not_span is not None and clause_solid_not_span[1] <= s_off:
                if re.fullmatch(
                    r"\s*(?:[.,]\s*)?(?:có\s+)?(?:chung\s+)?(?:mặt\s+)?",
                    ctext_norm[clause_solid_not_span[1] : s_off],
                    re.IGNORECASE,
                ):
                    s_off = clause_solid_not_span[0]
            elif ctext_norm[s_off : s_off + 3].lower() == "có " and "là tam giác" in m_iso_tri.group("full").lower():
                s_off += 3
            q_iso = _clean_quote(raw, ca + s_off, ca + m_iso_tri.end("full"))
            builder.premises.append(
                {
                    "kind": "equal_length",
                    "args": {"segment_a": [v, rays[0]], "segment_b": [v, rays[1]]},
                    "quote": q_iso,
                    "solid_id": builder._primary_solid_id,
                }
            )
            mapped_fact = True

    # 2h. FAMILY-2 Rhombus & Parallelogram ("đáy (ABCD )?là hình thoi( cạnh a)?" / "đáy (ABCD )?là hình bình hành")
    for m_rhom in re.finditer(
        rf"(?P<full>đáy(?:\s+(?P<verts>{_PTS4}))?\s+là\s+hình\s+thoi(?:\s+cạnh\s+(?:bằng\s+)?(?P<side>{_VAL}))?)",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        verts = _split_pts(m_rhom.group("verts")) if m_rhom.group("verts") else list(builder._base_vertices)
        if len(verts) == 4:
            rh_start = m_rhom.start("full")
            if (
                not m_rhom.group("verts")
                and clause_solid_not_span is not None
                and clause_solid_not_span[1] <= rh_start
                and re.fullmatch(
                    r"\s*(?:[.,]\s*)?(?:có\s+)?(?:chung\s+)?(?:mặt\s+)?",
                    ctext_norm[clause_solid_not_span[1] : rh_start],
                    re.IGNORECASE,
                )
            ):
                rh_start = clause_solid_not_span[0]
            q_rh = _clean_quote(raw, ca + rh_start, ca + m_rhom.end("full"))
            args_rh: dict[str, Any] = {"vertices": verts}
            if m_rhom.group("side") is not None:
                args_rh["side"] = _canon_val(m_rhom.group("side"))
            builder.premises.append(
                {"kind": "rhombus", "args": args_rh, "quote": q_rh, "solid_id": builder._primary_solid_id}
            )
            mapped_fact = True

    for m_para in re.finditer(
        rf"(?P<full>đáy(?:\s+(?P<verts>{_PTS4}))?\s+là\s+hình\s+bình\s+hành)",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        verts = _split_pts(m_para.group("verts")) if m_para.group("verts") else list(builder._base_vertices)
        if len(verts) == 4:
            pa_start = m_para.start("full")
            if (
                not m_para.group("verts")
                and clause_solid_not_span is not None
                and clause_solid_not_span[1] <= pa_start
                and re.fullmatch(
                    r"\s*(?:[.,]\s*)?(?:có\s+)?(?:chung\s+)?(?:mặt\s+)?",
                    ctext_norm[clause_solid_not_span[1] : pa_start],
                    re.IGNORECASE,
                )
            ):
                pa_start = clause_solid_not_span[0]
            q_pa = _clean_quote(raw, ca + pa_start, ca + m_para.end("full"))
            builder.premises.append(
                {"kind": "parallelogram", "args": {"vertices": verts}, "quote": q_pa, "solid_id": builder._primary_solid_id}
            )
            mapped_fact = True

    # ── 3. Perpendicularity & Altitude Premises ──────────────────────────────────────────────────────────────────
    # 3a. Pairwise perpendicular edges from apex: "OA, OB, OC đôi một vuông góc (với nhau)?"
    for m_pair_perp in re.finditer(
        rf"(?P<full>(?P<e1>{_PTS2})\s*,\s*(?P<e2>{_PTS2})\s*,\s*(?P<e3>{_PTS2})\s+đôi\s+một\s+vuông\s+góc(?:\s+với\s+nhau)?)",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        q_pp = _clean_quote(raw, ca + m_pair_perp.start("full"), ca + m_pair_perp.end("full"))
        e1 = _split_pts(m_pair_perp.group("e1"))
        e2 = _split_pts(m_pair_perp.group("e2"))
        e3 = _split_pts(m_pair_perp.group("e3"))
        for la, lb in ((e1, e2), (e1, e3), (e2, e3)):
            builder.premises.append(
                {
                    "kind": "perpendicular_lines",
                    "args": {"line1": la, "line2": lb},
                    "quote": q_pp,
                    "solid_id": builder._primary_solid_id,
                }
            )
        mapped_fact = True

    # 3b. Line perpendicular to plane: "(cạnh bên )?SA (vuông góc (với )?|⊥ )((mặt phẳng )?(ABCD)|mặt phẳng đáy|đáy)"
    for m_lpp in re.finditer(
        rf"(?P<full>(?:(?:Biết|Cạnh(?:\s+bên)?)\s+)?(?P<line>{_PTS2})\s*(?:vuông\s+góc(?:\s+với)?|⊥)\s*(?P<target>(?:mặt\s+phẳng\s+|mp\s*)?\((?P<plane>{_PTS3_6})\)|mặt\s+phẳng\s+đáy|mặt\s+đáy|đáy))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        line_pts = _split_pts(m_lpp.group("line"))
        plane_pts = (
            _split_pts(m_lpp.group("plane")) if m_lpp.group("plane") else list(builder._base_vertices)
        )
        if len(line_pts) == 2 and len(plane_pts) >= 3:
            # Determine target solid_id (e.g., if T.ABCD is s2 and line is TA)
            sid = builder._primary_solid_id
            for s in builder.solids:
                if s["solid_type"] == "pyramid" and s["notation"].split(".", 1)[0] in line_pts:
                    sid = s["solid_id"]
                    break
            # Strip leading "cạnh bên " if not "Biết "/"Cạnh PA"
            s_off = m_lpp.start("full")
            m_lead_cb = re.match(r"cạnh\s+bên\s+", ctext_norm[s_off : m_lpp.end("full")], re.IGNORECASE)
            if m_lead_cb:
                s_off += m_lead_cb.end()
            q_lpp = _clean_quote(raw, ca + s_off, ca + m_lpp.end("full"))
            builder.premises.append(
                {
                    "kind": "perpendicular_line_plane",
                    "args": {"line": line_pts, "plane": plane_pts},
                    "quote": q_lpp,
                    "solid_id": sid,
                }
            )
            mapped_fact = True

    # 3c. Line perpendicular to line: "SA vuông góc với SB" / "SA ⊥ BC"
    for m_lpl in re.finditer(
        rf"(?P<full>(?<![\w'.(])(?P<l1>{_PTS2})\s*(?:vuông\s+góc(?:\s+với)?|⊥)\s*(?:đường\s+thẳng\s+|cạnh\s+)?(?P<l2>{_PTS2}))(?![\w')])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        q_lpl = _clean_quote(raw, ca + m_lpl.start("full"), ca + m_lpl.end("full"))
        builder.premises.append(
            {
                "kind": "perpendicular_lines",
                "args": {"line1": _split_pts(m_lpl.group("l1")), "line2": _split_pts(m_lpl.group("l2"))},
                "quote": q_lpl,
                "solid_id": builder._primary_solid_id,
            }
        )
        mapped_fact = True

    # 3d-0. FAMILY-1 Triangle altitude: "(đường cao|chiều cao) AH của tam giác ABC (bằng|=) 4a"
    for m_tri_alt in re.finditer(
        rf"(?P<full>(?:đường|chiều)\s+cao\s+(?P<seg>{_PTS2})\s+của\s+(?:tam\s+giác|[Δ∆△])\s*(?P<tri>{_PTS3})\s*(?:=|bằng|là)\s*(?P<val>{_VAL}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        seg_pts = _split_pts(m_tri_alt.group("seg"))
        tri_pts = _split_pts(m_tri_alt.group("tri"))
        if len(set(seg_pts)) == 2 and len(set(tri_pts)) == 3:
            if seg_pts[0] in tri_pts and seg_pts[1] not in tri_pts:
                v_pt, h_pt = seg_pts[0], seg_pts[1]
            elif seg_pts[1] in tri_pts and seg_pts[0] not in tri_pts:
                v_pt, h_pt = seg_pts[1], seg_pts[0]
            else:
                continue
            opp_line = [p for p in tri_pts if p != v_pt]
            q_ta = _clean_quote(raw, ca + m_tri_alt.start("full"), ca + m_tri_alt.end("full"))
            builder.premises.append(
                {
                    "kind": "orthogonal_projection_line",
                    "args": {"point": v_pt, "line": opp_line, "image": h_pt},
                    "quote": q_ta,
                    "solid_id": builder._primary_solid_id,
                }
            )
            builder.premises.append(
                {
                    "kind": "segment_length",
                    "args": {"segment": [v_pt, h_pt], "value": _canon_val(m_tri_alt.group("val"))},
                    "quote": q_ta,
                    "solid_id": builder._primary_solid_id,
                }
            )
            mapped_fact = True

    # 3d. Altitude shorthand: "đường cao SA = 2"
    for m_alt in re.finditer(
        rf"(?P<full>đường\s+cao\s+(?P<seg>{_PTS2})\s*=\s*(?P<val>{_VAL}))",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        seg_pts = _split_pts(m_alt.group("seg"))
        q_alt = _clean_quote(raw, ca, ca + m_alt.end("seg"))
        q_len = _clean_quote(raw, ca + m_alt.start("seg"), ca + m_alt.end("full"))
        builder.premises.append(
            {
                "kind": "altitude",
                "args": {"apex": seg_pts[0], "foot": seg_pts[1]},
                "quote": q_alt,
                "solid_id": builder._primary_solid_id,
            }
        )
        builder.premises.append(
            {
                "kind": "segment_length",
                "args": {"segment": seg_pts, "value": m_alt.group("val")},
                "quote": q_len,
                "solid_id": builder._primary_solid_id,
            }
        )
        mapped_fact = True

    # 3e. Exact Angle Premises (`line_plane_angle`, `plane_plane_angle`, `dihedral_angle`, `line_line_angle`, `vertex_angle`)
    m_ambig_dihedral = re.search(
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:số\s+đo\s+)?góc\s+nhị\s+diện\s+(?:theo\s+)?cạnh\s+(?P<edge>{_PTS2})\s*(?:bằng|là|=)\s*(?P<aval>\d+(?:/\d+)?)\s*(?:°|độ\b))",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_ambig_dihedral:
        q_ad = _clean_quote(raw, ca + m_ambig_dihedral.start("full"), ca + m_ambig_dihedral.end("full"))
        builder.unresolved.append(
            {
                "unresolved_id": f"u{len(builder.unresolved) + 1}",
                "kind": "ambiguous",
                "quote": q_ad,
                "missing_roles": ["target_line_or_plane"],
                "candidate_relations": ["angle"],
            }
        )
        clause.classification = CLAUSE_MAPPED_FACT
        return

    for m_dih in re.finditer(
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:số\s+đo\s+)?góc\s+nhị\s+diện\s+\[\s*(?P<pa>{_PT})\s*,\s*(?P<edge>{_PTS2})\s*,\s*(?P<pb>{_PT})\s*\]\s*(?:bằng|là|=)\s*(?P<aval>\d+(?:/\d+)?)\s*(?:°|độ\b))",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        q_dih = _clean_quote(raw, ca + m_dih.start("full"), ca + m_dih.end("full"))
        builder.premises.append(
            {
                "kind": "dihedral_angle",
                "args": {
                    "point_a": m_dih.group("pa"),
                    "edge": _split_pts(m_dih.group("edge")),
                    "point_b": m_dih.group("pb"),
                    "value": m_dih.group("aval"),
                    "unit": "deg",
                },
                "quote": q_dih,
                "solid_id": builder._primary_solid_id,
            }
        )
        angle_spans.append((m_dih.start("full"), m_dih.end("full")))
        mapped_fact = True

    matched_plural_lpa = False
    for m_pl_lpa in re.finditer(
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?các\s+cạnh\s+bên(?:\s+(?P<elist>{_PTS2}(?:\s*(?:,\s*|\s+và\s+){_PTS2})+))?\s+cùng\s+(?:tạo|hợp)\s+với\s+(?:(?:mặt\s+phẳng\s+|mp\s*)?\((?P<pl>{_PTS3_6})\)|(?:mặt\s+phẳng\s+đáy|mặt\s+đáy|đáy)(?:\s*\((?P<pld>{_PTS3_6})\))?)\s+(?:một\s+)?góc(?:\s+(?:bằng|là|=))?\s*(?P<aval>\d+(?:/\d+)?)\s*(?:°|độ\b))",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        pl_s = m_pl_lpa.group("pl") or m_pl_lpa.group("pld")
        plane_pts = _split_pts(pl_s) if pl_s else list(builder._base_vertices)
        edges_pts: list[list[str]] = []
        if m_pl_lpa.group("elist"):
            edges_pts = [_split_pts(tok) for tok in re.findall(_PTS2, m_pl_lpa.group("elist"))]
        elif builder._primary_solid_type == "pyramid" and builder._primary_notation and "." in builder._primary_notation:
            ap = builder._primary_notation.split(".", 1)[0]
            edges_pts = [[ap, bv] for bv in builder._base_vertices]
        if len(plane_pts) >= 3 and edges_pts:
            q_plpa = _clean_quote(raw, ca + m_pl_lpa.start("full"), ca + m_pl_lpa.end("full"))
            for ed in edges_pts:
                builder.premises.append(
                    {
                        "kind": "line_plane_angle",
                        "args": {"line": ed, "plane": plane_pts, "value": m_pl_lpa.group("aval"), "unit": "deg"},
                        "quote": q_plpa,
                        "solid_id": builder._primary_solid_id,
                    }
                )
            angle_spans.append((m_pl_lpa.start("full"), m_pl_lpa.end("full")))
            mapped_fact = True
            matched_plural_lpa = True

    if not matched_plural_lpa:
        for lpa_pat in (
            rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:số\s+đo\s+)?góc\s+(?:giữa|tạo\s+bởi|hợp\s+bởi)\s+(?:đường\s+thẳng\s+|cạnh\s+bên\s+|cạnh\s+|đoạn(?:\s+thẳng)?\s+)?(?P<ln>{_PTS2})\s+(?:và|với)\s+(?:(?:mặt\s+phẳng\s+|mặt\s+bên\s+|mp\s*)?\((?P<pl>{_PTS3_6})\)|(?:mặt\s+phẳng\s+đáy|mặt\s+đáy|đáy)(?:\s*\((?P<pld>{_PTS3_6})\))?)\s*(?:bằng|là|=)\s*(?P<aval>\d+(?:/\d+)?)\s*(?:°|độ\b))",
            rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:đường\s+thẳng\s+|cạnh\s+bên\s+|cạnh\s+|đoạn(?:\s+thẳng)?\s+)?(?<![\w'.(])(?P<ln>{_PTS2})\s+(?:tạo|hợp)\s+với\s+(?:(?:mặt\s+phẳng\s+|mặt\s+bên\s+|mp\s*)?\((?P<pl>{_PTS3_6})\)|(?:mặt\s+phẳng\s+đáy|mặt\s+đáy|đáy)(?:\s*\((?P<pld>{_PTS3_6})\))?)\s+(?:một\s+)?góc(?:\s+(?:bằng|là|=))?\s*(?P<aval>\d+(?:/\d+)?)\s*(?:°|độ\b))",
        ):
            for m_lpa in re.finditer(lpa_pat, ctext_norm, re.IGNORECASE | re.UNICODE):
                if any(a <= m_lpa.start("full") < b for a, b in angle_spans):
                    continue
                pl_s = m_lpa.group("pl") or m_lpa.group("pld")
                plane_pts = _split_pts(pl_s) if pl_s else list(builder._base_vertices)
                line_pts = _split_pts(m_lpa.group("ln"))
                if len(line_pts) == 2 and len(plane_pts) >= 3:
                    sid_lpa = builder._primary_solid_id
                    for s_cand in builder.solids:
                        if s_cand["solid_type"] == "pyramid" and s_cand["notation"].split(".", 1)[0] in line_pts:
                            sid_lpa = s_cand["solid_id"]
                            break
                    q_lpa = _clean_quote(raw, ca + m_lpa.start("full"), ca + m_lpa.end("full"))
                    builder.premises.append(
                        {
                            "kind": "line_plane_angle",
                            "args": {
                                "line": line_pts,
                                "plane": plane_pts,
                                "value": m_lpa.group("aval"),
                                "unit": "deg",
                            },
                            "quote": q_lpa,
                            "solid_id": sid_lpa,
                        }
                    )
                    angle_spans.append((m_lpa.start("full"), m_lpa.end("full")))
                    mapped_fact = True

    for ppa_pat in (
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:số\s+đo\s+)?góc\s+(?:giữa|tạo\s+bởi|hợp\s+bởi)\s+(?:hai\s+mặt\s+phẳng\s+|mặt\s+phẳng\s+|mặt\s+bên\s+|mp\s*)?\((?P<p1>{_PTS3_6})\)\s+(?:và|với)\s+(?:(?:mặt\s+phẳng\s+|mặt\s+bên\s+|mp\s*)?\((?P<p2>{_PTS3_6})\)|(?:mặt\s+phẳng\s+đáy|mặt\s+đáy|đáy)(?:\s*\((?P<p2d>{_PTS3_6})\))?)\s*(?:bằng|là|=)\s*(?P<aval>\d+(?:/\d+)?)\s*(?:°|độ\b))",
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:mặt\s+bên\s+|mặt\s+phẳng\s+|mp\s*)?\((?P<p1>{_PTS3_6})\)\s+(?:tạo|hợp)\s+với\s+(?:(?:mặt\s+phẳng\s+|mặt\s+bên\s+|mp\s*)?\((?P<p2>{_PTS3_6})\)|(?:mặt\s+phẳng\s+đáy|mặt\s+đáy|đáy)(?:\s*\((?P<p2d>{_PTS3_6})\))?)\s+(?:một\s+)?góc(?:\s+(?:bằng|là|=))?\s*(?P<aval>\d+(?:/\d+)?)\s*(?:°|độ\b))",
    ):
        for m_ppa in re.finditer(ppa_pat, ctext_norm, re.IGNORECASE | re.UNICODE):
            if any(a <= m_ppa.start("full") < b for a, b in angle_spans):
                continue
            p1_pts = _split_pts(m_ppa.group("p1"))
            p2_s = m_ppa.group("p2") or m_ppa.group("p2d")
            p2_pts = _split_pts(p2_s) if p2_s else list(builder._base_vertices)
            if len(p1_pts) >= 3 and len(p2_pts) >= 3:
                q_ppa = _clean_quote(raw, ca + m_ppa.start("full"), ca + m_ppa.end("full"))
                builder.premises.append(
                    {
                        "kind": "plane_plane_angle",
                        "args": {
                            "plane1": p1_pts,
                            "plane2": p2_pts,
                            "value": m_ppa.group("aval"),
                            "unit": "deg",
                        },
                        "quote": q_ppa,
                        "solid_id": builder._primary_solid_id,
                    }
                )
                angle_spans.append((m_ppa.start("full"), m_ppa.end("full")))
                mapped_fact = True

    for lla_pat in (
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:số\s+đo\s+)?góc\s+(?:giữa|tạo\s+bởi|hợp\s+bởi)\s+(?:hai\s+đường\s+thẳng\s+|đường\s+thẳng\s+|cạnh\s+)?(?P<l1>{_PTS2})\s+(?:và|với)\s+(?:đường\s+thẳng\s+|cạnh\s+)?(?P<l2>{_PTS2})\s*(?:bằng|là|=)\s*(?P<aval>\d+(?:/\d+)?)\s*(?:°|độ\b))",
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:đường\s+thẳng\s+|cạnh\s+)?(?<![\w'.(])(?P<l1>{_PTS2})\s+(?:tạo|hợp)\s+với\s+(?:đường\s+thẳng\s+|cạnh\s+)?(?P<l2>{_PTS2})(?![\w')])\s+(?:một\s+)?góc(?:\s+(?:bằng|là|=))?\s*(?P<aval>\d+(?:/\d+)?)\s*(?:°|độ\b))",
    ):
        for m_lla in re.finditer(lla_pat, ctext_norm, re.IGNORECASE | re.UNICODE):
            if any(a <= m_lla.start("full") < b for a, b in angle_spans):
                continue
            q_lla = _clean_quote(raw, ca + m_lla.start("full"), ca + m_lla.end("full"))
            builder.premises.append(
                {
                    "kind": "line_line_angle",
                    "args": {
                        "line1": _split_pts(m_lla.group("l1")),
                        "line2": _split_pts(m_lla.group("l2")),
                        "value": m_lla.group("aval"),
                        "unit": "deg",
                    },
                    "quote": q_lla,
                    "solid_id": builder._primary_solid_id,
                }
            )
            angle_spans.append((m_lla.start("full"), m_lla.end("full")))
            mapped_fact = True

    for m_vang in re.finditer(
        rf"(?P<full>(?:góc\s+|[∠^]\s*)(?P<p3>{_PTS3})(?![\w'])\s*(?:bằng|là|=)\s*(?P<aval>\d+(?:/\d+)?)\s*(?:°|độ\b))",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        if any(a <= m_vang.start("full") < b for a, b in angle_spans):
            continue
        pts3 = _split_pts(m_vang.group("p3"))
        if len(pts3) == 3 and len(set(pts3)) == 3:
            q_vang = _clean_quote(raw, ca + m_vang.start("full"), ca + m_vang.end("full"))
            builder.premises.append(
                {
                    "kind": "vertex_angle",
                    "args": {
                        "vertex": pts3[1],
                        "rays": [pts3[0], pts3[2]],
                        "value": m_vang.group("aval"),
                        "unit": "deg",
                    },
                    "quote": q_vang,
                    "solid_id": builder._primary_solid_id,
                }
            )
            angle_spans.append((m_vang.start("full"), m_vang.end("full")))
            mapped_fact = True

    # ── 4. Segment Length Assignments (single and chained `SA = SB = SC = 13/2`) ────────────────────────────────
    for m_chain_eq in re.finditer(
        rf"(?P<full>(?<![\w'.])(?P<s1>{_PTS2})\s*=\s*(?P<s2>{_PTS2})(?:\s*=\s*(?P<s3>{_PTS2}))?\s*=\s*(?P<val>{_VAL}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        q_ch = _clean_quote(raw, ca + m_chain_eq.start("full"), ca + m_chain_eq.end("full"))
        val = _canon_val(m_chain_eq.group("val"))
        for gname in ("s1", "s2", "s3"):
            seg_s = m_chain_eq.group(gname)
            if seg_s:
                builder.premises.append(
                    {
                        "kind": "segment_length",
                        "args": {"segment": _split_pts(seg_s), "value": val},
                        "quote": q_ch,
                        "solid_id": builder._primary_solid_id,
                    }
                )
        mapped_fact = True

    # Single segment lengths (`AB = 3`, `Đường sinh SA = 3`), skipping those already inside a chain or `đường cao SA = 2`
    for m_seg_len in re.finditer(
        rf"(?P<full>(?:Đường\s+sinh\s+)?(?<![\w'.])(?P<seg>{_PTS2})\s*=\s*(?P<val>{_VAL}))(?![\s]*=)(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        # Skip if preceded by `= ` or `đường cao ` or followed by a segment token (e.g. `SM = 1/3 SA`)
        prefix_slice = ctext_norm[: m_seg_len.start("full")].rstrip()
        suffix_slice = ctext_norm[m_seg_len.end("full") :]
        if (
            prefix_slice.endswith("=")
            or re.search(r"(?:đường\s+cao|chiều\s+cao)$", prefix_slice, re.IGNORECASE)
            or re.match(rf"^\s*{_PTS2}(?![\w'])", suffix_slice)
        ):
            continue
        seg_pts = _split_pts(m_seg_len.group("seg"))
        val = _canon_val(m_seg_len.group("val"))
        q_sl = _clean_quote(raw, ca + m_seg_len.start("full"), ca + m_seg_len.end("full"))
        sid = builder._primary_solid_id
        for s in builder.solids:
            if s["solid_type"] == "pyramid" and s["notation"].split(".", 1)[0] in seg_pts:
                sid = s["solid_id"]
                break
        builder.premises.append(
            {"kind": "segment_length", "args": {"segment": seg_pts, "value": val}, "quote": q_sl, "solid_id": sid}
        )
        mapped_fact = True

    # ── 5. Explicit Point Constructions (Midpoint, Centroid, Projection, Intersection) ───────────────────────────
    # 5a. Paired or triple midpoints: "Gọi M, N(, P)? lần lượt là trung điểm của SA, SB(, SC)?"
    matched_mp_list = False
    for m_mp_list in re.finditer(
        rf"(?P<full>Gọi\s+(?P<p1>{_PT})\s*[,;]\s*(?P<p2>{_PT})(?:\s*[,;]\s*(?P<p3>{_PT}))?\s+lần\s+lượt\s+là\s+trung\s+điểm\s+của(?:\s+các\s+cạnh)?\s+(?P<s1>{_PTS2})\s*(?:[,;]\s*|\s+và\s+)(?P<s2>{_PTS2})(?:\s*(?:[,;]\s*|\s+và\s+)(?P<s3>{_PTS2}))?)",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        q_mpl = _clean_quote(raw, ca + m_mp_list.start("full"), ca + m_mp_list.end("full"))
        pairs = [(m_mp_list.group("p1"), m_mp_list.group("s1")), (m_mp_list.group("p2"), m_mp_list.group("s2"))]
        if m_mp_list.group("p3") and m_mp_list.group("s3"):
            pairs.append((m_mp_list.group("p3"), m_mp_list.group("s3")))
        for pt_s, seg_s in pairs:
            builder.premises.append(
                {
                    "kind": "midpoint",
                    "args": {"point": pt_s, "segment": _split_pts(seg_s)},
                    "quote": q_mpl,
                    "solid_id": builder._primary_solid_id,
                }
            )
        mapped_fact = True
        matched_mp_list = True

    # 5b. Single midpoint: "(Gọi )?M là trung điểm (của )?(cạnh )?SA"
    if not matched_mp_list:
        for m_mp1 in re.finditer(
            rf"(?P<full>(?:Gọi\s+)?(?<![\w'])(?P<pt>{_PT})\s+là\s+trung\s+điểm(?:\s+của)?(?:\s+cạnh|\s+đoạn(?:\s+thẳng)?)?\s+(?P<seg>{_PTS2}))(?![\w'])",
            ctext_norm,
            re.IGNORECASE | re.UNICODE,
        ):
            if not m_mp1.group("pt")[0].isupper():
                continue
            q_mp1 = _clean_quote(raw, ca + m_mp1.start("full"), ca + m_mp1.end("full"))
            builder.premises.append(
                {
                    "kind": "midpoint",
                    "args": {"point": m_mp1.group("pt"), "segment": _split_pts(m_mp1.group("seg"))},
                    "quote": q_mp1,
                    "solid_id": builder._primary_solid_id,
                }
            )
            mapped_fact = True

    # 5b-2. Point divides segment: "(Gọi |Điểm )?M (là điểm )?thuộc (cạnh )?SA sao cho SM = 1/3 SA"
    for m_div in re.finditer(
        rf"(?P<full>(?:Gọi\s+|Điểm\s+)?(?<![\w'])(?P<pt>{_PT})\s+(?:là\s+điểm\s+)?thuộc\s+(?:cạnh\s+|đoạn(?:\s+thẳng)?\s+)?(?P<seg>{_PTS2})\s+(?:sao\s+cho|thỏa\s+mãn)\s+(?P<subseg>{_PTS2})\s*=\s*(?P<rat>\d+\s*/\s*\d+)\s*(?P<seg2>{_PTS2}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        pt_d = m_div.group("pt")
        if not pt_d[0].isupper():
            continue
        q_div = _clean_quote(raw, ca + m_div.start("full"), ca + m_div.end("full"))
        builder.premises.append(
            {
                "kind": "point_divides_segment",
                "args": {
                    "point": pt_d,
                    "segment": _split_pts(m_div.group("seg")),
                    "ratio": re.sub(r"\s+", "", m_div.group("rat")),
                },
                "quote": q_div,
                "solid_id": builder._primary_solid_id,
            }
        )
        mapped_fact = True

    # 5b-3. Internal division by a part-to-part ratio: "(Gọi )?E (là điểm )?thuộc (cạnh )?SC sao cho SE = 3EC"
    # The two parts must be [end, point] and [point, other end] of the stated segment; t = AP/AB = k/(k + 1).
    for m_dv2 in re.finditer(
        rf"(?P<full>(?:Gọi\s+|Điểm\s+)?(?<![\w'])(?P<pt>{_PT})\s+(?:là\s+(?:một\s+)?điểm\s+)?(?:thuộc|nằm\s+trên)\s+(?:cạnh\s+|đoạn(?:\s+thẳng)?\s+)?(?P<seg>{_PTS2})\s+(?:sao\s+cho|thỏa\s+mãn)\s+(?P<p1>{_PTS2})\s*=\s*(?P<k>\d+(?:\s*/\s*\d+)?)\s*(?P<p2>{_PTS2}))(?![\w'/])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        pt_v = m_dv2.group("pt")
        seg_v = _split_pts(m_dv2.group("seg"))
        p1_v, p2_v = _split_pts(m_dv2.group("p1")), _split_pts(m_dv2.group("p2"))
        if not pt_v[0].isupper() or len(seg_v) != 2 or len(p1_v) != 2 or len(p2_v) != 2 or pt_v in seg_v:
            continue
        a_end = next((x for x in p1_v if x != pt_v), None)
        b_end = next((x for x in p2_v if x != pt_v), None)
        if pt_v not in p1_v or pt_v not in p2_v or {a_end, b_end} != set(seg_v):
            continue
        try:
            k_v = Fraction(re.sub(r"\s+", "", m_dv2.group("k")))
        except (ValueError, ZeroDivisionError):
            continue
        if k_v <= 0:
            continue
        t_v = k_v / (k_v + 1)
        q_dv2 = _clean_quote(raw, ca + m_dv2.start("full"), ca + m_dv2.end("full"))
        builder.premises.append(
            {
                "kind": "point_divides_segment",
                "args": {"point": pt_v, "segment": [a_end, b_end], "ratio": f"{t_v.numerator}/{t_v.denominator}"},
                "quote": q_dv2,
                "solid_id": builder._primary_solid_id,
            }
        )
        mapped_fact = True

    # 5c. Centroid: "(Gọi )?G là trọng tâm (của )?tam giác SBC"
    for m_cen in re.finditer(
        rf"(?P<full>(?:Gọi\s+)?(?<![\w'])(?P<pt>{_PT})\s+là\s+trọng\s+tâm(?:\s+của)?\s+tam\s+giác\s+(?P<poly>{_PTS3}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        if not m_cen.group("pt")[0].isupper():
            continue
        q_cen = _clean_quote(raw, ca + m_cen.start("full"), ca + m_cen.end("full"))
        builder.premises.append(
            {
                "kind": "centroid",
                "args": {"point": m_cen.group("pt"), "polygon": _split_pts(m_cen.group("poly"))},
                "quote": q_cen,
                "solid_id": builder._primary_solid_id,
            }
        )
        mapped_fact = True

    # 5d. Paired projections onto lines: "Gọi H, K lần lượt là hình chiếu vuông góc của A lên SB, SD"
    matched_pr_list = False
    for m_pr_list in re.finditer(
        rf"(?P<full>Gọi\s+(?P<p1>{_PT})\s*[,;]\s*(?P<p2>{_PT})\s+lần\s+lượt\s+là\s+hình\s+chiếu\s+vuông\s+góc\s+của\s+(?P<src>{_PT})\s+(?:lên|trên)\s+(?P<l1>{_PTS2})\s*(?:[,;]\s*|\s+và\s+)(?P<l2>{_PTS2}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        q_prl = _clean_quote(raw, ca + m_pr_list.start("full"), ca + m_pr_list.end("full"))
        src = m_pr_list.group("src")
        for img, ln in ((m_pr_list.group("p1"), m_pr_list.group("l1")), (m_pr_list.group("p2"), m_pr_list.group("l2"))):
            builder.premises.append(
                {
                    "kind": "orthogonal_projection_line",
                    "args": {"point": src, "image": img, "line": _split_pts(ln)},
                    "quote": q_prl,
                    "solid_id": builder._primary_solid_id,
                }
            )
        mapped_fact = True
        matched_pr_list = True

    # 5e. Single projection onto line: "(Gọi )?H là hình chiếu vuông góc của A lên SB"
    if not matched_pr_list:
        for m_pr_ln in re.finditer(
            rf"(?P<full>(?:Gọi\s+)?(?<![\w'])(?P<img>{_PT})\s+là\s+hình\s+chiếu\s+vuông\s+góc\s+của\s+(?P<src>{_PT})\s+(?:lên|trên)\s+(?:đường\s+thẳng\s+|cạnh\s+)?(?P<line>{_PTS2}))(?![\w')])",
            ctext_norm,
            re.IGNORECASE | re.UNICODE,
        ):
            if not m_pr_ln.group("img")[0].isupper():
                continue
            q_pr1 = _clean_quote(raw, ca + m_pr_ln.start("full"), ca + m_pr_ln.end("full"))
            builder.premises.append(
                {
                    "kind": "orthogonal_projection_line",
                    "args": {
                        "point": m_pr_ln.group("src"),
                        "image": m_pr_ln.group("img"),
                        "line": _split_pts(m_pr_ln.group("line")),
                    },
                    "quote": q_pr1,
                    "solid_id": builder._primary_solid_id,
                }
            )
            mapped_fact = True

    # 5f. Single projection onto plane:
    # "(Gọi )?H là hình chiếu vuông góc của A' lên mặt phẳng (ABC)" OR "hình chiếu vuông góc của A' lên mặt phẳng (ABC) là H"
    for m_pr_pl in re.finditer(
        rf"(?P<full>(?:Gọi\s+)?(?<![\w'])(?P<img>{_PT})\s+là\s+hình\s+chiếu\s+vuông\s+góc\s+của\s+(?P<src>{_PT})\s+(?:lên|trên)\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<plane>{_PTS3_6})\)"
        rf"|hình\s+chiếu\s+vuông\s+góc\s+của\s+(?P<src2>{_PT})\s+(?:lên|trên)\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<plane2>{_PTS3_6})\)\s+(?:là|trùng\s+với)\s+(?P<img2>{_PT}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        src = m_pr_pl.group("src") or m_pr_pl.group("src2")
        img = m_pr_pl.group("img") or m_pr_pl.group("img2")
        if not img[0].isupper() or not src[0].isupper():
            continue
        q_prp = _clean_quote(raw, ca + m_pr_pl.start("full"), ca + m_pr_pl.end("full"))
        pl = m_pr_pl.group("plane") or m_pr_pl.group("plane2")
        builder.premises.append(
            {
                "kind": "orthogonal_projection",
                "args": {"point": src, "image": img, "plane": _split_pts(pl)},
                "quote": q_prp,
                "solid_id": builder._primary_solid_id,
            }
        )
        mapped_fact = True

    # 5g. Line-plane intersection point: "(Gọi )?I là giao điểm của AC' và mặt phẳng (A'BD)"
    for m_ilp in re.finditer(
        rf"(?P<full>(?:Gọi\s+)?(?<![\w'])(?P<pt>{_PT})\s+là\s+giao\s+điểm(?:\s+của)?\s+(?:đường\s+thẳng\s+|cạnh\s+|đường\s+chéo\s+)?(?P<line>{_PTS2})\s+(?:và|với)\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<plane>{_PTS3_6})\))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        pt_i = m_ilp.group("pt")
        if not pt_i[0].isupper():
            continue
        q_ilp = _clean_quote(raw, ca + m_ilp.start("full"), ca + m_ilp.end("full"))
        builder.premises.append(
            {
                "kind": "intersect_line_plane",
                "args": {
                    "point": pt_i,
                    "line": _split_pts(m_ilp.group("line")),
                    "plane": _split_pts(m_ilp.group("plane")),
                },
                "quote": q_ilp,
                "solid_id": builder._primary_solid_id,
            }
        )
        mapped_fact = True

    # 5h. Line-line intersection point: "(Gọi )?O là giao điểm của AC và BD"
    for m_ill in re.finditer(
        rf"(?P<full>(?:Gọi\s+)?(?<![\w'])(?P<pt>{_PT})\s+là\s+giao\s+điểm(?:\s+của)?(?:\s+hai\s+(?:đường\s+thẳng|đường\s+chéo|cạnh))?\s+(?P<l1>{_PTS2})\s+(?:và|với)\s+(?P<l2>{_PTS2}))(?![\w'(])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        pt_o = m_ill.group("pt")
        if not pt_o[0].isupper():
            continue
        q_ill = _clean_quote(raw, ca + m_ill.start("full"), ca + m_ill.end("full"))
        builder.premises.append(
            {
                "kind": "intersect_line_line",
                "args": {
                    "point": pt_o,
                    "line1": _split_pts(m_ill.group("l1")),
                    "line2": _split_pts(m_ill.group("l2")),
                },
                "quote": q_ill,
                "solid_id": builder._primary_solid_id,
            }
        )
        mapped_fact = True

    # ── 6. Cutting Planes & Sections (`derived_sections`) ────────────────────────────────────────────────────────
    # 6a. Ambiguous constrained plane ("vuông góc với một mặt bên")
    m_sec_ambig = re.search(
        rf"(?:Gọi\s+)?(?:Mặt\s+phẳng\s+)?\((?P<pname>{_PT}|[α-ω]'?)\)\s+(?:là\s+mặt\s+phẳng\s+)?(?:đi\s+qua|qua|chứa)\s+[^.?!]*?(?P<amb>vuông\s+góc\s+với\s+một\s+mặt\s+bên)",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_sec_ambig:
        q_sa = _clean_quote(raw, ca, cb)
        builder.unresolved.append(
            {
                "unresolved_id": f"u{len(builder.unresolved) + 1}",
                "kind": "ambiguous",
                "quote": q_sa,
                "missing_roles": ["target_line_or_plane"],
                "candidate_relations": ["perpendicular"],
            }
        )
        clause.classification = CLAUSE_MAPPED_FACT
        return

    # 6b. Plane parallel to base at distance on cone/cylinder:
    # "Mặt phẳng (P) song song với đáy và cách đáy một khoảng bằng 1 cắt hình nón theo một đường tròn"
    m_sec_curved = re.search(
        rf"Mặt\s+phẳng\s+\((?P<pname>{_PT}|[α-ω]'?)\)\s+song\s+song\s+với\s+đáy\s+và\s+cách\s+đáy\s+một\s+khoảng\s+(?:bằng\s+)?(?P<dist>{_VAL})\s+cắt\s+hình\s+(?:nón|trụ)\s+theo\s+một\s+đường\s+tròn",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_sec_curved:
        q_scv = _clean_quote(raw, ca + m_sec_curved.start(), ca + m_sec_curved.end())
        pname = m_sec_curved.group("pname")
        sec_id = "td"
        builder.derived_sections.append(
            {
                "section_id": sec_id,
                "plane_name": pname,
                "target_solid_id": builder._primary_solid_id,
                "plane_kind": "parallel_to_base_at_distance",
                "distance_from_base": m_sec_curved.group("dist"),
                "section_shape": "circle",
                "quote": q_scv,
            }
        )
        builder.simulation_goals.append(
            {"goal_id": f"sg{len(builder.simulation_goals) + 1}", "kind": "construct_plane_section", "target_section_id": sec_id, "quote": q_scv}
        )
        builder._section_by_plane_name[pname] = sec_id
        builder._last_section_id = sec_id
        mapped_fact = True

    # Curved subsolid division: "Mặt phẳng (P) chia hình nón thành một khối nón nhỏ đỉnh S và một khối nón cụt"
    m_div_cone = re.search(
        rf"Mặt\s+phẳng\s+\((?P<pname>{_PT}|[α-ω]'?)\)\s+chia\s+hình\s+nón\s+thành\s+một\s+khối\s+nón\s+nhỏ\s+đỉnh\s+(?P<ap>{_PT})\s+và\s+một\s+khối\s+nón\s+cụt",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_div_cone:
        q_dc = _clean_quote(raw, ca + m_div_cone.start(), ca + m_div_cone.end())
        sec_id = builder._section_by_plane_name.get(m_div_cone.group("pname"), builder._last_section_id or "td")
        builder.simulation_goals.append(
            {
                "goal_id": f"sg{len(builder.simulation_goals) + 1}",
                "kind": "construct_derived_solid",
                "derived_solid_id": "kn",
                "target_section_id": sec_id,
                "apex_ref": m_div_cone.group("ap"),
                "quote": q_dc,
            }
        )
        mapped_fact = True

    # 6c. Section through point (named or described) parallel to plane or perpendicular to line:
    m_sec_par_or_perp = re.search(
        rf"(?:(?:Gọi\s+\((?P<p1>{_PT}|[α-ω]'?)\)\s+là\s+mặt\s+phẳng|Mặt\s+phẳng\s+\((?P<p2>{_PT}|[α-ω]'?)\))\s+(?:đi\s+qua|qua|chứa)\s+(?P<thru>[^,;]+?)|Qua\s+(?P<thru2>{_PT})\s+(?:kẻ|dựng)\s+mặt\s+phẳng\s+\((?P<p3>{_PT}|[α-ω]'?)\))(?:\s*,\s*(?:và\s+)?|\s+và\s+|\s+)(?:(?P<par>song\s+song\s+với\s+(?:mặt\s+phẳng\s+|mp\s*|đáy\s*)?\((?P<pplane>{_PTS3_6})\))|(?P<perp>vuông\s+góc\s+với\s+(?:đường\s+thẳng\s+|cạnh\s+)?(?P<pline>{_PTS2})))(?P<cuts>(?:\s*,\s*(?:\([A-Za-z0-9'α-ω]+\)\s+)?|\s+(?:và\s+)?)cắt\s+.+)?",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_sec_par_or_perp:
        pname = m_sec_par_or_perp.group("p1") or m_sec_par_or_perp.group("p2") or m_sec_par_or_perp.group("p3")
        thru_str = (m_sec_par_or_perp.group("thru") or m_sec_par_or_perp.group("thru2")).strip()
        # Exclude if `thru_str` is comma-separated multiple points (which belongs to constrained plane 6d)
        if not re.fullmatch(rf"{_PT}\s*(?:,\s*{_PT})+", thru_str):
            thru_offset = m_sec_par_or_perp.start("thru") if m_sec_par_or_perp.group("thru") else m_sec_par_or_perp.start("thru2")
            thru_ref = builder.parse_point_or_described(thru_str, ca + thru_offset)
            if thru_ref:
                q_sec = _clean_quote(raw, ca + m_sec_par_or_perp.start(), ca + m_sec_par_or_perp.end())
                sec_id = "sec"
                stated_cuts: list[dict[str, Any]] = []
                cuts_str = m_sec_par_or_perp.group("cuts") or ""
                if cuts_str:
                    m_cmulti = re.search(
                        rf"cắt\s+(?:các\s+cạnh\s+)?(?P<edges>{_PTS2}(?:\s*(?:,\s*|\s+và\s+){_PTS2})*)(?:\s+(?:lần\s+lượt\s+)?tại\s+(?P<pts>{_PT}(?:\s*(?:,\s*|\s+và\s+){_PT})*))?",
                        cuts_str,
                        re.IGNORECASE | re.UNICODE,
                    )
                    if m_cmulti and len(re.findall(rf"{_PTS2}", m_cmulti.group("edges"))) >= 2 and "cắt" not in m_cmulti.group("edges").lower():
                        e_list = [
                            _split_pts(e.strip())
                            for e in re.split(r"\s*(?:,|\bvà\b)\s*", m_cmulti.group("edges"))
                            if e.strip()
                        ]
                        p_list = (
                            [
                                p.strip()
                                for p in re.split(r"\s*(?:,|\bvà\b)\s*", m_cmulti.group("pts"))
                                if p.strip()
                            ]
                            if m_cmulti.group("pts")
                            else []
                        )
                        for idx, ed in enumerate(e_list):
                            stated_cuts.append(
                                {
                                    "edge": ed,
                                    "point": p_list[idx] if idx < len(p_list) else None,
                                    "quote": q_sec,
                                }
                            )
                    else:
                        for m_c1 in re.finditer(
                            rf"cắt\s+(?P<e>{_PTS2})(?:\s+tại\s+(?P<x>{_PT}))?",
                            cuts_str,
                            re.IGNORECASE | re.UNICODE,
                        ):
                            stated_cuts.append(
                                {"edge": _split_pts(m_c1.group("e")), "point": m_c1.group("x"), "quote": q_sec}
                            )

                if m_sec_par_or_perp.group("par"):
                    pplane_pts = _split_pts(m_sec_par_or_perp.group("pplane"))
                    # Note: TypedFactNext /2 `parallel_plane` takes 3 points (e.g. ["A", "B", "C"])
                    builder.derived_sections.append(
                        {
                            "section_id": sec_id,
                            "plane_name": pname,
                            "target_solid_id": builder._primary_solid_id,
                            "plane_kind": "through_point_parallel_plane",
                            "through_point": thru_ref,
                            "parallel_plane": pplane_pts[:3],
                            "stated_intersections": stated_cuts,
                            "quote": q_sec,
                            "_start_offset": ca + m_sec_par_or_perp.start(),
                        }
                    )
                else:
                    pline_pts = _split_pts(m_sec_par_or_perp.group("pline"))
                    builder.derived_sections.append(
                        {
                            "section_id": sec_id,
                            "plane_name": pname,
                            "target_solid_id": builder._primary_solid_id,
                            "plane_kind": "through_point_perpendicular_line",
                            "through_point": thru_ref,
                            "perpendicular_line": pline_pts,
                            "stated_intersections": stated_cuts,
                            "quote": q_sec,
                            "_start_offset": ca + m_sec_par_or_perp.start(),
                        }
                    )
                builder._section_by_plane_name[pname] = sec_id
                builder._last_section_id = sec_id
                mapped_fact = True

    # Follow-up cut clause after `;`: e.g. "(α) cắt SA, SB, SC, SD lần lượt tại M, N, P, Q"
    m_followup_cuts = re.match(
        rf"^\s*(?:Mặt\s+phẳng\s+)?\((?P<pname>{_PT}|[α-ω]'?)\)\s+cắt\s+(?P<edges>{_PTS2}(?:\s*(?:,\s*|\s+và\s+){_PTS2})*)(?:\s+(?:lần\s+lượt\s+)?tại\s+(?P<pts>{_PT}(?:\s*(?:,\s*|\s+và\s+){_PT})*))?\s*$",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_followup_cuts and builder.derived_sections:
        sec_obj = builder.derived_sections[-1]
        start_off = sec_obj.get("_start_offset", ca)
        q_fc = _clean_quote(raw, start_off, cb)
        sec_obj["quote"] = q_fc
        e_list = [_split_pts(e.strip()) for e in re.split(r"\s*(?:,|\bvà\b)\s*", m_followup_cuts.group("edges")) if e.strip()]
        p_list = (
            [p.strip() for p in re.split(r"\s*(?:,|\bvà\b)\s*", m_followup_cuts.group("pts")) if p.strip()]
            if m_followup_cuts.group("pts")
            else []
        )
        for idx, ed in enumerate(e_list):
            sec_obj["stated_intersections"].append(
                {"edge": ed, "point": p_list[idx] if idx < len(p_list) else None, "quote": q_fc}
            )
        mapped_fact = True

    # 6d. Constrained plane (`plane_kind="constrained"`):
    # - "Mặt phẳng (Q) đi qua M, N, P"
    # - "Mặt phẳng (P) đi qua A, B(, C)? và vuông góc với (SCD)"
    # - "Mặt phẳng (P) chứa AB' và song song với BC"
    m_sec_con = re.search(
        rf"(?:Gọi\s+\((?P<p1>{_PT}|[α-ω]'?)\)\s+là\s+mặt\s+phẳng|Mặt\s+phẳng\s+\((?P<p2>{_PT}|[α-ω]'?)\))\s+(?:đi\s+qua|qua|chứa)\s+(?P<pts>{_PT}\s*(?:,\s*{_PT})+|{_PTS2})(?:\s+và\s+(?:(?P<perp>vuông\s+góc\s+với\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<pplane>{_PTS3_6})\))|(?P<par>song\s+song\s+với\s+(?:đường\s+thẳng\s+|cạnh\s+)?(?P<pline>{_PTS2}))))?",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_sec_con and not m_sec_par_or_perp:
        pname = m_sec_con.group("p1") or m_sec_con.group("p2")
        pts_list = _split_pts(m_sec_con.group("pts"))
        constraints: list[dict[str, Any]] = [{"kind": "contains_points", "operands": pts_list}]
        if m_sec_con.group("perp"):
            constraints.append({"kind": "perpendicular_to_plane", "operands": _split_pts(m_sec_con.group("pplane"))})
        elif m_sec_con.group("par"):
            constraints.append({"kind": "parallel_to_line", "operands": _split_pts(m_sec_con.group("pline"))})
        if len(pts_list) >= 3 or len(constraints) >= 2:
            q_con = _clean_quote(raw, ca + m_sec_con.start(), ca + m_sec_con.end())
            sec_id = "sec"
            builder.derived_sections.append(
                {
                    "section_id": sec_id,
                    "plane_name": pname,
                    "target_solid_id": builder._primary_solid_id,
                    "plane_kind": "constrained",
                    "constraints": constraints,
                    "stated_intersections": [],
                    "quote": q_con,
                }
            )
            builder._section_by_plane_name[pname] = sec_id
            builder._last_section_id = sec_id
            mapped_fact = True

    # ── 7. Simulation & Math Goals ───────────────────────────────────────────────────────────────────────────────
    # 7a. Ambiguous "Vẽ hình rồi tính." (`S2-C-C05_draw_then_compute`)
    m_draw_compute_empty = re.search(
        r"(?P<v>Vẽ\s+hình|Mô\s+phỏng\s+hình)\s+(?P<t>rồi\s+tính)\s*$",
        ctext_norm.strip(),
        re.IGNORECASE | re.UNICODE,
    )
    if m_draw_compute_empty:
        q_v = _clean_quote(raw, ca + m_draw_compute_empty.start("v"), ca + m_draw_compute_empty.end("v"))
        q_t = _clean_quote(raw, ca + m_draw_compute_empty.start("t"), ca + m_draw_compute_empty.end("t"))
        builder.simulation_goals = [
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": builder._primary_solid_id, "quote": q_v}
        ]
        builder.unresolved.append(
            {
                "unresolved_id": f"u{len(builder.unresolved) + 1}",
                "kind": "missing_operand",
                "quote": q_t,
                "missing_roles": ["goal_object"],
                "candidate_relations": [],
            }
        )
        clause.classification = CLAUSE_MAPPED_GOAL
        return

    # 7b. Trailing simulation request: "Hãy mô phỏng hình (và điểm M)?(, rồi tính ...)?" / "Vẽ hình rồi tính ..." / "Mô phỏng hình chóp và tính ..."
    m_sim_lead = re.match(
        rf"^\s*(?P<sim>(?:Hãy\s+)?(?:mô\s+phỏng|vẽ)\s+hình(?:\s+chóp|\s+lăng\s+trụ)?(?:\s+và\s+điểm\s+{_PT})?)(?:\s*(?:,\s*)?(?:rồi\s+|và\s+)?(?P<rest>tính\s+.+))?$",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_sim_lead and builder.solids:
        q_sim = _clean_quote(raw, ca + m_sim_lead.start("sim"), ca + m_sim_lead.end("sim"))
        builder.simulation_goals = [
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": builder._primary_solid_id, "quote": q_sim}
        ]
        mapped_goal = True

    # 7c. Construct plane section + derived sub-pyramid ("Dựng thiết diện của hình chóp S.ABC bởi (α) và khối chóp đỉnh S cắt bởi (α)")
    m_con_sec_only = re.search(
        rf"Dựng\s+(?:từng\s+bước\s+hình\s+chóp\s*,\s*|lăng\s+trụ\s*,\s*)?thiết\s+diện(?:\s+của\s+hình\s+(?:chóp|lăng\s+trụ)(?:\s+{_PT}\.{_PTS3_6})?)?(?:\s+(?:cắt\s+)?bởi\s+\((?P<pname>{_PT}|[α-ω]'?)\))?(?:\s*(?:,|\bvà\b)\s*khối\s+chóp\s+(?:(?P<sub_ap>{_PT})\.{_PTS3_6}|đỉnh\s+(?P<ap>{_PT})\s+cắt\s+bởi\s+\((?P<pname2>{_PT}|[α-ω]'?)\)|cắt\s+bởi\s+\((?P<pname3>{_PT}|[α-ω]'?)\)\s+chứa\s+đỉnh\s+(?P<ap2>{_PT})))?",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_con_sec_only and (m_con_sec_only.group("pname") or m_con_sec_only.group("pname2") or m_con_sec_only.group("pname3")):
        pname = m_con_sec_only.group("pname") or m_con_sec_only.group("pname2") or m_con_sec_only.group("pname3")
        sec_id = builder._section_by_plane_name.get(pname, builder._last_section_id or "sec")
        q_cs = _clean_quote(raw, ca + m_con_sec_only.start(), ca + m_con_sec_only.end())
        builder.simulation_goals = [
            {"goal_id": "g_sec", "kind": "construct_plane_section", "target_section_id": sec_id, "quote": q_cs}
        ]
        ap_tok = m_con_sec_only.group("ap") or m_con_sec_only.group("sub_ap") or m_con_sec_only.group("ap2")
        if ap_tok:
            builder.simulation_goals.append(
                {
                    "goal_id": "g_sub",
                    "kind": "construct_derived_solid",
                    "derived_solid_id": "sub",
                    "parent_solid_id": builder._primary_solid_id,
                    "target_section_id": sec_id,
                    "apex_ref": ap_tok,
                    "quote": q_cs,
                }
            )
        mapped_goal = True

    # 7c-2. Volume ratio of cut sub-pyramid to parent pyramid:
    # "Tính tỉ số thể tích của hai khối chóp S.MNPQ và S.ABCD" / "Tính tỉ số thể tích giữa khối chóp đỉnh S cắt bởi (α) và khối chóp S.ABCD"
    m_vol_ratio = re.search(
        rf"(?P<full>Tính\s+tỉ\s+số\s+thể\s+tích\s+(?:của\s+hai\s+khối\s+chóp\s+(?P<ap1>{_PT})\.(?P<b1>{_PTS3_6})\s+và\s+(?P<ap2>{_PT})\.(?P<b2>{_PTS3_6})|(?:của|giữa)\s+khối\s+chóp\s+đỉnh\s+(?P<ap3>{_PT})\s+cắt\s+bởi\s+\((?P<pname>{_PT}|[α-ω]'?)\)\s+và\s+(?:khối\s+chóp\s+)?{_PT}\.{_PTS3_6}))",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_vol_ratio and builder.derived_sections:
        q_vr = _clean_quote(raw, ca + m_vol_ratio.start("full"), ca + m_vol_ratio.end("full"))
        sec_id = builder._last_section_id or "sec"
        ap_tok = m_vol_ratio.group("ap1") or m_vol_ratio.group("ap3") or (builder._primary_notation.split(".")[0] if "." in builder._primary_notation else "S")
        if not any(sg.get("kind") == "construct_plane_section" for sg in builder.simulation_goals):
            builder.simulation_goals = [
                {"goal_id": "g_sec", "kind": "construct_plane_section", "target_section_id": sec_id, "quote": builder.derived_sections[-1]["quote"]}
            ]
        if not any(sg.get("kind") == "construct_derived_solid" for sg in builder.simulation_goals):
            builder.simulation_goals.append(
                {
                    "goal_id": "g_sub",
                    "kind": "construct_derived_solid",
                    "derived_solid_id": "sub",
                    "parent_solid_id": builder._primary_solid_id,
                    "target_section_id": sec_id,
                    "apex_ref": ap_tok,
                    "quote": q_vr,
                }
            )
        builder.math_goals.append(
            {
                "goal_id": "g_ratio",
                "kind": "volume_ratio",
                "numerator_solid_id": "sub",
                "denominator_solid_id": builder._primary_solid_id,
                "quote": q_vr,
            }
        )
        mapped_goal = True

    # 7c-3. Residual volume of pyramid after cutting sub-pyramid:
    # "Tính thể tích phần còn lại của khối chóp S.ABCD sau khi cắt bỏ khối chóp S.MNPQ"
    m_res_pyr = re.search(
        rf"(?P<full>Tính\s+thể\s+tích\s+phần\s+còn\s+lại\s+của\s+khối\s+chóp\s+{_PT}\.{_PTS3_6}\s+sau\s+khi\s+cắt\s+bỏ\s+khối\s+chóp\s+(?P<ap>{_PT})\.{_PTS3_6})",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_res_pyr and builder.derived_sections:
        q_rp = _clean_quote(raw, ca + m_res_pyr.start("full"), ca + m_res_pyr.end("full"))
        sec_id = builder._last_section_id or "sec"
        if not any(sg.get("kind") == "construct_derived_solid" for sg in builder.simulation_goals):
            builder.simulation_goals.append(
                {
                    "goal_id": "g_sub",
                    "kind": "construct_derived_solid",
                    "derived_solid_id": "sub",
                    "parent_solid_id": builder._primary_solid_id,
                    "target_section_id": sec_id,
                    "apex_ref": m_res_pyr.group("ap"),
                    "quote": q_rp,
                }
            )
        builder.math_goals.append(
            {
                "goal_id": "g_res",
                "kind": "residual_volume",
                "parent_solid_id": builder._primary_solid_id,
                "cut_solid_id": "sub",
                "quote": q_rp,
            }
        )
        mapped_goal = True

    # 7d. Residual volume of cone frustum: "Tính thể tích của khối nón cụt" (when derived solid `kn` exists)
    if re.search(r"tính\s+thể\s+tích(?:\s+của)?\s+khối\s+nón\s+cụt", ctext_norm, re.IGNORECASE) and any(
        sg.get("kind") == "construct_derived_solid" for sg in builder.simulation_goals
    ):
        q_rv = _clean_quote(raw, ca, cb)
        builder.math_goals.append(
            {
                "goal_id": f"mg{len(builder.math_goals) + 1}",
                "kind": "residual_volume",
                "parent_solid_id": "k",
                "cut_solid_id": "kn",
                "quote": q_rv,
            }
        )
        clause.classification = CLAUSE_MAPPED_GOAL
        return

    # 7e. Section area goal:
    # "(Xác định thiết diện của ... cắt bởi (P) và )?tính diện tích thiết diện( của ... cắt bởi (mặt phẳng )?(P)| đó)?"
    m_sec_area = re.search(
        rf"(?P<full>(?:Xác\s+định\s+thiết\s+diện.*?và\s+)?tính\s+diện\s+tích\s+thiết\s+diện(?:\s+của\s+.*?cắt\s+bởi\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<pname>{_PT}|[α-ω]'?)\)|\s+đó)?)",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_sec_area:
        pname = m_sec_area.group("pname")
        sec_id = (
            builder._section_by_plane_name.get(pname, builder._last_section_id or "sec")
            if pname
            else (builder._last_section_id or "sec")
        )
        # Check if sentence also asks for another quantity (e.g. `và thể tích khối cầu (S)`)
        has_compound_tail = bool(
            re.search(r"và\s+thể\s+tích\s+khối\s+cầu", ctext_norm[m_sec_area.end("full") :], re.IGNORECASE)
        )
        q_sa = (
            _clean_quote(raw, ca, cb)
            if has_compound_tail
            else _clean_quote(raw, ca + m_sec_area.start("full"), ca + m_sec_area.end("full"))
        )
        if any(s["section_id"] == sec_id for s in builder.derived_sections):
            gid = f"q{len(builder.math_goals) + 1}"
            goal_entry: dict[str, Any] = {
                "goal_id": gid,
                "kind": "measurement",
                "goal_type": "area",
                "target": {"section_id": sec_id},
                "quote": q_sa,
            }
            if builder._primary_solid_type in ("pyramid", "tetrahedron", "prism", "box", "cube"):
                goal_entry["solid_id"] = builder._primary_solid_id
            builder.math_goals.append(goal_entry)
        mapped_goal = True

    # 7f. Volume goals:
    # Supports single or compound ("Tính diện tích mặt cầu (S1), diện tích mặt cầu (S2) và thể tích khối lập phương ABCD.A'B'C'D'")
    for m_sph_area in re.finditer(
        rf"diện\s+tích\s+mặt\s+cầu\s+(?P<sname>\({_PT}\))",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        sname = m_sph_area.group("sname")
        sph_sid = builder._sphere_by_notation.get(sname, "sph")
        q_spa = _clean_quote(raw, ca, cb)
        builder.math_goals.append(
            {
                "goal_id": f"q{len(builder.math_goals) + 1}",
                "kind": "measurement",
                "goal_type": "area",
                "target": {"solid": sname},
                "solid_id": sph_sid,
                "quote": q_spa,
            }
        )
        mapped_goal = True

    for m_sph_rad in re.finditer(
        rf"bán\s+kính\s+mặt\s+cầu(?:\s+(?:nội\s+tiếp|ngoại\s+tiếp)\s+(?:hình\s+chóp|khối\s+chóp|hình\s+lăng\s+trụ|hình\s+lập\s+phương)\s+{_PT}\.{_PTS3_6}|\s+(?P<sname>\({_PT}\)))",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        sname = m_sph_rad.group("sname")
        if sname and sname in builder._sphere_by_notation:
            sph_sid = builder._sphere_by_notation[sname]
            target_tok = sname
        elif builder._sphere_by_notation:
            target_tok, sph_sid = next(iter(builder._sphere_by_notation.items()))
        else:
            sph_sid = "sph"
            target_tok = sname or "I"
        q_rad = _clean_quote(raw, ca, cb)
        builder.math_goals.append(
            {
                "goal_id": f"q{len(builder.math_goals) + 1}",
                "kind": "measurement",
                "goal_type": "radius",
                "target": {"solid": target_tok},
                "solid_id": sph_sid,
                "quote": q_rad,
            }
        )
        mapped_goal = True

    for m_vol in (
        re.finditer(
            rf"(?P<full>(?:tính\s+)?thể\s+tích(?:\s+của)?\s+(?P<kind>(?:khối\s+chóp|hình\s+chóp)(?!\s+cụt)|khối\s+tứ\s+diện|tứ\s+diện|khối\s+lăng\s+trụ|hình\s+lăng\s+trụ|khối\s+lập\s+phương|hình\s+lập\s+phương|(?:khối|hình)\s+hộp(?:\s+chữ\s+nhật)?|khối\s+cầu|mặt\s+cầu|khối\s+trụ|hình\s+trụ|khối\s+nón|hình\s+nón)(?:\s+(?P<not>\({_PT}\)|{_PT}\.{_PTS3_6}|{_PTS3_6}\.{_PTS3_6}|{_PTS4})|\s+(?:đã\s+cho|đó|này))?)",
            ctext_norm,
            re.IGNORECASE | re.UNICODE,
        )
        if not (m_vol_ratio or m_res_pyr)
        else ()
    ):
        if not builder.solids and not builder._sphere_by_notation:
            continue
        not_v = m_vol.group("not")
        k_v = m_vol.group("kind").lower()
        if "cầu" in k_v and not_v and not_v in builder._sphere_by_notation:
            sid_v = builder._sphere_by_notation[not_v]
        elif not_v:
            sid_v = next(
                (s["solid_id"] for s in builder.solids if s["notation"].replace(".", "") == not_v.replace(".", "")),
                None,
            )
            if sid_v is None:
                continue
        else:
            sid_v = builder._primary_solid_id
        # Use full clause quote if multiple goals share the sentence, else exact match quote
        is_multi_in_clause = bool(re.search(r"\bvà\b|,.*tính", ctext_norm, re.IGNORECASE)) and not bool(m_sim_lead)
        q_v = (
            _clean_quote(raw, ca, cb)
            if is_multi_in_clause
            else _clean_quote(raw, ca + m_vol.start("full"), ca + m_vol.end("full"))
        )
        builder.math_goals.append(
            {
                "goal_id": f"q{len(builder.math_goals) + 1}",
                "kind": "measurement",
                "goal_type": "volume",
                "target": {"solid_id": sid_v},
                "solid_id": sid_v,
                "quote": q_v,
            }
        )
        mapped_goal = True

    # Curved surface area goals: "Tính diện tích toàn phần của hình trụ", "Tính diện tích xung quanh của hình nón"
    m_curved_area = re.search(
        r"(?P<full>Tính\s+diện\s+tích\s+(?P<kind>toàn\s+phần|xung\s+quanh)\s+của\s+hình\s+(?:trụ|nón))",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_curved_area and builder._primary_notation:
        q_ca = _clean_quote(raw, ca + m_curved_area.start("full"), ca + m_curved_area.end("full"))
        gtype = "area" if "toàn" in m_curved_area.group("kind").lower() else "lateral_area"
        builder.math_goals.append(
            {
                "goal_id": f"q{len(builder.math_goals) + 1}",
                "kind": "measurement",
                "goal_type": gtype,
                "target": {"solid": builder._primary_notation},
                "quote": q_ca,
            }
        )
        mapped_goal = True

    # 7g. Polygon area goal: "Tính diện tích tam giác tạo bởi trung điểm của SC, A và B" or "Tính diện tích tam giác S, C và trung điểm của AB" or "Tính diện tích tam giác ABC"
    m_tri_desc = re.search(
        rf"(?P<full>Tính\s+diện\s+tích\s+tam\s+giác\s+tạo\s+bởi\s+(?:(?P<d1>.+?)\s*,\s*(?P<p1>{_PT})\s+và\s+(?P<p2>{_PT})$|(?P<q1>{_PT})\s*,\s*(?P<q2>{_PT})\s+và\s+(?P<d2>.+)$))",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_tri_desc:
        q_td = _clean_quote(raw, ca + m_tri_desc.start("full"), ca + m_tri_desc.end("full"))
        if m_tri_desc.group("d1") and m_tri_desc.group("p1")[0].isupper() and m_tri_desc.group("p2")[0].isupper():
            d_ref = builder.parse_point_or_described(m_tri_desc.group("d1"), ca + m_tri_desc.start("d1"))
            poly = [d_ref, m_tri_desc.group("p1"), m_tri_desc.group("p2")] if d_ref else []
        elif m_tri_desc.group("d2") and m_tri_desc.group("q1")[0].isupper() and m_tri_desc.group("q2")[0].isupper():
            d_ref = builder.parse_point_or_described(m_tri_desc.group("d2"), ca + m_tri_desc.start("d2"))
            poly = [m_tri_desc.group("q1"), m_tri_desc.group("q2"), d_ref] if d_ref else []
        else:
            poly = []
        if len(poly) == 3:
            builder.math_goals.append(
                {
                    "goal_id": f"q{len(builder.math_goals) + 1}",
                    "kind": "measurement",
                    "goal_type": "area",
                    "target": {"polygon": poly},
                    "solid_id": builder._primary_solid_id,
                    "quote": q_td,
                }
            )
            mapped_goal = True

    for m_poly_area in re.finditer(
        rf"(?P<full>Tính\s+diện\s+tích\s+(?:tam\s+giác|tứ\s+giác|hình\s+vuông|hình\s+chữ\s+nhật)\s+(?P<poly>{_PTS3_6}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        q_pa = _clean_quote(raw, ca + m_poly_area.start("full"), ca + m_poly_area.end("full"))
        builder.math_goals.append(
            {
                "goal_id": f"q{len(builder.math_goals) + 1}",
                "kind": "measurement",
                "goal_type": "area",
                "target": {"polygon": _split_pts(m_poly_area.group("poly"))},
                "solid_id": builder._primary_solid_id,
                "quote": q_pa,
            }
        )
        mapped_goal = True

    # 7h. Segment length goals:
    # - "Tính độ dài đoạn thẳng nối <src> với <dst>"
    # - "(Tính )?độ dài (đoạn thẳng )?SC"
    m_len_join = re.search(
        rf"(?P<full>Tính\s+độ\s+dài\s+đoạn\s+thẳng\s+nối\s+(?P<a>.+?)\s+với\s+(?P<b>.+))",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_len_join:
        ref_a = builder.parse_point_or_described(m_len_join.group("a"), ca + m_len_join.start("a"))
        ref_b = builder.parse_point_or_described(m_len_join.group("b"), ca + m_len_join.start("b"))
        if ref_a and ref_b:
            q_lj = _clean_quote(raw, ca + m_len_join.start("full"), ca + m_len_join.end("full"))
            builder.math_goals.append(
                {
                    "goal_id": f"q{len(builder.math_goals) + 1}",
                    "kind": "measurement",
                    "goal_type": "distance",
                    "target": {"segment": [ref_a, ref_b]},
                    "solid_id": builder._primary_solid_id,
                    "quote": q_lj,
                }
            )
            mapped_goal = True

    for m_len_seg in re.finditer(
        rf"(?P<full>(?:tính\s+)?độ\s+dài(?:\s+(?:đoạn\s+thẳng|đường\s+chéo|cạnh))?\s+(?P<seg>{_PTS2}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        seg_pts = _split_pts(m_len_seg.group("seg"))
        has_other_goal_in_clause = bool(
            re.search(r"khoảng\s+cách|bán\s+kính|thể\s+tích", ctext_norm, re.IGNORECASE)
        )
        q_ls = (
            _clean_quote(raw, ca + m_len_seg.start("full"), ca + m_len_seg.end("full"))
            if m_sim_lead
            else (_clean_quote(raw, ca, cb) if has_other_goal_in_clause else _clean_quote(raw, ca + m_len_seg.start("full"), ca + m_len_seg.end("full")))
        )
        goal_seg_entry: dict[str, Any] = {
            "goal_id": f"q{len(builder.math_goals) + 1}",
            "kind": "measurement",
            "goal_type": "distance",
            "target": {"segment": seg_pts},
            "quote": q_ls,
        }
        poly_s = [s for s in builder.solids if s["solid_type"] in ("pyramid", "prism")]
        if len(poly_s) <= 1:
            goal_seg_entry["solid_id"] = builder._primary_solid_id
        else:
            matching_sids = [
                s["solid_id"]
                for s in poly_s
                if set(seg_pts) <= set(_split_pts(s["notation"].replace(".", "")))
            ]
            if len(matching_sids) == 1:
                goal_seg_entry["solid_id"] = matching_sids[0]
        builder.math_goals.append(goal_seg_entry)
        mapped_goal = True

    # 7i. Distance goals:
    # - Point/described-point to plane or line: "(Tính )?(khoảng cách|k/c) từ <src> (đến|tới) ((mặt phẳng|mp) (SBC) | (đường thẳng|cạnh) SC | đường thẳng nối A với <desc>)"
    for m_dist_from in re.finditer(
        rf"(?P<full>(?:tính\s+)?(?:khoảng\s+cách|k/c)\s+từ\s+(?P<src>.+?)\s+(?:đến|tới)\s+(?P<dst>(?:mặt\s+phẳng\s+|mp\s*)?\({_PTS3_6}\)|đường\s+thẳng\s+nối\s+{_PT}\s+với\s+.+|(?:đường\s+thẳng\s+|cạnh\s+)?{_PTS2}))(?![\w')])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        src_str = m_dist_from.group("src").strip()
        dst_str = m_dist_from.group("dst").strip()
        src_ref = builder.parse_point_or_described(src_str, ca + m_dist_from.start("src"))
        if src_ref:
            q_df = _clean_quote(raw, ca + m_dist_from.start("full"), ca + m_dist_from.end("full"))
            if not q_df.lower().startswith("tính"):
                q_df = _clean_quote(raw, ca, cb)
            m_pl = re.search(rf"\((?P<pl>{_PTS3_6})\)", dst_str)
            m_ln_desc = re.match(
                rf"đường\s+thẳng\s+nối\s+(?P<a>{_PT})\s+với\s+(?P<b>.+)",
                dst_str,
                re.IGNORECASE | re.UNICODE,
            )
            if m_pl:
                builder.math_goals.append(
                    {
                        "goal_id": f"q{len(builder.math_goals) + 1}",
                        "kind": "measurement",
                        "goal_type": "distance",
                        "target": {"point": src_ref, "plane": _split_pts(m_pl.group("pl"))},
                        "solid_id": builder._primary_solid_id,
                        "quote": q_df,
                    }
                )
                mapped_goal = True
            elif m_ln_desc:
                b_str = m_ln_desc.group("b")
                b_off = ca + m_dist_from.start("dst") + m_ln_desc.start("b")
                b_ref = builder.parse_point_or_described(b_str, b_off)
                if b_ref:
                    builder.math_goals.append(
                        {
                            "goal_id": f"q{len(builder.math_goals) + 1}",
                            "kind": "measurement",
                            "goal_type": "distance",
                            "target": {"point": src_ref, "line": [m_ln_desc.group("a"), b_ref]},
                            "solid_id": builder._primary_solid_id,
                            "quote": q_df,
                        }
                    )
                    mapped_goal = True
            else:
                m_ln = re.search(rf"(?P<ln>{_PTS2})$", dst_str)
                if m_ln:
                    builder.math_goals.append(
                        {
                            "goal_id": f"q{len(builder.math_goals) + 1}",
                            "kind": "measurement",
                            "goal_type": "distance",
                            "target": {"point": src_ref, "line": _split_pts(m_ln.group("ln"))},
                            "solid_id": builder._primary_solid_id,
                            "quote": q_df,
                        }
                    )
                    mapped_goal = True

    # - Distance between two lines or line and plane:
    # "Tính khoảng cách giữa hai đường thẳng AB và SC"
    # "Tính khoảng cách giữa đường thẳng AD và mặt phẳng (SBC)"
    # "Tính khoảng cách giữa đường thẳng nối M với trung điểm của SC và mặt phẳng (ABCD)"
    m_dist_between = re.search(
        rf"(?P<full>Tính\s+khoảng\s+cách\s+giữa\s+(?:hai\s+đường\s+thẳng\s+(?P<l1>{_PTS2})\s+và\s+(?P<l2>{_PTS2})|đường\s+thẳng\s+nối\s+(?P<la>{_PT})\s+với\s+(?P<lb>.+?)\s+và\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<pl1>{_PTS3_6})\)|(?:đường\s+thẳng\s+)?(?P<ln>{_PTS2})\s+và\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<pl2>{_PTS3_6})\)))",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_dist_between:
        q_db = _clean_quote(raw, ca + m_dist_between.start("full"), ca + m_dist_between.end("full"))
        if m_dist_between.group("l1") and m_dist_between.group("l2"):
            builder.math_goals.append(
                {
                    "goal_id": f"q{len(builder.math_goals) + 1}",
                    "kind": "measurement",
                    "goal_type": "distance",
                    "target": {
                        "line1": _split_pts(m_dist_between.group("l1")),
                        "line2": _split_pts(m_dist_between.group("l2")),
                    },
                    "solid_id": builder._primary_solid_id,
                    "quote": q_db,
                }
            )
            mapped_goal = True
        elif m_dist_between.group("la") and m_dist_between.group("lb"):
            lb_ref = builder.parse_point_or_described(
                m_dist_between.group("lb"), ca + m_dist_between.start("lb")
            )
            if lb_ref:
                builder.math_goals.append(
                    {
                        "goal_id": f"q{len(builder.math_goals) + 1}",
                        "kind": "measurement",
                        "goal_type": "distance",
                        "target": {
                            "line": [m_dist_between.group("la"), lb_ref],
                            "plane": _split_pts(m_dist_between.group("pl1")),
                        },
                        "solid_id": builder._primary_solid_id,
                        "quote": q_db,
                    }
                )
                mapped_goal = True
        elif m_dist_between.group("ln") and m_dist_between.group("pl2"):
            builder.math_goals.append(
                {
                    "goal_id": f"q{len(builder.math_goals) + 1}",
                    "kind": "measurement",
                    "goal_type": "distance",
                    "target": {
                        "line": _split_pts(m_dist_between.group("ln")),
                        "plane": _split_pts(m_dist_between.group("pl2")),
                    },
                    "solid_id": builder._primary_solid_id,
                    "quote": q_db,
                }
            )
            mapped_goal = True

    # 7j. Angle goals:
    # - Missing plane clarification: "Tính góc giữa SB và mặt phẳng." (`N4`, `HB41`, `S2-C-C04`)
    m_ang_missing = re.search(
        rf"(?P<full>Tính\s+góc\s+giữa\s+(?:đường\s+thẳng\s+|cạnh\s+)?(?P<ln>{_PTS2})\s+và\s+mặt\s+phẳng)\s*$",
        ctext_norm.strip(),
        re.IGNORECASE | re.UNICODE,
    )
    if m_ang_missing:
        q_am = _clean_quote(raw, ca + m_ang_missing.start("full"), ca + m_ang_missing.end("full"))
        if builder._base_vertices:
            builder.math_goals.append(
                {
                    "goal_id": f"q{len(builder.math_goals) + 1}",
                    "kind": "measurement",
                    "goal_type": "angle",
                    "target": {
                        "line": _split_pts(m_ang_missing.group("ln")),
                        "plane": list(builder._base_vertices),
                    },
                    "solid_id": builder._primary_solid_id,
                    "quote": q_am,
                }
            )
        builder.unresolved.append(
            {
                "unresolved_id": f"u{len(builder.unresolved) + 1}",
                "kind": "missing_operand",
                "quote": q_am,
                "missing_roles": ["target_line_or_plane"],
                "candidate_relations": ["angle"],
            }
        )
        clause.classification = CLAUSE_MAPPED_GOAL
        return

    # - Angle between line (or line joining A with @desc) and plane or line, or between two planes:
    m_ang = re.search(
        rf"(?P<full>(?:Tính\s+)?(?:số\s+đo\s+(?:của\s+)?)?góc\s+(?:giữa|tạo\s+bởi|hợp\s+bởi)\s+(?:"
        rf"(?:hai\s+mặt\s+phẳng\s+|mặt\s+phẳng\s+)?\((?P<pl1>{_PTS3_6})\)\s+và\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<pl2>{_PTS3_6})\)"
        rf"|đường\s+thẳng\s+(?:nối|đi\s+qua)\s+(?P<la>{_PT})\s+(?:với|và)\s+(?P<lb>.+?)\s+(?:và|với)\s+(?:(?P<is_pl>mặt\s+phẳng\s+|mp\s*)?\((?P<pl3>{_PTS3_6})\)|(?:đường\s+thẳng\s+|cạnh\s+)?(?P<l2_desc>{_PTS2}))"
        rf"|(?:hai\s+đường\s+thẳng\s+|đường\s+thẳng\s+|đt\s+|cạnh\s+)?(?P<l1>{_PTS2})\s+và\s+(?:(?:mặt\s+phẳng\s+|mp\s*)?\((?P<pl4>{_PTS3_6})\)|(?:đường\s+thẳng\s+|cạnh\s+)?(?P<l2>{_PTS2}))"
        rf"))",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if (
        m_ang
        and not any(a <= m_ang.start("full") < b for a, b in angle_spans)
        and not re.match(rf"\s*(?:bằng|là|=)\s*\d+(?:/\d+)?\s*(?:°|độ\b)", ctext_norm[m_ang.end("full") :], re.IGNORECASE)
    ):
        angle_spans.append((m_ang.start("full"), m_ang.end("full")))
        q_ang = _clean_quote(raw, ca + m_ang.start("full"), ca + m_ang.end("full"))
        if m_ang.group("pl1") and m_ang.group("pl2"):
            builder.math_goals.append(
                {
                    "goal_id": f"q{len(builder.math_goals) + 1}",
                    "kind": "measurement",
                    "goal_type": "angle",
                    "target": {
                        "plane1": _split_pts(m_ang.group("pl1")),
                        "plane2": _split_pts(m_ang.group("pl2")),
                    },
                    "solid_id": builder._primary_solid_id,
                    "quote": q_ang,
                }
            )
            mapped_goal = True
        elif m_ang.group("la") and m_ang.group("lb"):
            lb_ref = builder.parse_point_or_described(m_ang.group("lb"), ca + m_ang.start("lb"))
            if lb_ref:
                if m_ang.group("pl3"):
                    builder.math_goals.append(
                        {
                            "goal_id": f"q{len(builder.math_goals) + 1}",
                            "kind": "measurement",
                            "goal_type": "angle",
                            "target": {
                                "line": [m_ang.group("la"), lb_ref],
                                "plane": _split_pts(m_ang.group("pl3")),
                            },
                            "solid_id": builder._primary_solid_id,
                            "quote": q_ang,
                        }
                    )
                    mapped_goal = True
                elif m_ang.group("l2_desc"):
                    builder.math_goals.append(
                        {
                            "goal_id": f"q{len(builder.math_goals) + 1}",
                            "kind": "measurement",
                            "goal_type": "angle",
                            "target": {
                                "line1": [m_ang.group("la"), lb_ref],
                                "line2": _split_pts(m_ang.group("l2_desc")),
                            },
                            "solid_id": builder._primary_solid_id,
                            "quote": q_ang,
                        }
                    )
                    mapped_goal = True
        elif m_ang.group("l1"):
            if m_ang.group("pl4"):
                builder.math_goals.append(
                    {
                        "goal_id": f"q{len(builder.math_goals) + 1}",
                        "kind": "measurement",
                        "goal_type": "angle",
                        "target": {
                            "line": _split_pts(m_ang.group("l1")),
                            "plane": _split_pts(m_ang.group("pl4")),
                        },
                        "solid_id": builder._primary_solid_id,
                        "quote": q_ang,
                    }
                )
                mapped_goal = True
            elif m_ang.group("l2"):
                builder.math_goals.append(
                    {
                        "goal_id": f"q{len(builder.math_goals) + 1}",
                        "kind": "measurement",
                        "goal_type": "angle",
                        "target": {
                            "line1": _split_pts(m_ang.group("l1")),
                            "line2": _split_pts(m_ang.group("l2")),
                        },
                        "solid_id": builder._primary_solid_id,
                        "quote": q_ang,
                    }
                )
                mapped_goal = True

    # ── 7k. Intra-Sentence Integrity & Sub-Clause Coverage Guard ─────────────────────────────────────────────────
    if (mapped_fact or mapped_goal) and not builder.unresolved:
        clause_premises = builder.premises[pre_premises_len:]
        clause_sections = builder.derived_sections[pre_sections_len:]
        clause_goals = builder.math_goals[pre_goals_len:]
        clause_solids = builder.solids[pre_solids_len:]

        # 1) Every `=` in `ctext_norm` must belong to a recognized equality construct
        if "=" in ctext_norm:
            eq_spans: list[tuple[int, int]] = list(angle_spans)
            for eq_pat in (
                rf"chiều\s+cao(?:\s+của\s+hình\s+chóp(?:\s+[A-Z0-9'.]+)?)?\s*=\s*{_VAL}",
                rf"(?:đường|chiều)\s+cao\s+{_PTS2}\s+của\s+(?:tam\s+giác|[Δ∆△])\s*{_PTS3}\s*=\s*{_VAL}",
                rf"đường\s+cao\s+{_PTS2}\s*=\s*{_VAL}",
                rf"(?<![\w'.]){_PTS2}\s*=\s*{_PTS2}(?:\s*=\s*{_PTS2})?\s*=\s*{_VAL}(?![\w'])",
                rf"(?:Đường\s+sinh\s+)?(?<![\w'.]){_PTS2}\s*=\s*{_VAL}(?![\s]*=)(?![\w'])",
                rf"(?:sao\s+cho|thỏa\s+mãn)\s+{_PTS2}\s*=\s*\d+\s*/\s*\d+\s*{_PTS2}(?![\w'])",
            ):
                for m_eq in re.finditer(eq_pat, ctext_norm, re.IGNORECASE | re.UNICODE):
                    eq_spans.append((m_eq.start(), m_eq.end()))
            # Part-to-part ratio ("SE = 3EC") counts only when 5b-3 actually built its `point_divides_segment`.
            if any(p["kind"] == "point_divides_segment" for p in clause_premises):
                for m_eq in re.finditer(
                    rf"(?:sao\s+cho|thỏa\s+mãn)\s+{_PTS2}\s*=\s*\d+(?:\s*/\s*\d+)?\s*{_PTS2}(?![\w'/])",
                    ctext_norm, re.IGNORECASE | re.UNICODE,
                ):
                    eq_spans.append((m_eq.start(), m_eq.end()))
            for eq_idx, ch in enumerate(ctext_norm):
                if ch == "=" and not any(a <= eq_idx < b for a, b in eq_spans):
                    mapped_fact = False
                    mapped_goal = False
                    clause.classification = CLAUSE_UNPARSED_FACT_CANDIDATE
                    return

        # 2) Any `∥` or `song song` must belong to a recognized section or trapezoid parallel construct
        has_trap_parallel = any(p["kind"] in ("trapezoid", "isosceles_trapezoid") for p in clause_premises)
        if ("∥" in ctext_norm and not has_trap_parallel) or (
            re.search(r"\bsong\s+song\b", ctext_norm, re.IGNORECASE)
            and not clause_sections
            and not has_trap_parallel
        ):
            mapped_fact = False
            mapped_goal = False
            clause.classification = CLAUSE_UNPARSED_FACT_CANDIDATE
            return

        # 2b) Any `⊥` or `vuông góc` (outside `hình chiếu vuông góc`) must be backed by a perpendicularity premise/section/described_point
        ctext_no_hcvg = re.sub(r"\bhình\s+chiếu\s+vuông\s+góc\b", " ", ctext_norm, flags=re.IGNORECASE)
        if "⊥" in ctext_no_hcvg or re.search(r"\bvuông\s+góc\b", ctext_no_hcvg, re.IGNORECASE):
            has_perp_item = (
                any(
                    p["kind"]
                    in ("perpendicular_line_plane", "perpendicular_lines", "face_perpendicular_base", "right_angle")
                    for p in clause_premises
                )
                or bool(clause_sections)
                or any(
                    dp.get("kind") in ("orthogonal_projection", "orthogonal_projection_line")
                    for dp in builder.described_points
                )
            )
            if not has_perp_item:
                mapped_fact = False
                mapped_goal = False
                clause.classification = CLAUSE_UNPARSED_FACT_CANDIDATE
                return

        # 3) Every `∠`, standalone `góc` (outside `vuông góc` / `góc chiếu`), or `hợp với` / `tạo với` must lie inside a parsed `angle_spans`
        for m_ang_tok in re.finditer(r"∠|\bgóc\b|\b(?:hợp|tạo)\s+với\b", ctext_norm, re.IGNORECASE | re.UNICODE):
            s_tok = m_ang_tok.start()
            if ctext_norm[max(0, s_tok - 6) : m_ang_tok.end()].lower().endswith("vuông góc"):
                continue
            if ctext_norm[s_tok : s_tok + 10].lower().startswith("góc chiếu"):
                continue
            if not any(a <= s_tok < b for a, b in angle_spans):
                mapped_fact = False
                mapped_goal = False
                clause.classification = CLAUSE_UNPARSED_FACT_CANDIDATE
                return

        # 4) Unsupported geometric shape / relation / negation / conditional sub-clause inside the sentence
        prem_kinds = {p["kind"] for p in clause_premises}
        unbacked_base_shape = (
            (bool(re.search(r"\bhình\s+thoi\b", ctext_norm, re.IGNORECASE)) and "rhombus" not in prem_kinds)
            or (bool(re.search(r"\bhình\s+bình\s+hành\b", ctext_norm, re.IGNORECASE)) and "parallelogram" not in prem_kinds)
            or (
                bool(re.search(r"\bhình\s+thang\b", ctext_norm, re.IGNORECASE))
                and not (prem_kinds & {"trapezoid", "isosceles_trapezoid", "right_angle"})
            )
            or (
                bool(re.search(r"\btam\s+giác\s+cân\b|(?<!vuông\s)\bcân\s+(?:tại|ở)\b", ctext_norm, re.IGNORECASE))
                and "equal_length" not in prem_kinds
            )
        )
        if unbacked_base_shape or re.search(
            r"\btâm\s+đường\s+tròn\s+nội\s+tiếp\b"
            r"|\b(?:đường\s+phân\s+giác|đường\s+trung\s+tuyến|trọng\s+tuyến)\b"
            r"|\bnghiêng\s+đều\b"
            r"|\bkhông\s+(?:vuông\s+góc|song\s+song|cắt|đồng\s+phẳng|thẳng\s+hàng|trùng)\b"
            r"|\bnếu\b.+\bthì\b"
            r"|\bmặt\s+bên\b.*\bnằm\s+trong\s+mặt\s+phẳng\s+vuông\s+góc\b",
            ctext_norm,
            re.IGNORECASE | re.UNICODE,
        ):
            mapped_fact = False
            mapped_goal = False
            clause.classification = CLAUSE_UNPARSED_FACT_CANDIDATE
            return

        # 5) Named point introduction `Gọi <P> là ...` where `<P>` was not bound in premises or solids
        for m_goi_pt in re.finditer(rf"\bGọi\s+(?P<pt>{_PT})\s+là\b", ctext_norm, re.IGNORECASE | re.UNICODE):
            pt_name = m_goi_pt.group("pt")
            if not pt_name[0].isupper():
                continue
            bound_in_clause = any(
                p["args"].get("point") == pt_name or p["args"].get("image") == pt_name
                for p in clause_premises
            ) or any(
                s.get("center") == pt_name or s.get("notation") == pt_name
                for s in clause_solids
            )
            if not bound_in_clause:
                mapped_fact = False
                mapped_goal = False
                clause.classification = CLAUSE_UNPARSED_FACT_CANDIDATE
                return

        # 6) Compound goal completeness: if two scalar goal quantities are joined by `và`, must have >= 2 math_goals
        _q_kw = r"(?:diện\s+tích|thể\s+tích|khoảng\s+cách|k/c|độ\s+dài|bán\s+kính|góc\s+(?:giữa|tạo\s+bởi|hợp\s+bởi)|tỉ\s+số|chu\s+vi)"
        if mapped_goal and re.search(
            rf"\b{_q_kw}\b.+?\bvà\s+(?:tính\s+)?{_q_kw}\b",
            ctext_norm,
            re.IGNORECASE | re.UNICODE,
        ):
            if len(clause_goals) < 2:
                mapped_goal = False
                mapped_fact = False
                clause.classification = CLAUSE_UNPARSED_GOAL_CANDIDATE
                return

    # ── 8. Classify Clause Coverage ──────────────────────────────────────────────────────────────────────────────
    if mapped_goal:
        clause.classification = CLAUSE_MAPPED_GOAL
    elif mapped_fact:
        clause.classification = CLAUSE_MAPPED_FACT
    else:
        # Check if benign discourse (e.g., exam label "Câu 1:", "Bài 2:", "(2,5 điểm)")
        if _EXAM_HEADER_PREFIX_RE.fullmatch(ctext_norm.strip()):
            clause.classification = CLAUSE_BENIGN_DISCOURSE
        elif _QUESTION_STARTER_RE.search(ctext_norm):
            clause.classification = CLAUSE_UNPARSED_GOAL_CANDIDATE
        elif _FACT_INDICATOR_RE.search(ctext_norm):
            clause.classification = CLAUSE_UNPARSED_FACT_CANDIDATE
        else:
            clause.classification = CLAUSE_BENIGN_DISCOURSE


# ── Stage 6, 7 & 8: Semantic Validation, Source-Span Coverage Check & Source Gate Verification ───────────────────────

_EXTRACTION_FIDELITY_ERROR_CODES = frozenset(
    {
        "QUOTE_NOT_IN_SOURCE",
        "PREDICATE_NOT_IN_QUOTE",
        "ROLE_NOT_IN_QUOTE",
        "OBJECT_NOT_IN_QUOTE",
        "PLANE_NOT_IN_QUOTE",
        "AMBIGUOUS_VALUE_QUOTE",
        "UNGROUNDED_VALUE",
        "SOURCE_OBJECT_MISMATCH",
        "SOURCE_PREMISE_UNREAD",
        "SOURCE_GOAL_UNREAD",
        "NOT_ASKED_IN_SOURCE",
        "REQUEST_NOT_ANSWERED",
        "QUESTION_CONTEXT_UNSUPPORTED",
        "QUESTION_LOCAL_GIVEN_UNVERIFIED",
        "AUXILIARY_RULE_MISMATCH",
    }
)

MAX_PARSER_CACHE_SIZE = 256
_PARSER_CACHE: OrderedDict[tuple[str, str], LocalParseResult] = OrderedDict()
_PARSER_CACHE_HITS = 0
_PARSER_CACHE_MISSES = 0


def clear_local_geometry_parser_cache() -> None:
    """Clear the bounded in-memory parser cache and reset telemetry counters."""
    global _PARSER_CACHE_HITS, _PARSER_CACHE_MISSES
    _PARSER_CACHE.clear()
    _PARSER_CACHE_HITS = 0
    _PARSER_CACHE_MISSES = 0


def get_local_geometry_parser_cache_stats() -> dict[str, int]:
    """Return current bounded in-memory parser cache telemetry."""
    return {
        "size": len(_PARSER_CACHE),
        "max_size": MAX_PARSER_CACHE_SIZE,
        "hits": _PARSER_CACHE_HITS,
        "misses": _PARSER_CACHE_MISSES,
    }


def _parse_geometry_problem_locally_uncached(problem_text: str, t0: float) -> LocalParseResult:
    raw = normalize_problem_text(problem_text)
    if not raw or not raw.strip():
        empty_cov = SourceCoverageReport(0, 0, 0, 0, (), (), (), (), False)
        return LocalParseResult(
            parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
            status=LOCAL_PARSE_UNSUPPORTED,
            payload=None,
            parsed_contract=None,
            ast={},
            source_coverage=empty_cov,
            reason_code="EMPTY_PROBLEM_TEXT",
            fallback_reason="EMPTY_PROBLEM_TEXT",
            parse_latency_ms=(time.perf_counter() - t0) * 1000.0,
        )

    # Check domain gate first
    dom = detect_domain(raw)
    clauses = split_into_clauses(raw)
    builder = _AstBuilder(raw)

    for cl in clauses:
        _parse_clause_into_ast(builder, cl)

    unparsed_facts = tuple(c.text for c in clauses if c.classification == CLAUSE_UNPARSED_FACT_CANDIDATE)
    unparsed_goals = tuple(c.text for c in clauses if c.classification == CLAUSE_UNPARSED_GOAL_CANDIDATE)
    unresolved_refs = tuple(c.text for c in clauses if c.classification == CLAUSE_UNRESOLVED_REFERENCE)
    mapped_facts_n = sum(1 for c in clauses if c.classification == CLAUSE_MAPPED_FACT)
    mapped_goals_n = sum(1 for c in clauses if c.classification == CLAUSE_MAPPED_GOAL)
    benign_n = sum(1 for c in clauses if c.classification == CLAUSE_BENIGN_DISCOURSE)

    coverage_ok = (
        len(unparsed_facts) == 0
        and len(unparsed_goals) == 0
        and len(unresolved_refs) == 0
        and (mapped_facts_n + mapped_goals_n) > 0
    )

    cov_report = SourceCoverageReport(
        total_clauses=len(clauses),
        mapped_fact_clauses=mapped_facts_n,
        mapped_goal_clauses=mapped_goals_n,
        benign_discourse_clauses=benign_n,
        unparsed_fact_candidates=unparsed_facts,
        unparsed_goal_candidates=unparsed_goals,
        unresolved_references=unresolved_refs,
        clauses=tuple(
            {"index": c.index, "start": c.start, "end": c.end, "text": c.text, "classification": c.classification}
            for c in clauses
        ),
        coverage_complete=coverage_ok,
    )

    for ds in builder.derived_sections:
        ds.pop("_start_offset", None)

    payload: dict[str, Any] = {
        "schema_version": "typed-fact-next/2",
        "problem_text": raw,
        "length_unit": _detect_length_unit(raw),
        "solids": builder.solids,
        "premises": builder.premises,
        "relations": builder.relations,
        "derived_sections": builder.derived_sections,
        "simulation_goals": builder.simulation_goals,
        "math_goals": builder.math_goals,
    }
    if builder.described_points:
        payload["described_points"] = builder.described_points
    if builder.unresolved:
        payload["unresolved"] = builder.unresolved

    ast_summary = {
        "tokens_count": len(tokenize_problem_text(raw)),
        "solids_count": len(builder.solids),
        "premises_count": len(builder.premises),
        "described_points_count": len(builder.described_points),
        "derived_sections_count": len(builder.derived_sections),
        "relations_count": len(builder.relations),
        "simulation_goals_count": len(builder.simulation_goals),
        "math_goals_count": len(builder.math_goals),
        "unresolved_count": len(builder.unresolved),
    }

    if dom != DOMAIN_HINH_HOC and not builder.solids and not builder.unresolved:
        return LocalParseResult(
            parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
            status=LOCAL_PARSE_UNSUPPORTED,
            payload=None,
            parsed_contract=None,
            ast=ast_summary,
            source_coverage=cov_report,
            reason_code="GATE_OUT_OF_SCOPE",
            fallback_reason="OUT_OF_SCOPE_NON_GEOMETRY",
            parse_latency_ms=(time.perf_counter() - t0) * 1000.0,
        )

    # Validate against TypedFactNextPayloadV2 schema
    try:
        spec = parse_typed_fact_next_v2(payload)
    except TypedFactNextValidationError as exc:
        status = LOCAL_PARSE_PARTIAL if (builder.solids or builder.premises) else LOCAL_PARSE_UNSUPPORTED
        return LocalParseResult(
            parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
            status=status,
            payload=None,
            parsed_contract=None,
            ast=ast_summary,
            source_coverage=cov_report,
            reason_code=exc.code,
            fallback_reason=f"SCHEMA_VALIDATION_FAILED:{exc.code}:{exc}",
            parse_latency_ms=(time.perf_counter() - t0) * 1000.0,
        )

    # Check if explicit unresolved items were parsed (clarification or explicit unsupported capability)
    if builder.unresolved:
        kinds = {u["kind"] for u in builder.unresolved}
        if kinds & {"missing_operand", "ambiguous", "unrecognized_term"}:
            return LocalParseResult(
                parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
                status=LOCAL_PARSE_AMBIGUOUS,
                payload=payload,
                parsed_contract=spec,
                ast=ast_summary,
                source_coverage=cov_report,
                reason_code="AMBIGUOUS_FACT",
                fallback_reason=None,
                parse_latency_ms=(time.perf_counter() - t0) * 1000.0,
            )
        return LocalParseResult(
            parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
            status=LOCAL_PARSE_COMPLETE,
            payload=payload,
            parsed_contract=spec,
            ast=ast_summary,
            source_coverage=cov_report,
            reason_code="OUT_OF_SCOPE",
            fallback_reason=None,
            parse_latency_ms=(time.perf_counter() - t0) * 1000.0,
        )

    # Enforce strict Source-Span Coverage: never accept LOCAL_PARSE_COMPLETE if any fact/goal clause was unparsed
    if not coverage_ok or not builder.solids or (not builder.math_goals and not builder.simulation_goals):
        status = LOCAL_PARSE_PARTIAL if (builder.solids or builder.premises) else LOCAL_PARSE_UNSUPPORTED
        fb = (
            "UNPARSED_GOAL_CANDIDATE"
            if unparsed_goals
            else ("UNPARSED_FACT_CANDIDATE" if unparsed_facts else "INCOMPLETE_SOLID_OR_GOAL")
        )
        return LocalParseResult(
            parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
            status=status,
            payload=None,
            parsed_contract=None,
            ast=ast_summary,
            source_coverage=cov_report,
            reason_code=fb,
            fallback_reason=fb,
            parse_latency_ms=(time.perf_counter() - t0) * 1000.0,
        )

    # Stage 8: Verify with Bridge & Source Gate (`registry.kiem_nguon`) so no extraction-fidelity mismatch slips through
    try:
        bridged = bridge_v2(spec)
        plan = planner.lap_ke_hoach({"facts": bridged["facts"]}, raw)
        doc_quotes = tuple(
            q for g in (*plan.goals, *plan.negated) if g.get("call") for q in g["call"]["source"]["quotes"]
        )
        calls_t = registry.doc_ke_hoach({"calls": plan.calls})
        registry.kiem_nguon(calls_t, raw, tuple(plan.auxiliary), doc_quotes)
    except TuChoi as exc:
        if exc.code in _EXTRACTION_FIDELITY_ERROR_CODES:
            return LocalParseResult(
                parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
                status=LOCAL_PARSE_PARTIAL,
                payload=None,
                parsed_contract=None,
                ast=ast_summary,
                source_coverage=cov_report,
                reason_code=exc.code,
                fallback_reason=f"SOURCE_GATE_MISMATCH:{exc.code}:{exc.reason}",
                parse_latency_ms=(time.perf_counter() - t0) * 1000.0,
            )

    return LocalParseResult(
        parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
        status=LOCAL_PARSE_COMPLETE,
        payload=payload,
        parsed_contract=spec,
        ast=ast_summary,
        source_coverage=cov_report,
        reason_code=None,
        fallback_reason=None,
        parse_latency_ms=(time.perf_counter() - t0) * 1000.0,
    )


def parse_geometry_problem_locally(problem_text: str, *, use_cache: bool = True) -> LocalParseResult:
    """Parse a Vietnamese 3D geometry problem deterministically into `TypedFactNextPayloadV2` (`0` AI calls)."""
    global _PARSER_CACHE_HITS, _PARSER_CACHE_MISSES
    t0 = time.perf_counter()
    if not use_cache:
        return _parse_geometry_problem_locally_uncached(problem_text, t0)
    cache_key = (LOCAL_GEOMETRY_PARSER_VERSION, problem_text or "")
    cached = _PARSER_CACHE.get(cache_key)
    if cached is not None:
        _PARSER_CACHE_HITS += 1
        _PARSER_CACHE.move_to_end(cache_key)
        return LocalParseResult(
            parser_version=cached.parser_version,
            status=cached.status,
            payload=copy.deepcopy(cached.payload) if cached.payload is not None else None,
            parsed_contract=cached.parsed_contract,
            ast=dict(cached.ast),
            source_coverage=cached.source_coverage,
            reason_code=cached.reason_code,
            fallback_reason=cached.fallback_reason,
            parse_latency_ms=(time.perf_counter() - t0) * 1000.0,
        )

    _PARSER_CACHE_MISSES += 1
    res = _parse_geometry_problem_locally_uncached(problem_text, t0)
    if len(cache_key[1]) <= 4096:
        _PARSER_CACHE[cache_key] = LocalParseResult(
            parser_version=res.parser_version,
            status=res.status,
            payload=copy.deepcopy(res.payload) if res.payload is not None else None,
            parsed_contract=res.parsed_contract,
            ast=dict(res.ast),
            source_coverage=res.source_coverage,
            reason_code=res.reason_code,
            fallback_reason=res.fallback_reason,
            parse_latency_ms=res.parse_latency_ms,
        )
        while len(_PARSER_CACHE) > MAX_PARSER_CACHE_SIZE:
            _PARSER_CACHE.popitem(last=False)
    return res
