"""Geometry capability expansion (run `geometry-capability-expansion`, Hybrid Wave 2B): ratio point on a segment, plane
through a point ⊥ a line + its section, right-trapezoid base, oblique prism. Expected values come from `_E` below — exact
Fractions on coordinates written here (Euclidean or an explicit Gram chart), never from the engine.
"""
from __future__ import annotations

import json
from copy import deepcopy
from fractions import Fraction as F

import pytest

from app.ai.function_route import run_fact_route
from app.simulation.geometry_functions import planner
from app.simulation.geometry_functions.registry import TuChoi


def f(fid, kind, quote, role="premise", **kw):
    return {"id": fid, "kind": kind, "role": role, "quotes": [quote], **kw}


def run(text, facts):
    return run_fact_route(text, {"facts": json.loads(json.dumps(facts))})


def sq(r, q):
    v = r.exec_result.final_memory[f"kq_{q}"]
    if r.answers[q].startswith("cos²="):
        return F(v)
    return F(v.he) ** 2 * v.can if hasattr(v, "can") else F(v) ** 2


class _E:
    """Independent exact oracle on explicit coordinates with Gram matrix G (default Euclidean)."""

    def __init__(self, pts, G=((1, 0, 0), (0, 1, 0), (0, 0, 1))):
        self.p = {k: tuple(F(x) for x in v) for k, v in pts.items()}
        self.G = [[F(x) for x in r] for r in G]

    def v(self, a, b):
        a, b = (self.p[a] if isinstance(a, str) else a), (self.p[b] if isinstance(b, str) else b)
        return tuple(b[i] - a[i] for i in range(3))

    def ip(self, u, w):
        return sum(u[i] * self.G[i][j] * w[j] for i in range(3) for j in range(3))

    def det(self, *vs):
        m = [[self.ip(a, b) for b in vs] for a in vs]
        if len(m) == 2:
            return m[0][0] * m[1][1] - m[0][1] ** 2
        return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
                + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))

    def len2(self, a, b):
        return self.ip(self.v(a, b), self.v(a, b))

    def dist2_line(self, p, a, b):
        u, w = self.v(a, b), self.v(a, p)
        return self.ip(w, w) - self.ip(w, u) ** 2 / self.ip(u, u)

    def dist2_plane(self, p, a, b, c):
        u, w, x = self.v(a, b), self.v(a, c), self.v(a, p)
        return self.det(u, w, x) / self.det(u, w)

    def cos2_line_plane(self, p, q, a, b, c):
        u, w, x = self.v(a, b), self.v(a, c), self.v(p, q)
        return 1 - self.det(u, w, x) / (self.ip(x, x) * self.det(u, w))

    def area2_polygon(self, *ps):                       # convex polygon: fan of triangles from ps[0], Gram areas
        total = F(0)
        for i in range(1, len(ps) - 1):
            total += self.det(self.v(ps[0], ps[i]), self.v(ps[0], ps[i + 1])) / 4
        return total                                     # valid for a TRIANGLE only (one term); polygons use sum of roots


# ── Slice D: oblique prism (W2-EXP-06B, a = 1) ──────────────────────────────────────────────────────────────────────────
D_TEXT = ("Cho lăng trụ ABC.A'B'C' có đáy là tam giác đều ABC cạnh 1. Gọi H là trung điểm của BC. "
          "Hình chiếu vuông góc của A' lên (ABC) là H. AA' = 1. ")
D_Q1 = "Cho lăng trụ ABC.A'B'C' có đáy là tam giác đều ABC cạnh 1."
D_FACTS = [f("f1", "solid", D_Q1, solid="ABC.A'B'C'", solid_type="prism"),
           f("f2", "polygon_shape", D_Q1, points=list("ABC"), shape="equilateral_triangle", value="1"),
           f("h", "point_def", "Gọi H là trung điểm của BC.", point="H", point_kind="midpoint", points=["B", "C"]),
           f("p", "projection", "Hình chiếu vuông góc của A' lên (ABC) là H.", point="A'", points=list("ABC"), at="H"),
           f("l", "length", "AA' = 1.", points=["A", "A'"], measure="segment", value="1")]
# chart: A origin, AB, AC (|AB| = |AC| = 1 at 60°), vertical axis z; H = (1/2, 1/2, 0); A'H² = 1 − AH² = 1/4
D_ORACLE = _E({"A": (0, 0, 0), "B": (1, 0, 0), "C": (0, 1, 0), "H": ("1/2", "1/2", 0), "A'": ("1/2", "1/2", 1),
               "B'": ("3/2", "1/2", 1), "C'": ("1/2", "3/2", 1)},
              ((1, "1/2", 0), ("1/2", 1, 0), (0, 0, "1/4")))


def test_oblique_prism_volume_and_vertex_propagation():
    ask = "Tính thể tích khối lăng trụ ABC.A'B'C'."
    r = run(D_TEXT + ask, D_FACTS + [f("q", "question", ask, role="question", quantity="volume", solid="ABC.A'B'C'")])
    assert r.status == "SERVED", (r.code, r.reason)
    base2 = D_ORACLE.det(D_ORACLE.v("A", "B"), D_ORACLE.v("A", "C")) / 4
    h2 = D_ORACLE.dist2_plane("A'", "A", "B", "C")
    assert sq(r, "q") == base2 * h2 == F(3, 64)
    v = [tuple(r.points[t][i] - r.points[b][i] for i in range(3)) for b, t in (("A", "A'"), ("B", "B'"), ("C", "C'"))]
    assert v[0] == v[1] == v[2] and v[0][2] != 0                   # one lateral vector, off the base plane
    lateral = [o for o in r.scene3d["objects"] if o["type"] == "segment3"
               and {*(o.get("endpoint_ids") or ())} in ({"A", "A_prime"}, {"B", "B_prime"}, {"C", "C_prime"})]
    assert lateral and not any("perpendicular_witness" in o for o in lateral)   # oblique edges carry no right-angle mark


def test_oblique_prism_composes_with_a_described_point_goal():
    ask = "Tính khoảng cách từ trung điểm của B'C' đến (ABC)."
    q = f("q", "question", ask, role="question", quantity="distance", point_kind="midpoint", points=["B'", "C'"],
          points_b=list("ABC"))
    r = run(D_TEXT + ask, D_FACTS + [q])
    assert r.status == "SERVED", (r.code, r.reason)
    m = tuple((D_ORACLE.p["B'"][i] + D_ORACLE.p["C'"][i]) / 2 for i in range(3))
    D_ORACLE.p["Mbc"] = m
    assert sq(r, "q") == D_ORACLE.dist2_plane("Mbc", "A", "B", "C") == F(1, 4)


@pytest.mark.parametrize("name,mutate,code", [
    ("no-top-vertex-fixed", lambda t, fs: (t.replace("Hình chiếu vuông góc của A' lên (ABC) là H. ", ""),
                                           [x for x in fs if x["id"] != "p"]), "UNDERDETERMINED_POINT"),
    ("degenerate-height", lambda t, fs: (t.replace("AA' = 1.", "AA' = √3/2."),
                                         [{**x, "quotes": ["AA' = √3/2."], "value": "√3/2"} if x["id"] == "l" else x
                                          for x in fs]), "INCONSISTENT_FACTS"),
])
def test_oblique_prism_refusals(name, mutate, code):
    ask = "Tính thể tích khối lăng trụ ABC.A'B'C'."
    text, facts = mutate(D_TEXT + ask, D_FACTS + [f("q", "question", ask, role="question", quantity="volume",
                                                    solid="ABC.A'B'C'")])
    r = run(text, facts)
    assert r.status == "REFUSED" and r.code == code, (name, r.code, r.reason)


# ── Slice C: right trapezoid base (W2-EXP-06A, a = 1) ──────────────────────────────────────────────────────────────────
C_Q1 = "Cho hình chóp S.ABCD có đáy ABCD là hình thang vuông tại A và B."
C_TEXT = C_Q1 + " AB = 1. AD = 2. BC = 1. SA vuông góc với (ABCD). SA = 1. "
C_FACTS = [f("f1", "solid", C_Q1, solid="S.ABCD", solid_type="pyramid"),
           f("ra", "right_angle", C_Q1, at="A", points=["B", "D"]),
           f("rb", "right_angle", C_Q1, at="B", points=["A", "C"]),
           f("l1", "length", "AB = 1.", points=["A", "B"], measure="segment", value="1"),
           f("l2", "length", "AD = 2.", points=["A", "D"], measure="segment", value="2"),
           f("l3", "length", "BC = 1.", points=["B", "C"], measure="segment", value="1"),
           f("pp", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=list("ABCD")),
           f("l4", "length", "SA = 1.", points=["S", "A"], measure="segment", value="1")]
C_ORACLE = _E({"A": (0, 0, 0), "B": (1, 0, 0), "C": (1, 1, 0), "D": (0, 2, 0), "S": (0, 0, 1)})


def test_right_trapezoid_base_volume_angle_and_distance():
    asks = ["Tính thể tích khối chóp S.ABCD.", "Tính góc giữa SC và (SAD).", "Tính khoảng cách từ A đến (SCD)."]
    qs = [f("q1", "question", asks[0], role="question", quantity="volume", solid="S.ABCD"),
          f("q2", "question", asks[1], role="question", quantity="angle", points_a=["S", "C"], points_b=["S", "A", "D"]),
          f("q3", "question", asks[2], role="question", quantity="distance", points_a=["A"], points_b=["S", "C", "D"])]
    r = run(C_TEXT + " ".join(asks), C_FACTS + qs)
    assert r.status == "SERVED", (r.code, r.reason)
    E = C_ORACLE
    base = F(1 + 2, 2) * 1                                          # (AD + BC)/2 · AB
    assert sq(r, "q1") == (base * F(1) / 3) ** 2 == F(1, 4)
    assert sq(r, "q2") == E.cos2_line_plane("S", "C", "S", "A", "D") == F(2, 3)
    assert sq(r, "q3") == E.dist2_plane("A", "S", "C", "D") == F(2, 3)


@pytest.mark.parametrize("name,patch,code", [
    ("one-right-angle", lambda fs: [x for x in fs if x["id"] != "rb"], "UNSUPPORTED_BASE_SHAPE"),
    ("missing-BC", lambda fs: [x for x in fs if x["id"] != "l3"], "MISSING_DIMENSION"),
    ("non-consecutive-right-angles", lambda fs: [{**x, "at": "C", "points": ["B", "D"]} if x["id"] == "rb" else x for x in fs],
     "SOURCE_OBJECT_MISMATCH"),
    ("wrong-vertices-vs-source", lambda fs: [{**x, "at": "C", "points": ["B", "D"]} if x["id"] == "ra" else
                                             {**x, "at": "D", "points": ["A", "C"]} if x["id"] == "rb" else x for x in fs],
     "SOURCE_OBJECT_MISMATCH"),
])
def test_right_trapezoid_refusals(name, patch, code):
    ask = "Tính thể tích khối chóp S.ABCD."
    facts = patch(deepcopy(C_FACTS)) + [f("q", "question", ask, role="question", quantity="volume", solid="S.ABCD")]
    text = C_TEXT if any(x["id"] == "l3" for x in facts) else C_TEXT.replace(" BC = 1.", "")   # no unread premise left
    r = run(text + ask, facts)
    assert r.status == "REFUSED", (name, r.answers)
    if code:
        assert r.code == code, (name, r.code, r.reason)


def test_right_trapezoid_irrational_leg_ratio_is_refused_not_approximated():
    text = C_TEXT.replace("BC = 1.", "BC = √2.")
    facts = [{**x, "quotes": ["BC = √2."], "value": "√2"} if x["id"] == "l3" else x for x in C_FACTS]
    ask = "Tính thể tích khối chóp S.ABCD."
    r = run(text + ask, facts + [f("q", "question", ask, role="question", quantity="volume", solid="S.ABCD")])
    assert r.status == "REFUSED" and r.code == "UNSUPPORTED_IRRATIONAL_LAYOUT", (r.code, r.reason)


# ── Slice A: ratio point on a segment (W2-EXP-03, a = 1) ───────────────────────────────────────────────────────────────
A_TEXT = ("Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 1. SA vuông góc với (ABCD). SA = 3. "
          "Gọi M là điểm thuộc cạnh SA sao cho SM = 2MA. Gọi N là trung điểm của BC. ")
A_FACTS = [f("f1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
           f("f2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 1.", points=list("ABCD"), shape="square", value="1"),
           f("f3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=list("ABCD")),
           f("f4", "length", "SA = 3.", points=["S", "A"], measure="segment", value="3"),
           f("m", "point_def", "Gọi M là điểm thuộc cạnh SA sao cho SM = 2MA.", point="M", point_kind="divide_segment",
             points=["S", "A"], value="2/3"),
           f("n", "point_def", "Gọi N là trung điểm của BC.", point="N", point_kind="midpoint", points=["B", "C"])]
A_ORACLE = _E({"A": (0, 0, 0), "B": (1, 0, 0), "C": (1, 1, 0), "D": (0, 1, 0), "S": (0, 0, 3), "M": (0, 0, 1),
               "N": (1, "1/2", 0)})


def test_ratio_point_composes_with_length_and_point_line_distance():
    asks = ["Tính độ dài MN.", "Tính khoảng cách từ M đến DN."]
    qs = [f("q1", "question", asks[0], role="question", quantity="length", points=["M", "N"]),
          f("q2", "question", asks[1], role="question", quantity="distance", points_a=["M"], points_b=["D", "N"])]
    r = run(A_TEXT + " ".join(asks), A_FACTS + qs)
    assert r.status == "SERVED", (r.code, r.reason)
    assert sq(r, "q1") == A_ORACLE.len2("M", "N") == F(9, 4)
    assert sq(r, "q2") == A_ORACLE.dist2_line("M", "D", "N") == F(9, 5)
    assert {c["fn"] for c in r.planner["calls"]} >= {"divide_segment", "orthogonal_projection_line", "ask_length"}
    s, a, m = (r.points[x] for x in "SAM")
    assert all(m[i] == F(1, 3) * s[i] + F(2, 3) * a[i] for i in range(3))     # M = (1 − t)S + tA, t = SM/SA = 2/3


@pytest.mark.parametrize("wording,seg,t", [
    ("SM = 2MA", ["S", "A"], "2/3"),
    ("SM = 2MA", ["A", "S"], "1/3"),            # the same point written from the other end
    ("MA = 2SM", ["S", "A"], "1/3"),
    ("SA = 3SM", ["S", "A"], "1/3"),
    ("AM = 2MS", ["A", "S"], "2/3"),
])
def test_ratio_wordings_bind_the_same_convention(wording, seg, t):
    text = A_TEXT.replace("SM = 2MA", wording)
    facts = [{**x, "quotes": [x["quotes"][0].replace("SM = 2MA", wording)], "points": seg, "value": t}
             if x["id"] == "m" else x for x in A_FACTS]
    ask = "Tính độ dài MN."
    r = run(text + ask, facts + [f("q", "question", ask, role="question", quantity="length", points=["M", "N"])])
    assert r.status == "SERVED", (wording, r.code, r.reason)
    tt = F(t)
    p0, p1 = (A_ORACLE.p[x] for x in seg)
    A_ORACLE.p["Mx"] = tuple((1 - tt) * p0[i] + tt * p1[i] for i in range(3))
    assert sq(r, "q") == A_ORACLE.len2("Mx", "N")


@pytest.mark.parametrize("name,patch,codes", [
    ("ratio-disagrees-with-source", {"value": "1/3"}, {"SOURCE_OBJECT_MISMATCH"}),
    ("ratio-zero", {"value": "0"}, {"SCHEMA_INVALID", "INVALID_RATIO"}),
    ("ratio-one", {"value": "1"}, {"SCHEMA_INVALID", "INVALID_RATIO"}),
    ("ratio-outside", {"value": "3/2"}, {"SCHEMA_INVALID", "INVALID_RATIO"}),
    ("missing-ratio", {"value": None}, {"FACT_INCOMPLETE"}),
    ("same-endpoints", {"points": ["S", "S"]}, {"SCHEMA_INVALID", "DEGENERATE_POINTS", "FACT_INCOMPLETE"}),
    ("other-segment", {"points": ["S", "B"]}, {"SOURCE_OBJECT_MISMATCH"}),
])
def test_ratio_point_fails_closed(name, patch, codes):
    facts = deepcopy(A_FACTS)
    m = next(x for x in facts if x["id"] == "m")
    for k, v in patch.items():
        m.pop(k, None) if v is None else m.__setitem__(k, v)
    ask = "Tính độ dài MN."
    r = run(A_TEXT + ask, facts + [f("q", "question", ask, role="question", quantity="length", points=["M", "N"])])
    assert r.status == "REFUSED" and r.code in codes, (name, r.code, r.reason)


# ── Slice B: plane through a point ⊥ a line, its section (W2-EXP-07, a = 1) ────────────────────────────────────────────
B_Q1 = "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B."
B_DEF = "Dựng mặt phẳng (P) đi qua A và vuông góc với SC."
B_ASK = "Tính diện tích thiết diện của hình chóp S.ABC với (P)."
B_TEXT = f"{B_Q1} AB = 1. BC = 1. SA vuông góc với (ABC). SA = 1. {B_DEF} {B_ASK}"
B_FACTS = [f("f1", "solid", B_Q1, solid="S.ABC", solid_type="pyramid"),
           f("f2", "right_angle", B_Q1, at="B", points=["A", "C"]),
           f("f3", "length", "AB = 1.", points=["A", "B"], measure="segment", value="1"),
           f("f4", "length", "BC = 1.", points=["B", "C"], measure="segment", value="1"),
           f("f5", "perpendicular", "SA vuông góc với (ABC).", points_a=["S", "A"], points_b=list("ABC")),
           f("f6", "length", "SA = 1.", points=["S", "A"], measure="segment", value="1"),
           {"id": "q", "kind": "question", "role": "question", "quotes": [B_DEF, B_ASK], "quantity": "area",
            "solid": "S.ABC", "point": "A", "points_b": ["S", "C"], "plane_relation": "perpendicular"}]
# Euclid: A(0,0,0) B(1,0,0) C(1,1,0) S(0,0,1); (P): x + y − z = 0 cuts SB at (1/2,0,1/2), SC at (1/3,1/3,2/3)
B_ORACLE = _E({"A": (0, 0, 0), "B": (1, 0, 0), "C": (1, 1, 0), "S": (0, 0, 1), "M": ("1/2", 0, "1/2"),
               "N": ("1/3", "1/3", "2/3")})


def test_section_by_plane_through_point_perpendicular_to_line():
    r = run(B_TEXT, B_FACTS)
    assert r.status == "SERVED", (r.code, r.reason)
    E = B_ORACLE
    assert sq(r, "q") == E.det(E.v("A", "M"), E.v("A", "N")) / 4 == F(1, 48)
    sec = [o for o in r.scene3d["objects"] if o["type"] == "section"]
    assert len(sec) == 1
    fns = [c["fn"] for c in r.planner["calls"]]
    assert fns.count("orthogonal_projection_line") == 2 and fns.count("translate_point") == 2   # existing primitives only


def test_plane_perpendicular_to_a_plane_is_still_not_unique():
    facts = deepcopy(B_FACTS)
    facts[-1]["points_b"] = ["S", "B", "C"]
    text = B_TEXT.replace("vuông góc với SC", "vuông góc với (SBC)")
    facts[-1]["quotes"] = [q.replace("vuông góc với SC", "vuông góc với (SBC)") for q in facts[-1]["quotes"]]
    with pytest.raises(TuChoi) as e:
        planner.lap_ke_hoach({"facts": facts}, text)
    assert e.value.code == "PLANE_NOT_UNIQUE"


@pytest.mark.parametrize("name,text_from,text_to,patch,codes", [
    ("wrong-line-vs-source", "vuông góc với SC", "vuông góc với SB", {}, {"SOURCE_OBJECT_MISMATCH"}),
    ("plane-only-touches-apex", "đi qua A và", "đi qua S và", {"point": "S"}, {"PLANE_TOUCHES_VERTEX", "PLANE_DOES_NOT_CUT"}),
    ("point-on-the-line", "đi qua A và", "đi qua C và", {"point": "C"}, {"PLANE_TOUCHES_VERTEX", "PLANE_DOES_NOT_CUT"}),
])
def test_perpendicular_plane_section_fails_closed(name, text_from, text_to, patch, codes):
    facts = deepcopy(B_FACTS)
    facts[-1].update(patch)
    facts[-1]["quotes"] = [q.replace(text_from, text_to) for q in facts[-1]["quotes"]]
    r = run(B_TEXT.replace(text_from, text_to), facts)
    assert r.status == "REFUSED" and r.code in codes, (name, r.code, r.reason)
