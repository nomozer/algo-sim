"""Executable probes for the Hybrid simulation capability audit (run `hybrid-simulation-capability-audit`).

Evidence class: OFFLINE typed facts (verified Typed Facts → planner → source gate → engine → IR → kernel → Scene3D JSON).
Not fake-provider, not real Gemini, not browser, not human visual review.

Three kinds of probe:
- `CURRENT` rows pin today's behaviour of the Hybrid route (served answer = independent oracle, or the refusal code).
  They describe the system; they are not targets. A row that changes must be re-read, not blindly re-pinned.
- `test_shared_engine_builds_a_section_hybrid_cannot_request` shows a construction the shared engine/IR/Scene3D already
  performs but the Hybrid Registry has no function for ("engine knows, Hybrid has no way in").
- `KNOWN_DEFECTS` are strict xfail: they assert the SAFE behaviour and fail today; they flip when fixed.
"""
from __future__ import annotations

import copy
from fractions import Fraction as F

import pytest

from app.ai.function_route import run_fact_route, run_function_route
from tests.geometry import hybrid_compiler_benchmark as HB

f, ask = HB._f, HB._ask
A, B, C, D, S = HB.A, HB.B, HB.C, HB.D, HB.S


def _run(*extra, base=None, names="SABCD"):
    q, facts = HB._with(base or HB._square(names), *extra)
    return run_fact_route(" ".join(q), {"facts": facts})


def _proj(fid, quote, img, p, tgt):
    return f(fid, "projection", quote, point=p, points=list(tgt), at=img)


def _ask_len(a, b, quote=None):
    return ask("q", quote or f"Tính độ dài {a}{b}.", "length", points=[a, b])


SQ_AH = HB.dist2_point_line(A, S, B)                    # 36/13
SQ_AM = HB.len2(A, HB.mid(S, C))                         # 17/4

# (id, facts, expected) — expected is ("SERVED", answer²) or ("REFUSED", code) or ("SERVED", None) for construction only
CURRENT = [
    # constructions without any question (simulation-only requests)
    ("P01_midpoint_only", [HB._mid("f5", "M", "S", "C")], ("SERVED", None)),
    ("P03_projection_plane_only", [HB._proj("f5", "H", "A", "SBC")], ("SERVED", None)),
    ("P05_centroid_triangle", [f("f5", "point_def", "Gọi G là trọng tâm tam giác SBC.", point="G", point_kind="centroid",
                                 points=list("SBC"))], ("SERVED", None)),
    ("P11_line_plane_intersection_only", [HB._mid("f5", "M", "S", "A"), HB._ilp("f6", "P", "SD", "MBC")], ("SERVED", None)),
    # constructions the Hybrid route cannot request (no fact kind / Registry function)
    ("P02_draw_line_unsupported", [HB._mid("f5", "M", "S", "C"),
                                   f("f6", "unsupported", "Vẽ đường thẳng AM.", reason="vẽ đường thẳng")], ("REFUSED", "OUT_OF_SCOPE")),
    ("P05b_centroid_square", [f("f5", "point_def", "Gọi G là trọng tâm hình vuông ABCD.", point="G", point_kind="centroid",
                                points=list("ABCD"))], ("REFUSED", "UNSUPPORTED_CENTROID")),
    ("P09_section_unsupported", [HB._mid("f5", "M", "S", "C"),
                                 f("f6", "unsupported", "Dựng thiết diện của hình chóp cắt bởi (MAB).", reason="thiết diện")],
     ("REFUSED", "OUT_OF_SCOPE")),
    # degenerate / missing
    ("P17_parallel_lines_no_intersection", [HB._ill("f5", "I", "AB", "CD")], ("REFUSED", "PARALLEL_NO_INTERSECTION")),
    ("E13_projection_point_on_line", [_proj("f5", "Gọi H là hình chiếu vuông góc của A lên SA.", "H", "A", "SA"),
                                      _ask_len("A", "H")], ("SERVED", F(0))),
    # LINE vs SEGMENT: the line reading is served; the explicit segment wording fails closed
    ("P15_line_intersection_outside_segment", [HB._mid("f5", "M", "B", "C"), HB._ill("f6", "I", "AB", "DM")], ("SERVED", None)),
    ("P16_segment_wording_refused", [HB._mid("f5", "M", "B", "C"),
                                     f("f6", "point_def", "Gọi I là giao điểm của đoạn thẳng AB và đoạn thẳng DM.", point="I",
                                       point_kind="intersect_line_line", points_a=["A", "B"], points_b=["D", "M"])],
     ("REFUSED", "SOURCE_OBJECT_MISMATCH")),
    # clause roles handled today
    ("P19_proof_goal_role_prove", [f("f5", "perpendicular", "Chứng minh SA vuông góc với BC.", role="prove",
                                     points_a=["S", "A"], points_b=["B", "C"]), _ask_len("S", "C")],
     ("SERVED", HB.len2(S, C))),
    ("P21_negated_premise", [f("f5", "perpendicular", "SB không vuông góc với AD.", points_a=["S", "B"], points_b=["A", "D"])],
     ("REFUSED", "NEGATED_CLAUSE")),
    ("P23_wrong_object_bound", [f("f5", "projection", "Gọi H là hình chiếu vuông góc của A lên SB.", point="B",
                                  points=["S", "C"], at="H")], ("REFUSED", "ROLE_NOT_IN_QUOTE")),
    # wording breadth of construction clauses (metamorphic paraphrase)
    ("E01_projection_goi_la", [_proj("f5", "Gọi H là hình chiếu vuông góc của A lên SB.", "H", "A", "SB"), _ask_len("A", "H")],
     ("SERVED", SQ_AH)),
    ("E04_projection_hinh_chieu_la", [_proj("f5", "Hình chiếu vuông góc của A trên SB là H.", "H", "A", "SB"),
                                      _ask_len("A", "H")], ("SERVED", SQ_AH)),
    ("E02_ke_vuong_goc_tai", [_proj("f5", "Kẻ AH vuông góc với SB tại H.", "H", "A", "SB"), _ask_len("A", "H")],
     ("REFUSED", "PREDICATE_NOT_IN_QUOTE")),
    ("E03_dung_hinh_chieu", [_proj("f5", "Dựng hình chiếu H của A lên SB.", "H", "A", "SB"), _ask_len("A", "H")],
     ("REFUSED", "SOURCE_OBJECT_MISMATCH")),
    ("E05_chan_duong_vuong_goc", [_proj("f5", "Gọi H là chân đường vuông góc hạ từ A xuống SB.", "H", "A", "SB"),
                                  _ask_len("A", "H")], ("REFUSED", "PREDICATE_NOT_IN_QUOTE")),
    ("E06_midpoint_goi", [HB._mid("f5", "M", "S", "C"), _ask_len("A", "M")], ("SERVED", SQ_AM)),
    ("E07_midpoint_lay", [f("f5", "point_def", "Lấy M là trung điểm của cạnh SC.", point="M", point_kind="midpoint",
                            points=["S", "C"]), _ask_len("A", "M")], ("SERVED", SQ_AM)),
    ("E08_midpoint_doan_thang", [f("f5", "point_def", "M là trung điểm của đoạn thẳng SC.", point="M", point_kind="midpoint",
                                   points=["S", "C"]), _ask_len("A", "M")], ("SERVED", SQ_AM)),
    ("E09_irrelevant_extra_fact", [HB._mid("f5", "M", "S", "C"), HB._mid("f6", "K", "A", "B"), _ask_len("A", "M")],
     ("SERVED", SQ_AM)),
    ("E10_subscript_label", [f("f5", "point_def", "Gọi M₁ là trung điểm SC.", point="M1", point_kind="midpoint",
                               points=["S", "C"]), ask("q", "Tính độ dài AM₁.", "length", points=["A", "M1"])],
     ("REFUSED", "UNKNOWN_LABEL")),
]


@pytest.mark.parametrize("facts,expected", [pytest.param(fa, e, id=i) for i, fa, e in CURRENT])
def test_current_hybrid_behaviour(facts, expected):
    r = _run(*facts)
    status, want = expected
    assert r.status == status, (r.code, r.reason)
    if status == "REFUSED":
        assert r.code == want, r.reason
    elif want is not None:
        assert HB.answer_square(r.answers["q"]) == want, r.answers
    else:
        assert r.scene3d and r.scene3d["objects"]


def test_renamed_projection_is_invariant():
    r = _run(_proj("f5", "Gọi K là hình chiếu vuông góc của M lên TN.", "K", "M", "TN"),
             ask("q", "Tính độ dài MK.", "length", points=["M", "K"]), names="TMNPQ")
    assert HB.answer_square(r.answers["q"]) == SQ_AH


def test_shared_engine_builds_a_section_hybrid_cannot_request():
    """'Engine knows, Hybrid has no way in': append construct_plane(M,A,B) + construct_section to the IR the Hybrid route
    already produced; the existing interpreter and Scene3D build the section. Oracle: the plane through A, B and the
    midpoint M of SC cuts the pyramid in the trapezoid A, B, M, N with N the midpoint of SD (AB ∥ CD ⇒ MN ∥ CD)."""
    from app.simulation.geometry import metric as _metric
    from app.simulation.semantic_program import ir_builders as P
    from app.simulation.semantic_program.formation import hoan_thien_dung_hinh
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
    from app.simulation.semantic_program.scene3d import build_scene3d
    from app.simulation.semantic_program.simulation_state import build_simulation_state
    from app.simulation.semantic_program.validator import validate_semantic_program

    q, facts = HB._with(HB._square(), HB._mid("f5", "M", "S", "C"))
    r = run_fact_route(" ".join(q), {"facts": facts})
    assert r.status == "SERVED"
    assert not any(s["kind"] == "construct_section" for s in r.program["statements"])     # Hybrid never emits it
    prog = copy.deepcopy(r.program)
    solid = next(s["target_var"] for s in prog["statements"] if s["kind"] == "construct_solid")
    prog["statements"] += [{"kind": "construct_plane", "target_var": "mp_MAB", "through": ["M", "A", "B"]},
                           {"kind": "construct_section", "target_var": "td", "solid": solid, "plane": "mp_MAB"}]
    prog["memory_declarations"] += [P.memory_declaration("mp_MAB", "plane3"), P.memory_declaration("td", "section")]
    vr = validate_semantic_program(prog)
    assert vr.ok, vr.error
    spec = hoan_thien_dung_hinh(vr.spec, r.declared_topology).spec
    with _metric.using(r.chart_metric):
        ket = SemanticProgramInterpreter().execute(spec)
        canh = build_scene3d(build_simulation_state(spec, ket, r.declared_topology))
    pts = {k: tuple(v) for k, v in r.points.items()}
    mid = lambda a, b: tuple((x + y) / 2 for x, y in zip(pts[a], pts[b]))      # noqa: E731
    expected = {pts["A"], pts["B"], mid("S", "C"), mid("S", "D")}
    got = {(p.x, p.y, p.z) for p in ket.final_memory["td"].polygon}
    assert got == expected
    (o,) = [o for o in canh["objects"] if o["id"] == "td"]
    assert (o["type"], o["render"]) == ("section", "polygon")


def _no_perpendicular_base():
    q, facts = HB._square()
    return [q[0], q[1], q[3]], [facts[0], facts[1], facts[3]]       # no SA ⊥ (ABCD): apex undetermined


def test_control_apex_undetermined_without_perpendicularity():
    assert _run(_ask_len("S", "C"), base=_no_perpendicular_base()).code == "UNDERDETERMINED_POINT"


def _clause_as_premise(quote):
    return f("f5", "perpendicular", quote, points_a=["S", "A"], points_b=list("ABCD"))


# Known defects: SAFE behaviour asserted; strict xfail until fixed.
@pytest.mark.xfail(strict=True, reason="CRITICAL (this audit): the shared gate reads the clause role BEFORE the quote; a "
                                       "premise quote that carries its own 'Nếu … thì' is used as a given and served")
def test_conditional_clause_inside_the_quote_is_not_a_premise():
    r = _run(_clause_as_premise("Nếu SA vuông góc với (ABCD) thì SC = 5."), _ask_len("S", "C"), base=_no_perpendicular_base())
    assert r.status == "REFUSED", r.answers


@pytest.mark.xfail(strict=True, reason="CRITICAL (this audit): a premise quote that carries its own 'Chứng minh' is used as a given")
def test_proof_goal_inside_the_quote_is_not_a_premise():
    r = _run(_clause_as_premise("Chứng minh rằng SA vuông góc với (ABCD)."), _ask_len("S", "C"), base=_no_perpendicular_base())
    assert r.status == "REFUSED", r.answers


@pytest.mark.xfail(strict=True, reason="CRITICAL (this audit): same gate in route A (shared kiem_nguon)")
def test_route_a_conditional_clause_inside_the_quote_is_not_a_premise():
    t = "Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA = 3. Nếu SA vuông góc với (ABCD) thì SC = 5. Tính độ dài SC."
    calls = [
        {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": list("ABCD")}, "source": {"quotes": ["Cho hình chóp S.ABCD."]}},
        {"id": "c2", "fn": "regular_polygon", "args": {"vertices": list("ABCD"), "side": "2"},
         "source": {"quotes": ["Đáy ABCD là hình vuông cạnh 2."]}},
        {"id": "c3", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "3"}, "source": {"quotes": ["SA = 3."]}},
        {"id": "c4", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": list("ABCD")},
         "source": {"quotes": ["Nếu SA vuông góc với (ABCD) thì SC = 5."]}},
        {"id": "c5", "fn": "ask_length", "args": {"segment": ["S", "C"]}, "source": {"quotes": ["Tính độ dài SC."]}}]
    assert run_function_route(t, {"calls": calls}).status == "REFUSED"


@pytest.mark.xfail(strict=True, reason="ISSUE-ARCH-ASK-GATE-NO-QUESTION-CHECK: ask_* answers a clause that does not ask it")
def test_ask_point_plane_answers_only_a_question():
    r = _run(ask("q", "Hãy chỉ ra rằng khoảng cách từ S đến (ABCD) bằng 3.", "distance", points_a=["S"], points_b=list("ABCD")))
    assert r.status == "REFUSED", r.answers


@pytest.mark.xfail(strict=True, reason="ISSUE-ARCH-ENGINE-CENTRE-LABEL-EXHAUSTION: StopIteration instead of a coded refusal")
def test_centre_label_exhaustion_is_a_coded_outcome():
    q = ["Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 2 và cạnh bên bằng 3."]
    facts = [f("f1", "solid", "Cho hình chóp tứ giác đều S.ABCD", solid="S.ABCD", solid_type="pyramid", regular=True),
             f("f2", "length", "cạnh đáy bằng 2", solid="S.ABCD", measure="base_edge", value="2"),
             f("f3", "length", "cạnh bên bằng 3", solid="S.ABCD", measure="lateral_edge", value="3")]
    for i, (p, a, b) in enumerate((("O", "S", "A"), ("I", "S", "B"), ("O1", "S", "C"), ("O2", "S", "D")), start=4):
        facts.append(HB._mid(f"f{i}", p, a, b))
        q.append(facts[-1]["quotes"][0])
    q.append("Tính độ dài SO.")
    facts.append(_ask_len("S", "O"))
    r = run_fact_route(" ".join(q), {"facts": facts})
    assert r.status in ("SERVED", "REFUSED")
