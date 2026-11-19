# -*- coding: utf-8 -*-
"""AXO HYBRID /9 — Exact Multi-Goal Scorer for `val_v9.jsonl` Predictions."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("HYBRID_ROUTE_MODE", None)

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(REPO_ROOT / "backend/scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend/scripts"))

from app.ai.hybrid_offline import ReplayExtractor, hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.local_slm_extractor import (  # noqa: E402
    V9_CLOSURE_MODE,
    build_compact_clause_context,
    validate_and_lower_compact_clause,
)
from slm_math_evaluator_v2 import compare_math_expressions, infer_goal_kind_from_text  # noqa: E402


def _strip_json_reply(raw: str) -> str:
    s = str(raw or "").strip()
    if "<think>" in s and "</think>" in s:
        s = s.split("</think>", 1)[-1].strip()
    if s.startswith("```"):
        lines = [ln for ln in s.splitlines() if not ln.strip().startswith("```")]
        s = "\n".join(lines).strip()
    first = s.find("{")
    last = s.rfind("}")
    if first != -1 and last != -1 and last > first:
        return s[first:last + 1]
    return s


def score_predictions(val_path: Path, preds_path: Path) -> dict[str, Any]:
    val_rows = [json.loads(ln) for ln in val_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    preds_map: dict[str, str] = json.loads(preds_path.read_text(encoding="utf-8"))
    pol = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})

    json_valid = 0
    grounded_ok = 0
    pos_total = 0
    pos_served = 0
    pos_oracle_match = 0
    neg_total = 0
    neg_refused = 0
    wrong_served = 0
    per_family: dict[str, dict[str, int]] = {}
    sample_results: list[dict[str, Any]] = []

    for row in val_rows:
        sid = row["sample_id"]
        fam = row["problem_family_id"]
        kind = row["kind"]
        canon_txt = row["canonical_text"]
        oracles = [str(x) for x in (row.get("gold_oracles") or ())]
        raw_out = _strip_json_reply(preds_map.get(sid, ""))
        fam_rec = per_family.setdefault(fam, {"total": 0, "json_valid": 0, "grounded": 0, "correct": 0, "wrong_served": 0})
        fam_rec["total"] += 1

        parsed: dict[str, Any] | None = None
        try:
            obj = json.loads(raw_out)
            if isinstance(obj, dict):
                parsed = obj
                json_valid += 1
                fam_rec["json_valid"] += 1
        except Exception:
            parsed = None

        ctx = build_compact_clause_context(canon_txt)
        lowered: dict[str, Any] | None = None
        grounding_status = "INVALID_JSON"
        rejected_ops: list[Any] = []
        if parsed is not None:
            try:
                lowered, diag = validate_and_lower_compact_clause(ctx=ctx, raw_slm_json=parsed, closure_mode=V9_CLOSURE_MODE)
                grounding_status = str(diag.get("grounding_status") or "")
                rejected_ops = list(diag.get("rejected_ops") or [])
            except Exception as exc:
                grounding_status = f"VALIDATOR_ERR:{type(exc).__name__}"

        if kind == "positive":
            pos_total += 1
            served = False
            oracle_ok = False
            ans_vals: list[str] = []
            refusal_code = None
            if lowered is not None and not rejected_ops:
                grounded_ok += 1
                fam_rec["grounded"] += 1
                ho = run_hybrid_offline(canon_txt, ReplayExtractor({canon_txt: lowered}), policy=pol)
                rd = ho.response.get("route_d") or {}
                served = rd.get("status") == "SERVED"
                refusal_code = (rd.get("refusal") or {}).get("code")
                ans_vals = [str(v) for v in (rd.get("answers") or {}).values()] if served else []
                if served:
                    pos_served += 1
                    clean_gk = re.sub(r"\bvuông\s+góc\b", "vuong_goc", canon_txt, flags=re.IGNORECASE)
                    gk = infer_goal_kind_from_text(clean_gk) if len(oracles) == 1 else None
                    matched = sum(1 for ora in oracles if any(compare_math_expressions(a, ora, goal_kind=gk).matched is True for a in ans_vals))
                    any_bad = any(not any(compare_math_expressions(a, ora, goal_kind=gk).matched is True for ora in oracles) for a in ans_vals)
                    if oracles and matched == len(oracles) and not any_bad:
                        oracle_ok = True
                        pos_oracle_match += 1
                        fam_rec["correct"] += 1
                    elif not oracles:
                        oracle_ok = True
                        pos_oracle_match += 1
                        fam_rec["correct"] += 1
                    else:
                        wrong_served += 1
                        fam_rec["wrong_served"] += 1
            sample_results.append({
                "sample_id": sid,
                "family": fam,
                "kind": kind,
                "grounding_status": grounding_status,
                "served": served,
                "oracle_ok": oracle_ok,
                "answers": ans_vals,
                "refusal_code": refusal_code,
            })
        else:
            neg_total += 1
            refused = True
            ans_vals = []
            if lowered is not None and not rejected_ops:
                ho = run_hybrid_offline(canon_txt, ReplayExtractor({canon_txt: lowered}), policy=pol)
                rd = ho.response.get("route_d") or {}
                if rd.get("status") == "SERVED":
                    refused = False
                    wrong_served += 1
                    fam_rec["wrong_served"] += 1
                    ans_vals = [str(v) for v in (rd.get("answers") or {}).values()]
            if refused:
                neg_refused += 1
                fam_rec["correct"] += 1
            sample_results.append({
                "sample_id": sid,
                "family": fam,
                "kind": kind,
                "grounding_status": grounding_status,
                "refused": refused,
                "answers": ans_vals,
            })

    total = len(val_rows)
    return {
        "schema": "slm-v9-val-score/1",
        "total": total,
        "json_valid": json_valid,
        "json_valid_rate": round(json_valid / max(1, total), 4),
        "positives_total": pos_total,
        "positives_grounded": grounded_ok,
        "positives_served": pos_served,
        "positives_oracle_exact": pos_oracle_match,
        "positive_served_exact_rate": round(pos_oracle_match / max(1, pos_total), 4),
        "negatives_total": neg_total,
        "negatives_safe_refused": neg_refused,
        "negative_safe_refusal_rate": round(neg_refused / max(1, neg_total), 4),
        "wrong_served_count": wrong_served,
        "overall_correct": pos_oracle_match + neg_refused,
        "overall_accuracy_rate": round((pos_oracle_match + neg_refused) / max(1, total), 4),
        "per_family": per_family,
        "sample_results": sample_results,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--val-jsonl", required=True)
    ap.add_argument("--preds-json", required=True)
    ap.add_argument("--out-json", required=True)
    args = ap.parse_args(argv)
    res = score_predictions(Path(args.val_jsonl), Path(args.preds_json))
    Path(args.out_json).write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"[SCORE V9] total={res['total']} json_valid={res['json_valid']} "
        f"pos_exact={res['positives_oracle_exact']}/{res['positives_total']} ({res['positive_served_exact_rate']*100:.2f}%) "
        f"neg_refused={res['negatives_safe_refused']}/{res['negatives_total']} wrong_served={res['wrong_served_count']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
