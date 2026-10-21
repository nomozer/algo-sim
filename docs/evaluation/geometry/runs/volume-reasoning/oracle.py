"""Independent mathematical oracle for Wave 3A (`volume-reasoning`).

Strictly zero imports from `app` or `tests`. Computes exact rational / quadratic-surd volumes,
dimensionless volume ratios, and residual volumes from first principles:
- Simson / homothety / base-area ratio identities for sub-pyramids and prisms.
- Independent 3D affine coordinate + Gram matrix determinant calculation.
- Independent 3D Separating Axis Theorem (SAT) and outward half-space containment check.
"""
from __future__ import annotations

from fractions import Fraction as F
from math import gcd, isqrt
from typing import Any


def _radical_norm(coeff: F, rad: int) -> tuple[F, int]:
    """Normalize `coeff * sqrt(rad)` with square-free integer `rad >= 1`."""
    if coeff == 0 or rad == 0:
        return F(0), 1
    if rad < 0:
        raise ValueError("Negative radicand in volume oracle")
    # Extract square factors from rad
    k = 1
    d = 2
    r = rad
    while d * d <= r:
        while r % (d * d) == 0:
            k *= d
            r //= d * d
        d += 1
    return coeff * k, r


def _format_surd(coeff: F, rad: int, symbolic_deg: int = 0) -> str:
    """Format `coeff * sqrt(rad) * a^symbolic_deg` in canonical AlgoSim display format."""
    coeff, rad = _radical_norm(coeff, rad)
    if coeff == 0:
        return "0"
    num = abs(coeff.numerator)
    den = coeff.denominator
    sign = "-" if coeff < 0 else ""
    sup = {2: "a²", 3: "a³"}
    sym = "" if symbolic_deg == 0 else ("a" if symbolic_deg == 1 else sup.get(symbolic_deg, f"a^{symbolic_deg}"))
    if rad == 1:
        if sym:
            head = sym if num == 1 else f"{num}{sym}"
        else:
            head = str(num)
    else:
        if sym:
            prefix = "" if num == 1 else str(num)
            head = f"{prefix}{sym}√{rad}"
        else:
            head = f"√{rad}" if num == 1 else f"{num}√{rad}"
    return f"{sign}{head}" if den == 1 else f"{sign}{head}/{den}"


def _sqrt_fraction(q: F) -> F:
    if q < 0:
        raise ValueError("Negative ratio squared")
    sn = isqrt(q.numerator)
    sd = isqrt(q.denominator)
    if sn * sn != q.numerator or sd * sd != q.denominator:
        raise ValueError(f"Irrational ratio: sqrt({q})")
    return F(sn, sd)


def _base_area_squared(base_kind: str, params: dict[str, Any]) -> F:
    """Independent Gram determinant / Euclidean base area squared."""
    if base_kind == "equilateral_triangle":
        s = F(params["side"])
        return F(3, 16) * (s ** 4)
    if base_kind == "right_triangle":
        a, b = F(params["leg_a"]), F(params["leg_b"])
        return F(1, 4) * (a ** 2) * (b ** 2)
    if base_kind == "square":
        s = F(params["side"])
        return s ** 4
    if base_kind == "rectangle":
        a, b = F(params["side_a"]), F(params["side_b"])
        return (a ** 2) * (b ** 2)
    raise ValueError(f"Unsupported oracle base_kind: {base_kind}")


def _root_volume_squared(spec: dict[str, Any]) -> F:
    area2 = _base_area_squared(spec["base_kind"], spec)
    h = F(spec["height"])
    if spec.get("root_kind", "pyramid") == "prism":
        return area2 * (h ** 2)
    return area2 * (h ** 2) / F(9)


def _surd_from_squared(v2: F) -> tuple[F, int]:
    """Convert `v^2 = num / den` (`v > 0`) to `(coeff, squarefree_rad)` such that `(coeff * sqrt(rad))^2 == v2`."""
    # v = sqrt(num * den) / den
    rad = v2.numerator * v2.denominator
    return _radical_norm(F(1, v2.denominator), rad)


def _dot3(u: tuple[F, F, F], v: tuple[F, F, F]) -> F:
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]


def _sub3(u: tuple[F, F, F], v: tuple[F, F, F]) -> tuple[F, F, F]:
    return (u[0] - v[0], u[1] - v[1], u[2] - v[2])


def _cross3(u: tuple[F, F, F], v: tuple[F, F, F]) -> tuple[F, F, F]:
    return (
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    )


def verify_3d_containment_and_disjointness(
    orig_pts: list[tuple[F, F, F]],
    orig_faces: list[tuple[int, int, int]],
    sub_solids: list[list[tuple[F, F, F]]],
) -> bool:
    """Independent 3D half-space containment and Separating Axis Theorem (SAT) verifier over Q^3."""
    # Outward half-spaces of original solid
    planes: list[tuple[tuple[F, F, F], F]] = []
    for i, j, k in orig_faces:
        p0, p1, p2 = orig_pts[i], orig_pts[j], orig_pts[k]
        n = _cross3(_sub3(p1, p0), _sub3(p2, p0))
        d = _dot3(n, p0)
        vals = [_dot3(n, q) - d for q in orig_pts]
        if min(vals) < 0 < max(vals):
            return False
        if max(vals) > 0:
            n = (-n[0], -n[1], -n[2])
            d = -d
        planes.append((n, d))

    # 1. Every subtracted vertex must lie inside all outward half-spaces of orig
    for sub in sub_solids:
        for pt in sub:
            if any(_dot3(n, pt) - d > 0 for n, d in planes):
                return False

    # 2. Pairwise interior disjointness via exact 3D SAT
    for a_idx in range(len(sub_solids)):
        for b_idx in range(a_idx + 1, len(sub_solids)):
            sa, sb = sub_solids[a_idx], sub_solids[b_idx]
            axes: list[tuple[F, F, F]] = []
            for poly in (sa, sb):
                for i in range(len(poly)):
                    for j in range(i + 1, len(poly)):
                        for k in range(j + 1, len(poly)):
                            n = _cross3(_sub3(poly[j], poly[i]), _sub3(poly[k], poly[i]))
                            if any(n):
                                axes.append(n)
            edges_a = [_sub3(sa[j], sa[i]) for i in range(len(sa)) for j in range(i + 1, len(sa))]
            edges_b = [_sub3(sb[j], sb[i]) for i in range(len(sb)) for j in range(i + 1, len(sb))]
            for ea in edges_a:
                for eb in edges_b:
                    n = _cross3(ea, eb)
                    if any(n):
                        axes.append(n)
            separated = False
            for ax in axes:
                va = [_dot3(ax, p) for p in sa]
                vb = [_dot3(ax, p) for p in sb]
                if max(va) <= min(vb) or max(vb) <= min(va):
                    separated = True
                    break
            if not separated:
                return False
    return True


def expected(case: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Compute independent oracle expectations `{goal_id: {'display': ..., 'squared': ...}}`."""
    spec = case["oracle"]
    root_v2 = _root_volume_squared(spec)
    root_coeff, root_rad = _surd_from_squared(root_v2)
    sym_deg = int(spec.get("symbolic_power", 0))

    solid_scales: dict[str, F] = {spec["root_solid"]: F(1)}
    for name, sc in spec.get("solid_scales", {}).items():
        solid_scales[name] = F(sc)

    out: dict[str, dict[str, str]] = {}
    for gid, gspec in spec["goals"].items():
        gkind = gspec["kind"]
        if gkind == "volume_ratio":
            num_scale = solid_scales[gspec["numerator"]]
            den_scale = solid_scales[gspec["denominator"]]
            ratio = num_scale / den_scale
            if ratio <= 0:
                raise ValueError(f"Non-positive volume ratio in {case['id']}")
            out[gid] = {
                "display": _format_surd(ratio, 1, 0),
                "squared": str(ratio ** 2),
            }
        elif gkind == "residual_volume":
            orig_scale = solid_scales[gspec["original"]]
            sub_scale_sum = sum(solid_scales[s] for s in gspec["subtracted"])
            res_scale = orig_scale - sub_scale_sum
            if res_scale <= 0:
                raise ValueError(f"Non-positive residual volume in {case['id']}")
            res_coeff = root_coeff * res_scale
            res_v2 = root_v2 * (res_scale ** 2)
            out[gid] = {
                "display": _format_surd(res_coeff, root_rad, 3 if sym_deg else 0),
                "squared": str(res_v2),
            }
        elif gkind == "volume":
            sc = solid_scales[gspec["solid"]]
            v_coeff = root_coeff * sc
            v2 = root_v2 * (sc ** 2)
            out[gid] = {
                "display": _format_surd(v_coeff, root_rad, 3 if sym_deg else 0),
                "squared": str(v2),
            }
        else:
            raise ValueError(f"Unsupported oracle goal kind: {gkind}")
    return out


def self_check() -> None:
    # 1. Equilateral pyramid S.ABC side=4, height=6 -> V(root) = 8√3 (V^2 = 192).
    # Midpoint section S.MNP has scale 1/8 -> ratio = 1/8, residual = 7√3 (V_res^2 = 147).
    sample = {
        "id": "self-check-1",
        "oracle": {
            "root_solid": "S.ABC",
            "root_kind": "pyramid",
            "base_kind": "equilateral_triangle",
            "side": "4",
            "height": "6",
            "solid_scales": {"S.MNP": "1/8"},
            "goals": {
                "q_ratio": {"kind": "volume_ratio", "numerator": "S.MNP", "denominator": "S.ABC"},
                "q_res": {"kind": "residual_volume", "original": "S.ABC", "subtracted": ["S.MNP"]},
            },
        },
    }
    res = expected(sample)
    assert res["q_ratio"] == {"display": "1/8", "squared": "1/64"}
    assert res["q_res"] == {"display": "7√3", "squared": "147"}

    # 2. 3D SAT & containment check on tetrahedron S(0,0,1), A(0,0,0), B(1,0,0), C(0,1,0)
    orig_pts = [(F(0), F(0), F(1)), (F(0), F(0), F(0)), (F(1), F(0), F(0)), (F(0), F(1), F(0))]
    orig_faces = [(1, 2, 3), (0, 1, 2), (0, 2, 3), (0, 3, 1)]
    m1 = (F(1, 3), F(0), F(0))
    m2 = (F(2, 3), F(0), F(0))
    # Disjoint wedges along AB: [0, 1/3] and [2/3, 1]
    sub_disjoint_1 = [orig_pts[0], orig_pts[1], m1, orig_pts[3]]
    sub_disjoint_2 = [orig_pts[0], m2, orig_pts[2], orig_pts[3]]
    assert verify_3d_containment_and_disjointness(orig_pts, orig_faces, [sub_disjoint_1, sub_disjoint_2]) is True
    # Overlapping wedges along AB: [0, 2/3] and [1/3, 1]
    sub_overlap_1 = [orig_pts[0], orig_pts[1], m2, orig_pts[3]]
    sub_overlap_2 = [orig_pts[0], m1, orig_pts[2], orig_pts[3]]
    assert verify_3d_containment_and_disjointness(orig_pts, orig_faces, [sub_overlap_1, sub_overlap_2]) is False


self_check()
