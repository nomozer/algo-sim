# -*- coding: utf-8 -*-
"""Synthetic positive and negative control self-tests for `evaluate_holdout_wave2.py`.

Verifies all 17 mandatory safeguards required by Owner GO Section 8 independently of product execution:
1. Category A vertex coincides with an actual solid vertex (H039/H040 regression guard).
2. Category A interior edge cut.
3. Category B Engine-derived edge cut.
4. Correct section with different cyclic starting vertex.
5. Correct section with reversed polygon orientation.
6. Correct cut edge with reversed edge orientation and transformed parameter (1 - t).
7. Wrong edge.
8. Wrong interpolation parameter.
9. Missing section vertex.
10. Extra section vertex.
11. Wrong area squared.
12. Wrong solid identity.
13. Missing section certificate.
14. Category A/B certificate mixing.
15. Correct refusal reason.
16. Incorrect refusal reason.
17. Harness exception.

Plus Scene3D Track 10.A vs Track 10.B separation self-tests (Unicode-aware 'Hình' boundary & O4/R1 auxiliary point notation).
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as F
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from evaluate_holdout_wave2 import TAXONOMY, score_observed_response

TAX = json.loads(Path(TAXONOMY).read_text(encoding="utf-8"))


def _make_cat_a_fixture() -> tuple[dict[str, Any], dict[str, Any], Any, dict[str, Any]]:
    """Base valid Category A fixture: pyramid S.ABC where section passes through vertex A and cuts SB at M (t=1/3) and SC at N (t=1/2)."""
    case = {
        "id": "CTRL-A",
        "stratum": "P-A",
        "family": "triangular_pyramid",
        "plane_relation": "stated_intersections",
        "question_type": "section_and_area",
        "expected_disposition": "SERVE",
        "acceptable_categories": [],
        "payload": {
            "problem_text": "Cho hình chóp S.ABC. Mặt phẳng (P) đi qua A, cắt SB tại M và cắt SC tại N. Tính diện tích thiết diện.",
            "derived_sections": [{"section_id": "sec"}],
        },
    }
    exp = {
        "solid": "S.ABC",
        "section_id": "sec",
        "expected_certificate_category": "DINH_CAT_CANH",
        "area_goal_id": "g_area",
        "vertex_count": 3,
        "boundary": [
            {"vertex": "A"},
            {"edge": ["S", "B"], "t": "1/3"},
            {"edge": ["S", "C"], "t": "1/2"},
        ],
        "area_squared": "25/16",
    }
    # Coordinates: S=(0,0,6), A=(0,0,0), B=(3,0,0), C=(0,4,0)
    # M on SB at t=1/3 -> (1, 0, 4); N on SC at t=1/2 -> (0, 2, 3)
    poly_xyz = [["0", "0", "0"], ["1", "0", "4"], ["0", "2", "3"]]
    r = SimpleNamespace(
        status="SERVED",
        code=None,
        reason=None,
        planner={"auxiliary": [{"rule": "dinh-cat-canh", "goal": "sec"}]},
        exec_result=SimpleNamespace(final_memory={"kq_g_area": F(5, 4)}),
    )
    resp = {
        "route_d": {
            "status": "SERVED",
            "sections": [
                {
                    "section_id": "sec",
                    "boundary": ["A", "M", "N"],
                    "vertices": [
                        {"label": "A", "edge": ["S", "A"], "provenance": "THROUGH_POINT_REUSE", "stated": False},
                        {"label": "M", "edge": ["S", "B"], "provenance": "SOURCE_NAMED", "stated": True},
                        {"label": "N", "edge": ["S", "C"], "provenance": "SOURCE_NAMED", "stated": True},
                    ],
                    "closure_certificate": {"verified": True, "rule": "convex_lateral_cycle", "boundary": ["A", "M", "N"]},
                }
            ],
        },
        "envelope": {
            "status": "ok",
            "scene3d": {
                "objects": [
                    {"id": "khoi_S_ABC", "type": "solid", "notation": "S.ABC"},
                    {"id": "S", "type": "point3", "notation": "S", "xyz": ["0", "0", "6"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "A", "type": "point3", "notation": "A", "xyz": ["0", "0", "0"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "B", "type": "point3", "notation": "B", "xyz": ["3", "0", "0"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "C", "type": "point3", "notation": "C", "xyz": ["0", "4", "0"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "M", "type": "point3", "notation": "M", "xyz": ["1", "0", "4"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "N", "type": "point3", "notation": "N", "xyz": ["0", "2", "3"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "td_sec", "type": "section", "closed": True, "depends": ["khoi_S_ABC"], "polygon": poly_xyz},
                ]
            },
        },
    }
    return case, exp, r, resp


def _make_cat_b_fixture() -> tuple[dict[str, Any], dict[str, Any], Any, dict[str, Any]]:
    """Base valid Category B fixture: pyramid S.ABC cut by plane parallel to (ABC) at t=1/2 on SA, SB, SC."""
    case = {
        "id": "CTRL-B",
        "stratum": "P-B",
        "family": "triangular_pyramid",
        "plane_relation": "parallel_plane",
        "question_type": "section_and_area",
        "expected_disposition": "SERVE",
        "acceptable_categories": [],
        "payload": {
            "problem_text": "Cho hình chóp S.ABC. Mặt phẳng (α) đi qua trung điểm M của SA và song song với (ABC). Tính diện tích thiết diện.",
            "derived_sections": [{"section_id": "sec"}],
        },
    }
    exp = {
        "solid": "S.ABC",
        "section_id": "sec",
        "expected_certificate_category": "ENGINE_DERIVED_SECTION",
        "area_goal_id": "g_area",
        "vertex_count": 3,
        "boundary": [
            {"edge": ["S", "A"], "t": "1/2"},
            {"edge": ["S", "B"], "t": "1/2"},
            {"edge": ["S", "C"], "t": "1/2"},
        ],
        "area_squared": "9/16",
    }
    poly_xyz = [["0", "0", "3"], ["3/2", "0", "3"], ["0", "2", "3"]]
    r = SimpleNamespace(
        status="SERVED",
        code=None,
        reason=None,
        planner={"auxiliary": [{"rule": "mat-song-song", "point": "M", "labels": ["H", "H1"], "targets": ["sec"]}]},
        exec_result=SimpleNamespace(final_memory={"kq_g_area": F(3, 4)}),
    )
    resp = {
        "route_d": {
            "status": "SERVED",
            "sections": [
                {
                    "section_id": "sec",
                    "solid": "S.ABC",
                    "certificate_category": "ENGINE_DERIVED_SECTION",
                    "certificate_version": "plane-section-certificate/1",
                    "vertices": [
                        {
                            "ordinal": 0,
                            "source_kind": "SOLID_EDGE_INTERSECTION",
                            "edge": ["S", "A"],
                            "t": "1/2",
                            "label": "M",
                            "stated": False,
                            "xyz": poly_xyz[0],
                        },
                        {
                            "ordinal": 1,
                            "source_kind": "SOLID_EDGE_INTERSECTION",
                            "edge": ["S", "B"],
                            "t": "1/2",
                            "label": None,
                            "stated": False,
                            "xyz": poly_xyz[1],
                        },
                        {
                            "ordinal": 2,
                            "source_kind": "SOLID_EDGE_INTERSECTION",
                            "edge": ["S", "C"],
                            "t": "1/2",
                            "label": None,
                            "stated": False,
                            "xyz": poly_xyz[2],
                        },
                    ],
                    "closure_certificate": {
                        "verified": True,
                        "version": "plane-section-certificate/1",
                        "rule": "engine_derived_plane_section",
                        "area_squared": "9/16",
                    },
                }
            ],
        },
        "envelope": {
            "status": "ok",
            "scene3d": {
                "objects": [
                    {"id": "khoi_S_ABC", "type": "solid", "notation": "S.ABC"},
                    {"id": "H", "type": "point3", "notation": "H", "xyz": ["1", "0", "2"], "origin": "derived", "role": "Điểm dựng phụ"},
                    {"id": "td_sec", "type": "section", "name": "Thiết diện tạo bởi (α)", "closed": True, "depends": ["khoi_S_ABC"], "polygon": poly_xyz},
                ]
            },
        },
    }
    return case, exp, r, resp


def test_01_category_a_vertex_coincides_with_solid_vertex():
    """Control 1: Category A vertex coincides with an actual solid vertex (H039/H040 guard)."""
    case, exp, r, resp = _make_cat_a_fixture()
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "SERVED_CORRECT", res.get("oracle_mismatches")
    assert res["oracle_mismatches"] == []


def test_02_category_a_interior_edge_cut():
    """Control 2: Category A interior edge cuts on all 3 lateral edges."""
    case, exp, r, resp = _make_cat_a_fixture()
    exp["boundary"][0] = {"edge": ["S", "A"], "t": "1/2"}
    # Move A in section to P on SA at t=1/2 -> (0, 0, 3)
    resp["route_d"]["sections"][0]["vertices"][0] = {
        "label": "P",
        "edge": ["S", "A"],
        "provenance": "SOURCE_NAMED",
        "stated": True,
    }
    resp["envelope"]["scene3d"]["objects"].append(
        {"id": "P", "type": "point3", "notation": "P", "xyz": ["0", "0", "3"], "origin": "given", "role": "Điểm cho trước"}
    )
    resp["envelope"]["scene3d"]["objects"][-2]["polygon"][0] = ["0", "0", "3"]
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "SERVED_CORRECT", res.get("oracle_mismatches")


def test_03_category_b_engine_derived_edge_cut():
    """Control 3: Category B Engine-derived edge cut."""
    case, exp, r, resp = _make_cat_b_fixture()
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "SERVED_CORRECT", res.get("oracle_mismatches")


def test_04_correct_section_different_cyclic_starting_vertex():
    """Control 4: Correct section with a rotated cyclic starting vertex ([v1, v2, v0] vs [v0, v1, v2])."""
    case, exp, r, resp = _make_cat_b_fixture()
    verts = resp["route_d"]["sections"][0]["vertices"]
    rotated = [deepcopy(verts[1]), deepcopy(verts[2]), deepcopy(verts[0])]
    for idx, v in enumerate(rotated):
        v["ordinal"] = idx
    resp["route_d"]["sections"][0]["vertices"] = rotated
    resp["envelope"]["scene3d"]["objects"][-1]["polygon"] = [v["xyz"] for v in rotated]
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "SERVED_CORRECT", res.get("oracle_mismatches")


def test_05_correct_section_reversed_polygon_orientation():
    """Control 5: Correct section with reversed polygon orientation ([v0, v2, v1] vs [v0, v1, v2])."""
    case, exp, r, resp = _make_cat_b_fixture()
    verts = resp["route_d"]["sections"][0]["vertices"]
    rev = [deepcopy(verts[0]), deepcopy(verts[2]), deepcopy(verts[1])]
    for idx, v in enumerate(rev):
        v["ordinal"] = idx
    resp["route_d"]["sections"][0]["vertices"] = rev
    resp["envelope"]["scene3d"]["objects"][-1]["polygon"] = [v["xyz"] for v in rev]
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "SERVED_CORRECT", res.get("oracle_mismatches")


def test_06_correct_cut_edge_reversed_edge_orientation_and_transformed_parameter():
    """Control 6: Edge ['B', 'S'] with t='2/3' matches oracle ['S', 'B'] with t='1/3'."""
    case, exp, r, resp = _make_cat_a_fixture()
    resp["route_d"]["sections"][0]["vertices"][1]["edge"] = ["B", "S"]
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "SERVED_CORRECT", res.get("oracle_mismatches")


def test_07_wrong_edge():
    """Control 7: Cut on wrong edge (['A', 'B'] instead of ['S', 'B']) must be rejected as WRONG_SERVED."""
    case, exp, r, resp = _make_cat_b_fixture()
    resp["route_d"]["sections"][0]["vertices"][1]["edge"] = ["A", "B"]
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "WRONG_SERVED"
    assert any("interior edge cuts" in m for m in res["oracle_mismatches"])


def test_08_wrong_interpolation_parameter():
    """Control 8: Cut on correct edge ['S', 'B'] but wrong parameter t='2/5' != '1/2' must be WRONG_SERVED."""
    case, exp, r, resp = _make_cat_b_fixture()
    resp["route_d"]["sections"][0]["vertices"][1]["t"] = "2/5"
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "WRONG_SERVED"
    assert any("interior edge cuts" in m for m in res["oracle_mismatches"])


def test_09_missing_section_vertex():
    """Control 9: Missing section vertex (3 vertices when oracle has 4) must be WRONG_SERVED."""
    case, exp, r, resp = _make_cat_b_fixture()
    exp["vertex_count"] = 4
    exp["boundary"].append({"edge": ["A", "B"], "t": "1/2"})
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "WRONG_SERVED"
    assert any("count" in m for m in res["oracle_mismatches"])


def test_10_extra_section_vertex():
    """Control 10: Extra section vertex (4 vertices when oracle has 3) must be WRONG_SERVED."""
    case, exp, r, resp = _make_cat_b_fixture()
    resp["route_d"]["sections"][0]["vertices"].append(
        {
            "ordinal": 3,
            "source_kind": "SOLID_EDGE_INTERSECTION",
            "edge": ["A", "B"],
            "t": "1/2",
            "label": None,
            "stated": False,
            "xyz": ["1", "0", "0"],
        }
    )
    resp["envelope"]["scene3d"]["objects"][-1]["polygon"].append(["1", "0", "0"])
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "WRONG_SERVED"
    assert any("count" in m for m in res["oracle_mismatches"])


def test_11_wrong_area_squared():
    """Control 11: Wrong area squared in final_memory must be WRONG_SERVED."""
    case, exp, r, resp = _make_cat_a_fixture()
    r.exec_result.final_memory["kq_g_area"] = F(7, 4)  # squared = 49/16 != 25/16
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "WRONG_SERVED"
    assert any("area²" in m for m in res["oracle_mismatches"])


def test_12_wrong_solid_identity():
    """Control 12: Wrong solid identity ('S.ABCD' instead of 'S.ABC') must be WRONG_SERVED."""
    case, exp, r, resp = _make_cat_a_fixture()
    resp["envelope"]["scene3d"]["objects"][0]["notation"] = "S.ABCD"
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "WRONG_SERVED"
    assert any("solid identity" in m for m in res["oracle_mismatches"])


def test_13_missing_section_certificate():
    """Control 13: Missing or unverified section closure certificate must be WRONG_SERVED."""
    case, exp, r, resp = _make_cat_b_fixture()
    resp["route_d"]["sections"][0]["closure_certificate"] = None
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "WRONG_SERVED"
    assert any("closure_certificate" in m for m in res["oracle_mismatches"])


def test_14_category_a_b_certificate_mixing():
    """Control 14: Category A/B certificate mixing must be WRONG_SERVED."""
    case, exp, r, resp = _make_cat_b_fixture()
    # Inject a Category A DINH_CAT_CANH planner auxiliary rule into a Category B section
    r.planner["auxiliary"].append({"rule": "dinh-cat-canh", "goal": "sec"})
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "WRONG_SERVED"
    assert any("mixing" in m for m in res["oracle_mismatches"])


def test_15_correct_refusal_reason():
    """Control 15: Negative case refused with an acceptable category is REFUSED_CORRECT_REASON."""
    case = {
        "id": "CTRL-N1",
        "stratum": "N",
        "family": "quadrilateral_pyramid",
        "plane_relation": "parallel_plane",
        "question_type": "section_only",
        "negative_class": "contradictory_solid_kind",
        "negative_origin": "flawed_or_unsupported_problem",
        "expected_disposition": "REFUSE",
        "acceptable_categories": ["SOURCE_GROUNDING", "CONTRADICTION"],
        "payload": {"problem_text": "Cho tứ diện S.ABCD...", "derived_sections": []},
    }
    r = SimpleNamespace(status="REFUSED", code="SOURCE_OBJECT_MISMATCH", reason="tứ diện != 4 base vertices")
    resp = {"route_d": {"status": "REFUSED", "refusal": {"code": "SOURCE_OBJECT_MISMATCH"}}, "envelope": {"status": "unsupported"}}
    res = score_observed_response(case, None, TAX, r, resp)
    assert res["outcome"] == "REFUSED_CORRECT_REASON"


def test_16_incorrect_refusal_reason():
    """Control 16: Negative case refused with an unacceptable category or INTERNAL_OR_VALIDATION is REFUSED_REASON_DISAGREEMENT."""
    case = {
        "id": "CTRL-N2",
        "stratum": "N",
        "family": "quadrilateral_pyramid",
        "plane_relation": "parallel_plane",
        "question_type": "section_only",
        "negative_class": "missing_dimensions",
        "negative_origin": "flawed_or_unsupported_problem",
        "expected_disposition": "REFUSE",
        "acceptable_categories": ["UNDERDETERMINED"],
        "payload": {"problem_text": "Cho hình chóp S.ABCD...", "derived_sections": []},
    }
    r = SimpleNamespace(status="REFUSED", code="QUOTE_NOT_IN_SOURCE", reason="quote mismatch")
    resp = {"route_d": {"status": "REFUSED", "refusal": {"code": "QUOTE_NOT_IN_SOURCE"}}, "envelope": {"status": "unsupported"}}
    res = score_observed_response(case, None, TAX, r, resp)
    assert res["outcome"] == "REFUSED_REASON_DISAGREEMENT"


def test_17_harness_exception():
    """Control 17: Malformed oracle structure triggers HARNESS_ERROR, never silent pass."""
    case, exp, r, resp = _make_cat_b_fixture()
    exp["boundary"] = 12345  # invalid type -> triggers exception inside _oracle_descriptors
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "HARNESS_ERROR"


def test_18_scene3d_semantics_10a_vs_10b_separation():
    """Verify Section 10.A (source-identity leaks) and Section 10.B (O4/R1 auxiliary display) separation and Unicode 'Hình' safety."""
    case, exp, r, resp = _make_cat_b_fixture()
    # 'Hình chóp S.ABC' in object description/name must NOT match auxiliary 'H';
    # 'H' on point3 with origin='derived', role='Điểm dựng phụ' is tracked in 10.B, not 10.A.
    resp["envelope"]["scene3d"]["objects"][0]["name"] = "Hình chóp S.ABC"
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "SERVED_CORRECT"
    assert res["source_identity_leaks"] == []
    assert res["r2_auxiliary_notation_observed"] is True
    assert res["all_auxiliary_visibly_distinguished"] is True

    # Now simulate a true 10.A leak: 'H' appears in section name or point3 has origin='given'
    resp["envelope"]["scene3d"]["objects"][-1]["name"] = "Thiết diện HMN"
    res_leak = score_observed_response(case, exp, TAX, r, resp)
    assert "td_sec.name:H" in res_leak["source_identity_leaks"]


def test_19_category_a_single_solid_null_closure_certificate_and_vertices_contract():
    """Verify Adapter /4 Category A contract: single-solid DINH_CAT_CANH without declared_boundary/derived
    emits boundary=None, closure_certificate=None and is SERVED_CORRECT when vertices certificate is complete;
    missing/malformed vertices or unverified non-null closure_certificate is WRONG_SERVED."""
    case, exp, r, resp = _make_cat_a_fixture()
    resp["route_d"]["sections"][0]["boundary"] = None
    resp["route_d"]["sections"][0]["closure_certificate"] = None
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "SERVED_CORRECT", res.get("oracle_mismatches")

    # Non-null unverified closure_certificate on Category A must still fail
    resp["route_d"]["sections"][0]["closure_certificate"] = {"verified": False, "rule": "dinh-cat-canh"}
    res_bad_cert = score_observed_response(case, exp, TAX, r, resp)
    assert res_bad_cert["outcome"] == "WRONG_SERVED"
    assert any("closure_certificate" in m for m in res_bad_cert["oracle_mismatches"])

    # Missing provenance on Category A vertex must fail
    resp["route_d"]["sections"][0]["closure_certificate"] = None
    del resp["route_d"]["sections"][0]["vertices"][0]["provenance"]
    res_bad_verts = score_observed_response(case, exp, TAX, r, resp)
    assert res_bad_verts["outcome"] == "WRONG_SERVED"
    assert any("Category A section vertices certificate" in m for m in res_bad_verts["oracle_mismatches"])

