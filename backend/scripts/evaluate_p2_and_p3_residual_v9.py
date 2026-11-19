# -*- coding: utf-8 -*-
"""AXO HYBRID /9 — Step 2/P3 Residual Error Audit: Evaluate `AxoV7` + `v9`/`v3` Closure on C60 + /7 Residuals."""
from __future__ import annotations

from collections import Counter
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("HYBRID_ROUTE_MODE", None)

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
RUNS_DIR = ROOT / "docs/evaluation/geometry/runs"
OUT_DIR = RUNS_DIR / "axo-hybrid-local-ai-replacement-vietnamese-nlu-offline-cutover"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(BACKEND / "scripts") not in sys.path:
    sys.path.insert(0, str(BACKEND / "scripts"))

from app.ai import adaptive_input_router as AIR  # noqa: E402
from app.ai.local_geometry_parser import clear_local_geometry_parser_cache  # noqa: E402
from app.ai.local_slm_extractor import V9_CLOSURE_MODE  # noqa: E402
from app.ai.local_slm_runtime import (  # noqa: E402
    FINETUNED_LOCAL_SLM_MODEL_KEY,
    V9_LOCAL_SLM_MODEL_KEY,
    LocalSlmRuntime,
)
from slm_math_evaluator_v2 import compare_math_expressions, infer_goal_kind_from_text  # noqa: E402


V8_MANIFEST_PATH = RUNS_DIR / "independent-validation-local-ai-production-readiness/PERMISSIBLE_UNSEEN_CORPUS_MANIFEST.json"
V7_HOLDOUT_PATH = RUNS_DIR / "deterministic-geometry-language-closure-slm-finetuning/SLM_V7_HOLDOUT_MANIFEST.json"
V6_HOLDOUT_PATH = RUNS_DIR / "specialized-geometry-extraction-slm-optimization/SLM_NEW_HOLDOUT_MANIFEST.json"


def _check_ans(answers: dict[str, Any], oracles: list[str], orig_text: str) -> tuple[bool, bool, bool]:
    ans_vals = [str(v) for v in (answers or {}).values()]
    if not oracles:
        return True, True, False
    if not ans_vals:
        return False, False, False
    clean_gk = re.sub(r"\bvuông\s+góc\b", "vuong_goc", orig_text, flags=re.IGNORECASE)
    gk = infer_goal_kind_from_text(clean_gk) if len(oracles) == 1 else None
    matched = sum(1 for ora in oracles if any(compare_math_expressions(a, ora, goal_kind=gk).matched is True for a in ans_vals))
    any_wrong = any(not any(compare_math_expressions(a, ora, goal_kind=gk).matched is True for ora in oracles) for a in ans_vals)
    return matched >= 1 and not any_wrong, matched == len(oracles) and not any_wrong, any_wrong


def _load_residual_holdouts() -> list[dict[str, Any]]:
    targets = {"v7h_p8_01", "v7h_p8_02", "v7h_p8_03", "v7h_p8_04", "v7h_p8_05", "v7h_p5_09", "slm_h23"}
    found: list[dict[str, Any]] = []
    for path in (V7_HOLDOUT_PATH, V6_HOLDOUT_PATH):
        if not path.exists():
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        items = raw.get("cases") or raw.get("items") or (raw if isinstance(raw, list) else [])
        for it in items:
            cid = str(it.get("case_id") or it.get("id") or "")
            if cid in targets:
                found.append(it)
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate C60 + /7 residual holdouts with v9/v3 closure.")
    parser.add_argument("--model", choices=("v7", "v9"), default="v7", help="Local SLM model to evaluate.")
    args = parser.parse_args(argv)
    model_key = V9_LOCAL_SLM_MODEL_KEY if args.model == "v9" else FINETUNED_LOCAL_SLM_MODEL_KEY
    out_filename = "C60_POST_P3_V9_RESULTS.json" if args.model == "v9" else "C60_POST_P2_V9_RESULTS.json"
    schema_name = "c60-post-p3-v9-results/1" if args.model == "v9" else "c60-post-p2-v9-results/1"

    manifest = json.loads(V8_MANIFEST_PATH.read_text(encoding="utf-8"))
    c60_cases = [c for c in manifest["cases"] if c["corpus"] == "C60_BLIND_NLU"]
    p1_doc = {r["orig_id"]: r for r in json.loads((OUT_DIR / "C60_CASE_LEVEL_ROOT_CAUSE.json").read_text(encoding="utf-8"))["cases"]}
    res_cases = _load_residual_holdouts()

    rt = LocalSlmRuntime()
    c60_out: list[dict[str, Any]] = []
    res_out: list[dict[str, Any]] = []
    try:
        for idx, c in enumerate(c60_cases, 1):
            clear_local_geometry_parser_cache()
            oid = c["orig_id"]
            txt = c["text"]
            oracles = c["oracles"]
            t0 = time.perf_counter()
            out = AIR.route_text_input_local_slm(
                txt,
                model_key=model_key,
                strategy="compact_clause",
                runtime=rt,
                allow_download=False,
                use_verified_normalizer=True,
                closure_mode=V9_CLOSURE_MODE,
                normalizer_version="v3",
                use_cache=False,
                cache_prompt=True,
            )
            wall_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            rd = (out.response or {}).get("route_d") or {}
            st = str(rd.get("status") or "REFUSED")
            ref = rd.get("refusal") or {}
            rc = ref.get("code") or ref.get("reason_code")
            ans = rd.get("answers") or {}
            env = rd.get("slm_grounding_envelope") or {}
            ext_mode = rd.get("extraction_mode")
            ok_any, ok_strict, wrong = (
                _check_ans(ans, oracles, txt) if st == "SERVED" and c["eval_role"] == "VERIFIED_POSITIVE" else (False, False, st == "SERVED")
            )
            arm_b_canon_ok = bool(p1_doc[oid]["gold_intervention_outcome"]["arm_b_gold_v2_canon"]["ok_strict"])
            c60_out.append({
                "orig_id": oid,
                "eval_role": c["eval_role"],
                "extraction_mode": ext_mode,
                "slm_invoked": bool(env.get("slm_invoked")),
                "status": st,
                "reason_code": rc,
                "answers": ans,
                "ok_any": ok_any,
                "ok_strict": ok_strict,
                "wrong_served": wrong,
                "arm_b_canon_ok": arm_b_canon_ok,
                "wall_ms": wall_ms,
                "grounding_status": env.get("grounding_status"),
            })
            print(f"[C60 {idx:02d}/60] {oid} | mode={ext_mode} | slm={bool(env.get('slm_invoked'))} | {st}:{rc} | ok={ok_strict} wrong={wrong} | B_can={arm_b_canon_ok}", flush=True)

        for it in res_cases:
            clear_local_geometry_parser_cache()
            cid = str(it.get("case_id") or it.get("id"))
            txt = it.get("text") or it.get("problem_text") or ""
            raw_ora = it.get("expected_answers") or it.get("oracles") or (
                [it["oracle"]] if it.get("oracle") else ([it["expected_answer"]] if it.get("expected_answer") else [])
            )
            exp = [str(x) for x in raw_ora]
            kind = str(it.get("kind") or "").lower()
            exp_status = str(it.get("expected_status") or it.get("expected_route_status") or ("SERVED" if kind in ("positive", "") else "REFUSED"))
            out = AIR.route_text_input_local_slm(
                txt,
                model_key=model_key,
                strategy="compact_clause",
                runtime=rt,
                allow_download=False,
                use_verified_normalizer=True,
                closure_mode=V9_CLOSURE_MODE,
                normalizer_version="v3",
                use_cache=False,
                cache_prompt=True,
            )
            rd = (out.response or {}).get("route_d") or {}
            st = str(rd.get("status") or "REFUSED")
            ref = rd.get("refusal") or {}
            rc = ref.get("code") or ref.get("reason_code")
            ans = rd.get("answers") or {}
            env = rd.get("slm_grounding_envelope") or {}
            if exp_status == "SERVED" and exp:
                ok_any, ok_strict, wrong = _check_ans(ans, [str(x) for x in exp], txt) if st == "SERVED" else (False, False, False)
            else:
                ok_any, ok_strict, wrong = (st != "SERVED"), (st != "SERVED"), (st == "SERVED")
            res_out.append({
                "case_id": cid,
                "expected_status": exp_status,
                "extraction_mode": rd.get("extraction_mode"),
                "slm_invoked": bool(env.get("slm_invoked")),
                "status": st,
                "reason_code": rc,
                "answers": ans,
                "ok_strict": ok_strict,
                "wrong_served": wrong,
                "grounding_status": env.get("grounding_status"),
            })
            print(f"[RES {cid}] mode={rd.get('extraction_mode')} slm={bool(env.get('slm_invoked'))} {st}:{rc} ok={ok_strict} wrong={wrong}", flush=True)
    finally:
        rt.shutdown()

    vp = [r for r in c60_out if r["eval_role"] == "VERIFIED_POSITIVE"]
    solvable_misses = [r for r in vp if r["arm_b_canon_ok"] and not r["ok_strict"]]
    solvable_slm_misses = [r for r in solvable_misses if r["slm_invoked"]]
    fast_served = [r for r in vp if not r["slm_invoked"] and r["ok_strict"]]
    slm_served = [r for r in vp if r["slm_invoked"] and r["ok_strict"]]
    res_solvable_slm_misses = [r for r in res_out if r["expected_status"] == "SERVED" and not r["ok_strict"] and r["slm_invoked"]]

    summary = {
        "schema": schema_name,
        "model_key": model_key,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "external_ai_calls": 0,
        "c60_positives_total": len(vp),
        "c60_served_exact_strict_all": sum(1 for r in vp if r["ok_strict"]),
        "c60_fast_path_served": len(fast_served),
        "c60_slm_served": len(slm_served),
        "c60_wrong_served_total": sum(1 for r in c60_out if r["wrong_served"]),
        "c60_solvable_by_arm_b_canon_total": sum(1 for r in vp if r["arm_b_canon_ok"]),
        "c60_remaining_solvable_misses": [r["orig_id"] for r in solvable_misses],
        "c60_remaining_solvable_slm_misses": [r["orig_id"] for r in solvable_slm_misses],
        "residual_holdout_checked": len(res_out),
        "residual_holdout_served": sum(1 for r in res_out if r["ok_strict"]),
        "residual_holdout_wrong_served": sum(1 for r in res_out if r["wrong_served"]),
        "residual_holdout_slm_misses": [r["case_id"] for r in res_solvable_slm_misses],
        "total_genuine_slm_misses_solvable_downstream": len(solvable_slm_misses) + len(res_solvable_slm_misses),
        "c60_cases": c60_out,
        "residual_cases": res_out,
    }
    (OUT_DIR / out_filename).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n=== POST-{args.model.upper()} SUMMARY ===", json.dumps({k: v for k, v in summary.items() if k not in ("c60_cases", "residual_cases")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
