"""Slice 1 (run `hybrid-section-slice`): section of a polyhedron by a plane, intersection line of two planes, and the area
of a section — on the Hybrid route, built by the EXISTING shared engine (`construct_section`, `intersect_plane_plane`,
`measure area`), reached through new Registry functions, Typed Fact kinds and planner rules.

Evidence class: offline typed facts (and route-A calls). Oracle: Euclidean coordinates of `hybrid_compiler_benchmark`
(no product import) and hand-derived areas; section vertices are checked against points built from named vertices.
"""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from app.ai.function_route import run_fact_route, run_function_route
from tests.geometry import hybrid_compiler_benchmark as HB

f, ask = HB._f, HB._ask


def _section(fid, quote, plane, solid="S.ABCD", role="question"):
    return f(fid, "section", quote, role=role, solid=solid, points=list(plane))


def _area(quote, plane, solid="S.ABCD"):
    return ask("q", quote, "area", solid=solid, points=list(plane))


def _line(fid, quote, p1, p2, role="question"):
    return f(fid, "intersection_line", quote, role=role, points_a=list(p1), points_b=list(p2))


def _run(*extra, base=None):
    q, facts = HB._with(base or HB._square(), *extra)
    return run_fact_route(" ".join(q), {"facts": facts})


def _section_obj(r):
    (o,) = [o for o in r.scene3d["objects"] if o["type"] == "section"]
    return o


def _vertices(r):
    """Section polygon in chart coordinates, from the executed program."""
    var = _section_obj(r)["id"]
    return {(p.x, p.y, p.z) for p in r.exec_result.final_memory[var].polygon}


def _pt(r, *names):
    """Mean of named engine points (midpoint for two names)."""
    ps = [r.points[n] for n in names]
    return tuple(sum(p[i] for p in ps) / len(ps) for i in range(3))


# ── sections ───────────────────────────────────────────────────────────────────────────────────────────────────

def test_section_by_plane_through_an_edge_and_a_midpoint():
    """(MAB), M = mid SC: AB ∥ CD ⇒ the plane meets (SCD) in MN ∥ CD, N = mid SD — trapezoid A, B, M, N.
    Area (Euclid): bases AB = 2, MN = 1, height dist(AB, MN) = |(0,1,3/2)| = √13/2 ⇒ S = 3√13/4, S² = 117/16."""
    r = _run(HB._mid("f5", "M", "S", "C"), _section("f6", "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB).", "MAB"),
             _area("Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB).", "MAB"))
    assert r.status == "SERVED", (r.code, r.reason)
    assert _vertices(r) == {r.points["A"], r.points["B"], _pt(r, "S", "C"), _pt(r, "S", "D")}
    assert HB.answer_square(r.answers["q"]) == F(117, 16)
    assert _section_obj(r)["render"] == "polygon"


def test_diagonal_section_is_triangle_sac():
    """(SAC) through the apex and a diagonal: triangle S, A, C; S² = (½|AS × AC|)² = (½·6√2)² = 18."""
    r = _run(_section("f5", "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (SAC).", "SAC"),
             _area("Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (SAC).", "SAC"))
    assert _vertices(r) == {r.points["S"], r.points["A"], r.points["C"]}
    assert HB.answer_square(r.answers["q"]) == 18


def test_section_through_three_lateral_midpoints_is_the_mid_square():
    """(MNP), midpoints of SA, SB, SC: plane ∥ base at half height ⇒ square of side 1 with Q = mid SD; S² = 1."""
    r = _run(HB._mid("f5", "M", "S", "A"), HB._mid("f6", "N", "S", "B"), HB._mid("f7", "P", "S", "C"),
             _section("f8", "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MNP).", "MNP"),
             _area("Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MNP).", "MNP"))
    assert _vertices(r) == {_pt(r, "S", x) for x in "ABCD"}
    assert HB.answer_square(r.answers["q"]) == 1


def test_cube_section_a1bd_is_equilateral_triangle():
    """Cube edge 2, (A'BD): triangle with side 2√2 ⇒ S = (√3/4)·8 = 2√3, S² = 12."""
    q = ["Cho hình lập phương ABCD.A'B'C'D' cạnh 2.", "Xác định thiết diện của hình lập phương cắt bởi mặt phẳng (A'BD).",
         "Tính diện tích thiết diện của hình lập phương cắt bởi mặt phẳng (A'BD)."]
    facts = [f("f1", "solid", q[0], solid="ABCD.A'B'C'D'", solid_type="cube"),
             f("f2", "length", q[0], solid="ABCD.A'B'C'D'", measure="edge", value="2"),
             _section("f3", q[1], ["A'", "B", "D"], solid="ABCD.A'B'C'D'"),
             _area(q[2], ["A'", "B", "D"], solid="ABCD.A'B'C'D'")]
    r = run_fact_route(" ".join(q), {"facts": facts})
    assert r.status == "SERVED", (r.code, r.reason)
    assert _vertices(r) == {r.points["A'"], r.points["B"], r.points["D"]}
    assert HB.answer_square(r.answers["q"]) == 12


def test_section_only_without_area_is_a_simulation():
    r = _run(HB._mid("f5", "M", "S", "C"), _section("f6", "Dựng thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB).", "MAB"))
    assert r.status == "SERVED" and r.answers == {}
    assert len(_vertices(r)) == 4


def test_section_renamed_and_reordered_is_invariant():
    names = "TMNPQ"
    q, facts = HB._square(names)
    extra = [HB._mid("f5", "K", "T", "P"), _section("f6", "Xác định thiết diện của hình chóp T.MNPQ cắt bởi mặt phẳng (KMN).",
                                                     "KMN", solid="T.MNPQ"),
             _area("Tính diện tích thiết diện của hình chóp T.MNPQ cắt bởi mặt phẳng (KMN).", "KMN", solid="T.MNPQ")]
    q, facts = HB._with((q, facts), *extra)
    r = run_fact_route(" ".join(reversed(q)), {"facts": list(reversed(facts))})
    assert HB.answer_square(r.answers["q"]) == F(117, 16), (r.code, r.reason)


# ── intersection lines ─────────────────────────────────────────────────────────────────────────────────────────

def _line_obj(r):
    (o,) = [o for o in r.scene3d["objects"] if o["type"] == "line3" and o["id"].startswith("gt_")]
    return o


def _on_line(o, p):
    pt, d = [tuple(map(F, o["point"])), tuple(map(F, o["direction"]))]
    w = tuple(p[i] - pt[i] for i in range(3))
    return HB.cross(w, d) == (0, 0, 0)


def test_intersection_line_of_sab_and_scd_is_parallel_to_ab_through_s():
    r = _run(_line("f5", "Tìm giao tuyến của (SAB) và (SCD).", "SAB", "SCD"))
    assert r.status == "SERVED", (r.code, r.reason)
    o = _line_obj(r)
    ab = tuple(r.points["B"][i] - r.points["A"][i] for i in range(3))
    assert HB.cross(tuple(map(F, o["direction"])), ab) == (0, 0, 0)
    assert _on_line(o, r.points["S"])


def test_intersection_line_of_sac_and_sbd_passes_through_s_and_the_centre():
    r = _run(_line("f5", "Tìm giao tuyến của (SAC) và (SBD).", "SAC", "SBD"))
    o = _line_obj(r)
    assert _on_line(o, r.points["S"]) and _on_line(o, _pt(r, "A", "C"))


# ── refusals ───────────────────────────────────────────────────────────────────────────────────────────────────

def test_parallel_planes_have_no_intersection_line():
    r = _run(HB._mid("f5", "M", "S", "A"), HB._mid("f6", "N", "S", "B"), HB._mid("f7", "P", "S", "C"),
             _line("f8", "Tìm giao tuyến của (MNP) và (ABC).", "MNP", "ABC"))
    assert (r.status, r.code) == ("REFUSED", "PARALLEL_PLANES"), (r.answers, r.reason)


def test_section_by_collinear_points_is_refused():
    r = _run(HB._mid("f5", "M", "A", "B"), _section("f6", "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB).", "MAB"))
    assert r.status == "REFUSED", r.answers


@pytest.mark.parametrize("quote,plane,code", [
    ("Chứng minh rằng thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB) là hình thang.", "MAB", "GOAL_CLAUSE_NOT_PREMISE"),
    ("Nếu thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB) là hình thang thì SA = 3.", "MAB", "CONDITIONAL_CLAUSE"),
    ("Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MCD).", "MAB", "PLANE_NOT_IN_QUOTE"),
    ("Mặt phẳng (MAB) cắt hình chóp S.ABCD.", "MAB", "PREDICATE_NOT_IN_QUOTE"),
])
def test_section_grounding(quote, plane, code):
    r = _run(HB._mid("f5", "M", "S", "C"), _section("f6", quote, plane))
    assert (r.status, r.code) == ("REFUSED", code), (r.answers, r.reason)


def test_section_area_must_be_asked():
    r = _run(HB._mid("f5", "M", "S", "C"),
             _area("Diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB) bằng 3.", "MAB"))
    assert (r.status, r.code) == ("REFUSED", "NOT_ASKED_IN_SOURCE"), r.answers


# ── route A uses the same functions ───────────────────────────────────────────────────────────────────────────

def test_route_a_section_area():
    q, facts = HB._with(HB._square(), HB._mid("f5", "M", "S", "C"))
    text = " ".join(q) + " Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB)."
    from app.simulation.geometry_functions.planner import lap_ke_hoach

    calls = lap_ke_hoach({"facts": facts}, text).calls + [
        {"id": "a1", "fn": "ask_section_area", "args": {"solid": "S.ABCD", "plane": ["M", "A", "B"]},
         "source": {"quotes": ["Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB)."]}}]
    r = run_function_route(text, {"calls": calls})
    assert HB.answer_square(r.answers["a1"]) == F(117, 16), (r.code, r.reason)


# ── source mutants of the slice must be killed ─────────────────────────────────────────────────────────────────

def _mutant(monkeypatch, mod, old, new):
    import sys
    import types
    from pathlib import Path

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert src.count(old) == 1, old
    m = types.ModuleType(mod.__name__ + "_mutant")
    m.__package__ = mod.__package__
    monkeypatch.setitem(sys.modules, m.__name__, m)
    exec(compile(src.replace(old, new), mod.__file__, "exec"), m.__dict__)
    return m


def _mid_square_case():
    return [HB._mid("f5", "M", "S", "A"), HB._mid("f6", "N", "S", "B"), HB._mid("f7", "P", "S", "C")]


def _trapezoid_case():
    return [HB._mid("f5", "M", "S", "C"), _section("f6", "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB).", "MAB"),
            _area("Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB).", "MAB")]


def _engine_mutant(monkeypatch, old, new):
    from app.ai import function_route as FR
    from app.simulation.geometry_functions import engine as EN

    monkeypatch.setattr(FR, "dung_tu_loi_goi", _mutant(monkeypatch, EN, old, new).dung_tu_loi_goi)


def _planner_mutant(monkeypatch, old, new):
    from app.simulation.geometry_functions import planner as PL

    monkeypatch.setattr(PL, "lap_ke_hoach", _mutant(monkeypatch, PL, old, new).lap_ke_hoach)


SLICE_MUTANTS = [
    ("parallel-plane precheck dropped", _engine_mutant, "if p1.normal.cross(p2.normal).is_zero():", "if False:",
     lambda: _run(*_mid_square_case(), _line("f8", "Tìm giao tuyến của (MNP) và (ABC).", "MNP", "ABC")).code != "PARALLEL_PLANES"),
    ("section built twice", _engine_mutant, "            if (khoa := _khoa_mat_cat(c)) in td:\n                continue\n",
     "            khoa = _khoa_mat_cat(c)\n",
     lambda: len([o for o in _run(*_trapezoid_case()).scene3d["objects"] if o["type"] == "section"]) != 1),
    ("section area routed to polygon area", _planner_mutant, 'if n == "area" and f.solid and len(f.points or []) >= 3:',
     "if False:", lambda: _run(*_trapezoid_case()).answers.get("q") is None
     or HB.answer_square(_run(*_trapezoid_case()).answers["q"]) != F(117, 16)),
]


@pytest.mark.parametrize("name,apply,old,new,killed", SLICE_MUTANTS, ids=[m[0] for m in SLICE_MUTANTS])
def test_slice_mutant_is_killed(monkeypatch, name, apply, old, new, killed):
    assert not killed(), "the unmutated code must pass the kill check"
    apply(monkeypatch, old, new)
    assert killed(), f"mutant survived: {name}"
