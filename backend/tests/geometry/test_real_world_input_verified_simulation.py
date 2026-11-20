# -*- coding: utf-8 -*-
"""Focused test suite for `real-world-geometry-input-verified-simulation` (`CACHE_VERSION = 144`).

Covers:
1. OCR reconciliation hardening (`layout-aware-ocr-reconcile/3`):
   - Option-band detection requires explicit option punctuation (`A.`, `B)`, etc.) so horizontal diagram labels do not trigger false choice bands.
   - Multi-word Vietnamese prose inside figure bboxes stays in problem text, and choice options are never leaked into `diagram_tokens`.
   - `=` glyph topology (`has_equals_bars`) and uppercase serif homoglyph parity (`4->A, 8->B`) verify clean math tokens without relaxing `S,ABCD`, `600°`, `a2`, `4BC = 30°`, or `(tham khảo hình vẽ)` guards.
2. Worker edge-bleed upper-prime protection & per-box reread deduplication (`local_ocr_worker.py`, `local_ocr.py`).
3. Multi-problem band switching (`~band-1` vs `~band-2`), confirmation provenance (`verified-input-provenance/1`),
   edited-text auto-downgrade (`counted_as_unmodified_auto_ocr=False`), distinct `/api/analyze` cache keys, and `143:route-d` -> `144:route-d` invalidation.
4. Deterministic offline Vision fallback replay -> Local Parser -> Autonomous Planner -> Verified `Scene3D`.
5. Source Gate `_cac_moc_cau` missing-period Capitalized question boundary (`vmmu_r513` -> `MISSING_DIMENSION` + `determinacy_audit`),
   while preserving conditional clauses (`Nếu ...`) and `S-1` tone-typo refusal (`hình chop`).
"""
from __future__ import annotations

import asyncio
import hashlib
import json

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app import main as M
from app.ai import adaptive_input_router as AIR
from app.ai.hybrid_offline import prepare_local_first_hybrid, resolve_hybrid_gemini_model
from app.ingestion import local_ocr as LO
from app.ingestion import local_ocr_worker as LW
from app.ingestion import ocr_reconcile as OR
from app.persistence.db import SessionLocal, SimulationCache, init_db
from app.simulation.geometry_functions import registry
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity


def _line(words: list[str], y: int, *, x0: int = 10, h: int = 28, cw: int = 14, conf: float = 95.0, gaps=None):
    out, x = [], x0
    for i, w in enumerate(words):
        wid = max(cw, cw * len(w))
        out.append({"text": w, "conf": conf, "bbox": [x, y, x + wid, y + h]})
        x += wid + (gaps[i] if gaps else cw)
    return {"text": " ".join(words), "conf": conf, "bbox": [x0, y, x - cw, y + h], "words": out}


def _raw(rapid_lines, tess_lines, w: int = 1200, h: int = 600):
    return {
        "width": w,
        "height": h,
        "engines": {
            "rapidocr": {"engine_version": "rapidocr test", "lines": rapid_lines},
            "tesseract": {"engine_version": "tesseract test", "lines": tess_lines},
        },
    }


def test_figure_prose_choice_separation_and_diagram_label_safety():
    # Horizontal diagram labels ('D','A','C','B') MUST NOT start choice bands when they lack punctuation.
    r_lines = [
        _line(["Cho", "hình", "hộp", "chữ", "nhật", "ABCD.A'B'C'D'", "có", "AB", "=", "2."], 20),
        _line(["D"], 80, x0=520),
        _line(["A"], 82, x0=620),
        _line(["C"], 84, x0=700),
        _line(["B"], 83, x0=780),
        # Question prose accidentally overlapping the bottom of figure bbox must NOT be eaten into diagram_tokens!
        _line(["Tính", "khoảng", "cách", "từ", "A", "đến", "(SBC)."], 260, x0=40),
        # MC option row overlapping figure bbox must NOT leak numeric measurements into diagram_tokens.
        _line(["A.", "2√5."], 340, x0=40),
        _line(["B.", "√5."], 340, x0=540),
    ]
    t_lines = [
        _line(["Cho", "hình", "hộp", "chữ", "nhật", "ABCD.A'B'C'D'", "có", "AB", "=", "2."], 20),
        _line(["Tính", "khoảng", "cách", "từ", "A", "đến", "(SBC)."], 260, x0=40),
        _line(["A.", "2√5."], 340, x0=40),
        _line(["B.", "√5."], 340, x0=540),
    ]
    figs = [(480, 60, 860, 380)]
    rec = OR.reconcile_local_ocr(_raw(r_lines, t_lines), figure_bboxes=figs, min_agreeing_families=2)
    diag_texts = [t["text"] for t in rec["diagram"]["tokens"]]
    assert "D" in diag_texts and "A" in diag_texts
    assert not any("2√5" in t or "√5" in t or "Tính" in t for t in diag_texts)
    assert "Tính khoảng cách từ A đến (SBC)." in rec["draft_text"]
    assert rec["diagram"]["classification"] == "DIAGRAM_LABELS_ONLY_CONSISTENT"


def test_equals_topology_upper_homoglyph_and_negative_safety_guards():
    # 1. Clean '=' verified via has_equals_bars + horizontal dash Tesseract reading; '-' rejected.
    r_eq = [_line(["Cho", "cạnh", "SA", "=", "a."], 10)]
    t_eq = [_line(["Cho", "cạnh", "SA", "—", "a."], 10)]
    adj_eq = {"L1:S4": {"rapidocr_latin_rec": "="}}
    meta_eq = {"L1:S4": {"glyph_topology": {"blurry": False, "has_equals_bars": True}}}
    rec_eq = OR.reconcile_local_ocr(_raw(r_eq, t_eq), adjudications=adj_eq, adjudication_meta=meta_eq, min_agreeing_families=2)
    assert rec_eq["ocr_decision"] == "LOCAL_OCR_ACCEPT", rec_eq["uncertain_spans"]

    # Negative: has_equals_bars=False (e.g., minus '-') must stay REVIEW_REQUIRED.
    meta_minus = {"L1:S4": {"glyph_topology": {"blurry": False, "has_equals_bars": False}}}
    rec_minus = OR.reconcile_local_ocr(_raw(r_eq, t_eq), adjudications=adj_eq, adjudication_meta=meta_minus, min_agreeing_families=2)
    assert rec_minus["ocr_decision"] == "LOCAL_OCR_REVIEW_REQUIRED"

    # 2. Uppercase homoglyph parity ('4BC' / '48' with identical primes/dots) allowed ONLY when both Paddle agree and non-blurry.
    r_hom = [_line(["Cho", "hình", "lăng", "trụ", "ABC.A'B'C'"], 10)]
    t_hom = [_line(["Cho", "hình", "lăng", "trụ", "4BC.4'B'C'"], 10)]
    adj_hom = {"L1:S5": {"rapidocr_latin_rec": "ABC.A'B'C'"}}
    meta_hom = {"L1:S5": {"glyph_topology": {"blurry": False}}}
    rec_hom = OR.reconcile_local_ocr(_raw(r_hom, t_hom), adjudications=adj_hom, adjudication_meta=meta_hom, min_agreeing_families=2)
    assert rec_hom["ocr_decision"] == "LOCAL_OCR_ACCEPT", rec_hom["uncertain_spans"]

    # Negative: prime mismatch ('ABC.ABC' vs '4BC.4\'B\'C\'') must stay blocked!
    r_drop = [_line(["Cho", "hình", "lăng", "trụ", "ABC.ABC"], 10)]
    rec_drop = OR.reconcile_local_ocr(
        _raw(r_drop, t_hom),
        adjudications={"L1:S5": {"rapidocr_latin_rec": "ABC.ABC"}},
        adjudication_meta=meta_hom,
        min_agreeing_families=2,
    )
    assert rec_drop["ocr_decision"] == "LOCAL_OCR_REVIEW_REQUIRED"

    # 3. Angle-hat misread '4BC = 30°' and '(4BC)' and 'S,ABCD' and '600°'/'600º' MUST ALL remain blocked!
    for bad_line in (
        ["góc", "4BC", "=", "30°."],
        ["mặt", "phẳng", "(4BC)."],
        ["Cho", "chóp", "S,ABCD."],
        ["góc", "bằng", "600°."],
        ["góc", "bằng", "600º."],
    ):
        raw_bad = _raw([_line(bad_line, 10)], [_line(bad_line, 10)])
        rec_bad = OR.reconcile_local_ocr(raw_bad, min_agreeing_families=2)
        assert rec_bad["ocr_decision"] == "LOCAL_OCR_REVIEW_REQUIRED", f"False accept on {bad_line}"

    # 4. Crop-reread overvote guard: reread engines sharing a cropped artifact MUST NOT auto-verify over primary rapidocr.
    r_ov = [_line(["đáy", "ABCD", "là"], 10)]
    t_ov = [_line(["đáy", "4BCD", "là"], 10)]
    adj_ov = {"L1:S2": {"rapidocr_latin_rec": "ABCE", "tesseract_eng_line": "ABCE"}}
    rec_ov = OR.reconcile_local_ocr(_raw(r_ov, t_ov), adjudications=adj_ov, min_agreeing_families=2)
    assert rec_ov["ocr_decision"] == "LOCAL_OCR_REVIEW_REQUIRED"
    abcd_span = [s for s in rec_ov["spans"] if s["line_id"] == "L1" and "ABCD" in s["text"]][0]
    assert abcd_span["status"] == "uncertain"
    assert "ABCE" in abcd_span["alternatives"]

    # 5. Prose lexicon diacritic restoration / conflict guard (without bypass for arbitrary accented words):
    # - Uniquely matching skeleton ('khói chóp') restores cleanly to 'khối chóp';
    # - Multi-candidate skeleton ('cậu' vs 'cầu'/'câu') stays uncertain (AMBIGUOUS_DIACRITIC_RESTORATION).
    rec_lex = OR.reconcile_local_ocr(
        _raw(
            [_line(["Tính", "thể", "tích", "khói", "chóp", "S.ABC."], 10)],
            [_line(["Tính", "thể", "tích", "khói", "chóp", "S.ABC."], 10)],
        ),
        min_agreeing_families=2,
    )
    assert "khối chóp" in rec_lex["draft_text"]
    rec_amb = OR.reconcile_local_ocr(
        _raw(
            [_line(["Xét", "cậu", "SA", "=", "a."], 10)],
            [_line(["Xét", "cậu", "SA", "=", "a."], 10)],
        ),
        min_agreeing_families=2,
    )
    assert rec_amb["ocr_decision"] == "LOCAL_OCR_REVIEW_REQUIRED"
    assert any(s["status"] == "uncertain" and s["reason"] == "AMBIGUOUS_DIACRITIC_RESTORATION" for s in rec_amb["spans"])


def test_worker_edge_bleed_protects_upper_prime_and_detects_equals_bars():
    # Upper-right prime stroke near coreink stays intact; full-height right-edge bleed is stripped.
    img = Image.new("L", (40, 28), 255)
    d = ImageDraw.Draw(img)
    d.rectangle((8, 6, 35, 22), fill=0)       # main glyph extending near upper-right prime
    d.rectangle((37, 2, 39, 10), fill=0)      # upper-right prime at right edge -> protected
    cleaned = LW._strip_edge_bleed(img, pad_x=4)
    ccs = LW._extract_ccs(LW._estimate_crop_bg_and_mask(cleaned)[-1], 40, 28)
    assert any(c["x1"] >= 37 and c["y1"] <= 14 for c in ccs)

    # Full-height neighbor character on right edge is stripped.
    img2 = Image.new("L", (40, 28), 255)
    d2 = ImageDraw.Draw(img2)
    d2.rectangle((8, 6, 20, 22), fill=0)
    d2.rectangle((37, 6, 39, 24), fill=0)     # tall neighbor bleed (y1 > 0.55*28)
    cleaned2 = LW._strip_edge_bleed(img2, pad_x=4)
    ccs2 = LW._extract_ccs(LW._estimate_crop_bg_and_mask(cleaned2)[-1], 40, 28)
    assert not any(c["x1"] >= 37 for c in ccs2)

    # Synthetic '=' bitmap vs '-' bitmap in _analyze_crop_glyph_topology
    eq_img = Image.new("L", (40, 28), 255)
    deq = ImageDraw.Draw(eq_img)
    deq.rectangle((10, 9, 28, 11), fill=0)
    deq.rectangle((10, 16, 28, 18), fill=0)
    assert LW._analyze_crop_glyph_topology(eq_img)["has_equals_bars"] is True

    dash_img = Image.new("L", (40, 28), 255)
    ImageDraw.Draw(dash_img).rectangle((10, 13, 28, 15), fill=0)
    assert LW._analyze_crop_glyph_topology(dash_img)["has_equals_bars"] is False


def test_reread_cache_deduplication_and_worker_version_isolation(monkeypatch):
    LO.clear_local_ocr_cache()
    monkeypatch.setattr(
        LO,
        "local_ocr_config",
        lambda: {"available": True, "python": "dummy.exe", "tessdata": "dummy_tess", "timeout_s": 5.0},
    )
    calls: list[list[list[int]]] = []

    class _FakeWorker:
        python = "dummy.exe"

        def request(self, payload, timeout_s):
            calls.append(payload["boxes"])
            return {
                "ok": True,
                "worker_version": LO.LOCAL_OCR_WORKER_VERSION,
                "readings": [{"rapidocr_latin_rec": f"box_{i}"} for i, _ in enumerate(payload["boxes"])],
            }

        def kill(self):
            pass

    monkeypatch.setattr(LO, "_WORKER", _FakeWorker())
    try:
        res1 = LO.reread_local_ocr_regions(b"img-bytes-1", [[10, 10, 40, 30], [10, 10, 40, 30], [50, 10, 80, 30]])
        assert res1["ok"] is True
        assert res1["unique_requested"] == 2
        assert len(calls) == 1 and len(calls[0]) == 2
        assert res1["readings"][0] == res1["readings"][1]

        res2 = LO.reread_local_ocr_regions(b"img-bytes-1", [[50, 10, 80, 30]])
        assert res2["cached"] is True and res2["cache_hits"] == 1
        assert len(calls) == 1
    finally:
        monkeypatch.setattr(LO, "_WORKER", None)
        LO.clear_local_ocr_cache()


def test_confirmation_provenance_edited_cache_key_and_144_invalidation(monkeypatch):
    from tests.cache_policy import assert_cache_policy_at_least
    assert_cache_policy_at_least(144)

    draft_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, "
        "SA vuông góc với (ABCD) và SA = a. Tính thể tích khối chóp S.ABCD."
    )
    confirmed_edited_text = draft_text.replace("SA = a.", "SA = 2a.")
    raw_sha = hashlib.sha256(draft_text.encode("utf-8")).hexdigest()

    # 1. Build provenance detects edit against raw_ocr_text_sha256 and never credits unmodified auto-OCR.
    prov_edited = M.build_verified_input_provenance(
        confirmed_edited_text,
        M.InputSourceProvenance(
            origin="local_ocr_auto_verified",
            raw_ocr_text_sha256=raw_sha,
            confirmed_span_count=1,
            selected_candidate_id="region-1~band-2",
        ),
    )
    assert prov_edited is not None
    assert prov_edited["edited_from_raw_ocr"] is True
    assert prov_edited["origin"] == "local_ocr_student_confirmed"
    assert prov_edited["counted_as_unmodified_auto_ocr"] is False

    # 2. Distinct confirmed versions produce distinct Route D cache keys and distinct verified scenes/answers.
    k_draft = prepare_local_first_hybrid(draft_text, model=resolve_hybrid_gemini_model()).cache_key
    k_edit = prepare_local_first_hybrid(confirmed_edited_text, model=resolve_hybrid_gemini_model()).cache_key
    assert k_draft != k_edit

    # 3. Stale 143:route-d SQLite row MUST miss and rebuild under 144:route-d.
    stale_env = {
        "schema_version": next(iter(M.SUPPORTED_VERSIONS)),
        "envelope": {
            "status": "ready",
            "simulation_id": "generic.semantic_program",
            "domain": "solid_geometry",
            "visual_mode": "3d",
            "scene3d": {"objects": [{"id": "STALE_143_MARKER", "type": "point3"}], "events": []},
        },
        "route_d": {"status": "SERVED", "planner": {"calls": []}},
    }
    init_db()
    with SessionLocal() as s:
        s.query(SimulationCache).filter(SimulationCache.key.in_([k_draft, k_edit])).delete(synchronize_session=False)
        s.add(
            SimulationCache(
                key=k_edit,
                problem_text=confirmed_edited_text,
                simulation_id="generic.semantic_program",
                envelope_json=json.dumps(stale_env, ensure_ascii=False),
                dsl_version=next(iter(M.SUPPORTED_VERSIONS)),
                policy_version="143:route-d",
            )
        )
        s.commit()

    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-first")
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    try:
        from tests.route_client import sign_in

        with TestClient(M.app) as client:
            sign_in(client)
            res = client.post(
                "/api/analyze",
                json={
                    "input": {
                        "type": "text",
                        "content": confirmed_edited_text,
                        "source_provenance": {
                            "origin": "local_ocr_student_confirmed",
                            "raw_ocr_text_sha256": raw_sha,
                            "student_edited": True,
                            "confirmed_span_count": 1,
                        },
                    }
                },
            )
        assert res.status_code == 200
        body = res.json()
        assert body["route_d"]["status"] == "SERVED"
        assert body["route_d"]["answers"] == {"q1": "2a³/3"}
        assert body["input_provenance"]["edited_from_raw_ocr"] is True
        assert body["input_provenance"]["origin"] == "local_ocr_student_confirmed"
        obj_ids = {o["id"] for o in body["envelope"]["scene3d"]["objects"]}
        assert "STALE_143_MARKER" not in obj_ids
    finally:
        with SessionLocal() as s:
            s.query(SimulationCache).filter(SimulationCache.key.in_([k_draft, k_edit])).delete(synchronize_session=False)
            s.commit()


def test_source_gate_missing_period_alignment_and_vision_fallback_mock():
    assert LO.LOCAL_OCR_WORKER_VERSION == "local-ocr-worker/5"

    # 1. vmmu_r513: missing period before 'Khoảng cách...' now aligns with Source Gate -> MISSING_DIMENSION + determinacy_audit
    r513 = (
        "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AA' = 1, AB = 2 "
        "Khoảng cách từ điểm A' đến mặt phẳng ADC'B' bằng."
    )
    out513 = AIR.route_text_input(r513, allow_live_ai=False)
    assert out513.telemetry.local_parse_status == "LOCAL_PARSE_COMPLETE"
    assert out513.status == "REFUSED"
    assert out513.response["envelope"]["reason_code"] == "MISSING_DIMENSION"
    assert out513.receipt.get("determinacy_audit", {}).get("status") == "UNPROVED_DUE_TO_CAPABILITY_GAP"

    # Conditional clause guard: 'Nếu AB = 2 Khoảng cách ...' must NOT split as an independent question!
    cond = "Cho hình hộp chữ nhật ABCD.A'B'C'D'. Nếu AB = 2 Khoảng cách từ điểm A' đến mặt phẳng ADC'B' bằng."
    assert registry._bien_cau(cond, len(cond) - 10) == (cond.index("Nếu"), len(cond))

    # 1b. Bare clipped item header ("43. Cho ...") + missing space after ').' (').Tính') + ordinal degree homoglyph ('60º' -> '60°') -> SERVED,
    # whereas ungrounded numeric end-of-sentence ("SA = 43. Cho ...") remains REFUSED (SOURCE_PREMISE_UNREAD).
    bare_hdr = (
        "43. Cho lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B với BC = a, "
        "góc giữa mặt phẳng (A'BC) và (ABC) bằng 60º (tham khảo hình bên).Tính thể tích lăng trụ ABC.A'B'C'."
    )
    out_bare = AIR.route_text_input(bare_hdr, allow_live_ai=False)
    assert out_bare.status == "SERVED"
    assert out_bare.response["route_d"]["answers"] == {"q1": "a³√3/2"}

    bad_num = "SA = 43. Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với (ABCD). Tính thể tích khối chóp S.ABCD."
    out_bad_num = AIR.route_text_input(bad_num, allow_live_ai=False)
    assert out_bad_num.status == "REFUSED"

    # 2. Offline deterministic Vision fallback mock: OCR low_quality/review -> Vision transcript -> Local Parser -> Scene3D
    vis_prep = {
        "status": "ready",
        "source_kind": "image",
        "problem_text": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, "
            "SA vuông góc với (ABCD) và SA = a√3. Tính thể tích khối chóp S.ABCD."
        ),
        "provenance": {"extraction_method": "vlm", "confirmation_contract_version": "ocr-confirmation-provenance/1"},
        "metrics": {"vlm_calls": 1, "processing_ms": 50.0},
    }
    vis_out = AIR.route_image_or_prepare_outcome(vis_prep, allow_live_ai=False)
    assert vis_out.status == "SERVED"
    assert vis_out.telemetry.chosen_route == "VISION_THEN_LOCAL_DETERMINISTIC"
    assert vis_out.telemetry.gemini_typed_fact_calls == 0
    assert vis_out.response["route_d"]["answers"] == {"q1": "a³√3/3"}
    assert validate_construction_continuity(vis_out.response["envelope"]["scene3d"]) == []
