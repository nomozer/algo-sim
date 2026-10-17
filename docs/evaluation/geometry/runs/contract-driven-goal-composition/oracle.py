"""Independent Fraction/Gram mathematical oracle for run `contract-driven-goal-composition`.

Independence contract:
- Zero imports from `app` (no engine, planner, kernel, registry, or measure imports).
- All coordinates and Gram matrices are defined independently in this file.
- Computes exact rational values (`Fraction`) for midpoint, centroid, orthogonal projection onto line/plane,
  triangle area squared S² = (g(u,u)g(v,v) - g(u,v)²)/4, and line-plane angle sin²θ / cos²θ = 1 - sin²θ.
- Writes `corpus.json` once and refuses to overwrite an existing registered corpus.
"""
from __future__ import annotations

import json
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path

RUN = Path(__file__).resolve().parent
I3 = ((F(1), F(0), F(0)), (F(0), F(1), F(0)), (F(0), F(0), F(1)))


def v(*xs) -> tuple[F, F, F]:
    return tuple(F(x) for x in xs)


def add(a, b) -> tuple[F, F, F]:
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b) -> tuple[F, F, F]:
    return tuple(x - y for x, y in zip(a, b))


def scale(k, a) -> tuple[F, F, F]:
    return tuple(F(k) * x for x in a)


def g(a, b, G=I3) -> F:
    return sum(a[i] * F(G[i][j]) * b[j] for i in range(3) for j in range(3))


def det3(m) -> F:
    return (
        m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
        - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
        + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
    )


def mid(a, b) -> tuple[F, F, F]:
    return scale(F(1, 2), add(a, b))


def centroid(a, b, c) -> tuple[F, F, F]:
    return scale(F(1, 3), add(add(a, b), c))


def project_point_line(p, a, b, G=I3) -> tuple[F, F, F]:
    u = sub(b, a)
    uu = g(u, u, G)
    assert uu > 0, "degenerate line"
    t = g(sub(p, a), u, G) / uu
    return add(a, scale(t, u))


def project_point_plane(p, a, b, c, G=I3) -> tuple[F, F, F]:
    u, v_ = sub(b, a), sub(c, a)
    w = sub(p, a)
    uu, uv, vv = g(u, u, G), g(u, v_, G), g(v_, v_, G)
    det2 = uu * vv - uv * uv
    assert det2 > 0, "degenerate plane"
    wu, wv = g(w, u, G), g(w, v_, G)
    alpha = (vv * wu - uv * wv) / det2
    beta = (uu * wv - uv * wu) / det2
    return add(a, add(scale(alpha, u), scale(beta, v_)))


def d2_point_plane(p, a, b, c, G=I3) -> F:
    u, v_, w = sub(b, a), sub(c, a), sub(p, a)
    vs = (u, v_, w)
    m3 = [[g(s, t, G) for t in vs] for s in vs]
    m2 = m3[0][0] * m3[1][1] - m3[0][1] * m3[1][0]
    assert m2 > 0, "degenerate plane"
    return det3(m3) / m2


def area_sq_triangle(p, q, r, G=I3) -> F:
    """S² = ¼ (g(u,u)g(v,v) - g(u,v)²) for u = q - p, v = r - p."""
    u, v_ = sub(q, p), sub(r, p)
    dt4 = g(u, u, G) * g(v_, v_, G) - g(u, v_, G) ** 2
    assert dt4 > 0, "degenerate/collinear triangle"
    return dt4 / F(4)


def sin_sq_line_plane(p, q, a, b, c, G=I3) -> F:
    """sin²θ = det Gram(u, v, d) / (det Gram(u, v) · g(d, d))."""
    d = sub(q, p)
    u, v_ = sub(b, a), sub(c, a)
    dd = g(d, d, G)
    assert dd > 0, "degenerate line"
    vs = (u, v_, d)
    m3 = [[g(s, t, G) for t in vs] for s in vs]
    m2 = m3[0][0] * m3[1][1] - m3[0][1] * m3[1][0]
    assert m2 > 0, "degenerate plane"
    return det3(m3) / (m2 * dd)


def cos_sq_line_plane(p, q, a, b, c, G=I3) -> F:
    """cos²θ = 1 - sin²θ for line pq and plane (abc)."""
    return F(1) - sin_sq_line_plane(p, q, a, b, c, G)


# ── Independent reference figures ────────────────────────────────────────────────────────────────────────────────────
PYR = {"A": v(0, 0, 0), "B": v(2, 0, 0), "C": v(2, 2, 0), "D": v(0, 2, 0), "S": v(0, 0, 3)}
CUBE = {
    n: v(*xyz)
    for n, xyz in {
        "A": (0, 0, 0), "B": (2, 0, 0), "C": (2, 2, 0), "D": (0, 2, 0),
        "A'": (0, 0, 2), "B'": (2, 0, 2), "C'": (2, 2, 2), "D'": (0, 2, 2),
    }.items()
}
CUBOID = {
    n: v(*xyz)
    for n, xyz in {
        "A": (0, 0, 0), "B": (2, 0, 0), "C": (2, 4, 0), "D": (0, 4, 0),
        "A'": (0, 0, 3), "B'": (2, 0, 3), "C'": (2, 4, 3), "D'": (0, 4, 3),
    }.items()
}
PRISM_G = ((F(4), F(2), F(0)), (F(2), F(4), F(0)), (F(0), F(0), F(9)))
PRISM = {
    n: v(*xyz)
    for n, xyz in {
        "A": (0, 0, 0), "B": (1, 0, 0), "C": (0, 1, 0),
        "A'": (0, 0, 1), "B'": (1, 0, 1), "C'": (0, 1, 1),
    }.items()
}
# Held-out figure 1: regular tetrahedron ABCD of edge 2 (chart u=AB, v=AC, z_D over centroid of ABC, h² = 4 - 4/3 = 8/3)
TETRA_G = ((F(4), F(2), F(0)), (F(2), F(4), F(0)), (F(0), F(0), F(8, 3)))
TETRA = {"A": v(0, 0, 0), "B": v(1, 0, 0), "C": v(0, 1, 0), "D": v(F(1, 3), F(1, 3), 1)}
# Held-out figure 2: regular square pyramid S.ABCD with base edge 2, lateral edge 3 (center O=(1,1,0), h² = 9 - 2 = 7)
REG_PYR_G = ((F(4), F(0), F(0)), (F(0), F(4), F(0)), (F(0), F(0), F(7)))
REG_PYR = {"A": v(0, 0, 0), "B": v(1, 0, 0), "C": v(1, 1, 0), "D": v(0, 1, 0), "S": v(F(1, 2), F(1, 2), 1)}


def f(fid, kind, quote, role="premise", **kw):
    return {"id": fid, "kind": kind, "role": role, "quotes": [quote], **kw}


PYR_TEXT = ["Cho hình chóp S.ABCD.", "Đáy ABCD là hình vuông cạnh 2.", "SA vuông góc với (ABCD).", "SA = 3."]
PYR_FACTS = [
    f("f1", "solid", PYR_TEXT[0], solid="S.ABCD", solid_type="pyramid"),
    f("f2", "polygon_shape", PYR_TEXT[1], points=list("ABCD"), shape="square", value="2"),
    f("f3", "perpendicular", PYR_TEXT[2], points_a=["S", "A"], points_b=list("ABCD")),
    f("f4", "length", PYR_TEXT[3], points=["S", "A"], measure="segment", value="3"),
]
CUBE_TEXT = ["Cho hình lập phương ABCD.A'B'C'D' cạnh 2."]
CUBE_FACTS = [
    f("f1", "solid", CUBE_TEXT[0], solid="ABCD.A'B'C'D'", solid_type="cube"),
    f("f2", "length", CUBE_TEXT[0], solid="ABCD.A'B'C'D'", measure="edge", value="2"),
]
CUBOID_TEXT = ["Cho hình hộp chữ nhật ABCD.A'B'C'D'.", "AB = 2.", "AD = 4.", "AA' = 3."]
CUBOID_FACTS = [
    f("f1", "solid", CUBOID_TEXT[0], solid="ABCD.A'B'C'D'", solid_type="cuboid"),
    f("f2", "length", CUBOID_TEXT[1], points=["A", "B"], value="2", measure="segment"),
    f("f3", "length", CUBOID_TEXT[2], points=["A", "D"], value="4", measure="segment"),
    f("f4", "length", CUBOID_TEXT[3], points=["A", "A'"], value="3", measure="segment"),
]
PRISM_TEXT = ["Cho lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều ABC cạnh 2.", "AA' = 3."]
PRISM_FACTS = [
    f("f1", "solid", PRISM_TEXT[0], solid="ABC.A'B'C'", solid_type="prism", right=True),
    f("f2", "polygon_shape", PRISM_TEXT[0], points=["A", "B", "C"], shape="equilateral_triangle", value="2"),
    f("f3", "length", PRISM_TEXT[1], points=["A", "A'"], value="3", measure="segment"),
]
TETRA_TEXT = ["Cho tứ diện đều ABCD cạnh 2."]
TETRA_FACTS = [
    f("f1", "solid", TETRA_TEXT[0], solid="ABCD", solid_type="tetrahedron", regular=True),
    f("f2", "length", TETRA_TEXT[0], solid="ABCD", measure="edge", value="2"),
]
REG_PYR_TEXT = ["Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 2.", "SA = 3."]
REG_PYR_FACTS = [
    f("f1", "solid", REG_PYR_TEXT[0], solid="S.ABCD", solid_type="pyramid", regular=True),
    f("f2", "polygon_shape", REG_PYR_TEXT[0], points=list("ABCD"), shape="square", value="2"),
    f("f3", "length", REG_PYR_TEXT[1], points=["S", "A"], measure="segment", value="3"),
]


def make_corpus() -> dict:
    m_sc = mid(PYR["S"], PYR["C"])
    m_c_d = mid(CUBE["C'"], CUBE["D'"])
    m_a_c = mid(CUBOID["A'"], CUBOID["C'"])
    m_b_c_prism = mid(PRISM["B'"], PRISM["C'"])
    h_a_sbc = project_point_plane(PYR["A"], PYR["S"], PYR["B"], PYR["C"], I3)
    h_a_sb = project_point_line(PYR["A"], PYR["S"], PYR["B"], I3)

    q_pyr_ab = "Tính diện tích tam giác tạo bởi trung điểm của SC và hai điểm A, B."
    q_pyr_ad_rev = "Tính diện tích tam giác tạo bởi hai điểm A, D và trung điểm của SC."
    q_cube = "Tính diện tích tam giác tạo bởi trung điểm của C'D' và hai điểm A, B."
    q_cuboid = "Tính diện tích tam giác tạo bởi trung điểm của A'C' và hai điểm B, D."
    q_prism = "Tính diện tích tam giác tạo bởi trung điểm của B'C' và hai điểm A, B."

    proj_plane_q = "Gọi H là hình chiếu vuông góc của A lên (SBC)."
    ask_hab = "Tính diện tích tam giác HAB."
    proj_line_q = "Gọi H là hình chiếu vuông góc của A lên SB."
    ask_hcd = "Tính diện tích tam giác HCD."
    ask_mid_hd = "Tính diện tích tam giác tạo bởi trung điểm của SC và hai điểm H, D."
    named_mid_q = "Gọi N là trung điểm của SC."
    q_dist_sab = "Tính khoảng cách từ trung điểm của SC đến (SAB)."

    positive = [
        {
            "id": "pyramid-midpoint-area-AB",
            "slice": "A_area",
            "composition": "midpoint->ask_area",
            "text": " ".join([*PYR_TEXT, q_pyr_ab]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [f("q", "question", q_pyr_ab, role="question", quantity="area", point_kind="midpoint", points=["S", "C"], points_b=["A", "B"])]
            },
            "expected_squared": {"q": str(area_sq_triangle(m_sc, PYR["A"], PYR["B"], I3))},
        },
        {
            "id": "pyramid-midpoint-area-AD-reversed-wording",
            "slice": "A_area",
            "composition": "midpoint->ask_area",
            "text": " ".join([*PYR_TEXT, q_pyr_ad_rev]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [f("q", "question", q_pyr_ad_rev, role="question", quantity="area", point_kind="midpoint", points=["S", "C"], points_b=["A", "D"])]
            },
            "expected_squared": {"q": str(area_sq_triangle(m_sc, PYR["A"], PYR["D"], I3))},
        },
        {
            "id": "cube-midpoint-area",
            "slice": "A_area",
            "composition": "midpoint->ask_area",
            "text": " ".join([*CUBE_TEXT, q_cube]),
            "payload": {
                "facts": deepcopy(CUBE_FACTS)
                + [f("q", "question", q_cube, role="question", quantity="area", point_kind="midpoint", points=["C'", "D'"], points_b=["A", "B"])]
            },
            "expected_squared": {"q": str(area_sq_triangle(m_c_d, CUBE["A"], CUBE["B"], I3))},
        },
        {
            "id": "cuboid-midpoint-area",
            "slice": "A_area",
            "composition": "midpoint->ask_area",
            "text": " ".join([*CUBOID_TEXT, q_cuboid]),
            "payload": {
                "facts": deepcopy(CUBOID_FACTS)
                + [f("q", "question", q_cuboid, role="question", quantity="area", point_kind="midpoint", points=["A'", "C'"], points_b=["B", "D"])]
            },
            "expected_squared": {"q": str(area_sq_triangle(m_a_c, CUBOID["B"], CUBOID["D"], I3))},
        },
        {
            "id": "prism-midpoint-area",
            "slice": "A_area",
            "composition": "midpoint->ask_area",
            "text": " ".join([*PRISM_TEXT, q_prism]),
            "payload": {
                "facts": deepcopy(PRISM_FACTS)
                + [f("q", "question", q_prism, role="question", quantity="area", point_kind="midpoint", points=["B'", "C'"], points_b=["A", "B"])]
            },
            "expected_squared": {"q": str(area_sq_triangle(m_b_c_prism, PRISM["A"], PRISM["B"], PRISM_G))},
        },
        {
            "id": "pyramid-projection-plane-area",
            "slice": "A_area",
            "composition": "orthogonal_projection->ask_area",
            "text": " ".join([*PYR_TEXT, proj_plane_q, ask_hab]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [
                    f("fp", "projection", proj_plane_q, point="A", at="H", points=["S", "B", "C"]),
                    f("q", "question", ask_hab, role="question", quantity="area", points=["H", "A", "B"]),
                ]
            },
            "expected_squared": {"q": str(area_sq_triangle(h_a_sbc, PYR["A"], PYR["B"], I3))},
        },
        {
            "id": "pyramid-projection-line-area",
            "slice": "A_area",
            "composition": "orthogonal_projection_line->ask_area",
            "text": " ".join([*PYR_TEXT, proj_line_q, ask_hcd]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [
                    f("fp", "projection", proj_line_q, point="A", at="H", points=["S", "B"]),
                    f("q", "question", ask_hcd, role="question", quantity="area", points=["H", "C", "D"]),
                ]
            },
            "expected_squared": {"q": str(area_sq_triangle(h_a_sb, PYR["C"], PYR["D"], I3))},
        },
        {
            "id": "pyramid-projection-and-unnamed-midpoint-area",
            "slice": "A_area",
            "composition": "orthogonal_projection_line+midpoint->ask_area",
            "text": " ".join([*PYR_TEXT, proj_line_q, ask_mid_hd]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [
                    f("fp", "projection", proj_line_q, point="A", at="H", points=["S", "B"]),
                    f("q", "question", ask_mid_hd, role="question", quantity="area", point_kind="midpoint", points=["S", "C"], points_b=["H", "D"]),
                ]
            },
            "expected_squared": {"q": str(area_sq_triangle(m_sc, h_a_sb, PYR["D"], I3))},
        },
        {
            "id": "pyramid-reuse-named-midpoint-area",
            "slice": "A_area",
            "composition": "reuse_named_midpoint->ask_area",
            "text": " ".join([*PYR_TEXT, named_mid_q, q_pyr_ab]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [
                    f("fn", "point_def", named_mid_q, point="N", point_kind="midpoint", points=["S", "C"]),
                    f("q", "question", q_pyr_ab, role="question", quantity="area", point_kind="midpoint", points=["S", "C"], points_b=["A", "B"]),
                ]
            },
            "expected_squared": {"q": str(area_sq_triangle(m_sc, PYR["A"], PYR["B"], I3))},
            "expected_new_points": 0,
        },
        {
            "id": "pyramid-shared-midpoint-area-and-distance",
            "slice": "A_area",
            "composition": "midpoint->(ask_area+ask_distance_point_plane)",
            "text": " ".join([*PYR_TEXT, q_pyr_ab, q_dist_sab]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [
                    f("q1", "question", q_pyr_ab, role="question", quantity="area", point_kind="midpoint", points=["S", "C"], points_b=["A", "B"]),
                    f("q2", "question", q_dist_sab, role="question", quantity="distance", point_kind="midpoint", points=["S", "C"], points_b=["S", "A", "B"]),
                ]
            },
            "expected_squared": {
                "q1": str(area_sq_triangle(m_sc, PYR["A"], PYR["B"], I3)),
                "q2": str(d2_point_plane(m_sc, PYR["S"], PYR["A"], PYR["B"], I3)),
            },
            "expected_midpoint_constructions": 1,
        },
    ]

    g_sbc = centroid(PYR["S"], PYR["B"], PYR["C"])
    g_prism = centroid(PRISM["A'"], PRISM["B'"], PRISM["C'"])
    q_cent_ab = "Tính diện tích tam giác tạo bởi trọng tâm của tam giác SBC và hai điểm A, B."
    q_cent_ad_rev = "Tính diện tích tam giác tạo bởi hai điểm A, D và trọng tâm của tam giác SBC."
    q_cent_prism = "Tính diện tích tam giác tạo bởi trọng tâm của tam giác A'B'C' và hai điểm A, B."
    q_cent_hd = "Tính diện tích tam giác tạo bởi trọng tâm của tam giác SBC và hai điểm H, D."

    discovery = [
        {
            "id": "pyramid-centroid-area-AB",
            "slice": "A_area_discovery",
            "composition": "centroid->ask_area",
            "text": " ".join([*PYR_TEXT, q_cent_ab]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [f("q", "question", q_cent_ab, role="question", quantity="area", point_kind="centroid", points=["S", "B", "C"], points_b=["A", "B"])]
            },
            "expected_squared": {"q": str(area_sq_triangle(g_sbc, PYR["A"], PYR["B"], I3))},
        },
        {
            "id": "pyramid-centroid-area-AD-reversed-wording",
            "slice": "A_area_discovery",
            "composition": "centroid->ask_area",
            "text": " ".join([*PYR_TEXT, q_cent_ad_rev]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [f("q", "question", q_cent_ad_rev, role="question", quantity="area", point_kind="centroid", points=["S", "B", "C"], points_b=["A", "D"])]
            },
            "expected_squared": {"q": str(area_sq_triangle(g_sbc, PYR["A"], PYR["D"], I3))},
        },
        {
            "id": "prism-centroid-area",
            "slice": "A_area_discovery",
            "composition": "centroid->ask_area",
            "text": " ".join([*PRISM_TEXT, q_cent_prism]),
            "payload": {
                "facts": deepcopy(PRISM_FACTS)
                + [f("q", "question", q_cent_prism, role="question", quantity="area", point_kind="centroid", points=["A'", "B'", "C'"], points_b=["A", "B"])]
            },
            "expected_squared": {"q": str(area_sq_triangle(g_prism, PRISM["A"], PRISM["B"], PRISM_G))},
        },
        {
            "id": "pyramid-projection-and-unnamed-centroid-area",
            "slice": "A_area_discovery",
            "composition": "orthogonal_projection_line+centroid->ask_area",
            "text": " ".join([*PYR_TEXT, proj_line_q, q_cent_hd]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [
                    f("fp", "projection", proj_line_q, point="A", at="H", points=["S", "B"]),
                    f("q", "question", q_cent_hd, role="question", quantity="area", point_kind="centroid", points=["S", "B", "C"], points_b=["H", "D"]),
                ]
            },
            "expected_squared": {"q": str(area_sq_triangle(g_sbc, h_a_sb, PYR["D"], I3))},
        },
    ]

    # Held-out cases
    m_tetra_cd = mid(TETRA["C"], TETRA["D"])
    q_tetra = "Tính diện tích tam giác tạo bởi trung điểm của CD và hai điểm A, B."
    m_reg_sd = mid(REG_PYR["S"], REG_PYR["D"])
    q_reg_pyr = "Tính diện tích tam giác tạo bởi trung điểm của SD và hai điểm A, B."
    h_cuboid_bd = project_point_line(CUBOID["A"], CUBOID["B'"], CUBOID["D'"], I3)
    m_cuboid_cd = mid(CUBOID["C'"], CUBOID["D'"])
    proj_cuboid_q = "Gọi H là hình chiếu vuông góc của A lên B'D'."
    q_cuboid_held = "Tính diện tích tam giác tạo bởi trung điểm của C'D' và hai điểm H, A."
    m_prism_ab = mid(PRISM["A'"], PRISM["B'"])
    q_prism_held = "Tính diện tích tam giác tạo bởi hai điểm C, C' và trung điểm của A'B'."

    held_out = [
        {
            "id": "heldout-tetrahedron-midpoint-area",
            "slice": "A_area_held_out",
            "text": " ".join([*TETRA_TEXT, q_tetra]),
            "payload": {
                "facts": deepcopy(TETRA_FACTS)
                + [f("q", "question", q_tetra, role="question", quantity="area", point_kind="midpoint", points=["C", "D"], points_b=["A", "B"])]
            },
            "expected_squared": {"q": str(area_sq_triangle(m_tetra_cd, TETRA["A"], TETRA["B"], TETRA_G))},
        },
        {
            "id": "heldout-regular-pyramid-midpoint-area",
            "slice": "A_area_held_out",
            "text": " ".join([*REG_PYR_TEXT, q_reg_pyr]),
            "payload": {
                "facts": deepcopy(REG_PYR_FACTS)
                + [f("q", "question", q_reg_pyr, role="question", quantity="area", point_kind="midpoint", points=["S", "D"], points_b=["A", "B"])]
            },
            "expected_squared": {"q": str(area_sq_triangle(m_reg_sd, REG_PYR["A"], REG_PYR["B"], REG_PYR_G))},
        },
        {
            "id": "heldout-cuboid-projection-and-midpoint-area",
            "slice": "A_area_held_out",
            "text": " ".join([*CUBOID_TEXT, proj_cuboid_q, q_cuboid_held]),
            "payload": {
                "facts": deepcopy(CUBOID_FACTS)
                + [
                    f("fp", "projection", proj_cuboid_q, point="A", at="H", points=["B'", "D'"]),
                    f("q", "question", q_cuboid_held, role="question", quantity="area", point_kind="midpoint", points=["C'", "D'"], points_b=["H", "A"]),
                ]
            },
            "expected_squared": {"q": str(area_sq_triangle(m_cuboid_cd, h_cuboid_bd, CUBOID["A"], I3))},
        },
        {
            "id": "heldout-prism-midpoint-area-reversed",
            "slice": "A_area_held_out",
            "text": " ".join([*PRISM_TEXT, q_prism_held]),
            "payload": {
                "facts": deepcopy(PRISM_FACTS)
                + [f("q", "question", q_prism_held, role="question", quantity="area", point_kind="midpoint", points=["A'", "B'"], points_b=["C", "C'"])]
            },
            "expected_squared": {"q": str(area_sq_triangle(m_prism_ab, PRISM["C"], PRISM["C'"], PRISM_G))},
        },
    ]

    # Vertical Slice B: ANGLE LINE-PLANE (named derived points + schema blocker for unnamed point_kind)
    m_sd = mid(PYR["S"], PYR["D"])
    angle_line_plane_slice_b = [
        {
            "id": "angle-90deg-perpendicular-line-plane",
            "slice": "B_angle_line_plane",
            "angle_regime": "90_deg",
            "text": " ".join([*PYR_TEXT, "Gọi M là trung điểm của AB.", "Tính góc giữa SA và (ABCD)."]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [
                    f("fm", "point_def", "Gọi M là trung điểm của AB.", point="M", point_kind="midpoint", points=["A", "B"]),
                    f("q", "question", "Tính góc giữa SA và (ABCD).", role="question", quantity="angle", points_a=["S", "A"], points_b=list("ABCD")),
                ]
            },
            "expected_cos_sq": {"q": str(cos_sq_line_plane(PYR["S"], PYR["A"], PYR["A"], PYR["B"], PYR["C"], I3))},
            "expected_sin_sq": {"q": str(sin_sq_line_plane(PYR["S"], PYR["A"], PYR["A"], PYR["B"], PYR["C"], I3))},
        },
        {
            "id": "angle-0deg-parallel-midline-plane",
            "slice": "B_angle_line_plane",
            "angle_regime": "0_deg",
            "text": " ".join([*PYR_TEXT, "Gọi M là trung điểm của SC.", "Gọi N là trung điểm của SD.", "Tính góc giữa MN và (ABCD)."]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [
                    f("fm", "point_def", "Gọi M là trung điểm của SC.", point="M", point_kind="midpoint", points=["S", "C"]),
                    f("fn", "point_def", "Gọi N là trung điểm của SD.", point="N", point_kind="midpoint", points=["S", "D"]),
                    f("q", "question", "Tính góc giữa MN và (ABCD).", role="question", quantity="angle", points_a=["M", "N"], points_b=list("ABCD")),
                ]
            },
            "expected_cos_sq": {"q": str(cos_sq_line_plane(m_sc, m_sd, PYR["A"], PYR["B"], PYR["C"], I3))},
            "expected_sin_sq": {"q": str(sin_sq_line_plane(m_sc, m_sd, PYR["A"], PYR["B"], PYR["C"], I3))},
        },
        {
            "id": "angle-oblique-midpoint-line-plane",
            "slice": "B_angle_line_plane",
            "angle_regime": "oblique",
            "text": " ".join([*PYR_TEXT, "Gọi M là trung điểm của SC.", "Tính góc giữa AM và (ABCD)."]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [
                    f("fm", "point_def", "Gọi M là trung điểm của SC.", point="M", point_kind="midpoint", points=["S", "C"]),
                    f("q", "question", "Tính góc giữa AM và (ABCD).", role="question", quantity="angle", points_a=["A", "M"], points_b=list("ABCD")),
                ]
            },
            "expected_cos_sq": {"q": str(cos_sq_line_plane(PYR["A"], m_sc, PYR["A"], PYR["B"], PYR["C"], I3))},
            "expected_sin_sq": {"q": str(sin_sq_line_plane(PYR["A"], m_sc, PYR["A"], PYR["B"], PYR["C"], I3))},
        },
        {
            "id": "angle-oblique-centroid-line-plane",
            "slice": "B_angle_line_plane",
            "angle_regime": "oblique",
            "text": " ".join([*PYR_TEXT, "Gọi G là trọng tâm của tam giác SBC.", "Tính góc giữa AG và (ABCD)."]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [
                    f("fg", "point_def", "Gọi G là trọng tâm của tam giác SBC.", point="G", point_kind="centroid", points=["S", "B", "C"]),
                    f("q", "question", "Tính góc giữa AG và (ABCD).", role="question", quantity="angle", points_a=["A", "G"], points_b=list("ABCD")),
                ]
            },
            "expected_cos_sq": {"q": str(cos_sq_line_plane(PYR["A"], g_sbc, PYR["A"], PYR["B"], PYR["C"], I3))},
            "expected_sin_sq": {"q": str(sin_sq_line_plane(PYR["A"], g_sbc, PYR["A"], PYR["B"], PYR["C"], I3))},
        },
        {
            "id": "angle-oblique-projection-line-plane",
            "slice": "B_angle_line_plane",
            "angle_regime": "oblique",
            "text": " ".join([*PYR_TEXT, proj_line_q, "Tính góc giữa HC và (ABCD)."]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [
                    f("fp", "projection", proj_line_q, point="A", at="H", points=["S", "B"]),
                    f("q", "question", "Tính góc giữa HC và (ABCD).", role="question", quantity="angle", points_a=["H", "C"], points_b=list("ABCD")),
                ]
            },
            "expected_cos_sq": {"q": str(cos_sq_line_plane(h_a_sb, PYR["C"], PYR["A"], PYR["B"], PYR["C"], I3))},
            "expected_sin_sq": {"q": str(sin_sq_line_plane(h_a_sb, PYR["C"], PYR["A"], PYR["B"], PYR["C"], I3))},
        },
    ]

    # Fail-closed negatives
    q_collinear_unnamed = "Tính diện tích tam giác tạo bởi trung điểm của SC và hai điểm S, C."
    q_collinear_named = "Tính diện tích tam giác SMC."
    q_unnamed_angle = "Tính góc giữa đường thẳng đi qua trung điểm của SC và A với (ABCD)."

    negative = [
        {
            "id": "collinear-triangle-unnamed-midpoint",
            "text": " ".join([*PYR_TEXT, q_collinear_unnamed]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [f("q", "question", q_collinear_unnamed, role="question", quantity="area", point_kind="midpoint", points=["S", "C"], points_b=["S", "C"])]
            },
            "expected_codes": ["COLLINEAR_POINTS"],
        },
        {
            "id": "collinear-triangle-named-midpoint",
            "text": " ".join([*PYR_TEXT, "Gọi M là trung điểm của SC.", q_collinear_named]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [
                    f("fm", "point_def", "Gọi M là trung điểm của SC.", point="M", point_kind="midpoint", points=["S", "C"]),
                    f("q", "question", q_collinear_named, role="question", quantity="area", points=["S", "M", "C"]),
                ]
            },
            "expected_codes": ["COLLINEAR_POINTS"],
        },
        {
            "id": "underdetermined-metric",
            "text": " ".join([*PYR_TEXT[:3], q_pyr_ab]),
            "payload": {
                "facts": deepcopy(PYR_FACTS[:3])
                + [f("q", "question", q_pyr_ab, role="question", quantity="area", point_kind="midpoint", points=["S", "C"], points_b=["A", "B"])]
            },
            "expected_codes": ["MISSING_DIMENSION", "UNDERDETERMINED_POINT"],
        },
        {
            "id": "contradictory-facts",
            "text": " ".join([*PYR_TEXT, "SA = 4.", q_pyr_ab]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [
                    f("f_conflict", "length", "SA = 4.", points=["S", "A"], measure="segment", value="4"),
                    f("q", "question", q_pyr_ab, role="question", quantity="area", point_kind="midpoint", points=["S", "C"], points_b=["A", "B"]),
                ]
            },
            "expected_codes": ["INCONSISTENT_FACTS"],
        },
        {
            "id": "ambiguous-fact",
            "text": " ".join([*PYR_TEXT, q_pyr_ab]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [f("q", "question", q_pyr_ab, role="question", quantity="area", point_kind="midpoint", points=["S", "C"], points_b=["A", "B"], ambiguous=True)]
            },
            "expected_codes": ["AMBIGUOUS_FACT"],
        },
        {
            "id": "conditional-question",
            "text": " ".join([*PYR_TEXT, q_pyr_ab]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [f("q", "question", q_pyr_ab, role="condition", quantity="area", point_kind="midpoint", points=["S", "C"], points_b=["A", "B"])]
            },
            "expected_codes": ["CONDITIONAL_CLAUSE"],
        },
        {
            "id": "prove-role",
            "text": " ".join([*PYR_TEXT, q_pyr_ab]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [f("q", "question", q_pyr_ab, role="prove", quantity="area", point_kind="midpoint", points=["S", "C"], points_b=["A", "B"])]
            },
            "expected_codes": ["GOAL_CLAUSE_NOT_PREMISE"],
        },
        {
            "id": "negated-question",
            "text": " ".join([*PYR_TEXT, q_pyr_ab]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [f("q", "question", q_pyr_ab, role="question", quantity="area", point_kind="midpoint", points=["S", "C"], points_b=["A", "B"], negated=True)]
            },
            "expected_codes": ["NEGATED_CLAUSE"],
        },
        {
            "id": "missing-target-point",
            "text": " ".join([*PYR_TEXT, q_pyr_ab]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [f("q", "question", q_pyr_ab, role="question", quantity="area", point_kind="midpoint", points=["S", "C"], points_b=["A"])]
            },
            "expected_codes": ["FACT_INCOMPLETE"],
        },
        {
            "id": "extra-target-point",
            "text": " ".join([*PYR_TEXT, q_pyr_ab]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [f("q", "question", q_pyr_ab, role="question", quantity="area", point_kind="midpoint", points=["S", "C"], points_b=["A", "B", "D"])]
            },
            "expected_codes": ["FACT_INCOMPLETE"],
        },
        {
            "id": "duplicate-target-point",
            "text": " ".join([*PYR_TEXT, q_pyr_ab]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [f("q", "question", q_pyr_ab, role="question", quantity="area", point_kind="midpoint", points=["S", "C"], points_b=["A", "A"])]
            },
            "expected_codes": ["FACT_INCOMPLETE"],
        },
        {
            "id": "duplicate-descriptor-point",
            "text": " ".join([*PYR_TEXT, q_pyr_ab]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [f("q", "question", q_pyr_ab, role="question", quantity="area", point_kind="midpoint", points=["S", "S"], points_b=["A", "B"])]
            },
            "expected_codes": ["FACT_INCOMPLETE"],
        },
        {
            "id": "wrong-source-target",
            "text": " ".join([*PYR_TEXT, q_pyr_ab]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [f("q", "question", q_pyr_ab, role="question", quantity="area", point_kind="midpoint", points=["S", "C"], points_b=["A", "D"])]
            },
            "expected_codes": ["SOURCE_OBJECT_MISMATCH"],
        },
        {
            "id": "wrong-source-descriptor",
            "text": " ".join([*PYR_TEXT, q_pyr_ab]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [f("q", "question", q_pyr_ab, role="question", quantity="area", point_kind="midpoint", points=["S", "B"], points_b=["A", "B"])]
            },
            "expected_codes": ["SOURCE_OBJECT_MISMATCH"],
        },
        {
            "id": "unknown-label-in-target",
            "text": " ".join([*PYR_TEXT, q_pyr_ab]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [f("q", "question", q_pyr_ab, role="question", quantity="area", point_kind="midpoint", points=["S", "C"], points_b=["A", "Z"])]
            },
            "expected_codes": ["UNKNOWN_LABEL", "SOURCE_OBJECT_MISMATCH", "UNSUPPORTED_CAPABILITY"],
        },
        {
            "id": "unread-second-ask",
            "text": " ".join([*PYR_TEXT, q_pyr_ab + " Tính diện tích tam giác tạo bởi trung điểm của SC và hai điểm A, D."]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [
                    f(
                        "q",
                        "question",
                        q_pyr_ab + " Tính diện tích tam giác tạo bởi trung điểm của SC và hai điểm A, D.",
                        role="question",
                        quantity="area",
                        point_kind="midpoint",
                        points=["S", "C"],
                        points_b=["A", "B"],
                    )
                ]
            },
            "expected_codes": ["REQUEST_NOT_ANSWERED", "QUESTION_CONTEXT_UNSUPPORTED", "NOT_ASKED_IN_SOURCE"],
        },
        {
            "id": "unnamed-angle-line-plane-blocker",
            "blocker": "SCHEMA_REPRESENTATION_BLOCKER",
            "text": " ".join([*PYR_TEXT, q_unnamed_angle]),
            "payload": {
                "facts": deepcopy(PYR_FACTS)
                + [
                    f(
                        "q",
                        "question",
                        q_unnamed_angle,
                        role="question",
                        quantity="angle",
                        point_kind="midpoint",
                        points=["S", "C"],
                        points_b=["A", "A", "B", "C"],
                    )
                ]
            },
            "expected_codes": ["UNSUPPORTED_CAPABILITY", "SCHEMA_INVALID"],
        },
    ]

    return {
        "run": "contract-driven-goal-composition",
        "status": "DEVELOPMENT_AND_HELD_OUT_SPLITS",
        "slice_b_unnamed_status": "SCHEMA_REPRESENTATION_BLOCKER",
        "positive": positive,
        "discovery": discovery,
        "held_out": held_out,
        "angle_line_plane_slice_b": angle_line_plane_slice_b,
        "negative": negative,
    }


if __name__ == "__main__":
    out = RUN / "corpus.json"
    if out.exists():
        raise SystemExit("refusing to overwrite registered corpus")
    data = make_corpus()
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print({k: len(v) for k, v in data.items() if isinstance(v, list)})
