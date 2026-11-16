# -*- coding: utf-8 -*-
"""Unified Campaign Verification Suite (`unified-geometry-understanding-ocr-autonomous-planning`):

Covers Stream A (composable grounding, A4 `PlaneConstraintSpec(contains_points)` with `@id`,
nested descriptor bounds, `NC-*` + `DEV37` + `dp_unnamed_through_point` NL grounding, out-of-order MC stripping,
locked surface preservation), Stream B (`_RAW_OCR_CACHE`/`_REREAD_CACHE` split, `100°..179°`, `_yoverlap`
row clustering, choice-band tolerance, `_split_glued_words` preserving `S,ABCD`/`S.A8CD`, Unicode vote
ranking, `glyph_topology` strict positive + negative checks with `0` false auto-accepts, `ocr_decision`),
and Stream C (`Scene3D` continuity, `output-policy/1` Mode A `0` answer leaks, `MG9` IR budget gate,
SQLite `/api/analyze` `142:route-d` -> `143:route-d` cache invalidation).
"""
from __future__ import annotations

import asyncio
import importlib.util
import io
import json
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
import pytest

from app import main as M
from app.ai import adaptive_input_router as AIR
from app.ai import fact_extraction, function_calling
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.hybrid_offline import prepare_local_first_hybrid, resolve_hybrid_gemini_model
from app.ai.local_geometry_parser import LOCAL_PARSE_COMPLETE, parse_geometry_problem_locally
from app.ingestion import local_ocr as LO
from app.ingestion import local_ocr_route as LR
from app.ingestion import ocr_reconcile as OR
from app.persistence.db import SessionLocal, SimulationCache, init_db
from app.ai.typed_fact_next_extraction import typed_fact_next_surface_fingerprint
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity

ROOT = Path(__file__).resolve().parents[3]


def _load_mod(name: str, rel_path: str):
    spec = importlib.util.spec_from_file_location(name, str(ROOT / rel_path))
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _line(words: list[str], y: int, *, x0: int = 10, h: int = 28, cw: int = 14, conf: float = 92.0):
    out, x = [], x0
    for w in words:
        wid = max(cw, cw * len(w))
        out.append({"text": w, "conf": conf, "bbox": [x, y, x + wid, y + h]})
        x += wid + cw
    return {"text": " ".join(words), "conf": conf, "bbox": [x0, y, x - cw, y + h], "words": out}


def _raw(rapid_lines, tess_lines, w: int = 1200, h: int = 400):
    return {
        "width": w,
        "height": h,
        "engines": {
            "rapidocr": {"engine_version": "rapidocr test", "lines": rapid_lines},
            "tesseract": {"engine_version": "tesseract test", "lines": tess_lines},
        },
    }


# ── Stream A: Grounded Vietnamese Understanding & A4 PlaneConstraintSpec ─────────────────────────────────────────


def test_stream_a_locked_surfaces_preserved():
    assert function_calling.surface_fingerprint() == "7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25"
    assert fact_extraction.surface_fingerprint("flat") == "485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a"
    assert fact_extraction.surface_fingerprint("v3") == "4bff35bbf690a9973b2b7834019b908d507bbbb4277928e36d12dcff657e226f"
    assert typed_fact_next_surface_fingerprint() == "33197a45e0620d94a669047b47907479d1e7f07b1dc76e7c6abd75ada7a6df14"


def test_stream_a_nested_described_depth_bound():
    base = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD) và SA = 2. "
    )
    q_h1 = "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)"
    txt2 = base + f"Tính khoảng cách từ {q_h1} đến mặt phẳng (SAB)."
    p2 = {
        "schema_version": "typed-fact-next/2",
        "problem_text": txt2,
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
    res2 = run_typed_fact_next_v2_route(p2)
    assert res2.status == "SERVED", res2.reason
    assert res2.route_d["answers"]["q1"] == "2/3"
    assert validate_construction_continuity(res2.scene3d) == []

    nl2 = AIR.route_text_input(txt2, allow_live_ai=False)
    assert nl2.status == "SERVED", nl2.telemetry.fallback_reason
    assert nl2.response["route_d"]["answers"]["q1"] == "2/3"
    assert validate_construction_continuity(nl2.response["envelope"]["scene3d"]) == []

    # Nesting deeper than 2 levels must fail closed
    q_m3 = f"trung điểm của đoạn nối S với {q_h1}"
    txt3 = base + f"Tính khoảng cách từ {q_m3} đến mặt phẳng (SAB)."
    p3 = {
        **p2,
        "problem_text": txt3,
        "described_points": [
            *p2["described_points"],
            {"described_id": "m3", "kind": "midpoint", "segment": ["S", "@h1"], "quote": q_m3},
        ],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@m3", "plane": ["S", "A", "B"]}, "solid_id": "s1", "quote": f"Tính khoảng cách từ {q_m3} đến mặt phẳng (SAB)"}],
    }
    res3 = run_typed_fact_next_v2_route(p3)
    assert res3.status == "REFUSED"
    assert res3.code == "PLAN_TOO_LARGE"


def test_stream_a_a4_contains_points_served_and_non_contains_refused():
    for label, txt in [
        ("A4_nl_dir", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với đáy và SA = a. Gọi M là trung điểm SC. Mặt phẳng (P) đi qua A, M và song song với BD. Dựng thiết diện của hình chóp cắt bởi (P)."),
        ("A4_nl_3pt", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với đáy và SA = a. Gọi M là trung điểm SB, N là trung điểm SC, K là trọng tâm tam giác SAD. Xác định thiết diện của hình chóp cắt bởi mặt phẳng qua M, N, K."),
    ]:
        out = AIR.route_text_input(txt, allow_live_ai=False)
        assert out.status == "SERVED", (label, out.telemetry.fallback_reason)
        assert out.telemetry.total_provider_calls == 0
        assert validate_construction_continuity(out.response["envelope"]["scene3d"]) == []

    # Non-contains_points constraint carrying @id remains strictly refused
    bad_txt = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với đáy và SA = a. Gọi M là trung điểm SC. Mặt phẳng (P) đi qua A và song song với đường thẳng nối S với trung điểm của SC. Xác định thiết diện của hình chóp cắt bởi (P)."
    bad_payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": bad_txt,
        "length_unit": "a",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": [
            {"kind": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "a"}, "solid_id": "s1", "quote": "đáy ABCD là hình vuông cạnh a"},
            {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "solid_id": "s1", "quote": "SA vuông góc với đáy"},
            {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "a"}, "solid_id": "s1", "quote": "SA = a"},
        ],
        "described_points": [{"described_id": "m1", "kind": "midpoint", "segment": ["S", "C"], "quote": "M là trung điểm SC"}],
        "derived_sections": [{
            "section_id": "sec1", "plane_name": "P", "target_solid_id": "s1", "plane_kind": "constrained",
            "constraints": [{"kind": "contains_points", "operands": ["A"]}, {"kind": "parallel_to_line", "operands": ["S", "@m1"]}],
            "stated_intersections": [], "quote": "Mặt phẳng (P) đi qua A và song song với đường thẳng nối S với trung điểm của SC",
        }],
        "simulation_goals": [
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"},
            {"goal_id": "g_sec", "kind": "construct_plane_section", "target_section_id": "sec1", "quote": "Xác định thiết diện của hình chóp cắt bởi (P)"},
        ],
        "math_goals": [],
    }
    bad_res = run_typed_fact_next_v2_route(bad_payload)
    assert bad_res.status == "REFUSED" and bad_res.code == "INVALID_QUALIFIED_REF"


def test_stream_a_nc_nl_and_dev37_promotions_with_continuity():
    eval_nc = _load_mod("eval_nc_u", "docs/evaluation/geometry/runs/planner-autonomous-composition-and-search-efficiency/tools/evaluate_autonomous_composition.py")
    nc_cases = {c["id"]: c for c in eval_nc._build_novel_positive_cases()}
    for cid in ("NC-A1", "NC-B1", "NC-C1", "NC-D2_E1", "NC-E3_T5"):
        c = nc_cases[cid]
        out = AIR.route_text_input(c["text"], allow_live_ai=False)
        assert out.status == "SERVED", (cid, out.telemetry.fallback_reason)
        assert out.telemetry.local_parse_status == LOCAL_PARSE_COMPLETE
        assert validate_construction_continuity(out.response["envelope"]["scene3d"]) == []

    dev37 = _load_mod("dev37_u", "docs/evaluation/geometry/runs/semantic-failure-safe-image-segmentation/tools/semantic_dev_corpus.py").CORPUS
    for cid in ("diagram_benign", "sec_do_P_cat"):
        out = AIR.route_text_input(dev37[cid]["text"], allow_live_ai=False)
        assert out.status == "SERVED", (cid, out.telemetry.fallback_reason)
        assert validate_construction_continuity(out.response["envelope"]["scene3d"]) == []

    dp_txt = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
        "Xác định thiết diện của hình chóp cắt bởi mặt phẳng đi qua trung điểm của SA và song song với mặt đáy."
    )
    out_dp = AIR.route_text_input(dp_txt, allow_live_ai=False)
    assert out_dp.status == "SERVED"
    assert validate_construction_continuity(out_dp.response["envelope"]["scene3d"]) == []

    ooo_mc = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
        "Tính thể tích khối chóp S.ABCD.\nA. a³/3.\nB. a³/2.\nD. a³.\nC. a³/6."
    )
    out_mc = AIR.route_text_input(ooo_mc, allow_live_ai=False)
    assert out_mc.status == "SERVED"
    assert out_mc.response["route_d"]["answers"] == {"q1": "a³/3"}


def test_stream_a_compound_goals_and_trailing_unit_meta_preserved():
    # Regression guard for compound multi-distance / length clauses and trailing "theo đơn vị độ" / "theo x"
    t_two_dist = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với (ABCD), SA = a. "
        "Tính khoảng cách từ B đến mặt phẳng (SAC) và khoảng cách từ A đến mặt phẳng (SBC)."
    )
    lp_td = parse_geometry_problem_locally(t_two_dist)
    assert lp_td.status == LOCAL_PARSE_COMPLETE
    assert len(lp_td.payload["math_goals"]) == 2
    assert AIR.route_text_input(t_two_dist, allow_live_ai=False).status == "SERVED"

    t_dist_len = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD), SA = a. "
        "Tính khoảng cách từ B đến mặt phẳng (SAC) và độ dài đoạn thẳng SC."
    )
    assert AIR.route_text_input(t_dist_len, allow_live_ai=False).status == "SERVED"

    t_deg = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại B, AC = 2a, "
        "SA vuông góc với mặt phẳng (ABC), tam giác SAB cân. "
        "Tính số đo góc giữa hai mặt phẳng (SBC) và (ABC) theo đơn vị độ."
    )
    out_deg = AIR.route_text_input(t_deg, allow_live_ai=False)
    assert out_deg.status == "SERVED"
    assert out_deg.response["route_d"]["answers"]["q1"] == "45°"

    t_theo_x = (
        "Cho hình chóp tứ giác đều S.ABCD có độ dài cạnh bên bằng x và diện tích đáy bằng x². "
        "Tính khoảng cách từ A đến mặt phẳng (SBC) theo x."
    )
    out_x = AIR.route_text_input(t_theo_x, allow_live_ai=False)
    assert out_x.status == "SERVED"
    assert out_x.response["route_d"]["answers"]["q1"] == "x√6/3"


# ── Stream B: Geometry-Aware OCR Reliability & Strict Verification ───────────────────────────────────────────────


def test_stream_b_cache_split_non_eviction(monkeypatch):
    LO.clear_local_ocr_cache()
    monkeypatch.setattr(LO, "local_ocr_config", lambda: {"available": True, "python": "fake", "tessdata": "fake", "timeout_s": 5.0})

    class _FakeWorker:
        python = "fake"
        def pid(self):
            return 999
        def request(self, payload, timeout_s):
            if payload.get("op") == "reread":
                return {"ok": True, "readings": [{"rapidocr_latin_rec": "a²", "tesseract_eng_line": "a2"}], "ms": 1.0}
            return {"ok": True, "width": 100, "height": 40, "engines": {"rapidocr": {"lines": []}, "tesseract": {"lines": []}}}
        def kill(self):
            pass

    monkeypatch.setattr(LO, "_WORKER", _FakeWorker())
    LO.run_local_ocr(b"img-main")
    for idx in range(30):
        LO.reread_local_ocr_regions(b"img-main", [[idx, 0, idx + 10, 20]])
    hit_main = LO.run_local_ocr(b"img-main")
    assert hit_main["cached"] is True
    assert len(LO._REREAD_CACHE) == 30
    assert len(LO._RAW_OCR_CACHE) == 1
    LO.clear_local_ocr_cache()
    monkeypatch.setattr(LO, "_WORKER", None)


def test_stream_b_corruption_bounds_glued_tokens_row_clustering_and_ranking():
    assert not OR.has_shared_corruption("120°")
    assert not OR.has_shared_corruption("150°")
    assert OR.has_shared_corruption("180°")
    assert OR.has_shared_corruption("600°")
    assert OR.has_shared_corruption("S,ABCD")

    # _yoverlap row clustering keeps slightly shifted words on same baseline without round(cy/band) artifacts
    r = [_line(["Cho", "hình", "chóp"], 10), _line(["S.ABCD", "cạnh", "a."], 16, x0=220)]
    t = [_line(["Cho", "hình", "chóp", "S.ABCD", "cạnh", "a."], 12)]
    rec_row = OR.reconcile_local_ocr(_raw(r, t), min_agreeing_families=2)
    assert len(rec_row["lines"]) <= 2
    assert "Cho hình chóp S.ABCD cạnh a." == " ".join(rec_row["draft_text"].splitlines())

    # Glued prose(MATH) and non-decimal comma splitting, while S,ABCD & S.A8CD remain blocked
    r_glue = [{
        "text": "mặt phẳng(ABCD) có a,BC",
        "conf": 95.0,
        "bbox": [10, 10, 380, 38],
        "words": [
            {"text": "mặt", "conf": 95.0, "bbox": [10, 10, 52, 38]},
            {"text": "phẳng(ABCD)", "conf": 95.0, "bbox": [66, 10, 236, 38]},
            {"text": "có", "conf": 95.0, "bbox": [250, 10, 278, 38]},
            {"text": "a,BC", "conf": 95.0, "bbox": [292, 10, 352, 38]},
        ],
    }]
    t_glue = [{
        "text": "mặt phẳng (ABCD) có a, BC",
        "conf": 95.0,
        "bbox": [10, 10, 380, 38],
        "words": [
            {"text": "mặt", "conf": 95.0, "bbox": [10, 10, 52, 38]},
            {"text": "phẳng", "conf": 95.0, "bbox": [66, 10, 140, 38]},
            {"text": "(ABCD)", "conf": 95.0, "bbox": [146, 10, 236, 38]},
            {"text": "có", "conf": 95.0, "bbox": [250, 10, 278, 38]},
            {"text": "a,", "conf": 95.0, "bbox": [292, 10, 318, 38]},
            {"text": "BC", "conf": 95.0, "bbox": [322, 10, 352, 38]},
        ],
    }]
    rec_glue = OR.reconcile_local_ocr(_raw(r_glue, t_glue), min_agreeing_families=2)
    assert "phẳng (ABCD)" in rec_glue["draft_text"] and "a, BC" in rec_glue["draft_text"]
    assert rec_glue["extraction_verified"] is True, rec_glue["blocking_reasons"]

    rec_bad = OR.reconcile_local_ocr(_raw([_line(["Hình", "chóp", "S,ABCD."], 10)], [_line(["Hình", "chóp", "S,ABCD."], 10)]), min_agreeing_families=2)
    assert rec_bad["extraction_verified"] is False
    assert rec_bad["ocr_decision"] == "LOCAL_OCR_REVIEW_REQUIRED"

    # Unicode math ranks above degraded ASCII double-votes (`av3` across 2 readers)
    r_rk = [_line(["Cho", "SA", "=", "a√3."], 10)]
    t_rk = [_line(["Cho", "SA", "=", "av3."], 10)]
    adj_rk = {"L1:S4": {"rapidocr_latin_rec": "av3.", "tesseract_eng_line": "av3."}}
    rec_rk = OR.reconcile_local_ocr(_raw(r_rk, t_rk), adjudications=adj_rk, min_agreeing_families=2)
    assert "a√3." in rec_rk["draft_text"]
    assert rec_rk["extraction_verified"] is False  # no glyph_topology supplied -> must NOT auto-accept


def test_stream_b_glyph_topology_strict_positive_and_negative():
    r = [_line(["Cho", "cạnh", "SA", "=", "a²."], 10)]
    t = [_line(["Cho", "cạnh", "SA", "=", "a2."], 10)]
    raw = _raw(r, t)
    adj = {"L1:S5": {"rapidocr_latin_rec": "a2.", "tesseract_eng_line": "a2."}}

    # 1. Missing glyph_topology (synthetic dict) -> NEVER auto-accepts
    assert OR.reconcile_local_ocr(raw, adjudications=adj, min_agreeing_families=2)["ocr_decision"] == "LOCAL_OCR_REVIEW_REQUIRED"
    # 2. Blurry crop -> NEVER auto-accepts
    meta_blur = {"L1:S5": {"glyph_topology": {"blurry": True, "has_superscript_cc": True}}}
    assert OR.reconcile_local_ocr(raw, adjudications=adj, adjudication_meta=meta_blur, min_agreeing_families=2)["ocr_decision"] == "LOCAL_OCR_REVIEW_REQUIRED"
    # 3. Inline a2 (no superscript CC) -> NEVER auto-accepts
    meta_nosup = {"L1:S5": {"glyph_topology": {"blurry": False, "has_superscript_cc": False}}}
    assert OR.reconcile_local_ocr(raw, adjudications=adj, adjudication_meta=meta_nosup, min_agreeing_families=2)["ocr_decision"] == "LOCAL_OCR_REVIEW_REQUIRED"
    # 4. Wrong superscript digit (a³ vs Tesseract a2) -> NEVER auto-accepts
    raw_wrong = _raw([_line(["Cho", "cạnh", "SA", "=", "a³."], 10)], t)
    meta_ok = {"L1:S5": {"glyph_topology": {"blurry": False, "has_superscript_cc": True, "superscript_digit_hint": None}}}
    assert OR.reconcile_local_ocr(raw_wrong, adjudications=adj, adjudication_meta=meta_ok, min_agreeing_families=2)["ocr_decision"] == "LOCAL_OCR_REVIEW_REQUIRED"
    # 5. Low word confidence (<82) -> NEVER auto-accepts
    raw_low = _raw([_line(["Cho", "cạnh", "SA", "=", "a²."], 10, conf=70.0)], t)
    assert OR.reconcile_local_ocr(raw_low, adjudications=adj, adjudication_meta=meta_ok, min_agreeing_families=2)["ocr_decision"] == "LOCAL_OCR_REVIEW_REQUIRED"
    # 6. Clean crop + sharp superscript CC + conf>=82 + Tesseract base agreement -> LOCAL_OCR_ACCEPT
    acc = OR.reconcile_local_ocr(raw, adjudications=adj, adjudication_meta=meta_ok, min_agreeing_families=2)
    assert acc["extraction_verified"] is True
    assert acc["ocr_decision"] == "LOCAL_OCR_ACCEPT"
    # 7. Reject unreadable provenance
    rej = OR.reconcile_local_ocr(_raw([], []), min_agreeing_families=2)
    assert rej["ocr_decision"] == "LOCAL_OCR_REJECT_UNREADABLE"


# ── Stream C: Output Policy Mode A, Budget Gate, & Cache 143 Invalidation ─────────────────────────────────────────


def test_stream_c_mode_a_and_cache_143_invalidation(monkeypatch):
    assert M.CACHE_VERSION == "144"
    assert M.ROUTE_D_CACHE_POLICY == "144:route-d"

    trig_txt = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với (ABC) và SA = a. "
        "Tính côsin của góc giữa SB và mặt phẳng (ABC)."
    )
    out_trig = AIR.route_text_input(trig_txt, allow_live_ai=False)
    assert out_trig.status == "SERVED"
    sgc = out_trig.response["route_d"]["source_goal_completion"]
    assert sgc["numeric_answer_shown"] is False
    assert sgc["goals"][0]["numeric_source_goal"] == "NOT_ANSWERED"
    assert validate_construction_continuity(out_trig.response["envelope"]["scene3d"]) == []

    # Stale 142:route-d row must miss and rebuild under 143:route-d
    key = prepare_local_first_hybrid(trig_txt, model=resolve_hybrid_gemini_model()).cache_key
    stale_env = {
        "schema_version": next(iter(M.SUPPORTED_VERSIONS)),
        "envelope": {
            "status": "ready",
            "simulation_id": "generic.semantic_program",
            "domain": "solid_geometry",
            "visual_mode": "3d",
            "scene3d": {"objects": [{"id": "STALE_142_MARKER", "type": "point3"}], "events": []},
        },
        "route_d": {"status": "SERVED", "planner": {"calls": []}},
    }
    init_db()
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(
            SimulationCache(
                key=key,
                problem_text=trig_txt,
                simulation_id="generic.semantic_program",
                envelope_json=json.dumps(stale_env, ensure_ascii=False),
                dsl_version=next(iter(M.SUPPORTED_VERSIONS)),
                policy_version="142:route-d",
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
            res = client.post("/api/analyze", json={"input": {"type": "text", "content": trig_txt}})
        assert res.status_code == 200
        obj_ids = {o["id"] for o in res.json()["envelope"]["scene3d"]["objects"]}
        assert "STALE_142_MARKER" not in obj_ids
    finally:
        with SessionLocal() as s:
            s.query(SimulationCache).filter_by(key=key).delete()
            s.commit()
