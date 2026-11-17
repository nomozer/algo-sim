"""Grounded Vietnamese geometry extraction via local sub-1B SLM (Axo Hybrid /5).

Supports two experimental extraction strategies behind deterministic source
grounding, schema validation, and parser-conflict checks:
  - ``direct_wire`` (Approach A): SLM emits compact ``typed-fact-next/2`` wire
    JSON directly under constrained decoding, then passes quote/token validation.
  - ``minimal_ops`` (Approach B): SLM emits compact clause-indexed primitive ops
    and goals, which a deterministic validator lowers into canonical
    ``typed-fact-next/2`` payloads after checking verbatim tokens, quantities,
    negations, clause roles, ambiguity, and Local Parser consistency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
import re
from typing import Any

from app.ai.local_geometry_parser import (
    _canon_val,
    normalize_problem_text,
    parse_geometry_problem_locally,
    split_into_Sentences,
)
from app.ai.local_slm_runtime import (
    DEFAULT_LOCAL_SLM_MAX_TOKENS,
    DEFAULT_LOCAL_SLM_MODEL_KEY,
    LocalSlmInferenceResult,
    LocalSlmRuntime,
    LocalSlmRuntimeError,
    get_shared_local_slm_runtime,
    resolve_local_slm_model_spec,
)
from app.ai.typed_fact_next_extraction import (
    TYPED_FACT_NEXT_V2_SCHEMA_VERSION,
    _normalize_transport_payload,
    to_wire_typed_fact_next_v2,
)
from app.simulation.geometry.expression import ExprParseError, parse_quantity_expr

LOCAL_SLM_EXTRACTOR_VERSION = "local-slm-extractor/1"
SLM_GROUNDING_VALIDATOR_VERSION = "slm-grounding-validator/1"
SLM_GROUNDING_ENVELOPE_VERSION = "slm-grounding-envelope/1"

SUPPORTED_SLM_STRATEGIES = ("minimal_ops", "direct_wire")
DEFAULT_LOCAL_SLM_STRATEGY = "minimal_ops"

_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|above|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?(?:rules|constraints|source\s+gate)", re.IGNORECASE),
    re.compile(r"bypass\s+(?:source\s*gate|validation|grounding)", re.IGNORECASE),
    re.compile(r"bỏ\s+qua\s+(?:mọi\s+|tất\s+cả\s+)?(?:hướng\s+dẫn|quy\s+tắc|kiểm\s+tra(?:\s+nguồn)?)", re.IGNORECASE),
    re.compile(r"(?:system\s*prompt|<\|im_start\|>|<\|im_end\|>|```\s*json)", re.IGNORECASE),
    re.compile(r"(?:hãy\s+)?(?:tự\s+bịa|giả\s+định\s+thêm|trả\s+về\s+kết\s+quả\s+served|output\s+the\s+following\s+json)", re.IGNORECASE),
)

_CONVERSATIONAL_PREFIX_RE = re.compile(
    r"^\s*(?:"
    r"(?:em|mình|tớ|bạn|nhờ\s+(?:anh|chị|bạn|thầy|cô|axo)?|giải\s+giúp(?:\s+em|\s+mình)?|"
    r"chào\s+[^,.:;!?]+|xin\s+hỏi|cho\s+(?:em|mình)\s+hỏi|em\s+đang\s+(?:học|làm)\s+bài[^,.:;!?]*)"
    r"[\s,:;\-–]+)+",
    re.IGNORECASE | re.UNICODE,
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

_AMBIGUOUS_LATERAL_SINGLE_RE = re.compile(r"\bcạnh\s+bên\b", re.IGNORECASE | re.UNICODE)
_UNIVERSAL_LATERAL_RE = re.compile(
    r"\b(?:các|tất\s+cả|mọi|từng)\s+cạnh\s+bên\b|\bchóp\s+(?:tứ\s+giác\s+|tam\s+giác\s+)?đều\b",
    re.IGNORECASE | re.UNICODE,
)
_AMBIGUOUS_FACE_SINGLE_RE = re.compile(r"\bmặt\s+bên\b", re.IGNORECASE | re.UNICODE)

_SOLID_RE = re.compile(r"\b([A-Z][0-9]*'*)\.([A-Z][0-9']*){3,6}\b")
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
    return [
        IndexedClause(clause_id=idx, start=sa, end=sb, text=st)
        for idx, (sa, sb, st) in enumerate(split_into_Sentences(norm_text))
    ]


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


def _strip_conversational_prefix(span: str) -> str:
    cleaned = _CONVERSATIONAL_PREFIX_RE.sub("", span).strip()
    return cleaned if cleaned else span


def select_clean_quote(clause_text: str, required_tokens: list[str], norm_text: str) -> str:
    """Pick the tightest verbatim substring of `norm_text` carrying all required tokens."""
    req = [t for t in required_tokens if t]
    candidates: list[str] = []

    trimmed = _strip_conversational_prefix(clause_text)
    if trimmed and trimmed in norm_text:
        candidates.append(trimmed)

    for sep_pat in (r"\s*,\s*|\s+đồng\s+thời\s+|\s+và\s+|\s+còn\s+|\s+trong\s+đó\s+",):
        for piece in re.split(sep_pat, trimmed, flags=re.IGNORECASE):
            seg = piece.strip(" ,;:")
            if seg and seg in norm_text:
                candidates.append(seg)

    candidates.append(clause_text)

    # Prefer shortest candidate containing all required vertex/scalar tokens verbatim
    valid: list[str] = []
    for cand in candidates:
        if cand not in norm_text:
            continue
        cand_pts = extract_geometry_points(cand)
        ok = True
        for tok in req:
            if re.fullmatch(r"[A-Z][0-9]*'*", tok):
                if tok not in cand_pts and tok not in cand:
                    ok = False
                    break
            elif tok.lower() not in cand.lower():
                ok = False
                break
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
        plane = gb if len(gb) >= 3 and len(ga) < 3 else (ga if gtype in ("distance", "angle") and len(ga) >= 3 and len(gb) < 3 else [])
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
    ctext = ""
    for gcl in ordered_goal_clauses:
        if not _GOAL_MARKERS_RE.search(gcl.text):
            continue
        gcl_pts = extract_geometry_points(gcl.text)
        if not req_pts or all(rp in gcl_pts for rp in req_pts):
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
            target = {"point": pt, "plane": plane}
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
            quote_tokens = [*line, *plane]
        elif len(line) == 2 and len(line2) == 2:
            target = {"line1": line, "line2": line2}
            quote_tokens = [*line, *line2]
        elif len(plane) >= 3 and len(plane2) >= 3:
            target = {"plane1": plane, "plane2": plane2}
            quote_tokens = [*plane, *plane2]
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


def run_local_slm_extraction(
    problem_text: str,
    *,
    model_key: str | None = None,
    strategy: str | None = None,
    runtime: LocalSlmRuntime | None = None,
    allow_download: bool = False,
    threads: int | None = None,
    max_tokens: int | None = None,
) -> LocalSlmExtractionResult:
    """Run local SLM semantic extraction + deterministic source grounding."""
    norm_text = normalize_problem_text(problem_text or "")
    eff_strategy = resolve_local_slm_strategy(strategy)
    spec = resolve_local_slm_model_spec(model_key)

    inj = detect_prompt_injection(problem_text or "")
    if inj is not None:
        return LocalSlmExtractionResult(
            ok=False,
            strategy=eff_strategy,
            model_key=spec.model_key,
            model_sha256=spec.sha256,
            norm_text=norm_text,
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
        )

    local_res = parse_geometry_problem_locally(norm_text)
    clauses = index_source_clauses(norm_text)
    if not clauses:
        return LocalSlmExtractionResult(
            ok=False,
            strategy=eff_strategy,
            model_key=spec.model_key,
            model_sha256=spec.sha256,
            norm_text=norm_text,
            wire_payload=None,
            canonical_payload=None,
            reason_code="MISSING_DIMENSION",
            reason_detail="Empty problem text after normalization.",
            failure_taxonomy="EMPTY_INPUT",
            grounding_envelope={
                "envelope_version": SLM_GROUNDING_ENVELOPE_VERSION,
                "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
                "strategy": eff_strategy,
                "model_key": spec.model_key,
                "model_sha256": spec.sha256,
                "slm_invoked": False,
                "grounding_status": "EMPTY_INPUT",
                "failure_taxonomy": "EMPTY_INPUT",
            },
        )

    eff_runtime = runtime or get_shared_local_slm_runtime()
    if eff_strategy == "direct_wire":
        messages = _build_direct_wire_messages(norm_text)
        schema = DIRECT_WIRE_JSON_SCHEMA
        schema_name = "typed_fact_next_wire"
    else:
        messages = _build_minimal_ops_messages(norm_text, clauses, local_res)
        schema = MINIMAL_OPS_JSON_SCHEMA
        schema_name = "slm_minimal_ops"

    inf_res = eff_runtime.chat_completion_json(
        messages=messages,
        json_schema=schema,
        schema_name=schema_name,
        model_key=spec.model_key,
        max_tokens=max_tokens or DEFAULT_LOCAL_SLM_MAX_TOKENS,
        threads=threads,
        allow_download=allow_download,
    )

    if eff_strategy == "direct_wire":
        all_pts = extract_geometry_points(norm_text)
        repaired_wire, err = _repair_direct_wire_quotes(inf_res.parsed_json, norm_text, all_pts)
        if err is not None or repaired_wire is None:
            return LocalSlmExtractionResult(
                ok=False,
                strategy=eff_strategy,
                model_key=inf_res.model_key,
                model_sha256=inf_res.model_sha256,
                norm_text=norm_text,
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
            )
        try:
            canon = _normalize_transport_payload(repaired_wire)
        except Exception as exc:
            return LocalSlmExtractionResult(
                ok=False,
                strategy=eff_strategy,
                model_key=inf_res.model_key,
                model_sha256=inf_res.model_sha256,
                norm_text=norm_text,
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
            norm_text=norm_text,
            wire_payload=repaired_wire,
            canonical_payload=canon,
            reason_code=None,
            reason_detail=None,
            failure_taxonomy="NONE",
            grounding_envelope=envelope,
            inference=inf_res,
        )

    # Approach B: minimal_ops -> validate_and_lower_minimal_ops
    canon_payload, val_diag = validate_and_lower_minimal_ops(
        norm_text=norm_text,
        clauses=clauses,
        raw_slm_json=inf_res.parsed_json,
        local_parser_payload=local_res.payload,
    )
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
            norm_text=norm_text,
            wire_payload=None,
            canonical_payload=None,
            reason_code=val_diag.get("reason_code") or "AMBIGUOUS_FACT",
            reason_detail=str(val_diag.get("rejected_ops") or val_diag.get("grounding_status")),
            failure_taxonomy=str(val_diag.get("failure_taxonomy") or "GROUNDING_REJECTED"),
            grounding_envelope=envelope,
            inference=inf_res,
        )

    wire_payload = to_wire_typed_fact_next_v2(canon_payload)
    norm_canon = _normalize_transport_payload(wire_payload)
    return LocalSlmExtractionResult(
        ok=True,
        strategy=eff_strategy,
        model_key=inf_res.model_key,
        model_sha256=inf_res.model_sha256,
        norm_text=norm_text,
        wire_payload=wire_payload,
        canonical_payload=norm_canon,
        reason_code=None,
        reason_detail=None,
        failure_taxonomy="NONE",
        grounding_envelope=envelope,
        inference=inf_res,
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
    ) -> None:
        self.model_key = resolve_local_slm_model_spec(model_key).model_key
        self.strategy = resolve_local_slm_strategy(strategy)
        self.runtime = runtime
        self.allow_download = bool(allow_download)
        self.threads = threads
        self.last_result: LocalSlmExtractionResult | None = None

    def extract(self, source_text: str) -> dict[str, Any] | None:
        res = run_local_slm_extraction(
            source_text,
            model_key=self.model_key,
            strategy=self.strategy,
            runtime=self.runtime,
            allow_download=self.allow_download,
            threads=self.threads,
        )
        self.last_result = res
        return res.canonical_payload


__all__ = [
    "DEFAULT_LOCAL_SLM_STRATEGY",
    "DIRECT_WIRE_JSON_SCHEMA",
    "IndexedClause",
    "LOCAL_SLM_EXTRACTOR_VERSION",
    "LocalSlmExtractionResult",
    "LocalSlmExtractor",
    "MINIMAL_OPS_JSON_SCHEMA",
    "SLM_GROUNDING_ENVELOPE_VERSION",
    "SLM_GROUNDING_VALIDATOR_VERSION",
    "SUPPORTED_SLM_STRATEGIES",
    "detect_prompt_injection",
    "extract_geometry_points",
    "index_source_clauses",
    "is_value_grounded_in_clause",
    "resolve_local_slm_strategy",
    "run_local_slm_extraction",
    "select_clean_quote",
    "validate_and_lower_minimal_ops",
]
