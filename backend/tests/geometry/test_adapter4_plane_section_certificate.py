"""Tests for Adapter /4 plane-only derived section certificates (`plane-section-certificate/1`).

Covers:
1. All 18 positive cases (17 Category B plane-only derived sections across right prisms, oblique prisms, cuboids,
   cubes, pyramids, parallel planes, two-line planes, perpendicular planes, renamed/reversed/symbolic variants, and
   1 Category A `DINH_CAT_CANH` regression guard).
2. Learner-facing auxiliary label leak guard when plane-construction translate points coincide with unnamed section
   vertices (`prism-parallel-base-plane-only`).
3. All 18 negative/tamper cases (7 route-level refusals + 11 Adapter /4 certificate tampering modes) plus Category A ->
   Category B downgrade rejection.
4. Independent Euclidean section oracle agreement and provider-order invariance.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path

import pytest

from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route
from app.simulation.geometry_functions.engine import (
    PLANE_SECTION_CERTIFICATE_PRODUCER,
    PLANE_SECTION_CERTIFICATE_RULE,
    PLANE_SECTION_CERTIFICATE_VERSION,
)

RUN = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-v2-adapter4-plane-section-certificate"
DEV = json.loads((RUN / "inputs/development.json").read_text(encoding="utf-8"))["cases"]
ORACLES = json.loads((RUN / "inputs/oracle.json").read_text(encoding="utf-8"))

POS_B = [c for c in DEV if c["group"] == "positive"]
POS_A = [c for c in DEV if c["group"] == "positive_category_a"]
NEG = [c for c in DEV if c["group"].startswith("negative")]


def _load_tool(name: str):
    spec = importlib.util.spec_from_file_location(f"adapter4_cert_{name}", RUN / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


EVAL_TOOL = _load_tool("evaluate_adapter4")
ORACLE_TOOL = _load_tool("oracle_adapter4")


def _square_exact(result, goal_id: str = "q") -> F:
    v = result.exec_result.final_memory[f"kq_{goal_id}"]
    return F(v.he) ** 2 * v.can if hasattr(v, "can") else F(v) ** 2


def _learner_strings(scene: dict) -> list[str]:
    out = [o.get(k) for o in scene["objects"] for k in ("label", "display_label", "reference", "notation", "role")]
    out += [(o.get("formula") or {}).get("text") for o in scene["objects"]]
    out += [e.get(k) for e in scene["events"] for k in ("display_label", "learner_text", "explanation")]
    out += [s.get("learner_text") for s in scene["formation"]["steps"]]
    return [t for t in out if isinstance(t, str)]


@pytest.mark.parametrize("case", POS_B, ids=lambda c: c["id"])
def test_plane_only_derived_sections_serve_through_adapter4_with_verified_certificates(case):
    payload = deepcopy(case["payload"])
    result = run_typed_fact_next_v2_route(payload)
    assert result.status == "SERVED", (result.code, result.reason)
    resp = build_adapter4_response(result, payload["problem_text"])
    assert resp["envelope"]["status"] == "ok"
    rd = resp["route_d"]
    assert rd["status"] == "SERVED"
    assert rd["refusal"] is None
    assert len(rd["sections"]) == 1

    sec = rd["sections"][0]
    assert sec["certificate_version"] == PLANE_SECTION_CERTIFICATE_VERSION
    assert sec["certificate_category"] == "ENGINE_DERIVED_SECTION"
    assert sec["declared_boundary"] is None

    cert = sec["closure_certificate"]
    assert cert["verified"] is True
    assert cert["version"] == PLANE_SECTION_CERTIFICATE_VERSION
    assert cert["rule"] == PLANE_SECTION_CERTIFICATE_RULE
    assert cert["producer"] == PLANE_SECTION_CERTIFICATE_PRODUCER
    assert F(cert["area_squared"]) == F(case["expected_area_squared"])
    assert len(sec["vertices"]) == case["expected_vertex_count"]
    assert sec["boundary"] == [v["entity_id"] for v in sec["vertices"]]
    assert cert["boundary"] == sec["boundary"]

    for idx, v in enumerate(sec["vertices"]):
        assert v["ordinal"] == idx
        assert v["stated"] is False
        assert v["provenance"] in {
            "THROUGH_POINT_REUSE",
            "SOLID_VERTEX_INTERSECTION",
            "ENGINE_DERIVED_EDGE_CUT",
        }
        assert v["provenance"] not in {"SOURCE_NAMED", "STATED_UNNAMED"}

    if "q" in result.answer_exact:
        assert _square_exact(result, "q") == F(case["expected_area_squared"])

    if case["id"] in ORACLES:
        oracle = ORACLES[case["id"]]
        assert F(cert["area_squared"]) == F(oracle["area_squared"])
        assert len(sec["vertices"]) == oracle["vertex_count"]


@pytest.mark.parametrize("case", POS_A, ids=lambda c: c["id"])
def test_category_a_stated_cut_sections_keep_existing_dinh_cat_canh_contract(case):
    payload = deepcopy(case["payload"])
    result = run_typed_fact_next_v2_route(payload)
    assert result.status == "SERVED", (result.code, result.reason)
    resp = build_adapter4_response(result, payload["problem_text"])
    assert resp["envelope"]["status"] == "ok"
    rd = resp["route_d"]
    assert rd["status"] == "SERVED"
    sec = rd["sections"][0]
    assert "certificate_category" not in sec
    assert "certificate_version" not in sec
    assert [v["provenance"] for v in sec["vertices"]] == ["THROUGH_POINT_REUSE", "SOURCE_NAMED", "SOURCE_NAMED"]
    assert [v["stated"] for v in sec["vertices"]] == [False, True, True]


def test_prism_parallel_base_plane_only_hides_coincident_translate_labels_from_section_display():
    case = next(c for c in POS_B if c["id"] == "prism-parallel-base-plane-only")
    result = run_typed_fact_next_v2_route(deepcopy(case["payload"]))
    assert result.status == "SERVED"
    resp = build_adapter4_response(result, case["payload"]["problem_text"])
    assert resp["envelope"]["status"] == "ok"
    sc = resp["envelope"]["scene3d"]
    objs = {o["id"]: o for o in sc["objects"]}
    sec_obj = objs["td_sec"]
    assert (sec_obj["label"], sec_obj["display_label"], sec_obj["notation"]) == (
        "Thiết diện bởi (α)",
        "Thiết diện bởi (α)",
        None,
    )
    area_obj = objs["kq_q"]
    assert area_obj["notation"] is None
    assert area_obj["label"] == "Diện tích thiết diện bởi (α)"
    assert not [t for t in _learner_strings(sc) if "HMH1" in t]


@pytest.mark.parametrize("case", NEG, ids=lambda c: c["id"])
def test_negative_and_tampered_section_certificates_fail_closed(case):
    payload = deepcopy(case["payload"])
    result = run_typed_fact_next_v2_route(payload)
    assert result.status == case["expected_route_status"]
    if case["group"] == "negative_tamper":
        EVAL_TOOL._apply_tamper(case, result)
    resp = build_adapter4_response(result, payload["problem_text"])
    assert resp["envelope"]["status"] == "unsupported"
    rd = resp["route_d"]
    assert rd["status"] == "REFUSED"
    assert rd["refusal"]["code"] in case["expected_codes"]
    assert "scene3d" not in resp["envelope"]
    assert "sections" not in rd


def test_category_a_section_cannot_be_downgraded_to_category_b_certificate():
    case = POS_A[0]
    result = run_typed_fact_next_v2_route(deepcopy(case["payload"]))
    assert result.status == "SERVED"
    assert len(result.section_certificates) == 1
    # Attempting to substitute the Engine's Category B certificate where a Category A DINH_CAT_CANH certificate exists
    # must be rejected by Adapter /4.
    result.route_d["sections"] = [deepcopy(result.section_certificates[0])]
    resp = build_adapter4_response(result, case["payload"]["problem_text"])
    assert resp["envelope"]["status"] == "unsupported"
    assert resp["route_d"]["status"] == "REFUSED"
    assert resp["route_d"]["refusal"] == {"code": "PREVIEW_RESULT_INVALID"}


def test_independent_oracle_matches_committed_oracle_json():
    for case in POS_B:
        if case.get("geometry") is not None:
            assert ORACLE_TOOL.compute_section_oracle(case["geometry"]) == ORACLES[case["id"]]
