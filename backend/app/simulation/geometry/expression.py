# -*- coding: utf-8 -*-
"""Dimension-aware exact mathematical expression model over Kernel `Fraction` and `Radical`.

Reuses `fractions.Fraction` and `app.simulation.geometry.radical` as the sole numeric
substrate (zero float evaluation, zero external/second CAS). Enforces:
1. Algebraic `Dimension` lattice (`SCALAR` L^0, `LENGTH` L^1, `AREA` L^2, `VOLUME` L^3, `ANGLE`)
   separated cleanly from display/measurement units (`cm`, `cm²`, `m³`, `°`, `rad`) with zero
   speculative unit conversion.
2. Context-driven `SymbolEnvironment`: symbol names (`a`, `x`, `S`, `V`, `h`, `R`) never
   dictate dimension; geometric slots constrain symbol dimensions and fail closed on conflicting
   dimensions, inhomogeneous sums (`L + L^2`), fractional dimensions (`√(3a)`), ungrounded
   symbols, or non-length single-symbol coercion (`S : L^2` / `V : L^3` without an `L^1` unit).
3. Exact provenance (`original_expr`, `normalized_expr`, `source_span`, `operand_spans`) and
   fact roles (`SOURCE_QUANTITY`, `VERIFIED_DERIVED_QUANTITY`,
   `ILLUSTRATIVE_CONSTRUCTION_QUANTITY`, `UNVERIFIED_CANDIDATE`).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
import re
from typing import AbstractSet, Any, Literal, Mapping, Sequence

from app.simulation.geometry.radical import (
    ExactNumber,
    PI_EXPONENT_DOMAIN,
    Radical,
    RadicalDomainError,
    add as radical_add,
    display as radical_display,
    multiply as radical_multiply,
    negate as radical_negate,
    radical,
    sign as radical_sign,
    sqrt_rational,
    square as radical_square,
    times_rational,
)

EXPRESSION_MODEL_VERSION = "dimension-expression/1"
MAX_EXPONENT = 6


class ExpressionError(ValueError):
    """Base fail-closed error for parsing, dimensional typing, and algebraic domain checks."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.message = detail


class ExprParseError(ExpressionError):
    """Syntactic/lexical rejection (never guesses or truncates malformed expressions)."""


class ExprDimensionError(ExpressionError):
    """Dimensional-homogeneity or unit-consistency rejection."""


class ExprDomainError(ExpressionError):
    """Algebraic/positivity/divisor/radical-domain rejection."""


class FactRole(str, Enum):
    """Epistemic role of a quantity in the Hybrid /4 verification pipeline."""

    SOURCE_QUANTITY = "SOURCE_QUANTITY"
    VERIFIED_DERIVED_QUANTITY = "VERIFIED_DERIVED_QUANTITY"
    ILLUSTRATIVE_CONSTRUCTION_QUANTITY = "ILLUSTRATIVE_CONSTRUCTION_QUANTITY"
    UNVERIFIED_CANDIDATE = "UNVERIFIED_CANDIDATE"


@dataclass(frozen=True)
class Dimension:
    """Exact geometric dimension `L^length_exp` or `ANGLE`."""

    length_exp: int = 0
    is_angle: bool = False

    def __post_init__(self) -> None:
        if self.is_angle and self.length_exp != 0:
            raise ExprDimensionError("DIMENSION_MISMATCH", "góc không mang số mũ độ dài khác 0")

    @property
    def name(self) -> str:
        if self.is_angle:
            return "ANGLE"
        names = {0: "SCALAR", 1: "LENGTH", 2: "AREA", 3: "VOLUME"}
        return names.get(self.length_exp, f"L^{self.length_exp}")

    def __str__(self) -> str:
        return self.name


SCALAR = Dimension(0, False)
LENGTH = Dimension(1, False)
AREA = Dimension(2, False)
VOLUME = Dimension(3, False)
ANGLE = Dimension(0, True)


def dim_add(d1: Dimension, d2: Dimension) -> Dimension:
    if d1 != d2:
        raise ExprDimensionError(
            "DIMENSION_MISMATCH",
            f"không thể cộng/trừ hai đại lượng khác thứ nguyên ({d1.name} và {d2.name})",
        )
    return d1


def dim_mul(d1: Dimension, d2: Dimension) -> Dimension:
    if not d1.is_angle and not d2.is_angle:
        return Dimension(d1.length_exp + d2.length_exp, False)
    if d1 == SCALAR and d2.is_angle:
        return ANGLE
    if d2 == SCALAR and d1.is_angle:
        return ANGLE
    raise ExprDimensionError(
        "DIMENSION_MISMATCH",
        f"nhân thứ nguyên không hợp lệ ({d1.name} · {d2.name})",
    )


def dim_div(d1: Dimension, d2: Dimension) -> Dimension:
    if not d1.is_angle and not d2.is_angle:
        return Dimension(d1.length_exp - d2.length_exp, False)
    if d1.is_angle and d2 == SCALAR:
        return ANGLE
    if d1.is_angle and d2.is_angle:
        return SCALAR
    raise ExprDimensionError(
        "DIMENSION_MISMATCH",
        f"chia thứ nguyên không hợp lệ ({d1.name} / {d2.name})",
    )


def dim_pow(d: Dimension, exp: int) -> Dimension:
    if d.is_angle and exp != 1:
        raise ExprDimensionError("DIMENSION_MISMATCH", f"không nâng góc lên luỹ thừa {exp}")
    return Dimension(d.length_exp * exp, False)


def dim_sqrt(d: Dimension) -> Dimension:
    if d.is_angle or d.length_exp % 2 != 0:
        raise ExprDimensionError(
            "FRACTIONAL_DIMENSION",
            f"căn bậc hai của {d.name} sinh thứ nguyên phân số không hợp lệ",
        )
    return Dimension(d.length_exp // 2, False)


SLOT_DIMENSIONS: dict[str, Dimension] = {
    "segment_length": LENGTH,
    "regular_polygon": LENGTH,
    "rhombus": LENGTH,
    "height": LENGTH,
    "curved_radius": LENGTH,
    "curved_height": LENGTH,
    "polygon_area": AREA,
    "face_area": AREA,
    "solid_volume": VOLUME,
    "segment_ratio": SCALAR,
    "divide_segment": SCALAR,
    "trig_ratio": SCALAR,
    "line_plane_angle": ANGLE,
    "plane_plane_angle": ANGLE,
    "dihedral_angle": ANGLE,
    "line_line_angle": ANGLE,
    "vertex_angle": ANGLE,
}

GOAL_DEGREES: dict[str, int] = {
    "ask_volume": 3,
    "ask_residual_volume": 3,
    "ask_curved_volume": 3,
    "ask_curved_residual_volume": 3,
    "ask_area": 2,
    "ask_section_area": 2,
    "ask_lateral_area": 2,
    "ask_surface_area": 2,
    "ask_curved_section_area": 2,
    "ask_length": 1,
    "ask_radius": 1,
    "ask_curved_section_radius": 1,
    "ask_distance_point_plane": 1,
    "ask_distance_lines": 1,
    "ask_distance_line_plane": 1,
    "ask_distance_planes": 1,
    "ask_volume_ratio": 0,
    "ask_curved_volume_ratio": 0,
    "ask_length_ratio": 0,
    "ask_area_ratio": 0,
    "ask_angle_line_plane": 0,
    "ask_angle_plane_plane": 0,
    "ask_angle_lines": 0,
}


def goal_dimension(ask_fn: str) -> Dimension:
    if ask_fn.startswith("ask_angle"):
        return ANGLE
    deg = GOAL_DEGREES.get(ask_fn)
    if deg is None:
        raise ExprDimensionError("DIMENSION_MISMATCH", f"hàm mục tiêu chưa khai báo thứ nguyên: {ask_fn!r}")
    return Dimension(deg, False)


@dataclass(frozen=True)
class MeasurementUnit:
    """Display/measurement unit metadata, kept orthogonal to algebraic `Dimension`."""

    raw_unit: str
    canonical_unit: str
    base_metric_unit: str | None
    dimension: Dimension


_METRIC_UNIT_RE = re.compile(r"^(mm|cm|dm|km|m)\s*(?:(²|\^2|2)|(³|\^3|3))?$", re.IGNORECASE)


def parse_measurement_unit(raw: str) -> MeasurementUnit | None:
    s = (raw or "").strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1].strip()
    s = re.sub(r"^đơn\s+vị(?:\s+(?:độ\s+dài|diện\s+tích|thể\s+tích|góc))?\s*:?\s*", "", s, flags=re.IGNORECASE).strip()
    if not s:
        return None
    if s == "°" or s.lower() == "độ":
        return MeasurementUnit(raw, "°" if s == "°" else "độ", None, ANGLE)
    if s.lower() in ("rad", "radian"):
        return MeasurementUnit(raw, "rad", None, ANGLE)
    low = s.lower()
    if low == "đvđd":
        return MeasurementUnit(raw, "đvđd", None, LENGTH)
    if low == "đvdt":
        return MeasurementUnit(raw, "đvdt", None, AREA)
    if low == "đvtt":
        return MeasurementUnit(raw, "đvtt", None, VOLUME)
    m = _METRIC_UNIT_RE.fullmatch(s)
    if not m:
        return None
    base = m.group(1).lower()
    if m.group(2):
        return MeasurementUnit(raw, f"{base}²", base, AREA)
    if m.group(3):
        return MeasurementUnit(raw, f"{base}³", base, VOLUME)
    return MeasurementUnit(raw, base, base, LENGTH)


def validate_unit_consistency(
    units: Sequence[MeasurementUnit],
    *,
    expected_dim: Dimension | None = None,
) -> str | None:
    """Validate unit-vs-slot dimension and single metric base scale (zero unit conversion)."""
    bases: set[str] = set()
    for u in units:
        if expected_dim is not None and u.dimension != expected_dim:
            raise ExprDimensionError(
                "UNIT_DIMENSION_MISMATCH",
                f"đơn vị {u.raw_unit!r} ({u.dimension.name}) không khớp thứ nguyên {expected_dim.name}",
            )
        if u.base_metric_unit is not None:
            bases.add(u.base_metric_unit)
    if len(bases) > 1:
        raise ExprDimensionError(
            "UNIT_SYSTEM_MISMATCH",
            f"không tự quy đổi giữa các hệ đơn vị khác nhau: {sorted(bases)}",
        )
    return next(iter(bases), None)


@dataclass(frozen=True)
class DerivedQuantityRecord:
    """Machine-verifiable provenance record for a certified derived quantity."""

    rule_id: str
    target_entity: str
    target_dimension: Dimension
    premise_call_ids: tuple[str, ...]
    value_sq_unit: Fraction
    symbolic_unit: str | None = None
    positivity_certified: bool = True
    role: FactRole = FactRole.VERIFIED_DERIVED_QUANTITY

    def to_dict(self) -> dict[str, Any]:
        q = Fraction(self.value_sq_unit)
        return {
            "role": self.role.value,
            "rule_id": self.rule_id,
            "target_entity": self.target_entity,
            "target_dimension": self.target_dimension.name,
            "premise_call_ids": list(self.premise_call_ids),
            "value_sq_unit": f"{q.numerator}/{q.denominator}" if q.denominator != 1 else str(q.numerator),
            "symbolic_unit": self.symbolic_unit,
            "positivity_certified": self.positivity_certified,
        }


# ── AST & PROVENANCE ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RationalLit:
    value: Fraction
    raw: str
    span: tuple[int, int]


@dataclass(frozen=True)
class PiLit:
    raw: str
    span: tuple[int, int]


@dataclass(frozen=True)
class SymbolRef:
    name: str
    span: tuple[int, int]


@dataclass(frozen=True)
class UnaryOp:
    op: Literal["+", "-"]
    operand: "ExprNode"
    span: tuple[int, int]


@dataclass(frozen=True)
class BinOp:
    op: Literal["+", "-", "*", "/"]
    left: "ExprNode"
    right: "ExprNode"
    implicit: bool
    span: tuple[int, int]


@dataclass(frozen=True)
class PowOp:
    base: "ExprNode"
    exp: int
    raw_exp: str
    span: tuple[int, int]


@dataclass(frozen=True)
class SqrtOp:
    radicand: "ExprNode"
    span: tuple[int, int]


@dataclass(frozen=True)
class AnnotatedQuantity:
    expr: "ExprNode"
    unit: MeasurementUnit
    span: tuple[int, int]


ExprNode = (
    RationalLit | PiLit | SymbolRef | UnaryOp | BinOp | PowOp | SqrtOp | AnnotatedQuantity
)


@dataclass(frozen=True)
class ExprProvenance:
    original_expr: str
    normalized_expr: str
    source_span: tuple[int, int]
    operand_spans: tuple[tuple[str, int, int], ...]
    unit: MeasurementUnit | None = None
    role: FactRole = FactRole.SOURCE_QUANTITY


@dataclass(frozen=True)
class QuantityExpr:
    ast: ExprNode
    provenance: ExprProvenance

    @property
    def referenced_symbols(self) -> frozenset[str]:
        return _collect_symbols(self.ast)


def _collect_symbols(node: ExprNode) -> frozenset[str]:
    if isinstance(node, SymbolRef):
        return frozenset((node.name,))
    if isinstance(node, (RationalLit, PiLit)):
        return frozenset()
    if isinstance(node, UnaryOp):
        return _collect_symbols(node.operand)
    if isinstance(node, BinOp):
        return _collect_symbols(node.left) | _collect_symbols(node.right)
    if isinstance(node, PowOp):
        return _collect_symbols(node.base)
    if isinstance(node, SqrtOp):
        return _collect_symbols(node.radicand)
    if isinstance(node, AnnotatedQuantity):
        return _collect_symbols(node.expr)
    return frozenset()


def _collect_operand_spans(node: ExprNode, out: list[tuple[str, int, int]]) -> None:
    if isinstance(node, RationalLit):
        out.append((f"num:{node.raw}", node.span[0], node.span[1]))
    elif isinstance(node, PiLit):
        out.append((f"pi:{node.raw}", node.span[0], node.span[1]))
    elif isinstance(node, SymbolRef):
        out.append((f"sym:{node.name}", node.span[0], node.span[1]))
    elif isinstance(node, UnaryOp):
        _collect_operand_spans(node.operand, out)
    elif isinstance(node, BinOp):
        _collect_operand_spans(node.left, out)
        _collect_operand_spans(node.right, out)
    elif isinstance(node, PowOp):
        _collect_operand_spans(node.base, out)
    elif isinstance(node, SqrtOp):
        _collect_operand_spans(node.radicand, out)
    elif isinstance(node, AnnotatedQuantity):
        _collect_operand_spans(node.expr, out)


def _format_ast_normalized(node: ExprNode) -> str:
    if isinstance(node, RationalLit):
        f = node.value
        return str(f.numerator) if f.denominator == 1 else f"({f.numerator}/{f.denominator})"
    if isinstance(node, PiLit):
        return "π"
    if isinstance(node, SymbolRef):
        return node.name
    if isinstance(node, UnaryOp):
        inner = _format_ast_normalized(node.operand)
        return f"-{inner}" if node.op == "-" else inner
    if isinstance(node, PowOp):
        b = _format_ast_normalized(node.base)
        if isinstance(node.base, (BinOp, UnaryOp, PowOp)) or (
            isinstance(node.base, RationalLit) and node.base.value.denominator != 1
        ):
            b = f"({b})"
        sup = {2: "²", 3: "³"}.get(node.exp, f"^{node.exp}")
        return f"{b}{sup}"
    if isinstance(node, SqrtOp):
        if isinstance(node.radicand, RationalLit) and node.radicand.value.denominator == 1 and node.radicand.value >= 0:
            return f"√{node.radicand.value.numerator}"
        return f"√({_format_ast_normalized(node.radicand)})"
    if isinstance(node, BinOp):
        left = _format_ast_normalized(node.left)
        right = _format_ast_normalized(node.right)
        if node.op in ("+", "-"):
            return f"({left}{node.op}{right})"
        if node.op == "*":
            if isinstance(node.left, BinOp) and node.left.op in ("+", "-"):
                left = f"({left})"
            if isinstance(node.right, BinOp) and node.right.op in ("+", "-", "/"):
                right = f"({right})"
            if node.implicit and not (left[-1:].isdigit() and right[:1].isdigit()):
                return f"{left}{right}"
            return f"{left}*{right}"
        if node.op == "/":
            if isinstance(node.left, BinOp) and node.left.op in ("+", "-"):
                left = f"({left})"
            if isinstance(node.right, (BinOp, UnaryOp)):
                right = f"({right})"
            return f"{left}/{right}"
    if isinstance(node, AnnotatedQuantity):
        return f"{_format_ast_normalized(node.expr)} {node.unit.canonical_unit}"
    return ""


# ── LEXER & RECURSIVE-DESCENT PARSER ──────────────────────────────────────────


@dataclass(frozen=True)
class _Tok:
    kind: str  # NUM | SYM | PI | SQRT | SUP | OP | LPAREN | RPAREN
    text: str
    start: int
    end: int


_TRAILING_UNIT_RE = re.compile(
    r"""(?x)
    (?:
        \(\s*(?P<uparen>(?:mm|cm|dm|m|km)(?:²|\^2|2|³|\^3|3)?|đvđd|đvdt|đvtt|độ|radian|rad|°)\s*\)
        |
        (?P<udeg>°)
        |
        (?<=\s)(?P<uword>(?:mm|cm|dm|m|km)(?:²|\^2|2|³|\^3|3)?|đvđd|đvdt|đvtt|độ|radian|rad)
        |
        (?<![A-Za-zÀ-ỹ])(?P<umult>(?:mm|cm|dm|km)(?:²|\^2|2|³|\^3|3)?|m(?:²|\^2|2|³|\^3|3)|đvđd|đvdt|đvtt|radian|rad)
    )\s*$
    """,
    re.IGNORECASE,
)

_SUP_MAP = {"²": 2, "³": 3}


def _is_ascii_digit(ch: str) -> bool:
    return "0" <= ch <= "9"


def _tokenize(src: str, base_offset: int) -> list[_Tok]:
    toks: list[_Tok] = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch.isspace():
            i += 1
            continue
        pos = base_offset + i
        if _is_ascii_digit(ch):
            j = i
            while j < n and _is_ascii_digit(src[j]):
                j += 1
            if j < n and src[j] in (",", "."):
                sep = src[j]
                if j + 1 < n and _is_ascii_digit(src[j + 1]):
                    k = j + 1
                    while k < n and _is_ascii_digit(src[k]):
                        k += 1
                    if k < n and src[k] in (",", ".") and k + 1 < n and _is_ascii_digit(src[k + 1]):
                        raise ExprParseError(
                            "INVALID_DECIMAL_LIST",
                            f"chuỗi nhiều dấu phân cách {src[i:k + 2]!r} không phải một số thập phân",
                        )
                    j = k
                else:
                    raise ExprParseError("SYNTAX_ERROR", f"dấu {sep!r} treo sau chữ số tại vị trí {pos}")
            toks.append(_Tok("NUM", src[i:j], pos, base_offset + j))
            i = j
            continue
        if ch == "√":
            toks.append(_Tok("SQRT", ch, pos, pos + 1))
            i += 1
            continue
        if ch == "π":
            toks.append(_Tok("PI", ch, pos, pos + 1))
            i += 1
            continue
        if ch in _SUP_MAP:
            if i + 1 < n and src[i + 1] in _SUP_MAP:
                raise ExprParseError("AMBIGUOUS_EXPONENT", f"số mũ chồng mơ hồ {src[i:i + 2]!r}")
            toks.append(_Tok("SUP", ch, pos, pos + 1))
            i += 1
            continue
        if ch == "(":
            toks.append(_Tok("LPAREN", ch, pos, pos + 1))
            i += 1
            continue
        if ch == ")":
            toks.append(_Tok("RPAREN", ch, pos, pos + 1))
            i += 1
            continue
        if ch in "+-−*/·⋅×^":
            norm_op = "-" if ch == "−" else "*" if ch in "·⋅×" else ch
            toks.append(_Tok("OP", norm_op, pos, pos + 1))
            i += 1
            continue
        if ("A" <= ch <= "Z") or ("a" <= ch <= "z"):
            j = i
            while j < n and (("A" <= src[j] <= "Z") or ("a" <= src[j] <= "z")):
                j += 1
            word = src[i:j]
            low = word.lower()
            if low == "sqrt":
                toks.append(_Tok("SQRT", word, pos, base_offset + j))
            elif low == "pi":
                toks.append(_Tok("PI", word, pos, base_offset + j))
            elif len(word) == 1:
                toks.append(_Tok("SYM", word, pos, base_offset + j))
            else:
                raise ExprParseError(
                    "INVALID_IDENTIFIER",
                    f"định danh nhiều ký tự {word!r} không phải ký hiệu số đo hợp lệ",
                )
            i = j
            continue
        raise ExprParseError("SYNTAX_ERROR", f"ký tự không hợp lệ {ch!r} tại vị trí {pos}")
    return toks


class _Parser:
    def __init__(self, toks: list[_Tok], *, allow_signed: bool) -> None:
        self.toks = toks
        self.idx = 0
        self.allow_signed = allow_signed

    def peek(self) -> _Tok | None:
        return self.toks[self.idx] if self.idx < len(self.toks) else None

    def take(self) -> _Tok:
        t = self.toks[self.idx]
        self.idx += 1
        return t

    def parse_expr(self) -> ExprNode:
        node = self.parse_term()
        while (t := self.peek()) is not None and t.kind == "OP" and t.text in ("+", "-"):
            op_tok = self.take()
            rhs = self.parse_term()
            node = BinOp(op_tok.text, node, rhs, False, (node.span[0], rhs.span[1]))  # type: ignore[arg-type]
        return node

    def _can_implicitly_multiply(self, left: ExprNode, nxt: _Tok) -> bool:
        if nxt.kind not in ("SYM", "PI", "SQRT", "LPAREN", "NUM"):
            return False
        if nxt.kind == "NUM":
            if isinstance(left, RationalLit):
                raise ExprParseError(
                    "ADJACENT_NUMBERS",
                    "hai hằng số đứng cạnh nhau thiếu toán tử",
                )
            raise ExprParseError(
                "AMBIGUOUS_POSTFIX_NUMBER",
                f"chữ số {nxt.text!r} đứng ngay sau biểu thức (nghi mất dấu mũ hoặc thiếu '*')",
            )
        return True

    def parse_term(self) -> ExprNode:
        node = self.parse_unary(top_level=(self.idx == 0))
        while (t := self.peek()) is not None:
            if t.kind == "OP" and t.text in ("*", "/"):
                op_tok = self.take()
                rhs = self.parse_unary(top_level=False)
                node = BinOp(op_tok.text, node, rhs, False, (node.span[0], rhs.span[1]))  # type: ignore[arg-type]
            elif self._can_implicitly_multiply(node, t):
                rhs = self.parse_power()
                node = BinOp("*", node, rhs, True, (node.span[0], rhs.span[1]))
            else:
                break
        return node

    def parse_unary(self, *, top_level: bool) -> ExprNode:
        t = self.peek()
        if t is not None and t.kind == "OP" and t.text in ("+", "-"):
            if top_level and not self.allow_signed:
                raise ExprParseError(
                    "SIGNED_VALUE_FORBIDDEN",
                    f"không nhận dấu âm/dương đầu số đo {t.text!r}",
                )
            op_tok = self.take()
            inner = self.parse_unary(top_level=False)
            return UnaryOp(op_tok.text, inner, (op_tok.start, inner.span[1]))  # type: ignore[arg-type]
        return self.parse_power()

    def parse_power(self) -> ExprNode:
        base = self.parse_atom()
        t = self.peek()
        if t is not None and t.kind == "SUP":
            sup_tok = self.take()
            if (nxt := self.peek()) is not None and (nxt.kind == "SUP" or (nxt.kind == "OP" and nxt.text == "^")):
                raise ExprParseError("AMBIGUOUS_EXPONENT", "không nối tiếp nhiều số mũ liên tiếp")
            return PowOp(base, _SUP_MAP[sup_tok.text], sup_tok.text, (base.span[0], sup_tok.end))
        if t is not None and t.kind == "OP" and t.text == "^":
            self.take()
            exp_val, exp_raw, exp_end = self._parse_exponent_value()
            if (nxt := self.peek()) is not None and (nxt.kind == "SUP" or (nxt.kind == "OP" and nxt.text == "^")):
                raise ExprParseError("AMBIGUOUS_EXPONENT", "lũy thừa chồng a^b^c cần đóng ngoặc tường minh")
            return PowOp(base, exp_val, exp_raw, (base.span[0], exp_end))
        return base

    def _parse_exponent_value(self) -> tuple[int, str, int]:
        t = self.peek()
        if t is None:
            raise ExprParseError("SYNTAX_ERROR", "thiếu số mũ sau '^'")
        if t.kind == "NUM":
            nt = self.take()
            if "," in nt.text or "." in nt.text:
                raise ExprDomainError("FRACTIONAL_EXPONENT", f"số mũ không nguyên: {nt.text!r}")
            val = int(nt.text)
            if abs(val) > MAX_EXPONENT:
                raise ExprDomainError("EXACT_DOMAIN_EXCEEDED", f"số mũ {val} vượt trần {MAX_EXPONENT}")
            return val, nt.text, nt.end
        if t.kind == "LPAREN":
            lp = self.take()
            saved_signed = self.allow_signed
            self.allow_signed = True
            try:
                inner = self.parse_expr()
            finally:
                self.allow_signed = saved_signed
            rp = self.peek()
            if rp is None or rp.kind != "RPAREN":
                raise ExprParseError("UNBALANCED_PAREN", f"thiếu ')' đóng số mũ mở tại {lp.start}")
            self.take()
            ev = evaluate_quantity(
                QuantityExpr(
                    inner,
                    ExprProvenance("", "", (lp.start, rp.end), ()),
                ),
                symbol_dims={},
            )
            if ev.symbols or ev.referenced_symbols:
                raise ExprDomainError("EXACT_DOMAIN_EXCEEDED", "số mũ không được chứa biến")
            if isinstance(ev.coeff, Radical) or ev.coeff.denominator != 1:
                raise ExprDomainError("FRACTIONAL_EXPONENT", f"số mũ phân số/vô tỉ không thuộc miền: {ev.coeff}")
            val = int(ev.coeff.numerator)
            if abs(val) > MAX_EXPONENT:
                raise ExprDomainError("EXACT_DOMAIN_EXCEEDED", f"số mũ {val} vượt trần {MAX_EXPONENT}")
            return val, str(val), rp.end
        if t.kind == "OP" and t.text in ("+", "-"):
            if not self.allow_signed:
                raise ExprDomainError("EXACT_DOMAIN_EXCEEDED", "số mũ âm không hợp lệ cho đại lượng trực tiếp")
            op_tok = self.take()
            nt = self.peek()
            if nt is None or nt.kind != "NUM" or "," in nt.text or "." in nt.text:
                raise ExprDomainError("FRACTIONAL_EXPONENT", "số mũ sau dấu phải là số nguyên")
            self.take()
            val = -int(nt.text) if op_tok.text == "-" else int(nt.text)
            if abs(val) > MAX_EXPONENT:
                raise ExprDomainError("EXACT_DOMAIN_EXCEEDED", f"số mũ {val} vượt trần {MAX_EXPONENT}")
            return val, f"{op_tok.text}{nt.text}", nt.end
        raise ExprParseError("SYNTAX_ERROR", f"số mũ không hợp lệ {t.text!r}")

    def parse_atom(self) -> ExprNode:
        t = self.peek()
        if t is None:
            raise ExprParseError("SYNTAX_ERROR", "biểu thức kết thúc đột ngột")
        if t.kind == "NUM":
            nt = self.take()
            val = Fraction(nt.text.replace(",", "."))
            return RationalLit(val, nt.text, (nt.start, nt.end))
        if t.kind == "PI":
            pt = self.take()
            return PiLit(pt.text, (pt.start, pt.end))
        if t.kind == "SYM":
            st = self.take()
            return SymbolRef(st.text, (st.start, st.end))
        if t.kind == "SQRT":
            sq = self.take()
            nxt = self.peek()
            if nxt is None:
                raise ExprParseError("SYNTAX_ERROR", "thiếu biểu thức dưới dấu căn")
            if sq.text.lower() == "sqrt" and nxt.kind != "LPAREN":
                raise ExprParseError("SYNTAX_ERROR", "sqrt đòi hỏi dấu ngoặc sqrt(...)")
            if nxt.kind == "LPAREN":
                lp = self.take()
                saved_signed = self.allow_signed
                self.allow_signed = True
                try:
                    rad = self.parse_expr()
                finally:
                    self.allow_signed = saved_signed
                rp = self.peek()
                if rp is None or rp.kind != "RPAREN":
                    raise ExprParseError("UNBALANCED_PAREN", f"thiếu ')' đóng dấu căn mở tại {lp.start}")
                self.take()
                return SqrtOp(rad, (sq.start, rp.end))
            if nxt.kind == "NUM":
                nt = self.take()
                lit = RationalLit(Fraction(nt.text.replace(",", ".")), nt.text, (nt.start, nt.end))
                return SqrtOp(lit, (sq.start, nt.end))
            if nxt.kind in ("SYM", "PI"):
                atom = self.parse_power()
                return SqrtOp(atom, (sq.start, atom.span[1]))
            raise ExprParseError("SYNTAX_ERROR", f"toán hạng sau √ không hợp lệ: {nxt.text!r}")
        if t.kind == "LPAREN":
            lp = self.take()
            inner = self.parse_expr()
            rp = self.peek()
            if rp is None or rp.kind != "RPAREN":
                raise ExprParseError("UNBALANCED_PAREN", f"thiếu ')' cho '(' tại vị trí {lp.start}")
            self.take()
            return inner
        raise ExprParseError("SYNTAX_ERROR", f"token không mong đợi {t.text!r} tại vị trí {t.start}")


def parse_quantity_expr(
    text: str,
    *,
    base_offset: int = 0,
    allow_signed: bool = False,
    allow_unit: bool = False,
    role: FactRole = FactRole.SOURCE_QUANTITY,
) -> QuantityExpr:
    """Parse an exact mathematical quantity expression with full span & operand provenance."""
    if not isinstance(text, str):
        raise ExprParseError("EMPTY_EXPRESSION", f"biểu thức phải là chuỗi, nhận {type(text).__name__}")
    ltrim = len(text) - len(text.lstrip())
    rtrim = len(text.rstrip())
    if ltrim >= rtrim:
        raise ExprParseError("EMPTY_EXPRESSION", "biểu thức rỗng")
    core = text[ltrim:rtrim]
    core_offset = base_offset + ltrim
    unit: MeasurementUnit | None = None
    expr_body = core
    if allow_unit:
        um = _TRAILING_UNIT_RE.search(core)
        if um is not None and um.start() > 0:
            raw_u = um.group("uparen") or um.group("udeg") or um.group("uword") or um.group("umult") or ""
            parsed_u = parse_measurement_unit(raw_u)
            if parsed_u is not None and core[: um.start()].strip():
                unit = parsed_u
                expr_body = core[: um.start()].rstrip()
    toks = _tokenize(expr_body, core_offset)
    if not toks:
        raise ExprParseError("EMPTY_EXPRESSION", "biểu thức rỗng")
    parser = _Parser(toks, allow_signed=allow_signed)
    ast = parser.parse_expr()
    if parser.peek() is not None:
        rem = parser.peek()
        assert rem is not None
        raise ExprParseError("SYNTAX_ERROR", f"phần dư chưa đọc {rem.text!r} tại vị trí {rem.start}")
    full_span = (core_offset, base_offset + rtrim)
    if unit is not None:
        ast = AnnotatedQuantity(ast, unit, full_span)
    op_spans: list[tuple[str, int, int]] = []
    _collect_operand_spans(ast, op_spans)
    prov = ExprProvenance(
        original_expr=core,
        normalized_expr=_format_ast_normalized(ast),
        source_span=full_span,
        operand_spans=tuple(op_spans),
        unit=unit,
        role=role,
    )
    return QuantityExpr(ast=ast, provenance=prov)


_CONTIGUOUS_BAD_TAIL_RE = re.compile(r"^(?:[A-Za-z0-9À-ỹ²³√^]|,\d|\.\d|\s+\d)")
_EXPR_CHAR_STOP_RE = re.compile(r"[.;:!?]")


def scan_expression_prefix(
    text: str,
    start: int = 0,
    *,
    allow_signed: bool = False,
    allow_unit: bool = False,
    role: FactRole = FactRole.SOURCE_QUANTITY,
) -> tuple[QuantityExpr, int] | None:
    """Scan the longest valid, balanced quantity expression starting at `text[start:]`.

    Stops cleanly before Vietnamese prose words or unrelated parenthesized notes such as
    `(tham khảo hình bên dưới)`, while rejecting malformed contiguous tokens such as
    `3,5,6`, `a2`, or `a²ln2` (returns `None` so caller preserves `UNREAD_VALUE`).
    """
    n = len(text)
    i = start
    while i < n and text[i].isspace():
        i += 1
    if i >= n:
        return None
    # Collect candidate end offsets at clean token boundaries, respecting balanced parentheses.
    candidates: list[int] = []
    depth = 0
    j = i
    while j < n:
        ch = text[j]
        if depth == 0 and _EXPR_CHAR_STOP_RE.match(ch):
            break
        if ch == "(":
            depth += 1
            j += 1
            continue
        if ch == ")":
            if depth == 0:
                break
            depth -= 1
            j += 1
            if depth == 0:
                candidates.append(j)
            continue
        # Stop scanning across multi-letter Vietnamese prose words at depth 0 (except sqrt/pi/units).
        if depth == 0 and (ch.isalpha() or "\u00c0" <= ch <= "\u1ef9"):
            k = j
            while k < n and (text[k].isalpha() or "\u00c0" <= text[k] <= "\u1ef9"):
                k += 1
            word = text[j:k]
            low = word.lower()
            is_unit_word = allow_unit and parse_measurement_unit(word) is not None
            if len(word) > 1 and low not in ("sqrt", "pi") and not is_unit_word:
                # Contiguous invalid suffix attached directly to previous math char (`a²ln2`) -> hard fail!
                if j > i and not text[j - 1].isspace():
                    return None
                break
            j = k
            if depth == 0:
                candidates.append(j)
            continue
        j += 1
        if depth == 0 and not ch.isspace():
            candidates.append(j)

    for end_idx in reversed(candidates):
        tail = text[end_idx:]
        if _CONTIGUOUS_BAD_TAIL_RE.match(tail):
            continue
        sub = text[i:end_idx]
        try:
            qexpr = parse_quantity_expr(
                sub,
                base_offset=i,
                allow_signed=allow_signed,
                allow_unit=allow_unit,
                role=role,
            )
            return qexpr, end_idx
        except ExpressionError:
            continue
    return None


# ── EXACT EVALUATION & DIMENSIONAL MONOMIAL ALGEBRA ───────────────────────────


def _exact_divide(a: ExactNumber, b: ExactNumber) -> ExactNumber:
    if radical_sign(b) == 0:
        raise ExprDomainError("ZERO_DIVISOR", "chia cho 0")
    if not isinstance(b, Radical):
        return times_rational(a, Fraction(1) / Fraction(b))
    ha = a.he if isinstance(a, Radical) else Fraction(a)
    ca = a.can if isinstance(a, Radical) else 1
    ma = a.mu if isinstance(a, Radical) else 0
    mu_diff = ma - b.mu
    if mu_diff not in PI_EXPONENT_DOMAIN:
        raise ExprDomainError(
            "EXACT_DOMAIN_EXCEEDED",
            f"phép chia sinh số mũ π = {mu_diff} ngoài miền {PI_EXPONENT_DOMAIN}",
        )
    if ha == 0:
        return Fraction(0)
    try:
        return radical(ha / (b.he * b.can), ca * b.can, mu_diff)
    except RadicalDomainError as exc:
        raise ExprDomainError("EXACT_DOMAIN_EXCEEDED", str(exc)) from None


def _exact_pow(val: ExactNumber, exp: int) -> ExactNumber:
    if exp == 0:
        if radical_sign(val) == 0:
            raise ExprDomainError("ZERO_DIVISOR", "0^0 không xác định")
        return Fraction(1)
    if exp < 0:
        if radical_sign(val) == 0:
            raise ExprDomainError("ZERO_DIVISOR", "luỹ thừa âm của 0 chia cho 0")
        pos = _exact_pow(val, -exp)
        return _exact_divide(Fraction(1), pos)
    acc: ExactNumber = Fraction(1)
    try:
        for _ in range(exp):
            acc = radical_multiply(acc, val)
    except RadicalDomainError as exc:
        raise ExprDomainError("EXACT_DOMAIN_EXCEEDED", str(exc)) from None
    return acc


def _merge_exps(
    a: tuple[tuple[str, int], ...],
    b: tuple[tuple[str, int], ...],
    scale_b: int = 1,
) -> tuple[tuple[str, int], ...]:
    merged: dict[str, int] = dict(a)
    for sym, e in b:
        nv = merged.get(sym, 0) + scale_b * e
        if nv == 0:
            merged.pop(sym, None)
        else:
            merged[sym] = nv
    return tuple(sorted(merged.items()))


@dataclass(frozen=True)
class EvaluatedQuantity:
    """Exact evaluated monomial `coeff · Π sym^exp` with verified dimension & obligations."""

    coeff: ExactNumber
    symbols: tuple[tuple[str, int], ...]
    dimension: Dimension
    provenance: ExprProvenance
    referenced_symbols: frozenset[str] = frozenset()
    nonzero_obligations: frozenset[str] = frozenset()
    positive_obligations: frozenset[str] = frozenset()
    explicit_dimension: bool = False

    @property
    def coeff_sq(self) -> Fraction:
        try:
            return radical_square(self.coeff)
        except RadicalDomainError as exc:
            raise ExprDomainError("EXACT_DOMAIN_EXCEEDED", str(exc)) from None

    @property
    def sign(self) -> int:
        return radical_sign(self.coeff)

    def format_canonical(self) -> str:
        c_str = radical_display(self.coeff)
        if not self.symbols or self.sign == 0:
            return c_str
        sym_parts = []
        for s, e in self.symbols:
            if e == 1:
                sym_parts.append(s)
            elif e == 2:
                sym_parts.append(f"{s}²")
            elif e == 3:
                sym_parts.append(f"{s}³")
            else:
                sym_parts.append(f"{s}^{e}")
        sym_str = "".join(sym_parts)
        if self.coeff == Fraction(1):
            return sym_str
        if self.coeff == Fraction(-1):
            return f"-{sym_str}"
        if "/" in c_str:
            num, den = c_str.split("/", 1)
            if "√" in num:
                m = re.match(r"^(-?\d*)(π?)(√\d+)$", num)
                if m:
                    return f"{m.group(1)}{m.group(2)}{sym_str}{m.group(3)}/{den}"
            lead = "" if num == "1" else "-" if num == "-1" else num
            return f"{lead}{sym_str}/{den}"
        if "√" in c_str:
            m = re.match(r"^(-?\d*)(π?)(√\d+)$", c_str)
            if m:
                return f"{m.group(1)}{m.group(2)}{sym_str}{m.group(3)}"
        return f"{c_str}{sym_str}"


def evaluate_quantity(
    qexpr: QuantityExpr,
    *,
    symbol_dims: Mapping[str, Dimension] | None = None,
    certified_positive_symbols: AbstractSet[str] = frozenset(),
    certified_nonzero_symbols: AbstractSet[str] = frozenset(),
    expected_dim: Dimension | None = None,
    require_positive: bool = False,
) -> EvaluatedQuantity:
    """Evaluate `qexpr` over `Fraction`/`Radical` with strict dimension and domain checks."""
    sdims = dict(symbol_dims or {})
    pos_syms = set(certified_positive_symbols)
    nz_syms = set(certified_nonzero_symbols) | pos_syms

    def _eval(node: ExprNode) -> EvaluatedQuantity:
        if isinstance(node, RationalLit):
            return EvaluatedQuantity(
                coeff=node.value,
                symbols=(),
                dimension=SCALAR,
                provenance=qexpr.provenance,
                explicit_dimension=False,
            )
        if isinstance(node, PiLit):
            return EvaluatedQuantity(
                coeff=radical(Fraction(1), 1, mu=1),
                symbols=(),
                dimension=SCALAR,
                provenance=qexpr.provenance,
                explicit_dimension=False,
            )
        if isinstance(node, SymbolRef):
            if node.name not in sdims:
                raise ExprDomainError(
                    "UNGROUNDED_SYMBOL",
                    f"ký hiệu {node.name!r} chưa được gán thứ nguyên từ ngữ cảnh hình học",
                )
            d = sdims[node.name]
            return EvaluatedQuantity(
                coeff=Fraction(1),
                symbols=((node.name, 1),),
                dimension=d,
                provenance=qexpr.provenance,
                referenced_symbols=frozenset((node.name,)),
                explicit_dimension=True,
            )
        if isinstance(node, AnnotatedQuantity):
            inner = _eval(node.expr)
            u_dim = node.unit.dimension
            if inner.explicit_dimension and inner.dimension != u_dim:
                raise ExprDimensionError(
                    "UNIT_DIMENSION_MISMATCH",
                    f"biểu thức ({inner.dimension.name}) không khớp đơn vị {node.unit.raw_unit!r} ({u_dim.name})",
                )
            return EvaluatedQuantity(
                coeff=inner.coeff,
                symbols=inner.symbols,
                dimension=u_dim,
                provenance=qexpr.provenance,
                referenced_symbols=inner.referenced_symbols,
                nonzero_obligations=inner.nonzero_obligations,
                positive_obligations=inner.positive_obligations,
                explicit_dimension=True,
            )
        if isinstance(node, UnaryOp):
            sub = _eval(node.operand)
            c = radical_negate(sub.coeff) if node.op == "-" else sub.coeff
            return EvaluatedQuantity(
                coeff=c,
                symbols=sub.symbols,
                dimension=sub.dimension,
                provenance=qexpr.provenance,
                referenced_symbols=sub.referenced_symbols,
                nonzero_obligations=sub.nonzero_obligations,
                positive_obligations=sub.positive_obligations,
                explicit_dimension=sub.explicit_dimension,
            )
        if isinstance(node, BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            refs = left.referenced_symbols | right.referenced_symbols
            nz_obs = left.nonzero_obligations | right.nonzero_obligations
            pos_obs = left.positive_obligations | right.positive_obligations
            if node.op in ("+", "-"):
                res_dim = dim_add(left.dimension, right.dimension)
                if left.symbols != right.symbols:
                    raise ExprDomainError(
                        "EXACT_DOMAIN_EXCEEDED",
                        "tổng/hiệu khác bậc ký hiệu không rút gọn được thành đơn thức chính xác",
                    )
                rhs_c = radical_negate(right.coeff) if node.op == "-" else right.coeff
                try:
                    c = radical_add(left.coeff, rhs_c)
                except RadicalDomainError as exc:
                    raise ExprDomainError("EXACT_DOMAIN_EXCEEDED", str(exc)) from None
                syms = () if radical_sign(c) == 0 else left.symbols
                return EvaluatedQuantity(
                    coeff=c,
                    symbols=syms,
                    dimension=res_dim,
                    provenance=qexpr.provenance,
                    referenced_symbols=refs,
                    nonzero_obligations=nz_obs,
                    positive_obligations=pos_obs,
                    explicit_dimension=left.explicit_dimension or right.explicit_dimension,
                )
            if node.op == "*":
                res_dim = dim_mul(left.dimension, right.dimension)
                try:
                    c = radical_multiply(left.coeff, right.coeff)
                except RadicalDomainError as exc:
                    raise ExprDomainError("EXACT_DOMAIN_EXCEEDED", str(exc)) from None
                syms = () if radical_sign(c) == 0 else _merge_exps(left.symbols, right.symbols, 1)
                return EvaluatedQuantity(
                    coeff=c,
                    symbols=syms,
                    dimension=res_dim,
                    provenance=qexpr.provenance,
                    referenced_symbols=refs,
                    nonzero_obligations=nz_obs,
                    positive_obligations=pos_obs,
                    explicit_dimension=left.explicit_dimension or right.explicit_dimension,
                )
            if node.op == "/":
                if radical_sign(right.coeff) == 0:
                    raise ExprDomainError("ZERO_DIVISOR", "chia cho 0")
                denom_syms = {s for s, _ in right.symbols} | set(right.referenced_symbols)
                uncert = denom_syms - nz_syms
                if uncert:
                    raise ExprDomainError(
                        "UNCERTAIN_DIVISOR_ZERO",
                        f"mẫu số chứa ký hiệu chưa có chứng chỉ khác 0: {sorted(uncert)}",
                    )
                res_dim = dim_div(left.dimension, right.dimension)
                c = _exact_divide(left.coeff, right.coeff)
                syms = () if radical_sign(c) == 0 else _merge_exps(left.symbols, right.symbols, -1)
                return EvaluatedQuantity(
                    coeff=c,
                    symbols=syms,
                    dimension=res_dim,
                    provenance=qexpr.provenance,
                    referenced_symbols=refs,
                    nonzero_obligations=nz_obs | frozenset(denom_syms),
                    positive_obligations=pos_obs,
                    explicit_dimension=left.explicit_dimension or right.explicit_dimension,
                )
        if isinstance(node, PowOp):
            base = _eval(node.base)
            res_dim = dim_pow(base.dimension, node.exp)
            c = _exact_pow(base.coeff, node.exp)
            nz_obs = set(base.nonzero_obligations)
            if node.exp <= 0 and base.referenced_symbols:
                uncert = set(base.referenced_symbols) - nz_syms
                if uncert:
                    raise ExprDomainError(
                        "UNCERTAIN_DIVISOR_ZERO",
                        f"cơ số luỹ thừa {node.exp} chứa ký hiệu chưa có chứng chỉ khác 0: {sorted(uncert)}",
                    )
                nz_obs |= set(base.referenced_symbols)
            syms = (
                ()
                if node.exp == 0 or radical_sign(c) == 0
                else tuple((s, e * node.exp) for s, e in base.symbols)
            )
            return EvaluatedQuantity(
                coeff=c,
                symbols=syms,
                dimension=res_dim,
                provenance=qexpr.provenance,
                referenced_symbols=base.referenced_symbols,
                nonzero_obligations=frozenset(nz_obs),
                positive_obligations=base.positive_obligations,
                explicit_dimension=base.explicit_dimension and node.exp != 0,
            )
        if isinstance(node, SqrtOp):
            rad = _eval(node.radicand)
            if radical_sign(rad.coeff) < 0:
                raise ExprDomainError("NEGATIVE_RADICAND", "không lấy căn bậc hai của đại lượng âm")
            # Check odd symbol exponents BEFORE or alongside dimension sqrt so √(3a) always fails closed.
            for s, e in rad.symbols:
                if e % 2 != 0:
                    # Prefer FRACTIONAL_DIMENSION when dimension is odd, else ODD_SYMBOL_RADICAND.
                    dim_sqrt(rad.dimension)
                    raise ExprDomainError(
                        "FRACTIONAL_EXPONENT",
                        f"căn bậc hai sinh số mũ phân số cho ký hiệu {s!r}",
                    )
            res_dim = dim_sqrt(rad.dimension)
            if radical_sign(rad.coeff) == 0:
                return EvaluatedQuantity(
                    coeff=Fraction(0),
                    symbols=(),
                    dimension=res_dim,
                    provenance=qexpr.provenance,
                    referenced_symbols=rad.referenced_symbols,
                    nonzero_obligations=rad.nonzero_obligations,
                    positive_obligations=rad.positive_obligations,
                    explicit_dimension=rad.explicit_dimension,
                )
            if isinstance(rad.coeff, Radical):
                raise ExprDomainError(
                    "EXACT_DOMAIN_EXCEEDED",
                    f"căn lồng nhau √({radical_display(rad.coeff)}) vượt miền đơn thức căn bậc hai",
                )
            pos_needed: set[str] = set()
            for s, e in rad.symbols:
                if (e // 2) % 2 != 0:
                    if s not in pos_syms:
                        raise ExprDomainError(
                            "DOMAIN_SIGN_UNPROVED",
                            f"rút gọn √({s}^{e}) thành {s}^{e // 2} đòi hỏi chứng chỉ {s} > 0",
                        )
                    pos_needed.add(s)
            try:
                c = sqrt_rational(rad.coeff)
            except RadicalDomainError as exc:
                raise ExprDomainError("EXACT_DOMAIN_EXCEEDED", str(exc)) from None
            syms = tuple((s, e // 2) for s, e in rad.symbols)
            return EvaluatedQuantity(
                coeff=c,
                symbols=syms,
                dimension=res_dim,
                provenance=qexpr.provenance,
                referenced_symbols=rad.referenced_symbols,
                nonzero_obligations=rad.nonzero_obligations,
                positive_obligations=rad.positive_obligations | frozenset(pos_needed),
                explicit_dimension=rad.explicit_dimension,
            )
        raise ExprParseError("SYNTAX_ERROR", f"nút AST không xác định: {type(node).__name__}")

    out = _eval(qexpr.ast)
    if expected_dim is not None:
        if out.explicit_dimension or out.symbols:
            if out.dimension != expected_dim:
                raise ExprDimensionError(
                    "DIMENSION_MISMATCH",
                    f"biểu thức {qexpr.provenance.original_expr!r} có thứ nguyên {out.dimension.name}, "
                    f"nhưng vị trí hình học đòi hỏi {expected_dim.name}",
                )
        else:
            out = EvaluatedQuantity(
                coeff=out.coeff,
                symbols=out.symbols,
                dimension=expected_dim,
                provenance=out.provenance,
                referenced_symbols=out.referenced_symbols,
                nonzero_obligations=out.nonzero_obligations,
                positive_obligations=out.positive_obligations,
                explicit_dimension=True,
            )
    if require_positive:
        if out.sign <= 0:
            raise ExprDomainError(
                "NON_POSITIVE_QUANTITY",
                f"đại lượng hình học phải dương, nhận {qexpr.provenance.original_expr!r}",
            )
        odd_uncert = [s for s, e in out.symbols if e % 2 != 0 and s not in pos_syms]
        if odd_uncert:
            raise ExprDomainError(
                "INDETERMINATE_SIGN",
                f"dấu của {qexpr.provenance.original_expr!r} chưa xác định do {odd_uncert} chưa chứng nhận > 0",
            )
    return out


# ── CONTEXT-DRIVEN SYMBOL ENVIRONMENT ─────────────────────────────────────────


@dataclass(frozen=True)
class SlotQuantityEntry:
    call_id: str
    slot_name: str
    value: str | QuantityExpr
    target_dim: Dimension
    role: FactRole = FactRole.SOURCE_QUANTITY
    require_positive: bool = True


@dataclass(frozen=True)
class SymbolBindingPlan:
    symbol_dims: Mapping[str, Dimension]
    length_unit_symbol: str | None
    non_length_scale_symbol: tuple[str, Dimension] | None
    metric_base_unit: str | None
    evaluated_by_call: Mapping[tuple[str, str], EvaluatedQuantity]

    def check_goal_admissibility(
        self,
        goal_degrees: Sequence[int],
        *,
        target_invariant: bool = False,
    ) -> None:
        """Guard against single-premise non-length symbols (`S : L^2`, `V : L^3`) being coerced to `L^1`."""
        if self.non_length_scale_symbol is None:
            return
        sym, sdim = self.non_length_scale_symbol
        if not goal_degrees or any(d > 0 for d in goal_degrees) or not target_invariant:
            raise ExprDomainError(
                "EXACT_DOMAIN_EXCEEDED",
                f"tham số {sym!r} có thứ nguyên {sdim.name} và không có đơn vị độ dài L¹: "
                "từ chối ép kiểu sang L¹ để ngăn luỹ thừa phân số sai",
            )


def _provisional_net_exponents(node: ExprNode) -> dict[str, int] | None:
    """Extract net symbol exponents on a multiplicative/power/sqrt chain for constraint inference."""
    if isinstance(node, (RationalLit, PiLit)):
        return {}
    if isinstance(node, SymbolRef):
        return {node.name: 1}
    if isinstance(node, AnnotatedQuantity):
        return _provisional_net_exponents(node.expr)
    if isinstance(node, UnaryOp):
        return _provisional_net_exponents(node.operand)
    if isinstance(node, PowOp):
        sub = _provisional_net_exponents(node.base)
        if sub is None:
            return None
        return {} if node.exp == 0 else {s: e * node.exp for s, e in sub.items() if e * node.exp != 0}
    if isinstance(node, SqrtOp):
        sub = _provisional_net_exponents(node.radicand)
        if sub is None or any(e % 2 != 0 for e in sub.values()):
            return None
        return {s: e // 2 for s, e in sub.items() if e // 2 != 0}
    if isinstance(node, BinOp):
        left = _provisional_net_exponents(node.left)
        right = _provisional_net_exponents(node.right)
        if left is None or right is None:
            return None
        if node.op in ("+", "-"):
            return dict(left) if left == right else None
        scale = 1 if node.op == "*" else -1
        out = dict(left)
        for s, e in right.items():
            nv = out.get(s, 0) + scale * e
            if nv == 0:
                out.pop(s, None)
            else:
                out[s] = nv
        return out
    return None


class SymbolEnvironment:
    """Context-driven symbol dimension unifier across all premises of a geometry problem."""

    @staticmethod
    def bind_slots(
        entries: Sequence[SlotQuantityEntry],
        *,
        allow_unit: bool = False,
    ) -> SymbolBindingPlan:
        parsed_entries: list[tuple[SlotQuantityEntry, QuantityExpr]] = []
        units: list[MeasurementUnit] = []
        all_refs: set[str] = set()

        for entry in entries:
            if entry.role == FactRole.UNVERIFIED_CANDIDATE:
                raise ExprDomainError(
                    "UNGROUNDED_SYMBOL",
                    f"{entry.call_id}.{entry.slot_name}: đại lượng UNVERIFIED_CANDIDATE không được phép đi vào thực thi",
                )
            qexpr = (
                entry.value
                if isinstance(entry.value, QuantityExpr)
                else parse_quantity_expr(
                    entry.value,
                    allow_signed=False,
                    allow_unit=allow_unit,
                    role=entry.role,
                )
            )
            if qexpr.provenance.unit is not None:
                validate_unit_consistency([qexpr.provenance.unit], expected_dim=entry.target_dim)
                units.append(qexpr.provenance.unit)
            all_refs |= set(qexpr.referenced_symbols)
            parsed_entries.append((entry, qexpr))

        metric_base_unit = validate_unit_consistency(units)

        inferred: dict[str, Dimension] = {}
        # Pass 1: infer symbol dimensions strictly from geometric slot dimensions (never from symbol names).
        for entry, qexpr in parsed_entries:
            m = entry.target_dim.length_exp
            if entry.target_dim.is_angle or m <= 0:
                continue
            refs = qexpr.referenced_symbols
            if not refs:
                continue
            net = _provisional_net_exponents(qexpr.ast)
            if net is None:
                # Could be e.g. `a + a²` or `√(3a)` in a single-symbol slot: test candidate L^1..L^3 to surface
                # the exact dimension/radical error in Pass 2 if another slot doesn't already bind `s`.
                if len(refs) == 1:
                    only_sym = next(iter(refs))
                    inferred.setdefault(only_sym, LENGTH)
                continue
            if len(net) == 1:
                sym, k = next(iter(net.items()))
                if k <= 0 or m % k != 0:
                    raise ExprDimensionError(
                        "DIMENSION_MISMATCH",
                        f"{entry.call_id}.{entry.slot_name}: số mũ ký hiệu {sym}^{k} không khớp thứ nguyên {entry.target_dim.name}",
                    )
                cand = Dimension(m // k, False)
                prev = inferred.get(sym)
                if prev is not None and prev != cand:
                    raise ExprDimensionError(
                        "DIMENSION_MISMATCH",
                        f"ký hiệu {sym!r} xung đột thứ nguyên giữa {prev.name} và {cand.name}",
                    )
                inferred[sym] = cand

        ungrounded = sorted(all_refs - set(inferred))
        if ungrounded:
            raise ExprDomainError(
                "UNGROUNDED_SYMBOL",
                f"ký hiệu tự do {ungrounded} không được neo thứ nguyên bởi dữ kiện độ đo dương nào",
            )

        if len(inferred) > 1:
            raise ExprDomainError(
                "NON_HOMOGENEOUS_LENGTHS",
                f"bài toán chứa nhiều tham số độc lập chưa liên hệ: {sorted(inferred)}",
            )

        cert_pos = frozenset(inferred)
        evaluated: dict[tuple[str, str], EvaluatedQuantity] = {}
        has_numeric_metric = False
        has_symbolic_metric = False

        # Pass 2: evaluate every AST with full dimensional & domain enforcement.
        for entry, qexpr in parsed_entries:
            ev = evaluate_quantity(
                qexpr,
                symbol_dims=inferred,
                certified_positive_symbols=cert_pos,
                expected_dim=entry.target_dim,
                require_positive=entry.require_positive,
            )
            evaluated[(entry.call_id, entry.slot_name)] = ev
            if not entry.target_dim.is_angle and entry.target_dim.length_exp > 0:
                if ev.symbols:
                    has_symbolic_metric = True
                else:
                    has_numeric_metric = True

        if has_numeric_metric and has_symbolic_metric:
            raise ExprDomainError(
                "NON_HOMOGENEOUS_LENGTHS",
                "không trộn lẫn số đo cụ thể và tham số ký hiệu trong cùng bài toán",
            )

        length_unit_sym: str | None = None
        non_length_sym: tuple[str, Dimension] | None = None
        if len(inferred) == 1:
            sym, sdim = next(iter(inferred.items()))
            if sdim == LENGTH:
                length_unit_sym = sym
            else:
                non_length_sym = (sym, sdim)

        return SymbolBindingPlan(
            symbol_dims=inferred,
            length_unit_symbol=length_unit_sym,
            non_length_scale_symbol=non_length_sym,
            metric_base_unit=metric_base_unit,
            evaluated_by_call=evaluated,
        )


def substitute_symbol(
    qexpr: QuantityExpr,
    sym: str,
    replacement: str | QuantityExpr,
) -> QuantityExpr:
    """Deterministically substitute `sym` -> `replacement` AST (for dimensional metamorphic verification)."""
    rep_q = (
        replacement
        if isinstance(replacement, QuantityExpr)
        else parse_quantity_expr(replacement, allow_signed=False, allow_unit=False)
    )

    def _sub(node: ExprNode) -> ExprNode:
        if isinstance(node, SymbolRef):
            return rep_q.ast if node.name == sym else node
        if isinstance(node, (RationalLit, PiLit)):
            return node
        if isinstance(node, UnaryOp):
            return UnaryOp(node.op, _sub(node.operand), node.span)
        if isinstance(node, BinOp):
            return BinOp(node.op, _sub(node.left), _sub(node.right), node.implicit, node.span)
        if isinstance(node, PowOp):
            return PowOp(_sub(node.base), node.exp, node.raw_exp, node.span)
        if isinstance(node, SqrtOp):
            return SqrtOp(_sub(node.radicand), node.span)
        if isinstance(node, AnnotatedQuantity):
            return AnnotatedQuantity(_sub(node.expr), node.unit, node.span)
        return node

    new_ast = _sub(qexpr.ast)
    op_spans: list[tuple[str, int, int]] = []
    _collect_operand_spans(new_ast, op_spans)
    prov = ExprProvenance(
        original_expr=qexpr.provenance.original_expr,
        normalized_expr=_format_ast_normalized(new_ast),
        source_span=qexpr.provenance.source_span,
        operand_spans=tuple(op_spans),
        unit=qexpr.provenance.unit,
        role=qexpr.provenance.role,
    )
    return QuantityExpr(ast=new_ast, provenance=prov)
