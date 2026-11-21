# -*- coding: utf-8 -*-
"""Integration tests for `backend/app/ai/adaptive_input_router.py` (`adaptive-input-router/1`, Section X.2).

Verifies:
1. Route `T1`: `Text -> Deterministic Geometry Parser -> Hybrid /4` solves supported Vietnamese 3D geometry problems
   with `0` AI calls (`gemini_vision_calls == 0`, `gemini_typed_fact_calls == 0`), even when `ALLOW_LIVE_AI=0` and
   `GEMINI_API_KEY` is absent.
2. Route `T1` fallback: when a problem has an unparsed clause (`LOCAL_PARSE_PARTIAL` / `LOCAL_PARSE_UNSUPPORTED`),
   `AdaptiveInputRouter` invokes the fallback `Extractor` (`1` AI call) if `allow_live_ai=True`, or fails closed cleanly
   (`LIVE_AI_DISABLED`) when `ALLOW_LIVE_AI=0`.
3. Route `I1`: `Image -> CV Preprocessing & Region Detection -> 1 Vision Call -> Extracted Text -> Deterministic
   Geometry Parser -> Hybrid /4` completes with `1` AI call total (`gemini_vision_calls == 1`,
   `gemini_typed_fact_calls == 0`), and `0` AI calls when CV rejects blank/unreadable images or prompts `needs_selection`.
4. Route `I2`: `evaluate_local_ocr_gate` enforces `LOCAL_OCR_DIAGNOSTIC_ONLY` and rejects cross-engine math-token mismatches.
5. User-edited text re-submission (`route_edited_text_input`): treats user-edited text as authoritative with `0` new
   Vision calls and `0` `TypedFactNext` calls when `LOCAL_PARSE_COMPLETE`.
6. `POST /api/analyze` with `HYBRID_ROUTE_MODE=local-first` serves `Scene3D` + construction continuity with `0` AI calls.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from app import main as M
from app.ai.adaptive_input_router import (
    ADAPTIVE_INPUT_ROUTER_VERSION,
    LOCAL_OCR_PRODUCTION_STATUS,
    build_local_first_cache_identity,
    evaluate_local_ocr_gate,
    route_edited_text_input,
    route_image_or_prepare_outcome,
    route_text_input,
)
from app.ai.local_geometry_parser import (
    LOCAL_GEOMETRY_PARSER_VERSION,
    LOCAL_PARSE_AMBIGUOUS,
    LOCAL_PARSE_COMPLETE,
    LOCAL_PARSE_PARTIAL,
)
from app.ai.typed_fact_next_extraction import ReplayExtractor


def test_t1_text_route_zero_ai_calls_for_complete_and_ambiguous_and_out_of_scope(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    # 1. Supported geometry problem -> 0 AI calls, SERVED
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với mặt phẳng (ABCD), SA = 3. "
        "Tính thể tích khối chóp S.ABCD."
    )
    out = route_text_input(text)
    assert out.status == "SERVED"
    assert out.telemetry.chosen_route == "LOCAL_DETERMINISTIC_HYBRID"
    assert out.telemetry.local_parse_status == LOCAL_PARSE_COMPLETE
    assert out.telemetry.gemini_vision_calls == 0
    assert out.telemetry.gemini_typed_fact_calls == 0
    assert out.telemetry.total_provider_calls == 0
    assert out.response["route_d"]["extraction_mode"] == "LOCAL_DETERMINISTIC_PARSER"
    assert out.response["route_d"]["answer_exact"]["q1"]["coef"] == "16"
    assert out.cache_key is not None

    # 2. Ambiguous phrasing -> 0 AI calls, deterministic AMBIGUOUS_FACT clarification
    ambig_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD), SA = 2. "
        "Tính khoảng cách từ hình chiếu vuông góc của A đến S."
    )
    out_amb = route_text_input(ambig_text)
    assert out_amb.status == "REFUSED"
    assert out_amb.telemetry.chosen_route == "LOCAL_AMBIGUOUS_CLARIFICATION"
    assert out_amb.telemetry.local_parse_status == LOCAL_PARSE_AMBIGUOUS
    assert out_amb.telemetry.total_provider_calls == 0
    assert out_amb.response["envelope"]["reason_code"] == "AMBIGUOUS_FACT"

    # 3. Out-of-scope non-geometry -> 0 AI calls, GATE_OUT_OF_SCOPE
    oos_text = "Giải hệ phương trình tuyến tính bằng phương pháp khử Gauss."
    out_oos = route_text_input(oos_text)
    assert out_oos.status == "REFUSED"
    assert out_oos.telemetry.chosen_route == "LOCAL_OUT_OF_SCOPE_GATE"
    assert out_oos.telemetry.total_provider_calls == 0
    assert out_oos.response["error_code"].upper() == "GATE_OUT_OF_SCOPE"


def test_t1_partial_parse_fails_closed_when_live_ai_disabled_and_falls_back_when_enabled():
    partial_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA = 3. "
        "Biết mặt phẳng (ABCD) vuông góc với đường thẳng SA. "
        "Tính thể tích khối chóp S.ABCD."
    )
    fallback_payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": partial_text,
        "length_unit": "1",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "pyramid",
                "notation": "S.ABCD",
                "quote": "Cho hình chóp S.ABCD",
            }
        ],
        "premises": [
            {
                "kind": "regular_polygon",
                "args": {"vertices": ["A", "B", "C", "D"], "side": "4"},
                "quote": "đáy ABCD là hình vuông cạnh 4",
                "solid_id": "s1",
            },
            {
                "kind": "perpendicular_line_plane",
                "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
                "quote": "mặt phẳng (ABCD) vuông góc với đường thẳng SA",
                "solid_id": "s1",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["S", "A"], "value": "3"},
                "quote": "SA = 3",
                "solid_id": "s1",
            },
        ],
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "s1",
                "quote": "Cho hình chóp S.ABCD",
            }
        ],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "volume",
                "target": {"solid_id": "s1"},
                "solid_id": "s1",
                "quote": "Tính thể tích khối chóp S.ABCD",
            }
        ],
    }

    # 1. With allow_live_ai=False -> fail-closed LIVE_AI_DISABLED, 0 provider calls
    out_disabled = route_text_input(
        partial_text,
        fallback_extractor=ReplayExtractor({partial_text: fallback_payload}),
        allow_live_ai=False,
    )
    assert out_disabled.status == "REFUSED"
    assert out_disabled.telemetry.local_parse_status == LOCAL_PARSE_PARTIAL
    assert out_disabled.telemetry.chosen_route == "FAIL_CLOSED_LIVE_AI_DISABLED"
    assert out_disabled.telemetry.total_provider_calls == 0
    assert out_disabled.response["envelope"]["reason_code"] == "LIVE_AI_DISABLED"

    # 2. With allow_live_ai=True -> falls back to injected extractor (1 call), SERVED
    out_enabled = route_text_input(
        partial_text,
        fallback_extractor=ReplayExtractor({partial_text: fallback_payload}),
        allow_live_ai=True,
    )
    assert out_enabled.status == "SERVED"
    assert out_enabled.telemetry.local_parse_status == LOCAL_PARSE_PARTIAL
    assert out_enabled.telemetry.chosen_route == "AI_TYPED_FACT_FALLBACK"
    assert out_enabled.telemetry.gemini_typed_fact_calls == 1
    assert out_enabled.telemetry.total_provider_calls == 1
    assert out_enabled.response["route_d"]["extraction_mode"] == "AI_TYPED_FACT_FALLBACK"
    assert out_enabled.response["route_d"]["answer_exact"]["q1"]["coef"] == "16"


def test_i1_image_prepare_outcome_and_user_edited_resubmission_provider_call_counts():
    # 1. Image prepare outcome ("ready" after 1 Vision call) -> Local Parser -> Hybrid /4 -> 1 total AI call (0 TypedFactNext calls)
    prep_ready = {
        "status": "ready",
        "source_kind": "image",
        "problem_text": (
            "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 3. "
            "Tính khoảng cách từ A đến mặt phẳng (A'BD)."
        ),
        "provenance": {"extraction_method": "vlm"},
        "metrics": {"vlm_calls": 1, "processing_ms": 420.0},
    }
    out_i1 = route_image_or_prepare_outcome(prep_ready, allow_live_ai=False)
    assert out_i1.status == "SERVED"
    assert out_i1.telemetry.chosen_route == "VISION_THEN_LOCAL_DETERMINISTIC"
    assert out_i1.telemetry.gemini_vision_calls == 1
    assert out_i1.telemetry.gemini_typed_fact_calls == 0
    assert out_i1.telemetry.total_provider_calls == 1
    assert out_i1.response["route_d"]["answer_exact"]["q1"]["coef"] == "√3"

    # 2. Image rejected by local CV (blank/diagram-only) or needs_selection -> 0 Vision calls, 0 TypedFactNext calls
    prep_rejected = {
        "status": "rejected",
        "source_kind": "image",
        "reason_code": "IMAGE_NOT_READABLE",
        "provenance": {},
        "metrics": {"vlm_calls": 0, "processing_ms": 12.5},
    }
    out_rej = route_image_or_prepare_outcome(prep_rejected, allow_live_ai=False)
    assert out_rej.status == "REJECTED"
    assert out_rej.telemetry.chosen_route == "LOCAL_CV_REJECTED_OR_SELECTION"
    assert out_rej.telemetry.total_provider_calls == 0

    # 3. User edits the extracted text (e.g. changes side 3 -> 6) and clicks "Dựng hình" -> 0 new Vision calls, 0 TypedFactNext calls
    edited_text = (
        "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 6. "
        "Tính khoảng cách từ A đến mặt phẳng (A'BD)."
    )
    out_edit = route_edited_text_input(edited_text, previous_vision_calls=1, allow_live_ai=False)
    assert out_edit.status == "SERVED"
    assert out_edit.telemetry.input_kind == "user_edited_text"
    assert out_edit.telemetry.gemini_vision_calls == 0
    assert out_edit.telemetry.gemini_typed_fact_calls == 0
    assert out_edit.telemetry.total_provider_calls == 0
    assert out_edit.telemetry.cache_key_metadata["authoritative_source"] == "user_edited_text"
    assert out_edit.telemetry.cache_key_metadata["prior_session_vision_calls_not_repeated"] == 1
    assert out_edit.response["route_d"]["answer_exact"]["q1"]["coef"] == "2√3"


def test_i2_local_ocr_gate_remains_diagnostic_only_and_detects_symbol_mismatch():
    clean_txt = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA ⊥ (ABCD), SA = 2. Tính thể tích khối chóp S.ABCD."
    corrupted_txt = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA (ABCD), SA = 2. Tính thể tích khối chóp S.ABCD."

    gate_mismatch = evaluate_local_ocr_gate(
        corrupted_txt,
        clean_txt,
        reference_math_tokens=["S.ABCD", "⊥", "= 2"],
    )
    assert gate_mismatch["production_status"] == LOCAL_OCR_PRODUCTION_STATUS
    assert gate_mismatch["gate_passed"] is False
    assert gate_mismatch["cross_engine_math_tokens_agree"] is False

    gate_agree = evaluate_local_ocr_gate(
        clean_txt,
        clean_txt,
        reference_math_tokens=["S.ABCD", "⊥", "= 2"],
    )
    assert gate_agree["production_status"] == LOCAL_OCR_PRODUCTION_STATUS
    assert gate_agree["gate_passed"] is True
    assert gate_agree["local_parser_complete"] is True


def test_api_analyze_local_first_mode_serves_scene3d_with_zero_ai_calls(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-first")
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    text = (
        "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4 và AA' = 5. "
        "Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'."
    )
    from tests.route_client import sign_in

    with TestClient(M.app) as client:
        sign_in(client)
        resp = client.post("/api/analyze", json={"input": {"type": "text", "content": text}})

    assert resp.status_code == 200
    body = resp.json()
    assert body["route_d"]["status"] == "SERVED"
    assert body["route_d"]["extraction_mode"] == "LOCAL_DETERMINISTIC_PARSER"
    assert body["route_d"]["local_parser_version"] == LOCAL_GEOMETRY_PARSER_VERSION
    assert body["route_d"]["adaptive_router_version"] == ADAPTIVE_INPUT_ROUTER_VERSION
    assert body["route_d"]["adaptive_telemetry"]["total_provider_calls"] == 0
    assert body["route_d"]["answer_exact"]["q1"]["coef"] == "60"
    assert body["envelope"]["status"] == "ok"
    assert len(body["envelope"]["scene3d"]["formation"]["steps"]) >= 2

    # Cache identity includes parser & router versions
    k1, meta1 = build_local_first_cache_identity(
        text,
        extraction_route="LOCAL_DETERMINISTIC_PARSER",
        local_parse_status=LOCAL_PARSE_COMPLETE,
    )
    k2, _ = build_local_first_cache_identity(
        text,
        extraction_route="AI_TYPED_FACT_FALLBACK",
        model="gemini-2.5-flash",
        local_parse_status=LOCAL_PARSE_PARTIAL,
    )
    assert k1 != k2
    assert meta1["parser_version"] == LOCAL_GEOMETRY_PARSER_VERSION
    assert meta1["router_version"] == ADAPTIVE_INPUT_ROUTER_VERSION
