# -*- coding: utf-8 -*-
"""Deterministic local construction-step parser, dependency graph, and partial kernel rebuild engine.

Executes learner edits to Vietnamese geometry construction steps without calling
any external LLM or mutating unrelated steps:

    Edited Vietnamese Step
      -> Local Vietnamese Parser (zero-LLM, closed op grammar)
      -> Normalized Construction Intent & Equivalence Check
      -> Object/Step Dependency DAG + Cycle / Missing-Reference Gate
      -> Topological Partial Execution in Exact Kernel (Fraction / Radical / Gram Metric)
      -> Exact Geometric Predicate Verification & Continuity Validation
      -> Atomic Rebuild Snapshot (or fail-closed structured refusal)
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import time
import unicodedata
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from app.simulation.geometry import (
    GeometryError,
    Line3,
    Plane3,
    Point3,
    Segment3,
    Vec3,
    circumscribed_sphere,
    kernel as K,
    metric as _m,
    predicates as P,
)
from app.simulation.geometry import curved as CV
from app.simulation.geometry import measure as M
from app.simulation.geometry.curved import Circle3, CurvedSolid, Ellipse3
from app.simulation.geometry.radical import (
    Radical,
    RadicalDomainError,
    display as radical_display,
    parse_exact,
    sqrt_rational,
    to_json as radical_to_json,
)
from app.simulation.geometry.section import Polyhedron, Section, cross_section
from app.simulation.geometry_functions.construction_continuity import (
    enrich_construction_continuity,
    validate_construction_continuity,
)
from app.simulation.geometry_functions.registry import REGISTRY
from app.simulation.semantic_program.geometry_exec import area_of, lateral_area_of, volume_of
from app.simulation.semantic_program.scene3d import (
    RENDER_HINT,
    _attach_formulas,
    _attach_topology,
    _build_formation,
    _ke_lai,
)


STEP_EDITOR_VERSION = "step-editor/1"

_POINT_TOKEN_RE = re.compile(r"[A-Z][0-9]*'?")
_VERB_PREFIX_RE = re.compile(
    r"^(?:xác\s+định|gọi|lấy|chọn|dựng|kẻ|hạ|vẽ|nối|tìm|hoàn\s+thiện|cắt)\b",
    re.IGNORECASE,
)

# Registry operation mapping for provenance & feedback logging
OP_TO_REGISTRY: dict[str, tuple[str, ...]] = {
    "midpoint": ("midpoint",),
    "divide_segment": ("divide_segment",),
    "centroid": ("centroid",),
    "orthogonal_projection_plane": ("orthogonal_projection",),
    "orthogonal_projection_line": ("orthogonal_projection_line",),
    "perpendicular_bisector_plane": ("midpoint", "plane_perpendicular_to_line"),
    "plane_perpendicular_to_line": ("plane_perpendicular_to_line",),
    "plane_parallel_to_plane": ("plane_parallel_to_plane",),
    "plane_through_three_points": ("construct_plane",),
    "intersect_line_plane": ("intersect_line_plane",),
    "intersect_line_line": ("intersect_line_line",),
    "intersection_line": ("intersection_line",),
    "construct_segment": ("construct_segment",),
    "construct_line": ("construct_line",),
    "construct_polygon": ("construct_polygon",),
    "construct_solid": ("construct_solid",),
    "construct_section": ("section",),
    "ball_center_rim": ("curved_solid",),
    "circumscribed_sphere": ("curved_solid",),
}


class StepEditRefusal(Exception):
    """Fail-closed actionable refusal raised during parsing, planning, kernel execution, or validation."""

    def __init__(
        self,
        error_code: str,
        failed_stage: str,
        learner_error: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(f"{error_code}: {learner_error}")
        self.error_code = error_code
        self.failed_stage = failed_stage
        self.learner_error = learner_error
        self.details = dict(details or {})


@dataclass(frozen=True)
class AtomicClause:
    op: str
    output_symbol: str | None = None
    point_inputs: tuple[str, ...] = ()
    plane_inputs: tuple[str, ...] = ()
    line_inputs: tuple[str, ...] = ()
    solid_input: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    raw_clause: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "op": self.op,
            "output_symbol": self.output_symbol,
            "point_inputs": list(self.point_inputs),
            "plane_inputs": list(self.plane_inputs),
            "line_inputs": list(self.line_inputs),
            "solid_input": self.solid_input,
            "params": copy.deepcopy(self.params),
            "raw_clause": self.raw_clause,
        }


@dataclass(frozen=True)
class ParsedStepIntent:
    raw_text: str
    normalized_text: str
    clauses: tuple[AtomicClause, ...]
    registry_operations: tuple[str, ...]
    intent_signature: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "clauses": [c.to_dict() for c in self.clauses],
            "registry_operations": list(self.registry_operations),
            "intent_signature": self.intent_signature,
        }


def _normalize_vi_math(text: str) -> str:
    s = unicodedata.normalize("NFC", text or "")
    s = (
        s.replace("′", "'")
        .replace("’", "'")
        .replace("‘", "'")
        .replace("`", "'")
        .replace("⟂", " ⊥ ")
        .replace("∥", " // ")
        .replace("∩", " ∩ ")
    )
    greek_aliases = (
        ("alpha", "α"),
        ("beta", "β"),
        ("gamma", "γ"),
        ("delta", "δ"),
        ("phi", "φ"),
    )
    for word, sym in greek_aliases:
        s = re.sub(rf"\(\s*{word}\s*\)", f"({sym})", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _display_sym(sym: str) -> str:
    return sym.replace("'", "′")


def _extract_points(token: str) -> list[str]:
    return _POINT_TOKEN_RE.findall(_normalize_vi_math(token))


def _extract_segment_endpoints(token: str) -> list[str]:
    """Extract 2 endpoints from `AB`, `A'B'`, or lowercase segment reference like `ab`."""
    t = _normalize_vi_math(token).strip()
    pts = _POINT_TOKEN_RE.findall(t)
    if len(pts) == 2:
        return pts
    if re.fullmatch(r"[a-z][0-9]*'?[a-z][0-9]*'?", t):
        up_pts = _POINT_TOKEN_RE.findall(t.upper())
        if len(up_pts) == 2:
            return up_pts
    return pts


def _parse_point_ref_phrase(raw_phrase: str) -> tuple[str, dict[str, Any] | None] | None:
    """Parse point reference phrases such as `O`, `điểm O`, `tâm O`, `tâm O của hình vuông ABCD`,
    `trung điểm O của AC`, or `giao điểm O của AC và BD`. Returns `(point_symbol, role_assertion)`."""
    p = _normalize_vi_math(raw_phrase).strip(" ,.;:")
    if not p:
        return None
    pt_pat = r"[A-Z][0-9]*'?"
    # Case 1: bare point `"O"` or lowercase single letter `"o"`
    if re.fullmatch(r"[A-Za-z][0-9]*'?", p):
        return p.upper(), None
    # Case 2: `"điểm O"`
    m_pt = re.fullmatch(rf"(?:điểm|đỉnh)\s+(?P<pt>{pt_pat})", p, re.IGNORECASE)
    if m_pt:
        return m_pt.group("pt").upper(), None
    # Case 3: `"tâm O"` or `"tâm O của (hình vuông|hình chữ nhật|hình bình hành|mặt đáy|đáy) (ABCD)"`
    m_ctr_plain = re.fullmatch(rf"tâm(?:\s+(?:mặt\s+)?đáy)?\s+(?P<pt>{pt_pat})", p, re.IGNORECASE)
    if m_ctr_plain:
        return m_ctr_plain.group("pt").upper(), {
            "kind": "center",
            "pt": m_ctr_plain.group("pt").upper(),
            "shape": None,
            "target": None,
        }
    m_ctr2 = re.fullmatch(
        rf"tâm(?:\s+(?:mặt\s+)?đáy)?\s+(?P<pt>{pt_pat})"
        rf"\s+của\s+(?:(?P<shape>hình\s+vuông|hình\s+chữ\s+nhật|hình\s+bình\s+hành|mặt\s+đáy|đáy)\s+)?"
        rf"\(?(?P<poly>(?:{pt_pat}){{3,}})\)?",
        p,
        re.IGNORECASE,
    )
    if m_ctr2:
        shape_raw = (m_ctr2.group("shape") or "").strip().lower() or None
        return m_ctr2.group("pt").upper(), {
            "kind": "center",
            "pt": m_ctr2.group("pt").upper(),
            "shape": shape_raw,
            "target": m_ctr2.group("poly").upper(),
        }
    # Case 4: `"trung điểm O của AC"`
    m_mid = re.fullmatch(
        rf"(?:trung\s+điểm|điểm\s+chính\s+giữa)\s+(?P<pt>{pt_pat})\s+(?:của\s+)?(?:cạnh\s+|đoạn\s+thẳng\s+|đoạn\s+|đường\s+chéo\s+)?(?P<seg>[A-Za-z][0-9]*'?[A-Za-z][0-9]*'?)",
        p,
        re.IGNORECASE,
    )
    if m_mid:
        eps = _extract_segment_endpoints(m_mid.group("seg"))
        if len(eps) == 2 and eps[0] != eps[1]:
            return m_mid.group("pt").upper(), {
                "kind": "midpoint",
                "pt": m_mid.group("pt").upper(),
                "a": eps[0],
                "b": eps[1],
            }
    # Case 5: `"giao điểm O của AC và BD"`
    m_inter = re.fullmatch(
        rf"giao\s+điểm\s+(?P<pt>{pt_pat})\s+(?:của\s+)?(?:đường\s+thẳng\s+|đường\s+chéo\s+|hai\s+đường\s+chéo\s+|cạnh\s+)?(?P<l1>[A-Za-z][0-9]*'?[A-Za-z][0-9]*'?)\s+(?:và|với)\s+(?:đường\s+thẳng\s+|đường\s+chéo\s+|cạnh\s+)?(?P<l2>[A-Za-z][0-9]*'?[A-Za-z][0-9]*'?)",
        p,
        re.IGNORECASE,
    )
    if m_inter:
        l1 = _extract_segment_endpoints(m_inter.group("l1"))
        l2 = _extract_segment_endpoints(m_inter.group("l2"))
        if len(l1) == 2 and len(l2) == 2 and l1[0] != l1[1] and l2[0] != l2[1]:
            return m_inter.group("pt").upper(), {
                "kind": "intersection",
                "pt": m_inter.group("pt").upper(),
                "line1": l1,
                "line2": l2,
            }
    # Case 6: `"chân đường cao H"` / `"hình chiếu H"`
    m_foot = re.fullmatch(
        rf"(?:chân\s+đường\s+(?:cao|vuông\s+góc)|hình\s+chiếu(?:\s+vuông\s+góc)?)\s+(?P<pt>{pt_pat})",
        p,
        re.IGNORECASE,
    )
    if m_foot:
        return m_foot.group("pt").upper(), None
    return None


def _canon_plane_name(raw: str | None) -> str | None:
    if not raw:
        return None
    s = _normalize_vi_math(raw).strip()
    if s.startswith("(") and s.endswith(")"):
        return s
    return f"({s})"


def _split_compound_clauses(norm_text: str) -> list[str]:
    """Split multi-clause Vietnamese construction sentences safely without breaking vertex lists or coordinates."""
    cleaned = norm_text.rstrip(".").strip()
    if not cleaned:
        return []
    # Normalize explicit sequential connectors into a sentinel before verb phrases
    marked = re.sub(
        r"\s*(?:;|,(?=\s*(?:xác\s+định|gọi|lấy|chọn|dựng|kẻ|hạ|vẽ|nối|tìm)\b)|"
        r"\b(?:rồi|sau\s+đó|từ\s+đó|để)\b(?=\s*(?:xác\s+định|gọi|lấy|chọn|dựng|kẻ|hạ|vẽ|nối|tìm)\b))\s*",
        " || ",
        cleaned,
        flags=re.IGNORECASE,
    )
    # Also split `"và <verb>..."` when preceded by a construction clause
    marked = re.sub(
        r"\s+\bvà\b\s+(?=(?:xác\s+định|gọi|lấy|chọn|dựng|kẻ|hạ|vẽ|nối|tìm)\b)",
        " || ",
        marked,
        flags=re.IGNORECASE,
    )
    parts: list[str] = []
    pt_pat = r"[A-Z][0-9]*'?"
    seg_pat = r"[A-Z][0-9]*'?[A-Z][0-9]*'?"
    plane_pat = r"\([^()]+\)|[A-Z][0-9]*'?(?:[A-Z][0-9]*'?){2,}|[α-ω]'?"
    inline_mid_re = re.compile(
        rf"^(?:dựng|vẽ|xác\s+định)\s+(?:mặt\s+phẳng|mp)\s*(?P<pname>{plane_pat})?\s*"
        rf"(?:đi\s+)?qua\s+trung\s+điểm\s+(?P<pt>{pt_pat})\s+(?:của\s+)?(?:cạnh\s+|đoạn\s+thẳng\s+|đoạn\s+)?(?P<seg>{seg_pat})"
        rf"\s*(?:và|,)?\s*(?:vuông\s+góc\s+(?:với\s+)?|⊥\s*)(?:(?:cạnh|đoạn\s+thẳng|đoạn|đường\s+thẳng|đt)\s+)?(?P<line>{seg_pat}|[a-zΔ][0-9']*)$",
        re.IGNORECASE,
    )
    for raw_p in marked.split("||"):
        p = raw_p.strip(" ,.;")
        if not p:
            continue
        m_inline = inline_mid_re.fullmatch(p)
        if m_inline:
            pt = m_inline.group("pt")
            seg = m_inline.group("seg")
            pname = (m_inline.group("pname") or "").strip()
            line = m_inline.group("line").strip()
            parts.append(f"Xác định trung điểm {pt} của {seg}")
            p_lbl = f" {pname}" if pname else ""
            parts.append(f"Dựng mặt phẳng{p_lbl} đi qua {pt} và vuông góc với {line}")
        else:
            parts.append(p)
    return parts


def _parse_ratio_fraction(raw: str) -> Fraction | None:
    s = _normalize_vi_math(raw).replace(" ", "").replace(",", ".")
    if not s:
        return None
    try:
        return Fraction(s)
    except (ValueError, ZeroDivisionError):
        return None


def _resolve_divide_segment_ratio(seg_pts: tuple[str, str], pt: str, expr_rhs: str) -> tuple[str, str, Fraction]:
    """Parse ratio equations like `SM = 1/3 SA`, `AM/AB = 2/3`, `SM = 2 MA` into `(a, b, t)` with P = (1-t)*a + t*b."""
    a, b = seg_pts
    e = _normalize_vi_math(expr_rhs)
    # Form 1: X/Y = k  (e.g. "SM/SA = 1/3", "AM/AB = 2/3")
    m_div = re.fullmatch(
        r"(?P<s1>[A-Z][0-9]*'?[A-Z][0-9]*'?)\s*/\s*(?P<s2>[A-Z][0-9]*'?[A-Z][0-9]*'?)\s*=\s*(?P<k>[\d.,/]+)",
        e,
    )
    if m_div:
        k = _parse_ratio_fraction(m_div.group("k"))
        p1 = tuple(_extract_points(m_div.group("s1")))
        p2 = tuple(_extract_points(m_div.group("s2")))
        if k is None or len(p1) != 2 or len(p2) != 2:
            raise StepEditRefusal(
                "INVALID_RATIO",
                "parser",
                f"Tỉ số chia đoạn '{e}' không đúng định dạng phân số hợp lệ.",
            )
        if pt not in p1 or set(p2) != {a, b}:
            raise StepEditRefusal(
                "INVALID_RATIO",
                "parser",
                f"Biểu thức tỉ số '{e}' không khớp với điểm {pt} trên đoạn {a}{b}.",
            )
        anchor = next(x for x in p1 if x != pt)
        other = b if anchor == a else a
        if not (Fraction(0) < k < Fraction(1)):
            raise StepEditRefusal(
                "INVALID_RATIO",
                "parser",
                f"Tỉ số {e} cho t = {k} nằm ngoài đoạn {a}{b} (cần 0 < t < 1).",
            )
        return anchor, other, k

    # Form 2: seg1 = k seg2  (e.g. "SM = 1/3 SA", "SM = 2 MA", "AM = 2 MB", "MA = 2MB")
    m_eq = re.fullmatch(
        r"(?P<s1>[A-Z][0-9]*'?[A-Z][0-9]*'?)\s*=\s*(?P<k>[\d.,/]+)?\s*\*?\s*(?P<s2>[A-Z][0-9]*'?[A-Z][0-9]*'?)",
        e,
    )
    if m_eq:
        k = _parse_ratio_fraction(m_eq.group("k") or "1")
        p1 = tuple(_extract_points(m_eq.group("s1")))
        p2 = tuple(_extract_points(m_eq.group("s2")))
        if k is None or k <= 0 or len(p1) != 2 or len(p2) != 2 or p1[0] == p1[1] or p2[0] == p2[1]:
            raise StepEditRefusal(
                "INVALID_RATIO",
                "parser",
                f"Hệ thức chia đoạn '{e}' không hợp lệ.",
            )
        if set(p1) == {a, pt} and set(p2) == {a, b}:
            if not (Fraction(0) < k < Fraction(1)):
                raise StepEditRefusal("INVALID_RATIO", "parser", f"Hệ thức '{e}' phải có tỉ số trong (0, 1).")
            return a, b, k
        if set(p1) == {b, pt} and set(p2) == {a, b}:
            if not (Fraction(0) < k < Fraction(1)):
                raise StepEditRefusal("INVALID_RATIO", "parser", f"Hệ thức '{e}' phải có tỉ số trong (0, 1).")
            return b, a, k
        if set(p1) == {a, pt} and set(p2) == {pt, b}:
            return a, b, k / (k + 1)
        if set(p1) == {b, pt} and set(p2) == {pt, a}:
            return b, a, k / (k + 1)
        if set(p1) == {a, b} and set(p2) == {a, pt}:
            t = Fraction(1) / k
            if not (Fraction(0) < t < Fraction(1)):
                raise StepEditRefusal("INVALID_RATIO", "parser", f"Hệ thức '{e}' đẩy điểm {pt} ra ngoài đoạn {a}{b}.")
            return a, b, t
        if set(p1) == {a, b} and set(p2) == {b, pt}:
            t = Fraction(1) / k
            if not (Fraction(0) < t < Fraction(1)):
                raise StepEditRefusal("INVALID_RATIO", "parser", f"Hệ thức '{e}' đẩy điểm {pt} ra ngoài đoạn {a}{b}.")
            return b, a, t

    raise StepEditRefusal(
        "INVALID_RATIO",
        "parser",
        f"Chưa hiểu hệ thức chia đoạn '{e}'. Ví dụ hợp lệ: 'SM = 1/3 SA' hoặc 'AM = 2 MB'.",
    )


def _parse_single_clause(clause: str) -> AtomicClause:
    c = _normalize_vi_math(clause).strip(" .;:")
    if not c:
        raise StepEditRefusal("EMPTY_STEP_INSTRUCTION", "parser", "Mệnh đề bước dựng không được để trống.")

    pt_pat = r"[A-Z][0-9]*'?"
    seg_pat = r"[A-Z][0-9]*'?[A-Z][0-9]*'?"
    seg_or_pair_pat = r"[A-Z][0-9]*'?[A-Z][0-9]*'?|[A-Z][0-9]*'?\s*(?:,|và)\s*[A-Z][0-9]*'?"
    plane_pat = r"\([^()]+\)|[A-Z][0-9]*'?(?:[A-Z][0-9]*'?){2,}|[α-ω]'?"

    # 1a. Midpoint: "Xác định/Gọi/Lấy trung điểm H của AB" / "Xác định điểm chính giữa H của AB"
    m = re.fullmatch(
        rf"(?:xác\s+định|gọi|lấy|chọn|dựng)\s+(?:trung\s+điểm|điểm\s+chính\s+giữa)\s+(?P<pt>{pt_pat})\s+(?:của\s+)?(?:cạnh\s+|đoạn\s+thẳng\s+|đoạn\s+)?(?P<seg>{seg_or_pair_pat})",
        c,
        re.IGNORECASE,
    )
    if m:
        pts = _extract_points(m.group("seg"))
        if len(pts) != 2 or pts[0] == pts[1]:
            raise StepEditRefusal("INVALID_OPERAND", "parser", f"Đoạn thẳng '{m.group('seg')}' cần đúng hai đầu mút phân biệt.")
        return AtomicClause(
            op="midpoint",
            output_symbol=m.group("pt"),
            point_inputs=(pts[0], pts[1]),
            raw_clause=clause,
        )

    # 1b. Midpoint reverse wording: "Gọi H là trung điểm (của) AB"
    m = re.fullmatch(
        rf"(?:xác\s+định|gọi|lấy|chọn|dựng)\s+(?:điểm\s+)?(?P<pt>{pt_pat})\s+là\s+(?:trung\s+điểm|điểm\s+chính\s+giữa)\s+(?:của\s+)?(?:cạnh\s+|đoạn\s+thẳng\s+|đoạn\s+)?(?P<seg>{seg_or_pair_pat})",
        c,
        re.IGNORECASE,
    )
    if m:
        pts = _extract_points(m.group("seg"))
        if len(pts) != 2 or pts[0] == pts[1]:
            raise StepEditRefusal("INVALID_OPERAND", "parser", f"Đoạn thẳng '{m.group('seg')}' cần đúng hai đầu mút phân biệt.")
        return AtomicClause(
            op="midpoint",
            output_symbol=m.group("pt"),
            point_inputs=(pts[0], pts[1]),
            raw_clause=clause,
        )

    # 2. Ratio point on segment: "Lấy điểm M thuộc/trên cạnh SA sao cho SM = 1/3 SA"
    m = re.fullmatch(
        rf"(?:lấy|xác\s+định|gọi|chọn)\s+(?:điểm\s+)?(?P<pt>{pt_pat})\s+(?:thuộc|trên|nằm\s+trên)\s+(?:cạnh\s+|đoạn\s+thẳng\s+|đoạn\s+)?(?P<seg>{seg_pat})\s+(?:sao\s+cho|thỏa\s+mãn)\s+(?P<expr>.+)",
        c,
        re.IGNORECASE,
    )
    if m:
        pts = _extract_points(m.group("seg"))
        if len(pts) != 2 or pts[0] == pts[1]:
            raise StepEditRefusal("INVALID_OPERAND", "parser", f"Đoạn '{m.group('seg')}' không hợp lệ.")
        pt = m.group("pt")
        a, b, ratio_q = _resolve_divide_segment_ratio((pts[0], pts[1]), pt, m.group("expr"))
        return AtomicClause(
            op="divide_segment",
            output_symbol=pt,
            point_inputs=(a, b),
            params={"a": a, "b": b, "ratio": str(ratio_q)},
            raw_clause=clause,
        )

    # 3. Centroid: "Xác định trọng tâm G của tam giác ABC"
    m = re.fullmatch(
        rf"(?:xác\s+định|gọi|lấy|chọn|dựng)\s+(?:(?P<pt>{pt_pat})\s+là\s+)?trọng\s+tâm\s+(?:(?P<pt2>{pt_pat})\s+)?(?:của\s+)?(?:tam\s+giác\s+|Δ\s*)?(?P<poly>(?:{pt_pat}){{3}})",
        c,
        re.IGNORECASE,
    )
    if m:
        pt = m.group("pt") or m.group("pt2")
        pts = _extract_points(m.group("poly"))
        if pt and len(pts) == 3 and len(set(pts)) == 3:
            return AtomicClause(
                op="centroid",
                output_symbol=pt,
                point_inputs=tuple(pts),
                raw_clause=clause,
            )

    # 4. Perpendicular bisector plane: "Dựng mặt phẳng trung trực (α) của cạnh AB"
    m = re.fullmatch(
        rf"(?:dựng|vẽ|xác\s+định|gọi)\s+(?:(?:mặt\s+phẳng|mp)\s+trung\s+trực\s+(?P<pname>{plane_pat})?|(?P<pname2>{plane_pat})\s+là\s+(?:mặt\s+phẳng|mp)\s+trung\s+trực)\s+(?:của\s+)?(?:cạnh\s+|đoạn\s+thẳng\s+|đoạn\s+)?(?P<seg>{seg_pat})",
        c,
        re.IGNORECASE,
    )
    if m:
        pts = _extract_points(m.group("seg"))
        if len(pts) != 2 or pts[0] == pts[1]:
            raise StepEditRefusal("INVALID_OPERAND", "parser", f"Cạnh '{m.group('seg')}' cần đúng hai điểm phân biệt.")
        pname = _canon_plane_name(m.group("pname") or m.group("pname2"))
        return AtomicClause(
            op="perpendicular_bisector_plane",
            output_symbol=pname,
            point_inputs=(pts[0], pts[1]),
            raw_clause=clause,
        )

    # 5a. Plane through point (incl. role qualifiers: "tâm O", "tâm O của hình vuông ABCD", "Dựng (α) đi qua O...") perpendicular to AB:
    m = re.fullmatch(
        rf"(?:(?:dựng|vẽ|xác\s+định)\s+(?:mặt\s+phẳng|mp)\s*(?P<pname>{plane_pat})?"
        rf"|(?:dựng|vẽ|xác\s+định)\s+(?P<pname_bare>{plane_pat})"
        rf"|(?:mặt\s+phẳng|mp)\s+(?P<pname_np>{plane_pat})"
        rf"|gọi\s+(?P<pname2>{plane_pat})\s+là\s+(?:mặt\s+phẳng|mp))"
        rf"\s+(?:đi\s+)?qua\s+(?P<pt_phrase>.+?)\s+(?:và|rồi|,)?\s*(?:vuông\s+góc\s+(?:với\s+)?|⊥\s*)(?:(?:cạnh|đoạn\s+thẳng|đoạn|đường\s+thẳng|đt)\s+)?(?P<line>{seg_pat}|[a-z][0-9']*'?[a-z][0-9']*'?|[a-zΔ][0-9']*)",
        c,
        re.IGNORECASE,
    )
    if m:
        parsed_pt = _parse_point_ref_phrase(m.group("pt_phrase"))
        if parsed_pt is not None:
            pt_sym, role_assertion = parsed_pt
            pname = _canon_plane_name(
                m.group("pname") or m.group("pname_bare") or m.group("pname_np") or m.group("pname2")
            )
            line_tok = m.group("line").strip()
            lpts = _extract_segment_endpoints(line_tok)
            if len(lpts) == 2 and lpts[0] == lpts[1]:
                raise StepEditRefusal("INVALID_OPERAND", "parser", f"Đường thẳng '{line_tok}' cần hai điểm phân biệt.")
            params_5a: dict[str, Any] = {}
            if role_assertion is not None:
                params_5a["point_role_assertion"] = role_assertion
            return AtomicClause(
                op="plane_perpendicular_to_line",
                output_symbol=pname,
                point_inputs=(pt_sym, *(lpts if len(lpts) == 2 else ())),
                line_inputs=() if len(lpts) == 2 else (line_tok,),
                params=params_5a,
                raw_clause=clause,
            )

    # 5b. Reverse clause order: "Dựng mặt phẳng (α) vuông góc với AB tại H" / "qua tâm O vuông góc với AB"
    m = re.fullmatch(
        rf"(?:(?:dựng|vẽ|xác\s+định)\s+(?:(?:mặt\s+phẳng|mp)\s*)?(?P<pname>{plane_pat})?|(?:mặt\s+phẳng|mp)\s+(?P<pname_np>{plane_pat}))\s*(?:vuông\s+góc\s+(?:với\s+)?|⊥\s*)(?:(?:cạnh|đoạn\s+thẳng|đoạn|đường\s+thẳng|đt)\s+)?(?P<line>{seg_pat}|[a-z][0-9']*'?[a-z][0-9']*'?|[a-zΔ][0-9']*)\s+(?:tại|đi\s+qua|qua)\s+(?P<pt_phrase>.+)",
        c,
        re.IGNORECASE,
    )
    if m:
        parsed_pt = _parse_point_ref_phrase(m.group("pt_phrase"))
        if parsed_pt is not None:
            pt_sym, role_assertion = parsed_pt
            pname = _canon_plane_name(m.group("pname") or m.group("pname_np"))
            line_tok = m.group("line").strip()
            lpts = _extract_segment_endpoints(line_tok)
            if len(lpts) == 2 and lpts[0] == lpts[1]:
                raise StepEditRefusal("INVALID_OPERAND", "parser", f"Đường thẳng '{line_tok}' cần hai điểm phân biệt.")
            params_5b: dict[str, Any] = {}
            if role_assertion is not None:
                params_5b["point_role_assertion"] = role_assertion
            return AtomicClause(
                op="plane_perpendicular_to_line",
                output_symbol=pname,
                point_inputs=(pt_sym, *(lpts if len(lpts) == 2 else ())),
                line_inputs=() if len(lpts) == 2 else (line_tok,),
                params=params_5b,
                raw_clause=clause,
            )

    # 6. Plane through point parallel to another plane: "Dựng mặt phẳng (α) qua M song song với (ABCD)"
    m = re.fullmatch(
        rf"(?:dựng|vẽ|xác\s+định)\s+(?:mặt\s+phẳng|mp)\s*(?P<pname>{plane_pat})?\s*(?:đi\s+)?qua\s+(?:điểm\s+)?(?P<pt>{pt_pat})\s+(?:và\s+)?(?:song\s+song\s+(?:với\s+)?|//\s*)(?:(?:mặt\s+phẳng|mặt|mp)\s+)?(?P<ref>{plane_pat})",
        c,
        re.IGNORECASE,
    )
    if m:
        pname = _canon_plane_name(m.group("pname"))
        ref = _canon_plane_name(m.group("ref")) or m.group("ref")
        return AtomicClause(
            op="plane_parallel_to_plane",
            output_symbol=pname,
            point_inputs=(m.group("pt"),),
            plane_inputs=(ref,),
            raw_clause=clause,
        )

    # 7a. Plane through named points: "Dựng mặt phẳng (P) đi qua ba điểm M, N, P"
    m = re.fullmatch(
        rf"(?:dựng|vẽ|xác\s+định)\s+(?:mặt\s+phẳng|mp)\s*(?P<pname>{plane_pat})?\s*(?:đi\s+)?qua\s+(?:ba\s+|3\s+)?điểm\s+(?P<pts>.+)",
        c,
        re.IGNORECASE,
    )
    if m:
        pts = _extract_points(m.group("pts"))
        if len(pts) < 3:
            raise StepEditRefusal("INSUFFICIENT_POINTS", "parser", "Cần ít nhất 3 điểm phân biệt để xác định mặt phẳng.")
        pname = _canon_plane_name(m.group("pname")) or f"({''.join(pts)})"
        return AtomicClause(
            op="plane_through_three_points",
            output_symbol=pname,
            point_inputs=tuple(pts),
            raw_clause=clause,
        )

    # 7b. Plane named by points directly: "Dựng mặt phẳng (MNP)" / "Dựng (MNP)"
    m = re.fullmatch(
        rf"(?:dựng|vẽ|xác\s+định)\s+(?:(?:mặt\s+phẳng|mp|mặt\s+đáy|đáy)\s+)?\((?P<pts>(?:{pt_pat}){{3,}})\)",
        c,
        re.IGNORECASE,
    )
    if m:
        pts = _extract_points(m.group("pts"))
        if len(pts) >= 3:
            return AtomicClause(
                op="plane_through_three_points",
                output_symbol=f"({''.join(pts)})",
                point_inputs=tuple(pts),
                raw_clause=clause,
            )

    # 8a. Orthogonal projection onto plane/line: "Hạ/Xác định hình chiếu vuông góc H của A lên (SBC)"
    m = re.fullmatch(
        rf"(?:hạ|kẻ|dựng|xác\s+định|gọi)\s+(?:hình\s+chiếu(?:\s+vuông\s+góc)?|chân\s+đường\s+(?:vuông\s+góc|cao))\s+(?P<img>{pt_pat})\s+của\s+(?:điểm\s+)?(?P<pt>{pt_pat})\s+(?:lên|xuống|trên)\s+(?P<kind>mặt\s+phẳng|mp|đường\s+thẳng|đt|cạnh|đoạn)?\s*(?P<target>.+)",
        c,
        re.IGNORECASE,
    )
    if m:
        target_raw = m.group("target").strip()
        kind_kw = (m.group("kind") or "").lower()
        t_pts = _extract_points(target_raw)
        is_line = kind_kw in ("đường thẳng", "đt", "cạnh", "đoạn") or (
            not target_raw.startswith("(") and len(t_pts) == 2
        )
        if is_line:
            return AtomicClause(
                op="orthogonal_projection_line",
                output_symbol=m.group("img"),
                point_inputs=(m.group("pt"), *(t_pts if len(t_pts) == 2 else ())),
                line_inputs=() if len(t_pts) == 2 else (target_raw,),
                raw_clause=clause,
            )
        return AtomicClause(
            op="orthogonal_projection_plane",
            output_symbol=m.group("img"),
            point_inputs=(m.group("pt"),),
            plane_inputs=(_canon_plane_name(target_raw) or target_raw,),
            raw_clause=clause,
        )

    # 8b. Altitude / Drop perpendicular: "Dựng đường cao SA ⊥ (ABCD) tại A" / "Kẻ đường cao SH vuông góc với mặt phẳng (ABCD)"
    m = re.fullmatch(
        rf"(?:dựng|hạ|kẻ)\s+(?:đường\s+cao|đoạn\s+vuông\s+góc|đoạn)?\s*(?P<seg>{seg_pat})\s*(?:vuông\s+góc\s+(?:với\s+)?|⊥\s*)(?:mặt\s+phẳng\s+|mp\s+|mặt\s+đáy\s+|đáy\s+|đường\s+thẳng\s+|cạnh\s+)?(?P<target>{plane_pat}|[a-zΔ][0-9']*)(?:\s+tại\s+(?P<foot>{pt_pat}))?",
        c,
        re.IGNORECASE,
    )
    if m:
        seg_pts = _extract_points(m.group("seg"))
        foot = m.group("foot") or (seg_pts[1] if len(seg_pts) == 2 else None)
        if len(seg_pts) == 2 and foot and foot in seg_pts:
            other = seg_pts[1] if seg_pts[0] == foot else seg_pts[0]
            target_raw = m.group("target").strip()
            t_pts = _extract_points(target_raw)
            if not target_raw.startswith("(") and len(t_pts) == 2:
                return AtomicClause(
                    op="orthogonal_projection_line",
                    output_symbol=foot,
                    point_inputs=(other, *t_pts),
                    params={"segment_symbol": m.group("seg"), "is_altitude": "đường cao" in c.lower()},
                    raw_clause=clause,
                )
            return AtomicClause(
                op="orthogonal_projection_plane",
                output_symbol=foot,
                point_inputs=(other,),
                plane_inputs=(_canon_plane_name(target_raw) or target_raw,),
                params={"segment_symbol": m.group("seg"), "is_altitude": "đường cao" in c.lower()},
                raw_clause=clause,
            )

    # 9a. Line-plane or line-line intersection: "Xác định giao điểm E của SB với (MNP)" / "Tìm giao điểm E của đường thẳng MN và đường thẳng CD"
    m = re.fullmatch(
        rf"(?:(?:xác\s+định|tìm|gọi)\s+giao\s+điểm\s+(?P<pt>{pt_pat})\s+của\s+(?:cạnh\s+|đoạn\s+|đường\s+thẳng\s+|đt\s+)?(?P<l1>{seg_pat}|[a-zΔ][0-9']*)\s+(?:và|với)\s+(?:(?P<k2>mặt\s+phẳng|mp|cạnh|đoạn|đường\s+thẳng|đt)\s+)?(?P<t2>{plane_pat}|{seg_pat}|[a-zΔ][0-9']*)|(?:gọi|xác\s+định)\s+(?P<pt_b>{pt_pat})\s*=\s*(?P<l1_b>{seg_pat}|[a-zΔ][0-9']*)\s*∩\s*(?P<t2_b>{plane_pat}|{seg_pat}|[a-zΔ][0-9']*))",
        c,
        re.IGNORECASE,
    )
    if m:
        pt = m.group("pt") or m.group("pt_b")
        l1 = (m.group("l1") or m.group("l1_b")).strip()
        k2 = (m.group("k2") or "").lower()
        t2 = (m.group("t2") or m.group("t2_b")).strip()
        l1_pts = _extract_points(l1)
        t2_pts = _extract_points(t2)
        if k2 in ("cạnh", "đoạn", "đường thẳng", "đt") or (not t2.startswith("(") and len(t2_pts) == 2):
            return AtomicClause(
                op="intersect_line_line",
                output_symbol=pt,
                point_inputs=(*(l1_pts if len(l1_pts) == 2 else ()), *(t2_pts if len(t2_pts) == 2 else ())),
                line_inputs=(
                    *((() if len(l1_pts) == 2 else (l1,))),
                    *((() if len(t2_pts) == 2 else (t2,))),
                ),
                params={"line1": l1, "line2": t2},
                raw_clause=clause,
            )
        return AtomicClause(
            op="intersect_line_plane",
            output_symbol=pt,
            point_inputs=tuple(l1_pts) if len(l1_pts) == 2 else (),
            line_inputs=() if len(l1_pts) == 2 else (l1,),
            plane_inputs=(_canon_plane_name(t2) or t2,),
            params={"line": l1},
            raw_clause=clause,
        )

    # 9b. Plane-plane intersection line: "Dựng giao tuyến (d) của (α) và (β)" / "Tìm giao tuyến d của mặt phẳng (SBC) và mặt phẳng (MNP)"
    m = re.fullmatch(
        rf"(?:dựng|vẽ|tìm|xác\s+định)\s+(?:giao\s+tuyến|trục[^()]*?là\s+giao\s+tuyến)\s*(?P<lname>\([^()]+\)|[a-zΔ][0-9']*)?\s*(?:của\s+)?(?:(?:hai\s+)?(?:mặt\s+phẳng|mp)\s+)?(?P<p1>{plane_pat})\s+(?:và|với)\s+(?:(?:mặt\s+phẳng|mp)\s+)?(?P<p2>{plane_pat})",
        c,
        re.IGNORECASE,
    )
    if m:
        return AtomicClause(
            op="intersection_line",
            output_symbol=(m.group("lname") or "").strip("() ") or None,
            plane_inputs=(_canon_plane_name(m.group("p1")) or m.group("p1"), _canon_plane_name(m.group("p2")) or m.group("p2")),
            raw_clause=clause,
        )

    # 10. Base polygon / lateral edges / solid / section / sphere / segment / line
    m = re.fullmatch(
        r"(?:dựng|vẽ)\s+(?:mặt\s+)?đáy\s+(?P<poly>(?:[A-Z][0-9]*'?){3,})",
        c,
        re.IGNORECASE,
    )
    if m:
        pts = _extract_points(m.group("poly"))
        return AtomicClause(
            op="construct_polygon",
            output_symbol=f"Đáy {''.join(_display_sym(p) for p in pts)}",
            point_inputs=tuple(pts),
            raw_clause=clause,
        )

    m = re.fullmatch(
        r"(?:dựng|vẽ|nối)\s+(?:các\s+)?cạnh\s+bên\s+(?P<segs>.+)",
        c,
        re.IGNORECASE,
    )
    if m:
        segs = [s.strip() for s in m.group("segs").split(",") if s.strip()]
        all_pts: list[str] = []
        pairs: list[list[str]] = []
        for s in segs:
            pts = _extract_points(s)
            if len(pts) != 2:
                raise StepEditRefusal("INVALID_OPERAND", "parser", f"Cạnh '{s}' cần đúng hai điểm đầu mút.")
            pairs.append(pts)
            for p in pts:
                if p not in all_pts:
                    all_pts.append(p)
        return AtomicClause(
            op="construct_segment",
            output_symbol=", ".join(segs),
            point_inputs=tuple(all_pts),
            params={"segments": pairs},
            raw_clause=clause,
        )

    m = re.fullmatch(
        r"(?:dựng|vẽ|nối)\s+(?:đoạn\s+thẳng\s+|đoạn\s+)?(?P<seg>[A-Z][0-9]*'?[A-Z][0-9]*'?)",
        c,
        re.IGNORECASE,
    )
    if m:
        pts = _extract_points(m.group("seg"))
        if len(pts) != 2 or pts[0] == pts[1]:
            raise StepEditRefusal("INVALID_OPERAND", "parser", f"Đoạn thẳng '{m.group('seg')}' cần đúng hai đầu mút phân biệt.")
        return AtomicClause(
            op="construct_segment",
            output_symbol=f"{pts[0]}{pts[1]}",
            point_inputs=(pts[0], pts[1]),
            params={"segments": [pts]},
            raw_clause=clause,
        )

    m = re.fullmatch(
        r"(?:hoàn\s+thiện|dựng|vẽ)\s+(?:đa\s+giác(?:\s+thiết\s+diện)?|tam\s+giác|tứ\s+giác|ngũ\s+giác)\s+(?P<poly>(?:[A-Z][0-9]*'?){3,})",
        c,
        re.IGNORECASE,
    )
    if m:
        pts = _extract_points(m.group("poly"))
        return AtomicClause(
            op="construct_polygon",
            output_symbol="".join(_display_sym(p) for p in pts),
            point_inputs=tuple(pts),
            raw_clause=clause,
        )

    m = re.fullmatch(
        rf"(?:dựng|vẽ|kẻ)\s+(?:đường\s+thẳng|đt)\s*(?P<lname>[a-zΔ][0-9']*|\([^()]+\))?\s*(?:đi\s+)?qua\s+(?:điểm\s+)?(?P<pt>{pt_pat})\s+(?:và\s+)?(?:vuông\s+góc\s+(?:với\s+)?|⊥\s*)(?:(?:mặt\s+phẳng|mp|đáy)\s+)?(?P<pl>{plane_pat})",
        c,
        re.IGNORECASE,
    )
    if m:
        return AtomicClause(
            op="construct_line",
            output_symbol=(m.group("lname") or "Δ").strip("() "),
            point_inputs=(m.group("pt"),),
            plane_inputs=(_canon_plane_name(m.group("pl")) or m.group("pl"),),
            params={"mode": "perpendicular_to_plane"},
            raw_clause=clause,
        )

    m = re.fullmatch(
        r"(?:dựng|vẽ)\s+(?:đường\s+thẳng|đt)\s+(?:qua\s+hai\s+điểm\s+)?(?P<seg>[A-Z][0-9]*'?[A-Z][0-9]*'?|[A-Z][0-9]*'?\s*(?:,|và)\s*[A-Z][0-9]*'?)",
        c,
        re.IGNORECASE,
    )
    if m:
        pts = _extract_points(m.group("seg"))
        if len(pts) != 2 or pts[0] == pts[1]:
            raise StepEditRefusal("INVALID_OPERAND", "parser", "Đường thẳng cần đúng hai điểm phân biệt.")
        return AtomicClause(
            op="construct_line",
            output_symbol=f"{pts[0]}{pts[1]}",
            point_inputs=(pts[0], pts[1]),
            raw_clause=clause,
        )

    m = re.fullmatch(
        rf"(?:dựng|vẽ|tạo|xác\s+định)\s+thiết\s+diện(?:\s+[^()]+?)?\s+(?:cắt\s+bởi|của\s+mặt\s+phẳng|bởi)\s+(?:mặt\s+phẳng\s+|mp\s+)?(?P<plane>{plane_pat})",
        c,
        re.IGNORECASE,
    )
    if m:
        return AtomicClause(
            op="construct_section",
            plane_inputs=(_canon_plane_name(m.group("plane")) or m.group("plane"),),
            raw_clause=clause,
        )

    m = re.fullmatch(
        rf"(?:xác\s+định|gọi|tìm)\s+tâm\s+mặt\s+cầu\s+ngoại\s+tiếp\s+(?P<pt>{pt_pat})\s+của\s+(?:hình\s+chóp\s+|khối\s+chóp\s+|lăng\s+trụ\s+|tứ\s+diện\s+)?(?P<solid>(?:[A-Z][0-9]*'?)+(?:\.(?:[A-Z][0-9]*'?)+)?)",
        c,
        re.IGNORECASE,
    )
    if m:
        return AtomicClause(
            op="circumscribed_sphere",
            output_symbol=m.group("pt"),
            solid_input=m.group("solid"),
            point_inputs=(m.group("pt"),),
            params={"target_kind": "center_point"},
            raw_clause=clause,
        )

    m = re.fullmatch(
        rf"(?:dựng|vẽ)\s+mặt\s+cầu(?:\s+ngoại\s+tiếp|\s+nội\s+tiếp)?\s*(?P<sname>\([^()]+\))?\s*tâm\s+(?P<center>{pt_pat})(?:\s*(?:,|và)?\s*(?:đi\s+)?qua\s+(?P<rim>{pt_pat}))?",
        c,
        re.IGNORECASE,
    )
    if m:
        op = "circumscribed_sphere" if "ngoại tiếp" in c.lower() else "ball_center_rim"
        pts = [m.group("center")] + ([m.group("rim")] if m.group("rim") else [])
        return AtomicClause(
            op=op,
            output_symbol=m.group("sname") or "(S)",
            point_inputs=tuple(pts),
            raw_clause=clause,
        )

    m = re.fullmatch(
        r"(?:hoàn\s+thiện|dựng)\s+(?:hình\s+chóp|lăng\s+trụ|tứ\s+diện|hình\s+lập\s+phương|hình\s+hộp)\s+(?P<solid>(?:[A-Z][0-9]*'?)+(?:\.(?:[A-Z][0-9]*'?)+)?)",
        c,
        re.IGNORECASE,
    )
    if m:
        pts = _extract_points(m.group("solid"))
        return AtomicClause(
            op="construct_solid",
            output_symbol=m.group("solid"),
            solid_input=m.group("solid"),
            point_inputs=tuple(pts),
            raw_clause=clause,
        )

    if re.search(r"\b(?:hình\s+nón|khối\s+nón|mặt\s+nón|hình\s+trụ|khối\s+trụ|mặt\s+trụ|nón\s+tròn\s+xoay|khối\s+tròn\s+xoay)\b", c, re.IGNORECASE):
        raise StepEditRefusal(
            "UNSUPPORTED_CURVED_OR_FREEFORM_STEP",
            "parser",
            f"Phép dựng khối/mặt tròn xoay trong '{clause}' nằm ngoài phạm vi chỉnh sửa bước dựng hình phẳng/chóp hiện tại.",
        )

    raise StepEditRefusal(
        "UNSUPPORTED_STEP_SYNTAX",
        "parser",
        (
            f"Chưa nhận diện được phép dựng hình hợp lệ trong câu '{clause}'. "
            "Hãy mô tả rõ phép dựng (ví dụ: 'Xác định trung điểm H của AB', "
            "'Lấy điểm M thuộc SA sao cho SM = 1/3 SA', "
            "'Dựng mặt phẳng (α) qua H và vuông góc với AB', "
            "'Xác định giao điểm E của SB với (MNP)')."
        ),
    )


def parse_vietnamese_construction_step(text: str) -> ParsedStepIntent:
    """Parse one or more Vietnamese geometry construction clauses deterministically (0 LLM calls)."""
    norm = _normalize_vi_math(text)
    if not norm:
        raise StepEditRefusal("EMPTY_STEP_INSTRUCTION", "parser", "Nội dung bước dựng không được để trống.")
    if any(tok in norm.lower() for tok in ("chọn bừa", "đoán", "tọa độ giả", "giả sử tọa độ")):
        raise StepEditRefusal(
            "UNSUPPORTED_STEP_SYNTAX",
            "parser",
            "Không thể áp dụng tọa độ tự gán; mọi điểm mới phải được xác định bằng phép dựng hình học.",
        )
    raw_clauses = _split_compound_clauses(norm)
    if not raw_clauses:
        raise StepEditRefusal("EMPTY_STEP_INSTRUCTION", "parser", "Không tìm thấy câu lệnh dựng hình hợp lệ.")

    clauses = tuple(_parse_single_clause(cl) for cl in raw_clauses)
    reg_ops: list[str] = []
    for cl in clauses:
        for rop in OP_TO_REGISTRY.get(cl.op, (cl.op,)):
            if rop not in reg_ops:
                reg_ops.append(rop)
    sig_payload = [
        {
            "op": c.op,
            "out": c.output_symbol,
            "pts": list(c.point_inputs),
            "pls": list(c.plane_inputs),
            "lns": list(c.line_inputs),
            "params": c.params,
        }
        for c in clauses
    ]
    intent_signature = hashlib.sha256(
        json.dumps(sig_payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    return ParsedStepIntent(
        raw_text=text,
        normalized_text=norm,
        clauses=clauses,
        registry_operations=tuple(reg_ops),
        intent_signature=intent_signature,
    )


# ── Exact memory hydration / serialization helpers ──────────────────────────────
def _scene_metric(scene3d: dict[str, Any]) -> _m.Metric | None:
    mat = scene3d.get("chart_metric")
    if mat is None:
        return None
    return _m.Metric(tuple(tuple(Fraction(cell) for cell in row) for row in mat))


def _hydrate_object_value(obj: dict[str, Any], mem: dict[str, Any]) -> Any:
    """Hydrate exact Kernel value from a Scene3D JSON object without floating-point approximation."""
    otype = obj.get("type")
    if otype == "point3":
        xyz = obj.get("xyz")
        return Vec3.of(*xyz)
    if otype == "vector3":
        xyz = obj.get("xyz")
        return Vec3.of(*xyz)
    if otype == "line3":
        return Line3(Vec3.of(*obj["point"]), Vec3.of(*obj["direction"]))
    if otype == "segment3":
        return Segment3(Vec3.of(*obj["point_a"]), Vec3.of(*obj["point_b"]))
    if otype == "plane3":
        return Plane3(Vec3.of(*obj["point"]), Vec3.of(*obj["normal"]))
    if otype == "polygon3":
        return tuple(Vec3.of(*v) for v in (obj.get("vertices") or ()))
    if otype == "solid":
        verts = tuple(Vec3.of(*v) for v in (obj.get("vertices") or ()))
        faces = tuple(tuple(int(i) for i in f) for f in (obj.get("faces") or ()))
        return Polyhedron(vertices=verts, faces=faces)
    if otype == "section":
        solid_id = next((d for d in (obj.get("depends") or ()) if isinstance(mem.get(d), Polyhedron)), None)
        plane_id = next((d for d in (obj.get("depends") or ()) if isinstance(mem.get(d), Plane3)), None)
        if solid_id and plane_id:
            return cross_section(mem[solid_id], mem[plane_id])
        return Section(
            polygon=tuple(Vec3.of(*v) for v in (obj.get("polygon") or ())),
            is_closed=bool(obj.get("closed", True)),
            steps=tuple(),
            vertex_sources=tuple(),
        )
    if otype == "circle3":
        return Circle3(
            center=Vec3.of(*obj["center"]),
            normal=Vec3.of(*obj["normal"]),
            radius_sq=Fraction(obj["radius_sq"]),
        )
    if otype == "ellipse3":
        return Ellipse3(
            center=Vec3.of(*obj["center"]),
            normal=Vec3.of(*obj["normal"]),
            major_dir=Vec3.of(*obj["major_dir"]),
            minor_dir=Vec3.of(*obj["minor_dir"]),
            semi_major_sq=Fraction(obj["semi_major_sq"]),
            semi_minor_sq=Fraction(obj["semi_minor_sq"]),
        )
    if otype == "curved_solid":
        anchor = Vec3.of(*obj["anchor"])
        apex = Vec3.of(*obj["apex_or_top"]) if obj.get("apex_or_top") else None
        rim = Vec3.of(*obj["rim_point"]) if obj.get("rim_point") else None
        rsq = Fraction(obj["radius_sq"]) if obj.get("radius_sq") is not None else None
        hsq = Fraction(obj["height_sq"]) if (obj.get("curved_kind") != "ball" and obj.get("height_sq") is not None) else None
        return CurvedSolid(
            kind=obj["curved_kind"],
            anchor=anchor,
            apex_or_top=apex,
            rim_point=rim,
            radius_sq_khai=rsq if rim is None else None,
            height_sq_khai=hsq if (apex is None and obj.get("curved_kind") != "ball") else None,
        )
    if otype == "quantity":
        if obj.get("exact") is not None:
            ex = parse_exact(obj["exact"])
            if ex is not None:
                return ex
        if obj.get("value") is not None:
            return parse_exact(obj["value"])
    return None


def _exact_xyz_list(v: Vec3) -> list[str]:
    return [str(v.x), str(v.y), str(v.z)]


def _recover_divide_segment_params(
    obj: dict[str, Any],
    mem: dict[str, Any],
) -> tuple[str, str, Fraction] | None:
    """Recover exact `(a_id, b_id, t)` for an existing `divide_segment` point from `source.params` or `Vec3` coordinates."""
    src = obj.get("source") or {}
    params = src.get("params") or {}
    if isinstance(params.get("a"), str) and isinstance(params.get("b"), str) and params.get("ratio"):
        try:
            return params["a"], params["b"], Fraction(str(params["ratio"]))
        except (ValueError, ZeroDivisionError):
            pass
    deps = [d for d in (obj.get("depends") or ()) if isinstance(mem.get(d), Vec3)]
    if len(deps) != 2 or not obj.get("xyz"):
        return None
    a_id, b_id = deps[0], deps[1]
    pa, pb = mem[a_id], mem[b_id]
    pt = Vec3.of(*obj["xyz"])
    d = pb - pa
    if d.is_zero():
        return None
    for attr in ("x", "y", "z"):
        dv = getattr(d, attr)
        if dv != 0:
            t = (getattr(pt, attr) - getattr(pa, attr)) / dv
            if (pa + d.scale(t)) == pt:
                return a_id, b_id, t
    return None


def _reevaluate_object(
    obj: dict[str, Any],
    mem: dict[str, Any],
    by_id: dict[str, dict[str, Any]],
) -> Any:
    """Deterministically re-evaluate a single downstream dependent object using Exact Kernel primitives."""
    prod = obj.get("producer") or (obj.get("source") or {}).get("instruction") or ""
    deps = list(obj.get("depends") or ())

    if prod == "construct_point.midpoint":
        pts = [d for d in deps if isinstance(mem.get(d), Vec3)]
        if len(pts) != 2:
            raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Điểm '{obj['id']}' thiếu hai đầu mút.")
        return K.midpoint(mem[pts[0]], mem[pts[1]])

    if prod == "construct_point.divide_segment":
        recovered = _recover_divide_segment_params(obj, mem)
        if recovered is None:
            raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Không xác định được tỉ lệ chia đoạn của điểm '{obj['id']}'.")
        a_id, b_id, t = recovered
        return K.divide_segment(mem[a_id], mem[b_id], t)

    if prod == "construct_point.centroid":
        pts = [d for d in deps if isinstance(mem.get(d), Vec3)]
        if len(pts) < 3:
            raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Trọng tâm '{obj['id']}' thiếu đủ đỉnh tam giác.")
        acc = mem[pts[0]] + mem[pts[1]] + mem[pts[2]]
        return acc.scale(Fraction(1, 3))

    if prod == "construct_point.project_onto":
        pt_id = next((d for d in deps if isinstance(mem.get(d), Vec3)), None)
        target_id = next((d for d in deps if isinstance(mem.get(d), (Plane3, Line3))), None)
        if pt_id is None or target_id is None:
            raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Hình chiếu '{obj['id']}' thiếu điểm hoặc đối tượng chiếu.")
        tgt = mem[target_id]
        if isinstance(tgt, Plane3):
            return K.project_point_onto_plane(mem[pt_id], tgt)
        return K.project_point_onto_line(mem[pt_id], tgt)

    if prod == "construct_point.intersect_line_plane":
        ln_id = next((d for d in deps if isinstance(mem.get(d), Line3)), None)
        pl_id = next((d for d in deps if isinstance(mem.get(d), Plane3)), None)
        if ln_id is None or pl_id is None:
            raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Giao điểm '{obj['id']}' thiếu đường thẳng hoặc mặt phẳng.")
        return K.intersect_line_plane(mem[ln_id], mem[pl_id])

    if prod in ("construct_point.intersect_line_line", "construct_point.intersect_lines"):
        lns = [d for d in deps if isinstance(mem.get(d), Line3)]
        if len(lns) != 2:
            raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Giao điểm '{obj['id']}' cần hai đường thẳng.")
        return K.intersect_line_line(mem[lns[0]], mem[lns[1]])

    if prod == "construct_point.translate":
        pt_id = next((d for d in deps if by_id.get(d, {}).get("type") == "point3"), None)
        vec_id = next((d for d in deps if by_id.get(d, {}).get("type") == "vector3"), None)
        if pt_id is None or vec_id is None:
            raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Điểm tịnh tiến '{obj['id']}' thiếu điểm gốc hoặc vectơ.")
        return K.translate(mem[pt_id], mem[vec_id])

    if prod == "construct_line":
        pts = [d for d in deps if isinstance(mem.get(d), Vec3)]
        if len(pts) != 2:
            raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Đường thẳng '{obj['id']}' thiếu hai điểm.")
        return Line3.through(mem[pts[0]], mem[pts[1]])

    if prod == "construct_segment":
        eids = list(obj.get("endpoint_ids") or ())
        pts = eids if len(eids) == 2 else [d for d in deps if isinstance(mem.get(d), Vec3)]
        if len(pts) != 2:
            raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Đoạn thẳng '{obj['id']}' thiếu hai đầu mút.")
        return Segment3.between(mem[pts[0]], mem[pts[1]])

    if prod == "construct_plane":
        pts = [d for d in deps if isinstance(mem.get(d), Vec3)]
        if len(pts) < 3:
            raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Mặt phẳng '{obj['id']}' cần ít nhất ba điểm.")
        p0 = mem[pts[0]]
        chosen: tuple[Vec3, Vec3, Vec3] | None = None
        for i in range(1, len(pts)):
            for j in range(i + 1, len(pts)):
                if not P.collinear(p0, mem[pts[i]], mem[pts[j]]):
                    chosen = (p0, mem[pts[i]], mem[pts[j]])
                    break
            if chosen:
                break
        if chosen is None:
            raise GeometryError("COLLINEAR_POINTS", "Các điểm thẳng hàng, không xác định được mặt phẳng.")
        pl = Plane3.through(*chosen)
        for p in pts[3:]:
            if not P.point_on_plane(mem[p], pl):
                raise GeometryError("NON_COPLANAR_POINTS", f"Điểm '{p}' không đồng phẳng với các điểm còn lại.")
        return pl

    if prod == "plane_perpendicular_to_line":
        pt_id = next((d for d in deps if by_id.get(d, {}).get("type") == "point3"), None)
        ln_id = next((d for d in deps if by_id.get(d, {}).get("type") == "line3"), None)
        if pt_id is None or ln_id is None:
            raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Mặt phẳng '{obj['id']}' thiếu điểm đi qua hoặc đường vuông góc.")
        return K.plane_through_point_perpendicular_to(mem[pt_id], mem[ln_id])

    if prod == "intersect_plane_plane":
        pls = [d for d in deps if isinstance(mem.get(d), Plane3)]
        if len(pls) != 2:
            raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Giao tuyến '{obj['id']}' cần hai mặt phẳng.")
        return K.intersect_plane_plane(mem[pls[0]], mem[pls[1]])

    if prod == "construct_polygon":
        vids = list(obj.get("vertex_ids") or deps)
        pts = tuple(mem[v] for v in vids)
        for idx_k in range(3, len(pts)):
            if not P.coplanar(pts[0], pts[1], pts[2], pts[idx_k]):
                raise GeometryError("NON_COPLANAR_POINTS", f"Đỉnh '{vids[idx_k]}' không đồng phẳng trong đa giác.")
        return pts

    if prod == "construct_solid":
        vids = list(obj.get("vertex_ids") or deps)
        faces = tuple(tuple(int(i) for i in f) for f in (obj.get("faces") or ()))
        return Polyhedron(vertices=tuple(mem[v] for v in vids), faces=faces)

    if prod == "construct_section":
        sol_id = next((d for d in deps if isinstance(mem.get(d), Polyhedron)), None)
        pl_id = next((d for d in deps if isinstance(mem.get(d), Plane3)), None)
        if sol_id is None or pl_id is None:
            raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Thiết diện '{obj['id']}' thiếu khối hoặc mặt phẳng cắt.")
        return cross_section(mem[sol_id], mem[pl_id])

    if prod.startswith("construct_curved_solid"):
        kind = obj["curved_kind"]
        # Infer center/top/rim from `depends` order (first non-quantity point is anchor when originalrim/top match)
        pt_deps = [d for d in deps if by_id.get(d, {}).get("type") == "point3"]
        qty_deps = [d for d in deps if by_id.get(d, {}).get("type") == "quantity"]
        if not pt_deps:
            raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Khối cong '{obj['id']}' thiếu tâm.")
        anchor_id = pt_deps[0]
        rim_id = pt_deps[-1] if (kind == "ball" and len(pt_deps) >= 2) else (pt_deps[1] if len(pt_deps) >= 2 and obj.get("rim_point") else None)
        top_id = pt_deps[1] if (kind in ("cylinder", "cone") and len(pt_deps) >= 2 and obj.get("apex_or_top")) else None
        if kind == "ball" and len(pt_deps) == 2 and obj.get("anchor"):
            # Preserve semantic distinction: in balls with `depends = [I, S]`, center matches `anchor` originally
            orig_anchor = Vec3.of(*obj["anchor"])
            for cand in pt_deps:
                orig_cand_obj = by_id.get(cand)
                if orig_cand_obj and orig_cand_obj.get("xyz") and Vec3.of(*orig_cand_obj["xyz"]) == orig_anchor:
                    anchor_id = cand
                    rim_id = next((x for x in pt_deps if x != cand), cand)
                    break
        rsq = None
        if rim_id is None and obj.get("radius_sq") is not None:
            rsq = Fraction(obj["radius_sq"])
            for qd in qty_deps:
                qv = mem.get(qd)
                if isinstance(qv, Fraction):
                    rsq = qv * qv
                elif isinstance(qv, Radical) and qv.mu == 0:
                    rsq = qv.he * qv.he * qv.can
        return CurvedSolid(
            kind=kind,
            anchor=mem[anchor_id],
            apex_or_top=mem[top_id] if top_id else None,
            rim_point=mem[rim_id] if rim_id else None,
            radius_sq_khai=rsq if rim_id is None else None,
            height_sq_khai=Fraction(obj["height_sq"]) if (kind != "ball" and top_id is None and obj.get("height_sq") is not None) else None,
        )

    if prod == "intersect_plane_curved":
        sol_id = next((d for d in deps if isinstance(mem.get(d), CurvedSolid)), None)
        pl_id = next((d for d in deps if isinstance(mem.get(d), Plane3)), None)
        if sol_id is None or pl_id is None:
            raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Đường tròn giao tuyến '{obj['id']}' thiếu khối cong hoặc mặt phẳng.")
        return CV.intersect_plane_curved(mem[sol_id], mem[pl_id])

    if prod == "intersect_plane_curved_ellipse":
        sol_id = next((d for d in deps if isinstance(mem.get(d), CurvedSolid)), None)
        pl_id = next((d for d in deps if isinstance(mem.get(d), Plane3)), None)
        if sol_id is None or pl_id is None:
            raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Elip giao tuyến '{obj['id']}' thiếu khối trụ hoặc mặt phẳng.")
        return CV.intersect_plane_curved_ellipse(mem[sol_id], mem[pl_id])

    if prod.startswith("measure."):
        qty = prod.split(".", 1)[1]
        if qty == "volume":
            subj = next((mem[d] for d in deps if isinstance(mem.get(d), (Polyhedron, CurvedSolid))), None)
            if subj is None:
                raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Không tìm thấy khối cho phép đo thể tích '{obj['id']}'.")
            return volume_of(subj)
        if qty == "area":
            subj = next(
                (mem[d] for d in deps if isinstance(mem.get(d), (Section, Circle3, Ellipse3, tuple))),
                None,
            )
            if subj is None:
                raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Không tìm thấy hình phẳng cho phép đo diện tích '{obj['id']}'.")
            return area_of(subj)
        if qty == "radius":
            subj = next((mem[d] for d in deps if isinstance(mem.get(d), (Circle3, CurvedSolid))), None)
            if subj is None:
                raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", f"Không tìm thấy khối cầu/đường tròn cho bán kính '{obj['id']}'.")
            return CV.ban_kinh(subj)
        if qty == "lateral_area":
            subj = next((mem[d] for d in deps if isinstance(mem.get(d), CurvedSolid)), None)
            return lateral_area_of(subj)
        if qty == "distance" and len(deps) >= 2:
            a, b = mem[deps[0]], mem[deps[1]]
            if isinstance(a, Vec3) and isinstance(b, Plane3):
                d2 = M.distance_sq_point_plane(a, b)
            elif isinstance(a, Plane3) and isinstance(b, Vec3):
                d2 = M.distance_sq_point_plane(b, a)
            elif isinstance(a, Vec3) and isinstance(b, Line3):
                d2 = M.distance_sq_point_line(a, b)
            elif isinstance(a, Line3) and isinstance(b, Vec3):
                d2 = M.distance_sq_point_line(b, a)
            elif isinstance(a, Vec3) and isinstance(b, Vec3):
                d2 = M.distance_sq(a, b)
            elif isinstance(a, Line3) and isinstance(b, Line3):
                d2 = M.distance_sq_lines(a, b)
            elif isinstance(a, Line3) and isinstance(b, Plane3):
                d2 = M.distance_sq_line_plane(a, b)
            elif isinstance(a, Plane3) and isinstance(b, Line3):
                d2 = M.distance_sq_line_plane(b, a)
            elif isinstance(a, Plane3) and isinstance(b, Plane3):
                d2 = M.distance_sq_planes(a, b)
            else:
                raise GeometryError("INVALID_MEASURE_OPERANDS", "Cặp đối tượng đo khoảng cách không hợp lệ.")
            return sqrt_rational(d2)
        if qty == "angle_cos_sq" and len(deps) >= 2:
            return M.cos_sq_giua(mem[deps[0]], mem[deps[1]])

    return _hydrate_object_value(obj, mem)


def _sync_scene_object_from_value(
    obj: dict[str, Any],
    val: Any,
    by_id: dict[str, dict[str, Any]],
) -> None:
    """Write exact Kernel value back into a Scene3D object dict in exact rational/radical form."""
    if isinstance(val, Vec3):
        obj["xyz"] = _exact_xyz_list(val)
    elif isinstance(val, Line3):
        obj["point"] = _exact_xyz_list(val.point)
        obj["direction"] = _exact_xyz_list(val.direction)
    elif isinstance(val, Segment3):
        pa = _exact_xyz_list(val.point_a)
        pb = _exact_xyz_list(val.point_b)
        obj["point_a"] = pa
        obj["point_b"] = pb
        obj["endpoints"] = [pa, pb]
        if isinstance(obj.get("perpendicular_witness"), dict):
            pw = obj["perpendicular_witness"]
            from_pt = Vec3.of(*(by_id[pw["from"]]["xyz"])) if pw.get("from") in by_id else val.point_b
            foot_pt = Vec3.of(*(by_id[pw["foot_id"]]["xyz"])) if pw.get("foot_id") in by_id else val.point_a
            pw["foot"] = _exact_xyz_list(foot_pt)
            pw["line_direction"] = _exact_xyz_list(from_pt - foot_pt)
    elif isinstance(val, Plane3):
        obj["point"] = _exact_xyz_list(val.point)
        obj["normal"] = _exact_xyz_list(val.normal)
    elif isinstance(val, Section):
        obj["polygon"] = [_exact_xyz_list(v) for v in val.polygon]
        obj["closed"] = bool(val.is_closed)
        obj["steps"] = [
            {"face_index": s.face_index, "a": _exact_xyz_list(s.a), "b": _exact_xyz_list(s.b)}
            for s in val.steps
        ]
        obj["vertex_sources"] = [
            {
                "kind": vs.kind,
                "solid_vertex_index": vs.solid_vertex_index,
                "solid_edge_vertex_indices": list(vs.solid_edge_vertex_indices)
                if vs.solid_edge_vertex_indices is not None
                else None,
            }
            for vs in val.vertex_sources
        ]
    elif isinstance(val, Circle3):
        obj["center"] = _exact_xyz_list(val.center)
        obj["normal"] = _exact_xyz_list(val.normal)
        obj["radius_sq"] = str(val.radius_sq)
    elif isinstance(val, Ellipse3):
        obj["center"] = _exact_xyz_list(val.center)
        obj["normal"] = _exact_xyz_list(val.normal)
        obj["major_dir"] = _exact_xyz_list(val.major_dir)
        obj["minor_dir"] = _exact_xyz_list(val.minor_dir)
        obj["semi_major_sq"] = str(val.semi_major_sq)
        obj["semi_minor_sq"] = str(val.semi_minor_sq)
    elif isinstance(val, CurvedSolid):
        obj["anchor"] = _exact_xyz_list(val.anchor)
        obj["apex_or_top"] = _exact_xyz_list(val.apex_or_top) if val.apex_or_top else None
        obj["rim_point"] = _exact_xyz_list(val.rim_point) if val.rim_point else None
        obj["radius_sq"] = str(val.radius_sq)
        obj["height_sq"] = str(val.height_sq)
    elif isinstance(val, Polyhedron):
        obj["vertices"] = [_exact_xyz_list(v) for v in val.vertices]
        obj["faces"] = [list(f) for f in val.faces]
    elif isinstance(val, tuple) and val and all(isinstance(x, Vec3) for x in val):
        obj["vertices"] = [_exact_xyz_list(v) for v in val]
    elif isinstance(val, (Fraction, Radical)):
        txt = radical_display(val)
        obj["value"] = txt
        obj["exact"] = radical_to_json(val)
        if isinstance(obj.get("formula"), dict):
            prefix = (obj.get("notation") or obj.get("reference") or obj.get("label") or "Giá trị")
            obj["formula"]["text"] = f"{prefix} = {txt}"


# ── Dependency DAG builder & cycle/closure analyzer ────────────────────────────
def build_construction_dependency_graph(
    scene3d: dict[str, Any],
    *,
    target_ids: list[str] | None = None,
    step_id: str | None = None,
    step_index: int | None = None,
    absorbed_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Build explicit object & step dependency DAG from a canonical Scene3D contract."""
    objs = [o for o in (scene3d.get("objects") or ()) if isinstance(o, dict) and o.get("id")]
    by_id: dict[str, dict[str, Any]] = {o["id"]: o for o in objs}

    deps_of: dict[str, list[str]] = {}
    consumers_of: dict[str, list[str]] = {oid: [] for oid in by_id}
    for o in objs:
        oid = o["id"]
        raw_deps: list[str] = []
        for dep in o.get("depends") or ():
            if dep != oid and dep not in raw_deps:
                if dep not in by_id:
                    raise StepEditRefusal(
                        "MISSING_REFERENCE",
                        "dependency_graph",
                        f"Đối tượng '{oid}' phụ thuộc vào '{dep}' không tồn tại trong cảnh 3D.",
                    )
                raw_deps.append(dep)
        for ep in o.get("endpoint_ids") or ():
            if ep != oid and ep not in raw_deps:
                if ep not in by_id:
                    raise StepEditRefusal(
                        "MISSING_REFERENCE",
                        "dependency_graph",
                        f"Đoạn thẳng '{oid}' trỏ tới đầu mút '{ep}' không tồn tại.",
                    )
                raw_deps.append(ep)
        deps_of[oid] = raw_deps
        for dep in raw_deps:
            consumers_of[dep].append(oid)

    # Cycle detection via Kahn's algorithm on object graph
    indegree = {oid: len(deps_of[oid]) for oid in by_id}
    ready = [o["id"] for o in objs if indegree[o["id"]] == 0]
    topo_objects: list[str] = []
    while ready:
        cur = ready.pop(0)
        topo_objects.append(cur)
        for nxt in consumers_of[cur]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)
    if len(topo_objects) != len(by_id):
        cycled = sorted(set(by_id) - set(topo_objects))
        raise StepEditRefusal(
            "CYCLE_DEPENDENCY",
            "dependency_graph",
            f"Phát hiện chu trình phụ thuộc giữa các đối tượng: {', '.join(cycled)}.",
        )

    event_step_of: dict[str, int] = {}
    for ev in scene3d.get("events") or ():
        sidx = ev.get("step_index")
        if isinstance(sidx, int):
            if ev.get("object"):
                event_step_of.setdefault(str(ev["object"]), sidx)
            for oid in ev.get("objects") or ():
                event_step_of.setdefault(str(oid), sidx)

    object_nodes = {
        o["id"]: {
            "object_id": o["id"],
            "symbol": o.get("notation") or o.get("reference") or o.get("label"),
            "object_type": o.get("type"),
            "producer_op": o.get("producer") or (o.get("source") or {}).get("instruction") or o.get("origin"),
            "inputs": list(deps_of[o["id"]]),
            "consumers": list(consumers_of[o["id"]]),
            "event_step_index": event_step_of.get(o["id"], 0),
        }
        for o in objs
    }

    target_set = set(target_ids or ())
    absorbed_set = set(absorbed_ids or ())
    step_record = {
        "step_id": step_id or (f"step:{target_ids[0]}" if target_ids else f"step_{step_index or 0}"),
        "step_index": step_index if step_index is not None else 0,
        "outputs": sorted(target_set | absorbed_set),
        "inputs": sorted(
            {
                d
                for tid in target_set
                for d in deps_of.get(tid, [])
                if d not in target_set and d not in absorbed_set
            }
        ),
    }

    return {
        "deps_of": deps_of,
        "consumers_of": consumers_of,
        "topo_order": topo_objects,
        "object_nodes": object_nodes,
        "event_step_of": event_step_of,
        "edited_step": step_record,
    }


def _transitive_closure(seeds: set[str], adj: dict[str, list[str]]) -> set[str]:
    visited: set[str] = set()
    stack = list(seeds)
    while stack:
        cur = stack.pop()
        for nxt in adj.get(cur, ()):
            if nxt not in visited:
                visited.add(nxt)
                stack.append(nxt)
    return visited


def _scene_digest(scene3d: dict[str, Any]) -> str:
    payload = json.dumps(scene3d.get("objects") or [], sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _symbol_index_before_step(
    scene3d: dict[str, Any],
    graph: dict[str, Any],
    excluded_ids: set[str],
    *,
    allow_post_step: bool = False,
    target_step_anchor: int | None = None,
    prior_step_ids: set[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Map canonical math symbols (`A`, `(α)`, `AB`, `(ABCD)`, `(MNP)`) to objects eligible as inputs."""
    event_step_of = graph["event_step_of"]
    by_sym: dict[str, list[dict[str, Any]]] = {}

    def _add(sym: str | None, obj: dict[str, Any]) -> None:
        if not sym:
            return
        k = _normalize_vi_math(sym).upper() if obj.get("type") == "point3" else _normalize_vi_math(sym)
        lst = by_sym.setdefault(k, [])
        if all(x.get("id") != obj.get("id") for x in lst):
            lst.append(obj)

    for o in scene3d.get("objects") or ():
        oid = o.get("id")
        if not oid or oid in excluded_ids:
            continue
        if not allow_post_step and target_step_anchor is not None:
            is_prior_by_ui = prior_step_ids is not None and oid in prior_step_ids
            if o.get("origin") != "free" and not is_prior_by_ui and event_step_of.get(oid, 0) > target_step_anchor:
                continue
        if o.get("type") == "point3":
            ref_tok = o.get("reference")
            ref_sym = ref_tok if (isinstance(ref_tok, str) and re.fullmatch(r"[A-Z][0-9]*[′']?", ref_tok.strip())) else None
            for cand in (o.get("notation"), ref_sym, oid if re.fullmatch(r"[A-Z][0-9]*(?:'|_prime)?", oid) else None):
                if cand:
                    _add(cand.replace("_prime", "'"), o)
        elif o.get("type") == "plane3":
            for cand in (o.get("notation"), o.get("reference"), o.get("label")):
                if cand and isinstance(cand, str):
                    nc = _normalize_vi_math(cand)
                    _add(nc, o)
                    if nc.startswith("(") and nc.endswith(")"):
                        _add(nc[1:-1], o)
        elif o.get("type") == "line3":
            for cand in (o.get("notation"), o.get("reference"), o.get("label")):
                if cand and isinstance(cand, str):
                    _add(_normalize_vi_math(cand), o)
            pts = [d for d in (o.get("depends") or ()) if by_id_lookup(scene3d, d, "point3")]
            if len(pts) == 2:
                _add(f"{pts[0]}{pts[1]}".replace("_prime", "'"), o)
                _add(f"{pts[1]}{pts[0]}".replace("_prime", "'"), o)
        elif o.get("type") == "solid":
            for cand in (o.get("notation"), o.get("label")):
                if cand:
                    _add(_normalize_vi_math(cand), o)
    return by_sym


def by_id_lookup(scene3d: dict[str, Any], oid: str, expected_type: str | None = None) -> dict[str, Any] | None:
    for o in scene3d.get("objects") or ():
        if o.get("id") == oid:
            if expected_type is None or o.get("type") == expected_type:
                return o
            return None
    return None


def _resolve_point_id(
    sym: str,
    available: dict[str, list[dict[str, Any]]],
    local_mem: dict[str, Any],
    all_objs_by_id: dict[str, dict[str, Any]],
    downstream_ids: set[str],
    post_step_ids: set[str],
    edit_action: str,
) -> str:
    norm = _normalize_vi_math(sym).upper()
    cands = [o for o in available.get(norm, ()) if o.get("type") == "point3"]
    if cands:
        return cands[0]["id"]
    if norm in local_mem and isinstance(local_mem[norm], Vec3):
        return norm
    # Check whether it exists downstream / in a later step to report cycle / ordering error specifically
    for o in all_objs_by_id.values():
        if o.get("type") != "point3":
            continue
        onorm = _normalize_vi_math(o.get("notation") or o["id"]).replace("_prime", "'").upper()
        if onorm == norm:
            if o["id"] in downstream_ids or o["id"] in post_step_ids:
                raise StepEditRefusal(
                    "CYCLE_DEPENDENCY",
                    "dependency_analysis",
                    f"Không thể thực hiện {edit_action} vì tham chiếu tới điểm {_display_sym(norm)} phụ thuộc hoặc được dựng ở bước sau (tránh phụ thuộc vòng).",
                )
    raise StepEditRefusal(
        "MISSING_DEPENDENCY",
        "planner",
        f"Không thể {edit_action} vì chưa xác định được điểm {_display_sym(norm)}.",
    )


def _resolve_plane_id(
    sym: str,
    available: dict[str, list[dict[str, Any]]],
    local_objs: dict[str, dict[str, Any]],
    all_objs_by_id: dict[str, dict[str, Any]],
    downstream_ids: set[str],
    post_step_ids: set[str],
    edit_action: str,
) -> str:
    norm = _canon_plane_name(sym) or _normalize_vi_math(sym)
    for cand_map in (local_objs, available):
        if isinstance(cand_map, dict):
            val = cand_map.get(norm)
            if isinstance(val, dict) and val.get("type") == "plane3":
                return val["id"]
            if isinstance(val, list):
                pl = next((o for o in val if o.get("type") == "plane3"), None)
                if pl:
                    return pl["id"]
    # Also allow matching base polygon `(ABCD)` to existing plane or creating via 3 non-collinear points
    inner_pts = _extract_points(norm.strip("()"))
    if len(inner_pts) >= 3:
        for o in all_objs_by_id.values():
            if o.get("type") == "plane3" and set(inner_pts) <= {_normalize_vi_math(all_objs_by_id.get(d, {}).get("notation") or d) for d in (o.get("depends") or ())}:
                if o["id"] not in downstream_ids and o["id"] not in post_step_ids:
                    return o["id"]
    for o in all_objs_by_id.values():
        if o.get("type") == "plane3" and _canon_plane_name(o.get("notation") or o.get("label")) == norm:
            if o["id"] in downstream_ids or o["id"] in post_step_ids:
                raise StepEditRefusal(
                    "CYCLE_DEPENDENCY",
                    "dependency_analysis",
                    f"Không thể {edit_action} vì mặt phẳng {norm} phụ thuộc hoặc được dựng ở bước sau.",
                )
    raise StepEditRefusal(
        "MISSING_DEPENDENCY",
        "planner",
        f"Không thể {edit_action} vì chưa xác định được mặt phẳng {norm}.",
    )


# ── Exact Kernel role & predicate verification (§2.2, §8) ────────────────────────
def _verify_point_role_assertion(
    assertion: dict[str, Any],
    pt_id: str,
    pt_val: Vec3,
    mem: dict[str, Any],
    by_id: dict[str, dict[str, Any]],
    available_symbols: dict[str, list[dict[str, Any]]],
    all_objs: list[dict[str, Any]],
) -> None:
    """Strictly verify role-qualified point claims (`tâm O của hình vuông ABCD`, `trung điểm O của AC`,
    `giao điểm O của AC và BD`) against Exact Kernel coordinates without guessing by name."""
    kind = assertion.get("kind")
    disp = _display_sym(assertion.get("pt") or pt_id)

    if kind == "midpoint":
        a_sym, b_sym = assertion["a"], assertion["b"]
        a_obj = next((o for o in available_symbols.get(a_sym.upper(), ()) if o.get("type") == "point3" and o["id"] in mem), None)
        b_obj = next((o for o in available_symbols.get(b_sym.upper(), ()) if o.get("type") == "point3" and o["id"] in mem), None)
        if a_obj is None or b_obj is None:
            raise StepEditRefusal("MISSING_DEPENDENCY", "validation", f"Không thể kiểm chứng trung điểm {disp} của {a_sym}{b_sym} vì thiếu đầu mút.")
        if not P.same_point(pt_val, K.midpoint(mem[a_obj["id"]], mem[b_obj["id"]])):
            raise StepEditRefusal(
                "ROLE_ASSERTION_FAILED",
                "validation",
                f"Điểm {disp} không phải là trung điểm của đoạn {a_sym}{b_sym}.",
            )
        return

    if kind == "intersection":
        l1_syms = assertion["line1"]
        l2_syms = assertion["line2"]
        pts: list[Vec3] = []
        for psym in (*l1_syms, *l2_syms):
            po = next((o for o in available_symbols.get(psym.upper(), ()) if o.get("type") == "point3" and o["id"] in mem), None)
            if po is None:
                raise StepEditRefusal("MISSING_DEPENDENCY", "validation", f"Thiếu điểm '{psym}' để kiểm chứng giao điểm {disp}.")
            pts.append(mem[po["id"]])
        ln1 = Line3.through(pts[0], pts[1])
        ln2 = Line3.through(pts[2], pts[3])
        inter = K.intersect_line_line(ln1, ln2)
        if not P.same_point(pt_val, inter):
            raise StepEditRefusal(
                "ROLE_ASSERTION_FAILED",
                "validation",
                f"Điểm {disp} không trùng với giao điểm của {''.join(l1_syms)} và {''.join(l2_syms)}.",
            )
        return

    if kind == "center":
        target_poly = assertion.get("target")
        shape = assertion.get("shape")
        verts: list[Vec3] = []
        if target_poly:
            ps = _extract_points(target_poly)
            if len(ps) != 4:
                raise StepEditRefusal(
                    "ROLE_ASSERTION_FAILED",
                    "validation",
                    f"Chỉ hỗ trợ kiểm chứng tâm hình bình hành/chữ nhật/hình vuông 4 đỉnh (nhận được '{target_poly}').",
                )
            for psym in ps:
                po = next((o for o in available_symbols.get(psym.upper(), ()) if o.get("type") == "point3" and o["id"] in mem), None)
                if po is None:
                    raise StepEditRefusal("MISSING_DEPENDENCY", "validation", f"Thiếu đỉnh {psym} của '{target_poly}' để kiểm chứng tâm {disp}.")
                verts.append(mem[po["id"]])
        else:
            poly_obj = next(
                (
                    o
                    for o in all_objs
                    if o.get("type") == "polygon3"
                    and len(o.get("depends") or o.get("vertices") or ()) == 4
                    and (o.get("surface_role") == "BASE_REGION" or "day" in str(o.get("id", "")).lower())
                ),
                None,
            )
            if poly_obj is None:
                poly_obj = next(
                    (o for o in all_objs if o.get("type") == "polygon3" and len(o.get("depends") or o.get("vertices") or ()) == 4),
                    None,
                )
            if poly_obj is None:
                raise StepEditRefusal(
                    "ROLE_ASSERTION_FAILED",
                    "validation",
                    f"Không tìm thấy tứ giác đáy hợp lệ để kiểm chứng '{disp}' là tâm.",
                )
            deps4 = list(poly_obj.get("depends") or ())
            if len(deps4) == 4 and all(d in mem for d in deps4):
                verts = [mem[d] for d in deps4]
            elif poly_obj.get("vertices") and len(poly_obj["vertices"]) == 4:
                verts = [Vec3.of(*v) for v in poly_obj["vertices"]]
        if len(verts) != 4:
            raise StepEditRefusal("ROLE_ASSERTION_FAILED", "validation", f"Không xác định được 4 đỉnh để kiểm chứng tâm {disp}.")
        mid02 = K.midpoint(verts[0], verts[2])
        mid13 = K.midpoint(verts[1], verts[3])
        if not (P.same_point(mid02, mid13) and P.same_point(pt_val, mid02)):
            raise StepEditRefusal(
                "ROLE_ASSERTION_FAILED",
                "validation",
                f"Điểm {disp} không phải tâm (giao điểm hai đường chéo) của tứ giác {target_poly or 'đáy'}.",
            )
        if shape in ("hình vuông", "hình chữ nhật"):
            if _m.norm_sq(verts[2] - verts[0]) != _m.norm_sq(verts[3] - verts[1]):
                raise StepEditRefusal("ROLE_ASSERTION_FAILED", "validation", f"Tứ giác {target_poly or 'đáy'} không thỏa mãn tính chất {shape}.")
        if shape == "hình vuông":
            if _m.norm_sq(verts[1] - verts[0]) != _m.norm_sq(verts[2] - verts[1]):
                raise StepEditRefusal("ROLE_ASSERTION_FAILED", "validation", f"Tứ giác {target_poly or 'đáy'} không phải hình vuông.")
        return


def verify_rebuilt_geometry(
    scene3d: dict[str, Any],
    *,
    before_scene: dict[str, Any],
    edited_intent: ParsedStepIntent,
    created_or_updated_ids: list[str],
    expected_perpendicular_bisector_for: tuple[str, str, str, str] | None = None,
) -> dict[str, Any]:
    """Run exact Fraction/Radical/Gram-metric geometric predicate verification and continuity validation."""
    metric = _scene_metric(scene3d)
    objs = scene3d.get("objects") or []
    by_id: dict[str, dict[str, Any]] = {o["id"]: o for o in objs if o.get("id")}
    mem: dict[str, Any] = {}
    for o in objs:
        if o.get("type") in ("section", "quantity"):
            continue
        val = _hydrate_object_value(o, mem)
        if val is not None:
            mem[o["id"]] = val
    for o in objs:
        if o.get("type") in ("section", "quantity"):
            val = _hydrate_object_value(o, mem)
            if val is not None:
                mem[o["id"]] = val

    # 1. Preserve root / GIVEN point coordinates immutably
    before_free = {
        o["id"]: o.get("xyz")
        for o in (before_scene.get("objects") or ())
        if o.get("type") == "point3" and o.get("origin") == "free"
    }
    for fid, old_xyz in before_free.items():
        if by_id.get(fid, {}).get("xyz") != old_xyz:
            raise StepEditRefusal(
                "GIVEN_POINT_MUTATION",
                "validation",
                f"Không được phép thay đổi tọa độ điểm gốc '{fid}'.",
            )

    checks_passed: list[str] = ["given_points_immutable"]
    with _m.using(metric):
        # 2. Verify every constructed object's exact geometric predicates
        for oid in created_or_updated_ids:
            o = by_id.get(oid)
            if o is None:
                continue
            prod = o.get("producer") or (o.get("source") or {}).get("instruction") or ""
            deps = list(o.get("depends") or ())

            if o.get("type") == "point3" and isinstance(mem.get(oid), Vec3):
                pt = mem[oid]
                if prod == "construct_point.midpoint":
                    p_ids = [d for d in deps if isinstance(mem.get(d), Vec3)]
                    if len(p_ids) != 2 or not P.same_point(pt, K.midpoint(mem[p_ids[0]], mem[p_ids[1]])):
                        raise StepEditRefusal("MIDPOINT_VERIFICATION_FAILED", "validation", f"Kiểm chứng trung điểm '{o.get('notation') or oid}' thất bại.")
                    checks_passed.append(f"midpoint:{oid}")

                elif prod == "construct_point.divide_segment":
                    rec = _recover_divide_segment_params(o, mem)
                    if rec is None:
                        raise StepEditRefusal("RATIO_VERIFICATION_FAILED", "validation", f"Thiếu tỉ lệ chia đoạn của '{oid}'.")
                    a_id, b_id, t = rec
                    if not (Fraction(0) < t < Fraction(1)) or not P.same_point(pt, K.divide_segment(mem[a_id], mem[b_id], t)):
                        raise StepEditRefusal("RATIO_VERIFICATION_FAILED", "validation", f"Điểm chia đoạn '{o.get('notation') or oid}' không đúng tỉ lệ trong đoạn.")
                    checks_passed.append(f"divide_segment:{oid}")

                elif prod == "construct_point.project_onto":
                    src_pt = next((mem[d] for d in deps if isinstance(mem.get(d), Vec3)), None)
                    tgt = next((mem[d] for d in deps if isinstance(mem.get(d), (Plane3, Line3))), None)
                    if src_pt is None or tgt is None:
                        raise StepEditRefusal("PROJECTION_VERIFICATION_FAILED", "validation", f"Hình chiếu '{oid}' thiếu toán hạng.")
                    if isinstance(tgt, Plane3):
                        if not P.point_on_plane(pt, tgt):
                            raise StepEditRefusal("PROJECTION_VERIFICATION_FAILED", "validation", f"Hình chiếu '{oid}' không nằm trên mặt phẳng chiếu.")
                        drop = pt - src_pt
                        if not drop.is_zero() and not P.parallel_vectors(drop, _m.normal_vector(tgt.normal)):
                            raise StepEditRefusal("PROJECTION_VERIFICATION_FAILED", "validation", f"Đoạn hạ hình chiếu tại '{oid}' không vuông góc với mặt phẳng.")
                    else:
                        if not P.point_on_line(pt, tgt):
                            raise StepEditRefusal("PROJECTION_VERIFICATION_FAILED", "validation", f"Hình chiếu '{oid}' không nằm trên đường thẳng chiếu.")
                        drop = pt - src_pt
                        if not drop.is_zero() and _m.dot(drop, tgt.direction) != 0:
                            raise StepEditRefusal("PROJECTION_VERIFICATION_FAILED", "validation", f"Đoạn hạ hình chiếu tại '{oid}' không vuông góc với đường thẳng.")
                    checks_passed.append(f"projection:{oid}")

                elif prod == "construct_point.intersect_line_plane":
                    ln = next((mem[d] for d in deps if isinstance(mem.get(d), Line3)), None)
                    pl = next((mem[d] for d in deps if isinstance(mem.get(d), Plane3)), None)
                    if ln is None or pl is None or not P.point_on_line(pt, ln) or not P.point_on_plane(pt, pl):
                        raise StepEditRefusal("INTERSECTION_VERIFICATION_FAILED", "validation", f"Giao điểm '{o.get('notation') or oid}' không thuộc đồng thời đường thẳng và mặt phẳng.")
                    checks_passed.append(f"intersect_line_plane:{oid}")

                elif prod in ("construct_point.intersect_line_line", "construct_point.intersect_lines"):
                    lns = [mem[d] for d in deps if isinstance(mem.get(d), Line3)]
                    if len(lns) != 2 or not P.point_on_line(pt, lns[0]) or not P.point_on_line(pt, lns[1]):
                        raise StepEditRefusal("INTERSECTION_VERIFICATION_FAILED", "validation", f"Giao điểm '{o.get('notation') or oid}' không thuộc hai đường thẳng.")
                    checks_passed.append(f"intersect_line_line:{oid}")

            elif o.get("type") == "plane3" and isinstance(mem.get(oid), Plane3):
                pl = mem[oid]
                if _m.conorm_sq(pl.normal) <= 0:
                    raise StepEditRefusal("DEGENERATE_PLANE", "validation", "Mặt phẳng bị suy biến (pháp tuyến bằng không).")
                if prod == "plane_perpendicular_to_line":
                    pt_v = next((mem[d] for d in deps if isinstance(mem.get(d), Vec3)), None)
                    ln_v = next((mem[d] for d in deps if isinstance(mem.get(d), Line3)), None)
                    if pt_v is None or ln_v is None:
                        raise StepEditRefusal("PLANE_VERIFICATION_FAILED", "validation", "Mặt phẳng thiếu điểm đi qua hoặc đường vuông góc.")
                    if not P.point_on_plane(pt_v, pl) or not P.line_perpendicular_plane(ln_v, pl):
                        raise StepEditRefusal("PERPENDICULAR_VERIFICATION_FAILED", "validation", "Mặt phẳng không thỏa mãn đi qua điểm hoặc không vuông góc với đường thẳng đã nêu.")
                    checks_passed.append(f"plane_perpendicular_to_line:{oid}")
                elif prod == "construct_plane":
                    pt_vs = [mem[d] for d in deps if isinstance(mem.get(d), Vec3)]
                    if len(pt_vs) < 3 or any(not P.point_on_plane(pv, pl) for pv in pt_vs):
                        raise StepEditRefusal("COPLANAR_VERIFICATION_FAILED", "validation", "Các điểm định nghĩa mặt phẳng không đồng phẳng.")
                    checks_passed.append(f"construct_plane:{oid}")

            elif o.get("type") == "line3" and isinstance(mem.get(oid), Line3):
                ln = mem[oid]
                if _m.norm_sq(ln.direction) <= 0:
                    raise StepEditRefusal("DEGENERATE_LINE", "validation", "Đường thẳng có vectơ chỉ phương bằng không.")
                if prod == "intersect_plane_plane":
                    pls = [mem[d] for d in deps if isinstance(mem.get(d), Plane3)]
                    if len(pls) != 2 or not (P.line_in_plane(ln, pls[0]) and P.line_in_plane(ln, pls[1])):
                        raise StepEditRefusal("INTERSECTION_VERIFICATION_FAILED", "validation", f"Giao tuyến '{oid}' không nằm đồng thời trên cả hai mặt phẳng.")
                    checks_passed.append(f"intersect_plane_plane:{oid}")

            elif o.get("type") == "section" and isinstance(mem.get(oid), Section):
                sec = mem[oid]
                pl = next((mem[d] for d in deps if isinstance(mem.get(d), Plane3)), None)
                if not sec.is_closed or len(sec.polygon) < 3 or (pl is not None and any(not P.point_on_plane(v, pl) for v in sec.polygon)):
                    raise StepEditRefusal("SECTION_VERIFICATION_FAILED", "validation", "Thiết diện mới không tạo thành đa giác khép kín hợp lệ trên mặt phẳng cắt.")
                checks_passed.append(f"section:{oid}")

            elif o.get("type") == "curved_solid" and isinstance(mem.get(oid), CurvedSolid):
                cs = mem[oid]
                if cs.radius_sq <= 0:
                    raise StepEditRefusal("DEGENERATE_CURVED_SOLID", "validation", "Bán kính khối cong không dương.")
                checks_passed.append(f"curved_solid:{oid}")

        # 2b. Verify every circumscribed sphere invariant still holds across ALL Polyhedron vertices
        before_by_id = {o["id"]: o for o in (before_scene.get("objects") or ()) if o.get("id")}
        before_mem: dict[str, Any] = {}
        for bo in before_scene.get("objects") or ():
            if bo.get("id") and bo.get("type") not in ("section", "quantity"):
                bval = _hydrate_object_value(bo, before_mem)
                if bval is not None:
                    before_mem[bo["id"]] = bval
        for bo in before_scene.get("objects") or ():
            boid = bo.get("id")
            if not boid or bo.get("type") != "curved_solid" or bo.get("curved_kind") != "ball":
                continue
            orig_ball = before_mem.get(boid)
            rebuilt_ball = mem.get(boid)
            if not isinstance(orig_ball, CurvedSolid) or not isinstance(rebuilt_ball, CurvedSolid):
                continue
            # Identify circumscribed polyhedra in the original verified scene
            circumscribed_solids: list[str] = []
            for so in before_scene.get("objects") or ():
                sid = so.get("id")
                sval = before_mem.get(sid)
                if sid and isinstance(sval, Polyhedron) and sval.vertices:
                    if all(_m.norm_sq(v - orig_ball.anchor) == orig_ball.radius_sq for v in sval.vertices):
                        circumscribed_solids.append(sid)
            if not circumscribed_solids and ("ngoai_tiep" in boid.lower() or "ngoại tiếp" in str(bo.get("label") or "").lower()):
                circumscribed_solids = [
                    so["id"]
                    for so in objs
                    if so.get("id") and isinstance(mem.get(so["id"]), Polyhedron) and mem[so["id"]].vertices
                ]
            for sid in circumscribed_solids:
                rsol = mem.get(sid)
                if isinstance(rsol, Polyhedron):
                    for v in rsol.vertices:
                        if _m.norm_sq(v - rebuilt_ball.anchor) != rebuilt_ball.radius_sq:
                            raise StepEditRefusal(
                                "DOWNSTREAM_CIRCUMSCRIBED_SPHERE_BROKEN",
                                "validation",
                                "Phép dựng mới làm tâm ở bước sau không còn cách đều mọi đỉnh của khối đa diện, nên mặt cầu ngoại tiếp không còn hợp lệ.",
                            )
                    checks_passed.append(f"circumscribed_sphere_equidistant:{boid}")

        # 3. Special mandatory bisector check when Step 8 defines perpendicular bisector via midpoint + perp plane
        if expected_perpendicular_bisector_for is not None:
            mid_id, a_id, b_id, pl_id = expected_perpendicular_bisector_for
            pa, pb, pm, pl = mem[a_id], mem[b_id], mem[mid_id], mem[pl_id]
            ab_line = Line3.through(pa, pb)
            if not (
                P.same_point(pm, K.midpoint(pa, pb))
                and P.point_on_plane(pm, pl)
                and P.line_perpendicular_plane(ab_line, pl)
                and _m.norm_sq(pa - pm) == _m.norm_sq(pb - pm)
            ):
                raise StepEditRefusal(
                    "BISECTOR_VERIFICATION_FAILED",
                    "validation",
                    f"Mặt phẳng không phải mặt phẳng trung trực của đoạn {a_id}{b_id}.",
                )
            checks_passed.append(f"perpendicular_bisector:{pl_id}")

    # 4. Continuity validation across all 7 invariants
    issues = validate_construction_continuity(scene3d)
    if issues:
        raise StepEditRefusal(
            issues[0].get("code", "CONTINUITY_VALIDATION_FAILED"),
            "validation",
            f"Kiểm chứng tính liên tục hình học không đạt: {issues[0].get('detail', 'lỗi chuỗi dựng hình')}.",
            details={"continuity_issues": issues},
        )
    checks_passed.append("continuity_invariants_7_of_7")

    return {
        "valid": True,
        "passed": True,
        "checks_passed": checks_passed,
        "exact_arithmetic": True,
        "edited_operations": [c.op for c in edited_intent.clauses],
        "continuity": {"passed": True, "issues": []},
    }


def _semantic_equivalence_check(
    parsed_new: ParsedStepIntent,
    previous_instruction: str,
    target_objs: list[dict[str, Any]],
    absorbed_objs: list[dict[str, Any]],
    scene3d: dict[str, Any],
) -> tuple[bool, dict[str, Any] | None]:
    """Detect whether the new instruction is mathematically identical to the existing step (wording-only edit)."""
    try:
        parsed_old = parse_vietnamese_construction_step(previous_instruction)
        if parsed_old.intent_signature == parsed_new.intent_signature:
            return True, {"mode": "exact_intent_match", "previous_intent": parsed_old.to_dict()}
    except StepEditRefusal:
        parsed_old = None

    # Check structural equivalence: e.g., reworded `"Vẽ mặt phẳng trung trực (α) của đoạn thẳng AB"`
    # on an existing `perpendicular_bisector_plane`, or `"Dựng mặt phẳng (α) qua H vuông góc với AB"` when H already exists!
    if len(parsed_new.clauses) == 1 and len(target_objs) == 1:
        c = parsed_new.clauses[0]
        tgt = target_objs[0]
        t_prod = tgt.get("producer") or (tgt.get("source") or {}).get("instruction") or ""
        t_not = _canon_plane_name(tgt.get("notation")) if tgt.get("type") == "plane3" else tgt.get("notation")
        if c.op == "midpoint" and t_prod == "construct_point.midpoint":
            if len(c.point_inputs) == 2 and set(c.point_inputs) == set(tgt.get("depends") or ()) and (c.output_symbol or t_not) == t_not:
                return True, {"mode": "existing_midpoint_match"}
        if c.op == "perpendicular_bisector_plane" and t_prod == "plane_perpendicular_to_line":
            # Check absorbed/depends form midpoint(A, B) + line(A, B)
            mid_dep = next((o for o in absorbed_objs if (o.get("producer") or "") == "construct_point.midpoint" and o.get("notation") is None), None)
            if mid_dep and set(mid_dep.get("depends") or ()) == set(c.point_inputs) and (c.output_symbol in (None, t_not)):
                return True, {"mode": "existing_bisector_match"}
        if c.op == "plane_perpendicular_to_line" and t_prod == "plane_perpendicular_to_line" and (c.output_symbol in (None, t_not)) and not c.params.get("point_role_assertion"):
            objs_by_id = {o["id"]: o for o in (scene3d.get("objects") or ()) if o.get("id")}
            tgt_deps = list(tgt.get("depends") or ())
            pt_dep = next((objs_by_id[d] for d in tgt_deps if objs_by_id.get(d, {}).get("type") == "point3"), None)
            ln_dep = next((objs_by_id[d] for d in tgt_deps if objs_by_id.get(d, {}).get("type") == "line3"), None)
            if pt_dep and ln_dep and c.point_inputs:
                pt_sym = _normalize_vi_math(c.point_inputs[0]).upper()
                cand_pt = next(
                    (
                        o
                        for o in objs_by_id.values()
                        if o.get("type") == "point3"
                        and _normalize_vi_math(o.get("notation") or o.get("reference") or o["id"]).replace("_prime", "'").upper() == pt_sym
                    ),
                    None,
                )
                if cand_pt and cand_pt.get("id") == pt_dep.get("id") and cand_pt.get("xyz") and pt_dep.get("xyz"):
                    v_cand = Vec3.of(*cand_pt["xyz"])
                    v_tgt = Vec3.of(*pt_dep["xyz"])
                    if P.same_point(v_cand, v_tgt):
                        ln_dir = Vec3.of(*ln_dep["direction"])
                        cand_dir = None
                        if len(c.point_inputs) >= 3:
                            p_a = next((o for o in objs_by_id.values() if o.get("type") == "point3" and _normalize_vi_math(o.get("notation") or o["id"]).upper() == _normalize_vi_math(c.point_inputs[1]).upper()), None)
                            p_b = next((o for o in objs_by_id.values() if o.get("type") == "point3" and _normalize_vi_math(o.get("notation") or o["id"]).upper() == _normalize_vi_math(c.point_inputs[2]).upper()), None)
                            if p_a and p_b and p_a.get("xyz") and p_b.get("xyz"):
                                d_vec = Vec3.of(*p_b["xyz"]) - Vec3.of(*p_a["xyz"])
                                if not d_vec.is_zero():
                                    cand_dir = d_vec
                        if cand_dir is not None and P.parallel_vectors(ln_dir, cand_dir):
                            return True, {"mode": "existing_perp_plane_match"}
    return False, None


def _apply_notation_renames(text: str, renames: dict[str, str]) -> str:
    """Propagate renamed mathematical notations (e.g., `(α)` -> `(P)`) cleanly across downstream step labels."""
    out = text
    for old_sym, new_sym in renames.items():
        if not old_sym or old_sym == new_sym:
            continue
        if old_sym.startswith("(") and old_sym.endswith(")"):
            out = out.replace(old_sym, new_sym)
        else:
            out = re.sub(
                rf"(?<![A-Za-z0-9_]){re.escape(old_sym)}(?![A-Za-z0-9_])",
                new_sym,
                out,
            )
    return out


# ── Main Entry Point: Execute Step Edit Atomically ─────────────────────────────
def execute_step_edit(
    *,
    scene3d: dict[str, Any],
    step_id: str,
    step_index: int,
    previous_instruction: str,
    edited_instruction: str,
    target_ids: list[str] | None = None,
    absorbed_ids: list[str] | None = None,
    step_overrides: dict[str, str] | None = None,
    prior_step_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Parse, plan, topologically rebuild, and verify an edited construction step atomically."""
    t_start = time.perf_counter()
    timings: dict[str, float] = {}
    before_snapshot = copy.deepcopy(scene3d)
    before_digest = _scene_digest(before_snapshot)
    existing_overrides = dict(step_overrides or {})

    # ── Stage 1: Parse Edited Vietnamese Step ──────────────────────────────────
    t0 = time.perf_counter()
    parsed_new = parse_vietnamese_construction_step(edited_instruction)
    timings["parser_ms"] = round((time.perf_counter() - t0) * 1000.0, 3)

    # ── Stage 2: Build Dependency Graph & Locate Edited Target Scope ───────────
    t_plan = time.perf_counter()
    graph = build_construction_dependency_graph(
        before_snapshot,
        target_ids=target_ids,
        step_id=step_id,
        step_index=step_index,
        absorbed_ids=absorbed_ids,
    )
    all_objs: list[dict[str, Any]] = copy.deepcopy(before_snapshot.get("objects") or [])
    by_id: dict[str, dict[str, Any]] = {o["id"]: o for o in all_objs if o.get("id")}
    resolved_target_ids = [tid for tid in (target_ids or ()) if tid in by_id]
    if not resolved_target_ids:
        # Fallback: locate by step_index formation created_ids
        f_steps = (before_snapshot.get("formation") or {}).get("steps") or []
        if 0 <= step_index < len(f_steps):
            resolved_target_ids = [
                oid
                for oid in (f_steps[step_index].get("created_ids") or f_steps[step_index].get("focus_ids") or ())
                if oid in by_id and by_id[oid].get("type") != "quantity"
            ]
    if not resolved_target_ids:
        raise StepEditRefusal(
            "STEP_TARGET_NOT_FOUND",
            "dependency_analysis",
            f"Không xác định được đối tượng hình học tương ứng với bước {step_index + 1}.",
        )

    primary_id = resolved_target_ids[0]
    primary_obj = by_id[primary_id]
    # Identify helper objects exclusively owned by this UI step (absorbed or inline_step_parent == primary_id)
    target_set = set(resolved_target_ids)
    exclusive_helpers: list[str] = []
    for hid in (absorbed_ids or ()):
        if hid in by_id and hid not in target_set:
            # Exclusive if all consumers are inside target_set + resolved_target_ids
            if set(graph["consumers_of"].get(hid, ())) <= target_set:
                exclusive_helpers.append(hid)
    # Also scan unnamed auxiliary midpoints/lines referenced ONLY by `primary_id`, or earlier inline sub-objects
    for dep in list(primary_obj.get("depends") or ()):
        if dep not in by_id or dep in target_set or dep in exclusive_helpers:
            continue
        dep_obj = by_id[dep]
        dep_src = dep_obj.get("source") or {}
        if dep_src.get("inline_step_parent") == primary_id:
            if set(graph["consumers_of"].get(dep, ())) <= (target_set | set(exclusive_helpers)):
                exclusive_helpers.append(dep)
        elif dep_obj.get("type") == "point3" and dep_obj.get("origin") == "derived" and not dep_obj.get("notation"):
            if set(graph["consumers_of"].get(dep, ())) <= (target_set | set(exclusive_helpers)):
                exclusive_helpers.append(dep)

    target_objs = [by_id[tid] for tid in resolved_target_ids]
    absorbed_objs = [by_id[hid] for hid in exclusive_helpers if hid in by_id]
    downstream_ids = _transitive_closure(target_set, graph["consumers_of"]) - target_set - set(exclusive_helpers)

    event_step_of = graph["event_step_of"]
    primary_ev_step = max((event_step_of.get(oid, 0) for oid in (target_set | set(exclusive_helpers))), default=0)
    prior_set = (set(prior_step_ids) - target_set - set(exclusive_helpers) - downstream_ids) if prior_step_ids else set()
    post_step_ids = {
        oid
        for oid, o in by_id.items()
        if o.get("origin") != "free"
        and oid not in target_set
        and oid not in exclusive_helpers
        and oid not in downstream_ids
        and oid not in prior_set
        and event_step_of.get(oid, 0) > primary_ev_step
    }

    # Verify Registry availability for every parsed clause
    t_reg = time.perf_counter()
    for reg_op in parsed_new.registry_operations:
        if reg_op not in REGISTRY and reg_op not in {
            "plane_perpendicular_to_line",
            "plane_parallel_to_plane",
            "construct_plane",
            "construct_segment",
            "construct_line",
            "construct_polygon",
            "construct_solid",
        }:
            raise StepEditRefusal(
                "UNSUPPORTED_REGISTRY_OPERATION",
                "registry",
                f"Thao tác '{reg_op}' chưa được hỗ trợ trong thư viện Registry.",
            )
    timings["registry_ms"] = round((time.perf_counter() - t_reg) * 1000.0, 3)

    # Check if this is purely a text-only equivalent edit
    is_equiv, equiv_info = _semantic_equivalence_check(
        parsed_new,
        previous_instruction,
        target_objs,
        absorbed_objs,
        before_snapshot,
    )
    if is_equiv:
        t_val = time.perf_counter()
        equiv_scene = copy.deepcopy(before_snapshot)
        if not (equiv_scene.get("formation") or {}).get("steps"):
            equiv_scene["formation"] = _build_formation(
                equiv_scene.get("objects") or [],
                equiv_scene.get("events") or [],
                equiv_scene.get("free_objects") or [],
            )
        enrich_construction_continuity(equiv_scene)
        val_res = verify_rebuilt_geometry(
            equiv_scene,
            before_scene=before_snapshot,
            edited_intent=parsed_new,
            created_or_updated_ids=resolved_target_ids,
        )
        timings["validation_ms"] = round((time.perf_counter() - t_val) * 1000.0, 3)
        timings["planner_ms"] = round((time.perf_counter() - t_plan) * 1000.0, 3)
        timings["kernel_ms"] = 0.0
        timings["dependency_rebuild_ms"] = 0.0
        timings["scene3d_build_ms"] = 0.0
        timings["total_ms"] = round((time.perf_counter() - t_start) * 1000.0, 3)
        next_overrides = dict(existing_overrides)
        next_overrides[primary_id] = parsed_new.normalized_text
        return {
            "status": "committed",
            "mode": "NO_OP_EQUIVALENT",
            "equivalence_info": equiv_info,
            "scene3d": equiv_scene,
            "step_overrides": next_overrides,
            "normalized_intent": parsed_new.to_dict(),
            "registry_operations": list(parsed_new.registry_operations),
            "dependency_summary": {
                "edited_target_ids": resolved_target_ids,
                "created_ids": [],
                "reused_ids": resolved_target_ids,
                "retired_ids": [],
                "recomputed_ids": [],
                "skipped_unaffected_ids": [o["id"] for o in all_objs if o["id"] not in resolved_target_ids],
                "cycle_detected": False,
            },
            "validation_result": val_res,
            "before_after_diff": {"changed": False, "changed_objects": {}},
            "before_scene_digest": before_digest,
            "after_scene_digest": before_digest,
            "stage_timings_ms": timings,
            "primary_target_id": primary_id,
        }

    # ── Stage 3: Execute Edited Clauses & Topological Downstream Closure ────────
    metric = _scene_metric(before_snapshot)
    available_symbols = _symbol_index_before_step(
        before_snapshot,
        graph,
        excluded_ids=target_set | set(exclusive_helpers) | downstream_ids,
        allow_post_step=False,
        target_step_anchor=primary_ev_step,
        prior_step_ids=prior_set if prior_set else None,
    )

    # Seed memory with UNAFFECTED objects ONLY (reusing verified state without recomputing!)
    unaffected_ids = [
        oid
        for oid in graph["topo_order"]
        if oid not in target_set and oid not in exclusive_helpers and oid not in downstream_ids
    ]
    mem: dict[str, Any] = {}
    for oid in unaffected_ids:
        val = _hydrate_object_value(by_id[oid], mem)
        if val is not None:
            mem[oid] = val

    timings["planner_ms"] = round((time.perf_counter() - t_plan) * 1000.0, 3)
    t_kernel = time.perf_counter()

    # Local scope for newly created/reused items within this edit
    local_objects_by_symbol: dict[str, dict[str, Any]] = {}
    newly_created_objs: list[dict[str, Any]] = []
    reused_ids: list[str] = []
    retired_helper_ids: list[str] = list(exclusive_helpers)
    kept_helpers: list[str] = []
    updated_ids: list[str] = []
    created_inline_point_for_bisector: tuple[str, str, str] | None = None  # (pt_id, a_id, b_id)

    def _next_helper_id(prefix: str) -> str:
        cand = prefix
        i = 2
        while cand in by_id:
            cand = f"{prefix}_{i}"
            i += 1
        return cand

    with _m.using(metric):
        try:
            n_clauses = len(parsed_new.clauses)
            for c_idx, clause in enumerate(parsed_new.clauses):
                is_final_clause = c_idx == n_clauses - 1

                # Lookup symbol in local_objects first (allows earlier clause in compound step to feed later clause!)
                def _find_pt(sym: str, act: str) -> str:
                    norm = _normalize_vi_math(sym).upper()
                    if norm in local_objects_by_symbol and local_objects_by_symbol[norm].get("type") == "point3":
                        return local_objects_by_symbol[norm]["id"]
                    return _resolve_point_id(sym, available_symbols, {}, by_id, downstream_ids, post_step_ids, act)

                def _reuse_or_assign_point(pt_sym: str, coords: Vec3, producer: str, deps: list[str], label_text: str, extra_source: dict[str, Any] | None = None) -> dict[str, Any]:
                    norm = _normalize_vi_math(pt_sym).upper()
                    existing_cands = [o for o in available_symbols.get(norm, ()) if o.get("type") == "point3"]
                    if existing_cands:
                        ex = existing_cands[0]
                        ex_val = mem.get(ex["id"])
                        if isinstance(ex_val, Vec3) and P.same_point(ex_val, coords):
                            if ex["id"] not in reused_ids:
                                reused_ids.append(ex["id"])
                            local_objects_by_symbol[norm] = ex
                            return ex
                        raise StepEditRefusal(
                            "SYMBOL_CONFLICT",
                            "kernel",
                            f"Điểm {_display_sym(norm)} đã tồn tại ở bước trước nhưng ở vị trí khác với phép dựng mới.",
                        )
                    # Determine ID: reuse `primary_id` if this is the final/only clause targeting a point step!
                    use_primary = is_final_clause and primary_obj.get("type") == "point3"
                    oid = primary_id if use_primary else _normalize_vi_math(pt_sym).replace("'", "_prime")
                    if not use_primary and oid in by_id and oid not in set(exclusive_helpers):
                        # If existing point belongs downstream or post-step, forbid silent overwrite!
                        if oid in downstream_ids or oid in post_step_ids:
                            raise StepEditRefusal(
                                "SYMBOL_CONFLICT",
                                "dependency_analysis",
                                f"Tên điểm {_display_sym(norm)} đã được dùng ở bước sau.",
                            )
                        oid = _next_helper_id(oid)
                    obj = primary_obj if use_primary else {
                        "id": oid,
                        "render": "point_marker",
                        "display_role": "visual_owner",
                        "origin": "derived",
                        "display_group": ["construction"],
                        "visual_transform": {"translate": [0, 0, 0], "scale": 1},
                        "formation_roles": ["CONSTRUCT_AUXILIARY_GEOMETRY"],
                    }
                    disp = _display_sym(pt_sym)
                    obj.update({
                        "id": oid,
                        "type": "point3",
                        "label": label_text,
                        "notation": disp,
                        "reference": disp,
                        "role": f"Điểm {disp}",
                        "display_label": label_text,
                        "origin": "derived",
                        "producer": producer,
                        "depends": list(deps),
                        "xyz": _exact_xyz_list(coords),
                        "source": {
                            "instruction": producer,
                            "binding": "TEXT_RELATION",
                            **(extra_source or {}),
                            **({"inline_step_parent": primary_id} if not use_primary else {}),
                        },
                    })
                    mem[oid] = coords
                    by_id[oid] = obj
                    local_objects_by_symbol[norm] = obj
                    if not use_primary:
                        newly_created_objs.append(obj)
                    else:
                        if oid not in updated_ids:
                            updated_ids.append(oid)
                    return obj

                if clause.op == "midpoint":
                    a_id = _find_pt(clause.point_inputs[0], "xác định trung điểm")
                    b_id = _find_pt(clause.point_inputs[1], "xác định trung điểm")
                    pt_sym = clause.output_symbol or (primary_obj.get("notation") or "M")
                    mid_val = K.midpoint(mem[a_id], mem[b_id])
                    pt_obj = _reuse_or_assign_point(
                        pt_sym,
                        mid_val,
                        "construct_point.midpoint",
                        [a_id, b_id],
                        f"Trung điểm {_display_sym(pt_sym)} của {a_id}{b_id}",
                    )
                    if not is_final_clause:
                        created_inline_point_for_bisector = (pt_obj["id"], a_id, b_id)

                elif clause.op == "divide_segment":
                    a_id = _find_pt(clause.params["a"], "chia đoạn thẳng")
                    b_id = _find_pt(clause.params["b"], "chia đoạn thẳng")
                    t_val = Fraction(clause.params["ratio"])
                    pt_val = K.divide_segment(mem[a_id], mem[b_id], t_val)
                    pt_sym = clause.output_symbol or (primary_obj.get("notation") or "M")
                    _reuse_or_assign_point(
                        pt_sym,
                        pt_val,
                        "construct_point.divide_segment",
                        [a_id, b_id],
                        f"Điểm {_display_sym(pt_sym)} trên {a_id}{b_id} (tỉ lệ {t_val})",
                        extra_source={"params": {"a": a_id, "b": b_id, "ratio": str(t_val)}},
                    )

                elif clause.op == "centroid":
                    p0 = _find_pt(clause.point_inputs[0], "xác định trọng tâm")
                    p1 = _find_pt(clause.point_inputs[1], "xác định trọng tâm")
                    p2 = _find_pt(clause.point_inputs[2], "xác định trọng tâm")
                    c_val = (mem[p0] + mem[p1] + mem[p2]).scale(Fraction(1, 3))
                    pt_sym = clause.output_symbol or (primary_obj.get("notation") or "G")
                    _reuse_or_assign_point(
                        pt_sym,
                        c_val,
                        "construct_point.centroid",
                        [p0, p1, p2],
                        f"Trọng tâm {_display_sym(pt_sym)} của tam giác {p0}{p1}{p2}",
                    )

                elif clause.op in ("perpendicular_bisector_plane", "plane_perpendicular_to_line"):
                    if not is_final_clause or primary_obj.get("type") != "plane3":
                        raise StepEditRefusal(
                            "STEP_TYPE_MISMATCH",
                            "planner",
                            f"Bước đang sửa tạo đối tượng kiểu '{primary_obj.get('type')}', không tương thích với phép dựng mặt phẳng ở mệnh đề '{clause.raw_clause}'.",
                        )
                    if clause.op == "perpendicular_bisector_plane":
                        a_id = _find_pt(clause.point_inputs[0], "dựng mặt phẳng trung trực")
                        b_id = _find_pt(clause.point_inputs[1], "dựng mặt phẳng trung trực")
                        mid_val = K.midpoint(mem[a_id], mem[b_id])
                        mid_helper = next(
                            (
                                by_id[hid]
                                for hid in exclusive_helpers
                                if by_id[hid].get("type") == "point3"
                                and (by_id[hid].get("producer") or "") == "construct_point.midpoint"
                            ),
                            None,
                        )
                        if mid_helper is not None:
                            mid_helper.update({
                                "depends": [a_id, b_id],
                                "xyz": _exact_xyz_list(mid_val),
                                "label": f"Trung điểm của {a_id} và {b_id}",
                            })
                            mem[mid_helper["id"]] = mid_val
                            if mid_helper["id"] in retired_helper_ids:
                                retired_helper_ids.remove(mid_helper["id"])
                            kept_helpers.append(mid_helper["id"])
                            mid_id = mid_helper["id"]
                        else:
                            mid_id = _next_helper_id(f"mid_{a_id}_{b_id}")
                            h_obj = {
                                "id": mid_id,
                                "type": "point3",
                                "label": f"Trung điểm của {a_id} và {b_id}",
                                "notation": None,
                                "reference": f"Trung điểm của {a_id} và {b_id}",
                                "role": "Điểm dựng phụ",
                                "origin": "derived",
                                "producer": "construct_point.midpoint",
                                "depends": [a_id, b_id],
                                "render": "point_marker",
                                "display_role": "visual_owner",
                                "display_group": ["construction"],
                                "visual_transform": {"translate": [0, 0, 0], "scale": 1},
                                "formation_roles": ["CONSTRUCT_AUXILIARY_GEOMETRY"],
                                "xyz": _exact_xyz_list(mid_val),
                                "source": {"instruction": "construct_point.midpoint", "binding": "AUXILIARY", "inline_step_parent": primary_id},
                            }
                            mem[mid_id] = mid_val
                            by_id[mid_id] = h_obj
                            newly_created_objs.append(h_obj)
                        # Line through A, B
                        ln_id = next(
                            (
                                cand["id"]
                                for cand in all_objs
                                if cand.get("type") == "line3"
                                and set(cand.get("depends") or ()) == {a_id, b_id}
                                and cand["id"] not in downstream_ids
                            ),
                            None,
                        )
                        if ln_id is not None and ln_id in retired_helper_ids:
                            retired_helper_ids.remove(ln_id)
                            kept_helpers.append(ln_id)
                            if ln_id not in mem:
                                mem[ln_id] = Line3.through(mem[a_id], mem[b_id])
                        elif ln_id is None:
                            ln_id = _next_helper_id(f"line_{a_id}_{b_id}")
                            ln_val = Line3.through(mem[a_id], mem[b_id])
                            ln_obj = {
                                "id": ln_id,
                                "type": "line3",
                                "label": f"{a_id}{b_id}",
                                "notation": f"{a_id}{b_id}",
                                "reference": f"{a_id}{b_id}",
                                "role": "Đường thẳng",
                                "origin": "derived",
                                "producer": "construct_line",
                                "depends": [a_id, b_id],
                                "render": "line",
                                "display_role": "visual_owner",
                                "display_group": ["construction"],
                                "visual_transform": {"translate": [0, 0, 0], "scale": 1},
                                "formation_roles": ["CONSTRUCT_AUXILIARY_GEOMETRY"],
                                "point": _exact_xyz_list(ln_val.point),
                                "direction": _exact_xyz_list(ln_val.direction),
                                "source": {"instruction": "construct_line", "inline_step_parent": primary_id},
                            }
                            mem[ln_id] = ln_val
                            by_id[ln_id] = ln_obj
                            newly_created_objs.append(ln_obj)
                        pt_id = mid_id
                        ln_ref_id = ln_id
                    else:
                        # plane_perpendicular_to_line(point=H, line=AB or named line)
                        pt_sym = clause.point_inputs[0]
                        pt_id = _find_pt(pt_sym, f"dựng mặt phẳng {clause.output_symbol or primary_obj.get('notation') or ''}")
                        if len(clause.point_inputs) >= 3:
                            a_id = _find_pt(clause.point_inputs[1], "dựng mặt phẳng vuông góc")
                            b_id = _find_pt(clause.point_inputs[2], "dựng mặt phẳng vuông góc")
                            # Reuse an existing line through (a_id, b_id) if already built before or owned here
                            ln_ref_id = next(
                                (
                                    cand["id"]
                                    for cand in all_objs
                                    if cand.get("type") == "line3"
                                    and set(cand.get("depends") or ()) == {a_id, b_id}
                                    and cand["id"] not in downstream_ids
                                    and cand["id"] not in post_step_ids
                                ),
                                None,
                            )
                            if ln_ref_id is not None:
                                if ln_ref_id in retired_helper_ids:
                                    retired_helper_ids.remove(ln_ref_id)
                                    kept_helpers.append(ln_ref_id)
                                if ln_ref_id not in mem:
                                    mem[ln_ref_id] = Line3.through(mem[a_id], mem[b_id])
                                    by_id[ln_ref_id]["point"] = _exact_xyz_list(mem[ln_ref_id].point)
                                    by_id[ln_ref_id]["direction"] = _exact_xyz_list(mem[ln_ref_id].direction)
                            else:
                                ln_ref_id = _next_helper_id(f"line_{a_id}_{b_id}")
                                ln_val = Line3.through(mem[a_id], mem[b_id])
                                ln_obj = {
                                    "id": ln_ref_id,
                                    "type": "line3",
                                    "label": f"{a_id}{b_id}",
                                    "notation": f"{a_id}{b_id}",
                                    "reference": f"{a_id}{b_id}",
                                    "role": "Đường thẳng",
                                    "origin": "derived",
                                    "producer": "construct_line",
                                    "depends": [a_id, b_id],
                                    "render": "line",
                                    "display_role": "visual_owner",
                                    "display_group": ["construction"],
                                    "visual_transform": {"translate": [0, 0, 0], "scale": 1},
                                    "formation_roles": ["CONSTRUCT_AUXILIARY_GEOMETRY"],
                                    "point": _exact_xyz_list(ln_val.point),
                                    "direction": _exact_xyz_list(ln_val.direction),
                                    "source": {"instruction": "construct_line", "inline_step_parent": primary_id},
                                }
                                mem[ln_ref_id] = ln_val
                                by_id[ln_ref_id] = ln_obj
                                newly_created_objs.append(ln_obj)
                            if (
                                created_inline_point_for_bisector is not None
                                and created_inline_point_for_bisector[0] == pt_id
                                and set(created_inline_point_for_bisector[1:]) == {a_id, b_id}
                            ):
                                expected_bisector = (pt_id, a_id, b_id, primary_id)
                            else:
                                expected_bisector = None
                        else:
                            ln_tok = _normalize_vi_math(clause.line_inputs[0])
                            ln_cand = next(
                                (
                                    o["id"]
                                    for o in available_symbols.get(ln_tok, ())
                                    if o.get("type") == "line3"
                                ),
                                None,
                            )
                            if ln_cand is None:
                                raise StepEditRefusal(
                                    "MISSING_DEPENDENCY",
                                    "planner",
                                    f"Không thể dựng mặt phẳng vì chưa xác định được đường thẳng '{clause.line_inputs[0]}'.",
                                )
                            ln_ref_id = ln_cand
                            expected_bisector = None

                    if clause.params.get("point_role_assertion"):
                        _verify_point_role_assertion(
                            clause.params["point_role_assertion"],
                            pt_id,
                            mem[pt_id],
                            mem,
                            by_id,
                            available_symbols,
                            all_objs,
                        )
                    if pt_id not in reused_ids and pt_id not in {o["id"] for o in newly_created_objs}:
                        reused_ids.append(pt_id)
                    pl_val = K.plane_through_point_perpendicular_to(mem[pt_id], mem[ln_ref_id])
                    pname = clause.output_symbol or primary_obj.get("notation") or "(α)"
                    pt_disp = by_id[pt_id].get("notation") or pt_id
                    ln_disp = by_id[ln_ref_id].get("notation") or ln_ref_id
                    new_label = f"Mặt phẳng {pname} qua {pt_disp} và vuông góc với {ln_disp}"
                    primary_obj.update({
                        "label": new_label,
                        "notation": pname,
                        "reference": pname,
                        "display_label": new_label,
                        "producer": "plane_perpendicular_to_line",
                        "depends": [pt_id, ln_ref_id],
                        "point": _exact_xyz_list(pl_val.point),
                        "normal": _exact_xyz_list(pl_val.normal),
                        "source": {**(primary_obj.get("source") or {}), "instruction": "plane_perpendicular_to_line"},
                    })
                    mem[primary_id] = pl_val
                    updated_ids.append(primary_id)

                elif clause.op == "plane_through_three_points":
                    if not is_final_clause or primary_obj.get("type") != "plane3":
                        raise StepEditRefusal(
                            "STEP_TYPE_MISMATCH",
                            "planner",
                            "Bước đang sửa không phải bước dựng mặt phẳng.",
                        )
                    pt_ids = [_find_pt(s, f"dựng mặt phẳng {clause.output_symbol or ''}") for s in clause.point_inputs]
                    p0, p1, p2 = mem[pt_ids[0]], mem[pt_ids[1]], mem[pt_ids[2]]
                    pl_val = Plane3.through(p0, p1, p2)
                    for extra in pt_ids[3:]:
                        if not P.point_on_plane(mem[extra], pl_val):
                            raise GeometryError("NON_COPLANAR_POINTS", f"Điểm '{extra}' không nằm trên mặt phẳng qua ba điểm đầu.")
                    pname = clause.output_symbol or f"({''.join(pt_ids)})"
                    primary_obj.update({
                        "label": pname,
                        "notation": pname,
                        "reference": pname,
                        "display_label": pname,
                        "producer": "construct_plane",
                        "depends": list(pt_ids),
                        "point": _exact_xyz_list(pl_val.point),
                        "normal": _exact_xyz_list(pl_val.normal),
                        "source": {**(primary_obj.get("source") or {}), "instruction": "construct_plane"},
                    })
                    mem[primary_id] = pl_val
                    updated_ids.append(primary_id)
                    expected_bisector = None

                elif clause.op == "plane_parallel_to_plane":
                    if not is_final_clause or primary_obj.get("type") != "plane3":
                        raise StepEditRefusal("STEP_TYPE_MISMATCH", "planner", "Bước đang sửa không phải bước dựng mặt phẳng.")
                    pt_id = _find_pt(clause.point_inputs[0], "dựng mặt phẳng song song")
                    ref_id = _resolve_plane_id(
                        clause.plane_inputs[0],
                        available_symbols,
                        local_objects_by_symbol,
                        by_id,
                        downstream_ids,
                        post_step_ids,
                        "dựng mặt phẳng song song",
                    )
                    pl_val = K.plane_through_point_parallel_to(mem[pt_id], mem[ref_id])
                    pname = clause.output_symbol or primary_obj.get("notation") or "(α)"
                    ref_not = by_id[ref_id].get("notation") or clause.plane_inputs[0]
                    new_label = f"Mặt phẳng {pname} qua {by_id[pt_id].get('notation') or pt_id} và song song với {ref_not}"
                    primary_obj.update({
                        "label": new_label,
                        "notation": pname,
                        "reference": pname,
                        "display_label": new_label,
                        "producer": "construct_plane",
                        "depends": [pt_id, ref_id],
                        "point": _exact_xyz_list(pl_val.point),
                        "normal": _exact_xyz_list(pl_val.normal),
                        "source": {**(primary_obj.get("source") or {}), "instruction": "plane_parallel_to_plane"},
                    })
                    mem[primary_id] = pl_val
                    updated_ids.append(primary_id)
                    expected_bisector = None

                elif clause.op == "orthogonal_projection_plane":
                    src_id = _find_pt(clause.point_inputs[0], "hạ hình chiếu vuông góc")
                    pl_id = _resolve_plane_id(
                        clause.plane_inputs[0],
                        available_symbols,
                        local_objects_by_symbol,
                        by_id,
                        downstream_ids,
                        post_step_ids,
                        "hạ hình chiếu vuông góc",
                    )
                    foot_val = K.project_point_onto_plane(mem[src_id], mem[pl_id])
                    img_sym = clause.output_symbol or "H"
                    _reuse_or_assign_point(
                        img_sym,
                        foot_val,
                        "construct_point.project_onto",
                        [src_id, pl_id],
                        f"Hình chiếu {_display_sym(img_sym)} của {src_id} lên {clause.plane_inputs[0]}",
                    )

                elif clause.op == "orthogonal_projection_line":
                    src_id = _find_pt(clause.point_inputs[0], "hạ hình chiếu vuông góc lên đường thẳng")
                    if len(clause.point_inputs) >= 3:
                        la = _find_pt(clause.point_inputs[1], "xác định đường thẳng chiếu")
                        lb = _find_pt(clause.point_inputs[2], "xác định đường thẳng chiếu")
                        ln_val = Line3.through(mem[la], mem[lb])
                        ln_id = next(
                            (o["id"] for o in all_objs if o.get("type") == "line3" and set(o.get("depends") or ()) == {la, lb} and o["id"] not in downstream_ids),
                            None,
                        )
                        if ln_id is None:
                            ln_id = _next_helper_id(f"line_{la}_{lb}")
                            ln_obj = {
                                "id": ln_id,
                                "type": "line3",
                                "label": f"{la}{lb}",
                                "notation": f"{la}{lb}",
                                "reference": f"{la}{lb}",
                                "role": "Đường thẳng",
                                "origin": "derived",
                                "producer": "construct_line",
                                "depends": [la, lb],
                                "render": "line",
                                "display_role": "visual_owner",
                                "display_group": ["construction"],
                                "visual_transform": {"translate": [0, 0, 0], "scale": 1},
                                "formation_roles": ["CONSTRUCT_AUXILIARY_GEOMETRY"],
                                "point": _exact_xyz_list(ln_val.point),
                                "direction": _exact_xyz_list(ln_val.direction),
                                "source": {"instruction": "construct_line", "inline_step_parent": primary_id},
                            }
                            mem[ln_id] = ln_val
                            by_id[ln_id] = ln_obj
                            newly_created_objs.append(ln_obj)
                    else:
                        ln_tok = _normalize_vi_math(clause.line_inputs[0])
                        ln_id = next((o["id"] for o in available_symbols.get(ln_tok, ()) if o.get("type") == "line3"), None)
                        if ln_id is None:
                            raise StepEditRefusal("MISSING_DEPENDENCY", "planner", f"Không tìm thấy đường thẳng '{clause.line_inputs[0]}'.")
                    foot_val = K.project_point_onto_line(mem[src_id], mem[ln_id])
                    img_sym = clause.output_symbol or "H"
                    _reuse_or_assign_point(
                        img_sym,
                        foot_val,
                        "construct_point.project_onto",
                        [src_id, ln_id],
                        f"Hình chiếu {_display_sym(img_sym)} của {src_id} lên đường thẳng",
                    )

                elif clause.op == "intersect_line_plane":
                    if len(clause.point_inputs) >= 2:
                        la = _find_pt(clause.point_inputs[0], "tìm giao điểm đường và mặt phẳng")
                        lb = _find_pt(clause.point_inputs[1], "tìm giao điểm đường và mặt phẳng")
                        ln_val = Line3.through(mem[la], mem[lb])
                        ln_id = next(
                            (o["id"] for o in all_objs if o.get("type") == "line3" and set(o.get("depends") or ()) == {la, lb} and o["id"] not in downstream_ids),
                            None,
                        )
                        if ln_id is None:
                            ln_id = _next_helper_id(f"line_{la}_{lb}")
                            ln_obj = {
                                "id": ln_id,
                                "type": "line3",
                                "label": f"{la}{lb}",
                                "notation": f"{la}{lb}",
                                "reference": f"{la}{lb}",
                                "role": "Đường thẳng",
                                "origin": "derived",
                                "producer": "construct_line",
                                "depends": [la, lb],
                                "render": "line",
                                "display_role": "visual_owner",
                                "display_group": ["construction"],
                                "visual_transform": {"translate": [0, 0, 0], "scale": 1},
                                "formation_roles": ["CONSTRUCT_AUXILIARY_GEOMETRY"],
                                "point": _exact_xyz_list(ln_val.point),
                                "direction": _exact_xyz_list(ln_val.direction),
                                "source": {"instruction": "construct_line", "inline_step_parent": primary_id},
                            }
                            mem[ln_id] = ln_val
                            by_id[ln_id] = ln_obj
                            newly_created_objs.append(ln_obj)
                    else:
                        ln_tok = _normalize_vi_math(clause.line_inputs[0])
                        ln_id = next((o["id"] for o in available_symbols.get(ln_tok, ()) if o.get("type") == "line3"), None)
                        if ln_id is None:
                            raise StepEditRefusal("MISSING_DEPENDENCY", "planner", f"Không tìm thấy đường thẳng '{clause.line_inputs[0]}'.")
                    pl_id = _resolve_plane_id(
                        clause.plane_inputs[0],
                        available_symbols,
                        local_objects_by_symbol,
                        by_id,
                        downstream_ids,
                        post_step_ids,
                        "tìm giao điểm đường và mặt phẳng",
                    )
                    pt_val = K.intersect_line_plane(mem[ln_id], mem[pl_id])
                    pt_sym = clause.output_symbol or "E"
                    _reuse_or_assign_point(
                        pt_sym,
                        pt_val,
                        "construct_point.intersect_line_plane",
                        [ln_id, pl_id],
                        f"Giao điểm {_display_sym(pt_sym)}",
                    )

                elif clause.op == "intersect_line_line":
                    pts_l = [_find_pt(p, "tìm giao điểm hai đường thẳng") for p in clause.point_inputs]
                    if len(pts_l) < 4:
                        raise StepEditRefusal("MISSING_DEPENDENCY", "planner", "Cần nêu đủ hai đường thẳng cắt nhau qua bốn đầu mút.")
                    la_val = Line3.through(mem[pts_l[0]], mem[pts_l[1]])
                    lb_val = Line3.through(mem[pts_l[2]], mem[pts_l[3]])
                    pt_val = K.intersect_line_line(la_val, lb_val)
                    la_id = _next_helper_id(f"line_{pts_l[0]}_{pts_l[1]}")
                    lb_id = _next_helper_id(f"line_{pts_l[2]}_{pts_l[3]}")
                    for lid, lv, p_pair in ((la_id, la_val, pts_l[:2]), (lb_id, lb_val, pts_l[2:4])):
                        lo = {
                            "id": lid,
                            "type": "line3",
                            "label": "".join(p_pair),
                            "notation": "".join(p_pair),
                            "reference": "".join(p_pair),
                            "role": "Đường thẳng",
                            "origin": "derived",
                            "producer": "construct_line",
                            "depends": list(p_pair),
                            "render": "line",
                            "display_role": "visual_owner",
                            "display_group": ["construction"],
                            "visual_transform": {"translate": [0, 0, 0], "scale": 1},
                            "formation_roles": ["CONSTRUCT_AUXILIARY_GEOMETRY"],
                            "point": _exact_xyz_list(lv.point),
                            "direction": _exact_xyz_list(lv.direction),
                            "source": {"instruction": "construct_line", "inline_step_parent": primary_id},
                        }
                        mem[lid] = lv
                        by_id[lid] = lo
                        newly_created_objs.append(lo)
                    pt_sym = clause.output_symbol or "O"
                    _reuse_or_assign_point(
                        pt_sym,
                        pt_val,
                        "construct_point.intersect_line_line",
                        [la_id, lb_id],
                        f"Giao điểm {_display_sym(pt_sym)}",
                    )

                elif clause.op == "construct_line":
                    if primary_obj.get("type") != "line3":
                        raise StepEditRefusal("STEP_TYPE_MISMATCH", "planner", "Bước đang sửa không phải bước dựng đường thẳng.")
                    if clause.params.get("mode") == "perpendicular_to_plane" and clause.plane_inputs:
                        pt_id = _find_pt(clause.point_inputs[0], "dựng đường thẳng vuông góc với mặt phẳng")
                        pl_id = _resolve_plane_id(
                            clause.plane_inputs[0],
                            available_symbols,
                            local_objects_by_symbol,
                            by_id,
                            downstream_ids,
                            post_step_ids,
                            "dựng đường thẳng vuông góc với mặt phẳng",
                        )
                        dir_v = _m.normal_vector(mem[pl_id].normal)
                        if dir_v.is_zero():
                            raise GeometryError("ZERO_VECTOR", "Vectơ pháp tuyến suy biến.")
                        ln_val = Line3(mem[pt_id], dir_v)
                        primary_obj.update({
                            "producer": "construct_line",
                            "depends": [pt_id, pl_id],
                            "point": _exact_xyz_list(ln_val.point),
                            "direction": _exact_xyz_list(ln_val.direction),
                        })
                    else:
                        pa_id = _find_pt(clause.point_inputs[0], "dựng đường thẳng")
                        pb_id = _find_pt(clause.point_inputs[1], "dựng đường thẳng")
                        ln_val = Line3.through(mem[pa_id], mem[pb_id])
                        primary_obj.update({
                            "producer": "construct_line",
                            "depends": [pa_id, pb_id],
                            "point": _exact_xyz_list(ln_val.point),
                            "direction": _exact_xyz_list(ln_val.direction),
                        })
                    mem[primary_id] = ln_val
                    updated_ids.append(primary_id)

                elif clause.op == "intersection_line":
                    if primary_obj.get("type") != "line3":
                        raise StepEditRefusal("STEP_TYPE_MISMATCH", "planner", "Bước đang sửa không phải bước dựng giao tuyến hai mặt phẳng.")
                    p1_id = _resolve_plane_id(clause.plane_inputs[0], available_symbols, local_objects_by_symbol, by_id, downstream_ids, post_step_ids, "dựng giao tuyến")
                    p2_id = _resolve_plane_id(clause.plane_inputs[1], available_symbols, local_objects_by_symbol, by_id, downstream_ids, post_step_ids, "dựng giao tuyến")
                    ln_val = K.intersect_plane_plane(mem[p1_id], mem[p2_id])
                    primary_obj.update({
                        "producer": "intersect_plane_plane",
                        "depends": [p1_id, p2_id],
                        "point": _exact_xyz_list(ln_val.point),
                        "direction": _exact_xyz_list(ln_val.direction),
                    })
                    mem[primary_id] = ln_val
                    updated_ids.append(primary_id)

                elif clause.op == "construct_segment":
                    if primary_obj.get("type") != "segment3":
                        raise StepEditRefusal("STEP_TYPE_MISMATCH", "planner", "Bước đang sửa không phải bước dựng đoạn thẳng.")
                    seg_pairs = clause.params.get("segments") or [list(clause.point_inputs)]
                    if len(seg_pairs) != len(resolved_target_ids):
                        raise StepEditRefusal("STEP_TYPE_MISMATCH", "planner", "Số đoạn thẳng sửa đổi không khớp với các đoạn của bước hiện tại.")
                    for tid, pair in zip(resolved_target_ids, seg_pairs):
                        pa_id = _find_pt(pair[0], "dựng đoạn thẳng")
                        pb_id = _find_pt(pair[1], "dựng đoạn thẳng")
                        sv = Segment3.between(mem[pa_id], mem[pb_id])
                        seg_o = by_id[tid]
                        seg_o.update({
                            "label": f"{pa_id}{pb_id}",
                            "notation": f"{pa_id}{pb_id}",
                            "reference": f"{pa_id}{pb_id}",
                            "depends": [pa_id, pb_id],
                            "endpoint_ids": [pa_id, pb_id],
                        })
                        mem[tid] = sv
                        _sync_scene_object_from_value(seg_o, sv, by_id)
                        updated_ids.append(tid)

                elif clause.op == "construct_section":
                    if primary_obj.get("type") != "section":
                        raise StepEditRefusal("STEP_TYPE_MISMATCH", "planner", "Bước đang sửa không phải bước dựng thiết diện.")
                    pl_id = _resolve_plane_id(clause.plane_inputs[0], available_symbols, local_objects_by_symbol, by_id, downstream_ids, post_step_ids, "dựng thiết diện")
                    sol_id = next((d for d in (primary_obj.get("depends") or ()) if by_id.get(d, {}).get("type") == "solid"), None)
                    if sol_id is None:
                        raise StepEditRefusal("MISSING_DEPENDENCY", "planner", "Không tìm thấy khối đa diện gốc cho thiết diện.")
                    sec_val = cross_section(mem[sol_id], mem[pl_id])
                    primary_obj["depends"] = [sol_id, pl_id]
                    mem[primary_id] = sec_val
                    _sync_scene_object_from_value(primary_obj, sec_val, by_id)
                    updated_ids.append(primary_id)

                elif clause.op in ("ball_center_rim", "circumscribed_sphere"):
                    if primary_obj.get("type") == "point3" and clause.op == "circumscribed_sphere":
                        sol = next((mem[o["id"]] for o in all_objs if o.get("type") == "solid" and isinstance(mem.get(o["id"]), Polyhedron)), None)
                        sol_id = next((o["id"] for o in all_objs if o.get("type") == "solid" and isinstance(mem.get(o["id"]), Polyhedron)), None)
                        if sol is None or sol_id is None:
                            raise StepEditRefusal("MISSING_DEPENDENCY", "kernel", "Không tìm thấy khối đa diện để xác định tâm mặt cầu ngoại tiếp.")
                        center_ex, _ = circumscribed_sphere(sol.vertices)
                        pt_sym = clause.output_symbol or primary_obj.get("notation") or "I"
                        _reuse_or_assign_point(
                            pt_sym,
                            center_ex,
                            "circumscribed_sphere.center",
                            [sol_id],
                            f"Tâm mặt cầu ngoại tiếp {_display_sym(pt_sym)}",
                        )
                    else:
                        if primary_obj.get("type") != "curved_solid":
                            raise StepEditRefusal("STEP_TYPE_MISMATCH", "planner", "Bước đang sửa không phải bước dựng mặt cầu.")
                        c_id = _find_pt(clause.point_inputs[0], "dựng mặt cầu")
                        r_id = _find_pt(clause.point_inputs[1], "dựng mặt cầu") if len(clause.point_inputs) >= 2 else None
                        if clause.op == "circumscribed_sphere":
                            sol = next((mem[o["id"]] for o in all_objs if o.get("type") == "solid" and isinstance(mem.get(o["id"]), Polyhedron)), None)
                            if sol is not None:
                                center_ex, _ = circumscribed_sphere(sol.vertices)
                                if not P.same_point(mem[c_id], center_ex):
                                    raise StepEditRefusal(
                                        "NO_CIRCUMSCRIBED_SPHERE",
                                        "kernel",
                                        f"Điểm {_display_sym(c_id)} không phải tâm mặt cầu ngoại tiếp của khối đa diện.",
                                    )
                        if r_id is None:
                            rsq = Fraction(primary_obj["radius_sq"])
                            cs_val = CurvedSolid("ball", anchor=mem[c_id], apex_or_top=None, rim_point=None, radius_sq_khai=rsq)
                            primary_obj["depends"] = [c_id]
                        else:
                            cs_val = CurvedSolid("ball", anchor=mem[c_id], apex_or_top=None, rim_point=mem[r_id])
                            primary_obj["depends"] = [c_id, r_id]
                        mem[primary_id] = cs_val
                        _sync_scene_object_from_value(primary_obj, cs_val, by_id)
                        updated_ids.append(primary_id)

                elif clause.op == "construct_polygon":
                    if primary_obj.get("type") != "polygon3":
                        raise StepEditRefusal("STEP_TYPE_MISMATCH", "planner", "Bước đang sửa không phải bước dựng đa giác.")
                    pt_ids = [_find_pt(s, "dựng đa giác") for s in clause.point_inputs]
                    if len(pt_ids) < 3:
                        raise StepEditRefusal("INSUFFICIENT_POINTS", "planner", "Đa giác cần ít nhất 3 đỉnh.")
                    pts_vals = tuple(mem[pid] for pid in pt_ids)
                    for idx_k in range(3, len(pts_vals)):
                        if not P.coplanar(pts_vals[0], pts_vals[1], pts_vals[2], pts_vals[idx_k]):
                            raise GeometryError("NON_COPLANAR_POINTS", f"Đỉnh '{pt_ids[idx_k]}' không đồng phẳng.")
                    poly_label = clause.output_symbol or f"Đáy {''.join(pt_ids)}"
                    primary_obj.update({
                        "label": poly_label,
                        "notation": "".join(pt_ids),
                        "depends": list(pt_ids),
                        "vertex_ids": list(pt_ids),
                        "vertices": [_exact_xyz_list(v) for v in pts_vals],
                    })
                    mem[primary_id] = pts_vals
                    updated_ids.append(primary_id)

                elif clause.op == "construct_solid":
                    if primary_obj.get("type") != "solid":
                        raise StepEditRefusal("STEP_TYPE_MISMATCH", "planner", "Bước đang sửa không phải bước dựng khối đa diện.")
                    pt_ids = [_find_pt(s, "dựng khối đa diện") for s in clause.point_inputs]
                    existing_vids = list(primary_obj.get("vertex_ids") or primary_obj.get("depends") or ())
                    if set(pt_ids) != set(existing_vids):
                        raise StepEditRefusal("STEP_TYPE_MISMATCH", "planner", "Danh sách đỉnh khối đa diện không khớp với cấu trúc mặt của khối.")
                    sol_val = _hydrate_object_value(primary_obj, mem)
                    if sol_val is not None:
                        mem[primary_id] = sol_val
                    updated_ids.append(primary_id)

                else:
                    raise StepEditRefusal(
                        "STEP_TYPE_MISMATCH",
                        "planner",
                        f"Phép dựng '{clause.op}' chưa tương thích để thay thế trực tiếp bước hiện tại.",
                    )

            # Recompute ONLY transitive downstream closure in topological order!
            t_dep = time.perf_counter()
            recomputed_ids: list[str] = []
            # Ensure local `depends` updated cleanly; filter objects to rebuild
            retired_set = set(retired_helper_ids)
            if primary_obj["id"] not in (updated_ids or []):
                updated_ids.append(primary_obj["id"])
            for oid in updated_ids:
                _sync_scene_object_from_value(by_id[oid], mem[oid], by_id)

            topo_downstream = [oid for oid in graph["topo_order"] if oid in downstream_ids and oid not in retired_set]
            for did in topo_downstream:
                d_obj = by_id[did]
                # Ensure all depends still exist and aren't retired
                for ddep in d_obj.get("depends") or ():
                    if ddep in retired_set or ddep not in mem:
                        raise StepEditRefusal(
                            "DANGLING_REFERENCE",
                            "dependency_rebuild",
                            f"Phép dựng phía sau '{d_obj.get('label') or did}' tham chiếu đối tượng '{ddep}' đã bị loại bỏ.",
                        )
                new_val = _reevaluate_object(d_obj, mem, by_id)
                mem[did] = new_val
                _sync_scene_object_from_value(d_obj, new_val, by_id)
                recomputed_ids.append(did)
            timings["dependency_rebuild_ms"] = round((time.perf_counter() - t_dep) * 1000.0, 3)

        except StepEditRefusal:
            raise
        except GeometryError as ge:
            raise StepEditRefusal(ge.code, "kernel", str(ge).split(": ", 1)[-1]) from ge
        except RadicalDomainError as rde:
            raise StepEditRefusal("EXACT_DOMAIN_EXCEEDED", "kernel", f"Giá trị căn thức vượt miền chính xác: {rde}") from rde

    timings["kernel_ms"] = round((time.perf_counter() - t_kernel) * 1000.0, 3)

    # ── Stage 4: Sync Scene3D (events, topology, formulas, formation, continuity) ──
    t_scene = time.perf_counter()
    # Build ordered object list: keep existing unaffected/recomputed ordering, retire exclusive helpers, splice new inline objs
    surviving_objs = [by_id[o["id"]] for o in all_objs if o["id"] not in set(retired_helper_ids)]
    # Insert newly created inline objects immediately before `primary_id`
    insert_pos = next((idx_o for idx_o, o in enumerate(surviving_objs) if o["id"] == primary_id), len(surviving_objs))
    for offset, new_o in enumerate(newly_created_objs):
        if not any(x["id"] == new_o["id"] for x in surviving_objs):
            surviving_objs.insert(insert_pos + offset, new_o)

    before_objs_map = {o["id"]: o for o in (before_snapshot.get("objects") or ())}
    notation_renames: dict[str, str] = {}
    for oid in updated_ids:
        b_obj = before_objs_map.get(oid)
        a_obj = by_id.get(oid)
        if not b_obj or not a_obj:
            continue
        old_not = b_obj.get("notation")
        new_not = a_obj.get("notation")
        if isinstance(old_not, str) and isinstance(new_not, str) and old_not.strip() and new_not.strip() and old_not != new_not:
            notation_renames[old_not] = new_not
    if notation_renames:
        for did in recomputed_ids:
            d_obj = by_id.get(did)
            if not d_obj:
                continue
            for field_name in ("label", "display_label", "reference"):
                val_str = d_obj.get(field_name)
                if isinstance(val_str, str):
                    d_obj[field_name] = _apply_notation_renames(val_str, notation_renames)

    rebuilt_scene = copy.deepcopy(before_snapshot)
    rebuilt_scene["objects"] = surviving_objs
    _attach_topology(rebuilt_scene["objects"])
    _attach_formulas(rebuilt_scene["objects"])

    # Rebuild timeline events preserving step order while splicing new inline events,
    # hoisting any existing dependencies needed earlier at `primary_id`, & updating sections.
    orig_events = copy.deepcopy(before_snapshot.get("events") or [])
    new_events: list[dict[str, Any]] = []
    retired_set = set(retired_helper_ids)
    # Remove old EXTEND/STEP events for rebuilt sections if we are regenerating them
    rebuilt_sections = {oid for oid in [*updated_ids, *recomputed_ids] if by_id.get(oid, {}).get("type") == "section"}
    inserted_inline = False
    emitted_section_events: set[str] = set()
    emitted_obj_events: set[str] = set()
    primary_deps_closure: set[str] = set()
    stack_pd = list(primary_obj.get("depends") or ())
    while stack_pd:
        d_cur = stack_pd.pop()
        if d_cur in primary_deps_closure or d_cur in retired_set:
            continue
        primary_deps_closure.add(d_cur)
        if d_cur in by_id:
            stack_pd.extend(by_id[d_cur].get("depends") or ())
    hoist_ev_by_obj = {
        str(ev.get("object")): copy.deepcopy(ev)
        for ev in orig_events
        if ev.get("action") == "CREATE" and ev.get("object") in primary_deps_closure
    }

    for ev in orig_events:
        ev_obj_id = ev.get("object")
        if ev_obj_id in retired_set:
            continue
        if ev.get("action") == "CREATE" and ev_obj_id in emitted_obj_events:
            continue
        if ev_obj_id in rebuilt_sections:
            if ev_obj_id not in emitted_section_events:
                emitted_section_events.add(ev_obj_id)
                sec_o = next(o for o in surviving_objs if o["id"] == ev_obj_id)
                for edge_idx, _st in enumerate(sec_o.get("steps") or ()):
                    new_events.append({
                        "step_index": len(new_events),
                        "action": "EXTEND",
                        "object": ev_obj_id,
                        "depends": list(sec_o.get("depends") or ()),
                        "explanation": f"Nối cạnh thiết diện thứ {edge_idx + 1}.",
                        "display_label": f"Cạnh thiết diện {edge_idx + 1}",
                        "semantic_kind": "GEOMETRY_CONSTRUCTION",
                        "details": {"canh": edge_idx},
                        "learner_text": f"Nối cạnh thiết diện thứ {edge_idx + 1}.",
                    })
                new_events.append({
                    "step_index": len(new_events),
                    "action": "STEP",
                    "object": ev_obj_id,
                    "depends": list(sec_o.get("depends") or ()),
                    "explanation": sec_o.get("label") or "Thiết diện khép kín.",
                    "display_label": sec_o.get("label") or "Thiết diện",
                    "semantic_kind": "GEOMETRY_CONSTRUCTION",
                    "details": {},
                    "learner_text": f"Thiết diện khép lại thành đa giác {len(sec_o.get('polygon') or ())} đỉnh.",
                })
            continue

        if ev_obj_id == primary_id and not inserted_inline:
            inserted_inline = True
            for dep_oid in graph["topo_order"]:
                if dep_oid in primary_deps_closure and dep_oid not in emitted_obj_events and dep_oid in hoist_ev_by_obj:
                    h_ev = hoist_ev_by_obj[dep_oid]
                    new_events.append(h_ev)
                    emitted_obj_events.add(dep_oid)
            for new_o in newly_created_objs:
                new_events.append({
                    "step_index": len(new_events),
                    "action": "CREATE",
                    "object": new_o["id"],
                    "depends": list(new_o.get("depends") or ()),
                    "explanation": new_o.get("label") or f"Dựng {new_o.get('notation') or new_o['id']}.",
                    "display_label": new_o.get("label") or new_o["id"],
                    "semantic_kind": "GEOMETRY_CONSTRUCTION",
                    "details": {},
                    "learner_text": new_o.get("label") or f"Dựng {new_o.get('notation') or new_o['id']}.",
                })
                emitted_obj_events.add(new_o["id"])
        ev_copy = copy.deepcopy(ev)
        if ev.get("action") == "CREATE" and ev_obj_id:
            emitted_obj_events.add(str(ev_obj_id))
        if ev_obj_id in updated_ids or ev_obj_id in recomputed_ids:
            cur_o = next((o for o in surviving_objs if o["id"] == ev_obj_id), None)
            if cur_o is not None:
                ev_copy["depends"] = list(cur_o.get("depends") or ())
                if notation_renames and ev_obj_id in recomputed_ids:
                    for ev_field in ("learner_text", "display_label", "explanation", "title"):
                        if isinstance(ev_copy.get(ev_field), str):
                            ev_copy[ev_field] = _apply_notation_renames(ev_copy[ev_field], notation_renames)
                if cur_o.get("type") == "quantity" and cur_o.get("value") is not None:
                    ev_copy["learner_text"] = f"{cur_o.get('label') or cur_o['id']} bằng {cur_o['value']}."
                elif ev_obj_id == primary_id and parsed_new.normalized_text:
                    ev_copy["learner_text"] = parsed_new.normalized_text
                elif not ev_copy.get("learner_text"):
                    ev_copy["learner_text"] = cur_o.get("label") or ""
        new_events.append(ev_copy)

    for idx_e, ev in enumerate(new_events):
        ev["step_index"] = idx_e
    rebuilt_scene["events"] = new_events
    rebuilt_scene["formation"] = _build_formation(
        surviving_objs,
        new_events,
        rebuilt_scene.get("free_objects") or [],
    )
    enrich_construction_continuity(rebuilt_scene)
    timings["scene3d_build_ms"] = round((time.perf_counter() - t_scene) * 1000.0, 3)

    # ── Stage 5: Exact Geometry Verification (§8) ─────────────────────────────
    t_val = time.perf_counter()
    bisector_arg = None
    if "expected_bisector" in locals() and expected_bisector is not None:
        bisector_arg = expected_bisector
    elif any(c.op == "perpendicular_bisector_plane" for c in parsed_new.clauses):
        pl_deps = primary_obj.get("depends") or ()
        mid_cand = next((d for d in pl_deps if by_id.get(d, {}).get("type") == "point3"), None)
        ln_cand = next((d for d in pl_deps if by_id.get(d, {}).get("type") == "line3"), None)
        if mid_cand and ln_cand and len(by_id[ln_cand].get("depends") or ()) == 2:
            a0, b0 = by_id[ln_cand]["depends"]
            bisector_arg = (mid_cand, a0, b0, primary_id)

    all_changed = [*[o["id"] for o in newly_created_objs], *updated_ids, *recomputed_ids]
    val_res = verify_rebuilt_geometry(
        rebuilt_scene,
        before_scene=before_snapshot,
        edited_intent=parsed_new,
        created_or_updated_ids=all_changed,
        expected_perpendicular_bisector_for=bisector_arg,
    )
    timings["validation_ms"] = round((time.perf_counter() - t_val) * 1000.0, 3)
    timings["total_ms"] = round((time.perf_counter() - t_start) * 1000.0, 3)

    after_digest = _scene_digest(rebuilt_scene)
    changed_objects: dict[str, dict[str, Any]] = {}
    for oid in all_changed:
        after_o = next((o for o in surviving_objs if o["id"] == oid), None)
        before_o = before_objs_map.get(oid)
        if after_o is None:
            continue
        changed_objects[oid] = {
            "before": {
                k: before_o.get(k)
                for k in ("xyz", "point", "normal", "direction", "polygon", "anchor", "radius_sq", "value", "depends")
                if before_o and k in before_o
            } if before_o else None,
            "after": {
                k: after_o.get(k)
                for k in ("xyz", "point", "normal", "direction", "polygon", "anchor", "radius_sq", "value", "depends")
                if k in after_o
            },
        }

    next_overrides = dict(existing_overrides)
    if notation_renames:
        for did in recomputed_ids:
            if did in next_overrides and isinstance(next_overrides[did], str):
                next_overrides[did] = _apply_notation_renames(next_overrides[did], notation_renames)
    next_overrides[primary_id] = parsed_new.normalized_text

    return {
        "status": "committed",
        "mode": "PARTIAL_TOPOLOGICAL_REBUILD",
        "scene3d": rebuilt_scene,
        "step_overrides": next_overrides,
        "normalized_intent": parsed_new.to_dict(),
        "registry_operations": list(parsed_new.registry_operations),
        "dependency_summary": {
            "edited_target_ids": resolved_target_ids,
            "created_ids": [o["id"] for o in newly_created_objs],
            "reused_ids": list(dict.fromkeys(reused_ids)),
            "retired_ids": retired_helper_ids,
            "recomputed_ids": recomputed_ids,
            "skipped_unaffected_ids": unaffected_ids,
            "cycle_detected": False,
        },
        "validation_result": val_res,
        "before_after_diff": {
            "changed": True,
            "changed_objects": changed_objects,
        },
        "before_scene_digest": before_digest,
        "after_scene_digest": after_digest,
        "stage_timings_ms": timings,
        "primary_target_id": primary_id,
    }
