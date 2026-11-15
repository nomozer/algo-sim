# -*- coding: utf-8 -*-
"""Run `compositional-semantics-simulation-goals`: comma-joined sub-clauses, a plane defined after the question that
uses it, and simulation-oriented trigonometric goals (the angle is constructed; its cos/sin/tan is never answered).

Every positive has a negative or a metamorphic partner; nothing here names a dataset case.
"""
from __future__ import annotations

import copy

import pytest

from app.ai.adaptive_input_router import route_text_input
from app.ai.local_geometry_parser import _subclause_spans, parse_geometry_problem_locally

B4 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a"
B3 = "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC) và SA = a"


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.setenv("GEMINI_API_KEY", "")


def _route(text):
    out = route_text_input(text, allow_live_ai=False)
    return out, (out.response or {}).get("route_d") or {}


def _section_polygon(out):
    objs = ((out.response or {}).get("envelope") or {}).get("scene3d", {}).get("objects") or []
    return sorted(len(o.get("polygon") or []) for o in objs if o.get("type") == "section")


# ── comma-joined sub-clauses ────────────────────────────────────────────────────────────────────────────────────────
ONE = f"{B4}, M là trung điểm của SA, mặt phẳng (P) đi qua M và song song với mặt đáy. Xác định thiết diện của hình chóp bởi (P)."
SPLIT = (f"{B4}. Gọi M là trung điểm của SA. Mặt phẳng (P) đi qua M và song song với mặt đáy. "
         "Xác định thiết diện của hình chóp bởi (P).")


def test_one_sentence_definitions_build_the_same_section_as_separate_sentences():
    one, rd1 = _route(ONE)
    split, rd2 = _route(SPLIT)
    assert one.status == split.status == "SERVED"
    assert _section_polygon(one) == _section_polygon(split) == [4]


@pytest.mark.parametrize("extra", ["N thuộc cạnh SB", "các cạnh bên bằng nhau", "tam giác SBC có diện tích lớn nhất"])
def test_an_unread_comma_joined_part_makes_the_sentence_partial_never_complete(extra):
    text = f"{B4}, M là trung điểm của SA, {extra}, mặt phẳng (P) đi qua M và song song với mặt đáy. Xác định thiết diện của hình chóp bởi (P)."
    lp = parse_geometry_problem_locally(text, use_cache=False)
    assert lp.status != "LOCAL_PARSE_COMPLETE"
    notes = [n for c in lp.source_coverage.clauses for n in c.get("notes") or ()]
    assert any(n.startswith("UNREAD_SUBCLAUSE@") and extra[:10] in n for n in notes)
    assert _route(text)[0].status != "SERVED"


def test_label_lists_numbers_and_brackets_are_not_cut_but_new_clauses_are():
    s = "Gọi M, N lần lượt là trung điểm của SA, SB và góc nhị diện [S, BC, A] bằng 60°, SA = 3,5, M, N thuộc mặt phẳng (P)"
    parts = [s[a:b].strip() for a, b in _subclause_spans(s, 0, len(s))]
    assert parts == ["Gọi M, N lần lượt là trung điểm của SA, SB và góc nhị diện [S, BC, A] bằng 60°", "SA = 3,5",
                     "M, N thuộc mặt phẳng (P)"]
    u = "SA = a và hình chiếu vuông góc của S lên (ABC) là H, diện tích tam giác SAB và tam giác SBC"
    assert [u[a:b].strip() for a, b in _subclause_spans(u, 0, len(u))] == [
        "SA = a", "và hình chiếu vuông góc của S lên (ABC) là H", "diện tích tam giác SAB và tam giác SBC"]
    t = "SA = a, N thuộc cạnh SB"                       # a label with its own predicate after a comma is a new clause
    assert [t[a:b].strip() for a, b in _subclause_spans(t, 0, len(t))] == ["SA = a", "N thuộc cạnh SB"]


def test_renamed_vertices_and_greek_plane_name_behave_alike():
    renamed = ("Cho hình chóp T.EFGH có đáy EFGH là hình vuông cạnh a, TE vuông góc với mặt phẳng đáy và TE = a, K là trung "
               "điểm của TE, mặt phẳng (Q) đi qua K và song song với mặt đáy. Xác định thiết diện của hình chóp bởi (Q).")
    greek = ONE.replace("(P)", "(α)")
    assert {_route(t)[0].status for t in (renamed, greek)} == {"SERVED"}


# ── a plane defined AFTER the question that uses it ─────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("tail", [", biết (P) đi qua M và song song với mặt đáy.", ". Biết (P) đi qua M và song song với mặt đáy."])
def test_a_plane_defined_after_its_question_is_bound_like_one_defined_before(tail):
    text = f"{B4}. Gọi M là trung điểm của SA. Xác định thiết diện của hình chóp bởi mặt phẳng (P){tail}"
    out, _rd = _route(text)
    assert out.status == "SERVED" and _section_polygon(out) == _section_polygon(_route(SPLIT)[0])


def test_a_plane_never_defined_stays_an_unresolved_reference():
    out, rd = _route(f"{B4}. Gọi M là trung điểm của SA. Xác định thiết diện của hình chóp bởi mặt phẳng (P).")
    assert out.status != "SERVED"
    assert rd["local_diagnostics"]["root_cause"] == "UNRESOLVED_REFERENCE"


# ── trigonometric value of an angle: the angle is constructed, the number is NOT answered ───────────────────────────
@pytest.mark.parametrize("ask, fn", [("Tính cosin của góc", "cos"), ("Tính côsin của góc", "cos"), ("Tính tang của góc", "tan"),
                                     ("Sin của góc", "sin")])
def test_a_trigonometric_goal_serves_the_angle_and_states_the_number_unanswered(ask, fn):
    tail = " bằng" if ask.startswith("Sin") else "."
    out, rd = _route(f"{B3}. {ask} giữa SB và mặt phẳng (ABC){tail}")
    plain, rd_plain = _route(f"{B3}. Tính góc giữa SB và mặt phẳng (ABC).")
    assert out.status == plain.status == "SERVED"
    sgc = rd["source_goal_completion"]
    assert sgc["source_goal_fully_satisfied"] is False and sgc["numeric_answer_shown"] is False
    assert [(g["function"], g["state"], g["numeric_source_goal"]) for g in sgc["goals"]] == [(fn, "GOAL_VISUALIZATION_READY", "NOT_ANSWERED")]
    # the constructed angle is the very angle of the plain question; a plain angle question carries no such record
    assert rd["answer_exact"] == rd_plain["answer_exact"] and "source_goal_completion" not in rd_plain


def test_tangent_of_a_right_angle_is_reported_undefined_not_computed():
    _out, rd = _route(f"{B4}. Tính tang của góc giữa SA và mặt phẳng (ABCD).")
    assert [g["value_defined"] for g in rd["source_goal_completion"]["goals"]] == [False]


@pytest.mark.parametrize("text", [
    f"{B3}. Tính cosin của độ dài SB.",                                                       # not an angle
    f"{B3}. Tính bình phương cosin của góc giữa SB và mặt phẳng (ABC).",                       # another quantity of it
    f"{B3}. Tính cosin của góc giữa SB và mặt phẳng (SAC) và độ dài SC.",                      # an unanswered request remains
])
def test_trigonometric_wording_never_answers_another_object_or_becomes_a_fact(text):
    assert _route(text)[0].status != "SERVED"


def test_trigonometric_angle_premise_serves_verified_length_goal_without_goal_confusion():
    # Before run `dimension-aware-verified-construction` (Stage P1c), `cosin của góc giữa SB và mặt phẳng (ABC) bằng 1/2`
    # was unparsed as a premise and refused; Stage P1c parses and Source-Gate-verifies trigonometric angle premises
    # (`unit='cos'`, `cos=1/2` => `tan=√3` => `SA = a√3`) with `trig-construction-certificate/1`, answering ONLY the
    # asked length goal `SA` (never treating the premise angle as an asked trigonometric goal).
    text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC) và cosin của góc giữa SB và "
        "mặt phẳng (ABC) bằng 1/2. Tính độ dài SA."
    )
    out, rd = _route(text)
    assert out.status == "SERVED"
    assert rd["answer_exact"] == {"q1": {"coef": "√3", "dim": 1, "unit": "a"}}
    assert "source_goal_completion" not in rd
    certs = rd.get("trig_construction_certificates") or []
    assert len(certs) == 1 and certs[0]["verified"] is True and certs[0]["derived_quantity_id"] == ["A", "S"]


def test_the_completion_record_is_bound_to_the_verified_result():
    from app.ai.adapter4_route import build_adapter4_response
    from app.ai.hybrid_offline import run_hybrid_offline  # noqa: F401  (route import side effects)
    from app.ai.adapter4_route import run_typed_fact_next_v2_route

    text = f"{B3}. Tính cosin của góc giữa SB và mặt phẳng (ABC)."
    lp = parse_geometry_problem_locally(text, use_cache=False)
    r = run_typed_fact_next_v2_route(lp.payload)
    assert r.status == "SERVED" and build_adapter4_response(r, text)["route_d"]["status"] == "SERVED"
    forged = copy.deepcopy(r)
    forged.route_d["source_goal_completion"]["goals"][0]["numeric_source_goal"] = "ANSWERED"
    assert build_adapter4_response(forged, text)["route_d"]["status"] == "REFUSED"
    dropped = copy.deepcopy(r)
    dropped.route_d.pop("source_goal_completion")
    assert build_adapter4_response(dropped, text)["route_d"]["status"] == "REFUSED"


@pytest.mark.parametrize("mutate", [
    lambda ac: ac["perpendicular"].__setitem__("foot", ["1/7", "0", "0"]),               # wrong projection foot
    lambda ac: ac["perpendicular"].__setitem__("foot", list(ac["perpendicular"]["from"])),  # degenerate marker
    lambda ac: ac["arms"][0].__setitem__("to", ["9", "9", "9"]),                          # arm end is not its point
    lambda ac: ac.__setitem__("vertex", ["0", "1", "0"]),                                 # vertex is not its point
])
def test_a_drawn_angle_is_bound_to_the_verified_points(mutate):
    from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route

    text = f"{B3}. Tính cosin của góc giữa SB và mặt phẳng (ABC)."
    r = run_typed_fact_next_v2_route(parse_geometry_problem_locally(text, use_cache=False).payload)
    assert build_adapter4_response(r, text)["route_d"]["status"] == "SERVED"
    m = copy.deepcopy(r)
    mutate(next(o for o in m.scene3d["objects"] if o.get("angle_construction"))["angle_construction"])
    assert build_adapter4_response(m, text)["route_d"]["status"] == "REFUSED"


def test_gate_reads_the_function_only_before_an_angle_phrase():
    from app.simulation.geometry_functions.registry import ham_luong_giac_hoi
    de = f"{B3}. Tính cosin của góc giữa SB và mặt phẳng (ABC)."
    assert ham_luong_giac_hoi(de, "góc giữa SB và mặt phẳng (ABC)") == "cos"
    assert ham_luong_giac_hoi(f"{B3}. Tính góc giữa SB và mặt phẳng (ABC).", "góc giữa SB và mặt phẳng (ABC)") is None
    assert ham_luong_giac_hoi(f"{B3}. Tính cosin của độ dài SB.", "độ dài SB") is None


# ── the gate's closed plane-definition clause ──────────────────────────────────────────────────────────────────────
def test_a_plane_definition_clause_is_closed_grammar_but_never_carries_a_number_or_binds_a_role():
    from app.simulation.geometry_functions.registry import _phan_tich_cau
    assert [k for k, _m in _phan_tich_cau("mặt phẳng (P) đi qua M và song song với mặt đáy") or ()] == ["mpdn"]
    assert _phan_tich_cau("mặt phẳng (P) song song với đáy và cách đáy một khoảng bằng 2") is None
    # an unlabelled role in a sentence holding a plane definition still binds nothing (subject change)
    text = "Cho hình chóp tứ giác đều S.ABCD, mặt phẳng (P) đi qua S và song song với AB, có cạnh đáy bằng 2. Tính thể tích khối chóp S.ABCD."
    assert _route(text)[0].status != "SERVED"


# ── diagnostics: understood-but-unsupported is told apart from missing data ─────────────────────────────────────────
@pytest.mark.parametrize("text, root", [
    (f"{B4}. Điểm M thuộc cạnh SC. Tính khoảng cách từ M đến mặt phẳng (ABCD).", "FREE_POINT_UNDERDETERMINED"),
    (f"{B4}. Gọi E là điểm đối xứng của A qua C. Tính khoảng cách từ E đến mặt phẳng (SBC).", "UNSUPPORTED_POINT_CONSTRUCTION"),
    ("Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA = a và hình chiếu vuông góc của S lên mặt phẳng (ABC) trùng "
     "với trọng tâm của tam giác ABC. Tính khoảng cách từ S đến mặt phẳng (ABC).", "DESCRIBED_POINT_IN_PREMISE_UNSUPPORTED"),
    # a regular tetrahedron without side is now served (run `target-invariant-regular-solid-semantics`); a NON-regular
    # one keeps a shape freedom that no target-invariance proof covers
    ("Cho tứ diện ABCD. Gọi M là trung điểm của CD. Côsin của góc giữa hai đường thẳng AC và BM bằng",
     "SHAPE_FREEDOM_UNCERTIFIED"),
])
def test_specific_root_causes(text, root):
    out, rd = _route(text)
    assert out.status != "SERVED" and rd["local_diagnostics"]["root_cause"] == root


def test_a_named_point_on_a_segment_with_a_ratio_is_not_called_free():
    from app.ai.local_failure_diagnostics import _clause_root
    assert _clause_root("M thuộc cạnh SA sao cho SM = 2MA") is None
    assert _clause_root("Gọi M là một điểm thuộc cạnh SC") == "FREE_POINT_UNDERDETERMINED"
