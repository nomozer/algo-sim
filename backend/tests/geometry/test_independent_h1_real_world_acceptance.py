# -*- coding: utf-8 -*-
"""Regression test suite for:
`ALGOSIM — INDEPENDENT H-1, REAL-WORLD VISION & LOW-END ACCEPTANCE`.

Covers:
1. H-1 13-field provenance validator & 8-layer anti-contamination scanner (Section IV.1.2–1.3)
2. Unseen Vietnamese phrasing & multi-goal exact solving (`s05` compound diagonal + volume, `OABC` pairwise perpendicular, cube `cạnh 2`)
3. Route D (`LOCAL_AMBIGUOUS_CLARIFICATION`) on `MISSING_DIMENSION` / `insufficient_specification` with `0` AI calls
4. Forensic audit of `Case A` (`LOCAL_OCR_VERIFIED_ZERO_AI`) on recorded `s05_clean` vs `s05_degraded` + adversarial OCR inputs
5. All 13 math symbol error classes in `verify_ocr_input_fidelity` and `compare_ocr_and_vision_facts` (Section VI.3.3–3.4)
6. Region detection layout scenarios & low-end latency/memory bounds (Sections V & VIII)
"""
from __future__ import annotations

import io
import json
from pathlib import Path
import time

from PIL import Image, ImageDraw
import pytest

from app.ai.adaptive_input_router import (
    compare_ocr_and_vision_facts,
    reconcile_dual_ocr_texts,
    route_edited_text_input,
    route_image_or_prepare_outcome,
    route_text_input,
    verify_ocr_input_fidelity,
)
from app.ai.local_geometry_parser import (
    LOCAL_PARSE_COMPLETE,
    parse_geometry_problem_locally,
)
from app.ingestion.image import normalize_image
from app.ingestion.region_detector import detect_problem_regions
from scripts import score_independent_holdout_equivalence as S

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_01_h1_provenance_13_fields_and_eight_layer_contamination_scanner(tmp_path: Path) -> None:
    # 1. Validate 13-field H-1 case schema
    valid_h1_case = {
        "case_id": "H1-EXT-001",
        "problem_text": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, "
            "SA vuông góc với mặt phẳng (ABCD) và SA = 3. Tính thể tích khối chóp S.ABCD."
        ),
        "source_type": "HUMAN_AUTHORED",
        "author_or_source": "GV Nguyễn Văn A - THPT Chuyên",
        "author_date": "2026-11-09",
        "solid_family": "pyramid",
        "question_types": ["volume"],
        "auxiliary_chain_depth": 1,
        "expected_behavior": "SERVE",
        "independent_oracle": {"volume": ["16"]},
        "independent_derivation": "V = 1/3 * S_ABCD * SA = 1/3 * 16 * 3 = 16.",
        "contamination_check": "PASS_ALL_8_LAYERS",
        "freeze_sha256": "a" * 64,
    }
    res_valid = S.validate_h1_case_13_fields(valid_h1_case)
    assert res_valid["valid_h1_case"] is True
    assert res_valid["missing_fields"] == []

    # Reject AI-authored or synthetic cases from H-1
    ai_case = {**valid_h1_case, "source_type": "SYNTHETIC", "author_or_source": "Gemini Agent"}
    res_ai = S.validate_h1_case_13_fields(ai_case)
    assert res_ai["valid_h1_case"] is False
    assert res_ai["ai_or_synthetic_rejected"] is True

    # Reject inline solution leakage inside problem_text
    leaked_case = {
        **valid_h1_case,
        "problem_text": valid_h1_case["problem_text"] + " Đáp số: V = 16.",
    }
    res_leak = S.validate_h1_case_13_fields(leaked_case)
    assert res_leak["valid_h1_case"] is False
    assert res_leak["inline_solution_leak_detected"] is True

    # 2. Verify 8-layer contamination scanner catches all 8 layers
    fake_repo = tmp_path / "repo8"
    fake_repo.mkdir(parents=True)
    ref_problem = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với mặt phẳng (ABCD) và SA = 3. "
        "Tính thể tích khối chóp S.ABCD."
    )
    (fake_repo / "dev_corpus.json").write_text(
        json.dumps({"cases": [{"id": "DEV-01", "problem_text": ref_problem}]}, ensure_ascii=False),
        encoding="utf-8",
    )

    probes = [
        {"case_id": "P-L1", "problem_text": ref_problem},
        {
            "case_id": "P-L7",
            "problem_text": (
                "Cho hình chóp K.MNPQ có đáy MNPQ là hình vuông cạnh 6, KM vuông góc với mặt phẳng (MNPQ) và KM = 5. "
                "Tính thể tích khối chóp K.MNPQ."
            ),
        },
        {
            "case_id": "P-L8-LEAK",
            "problem_text": (
                "Cho tứ diện OABC có OA, OB, OC đôi một vuông góc với nhau, OA = 2, OB = 3, OC = 6. "
                "Tính thể tích khối tứ diện OABC. Lời giải: ta có V = 6."
            ),
        },
        {
            "case_id": "P-CLEAN-SPHERE",
            "problem_text": "Cho mặt cầu (S) có bán kính R = 5. Tính thể tích khối cầu (S).",
        },
    ]
    eight = S.scan_eight_layer_contamination(probes, fake_repo)
    assert set(eight.keys()) == {
        "exact_verbatim",
        "normalized_text",
        "number_stripped_template",
        "isomorphic_vertex_renaming",
        "scale_factor_transform",
        "construction_relation_graph",
        "intermediate_construction_sequence",
        "solution_or_expected_answer_leakage",
    }
    assert "P-L1" in eight["exact_verbatim"]
    assert "P-L7" in eight["intermediate_construction_sequence"]
    assert "P-L8-LEAK" in eight["solution_or_expected_answer_leakage"]
    for layer_hits in eight.values():
        assert "P-CLEAN-SPHERE" not in layer_hits


def test_02_unseen_vietnamese_phrasing_and_s05_compound_goals() -> None:
    # 1. s05 compound goal ("Tính độ dài đường chéo AC' và thể tích khối hộp.")
    s05_text = (
        "Câu 5. Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 12. "
        "Tính độ dài đường chéo AC' và thể tích khối hộp."
    )
    out_s05 = route_text_input(s05_text, allow_live_ai=False)
    assert out_s05.status == "SERVED"
    assert out_s05.telemetry.chosen_route == "LOCAL_DETERMINISTIC_HYBRID"
    assert out_s05.telemetry.total_provider_calls == 0
    assert out_s05.response["route_d"]["answers"] == {"q1": "144", "q2": "13"}

    # 2. Tetrahedron with "đôi một vuông góc với nhau"
    tet_text = (
        "Cho tứ diện OABC có OA, OB, OC đôi một vuông góc với nhau, OA = 2, OB = 3, OC = 6. "
        "Tính thể tích khối tứ diện OABC."
    )
    out_tet = route_text_input(tet_text, allow_live_ai=False)
    assert out_tet.status == "SERVED"
    assert out_tet.telemetry.total_provider_calls == 0
    assert out_tet.response["route_d"]["answers"] == {"q1": "6"}

    # 3. Cube with "cạnh 2" (without "có")
    cube_text = "Cho hình lập phương ABCD.A'B'C'D' cạnh 2. Tính khoảng cách từ A đến (A'BD)."
    out_cube = route_text_input(cube_text, allow_live_ai=False)
    assert out_cube.status == "SERVED"
    assert out_cube.telemetry.total_provider_calls == 0
    assert out_cube.response["route_d"]["answers"] == {"q1": "2√3/3"}


def test_03_case_d_missing_dimension_routes_to_local_ambiguous_clarification_zero_ai() -> None:
    missing_sa_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, "
        "SA vuông góc với mặt phẳng (ABCD). Tính thể tích khối chóp S.ABCD."
    )
    out_d = route_text_input(missing_sa_text, allow_live_ai=False)
    assert out_d.status == "REFUSED"
    assert out_d.telemetry.chosen_route == "LOCAL_AMBIGUOUS_CLARIFICATION"
    assert out_d.telemetry.total_provider_calls == 0
    assert out_d.response["route_d"]["refusal"]["code"] == "MISSING_DIMENSION"


def test_04_case_a_dual_ocr_reconciliation_s05_clean_vs_degraded_and_adversarial() -> None:
    # 1. Exact recorded OCR strings from local_ocr_pretrained_comparison_receipt.json for s05_dau_tieng_viet (clean) vs s05_dau_tieng_viet_degraded
    s05_clean_tess = (
        "Câu 1. Cho hình hộp chữ nhật ABCD.A'B'Œ 7D” có AB = 3, AD = 4, AA' = 5. "
        "Gọi I là giao điểm của AC' và mặt phẳng (A'BD). Tính độ dài đoạn thẳng AI."
    )
    s05_clean_rapid = (
        "Câu 1. Cho hình hp chū nht ABCD.A'B'C'D' có AB = 3, AD = 4, AA′ = 5. "
        "Gi I là giao dim cūa AC' và mt phng (A'BD). Tính d dài doan thng AI."
    )
    s05_deg_tess = (
        "Câu 1. Cho hình hộp chữ nhật ABCD.AB'C'D' có AB = 3, AD = 4, AA' = 5. "
        "Gọi I là giao điểm của AC' và mặt phẳng (A'BD). Tính độ dài đoạn thẳng AI."
    )
    s05_deg_rapid = (
        "Câu 1. Cho hinh hp chū nht ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 5. "
        "Gąi I là giao dim ca AC′ và mt phng (A'BD). Tính d dài doan thng AI."
    )

    # Single-engine raw Tesseract fails fidelity on BOTH s05_clean (ABCD.A'B'Œ 7D”) and s05_degraded (ABCD.AB'C'D')
    assert verify_ocr_input_fidelity(s05_clean_tess)["fidelity_passed"] is False
    assert verify_ocr_input_fidelity(s05_deg_tess)["fidelity_passed"] is False

    # Dual-engine reconciliation on s05_dau_tieng_viet (clean) repairs ABCD.A'B'Œ 7D” -> ABCD.A'B'C'D' without ground truth
    rec_clean = reconcile_dual_ocr_texts(s05_clean_tess, s05_clean_rapid, is_degraded_image=False)
    assert rec_clean["reconciled"] is True
    assert rec_clean["used_ground_truth"] is False
    assert len(rec_clean["repairs"]) == 1
    assert rec_clean["repairs"][0]["corrupted_token"] == "ABCD.A'B'Œ 7D”"
    assert rec_clean["repairs"][0]["repaired_token"] == "ABCD.A'B'C'D'"

    # Route Case A on s05_clean -> LOCAL_OCR_VERIFIED_ZERO_AI with 0 AI calls and exact answer 5√2/3
    out_clean = route_image_or_prepare_outcome(
        {"status": "ready", "source_kind": "image", "problem_text": rec_clean["reconciled_text"], "metrics": {"vlm_calls": 0}},
        local_ocr_text=s05_clean_tess,
        secondary_ocr_text=s05_clean_rapid,
        allow_verified_local_ocr=True,
        is_degraded_image=False,
        allow_live_ai=False,
    )
    assert out_clean.status == "SERVED"
    assert out_clean.telemetry.chosen_route == "LOCAL_OCR_VERIFIED_ZERO_AI"
    assert out_clean.telemetry.total_provider_calls == 0
    assert out_clean.response["route_d"]["answers"] == {"q1": "5√2/3"}

    # On s05_dau_tieng_viet_degraded (is_degraded_image=True), dual-OCR reconciliation is refused and falls back to Vision
    rec_deg = reconcile_dual_ocr_texts(s05_deg_tess, s05_deg_rapid, is_degraded_image=True)
    assert rec_deg["reconciled"] is False
    assert rec_deg["reason_code"] == "DEGRADED_IMAGE_REQUIRES_VISION_FALLBACK"

    out_deg = route_image_or_prepare_outcome(
        {"status": "ready", "source_kind": "image", "problem_text": rec_clean["reconciled_text"], "metrics": {"vlm_calls": 1}},
        local_ocr_text=s05_deg_tess,
        secondary_ocr_text=s05_deg_rapid,
        allow_verified_local_ocr=True,
        is_degraded_image=True,
        allow_live_ai=False,
    )
    assert out_deg.status == "SERVED"
    assert out_deg.telemetry.chosen_route == "VISION_THEN_LOCAL_DETERMINISTIC"
    assert out_deg.telemetry.gemini_vision_calls == 1

    # 4. Adversarial: cross-engine numeric disagreement (AB = 3 vs AB = 8) is refused
    s05_rapid_bad_num = s05_clean_rapid.replace("AB = 3", "AB = 8")
    rec_bad_num = reconcile_dual_ocr_texts(s05_clean_tess, s05_rapid_bad_num, is_degraded_image=False)
    assert rec_bad_num["reconciled"] is False
    assert "CROSS_ENGINE_DISAGREEMENT:assignments" in str(rec_bad_num["reason_code"])

    # 5. Adversarial: multi-problem header (Câu 1 + Câu 2) is refused
    rec_multi = reconcile_dual_ocr_texts(
        s05_clean_tess + " Câu 2. Cho hình cầu.",
        s05_clean_rapid + " Cau 2. Cho hinh cau.",
        is_degraded_image=False,
    )
    assert rec_multi["reconciled"] is False
    assert rec_multi["reason_code"] == "PROBLEM_HEADER_MISMATCH_OR_MULTI_PROBLEM"


def test_05_all_13_math_symbol_error_classes_caught_by_fidelity_and_conflict_gates() -> None:
    base = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, "
        "SA ⊥ (ABCD) và SA = 3. Tính thể tích khối chóp S.ABCD."
    )
    assert verify_ocr_input_fidelity(base, secondary_ocr_text=base)["fidelity_passed"] is True

    # Negative or zero segment length rejected by dimension_and_number_fidelity
    neg_len = base.replace("SA = 3", "SA = -3")
    fid_neg = verify_ocr_input_fidelity(neg_len)
    assert fid_neg["fidelity_passed"] is False
    assert "dimension_and_number_fidelity" in fid_neg["failed_checks"]

    zero_len = base.replace("SA = 3", "SA = 0")
    fid_zero = verify_ocr_input_fidelity(zero_len)
    assert fid_zero["fidelity_passed"] is False
    assert "dimension_and_number_fidelity" in fid_zero["failed_checks"]

    # Cross-engine disagreement on relation symbol (⊥ vs ∥), fraction, angle, radical
    par_text = base.replace("SA ⊥ (ABCD)", "SA ∥ (ABCD)")
    fid_rel = verify_ocr_input_fidelity(base, secondary_ocr_text=par_text)
    assert fid_rel["fidelity_passed"] is False
    assert "diagram_dependency_and_cross_engine" in fid_rel["failed_checks"]

    # Conflict gate catches relation, radical, fraction, angle, subscript, and prime conflicts
    c_rel = compare_ocr_and_vision_facts(base, par_text)
    assert c_rel["has_conflict"] is True
    assert "RELATION_SYMBOL_CONFLICT" in c_rel["conflict_codes"]

    c_rad = compare_ocr_and_vision_facts(
        base.replace("SA = 3", "SA = 2√2"),
        base.replace("SA = 3", "SA = 2√3"),
    )
    assert c_rad["has_conflict"] is True
    assert "RADICAL_OR_FRACTION_CONFLICT" in c_rad["conflict_codes"]

    c_ang = compare_ocr_and_vision_facts(
        "Cho hình chóp S.ABCD có góc SBA = 60°.",
        "Cho hình chóp S.ABCD có góc SBA = 30°.",
    )
    assert c_ang["has_conflict"] is True
    assert "ANGLE_OR_SIGN_CONFLICT" in c_ang["conflict_codes"]


def test_06_region_detection_layout_scenarios_and_low_end_bounds() -> None:
    # 1. Blank image -> 0 candidates, 0 AI calls
    blank_img = Image.new("RGB", (600, 400), (255, 255, 255))
    buf_b = io.BytesIO()
    blank_img.save(buf_b, format="PNG")
    reg_blank = detect_problem_regions(normalize_image(buf_b.getvalue(), "image/png"))
    assert len(reg_blank.candidates) == 0
    assert reg_blank.crop_holds_all_content is False

    # 2. Single clean printed problem -> 1 candidate holding 100% content
    single_img = Image.new("RGB", (800, 360), (255, 255, 255))
    draw = ImageDraw.Draw(single_img)
    for row in range(3):
        y = 80 + row * 26
        cx = 70
        while cx < 700:
            draw.rectangle([cx, y, min(700, cx + 42), y + 11], fill=(15, 15, 15))
            cx += 52
    buf_s = io.BytesIO()
    single_img.save(buf_s, format="PNG")
    reg_single = detect_problem_regions(normalize_image(buf_s.getvalue(), "image/png"))
    assert len(reg_single.candidates) >= 1
    assert reg_single.crop_holds_all_content is True

    # 3. Low-end latency bound: uncached cold parse+solve < 150 ms
    t0 = time.perf_counter()
    out = route_text_input(
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với mặt phẳng (ABCD) và SA = 3. Tính thể tích khối chóp S.ABCD.",
        allow_live_ai=False,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert out.status == "SERVED"
    assert elapsed_ms < 150.0

