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

from ..simulation.geometry.expression import (
    AREA,
    LENGTH,
    SCALAR,
    VOLUME,
    ExprDimensionError,
    ExprDomainError,
    ExprParseError,
    SlotQuantityEntry,
    SymbolEnvironment,
    parse_quantity_expr,
)
from ..simulation.geometry_functions import TuChoi, planner, registry
from ..simulation.geometry_functions.typed_fact_next import (
    TypedFactNextPayloadV2,
    TypedFactNextValidationError,
    parse_typed_fact_next_v2,
    premise_slot_dimension,
)
from ..simulation.geometry_functions.typed_fact_next_bridge import bridge_v2
from ..simulation.semantic_program.domain_profile import DOMAIN_HINH_HOC, detect_domain

from .compositional_clause_analysis import (
    CONTEXT_HEADER_RE,
    INLINE_EXAM_HEADER_PREFIX_RE,
    INLINE_LEADING_META_RE,
    INLINE_TRAILING_META_RE,
    META_NO_CALC_RE,
    analyze_compositional_geometry,
)

LOCAL_GEOMETRY_PARSER_VERSION = "local-geometry-parser/3"

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
#: Lead of a NAMED base polygon "có / với / biết (rằng) ABCD là hình …" (/13 adds "biết (rằng)"); the quote starts at the
#: labels, and the rules using it require the labels to be the declared solid's base.
_BASE_NAMED_LEAD = r"(?:(?:có|với|và|biết(?:\s+rằng)?)\s+|(?<=[,;]\s))"
_W_NO_SUP = r"[^\W²³']"
_PAREN_UNIT_RE = r"\s*(?:đơn\s+vị(?:\s+(?:độ\s+dài|diện\s+tích|thể\s+tích|góc))?\s*:?\s*)?(?:(?-i:mm|cm|dm|km|m)|đvđd|đvdt|đvtt|°|độ|radian|rad)(?:\s*(?:[²³]|\^\s*[23]|[23]))?\s*\)"
_ATTACHED_UNIT_RE = r"(?=(?:(?-i:mm|cm|dm|km|m)(?:\s*(?:[²³]|\^\s*[23]|[23]))?|đvđd|đvdt|đvtt|°|độ|radian|rad)(?!" + _W_NO_SUP + r")(?![²³^0-9]))"
_EXPR_END_BOUND = (
    r"(?:(?<=[0-9²³)])" + _ATTACHED_UNIT_RE
    + r"|(?<=[a-z])(?=°(?!" + _W_NO_SUP + r"))"
    + r"|(?!" + _W_NO_SUP + r")(?![²³^°~√]))(?![.,]\d)"
)
_EXPR_ATOM = (
    r"(?:"
    r"\d+(?:[.,]\d+(?![.,]\d))?"
    r"|(?:√|(?-i:sqrt))\s*(?:\((?!" + _PAREN_UNIT_RE + r")(?-i:[0-9a-z.,+\-*/^²³√\s]+)\)|\d+(?:[.,]\d+(?![.,]\d))?|(?-i:[a-z])(?!" + _W_NO_SUP + r"))"
    r"|\((?!" + _PAREN_UNIT_RE + r")(?=(?-i:[0-9a-z.,+\-*/^²³√\s]*[0-9√²³^+\-*/]))(?-i:[0-9a-z.,+\-*/^²³√\s]+)\)"
    r"|\((?-i:[a-z])\)(?=\s*(?:[²³]|\^\s*[23]))"
    r"|(?-i:[a-z])(?!" + _W_NO_SUP + r")"
    r")(?:\s*(?:[²³]|\^\s*[23]))?"
)
#: Dimension-aware mathematical quantity expression (`dimension-expression/1`): exact decimals, fractions, radicals,
#: powers (`²`, `³`, `^2`, `^3`), parenthesized sub-expressions, and lowercase symbolic parameters (`a`, `x`, ...),
#: cleanly separated from trailing metric units (`cm`, `cm²`, `m³`, `(cm²)`) and rejecting comma-lists (`3,5,6`) or
#: glued non-unit identifiers (`a2`, `a²ln2`).
_VAL = (
    r"(?:"
    + _EXPR_ATOM
    + r"(?:(?:\s*[*/]\s*|(?=[√]|(?:\((?!" + _PAREN_UNIT_RE + r"))|(?-i:[a-ln-z])(?!" + _W_NO_SUP + r")))" + _EXPR_ATOM
    + r"|(?:\s*[+\-]\s*)" + _EXPR_ATOM + r")*"
    + r")" + _EXPR_END_BOUND
)
_SCALAR_VAL = (
    r"(?:\d+(?:[.,]\d+(?![.,]\d))?(?:\s*√\s*(?:\(\s*\d+\s*\)|\d+))?|√\s*(?:\(\s*\d+\s*\)|\d+))"
    r"(?:\s*/\s*(?:\d+(?:[.,]\d+(?![.,]\d))?|√\s*(?:\(\s*\d+\s*\)|\d+)))?"
    + _EXPR_END_BOUND
)
_SCALAR_COEFF = (
    r"(?:\d+(?:[.,]\d+(?![.,]\d))?(?:\s*√\s*(?:\(\s*\d+\s*\)|\d+))?|√\s*(?:\(\s*\d+\s*\)|\d+))"
    r"(?:\s*/\s*(?:\d+(?:[.,]\d+(?![.,]\d))?|√\s*(?:\(\s*\d+\s*\)|\d+)))?"
    r"(?!\d|[.,]\d|(?-i:[a-z])|[²³^])"
)
_OPT_ANY_UNIT_TAIL = (
    r"(?:\s*(?:\(\s*(?:đơn\s+vị(?:\s+(?:độ\s+dài|diện\s+tích|thể\s+tích|góc))?\s*:?\s*)?"
    r"(?:(?-i:mm|cm|dm|km|m)(?:\s*(?:2|\^2|²|3|\^3|³))?|đvđd|đvdt|đvtt|°|độ|radian|rad)\s*\)"
    r"|(?:(?-i:mm|cm|dm|km|m)(?:\s*(?:2|\^2|²|3|\^3|³))?|đvđd|đvdt|đvtt|°|độ|radian|rad)(?!" + _W_NO_SUP + r")(?![²³^0-9])))?"
)
_OPT_LEN_UNIT_TAIL = _OPT_ANY_UNIT_TAIL
_OPT_AREA_UNIT_TAIL = _OPT_ANY_UNIT_TAIL
_OPT_VOL_UNIT_TAIL = _OPT_ANY_UNIT_TAIL
_DEG_OR_WRONG_DIM_UNIT_TAIL = (
    r"\s*(?:°|độ\b"
    r"|\(\s*(?:đơn\s+vị(?:\s+(?:độ\s+dài|diện\s+tích|thể\s+tích))?\s*:?\s*)?"
    r"(?:(?-i:mm|cm|dm|km|m)(?:\s*(?:2|\^2|²|3|\^3|³))?|đvđd|đvdt|đvtt)\s*\)"
    r"|(?:(?-i:mm|cm|dm|km|m)(?:\s*(?:2|\^2|²|3|\^3|³))?|đvđd|đvdt|đvtt)(?!" + _W_NO_SUP + r")(?![²³^0-9]))"
)


def _canon_val(v: str) -> str:
    """Canonicalize textbook `√3a` / `2√3x` into `a√3` / `2x√3` while preserving structured AST forms (`a²`, `(2a)²`, `√(3a)`)."""
    s = v.strip()
    m = re.fullmatch(r"(?P<k>\d*)√(?P<r>\d+)(?P<sym>(?-i:[a-z]))(?P<d>/\d+)?", s)
    if m:
        return f"{m.group('k')}{m.group('sym')}√{m.group('r')}{m.group('d') or ''}"
    return s


def _is_valid_val(v: str | None) -> bool:
    if not v or not v.strip():
        return False
    try:
        parse_quantity_expr(_canon_val(v), allow_signed=True, allow_unit=False)
        return True
    except ExprParseError:
        return False


def _is_valid_scalar_val(v: str | None) -> bool:
    if not v or not v.strip():
        return False
    try:
        q = parse_quantity_expr(_canon_val(v), allow_signed=True, allow_unit=False)
        return not q.referenced_symbols
    except ExprParseError:
        return False


_TRIG_KW_RE = r"(?:sin|cos|côsin|cosin|tan|tang|tg|cot|côtang|cotang|cotg)"
_ANGLE_OBJ_PLANE_RE = (
    rf"(?:(?:mặt\s+phẳng|mặt\s+bên|mặt|mp)\s*\({_PTS3_6}\)"
    rf"|\({_PTS3_6}\)"
    rf"|(?:mặt\s+phẳng|mặt\s+bên|mặt|mp)\s+{_PTS3_6}(?![\w'])"
    rf"|(?:mặt\s+phẳng\s+đáy|mặt\s+đáy|đáy)(?:\s*\(?{_PTS3_6}\)?)?(?!\w)"
    rf"|(?:(?:mặt\s+phẳng|mp)\s*)?\((?:[A-Z]|[α-ω])'?\))"
)
_ANGLE_OBJ_LINE_RE = (
    rf"(?:(?:(?:đường\s+thẳng|cạnh(?:\s+bên|\s+đáy)?|đoạn(?:\s+thẳng)?|tia|đường\s+cao|đường\s+chéo|đường\s+sinh|trục)\s+)?{_PTS2}(?![\w'])"
    rf"|(?:cạnh\s+bên|cạnh\s+đáy|đường\s+cao|chiều\s+cao|đường\s+sinh|trục)(?!\w)"
    rf"|đường\s+thẳng\s+\(?(?-i:[a-zΔ∆])'?\)?(?![\w']))"
)
_ANGLE_OR_RATIO_OPERAND_PREFIX_RE = re.compile(
    rf"(?:(?<!vuông\s)(?<!\w)góc\s+(?:giữa|tạo\s+bởi|hợp\s+bởi)\s+"
    rf"(?:hai\s+(?:đường\s+thẳng|mặt\s+phẳng|cạnh(?:\s+bên|\s+đáy)?|mặt\s+bên)\s+)?"
    rf"(?:{_ANGLE_OBJ_PLANE_RE}|{_ANGLE_OBJ_LINE_RE})\s+(?:và|với)\s+"
    rf"(?:(?:đường\s+thẳng|cạnh(?:\s+bên|\s+đáy)?|đoạn(?:\s+thẳng)?|tia|đường\s+cao|đường\s+chéo|đường\s+sinh)\s+)?"
    rf"|(?<!vuông\s)(?<!\w)góc\s+nhị\s+diện\s+(?:theo\s+)?cạnh\s+"
    rf"|(?:tỉ|tỷ)\s+số(?:\s+độ\s+dài)?(?:\s+(?:giữa|của))?(?:\s+hai)?(?:\s+(?:cạnh|đoạn(?:\s+thẳng)?))?\s+"
    rf"(?:(?:cạnh|đoạn(?:\s+thẳng)?)\s+)?(?:{_PTS2}|cạnh\s+bên|cạnh\s+đáy)\s+(?:và|với)\s+(?:(?:cạnh|đoạn(?:\s+thẳng)?)\s+)?)\s*$",
    re.IGNORECASE | re.UNICODE,
)


def _canon_trig_unit(raw_fn: str) -> str:
    fn = unicodedata.normalize("NFC", raw_fn.strip().lower())
    if fn == "sin":
        return "sin"
    if fn in ("cos", "côsin", "cosin"):
        return "cos"
    if fn in ("tan", "tang", "tg"):
        return "tan"
    if fn in ("cot", "côtang", "cotang", "cotg"):
        return "cot"
    raise ValueError(f"unsupported trig function keyword {raw_fn!r}")

_TOKEN_RE = re.compile(
    rf"(?P<solid>{_PT}\.{_PTS3_6}|{_PTS3_6}\.{_PTS3_6})"
    rf"|(?P<plane>\((?:{_PTS3_6}|{_PT}|[α-ω]'?)\))"
    rf"|(?P<value>{_VAL})"
    rf"|(?P<op>[⊥∥=])"
    rf"|(?P<label>{_PT}(?:{_PT})*)"
    rf"|(?P<word>[^\s,.;:?!()]+)",
    re.UNICODE,
)


_DIM_ATTR = r"(?P<item>(?:độ\s+dài\s+(?:của\s+)?)?(?P<attr>cạnh\s+đáy|cạnh\s+bên)\s*(?:(?:đều\s+)?(?:bằng|là)\s*|=\s*)?(?P<val>{val}){unit_tail})"
_DIM_FIRST_RE = re.compile(
    rf"(?<![\w'])(?:(?:có|với)\s+)?{_DIM_ATTR.format(val=_VAL, unit_tail=_OPT_LEN_UNIT_TAIL)}",
    re.IGNORECASE | re.UNICODE,
)
_DIM_NEXT_RE = re.compile(
    rf"\s*(?:,\s*|\s+và\s+|\s+có\s+)(?:có\s+)?{_DIM_ATTR.format(val=_VAL, unit_tail=_OPT_LEN_UNIT_TAIL)}",
    re.IGNORECASE | re.UNICODE,
)


def _solid_dimension_items(text: str, start: int) -> list[tuple[str, str, int, int]]:
    """Edge dimensions listed after a regular solid's notation, in any order: `(độ dài) cạnh đáy|cạnh bên (bằng|=|là) VAL`.

    The first item may appear anywhere after `start`; later items must follow it directly, joined by `,`, `và` or `có`.
    Stops at the first gap, at a repeated attribute, or at anything else, so an unread remainder still reaches the
    clause guards and the Source Gate instead of being skipped. Returns (`base`|`lateral`, raw value, attribute start,
    end offset); callers quote the first item from the solid name and later items from their own attribute, so two
    equal values ("cạnh bên bằng a và cạnh đáy bằng a") each sit in exactly one quote.
    """
    m = _DIM_FIRST_RE.search(text, start)
    items: list[tuple[str, str, int, int]] = []
    seen: set[str] = set()
    while m:
        if not _is_valid_val(m.group("val")):
            break
        attr = "lateral" if "bên" in m.group("attr").lower() else "base"
        if attr in seen:
            break
        seen.add(attr)
        items.append((attr, m.group("val"), m.start("item"), m.end()))
        m = _DIM_NEXT_RE.match(text, m.end())
    return items


_BARE_SEGMENT_EQUALITY_RE = re.compile(
    rf"(?P<full>(?<![\w'.=])(?P<s1>{_PTS2})\s*=\s*(?P<s2>{_PTS2})(?:\s*=\s*(?P<s3>{_PTS2}))?)(?![\w'])(?!\s*=)",
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

_TRAILING_MC_OPTIONS_RE = re.compile(
    r"(?P<stem_end>(?:(?<!\w)(?i:bằng|là)|[.?:)])\s*:?)"
    r"\s+(?<![\w'])A\s*[.)]\s*\S.*?"
    r"\s+(?<![\w'])B\s*[.)]\s*\S.*?"
    r"\s+(?<![\w'])C\s*[.)]\s*\S.*?"
    r"\s+(?<![\w'])D\s*[.)]\s*\S+\s*$",
    re.DOTALL,
)

_TRAILING_PARTIAL_MC_RE = re.compile(
    r"(?P<stem_end>(?:(?<!\w)(?i:bằng|là)|[.?:)])\s*:?)"
    r"\s+(?<![\w'])[A-D]\s*[.)]\s*(?:\d|(?i:[a-z0-9²³√π/]+\b))[^\n]*\s*$"
)

_COMPUTABLE_LATER_SUBQ_RE = re.compile(
    r"(?m)^\s*[b-d][.)]\s+.*?\b(?i:tính|khoảng\s+cách|thể\s+tích|diện\s+tích|tỉ\s+số)\b"
)

_PURE_PROOF_OR_INTERSECTION_SUBQ_LINE_RE = re.compile(
    r"(?m)^[ \t]*[a-c][.)]\s+(?!(?:[^\n]*\b(?i:gọi|biết|sao\s+cho|giả\s+sử|lấy|cho)\b|[^\n]*=))"
    r"(?i:chứng\s+m[iì]nh\b|tìm\s+giao\s+tuyến\s+của\s+hai\s+mặt\s+phẳng\b)[^\n.?!]*[.?!]?[ \t]*\n?"
)


_MC_OPT_MARKER_RE = re.compile(r"(?:^|(?<=[\s:]))(?<![\w'])[A-D]\s*[.)](?=\s*\S)")
_MC_FORBID_SENTENCE_RE = re.compile(
    r"\b(?:cho|gọi|biết|giả\s+sử|tính|tìm|xác\s+định|chứng\s+minh|dựng|lấy|kẻ|hỏi|cắt|vuông\s+góc|song\s+song|trung\s+điểm|trọng\s+tâm)\b",
    re.IGNORECASE | re.UNICODE,
)


def strip_mc_options_block(text: str) -> str:
    """Strip trailing multiple-choice option tails (`A. ...`, including partial `\n`-delimited rows with dropped `A.`) without touching geometry subquestions."""
    if not text:
        return ""
    s = _TRAILING_MC_OPTIONS_RE.sub(r"\g<stem_end>", text)
    s = _TRAILING_PARTIAL_MC_RE.sub(r"\g<stem_end>", s)
    if (nl := s.rfind("\n")) >= 0:
        tail_line = s[nl + 1 :]
        if (
            re.search(r"(?<![\w'])B\s*[.)]\s*\S.*(?<![\w'])C\s*[.)]\s*\S", tail_line)
            and not _MC_FORBID_SENTENCE_RE.search(tail_line)
        ):
            s = s[:nl].rstrip()
    for m_start in re.finditer(r"(?P<stem_end>(?:(?<!\w)(?i:bằng|là)|[.?:)]|\n)\s*:?)\s+(?=(?<![\w'])[A-D]\s*[.)]\s*\S)", s):
        tail = s[m_start.end("stem_end") :]
        markers = [m.group(0).strip()[0] for m in _MC_OPT_MARKER_RE.finditer(tail)]
        if len(set(markers)) >= 2 and not _MC_FORBID_SENTENCE_RE.search(tail):
            s = s[: m_start.end("stem_end")].strip()
            break
    s = re.sub(r"\n\s*[A-D]\s*[.]\s*$", "", s).rstrip()
    return s


def normalize_problem_text(problem_text: str) -> str:
    """Unicode NFC normalization preserving character alignment for standard Vietnamese text, stripping trailing MC options."""
    s = unicodedata.normalize("NFC", problem_text or "").replace("\u2032", "'")
    s = re.sub(r"(?<=\d)º", "°", s)
    # /14: "⟂" (U+27C2 PERPENDICULAR, from Word / LaTeX \perp) is the relation every reader here knows as "⊥" (U+22A5);
    # NFC/NFKC map neither to the other. One character for one, so offsets and quotes are kept.
    s = s.replace("⟂", "⊥")
    s = re.sub(r"(?m)^(\s*(?:Câu|Bài)\s+\d+)\s*\((?:VD|VDC|TH|NB)\)\s*:?\s*", r"\1: ", s, flags=re.IGNORECASE)
    s = re.sub(r"[Δ∆△]\s*(?=[A-Z]{3}\b)", "tam giác ", s)
    s = re.sub(r"(?m)^(\s*[a-d])\.(?=\s+[A-ZĐÀ-Ỹ])", r"\1)", s)
    s = re.sub(r"\b([A-Z][0-9']*)\.([A-Z][0-9']*)(?=\s+(?i:là|thuộc|nằm)\b)", r"\1. \2", s)
    if _COMPUTABLE_LATER_SUBQ_RE.search(s):
        s = _PURE_PROOF_OR_INTERSECTION_SUBQ_LINE_RE.sub("", s)
    return strip_mc_options_block(s)


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
    for m_split in re.finditer(
        r"(?<=[0-9a-zA-Z'°²³\)])(?<!:)(?<!,)(?<!;)\s+(?=(?-i:(?:Khoảng\s+cách|Thể\s+tích|Diện\s+tích|Số\s+đo|Góc|Tính|Tìm|Xác\s+định)\b))",
        text,
    ):
        before_tail = text[: m_split.start()].rstrip().lower()
        if re.search(r"(?:^|\b(?:và|rồi|thì|nên|hãy|em|của|là|tức|về|với|theo|hoặc|biết|rằng))$", before_tail):
            continue
        after = text[m_split.end() :]
        if re.match(
            r"(?:Khoảng\s+cách\s+(?:từ|giữa)|Thể\s+tích\b|Diện\s+tích\b|Số\s+đo\b|Góc\s+(?:giữa|tạo|hợp)|(?:Tính|Tìm|Xác\s+định)\s+(?:thể|diện|khoảng|góc|độ|tỉ|tỷ|thiết))",
            after,
        ):
            bounds.append(m_split.end())
    bounds.append(n)
    bounds = sorted(set(bounds))
    out: list[tuple[int, int, str]] = []
    for a, b in zip(bounds, bounds[1:]):
        while a < b and text[a].isspace():
            a += 1
        while b > a and (text[b - 1].isspace() or text[b - 1] in ".;?!"):
            b -= 1
        # Nhãn câu hỏi con ở đầu dòng ("a. Tính …", "b) Chứng minh …") là cấu trúc trình bày, không phải mệnh đề.
        at_line_start = a == 0 or text[:a].rstrip(" \t").endswith("\n")
        if at_line_start and a < b:
            if re.fullmatch(r"[a-d]", text[a:b]) and re.match(r"\.\s+[A-ZĐÀ-Ỹ]", text[b:]):
                continue
            m_sub = re.match(r"[a-d]\)\s+(?=[A-ZĐÀ-Ỹ])", text[a:b])
            if m_sub:
                a += m_sub.end()
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
    r"(?:^|\b)(?:tính|tìm|xác\s+định|hỏi|hãy\s+cho\s+biết|cho\s+(?:em|mình|tôi|tớ|bạn)\s+biết|dựng|vẽ|mô\s+phỏng|cho\s+mình\s+xem|chứng\s+minh|bao\s+nhiêu|mấy)\b|\?|(?<!\w)(?:bằng|là)\s*:?\s*$",
    re.IGNORECASE | re.UNICODE,
)

_FACT_INDICATOR_RE = re.compile(
    r"\b(?:cho|hình\s+chóp|hình\s+lăng\s+trụ|lăng\s+trụ|tứ\s+diện|hình\s+lập\s+phương|hình\s+hộp|"
    r"mặt\s+cầu|khối\s+cầu|hình\s+trụ|hình\s+nón|đáy|vuông\s+góc|song\s+song|trung\s+điểm|trọng\s+tâm|"
    r"hình\s+chiếu|giao\s+điểm|mặt\s+phẳng|cạnh|chiều\s+cao|đường\s+cao|đường\s+sinh|bán\s+kính|"
    r"diện\s+tích|thể\s+tích|tỉ\s+số|tỷ\s+số|gọi|biết)\b|[⊥∥=]",
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


def _iter_top_splits(s: str, sep_pat: str = r"\s+(?:và|với)\s+") -> list[tuple[str, int, str, int]]:
    """Return every binary split `(left, left_off, right, right_off)` across top-level connectors in `s`."""
    return [
        (s[: m.start()], 0, s[m.end() :], m.end())
        for m in re.finditer(sep_pat, s, re.IGNORECASE | re.UNICODE)
    ]


_TRAILING_GOAL_META_RE = re.compile(
    r"(?:\s*(?:có\s+(?:số\s+đo|giá\s+trị|độ\s+dài)\s+|có\s+)?(?:bằng|là)\s+bao\s+nhiêu(?:\s+(?:độ|radian|rad))?"
    r"|\s*(?:bằng|là)\s*:?\s*[.?]?"
    r"|\s*(?:theo|bằng|tính\s+bằng)\s+(?:(?:đơn\s+vị(?:\s+(?:độ\s+dài|diện\s+tích|thể\s+tích|góc))?\s+)?(?:độ|radian|rad|đvđd|đvdt|đvtt|mm²|cm²|dm²|km²|m²|mm³|cm³|dm³|km³|m³|mm|cm|dm|km|m)|(?-i:[a-z])(?![\w']))"
    r"|\s*\(\s*(?:(?:đơn\s+vị|kết\s+quả|làm\s+tròn|(?:hình\s+)?minh\s+h[ọo]a|tham\s+khảo|như|xem|hình\s+vẽ)[^()]*)\s*\)"
    r"|\s*(?:kết\s+quả\s+)?làm\s+tròn[^.;?!]*"
    r"|\s*[.?])+\s*$",
    re.IGNORECASE | re.UNICODE,
)

_NEXT_GOAL_LOOKAHEAD = (
    r"(?=(?:(?:\s*,\s*(?:(?:và|rồi)\s+)?|\s+(?:và|rồi)\s+)(?:(?:tính|tìm|xác\s+định)\s+)?"
    r"(?:khoảng\s+cách|k/c|độ\s+dài|thể\s+tích|diện\s+tích|(?:số\s+đo\s+(?:của\s+)?)?góc\s+(?:giữa|tạo|hợp|nhị\s+diện)"
    r"|(?:côsin|cosin|cos|sin|tang|tan|côtang|cotang|cot)\b|bán\s+kính|(?:tỉ|tỷ)\s+số|thiết\s+diện|giao\s+tuyến)\b)|$)"
)


def _strip_trailing_goal_meta(s: str) -> str:
    return _TRAILING_GOAL_META_RE.sub("", s).strip()


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
        self._area_symbol_map: dict[str, list[str]] = {}

    def _snapshot(self) -> tuple[int, dict[tuple[Any, ...], str], dict[str, int]]:
        return (len(self.described_points), dict(self._desc_by_key), dict(self._desc_counters))

    def _restore(self, snap: tuple[int, dict[tuple[Any, ...], str], dict[str, int]]) -> None:
        n_dp, by_k, ctrs = snap
        del self.described_points[n_dp:]
        self._desc_by_key = by_k
        self._desc_counters = ctrs

    def _subquote(self, phrase_text: str, approx_start: int) -> str:
        s = phrase_text.strip()
        if not s:
            return ""
        lo = max(0, approx_start - 8)
        hi = min(len(self.raw_text), approx_start + len(s) + 24)
        idx = self.raw_text.find(s, lo, hi)
        if idx >= 0:
            return _clean_quote(self.raw_text, idx, idx + len(s))
        return _clean_quote(self.raw_text, approx_start, approx_start + len(s))

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
        q_key = re.sub(r"\s+", " ", str(spec.get("quote") or "")).strip().lower()
        key = (
            spec["kind"],
            tuple(spec.get("segment") or ()),
            tuple(spec.get("polygon") or ()),
            spec.get("point"),
            tuple(spec.get("line") or ()),
            tuple(spec.get("plane") or ()),
            tuple(spec.get("line1") or ()),
            tuple(spec.get("line2") or ()),
            q_key,
        )
        if key in self._desc_by_key:
            return f"@{self._desc_by_key[key]}"
        did = self._alloc_desc_id(spec["kind"])
        full = {"described_id": did, **spec}
        self.described_points.append(full)
        self._desc_by_key[key] = did
        return f"@{did}"

    def parse_plane_or_base(self, phrase: str) -> list[str] | None:
        s = phrase.strip()
        m_pl = re.fullmatch(
            rf"(?:(?:mặt\s+phẳng|mp|mặt\s+bên|mặt\s+đáy)\s*)?\((?P<pl>{_PTS3_6})\)"
            rf"|(?:mặt\s+phẳng|mp|mặt\s+bên|mặt\s+đáy)\s+(?P<pl_nb>{_PTS3_6})(?![\w'])"
            rf"|(?P<pld>(?:mặt\s+phẳng\s+|mặt\s+)?đáy)(?![\w'])",
            s,
            re.IGNORECASE | re.UNICODE,
        )
        if not m_pl:
            return None
        if m_pl.group("pl") or m_pl.group("pl_nb"):
            pts = _split_pts(m_pl.group("pl") or m_pl.group("pl_nb"))
            return pts if len(set(pts)) >= 3 else None
        return list(self._base_vertices) if len(self._base_vertices) >= 3 else None

    def parse_line_or_described(self, phrase: str, phrase_start_in_raw: int, depth: int = 0) -> list[str] | None:
        """Resolve either a named segment (`AB`, `đường thẳng SC`) or an endpoint-described line (`nối @a với @b`)."""
        if depth > 3:
            return None
        lpad = len(phrase) - len(phrase.lstrip())
        s = phrase.strip()
        start = phrase_start_in_raw + lpad
        m_named = re.fullmatch(
            rf"(?:(?:đường\s+thẳng|đt|cạnh(?:\s+bên|\s+đáy)?|đoạn(?:\s+thẳng)?)\s+)?(?P<pts>{_PTS2})(?![\w'])",
            s,
            re.IGNORECASE | re.UNICODE,
        )
        if m_named:
            pts = _split_pts(m_named.group("pts"))
            return pts if len(pts) == 2 and len(set(pts)) == 2 else None
        m_join = re.fullmatch(
            r"(?:(?:đường\s+thẳng|đt|đoạn(?:\s+thẳng)?)\s+)?(?:nối|đi\s+qua)\s+(?P<body>.+)",
            s,
            re.IGNORECASE | re.UNICODE,
        )
        if m_join:
            body = m_join.group("body")
            body_off = start + m_join.start("body")
            for a_s, ao, b_s, bo in _iter_top_splits(body):
                snap = self._snapshot()
                ra = self.parse_point_or_described(a_s, body_off + ao, depth + 1)
                rb = self.parse_point_or_described(b_s, body_off + bo, depth + 1) if ra else None
                if ra and rb and ra != rb:
                    return [ra, rb]
                self._restore(snap)
        return None

    def parse_point_or_described(self, phrase: str, phrase_start_in_raw: int, depth: int = 0) -> str | None:
        """Resolve either a single vertex label (e.g. `A` or `điểm A`) or a composable described point (`@m1`, depth <= 3)."""
        if depth > 3:
            return None
        lpad = len(phrase) - len(phrase.lstrip())
        s = phrase.strip()
        start = phrase_start_in_raw + lpad
        m_pt = re.fullmatch(rf"(?:điểm\s+)?(?P<p>{_PT})", s, re.IGNORECASE | re.UNICODE)
        if m_pt:
            return m_pt.group("p").replace("′", "'")

        # Recursive orthogonal projection onto plane or line (try splits right-to-left for nested descriptors)
        if re.match(r"hình\s+chiếu\b", s, re.IGNORECASE):
            for m_head in [re.match(r"hình\s+chiếu(?:\s+vuông\s+góc)?\s+của(?:\s+điểm)?\s+", s, re.IGNORECASE | re.UNICODE)]:
                if not m_head:
                    continue
                rest = s[m_head.end() :]
                rest_off = start + m_head.end()
                for sp in reversed(list(re.finditer(r"\s+(?:lên|trên)\s+", rest, re.IGNORECASE | re.UNICODE))):
                    pt_s = rest[: sp.start()]
                    dst_s = rest[sp.end() :]
                    dst_off = rest_off + sp.end()
                    snap = self._snapshot()
                    pl = self.parse_plane_or_base(dst_s)
                    if pl:
                        pt_ref = self.parse_point_or_described(pt_s, rest_off, depth + 1)
                        if pt_ref:
                            q_outer = self._subquote(s, start)
                            return self._register_described_point(
                                {"kind": "orthogonal_projection", "point": pt_ref, "plane": pl, "quote": q_outer}
                            )
                        self._restore(snap)
                        continue
                    ln_refs = self.parse_line_or_described(dst_s, dst_off, depth + 1)
                    pt_ref = self.parse_point_or_described(pt_s, rest_off, depth + 1) if ln_refs else None
                    if pt_ref and ln_refs:
                        q_outer = self._subquote(s, start)
                        return self._register_described_point(
                            {"kind": "orthogonal_projection_line", "point": pt_ref, "line": ln_refs, "quote": q_outer}
                        )
                    self._restore(snap)

        # Recursive midpoint of segment between two described/named points
        m_mid_join = re.fullmatch(
            r"(?:trung\s+điểm|điểm\s+chính\s+giữa)(?:\s+của)?\s+(?:đoạn\s+thẳng\s+|đoạn\s+|cạnh\s+)?(?:nối|đi\s+qua)\s+(?P<body>.+)",
            s,
            re.IGNORECASE | re.UNICODE,
        )
        if m_mid_join:
            body = m_mid_join.group("body")
            body_off = start + m_mid_join.start("body")
            for a_s, ao, b_s, bo in _iter_top_splits(body):
                snap = self._snapshot()
                ra = self.parse_point_or_described(a_s, body_off + ao, depth + 1)
                rb = self.parse_point_or_described(b_s, body_off + bo, depth + 1) if ra else None
                if ra and rb and ra != rb:
                    q_outer = self._subquote(s, start)
                    return self._register_described_point({"kind": "midpoint", "segment": [ra, rb], "quote": q_outer})
                self._restore(snap)

        # Recursive intersection of line (possibly described) and plane, or two lines (possibly described)
        m_int_pl = re.fullmatch(
            rf"giao\s+điểm(?:\s+của)?\s+(?P<line>.+?)\s+(?:và|với)\s+(?:(?:mặt\s+phẳng|mp|mặt\s+bên|mặt\s+đáy)\s*)?\((?P<plane>{_PTS3_6})\)",
            s,
            re.IGNORECASE | re.UNICODE,
        )
        if m_int_pl:
            snap = self._snapshot()
            ln_refs = self.parse_line_or_described(m_int_pl.group("line"), start + m_int_pl.start("line"), depth + 1)
            pl_pts = _split_pts(m_int_pl.group("plane"))
            if ln_refs and len(set(pl_pts)) >= 3:
                q_outer = self._subquote(s, start)
                return self._register_described_point(
                    {"kind": "intersect_line_plane", "line": ln_refs, "plane": pl_pts, "quote": q_outer}
                )
            self._restore(snap)

        m_int_ll = re.fullmatch(
            r"giao\s+điểm(?:\s+của)?(?:\s+hai\s+đường\s+thẳng)?\s+(?P<body>.+)",
            s,
            re.IGNORECASE | re.UNICODE,
        )
        if m_int_ll:
            body = m_int_ll.group("body")
            body_off = start + m_int_ll.start("body")
            for l1_s, o1, l2_s, o2 in _iter_top_splits(body):
                snap = self._snapshot()
                l1 = self.parse_line_or_described(l1_s, body_off + o1, depth + 1)
                l2 = self.parse_line_or_described(l2_s, body_off + o2, depth + 1) if l1 else None
                if l1 and l2 and set(l1) != set(l2):
                    q_outer = self._subquote(s, start)
                    return self._register_described_point(
                        {"kind": "intersect_line_line", "line1": l1, "line2": l2, "quote": q_outer}
                    )
                self._restore(snap)

        # Depth-1 leaf described point patterns
        for kind, pat in _DESC_LEAF_PATTERNS:
            m = pat.fullmatch(s)
            if m:
                q = self._subquote(s, start)
                if kind == "midpoint":
                    seg_str = m.group("seg") or m.group("seg2")
                    return self._register_described_point({"kind": "midpoint", "segment": _split_pts(seg_str), "quote": q})
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


#: A comma joins two sub-clauses unless it separates two bare labels of one list ("M, N lần lượt", "SA, SB") or sits
#: inside a number ("3,5a") or brackets ("[S, BC, A]", "(ABC)"). Parts with no geometric content are discourse.
_SUBCLAUSE_LABEL_RE = re.compile(r"(?:[A-Z][0-9]*'?)+")
_SUBCLAUSE_CONTENT_RE = re.compile(
    r"[A-Z]|\b(?:vuông|song\s+song|bằng|trung\s+điểm|trọng\s+tâm|thuộc|nằm|cắt|đều|cân|đáy|cạnh|góc|chiều\s+cao|đường\s+cao|"
    r"diện\s+tích|thể\s+tích|tỉ\s+số|tỷ\s+số|mặt\s+phẳng|đi\s+qua|chứa|tâm|bán\s+kính|tính|tìm|xác\s+định|dựng)\b|[=⊥∥√°]",
    re.IGNORECASE | re.UNICODE,
)


#: Rule 7b grammar of a request to SHOW the built figure (/11, shared vocabulary with the Source Gate's `_VAT_MO_PHONG`):
#: a show verb, then the figure or a declared solid by its kind words (+ optional notation, deixis, extra points) and a
#: content-free tail. It asks nothing and states no fact; whether a kind word is TRUE of the solid is the Source Gate's
#: claim check, which solid it names is `_sim_request_target`. Negated ("Không/Đừng …") or conditional requests never match.
_SIM_VERB = (r"(?:(?:em|bạn)\s+)?(?:hãy\s+)?(?:chỉ\s+cần\s+)?(?:vẽ|dựng|mô\s+phỏng|minh\s+ho[ạa]|biểu\s+diễn|hiển\s+thị"
             r"|cho\s+(?:mình|em|tôi|tớ)\s+xem)(?:\s+giúp(?:\s+(?:mình|em|tôi|tớ))?|\s+lại)?")
_SIM_SOLID = (rf"(?:(?:(?:mô\s+)?hình\s+3D)\s+(?:của\s+)?)?(?:(?:hình|khối)\s+)?(?P<kn>chóp|lăng\s+trụ|hộp(?:\s+chữ\s+nhật)?|lập\s+phương|tứ\s+diện)"
              rf"(?:\s+(?:đứng|đều|xiên|tam\s+giác|tứ\s+giác|ngũ\s+giác|lục\s+giác|chữ\s+nhật))*"
              rf"(?:\s+(?P<lbl>(?:{_PT})+(?:\.(?:{_PT})+)?))?(?![\w'])(?:\s+(?:đứng|đều|xiên))*")
_SIM_FIGURE = r"(?P<fig>hình(?:\s+(?:vẽ|3D|không\s+gian|ba\s+chiều))?(?:\s+theo\s+giả\s+thiết(?:\s+(?:trên|đã\s+cho))?)?)"
_SIM_SEG = rf"(?:(?:đường\s+cao|chiều\s+cao|cạnh(?:\s+(?:bên|đáy))?|đoạn(?:\s+thẳng)?|đường\s+chéo)\s+{_PTS2}(?![\w']))"
_SIM_PTS = rf"(?:(?:các\s+)?(?:điểm|đỉnh)\s+{_PT}(?:\s*(?:,|và)\s*{_PT})*)"
_SIM_EXTRA_ITEM = rf"(?:{_SIM_SEG}|{_SIM_PTS})"
_SIM_JOIN = r"(?:\s*,\s*(?:và\s+)?|\s+(?:và|cùng(?:\s+với)?)\s+)"
_SIM_CORE = rf"(?:{_SIM_SOLID}|{_SIM_FIGURE})(?P<deix>\s+(?:này|đó|đã\s+cho|trên))?(?![\w'])"
_SIM_OBJECT = (
    rf"(?:{_SIM_EXTRA_ITEM}{_SIM_JOIN})*{_SIM_CORE}"
    rf"(?:{_SIM_JOIN}{_SIM_EXTRA_ITEM})*"
    r"(?:\s*,?\s*(?:và\s+)?(?:không|chưa)\s+cần\s+tính(?:\s+toán|\s+gì(?:\s+thêm)?)?|\s+giúp(?:\s+(?:mình|em|tôi|tớ))?)*"
)
_SIM_REQUEST_RE = re.compile(
    rf"^\s*(?P<sim>(?:(?:yêu\s+cầu(?:\s+bài\s+toán)?|nhiệm\s+vụ)\s*:\s*)?{_SIM_VERB}\s+{_SIM_OBJECT})"
    r"(?:\s*(?:,\s*)?(?:rồi\s+|và\s+|sau\s+đó\s+|đồng\s+thời\s+)?(?:hãy\s+)?(?P<rest>(?:tính|tìm|xác\s+định|hãy\s+cho\s+biết|cho\s+(?:em|mình|tôi|tớ|bạn)\s+biết)\s+.+))?\s*[!.…]*\s*$",
    re.IGNORECASE | re.UNICODE)
#: a request to SHOW the built figure (rule 7b; the gate reads it whole and it asks nothing): "Hãy mô phỏng hình và điểm H"
_SUBCLAUSE_SHOW_RE = re.compile(rf"{_SIM_VERB}\s+{_SIM_OBJECT}", re.IGNORECASE | re.UNICODE)

_PYRAMID_KIND_WORDS = ("chóp", "tứ diện")


def _sim_request_target(m: re.Match[str], solids: list[dict[str, Any]], primary: str) -> str | None:
    """The declared solid a 7b request names, or None when it names none or more than one (never a guess).
    A notation must equal a declared solid's (as a label set); a kind word with no notation picks the ONLY declared solid of
    that pyramid/prism class; the bare figure ("hình", "hình 3D") is the primary solid, but with deixis ("hình đó") and
    several solids it is ambiguous."""
    if not solids:
        return None
    if m["lbl"]:
        want = set(re.findall(_PT, m["lbl"]))
        hits = [s["solid_id"] for s in solids if set(re.findall(_PT, str(s.get("notation") or ""))) == want]
        return hits[0] if len(hits) == 1 else None
    if m["kn"]:
        pyr = re.sub(r"\s+", " ", m["kn"].lower()) in _PYRAMID_KIND_WORDS
        hits = [s["solid_id"] for s in solids if ("pyramid" in str(s.get("solid_type"))) == pyr]
        return hits[0] if len(hits) == 1 else None
    if m["deix"] and len(solids) > 1:
        return None
    return primary
#: the part before the comma is itself only a list of labels ("M, N thuộc (P)", "Gọi M, N lần lượt …"): a list of subjects
_SUBCLAUSE_SUBJECTS_RE = re.compile(r"(?:(?:Gọi|Cho|các|hai|ba)\s+(?:điểm\s+)?)?(?:(?:[A-Z][0-9]*'?)+\s*,\s*)*(?:[A-Z][0-9]*'?)+",
                                    re.IGNORECASE)
_SUBCLAUSE_VA_RE = re.compile(
    # an object noun ("và điểm M", "và tam giác SBC", "và mặt phẳng (ABC)") is usually the next item of a LIST; it opens a
    # clause only with a predicate of its own
    r"\s(?=và\s+(?:hình\s+chiếu|mặt\s+bên|đáy|cạnh\s+bên|đường\s+cao|chiều\s+cao|"
    r"(?:mặt\s+phẳng\s+|mp\s*)?\([^)]{1,8}\)\s+(?:đi\s+qua|qua|chứa|song|vuông|cắt)|"
    r"(?:tam\s+giác|điểm)\s+(?:[A-Z][0-9]*'?)+\s+(?:là|đều|vuông|cân|thuộc|nằm)|"
    r"(?:[A-Z][0-9]*'?)+\s+(?:là|vuông|song|thuộc|nằm|cắt|đi\s+qua|bằng|=|⊥|∥)))",
    re.UNICODE)


def _subclause_spans(raw: str, a: int, b: int) -> list[tuple[int, int]]:
    """Comma/semicolon-separated parts of `raw[a:b]` (absolute spans), outside brackets and label lists."""
    cuts, depth = [], 0
    for i in range(a, b):
        ch = raw[i]
        depth += ch in "([{"
        depth -= ch in ")]}" and depth > 0
        if ch not in ",;" or depth or i + 1 >= b or not raw[i + 1].isspace():
            continue
        left = re.search(r"(\S+)\s*$", raw[a:i])
        right = re.match(r"\s*(\S+?)(?=[,;.)]|\s|$)", raw[i + 1:b])
        # a list item is followed by list punctuation or a list word ("M, N lần lượt là", "SA, SB và SC"), never by a
        # predicate of its own ("…, SA, N thuộc cạnh SB" is two clauses)
        part = raw[(cuts[-1] + 1) if cuts else a:i].strip()
        if (left and right and _SUBCLAUSE_LABEL_RE.fullmatch(left.group(1).strip("′"))
                and _SUBCLAUSE_LABEL_RE.fullmatch(right.group(1).strip("′"))
                and (re.match(r"(?:\s*(?:[,;.)]|$)|\s+(?:và|lần\s+lượt|là|đôi|cùng|tương\s+ứng)(?!\w))",
                              raw[i + 1 + right.end():b], re.IGNORECASE)
                     or _SUBCLAUSE_SUBJECTS_RE.fullmatch(part))):
            continue
        cuts.append(i)
    # "… SA = a và hình chiếu vuông góc của S …": "và" opening a NEW clause (a clause-opening noun phrase, or a label with
    # its own predicate) joins two sub-clauses too; a "và" inside one relation ("góc giữa SB và (ABC)") is covered by that
    # relation's quote anyway, so an extra cut there never reports a loss
    for m in _SUBCLAUSE_VA_RE.finditer(raw, a, b):
        cuts.append(m.start())
    cuts.sort()
    bounds = [a, *[c + 1 for c in cuts], b]
    return [(x, y - (1 if y != b else 0)) for x, y in zip(bounds, bounds[1:]) if y > x]


def _unread_subclauses(builder: "_AstBuilder", a: int, b: int, pre4: tuple[int, int, int, int],
                       pre3: tuple[int, int, int]) -> list[tuple[int, int]]:
    """Parts of the sentence `raw[a:b]` with geometric content that no quote of an item created by this sentence overlaps."""
    raw = builder.raw_text
    parts = _subclause_spans(raw, a, b)
    if len(parts) < 2:          # one part: the whole-sentence classification above already decided it
        return []
    # items of this sentence, and earlier sections a later sentence may extend (stated intersections carry own quotes)
    items = (builder.solids[pre4[0]:], builder.premises[pre4[1]:], builder.derived_sections,
             builder.math_goals[pre4[3]:], builder.described_points[pre3[0]:], builder.relations[pre3[1]:],
             # rule 7b REPLACES the declaration's auto goal, so a slice from pre3 can be empty; quotes are searched in this
             # sentence only, so the whole list is safe (/11)
             builder.simulation_goals, builder.unresolved)

    def quotes(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "quote" and isinstance(v, str) and v.strip():
                    yield v
                else:
                    yield from quotes(v)
        elif isinstance(x, list):
            for v in x:
                yield from quotes(v)

    spans = []
    for q in {q for group in items for q in quotes(list(group))}:
        p = raw.find(q, a, b + len(q))
        while p >= 0:
            spans.append((p, p + len(q)))
            p = raw.find(q, p + 1, b + len(q))
    lost = []
    for x, y in parts:
        part = _FIG_REF_SUFFIX_RE.sub("", raw[x:y])
        if not _SUBCLAUSE_CONTENT_RE.search(part) or _SUBCLAUSE_SHOW_RE.fullmatch(part.strip()):
            continue
        if not any(s < y and x < e for s, e in spans):
            lost.append((x, y))
    return lost


#: A value written in a premise: a number/decimal-list, a radical, or a symbolic/parenthesized math expression right after "bằng" / "=" / "cạnh" / "là".
_PREMISE_VALUE_RE = re.compile(
    r"(?<![\w'.,])(?:\d+(?:[.,]\d+)*|√\s*\(?\s*(?:\d+|(?-i:[a-z])))"
    r"|(?:(?<=bằng\s)|(?<==\s)|(?<==)|(?<=cạnh\s)|(?<=là\s))(?:\(?\s*[0-9√]|(?-i:\(\s*[a-z])|(?-i:[a-z]+(?:\(|[0-9²³]))|(?-i:[a-z])(?:[0-9²³^+\-*/]|(?![^\W²³'])))",
    re.UNICODE,
)


def _unread_values(builder: "_AstBuilder", a: int, b: int, pre4: tuple[int, int, int, int],
                   pre3: tuple[int, int, int]) -> list[int]:
    """Positions of values in the PREMISE part of sentence `raw[a:b]` (before its question) that no quote of an item
    created by this sentence covers. Exam headers ("Câu 39:") and figure references carry no premise value."""
    raw = builder.raw_text
    stop = b
    if (q := _QUESTION_STARTER_RE.search(raw, a, b)) is not None:
        stop = q.start()
    start = a
    if (h := _EXAM_HEADER_PREFIX_RE.match(raw[a:b])) is not None:
        start = a + h.end()
    items = (builder.solids[pre4[0]:], builder.premises[pre4[1]:], builder.derived_sections,
             builder.math_goals[pre4[3]:], builder.described_points[pre3[0]:], builder.relations[pre3[1]:],
             # rule 7b REPLACES the declaration's auto goal, so a slice from pre3 can be empty; quotes are searched in this
             # sentence only, so the whole list is safe (/11)
             builder.simulation_goals, builder.unresolved)

    def quotes(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "quote" and isinstance(v, str) and v.strip():
                    yield v
                else:
                    yield from quotes(v)
        elif isinstance(x, list):
            for v in x:
                yield from quotes(v)

    spans = []
    for qt in {qt for group in items for qt in quotes(list(group))}:
        p = raw.find(qt, a, b + len(qt))
        while p >= 0:
            spans.append((p, p + len(qt)))
            p = raw.find(qt, p + 1, b + len(qt))
    figs = [(m.start(), m.end()) for m in _FIG_REF_ANY_RE.finditer(raw, a, b)]
    figs.extend((m.start(), m.end()) for m in _FIG_3D_RE.finditer(raw, a, b))
    return [m.start() for m in _PREMISE_VALUE_RE.finditer(raw, start, stop)
            if not any(s <= m.start() < e for s, e in spans) and not any(s <= m.start() < e for s, e in figs)]


def _right_angle_vertex(premises: list[dict[str, Any]], tri: list[str]) -> str | None:
    """The vertex of triangle `tri` at which a premise read so far makes it right-angled, when exactly one does:
    `perpendicular_line_plane(VX, plane ∋ V, Y)` or `right_angle(V; X, Y)` with {V, X, Y} = the triangle."""
    found = set()
    for p in premises:
        a = p.get("args") or {}
        if p.get("kind") == "perpendicular_line_plane" and len(set(a.get("line") or ())) == 2 and set(a["line"]) < set(tri):
            third = (set(tri) - set(a["line"])).pop()
            for v in a["line"]:
                if v in (a.get("plane") or ()) and third in (a.get("plane") or ()):
                    found.add(v)
        elif p.get("kind") == "right_angle" and {a.get("vertex"), *(a.get("rays") or ())} == set(tri):
            found.add(a["vertex"])
    return found.pop() if len(found) == 1 else None


def _detect_length_unit(raw_text: str) -> str:
    # Check if symbolic unit `a` is used in length assignments (e.g. `cạnh a`, `= a`, `= 2a`, `= a√3`, `= √3a`, `chiều cao bằng a`)
    if re.search(
        r"(?:\bcạnh(?:\s+đáy|\s+bên)?(?:\s+bằng)?\s+|\b(?:chiều|đường)\s+cao(?:\s+bằng)?\s+|\=\s*)(?:\d*a(?:√\d+)?(?:/\d+)?|\d*√\d+a(?:/\d+)?)\b",
        raw_text,
    ):
        return "a"
    return "1"


def _infer_length_unit(
    raw_text: str,
    premises: list[dict[str, Any]],
    solids: list[dict[str, Any]],
) -> str:
    """Infer context-driven symbolic length unit (`1`, `a`, `x`, ...) from typed premise/solid quantity slots."""
    entries: list[SlotQuantityEntry] = []
    for idx, p in enumerate(premises, 1):
        args = p.get("args") or {}
        for fname in ("side", "value", "ratio"):
            val = args.get(fname)
            dim = premise_slot_dimension(str(p.get("kind") or ""), fname)
            if isinstance(val, str) and val.strip() and dim is not None and not dim.is_angle:
                entries.append(
                    SlotQuantityEntry(
                        call_id=f"p{idx}",
                        slot_name=fname,
                        value=_canon_val(val),
                        target_dim=dim,
                    )
                )
    for idx, s in enumerate(solids, 1):
        for fname in ("radius", "height"):
            val = s.get(fname)
            if isinstance(val, str) and val.strip():
                entries.append(
                    SlotQuantityEntry(
                        call_id=f"s{idx}",
                        slot_name=fname,
                        value=_canon_val(val),
                        target_dim=LENGTH,
                    )
                )
    if not entries:
        return _detect_length_unit(raw_text)
    try:
        plan = SymbolEnvironment.bind_slots(entries, allow_unit=False)
        return plan.length_unit_symbol or "1"
    except (ExprParseError, ExprDimensionError, ExprDomainError):
        syms: set[str] = set()
        for ent in entries:
            try:
                q = parse_quantity_expr(str(ent.value), allow_signed=True, allow_unit=False)
                syms |= set(q.referenced_symbols)
            except ExprParseError:
                pass
        if len(syms) == 1:
            return next(iter(syms))
        return _detect_length_unit(raw_text)


_EXAM_HEADER_PREFIX_RE = re.compile(
    r"^(?:\s*(?:(?:Câu|Bài(?:\s+tập)?|Ví\s+dụ)\s*(?:\d+|[a-d])\s*[:.)]?|(?:\d+|[a-d])\s*\)|\(\s*\d+(?:[.,]\d+)?\s*điểm\s*\)|(?:đề\s+bài|bài\s+toán)\s*:|trong\s+không\s+gian(?!\s+(?:tọa\s+độ|Oxyz|với\s+hệ))\s*,)\s*)+",
    re.IGNORECASE | re.UNICODE,
)
_FIG_3D_RE = re.compile(r"\bhình\s+3D\b", re.IGNORECASE)
_FIG_REF_ANY_RE = re.compile(
    r"\(\s*(?:(?:hình\s+)?minh\s+h[ọo]a(?:\s+như)?|tham\s+khảo|như|xem)\s+hình(?:\s+vẽ)?(?:\s+bên(?:\s+dưới|\s+trên)?)?\s*\)",
    re.IGNORECASE | re.UNICODE,
)
_FIG_REF_SUFFIX_RE = re.compile(
    r"\s*\(\s*(?:(?:hình\s+)?minh\s+h[ọo]a(?:\s+như)?|tham\s+khảo|như|xem)\s+hình(?:\s+vẽ)?(?:\s+bên(?:\s+dưới|\s+trên)?)?\s*\)\s*$",
    re.IGNORECASE | re.UNICODE,
)


def _emit_proved_polygon_center(
    builder: _AstBuilder,
    pt: str,
    target_verts: list[str],
    quote: str,
) -> bool:
    """§19: Emit exact construction (`midpoint` of opposite vertices or `centroid` for equilateral triangle)
    for explicit polygon center ONLY when `builder.premises` already proves central symmetry or equilateral base."""
    if not pt or not pt[0].isupper() or len(target_verts) < 3 or len(set(target_verts)) != len(target_verts):
        return False
    target_set = frozenset(target_verts)
    if any(
        p.get("kind") in ("trapezoid", "isosceles_trapezoid")
        and frozenset(p.get("args", {}).get("vertices") or ()) == target_set
        for p in builder.premises
    ):
        return False
    for p in builder.premises:
        kind = p.get("kind")
        v = list(p.get("args", {}).get("vertices") or ())
        if frozenset(v) != target_set:
            continue
        if kind == "regular_polygon" and len(v) == 3:
            builder.premises.append(
                {
                    "kind": "centroid",
                    "args": {"point": pt, "polygon": v},
                    "quote": quote,
                    "solid_id": builder._primary_solid_id,
                }
            )
            return True
        if kind in ("regular_polygon", "rectangle", "rhombus", "parallelogram") and len(v) >= 4 and len(v) % 2 == 0:
            builder.premises.append(
                {
                    "kind": "midpoint",
                    "args": {"point": pt, "segment": [v[0], v[len(v) // 2]]},
                    "quote": quote,
                    "solid_id": builder._primary_solid_id,
                }
            )
            return True
    return False


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
    pre_other_lens = (len(builder.described_points), len(builder.relations), len(builder.simulation_goals))

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

    m_bare_sim = re.fullmatch(
        r"(?P<v>Mô\s+phỏng|Vẽ|Dựng|Biểu\s+diễn|Hiển\s+thị|Cho)\s+(?:hình|khối)\s+(?:lăng\s+trụ|chóp|hộp|tứ\s+diện|lập\s+phương)(?:\s+(?:đó|này|đã\s+cho|trên))?",
        ctext_norm.strip(),
        re.IGNORECASE,
    )
    if m_bare_sim:
        if builder.solids and m_bare_sim.group("v").lower() != "cho":
            q = _clean_quote(raw, ca, cb)
            if not builder.simulation_goals:
                builder.simulation_goals.append(
                    {
                        "goal_id": "sg1",
                        "kind": "construct_object",
                        "target_solid_id": builder._primary_solid_id,
                        "quote": q,
                    }
                )
            clause.classification = CLAUSE_MAPPED_GOAL
            return
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

    is_derived_vol_ratio_goal = bool(builder.derived_sections) and bool(
        re.search(r"\b(?:tỉ|tỷ)\s+số\s+thể\s+tích\b", ctext_norm, re.IGNORECASE)
    )
    if not m_two_pyr and not is_derived_vol_ratio_goal:
        m_two_unshared = re.search(
            r"(?:\b(?:Hai|2)\s+(?:hình\s+|khối\s+)?(?:tứ\s+diện|chóp|lăng\s+trụ(?:\s+đứng|\s+đều)?)\s+"
            r"(?P<s1>[A-Z][0-9]*'?(?:\.?[A-Z0-9']+){2,6})\s+và\s+(?:(?:hình\s+|khối\s+)?(?:tứ\s+diện|chóp|lăng\s+trụ(?:\s+đứng|\s+đều)?)\s+)?(?P<s2>[A-Z][0-9]*'?(?:\.?[A-Z0-9']+){2,6})"
            r"|\b(?:hình\s+|khối\s+)?(?:tứ\s+diện|chóp|lăng\s+trụ(?:\s+đứng|\s+đều)?)\s+"
            r"(?P<s3>[A-Z][0-9]*'?(?:\.?[A-Z0-9']+){2,6})\s+và\s+(?:hình\s+|khối\s+)?(?:tứ\s+diện|chóp|lăng\s+trụ(?:\s+đứng|\s+đều)?)\s+(?P<s4>[A-Z][0-9]*'?(?:\.?[A-Z0-9']+){2,6}))(?![A-Z0-9'])",
            ctext_norm,
            re.IGNORECASE | re.UNICODE,
        )
        if m_two_unshared:
            q = _clean_quote(raw, ca + m_two_unshared.start(), ca + m_two_unshared.end())
            builder.unresolved.append(
                {
                    "unresolved_id": f"u{len(builder.unresolved) + 1}",
                    "kind": "ambiguous",
                    "quote": q,
                    "missing_roles": ["target_solid_disambiguation"],
                    "candidate_relations": ["solid"],
                }
            )
            clause.classification = CLAUSE_MAPPED_FACT
            return

    # 1b. Regular pyramid: "(Cho )?(Hình|Khối) chóp (tứ giác|tam giác|lục giác)? đều S.ABCD có cạnh đáy bằng 6..."
    _SOLID_LEAD = (
        r"(?:(?:(?:Em|Mình|Bạn|Tớ)\s+)?(?:(?:muốn|cần)\s+xem"
        r"|(?:(?:Hãy)\s+)?(?:Chỉ\s+cần\s+)?(?:Vẽ|Dựng|Mô\s+phỏng|Minh\s+ho[ạa]|Biểu\s+diễn|Hiển\s+thị|Cho(?:\s+(?:mình|em|tôi|tớ)\s+xem)?))"
        r"(?:\s+giúp(?:\s+(?:mình|em|tôi|tớ))?|\s+lại)?)"
    )
    m_reg_pyr = re.search(
        rf"(?P<lead>{_SOLID_LEAD}\s+)?(?P<core>(?:hình|khối)\s+chóp(?:\s+(?:tứ\s+giác|tam\s+giác|lục\s+giác))?\s+đều\s+(?P<not>{_PT}\.{_PTS3_6}))",
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
        q_from = ca + (m_reg_pyr.start("lead") if m_reg_pyr.group("lead") else m_reg_pyr.start("core"))
        for i_dim, (attr, val, a_start, end) in enumerate(_solid_dimension_items(ctext_norm, m_reg_pyr.end("core"))):
            # All lateral edges of a regular pyramid are congruent, so "cạnh bên" binds the apex to the first base vertex.
            q_dim = _clean_quote(raw, q_from if i_dim == 0 else ca + a_start, ca + end)
            builder.premises.append(
                {"kind": "regular_polygon", "args": {"vertices": base_pts, "side": _canon_val(val)}, "quote": q_dim, "solid_id": sid}
                if attr == "base" else
                {"kind": "segment_length", "args": {"segment": [apex_s, base_pts[0]], "value": _canon_val(val)}, "quote": q_dim, "solid_id": sid}
            )
        m_all_rp = re.search(
            rf"(?:có\s+)?(?:tất\s+cả\s+(?:các\s+)?|mọi\s+)cạnh(?:\s+đều)?\s*(?:bằng|=|là)\s*(?P<val>{_VAL}){_OPT_LEN_UNIT_TAIL}",
            ctext_norm[m_reg_pyr.end("core") :],
            re.IGNORECASE | re.UNICODE,
        )
        m_all_eq_rp = None if m_all_rp else re.search(
            r"(?:có\s+)?(?:(?:tất\s+cả\s+(?:các\s+)?|mọi\s+|các\s+)cạnh(?:\s+đều)?\s+bằng\s+nhau|(?:các\s+)?cạnh\s+bên(?:\s+đều)?\s+bằng\s+cạnh\s+đáy)(?!\w)",
            ctext_norm[m_reg_pyr.end("core") :],
            re.IGNORECASE | re.UNICODE,
        )
        if m_all_rp and _is_valid_val(m_all_rp.group("val")):
            all_val = _canon_val(m_all_rp.group("val"))
            q_all = _clean_quote(raw, q_from, ca + m_reg_pyr.end("core") + m_all_rp.end())
            builder.premises.extend(
                [
                    {"kind": "regular_polygon", "args": {"vertices": base_pts, "side": all_val}, "quote": q_all, "solid_id": sid},
                    {"kind": "segment_length", "args": {"segment": [apex_s, base_pts[0]], "value": all_val}, "quote": q_all, "solid_id": sid},
                ]
            )
        elif m_all_eq_rp:
            q_all_eq = _clean_quote(raw, q_from, ca + m_reg_pyr.end("core") + m_all_eq_rp.end())
            builder.premises.extend(
                [
                    {"kind": "regular_polygon", "args": {"vertices": base_pts}, "quote": q_all_eq, "solid_id": sid},
                    {"kind": "equal_length", "args": {"segment_a": [apex_s, base_pts[0]], "segment_b": [base_pts[0], base_pts[1]]}, "quote": q_all_eq, "solid_id": sid},
                ]
            )
        m_h = re.search(
            rf"(?:độ\s+dài\s+(?:của\s+)?)?(?:chiều|đường)\s+cao(?:\s+của\s+(?:hình|khối)\s+chóp(?:\s+{re.escape(not_str)})?)?\s*(?:bằng\s+|là\s+|=\s*)(?P<h>{_VAL}){_OPT_LEN_UNIT_TAIL}",
            ctext_norm,
            re.IGNORECASE | re.UNICODE,
        )
        if m_h and _is_valid_val(m_h.group("h")):
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

    # 1c. A named pyramid with optional "hình" or "khối".
    if not m_reg_pyr and not m_two_pyr:
        m_pyr = re.search(
            rf"(?P<lead>{_SOLID_LEAD}\s+)?(?P<core>(?<![\w'])(?:(?:hình|khối)\s+)?ch[oó]p\s+(?P<not>{_PT}\.{_PTS3_6}))(?![\w'.])",
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
            if builder.solids and builder._primary_notation == not_str and lead_txt and lead_txt != "cho":
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
                    if (lead_txt and lead_txt != "cho")
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

    # 1d. Tetrahedron: "Cho (hình|khối) tứ diện (đều )?OABC" or the apex-dotted "tứ diện O.ABC" (/13)
    m_tet = re.search(
        rf"(?P<lead>{_SOLID_LEAD}\s+)?(?P<core>(?:(?:hình|khối)\s+)?tứ\s+diện(?:\s+(?P<reg>đều))?\s+(?P<pts>{_PT}\.{_PTS3}|{_PTS4}))(?![\w'.])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_tet and not builder.solids:
        pts = _split_pts(m_tet.group("pts").replace(".", ""))
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
            m_side = re.search(
                rf"cạnh\s+(?:bằng\s+|là\s+|=\s*)?(?P<val>{_VAL}){_OPT_LEN_UNIT_TAIL}",
                ctext_norm,
                re.IGNORECASE | re.UNICODE,
            )
            q_full = _clean_quote(raw, ca, cb)
            builder.premises.append(
                {"kind": "regular_pyramid", "args": {"apex": pts[0], "base": pts[1:]}, "quote": q_full, "solid_id": sid}
            )
            if m_side and _is_valid_val(m_side.group("val")):
                val = _canon_val(m_side.group("val"))
                builder.premises.append(
                    {"kind": "regular_polygon", "args": {"vertices": pts[1:], "side": val}, "quote": q_full, "solid_id": sid}
                )
                builder.premises.append(
                    {"kind": "segment_length", "args": {"segment": [pts[0], pts[1]], "value": val}, "quote": q_full, "solid_id": sid}
                )
            else:
                # (target-invariant-regular-solid-semantics) no side: the DEFINITION still makes all six edges equal. With
                # the regular base and the apex over its centre (regular_pyramid), one lateral edge = one base edge fixes
                # them all; the quote is the defining phrase itself (gate `_canh_tu_dien_deu`), never an invented equality
                q_def = _clean_quote(raw, ca + m_tet.start("core"), ca + m_tet.end("core"))
                builder.premises.append(
                    {"kind": "equal_length", "args": {"segment_a": [pts[0], pts[1]], "segment_b": [pts[1], pts[2]]},
                     "quote": q_def, "solid_id": sid}
                )
        mapped_fact = True

    # 1e. Cube: "Cho (hình|khối) lập phương ABCD.A'B'C'D' (có cạnh bằng 2)?"
    m_cube = re.search(
        rf"(?P<lead>{_SOLID_LEAD}\s+)?(?:hình|khối)\s+lập\s+phương\s+(?P<not>{_PTS4}\.{_PTS4})(?P<tail>\s+(?:có\s+)?cạnh\s+(?:bằng\s+|là\s+|=\s*)?(?P<val>{_VAL}){_OPT_LEN_UNIT_TAIL})?",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_cube and not builder.solids:
        not_str = m_cube.group("not")
        b_str, t_str = not_str.split(".", 1)
        base_pts, top_pts = _split_pts(b_str), _split_pts(t_str)
        builder._base_vertices = base_pts
        sid = "s1"
        if m_cube.group("val") and _is_valid_val(m_cube.group("val")):
            q_cube = _clean_quote(raw, ca + m_cube.start(), ca + m_cube.end())
            val = _canon_val(m_cube.group("val"))
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
            builder.premises.extend(
                [
                    {"kind": "right_prism", "args": {"base": base_pts, "top": top_pts}, "quote": q_cube, "solid_id": sid},
                    {"kind": "regular_polygon", "args": {"vertices": base_pts}, "quote": q_cube, "solid_id": sid},
                    {"kind": "equal_length", "args": {"segment_a": [base_pts[0], top_pts[0]], "segment_b": [base_pts[0], base_pts[1]]}, "quote": q_cube, "solid_id": sid},
                ]
            )
        builder._primary_solid_id = sid
        builder._primary_solid_type = "prism"
        builder._primary_notation = not_str
        mapped_fact = True

    # 1e-2. Rectangular box (cuboid): "Cho (hình|khối) hộp chữ nhật ABCD.A'B'C'D'"
    m_cuboid = re.search(
        rf"(?P<lead>{_SOLID_LEAD}\s+)?(?:hình|khối)\s+hộp\s+chữ\s+nhật\s+(?P<not>{_PTS4}\.{_PTS4})",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_cuboid and not builder.solids:
        # Run `grounded-vietnamese-geometry-understanding`: like the prism branch, the notation span lets an unnamed
        # "có đáy là hình vuông" right after it quote the solid it belongs to ("ABCD.A'B'C'D' có đáy là hình vuông").
        clause_solid_not_span = (m_cuboid.start("not"), m_cuboid.end("not"))
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
        rf"(?P<lead>{_SOLID_LEAD}\s+)?(?:(?:hình|khối)\s+)?lăng\s+trụ(?:\s+(?P<mod>đứng|đều|tam\s+giác\s+đều|tứ\s+giác\s+đều|lục\s+giác\s+đều|xiên))?\s+(?P<not>{_PTS3_6}\.{_PTS3_6}|(?P<nd>(?:[A-Z](?!['′]))+(?:[A-Z]['′])+)(?![\w'′]))",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_prism and m_prism.group("nd"):
        # Run `grounded-vietnamese-geometry-understanding`: the notation written without its dot ("ABCDA'B'C'D'") splits
        # ONLY when the top is the base's letters primed in the same order; anything else is not read as a prism.
        nd_pts = _split_pts(m_prism.group("nd").replace("′", "'"))
        nd_base = [x for x in nd_pts if not x.endswith("'")]
        nd_top = [x for x in nd_pts if x.endswith("'")]
        if not (3 <= len(nd_base) <= 6 and nd_pts == nd_base + nd_top and nd_top == [x + "'" for x in nd_base]):
            m_prism = None
    if m_prism and not builder.solids:
        clause_solid_not_span = (m_prism.start("not"), m_prism.end("not"))
        if m_prism.group("nd"):
            nd_pts = _split_pts(m_prism.group("nd").replace("′", "'"))
            not_str = "".join(nd_pts[: len(nd_pts) // 2]) + "." + "".join(nd_pts[len(nd_pts) // 2:])
        else:
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
        dims = _solid_dimension_items(ctext_norm, m_prism.end()) if ("đứng" in mod or "đều" in mod) else []
        # A right (or regular) prism's lateral edges are its height: "cạnh bên bằng h" binds the first lateral edge.
        dim_quote = lambda i, a_start, end: _clean_quote(raw, ca + (m_prism.start() if i == 0 else a_start), ca + end)  # noqa: E731
        for i_dim, (attr, val, a_start, end) in enumerate(dims):
            if attr == "lateral":
                builder.premises.append(
                    {"kind": "segment_length", "args": {"segment": [base_pts[0], top_pts[0]], "value": _canon_val(val)},
                     "quote": dim_quote(i_dim, a_start, end), "solid_id": sid}
                )
        # The base side's quote always starts at the prism name: only that span says "đều" for the base polygon.
        base_dim = next(((val, dim_quote(0, a_start, end)) for attr, val, a_start, end in dims if attr == "base"), None)
        if "đều" in mod:
            m_all_pr = re.search(
                rf"(?:có\s+)?(?:tất\s+cả\s+(?:các\s+)?|mọi\s+)cạnh(?:\s+đều)?\s*(?:bằng|=|là)\s*(?P<val>{_VAL}){_OPT_LEN_UNIT_TAIL}",
                ctext_norm[m_prism.end() :],
                re.IGNORECASE | re.UNICODE,
            )
            m_pside = None if (base_dim or m_all_pr) else re.search(
                rf"(?:có\s+)?cạnh(?:\s+đáy)?\s+(?:bằng\s+|=\s*)?(?P<val>{_VAL})",
                ctext_norm[m_prism.end() :],
                re.IGNORECASE | re.UNICODE,
            )
            if base_dim:
                builder.premises.append(
                    {"kind": "regular_polygon", "args": {"vertices": base_pts, "side": _canon_val(base_dim[0])},
                     "quote": base_dim[1], "solid_id": sid}
                )
            elif m_all_pr and _is_valid_val(m_all_pr.group("val")):
                all_p_val = _canon_val(m_all_pr.group("val"))
                q_all_p = _clean_quote(raw, ca + m_prism.start(), ca + m_prism.end() + m_all_pr.end())
                builder.premises.extend(
                    [
                        {"kind": "regular_polygon", "args": {"vertices": base_pts, "side": all_p_val}, "quote": q_all_p, "solid_id": sid},
                        {"kind": "segment_length", "args": {"segment": [base_pts[0], top_pts[0]], "value": all_p_val}, "quote": q_all_p, "solid_id": sid},
                    ]
                )
            elif m_pside:
                q_pside = _clean_quote(raw, ca + m_prism.start(), ca + m_prism.end() + m_pside.end())
                builder.premises.append(
                    {
                        "kind": "regular_polygon",
                        "args": {"vertices": base_pts, "side": _canon_val(m_pside.group("val"))},
                        "quote": q_pside,
                        "solid_id": sid,
                    }
                )
            elif (m_all_eq_pr := re.search(
                r"(?:có\s+)?(?:(?:tất\s+cả\s+(?:các\s+)?|mọi\s+|các\s+)cạnh(?:\s+đều)?\s+bằng\s+nhau|(?:các\s+)?cạnh\s+bên(?:\s+đều)?\s+bằng\s+cạnh\s+đáy)(?!\w)",
                ctext_norm[m_prism.end() :],
                re.IGNORECASE | re.UNICODE,
            )):
                q_eq_pr = _clean_quote(raw, ca + m_prism.start(), ca + m_prism.end() + m_all_eq_pr.end())
                builder.premises.extend(
                    [
                        {"kind": "regular_polygon", "args": {"vertices": base_pts}, "quote": q_eq_pr, "solid_id": sid},
                        {"kind": "equal_length", "args": {"segment_a": [base_pts[0], top_pts[0]], "segment_b": [base_pts[0], base_pts[1]]}, "quote": q_eq_pr, "solid_id": sid},
                    ]
                )
            else:
                builder.premises.append(
                    {"kind": "regular_polygon", "args": {"vertices": base_pts}, "quote": q_prism, "solid_id": sid}
                )
        m_ph = re.search(
            rf"(?:độ\s+dài\s+(?:của\s+)?)?(?:chiều|đường)\s+cao(?:\s+(?:của\s+)?(?:(?:hình|khối)\s+)?lăng\s+trụ(?:\s+{re.escape(not_str)})?)?\s*(?:bằng\s+|là\s+|=\s*)(?P<h>{_VAL}){_OPT_LEN_UNIT_TAIL}",
            ctext_norm,
            re.IGNORECASE | re.UNICODE,
        )
        if m_ph and _is_valid_val(m_ph.group("h")):
            end_ph = max(m_ph.end(), (m_prism.end() + m_pside.end()) if ("đều" in mod and m_pside) else m_ph.end())
            q_ph = _clean_quote(raw, ca + m_prism.start(), ca + end_ph)
            builder.premises.append(
                {
                    "kind": "height",
                    "args": {"solid": sid, "value": _canon_val(m_ph.group("h"))},
                    "quote": q_ph,
                    "solid_id": sid,
                }
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
                "radius": _canon_val(m_sph_stand.group("rad")),
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
            "radius": _canon_val(m_cyl_stand.group("rad")),
            "quote": q_c,
        }
        if m_cyl_stand.group("h"):
            spec_c["height"] = _canon_val(m_cyl_stand.group("h"))
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
            "radius": _canon_val(m_cone_stand.group("rad")),
            "quote": q_cn,
        }
        if m_cone_stand.group("h"):
            spec_cn["height"] = _canon_val(m_cone_stand.group("h"))
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
    # 2a. Square or equilateral triangle base: "đáy (ABCD )?là (hình vuông|tam giác đều|lục giác đều)( ABCD)?( có tâm O)?( cạnh (bằng )?2)?"
    for m_reg_base in re.finditer(
        rf"(?P<full>đáy(?:\s+(?P<verts>{_PTS3_6}))?\s+là\s+(?P<shape>hình\s+vuông|tam\s+giác\s+đều|lục\s+giác\s+đều)(?:\s+(?P<verts2>{_PTS3_6})(?![\w']))?(?:\s*(?:,\s*)?(?:có\s+)?tâm(?:\s+đối\s+xứng)?(?:\s+là)?\s+(?P<ctr0>{_PT})(?![\w']))?(?:\s*(?:,\s*)?(?:có\s+)?cạnh\s+(?:bằng\s+)?(?P<side>{_VAL}){_OPT_LEN_UNIT_TAIL})?(?:\s*(?:,\s*)?(?:có\s+)?tâm(?:\s+đối\s+xứng)?(?:\s+là)?\s+(?P<ctr>{_PT})(?![\w']))?)",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        raw_verts = m_reg_base.group("verts") or m_reg_base.group("verts2")
        verts = _split_pts(raw_verts) if raw_verts else list(builder._base_vertices)
        rb_start = m_reg_base.start("full")
        if (
            not raw_verts
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
        ctr_rb = m_reg_base.group("ctr") or m_reg_base.group("ctr0")
        if ctr_rb:
            _emit_proved_polygon_center(builder, ctr_rb, verts, q_rb)
        mapped_fact = True

    for m_reg_named in re.finditer(
        rf"(?P<full>{_BASE_NAMED_LEAD}(?P<verts>{_PTS3_6})\s+là\s+(?:một\s+)?(?P<shape>hình\s+vuông|tam\s+giác\s+đều|lục\s+giác\s+đều)(?![\w'])(?:\s*(?:,\s*)?(?:có\s+)?tâm(?:\s+đối\s+xứng)?(?:\s+là)?\s+(?P<ctr0>{_PT})(?![\w']))?(?:\s*(?:,\s*)?(?:có\s+)?cạnh\s+(?:bằng\s+)?(?P<side>{_VAL}){_OPT_LEN_UNIT_TAIL})?(?:\s*(?:,\s*)?(?:có\s+)?tâm(?:\s+đối\s+xứng)?(?:\s+là)?\s+(?P<ctr>{_PT})(?![\w']))?)",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        verts_rn = _split_pts(m_reg_named.group("verts"))
        if builder._base_vertices and set(verts_rn) == set(builder._base_vertices):
            q_rn = _clean_quote(raw, ca + m_reg_named.start("verts"), ca + m_reg_named.end("full"))
            side_rn = m_reg_named.group("side")
            args_rn: dict[str, Any] = {"vertices": verts_rn}
            if side_rn is not None and _is_valid_val(side_rn):
                args_rn["side"] = _canon_val(side_rn)
            else:
                builder.unresolved.append(
                    {
                        "unresolved_id": f"u{len(builder.unresolved) + 1}",
                        "kind": "missing_operand",
                        "quote": q_rn,
                        "missing_roles": ["dimension"],
                        "candidate_relations": [],
                    }
                )
            if not any(p.get("kind") == "regular_polygon" and set(p["args"].get("vertices") or ()) == set(verts_rn) for p in builder.premises):
                builder.premises.append(
                    {"kind": "regular_polygon", "args": args_rn, "quote": q_rn, "solid_id": builder._primary_solid_id}
                )
                mapped_fact = True
            ctr_rn = m_reg_named.group("ctr") or m_reg_named.group("ctr0")
            if ctr_rn:
                _emit_proved_polygon_center(builder, ctr_rn, verts_rn, q_rn)

    for m_reg_tri in re.finditer(
        rf"(?P<full>(?:tam\s+giác|mặt\s+bên)\s+(?P<verts>{_PTS3})\s+(?:là\s+(?:một\s+)?tam\s+giác\s+)?đều(?:\s+cạnh\s+(?:bằng\s+)?(?P<side>{_VAL}){_OPT_LEN_UNIT_TAIL})?)",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        verts_tri = _split_pts(m_reg_tri.group("verts"))
        # semantic-to-scene3d: an equilateral LATERAL face of the declared solid ("tam giác SAB đều", "mặt bên SAB là
        # tam giác đều") — three labels of the solid that are not its base; the side comes from the base edge it shares.
        dinh_tri = {x for sd in builder.solids for x in _split_pts(str(sd.get("notation") or "").replace(".", ""))}
        if (builder._base_vertices and set(verts_tri) != set(builder._base_vertices) and set(verts_tri) <= dinh_tri
                and len(set(verts_tri) & set(builder._base_vertices)) == 2):
            q_lt = _clean_quote(raw, ca + m_reg_tri.start("full"), ca + m_reg_tri.end("full"))
            if not any(p.get("kind") == "regular_polygon" and set(p["args"].get("vertices") or ()) == set(verts_tri)
                       for p in builder.premises):
                args_lt: dict[str, Any] = {"vertices": verts_tri}
                if m_reg_tri.group("side") is not None:
                    args_lt["side"] = _canon_val(m_reg_tri.group("side"))
                builder.premises.append(
                    {"kind": "regular_polygon", "args": args_lt, "quote": q_lt, "solid_id": builder._primary_solid_id})
                mapped_fact = True
            continue
        if builder._base_vertices and set(verts_tri) == set(builder._base_vertices):
            q_rt = _clean_quote(raw, ca + m_reg_tri.start("full"), ca + m_reg_tri.end("full"))
            if not any(p.get("kind") == "regular_polygon" and set(p["args"].get("vertices") or ()) == set(verts_tri) for p in builder.premises):
                args_rt: dict[str, Any] = {"vertices": list(builder._base_vertices)}
                if m_reg_tri.group("side") is not None:
                    args_rt["side"] = _canon_val(m_reg_tri.group("side"))
                builder.premises.append(
                    {"kind": "regular_polygon", "args": args_rt, "quote": q_rt, "solid_id": builder._primary_solid_id}
                )
                mapped_fact = True

    # 2b. Rectangle base: "đáy (ABCD )?là hình chữ nhật( ABCD)?( tâm O)?" — or the named base "biết / có / với ABCD là hình chữ nhật" (/13)
    for m_rect in re.finditer(
        rf"(?P<full>(?:đáy(?:\s+(?P<verts>{_PTS4}))?\s+(?:là\s+(?:một\s+)?)?|{_BASE_NAMED_LEAD}(?P<verts0>{_PTS4})\s+là\s+(?:một\s+)?)hình\s+chữ\s+nhật(?!\w)(?:\s+(?P<verts2>{_PTS4})(?![\w']))?(?:\s*(?:,\s*)?(?:có\s+)?tâm(?:\s+đối\s+xứng)?(?:\s+là)?\s+(?P<ctr>{_PT})(?![\w']))?)",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        if m_rect.group("verts0") and set(_split_pts(m_rect.group("verts0"))) != set(builder._base_vertices):
            continue                                     # a named polygon that is not this solid's base: not this rule
        rc_verts_raw = m_rect.group("verts") or m_rect.group("verts0") or m_rect.group("verts2")
        verts = _split_pts(rc_verts_raw) if rc_verts_raw else list(builder._base_vertices)
        rc_start = m_rect.start("verts0") if m_rect.group("verts0") else m_rect.start("full")
        if (
            not rc_verts_raw
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
        if m_rect.group("ctr"):
            _emit_proved_polygon_center(builder, m_rect.group("ctr"), verts, q_rc)
        mapped_fact = True

    # 2c. Right (or right-isosceles) triangle base / named triangle:
    # "(có )?đáy (ABC )?(là tam giác (ABC )?)?vuông (cân )?tại A" or standalone "tam giác ABC vuông (cân )?tại A"
    for m_rt in re.finditer(
        rf"(?P<full>(?:(?:(?:có|với)\s+)?đáy(?:\s+(?P<verts>{_PTS3}))?\s+(?:là\s+tam\s+giác\s+(?:(?P<verts2>{_PTS3})\s+)?)?|tam\s+giác\s+(?P<verts3>{_PTS3})\s+)vuông(?:\s+(?P<iso>cân))?\s+(?:tại|ở)\s+(?P<v>{_PT}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        explicit_v = m_rt.group("verts") or m_rt.group("verts2") or m_rt.group("verts3")
        verts = _split_pts(explicit_v) if explicit_v else list(builder._base_vertices)
        if len(verts) != 3 or len(set(verts)) != 3:
            continue
        v = m_rt.group("v")
        rays = [p for p in verts if p != v]
        if len(rays) == 2:
            s_off = m_rt.start("full")
            if m_rt.group("verts2"):
                # "có đáy là tam giác ABC vuông tại B" -> quote "tam giác ABC vuông tại B"
                m_sub = re.search(rf"tam\s+giác\s+{re.escape(m_rt.group('verts2'))}\b", m_rt.group("full"), re.IGNORECASE)
                if m_sub:
                    s_off += m_sub.start()
            elif clause_solid_not_span is not None and clause_solid_not_span[1] <= s_off:
                if re.fullmatch(
                    r"\s*(?:[.,]\s*)?(?:có\s+)?(?:chung\s+)?(?:mặt\s+)?",
                    ctext_norm[clause_solid_not_span[1] : s_off],
                    re.IGNORECASE,
                ):
                    s_off = clause_solid_not_span[0]
            else:
                for pfx in ("có ", "với "):
                    if ctext_norm[s_off : s_off + len(pfx)].lower() == pfx:
                        s_off += len(pfx)
                        break
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
        rf"(?P<full>đáy(?:\s+(?P<verts>{_PTS4}))?\s+là\s+hình\s+thang(?:\s+(?P<iso>cân))?\s+(?:(?:với|có)\s+hai\s+đáy(?:\s+là)?\s+(?P<ba1>{_PTS2})\s*(?:và|,\s*)\s*(?P<bb1>{_PTS2})|(?:(?:với|có)\s+)?(?P<ba2>{_PTS2})\s*(?:song\s+song(?:\s+với)?|//|∥)\s*(?P<bb2>{_PTS2})))(?![\w'])",
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

    # 2h. FAMILY-2 Rhombus & Parallelogram ("đáy (ABCD )?là hình thoi( ABCD)?( tâm O)?( cạnh a)?" / "đáy (ABCD )?là hình bình hành( ABCD)?( tâm O)?")
    for m_rhom in re.finditer(
        rf"(?P<full>(?:đáy(?:\s+(?P<verts>{_PTS4})(?![\w']))?|{_BASE_NAMED_LEAD}(?P<verts0>{_PTS4}))\s+là\s+(?:một\s+)?hình\s+thoi(?:\s+(?P<verts2>{_PTS4})(?![\w']))?(?:\s*(?:,\s*)?(?:có\s+)?tâm(?:\s+đối\s+xứng)?(?:\s+là)?\s+(?P<ctr0>{_PT})(?![\w']))?(?:(?:\s*,\s*|\s+)(?:có\s+)?(?:độ\s+dài\s+)?cạnh(?:\s*(?:bằng|=|là))?\s*(?P<side>{_VAL}){_OPT_LEN_UNIT_TAIL})?(?:\s*(?:,\s*)?(?:có\s+)?tâm(?:\s+đối\s+xứng)?(?:\s+là)?\s+(?P<ctr>{_PT})(?![\w']))?)",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        if m_rhom.group("verts0") and set(_split_pts(m_rhom.group("verts0"))) != set(builder._base_vertices):
            continue                                     # /13 named form: only this solid's own base
        rh_verts_raw = m_rhom.group("verts") or m_rhom.group("verts0") or m_rhom.group("verts2")
        verts = _split_pts(rh_verts_raw) if rh_verts_raw else list(builder._base_vertices)
        if len(verts) == 4:
            rh_start = m_rhom.start("verts0") if m_rhom.group("verts0") else m_rhom.start("full")
            if (
                not rh_verts_raw
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
            ctr_rh = m_rhom.group("ctr") or m_rhom.group("ctr0")
            if ctr_rh:
                _emit_proved_polygon_center(builder, ctr_rh, verts, q_rh)
            mapped_fact = True

    for m_para in re.finditer(
        rf"(?P<full>đáy(?:\s+(?P<verts>{_PTS4})(?![\w']))?\s+là\s+(?:một\s+)?hình\s+bình\s+hành(?:\s+(?P<verts2>{_PTS4})(?![\w']))?(?:\s*(?:,\s*)?(?:có\s+)?tâm(?:\s+đối\s+xứng)?(?:\s+là)?\s+(?P<ctr>{_PT}))?)(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        pa_verts_raw = m_para.group("verts") or m_para.group("verts2")
        verts = _split_pts(pa_verts_raw) if pa_verts_raw else list(builder._base_vertices)
        if len(verts) == 4:
            pa_start = m_para.start("full")
            if (
                not pa_verts_raw
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
            if m_para.group("ctr"):
                _emit_proved_polygon_center(builder, m_para.group("ctr"), verts, q_pa)
            mapped_fact = True

    # 2i. Named polygon / face area premise: "diện tích của hình vuông ABB'A' bằng 12(cm²)", "diện tích tam giác ABC bằng a²/2", "S_{ABCD} = a²"
    area_spans: list[tuple[int, int]] = []
    for m_parea in re.finditer(
        rf"(?P<full>diện\s+tích(?:\s+của)?\s+(?:(?P<shape>hình\s+vuông|hình\s+chữ\s+nhật|tam\s+giác\s+đều|tam\s+giác|tứ\s+giác|mặt\s+bên|mặt\s+đáy|đáy)\s+)?\(?((?P<poly>{_PTS3_6}))\)?\s*(?:bằng|là|=)\s*(?P<val>{_VAL}){_OPT_AREA_UNIT_TAIL}"
        rf"|(?P<shape2>hình\s+vuông|hình\s+chữ\s+nhật|tam\s+giác\s+đều|tam\s+giác|tứ\s+giác|mặt\s+bên|mặt\s+đáy)\s+\(?(?P<poly2>{_PTS3_6})\)?\s+có\s+diện\s+tích(?:\s+(?:bằng|là|=))?\s*(?P<val2>{_VAL}){_OPT_AREA_UNIT_TAIL}"
        rf"|(?<![\w'.])(?-i:S)\s*(?:_|\()\s*\{{?\s*(?P<poly3>{_PTS3_6})\s*\}}?\s*\)?\s*(?:=|bằng)\s*(?P<val3>{_VAL}){_OPT_AREA_UNIT_TAIL})",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        val_pa = m_parea.group("val") or m_parea.group("val2") or m_parea.group("val3")
        if not _is_valid_val(val_pa):
            continue
        poly_pts = _split_pts(m_parea.group("poly") or m_parea.group("poly2") or m_parea.group("poly3"))
        if len(poly_pts) >= 3:
            sh_raw = re.sub(r"\s+", " ", ((m_parea.group("shape") or m_parea.group("shape2")) or "").strip().lower())
            sh_code = {
                "hình vuông": "square",
                "hình chữ nhật": "rectangle",
                "tam giác đều": "equilateral_triangle",
                "tam giác": "triangle",
            }.get(sh_raw, "polygon")
            q_parea = _clean_quote(raw, ca + m_parea.start("full"), ca + m_parea.end("full"))
            builder.premises.append(
                {
                    "kind": "face_area",
                    "args": {"polygon": poly_pts, "value": _canon_val(val_pa), "shape": sh_code},
                    "quote": q_parea,
                    "solid_id": builder._primary_solid_id,
                }
            )
            area_spans.append((m_parea.start("full"), m_parea.end("full")))
            mapped_fact = True

    # Run `grounded-vietnamese-geometry-understanding`: the area of the UNNAMED base of the declared solid ("diện tích đáy
    # bằng a²"); quoted as written — the Source Gate resolves "đáy" to the unique solid's base itself.
    for m_dt_day in re.finditer(
        rf"(?P<full>diện\s+tích(?:\s+của)?\s+(?:mặt\s+)?đáy\s*(?:bằng|là|=)\s*(?P<val>{_VAL}){_OPT_AREA_UNIT_TAIL})",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        if any(a_s <= m_dt_day.start("full") < b_s for a_s, b_s in area_spans):
            continue
        if not _is_valid_val(m_dt_day.group("val")):
            continue
        if len(builder._base_vertices) >= 3 and len(builder.solids) == 1:
            builder.premises.append(
                {
                    "kind": "face_area",
                    "args": {
                        "polygon": list(builder._base_vertices),
                        "value": _canon_val(m_dt_day.group("val")),
                        "shape": "polygon",
                    },
                    "quote": _clean_quote(raw, ca + m_dt_day.start("full"), ca + m_dt_day.end("full")),
                    "solid_id": builder._primary_solid_id,
                }
            )
            mapped_fact = True

    # 2j. Solid volume premise: "Thể tích hình chóp bằng a³/3", "Thể tích khối chóp S.ABCD bằng a³", "V_{S.ABCD} = a³/3"
    _solid_kind_words = r"(?:chóp|lăng\s+trụ|hộp(?:\s+chữ\s+nhật)?|lập\s+phương|tứ\s+diện)(?:\s+(?:đứng|đều|xiên|tam\s+giác|tứ\s+giác|lục\s+giác|chữ\s+nhật))*"
    _solid_not_any = rf"(?:{_PT}\.{_PTS3_6}|{_PTS3_6}\.{_PTS3_6}|{_PTS4})"
    for m_svol in re.finditer(
        rf"(?P<full>thể\s+tích(?:\s+của)?(?:\s+(?:(?:hình|khối)\s+)?(?P<sk>{_solid_kind_words})(?:\s+(?P<snot>{_solid_not_any})(?![\w'.]))?|\s+(?P<snot0>{_PT}\.{_PTS3_6}|{_PTS3_6}\.{_PTS3_6})(?![\w'.]))?\s*(?:bằng|là|=)\s*(?P<val>{_VAL}){_OPT_VOL_UNIT_TAIL}"
        rf"|(?:(?:hình|khối)\s+)?(?P<sk2>{_solid_kind_words})\s+(?P<snot2>{_solid_not_any})(?![\w'.])\s+có\s+thể\s+tích(?:\s+(?:bằng|là|=))?\s*(?P<val2>{_VAL}){_OPT_VOL_UNIT_TAIL}"
        rf"|(?<![\w'.])(?-i:V)\s*(?:_|\()\s*\{{?\s*(?P<snot3>{_PT}\.{_PTS3_6}|{_PTS3_6}\.{_PTS3_6}|{_PTS4})\s*\}}?\s*\)?\s*(?:=|bằng)\s*(?P<val3>{_VAL}){_OPT_VOL_UNIT_TAIL})",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        val_sv = m_svol.group("val") or m_svol.group("val2") or m_svol.group("val3")
        if not _is_valid_val(val_sv):
            continue
        snot = (
            m_svol.group("snot")
            or m_svol.group("snot0")
            or m_svol.group("snot2")
            or m_svol.group("snot3")
        )
        sid_sv: str | None = None
        if snot:
            snot_clean = snot.replace("′", "'")
            for s_cand in builder.solids:
                if s_cand["notation"] == snot_clean or set(_split_pts(s_cand["notation"].replace(".", ""))) == set(_split_pts(snot_clean.replace(".", ""))):
                    sid_sv = s_cand["solid_id"]
                    break
        elif len(builder.solids) == 1:
            sid_sv = builder._primary_solid_id
        if sid_sv is not None:
            q_sv = _clean_quote(raw, ca + m_svol.start("full"), ca + m_svol.end("full"))
            builder.premises.append(
                {
                    "kind": "solid_volume",
                    "args": {"solid": sid_sv, "value": _canon_val(val_sv)},
                    "quote": q_sv,
                    "solid_id": sid_sv,
                }
            )
            mapped_fact = True

    # 2k. Standalone "Cạnh đáy / Cạnh bên (bằng|là|=) <_VAL>" in a separate premise clause when the unique solid's role edges are equal
    if len(builder.solids) == pre_solids_len and len(builder.solids) == 1:
        for m_st_edge in re.finditer(
            rf"(?P<full>(?:(?:Biết(?:\s+rằng)?|Có|Với)\s+)?(?:độ\s+dài\s+(?:của\s+)?)?(?P<attr>cạnh\s+đáy|cạnh\s+bên)(?:\s+của\s+(?:hình|khối)\s+(?:chóp|lăng\s+trụ|hộp|lập\s+phương|tứ\s+diện)(?:\s+{_solid_not_any})?)?\s*(?:(?:đều\s+)?(?:bằng|là)\s+|=\s*)(?P<val>{_VAL}){_OPT_LEN_UNIT_TAIL})",
            ctext_norm,
            re.IGNORECASE | re.UNICODE,
        ):
            val_se = m_st_edge.group("val")
            if not _is_valid_val(val_se):
                continue
            attr_se = "lateral" if "bên" in m_st_edge.group("attr").lower() else "base"
            q_se = _clean_quote(raw, ca + m_st_edge.start("full"), ca + m_st_edge.end("full"))
            if attr_se == "base":
                has_equal_base = any(
                    p.get("kind") in ("regular_pyramid", "regular_polygon", "rhombus")
                    for p in builder.premises
                )
                if has_equal_base and len(builder._base_vertices) >= 3:
                    builder.premises.append(
                        {
                            "kind": "segment_length",
                            "args": {"segment": list(builder._base_vertices[:2]), "value": _canon_val(val_se)},
                            "quote": q_se,
                            "solid_id": builder._primary_solid_id,
                        }
                    )
                    mapped_fact = True
            else:
                sol0 = builder.solids[0]
                if sol0["solid_type"] == "pyramid" and "." in sol0["notation"] and any(
                    p.get("kind") == "regular_pyramid" for p in builder.premises
                ):
                    ap0, b0_s = sol0["notation"].split(".", 1)
                    b0_pts = _split_pts(b0_s)
                    if b0_pts:
                        builder.premises.append(
                            {
                                "kind": "segment_length",
                                "args": {"segment": [ap0, b0_pts[0]], "value": _canon_val(val_se)},
                                "quote": q_se,
                                "solid_id": sol0["solid_id"],
                            }
                        )
                        mapped_fact = True
                elif sol0["solid_type"] == "prism" and "." in sol0["notation"]:
                    b0_s, t0_s = sol0["notation"].split(".", 1)
                    b0_pts, t0_pts = _split_pts(b0_s), _split_pts(t0_s)
                    if b0_pts and t0_pts:
                        builder.premises.append(
                            {
                                "kind": "segment_length",
                                "args": {"segment": [b0_pts[0], t0_pts[0]], "value": _canon_val(val_se)},
                                "quote": q_se,
                                "solid_id": sol0["solid_id"],
                            }
                        )
                        mapped_fact = True

    # ── 3. Perpendicularity & Altitude Premises ──────────────────────────────────────────────────────────────────
    # 3a. Pairwise perpendicular edges from apex: "OA, OB, OC đôi một vuông góc (với nhau)?" and the synonym
    #     "… vuông góc (với nhau) từng đôi (một)" that the v3 normalizer and the SLM prompt canonicalizer already read
    #     (run `model1-integration-readiness`: it was kept out of the parser only to keep a benchmark's SLM stratum).
    for m_pair_perp in re.finditer(
        rf"(?P<full>(?P<e1>{_PTS2})\s*,\s*(?P<e2>{_PTS2})\s*,\s*(?P<e3>{_PTS2})\s+(?:đôi\s+một\s+vuông\s+góc(?:\s+với\s+nhau)?"
        rf"|vuông\s+góc\s+(?:với\s+nhau\s+)?từng\s+đôi(?:\s+một)?))",
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

    # 3a-bis. Right-corner tetrahedron: "tứ diện OABC vuông tại O"
    for m_tdv in re.finditer(
        rf"(?P<full>tứ\s+diện\s+(?P<verts>{_PTS4})\s+vuông\s+(?:tại|ở)\s+(?:đỉnh\s+)?(?P<v>{_PT}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        tet_vs = _split_pts(m_tdv.group("verts"))
        v_td = m_tdv.group("v")
        if len(tet_vs) != 4 or len(set(tet_vs)) != 4 or v_td not in tet_vs:
            continue
        others = [x for x in tet_vs if x != v_td]
        q_tdv = _clean_quote(raw, ca + m_tdv.start("full"), ca + m_tdv.end("full"))
        for la, lb in (([v_td, others[0]], [v_td, others[1]]), ([v_td, others[0]], [v_td, others[2]]), ([v_td, others[1]], [v_td, others[2]])):
            builder.premises.append(
                {
                    "kind": "perpendicular_lines",
                    "args": {"line1": la, "line2": lb},
                    "quote": q_tdv,
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

    # 3b-bis (/13). Two planes through one lateral edge, both ⊥ the base: "hai mặt phẳng (SAB) và (SAD) cùng vuông góc với
    # (mặt) đáy / (ABCD)" — the textbook way of stating SA ⊥ base. Only when the two planes share EXACTLY two points; the
    # Source Gate binds the call to this phrase (`registry._hai_mat_vuong_day_khop`), never to an invented "SA ⊥ …".
    for m_2p in re.finditer(
        rf"(?P<full>hai\s+mặt\s+(?:phẳng|bên)\s+\(\s*(?P<p1>{_PTS3})\s*\)\s*(?:,|và)\s*(?:mặt\s+phẳng\s+)?\(\s*(?P<p2>{_PTS3})\s*\)"
        rf"\s+(?:cùng|đều)\s+vuông\s+góc\s+(?:với\s+)?(?P<target>(?:mặt\s+phẳng\s+|mp\s*)?\((?P<plane>{_PTS3_6})\)|mặt\s+phẳng\s+đáy(?:\s+\({_PTS3_6}\))?|mặt\s+đáy(?:\s+\({_PTS3_6}\))?|đáy(?:\s+\({_PTS3_6}\))?))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        p1, p2 = _split_pts(m_2p.group("p1")), _split_pts(m_2p.group("p2"))
        line_pts = [v for v in p1 if v in p2]
        plane_pts = _split_pts(m_2p.group("plane")) if m_2p.group("plane") else list(builder._base_vertices)
        if len(set(p1)) == 3 and len(set(p2)) == 3 and set(p1) != set(p2) and len(line_pts) == 2 and len(plane_pts) >= 3:
            builder.premises.append(
                {
                    "kind": "perpendicular_line_plane",
                    "args": {"line": line_pts, "plane": plane_pts},
                    "quote": _clean_quote(raw, ca + m_2p.start("full"), ca + m_2p.end("full")),
                    "solid_id": builder._primary_solid_id,
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
        rf"(?P<full>đường\s+cao\s+(?P<seg>{_PTS2})\s*=\s*(?P<val>{_VAL}){_OPT_LEN_UNIT_TAIL})",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        if not _is_valid_val(m_alt.group("val")):
            continue
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
                "args": {"segment": seg_pts, "value": _canon_val(m_alt.group("val"))},
                "quote": q_len,
                "solid_id": builder._primary_solid_id,
            }
        )
        mapped_fact = True

    # 3d-1. Standalone solid height premise: "Độ dài đường cao bằng a√3", "Chiều cao hình chóp bằng 2a"
    if not any(p.get("kind") == "height" for p in builder.premises[pre_premises_len:]) and len(builder.solids) == 1:
        for m_sh in re.finditer(
            rf"(?P<full>(?:(?:Biết(?:\s+rằng)?|Có|Với)\s+)?(?:độ\s+dài\s+(?:của\s+)?)?(?:chiều|đường)\s+cao(?:\s+(?:của\s+)?(?:(?:hình|khối)\s+)?(?:chóp|lăng\s+trụ|hộp(?:\s+chữ\s+nhật)?|lập\s+phương|tứ\s+diện)(?:\s+(?:đứng|đều|xiên|tam\s+giác|tứ\s+giác|lục\s+giác|chữ\s+nhật))*(?:\s+(?:{_PT}\.{_PTS3_6}|{_PTS3_6}\.{_PTS3_6}|{_PTS4})(?![\w'.]))?)?\s*(?:bằng|là|=)\s*(?P<val>{_VAL}){_OPT_LEN_UNIT_TAIL})",
            ctext_norm,
            re.IGNORECASE | re.UNICODE,
        ):
            if not _is_valid_val(m_sh.group("val")):
                continue
            sid_sh = builder.solids[0]["solid_id"]
            q_sh = _clean_quote(raw, ca + m_sh.start("full"), ca + m_sh.end("full"))
            builder.premises.append(
                {
                    "kind": "height",
                    "args": {"solid": sid_sh, "value": _canon_val(m_sh.group("val"))},
                    "quote": q_sh,
                    "solid_id": sid_sh,
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
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:số\s+đo\s+)?góc\s+nhị\s+diện\s+\[\s*(?P<pa>{_PT})\s*,\s*(?P<edge>{_PTS2})\s*,\s*(?P<pb>{_PT})\s*\]\s*(?:bằng|là|=)\s*(?P<aval>\d+(?:/\d+)?){_DEG_OR_WRONG_DIM_UNIT_TAIL})",
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
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?các\s+cạnh\s+bên(?:\s+(?P<elist>{_PTS2}(?:\s*(?:,\s*|\s+và\s+){_PTS2})+))?\s+cùng\s+(?:tạo|hợp)\s+với\s+(?:(?:mặt\s+phẳng\s+|mp\s*)?\((?P<pl>{_PTS3_6})\)|(?:mặt\s+phẳng\s+đáy|mặt\s+đáy|đáy)(?:\s*\((?P<pld>{_PTS3_6})\))?)\s+(?:một\s+)?góc(?:\s+(?:bằng|là|=))?\s*(?P<aval>\d+(?:/\d+)?){_DEG_OR_WRONG_DIM_UNIT_TAIL})",
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
            rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:số\s+đo\s+)?góc\s+(?:giữa|tạo\s+bởi|hợp\s+bởi)\s+(?:đường\s+thẳng\s+|cạnh\s+bên\s+|cạnh\s+|đoạn(?:\s+thẳng)?\s+)?(?P<ln>{_PTS2})\s+(?:và|với)\s+(?:(?:mặt\s+phẳng\s+|mặt\s+bên\s+|mp\s*)?\((?P<pl>{_PTS3_6})\)|(?:mặt\s+phẳng\s+đáy|mặt\s+đáy|đáy)(?:\s*\((?P<pld>{_PTS3_6})\))?)\s*(?:bằng|là|=)\s*(?P<aval>\d+(?:/\d+)?){_DEG_OR_WRONG_DIM_UNIT_TAIL})",
            rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:đường\s+thẳng\s+|cạnh\s+bên\s+|cạnh\s+|đoạn(?:\s+thẳng)?\s+)?(?<![\w'.(])(?P<ln>{_PTS2})\s+(?:tạo|hợp)\s+với\s+(?:(?:mặt\s+phẳng\s+|mặt\s+bên\s+|mp\s*)?\((?P<pl>{_PTS3_6})\)|(?:mặt\s+phẳng\s+đáy|mặt\s+đáy|đáy)(?:\s*\((?P<pld>{_PTS3_6})\))?)\s+(?:một\s+)?góc(?:\s+(?:bằng|là|=))?\s*(?P<aval>\d+(?:/\d+)?){_DEG_OR_WRONG_DIM_UNIT_TAIL})",
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
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:số\s+đo\s+)?góc\s+(?:giữa|tạo\s+bởi|hợp\s+bởi)\s+(?:hai\s+mặt\s+phẳng\s+|mặt\s+phẳng\s+|mặt\s+bên\s+|mp\s*)?\((?P<p1>{_PTS3_6})\)\s+(?:và|với)\s+(?:(?:mặt\s+phẳng\s+|mặt\s+bên\s+|mp\s*)?\((?P<p2>{_PTS3_6})\)|(?:mặt\s+phẳng\s+đáy|mặt\s+đáy|đáy)(?:\s*\((?P<p2d>{_PTS3_6})\))?)\s*(?:bằng|là|=)\s*(?P<aval>\d+(?:/\d+)?){_DEG_OR_WRONG_DIM_UNIT_TAIL})",
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:mặt\s+bên\s+|mặt\s+phẳng\s+|mp\s*)?\((?P<p1>{_PTS3_6})\)\s+(?:tạo|hợp)\s+với\s+(?:(?:mặt\s+phẳng\s+|mặt\s+bên\s+|mp\s*)?\((?P<p2>{_PTS3_6})\)|(?:mặt\s+phẳng\s+đáy|mặt\s+đáy|đáy)(?:\s*\((?P<p2d>{_PTS3_6})\))?)\s+(?:một\s+)?góc(?:\s+(?:bằng|là|=))?\s*(?P<aval>\d+(?:/\d+)?){_DEG_OR_WRONG_DIM_UNIT_TAIL})",
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
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:số\s+đo\s+)?góc\s+(?:giữa|tạo\s+bởi|hợp\s+bởi)\s+(?:hai\s+đường\s+thẳng\s+|đường\s+thẳng\s+|cạnh\s+)?(?P<l1>{_PTS2})\s+(?:và|với)\s+(?:đường\s+thẳng\s+|cạnh\s+)?(?P<l2>{_PTS2})\s*(?:bằng|là|=)\s*(?P<aval>\d+(?:/\d+)?){_DEG_OR_WRONG_DIM_UNIT_TAIL})",
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:đường\s+thẳng\s+|cạnh\s+)?(?<![\w'.(])(?P<l1>{_PTS2})\s+(?:tạo|hợp)\s+với\s+(?:đường\s+thẳng\s+|cạnh\s+)?(?P<l2>{_PTS2})(?![\w')])\s+(?:một\s+)?góc(?:\s+(?:bằng|là|=))?\s*(?P<aval>\d+(?:/\d+)?){_DEG_OR_WRONG_DIM_UNIT_TAIL})",
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
        rf"(?P<full>(?:góc\s+|[∠^]\s*)(?P<p3>{_PTS3})(?![\w'])\s*(?:bằng|là|=)\s*(?P<aval>\d+(?:/\d+)?){_DEG_OR_WRONG_DIM_UNIT_TAIL})",
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

    # Single-letter hat vertex angle on a triangle base: `Â = 60°`, `Â = 60°`, `\hat{A} = 60°`, `góc A = 60°`
    for m_vhat in re.finditer(
        rf"(?P<full>(?:\\hat\s*\{{\s*(?P<vh1>{_PT})\s*\}}|(?<![\w'.])(?P<vh2>(?:[\u00C2\u00CA\u00D4][0-9]*'?|{_PT}(?:\u0302|\s*\^)))|góc\s+(?P<vh3>{_PT}))(?![\w'])\s*(?:bằng|là|=)\s*(?P<aval>\d+(?:/\d+)?){_DEG_OR_WRONG_DIM_UNIT_TAIL})",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        if any(a <= m_vhat.start("full") < b for a, b in angle_spans):
            continue
        raw_vh = m_vhat.group("vh1") or m_vhat.group("vh2") or m_vhat.group("vh3") or ""
        v_clean = unicodedata.normalize("NFD", raw_vh).replace("\u0302", "").replace("^", "").strip().upper()
        if len(builder._base_vertices) == 3 and v_clean in builder._base_vertices:
            rays = [p for p in builder._base_vertices if p != v_clean]
            q_vhat = _clean_quote(raw, ca + m_vhat.start("full"), ca + m_vhat.end("full"))
            builder.premises.append(
                {
                    "kind": "vertex_angle",
                    "args": {
                        "vertex": v_clean,
                        "rays": rays,
                        "value": m_vhat.group("aval"),
                        "unit": "deg",
                    },
                    "quote": q_vhat,
                    "solid_id": builder._primary_solid_id,
                }
            )
            angle_spans.append((m_vhat.start("full"), m_vhat.end("full")))
            mapped_fact = True

    # 3e-trig. Exact trigonometric ratio angle premises (`sin`, `cos`/`côsin`/`cosin`, `tan`/`tang`/`tg`, `cot`/`côtang`/`cotang`/`cotg`)
    for dih_t_pat in (
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?P<tf>{_TRIG_KW_RE})\s+(?:của\s+)?(?:số\s+đo\s+)?góc\s+nhị\s+diện\s+\[\s*(?P<pa>{_PT})\s*,\s*(?P<edge>{_PTS2})\s*,\s*(?P<pb>{_PT})\s*\]\s*(?:bằng|là|=)\s*(?P<tval>(?:-\s*)?{_VAL}){_OPT_ANY_UNIT_TAIL})",
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:số\s+đo\s+)?góc\s+nhị\s+diện\s+\[\s*(?P<pa>{_PT})\s*,\s*(?P<edge>{_PTS2})\s*,\s*(?P<pb>{_PT})\s*\]\s+có\s+(?P<tf>{_TRIG_KW_RE})\s*(?:bằng|là|=)\s*(?P<tval>(?:-\s*)?{_VAL}){_OPT_ANY_UNIT_TAIL})",
    ):
        for m_dt in re.finditer(dih_t_pat, ctext_norm, re.IGNORECASE | re.UNICODE):
            if any(a <= m_dt.start("full") < b for a, b in angle_spans):
                continue
            if re.search(r"\b(?:tính|tìm|xác\s+định|hỏi)\b", ctext_norm[: m_dt.start("full")].rstrip(), re.IGNORECASE):
                continue
            tv = _canon_val(re.sub(r"\s+", "", m_dt.group("tval")))
            if not _is_valid_val(tv):
                continue
            q_dt = _clean_quote(raw, ca + m_dt.start("full"), ca + m_dt.end("full"))
            builder.premises.append(
                {
                    "kind": "dihedral_angle",
                    "args": {
                        "point_a": m_dt.group("pa"),
                        "edge": _split_pts(m_dt.group("edge")),
                        "point_b": m_dt.group("pb"),
                        "value": tv,
                        "unit": _canon_trig_unit(m_dt.group("tf")),
                    },
                    "quote": q_dt,
                    "solid_id": builder._primary_solid_id,
                }
            )
            angle_spans.append((m_dt.start("full"), m_dt.end("full")))
            mapped_fact = True

    for lpa_t_pat in (
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?P<tf>{_TRIG_KW_RE})\s+(?:của\s+)?(?:số\s+đo\s+)?góc\s+(?:giữa|tạo\s+bởi|hợp\s+bởi)\s+(?:đường\s+thẳng\s+|cạnh\s+bên\s+|cạnh\s+|đoạn(?:\s+thẳng)?\s+)?(?P<ln>{_PTS2})\s+(?:và|với)\s+(?:(?:mặt\s+phẳng\s+|mặt\s+bên\s+|mp\s*)?\((?P<pl>{_PTS3_6})\)|(?:mặt\s+phẳng\s+đáy|mặt\s+đáy|đáy)(?:\s*\((?P<pld>{_PTS3_6})\))?)\s*(?:bằng|là|=)\s*(?P<tval>(?:-\s*)?{_VAL}){_OPT_ANY_UNIT_TAIL})",
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:(?:số\s+đo\s+)?góc\s+(?:giữa|tạo\s+bởi|hợp\s+bởi)\s+(?:đường\s+thẳng\s+|cạnh\s+bên\s+|cạnh\s+|đoạn(?:\s+thẳng)?\s+)?(?P<ln>{_PTS2})\s+(?:và|với)\s+(?:(?:mặt\s+phẳng\s+|mặt\s+bên\s+|mp\s*)?\((?P<pl>{_PTS3_6})\)|(?:mặt\s+phẳng\s+đáy|mặt\s+đáy|đáy)(?:\s*\((?P<pld>{_PTS3_6})\))?)|(?:đường\s+thẳng\s+|cạnh\s+bên\s+|cạnh\s+|đoạn(?:\s+thẳng)?\s+)?(?<![\w'.(])(?P<ln2>{_PTS2})\s+(?:tạo|hợp)\s+với\s+(?:(?:mặt\s+phẳng\s+|mặt\s+bên\s+|mp\s*)?\((?P<pl2>{_PTS3_6})\)|(?:mặt\s+phẳng\s+đáy|mặt\s+đáy|đáy)(?:\s*\((?P<pld2>{_PTS3_6})\))?)\s+(?:một\s+)?góc)\s+có\s+(?P<tf>{_TRIG_KW_RE})\s*(?:bằng|là|=)\s*(?P<tval>(?:-\s*)?{_VAL}){_OPT_ANY_UNIT_TAIL})",
    ):
        for m_lt in re.finditer(lpa_t_pat, ctext_norm, re.IGNORECASE | re.UNICODE):
            if any(a <= m_lt.start("full") < b for a, b in angle_spans):
                continue
            if re.search(r"\b(?:tính|tìm|xác\s+định|hỏi)\b", ctext_norm[: m_lt.start("full")].rstrip(), re.IGNORECASE):
                continue
            tv = _canon_val(re.sub(r"\s+", "", m_lt.group("tval")))
            if not _is_valid_val(tv):
                continue
            ln_s = m_lt.groupdict().get("ln") or m_lt.groupdict().get("ln2") or ""
            pl_s = (
                m_lt.groupdict().get("pl")
                or m_lt.groupdict().get("pld")
                or m_lt.groupdict().get("pl2")
                or m_lt.groupdict().get("pld2")
            )
            plane_pts = _split_pts(pl_s) if pl_s else list(builder._base_vertices)
            line_pts = _split_pts(ln_s)
            if len(line_pts) == 2 and len(plane_pts) >= 3:
                sid_lpa = builder._primary_solid_id
                for s_cand in builder.solids:
                    if s_cand["solid_type"] == "pyramid" and s_cand["notation"].split(".", 1)[0] in line_pts:
                        sid_lpa = s_cand["solid_id"]
                        break
                q_lt = _clean_quote(raw, ca + m_lt.start("full"), ca + m_lt.end("full"))
                builder.premises.append(
                    {
                        "kind": "line_plane_angle",
                        "args": {
                            "line": line_pts,
                            "plane": plane_pts,
                            "value": tv,
                            "unit": _canon_trig_unit(m_lt.group("tf")),
                        },
                        "quote": q_lt,
                        "solid_id": sid_lpa,
                    }
                )
                angle_spans.append((m_lt.start("full"), m_lt.end("full")))
                mapped_fact = True

    for ppa_t_pat in (
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?P<tf>{_TRIG_KW_RE})\s+(?:của\s+)?(?:số\s+đo\s+)?góc\s+(?:giữa|tạo\s+bởi|hợp\s+bởi)\s+(?:hai\s+mặt\s+phẳng\s+|mặt\s+phẳng\s+|mặt\s+bên\s+|mp\s*)?\((?P<p1>{_PTS3_6})\)\s+(?:và|với)\s+(?:(?:mặt\s+phẳng\s+|mặt\s+bên\s+|mp\s*)?\((?P<p2>{_PTS3_6})\)|(?:mặt\s+phẳng\s+đáy|mặt\s+đáy|đáy)(?:\s*\((?P<p2d>{_PTS3_6})\))?)\s*(?:bằng|là|=)\s*(?P<tval>(?:-\s*)?{_VAL}){_OPT_ANY_UNIT_TAIL})",
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:(?:số\s+đo\s+)?góc\s+(?:giữa|tạo\s+bởi|hợp\s+bởi)\s+(?:hai\s+mặt\s+phẳng\s+|mặt\s+phẳng\s+|mặt\s+bên\s+|mp\s*)?\((?P<p1>{_PTS3_6})\)\s+(?:và|với)\s+(?:(?:mặt\s+phẳng\s+|mặt\s+bên\s+|mp\s*)?\((?P<p2>{_PTS3_6})\)|(?:mặt\s+phẳng\s+đáy|mặt\s+đáy|đáy)(?:\s*\((?P<p2d>{_PTS3_6})\))?)|(?:mặt\s+bên\s+|mặt\s+phẳng\s+|mp\s*)?\((?P<p1b>{_PTS3_6})\)\s+(?:tạo|hợp)\s+với\s+(?:(?:mặt\s+phẳng\s+|mặt\s+bên\s+|mp\s*)?\((?P<p2b>{_PTS3_6})\)|(?:mặt\s+phẳng\s+đáy|mặt\s+đáy|đáy)(?:\s*\((?P<p2db>{_PTS3_6})\))?)\s+(?:một\s+)?góc)\s+có\s+(?P<tf>{_TRIG_KW_RE})\s*(?:bằng|là|=)\s*(?P<tval>(?:-\s*)?{_VAL}){_OPT_ANY_UNIT_TAIL})",
    ):
        for m_pt_a in re.finditer(ppa_t_pat, ctext_norm, re.IGNORECASE | re.UNICODE):
            if any(a <= m_pt_a.start("full") < b for a, b in angle_spans):
                continue
            if re.search(r"\b(?:tính|tìm|xác\s+định|hỏi)\b", ctext_norm[: m_pt_a.start("full")].rstrip(), re.IGNORECASE):
                continue
            tv = _canon_val(re.sub(r"\s+", "", m_pt_a.group("tval")))
            if not _is_valid_val(tv):
                continue
            p1_s = m_pt_a.groupdict().get("p1") or m_pt_a.groupdict().get("p1b") or ""
            p2_s = (
                m_pt_a.groupdict().get("p2")
                or m_pt_a.groupdict().get("p2d")
                or m_pt_a.groupdict().get("p2b")
                or m_pt_a.groupdict().get("p2db")
            )
            p1_pts = _split_pts(p1_s)
            p2_pts = _split_pts(p2_s) if p2_s else list(builder._base_vertices)
            if len(p1_pts) >= 3 and len(p2_pts) >= 3:
                q_pt_a = _clean_quote(raw, ca + m_pt_a.start("full"), ca + m_pt_a.end("full"))
                builder.premises.append(
                    {
                        "kind": "plane_plane_angle",
                        "args": {
                            "plane1": p1_pts,
                            "plane2": p2_pts,
                            "value": tv,
                            "unit": _canon_trig_unit(m_pt_a.group("tf")),
                        },
                        "quote": q_pt_a,
                        "solid_id": builder._primary_solid_id,
                    }
                )
                angle_spans.append((m_pt_a.start("full"), m_pt_a.end("full")))
                mapped_fact = True

    for lla_t_pat in (
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?P<tf>{_TRIG_KW_RE})\s+(?:của\s+)?(?:số\s+đo\s+)?góc\s+(?:giữa|tạo\s+bởi|hợp\s+bởi)\s+(?:hai\s+đường\s+thẳng\s+|đường\s+thẳng\s+|cạnh\s+)?(?P<l1>{_PTS2})\s+(?:và|với)\s+(?:đường\s+thẳng\s+|cạnh\s+)?(?P<l2>{_PTS2})\s*(?:bằng|là|=)\s*(?P<tval>(?:-\s*)?{_VAL}){_OPT_ANY_UNIT_TAIL})",
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:(?:số\s+đo\s+)?góc\s+(?:giữa|tạo\s+bởi|hợp\s+bởi)\s+(?:hai\s+đường\s+thẳng\s+|đường\s+thẳng\s+|cạnh\s+)?(?P<l1>{_PTS2})\s+(?:và|với)\s+(?:đường\s+thẳng\s+|cạnh\s+)?(?P<l2>{_PTS2})|(?:đường\s+thẳng\s+|cạnh\s+)?(?<![\w'.(])(?P<l1b>{_PTS2})\s+(?:tạo|hợp)\s+với\s+(?:đường\s+thẳng\s+|cạnh\s+)?(?P<l2b>{_PTS2})(?![\w')])\s+(?:một\s+)?góc)\s+có\s+(?P<tf>{_TRIG_KW_RE})\s*(?:bằng|là|=)\s*(?P<tval>(?:-\s*)?{_VAL}){_OPT_ANY_UNIT_TAIL})",
    ):
        for m_llt in re.finditer(lla_t_pat, ctext_norm, re.IGNORECASE | re.UNICODE):
            if any(a <= m_llt.start("full") < b for a, b in angle_spans):
                continue
            if re.search(r"\b(?:tính|tìm|xác\s+định|hỏi)\b", ctext_norm[: m_llt.start("full")].rstrip(), re.IGNORECASE):
                continue
            tv = _canon_val(re.sub(r"\s+", "", m_llt.group("tval")))
            if not _is_valid_val(tv):
                continue
            l1_s = m_llt.groupdict().get("l1") or m_llt.groupdict().get("l1b") or ""
            l2_s = m_llt.groupdict().get("l2") or m_llt.groupdict().get("l2b") or ""
            q_llt = _clean_quote(raw, ca + m_llt.start("full"), ca + m_llt.end("full"))
            builder.premises.append(
                {
                    "kind": "line_line_angle",
                    "args": {
                        "line1": _split_pts(l1_s),
                        "line2": _split_pts(l2_s),
                        "value": tv,
                        "unit": _canon_trig_unit(m_llt.group("tf")),
                    },
                    "quote": q_llt,
                    "solid_id": builder._primary_solid_id,
                }
            )
            angle_spans.append((m_llt.start("full"), m_llt.end("full")))
            mapped_fact = True

    for vang_t_pat in (
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?P<tf>{_TRIG_KW_RE})\s*(?:\(\s*)?(?:(?:của\s+)?(?:góc\s+|[∠^]\s*)(?P<p3>{_PTS3})|(?<![\w'.])(?P<p3b>{_PTS3}))(?![\w'])\s*\)?\s*(?:bằng|là|=)\s*(?P<tval>(?:-\s*)?{_VAL}){_OPT_ANY_UNIT_TAIL})",
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?:góc\s+|[∠^]\s*)(?P<p3>{_PTS3})(?![\w'])\s+có\s+(?P<tf>{_TRIG_KW_RE})\s*(?:bằng|là|=)\s*(?P<tval>(?:-\s*)?{_VAL}){_OPT_ANY_UNIT_TAIL})",
    ):
        for m_vt in re.finditer(vang_t_pat, ctext_norm, re.IGNORECASE | re.UNICODE):
            if any(a <= m_vt.start("full") < b for a, b in angle_spans):
                continue
            if re.search(r"\b(?:tính|tìm|xác\s+định|hỏi)\b", ctext_norm[: m_vt.start("full")].rstrip(), re.IGNORECASE):
                continue
            tv = _canon_val(re.sub(r"\s+", "", m_vt.group("tval")))
            if not _is_valid_val(tv):
                continue
            pts3 = _split_pts(m_vt.groupdict().get("p3") or m_vt.groupdict().get("p3b") or "")
            if len(pts3) == 3 and len(set(pts3)) == 3:
                q_vt = _clean_quote(raw, ca + m_vt.start("full"), ca + m_vt.end("full"))
                builder.premises.append(
                    {
                        "kind": "vertex_angle",
                        "args": {
                            "vertex": pts3[1],
                            "rays": [pts3[0], pts3[2]],
                            "value": tv,
                            "unit": _canon_trig_unit(m_vt.group("tf")),
                        },
                        "quote": q_vt,
                        "solid_id": builder._primary_solid_id,
                    }
                )
                angle_spans.append((m_vt.start("full"), m_vt.end("full")))
                mapped_fact = True

    for m_vht in re.finditer(
        rf"(?P<full>(?:Biết(?:\s+rằng)?\s+)?(?P<tf>{_TRIG_KW_RE})\s*(?:\(\s*)?(?:(?:của\s+)?(?:\\hat\s*\{{\s*(?P<vh1>{_PT})\s*\}}|(?<![\w'.])(?P<vh2>(?:[\u00C2\u00CA\u00D4][0-9]*'?|{_PT}(?:\u0302|\s*\^)))|góc\s+(?P<vh3>{_PT})))(?![\w'])\s*\)?\s*(?:bằng|là|=)\s*(?P<tval>(?:-\s*)?{_VAL}){_OPT_ANY_UNIT_TAIL})",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        if any(a <= m_vht.start("full") < b for a, b in angle_spans):
            continue
        if re.search(r"\b(?:tính|tìm|xác\s+định|hỏi)\b", ctext_norm[: m_vht.start("full")].rstrip(), re.IGNORECASE):
            continue
        tv = _canon_val(re.sub(r"\s+", "", m_vht.group("tval")))
        if not _is_valid_val(tv):
            continue
        raw_vh = m_vht.group("vh1") or m_vht.group("vh2") or m_vht.group("vh3") or ""
        v_clean = unicodedata.normalize("NFD", raw_vh).replace("\u0302", "").replace("^", "").strip().upper()
        if len(builder._base_vertices) == 3 and v_clean in builder._base_vertices:
            rays = [p for p in builder._base_vertices if p != v_clean]
            q_vht = _clean_quote(raw, ca + m_vht.start("full"), ca + m_vht.end("full"))
            builder.premises.append(
                {
                    "kind": "vertex_angle",
                    "args": {
                        "vertex": v_clean,
                        "rays": rays,
                        "value": tv,
                        "unit": _canon_trig_unit(m_vht.group("tf")),
                    },
                    "quote": q_vht,
                    "solid_id": builder._primary_solid_id,
                }
            )
            angle_spans.append((m_vht.start("full"), m_vht.end("full")))
            mapped_fact = True

    # ── 4. Segment Length Assignments & Ratios ───────────────────────────────────────────────────────────────────
    # 4a-0. Segment length ratio (`AD = 2BC`, `AD = 2/3 BC`, `AD = BC/2`) outside `sao cho` / `thỏa mãn`
    for m_srat in re.finditer(
        rf"(?P<full>(?:(?:độ\s+dài|cạnh|đoạn(?:\s+thẳng)?)\s+)?(?<![\w'./])(?P<s1>{_PTS2})\s*(?:=|bằng)\s*(?:(?P<rat>{_SCALAR_COEFF})\s*(?:lần\s+|\.\s*|\*\s*)?(?P<s2>{_PTS2})|(?P<s2b>{_PTS2})\s*/\s*(?P<kdiv>\d+)))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        pref_sr = ctext_norm[: m_srat.start("full")].rstrip()
        if re.search(r"(?:sao\s+cho|thỏa\s+mãn)$", pref_sr, re.IGNORECASE):
            continue
        s1_pts = _split_pts(m_srat.group("s1"))
        s2_pts = _split_pts(m_srat.group("s2") or m_srat.group("s2b"))
        m_pt_div_pref = re.search(
            rf"(?<![\w'])(?P<pt>{_PT})\s+(?:là\s+(?:một\s+)?điểm\s+)?(?:thuộc|nằm\s+trên|trên)\s+"
            rf"(?:cạnh\s+|đoạn(?:\s+thẳng)?\s+)?(?P<seg>{_PTS2})\s*,?\s*(?:với|biết(?:\s+rằng)?|mà)$",
            pref_sr,
            re.IGNORECASE | re.UNICODE,
        )
        if m_pt_div_pref and m_pt_div_pref.group("pt") in (s1_pts + s2_pts):
            continue
        rat_str = (
            f"1/{m_srat.group('kdiv')}"
            if m_srat.group("kdiv")
            else _canon_val(re.sub(r"\s+", "", m_srat.group("rat")))
        )
        if not _is_valid_scalar_val(rat_str):
            continue
        if len(s1_pts) == 2 and len(s2_pts) == 2 and set(s1_pts) != set(s2_pts):
            q_sr = _clean_quote(raw, ca + m_srat.start("full"), ca + m_srat.end("full"))
            builder.premises.append(
                {
                    "kind": "segment_ratio",
                    "args": {
                        "segment_a": s1_pts,
                        "segment_b": s2_pts,
                        "ratio": rat_str,
                    },
                    "quote": q_sr,
                    "solid_id": builder._primary_solid_id,
                }
            )
            mapped_fact = True

    # 4a-1. Explicit named segment ratio: "Tỉ số hai cạnh AB và CD bằng 2/3" or "AB / CD = 2/3"
    for m_nrat in re.finditer(
        rf"(?P<full>(?:(?:Biết(?:\s+rằng)?|Có|Với)\s+)?(?:(?:tỉ|tỷ)\s+số(?:\s+độ\s+dài)?(?:\s+(?:giữa|của))?(?:\s+hai)?(?:\s+(?:cạnh|đoạn(?:\s+thẳng)?))?\s+(?P<s1>{_PTS2})\s+(?:và|với)\s+(?P<s2>{_PTS2})\s*(?:bằng|là|=)\s*(?P<rat>{_VAL}){_OPT_ANY_UNIT_TAIL}"
        rf"|(?<![\w'./])(?P<s3>{_PTS2})\s*/\s*(?P<s4>{_PTS2})\s*(?:=|bằng)\s*(?P<rat2>{_VAL}){_OPT_ANY_UNIT_TAIL}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        pref_nr = ctext_norm[: m_nrat.start("full")].rstrip()
        if re.search(r"\b(?:tính|tìm|xác\s+định|hỏi)\b", pref_nr, re.IGNORECASE):
            continue
        rat_nr = _canon_val(m_nrat.group("rat") or m_nrat.group("rat2"))
        if not _is_valid_val(rat_nr):
            continue
        sa_nr = _split_pts(m_nrat.group("s1") or m_nrat.group("s3"))
        sb_nr = _split_pts(m_nrat.group("s2") or m_nrat.group("s4"))
        if len(sa_nr) == 2 and len(sb_nr) == 2 and set(sa_nr) != set(sb_nr):
            q_nr = _clean_quote(raw, ca + m_nrat.start("full"), ca + m_nrat.end("full"))
            builder.premises.append(
                {
                    "kind": "segment_ratio",
                    "args": {"segment_a": sa_nr, "segment_b": sb_nr, "ratio": rat_nr},
                    "quote": q_nr,
                    "solid_id": builder._primary_solid_id,
                }
            )
            mapped_fact = True

    # 4a-2. Role-ordered segment ratio: "Tỉ số giữa cạnh bên và cạnh đáy bằng 2/3"
    for m_rrat in re.finditer(
        rf"(?P<full>(?:(?:Biết(?:\s+rằng)?|Có|Với)\s+)?(?:tỉ|tỷ)\s+số(?:\s+độ\s+dài)?(?:\s+(?:giữa|của))?\s+(?P<r1>cạnh\s+bên|cạnh\s+đáy)\s+(?:và|với)\s+(?P<r2>cạnh\s+đáy|cạnh\s+bên)\s*(?:bằng|là|=)\s*(?P<rat>{_VAL}){_OPT_ANY_UNIT_TAIL})",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        pref_rr = ctext_norm[: m_rrat.start("full")].rstrip()
        if re.search(r"\b(?:tính|tìm|xác\s+định|hỏi)\b", pref_rr, re.IGNORECASE):
            continue
        rat_rr = _canon_val(m_rrat.group("rat"))
        if not _is_valid_val(rat_rr):
            continue
        r1_lat = "bên" in m_rrat.group("r1").lower()
        r2_lat = "bên" in m_rrat.group("r2").lower()
        q_rr = _clean_quote(raw, ca + m_rrat.start("full"), ca + m_rrat.end("full"))
        rep_lat: list[str] | None = None
        rep_base: list[str] | None = None
        if len(builder.solids) == 1:
            sol_r = builder.solids[0]
            has_eq_base = any(
                p.get("kind") in ("regular_pyramid", "regular_polygon", "rhombus")
                for p in builder.premises
            )
            if has_eq_base and len(builder._base_vertices) >= 3:
                rep_base = list(builder._base_vertices[:2])
            if sol_r["solid_type"] == "pyramid" and "." in sol_r["notation"] and any(
                p.get("kind") == "regular_pyramid" for p in builder.premises
            ):
                ap_r, b_r = sol_r["notation"].split(".", 1)
                bp_r = _split_pts(b_r)
                if bp_r:
                    rep_lat = [ap_r, bp_r[0]]
            elif sol_r["solid_type"] == "prism" and "." in sol_r["notation"]:
                b_r, t_r = sol_r["notation"].split(".", 1)
                bp_r, tp_r = _split_pts(b_r), _split_pts(t_r)
                if bp_r and tp_r:
                    rep_lat = [bp_r[0], tp_r[0]]
        if r1_lat != r2_lat and rep_lat and rep_base:
            builder.premises.append(
                {
                    "kind": "segment_ratio",
                    "args": {
                        "segment_a": rep_lat if r1_lat else rep_base,
                        "segment_b": rep_lat if r2_lat else rep_base,
                        "ratio": rat_rr,
                    },
                    "quote": q_rr,
                    "solid_id": builder._primary_solid_id,
                }
            )
            mapped_fact = True
        else:
            builder.unresolved.append(
                {
                    "unresolved_id": f"u{len(builder.unresolved) + 1}",
                    "kind": "ambiguous",
                    "quote": q_rr,
                    "missing_roles": [],
                    "candidate_relations": [],
                }
            )
            clause.classification = CLAUSE_MAPPED_FACT
            return

    # 4a-3. Unordered / unnamed ambiguous segment ratio: "Tỉ số hai cạnh bằng 2/3" -> explicit clarification (`AMBIGUOUS_FACT`)
    m_ambig_rat = re.search(
        rf"(?P<full>(?:(?:Biết(?:\s+rằng)?|Có|Với)\s+)?(?:tỉ|tỷ)\s+số(?:\s+độ\s+dài)?(?:\s+(?:giữa|của))?\s+hai\s+(?:cạnh|đoạn(?:\s+thẳng)?)(?:\s+(?:đáy|bên))?\s*(?:bằng|là|=)\s*(?P<rat>{_VAL}))",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_ambig_rat and not re.search(r"\b(?:tính|tìm|xác\s+định|hỏi)\b", ctext_norm[: m_ambig_rat.start("full")], re.IGNORECASE):
        if _is_valid_val(m_ambig_rat.group("rat")):
            q_ar_amb = _clean_quote(raw, ca + m_ambig_rat.start("full"), ca + m_ambig_rat.end("full"))
            builder.unresolved.append(
                {
                    "unresolved_id": f"u{len(builder.unresolved) + 1}",
                    "kind": "ambiguous",
                    "quote": q_ar_amb,
                    "missing_roles": [],
                    "candidate_relations": [],
                }
            )
            clause.classification = CLAUSE_MAPPED_FACT
            return

    for m_chain_eq in re.finditer(
        rf"(?P<full>(?<![\w'./])(?P<s1>{_PTS2})\s*=\s*(?P<s2>{_PTS2})(?:\s*=\s*(?P<s3>{_PTS2}))?\s*=\s*(?P<val>{_VAL}){_OPT_LEN_UNIT_TAIL})(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        if (
            any(a <= m_chain_eq.start("full") < b for a, b in angle_spans)
            or _ANGLE_OR_RATIO_OPERAND_PREFIX_RE.search(ctext_norm[: m_chain_eq.start("full")])
            or not _is_valid_val(m_chain_eq.group("val"))
        ):
            continue
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

    # Bare segment equality (`SA = AB`, `AB = AC = AD`): congruent segments, no value. A value at the end is the chain
    # rule above; a coefficient (`AD = 2BC`) is a ratio; anything else stays unread for the guards below.
    for m_bare_eq in _BARE_SEGMENT_EQUALITY_RE.finditer(ctext_norm):
        if ctext_norm[: m_bare_eq.start("full")].rstrip().endswith("/"):
            continue
        segs = [_split_pts(m_bare_eq.group(g)) for g in ("s1", "s2", "s3") if m_bare_eq.group(g)]
        # Degenerate (`AA`) or repeated (`AB = BA`) segments are not a congruence statement: leave them to the guards.
        if any(len(set(sg)) != 2 for sg in segs) or len({frozenset(sg) for sg in segs}) != len(segs):
            continue
        q_be = _clean_quote(raw, ca + m_bare_eq.start("full"), ca + m_bare_eq.end("full"))
        for sa_pts, sb_pts in zip(segs, segs[1:]):
            builder.premises.append(
                {"kind": "equal_length", "args": {"segment_a": sa_pts, "segment_b": sb_pts},
                 "quote": q_be, "solid_id": builder._primary_solid_id}
            )
        mapped_fact = True

    # Single segment lengths (`AB = 3`, `Đường sinh SA = 3`), skipping those already inside a chain or `đường cao SA = 2`
    for m_seg_len in re.finditer(
        rf"(?P<full>(?:Đường\s+sinh\s+)?(?<![\w'./])(?P<seg>{_PTS2})\s*=\s*(?P<val>{_VAL}){_OPT_LEN_UNIT_TAIL})(?![\s]*=)(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        if any(a <= m_seg_len.start("full") < b for a, b in angle_spans):
            continue
        # Skip if preceded by `= ` or `/ ` or `đường cao ` or structured angle/ratio operand prefix or followed by a segment token (`SM = 1/3 SA`)
        prefix_slice = ctext_norm[: m_seg_len.start("full")].rstrip()
        suffix_slice = ctext_norm[m_seg_len.end("full") :]
        if (
            prefix_slice.endswith("=")
            or prefix_slice.endswith("/")
            or re.search(r"(?:đường\s+cao|chiều\s+cao)$", prefix_slice, re.IGNORECASE)
            or _ANGLE_OR_RATIO_OPERAND_PREFIX_RE.search(ctext_norm[: m_seg_len.start("full")])
            or re.match(rf"^\s*{_PTS2}(?![\w'])", suffix_slice)
            or not _is_valid_val(m_seg_len.group("val"))
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
        rf"(?P<full>Gọi\s+(?P<p1>{_PT})\s*(?:[,;]\s*|\s+và\s+)(?P<p2>{_PT})(?:\s*(?:[,;]\s*|\s+và\s+)(?P<p3>{_PT}))?\s+lần\s+lượt\s+là\s+trung\s+điểm\s+của(?:\s+các\s+cạnh)?\s+(?P<s1>{_PTS2})\s*(?:[,;]\s*|\s+và\s+)(?P<s2>{_PTS2})(?:\s*(?:[,;]\s*|\s+và\s+)(?P<s3>{_PTS2}))?)",
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

    # 5b-2. Point divides segment: "(Gọi |Điểm )?M (là điểm )?(thuộc|nằm trên) (cạnh )?SA (sao cho|với) SM = 1/3 SA"
    for m_div in re.finditer(
        rf"(?P<full>(?:Gọi\s+|Điểm\s+)?(?<![\w'])(?P<pt>{_PT})\s+(?:là\s+(?:một\s+)?điểm\s+)?(?:thuộc|nằm\s+trên|trên)\s+(?:cạnh\s+|đoạn(?:\s+thẳng)?\s+)?(?P<seg>{_PTS2})\s*,?\s*(?:sao\s+cho|thỏa\s+mãn|với|biết(?:\s+rằng)?|mà)\s+(?P<subseg>{_PTS2})\s*=\s*(?P<rat>\d+\s*/\s*\d+)\s*(?P<seg2>{_PTS2}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        pt_d = m_div.group("pt")
        seg_d = _split_pts(m_div.group("seg"))
        sub_d = _split_pts(m_div.group("subseg"))
        seg2_d = _split_pts(m_div.group("seg2"))
        if not pt_d[0].isupper() or len(seg_d) != 2 or len(sub_d) != 2 or len(seg2_d) != 2 or pt_d in seg_d:
            continue
        if set(seg2_d) != set(seg_d) or pt_d not in sub_d:
            continue
        other_d = next((x for x in sub_d if x != pt_d), None)
        if other_d not in seg_d:
            continue
        opp_d = next(x for x in seg_d if x != other_d)
        q_div = _clean_quote(raw, ca + m_div.start("full"), ca + m_div.end("full"))
        builder.premises.append(
            {
                "kind": "point_divides_segment",
                "args": {
                    "point": pt_d,
                    "segment": [other_d, opp_d],
                    "ratio": re.sub(r"\s+", "", m_div.group("rat")),
                },
                "quote": q_div,
                "solid_id": builder._primary_solid_id,
            }
        )
        mapped_fact = True

    # 5b-3. Internal division by a part-to-part ratio: "(Gọi |Điểm )?E (là điểm )?(thuộc|nằm trên) (cạnh )?SC (sao cho|với) SE = 3EC"
    # The two parts must be [end, point] and [point, other end] of the stated segment; t = AP/AB = k/(k + 1).
    for m_dv2 in re.finditer(
        rf"(?P<full>(?:Gọi\s+|Điểm\s+)?(?<![\w'])(?P<pt>{_PT})\s+(?:là\s+(?:một\s+)?điểm\s+)?(?:thuộc|nằm\s+trên|trên)\s+(?:cạnh\s+|đoạn(?:\s+thẳng)?\s+)?(?P<seg>{_PTS2})\s*,?\s*(?:sao\s+cho|thỏa\s+mãn|với|biết(?:\s+rằng)?|mà)\s+(?P<p1>{_PTS2})\s*=\s*(?P<k>\d+(?:\s*/\s*\d+)?)\s*(?P<p2>{_PTS2}))(?![\w'/])",
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

    # 5c'. §19 Explicit polygon center: "(Gọi/Đặt )?O là tâm (đối xứng )?(của )?(đáy|hình ...|ABC...)" / "tâm O của ..."
    for m_pctr in re.finditer(
        rf"(?P<full>(?:(?P<lead>gọi|đặt|lấy|chọn|với|biết)\s+)?(?<![\w'])(?P<pt>{_PT})\s+là\s+(?<!trọng\s)tâm(?:\s+đối\s+xứng)?(?:\s+của)?\s+(?P<obj>(?:(?:hình\s+vuông|hình\s+chữ\s+nhật|hình\s+thoi|hình\s+bình\s+hành|tam\s+giác(?:\s+đều)?|tứ\s+giác\s+đều|lục\s+giác\s+đều|đa\s+giác\s+đều|mặt\s+đáy|đáy)\s*)?\(?(?P<poly>{_PTS3_6})\)?|(?:mặt\s+)?đáy(?:\s+\(?(?P<poly_d>{_PTS3_6})\)?)?)"
        rf"|(?<![\w'])tâm(?:\s+đối\s+xứng)?\s+(?P<pt2>{_PT})\s+của\s+(?P<obj2>(?:(?:hình\s+vuông|hình\s+chữ\s+nhật|hình\s+thoi|hình\s+bình\s+hành|tam\s+giác(?:\s+đều)?|tứ\s+giác\s+đều|lục\s+giác\s+đều|đa\s+giác\s+đều|mặt\s+đáy|đáy)\s*)?\(?(?P<poly2>{_PTS3_6})\)?|(?:mặt\s+)?đáy(?:\s+\(?(?P<poly_d2>{_PTS3_6})\)?)?))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        pt_c = m_pctr.group("pt") or m_pctr.group("pt2")
        if not pt_c or not pt_c[0].isupper():
            continue
        if any(
            p.get("kind") in ("midpoint", "centroid") and p.get("args", {}).get("point") == pt_c
            for p in builder.premises
        ):
            continue
        if re.search(r"mặt\s+cầu|khối\s+cầu|hình\s+cầu|nội\s+tiếp|ngoại\s+tiếp|đường\s+tròn", ctext_norm, re.IGNORECASE):
            continue
        raw_poly = m_pctr.group("poly") or m_pctr.group("poly_d") or m_pctr.group("poly2") or m_pctr.group("poly_d2")
        verts_c = _split_pts(raw_poly) if raw_poly else list(builder._base_vertices)
        lead_c = (m_pctr.group("lead") or "").lower()
        q_start = m_pctr.start("pt") if lead_c in ("lấy", "chọn", "với", "biết") else m_pctr.start("full")
        q_pctr = _clean_quote(raw, ca + q_start, ca + m_pctr.end("full"))
        if _emit_proved_polygon_center(builder, pt_c, verts_c, q_pctr):
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

    # 5f-bis (semantic-to-scene3d). The projection's IMAGE is a named point defined in place by a descriptor:
    # "hình chiếu vuông góc của S lên (mặt phẳng) (ABC)/đáy trùng với trọng tâm G của tam giác ABC" (or "trung điểm H
    # của (cạnh) AB"). Two facts, each with its own quote: the descriptor (centroid / midpoint) and the projection.
    # The image must be NAMED in the source — an unnamed "trọng tâm của tam giác ABC" stays unparsed (no invented label).
    for m_pr_d in re.finditer(
        rf"(?P<full>hình\s+chiếu\s+(?:vuông\s+góc\s+)?của\s+(?:điểm\s+)?(?P<src>{_PT})\s+(?:lên|trên|xuống)\s+"
        rf"(?:(?:mặt\s+phẳng\s+|mp\s*)?\((?P<plane>{_PTS3_6})\)|(?:mặt\s+phẳng\s+)?(?P<day>đáy))\s+(?:là|trùng\s+với)\s+"
        rf"(?P<desc>(?:điểm\s+)?(?P<dk>trọng\s+tâm|trung\s+điểm)\s+(?P<img>{_PT})\s+(?:của\s+)?"
        rf"(?:tam\s+giác\s+(?P<tri>{_PTS3})|(?:(?:cạnh|đoạn(?:\s+thẳng)?)\s+)?(?P<seg>{_PTS2}))))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        src_d, img_d = m_pr_d.group("src"), m_pr_d.group("img")
        plane_d = _split_pts(m_pr_d.group("plane")) if m_pr_d.group("plane") else list(builder._base_vertices)
        centroid = m_pr_d.group("dk").lower().startswith("trọng")
        operand = m_pr_d.group("tri") if centroid else m_pr_d.group("seg")
        if (not src_d[0].isupper() or not img_d[0].isupper() or len(plane_d) < 3 or operand is None
                or img_d in _split_pts(operand) or src_d in plane_d):
            continue
        q_desc = _clean_quote(raw, ca + m_pr_d.start("desc"), ca + m_pr_d.end("desc"))
        q_full_d = _clean_quote(raw, ca + m_pr_d.start("full"), ca + m_pr_d.end("full"))
        builder.premises.append(
            {"kind": "centroid", "args": {"point": img_d, "polygon": _split_pts(operand)}, "quote": q_desc,
             "solid_id": builder._primary_solid_id} if centroid else
            {"kind": "midpoint", "args": {"point": img_d, "segment": _split_pts(operand)}, "quote": q_desc,
             "solid_id": builder._primary_solid_id})
        builder.premises.append(
            {"kind": "orthogonal_projection", "args": {"point": src_d, "image": img_d, "plane": plane_d},
             "quote": q_full_d, "solid_id": builder._primary_solid_id})
        mapped_fact = True

    # 5f-bis-u (`D-C` unnamed `@id` projection target): "Hình chiếu vuông góc của B' lên (ABC) trùng với trọng tâm của tam giác ABC"
    for m_pr_u in re.finditer(
        rf"(?P<full>hình\s+chiếu\s+(?:vuông\s+góc\s+)?của\s+(?:điểm\s+)?(?P<src>{_PT})\s+(?:lên|trên|xuống)\s+"
        rf"(?:(?:mặt\s+phẳng\s+|mp\s*)?\((?P<plane>{_PTS3_6})\)|(?:mặt\s+phẳng\s+)?(?P<day>đáy))\s+(?:là|trùng\s+với)\s+"
        rf"(?P<desc>[^.,;]+?))(?=$|[.,;])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        src_u = m_pr_u.group("src")
        plane_u = _split_pts(m_pr_u.group("plane")) if m_pr_u.group("plane") else list(builder._base_vertices)
        desc_u = m_pr_u.group("desc").strip()
        if (not src_u[0].isupper() or len(plane_u) < 3 or src_u in plane_u
                or re.fullmatch(rf"(?:điểm\s+)?{_PT}", desc_u)
                or re.match(rf"(?:điểm\s+)?(?:trọng\s+tâm|trung\s+điểm)\s+{_PT}\s+của\b", desc_u, re.IGNORECASE)):
            continue
        d_ref = builder.parse_point_or_described(desc_u, ca + m_pr_u.start("desc"))
        if not d_ref or not d_ref.startswith("@"):
            continue
        q_full_u = _clean_quote(raw, ca + m_pr_u.start("full"), ca + m_pr_u.end("full"))
        builder.premises.append(
            {"kind": "orthogonal_projection", "args": {"point": src_u, "image": d_ref, "plane": plane_u},
             "quote": q_full_u, "solid_id": builder._primary_solid_id})
        mapped_fact = True

    # 5f-sym (`D-B` + `D-C` point reflection): plural `lần lượt` across midpoints (`vmmu_r277`) & singular general
    plural_sym_spans: list[tuple[int, int]] = []
    for m_sym_pl in re.finditer(
        rf"(?P<full>(?:Gọi\s+)?(?P<imgs>{_PT}(?:\s*(?:,|và)\s*{_PT})+)\s+lần\s+lượt\s+là\s+(?:các\s+)?điểm\s+đối\s+xứng\s+"
        rf"(?:với|của)\s+(?:điểm\s+|đỉnh\s+)?(?P<pt>{_PT})\s+qua\s+trung\s+điểm\s+"
        rf"(?:(?:hai|ba|bốn|năm|sáu|\d+)\s+)?(?:các\s+)?(?:(?:cạnh|đoạn(?:\s+thẳng)?)\s+)?"
        rf"(?P<segs>{_PTS2}(?:\s*(?:,|và)\s*{_PTS2})+)(?:\s+của\s+(?:tam\s+giác|tứ\s+giác|hình\s+\w+|đáy)\s+{_PTS3_6})?)(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        imgs = _split_pts(m_sym_pl.group("imgs"))
        pt_s = m_sym_pl.group("pt")
        segs = [_split_pts(sg) for sg in re.findall(_PTS2, m_sym_pl.group("segs"))]
        if (len(imgs) != len(segs) or len(imgs) < 2 or len(set(imgs)) != len(imgs)
                or not pt_s[0].isupper() or pt_s in imgs
                or any(len(s) != 2 or len(set(s)) != 2 for s in segs)):
            continue
        q_sym = _clean_quote(raw, ca + m_sym_pl.start("full"), ca + m_sym_pl.end("full"))
        plural_sym_spans.append((m_sym_pl.start("full"), m_sym_pl.end("full")))
        for img_i, seg_i in zip(imgs, segs):
            mid_ref = builder._register_described_point({"kind": "midpoint", "segment": seg_i, "quote": q_sym})
            builder.premises.append({
                "kind": "point_reflection",
                "args": {"point": pt_s, "center": mid_ref, "image": img_i},
                "quote": q_sym,
                "solid_id": builder._primary_solid_id,
            })
        mapped_fact = True

    for pat_sym in (
        rf"(?P<full>(?:Gọi\s+)?(?P<img>{_PT})\s+là\s+điểm\s+đối\s+xứng\s+(?:với|của)\s+(?:điểm\s+|đỉnh\s+)?(?P<pt>{_PT})\s+qua\s+(?P<ctr>[^.,;]+?))(?=$|[.,;])",
        rf"(?P<full>[Đđ]iểm\s+đối\s+xứng\s+(?:với|của)\s+(?:điểm\s+|đỉnh\s+)?(?P<pt>{_PT})\s+qua\s+(?P<ctr>[^.,;]+?)\s+(?:là|trùng\s+với)\s+(?:điểm\s+)?(?P<img>{_PT}))(?=$|[.,;])",
    ):
        for m_sym in re.finditer(pat_sym, ctext_norm, re.IGNORECASE | re.UNICODE):
            if any(a0 <= m_sym.start("full") < b0 for a0, b0 in plural_sym_spans):
                continue
            img_s, pt_s, ctr_txt = m_sym.group("img"), m_sym.group("pt"), m_sym.group("ctr").strip()
            if not img_s[0].isupper() or not pt_s[0].isupper() or img_s == pt_s:
                continue
            m_named_c = re.fullmatch(rf"(?:điểm\s+|đỉnh\s+)?(?P<c>{_PT})", ctr_txt, re.IGNORECASE | re.UNICODE)
            if m_named_c and m_named_c.group("c")[0].isupper():
                ctr_ref = m_named_c.group("c")
            else:
                ctr_ref = builder.parse_point_or_described(ctr_txt, ca + m_sym.start("ctr"))
            if not ctr_ref or ctr_ref in (pt_s, img_s):
                continue
            q_sym = _clean_quote(raw, ca + m_sym.start("full"), ca + m_sym.end("full"))
            builder.premises.append({
                "kind": "point_reflection",
                "args": {"point": pt_s, "center": ctr_ref, "image": img_s},
                "quote": q_sym,
                "solid_id": builder._primary_solid_id,
            })
            mapped_fact = True

    # 5f-ter (semantic-to-scene3d). A lateral face perpendicular to the base: "(mặt bên / tam giác) SAB … nằm trong mặt
    # phẳng vuông góc với (mặt phẳng) đáy" or "(SAB) ⊥ (ABCD)" / "mặt phẳng (SAB) vuông góc với mặt phẳng đáy". The face
    # is three labels of the primary solid, not the base itself; the base is the solid's base (by name or "đáy").
    dinh_khoi = {x for sd in builder.solids for x in _split_pts(str(sd.get("notation") or "").replace(".", ""))}
    for m_fp in re.finditer(
        rf"(?P<full>(?:mặt\s+bên\s+|tam\s+giác\s+)\(?(?P<face>{_PTS3})\)?(?:\s+(?!vuông\b)[^.;]{{0,40}}?)?\s+nằm\s+trong\s+"
        rf"mặt\s+phẳng\s+vuông\s+góc\s+với\s+(?:(?:mặt\s+phẳng\s+)?(?P<day>đáy)|(?:mặt\s+phẳng\s+)?\((?P<base>{_PTS3_6})\))"
        rf"|(?:mặt\s+phẳng\s+|mp\s*)?\((?P<face2>{_PTS3})\)\s*(?:⊥|vuông\s+góc\s+với)\s*"
        rf"(?:(?:mặt\s+phẳng\s+)?(?P<day2>đáy)|(?:mặt\s+phẳng\s+|mp\s*)?\((?P<base2>{_PTS3_6})\)))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        face_f = _split_pts(m_fp.group("face") or m_fp.group("face2"))
        base_g = m_fp.group("base") or m_fp.group("base2")
        base_f = _split_pts(base_g) if base_g else list(builder._base_vertices)
        if (len(base_f) < 3 or set(base_f) != set(builder._base_vertices) or set(face_f) <= set(base_f)
                or not set(face_f) <= dinh_khoi):
            continue
        q_fp = _clean_quote(raw, ca + m_fp.start("full"), ca + m_fp.end("full"))
        builder.premises.append(
            {"kind": "face_perpendicular_base", "args": {"face": face_f, "base": base_f}, "quote": q_fp,
             "solid_id": builder._primary_solid_id})
        mapped_fact = True

    # 5g. Line-plane intersection point: "(Gọi )?I là giao điểm của AC' và mặt phẳng (A'BD)" or "Mặt phẳng (SAD) và đường thẳng ME cắt nhau tại I"
    for m_ilp in re.finditer(
        rf"(?P<full>(?:Gọi\s+)?(?<![\w'])(?P<pt>{_PT})\s+là\s+giao\s+điểm(?:\s+của)?\s+(?:đường\s+thẳng\s+|cạnh\s+|đường\s+chéo\s+)?(?P<line>{_PTS2})\s+(?:và|với)\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<plane>{_PTS3_6})\)"
        rf"|(?:(?:mặt\s+phẳng\s+|mp\s*)?\((?P<pl2>{_PTS3_6})\)\s+(?:và|với)\s+(?:đường\s+thẳng\s+|cạnh\s+)?(?P<ln2>{_PTS2})\s+cắt\s+nhau"
        rf"|(?:đường\s+thẳng\s+|cạnh\s+)?(?P<ln3>{_PTS2})\s+(?:(?:và|với)\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<pl3>{_PTS3_6})\)\s+cắt\s+nhau|cắt\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<pl4>{_PTS3_6})\)))\s+(?:tại|ở)\s+(?:(?:điểm|giao\s+điểm)\s+)?(?P<pt2>{_PT}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        pt_i = m_ilp.group("pt") or m_ilp.group("pt2")
        ln_i = m_ilp.group("line") or m_ilp.group("ln2") or m_ilp.group("ln3")
        pl_i = m_ilp.group("plane") or m_ilp.group("pl2") or m_ilp.group("pl3") or m_ilp.group("pl4")
        if not pt_i or not pt_i[0].isupper() or not ln_i or not pl_i:
            continue
        q_ilp = _clean_quote(raw, ca + m_ilp.start("full"), ca + m_ilp.end("full"))
        builder.premises.append(
            {
                "kind": "intersect_line_plane",
                "args": {
                    "point": pt_i,
                    "line": _split_pts(ln_i),
                    "plane": _split_pts(pl_i),
                },
                "quote": q_ilp,
                "solid_id": builder._primary_solid_id,
            }
        )
        mapped_fact = True

    # 5g-2. Area symbol definition (`Gọi S1; S2 lần lượt là diện tích tam giác SMI và tứ giác BCEM`)
    m_area_sym = re.search(
        rf"(?P<full>(?:Gọi|Kí\s+hiệu|Đặt)\s+(?P<s1>S\d+)\s*[,;]\s*(?P<s2>S\d+)\s+lần\s+lượt\s+là\s+diện\s+tích(?:\s+của)?\s+(?:(?:tam\s+giác|tứ\s+giác|đa\s+giác|hình\s+\w+)\s+)?(?P<p1>{_PTS3_6})\s+và\s+(?:diện\s+tích(?:\s+của)?\s+)?(?:(?:tam\s+giác|tứ\s+giác|đa\s+giác|hình\s+\w+)\s+)?(?P<p2>{_PTS3_6}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_area_sym:
        builder._area_symbol_map[m_area_sym.group("s1").upper()] = _split_pts(m_area_sym.group("p1"))
        builder._area_symbol_map[m_area_sym.group("s2").upper()] = _split_pts(m_area_sym.group("p2"))
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
        rf"(?:(?:Gọi\s+\((?P<p1>{_PT}|[α-ω]'?)\)\s+là\s+mặt\s+phẳng|Mặt\s+phẳng\s+\((?P<p2>{_PT}|[α-ω]'?)\)"
        # (compositional-semantics-simulation-goals) the bare name opening a "biết …" clause, the definition given after
        # the question that uses it: "…bởi mặt phẳng (P), biết (P) đi qua M và song song với mặt đáy"
        rf"|(?:(?<=biết\s)|(?<=biết\srằng\s)|(?<=^))\((?P<p2b>{_PT}|[α-ω]'?)\))\s+(?:đi\s+qua|qua|chứa)\s+(?P<thru>[^,;]+?)|Qua\s+(?P<thru2>{_PT})\s+(?:kẻ|dựng)\s+mặt\s+phẳng\s+\((?P<p3>{_PT}|[α-ω]'?)\))(?:\s*,\s*(?:và\s+)?|\s+và\s+|\s+)(?:(?P<par>song\s+song\s+với\s+(?:(?:mặt\s+phẳng\s+|mp\s*|đáy\s*)?\((?P<pplane>{_PTS3_6})\)|(?P<pday>(?:mặt\s+phẳng\s+|mặt\s+)?đáy)(?![\w])))|(?P<perp>vuông\s+góc\s+với\s+(?:đường\s+thẳng\s+|cạnh\s+)?(?P<pline>{_PTS2})))(?P<cuts>(?:\s*,\s*(?:\([A-Za-z0-9'α-ω]+\)\s+)?|\s+(?:và\s+)?)cắt\s+.+)?",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_sec_par_or_perp:
        pname = (m_sec_par_or_perp.group("p1") or m_sec_par_or_perp.group("p2") or m_sec_par_or_perp.group("p2b")
                 or m_sec_par_or_perp.group("p3"))
        thru_str = (m_sec_par_or_perp.group("thru") or m_sec_par_or_perp.group("thru2")).strip()
        # Exclude if `thru_str` is comma-separated multiple points (which belongs to constrained plane 6d)
        if not re.fullmatch(rf"{_PT}\s*(?:,\s*{_PT})+", thru_str) and "," not in thru_str:
            thru_offset = m_sec_par_or_perp.start("thru") if m_sec_par_or_perp.group("thru") else m_sec_par_or_perp.start("thru2")
            # a NAMED point defined in place (semantic-failure-safe-image-segmentation): "trung điểm M của (cạnh) SA",
            # "trọng tâm G của tam giác ABC" — the descriptor becomes its own premise with its own quote and the plane goes
            # through the named label; a label already defined by a midpoint / centroid premise is not redefined here
            m_rel = re.fullmatch(
                rf"(?:điểm\s+)?(?P<dk>trung\s+điểm|trọng\s+tâm)\s+(?P<pt>{_PT})\s+của\s+(?:(?:(?:cạnh|đoạn(?:\s+thẳng)?)\s+)?(?P<seg>{_PTS2})|tam\s+giác\s+(?P<tri>{_PTS3}))",
                thru_str, re.IGNORECASE | re.UNICODE)
            defined_here = {str((pr.get("args") or {}).get("point")) for pr in builder.premises if pr.get("kind") in ("midpoint", "centroid")}
            if m_rel and m_rel.group("pt") not in defined_here and (
                    (m_rel.group("dk").lower().startswith("trung") and m_rel.group("seg"))
                    or (m_rel.group("dk").lower().startswith("trọng") and m_rel.group("tri"))):
                q_rel = _clean_quote(raw, ca + thru_offset, ca + thru_offset + len(thru_str))
                builder.premises.append(
                    {"kind": "midpoint", "args": {"point": m_rel.group("pt"), "segment": _split_pts(m_rel.group("seg"))},
                     "quote": q_rel, "solid_id": builder._primary_solid_id} if m_rel.group("seg") else
                    {"kind": "centroid", "args": {"point": m_rel.group("pt"), "polygon": _split_pts(m_rel.group("tri"))},
                     "quote": q_rel, "solid_id": builder._primary_solid_id})
                thru_ref = m_rel.group("pt")
            else:
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
                    # "song song với (mặt phẳng) đáy" (independent-geometry-plane-constraints): the declared base of the
                    # primary solid, the same plane the Source Gate reads for "đáy" — never a guessed face.
                    pplane_pts = (_split_pts(m_sec_par_or_perp.group("pplane")) if m_sec_par_or_perp.group("pplane")
                                  else list(builder._base_vertices))
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

    # Follow-up cut clause after `;` or in next sentence: e.g. "(α) cắt SA, SB, SC, SD lần lượt tại M, N, P, Q" or "Gọi K là giao điểm của BC với (P)"
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

    # 6c-2. Plane through point parallel to two lines (`plane_kind="through_point_parallel_lines"`):
    # "Mặt phẳng (P) qua I và song song với hai đường thẳng SA, SC"
    m_sec_two_lines = re.search(
        rf"(?:(?:Gọi\s+\((?P<p1>{_PT}|[α-ω]'?)\)\s+là\s+mặt\s+phẳng|Mặt\s+phẳng\s+\((?P<p2>{_PT}|[α-ω]'?)\))\s+(?:đi\s+qua|qua|chứa)\s+(?P<thru>{_PT})|Qua\s+(?P<thru2>{_PT})\s+(?:kẻ|dựng)\s+mặt\s+phẳng\s+\((?P<p3>{_PT}|[α-ω]'?)\))(?:\s*,\s*(?:và\s+)?|\s+và\s+|\s+)song\s+song\s+với\s+(?:hai\s+đường\s+thẳng\s+|hai\s+cạnh\s+|đường\s+thẳng\s+|cạnh\s+)?(?P<l1>{_PTS2})\s*(?:,\s*|\s+và\s+)\s*(?:đường\s+thẳng\s+|cạnh\s+)?(?P<l2>{_PTS2})(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_sec_two_lines:
        pname = m_sec_two_lines.group("p1") or m_sec_two_lines.group("p2") or m_sec_two_lines.group("p3")
        thru_pt = (m_sec_two_lines.group("thru") or m_sec_two_lines.group("thru2")).strip()
        q_stl = _clean_quote(raw, ca + m_sec_two_lines.start(), ca + m_sec_two_lines.end())
        sec_id = "sec"
        builder.derived_sections.append(
            {
                "section_id": sec_id,
                "plane_name": pname,
                "target_solid_id": builder._primary_solid_id,
                "plane_kind": "through_point_parallel_two_lines",
                "through_point": thru_pt,
                "parallel_line_a": _split_pts(m_sec_two_lines.group("l1")),
                "parallel_line_b": _split_pts(m_sec_two_lines.group("l2")),
                "stated_intersections": [],
                "quote": q_stl,
                "_start_offset": ca + m_sec_two_lines.start(),
            }
        )
        builder._section_by_plane_name[pname] = sec_id
        builder._last_section_id = sec_id
        mapped_fact = True

    # Follow-up intersection of an edge with a named derived plane: "Gọi K là giao điểm của BC với (P)" or "... của (P) và BC"
    m_named_plane_cut = re.search(
        rf"(?P<full>(?:(?:Gọi|Cho|Lấy)\s+)?(?<![\w'])(?P<pt>{_PT})\s+là\s+giao\s+điểm(?:\s+của)?\s+(?:(?:(?:đường\s+thẳng|cạnh|đoạn(?:\s+thẳng)?)\s+)?(?P<edge>{_PTS2})\s+(?:và|với)\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<pname>{_PT}|[α-ω]'?)\)|(?:mặt\s+phẳng\s+|mp\s*)?\((?P<pname2>{_PT}|[α-ω]'?)\)\s+(?:và|với)\s+(?:(?:đường\s+thẳng|cạnh|đoạn(?:\s+thẳng)?)\s+)?(?P<edge2>{_PTS2})))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_named_plane_cut and builder.derived_sections:
        pname_c = m_named_plane_cut.group("pname") or m_named_plane_cut.group("pname2")
        edge_c = m_named_plane_cut.group("edge") or m_named_plane_cut.group("edge2")
        sec_match = next((s for s in reversed(builder.derived_sections) if s.get("plane_name") == pname_c), None)
        if sec_match is not None:
            start_off = sec_match.get("_start_offset", ca)
            sec_match["quote"] = _clean_quote(raw, start_off, ca + m_named_plane_cut.end("full"))
            q_npc = _clean_quote(raw, ca + m_named_plane_cut.start("full"), ca + m_named_plane_cut.end("full"))
            sec_match["stated_intersections"].append(
                {
                    "edge": _split_pts(edge_c),
                    "point": m_named_plane_cut.group("pt"),
                    "quote": q_npc,
                }
            )
            mapped_fact = True

    # 6d-0 & 6d (independent-geometry-plane-constraints + A4 `@id` in `contains_points`).
    m_sec_con_hdr = re.search(
        rf"(?:Gọi\s+\((?P<p1>{_PT}|[α-ω]'?)\)\s+là\s+mặt\s+phẳng|Mặt\s+phẳng\s+\((?P<p2>{_PT}|[α-ω]'?)\))\s+(?P<body>(?:đi\s+qua|qua|chứa)\s+.+?)(?:\s*(?:,?\s*(?:(?:và(?:\s+đồng\s+thời)?|đồng\s+thời)\s+)?(?:(?P<perp>vuông\s+góc\s+với\s+(?:mặt\s+phẳng\s+|mp\s*|mặt\s+(?:đáy|bên)\s*)?\((?P<pplane>{_PTS3_6})\))|(?P<par>song\s+song\s+với\s+(?:đường\s+thẳng\s+|cạnh\s+|đoạn(?:\s+thẳng)?\s+)?(?P<pline>{_PTS2})))))?\s*[.;]?\s*$",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_sec_con_hdr and not m_sec_par_or_perp and not m_sec_two_lines:
        pname = m_sec_con_hdr.group("p1") or m_sec_con_hdr.group("p2")
        body_c = m_sec_con_hdr.group("body").strip()
        body_off = ca + m_sec_con_hdr.start("body")
        pts_con: list[str] = []
        valid_con_body = True
        has_dir = bool(m_sec_con_hdr.group("perp") or m_sec_con_hdr.group("par"))

        def _parse_contains_items(txt: str, off: int) -> list[str] | None:
            t = txt.strip()
            t = re.sub(r"^(?:(?:đi\s+)?qua|chứa)\s+(?:(?:hai|ba|các)\s+điểm\s+)?", "", t, flags=re.IGNORECASE)
            off += txt.find(t) if t in txt else 0
            # First check intersecting named lines only when 3 named points result: "hai đường thẳng (cắt nhau) AB và AC"
            m_two_l = re.fullmatch(rf"hai\s+đường\s+thẳng\s+(?:cắt\s+nhau\s+)?(?P<l1>{_PTS2})\s+và\s+(?P<l2>{_PTS2})", t, re.I)
            if m_two_l and not has_dir:
                a_pts, b_pts = _split_pts(m_two_l.group("l1")), _split_pts(m_two_l.group("l2"))
                if len(set(a_pts)) == 2 and len(set(b_pts)) == 2 and len(set(a_pts) & set(b_pts)) == 1:
                    sh = (set(a_pts) & set(b_pts)).pop()
                    return [sh, *(x for x in a_pts if x != sh), *(x for x in b_pts if x != sh)]
                return None
            # Single named line only when followed by another item (contains "và (đi )?qua / chứa") or concatenated edge in `chứa AB và song song ...`
            if re.fullmatch(rf"{_PTS2}", t) and has_dir:
                pts_2 = _split_pts(t)
                return pts_2 if len(pts_2) == 2 and len(set(pts_2)) == 2 else None
            # Split across top-level connectors `, `, ` và `, ` và đi qua `, ` và chứa ` cleanly using snapshot
            parts_raw = [m for m in re.finditer(r"(?:\s*,\s*(?:(?:đi\s+)?qua|chứa)?\s*|\s+và\s+(?:(?:đi\s+)?qua|chứa)?\s*)", t, re.I)]
            spans_idx = [0]
            out_items: list[str] = []
            # Greedy left-to-right only over unambiguous item delimiters (comma or verb-carrying `và đi qua` / `và chứa` or standalone `,`/`và` where each segment resolves)
            chunks: list[tuple[int, int, str]] = []
            prev = 0
            for m_sp in parts_raw:
                seg = t[prev : m_sp.start()].strip()
                # Do not split `và`/`với` inside `trung điểm của đoạn nối X với Y` or `giao điểm của AB và CD`
                if m_sp.group(0).strip().lower() == "và" and re.search(r"(?:giao\s+điểm|nối|cắt\s+nhau)[^,]*$", t[prev : m_sp.start()], re.I):
                    continue
                if seg:
                    l_s = t.find(seg, prev)
                    chunks.append((off + l_s, off + l_s + len(seg), seg))
                prev = m_sp.end()
            last_seg = t[prev:].strip()
            if last_seg:
                l_s = t.find(last_seg, prev)
                chunks.append((off + l_s, off + l_s + len(last_seg), last_seg))
            for ch_s, _ch_e, ch_txt in chunks:
                ch_txt_clean = re.sub(r"^(?:đường\s+thẳng|đoạn(?:\s+thẳng)?|cạnh)\s+", "", ch_txt, flags=re.I)
                if ch_txt_clean != ch_txt or re.fullmatch(rf"{_PTS2}", ch_txt_clean):
                    ln_p = _split_pts(ch_txt_clean)
                    if len(ln_p) != 2 or len(set(ln_p)) != 2:
                        return None
                    for pt_l in ln_p:
                        if pt_l not in out_items:
                            out_items.append(pt_l)
                else:
                    snap_c = builder._snapshot()
                    pt_r = builder.parse_point_or_described(ch_txt, ch_s)
                    if pt_r is None:
                        builder._restore(snap_c)
                        return None
                    if pt_r not in out_items:
                        out_items.append(pt_r)
            return out_items

        parsed_pts = _parse_contains_items(body_c, body_off)
        if parsed_pts and (len(parsed_pts) >= 3 or (len(parsed_pts) >= 1 and has_dir and len(parsed_pts) + 1 >= 3)):
            constraints: list[dict[str, Any]] = [{"kind": "contains_points", "operands": parsed_pts}]
            if m_sec_con_hdr.group("perp"):
                constraints.append({"kind": "perpendicular_to_plane", "operands": _split_pts(m_sec_con_hdr.group("pplane"))})
            elif m_sec_con_hdr.group("par"):
                constraints.append({"kind": "parallel_to_line", "operands": _split_pts(m_sec_con_hdr.group("pline"))})
            q_con = _clean_quote(raw, ca + m_sec_con_hdr.start(), ca + m_sec_con_hdr.end())
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
    # /11: one shared grammar (`_SIM_REQUEST_RE`) for every show verb and declared-solid kind word; the request must name
    # exactly one declared solid (`_sim_request_target`), otherwise it stays unparsed (refused / clarified downstream).
    m_sim_lead = _SIM_REQUEST_RE.match(ctext_norm)
    sim_target = _sim_request_target(m_sim_lead, builder.solids, builder._primary_solid_id) if m_sim_lead else None
    if m_sim_lead and sim_target:
        q_sim = _clean_quote(raw, ca + m_sim_lead.start("sim"), ca + m_sim_lead.end("sim"))
        builder.simulation_goals = [
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": sim_target, "quote": q_sim}
        ]
        mapped_goal = True

    # 7c-0 (verified-section-intersection-dihedral-local). A section by the plane NAMED BY THREE POINTS in the question
    # itself — the existing three-point section of the planner (`constrained` + `contains_points`):
    #   "Xác định / Dựng / Tìm / Vẽ thiết diện (của hình chóp S.ABCD) (cắt|tạo) bởi (mặt phẳng) (MAB)"
    # NOT "Mặt phẳng (MAB) cắt hình chóp theo thiết diện là hình gì?": the plane is stated inside the question itself, and the
    # Source Gate's goal-as-premise guard refuses it (QUESTION_CLAUSE_NOT_PREMISE) — left unparsed, the guard is not loosened.
    #   "Tính diện tích thiết diện (của …) (cắt|tạo) bởi (mặt phẳng) (MAB)" (the area goal itself is rule 7e's)
    # The engine proves the three points distinct and non-collinear and computes the bounded section; a solid named in
    # the clause must be the declared one. Nothing is assumed about the plane beyond the three points the source names.
    _SOLID_WORDS = r"(?:hình|khối)\s+(?:chóp(?:\s+cụt)?|lăng\s+trụ(?:\s+đứng)?|hộp(?:\s+chữ\s+nhật)?|lập\s+phương|tứ\s+diện)"
    m_sec3 = re.search(
        rf"(?P<full>(?:(?P<area>tính\s+diện\s+tích)|(?:Xác\s+định|Dựng|Tìm|Vẽ))\s+thiết\s+diện(?:\s+của\s+{_SOLID_WORDS}"
        rf"(?:\s+(?P<sol>{_PT}\.{_PTS3_6}|{_PTS3_6}\.{_PTS3_6}|{_PTS3_6}))?)?\s+(?:cắt\s+|tạo\s+)?bởi\s+"
        rf"(?:(?:mặt\s+phẳng|mp)\s*(?:\((?P<pl>{_PTS3})\)|(?:đi\s+)?qua\s+(?:(?:ba|3)\s+điểm\s+)?(?P<p1>{_PT})\s*(?:,\s*|\s+và\s+)(?P<p2>{_PT})\s*(?:,\s*|\s+và\s+)(?P<p3>{_PT}))|\((?P<pl_b>{_PTS3})\)))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_sec3 and builder._primary_solid_id and not builder.derived_sections:
        pl_raw3 = m_sec3.group("pl") or m_sec3.group("pl_b")
        pl = _split_pts(pl_raw3) if pl_raw3 else [m_sec3.group("p1"), m_sec3.group("p2"), m_sec3.group("p3")]
        sol = m_sec3.group("sol")
        primary = next((sd for sd in builder.solids if sd.get("solid_id") == builder._primary_solid_id), {})
        if len(set(pl)) == 3 and (sol is None or sol == primary.get("notation")):
            q_s3 = _clean_quote(raw, ca + m_sec3.start("full"), ca + m_sec3.end("full"))
            builder.derived_sections.append({
                "section_id": "sec", "target_solid_id": builder._primary_solid_id, "plane_kind": "constrained",
                "constraints": [{"kind": "contains_points", "operands": pl}], "stated_intersections": [], "quote": q_s3})
            builder._section_by_plane_name["".join(pl)] = "sec"
            builder._last_section_id = "sec"
            builder.simulation_goals.append(
                {"goal_id": "g_sec", "kind": "construct_plane_section", "target_section_id": "sec", "quote": q_s3})
            mapped_goal = True

    # 7c-0b (independent-geometry-plane-constraints). The section by a plane the source DEFINED earlier under a name
    # (rules 6c / 6c-2 / 6d: "(P) qua M và song song với (ABCD)", "(P) chứa AB và đi qua M", …), asked in the question:
    #   "Xác định / Dựng / Tìm / Vẽ thiết diện (của hình chóp …) (cắt|tạo) bởi | với (mặt phẳng) (P)"
    # Only a name already bound to a defined plane is accepted — the plane is never guessed from the question; an
    # undefined name stays unparsed. The area goal of the same sentence remains rule 7e's.
    #   (semantic-failure-safe-image-segmentation) also the question "Thiết diện (của hình chóp …) cắt bởi (P) là hình
    #   gì?" — same request, other word order. "… thiết diện do (P) cắt hình chóp" is NOT read: the Source Gate has no
    #   reading of that order for a derived plane, so the parser leaves it unread rather than produce a fact it refuses.
    _SOL_SYM = rf"{_PT}\.{_PTS3_6}|{_PTS3_6}\.{_PTS3_6}|{_PTS3_6}"
    m_sec_named = re.search(
        rf"(?P<full>(?:Xác\s+định|Dựng|Tìm|Vẽ)\s+thiết\s+diện(?:\s+của\s+{_SOLID_WORDS}"
        rf"(?:\s+(?P<sol>{_SOL_SYM}))?)?\s+(?:(?:cắt\s+|tạo\s+)?bởi|với)\s+(?:mặt\s+phẳng\s+|mp\s*)?"
        rf"\((?P<pl>{_PT}|[α-ω]'?)\)"
        rf"|(?:Xác\s+định|Dựng|Tìm|Vẽ)\s+thiết\s+diện\s+do\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<pl_do>{_PT}|[α-ω]'?)\)\s+cắt(?:\s+{_SOLID_WORDS}(?:\s+(?P<sol_do>{_SOL_SYM}))?)?"
        rf"|Thiết\s+diện(?:\s+của\s+{_SOLID_WORDS}(?:\s+(?P<sol_q>{_SOL_SYM}))?)?\s+(?:(?:cắt\s+|tạo\s+)?bởi|với)\s+"
        rf"(?:mặt\s+phẳng\s+|mp\s*)?\((?P<pl_q>{_PT}|[α-ω]'?)\)\s+là\s+hình\s+gì)(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    named_pl = m_sec_named and (m_sec_named.group("pl") or m_sec_named.group("pl_q") or m_sec_named.group("pl_do"))
    if m_sec_named and named_pl in builder._section_by_plane_name and not any(
            g.get("kind") == "construct_plane_section" for g in builder.simulation_goals):
        sol = m_sec_named.group("sol") or m_sec_named.group("sol_q") or m_sec_named.group("sol_do")
        primary = next((sd for sd in builder.solids if sd.get("solid_id") == builder._primary_solid_id), {})
        if sol is None or sol == primary.get("notation"):
            builder.simulation_goals.append(
                {"goal_id": "g_sec", "kind": "construct_plane_section",
                 "target_section_id": builder._section_by_plane_name[named_pl],
                 "quote": _clean_quote(raw, ca + m_sec_named.start("full"), ca + m_sec_named.end("full"))})
            mapped_goal = True

    # 7c-0c. Unnamed inline derived plane inside a section goal ("Xác định thiết diện của hình chóp cắt bởi mặt phẳng đi qua trung điểm của SA và song song với mặt đáy")
    m_sec_anon = re.search(
        rf"(?P<full>(?:Xác\s+định|Dựng|Tìm|Vẽ)\s+thiết\s+diện(?:\s+của\s+{_SOLID_WORDS}(?:\s+(?P<sol>{_SOL_SYM}))?)?\s+(?:(?:cắt\s+|tạo\s+)?bởi|với)\s+(?:mặt\s+phẳng|mp)\s+(?:đi\s+qua|qua|chứa)\s+(?P<thru>.+?)\s+(?:và\s+)?(?:(?P<par>song\s+song\s+với\s+(?:(?:mặt\s+phẳng|mp\s*|đáy\s*)?\((?P<pplane>{_PTS3_6})\)|(?P<pday>(?:mặt\s+phẳng\s+|mặt\s+)?đáy)(?![\w])))|(?P<perp>vuông\s+góc\s+với\s+(?:đường\s+thẳng\s+|cạnh\s+)?(?P<pline>{_PTS2}))))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_sec_anon and builder._primary_solid_id and not builder.derived_sections and not m_sec_named:
        sol_a = m_sec_anon.group("sol")
        primary_a = next((sd for sd in builder.solids if sd.get("solid_id") == builder._primary_solid_id), {})
        if sol_a is None or sol_a == primary_a.get("notation"):
            thru_str_a = m_sec_anon.group("thru").strip()
            thru_off_a = ca + m_sec_anon.start("thru")
            m_rel_a = re.fullmatch(
                rf"(?:điểm\s+)?(?P<dk>trung\s+điểm|trọng\s+tâm)\s+(?P<pt>{_PT})\s+của\s+(?:(?:(?:cạnh|đoạn(?:\s+thẳng)?)\s+)?(?P<seg>{_PTS2})|tam\s+giác\s+(?P<tri>{_PTS3}))",
                thru_str_a,
                re.IGNORECASE | re.UNICODE,
            )
            thru_ref_a: str | None = None
            if m_rel_a:
                q_rel_a = _clean_quote(raw, thru_off_a, thru_off_a + len(thru_str_a))
                builder.premises.append(
                    {"kind": "midpoint", "args": {"point": m_rel_a.group("pt"), "segment": _split_pts(m_rel_a.group("seg"))},
                     "quote": q_rel_a, "solid_id": builder._primary_solid_id} if m_rel_a.group("seg") else
                    {"kind": "centroid", "args": {"point": m_rel_a.group("pt"), "polygon": _split_pts(m_rel_a.group("tri"))},
                     "quote": q_rel_a, "solid_id": builder._primary_solid_id}
                )
                thru_ref_a = m_rel_a.group("pt")
            else:
                thru_ref_a = builder.parse_point_or_described(thru_str_a, thru_off_a)
            if thru_ref_a:
                q_sa_full = _clean_quote(raw, ca + m_sec_anon.start("full"), ca + m_sec_anon.end("full"))
                sec_entry_a: dict[str, Any] = {
                    "section_id": "sec",
                    "target_solid_id": builder._primary_solid_id,
                    "through_point": thru_ref_a,
                    "stated_intersections": [],
                    "quote": q_sa_full,
                }
                if m_sec_anon.group("par"):
                    pl_ref_a = _split_pts(m_sec_anon.group("pplane")) if m_sec_anon.group("pplane") else list(builder._base_vertices)
                    if len(set(pl_ref_a)) >= 3:
                        sec_entry_a["plane_kind"] = "through_point_parallel_plane"
                        sec_entry_a["parallel_plane"] = list(dict.fromkeys(pl_ref_a))[:3]
                elif m_sec_anon.group("perp"):
                    sec_entry_a["plane_kind"] = "through_point_perpendicular_line"
                    sec_entry_a["perpendicular_line"] = _split_pts(m_sec_anon.group("pline"))
                if "plane_kind" in sec_entry_a:
                    builder.derived_sections.append(sec_entry_a)
                    builder._last_section_id = "sec"
                    builder.simulation_goals.append(
                        {"goal_id": "g_sec", "kind": "construct_plane_section", "target_section_id": "sec", "quote": q_sa_full}
                    )
                    mapped_goal = True

    # 7c-1 (verified-section-intersection-dihedral-local). The intersection line of two planes, each named by three
    # labels: "Tìm / Xác định / Dựng giao tuyến (của) (hai mặt phẳng) (SAB) và (mặt phẳng) (SCD)", "Gọi d là giao tuyến
    # của (SAB) và (SCD)". A construction goal (`/2` construct_intersection_line): the line is never assumed known —
    # the engine decides whether the planes meet in one line, are parallel or coincide.
    for m_il in re.finditer(
        rf"(?P<full>(?:(?:Tìm|Xác\s+định|Dựng|Vẽ)|Gọi\s+(?P<lname>[a-zΔ]|{_PT})\s+là)\s+giao\s+tuyến\s+(?:của\s+)?"
        rf"(?:hai\s+mặt\s+phẳng\s+|mặt\s+phẳng\s+|mp\s*)?\((?P<pa>{_PTS3})\)\s+(?:và|với)\s+(?:mặt\s+phẳng\s+|mp\s*)?"
        rf"\((?P<pb>{_PTS3})\))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        pa, pb = _split_pts(m_il.group("pa")), _split_pts(m_il.group("pb"))
        if len(set(pa)) != 3 or len(set(pb)) != 3 or set(pa) == set(pb) or not builder._primary_solid_id:
            continue
        q_il = _clean_quote(raw, ca + m_il.start("full"), ca + m_il.end("full"))
        builder.simulation_goals.append(
            {"goal_id": f"g_il{len(builder.simulation_goals) + 1}", "kind": "construct_intersection_line",
             "target_planes": [pa, pb], "target_solid_id": builder._primary_solid_id, "quote": q_il})
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
    # "(Xác định thiết diện của ... cắt bởi (P) và )?tính diện tích thiết diện( của ... cắt bởi (mặt phẳng )?(P)| do (P) cắt ...| đó)?"
    m_sec_area = re.search(
        rf"(?P<full>(?:Xác\s+định\s+thiết\s+diện.*?và\s+)?(?P<tinh>tính\s+)?diện\s+tích\s+thiết\s+diện(?:\s+(?:(?:của\s+.*?cắt\s+bởi|tạo\s+bởi)\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<pname>{_PT}|[α-ω]'?)\)|do\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<pname2>{_PT}|[α-ω]'?)\)\s+cắt(?:\s+[^.;?!]*)?)|\s+(?:đó|này|trên))?"
        rf"|(?P<tinh_do>tính\s+|xác\s+định\s+)?thiết\s+diện\s+do\s+(?:mặt\s+phẳng\s+|mp\s*)?\((?P<pname_do>{_PT}|[α-ω]'?)\)\s+cắt\s+[^.;?!]*?\s+có\s+diện\s+tích(?:\s+bằng\s+bao\s+nhiêu)?)",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_sec_area and not (m_sec_area.group("tinh") or m_sec_area.group("pname_do")) and not re.fullmatch(
            r"\s*(?:có\s+)?(?:diện\s+tích\s+)?(?:bằng|là)(?:\s+bao\s+nhiêu)?\s*:?\s*[.?]?\s*", ctext_norm[m_sec_area.end("full"):], re.IGNORECASE):
        m_sec_area = None              # without "tính", only the exam stem "Diện tích thiết diện … bằng" asks — never a given
    if m_sec_area:
        pname = m_sec_area.group("pname") or m_sec_area.group("pname2") or m_sec_area.group("pname_do")
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
            rf"(?P<full>(?:tính\s+)?thể\s+tích(?:\s+V)?(?:\s+của)?\s+(?P<kind>(?:khối\s+chóp|hình\s+chóp)(?!\s+cụt)|khối\s+tứ\s+diện|tứ\s+diện|khối\s+lăng\s+trụ|hình\s+lăng\s+trụ|lăng\s+trụ|khối\s+lập\s+phương|hình\s+lập\s+phương|(?:khối|hình)\s+hộp(?:\s+chữ\s+nhật)?|khối\s+cầu|mặt\s+cầu|khối\s+trụ|hình\s+trụ|khối\s+nón|hình\s+nón)(?:\s+(?P<not>\({_PT}\)|{_PT}\.{_PTS3_6}|{_PTS3_6}\.{_PTS3_6}|{_PTS4})|\s+(?:đã\s+cho|đó|này))?)",
            ctext_norm,
            re.IGNORECASE | re.UNICODE,
        )
        if not (m_vol_ratio or m_res_pyr)
        else ()
    ):
        if not builder.solids and not builder._sphere_by_notation:
            continue
        if not re.search(r"\b(?:tính|tìm|xác\s+định|hỏi|hãy\s+cho\s+biết|cho\s+(?:em|mình|tôi|tớ|bạn)\s+biết)\b", ctext_norm[: m_vol.end("full")], re.IGNORECASE):
            if re.match(rf"^\s*(?:=|bằng|là)\s*{_VAL}", ctext_norm[m_vol.end("full") :], re.IGNORECASE | re.UNICODE):
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
            if sid_v is None and ("chóp" in k_v or "tứ diện" in k_v) and builder.solids:
                known_verts = {
                    v for sd in builder.solids for v in _split_pts(str(sd.get("notation") or "").replace(".", ""))
                }
                for pr in builder.premises:
                    pk_pr = pr.get("kind")
                    pa_pr = pr.get("args") or {}
                    out_k = {"midpoint": "point", "centroid": "point", "divide_segment": "point",
                             "intersect_line_line": "point", "intersect_line_plane": "point",
                             "orthogonal_projection": "image", "orthogonal_projection_line": "image",
                             "point_reflection": "image"}.get(pk_pr)
                    if out_k and isinstance(pa_pr.get(out_k), str) and not str(pa_pr[out_k]).startswith("@"):
                        known_verts.add(pa_pr[out_k])
                apex_s: str | None = None
                base_pts: list[str] = []
                if "." in not_v:
                    l_part, r_part = not_v.split(".", 1)
                    l_ps, r_ps = _split_pts(l_part), _split_pts(r_part)
                    if len(l_ps) == 1 and 3 <= len(r_ps) <= 6:
                        apex_s, base_pts = l_ps[0], r_ps
                elif "tứ diện" in k_v:
                    all_ps = _split_pts(not_v)
                    if len(all_ps) == 4:
                        apex_s, base_pts = all_ps[0], all_ps[1:]
                if apex_s is not None and len({apex_s, *base_pts}) == 1 + len(base_pts) and {apex_s, *base_pts} <= known_verts:
                    sub_not = f"{apex_s}.{''.join(base_pts)}"
                    sid_v = f"s{len(builder.solids) + 1}"
                    builder.solids.append({
                        "solid_id": sid_v,
                        "solid_type": "pyramid",
                        "notation": sub_not,
                        "quote": _clean_quote(raw, ca, cb),
                    })
            if sid_v is None:
                continue
        else:
            sid_v = builder._primary_solid_id
        # Use full clause quote if multiple goals share the sentence or if noun-phrase question (no leading 'tính'), else exact match quote
        is_multi_in_clause = bool(re.search(r"\b(?:và|cùng)\b|,.*tính", ctext_norm, re.IGNORECASE)) and not bool(m_sim_lead)
        is_noun_phrase = not m_vol.group("full").lower().startswith("tính")
        q_v = (
            _clean_quote(raw, ca, cb)
            if (is_multi_in_clause or is_noun_phrase)
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
        rf"(?P<full>(?:tính\s+)?diện\s+tích(?:\s+của)?\s+(?:tam\s+giác|tứ\s+giác|hình\s+vuông|hình\s+chữ\s+nhật|hình\s+thoi|hình\s+bình\s+hành|hình\s+thang|đa\s+giác)\s+(?P<poly>{_PTS3_6}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        if re.search(r"(?:tỉ\s+số|tỷ\s+số|thương(?:\s+số)?)\s*(?:của\s+|giữa\s+)?$", ctext_norm[: m_poly_area.start("full")], re.IGNORECASE):
            continue
        has_ask_verb_pa = m_poly_area.group("full").lower().startswith("tính") or bool(
            re.search(r"\b(?:tính|tìm|xác\s+định|hỏi|hãy\s+cho\s+biết|cho\s+(?:em|mình|tôi|tớ|bạn)\s+biết)\b", ctext_norm[: m_poly_area.start("full")], re.IGNORECASE)
        )
        if not has_ask_verb_pa or re.match(rf"^\s*(?:=|bằng|là)\s*{_VAL}", ctext_norm[m_poly_area.end("full") :], re.IGNORECASE | re.UNICODE):
            continue
        is_multi_pa = bool(re.search(r"\b(?:và|cùng)\b|,.*tính", ctext_norm, re.IGNORECASE)) and not bool(m_sim_lead)
        q_pa = (
            _clean_quote(raw, ca, cb)
            if (not m_poly_area.group("full").lower().startswith("tính") or is_multi_pa)
            else _clean_quote(raw, ca + m_poly_area.start("full"), ca + m_poly_area.end("full"))
        )
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
        rf"(?P<full>Tính\s+độ\s+dài\s+đoạn\s+thẳng\s+nối\s+(?P<a>.+?)\s+với\s+(?P<b>.+?)){_NEXT_GOAL_LOOKAHEAD}",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_len_join:
        b_clean = _strip_trailing_goal_meta(m_len_join.group("b"))
        ref_a = builder.parse_point_or_described(m_len_join.group("a"), ca + m_len_join.start("a"))
        ref_b = builder.parse_point_or_described(b_clean, ca + m_len_join.start("b"))
        if ref_a and ref_b:
            q_lj = _clean_quote(raw, ca + m_len_join.start("full"), ca + m_len_join.start("b") + len(b_clean))
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

    # A length goal is a question, never an assignment: "Độ dài KL = 7." states a premise (run
    # `model1-integration-readiness` — read as a goal it made the Source Gate refuse NOT_ASKED_IN_SOURCE).
    for m_len_seg in re.finditer(
        rf"(?P<full>(?:tính\s+)?độ\s+dài(?:\s+(?:đoạn(?:\s+thẳng)?|đường\s+chéo|cạnh(?:\s+(?:bên|đáy))?))?\s+(?P<seg>{_PTS2}))(?![\w'])"
        rf"(?!\s*(?:=|bằng|là)\s*{_VAL})",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        seg_pts = _split_pts(m_len_seg.group("seg"))
        has_other_goal_in_clause = bool(
            re.search(r"khoảng\s+cách|bán\s+kính|thể\s+tích|diện\s+tích|góc|tỉ\s+số", ctext_norm, re.IGNORECASE)
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

    # 7i. Distance goals (fully composable over recursive point & line descriptors):
    df_spans: list[tuple[int, int]] = []
    for m_dist_from in re.finditer(
        rf"(?P<full>(?:(?:tính|tìm|xác\s+định)\s+)?(?:khoảng\s+cách|k/c)\s+từ\s+(?P<body>.+?)){_NEXT_GOAL_LOOKAHEAD}",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        matched_df: tuple[str, dict[str, Any]] | None = None
        body_df = _strip_trailing_goal_meta(m_dist_from.group("body"))
        body_df_off = ca + m_dist_from.start("body")
        for sp in reversed(list(re.finditer(r"\s+(?:đến|tới)\s+", body_df, re.IGNORECASE | re.UNICODE))):
            src_str = body_df[: sp.start()].strip()
            dst_str = body_df[sp.end() :].strip()
            src_off = body_df_off + (len(body_df[: sp.start()]) - len(body_df[: sp.start()].lstrip()))
            dst_off = body_df_off + sp.end() + (len(body_df[sp.end() :]) - len(body_df[sp.end() :].lstrip()))
            snap_df = builder._snapshot()
            pl_dst = builder.parse_plane_or_base(dst_str)
            if pl_dst:
                src_ref = builder.parse_point_or_described(src_str, src_off)
                if src_ref:
                    matched_df = ("plane", {"point": src_ref, "plane": pl_dst})
                    break
                builder._restore(snap_df)
                ln_src = builder.parse_line_or_described(src_str, src_off)
                if ln_src:
                    matched_df = ("line_plane", {"line": ln_src, "plane": pl_dst})
                    break
                builder._restore(snap_df)
                continue
            ln_dst = builder.parse_line_or_described(dst_str, dst_off)
            src_ref = builder.parse_point_or_described(src_str, src_off) if ln_dst else None
            if src_ref and ln_dst:
                matched_df = ("line", {"point": src_ref, "line": ln_dst})
                break
            builder._restore(snap_df)
        if matched_df is not None:
            df_spans.append((m_dist_from.start("full"), m_dist_from.end("full")))
            q_df = _clean_quote(raw, ca + m_dist_from.start("full"), ca + m_dist_from.start("body") + len(body_df))
            if not re.match(r"(?:tính|tìm|xác\s+định)\b", q_df, re.IGNORECASE):
                q_df = _clean_quote(raw, ca, cb)
            builder.math_goals.append(
                {
                    "goal_id": f"q{len(builder.math_goals) + 1}",
                    "kind": "measurement",
                    "goal_type": "distance",
                    "target": matched_df[1],
                    "solid_id": builder._primary_solid_id,
                    "quote": q_df,
                }
            )
            mapped_goal = True

    for m_dist_between in re.finditer(
        rf"(?P<full>(?:(?:tính|tìm|xác\s+định)\s+)?(?:khoảng\s+cách|k/c)\s+giữa\s+(?:hai\s+đường\s+thẳng(?:\s+chéo\s+nhau)?\s+|hai\s+mặt\s+phẳng\s+)?(?P<body>.+?)){_NEXT_GOAL_LOOKAHEAD}",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        if any(a <= m_dist_between.start("full") < b for a, b in df_spans):
            continue
        body_db = _strip_trailing_goal_meta(m_dist_between.group("body"))
        body_db_off = ca + m_dist_between.start("body")
        q_db = _clean_quote(raw, ca + m_dist_between.start("full"), ca + m_dist_between.start("body") + len(body_db))
        if not re.match(r"(?:tính|tìm|xác\s+định)\b", q_db, re.IGNORECASE):
            q_db = _clean_quote(raw, ca, cb)
        for op1_s, o1, op2_s, o2 in _iter_top_splits(body_db):
            snap_db = builder._snapshot()
            pl1_d = builder.parse_plane_or_base(op1_s)
            pl2_d = builder.parse_plane_or_base(op2_s)
            if pl1_d and pl2_d:
                builder.math_goals.append(
                    {"goal_id": f"q{len(builder.math_goals) + 1}", "kind": "measurement", "goal_type": "distance",
                     "target": {"plane1": pl1_d, "plane2": pl2_d}, "solid_id": builder._primary_solid_id, "quote": q_db}
                )
                mapped_goal = True
                break
            if pl2_d:
                ln1_d = builder.parse_line_or_described(op1_s, body_db_off + o1)
                if ln1_d:
                    builder.math_goals.append(
                        {"goal_id": f"q{len(builder.math_goals) + 1}", "kind": "measurement", "goal_type": "distance",
                         "target": {"line": ln1_d, "plane": pl2_d}, "solid_id": builder._primary_solid_id, "quote": q_db}
                    )
                    mapped_goal = True
                    break
                builder._restore(snap_db)
            if pl1_d:
                ln2_d = builder.parse_line_or_described(op2_s, body_db_off + o2)
                if ln2_d:
                    builder.math_goals.append(
                        {"goal_id": f"q{len(builder.math_goals) + 1}", "kind": "measurement", "goal_type": "distance",
                         "target": {"line": ln2_d, "plane": pl1_d}, "solid_id": builder._primary_solid_id, "quote": q_db}
                    )
                    mapped_goal = True
                    break
                builder._restore(snap_db)
            ln1_d = builder.parse_line_or_described(op1_s, body_db_off + o1)
            ln2_d = builder.parse_line_or_described(op2_s, body_db_off + o2) if ln1_d else None
            if ln1_d and ln2_d:
                builder.math_goals.append(
                    {"goal_id": f"q{len(builder.math_goals) + 1}", "kind": "measurement", "goal_type": "distance",
                     "target": {"line1": ln1_d, "line2": ln2_d}, "solid_id": builder._primary_solid_id, "quote": q_db}
                )
                mapped_goal = True
                break
            builder._restore(snap_db)

    # 7i-1b. Solid height goal: "tính chiều cao của hình chóp / khối chóp / tứ diện / lăng trụ"
    for m_hgoal in re.finditer(
        rf"(?:hãy\s+)?(?P<full>(?:tính|tìm|xác\s+định)\s+(?:độ\s+dài\s+)?(?:chiều|đường)\s+cao(?:\s+của\s+(?:(?:hình|khối)\s+)?(?:chóp|tứ\s+diện|lăng\s+trụ)(?:\s+[A-Z0-9'.]+)?)?)(?![\w']){_NEXT_GOAL_LOOKAHEAD}",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        if builder._primary_solid_type == "pyramid" and "." in builder._primary_notation and len(builder._base_vertices) >= 3:
            apex_h = builder._primary_notation.split(".", 1)[0]
            q_hg = _clean_quote(raw, ca + m_hgoal.start("full"), ca + m_hgoal.end("full"))
            builder.math_goals.append(
                {
                    "goal_id": f"q{len(builder.math_goals) + 1}",
                    "kind": "measurement",
                    "goal_type": "distance",
                    "target": {"point": apex_h, "plane": builder._base_vertices[:3]},
                    "solid_id": builder._primary_solid_id,
                    "quote": q_hg,
                }
            )
            mapped_goal = True

    # 7i-2. Affine Length Ratio & Polygon Area Ratio goals (`ext04`, `ext05`):
    # - "(Khi đó )?(tính|tìm) tỉ số KC/KB"
    m_len_ratio = re.search(
        rf"(?P<full>(?:Khi\s+đó\s+|Từ\s+đó\s+)?(?:(?:tính|tìm|xác\s+định)\s+)?(?:tỉ|tỷ)\s+số(?:\s+độ\s+dài)?\s+(?P<n>{_PTS2})\s*/\s*(?P<d>{_PTS2}))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_len_ratio:
        q_lr = _clean_quote(raw, ca + m_len_ratio.start("full"), ca + m_len_ratio.end("full"))
        builder.math_goals.append(
            {
                "goal_id": f"q{len(builder.math_goals) + 1}",
                "kind": "length_ratio",
                "numerator_segment": _split_pts(m_len_ratio.group("n")),
                "denominator_segment": _split_pts(m_len_ratio.group("d")),
                "solid_id": builder._primary_solid_id,
                "quote": q_lr,
            }
        )
        mapped_goal = True

    # - "(Tính )?S1/S2" or "Tính tỉ số diện tích tam giác SMI và tứ giác BCEM"
    m_area_ratio = re.search(
        rf"(?P<full>(?:Khi\s+đó\s+|Từ\s+đó\s+)?(?:(?:tính|tìm|xác\s+định)\s+)(?:(?:(?P<tiso>(?:tỉ|tỷ)\s+số(?:\s+diện\s+tích)?)\s+)?(?P<sn>S\d+)\s*/\s*(?P<sd>S\d+)|(?:(?:tỉ|tỷ)\s+số(?:\s+diện\s+tích)?(?:\s+(?:của|giữa))?\s+)?S\s*(?:_|\()?\s*(?P<n1>{_PTS3_6})\s*\)?\s*/\s*S\s*(?:_|\()?\s*(?P<d1>{_PTS3_6})\s*\)?|(?:tỉ|tỷ)\s+số\s+diện\s+tích(?:\s+(?:của|giữa))?\s+(?:(?:tam\s+giác|tứ\s+giác|đa\s+giác|hình\s+\w+)\s+)?(?P<n2>{_PTS3_6})\s+(?:và|với|trên|so\s+với)\s+(?:diện\s+tích(?:\s+của)?\s+)?(?:(?:tam\s+giác|tứ\s+giác|đa\s+giác|hình\s+\w+)\s+)?(?P<d2>{_PTS3_6})))(?![\w'])",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    )
    if m_area_ratio:
        poly_n: list[str] | None = None
        poly_d: list[str] | None = None
        if m_area_ratio.group("sn") and m_area_ratio.group("sd"):
            poly_n = builder._area_symbol_map.get(m_area_ratio.group("sn").upper())
            poly_d = builder._area_symbol_map.get(m_area_ratio.group("sd").upper())
        elif m_area_ratio.group("n1") and m_area_ratio.group("d1"):
            poly_n = _split_pts(m_area_ratio.group("n1"))
            poly_d = _split_pts(m_area_ratio.group("d1"))
        elif m_area_ratio.group("n2") and m_area_ratio.group("d2"):
            poly_n = _split_pts(m_area_ratio.group("n2"))
            poly_d = _split_pts(m_area_ratio.group("d2"))
        if poly_n and poly_d:
            q_ar = _clean_quote(raw, ca + m_area_ratio.start("full"), ca + m_area_ratio.end("full"))
            builder.math_goals.append(
                {
                    "goal_id": f"q{len(builder.math_goals) + 1}",
                    "kind": "area_ratio",
                    "numerator_polygon": poly_n,
                    "denominator_polygon": poly_d,
                    "solid_id": builder._primary_solid_id,
                    "quote": q_ar,
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

    # - Angle between line(s) (named or with described endpoints via A3/NC-D2_E1) and plane(s):
    for m_ang in re.finditer(
        rf"(?P<full>(?:(?:Tính|Tìm|Xác\s+định)\s+)?(?:số\s+đo\s+(?:của\s+)?)?góc\s+(?:giữa|tạo\s+bởi|hợp\s+bởi)\s+(?:hai\s+(?:đường\s+thẳng|mặt\s+phẳng)\s+)?(?P<body>.+?)){_NEXT_GOAL_LOOKAHEAD}",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        if any(a <= m_ang.start("full") < b for a, b in angle_spans):
            continue
        if re.search(rf"\b(?:bằng|là)\s*{_VAL}\s*(?:°|độ\b)|\s=\s*{_VAL}", m_ang.group("body"), re.IGNORECASE):
            continue
        body_ang = _strip_trailing_goal_meta(m_ang.group("body"))
        body_ang_off = ca + m_ang.start("body")
        ang_end_abs = ca + m_ang.start("body") + len(body_ang)
        req_deg = bool(
            re.search(r"\bsố\s+đo\b", m_ang.group("full"), re.IGNORECASE)
            or re.search(r"\b(?:theo|bằng|tính\s+bằng)\s+(?:đơn\s+vị(?:\s+góc)?\s+)?độ\b|\(\s*(?:đơn\s+vị(?:\s+góc)?\s*:?\s*)?độ\s*\)", m_ang.group("body")[len(body_ang):], re.IGNORECASE)
        )
        ang_extra: dict[str, Any] = {"requested_unit": "deg"} if req_deg else {}
        day_pts = list(builder._base_vertices) if len(builder._base_vertices) >= 3 else None

        if re.fullmatch(r"(?:một\s+)?cạnh\s+bên\s+(?:và|với)\s+(?:mặt\s+phẳng\s+|mặt\s+)?đáy", body_ang, re.IGNORECASE):
            q_ang = _clean_quote(raw, ca + m_ang.start("full"), ang_end_abs)
            if not re.match(r"(?:tính|tìm|xác\s+định|số\s+đo|góc)\b", q_ang, re.IGNORECASE):
                q_ang = _clean_quote(raw, ca, cb)
            angle_spans.append((m_ang.start("full"), m_ang.end("full")))
            notation = str(builder._primary_notation or "")
            regular = any(p.get("kind") == "regular_pyramid" for p in builder.premises)
            if builder._primary_solid_type == "pyramid" and "." in notation and regular and day_pts:
                apex = _split_pts(notation.split(".", 1)[0])
                if len(apex) == 1:
                    builder.math_goals.append({"goal_id": f"q{len(builder.math_goals) + 1}", "kind": "measurement",
                                               "goal_type": "angle", "target": {"line": [apex[0], day_pts[0]], "plane": day_pts},
                                               "solid_id": builder._primary_solid_id, "quote": q_ang, **ang_extra})
                    mapped_goal = True
            else:
                builder.unresolved.append({"unresolved_id": f"u{len(builder.unresolved) + 1}", "kind": "ambiguous",
                                           "quote": q_ang, "missing_roles": ["goal_object"], "candidate_relations": ["angle"]})
                mapped_goal = True
        else:
            ang_target: dict[str, Any] | None = None
            for op1_s, o1, op2_s, o2 in _iter_top_splits(body_ang):
                snap_a = builder._snapshot()
                pl1_a = builder.parse_plane_or_base(op1_s)
                pl2_a = builder.parse_plane_or_base(op2_s)
                if pl1_a and pl2_a:
                    ang_target = {"plane1": pl1_a, "plane2": pl2_a}
                    break
                if pl2_a:
                    ln1_a = builder.parse_line_or_described(op1_s, body_ang_off + o1)
                    if ln1_a:
                        ang_target = {"line": ln1_a, "plane": pl2_a}
                        break
                    builder._restore(snap_a)
                if pl1_a:
                    ln2_a = builder.parse_line_or_described(op2_s, body_ang_off + o2)
                    if ln2_a:
                        ang_target = {"line": ln2_a, "plane": pl1_a}
                        break
                    builder._restore(snap_a)
                ln1_a = builder.parse_line_or_described(op1_s, body_ang_off + o1)
                ln2_a = builder.parse_line_or_described(op2_s, body_ang_off + o2) if ln1_a else None
                if ln1_a and ln2_a:
                    ang_target = {"line1": ln1_a, "line2": ln2_a}
                    break
                builder._restore(snap_a)
            if ang_target is not None:
                q_ang = _clean_quote(raw, ca + m_ang.start("full"), ang_end_abs)
                if not re.match(r"(?:tính|tìm|xác\s+định|số\s+đo|góc)\b", q_ang, re.IGNORECASE):
                    q_ang = _clean_quote(raw, ca, cb)
                angle_spans.append((m_ang.start("full"), m_ang.end("full")))
                builder.math_goals.append(
                    {
                        "goal_id": f"q{len(builder.math_goals) + 1}",
                        "kind": "measurement",
                        "goal_type": "angle",
                        "target": ang_target,
                        "solid_id": builder._primary_solid_id,
                        "quote": q_ang,
                        **ang_extra,
                    }
                )
                mapped_goal = True

    # Attach rounding policy to goals emitted in this clause when the clause states a closed rounding directive
    if mapped_goal and len(builder.math_goals) > pre_goals_len:
        from ..simulation.geometry_functions.output_policy import parse_rounding_spec_from_text

        rd_spec = parse_rounding_spec_from_text(ctext_norm)
        if rd_spec is not None:
            q_full_cl = _clean_quote(raw, ca, cb)
            for g_item in builder.math_goals[pre_goals_len:]:
                g_item["rounding"] = rd_spec
                g_item["quote"] = q_full_cl

    # Run `grounded-vietnamese-geometry-understanding`: "tam giác XYZ cân" WITHOUT its apex. When a premise read so far
    # makes the triangle right-angled at one vertex V (a line ⊥ plane through V, or a stated right angle at V), the two
    # equal sides can only be the legs at V (the hypotenuse is strictly longest): the definition reads as one equality,
    # quoted by the phrase itself. Without such a right angle the apex is unknown and the phrase stays unread.
    for m_can in re.finditer(rf"(?P<full>tam\s+giác\s+(?P<v>{_PTS3})\s+cân)(?![\w'])(?!\s+(?:tại|ở))", ctext_norm,
                             re.IGNORECASE | re.UNICODE):
        tri = _split_pts(m_can.group("v"))
        dinh_vuong = _right_angle_vertex(builder.premises, tri)
        if len(set(tri)) != 3 or dinh_vuong is None:
            continue
        legs = [x for x in tri if x != dinh_vuong]
        if any(p.get("kind") == "equal_length" and {frozenset(p["args"]["segment_a"]), frozenset(p["args"]["segment_b"])}
               == {frozenset((dinh_vuong, legs[0])), frozenset((dinh_vuong, legs[1]))} for p in builder.premises):
            continue
        builder.premises.append({"kind": "equal_length",
                                 "args": {"segment_a": [dinh_vuong, legs[0]], "segment_b": [dinh_vuong, legs[1]]},
                                 "quote": _clean_quote(raw, ca + m_can.start("full"), ca + m_can.end("full")),
                                 "solid_id": builder._primary_solid_id})
        mapped_fact = True

    # Equal-leg bare right triangle ("đáy ABC là tam giác vuông, AB = BC = a" or "tam giác ABC vuông, AB = AC = a")
    for m_bare_rt in re.finditer(
        rf"(?P<full>(?:đáy(?:\s+(?P<verts>{_PTS3}))?\s+(?:là\s+tam\s+giác\s+(?:(?P<verts2>{_PTS3})\s+)?)?|tam\s+giác\s+(?P<verts3>{_PTS3})\s+)vuông)(?![\w'])(?!\s*(?:tại|ở|cân|cạnh)\b)",
        ctext_norm,
        re.IGNORECASE | re.UNICODE,
    ):
        exp_v = m_bare_rt.group("verts") or m_bare_rt.group("verts2") or m_bare_rt.group("verts3")
        tri = _split_pts(exp_v) if exp_v else list(builder._base_vertices)
        if len(tri) != 3 or len(set(tri)) != 3 or _right_angle_vertex(builder.premises, tri) is not None:
            continue
        tri_edges = [frozenset((tri[0], tri[1])), frozenset((tri[0], tri[2])), frozenset((tri[1], tri[2]))]
        eq_pairs: list[tuple[frozenset[str], frozenset[str]]] = []
        len_by_edge: dict[frozenset[str], set[str]] = {}
        for pr in builder.premises:
            pk_p, pa_p = pr.get("kind"), pr.get("args") or {}
            if pk_p == "equal_length":
                ea = frozenset(pa_p.get("segment_a") or ())
                eb = frozenset(pa_p.get("segment_b") or ())
                if ea in tri_edges and eb in tri_edges and ea != eb:
                    eq_pairs.append((ea, eb))
            elif pk_p == "segment_length":
                es = frozenset(pa_p.get("segment") or ())
                if es in tri_edges and pa_p.get("value") is not None:
                    len_by_edge.setdefault(es, set()).add(re.sub(r"\s+", "", str(pa_p["value"])))
        for idx_i, e1 in enumerate(tri_edges):
            for e2 in tri_edges[idx_i + 1 :]:
                if len_by_edge.get(e1) and len_by_edge.get(e2) and (len_by_edge[e1] & len_by_edge[e2]):
                    eq_pairs.append((e1, e2))
        cand_vs = {v for ea, eb in eq_pairs for v in (ea & eb) if v in tri}
        if len(cand_vs) == 1:
            v_rt = next(iter(cand_vs))
            rays_rt = [x for x in tri if x != v_rt]
            s_off = m_bare_rt.start("full")
            if m_bare_rt.group("verts2"):
                m_sub_rt = re.search(rf"tam\s+giác\s+{re.escape(m_bare_rt.group('verts2'))}\b", m_bare_rt.group("full"), re.IGNORECASE)
                if m_sub_rt:
                    s_off += m_sub_rt.start()
            builder.premises.append({
                "kind": "right_angle",
                "args": {"vertex": v_rt, "rays": rays_rt},
                "quote": _clean_quote(raw, ca + s_off, ca + m_bare_rt.end("full")),
                "solid_id": builder._primary_solid_id,
            })
            mapped_fact = True

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
                rf"(?:có\s+)?(?:tất\s+cả\s+(?:các\s+)?|mọi\s+)cạnh(?:\s+đều)?\s*=\s*{_VAL}{_OPT_ANY_UNIT_TAIL}",
                rf"(?:độ\s+dài\s+(?:của\s+)?)?(?:chiều|đường)\s+cao(?:\s+của\s+(?:(?:hình|khối)\s+)?(?:chóp|lăng\s+trụ|hộp(?:\s+chữ\s+nhật)?|lập\s+phương|tứ\s+diện)(?:\s+(?:đứng|đều|xiên|tam\s+giác|tứ\s+giác|lục\s+giác|chữ\s+nhật))*(?:\s+[A-Z0-9'.]+)?)?\s*=\s*{_VAL}",
                rf"(?:độ\s+dài\s+(?:của\s+)?)?(?:cạnh\s+đáy|cạnh\s+bên)(?:\s+của\s+(?:hình|khối)\s+(?:chóp|lăng\s+trụ|hộp|lập\s+phương|tứ\s+diện)(?:\s+[A-Z0-9'.]+)?)?\s*=\s*{_VAL}",
                rf"(?:đường|chiều)\s+cao\s+{_PTS2}\s+của\s+(?:tam\s+giác|[Δ∆△])\s*{_PTS3}\s*=\s*{_VAL}",
                rf"đường\s+cao\s+{_PTS2}\s*=\s*{_VAL}{_OPT_ANY_UNIT_TAIL}",
                rf"(?<![\w'./]){_PTS2}\s*=\s*{_PTS2}(?:\s*=\s*{_PTS2})?\s*=\s*{_VAL}{_OPT_ANY_UNIT_TAIL}(?![\w'])",
                rf"(?:Đường\s+sinh\s+)?(?<![\w'./]){_PTS2}\s*=\s*{_VAL}{_OPT_ANY_UNIT_TAIL}(?![\s]*=)(?![\w'])",
                rf"(?:(?:độ\s+dài|cạnh|đoạn(?:\s+thẳng)?)\s+)?(?<![\w'./]){_PTS2}\s*=\s*(?:{_SCALAR_COEFF}\s*(?:lần\s+|\.\s*|\*\s*)?{_PTS2}|{_PTS2}\s*/\s*\d+)(?![\w'])",
                rf"(?<![\w'./]){_PTS2}\s*/\s*{_PTS2}\s*=\s*{_VAL}{_OPT_ANY_UNIT_TAIL}(?![\w'])",
                rf"(?:tỉ|tỷ)\s+số(?:\s+độ\s+dài)?(?:\s+(?:giữa|của))?(?:\s+hai)?(?:\s+(?:cạnh|đoạn(?:\s+thẳng)?))?\s+(?:{_PTS2}\s+(?:và|với)\s+{_PTS2}|(?:cạnh\s+bên|cạnh\s+đáy)\s+(?:và|với)\s+(?:cạnh\s+đáy|cạnh\s+bên))\s*=\s*{_VAL}{_OPT_ANY_UNIT_TAIL}",
                rf"diện\s+tích(?:\s+của)?\s+(?:(?:hình\s+vuông|hình\s+chữ\s+nhật|tam\s+giác\s+đều|tam\s+giác|tứ\s+giác|mặt\s+bên|mặt\s+đáy|đáy)\s+)?\(?{_PTS3_6}\)?\s*=\s*{_VAL}{_OPT_ANY_UNIT_TAIL}",
                rf"(?:hình\s+vuông|hình\s+chữ\s+nhật|tam\s+giác\s+đều|tam\s+giác|tứ\s+giác|mặt\s+bên|mặt\s+đáy)\s+\(?{_PTS3_6}\)?\s+có\s+diện\s+tích\s*=\s*{_VAL}{_OPT_ANY_UNIT_TAIL}",
                rf"diện\s+tích(?:\s+của)?\s+(?:mặt\s+)?đáy\s*=\s*{_VAL}{_OPT_ANY_UNIT_TAIL}",
                rf"(?<![\w'.])(?-i:S)\s*(?:_|\()\s*\{{?\s*{_PTS3_6}\s*\}}?\s*\)?\s*=\s*{_VAL}{_OPT_ANY_UNIT_TAIL}",
                rf"thể\s+tích(?:\s+của)?(?:\s+(?:(?:hình|khối)\s+)?(?:chóp|lăng\s+trụ|hộp(?:\s+chữ\s+nhật)?|lập\s+phương|tứ\s+diện)(?:\s+(?:đứng|đều|xiên|tam\s+giác|tứ\s+giác|lục\s+giác|chữ\s+nhật))*(?:\s+[A-Z0-9'.]+)?|\s+[A-Z0-9'.]+)?\s*=\s*{_VAL}{_OPT_ANY_UNIT_TAIL}",
                rf"(?:(?:hình|khối)\s+)?(?:chóp|lăng\s+trụ|hộp(?:\s+chữ\s+nhật)?|lập\s+phương|tứ\s+diện)(?:\s+(?:đứng|đều|xiên|tam\s+giác|tứ\s+giác|lục\s+giác|chữ\s+nhật))*\s+[A-Z0-9'.]+\s+có\s+thể\s+tích\s*=\s*{_VAL}{_OPT_ANY_UNIT_TAIL}",
                rf"(?<![\w'.])(?-i:V)\s*(?:_|\()\s*\{{?\s*[A-Z0-9'.]+\s*\}}?\s*\)?\s*=\s*{_VAL}{_OPT_ANY_UNIT_TAIL}",
                rf",?\s*(?:sao\s+cho|thỏa\s+mãn|với|biết(?:\s+rằng)?|mà)\s+{_PTS2}\s*=\s*\d+\s*/\s*\d+\s*{_PTS2}(?![\w'])",
            ):
                for m_eq in re.finditer(eq_pat, ctext_norm, re.IGNORECASE | re.UNICODE):
                    eq_spans.append((m_eq.start(), m_eq.end()))
            # Bare segment equalities count only when the rule above actually built their `equal_length` premises.
            if any(p["kind"] == "equal_length" for p in clause_premises):
                for m_eq in _BARE_SEGMENT_EQUALITY_RE.finditer(ctext_norm):
                    eq_spans.append((m_eq.start("full"), m_eq.end("full")))
            # Part-to-part ratio ("SE = 3EC") counts only when 5b-3 actually built its `point_divides_segment`.
            if any(p["kind"] == "point_divides_segment" for p in clause_premises):
                for m_eq in re.finditer(
                    rf",?\s*(?:sao\s+cho|thỏa\s+mãn|với|biết(?:\s+rằng)?|mà)\s+{_PTS2}\s*=\s*\d+(?:\s*/\s*\d+)?\s*{_PTS2}(?![\w'/])",
                    ctext_norm, re.IGNORECASE | re.UNICODE,
                ):
                    eq_spans.append((m_eq.start(), m_eq.end()))
            for eq_idx, ch in enumerate(ctext_norm):
                if ch == "=" and not any(a <= eq_idx < b for a, b in eq_spans):
                    mapped_fact = False
                    mapped_goal = False
                    clause.notes.append(f"UNBACKED_EQUALS@{eq_idx}:{ctext_norm[max(0, eq_idx - 12):eq_idx + 12].strip()}")
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
            clause.notes.append("UNBACKED_PARALLEL")
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
                clause.notes.append("UNBACKED_PERPENDICULAR")
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
                clause.notes.append(f"UNBACKED_ANGLE@{s_tok}:{ctext_norm[s_tok:s_tok + 24].strip()}")
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
            + (r"|\bmặt\s+bên\b.*\bnằm\s+trong\s+mặt\s+phẳng\s+vuông\s+góc\b"
               if "face_perpendicular_base" not in prem_kinds else ""),
            ctext_norm,
            re.IGNORECASE | re.UNICODE,
        ):
            mapped_fact = False
            mapped_goal = False
            clause.notes.append("UNSUPPORTED_SHAPE_RELATION_OR_CONDITION" if not unbacked_base_shape else "UNBACKED_BASE_SHAPE")
            clause.classification = CLAUSE_UNPARSED_FACT_CANDIDATE
            return

        # 5) Named point introduction `Gọi <P> là ...` where `<P>` was not bound in premises or solids
        for m_goi_pt in re.finditer(rf"\bGọi\s+(?P<pt>{_PT})\s+là\b", ctext_norm, re.IGNORECASE | re.UNICODE):
            pt_name = m_goi_pt.group("pt")
            if not pt_name[0].isupper():
                continue
            bound_in_clause = (
                any(
                    p["args"].get("point") == pt_name or p["args"].get("image") == pt_name
                    for p in clause_premises
                )
                or any(
                    s.get("center") == pt_name or s.get("notation") == pt_name
                    for s in clause_solids
                )
                or any(
                    st.get("point") == pt_name
                    for sec_d in builder.derived_sections
                    for st in (sec_d.get("stated_intersections") or ())
                )
            )
            if not bound_in_clause:
                mapped_fact = False
                mapped_goal = False
                clause.notes.append(f"UNBOUND_NAMED_POINT:{pt_name}")
                clause.classification = CLAUSE_UNPARSED_FACT_CANDIDATE
                return

        # 6) Compound goal completeness: if two scalar goal quantities are joined by `và`/`cùng`, must have >= 2 math_goals
        _q_kw = r"(?:diện\s+tích|thể\s+tích|khoảng\s+cách|k/c|độ\s+dài|bán\s+kính|góc\s+(?:giữa|tạo\s+bởi|hợp\s+bởi)|tỉ\s+số|chu\s+vi)"
        if mapped_goal and re.search(
            rf"\b{_q_kw}\b.+?\b(?:và|cùng)\s+(?:tính\s+)?{_q_kw}\b",
            ctext_norm,
            re.IGNORECASE | re.UNICODE,
        ):
            if len(clause_goals) < 2:
                mapped_goal = False
                mapped_fact = False
                clause.notes.append("INCOMPLETE_COMPOUND_GOAL")
                clause.classification = CLAUSE_UNPARSED_GOAL_CANDIDATE
                return

        # 7) Comma-joined sub-clauses (run `compositional-semantics-simulation-goals`): a sentence is read by many rules at
        # once, so one recognised relation must not make the whole sentence MAPPED while another comma-joined part of it was
        # read by nothing ("…, SA = a, N thuộc cạnh SB."). Every part with geometric content must overlap a quote that an
        # item of THIS sentence carries; otherwise the sentence is partially read and never complete.
        lost = _unread_subclauses(builder, ca, cb, (pre_solids_len, pre_premises_len, pre_sections_len, pre_goals_len),
                                  pre_other_lens)
        if lost:
            mapped_fact = False
            mapped_goal = False
            clause.notes.extend(f"UNREAD_SUBCLAUSE@{a - clause.start}:{raw[a:b].strip()[:120]}" for a, b in lost)
            lost_v_sub = _unread_values(builder, ca, cb, (pre_solids_len, pre_premises_len, pre_sections_len, pre_goals_len),
                                        pre_other_lens)
            if lost_v_sub:
                clause.notes.extend(f"UNREAD_VALUE@{p - clause.start}:{raw[max(ca, p - 40):p + 12].strip()}" for p in lost_v_sub)
            clause.classification = (CLAUSE_UNPARSED_GOAL_CANDIDATE if any(_QUESTION_STARTER_RE.search(raw[a:b]) for a, b in lost)
                                     else CLAUSE_UNPARSED_FACT_CANDIDATE)
            return
        # 7b) Run `grounded-vietnamese-geometry-understanding`: a recognised part may still carry a value no item read
        # ("… cạnh bên bằng a và diện tích đáy bằng a²": the side was read, the area was not). A value of the premise part
        # of the sentence outside every quote of this sentence's items is a silently lost premise: never complete.
        lost_v = _unread_values(builder, ca, cb, (pre_solids_len, pre_premises_len, pre_sections_len, pre_goals_len),
                                pre_other_lens)
        if lost_v:
            mapped_fact = False
            mapped_goal = False
            clause.notes.extend(f"UNREAD_VALUE@{p - clause.start}:{raw[max(ca, p - 40):p + 12].strip()}" for p in lost_v)
            clause.classification = CLAUSE_UNPARSED_FACT_CANDIDATE
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
            clause.notes.append("NO_GOAL_RULE_MATCHED")
            clause.classification = CLAUSE_UNPARSED_GOAL_CANDIDATE
        elif _FACT_INDICATOR_RE.search(ctext_norm):
            clause.notes.append("NO_FACT_RULE_MATCHED")
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
    comp = analyze_compositional_geometry(raw)
    parse_raw = normalize_problem_text(comp.mapped.normalized_text) if comp.mapped.diacritic_projected else raw
    clauses = split_into_clauses(parse_raw)
    builder = _AstBuilder(parse_raw)

    ambig_spans = [(a.norm_start, a.norm_end) for a in comp.ambiguous_visualization_clauses]
    if comp.ambiguous_visualization_clauses:
        for amb_cl in comp.ambiguous_visualization_clauses:
            builder.unresolved.append(
                {
                    "unresolved_id": f"u{len(builder.unresolved) + 1}",
                    "kind": "ambiguous",
                    "quote": amb_cl.orig_text,
                    "missing_roles": ["calculation_or_named_entity"],
                    "candidate_relations": [],
                }
            )
    for i in _clause_order(clauses):
        cl_orig = clauses[i]
        if any(max(cl_orig.start, sa) < min(cl_orig.end, sb) for sa, sb in ambig_spans):
            cl_orig.classification = CLAUSE_UNPARSED_FACT_CANDIDATE
            continue
        ct_s = cl_orig.text.strip()
        if CONTEXT_HEADER_RE.fullmatch(ct_s) or META_NO_CALC_RE.fullmatch(ct_s.strip(" .;!?")):
            cl_orig.classification = CLAUSE_BENIGN_DISCOURSE
            continue
        l_off = 0
        r_off = len(cl_orig.text)
        sub = cl_orig.text
        if m_eh := INLINE_EXAM_HEADER_PREFIX_RE.match(sub):
            if sub[m_eh.end():].strip():
                l_off += m_eh.end()
                sub = sub[m_eh.end():]
        if m_lm := INLINE_LEADING_META_RE.match(sub):
            if sub[m_lm.end():].strip():
                l_off += m_lm.end()
                sub = sub[m_lm.end():]
        if m_tm := INLINE_TRAILING_META_RE.search(sub):
            if sub[:m_tm.start()].strip():
                r_off = l_off + m_tm.start()
        if l_off or r_off != len(cl_orig.text):
            adj_cl = ClauseSpan(
                index=cl_orig.index,
                start=cl_orig.start + l_off,
                end=cl_orig.start + r_off,
                text=parse_raw[cl_orig.start + l_off : cl_orig.start + r_off],
            )
            _parse_clause_into_ast(builder, adj_cl)
            cl_orig.classification = adj_cl.classification
            cl_orig.notes = list(adj_cl.notes)
        else:
            _parse_clause_into_ast(builder, cl_orig)
    _resolve_late_regular_polygon_dimension(builder)

    if comp.mapped.diacritic_projected:
        mapped_src = comp.mapped.normalized_text

        def _orig_quote(q_txt: str) -> str:
            if not q_txt or q_txt in raw:
                return q_txt
            p0 = mapped_src.find(q_txt)
            if p0 >= 0:
                oq = comp.mapped.orig_quote(p0, p0 + len(q_txt))
                if oq and oq in raw:
                    return oq
            return q_txt

        for coll in (
            builder.solids,
            builder.premises,
            builder.relations,
            builder.derived_sections,
            builder.simulation_goals,
            builder.math_goals,
            builder.unresolved,
        ):
            for entry in coll:
                if isinstance(entry, dict) and isinstance(entry.get("quote"), str):
                    entry["quote"] = _orig_quote(entry["quote"])

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
            {"index": c.index, "start": c.start, "end": c.end, "text": c.text, "classification": c.classification,
             **({"notes": list(c.notes)} if c.notes else {})}
            for c in clauses
        ),
        coverage_complete=coverage_ok,
    )

    for ds in builder.derived_sections:
        ds.pop("_start_offset", None)

    payload: dict[str, Any] = {
        "schema_version": "typed-fact-next/2",
        "problem_text": raw,
        "length_unit": _infer_length_unit(raw, builder.premises, builder.solids),
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
        if builder.unresolved and ({u["kind"] for u in builder.unresolved} & {"missing_operand", "ambiguous", "unrecognized_term"}):
            return LocalParseResult(
                parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
                status=LOCAL_PARSE_AMBIGUOUS,
                payload=None,
                parsed_contract=None,
                ast=ast_summary,
                source_coverage=cov_report,
                reason_code="AMBIGUOUS_FACT",
                fallback_reason=f"AMBIGUOUS_UNRESOLVED:{exc.code}",
                parse_latency_ms=(time.perf_counter() - t0) * 1000.0,
            )
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
        tok_pol = registry._CHINH_SACH_XUAT.set(bridged["bridge"].get("output_policies"))
        try:
            registry.kiem_nguon(calls_t, raw, tuple(plan.auxiliary), doc_quotes)
        finally:
            registry._CHINH_SACH_XUAT.reset(tok_pol)
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


_PLANE_NAME_DEF_RE = re.compile(
    r"\((?P<n>[A-Z]|[α-ω])'?\)\s+(?:đi\s+qua|qua|chứa)(?!\w)|Gọi\s+\((?P<g>[A-Z]|[α-ω])'?\)\s+là\s+mặt\s+phẳng",
    re.IGNORECASE | re.UNICODE)
_PLANE_NAME_USE_RE = re.compile(r"\((?P<n>[A-Z]|[α-ω])'?\)", re.UNICODE)


def _clause_order(clauses: list[ClauseSpan]) -> list[int]:
    """Order of clause parsing (run `compositional-semantics-simulation-goals`): source order, except that a QUESTION
    clause using a plane name that only a LATER clause defines ("Xác định thiết diện … bởi (P). Biết (P) đi qua M …") is
    parsed right after that definition. Nothing is assumed: the question still binds only a plane the source defines, and
    an undefined name stays unparsed. Clause indices, spans and classifications are unchanged."""
    defs = [{m.group("n") or m.group("g") for m in _PLANE_NAME_DEF_RE.finditer(c.text)} for c in clauses]
    order: list[int] = []
    deferred: dict[int, list[int]] = {}
    for i, c in enumerate(clauses):
        used = {m.group("n") for m in _PLANE_NAME_USE_RE.finditer(c.text)} - defs[i]
        earlier = set().union(*defs[:i]) if i else set()
        later = [j for j in range(i + 1, len(clauses)) if used & defs[j]]
        if used and not (used & earlier) and later and _QUESTION_STARTER_RE.match(c.text.strip()):
            deferred.setdefault(max(later), []).append(i)
            continue
        order.append(i)
        order += deferred.pop(i, [])
    return order


def _resolve_late_regular_polygon_dimension(builder: "_AstBuilder") -> None:
    """semantic-to-scene3d: "đáy ABCD là hình vuông, biết AB = 1" — the side is given by a LATER clause.

    The regular-polygon rule records a `missing_operand` (dimension) when its own clause has no side. Under the strict
    Coupling Guard (`dimension-aware-verified-construction`), `missing_operand(dimension)` is cleared ONLY when:
    1. A direct base metric/ratio premise exists on `poly` (`segment_length`, `face_area`, `solid_volume`, `segment_ratio`); OR
    2. An off-base metric premise (`segment_length`, `height`, `face_area`) is algebraically coupled to `poly` via an
       explicit angle (`line_plane_angle`, `plane_plane_angle`, `dihedral_angle`, `line_line_angle`, `vertex_angle`) or
       `equal_length` bridging off-base and base vertices; OR
    3. All goals are strictly scale-invariant (`angle`, `length_ratio`, `area_ratio`, `volume_ratio`) AND an angle /
       equal-length coupling fixes the aspect ratio between off-base and base vertices.
    Uncoupled off-base lengths (e.g. `đáy ABCD là hình vuông, SA = 2a`) and bare regular pyramids (`DEV37:missing_dimension`)
    stay `LOCAL_PARSE_AMBIGUOUS`. Nothing is added — every fact carries its own quote."""
    if not builder.unresolved:
        return
    keep = []
    for u in builder.unresolved:
        poly = next((p for p in builder.premises if p.get("kind") == "regular_polygon" and p.get("quote") == u.get("quote")
                     and "side" not in (p.get("args") or {})), None)
        if u.get("kind") == "missing_operand" and u.get("missing_roles") == ["dimension"] and poly is not None:
            p_verts = set(poly["args"]["vertices"])
            has_direct_dim = any(
                (
                    q.get("kind") == "segment_length"
                    and len(set(q["args"].get("segment") or ())) == 2
                    and set(q["args"]["segment"]) <= p_verts
                )
                or (
                    q.get("kind") == "face_area"
                    and set(q["args"].get("polygon") or ()) == p_verts
                )
                or (
                    q.get("kind") == "solid_volume"
                    and q.get("solid_id") == poly.get("solid_id")
                )
                or (
                    q.get("kind") == "segment_ratio"
                    and (
                        set(q["args"].get("segment_a") or ()) <= p_verts
                        or set(q["args"].get("segment_b") or ()) <= p_verts
                    )
                )
                for q in builder.premises
            )
            has_off_base_metric = any(
                (
                    q.get("kind") == "segment_length"
                    and len(set(q["args"].get("segment") or ())) == 2
                    and not (set(q["args"]["segment"]) <= p_verts)
                )
                or (
                    q.get("kind") == "height"
                    and (q.get("solid_id") in (None, poly.get("solid_id")))
                )
                or (
                    q.get("kind") == "face_area"
                    and set(q["args"].get("polygon") or ()) != p_verts
                )
                for q in builder.premises
            )
            has_equal_bridge = any(
                q.get("kind") == "equal_length"
                and (
                    (set(q["args"].get("segment_a") or ()) <= p_verts)
                    != (set(q["args"].get("segment_b") or ()) <= p_verts)
                )
                for q in builder.premises
            )
            has_angle_coupling = False
            for q in builder.premises:
                qk = q.get("kind")
                qa = q.get("args") or {}
                if qk == "line_plane_angle":
                    pts_q = set(qa.get("line") or ()) | set(qa.get("plane") or ())
                elif qk == "plane_plane_angle":
                    pts_q = set(qa.get("plane1") or ()) | set(qa.get("plane2") or ())
                elif qk == "dihedral_angle":
                    pts_q = {qa.get("point_a"), qa.get("point_b"), *(qa.get("edge") or ())} - {None}
                elif qk == "line_line_angle":
                    pts_q = set(qa.get("line1") or ()) | set(qa.get("line2") or ())
                elif qk == "vertex_angle":
                    pts_q = {qa.get("vertex"), *(qa.get("rays") or ())} - {None}
                else:
                    continue
                if (pts_q & p_verts) and (pts_q - p_verts):
                    has_angle_coupling = True
                    break
            all_goals_scale_invariant = (
                (not builder.math_goals and bool(builder.simulation_goals))
                or (
                    bool(builder.math_goals)
                    and all(
                        (g.get("goal_type") if g.get("kind") == "measurement" else g.get("kind"))
                        in ("angle", "length_ratio", "area_ratio", "volume_ratio")
                        for g in builder.math_goals
                    )
                )
            )
            if (
                has_direct_dim
                or (has_off_base_metric and (has_angle_coupling or has_equal_bridge))
                or (all_goals_scale_invariant and (has_angle_coupling or has_equal_bridge))
            ):
                continue
        keep.append(u)
    builder.unresolved[:] = keep


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
