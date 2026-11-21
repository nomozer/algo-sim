# -*- coding: utf-8 -*-
"""Đánh giá ảnh thật cho run `image-first-ocr-verified-geometry` (offline, ALLOW_LIVE_AI=0, 0 lời gọi Gemini).

Chạy OCR local THẬT (Tesseract `vie` fast + RapidOCR PP-OCRv6 + đọc lại vùng tranh chấp bằng RapidOCR Latin rec
và Tesseract `eng` một dòng) trên ảnh gốc trong `.superpowers/external_image_cache/` (gitignored), qua đúng mã sản
phẩm (`region_detector` → `local_ocr_route` → `unified_input`), rồi chấm với bản chép tay `ground_truth_text`
(GROUND_TRUTH_UNVERIFIED — do agent chép, chưa có người chấm độc lập) và oracle toán của run trước.

Ba kết quả tách riêng, KHÔNG gộp:
  A. LOCAL_AUTO — ảnh → OCR local đã xác minh → giải (0 AI, 0 sửa).
  B. VISION_ASSISTED — không có bản ghi Vision thật nào cho các ảnh này ⇒ NOT_MEASURED.
  C. USER_CORRECTED_SIMULATED — học sinh MÔ PHỎNG: chỉ sửa đúng các chỗ hệ thống đánh dấu, lấy giá trị đúng từ
     bản chép tay; lỗi KHÔNG được đánh dấu vẫn giữ nguyên (đo rủi ro thật của luồng xác nhận).

Usage:
  python docs/evaluation/geometry/runs/image-first-ocr-verified-geometry/tools/evaluate_image_first_ocr.py \
      [--corpus external16|new_external] [--replay]
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import difflib
import hashlib
import json
import os
import platform
import re
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"
THIS = Path(__file__).resolve().parent
RUN_DIR = THIS.parent
ROOT = RUN_DIR.parents[4]
CACHE = ROOT / ".superpowers" / "external_image_cache"
os.environ.setdefault("LOCAL_OCR_PYTHON", str(ROOT / ".superpowers" / "ocr-venv" / "Scripts" / "python.exe"))
os.environ.setdefault("LOCAL_OCR_TESSDATA", str(ROOT / ".superpowers" / "tessdata_fast"))
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
sys.path.insert(0, str(ROOT / "docs/evaluation/geometry/runs/real-world-printed-handwriting-acquisition/tools"))
sys.path.insert(0, str(THIS))

import freeze_evaluation_candidate as F  # noqa: E402
from corpus_catalog import CORPUS_ITEMS  # noqa: E402

from app.ai.adaptive_input_router import (  # noqa: E402
    extract_structured_math_tokens,
    reconcile_dual_ocr_texts,
    route_text_input,
)
from app.ai.local_geometry_parser import clear_local_geometry_parser_cache  # noqa: E402
from app.ingestion import local_ocr_route as LR  # noqa: E402
from app.ingestion.image import normalize_image  # noqa: E402
from app.ingestion.ocr_reconcile import norm_math, reconcile_local_ocr  # noqa: E402
from app.ingestion.region_detector import detect_problem_regions  # noqa: E402
from app.ingestion.unified_input import prepare_unified_input  # noqa: E402
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity  # noqa: E402

RUN_ID = "image-first-ocr-verified-geometry"

# Oracle toán: run `formal-correctness-real-world-acceptance` (ORACLE, có lời giải tay) + bổ sung câu b của ext01
# do run này tự dẫn (độc lập với AlgoSim): SA = a√3, G = (2a/3, a/3, a√3/3), (SBD): x/a + y/a + z/(a√3) = 1
# ⇒ d = (a/3)/√(7/3) = a√21/21.
ORACLE: dict[str, dict[str, Any]] = {
    "ext_prt_01_hd_q_5259753": {"answers": {"q1": "a³√3/3", "q2": "a√21/21"}, "provenance": "formal-run ORACLE (q1) + run hand derivation (q2)"},
    "ext_prt_02_hd_q_7922924": {"answers": None, "expected": "REFUSE_MISSING_DIMENSION_OR_HEIGHT_INVARIANT", "served_ok": {"q1": "6"}},
    "ext_prt_03_hd_q_7907931#1": {"answers": {"q1": "a√2/2"}},
    "ext_prt_03_hd_q_7907931#2": {"answers": {"q1": "a³/4"}},
    "ext_prt_04_hd_q_8436784": {"answers": {"q1": "1/2"}},
    "ext_prt_05_hd_q_7451806": {"answers": {"q1": "6/5"}},
    "ext_prt_06_hd_q_1084979": {"answers": {"q1": "a³√15/4", "q2": "a√15/5"}},
    "ext_prt_07_hd_q_7958052": {"answers": {"q1": "4,7"}},
    "ext_prt_08_hd_q_7509702": {"answers": None, "expected": "OUT_OF_SCOPE_VECTOR_MULTI_PROBLEM"},
    "ext_prt_09_vmmu_page_r4": {"answers": {"q1": "2"}},
    "ext_prt_10_vmmu_page_r7": {"answers": None, "expected": "OUT_OF_SCOPE_CURVED"},
    "ext_prt_11_vmmu_page_r10": {"answers": {"q1": "30°"}},
    "ext_prt_12_vmmu_page_r11": {"answers": {"q1": "2√3"}},
    "ext_prt_13_vmmu_page_r25": {"answers": None, "expected": "OUT_OF_SCOPE_CURVED"},
    "ext_prt_14_vmmu_page_r26": {"answers": None, "expected": "OUT_OF_SCOPE_CURVED"},
    "ext_prt_15_vmmu_page_r28": {"answers": None, "expected": "DIAGRAM_ONLY_FACTS"},
    "ext_hw_b1_01_hd_a_6043187": {"answers": {"q1": "a³√3"}},
    "new_ext_01_vmmu_full_r313": {"answers": {"q1": "2a√57/19"}, "provenance": "VMMU key A + hand derivation d(A,(SBC))=2a√57/19"},
    "new_ext_02_vmmu_full_r351": {"answers": {"q1": "60°"}, "provenance": "VMMU key B + hand derivation equilateral △A'BD ⇒ 60°"},
    "new_ext_03_vmmu_full_r387": {"answers": {"q1": "a√21/14"}, "provenance": "VMMU key D + hand derivation d(M,(A'BC))=a√21/14"},
    "new_ext_04_vmmu_full_r403": {"answers": {"q1": "60°"}, "provenance": "VMMU key D + hand derivation MN∥SB, CD∥AB, △SAB đều ⇒ 60°"},
    "new_ext_05_vmmu_full_r411": {"answers": {"q1": "45°"}, "provenance": "VMMU key B + hand derivation AB=a√2=SA ⇒ ∠(SB,(ABC))=45°"},
    "new_ext_06_vmmu_full_r395": {"answers": None, "expected": "OUT_OF_SCOPE_CURVED", "provenance": "VMMU key A (cylinder)"},
    "new_ext_07_vmmu_full_r412": {"answers": None, "expected": "OUT_OF_SCOPE_CURVED", "provenance": "VMMU key A (cylinder+sphere+cone)"},
    "new_ext_08_vmmu_full_r424": {"answers": None, "expected": "OUT_OF_SCOPE_CURVED", "provenance": "VMMU key B (cylinder)"},
    "new_ext_09_vmmu_ocr_r18": {"answers": None, "expected": "OUT_OF_SCOPE_PLANAR_MENSURATION", "provenance": "VMMU key B"},
    "new_ext_10_vmmu_ocr_r21": {"answers": None, "expected": "OUT_OF_SCOPE_PLANAR_OPTIMIZATION", "provenance": "VMMU key C"},
    "new_ext_11_vmmu_ocr_r31": {"answers": None, "expected": "OUT_OF_SCOPE_PLANAR_OPTIMIZATION", "provenance": "VMMU key C"},
    "new_ext_12_vmmu_ocr_r3": {"answers": None, "expected": "OUT_OF_SCOPE_CALCULUS", "provenance": "VMMU key D"},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _env() -> dict[str, Any]:
    return {
        "os": platform.platform(),
        "python": platform.python_version(),
        "cpu_logical_cores": os.cpu_count(),
        "allow_live_ai": 0,
        "live_gemini_calls": 0,
        "local_ocr_python": "ocr-venv (rapidocr 3.10.0, onnxruntime 1.31.1, tesserocr 2.12.0 / tesseract 5.5.3)",
        "tessdata": "tessdata_fast vie + eng",
        "benchmark_tier": "HOST_BENCHMARK_OFFLINE",
    }


def header(schema: str, **kw: Any) -> dict[str, Any]:
    tree, n = F.measured_system_hash()
    return {
        "schema": schema,
        "run_id": RUN_ID,
        "generated_at_utc": _now(),
        "head_commit": F._git("rev-parse", "HEAD"),
        "product_commit": F.product_commit(),
        "working_tree_dirty": bool(F._git("status", "--porcelain", "--", "backend/app", "frontend/src")),
        "measured_system_tree_hash": tree,
        "measured_system_file_count": n,
        "test_environment": _env(),
        "model_versions": {
            "local_ocr_route": LR.LOCAL_OCR_ROUTE_VERSION,
            "reconcile": "layout-aware-ocr-reconcile/1",
            "readers": ["tesseract-vie (tessdata_fast)", "rapidocr PP-OCRv6 det/rec small", "rapidocr latin PP-OCRv5 rec mobile (re-read)", "tesseract-eng single-line ×3 (re-read)"],
            "vision": "NOT_CALLED (ALLOW_LIVE_AI=0)",
        },
        **kw,
    }


def write(name: str, obj: dict[str, Any]) -> str:
    p = RUN_DIR / name
    data = json.dumps(obj, ensure_ascii=False, indent=1) + "\n"
    p.write_text(data, encoding="utf-8")
    return _sha(data.encode("utf-8"))


# ── chấm OCR ─────────────────────────────────────────────────────────────────────────────────────────────────────

def _cer(hyp: str, ref: str) -> float:
    h, r = re.sub(r"\s+", " ", hyp).strip(), re.sub(r"\s+", " ", ref).strip()
    if not r:
        return 0.0
    # Levenshtein
    prev = list(range(len(r) + 1))
    for i, ch in enumerate(h, 1):
        cur = [i]
        for j, cr in enumerate(r, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ch != cr)))
        prev = cur
    return round(prev[-1] / len(r), 4)


def _wer(hyp: str, ref: str) -> float:
    h, r = hyp.split(), ref.split()
    if not r:
        return 0.0
    prev = list(range(len(r) + 1))
    for i, w in enumerate(h, 1):
        cur = [i]
        for j, wr in enumerate(r, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (w != wr)))
        prev = cur
    return round(prev[-1] / len(r), 4)


_MATH_TOK = re.compile(r"[A-Z][A-Z0-9'′]*(?:\.[A-Z0-9'′]+)?|\([A-Z0-9'′]+\)|\d+(?:[.,]\d+)?°?|[a-z]?√\d+|[⊥∥]|[a-z]√\d+")


def _math_tokens(text: str) -> list[str]:
    t = text.replace("′", "'")
    return [norm_math(m.group(0)) for m in _MATH_TOK.finditer(t)]


def _prf(hyp: list[str], ref: list[str]) -> dict[str, Any]:
    from collections import Counter

    ch, cr = Counter(hyp), Counter(ref)
    tp = sum((ch & cr).values())
    return {
        "tp": tp,
        "hyp": sum(ch.values()),
        "ref": sum(cr.values()),
        "precision": round(tp / max(1, sum(ch.values())), 4),
        "recall": round(tp / max(1, sum(cr.values())), 4),
    }


def _category_recall(hyp: str, ref: str) -> dict[str, Any]:
    def cats(s: str) -> dict[str, list[str]]:
        s = s.replace("′", "'")
        return {
            "prime_labels": re.findall(r"[A-Z]'+", s),
            "radicals": re.findall(r"√\d+", s),
            "fractions": re.findall(r"[0-9a-zA-Z√π]+/[0-9a-zA-Z]+", s),
            "angle_degrees": re.findall(r"\d+°", s),
            "point_labels": re.findall(r"(?<![A-Za-z])[A-Z](?![a-z])", s),
            "relation_symbols": re.findall(r"[⊥∥]", s),
            "vietnamese_diacritic_words": [w for w in re.findall(r"[^\W\d_]+", s.lower()) if re.search(r"[à-ỹđ]", w)],
        }

    ch, cr = cats(hyp), cats(ref)
    return {k: _prf(ch[k], cr[k]) for k in cr}


def _engine_text(raw: dict[str, Any], name: str) -> str:
    e = (raw.get("engines") or {}).get(name) or {}
    return "\n".join(ln.get("text", "") for ln in e.get("lines") or [])


# ── mô phỏng học sinh sửa đúng các chỗ được đánh dấu ─────────────────────────────────────────────────────────────

def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("′", "'")).strip()


def simulate_student(problem_text: str, tokens: list[dict[str, Any]], gt_text: str) -> dict[str, Any]:
    """Thay mỗi khoảng được đánh dấu bằng đoạn tương ứng của bản chép tay (căn chỉnh difflib ký tự)."""
    src = problem_text
    ref = gt_text
    sm = difflib.SequenceMatcher(None, src, ref, autojunk=False)
    blocks = sm.get_opcodes()

    def map_pos(p: int) -> int:
        for tag, i1, i2, j1, j2 in blocks:
            if i1 <= p < i2 or (p == i2 and tag != "equal" and i2 == len(src)):
                if tag == "equal":
                    return j1 + (p - i1)
                return j1 if p == i1 else j2
        return len(ref)

    edits, confirms, actions = [], 0, 0
    spans = sorted([t for t in tokens if (t.get("span_start") or -1) >= 0], key=lambda t: -t["span_start"])
    out = src
    for t in spans:
        s, e = t["span_start"], t["span_end"]
        rs, re_ = map_pos(s), map_pos(e)
        truth = ref[rs:re_].strip()
        cur = src[s:e]
        actions += 1
        if _norm_ws(truth) == _norm_ws(cur):
            confirms += 1
            continue
        if not truth:
            out = (out[:s].rstrip(" ") + (" " if out[:s] and out[e:] else "") + out[e:].lstrip(" ")).strip()
        else:
            out = out[:s] + truth + out[e:]
        edits.append({"span_id": t.get("span_id"), "from": cur, "to": truth, "chosen_from_alternatives": truth in (t.get("alternatives") or [])})
    diag_items = [t for t in tokens if t.get("kind") == "diagram"]
    actions += len(diag_items)
    return {"text": out, "edits": edits, "confirms": confirms, "diagram_confirms": len(diag_items), "actions": actions,
            "chars_typed": sum(len(e["to"]) for e in edits if not e["chosen_from_alternatives"])}


def solve(text: str) -> dict[str, Any]:
    clear_local_geometry_parser_cache()
    t0 = time.perf_counter()
    out = route_text_input(text, allow_live_ai=False, input_kind="image")
    ms = round((time.perf_counter() - t0) * 1000.0, 2)
    resp = out.response or {}
    env = resp.get("envelope") or {}
    rd = resp.get("route_d") or {}
    scene = env.get("scene3d")
    cont = validate_construction_continuity(scene) if scene else None
    return {
        "status": out.status,
        "route": out.telemetry.chosen_route,
        "local_parse_status": out.telemetry.local_parse_status,
        "answers": rd.get("answers") or None,
        "reason_code": env.get("reason_code") or (out.receipt or {}).get("code"),
        "scene3d_objects": len((scene or {}).get("objects") or []) if scene else 0,
        "scene3d_continuity_violations": len(cont) if cont is not None else None,
        "solve_ms": ms,
    }


def grade(case_key: str, res: dict[str, Any]) -> str:
    o = ORACLE.get(case_key) or ORACLE.get(case_key.split("#")[0]) or {}
    exp = o.get("answers")
    got = res.get("answers")
    if got:
        if exp is None:
            if o.get("served_ok") and got == o["served_ok"]:
                return "SERVED_CORRECT"
            return "WRONG_SERVED_OR_UNGRADED"
        if all(got.get(k) == v for k, v in exp.items()) and len(got) >= len(exp):
            return "SERVED_CORRECT"
        if all(got.get(k) == v for k, v in exp.items()):
            return "SERVED_CORRECT"
        return "WRONG_SERVED"
    return "REFUSED_OR_NOT_SERVED"


# ── vòng chính ───────────────────────────────────────────────────────────────────────────────────────────────────

def corpus_items(name: str) -> list[dict[str, Any]]:
    if name == "external16":
        return [it for it in CORPUS_ITEMS if it.get("has_complete_problem")]
    from new_external_catalog import NEW_EXTERNAL_ITEMS  # noqa: WPS433

    return list(NEW_EXTERNAL_ITEMS)


def evaluate_image(it: dict[str, Any], raw_store: dict[str, Any], replay: bool) -> dict[str, Any]:
    path = CACHE / it["filename"]
    data = path.read_bytes()
    rec_case: dict[str, Any] = {
        "image_id": it["image_id"],
        "filename": it["filename"],
        "source_url": it.get("source_url"),
        "original_image_url": it.get("original_image_url"),
        "license_status": it.get("license_status"),
        "sha256_original": _sha(data),
        "sha256_catalog": it.get("original_file_sha256"),
        "printed_or_handwritten": it.get("printed_or_handwritten"),
        "has_geometry_diagram_catalog": it.get("has_geometry_diagram"),
        "diagram_embedded_facts_catalog": it.get("diagram_embedded_facts"),
        "ground_truth_status": it.get("ground_truth_verification_status", "GROUND_TRUTH_UNVERIFIED"),
        "data_partition": it.get("data_partition"),
    }
    t0 = time.perf_counter()
    norm = normalize_image(data)
    t_dec = time.perf_counter()
    rr = detect_problem_regions(norm)
    t_reg = time.perf_counter()
    rec_case["image_resolution"] = [norm.width, norm.height]
    rec_case["region_detection"] = {
        "selected_bbox_original": [rr.selected_bbox.x0, rr.selected_bbox.y0, rr.selected_bbox.x1, rr.selected_bbox.y1],
        "used_crop": rr.used_crop,
        "prepared_size": [rr.prepared_image.width, rr.prepared_image.height],
        "figure_bboxes_prepared": [list(b) for b in rr.prepared_figure_bboxes()],
        "has_associated_figure": rr.has_associated_figure,
        "ambiguous_multi_problem": rr.ambiguous_multi_problem,
        "candidate_regions": len(rr.candidates),
        "desk_trimmed": rr.desk_trimmed,
        "deskew_applied": rr.deskew_applied,
    }
    if it["image_id"] in raw_store and (raw_store[it["image_id"]].get("raw") or {}).get("ok"):
        from app.ingestion import local_ocr as LO

        cfg = LO.local_ocr_config() or {}
        if cfg.get("available"):
            saved_raw = raw_store[it["image_id"]]["raw"]
            LO._CACHE[f"{_sha(rr.prepared_image.data)}:tesseract,rapidocr:{cfg['tessdata']}"] = saved_raw
            if rr.prepared_image.data == rr.full_image.data:
                LO._CACHE[f"{_sha(rr.full_image.data)}:tesseract,rapidocr:{cfg['tessdata']}"] = saved_raw
            saved_rereads = raw_store[it["image_id"]].get("rereads") or {}
            if saved_rereads:
                from app.ingestion.ocr_reconcile import reconcile_local_ocr as _rec0

                disp0 = _rec0(saved_raw, figure_bboxes=rr.prepared_figure_bboxes(), min_agreeing_families=LR.MIN_AGREEING_FAMILIES)["disputed_math_slots"]
                boxes0 = [d["bbox"] for d in disp0]
                if boxes0 and all(json.dumps(b) in saved_rereads for b in boxes0):
                    LO._CACHE[f"reread:{_sha(rr.prepared_image.data)}:{json.dumps(boxes0)}:{cfg['tessdata']}"] = {
                        "ok": True,
                        "readings": [saved_rereads[json.dumps(b)] for b in boxes0],
                        "worker_ms": 0.0,
                        "total_ms": 0.0,
                        "cached": True,
                    }
    if replay and it["image_id"] in raw_store:
        loc_raw = raw_store[it["image_id"]]["raw"]
        adj = raw_store[it["image_id"]].get("rereads") or {}
        from app.ingestion.ocr_reconcile import reconcile_with_adjudication

        def rr_fn(boxes):
            return {"ok": True, "readings": [adj.get(json.dumps(b), {}) for b in boxes]}

        loc = reconcile_with_adjudication(loc_raw, rr_fn, figure_bboxes=rr.prepared_figure_bboxes(), min_agreeing_families=LR.MIN_AGREEING_FAMILIES)
        loc.update(ok=True, solve_text=LR._reflow(loc["draft_text"]), raw_ocr=loc_raw, timing={"replay": True})
    else:
        loc = LR.run_local_ocr_route(rr.prepared_image.data, rr.prepared_figure_bboxes())
    t_ocr = time.perf_counter()
    raw = loc.get("raw_ocr") or {}
    # Lưu bản ghi thô (văn bản OCR + hộp bao; không có byte ảnh) để tái lập không cần engine.
    from app.ingestion.local_ocr import reread_local_ocr_regions

    rereads = {}
    if not replay:
        disputes = reconcile_local_ocr(raw, figure_bboxes=rr.prepared_figure_bboxes(), min_agreeing_families=LR.MIN_AGREEING_FAMILIES)["disputed_math_slots"]
        boxes = [d["bbox"] for d in disputes]
        rd = reread_local_ocr_regions(rr.prepared_image.data, boxes) if boxes else {"readings": []}
        rereads = {json.dumps(b): r for b, r in zip(boxes, rd.get("readings") or [])}
        raw_store[it["image_id"]] = {"raw": raw, "rereads": rereads}
    gt = it.get("ground_truth_text") or ""
    tess_txt, rapid_txt = _engine_text(raw, "tesseract"), _engine_text(raw, "rapidocr")
    draft = loc.get("solve_text") or ""

    # Trước: cổng cũ (reconcile_dual_ocr_texts → verify_ocr_input_fidelity) trên cùng OCR thô.
    old = reconcile_dual_ocr_texts(tess_txt, rapid_txt, has_diagram=bool(rr.has_associated_figure),
                                   is_handwritten=it.get("printed_or_handwritten") == "HANDWRITTEN")
    old_report = old.get("fidelity_report") or {}
    rec_case["ocr"] = {
        "engines": {
            name: {
                "engine_version": e.get("engine_version"),
                "model": e.get("model"),
                "ms": e.get("ms"),
                "error": e.get("error"),
                "preprocess": e.get("preprocess"),
                "lines": [{"text": ln.get("text"), "bbox": ln.get("bbox"), "raw_confidence": ln.get("conf"), "words": len(ln.get("words") or [])} for ln in e.get("lines") or []],
            }
            for name, e in (raw.get("engines") or {}).items()
        },
        "confidence_note": "raw engine confidence, NOT calibrated probability (OCR_CONFIDENCE_UNCALIBRATED)",
    }
    rec_case["before_gate"] = {
        "gate": "reconcile_dual_ocr_texts + verify_ocr_input_fidelity (adaptive-input-router/1, unchanged)",
        "accepted": bool(old.get("reconciled")),
        "reason_code": old.get("reason_code"),
        "failed_checks": old_report.get("failed_checks"),
    }
    blocking_unc = [s for s in loc.get("uncertain_spans") or [] if s.get("blocking")]
    rec_case["after_reconcile"] = {
        "draft_text": draft,
        "extraction_verified": bool(loc.get("extraction_verified")),
        "blocking_reasons": loc.get("blocking_reasons"),
        "uncertain_spans": [{k: s.get(k) for k in ("span_id", "text", "kind", "reason", "alternatives", "readings", "bbox", "blocking")} for s in loc.get("uncertain_spans") or []],
        "blocking_uncertain_count": len(blocking_unc),
        "layout_flags": loc.get("layout_flags"),
        "diagram": loc.get("diagram"),
        "adjudication": loc.get("adjudication"),
        "low_quality": loc.get("low_quality"),
        "timing": loc.get("timing"),
    }
    # Chấm OCR theo bản chép tay.
    vmath = [s for s in loc.get("spans") or [] if s.get("status") == "verified" and s.get("kind") == "math"]
    gt_tokens = set(_math_tokens(gt))
    gt_norm = norm_math(gt)
    wrong_verified = [
        s["text"]
        for s in vmath
        if norm_math(s["text"]).strip(".,:;)") not in gt_norm
        and norm_math(s["text"]) not in gt_tokens
        and not any(norm_math(s["text"]) in t or t in norm_math(s["text"]) for t in gt_tokens if len(t) > 1)
    ]
    rec_case["scoring"] = {
        "cer": {"tesseract": _cer(tess_txt, gt), "rapidocr": _cer(rapid_txt, gt), "reconciled_draft": _cer(draft, gt)},
        "wer": {"tesseract": _wer(tess_txt, gt), "rapidocr": _wer(rapid_txt, gt), "reconciled_draft": _wer(draft, gt)},
        "math_tokens": {"tesseract": _prf(_math_tokens(tess_txt), _math_tokens(gt)), "rapidocr": _prf(_math_tokens(rapid_txt), _math_tokens(gt)),
                        "reconciled_draft": _prf(_math_tokens(draft), _math_tokens(gt))},
        "categories_reconciled": _category_recall(draft, gt),
        "categories_tesseract": _category_recall(tess_txt, gt),
        "categories_rapidocr": _category_recall(rapid_txt, gt),
        "verified_math_span_count": len(vmath),
        "verified_math_spans_not_in_ground_truth": wrong_verified,
        "exact_statement_match": _norm_ws(draft) == _norm_ws(gt),
    }
    # Kết quả học sinh thấy (đi đúng tuyến sản phẩm).
    t_p0 = time.perf_counter()
    out = asyncio.run(prepare_unified_input(content=base64.b64encode(data).decode(), declared_mime=None, filename=it["filename"])).to_dict()
    t_p1 = time.perf_counter()
    rec_case["user_facing"] = {
        "status": out["status"],
        "reason_code": out["reason_code"],
        "learner_message": out["learner_message"],
        "input_route": out["provenance"].get("input_route"),
        "vlm_calls": out["metrics"].get("vlm_calls"),
        "review_items": len(out["uncertain_tokens"]),
        "candidates": len(out["candidates"]),
        "prepare_ms": round((t_p1 - t_p0) * 1000.0, 2),
    }
    rec_case["timing_ms"] = {
        "decode": round((t_dec - t0) * 1000.0, 2),
        "region_detection": round((t_reg - t_dec) * 1000.0, 2),
        "local_ocr_route": round((t_ocr - t_reg) * 1000.0, 2),
    }
    # A / C
    outcomes = []
    problem_variants: list[tuple[str, dict[str, Any], str]] = []
    if out["status"] == "needs_selection":
        for c in out["candidates"]:
            out2 = asyncio.run(prepare_unified_input(content=base64.b64encode(data).decode(), declared_mime=None, filename=it["filename"], selected_candidate_id=c["candidate_id"])).to_dict()
            problem_variants.append((c["candidate_id"], out2, c.get("label", "")))
    else:
        problem_variants.append(("single", out, ""))
    gt_parts = it.get("verbatim_problem_texts") or [gt]
    for idx, (cid, o, _lab) in enumerate(problem_variants):
        key = it["image_id"] + (f"#{idx + 1}" if len(problem_variants) > 1 else "")
        entry: dict[str, Any] = {"case_key": key, "selection": cid, "prepare_status": o["status"], "input_route": o["provenance"].get("input_route")}
        gt_text = gt_parts[idx] if len(problem_variants) > 1 and idx < len(gt_parts) else gt
        if o["status"] == "ready":
            r = solve(o["problem_text"])
            entry["local_auto"] = {**r, "grade": grade(key, r), "corrections": 0, "ai_calls": 0}
        elif o["status"] == "needs_confirmation":
            sim = simulate_student(o["problem_text"], o["uncertain_tokens"], gt_text)
            r = solve(sim["text"])
            entry["user_corrected_simulated"] = {**r, "grade": grade(key, r), "edits": sim["edits"], "confirms": sim["confirms"],
                                                 "diagram_confirms": sim["diagram_confirms"], "actions": sim["actions"],
                                                 "chars_typed": sim["chars_typed"], "full_retype_chars": len(gt_text),
                                                 "final_text": sim["text"]}
        else:
            entry["not_solved_reason"] = o["reason_code"]
        outcomes.append(entry)
    rec_case["outcomes"] = outcomes
    return rec_case


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="external16", choices=["external16", "new_external"])
    ap.add_argument("--replay", action="store_true")
    a = ap.parse_args()
    raw_path = RUN_DIR / ("local_ocr_raw_outputs.json" if a.corpus == "external16" else "new_external_local_ocr_raw_outputs.json")
    raw_store = json.loads(raw_path.read_text(encoding="utf-8")).get("items", {}) if raw_path.exists() else {}
    cases = []
    for it in corpus_items(a.corpus):
        print("…", it["image_id"], flush=True)
        cases.append(evaluate_image(it, raw_store, a.replay))
    if not a.replay:
        raw_path.write_text(json.dumps({"schema": "local-ocr-raw-store/1", "note": "OCR text + boxes only; no image bytes",
                                        "generated_at_utc": _now(), "items": raw_store}, ensure_ascii=False) + "\n", encoding="utf-8")
    out = RUN_DIR / ("_eval_core_external16.json" if a.corpus == "external16" else "_eval_core_new_external.json")
    out.write_text(json.dumps({"generated_at_utc": _now(), "corpus": a.corpus, "replay": a.replay, "cases": cases}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
