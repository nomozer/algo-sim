"""Evaluate quantized Q4_K_M models (fine-tuned v7 vs original base) on val.jsonl via LocalSlmRuntime."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import sys
import time
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import benchmark_slm_v6_campaign as BV6  # noqa: E402
import build_slm_training_dataset as DATA_MOD  # noqa: E402
from app.ai.adaptive_input_router import route_text_input_local_slm  # noqa: E402
from app.ai.hybrid_offline import ReplayExtractor, hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.local_geometry_parser import clear_local_geometry_parser_cache  # noqa: E402
from app.ai.local_slm_extractor import run_local_slm_extraction  # noqa: E402
from app.ai.local_slm_runtime import (  # noqa: E402
    DEFAULT_LOCAL_SLM_MODEL_KEY,
    FINETUNED_LOCAL_SLM_MODEL_KEY,
    LocalSlmRuntime,
)

ESC = BV6.ESC
VAL_JSONL = Path(r"C:\Users\Bunny\AppData\Local\axo-slm\training\datasets\val.jsonl")
OUT_DIR = REPO_ROOT / "docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning"


def _eval_gguf_on_val(model_key: str, val_rows: list[dict[str, Any]], *, threads: int = 6) -> dict[str, Any]:
    rt = LocalSlmRuntime(threads=threads, allow_download=False)
    pol = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})

    raw_pos_ok = 0
    raw_neg_ref = 0
    raw_wrong = 0
    routed_pos_ok = 0
    routed_neg_ref = 0
    routed_wrong = 0
    pos_total = 0
    neg_total = 0
    lat_ms: list[float] = []
    per_sample: list[dict[str, Any]] = []

    try:
        for idx, row in enumerate(val_rows):
            txt = row["source_text"]
            canon_txt = row["canonical_text"]
            kind = row["kind"]
            exp_str = (row.get("validation_evidence") or {}).get("exact_oracle_decimal_at_a1")

            # 1. Direct SLM extraction on canonical text (matches PyTorch SFT / Merged HF val eval directly)
            ext = run_local_slm_extraction(
                canon_txt,
                runtime=rt,
                model_key=model_key,
                use_verified_normalizer=True,
                closure_mode="v7",
                normalizer_version="v2",
                use_cache=False,
            )
            ext_served = False
            ext_exact = False
            if ext.ok and ext.canonical_payload is not None:
                ho = run_hybrid_offline(canon_txt, ReplayExtractor({canon_txt: ext.canonical_payload}), policy=pol)
                rd = ho.response.get("route_d") or {}
                ext_served = rd.get("status") == "SERVED"
                ans_str = ESC._extract_answer_str(ho.response) if ext_served else None
                if ext_served and ans_str is not None and exp_str:
                    ext_exact = abs(DATA_MOD._qty_str_to_dec(ans_str) - Decimal(exp_str)) < Decimal("1e-7")
                elif ext_served:
                    ext_exact = True

            # 2. Full production routed pipeline (`route_text_input_local_slm` from raw text)
            clear_local_geometry_parser_cache()
            t0 = time.perf_counter()
            res = route_text_input_local_slm(
                txt,
                runtime=rt,
                model_key=model_key,
                use_verified_normalizer=True,
                closure_mode="v7",
                normalizer_version="v2",
                threads=threads,
                use_cache=False,
            )
            lat_ms.append(round((time.perf_counter() - t0) * 1000.0, 2))
            routed_served = res.status == "SERVED"
            routed_exact = False
            if routed_served:
                ans_r = ESC._extract_answer_str(res.response)
                if ans_r is not None and exp_str:
                    routed_exact = abs(DATA_MOD._qty_str_to_dec(ans_r) - Decimal(exp_str)) < Decimal("1e-7")
                elif kind == "positive":
                    routed_exact = True
            routed_reason = ((res.response.get("route_d") or {}).get("refusal") or {}).get("code") or res.telemetry.fallback_reason

            if kind == "positive":
                pos_total += 1
                if ext_exact:
                    raw_pos_ok += 1
                elif ext_served:
                    raw_wrong += 1
                if routed_exact:
                    routed_pos_ok += 1
                elif routed_served:
                    routed_wrong += 1
            else:
                neg_total += 1
                if not ext_served:
                    raw_neg_ref += 1
                else:
                    raw_wrong += 1
                if not routed_served:
                    routed_neg_ref += 1
                else:
                    routed_wrong += 1

            per_sample.append({
                "sample_id": row["sample_id"],
                "kind": kind,
                "direct_slm_served": ext_served,
                "direct_slm_exact": ext_exact,
                "direct_slm_reason": ext.reason_code,
                "routed_status": res.status,
                "routed_exact": routed_exact,
                "routed_reason": routed_reason,
                "latency_ms": lat_ms[-1],
            })
            if (idx + 1) % 23 == 0 or (idx + 1) == len(val_rows):
                print(
                    f"  [GGUF {model_key}] {idx+1}/{len(val_rows)} "
                    f"direct_pos={raw_pos_ok}/{pos_total} routed_pos={routed_pos_ok}/{pos_total} neg_ref={routed_neg_ref}/{neg_total}",
                    flush=True,
                )
    finally:
        rt.shutdown()

    lat_sorted = sorted(lat_ms)
    return {
        "model_key": model_key,
        "threads": threads,
        "total": len(val_rows),
        "positives_total": pos_total,
        "negatives_total": neg_total,
        "direct_slm_only": {
            "positives_oracle_exact": raw_pos_ok,
            "positive_exact_rate": round(raw_pos_ok / max(1, pos_total), 4),
            "negatives_safe_refused": raw_neg_ref,
            "negative_refusal_rate": round(raw_neg_ref / max(1, neg_total), 4),
            "overall_correct": raw_pos_ok + raw_neg_ref,
            "overall_accuracy": round((raw_pos_ok + raw_neg_ref) / max(1, len(val_rows)), 4),
            "wrong_served_count": raw_wrong,
        },
        "full_v7_routed": {
            "positives_oracle_exact": routed_pos_ok,
            "positive_exact_rate": round(routed_pos_ok / max(1, pos_total), 4),
            "negatives_safe_refused": routed_neg_ref,
            "negative_refusal_rate": round(routed_neg_ref / max(1, neg_total), 4),
            "overall_correct": routed_pos_ok + routed_neg_ref,
            "overall_accuracy": round((routed_pos_ok + routed_neg_ref) / max(1, len(val_rows)), 4),
            "wrong_served_count": routed_wrong,
        },
        "median_routed_ms": lat_sorted[len(lat_sorted) // 2] if lat_sorted else 0.0,
        "samples": per_sample,
    }


def main() -> int:
    val_rows = [json.loads(ln) for ln in VAL_JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
    train_run = json.loads((OUT_DIR / "SLM_TRAINING_RUN.json").read_text(encoding="utf-8"))
    stage = json.loads(Path(r"C:\Users\Bunny\AppData\Local\axo-slm\merged_hf\SLM_QUANTIZATION_MERGE_STAGE.json").read_text(encoding="utf-8"))

    sel_ep = train_run["selected_epoch"]
    ep_entry = next(e for e in train_run["epoch_history"] if e["epoch"] == sel_ep)

    print("[P5 EVAL] Evaluating quantized fine-tuned GGUF on val.jsonl via LocalSlmRuntime...", flush=True)
    ft_gguf = _eval_gguf_on_val(FINETUNED_LOCAL_SLM_MODEL_KEY, val_rows, threads=6)
    print("[P5 EVAL] Evaluating original un-tuned Qwen3-0.6B GGUF on val.jsonl via LocalSlmRuntime...", flush=True)
    orig_gguf = _eval_gguf_on_val(DEFAULT_LOCAL_SLM_MODEL_KEY, val_rows, threads=6)

    lora_pos_rate = ep_entry["val_metrics"]["positive_served_exact_rate"]
    merged_pos_rate = stage["merged_hf_fp16"]["val_metrics"]["positive_served_exact_rate"]
    gguf_direct_pos_rate = ft_gguf["direct_slm_only"]["positive_exact_rate"]

    out = {
        "schema": "slm-quantization-evaluation/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "external_ai_calls": 0,
        "val_split": {"path": str(VAL_JSONL), "total": len(val_rows), "holdouts_touched": False},
        "artifacts": {
            "f16_gguf": stage["f16_gguf"],
            "q4_k_m_gguf": stage["q4_k_m_gguf"],
            "original_q4_k_m_sha256_verified": stage["original_q4_k_m_sha256_verified"],
        },
        "stages": {
            "1_pytorch_base_plus_best_lora": {
                "selected_epoch": sel_ep,
                "val_metrics": ep_entry["val_metrics"],
            },
            "2_standalone_merged_hf_fp16": {
                "val_metrics": stage["merged_hf_fp16"]["val_metrics"],
            },
            "3_quantized_q4_k_m_finetuned_runtime": {k: v for k, v in ft_gguf.items() if k != "samples"},
            "4_quantized_q4_k_m_original_runtime": {k: v for k, v in orig_gguf.items() if k != "samples"},
        },
        "parity_summary": {
            "merge_delta_pp": round((merged_pos_rate - lora_pos_rate) * 100.0, 2),
            "quantization_delta_vs_merged_pp": round((gguf_direct_pos_rate - merged_pos_rate) * 100.0, 2),
            "quantization_delta_vs_lora_pp": round((gguf_direct_pos_rate - lora_pos_rate) * 100.0, 2),
            "finetuned_vs_original_direct_pp": round(
                (gguf_direct_pos_rate - orig_gguf["direct_slm_only"]["positive_exact_rate"]) * 100.0, 2
            ),
            "finetuned_vs_original_routed_pp": round(
                (ft_gguf["full_v7_routed"]["positive_exact_rate"] - orig_gguf["full_v7_routed"]["positive_exact_rate"]) * 100.0, 2
            ),
            "all_stages_zero_wrong_served": (
                ep_entry["val_metrics"]["wrong_served_count"] == 0
                and stage["merged_hf_fp16"]["val_metrics"]["wrong_served_count"] == 0
                and ft_gguf["direct_slm_only"]["wrong_served_count"] == 0
                and ft_gguf["full_v7_routed"]["wrong_served_count"] == 0
                and orig_gguf["full_v7_routed"]["wrong_served_count"] == 0
            ),
        },
        "per_sample_gguf_comparison": {
            "finetuned": ft_gguf["samples"],
            "original": orig_gguf["samples"],
        },
    }
    out_path = OUT_DIR / "SLM_QUANTIZATION_EVALUATION.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[P5 EVAL DONE] Wrote {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
