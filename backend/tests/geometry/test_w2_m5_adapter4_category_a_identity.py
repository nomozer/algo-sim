# -*- coding: utf-8 -*-
"""Unit and adversarial tamper tests for W2-M5 Adapter /4 Category A Identity Repair."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import pytest

from app.ai.adapter4_route import (
    _phong_bi,
    _validate_sections,
    build_adapter4_response,
    run_typed_fact_next_v2_route,
)
from app.ai.hybrid_preview import PreviewInvalid
from app.simulation.geometry.exact import Vec3
from app.simulation.geometry_functions.engine import _binh_phuong
from app.simulation.geometry_functions.planner import DINH_CAT_CANH

REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = REPO_ROOT / "docs/evaluation/geometry/runs/hybrid-v2-w2-m5-adapter4-category-a-identity-repair"


@pytest.fixture(scope="module")
def dev_bundle() -> tuple[list[dict], dict[str, dict]]:
    with open(RUN_DIR / "inputs/development.json", "r", encoding="utf-8") as f:
        dev = json.load(f)
    with open(RUN_DIR / "inputs/oracle.json", "r", encoding="utf-8") as f:
        ora = json.load(f)["oracles"]
    return dev["positive_cases"], ora


@pytest.fixture(scope="module")
def route_cache(dev_bundle) -> dict[str, object]:
    positives, _ = dev_bundle
    out = {}
    for c in positives:
        out[c["id"]] = run_typed_fact_next_v2_route(deepcopy(c["payload"]))
    return out


def test_w2_a07_and_w2_a10_served_with_exact_oracle_and_learner_notation(dev_bundle, route_cache):
    positives, oracles = dev_bundle
    by_id = {c["id"]: c for c in positives}

    for cid in ("W2-A07", "W2-A10"):
        case = by_id[cid]
        exp = oracles[cid]
        r = deepcopy(route_cache[cid])
        assert r.status == "SERVED"

        resp = build_adapter4_response(r, case["problem_text"])
        assert resp["route_d"]["status"] == "SERVED"
        assert resp["envelope"]["status"] == "ok"

        sections = resp["route_d"]["sections"]
        assert len(sections) == 1
        sec = sections[0]
        assert "certificate_version" not in sec
        assert sec.get("certificate_category") is None

        # Verify learner-facing primed vertex label "A'" is preserved and no "_prime" leaks
        labels = [v["label"] for v in sec["vertices"]]
        assert "A'" in labels
        assert all("_prime" not in lbl for lbl in labels)
        for v in sec["vertices"]:
            assert all("_prime" not in ep for ep in v["edge"])

        # Verify scene3d point object keeps id="A_prime" and notation="A′"
        objs = {o["id"]: o for o in resp["envelope"]["scene3d"]["objects"]}
        assert "A_prime" in objs
        assert objs["A_prime"]["notation"] == "A′"

        if exp.get("area_goal_id"):
            ans = r.exec_result.final_memory[f"kq_{exp['area_goal_id']}"]
            assert _binh_phuong(ans) == Fraction(exp["area_squared"])


def test_all_14_positive_primed_category_a_cases_served(dev_bundle, route_cache):
    positives, oracles = dev_bundle
    assert len(positives) == 14

    for case in positives:
        cid = case["id"]
        exp = oracles[cid]
        r = deepcopy(route_cache[cid])
        assert r.status == "SERVED", f"{cid}: engine status={r.status}"

        resp = build_adapter4_response(r, case["problem_text"])
        assert resp["route_d"]["status"] == "SERVED", f"{cid}: adapter refused with {resp['route_d'].get('refusal')}"
        sec = resp["route_d"]["sections"][0]
        assert len(sec["vertices"]) == exp["vertex_count"]
        if sec["boundary"] is not None:
            assert any("'" in b for b in sec["boundary"])
            assert all("_prime" not in b for b in sec["boundary"])
        if exp.get("area_goal_id"):
            ans = r.exec_result.final_memory[f"kq_{exp['area_goal_id']}"]
            assert _binh_phuong(ans) == Fraction(exp["area_squared"])


@pytest.mark.parametrize(
    "tamper_kind",
    [
        "NONEXISTENT_PRIMED_POINT",
        "WRONG_SOLID_IDENTITY",
        "VERTEX_FROM_ANOTHER_SOLID",
        "CUT_VERTEX_OFF_EDGE",
        "INTERPOLATION_T_OUTSIDE_0_1",
        "SAME_LABEL_MISMATCHED_COORDINATES",
        "MISSING_VERTEX_IN_CYCLE",
        "DUPLICATE_VERTEX",
        "WRONG_SECTION_TOPOLOGY_ORDER",
        "CATEGORY_A_B_CERTIFICATE_MIXING",
        "FORGED_PROVENANCE_STATED",
        "AREA_SQUARED_MISMATCH",
        "MACHINE_ID_LEAK_IN_VERTEX_LABEL",
        "MACHINE_ID_LEAK_IN_EDGE_LABEL",
        "MACHINE_ID_LEAK_IN_BOUNDARY",
    ],
)
def test_category_a_tamper_modes_fail_closed(dev_bundle, route_cache, tamper_kind: str):
    positives, _ = dev_bundle
    by_id = {c["id"]: c for c in positives}

    if tamper_kind in ("MISSING_VERTEX_IN_CYCLE", "WRONG_SECTION_TOPOLOGY_ORDER"):
        base_id = "W2-A10"
    elif tamper_kind == "MACHINE_ID_LEAK_IN_BOUNDARY":
        base_id = "DEV-POS-08"
    else:
        base_id = "W2-A07"

    rt = deepcopy(route_cache[base_id])
    problem_text = by_id[base_id]["problem_text"]
    scene = rt.scene3d
    objs = {o["id"]: o for o in scene["objects"]}
    d_aux = next(d for d in rt.planner["auxiliary"] if d.get("rule") == DINH_CAT_CANH)
    sid = d_aux["goal"]
    td_obj = objs[f"td_{sid}"]

    if tamper_kind == "NONEXISTENT_PRIMED_POINT":
        d_aux["vertices"][0]["label"] = "Z'"
        rt.route_d = _phong_bi(rt)
    elif tamper_kind == "WRONG_SOLID_IDENTITY":
        solid_obj = next(o for o in scene["objects"] if o.get("type") == "solid")
        solid_obj["notation"] = "S.XYZ"
    elif tamper_kind == "VERTEX_FROM_ANOTHER_SOLID":
        scene["objects"].append(
            {"id": "X_prime", "type": "point3", "notation": "X′", "origin": "source", "xyz": ["5", "0", "10"]}
        )
        rt.exec_result.final_memory["X_prime"] = Vec3(Fraction(5), Fraction(0), Fraction(10))
        d_aux["vertices"][1]["edge"] = ["B", "X'"]
        rt.route_d = _phong_bi(rt)
    elif tamper_kind == "CUT_VERTEX_OFF_EDGE":
        objs["M"]["xyz"] = ["4", "1", "15/2"]
        rt.exec_result.final_memory["M"] = Vec3(Fraction(4), Fraction(1), Fraction(15, 2))
        td_obj["polygon"][1] = ["4", "1", "15/2"]
    elif tamper_kind == "INTERPOLATION_T_OUTSIDE_0_1":
        objs["M"]["xyz"] = ["5", "0", "25/2"]
        rt.exec_result.final_memory["M"] = Vec3(Fraction(5), Fraction(0), Fraction(25, 2))
        td_obj["polygon"][1] = ["5", "0", "25/2"]
    elif tamper_kind == "SAME_LABEL_MISMATCHED_COORDINATES":
        objs["A_prime"]["xyz"] = ["0", "0", "9"]
        rt.exec_result.final_memory["A_prime"] = Vec3(Fraction(0), Fraction(0), Fraction(9))
    elif tamper_kind == "MISSING_VERTEX_IN_CYCLE":
        d_aux["vertices"] = d_aux["vertices"][:3]
        rt.route_d = _phong_bi(rt)
    elif tamper_kind == "DUPLICATE_VERTEX":
        d_aux["vertices"][1]["label"] = "A′"
        rt.route_d = _phong_bi(rt)
    elif tamper_kind == "WRONG_SECTION_TOPOLOGY_ORDER":
        p = td_obj["polygon"]
        vs = td_obj["vertex_sources"]
        td_obj["polygon"] = [p[0], p[3], p[1], p[2]]
        td_obj["vertex_sources"] = [vs[0], vs[3], vs[1], vs[2]]
    elif tamper_kind == "CATEGORY_A_B_CERTIFICATE_MIXING":
        rt.route_d = _phong_bi(rt)
        rt.route_d["sections"][0]["certificate_category"] = "ENGINE_DERIVED_SECTION"
        rt.route_d["sections"][0]["certificate_version"] = "plane-section-certificate/1"
    elif tamper_kind == "FORGED_PROVENANCE_STATED":
        d_aux["vertices"][0]["stated"] = True
        rt.route_d = _phong_bi(rt)
    elif tamper_kind == "AREA_SQUARED_MISMATCH":
        rt.exec_result.final_memory["kq_mg1"] = Fraction(999)
        objs["kq_mg1"]["value"] = "999"
        rt.answers["mg1"] = "999"
        rt.answer_exact["mg1"]["coef"] = "999"
        rt.route_d = _phong_bi(rt)
    elif tamper_kind == "MACHINE_ID_LEAK_IN_VERTEX_LABEL":
        d_aux["vertices"][0]["label"] = "A_prime"
        rt.route_d = _phong_bi(rt)
    elif tamper_kind == "MACHINE_ID_LEAK_IN_EDGE_LABEL":
        d_aux["vertices"][0]["edge"] = ["A", "A_prime"]
        rt.route_d = _phong_bi(rt)
    elif tamper_kind == "MACHINE_ID_LEAK_IN_BOUNDARY":
        d_aux["closure"]["boundary"] = ["A_prime", "M", "N"]
        rt.route_d = _phong_bi(rt)

    with pytest.raises(PreviewInvalid):
        _validate_sections(rt.route_d["sections"], {o["id"]: o for o in rt.scene3d["objects"]}, rt)

    resp = build_adapter4_response(rt, problem_text)
    assert resp["route_d"]["status"] == "REFUSED"
    assert resp["route_d"]["refusal"]["code"] == "PREVIEW_RESULT_INVALID"
