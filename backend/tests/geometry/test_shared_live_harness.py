"""Lock on the shared live-acceptance harness (`docs/evaluation/geometry/harness/live-acceptance/`, run
`axo-hybrid-local-model1-finalization-test-consolidation`).

The harness replaced per-run copies whose default output was the run directory they sat in. Equivalence is shown on
the frozen /12 evidence: the oracle and the aggregator, run on /12 inputs, reproduce the /12 deliverables exactly
(only `schema`/`harness_version` keys were renamed); the samplers, proxy and bench are byte-copies of the /12 tools
apart from bench identity strings. Every tool refuses to write over existing output."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
H = ROOT / "docs/evaluation/geometry/harness/live-acceptance"
R12 = ROOT / "docs/evaluation/geometry/runs/axo-hybrid-compositional-geometry-language-grounded-simulation"
OUTPUTS = ("LIVE_ACCEPTANCE_RESULTS", "SLM_LIVE_CONTRIBUTION_AUDIT", "VISUAL_AND_INTERACTION_ACCEPTANCE",
           "NETWORK_ISOLATION_PROOF")


def _py(*args):
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8",
                          env=env, timeout=300)


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _norm(d):
    return {k: v for k, v in d.items() if k not in ("schema", "harness_version")}


def test_oracle_selfcheck_and_replay_reproduce_the_frozen_12_verification(tmp_path):
    assert _py(H / "scene_oracle.py", "--selfcheck").returncode == 0
    out = tmp_path / "oracle.json"
    r = _py(H / "scene_oracle.py", R12 / "V12_ACCEPTANCE_MANIFEST.json", R12 / "evidence/v12_responses.jsonl", out)
    assert r.returncode == 0, r.stderr[-2000:]
    assert _load(out)["results"] == _load(R12 / "SCENE_ORACLE_VERIFICATION.json")["results"]
    before = out.read_bytes()
    r = _py(H / "scene_oracle.py", R12 / "V12_ACCEPTANCE_MANIFEST.json", R12 / "evidence/v12_responses.jsonl", out)
    assert r.returncode != 0 and "refusing to overwrite" in r.stderr and out.read_bytes() == before


def test_aggregate_replay_on_12_inputs_equals_the_frozen_12_deliverables(tmp_path):
    out = tmp_path / "agg"
    r = _py(H / "aggregate.py", "--run-dir", R12, "--layout", "v12", "--out-dir", out,
            "--proxy-selfcheck-ok", "--proxy-selfcheck-records", "2")
    assert r.returncode == 0, r.stderr[-2000:]
    for name in OUTPUTS:
        fresh = _load(out / f"{name}.json")
        assert _norm(fresh) == _norm(_load(R12 / f"{name}.json")), name
    assert _load(out / "LIVE_ACCEPTANCE_RESULTS.json")["harness_version"] == "axo-live-acceptance-harness/1"
    r = _py(H / "aggregate.py", "--run-dir", R12, "--layout", "v12", "--out-dir", out)
    assert r.returncode != 0 and "refusing to write into non-empty" in r.stderr


def test_unchanged_tools_are_byte_copies_of_the_12_tools():
    for name in ("egress_blackhole_proxy.py", "stack_memory_sampler.ps1", "tcp_egress_sampler.ps1"):
        assert (H / name).read_bytes() == (R12 / "tools" / name).read_bytes(), name


def test_holdout_freeze_is_intact():
    """/13 holdout: manifest, criteria, baseline stratum, builder and the harness it is measured with are frozen
    (LF-normalised SHA-256) before any Model 1 or geometry change; editing any of them afterwards is red."""
    import hashlib

    freeze = _load(ROOT / "docs/evaluation/geometry/runs/axo-hybrid-local-model1-finalization-test-consolidation/ACCEPTANCE_FREEZE.json")
    for rel, digest in freeze["files"].items():
        raw = (ROOT / rel).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(raw).hexdigest() == digest, rel
    frozen_harness = {Path(rel).name for rel in freeze["files"] if rel.startswith("docs/evaluation/geometry/harness/")}
    assert frozen_harness == {p.name for p in H.iterdir() if p.is_file()}, "harness file added/removed after the freeze"


def test_no_harness_tool_defaults_its_output_into_a_run_directory():
    for p in H.iterdir():
        if p.suffix in (".py", ".mjs"):
            text = p.read_text(encoding="utf-8")
            assert "runs/" not in text and "V12_ACCEPTANCE_MANIFEST" not in text.replace('"V12_ACCEPTANCE_MANIFEST.json"', ""), p.name
    shared = (H / "harness_paths.mjs").read_text(encoding="utf-8")
    assert "--out-dir is required" in shared and "refusing to write into non-empty" in shared
    for name in ("live_browser_acceptance.mjs", "ui_scenarios.mjs"):
        text = (H / name).read_text(encoding="utf-8")
        assert 'freshOutDir(ARGS.values["out-dir"])' in text and "process.env.AXO_" not in text, name


def test_triangle_area_audit_preserves_frozen_scores_and_checks_gram_coordinates():
    import importlib.util
    from fractions import Fraction
    from math import sqrt

    spec = importlib.util.spec_from_file_location("scene_oracle", H / "scene_oracle.py")
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)

    run = R12.parent / "axo-hybrid-local-model1-finalization-test-consolidation"
    expected = {"H057": ("S", "B", "C", 80), "H069": ("I'", "J", "K", 61)}
    manifest = _load(run / "ACCEPTANCE_MANIFEST.json")
    registered = {c["case_id"]: c["metric_oracle"] for c in manifest["valid_cases"]}
    lines = (run / "evidence/responses.jsonl").read_text(encoding="utf-8").splitlines()
    rows = {record["case_id"]: record["body"] for line in lines if (record := json.loads(line))["case_id"] in expected}

    for case_id, (a, b, c, area2) in expected.items():
        response = rows[case_id]
        triangle = oracle.Scene(response["envelope"]["scene3d"])
        u, v = (oracle.sub(triangle.P[oracle.pid(point)], triangle.P[oracle.pid(a)]) for point in (b, c))
        determinant = triangle.dot(u, u) * triangle.dot(v, v) - triangle.dot(u, v) ** 2
        assert determinant / 4 == Fraction(area2)
        rd = response["route_d"]
        assert oracle.numeric(rd["answers"], rd["answer_exact"], [sqrt(area2)])["status"] == "CORRECT"
        assert oracle.numeric(rd["answers"], rd["answer_exact"], registered[case_id])["status"] == "MISMATCH"
        assert oracle.numeric({"q1": "4"}, {}, [sqrt(area2)])["status"] == "MISMATCH"


def test_unified_verdict_fails_composite_when_completion_passes_but_slm_fails():
    from scripts.evaluate_live_text_acceptance import compute_live_text_verdicts

    criteria = {
        "primary": {"completion_rate_min": 0.85},
        "modalities": {"required": ["text"], "positive_completion_rate_min": 0.85},
        "slm_fallback": {"min_routed_sample": 8, "min_live_verified_scenes": 5, "rate_min": 0.50},
        "slm_independent": {"positive_total": 30, "verified_scene_rate_min": 0.60},
        "safety": {"all_negative_safe": True},
    }
    clean_safety = {
        "wrong_served": [],
        "grounding_violations_served": [],
        "unverified_relations_served": [],
        "fabricated_numeric_goals": [],
        "served_numeric_mismatch": [],
        "attachment_provenance_not_present": [],
    }
    clean_net = {
        "external_ai_calls_reported": 0,
        "browser_external_requests": 0,
        "proxy_intercepted": 0,
        "tcp_non_loopback_records": 0,
    }
    res = compute_live_text_verdicts(
        criteria=criteria,
        positive_completed=58,
        positive_total=66,
        by_modality={"text": {"positive": 66, "served": 58, "completed": 58, "negative": 22, "negative_safely_refused": 22}},
        candidate_slm_routed_ids=[f"S{i}" for i in range(13)],
        candidate_slm_verified_ids=["S0", "S1", "S2", "S3", "S4"],  # 5/13 = 0.3846 < 0.50
        baseline_slm_required_ids=[f"B{i}" for i in range(38)],
        baseline_slm_det_rescued_ids=[f"B{i}" for i in range(25)],
        baseline_slm_live_verified_ids=["B0", "B1", "B2", "B3", "B4"],
        negative_safe_count=22,
        negative_total=22,
        safety=clean_safety,
        network=clean_net,
        candidate_identity_consistent=True,
        slm_independent_audit={"positive_total": 30, "verified_scenes": 20, "negative_safe_refused": 10, "negative_total": 10, "false_assertions_served": 0, "invalid_relations_served": 0},
        t3_receipt={"verdict": "FULL_PRODUCT_GATE_PASS"},
        rewrite_safety_audit={"SEMANTIC_REWRITE_SAFETY_VERIFIED": True},
    )
    v = res["gates"]
    assert v["SYSTEM_TEXT_COMPLETION_THRESHOLD_MET"] is True
    assert v["TEXT_COMPLETION_THRESHOLD_MET"] is True
    assert v["NEGATIVE_SAFETY_GATE_MET"] is True
    assert v["SLM_FALLBACK_SAMPLE_FLOOR_MET"] is True
    assert v["SLM_FALLBACK_RATE_THRESHOLD_MET"] is False
    assert v["SLM_FALLBACK_GATE_MET"] is False
    assert v["COMPOSITE_LIVE_TEXT_ACCEPTED"] is False
    assert v["LOCAL_TEXT_MODEL1_VERIFIED"] is False
    assert v["LOCAL_VISION_REPLACEMENT_VERIFIED"] is False
    assert v["FULL_GEMINI_ROLE_REPLACEMENT_VERIFIED"] is False


def test_unified_verdict_enforces_small_denominator_and_safety_zero_tolerance():
    from scripts.evaluate_live_text_acceptance import compute_live_text_verdicts

    criteria = {
        "primary": {"completion_rate_min": 0.85},
        "modalities": {"required": ["text"], "positive_completion_rate_min": 0.85},
        "slm_fallback": {"min_routed_sample": 8, "min_live_verified_scenes": 5, "rate_min": 0.50},
        "slm_independent": {"positive_total": 30, "verified_scene_rate_min": 0.60},
        "safety": {"all_negative_safe": True},
    }
    clean_safety = {
        "wrong_served": [], "grounding_violations_served": [],
        "unverified_relations_served": [], "fabricated_numeric_goals": [],
        "served_numeric_mismatch": [], "attachment_provenance_not_present": [],
    }
    clean_net = {
        "external_ai_calls_reported": 0, "browser_external_requests": 0,
        "proxy_intercepted": 0, "tcp_non_loopback_records": 0,
    }
    # Small denominator: 5/6 (83% rate, 5 scenes) MUST fail sample floor (< 8)
    small_denom = compute_live_text_verdicts(
        criteria=criteria, positive_completed=65, positive_total=70,
        by_modality={"text": {"positive": 70, "served": 65, "completed": 65, "negative": 20, "negative_safely_refused": 20}},
        candidate_slm_routed_ids=[f"S{i}" for i in range(6)],
        candidate_slm_verified_ids=[f"S{i}" for i in range(5)],
        baseline_slm_required_ids=[f"B{i}" for i in range(10)],
        baseline_slm_det_rescued_ids=[], baseline_slm_live_verified_ids=[],
        negative_safe_count=20, negative_total=20,
        safety=clean_safety, network=clean_net, candidate_identity_consistent=True,
        slm_independent_audit={"positive_total": 30, "verified_scenes": 22, "negative_safe_refused": 10, "negative_total": 10},
        t3_receipt={"verdict": "FULL_PRODUCT_GATE_PASS"},
    )
    assert small_denom["gates"]["SLM_FALLBACK_SAMPLE_FLOOR_MET"] is False
    assert small_denom["gates"]["SLM_FALLBACK_GATE_MET"] is False
    assert small_denom["gates"]["COMPOSITE_LIVE_TEXT_ACCEPTED"] is False

    # Single fabricated numeric goal MUST fail safety & composite acceptance
    unsafe = compute_live_text_verdicts(
        criteria=criteria, positive_completed=65, positive_total=70,
        by_modality={"text": {"positive": 70, "served": 65, "completed": 65, "negative": 20, "negative_safely_refused": 20}},
        candidate_slm_routed_ids=[f"S{i}" for i in range(10)],
        candidate_slm_verified_ids=[f"S{i}" for i in range(7)],
        baseline_slm_required_ids=[], baseline_slm_det_rescued_ids=[], baseline_slm_live_verified_ids=[],
        negative_safe_count=20, negative_total=20,
        safety={**clean_safety, "fabricated_numeric_goals": [{"case_id": "F01"}]},
        network=clean_net, candidate_identity_consistent=True,
        slm_independent_audit={"positive_total": 30, "verified_scenes": 22, "negative_safe_refused": 10, "negative_total": 10},
        t3_receipt={"verdict": "FULL_PRODUCT_GATE_PASS"},
    )
    assert unsafe["gates"]["NEGATIVE_SAFETY_GATE_MET"] is False
    assert unsafe["gates"]["COMPOSITE_LIVE_TEXT_ACCEPTED"] is False


def test_historical_v15_live_results_reconciliation():
    from scripts.evaluate_live_text_acceptance import reconcile_live_results_artifact

    r15 = ROOT / "docs/evaluation/geometry/runs/grounded-geometry-language-recovery"
    rec = reconcile_live_results_artifact(
        live_results_path=r15 / "LIVE_TEXT_ACCEPTANCE_RESULTS.json",
        criteria_path=r15 / "holdout-3/ACCEPTANCE_CRITERIA.json",
        acceptance_freeze_path=r15 / "holdout-3/ACCEPTANCE_FREEZE.json",
        candidate_freeze_path=r15 / "holdout-3/CANDIDATE_FREEZE.json",
        t3_receipt_path=r15 / "FULL_T3_CACHE155_RECEIPT.json",
    )
    assert rec["reported_raw_flag_LIVE_SIMULATION_ACCEPTED"] is True
    assert rec["reconciled_verdicts"]["TEXT_COMPLETION_THRESHOLD_MET"] is True
    assert rec["reconciled_verdicts"]["NEGATIVE_SAFETY_GATE_MET"] is True
    assert rec["reconciled_verdicts"]["SLM_RATE_THRESHOLD_MET"] is False
    assert rec["reconciled_verdicts"]["SLM_COUNT_THRESHOLD_MET"] is True
    assert rec["reconciled_verdicts"]["COMPOSITE_LIVE_TEXT_ACCEPTED"] is False
    assert rec["reconciled_verdicts"]["LOCAL_TEXT_MODEL1_VERIFIED"] is False
    assert rec["scores"]["LEGACY_BASELINE_STRATUM_SCORE"]["completed_via_live_slm"] == 5
    assert rec["scores"]["LEGACY_BASELINE_STRATUM_SCORE"]["baseline_slm_required_total"] == 38


def test_independent_slm_capability_evaluator_contract_and_isolation(tmp_path, monkeypatch):
    import pytest
    from app.ai.local_slm_extractor import LocalSlmExtractionResult, build_compact_clause_context, validate_and_lower_compact_clause
    from scripts import evaluate_slm_independent_capability as eval_ind

    assert os.environ.get("ALLOW_LIVE_AI") == "0"
    assert not os.environ.get("GEMINI_API_KEY")

    pos_text = "Cho hình chóp P.QRS có PQ, PR, PS đôi một vuông góc, PQ = 2, PR = 3, PS = 6. Tính thể tích khối chóp P.QRS."
    neg_text = "Cho tứ diện PQRS có PQ, PR, PS không đôi một vuông góc, PQ = 2, PR = 3, PS = 4. Vẽ hình."

    def _fake_slm(text, **kwargs):
        assert kwargs.get("allow_parser_reconcile") is False
        assert kwargs.get("use_cache") is False
        assert kwargs.get("allow_download") is False
        if "không" in text:
            return LocalSlmExtractionResult(
                ok=False, strategy="compact_clause", model_key="qwen3-0.6b-axo-v9-q4_k_m",
                model_sha256="0" * 64, norm_text=text, wire_payload=None, canonical_payload=None,
                reason_code="INCONSISTENT_FACTS", reason_detail="negated",
                failure_taxonomy="CONTRADICTION_OR_UNGROUNDED",
                grounding_envelope={"slm_invoked": True, "accepted_ops": [], "grounding_status": "SLM_REPORTED_UNRESOLVED"},
            )
        ctx = build_compact_clause_context(text)
        canon, _ = validate_and_lower_compact_clause(
            ctx=ctx,
            raw_slm_json={
                "s": [0, "pyr", "P.QRS", 0],
                "r": [
                    {"c": 0, "p": "perp_ll", "a": "PQ", "b": "PR"},
                    {"c": 0, "p": "perp_ll", "a": "PQ", "b": "PS"},
                    {"c": 0, "p": "perp_ll", "a": "PR", "b": "PS"},
                    {"c": 1, "p": "len", "a": "PQ", "q": "2"},
                    {"c": 1, "p": "len", "a": "PR", "q": "3"},
                    {"c": 1, "p": "len", "a": "PS", "q": "6"},
                ],
                "g": [{"c": 2, "t": "vol", "tgt": "P.QRS"}],
                "u": [],
            },
            closure_mode="v9",
            allow_parser_reconcile=False,
        )
        assert canon is not None
        return LocalSlmExtractionResult(
            ok=True, strategy="compact_clause", model_key="qwen3-0.6b-axo-v9-q4_k_m",
            model_sha256="0" * 64, norm_text=text, wire_payload=canon, canonical_payload=canon,
            reason_code=None, reason_detail=None, failure_taxonomy="NONE",
            grounding_envelope={"slm_invoked": True, "accepted_ops": [], "grounding_status": "GROUNDED_AND_LOWERED"},
        )

    monkeypatch.setattr(eval_ind, "run_local_slm_extraction", _fake_slm)
    manifest = {
        "run_id": "test-ind", "set": "unit",
        "valid_cases": [{
            "case_id": "T1", "original_input": pos_text, "expected_behavior": "SERVE",
            "gold_entities": {"solid_vertices": ["P", "Q", "R", "S"], "auxiliary_points": []},
            "expected_counts": {"vertices": 4, "faces": 4},
            "expected_scene_object_types": ["solid", "point3"],
            "gold_relations": [["perp_ll", "PQ", "PR"], ["perp_ll", "PQ", "PS"], ["perp_ll", "PR", "PS"], ["len2", "PQ", "4"]],
            "metric_oracle": [6.0],
        }],
        "negative_cases": [{"case_id": "N1", "original_input": neg_text, "expected_behavior": "SAFE_REFUSE"}],
    }
    mpath = tmp_path / "manifest.json"
    opath = tmp_path / "out.json"
    mpath.write_text(json.dumps(manifest), encoding="utf-8")
    assert eval_ind.main(["--manifest", str(mpath), "--out", str(opath)]) == 0
    rep = _load(opath)
    assert rep["schema"] == "axo-slm-independent-capability-audit/1"
    assert rep["allow_parser_reconcile"] is False
    assert rep["local_parser_bypass_used"] is False
    assert rep["summary"]["verified_scenes"] == 1
    assert rep["summary"]["negative_safe_refused"] == 1
    assert rep["summary"]["false_assertions_served"] == 0
    with pytest.raises(FileExistsError):
        eval_ind.main(["--manifest", str(mpath), "--out", str(opath)])

    # Isolation violation if accepted_ops ever contains parser_reconcile
    monkeypatch.setattr(
        eval_ind, "run_local_slm_extraction",
        lambda text, **kw: LocalSlmExtractionResult(
            ok=True, strategy="compact_clause", model_key="x", model_sha256="0" * 64, norm_text=text,
            wire_payload=None, canonical_payload={}, reason_code=None, reason_detail=None, failure_taxonomy="NONE",
            grounding_envelope={"slm_invoked": True, "accepted_ops": ["parser_reconcile"]},
        ),
    )
    with pytest.raises(RuntimeError, match="Isolation violation"):
        eval_ind.evaluate_manifest(manifest)
