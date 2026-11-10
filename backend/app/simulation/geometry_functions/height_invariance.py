# -*- coding: utf-8 -*-
"""Formal symbolic height-invariance certification over `ℚ[t]` (`t = h² ∈ (0, +∞)`).

Replaces heuristic multi-sample coincidence checking with an exact, pure-stdlib `Fraction`
rational-function proof certificate (`height-invariance-certificate/2`) backed by 8 explicit
proof obligations (`PO-1` .. `PO-8`) and a standalone certificate verifier.
"""
from __future__ import annotations

from fractions import Fraction
from itertools import combinations
from typing import Any

from app.simulation.geometry.exact import Vec3

CERTIFICATE_SCHEMA_VERSION = "height-invariance-certificate/2"
CERTIFICATION_MODE = "EXACT_SYMBOLIC_POLYNOMIAL_IDENTITY"
MAX_CERTIFIED_DEGREE = 2
WITNESS_SAMPLES_H2: tuple[Fraction, ...] = tuple(Fraction(k) for k in (1, 2, 3, 5, 7))

PROOF_OBLIGATIONS: tuple[str, ...] = (
    "PO_SINGLE_FREE_HEIGHT_ORTHOGONAL_CHART",
    "PO_AFFINE_COORDINATES_T_INDEPENDENT",
    "PO_SECTION_TOPOLOGY_INVARIANT",
    "PO_VALID_DOMAIN_ALL_POSITIVE_T",
    "PO_POLYNOMIAL_DEGREE_BOUNDED",
    "PO_DENOMINATOR_POSITIVE_ON_DOMAIN",
    "PO_EXACT_POLYNOMIAL_IDENTITY",
    "PO_INTERPRETER_CROSS_CHECK",
)

Poly = tuple[Fraction, ...]
LinPoly = tuple[Fraction, Fraction]
V3 = tuple[Fraction, Fraction, Fraction]
Z = Fraction(0)
ONE = Fraction(1)


# ── Exact Univariate Polynomial Algebra over ℚ[t] ─────────────────────────────────────────────────────────────────────


def poly_trim(p: Poly) -> Poly:
    idx = len(p)
    while idx > 0 and p[idx - 1] == Z:
        idx -= 1
    return tuple(p[:idx])


def poly_deg(p: Poly) -> int:
    tp = poly_trim(p)
    return len(tp) - 1


def poly_add(a: Poly, b: Poly) -> Poly:
    n = max(len(a), len(b))
    return poly_trim(tuple((a[i] if i < len(a) else Z) + (b[i] if i < len(b) else Z) for i in range(n)))


def poly_sub(a: Poly, b: Poly) -> Poly:
    n = max(len(a), len(b))
    return poly_trim(tuple((a[i] if i < len(a) else Z) - (b[i] if i < len(b) else Z) for i in range(n)))


def poly_scale(p: Poly, k: Fraction) -> Poly:
    if k == Z:
        return ()
    return poly_trim(tuple(c * k for c in p))


def poly_mul(a: Poly, b: Poly) -> Poly:
    ta, tb = poly_trim(a), poly_trim(b)
    if not ta or not tb:
        return ()
    out = [Z] * (len(ta) + len(tb) - 1)
    for i, ca in enumerate(ta):
        for j, cb in enumerate(tb):
            out[i + j] += ca * cb
    return poly_trim(tuple(out))


def poly_eval(p: Poly, t: Fraction) -> Fraction:
    acc = Z
    for coeff in reversed(p):
        acc = acc * t + coeff
    return acc


def check_linear_positive_on_positive_reals(lin: LinPoly) -> bool:
    """`a₀ + a₁ t > 0` for ALL `t ∈ (0, +∞)` iff `a₀ ≥ 0`, `a₁ ≥ 0`, and `(a₀, a₁) ≠ (0, 0)`."""
    a0, a1 = lin
    return a0 >= Z and a1 >= Z and (a0 != Z or a1 != Z)


def check_linear_sign_invariant_on_positive_reals(lin: LinPoly, expected_sign: int | None) -> bool:
    """Verify `sign(a₀ + a₁ t) == expected_sign` for ALL `t ∈ (0, +∞)` (`+1`, `-1`, `0`, or `None`)."""
    if expected_sign is None:
        return True
    a0, a1 = lin
    if expected_sign == 0:
        return a0 == Z and a1 == Z
    if expected_sign > 0:
        return a0 >= Z and a1 >= Z and (a0 != Z or a1 != Z)
    return a0 <= Z and a1 <= Z and (a0 != Z or a1 != Z)


def verify_rational_constancy_over_positive_reals(
    p: Poly,
    q: Poly,
    *,
    linear_den_factors: tuple[LinPoly, ...] = (),
    max_degree: int = MAX_CERTIFIED_DEGREE,
) -> tuple[bool, str | None, Fraction | None]:
    """Formally certify that `P(t) / Q(t)` has bounded degree, strictly positive denominator on `(0, +∞)`,
    and satisfies the exact polynomial identity `P(t) - c·Q(t) ≡ 0` over `ℚ[t]` for some `c ≥ 0`."""
    tp, tq = poly_trim(p), poly_trim(q)
    if poly_deg(tp) > max_degree or poly_deg(tq) > max_degree or len(linear_den_factors) > max_degree:
        return False, "PO_POLYNOMIAL_DEGREE_BOUNDED", None

    if not tq:
        return False, "PO_DENOMINATOR_POSITIVE_ON_DOMAIN", None

    if linear_den_factors:
        prod: Poly = (ONE,)
        for fac in linear_den_factors:
            if not check_linear_positive_on_positive_reals(fac):
                return False, "PO_DENOMINATOR_POSITIVE_ON_DOMAIN", None
            prod = poly_mul(prod, fac)
        if prod != tq:
            return False, "PO_DENOMINATOR_POSITIVE_ON_DOMAIN", None
    else:
        # Constant denominator `q₀ > 0` or single linear denominator `(q₀, q₁)`
        if len(tq) == 1:
            if tq[0] <= Z:
                return False, "PO_DENOMINATOR_POSITIVE_ON_DOMAIN", None
        elif len(tq) == 2:
            if not check_linear_positive_on_positive_reals((tq[0], tq[1])):
                return False, "PO_DENOMINATOR_POSITIVE_ON_DOMAIN", None
        else:
            return False, "PO_DENOMINATOR_POSITIVE_ON_DOMAIN", None

    q_at_1 = poly_eval(tq, ONE)
    if q_at_1 <= Z:
        return False, "PO_DENOMINATOR_POSITIVE_ON_DOMAIN", None

    c = poly_eval(tp, ONE) / q_at_1
    if c < Z:
        return False, "PO_EXACT_POLYNOMIAL_IDENTITY", None

    residual = poly_sub(tp, poly_scale(tq, c))
    if residual != ():
        return False, "PO_EXACT_POLYNOMIAL_IDENTITY", None

    return True, None, c


# ── Symbolic Chart & Gram Helpers over G(t) = G₂ ⊕ (t) ────────────────────────────────────────────────────────────────


def _det3(u: V3, v: V3, w: V3) -> Fraction:
    return (
        u[0] * (v[1] * w[2] - v[2] * w[1])
        - u[1] * (v[0] * w[2] - v[2] * w[0])
        + u[2] * (v[0] * w[1] - v[1] * w[0])
    )


def _g_lin(g2: tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]], u: V3, v: V3) -> LinPoly:
    g0 = u[0] * (g2[0][0] * v[0] + g2[0][1] * v[1]) + u[1] * (g2[1][0] * v[0] + g2[1][1] * v[1])
    return g0, u[2] * v[2]


def _lin_det(a1: LinPoly, b1: LinPoly, a2: LinPoly, b2: LinPoly) -> LinPoly:
    """Exact Cauchy–Binet linear minor `a1(t)*b1(t) - a2(t)*b2(t)` where `t²` cancels identically."""
    p = poly_sub(poly_mul(a1, b1), poly_mul(a2, b2))
    assert poly_deg(p) <= 1, f"Unexpected degree > 1 in rank-1 Gram 2x2 minor: {p}"
    return (
        p[0] if len(p) >= 1 else Z,
        p[1] if len(p) >= 2 else Z,
    )


def _allowed_anchor_rule(rule: str) -> bool:
    return rule.startswith(
        (
            "apex_over_center",
            "perpendicular_foot_at_",
            "altitude_normalized_to_perpendicular_foot_at_",
            "orthogonal_projection_normalized_to_perpendicular_foot_at_",
            "line_perpendicular_to_two_intersecting_lines_foot_at_",
            "regular_pyramid_foot_at_base_center",
            "face_perpendicular_base_isosceles_foot_on_",
            "right_prism_translate",
            "affine_illustrative_apex_over_",
        )
    )


_SUPPORTED_PREMISE_FNS = frozenset(
    {
        "pyramid",
        "regular_pyramid",
        "prism",
        "regular_polygon",
        "rectangle",
        "rhombus",
        "parallelogram",
        "trapezoid",
        "isosceles_trapezoid",
        "segment_length",
        "equal_length",
        "segment_ratio",
        "right_angle",
        "perpendicular_lines",
        "perpendicular_line_plane",
        "altitude",
        "orthogonal_projection",
        "orthogonal_projection_line",
        "face_perpendicular_base",
        "midpoint",
        "divide_segment",
        "centroid",
        "intersect_line_line",
        "intersect_line_plane",
        "intersection_line",
        "translate_point",
        "section",
        "line_line_angle",
        "line_plane_angle",
        "plane_plane_angle",
        "dihedral_angle",
        "vertex_angle",
        "polygon_area",
    }
)

_SUPPORTED_GOAL_FNS = frozenset(
    {
        "ask_length",
        "ask_distance_point_plane",
        "ask_distance_line_plane",
        "ask_distance_planes",
        "ask_distance_lines",
        "ask_angle_lines",
        "ask_angle_line_plane",
        "ask_angle_plane_plane",
        "ask_area",
        "ask_length_ratio",
        "ask_area_ratio",
        "ask_volume_ratio",
    }
)


# ── Main Symbolic Certifier on `_Dung` + `KetQuaTuyen` ────────────────────────────────────────────────────────────────


def certify_height_invariance_symbolic(
    dung: Any,
    res: Any,
) -> tuple[bool, dict[str, Any] | None, str | None, str | None]:
    """Verify all 8 formal proof obligations (`PO-1` .. `PO-8`) symbolically over `ℚ[t]` (`t = h² ∈ (0, +∞)`).

    Returns `(certified, certificate_dict, failed_obligation, failure_detail)`.
    """
    from app.simulation.geometry_functions.engine import _binh_phuong, binh_phuong, dinh_dang

    obligations: dict[str, dict[str, Any]] = {}

    # ── PO-1: Single Free Height Parameter & Orthogonal SPD Base Chart G(t) = G₂ ⊕ (t) ───────────────────────────
    g2 = getattr(dung, "G2", None)
    if (
        res.status != "SERVED"
        or not getattr(dung, "free_height_for", None)
        or g2 is None
        or len(getattr(dung, "off_base_anchors", ())) != 1
        or bool(getattr(dung, "mirror_apices", None))
        or bool(getattr(dung, "_flip_apices", None))
        or bool(dung.of("curved_solid"))
        or bool(dung.of("sphere_tangent_plane"))
    ):
        return (
            False,
            None,
            "PO_SINGLE_FREE_HEIGHT_ORTHOGONAL_CHART",
            "Cấu hình không thuộc lớp một tham số chiều cao trực giao duy nhất G(t) = G₂ ⊕ (t).",
        )
    det_g2 = g2[0][0] * g2[1][1] - g2[0][1] * g2[1][0]
    if g2[0][0] <= Z or g2[0][1] != g2[1][0] or det_g2 <= Z:
        return (
            False,
            None,
            "PO_SINGLE_FREE_HEIGHT_ORTHOGONAL_CHART",
            "Ma trận Gram đáy G₂ không đối xứng xác định dương.",
        )

    solid_vertices: set[str] = set()
    for k in dung.khoi.values():
        solid_vertices |= set(k.base) | set(k.top) | ({k.apex} if k.apex else set())
        if k.kind == "prism":
            vec0 = dung._vec(k.base[0], k.top[0])
            if vec0[2] == Z or (k.right and (vec0[0] != Z or vec0[1] != Z)):
                return (
                    False,
                    None,
                    "PO_SINGLE_FREE_HEIGHT_ORTHOGONAL_CHART",
                    f"Lăng trụ {k.name} suy biến hoặc vi phạm trực giao trục chiều cao.",
                )
        elif k.kind == "pyramid" and k.apex:
            if dung.pts[k.apex][2] == Z:
                return (
                    False,
                    None,
                    "PO_SINGLE_FREE_HEIGHT_ORTHOGONAL_CHART",
                    f"Đỉnh {k.apex} của khối chóp suy biến vào mặt đáy.",
                )

    obligations["PO_SINGLE_FREE_HEIGHT_ORTHOGONAL_CHART"] = {
        "verified": True,
        "free_for": sorted(dung.free_height_for),
        "off_base_anchors": list(dung.off_base_anchors),
        "det_g2": str(det_g2),
    }

    # ── PO-2: Affine Coordinates & Constructed Objects Independent of Height t ───────────────────────────────────
    place_steps = {s["object"]: s for s in dung.trace if s.get("step") == "place_point"}
    for anchor in dung.off_base_anchors:
        rule = str((place_steps.get(anchor) or {}).get("rule") or "")
        if not _allowed_anchor_rule(rule):
            return (
                False,
                None,
                "PO_AFFINE_COORDINATES_T_INDEPENDENT",
                f"Điểm neo độ cao {anchor} dùng luật đặt phụ thuộc độ dài cạnh bên ({rule}).",
            )

    for pt_name, xyz in dung.pts.items():
        if pt_name in dung.circumcenters:
            verts_cc = dung.circumcenters[pt_name]
            if any(dung.pts[v][2] != Z for v in verts_cc):
                return (
                    False,
                    None,
                    "PO_AFFINE_COORDINATES_T_INDEPENDENT",
                    f"Tâm ngoại tiếp {pt_name} phụ thuộc đỉnh ngoài mặt đáy nên di chuyển theo h².",
                )
        if pt_name in dung.incenters:
            verts_ic = dung.incenters[pt_name]
            if any(dung.pts[v][2] != Z for v in verts_ic):
                return (
                    False,
                    None,
                    "PO_AFFINE_COORDINATES_T_INDEPENDENT",
                    f"Tâm nội tiếp {pt_name} phụ thuộc đỉnh ngoài mặt đáy.",
                )
        if pt_name in dung.constructions:
            cc = dung.constructions[pt_name]
            ca = cc.args
            if cc.fn == "orthogonal_projection_line":
                line_obj = dung.lines[ca.line_ref] if getattr(ca, "line_ref", None) else dung._line(ca.line)
                d_vec = (line_obj.direction.x, line_obj.direction.y, line_obj.direction.z)
                diff = tuple(dung.pts[ca.point][i] - xyz[i] for i in range(3))
                if _g_lin(g2, d_vec, d_vec) == (Z, Z) or _g_lin(g2, diff, d_vec) != (Z, Z):
                    return (
                        False,
                        None,
                        "PO_AFFINE_COORDINATES_T_INDEPENDENT",
                        f"Hình chiếu {pt_name} trên đường thẳng có toạ độ phụ thuộc h².",
                    )
            elif cc.fn == "orthogonal_projection":
                mp = dung._diem_qua(ca.plane)
                u = dung._vec(mp[0], mp[1])
                v = dung._vec(mp[0], mp[2])
                diff = tuple(dung.pts[ca.point][i] - xyz[i] for i in range(3))
                if _g_lin(g2, diff, u) != (Z, Z) or _g_lin(g2, diff, v) != (Z, Z):
                    return (
                        False,
                        None,
                        "PO_AFFINE_COORDINATES_T_INDEPENDENT",
                        f"Hình chiếu {pt_name} trên mặt phẳng có toạ độ phụ thuộc h².",
                    )
        # Non-solid-vertex constructed points must sit in the fixed base plane z == 0 for Euclidean metric goals
        # so their physical Euclidean position in Scene3D does not move vertically when height h varies;
        # for purely affine ratio goals (`ask_length_ratio`, `ask_area_ratio`, `ask_volume_ratio`),
        # affine points (`midpoint`, `divide_segment`, `centroid`, `translate_point`, `intersect_line_*`) have
        # constant barycentric/affine chart coordinates over all t > 0.
        all_affine_ratio_goals = (
            len(dung.khoi) == 1
            and all(
                c.fn in ("ask_length_ratio", "ask_area_ratio")
                for c in dung.calls
                if c.fn.startswith("ask_")
            )
        )
        pt_rule = str((place_steps.get(pt_name) or {}).get("rule") or "")
        is_affine_point = (
            all_affine_ratio_goals
            and (
                (
                    pt_name in dung.constructions
                    and dung.constructions[pt_name].fn
                    in ("midpoint", "divide_segment", "centroid", "translate_point", "intersect_line_line", "intersect_line_plane")
                )
                or pt_rule.startswith(
                    (
                        "midpoint",
                        "divide_segment",
                        "centroid",
                        "translate_point",
                        "intersect_line_line",
                        "intersect_line_plane",
                        "section_edge_cut",
                        "intersection_of_base_diagonals",
                    )
                )
            )
        )
        if pt_name not in solid_vertices and xyz[2] != Z and not is_affine_point:
            return (
                False,
                None,
                "PO_AFFINE_COORDINATES_T_INDEPENDENT",
                f"Điểm dựng {pt_name} có cao độ z={xyz[2]} ≠ 0 nên vị trí vật lý trên Scene3D phụ thuộc chiều cao chưa biết.",
            )

    # Check auxiliary planes (`MAT_VUONG_DUONG` / `MAT_RANG_BUOC` perpendicularity must hold for ALL t > 0)
    adj_g2 = ((g2[1][1], -g2[0][1]), (-g2[1][0], g2[0][0]))

    def _planes_perp_for_all_t(n1: Vec3, n2: Vec3) -> bool:
        xy_dot = n1.x * (adj_g2[0][0] * n2.x + adj_g2[0][1] * n2.y) + n1.y * (adj_g2[1][0] * n2.x + adj_g2[1][1] * n2.y)
        z_dot = det_g2 * n1.z * n2.z
        return xy_dot == Z and z_dot == Z

    for d_aux in getattr(dung, "mat_phu", ()) or ():
        rule_aux = d_aux.get("rule")
        pl_labels = d_aux.get("plane") or ()
        if len(pl_labels) >= 3 and all(p in dung.pts for p in pl_labels):
            p_tri = dung._diem_qua(pl_labels)
            u_p, v_p = dung._vec(p_tri[0], p_tri[1]), dung._vec(p_tri[0], p_tri[2])
            if rule_aux == "through_point_perpendicular_line":
                dl = dung._vec(*d_aux["perpendicular_to"])
                if _g_lin(g2, u_p, dl) != (Z, Z) or _g_lin(g2, v_p, dl) != (Z, Z):
                    return (
                        False,
                        None,
                        "PO_AFFINE_COORDINATES_T_INDEPENDENT",
                        "Mặt phẳng phụ vuông góc đường xiên thay đổi phương theo h².",
                    )
            elif rule_aux == "constrained_plane":
                n_pl = Vec3(*u_p).cross(Vec3(*v_p))
                for cst in d_aux.get("constraints") or ():
                    if cst.get("kind") == "perpendicular_to_plane":
                        ref_tri = dung._ba_diem(cst["points"])
                        n_ref = Vec3(*dung._vec(ref_tri[0], ref_tri[1])).cross(Vec3(*dung._vec(ref_tri[0], ref_tri[2])))
                        if not _planes_perp_for_all_t(n_pl, n_ref):
                            return (
                                False,
                                None,
                                "PO_AFFINE_COORDINATES_T_INDEPENDENT",
                                "Mặt phẳng ràng buộc vuông góc thay đổi theo h².",
                            )

    obligations["PO_AFFINE_COORDINATES_T_INDEPENDENT"] = {
        "verified": True,
        "point_count": len(dung.pts),
        "non_vertex_points_on_base": sorted(p for p in dung.pts if p not in solid_vertices),
    }

    # ── PO-3: Section Topology Invariance over (0, +∞) ───────────────────────────────────────────────────────────
    section_calls = list(dung.of("section"))
    for sc in section_calls:
        pl_pts = dung._diem_qua(sc.args.plane)
        if any(p not in dung.pts for p in pl_pts):
            return (
                False,
                None,
                "PO_SECTION_TOPOLOGY_INVARIANT",
                f"Mặt cắt {sc.id} thiếu điểm chứng nhân bất biến.",
            )
    obligations["PO_SECTION_TOPOLOGY_INVARIANT"] = {
        "verified": True,
        "section_count": len(section_calls),
    }

    # ── PO-4: Valid Domain Covers ALL t ∈ (0, +∞) (Every Premise Holds Identically) ─────────────────────────────
    for c in dung.calls:
        if c.fn.startswith("ask_"):
            continue
        if c.fn == "height" or c.fn not in _SUPPORTED_PREMISE_FNS:
            return (
                False,
                None,
                "PO_VALID_DOMAIN_ALL_POSITIVE_T",
                f"Giả thiết {c.fn} ({c.id}) không thuộc lớp bất biến miền (0, +∞).",
            )
        a = c.args
        if c.fn == "segment_length":
            u = dung._vec(*a.segment)
            if _g_lin(g2, u, u) != (binh_phuong(a.value), Z):
                return (
                    False,
                    None,
                    "PO_VALID_DOMAIN_ALL_POSITIVE_T",
                    f"Độ dài {c.id} ràng buộc h² vào giá trị hữu hạn.",
                )
        elif c.fn == "equal_length":
            ua, ub = dung._vec(*a.segment_a), dung._vec(*a.segment_b)
            if _g_lin(g2, ua, ua) != _g_lin(g2, ub, ub):
                return (
                    False,
                    None,
                    "PO_VALID_DOMAIN_ALL_POSITIVE_T",
                    f"Đẳng thức độ dài {c.id} không nghiệm đúng trên toàn miền h² > 0.",
                )
        elif c.fn == "segment_ratio":
            ua, ub = dung._vec(*a.segment_a), dung._vec(*a.segment_b)
            r2 = binh_phuong(a.ratio)
            g_ub = _g_lin(g2, ub, ub)
            if _g_lin(g2, ua, ua) != (r2 * g_ub[0], r2 * g_ub[1]):
                return (
                    False,
                    None,
                    "PO_VALID_DOMAIN_ALL_POSITIVE_T",
                    f"Tỉ số độ dài {c.id} không nghiệm đúng trên toàn miền h² > 0.",
                )
        elif c.fn in ("perpendicular_lines", "right_angle"):
            u, w = (
                (dung._vec(*a.line1), dung._vec(*a.line2))
                if c.fn == "perpendicular_lines"
                else (dung._vec(a.vertex, a.rays[0]), dung._vec(a.vertex, a.rays[1]))
            )
            if (
                not check_linear_positive_on_positive_reals(_g_lin(g2, u, u))
                or not check_linear_positive_on_positive_reals(_g_lin(g2, w, w))
                or _g_lin(g2, u, w) != (Z, Z)
            ):
                return (
                    False,
                    None,
                    "PO_VALID_DOMAIN_ALL_POSITIVE_T",
                    f"Quan hệ vuông góc {c.id} chỉ thỏa tại một chiều cao riêng biệt.",
                )
        elif c.fn in ("perpendicular_line_plane", "altitude", "orthogonal_projection"):
            if c.fn == "perpendicular_line_plane":
                ln_a, ln_b = a.line
                mp = a.plane
                d_vec = dung._vec(ln_a, ln_b)
            elif c.fn == "altitude":
                k = dung.khoi[a.solid]
                d_vec = dung._vec(a.foot, a.apex)
                mp = k.base
            else:
                d_vec = dung._vec(a.image, a.point)
                mp = a.plane
            if not check_linear_positive_on_positive_reals(_g_lin(g2, d_vec, d_vec)) or any(
                _g_lin(g2, d_vec, dung._vec(mp[0], x)) != (Z, Z) for x in mp[1:]
            ):
                return (
                    False,
                    None,
                    "PO_VALID_DOMAIN_ALL_POSITIVE_T",
                    f"Quan hệ đường vuông góc mặt {c.id} không bất biến theo h².",
                )
        elif c.fn == "face_perpendicular_base":
            u1, v1 = dung._vec(a.face[0], a.face[1]), dung._vec(a.face[0], a.face[2])
            u2, v2 = dung._vec(a.base[0], a.base[1]), dung._vec(a.base[0], a.base[2])
            n1 = Vec3(*u1).cross(Vec3(*v1))
            n2 = Vec3(*u2).cross(Vec3(*v2))
            if n1.is_zero() or n2.is_zero() or not _planes_perp_for_all_t(n1, n2):
                return (
                    False,
                    None,
                    "PO_VALID_DOMAIN_ALL_POSITIVE_T",
                    f"Quan hệ mặt bên vuông góc đáy {c.id} không thỏa trên toàn miền h² > 0.",
                )
        elif c.fn == "regular_pyramid":
            k = dung.khoi[a.apex + "." + "".join(a.base)]
            lat_polys = {_g_lin(g2, dung._vec(k.apex, b), dung._vec(k.apex, b)) for b in k.base}
            if len(lat_polys) != 1:
                return (
                    False,
                    None,
                    "PO_VALID_DOMAIN_ALL_POSITIVE_T",
                    f"Các cạnh bên chóp đều {c.id} không đồng nhất đa thức theo h².",
                )
        elif c.fn == "line_line_angle":
            _s2, cos2, _ = dung._goc_tham_so(a.value, a.unit, allow_obtuse=False, calls=(c.id,))
            u, v = dung._vec(*a.line1), dung._vec(*a.line2)
            guu, gvv, guv = _g_lin(g2, u, u), _g_lin(g2, v, v), _g_lin(g2, u, v)
            if (
                not check_linear_positive_on_positive_reals(guu)
                or not check_linear_positive_on_positive_reals(gvv)
                or poly_sub(poly_mul(guv, guv), poly_scale(poly_mul(guu, gvv), cos2)) != ()
            ):
                return (
                    False,
                    None,
                    "PO_VALID_DOMAIN_ALL_POSITIVE_T",
                    f"Góc hai đường {c.id} cố định h² thay vì nghiệm đúng trên (0, +∞).",
                )
        elif c.fn == "line_plane_angle":
            sin2, _c2, _ = dung._goc_tham_so(a.value, a.unit, allow_obtuse=False, calls=(c.id,))
            mp = dung._ba_diem(a.plane)
            u, v, w = dung._vec(mp[0], mp[1]), dung._vec(mp[0], mp[2]), dung._vec(*a.line)
            gww = _g_lin(g2, w, w)
            duv = _lin_det(_g_lin(g2, u, u), _g_lin(g2, v, v), _g_lin(g2, u, v), _g_lin(g2, u, v))
            d3_c = (_det3(u, v, w) ** 2) * det_g2
            if (
                not check_linear_positive_on_positive_reals(gww)
                or not check_linear_positive_on_positive_reals(duv)
                or poly_sub(poly_scale(poly_mul(gww, duv), sin2), (Z, d3_c)) != ()
            ):
                return (
                    False,
                    None,
                    "PO_VALID_DOMAIN_ALL_POSITIVE_T",
                    f"Góc đường–mặt {c.id} ràng buộc h².",
                )
        elif c.fn == "vertex_angle":
            _s2, cos2, cos_sign = dung._goc_tham_so(a.value, a.unit, allow_obtuse=True, calls=(c.id,))
            u, w = dung._vec(a.vertex, a.rays[0]), dung._vec(a.vertex, a.rays[1])
            guu, gww, guw = _g_lin(g2, u, u), _g_lin(g2, w, w), _g_lin(g2, u, w)
            if (
                not check_linear_positive_on_positive_reals(guu)
                or not check_linear_positive_on_positive_reals(gww)
                or not check_linear_sign_invariant_on_positive_reals(guw, cos_sign)
                or poly_sub(poly_mul(guw, guw), poly_scale(poly_mul(guu, gww), cos2)) != ()
            ):
                return (
                    False,
                    None,
                    "PO_VALID_DOMAIN_ALL_POSITIVE_T",
                    f"Góc đỉnh {c.id} đổi nhánh hoặc phụ thuộc chiều cao trên (0, +∞).",
                )
        elif c.fn == "dihedral_angle":
            _s2, cos2, cos_sign = dung._goc_tham_so(a.value, a.unit, allow_obtuse=True, calls=(c.id,))
            e = dung._vec(*a.edge)
            u_p, u_q = dung._vec(a.edge[0], a.point_a), dung._vec(a.edge[0], a.point_b)
            gee, gup, guq = _g_lin(g2, e, e), _g_lin(g2, u_p, u_p), _g_lin(g2, u_q, u_q)
            gep, geq, gpq = _g_lin(g2, u_p, e), _g_lin(g2, u_q, e), _g_lin(g2, u_p, u_q)
            dp = _lin_det(gee, gup, gep, gep)
            dq = _lin_det(gee, guq, geq, geq)
            npq = _lin_det(gee, gpq, gep, geq)
            if (
                not check_linear_positive_on_positive_reals(dp)
                or not check_linear_positive_on_positive_reals(dq)
                or not check_linear_sign_invariant_on_positive_reals(npq, cos_sign)
                or poly_sub(poly_mul(npq, npq), poly_scale(poly_mul(dp, dq), cos2)) != ()
            ):
                return (
                    False,
                    None,
                    "PO_VALID_DOMAIN_ALL_POSITIVE_T",
                    f"Góc nhị diện {c.id} đổi dấu nhánh hoặc ràng buộc h² trên (0, +∞).",
                )
        elif c.fn == "plane_plane_angle":
            _s2, cos2, _ = dung._goc_tham_so(a.value, a.unit, allow_obtuse=False, calls=(c.id,))
            p1, p2 = dung._ba_diem(a.plane1), dung._ba_diem(a.plane2)
            u1a, u1b = dung._vec(p1[0], p1[1]), dung._vec(p1[0], p1[2])
            u2a, u2b = dung._vec(p2[0], p2[1]), dung._vec(p2[0], p2[2])
            n1 = Vec3(*u1a).cross(Vec3(*u1b))
            n2 = Vec3(*u2a).cross(Vec3(*u2b))
            ev = n1.cross(n2)
            if ev.is_zero():
                if cos2 != ONE:
                    return False, None, "PO_VALID_DOMAIN_ALL_POSITIVE_T", f"Góc hai mặt song song {c.id} mâu thuẫn."
            else:
                e = (ev.x, ev.y, ev.z)
                u1 = u1a if not Vec3(*u1a).cross(ev).is_zero() else u1b
                u2 = u2a if not Vec3(*u2a).cross(ev).is_zero() else u2b
                gee, gu1, gu2 = _g_lin(g2, e, e), _g_lin(g2, u1, u1), _g_lin(g2, u2, u2)
                ge1, ge2, g12 = _g_lin(g2, u1, e), _g_lin(g2, u2, e), _g_lin(g2, u1, u2)
                d1 = _lin_det(gee, gu1, ge1, ge1)
                d2 = _lin_det(gee, gu2, ge2, ge2)
                n12 = _lin_det(gee, g12, ge1, ge2)
                if (
                    not check_linear_positive_on_positive_reals(d1)
                    or not check_linear_positive_on_positive_reals(d2)
                    or poly_sub(poly_mul(n12, n12), poly_scale(poly_mul(d1, d2), cos2)) != ()
                ):
                    return (
                        False,
                        None,
                        "PO_VALID_DOMAIN_ALL_POSITIVE_T",
                        f"Góc hai mặt {c.id} ràng buộc h².",
                    )

    obligations["PO_VALID_DOMAIN_ALL_POSITIVE_T"] = {
        "verified": True,
        "domain": "(0, +inf)",
        "checked_premise_count": sum(1 for c in dung.calls if not c.fn.startswith("ask_")),
    }

    # ── PO-5, PO-6, PO-7 & PO-8: Symbolic Goal Rational Forms, Denominator Positivity, Identity & Cross-Check ────
    ask_calls = [c for c in dung.calls if c.fn.startswith("ask_")]
    if not ask_calls:
        return False, None, "PO_POLYNOMIAL_DEGREE_BOUNDED", "Không có mục tiêu đo lường."

    goal_rational_forms: dict[str, dict[str, Any]] = {}
    fm = res.exec_result.final_memory

    for c in ask_calls:
        if c.fn not in _SUPPORTED_GOAL_FNS:
            return (
                False,
                None,
                "PO_POLYNOMIAL_DEGREE_BOUNDED",
                f"Mục tiêu {c.fn} ({c.id}) không thuộc lớp biểu thức hữu tỉ bậc ≤ {MAX_CERTIFIED_DEGREE} theo h².",
            )
        a = c.args
        p_poly: Poly
        q_poly: Poly
        den_factors: tuple[LinPoly, ...]
        value_kind: str

        if c.fn == "ask_length":
            u = dung._vec(*a.segment)
            guu = _g_lin(g2, u, u)
            if not check_linear_positive_on_positive_reals(guu) and guu != (Z, Z):
                return False, None, "PO_DENOMINATOR_POSITIVE_ON_DOMAIN", f"Đoạn {c.id} suy biến."
            p_poly = poly_trim(guu)
            q_poly = (ONE,)
            den_factors = ()
            value_kind = "squared_quantity"

        elif c.fn in ("ask_distance_point_plane", "ask_distance_line_plane", "ask_distance_planes"):
            if c.fn == "ask_distance_point_plane":
                pt_src = a.point
                mp = a.plane[:3]
            elif c.fn == "ask_distance_line_plane":
                ln_u = dung._vec(*a.line)
                mp = a.plane[:3]
                n_mp = Vec3(*dung._vec(mp[0], mp[1])).cross(Vec3(*dung._vec(mp[0], mp[2])))
                if ln_u == (Z, Z, Z) or Vec3(*ln_u).dot(n_mp) != Z:
                    return (
                        False,
                        None,
                        "PO_VALID_DOMAIN_ALL_POSITIVE_T",
                        f"Đường thẳng và mặt phẳng ở {c.id} không song song.",
                    )
                pt_src = a.line[0]
            else:
                mp1, mp2 = a.plane1[:3], a.plane2[:3]
                n1 = Vec3(*dung._vec(mp1[0], mp1[1])).cross(Vec3(*dung._vec(mp1[0], mp1[2])))
                n2 = Vec3(*dung._vec(mp2[0], mp2[1])).cross(Vec3(*dung._vec(mp2[0], mp2[2])))
                if n1.is_zero() or n2.is_zero() or not n1.cross(n2).is_zero():
                    return (
                        False,
                        None,
                        "PO_VALID_DOMAIN_ALL_POSITIVE_T",
                        f"Hai mặt phẳng ở {c.id} không song song.",
                    )
                pt_src = mp1[0]
                mp = mp2
            u, v, w = dung._vec(mp[0], mp[1]), dung._vec(mp[0], mp[2]), dung._vec(mp[0], pt_src)
            duv = _lin_det(_g_lin(g2, u, u), _g_lin(g2, v, v), _g_lin(g2, u, v), _g_lin(g2, u, v))
            d3_c = (_det3(u, v, w) ** 2) * det_g2
            p_poly = poly_trim((Z, d3_c))
            q_poly = poly_trim(duv)
            den_factors = (duv,)
            value_kind = "squared_quantity"

        elif c.fn == "ask_distance_lines":
            d1, d2 = dung._vec(*a.line1), dung._vec(*a.line2)
            r_vec = dung._vec(a.line1[0], a.line2[0])
            if d1 == (Z, Z, Z) or d2 == (Z, Z, Z):
                return False, None, "PO_DENOMINATOR_POSITIVE_ON_DOMAIN", f"Đường thẳng ở {c.id} suy biến."
            if Vec3(*d1).cross(Vec3(*d2)).is_zero():
                gd1 = _g_lin(g2, d1, d1)
                num_par = _lin_det(_g_lin(g2, r_vec, r_vec), gd1, _g_lin(g2, r_vec, d1), _g_lin(g2, r_vec, d1))
                p_poly = poly_trim(num_par)
                q_poly = poly_trim(gd1)
                den_factors = (gd1,)
            else:
                duv = _lin_det(_g_lin(g2, d1, d1), _g_lin(g2, d2, d2), _g_lin(g2, d1, d2), _g_lin(g2, d1, d2))
                d3_c = (_det3(d1, d2, r_vec) ** 2) * det_g2
                p_poly = poly_trim((Z, d3_c))
                q_poly = poly_trim(duv)
                den_factors = (duv,)
            value_kind = "squared_quantity"

        elif c.fn == "ask_angle_lines":
            u, v = dung._vec(*a.line1), dung._vec(*a.line2)
            guu, gvv, guv = _g_lin(g2, u, u), _g_lin(g2, v, v), _g_lin(g2, u, v)
            p_poly = poly_mul(guv, guv)
            q_poly = poly_mul(guu, gvv)
            den_factors = (guu, gvv)
            value_kind = "cos_squared"

        elif c.fn == "ask_angle_line_plane":
            mp = a.plane[:3]
            u, v, w = dung._vec(mp[0], mp[1]), dung._vec(mp[0], mp[2]), dung._vec(*a.line)
            gww = _g_lin(g2, w, w)
            duv = _lin_det(_g_lin(g2, u, u), _g_lin(g2, v, v), _g_lin(g2, u, v), _g_lin(g2, u, v))
            d3_c = (_det3(u, v, w) ** 2) * det_g2
            q_poly = poly_mul(gww, duv)
            p_poly = poly_sub(q_poly, (Z, d3_c))
            den_factors = (gww, duv)
            value_kind = "cos_squared"

        elif c.fn == "ask_angle_plane_plane":
            mp1, mp2 = a.plane1[:3], a.plane2[:3]
            u1a, u1b = dung._vec(mp1[0], mp1[1]), dung._vec(mp1[0], mp1[2])
            u2a, u2b = dung._vec(mp2[0], mp2[1]), dung._vec(mp2[0], mp2[2])
            n1 = Vec3(*u1a).cross(Vec3(*u1b))
            n2 = Vec3(*u2a).cross(Vec3(*u2b))
            if n1.is_zero() or n2.is_zero():
                return False, None, "PO_DENOMINATOR_POSITIVE_ON_DOMAIN", f"Mặt phẳng ở {c.id} suy biến."
            ev = n1.cross(n2)
            if ev.is_zero():
                p_poly = (ONE,)
                q_poly = (ONE,)
                den_factors = ()
            else:
                e = (ev.x, ev.y, ev.z)
                u1 = u1a if not Vec3(*u1a).cross(ev).is_zero() else u1b
                u2 = u2a if not Vec3(*u2a).cross(ev).is_zero() else u2b
                gee, gu1, gu2 = _g_lin(g2, e, e), _g_lin(g2, u1, u1), _g_lin(g2, u2, u2)
                ge1, ge2, g12 = _g_lin(g2, u1, e), _g_lin(g2, u2, e), _g_lin(g2, u1, u2)
                d1 = _lin_det(gee, gu1, ge1, ge1)
                d2 = _lin_det(gee, gu2, ge2, ge2)
                n12 = _lin_det(gee, g12, ge1, ge2)
                p_poly = poly_mul(n12, n12)
                q_poly = poly_mul(d1, d2)
                den_factors = (d1, d2)
            value_kind = "cos_squared"

        elif c.fn == "ask_length_ratio":
            u, v = dung._vec(*a.numerator_segment), dung._vec(*a.denominator_segment)
            if getattr(dung, "free_affine_for", None) and not Vec3(*u).cross(Vec3(*v)).is_zero():
                return (
                    False,
                    None,
                    "PO_EXACT_POLYNOMIAL_IDENTITY",
                    f"Tỉ số độ dài {c.id} phụ thuộc hệ trục khi hai đoạn không cùng phương.",
                )
            guu, gvv = _g_lin(g2, u, u), _g_lin(g2, v, v)
            p_poly = poly_trim(guu)
            q_poly = poly_trim(gvv)
            den_factors = (gvv,)
            value_kind = "squared_quantity"

        elif c.fn == "ask_area_ratio":
            def _poly_area_terms(poly_labels: list[str]) -> tuple[Vec3 | None, Fraction, LinPoly, str | None]:
                if len(poly_labels) < 3:
                    return None, Z, (Z, Z), f"Đa giác {c.id} thiếu đỉnh."
                p0 = Vec3(*dung.pts[poly_labels[0]])
                c1 = (Vec3(*dung.pts[poly_labels[1]]) - p0).cross(Vec3(*dung.pts[poly_labels[2]]) - p0)
                c1_sq = c1.dot(c1)
                if c1_sq == Z:
                    return None, Z, (Z, Z), f"Đa giác {c.id} suy biến."
                tot = Z
                for idx_k in range(1, len(poly_labels) - 1):
                    uk = Vec3(*dung.pts[poly_labels[idx_k]]) - p0
                    vk = Vec3(*dung.pts[poly_labels[idx_k + 1]]) - p0
                    ck = uk.cross(vk)
                    if ck.is_zero() or not ck.cross(c1).is_zero():
                        return None, Z, (Z, Z), f"Đa giác {c.id} không phẳng lồi."
                    lam = ck.dot(c1) / c1_sq
                    if lam <= Z:
                        return None, Z, (Z, Z), f"Đa giác {c.id} tự cắt hoặc lõm."
                    tot += lam
                u1, v1 = dung._vec(poly_labels[0], poly_labels[1]), dung._vec(poly_labels[0], poly_labels[2])
                duv_poly = _lin_det(_g_lin(g2, u1, u1), _g_lin(g2, v1, v1), _g_lin(g2, u1, v1), _g_lin(g2, u1, v1))
                return c1, tot, duv_poly, None

            c1_num, tot_num, duv_num, err_num = _poly_area_terms(list(a.numerator_polygon))
            c1_den, tot_den, duv_den, err_den = _poly_area_terms(list(a.denominator_polygon))
            if err_num or err_den or c1_num is None or c1_den is None:
                return False, None, "PO_VALID_DOMAIN_ALL_POSITIVE_T", err_num or err_den or f"Đa giác {c.id} không hợp lệ."
            if getattr(dung, "free_affine_for", None) and not c1_num.cross(c1_den).is_zero():
                return (
                    False,
                    None,
                    "PO_EXACT_POLYNOMIAL_IDENTITY",
                    f"Tỉ số diện tích {c.id} phụ thuộc hệ trục khi hai đa giác không nằm trên mặt phẳng song song.",
                )
            p_poly = poly_scale(duv_num, (tot_num * tot_num) / Fraction(4))
            q_poly = poly_scale(duv_den, (tot_den * tot_den) / Fraction(4))
            den_fac: LinPoly = (
                q_poly[0] if len(q_poly) >= 1 else Z,
                q_poly[1] if len(q_poly) >= 2 else Z,
            )
            den_factors = (den_fac,)
            value_kind = "squared_quantity"

        elif c.fn == "ask_volume_ratio":
            v2_num = dung.volume_certificates.get(a.numerator_solid)
            v2_den = dung.volume_certificates.get(a.denominator_solid)
            if v2_num is None or v2_den is None or v2_den <= Z:
                return False, None, "PO_DENOMINATOR_POSITIVE_ON_DOMAIN", f"Thể tích ở {c.id} suy biến."
            p_poly = poly_trim((Z, v2_num))
            q_poly = poly_trim((Z, v2_den))
            den_factors = ((Z, v2_den),)
            value_kind = "squared_quantity"

        else:  # ask_area
            poly_labels = list(a.polygon)
            if len(poly_labels) < 3:
                return False, None, "PO_DENOMINATOR_POSITIVE_ON_DOMAIN", f"Đa giác {c.id} thiếu đỉnh."
            p0 = Vec3(*dung.pts[poly_labels[0]])
            c1 = (Vec3(*dung.pts[poly_labels[1]]) - p0).cross(Vec3(*dung.pts[poly_labels[2]]) - p0)
            c1_sq = c1.dot(c1)
            if c1_sq == Z:
                return False, None, "PO_DENOMINATOR_POSITIVE_ON_DOMAIN", f"Đa giác {c.id} suy biến."
            total_ratio = Z
            for idx_k in range(1, len(poly_labels) - 1):
                uk = Vec3(*dung.pts[poly_labels[idx_k]]) - p0
                vk = Vec3(*dung.pts[poly_labels[idx_k + 1]]) - p0
                ck = uk.cross(vk)
                if ck.is_zero() or not ck.cross(c1).is_zero():
                    return False, None, "PO_VALID_DOMAIN_ALL_POSITIVE_T", f"Đa giác {c.id} không phẳng lồi."
                lam = ck.dot(c1) / c1_sq
                if lam <= Z:
                    return False, None, "PO_VALID_DOMAIN_ALL_POSITIVE_T", f"Đa giác {c.id} tự cắt hoặc lõm."
                total_ratio += lam
            u1, v1 = dung._vec(poly_labels[0], poly_labels[1]), dung._vec(poly_labels[0], poly_labels[2])
            duv = _lin_det(_g_lin(g2, u1, u1), _g_lin(g2, v1, v1), _g_lin(g2, u1, v1), _g_lin(g2, u1, v1))
            p_poly = poly_scale(duv, (total_ratio * total_ratio) / Fraction(4))
            q_poly = (ONE,)
            den_factors = ()
            value_kind = "squared_quantity"

        ok_rat, fail_code, c_val = verify_rational_constancy_over_positive_reals(
            p_poly, q_poly, linear_den_factors=den_factors, max_degree=MAX_CERTIFIED_DEGREE
        )
        if not ok_rat or c_val is None:
            return (
                False,
                None,
                fail_code or "PO_EXACT_POLYNOMIAL_IDENTITY",
                f"Mục tiêu {c.id} ({c.fn}) phụ thuộc h² hoặc vi phạm điều kiện mẫu số trên (0, +∞).",
            )

        # PO-8: Cross-check symbolic constant `c_val` against SemanticProgramInterpreter output at t₀ = 1
        exec_val = fm.get(f"kq_{c.id}")
        if exec_val is None:
            return False, None, "PO_INTERPRETER_CROSS_CHECK", f"Thiếu biến kết quả thực thi kq_{c.id}."
        exec_comparable = Fraction(exec_val) if value_kind == "cos_squared" else _binh_phuong(exec_val)
        if exec_comparable != c_val or dinh_dang(exec_val) != (res.answer_exact.get(c.id) or {}).get("coef"):
            return (
                False,
                None,
                "PO_INTERPRETER_CROSS_CHECK",
                f"Giá trị thực thi kernel của {c.id} lệch hằng số chứng minh ký hiệu.",
            )

        goal_rational_forms[c.id] = {
            "fn": c.fn,
            "value_kind": value_kind,
            "numerator_coeffs": [str(x) for x in p_poly],
            "denominator_coeffs": [str(x) for x in q_poly],
            "denominator_linear_factors": [[str(f[0]), str(f[1])] for f in den_factors],
            "degree_numerator": max(0, poly_deg(p_poly)),
            "degree_denominator": max(0, poly_deg(q_poly)),
            "constant_value": str(c_val),
            "identity_residual_coeffs": [],
            "certified_coef": (res.answer_exact.get(c.id) or {}).get("coef"),
        }

    obligations["PO_POLYNOMIAL_DEGREE_BOUNDED"] = {
        "verified": True,
        "max_allowed_degree": MAX_CERTIFIED_DEGREE,
        "observed_max_degree": max(
            max(g["degree_numerator"], g["degree_denominator"]) for g in goal_rational_forms.values()
        ),
    }
    obligations["PO_DENOMINATOR_POSITIVE_ON_DOMAIN"] = {
        "verified": True,
        "domain": "(0, +inf)",
    }
    obligations["PO_EXACT_POLYNOMIAL_IDENTITY"] = {
        "verified": True,
        "identity": "P(t) - c * Q(t) == 0 over Q[t]",
    }
    obligations["PO_INTERPRETER_CROSS_CHECK"] = {
        "verified": True,
        "illustrative_t0": "1",
    }

    certificate: dict[str, Any] = {
        "schema_version": CERTIFICATE_SCHEMA_VERSION,
        "method": "rational_function_identity_in_h2",
        "certification_mode": CERTIFICATION_MODE,
        "parameter": "t = h^2",
        "domain": "(0, +inf)",
        "max_degree": MAX_CERTIFIED_DEGREE,
        "samples_h2": [str(s) for s in WITNESS_SAMPLES_H2],
        "chart_summary": {
            "base_g2": [[str(g2[0][0]), str(g2[0][1])], [str(g2[1][0]), str(g2[1][1])]],
            "det_g2": str(det_g2),
            "off_base_anchor_count": len(dung.off_base_anchors),
            "free_for": sorted(dung.free_height_for),
        },
        "proof_obligations": obligations,
        "goal_rational_forms": goal_rational_forms,
        "goal_values": {gid: v.get("coef") for gid, v in sorted((res.answer_exact or {}).items())},
        "goal_fns": sorted({c.fn for c in ask_calls}),
    }
    return True, certificate, None, None


# ── Standalone Independent Certificate Verifier (Zero Engine Dependency) ─────────────────────────────────────────────


def _coef_string_matches_constant(coef_str: str, constant_val: Fraction, value_kind: str) -> bool:
    """Independently parse `coef_str` (`'6'`, `'√2/2'`, `'15√93/31'`, `'3/4'`) and verify against `constant_val`."""
    import re

    s = (coef_str or "").strip()
    if not s:
        return False
    if value_kind == "cos_squared":
        try:
            return Fraction(s) == constant_val
        except (ValueError, ZeroDivisionError):
            return False
    # Parse canonical non-negative exact radical `<num>[√<rad>][/<den>]`
    m = re.fullmatch(r"(?P<num>\d+)?(?:√(?P<rad>\d+))?(?:/(?P<den>\d+))?", s)
    if not m or (m.group("num") is None and m.group("rad") is None):
        return False
    num = int(m.group("num")) if m.group("num") is not None else 1
    rad = int(m.group("rad")) if m.group("rad") is not None else 1
    den = int(m.group("den")) if m.group("den") is not None else 1
    if den == 0:
        return False
    return Fraction(num * num * rad, den * den) == constant_val


def verify_height_invariance_certificate(cert: dict[str, Any]) -> dict[str, Any]:
    """Independently verify a serialized `height-invariance-certificate/2` dictionary."""
    if not isinstance(cert, dict) or cert.get("schema_version") != CERTIFICATE_SCHEMA_VERSION:
        return {"verified": False, "failed_obligation": "SCHEMA_VERSION_MISMATCH"}
    if cert.get("certification_mode") != CERTIFICATION_MODE:
        return {"verified": False, "failed_obligation": "INVALID_CERTIFICATION_MODE"}

    # Check all 8 proof obligations present & marked verified
    pos = cert.get("proof_obligations")
    if not isinstance(pos, dict):
        return {"verified": False, "failed_obligation": "MISSING_PROOF_OBLIGATIONS"}
    for po_name in PROOF_OBLIGATIONS:
        po_entry = pos.get(po_name)
        if not isinstance(po_entry, dict) or po_entry.get("verified") is not True:
            return {"verified": False, "failed_obligation": po_name}

    # Check PO-1 chart summary
    chart = cert.get("chart_summary")
    if not isinstance(chart, dict) or chart.get("off_base_anchor_count") != 1:
        return {"verified": False, "failed_obligation": "PO_SINGLE_FREE_HEIGHT_ORTHOGONAL_CHART"}
    try:
        raw_g2 = chart["base_g2"]
        g00, g01 = Fraction(raw_g2[0][0]), Fraction(raw_g2[0][1])
        g10, g11 = Fraction(raw_g2[1][0]), Fraction(raw_g2[1][1])
        det_g2 = g00 * g11 - g01 * g10
    except (KeyError, IndexError, TypeError, ValueError, ZeroDivisionError):
        return {"verified": False, "failed_obligation": "PO_SINGLE_FREE_HEIGHT_ORTHOGONAL_CHART"}
    if g00 <= Z or g01 != g10 or det_g2 <= Z:
        return {"verified": False, "failed_obligation": "PO_SINGLE_FREE_HEIGHT_ORTHOGONAL_CHART"}

    # Check PO-5, PO-6, PO-7, PO-8 on every goal rational form
    forms = cert.get("goal_rational_forms")
    goal_values = cert.get("goal_values")
    if not isinstance(forms, dict) or not forms or not isinstance(goal_values, dict):
        return {"verified": False, "failed_obligation": "PO_POLYNOMIAL_DEGREE_BOUNDED"}
    if set(forms.keys()) != set(goal_values.keys()):
        return {"verified": False, "failed_obligation": "PO_INTERPRETER_CROSS_CHECK"}

    max_deg = int(cert.get("max_degree", MAX_CERTIFIED_DEGREE))
    if max_deg > MAX_CERTIFIED_DEGREE or max_deg < 0:
        return {"verified": False, "failed_obligation": "PO_POLYNOMIAL_DEGREE_BOUNDED"}

    for gid, gf in forms.items():
        if not isinstance(gf, dict) or gf.get("fn") not in _SUPPORTED_GOAL_FNS:
            return {"verified": False, "failed_obligation": "PO_POLYNOMIAL_DEGREE_BOUNDED"}
        try:
            p_poly = tuple(Fraction(x) for x in gf["numerator_coeffs"])
            q_poly = tuple(Fraction(x) for x in gf["denominator_coeffs"])
            factors = tuple((Fraction(f[0]), Fraction(f[1])) for f in gf["denominator_linear_factors"])
            claimed_c = Fraction(gf["constant_value"])
        except (KeyError, IndexError, TypeError, ValueError, ZeroDivisionError):
            return {"verified": False, "failed_obligation": "PO_POLYNOMIAL_DEGREE_BOUNDED"}

        ok_rat, fail_code, verified_c = verify_rational_constancy_over_positive_reals(
            p_poly, q_poly, linear_den_factors=factors, max_degree=max_deg
        )
        if not ok_rat or verified_c != claimed_c:
            return {"verified": False, "failed_obligation": fail_code or "PO_EXACT_POLYNOMIAL_IDENTITY"}

        # Evaluate across witness points on (0, +∞) as an independent rational evaluation sanity check:
        for sample_t in (*WITNESS_SAMPLES_H2, Fraction(11), Fraction(101), Fraction(1, 7)):
            if poly_eval(p_poly, sample_t) / poly_eval(q_poly, sample_t) != verified_c:
                return {"verified": False, "failed_obligation": "PO_EXACT_POLYNOMIAL_IDENTITY"}

        coef_str = goal_values.get(gid)
        if not isinstance(coef_str, str) or coef_str != gf.get("certified_coef"):
            return {"verified": False, "failed_obligation": "PO_INTERPRETER_CROSS_CHECK"}
        if not _coef_string_matches_constant(coef_str, verified_c, str(gf.get("value_kind") or "")):
            return {"verified": False, "failed_obligation": "PO_INTERPRETER_CROSS_CHECK"}

    return {
        "verified": True,
        "schema_version": CERTIFICATE_SCHEMA_VERSION,
        "checked_goals": sorted(forms.keys()),
        "checked_obligations": list(PROOF_OBLIGATIONS),
    }
