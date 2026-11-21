# -*- coding: utf-8 -*-
"""Semantic-to-Scene3D — phép dựng của góc khác 90° (`quantity_annotations.gan_dung_goc`).

Mỗi phép dựng được kiểm LẠI ở đây bằng phép tính độc lập với mã dựng: toạ độ chính xác của cảnh + ma trận Gram
`chart_metric` của chính envelope, tích vô hướng viết tay. cos² của góc dựng phải bằng đáp số kernel đã phục vụ;
chân hình chiếu phải nằm trên mặt và đoạn tới chân phải trực giao mặt; tia của góc nhị diện phải trực giao giao tuyến.
"""
from __future__ import annotations

import os
from fractions import Fraction

import pytest

from app.ai.adaptive_input_router import route_text_input
from app.simulation.geometry.exact import Line3, Plane3, Vec3
from app.simulation.semantic_program import quantity_annotations as QA

os.environ.setdefault("ALLOW_LIVE_AI", "0")

P = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "


def _serve(text: str):
    r = route_text_input(text, allow_live_ai=False).response
    rd = r.get("route_d") or {}
    assert rd.get("status") == "SERVED", rd.get("refusal")
    sc = r["envelope"]["scene3d"]
    g = [[Fraction(x) for x in row] for row in sc["chart_metric"]]
    pts = {o["id"]: [Fraction(x) for x in o["xyz"]] for o in sc["objects"] if o["type"] == "point3" and o.get("xyz")}
    q = next(o for o in sc["objects"] if o["type"] == "quantity" and "target" in (o.get("display_group") or []))
    served = Fraction(rd["answers"]["q1"].split("=")[1])
    return sc, g, pts, q, served


def _v(x):
    return [Fraction(c) for c in x]


def _sub(a, b):
    return [x - y for x, y in zip(a, b)]


def _dot(g, u, w):
    return sum(u[i] * g[i][j] * w[j] for i in range(3) for j in range(3))


def _cos2(g, u, w):
    return _dot(g, u, w) ** 2 / (_dot(g, u, u) * _dot(g, w, w))


def _arms(ac):
    o = _v(ac["vertex"])
    return o, _sub(_v(ac["arms"][0]["to"]), o), _sub(_v(ac["arms"][1]["to"]), o)


@pytest.mark.parametrize("text,plane,vertex,ids", [
    (P + "Tính góc giữa đường thẳng SC và mặt phẳng (ABCD).", "ABD", "C", ("S", "A")),
    (P + "Tính góc giữa đường thẳng SC và mặt phẳng (SAB).", "SAB", "S", ("C", "B")),
    ("Cho tứ diện đều ABCD có cạnh bằng a. Tính góc giữa đường thẳng AB và mặt phẳng (BCD).", "BCD", "B", ("A", None)),
])
def test_line_plane_angle_is_the_angle_between_the_line_and_its_orthogonal_projection(text, plane, vertex, ids):
    sc, g, pts, q, served = _serve(text)
    ac = q["angle_construction"]
    assert ac["relation"] == "line_plane" and ac.get("vertex_id") == vertex and ac["arms"][0].get("to_id") == ids[0]
    o, a1, a2 = _arms(ac)
    assert _cos2(g, a1, a2) == served                           # the drawn angle IS the measured one
    p, h = _v(ac["perpendicular"]["from"]), _v(ac["perpendicular"]["foot"])
    x, y, z = (pts[c] for c in plane)
    for d in (_sub(y, x), _sub(z, x)):                          # PH ⟂ plane, in the frame metric
        assert _dot(g, _sub(p, h), d) == 0
    # H on the plane: (H − X) is a combination of the two plane directions ⇔ triple product 0 (affine, metric-free).
    m = [_sub(h, x), _sub(y, x), _sub(z, x)]
    det = (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
           + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))
    assert det == 0 and _v(ac["arms"][1]["to"]) == h
    if ids[1]:
        assert ac["arms"][1].get("to_id") == ids[1] and pts[ids[1]] == h


def test_tetrahedron_runs_in_a_non_euclidean_chart_and_still_certifies():
    sc, g, *_ = _serve("Cho tứ diện đều ABCD có cạnh bằng a. Tính góc giữa đường thẳng AB và mặt phẳng (BCD).")
    assert g != [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def test_intersecting_lines_angle_has_its_vertex_at_the_intersection():
    sc, g, pts, q, served = _serve(P + "Tính góc giữa hai đường thẳng SC và AC.")
    ac = q["angle_construction"]
    assert ac["relation"] == "line_line" and ac["vertex_id"] == "C"
    o, a1, a2 = _arms(ac)
    assert _cos2(g, a1, a2) == served and {ac["arms"][0]["to_id"], ac["arms"][1]["to_id"]} == {"S", "A"}


def test_skew_lines_angle_uses_a_named_parallel_segment():
    sc, g, pts, q, served = _serve("Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. Tính góc giữa hai đường thẳng AC và A'D.")
    ac = q["angle_construction"]
    assert ac["relation"] == "line_line_skew"
    o, a1, a2 = _arms(ac)
    assert _cos2(g, a1, a2) == served
    d2 = _sub(pts["D"], pts["A_prime"])                         # helper ∥ A'D (cross product 0)
    cross = [a2[1] * d2[2] - a2[2] * d2[1], a2[2] * d2[0] - a2[0] * d2[2], a2[0] * d2[1] - a2[1] * d2[0]]
    assert cross == [0, 0, 0] and ac["parallel"]["of"] in {o_["id"] for o_ in sc["objects"]}
    # vertex on AC
    ac_dir, cv = _sub(pts["C"], pts["A"]), _sub(o, pts["A"])
    assert [ac_dir[1] * cv[2] - ac_dir[2] * cv[1], ac_dir[2] * cv[0] - ac_dir[0] * cv[2], ac_dir[0] * cv[1] - ac_dir[1] * cv[0]] == [0, 0, 0]


@pytest.mark.parametrize("text,edge", [
    (P + "Tính góc giữa mặt phẳng (SBC) và mặt phẳng (ABCD).", "BC"),
    ("Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác đều cạnh a, AA' = a. "
     "Tính góc giữa mặt phẳng (A'BC) và mặt phẳng (ABC).", "BC"),
])
def test_dihedral_plane_angle_rays_are_orthogonal_to_the_common_line(text, edge):
    sc, g, pts, q, served = _serve(text)
    ac = q["angle_construction"]
    assert ac["relation"] == "plane_plane"
    o, a1, a2 = _arms(ac)
    e = _sub(pts[edge[1]], pts[edge[0]])
    assert _dot(g, a1, e) == 0 and _dot(g, a2, e) == 0 and _cos2(g, a1, a2) == served


def test_right_angle_keeps_its_angle_witness_and_no_angle_construction():
    sc, g, pts, q, served = _serve(P + "Tính góc giữa đường thẳng SA và mặt phẳng (ABCD).")
    assert served == 0 and "angle_construction" not in q
    assert q["annotation"]["kind"] == "angle" and q["annotation"]["anchor"] == "witness"   # not relabelled as a length


def test_renaming_the_vertices_gives_the_same_construction():
    a = _serve(P + "Tính góc giữa đường thẳng SC và mặt phẳng (ABCD).")[3]["angle_construction"]
    b = _serve("Cho hình chóp T.MNPQ có đáy MNPQ là hình vuông cạnh a, TM vuông góc với mặt phẳng đáy và TM = a. "
               "Tính góc giữa đường thẳng TP và mặt phẳng (MNPQ).")[3]["angle_construction"]
    ren = {"S": "T", "A": "M", "B": "N", "C": "P", "D": "Q"}
    assert b["vertex"] == a["vertex"] and b["perpendicular"] == a["perpendicular"]
    assert b["vertex_id"] == ren[a["vertex_id"]] and [x.get("to_id") for x in b["arms"]] == [ren[x["to_id"]] for x in a["arms"]]


def test_scaled_lengths_give_the_same_construction():
    a = _serve(P + "Tính góc giữa mặt phẳng (SBC) và mặt phẳng (ABCD).")[3]["angle_construction"]
    b = _serve(P.replace("cạnh a", "cạnh 2a").replace("SA = a", "SA = 2a")
               + "Tính góc giữa mặt phẳng (SBC) và mặt phẳng (ABCD).")[3]["angle_construction"]
    assert a == b                                               # homogeneous lengths ⇒ the unit-scale chart is reused


# ── fail-closed: the construction is emitted only when it reproduces the measurement ────────────────────────────────
def _pyramid_memory():
    pts = {"A": Vec3.of(0, 0, 0), "B": Vec3.of(1, 0, 0), "C": Vec3.of(1, 1, 0), "D": Vec3.of(0, 1, 0), "S": Vec3.of(0, 0, 1)}
    mem = dict(pts)
    mem["dt"] = Line3.through(pts["S"], pts["C"])
    mem["mp"] = Plane3.through(pts["A"], pts["B"], pts["C"])
    return mem, [(n, p) for n, p in pts.items()]


def test_wrong_measurement_is_never_drawn():
    mem, co_ten = _pyramid_memory()
    ok = QA._dung_goc("dt", "mp", Fraction(2, 3), mem, {}, co_ten)
    assert isinstance(ok, dict) and ok["relation"] == "line_plane"
    assert isinstance(QA._dung_goc("dt", "mp", Fraction(1, 2), mem, {}, co_ten), str)


def test_degenerate_line_parallel_to_plane_has_no_construction():
    mem, co_ten = _pyramid_memory()
    mem["ss"] = Line3.through(mem["S"], mem["S"] + Vec3.of(1, 0, 0))   # parallel to (ABCD)
    with pytest.raises(Exception):
        QA._dung_goc("ss", "mp", Fraction(1), mem, {}, co_ten)


def test_parallel_lines_and_parallel_planes_have_no_construction():
    mem, co_ten = _pyramid_memory()
    mem["l1"] = Line3.through(mem["A"], mem["B"])
    mem["l2"] = Line3.through(mem["D"], mem["C"])
    assert isinstance(QA._dung_goc("l1", "l2", Fraction(1), mem, {}, co_ten), str)
    mem["p2"] = Plane3.through(mem["S"], mem["S"] + Vec3.of(1, 0, 0), mem["S"] + Vec3.of(0, 1, 0))
    with pytest.raises(Exception):
        QA._dung_goc("mp", "p2", Fraction(1), mem, {}, co_ten)
