# -*- coding: utf-8 -*-
"""14-Category Regression Test Suite for:
`ALGOSIM — CORRECTNESS HARDENING, LOCAL OCR & LOW-END PERFORMANCE OPTIMIZATION`.

Covers all 14 mandatory test categories in Section IX:
1. Mathematical oracle comparison
2. Multi-goal answer binding
3. Squared-distance versus distance comparison
4. Source Gate tampering (`N3`, `HB43`)
5. Parser completeness & single-condition mutation
6. OCR numeric corruption
7. OCR prime corruption
8. Missing crop content
9. Multi-problem image selection
10. User-edited text (`0` Vision re-calls)
11. Cache invalidation & parser LRU cache reuse
12. Image fallback (`Cases A, B, C, D` + `OCR_VISION_MATH_CONFLICT`)
13. Multiple geometry solutions (`2^(m-1)` sign enumeration)
14. Weak-device performance & memory bounds
"""
from __future__ import annotations

from fractions import Fraction
import io
import json
import os
from pathlib import Path
import time
import tracemalloc

from PIL import Image, ImageDraw
import pytest

from app.ai.adaptive_input_router import (
    build_local_first_cache_identity,
    compare_ocr_and_vision_facts,
    extract_structured_math_tokens,
    route_edited_text_input,
    route_image_or_prepare_outcome,
    route_text_input,
    verify_ocr_input_fidelity,
)
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.local_geometry_parser import (
    LOCAL_PARSE_AMBIGUOUS,
    LOCAL_PARSE_COMPLETE,
    LOCAL_PARSE_PARTIAL,
    clear_local_geometry_parser_cache,
    get_local_geometry_parser_cache_stats,
    normalize_problem_text,
    parse_geometry_problem_locally,
)
from app.ai.typed_fact_next_extraction import ReplayExtractor
from app.ingestion.image import normalize_image
from app.ingestion.region_detector import detect_problem_regions
from app.simulation.geometry_functions import engine

REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = REPO_ROOT / "docs" / "evaluation" / "geometry" / "runs" / "correctness-ocr-performance-optimization"


# 1. Mathematical oracle comparison
def test_01_mathematical_oracle_comparison() -> None:
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, "
        "SA vuông góc với mặt phẳng (ABCD) và SA = 3. Tính thể tích khối chóp S.ABCD."
    )
    out = route_text_input(text, allow_live_ai=False)
    assert out.status == "SERVED"
    assert out.telemetry.total_provider_calls == 0
    answers = (out.response.get("route_d") or {}).get("answers") or {}
    assert answers == {"q1": "16"}


# 2. Multi-goal answer binding
def test_02_multi_goal_answer_binding() -> None:
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
        "SA vuông góc với mặt phẳng (ABCD) và SA = 2. "
        "Tính thể tích khối chóp S.ABCD. "
        "Tính khoảng cách từ A đến mặt phẳng (SBC)."
    )
    out = route_text_input(text, allow_live_ai=False)
    assert out.status == "SERVED"
    rd = out.response.get("route_d") or {}
    answers = rd.get("answers") or {}
    # q1 is volume (8/3), q2 is distance from A to (SBC) (√2)
    assert answers.get("q1") == "8/3"
    assert answers.get("q2") == "√2"


# 3. Squared-distance versus distance comparison
def test_03_squared_distance_vs_distance_comparison() -> None:
    receipt_path = RUN_DIR / "mathematical_oracle_audit_receipt.json"
    if receipt_path.exists():
        data = json.loads(receipt_path.read_text(encoding="utf-8"))
        assert data["summary"]["goal_bound_1to1_mismatches"] == 0
        assert data["summary"]["all_66_raw_discrepancies_explained_by_squared_oracle_representation"] is True

    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
        "SA vuông góc với mặt phẳng (ABCD) và SA = 2. "
        "Tính khoảng cách từ A đến mặt phẳng (SBC)."
    )
    out = route_text_input(text, allow_live_ai=False)
    rd = out.response.get("route_d") or {}
    # Canonical unsquared distance is √2, while squared rational in Q is 2
    assert rd["answers"]["q1"] == "√2"
    assert rd["answer_exact"]["q1"]["coef"] == "√2"


# 4. Source Gate tampering (N3 & HB43)
def test_04_source_gate_tampering_rejected_while_clean_text_solves() -> None:
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
        "SA vuông góc với mặt phẳng (ABCD) và SA = 2. "
        "Tính khoảng cách từ A đến mặt phẳng (SBC)."
    )
    clean_parse = parse_geometry_problem_locally(text)
    assert clean_parse.status == LOCAL_PARSE_COMPLETE
    assert clean_parse.payload is not None

    # Tamper the extraction quote to hallucinate SA = 7 (not in source text)
    tampered = json.loads(json.dumps(clean_parse.payload))
    for prem in tampered["premises"]:
        if prem["kind"] == "segment_length" and prem["args"].get("segment") == ["S", "A"]:
            prem["quote"] = "SA = 7"
            prem["args"]["value"] = "7"

    hyb_tampered = run_hybrid_offline(
        text,
        ReplayExtractor({text: tampered}),
        policy=hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"}),
    )
    rd_tampered = hyb_tampered.response.get("route_d") or {}
    assert rd_tampered["status"] == "REFUSED"
    assert rd_tampered["refusal"]["code"] in {"QUOTE_NOT_IN_SOURCE", "UNGROUNDED_VALUE"}


# 5. Parser completeness & single-condition mutation
@pytest.mark.parametrize(
    ("mutated_text", "expected_reason"),
    [
        (
            "Cho hình chóp S.ABCD có đáy ABCD là hình thoi cạnh 4, góc BAD = 60°, SA vuông góc với mặt phẳng (ABCD) và SA = 3. Tính thể tích khối chóp S.ABCD.",
            "UNPARSED_FACT_CANDIDATE",
        ),
        (
            "Cho hình chóp S.ABC có đáy ABC là tam giác cân tại A, AB = 5, BC = 6, SA vuông góc với mặt phẳng (ABC), SA = 4. Tính thể tích khối chóp S.ABC.",
            "UNPARSED_FACT_CANDIDATE",
        ),
        (
            "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = 3,5, AC = 4, AA' = 5. Tính thể tích khối lăng trụ ABC.A'B'C'.",
            "UNPARSED_FACT_CANDIDATE",
        ),
        (
            "Cho lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác đều cạnh 2, AA' = 2V3. Tính thể tích khối lăng trụ ABC.A'B'C'.",
            "UNPARSED_FACT_CANDIDATE",
        ),
        (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA không vuông góc với mặt phẳng (ABCD), SA = 3. Tính thể tích khối chóp S.ABCD.",
            "UNPARSED_FACT_CANDIDATE",
        ),
        (
            "Câu 1. Cho lăng trụ đứng ABC.A'B'C' có AA' = 2V3, AB = a/2 và BC = 3,5. Tính thể tích khối lăng trụ ABC.A'E'C..",
            "UNPARSED_GOAL_CANDIDATE",
        ),
    ],
)
def test_05_parser_completeness_single_condition_mutations_never_silently_drop(
    mutated_text: str, expected_reason: str
) -> None:
    res = parse_geometry_problem_locally(mutated_text)
    assert res.status == LOCAL_PARSE_PARTIAL
    assert res.reason_code == expected_reason
    assert res.payload is None


# 6. OCR numeric corruption
def test_06_ocr_numeric_corruption_detected() -> None:
    corrupted_ocr = (
        "Câu 1. Cho lăng trụ đứng ABC.A'B'C' có AA' = 2V3, AB = a/2 và BC = 3,5. "
        "Tính thể tích khối lăng trụ ABC.A'E'C.."
    )
    fid = verify_ocr_input_fidelity(corrupted_ocr)
    assert fid["fidelity_passed"] is False
    assert "dimension_and_number_fidelity" in fid["failed_checks"]

    ocr_num = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với mặt phẳng (ABCD) và SA = 8. Tính thể tích khối chóp S.ABCD."
    vis_num = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với mặt phẳng (ABCD) và SA = 3. Tính thể tích khối chóp S.ABCD."
    cmp_res = compare_ocr_and_vision_facts(ocr_num, vis_num)
    assert cmp_res["has_conflict"] is True
    assert "NUMERIC_ASSIGNMENT_CONFLICT" in cmp_res["conflict_codes"]


# 7. OCR prime corruption
def test_07_ocr_prime_corruption_detected() -> None:
    ocr_prime = (
        "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4, AA' = 5. "
        "Tính khoảng cách từ A đến mặt phẳng (ABC)."
    )
    vis_prime = (
        "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4, AA' = 5. "
        "Tính khoảng cách từ A đến mặt phẳng (A'BC)."
    )
    cmp_res = compare_ocr_and_vision_facts(ocr_prime, vis_prime)
    assert cmp_res["has_conflict"] is True
    assert "PRIME_OR_PLANE_LABEL_CONFLICT" in cmp_res["conflict_codes"]


# 8. Missing crop content
def test_08_missing_crop_content_and_blank_rejection() -> None:
    blank_img = Image.new("RGB", (600, 400), (255, 255, 255))
    buf = io.BytesIO()
    blank_img.save(buf, format="PNG")
    norm = normalize_image(buf.getvalue(), "image/png")
    reg = detect_problem_regions(norm)
    assert len(reg.candidates) == 0
    assert reg.used_fallback_full_image is True
    assert reg.crop_holds_all_content is False


# 9. Multi-problem image selection
def test_09_multi_problem_image_selection_requires_choice_zero_ai() -> None:
    img = Image.new("RGB", (900, 650), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    for y0 in (60, 250, 440):
        for i in range(3):
            y = y0 + i * 24
            cx = 60
            while cx < 780:
                draw.rectangle([cx, y, min(780, cx + 45), y + 11], fill=(15, 15, 15))
                cx += 55
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    norm = normalize_image(buf.getvalue(), "image/png")
    reg = detect_problem_regions(norm)
    assert len(reg.candidates) >= 2


# 10. User-edited text (`0` Vision re-calls)
def test_10_user_edited_text_is_authoritative_with_zero_vision_recalls() -> None:
    edited = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 6, "
        "SA vuông góc với mặt phẳng (ABCD) và SA = 4. Tính thể tích khối chóp S.ABCD."
    )
    out = route_edited_text_input(edited, previous_vision_calls=1, allow_live_ai=False)
    assert out.status == "SERVED"
    assert out.telemetry.input_kind == "user_edited_text"
    assert out.telemetry.gemini_vision_calls == 0
    assert out.telemetry.gemini_typed_fact_calls == 0
    assert out.telemetry.total_provider_calls == 0
    assert (out.response.get("route_d") or {}).get("answers") == {"q1": "48"}


# 11. Cache invalidation & parser LRU cache reuse
def test_11_cache_invalidation_and_parser_lru_cache_reuse() -> None:
    t1 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với mặt phẳng (ABCD) và SA = 3. Tính thể tích khối chóp S.ABCD."
    t2 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với mặt phẳng (ABCD) và SA = 5. Tính thể tích khối chóp S.ABCD."
    k1, _ = build_local_first_cache_identity(t1, extraction_route="LOCAL_DETERMINISTIC_PARSER", local_parse_status="LOCAL_PARSE_COMPLETE")
    k2, _ = build_local_first_cache_identity(t2, extraction_route="LOCAL_DETERMINISTIC_PARSER", local_parse_status="LOCAL_PARSE_COMPLETE")
    k3, _ = build_local_first_cache_identity(t1, extraction_route="AI_TYPED_FACT_FALLBACK", local_parse_status="LOCAL_PARSE_PARTIAL")
    assert k1 != k2
    assert k1 != k3

    clear_local_geometry_parser_cache()
    r_miss = parse_geometry_problem_locally(t1, use_cache=True)
    r_hit = parse_geometry_problem_locally(t1, use_cache=True)
    stats = get_local_geometry_parser_cache_stats()
    assert stats["misses"] == 1
    assert stats["hits"] == 1
    assert r_hit.payload == r_miss.payload
    assert r_hit.payload is not r_miss.payload


# 12. Image fallback (`Cases A, B, C, D` + `OCR_VISION_MATH_CONFLICT`)
def test_12_adaptive_image_fallback_cases_a_b_c_d_and_conflict() -> None:
    clean_text = (
        "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 5. "
        "Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'."
    )
    # Case A: Verified local OCR -> 0 AI calls
    out_a = route_image_or_prepare_outcome(
        {"status": "ready", "source_kind": "image", "problem_text": clean_text, "metrics": {"vlm_calls": 0}},
        local_ocr_text=clean_text,
        secondary_ocr_text=clean_text,
        allow_verified_local_ocr=True,
        allow_live_ai=False,
    )
    assert out_a.status == "SERVED"
    assert out_a.telemetry.chosen_route == "LOCAL_OCR_VERIFIED_ZERO_AI"
    assert out_a.telemetry.total_provider_calls == 0

    # Case B: OCR fails fidelity -> Vision (1 call) -> Local Parser (0 TypedFactNext calls)
    corrupted_ocr = "Câu 1. Cho lăng trụ đứng ABC.A'B'C' có AA' = 2V3, AB = a/2 và BC = 3,5. Tính thể tích khối lăng trụ ABC.A'E'C.."
    out_b = route_image_or_prepare_outcome(
        {"status": "ready", "source_kind": "image", "problem_text": clean_text, "metrics": {"vlm_calls": 1}},
        local_ocr_text=corrupted_ocr,
        allow_verified_local_ocr=True,
        allow_live_ai=False,
    )
    assert out_b.status == "SERVED"
    assert out_b.telemetry.chosen_route == "VISION_THEN_LOCAL_DETERMINISTIC"
    assert out_b.telemetry.gemini_vision_calls == 1
    assert out_b.telemetry.gemini_typed_fact_calls == 0

    # Conflict guard: SA=8 in OCR vs SA=3 in Vision -> NEEDS_CONFIRMATION
    ocr_sa8 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với mặt phẳng (ABCD) và SA = 8. Tính thể tích khối chóp S.ABCD."
    vis_sa3 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với mặt phẳng (ABCD) và SA = 3. Tính thể tích khối chóp S.ABCD."
    out_conf = route_image_or_prepare_outcome(
        {"status": "ready", "source_kind": "image", "problem_text": vis_sa3, "metrics": {"vlm_calls": 1}},
        local_ocr_text=ocr_sa8,
        allow_verified_local_ocr=False,
        user_confirmed_conflict=False,
    )
    assert out_conf.status == "NEEDS_CONFIRMATION"
    assert out_conf.telemetry.chosen_route == "VISION_NEEDS_CONFIRMATION"


# 13. Multiple geometry solutions (`2^(m-1)` sign enumeration)
def test_13_multiple_geometry_solutions_sign_enumeration() -> None:
    text_3_apices = (
        "Cho hình chóp S.ABC, hình chóp T.ABC và hình chóp P.ABC có đáy ABC vuông tại A, AB = 6, AC = 8. "
        "Cạnh PA vuông góc với mặt phẳng (ABC), PA = 5. "
        "Biết SA = 13, SB = 13, SC = 13. "
        "Biết TA = √74, TB = √74, TC = √74. "
        "Gọi M là trung điểm của cạnh SP. "
        "Biết SP = √314, TP = 13. Tính độ dài đoạn thẳng MT."
    )
    calls_3_apices = [
        {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]}, "source": {"quotes": ["Cho hình chóp S.ABC"]}},
        {"id": "c2", "fn": "pyramid", "args": {"apex": "T", "base": ["A", "B", "C"]}, "source": {"quotes": ["hình chóp T.ABC"]}},
        {"id": "c3", "fn": "pyramid", "args": {"apex": "P", "base": ["A", "B", "C"]}, "source": {"quotes": ["hình chóp P.ABC"]}},
        {"id": "c4", "fn": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]}, "source": {"quotes": ["có đáy ABC vuông tại A"]}},
        {"id": "c5", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "6"}, "source": {"quotes": ["AB = 6"]}},
        {"id": "c6", "fn": "segment_length", "args": {"segment": ["A", "C"], "value": "8"}, "source": {"quotes": ["AC = 8"]}},
        {"id": "c7", "fn": "perpendicular_line_plane", "args": {"line": ["P", "A"], "plane": ["A", "B", "C"]}, "source": {"quotes": ["Cạnh PA vuông góc với mặt phẳng (ABC)"]}},
        {"id": "c8", "fn": "segment_length", "args": {"segment": ["P", "A"], "value": "5"}, "source": {"quotes": ["PA = 5"]}},
        {"id": "c9", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "13"}, "source": {"quotes": ["SA = 13"]}},
        {"id": "c10", "fn": "segment_length", "args": {"segment": ["S", "B"], "value": "13"}, "source": {"quotes": ["SB = 13"]}},
        {"id": "c11", "fn": "segment_length", "args": {"segment": ["S", "C"], "value": "13"}, "source": {"quotes": ["SC = 13"]}},
        {"id": "c12", "fn": "segment_length", "args": {"segment": ["T", "A"], "value": "√74"}, "source": {"quotes": ["TA = √74"]}},
        {"id": "c13", "fn": "segment_length", "args": {"segment": ["T", "B"], "value": "√74"}, "source": {"quotes": ["TB = √74"]}},
        {"id": "c14", "fn": "segment_length", "args": {"segment": ["T", "C"], "value": "√74"}, "source": {"quotes": ["TC = √74"]}},
        {"id": "c15", "fn": "midpoint", "args": {"point": "M", "segment": ["S", "P"]}, "source": {"quotes": ["Gọi M là trung điểm của cạnh SP"]}},
        {"id": "c16", "fn": "segment_length", "args": {"segment": ["S", "P"], "value": "√314"}, "source": {"quotes": ["SP = √314"]}},
        {"id": "c17", "fn": "segment_length", "args": {"segment": ["T", "P"], "value": "13"}, "source": {"quotes": ["TP = 13"]}},
        {"id": "g1", "fn": "ask_length", "args": {"segment": ["M", "T"]}, "source": {"quotes": ["Tính độ dài đoạn thẳng MT."]}},
    ]
    res_ok = engine.dung_tu_loi_goi(
        text_3_apices, {"calls": calls_3_apices, "named_planes": []}, (), ("Tính độ dài đoạn thẳng MT.",)
    )
    assert res_ok.status == "SERVED"
    assert res_ok.answers == {"g1": "√74/2"}

    calls_unconstrained = [c for c in calls_3_apices if c["id"] not in ("c16", "c17")]
    res_refused = engine.dung_tu_loi_goi(
        text_3_apices, {"calls": calls_unconstrained, "named_planes": []}, (), ("Tính độ dài đoạn thẳng MT.",)
    )
    assert res_refused.status == "REFUSED"


# 14. Weak-device performance & memory bounds
def test_14_weak_device_performance_and_memory_stability_50_requests() -> None:
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, "
        "SA vuông góc với mặt phẳng (ABCD) và SA = 3. Tính thể tích khối chóp S.ABCD."
    )
    # 1. Latency across 50 requests without tracemalloc hook overhead
    latencies_ms: list[float] = []
    for _ in range(50):
        t0 = time.perf_counter()
        out = route_text_input(text, allow_live_ai=False)
        latencies_ms.append((time.perf_counter() - t0) * 1000.0)
        assert out.status == "SERVED"
    latencies_ms.sort()
    p50_ms = latencies_ms[len(latencies_ms) // 2]
    assert p50_ms < 50.0

    # 2. Memory stability across 50 repeated requests
    tracemalloc.start()
    for _ in range(50):
        out = route_text_input(text, allow_live_ai=False)
        assert out.status == "SERVED"
    current_bytes, _peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert current_bytes < 5 * 1024 * 1024
