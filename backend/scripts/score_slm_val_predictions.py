"""Score raw SLM compact_clause JSON predictions on val.jsonl using production validator + Exact Kernel."""

from __future__ import annotations

import argparse
from decimal import Decimal
import json
import os
from pathlib import Path
import sys
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ai.hybrid_offline import ReplayExtractor, hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.local_slm_extractor import (  # noqa: E402
    build_compact_clause_context,
    validate_and_lower_compact_clause,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_slm_v6_campaign as BV6  # noqa: E402
import build_slm_training_dataset as DATA_MOD  # noqa: E402

ESC = BV6.ESC


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
    val_rows = [json.loads(line) for line in val_path.read_text(encoding="utf-8").splitlines() if line.strip()]
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
                lowered, diag = validate_and_lower_compact_clause(ctx=ctx, raw_slm_json=parsed, closure_mode="v7")
                grounding_status = str(diag.get("grounding_status") or "")
                rejected_ops = list(diag.get("rejected_ops") or [])
            except Exception as exc:
                grounding_status = f"VALIDATOR_ERR:{type(exc).__name__}"

        if kind == "positive":
            pos_total += 1
            served = False
            oracle_ok = False
            ans_str = None
            refusal_code = None
            if lowered is not None and not rejected_ops:
                grounded_ok += 1
                fam_rec["grounded"] += 1
                ho = run_hybrid_offline(canon_txt, ReplayExtractor({canon_txt: lowered}), policy=pol)
                rd = ho.response.get("route_d") or {}
                served = rd.get("status") == "SERVED"
                refusal_code = (rd.get("refusal") or {}).get("code")
                ans_str = ESC._extract_answer_str(ho.response) if served else None
                exp_str = (row.get("validation_evidence") or {}).get("exact_oracle_decimal_at_a1")
                if served and ans_str is not None:
                    pos_served += 1
                    if exp_str:
                        ans_dec = DATA_MOD._qty_str_to_dec(ans_str)
                        exp_dec = Decimal(exp_str)
                        if abs(ans_dec - exp_dec) < Decimal("1e-7"):
                            oracle_ok = True
                            pos_oracle_match += 1
                            fam_rec["correct"] += 1
                        else:
                            wrong_served += 1
                            fam_rec["wrong_served"] += 1
                    else:
                        oracle_ok = True
                        pos_oracle_match += 1
                        fam_rec["correct"] += 1
            sample_results.append({
                "sample_id": sid,
                "family": fam,
                "kind": kind,
                "json_valid": parsed is not None,
                "grounding_status": grounding_status,
                "rejected_ops": rejected_ops,
                "served": served,
                "oracle_match": oracle_ok,
                "answer": ans_str,
                "refusal_code": refusal_code,
            })
        else:
            neg_total += 1
            served = False
            if lowered is not None:
                ho = run_hybrid_offline(canon_txt, ReplayExtractor({canon_txt: lowered}), policy=pol)
                rd = ho.response.get("route_d") or {}
                served = rd.get("status") == "SERVED"
            else:
                # Negative safely rejected/unresolved by validator -> SAFE_REFUSED
                if parsed is not None:
                    grounded_ok += 1
                    fam_rec["grounded"] += 1
            if not served:
                neg_refused += 1
                fam_rec["correct"] += 1
            else:
                wrong_served += 1
                fam_rec["wrong_served"] += 1
            sample_results.append({
                "sample_id": sid,
                "family": fam,
                "kind": kind,
                "json_valid": parsed is not None,
                "grounding_status": grounding_status,
                "rejected_ops": rejected_ops,
                "served": served,
            })

    total = len(val_rows)
    return {
        "total": total,
        "json_valid": json_valid,
        "json_valid_rate": round(json_valid / max(1, total), 4),
        "grounded_ok": grounded_ok,
        "grounded_rate": round(grounded_ok / max(1, total), 4),
        "positives_total": pos_total,
        "positives_served": pos_served,
        "positives_oracle_exact": pos_oracle_match,
        "positive_served_exact_rate": round(pos_oracle_match / max(1, pos_total), 4),
        "negatives_total": neg_total,
        "negatives_safe_refused": neg_refused,
        "negative_safe_refusal_rate": round(neg_refused / max(1, neg_total), 4),
        "overall_correct": pos_oracle_match + neg_refused,
        "overall_accuracy": round((pos_oracle_match + neg_refused) / max(1, total), 4),
        "wrong_served_count": wrong_served,
        "per_family": per_family,
        "samples": sample_results,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--val-jsonl", required=True)
    ap.add_argument("--preds-json", required=True)
    ap.add_argument("--out-json", required=True)
    args = ap.parse_args(argv)
    report = score_predictions(Path(args.val_jsonl), Path(args.preds_json))
    Path(args.out_json).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"[SCORE] valid={report['json_valid']}/{report['total']} "
        f"pos_exact={report['positives_oracle_exact']}/{report['positives_total']} "
        f"neg_refused={report['negatives_safe_refused']}/{report['negatives_total']} "
        f"wrong_served={report['wrong_served_count']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
