"""Grounded Vietnamese geometry extraction via local sub-1B SLM (Axo Hybrid /5 & /6).

Supports three extraction strategies behind deterministic source grounding,
schema validation, and parser-conflict checks:
  - ``compact_clause`` (AXO HYBRID /6): Deterministic clause/entity/quantity
    indexing + span-audited Verified Normalization + whitespace-free GBNF
    clause-level classification and slot filling + deterministic lowering into
    canonical ``typed-fact-next/2`` payloads.
  - ``minimal_ops`` (AXO HYBRID /5 baseline): Clause-indexed primitive ops.
  - ``direct_wire`` (AXO HYBRID /5 comparator): Direct wire JSON emission.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import os
import re
import threading
import time
from typing import Any

from app.ai.adapter4_route import ADAPTER_V4_VERSION, ROUTE_D_SIMULATION_V4_SCHEMA_VERSION
from app.ai.compositional_clause_analysis import (
    CONTEXT_HEADER_RE,
    INLINE_EXAM_HEADER_PREFIX_RE,
    INLINE_LEADING_META_RE,
    INLINE_TRAILING_META_RE,
    META_NO_CALC_RE,
    SIMULATION_LEAD_VERB_RE,
    _EMBEDDED_SOLID_HEAD_RE,
    _TRAILING_GOAL_SPLIT_RE,
    analyze_compositional_geometry,
)
from app.ai.local_geometry_parser import (
    LOCAL_GEOMETRY_PARSER_VERSION,
    LOCAL_PARSE_COMPLETE,
    _SIM_REQUEST_RE,
    _canon_val,
    normalize_problem_text,
    parse_geometry_problem_locally,
    split_into_Sentences,
)
from app.ai.local_slm_runtime import (
    DEFAULT_LOCAL_SLM_MAX_TOKENS,
    DEFAULT_LOCAL_SLM_MODEL_KEY,
    LOCAL_SLM_CACHE_NAMESPACE,
    LOCAL_SLM_CACHE_V9_NAMESPACE,
    LOCAL_SLM_RUNTIME_V9_VERSION,
    LOCAL_SLM_RUNTIME_VERSION,
    LocalSlmInferenceResult,
    LocalSlmRuntime,
    LocalSlmRuntimeError,
    build_local_slm_cache_identity,
    get_shared_local_slm_extraction_cache,
    get_shared_local_slm_runtime,
    resolve_local_slm_model_spec,
)
from app.ai.slm_verified_normalizer import (
    SLM_VERIFIED_NORMALIZER_V1_VERSION,
    SLM_VERIFIED_NORMALIZER_V3_VERSION,
    SLM_VERIFIED_NORMALIZER_VERSION,
    VerifiedNormalizationResult,
    _CONDITIONAL_MARKER_RE,
    _NEGATED_SPAN_RE,
    normalize_for_slm_grounding,
)
from app.ai.typed_fact_next_extraction import (
    TYPED_FACT_NEXT_V2_SCHEMA_VERSION,
    _normalize_transport_payload,
    to_wire_typed_fact_next_v2,
)
from app.simulation.geometry.expression import ExprParseError, parse_quantity_expr
from app.simulation.geometry_functions import engine, planner, registry

LOCAL_SLM_EXTRACTOR_VERSION = "local-slm-extractor/3"
#: /6 and validator /6 (AXO HYBRID /12): compositional clause splitting, nested simulation lead-in canonicalization,
#: universal edge / solid height cues, controlled diacritic restoration, and A3 visualization ambiguity refusal.
LOCAL_SLM_EXTRACTOR_V9_VERSION = "local-slm-extractor/6"
SLM_COMPACT_SCHEMA_VERSION = "slm-compact-clause/1"
SLM_GROUNDING_VALIDATOR_VERSION = "slm-grounding-validator/3"
SLM_GROUNDING_VALIDATOR_V9_VERSION = "slm-grounding-validator/6"
#: /11 grammar variant (chosen by SLM_RECOVERY_ABLATION.json): in a simulation-only root, `u` non-empty only with `r:[]`.
SIM_ONLY_UNRESOLVED_WITHOUT_FACTS = True
SLM_GROUNDING_ENVELOPE_VERSION = "slm-grounding-envelope/3"
SLM_GROUNDING_ENVELOPE_V9_VERSION = "slm-grounding-envelope/4"
DEFAULT_COMPACT_SLM_MAX_TOKENS = 320
DEFAULT_COMPACT_SLM_CTX_SIZE = 2048

SUPPORTED_SLM_STRATEGIES = ("compact_clause", "compact_clause_per_clause", "minimal_ops", "direct_wire")
DEFAULT_LOCAL_SLM_STRATEGY = "compact_clause"
V9_CLOSURE_MODE = "v9"
SUPPORTED_CLOSURE_MODES = ("v6", "v7", "v9")
DEFAULT_CLOSURE_MODE = "v7"

_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|above|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?(?:rules|constraints|source\s+gate)", re.IGNORECASE),
    re.compile(r"bypass\s+(?:source\s*gate|validation|grounding)", re.IGNORECASE),
    re.compile(r"bỏ\s+qua\s+(?:mọi\s+|tất\s+cả\s+)?(?:hướng\s+dẫn|quy\s+tắc|kiểm\s+tra(?:\s+nguồn)?)", re.IGNORECASE),
    re.compile(r"(?:system\s*prompt|<\|im_start\|>|<\|im_end\|>|```\s*json)", re.IGNORECASE),
    re.compile(r"(?:hãy\s+)?(?:tự\s+bịa|giả\s+định\s+thêm|trả\s+về\s+kết\s+quả\s+served|output\s+the\s+following\s+json)", re.IGNORECASE),
)

_CONVERSATIONAL_PREFIX_V6_RE = re.compile(
    r"^\s*(?:"
    r"(?:em|mình|tớ|bạn|nhờ\s+(?:anh|chị|bạn|thầy|cô|axo)?|giải\s+giúp(?:\s+em|\s+mình)?|"
    r"chào\s+[^,.:;!?]+|xin\s+hỏi|cho\s+(?:em|mình)\s+hỏi|em\s+đang\s+(?:học|làm)\s+bài[^,.:;!?]*)"
    r"[\s,:;\-–]+)+",
    re.IGNORECASE | re.UNICODE,
)

# Case-safe greeting prefix regex (`v7`): NEVER match uppercase 2+ letter geometry edge labels like "EM", "MN", "CD".
_CONVERSATIONAL_PREFIX_RE = re.compile(
    r"^\s*(?:"
    r"(?:(?:[Ee]m|[Mm]ình|[Tt]ớ|[Bb]ạn)\s+(?:ơi|nhé|hỏi|cần|muốn|nhờ|đang(?:\s+học|\s+làm)?|có\s+bài)|"
    r"(?:[Ee]m|[Mm]ình|[Tt]ớ|[Bb]ạn)\s+(?=[a-zà-ỹ]{2,})|"
    r"[Nn]hờ(?:\s+(?:anh|chị|bạn|thầy|cô|[Aa]xo))?|"
    r"[Gg]iải\s+giúp(?:\s+em|\s+mình)?|"
    r"[Cc]hào\s+[^,.:;!?]+|[Xx]in\s+hỏi|[Cc]ho\s+(?:em|mình)\s+hỏi)"
    r"[\s,:;\-–]+)+",
    re.UNICODE,
)

_NEGATED_PREDICATE_RE = re.compile(
    r"\b(?:không|chẳng|chưa)\s+(?:hề\s+)?(?:vuông\s+góc|vuông|cắt|song\s+song|bằng|đều|cân|trùng|thuộc|nằm\s+trong)\b"
    r"|\bkhông\s+phải\s+(?:hình\s+vuông|hình\s+chữ\s+nhật|tam\s+giác\s+đều|tam\s+giác\s+vuông|lăng\s+trụ\s+đứng|chóp\s+đều)\b",
    re.IGNORECASE | re.UNICODE,
)

_PURE_QUESTION_RE = re.compile(
    r"^\s*(?:hãy\s+)?(?:tính|tìm|xác\s+định|hỏi|cho\s+biết|yêu\s+cầu\s+tính)\b",
    re.IGNORECASE | re.UNICODE,
)
_PREMISE_MARKERS_IN_CLAUSE_RE = re.compile(
    r"\b(?:cho|biết|biết\s+rằng|với|có|trong\s+đó|giả\s+sử|khi\s+đó)\b",
    re.IGNORECASE | re.UNICODE,
)
_GOAL_MARKERS_RE = re.compile(
    r"(?:\b(?:tính|tìm|xác\s+định|hỏi|dựng|mô\s+phỏng|vẽ|thể\s+tích|khoảng\s+cách|diện\s+tích|góc|tỉ\s+số|độ\s+dài|chiều\s+cao|bán\s+kính)\b|\?)",
    re.IGNORECASE | re.UNICODE,
)
_GOAL_VERB_RE = re.compile(
    r"(?:\b(?:tính|tìm|xác\s+định|hỏi|cho\s+biết|yêu\s+cầu|bao\s+nhiêu|bằng\s+mấy|dài\s+bao\s+nhiêu|rộng\s+bao\s+nhiêu|cao\s+bao\s+nhiêu)\b|\?)",
    re.IGNORECASE | re.UNICODE,
)
_STRICT_GOAL_ASK_RE = re.compile(
    r"(?:\b(?:tính(?!\s+chất)|tìm|xác\s+định|hỏi|bao\s+nhiêu|bằng\s+mấy)\b|\?)",
    re.IGNORECASE | re.UNICODE,
)

_AMBIGUOUS_LATERAL_SINGLE_RE = re.compile(r"\bcạnh\s+bên\b", re.IGNORECASE | re.UNICODE)
_UNIVERSAL_LATERAL_RE = re.compile(
    r"\b(?:các|tất\s+cả|mọi|từng)\s+cạnh\s+bên\b|\bchóp\s+(?:tứ\s+giác\s+|tam\s+giác\s+)?đều\b",
    re.IGNORECASE | re.UNICODE,
)
_AMBIGUOUS_FACE_SINGLE_RE = re.compile(r"\bmặt\s+bên\b", re.IGNORECASE | re.UNICODE)

_SOLID_RE = re.compile(r"(?<![A-Za-zÀ-Ỹà-ỹ0-9'])((?:[A-Z][0-9]*'*){1,6})\.((?:[A-Z][0-9]*'*){3,6})(?![A-Za-zÀ-Ỹà-ỹ0-9'])")
_VERTEX_PAIR_OR_CHAIN_RE = re.compile(r"(?<![A-Za-zÀ-Ỹà-ỹ])([A-Z][0-9]*'*)(?=[A-Z0-9'\.)\]\s,;:/=-]|$)")
_TOKEN_QTY_RE = re.compile(
    r"(?<![A-Za-zÀ-Ỹà-ỹ])("
    r"(?:\d+(?:[.,]\d+)?\s*\*?\s*)?[a-zA-Z]?(?:\s*√\s*\d+|sqrt\(\d+\))(?:\s*/\s*\d+)?"
    r"|(?:\d+(?:[.,]\d+)?\s*\*?\s*)?a(?:\s*/\s*\d+)?"
    r"|\d+(?:[.,]\d+)?(?:\s*/\s*\d+)?\s*°?"
    r")(?![A-Za-zÀ-Ỹà-ỹ])",
    re.UNICODE,
)

_PREDICATE_LEXICAL_CUES: dict[str, tuple[str, ...]] = {
    "regular_polygon": ("đều", "hình vuông", "vuông cạnh", "lập phương", "tứ diện đều"),
    "rectangle": ("chữ nhật", "hcn"),
    "parallelogram": ("bình hành", "hbh"),
    "rhombus": ("hình thoi",),
    "trapezoid": ("hình thang",),
    "isosceles_trapezoid": ("hình thang cân",),
    "right_angle": ("vuông", "90", "⊥"),
    "perpendicular_line_plane": ("vuông góc", "vuông", "⊥", "đứng", "đường cao", "chiều cao", "trục"),
    "perpendicular_lines": ("vuông góc", "vuông", "⊥"),
    "face_perpendicular_base": ("vuông góc", "⊥"),
    "altitude": ("đường cao", "chiều cao", "chân đường cao", "vuông góc", "hình chiếu", "đều"),
    "orthogonal_projection": ("hình chiếu", "chiếu"),
    "orthogonal_projection_line": ("hình chiếu", "chiếu"),
    "midpoint": ("trung điểm", "điểm chính giữa"),
    "centroid": ("trọng tâm",),
    "divide_segment": ("chia", "tỉ số", "=", "/", "lần", "nửa", "gấp"),
    "intersect_line_line": ("cắt", "giao điểm", "giao của", "∩"),
    "intersect_line_plane": ("cắt", "giao điểm", "∩"),
    "segment_length": ("=", "bằng", "cạnh", "dài", "độ dài", "a", "chiều cao"),
    "equal_length": ("=", "bằng", "cân", "đều"),
    "height": ("chiều cao", "đường cao", "cao bằng", "cao"),
    "line_plane_angle": ("góc", "tạo với", "hợp với", "°", "sin", "cos", "tan", "cot"),
    "plane_plane_angle": ("góc", "°", "sin", "cos", "tan", "cot"),
    "dihedral_angle": ("nhị diện", "góc", "°"),
    "line_line_angle": ("góc", "°"),
    "vertex_angle": ("góc", "°"),
    "face_area": ("diện tích",),
    "solid_volume": ("thể tích",),
    "segment_ratio": ("tỉ số", "tỷ số", "gấp", "nửa", "=", "/"),
}

_PREDICATE_NEGATION_EXEMPT = frozenset({"segment_length", "height", "face_area", "solid_volume"})

_VALUE_CARRYING_OPS = frozenset({
    "regular_polygon",
    "rhombus",
    "segment_length",
    "height",
    "divide_segment",
    "line_plane_angle",
    "plane_plane_angle",
    "dihedral_angle",
    "line_line_angle",
    "vertex_angle",
    "face_area",
    "solid_volume",
    "segment_ratio",
})

_WORD_RATIO_MAP: dict[str, str] = {
    "gấp đôi": "2",
    "gấp ba": "3",
    "gấp bốn": "4",
    "một nửa": "1/2",
    "nửa": "1/2",
}

MINIMAL_OPS_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "solid": {
            "type": ["object", "null"],
            "additionalProperties": False,
            "properties": {
                "clause_id": {"type": "integer"},
                "solid_type": {"type": "string", "enum": ["pyramid", "prism"]},
                "notation": {"type": "string"},
                "reg": {"type": "boolean"},
            },
            "required": ["clause_id", "solid_type", "notation", "reg"],
        },
        "ops": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "clause_id": {"type": "integer"},
                    "kind": {
                        "type": "string",
                        "enum": sorted(_PREDICATE_LEXICAL_CUES.keys()),
                    },
                    "a": {"type": "array", "items": {"type": "string"}},
                    "b": {"type": "array", "items": {"type": "string"}},
                    "pt": {"type": "string"},
                    "val": {"type": "string"},
                    "unit": {"type": "string", "enum": ["", "deg", "rad", "sin", "cos", "tan", "cot"]},
                },
                "required": ["clause_id", "kind", "a", "b", "pt", "val", "unit"],
            },
        },
        "goals": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "clause_id": {"type": "integer"},
                    "goal_type": {
                        "type": "string",
                        "enum": ["volume", "distance", "angle", "area", "length", "length_ratio", "area_ratio"],
                    },
                    "a": {"type": "array", "items": {"type": "string"}},
                    "b": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["clause_id", "goal_type", "a", "b"],
            },
        },
        "unresolved": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "clause_id": {"type": "integer"},
                    "kind": {
                        "type": "string",
                        "enum": ["ambiguous", "missing_operand", "unrecognized_term", "unsupported", "contradictory"],
                    },
                    "reason": {"type": "string"},
                },
                "required": ["clause_id", "kind", "reason"],
            },
        },
    },
    "required": ["solid", "ops", "goals", "unresolved"],
}

DIRECT_WIRE_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "length_unit": {"type": "string"},
        "solids": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "solid_id": {"type": "string"},
                    "solid_type": {"type": "string", "enum": ["pyramid", "prism"]},
                    "notation": {"type": "string"},
                    "quote": {"type": "string"},
                },
                "required": ["solid_id", "solid_type", "notation", "quote"],
            },
        },
        "premises": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "kind": {"type": "string"},
                    "args": {"type": "array", "items": {"type": "string"}},
                    "quote": {"type": "string"},
                    "solid_id": {"type": "string"},
                },
                "required": ["kind", "args", "quote", "solid_id"],
            },
        },
        "simulation_goals": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "goal_id": {"type": "string"},
                    "kind": {"type": "string", "enum": ["construct_object", "construct_plane_section", "construct_intersection_line"]},
                    "target_solid_id": {"type": "string"},
                    "quote": {"type": "string"},
                },
                "required": ["goal_id", "kind", "target_solid_id", "quote"],
            },
        },
        "math_goals": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "goal_id": {"type": "string"},
                    "kind": {"type": "string", "enum": ["measurement", "length_ratio", "area_ratio"]},
                    "goal_type": {"type": "string", "enum": ["volume", "distance", "angle", "area", "length"]},
                    "target": {"type": "array", "items": {"type": "string"}},
                    "solid_id": {"type": "string"},
                    "quote": {"type": "string"},
                },
                "required": ["goal_id", "kind", "goal_type", "target", "solid_id", "quote"],
            },
        },
        "unresolved": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "kind": {"type": "string", "enum": ["ambiguous", "missing_operand", "unrecognized_term", "unsupported"]},
                    "excerpt": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["kind", "excerpt", "reason"],
            },
        },
    },
    "required": ["length_unit", "solids", "premises", "simulation_goals", "math_goals", "unresolved"],
}


@dataclass(frozen=True)
class IndexedClause:
    clause_id: int
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class LocalSlmExtractionResult:
    ok: bool
    strategy: str
    model_key: str
    model_sha256: str
    norm_text: str
    wire_payload: dict[str, Any] | None
    canonical_payload: dict[str, Any] | None
    reason_code: str | None
    reason_detail: str | None
    failure_taxonomy: str
    grounding_envelope: dict[str, Any]
    inference: LocalSlmInferenceResult | None = None
    stage_timings_ms: dict[str, Any] = field(default_factory=dict)
    normalization_provenance: dict[str, Any] | None = None
    cache_hit: bool = False
    cache_key: str | None = None


def resolve_local_slm_strategy(strategy: str | None = None) -> str:
    raw = str(strategy or os.getenv("LOCAL_SLM_STRATEGY") or DEFAULT_LOCAL_SLM_STRATEGY).strip().lower()
    if raw not in SUPPORTED_SLM_STRATEGIES:
        return DEFAULT_LOCAL_SLM_STRATEGY
    return raw


def detect_prompt_injection(text: str) -> str | None:
    for pat in _INJECTION_PATTERNS:
        m = pat.search(text or "")
        if m:
            return m.group(0)
    return None


def index_source_clauses(norm_text: str) -> list[IndexedClause]:
    out: list[IndexedClause] = []
    for sa, sb, st in split_into_Sentences(norm_text):
        s_trim = st.strip()
        if not s_trim:
            continue
        if CONTEXT_HEADER_RE.fullmatch(s_trim) or META_NO_CALC_RE.fullmatch(s_trim.strip(" .;!?")):
            continue
        cur_a, cur_b = sa, sb
        sub = norm_text[cur_a:cur_b]
        if m_eh := INLINE_EXAM_HEADER_PREFIX_RE.match(sub):
            if sub[m_eh.end():].strip():
                cur_a += m_eh.end()
                sub = norm_text[cur_a:cur_b]
        if m_lm := INLINE_LEADING_META_RE.match(sub):
            if sub[m_lm.end():].strip():
                cur_a += m_lm.end()
                sub = norm_text[cur_a:cur_b]
        if m_tm := INLINE_TRAILING_META_RE.search(sub):
            if sub[:m_tm.start()].strip():
                cur_b = cur_a + m_tm.start()
                sub = norm_text[cur_a:cur_b]
        split_hits = [] if _SIM_REQUEST_RE.match(sub) else list(_TRAILING_GOAL_SPLIT_RE.finditer(sub))
        if split_hits:
            pos = 0
            for m_sp in split_hits:
                l_end = m_sp.start()
                while l_end > pos and sub[l_end - 1] in " \t,;:":
                    l_end -= 1
                l_start = pos
                while l_start < l_end and sub[l_start].isspace():
                    l_start += 1
                if l_start < l_end:
                    out.append(IndexedClause(
                        clause_id=len(out),
                        start=cur_a + l_start,
                        end=cur_a + l_end,
                        text=norm_text[cur_a + l_start : cur_a + l_end],
                    ))
                pos = m_sp.end()
            t_a, t_b = pos, len(sub)
            while t_a < t_b and sub[t_a].isspace():
                t_a += 1
            while t_b > t_a and sub[t_b - 1] in " \t":
                t_b -= 1
            if t_a < t_b:
                out.append(IndexedClause(
                    clause_id=len(out),
                    start=cur_a + t_a,
                    end=cur_a + t_b,
                    text=norm_text[cur_a + t_a : cur_a + t_b],
                ))
        else:
            t_a, t_b = cur_a, cur_b
            while t_a < t_b and norm_text[t_a].isspace():
                t_a += 1
            while t_b > t_a and norm_text[t_b - 1].isspace():
                t_b -= 1
            if t_a < t_b:
                out.append(IndexedClause(
                    clause_id=len(out),
                    start=t_a,
                    end=t_b,
                    text=norm_text[t_a:t_b],
                ))
    return out


def extract_geometry_points(text: str) -> set[str]:
    pts: set[str] = set()
    for s_match in _SOLID_RE.finditer(text or ""):
        pts.update(re.findall(r"[A-Z][0-9]*'*", s_match.group(0)))
    for m in re.finditer(r"(?<![A-Za-zÀ-Ỹà-ỹ])([A-Z][0-9]*'*)(?=[A-Z0-9'\.)\]\s,;:/=-]|$)", text or ""):
        pts.add(m.group(1))
    # Remove trailing empty artifacts and add any multi-cap contiguous vertices (like "SA" -> S, A; "ABC" -> A, B, C)
    expanded: set[str] = set()
    for p in list(pts):
        parts = re.findall(r"[A-Z][0-9]*'*", p)
        if parts:
            expanded.update(parts)
    # Catch contiguous uppercase vertex runs such as "S.ABCD" or "(SBC)" or "SA"
    for m_run in re.finditer(r"(?<![a-zà-ỹ])[A-Z][A-Z0-9'\.]{1,12}(?![a-zà-ỹ])", text or ""):
        expanded.update(re.findall(r"[A-Z][0-9]*'*", m_run.group(0)))
    return expanded


def _strip_conversational_prefix(span: str, *, closure_mode: str = DEFAULT_CLOSURE_MODE) -> str:
    rx = _CONVERSATIONAL_PREFIX_V6_RE if closure_mode == "v6" else _CONVERSATIONAL_PREFIX_RE
    cleaned = rx.sub("", span).strip()
    return cleaned if cleaned else span


def _cand_has_contiguous(cand: str, label: str) -> bool:
    """True when `label` (or its 2-vertex reversal) appears contiguously at proper label boundaries inside `cand`."""
    if "." in label:
        return bool(re.search(rf"(?<![A-Z0-9']){re.escape(label)}(?![A-Z0-9'])", cand))
    if re.search(rf"(?<![A-Z0-9'.]){re.escape(label)}(?![A-Z0-9'.])", cand):
        return True
    pts = re.findall(r"[A-Z][0-9]*'*", label)
    if len(pts) == 2:
        rev = f"{pts[1]}{pts[0]}"
        return bool(re.search(rf"(?<![A-Z0-9'.]){re.escape(rev)}(?![A-Z0-9'.])", cand))
    return False


def select_clean_quote(
    clause_text: str,
    required_tokens: list[str],
    norm_text: str,
    *,
    required_contiguous: list[str] | None = None,
    required_cues: tuple[str, ...] | None = None,
    closure_mode: str = DEFAULT_CLOSURE_MODE,
) -> str:
    """Pick the tightest verbatim substring of `norm_text` carrying all required tokens."""
    use_v7 = closure_mode != "v6"
    use_v9 = closure_mode == V9_CLOSURE_MODE
    req = [t for t in required_tokens if t]
    contig_req = (
        [
            lbl
            for lbl in (required_contiguous or ())
            if lbl and _cand_has_contiguous(clause_text, lbl)
        ]
        if use_v7
        else []
    )
    clause_low = clause_text.lower()
    active_cues = tuple(c for c in (required_cues or ()) if c and c.lower() in clause_low) if use_v7 else ()

    candidates: list[str] = []
    trimmed = _strip_conversational_prefix(clause_text, closure_mode=closure_mode)
    if trimmed and trimmed in norm_text:
        candidates.append(trimmed)

    # First split strictly on major punctuation in v7 (preserving "và" inside compound clauses),
    # while preserving exact /6 splitting in v6 ablation mode.
    if use_v7:
        for piece in re.split(r"\s*[,;]\s*", trimmed):
            seg = piece.strip(" ,;:")
            if seg and seg in norm_text:
                candidates.append(seg)
    for sep_pat in (r"\s*,\s*|\s+đồng\s+thời\s+|\s+và\s+|\s+còn\s+|\s+trong\s+đó\s+",):
        for piece in re.split(sep_pat, trimmed, flags=re.IGNORECASE):
            seg = piece.strip(" ,;:")
            if seg and seg in norm_text:
                candidates.append(seg)

    candidates.append(clause_text)

    # Prefer shortest candidate containing all required vertex/scalar tokens, contiguous labels, and active cues
    valid: list[str] = []
    for cand in candidates:
        if cand not in norm_text:
            continue
        cand_pts = extract_geometry_points(cand)
        ok = True
        for tok in req:
            if re.fullmatch(r"[A-Z][0-9]*'*", tok):
                if use_v9:
                    if tok not in cand_pts:
                        ok = False
                        break
                elif tok not in cand_pts and tok not in cand:
                    ok = False
                    break
            elif tok.lower() not in cand.lower():
                ok = False
                break
        if ok and contig_req:
            if not all(_cand_has_contiguous(cand, lbl) for lbl in contig_req):
                ok = False
        if ok and active_cues:
            cand_low = cand.lower()
            if not any(cue.lower() in cand_low for cue in active_cues):
                ok = False
        if ok:
            valid.append(cand)
    if valid:
        valid.sort(key=len)
        return valid[0]
    if trimmed in norm_text and len(trimmed) >= 4:
        return trimmed
    return clause_text


def _try_eval_qty(raw: str) -> str | None:
    s = _canon_val(str(raw or "").strip().rstrip("°"))
    if not s:
        return None
    try:
        expr = parse_quantity_expr(s, allow_signed=False, allow_unit=False)
        return repr(expr)
    except ExprParseError:
        return None


def _normalize_scalar_str(raw: str) -> str:
    s = _canon_val(str(raw or "").strip())
    s = re.sub(r"\s+", "", s)
    s = s.rstrip(".,;:")
    return s


def is_value_grounded_in_clause(slm_value: str, clause_text: str, *, allow_unit_default_a: bool = False) -> tuple[bool, str]:
    raw_val = str(slm_value or "").strip()
    if not raw_val:
        return False, ""

    norm_slm = _normalize_scalar_str(raw_val)
    slm_eval = _try_eval_qty(raw_val)

    # Collect candidate quantity tokens from clause_text
    candidates: list[str] = [m.group(1) for m in _TOKEN_QTY_RE.finditer(clause_text)]
    clow = clause_text.lower()
    for word, mapped in _WORD_RATIO_MAP.items():
        if word in clow:
            candidates.append(mapped)

    # Reject pure numberless standalone "a" unless "a" truly appears as a quantity/length symbol in clause_text
    for cand in candidates:
        norm_c = _normalize_scalar_str(cand)
        if not norm_c:
            continue
        if norm_c.lower() == norm_slm.lower():
            return True, cand.strip().rstrip(".,;:")
        cand_eval = _try_eval_qty(cand)
        if slm_eval is not None and cand_eval is not None and slm_eval == cand_eval:
            return True, cand.strip().rstrip(".,;:")

    # Handle implicit "đều cạnh a" style expressions where whitespace separated multiplier or √
    if norm_slm.rstrip("°").isdigit():
        deg_re = re.compile(rf"(?<!\d){re.escape(norm_slm.rstrip('°'))}\s*°?")
        if deg_re.search(clause_text):
            return True, norm_slm.rstrip("°")

    if allow_unit_default_a and norm_slm == "a" and re.search(r"\bcạnh\s+a\b|\bbằng\s+a\b", clause_text, re.IGNORECASE):
        return True, "a"

    return False, ""


def _parse_solid_vertices(solid_type: str, notation: str) -> tuple[str, ...]:
    s = str(notation or "").strip()
    if "." not in s:
        return ()
    left, right = s.split(".", 1)
    if solid_type == "pyramid":
        apex = re.findall(r"[A-Z][0-9]*'*", left)
        base = re.findall(r"[A-Z][0-9]*'*", right)
        if len(apex) != 1 or len(base) < 3 or apex[0] in base or len(set(base)) != len(base):
            return ()
        return (apex[0], *base)
    if solid_type == "prism":
        b1 = re.findall(r"[A-Z][0-9]*'*", left)
        b2 = re.findall(r"[A-Z][0-9]*'*", right)
        if len(b1) < 3 or len(b1) != len(b2) or set(b1) & set(b2):
            return ()
        return (*b1, *b2)
    return ()


def _solid_base_vertices(solid_info: dict[str, Any] | None) -> list[str]:
    if not solid_info:
        return []
    notation = solid_info["notation"]
    stype = solid_info["solid_type"]
    _, right = notation.split(".", 1)
    if stype == "pyramid":
        return re.findall(r"[A-Z][0-9]*'*", right)
    left, _ = notation.split(".", 1)
    return re.findall(r"[A-Z][0-9]*'*", left)


def _infer_length_unit(premises: list[dict[str, Any]]) -> str:
    for p in premises:
        args = p.get("args") or {}
        for k in ("side", "value"):
            v = str(args.get(k) or "").strip()
            if "a" in v:
                return "a"
    return "1"


def _local_parser_segment_lengths(local_res_payload: dict[str, Any] | None) -> dict[frozenset[str], str]:
    out: dict[frozenset[str], str] = {}
    if not local_res_payload:
        return out
    for p in local_res_payload.get("premises") or ():
        if p.get("kind") == "segment_length":
            seg = (p.get("args") or {}).get("segment") or []
            val = (p.get("args") or {}).get("value")
            if len(seg) == 2 and val:
                out[frozenset(seg)] = _normalize_scalar_str(str(val))
    return out


def _clause_supports_op(
    clause: IndexedClause,
    kind: str,
    pts1: list[str],
    pts2: list[str],
    tpt: str,
    raw_val: str,
    solid_info: dict[str, Any] | None,
    all_points: set[str],
) -> tuple[bool, str | None]:
    ctext = clause.text
    clow = ctext.lower()
    if _PURE_QUESTION_RE.match(ctext) and not _PREMISE_MARKERS_IN_CLAUSE_RE.search(clow):
        return False, f"GOAL_CLAUSE_USED_AS_PREMISE:clause_{clause.clause_id}"
    if kind not in _PREDICATE_NEGATION_EXEMPT and _NEGATED_PREDICATE_RE.search(clow):
        return False, f"NEGATED_PREDICATE_CLAUSE:{kind}"
    cues = _PREDICATE_LEXICAL_CUES[kind]
    if not any(cue in clow for cue in cues):
        return False, f"PREDICATE_CUE_MISSING:{kind}"
    if _AMBIGUOUS_LATERAL_SINGLE_RE.search(clow) and not _UNIVERSAL_LATERAL_RE.search(clow):
        if not re.findall(r"\b[A-Z][0-9]*'*[A-Z][0-9]*'*\b", ctext):
            return False, "AMBIGUOUS_REFERENCE:lateral_edge_not_unique"
    if _AMBIGUOUS_FACE_SINGLE_RE.search(clow) and "(" not in ctext:
        if not re.findall(r"\b[A-Z][0-9]*'*[A-Z][0-9]*'*[A-Z][0-9]*'*\b", ctext):
            return False, "AMBIGUOUS_REFERENCE:lateral_face_not_unique"
    all_op_pts = pts1 + pts2 + ([tpt] if tpt else [])
    clause_pts = extract_geometry_points(ctext)
    base_pts = set(_solid_base_vertices(solid_info))
    for pt in all_op_pts:
        if not re.fullmatch(r"[A-Z][0-9]*'*", pt):
            return False, f"INVALID_POINT_TOKEN:{pt}"
        in_clause = pt in clause_pts
        in_base_indirect = ("đáy" in clow or "mặt đáy" in clow) and solid_info is not None and pt in base_pts
        if not (in_clause or in_base_indirect or (pt in all_points and len(all_points) <= 12 and in_clause)):
            if not (in_base_indirect or in_clause):
                return False, f"UNGROUNDED_POINT:{pt}"
    if kind == "segment_length" and len(pts1) == 2:
        seg_ab = f"{pts1[0]}{pts1[1]}"
        seg_ba = f"{pts1[1]}{pts1[0]}"
        if seg_ab not in ctext and seg_ba not in ctext:
            return False, f"UNGROUNDED_SEGMENT_PAIR:{seg_ab}"
    if raw_val:
        ok, gval = is_value_grounded_in_clause(raw_val, ctext, allow_unit_default_a=True)
        if not ok:
            return None if False else False, f"UNGROUNDED_VALUE:{kind}:{raw_val}"
        if kind == "segment_length" and len(pts1) == 2:
            seg_ab = f"{pts1[0]}{pts1[1]}"
            seg_ba = f"{pts1[1]}{pts1[0]}"
            esc_v = re.escape(gval)
            near_pat = re.compile(
                rf"(?:{re.escape(seg_ab)}|{re.escape(seg_ba)})[^.;!?]{{0,40}}{esc_v}"
                rf"|{esc_v}[^.;!?]{{0,25}}(?:{re.escape(seg_ab)}|{re.escape(seg_ba)})",
                re.IGNORECASE | re.UNICODE,
            )
            if not near_pat.search(ctext):
                return False, f"UNGROUNDED_VALUE:segment_length_proximity:{seg_ab}:{raw_val}"
    return True, None


def _convert_op_to_premise(
    op: dict[str, Any],
    clauses: list[IndexedClause],
    norm_text: str,
    solid_info: dict[str, Any] | None,
    all_points: set[str],
) -> tuple[dict[str, Any] | None, str | None]:
    """Validate and lower one Approach-B minimal op into a grounded premise dict."""
    cid = op.get("clause_id")
    kind = str(op.get("kind") or "").strip()
    if kind not in _PREDICATE_LEXICAL_CUES:
        return None, f"UNSUPPORTED_OP_KIND:{kind}"

    pts1 = [str(x).strip() for x in (op.get("a") if "a" in op else op.get("points") or []) if str(x).strip()]
    pts2 = [str(x).strip() for x in (op.get("b") if "b" in op else op.get("points2") or []) if str(x).strip()]
    tpt = str(op.get("pt") if "pt" in op else op.get("target_point") or "").strip()
    raw_val = str(op.get("val") if "val" in op else op.get("value") or "").strip()
    unit = str(op.get("unit") or "").strip()

    all_op_pts = pts1 + pts2 + ([tpt] if tpt else [])
    for pt in all_op_pts:
        if not re.fullmatch(r"[A-Z][0-9]*'*", pt):
            return None, f"INVALID_POINT_TOKEN:{pt}"
        if pt not in all_points:
            return None, f"UNGROUNDED_POINT:{pt}"

    ordered_clauses: list[IndexedClause] = []
    if isinstance(cid, int) and 0 <= cid < len(clauses):
        ordered_clauses.append(clauses[cid])
    for cl in clauses:
        if cl not in ordered_clauses:
            ordered_clauses.append(cl)
    if not ordered_clauses:
        return None, f"UNGROUNDED_CLAUSE_ID:{cid}"

    clause: IndexedClause | None = None
    first_err: str | None = None
    for cand_cl in ordered_clauses:
        ok_cl, err_cl = _clause_supports_op(cand_cl, kind, pts1, pts2, tpt, raw_val, solid_info, all_points)
        if err_cl in ("NEGATED_PREDICATE_CLAUSE:" + kind,) or (err_cl or "").startswith("AMBIGUOUS_REFERENCE:"):
            # Wait: check if negated predicate specifically mentions ALL op points or primary cue
            cand_pts = extract_geometry_points(cand_cl.text)
            if not all_op_pts or any(p in cand_pts for p in all_op_pts):
                return None, err_cl
        if ok_cl:
            clause = cand_cl
            break
        if first_err is None:
            first_err = err_cl

    if clause is None:
        return None, first_err or f"UNGROUNDED_CLAUSE_ID:{cid}"
    ctext = clause.text
    clow = ctext.lower()

    # 5. Build exact TypedFactNext /2 premise args + value grounding
    args: dict[str, Any] = {}
    quote_tokens = list(all_op_pts)

    if kind == "regular_polygon":
        if len(pts1) < 3:
            return None, "INVALID_PREMISE_ARGS:regular_polygon"
        args["vertices"] = pts1
        if raw_val:
            ok, gval = is_value_grounded_in_clause(raw_val, ctext, allow_unit_default_a=True)
            if not ok:
                return None, f"UNGROUNDED_VALUE:regular_polygon:{raw_val}"
            args["side"] = gval
            quote_tokens.append(gval)
    elif kind == "rectangle":
        if len(pts1) != 4:
            return None, "INVALID_PREMISE_ARGS:rectangle"
        args["vertices"] = pts1
    elif kind == "parallelogram":
        if len(pts1) != 4:
            return None, "INVALID_PREMISE_ARGS:parallelogram"
        args["vertices"] = pts1
    elif kind == "rhombus":
        if len(pts1) != 4:
            return None, "INVALID_PREMISE_ARGS:rhombus"
        args["vertices"] = pts1
        if raw_val:
            ok, gval = is_value_grounded_in_clause(raw_val, ctext, allow_unit_default_a=True)
            if not ok:
                return None, f"UNGROUNDED_VALUE:rhombus:{raw_val}"
            args["side"] = gval
            quote_tokens.append(gval)
    elif kind in ("trapezoid", "isosceles_trapezoid"):
        if len(pts1) != 4 or len(pts2) != 2:
            return None, f"INVALID_PREMISE_ARGS:{kind}"
        rem = [v for v in pts1 if v not in pts2]
        if len(rem) != 2:
            return None, f"INVALID_PREMISE_ARGS:{kind}"
        args = {"vertices": pts1, "base_a": pts2, "base_b": rem}
    elif kind == "right_angle":
        if len(pts1) >= 3 and not tpt:
            v = pts1[1] if "vuông tại" not in clow else next((x for x in pts1 if f"vuông tại {x.lower()}" in clow or f"tại {x.lower()}" in clow), pts1[0])
            rays = [x for x in pts1 if x != v][:2]
            tpt = v
            pts1 = rays
        if not tpt or len(pts1) != 2:
            return None, "INVALID_PREMISE_ARGS:right_angle"
        args = {"vertex": tpt, "rays": pts1}
    elif kind == "segment_length":
        if len(pts1) != 2 or not raw_val:
            return None, "INVALID_PREMISE_ARGS:segment_length"
        ok, gval = is_value_grounded_in_clause(raw_val, ctext, allow_unit_default_a=True)
        if not ok:
            return None, f"UNGROUNDED_VALUE:segment_length:{raw_val}"
        args = {"segment": pts1, "value": gval}
        quote_tokens.append(gval)
    elif kind == "equal_length":
        if len(pts1) != 2 or len(pts2) != 2:
            return None, "INVALID_PREMISE_ARGS:equal_length"
        args = {"segment_a": pts1, "segment_b": pts2}
    elif kind == "height":
        ok, gval = is_value_grounded_in_clause(raw_val, ctext, allow_unit_default_a=True)
        if not ok:
            return None, f"UNGROUNDED_VALUE:height:{raw_val}"
        args = {"value": gval}
        quote_tokens.append(gval)
    elif kind == "perpendicular_line_plane":
        if len(pts1) != 2 or len(pts2) < 3:
            if len(pts1) == 2 and ("đáy" in clow) and len(base_pts := _solid_base_vertices(solid_info)) >= 3:
                pts2 = base_pts
            else:
                return None, "INVALID_PREMISE_ARGS:perpendicular_line_plane"
        args = {"line": pts1, "plane": pts2}
    elif kind == "perpendicular_lines":
        if len(pts1) != 2 or len(pts2) != 2:
            return None, "INVALID_PREMISE_ARGS:perpendicular_lines"
        args = {"line1": pts1, "line2": pts2}
    elif kind == "face_perpendicular_base":
        if len(pts1) < 3:
            return None, "INVALID_PREMISE_ARGS:face_perpendicular_base"
        if len(pts2) < 3:
            pts2 = _solid_base_vertices(solid_info)
        if len(pts2) < 3:
            return None, "INVALID_PREMISE_ARGS:face_perpendicular_base"
        args = {"face": pts1, "base": pts2}
    elif kind == "altitude":
        apex = tpt or (pts1[0] if len(pts1) >= 1 else "")
        foot = pts2[0] if len(pts2) >= 1 else (pts1[1] if len(pts1) >= 2 else "")
        if not apex or not foot or apex == foot:
            return None, "INVALID_PREMISE_ARGS:altitude"
        args = {"apex": apex, "foot": foot}
    elif kind == "orthogonal_projection":
        img = tpt or (pts1[1] if len(pts1) >= 2 else "")
        src_pt = pts1[0] if len(pts1) >= 1 else ""
        if not img or not src_pt or len(pts2) < 3:
            if img and src_pt and ("đáy" in clow) and len(bverts := _solid_base_vertices(solid_info)) >= 3:
                pts2 = bverts
            else:
                return None, "INVALID_PREMISE_ARGS:orthogonal_projection"
        args = {"point": src_pt, "image": img, "plane": pts2}
    elif kind == "orthogonal_projection_line":
        img = tpt
        src_pt = pts1[0] if len(pts1) >= 1 else ""
        if not img or not src_pt or len(pts2) != 2:
            return None, "INVALID_PREMISE_ARGS:orthogonal_projection_line"
        args = {"point": src_pt, "image": img, "line": pts2}
    elif kind == "midpoint":
        if not tpt or len(pts1) != 2:
            return None, "INVALID_PREMISE_ARGS:midpoint"
        args = {"point": tpt, "segment": pts1}
    elif kind == "centroid":
        if not tpt or len(pts1) < 3:
            return None, "INVALID_PREMISE_ARGS:centroid"
        args = {"point": tpt, "polygon": pts1}
    elif kind == "divide_segment":
        if not tpt or len(pts1) != 2 or not raw_val:
            return None, "INVALID_PREMISE_ARGS:divide_segment"
        ok, gval = is_value_grounded_in_clause(raw_val, ctext)
        if not ok:
            return None, f"UNGROUNDED_VALUE:divide_segment:{raw_val}"
        args = {"point": tpt, "segment": pts1, "ratio": gval}
        quote_tokens.append(gval)
    elif kind == "intersect_line_line":
        if not tpt or len(pts1) != 2 or len(pts2) != 2:
            return None, "INVALID_PREMISE_ARGS:intersect_line_line"
        args = {"point": tpt, "line1": pts1, "line2": pts2}
    elif kind == "intersect_line_plane":
        if not tpt or len(pts1) != 2 or len(pts2) < 3:
            return None, "INVALID_PREMISE_ARGS:intersect_line_plane"
        args = {"point": tpt, "line": pts1, "plane": pts2}
    elif kind == "line_plane_angle":
        if len(pts1) != 2 or len(pts2) < 3 or not raw_val:
            return None, "INVALID_PREMISE_ARGS:line_plane_angle"
        ok, gval = is_value_grounded_in_clause(raw_val, ctext)
        if not ok:
            return None, f"UNGROUNDED_VALUE:line_plane_angle:{raw_val}"
        args = {"line": pts1, "plane": pts2, "value": gval}
        if unit:
            args["unit"] = unit
        quote_tokens.append(gval)
    elif kind == "plane_plane_angle":
        if len(pts1) < 3 or len(pts2) < 3 or not raw_val:
            return None, "INVALID_PREMISE_ARGS:plane_plane_angle"
        ok, gval = is_value_grounded_in_clause(raw_val, ctext)
        if not ok:
            return None, f"UNGROUNDED_VALUE:plane_plane_angle:{raw_val}"
        args = {"plane1": pts1, "plane2": pts2, "value": gval}
        if unit:
            args["unit"] = unit
        quote_tokens.append(gval)
    elif kind == "dihedral_angle":
        if len(pts1) < 2 or len(pts2) != 2 or not raw_val:
            return None, "INVALID_PREMISE_ARGS:dihedral_angle"
        ok, gval = is_value_grounded_in_clause(raw_val, ctext)
        if not ok:
            return None, f"UNGROUNDED_VALUE:dihedral_angle:{raw_val}"
        args = {"point_a": pts1[0], "edge": pts2, "point_b": pts1[1], "value": gval}
        if unit:
            args["unit"] = unit
        quote_tokens.append(gval)
    elif kind == "line_line_angle":
        if len(pts1) != 2 or len(pts2) != 2 or not raw_val:
            return None, "INVALID_PREMISE_ARGS:line_line_angle"
        ok, gval = is_value_grounded_in_clause(raw_val, ctext)
        if not ok:
            return None, f"UNGROUNDED_VALUE:line_line_angle:{raw_val}"
        args = {"line1": pts1, "line2": pts2, "value": gval}
        if unit:
            args["unit"] = unit
        quote_tokens.append(gval)
    elif kind == "vertex_angle":
        if not tpt or len(pts1) != 2 or not raw_val:
            return None, "INVALID_PREMISE_ARGS:vertex_angle"
        ok, gval = is_value_grounded_in_clause(raw_val, ctext)
        if not ok:
            return None, f"UNGROUNDED_VALUE:vertex_angle:{raw_val}"
        args = {"vertex": tpt, "rays": pts1, "value": gval}
        if unit:
            args["unit"] = unit
        quote_tokens.append(gval)
    elif kind == "face_area":
        if len(pts1) < 3 or not raw_val:
            return None, "INVALID_PREMISE_ARGS:face_area"
        ok, gval = is_value_grounded_in_clause(raw_val, ctext)
        if not ok:
            return None, f"UNGROUNDED_VALUE:face_area:{raw_val}"
        args = {"polygon": pts1, "value": gval}
        quote_tokens.append(gval)
    elif kind == "solid_volume":
        if not raw_val:
            return None, "INVALID_PREMISE_ARGS:solid_volume"
        ok, gval = is_value_grounded_in_clause(raw_val, ctext)
        if not ok:
            return None, f"UNGROUNDED_VALUE:solid_volume:{raw_val}"
        args = {"value": gval}
        quote_tokens.append(gval)
    elif kind == "segment_ratio":
        if len(pts1) != 2 or len(pts2) != 2 or not raw_val:
            return None, "INVALID_PREMISE_ARGS:segment_ratio"
        ok, gval = is_value_grounded_in_clause(raw_val, ctext)
        if not ok:
            return None, f"UNGROUNDED_VALUE:segment_ratio:{raw_val}"
        args = {"segment_a": pts1, "segment_b": pts2, "ratio": gval}
        quote_tokens.append(gval)

    quote = select_clean_quote(ctext, quote_tokens, norm_text)
    premise: dict[str, Any] = {
        "kind": kind,
        "args": args,
        "quote": quote,
    }
    if solid_info is not None:
        premise["solid_id"] = solid_info["solid_id"]
    return premise, None


def _convert_goal(
    goal: dict[str, Any],
    idx: int,
    clauses: list[IndexedClause],
    norm_text: str,
    solid_info: dict[str, Any] | None,
    all_points: set[str],
) -> tuple[dict[str, Any] | None, str | None]:
    cid = goal.get("clause_id")
    ordered_goal_clauses: list[IndexedClause] = []
    if isinstance(cid, int) and 0 <= cid < len(clauses):
        ordered_goal_clauses.append(clauses[cid])
    for cl in clauses:
        if cl not in ordered_goal_clauses and _STRICT_GOAL_ASK_RE.search(cl.text):
            ordered_goal_clauses.append(cl)
    for cl in clauses:
        if cl not in ordered_goal_clauses and _GOAL_MARKERS_RE.search(cl.text):
            ordered_goal_clauses.append(cl)
    if not ordered_goal_clauses:
        return None, f"UNGROUNDED_GOAL_CLAUSE_ID:{cid}"

    # Collect target tokens cleanly first before picking the exact verbatim goal clause
    gtype = str(goal.get("goal_type") or "").strip()
    gid = f"q{idx + 1}"
    quote_tokens: list[str] = []
    if "a" in goal or "b" in goal:
        ga = [str(x).strip() for x in (goal.get("a") or []) if str(x).strip()]
        gb = [str(x).strip() for x in (goal.get("b") or []) if str(x).strip()]
        pt = ga[0] if gtype == "distance" and len(ga) == 1 and len(gb) >= 2 else ""
        seg = ga if gtype in ("length", "length_ratio") or (gtype == "distance" and len(ga) == 2 and not gb) else []
        line = ga if (gtype == "angle" and len(ga) == 2) or (gtype == "distance" and len(ga) == 2 and len(gb) >= 2) else (gb if gtype in ("distance", "angle") and len(gb) == 2 and len(ga) != 2 else [])
        line2 = gb if len(ga) == 2 and len(gb) == 2 else []
        plane = gb if len(gb) >= 3 and len(ga) < 3 else (ga if gtype in ("distance", "angle") and len(ga) >= 3 else [])
        plane2 = gb if len(ga) >= 3 and len(gb) >= 3 else []
        poly = ga if gtype in ("area", "area_ratio") else []
        if gtype == "angle" and len(ga) >= 3 and len(gb) == 2:
            line, plane = gb, ga
        if gtype == "distance" and len(ga) >= 3 and len(gb) == 1:
            pt, plane = gb[0], ga
        if gtype == "distance" and len(ga) == 2 and len(gb) == 1:
            pt, line = gb[0], ga
    else:
        pt = str(goal.get("point") or "").strip()
        seg = [str(x).strip() for x in (goal.get("segment") or []) if str(x).strip()]
        line = [str(x).strip() for x in (goal.get("line") or []) if str(x).strip()]
        line2 = [str(x).strip() for x in (goal.get("line2") or []) if str(x).strip()]
        plane = [str(x).strip() for x in (goal.get("plane") or []) if str(x).strip()]
        plane2 = [str(x).strip() for x in (goal.get("plane2") or []) if str(x).strip()]
        poly = [str(x).strip() for x in (goal.get("polygon") or []) if str(x).strip()]

    for vtok in [x for x in ([pt] if pt else []) + seg + line + line2 + plane + plane2 + poly]:
        if vtok not in all_points:
            return None, f"UNGROUNDED_GOAL_POINT:{vtok}"

    req_pts = [x for x in ([pt] if pt else []) + seg + line + line2 + plane + plane2 + poly]
    is_solid_height_goal = False
    if gtype == "distance" and pt and len(plane) >= 3 and solid_info and solid_info.get("solid_type") == "pyramid" and "." in str(solid_info.get("notation") or ""):
        s_apex, s_base_raw = str(solid_info["notation"]).split(".", 1)
        s_base_pts = re.findall(r"[A-Z][0-9]*'*", s_base_raw)
        if pt == s_apex and set(plane) <= set(s_base_pts):
            is_solid_height_goal = True
    ctext = ""
    for gcl in ordered_goal_clauses:
        if not _GOAL_MARKERS_RE.search(gcl.text):
            continue
        gcl_pts = extract_geometry_points(gcl.text)
        gcl_low = gcl.text.lower()
        if gtype == "volume" and "thể tích" not in gcl_low and not re.search(r"\bv\s*[_(\[]", gcl_low):
            continue
        if not req_pts or all(rp in gcl_pts for rp in req_pts):
            ctext = gcl.text
            break
        if is_solid_height_goal and ("chiều cao" in gcl_low or "đường cao" in gcl_low):
            ctext = gcl.text
            break
    if not ctext:
        return None, f"UNGROUNDED_GOAL_CLAUSE_TOKENS:{gtype}"

    sid = solid_info["solid_id"] if solid_info is not None else None
    if gtype == "volume":
        if sid is None:
            return None, "MISSING_SOLID_FOR_VOLUME_GOAL"
        quote = select_clean_quote(ctext, ["thể tích"], norm_text)
        return {
            "goal_id": gid,
            "kind": "measurement",
            "goal_type": "volume",
            "target": {"solid_id": sid},
            "solid_id": sid,
            "quote": quote,
        }, None

    if gtype == "distance":
        target: dict[str, Any] = {}
        if pt and len(plane) >= 3:
            target = {"point": pt, "plane": plane[:3] if is_solid_height_goal else plane}
            if is_solid_height_goal and not all(tok in extract_geometry_points(ctext) for tok in [pt, *plane]):
                quote_tokens = ["chiều cao"] if "chiều cao" in ctext.lower() else ["đường cao"]
            else:
                quote_tokens = [pt, *plane]
        elif pt and len(line) == 2:
            target = {"point": pt, "line": line}
            quote_tokens = [pt, *line]
        elif len(line) == 2 and len(line2) == 2:
            target = {"line1": line, "line2": line2}
            quote_tokens = [*line, *line2]
        elif len(line) == 2 and len(plane) >= 3:
            target = {"line": line, "plane": plane}
            quote_tokens = [*line, *plane]
        elif len(plane) >= 3 and len(plane2) >= 3:
            target = {"plane1": plane, "plane2": plane2}
            quote_tokens = [*plane, *plane2]
        elif len(seg) == 2:
            target = {"segment": seg}
            quote_tokens = list(seg)
        else:
            return None, "INVALID_DISTANCE_GOAL_TARGET"
        mg: dict[str, Any] = {
            "goal_id": gid,
            "kind": "measurement",
            "goal_type": "distance",
            "target": target,
            "quote": select_clean_quote(ctext, quote_tokens, norm_text),
        }
        if sid is not None:
            mg["solid_id"] = sid
        return mg, None

    if gtype == "angle":
        target = {}
        if len(line) == 2 and len(plane) >= 3:
            target = {"line": line, "plane": plane}
            quote_tokens = [*line, *plane, "".join(line), "".join(plane)]
        elif len(line) == 2 and len(line2) == 2:
            target = {"line1": line, "line2": line2}
            quote_tokens = [*line, *line2, "".join(line), "".join(line2)]
        elif len(plane) >= 3 and len(plane2) >= 3:
            target = {"plane1": plane, "plane2": plane2}
            quote_tokens = [*plane, *plane2, "".join(plane), "".join(plane2)]
        else:
            return None, "INVALID_ANGLE_GOAL_TARGET"
        mg = {
            "goal_id": gid,
            "kind": "measurement",
            "goal_type": "angle",
            "target": target,
            "quote": select_clean_quote(ctext, quote_tokens, norm_text),
        }
        if sid is not None:
            mg["solid_id"] = sid
        return mg, None

    if gtype == "area":
        if len(poly) < 3:
            return None, "INVALID_AREA_GOAL_TARGET"
        mg = {
            "goal_id": gid,
            "kind": "measurement",
            "goal_type": "area",
            "target": {"polygon": poly},
            "quote": select_clean_quote(ctext, poly, norm_text),
        }
        if sid is not None:
            mg["solid_id"] = sid
        return mg, None

    if gtype == "length":
        if len(seg) != 2:
            return None, "INVALID_LENGTH_GOAL_TARGET"
        mg = {
            "goal_id": gid,
            "kind": "measurement",
            "goal_type": "distance",
            "target": {"segment": seg},
            "quote": select_clean_quote(ctext, seg, norm_text),
        }
        if sid is not None:
            mg["solid_id"] = sid
        return mg, None

    if gtype == "length_ratio":
        if len(seg) != 2 or len(line2) != 2:
            return None, "INVALID_LENGTH_RATIO_TARGET"
        mg = {
            "goal_id": gid,
            "kind": "length_ratio",
            "numerator_segment": seg,
            "denominator_segment": line2,
            "quote": select_clean_quote(ctext, [*seg, *line2], norm_text),
        }
        if sid is not None:
            mg["solid_id"] = sid
        return mg, None

    if gtype == "area_ratio":
        if len(poly) < 3 or len(plane2) < 3:
            return None, "INVALID_AREA_RATIO_TARGET"
        mg = {
            "goal_id": gid,
            "kind": "area_ratio",
            "numerator_polygon": poly,
            "denominator_polygon": plane2,
            "quote": select_clean_quote(ctext, [*poly, *plane2], norm_text),
        }
        if sid is not None:
            mg["solid_id"] = sid
        return mg, None

    return None, f"UNSUPPORTED_GOAL_TYPE:{gtype}"


def validate_and_lower_minimal_ops(
    *,
    norm_text: str,
    clauses: list[IndexedClause],
    raw_slm_json: dict[str, Any],
    local_parser_payload: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Deterministically verify every SLM emission against source text & parser facts."""
    all_points = extract_geometry_points(norm_text)
    accepted_ops: list[dict[str, Any]] = []
    rejected_ops: list[dict[str, str]] = []

    raw_unresolved = raw_slm_json.get("unresolved") or []
    unresolved_items: list[dict[str, Any]] = []
    for item in raw_unresolved:
        if not isinstance(item, dict):
            continue
        cid = item.get("clause_id")
        ukind = str(item.get("kind") or "ambiguous").strip()
        reason = str(item.get("reason") or "Unspecified uncertainty").strip()
        if isinstance(cid, int) and 0 <= cid < len(clauses):
            excerpt = select_clean_quote(clauses[cid].text, [], norm_text)
        else:
            excerpt = clauses[0].text if clauses else norm_text
        unresolved_items.append({"kind": ukind, "excerpt": excerpt, "reason": reason})

    if unresolved_items:
        # Check if contradiction vs missing/ambiguous
        has_contra = any(u.get("kind") == "contradictory" for u in unresolved_items)
        reason_code = "INCONSISTENT_FACTS" if has_contra else "AMBIGUOUS_FACT"
        if any(u.get("kind") == "unsupported" for u in unresolved_items) and len(unresolved_items) == 1:
            reason_code = "OUT_OF_SCOPE"
        return None, {
            "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
            "grounding_status": "SLM_REPORTED_UNRESOLVED",
            "reason_code": reason_code,
            "failure_taxonomy": "CONTRADICTION_OR_UNGROUNDED" if has_contra else "SLM_UNRESOLVED",
            "accepted_ops": [],
            "rejected_ops": [{"op": "unresolved", "reason": u["reason"]} for u in unresolved_items],
            "unresolved": unresolved_items,
        }

    # Validate solid
    solid_raw = raw_slm_json.get("solid")
    solids_list: list[dict[str, Any]] = []
    solid_info: dict[str, Any] | None = None
    solid_quote = ""
    if isinstance(solid_raw, dict):
        cid = solid_raw.get("clause_id")
        stype = str(solid_raw.get("solid_type") or "").strip()
        notation = str(solid_raw.get("notation") or "").strip()
        if not isinstance(cid, int) or cid < 0 or cid >= len(clauses):
            rejected_ops.append({"op": "solid", "reason": f"UNGROUNDED_SOLID_CLAUSE:{cid}"})
        else:
            verts = _parse_solid_vertices(stype, notation)
            if not verts:
                rejected_ops.append({"op": "solid", "reason": f"INVALID_SOLID_NOTATION:{notation}"})
            else:
                ctext = clauses[cid].text
                # Ground all vertices in clause text
                cpts = extract_geometry_points(ctext)
                if not all(v in cpts for v in verts):
                    rejected_ops.append({"op": "solid", "reason": f"UNGROUNDED_SOLID_VERTICES:{notation}"})
                else:
                    # Handle "tứ diện ABCD" where text doesn't have dot literal: quote clause cleanly
                    solid_quote = select_clean_quote(ctext, list(verts), norm_text)
                    solid_info = {
                        "solid_id": "s1",
                        "solid_type": stype,
                        "notation": notation,
                        "quote": solid_quote,
                    }
                    solids_list.append(solid_info)

    if not solids_list:
        return None, {
            "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
            "grounding_status": "REJECTED_MISSING_OR_INVALID_SOLID",
            "reason_code": "MISSING_DIMENSION" if not rejected_ops else "SOURCE_OBJECT_MISMATCH",
            "failure_taxonomy": "GROUNDING_REJECTED",
            "accepted_ops": [],
            "rejected_ops": rejected_ops or [{"op": "solid", "reason": "NO_GROUNDED_SOLID"}],
        }

    # Check Local Parser vs SLM solid conflict
    if local_parser_payload and local_parser_payload.get("solids"):
        lp_solid = local_parser_payload["solids"][0]
        if lp_solid.get("notation") and lp_solid.get("notation") != solid_info["notation"]:
            return None, {
                "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
                "grounding_status": "REJECTED_PARSER_SLM_CONFLICT",
                "reason_code": "PARSER_SLM_CONFLICT",
                "failure_taxonomy": "PARSER_SLM_CONFLICT",
                "accepted_ops": [],
                "rejected_ops": [{"op": "solid", "reason": f"CONFLICT_LOCAL={lp_solid.get('notation')}_SLM={solid_info['notation']}"}],
            }

    premises: list[dict[str, Any]] = []
    # Add implicit regular_pyramid / right_prism structural premise if grounded in clause text
    is_reg = bool(solid_raw.get("reg", solid_raw.get("is_regular_pyramid")))
    if is_reg and solid_info["solid_type"] == "pyramid":
        ctext_s = clauses[solid_raw["clause_id"]].text
        if "đều" in ctext_s.lower():
            apex = solid_info["notation"].split(".", 1)[0]
            base = _solid_base_vertices(solid_info)
            premises.append({
                "kind": "regular_pyramid",
                "args": {"apex": apex, "base": base},
                "quote": solid_quote,
                "solid_id": "s1",
            })
            accepted_ops.append({"kind": "regular_pyramid", "clause_id": solid_raw["clause_id"]})
    elif (
        is_reg or any(k in clauses[solid_raw["clause_id"]].text.lower() for k in ("đứng", "lập phương", "hộp chữ nhật"))
    ) and solid_info["solid_type"] == "prism":
        ctext_s = clauses[solid_raw["clause_id"]].text
        if any(k in ctext_s.lower() for k in ("đứng", "lập phương", "hộp chữ nhật")):
            left_s, right_s = solid_info["notation"].split(".", 1)
            b_verts = re.findall(r"[A-Z][0-9]*'*", left_s)
            t_verts = re.findall(r"[A-Z][0-9]*'*", right_s)
            premises.append({
                "kind": "right_prism",
                "args": {"base": b_verts, "top": t_verts},
                "quote": solid_quote,
                "solid_id": "s1",
            })
            accepted_ops.append({"kind": "right_prism", "clause_id": solid_raw["clause_id"]})

    # Validate each premise op
    lp_lengths = _local_parser_segment_lengths(local_parser_payload)
    for op in raw_slm_json.get("ops") or ():
        if not isinstance(op, dict):
            continue
        prem, err = _convert_op_to_premise(op, clauses, norm_text, solid_info, all_points)
        if err is not None:
            rejected_ops.append({"op": str(op.get("kind") or "unknown"), "reason": err})
            if err.startswith("AMBIGUOUS_REFERENCE"):
                return None, {
                    "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
                    "grounding_status": "REJECTED_AMBIGUOUS_REFERENCE",
                    "reason_code": "AMBIGUOUS_REFERENCE",
                    "failure_taxonomy": "AMBIGUOUS_REFERENCE",
                    "accepted_ops": accepted_ops,
                    "rejected_ops": rejected_ops,
                }
            if err.startswith("NEGATED_PREDICATE_CLAUSE"):
                return None, {
                    "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
                    "grounding_status": "REJECTED_NEGATED_FACT",
                    "reason_code": "INCONSISTENT_FACTS",
                    "failure_taxonomy": "GROUNDING_REJECTED",
                    "accepted_ops": accepted_ops,
                    "rejected_ops": rejected_ops,
                }
            continue
        assert prem is not None
        # Conflict check against Local Parser scalar lengths
        if prem["kind"] == "segment_length":
            seg_fs = frozenset(prem["args"]["segment"])
            slm_norm_val = _normalize_scalar_str(str(prem["args"]["value"]))
            if seg_fs in lp_lengths and lp_lengths[seg_fs] != slm_norm_val:
                return None, {
                    "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
                    "grounding_status": "REJECTED_PARSER_SLM_CONFLICT",
                    "reason_code": "PARSER_SLM_CONFLICT",
                    "failure_taxonomy": "PARSER_SLM_CONFLICT",
                    "accepted_ops": accepted_ops,
                    "rejected_ops": [*rejected_ops, {"op": "segment_length", "reason": f"CONFLICT_LOCAL={lp_lengths[seg_fs]}_SLM={slm_norm_val}"}],
                }
        # Avoid exact duplicates
        if not any(existing["kind"] == prem["kind"] and existing["args"] == prem["args"] for existing in premises):
            premises.append(prem)
            accepted_ops.append({"kind": prem["kind"], "clause_id": op.get("clause_id")})

    # Merge any Local Parser verified premises not already present (parser-first preservation)
    if local_parser_payload and local_parser_payload.get("premises"):
        for lp_p in local_parser_payload["premises"]:
            if not any(ep["kind"] == lp_p.get("kind") and ep["args"] == lp_p.get("args") for ep in premises):
                premises.append(lp_p)

    # Validate goals
    math_goals: list[dict[str, Any]] = []
    for idx, g in enumerate(raw_slm_json.get("goals") or ()):
        if not isinstance(g, dict):
            continue
        mg, gerr = _convert_goal(g, idx, clauses, norm_text, solid_info, all_points)
        if gerr is not None:
            rejected_ops.append({"op": f"goal:{g.get('goal_type')}", "reason": gerr})
            continue
        assert mg is not None
        math_goals.append(mg)
        accepted_ops.append({"kind": f"goal:{g.get('goal_type')}", "clause_id": g.get("clause_id")})

    if not math_goals:
        return None, {
            "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
            "grounding_status": "REJECTED_NO_GROUNDED_GOAL",
            "reason_code": "AMBIGUOUS_FACT" if rejected_ops else "MISSING_DIMENSION",
            "failure_taxonomy": "GROUNDING_REJECTED",
            "accepted_ops": accepted_ops,
            "rejected_ops": rejected_ops or [{"op": "goal", "reason": "NO_GROUNDED_GOAL"}],
        }

    # If any critical op was rejected due to ungrounded value/point/stray value, fail closed rather than partial guessing
    if any(r["reason"].startswith(("UNGROUNDED_VALUE:", "UNGROUNDED_POINT:", "UNEXPECTED_VALUE_ON_OP:")) for r in rejected_ops):
        return None, {
            "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
            "grounding_status": "REJECTED_UNGROUNDED_TOKEN",
            "reason_code": "UNGROUNDED_VALUE",
            "failure_taxonomy": "GROUNDING_REJECTED",
            "accepted_ops": accepted_ops,
            "rejected_ops": rejected_ops,
        }

    canon_payload: dict[str, Any] = {
        "schema_version": TYPED_FACT_NEXT_V2_SCHEMA_VERSION,
        "problem_text": norm_text,
        "length_unit": _infer_length_unit(premises),
        "solids": solids_list,
        "premises": premises,
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "s1",
                "quote": solid_quote,
            }
        ],
        "math_goals": math_goals,
    }
    return canon_payload, {
        "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
        "grounding_status": "GROUNDED_AND_LOWERED",
        "reason_code": None,
        "failure_taxonomy": "NONE",
        "accepted_ops": accepted_ops,
        "rejected_ops": rejected_ops,
    }


def _build_minimal_ops_messages(norm_text: str, clauses: list[IndexedClause], local_res: Any) -> list[dict[str, str]]:
    clause_lines = "\n".join(f"[{c.clause_id}] {c.text}" for c in clauses)
    parser_hint = f"Local parser: {local_res.status} ({local_res.reason_code or 'NONE'})."
    system_prompt = (
        "/no_think\n"
        "Trích xuất dữ kiện hình học không gian tiếng Việt sang JSON theo đúng schema.\n"
        "Quy tắc:\n"
        "- Chọn ĐÚNG [clause_id]; KHÔNG tự bịa số đo hay đỉnh.\n"
        "- Tách riêng từng quan hệ và độ dài thành op riêng: perpendicular_line_plane(a=đt,b=mp,val=''), segment_length(a=[P,Q],val='2a'), right_angle(pt=V,a=[X,Y],val=''), midpoint(pt=M,a=[X,Y],val=''), line_plane_angle(a=đt,b=mp,val='60',unit='deg').\n"
        "- Đỉnh có dấu phẩy giữ nguyên (vd \"A'\"). solid.reg=true khi là chóp đều hoặc lăng trụ đứng/hộp chữ nhật/lập phương.\n"
        "- goals: volume(a=[],b=[]), distance điểm tới mp(a=[pt],b=[p1,p2,p3]), angle đt và mp(a=[l1,l2],b=[p1,p2,p3]), length(a=[p1,p2],b=[]).\n"
        "- Thiếu dữ kiện, mơ hồ ('cạnh bên' đơn lẻ), mâu thuẫn ('không vuông góc') hoặc cầu/nón/trụ -> đưa vào unresolved.\n"
        "Ví dụ 1:\n"
        "[0] Cho hình chóp X.PQR có đáy PQR đều cạnh m\n"
        "[1] XP vuông góc với (PQR), XP=3m\n"
        "[2] Tính thể tích X.PQR\n"
        "=> solid:{clause_id:0,solid_type:'pyramid',notation:'X.PQR',reg:false}, "
        "ops:[{clause_id:0,kind:'regular_polygon',a:['P','Q','R'],b:[],pt:'',val:'m',unit:''},"
        "{clause_id:1,kind:'perpendicular_line_plane',a:['X','P'],b:['P','Q','R'],pt:'',val:'',unit:''},"
        "{clause_id:1,kind:'segment_length',a:['X','P'],b:[],pt:'',val:'3m',unit:''}], "
        "goals:[{clause_id:2,goal_type:'volume',a:[],b:[]}], unresolved:[].\n"
        "Ví dụ 2:\n"
        "[0] Xét chóp K.UVW\n"
        "[1] Tam giác UVW đều cạnh 2k\n"
        "[2] KU vuông góc (UVW), KU=k\n"
        "[3] Tìm khoảng cách từ U đến (KVW)\n"
        "=> solid:{clause_id:0,solid_type:'pyramid',notation:'K.UVW',reg:false}, "
        "ops:[{clause_id:1,kind:'regular_polygon',a:['U','V','W'],b:[],pt:'',val:'2k',unit:''},"
        "{clause_id:2,kind:'perpendicular_line_plane',a:['K','U'],b:['U','V','W'],pt:'',val:'',unit:''},"
        "{clause_id:2,kind:'segment_length',a:['K','U'],b:[],pt:'',val:'k',unit:''}], "
        "goals:[{clause_id:3,goal_type:'distance',a:['U'],b:['K','V','W']}], unresolved:[]."
    )
    user_prompt = f"{parser_hint}\nMệnh đề:\n{clause_lines}\nĐề bài:\n{norm_text}"
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _build_direct_wire_messages(norm_text: str) -> list[dict[str, str]]:
    system_prompt = (
        "/no_think\n"
        "Trích xuất đề toán hình học không gian tiếng Việt sang JSON theo đúng wire contract typed-fact-next/2.\n"
        "Chỉ trích quote nguyên văn từ đề bài, không bịa đặt số đo hay đỉnh không có trong đề. "
        "Đóng gói args/target theo danh sách chuỗi 'key=value' (ví dụ 'vertices=A,B,C', 'side=a', 'line=S,A', 'plane=A,B,C', 'solid_id=s1')."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": norm_text},
    ]


def _repair_direct_wire_quotes(wire: dict[str, Any], norm_text: str, all_points: set[str]) -> tuple[dict[str, Any] | None, str | None]:
    """Verify verbatim quotes & token grounding on Approach-A direct_wire JSON."""
    for s in wire.get("solids") or ():
        q = str(s.get("quote") or "")
        if not q or q not in norm_text:
            return None, f"QUOTE_NOT_IN_SOURCE:solid:{q}"
        stype = str(s.get("solid_type") or "")
        notation = str(s.get("notation") or "")
        verts = _parse_solid_vertices(stype, notation)
        if not verts or not all(v in all_points for v in verts):
            return None, f"UNGROUNDED_SOLID:{notation}"

    for p in wire.get("premises") or ():
        q = str(p.get("quote") or "")
        if not q or q not in norm_text:
            return None, f"QUOTE_NOT_IN_SOURCE:premise:{q}"
        for kv in p.get("args") or ():
            if not isinstance(kv, str) or "=" not in kv:
                return None, f"MALFORMED_WIRE_ARG:{kv}"
            k, _, rhs = kv.partition("=")
            if k.strip() in ("value", "side", "ratio"):
                ok, _ = is_value_grounded_in_clause(rhs.strip(), q, allow_unit_default_a=True)
                if not ok:
                    return None, f"UNGROUNDED_VALUE:direct_wire:{rhs}"

    for g in wire.get("math_goals") or ():
        q = str(g.get("quote") or "")
        if not q or q not in norm_text:
            return None, f"QUOTE_NOT_IN_SOURCE:math_goal:{q}"

    out = {
        "schema_version": TYPED_FACT_NEXT_V2_SCHEMA_VERSION,
        "problem_text": norm_text,
        "length_unit": wire.get("length_unit") or "1",
        "solids": wire.get("solids") or [],
        "premises": wire.get("premises") or [],
        "simulation_goals": wire.get("simulation_goals") or [],
        "math_goals": wire.get("math_goals") or [],
    }
    if wire.get("unresolved"):
        out["unresolved"] = wire["unresolved"]
    return out, None


# ===========================================================================
# AXO HYBRID /6: Clause-Level Compact Extraction, GBNF & Verified Lowering
# ===========================================================================

_COMPACT_PRED_CODES = (
    "reg_poly", "rect", "para", "rhom", "trap", "iso_trap",
    "right_tri", "right_iso_tri", "iso_tri",
    "perp_lp", "perp_ll", "face_perp",
    "mid", "cent", "proj", "alt", "inter_ll", "inter_lp", "div",
    "len", "eq_len", "height",
    "ang_lp", "ang_pp", "dihed", "ang_ll", "ang_vtx",
    "area", "vol", "ratio",
)

_COMPACT_TO_V5_KIND: dict[str, str] = {
    "reg_poly": "regular_polygon",
    "rect": "rectangle",
    "para": "parallelogram",
    "rhom": "rhombus",
    "trap": "trapezoid",
    "iso_trap": "isosceles_trapezoid",
    "right_tri": "right_angle",
    "right_iso_tri": "right_angle",
    "iso_tri": "equal_length",
    "perp_lp": "perpendicular_line_plane",
    "perp_ll": "perpendicular_lines",
    "face_perp": "face_perpendicular_base",
    "mid": "midpoint",
    "cent": "centroid",
    "proj": "orthogonal_projection",
    "alt": "altitude",
    "inter_ll": "intersect_line_line",
    "inter_lp": "intersect_line_plane",
    "div": "divide_segment",
    "len": "segment_length",
    "eq_len": "equal_length",
    "height": "height",
    "ang_lp": "line_plane_angle",
    "ang_pp": "plane_plane_angle",
    "dihed": "dihedral_angle",
    "ang_ll": "line_line_angle",
    "ang_vtx": "vertex_angle",
    "area": "face_area",
    "vol": "solid_volume",
    "ratio": "segment_ratio",
}

_COMPACT_GOAL_CODES: dict[str, str] = {
    "vol": "volume",
    "dist": "distance",
    "dist_pt_plane": "distance",
    "dist_pt_line": "distance",
    "dist_line_line": "distance",
    "ang": "angle",
    "ang_lp": "angle",
    "ang_ll": "angle",
    "ang_pp": "angle",
    "area": "area",
    "len": "length",
    "lratio": "length_ratio",
    "aratio": "area_ratio",
}

_COMPACT_UNRES_CODES: dict[str, str] = {
    "ambig": "ambiguous",
    "missing": "missing_operand",
    "unsup": "unsupported",
    "contra": "contradictory",
}

# Whitespace-free static fallback GBNF + dynamic per-problem literal-constrained GBNF builder.
COMPACT_CLAUSE_GBNF = r"""root ::= "{\"s\":" solidval ",\"r\":[" rellist "],\"g\":[" goallist "],\"u\":[" unreslist "]}"
solidval ::= "null" | "[" cid "," stype "," tok "," bit "]"
stype ::= "\"pyr\"" | "\"pri\"" | "\"cube\"" | "\"box\""
bit ::= "0" | "1"
cid ::= [0-9] | [1-9][0-9]
tok ::= "\"" [A-Za-z0-9'.°√/*+-]{1,24} "\""
relitem ::= relbaseq | relbasenq | reltript | relpair | relptsrc | relptpair | relptqty | relqty | relpairqty | relvtxqty
relbaseq ::= "{\"c\":" cid ",\"p\":" pbaseq ",\"a\":" tok (",\"q\":" tok)? "}"
pbaseq ::= "\"reg_poly\"" | "\"rhom\""
relbasenq ::= "{\"c\":" cid ",\"p\":" pbasenq ",\"a\":" tok (",\"b\":" tok)? "}"
pbasenq ::= "\"rect\"" | "\"para\"" | "\"trap\"" | "\"iso_trap\""
reltript ::= "{\"c\":" cid ",\"p\":" ptript ",\"a\":" tok ",\"pt\":" tok "}"
ptript ::= "\"right_tri\"" | "\"right_iso_tri\"" | "\"iso_tri\""
relpair ::= "{\"c\":" cid ",\"p\":" ppair ",\"a\":" tok ",\"b\":" tok "}"
ppair ::= "\"perp_lp\"" | "\"perp_ll\"" | "\"face_perp\"" | "\"eq_len\""
relptsrc ::= "{\"c\":" cid ",\"p\":" pptsrc ",\"pt\":" tok ",\"a\":" tok "}"
pptsrc ::= "\"mid\"" | "\"cent\""
relptpair ::= "{\"c\":" cid ",\"p\":" pptpair ",\"pt\":" tok ",\"a\":" tok ",\"b\":" tok "}"
pptpair ::= "\"proj\"" | "\"alt\"" | "\"inter_ll\"" | "\"inter_lp\""
relptqty ::= "{\"c\":" cid ",\"p\":\"div\",\"pt\":" tok ",\"a\":" tok ",\"q\":" tok "}"
relqty ::= "{\"c\":" cid ",\"p\":" pqty ",\"a\":" tok ",\"q\":" tok "}"
pqty ::= "\"len\"" | "\"height\"" | "\"area\"" | "\"vol\""
relpairqty ::= "{\"c\":" cid ",\"p\":" ppairqty ",\"a\":" tok ",\"b\":" tok ",\"q\":" tok "}"
ppairqty ::= "\"ang_lp\"" | "\"ang_pp\"" | "\"dihed\"" | "\"ang_ll\"" | "\"ratio\""
relvtxqty ::= "{\"c\":" cid ",\"p\":\"ang_vtx\",\"a\":" tok ",\"pt\":" tok ",\"q\":" tok "}"
rellist ::= "" | relitem ("," relitem)*
goalitem ::= goalvol | goaldistptpl | goaldistptln | goaldistll | goallen | goalarea | goalanglp | goalangpp | goalangll | goallratio | goalaratio
goalvol ::= "{\"c\":" cid ",\"t\":\"vol\",\"tgt\":" tok "}"
goaldistptpl ::= "{\"c\":" cid ",\"t\":\"dist_pt_plane\",\"a\":" tok ",\"b\":" tok "}"
goaldistptln ::= "{\"c\":" cid ",\"t\":\"dist_pt_line\",\"a\":" tok ",\"b\":" tok "}"
goaldistll ::= "{\"c\":" cid ",\"t\":\"dist_line_line\",\"a\":" tok ",\"b\":" tok "}"
goallen ::= "{\"c\":" cid ",\"t\":\"len\",\"a\":" tok "}"
goalarea ::= "{\"c\":" cid ",\"t\":\"area\",\"a\":" tok "}"
goalanglp ::= "{\"c\":" cid ",\"t\":\"ang_lp\",\"a\":" tok ",\"b\":" tok "}"
goalangpp ::= "{\"c\":" cid ",\"t\":\"ang_pp\",\"a\":" tok ",\"b\":" tok "}"
goalangll ::= "{\"c\":" cid ",\"t\":\"ang_ll\",\"a\":" tok ",\"b\":" tok "}"
goallratio ::= "{\"c\":" cid ",\"t\":\"lratio\",\"a\":" tok ",\"b\":" tok "}"
goalaratio ::= "{\"c\":" cid ",\"t\":\"aratio\",\"a\":" tok ",\"b\":" tok "}"
goallist ::= "" | goalitem ("," goalitem)*
unresitem ::= "{\"c\":" cid ",\"k\":" ukind "}"
ukind ::= "\"ambig\"" | "\"missing\"" | "\"unsup\"" | "\"contra\""
unreslist ::= "" | unresitem ("," unresitem)*
"""


def _gbnf_str_literal(val: str) -> str:
    esc = val.replace("\\", "\\\\").replace('"', '\\"')
    return f'"\\"{esc}\\""'


def _gbnf_union(items: list[str]) -> str:
    seen: list[str] = []
    for x in items:
        if x not in seen:
            seen.append(x)
    return " | ".join(_gbnf_str_literal(x) for x in seen)


def build_compact_grammar_for_context(
    ctx: "CompactClauseContext",
    *,
    clause_subset: list[IndexedClause] | None = None,
    closure_mode: str = DEFAULT_CLOSURE_MODE,
) -> str:
    """Build a per-problem, clause-scoped, arity-safe whitespace-free GBNF grammar over exact source literals."""
    use_v7 = closure_mode != "v6"
    use_v9 = closure_mode == V9_CLOSURE_MODE
    active_clauses = clause_subset if clause_subset is not None else ctx.clauses
    target_cids = [str(c.clause_id) for c in active_clauses]
    target_cid_set = {c.clause_id for c in active_clauses}
    cid_rule = " | ".join(f'"{c}"' for c in target_cids) or '"0"'

    all_solids = [e for e in ctx.entities if e.kind == "solid"]
    base_polys_from_solids: list[str] = []
    top_polys_from_solids: list[str] = []
    for se in all_solids:
        left_s, right_s = se.label.split(".", 1)
        base_lbl = right_s if se.solid_subtype == "pyr" else left_s
        if base_lbl and base_lbl not in base_polys_from_solids:
            base_polys_from_solids.append(base_lbl)
        if se.solid_subtype != "pyr" and right_s and right_s not in top_polys_from_solids:
            top_polys_from_solids.append(right_s)

    lines: list[str] = [
        f"cid ::= {cid_rule}",
        'bit ::= "0" | "1"',
    ]

    # 1. Anchor each extracted solid to its valid clause_ids and deterministic subtype
    solid_rule_names: list[str] = []
    for idx_s, se in enumerate(all_solids):
        scids = [str(c) for c in se.clause_ids if c in target_cid_set]
        if not scids:
            continue
        scid_rule = " | ".join(f'"{c}"' for c in scids)
        stype_val = se.solid_subtype if se.solid_subtype in ("pyr", "pri", "cube", "box") else "pyr"
        bit_rule = '"1"' if (se.is_regular_solid or stype_val in ("cube", "box")) else '"0"'
        rname = f"solid{idx_s}"
        lines.append(
            rf'{rname} ::= "[" ({scid_rule}) "," {_gbnf_str_literal(stype_val)} "," {_gbnf_str_literal(se.label)} "," {bit_rule} "]"'
        )
        solid_rule_names.append(rname)

    if solid_rule_names:
        lines.append("solidreq ::= " + " | ".join(solid_rule_names))
        lines.append('solidval ::= "null" | solidreq')
    else:
        lines.append('solidval ::= "null"')

    # 2. Clause-local relation rules (relc{cid})
    poly_verts_len = {e.label: len(e.vertices) for e in ctx.entities if e.kind == "poly"}

    rel_clause_rules: list[str] = []
    for cl in active_clauses:
        cid = cl.clause_id
        clow = cl.text.lower()
        # Exclude pure question clauses from relation rules (enforced by GOAL_CLAUSE_USED_AS_PREMISE)
        if _PURE_QUESTION_RE.match(cl.text) and not _PREMISE_MARKERS_IN_CLAUSE_RE.search(clow):
            continue

        c_polys: list[str] = []
        for e in ctx.entities:
            if e.kind != "poly" or cid not in e.clause_ids:
                continue
            # Only include base polygons in a clause if explicitly referenced outside solid notation, "đáy" is present, or v9 cube/box clause
            allow_implicit_solid_base = (
                "đáy" in clow
                or (use_v9 and ("lập phương" in clow or "hộp chữ nhật" in clow))
            )
            if e.label in top_polys_from_solids:
                if not re.search(rf"(?<![A-Z0-9'.]){re.escape(e.label)}(?![A-Z0-9'])", cl.text) and not any(
                    w in clow for w in ("hai đáy", "mặt trên", "đáy trên")
                ):
                    continue
            if e.label in base_polys_from_solids and not allow_implicit_solid_base:
                if not re.search(rf"(?<![A-Z0-9'.]){re.escape(e.label)}(?![A-Z0-9'])", cl.text):
                    continue
            if e.label not in c_polys:
                c_polys.append(e.label)
        if "đáy" in clow or (use_v9 and ("lập phương" in clow or "hộp chữ nhật" in clow)):
            for bp in base_polys_from_solids:
                if bp not in c_polys:
                    c_polys.append(bp)

        c_tris = [p for p in c_polys if poly_verts_len.get(p, 3) == 3]
        c_quads = [p for p in c_polys if poly_verts_len.get(p, 3) >= 4]
        c_segs = [e.label for e in ctx.entities if e.kind == "seg" and cid in e.clause_ids]
        c_pts = [e.label for e in ctx.entities if e.kind == "point" and cid in e.clause_ids]
        c_len_qtys = [q.raw_token for q in ctx.quantities if cid in q.clause_ids and q.implied_unit == ""]
        c_ratio_qtys = [
            q.raw_token
            for q in ctx.quantities
            if cid in q.clause_ids and q.implied_unit == "" and "a" not in q.canon_expr.lower()
        ]
        c_ang_qtys = [
            q.raw_token
            for q in ctx.quantities
            if cid in q.clause_ids and q.implied_unit in ("deg", "sin", "cos", "tan", "cot")
        ]
        c_reg_pyr = [
            e.label
            for e in all_solids
            if (
                (e.is_regular_solid and e.solid_subtype == "pyr" and ("cạnh bên" in clow or "tứ diện đều" in clow or cid in e.clause_ids))
                or (use_v9 and any(w in clow for w in ("tất cả các cạnh", "tất cả cạnh", "mọi cạnh")))
            )
        ]
        c_len_tgts = list(dict.fromkeys(c_segs if c_segs else c_reg_pyr))
        c_solids = [e.label for e in all_solids if cid in e.clause_ids] or [e.label for e in all_solids]

        pfx = f"rc{cid}"
        if c_polys:
            lines.append(f"{pfx}poly ::= {_gbnf_union(c_polys)}")
        if c_tris:
            lines.append(f"{pfx}tri ::= {_gbnf_union(c_tris)}")
        if c_quads:
            lines.append(f"{pfx}quad ::= {_gbnf_union(c_quads)}")
        if c_segs:
            lines.append(f"{pfx}seg ::= {_gbnf_union(c_segs)}")
        if c_pts:
            lines.append(f"{pfx}pt ::= {_gbnf_union(c_pts)}")
        if c_len_qtys:
            lines.append(f"{pfx}lqty ::= {_gbnf_union(c_len_qtys)}")
        if c_ratio_qtys:
            lines.append(f"{pfx}rqty ::= {_gbnf_union(c_ratio_qtys)}")
        if c_ang_qtys:
            lines.append(f"{pfx}aqty ::= {_gbnf_union(c_ang_qtys)}")
        if c_len_tgts:
            lines.append(f"{pfx}lentgt ::= {_gbnf_union(c_len_tgts)}")
        if c_solids:
            lines.append(f"{pfx}sol ::= {_gbnf_union(c_solids)}")

        def _cue(v5_kind: str) -> bool:
            return any(c in clow for c in _PREDICATE_LEXICAL_CUES[v5_kind])

        ang_spans = [
            sp
            for sp in re.split(r"[,;]", cl.text)
            if re.search(r"(?<!vuông\s)\bgóc\b|\b(?:sin|cos|tan|cot)\b|°", sp.lower())
        ]

        def _span_has_poly(sp: str) -> bool:
            return bool(
                any(re.search(rf"(?<![A-Z0-9'.]){re.escape(p)}(?![A-Z0-9'])", sp) for p in c_polys)
                or ("đáy" in sp.lower() and len(c_polys) >= 1)
            )

        def _span_poly_count(sp: str) -> int:
            hits = {p for p in c_polys if re.search(rf"(?<![A-Z0-9'.]){re.escape(p)}(?![A-Z0-9'])", sp)}
            if "đáy" in sp.lower() and base_polys_from_solids:
                hits.update(p for p in base_polys_from_solids if p in c_polys)
            return len(hits)

        def _span_segs(sp: str) -> list[str]:
            return [s for s in c_segs if re.search(rf"(?<![A-Z0-9']){re.escape(s)}(?![A-Z0-9'])", sp)]

        allow_ang_lp = (
            bool(c_polys and c_segs and c_ang_qtys and _cue("line_plane_angle"))
            and (
                not ang_spans
                or any(_span_has_poly(sp) and len(_span_segs(sp)) >= 1 for sp in ang_spans)
            )
        )
        allow_ang_pp = (
            bool(len(c_polys) >= 2 and c_ang_qtys and _cue("plane_plane_angle"))
            and (
                not ang_spans
                or any(_span_poly_count(sp) >= 2 for sp in ang_spans)
            )
        )
        allow_ang_ll = (
            bool(len(c_segs) >= 2 and c_ang_qtys and _cue("line_line_angle"))
            and (
                not ang_spans
                or any(len(_span_segs(sp)) >= 2 and not _span_has_poly(sp) for sp in ang_spans)
            )
        )
        has_ratio_cue = any(w in clow for w in ("chia", "tỉ số", "tỷ số", "gấp", "nửa", "lần", "/")) or bool(
            re.search(r"\b[A-Z][0-9']*=[0-9]+\s*\*?\s*[A-Z][0-9']*\b", cl.text)
        )

        c_rels: list[str] = []
        has_sspair = False
        if c_polys:
            if _cue("regular_polygon"):
                reg_tgt = f"{pfx}poly"
                if use_v7:
                    has_quad_reg = any(w in clow for w in ("hình vuông", "tứ giác đều", "ngũ giác đều", "lục giác đều", "đa giác đều", "lập phương"))
                    has_tri_reg = "tam giác đều" in clow
                    if has_tri_reg and not has_quad_reg and c_tris:
                        reg_tgt = f"{pfx}tri"
                    elif has_quad_reg and not has_tri_reg and c_quads:
                        reg_tgt = f"{pfx}quad"
                if c_len_qtys:
                    lines.append(
                        rf'{pfx}regp ::= "{{\"c\":{cid},\"p\":\"reg_poly\",\"a\":" {reg_tgt} (",\"q\":" {pfx}lqty)? "}}"'
                    )
                else:
                    lines.append(rf'{pfx}regp ::= "{{\"c\":{cid},\"p\":\"reg_poly\",\"a\":" {reg_tgt} "}}"')
                c_rels.append(f"{pfx}regp")
            if c_quads:
                if _cue("rhombus"):
                    if c_len_qtys:
                        lines.append(
                            rf'{pfx}rhom ::= "{{\"c\":{cid},\"p\":\"rhom\",\"a\":" {pfx}quad (",\"q\":" {pfx}lqty)? "}}"'
                        )
                    else:
                        lines.append(rf'{pfx}rhom ::= "{{\"c\":{cid},\"p\":\"rhom\",\"a\":" {pfx}quad "}}"')
                    c_rels.append(f"{pfx}rhom")
                quad_kinds = [
                    name
                    for name, vkind in (("rect", "rectangle"), ("para", "parallelogram"), ("trap", "trapezoid"), ("iso_trap", "isosceles_trapezoid"))
                    if _cue(vkind)
                ]
                if quad_kinds:
                    qk_rule = " | ".join(f'"\\"{q}\\""' for q in quad_kinds)
                    if c_segs and any(q in ("trap", "iso_trap") for q in quad_kinds):
                        lines.append(
                            rf'{pfx}basenq ::= "{{\"c\":{cid},\"p\":" ({qk_rule}) ",\"a\":" {pfx}quad (",\"b\":" {pfx}seg)? "}}"'
                        )
                    else:
                        lines.append(
                            rf'{pfx}basenq ::= "{{\"c\":{cid},\"p\":" ({qk_rule}) ",\"a\":" {pfx}quad "}}"'
                        )
                    c_rels.append(f"{pfx}basenq")
            if c_tris and c_pts:
                tri_pts = [pt for pt in c_pts if any(pt in t for t in c_tris)]
                if tri_pts:
                    lines.append(f"{pfx}tript ::= {_gbnf_union(tri_pts)}")
                    tri_shapes: list[str] = []
                    if _cue("right_angle") and ("tam giác" in clow or "vuông tại" in clow or "vuông ở" in clow or "vuông cân" in clow or "90" in clow):
                        tri_shapes.append('"\\"right_tri\\""')
                        if "vuông cân" in clow:
                            tri_shapes.append('"\\"right_iso_tri\\""')
                    if _cue("equal_length") and ("cân" in clow):
                        tri_shapes.append('"\\"iso_tri\\""')
                    if tri_shapes:
                        lines.append(
                            rf'{pfx}triptr ::= "{{\"c\":{cid},\"p\":" ({" | ".join(tri_shapes)}) ",\"a\":" {pfx}tri ",\"pt\":" {pfx}tript "}}"'
                        )
                        c_rels.append(f"{pfx}triptr")
                    if _cue("centroid"):
                        lines.append(rf'{pfx}cent ::= "{{\"c\":{cid},\"p\":\"cent\",\"pt\":" {pfx}pt ",\"a\":" {pfx}tri "}}"')
                        c_rels.append(f"{pfx}cent")
                    if c_ang_qtys and _cue("vertex_angle"):
                        lines.append(
                            rf'{pfx}angvtx ::= "{{\"c\":{cid},\"p\":\"ang_vtx\",\"a\":" {pfx}tri ",\"pt\":" {pfx}tript ",\"q\":" {pfx}aqty "}}"'
                        )
                        c_rels.append(f"{pfx}angvtx")
            if len(c_polys) >= 2 and (_cue("face_perpendicular_base") or allow_ang_pp):
                if len(c_polys) <= 5:
                    pp_alts = [rf'"\"{a}\",\"b\":\"{b}\""' for a in c_polys for b in c_polys if a != b]
                    lines.append(f"{pfx}pppair ::= " + " | ".join(pp_alts))
                if _cue("face_perpendicular_base"):
                    if len(c_polys) <= 5:
                        lines.append(rf'{pfx}facep ::= "{{\"c\":{cid},\"p\":\"face_perp\",\"a\":" {pfx}pppair "}}"')
                    else:
                        lines.append(rf'{pfx}facep ::= "{{\"c\":{cid},\"p\":\"face_perp\",\"a\":" {pfx}poly ",\"b\":" {pfx}poly "}}"')
                    c_rels.append(f"{pfx}facep")
                if allow_ang_pp:
                    if len(c_polys) <= 5:
                        lines.append(rf'{pfx}angpp ::= "{{\"c\":{cid},\"p\":\"ang_pp\",\"a\":" {pfx}pppair ",\"q\":" {pfx}aqty "}}"')
                    else:
                        lines.append(rf'{pfx}angpp ::= "{{\"c\":{cid},\"p\":\"ang_pp\",\"a\":" {pfx}poly ",\"b\":" {pfx}poly ",\"q\":" {pfx}aqty "}}"')
                    c_rels.append(f"{pfx}angpp")
            if c_len_qtys and _cue("face_area"):
                lines.append(rf'{pfx}area ::= "{{\"c\":{cid},\"p\":\"area\",\"a\":" {pfx}poly ",\"q\":" {pfx}lqty "}}"')
                c_rels.append(f"{pfx}area")
            if len(c_segs) >= 2 and c_ang_qtys and _cue("dihedral_angle"):
                if len(c_segs) <= 5:
                    ss_alts = [rf'"\"{a}\",\"b\":\"{b}\""' for a in c_segs for b in c_segs if a != b]
                    lines.append(f"{pfx}sspair ::= " + " | ".join(ss_alts))
                    has_sspair = True
                    lines.append(rf'{pfx}dihed ::= "{{\"c\":{cid},\"p\":\"dihed\",\"a\":" {pfx}sspair ",\"q\":" {pfx}aqty "}}"')
                else:
                    lines.append(rf'{pfx}dihed ::= "{{\"c\":{cid},\"p\":\"dihed\",\"a\":" {pfx}seg ",\"b\":" {pfx}seg ",\"q\":" {pfx}aqty "}}"')
                c_rels.append(f"{pfx}dihed")
        if c_segs:
            perp_lp_ok = (
                any(w in clow for w in ("vuông góc", "⊥", "đường cao", "trục"))
                if use_v7
                else _cue("perpendicular_line_plane")
            )
            if c_polys and perp_lp_ok:
                lines.append(rf'{pfx}perplp ::= "{{\"c\":{cid},\"p\":\"perp_lp\",\"a\":" {pfx}seg ",\"b\":" {pfx}poly "}}"')
                c_rels.append(f"{pfx}perplp")
            if len(c_segs) >= 2:
                pair_ll_preds: list[str] = []
                if _cue("perpendicular_lines"):
                    pair_ll_preds.append('"\\"perp_ll\\""')
                if _cue("equal_length"):
                    pair_ll_preds.append('"\\"eq_len\\""')
                if pair_ll_preds:
                    if len(c_segs) <= 5:
                        if not has_sspair:
                            ss_alts = [rf'"\"{a}\",\"b\":\"{b}\""' for a in c_segs for b in c_segs if a != b]
                            lines.append(f"{pfx}sspair ::= " + " | ".join(ss_alts))
                            has_sspair = True
                        lines.append(rf'{pfx}pairll ::= "{{\"c\":{cid},\"p\":" ({" | ".join(pair_ll_preds)}) ",\"a\":" {pfx}sspair "}}"')
                    else:
                        lines.append(rf'{pfx}pairll ::= "{{\"c\":{cid},\"p\":" ({" | ".join(pair_ll_preds)}) ",\"a\":" {pfx}seg ",\"b\":" {pfx}seg "}}"')
                    c_rels.append(f"{pfx}pairll")
            if c_pts:
                if _cue("midpoint"):
                    lines.append(rf'{pfx}mid ::= "{{\"c\":{cid},\"p\":\"mid\",\"pt\":" {pfx}pt ",\"a\":" {pfx}seg "}}"')
                    c_rels.append(f"{pfx}mid")
                if use_v9 and c_tris and _cue("centroid"):
                    lines.append(rf'{pfx}cent ::= "{{\"c\":{cid},\"p\":\"cent\",\"pt\":" {pfx}pt ",\"a\":" {pfx}tri "}}"')
                    c_rels.append(f"{pfx}cent")
                if len(c_segs) >= 2 and _cue("intersect_line_line"):
                    lines.append(rf'{pfx}interll ::= "{{\"c\":{cid},\"p\":\"inter_ll\",\"pt\":" {pfx}pt ",\"a\":" {pfx}seg ",\"b\":" {pfx}seg "}}"')
                    c_rels.append(f"{pfx}interll")
                if c_polys and _cue("intersect_line_plane"):
                    lines.append(rf'{pfx}interlp ::= "{{\"c\":{cid},\"p\":\"inter_lp\",\"pt\":" {pfx}pt ",\"a\":" {pfx}seg ",\"b\":" {pfx}poly "}}"')
                    c_rels.append(f"{pfx}interlp")
                if c_ratio_qtys and has_ratio_cue:
                    lines.append(rf'{pfx}div ::= "{{\"c\":{cid},\"p\":\"div\",\"pt\":" {pfx}pt ",\"a\":" {pfx}seg ",\"q\":" {pfx}rqty "}}"')
                    c_rels.append(f"{pfx}div")
            if allow_ang_lp:
                lines.append(rf'{pfx}anglp ::= "{{\"c\":{cid},\"p\":\"ang_lp\",\"a\":" {pfx}seg ",\"b\":" {pfx}poly ",\"q\":" {pfx}aqty "}}"')
                c_rels.append(f"{pfx}anglp")
            if allow_ang_ll:
                lines.append(rf'{pfx}angll ::= "{{\"c\":{cid},\"p\":\"ang_ll\",\"a\":" {pfx}seg ",\"b\":" {pfx}seg ",\"q\":" {pfx}aqty "}}"')
                c_rels.append(f"{pfx}angll")
            if len(c_segs) >= 2 and c_ratio_qtys and has_ratio_cue:
                lines.append(rf'{pfx}ratio ::= "{{\"c\":{cid},\"p\":\"ratio\",\"a\":" {pfx}seg ",\"b\":" {pfx}seg ",\"q\":" {pfx}rqty "}}"')
                c_rels.append(f"{pfx}ratio")
        if len(c_pts) >= 2 and ("chiếu" in clow or "đường cao" in clow or "chân đường cao" in clow):
            proj_preds = []
            if "chiếu" in clow:
                proj_preds.append('"\\"proj\\""')
            if "đường cao" in clow or "chân đường cao" in clow or "vuông góc" in clow:
                proj_preds.append('"\\"alt\\""')
            if proj_preds:
                p_rule = " | ".join(proj_preds)
                if c_segs and c_polys:
                    lines.append(rf'{pfx}projtgt ::= {pfx}seg | {pfx}poly')
                    lines.append(rf'{pfx}proj ::= "{{\"c\":{cid},\"p\":" ({p_rule}) ",\"pt\":" {pfx}pt ",\"a\":" {pfx}pt ",\"b\":" {pfx}projtgt "}}"')
                    c_rels.append(f"{pfx}proj")
                elif c_segs:
                    lines.append(rf'{pfx}proj ::= "{{\"c\":{cid},\"p\":" ({p_rule}) ",\"pt\":" {pfx}pt ",\"a\":" {pfx}pt ",\"b\":" {pfx}seg "}}"')
                    c_rels.append(f"{pfx}proj")
                elif c_polys:
                    lines.append(rf'{pfx}proj ::= "{{\"c\":{cid},\"p\":" ({p_rule}) ",\"pt\":" {pfx}pt ",\"a\":" {pfx}pt ",\"b\":" {pfx}poly "}}"')
                    c_rels.append(f"{pfx}proj")
        if c_len_tgts and c_len_qtys and _cue("segment_length"):
            lines.append(rf'{pfx}len ::= "{{\"c\":{cid},\"p\":\"len\",\"a\":" {pfx}lentgt ",\"q\":" {pfx}lqty "}}"')
            c_rels.append(f"{pfx}len")
        if c_solids and c_len_qtys:
            solidq_preds: list[str] = []
            if _cue("height"):
                solidq_preds.append('"\\"height\\""')
            if _cue("solid_volume"):
                solidq_preds.append('"\\"vol\\""')
            if solidq_preds:
                lines.append(rf'{pfx}solidq ::= "{{\"c\":{cid},\"p\":" ({" | ".join(solidq_preds)}) ",\"a\":" {pfx}sol ",\"q\":" {pfx}lqty "}}"')
                c_rels.append(f"{pfx}solidq")

        if c_rels:
            lines.append(f"relc{cid} ::= " + " | ".join(c_rels))
            raw_qty_occ = len(_TOKEN_QTY_RE.findall(cl.text))
            struct_cues = sum(
                1
                for k in (
                    "regular_polygon", "rectangle", "parallelogram", "rhombus", "trapezoid",
                    "right_angle", "perpendicular_line_plane", "perpendicular_lines",
                    "face_perpendicular_base", "midpoint", "centroid", "orthogonal_projection",
                )
                if _cue(k)
            )
            k_max = min(6, max(2, raw_qty_occ + struct_cues))
            seq_expr = f"relc{cid}"
            for _ in range(k_max - 1):
                seq_expr = f'relc{cid} ("," {seq_expr})?'
            lines.append(f"rseq{cid} ::= {seq_expr}")
            rel_clause_rules.append(f"rseq{cid}")

    if rel_clause_rules:
        if len(rel_clause_rules) == 1:
            lines.append(f"rellistreq ::= {rel_clause_rules[0]}")
        else:
            lines.append(f"rtail{len(rel_clause_rules) - 1} ::= {rel_clause_rules[-1]}")
            for i in range(len(rel_clause_rules) - 2, -1, -1):
                cur_name = "rellistreq" if i == 0 else f"rtail{i}"
                nxt_name = f"rtail{i + 1}"
                lines.append(f'{cur_name} ::= {rel_clause_rules[i]} ("," {nxt_name})? | {nxt_name}')
        lines.append('rellist ::= "" | rellistreq')
    else:
        lines.append('rellist ::= ""')

    # 3. Goal-clause scoped goal rules (goalc{cid})
    marked_goal_clauses = [cl for cl in active_clauses if _GOAL_VERB_RE.search(cl.text)]
    # /11: a simulation-only source has NO goal clause (a show request is not a metric question); the root below then
    # admits facts with `g:[]`, so the model is never forced to invent a metric goal or report the clause ambiguous.
    sim_only = clause_subset is None and not marked_goal_clauses and is_simulation_only_source(ctx)
    if clause_subset is None and not marked_goal_clauses and not sim_only:
        marked_goal_clauses = [cl for cl in active_clauses if _GOAL_MARKERS_RE.search(cl.text)] or list(active_clauses)

    all_solid_lbls = [e.label for e in all_solids]
    all_poly_lbls = [e.label for e in ctx.entities if e.kind == "poly"]
    all_seg_lbls = [e.label for e in ctx.entities if e.kind == "seg"]
    all_pt_lbls = [e.label for e in ctx.entities if e.kind == "point"]

    goal_clause_rules: list[str] = []
    for gcl in marked_goal_clauses:
        cid = gcl.clause_id
        glow = gcl.text.lower()
        g_polys = [e.label for e in ctx.entities if e.kind == "poly" and cid in e.clause_ids]
        if "đáy" in glow or "chiều cao" in glow or "đường cao" in glow:
            for bp in base_polys_from_solids:
                if bp not in g_polys:
                    g_polys.append(bp)
        g_segs = [e.label for e in ctx.entities if e.kind == "seg" and cid in e.clause_ids]
        g_pts = [e.label for e in ctx.entities if e.kind == "point" and cid in e.clause_ids]
        if ("chiều cao" in glow or "đường cao" in glow) and not g_pts:
            g_pts = list(all_pt_lbls)
        if not (g_polys or g_segs or g_pts):
            g_polys, g_segs, g_pts = all_poly_lbls, all_seg_lbls, all_pt_lbls

        gpfx = f"gc{cid}"
        if all_solid_lbls:
            lines.append(f"{gpfx}sol ::= {_gbnf_union(all_solid_lbls)}")
        if g_polys:
            lines.append(f"{gpfx}poly ::= {_gbnf_union(g_polys)}")
        if g_segs:
            lines.append(f"{gpfx}seg ::= {_gbnf_union(g_segs)}")
        if g_pts:
            lines.append(f"{gpfx}pt ::= {_gbnf_union(g_pts)}")

        g_alts: list[str] = []
        has_dist_cue_g = any(w in glow for w in ("khoảng cách", "cách ", "k/c", "chiều cao", "đường cao"))
        if all_solid_lbls:
            lines.append(rf'{gpfx}vol ::= "{{\"c\":{cid},\"t\":\"vol\",\"tgt\":" {gpfx}sol "}}"')
            g_alts.append(f"{gpfx}vol")
        if g_pts and g_polys and (not use_v9 or has_dist_cue_g):
            lines.append(rf'{gpfx}dpp ::= "{{\"c\":{cid},\"t\":\"dist_pt_plane\",\"a\":" {gpfx}pt ",\"b\":" {gpfx}poly "}}"')
            g_alts.append(f"{gpfx}dpp")
        if g_pts and g_segs and (not use_v9 or has_dist_cue_g):
            lines.append(rf'{gpfx}dpl ::= "{{\"c\":{cid},\"t\":\"dist_pt_line\",\"a\":" {gpfx}pt ",\"b\":" {gpfx}seg "}}"')
            g_alts.append(f"{gpfx}dpl")
        if g_segs:
            if len(g_segs) >= 2:
                lines.append(rf'{gpfx}pll ::= "{{\"c\":{cid},\"t\":" ("\"dist_line_line\"" | "\"ang_ll\"" | "\"lratio\"") ",\"a\":" {gpfx}seg ",\"b\":" {gpfx}seg "}}"')
                g_alts.append(f"{gpfx}pll")
            lines.append(rf'{gpfx}len ::= "{{\"c\":{cid},\"t\":\"len\",\"a\":" {gpfx}seg "}}"')
            g_alts.append(f"{gpfx}len")
            if g_polys:
                lines.append(rf'{gpfx}alp ::= "{{\"c\":{cid},\"t\":\"ang_lp\",\"a\":" {gpfx}seg ",\"b\":" {gpfx}poly "}}"')
                g_alts.append(f"{gpfx}alp")
        if g_polys:
            lines.append(rf'{gpfx}area ::= "{{\"c\":{cid},\"t\":\"area\",\"a\":" {gpfx}poly "}}"')
            g_alts.append(f"{gpfx}area")
            if len(g_polys) >= 2:
                lines.append(rf'{gpfx}ppp ::= "{{\"c\":{cid},\"t\":" ("\"ang_pp\"" | "\"aratio\"") ",\"a\":" {gpfx}poly ",\"b\":" {gpfx}poly "}}"')
                g_alts.append(f"{gpfx}ppp")

        if g_alts:
            lines.append(f"goalc{cid} ::= " + " | ".join(g_alts))
            goal_clause_rules.append(f"goalc{cid}")

    if goal_clause_rules:
        lines.append("goalitem ::= " + " | ".join(goal_clause_rules))
        if use_v9:
            lines.append('goallistreq ::= goalitem ("," goalitem ("," goalitem ("," goalitem)?)?)?')
        else:
            lines.append('goallistreq ::= goalitem ("," goalitem)?')
        lines.append('goallist ::= "" | goallistreq')
    else:
        lines.append('goallist ::= ""')

    lines.extend([
        r'unresitem ::= "{\"c\":" cid ",\"k\":" ukind "}"',
        r'ukind ::= "\"ambig\"" | "\"missing\"" | "\"unsup\"" | "\"contra\""',
        'unresreq ::= unresitem ("," unresitem)?',
        'unreslist ::= "" | unresreq',
    ])

    if clause_subset is None:
        if solid_rule_names and sim_only:
            r_expr = "rellistreq" if rel_clause_rules else "rellist"
            # SIM_ONLY_UNRESOLVED_WITHOUT_FACTS: an unresolved item is admitted only with an EMPTY relation list (the model
            # cannot extract facts and then flag the clause by habit; unread facts are still refused by the Source Gate).
            r_unres = '""' if SIM_ONLY_UNRESOLVED_WITHOUT_FACTS else "rellist"
            lines.insert(
                0,
                rf'root ::= "{{\"s\":" solidreq ",\"r\":[" {r_expr} "],\"g\":[],\"u\":[]}}" | "{{\"s\":" solidval ",\"r\":[" {r_unres} "],\"g\":[],\"u\":[" unresreq "]}}"',
            )
        elif solid_rule_names and goal_clause_rules:
            r_expr = "rellistreq" if rel_clause_rules else "rellist"
            lines.insert(
                0,
                rf'root ::= "{{\"s\":" solidreq ",\"r\":[" {r_expr} "],\"g\":[" goallistreq "],\"u\":[]}}" | "{{\"s\":" solidval ",\"r\":[" rellist "],\"g\":[" goallist "],\"u\":[" unresreq "]}}"',
            )
        else:
            lines.insert(0, r'root ::= "{\"s\":" solidval ",\"r\":[" rellist "],\"g\":[" goallist "],\"u\":[" unresreq "]}"')
    else:
        lines.insert(0, r'root ::= "{\"s\":" solidval ",\"r\":[" rellist "],\"g\":[" goallist "],\"u\":[" unreslist "]}"')

    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class CandidateEntity:
    entity_id: int
    kind: str  # "solid" | "poly" | "seg" | "point"
    label: str
    vertices: tuple[str, ...]
    clause_ids: tuple[int, ...]
    solid_subtype: str = ""  # "pyr" | "pri" | "cube" | "box" | ""
    is_regular_solid: bool = False


@dataclass(frozen=True)
class CandidateQuantity:
    qty_id: int
    raw_token: str
    canon_expr: str
    implied_unit: str  # "" | "deg" | "rad" | "sin" | "cos" | "tan" | "cot"
    clause_ids: tuple[int, ...]


@dataclass(frozen=True)
class CompactClauseContext:
    working_text: str
    clauses: list[IndexedClause]
    entities: list[CandidateEntity]
    quantities: list[CandidateQuantity]
    local_parser_status: str
    local_parser_reason: str | None
    local_parser_payload: dict[str, Any] | None

    def format_entity_table(self) -> str:
        return " ".join(
            f"{e.entity_id}:{e.label}({e.kind[0]})" for e in self.entities
        ) or "none"

    def format_quantity_table(self) -> str:
        return " ".join(
            f"{q.qty_id}:{q.raw_token}" for q in self.quantities
        ) or "none"


def _compact_schema_sha256() -> str:
    return hashlib.sha256(COMPACT_CLAUSE_GBNF.encode("utf-8")).hexdigest()


def _detect_solid_subtype(text_low: str) -> tuple[str, bool]:
    if "lập phương" in text_low:
        return "cube", True
    if "hộp chữ nhật" in text_low:
        return "box", True
    if "lăng trụ" in text_low or "hình hộp" in text_low:
        return "pri", ("đứng" in text_low or "đều" in text_low)
    return "pyr", bool(re.search(r"chóp\s+(?:tam\s+giác\s+|tứ\s+giác\s+)?đều|tứ\s+diện\s+đều", text_low))


def _dedup_ordered_pts(seq: list[str]) -> tuple[str, ...]:
    out: list[str] = []
    for p in seq:
        if p and p not in out:
            out.append(p)
    return tuple(out)


def build_compact_clause_context(working_text: str) -> CompactClauseContext:
    """Deterministically index clauses, geometric entities (E), and quantities (Q)."""
    clauses = index_source_clauses(working_text)
    local_res = parse_geometry_problem_locally(working_text)

    entities: list[CandidateEntity] = []
    ent_key_to_idx: dict[tuple[str, str], int] = {}

    def _add_entity(
        kind: str,
        label: str,
        verts: tuple[str, ...],
        cid: int,
        *,
        solid_subtype: str = "",
        is_reg: bool = False,
    ) -> int:
        key = (kind, label)
        if key in ent_key_to_idx:
            idx = ent_key_to_idx[key]
            existing = entities[idx]
            if cid not in existing.clause_ids:
                entities[idx] = CandidateEntity(
                    entity_id=existing.entity_id,
                    kind=existing.kind,
                    label=existing.label,
                    vertices=existing.vertices,
                    clause_ids=(*existing.clause_ids, cid),
                    solid_subtype=existing.solid_subtype or solid_subtype,
                    is_regular_solid=existing.is_regular_solid or is_reg,
                )
            return idx
        idx = len(entities)
        ent_key_to_idx[key] = idx
        entities.append(
            CandidateEntity(
                entity_id=idx,
                kind=kind,
                label=label,
                vertices=verts,
                clause_ids=(cid,),
                solid_subtype=solid_subtype,
                is_regular_solid=is_reg,
            )
        )
        return idx

    # 1. Extract Entities per clause in textual order
    for cl in clauses:
        ctext = cl.text
        clow = ctext.lower()
        cid = cl.clause_id
        # 1a. Dotted solids S.ABC / ABC.A'B'C'
        for sm in _SOLID_RE.finditer(ctext):
            s_lbl = sm.group(0)
            subtype, is_reg = _detect_solid_subtype(clow)
            left, right = s_lbl.split(".", 1)
            lpts = re.findall(r"[A-Z][0-9]*'*", left)
            rpts = re.findall(r"[A-Z][0-9]*'*", right)
            if len(lpts) >= 3 and len(lpts) == len(rpts):
                if subtype == "pyr":
                    subtype = "pri"
                all_v = tuple([*lpts, *rpts])
                _add_entity("solid", s_lbl, all_v, cid, solid_subtype=subtype, is_reg=is_reg)
                _add_entity("poly", left, tuple(lpts), cid)
                _add_entity("poly", right, tuple(rpts), cid)
                # Regular/explicit cube, box, or prism with universal edge/height cues needs AA' lateral edge anchor if not explicitly named in text
                if (
                    subtype in ("cube", "box", "pri")
                    and len(lpts) >= 1
                    and len(rpts) >= 1
                    and (
                        subtype in ("cube", "box")
                        or any(w in clow for w in ("tất cả các cạnh", "tất cả cạnh", "mọi cạnh", "chiều cao", "đường cao"))
                    )
                ):
                    _add_entity("seg", f"{lpts[0]}{rpts[0]}", (lpts[0], rpts[0]), cid)
            elif len(lpts) == 1 and len(rpts) >= 3:
                all_v = tuple([*lpts, *rpts])
                _add_entity("solid", s_lbl, all_v, cid, solid_subtype="pyr", is_reg=is_reg)
                _add_entity("poly", right, tuple(rpts), cid)
                if (is_reg and _AMBIGUOUS_LATERAL_SINGLE_RE.search(clow)) or any(
                    w in clow for w in ("tất cả các cạnh", "tất cả cạnh", "mọi cạnh", "tứ diện đều")
                ):
                    _add_entity("seg", f"{lpts[0]}{rpts[0]}", (lpts[0], rpts[0]), cid)

        # 1b. Tetrahedron without dot ("tứ diện ABCD")
        for tm in re.finditer(r"tứ\s+diện(?:\s+đều)?\s+((?:[A-Z][0-9]*'*){4})\b", ctext, re.IGNORECASE | re.UNICODE):
            pts = re.findall(r"[A-Z][0-9]*'*", tm.group(1))
            if len(pts) == 4 and len(set(pts)) == 4:
                is_reg = "đều" in tm.group(0).lower()
                s_lbl = f"{pts[0]}.{''.join(pts[1:])}"
                _add_entity("solid", s_lbl, tuple(pts), cid, solid_subtype="pyr", is_reg=is_reg)
                _add_entity("poly", "".join(pts[1:]), tuple(pts[1:]), cid)
                if is_reg or any(w in clow for w in ("tất cả các cạnh", "tất cả cạnh", "mọi cạnh")):
                    _add_entity("seg", f"{pts[0]}{pts[1]}", (pts[0], pts[1]), cid)

        # 1c. Parenthesized planes (SBC), (ABCD) & named triangles / faces / angles
        for pm in re.finditer(r"\(\s*((?:[A-Z][0-9]*'*){3,6})\s*\)", ctext):
            plbl = pm.group(1)
            pts = _dedup_ordered_pts(re.findall(r"[A-Z][0-9]*'*", plbl))
            if len(pts) >= 3:
                _add_entity("poly", "".join(pts), pts, cid)

        for nm in re.finditer(
            r"\b(?:đáy|mặt\s+bên|mặt\s+phẳng|tam\s+giác|tứ\s+giác|hình\s+vuông|hình\s+chữ\s+nhật|hình\s+thoi|hình\s+bình\s+hành|hình\s+thang|góc)\s+([A-Z][0-9]*'*(?:[A-Z][0-9]*'*){2,5})(?![A-Za-zÀ-Ỹà-ỹ0-9'])",
            ctext,
            re.IGNORECASE | re.UNICODE,
        ):
            plbl = nm.group(1)
            pts = _dedup_ordered_pts(re.findall(r"[A-Z][0-9]*'*", plbl))
            if len(pts) >= 3:
                _add_entity("poly", "".join(pts), pts, cid)

        # 1d. Standalone 2-vertex segments/lines (SA, BC, AA', CD, AH, ...)
        for lm in re.finditer(r"(?<![A-Za-zÀ-Ỹà-ỹ0-9'])([A-Z][0-9]*'?)([A-Z][0-9]*'?)(?![A-Z0-9'a-zà-ỹ])", ctext):
            p1, p2 = lm.group(1), lm.group(2)
            if p1 != p2:
                _add_entity("seg", f"{p1}{p2}", (p1, p2), cid)

        # 1e. Single vertices in clause
        for vp in sorted(extract_geometry_points(ctext), key=lambda x: (ctext.find(x), x)):
            if re.fullmatch(r"[A-Z][0-9]*'*", vp):
                _add_entity("point", vp, (vp,), cid)

    # 2. Extract Quantities per clause in textual order
    quantities: list[CandidateQuantity] = []
    qty_key_to_idx: dict[tuple[str, str], int] = {}

    def _add_qty(raw_tok: str, canon_expr: str, implied_unit: str, cid: int) -> int:
        key = (raw_tok, implied_unit)
        if key in qty_key_to_idx:
            idx = qty_key_to_idx[key]
            ex = quantities[idx]
            if cid not in ex.clause_ids:
                quantities[idx] = CandidateQuantity(
                    qty_id=ex.qty_id,
                    raw_token=ex.raw_token,
                    canon_expr=ex.canon_expr,
                    implied_unit=ex.implied_unit,
                    clause_ids=(*ex.clause_ids, cid),
                )
            return idx
        idx = len(quantities)
        qty_key_to_idx[key] = idx
        quantities.append(
            CandidateQuantity(
                qty_id=idx,
                raw_token=raw_tok,
                canon_expr=canon_expr,
                implied_unit=implied_unit,
                clause_ids=(cid,),
            )
        )
        return idx

    for cl in clauses:
        ctext = cl.text
        clow = ctext.lower()
        cid = cl.clause_id
        for qm in _TOKEN_QTY_RE.finditer(ctext):
            raw_tok = qm.group(1).strip().rstrip(".,;:")
            if not raw_tok:
                continue
            eval_ok = _try_eval_qty(raw_tok)
            if eval_ok is None and not re.fullmatch(r"\d+(?:[.,]\d+)?°?", raw_tok):
                continue
            # Detect degree or trig context in window preceding match
            win = clow[max(0, qm.start() - 35): qm.start()]
            if raw_tok.endswith("°") or re.match(r"^\s*độ\b", clow[qm.end(): qm.end() + 6]):
                u = "deg"
                canon = raw_tok.rstrip("°").strip()
            elif re.search(r"\b(sin|cos|tan|cot)\b", win):
                m_trig = re.findall(r"\b(sin|cos|tan|cot)\b", win)
                u = m_trig[-1]
                canon = _canon_val(raw_tok)
            else:
                u = ""
                canon = _canon_val(raw_tok)
            _add_qty(raw_tok, canon, u, cid)

        for wphrase, mapped in _WORD_RATIO_MAP.items():
            if wphrase in clow:
                _add_qty(wphrase, mapped, "", cid)

    return CompactClauseContext(
        working_text=working_text,
        clauses=clauses,
        entities=entities,
        quantities=quantities,
        local_parser_status=local_res.status,
        local_parser_reason=local_res.reason_code,
        local_parser_payload=local_res.payload,
    )


_VALUE_ROLE_KINDS = frozenset({"regular_polygon", "rhombus", "segment_length", "height"})
_KEEP_CLAUSE_KINDS = frozenset({
    "midpoint", "centroid", "orthogonal_projection", "orthogonal_projection_line",
    "divide_segment", "intersect_line_line", "intersect_line_plane",
    "right_angle", "altitude", "face_perpendicular_base",
})


def _select_source_gate_quote(
    clause_text: str,
    required_tokens: list[str],
    working_text: str,
    kind: str,
    role_val: str | None = None,
    *,
    required_contiguous: list[str] | None = None,
    required_cues: tuple[str, ...] | None = None,
    closure_mode: str = DEFAULT_CLOSURE_MODE,
) -> str:
    """Pick a verbatim substring that respects both clause grounding and Registry `_lien_ket_cau`."""
    use_v7 = closure_mode != "v6"
    use_v9 = closure_mode == V9_CLOSURE_MODE
    req = [t for t in required_tokens if t]
    if not use_v7 and kind in _KEEP_CLAUSE_KINDS and clause_text in working_text:
        return clause_text

    # In v7, for construction/shape clauses keep tightest valid comma/sentence sub-clause containing cues + contiguous labels
    if use_v7 and kind in _KEEP_CLAUSE_KINDS and clause_text in working_text:
        if not required_contiguous and not required_cues:
            return clause_text
        return select_clean_quote(
            clause_text,
            req,
            working_text,
            required_contiguous=required_contiguous,
            required_cues=required_cues,
            closure_mode=closure_mode,
        )

    # On multi-value clauses (e.g. regular pyramid base side AND lateral edge), isolate sub-clause with fewest extra numbers
    if kind in _VALUE_ROLE_KINDS and role_val:
        pieces: list[str] = []
        for piece in re.split(r"\s*,\s*|\s+và\s+|\s+với\s+|\s+đồng\s+thời\s+", clause_text, flags=re.IGNORECASE):
            seg = piece.strip(" ,;:")
            if seg and seg in working_text:
                pieces.append(seg)
        pieces.append(clause_text)
        contig_req = (
            [lbl for lbl in (required_contiguous or ()) if lbl and _cand_has_contiguous(clause_text, lbl)]
            if use_v7
            else []
        )
        valid_cands: list[tuple[int, int, str]] = []
        for cand in pieces:
            cpts = extract_geometry_points(cand)
            tok_ok = all(
                (t in cpts or t in cand) if re.fullmatch(r"[A-Z][0-9]*'*", t) else (t.lower() in cand.lower())
                for t in req
            )
            if not tok_ok:
                continue
            if contig_req and not all(_cand_has_contiguous(cand, lbl) for lbl in contig_req):
                continue
            qty_hits = len(_TOKEN_QTY_RE.findall(cand))
            # Prefer sub-clause containing role_val uniquely (fewest numbers) and tightest length
            valid_cands.append((abs(qty_hits - 1), len(cand), cand))
        if valid_cands:
            valid_cands.sort()
            return valid_cands[0][2]

    return select_clean_quote(
        clause_text,
        req,
        working_text,
        required_contiguous=required_contiguous if use_v7 else None,
        required_cues=required_cues if use_v7 else None,
        closure_mode=closure_mode,
    )


def _expand_compact_relation(
    rel: dict[str, Any],
    ctx: CompactClauseContext,
    solid_info: dict[str, Any] | None,
    *,
    closure_mode: str = DEFAULT_CLOSURE_MODE,
) -> tuple[list[dict[str, Any]], str | None]:
    """Validate entity/quantity indices + source cues and lower into typed-fact-next/2 premises."""
    use_v7 = closure_mode != "v6"
    use_v9 = closure_mode == V9_CLOSURE_MODE
    cid = rel.get("c")
    pcode = str(rel.get("p") or "").strip()
    if pcode not in _COMPACT_TO_V5_KIND:
        return [], f"UNSUPPORTED_OP_KIND:{pcode}"
    if not isinstance(cid, int) or cid < 0 or cid >= len(ctx.clauses):
        return [], f"UNGROUNDED_CLAUSE_ID:{cid}"

    clause = ctx.clauses[cid]
    ctext = clause.text
    clow = ctext.lower()
    v5_kind = _COMPACT_TO_V5_KIND[pcode]

    # Pre-check clause-level safety invariants BEFORE expanding
    if _PURE_QUESTION_RE.match(ctext) and not _PREMISE_MARKERS_IN_CLAUSE_RE.search(clow):
        return [], f"GOAL_CLAUSE_USED_AS_PREMISE:clause_{cid}"
    if v5_kind not in _PREDICATE_NEGATION_EXEMPT and _NEGATED_PREDICATE_RE.search(clow):
        return [], f"NEGATED_PREDICATE_CLAUSE:{v5_kind}"
    if _AMBIGUOUS_LATERAL_SINGLE_RE.search(clow) and not _UNIVERSAL_LATERAL_RE.search(clow):
        if not re.findall(r"\b[A-Z][0-9]*'*[A-Z][0-9]*'*\b", ctext):
            return [], "AMBIGUOUS_REFERENCE:lateral_edge_not_unique"
    if _AMBIGUOUS_FACE_SINGLE_RE.search(clow) and "(" not in ctext:
        if not re.findall(r"\b[A-Z][0-9]*'*[A-Z][0-9]*'*[A-Z][0-9]*'*\b", ctext):
            return [], "AMBIGUOUS_REFERENCE:lateral_face_not_unique"

    def _resolve_entity(val: Any, preferred_kinds: tuple[str, ...]) -> tuple[CandidateEntity | None, str | None]:
        if val is None or val == -1 or val == "":
            return None, None
        if isinstance(val, int):
            if val < 0 or val >= len(ctx.entities):
                return None, f"OUT_OF_RANGE_ENTITY_ID:{val}"
            return ctx.entities[val], None
        sval = str(val).strip()
        for pk in preferred_kinds:
            for e in ctx.entities:
                if e.kind == pk and e.label == sval:
                    return e, None
        for e in ctx.entities:
            if e.label == sval:
                return e, None
        return None, f"OUT_OF_RANGE_ENTITY_LABEL:{sval}"

    _KIND_BY_SLOT: dict[tuple[str, str], tuple[str, ...]] = {
        ("reg_poly", "a"): ("poly",), ("rhom", "a"): ("poly",),
        ("rect", "a"): ("poly",), ("para", "a"): ("poly",),
        ("trap", "a"): ("poly",), ("trap", "b"): ("seg",),
        ("iso_trap", "a"): ("poly",), ("iso_trap", "b"): ("seg",),
        ("right_tri", "a"): ("poly",), ("right_tri", "pt"): ("point",),
        ("right_iso_tri", "a"): ("poly",), ("right_iso_tri", "pt"): ("point",),
        ("iso_tri", "a"): ("poly",), ("iso_tri", "pt"): ("point",),
        ("perp_lp", "a"): ("seg",), ("perp_lp", "b"): ("poly",),
        ("perp_ll", "a"): ("seg",), ("perp_ll", "b"): ("seg",),
        ("face_perp", "a"): ("poly",), ("face_perp", "b"): ("poly",),
        ("mid", "pt"): ("point",), ("mid", "a"): ("seg",),
        ("cent", "pt"): ("point",), ("cent", "a"): ("poly",),
        ("proj", "pt"): ("point",), ("proj", "a"): ("point",), ("proj", "b"): ("seg", "poly"),
        ("alt", "pt"): ("point",), ("alt", "a"): ("point",), ("alt", "b"): ("seg", "poly"),
        ("inter_ll", "pt"): ("point",), ("inter_ll", "a"): ("seg",), ("inter_ll", "b"): ("seg",),
        ("inter_lp", "pt"): ("point",), ("inter_lp", "a"): ("seg",), ("inter_lp", "b"): ("poly",),
        ("div", "pt"): ("point",), ("div", "a"): ("seg",),
        ("len", "a"): ("seg", "solid"),
        ("eq_len", "a"): ("seg",), ("eq_len", "b"): ("seg",),
        ("height", "a"): ("solid", "seg"),
        ("ang_lp", "a"): ("seg",), ("ang_lp", "b"): ("poly",),
        ("ang_pp", "a"): ("poly",), ("ang_pp", "b"): ("poly",),
        ("dihed", "a"): ("seg", "point"), ("dihed", "b"): ("seg",),
        ("ang_ll", "a"): ("seg",), ("ang_ll", "b"): ("seg",),
        ("ang_vtx", "a"): ("poly",), ("ang_vtx", "pt"): ("point",),
        ("area", "a"): ("poly",), ("vol", "a"): ("solid",),
        ("ratio", "a"): ("seg",), ("ratio", "b"): ("seg",),
    }

    ea, err = _resolve_entity(rel.get("a"), _KIND_BY_SLOT.get((pcode, "a"), ("seg", "poly", "point", "solid")))
    if err:
        return [], err
    eb, err = _resolve_entity(rel.get("b"), _KIND_BY_SLOT.get((pcode, "b"), ("poly", "seg", "point")))
    if err:
        return [], err
    ept, err = _resolve_entity(rel.get("pt"), _KIND_BY_SLOT.get((pcode, "pt"), ("point",)))
    if err:
        return [], err

    qty_entry: CandidateQuantity | None = None
    q_ref = rel.get("q")
    if q_ref is not None and q_ref != -1 and q_ref != "":
        if isinstance(q_ref, int):
            if q_ref < 0 or q_ref >= len(ctx.quantities):
                return [], f"OUT_OF_RANGE_QTY_ID:q={q_ref}"
            qty_entry = ctx.quantities[q_ref]
        else:
            qs = str(q_ref).strip()
            for qe in ctx.quantities:
                if qe.raw_token == qs or qe.canon_expr == qs:
                    qty_entry = qe
                    break
            if qty_entry is None:
                return [], f"OUT_OF_RANGE_QTY_LABEL:q={qs}"
        ok_q, _ = is_value_grounded_in_clause(qty_entry.raw_token, ctext, allow_unit_default_a=True)
        if not ok_q:
            return [], f"UNGROUNDED_VALUE:{v5_kind}:{qty_entry.canon_expr}"

    cues = _PREDICATE_LEXICAL_CUES[v5_kind]
    if not any(cue in clow for cue in cues):
        return [], f"PREDICATE_CUE_MISSING:{v5_kind}"

    # Verify all referenced entity points appear grounded in working text / base context
    cpts = extract_geometry_points(ctext)
    bpts = set(_solid_base_vertices(solid_info))
    all_pts = extract_geometry_points(ctx.working_text)
    is_reg_cube_or_lat = bool(
        solid_info
        and (
            (
                solid_info.get("_is_reg")
                and (
                    "cạnh bên" in clow
                    or "lập phương" in ctx.working_text.lower()
                    or (use_v7 and "tứ diện đều" in ctx.working_text.lower())
                )
            )
            or (use_v9 and any(w in clow for w in ("tất cả các cạnh", "tất cả cạnh", "mọi cạnh")))
            or (use_v9 and solid_info.get("solid_type") == "prism" and any(w in clow for w in ("chiều cao", "đường cao", "lập phương", "hộp chữ nhật")))
        )
    )
    for ent in (ea, eb, ept):
        if ent is None:
            continue
        for pt in ent.vertices:
            if pt not in all_pts:
                return [], f"UNGROUNDED_POINT:{pt}"
            in_base_indirect = ("đáy" in clow or "mặt đáy" in clow) and pt in bpts
            if pt not in cpts and not in_base_indirect:
                poly_is_implicit_base = ent.kind == "poly" and set(ent.vertices) == bpts and "đáy" in clow
                if not (ent.kind == "solid" and solid_info is not None) and not poly_is_implicit_base and not (is_reg_cube_or_lat and ent.kind == "seg"):
                    return [], f"UNGROUNDED_POINT:{pt}"

    sid = solid_info["solid_id"] if solid_info is not None else "s1"
    out_premises: list[dict[str, Any]] = []

    def _pts(e: CandidateEntity | None) -> list[str]:
        return list(e.vertices) if e is not None else []

    def _poly_contig(pts: list[str]) -> list[str]:
        return ["".join(pts)] if use_v7 and len(pts) >= 3 else []

    if pcode == "reg_poly":
        verts = _pts(ea)
        if len(verts) < 3:
            return [], "INVALID_PREMISE_ARGS:regular_polygon"
        if use_v7 and len(verts) >= 4 and "tam giác đều" in clow and not any(
            w in clow for w in ("hình vuông", "tứ giác đều", "ngũ giác đều", "lục giác đều", "đa giác đều", "lập phương")
        ):
            return [], "INVALID_PREMISE_ARGS:regular_polygon_vertex_count_mismatch"
        args: dict[str, Any] = {"vertices": verts}
        req = list(verts)
        rv: str | None = None
        if qty_entry is not None:
            args["side"] = qty_entry.canon_expr
            req.append(qty_entry.canon_expr)
            rv = qty_entry.canon_expr
        q_str = _select_source_gate_quote(
            ctext, req, ctx.working_text, "regular_polygon", role_val=rv,
            required_contiguous=_poly_contig(verts),
            required_cues=("đều", "hình vuông", "lập phương", "tứ diện đều") if use_v7 else None,
            closure_mode=closure_mode,
        )
        out_premises.append({"kind": "regular_polygon", "args": args, "quote": q_str, "solid_id": sid})

    elif pcode in ("rect", "para"):
        verts = _pts(ea)
        if len(verts) != 4:
            return [], f"INVALID_PREMISE_ARGS:{v5_kind}"
        q_str = _select_source_gate_quote(
            ctext, verts, ctx.working_text, v5_kind,
            required_contiguous=_poly_contig(verts),
            required_cues=(("chữ nhật", "hcn") if pcode == "rect" else ("bình hành", "hbh")) if use_v7 else None,
            closure_mode=closure_mode,
        )
        out_premises.append({"kind": v5_kind, "args": {"vertices": verts}, "quote": q_str, "solid_id": sid})

    elif pcode == "rhom":
        verts = _pts(ea)
        if len(verts) != 4:
            return [], "INVALID_PREMISE_ARGS:rhombus"
        args = {"vertices": verts}
        req = list(verts)
        rv = None
        if qty_entry is not None:
            args["side"] = qty_entry.canon_expr
            req.append(qty_entry.canon_expr)
            rv = qty_entry.canon_expr
        q_str = _select_source_gate_quote(
            ctext, req, ctx.working_text, "rhombus", role_val=rv,
            required_contiguous=_poly_contig(verts),
            required_cues=("hình thoi",) if use_v7 else None,
            closure_mode=closure_mode,
        )
        out_premises.append({"kind": "rhombus", "args": args, "quote": q_str, "solid_id": sid})

    elif pcode in ("trap", "iso_trap"):
        verts, base_a = _pts(ea), _pts(eb)
        if len(verts) != 4 or len(base_a) != 2:
            return [], f"INVALID_PREMISE_ARGS:{v5_kind}"
        rem = [v for v in verts if v not in base_a]
        if len(rem) != 2:
            return [], f"INVALID_PREMISE_ARGS:{v5_kind}"
        q_str = _select_source_gate_quote(
            ctext, verts, ctx.working_text, v5_kind,
            required_contiguous=_poly_contig(verts),
            required_cues=("hình thang",) if use_v7 else None,
            closure_mode=closure_mode,
        )
        out_premises.append({"kind": v5_kind, "args": {"vertices": verts, "base_a": base_a, "base_b": rem}, "quote": q_str, "solid_id": sid})

    elif pcode in ("right_tri", "right_iso_tri"):
        poly_pts = _pts(ea)
        vtx = _pts(ept)[0] if ept and len(ept.vertices) == 1 else ""
        if not vtx or len(poly_pts) != 3 or vtx not in poly_pts:
            return [], f"INVALID_PREMISE_ARGS:{pcode}"
        rays = [x for x in poly_pts if x != vtx]
        # /11 (Q10 of /10): "vuông" alone let the shortest piece "SA vuông góc với (ABC)" win over "đáy ABC là tam giác
        # vuông tại A"; when the clause states the right angle AT the vertex, the quote must contain that statement.
        at_vtx = tuple(f"vuông{c} {w} {vtx}" for c in ("", " cân") for w in ("tại", "ở"))
        cues = at_vtx if any(c.lower() in clow for c in at_vtx) else ("vuông", "90")
        q_str = _select_source_gate_quote(
            ctext, poly_pts, ctx.working_text, "right_angle",
            required_contiguous=_poly_contig(poly_pts),
            required_cues=cues if use_v7 else None,
            closure_mode=closure_mode,
        )
        out_premises.append({"kind": "right_angle", "args": {"vertex": vtx, "rays": rays}, "quote": q_str, "solid_id": sid})
        if pcode == "right_iso_tri" or "vuông cân" in clow:
            out_premises.append({"kind": "equal_length", "args": {"segment_a": [vtx, rays[0]], "segment_b": [vtx, rays[1]]}, "quote": q_str, "solid_id": sid})

    elif pcode == "iso_tri":
        poly_pts = _pts(ea)
        vtx = _pts(ept)[0] if ept and len(ept.vertices) == 1 else ""
        if not vtx or len(poly_pts) != 3 or vtx not in poly_pts:
            return [], "INVALID_PREMISE_ARGS:iso_tri"
        rays = [x for x in poly_pts if x != vtx]
        q_str = _select_source_gate_quote(
            ctext, poly_pts, ctx.working_text, "equal_length",
            required_contiguous=_poly_contig(poly_pts),
            required_cues=("cân",) if use_v7 else None,
            closure_mode=closure_mode,
        )
        out_premises.append({"kind": "equal_length", "args": {"segment_a": [vtx, rays[0]], "segment_b": [vtx, rays[1]]}, "quote": q_str, "solid_id": sid})

    elif pcode == "perp_lp":
        line = _pts(ea)
        plane = _pts(eb) if eb is not None else _solid_base_vertices(solid_info)
        if len(plane) < 3 and "đáy" in clow:
            plane = _solid_base_vertices(solid_info)
        if len(line) != 2 or len(plane) < 3:
            return [], "INVALID_PREMISE_ARGS:perpendicular_line_plane"
        # In v7, filter out spurious right-prism lateral-edge perp_lp when clause has no explicit "vuông góc"/"⊥"
        if use_v7 and not any(w in clow for w in ("vuông góc", "⊥", "đường cao")):
            if set(line).issubset(set(plane)):
                return [], "INVALID_PREMISE_ARGS:line_lies_in_plane"
            if solid_info and solid_info.get("solid_type") == "prism" and any(w in clow for w in ("đứng", "đều", "hộp chữ nhật", "lập phương")):
                return [], "PREDICATE_CUE_MISSING:perpendicular_line_plane"
        q_str = _select_source_gate_quote(
            ctext, [*line, *plane], ctx.working_text, "perpendicular_line_plane",
            required_contiguous=["".join(line)] if use_v7 else None,
            required_cues=("vuông góc", "⊥", "đường cao") if use_v7 else None,
            closure_mode=closure_mode,
        )
        out_premises.append({"kind": "perpendicular_line_plane", "args": {"line": line, "plane": plane}, "quote": q_str, "solid_id": sid})

    elif pcode == "perp_ll":
        l1, l2 = _pts(ea), _pts(eb)
        if len(l1) != 2 or len(l2) != 2:
            return [], "INVALID_PREMISE_ARGS:perpendicular_lines"
        q_str = _select_source_gate_quote(
            ctext, [*l1, *l2], ctx.working_text, "perpendicular_lines",
            required_contiguous=["".join(l1), "".join(l2)] if use_v7 else None,
            required_cues=("vuông góc", "⊥") if use_v7 else None,
            closure_mode=closure_mode,
        )
        out_premises.append({"kind": "perpendicular_lines", "args": {"line1": l1, "line2": l2}, "quote": q_str, "solid_id": sid})

    elif pcode == "face_perp":
        face = _pts(ea)
        base = _pts(eb) if eb is not None else _solid_base_vertices(solid_info)
        if len(base) < 3 and "đáy" in clow:
            base = _solid_base_vertices(solid_info)
        if len(face) < 3 or len(base) < 3:
            return [], "INVALID_PREMISE_ARGS:face_perpendicular_base"
        q_str = _select_source_gate_quote(
            ctext, [*face, *base], ctx.working_text, "face_perpendicular_base",
            required_contiguous=_poly_contig(face),
            required_cues=("vuông góc", "⊥") if use_v7 else None,
            closure_mode=closure_mode,
        )
        out_premises.append({"kind": "face_perpendicular_base", "args": {"face": face, "base": base}, "quote": q_str, "solid_id": sid})

    elif pcode == "mid":
        pt = _pts(ept)[0] if ept and len(ept.vertices) == 1 else ""
        seg = _pts(ea)
        if not pt or len(seg) != 2:
            return [], "INVALID_PREMISE_ARGS:midpoint"
        if pt in seg:
            return [], "INVALID_PREMISE_ARGS:endpoint_cannot_divide_segment"
        q_str = _select_source_gate_quote(
            ctext, [pt, *seg], ctx.working_text, "midpoint",
            required_contiguous=["".join(seg)] if use_v7 else None,
            required_cues=("trung điểm", "chính giữa") if use_v7 else None,
            closure_mode=closure_mode,
        )
        out_premises.append({"kind": "midpoint", "args": {"point": pt, "segment": seg}, "quote": q_str, "solid_id": sid})

    elif pcode == "cent":
        pt = _pts(ept)[0] if ept and len(ept.vertices) == 1 else ""
        poly = _pts(ea)
        if not pt or len(poly) < 3:
            return [], "INVALID_PREMISE_ARGS:centroid"
        q_str = _select_source_gate_quote(
            ctext, [pt, *poly], ctx.working_text, "centroid",
            required_contiguous=_poly_contig(poly),
            required_cues=("trọng tâm",) if use_v7 else None,
            closure_mode=closure_mode,
        )
        out_premises.append({"kind": "centroid", "args": {"point": pt, "polygon": poly}, "quote": q_str, "solid_id": sid})

    elif pcode in ("proj", "alt"):
        img = _pts(ept)[0] if ept and len(ept.vertices) == 1 else ""
        src_p = _pts(ea)[0] if ea and len(ea.vertices) == 1 else ""
        tgt = _pts(eb)
        if not img or not src_p:
            return [], f"INVALID_PREMISE_ARGS:{pcode}"
        if len(tgt) == 2:
            q_str = _select_source_gate_quote(
                ctext, [src_p, img, *tgt], ctx.working_text, "orthogonal_projection_line",
                required_contiguous=["".join(tgt)] if use_v7 else None,
                required_cues=("chiếu", "đường cao") if use_v7 else None,
                closure_mode=closure_mode,
            )
            out_premises.append({"kind": "orthogonal_projection_line", "args": {"point": src_p, "image": img, "line": tgt}, "quote": q_str, "solid_id": sid})
        elif len(tgt) >= 3:
            q_str = _select_source_gate_quote(
                ctext, [src_p, img, *tgt], ctx.working_text, "orthogonal_projection",
                required_contiguous=_poly_contig(tgt),
                required_cues=("chiếu", "đường cao") if use_v7 else None,
                closure_mode=closure_mode,
            )
            out_premises.append({"kind": "orthogonal_projection", "args": {"point": src_p, "image": img, "plane": tgt}, "quote": q_str, "solid_id": sid})
        elif "đáy" in clow and len(bverts := _solid_base_vertices(solid_info)) >= 3:
            q_str = _select_source_gate_quote(
                ctext, [src_p, img], ctx.working_text, "orthogonal_projection",
                required_cues=("chiếu", "đường cao") if use_v7 else None,
                closure_mode=closure_mode,
            )
            out_premises.append({"kind": "orthogonal_projection", "args": {"point": src_p, "image": img, "plane": bverts}, "quote": q_str, "solid_id": sid})
        else:
            return [], f"INVALID_PREMISE_ARGS:{pcode}"

    elif pcode == "inter_ll":
        pt = _pts(ept)[0] if ept and len(ept.vertices) == 1 else ""
        l1, l2 = _pts(ea), _pts(eb)
        if not pt or len(l1) != 2 or len(l2) != 2:
            return [], "INVALID_PREMISE_ARGS:intersect_line_line"
        q_str = _select_source_gate_quote(ctext, [pt, *l1, *l2], ctx.working_text, "intersect_line_line")
        out_premises.append({"kind": "intersect_line_line", "args": {"point": pt, "line1": l1, "line2": l2}, "quote": q_str, "solid_id": sid})

    elif pcode == "inter_lp":
        pt = _pts(ept)[0] if ept and len(ept.vertices) == 1 else ""
        line, plane = _pts(ea), _pts(eb)
        if not pt or len(line) != 2 or len(plane) < 3:
            return [], "INVALID_PREMISE_ARGS:intersect_line_plane"
        q_str = _select_source_gate_quote(ctext, [pt, *line, *plane], ctx.working_text, "intersect_line_plane")
        out_premises.append({"kind": "intersect_line_plane", "args": {"point": pt, "line": line, "plane": plane}, "quote": q_str, "solid_id": sid})

    elif pcode == "div":
        pt = _pts(ept)[0] if ept and len(ept.vertices) == 1 else ""
        seg = _pts(ea)
        if not pt or len(seg) != 2 or qty_entry is None:
            return [], "INVALID_PREMISE_ARGS:divide_segment"
        if pt in seg:
            return [], "INVALID_PREMISE_ARGS:endpoint_cannot_divide_segment"
        q_str = _select_source_gate_quote(ctext, [pt, *seg, qty_entry.canon_expr], ctx.working_text, "divide_segment")
        out_premises.append({"kind": "divide_segment", "args": {"point": pt, "segment": seg, "ratio": qty_entry.canon_expr}, "quote": q_str, "solid_id": sid})

    elif pcode == "len":
        seg = _pts(ea)
        if qty_entry is None:
            return [], "INVALID_PREMISE_ARGS:segment_length"
        is_all_edges_cl = use_v9 and any(w in clow for w in ("tất cả các cạnh", "tất cả cạnh", "mọi cạnh"))
        is_reg_lat = bool(solid_info and solid_info.get("_is_reg") and "cạnh bên" in clow)
        is_reg_tet_all = bool(use_v7 and solid_info and (solid_info.get("_is_reg") and "tứ diện đều" in clow or (is_all_edges_cl and solid_info["solid_type"] == "pyramid")))
        if is_all_edges_cl and solid_info and solid_info.get("solid_type") == "prism" and "." in str(solid_info.get("notation") or ""):
            bverts = _solid_base_vertices(solid_info)
            tverts = _parse_solid_vertices("prism", solid_info["notation"])[len(bverts):]
            q_pri_all = ctext if (ctext in ctx.working_text and solid_info["notation"] in ctext) else solid_info.get("quote") or ctext
            if q_pri_all not in ctx.working_text or qty_entry.canon_expr not in q_pri_all:
                q_pri_all = select_clean_quote(ctext, [*bverts, qty_entry.canon_expr], ctx.working_text, closure_mode=closure_mode)
            out_premises.append({"kind": "regular_polygon", "args": {"vertices": bverts, "side": qty_entry.canon_expr}, "quote": q_pri_all, "solid_id": sid})
            out_premises.append({"kind": "segment_length", "args": {"segment": [bverts[0], tverts[0]], "value": qty_entry.canon_expr}, "quote": q_pri_all, "solid_id": sid})
            return out_premises, None
        if len(seg) != 2:
            # Allow solid entity for regular pyramid lateral edge ("cạnh bên bằng 2a"), regular tetrahedron, or all-edges-equal
            if ea is not None and ea.kind == "solid" and solid_info and solid_info["solid_type"] == "pyramid" and (solid_info.get("_is_reg") or is_all_edges_cl):
                apex = solid_info["notation"].split(".", 1)[0]
                bverts = _solid_base_vertices(solid_info)
                seg = [apex, bverts[0]]
                if is_reg_tet_all:
                    q_tet = ctext if ctext in ctx.working_text else _select_source_gate_quote(ctext, [*bverts, qty_entry.canon_expr], ctx.working_text, "regular_polygon", role_val=qty_entry.canon_expr, closure_mode=closure_mode)
                    out_premises.append({"kind": "regular_polygon", "args": {"vertices": bverts, "side": qty_entry.canon_expr}, "quote": q_tet, "solid_id": sid})
                    out_premises.append({"kind": "segment_length", "args": {"segment": seg, "value": qty_entry.canon_expr}, "quote": q_tet, "solid_id": sid})
                    return out_premises, None
            else:
                return [], "INVALID_PREMISE_ARGS:segment_length"
        else:
            seg_ab, seg_ba = f"{seg[0]}{seg[1]}", f"{seg[1]}{seg[0]}"
            is_v9_cube_side = bool(
                use_v9
                and solid_info is not None
                and "lập phương" in clow
                and "cạnh" in clow
                and qty_entry.canon_expr in ctext
                and set(seg).issubset(set(_parse_solid_vertices("prism", solid_info["notation"])))
            )
            if is_v9_cube_side and seg_ab not in ctext and seg_ba not in ctext:
                q_cube = solid_info["quote"] if solid_info.get("quote") else ctext
                b_verts = _solid_base_vertices(solid_info)
                out_premises.append({"kind": "regular_polygon", "args": {"vertices": b_verts, "side": qty_entry.canon_expr}, "quote": q_cube, "solid_id": sid})
                out_premises.append({"kind": "segment_length", "args": {"segment": seg, "value": qty_entry.canon_expr}, "quote": q_cube, "solid_id": sid})
                return out_premises, None
            if (
                use_v9
                and solid_info is not None
                and solid_info.get("solid_type") == "prism"
                and ("chiều cao" in clow or "đường cao" in clow)
                and seg_ab not in ctext
                and seg_ba not in ctext
                and qty_entry.canon_expr in ctext
                and set(seg).issubset(set(_parse_solid_vertices("prism", solid_info["notation"])))
            ):
                q_h = _select_source_gate_quote(
                    ctext, [qty_entry.canon_expr], ctx.working_text, "height",
                    role_val=qty_entry.canon_expr, required_cues=("chiều cao", "đường cao"), closure_mode=closure_mode,
                )
                out_premises.append({"kind": "height", "args": {"solid": sid, "value": qty_entry.canon_expr}, "quote": q_h, "solid_id": sid})
                return out_premises, None
            if is_all_edges_cl and solid_info and solid_info.get("solid_type") == "pyramid" and seg_ab not in ctext and seg_ba not in ctext and qty_entry.canon_expr in ctext:
                apex = solid_info["notation"].split(".", 1)[0]
                bverts = _solid_base_vertices(solid_info)
                q_tet = ctext if (ctext in ctx.working_text and solid_info["notation"] in ctext) else _select_source_gate_quote(ctext, [*bverts, qty_entry.canon_expr], ctx.working_text, "regular_polygon", role_val=qty_entry.canon_expr, closure_mode=closure_mode)
                out_premises.append({"kind": "regular_polygon", "args": {"vertices": bverts, "side": qty_entry.canon_expr}, "quote": q_tet, "solid_id": sid})
                out_premises.append({"kind": "segment_length", "args": {"segment": [apex, bverts[0]], "value": qty_entry.canon_expr}, "quote": q_tet, "solid_id": sid})
                return out_premises, None
            if not is_reg_lat and seg_ab not in ctext and seg_ba not in ctext:
                return [], f"UNGROUNDED_SEGMENT_PAIR:{seg_ab}"
            if not is_reg_lat:
                esc_s = rf"(?:{re.escape(seg_ab)}|{re.escape(seg_ba)})"
                m_eq = re.search(rf"(?<![A-Z0-9']){esc_s}(?![A-Z0-9'])\s*=\s*([^\s,.;!?]+)", ctext)
                if m_eq:
                    rhs = m_eq.group(1)
                    if not re.fullmatch(r"(?:[A-Z][0-9']*'?){2,}", rhs) and _canon_val(rhs) != qty_entry.canon_expr:
                        return [], f"UNGROUNDED_VALUE:segment_length_conflict:{seg_ab}:{rhs}!={qty_entry.canon_expr}"
                esc_v = re.escape(qty_entry.canon_expr)
                # Check within comma/conjunction sub-clauses first to avoid binding across adjacent segments
                pieces_v = [p.strip() for p in re.split(r"[,;]|\bvà\b|\bđồng\s+thời\b", ctext, flags=re.IGNORECASE) if p.strip()]
                seg_pat = re.compile(rf"(?<![A-Z0-9']){esc_s}(?![A-Z0-9'])")
                val_pat = re.compile(rf"(?<![A-Za-z0-9]){esc_v}(?![A-Za-z0-9√/])")
                same_piece_ok = any(seg_pat.search(p) and val_pat.search(p) for p in pieces_v)
                if not same_piece_ok:
                    # Allow explicit shared list ("AB, AC cùng bằng a") or long subject clause ("đường cao SA ... có độ dài a√3")
                    between_pat = re.compile(
                        rf"(?<![A-Z0-9']){esc_s}(?![A-Z0-9'])[^.;!?=]{{0,64}}(?:=|bằng|(?:có\s+)?(?:độ\s+)?dài(?:\s*(?:=|bằng|là))?)\s*{esc_v}(?![A-Za-z0-9√/])",
                        re.IGNORECASE | re.UNICODE,
                    )
                    if not between_pat.search(ctext):
                        return [], f"UNGROUNDED_VALUE:segment_length_proximity:{seg_ab}:{qty_entry.canon_expr}"
        req_len = ["cạnh bên", qty_entry.canon_expr] if is_reg_lat else [*seg, qty_entry.canon_expr]
        q_str = _select_source_gate_quote(
            ctext, req_len, ctx.working_text, "segment_length", role_val=qty_entry.canon_expr,
            required_contiguous=(None if (is_reg_lat or not use_v7) else ["".join(seg)]),
            closure_mode=closure_mode,
        )
        out_premises.append({"kind": "segment_length", "args": {"segment": seg, "value": qty_entry.canon_expr}, "quote": q_str, "solid_id": sid})

    elif pcode == "eq_len":
        s1, s2 = _pts(ea), _pts(eb)
        if len(s1) != 2 or len(s2) != 2:
            return [], "INVALID_PREMISE_ARGS:equal_length"
        q_str = _select_source_gate_quote(ctext, [*s1, *s2], ctx.working_text, "equal_length", closure_mode=closure_mode)
        out_premises.append({"kind": "equal_length", "args": {"segment_a": s1, "segment_b": s2}, "quote": q_str, "solid_id": sid})

    elif pcode == "height":
        if qty_entry is None:
            return [], "INVALID_PREMISE_ARGS:height"
        q_str = _select_source_gate_quote(
            ctext,
            [qty_entry.canon_expr],
            ctx.working_text,
            "height",
            role_val=qty_entry.canon_expr,
            required_cues=("chiều cao", "đường cao") if use_v9 else None,
            closure_mode=closure_mode,
        )
        out_premises.append({"kind": "height", "args": {"solid": sid, "value": qty_entry.canon_expr}, "quote": q_str, "solid_id": sid})

    elif pcode in ("ang_lp", "ang_pp", "dihed", "ang_ll", "ang_vtx"):
        if qty_entry is None:
            return [], f"INVALID_PREMISE_ARGS:{v5_kind}"
        val_str = qty_entry.canon_expr.rstrip("°")
        unit_str = qty_entry.implied_unit or ("deg" if "°" in qty_entry.raw_token or "độ" in clow else "")
        a_pts = _pts(ea)
        b_pts = _pts(eb)
        contig_ang: list[str] | None = None
        if pcode == "ang_lp":
            if len(b_pts) < 3 and "đáy" in clow:
                b_pts = _solid_base_vertices(solid_info)
            if len(a_pts) != 2 or len(b_pts) < 3:
                return [], "INVALID_PREMISE_ARGS:line_plane_angle"
            args = {"line": a_pts, "plane": b_pts, "value": val_str}
            req = [*a_pts, *b_pts, val_str]
            contig_ang = ["".join(a_pts)] if use_v7 else None
        elif pcode == "ang_pp":
            if len(b_pts) < 3 and "đáy" in clow:
                b_pts = _solid_base_vertices(solid_info)
            if len(a_pts) < 3 or len(b_pts) < 3:
                return [], "INVALID_PREMISE_ARGS:plane_plane_angle"
            args = {"plane1": a_pts, "plane2": b_pts, "value": val_str}
            req = [*a_pts, *b_pts, val_str]
            contig_ang = [x for x in ("".join(a_pts), "".join(b_pts)) if _cand_has_contiguous(ctext, x)] if use_v7 else None
        elif pcode == "dihed":
            if len(a_pts) < 2 or len(b_pts) != 2:
                return [], "INVALID_PREMISE_ARGS:dihedral_angle"
            args = {"point_a": a_pts[0], "edge": b_pts, "point_b": a_pts[1], "value": val_str}
            req = [*a_pts[:2], *b_pts, val_str]
        elif pcode == "ang_ll":
            if len(a_pts) != 2 or len(b_pts) != 2:
                return [], "INVALID_PREMISE_ARGS:line_line_angle"
            args = {"line1": a_pts, "line2": b_pts, "value": val_str}
            req = [*a_pts, *b_pts, val_str]
            contig_ang = ["".join(a_pts), "".join(b_pts)] if use_v7 else None
        else:
            vtx = _pts(ept)[0] if ept and len(ept.vertices) == 1 else (a_pts[1] if len(a_pts) == 3 else "")
            rays = [x for x in a_pts if x != vtx][:2]
            if not vtx or len(rays) != 2:
                return [], "INVALID_PREMISE_ARGS:vertex_angle"
            args = {"vertex": vtx, "rays": rays, "value": val_str}
            req = [vtx, *rays, val_str]
        if unit_str:
            args["unit"] = unit_str
        q_str = _select_source_gate_quote(
            ctext, req, ctx.working_text, v5_kind,
            required_contiguous=contig_ang,
            required_cues=("góc", "°", "sin", "cos", "tan", "cot") if use_v7 else None,
            closure_mode=closure_mode,
        )
        out_premises.append({"kind": v5_kind, "args": args, "quote": q_str, "solid_id": sid})

    elif pcode == "area":
        poly = _pts(ea)
        if len(poly) < 3 or qty_entry is None:
            return [], "INVALID_PREMISE_ARGS:face_area"
        q_str = _select_source_gate_quote(ctext, [*poly, qty_entry.canon_expr], ctx.working_text, "face_area")
        out_premises.append({"kind": "face_area", "args": {"polygon": poly, "value": qty_entry.canon_expr}, "quote": q_str, "solid_id": sid})

    elif pcode == "vol":
        if qty_entry is None:
            return [], "INVALID_PREMISE_ARGS:solid_volume"
        q_str = _select_source_gate_quote(ctext, [qty_entry.canon_expr], ctx.working_text, "solid_volume")
        out_premises.append({"kind": "solid_volume", "args": {"value": qty_entry.canon_expr}, "quote": q_str, "solid_id": sid})

    elif pcode == "ratio":
        s1, s2 = _pts(ea), _pts(eb)
        if len(s1) != 2 or len(s2) != 2 or qty_entry is None:
            return [], "INVALID_PREMISE_ARGS:segment_ratio"
        q_str = _select_source_gate_quote(ctext, [*s1, *s2, qty_entry.canon_expr], ctx.working_text, "segment_ratio")
        out_premises.append({"kind": "segment_ratio", "args": {"segment_a": s1, "segment_b": s2, "ratio": qty_entry.canon_expr}, "quote": q_str, "solid_id": sid})

    return out_premises, None


def _convert_compact_goal(
    goal: dict[str, Any],
    idx: int,
    ctx: CompactClauseContext,
    solid_info: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, str | None]:
    cid = goal.get("c")
    gcode = str(goal.get("t") or "").strip()
    v5_gtype = _COMPACT_GOAL_CODES.get(gcode)
    if v5_gtype is None:
        return None, f"UNSUPPORTED_GOAL_TYPE:{gcode}"

    ordered_goal_clauses: list[IndexedClause] = []
    if isinstance(cid, int) and 0 <= cid < len(ctx.clauses):
        ordered_goal_clauses.append(ctx.clauses[cid])
    for cl in ctx.clauses:
        if cl not in ordered_goal_clauses and _GOAL_MARKERS_RE.search(cl.text):
            ordered_goal_clauses.append(cl)
    if not ordered_goal_clauses:
        return None, f"UNGROUNDED_GOAL_CLAUSE_ID:{cid}"

    def _ent_pts(slot: str, preferred_kinds: tuple[str, ...]) -> tuple[list[str], str | None]:
        raw_val = goal.get(slot)
        if raw_val is None or raw_val == -1 or raw_val == "":
            return [], None
        if isinstance(raw_val, int):
            if raw_val < 0 or raw_val >= len(ctx.entities):
                return [], f"OUT_OF_RANGE_GOAL_ENTITY:{slot}={raw_val}"
            return list(ctx.entities[raw_val].vertices), None
        sval = str(raw_val).strip()
        for pk in preferred_kinds:
            for e in ctx.entities:
                if e.kind == pk and e.label == sval:
                    return list(e.vertices), None
        for e in ctx.entities:
            if e.label == sval:
                return list(e.vertices), None
        return [], f"OUT_OF_RANGE_GOAL_ENTITY:{slot}={sval}"

    pref_a: tuple[str, ...] = ("solid", "point", "seg", "poly")
    pref_b: tuple[str, ...] = ("poly", "seg", "point")
    if gcode in ("ang_pp", "area", "aratio"):
        pref_a = ("poly", "seg", "point")
        pref_b = ("poly", "seg", "point")
    elif gcode in ("len", "ang_ll", "dist_line_line", "lratio"):
        pref_a = ("seg", "poly", "point")
        pref_b = ("seg", "poly", "point")
    elif gcode in ("ang_lp", "dist_line_plane"):
        pref_a = ("seg", "poly", "point")
        pref_b = ("poly", "seg", "point")
    elif gcode in ("dist_pt_plane", "dist_pt_line"):
        pref_a = ("point", "seg", "poly")

    ga, err_a = _ent_pts("tgt" if gcode == "vol" else "a", pref_a)
    if err_a:
        return None, err_a
    gb, err_b = _ent_pts("b", pref_b)
    if err_b:
        return None, err_b

    req_pts = [*ga, *gb]
    # For solid volume / full-solid area, req_pts may be empty or solid vertices
    if gcode == "vol":
        req_pts = []
    is_solid_height_goal = bool(
        gcode == "dist_pt_plane"
        and len(ga) == 1
        and len(gb) >= 3
        and solid_info
        and solid_info.get("solid_type") == "pyramid"
        and "." in str(solid_info.get("notation") or "")
        and ga[0] == str(solid_info["notation"]).split(".", 1)[0]
        and set(gb) <= set(_solid_base_vertices(solid_info))
    )
    ctext = ""
    matched_cid: int | None = None
    for gcl in ordered_goal_clauses:
        if not _GOAL_MARKERS_RE.search(gcl.text):
            continue
        gcl_pts = extract_geometry_points(gcl.text)
        gcl_low = gcl.text.lower()
        if gcode == "vol" and "thể tích" not in gcl_low and not re.search(r"\bv\s*[_(\[]", gcl_low):
            continue
        if not req_pts or all(rp in gcl_pts for rp in req_pts):
            ctext = gcl.text
            matched_cid = gcl.clause_id
            break
        if is_solid_height_goal and ("chiều cao" in gcl_low or "đường cao" in gcl_low):
            ctext = gcl.text
            matched_cid = gcl.clause_id
            gb = gb[:3]
            break
    if not ctext or matched_cid is None:
        return None, f"UNGROUNDED_GOAL_CLAUSE_TOKENS:{v5_gtype}"

    # Reuse _convert_goal target mapping cleanly by building normalized dict
    goal_proxy: dict[str, Any] = {
        "clause_id": matched_cid,
        "goal_type": v5_gtype,
        "a": ga,
        "b": gb,
    }
    return _convert_goal(goal_proxy, idx, ctx.clauses, ctx.working_text, solid_info, extract_geometry_points(ctx.working_text))


def _premise_dedup_key(prem: dict[str, Any]) -> tuple[Any, ...]:
    """Canonical signature so set-equivalent segment/polygon vertices don't duplicate."""
    kind = str(prem.get("kind") or "")
    args = prem.get("args") or {}
    norm_items: list[tuple[str, Any]] = []
    for k in sorted(args.keys()):
        v = args[k]
        if k in ("vertices", "base", "top", "segment", "segment_a", "segment_b", "line", "line1", "line2", "plane", "plane1", "plane2", "face", "polygon", "rays") and isinstance(v, list):
            norm_items.append((k, tuple(sorted(str(x).strip().upper() for x in v))))
        elif k in ("value", "side", "ratio", "distance"):
            norm_items.append((k, _normalize_scalar_str(str(v or ""))))
        else:
            norm_items.append((k, str(v).strip().upper() if isinstance(v, str) else str(v)))
    return (kind, tuple(norm_items))


def simulation_request_span(clauses: list[IndexedClause], working_text: str) -> tuple[int, int] | None:
    """Span in `working_text` of the show request (rule 7b grammar or nested lead-in verb + solid head)."""
    for cl in clauses:
        m = _SIM_REQUEST_RE.match(cl.text)
        if m is not None:
            sim = m.group("sim").strip()
            p = working_text.find(sim, cl.start)
            if p >= 0:
                return p, p + len(sim)
        if m_lead := SIMULATION_LEAD_VERB_RE.match(cl.text):
            tail = cl.text[m_lead.end():]
            if m_head := _EMBEDDED_SOLID_HEAD_RE.match(tail):
                rel_a = len(cl.text) - len(cl.text.lstrip())
                rel_b = m_lead.end() + m_head.end("head")
                return cl.start + rel_a, cl.start + rel_b
    return None


def is_simulation_only_source(ctx: "CompactClauseContext") -> bool:
    """/12: simulation-only check strips leading/trailing meta_no_calc clauses and supports nested simulation lead-ins."""
    if any(_GOAL_VERB_RE.search(cl.text) for cl in ctx.clauses):
        return False
    comp = analyze_compositional_geometry(ctx.working_text)
    if comp.is_simulation_only_intent:
        return True
    return simulation_request_span(ctx.clauses, ctx.working_text) is not None


def count_expected_source_goals(ctx: "CompactClauseContext") -> int:
    """Count distinct explicit goal clauses in `ctx`."""
    solid_cids = {c for e in ctx.entities if e.kind == "solid" for c in e.clause_ids}
    count = 0
    for cl in ctx.clauses:
        if not _STRICT_GOAL_ASK_RE.search(cl.text):
            continue
        # Only count clause containing the solid declaration if it genuinely has a question mark or trailing ask outside premise
        if cl.clause_id in solid_cids and not _PURE_QUESTION_RE.match(cl.text) and "?" not in cl.text and not re.search(r"\b(?:tính|tìm|bao\s+nhiêu|bằng\s+mấy)\b", cl.text, re.I):
            continue
        count += 1
    return count


def classify_multi_goal_status(
    expected_goal_count: int,
    grounded_goals: list[dict[str, Any]],
    unresolved_items: list[dict[str, Any]] | None = None,
) -> str:
    """Classify multi-goal completeness cleanly without silent partial-drop serving."""
    if expected_goal_count <= 1:
        return "COMPLETE_SINGLE_GOAL" if len(grounded_goals) >= 1 else "INCOMPLETE_EXTRACTION_REFUSED"
    if len(grounded_goals) >= expected_goal_count:
        return "COMPLETE_MULTI_GOAL"
    if unresolved_items:
        return "PARTIAL_UNSUPPORTED_SUBGOAL_REFUSED"
    return "INCOMPLETE_EXTRACTION_REFUSED"


def validate_and_lower_compact_clause(
    *,
    ctx: CompactClauseContext,
    raw_slm_json: dict[str, Any],
    closure_mode: str = DEFAULT_CLOSURE_MODE,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Deterministically validate compact slot-filled SLM output and lower to `typed-fact-next/2`."""
    use_v7 = closure_mode != "v6"
    use_v9 = closure_mode == V9_CLOSURE_MODE
    val_ver = SLM_GROUNDING_VALIDATOR_V9_VERSION if use_v9 else SLM_GROUNDING_VALIDATOR_VERSION
    if not isinstance(raw_slm_json, dict):
        return None, {
            "validator_version": val_ver,
            "grounding_status": "REJECTED_INVALID_COMPACT_OP",
            "reason_code": "INVALID_JSON_TYPE",
            "failure_taxonomy": "GROUNDING_REJECTED",
            "accepted_ops": [],
            "rejected_ops": [{"op": "root", "reason": f"EXPECTED_DICT_GOT:{type(raw_slm_json).__name__}"}],
        }
    accepted_ops: list[dict[str, Any]] = []
    rejected_ops: list[dict[str, str]] = []

    raw_unresolved = raw_slm_json.get("u") or []
    unresolved_items: list[dict[str, Any]] = []
    for item in raw_unresolved:
        if not isinstance(item, dict):
            continue
        cid = item.get("c")
        uk = _COMPACT_UNRES_CODES.get(str(item.get("k") or "ambig"), "ambiguous")
        excerpt = ctx.clauses[cid].text if isinstance(cid, int) and 0 <= cid < len(ctx.clauses) else ctx.working_text
        unresolved_items.append({"kind": uk, "excerpt": excerpt, "reason": f"SLM marked clause {cid} as {uk}."})

    if unresolved_items:
        has_contra = any(u["kind"] == "contradictory" for u in unresolved_items)
        reason_code = "INCONSISTENT_FACTS" if has_contra else "AMBIGUOUS_FACT"
        if any(u["kind"] == "unsupported" for u in unresolved_items) and len(unresolved_items) == 1:
            reason_code = "OUT_OF_SCOPE"
        return None, {
            "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
            "grounding_status": "SLM_REPORTED_UNRESOLVED",
            "reason_code": reason_code,
            "failure_taxonomy": "CONTRADICTION_OR_UNGROUNDED" if has_contra else "SLM_UNRESOLVED",
            "accepted_ops": [],
            "rejected_ops": [{"op": "unresolved", "reason": u["reason"]} for u in unresolved_items],
            "unresolved": unresolved_items,
        }

    # 1. Validate solid slot [cid, stype, eid_or_label, reg]
    solid_raw = raw_slm_json.get("s")
    solid_info: dict[str, Any] | None = None
    solids_list: list[dict[str, Any]] = []
    solid_quote = ""
    solid_subtype = ""
    solid_reg_bit = 0

    if isinstance(solid_raw, list) and len(solid_raw) >= 4:
        scid, stype_code, sref, reg_bit = solid_raw[0], str(solid_raw[1]), solid_raw[2], int(solid_raw[3])
        s_ent: CandidateEntity | None = None
        if isinstance(sref, int) and 0 <= sref < len(ctx.entities):
            s_ent = ctx.entities[sref]
        elif isinstance(sref, str):
            s_ent = next((e for e in ctx.entities if e.kind == "solid" and e.label == sref.strip()), None)
        if isinstance(scid, int) and 0 <= scid < len(ctx.clauses) and s_ent is not None:
            v5_stype = "pyramid" if stype_code == "pyr" else "prism"
            if s_ent.kind == "solid" and _parse_solid_vertices(v5_stype, s_ent.label):
                ctext_s = ctx.clauses[scid].text
                cpts_s = extract_geometry_points(ctext_s)
                if all(v in cpts_s for v in s_ent.vertices):
                    # Preserve solid quote up through its solid symbol/qualifier
                    if use_v7:
                        s_cues = (
                            ("lăng trụ đứng", "lăng trụ đều", "hộp chữ nhật", "lập phương", "lăng trụ", "hộp")
                            if v5_stype == "prism"
                            else ("tứ diện đều", "chóp", "tứ diện")
                        )
                        m_tight_sol = re.search(
                            rf"(?:(?:hình|khối)\s+)?(?:chóp|lăng\s+trụ|hộp(?:\s+chữ\s+nhật)?|lập\s+phương|tứ\s+diện)"
                            rf"(?:\s+(?:đứng|đều|xiên|tam\s+giác|tứ\s+giác|ngũ\s+giác|lục\s+giác|chữ\s+nhật))*"
                            rf"\s+{re.escape(s_ent.label)}(?![A-Z0-9'])",
                            ctext_s,
                            re.IGNORECASE,
                        )
                        if m_tight_sol and m_tight_sol.group(0) in ctx.working_text:
                            solid_quote = m_tight_sol.group(0)
                        else:
                            solid_quote = select_clean_quote(
                                ctext_s,
                                list(s_ent.vertices),
                                ctx.working_text,
                                required_contiguous=[s_ent.label] if s_ent.label in ctext_s else None,
                                required_cues=s_cues,
                                closure_mode=closure_mode,
                            )
                    else:
                        solid_quote = select_clean_quote(ctext_s, list(s_ent.vertices), ctx.working_text, closure_mode=closure_mode)
                    if stype_code == "cube" and ctext_s in ctx.working_text:
                        solid_quote = ctext_s
                    solid_subtype = stype_code
                    solid_reg_bit = reg_bit
                    solid_info = {
                        "solid_id": "s1",
                        "solid_type": v5_stype,
                        "notation": s_ent.label,
                        "quote": solid_quote,
                        "_is_reg": bool(reg_bit or s_ent.is_regular_solid),
                    }
                    solids_list.append({
                        "solid_id": "s1",
                        "solid_type": v5_stype,
                        "notation": s_ent.label,
                        "quote": solid_quote,
                    })
                else:
                    rejected_ops.append({"op": "solid", "reason": f"UNGROUNDED_SOLID_VERTICES:{s_ent.label}"})
            else:
                rejected_ops.append({"op": "solid", "reason": f"INVALID_SOLID_ENTITY:{sref}"})
        else:
            rejected_ops.append({"op": "solid", "reason": f"OUT_OF_RANGE_SOLID_REF:{solid_raw}"})

    if not solids_list or solid_info is None:
        return None, {
            "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
            "grounding_status": "REJECTED_MISSING_OR_INVALID_SOLID",
            "reason_code": "MISSING_DIMENSION" if not rejected_ops else "SOURCE_OBJECT_MISMATCH",
            "failure_taxonomy": "GROUNDING_REJECTED",
            "accepted_ops": [],
            "rejected_ops": rejected_ops or [{"op": "solid", "reason": "NO_GROUNDED_SOLID"}],
        }

    # Check Local Parser vs SLM solid conflict
    if ctx.local_parser_payload and ctx.local_parser_payload.get("solids"):
        lp_solid = ctx.local_parser_payload["solids"][0]
        if lp_solid.get("notation") and lp_solid.get("notation") != solid_info["notation"]:
            return None, {
                "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
                "grounding_status": "REJECTED_PARSER_SLM_CONFLICT",
                "reason_code": "PARSER_SLM_CONFLICT",
                "failure_taxonomy": "PARSER_SLM_CONFLICT",
                "accepted_ops": [],
                "rejected_ops": [{"op": "solid", "reason": f"CONFLICT_LOCAL={lp_solid.get('notation')}_SLM={solid_info['notation']}"}],
            }

    premises: list[dict[str, Any]] = []
    ctext_s = ctx.clauses[solid_raw[0]].text
    cs_low = ctext_s.lower()
    if solid_info["solid_type"] == "pyramid" and _detect_solid_subtype(cs_low)[1]:
        apex = solid_info["notation"].split(".", 1)[0]
        base = _solid_base_vertices(solid_info)
        premises.append({"kind": "regular_pyramid", "args": {"apex": apex, "base": base}, "quote": solid_quote, "solid_id": "s1"})
        accepted_ops.append({"kind": "regular_pyramid", "clause_id": solid_raw[0]})
        if use_v7 and "tứ diện đều" in cs_low and "cạnh" in cs_low:
            c_q_tet = [q for q in ctx.quantities if solid_raw[0] in q.clause_ids and q.implied_unit == ""]
            if len(c_q_tet) == 1 and not _NEGATED_PREDICATE_RE.search(cs_low):
                side_val = c_q_tet[0].canon_expr
                premises.append({"kind": "regular_polygon", "args": {"vertices": base, "side": side_val}, "quote": ctext_s, "solid_id": "s1"})
                premises.append({"kind": "segment_length", "args": {"segment": [apex, base[0]], "value": side_val}, "quote": ctext_s, "solid_id": "s1"})
                accepted_ops.append({"kind": "tetrahedron_expansion", "clause_id": solid_raw[0]})
    elif solid_info["solid_type"] == "prism" and re.search(
        r"lăng\s+trụ\s+(?:tam\s+giác\s+|tứ\s+giác\s+)?đều|lăng\s+trụ\s+đứng|lập\s+phương|hộp\s+chữ\s+nhật",
        cs_low,
    ):
        left_s, right_s = solid_info["notation"].split(".", 1)
        b_verts = re.findall(r"[A-Z][0-9]*'*", left_s)
        t_verts = re.findall(r"[A-Z][0-9]*'*", right_s)
        premises.append({"kind": "right_prism", "args": {"base": b_verts, "top": t_verts}, "quote": solid_quote, "solid_id": "s1"})
        accepted_ops.append({"kind": "right_prism", "clause_id": solid_raw[0]})
        if solid_subtype == "box" or "hộp chữ nhật" in cs_low:
            premises.append({"kind": "rectangle", "args": {"vertices": b_verts}, "quote": solid_quote, "solid_id": "s1"})
            accepted_ops.append({"kind": "rectangle", "clause_id": solid_raw[0]})
        if solid_subtype == "cube" or "lập phương" in cs_low:
            # Find side length quantity in solid clause if any
            c_q = [q for q in ctx.quantities if solid_raw[0] in q.clause_ids]
            if len(c_q) == 1:
                side_val = c_q[0].canon_expr
                premises.append({"kind": "regular_polygon", "args": {"vertices": b_verts, "side": side_val}, "quote": ctext_s, "solid_id": "s1"})
                premises.append({"kind": "segment_length", "args": {"segment": [b_verts[0], t_verts[0]], "value": side_val}, "quote": ctext_s, "solid_id": "s1"})
                accepted_ops.append({"kind": "cube_expansion", "clause_id": solid_raw[0]})

    # 2. Expand relations deterministically
    lp_lengths = _local_parser_segment_lengths(ctx.local_parser_payload)
    for rel in raw_slm_json.get("r") or ():
        if not isinstance(rel, dict):
            continue
        expanded, err = _expand_compact_relation(rel, ctx, solid_info, closure_mode=closure_mode)
        if err is not None:
            rejected_ops.append({"op": str(rel.get("p") or "unknown"), "reason": err})
            if err.startswith("AMBIGUOUS_REFERENCE"):
                return None, {
                    "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
                    "grounding_status": "REJECTED_AMBIGUOUS_REFERENCE",
                    "reason_code": "AMBIGUOUS_REFERENCE",
                    "failure_taxonomy": "AMBIGUOUS_REFERENCE",
                    "accepted_ops": accepted_ops,
                    "rejected_ops": rejected_ops,
                }
            if err.startswith("NEGATED_PREDICATE_CLAUSE"):
                return None, {
                    "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
                    "grounding_status": "REJECTED_NEGATED_FACT",
                    "reason_code": "INCONSISTENT_FACTS",
                    "failure_taxonomy": "GROUNDING_REJECTED",
                    "accepted_ops": accepted_ops,
                    "rejected_ops": rejected_ops,
                }
            if err.startswith(("OUT_OF_RANGE_", "UNGROUNDED_")):
                return None, {
                    "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
                    "grounding_status": "REJECTED_UNGROUNDED_TOKEN",
                    "reason_code": "UNGROUNDED_VALUE",
                    "failure_taxonomy": "GROUNDING_REJECTED",
                    "accepted_ops": accepted_ops,
                    "rejected_ops": rejected_ops,
                }
            continue
        for prem in expanded:
            if prem["kind"] == "segment_length":
                seg_fs = frozenset(prem["args"]["segment"])
                slm_norm_val = _normalize_scalar_str(str(prem["args"]["value"]))
                if seg_fs in lp_lengths and lp_lengths[seg_fs] != slm_norm_val:
                    return None, {
                        "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
                        "grounding_status": "REJECTED_PARSER_SLM_CONFLICT",
                        "reason_code": "PARSER_SLM_CONFLICT",
                        "failure_taxonomy": "PARSER_SLM_CONFLICT",
                        "accepted_ops": accepted_ops,
                        "rejected_ops": [*rejected_ops, {"op": "segment_length", "reason": f"CONFLICT_LOCAL={lp_lengths[seg_fs]}_SLM={slm_norm_val}"}],
                    }
            if not any(ep["kind"] == prem["kind"] and ep["args"] == prem["args"] for ep in premises):
                premises.append(prem)
                accepted_ops.append({"kind": prem["kind"], "clause_id": rel.get("c")})

    # Reconcile verified Local Parser premises from normalized working text when full parse succeeded cleanly (`v7`)
    if use_v7 and ctx.local_parser_status == LOCAL_PARSE_COMPLETE and ctx.local_parser_payload and not rejected_ops and not raw_slm_json.get("u"):
        lp_prems = [dict(p) for p in (ctx.local_parser_payload.get("premises") or ()) if isinstance(p, dict)]
        lp_keys = {_premise_dedup_key(p) for p in lp_prems}
        if lp_prems and not _CONDITIONAL_MARKER_RE.search(ctx.working_text) and not _NEGATED_SPAN_RE.search(ctx.working_text):
            parsed_lp_qtys: set[str] = set()
            for lp_p in lp_prems:
                largs = lp_p.get("args") or {}
                for qk in ("side", "value", "ratio", "distance"):
                    if largs.get(qk) is not None:
                        ev = _try_eval_qty(str(largs[qk]))
                        if ev is not None:
                            parsed_lp_qtys.add(ev)
            unconsumed_lp = any(
                (ev := _try_eval_qty(qm.group(1))) is not None and ev not in parsed_lp_qtys
                for qm in _TOKEN_QTY_RE.finditer(ctx.working_text)
            )
            if not unconsumed_lp:
                # Local Parser completely parsed every clause with 0 unconsumed quantities:
                # adopt its Source-Gate-aligned quotes for all parsed kinds, while preserving any
                # non-overlapping valid SLM premise kinds (e.g. right_angle/equal_length on compound face_perp clauses)
                # unless Local Parser already covers the entire clause set.
                lp_kinds = {str(p.get("kind") or "") for p in lp_prems}
                kept_extra: list[dict[str, Any]] = []
                seen_extra: set[tuple[Any, ...]] = set(lp_keys)
                for ep in premises:
                    ek = _premise_dedup_key(ep)
                    ekind = str(ep.get("kind") or "")
                    if ekind not in lp_kinds and ek not in seen_extra:
                        kept_extra.append(ep)
                        seen_extra.add(ek)
                premises = [*lp_prems, *kept_extra]
                accepted_ops = [{"kind": p.get("kind"), "clause_id": "parser_reconciled"} for p in lp_prems] + [
                    {"kind": p.get("kind"), "clause_id": "slm_preserved"} for p in kept_extra
                ]
            else:
                # Upgrade matching keys to Local Parser's Source-Gate-aligned quote and append any omitted premises
                lp_by_key = {_premise_dedup_key(p): p for p in lp_prems}
                premises = [lp_by_key.get(_premise_dedup_key(ep), ep) for ep in premises]
                existing_keys = {_premise_dedup_key(ep) for ep in premises}
                for lp_k, lp_p in lp_by_key.items():
                    if lp_k not in existing_keys:
                        premises.append(lp_p)
                        existing_keys.add(lp_k)
                        accepted_ops.append({"kind": lp_p.get("kind"), "clause_id": "parser_merged"})
        else:
            existing_keys = {_premise_dedup_key(ep) for ep in premises}
            for lp_p in lp_prems:
                if _premise_dedup_key(lp_p) not in existing_keys:
                    premises.append(lp_p)
                    existing_keys.add(_premise_dedup_key(lp_p))
                    accepted_ops.append({"kind": lp_p.get("kind"), "clause_id": "parser_merged"})

    # 3. Validate goals
    math_goals: list[dict[str, Any]] = []
    for idx, g in enumerate(raw_slm_json.get("g") or ()):
        if not isinstance(g, dict):
            continue
        mg, gerr = _convert_compact_goal(g, idx, ctx, solid_info)
        if gerr is not None:
            rejected_ops.append({"op": f"goal:{g.get('t')}", "reason": gerr})
            continue
        assert mg is not None
        math_goals.append(mg)
        accepted_ops.append({"kind": f"goal:{g.get('t')}", "clause_id": g.get("c")})

    # /11: a simulation-only source legitimately has no math goal (construct_object only); a goal the model emitted and
    # the validator rejected still refuses.
    sim_only = is_simulation_only_source(ctx)
    goal_rejected = any(str(r.get("op", "")).startswith("goal") for r in rejected_ops)
    if not math_goals and not (sim_only and not goal_rejected):
        return None, {
            "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
            "grounding_status": "REJECTED_NO_GROUNDED_GOAL",
            "reason_code": "AMBIGUOUS_FACT" if rejected_ops else "MISSING_DIMENSION",
            "failure_taxonomy": "GROUNDING_REJECTED",
            "accepted_ops": accepted_ops,
            "rejected_ops": rejected_ops or [{"op": "goal", "reason": "NO_GROUNDED_GOAL"}],
        }

    expected_goals = count_expected_source_goals(ctx)
    mg_status = ("SIMULATION_ONLY" if sim_only and not math_goals
                 else classify_multi_goal_status(expected_goals, math_goals, unresolved_items))

    if use_v9 and expected_goals >= 2 and len(math_goals) < expected_goals:
        return None, {
            "validator_version": val_ver,
            "grounding_status": "INCOMPLETE_EXTRACTION_REFUSED",
            "reason_code": "REQUEST_NOT_ANSWERED",
            "failure_taxonomy": "MULTI_GOAL_INCOMPLETE",
            "multi_goal_status": mg_status,
            "expected_goal_count": expected_goals,
            "extracted_goal_count": len(math_goals),
            "accepted_ops": accepted_ops,
            "rejected_ops": rejected_ops or [{"op": "multi_goal", "reason": f"EXTRACTED_{len(math_goals)}_OF_{expected_goals}"}],
        }

    if rejected_ops:
        return None, {
            "validator_version": val_ver,
            "grounding_status": "REJECTED_INVALID_COMPACT_OP",
            "reason_code": "UNGROUNDED_VALUE",
            "failure_taxonomy": "GROUNDING_REJECTED",
            "accepted_ops": accepted_ops,
            "rejected_ops": rejected_ops,
        }

    # /11: the construct_object goal quotes the show request itself when the source has one (the Source Gate then reads
    # that clause as the request), exactly as rule 7b of the deterministic parser does; else the solid declaration.
    req = simulation_request_span(ctx.clauses, ctx.working_text)
    sim_quote = ctx.working_text[req[0]:req[1]] if req else solid_quote
    canon_payload: dict[str, Any] = {
        "schema_version": TYPED_FACT_NEXT_V2_SCHEMA_VERSION,
        "problem_text": ctx.working_text,
        "length_unit": _infer_length_unit(premises),
        "solids": solids_list,
        "premises": premises,
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": sim_quote}
        ],
        "math_goals": math_goals,
    }
    return canon_payload, {
        "validator_version": val_ver,
        "grounding_status": "GROUNDED_AND_LOWERED",
        "reason_code": None,
        "failure_taxonomy": "NONE",
        "multi_goal_status": mg_status,
        "accepted_ops": accepted_ops,
        "rejected_ops": [],
    }


def _prompt_clause_text(text: str) -> str:
    """Canonicalize nested simulation lead-ins ("Mô phỏng hình chóp..." -> "Cho hình chóp...") for AxoV9 prompt ONLY."""
    if m_lead := SIMULATION_LEAD_VERB_RE.match(text):
        tail = text[m_lead.end():]
        if _EMBEDDED_SOLID_HEAD_RE.match(tail):
            cleaned_tail = re.sub(r"^(?:(?:mô\s+hình|hình)\s+3D\s+của\s+)", "", tail, flags=re.IGNORECASE)
            return f"Cho {cleaned_tail}"
    return text


def _build_compact_clause_messages(ctx: CompactClauseContext, *, clause_subset: list[IndexedClause] | None = None) -> list[dict[str, str]]:
    """Build static-prefix-cacheable prompt with typed symbol tables and worked JSON examples."""
    target_clauses = clause_subset if clause_subset is not None else ctx.clauses
    clause_block = "\n".join(f"[{c.clause_id}] {_prompt_clause_text(c.text)}" for c in target_clauses)

    def _lbls(kind: str) -> str:
        vals = [e.label for e in ctx.entities if e.kind == kind]
        return ", ".join(vals) if vals else "none"

    qty_vals = ", ".join(q.raw_token for q in ctx.quantities) or "none"
    system_prompt = (
        "/no_think\n"
        "Trích xuất bài toán hình học không gian tiếng Việt thành đúng 1 dòng JSON:\n"
        "{\"s\":[cid,stype,solid,reg],\"r\":[...],\"g\":[...],\"u\":[]}\n"
        "Quy tắc:\n"
        "- s: [cid, \"pyr\"|\"pri\"|\"cube\"|\"box\", solid, 0|1].\n"
        "- r: trích xuất MỌI giả thiết theo từng mệnh đề c=0,1,2... (KHÔNG bỏ sót dữ kiện):\n"
        "  * Hình đáy/mặt: reg_poly(a,q?), rhom(a,q?), rect(a), para(a), right_tri(a,pt), right_iso_tri(a,pt), iso_tri(a,pt)\n"
        "  * Vuông góc/điểm/chiếu: perp_lp(a,b), perp_ll(a,b), face_perp(a,b), mid(pt,a), cent(pt,a), proj(pt,a,b), div(pt,a,q)\n"
        "  * Độ dài/góc: len(a,q), eq_len(a,b), height(a,q), ang_lp(a,b,q), ang_pp(a,b,q), ang_ll(a,b,q), ang_vtx(a,pt,q), area(a,q)\n"
        "- g: trích xuất MỌI câu hỏi: vol(tgt), dist_pt_plane(a,b), dist_pt_line(a,b), dist_line_line(a,b), len(a), ang_lp(a,b), ang_pp(a,b), ang_ll(a,b), area(a)\n"
        "- u: chỉ dùng [{\"c\":cid,\"k\":\"ambig|missing|contra|unsup\"}] nếu mệnh đề mơ hồ ('cạnh bên' trên chóp thường), thiếu kích thước, phủ định ('không vuông góc'), hoặc mặt cầu/nón/trụ.\n"
        "- BẮT BUỘC dùng đúng tên hình/điểm/số của đề hiện tại.\n\n"
        "Ví dụ 1:\n"
        "[0] Cho hình chóp P.UVW có đáy UVW là tam giác vuông tại V, UV=a, VW=2a.\n"
        "[1] PU vuông góc với đáy (UVW) và góc giữa PV và (UVW) bằng 45°.\n"
        "[2] Tính khoảng cách từ U đến (PVW).\n"
        "-> {\"s\":[0,\"pyr\",\"P.UVW\",0],\"r\":[{\"c\":0,\"p\":\"right_tri\",\"a\":\"UVW\",\"pt\":\"V\"},{\"c\":0,\"p\":\"len\",\"a\":\"UV\",\"q\":\"a\"},{\"c\":0,\"p\":\"len\",\"a\":\"VW\",\"q\":\"2a\"},{\"c\":1,\"p\":\"perp_lp\",\"a\":\"PU\",\"b\":\"UVW\"},{\"c\":1,\"p\":\"ang_lp\",\"a\":\"PV\",\"b\":\"UVW\",\"q\":\"45°\"}],\"g\":[{\"c\":2,\"t\":\"dist_pt_plane\",\"a\":\"U\",\"b\":\"PVW\"}],\"u\":[]}\n\n"
        "Ví dụ 2:\n"
        "[0] Cho lăng trụ đứng XYZ.X'Y'Z' có đáy XYZ là tam giác đều cạnh 2a, XX'=2a.\n"
        "[1] Gọi M là trung điểm XZ, mặt bên XYY'X' là hình vuông và vuông góc với đáy XYZ, góc giữa (X'YZ) và (XYZ) bằng 60°.\n"
        "[2] Tính thể tích khối lăng trụ XYZ.X'Y'Z'.\n"
        "-> {\"s\":[0,\"pri\",\"XYZ.X'Y'Z'\",1],\"r\":[{\"c\":0,\"p\":\"reg_poly\",\"a\":\"XYZ\",\"q\":\"2a\"},{\"c\":0,\"p\":\"len\",\"a\":\"XX'\",\"q\":\"2a\"},{\"c\":1,\"p\":\"mid\",\"pt\":\"M\",\"a\":\"XZ\"},{\"c\":1,\"p\":\"reg_poly\",\"a\":\"XYY'X'\"},{\"c\":1,\"p\":\"face_perp\",\"a\":\"XYY'X'\",\"b\":\"XYZ\"},{\"c\":1,\"p\":\"ang_pp\",\"a\":\"X'YZ\",\"b\":\"XYZ\",\"q\":\"60°\"}],\"g\":[{\"c\":2,\"t\":\"vol\",\"tgt\":\"XYZ.X'Y'Z'\"}],\"u\":[]}"
    )
    user_prompt = (
        f"Mệnh đề cần trích xuất:\n{clause_block}\n"
        f"Solids: {_lbls('solid')} | Planes: {_lbls('poly')} | Segs: {_lbls('seg')} | Pts: {_lbls('point')} | Qtys: {qty_vals}\n"
        "JSON:"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def compute_local_slm_capability_identity() -> dict[str, str]:
    return {
        "registry_version": registry.REGISTRY_VERSION,
        "planner_version": planner.PLANNER_VERSION,
        "engine_version": engine.ENGINE_VERSION,
        "typed_fact_next": TYPED_FACT_NEXT_V2_SCHEMA_VERSION,
        "adapter_version": ADAPTER_V4_VERSION,
        "envelope_version": ROUTE_D_SIMULATION_V4_SCHEMA_VERSION,
    }


DEFAULT_V9_SLM_MAX_TOKENS = 256
SUPPORTED_GRAMMAR_MODES = ("gbnf", "retry_on_invalid")
_V9_INFLIGHT_LOCK = threading.Lock()
_V9_INFLIGHT_EVENTS: dict[str, threading.Event] = {}


def _compact_grounding_policy_version(
    use_verified_normalizer: bool,
    *,
    closure_mode: str = DEFAULT_CLOSURE_MODE,
    normalizer_version: str = "v2",
    grammar_mode: str = "gbnf",
) -> str:
    if not use_verified_normalizer:
        norm_id = "none"
    elif normalizer_version == "v1":
        norm_id = SLM_VERIFIED_NORMALIZER_V1_VERSION
    elif normalizer_version == "v3":
        norm_id = SLM_VERIFIED_NORMALIZER_V3_VERSION
    else:
        norm_id = SLM_VERIFIED_NORMALIZER_VERSION
    val_ver = SLM_GROUNDING_VALIDATOR_V9_VERSION if closure_mode == V9_CLOSURE_MODE else SLM_GROUNDING_VALIDATOR_VERSION
    suffix = f"|gm={grammar_mode}" if closure_mode == V9_CLOSURE_MODE and grammar_mode != "gbnf" else ""
    return f"{val_ver}|norm={norm_id}|closure={closure_mode}{suffix}"


def run_local_slm_extraction(
    problem_text: str,
    *,
    model_key: str | None = None,
    strategy: str | None = None,
    runtime: LocalSlmRuntime | None = None,
    allow_download: bool = False,
    threads: int | None = None,
    max_tokens: int | None = None,
    use_verified_normalizer: bool | None = None,
    closure_mode: str | None = None,
    normalizer_version: str | None = None,
    grammar_mode: str | None = None,
    use_cache: bool = True,
    cache_prompt: bool = True,
) -> LocalSlmExtractionResult:
    """Run local SLM semantic extraction + deterministic source grounding."""
    norm_raw = normalize_problem_text(problem_text or "")
    eff_strategy = resolve_local_slm_strategy(strategy)
    spec = resolve_local_slm_model_spec(model_key)
    eff_closure = str(closure_mode or DEFAULT_CLOSURE_MODE).strip().lower()
    if eff_closure not in SUPPORTED_CLOSURE_MODES:
        eff_closure = DEFAULT_CLOSURE_MODE
    is_v9_mode = eff_closure == V9_CLOSURE_MODE
    eff_grammar_mode = str(grammar_mode or "gbnf").strip().lower()
    if eff_grammar_mode not in SUPPORTED_GRAMMAR_MODES:
        eff_grammar_mode = "gbnf"
    eff_env_ver = SLM_GROUNDING_ENVELOPE_V9_VERSION if is_v9_mode else SLM_GROUNDING_ENVELOPE_VERSION
    eff_val_ver = SLM_GROUNDING_VALIDATOR_V9_VERSION if is_v9_mode else SLM_GROUNDING_VALIDATOR_VERSION
    eff_norm_ver = str(normalizer_version or ("v3" if is_v9_mode else ("v1" if eff_closure == "v6" else "v2"))).strip().lower()
    eff_use_norm = (
        (eff_strategy in ("compact_clause", "compact_clause_per_clause"))
        if use_verified_normalizer is None
        else bool(use_verified_normalizer)
    )

    t_prep0 = time.perf_counter()
    inj = detect_prompt_injection(problem_text or "")
    if inj is not None:
        return LocalSlmExtractionResult(
            ok=False,
            strategy=eff_strategy,
            model_key=spec.model_key,
            model_sha256=spec.sha256,
            norm_text=norm_raw,
            wire_payload=None,
            canonical_payload=None,
            reason_code="UNGROUNDED_VALUE",
            reason_detail=f"Rejected adversarial instruction pattern: {inj!r}",
            failure_taxonomy="PROMPT_INJECTION_REJECTED",
            grounding_envelope={
                "envelope_version": SLM_GROUNDING_ENVELOPE_VERSION,
                "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
                "strategy": eff_strategy,
                "model_key": spec.model_key,
                "model_sha256": spec.sha256,
                "slm_invoked": False,
                "grounding_status": "REJECTED_PROMPT_INJECTION",
                "failure_taxonomy": "PROMPT_INJECTION_REJECTED",
            },
            stage_timings_ms={"preprocessing_ms": round((time.perf_counter() - t_prep0) * 1000.0, 3)},
        )

    # Phase B2 (/12): reject A3 visualization-metric ambiguity before invoking SLM; project diacritic-free text 1-1
    comp_analysis = analyze_compositional_geometry(norm_raw)
    if comp_analysis.ambiguous_visualization_clauses:
        prep_ms = round((time.perf_counter() - t_prep0) * 1000.0, 3)
        amb_reasons = [c.ambiguity_reason for c in comp_analysis.ambiguous_visualization_clauses if c.ambiguity_reason]
        return LocalSlmExtractionResult(
            ok=False,
            strategy=eff_strategy,
            model_key=spec.model_key,
            model_sha256=spec.sha256,
            norm_text=norm_raw,
            wire_payload=None,
            canonical_payload=None,
            reason_code="AMBIGUOUS_FACT",
            reason_detail=f"Refused A3 ambiguous display-metric wording without explicit query/construction target: {amb_reasons}",
            failure_taxonomy="AMBIGUOUS_DISPLAY_METRIC",
            grounding_envelope={
                "envelope_version": eff_env_ver,
                "validator_version": eff_val_ver,
                "strategy": eff_strategy,
                "closure_mode": eff_closure,
                "model_key": spec.model_key,
                "model_sha256": spec.sha256,
                "slm_invoked": False,
                "grounding_status": "REJECTED_AMBIGUOUS_DISPLAY_METRIC",
                "failure_taxonomy": "AMBIGUOUS_DISPLAY_METRIC",
            },
            stage_timings_ms={"preprocessing_ms": prep_ms},
        )

    # Phase C: span-audited Verified Normalization (only when enabled)
    norm_res: VerifiedNormalizationResult | None = None
    norm_input = normalize_problem_text(comp_analysis.mapped.normalized_text) if comp_analysis.mapped.diacritic_projected else norm_raw
    working_text = norm_input
    t_norm0 = time.perf_counter()
    if eff_use_norm:
        norm_res = normalize_for_slm_grounding(norm_input, normalizer_version=eff_norm_ver)
        working_text = norm_res.canonical_text
        if norm_res.typo_detected:
            prep_ms = round((time.perf_counter() - t_prep0) * 1000.0, 3)
            norm_ms = round((time.perf_counter() - t_norm0) * 1000.0, 3)
            return LocalSlmExtractionResult(
                ok=False,
                strategy=eff_strategy,
                model_key=spec.model_key,
                model_sha256=spec.sha256,
                norm_text=working_text,
                wire_payload=None,
                canonical_payload=None,
                reason_code="AMBIGUOUS_FACT",
                reason_detail=f"Conservative ambiguity refusal on diacritic typo: {norm_res.ambiguity_flags}",
                failure_taxonomy="TYPO_REQUIRES_CONFIRMATION",
                grounding_envelope={
                    "envelope_version": eff_env_ver,
                    "validator_version": eff_val_ver,
                    "strategy": eff_strategy,
                    "closure_mode": eff_closure,
                    "normalizer_version": eff_norm_ver,
                    "model_key": spec.model_key,
                    "model_sha256": spec.sha256,
                    "slm_invoked": False,
                    "grounding_status": "REJECTED_TYPO_AMBIGUITY",
                    "failure_taxonomy": "TYPO_REQUIRES_CONFIRMATION",
                    "normalization_provenance": norm_res.to_provenance_dict(),
                },
                stage_timings_ms={"preprocessing_ms": prep_ms, "normalizer_ms": norm_ms},
                normalization_provenance=norm_res.to_provenance_dict(),
            )
    normalizer_ms = round((time.perf_counter() - t_norm0) * 1000.0, 3)

    t_lp0 = time.perf_counter()
    local_res = parse_geometry_problem_locally(working_text)
    clauses = index_source_clauses(working_text)
    local_parser_ms = round((time.perf_counter() - t_lp0) * 1000.0, 3)
    if not clauses:
        return LocalSlmExtractionResult(
            ok=False,
            strategy=eff_strategy,
            model_key=spec.model_key,
            model_sha256=spec.sha256,
            norm_text=working_text,
            wire_payload=None,
            canonical_payload=None,
            reason_code="MISSING_DIMENSION",
            reason_detail="Empty problem text after normalization.",
            failure_taxonomy="EMPTY_INPUT",
            grounding_envelope={
                "envelope_version": eff_env_ver,
                "validator_version": eff_val_ver,
                "strategy": eff_strategy,
                "model_key": spec.model_key,
                "model_sha256": spec.sha256,
                "slm_invoked": False,
                "grounding_status": "EMPTY_INPUT",
                "failure_taxonomy": "EMPTY_INPUT",
            },
        )

    # Build 9-field deterministic cache identity (`§7.D3`)
    if eff_strategy in ("compact_clause", "compact_clause_per_clause"):
        schema_ver = SLM_COMPACT_SCHEMA_VERSION
        schema_hash = _compact_schema_sha256()
    elif eff_strategy == "minimal_ops":
        schema_ver = "slm-minimal-ops/1"
        schema_hash = hashlib.sha256(json.dumps(MINIMAL_OPS_JSON_SCHEMA, sort_keys=True).encode("utf-8")).hexdigest()
    else:
        schema_ver = "slm-direct-wire/1"
        schema_hash = hashlib.sha256(json.dumps(DIRECT_WIRE_JSON_SCHEMA, sort_keys=True).encode("utf-8")).hexdigest()

    cache_key, _cache_meta = build_local_slm_cache_identity(
        exact_input_text=norm_raw,
        model_key=spec.model_key,
        model_sha256=spec.sha256,
        runtime_version=LOCAL_SLM_RUNTIME_V9_VERSION if is_v9_mode else LOCAL_SLM_RUNTIME_VERSION,
        strategy=eff_strategy,
        schema_version=schema_ver,
        schema_sha256=schema_hash,
        grounding_policy_version=_compact_grounding_policy_version(
            eff_use_norm,
            closure_mode=eff_closure,
            normalizer_version=eff_norm_ver,
            grammar_mode=eff_grammar_mode,
        ),
        parser_version=LOCAL_GEOMETRY_PARSER_VERSION,
        capability_identity=compute_local_slm_capability_identity(),
        namespace=LOCAL_SLM_CACHE_V9_NAMESPACE if is_v9_mode else LOCAL_SLM_CACHE_NAMESPACE,
    )
    cache_allowed = bool(use_cache and (is_v9_mode or runtime is None))

    def _hit_result(cached_res: LocalSlmExtractionResult, lookup_ms: float) -> LocalSlmExtractionResult:
        return LocalSlmExtractionResult(
            ok=cached_res.ok,
            strategy=cached_res.strategy,
            model_key=cached_res.model_key,
            model_sha256=cached_res.model_sha256,
            norm_text=cached_res.norm_text,
            wire_payload=cached_res.wire_payload,
            canonical_payload=cached_res.canonical_payload,
            reason_code=cached_res.reason_code,
            reason_detail=cached_res.reason_detail,
            failure_taxonomy=cached_res.failure_taxonomy,
            grounding_envelope={**cached_res.grounding_envelope, "cache_hit": True},
            inference=cached_res.inference,
            stage_timings_ms={
                "cache_lookup_ms": lookup_ms,
                "cache_hit_ms": round((time.perf_counter() - t_prep0) * 1000.0, 3),
            },
            normalization_provenance=cached_res.normalization_provenance,
            cache_hit=True,
            cache_key=cache_key,
        )

    t_cl0 = time.perf_counter()
    inflight_evt: threading.Event | None = None
    inflight_owner = False
    if cache_allowed:
        cached_res = get_shared_local_slm_extraction_cache().get(cache_key)
        if cached_res is not None:
            return _hit_result(cached_res, round((time.perf_counter() - t_cl0) * 1000.0, 3))
        if is_v9_mode:
            wait_evt: threading.Event | None = None
            with _V9_INFLIGHT_LOCK:
                wait_evt = _V9_INFLIGHT_EVENTS.get(cache_key)
                if wait_evt is None:
                    inflight_evt = threading.Event()
                    _V9_INFLIGHT_EVENTS[cache_key] = inflight_evt
                    inflight_owner = True
            if wait_evt is not None:
                wait_evt.wait(timeout=45.0)
                cached_after = get_shared_local_slm_extraction_cache().get(cache_key)
                if cached_after is not None:
                    return _hit_result(cached_after, round((time.perf_counter() - t_cl0) * 1000.0, 3))
                with _V9_INFLIGHT_LOCK:
                    if _V9_INFLIGHT_EVENTS.get(cache_key) is None:
                        inflight_evt = threading.Event()
                        _V9_INFLIGHT_EVENTS[cache_key] = inflight_evt
                        inflight_owner = True
    cache_lookup_ms = round((time.perf_counter() - t_cl0) * 1000.0, 3)

    eff_runtime = runtime or get_shared_local_slm_runtime()

    try:
        if eff_strategy in ("compact_clause", "compact_clause_per_clause"):
            t_ctx0 = time.perf_counter()
            ctx = build_compact_clause_context(working_text)
            clause_context_ms = round((time.perf_counter() - t_ctx0) * 1000.0, 3)
            prep_ms = round((time.perf_counter() - t_prep0) * 1000.0, 3)
            eff_max_tok = max_tokens or (DEFAULT_V9_SLM_MAX_TOKENS if is_v9_mode else DEFAULT_COMPACT_SLM_MAX_TOKENS)

            t_pb0 = time.perf_counter()
            grammar_build_ms = 0.0
            grammar_retry_used = False
            grammar_retry_ms = 0.0
            if eff_strategy == "compact_clause":
                messages = _build_compact_clause_messages(ctx)
                prompt_build_ms = round((time.perf_counter() - t_pb0) * 1000.0, 3)
                t_gb0 = time.perf_counter()
                dyn_grammar = build_compact_grammar_for_context(ctx, closure_mode=eff_closure)
                grammar_build_ms = round((time.perf_counter() - t_gb0) * 1000.0, 3)
                if eff_grammar_mode == "retry_on_invalid":
                    inf_res = eff_runtime.chat_completion_json(
                        messages=messages,
                        json_schema={"type": "object"},
                        schema_name="compact_clause_loose",
                        cache_prompt=cache_prompt,
                        model_key=spec.model_key,
                        ctx_size=DEFAULT_COMPACT_SLM_CTX_SIZE,
                        max_tokens=eff_max_tok,
                        threads=threads,
                        allow_download=allow_download,
                    )
                    raw_merged = inf_res.parsed_json
                else:
                    inf_res = eff_runtime.chat_completion_json(
                        messages=messages,
                        grammar=dyn_grammar,
                        cache_prompt=cache_prompt,
                        model_key=spec.model_key,
                        ctx_size=DEFAULT_COMPACT_SLM_CTX_SIZE,
                        max_tokens=eff_max_tok,
                        threads=threads,
                        allow_download=allow_download,
                    )
                    raw_merged = inf_res.parsed_json
            else:
                # Per-clause batching ablation: one call per clause, then merge s/r/g/u
                merged: dict[str, Any] = {"s": None, "r": [], "g": [], "u": []}
                last_inf: LocalSlmInferenceResult | None = None
                total_infer_ms = 0.0
                total_prompt_tok = 0
                total_comp_tok = 0
                for cl in ctx.clauses:
                    messages = _build_compact_clause_messages(ctx, clause_subset=[cl])
                    t_gb0 = time.perf_counter()
                    dyn_grammar = build_compact_grammar_for_context(ctx, clause_subset=[cl], closure_mode=eff_closure)
                    grammar_build_ms += (time.perf_counter() - t_gb0) * 1000.0
                    inf_i = eff_runtime.chat_completion_json(
                        messages=messages,
                        grammar=dyn_grammar,
                        cache_prompt=cache_prompt,
                        model_key=spec.model_key,
                        ctx_size=DEFAULT_COMPACT_SLM_CTX_SIZE,
                        max_tokens=eff_max_tok,
                        threads=threads,
                        allow_download=allow_download,
                    )
                    last_inf = inf_i
                    total_infer_ms += inf_i.inference_time_ms
                    total_prompt_tok += inf_i.prompt_tokens or 0
                    total_comp_tok += inf_i.completion_tokens or 0
                    pj = inf_i.parsed_json
                    if merged["s"] is None and pj.get("s") is not None:
                        merged["s"] = pj["s"]
                    merged["r"].extend(pj.get("r") or ())
                    merged["g"].extend(pj.get("g") or ())
                    merged["u"].extend(pj.get("u") or ())
                grammar_build_ms = round(grammar_build_ms, 3)
                prompt_build_ms = round((time.perf_counter() - t_pb0) * 1000.0 - grammar_build_ms, 3)
                assert last_inf is not None
                inf_res = LocalSlmInferenceResult(
                    raw_content=json.dumps(merged, ensure_ascii=False),
                    parsed_json=merged,
                    model_key=last_inf.model_key,
                    model_sha256=last_inf.model_sha256,
                    runtime_version=last_inf.runtime_version,
                    server_load_time_ms=last_inf.server_load_time_ms,
                    inference_time_ms=round(total_infer_ms, 2),
                    prompt_tokens=total_prompt_tok,
                    completion_tokens=total_comp_tok,
                    thinking_stripped=last_inf.thinking_stripped,
                    server_restarted=last_inf.server_restarted,
                    python_rss_mib=last_inf.python_rss_mib,
                    server_rss_mib=last_inf.server_rss_mib,
                    combined_rss_mib=last_inf.combined_rss_mib,
                    server_peak_rss_mib=last_inf.server_peak_rss_mib,
                    threads=last_inf.threads,
                    ctx_size=last_inf.ctx_size,
                    queue_wait_ms=last_inf.queue_wait_ms,
                    prompt_eval_ms=last_inf.prompt_eval_ms,
                    token_gen_ms=round(total_infer_ms, 2),
                    tokens_per_sec=last_inf.tokens_per_sec,
                    cached_prompt_tokens=last_inf.cached_prompt_tokens,
                    json_decode_ms=last_inf.json_decode_ms,
                    cache_prompt_enabled=bool(cache_prompt),
                )
                raw_merged = merged

            t_val0 = time.perf_counter()
            canon_payload, val_diag = validate_and_lower_compact_clause(ctx=ctx, raw_slm_json=raw_merged, closure_mode=eff_closure)
            if (
                eff_grammar_mode == "retry_on_invalid"
                and eff_strategy == "compact_clause"
                and canon_payload is None
                and val_diag.get("grounding_status") != "REFUSED_UNRESOLVABLE"
            ):
                t_ret0 = time.perf_counter()
                inf_retry = eff_runtime.chat_completion_json(
                    messages=messages,
                    grammar=dyn_grammar,
                    cache_prompt=cache_prompt,
                    model_key=spec.model_key,
                    ctx_size=DEFAULT_COMPACT_SLM_CTX_SIZE,
                    max_tokens=eff_max_tok,
                    threads=threads,
                    allow_download=allow_download,
                )
                canon_payload, val_diag = validate_and_lower_compact_clause(
                    ctx=ctx, raw_slm_json=inf_retry.parsed_json, closure_mode=eff_closure
                )
                grammar_retry_used = True
                grammar_retry_ms = round((time.perf_counter() - t_ret0) * 1000.0, 3)
                inf_res = inf_retry
            val_lower_ms = round((time.perf_counter() - t_val0) * 1000.0, 3)

            wire_normalize_ms = 0.0
            if canon_payload is not None:
                t_wn0 = time.perf_counter()
                mapped = comp_analysis.mapped
                norm_mapped = mapped.normalized_text if mapped.diacritic_projected else norm_raw

                def _orig_quote_slm(q_val: Any) -> Any:
                    if not isinstance(q_val, str) or not q_val or q_val in norm_raw:
                        return q_val
                    cand = q_val
                    if norm_res is not None and getattr(norm_res, "steps", None) and cand not in norm_mapped:
                        for st in reversed(norm_res.steps):
                            if st.normalized_excerpt and st.normalized_excerpt in cand and st.original_excerpt:
                                cand = cand.replace(st.normalized_excerpt, st.original_excerpt)
                    if cand in norm_raw:
                        return cand
                    if mapped.diacritic_projected:
                        p0 = norm_mapped.find(cand)
                        if p0 < 0 and len(cand) > 1:
                            for alt in (cand[0].lower() + cand[1:], cand[0].upper() + cand[1:]):
                                p0 = norm_mapped.find(alt)
                                if p0 >= 0:
                                    break
                        if p0 < 0:
                            m_ci = re.search(re.escape(cand), norm_mapped, re.IGNORECASE | re.UNICODE)
                            if m_ci:
                                p0 = m_ci.start()
                        if p0 >= 0:
                            oq = mapped.orig_quote(p0, p0 + len(cand))
                            if oq and oq in norm_raw:
                                return oq
                    return cand if cand in norm_raw else q_val

                if mapped.diacritic_projected:
                    canon_payload["problem_text"] = norm_raw
                    for key in ("solids", "premises", "derived_sections", "relations", "simulation_goals", "math_goals", "unresolved", "described_points"):
                        for item in canon_payload.get(key) or ():
                            if isinstance(item, dict) and "quote" in item:
                                item["quote"] = _orig_quote_slm(item["quote"])
                wire_payload = to_wire_typed_fact_next_v2(canon_payload)
                norm_canon = _normalize_transport_payload(wire_payload)
                wire_normalize_ms = round((time.perf_counter() - t_wn0) * 1000.0, 3)
            else:
                wire_payload = None
                norm_canon = None

            stage_timings = {
                "preprocessing_ms": prep_ms,
                "normalizer_ms": normalizer_ms,
                "local_parser_ms": local_parser_ms,
                "cache_lookup_ms": cache_lookup_ms,
                "clause_context_ms": clause_context_ms,
                "prompt_build_ms": prompt_build_ms,
                "grammar_build_ms": grammar_build_ms,
                "queue_wait_ms": inf_res.queue_wait_ms,
                "prompt_eval_ms": inf_res.prompt_eval_ms,
                "token_gen_ms": inf_res.token_gen_ms,
                "json_decode_ms": inf_res.json_decode_ms,
                "grounding_and_lowering_ms": val_lower_ms,
                "wire_normalize_ms": wire_normalize_ms,
                "server_load_time_ms": inf_res.server_load_time_ms,
                "slm_inference_ms": inf_res.inference_time_ms,
                "grammar_retry_ms": grammar_retry_ms,
                "grammar_retry_used": grammar_retry_used,
                "prompt_tokens": inf_res.prompt_tokens,
                "completion_tokens": inf_res.completion_tokens,
                "cached_prompt_tokens": inf_res.cached_prompt_tokens,
                "tokens_per_sec": inf_res.tokens_per_sec,
            }
            norm_prov = norm_res.to_provenance_dict() if norm_res is not None else None
            envelope = {
                "envelope_version": eff_env_ver,
                "validator_version": eff_val_ver,
                "schema_version": SLM_COMPACT_SCHEMA_VERSION,
                "strategy": eff_strategy,
                "closure_mode": eff_closure,
                "grammar_mode": eff_grammar_mode,
                "grammar_retry_used": grammar_retry_used,
                "normalizer_version": eff_norm_ver if eff_use_norm else "none",
                "model_key": inf_res.model_key,
                "model_sha256": inf_res.model_sha256,
                "slm_invoked": True,
                "cache_hit": False,
                "cache_key": cache_key,
                "parser_status": local_res.status,
                "grounding_status": val_diag.get("grounding_status"),
                "multi_goal_status": val_diag.get("multi_goal_status"),
                "accepted_ops": val_diag.get("accepted_ops", []),
                "rejected_ops": val_diag.get("rejected_ops", []),
                "failure_taxonomy": val_diag.get("failure_taxonomy", "NONE"),
                "normalization_provenance": norm_prov,
                "stage_timings_ms": stage_timings,
                "server_load_time_ms": inf_res.server_load_time_ms,
                "inference_time_ms": inf_res.inference_time_ms,
                "combined_rss_mib": inf_res.combined_rss_mib,
            }
            if canon_payload is None:
                res_out = LocalSlmExtractionResult(
                    ok=False,
                    strategy=eff_strategy,
                    model_key=inf_res.model_key,
                    model_sha256=inf_res.model_sha256,
                    norm_text=working_text,
                    wire_payload=None,
                    canonical_payload=None,
                    reason_code=val_diag.get("reason_code") or "AMBIGUOUS_FACT",
                    reason_detail=str(val_diag.get("rejected_ops") or val_diag.get("grounding_status")),
                    failure_taxonomy=str(val_diag.get("failure_taxonomy") or "GROUNDING_REJECTED"),
                    grounding_envelope=envelope,
                    inference=inf_res,
                    stage_timings_ms=stage_timings,
                    normalization_provenance=norm_prov,
                    cache_hit=False,
                    cache_key=cache_key,
                )
            else:
                res_out = LocalSlmExtractionResult(
                    ok=True,
                    strategy=eff_strategy,
                    model_key=inf_res.model_key,
                    model_sha256=inf_res.model_sha256,
                    norm_text=working_text,
                    wire_payload=wire_payload,
                    canonical_payload=norm_canon,
                    reason_code=None,
                    reason_detail=None,
                    failure_taxonomy="NONE",
                    grounding_envelope=envelope,
                    inference=inf_res,
                    stage_timings_ms=stage_timings,
                    normalization_provenance=norm_prov,
                    cache_hit=False,
                    cache_key=cache_key,
                )
            if cache_allowed:
                get_shared_local_slm_extraction_cache().put(cache_key, res_out)
            return res_out
    finally:
        if inflight_owner and inflight_evt is not None:
            with _V9_INFLIGHT_LOCK:
                if _V9_INFLIGHT_EVENTS.get(cache_key) is inflight_evt:
                    _V9_INFLIGHT_EVENTS.pop(cache_key, None)
            inflight_evt.set()

    # Legacy /5 strategies preserved verbatim for Config B & ablation reproducibility
    if eff_strategy == "direct_wire":
        messages = _build_direct_wire_messages(working_text)
        schema = DIRECT_WIRE_JSON_SCHEMA
        schema_name = "typed_fact_next_wire"
    else:
        messages = _build_minimal_ops_messages(working_text, clauses, local_res)
        schema = MINIMAL_OPS_JSON_SCHEMA
        schema_name = "slm_minimal_ops"

    inf_res = eff_runtime.chat_completion_json(
        messages=messages,
        json_schema=schema,
        schema_name=schema_name,
        cache_prompt=cache_prompt,
        model_key=spec.model_key,
        max_tokens=max_tokens or DEFAULT_LOCAL_SLM_MAX_TOKENS,
        threads=threads,
        allow_download=allow_download,
    )

    if eff_strategy == "direct_wire":
        all_pts = extract_geometry_points(working_text)
        repaired_wire, err = _repair_direct_wire_quotes(inf_res.parsed_json, working_text, all_pts)
        if err is not None or repaired_wire is None:
            return LocalSlmExtractionResult(
                ok=False,
                strategy=eff_strategy,
                model_key=inf_res.model_key,
                model_sha256=inf_res.model_sha256,
                norm_text=working_text,
                wire_payload=None,
                canonical_payload=None,
                reason_code="QUOTE_NOT_IN_SOURCE" if str(err).startswith("QUOTE_") else "UNGROUNDED_VALUE",
                reason_detail=err,
                failure_taxonomy="GROUNDING_REJECTED",
                grounding_envelope={
                    "envelope_version": SLM_GROUNDING_ENVELOPE_VERSION,
                    "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
                    "strategy": eff_strategy,
                    "model_key": inf_res.model_key,
                    "model_sha256": inf_res.model_sha256,
                    "slm_invoked": True,
                    "grounding_status": "REJECTED_DIRECT_WIRE",
                    "error": err,
                    "failure_taxonomy": "GROUNDING_REJECTED",
                },
                inference=inf_res,
                cache_key=cache_key,
            )
        try:
            canon = _normalize_transport_payload(repaired_wire)
        except Exception as exc:
            return LocalSlmExtractionResult(
                ok=False,
                strategy=eff_strategy,
                model_key=inf_res.model_key,
                model_sha256=inf_res.model_sha256,
                norm_text=working_text,
                wire_payload=repaired_wire,
                canonical_payload=None,
                reason_code="INVALID_TYPED_FACT_NEXT",
                reason_detail=str(exc),
                failure_taxonomy="SCHEMA_VALIDATION_ERROR",
                grounding_envelope={
                    "envelope_version": SLM_GROUNDING_ENVELOPE_VERSION,
                    "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
                    "strategy": eff_strategy,
                    "model_key": inf_res.model_key,
                    "model_sha256": inf_res.model_sha256,
                    "slm_invoked": True,
                    "grounding_status": "REJECTED_WIRE_UNPACK",
                    "error": str(exc),
                    "failure_taxonomy": "SCHEMA_VALIDATION_ERROR",
                },
                inference=inf_res,
                cache_key=cache_key,
            )
        envelope = {
            "envelope_version": SLM_GROUNDING_ENVELOPE_VERSION,
            "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
            "strategy": eff_strategy,
            "model_key": inf_res.model_key,
            "model_sha256": inf_res.model_sha256,
            "slm_invoked": True,
            "grounding_status": "GROUNDED_DIRECT_WIRE",
            "failure_taxonomy": "NONE",
            "server_load_time_ms": inf_res.server_load_time_ms,
            "inference_time_ms": inf_res.inference_time_ms,
            "combined_rss_mib": inf_res.combined_rss_mib,
        }
        return LocalSlmExtractionResult(
            ok=True,
            strategy=eff_strategy,
            model_key=inf_res.model_key,
            model_sha256=inf_res.model_sha256,
            norm_text=working_text,
            wire_payload=repaired_wire,
            canonical_payload=canon,
            reason_code=None,
            reason_detail=None,
            failure_taxonomy="NONE",
            grounding_envelope=envelope,
            inference=inf_res,
            cache_key=cache_key,
        )

    # Approach B: minimal_ops -> validate_and_lower_minimal_ops
    canon_payload, val_diag = validate_and_lower_minimal_ops(
        norm_text=working_text,
        clauses=clauses,
        raw_slm_json=inf_res.parsed_json,
        local_parser_payload=local_res.payload,
    )
    norm_prov = norm_res.to_provenance_dict() if norm_res is not None else None
    envelope = {
        "envelope_version": SLM_GROUNDING_ENVELOPE_VERSION,
        "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
        "strategy": eff_strategy,
        "model_key": inf_res.model_key,
        "model_sha256": inf_res.model_sha256,
        "slm_invoked": True,
        "parser_status": local_res.status,
        "grounding_status": val_diag.get("grounding_status"),
        "accepted_ops": val_diag.get("accepted_ops", []),
        "rejected_ops": val_diag.get("rejected_ops", []),
        "failure_taxonomy": val_diag.get("failure_taxonomy", "NONE"),
        "normalization_provenance": norm_prov,
        "server_load_time_ms": inf_res.server_load_time_ms,
        "inference_time_ms": inf_res.inference_time_ms,
        "combined_rss_mib": inf_res.combined_rss_mib,
    }
    if canon_payload is None:
        return LocalSlmExtractionResult(
            ok=False,
            strategy=eff_strategy,
            model_key=inf_res.model_key,
            model_sha256=inf_res.model_sha256,
            norm_text=working_text,
            wire_payload=None,
            canonical_payload=None,
            reason_code=val_diag.get("reason_code") or "AMBIGUOUS_FACT",
            reason_detail=str(val_diag.get("rejected_ops") or val_diag.get("grounding_status")),
            failure_taxonomy=str(val_diag.get("failure_taxonomy") or "GROUNDING_REJECTED"),
            grounding_envelope=envelope,
            inference=inf_res,
            normalization_provenance=norm_prov,
            cache_key=cache_key,
        )

    wire_payload = to_wire_typed_fact_next_v2(canon_payload)
    norm_canon = _normalize_transport_payload(wire_payload)
    return LocalSlmExtractionResult(
        ok=True,
        strategy=eff_strategy,
        model_key=inf_res.model_key,
        model_sha256=inf_res.model_sha256,
        norm_text=working_text,
        wire_payload=wire_payload,
        canonical_payload=norm_canon,
        reason_code=None,
        reason_detail=None,
        failure_taxonomy="NONE",
        grounding_envelope=envelope,
        inference=inf_res,
        normalization_provenance=norm_prov,
        cache_key=cache_key,
    )


class LocalSlmExtractor:
    """Adapter implementing ``Extractor.extract(source_text)`` via local CPU SLM."""

    def __init__(
        self,
        *,
        model_key: str | None = None,
        strategy: str | None = None,
        runtime: LocalSlmRuntime | None = None,
        allow_download: bool = False,
        threads: int | None = None,
        use_verified_normalizer: bool | None = None,
        closure_mode: str | None = None,
        normalizer_version: str | None = None,
        grammar_mode: str | None = None,
        use_cache: bool = True,
    ) -> None:
        self.model_key = resolve_local_slm_model_spec(model_key).model_key
        self.strategy = resolve_local_slm_strategy(strategy)
        self.runtime = runtime
        self.allow_download = bool(allow_download)
        self.threads = threads
        self.use_verified_normalizer = use_verified_normalizer
        self.closure_mode = closure_mode
        self.normalizer_version = normalizer_version
        self.grammar_mode = grammar_mode
        self.use_cache = bool(use_cache)
        self.last_result: LocalSlmExtractionResult | None = None

    def extract(self, source_text: str) -> dict[str, Any] | None:
        res = run_local_slm_extraction(
            source_text,
            model_key=self.model_key,
            strategy=self.strategy,
            runtime=self.runtime,
            allow_download=self.allow_download,
            threads=self.threads,
            use_verified_normalizer=self.use_verified_normalizer,
            closure_mode=self.closure_mode,
            normalizer_version=self.normalizer_version,
            grammar_mode=self.grammar_mode,
            use_cache=self.use_cache,
        )
        self.last_result = res
        return res.canonical_payload


__all__ = [
    "COMPACT_CLAUSE_GBNF",
    "CandidateEntity",
    "CandidateQuantity",
    "CompactClauseContext",
    "DEFAULT_CLOSURE_MODE",
    "DEFAULT_COMPACT_SLM_CTX_SIZE",
    "DEFAULT_COMPACT_SLM_MAX_TOKENS",
    "DEFAULT_V9_SLM_MAX_TOKENS",
    "DEFAULT_LOCAL_SLM_STRATEGY",
    "DIRECT_WIRE_JSON_SCHEMA",
    "IndexedClause",
    "LOCAL_SLM_EXTRACTOR_V9_VERSION",
    "LOCAL_SLM_EXTRACTOR_VERSION",
    "LocalSlmExtractionResult",
    "LocalSlmExtractor",
    "MINIMAL_OPS_JSON_SCHEMA",
    "SLM_COMPACT_SCHEMA_VERSION",
    "SLM_GROUNDING_ENVELOPE_V9_VERSION",
    "SLM_GROUNDING_ENVELOPE_VERSION",
    "SLM_GROUNDING_VALIDATOR_V9_VERSION",
    "SLM_GROUNDING_VALIDATOR_VERSION",
    "SUPPORTED_CLOSURE_MODES",
    "SUPPORTED_GRAMMAR_MODES",
    "SUPPORTED_SLM_STRATEGIES",
    "V9_CLOSURE_MODE",
    "build_compact_clause_context",
    "build_compact_grammar_for_context",
    "classify_multi_goal_status",
    "compute_local_slm_capability_identity",
    "detect_prompt_injection",
    "extract_geometry_points",
    "index_source_clauses",
    "is_value_grounded_in_clause",
    "resolve_local_slm_strategy",
    "run_local_slm_extraction",
    "select_clean_quote",
    "validate_and_lower_compact_clause",
    "validate_and_lower_minimal_ops",
]
