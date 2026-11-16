# -*- coding: utf-8 -*-
"""End-to-End Campaign Offline Evaluator (`real-world-geometry-input-verified-simulation`).

Strictly offline (`ALLOW_LIVE_AI=0`, `GEMINI_API_KEY=""`, 0 live Gemini/Vision API calls).
Never reads sealed `H-1` or locked `W2`/`W3`, and never edits `axo-geometry-library`.

Measures:
  1. Locked extraction surfaces (4 SHA-256 fingerprints) + cache version `144`.
  2. Stream B (Real-World Image -> OCR -> Confirmation/Selection -> Grounding -> Kernel -> Scene3D):
     - `glyph_topology` (12/12 via real sidecar worker: superscript, radical, perp, parallel, equals vs minus)
     - `rendered_positive` (4/4 LOCAL_OCR_ACCEPT + exact served answer)
     - `adversarial_negative` (3/3 LOCAL_OCR_REVIEW_REQUIRED, 0 false auto-accepts)
     - `real27_images` (27 cached images split by development vs frozen/fresh external; before/after CER,
       blocking spans, zero-text spans, critical-fact preservation, safe auto-accept vs review, 0 false
       auto-accepts, simulated minimal confirmation + effort + provenance contract + Scene3D continuity,
       and cold vs warm stage-by-stage p50/p95 latencies inside ONE asyncio event loop)
     - `external16_images` (15 printed + 1 handwritten reported separately, plus multi-problem band
       selection/switching on `ext_prt_03` and `ext_prt_08`)
     - `untouched_external_image_sets` reported separately: `new_external_12` and `new_image_corpus_8`
       (split development [2] vs frozen_external_evaluation [6])
     - Deterministic offline Vision-fallback mock + edited confirmation cache/provenance separation
  3. Stream A & C (Understanding, Autonomous Planning, Source Gate, Scene3D, Mode A):
     - `REAL27_TEXT` (27) with full 9-refusal & 3-adjudication forensics (`vmmu_r513` Source Gate fix)
     - `NC-*` (21/21 Gold & NL + 11/11 neg), `A4` & depth (6/6), `reasoning_matrix` (72 + MG9), `r1_probe` (19)
     - `DEV37` (37), `COMP112` (112), `PROBES39` (39), `Scene3D` continuity (0 errors), Mode A (`0` leaks)
"""
from __future__ import annotations

import argparse
import asyncio
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time
from typing import Any

RUN_DIR = Path(__file__).resolve().parents[1]
RUNS_DIR = RUN_DIR.parent
ROOT = RUN_DIR.parents[4]
BACKEND = ROOT / "backend"

for _p in (
    BACKEND,
    BACKEND / "scripts",
    BACKEND / "tests" / "geometry",
    RUNS_DIR / "unified-geometry-understanding-ocr-autonomous-planning" / "tools",
    RUNS_DIR / "planner-autonomous-composition-and-search-efficiency" / "tools",
    RUNS_DIR / "hybrid-reasoning-generalization" / "tools",
    RUNS_DIR / "semantic-failure-safe-image-segmentation" / "tools",
    RUNS_DIR / "dimension-aware-verified-construction" / "tools",
    RUNS_DIR / "independent-geometry-plane-constraints" / "tools",
    RUNS_DIR / "controlled-vision-real-image-validation" / "tools",
    RUNS_DIR / "image-first-ocr-verified-geometry" / "tools",
    RUNS_DIR / "real-world-printed-handwriting-acquisition" / "tools",
    RUNS_DIR / "real-image-ocr-vision-comparative-acceptance" / "tools",
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("HYBRID_ROUTE_MODE", None)
os.environ.pop("LOCAL_OCR_PYTHON", None)
os.environ.pop("LOCAL_OCR_TESSDATA", None)

import check_publication_safety as pub_safety  # noqa: E402
import evaluate_autonomous_composition as EAC  # noqa: E402
import evaluate_image_first_ocr as EIFO  # noqa: E402
import evaluate_images as EVI  # noqa: E402
import evaluate_unified_campaign as EUC  # noqa: E402
import freeze_evaluation_candidate as FZ  # noqa: E402
import new_external_catalog as NEC  # noqa: E402
from build_corpus import fact_norm  # noqa: E402
from corpus_catalog import CORPUS_ITEMS  # noqa: E402
from ocr_scoring_helpers import compute_cer_wer  # noqa: E402

# EIFO calls os.environ.setdefault("LOCAL_OCR_PYTHON", ...) at import time; enforce clean default state here.
os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("HYBRID_ROUTE_MODE", None)
os.environ.pop("LOCAL_OCR_PYTHON", None)
os.environ.pop("LOCAL_OCR_TESSDATA", None)

from app.ai import adaptive_input_router as AIR  # noqa: E402
from app.ai.hybrid_offline import prepare_local_first_hybrid, resolve_hybrid_gemini_model  # noqa: E402
from app.ai.local_geometry_parser import (  # noqa: E402
    LOCAL_PARSE_COMPLETE,
    clear_local_geometry_parser_cache,
    parse_geometry_problem_locally,
)
from app.ingestion import local_ocr as LO  # noqa: E402
from app.ingestion import local_ocr_route as LR  # noqa: E402
from app.ingestion import ocr_reconcile as OR  # noqa: E402
from app.ingestion.image import normalize_image  # noqa: E402
from app.ingestion.region_detector import detect_problem_regions  # noqa: E402
from app.ingestion.unified_input import prepare_unified_input  # noqa: E402
from app.main import (  # noqa: E402
    CACHE_VERSION,
    ROUTE_D_CACHE_POLICY,
    InputSourceProvenance,
    build_verified_input_provenance,
)
from app.runtime_identity import runtime_identity, semantic_environment_hash  # noqa: E402
from app.simulation.geometry_functions.construction_continuity import (  # noqa: E402
    validate_construction_continuity,
)


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _percentile(vals: list[float], p: float) -> float:
    return EUC._percentile(vals, p)


def _stats(vals: list[float]) -> dict[str, Any]:
    clean = [round(float(v), 2) for v in vals if v is not None]
    if not clean:
        return {"n": 0, "p50": None, "p95": None, "mean": None}
    return {
        "n": len(clean),
        "p50": round(float(statistics.median(clean)), 2),
        "p95": _percentile(clean, 0.95),
        "mean": round(sum(clean) / len(clean), 2),
    }


def _continuity_count(env: dict[str, Any] | None) -> int:
    sc = (env or {}).get("scene3d")
    if not sc:
        return 0
    return len(validate_construction_continuity(sc))


def _mime_and_name(raw_b: bytes, p: Path) -> tuple[str, str]:
    if raw_b.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", p.with_suffix(".png").name
    if raw_b.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", p.with_suffix(".jpg").name
    if raw_b.startswith(b"RIFF") and b"WEBP" in raw_b[:16]:
        return "image/webp", p.with_suffix(".webp").name
    return ("image/jpeg" if p.suffix.lower() in (".jpg", ".jpeg") else "image/png"), p.name


def _critical_fact_stats(text: str, *, critical_facts: list[dict[str, Any]] | None = None, fact_texts: list[str] | None = None) -> dict[str, Any]:
    norm_txt = fact_norm(text or "")
    if critical_facts is not None:
        rows = [
            {
                "kind": f["kind"],
                "reference": f["accepted_forms"][0],
                "recovered": any(fact_norm(form) in norm_txt for form in f["accepted_forms"]),
            }
            for f in critical_facts
        ]
        rec = sum(1 for r in rows if r["recovered"])
        return {"recovered": rec, "total": len(rows), "all_recovered": rec == len(rows), "items": rows}
    if fact_texts is not None:
        rows = [{"reference": t, "recovered": fact_norm(t) in norm_txt} for t in fact_texts]
        rec = sum(1 for r in rows if r["recovered"])
        return {"recovered": rec, "total": len(rows), "all_recovered": rec == len(rows), "items": rows}
    return {"recovered": 0, "total": 0, "all_recovered": True, "items": []}


def _critical_math_token_prf(hyp: str, ref: str) -> dict[str, Any]:
    return EIFO._prf(EIFO._math_tokens(hyp or ""), EIFO._math_tokens(ref or ""))


def _load_baselines() -> dict[str, Any]:
    prior_eval_p = RUNS_DIR / "unified-geometry-understanding-ocr-autonomous-planning" / "END_TO_END_CAPABILITY_EVALUATION.json"
    prior_eval = json.loads(prior_eval_p.read_text(encoding="utf-8"))
    ext16_p = RUNS_DIR / "image-first-ocr-verified-geometry" / "external16_image_diagnostics.json"
    ext16_diag = json.loads(ext16_p.read_text(encoding="utf-8"))
    dump_p = ROOT / ".superpowers" / "offline-logs" / "real_world_ocr_forensic_dump.json"
    dump = json.loads(dump_p.read_text(encoding="utf-8")) if dump_p.exists() else {}

    real27_prior_rows = {
        r["case_id"]: r for r in (prior_eval.get("stream_b", {}).get("real27_images", {}).get("rows") or [])
    }
    ext16_prior_rows = {c["image_id"]: c for c in ext16_diag.get("cases") or []}
    dump_real27 = {r["id"]: r for r in dump.get("real27") or []}
    dump_ext15 = {r["id"]: r for r in dump.get("ext15") or []}
    return {
        "prior_eval_meta": {
            "run_id": prior_eval.get("run_id"),
            "product_commit": prior_eval.get("product_commit"),
            "ocr_reconcile_version": prior_eval.get("stream_b", {}).get("ocr_reconcile_version"),
        },
        "real27_summary": {
            k: v
            for k, v in (prior_eval.get("stream_b", {}).get("real27_images") or {}).items()
            if k != "rows"
        },
        "ext15_summary": {
            k: v
            for k, v in (prior_eval.get("stream_b", {}).get("external16_printed_images") or {}).items()
            if k != "rows"
        },
        "real27_prior_rows": real27_prior_rows,
        "ext16_prior_rows": ext16_prior_rows,
        "dump_real27": dump_real27,
        "dump_ext15": dump_ext15,
    }


def _run_text_forensics(real27_items: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    refused_layers: Counter[str] = Counter()
    adj_rows = []
    for it in real27_items:
        cid = it["case_id"]
        txt = it["ground_truth_text"]
        clear_local_geometry_parser_cache()
        lp = parse_geometry_problem_locally(txt)
        out = AIR.route_text_input(txt, allow_live_ai=False)
        rd = (out.response or {}).get("route_d") or {}
        env = (out.response or {}).get("envelope") or {}
        rc = env.get("reason_code") or (out.receipt or {}).get("code")
        det_audit = (out.receipt or {}).get("determinacy_audit") or rd.get("determinacy_audit")
        if out.status != "SERVED":
            layer = (
                "OUT_OF_SCOPE_OR_NON_CONVEX"
                if "NON_CONVEX" in str(rc) or cid == "vmmu_r475"
                else ("LOCAL_PARSER_OR_TYPED_FACT_GAP" if lp.status != LOCAL_PARSE_COMPLETE else "KERNEL_OR_SOURCE_GATE_BOUNDARY")
            )
            refused_layers[layer] += 1
            rows.append({
                "case_id": cid,
                "partition": it.get("partition"),
                "local_parse_status": lp.status,
                "local_parse_reason": lp.reason_code,
                "route_status": out.status,
                "reason_code": rc,
                "layer": layer,
                "determinacy_audit_status": (det_audit or {}).get("status") if isinstance(det_audit, dict) else None,
            })
        elif rd.get("source_goal_completion") is not None:
            sgc = rd.get("source_goal_completion") or {}
            adj_rows.append({
                "case_id": cid,
                "partition": it.get("partition"),
                "answers_internal": rd.get("answers"),
                "expected_answer": it.get("expected_answer"),
                "numeric_answer_shown": sgc.get("numeric_answer_shown"),
                "numeric_source_goal": (sgc.get("goals") or [{}])[0].get("numeric_source_goal"),
                "continuity_errors": _continuity_count(env),
            })
    r513 = next((r for r in rows if r["case_id"] == "vmmu_r513"), None)
    return {
        "refused_count": len(rows),
        "refused_layer_counts": dict(refused_layers),
        "refused_cases": rows,
        "adjudicated_mode_a_count": len(adj_rows),
        "adjudicated_mode_a_cases": adj_rows,
        "r513_source_gate_alignment": {
            "verified": bool(
                r513
                and r513["local_parse_status"] == LOCAL_PARSE_COMPLETE
                and r513["route_status"] == "REFUSED"
                and r513["reason_code"] == "MISSING_DIMENSION"
                and r513["determinacy_audit_status"] == "UNPROVED_DUE_TO_CAPABILITY_GAP"
            ),
            "details": r513,
        },
    }


async def _evaluate_ocr_and_confirmation_async(baselines: dict[str, Any]) -> tuple[dict[str, Any], int]:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    cont_errors = 0
    ocr_py = ROOT / ".superpowers" / "ocr-venv" / "Scripts" / "python.exe"
    ocr_tess = ROOT / ".superpowers" / "tessdata_fast"

    # Non-negotiable invariant checks that always run
    assert not OR.has_shared_corruption("120°")
    assert not OR.has_shared_corruption("150°")
    assert OR.has_shared_corruption("600°") is True
    assert OR.has_shared_corruption("S,ABCD") is True
    assert LO.LOCAL_OCR_WORKER_VERSION == "local-ocr-worker/3"
    assert OR.OCR_RECONCILE_VERSION == "layout-aware-ocr-reconcile/3"
    assert LR.LOCAL_OCR_ROUTE_VERSION == "local-ocr-route/2"

    if not ocr_py.exists() or not ocr_tess.is_dir():
        return {"available": False, "reason": "SIDECAR_NOT_PRESENT"}, 0

    prev_py = os.environ.get("LOCAL_OCR_PYTHON")
    prev_tess = os.environ.get("LOCAL_OCR_TESSDATA")
    os.environ["LOCAL_OCR_PYTHON"] = str(ocr_py)
    os.environ["LOCAL_OCR_TESSDATA"] = str(ocr_tess)
    LO.clear_local_ocr_cache()

    try:
        # 1. Glyph topology probes (12/12 including '=' vs '-')
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

        # 2. Rendered positive (4/4) & adversarial negative (3/3)
        rendered_pos = [
            ("pos_area_a2", "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a². Tính khoảng cách từ A đến mặt phẳng (SBC).", "a√6/3"),
            ("pos_2a_sqrt3", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA vuông góc với (ABCD) và SA = a√3. Tính thể tích khối chóp S.ABCD.", "4a³√3/3"),
            ("pos_area_frac_a2_2", "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại B, diện tích tam giác ABC bằng a²/2, SA vuông góc với (ABC) và SA = a. Tính thể tích khối chóp S.ABC.", "a³/6"),
            ("pos_cm_cm2", "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3cm và diện tích đáy bằng 9cm². Tính khoảng cách từ A đến mặt phẳng (SBC).", "√6"),
        ]
        pos_rows = []
        for pid, txt, want_ans in rendered_pos:
            im = Image.new("RGB", (1320, 220), "white")
            dr = ImageDraw.Draw(im)
            lines_out, cur = [], ""
            for w in txt.split():
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
            prep = (await prepare_unified_input(content=b64, declared_mime="image/png", filename=f"{pid}.png", api_key="", cache_version=CACHE_VERSION)).to_dict()
            pms = round((time.perf_counter() - t0) * 1000.0, 2)
            dec = (prep.get("provenance") or {}).get("ocr_decision")
            ans_got, routed_status = None, None
            if prep["status"] == "ready":
                routed = AIR.route_text_input(prep["problem_text"], allow_live_ai=False, input_kind="image")
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

        neg_specs = [
            ("neg_inline_a2", "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a2. Tính thể tích khối chóp S.ABCD.", False),
            ("neg_blurry_crop", "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a². Tính thể tích khối chóp S.ABCD.", True),
            ("neg_diagram_ref", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a (tham khảo hình vẽ). Tính thể tích khối chóp S.ABCD.", False),
        ]
        neg_rows = []
        false_accepts = 0
        for nid, txt, do_blur in neg_specs:
            im = Image.new("RGB", (1320, 200), "white")
            dr = ImageDraw.Draw(im)
            dr.text((36, 40), txt[:70], fill="black", font=font)
            dr.text((36, 96), txt[70:].strip(), fill="black", font=font)
            if do_blur:
                im = im.filter(ImageFilter.GaussianBlur(radius=2.2))
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            prep = (await prepare_unified_input(content=b64, declared_mime="image/png", filename=f"{nid}.png", api_key="", cache_version=CACHE_VERSION)).to_dict()
            dec = (prep.get("provenance") or {}).get("ocr_decision")
            if dec == "LOCAL_OCR_ACCEPT" or prep["status"] == "ready":
                false_accepts += 1
            neg_rows.append({
                "id": nid,
                "prepare_status": prep["status"],
                "ocr_decision": dec,
                "blocked": dec != "LOCAL_OCR_ACCEPT" and prep["status"] != "ready",
            })

        # 3. Helper to run single image end-to-end with confirmation simulation
        async def _eval_single_image(
            *,
            cid: str,
            raw_b: bytes,
            filename: str,
            gt: str,
            grade_fn: Any,
            critical_facts: list[dict[str, Any]] | None = None,
            fact_texts: list[str] | None = None,
            partition: str | None = None,
            measure_cold_breakdown: bool = False,
        ) -> tuple[dict[str, Any], int]:
            local_cont = 0
            p_path = Path(filename)
            mime, fname_use = _mime_and_name(raw_b, p_path)
            b64 = base64.b64encode(raw_b).decode("ascii")

            stage_timing: dict[str, Any] = {}
            blocking_spans_count = None
            zero_text_spans_count = None
            diagram_class = None

            if measure_cold_breakdown:
                LO.clear_local_ocr_cache()
                t0 = time.perf_counter()
                norm = normalize_image(raw_b)
                t_norm = time.perf_counter()
                rr = detect_problem_regions(norm)
                t_reg = time.perf_counter()
                rec = LR.run_local_ocr_route(rr.prepared_image.data, rr.prepared_figure_bboxes())
                t_rec = time.perf_counter()
                tm = rec.get("timing") or {}
                rb = tm.get("reread_breakdown") or {}
                unc = rec.get("uncertain_spans") or []
                blocking_spans_count = sum(1 for s in unc if s.get("blocking"))
                zero_text_spans_count = sum(1 for s in unc if s.get("text") == "0")
                diagram_class = (rec.get("diagram") or {}).get("classification")
                stage_timing = {
                    "normalize_ms": round((t_norm - t0) * 1000.0, 2),
                    "region_detect_ms": round((t_reg - t_norm) * 1000.0, 2),
                    "route_total_ms": round((t_rec - t_reg) * 1000.0, 2),
                    "decode_ms": tm.get("decode_ms"),
                    "tesseract_ms": tm.get("tesseract_ms"),
                    "rapidocr_ms": tm.get("rapidocr_ms"),
                    "reconcile_only_ms": tm.get("reconcile_only_ms"),
                    "reread_ms": tm.get("reread_ms"),
                    "reread_crop_ms": rb.get("crop_ms"),
                    "reread_topology_ms": rb.get("topology_ms"),
                    "reread_latin_rec_ms": rb.get("latin_rec_ms"),
                    "reread_tess_eng_ms": rb.get("tess_eng_ms"),
                    "reread_tess_vie_ms": rb.get("tess_vie_ms"),
                }

            # Cold prepare timing (fresh local OCR cache)
            LO.clear_local_ocr_cache()
            t_p0 = time.perf_counter()
            prep = (await prepare_unified_input(content=b64, declared_mime=mime, filename=fname_use, api_key="", cache_version=CACHE_VERSION)).to_dict()
            cold_prepare_ms = round((time.perf_counter() - t_p0) * 1000.0, 2)

            # Warm prepare timing (hitting _RAW_OCR_CACHE & _REREAD_CACHE)
            t_w0 = time.perf_counter()
            prep_warm = (await prepare_unified_input(content=b64, declared_mime=mime, filename=fname_use, api_key="", cache_version=CACHE_VERSION)).to_dict()
            warm_prepare_ms = round((time.perf_counter() - t_w0) * 1000.0, 2)
            assert prep_warm["status"] == prep["status"]

            prov = prep.get("provenance") or {}
            dec = prov.get("ocr_decision")
            draft = prep.get("problem_text") or ""
            cer = EUC._cer(draft, gt) if (draft and gt) else None
            wer = EIFO._wer(draft, gt) if (draft and gt) else None
            math_prf = _critical_math_token_prf(draft, gt) if (draft and gt) else None
            cf_draft = _critical_fact_stats(draft, critical_facts=critical_facts, fact_texts=fact_texts)

            # Provenance contract check on raw auto/review draft
            raw_sha = prov.get("raw_ocr_text_sha256")
            prep_origin = prov.get("input_route") or "local_ocr"

            row: dict[str, Any] = {
                "case_id": cid,
                "partition": partition,
                "prepare_status": prep["status"],
                "reason_code": prep.get("reason_code"),
                "ocr_decision": dec,
                "cer": cer,
                "wer": wer,
                "math_tokens_prf": math_prf,
                "critical_facts_draft": cf_draft,
                "blocking_uncertain_spans": blocking_spans_count,
                "zero_text_spans": zero_text_spans_count,
                "diagram_classification": diagram_class,
                "review_items_count": len(prep.get("uncertain_tokens") or []),
                "candidates_count": len(prep.get("candidates") or []),
                "confirmation_contract_version": prov.get("confirmation_contract_version"),
                "cold_prepare_ms": cold_prepare_ms,
                "warm_prepare_ms": warm_prepare_ms,
                "stage_timing_ms": stage_timing,
                "auto_route": None,
                "confirmation_simulated": None,
            }

            if prep["status"] == "ready" and draft:
                clear_local_geometry_parser_cache()
                t_s0 = time.perf_counter()
                routed = AIR.route_text_input(draft, allow_live_ai=False, input_kind="image")
                solve_ms = round((time.perf_counter() - t_s0) * 1000.0, 2)
                rd = (routed.response or {}).get("route_d") or {}
                env = (routed.response or {}).get("envelope") or {}
                c_err = _continuity_count(env) if routed.status == "SERVED" else 0
                local_cont += c_err
                ans = rd.get("answers") if routed.status == "SERVED" else None
                g = grade_fn(routed.status, ans, rd, env)
                p_rec = build_verified_input_provenance(
                    draft,
                    InputSourceProvenance(
                        origin="local_ocr_auto_verified" if dec == "LOCAL_OCR_ACCEPT" else "local_ocr_student_confirmed",
                        raw_ocr_text_sha256=raw_sha,
                        prepared_region_sha256=prov.get("prepared_region_sha256"),
                        student_edited=False,
                    ),
                )
                row["auto_route"] = {
                    "routed_status": routed.status,
                    "answers": ans,
                    "grade": g,
                    "continuity_errors": c_err,
                    "scene3d_objects": len((env.get("scene3d") or {}).get("objects") or []) if routed.status == "SERVED" else 0,
                    "solve_ms": solve_ms,
                    "provenance": p_rec,
                    "false_auto_accept": (dec == "LOCAL_OCR_ACCEPT" and routed.status == "SERVED" and g.get("verdict") == "WRONG_SERVED"),
                }
            elif prep["status"] == "needs_confirmation" and draft:
                sim = EIFO.simulate_student(draft, prep.get("uncertain_tokens") or [], gt)
                confirmed_text = sim["text"]
                cf_after = _critical_fact_stats(confirmed_text, critical_facts=critical_facts, fact_texts=fact_texts)
                clear_local_geometry_parser_cache()
                t_s0 = time.perf_counter()
                routed = AIR.route_text_input(confirmed_text, allow_live_ai=False, input_kind="image")
                solve_ms = round((time.perf_counter() - t_s0) * 1000.0, 2)
                rd = (routed.response or {}).get("route_d") or {}
                env = (routed.response or {}).get("envelope") or {}
                c_err = _continuity_count(env) if routed.status == "SERVED" else 0
                local_cont += c_err
                ans = rd.get("answers") if routed.status == "SERVED" else None
                g = grade_fn(routed.status, ans, rd, env)
                p_rec = build_verified_input_provenance(
                    confirmed_text,
                    InputSourceProvenance(
                        origin="local_ocr_student_confirmed",
                        raw_ocr_text_sha256=raw_sha,
                        prepared_region_sha256=prov.get("prepared_region_sha256"),
                        confirmed_span_count=len(prep.get("uncertain_tokens") or []),
                        student_edited=bool(sim["edits"]),
                    ),
                )
                assert p_rec is not None and p_rec["counted_as_unmodified_auto_ocr"] is False
                row["confirmation_simulated"] = {
                    "cer_after": EUC._cer(confirmed_text, gt) if gt else None,
                    "critical_facts_after": cf_after,
                    "edits": sim["edits"],
                    "edit_count": len(sim["edits"]),
                    "confirms": sim["confirms"],
                    "diagram_confirms": sim["diagram_confirms"],
                    "actions": sim["actions"],
                    "chars_typed": sim["chars_typed"],
                    "full_retype_chars": len(gt),
                    "routed_status": routed.status,
                    "reason_code": env.get("reason_code") or (routed.receipt or {}).get("code"),
                    "answers": ans,
                    "grade": g,
                    "continuity_errors": c_err,
                    "scene3d_objects": len((env.get("scene3d") or {}).get("objects") or []) if routed.status == "SERVED" else 0,
                    "solve_ms": solve_ms,
                    "provenance": p_rec,
                }
            elif prep["status"] == "needs_selection":
                # Multi-problem band switching flow
                sel_outcomes = []
                gt_parts = []
                # Find verbatim parts if provided for external16
                cat_match = next((c for c in CORPUS_ITEMS if c.get("image_id") == cid), None)
                if cat_match:
                    gt_parts = cat_match.get("verbatim_problem_texts") or []
                for idx, cand in enumerate(prep.get("candidates") or []):
                    sub_prep = (await prepare_unified_input(
                        content=b64,
                        declared_mime=mime,
                        filename=fname_use,
                        api_key="",
                        cache_version=CACHE_VERSION,
                        selected_candidate_id=cand["candidate_id"],
                    )).to_dict()
                    sub_text = sub_prep.get("problem_text") or ""
                    sub_gt = gt_parts[idx] if idx < len(gt_parts) else gt
                    if sub_prep["status"] == "needs_confirmation" and sub_text and sub_gt:
                        sub_sim = EIFO.simulate_student(sub_text, sub_prep.get("uncertain_tokens") or [], sub_gt)
                        final_sub = sub_sim["text"]
                        edits_n = len(sub_sim["edits"])
                    else:
                        final_sub = sub_text
                        edits_n = 0
                    clear_local_geometry_parser_cache()
                    sub_routed = AIR.route_text_input(final_sub, allow_live_ai=False, input_kind="image") if final_sub else None
                    sub_rd = ((sub_routed.response or {}).get("route_d") or {}) if sub_routed else {}
                    sub_env = ((sub_routed.response or {}).get("envelope") or {}) if sub_routed else {}
                    c_err = _continuity_count(sub_env) if (sub_routed and sub_routed.status == "SERVED") else 0
                    local_cont += c_err
                    sub_ans = sub_rd.get("answers") if (sub_routed and sub_routed.status == "SERVED") else None
                    sub_key = f"{cid}#{idx + 1}"
                    sub_oracle = EIFO.grade(sub_key, {"answers": sub_ans}) if sub_key in EIFO.ORACLE else None
                    sel_outcomes.append({
                        "candidate_id": cand["candidate_id"],
                        "label": cand.get("label"),
                        "prepare_status": sub_prep["status"],
                        "edits": edits_n,
                        "routed_status": sub_routed.status if sub_routed else None,
                        "answers": sub_ans,
                        "oracle_verdict": sub_oracle,
                        "continuity_errors": c_err,
                    })
                row["selection_outcomes"] = sel_outcomes

            return row, local_cont

        # 4. Evaluate REAL27 (27 images)
        real25 = json.loads((RUNS_DIR / "controlled-vision-real-image-validation/new_in_scope_image_manifest.json").read_text(encoding="utf-8"))["items"]
        real2 = json.loads((RUNS_DIR / "local-semantic-source-gate-reliability/fresh_external_manifest.json").read_text(encoding="utf-8"))["items"]
        real27_items = real25 + real2

        real27_rows = []
        for it in real27_items:
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

            row, l_cont = await _eval_single_image(
                cid=cid,
                raw_b=p.read_bytes(),
                filename=p.name,
                gt=it["ground_truth_text"],
                grade_fn=_grade_real27,
                critical_facts=it.get("critical_facts"),
                partition=it.get("partition"),
                measure_cold_breakdown=True,
            )
            cont_errors += l_cont
            prior_r = baselines["real27_prior_rows"].get(cid) or {}
            dump_r = baselines["dump_real27"].get(cid) or {}
            row["before_baseline"] = {
                "cer": prior_r.get("cer"),
                "ocr_decision": prior_r.get("ocr_decision"),
                "blocking_uncertain_spans": dump_r.get("uncertain_blocking_count"),
                "zero_text_spans": (
                    sum(1 for u in (dump_r.get("uncertain_blocking") or []) if u.get("text") == "0")
                    if dump_r else None
                ),
            }
            real27_rows.append(row)

        def _summarize_real27(subset: list[dict[str, Any]]) -> dict[str, Any]:
            if not subset:
                return {"count": 0}
            cers_after = [r["cer"] for r in subset if r["cer"] is not None]
            cers_before = [r["before_baseline"]["cer"] for r in subset if r["before_baseline"].get("cer") is not None]
            block_after = [r["blocking_uncertain_spans"] for r in subset if r["blocking_uncertain_spans"] is not None]
            block_before = [r["before_baseline"]["blocking_uncertain_spans"] for r in subset if r["before_baseline"].get("blocking_uncertain_spans") is not None]
            z_after = [r["zero_text_spans"] for r in subset if r["zero_text_spans"] is not None]
            z_before = [r["before_baseline"]["zero_text_spans"] for r in subset if r["before_baseline"].get("zero_text_spans") is not None]
            cf_rec = sum(r["critical_facts_draft"]["recovered"] for r in subset)
            cf_tot = sum(r["critical_facts_draft"]["total"] for r in subset)
            cf_after_rec = sum(
                (r["confirmation_simulated"]["critical_facts_after"]["recovered"] if r["confirmation_simulated"] else r["critical_facts_draft"]["recovered"])
                for r in subset
            )
            mt_tp = sum((r["math_tokens_prf"] or {}).get("tp", 0) for r in subset)
            mt_ref = sum((r["math_tokens_prf"] or {}).get("ref", 0) for r in subset)
            auto_rows = [r for r in subset if r["auto_route"] is not None]
            conf_rows = [r for r in subset if r["confirmation_simulated"] is not None]
            return {
                "count": len(subset),
                "ocr_decision_counts": dict(Counter(r["ocr_decision"] for r in subset)),
                "cer_before_median": round(statistics.median(cers_before), 4) if cers_before else None,
                "cer_after_median": round(statistics.median(cers_after), 4) if cers_after else None,
                "cer_after_mean": round(sum(cers_after) / len(cers_after), 4) if cers_after else None,
                "blocking_spans_before": sum(block_before) if block_before else None,
                "blocking_spans_after": sum(block_after) if block_after else None,
                "zero_text_spans_before": sum(z_before) if z_before else None,
                "zero_text_spans_after": sum(z_after) if z_after else None,
                "math_token_recall_draft": round(mt_tp / max(1, mt_ref), 4),
                "critical_facts_draft": f"{cf_rec}/{cf_tot}",
                "critical_facts_after_confirmation": f"{cf_after_rec}/{cf_tot}",
                "critical_facts_after_rate": round(cf_after_rec / max(1, cf_tot), 4),
                "false_auto_accepts": sum(1 for r in auto_rows if r["auto_route"].get("false_auto_accept")),
                "auto_served_correct": sum(1 for r in auto_rows if r["auto_route"].get("routed_status") == "SERVED" and r["auto_route"].get("grade", {}).get("verdict") != "WRONG_SERVED"),
                "confirmed_ready_count": len(conf_rows),
                "confirmed_served": sum(1 for r in conf_rows if r["confirmation_simulated"].get("routed_status") == "SERVED"),
                "confirmed_wrong_served": sum(1 for r in conf_rows if r["confirmation_simulated"].get("grade", {}).get("verdict") == "WRONG_SERVED"),
                "confirmation_median_actions": statistics.median([r["confirmation_simulated"]["actions"] for r in conf_rows]) if conf_rows else 0,
                "confirmation_median_chars_typed": statistics.median([r["confirmation_simulated"]["chars_typed"] for r in conf_rows]) if conf_rows else 0,
                "confirmation_total_chars_typed": sum(r["confirmation_simulated"]["chars_typed"] for r in conf_rows),
                "confirmation_total_full_retype_chars": sum(r["confirmation_simulated"]["full_retype_chars"] for r in conf_rows),
                "latency_cold_prepare": _stats([r["cold_prepare_ms"] for r in subset]),
                "latency_warm_prepare": _stats([r["warm_prepare_ms"] for r in subset]),
                "latency_stage_breakdown": {
                    k: _stats([r["stage_timing_ms"].get(k) for r in subset if r["stage_timing_ms"].get(k) is not None])
                    for k in ("normalize_ms", "region_detect_ms", "decode_ms", "tesseract_ms", "rapidocr_ms", "reconcile_only_ms", "reread_ms")
                },
                "latency_solve": _stats([
                    (r["auto_route"]["solve_ms"] if r["auto_route"] else r["confirmation_simulated"]["solve_ms"])
                    for r in subset if (r["auto_route"] or r["confirmation_simulated"])
                ]),
                "latency_cold_end_to_end": _stats([
                    r["cold_prepare_ms"] + (r["auto_route"]["solve_ms"] if r["auto_route"] else (r["confirmation_simulated"]["solve_ms"] if r["confirmation_simulated"] else 0.0))
                    for r in subset
                ]),
                "latency_warm_end_to_end": _stats([
                    r["warm_prepare_ms"] + (r["auto_route"]["solve_ms"] if r["auto_route"] else (r["confirmation_simulated"]["solve_ms"] if r["confirmation_simulated"] else 0.0))
                    for r in subset
                ]),
            }

        # 5. Evaluate EXTERNAL16 (15 printed + 1 handwritten reported separately)
        ext_all = [c for c in CORPUS_ITEMS if c.get("has_complete_problem")]
        ext_printed_rows, ext_hw_rows = [], []
        for it in ext_all:
            iid = it["image_id"]
            cand_path = ROOT / ".superpowers" / "external_image_cache" / (it.get("filename") or "")
            if not cand_path.exists():
                continue

            def _grade_ext16(st: str, ans: dict[str, Any] | None, _rd: dict[str, Any], _env: dict[str, Any], case_id=iid) -> dict[str, Any]:
                if st != "SERVED":
                    return {"verdict": "NOT_SERVED"}
                return {"verdict": EIFO.grade(case_id, {"answers": ans})}

            row, l_cont = await _eval_single_image(
                cid=iid,
                raw_b=cand_path.read_bytes(),
                filename=cand_path.name,
                gt=it.get("ground_truth_text") or "",
                grade_fn=_grade_ext16,
                partition=it.get("printed_or_handwritten"),
                measure_cold_breakdown=True,
            )
            cont_errors += l_cont
            prior_e = baselines["ext16_prior_rows"].get(iid) or {}
            row["before_baseline"] = {
                "cer": ((prior_e.get("scoring") or {}).get("cer") or {}).get("reconciled_draft"),
                "blocking_uncertain_spans": (prior_e.get("after_reconcile") or {}).get("blocking_uncertain_count"),
                "ocr_decision": "LOCAL_OCR_ACCEPT" if (prior_e.get("after_reconcile") or {}).get("extraction_verified") else "LOCAL_OCR_REVIEW_REQUIRED",
            }
            if it.get("printed_or_handwritten") == "HANDWRITTEN":
                ext_hw_rows.append(row)
            else:
                ext_printed_rows.append(row)

        # 6. Evaluate UNTOUCHED External Image Sets (reported strictly separately)
        new_ext_rows = []
        for it in NEC.NEW_EXTERNAL_ITEMS:
            iid = it["image_id"]
            p = ROOT / ".superpowers" / "external_image_cache" / it["filename"]
            if not p.exists():
                continue

            def _grade_ne(st: str, ans: dict[str, Any] | None, _rd: dict[str, Any], _env: dict[str, Any], case_id=iid) -> dict[str, Any]:
                if st != "SERVED":
                    return {"verdict": "NOT_SERVED"}
                return {"verdict": EIFO.grade(case_id, {"answers": ans})}

            row, l_cont = await _eval_single_image(
                cid=iid,
                raw_b=p.read_bytes(),
                filename=p.name,
                gt=it.get("ground_truth_text") or "",
                grade_fn=_grade_ne,
                partition="untouched_new_external_12",
                measure_cold_breakdown=False,
            )
            cont_errors += l_cont
            new_ext_rows.append(row)

        nic8_manifest = json.loads((RUNS_DIR / "real-image-ocr-vision-comparative-acceptance/new_image_corpus_manifest.json").read_text(encoding="utf-8"))["items"]
        nic8_rows = []
        for it in nic8_manifest:
            cid = it["case_id"]
            p = ROOT / it["cache_path"]
            if not p.exists():
                continue

            def _grade_nic(st: str, ans: dict[str, Any] | None, _rd: dict[str, Any], _env: dict[str, Any]) -> dict[str, Any]:
                return {"verdict": "SERVED_NO_EXPLICIT_NUMERIC_ORACLE" if st == "SERVED" else "NOT_SERVED"}

            row, l_cont = await _eval_single_image(
                cid=cid,
                raw_b=p.read_bytes(),
                filename=p.name,
                gt=it.get("ground_truth_text") or "",
                grade_fn=_grade_nic,
                fact_texts=it.get("critical_fact_texts") or [],
                partition=it.get("partition"),
                measure_cold_breakdown=False,
            )
            cont_errors += l_cont
            nic8_rows.append(row)

        # 7. Deterministic offline Vision-fallback mock + edited confirmation cache/provenance separation
        vis_prep = {
            "status": "ready",
            "source_kind": "image",
            "problem_text": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với (ABCD) và SA = a√3. Tính thể tích khối chóp S.ABCD.",
            "provenance": {"extraction_method": "vlm", "confirmation_contract_version": "ocr-confirmation-provenance/1"},
            "metrics": {"vlm_calls": 1, "processing_ms": 50.0},
        }
        vis_out = AIR.route_image_or_prepare_outcome(vis_prep, allow_live_ai=False)
        vis_env = (vis_out.response or {}).get("envelope") or {}
        vis_cont = _continuity_count(vis_env) if vis_out.status == "SERVED" else 0
        cont_errors += vis_cont
        vision_fallback_mock = {
            "passed": (
                vis_out.status == "SERVED"
                and vis_out.telemetry.chosen_route == "VISION_THEN_LOCAL_DETERMINISTIC"
                and vis_out.telemetry.gemini_typed_fact_calls == 0
                and ((vis_out.response or {}).get("route_d") or {}).get("answers") == {"q1": "a³√3/3"}
                and vis_cont == 0
            ),
            "route": vis_out.telemetry.chosen_route,
            "answers": ((vis_out.response or {}).get("route_d") or {}).get("answers"),
            "live_ai_calls": vis_out.telemetry.gemini_typed_fact_calls,
            "continuity_errors": vis_cont,
        }

        draft_t = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với (ABCD) và SA = a. Tính thể tích khối chóp S.ABCD."
        edit_t = draft_t.replace("SA = a.", "SA = 2a.")
        raw_sha = hashlib.sha256(draft_t.encode("utf-8")).hexdigest()
        prov_edit = build_verified_input_provenance(
            edit_t,
            InputSourceProvenance(origin="local_ocr_auto_verified", raw_ocr_text_sha256=raw_sha, confirmed_span_count=1, selected_candidate_id="region-1~band-2"),
        )
        k_draft = prepare_local_first_hybrid(draft_t, model=resolve_hybrid_gemini_model()).cache_key
        k_edit = prepare_local_first_hybrid(edit_t, model=resolve_hybrid_gemini_model()).cache_key
        provenance_cache_check = {
            "passed": bool(
                prov_edit
                and prov_edit["edited_from_raw_ocr"] is True
                and prov_edit["origin"] == "local_ocr_student_confirmed"
                and prov_edit["counted_as_unmodified_auto_ocr"] is False
                and k_draft != k_edit
            ),
            "distinct_cache_keys": k_draft != k_edit,
            "cache_version": CACHE_VERSION,
            "route_d_cache_policy": ROUTE_D_CACHE_POLICY,
        }

        cache_split_ok = len(LO._RAW_OCR_CACHE) <= LO._RAW_OCR_CACHE_MAX and len(LO._REREAD_CACHE) <= LO._REREAD_CACHE_MAX

        def _ext16_summary(rows_in: list[dict[str, Any]]) -> dict[str, Any]:
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
                "confirmed_served_correct": sum(1 for r in conf_rows if r["confirmation_simulated"].get("grade", {}).get("verdict") == "SERVED_CORRECT"),
                "confirmed_wrong_served": sum(1 for r in conf_rows if r["confirmation_simulated"].get("grade", {}).get("verdict") == "WRONG_SERVED"),
                "selection_bands_tested": sum(len(r["selection_outcomes"]) for r in sel_rows),
                "selection_served_correct": sum(1 for r in sel_rows for s in r["selection_outcomes"] if s.get("oracle_verdict") == "SERVED_CORRECT"),
                "latency_cold_prepare": _stats([r["cold_prepare_ms"] for r in rows_in]),
                "latency_warm_prepare": _stats([r["warm_prepare_ms"] for r in rows_in]),
            }

        def _untouched_summary(rows_in: list[dict[str, Any]]) -> dict[str, Any]:
            cers = [r["cer"] for r in rows_in if r["cer"] is not None]
            cf_rec = sum(r["critical_facts_draft"]["recovered"] for r in rows_in)
            cf_tot = sum(r["critical_facts_draft"]["total"] for r in rows_in)
            auto_rows = [r for r in rows_in if r["auto_route"] is not None]
            conf_rows = [r for r in rows_in if r["confirmation_simulated"] is not None]
            return {
                "count": len(rows_in),
                "ocr_decision_counts": dict(Counter(r["ocr_decision"] for r in rows_in)),
                "cer_median": round(statistics.median(cers), 4) if cers else None,
                "critical_facts_draft": f"{cf_rec}/{cf_tot}" if cf_tot else None,
                "auto_accepts": len(auto_rows),
                "auto_wrong_served": sum(1 for r in auto_rows if r["auto_route"].get("grade", {}).get("verdict") == "WRONG_SERVED"),
                "confirmed_served": sum(1 for r in conf_rows if r["confirmation_simulated"].get("routed_status") == "SERVED"),
                "confirmed_served_correct": sum(1 for r in conf_rows if r["confirmation_simulated"].get("grade", {}).get("verdict") == "SERVED_CORRECT"),
                "confirmed_wrong_served": sum(1 for r in conf_rows if r["confirmation_simulated"].get("grade", {}).get("verdict") == "WRONG_SERVED"),
                "latency_cold_prepare": _stats([r["cold_prepare_ms"] for r in rows_in]),
                "rows": rows_in,
            }

        real27_overall = _summarize_real27(real27_rows)
        real27_by_partition = {
            part: _summarize_real27([r for r in real27_rows if r["partition"] == part])
            for part in ("development", "frozen_external_evaluation", "fresh_external_evaluation")
        }

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
            "false_auto_accepts_negative": false_accepts,
            "adversarial_negative_rows": neg_rows,
            "real27_images": {
                "summary": real27_overall,
                "by_partition": real27_by_partition,
                "before_baseline_meta": baselines["prior_eval_meta"],
                "before_baseline_summary": baselines["real27_summary"],
                "rows": real27_rows,
            },
            "external16_printed_images": {
                "summary": _ext16_summary(ext_printed_rows),
                "before_baseline_summary": baselines["ext15_summary"],
                "rows": ext_printed_rows,
            },
            "external16_handwritten_diagnostic": {
                "note": "Real student handwriting reported separately; never claimed as reliable printed OCR.",
                "summary": _ext16_summary(ext_hw_rows),
                "rows": ext_hw_rows,
            },
            "untouched_external_image_sets": {
                "note": "Held outside REAL27/External16 OCR tuning; reported strictly separately from development subsets.",
                "new_external_12": _untouched_summary(new_ext_rows),
                "new_image_corpus_8": {
                    "development": _untouched_summary([r for r in nic8_rows if r["partition"] == "development"]),
                    "frozen_external_evaluation": _untouched_summary([r for r in nic8_rows if r["partition"] == "frozen_external_evaluation"]),
                },
            },
            "vision_fallback_offline_mock": vision_fallback_mock,
            "confirmation_provenance_and_cache_144": provenance_cache_check,
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


def _build_dataset_provenance() -> dict[str, Any]:
    return {
        "real27_images_and_text": {
            "count": 27,
            "sources": [
                "docs/evaluation/geometry/runs/controlled-vision-real-image-validation/new_in_scope_image_manifest.json (25 anvo25/vmmu MIT images: 6 development + 19 frozen_external_evaluation)",
                "docs/evaluation/geometry/runs/local-semantic-source-gate-reliability/fresh_external_manifest.json (2 anvo25/vmmu MIT images: fresh_external_evaluation)",
            ],
            "ground_truth_status": "GROUND_TRUTH_UNVERIFIED (agent-transcribed from source images + MIT dataset answer keys)",
        },
        "external16_printed_and_handwritten": {
            "count": 16,
            "source": "docs/evaluation/geometry/runs/real-world-printed-handwriting-acquisition/tools/corpus_catalog.py",
            "split": "15 printed (8 hoidap247 LICENSE_UNVERIFIED in gitignored cache + 7 vmmu MIT) + 1 handwritten (hd_a_6043187)",
        },
        "new_external_12": {
            "count": 12,
            "source": "docs/evaluation/geometry/runs/image-first-ocr-verified-geometry/tools/new_external_catalog.py",
            "partition": "untouched_external_image_set (MIT anvo25/vmmu)",
        },
        "new_image_corpus_8": {
            "count": 8,
            "source": "docs/evaluation/geometry/runs/real-image-ocr-vision-comparative-acceptance/new_image_corpus_manifest.json",
            "partition": "2 development + 6 frozen_external_evaluation",
        },
        "sealed_or_locked_corpora_opened": {
            "H-1": 0,
            "W2": 0,
            "W3": 0,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Do not write REAL_WORLD_END_TO_END_EVALUATION.json")
    args = ap.parse_args()

    baselines = _load_baselines()
    surfaces = EUC._check_surfaces()
    rm_eval = EAC._evaluate_reasoning_matrix()
    r1_eval = EAC._evaluate_r1_probe()
    nc_eval, cont_nc = EUC._run_nc_and_negatives()
    a4_eval, cont_a4 = EUC._run_a4_and_depth_bounds()
    dev_eval, cont_dev = EUC._run_exposed_dev_corpora()

    real25 = json.loads((RUNS_DIR / "controlled-vision-real-image-validation/new_in_scope_image_manifest.json").read_text(encoding="utf-8"))["items"]
    real2 = json.loads((RUNS_DIR / "local-semantic-source-gate-reliability/fresh_external_manifest.json").read_text(encoding="utf-8"))["items"]
    real27_forensics = _run_text_forensics(real25 + real2)

    loop = asyncio.new_event_loop()
    try:
        ocr_eval, cont_ocr = loop.run_until_complete(_evaluate_ocr_and_confirmation_async(baselines))
    finally:
        loop.close()

    c_safety = EUC._run_stream_c_safety()
    total_cont_errors = cont_nc + cont_a4 + cont_dev + cont_ocr
    measured_hash, measured_count = FZ.measured_system_hash()
    head_sha = _git_head()
    dirty_product = bool(
        subprocess.check_output(
            ["git", "status", "--porcelain", "--", "backend/app", "frontend/src"],
            cwd=ROOT,
            text=True,
        ).strip()
    )

    report = {
        "schema": "axo-real-world-end-to-end-evaluation/1",
        "run_id": "real-world-geometry-input-verified-simulation",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "measurement_class": "OFFLINE_DEVELOPMENT_AND_EXTERNAL_IMAGE_EVIDENCE",
        "independent_h1_validation": "NOT_MEASURED",
        "independent_generalization": "NOT_MEASURED",
        "real_student_usability": "NOT_MEASURED",
        "physical_low_end": "NOT_MEASURED",
        "live_ai_calls": 0,
        "sealed_h1_rows_opened": 0,
        "locked_w2_w3_rows_read": 0,
        "git_head": head_sha,
        "product_commit": FZ.product_commit(),
        "working_tree_dirty": dirty_product,
        "measured_system": measured_hash,
        "measured_files": measured_count,
        "cache_version": CACHE_VERSION,
        "route_d_cache_policy": ROUTE_D_CACHE_POLICY,
        "semantic_environment_hash": semantic_environment_hash(),
        "runtime_identity": runtime_identity(),
        "locked_surfaces": surfaces,
        "dataset_provenance": _build_dataset_provenance(),
        "ocr_before_after": ocr_eval,
        "understanding_planning_and_verification": {
            "nc_and_autonomous_negatives": nc_eval,
            "a4_plane_constraints_and_depth": a4_eval,
            "reasoning_matrix_72": rm_eval,
            "r1_probe_19": r1_eval,
            "exposed_dev_corpora": dev_eval,
            "real27_text_forensics": real27_forensics,
        },
        "safety_invariants": {
            "total_scene3d_continuity_errors": total_cont_errors,
            **c_safety,
        },
    }

    encoded = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    findings = pub_safety.findings_in(encoded)
    assert not findings, f"Publication safety violation: {findings}"
    assert ("APPROVED_BY" + "_USER") not in encoded.decode("utf-8")

    if not args.dry_run:
        out_path = RUN_DIR / "REAL_WORLD_END_TO_END_EVALUATION.json"
        out_path.write_bytes(encoded)
    sha = hashlib.sha256(encoded).hexdigest()

    r27s = (ocr_eval.get("real27_images") or {}).get("summary") or {}
    e16s = (ocr_eval.get("external16_printed_images") or {}).get("summary") or {}
    summary = {
        "surfaces_ok": surfaces["all_match"],
        "product_commit": report["product_commit"][:12],
        "measured_system": measured_hash[:16],
        "glyph_topo": f"{ocr_eval.get('glyph_topology_passed')}/{ocr_eval.get('glyph_topology_total')}",
        "rendered_pos": f"{ocr_eval.get('rendered_positive_accepted')}/{ocr_eval.get('rendered_positive_total')}",
        "adv_neg_false_accepts": ocr_eval.get("false_auto_accepts_negative"),
        "real27_cer": f"{r27s.get('cer_before_median')} -> {r27s.get('cer_after_median')}",
        "real27_decisions": r27s.get("ocr_decision_counts"),
        "real27_false_auto": r27s.get("false_auto_accepts"),
        "real27_confirmed_served": f"{r27s.get('confirmed_served')}/{r27s.get('confirmed_ready_count')} (wrong={r27s.get('confirmed_wrong_served')})",
        "real27_cold_e2e_p50_p95": (r27s.get("latency_cold_end_to_end") or {}).get("p50"),
        "real27_warm_e2e_p50_p95": (r27s.get("latency_warm_end_to_end") or {}).get("p50"),
        "ext15_cer": f"{e16s.get('cer_before_median')} -> {e16s.get('cer_after_median')}",
        "ext15_selection": f"{e16s.get('selection_served_correct')}/{e16s.get('selection_bands_tested')}",
        "r513_aligned": real27_forensics["r513_source_gate_alignment"]["verified"],
        "real27_text": f"{dev_eval['real27_text']['served']}/{dev_eval['real27_text']['total']} (wrong={dev_eval['real27_text']['wrong_served']})",
        "nc_nl": f"{nc_eval['nc_nl_passed']}/{nc_eval['nc_nl_total']}",
        "continuity_errors": total_cont_errors,
        "mode_a_ok": c_safety["mode_a_trig_no_answer_leak"],
        "json_sha256": sha[:16],
    }
    print(json.dumps(summary, ensure_ascii=False))

    ok = (
        surfaces["all_match"]
        and ocr_eval.get("glyph_topology_passed") == 12
        and ocr_eval.get("rendered_positive_accepted") == 4
        and ocr_eval.get("false_auto_accepts_negative") == 0
        and r27s.get("false_auto_accepts", 0) == 0
        and r27s.get("confirmed_wrong_served", 0) == 0
        and e16s.get("false_auto_accepts", 0) == 0
        and e16s.get("confirmed_wrong_served", 0) == 0
        and ocr_eval.get("vision_fallback_offline_mock", {}).get("passed") is True
        and ocr_eval.get("confirmation_provenance_and_cache_144", {}).get("passed") is True
        and real27_forensics["r513_source_gate_alignment"]["verified"] is True
        and nc_eval["nc_gold_passed"] == 21
        and nc_eval["nc_nl_passed"] == 21
        and nc_eval["autonomous_negatives_false_served"] == 0
        and a4_eval["all_passed"]
        and dev_eval["real27_text"]["wrong_served"] == 0
        and total_cont_errors == 0
        and c_safety["mode_a_trig_no_answer_leak"] is True
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
