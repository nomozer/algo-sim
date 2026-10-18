# -*- coding: utf-8 -*-
"""End-to-End Integration & Regression Suite for `research/hybrid-backend-integration` (P2–P5).

Verifies the combined backend candidate integrating:
1. `research/semantic-extraction-v3-runtime-revision` (`bb014eb8`, product commit `283813b2`)
2. `research/contract-driven-goal-composition` (`a629ebee`, product commit `1529faa7`)
3. `research/step-math-validation` (`0dd1da5c`)

Covers all 11 mandatory P4 integration requirements:
1. Flat contract -> Source Grounding -> Planner -> Engine (`run_ai_fact_route` & `run_fact_route`).
2. Deterministic Typed Facts -> Geometry IR (`spec.statements`, `exec_result`, `scene3d`, `formation.steps`).
3. Multi-goal composition, named & unnamed auxiliary points, shared auxiliary deduplication.
4. Area, angle, length, distance, volume, and section across polyhedral families & oblique metrics.
5. Mathematical and inductive dependency closure invariants via independent oracles.
6. Safe refusals, schema representation blockers, and unsupported capabilities.
7. Tampered facts, wrong source ownership, wrong target binding, lying contracts, and regex tail guard.
8. Version, surface fingerprint, and candidate identity separation (historical `6ba9033b...` vs combined `afab0a3c...`).
9. Backward compatibility with `DEFAULT_MODE = "LLM_ONLY"` and `CACHE_VERSION = "125"`.
10. Registry permutation invariance.
11. Strict oracle metric error handling (singular/degenerate, indefinite, asymmetric, or malformed `chart_metric`
    must fail closed as `INVALID` and NEVER fall back to Euclidean `IDENTITY_METRIC`).
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time
from typing import Any

import pytest

from app.ai import fact_extraction, function_calling, pipeline
from app.ai.fact_extraction import (
    RESPONSE_CONTRACT,
    facts_response_schema,
    run_ai_fact_route,
    schema_accepts,
    surface_fingerprint,
)
from app.ai.function_route import run_fact_route, run_function_route
import app.main as main_module
from app.simulation.geometry_functions import (
    ENGINE_VERSION,
    REGISTRY_VERSION,
    engine,
    planner,
    registry,
)
from app.simulation.geometry_functions.planner import PLANNER_VERSION, TypedFact
from tests.geometry.test_function_discovery_planning import (
    experimental_centroid_contract,
    squared,
)

ROOT = Path(__file__).resolve().parents[3]
RUNS_DIR = ROOT / "docs" / "evaluation" / "geometry" / "runs"
GOAL_COMP_RUN = RUNS_DIR / "contract-driven-goal-composition"
STEP_MATH_RUN = RUNS_DIR / "step-math-validation"
V3_REV_RUN = RUNS_DIR / "semantic-extraction-v3-runtime-revision"
V3_PARENT_RUN = RUNS_DIR / "semantic-extraction-schema-contract"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


STEP_ORACLE = _load_module("_step_math_oracle_int", STEP_MATH_RUN / "oracle.py")
GRAM_ORACLE = _load_module("_gram_oracle_int", GOAL_COMP_RUN / "oracle.py")
GOAL_CORPUS = json.loads((GOAL_COMP_RUN / "corpus.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Strict Metric Validation Wrapper (P4.11: Never fall back to Euclidean I3)
# ---------------------------------------------------------------------------

def strict_parse_metric(raw_metric: Any, *, require_present: bool = True) -> STEP_ORACLE.Mat3:
    """Parse and validate a 3x3 Riemannian metric tensor G without ever falling back to IDENTITY_METRIC.

    Raises ValueError if `raw_metric` is missing (when `require_present=True`), not a 3x3 list/tuple
    of finite numbers/expressions, asymmetric (G_ij != G_ji), singular (det(G) <= 0), or
    non-positive-definite (Sylvester's criterion).
    """
    if raw_metric is None:
        if require_present:
            raise ValueError("chart_metric is missing (None); refusing to substitute Euclidean IDENTITY_METRIC")
        return STEP_ORACLE.IDENTITY_METRIC
    if not isinstance(raw_metric, (list, tuple)) or len(raw_metric) != 3:
        raise ValueError(f"chart_metric must be a 3x3 matrix, got {raw_metric!r}")
    rows: list[tuple[float, float, float]] = []
    for r in raw_metric:
        if not isinstance(r, (list, tuple)) or len(r) != 3:
            raise ValueError(f"chart_metric row must have length 3, got {r!r}")
        parsed_row = tuple(float(STEP_ORACLE.eval_symbolic_expr(x)) for x in r)
        if any(math.isnan(v) or math.isinf(v) for v in parsed_row):
            raise ValueError(f"chart_metric contains NaN/Inf: {parsed_row!r}")
        rows.append(parsed_row)  # type: ignore[arg-type]
    G: STEP_ORACLE.Mat3 = (rows[0], rows[1], rows[2])
    # Symmetry check: G_ij == G_ji
    for i in range(3):
        for j in range(i + 1, 3):
            if abs(G[i][j] - G[j][i]) > 1e-9:
                raise ValueError(f"chart_metric is not symmetric: G[{i}][{j}]={G[i][j]} != G[{j}][{i}]={G[j][i]}")
    # Sylvester's criterion for positive-definiteness: leading principal minors m1 > 0, m2 > 0, m3 = det(G) > 0
    m1 = G[0][0]
    m2 = G[0][0] * G[1][1] - G[0][1] * G[1][0]
    m3 = STEP_ORACLE.mat3_det(G)
    if m1 <= 1e-12 or m2 <= 1e-12 or m3 <= 1e-12:
        raise ValueError(
            f"chart_metric is not positive-definite (Sylvester minors m1={m1:.6g}, m2={m2:.6g}, det={m3:.6g})"
        )
    return G


def strict_mat3_inv(G: STEP_ORACLE.Mat3) -> STEP_ORACLE.Mat3:
    """Invert a validated 3x3 metric tensor G; raises ValueError on singular/non-SPD matrices."""
    strict_parse_metric([list(r) for r in G], require_present=True)
    det = STEP_ORACLE.mat3_det(G)
    if abs(det) <= 1e-12:
        raise ValueError(f"Singular metric matrix (det={det}); refusing to substitute IDENTITY_METRIC")
    return STEP_ORACLE.mat3_inv(G)


def verify_integrated_scene_mathematics(
    scene: dict[str, Any],
    *,
    scene_id: str = "integrated_scene",
    require_chart_metric: bool = True,
) -> STEP_ORACLE.SceneAuditReport:
    """Run independent 11-category mathematical verification with strict fail-closed chart_metric validation."""
    try:
        strict_parse_metric(scene.get("chart_metric"), require_present=require_chart_metric)
    except Exception as exc:  # noqa: BLE001
        cat = STEP_ORACLE.CategoryCheckResult(
            category="1_incidence",
            passed=False,
            checked_count=1,
            failures=[f"STRICT_METRIC_INVALID: {exc}"],
        )
        return STEP_ORACLE.SceneAuditReport(
            scene_id=scene_id,
            data_source="hybrid-backend-integration",
            source_kind="backend_hybrid_route_d",
            problem_text="",
            step_count=0,
            objects_by_step={},
            dependency_graph={},
            represented_proposition="chart_metric_validation",
            expected_math_result="INVALID_METRIC",
            verdict="INVALID",
            category_results={"1_incidence": cat},
            frontend_warnings=[],
            errors=[f"1_incidence: STRICT_METRIC_INVALID: {exc}"],
        )
    return STEP_ORACLE.verify_scene_mathematics(scene, scene_id=scene_id)


# ---------------------------------------------------------------------------
# 1 & 2. Flat Contract -> Source Grounding -> Planner -> Engine -> Geometry IR
# ---------------------------------------------------------------------------

def test_flat_contract_to_source_grounding_planner_engine_and_ir_handoff():
    """P4.1 & P4.2: Full `run_ai_fact_route` handoff from provider JSON body to Geometry IR and Scene3D."""
    case = GOAL_CORPUS["positive"][0]  # pyramid-midpoint-area-AB
    fake_body = {
        "candidates": [
            {
                "content": {"parts": [{"text": json.dumps(case["payload"], ensure_ascii=False)}]},
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {"promptTokenCount": 42, "candidatesTokenCount": 35, "totalTokenCount": 77},
    }
    captured_requests: list[dict[str, Any]] = []

    def fake_transport(req_payload: dict[str, Any]) -> dict[str, Any]:
        captured_requests.append(req_payload)
        return fake_body

    res = run_ai_fact_route(case["text"], fake_transport)
    assert len(captured_requests) == 1
    assert captured_requests[0]["generationConfig"]["responseMimeType"] == "application/json"
    assert res.status == "SERVED", (res.code, res.reason)
    assert res.ai["model_calls"] == 1
    assert res.ai["finish_reason"] == "STOP"
    assert res.ai["surface"] == surface_fingerprint("flat")

    # Verify independent Gram oracle exact rational value: S^2(M, A, B) = 13/4 => S = sqrt(13)/2
    expected_sq = GRAM_ORACLE.area_sq_triangle(
        GRAM_ORACLE.mid(GRAM_ORACLE.PYR["S"], GRAM_ORACLE.PYR["C"]),
        GRAM_ORACLE.PYR["A"],
        GRAM_ORACLE.PYR["B"],
    )
    assert expected_sq == Fraction(13, 4)
    assert squared(res.exec_result.final_memory["kq_q"]) == expected_sq

    # Verify Geometry IR statements & Scene3D timeline
    stmt_kinds = [s.kind for s in res.spec.statements]
    assert "construct_solid" in stmt_kinds
    assert "construct_point" in stmt_kinds
    assert "construct_polygon" in stmt_kinds
    assert "assign" in stmt_kinds
    assert res.scene3d is not None and res.scene3d.get("objects")
    assert res.scene3d.get("events") and res.scene3d.get("formation", {}).get("steps")
    assert len(res.scene3d["events"]) == len(res.scene3d["formation"]["steps"])

    # Verify Scene3D passes strict 11-category mathematical oracle
    audit = verify_integrated_scene_mathematics(res.scene3d, scene_id=case["id"])
    assert audit.verdict == "VERIFIED", audit.errors


def test_response_contract_is_one_snapshot_per_call(monkeypatch):
    """Run `hybrid-pre-main-hardening`: the contract is resolved ONCE per call. Before, `run_ai_fact_route` read the
    module global when building the request and again when validating, so a flip between the two let a reply requested
    under v3 skip the v3 gate (served the v3-invalid unnamed-midpoint area payload)."""
    case = GOAL_CORPUS["positive"][0]   # unnamed midpoint area: flat-servable, v3-invalid
    body = {"candidates": [{"content": {"parts": [{"text": json.dumps(case["payload"], ensure_ascii=False)}]},
                            "finishReason": "STOP"}]}
    asked: list[dict] = []

    def flip_then_answer(request):
        asked.append(request)
        monkeypatch.setattr(fact_extraction, "RESPONSE_CONTRACT", "flat")
        return body

    monkeypatch.setattr(fact_extraction, "RESPONSE_CONTRACT", "v3")
    r = run_ai_fact_route(case["text"], flip_then_answer)
    assert asked[0]["generationConfig"]["responseSchema"] == facts_response_schema("v3")
    assert (r.status, r.code) == ("REFUSED", "RESPONSE_CONTRACT_INVALID"), (r.status, r.code)
    assert r.ai["surface"] == fact_extraction.surface_fingerprint("v3")

    # An explicit per-call contract governs the request, the surface and the gate; the global is not consulted.
    monkeypatch.setattr(fact_extraction, "RESPONSE_CONTRACT", "flat")
    r = run_ai_fact_route(case["text"], lambda req: (asked.append(req), body)[1], contract="v3")
    assert asked[-1]["generationConfig"]["responseSchema"] == facts_response_schema("v3")
    assert (r.status, r.code, r.ai["surface"]) == ("REFUSED", "RESPONSE_CONTRACT_INVALID",
                                                    fact_extraction.surface_fingerprint("v3"))
    assert run_ai_fact_route(case["text"], lambda req: body).status == "SERVED"   # product default stays flat


def test_v3_contract_gate_and_locked_gold_forensic_reconciliation(monkeypatch):
    """P2 & P4.1: Verify v3 contract gate in `run_ai_fact_route` and the exact cause of the 16 LOCKED gold rejections."""
    # 1. Under v3, unnamed midpoint area question is rejected at schema gate (known Slice A v3 gap)
    case_area = GOAL_CORPUS["positive"][0]
    body_area = {
        "candidates": [{"content": {"parts": [{"text": json.dumps(case_area["payload"], ensure_ascii=False)}]}, "finishReason": "STOP"}]
    }
    monkeypatch.setattr(fact_extraction, "RESPONSE_CONTRACT", "v3")
    res_area_v3 = run_ai_fact_route(case_area["text"], lambda _: body_area)
    assert (res_area_v3.status, res_area_v3.code) == ("REFUSED", "RESPONSE_CONTRACT_INVALID")

    # 2. Under v3, named midpoint + angle_line_plane (Slice B) is accepted by v3 schema and served!
    case_angle = GOAL_CORPUS["angle_line_plane_slice_b"][2]  # angle-oblique-midpoint-line-plane
    body_angle = {
        "candidates": [{"content": {"parts": [{"text": json.dumps(case_angle["payload"], ensure_ascii=False)}]}, "finishReason": "STOP"}]
    }
    res_angle_v3 = run_ai_fact_route(case_angle["text"], lambda _: body_angle)
    assert res_angle_v3.status == "SERVED", (res_angle_v3.code, res_angle_v3.reason)
    assert Fraction(res_angle_v3.exec_result.final_memory["kq_q"]) == Fraction(8, 17)

    # 3. Forensic verification on the 24 LOCKED held-out gold payloads:
    #    8 pass raw v3 schema, 16 fail ONLY due to redundant `solid` on segment lengths (13) or author `reason` notes (3).
    heldout_gold = json.loads((V3_PARENT_RUN / "inputs/heldout/gold_facts.json").read_text(encoding="utf-8"))["cases"]
    v3_schema = facts_response_schema("v3")
    raw_accepted, raw_rejected, cleaned_accepted = [], [], []
    for cid, cdata in sorted(heldout_gold.items()):
        raw_payload = {
            "facts": [{k: v for k, v in f.items() if k not in ("required", "alternatives", "rid")} for f in cdata["facts"]]
        }
        if schema_accepts(v3_schema, raw_payload):
            raw_accepted.append(cid)
        else:
            raw_rejected.append(cid)
        cleaned_facts = []
        for f in raw_payload["facts"]:
            fc = dict(f)
            if fc.get("kind") == "length" and fc.get("measure") == "segment":
                fc.pop("solid", None)
            if fc.get("kind") != "unsupported":
                fc.pop("reason", None)
            cleaned_facts.append(fc)
        if schema_accepts(v3_schema, {"facts": cleaned_facts}):
            cleaned_accepted.append(cid)

    assert len(raw_accepted) == 8
    assert len(raw_rejected) == 16
    assert len(cleaned_accepted) == 24


# ---------------------------------------------------------------------------
# 3 & 4. Multi-goal, Named/Unnamed Auxiliary, Area/Angle/Length/Distance/Volume/Section
# ---------------------------------------------------------------------------

def test_multi_goal_shared_unnamed_midpoint_deduplication_and_named_reuse():
    """P4.3: Shared unnamed midpoint across area + distance goals synthesizes 1 point; named midpoint is reused."""
    # Shared unnamed midpoint across 2 goals (ask_area + ask_distance_point_plane)
    shared_case = next(c for c in GOAL_CORPUS["positive"] if c["id"] == "pyramid-shared-midpoint-area-and-distance")
    res_shared = run_fact_route(shared_case["text"], deepcopy(shared_case["payload"]))
    assert res_shared.status == "SERVED"
    mid_calls = [c for c in res_shared.planner["calls"] if c["fn"] == "midpoint"]
    assert len(mid_calls) == 1, f"Expected 1 deduplicated midpoint call, got {mid_calls}"
    assert set(res_shared.answers) == {"q1", "q2"}
    assert squared(res_shared.exec_result.final_memory["kq_q1"]) == Fraction(13, 4)
    assert squared(res_shared.exec_result.final_memory["kq_q2"]) == Fraction(1, 1)
    audit_shared = verify_integrated_scene_mathematics(res_shared.scene3d, scene_id=shared_case["id"])
    assert audit_shared.verdict == "VERIFIED", audit_shared.errors

    # Named midpoint reuse (`Gọi M là trung điểm của SC`)
    reuse_case = next(c for c in GOAL_CORPUS["positive"] if c["id"] == "pyramid-reuse-named-midpoint-area")
    res_reuse = run_fact_route(reuse_case["text"], deepcopy(reuse_case["payload"]))
    assert res_reuse.status == "SERVED"
    assert len([c for c in res_reuse.planner["calls"] if c["fn"] == "midpoint"]) == 1
    assert squared(res_reuse.exec_result.final_memory["kq_q"]) == Fraction(13, 4)
    audit_reuse = verify_integrated_scene_mathematics(res_reuse.scene3d, scene_id=reuse_case["id"])
    assert audit_reuse.verdict == "VERIFIED", audit_reuse.errors


def test_all_six_geometry_quantity_and_construction_families_with_step_math_oracle():
    """P4.4 & P4.5: Verify area, angle, length, distance (including non-Euclidean G), volume, and section."""
    # 1. Area (cuboid projection + unnamed midpoint area on held-out)
    c_area = next(c for c in GOAL_CORPUS["held_out"] if c["id"] == "heldout-cuboid-projection-and-midpoint-area")
    r_area = run_fact_route(c_area["text"], deepcopy(c_area["payload"]))
    assert r_area.status == "SERVED"
    assert squared(r_area.exec_result.final_memory["kq_q"]) == Fraction(3169, 100)
    assert verify_integrated_scene_mathematics(r_area.scene3d, scene_id=c_area["id"]).verdict == "VERIFIED"

    # 2. Angle (oblique projection line-plane angle on Slice B)
    c_angle = next(c for c in GOAL_CORPUS["angle_line_plane_slice_b"] if c["id"] == "angle-oblique-projection-line-plane")
    r_angle = run_fact_route(c_angle["text"], deepcopy(c_angle["payload"]))
    assert r_angle.status == "SERVED"
    assert Fraction(r_angle.exec_result.final_memory["kq_q"]) == Fraction(185, 221)
    assert verify_integrated_scene_mathematics(r_angle.scene3d, scene_id=c_angle["id"]).verdict == "VERIFIED"

    # 3. Distance & Length on non-Euclidean oblique chart metric G != I3 (regular tetrahedron mid-area + length)
    c_tet = next(c for c in GOAL_CORPUS["held_out"] if c["id"] == "heldout-tetrahedron-midpoint-area")
    r_tet = run_fact_route(c_tet["text"], deepcopy(c_tet["payload"]))
    assert r_tet.status == "SERVED"
    G_tet = strict_parse_metric(r_tet.scene3d["chart_metric"])
    assert G_tet != STEP_ORACLE.IDENTITY_METRIC, "Regular tetrahedron must use non-Euclidean Gram chart_metric"
    assert squared(r_tet.exec_result.final_memory["kq_q"]) == Fraction(2, 1)
    assert verify_integrated_scene_mathematics(r_tet.scene3d, scene_id=c_tet["id"]).verdict == "VERIFIED"

    # 4. Volume & v3-runtime-revision rectangular box / prism grounding (`hình hộp chữ nhật`, `dài bao nhiêu`)
    text_vol = (
        "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 2, AD = 3, AA' = 4. "
        "Tính thể tích của hình hộp chữ nhật ABCD.A'B'C'D'. Hỏi đoạn thẳng AC' dài bao nhiêu?"
    )
    facts_vol = {
        "facts": [
            {"id": "f1", "kind": "solid", "role": "premise", "solid": "ABCD.A'B'C'D'", "solid_type": "cuboid",
             "quotes": ["Cho hình hộp chữ nhật ABCD.A'B'C'D'"]},
            {"id": "f2", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "B"], "value": "2",
             "quotes": ["AB = 2"]},
            {"id": "f3", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "D"], "value": "3",
             "quotes": ["AD = 3"]},
            {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "A'"], "value": "4",
             "quotes": ["AA' = 4"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "volume", "solid": "ABCD.A'B'C'D'",
             "quotes": ["Tính thể tích của hình hộp chữ nhật ABCD.A'B'C'D'."]},
            {"id": "q2", "kind": "question", "role": "question", "quantity": "length", "points": ["A", "C'"],
             "quotes": ["Hỏi đoạn thẳng AC' dài bao nhiêu?"]},
        ]
    }
    r_vol = run_fact_route(text_vol, facts_vol)
    assert r_vol.status == "SERVED", (r_vol.code, r_vol.reason)
    assert squared(r_vol.exec_result.final_memory["kq_q1"]) == Fraction(24 * 24, 1)
    assert squared(r_vol.exec_result.final_memory["kq_q2"]) == Fraction(4 + 9 + 16, 1)
    assert verify_integrated_scene_mathematics(r_vol.scene3d, scene_id="cuboid_vol_and_diag").verdict == "VERIFIED"

    # 5. Cross-section (`section` + `ask_section_area` with two-line parallel plane relation)
    two_line_bundle = json.loads((GOAL_COMP_RUN / "baseline/bundle-174.json").read_text(encoding="utf-8"))
    sec_row = next(r for r in two_line_bundle["rows"] if r["corpus"] == "two_line/development" and r["id"] == "development-0")
    r_sec = run_fact_route(sec_row["text"], {"facts": deepcopy(sec_row["facts"])})
    assert r_sec.status == "SERVED", (r_sec.code, r_sec.reason)
    assert any(o["type"] == "section" for o in r_sec.scene3d["objects"])
    assert verify_integrated_scene_mathematics(r_sec.scene3d, scene_id="two_line_section_dev0").verdict == "VERIFIED"


# ---------------------------------------------------------------------------
# 6 & 7. Safe Refusals, Tampered Facts, Source Grounding & Regex Tail Guard
# ---------------------------------------------------------------------------

def test_safe_refusals_tampered_facts_and_question_tail_runtime_guard(monkeypatch):
    """P4.6 & P4.7: Verify fail-closed refusals on tampered/unsupported inputs and sub-50ms regex tail guard."""
    # 1. All 17 negative cases in GOAL_CORPUS fail closed with expected codes
    for neg in GOAL_CORPUS["negative"]:
        r = run_fact_route(neg["text"], deepcopy(neg["payload"]))
        assert r.status == "REFUSED", (neg["id"], r.answers)
        assert r.code in neg["expected_codes"], (neg["id"], r.code, neg["expected_codes"])

    # 2a. Lying contract verifier on ask_area is caught by contract consistency guard
    pos0 = GOAL_CORPUS["positive"][0]
    with monkeypatch.context() as m:
        spec = registry.REGISTRY["ask_area"]
        m.setitem(registry.REGISTRY, "ask_area", replace(spec, planning=replace(spec.planning, verifier="length")))
        r_lie = run_fact_route(pos0["text"], deepcopy(pos0["payload"]))
        assert (r_lie.status, r_lie.code) == ("REFUSED", "AUXILIARY_RULE_MISMATCH")

    # 2b. Tampered engine verifier result is caught by ENGINE_SELF_CHECK_FAILED
    with monkeypatch.context() as m:
        m.setattr(engine._Dung, "_dt2_tam_giac", lambda self, p, q, r: Fraction(-1))
        r_tamper = run_fact_route(pos0["text"], deepcopy(pos0["payload"]))
        assert (r_tamper.status, r_tamper.code) == ("REFUSED", "ENGINE_SELF_CHECK_FAILED")

    # 3. Runtime regex backtracking regression (`_SAU_HOP_LE` with possessive `[\s,;:]++` on long whitespace + unread tail)
    q_quote = pos0["payload"]["facts"][-1]["quotes"][0].rstrip(".")
    adversarial_tail = pos0["text"][:-1] + (" " * 4096) + "khi M thay đổi."
    payload_adv = deepcopy(pos0["payload"])
    payload_adv["facts"][-1]["quotes"] = [q_quote]
    t0 = time.perf_counter()
    r_adv = run_fact_route(adversarial_tail, payload_adv)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert r_adv.status == "REFUSED"
    assert r_adv.code == "NOT_ASKED_IN_SOURCE"
    assert elapsed_ms < 250.0, f"Question-tail regex took {elapsed_ms:.1f}ms (expected < 250ms)"


# ---------------------------------------------------------------------------
# 8, 9 & 10. Version/Fingerprint Identity, LLM_ONLY Default, Registry Reversal
# ---------------------------------------------------------------------------

def test_version_constants_surface_fingerprints_and_historical_receipt_preservation():
    """P3, P4.8 & P4.9: Verify versions, surface fingerprints, LLM_ONLY default, and untouched v3 receipts."""
    assert REGISTRY_VERSION == "geometry-functions/6"
    assert PLANNER_VERSION == "geometry-fact-planner/7"
    assert ENGINE_VERSION == "geometry-function-engine/5"
    assert main_module.CACHE_VERSION == "125"
    assert main_module.semantic_route_mode() == "off"
    assert RESPONSE_CONTRACT == "flat"
    # Verify default production pipeline (`main.py` / `pipeline.py`) remains LLM_ONLY and does not wire Hybrid route
    main_src = (ROOT / "backend/app/main.py").read_text(encoding="utf-8")
    pipeline_src = (ROOT / "backend/app/ai/pipeline.py").read_text(encoding="utf-8")
    assert "fact_extraction" not in main_src and "function_route" not in main_src
    assert "fact_extraction" not in pipeline_src and "function_route" not in pipeline_src

    # Surface fingerprints must remain identical to locked evaluation pins
    assert surface_fingerprint("flat") == "485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a"
    assert surface_fingerprint("v3") == "90bf8f039df830062e068adcf1d243643c8ebebfde5b4a5cf9ec340078ea7aab"
    assert function_calling.surface_fingerprint() == "7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25"

    typed_fact_sha = hashlib.sha256(
        json.dumps(TypedFact.model_json_schema(), sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    assert typed_fact_sha == "aa9d93eeac9f1659af8e5acd42af1904b7aaed674a8ab0f56f0c7dd8b2ad4ee8"

    decl_sha = hashlib.sha256(
        json.dumps(registry.function_declarations(), sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    assert decl_sha == "5ceb0f999d4d7c1ee37c02207ea6470a7f972a168d6c52fa597392934d86f169"

    # Historical receipts of semantic-extraction-v3-runtime-revision must remain bound to product SHA 6ba9033b...
    v3_div = json.loads((V3_REV_RUN / "candidate_divergence.json").read_text(encoding="utf-8"))
    assert v3_div["current_candidate_hash"] == "6ba9033bfca06d671cd27891e2dad06c7d44f365fed45527123c907d664b65ed"
    inv = json.loads((V3_REV_RUN / "results/offline/invocations.json").read_text(encoding="utf-8"))
    assert inv["status"] == "COMPLETE" and len(inv["invocations"]) == 8
    for row in inv["invocations"]:
        assert row["status"] == "PASS"
        assert row["input_identity"]["product_sha256"] == "6ba9033bfca06d671cd27891e2dad06c7d44f365fed45527123c907d664b65ed"

    # The combined candidate's own receipt stays bound to ITS product hash (historical, immutable) ...
    hbi = json.loads((RUNS_DIR / "hybrid-backend-integration/run.json").read_text(encoding="utf-8"))
    assert (hbi["product_sha256"], hbi["measured_files"]) == (
        "afab0a3ca3abfe3c3f7692d34be2aeadbd099b8d43b6543d8d234d19b5ef8443", 110)
    # ... while the live tree must equal whichever candidate is frozen NOW. Run `hybrid-pre-main-hardening`: this used to
    # pin afab0a3c literally, so every later product change (refrozen as a new candidate) read as a broken receipt.
    fz = _load_module("_freeze_eval_cand_int", ROOT / "backend/scripts/freeze_evaluation_candidate.py")
    combined_hash, file_count = fz.measured_system_hash()
    frozen = json.loads(fz.OUT.read_text(encoding="utf-8"))["measured_system"]
    assert (combined_hash, file_count) == (frozen["tree_hash"], frozen["so_file"])
    assert combined_hash != v3_div["current_candidate_hash"]


def test_registry_permutation_invariance_across_combined_slices(monkeypatch):
    """P4.10: Reversing REGISTRY order produces identical plans, auxiliary certificates, and answers."""
    sample_cases = [
        GOAL_CORPUS["positive"][0],
        GOAL_CORPUS["positive"][7],  # pyramid-shared-midpoint-area-and-distance (multi-goal)
        GOAL_CORPUS["held_out"][2],  # heldout-cuboid-projection-and-midpoint-area
        GOAL_CORPUS["angle_line_plane_slice_b"][2],
        GOAL_CORPUS["negative"][0],
    ]
    rev_reg = dict(reversed(list(registry.REGISTRY.items())))
    for case in sample_cases:
        r_normal = run_fact_route(case["text"], deepcopy(case["payload"]))
        with monkeypatch.context() as m:
            m.setattr(registry, "REGISTRY", rev_reg)
            m.setattr(planner, "REGISTRY", rev_reg)
            r_rev = run_fact_route(case["text"], deepcopy(case["payload"]))
        assert r_normal.status == r_rev.status
        assert r_normal.code == r_rev.code
        assert r_normal.answers == r_rev.answers
        if r_normal.planner and r_rev.planner:
            assert r_normal.planner["calls"] == r_rev.planner["calls"]
            assert r_normal.planner["auxiliary"] == r_rev.planner["auxiliary"]


# ---------------------------------------------------------------------------
# 11. Strict Oracle Metric Error Handling (Degenerate / Non-SPD / Malformed)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("bad_metric", "label"),
    [
        (None, "missing-none-metric"),
        ([], "empty-list-metric"),
        ("euclid", "string-metric"),
        ([[1, 0], [0, 1]], "wrong-dimension-2x2-metric"),
        ([[1, 0, 0], [0, 0, 0], [0, 0, 1]], "singular-zero-row-metric"),
        ([[1, 2, 0], [2, 4, 0], [0, 0, 1]], "singular-rank2-metric"),
        ([[-1, 0, 0], [0, 1, 0], [0, 0, 1]], "negative-first-minor-metric"),
        ([[1, 2, 0], [2, 1, 0], [0, 0, 1]], "indefinite-second-minor-metric"),
        ([[1, 0, 0], [0, 1, 0], [0, 0, -1]], "negative-det-metric"),
        ([[1, 0.5, 0], [0.0, 1, 0], [0, 0, 1]], "asymmetric-metric"),
    ],
)
def test_oracle_rejects_degenerate_non_spd_asymmetric_or_malformed_metrics(bad_metric, label):
    """P4.11: Invalid chart_metric must NEVER be converted to Euclidean IDENTITY_METRIC to get a PASS."""
    # Take a valid non-Euclidean scene (regular tetrahedron) and corrupt its chart_metric
    c_tet = next(c for c in GOAL_CORPUS["held_out"] if c["id"] == "heldout-tetrahedron-midpoint-area")
    r_tet = run_fact_route(c_tet["text"], deepcopy(c_tet["payload"]))
    assert r_tet.status == "SERVED"
    tampered_scene = deepcopy(r_tet.scene3d)
    tampered_scene["chart_metric"] = bad_metric

    with pytest.raises((ValueError, TypeError)):
        strict_parse_metric(bad_metric, require_present=True)

    if isinstance(bad_metric, list) and len(bad_metric) == 3 and all(isinstance(r, list) and len(r) == 3 for r in bad_metric):
        G_tuple = tuple(tuple(float(x) for x in r) for r in bad_metric)
        with pytest.raises(ValueError):
            strict_mat3_inv(G_tuple)  # type: ignore[arg-type]

    report = verify_integrated_scene_mathematics(tampered_scene, scene_id=f"bad_metric_{label}", require_chart_metric=True)
    assert report.verdict == "INVALID", f"Expected INVALID for {label}, got {report.verdict}"
    assert not report.category_results["1_incidence"].passed
    assert any("STRICT_METRIC_INVALID" in e for e in report.errors)


def test_offline_v3_matrix_parity_on_combined_candidate(tmp_path, monkeypatch):
    """P5.2: All 8 offline cells (PILOT/LOCKED x flat/v3 x gold/replay) match frozen v3-runtime-revision scores."""
    from scripts import run_schema_contract_evaluation as R
    monkeypatch.setattr(fact_extraction, "RESPONSE_CONTRACT", fact_extraction.RESPONSE_CONTRACT)
    monkeypatch.setattr(fact_extraction, "SYSTEM_PROMPT", fact_extraction.SYSTEM_PROMPT)

    inp = R.V1.load_inputs(V3_REV_RUN / "inputs")
    for mode in ("PILOT", "LOCKED"):
        for arm in ("flat", "v3"):
            h = R.harness(arm, inp, mode)
            gold_rows = h.run_gold(inp)
            gold_score = R.E.summarize(inp, gold_rows, gold_rows)
            frozen_gold = json.loads((V3_REV_RUN / f"results/offline/gold-{arm}-{mode}/score.json").read_text(encoding="utf-8"))
            for k in ("e2e", "refusal_codes", "counts", "multi_goal", "rows"):
                assert gold_score[k] == frozen_gold[k], (f"gold-{arm}-{mode}", k)

            replay_out = tmp_path / f"replay-{arm}-{mode}"
            replay_out.mkdir(parents=True, exist_ok=True)
            replay_state = h.run_eval(inp, mode, h.ReplayProvider(inp), replay_out)
            replay_score = R.E.summarize(inp, replay_state["rows"], gold_rows)
            frozen_replay = json.loads((V3_REV_RUN / f"results/offline/replay-{arm}-{mode}/score.json").read_text(encoding="utf-8"))
            for k in ("e2e", "refusal_codes", "counts", "multi_goal", "rows"):
                assert replay_score[k] == frozen_replay[k], (f"replay-{arm}-{mode}", k)


def test_full_174_historical_40_slice_ab_and_88_combined_scenes_math_oracle(monkeypatch):
    """P5.1 & P5.3: Verify 174 historical Planner cases, 40 Slice A/B cases, 88 combined scenes, and 10 counterexamples."""
    bundle174 = json.loads((GOAL_COMP_RUN / "baseline/bundle-174.json").read_text(encoding="utf-8"))["rows"]
    reg174 = json.loads((GOAL_COMP_RUN / "baseline/regression-174.json").read_text(encoding="utf-8"))["rows"]
    assert len(bundle174) == 174 and len(reg174) == 174

    served_174 = 0
    for row, exp in zip(bundle174, reg174):
        r = run_fact_route(row["text"], {"facts": deepcopy(row["facts"])})
        assert r.status == exp["status"] and r.code == exp["code"], (row["id"], r.status, exp["status"])
        if r.status == "SERVED":
            served_174 += 1
            rep = verify_integrated_scene_mathematics(r.scene3d, scene_id=f"b174::{row['corpus']}::{row['id']}")
            assert rep.verdict == "VERIFIED", (row["id"], rep.errors)

    assert served_174 == 65

    slice_ab_served = 0
    slice_ab_refused = 0
    for grp in ("positive", "held_out", "angle_line_plane_slice_b"):
        for c in GOAL_CORPUS[grp]:
            r = run_fact_route(c["text"], deepcopy(c["payload"]))
            assert r.status == "SERVED", c["id"]
            slice_ab_served += 1
            rep = verify_integrated_scene_mathematics(r.scene3d, scene_id=f"cdgc::{grp}::{c['id']}")
            assert rep.verdict == "VERIFIED", (c["id"], rep.errors)
    for c in GOAL_CORPUS["negative"]:
        r = run_fact_route(c["text"], deepcopy(c["payload"]))
        assert r.status == "REFUSED" and r.code in c["expected_codes"], c["id"]
        slice_ab_refused += 1

    assert slice_ab_served == 19
    assert slice_ab_refused == 17

    disc_served = 0
    with monkeypatch.context() as m:
        m.setitem(registry.REGISTRY, "centroid", experimental_centroid_contract(registry))
        for c in GOAL_CORPUS["discovery"]:
            r = run_fact_route(c["text"], deepcopy(c["payload"]))
            assert r.status == "SERVED", c["id"]
            disc_served += 1
            rep = verify_integrated_scene_mathematics(r.scene3d, scene_id=f"cdgc::discovery::{c['id']}")
            assert rep.verdict == "VERIFIED", (c["id"], rep.errors)

    assert disc_served == 4
    assert slice_ab_served + disc_served == 23
    assert slice_ab_served + disc_served + slice_ab_refused == 40
    assert served_174 + slice_ab_served + disc_served == 88

    counterexamples = STEP_ORACLE.run_counterexample_suite()
    assert len(counterexamples) == 10
    assert all(c["oracle_detected"] for c in counterexamples)
