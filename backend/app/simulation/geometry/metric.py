# -*- coding: utf-8 -*-
"""Metric of the chart — the one place where "length" is defined for the kernel.

─── WHY (exact-dimensions, 2026-10-07) ─────────────────────────────────────

Points are ℚ³ (`exact.Vec3`). An equilateral triangle with rational vertices has side² = 2N, never a rational
square, so a regular triangular pyramid or tetrahedron with a RATIONAL edge has no Euclidean ℚ³ layout. Rather than
leave ℚ (irrational coordinates break every exact equality of the kernel), the layout is read as an AFFINE CHART and
lengths come from a rational Gram matrix G: |v|² = vᵀ G v.

─── WHY IT IS SOUND ───────────────────────────────────────────────────────

G symmetric positive definite ⇒ G = TᵀT for an invertible linear T. T maps the chart onto a Euclidean figure, and:

* affine facts (incidence, ratios, midpoints, intersections, centroids, sections, coplanarity, parallelism) are
  invariant under T — the kernel's affine operations need no metric;
* every metric quantity of the Euclidean figure equals the G-quantity of the chart: |Tv|² = vᵀGv;
  (Tu)·(Tv) = uᵀGv; a plane with covector n has unit-free normal G⁻¹n; |Tu × Tv|² = det G · cᵀG⁻¹c with c = u × v;
  volume scales by |det T| = √det G.

G is rational, so lengths², cos², areas², distances² stay in ℚ and their roots stay in `radical.py` (`a·√b`); only
the volume gains the factor √det G, also `a·√b`.

For four affinely independent chart points the six squared edge lengths fix G UNIQUELY (`gram_from_lengths`): with
eᵢ = Pᵢ − P₀ the Gram matrix of the basis is K = (eᵢ·eⱼ) from the polarisation identity, and G = E⁻ᵀ K E⁻¹. The six
lengths come from the problem text, never from the layout — so the layout cannot smuggle in a size.

─── SCOPE ─────────────────────────────────────────────────────────────────

One metric per program run, held in a context variable (`using`). Default None = the identity, and every helper
below then evaluates EXACTLY the expression the kernel used before — existing families stay byte-identical.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from fractions import Fraction
from typing import Iterator

from .exact import GeometryError, Vec3

#: The text's lengths do not describe a Euclidean simplex (G not positive definite), or the chart is flat.
ERR_KHONG_EUCLID = "METRIC_NOT_EUCLIDEAN"
#: A construction whose meaning needs the identity metric (curved solids) under an oblique chart.
ERR_CAN_EUCLID = "METRIC_REQUIRES_EUCLIDEAN_CHART"

_M3 = tuple[tuple[Fraction, Fraction, Fraction], tuple[Fraction, Fraction, Fraction],
            tuple[Fraction, Fraction, Fraction]]


def _det(m: _M3) -> Fraction:
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def _inv(m: _M3) -> _M3:
    d = _det(m)
    if d == 0:
        raise GeometryError(ERR_KHONG_EUCLID, "singular matrix")
    c = [[(m[(j + 1) % 3][(i + 1) % 3] * m[(j + 2) % 3][(i + 2) % 3]
           - m[(j + 1) % 3][(i + 2) % 3] * m[(j + 2) % 3][(i + 1) % 3]) / d for j in range(3)] for i in range(3)]
    return tuple(tuple(r) for r in c)  # type: ignore[return-value]


def _mul(a: _M3, b: _M3) -> _M3:
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))  # type: ignore


def _t(a: _M3) -> _M3:
    return tuple(tuple(a[j][i] for j in range(3)) for i in range(3))  # type: ignore[return-value]


def _ap(m: _M3, v: Vec3) -> Vec3:
    x = (v.x, v.y, v.z)
    return Vec3(*(sum(m[i][k] * x[k] for k in range(3)) for i in range(3)))


@dataclass(frozen=True)
class Metric:
    """Symmetric positive definite rational Gram matrix of the chart."""

    g: _M3

    @property
    def det(self) -> Fraction:
        return _det(self.g)

    def dot(self, u: Vec3, v: Vec3) -> Fraction:
        return _ap(self.g, v).dot(u)

    def vector(self, n: Vec3) -> Vec3:
        """Covector (plane normal as stored by `Plane3`) → the vector orthogonal to that plane: G⁻¹n."""
        return _ap(_inv(self.g), n)

    def covector(self, v: Vec3) -> Vec3:
        """Direction → covector of the plane orthogonal to it: G v."""
        return _ap(self.g, v)

    def as_json(self) -> list[list[str]]:
        return [[str(x) for x in r] for r in self.g]


_ACTIVE: ContextVar[Metric | None] = ContextVar("chart_metric", default=None)


@contextmanager
def using(m: Metric | None) -> Iterator[None]:
    """Run a program (and every check on it) in the chart metric `m`; None = identity."""
    tok = _ACTIVE.set(m)
    try:
        yield
    finally:
        _ACTIVE.reset(tok)


def require_euclidean(what: str) -> None:
    if _ACTIVE.get() is not None:
        raise GeometryError(ERR_CAN_EUCLID, f"{what} needs a Euclidean chart; this program's chart has a derived metric")


# ── kernel helpers: identity ⇒ the exact expression used before ─────────────────

def dot(u: Vec3, v: Vec3) -> Fraction:
    m = _ACTIVE.get()
    return u.dot(v) if m is None else m.dot(u, v)


def norm_sq(v: Vec3) -> Fraction:
    m = _ACTIVE.get()
    return v.norm_sq() if m is None else m.dot(v, v)


def normal_vector(n: Vec3) -> Vec3:
    """Plane covector → a vector orthogonal to the plane."""
    m = _ACTIVE.get()
    return n if m is None else m.vector(n)


def plane_covector(d: Vec3) -> Vec3:
    """Direction → covector of a plane orthogonal to it."""
    m = _ACTIVE.get()
    return d if m is None else m.covector(d)


def conorm_sq(n: Vec3) -> Fraction:
    """nᵀG⁻¹n — the squared length that turns a covector value into a distance."""
    m = _ACTIVE.get()
    return n.norm_sq() if m is None else n.dot(m.vector(n))


def area_sq_from_cross_sum(c: Vec3) -> Fraction:
    """|Σ Pᵢ × Pᵢ₊₁|² of a planar polygon, in the chart metric (det G · cᵀG⁻¹c)."""
    m = _ACTIVE.get()
    return c.dot(c) if m is None else m.det * c.dot(m.vector(c))


def volume_det_factor_sq() -> Fraction:
    """det G — the volume of a chart solid is |det|·√(det G)/6."""
    m = _ACTIVE.get()
    return Fraction(1) if m is None else m.det


# ── the metric from the text's lengths ─────────────────────────────────────────

def gram_from_lengths(points: tuple[Vec3, Vec3, Vec3, Vec3],
                      length_sq: dict[tuple[int, int], Fraction]) -> Metric:
    """THE metric in which the chart simplex `points` has the six squared edge lengths `length_sq` (keys (i, j),
    i < j). Raises when the chart is flat or the lengths are not those of a Euclidean tetrahedron."""
    p0 = points[0]
    e = [points[i] - p0 for i in (1, 2, 3)]
    E: _M3 = tuple(tuple(getattr(e[j], a) for j in range(3)) for a in "xyz")  # type: ignore[assignment]
    if _det(E) == 0:
        raise GeometryError(ERR_KHONG_EUCLID, "the four chart points are coplanar")

    def L(i: int, j: int) -> Fraction:
        return Fraction(length_sq[(min(i, j), max(i, j))])

    K: _M3 = tuple(tuple((L(0, i) + L(0, j) - (L(i, j) if i != j else 0)) / 2 for j in (1, 2, 3))
                   for i in (1, 2, 3))  # type: ignore[assignment]
    # positive definite ⇔ leading principal minors > 0 (Sylvester) — exact
    if not (K[0][0] > 0 and K[0][0] * K[1][1] - K[0][1] * K[1][0] > 0 and _det(K) > 0):
        raise GeometryError(ERR_KHONG_EUCLID, "the lengths do not form a Euclidean tetrahedron")
    Ei = _inv(E)
    G = _mul(_mul(_t(Ei), K), Ei)
    m = Metric(G)
    for (i, j), v in length_sq.items():                      # self-check: the six lengths hold exactly
        d = points[j] - points[i]
        if m.dot(d, d) != v:
            raise GeometryError(ERR_KHONG_EUCLID, f"metric check failed on edge {i}{j}")
    return m


def is_identity(m: Metric) -> bool:
    return all(m.g[i][j] == (1 if i == j else 0) for i in range(3) for j in range(3))
