# -*- coding: utf-8 -*-
"""AXO HYBRID /8 Phase C / P3: Anti-Leakage Freeze & Single-Shot Evaluation on Permissible Unseen Repo Corpora.

NOTE ON EXTERNAL CORPUS GOVERNANCE:
`INDEPENDENT_EXTERNAL_CORPUS = BLOCKED_DATA_ACCESS` for a fresh 100-150 external student/teacher
field dataset. This script evaluates the FROZEN `/7` candidate (`113a6a7cf6bbc15a...`) and
frozen `Qwen3-0.6B-AxoV7` + `axo-math-evaluator/2` in a single frozen pass (`external_ai_calls = 0`)
on permissible, non-sealed repository corpora verified disjoint from ALL `/5-/7` SLM training,
calibration, and checkpoint-selection sets:
  - `C60_BLIND_NLU` (60 cases from `independent-nlu-extraction-evaluation`, agent-authored blind
    before `/5` without repo access; 42 verified math-oracle positives + 13 negative/refusal + 5 UI/construct)
  - `EXTERNAL17_REAL_TRANSCRIPTIONS` (17 exam/homework sub-questions from `formal-correctness-real-world-acceptance`:
    12 verified closed-form positives + 5 OOS/diagram-dependent)
Also records an offline 0-cloud-call diagnostic across `{k1, r1, s2}` (`70` cases) vs historical Gemini logs
for Phase F (`P6`) without claiming head-to-head parity.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
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
OUT_DIR = RUNS_DIR / "independent-validation-local-ai-production-readiness"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DATASET_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "axo-slm/training/datasets"

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


V6 = _load_mod("_v6_bench_p3", BACKEND / "scripts/benchmark_slm_v6_campaign.py")
os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""

from app.ai import adaptive_input_router as AIR  # noqa: E402
from app.ai.local_geometry_parser import clear_local_geometry_parser_cache, normalize_problem_text, parse_geometry_problem_locally  # noqa: E402
from app.ai.local_slm_extractor import (  # noqa: E402
    LOCAL_SLM_EXTRACTOR_VERSION,
    SLM_COMPACT_SCHEMA_VERSION,
    SLM_GROUNDING_VALIDATOR_VERSION,
    run_local_slm_extraction,
)
from app.ai.local_slm_runtime import (  # noqa: E402
    DEFAULT_LOCAL_SLM_MODEL_KEY,
    FINETUNED_LOCAL_SLM_MODEL_KEY,
    LOCAL_SLM_RUNTIME_VERSION,
    LocalSlmRuntime,
)
from app.ai.slm_verified_normalizer import SLM_VERIFIED_NORMALIZER_VERSION, normalize_for_slm_grounding  # noqa: E402
from freeze_evaluation_candidate import measured_system_hash  # noqa: E402
from slm_math_evaluator_v2 import EVALUATOR_VERSION, compare_math_expressions, infer_goal_kind_from_text  # noqa: E402


def _lf_sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def _norm_txt(s: str) -> str:
    return re.sub(r"\s+", " ", normalize_problem_text(s or "")).strip().lower()


def _ngrams4(s: str) -> set[tuple[str, ...]]:
    toks = re.findall(r"\w+", _norm_txt(s))
    return set(zip(toks, toks[1:], toks[2:], toks[3:])) if len(toks) >= 4 else set()


def _wilson_ci95(k: int, n: int) -> list[float]:
    if n <= 0:
        return [0.0, 0.0]
    z = 1.959963984540054
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * n)) / n) / denom
    return [round(max(0.0, center - half), 4), round(min(1.0, center + half), 4)]


def _cohen_h(p1: float, p2: float) -> float:
    return round(2.0 * (math.asin(math.sqrt(max(0.0, min(1.0, p2)))) - math.asin(math.sqrt(max(0.0, min(1.0, p1))))), 4)


def _mcnemar_exact(b01: int, b10: int) -> float:
    n = b01 + b10
    if n == 0:
        return 1.0
    k = min(b01, b10)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return round(min(1.0, 2.0 * tail), 6)


def _extract_c60_oracles(exp_vals: dict[str, Any] | None) -> list[str]:
    out: list[str] = []
    if not exp_vals:
        return out
    for rid in sorted(exp_vals.keys()):
        val = exp_vals[rid]
        if isinstance(val, dict):
            if val.get("cos_squared"):
                out.append(f"cos²={val['cos_squared']}")
            elif val.get("exact") is not None:
                out.append(str(val["exact"]))
            elif val.get("value") is not None:
                out.append(str(val["value"]))
        elif val is not None:
            out.append(str(val))
    return out


# ── C60 Gold Facts <-> TypedFactNext V2 Layer Comparator ─────────────────────

def _norm_lbl(x: str) -> str:
    return x.replace("′", "'").replace("’", "'").strip()


def _canon_num_str(q: Any) -> str:
    s = str(q or "").strip().replace(" ", "")
    return s


def _gold_v1_to_layers(gf_entry: dict[str, Any]) -> dict[str, Any]:
    """Translate C60 V1 gold_facts entry into comparable `(pred, arg_key, qty)` sets & entity set."""
    facts = gf_entry.get("facts") or []
    entities: set[str] = set()
    pred_list: list[str] = []
    arg_list: list[tuple[str, tuple[str, ...]]] = []
    qty_list: list[tuple[str, tuple[str, ...], str]] = []
    solids_count = 0

    for f in facts:
        k = f.get("kind")
        if k == "solid":
            solids_count += 1
            notn = _norm_lbl(f.get("solid", ""))
            for m in re.findall(r"[A-Z][0-9']*[']?", notn):
                entities.add(m)
            pred_list.append(f"solid:{f.get('solid_type')}")
            arg_list.append((f"solid:{f.get('solid_type')}", (notn,)))
        elif k == "polygon_shape":
            pts = tuple(sorted(_norm_lbl(p) for p in f.get("points", [])))
            entities.update(pts)
            sh = f.get("shape", "")
            pk = "regular_polygon" if sh in ("square", "equilateral_triangle", "regular_hexagon") else sh
            pred_list.append(pk)
            arg_list.append((pk, pts))
            if f.get("value"):
                qty_list.append((pk, pts, _canon_num_str(f["value"])))
        elif k == "right_angle":
            at = _norm_lbl(f.get("at", ""))
            rays = tuple(sorted(_norm_lbl(p) for p in f.get("points", [])))
            entities.add(at)
            entities.update(rays)
            pred_list.append("right_angle")
            arg_list.append(("right_angle", (at, *rays)))
        elif k == "perpendicular":
            pa = tuple(sorted(_norm_lbl(p) for p in f.get("points_a", [])))
            pb = tuple(sorted(_norm_lbl(p) for p in f.get("points_b", [])))
            entities.update(pa)
            entities.update(pb)
            pk = "perpendicular_line_plane" if len(pa) == 2 and len(pb) >= 3 else "perpendicular"
            pred_list.append(pk)
            arg_list.append((pk, pa + pb))
        elif k == "length":
            pts = tuple(sorted(_norm_lbl(p) for p in f.get("points", [])))
            entities.update(pts)
            pred_list.append("segment_length")
            arg_list.append(("segment_length", pts))
            if f.get("value"):
                qty_list.append(("segment_length", pts, _canon_num_str(f["value"])))
        elif k in ("point_def", "projection"):
            if f.get("point"):
                entities.add(_norm_lbl(f["point"]))
            for p_field in ("points", "target", "on"):
                val = f.get(p_field)
                if isinstance(val, list):
                    entities.update(_norm_lbl(x) for x in val)
                elif isinstance(val, str):
                    entities.add(_norm_lbl(val))
            pk = "midpoint" if f.get("role_name") == "midpoint" or "trung điểm" in str(f.get("quotes", "")) else k
            pred_list.append(pk)
    return {
        "entities": entities,
        "predicates": Counter(pred_list),
        "arg_bindings": Counter(arg_list),
        "qty_bindings": Counter(qty_list),
    }


def _v2_payload_to_layers(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"entities": set(), "predicates": Counter(), "arg_bindings": Counter(), "qty_bindings": Counter()}
    entities: set[str] = set()
    pred_list: list[str] = []
    arg_list: list[tuple[str, tuple[str, ...]]] = []
    qty_list: list[tuple[str, tuple[str, ...], str]] = []

    for s in payload.get("solids") or []:
        notn = _norm_lbl(s.get("notation", ""))
        for m in re.findall(r"[A-Z][0-9']*[']?", notn):
            entities.add(m)
        st = s.get("solid_type", "")
        pred_list.append(f"solid:{st}")
        arg_list.append((f"solid:{st}", (notn,)))

    for p in payload.get("premises") or []:
        k = p.get("kind", "")
        args = p.get("args") or {}
        if k == "regular_polygon":
            pts = tuple(sorted(_norm_lbl(x) for x in args.get("vertices", [])))
            entities.update(pts)
            pred_list.append("regular_polygon")
            arg_list.append(("regular_polygon", pts))
            if args.get("side"):
                qty_list.append(("regular_polygon", pts, _canon_num_str(args["side"])))
        elif k in ("rectangle", "rhombus", "parallelogram", "trapezoid", "isosceles_trapezoid"):
            pts = tuple(sorted(_norm_lbl(x) for x in args.get("vertices", [])))
            entities.update(pts)
            pred_list.append(k)
            arg_list.append((k, pts))
        elif k == "right_angle":
            at = _norm_lbl(args.get("vertex", ""))
            rays = tuple(sorted(_norm_lbl(x) for x in args.get("rays", [])))
            entities.add(at)
            entities.update(rays)
            pred_list.append("right_angle")
            arg_list.append(("right_angle", (at, *rays)))
        elif k == "perpendicular_line_plane":
            pa = tuple(sorted(_norm_lbl(x) for x in args.get("line", [])))
            pb = tuple(sorted(_norm_lbl(x) for x in args.get("plane", [])))
            entities.update(pa)
            entities.update(pb)
            pred_list.append("perpendicular_line_plane")
            arg_list.append(("perpendicular_line_plane", pa + pb))
        elif k == "segment_length":
            pts = tuple(sorted(_norm_lbl(x) for x in args.get("segment", [])))
            entities.update(pts)
            pred_list.append("segment_length")
            arg_list.append(("segment_length", pts))
            if args.get("value"):
                qty_list.append(("segment_length", pts, _canon_num_str(args["value"])))
        else:
            pred_list.append(k)
            for m in re.findall(r"[A-Z][0-9']*[']?", json.dumps(args, ensure_ascii=False)):
                entities.add(m)
    return {
        "entities": entities,
        "predicates": Counter(pred_list),
        "arg_bindings": Counter(arg_list),
        "qty_bindings": Counter(qty_list),
    }


def _counter_prf(pred: Counter, gold: Counter) -> tuple[int, int, int]:
    tp = sum((pred & gold).values())
    fp = sum(pred.values()) - tp
    fn = sum(gold.values()) - tp
    return tp, fp, fn


# ── Build & Freeze Manifest FIRST ────────────────────────────────────────────

def _build_and_freeze_manifest() -> tuple[dict[str, Any], str]:
    # Collect anti-leakage reference corpus
    ref_train: list[tuple[str, set[tuple[str, ...]], str]] = []
    for fn in ("train.jsonl", "val.jsonl"):
        p = DATASET_DIR / fn
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                d = json.loads(line)
                # extract user text
                msgs = d.get("messages") or []
                u = next((m.get("content", "") for m in msgs if m.get("role") == "user"), json.dumps(d, ensure_ascii=False))
                # problem text typically appears between markers or take full user prompt + norm
                ref_train.append((fn, _ngrams4(u), _norm_txt(u)))

    prior_slm_holdout_texts: list[tuple[str, set[tuple[str, ...]], str]] = []
    for src, p, k, tk in [
        ("V7H_112", RUNS_DIR / "deterministic-geometry-language-closure-slm-finetuning/SLM_V7_HOLDOUT_MANIFEST.json", "cases", "text"),
        ("NH48", RUNS_DIR / "specialized-geometry-extraction-slm-optimization/SLM_NEW_HOLDOUT_MANIFEST.json", "cases", "text"),
        ("H40", RUNS_DIR / "slm-local-geometry-understanding/independent_slm_holdout_manifest.json", "items", "problem_text"),
    ]:
        for c in json.loads(p.read_text(encoding="utf-8"))[k]:
            t = c[tk]
            prior_slm_holdout_texts.append((src, _ngrams4(t), _norm_txt(t)))

    c60 = json.loads((RUNS_DIR / "independent-nlu-extraction-evaluation/inputs/corpus-authoring/corpus.json").read_text(encoding="utf-8"))["cases"]
    c60_gold_facts = json.loads((RUNS_DIR / "independent-nlu-extraction-evaluation/inputs/gold_facts.json").read_text(encoding="utf-8"))["cases"]

    ext_manifest = json.loads((RUNS_DIR / "real-world-printed-handwriting-acquisition/external_image_corpus_manifest.json").read_text(encoding="utf-8"))["items"]
    ext_ora = json.loads((RUNS_DIR / "formal-correctness-real-world-acceptance/independent_mathematical_oracle.json").read_text(encoding="utf-8"))
    ext_ora_map = {r["case_id"]: r for r in ext_ora["served_checks"]}

    cases: list[dict[str, Any]] = []
    max_j_train = 0.0
    max_j_prior = 0.0
    exact_train_hits = 0

    def _leak_check(text: str) -> dict[str, Any]:
        nonlocal max_j_train, max_j_prior, exact_train_hits
        ng = _ngrams4(text)
        nt = _norm_txt(text)
        jt = max((len(ng & tng) / len(ng | tng) for _, tng, _ in ref_train if ng and (ng | tng)), default=0.0)
        jp = max((len(ng & png) / len(ng | png) for _, png, _ in prior_slm_holdout_texts if ng and (ng | png)), default=0.0)
        ex_hit = any(nt == ref_nt for _, _, ref_nt in ref_train + prior_slm_holdout_texts)
        max_j_train = max(max_j_train, jt)
        max_j_prior = max(max_j_prior, jp)
        if ex_hit:
            exact_train_hits += 1
        return {"max_4gram_vs_v7_train_val": round(jt, 4), "max_4gram_vs_prior_slm_holdouts": round(jp, 4), "exact_match": ex_hit}

    for c in c60:
        cid = c["id"]
        disp = c["gold_disposition"]
        oracles = _extract_c60_oracles(c.get("expected_values"))
        if disp == "answer_all" and oracles:
            eval_role = "VERIFIED_POSITIVE"
            ora_status = "VERIFIED_MATHEMATICAL_ORACLE"
        elif disp == "answer_all":
            eval_role = "NON_SCALAR_UI_OR_CONSTRUCT"
            ora_status = "GROUND_TRUTH_UNVERIFIED_OR_NON_SCALAR"
        else:
            eval_role = "NEGATIVE_OR_REFUSAL_EXPECTED"
            ora_status = "VERIFIED_REFUSAL_DISPOSITION"
        cases.append({
            "case_id": f"c60_{cid}",
            "orig_id": cid,
            "corpus": "C60_BLIND_NLU",
            "split": c["split"],
            "group": c["group"],
            "n_source_requests": c["n_source_requests"],
            "gold_disposition": disp,
            "eval_role": eval_role,
            "oracle_status": ora_status,
            "oracles": oracles,
            "text": c["source_text"],
            "provenance": "independent-nlu-extraction-evaluation (blind subagent, ZERO repo access, 2026-10-17, never exposed in /5-/7 SLM training or calibration)",
            "leakage_audit": _leak_check(c["source_text"]),
            "has_gold_facts": cid in c60_gold_facts,
        })

    for it in ext_manifest:
        if not it.get("has_complete_problem"):
            continue
        for sub_i, txt in enumerate(it.get("verbatim_problem_texts", []), 1):
            ecid = f"{it['image_id']}#{sub_i}"
            chk = ext_ora_map.get(ecid)
            if chk is not None:
                use_rounded = "làm tròn" in txt.lower() and chk.get("oracle_expected_answer") is not None
                ans = chk["oracle_expected_answer"] if use_rounded else chk["oracle_exact_answer"]
                if isinstance(ans, dict):
                    oracles = [str(ans[k]) for k in sorted(ans.keys())]
                else:
                    oracles = [str(ans)]
                eval_role = "VERIFIED_POSITIVE"
                ora_status = "VERIFIED_MATHEMATICAL_ORACLE"
            else:
                oracles = []
                eval_role = "OOS_OR_DIAGRAM_DEPENDENT"
                ora_status = "OUT_OF_SCOPE_OR_UNVERIFIED"
            cases.append({
                "case_id": f"ext_{ecid}",
                "orig_id": ecid,
                "corpus": "EXTERNAL17_REAL_TRANSCRIPTIONS",
                "split": it.get("corpus_subgroup", "external"),
                "group": it.get("license_status", "unknown"),
                "n_source_requests": len(oracles) or 1,
                "gold_disposition": "SERVE" if eval_role == "VERIFIED_POSITIVE" else "OOS_REFUSE",
                "eval_role": eval_role,
                "oracle_status": ora_status,
                "oracles": oracles,
                "text": txt,
                "provenance": f"{it['source_domain']} ({it['license_status']}) via formal-correctness-real-world-acceptance",
                "leakage_audit": _leak_check(txt),
                "has_gold_facts": False,
            })

    cand_sha, _ = measured_system_hash()
    manifest = {
        "schema": "slm-permissible-unseen-corpus-manifest/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "external_corpus_access_status": "INDEPENDENT_EXTERNAL_CORPUS = BLOCKED_DATA_ACCESS (for 100-150 fresh external student/teacher target)",
        "provenance_disclosure": (
            "Contains 77 permissible non-sealed repository items never used in /5, /6, or /7 SLM training or calibration "
            "(C60 blind agent-authored + External17 public/homework verbatim transcriptions). "
            "Not mislabeled as a new 100-150 external real-world human pilot."
        ),
        "frozen_candidate_sha256": cand_sha,
        "evaluator_version": EVALUATOR_VERSION,
        "anti_leakage_summary": {
            "reference_train_val_rows": len(ref_train),
            "reference_prior_slm_holdout_rows": len(prior_slm_holdout_texts),
            "exact_text_overlaps": exact_train_hits,
            "max_4gram_jaccard_vs_v7_train_val": round(max_j_train, 4),
            "max_4gram_jaccard_vs_prior_slm_holdouts": round(max_j_prior, 4),
            "zero_leakage_vs_train_val_lt_0_25": exact_train_hits == 0 and max_j_train < 0.25,
            "zero_leakage_verified_all_lt_0_55": exact_train_hits == 0 and max_j_train < 0.25 and max_j_prior < 0.55,
        },
        "counts": {
            "total_items": len(cases),
            "c60_total": sum(1 for x in cases if x["corpus"] == "C60_BLIND_NLU"),
            "c60_verified_positives": sum(1 for x in cases if x["corpus"] == "C60_BLIND_NLU" and x["eval_role"] == "VERIFIED_POSITIVE"),
            "c60_single_req_verified": sum(1 for x in cases if x["corpus"] == "C60_BLIND_NLU" and x["eval_role"] == "VERIFIED_POSITIVE" and x["n_source_requests"] == 1),
            "c60_multi_req_verified": sum(1 for x in cases if x["corpus"] == "C60_BLIND_NLU" and x["eval_role"] == "VERIFIED_POSITIVE" and x["n_source_requests"] > 1),
            "c60_negatives": sum(1 for x in cases if x["corpus"] == "C60_BLIND_NLU" and x["eval_role"] == "NEGATIVE_OR_REFUSAL_EXPECTED"),
            "c60_non_scalar_ui_construct": sum(1 for x in cases if x["corpus"] == "C60_BLIND_NLU" and x["eval_role"] == "NON_SCALAR_UI_OR_CONSTRUCT"),
            "external17_total": sum(1 for x in cases if x["corpus"] == "EXTERNAL17_REAL_TRANSCRIPTIONS"),
            "external17_verified_positives": sum(1 for x in cases if x["corpus"] == "EXTERNAL17_REAL_TRANSCRIPTIONS" and x["eval_role"] == "VERIFIED_POSITIVE"),
            "external17_oos_unverified": sum(1 for x in cases if x["corpus"] == "EXTERNAL17_REAL_TRANSCRIPTIONS" and x["eval_role"] == "OOS_OR_DIAGRAM_DEPENDENT"),
        },
        "cases": cases,
    }
    m_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    m_path = OUT_DIR / "PERMISSIBLE_UNSEEN_CORPUS_MANIFEST.json"
    m_path.write_bytes(m_bytes)
    return manifest, _lf_sha256_bytes(m_bytes)


def _grade_unseen_case(case: dict[str, Any], out_status: str, answers: dict[str, Any], refusal_code: str | None) -> dict[str, Any]:
    role = case["eval_role"]
    oracles = case["oracles"]
    ans_vals = [str(v) for v in (answers or {}).values()] if answers else []
    first_ans = ans_vals[0] if ans_vals else None
    goal_kind = infer_goal_kind_from_text(case["text"]) if len(oracles) == 1 else None

    if role == "VERIFIED_POSITIVE":
        if out_status != "SERVED" or not ans_vals:
            return {
                "ok_any_verified": False,
                "ok_strict_all": False,
                "wrong_served": False,
                "false_refusal": True,
                "safe_refusal": False,
                "matched_answers": 0,
                "first_answer": first_ans,
            }
        # Compare returned answers against verified oracle list
        matched_oracles = 0
        for ora in oracles:
            # Check direct goal_kind if single-request, else None to avoid single-goal assumption on multi-request items
            gk = goal_kind if len(oracles) == 1 else None
            if any(compare_math_expressions(a, ora, goal_kind=gk).matched is True for a in ans_vals):
                matched_oracles += 1
        any_wrong_answer = any(
            not any(compare_math_expressions(a, ora, goal_kind=(goal_kind if len(oracles) == 1 else None)).matched is True for ora in oracles)
            for a in ans_vals
        )
        ok_any = matched_oracles >= 1 and not any_wrong_answer
        ok_strict = matched_oracles == len(oracles) and not any_wrong_answer
        return {
            "ok_any_verified": ok_any,
            "ok_strict_all": ok_strict,
            "wrong_served": bool(out_status == "SERVED" and any_wrong_answer),
            "false_refusal": False,
            "safe_refusal": False,
            "matched_answers": matched_oracles,
            "first_answer": first_ans,
        }
    elif role in ("NEGATIVE_OR_REFUSAL_EXPECTED", "OOS_OR_DIAGRAM_DEPENDENT"):
        served = out_status == "SERVED"
        return {
            "ok_any_verified": not served,
            "ok_strict_all": not served,
            "wrong_served": served,
            "false_refusal": False,
            "safe_refusal": not served,
            "matched_answers": 0,
            "first_answer": first_ans,
        }
    else:
        # NON_SCALAR_UI_OR_CONSTRUCT: excluded from accuracy denominator
        return {
            "ok_any_verified": None,
            "ok_strict_all": None,
            "wrong_served": False,
            "false_refusal": False,
            "safe_refusal": out_status != "SERVED",
            "matched_answers": 0,
            "first_answer": first_ans,
        }


def _evaluate_config(
    *,
    config_name: str,
    cases: list[dict[str, Any]],
    c60_gold_facts: dict[str, Any],
    mode: str,
    model_key: str | None,
    closure_mode: str | None,
    normalizer_version: str | None,
    runtime: LocalSlmRuntime | None,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    agg_tp_pred = agg_fp_pred = agg_fn_pred = 0
    agg_tp_arg = agg_fp_arg = agg_fn_arg = 0
    agg_tp_qty = agg_fp_qty = agg_fn_qty = 0
    entity_exact_hits = 0
    tf_exact_hits = 0
    layer_scored_n = 0
    grounding_valid_n = 0
    slm_invoked_n = 0
    slm_rescue_n = 0
    parser_complete_n = 0
    det_rule_rescue_n = 0
    invented_premise_refusals = 0

    for idx, c in enumerate(cases, 1):
        clear_local_geometry_parser_cache()
        text = c["text"]
        t0 = time.perf_counter()
        raw_lp = parse_geometry_problem_locally(text)
        raw_complete = raw_lp.status == "LOCAL_PARSE_COMPLETE"
        if raw_complete:
            parser_complete_n += 1

        if mode == "det":
            out = AIR.route_text_input(text, allow_live_ai=False)
            norm_changed = False
            norm_lp_complete = False
            ex_payload = getattr(raw_lp, "payload", None) if raw_complete else None
        else:
            nr = normalize_for_slm_grounding(text, normalizer_version=normalizer_version or "v2")
            norm_changed = nr.changed
            lp_n = parse_geometry_problem_locally(nr.canonical_text)
            norm_lp_complete = bool(nr.changed and not nr.typo_detected and lp_n.status == "LOCAL_PARSE_COMPLETE")
            out = AIR.route_text_input_local_slm(
                text,
                model_key=model_key,
                strategy="compact_clause",
                runtime=runtime,
                allow_download=False,
                use_verified_normalizer=True,
                closure_mode=closure_mode or "v7",
                normalizer_version=normalizer_version or "v2",
                use_cache=False,
                cache_prompt=True,
            )
            ex_payload = None
            rd_tmp = out.response.get("route_d") or {}
            # Recover extraction payload if present in route telemetry or re-check parser
            ex_payload = rd_tmp.get("extracted_payload")

        wall_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        rd = out.response.get("route_d") or {}
        ref = rd.get("refusal") or {}
        slm_env = rd.get("slm_grounding_envelope") or {}
        ref_code = ref.get("code") or ref.get("reason_code")
        slm_inv = bool(slm_env.get("slm_invoked"))
        if slm_inv:
            slm_invoked_n += 1
        g_status = slm_env.get("grounding_status")
        if g_status == "GROUNDED_AND_LOWERED" or (not slm_inv and raw_complete):
            grounding_valid_n += 1
        if str(ref_code or "") in ("QUOTE_NOT_IN_SOURCE", "UNGROUNDED_VALUE") or "UNGROUNDED" in str(slm_env.get("failure_taxonomy") or ""):
            invented_premise_refusals += 1

        answers = rd.get("answers") or {}
        grade = _grade_unseen_case(c, out.status, answers, ref_code)

        if grade["ok_any_verified"] is True and c["eval_role"] == "VERIFIED_POSITIVE":
            if norm_lp_complete and not raw_complete:
                det_rule_rescue_n += 1
            elif slm_inv:
                slm_rescue_n += 1

        # Layer metrics against C60 gold_facts when verified SLM or deterministic payload exists
        layer_diag: dict[str, Any] | None = None
        if c["has_gold_facts"]:
            layer_scored_n += 1
            # Obtain canonical payload directly without second SLM call only via parser when not invoked, or if SLM invoked inspect accepted_ops/normalized
            gold_l = _gold_v1_to_layers(c60_gold_facts[c["orig_id"]])
            # For SLM-invoked C60 cases we don't duplicate an SLM call; reconstruct payload only if available, else check accepted_ops + parser
            cand_payload = ex_payload or (raw_lp.payload if raw_complete and hasattr(raw_lp, "payload") else None)
            if cand_payload is None and mode != "det" and slm_inv and g_status == "GROUNDED_AND_LOWERED":
                # Run fast cached extraction once (`use_cache=True`) or inspect accepted_ops
                cand_payload = {"premises": [{"kind": op.get("kind"), "args": {}} for op in (slm_env.get("accepted_ops") or []) if not str(op.get("kind", "")).startswith("goal:")]}
            ext_l = _v2_payload_to_layers(cand_payload)
            tp_p, fp_p, fn_p = _counter_prf(ext_l["predicates"], gold_l["predicates"])
            tp_a, fp_a, fn_a = _counter_prf(ext_l["arg_bindings"], gold_l["arg_bindings"])
            tp_q, fp_q, fn_q = _counter_prf(ext_l["qty_bindings"], gold_l["qty_bindings"])
            agg_tp_pred += tp_p; agg_fp_pred += fp_p; agg_fn_pred += fn_p
            agg_tp_arg += tp_a; agg_fp_arg += fp_a; agg_fn_arg += fn_a
            agg_tp_qty += tp_q; agg_fp_qty += fp_q; agg_fn_qty += fn_q
            ent_ex = bool(ext_l["entities"] == gold_l["entities"] and ext_l["entities"])
            if ent_ex:
                entity_exact_hits += 1
            if tp_a == sum(gold_l["arg_bindings"].values()) and fp_a == 0 and tp_q == sum(gold_l["qty_bindings"].values()) and fp_q == 0 and sum(gold_l["arg_bindings"].values()) > 0:
                tf_exact_hits += 1
            layer_diag = {"entity_exact": ent_ex, "pred_tp_fp_fn": [tp_p, fp_p, fn_p], "arg_tp_fp_fn": [tp_a, fp_a, fn_a], "qty_tp_fp_fn": [tp_q, fp_q, fn_q]}

        rows.append({
            "case_id": c["case_id"],
            "corpus": c["corpus"],
            "split": c["split"],
            "group": c["group"],
            "eval_role": c["eval_role"],
            "n_source_requests": c["n_source_requests"],
            "raw_parser_complete": raw_complete,
            "norm_changed": norm_changed,
            "norm_lp_complete": norm_lp_complete,
            "slm_invoked": slm_inv,
            "grounding_status": g_status,
            "status": out.status,
            "refusal_code": ref_code,
            "answers": answers,
            "oracles": c["oracles"],
            **grade,
            "wall_ms": wall_ms,
            "layer_diag": layer_diag,
        })
        if idx % 15 == 0 or idx == len(cases):
            print(f"[{config_name}] {idx}/{len(cases)} processed (last={c['case_id']} status={out.status} ok={grade['ok_any_verified']})", flush=True)

    # Aggregate verified metrics cleanly per split/role
    def _agg(sub: list[dict[str, Any]]) -> dict[str, Any]:
        vp = [r for r in sub if r["eval_role"] == "VERIFIED_POSITIVE"]
        vp_single = [r for r in vp if r["n_source_requests"] == 1]
        vp_multi = [r for r in vp if r["n_source_requests"] > 1]
        negs = [r for r in sub if r["eval_role"] in ("NEGATIVE_OR_REFUSAL_EXPECTED", "OOS_OR_DIAGRAM_DEPENDENT")]
        ok_any_n = sum(1 for r in vp if r["ok_any_verified"])
        ok_strict_n = sum(1 for r in vp if r["ok_strict_all"])
        ok_single_n = sum(1 for r in vp_single if r["ok_any_verified"])
        ok_multi_strict_n = sum(1 for r in vp_multi if r["ok_strict_all"])
        ws_pos = sum(1 for r in vp if r["wrong_served"])
        ws_neg = sum(1 for r in negs if r["wrong_served"])
        safe_neg = sum(1 for r in negs if r["safe_refusal"])
        false_ref = sum(1 for r in vp if r["false_refusal"])
        n_vp = len(vp)
        n_neg = len(negs)
        return {
            "total_items": len(sub),
            "verified_positives": n_vp,
            "correct_served_any_verified": ok_any_n,
            "correct_served_any_rate": round(ok_any_n / n_vp, 4) if n_vp else None,
            "correct_served_wilson95": _wilson_ci95(ok_any_n, n_vp),
            "correct_served_strict_all": ok_strict_n,
            "correct_served_strict_rate": round(ok_strict_n / n_vp, 4) if n_vp else None,
            "single_request_verified": f"{ok_single_n}/{len(vp_single)}",
            "multi_request_strict_all": f"{ok_multi_strict_n}/{len(vp_multi)}",
            "wrong_served_total": ws_pos + ws_neg,
            "wrong_served_on_positives": ws_pos,
            "wrong_served_on_negatives_or_oos": ws_neg,
            "safe_refusal_on_neg_or_oos": f"{safe_neg}/{n_neg}",
            "false_refusal_on_positives": false_ref,
        }

    def _f1(tp: int, fp: int, fn: int) -> dict[str, Any]:
        p = tp / (tp + fp) if (tp + fp) else 0.0
        r = tp / (tp + fn) if (tp + fn) else 0.0
        f = 2 * p * r / (p + r) if (p + r) else 0.0
        return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4)}

    by_group: dict[str, Any] = {}
    for gkey in sorted({r["group"] for r in rows}):
        by_group[gkey] = _agg([r for r in rows if r["group"] == gkey])

    return {
        "config_name": config_name,
        "summary_overall": _agg(rows),
        "summary_c60_blind_nlu": _agg([r for r in rows if r["corpus"] == "C60_BLIND_NLU"]),
        "summary_external17": _agg([r for r in rows if r["corpus"] == "EXTERNAL17_REAL_TRANSCRIPTIONS"]),
        "by_group": by_group,
        "stage_separation": {
            "parser_complete_on_all_77": parser_complete_n,
            "deterministic_rule_rescue_positives": det_rule_rescue_n,
            "slm_invocation_count": slm_invoked_n,
            "slm_invocation_rate": round(slm_invoked_n / len(rows), 4),
            "slm_successful_rescue_positives": slm_rescue_n,
            "source_grounding_valid_count": grounding_valid_n,
            "invented_premise_refusals": invented_premise_refusals,
        },
        "c60_extraction_layers_partial_or_parser": {
            "note": "Exact predicate/arg/qty F1 computed when structured TypedFactNext payload is produced on deterministic parse; full C60 SLM payloads traced separately.",
            "scored_items": layer_scored_n,
            "entity_exact_match": f"{entity_exact_hits}/{layer_scored_n}",
            "typed_facts_exact_match": f"{tf_exact_hits}/{layer_scored_n}",
            "predicate_prf": _f1(agg_tp_pred, agg_fp_pred, agg_fn_pred),
            "argument_binding_prf": _f1(agg_tp_arg, agg_fp_arg, agg_fn_arg),
            "quantity_binding_prf": _f1(agg_tp_qty, agg_fp_qty, agg_fn_qty),
        },
        "rows": rows,
    }


def _run_offline_k1_r1_s2_diagnostic(runtime: LocalSlmRuntime) -> dict[str, Any]:
    """0-cloud-call Config A vs C vs D check on {k1, r1, s2} vs historical Gemini 2.5 Flash logs (for P6 diagnostic ONLY)."""
    pilot_dir = RUNS_DIR / "hybrid-master-backend-replacement"
    gemini_dir = RUNS_DIR / "hybrid-live-extraction-retest/full"
    studies = []
    for sname, cfile, lfile in [
        ("K-1", "k1-live-pilot-corpus.json", "k1-live.jsonl"),
        ("R-1", "r1-live-pilot-corpus.json", "r1-live.jsonl"),
        ("S-2", "s2-student-language-pilot-corpus.json", "s2-live.jsonl"),
    ]:
        cases = json.loads((pilot_dir / cfile).read_text(encoding="utf-8"))["cases"]
        gem_rows = [json.loads(ln) for ln in (gemini_dir / lfile).read_text(encoding="utf-8").splitlines() if ln.strip() and '"type": "row"' in ln]
        gem_served = sum(1 for r in gem_rows if (r.get("observed") or {}).get("status") == "SERVED")
        gem_e2e_ok = sum(1 for r in gem_rows if r.get("end_to_end_correct") is True)
        gem_lats = sorted(float(r["latency_s"]) for r in gem_rows if r.get("latency_s") is not None)
        gem_usd = sum(float(r.get("usd") or 0.0) for r in gem_rows)

        d_served = 0
        d_expected_serve = 0
        d_lats: list[float] = []
        d_refusals: Counter[str] = Counter()
        for c in cases:
            txt = c["problem_text"]
            exp_out = (c.get("expected") or {}).get("outcome")
            if exp_out == "SERVED":
                d_expected_serve += 1
            t0 = time.perf_counter()
            out = AIR.route_text_input_local_slm(
                txt,
                model_key=FINETUNED_LOCAL_SLM_MODEL_KEY,
                strategy="compact_clause",
                runtime=runtime,
                allow_download=False,
                use_verified_normalizer=True,
                closure_mode="v7",
                normalizer_version="v2",
                use_cache=False,
                cache_prompt=True,
            )
            d_lats.append((time.perf_counter() - t0) * 1000.0)
            rd = out.response.get("route_d") or {}
            ref = rd.get("refusal") or {}
            if out.status == "SERVED":
                d_served += 1
            else:
                d_refusals[str(ref.get("code") or ref.get("reason_code") or out.status)] += 1
        d_lats.sort()
        studies.append({
            "study": sname,
            "cases_count": len(cases),
            "expected_served_cases": d_expected_serve,
            "gemini_2_5_flash_historical": {
                "rows": len(gem_rows),
                "served": gem_served,
                "end_to_end_correct": gem_e2e_ok,
                "median_latency_ms": round(gem_lats[len(gem_lats) // 2] * 1000.0, 1) if gem_lats else None,
                "total_est_usd": round(gem_usd, 6),
            },
            "config_d_axov7_local_offline": {
                "served": d_served,
                "median_latency_ms": round(d_lats[len(d_lats) // 2], 1) if d_lats else None,
                "refusal_codes": dict(d_refusals),
                "parity_claim": "NOT_COMPATIBLE_FOR_HEAD_TO_HEAD_PARITY (K-1 tests derived sections outside compact_clause/1; R-1/S-2 test pilot-specific contracts; see GEMINI_PARITY_PROTOCOL.md)",
            },
        })
        print(f"[OFFLINE {sname}] Gemini e2e={gem_e2e_ok}/{len(gem_rows)} vs AxoV7 served={d_served}/{len(cases)}", flush=True)
    return {"external_ai_calls": 0, "studies": studies}


def main() -> int:
    manifest, manifest_sha = _build_and_freeze_manifest()
    print(
        f"Manifest frozen before inference: items={manifest['counts']['total_items']}, "
        f"leakage_train_val_ok={manifest['anti_leakage_summary']['zero_leakage_vs_train_val_lt_0_25']}, "
        f"leakage_all_ok={manifest['anti_leakage_summary']['zero_leakage_verified_all_lt_0_55']}, "
        f"max_4gram_train={manifest['anti_leakage_summary']['max_4gram_jaccard_vs_v7_train_val']}, "
        f"sha256_lf={manifest_sha[:16]}...",
        flush=True,
    )
    c60_gold_facts = json.loads((RUNS_DIR / "independent-nlu-extraction-evaluation/inputs/gold_facts.json").read_text(encoding="utf-8"))["cases"]
    cases = manifest["cases"]

    configs_out: dict[str, Any] = {}
    rt = LocalSlmRuntime()
    try:
        configs_out["config_a_deterministic_v145"] = _evaluate_config(
            config_name="config_a_deterministic_v145", cases=cases, c60_gold_facts=c60_gold_facts,
            mode="det", model_key=None, closure_mode=None, normalizer_version=None, runtime=None,
        )
        rt.shutdown()
        configs_out["config_b_v6_compact_original"] = _evaluate_config(
            config_name="config_b_v6_compact_original", cases=cases, c60_gold_facts=c60_gold_facts,
            mode="slm", model_key=DEFAULT_LOCAL_SLM_MODEL_KEY, closure_mode="v6", normalizer_version="v1", runtime=rt,
        )
        rt.shutdown()
        configs_out["config_c_v7_closure_original_slm"] = _evaluate_config(
            config_name="config_c_v7_closure_original_slm", cases=cases, c60_gold_facts=c60_gold_facts,
            mode="slm", model_key=DEFAULT_LOCAL_SLM_MODEL_KEY, closure_mode="v7", normalizer_version="v2", runtime=rt,
        )
        rt.shutdown()
        configs_out["config_d_v7_closure_finetuned_slm"] = _evaluate_config(
            config_name="config_d_v7_closure_finetuned_slm", cases=cases, c60_gold_facts=c60_gold_facts,
            mode="slm", model_key=FINETUNED_LOCAL_SLM_MODEL_KEY, closure_mode="v7", normalizer_version="v2", runtime=rt,
        )
        offline_k1r1s2 = _run_offline_k1_r1_s2_diagnostic(rt)
    finally:
        rt.shutdown()

    # Paired comparisons on verified positives (n = 54)
    def _paired(k1: str, k2: str) -> dict[str, Any]:
        m1 = {r["case_id"]: r for r in configs_out[k1]["rows"]}
        m2 = {r["case_id"]: r for r in configs_out[k2]["rows"]}
        gained, lost = [], []
        both_p = both_f = 0
        for cid, r1 in m1.items():
            if r1["eval_role"] != "VERIFIED_POSITIVE":
                continue
            r2 = m2[cid]
            o1, o2 = bool(r1["ok_any_verified"]), bool(r2["ok_any_verified"])
            if o1 and o2: both_p += 1
            elif not o1 and not o2: both_f += 1
            elif not o1 and o2: gained.append(cid)
            else: lost.append(cid)
        n = both_p + both_f + len(gained) + len(lost)
        p1 = (both_p + len(lost)) / n if n else 0.0
        p2 = (both_p + len(gained)) / n if n else 0.0
        return {
            "n_verified_positives": n,
            "gained": gained,
            "lost": lost,
            "b01_gained": len(gained),
            "b10_lost": len(lost),
            "mcnemar_exact_p": _mcnemar_exact(len(gained), len(lost)),
            "cohen_h": _cohen_h(p1, p2),
        }

    paired = {
        "b_to_c_deterministic_closure": _paired("config_b_v6_compact_original", "config_c_v7_closure_original_slm"),
        "c_to_d_finetuning_contribution": _paired("config_c_v7_closure_original_slm", "config_d_v7_closure_finetuned_slm"),
        "a_to_d_total_local_gain": _paired("config_a_deterministic_v145", "config_d_v7_closure_finetuned_slm"),
    }

    report = {
        "schema": "slm-permissible-unseen-evaluation/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "single_shot": True,
        "external_ai_calls": 0,
        "external_corpus_access_status": "INDEPENDENT_EXTERNAL_CORPUS = BLOCKED_DATA_ACCESS",
        "manifest_sha256_lf": manifest_sha,
        "frozen_candidate_sha256": manifest["frozen_candidate_sha256"],
        "evaluator_version": EVALUATOR_VERSION,
        "contracts": {
            "runtime": LOCAL_SLM_RUNTIME_VERSION,
            "extractor": LOCAL_SLM_EXTRACTOR_VERSION,
            "validator": SLM_GROUNDING_VALIDATOR_VERSION,
            "normalizer": SLM_VERIFIED_NORMALIZER_VERSION,
            "compact_clause": SLM_COMPACT_SCHEMA_VERSION,
        },
        "configs": configs_out,
        "paired_comparisons": paired,
        "offline_k1_r1_s2_historical_gemini_diagnostic": offline_k1r1s2,
    }
    out_p = OUT_DIR / "PERMISSIBLE_UNSEEN_CORPUS_EVALUATION.json"
    out_p.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("=== UNSEEN PERMISSIBLE CORPORA SUMMARY (overall verified N=54, C60 N=42, Ext17 N=12) ===")
    for k, v in configs_out.items():
        so, c6, ex = v["summary_overall"], v["summary_c60_blind_nlu"], v["summary_external17"]
        print(
            f"  {k}: overall={so['correct_served_any_verified']}/{so['verified_positives']} ({so['correct_served_any_rate']:.1%}) "
            f"| C60={c6['correct_served_any_verified']}/{c6['verified_positives']} (single={c6['single_request_verified']}, multi_strict={c6['multi_request_strict_all']}) "
            f"| Ext17={ex['correct_served_any_verified']}/{ex['verified_positives']} | wrong_served={so['wrong_served_total']} | neg_safe={so['safe_refusal_on_neg_or_oos']}",
            flush=True,
        )
    print("Paired C->D:", paired["c_to_d_finetuning_contribution"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
