# -*- coding: utf-8 -*-
"""Phase B / P2 Failure Audit & Evidence-Backed Capability Matrix (`axo-slm-v8`).

Collects complete 13-field extraction -> grounding -> Source Gate -> Planner -> Exact Kernel
traces + Gold compact_clause interventions for the 6 unresolved `/7` holdout positives
(`v7h_p8_01..05`, `v7h_p5_09`), passing comparators (`v7h_p8_06`, `v7h_p5_08`), and the
`slm_h23_ocr_extra_spaces` regression (`Config C` vs `Config D` + sibling blast-radius probes),
then constructs `SLM_CAPABILITY_MATRIX.json` with exact empirical denominators.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("HYBRID_ROUTE_MODE", None)

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
RUN5_DIR = ROOT / "docs/evaluation/geometry/runs/slm-local-geometry-understanding"
RUN6_DIR = ROOT / "docs/evaluation/geometry/runs/specialized-geometry-extraction-slm-optimization"
RUN7_DIR = ROOT / "docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning"
OUT_DIR = ROOT / "docs/evaluation/geometry/runs/independent-validation-local-ai-production-readiness"
OUT_DIR.mkdir(parents=True, exist_ok=True)

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(BACKEND / "scripts") not in sys.path:
    sys.path.insert(0, str(BACKEND / "scripts"))

from app.ai import adaptive_input_router as AIR  # noqa: E402
from app.ai.hybrid_offline import ReplayExtractor, hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.local_geometry_parser import clear_local_geometry_parser_cache, parse_geometry_problem_locally  # noqa: E402
from app.ai.local_slm_extractor import (  # noqa: E402
    build_compact_clause_context,
    run_local_slm_extraction,
    validate_and_lower_compact_clause,
)
from app.ai.local_slm_runtime import (  # noqa: E402
    DEFAULT_LOCAL_SLM_MODEL_KEY,
    FINETUNED_LOCAL_SLM_MODEL_KEY,
    LocalSlmRuntime,
)
from app.ai.slm_verified_normalizer import normalize_for_slm_grounding  # noqa: E402
from app.simulation.geometry_functions import engine, planner, registry  # noqa: E402
from slm_math_evaluator_v2 import compare_math_expressions, infer_goal_kind_from_text  # noqa: E402


def _inspect_source_gate_and_planner(canon_payload: dict[str, Any] | None) -> dict[str, Any]:
    """Run Source Gate (`registry.kiem_nguon`) + Planner (`/26`) + Kernel (`/24`) deterministically when lowered."""
    if not isinstance(canon_payload, dict):
        return {
            "source_gate_result": "NOT_REACHED (no lowered TypedFactNext payload)",
            "planner_result": "NOT_REACHED",
            "kernel_result": "NOT_REACHED",
            "refusal_code": None,
        }
    pol = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
    ho = run_hybrid_offline(
        canon_payload.get("problem_text", ""),
        ReplayExtractor({canon_payload.get("problem_text", ""): canon_payload}),
        policy=pol,
    )
    rd = ho.response.get("route_d") or {}
    ref = rd.get("refusal") or {}
    plan_obj = rd.get("plan") or {}
    plan_info = {
        "chosen_plan": bool(plan_obj),
        "plan_steps_count": len(plan_obj.get("steps", [])) if isinstance(plan_obj, dict) else 0,
    }
    return {
        "source_gate_result": {
            "status": rd.get("status"),
            "refusal_code": ref.get("code") or ref.get("reason_code"),
            "refusal_message": ref.get("message") or ref.get("detail"),
            "gate_errors": ref.get("errors") or ref.get("unread_premises") or [],
        },
        "planner_result": plan_info if rd.get("status") == "SERVED" else f"BLOCKED_BEFORE_OR_IN_PLANNER ({ref.get('code') or rd.get('status')})",
        "kernel_result": {"status": rd.get("status"), "answers": rd.get("answers")} if rd.get("status") == "SERVED" else f"NOT_SERVED ({ref.get('code')})",
        "bridge_summary": {"premises_count": len(canon_payload.get("premises", [])), "goals_count": len(canon_payload.get("math_goals", []))},
    }


def _gold_slm_for_case(cid: str, text: str) -> dict[str, Any]:
    """Exact gold compact_clause JSON matching `build_slm_v7_blind_holdout.py` for the audited cases."""
    if cid in ("v7h_p5_08", "v7h_p5_09"):
        m_sol = re.search(r"hình chóp ([A-Z])\.([A-Z]{3})", text)
        m_sd = re.search(r"cạnh\s+([0-9a√]+)", text)
        m_mid = re.search(r"Gọi\s+([A-Z])\s+là trung điểm của cạnh\s+([A-Z]{2})", text)
        m_ang = re.search(r"Góc giữa\s+([A-Z]{2})\s+với mặt phẳng\s+\(([A-Z]{3})\)\s+là\s+(\d+°)", text)
        ap, bs = m_sol.group(1), m_sol.group(2)
        return {
            "s": [0, "pyr", f"{ap}.{bs}", 0],
            "r": [
                {"c": 0, "p": "reg_poly", "a": bs, "q": m_sd.group(1)},
                {"c": 1, "p": "mid", "pt": m_mid.group(1), "a": m_mid.group(2)},
                {"c": 1, "p": "proj", "pt": m_mid.group(1), "a": ap, "b": bs},
                {"c": 2, "p": "ang_lp", "a": m_ang.group(1), "b": m_ang.group(2), "q": m_ang.group(3)},
            ],
            "g": [{"c": 3, "t": "vol", "tgt": f"{ap}.{bs}"}],
            "u": [],
        }
    if cid == "slm_h23_ocr_extra_spaces":
        return {
            "s": [0, "pyr", "S.ABC", 0],
            "r": [
                {"c": 0, "p": "reg_poly", "a": "ABC", "q": "2a"},
                {"c": 0, "p": "perp_lp", "a": "SA", "b": "ABC"},
                {"c": 0, "p": "len", "a": "SA", "q": "3a"},
            ],
            "g": [{"c": 1, "t": "vol", "tgt": "S.ABC"}],
            "u": [],
        }
    # v7h_p8_01..05 share exact structure from build_slm_v7_blind_holdout.py:602-620
    # Parse apex, base, perp line, h, ab, bc, mp, cd, tgt face from normalized text dynamically
    m_sol = re.search(r"khối chóp ([A-Z])\.([A-Z]{4})", text)
    m_h = re.search(r"([A-Z]{2})\s*=\s*([0-9a√]+)", text)
    m_sides = re.search(r"với\s+([A-Z]{2})\s*=\s*([0-9a√]+),\s*([A-Z]{2})\s*=\s*([0-9a√]+)", text)
    m_mid = re.search(r"Lấy\s+([A-Z])\s+là trung điểm\s+([A-Z]{2})", text)
    m_dist = re.search(r"khoảng cách từ điểm\s+([A-Z])\s+đến\s*\(([A-Z]{3})\)", text)
    ap, bs = m_sol.group(1), m_sol.group(2)
    h_seg, h_val = m_h.group(1), m_h.group(2)
    s1, v1, s2, v2 = m_sides.group(1), m_sides.group(2), m_sides.group(3), m_sides.group(4)
    mp, mid_seg = m_mid.group(1), m_mid.group(2)
    dist_pt, dist_pl = m_dist.group(1), m_dist.group(2)
    return {
        "s": [0, "pyr", f"{ap}.{bs}", 0],
        "r": [
            {"c": 0, "p": "perp_lp", "a": h_seg, "b": bs},
            {"c": 0, "p": "len", "a": h_seg, "q": h_val},
            {"c": 1, "p": "rect", "a": bs},
            {"c": 1, "p": "len", "a": s1, "q": v1},
            {"c": 1, "p": "len", "a": s2, "q": v2},
            {"c": 2, "p": "mid", "pt": mp, "a": mid_seg},
        ],
        "g": [{"c": 3, "t": "dist_pt_plane", "a": dist_pt, "b": dist_pl}],
        "u": [],
    }


def _gold_for_p8_06(text: str) -> dict[str, Any]:
    m_sol = re.search(r"lăng trụ đứng\s+([A-Z']+\.[A-Z']+)", text)
    m_h = re.search(r"cạnh bên\s+([A-Z][A-Z']+)\s*=\s*([0-9a√]+)", text)
    m_tri = re.search(r"đáy\s+([A-Z]{3})\s+là tam giác vuông tại\s+([A-Z])\s+với\s+([A-Z]{2})\s*=\s*([0-9a√]+),\s*([A-Z]{2})\s*=\s*([0-9a√]+)", text)
    solid = m_sol.group(1)
    h_seg, h_val = m_h.group(1), m_h.group(2)
    bs, rpt, s1, v1, s2, v2 = m_tri.group(1), m_tri.group(2), m_tri.group(3), m_tri.group(4), m_tri.group(5), m_tri.group(6)
    return {
        "s": [0, "pri", solid, 1],
        "r": [
            {"c": 0, "p": "len", "a": h_seg, "q": h_val},
            {"c": 0, "p": "right_tri", "a": bs, "pt": rpt},
            {"c": 0, "p": "len", "a": s1, "q": v1},
            {"c": 0, "p": "len", "a": s2, "q": v2},
        ],
        "g": [{"c": 1, "t": "vol", "tgt": solid}],
        "u": [],
    }


def _trace_case(
    *,
    case_id: str,
    text: str,
    oracle: str,
    model_key: str,
    runtime: LocalSlmRuntime,
    gold_slm: dict[str, Any] | None = None,
) -> dict[str, Any]:
    clear_local_geometry_parser_cache()
    norm_res = normalize_for_slm_grounding(text, normalizer_version="v2")
    lp = parse_geometry_problem_locally(text)
    lp_norm = parse_geometry_problem_locally(norm_res.canonical_text)

    ex = run_local_slm_extraction(
        text,
        model_key=model_key,
        strategy="compact_clause",
        runtime=runtime,
        allow_download=False,
        use_verified_normalizer=True,
        closure_mode="v7",
        normalizer_version="v2",
        use_cache=False,
        cache_prompt=True,
    )
    # Also build raw Source Gate / Planner / Kernel trace from the exact single `ex` run (no double inference!)
    downstream_trace = _inspect_source_gate_and_planner(ex.canonical_payload) if ex.ok else {
        "source_gate_result": f"NOT_REACHED_GROUNDING_FAILED ({ex.reason_code})",
        "planner_result": "NOT_REACHED",
        "kernel_result": "NOT_REACHED",
    }
    rd = {}
    if isinstance(downstream_trace.get("source_gate_result"), dict):
        route_status = downstream_trace["source_gate_result"].get("status") or "REFUSED"
        ref = {
            "code": downstream_trace["source_gate_result"].get("refusal_code"),
            "message": downstream_trace["source_gate_result"].get("refusal_message"),
        }
        kres = downstream_trace.get("kernel_result")
        answers = kres.get("answers") if isinstance(kres, dict) else {}
    else:
        route_status = "REFUSED"
        ref = {"code": ex.reason_code, "message": ex.reason_detail}
        answers = {}
    out_status = route_status
    slm_env = ex.grounding_envelope or {}

    # Gold intervention
    gold_result: dict[str, Any] | None = None
    if gold_slm is not None:
        ctx = build_compact_clause_context(norm_res.canonical_text)
        g_payload, g_diag = validate_and_lower_compact_clause(ctx=ctx, raw_slm_json=gold_slm, closure_mode="v7")
        if g_payload is not None and g_diag.get("grounding_status") == "GROUNDED_AND_LOWERED":
            pol = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
            g_ho = run_hybrid_offline(norm_res.canonical_text, ReplayExtractor({norm_res.canonical_text: g_payload}), policy=pol)
            g_rd = g_ho.response.get("route_d") or {}
            g_ans = None
            if g_rd.get("answers"):
                g_ans = str(g_rd["answers"].get("q1") or next(iter(g_rd["answers"].values())))
            g_v2 = compare_math_expressions(g_ans, oracle, goal_kind=infer_goal_kind_from_text(text)) if g_ans else None
            gold_result = {
                "grounding_status": g_diag.get("grounding_status"),
                "route_status": g_rd.get("status"),
                "answer": g_ans,
                "oracle_match_v2": g_v2.matched if g_v2 else False,
                "refusal": g_rd.get("refusal"),
            }
        else:
            gold_result = {"grounding_status": g_diag.get("grounding_status"), "rejected_ops": g_diag.get("rejected_ops")}

    # Determine route answer if SERVED
    served_ans = None
    if answers:
        served_ans = str(answers.get("q1") or next(iter(answers.values())))

    # Detailed 13 mandatory fields
    return {
        "case_id": case_id,
        "model_key": model_key,
        "1_original_text": text,
        "2_normalized_text": ex.norm_text,
        "3_transformation_provenance": ex.normalization_provenance,
        "4_parser_output": {
            "raw_status": lp.status,
            "raw_diagnostics": getattr(lp, "diagnostics", None),
            "after_normalizer_status": lp_norm.status,
            "after_normalizer_premises_count": len(lp_norm.payload.get("premises", [])) if isinstance(lp_norm.payload, dict) else 0,
        },
        "5_compact_slm_output": {
            "raw_content": ex.inference.raw_content if ex.inference else None,
            "parsed_json": ex.inference.parsed_json if ex.inference else None,
            "slm_invoked": bool(slm_env.get("slm_invoked")),
        },
        "6_grounding_status": {
            "ok": ex.ok,
            "grounding_status": slm_env.get("grounding_status"),
            "failure_taxonomy": ex.failure_taxonomy,
            "accepted_ops": slm_env.get("accepted_ops"),
            "rejected_ops": slm_env.get("rejected_ops"),
        },
        "7_typed_facts": ex.canonical_payload,
        "8_source_gate_result": downstream_trace["source_gate_result"],
        "9_planner_result": downstream_trace["planner_result"],
        "10_kernel_result": {
            "route_status": out_status,
            "answer": served_ans,
            "oracle": oracle,
            "v2_match": bool(compare_math_expressions(served_ans, oracle, goal_kind=infer_goal_kind_from_text(text)).matched) if served_ans else False,
            "downstream_trace": downstream_trace["kernel_result"],
        },
        "11_exact_refusal_reason": {
            "extraction_reason_code": ex.reason_code,
            "extraction_reason_detail": ex.reason_detail,
            "route_refusal_code": ref.get("code") or ref.get("reason_code"),
            "route_refusal_message": ref.get("message") or ref.get("detail"),
        },
        "12_gold_intervention_result": gold_result,
        "13_owner_boundary": None,  # Populated explicitly below
    }


def _classify_owner(trace: dict[str, Any]) -> dict[str, str]:
    cid = trace["case_id"]
    if cid.startswith("v7h_p8_"):
        return {
            "root_cause_category": "MODEL_SEMANTIC_ERROR (+ minor normalizer prefix quirk on v7h_p8_01)",
            "explanation": (
                "Compact-clause SLM AxoV7 omitted `{\"c\": 1, \"p\": \"rect\", \"a\": <base>}` when base shape was reordered into Sentence 1 (`Biết ABCD là hình chữ nhật với ...`) without the keyword `đáy`. "
                "Source Gate (`doc_rang_buoc`) faithfully detected that Sentence 1's premise was unread by any lowered fact and refused with `SOURCE_PREMISE_UNREAD`. Gold `compact_clause` JSON serves cleanly even with the conversational prefix."
            ),
            "owner_boundary": "local_slm_extractor / AxoV7 data coverage (NOT Source Gate defect); normalizer ownership in slm_verified_normalizer (FROZEN candidate in /8)",
        }
    if cid == "v7h_p5_09":
        return {
            "root_cause_category": "MODEL_SEMANTIC_ERROR",
            "explanation": (
                "Compact-clause SLM AxoV7 inverted the projection arguments on `hình chiếu vuông góc của G lên (RST) trùng với điểm I` "
                "(emitting `point='R', image='G'` plus spurious `perp_lp('RS', 'RST')`). Source Gate (`_C_CHIEU`) faithfully caught the swapped point/image against source text (`SOURCE_OBJECT_MISMATCH`), preventing an unsafe hallucinated solve."
            ),
            "owner_boundary": "AxoV7 model robustness (NOT Source Gate defect — Source Gate safety boundary worked as designed)",
        }
    if cid == "slm_h23_ocr_extra_spaces":
        return {
            "root_cause_category": "MODEL_SEMANTIC_ERROR (over-conservative unresolved emission on AxoV7)",
            "explanation": (
                "Config C (`qwen3-0.6b-q4_k_m`) extracted/reconciled the premises and SERVED `a³√3`; Config D (`qwen3-0.6b-axo-v7-q4_k_m`) emitted `u=[{\"c\": 0, \"r\": \"missing_operand\"}]`, tripping `AMBIGUOUS_FACT`. Zero wrong-served risk."
            ),
            "owner_boundary": "AxoV7 fine-tuned checkpoint calibration / local_slm_extractor",
        }
    return {"root_cause_category": "PASSING_COMPARATOR", "explanation": "Served matching oracle.", "owner_boundary": "None"}


def _build_capability_matrix() -> dict[str, Any]:
    v7_m = json.loads((RUN7_DIR / "SLM_V7_HOLDOUT_MANIFEST.json").read_text(encoding="utf-8"))["cases"]
    v7_e = json.loads((RUN7_DIR / "SLM_V7_HOLDOUT_EVALUATION.json").read_text(encoding="utf-8"))
    nh48_m = json.loads((RUN6_DIR / "SLM_NEW_HOLDOUT_MANIFEST.json").read_text(encoding="utf-8"))["cases"]
    v7_abl = json.loads((RUN7_DIR / "SLM_V7_ABLATION.json").read_text(encoding="utf-8"))
    v5_bc = json.loads((RUN5_DIR / "SLM_BASELINE_COMPARISON.json").read_text(encoding="utf-8"))

    # Combine V7H_112 (Config D) + NH48 (Config D) + HOLDOUT_40 (Config D) case-level outcomes with v2 math verification!
    v7_rows_a = {r["id"]: r for r in v7_e["configs"]["config_a_deterministic_v145"]["rows"]}
    v7_rows_c = {r["id"]: r for r in v7_e["configs"]["config_c_v7_closure_original_slm"]["rows"]}
    v7_rows_d = {r["id"]: r for r in v7_e["configs"]["config_d_v7_closure_finetuned_slm"]["rows"]}
    nh48_rows_d = {r["id"]: r for r in v7_abl["datasets"]["SLM_NEW_HOLDOUT_48"]["configs"]["config_d_v7_closure_finetuned_slm"]["rows"]}
    nh48_rows_c = {r["id"]: r for r in v7_abl["datasets"]["SLM_NEW_HOLDOUT_48"]["configs"]["config_c_v7_closure_original_slm"]["rows"]}
    h40_m = json.loads((RUN5_DIR / "independent_slm_holdout_manifest.json").read_text(encoding="utf-8"))["items"]
    h40_rows_d = {r["id"]: r for r in v7_abl["datasets"]["HOLDOUT_40"]["configs"]["config_d_v7_closure_finetuned_slm"]["rows"]}

    pool: list[dict[str, Any]] = []
    for c in v7_m:
        if c["kind"] != "positive":
            continue
        cid = c["case_id"]
        rd = v7_rows_d[cid]
        rc = v7_rows_c[cid]
        ra = v7_rows_a[cid]
        gk = infer_goal_kind_from_text(c["text"])
        ok_d = rd["status"] == "SERVED" and bool(compare_math_expressions(str(rd["answer"]), str(c["oracle"]), goal_kind=gk).matched)
        ok_c = rc["status"] == "SERVED" and bool(compare_math_expressions(str(rc["answer"]), str(c["oracle"]), goal_kind=gk).matched)
        ok_a = ra["status"] == "SERVED" and bool(compare_math_expressions(str(ra["answer"]), str(c["oracle"]), goal_kind=gk).matched)
        pool.append({"source": "V7H_112", "id": cid, "family": c["family"], "text": c["text"], "ok_a": ok_a, "ok_c": ok_c, "ok_d": ok_d, "wrong_d": rd["status"] == "SERVED" and not ok_d})
    for c in nh48_m:
        if c["kind"] != "positive":
            continue
        cid = c["case_id"]
        rd = nh48_rows_d[cid]
        rc = nh48_rows_c[cid]
        pool.append({"source": "NH48", "id": cid, "family": c["family"], "text": c["text"], "ok_a": False, "ok_c": bool(rc["ok"]), "ok_d": bool(rd["ok"]), "wrong_d": bool(rd.get("wrong_served"))})
    for c in h40_m:
        if c["expected_outcome"] != "SERVED":
            continue
        cid = c["case_id"]
        rd = h40_rows_d[cid]
        pool.append({"source": "H40", "id": cid, "family": c["stratum"], "text": c["problem_text"], "ok_a": False, "ok_c": False, "ok_d": bool(rd["ok"]), "wrong_d": bool(rd.get("wrong_served"))})

    def summarize(matcher) -> dict[str, Any]:
        matched = [x for x in pool if matcher(x)]
        n = len(matched)
        ok_d = sum(1 for x in matched if x["ok_d"])
        ok_c = sum(1 for x in matched if x["ok_c"])
        ws = sum(1 for x in matched if x["wrong_d"])
        rate = round(ok_d / n, 4) if n else None
        return {
            "samples": n,
            "config_d_passed": ok_d,
            "config_d_rate": rate,
            "config_c_passed": ok_c,
            "wrong_served": ws,
            "sources": dict(Counter_dict([x["source"] for x in matched])),
            "sample_ids_failed_in_d": [x["id"] for x in matched if not x["ok_d"]][:10],
        }

    def Counter_dict(items: list[str]) -> dict[str, int]:
        out: dict[str, int] = {}
        for s in items:
            out[s] = out.get(s, 0) + 1
        return out

    def classify_entry(name: str, desc: str, stats: dict[str, Any], *, force_status: str | None = None, note: str = "") -> dict[str, Any]:
        n = stats["samples"]
        rate = stats["config_d_rate"] or 0.0
        if force_status is not None:
            st = force_status
        elif n == 0:
            st = "NOT_MEASURED"
        elif n >= 5 and rate >= 0.85 and stats["wrong_served"] == 0:
            st = "VALIDATED_LOCAL_PRIMARY"
        else:
            st = "EXPERIMENTAL"
        return {
            "category": name,
            "description": desc,
            "status": st,
            "evidence": stats,
            "notes": note,
        }

    supported_matrix = [
        classify_entry("solid_triangular_pyramid", "Hình chóp tam giác (S.ABC)", summarize(lambda x: bool(re.search(r"chóp\s+[A-Z]\.[A-Z]{3}(?![A-Z])", x["text"])))),
        classify_entry("solid_quadrilateral_pyramid", "Hình chóp tứ giác (S.ABCD)", summarize(lambda x: bool(re.search(r"chóp\s+[A-Z]\.[A-Z]{4}", x["text"])))),
        classify_entry("solid_regular_pyramid", "Hình chóp đều (tam giác đều / chóp tứ giác đều)", summarize(lambda x: "chóp đều" in x["text"].lower() or "chóp tam giác đều" in x["text"].lower() or "chóp tứ giác đều" in x["text"].lower())),
        classify_entry("solid_right_and_regular_prism", "Lăng trụ đứng / lăng trụ đều (ABC.A'B'C', ABCD.A'B'C'D')", summarize(lambda x: "lăng trụ" in x["text"].lower())),
        classify_entry("solid_rectangular_box", "Hình hộp chữ nhật", summarize(lambda x: "hình hộp chữ nhật" in x["text"].lower())),
        classify_entry("solid_cube", "Hình lập phương", summarize(lambda x: "lập phương" in x["text"].lower())),
        classify_entry("solid_regular_tetrahedron", "Tứ diện đều", summarize(lambda x: "tứ diện đều" in x["text"].lower())),
        classify_entry("base_right_or_right_iso_triangle", "Đáy tam giác vuông / vuông cân", summarize(lambda x: "vuông cân" in x["text"].lower() or bool(re.search(r"vuông\s+tại", x["text"].lower())))),
        classify_entry("base_equilateral_or_isosceles_triangle", "Đáy tam giác đều / tam giác cân", summarize(lambda x: "tam giác đều" in x["text"].lower() or "tam giác cân" in x["text"].lower())),
        classify_entry("base_square_and_rectangle", "Đáy hình vuông & hình chữ nhật", summarize(lambda x: "hình vuông" in x["text"].lower() or "hình chữ nhật" in x["text"].lower())),
        classify_entry("base_rhombus_parallelogram_trapezoid", "Đáy hình thoi, hình bình hành, hình thang vuông/cân", summarize(lambda x: any(k in x["text"].lower() for k in ("hình thoi", "hình bình hành", "hình thang"))), note="Restricted to contracted regular/metric parameters present in Registry/33"),
        classify_entry("relation_perp_and_face_perp", "Quan hệ vuông góc (cạnh vuông đáy, mặt bên vuông đáy, góc giữa đường-mặt/mặt-mặt)", summarize(lambda x: "vuông góc" in x["text"].lower() or "⊥" in x["text"])),
        classify_entry("relation_parallel", "Quan hệ song song trong không gian (chứng minh/suy khoảng cách đường chéo nhau)", summarize(lambda x: "song song" in x["text"].lower()), force_status="EXPERIMENTAL", note="Dedicated parallel premise wording appears rarely across SLM positive holdouts; deterministic COMP112/RM72 covers parallel constraints on canonical grammar"),
        classify_entry("construction_midpoint", "Trung điểm cạnh (khi hình đáy không bị lược mất ở câu đảo ngữ)", summarize(lambda x: "trung điểm" in x["text"].lower() and "v7h_p8_" not in x["id"])),
        classify_entry("construction_centroid", "Trọng tâm tam giác", summarize(lambda x: "trọng tâm" in x["text"].lower())),
        classify_entry("construction_projection", "Hình chiếu vuông góc lên cạnh / mặt đáy", summarize(lambda x: "hình chiếu" in x["text"].lower())),
        classify_entry("construction_midpoint_centroid_projection_all", "Trung điểm, trọng tâm, hình chiếu (tổng hợp kể cả câu đảo ngữ P8)", summarize(lambda x: any(k in x["text"].lower() for k in ("trung điểm", "trọng tâm", "hình chiếu")))),
        classify_entry("construction_segment_ratio", "Chia đoạn theo tỉ số (SM = k·SC)", summarize(lambda x: "sao cho" in x["text"].lower() or "tỉ số" in x["text"].lower() or "v7h_p6_01" <= x["id"] <= "v7h_p6_05")),
        classify_entry("goal_point_plane_distance", "Khoảng cách từ điểm đến mặt phẳng", summarize(lambda x: "khoảng cách từ" in x["text"].lower() and "đến" in x["text"].lower() and ("mặt" in x["text"].lower() or "(" in x["text"].split("đến")[-1]))),
        classify_entry("goal_skew_lines_distance", "Khoảng cách giữa hai đường thẳng chéo nhau", summarize(lambda x: "chéo nhau" in x["text"].lower() or ("khoảng cách giữa" in x["text"].lower() and "đường thẳng" in x["text"].lower()))),
        classify_entry("goal_line_plane_angle", "Góc giữa đường thẳng và mặt phẳng (mục tiêu cần tính)", summarize(lambda x: bool(re.search(r"(?:tính|tìm)\s+góc\s+giữa\s+(?:đường thẳng\s+)?[A-Z']{2}", x["text"], re.I)))),
        classify_entry("relation_plane_plane_angle_premise", "Góc giữa hai mặt phẳng / góc nhị diện (làm giả thiết xác định chiều cao)", summarize(lambda x: "NH48" in x["source"] and x["family"] == "F5_plane_plane_angle" or "V7H_P4" in x["family"] or ("V7H_P7" in x["family"] and "góc giữa (" in x["text"].lower()))),
        classify_entry("goal_plane_plane_angle", "Góc giữa hai mặt phẳng / góc nhị diện (làm mục tiêu cần tính trên holdout SLM)", summarize(lambda x: infer_goal_kind_from_text(x["text"]) == "angle" and bool(re.search(r"mặt\s*\(|\([A-Z']{3,4}\)\s+và\s+\([A-Z']{3,4}\)", x["text"].split(".")[-2] if "." in x["text"] else x["text"], re.I))), force_status="NOT_MEASURED", note="SLM holdouts (V7H_112, NH48, H40) evaluate plane-plane angle as a PREMISE (`relation_plane_plane_angle_premise`), whereas computing plane-plane angle directly as a GOAL is not sampled in those holdouts (`0/0`; deterministic Parser + Kernel covers `ext_prt_11` separately)."),
        classify_entry("goal_volume_and_area", "Thể tích khối đa diện & diện tích/chiều dài cơ bản", summarize(lambda x: "thể tích" in x["text"].lower() or "diện tích" in x["text"].lower() or "độ dài" in x["text"].lower())),
    ]

    unsupported_or_unmeasured = [
        classify_entry("domain_complex_derived_sections", "Thiết diện suy diễn phức tạp (nhiều bước giao tuyến, cắt khối đa diện tự do)", {"samples": 0, "config_d_passed": 0, "config_d_rate": None, "config_c_passed": 0, "wrong_served": 0, "sources": {}, "sample_ids_failed_in_d": []}, force_status="UNSUPPORTED", note="Outside compact_clause/1 & SLM training; covered separately by K-1 pending owner approval"),
        classify_entry("domain_multi_step_intersection", "Giao tuyến nhiều bước / dựng thiết diện tổng quát", {"samples": 0, "config_d_passed": 0, "config_d_rate": None, "config_c_passed": 0, "wrong_served": 0, "sources": {}, "sample_ids_failed_in_d": []}, force_status="UNSUPPORTED", note="Requires Dynamic Construction Planner (out of /8 scope)"),
        classify_entry("domain_spheres_and_curved_solids", "Mặt cầu ngoại tiếp/nội tiếp, hình nón, hình trụ", {"samples": 0, "config_d_passed": 0, "config_c_passed": 0, "config_d_rate": None, "wrong_served": 0, "sources": {}, "sample_ids_failed_in_d": []}, force_status="UNSUPPORTED", note="Tested as negative OOS traps in SLM_V7_HOLDOUT_112 (correctly refused with 0 false serves); curved geometry disabled/unsupported on local-slm compact_clause"),
        classify_entry("domain_multi_solid_compositions", "Quan hệ nhiều khối hình lồng/ghép đồng thời", {"samples": 0, "config_d_passed": 0, "config_d_rate": None, "config_c_passed": 0, "wrong_served": 0, "sources": {}, "sample_ids_failed_in_d": []}, force_status="UNSUPPORTED", note="Single active solid slot (`s`) in slm-compact-clause/1"),
        classify_entry("domain_non_registry_aux_constructions", "Dựng hình phụ ngoài Registry /33 & Planner tổng quát", {"samples": 0, "config_d_passed": 0, "config_d_rate": None, "config_c_passed": 0, "wrong_served": 0, "sources": {}, "sample_ids_failed_in_d": []}, force_status="UNSUPPORTED", note="Registry /33 & Planner /26 remain blocked/frozen"),
        classify_entry("style_conversational_and_reordered_base", "Đề mở đầu hội thoại + hình đáy đảo câu không chứa từ khóa 'đáy' (`Biết ABCD là hình chữ nhật`)", summarize(lambda x: "v7h_p8_" in x["id"]), force_status="EXPERIMENTAL", note="5/10 passed in V7H P8; 5/5 reordered `Biết <base> là hình chữ nhật` failed via SLM premise omission (`v7h_p8_01..05`), safely refused"),
    ]

    # Attach non-gating negative safety evidence summary
    v7_neg_safe = sum(1 for r in v7_e["configs"]["config_d_v7_closure_finetuned_slm"]["rows"] if r["kind"] == "negative" and r["status"] != "SERVED")
    v7_neg_total = sum(1 for r in v7_e["configs"]["config_d_v7_closure_finetuned_slm"]["rows"] if r["kind"] == "negative")
    return {
        "schema": "slm-capability-matrix/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_key": FINETUNED_LOCAL_SLM_MODEL_KEY,
        "positive_pool_size": len(pool),
        "positive_sources": ["V7H_112 (80 pos, evaluator v2)", "SLM_NEW_HOLDOUT_48 (32 pos)", "HOLDOUT_40 (28 pos)"],
        "negative_safety_reference": {
            "v7h_negatives_safe": f"{v7_neg_safe}/{v7_neg_total}",
            "baseline_suites": {k: v for k, v in v5_bc["suites"].items() if isinstance(v, dict) and "total" in v},
        },
        "supported_domains": supported_matrix,
        "unsupported_and_boundary_domains": unsupported_or_unmeasured,
        "scope_statement": "Local SLM primary eligibility strictly scoped to VALIDATED_LOCAL_PRIMARY Euclidean polyhedron problems above; NEVER promoted to general arbitrary solid geometry or unsupported domains.",
    }


def main() -> int:
    m7 = {c["case_id"]: c for c in json.loads((RUN7_DIR / "SLM_V7_HOLDOUT_MANIFEST.json").read_text(encoding="utf-8"))["cases"]}
    h40 = {c["case_id"]: c for c in json.loads((RUN5_DIR / "independent_slm_holdout_manifest.json").read_text(encoding="utf-8"))["items"]}

    rt = LocalSlmRuntime()
    try:
        # 1. Trace 6 failed positives + 2 passing comparators under Config D
        six_plus_comparators = []
        target_ids = [
            "v7h_p8_01", "v7h_p8_02", "v7h_p8_03", "v7h_p8_04", "v7h_p8_05",
            "v7h_p5_09",
            "v7h_p8_06",  # passing conversational comparator
            "v7h_p5_08",  # passing projection+midpoint comparator
        ]
        for cid in target_ids:
            c = m7[cid]
            gold = _gold_for_p8_06(c["text"]) if cid == "v7h_p8_06" else _gold_slm_for_case(cid, c["text"])
            tr = _trace_case(case_id=cid, text=c["text"], oracle=str(c["oracle"]), model_key=FINETUNED_LOCAL_SLM_MODEL_KEY, runtime=rt, gold_slm=gold)
            tr["13_owner_boundary"] = _classify_owner(tr)
            six_plus_comparators.append(tr)
            print(
                f"[6-CASE AUDIT] {cid}: status={tr['10_kernel_result']['route_status']} "
                f"norm_lp={tr['4_parser_output']['after_normalizer_status']} "
                f"grounding={tr['6_grounding_status']['grounding_status']} "
                f"reason={tr['11_exact_refusal_reason']['route_refusal_code']} "
                f"gold_served={(tr['12_gold_intervention_result'] or {}).get('route_status')}",
                flush=True,
            )

        # 2. Trace slm_h23 Config C vs Config D + 6 sibling blast-radius probes
        h23 = h40["slm_h23_ocr_extra_spaces"]
        h23_c = _trace_case(case_id="slm_h23_ocr_extra_spaces", text=h23["problem_text"], oracle=str(h23["oracle"]), model_key=DEFAULT_LOCAL_SLM_MODEL_KEY, runtime=rt, gold_slm=_gold_slm_for_case("slm_h23_ocr_extra_spaces", h23["problem_text"]))
        h23_d = _trace_case(case_id="slm_h23_ocr_extra_spaces", text=h23["problem_text"], oracle=str(h23["oracle"]), model_key=FINETUNED_LOCAL_SLM_MODEL_KEY, runtime=rt, gold_slm=_gold_slm_for_case("slm_h23_ocr_extra_spaces", h23["problem_text"]))
        h23_d["13_owner_boundary"] = _classify_owner(h23_d)

        # Controlled blast-radius probes
        sibling_prompts = [
            ("probe_clean_the_tich", "Cho hình chóp S.ABC có đáy ABC đều cạnh 2a, SA vuông góc với (ABC), SA=3a. Tính thể tích khối chóp S.ABC."),
            ("probe_ocr_the_tich", "Cho hình chóp S.ABC có đáy ABC đều cạnh 2a , SA vuông góc với ( ABC ) , SA = 3a . Tính thể tích S.ABC."),
            ("probe_clean_V_cua", "Cho hình chóp S.ABC có đáy ABC đều cạnh 2a, SA vuông góc với (ABC), SA=3a. Tính V của S.ABC."),
            ("probe_ocr_V_cua", "Cho hình chóp S.ABC có đáy ABC đều cạnh 2a , SA vuông góc với ( ABC ) , SA = 3a . Tính V của S.ABC."),
            ("probe_ocr_la_tam_giac_deu", "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2a , SA vuông góc với ( ABC ) , SA = 3a . Tính thể tích khối chóp S.ABC."),
            ("probe_reordered_rect_with_day_kw", "Thưa thầy, nhờ giải bài: Cho khối chóp H.UVWX có cạnh HU vuông góc với (UVWX) và HU=3a. Biết đáy UVWX là hình chữ nhật với UV=a√2, VW=2a. Lấy T là trung điểm WX. Hãy tìm khoảng cách từ điểm T đến (HVW)."),
        ]
        probe_results = []
        for pid, ptxt in sibling_prompts:
            tr = _trace_case(case_id=pid, text=ptxt, oracle="a³√3" if "S.ABC" in ptxt else str(m7["v7h_p8_01"]["oracle"]), model_key=FINETUNED_LOCAL_SLM_MODEL_KEY, runtime=rt)
            probe_results.append({
                "probe_id": pid,
                "text": ptxt,
                "norm_text": tr["2_normalized_text"],
                "parser_after_norm": tr["4_parser_output"]["after_normalizer_status"],
                "slm_invoked": tr["5_compact_slm_output"]["slm_invoked"],
                "slm_json": tr["5_compact_slm_output"]["parsed_json"],
                "grounding_status": tr["6_grounding_status"]["grounding_status"],
                "route_status": tr["10_kernel_result"]["route_status"],
                "answer": tr["10_kernel_result"]["answer"],
                "refusal_code": tr["11_exact_refusal_reason"]["route_refusal_code"],
            })
            print(f"[PROBE] {pid}: status={tr['10_kernel_result']['route_status']} slm_invoked={tr['5_compact_slm_output']['slm_invoked']} grounding={tr['6_grounding_status']['grounding_status']} slm={tr['5_compact_slm_output']['parsed_json']}")

        traces_out = {
            "schema": "slm-failure-audit-traces/1",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "six_unresolved_v7_cases_and_comparators": six_plus_comparators,
            "slm_h23_regression": {
                "config_c_original_qwen": h23_c,
                "config_d_finetuned_axov7": h23_d,
            },
            "controlled_blast_radius_probes": probe_results,
        }
        (OUT_DIR / "SLM_FAILURE_AUDIT_TRACES.json").write_text(
            json.dumps(traces_out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        matrix = _build_capability_matrix()
        (OUT_DIR / "SLM_CAPABILITY_MATRIX.json").write_text(
            json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print("CAPABILITY MATRIX SUMMARY:")
        for e in matrix["supported_domains"] + matrix["unsupported_and_boundary_domains"]:
            ev = e["evidence"]
            print(f"  {e['status']:24s} | {e['category']:42s} | {ev['config_d_passed']}/{ev['samples']} ({ev['config_d_rate']})")
    finally:
        rt.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
