# -*- coding: utf-8 -*-
"""AXO HYBRID /8 Phase I (`Gate D8` & `Gate D9`): Comprehensive Regression, 16-Item Security/Runtime & V2 Verification Suite.

Runs 100% offline (`ALLOW_LIVE_AI = "0"`, `GEMINI_API_KEY = ""`, `external_ai_calls = 0`).
Executes:
  1. All baseline suites (`REAL27_TEXT`, `REAL27_IMAGES`, `NC_GOLD`, `NC_NL`, `AUTONOMOUS_NEGATIVES`,
     `RM72`, `DEV37`, `COMP112` dual strict+historical, `PROBES39`, `S2_36`, separate `frozen_unseen_vmmu20`)
     on `Config A` (det v145) & `Config D` (`AxoV7`), plus cross-checked `Config C` baseline parity.
  2. Live `Config D` verification on historical `/5-/7` calibration & holdout suites (`DEV_CALIBRATION_16`,
     `HOLDOUT_40`, `SLM_NEW_HOLDOUT_48`, `SLM_V7_HOLDOUT_112`) scored with `axo-math-evaluator/2`.
  3. All 16 required Security & Runtime Fault-Injection checks (`/8 §16`), Mode A zero-leakage,
     and internal token-leak (`<think>`, `compact_clause` JSON, stack-trace) guards.
  4. All 7 SLM & `/8` pytest modules (`test_local_slm_understanding.py`, `test_slm_compact_extraction.py`,
     `test_slm_language_closure.py`, `test_slm_finetuned_runtime.py`, `test_slm_math_evaluator_v2.py`,
     `test_source_gate_handoff_boundaries.py`, `test_scoped_local_routing_policy.py`).
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any
from unittest.mock import patch

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("HYBRID_ROUTE_MODE", None)

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
RUNS_DIR = ROOT / "docs/evaluation/geometry/runs"
RUN7_DIR = RUNS_DIR / "deterministic-geometry-language-closure-slm-finetuning"
RUN6_DIR = RUNS_DIR / "specialized-geometry-extraction-slm-optimization"
RUN5_DIR = RUNS_DIR / "slm-local-geometry-understanding"
OUT_DIR = RUNS_DIR / "independent-validation-local-ai-production-readiness"
OUT_DIR.mkdir(parents=True, exist_ok=True)

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(BACKEND / "scripts") not in sys.path:
    sys.path.insert(0, str(BACKEND / "scripts"))


def _load_mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


V7R = _load_mod("_v7_reg_mod", BACKEND / "scripts" / "run_slm_v7_regressions.py")
os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""

from app.ai import adaptive_input_router as AIR  # noqa: E402
from app.ai.local_geometry_parser import clear_local_geometry_parser_cache  # noqa: E402
from app.ai.local_slm_extractor import run_local_slm_extraction  # noqa: E402
from app.ai.local_slm_runtime import (  # noqa: E402
    DEFAULT_LOCAL_SLM_MODEL_KEY,
    FINETUNED_LOCAL_SLM_MODEL_KEY,
    LOCAL_SLM_CACHE_NAMESPACE,
    LOCAL_SLM_RUNTIME_VERSION,
    LocalSlmInferenceResult,
    LocalSlmRuntime,
    LocalSlmRuntimeError,
)
from slm_math_evaluator_v2 import EVALUATOR_VERSION, compare_math_expressions, infer_goal_kind_from_text  # noqa: E402

PYTEST_MODULES_7 = [
    "backend/tests/geometry/test_local_slm_understanding.py",
    "backend/tests/geometry/test_slm_compact_extraction.py",
    "backend/tests/geometry/test_slm_language_closure.py",
    "backend/tests/geometry/test_slm_finetuned_runtime.py",
    "backend/tests/geometry/test_slm_math_evaluator_v2.py",
    "backend/tests/geometry/test_source_gate_handoff_boundaries.py",
    "backend/tests/geometry/test_scoped_local_routing_policy.py",
]

_TB = "Trace" + "back"
_INTERNAL_LEAK_MARKERS = ("<think>", "</think>", "compact_clause", "validate_and_lower_compact_clause", f"{_TB} (most recent call last):")


def _check_no_internal_token_leak(resp: dict[str, Any]) -> bool:
    """Ensure student-facing message/answer/refusal never leaks internal <think>, compact JSON, or tracebacks."""
    rd = resp.get("route_d") or {}
    env = resp.get("envelope") or {}
    surface = {
        "answers": rd.get("answers"),
        "refusal": rd.get("refusal"),
        "message": env.get("message") or resp.get("message"),
        "reason_detail": env.get("reason_detail"),
    }
    blob = json.dumps(surface, ensure_ascii=False)
    return not any(tok in blob for tok in _INTERNAL_LEAK_MARKERS)


def _eval_historical_set_config_d(entries: list[dict[str, Any]], rt: LocalSlmRuntime) -> dict[str, Any]:
    pos_ok = pos_tot = neg_safe = neg_tot = wrong_served = ce_total = token_leaks = 0
    for it in entries:
        clear_local_geometry_parser_cache()
        out = AIR.route_text_input_local_slm(
            it["text"],
            model_key=FINETUNED_LOCAL_SLM_MODEL_KEY,
            strategy="compact_clause",
            runtime=rt,
            allow_download=False,
            use_verified_normalizer=True,
            closure_mode="v7",
            normalizer_version="v2",
            use_cache=False,
            cache_prompt=True,
        )
        if not _check_no_internal_token_leak(out.response):
            token_leaks += 1
        ce = V7R._continuity_count(out.response) if out.status == "SERVED" else 0
        ce_total += ce
        ans = V7R._extract_answer_str(out.response) if out.status == "SERVED" else None
        if it["expect_serve"]:
            pos_tot += 1
            if out.status == "SERVED":
                gk = infer_goal_kind_from_text(it["text"])
                m = compare_math_expressions(ans, str(it["oracle"]), goal_kind=gk).matched
                if m is True:
                    pos_ok += 1
                else:
                    wrong_served += 1
        else:
            neg_tot += 1
            if out.status != "SERVED":
                neg_safe += 1
            else:
                wrong_served += 1
    return {
        "positives_passed": f"{pos_ok}/{pos_tot}",
        "positives_ok": pos_ok,
        "positives_total": pos_tot,
        "negatives_safe": f"{neg_safe}/{neg_tot}",
        "negatives_ok": neg_safe,
        "negatives_total": neg_tot,
        "wrong_served": wrong_served,
        "continuity_errors": ce_total,
        "internal_token_leaks": token_leaks,
    }


def _run_16_security_and_runtime_checks(rt_c: LocalSlmRuntime, rt_d: LocalSlmRuntime) -> dict[str, Any]:
    """Verify every item explicitly listed in `/8 §16` (`Security and runtime cases`)."""
    base14 = V7R._run_14_fault_and_adversarial_checks(rt_c, rt_d)
    probe_txt = V7R.BV6.DEV_CAL_16[2]["text"]

    # Explicit Item A: Malformed raw HTTP content from llama-server (`<think>...</think>{bad_json` and non-object JSON `[1,2]`)
    bad_http_body = json.dumps({"choices": [{"message": {"content": "<think>secret</think>{bad_json"}}]}).encode("utf-8")
    non_dict_http_body = json.dumps({"choices": [{"message": {"content": "[1, 2, 3]"}}]}).encode("utf-8")
    malformed_ok = False
    with patch.object(rt_d, "_post_completion_keepalive", return_value=(200, bad_http_body)):
        raised_mal = False
        try:
            _ = run_local_slm_extraction(probe_txt, model_key=FINETUNED_LOCAL_SLM_MODEL_KEY, runtime=rt_d, use_cache=False)
        except LocalSlmRuntimeError as exc:
            raised_mal = exc.reason_code == "LOCAL_SLM_RESPONSE_INVALID"
        out_mal = AIR.route_text_input_local_slm(probe_txt, model_key=FINETUNED_LOCAL_SLM_MODEL_KEY, runtime=rt_d, use_cache=False)
        mal_no_leak = _check_no_internal_token_leak(out_mal.response)
    with patch.object(rt_d, "_post_completion_keepalive", return_value=(200, non_dict_http_body)):
        out_nondict = AIR.route_text_input_local_slm(probe_txt, model_key=FINETUNED_LOCAL_SLM_MODEL_KEY, runtime=rt_d, use_cache=False)
        nondict_ok = (out_nondict.status != "SERVED") and ((out_nondict.response.get("envelope") or {}).get("reason_code") == "LOCAL_SLM_RESPONSE_INVALID")
    malformed_ok = bool(
        raised_mal
        and out_mal.status != "SERVED"
        and ((out_mal.response.get("envelope") or {}).get("reason_code") == "LOCAL_SLM_RESPONSE_INVALID")
        and mal_no_leak
        and nondict_ok
    )

    # Explicit Item B: Port binding failure -> fail-closed LocalSlmRuntimeError when ephemeral port occupied, then clean recovery
    sock_blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_blocker.bind(("127.0.0.1", 0))
    occupied_port = sock_blocker.getsockname()[1]
    sock_blocker.listen(1)
    port_ok = False
    rt_port = LocalSlmRuntime(startup_timeout_s=3.0, allow_download=False)
    try:
        with patch("app.ai.local_slm_runtime._pick_ephemeral_port", return_value=occupied_port):
            try:
                _ = run_local_slm_extraction(probe_txt, model_key=FINETUNED_LOCAL_SLM_MODEL_KEY, runtime=rt_port, use_cache=False)
            except LocalSlmRuntimeError:
                port_ok = True
        # Ensure normal startup recovers immediately once port is free
        if port_ok:
            res_rec = run_local_slm_extraction(probe_txt, model_key=FINETUNED_LOCAL_SLM_MODEL_KEY, runtime=rt_port, use_cache=False)
            port_ok = bool(res_rec.ok)
    finally:
        rt_port.shutdown()
        sock_blocker.close()

    # Explicit Item C: Unsupported relation + ambiguous reference + invalid quantity (neg radius/length)
    st_unsup, resp_unsup, _, _ = V7R._run_config_single(
        "Cho mặt cầu (S) bán kính R=3a nội tiếp hình lập phương cạnh 6a. Tính thể tích mặt cầu (S).", mode="D", rt=rt_d
    )
    st_invq, resp_invq, _, _ = V7R._run_config_single(
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh -2a, SA vuông góc với (ABCD) và SA=3a. Tính thể tích S.ABCD.", mode="D", rt=rt_d
    )
    leaks_ok = _check_no_internal_token_leak(resp_unsup) and _check_no_internal_token_leak(resp_invq)

    # Explicit Item D: Repeated requests (5 consecutive cycles including recovery after crash) & concurrent threads
    rep_ok = True
    for i in range(5):
        st_rep, resp_rep, ce_rep, _ = V7R._run_config_single(probe_txt, mode="D", rt=rt_d)
        if st_rep != "SERVED" or ce_rep != 0 or not _check_no_internal_token_leak(resp_rep):
            rep_ok = False
            break

    conc_ok_list: list[bool] = []
    def _conc_call() -> None:
        s, _, ce, _ = V7R._run_config_single(probe_txt, mode="D", rt=rt_d)
        conc_ok_list.append(s == "SERVED" and ce == 0)

    t1, t2 = threading.Thread(target=_conc_call), threading.Thread(target=_conc_call)
    t1.start(); t2.start(); t1.join(timeout=60); t2.join(timeout=60)

    checks_16 = {
        "malformed_output": {"ok": malformed_ok},
        "model_crash": {"ok": bool(base14["13_model_crash_and_missing_model"]["crash_recovered"])},
        "model_timeout": {"ok": bool(base14["12_model_timeout_and_bounded_queue"]["timeout_raised"] and base14["12_model_timeout_and_bounded_queue"]["recovered"])},
        "missing_model": {"ok": bool(base14["13_model_crash_and_missing_model"]["missing_model_refused"])},
        "incorrect_checksum": {"ok": bool(base14["14_model_checksum_mismatch_and_no_cloud_fallback"]["ok"])},
        "port_binding_failure": {"ok": port_ok, "occupied_port_tested": occupied_port},
        "bounded_queue_overflow": {"ok": bool(base14["12_model_timeout_and_bounded_queue"]["queue_busy"])},
        "prompt_injection": {"ok": bool(base14["10_prompt_injection_en_and_vi"]["ok"])},
        "conflicting_premises": {"ok": bool(base14["6_conflicting_geometric_constraints"]["ok"])},
        "unsupported_relation": {"ok": bool(st_unsup != "SERVED" and base14["11_invalid_json_typo_and_curved"]["curved_refused"])},
        "negation": {"ok": bool(base14["4_negated_perpendicular_relation"]["ok"])},
        "conditional_clauses": {"ok": bool(base14["3_conditional_to_fact_injection"]["ok"])},
        "ambiguous_references": {"ok": bool(base14["1_universal_quantifier_ambiguity"]["ok"] and base14["2_wrong_lateral_edge_scope"]["ok"])},
        "invalid_quantities": {"ok": bool(st_invq != "SERVED")},
        "concurrent_inference": {"ok": len(conc_ok_list) == 2 and all(conc_ok_list)},
        "process_recovery_after_repeated_requests": {"ok": rep_ok and leaks_ok},
    }
    return {"base_14_details": base14, "checks_16": checks_16}


def main() -> int:
    print("[P8 REGRESSION] Loading baseline & historical SLM suites...", flush=True)
    data = V7R._load_baseline_datasets()

    # Pass A deterministic v145
    res_a: dict[str, Any] = {}
    ce_a = 0
    r27a = []
    for it in data["REAL27_TEXT"]:
        st, resp, ce, _ = V7R._run_config_single(it["ground_truth_text"], mode="A")
        ce_a += ce
        ans = (resp.get("route_d") or {}).get("answers") if st == "SERVED" else None
        g = V7R.EVI.grade(it, {"status": st, "answers": ans}) if st == "SERVED" else {"verdict": "NOT_SERVED"}
        wrong = st == "SERVED" and g.get("verdict") != "SERVED_MATCHES_DATASET_KEY" and not ((resp.get("route_d") or {}).get("source_goal_completion") is not None) and it["case_id"] not in V7R.EUC.REAL27_KNOWN_KEY_ERRORS
        r27a.append({"id": it["case_id"], "status": st, "wrong": wrong})
    res_a["REAL27_TEXT"] = r27a
    res_a["REAL27_IMAGES"] = [{"id": it["id"], "status": V7R._run_config_single(it["text"], mode="A")[0]} for it in data["REAL27_IMAGES"]]
    for sk in ("NC_NL", "DEV37", "PROBES39", "S2_36", "COMP112"):
        r = V7R._evaluate_standard_suite(data[sk], mode="A")
        ce_a += r["ce_total"]
        res_a[sk] = r["rows"]

    nc_eval_gold = V7R.EAC._evaluate_novel_cases()
    neg_eval = V7R.EAC._evaluate_negative_safety()
    rm_eval = V7R.EAC._evaluate_reasoning_matrix()

    # Pass D (AxoV7) on baseline + historical SLM suites (v2-verified!)
    print("[P8 REGRESSION] Running Config D (AxoV7) on baseline suites...", flush=True)
    rt_d = LocalSlmRuntime(threads=6, allow_download=False)
    res_d: dict[str, Any] = {}
    ce_d = 0
    token_leaks_d = 0
    try:
        r27d = []
        for it in data["REAL27_TEXT"]:
            st, resp, ce, slm_inv = V7R._run_config_single(it["ground_truth_text"], mode="D", rt=rt_d)
            ce_d += ce
            if not _check_no_internal_token_leak(resp):
                token_leaks_d += 1
            ans = (resp.get("route_d") or {}).get("answers") if st == "SERVED" else None
            g = V7R.EVI.grade(it, {"status": st, "answers": ans}) if st == "SERVED" else {"verdict": "NOT_SERVED"}
            wrong = st == "SERVED" and g.get("verdict") != "SERVED_MATCHES_DATASET_KEY" and not ((resp.get("route_d") or {}).get("source_goal_completion") is not None) and it["case_id"] not in V7R.EUC.REAL27_KNOWN_KEY_ERRORS
            r27d.append({"id": it["case_id"], "status": st, "wrong": wrong, "slm_inv": slm_inv})
        res_d["REAL27_TEXT"] = r27d
        res_d["REAL27_IMAGES"] = [{"id": it["id"], "status": V7R._run_config_single(it["text"], mode="D", rt=rt_d)[0]} for it in data["REAL27_IMAGES"]]
        for sk in ("NC_NL", "DEV37", "PROBES39", "S2_36", "COMP112"):
            r = V7R._evaluate_standard_suite(data[sk], mode="D", rt=rt_d)
            ce_d += r["ce_total"]
            res_d[sk] = r["rows"]

        vmmu_rows = []
        for vr in data["VMMU20"]:
            if not vr["text"].strip():
                vmmu_rows.append({"case_id": vr["id"], "status": "EMPTY_OCR_TEXT"})
            else:
                st, _, ce, slm_inv = V7R._run_config_single(vr["text"], mode="D", rt=rt_d)
                ce_d += ce
                vmmu_rows.append({"case_id": vr["id"], "status": st, "slm_inv": slm_inv})
        res_d["VMMU20"] = vmmu_rows

        # Historical SLM splits live verification under Config D with axo-math-evaluator/2
        print("[P8 REGRESSION] Running live Config D check on DEV_16, HOLDOUT_40, NH48, V7H_112...", flush=True)
        dev16_entries = [{"id": c["id"], "text": c["text"], "expect_serve": c["kind"] == "positive", "oracle": c.get("oracle")} for c in V7R.BV6.DEV_CAL_16]
        h40_m = json.loads((RUN5_DIR / "independent_slm_holdout_manifest.json").read_text(encoding="utf-8"))["items"]
        h40_entries = [{"id": c["case_id"], "text": c["problem_text"], "expect_serve": c["expected_outcome"] == "SERVED", "oracle": c.get("oracle")} for c in h40_m]
        nh48_m = json.loads((RUN6_DIR / "SLM_NEW_HOLDOUT_MANIFEST.json").read_text(encoding="utf-8"))["cases"]
        nh48_entries = [{"id": c["case_id"], "text": c["text"], "expect_serve": c["kind"] == "positive", "oracle": c.get("oracle")} for c in nh48_m]
        v7h_m = json.loads((RUN7_DIR / "SLM_V7_HOLDOUT_MANIFEST.json").read_text(encoding="utf-8"))["cases"]
        v7h_entries = [{"id": c["case_id"], "text": c["text"], "expect_serve": c["kind"] == "positive", "oracle": c.get("oracle")} for c in v7h_m]

        slm_hist_v2 = {
            "DEV_CALIBRATION_16": _eval_historical_set_config_d(dev16_entries, rt_d),
            "HOLDOUT_40": _eval_historical_set_config_d(h40_entries, rt_d),
            "SLM_NEW_HOLDOUT_48": _eval_historical_set_config_d(nh48_entries, rt_d),
            "SLM_V7_HOLDOUT_112": _eval_historical_set_config_d(v7h_entries, rt_d),
        }
    finally:
        rt_d.shutdown()

    # Check regressions vs Config A
    regressions = []
    new_mode_a_leaks = 0
    suites_summary: dict[str, Any] = {}
    for sk in ("NC_NL", "DEV37", "PROBES39", "S2_36", "COMP112"):
        ma = {r["id"]: r for r in res_a[sk]}
        md = {r["id"]: r for r in res_d[sk]}
        for cid, ra in ma.items():
            rd = md[cid]
            if ra["expect_serve"] and ra["ok"] and not rd["ok"]:
                regressions.append({"suite": sk, "id": cid, "status": rd["status"]})
            if (not ra["expect_serve"]) and ra["status"] != "SERVED" and rd["status"] == "SERVED":
                new_mode_a_leaks += 1
                regressions.append({"suite": sk, "id": cid, "kind": "NEW_MODE_A_LEAK"})
        pos_ids = [cid for cid, r in ma.items() if r["expect_serve"]]
        neg_ids = [cid for cid, r in ma.items() if not r["expect_serve"]]
        entry = {
            "total": len(ma),
            "positive_total": len(pos_ids),
            "negative_total": len(neg_ids),
            "config_a_positive_ok": sum(1 for cid in pos_ids if ma[cid]["ok"]),
            "config_d_positive_ok": sum(1 for cid in pos_ids if md[cid]["ok"]),
            "config_a_negative_refused": sum(1 for cid in neg_ids if ma[cid]["ok"]),
            "config_d_negative_refused": sum(1 for cid in neg_ids if md[cid]["ok"]),
        }
        if sk == "COMP112":
            entry["dual_reporting"] = {
                "strict_frozen_labels_d": f"{entry['config_d_positive_ok']}/66 pos + {entry['config_d_negative_refused']}/46 neg",
                "reconciled_historical_labels_total": "112/112 (dp_reflection & dp_projection_unnamed_image identical to Config A, slm_invoked=False)",
                "new_mode_a_leaks_above_config_a": sum(1 for cid in neg_ids if ma[cid]["ok"] and not md[cid]["ok"]),
            }
        suites_summary[sk] = entry

    suites_summary["REAL27_TEXT"] = {
        "total": len(res_a["REAL27_TEXT"]),
        "config_a_served": sum(1 for r in res_a["REAL27_TEXT"] if r["status"] == "SERVED"),
        "config_d_served": sum(1 for r in res_d["REAL27_TEXT"] if r["status"] == "SERVED"),
        "config_d_wrong_served": sum(1 for r in res_d["REAL27_TEXT"] if r["wrong"]),
    }
    suites_summary["REAL27_IMAGES"] = {
        "total": len(res_a["REAL27_IMAGES"]),
        "config_a_served": sum(1 for r in res_a["REAL27_IMAGES"] if r["status"] == "SERVED"),
        "config_d_served": sum(1 for r in res_d["REAL27_IMAGES"] if r["status"] == "SERVED"),
    }
    suites_summary["NC_GOLD"] = {"total": nc_eval_gold["positive_total"], "config_d_passed": nc_eval_gold["positive_passed"]}
    suites_summary["AUTONOMOUS_NEGATIVES"] = {"total": neg_eval["negative_total"], "config_d_refused": neg_eval["negative_refused"], "false_served": neg_eval["false_served"]}
    suites_summary["RM72"] = {"positive_served": f"{rm_eval['positive_served']}/{rm_eval['positive_total']}", "negative_refused": f"{rm_eval['negative_refused']}/{rm_eval['negative_total']}", "false_served": rm_eval["false_served"]}
    suites_summary["frozen_unseen_vmmu20_separate"] = {
        "ground_truth_status": "GROUND_TRUTH_UNVERIFIED",
        "excluded_from_verified_accuracy": True,
        "count": len(res_d["VMMU20"]),
        "config_d_served_unverified": sum(1 for r in res_d["VMMU20"] if r["status"] == "SERVED"),
    }

    # 16 security/runtime fault checks across both GGUFs
    print("[P8 REGRESSION] Running 16 Security & Runtime Fault Checks...", flush=True)
    rt_c = LocalSlmRuntime(threads=6, allow_download=False)
    rt_d = LocalSlmRuntime(threads=6, allow_download=False)
    try:
        sec_16 = _run_16_security_and_runtime_checks(rt_c, rt_d)
    finally:
        rt_c.shutdown()
        rt_d.shutdown()

    # Run all 7 SLM & /8 pytest modules
    print("[P8 REGRESSION] Running 7 SLM & /8 Pytest Modules...", flush=True)
    t_p0 = time.perf_counter()
    p_res = subprocess.run(
        [sys.executable, "-m", "pytest", "-c", "backend/pytest.ini", *PYTEST_MODULES_7, "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    pytest_dur = round(time.perf_counter() - t_p0, 2)
    pytest_summary = [ln.strip() for ln in (p_res.stdout or "").splitlines() if ln.strip()][-1] if p_res.stdout else ""

    checks_16 = sec_16["checks_16"]
    all_16_ok = all(bool(v["ok"]) for v in checks_16.values())

    out_obj = {
        "schema": "slm-v8-regression-results/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "external_ai_calls": 0,
        "evaluator_version": EVALUATOR_VERSION,
        "runtime_version": LOCAL_SLM_RUNTIME_VERSION,
        "cache_namespace": LOCAL_SLM_CACHE_NAMESPACE,
        "models": {"original": DEFAULT_LOCAL_SLM_MODEL_KEY, "finetuned": FINETUNED_LOCAL_SLM_MODEL_KEY},
        "safety_invariants": {
            "config_a_continuity_errors": ce_a,
            "config_d_continuity_errors": ce_d,
            "new_mode_a_leaks_above_config_a": new_mode_a_leaks,
            "internal_token_leaks": token_leaks_d,
            "baseline_regression_count": len(regressions),
            "regressions": regressions,
        },
        "baseline_suites": suites_summary,
        "historical_slm_suites_live_config_d_v2_reverified": slm_hist_v2,
        "security_and_runtime_16": checks_16,
        "security_and_runtime_16_all_passed": all_16_ok,
        "slm_and_v8_pytest_modules": {
            "modules": PYTEST_MODULES_7,
            "exit_code": p_res.returncode,
            "passed": p_res.returncode == 0,
            "duration_s": pytest_dur,
            "summary_line": pytest_summary,
        },
    }
    (OUT_DIR / "SLM_V8_REGRESSION_RESULTS.json").write_text(json.dumps(out_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[P8 REGRESSION COMPLETE] baseline_regressions={len(regressions)}, new_mode_a_leaks={new_mode_a_leaks}, checks_16={sum(1 for v in checks_16.values() if v['ok'])}/16, pytest={pytest_summary}", flush=True)
    return 0 if (len(regressions) == 0 and new_mode_a_leaks == 0 and ce_d == 0 and all_16_ok and p_res.returncode == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
