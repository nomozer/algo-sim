"""Independent oracle + preregistered corpus for run `goal-directed-function-discovery`.

Run once, before any product change:  python oracle.py  →  writes corpus.json next to this file.

Independence: never imports `app` (engine, planner, kernel, registry). Points live in an affine frame with an explicit Gram
matrix G (identity for Euclidean figures); every expected value is a SQUARED distance computed with `Fraction` from the
definitions below (midpoint, centroid, plane covector, intersection line by covectors, Gram minimisation). Expected refusal
codes come from the repository's refusal policy, written before the planner is changed; they are never copied from output.
Corpus status: DEVELOPMENT, NOT_HELD_OUT (the author designed the slice and the cases together).
"""
from __future__ import annotations

import json
from fractions import Fraction as F
from pathlib import Path

# ── exact affine/Gram geometry ───────────────────────────────────────────────────────────────────────────────────────
I3 = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


def v(*xs):
    return tuple(F(x) for x in xs)


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def scale(k, a):
    return tuple(F(k) * x for x in a)


def g(a, b, G):
    return sum(a[i] * F(G[i][j]) * b[j] for i in range(3) for j in range(3))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def det3(m):
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def mid(a, b):
    return scale(F(1, 2), add(a, b))


def centroid(a, b, c):
    return scale(F(1, 3), add(add(a, b), c))


def d2_point_plane(p, a, b, c, G):
    """det Gram(u, v, w) / det Gram(u, v): squared height of the parallelepiped over the parallelogram."""
    u, w_, x = sub(b, a), sub(c, a), sub(p, a)
    vs = (u, w_, x)
    m3 = [[g(s, t, G) for t in vs] for s in vs]
    m2 = m3[0][0] * m3[1][1] - m3[0][1] * m3[1][0]
    return det3(m3) / m2


def d2_point_line(p, a, d, G):
    w_ = sub(p, a)
    return g(w_, w_, G) - g(w_, d, G) ** 2 / g(d, d, G)


def plane_line(a1, b1, c1, a2, b2, c2):
    """Intersection line of planes (a1 b1 c1), (a2 b2 c2) by affine covectors (metric-free)."""
    n1, n2 = cross(sub(b1, a1), sub(c1, a1)), cross(sub(b2, a2), sub(c2, a2))
    d = cross(n1, n2)
    assert any(d), "parallel planes"
    k = max(range(3), key=lambda i: abs(d[i]))          # fix coordinate k = 0, solve the other two
    i, j = [t for t in range(3) if t != k]
    r1, r2 = dot(n1, a1), dot(n2, a2)
    den = n1[i] * n2[j] - n1[j] * n2[i]
    x = [F(0)] * 3
    x[i] = (r1 * n2[j] - r2 * n1[j]) / den
    x[j] = (n1[i] * r2 - n2[i] * r1) / den
    p = tuple(x)
    assert dot(n1, p) == r1 and dot(n2, p) == r2
    return p, d


# ── figures (coordinates are the oracle's own choice, never the engine's layout) ────────────────────────────────────
PYR = {"A": v(0, 0, 0), "B": v(2, 0, 0), "C": v(2, 2, 0), "D": v(0, 2, 0), "S": v(0, 0, 3)}
CUBE = {n: v(x, y, z) for n, (x, y, z) in {"A": (0, 0, 0), "B": (2, 0, 0), "C": (2, 2, 0), "D": (0, 2, 0),
                                           "A'": (0, 0, 2), "B'": (2, 0, 2), "C'": (2, 2, 2), "D'": (0, 2, 2)}.items()}
CUBOID = {n: v(x, y, z) for n, (x, y, z) in {"A": (0, 0, 0), "B": (2, 0, 0), "C": (2, 4, 0), "D": (0, 4, 0),
                                             "A'": (0, 0, 3), "B'": (2, 0, 3), "C'": (2, 4, 3), "D'": (0, 4, 3)}.items()}
# Right prism, equilateral base of side 2, AA' = 3: affine frame u = AB, v = AC, w = AA' with Gram diag blocks.
PRISM_G = ((4, 2, 0), (2, 4, 0), (0, 0, 9))
PRISM = {n: v(x, y, z) for n, (x, y, z) in {"A": (0, 0, 0), "B": (1, 0, 0), "C": (0, 1, 0),
                                            "A'": (0, 0, 1), "B'": (1, 0, 1), "C'": (0, 1, 1)}.items()}


def answers():
    P, Q = PYR, CUBE
    m_sc = mid(P["S"], P["C"])
    g_sbc = centroid(P["S"], P["B"], P["C"])
    sab_scd = plane_line(P["S"], P["A"], P["B"], P["S"], P["C"], P["D"])
    abb_bcc = plane_line(CUBOID["A"], CUBOID["B"], CUBOID["B'"], CUBOID["B"], CUBOID["C"], CUBOID["C'"])
    return {
        "pyr-midpoint-to-plane": d2_point_plane(m_sc, P["S"], P["A"], P["B"], I3),
        "pyr-midpoint-to-named-line": d2_point_line(m_sc, P["B"], sub(P["D"], P["B"]), I3),
        "pyr-midpoint-to-result-line": d2_point_line(m_sc, *sab_scd, I3),
        "cube-midpoint-to-plane": d2_point_plane(mid(Q["C'"], Q["D'"]), Q["A'"], Q["B"], Q["D"], I3),
        "cuboid-midpoint-to-result-line": d2_point_line(mid(CUBOID["A'"], CUBOID["C'"]), *abb_bcc, I3),
        "prism-midpoint-to-plane": d2_point_plane(mid(PRISM["B'"], PRISM["C'"]), PRISM["A"], PRISM["B"], PRISM["B'"], PRISM_G),
        "pyr-reuse-named-midpoint": d2_point_plane(m_sc, P["S"], P["A"], P["B"], I3),
        "pyr-two-goals-shared-point": {"q1": d2_point_plane(m_sc, P["S"], P["A"], P["B"], I3),
                                       "q2": d2_point_line(m_sc, P["B"], sub(P["D"], P["B"]), I3)},
        "pyr-zero-distance": d2_point_plane(mid(P["A"], P["B"]), P["S"], P["A"], P["B"], I3),
        # discovery (experimental registry only)
        "centroid-to-plane": d2_point_plane(g_sbc, P["S"], P["A"], P["D"], I3),
        "centroid-to-named-line": d2_point_line(g_sbc, P["A"], sub(P["D"], P["A"]), I3),
        "centroid-to-result-line": d2_point_line(g_sbc, *sab_scd, I3),
    }


# ── texts and verified Typed Facts (one fact per clause; quotes = the clause sentence) ──────────────────────────────
def f(fid, kind, quote, role="premise", **kw):
    return {"id": fid, "kind": kind, "role": role, "quotes": [quote], **kw}


PYR_TEXT = ["Cho hình chóp S.ABCD.", "Đáy ABCD là hình vuông cạnh 2.", "SA vuông góc với (ABCD).", "SA = 3."]
PYR_FACTS = [f("f1", "solid", PYR_TEXT[0], solid="S.ABCD", solid_type="pyramid"),
             f("f2", "polygon_shape", PYR_TEXT[1], points=list("ABCD"), shape="square", value="2"),
             f("f3", "perpendicular", PYR_TEXT[2], points_a=["S", "A"], points_b=list("ABCD")),
             f("f4", "length", PYR_TEXT[3], points=["S", "A"], measure="segment", value="3")]
CUBE_TEXT = ["Cho hình lập phương ABCD.A'B'C'D' cạnh 2."]
CUBE_FACTS = [f("f1", "solid", CUBE_TEXT[0], solid="ABCD.A'B'C'D'", solid_type="cube"),
              f("f2", "length", CUBE_TEXT[0], solid="ABCD.A'B'C'D'", measure="edge", value="2")]
CUBOID_TEXT = ["Cho hình hộp chữ nhật ABCD.A'B'C'D'.", "AB = 2.", "AD = 4.", "AA' = 3."]
CUBOID_FACTS = [f("f1", "solid", CUBOID_TEXT[0], solid="ABCD.A'B'C'D'", solid_type="cuboid"),
                f("f2", "length", CUBOID_TEXT[1], points=["A", "B"], value="2", measure="segment"),
                f("f3", "length", CUBOID_TEXT[2], points=["A", "D"], value="4", measure="segment"),
                f("f4", "length", CUBOID_TEXT[3], points=["A", "A'"], value="3", measure="segment")]
PRISM_TEXT = ["Cho lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều ABC cạnh 2.", "AA' = 3."]
PRISM_FACTS = [f("f1", "solid", PRISM_TEXT[0], solid="ABC.A'B'C'", solid_type="prism", right=True),
               f("f2", "polygon_shape", PRISM_TEXT[0], points=["A", "B", "C"], shape="equilateral_triangle", value="2"),
               f("f3", "length", PRISM_TEXT[1], points=["A", "A'"], value="3", measure="segment")]


def ask(fid, quote, desc_kind, desc_points, *, plane=None, line=None, line_ref=None, role="question", **kw):
    """Distance question whose FIRST operand is an UNNAMED derived point: `point_kind` + `points` (no `points_a`)."""
    target = {"points_b": list(plane)} if plane else {"points_b": list(line)} if line else {"line_ref": line_ref}
    return f(fid, "question", quote, role=role, quantity="distance", point_kind=desc_kind, points=list(desc_points),
             **target, **kw)


def gt(fid, quote, a, b):
    return f(fid, "intersection_line", quote, points_a=list(a), points_b=list(b))


def case(cid, text, facts, **expect):
    return {"id": cid, "text": " ".join(text), "payload": {"facts": facts}, **expect}


def build():
    ans = answers()
    sq = lambda k: str(ans[k])                                                       # noqa: E731
    q_plane = "Tính khoảng cách từ trung điểm của SC đến (SAB)."
    q_line = "Tính khoảng cách từ trung điểm của SC đến BD."
    gt_pyr = "Tìm giao tuyến của (SAB) và (SCD)."
    q_res = "Tính khoảng cách từ trung điểm của SC đến giao tuyến của (SAB) và (SCD)."
    positive = [
        case("pyr-midpoint-to-plane", PYR_TEXT + [q_plane], PYR_FACTS + [ask("q", q_plane, "midpoint", "SC", plane="SAB")],
             expected_squared={"q": sq("pyr-midpoint-to-plane")}, target="plane"),
        case("pyr-midpoint-to-named-line", PYR_TEXT + [q_line], PYR_FACTS + [ask("q", q_line, "midpoint", "SC", line="BD")],
             expected_squared={"q": sq("pyr-midpoint-to-named-line")}, target="named_line"),
        case("pyr-midpoint-to-result-line", PYR_TEXT + [gt_pyr, q_res],
             PYR_FACTS + [gt("g", gt_pyr, "SAB", "SCD"), ask("q", q_res, "midpoint", "SC", line_ref="g")],
             expected_squared={"q": sq("pyr-midpoint-to-result-line")}, target="result_line"),
        case("cube-midpoint-to-plane", CUBE_TEXT + ["Tính khoảng cách từ trung điểm của C'D' đến (A'BD)."],
             CUBE_FACTS + [ask("q", "Tính khoảng cách từ trung điểm của C'D' đến (A'BD).", "midpoint", ["C'", "D'"],
                               plane=["A'", "B", "D"])],
             expected_squared={"q": sq("cube-midpoint-to-plane")}, target="plane"),
        case("cuboid-midpoint-to-result-line",
             CUBOID_TEXT + ["Tìm giao tuyến của (ABB') và (BCC').",
                            "Tính khoảng cách từ trung điểm của A'C' đến giao tuyến của (ABB') và (BCC')."],
             CUBOID_FACTS + [gt("g", "Tìm giao tuyến của (ABB') và (BCC').", ["A", "B", "B'"], ["B", "C", "C'"]),
                             ask("q", "Tính khoảng cách từ trung điểm của A'C' đến giao tuyến của (ABB') và (BCC').",
                                 "midpoint", ["A'", "C'"], line_ref="g")],
             expected_squared={"q": sq("cuboid-midpoint-to-result-line")}, target="result_line"),
        case("prism-midpoint-to-plane", PRISM_TEXT + ["Tính khoảng cách từ trung điểm của B'C' đến (ABB')."],
             PRISM_FACTS + [ask("q", "Tính khoảng cách từ trung điểm của B'C' đến (ABB').", "midpoint", ["B'", "C'"],
                                plane=["A", "B", "B'"])],
             expected_squared={"q": sq("prism-midpoint-to-plane")}, target="plane"),
        case("pyr-reuse-named-midpoint", PYR_TEXT + ["Gọi M là trung điểm SC.", q_plane],
             PYR_FACTS + [f("fm", "point_def", "Gọi M là trung điểm SC.", point="M", point_kind="midpoint", points=["S", "C"]),
                          ask("q", q_plane, "midpoint", "SC", plane="SAB")],
             expected_squared={"q": sq("pyr-reuse-named-midpoint")}, target="plane", expected_new_points=0),
        case("pyr-two-goals-shared-point", PYR_TEXT + [q_plane, q_line],
             PYR_FACTS + [ask("q1", q_plane, "midpoint", "SC", plane="SAB"), ask("q2", q_line, "midpoint", "SC", line="BD")],
             expected_squared={k: str(x) for k, x in ans["pyr-two-goals-shared-point"].items()}, target="plane+named_line",
             expected_midpoint_constructions=1),
        case("pyr-zero-distance", PYR_TEXT + ["Tính khoảng cách từ trung điểm của AB đến (SAB)."],
             PYR_FACTS + [ask("q", "Tính khoảng cách từ trung điểm của AB đến (SAB).", "midpoint", "AB", plane="SAB")],
             expected_squared={"q": sq("pyr-zero-distance")}, target="plane"),
    ]
    neg = lambda cid, text, facts, codes: case(cid, text, facts, expected_codes=codes)   # noqa: E731
    centroid_q = "Tính khoảng cách từ trọng tâm của tam giác SBC đến (SAD)."
    negative = [
        neg("label-not-in-source", PYR_TEXT + [q_plane], PYR_FACTS + [ask("q", q_plane, "midpoint", ["S", "X"], plane="SAB")],
            ["UNKNOWN_LABEL"]),
        neg("descriptor-operands-mismatch", PYR_TEXT + ["Tính khoảng cách từ trung điểm của SB đến (SAB)."],
            PYR_FACTS + [ask("q", "Tính khoảng cách từ trung điểm của SB đến (SAB).", "midpoint", "SC", plane="SAB")],
            ["SOURCE_OBJECT_MISMATCH"]),
        neg("descriptor-kind-mismatch", PYR_TEXT + ["Tính khoảng cách từ trọng tâm của tam giác SBC đến (SAB)."],
            PYR_FACTS + [ask("q", "Tính khoảng cách từ trọng tâm của tam giác SBC đến (SAB).", "midpoint", "SC", plane="SAB")],
            ["SOURCE_OBJECT_MISMATCH"]),
        neg("conditional-question", PYR_TEXT + ["Nếu SA = 3 thì tính khoảng cách từ trung điểm của SC đến (SAB)."],
            PYR_FACTS + [ask("q", "Nếu SA = 3 thì tính khoảng cách từ trung điểm của SC đến (SAB).", "midpoint", "SC",
                             plane="SAB")],
            ["CONDITIONAL_CLAUSE"]),
        neg("asserted-not-asked", PYR_TEXT + ["Khoảng cách từ trung điểm của SC đến (SAB) bằng 1."],
            PYR_FACTS + [ask("q", "Khoảng cách từ trung điểm của SC đến (SAB) bằng 1.", "midpoint", "SC", plane="SAB")],
            ["NOT_ASKED_IN_SOURCE", "QUESTION_CONTEXT_UNSUPPORTED"]),
        neg("proof-goal", PYR_TEXT + ["Chứng minh rằng khoảng cách từ trung điểm của SC đến (SAB) bằng 1."],
            PYR_FACTS + [ask("q", "Chứng minh rằng khoảng cách từ trung điểm của SC đến (SAB) bằng 1.", "midpoint", "SC",
                             plane="SAB", role="prove")],
            ["GOAL_CLAUSE_NOT_PREMISE"]),
        neg("negated-question", PYR_TEXT + ["Khoảng cách từ trung điểm của SC đến (SAB) không phải là 2."],
            PYR_FACTS + [ask("q", "Khoảng cách từ trung điểm của SC đến (SAB) không phải là 2.", "midpoint", "SC",
                             plane="SAB", negated=True)],
            ["NEGATED_CLAUSE"]),
        neg("centroid-without-contract", PYR_TEXT + [centroid_q],
            PYR_FACTS + [ask("q", centroid_q, "centroid", "SBC", plane="SAD")], ["UNSUPPORTED_CAPABILITY"]),
        neg("named-descriptor", PYR_TEXT + [q_plane],
            PYR_FACTS + [ask("q", q_plane, "midpoint", "SC", plane="SAB", point="M")], ["SCHEMA_INVALID"]),
        neg("descriptor-arity", PYR_TEXT + [q_plane], PYR_FACTS + [ask("q", q_plane, "midpoint", "SBC", plane="SAB")],
            ["FACT_INCOMPLETE"]),
        neg("degenerate-descriptor", PYR_TEXT + ["Tính khoảng cách từ trung điểm của SS đến (SAB)."],
            PYR_FACTS + [ask("q", "Tính khoảng cách từ trung điểm của SS đến (SAB).", "midpoint", "SS", plane="SAB")],
            ["FACT_INCOMPLETE"]),
        neg("underdetermined-figure", PYR_TEXT[:3] + [q_plane], PYR_FACTS[:3] + [ask("q", q_plane, "midpoint", "SC", plane="SAB")],
            ["UNDERDETERMINED_POINT", "MISSING_DIMENSION"]),
        neg("contradictory-givens", PYR_TEXT + ["SB = 5.", q_plane],
            PYR_FACTS + [f("f5", "length", "SB = 5.", points=["S", "B"], measure="segment", value="5"),
                         ask("q", q_plane, "midpoint", "SC", plane="SAB")], ["INCONSISTENT_FACTS"]),
        neg("unread-modifier", PYR_TEXT + ["Tính hai lần khoảng cách từ trung điểm của SC đến (SAB)."],
            PYR_FACTS + [ask("q", "Tính hai lần khoảng cách từ trung điểm của SC đến (SAB).", "midpoint", "SC", plane="SAB")],
            ["NOT_ASKED_IN_SOURCE", "QUESTION_CONTEXT_UNSUPPORTED"]),
        neg("parallel-result-line", CUBE_TEXT + ["Tìm giao tuyến của (ABC) và (A'B'C').",
                                                 "Tính khoảng cách từ trung điểm của AC' đến giao tuyến của (ABC) và (A'B'C')."],
            CUBE_FACTS + [gt("g", "Tìm giao tuyến của (ABC) và (A'B'C').", "ABC", ["A'", "B'", "C'"]),
                          ask("q", "Tính khoảng cách từ trung điểm của AC' đến giao tuyến của (ABC) và (A'B'C').",
                              "midpoint", ["A", "C'"], line_ref="g")],
            ["PARALLEL_NO_INTERSECTION", "PARALLEL_PLANES"]),
        neg("segment-is-not-a-line", PYR_TEXT + ["Tính khoảng cách từ trung điểm của SC đến đoạn BD."],
            PYR_FACTS + [ask("q", "Tính khoảng cách từ trung điểm của SC đến đoạn BD.", "midpoint", "SC", line="BD")],
            ["SOURCE_OBJECT_MISMATCH"]),
    ]
    disc = lambda cid, q, target_kw: case(                                            # noqa: E731
        cid, PYR_TEXT + ([gt_pyr] if "line_ref" in target_kw else []) + [q],
        PYR_FACTS + ([gt("g", gt_pyr, "SAB", "SCD")] if "line_ref" in target_kw else [])
        + [ask("q", q, "centroid", "SBC", **target_kw)], expected_squared={"q": sq(cid)})
    discovery = [
        disc("centroid-to-plane", centroid_q, {"plane": "SAD"}),
        disc("centroid-to-named-line", "Tính khoảng cách từ trọng tâm của tam giác SBC đến AD.", {"line": "AD"}),
        disc("centroid-to-result-line", "Tính khoảng cách từ trọng tâm của tam giác SBC đến giao tuyến của (SAB) và (SCD).",
             {"line_ref": "g"}),
    ]
    return {"run": "goal-directed-function-discovery", "status": "DEVELOPMENT_NOT_HELD_OUT",
            "transport": "question fact: quantity=distance, point_kind + points = unnamed derived first operand "
                         "(no points_a); target = points_b (2 labels line, 3 plane) or line_ref",
            "positive": positive, "negative": negative, "discovery": discovery}


if __name__ == "__main__":
    out = Path(__file__).with_name("corpus.json")
    out.write_text(json.dumps(build(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    c = json.loads(out.read_text(encoding="utf-8"))
    print(len(c["positive"]), "positive,", len(c["negative"]), "negative,", len(c["discovery"]), "discovery")
    for x in c["positive"] + c["discovery"]:
        print(x["id"], x["expected_squared"])
