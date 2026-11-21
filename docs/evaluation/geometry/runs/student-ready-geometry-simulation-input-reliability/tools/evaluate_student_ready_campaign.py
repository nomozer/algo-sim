# -*- coding: utf-8 -*-
"""Offline end-to-end evaluator for `student-ready-geometry-simulation-input-reliability`.

Measures the frozen `CACHE_VERSION = 145` product candidate strictly offline
(`ALLOW_LIVE_AI = "0"`, `GEMINI_API_KEY = ""`, 0 paid provider calls, 0 sealed H-1 /
locked W2 / W3 rows opened), keeping:
1. `SPAN_ONLY_SCENE3D_SUCCESS_RATE` strictly separate from `whole_draft_fallback_served`.
2. `frozen_unseen_vmmu20` (19 unseen MIT items frozen before tuning) strictly separated under
   `ground_truth_status = "GROUND_TRUTH_UNVERIFIED"` / `independent_ground_truth_validation = "NOT_MEASURED"`,
   never merged into verified accuracy denominators.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time
from types import SimpleNamespace
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "backend" / "app").is_dir())
RUN_DIR = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "docs/evaluation/geometry/runs"

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""

for _p in (ROOT / "backend", ROOT / "backend/scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ERWC = _load(
    "_eval_real_world_v144_mod",
    RUNS_DIR / "real-world-geometry-input-verified-simulation/tools/evaluate_real_world_campaign.py",
)
CORPUS_CAT = _load(
    "_ext16_corpus_catalog",
    RUNS_DIR / "real-world-printed-handwriting-acquisition/tools/corpus_catalog.py",
)
NEW_EXT_CAT = _load(
    "_new_ext12_catalog",
    RUNS_DIR / "image-first-ocr-verified-geometry/tools/new_external_catalog.py",
)

from app import main as M  # noqa: E402
from app.ai import adaptive_input_router as AIR  # noqa: E402
from app.ai.hybrid_offline import prepare_local_first_hybrid, resolve_hybrid_gemini_model  # noqa: E402
from app.ai.local_geometry_parser import parse_geometry_problem_locally  # noqa: E402
from app.ingestion import local_ocr as LO  # noqa: E402
from app.ingestion import local_ocr_route as LR  # noqa: E402
from app.ingestion import ocr_reconcile as OR  # noqa: E402
from app.ingestion.unified_input import prepare_unified_input  # noqa: E402
from app.learner_messages import _MACHINE_TOKEN_RE, learner_reason  # noqa: E402
from app.runtime_identity import runtime_identity, semantic_environment_hash  # noqa: E402

EUC = ERWC.EUC
EAC = ERWC.EAC
EVI = ERWC.EVI
FZ = ERWC.FZ
pub_safety = ERWC.pub_safety


def _mime_and_name(raw_b: bytes, p: Path) -> tuple[str, str]:
    if raw_b.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", p.with_suffix(".png").name
    if raw_b.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", p.with_suffix(".jpg").name
    if raw_b.startswith(b"RIFF") and b"WEBP" in raw_b[:16]:
        return "image/webp", p.with_suffix(".webp").name
    return ("image/jpeg" if p.suffix.lower() in (".jpg", ".jpeg") else "image/png"), p.name


def _render_problem_png_bytes(txt: str, *, blur: bool = False) -> bytes:
    font_path = "C:/Windows/Fonts/arial.ttf"
    if not Path(font_path).exists():
        font_path = "C:/Windows/Fonts/segoeui.ttf"
    font = ImageFont.truetype(font_path, 28) if Path(font_path).exists() else ImageFont.load_default()
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
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(radius=2.2))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def _classify_diagnostic_4_1(prep_dict: dict[str, Any], cer: float | None, cf_draft: dict[str, Any]) -> dict[str, Any]:
    dec = (prep_dict.get("provenance") or {}).get("ocr_decision")
    reason = prep_dict.get("reason_code")
    spans = prep_dict.get("uncertain_tokens") or []
    blocking = sum(1 for s in spans if s.get("blocking"))
    if prep_dict.get("status") == "needs_selection":
        bucket = "MULTI_PROBLEM_NEEDS_SELECTION"
    elif dec == "LOCAL_OCR_ACCEPT":
        bucket = "AUTO_ACCEPTED_SAFE"
    elif (cer is not None and cer > 0.03) or (cf_draft["total"] > 0 and not cf_draft["all_recovered"]):
        bucket = "RECOGNITION_ERROR_NEEDS_CONFIRMATION"
    elif blocking == 0 or reason == "DIAGRAM_FACTS_UNVERIFIED":
        bucket = "GENUINE_DIAGRAM_OR_AMBIGUITY_CONFIRMATION"
    else:
        bucket = "GENUINE_DIAGRAM_OR_AMBIGUITY_CONFIRMATION" if any("PRIME" in str(s.get("reason") or "") for s in spans) else "INSUFFICIENT_ACCEPTANCE_EVIDENCE_TEXT_ACCURATE"
    return {"diagnostic_bucket": bucket, "blocking_spans": blocking, "reason_code": reason}


def _route_and_grade(
    text: str,
    grade_fn,
    *,
    origin: str,
    raw_sha: str,
    reg_sha: str | None,
    confirmed_span_count: int | None = None,
    selected_candidate_id: str | None = None,
    student_edited: bool = False,
) -> tuple[dict[str, Any], int]:
    prov_in = M.InputSourceProvenance(
        origin=origin,
        raw_ocr_text_sha256=raw_sha,
        prepared_region_sha256=reg_sha,
        student_edited=student_edited,
        confirmed_span_count=confirmed_span_count,
        selected_candidate_id=selected_candidate_id,
    )
    built_prov = M.build_verified_input_provenance(text, prov_in)
    from app.ai.local_geometry_parser import clear_local_geometry_parser_cache  # noqa: WPS433

    clear_local_geometry_parser_cache()
    t0 = time.perf_counter()
    out = AIR.route_text_input(text, allow_live_ai=False, input_kind="image")
    solve_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    rd = (out.response or {}).get("route_d") or {}
    env = (out.response or {}).get("envelope") or {}
    t_c0 = time.perf_counter()
    c_err = EUC._continuity_count(env) if out.status == "SERVED" else 0
    cont_ms = round((time.perf_counter() - t_c0) * 1000.0, 2)
    ans = rd.get("answers") if out.status == "SERVED" else None
    grade = grade_fn(out.status, ans, rd, env)
    ref = rd.get("refusal") or {}
    return {
        "routed_status": out.status,
        "reason_code": (None if out.status == "SERVED" else (ref.get("reason_code") or ref.get("code") or env.get("reason_code") or env.get("error_code"))),
        "answers": ans,
        "grade": grade,
        "continuity_errors": c_err,
        "scene3d_objects": len((env.get("scene3d") or {}).get("objects") or []) if out.status == "SERVED" else 0,
        "solve_ms": solve_ms,
        "telemetry_ms": {
            "local_parse_ms": round(float(getattr(out.telemetry, "local_parse_latency_ms", 0.0) or 0.0), 3),
            "hybrid_execution_ms": solve_ms,
            "continuity_check_ms": cont_ms,
        },
        "provenance": built_prov,
    }, c_err


async def _eval_single_image_v145(
    *,
    cid: str,
    raw_b: bytes,
    filename: str,
    gt: str,
    grade_fn,
    statement_ref: str | None = None,
    critical_facts: list[dict[str, Any]] | None = None,
    fact_texts: list[str] | None = None,
    partition: str | None = None,
    before_row: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], int]:
    mime, fname_use = _mime_and_name(raw_b, Path(filename))
    b64 = base64.b64encode(raw_b).decode("ascii")

    LO.clear_local_ocr_cache()
    t0 = time.perf_counter()
    cold_res = await prepare_unified_input(content=b64, declared_mime=mime, filename=fname_use, api_key="", cache_version=M.CACHE_VERSION)
    cold_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    cold = cold_res.to_dict()

    t1 = time.perf_counter()
    await prepare_unified_input(content=b64, declared_mime=mime, filename=fname_use, api_key="", cache_version=M.CACHE_VERSION)
    warm_ms = round((time.perf_counter() - t1) * 1000.0, 2)

    prov = cold.get("provenance") or {}
    loc = prov.get("local_ocr") or {}
    dec = loc.get("ocr_decision") or prov.get("ocr_decision")
    draft = cold.get("problem_text") or ""
    cer = EUC._cer(draft, gt) if (draft and gt) else None
    cf_draft = ERWC._critical_fact_stats(draft, critical_facts=critical_facts, fact_texts=fact_texts)
    spans = cold.get("uncertain_tokens") or []
    blocking = sum(1 for s in spans if s.get("blocking"))
    raw_sha = prov.get("raw_ocr_text_sha256") or hashlib.sha256(draft.encode("utf-8")).hexdigest()
    reg_sha = prov.get("prepared_region_sha256")
    cont_errors = 0

    auto_route = None
    conf_sim = None
    if cold.get("status") == "ready" and draft.strip():
        ar, ce = _route_and_grade(
            draft,
            grade_fn,
            origin="local_ocr_auto_verified" if dec == "LOCAL_OCR_ACCEPT" else "local_ocr_student_confirmed",
            raw_sha=raw_sha,
            reg_sha=reg_sha,
            student_edited=False,
        )
        cont_errors += ce
        ar["false_auto_accept"] = (dec == "LOCAL_OCR_ACCEPT" and ar["routed_status"] == "SERVED" and ar["grade"].get("verdict") == "WRONG_SERVED")
        auto_route = ar
    elif cold.get("status") == "needs_confirmation" and draft.strip():
        t_sim0 = time.perf_counter()
        sim = ERWC.EIFO.simulate_student(draft, spans, gt)
        sim_ms = round((time.perf_counter() - t_sim0) * 1000.0, 2)
        confirmed_text = sim["text"]
        cf_after = ERWC._critical_fact_stats(confirmed_text, critical_facts=critical_facts, fact_texts=fact_texts)
        rt, ce = _route_and_grade(
            confirmed_text,
            grade_fn,
            origin="local_ocr_student_confirmed",
            raw_sha=raw_sha,
            reg_sha=reg_sha,
            confirmed_span_count=len(spans),
            student_edited=bool(sim["edits"]),
        )
        cont_errors += ce
        wb = None
        fb_txt = statement_ref or gt
        if rt["routed_status"] != "SERVED" and fb_txt and fb_txt != confirmed_text:
            wb_rt, wb_ce = _route_and_grade(
                fb_txt,
                grade_fn,
                origin="local_ocr_student_confirmed",
                raw_sha=raw_sha,
                reg_sha=reg_sha,
                confirmed_span_count=len(spans),
                student_edited=True,
            )
            cont_errors += wb_ce
            wb = {
                "routed_status": wb_rt["routed_status"],
                "reason_code": wb_rt["reason_code"],
                "answers": wb_rt["answers"],
                "grade": wb_rt["grade"],
                "continuity_errors": wb_rt["continuity_errors"],
                "note": "Requires free-text edit on unflagged OCR error; reported strictly separately from span-only confirmation.",
            }
        conf_sim = {
            "cer_after": EUC._cer(confirmed_text, gt) if gt else None,
            "critical_facts_after": cf_after,
            "edits": sim["edits"],
            "edit_count": len(sim["edits"]),
            "confirms": sim["confirms"],
            "diagram_confirms": sim["diagram_confirms"],
            "actions": sim["actions"],
            "chars_typed": sim["chars_typed"],
            "full_retype_chars": len(gt),
            **rt,
            "simulate_ms": sim_ms,
            "whole_draft_confirmation_fallback": wb,
        }

    row = {
        "case_id": cid,
        "partition": partition,
        "prepare_status": cold.get("status"),
        "reason_code": cold.get("reason_code"),
        "ocr_decision": dec,
        "cer": cer,
        "blocking_uncertain_spans": blocking,
        "zero_text_spans": sum(1 for s in spans if s.get("text") == "0"),
        "critical_facts_draft": cf_draft,
        "review_items_count": len(spans),
        "candidates_count": len(cold.get("candidates") or []),
        "confirmation_contract_version": prov.get("confirmation_contract_version"),
        "cold_prepare_ms": cold_ms,
        "warm_prepare_ms": warm_ms,
        "diagnostic_4_1": _classify_diagnostic_4_1(cold, cer, cf_draft),
        "auto_route": auto_route,
        "confirmation_simulated": conf_sim,
        "before_baseline": before_row or {},
    }
    return row, cont_errors


def _run_learner_hygiene_and_cache_145_checks() -> dict[str, Any]:
    poisoned = ("s1", "s2", "c1", "q1", "p1", "d1", "@d1", "@orthocenter_1", "snake_case", "{'raw': 1}")
    leaks: list[dict[str, str]] = []
    for code, fcat in (
        ("MISSING_DIMENSION", "insufficient_specification"),
        ("INCONSISTENT_FACTS", "geometry_generation_failed"),
        ("DEGENERATE_CONSTRUCTION", "geometry_generation_failed"),
        ("UNSUPPORTED_CAPABILITY", "capability_gap"),
        ("NON_POSITIVE_LENGTH", "geometry_generation_failed"),
        ("CONSTRUCTION_NOT_TEXT_BOUND", "verification_gap"),
    ):
        for sub in poisoned:
            msg = learner_reason(
                {
                    "status": "unsupported",
                    "reason_code": code,
                    "refusal_cause": "SOURCE",
                    "failure_category": fcat,
                    "reason_subjects": [sub, "SA"],
                    "reason": f"{sub}: không gắn được dữ kiện trong câu đề {sub}",
                }
            )
            m = _MACHINE_TOKEN_RE.search(msg)
            if m:
                leaks.append({"code": code, "poison": sub, "token": m.group(0), "msg": msg})

    miss_144 = M._cache_lookup(
        SimpleNamespace(
            query=lambda *_a: SimpleNamespace(
                filter_by=lambda **_k: SimpleNamespace(
                    first=lambda: SimpleNamespace(
                        policy_version="144:route-d",
                        dsl_version=next(iter(M.SUPPORTED_VERSIONS)),
                    )
                )
            )
        ),
        "probe-144-key",
        M.ROUTE_D_CACHE_POLICY,
    ) is None

    draft_t = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với (ABCD) và SA = a. Tính thể tích khối chóp S.ABCD."
    edit_t = draft_t.replace("SA = a.", "SA = 2a.")
    k_draft = prepare_local_first_hybrid(draft_t, model=resolve_hybrid_gemini_model()).cache_key
    k_edit = prepare_local_first_hybrid(edit_t, model=resolve_hybrid_gemini_model()).cache_key

    return {
        "passed": (not leaks) and bool(miss_144) and (M.CACHE_VERSION == "145") and (k_draft != k_edit),
        "cache_version": M.CACHE_VERSION,
        "route_d_cache_policy": M.ROUTE_D_CACHE_POLICY,
        "stale_144_row_misses": bool(miss_144),
        "distinct_cache_keys": k_draft != k_edit,
        "learner_message_machine_token_leaks": leaks,
    }


def _evaluate_real27_promotions_and_forensics(real27_items: list[dict[str, Any]]) -> dict[str, Any]:
    rmap = {it["case_id"]: it for it in real27_items}
    promoted_specs = {
        "vmmu_r254": "9a³√13/2",
        "vmmu_r277": "8a³",
        "vmmu_r488": "a³/3",
    }
    promoted_rows: list[dict[str, Any]] = []
    for cid, expected in promoted_specs.items():
        it = rmap[cid]
        parsed = parse_geometry_problem_locally(it["ground_truth_text"])
        out = AIR.route_text_input(it["ground_truth_text"], allow_live_ai=False)
        rd = (out.response or {}).get("route_d") or {}
        ans = rd.get("answers") if out.status == "SERVED" else None
        cont_err = EUC._continuity_count((out.response or {}).get("envelope") or {}) if out.status == "SERVED" else 1
        promoted_rows.append(
            {
                "case_id": cid,
                "partition": it.get("partition"),
                "parse_status": parsed.status,
                "status": out.status,
                "answers": ans,
                "expected": expected,
                "exact_match": bool(ans and list(ans.values()) == [expected]),
                "scene3d_continuity_errors": cont_err,
            }
        )

    still_refused_specs = {
        "vmmu_r256": ("SOURCE_GROUNDING_GAP", "Source typo 'đên' instead of 'đến'; counterfactual 'đến' serves a√15/5."),
        "vmmu_r266": ("KERNEL_EXACT_DOMAIN_GAP", "PROVED_DETERMINATE_EXACT_DOMAIN_EXCEEDED: nested radical cosine outside rational Gram chart."),
        "vmmu_r461": ("INTENTIONALLY_UNSUPPORTED", "Out-of-scope rolled circular sector -> cone application."),
        "vmmu_r475": ("INTENTIONALLY_UNSUPPORTED", "Out-of-scope multi-curved Archimedes displacement problem."),
        "vmmu_r491": ("TYPED_FACT_GAP", "Free sliding projection locus I in BC with undetermined AA' height."),
        "vmmu_r513": ("INSUFFICIENT_SPECIFICATION", "Missing rectangle edge BC/AD -> MISSING_DIMENSION aligned with Source Gate."),
    }
    refused_rows: list[dict[str, Any]] = []
    for cid, (cat, note) in still_refused_specs.items():
        it = rmap[cid]
        out = AIR.route_text_input(it["ground_truth_text"], allow_live_ai=False)
        rd = (out.response or {}).get("route_d") or {}
        diag = rd.get("local_diagnostics") or {}
        ref = rd.get("refusal") or {}
        refused_rows.append(
            {
                "case_id": cid,
                "partition": it.get("partition"),
                "category": cat,
                "status": out.status,
                "code": ref.get("reason_code") or ref.get("code"),
                "root_cause": diag.get("root_cause"),
                "determinacy_status": diag.get("determinacy_status"),
                "note": note,
            }
        )

    r256_cf_out = AIR.route_text_input(rmap["vmmu_r256"]["ground_truth_text"].replace("đên", "đến"), allow_live_ai=False)
    r256_cf_ans = ((r256_cf_out.response or {}).get("route_d") or {}).get("answers") if r256_cf_out.status == "SERVED" else None

    r513_parsed = parse_geometry_problem_locally(rmap["vmmu_r513"]["ground_truth_text"])
    r513_out = AIR.route_text_input(rmap["vmmu_r513"]["ground_truth_text"], allow_live_ai=False)
    r513_diag = ((r513_out.response or {}).get("route_d") or {}).get("local_diagnostics") or {}

    return {
        "newly_promoted_from_144": {
            "count": len(promoted_rows),
            "all_exact_match": all(r["exact_match"] and r["scene3d_continuity_errors"] == 0 for r in promoted_rows),
            "rows": promoted_rows,
        },
        "remaining_refused_6_count": len(refused_rows),
        "remaining_refused_6_categories": dict(Counter(r["category"] for r in refused_rows)),
        "remaining_refused_6_rows": refused_rows,
        "r256_counterfactual_fixed_typo": {
            "status": r256_cf_out.status,
            "answers": r256_cf_ans,
            "expected": "a√15/5",
        },
        "r513_source_gate_alignment": {
            "verified": r513_parsed.status == "LOCAL_PARSE_COMPLETE" and r513_diag.get("determinacy_status") == "UNPROVED_DUE_TO_CAPABILITY_GAP",
            "local_parse_status": r513_parsed.status,
            "determinacy_status": r513_diag.get("determinacy_status"),
            "root_cause": r513_diag.get("root_cause"),
        },
    }


async def _evaluate_ocr_and_confirmation_v145_async(baselines: dict[str, Any], prior_eval: dict[str, Any]) -> tuple[dict[str, Any], int]:
    assert LO.LOCAL_OCR_WORKER_VERSION == "local-ocr-worker/5"
    assert OR.OCR_RECONCILE_VERSION == "layout-aware-ocr-reconcile/4"
    assert LR.LOCAL_OCR_ROUTE_VERSION == "local-ocr-route/3"

    ocr_py = ROOT / ".superpowers/ocr-venv/Scripts/python.exe"
    ocr_tess = ROOT / ".superpowers/tessdata_fast"
    assert ocr_py.exists() and ocr_tess.is_dir(), "Local OCR sidecar missing"

    prev_py = os.environ.get("LOCAL_OCR_PYTHON")
    prev_tess = os.environ.get("LOCAL_OCR_TESSDATA")
    os.environ["LOCAL_OCR_PYTHON"] = str(ocr_py)
    os.environ["LOCAL_OCR_TESSDATA"] = str(ocr_tess)
    LO.clear_local_ocr_cache()

    cont_errors = 0
    try:
        # 1. Glyph topology 12/12
        topo_font_path = "C:/Windows/Fonts/cambria.ttc"
        if not Path(topo_font_path).exists():
            topo_font_path = "C:/Windows/Fonts/arial.ttf"
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
            ("=", {"has_equals_bars": True, "blurry": False}),
            ("-", {"has_equals_bars": False, "blurry": False}),
        ]
        topo_rows = []
        for tok, want_flags in topo_specs:
            im = Image.new("RGB", (180, 64), "white")
            ImageDraw.Draw(im).text((30, 14), tok, fill="black", font=topo_font)
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            res = LO.reread_local_ocr_regions(buf.getvalue(), [[20, 10, 150, 56]])
            gt = ((res.get("readings") or [{}])[0]).get("glyph_topology") or {}
            ok = all(bool(gt.get(k)) is bool(v) for k, v in want_flags.items())
            topo_rows.append({"token": tok, "want": want_flags, "got": gt, "passed": ok})

        # 2. Rendered positives 4/4
        rendered_pos = [
            ("pos_area_a2", "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a². Tính khoảng cách từ A đến mặt phẳng (SBC).", "a√6/3"),
            ("pos_2a_sqrt3", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA vuông góc với (ABCD) và SA = a√3. Tính thể tích khối chóp S.ABCD.", "4a³√3/3"),
            ("pos_area_frac_a2_2", "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại B, diện tích tam giác ABC bằng a²/2, SA vuông góc với (ABC) và SA = a. Tính thể tích khối chóp S.ABC.", "a³/6"),
            ("pos_cm_cm2", "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3cm và diện tích đáy bằng 9cm². Tính khoảng cách từ A đến mặt phẳng (SBC).", "√6"),
        ]
        pos_rows = []
        for pid, txt, want_ans in rendered_pos:
            raw_b = _render_problem_png_bytes(txt)
            b64 = base64.b64encode(raw_b).decode("ascii")
            LO.clear_local_ocr_cache()
            t0 = time.perf_counter()
            prep = (await prepare_unified_input(content=b64, declared_mime="image/png", filename=f"{pid}.png", api_key="", cache_version=M.CACHE_VERSION)).to_dict()
            pms = round((time.perf_counter() - t0) * 1000.0, 2)
            dec = (prep.get("provenance") or {}).get("ocr_decision") or ((prep.get("provenance") or {}).get("local_ocr") or {}).get("ocr_decision")
            ans_got = None
            routed_status = None
            if prep["status"] == "ready":
                routed = AIR.route_text_input(prep["problem_text"], allow_live_ai=False, input_kind="image")
                routed_status = routed.status
                env = (routed.response or {}).get("envelope") or {}
                if routed.status == "SERVED":
                    cont_errors += EUC._continuity_count(env)
                ans_got = ((routed.response or {}).get("route_d") or {}).get("answers", {}).get("q1")
            pos_rows.append(
                {
                    "id": pid,
                    "prepare_status": prep["status"],
                    "ocr_decision": dec,
                    "routed_status": routed_status,
                    "answer": ans_got,
                    "want": want_ans,
                    "matched": dec == "LOCAL_OCR_ACCEPT" and routed_status == "SERVED" and bool(EVI.same_value(str(ans_got), want_ans)),
                    "ms": pms,
                }
            )

        # 3. Adversarial negatives 3/3 (0 false auto-accepts)
        neg_specs = [
            ("neg_inline_a2", "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a2. Tính thể tích khối chóp S.ABCD.", False),
            ("neg_blurry_crop", "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a². Tính thể tích khối chóp S.ABCD.", True),
            ("neg_diagram_ref", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a (tham khảo hình vẽ). Tính thể tích khối chóp S.ABCD.", False),
        ]
        neg_rows = []
        false_accepts_neg = 0
        for nid, txt, do_blur in neg_specs:
            b64 = base64.b64encode(_render_problem_png_bytes(txt, blur=do_blur)).decode("ascii")
            LO.clear_local_ocr_cache()
            prep = (await prepare_unified_input(content=b64, declared_mime="image/png", filename=f"{nid}.png", api_key="", cache_version=M.CACHE_VERSION)).to_dict()
            dec = (prep.get("provenance") or {}).get("ocr_decision") or ((prep.get("provenance") or {}).get("local_ocr") or {}).get("ocr_decision")
            if dec == "LOCAL_OCR_ACCEPT" or prep["status"] == "ready":
                false_accepts_neg += 1
            neg_rows.append({"id": nid, "prepare_status": prep["status"], "ocr_decision": dec, "blocked": dec != "LOCAL_OCR_ACCEPT" and prep["status"] != "ready"})

        # 4. REAL27 images
        prior_r27_rows = {r["case_id"]: r for r in ((prior_eval.get("ocr_before_after") or {}).get("real27_images") or {}).get("rows") or []}
        real25 = json.loads((RUNS_DIR / "controlled-vision-real-image-validation/new_in_scope_image_manifest.json").read_text(encoding="utf-8"))["items"]
        real2 = json.loads((RUNS_DIR / "local-semantic-source-gate-reliability/fresh_external_manifest.json").read_text(encoding="utf-8"))["items"]
        real27_rows = []
        for it in real25 + real2:
            cid = it["case_id"]
            p = ROOT / it["cache_path"]
            if not p.exists():
                continue

            def _grade_real27(st: str, ans: dict[str, Any] | None, rd: dict[str, Any], _env: dict[str, Any], item=it, case_id=cid) -> dict[str, Any]:
                if st != "SERVED":
                    return {"verdict": "NOT_SERVED"}
                g = EVI.grade(item, {"status": st, "answers": ans})
                is_adj = g.get("verdict") == "SERVED_NOT_COMPARABLE_NEEDS_ADJUDICATION" and rd.get("source_goal_completion") is not None
                if g.get("verdict") == "SERVED_DIFFERS_FROM_DATASET_KEY" and case_id in EUC.REAL27_KNOWN_KEY_ERRORS:
                    g["verdict"] = "SERVED_KNOWN_DATASET_KEY_ERRATUM"
                elif is_adj:
                    g["verdict"] = "SERVED_MODE_A_ADJUDICATED"
                elif g.get("verdict") == "SERVED_DIFFERS_FROM_DATASET_KEY":
                    g["verdict"] = "WRONG_SERVED"
                return g

            prior_r = (baselines.get("real27_prior_rows") or {}).get(cid) or prior_r27_rows.get(cid) or {}
            dump_r = (baselines.get("dump_real27") or {}).get(cid) or {}
            before_r27 = {
                "cer": prior_r.get("cer"),
                "ocr_decision": prior_r.get("ocr_decision"),
                "blocking_uncertain_spans": dump_r.get("uncertain_blocking_count"),
            }
            row, l_ce = await _eval_single_image_v145(
                cid=cid,
                raw_b=p.read_bytes(),
                filename=p.name,
                gt=it["ground_truth_text"],
                grade_fn=_grade_real27,
                statement_ref=it.get("statement"),
                critical_facts=it.get("critical_facts"),
                partition=it.get("partition"),
                before_row=before_r27,
            )
            cont_errors += l_ce
            real27_rows.append(row)

        def _summarize_r27(subset: list[dict[str, Any]]) -> dict[str, Any]:
            if not subset:
                return {"count": 0}
            cers_a = [r["cer"] for r in subset if r["cer"] is not None]
            cers_b = [r["before_baseline"]["cer"] for r in subset if r["before_baseline"].get("cer") is not None]
            blk_a = [r["blocking_uncertain_spans"] for r in subset]
            blk_b = [r["before_baseline"]["blocking_uncertain_spans"] for r in subset if r["before_baseline"].get("blocking_uncertain_spans") is not None]
            cf_d_rec = sum(r["critical_facts_draft"]["recovered"] for r in subset)
            cf_d_tot = sum(r["critical_facts_draft"]["total"] for r in subset)
            cf_a_rec = sum(
                (r["confirmation_simulated"]["critical_facts_after"]["recovered"] if r["confirmation_simulated"] else r["critical_facts_draft"]["recovered"])
                for r in subset
            )
            auto_rows = [r for r in subset if r["auto_route"] is not None]
            conf_rows = [r for r in subset if r["confirmation_simulated"] is not None]
            conf_srv = [r for r in conf_rows if r["confirmation_simulated"]["routed_status"] == "SERVED"]
            conf_wrong = [r for r in conf_srv if r["confirmation_simulated"]["grade"].get("verdict") == "WRONG_SERVED"]
            return {
                "count": len(subset),
                "ocr_decision_counts": dict(Counter(r["ocr_decision"] for r in subset)),
                "cer_before_median": round(statistics.median(cers_b), 4) if cers_b else None,
                "cer_after_median": round(statistics.median(cers_a), 4) if cers_a else None,
                "cer_after_mean": round(sum(cers_a) / len(cers_a), 4) if cers_a else None,
                "blocking_spans_before": sum(blk_b) if blk_b else None,
                "blocking_spans_after": sum(blk_a),
                "critical_facts_draft": f"{cf_d_rec}/{cf_d_tot}",
                "critical_facts_after_confirmation": f"{cf_a_rec}/{cf_d_tot}",
                "critical_facts_after_rate": round(cf_a_rec / cf_d_tot, 4) if cf_d_tot else None,
                "false_auto_accepts": sum(1 for r in auto_rows if r["auto_route"].get("false_auto_accept")),
                "auto_served_correct": sum(1 for r in auto_rows if r["auto_route"].get("routed_status") == "SERVED" and not r["auto_route"].get("false_auto_accept")),
                "confirmed_ready_count": len(conf_rows),
                "confirmed_served": len(conf_srv),
                "confirmed_wrong_served": len(conf_wrong),
                "whole_draft_fallback_served": sum(1 for r in conf_rows if ((r["confirmation_simulated"].get("whole_draft_confirmation_fallback") or {}).get("routed_status") == "SERVED")),
                "confirmation_median_actions": statistics.median([r["confirmation_simulated"]["actions"] for r in conf_rows]) if conf_rows else 0,
                "confirmation_median_chars_typed": statistics.median([r["confirmation_simulated"]["chars_typed"] for r in conf_rows]) if conf_rows else 0,
                "confirmation_total_chars_typed": sum(r["confirmation_simulated"]["chars_typed"] for r in conf_rows),
                "confirmation_total_full_retype_chars": sum(r["confirmation_simulated"]["full_retype_chars"] for r in conf_rows),
                "latency_cold_prepare": ERWC._stats([r["cold_prepare_ms"] for r in subset]),
                "latency_warm_prepare": ERWC._stats([r["warm_prepare_ms"] for r in subset]),
            }

        # 5. External16 (15 printed + 1 handwritten reported separately)
        ext_printed_rows = []
        ext_hw_rows = []
        for it in [c for c in CORPUS_CAT.CORPUS_ITEMS if c.get("has_complete_problem")]:
            iid = it["image_id"]
            p = ROOT / ".superpowers/external_image_cache" / (it.get("filename") or "")
            if not p.exists():
                continue
            raw_b = p.read_bytes()
            gt = it.get("ground_truth_text") or ""

            def _grade_ext(st: str, ans: dict[str, Any] | None, _rd: dict[str, Any], _env: dict[str, Any], cid=iid) -> dict[str, Any]:
                if st != "SERVED":
                    return {"verdict": "NOT_SERVED"}
                return {"verdict": ERWC._grade_eifo_oracle(cid, ans)}

            prior_e = (baselines.get("ext16_prior_rows") or {}).get(iid) or {}
            before_e16 = {
                "cer": ((prior_e.get("scoring") or {}).get("cer") or {}).get("reconciled_draft"),
                "blocking_uncertain_spans": (prior_e.get("after_reconcile") or {}).get("blocking_uncertain_count"),
                "ocr_decision": "LOCAL_OCR_ACCEPT" if (prior_e.get("after_reconcile") or {}).get("extraction_verified") else "LOCAL_OCR_REVIEW_REQUIRED",
            }
            row, l_ce = await _eval_single_image_v145(
                cid=iid,
                raw_b=raw_b,
                filename=p.name,
                gt=gt,
                grade_fn=_grade_ext,
                statement_ref=gt,
                partition=it.get("printed_or_handwritten"),
                before_row=before_e16,
            )
            cont_errors += l_ce

            # Handle needs_selection bands if multi-problem
            if row["prepare_status"] == "needs_selection":
                mime, fname_use = _mime_and_name(raw_b, p)
                b64 = base64.b64encode(raw_b).decode("ascii")
                base_prep = (
                    await prepare_unified_input(
                        content=b64,
                        declared_mime=mime,
                        filename=fname_use,
                        api_key="",
                        cache_version=M.CACHE_VERSION,
                    )
                ).to_dict()
                sel_outcomes = []
                gt_parts = it.get("verbatim_problem_texts") or []
                for idx, cand in enumerate(base_prep.get("candidates") or []):
                    cid_cand = cand["candidate_id"]
                    b_prep = (
                        await prepare_unified_input(
                            content=b64,
                            declared_mime=mime,
                            filename=fname_use,
                            selected_candidate_id=cid_cand,
                            api_key="",
                            cache_version=M.CACHE_VERSION,
                        )
                    ).to_dict()
                    band_gt = gt_parts[idx] if idx < len(gt_parts) else gt
                    band_draft = b_prep.get("problem_text") or ""
                    band_spans = b_prep.get("uncertain_tokens") or []
                    if b_prep.get("status") == "needs_confirmation" and band_draft and band_gt:
                        b_sim = ERWC.EIFO.simulate_student(band_draft, band_spans, band_gt)
                        final_sub = b_sim["text"]
                        edits_n = len(b_sim["edits"])
                    else:
                        final_sub = band_draft
                        edits_n = 0
                    from app.ai.local_geometry_parser import clear_local_geometry_parser_cache  # noqa: WPS433

                    clear_local_geometry_parser_cache()
                    rt_out = AIR.route_text_input(final_sub, allow_live_ai=False, input_kind="image") if final_sub.strip() else None
                    rt_st = rt_out.status if rt_out else "REFUSED"
                    rt_ans = ((rt_out.response or {}).get("route_d") or {}).get("answers") if (rt_out and rt_st == "SERVED") else None
                    ce = EUC._continuity_count((rt_out.response or {}).get("envelope") or {}) if (rt_out and rt_st == "SERVED") else 0
                    cont_errors += ce
                    sub_key = f"{iid}#{idx + 1}"
                    if rt_st != "SERVED":
                        ov = "NOT_SERVED"
                    elif sub_key in ERWC.EIFO.ORACLE:
                        ov = ERWC._grade_eifo_oracle(sub_key, rt_ans)
                    else:
                        ov = "SERVED_NO_ORACLE"
                    sel_outcomes.append(
                        {
                            "candidate_id": cid_cand,
                            "label": cand.get("label"),
                            "prepare_status": b_prep.get("status"),
                            "edits": edits_n,
                            "routed_status": rt_st,
                            "answers": rt_ans,
                            "oracle_verdict": ov,
                            "continuity_errors": ce,
                        }
                    )
                row["selection_outcomes"] = sel_outcomes

            if it.get("printed_or_handwritten") == "HANDWRITTEN":
                ext_hw_rows.append(row)
            else:
                ext_printed_rows.append(row)

        def _summarize_ext(rows_in: list[dict[str, Any]]) -> dict[str, Any]:
            cers_a = [r["cer"] for r in rows_in if r["cer"] is not None]
            cers_b = [r["before_baseline"]["cer"] for r in rows_in if r["before_baseline"].get("cer") is not None]
            auto_rows = [r for r in rows_in if r["auto_route"] is not None]
            conf_rows = [r for r in rows_in if r["confirmation_simulated"] is not None]
            sel_rows = [r for r in rows_in if r.get("selection_outcomes") is not None]
            return {
                "count": len(rows_in),
                "ocr_decision_counts": dict(Counter(r["ocr_decision"] for r in rows_in)),
                "prepare_status_counts": dict(Counter(r["prepare_status"] for r in rows_in)),
                "cer_before_median": round(statistics.median(cers_b), 4) if cers_b else None,
                "cer_after_median": round(statistics.median(cers_a), 4) if cers_a else None,
                "false_auto_accepts": sum(1 for r in auto_rows if r["auto_route"].get("false_auto_accept")),
                "auto_served_correct": sum(1 for r in auto_rows if r["auto_route"].get("grade", {}).get("verdict") == "SERVED_CORRECT"),
                "confirmed_ready_count": len(conf_rows),
                "confirmed_served_correct": sum(1 for r in conf_rows if r["confirmation_simulated"].get("grade", {}).get("verdict") == "SERVED_CORRECT"),
                "confirmed_wrong_served": sum(1 for r in conf_rows if r["confirmation_simulated"].get("grade", {}).get("verdict") == "WRONG_SERVED"),
                "whole_draft_fallback_served": sum(1 for r in conf_rows if ((r["confirmation_simulated"].get("whole_draft_confirmation_fallback") or {}).get("routed_status") == "SERVED")),
                "confirmation_median_actions": statistics.median([r["confirmation_simulated"]["actions"] for r in conf_rows]) if conf_rows else 0,
                "confirmation_median_chars_typed": statistics.median([r["confirmation_simulated"]["chars_typed"] for r in conf_rows]) if conf_rows else 0,
                "selection_bands_tested": sum(len(r["selection_outcomes"]) for r in sel_rows),
                "selection_served_correct": sum(1 for r in sel_rows for s in r["selection_outcomes"] if s.get("oracle_verdict") == "SERVED_CORRECT"),
                "latency_cold_prepare": ERWC._stats([r["cold_prepare_ms"] for r in rows_in]),
                "latency_warm_prepare": ERWC._stats([r["warm_prepare_ms"] for r in rows_in]),
            }

        # 6. Untouched external image sets: new_external_12 & new_image_corpus_8
        new_ext_rows = []
        for it in NEW_EXT_CAT.NEW_EXTERNAL_ITEMS:
            p = ROOT / ".superpowers/external_image_cache" / it["filename"]
            if not p.exists():
                continue

            def _grade_ne(st: str, ans: dict[str, Any] | None, _rd: dict[str, Any], _env: dict[str, Any], cid=it["image_id"]) -> dict[str, Any]:
                if st != "SERVED":
                    return {"verdict": "NOT_SERVED"}
                return {"verdict": ERWC._grade_eifo_oracle(cid, ans)}

            r_ne, ce_ne = await _eval_single_image_v145(
                cid=it["image_id"],
                raw_b=p.read_bytes(),
                filename=p.name,
                gt=it.get("ground_truth_text") or "",
                grade_fn=_grade_ne,
                partition="untouched_new_external_12",
            )
            cont_errors += ce_ne
            new_ext_rows.append(r_ne)

        nic8_manifest = json.loads((RUNS_DIR / "real-image-ocr-vision-comparative-acceptance/new_image_corpus_manifest.json").read_text(encoding="utf-8"))["items"]
        nic8_rows = []
        for it in nic8_manifest:
            p = ROOT / it["cache_path"]
            if not p.exists():
                continue

            def _grade_n8(st: str, ans: dict[str, Any] | None, _rd: dict[str, Any], _env: dict[str, Any], cid=it["case_id"]) -> dict[str, Any]:
                if st != "SERVED":
                    return {"verdict": "NOT_SERVED"}
                if cid == "new_vmmu_full_r446":
                    ok = bool(ans) and EVI.same_value(str(next(iter(ans.values()))), "√3/3")
                    return {"verdict": "SERVED_CORRECT" if ok else "WRONG_SERVED"}
                return {"verdict": "SERVED_NO_EXPLICIT_NUMERIC_ORACLE"}

            r_n8, ce_n8 = await _eval_single_image_v145(
                cid=it["case_id"],
                raw_b=p.read_bytes(),
                filename=p.name,
                gt=it.get("ground_truth_text") or "",
                grade_fn=_grade_n8,
                fact_texts=it.get("critical_fact_texts") or [],
                partition=it.get("partition"),
            )
            cont_errors += ce_n8
            nic8_rows.append(r_n8)

        def _summarize_untouched(rows_in: list[dict[str, Any]]) -> dict[str, Any]:
            cers = [r["cer"] for r in rows_in if r["cer"] is not None]
            auto_rows = [r for r in rows_in if r["auto_route"] is not None]
            conf_rows = [r for r in rows_in if r["confirmation_simulated"] is not None]
            return {
                "count": len(rows_in),
                "ocr_decision_counts": dict(Counter(r["ocr_decision"] for r in rows_in)),
                "cer_median": round(statistics.median(cers), 4) if cers else None,
                "auto_accepts": len(auto_rows),
                "auto_wrong_served": sum(1 for r in auto_rows if r["auto_route"].get("grade", {}).get("verdict") == "WRONG_SERVED"),
                "confirmed_served": sum(1 for r in conf_rows if r["confirmation_simulated"].get("routed_status") == "SERVED"),
                "confirmed_served_correct": sum(1 for r in conf_rows if r["confirmation_simulated"].get("grade", {}).get("verdict") == "SERVED_CORRECT"),
                "confirmed_wrong_served": sum(1 for r in conf_rows if r["confirmation_simulated"].get("grade", {}).get("verdict") == "WRONG_SERVED"),
                "latency_cold_prepare": ERWC._stats([r["cold_prepare_ms"] for r in rows_in]),
                "rows": rows_in,
            }

        # 7. Deterministic offline Vision-fallback mock
        vis_prep = {
            "status": "ready",
            "source_kind": "image",
            "problem_text": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với (ABCD) và SA = a√3. Tính thể tích khối chóp S.ABCD.",
            "provenance": {"extraction_method": "vlm", "confirmation_contract_version": "ocr-confirmation-provenance/1"},
            "metrics": {"vlm_calls": 1, "processing_ms": 50.0},
        }
        vis_out = AIR.route_image_or_prepare_outcome(vis_prep, allow_live_ai=False)
        vis_env = (vis_out.response or {}).get("envelope") or {}
        vis_ce = EUC._continuity_count(vis_env) if vis_out.status == "SERVED" else 1
        cont_errors += vis_ce
        vis_ans = ((vis_out.response or {}).get("route_d") or {}).get("answers")
        vision_fallback_mock = {
            "passed": (
                vis_out.status == "SERVED"
                and vis_out.telemetry.chosen_route == "VISION_THEN_LOCAL_DETERMINISTIC"
                and vis_out.telemetry.gemini_typed_fact_calls == 0
                and vis_ans == {"q1": "a³√3/3"}
                and vis_ce == 0
            ),
            "route": vis_out.telemetry.chosen_route,
            "answers": vis_ans,
            "live_ai_calls": vis_out.telemetry.gemini_typed_fact_calls,
            "continuity_errors": vis_ce,
        }

        cache_split_ok = len(LO._RAW_OCR_CACHE) <= LO._RAW_OCR_CACHE_MAX and len(LO._REREAD_CACHE) <= LO._REREAD_CACHE_MAX
        return {
            "available": True,
            "worker_version": LO.LOCAL_OCR_WORKER_VERSION,
            "ocr_reconcile_version": OR.OCR_RECONCILE_VERSION,
            "local_ocr_route_version": LR.LOCAL_OCR_ROUTE_VERSION,
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
            "false_auto_accepts_negative": false_accepts_neg,
            "adversarial_negative_rows": neg_rows,
            "real27_images": {
                "summary": _summarize_r27(real27_rows),
                "by_partition": {
                    part: _summarize_r27([r for r in real27_rows if r["partition"] == part])
                    for part in ("development", "frozen_external_evaluation", "fresh_external_evaluation")
                },
                "rows": real27_rows,
            },
            "external16_printed_images": {
                "summary": _summarize_ext(ext_printed_rows),
                "rows": ext_printed_rows,
            },
            "external16_handwritten_diagnostic": {
                "note": "Real student handwriting reported separately; never claimed as reliable printed OCR.",
                "summary": _summarize_ext(ext_hw_rows),
                "rows": ext_hw_rows,
            },
            "untouched_external_image_sets": {
                "new_external_12": _summarize_untouched(new_ext_rows),
                "new_image_corpus_8": {
                    "development": _summarize_untouched([r for r in nic8_rows if r["partition"] == "development"]),
                    "frozen_external_evaluation": _summarize_untouched([r for r in nic8_rows if r["partition"] == "frozen_external_evaluation"]),
                },
            },
            "vision_fallback_offline_mock": vision_fallback_mock,
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


async def _evaluate_frozen_unseen_vmmu20_async() -> dict[str, Any]:
    manifest = json.loads((RUN_DIR / "frozen_unseen_vmmu20_manifest.json").read_text(encoding="utf-8"))
    items = manifest.get("items") or []
    prev_py = os.environ.get("LOCAL_OCR_PYTHON")
    prev_tess = os.environ.get("LOCAL_OCR_TESSDATA")
    ocr_py = ROOT / ".superpowers/ocr-venv/Scripts/python.exe"
    ocr_tess = ROOT / ".superpowers/tessdata_fast"
    os.environ["LOCAL_OCR_PYTHON"] = str(ocr_py)
    os.environ["LOCAL_OCR_TESSDATA"] = str(ocr_tess)
    LO.clear_local_ocr_cache()

    rows: list[dict[str, Any]] = []
    cont_errors = 0
    try:
        for it in items:
            cid = it["case_id"]
            p = ROOT / it["cache_path"]
            raw_b = p.read_bytes()
            sha_actual = hashlib.sha256(raw_b).hexdigest()
            assert sha_actual == it["sha256"], f"SHA mismatch on frozen manifest item {cid}"
            mime, fname_use = _mime_and_name(raw_b, p)
            b64 = base64.b64encode(raw_b).decode("ascii")

            LO.clear_local_ocr_cache()
            t0 = time.perf_counter()
            cold = (await prepare_unified_input(content=b64, declared_mime=mime, filename=fname_use, api_key="", cache_version=M.CACHE_VERSION)).to_dict()
            cold_ms = round((time.perf_counter() - t0) * 1000.0, 2)

            t1 = time.perf_counter()
            warm = (await prepare_unified_input(content=b64, declared_mime=mime, filename=fname_use, api_key="", cache_version=M.CACHE_VERSION)).to_dict()
            warm_ms = round((time.perf_counter() - t1) * 1000.0, 2)

            prov = cold.get("provenance") or {}
            loc_ocr = prov.get("local_ocr") or {}
            spans = cold.get("uncertain_tokens") or []
            blocking_spans = [s for s in spans if s.get("blocking")]
            draft_text = cold.get("problem_text") or ""

            downstream_status = None
            downstream_code = None
            route_ms = None
            c_err = 0
            if cold.get("status") in ("ready", "needs_confirmation") and draft_text.strip():
                t2 = time.perf_counter()
                out = AIR.route_text_input(draft_text, allow_live_ai=False, input_kind="image")
                route_ms = round((time.perf_counter() - t2) * 1000.0, 2)
                downstream_status = out.status
                rd = (out.response or {}).get("route_d") or {}
                if out.status == "SERVED":
                    c_err = EUC._continuity_count((out.response or {}).get("envelope") or {})
                    cont_errors += c_err
                else:
                    ref = rd.get("refusal") or {}
                    downstream_code = ref.get("reason_code") or ref.get("code")

            rows.append(
                {
                    "case_id": cid,
                    "qid": it.get("qid"),
                    "hf_row_idx": it.get("hf_row_idx"),
                    "screen_bucket": it.get("screen_bucket"),
                    "sha256_verified": True,
                    "prepare_status": cold.get("status"),
                    "warm_prepare_status": warm.get("status"),
                    "ocr_decision": loc_ocr.get("ocr_decision") or prov.get("ocr_decision"),
                    "uncertain_spans_count": len(spans),
                    "blocking_uncertain_spans_count": len(blocking_spans),
                    "draft_text_len": len(draft_text),
                    "cold_prepare_ms": cold_ms,
                    "warm_prepare_ms": warm_ms,
                    "downstream_draft_route_status": downstream_status,
                    "downstream_draft_refusal_code": downstream_code,
                    "downstream_draft_route_ms": route_ms,
                    "scene3d_continuity_errors": c_err,
                    "ground_truth_status": "GROUND_TRUTH_UNVERIFIED",
                }
            )
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

    return {
        "ground_truth_status": "GROUND_TRUTH_UNVERIFIED",
        "independent_ground_truth_validation": "NOT_MEASURED",
        "status": "FROZEN_BEFORE_ANY_TUNING_OR_FINAL_EVAL",
        "manifest_path": "docs/evaluation/geometry/runs/student-ready-geometry-simulation-input-reliability/frozen_unseen_vmmu20_manifest.json",
        "note": (
            "19 unseen MIT anvo25/vmmu images frozen prior to tuning. Reported strictly separately for "
            "OCR readiness, latency, and continuity observation; zero oracle answer keys verified and "
            "NEVER merged into verified accuracy denominators."
        ),
        "total_items": len(rows),
        "screen_bucket_counts": dict(Counter(r["screen_bucket"] for r in rows)),
        "prepare_status_counts": dict(Counter(r["prepare_status"] for r in rows)),
        "ocr_decision_counts": dict(Counter(r["ocr_decision"] for r in rows)),
        "downstream_draft_route_status_counts": dict(Counter(r["downstream_draft_route_status"] for r in rows if r["downstream_draft_route_status"] is not None)),
        "scene3d_continuity_errors": cont_errors,
        "latency_cold_prepare_ms": ERWC._stats([r["cold_prepare_ms"] for r in rows]),
        "latency_warm_prepare_ms": ERWC._stats([r["warm_prepare_ms"] for r in rows]),
        "rows": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Run evaluation without writing STUDENT_READY_EVALUATION.json")
    args = ap.parse_args()

    baselines = ERWC._load_baselines()
    prior_eval_path = RUNS_DIR / "real-world-geometry-input-verified-simulation/REAL_WORLD_END_TO_END_EVALUATION.json"
    prior_eval = json.loads(prior_eval_path.read_text(encoding="utf-8")) if prior_eval_path.exists() else {}

    surfaces = EUC._check_surfaces()
    rm_eval = EAC._evaluate_reasoning_matrix()
    r1_eval = EAC._evaluate_r1_probe()
    nc_eval, cont_nc = EUC._run_nc_and_negatives()
    a4_eval, cont_a4 = EUC._run_a4_and_depth_bounds()
    dev_eval, cont_dev = EUC._run_exposed_dev_corpora()

    real25 = json.loads((RUNS_DIR / "controlled-vision-real-image-validation/new_in_scope_image_manifest.json").read_text(encoding="utf-8"))["items"]
    real2 = json.loads((RUNS_DIR / "local-semantic-source-gate-reliability/fresh_external_manifest.json").read_text(encoding="utf-8"))["items"]
    real27_forensics = _evaluate_real27_promotions_and_forensics(real25 + real2)

    ERWC._install_windows_socketpair_guard()
    loop = asyncio.new_event_loop()
    try:
        ocr_eval, cont_ocr = loop.run_until_complete(_evaluate_ocr_and_confirmation_v145_async(baselines, prior_eval))
        unseen_vmmu20 = loop.run_until_complete(_evaluate_frozen_unseen_vmmu20_async())
    finally:
        loop.close()

    hygiene_cache_145 = _run_learner_hygiene_and_cache_145_checks()
    c_safety = EUC._run_stream_c_safety()
    total_cont_errors = cont_nc + cont_a4 + cont_dev + cont_ocr + int(unseen_vmmu20["scene3d_continuity_errors"])

    measured_hash, measured_count = FZ.measured_system_hash()
    head_sha = ERWC._git_head()
    dirty_product = bool(
        subprocess.check_output(
            ["git", "status", "--porcelain", "--", "backend/app", "frontend/src"],
            cwd=ROOT,
            text=True,
        ).strip()
    )
    cand_doc = json.loads(FZ.OUT.read_text(encoding="utf-8"))
    freeze_matches = (
        cand_doc.get("cay_lam_viec_sach") is True
        and (cand_doc.get("measured_system") or {}).get("tree_hash") == measured_hash
        and (cand_doc.get("measured_system") or {}).get("so_file") == measured_count
        and cand_doc.get("product_commit_sha") == FZ.product_commit()
    )

    r27s = (ocr_eval.get("real27_images") or {}).get("summary") or {}
    e16s = (ocr_eval.get("external16_printed_images") or {}).get("summary") or {}
    rm_pos = rm_eval.get("positive_rows") or []
    rm_cls = dict(Counter((r.get("search_telemetry") or {}).get("classification") for r in rm_pos if r.get("status") == "SERVED"))
    rm_reuse = sum(1 for r in rm_pos if ((r.get("search_telemetry") or {}).get("reused_intermediates") or 0) > 0)
    rm_budget_exceeded = sum(1 for r in rm_pos if "BUDGET" in str(r.get("reason_code") or ""))

    r27_auto_n = int((r27s.get("ocr_decision_counts") or {}).get("LOCAL_OCR_ACCEPT", 0))
    r27_n = int(r27s.get("count", 0) or 0)
    r27_conf_n = int(r27s.get("confirmed_ready_count", 0) or 0)
    r27_conf_srv = int(r27s.get("confirmed_served", 0) or 0)
    e16_n = int(e16s.get("count", 0) or 0)
    e16_auto_n = int((e16s.get("ocr_decision_counts") or {}).get("LOCAL_OCR_ACCEPT", 0))
    e16_conf_n = int(e16s.get("confirmed_ready_count", 0) or 0)
    e16_conf_srv = int(e16s.get("confirmed_served_correct", 0) or 0)

    mandatory_metrics = {
        "ocr": {
            "character_error_rate_median_before_after_original_baseline": {
                "real27": [r27s.get("cer_before_median"), r27s.get("cer_after_median")],
                "external15_printed": [e16s.get("cer_before_median"), e16s.get("cer_after_median")],
            },
            "character_error_rate_median_v144_vs_v145": {
                "real27": [((prior_eval.get("ocr_before_after") or {}).get("real27_images") or {}).get("summary", {}).get("cer_after_median"), r27s.get("cer_after_median")],
                "external15_printed": [((prior_eval.get("ocr_before_after") or {}).get("external16_printed_images") or {}).get("summary", {}).get("cer_after_median"), e16s.get("cer_after_median")],
            },
            "critical_fact_preservation_rate_real27": {
                "draft": r27s.get("critical_facts_draft"),
                "after_span_confirmation": r27s.get("critical_facts_after_confirmation"),
                "after_span_confirmation_rate": r27s.get("critical_facts_after_rate"),
            },
            "region_selection_accuracy": {
                "rendered_positive": f"{ocr_eval.get('rendered_positive_accepted')}/{ocr_eval.get('rendered_positive_total')}",
                "ext15_selection_bands_served_correct": f"{e16s.get('selection_served_correct')}/{e16s.get('selection_bands_tested')}",
            },
            "safe_auto_accept_rate": {
                "real27": f"{r27_auto_n}/{r27_n}",
                "external15_printed": f"{e16_auto_n}/{e16_n}",
            },
            "false_auto_accept_rate": {
                "adversarial_negative": ocr_eval.get("false_auto_accepts_negative"),
                "real27": r27s.get("false_auto_accepts"),
                "external15_printed": e16s.get("false_auto_accepts"),
            },
            "review_rate_or_selection": {
                "real27_needs_confirmation": f"{r27_conf_n}/{r27_n}",
                "external15_needs_confirmation": f"{e16_conf_n}/{e16_n}",
                "external15_needs_selection": (e16s.get("prepare_status_counts") or {}).get("needs_selection", 0),
            },
            "span_only_scene3d_success_rate": {
                "real27": f"{r27_conf_srv}/{r27_conf_n}",
                "external15_printed": f"{e16_conf_srv}/{e16_conf_n}",
                "whole_draft_fallback_additional_real27": r27s.get("whole_draft_fallback_served", 0),
                "whole_draft_fallback_additional_ext15": e16s.get("whole_draft_fallback_served", 0),
            },
            "confirmation_effort_real27": {
                "median_actions": r27s.get("confirmation_median_actions"),
                "median_chars_typed": r27s.get("confirmation_median_chars_typed"),
                "chars_typed_vs_full_retype": f"{r27s.get('confirmation_total_chars_typed')}/{r27s.get('confirmation_total_full_retype_chars')}",
            },
            "ocr_latency_p50_p95_ms": {
                "real27_cold_prepare": r27s.get("latency_cold_prepare"),
                "real27_warm_prepare": r27s.get("latency_warm_prepare"),
                "external15_cold_prepare": e16s.get("latency_cold_prepare"),
                "external15_warm_prepare": e16s.get("latency_warm_prepare"),
            },
        },
        "understanding": {
            "real27_text_served_and_wrong": f"{dev_eval['real27_text']['served']}/{dev_eval['real27_text']['total']} (wrong={dev_eval['real27_text']['wrong_served']})",
            "real27_newly_promoted_from_v144": [r["case_id"] for r in real27_forensics["newly_promoted_from_144"]["rows"] if r["exact_match"]],
            "real27_remaining_refused_6_categories": real27_forensics["remaining_refused_6_categories"],
            "nc_nl_correct_rate": f"{nc_eval['nc_nl_passed']}/{nc_eval['nc_nl_total']}",
            "nc_gold_correct_rate": f"{nc_eval['nc_gold_passed']}/{nc_eval['nc_gold_total']}",
            "r513_missing_fact_detection_aligned": real27_forensics["r513_source_gate_alignment"]["verified"],
            "autonomous_negatives_correct_refusal_rate": f"{nc_eval['autonomous_negatives_refused']}/{nc_eval['autonomous_negatives_total']}",
            "false_complete_or_wrong_served_negatives": nc_eval["autonomous_negatives_false_served"],
        },
        "planner": {
            "valid_plan_rate_rm72_positive": f"{rm_eval['positive_served']}/{rm_eval['positive_total']}",
            "negative_refusal_rm72": f"{rm_eval['negative_refused']}/{rm_eval['negative_total']}",
            "classification_counts_rm72_served": rm_cls,
            "intermediate_reuse_cases_rm72": rm_reuse,
            "budget_exceeded_or_ir_limit_rm72": {
                "ir_or_search_budget_exceeded_rows": rm_budget_exceeded,
                "max_memory_declarations": 32,
                "mg9_planner_candidates_generated": ((rm_eval.get("mg9_root_cause_7_questions") or {}).get("q2_search_telemetry") or {}).get("candidate_count"),
            },
            "kernel_verification_continuity_errors": total_cont_errors,
            "planning_latency_p50_p95_ms_rm72": [rm_eval.get("latency_p50_ms"), rm_eval.get("latency_p95_ms")],
        },
        "end_to_end": {
            "text_to_verified_scene3d_real27": f"{dev_eval['real27_text']['served']}/{dev_eval['real27_text']['total']}",
            "image_to_verified_scene3d_without_confirmation_real27": f"{r27s.get('auto_served_correct', 0)}/{r27_n}",
            "image_to_verified_scene3d_after_span_confirmation_only_real27": f"{int(r27s.get('auto_served_correct', 0) or 0) + r27_conf_srv}/{r27_n}",
            "image_to_verified_scene3d_whole_draft_fallback_additional_real27": r27s.get("whole_draft_fallback_served", 0),
            "image_to_verified_scene3d_without_confirmation_ext15": f"{e16s.get('auto_served_correct', 0)}/{e16_n}",
            "image_to_verified_scene3d_after_span_confirmation_only_ext15": f"{int(e16s.get('auto_served_correct', 0) or 0) + e16_conf_srv}/{e16_n}",
            "image_to_verified_scene3d_ext15_selection_bands": f"{e16s.get('selection_served_correct', 0)}/{e16s.get('selection_bands_tested', 0)}",
            "image_to_verified_scene3d_whole_draft_fallback_additional_ext15": e16s.get("whole_draft_fallback_served", 0),
            "wrong_scene_served_total": (
                int(r27s.get("false_auto_accepts", 0) or 0)
                + int(r27s.get("confirmed_wrong_served", 0) or 0)
                + int(e16s.get("false_auto_accepts", 0) or 0)
                + int(e16s.get("confirmed_wrong_served", 0) or 0)
                + int(dev_eval["real27_text"]["wrong_served"])
            ),
            "scene_continuity_errors": total_cont_errors,
            "user_visible_output_policy_mode_a_compliant": c_safety["mode_a_trig_no_answer_leak"],
        },
    }

    report = {
        "schema": "axo-student-ready-evaluation/1",
        "run_id": "student-ready-geometry-simulation-input-reliability",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "measurement_class": "OFFLINE_DEVELOPMENT_AND_EXTERNAL_IMAGE_EVIDENCE",
        "independent_h1_validation": "NOT_MEASURED",
        "independent_generalization": "NOT_MEASURED",
        "real_student_usability": "NOT_MEASURED",
        "physical_low_end": "NOT_MEASURED",
        "frontend_integration": "BLOCKED_OWNERSHIP",
        "live_ai_calls": 0,
        "sealed_h1_rows_opened": 0,
        "locked_w2_w3_rows_read": 0,
        "git_head": head_sha,
        "product_commit": FZ.product_commit(),
        "working_tree_dirty_product": dirty_product,
        "freeze_candidate_matches": freeze_matches,
        "measured_system": measured_hash,
        "measured_files": measured_count,
        "cache_version": M.CACHE_VERSION,
        "route_d_cache_policy": M.ROUTE_D_CACHE_POLICY,
        "semantic_environment_hash": semantic_environment_hash(),
        "runtime_identity": runtime_identity(),
        "locked_surfaces": surfaces,
        "hygiene_and_cache_145": hygiene_cache_145,
        "comparison_baseline_v144": {
            "run_id": "real-world-geometry-input-verified-simulation",
            "product_commit": prior_eval.get("product_commit"),
            "cache_version": prior_eval.get("cache_version"),
            "mandatory_metrics_summary": (prior_eval.get("mandatory_metrics_9_3") or {}).get("end_to_end"),
        },
        "ocr_before_after": ocr_eval,
        "understanding_planning_and_verification": {
            "nc_and_autonomous_negatives": nc_eval,
            "a4_plane_constraints_and_depth": a4_eval,
            "reasoning_matrix_72": rm_eval,
            "r1_probe_19": r1_eval,
            "exposed_dev_corpora": dev_eval,
            "real27_v145_promotions_and_forensics": real27_forensics,
        },
        "mandatory_metrics": mandatory_metrics,
        "safety_invariants": {
            "total_scene3d_continuity_errors": total_cont_errors,
            **c_safety,
        },
        "frozen_unseen_vmmu20": unseen_vmmu20,
    }

    encoded = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    findings = pub_safety.findings_in(encoded)
    assert not findings, f"Publication safety violation: {findings}"
    assert ("APPROVED_BY" + "_USER") not in encoded.decode("utf-8")

    if not args.dry_run:
        out_path = RUN_DIR / "STUDENT_READY_EVALUATION.json"
        out_path.write_bytes(encoded)
    sha = hashlib.sha256(encoded).hexdigest()

    summary = {
        "surfaces_ok": surfaces["all_match"],
        "freeze_matches": freeze_matches,
        "product_commit": report["product_commit"][:12],
        "measured_system": measured_hash[:16],
        "cache_version": M.CACHE_VERSION,
        "worker_version": LO.LOCAL_OCR_WORKER_VERSION,
        "route_version": LR.LOCAL_OCR_ROUTE_VERSION,
        "reconcile_version": OR.OCR_RECONCILE_VERSION,
        "hygiene_and_cache_145": hygiene_cache_145["passed"],
        "glyph_topo": f"{ocr_eval.get('glyph_topology_passed')}/{ocr_eval.get('glyph_topology_total')}",
        "rendered_pos": f"{ocr_eval.get('rendered_positive_accepted')}/{ocr_eval.get('rendered_positive_total')}",
        "adv_neg_false_accepts": ocr_eval.get("false_auto_accepts_negative"),
        "real27_cer": f"{r27s.get('cer_before_median')} -> {r27s.get('cer_after_median')}",
        "real27_span_only_served": f"{r27_conf_srv}/{r27_conf_n}",
        "real27_whole_draft_fallback": r27s.get("whole_draft_fallback_served"),
        "ext15_span_only_served": f"{e16_conf_srv}/{e16_conf_n}",
        "ext15_auto_served": e16s.get("auto_served_correct"),
        "ext15_selection": f"{e16s.get('selection_served_correct')}/{e16s.get('selection_bands_tested')}",
        "real27_text": f"{dev_eval['real27_text']['served']}/{dev_eval['real27_text']['total']} (wrong={dev_eval['real27_text']['wrong_served']})",
        "promoted_r254_r277_r488": real27_forensics["newly_promoted_from_144"]["all_exact_match"],
        "unseen_vmmu20_items": unseen_vmmu20["total_items"],
        "unseen_vmmu20_decisions": unseen_vmmu20["ocr_decision_counts"],
        "continuity_errors": total_cont_errors,
        "mode_a_ok": c_safety["mode_a_trig_no_answer_leak"],
        "json_sha256": sha,
    }
    print(json.dumps(summary, ensure_ascii=False))

    ok = (
        surfaces["all_match"]
        and freeze_matches
        and not dirty_product
        and hygiene_cache_145["passed"]
        and ocr_eval.get("glyph_topology_passed") == 12
        and ocr_eval.get("rendered_positive_accepted") == 4
        and ocr_eval.get("false_auto_accepts_negative") == 0
        and r27s.get("false_auto_accepts", 0) == 0
        and r27s.get("confirmed_wrong_served", 0) == 0
        and e16s.get("false_auto_accepts", 0) == 0
        and e16s.get("confirmed_wrong_served", 0) == 0
        and ocr_eval.get("vision_fallback_offline_mock", {}).get("passed") is True
        and real27_forensics["newly_promoted_from_144"]["all_exact_match"] is True
        and real27_forensics["r513_source_gate_alignment"]["verified"] is True
        and nc_eval["nc_gold_passed"] == 21
        and nc_eval["nc_nl_passed"] == 21
        and nc_eval["autonomous_negatives_false_served"] == 0
        and a4_eval["all_passed"]
        and dev_eval["real27_text"]["wrong_served"] == 0
        and total_cont_errors == 0
        and c_safety["mode_a_trig_no_answer_leak"] is True
        and unseen_vmmu20["total_items"] == 19
        and unseen_vmmu20["scene3d_continuity_errors"] == 0
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
