# -*- coding: utf-8 -*-
"""Base-centre wording, the general apex ratio k and sphere sections on Route D /4 (seventh continuation, registry /25).
0 provider calls.

Hand oracles: `tools/base_center_probe.py` (the wording of the Adapter /3 fixtures /4 refused, plus variants and
negatives) and `tools/apex_ratio_probe.py` (k = SM/SO from the apex, OM/OS from the base converted by the GATE, never by the
model; k³ volume law through the existing similarity certificate), `tools/sphere_section_probe.py` (r'² = R² − d²; d = R is
a tangent point, d > R misses). Each negative carries the exact code it must refuse with.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry.radical import parse_exact

_RUN = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/tools"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _RUN / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


B, K, S = _load("base_center_probe"), _load("apex_ratio_probe"), _load("sphere_section_probe")
B_POS = [c for c in B.CASES if not c[3].startswith("REFUSE")]
B_NEG = [c for c in B.CASES if c[3].startswith("REFUSE")]


@pytest.mark.parametrize("cid,fig,ask,oracle", B_POS, ids=[c[0] for c in B_POS])
def test_base_centre_wordings_are_served_exactly(cid, fig, ask, oracle):
    r = run_typed_fact_next_v2_route(B.CP.payload(fig, *ask))
    assert r.status == "SERVED", (r.code, r.reason)
    assert parse_exact(r.answer_exact["mg1"]["coef"]) == parse_exact(oracle)


@pytest.mark.parametrize("cid,fig,ask,oracle", B_NEG, ids=[c[0] for c in B_NEG])
def test_base_centre_negatives_are_refused_for_the_right_reason(cid, fig, ask, oracle):
    r = run_typed_fact_next_v2_route(B.CP.payload(fig, *ask))
    assert r.status == "REFUSED" and not r.answer_exact and r.code == oracle.split(":", 1)[1], (r.code, r.reason)


@pytest.mark.parametrize("cid,payload,oracle", K.CASES, ids=[c[0] for c in K.CASES])
def test_apex_ratio_sections_and_volumes_are_served_exactly(cid, payload, oracle):
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "SERVED" and r.kernel_check is True, (r.code, r.reason)
    assert parse_exact(r.answer_exact["mg1"]["coef"]) == parse_exact(oracle)


@pytest.mark.parametrize("cid,payload,code", K.NEGATIVES, ids=[c[0] for c in K.NEGATIVES])
def test_apex_ratio_negatives_are_refused_for_the_right_reason(cid, payload, code):
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "REFUSED" and not r.answer_exact and r.code == code, (r.code, r.reason)


def test_a_named_point_on_the_axis_is_the_small_cones_base_centre():
    (cid, p, _o) = next(c for c in K.CASES if c[0] == "k.13.ratio")
    r = run_typed_fact_next_v2_route(p)
    assert r.points.get("M") == (0, 0, parse_exact("8/3"))           # SM/SO = 1/3 of h = 4 ⇒ z = 4 − 4/3 = 8/3
    assert any(s.get("object") == "M" and s.get("provenance") == "SOURCE_NAMED" for s in r.trace)


@pytest.mark.parametrize("cid,payload,oracle", S.CASES, ids=[c[0] for c in S.CASES])
def test_sphere_sections_are_served_exactly(cid, payload, oracle):
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "SERVED" and r.kernel_check is True, (r.code, r.reason)
    assert parse_exact(r.answer_exact["mg1"]["coef"]) == parse_exact(oracle)


@pytest.mark.parametrize("cid,payload,code", S.NEGATIVES, ids=[c[0] for c in S.NEGATIVES])
def test_sphere_section_negatives_are_refused_for_the_right_reason(cid, payload, code):
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "REFUSED" and not r.answer_exact and r.code == code, (r.code, r.reason)


def test_the_sphere_section_is_the_kernels_circle_not_a_formula():
    """The served circle is executed by the kernel (`_giao_cau`): centre = projection of the sphere's centre, r'² = R² − d²."""
    (cid, p, _o) = next(c for c in S.CASES if c[0] == "s.d3.radius")
    r = run_typed_fact_next_v2_route(p)
    assert any(s.get("rule") == "sphere_plane_at_distance" and s.get("plane_distance") == "3" for s in r.trace)
    assert "intersect_plane_curved" in str(r.program["statements"])


def test_a_missing_centre_distance_is_a_contract_error():
    import copy
    (cid, p, _o) = S.CASES[0]
    p = copy.deepcopy(p)
    del p["derived_sections"][0]["distance_from_center"]
    r = run_typed_fact_next_v2_route(p)
    assert r.status == "REFUSED" and not r.answer_exact


# ── independent review round 1 (seventh continuation): each finding's reproducer, locked with its exact code ────────────
def _greek_plane(p):
    import copy
    p = copy.deepcopy(p)
    sec = p["derived_sections"][0]
    p["problem_text"] = p["problem_text"].replace("(P)", "(α)")
    sec["plane_name"], sec["quote"] = "α", sec["quote"].replace("(P)", "(α)")
    p["simulation_goals"][1]["quote"] = sec["quote"]
    return p


def _two_sections_second_distance_invented():
    SP = S.SP
    s1 = "Mặt phẳng (P) song song với đáy và cách đáy một khoảng bằng 1 cắt hình nón theo một đường tròn."
    s2 = "Mặt phẳng (Q) song song với đáy và cách đáy một khoảng bằng 2 cắt hình nón theo một đường tròn."
    p = SP.build(SP.CONE_G, SP.CONE_S, f"{s1} {s2}", SP.dist("1", s1), "Tính diện tích thiết diện.", SP.AREA)
    p["derived_sections"].append({**SP.dist("3", s2), "section_id": "td2", "plane_name": "Q"})   # the text says 2
    return p


def _solid_quote_is_the_section_sentence():
    SP = S.SP
    q = SP.build(SP.CONE_G, SP.CONE_S, SP.SEC_CONE1, SP.dist("1", SP.SEC_CONE1), "Tính diện tích thiết diện.", SP.AREA)
    q["solids"][0]["quote"] = q["simulation_goals"][0]["quote"] = SP.SEC_CONE1.rstrip(".")
    return q


def _sphere_with_a_base_distance_too():
    p = S.case("cách tâm O một khoảng bằng 3", "at_distance_from_center", S.AREA, S.A_Q, distance_from_center="3")
    p["derived_sections"][0]["distance_from_base"] = "2"
    return p


def _passive(sentence, kind, **fields):
    SP = S.SP
    return SP.build(SP.CONE_G, SP.CONE_S, sentence, SP.section(kind, sentence.rstrip("."), section_shape="circle", **fields),
                    "Tính diện tích thiết diện.", SP.AREA)


def _two_sections_second_quote_cut_mid_sentence():
    SP = S.SP
    s1 = "Mặt phẳng (P) song song với đáy và cách đáy một khoảng bằng 1 cắt hình nón theo một đường tròn."
    q2 = "mặt phẳng (Q) song song với đáy và cách đáy một khoảng bằng 2 cắt hình nón theo một đường tròn"
    p = SP.build(SP.CONE_G, SP.CONE_S, f"{s1} Biết rằng {q2}.", SP.dist("1", s1), "Tính diện tích thiết diện.", SP.AREA)
    p["derived_sections"].append({**SP.dist("2", q2), "section_id": "td2", "plane_name": "Q"})
    return p


_AREA_Q = "Tính diện tích thiết diện."
REVIEW_1 = [  # (id, payload builder, expected code)
    ("M1.zero_denominator_axis_point",
     lambda: K.ratio_case("và cắt SO tại M sao cho SM/SO = 1/0", "1/3", K.AREA, _AREA_Q, point="M"), "SCHEMA_INVALID"),
    ("M1.zero_denominator_axis_ratio",
     lambda: K.ratio_case("cắt trục SO theo tỉ lệ 2/0 tính từ đỉnh S", "1/3", K.AREA, _AREA_Q), "SCHEMA_INVALID"),
    ("M2.rim_on_another_circle", lambda: B.CP.payload(B.cone(
        "Cho hình nón đỉnh S, đáy là đường tròn tâm O, điểm A thuộc đường tròn đáy tâm I, bán kính đáy bằng 3 và chiều cao "
        "bằng 4.", rim=None), "volume", "Tính thể tích khối nón."), "SOURCE_OBJECT_MISMATCH"),
    ("M3.second_section_distance_invented", _two_sections_second_distance_invented, "UNGROUNDED_VALUE"),
    ("M4.solid_quote_is_the_section_sentence", _solid_quote_is_the_section_sentence, "SOURCE_OBJECT_MISMATCH"),
    ("M5.ti_so_reads_parts_or_whole",
     lambda: K.ratio_case("cắt trục SO theo tỉ số 1/2 tính từ đỉnh S", "1/2", K.AREA, _AREA_Q), "AMBIGUOUS_REFERENCE"),
    ("minor.sphere_section_with_a_base_distance", _sphere_with_a_base_distance_too, "SOURCE_OBJECT_MISMATCH"),
    ("minor.one_point_as_both_centres", lambda: B.CP.payload(B.cyl(
        "Cho hình trụ tròn xoay có tâm đáy dưới O, tâm đáy trên O, bán kính đáy R = 2 và chiều cao h = 3.", top="O", rim=None,
        notation="O.O"), "volume", "Tính thể tích khối trụ."), "SOURCE_OBJECT_MISMATCH"),
    # round 2: a correct quote the grammar cannot read is a capability gap; a quote cut mid-sentence keeps its source verdict
    ("R2-M1.passive_section_sentence", lambda: _passive(
        "Hình nón được cắt bởi mặt phẳng (P) song song với đáy và cách đáy một khoảng bằng 1.", "parallel_to_base_at_distance",
        distance_from_base="1"), "CURVED_WORDING_UNSUPPORTED"),
    ("R2-M2.second_quote_cut_mid_sentence", _two_sections_second_quote_cut_mid_sentence, "SOURCE_OBJECT_MISMATCH"),
]


@pytest.mark.parametrize("cid,build,code", REVIEW_1, ids=[c[0] for c in REVIEW_1])
def test_review_round_1_reproducers_are_refused_for_the_right_reason(cid, build, code):
    r = run_typed_fact_next_v2_route(build())
    assert r.status == "REFUSED" and not r.answer_exact and r.code == code, (r.code, r.reason)


def test_a_greek_plane_name_is_read():
    p = _greek_plane(S.CASES[0][1])                     # "Mặt phẳng (α) cách tâm O một khoảng bằng 3 …"
    r = run_typed_fact_next_v2_route(p)
    assert r.status == "SERVED", (r.code, r.reason)
    assert parse_exact(r.answer_exact["mg1"]["coef"]) == parse_exact("16π")
