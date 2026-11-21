# -*- coding: utf-8 -*-
"""Exact typed mathematical expression evaluator for Axo Hybrid /8 (axo-math-evaluator/2).

Replaces the frozen float-based and asymmetric `EVI.same_value` heuristic with:
1. Exact symbolic algebra over `Fraction` linear combinations of square-free integer
   radicals times `a^dim_a * pi^dim_pi` (zero floating-point comparison).
2. Explicit expression kinds (`SCALAR_OR_DIMENSIONAL`, `ANGLE_DEG`, `ANGLE_RAD`,
   `TRIG_COS`, `TRIG_COS2`, `TRIG_SIN`, `TRIG_SIN2`, `TRIG_TAN`, `TRIG_TAN2`,
   `TRIG_COT`, `TRIG_COT2`, `TRIG_COS_2X`) so `cos(x)`, `cos²(x)`, `cos(2x)`,
   degrees, and untagged scalars are never conflated by string similarity.
3. Goal-kind compatibility checks (`length`, `area`, `volume`, `ratio`, `angle`,
   `angle_oriented`, `trig_cos`, `trig_cos2`, `trig_sin`, `trig_tan`, `trig_cos_2x`).
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
import re
from typing import Any

EVALUATOR_VERSION = "axo-math-evaluator/2"

VALID_GOAL_KINDS = frozenset({
    "length",
    "area",
    "volume",
    "ratio",
    "angle",
    "angle_oriented",
    "trig_cos",
    "trig_cos2",
    "trig_sin",
    "trig_sin2",
    "trig_tan",
    "trig_tan2",
    "trig_cot",
    "trig_cos_2x",
})

_SUPERSCRIPT_MAP = str.maketrans({
    "²": "^2",
    "³": "^3",
    "⁰": "^0",
    "¹": "^1",
    "⁴": "^4",
    "⁵": "^5",
    "⁶": "^6",
    "⁷": "^7",
    "⁸": "^8",
    "⁹": "^9",
    "−": "-",
    "–": "-",
    "—": "-",
    "×": "*",
    "·": "*",
    "⋅": "*",
    "÷": "/",
    "∶": "/",
    "：": ":",
    "′": "'",
    "’": "'",
})

_TRIG_KIND_MAP = {
    "cos²": "TRIG_COS2",
    "cos^2": "TRIG_COS2",
    "sin²": "TRIG_SIN2",
    "sin^2": "TRIG_SIN2",
    "tan²": "TRIG_TAN2",
    "tan^2": "TRIG_TAN2",
    "tg²": "TRIG_TAN2",
    "tg^2": "TRIG_TAN2",
    "cot²": "TRIG_COT2",
    "cot^2": "TRIG_COT2",
    "cotg²": "TRIG_COT2",
    "cotg^2": "TRIG_COT2",
    "cos": "TRIG_COS",
    "sin": "TRIG_SIN",
    "tan": "TRIG_TAN",
    "tg": "TRIG_TAN",
    "cot": "TRIG_COT",
    "cotg": "TRIG_COT",
}

_GOAL_TO_TRIG_KIND = {
    "trig_cos": "TRIG_COS",
    "trig_cos2": "TRIG_COS2",
    "trig_sin": "TRIG_SIN",
    "trig_sin2": "TRIG_SIN2",
    "trig_tan": "TRIG_TAN",
    "trig_tan2": "TRIG_TAN2",
    "trig_cot": "TRIG_COT",
    "trig_cos_2x": "TRIG_COS_2X",
}

_METRIC_UNIT_RE = re.compile(
    r"^(.*?)(?:\s+|\b)(mm|cm|dm|km|m)(?:\s*\^\s*([23]))?(?:\s*(²|³))?\s*\.?\s*$",
    re.IGNORECASE,
)
_UNIT_SCALE_NUM = {
    "mm": Fraction(1, 1000),
    "cm": Fraction(1, 100),
    "dm": Fraction(1, 10),
    "m": Fraction(1, 1),
    "km": Fraction(1000, 1),
}

# Exact acute [0°, 90°] table: deg -> (cos^2, is_right_angle)
_SPECIAL_ANGLE_COS2: dict[Fraction, Fraction] = {
    Fraction(0): Fraction(1, 1),
    Fraction(30): Fraction(3, 4),
    Fraction(45): Fraction(1, 2),
    Fraction(60): Fraction(1, 4),
    Fraction(90): Fraction(0, 1),
}

# Exact special values in Q(sqrt(k)) for angles in [0°, 90°] with non-rational cos^2 (15°, 75°)
def _sqfree_parts(n: int) -> tuple[int, int]:
    """Return `(coeff, sqfree)` where `n = coeff² * sqfree`, `n >= 0`."""
    if n < 0:
        raise ValueError(f"negative radicand: {n}")
    if n == 0:
        return 0, 1
    coeff = 1
    rem = n
    d = 2
    while d * d <= rem:
        while rem % (d * d) == 0:
            coeff *= d
            rem //= d * d
        d += 1 if d == 2 else 2
    return coeff, rem


@dataclass(frozen=True)
class ExactAlgExpr:
    """Exact representation of `a^dim_a * pi^dim_pi * sum(coeff * sqrt(k))`."""

    dim_a: int
    dim_pi: int
    terms: tuple[tuple[int, Fraction], ...]  # sorted canonical (sqfree_k, nonzero Fraction)

    @staticmethod
    def zero() -> "ExactAlgExpr":
        return ExactAlgExpr(0, 0, ())

    @staticmethod
    def from_rational(val: Fraction | int, dim_a: int = 0, dim_pi: int = 0) -> "ExactAlgExpr":
        f = Fraction(val)
        if f == 0:
            return ExactAlgExpr(0, 0, ())
        return ExactAlgExpr(dim_a, dim_pi, ((1, f),))

    @staticmethod
    def from_terms(dim_a: int, dim_pi: int, term_dict: dict[int, Fraction]) -> "ExactAlgExpr":
        cleaned = tuple(sorted((k, v) for k, v in term_dict.items() if v != 0))
        if not cleaned:
            return ExactAlgExpr(0, 0, ())
        return ExactAlgExpr(dim_a, dim_pi, cleaned)

    def is_zero(self) -> bool:
        return not self.terms

    def is_rational_pure(self) -> Fraction | None:
        if self.dim_a != 0 or self.dim_pi != 0:
            return None
        if not self.terms:
            return Fraction(0)
        if len(self.terms) == 1 and self.terms[0][0] == 1:
            return self.terms[0][1]
        return None

    def as_dict(self) -> dict[int, Fraction]:
        return dict(self.terms)

    def neg(self) -> "ExactAlgExpr":
        return ExactAlgExpr(self.dim_a, self.dim_pi, tuple((k, -v) for k, v in self.terms))

    def scale_rational(self, f: Fraction | int) -> "ExactAlgExpr":
        fr = Fraction(f)
        if fr == 0 or self.is_zero():
            return ExactAlgExpr.zero()
        return ExactAlgExpr(self.dim_a, self.dim_pi, tuple((k, v * fr) for k, v in self.terms))

    def add(self, other: "ExactAlgExpr") -> "ExactAlgExpr":
        if self.is_zero():
            return other
        if other.is_zero():
            return self
        if self.dim_a != other.dim_a or self.dim_pi != other.dim_pi:
            raise ValueError(f"inhomogeneous dimension addition: a^{self.dim_a}*pi^{self.dim_pi} vs a^{other.dim_a}*pi^{other.dim_pi}")
        acc = self.as_dict()
        for k, v in other.terms:
            acc[k] = acc.get(k, Fraction(0)) + v
        return ExactAlgExpr.from_terms(self.dim_a, self.dim_pi, acc)

    def sub(self, other: "ExactAlgExpr") -> "ExactAlgExpr":
        return self.add(other.neg())

    def mul(self, other: "ExactAlgExpr") -> "ExactAlgExpr":
        if self.is_zero() or other.is_zero():
            return ExactAlgExpr.zero()
        acc: dict[int, Fraction] = {}
        for k1, v1 in self.terms:
            for k2, v2 in other.terms:
                prod = k1 * k2
                g = math.gcd(k1, k2)
                sqfree = (k1 // g) * (k2 // g)
                coeff = v1 * v2 * g
                # Sanity: prod == g*g*sqfree always holds when k1, k2 square-free
                assert prod == g * g * sqfree
                acc[sqfree] = acc.get(sqfree, Fraction(0)) + coeff
        return ExactAlgExpr.from_terms(self.dim_a + other.dim_a, self.dim_pi + other.dim_pi, acc)

    def div(self, other: "ExactAlgExpr") -> "ExactAlgExpr":
        if other.is_zero():
            raise ZeroDivisionError("division by zero")
        if self.is_zero():
            return ExactAlgExpr.zero()
        new_dim_a = self.dim_a - other.dim_a
        new_dim_pi = self.dim_pi - other.dim_pi
        if len(other.terms) == 1:
            k2, v2 = other.terms[0]
            # 1 / (v2 * sqrt(k2)) = sqrt(k2) / (v2 * k2)
            inv = ExactAlgExpr(0, 0, ((k2, Fraction(1) / (v2 * k2)),))
            res = self.mul(inv)
            return ExactAlgExpr(new_dim_a, new_dim_pi, res.terms)
        if len(other.terms) == 2:
            (k1, v1), (k2, v2) = other.terms
            conj = ExactAlgExpr(0, 0, ((k1, v1), (k2, -v2)))
            denom = Fraction(v1 * v1 * k1 - v2 * v2 * k2)
            if denom == 0:
                raise ZeroDivisionError("zero conjugate denominator")
            num = self.mul(conj).scale_rational(Fraction(1) / denom)
            return ExactAlgExpr(new_dim_a, new_dim_pi, num.terms)
        # Small multiquadratic linear solve in generated square-free closure
        basis = _closure_basis([k for k, _ in self.terms] + [k for k, _ in other.terms])
        if len(basis) > 8:
            raise ValueError("denominator radical field too large")
        idx = {b: i for i, b in enumerate(basis)}
        n = len(basis)
        mat = [[Fraction(0) for _ in range(n + 1)] for _ in range(n)]
        for j, bj in enumerate(basis):
            for ko, vo in other.terms:
                g = math.gcd(bj, ko)
                prod_k = (bj // g) * (ko // g)
                mat[idx[prod_k]][j] += vo * g
        for ks, vs in self.terms:
            mat[idx[ks]][n] += vs
        sol = _solve_linear_fraction(mat, n)
        out_terms = {basis[j]: sol[j] for j in range(n) if sol[j] != 0}
        return ExactAlgExpr.from_terms(new_dim_a, new_dim_pi, out_terms)

    def pow_int(self, exp: int) -> "ExactAlgExpr":
        if exp < 0 or exp > 6:
            raise ValueError(f"unsupported exponent: {exp}")
        res = ExactAlgExpr.from_rational(1)
        for _ in range(exp):
            res = res.mul(self)
        return res

    def sqrt_exact(self) -> "ExactAlgExpr":
        if self.dim_a != 0 or self.dim_pi != 0:
            if self.dim_a % 2 != 0 or self.dim_pi % 2 != 0:
                raise ValueError("fractional symbol exponent in sqrt")
        new_dim_a = self.dim_a // 2
        new_dim_pi = self.dim_pi // 2
        if self.is_zero():
            return ExactAlgExpr.zero()
        if len(self.terms) == 1:
            k, v = self.terms[0]
            if k != 1 or v < 0:
                raise ValueError("nested or negative sqrt unsupported")
            c_num, s_num = _sqfree_parts(v.numerator)
            c_den, s_den = _sqfree_parts(v.denominator)
            # sqrt(num/den) = c_num/(c_den*s_den) * sqrt(s_num*s_den)
            c_tot, sqfree = _sqfree_parts(s_num * s_den)
            coeff = Fraction(c_num * c_tot, c_den * s_den)
            return ExactAlgExpr.from_terms(new_dim_a, new_dim_pi, {sqfree: coeff})
        # Check exact nested denesting sqrt(A + B*sqrt(k)) where A^2 - k*B^2 is rational square (e.g. 15°/75°: (2±√3)/4)
        if len(self.terms) == 2 and self.terms[0][0] == 1:
            a_val = self.terms[0][1]
            k_val, b_val = self.terms[1]
            disc = a_val * a_val - b_val * b_val * k_val
            if a_val > 0 and disc >= 0:
                # disc = p/q rational square?
                cn, sn = _sqfree_parts(disc.numerator)
                cd, sd = _sqfree_parts(disc.denominator)
                if sn == 1 and sd == 1:
                    d_rat = Fraction(cn, cd)
                    # sqrt(a ± b√k) = sqrt((a + d)/2) ± sign(b)*sqrt((a - d)/2)
                    u2 = (a_val + d_rat) / 2
                    v2 = (a_val - d_rat) / 2
                    if u2 >= 0 and v2 >= 0:
                        u_expr = ExactAlgExpr.from_rational(u2).sqrt_exact()
                        v_expr = ExactAlgExpr.from_rational(v2).sqrt_exact()
                        combined = u_expr.add(v_expr if b_val >= 0 else v_expr.neg())
                        return ExactAlgExpr(new_dim_a, new_dim_pi, combined.terms)
        raise ValueError(f"unsupported sqrt operand: {self.canonical_str()}")

    def exact_sign(self) -> int:
        """Exact sign (-1, 0, +1) assuming positive symbolic bases `a > 0, pi > 0`."""
        if not self.terms:
            return 0
        if len(self.terms) == 1:
            return 1 if self.terms[0][1] > 0 else -1
        # Exact high-precision integer floor bounding with bisection on common denominator
        # Since all terms are rational * sqrt(int), refine rational interval with 80 bits -> guaranteed exact separation for THPT expressions;
        # for 2 terms (c1√k1 + c2√k2), use algebraic sign test: no float or approximation!
        if len(self.terms) == 2:
            (k1, c1), (k2, c2) = self.terms
            if (c1 > 0 and c2 > 0) or (c1 < 0 and c2 < 0):
                return 1 if c1 > 0 else -1
            # Opposite signs: compare c1^2 * k1 vs c2^2 * k2
            s1 = c1 * c1 * k1
            s2 = c2 * c2 * k2
            if s1 == s2:
                return 0
            return (1 if c1 > 0 else -1) if s1 > s2 else (1 if c2 > 0 else -1)
        # Integer scaled isqrt bounding: scale so coeffs integer; iterate precision P bits until interval strictly excludes 0
        lcd = 1
        for _, c in self.terms:
            lcd = math.lcm(lcd, c.denominator)
        scaled = [(k, int(c * lcd)) for k, c in self.terms]
        bits = 64
        while bits <= 512:
            scale = 1 << bits
            lo_sum = 0
            hi_sum = 0
            for k, ic in scaled:
                r_lo = math.isqrt(k * (1 << (2 * bits)))
                r_hi = r_lo if r_lo * r_lo == k * (1 << (2 * bits)) else r_lo + 1
                if ic >= 0:
                    lo_sum += ic * r_lo
                    hi_sum += ic * r_hi
                else:
                    lo_sum += ic * r_hi
                    hi_sum += ic * r_lo
            if lo_sum > 0:
                return 1
            if hi_sum < 0:
                return -1
            if lo_sum == 0 and hi_sum == 0:
                return 0
            bits *= 2
        raise ValueError("cannot separate radical sum sign within 512 bits")

    def cmp_rational(self, target: Fraction | int) -> int:
        diff = ExactAlgExpr(0, 0, self.terms).sub(ExactAlgExpr.from_rational(target))
        return diff.exact_sign()

    def canonical_str(self) -> str:
        if not self.terms:
            return "0"
        pieces = []
        for idx, (k, v) in enumerate(self.terms):
            sign = "-" if v < 0 else ("+" if idx > 0 else "")
            av = abs(v)
            num, den = av.numerator, av.denominator
            body = ""
            if num != 1 or (k == 1 and den == 1):
                body += str(num)
            if k != 1:
                body += f"√{k}"
            if den != 1:
                body = f"{body or '1'}/{den}"
            pieces.append(f"{sign}{body}")
        s = "".join(pieces)
        if len(self.terms) > 1 and (self.dim_a != 0 or self.dim_pi != 0):
            s = f"({s})"
        if self.dim_pi == 1:
            s = f"{s}π" if s != "1" else "π"
        elif self.dim_pi != 0:
            s = f"{s}*π^{self.dim_pi}"
        if self.dim_a == 1:
            s = f"{s}a" if s != "1" else "a"
        elif self.dim_a > 1:
            sup = {2: "²", 3: "³"}.get(self.dim_a, f"^{self.dim_a}")
            s = f"{s}a{sup}" if s != "1" else f"a{sup}"
        elif self.dim_a < 0:
            s = f"{s}*a^{self.dim_a}"
        return s


def _closure_basis(keys: list[int]) -> list[int]:
    basis = {1}
    for k in keys:
        cur = set(basis)
        for b in cur:
            g = math.gcd(b, k)
            basis.add((b // g) * (k // g))
    return sorted(basis)


def _solve_linear_fraction(mat: list[list[Fraction]], n: int) -> list[Fraction]:
    a = [row[:] for row in mat]
    for col in range(n):
        piv = None
        for r in range(col, n):
            if a[r][col] != 0:
                piv = r
                break
        if piv is None:
            raise ZeroDivisionError("singular denominator system")
        a[col], a[piv] = a[piv], a[col]
        inv = Fraction(1) / a[col][col]
        for j in range(col, n + 1):
            a[col][j] *= inv
        for r in range(n):
            if r != col and a[r][col] != 0:
                f = a[r][col]
                for j in range(col, n + 1):
                    a[r][j] -= f * a[col][j]
    return [a[i][n] for i in range(n)]


# ── Lexer / Recursive-Descent Parser for Vietnamese Geometry Answers ─────────

_TOKEN_RE = re.compile(
    r"""
    (?P<WS>\s+)
  | (?P<FRAC>\\frac\b)
  | (?P<SQRT_TEX>\\sqrt\b)
  | (?P<SQRT_WORD>sqrt\b)
  | (?P<PI_TEX>\\pi\b)
  | (?P<NUM>\d+(?:[.,]\d+)?)
  | (?P<SQRT>√)
  | (?P<PI>π)
  | (?P<VAR>a)
  | (?P<OP>[+\-*/^()])
  | (?P<BRACE>[{}])
    """,
    re.VERBOSE,
)


def _preprocess_latex(text: str) -> str:
    s = text.strip().translate(_SUPERSCRIPT_MAP)
    s = s.replace("$", "")
    return s


class _ExprParser:
    def __init__(self, text: str) -> None:
        self.tokens: list[tuple[str, str]] = []
        pos = 0
        n = len(text)
        while pos < n:
            m = _TOKEN_RE.match(text, pos)
            if not m:
                raise ValueError(f"unexpected character {text[pos]!r} at {pos} in {text!r}")
            kind = m.lastgroup
            assert kind is not None
            if kind != "WS":
                val = m.group(kind)
                if kind == "SQRT_WORD" or kind == "SQRT_TEX":
                    kind = "SQRT"
                elif kind == "PI_TEX":
                    kind = "PI"
                self.tokens.append((kind, val))
            pos = m.end()
        if not self.tokens:
            raise ValueError("empty expression")
        self.pos = 0

    def peek(self) -> tuple[str, str] | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def eat(self, expected_kind: str | None = None, expected_val: str | None = None) -> tuple[str, str]:
        tok = self.peek()
        if tok is None:
            raise ValueError("unexpected end of expression")
        if expected_kind is not None and tok[0] != expected_kind:
            raise ValueError(f"expected {expected_kind}, got {tok}")
        if expected_val is not None and tok[1] != expected_val:
            raise ValueError(f"expected {expected_val!r}, got {tok}")
        self.pos += 1
        return tok

    def parse(self) -> ExactAlgExpr:
        val = self.parse_expr()
        if self.peek() is not None:
            raise ValueError(f"trailing token {self.peek()}")
        return val

    def parse_expr(self) -> ExactAlgExpr:
        val = self.parse_term()
        while (tok := self.peek()) is not None and tok[0] == "OP" and tok[1] in ("+", "-"):
            self.eat()
            rhs = self.parse_term()
            val = val.add(rhs) if tok[1] == "+" else val.sub(rhs)
        return val

    def parse_term(self) -> ExactAlgExpr:
        val = self.parse_unary()
        while (tok := self.peek()) is not None:
            if tok[0] == "OP" and tok[1] in ("*", "/"):
                self.eat()
                rhs = self.parse_unary()
                val = val.mul(rhs) if tok[1] == "*" else val.div(rhs)
            elif self._starts_implicit_factor(tok):
                rhs = self.parse_power()
                val = val.mul(rhs)
            else:
                break
        return val

    def _starts_implicit_factor(self, tok: tuple[str, str]) -> bool:
        kind, val = tok
        if kind in ("NUM", "SQRT", "PI", "VAR", "FRAC"):
            return True
        if kind == "OP" and val == "(":
            return True
        return False

    def parse_unary(self) -> ExactAlgExpr:
        tok = self.peek()
        if tok is not None and tok[0] == "OP" and tok[1] in ("+", "-"):
            self.eat()
            sub = self.parse_unary()
            return sub.neg() if tok[1] == "-" else sub
        return self.parse_power()

    def parse_power(self) -> ExactAlgExpr:
        base = self.parse_primary()
        if (tok := self.peek()) is not None and tok[0] == "OP" and tok[1] == "^":
            self.eat()
            if (nxt := self.peek()) is not None and nxt[0] == "BRACE" and nxt[1] == "{":
                self.eat("BRACE", "{")
                exp_tok = self.eat("NUM")
                self.eat("BRACE", "}")
            elif nxt is not None and nxt[0] == "OP" and nxt[1] == "(":
                self.eat("OP", "(")
                exp_tok = self.eat("NUM")
                self.eat("OP", ")")
            else:
                exp_tok = self.eat("NUM")
            if "." in exp_tok[1] or "," in exp_tok[1]:
                raise ValueError("non-integer exponent unsupported")
            return base.pow_int(int(exp_tok[1]))
        return base

    def parse_primary(self) -> ExactAlgExpr:
        tok = self.peek()
        if tok is None:
            raise ValueError("unexpected end of expression")
        kind, val = tok
        if kind == "NUM":
            self.eat()
            norm = val.replace(",", ".")
            return ExactAlgExpr.from_rational(Fraction(norm))
        if kind == "VAR":
            self.eat()
            return ExactAlgExpr.from_rational(1, dim_a=1)
        if kind == "PI":
            self.eat()
            return ExactAlgExpr.from_rational(1, dim_pi=1)
        if kind == "FRAC":
            self.eat()
            self.eat("BRACE", "{")
            num = self.parse_expr()
            self.eat("BRACE", "}")
            self.eat("BRACE", "{")
            den = self.parse_expr()
            self.eat("BRACE", "}")
            return num.div(den)
        if kind == "SQRT":
            self.eat()
            nxt = self.peek()
            if nxt is not None and nxt[0] == "BRACE" and nxt[1] == "{":
                self.eat("BRACE", "{")
                inner = self.parse_expr()
                self.eat("BRACE", "}")
                return inner.sqrt_exact()
            if nxt is not None and nxt[0] == "OP" and nxt[1] == "(":
                self.eat("OP", "(")
                inner = self.parse_expr()
                self.eat("OP", ")")
                return inner.sqrt_exact()
            if nxt is not None and nxt[0] == "NUM":
                num_tok = self.eat("NUM")
                inner = ExactAlgExpr.from_rational(Fraction(num_tok[1].replace(",", ".")))
                return inner.sqrt_exact()
            raise ValueError(f"invalid √ operand: {nxt}")
        if kind == "OP" and val == "(":
            self.eat("OP", "(")
            inner = self.parse_expr()
            self.eat("OP", ")")
            return inner
        raise ValueError(f"unexpected token in primary: {tok}")


@dataclass(frozen=True)
class ParsedAnswer:
    kind: str  # SCALAR_OR_DIMENSIONAL | ANGLE_DEG | ANGLE_RAD | TRIG_*
    expr: ExactAlgExpr
    metric_unit: str | None = None
    metric_dim_exp: int = 0
    metric_scale_to_m: Fraction | None = None
    lhs_label: str | None = None


def parse_typed_answer(raw: Any) -> ParsedAnswer:
    """Parse any exact geometry answer into a typed `ParsedAnswer`. Raises ValueError if unparseable."""
    if raw is None or isinstance(raw, bool):
        raise ValueError(f"empty or boolean answer: {raw!r}")
    s = str(raw).strip()
    if not s:
        raise ValueError("empty string")
    s_clean = s.rstrip(".").strip()
    # Disallow obvious non-exact / malformed phrases
    low = s_clean.lower()
    if low in ("nan", "inf", "-inf", "infinity", "none", "null", "unknown"):
        raise ValueError(f"invalid literal: {s!r}")

    # 1. Check TRIG_COS_2X first: cos(2x)=..., cos(2α)=..., cos2x=...
    m_2x = re.fullmatch(
        r"\\?(?:cos)\s*(?:\(\s*2\s*[a-zα-ωφθ]\s*\)|2\s*[a-zα-ωφθ])\s*=\s*(.+)",
        s_clean,
        re.IGNORECASE,
    )
    if m_2x:
        expr = _ExprParser(_preprocess_latex(m_2x.group(1))).parse()
        if expr.dim_a != 0 or expr.dim_pi != 0:
            raise ValueError("dimensional symbol inside trig value")
        if expr.cmp_rational(-1) < 0 or expr.cmp_rational(1) > 0:
            raise ValueError(f"cos(2x) out of [-1, 1]: {s!r}")
        return ParsedAnswer("TRIG_COS_2X", expr)

    # 2. Check other trig forms: cos²=..., cos^2(x)=..., sin=..., sin²=..., tan=..., tan²=..., cot=...
    m_trig = re.fullmatch(
        r"\\?(cos|sin|tan|tg|cot|cotg)\s*(²|\^\s*2|\^\s*\{\s*2\s*\})?(?:\s*\(\s*[a-zα-ωφθ]+\s*\)|\s+[a-zα-ωφθ])?\s*=\s*(.+)",
        s_clean,
        re.IGNORECASE,
    )
    if m_trig:
        fn = m_trig.group(1).lower()
        sq = "^2" if m_trig.group(2) else ""
        kind = _TRIG_KIND_MAP[f"{fn}{sq}"]
        expr = _ExprParser(_preprocess_latex(m_trig.group(3))).parse()
        if expr.dim_a != 0 or expr.dim_pi != 0:
            raise ValueError("dimensional symbol inside trig value")
        if kind in ("TRIG_COS2", "TRIG_SIN2", "TRIG_TAN2", "TRIG_COT2") and expr.exact_sign() < 0:
            raise ValueError(f"negative squared trig value: {s!r}")
        if kind in ("TRIG_COS2", "TRIG_SIN2") and expr.cmp_rational(1) > 0:
            raise ValueError(f"squared sin/cos > 1: {s!r}")
        if kind in ("TRIG_COS", "TRIG_SIN") and (expr.cmp_rational(-1) < 0 or expr.cmp_rational(1) > 0):
            raise ValueError(f"sin/cos out of [-1, 1]: {s!r}")
        return ParsedAnswer(kind, expr)

    # Reject trig expression without '=' (e.g. "cos² 1/2" or "cos(45)") — don't guess malformed trig
    if re.search(r"\b(cos|sin|tan|cot|cotg|tg)\b", low):
        raise ValueError(f"malformed trig expression: {s!r}")

    # 3. Angle in degrees or radians
    m_deg = re.fullmatch(r"(.+?)\s*(?:°|độ)\s*", s_clean, re.IGNORECASE)
    if m_deg:
        expr = _ExprParser(_preprocess_latex(m_deg.group(1))).parse()
        if expr.dim_a != 0 or expr.dim_pi != 0:
            raise ValueError("dimensional symbol in angle degrees")
        if expr.cmp_rational(0) < 0 or expr.cmp_rational(360) > 0:
            raise ValueError(f"angle degrees out of [0, 360]: {s!r}")
        return ParsedAnswer("ANGLE_DEG", expr)

    m_rad = re.fullmatch(r"(.+?)\s*rad(?:ian)?s?\s*", s_clean, re.IGNORECASE)
    if m_rad:
        expr = _ExprParser(_preprocess_latex(m_rad.group(1))).parse()
        if expr.dim_a != 0:
            raise ValueError("a symbol in radian angle")
        # Must be a pi multiple or zero
        if not expr.is_zero() and expr.dim_pi != 1:
            raise ValueError("unsupported non-pi exact radian expression")
        deg_expr = ExactAlgExpr(0, 0, expr.terms).scale_rational(180)
        return ParsedAnswer("ANGLE_DEG", deg_expr)

    # 4. Strip optional non-trig LHS label like "V = ...", "S = ...", "d = ...", "h = ..."
    lhs_label: str | None = None
    body = s_clean
    m_lhs = re.fullmatch(r"([A-Za-z][A-Za-z0-9_']*)\s*=\s*(.+)", s_clean)
    if m_lhs:
        lhs_label = m_lhs.group(1)
        body = m_lhs.group(2).strip()

    # 5. Strip optional trailing measurement units (`cm`, `cm²`, `dm³`, `đvtt`, ...)
    metric_unit: str | None = None
    metric_dim_exp = 0
    metric_scale_to_m: Fraction | None = None
    m_vunit = re.fullmatch(r"(.+?)\s*(đvđd|đvdt|đvtt)\s*", body, re.IGNORECASE)
    if m_vunit:
        body = m_vunit.group(1).strip()
        u_low = m_vunit.group(2).lower()
        metric_unit = u_low
        metric_dim_exp = {"đvđd": 1, "đvdt": 2, "đvtt": 3}[u_low]
    else:
        m_mu = _METRIC_UNIT_RE.fullmatch(body)
        if m_mu:
            body = m_mu.group(1).strip()
            base_u = m_mu.group(2).lower()
            pow_s = m_mu.group(3) or ({"²": "2", "³": "3"}.get(m_mu.group(4) or "", "1"))
            exp_i = int(pow_s)
            metric_unit = base_u + ({1: "", 2: "²", 3: "³"}[exp_i])
            metric_dim_exp = exp_i
            metric_scale_to_m = _UNIT_SCALE_NUM[base_u] ** exp_i

    # Guard leading/trailing trailing-`a` after fraction like `2√5/5a` or `√21/7 a` vs `3a√22/22`
    # Notice `2√5/5 a` is already tokenized as `(2*√5 / 5) * a` by standard operator precedence `/` > implicit `*`?
    # Wait! In our parser, `/` and implicit `*` are at the same precedence level `parse_term()`, evaluated left-to-right!
    # Check `"2√5/5 a"`: `parse_term()` reads `2*√5`, divides by `5`, then multiplies by `a` -> `(2√5/5)*a`!
    # What about `"3a√22/22"`? Reads `3*a*√22`, divides by `22` -> `(3a√22)/22`!
    # What about `"1/2a"` or `"1/2 a"` vs `"3/(2a)"`? Check denominator edge case: `"2a/√22"` -> `(2a)/√22`, `"a/(2√2)"` -> `a/(2√2)`!
    # Wait: what about Axo / textbook shorthand like `"a²/2a"` (rare) vs `"√21a/7"`? In left-to-right `parse_term()`, `√21a` multiplies before `/7`, while `2√5/5a` divides `/5` then `*a`, BOTH matching human textbook precedence!
    expr = _ExprParser(_preprocess_latex(body)).parse()
    return ParsedAnswer(
        kind="SCALAR_OR_DIMENSIONAL",
        expr=expr,
        metric_unit=metric_unit,
        metric_dim_exp=metric_dim_exp,
        metric_scale_to_m=metric_scale_to_m,
        lhs_label=lhs_label,
    )


def _to_acute_angle_rep(p: ParsedAnswer, *, allow_obtuse: bool = False) -> tuple[ExactAlgExpr, int]:
    """Convert an angle or trig `ParsedAnswer` to canonical `(cos_squared, cos_sign)`.

    `cos_sign` is `+1`, `0`, or `-1`. Raises ValueError if out of domain or unconvertible.
    """
    if p.kind == "ANGLE_DEG":
        deg_q = p.expr.is_rational_pure()
        if deg_q is None:
            raise ValueError("non-rational degree value unsupported")
        if deg_q < 0 or deg_q > (180 if allow_obtuse else 90):
            raise ValueError(f"angle degree {deg_q}° out of acute/oriented domain")
        if deg_q in _SPECIAL_ANGLE_COS2:
            return ExactAlgExpr.from_rational(_SPECIAL_ANGLE_COS2[deg_q]), (0 if deg_q == 90 else 1)
        if allow_obtuse and (180 - deg_q) in _SPECIAL_ANGLE_COS2:
            return ExactAlgExpr.from_rational(_SPECIAL_ANGLE_COS2[180 - deg_q]), -1
        if deg_q == 15:
            # cos²(15°) = (2 + √3)/4
            return ExactAlgExpr.from_terms(0, 0, {1: Fraction(1, 2), 3: Fraction(1, 4)}), 1
        if deg_q == 75:
            return ExactAlgExpr.from_terms(0, 0, {1: Fraction(1, 2), 3: Fraction(-1, 4)}), 1
        raise ValueError(f"angle {deg_q}° has no closed-form quadratic radical cos²")
    if p.kind == "TRIG_COS2":
        sgn = 0 if p.expr.is_zero() else 1
        return p.expr, sgn
    if p.kind == "TRIG_COS":
        sgn = p.expr.exact_sign()
        if not allow_obtuse and sgn < 0:
            raise ValueError("negative cos incompatible with acute angle [0°, 90°]")
        return p.expr.mul(p.expr), sgn
    if p.kind == "TRIG_SIN2":
        cos2 = ExactAlgExpr.from_rational(1).sub(p.expr)
        return cos2, (0 if cos2.is_zero() else 1)
    if p.kind == "TRIG_SIN":
        if p.expr.exact_sign() < 0:
            raise ValueError("negative sin out of [0°, 180°]")
        cos2 = ExactAlgExpr.from_rational(1).sub(p.expr.mul(p.expr))
        return cos2, (0 if cos2.is_zero() else 1)
    if p.kind == "TRIG_TAN2":
        denom = ExactAlgExpr.from_rational(1).add(p.expr)
        cos2 = ExactAlgExpr.from_rational(1).div(denom)
        return cos2, 1
    if p.kind == "TRIG_TAN":
        sgn = p.expr.exact_sign()
        if not allow_obtuse and sgn < 0:
            raise ValueError("negative tan incompatible with acute angle")
        t2 = p.expr.mul(p.expr)
        cos2 = ExactAlgExpr.from_rational(1).div(ExactAlgExpr.from_rational(1).add(t2))
        return cos2, sgn
    if p.kind == "TRIG_COT2":
        denom = ExactAlgExpr.from_rational(1).add(p.expr)
        cos2 = p.expr.div(denom)
        return cos2, (0 if cos2.is_zero() else 1)
    if p.kind == "TRIG_COT":
        sgn = p.expr.exact_sign()
        if not allow_obtuse and sgn < 0:
            raise ValueError("negative cot incompatible with acute angle")
        c2 = p.expr.mul(p.expr)
        cos2 = c2.div(ExactAlgExpr.from_rational(1).add(c2))
        return cos2, (0 if cos2.is_zero() else sgn)
    if p.kind == "TRIG_COS_2X":
        # cos²(x) = (1 + cos(2x)) / 2
        cos2 = ExactAlgExpr.from_rational(1).add(p.expr).scale_rational(Fraction(1, 2))
        sgn = 0 if cos2.is_zero() else 1
        return cos2, sgn
    raise ValueError(f"cannot convert kind {p.kind} to angle representation")


@dataclass(frozen=True)
class MathComparisonResult:
    matched: bool | None
    verdict_code: str
    actual_kind: str | None
    oracle_kind: str | None
    canonical_actual: str | None
    canonical_oracle: str | None
    reason: str


def compare_math_expressions(actual: Any, oracle: Any, *, goal_kind: str | None = None) -> MathComparisonResult:
    """Compare two geometric answer strings with full symbolic & semantic typing."""
    if goal_kind is not None and goal_kind not in VALID_GOAL_KINDS:
        raise ValueError(f"unsupported goal_kind: {goal_kind!r}")

    try:
        pa = parse_typed_answer(actual)
    except (ValueError, ZeroDivisionError) as exc:
        return MathComparisonResult(None, "UNPARSEABLE_ACTUAL", None, None, None, None, str(exc))

    try:
        po = parse_typed_answer(oracle)
    except (ValueError, ZeroDivisionError) as exc:
        return MathComparisonResult(None, "UNPARSEABLE_ORACLE", pa.kind, None, pa.expr.canonical_str(), None, str(exc))

    a_can = pa.expr.canonical_str()
    o_can = po.expr.canonical_str()

    # 1. Explicit scalar trig-function goal (e.g. goal asks specifically for cos(phi) or cos²(phi) or cos(2phi))
    if goal_kind in _GOAL_TO_TRIG_KIND:
        req_trig = _GOAL_TO_TRIG_KIND[goal_kind]
        if pa.kind != req_trig and pa.kind != "SCALAR_OR_DIMENSIONAL":
            return MathComparisonResult(
                False, "MISMATCH_WRONG_TRIG_FUNCTION", pa.kind, po.kind, a_can, o_can,
                f"actual kind {pa.kind} conflicts with requested goal {goal_kind} ({req_trig})",
            )
        if po.kind != req_trig and po.kind != "SCALAR_OR_DIMENSIONAL":
            return MathComparisonResult(
                False, "MISMATCH_WRONG_TRIG_FUNCTION", pa.kind, po.kind, a_can, o_can,
                f"oracle kind {po.kind} conflicts with requested goal {goal_kind} ({req_trig})",
            )
        eq = pa.expr == po.expr
        return MathComparisonResult(
            eq,
            "EXACT_EQUIVALENT_EXPLICIT_TRIG_GOAL" if eq else "MISMATCH_VALUE",
            pa.kind,
            po.kind,
            a_can,
            o_can,
            "exact trig goal value comparison",
        )

    # 2. Non-angle / non-trig goals (`length`, `area`, `volume`, `ratio`)
    if goal_kind in ("length", "area", "volume", "ratio"):
        if pa.kind != "SCALAR_OR_DIMENSIONAL" or po.kind != "SCALAR_OR_DIMENSIONAL":
            return MathComparisonResult(
                False, "MISMATCH_GOAL_KIND", pa.kind, po.kind, a_can, o_can,
                f"angle/trig answer not valid for goal_kind={goal_kind}",
            )
        expected_dim = {"length": 1, "area": 2, "volume": 3, "ratio": 0}[goal_kind]
        if pa.expr.dim_a != po.expr.dim_a or pa.expr.dim_pi != po.expr.dim_pi:
            return MathComparisonResult(
                False, "MISMATCH_DIMENSION_POWER", pa.kind, po.kind, a_can, o_can,
                f"dimension exponent mismatch: a^{pa.expr.dim_a}*pi^{pa.expr.dim_pi} vs a^{po.expr.dim_a}*pi^{po.expr.dim_pi}",
            )
        if (pa.expr.dim_a != 0 and pa.expr.dim_a != expected_dim) or (pa.metric_dim_exp and pa.metric_dim_exp != expected_dim):
            return MathComparisonResult(
                False, "MISMATCH_GOAL_DIMENSION", pa.kind, po.kind, a_can, o_can,
                f"actual dimension does not match {goal_kind} (expected L^{expected_dim})",
            )
        if pa.metric_scale_to_m is not None and po.metric_scale_to_m is not None:
            if pa.metric_dim_exp != po.metric_dim_exp:
                return MathComparisonResult(False, "MISMATCH_UNIT_DIMENSION", pa.kind, po.kind, a_can, o_can, "unit dimension mismatch")
            ea = pa.expr.scale_rational(pa.metric_scale_to_m)
            eo = po.expr.scale_rational(po.metric_scale_to_m)
            eq = ea == eo
            return MathComparisonResult(eq, "EXACT_EQUIVALENT" if eq else "MISMATCH_VALUE", pa.kind, po.kind, a_can, o_can, "metric-normalized comparison")
        if pa.lhs_label and po.lhs_label and pa.lhs_label.upper() in ("S", "V") and po.lhs_label.upper() in ("S", "V") and pa.lhs_label.upper() != po.lhs_label.upper():
            return MathComparisonResult(False, "MISMATCH_LHS_LABEL", pa.kind, po.kind, a_can, o_can, f"{pa.lhs_label} vs {po.lhs_label}")
        eq = pa.expr == po.expr
        return MathComparisonResult(eq, "EXACT_EQUIVALENT" if eq else "MISMATCH_VALUE", pa.kind, po.kind, a_can, o_can, "exact algebraic equality")

    # 3. Untagged (`goal_kind is None`) or Angle goals (`angle`, `angle_oriented`)
    a_is_scalar = pa.kind == "SCALAR_OR_DIMENSIONAL"
    o_is_scalar = po.kind == "SCALAR_OR_DIMENSIONAL"

    if goal_kind in ("angle", "angle_oriented"):
        if a_is_scalar or o_is_scalar:
            return MathComparisonResult(
                False, "MISMATCH_SCALAR_VS_ANGLE", pa.kind, po.kind, a_can, o_can,
                "untagged scalar cannot satisfy angle/trig goal without unit or trig prefix",
            )
    else:
        # Both must either be SCALAR_OR_DIMENSIONAL or both be angle/trig (NEVER conflate scalar `1/2` with `cos²=1/2`!)
        if a_is_scalar != o_is_scalar:
            return MathComparisonResult(
                False, "MISMATCH_SCALAR_VS_TRIG", pa.kind, po.kind, a_can, o_can,
                f"refusing to conflate {pa.kind} with {po.kind}",
            )

    if a_is_scalar and o_is_scalar:
        if pa.expr.dim_a != po.expr.dim_a or pa.expr.dim_pi != po.expr.dim_pi:
            return MathComparisonResult(
                False, "MISMATCH_DIMENSION_POWER", pa.kind, po.kind, a_can, o_can,
                f"a^{pa.expr.dim_a}*pi^{pa.expr.dim_pi} vs a^{po.expr.dim_a}*pi^{po.expr.dim_pi}",
            )
        if pa.metric_dim_exp and po.metric_dim_exp and pa.metric_dim_exp != po.metric_dim_exp:
            return MathComparisonResult(False, "MISMATCH_UNIT_DIMENSION", pa.kind, po.kind, a_can, o_can, "unit dimension mismatch")
        if pa.metric_scale_to_m is not None and po.metric_scale_to_m is not None:
            eq = pa.expr.scale_rational(pa.metric_scale_to_m) == po.expr.scale_rational(po.metric_scale_to_m)
            return MathComparisonResult(eq, "EXACT_EQUIVALENT" if eq else "MISMATCH_VALUE", pa.kind, po.kind, a_can, o_can, "metric-normalized comparison")
        eq = pa.expr == po.expr
        return MathComparisonResult(eq, "EXACT_EQUIVALENT" if eq else "MISMATCH_VALUE", pa.kind, po.kind, a_can, o_can, "exact algebraic equality")

    # Both are ANGLE / TRIG expressions!
    if pa.kind == po.kind:
        eq = pa.expr == po.expr
        return MathComparisonResult(
            eq,
            "EXACT_EQUIVALENT_SAME_KIND" if eq else "MISMATCH_ANGLE_VALUE",
            pa.kind,
            po.kind,
            a_can,
            o_can,
            f"exact {pa.kind} equality",
        )

    # Different trig/angle kinds (e.g., `cos²=1/2` vs `45°`, or `cos=1/2` vs `cos²=1/2`, or `cos(2x)=1/2` vs `cos²=1/2`):
    # Convert both to underlying canonical angle `(cos², sign)` and verify exact geometric equivalence.
    # Notice: `"cos=1/2"` (60°, cos²=1/4) != `"cos²=1/2"` (45°, cos²=1/2) -> False!
    # `"cos(2x)=0"` (45°, cos²=1/2) != `"cos²=0"` (90°, cos²=0) -> False!
    allow_obtuse = goal_kind == "angle_oriented"
    try:
        cos2_a, sgn_a = _to_acute_angle_rep(pa, allow_obtuse=allow_obtuse)
        cos2_o, sgn_o = _to_acute_angle_rep(po, allow_obtuse=allow_obtuse)
    except ValueError as exc:
        return MathComparisonResult(None, "UNCOMPARABLE_ANGLE_TRIG", pa.kind, po.kind, a_can, o_can, str(exc))

    # Ambiguous oriented case: e.g., `cos²=1/4` vs `120°` (cos=-1/2): `cos²` loses obtuse quadrant information -> False!
    if allow_obtuse and (sgn_o < 0 or sgn_a < 0) and (pa.kind.endswith("2") or po.kind.endswith("2") or pa.kind == "TRIG_COS_2X" or po.kind == "TRIG_COS_2X"):
        return MathComparisonResult(
            False, "MISMATCH_SIGN_LOST_IN_SQUARED_TRIG", pa.kind, po.kind, a_can, o_can,
            "squared trig expression cannot verify obtuse angle > 90°",
        )

    if cos2_a == cos2_o and sgn_a == sgn_o:
        return MathComparisonResult(
            True, "EXACT_EQUIVALENT_ANGLE_TRIG", pa.kind, po.kind, a_can, o_can,
            f"equivalent angle across {pa.kind} <-> {po.kind} (cos²={cos2_a.canonical_str()})",
        )
    code = "MISMATCH_WRONG_TRIG_FUNCTION" if (pa.expr == po.expr and pa.kind != po.kind) else "MISMATCH_ANGLE_VALUE"
    return MathComparisonResult(
        False, code, pa.kind, po.kind, a_can, o_can,
        f"unequal angle: {pa.kind} ({cos2_a.canonical_str()}) vs {po.kind} ({cos2_o.canonical_str()})",
    )


def same_value_v2(actual: Any, oracle: Any, *, goal_kind: str | None = None) -> bool | None:
    """Drop-in exact replacement for `EVI.same_value` / `nl_eval_scoring.same_value`."""
    return compare_math_expressions(actual, oracle, goal_kind=goal_kind).matched


def infer_goal_kind_from_text(text: str | None) -> str | None:
    """Infer goal quantity kind solely from the final question/goal clause (never premise clauses)."""
    if not text:
        return None
    sents = [s.strip() for s in re.split(r"[.?!\n]+", text) if s.strip()]
    goal_sent = sents[-1] if sents else text
    for s in reversed(sents):
        if re.search(r"\b(?:hãy\s+)?(?:tính|tìm|xác\s+định|hỏi)\b|\bbằng\s+(?:bao\s+nhiêu|mấy)\b", s, re.IGNORECASE):
            goal_sent = s
            break
    m = re.search(r"(?:hãy\s+)?(?:tính|tìm|xác\s+định)\s+(.+)$", goal_sent, re.IGNORECASE)
    clause = (m.group(1) if m else goal_sent).lower()
    if re.search(r"cos\s*(?:²|\^\s*2)", clause):
        return "trig_cos2"
    if re.search(r"\bcos\s*\(\s*2", clause):
        return "trig_cos_2x"
    if re.search(r"\bcos\b", clause):
        return "trig_cos"
    if re.search(r"sin\s*(?:²|\^\s*2)", clause):
        return "trig_sin2"
    if re.search(r"\bsin\b", clause):
        return "trig_sin"
    if re.search(r"tan\s*(?:²|\^\s*2)", clause):
        return "trig_tan2"
    if re.search(r"\btan\b|\btg\b", clause):
        return "trig_tan"
    if "tỉ số" in clause or "tỷ số" in clause:
        return "ratio"
    if "góc" in clause:
        return "angle"
    if "thể tích" in clause or re.search(r"\bv\b", clause):
        return "volume"
    if "diện tích" in clause:
        return "area"
    if "khoảng cách" in clause or "độ dài" in clause or re.search(r"\bd\s*\(", clause):
        return "length"
    return None

