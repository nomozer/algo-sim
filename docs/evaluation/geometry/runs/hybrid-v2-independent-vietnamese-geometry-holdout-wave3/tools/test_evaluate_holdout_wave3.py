# -*- coding: utf-8 -*-
"""Synthetic scorer qualification & mutation controls for `evaluate_holdout_wave3.py`.

Verifies all 22 mandatory synthetic control categories required by Owner GO Section 3 BEFORE any Wave 3 corpus is created:
1. Source vertex `A'`, `A′`, and internal `A_prime` (including 4-vertex Category A section with `A'` at non-zero polygon index).
2. No machine-ID leakage (`_prime` or internal auxiliary labels) onto learner-facing surfaces.
3. Triangle with 3 vertices.
4. Quadrilateral with 4 vertices.
5. Polygon with >= 5 vertices (pentagon / hexagon).
6. Cyclic shift invariance.
7. Reversed orientation invariance.
8. Non-cyclic vertex permutation rejection (e.g. bow-tie `[v0, v2, v1, v3]`).
9. Duplicate vertex / duplicate coordinate rejection.
10. Solid vertex reuse at `t=0` or `t=1`.
11. Interior edge intersection at `0 < t < 1`.
12. Reversed edge endpoint orientation with transformed parameter `1 - t`.
13. Category A `DINH_CAT_CANH`.
14. Category B `ENGINE_DERIVED_SECTION`.
15. Category A/B mixing tamper rejection.
16. Wrong solid identity rejection.
17. Wrong edge topology rejection.
18. Wrong area squared rejection.
19. Missing section certificate rejection.
20. Wrong refusal reason rejection (`REFUSED_REASON_DISAGREEMENT` vs `REFUSED_CORRECT_REASON`).
21. Uncaught product exception handling (`PRODUCT_EXCEPTION`).
22. Missing oracle entry rejection (`no oracle entry for a served case` / `HARNESS_ERROR` on malformed oracle).
Plus:
- Explicit guard proving the scorer NEVER defaults an unfound vertex to polygon index `0`.
- Systematic mutation control suite verifying 100% kill rate across valid 3-vertex, 4-vertex, and 5-vertex fixtures.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from evaluate_holdout_wave3 import RUN, TAXONOMY, score_case, score_observed_response  # noqa: E402

TAX = json.loads(Path(TAXONOMY).read_text(encoding="utf-8"))


def _make_cat_a_triangle_fixture() -> tuple[dict[str, Any], dict[str, Any], Any, dict[str, Any]]:
    """Valid 3-vertex Category A fixture on prism ABC.A'B'C' with primed vertex A' (internal id A_prime, notation A′) at index 1."""
    case = {
        "id": "CTRL-CAT-A-TRI",
        "stratum": "P-A",
        "family": "right_triangular_prism",
        "plane_relation": "stated_intersections",
        "question_type": "section_and_area",
        "expected_disposition": "SERVE",
        "acceptable_categories": [],
        "payload": {
            "problem_text": "Cho hình lăng trụ đứng ABC.A'B'C'. Mặt phẳng (α) đi qua A', cắt BB' tại M và CC' tại N.",
            "derived_sections": [{"section_id": "sec"}],
        },
    }
    exp = {
        "solid": "ABC.A'B'C'",
        "section_id": "sec",
        "expected_certificate_category": "DINH_CAT_CANH",
        "area_goal_id": "mg1",
        "vertex_count": 3,
        "boundary": [
            {"vertex": "A'"},
            {"edge": ["B", "B'"], "t": "3/4"},
            {"edge": ["C", "C'"], "t": "1/2"},
        ],
        "area_squared": "1875/8",
    }
    # Polygon order [M, A', N] so A' is at index 1 (not 0)
    poly_xyz = [["1", "0", "3/4"], ["0", "0", "1"], ["0", "1", "1/2"]]
    r = SimpleNamespace(
        status="SERVED",
        code=None,
        reason=None,
        planner={"auxiliary": [{"rule": "dinh-cat-canh", "goal": "sec"}]},
        exec_result=SimpleNamespace(final_memory={"kq_mg1": {"he": "25/4", "can": 6}}),
    )
    resp = {
        "route_d": {
            "status": "SERVED",
            "sections": [
                {
                    "section_id": "sec",
                    "boundary": None,
                    "vertices": [
                        {"label": "A'", "edge": ["A", "A'"], "provenance": "THROUGH_POINT_REUSE", "stated": False},
                        {"label": "M", "edge": ["B", "B'"], "provenance": "SOURCE_NAMED", "stated": True},
                        {"label": "N", "edge": ["C", "C'"], "provenance": "SOURCE_NAMED", "stated": True},
                    ],
                    "closure_certificate": None,
                }
            ],
        },
        "envelope": {
            "status": "ok",
            "answer": "25√6/4",
            "scene3d": {
                "objects": [
                    {"id": "khoi_ABC_A_primeB_primeC_prime", "type": "solid", "notation": "ABC.A′B′C′"},
                    {"id": "A", "type": "point3", "notation": "A", "xyz": ["0", "0", "0"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "B", "type": "point3", "notation": "B", "xyz": ["1", "0", "0"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "C", "type": "point3", "notation": "C", "xyz": ["0", "1", "0"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "A_prime", "type": "point3", "notation": "A′", "xyz": ["0", "0", "1"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "B_prime", "type": "point3", "notation": "B′", "xyz": ["1", "0", "1"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "C_prime", "type": "point3", "notation": "C′", "xyz": ["0", "1", "1"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "M", "type": "point3", "notation": "M", "xyz": ["1", "0", "3/4"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "N", "type": "point3", "notation": "N", "xyz": ["0", "1", "1/2"], "origin": "given", "role": "Điểm cho trước"},
                    {
                        "id": "td_sec",
                        "type": "section",
                        "label": "Thiết diện MA′N",
                        "notation": "MA′N",
                        "closed": True,
                        "depends": ["khoi_ABC_A_primeB_primeC_prime"],
                        "polygon": poly_xyz,
                    },
                ]
            },
        },
    }
    return case, exp, r, resp


def _make_cat_a_quad_fixture() -> tuple[dict[str, Any], dict[str, Any], Any, dict[str, Any]]:
    """Valid 4-vertex Category A fixture on cuboid ABCD.A'B'C'D' with primed vertex A' at polygon index 1 (W2-A10 guard)."""
    case = {
        "id": "CTRL-CAT-A-QUAD",
        "stratum": "P-A",
        "family": "cuboid",
        "plane_relation": "stated_intersections",
        "question_type": "section_only",
        "expected_disposition": "SERVE",
        "acceptable_categories": [],
        "payload": {
            "problem_text": "Cho hình hộp chữ nhật ABCD.A'B'C'D'. Mặt phẳng (Q) đi qua A' và vuông góc với AC', cắt BB', CC', DD'.",
            "derived_sections": [{"section_id": "sec"}],
        },
    }
    exp = {
        "solid": "ABCD.A'B'C'D'",
        "section_id": "sec",
        "expected_certificate_category": "DINH_CAT_CANH",
        "area_goal_id": None,
        "vertex_count": 4,
        "boundary": [
            {"vertex": "A'"},
            {"edge": ["B", "B'"], "t": "8/9"},
            {"edge": ["C", "C'"], "t": "4/9"},
            {"edge": ["D", "D'"], "t": "5/9"},
        ],
        "area_squared": "504",
    }
    # Polygon order [I, A', I2, I1]: reversed + shifted by 2 relative to [A', I, I1, I2]
    poly_xyz = [["1", "0", "8/9"], ["0", "0", "1"], ["0", "1", "5/9"], ["1", "1", "4/9"]]
    r = SimpleNamespace(
        status="SERVED",
        code=None,
        reason=None,
        planner={"auxiliary": [{"rule": "dinh-cat-canh", "goal": "sec", "labels": ["I", "I1", "I2"]}]},
        exec_result=SimpleNamespace(final_memory={}),
    )
    resp = {
        "route_d": {
            "status": "SERVED",
            "sections": [
                {
                    "section_id": "sec",
                    "boundary": None,
                    "vertices": [
                        {"label": "A'", "edge": ["A", "A'"], "provenance": "THROUGH_POINT_REUSE", "stated": False},
                        {"label": "I", "edge": ["B", "B'"], "provenance": "STATED_EDGE_UNNAMED_CUT", "stated": True},
                        {"label": "I1", "edge": ["C", "C'"], "provenance": "STATED_EDGE_UNNAMED_CUT", "stated": True},
                        {"label": "I2", "edge": ["D", "D'"], "provenance": "STATED_EDGE_UNNAMED_CUT", "stated": True},
                    ],
                    "closure_certificate": None,
                }
            ],
        },
        "envelope": {
            "status": "ok",
            "scene3d": {
                "objects": [
                    {"id": "khoi_ABCD_A_primeB_primeC_primeD_prime", "type": "solid", "notation": "ABCD.A′B′C′D′"},
                    {"id": "A", "type": "point3", "notation": "A", "xyz": ["0", "0", "0"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "B", "type": "point3", "notation": "B", "xyz": ["1", "0", "0"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "C", "type": "point3", "notation": "C", "xyz": ["1", "1", "0"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "D", "type": "point3", "notation": "D", "xyz": ["0", "1", "0"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "A_prime", "type": "point3", "notation": "A′", "xyz": ["0", "0", "1"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "B_prime", "type": "point3", "notation": "B′", "xyz": ["1", "0", "1"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "C_prime", "type": "point3", "notation": "C′", "xyz": ["1", "1", "1"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "D_prime", "type": "point3", "notation": "D′", "xyz": ["0", "1", "1"], "origin": "given", "role": "Điểm cho trước"},
                    {"id": "I", "type": "point3", "notation": None, "xyz": ["1", "0", "8/9"], "origin": "derived", "role": "Điểm dựng phụ"},
                    {"id": "I1", "type": "point3", "notation": None, "xyz": ["1", "1", "4/9"], "origin": "derived", "role": "Điểm dựng phụ"},
                    {"id": "I2", "type": "point3", "notation": None, "xyz": ["0", "1", "5/9"], "origin": "derived", "role": "Điểm dựng phụ"},
                    {
                        "id": "td_sec",
                        "type": "section",
                        "label": "Thiết diện bởi (Q)",
                        "notation": None,
                        "closed": True,
                        "depends": ["khoi_ABCD_A_primeB_primeC_primeD_prime"],
                        "polygon": poly_xyz,
                    },
                ]
            },
        },
    }
    return case, exp, r, resp


def _make_cat_b_pentagon_fixture() -> tuple[dict[str, Any], dict[str, Any], Any, dict[str, Any]]:
    """Valid 5-vertex Category B fixture on cube ABCD.A'B'C'D'."""
    case = {
        "id": "CTRL-CAT-B-PENT",
        "stratum": "P-B",
        "family": "cube",
        "plane_relation": "perpendicular_line",
        "question_type": "section_and_area",
        "expected_disposition": "SERVE",
        "acceptable_categories": [],
        "payload": {
            "problem_text": "Cho hình lập phương ABCD.A'B'C'D'. Mặt phẳng (P) cắt 5 cạnh tạo thành thiết diện ngũ giác.",
            "derived_sections": [{"section_id": "sec"}],
        },
    }
    exp = {
        "solid": "ABCD.A'B'C'D'",
        "section_id": "sec",
        "expected_certificate_category": "ENGINE_DERIVED_SECTION",
        "area_goal_id": "mg1",
        "vertex_count": 5,
        "boundary": [
            {"edge": ["A", "B"], "t": "1/2"},
            {"edge": ["B", "C"], "t": "1/2"},
            {"edge": ["C", "C'"], "t": "1/2"},
            {"edge": ["D'", "C'"], "t": "1/2"},
            {"edge": ["A", "A'"], "t": "1/2"},
        ],
        "area_squared": "27/16",
    }
    poly_xyz = [
        ["1/2", "0", "0"],
        ["1", "1/2", "0"],
        ["1", "1", "1/2"],
        ["1/2", "1", "1"],
        ["0", "0", "1/2"],
    ]
    r = SimpleNamespace(
        status="SERVED",
        code=None,
        reason=None,
        planner={"auxiliary": [{"rule": "mat-vuong-duong", "point": "M", "labels": ["H", "H1"], "targets": ["sec"]}]},
        exec_result=SimpleNamespace(final_memory={"kq_mg1": {"he": "3/4", "can": 3}}),
    )
    resp = {
        "route_d": {
            "status": "SERVED",
            "sections": [
                {
                    "section_id": "sec",
                    "solid": "ABCD.A'B'C'D'",
                    "certificate_category": "ENGINE_DERIVED_SECTION",
                    "certificate_version": "plane-section-certificate/1",
                    "vertices": [
                        {"ordinal": 0, "source_kind": "SOLID_EDGE_INTERSECTION", "edge": ["A", "B"], "t": "1/2", "label": None, "stated": False, "xyz": poly_xyz[0]},
                        {"ordinal": 1, "source_kind": "SOLID_EDGE_INTERSECTION", "edge": ["B", "C"], "t": "1/2", "label": None, "stated": False, "xyz": poly_xyz[1]},
                        {"ordinal": 2, "source_kind": "SOLID_EDGE_INTERSECTION", "edge": ["C", "C'"], "t": "1/2", "label": None, "stated": False, "xyz": poly_xyz[2]},
                        {"ordinal": 3, "source_kind": "SOLID_EDGE_INTERSECTION", "edge": ["D'", "C'"], "t": "1/2", "label": None, "stated": False, "xyz": poly_xyz[3]},
                        {"ordinal": 4, "source_kind": "SOLID_EDGE_INTERSECTION", "edge": ["A", "A'"], "t": "1/2", "label": None, "stated": False, "xyz": poly_xyz[4]},
                    ],
                    "closure_certificate": {
                        "verified": True,
                        "version": "plane-section-certificate/1",
                        "rule": "engine_derived_plane_section",
                        "area_squared": "27/16",
                    },
                }
            ],
        },
        "envelope": {
            "status": "ok",
            "answer": "3√3/4",
            "scene3d": {
                "objects": [
                    {"id": "khoi_ABCD_A_primeB_primeC_primeD_prime", "type": "solid", "notation": "ABCD.A′B′C′D′"},
                    {"id": "H", "type": "point3", "notation": "H", "xyz": ["1", "0", "0"], "origin": "derived", "role": "Điểm dựng phụ"},
                    {"id": "td_sec", "type": "section", "name": "Thiết diện bởi (P)", "closed": True, "depends": ["khoi_ABCD_A_primeB_primeC_primeD_prime"], "polygon": poly_xyz},
                ]
            },
        },
    }
    return case, exp, r, resp


def test_01_primed_source_vertex_and_internal_a_prime():
    """Control 1: Source vertex A', A′ and internal A_prime on both 3-vertex and 4-vertex Category A sections."""
    for fn in (_make_cat_a_triangle_fixture, _make_cat_a_quad_fixture):
        case, exp, r, resp = fn()
        res = score_observed_response(case, exp, TAX, r, resp)
        assert res["outcome"] == "SERVED_CORRECT", res.get("oracle_mismatches")
        assert res["oracle_mismatches"] == []


def test_02_no_machine_id_leakage_to_learner_surface():
    """Control 2: Raw `_prime` or internal auxiliary labels leaking onto learner-facing fields must fail as WRONG_SERVED."""
    case, exp, r, resp = _make_cat_a_triangle_fixture()
    resp["envelope"]["scene3d"]["objects"][-1]["notation"] = "MA_primeN"
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "WRONG_SERVED"
    assert "td_sec.notation:_prime_leak" in res["machine_id_leaks"]

    # Also check fresh auxiliary point masquerading as origin='given'
    case2, exp2, r2, resp2 = _make_cat_b_pentagon_fixture()
    resp2["envelope"]["scene3d"]["objects"][1]["origin"] = "given"
    res2 = score_observed_response(case2, exp2, TAX, r2, resp2)
    assert res2["outcome"] == "WRONG_SERVED"
    assert "H.false_given_origin:H" in res2["source_identity_leaks"]


def test_03_triangle_3_vertices():
    """Control 3: 3-vertex triangle section."""
    case, exp, r, resp = _make_cat_a_triangle_fixture()
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "SERVED_CORRECT"
    assert exp["vertex_count"] == 3


def test_04_quadrilateral_4_vertices():
    """Control 4: 4-vertex quadrilateral section."""
    case, exp, r, resp = _make_cat_a_quad_fixture()
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "SERVED_CORRECT"
    assert exp["vertex_count"] == 4


def test_05_polygon_5_or_more_vertices():
    """Control 5: 5-vertex pentagon section."""
    case, exp, r, resp = _make_cat_b_pentagon_fixture()
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "SERVED_CORRECT"
    assert exp["vertex_count"] == 5


def test_06_cyclic_shift():
    """Control 6: Cyclic shift of polygon vertices preserves SERVED_CORRECT."""
    case, exp, r, resp = _make_cat_b_pentagon_fixture()
    verts = resp["route_d"]["sections"][0]["vertices"]
    shifted = verts[2:] + verts[:2]
    for idx, v in enumerate(shifted):
        v["ordinal"] = idx
    resp["route_d"]["sections"][0]["vertices"] = shifted
    resp["envelope"]["scene3d"]["objects"][-1]["polygon"] = [v["xyz"] for v in shifted]
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "SERVED_CORRECT", res.get("oracle_mismatches")


def test_07_reversed_orientation():
    """Control 7: Reversed orientation of polygon vertices preserves SERVED_CORRECT."""
    case, exp, r, resp = _make_cat_b_pentagon_fixture()
    verts = list(reversed(resp["route_d"]["sections"][0]["vertices"]))
    for idx, v in enumerate(verts):
        v["ordinal"] = idx
    resp["route_d"]["sections"][0]["vertices"] = verts
    resp["envelope"]["scene3d"]["objects"][-1]["polygon"] = [v["xyz"] for v in verts]
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "SERVED_CORRECT", res.get("oracle_mismatches")


def test_08_non_cyclic_vertex_permutation_rejected():
    """Control 8: Non-cyclic vertex permutation (bow-tie `[v0, v2, v1, v3]`) is rejected as WRONG_SERVED."""
    case, exp, r, resp = _make_cat_a_quad_fixture()
    poly = resp["envelope"]["scene3d"]["objects"][-1]["polygon"]
    # Swap index 0 and index 1 -> [A', I, I2, I1] which is a non-cyclic bow-tie relative to [A', I, I1, I2]
    resp["envelope"]["scene3d"]["objects"][-1]["polygon"] = [poly[1], poly[0], poly[2], poly[3]]
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "WRONG_SERVED"
    assert any("polygon cyclic order" in m for m in res["oracle_mismatches"])


def test_09_duplicate_vertices_rejected():
    """Control 9: Duplicate vertices or duplicate coordinates in polygon/section are rejected as WRONG_SERVED."""
    case, exp, r, resp = _make_cat_a_quad_fixture()
    # Make I2 have the same coordinates as I
    resp["envelope"]["scene3d"]["objects"][-1]["polygon"][2] = ["1", "0", "8/9"]
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "WRONG_SERVED"
    assert any("duplicate" in m for m in res["oracle_mismatches"])


def test_10_solid_vertex_reuse_at_t0_or_t1():
    """Control 10: Solid vertex reuse at t=0 or t=1 in both Category A and Category B."""
    case, exp, r, resp = _make_cat_b_pentagon_fixture()
    # Replace first vertex with SOLID_VERTEX B at t=1 on edge [A, B]
    exp["boundary"][0] = {"vertex": "B"}
    resp["route_d"]["sections"][0]["vertices"][0] = {
        "ordinal": 0,
        "source_kind": "SOLID_VERTEX",
        "edge": ["A", "B"],
        "t": "1",
        "label": "B",
        "stated": False,
        "xyz": ["1", "0", "0"],
    }
    resp["envelope"]["scene3d"]["objects"][-1]["polygon"][0] = ["1", "0", "0"]
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "SERVED_CORRECT", res.get("oracle_mismatches")


def test_11_interior_edge_intersection():
    """Control 11: Interior edge intersection 0 < t < 1 and rejection of out-of-range t."""
    case, exp, r, resp = _make_cat_b_pentagon_fixture()
    resp["route_d"]["sections"][0]["vertices"][0]["t"] = "3/2"
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "WRONG_SERVED"
    assert any("not in (0, 1)" in m for m in res["oracle_mismatches"])


def test_12_reversed_edge_endpoints_and_complement_t():
    """Control 12: Reversing edge endpoints [U, V] -> [V, U] and transforming t -> 1 - t matches oracle."""
    case, exp, r, resp = _make_cat_a_triangle_fixture()
    # Edge ["B", "B'"] at t=3/4 is equivalent to ["B'", "B"] at t=1/4
    resp["route_d"]["sections"][0]["vertices"][1]["edge"] = ["B'", "B"]
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "SERVED_CORRECT", res.get("oracle_mismatches")


def test_13_category_a_dinh_cat_canh():
    """Control 13: Valid Category A DINH_CAT_CANH section."""
    case, exp, r, resp = _make_cat_a_triangle_fixture()
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "SERVED_CORRECT"
    assert res["certificate_category"] == ["DINH_CAT_CANH"]


def test_14_category_b_engine_derived_section():
    """Control 14: Valid Category B ENGINE_DERIVED_SECTION."""
    case, exp, r, resp = _make_cat_b_pentagon_fixture()
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "SERVED_CORRECT"
    assert res["certificate_category"] == ["ENGINE_DERIVED_SECTION"]


def test_15_category_mixing_tamper_rejected():
    """Control 15: Category A/B mixing tamper is rejected as WRONG_SERVED."""
    case, exp, r, resp = _make_cat_b_pentagon_fixture()
    r.planner["auxiliary"].append({"rule": "dinh-cat-canh", "goal": "sec"})
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "WRONG_SERVED"
    assert any("mixing" in m for m in res["oracle_mismatches"])


def test_16_wrong_solid_identity_rejected():
    """Control 16: Wrong solid identity is rejected as WRONG_SERVED."""
    case, exp, r, resp = _make_cat_a_triangle_fixture()
    resp["envelope"]["scene3d"]["objects"][0]["notation"] = "MNP.M′N′P′"
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "WRONG_SERVED"
    assert any("solid identity" in m for m in res["oracle_mismatches"])


def test_17_wrong_edge_topology_rejected():
    """Control 17: Cut on wrong edge is rejected as WRONG_SERVED."""
    case, exp, r, resp = _make_cat_b_pentagon_fixture()
    resp["route_d"]["sections"][0]["vertices"][0]["edge"] = ["A", "D"]
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "WRONG_SERVED"
    assert any("interior edge cuts" in m for m in res["oracle_mismatches"])


def test_18_wrong_area_squared_rejected():
    """Control 18: Wrong area squared in final_memory or certificate is rejected as WRONG_SERVED."""
    case, exp, r, resp = _make_cat_a_triangle_fixture()
    r.exec_result.final_memory["kq_mg1"] = {"he": "25/4", "can": 5}
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "WRONG_SERVED"
    assert any("area²" in m for m in res["oracle_mismatches"])


def test_19_missing_section_certificate_rejected():
    """Control 19: Missing section certificate on Category B or incomplete provenance on Category A is rejected."""
    case_b, exp_b, r_b, resp_b = _make_cat_b_pentagon_fixture()
    resp_b["route_d"]["sections"][0]["closure_certificate"] = None
    res_b = score_observed_response(case_b, exp_b, TAX, r_b, resp_b)
    assert res_b["outcome"] == "WRONG_SERVED"

    case_a, exp_a, r_a, resp_a = _make_cat_a_triangle_fixture()
    del resp_a["route_d"]["sections"][0]["vertices"][0]["provenance"]
    res_a = score_observed_response(case_a, exp_a, TAX, r_a, resp_a)
    assert res_a["outcome"] == "WRONG_SERVED"


def test_20_wrong_refusal_reason_rejected():
    """Control 20: Refusal reason agreement vs disagreement."""
    case = {
        "id": "CTRL-REFUSE",
        "stratum": "N",
        "family": "cuboid",
        "plane_relation": "parallel_plane",
        "question_type": "section_only",
        "negative_class": "missing_mandatory_premise",
        "negative_origin": "flawed_or_unsupported_problem",
        "expected_disposition": "REFUSE",
        "acceptable_categories": ["UNDERDETERMINED"],
        "payload": {"problem_text": "Cho hình hộp chữ nhật ABCD.A'B'C'D'...", "derived_sections": []},
    }
    r_ok = SimpleNamespace(status="REFUSED", code="MISSING_DIMENSION", reason="thiếu kích thước")
    resp_ok = {"route_d": {"status": "REFUSED", "refusal": {"code": "MISSING_DIMENSION"}}, "envelope": {"status": "unsupported"}}
    assert score_observed_response(case, None, TAX, r_ok, resp_ok)["outcome"] == "REFUSED_CORRECT_REASON"

    r_bad = SimpleNamespace(status="REFUSED", code="QUOTE_NOT_IN_SOURCE", reason="quote mismatch")
    resp_bad = {"route_d": {"status": "REFUSED", "refusal": {"code": "QUOTE_NOT_IN_SOURCE"}}, "envelope": {"status": "unsupported"}}
    assert score_observed_response(case, None, TAX, r_bad, resp_bad)["outcome"] == "REFUSED_REASON_DISAGREEMENT"


def test_21_uncaught_product_exception_handled():
    """Control 21: Uncaught exception inside product route/adapter is caught as PRODUCT_EXCEPTION and never crashes scorer."""
    case, exp, _, _ = _make_cat_a_triangle_fixture()

    def _boom_route(_payload):
        raise RuntimeError("simulated uncaught product crash")

    res = score_case(case, exp, TAX, route_fn=_boom_route, adapter_fn=lambda r, t: {})
    assert res["product_exception"] is True
    assert res["outcome"] == "FALSE_REFUSAL"
    assert res["category"] == "INTERNAL_OR_VALIDATION"


def test_22_missing_oracle_entry_rejected():
    """Control 22: Served case with missing oracle entry is rejected as WRONG_SERVED; malformed oracle triggers HARNESS_ERROR."""
    case, exp, r, resp = _make_cat_a_triangle_fixture()
    res_none = score_observed_response(case, None, TAX, r, resp)
    assert res_none["outcome"] == "WRONG_SERVED"
    assert "no oracle entry for a served case" in res_none["oracle_mismatches"]

    exp_bad = deepcopy(exp)
    exp_bad["boundary"] = "not-a-list"
    res_err = score_observed_response(case, exp_bad, TAX, r, resp)
    assert res_err["outcome"] == "HARNESS_ERROR"


def test_23_unfound_vertex_never_defaults_to_polygon_index_zero():
    """Mandatory Guard: If a vertex in section.vertices is missing from scene3d.objects / polygon, scorer MUST NOT default poly_idx to 0."""
    case, exp, r, resp = _make_cat_a_quad_fixture()
    # Remove A_prime from scene3d.objects so A' cannot be looked up by label
    resp["envelope"]["scene3d"]["objects"] = [
        o for o in resp["envelope"]["scene3d"]["objects"] if o.get("id") != "A_prime"
    ]
    res = score_observed_response(case, exp, TAX, r, resp)
    assert res["outcome"] == "WRONG_SERVED"
    assert any("could not be resolved to any polygon index" in m for m in res["oracle_mismatches"])


def test_24_systematic_mutation_kill_suite():
    """Mutation controls: 10 distinct mutations on valid fixtures must all be killed (0% survival)."""
    mutations_killed = 0
    total_mutations = 10

    # M1: Perturb 1 coordinate in polygon
    c, e, r, resp = _make_cat_a_triangle_fixture()
    resp["envelope"]["scene3d"]["objects"][-1]["polygon"][0][2] = "2/3"
    assert score_observed_response(c, e, TAX, r, resp)["outcome"] == "WRONG_SERVED"
    mutations_killed += 1

    # M2: Perturb t parameter on Category B vertex
    c, e, r, resp = _make_cat_b_pentagon_fixture()
    resp["route_d"]["sections"][0]["vertices"][2]["t"] = "1/3"
    assert score_observed_response(c, e, TAX, r, resp)["outcome"] == "WRONG_SERVED"
    mutations_killed += 1

    # M3: Flip edge endpoints without complementing t on Category B
    c, e, r, resp = _make_cat_b_pentagon_fixture()
    e["boundary"][0] = {"edge": ["A", "B"], "t": "1/3"}
    resp["route_d"]["sections"][0]["vertices"][0]["edge"] = ["B", "A"]
    resp["route_d"]["sections"][0]["vertices"][0]["t"] = "1/3"  # should be 2/3 if flipped
    assert score_observed_response(c, e, TAX, r, resp)["outcome"] == "WRONG_SERVED"
    mutations_killed += 1

    # M4: Swap two non-adjacent vertices in 5-gon
    c, e, r, resp = _make_cat_b_pentagon_fixture()
    v = resp["route_d"]["sections"][0]["vertices"]
    v[1]["ordinal"], v[3]["ordinal"] = 3, 1
    assert score_observed_response(c, e, TAX, r, resp)["outcome"] == "WRONG_SERVED"
    mutations_killed += 1

    # M5: Perturb area_squared in Category B closure_certificate
    c, e, r, resp = _make_cat_b_pentagon_fixture()
    resp["route_d"]["sections"][0]["closure_certificate"]["area_squared"] = "28/16"
    assert score_observed_response(c, e, TAX, r, resp)["outcome"] == "WRONG_SERVED"
    mutations_killed += 1

    # M6: Unclosed section polygon (`closed=False`)
    c, e, r, resp = _make_cat_a_triangle_fixture()
    resp["envelope"]["scene3d"]["objects"][-1]["closed"] = False
    assert score_observed_response(c, e, TAX, r, resp)["outcome"] == "WRONG_SERVED"
    mutations_killed += 1

    # M7: Inject `_prime` into envelope.answer
    c, e, r, resp = _make_cat_a_triangle_fixture()
    resp["envelope"]["answer"] = "S_A_primeMN = 25√6/4"
    assert score_observed_response(c, e, TAX, r, resp)["outcome"] == "WRONG_SERVED"
    mutations_killed += 1

    # M8: Inject auxiliary label `H` into section name
    c, e, r, resp = _make_cat_b_pentagon_fixture()
    resp["envelope"]["scene3d"]["objects"][-1]["name"] = "Thiết diện HMN"
    assert score_observed_response(c, e, TAX, r, resp)["outcome"] == "WRONG_SERVED"
    mutations_killed += 1

    # M9: Serve a REFUSE case
    c, e, r, resp = _make_cat_a_triangle_fixture()
    c["expected_disposition"] = "REFUSE"
    assert score_observed_response(c, e, TAX, r, resp)["outcome"] == "WRONG_SERVED"
    mutations_killed += 1

    # M10: Refuse a SERVE case
    c, e, _, _ = _make_cat_a_triangle_fixture()
    r_ref = SimpleNamespace(status="REFUSED", code="QUOTE_NOT_IN_SOURCE", reason="test")
    resp_ref = {"route_d": {"status": "REFUSED", "refusal": {"code": "QUOTE_NOT_IN_SOURCE"}}, "envelope": {"status": "unsupported"}}
    assert score_observed_response(c, e, TAX, r_ref, resp_ref)["outcome"] == "FALSE_REFUSAL"
    mutations_killed += 1

    assert mutations_killed == total_mutations


if __name__ == "__main__":
    # Run all test functions and emit qualification receipt
    test_fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    results = []
    for fn in test_fns:
        fn()
        results.append({"test": fn.__name__, "doc": (fn.__doc__ or "").strip(), "status": "PASS"})
    scorer_bytes = (THIS_DIR / "evaluate_holdout_wave3.py").read_bytes().replace(b"\r\n", b"\n")
    test_bytes = Path(__file__).read_bytes().replace(b"\r\n", b"\n")
    receipt = {
        "schema": "HOLDOUT_WAVE3_SCORER_QUALIFICATION_RECEIPT/1",
        "qualified_before_corpus_creation": True,
        "scorer_sha256_lf": hashlib.sha256(scorer_bytes).hexdigest(),
        "qualification_tests_sha256_lf": hashlib.sha256(test_bytes).hexdigest(),
        "total_test_suites": len(results),
        "all_passed": True,
        "mandatory_22_controls_verified": True,
        "non_zero_fallback_guard_verified": True,
        "mutation_controls_verified": {"killed": 10, "total": 10, "kill_rate": 1.0},
        "tests": results,
    }
    out_path = RUN / "verification/scorer-qualification-receipt.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "SCORER_QUALIFIED", "tests_passed": len(results)}, indent=2))
