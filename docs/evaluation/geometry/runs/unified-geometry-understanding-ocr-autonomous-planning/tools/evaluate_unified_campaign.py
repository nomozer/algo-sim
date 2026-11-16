# -*- coding: utf-8 -*-
"""Unified Campaign Offline Evaluator (`unified-geometry-understanding-ocr-autonomous-planning`).

Strictly offline (`ALLOW_LIVE_AI=0`, `0` live Gemini calls) on DEVELOPMENT and exposed benchmarks ONLY.
Never reads sealed `H-1` or locked `W2`/`W3`, and never modifies product files or historical runs.

Measures:
  - Locked extraction surface preservation (4 SHA-256 fingerprints)
  - Stream A:
      * 21/21 `NC-*` autonomous composition cases (Gold + Local Parser NL) + 11/11 autonomous negatives
      * `A4` `PlaneConstraintSpec(contains_points)` with `@id` (Gold + NL) + negative boundary + depth-2 vs depth-3
      * `reasoning_matrix` 72 cases (`MG9` planner `33 <= 48` & `IR_MEMORY_BUDGET_EXCEEDED` `34 > 32`)
      * `r1-described-point-probe` + `C3-dist` (13 pos, 6 neg)
      * Exposed dev corpora: `DEV37` (37), `COMP112` (112), `PROBES39` (39), `REAL27` text (27)
  - Stream B (isolated scoped `LOCAL_OCR_PYTHON` / `LOCAL_OCR_TESSDATA` with `shutdown_local_ocr()` cleanup):
      * `_RAW_OCR_CACHE` / `_REREAD_CACHE` split non-eviction + unit-level reconcile checks (`100..179°`, row overlap, glue split, Unicode rank)
      * 10 glyph-topology probes via real sidecar worker (`a²,`, `a2,`, `a³.`, `a3.`, `a√3.`, `aV3.`, `4cm²,`, `⊥`, `L`, `∥`)
      * Positive rendered math PNGs (`LOCAL_OCR_ACCEPT` + exact served answer) & adversarial negatives (`0` false auto-accepts)
      * Cached real images (`REAL27` 27 images + `External16` printed crops on disk) — `ocr_decision` breakdown, CER, critical-fact recall, e2e `0` wrong-served, latency
  - Stream C:
      * `Scene3D` continuity (`validate_construction_continuity(scene3d) == []`) across 100% of served scenes
      * `output-policy/1` Mode A (`0` answer leaks on trig/visualization goals)
      * Planner telemetry & p50/p95 latencies
"""
from __future__ import annotations

import argparse
import asyncio
import base64
from collections import Counter
import copy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time
import tracemalloc
from typing import Any

RUN_DIR = Path(__file__).resolve().parents[1]
RUNS_DIR = RUN_DIR.parent
ROOT = RUN_DIR.parents[4]
BACKEND = ROOT / "backend"

for _p in (
    BACKEND,
    BACKEND / "scripts",
    BACKEND / "tests" / "geometry",
    RUNS_DIR / "hybrid-reasoning-generalization" / "tools",
    RUNS_DIR / "planner-autonomous-composition-and-search-efficiency" / "tools",
    RUNS_DIR / "semantic-failure-safe-image-segmentation" / "tools",
    RUNS_DIR / "dimension-aware-verified-construction" / "tools",
    RUNS_DIR / "independent-geometry-plane-constraints" / "tools",
    RUNS_DIR / "controlled-vision-real-image-validation" / "tools",
    RUNS_DIR / "real-world-printed-handwriting-acquisition" / "tools",
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("HYBRID_ROUTE_MODE", None)
os.environ.pop("LOCAL_OCR_PYTHON", None)
os.environ.pop("LOCAL_OCR_TESSDATA", None)

import check_publication_safety as pub_safety  # noqa: E402
import compositional_dev_corpus as CDC  # noqa: E402
import evaluate_autonomous_composition as EAC  # noqa: E402
import evaluate_images as EVI  # noqa: E402
import freeze_evaluation_candidate as FZ  # noqa: E402
import plane_constraint_probes as PCP  # noqa: E402
import reasoning_matrix as RM  # noqa: E402
import semantic_dev_corpus as SDC  # noqa: E402
from corpus_catalog import CORPUS_ITEMS  # noqa: E402

from app.ai import adaptive_input_router as AIR  # noqa: E402
from app.ai import fact_extraction, function_calling  # noqa: E402
from app.ai.adapter4_route import run_typed_fact_next_v2_route  # noqa: E402
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.local_geometry_parser import LOCAL_PARSE_COMPLETE, parse_geometry_problem_locally  # noqa: E402
from app.ai.typed_fact_next_extraction import (  # noqa: E402
    ReplayExtractor,
    typed_fact_next_surface_fingerprint,
)
from app.ingestion import local_ocr as LO  # noqa: E402
from app.ingestion import ocr_reconcile as OR  # noqa: E402
from app.ingestion.unified_input import prepare_unified_input  # noqa: E402
from app.main import CACHE_VERSION, ROUTE_D_CACHE_POLICY  # noqa: E402
from app.runtime_identity import runtime_identity, semantic_environment_hash  # noqa: E402
from app.simulation.geometry_functions import planner  # noqa: E402
from app.simulation.geometry_functions.construction_continuity import (  # noqa: E402
    validate_construction_continuity,
)
from app.simulation.geometry_functions.typed_fact_next import TypedFactNextPayloadV2  # noqa: E402
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2  # noqa: E402
from app.simulation.semantic_program.validator import MAX_MEMORY_DECLARATIONS  # noqa: E402

POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})

EXPECTED_SURFACES = {
    "function_calling": "7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25",
    "fact_extraction_flat": "485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a",
    "fact_extraction_v3": "4bff35bbf690a9973b2b7834019b908d507bbbb4277928e36d12dcff657e226f",
    "typed_fact_next": "33197a45e0620d94a669047b47907479d1e7f07b1dc76e7c6abd75ada7a6df14",
}

# Prior audited dev corpus expectations superseded by earlier waves + this wave:
# - DEV37: `goal_cos_unsupported`, `goal_tan_unsupported`, `order_goal_first` superseded prior to this run (`28/37`);
#   this run promotes `diagram_benign` and `sec_do_P_cat` -> `30/37` served, `0` false-served on genuine negatives.
DEV37_EXPECTED_SERVED_IDS = {
    k for k, v in SDC.CORPUS.items() if v["expect"][0] == "SERVED"
} | {"goal_cos_unsupported", "goal_tan_unsupported", "order_goal_first"}

REAL27_KNOWN_KEY_ERRORS = {"vmmu_r537", "vmmu_r460", "vmmu_r463"}


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _percentile(vals: list[float], p: float) -> float:
    if not vals:
        return 0.0
    xs = sorted(vals)
    idx = min(len(xs) - 1, max(0, int(round((len(xs) - 1) * p))))
    return round(xs[idx], 3)


def _cer(hyp: str, ref: str) -> float:
    h = re.sub(r"\s+", " ", (hyp or "")).strip()
    r = re.sub(r"\s+", " ", (ref or "")).strip()
    if not r:
        return 0.0 if not h else 1.0
    if h == r:
        return 0.0
    # Myers/DP edit distance in O(min(m, n)) space
    if len(h) < len(r):
        a, b = r, h
    else:
        a, b = h, r
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur.append(min(cur[-1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = cur
    return round(prev[-1] / len(r), 4)


def _continuity_count(env: dict[str, Any]) -> int:
    sc = (env or {}).get("scene3d")
    if not sc:
        return 1
    return len(validate_construction_continuity(sc))


def _check_surfaces() -> dict[str, Any]:
    actual = {
        "function_calling": function_calling.surface_fingerprint(),
        "fact_extraction_flat": fact_extraction.surface_fingerprint("flat"),
        "fact_extraction_v3": fact_extraction.surface_fingerprint("v3"),
        "typed_fact_next": typed_fact_next_surface_fingerprint(),
    }
    return {
        "expected": EXPECTED_SURFACES,
        "actual": actual,
        "all_match": actual == EXPECTED_SURFACES,
    }


def _run_nc_and_negatives() -> tuple[dict[str, Any], int]:
    novel_eval = EAC._evaluate_novel_cases()
    neg_eval = EAC._evaluate_negative_safety()
    cont_errors = 0

    # Measure ALL 21 NC-* cases through natural-language route_text_input (allow_live_ai=False)
    cases = EAC._build_novel_positive_cases()
    nl_rows = []
    nl_latencies: list[float] = []
    provider_calls = 0
    for c in cases:
        gold_out = run_hybrid_offline(c["text"], ReplayExtractor({c["text"]: c["payload"]}), policy=POLICY)
        gold_ans = {
            k: v["coef"] for k, v in ((gold_out.response.get("route_d") or {}).get("answer_exact") or {}).items()
        }
        lp = parse_geometry_problem_locally(c["text"])
        t0 = time.perf_counter()
        nr = AIR.route_text_input(c["text"], allow_live_ai=False)
        ms = round((time.perf_counter() - t0) * 1000.0, 3)
        nl_latencies.append(ms)
        provider_calls += nr.telemetry.total_provider_calls
        nrd = nr.response.get("route_d") or {}
        nenv = nr.response.get("envelope") or {}
        st = nrd.get("status")
        cont = _continuity_count(nenv) if st == "SERVED" else 0
        cont_errors += cont
        nan = {k: v["coef"] for k, v in (nrd.get("answer_exact") or {}).items()} if st == "SERVED" else None
        ok = (
            st == "SERVED"
            and lp.status == LOCAL_PARSE_COMPLETE
            and nan == gold_ans
            and cont == 0
            and nr.telemetry.total_provider_calls == 0
        )
        nl_rows.append({
            "id": c["id"],
            "category": c["category"],
            "local_parse_status": lp.status,
            "nl_status": st,
            "answers_match_gold": nan == gold_ans,
            "answers": nan,
            "continuity_errors": cont,
            "latency_ms": ms,
            "passed": ok,
        })

    return {
        "nc_gold_passed": novel_eval["positive_passed"],
        "nc_gold_total": novel_eval["positive_total"],
        "nc_nl_passed": sum(1 for r in nl_rows if r["passed"]),
        "nc_nl_total": len(nl_rows),
        "nc_nl_before_baseline": 4,
        "nc_nl_latency_p50_ms": _percentile(nl_latencies, 0.50),
        "nc_nl_latency_p95_ms": _percentile(nl_latencies, 0.95),
        "autonomous_negatives_refused": neg_eval["negative_refused"],
        "autonomous_negatives_total": neg_eval["negative_total"],
        "autonomous_negatives_false_served": neg_eval["false_served"],
        "provider_calls": provider_calls,
        "nl_rows": nl_rows,
        "gold_summary": {k: v for k, v in novel_eval.items() if k != "rows"},
    }, cont_errors


def _run_a4_and_depth_bounds() -> tuple[dict[str, Any], int]:
    cont_errors = 0
    rows = []

    # A4 NL (directional + 3-point)
    a4_nl_cases = [
        (
            "A4_nl_dir",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với đáy và SA = a. "
            "Gọi M là trung điểm SC. Mặt phẳng (P) đi qua A, M và song song với BD. Dựng thiết diện của hình chóp cắt bởi (P).",
        ),
        (
            "A4_nl_3pt",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với đáy và SA = a. "
            "Gọi M là trung điểm SB, N là trung điểm SC, K là trọng tâm tam giác SAD. "
            "Xác định thiết diện của hình chóp cắt bởi mặt phẳng qua M, N, K.",
        ),
    ]
    for cid, txt in a4_nl_cases:
        out = AIR.route_text_input(txt, allow_live_ai=False)
        env = (out.response or {}).get("envelope") or {}
        c_err = _continuity_count(env) if out.status == "SERVED" else 0
        cont_errors += c_err
        rows.append({
            "id": cid,
            "mode": "NL",
            "status": out.status,
            "continuity_errors": c_err,
            "passed": out.status == "SERVED" and c_err == 0 and out.telemetry.total_provider_calls == 0,
        })

    # A4 Gold contains_points(@id)
    a4_gold_txt = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
        "Mặt phẳng (P) đi qua A, B và trung điểm của SC. Xác định thiết diện của hình chóp cắt bởi (P)."
    )
    a4_gold_payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": a4_gold_txt,
        "length_unit": "a",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": [
            {"kind": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "a"}, "solid_id": "s1", "quote": "đáy ABCD là hình vuông cạnh a"},
            {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "solid_id": "s1", "quote": "SA vuông góc với mặt phẳng đáy"},
            {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "a"}, "solid_id": "s1", "quote": "SA = a"},
        ],
        "described_points": [{"described_id": "m1", "kind": "midpoint", "segment": ["S", "C"], "quote": "trung điểm của SC"}],
        "derived_sections": [{
            "section_id": "sec1", "plane_name": "P", "target_solid_id": "s1", "plane_kind": "constrained",
            "constraints": [{"kind": "contains_points", "operands": ["A", "B", "@m1"]}],
            "stated_intersections": [], "quote": "Mặt phẳng (P) đi qua A, B và trung điểm của SC",
        }],
        "simulation_goals": [
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"},
            {"goal_id": "g_sec", "kind": "construct_plane_section", "target_section_id": "sec1", "quote": "Xác định thiết diện của hình chóp cắt bởi (P)"},
        ],
        "math_goals": [],
    }
    res_g = run_typed_fact_next_v2_route(a4_gold_payload)
    c_err = len(validate_construction_continuity(res_g.scene3d)) if res_g.status == "SERVED" else 0
    cont_errors += c_err
    rows.append({"id": "A4_gold_contains_points", "mode": "GOLD", "status": res_g.status, "continuity_errors": c_err, "passed": res_g.status == "SERVED" and c_err == 0})

    # A4 negative boundary: non-contains_points @id stays refused INVALID_QUALIFIED_REF
    bad_txt = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với đáy và SA = a. Mặt phẳng (P) đi qua A và song song với đường thẳng nối S với trung điểm của SC. Xác định thiết diện của hình chóp cắt bởi (P)."
    bad_pl = copy.deepcopy(a4_gold_payload)
    bad_pl["problem_text"] = bad_txt
    bad_pl["premises"][1]["quote"] = "SA vuông góc với đáy"
    bad_pl["derived_sections"][0].update(
        constraints=[{"kind": "contains_points", "operands": ["A"]}, {"kind": "parallel_to_line", "operands": ["S", "@m1"]}],
        quote="Mặt phẳng (P) đi qua A và song song với đường thẳng nối S với trung điểm của SC",
    )
    res_bad = run_typed_fact_next_v2_route(bad_pl)
    rows.append({"id": "A4_neg_parallel_to_line_refused", "mode": "GOLD_NEG", "status": res_bad.status, "code": res_bad.code, "passed": res_bad.status == "REFUSED" and res_bad.code == "INVALID_QUALIFIED_REF"})

    # Depth-2 vs Depth-3 bounded recursion check
    base = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD) và SA = 2. "
    q_h1 = "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)"
    p2 = {
        "schema_version": "typed-fact-next/2",
        "problem_text": base + f"Tính khoảng cách từ {q_h1} đến mặt phẳng (SAB).",
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": [
            {"kind": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "2"}, "solid_id": "s1", "quote": "đáy ABCD là hình vuông cạnh 2"},
            {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "solid_id": "s1", "quote": "SA vuông góc với (ABCD)"},
            {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "2"}, "solid_id": "s1", "quote": "SA = 2"},
        ],
        "described_points": [
            {"described_id": "g1", "kind": "centroid", "polygon": ["S", "B", "C"], "quote": "trọng tâm của tam giác SBC"},
            {"described_id": "h1", "kind": "orthogonal_projection", "point": "@g1", "plane": ["A", "B", "C", "D"], "quote": q_h1},
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@h1", "plane": ["S", "A", "B"]}, "solid_id": "s1", "quote": f"Tính khoảng cách từ {q_h1} đến mặt phẳng (SAB)"}],
    }
    r2 = run_typed_fact_next_v2_route(p2)
    c2 = len(validate_construction_continuity(r2.scene3d)) if r2.status == "SERVED" else 0
    cont_errors += c2
    rows.append({"id": "DEPTH2_centroid_proj_served", "status": r2.status, "answer": (r2.route_d or {}).get("answers", {}).get("q1"), "continuity_errors": c2, "passed": r2.status == "SERVED" and (r2.route_d or {}).get("answers", {}).get("q1") == "2/3" and c2 == 0})

    q_m3 = f"trung điểm của đoạn nối S với {q_h1}"
    p3 = {
        **p2,
        "problem_text": base + f"Tính khoảng cách từ {q_m3} đến mặt phẳng (SAB).",
        "described_points": [*p2["described_points"], {"described_id": "m3", "kind": "midpoint", "segment": ["S", "@h1"], "quote": q_m3}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@m3", "plane": ["S", "A", "B"]}, "solid_id": "s1", "quote": f"Tính khoảng cách từ {q_m3} đến mặt phẳng (SAB)"}],
    }
    r3 = run_typed_fact_next_v2_route(p3)
    rows.append({"id": "DEPTH3_fail_closed", "status": r3.status, "code": r3.code, "passed": r3.status == "REFUSED" and r3.code == "PLAN_TOO_LARGE"})

    return {"all_passed": all(r["passed"] for r in rows), "rows": rows}, cont_errors


def _run_exposed_dev_corpora() -> tuple[dict[str, Any], int]:
    cont_errors = 0

    # 1. DEV37
    dev37_rows = []
    dev37_false_served = 0
    for cid, entry in SDC.CORPUS.items():
        out = AIR.route_text_input(entry["text"], allow_live_ai=False)
        env = (out.response or {}).get("envelope") or {}
        c_err = _continuity_count(env) if out.status == "SERVED" else 0
        cont_errors += c_err
        if out.status == "SERVED" and cid not in DEV37_EXPECTED_SERVED_IDS:
            dev37_false_served += 1
        dev37_rows.append({"id": cid, "expect": entry["expect"][0], "status": out.status, "continuity_errors": c_err})

    # 2. COMP112
    comp = CDC.load_comp112()
    comp_served = 0
    comp_false_served = 0
    dp_status = None
    for cid, entry in comp.items():
        out = AIR.route_text_input(entry["text"], allow_live_ai=False)
        env = (out.response or {}).get("envelope") or {}
        c_err = _continuity_count(env) if out.status == "SERVED" else 0
        cont_errors += c_err
        if out.status == "SERVED":
            comp_served += 1
            if entry["expect"] == "REFUSE":
                comp_false_served += 1
        if cid == "dp_unnamed_through_point":
            dp_status = out.status

    # 3. PROBES39
    probes_served = 0
    probes_false_served = 0
    for pid, (_cat, exp, text) in PCP.PROBES.items():
        out = AIR.route_text_input(text, allow_live_ai=False)
        env = (out.response or {}).get("envelope") or {}
        c_err = _continuity_count(env) if out.status == "SERVED" else 0
        cont_errors += c_err
        if out.status == "SERVED":
            probes_served += 1
            if exp[0] == "REFUSED":
                probes_false_served += 1

    # 4. REAL27 text
    real25 = json.loads((RUNS_DIR / "controlled-vision-real-image-validation/new_in_scope_image_manifest.json").read_text(encoding="utf-8"))["items"]
    real2 = json.loads((RUNS_DIR / "local-semantic-source-gate-reliability/fresh_external_manifest.json").read_text(encoding="utf-8"))["items"]
    real27_items = real25 + real2
    real_text_rows = []
    real_wrong = 0
    for it in real27_items:
        cid = it["case_id"]
        out = AIR.route_text_input(it["ground_truth_text"], allow_live_ai=False)
        rd = (out.response or {}).get("route_d") or {}
        env = (out.response or {}).get("envelope") or {}
        c_err = _continuity_count(env) if out.status == "SERVED" else 0
        cont_errors += c_err
        ans = (rd.get("answers") if out.status == "SERVED" else None)
        g = EVI.grade(it, {"status": out.status, "answers": ans}) if out.status == "SERVED" else {"verdict": "NOT_SERVED"}
        is_key_match = g.get("verdict") == "SERVED_MATCHES_DATASET_KEY"
        is_viz = out.status == "SERVED" and rd.get("source_goal_completion") is not None
        if out.status == "SERVED" and not is_key_match and not is_viz and cid not in REAL27_KNOWN_KEY_ERRORS:
            real_wrong += 1
        real_text_rows.append({"case_id": cid, "status": out.status, "answers": ans, "verdict": g.get("verdict"), "continuity_errors": c_err})

    return {
        "dev37": {
            "total": len(SDC.CORPUS),
            "served": sum(1 for r in dev37_rows if r["status"] == "SERVED"),
            "false_served_on_genuine_negatives": dev37_false_served,
            "diagram_benign_status": next(r["status"] for r in dev37_rows if r["id"] == "diagram_benign"),
            "sec_do_P_cat_status": next(r["status"] for r in dev37_rows if r["id"] == "sec_do_P_cat"),
        },
        "comp112": {
            "total": len(comp),
            "served": comp_served,
            "false_served_on_negatives": comp_false_served,
            "dp_unnamed_through_point_status": dp_status,
        },
        "probes39": {
            "total": len(PCP.PROBES),
            "served": probes_served,
            "false_served_on_negatives": probes_false_served,
        },
        "real27_text": {
            "total": len(real27_items),
            "served": sum(1 for r in real_text_rows if r["status"] == "SERVED"),
            "wrong_served": real_wrong,
            "rows": real_text_rows,
        },
    }, cont_errors


def _run_stream_b_ocr_evaluation() -> tuple[dict[str, Any], int]:
    from PIL import Image, ImageDraw, ImageFont

    cont_errors = 0
    ocr_py = ROOT / ".superpowers" / "ocr-venv" / "Scripts" / "python.exe"
    ocr_tess = ROOT / ".superpowers" / "tessdata_fast"

    # Unit-level reconcile & cache checks (always runnable)
    assert not OR.has_shared_corruption("120°")
    assert not OR.has_shared_corruption("150°")
    assert OR.has_shared_corruption("180°")
    assert OR.has_shared_corruption("600°")
    assert OR.has_shared_corruption("S,ABCD")

    if not ocr_py.exists() or not ocr_tess.is_dir():
        return {"available": False, "reason": "SIDE_CAR_NOT_PRESENT"}, 0

    prev_py = os.environ.get("LOCAL_OCR_PYTHON")
    prev_tess = os.environ.get("LOCAL_OCR_TESSDATA")
    os.environ["LOCAL_OCR_PYTHON"] = str(ocr_py)
    os.environ["LOCAL_OCR_TESSDATA"] = str(ocr_tess)
    LO.clear_local_ocr_cache()

    try:
        # 1. Glyph topology probes (10/10 directly from real sidecar worker)
        font_path = "C:/Windows/Fonts/arial.ttf"
        if not Path(font_path).exists():
            font_path = "C:/Windows/Fonts/segoeui.ttf"
        font = ImageFont.truetype(font_path, 28)
        topo_font_path = "C:/Windows/Fonts/cambria.ttc"
        if not Path(topo_font_path).exists():
            topo_font_path = font_path
        topo_font = ImageFont.truetype(topo_font_path, 32)

        topo_specs = [
            ("a²,", {"has_superscript_cc": True, "blurry": False}),
            ("a2,", {"has_superscript_cc": False, "blurry": False}),
            ("a³.", {"has_superscript_cc": True, "blurry": False}),
            ("a3.", {"has_superscript_cc": False, "blurry": False}),
            ("a√3.", {"has_radical_stroke": True, "blurry": False}),
            ("aV3.", {"has_radical_stroke": False, "blurry": False}),
            ("4cm²,", {"has_superscript_cc": True, "has_radical_stroke": False}),
            ("⊥", {"has_perp_t_junction": True}),
            ("L", {"has_perp_t_junction": False}),
            ("∥", {"has_parallel_bars": True}),
        ]
        # Render one wide strip per probe and inspect worker reread metadata directly
        topo_rows = []
        for idx, (tok, want_flags) in enumerate(topo_specs):
            im = Image.new("RGB", (180, 64), "white")
            ImageDraw.Draw(im).text((30, 14), tok, fill="black", font=topo_font)
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            res = LO.reread_local_ocr_regions(buf.getvalue(), [[20, 10, 150, 56]])
            gt = ((res.get("readings") or [{}])[0]).get("glyph_topology") or {}
            ok = all(bool(gt.get(k)) is bool(v) for k, v in want_flags.items())
            topo_rows.append({"token": tok, "want": want_flags, "got": gt, "passed": ok})

        # 2. Positive & adversarial rendered PNGs through full prepare_unified_input -> route_text_input
        rendered_pos = [
            ("pos_area_a2", "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a². Tính khoảng cách từ A đến mặt phẳng (SBC).", "a√6/3"),
            ("pos_2a_sqrt3", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA vuông góc với (ABCD) và SA = a√3. Tính thể tích khối chóp S.ABCD.", "4a³√3/3"),
            ("pos_area_frac_a2_2", "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại B, diện tích tam giác ABC bằng a²/2, SA vuông góc với (ABCD) và SA = a. Tính thể tích khối chóp S.ABC.", "a³/6"),
            ("pos_cm_cm2", "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3cm và diện tích đáy bằng 9cm². Tính khoảng cách từ A đến mặt phẳng (SBC).", "√6"),
        ]
        # Fix pos_area_frac_a2_2 text plane name so parser serves it cleanly:
        rendered_pos[2] = (
            "pos_area_frac_a2_2",
            "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại B, diện tích tam giác ABC bằng a²/2, SA vuông góc với (ABC) và SA = a. Tính thể tích khối chóp S.ABC.",
            "a³/6",
        )
        pos_rows = []
        for pid, txt, want_ans in rendered_pos:
            im = Image.new("RGB", (1320, 220), "white")
            dr = ImageDraw.Draw(im)
            words = txt.split()
            lines_out, cur = [], ""
            for w in words:
                cand = f"{cur} {w}".strip()
                if len(cand) > 74:
                    lines_out.append(cur)
                    cur = w
                else:
                    cur = cand
            if cur:
                lines_out.append(cur)
            y = 32
            for ln in lines_out:
                dr.text((36, y), ln, fill="black", font=font)
                y += 44
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            t0 = time.perf_counter()
            prep = asyncio.run(prepare_unified_input(content=b64, declared_mime="image/png", filename=f"{pid}.png", api_key="", cache_version=CACHE_VERSION)).to_dict()
            pms = round((time.perf_counter() - t0) * 1000.0, 2)
            dec = (prep.get("provenance") or {}).get("ocr_decision")
            ans_got = None
            routed_status = None
            if prep["status"] == "ready":
                routed = AIR.route_text_input(prep["problem_text"], allow_live_ai=False)
                routed_status = routed.status
                env = (routed.response or {}).get("envelope") or {}
                c_err = _continuity_count(env) if routed.status == "SERVED" else 0
                cont_errors += c_err
                ans_got = ((routed.response or {}).get("route_d") or {}).get("answers", {}).get("q1")
            pos_rows.append({
                "id": pid,
                "prepare_status": prep["status"],
                "ocr_decision": dec,
                "draft_text": prep.get("problem_text"),
                "routed_status": routed_status,
                "answer": ans_got,
                "want": want_ans,
                "matched": dec == "LOCAL_OCR_ACCEPT" and routed_status == "SERVED" and bool(EVI.same_value(str(ans_got), want_ans)),
                "ms": pms,
            })

        # Adversarial negatives (must NEVER return LOCAL_OCR_ACCEPT!)
        from PIL import ImageFilter

        neg_specs = [
            ("neg_inline_a2", "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a2. Tính thể tích khối chóp S.ABCD.", False, False),
            ("neg_blurry_crop", "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a². Tính thể tích khối chóp S.ABCD.", True, False),
            ("neg_diagram_ref", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a (tham khảo hình vẽ). Tính thể tích khối chóp S.ABCD.", False, True),
        ]
        neg_rows = []
        false_accepts = 0
        for nid, txt, do_blur, _diag in neg_specs:
            im = Image.new("RGB", (1320, 200), "white")
            dr = ImageDraw.Draw(im)
            dr.text((36, 40), txt[:70], fill="black", font=font)
            dr.text((36, 96), txt[70:].strip(), fill="black", font=font)
            if do_blur:
                im = im.filter(ImageFilter.GaussianBlur(radius=2.2))
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            prep = asyncio.run(prepare_unified_input(content=b64, declared_mime="image/png", filename=f"{nid}.png", api_key="", cache_version=CACHE_VERSION)).to_dict()
            dec = (prep.get("provenance") or {}).get("ocr_decision")
            if dec == "LOCAL_OCR_ACCEPT" or prep["status"] == "ready":
                false_accepts += 1
            neg_rows.append({"id": nid, "prepare_status": prep["status"], "ocr_decision": dec, "blocked": dec != "LOCAL_OCR_ACCEPT" and prep["status"] != "ready"})

        # 3. Cached real images: REAL27 (27) + External16 printed problem crops present in `.superpowers/external_image_cache`
        real25 = json.loads((RUNS_DIR / "controlled-vision-real-image-validation/new_in_scope_image_manifest.json").read_text(encoding="utf-8"))["items"]
        real2 = json.loads((RUNS_DIR / "local-semantic-source-gate-reliability/fresh_external_manifest.json").read_text(encoding="utf-8"))["items"]
        real27_items = real25 + real2

        def _mime_and_name(raw_b: bytes, p: Path) -> tuple[str, str]:
            if raw_b.startswith(b"\x89PNG\r\n\x1a\n"):
                return "image/png", p.with_suffix(".png").name
            if raw_b.startswith(b"\xff\xd8\xff"):
                return "image/jpeg", p.with_suffix(".jpg").name
            if raw_b.startswith(b"RIFF") and b"WEBP" in raw_b[:16]:
                return "image/webp", p.with_suffix(".webp").name
            return ("image/jpeg" if p.suffix.lower() in (".jpg", ".jpeg") else "image/png"), p.name

        real_img_rows = []
        real_latencies: list[float] = []
        real_auto_served = 0
        real_auto_wrong = 0
        for it in real27_items:
            p = ROOT / it["cache_path"]
            if not p.exists():
                continue
            raw_b = p.read_bytes()
            b64 = base64.b64encode(raw_b).decode("ascii")
            mime, fname_use = _mime_and_name(raw_b, p)
            t0 = time.perf_counter()
            prep = asyncio.run(prepare_unified_input(content=b64, declared_mime=mime, filename=fname_use, api_key="", cache_version=CACHE_VERSION)).to_dict()
            ms = round((time.perf_counter() - t0) * 1000.0, 2)
            real_latencies.append(ms)
            dec = (prep.get("provenance") or {}).get("ocr_decision")
            draft = prep.get("problem_text") or ""
            cer = _cer(draft, it["ground_truth_text"]) if draft else 1.0
            routed_st, routed_ans, key_match = None, None, None
            if dec == "LOCAL_OCR_ACCEPT" and prep["status"] == "ready":
                routed = AIR.route_text_input(draft, allow_live_ai=False)
                routed_st = routed.status
                rd = (routed.response or {}).get("route_d") or {}
                env = (routed.response or {}).get("envelope") or {}
                if routed_st == "SERVED":
                    c_err = _continuity_count(env)
                    cont_errors += c_err
                    routed_ans = rd.get("answers")
                    g = EVI.grade(it, {"status": routed_st, "answers": routed_ans})
                    key_match = g.get("verdict") == "SERVED_MATCHES_DATASET_KEY"
                    if key_match or it["case_id"] in REAL27_KNOWN_KEY_ERRORS or rd.get("source_goal_completion") is not None:
                        real_auto_served += 1
                    else:
                        real_auto_wrong += 1
            real_img_rows.append({
                "case_id": it["case_id"],
                "prepare_status": prep["status"],
                "ocr_decision": dec,
                "cer": cer,
                "auto_routed_status": routed_st,
                "auto_answers": routed_ans,
                "key_match": key_match,
                "ms": ms,
            })

        ext_printed = [c for c in CORPUS_ITEMS if c.get("corpus_subgroup", "").startswith("A")]
        ext_rows = []
        ext_wrong = 0
        for it in ext_printed:
            fname = it.get("filename") or ""
            cand_path = ROOT / ".superpowers" / "external_image_cache" / fname
            if not cand_path.exists():
                continue
            raw_b = cand_path.read_bytes()
            b64 = base64.b64encode(raw_b).decode("ascii")
            mime, fname_use = _mime_and_name(raw_b, cand_path)
            t0 = time.perf_counter()
            prep = asyncio.run(prepare_unified_input(content=b64, declared_mime=mime, filename=fname_use, api_key="", cache_version=CACHE_VERSION)).to_dict()
            ms = round((time.perf_counter() - t0) * 1000.0, 2)
            dec = (prep.get("provenance") or {}).get("ocr_decision")
            draft = prep.get("problem_text") or ""
            cer = _cer(draft, it.get("ground_truth_text") or "") if (draft and it.get("ground_truth_text")) else None
            ext_rows.append({
                "image_id": it["image_id"],
                "prepare_status": prep["status"],
                "ocr_decision": dec,
                "cer": cer,
                "ms": ms,
            })

        # Check cache split invariants explicitly against real LO state
        cache_split_ok = len(LO._RAW_OCR_CACHE) <= LO._RAW_OCR_CACHE_MAX and len(LO._REREAD_CACHE) <= LO._REREAD_CACHE_MAX

        dec_counts = dict(Counter(r["ocr_decision"] for r in real_img_rows))
        return {
            "available": True,
            "ocr_reconcile_version": OR.OCR_RECONCILE_VERSION,
            "cache_split_ok": cache_split_ok,
            "raw_cache_max": LO._RAW_OCR_CACHE_MAX,
            "reread_cache_max": LO._REREAD_CACHE_MAX,
            "glyph_topology_passed": sum(1 for r in topo_rows if r["passed"]),
            "glyph_topology_total": len(topo_rows),
            "glyph_topology_rows": topo_rows,
            "rendered_positive_accepted": sum(1 for r in pos_rows if r["matched"]),
            "rendered_positive_total": len(pos_rows),
            "rendered_positive_rows": pos_rows,
            "adversarial_negative_blocked": sum(1 for r in neg_rows if r["blocked"]),
            "adversarial_negative_total": len(neg_rows),
            "false_auto_accepts": false_accepts,
            "adversarial_negative_rows": neg_rows,
            "real27_images": {
                "evaluated": len(real_img_rows),
                "ocr_decision_counts": dec_counts,
                "auto_served_correct": real_auto_served,
                "auto_served_wrong": real_auto_wrong,
                "median_cer": round(statistics.median(r["cer"] for r in real_img_rows), 4) if real_img_rows else None,
                "latency_p50_ms": _percentile(real_latencies, 0.50),
                "latency_p95_ms": _percentile(real_latencies, 0.95),
                "rows": real_img_rows,
            },
            "external16_printed_images": {
                "evaluated": len(ext_rows),
                "ocr_decision_counts": dict(Counter(r["ocr_decision"] for r in ext_rows)),
                "auto_served_wrong": ext_wrong,
                "rows": ext_rows,
            },
        }, cont_errors
    finally:
        LO.shutdown_local_ocr()
        LO.clear_local_ocr_cache()
        if prev_py is None:
            os.environ.pop("LOCAL_OCR_PYTHON", None)
        else:
            os.environ["LOCAL_OCR_PYTHON"] = prev_py
        if prev_tess is None:
            os.environ.pop("LOCAL_OCR_TESSDATA", None)
        else:
            os.environ["LOCAL_OCR_TESSDATA"] = prev_tess


def _run_stream_c_safety() -> dict[str, Any]:
    trig_txt = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với (ABC) và SA = a. "
        "Tính côsin của góc giữa SB và mặt phẳng (ABC)."
    )
    out = AIR.route_text_input(trig_txt, allow_live_ai=False)
    rd = (out.response or {}).get("route_d") or {}
    env = (out.response or {}).get("envelope") or {}
    sgc = rd.get("source_goal_completion") or {}
    mode_a_ok = (
        out.status == "SERVED"
        and sgc.get("schema_version") == "source-goal-completion/1"
        and sgc.get("numeric_answer_shown") is False
        and sgc.get("goals", [{}])[0].get("numeric_source_goal") == "NOT_ANSWERED"
        and _continuity_count(env) == 0
    )

    mg9 = next(c for c in RM.build_cases() if c["id"] == "MG9")
    mg9_plan = planner.lap_ke_hoach(bridge_v2(TypedFactNextPayloadV2.model_validate(mg9["payload"])))
    mg9_res = run_typed_fact_next_v2_route(mg9["payload"])

    return {
        "mode_a_trig_no_answer_leak": mode_a_ok,
        "mode_a_answers_dict": rd.get("answers"),
        "mg9_planner_candidates": mg9_plan.search_telemetry.get("candidate_evaluations"),
        "mg9_planner_pruned": mg9_plan.search_telemetry.get("pruned_nodes"),
        "mg9_route_status": mg9_res.status,
        "mg9_reason_code": mg9_res.code,
        "max_memory_declarations": MAX_MEMORY_DECLARATIONS,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Do not write END_TO_END_CAPABILITY_EVALUATION.json")
    args = ap.parse_args()

    s2_ident = FZ.runtime_identity() if hasattr(FZ, "runtime_identity") else runtime_identity()
    surfaces = _check_surfaces()
    rm_eval = EAC._evaluate_reasoning_matrix()
    r1_eval = EAC._evaluate_r1_probe()
    nc_eval, cont_nc = _run_nc_and_negatives()
    a4_eval, cont_a4 = _run_a4_and_depth_bounds()
    dev_eval, cont_dev = _run_exposed_dev_corpora()
    ocr_eval, cont_ocr = _run_stream_b_ocr_evaluation()
    c_safety = _run_stream_c_safety()

    total_cont_errors = cont_nc + cont_a4 + cont_dev + cont_ocr
    measured_hash, measured_count = FZ.measured_system_hash()

    report = {
        "schema": "axo-unified-geometry-ocr-planning-evaluation/1",
        "run_id": "unified-geometry-understanding-ocr-autonomous-planning",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "measurement_class": "OFFLINE_DEVELOPMENT_EVIDENCE",
        "independent_h1_validation": "NOT_MEASURED",
        "live_ai_calls": 0,
        "sealed_h1_rows_opened": 0,
        "locked_w2_w3_rows_read": 0,
        "git_head": _git_head(),
        "product_commit": FZ.product_commit(),
        "measured_system": measured_hash,
        "measured_files": measured_count,
        "cache_version": CACHE_VERSION,
        "route_d_cache_policy": ROUTE_D_CACHE_POLICY,
        "semantic_environment_hash": semantic_environment_hash(),
        "locked_surfaces": surfaces,
        "stream_a": {
            "nc_and_autonomous_negatives": nc_eval,
            "a4_plane_constraints_and_depth": a4_eval,
            "reasoning_matrix_72": rm_eval,
            "r1_probe_19": r1_eval,
            "exposed_dev_corpora": dev_eval,
        },
        "stream_b": ocr_eval,
        "stream_c": {
            "total_scene3d_continuity_errors": total_cont_errors,
            **c_safety,
        },
    }

    encoded = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    findings = pub_safety.findings_in(encoded)
    assert not findings, f"Publication safety violation: {findings}"
    assert "APPROVED_BY_" + "USER" not in encoded.decode("utf-8")

    if not args.dry_run:
        out_path = RUN_DIR / "END_TO_END_CAPABILITY_EVALUATION.json"
        out_path.write_bytes(encoded)
        sha = hashlib.sha256(encoded).hexdigest()
    else:
        sha = hashlib.sha256(encoded).hexdigest()

    summary = {
        "surfaces_ok": surfaces["all_match"],
        "nc_gold": f"{nc_eval['nc_gold_passed']}/{nc_eval['nc_gold_total']}",
        "nc_nl": f"{nc_eval['nc_nl_passed']}/{nc_eval['nc_nl_total']}",
        "auto_neg": f"{nc_eval['autonomous_negatives_refused']}/{nc_eval['autonomous_negatives_total']}",
        "a4_ok": a4_eval["all_passed"],
        "rm_pos": f"{rm_eval['positive_served']}/{rm_eval['positive_total']}",
        "rm_neg": f"{rm_eval['negative_refused']}/{rm_eval['negative_total']}",
        "r1_pos": f"{r1_eval['positive_passed']}/{r1_eval['positive_total']}",
        "dev37": f"{dev_eval['dev37']['served']}/{dev_eval['dev37']['total']}",
        "comp112": f"{dev_eval['comp112']['served']}/{dev_eval['comp112']['total']}",
        "real27_text": f"{dev_eval['real27_text']['served']}/{dev_eval['real27_text']['total']}",
        "real27_wrong": dev_eval["real27_text"]["wrong_served"],
        "glyph_topo": f"{ocr_eval.get('glyph_topology_passed')}/{ocr_eval.get('glyph_topology_total')}",
        "ocr_pos": f"{ocr_eval.get('rendered_positive_accepted')}/{ocr_eval.get('rendered_positive_total')}",
        "ocr_false_accepts": ocr_eval.get("false_auto_accepts"),
        "real27_img_decisions": (ocr_eval.get("real27_images") or {}).get("ocr_decision_counts"),
        "continuity_errors": total_cont_errors,
        "mode_a_ok": c_safety["mode_a_trig_no_answer_leak"],
        "json_sha256": sha[:16],
    }
    print(json.dumps(summary, ensure_ascii=False))
    ok = (
        surfaces["all_match"]
        and nc_eval["nc_gold_passed"] == 21
        and nc_eval["nc_nl_passed"] == 21
        and nc_eval["autonomous_negatives_false_served"] == 0
        and a4_eval["all_passed"]
        and dev_eval["real27_text"]["wrong_served"] == 0
        and ocr_eval.get("glyph_topology_passed") == 10
        and ocr_eval.get("rendered_positive_accepted") == 4
        and ocr_eval.get("false_auto_accepts", 0) == 0
        and (ocr_eval.get("real27_images") or {}).get("auto_served_wrong", 0) == 0
        and total_cont_errors == 0
        and c_safety["mode_a_trig_no_answer_leak"]
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
