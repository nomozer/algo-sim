# -*- coding: utf-8 -*-
"""Stage P0 — Orthogonal Failure Taxonomy, Exact Determinacy Audit, and API 503 Contract Tests.

Verifies the 6 canonical states across the 5 orthogonal dimensions without guessing mathematical determinacy:
1. SEMANTIC_COMPLETENESS -> SEMANTIC_INPUT_INCOMPLETE
2. SEMANTIC_COMPLETENESS -> SEMANTIC_ENTITY_UNRESOLVED
3. MATHEMATICAL_DETERMINACY -> MATHEMATICALLY_UNDERDETERMINED (machine-certified non-uniqueness only)
4. IMPLEMENTATION_CAPABILITY -> CAPABILITY_UNSUPPORTED (known capability gap OR unproved determinacy / deduction gap)
5. CONTRADICTORY_CONSTRAINTS -> CONTRADICTORY_CONSTRAINTS (source-verified impossibility)
6. INFRASTRUCTURE_AVAILABILITY -> INFRASTRUCTURE_UNAVAILABLE (HTTP 502/503/504 operational unavailability)
"""
from __future__ import annotations

import re
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient

from app import main as M
from app.ai.adaptive_input_router import route_text_input
from app.ai.hybrid_preview import classify_refusal
from app.learner_messages import learner_reason
from app.simulation.geometry_functions.determinacy_audit import (
    DETERMINACY_AUDIT_VERSION,
    audit_determinacy,
    audit_determinacy_from_typed_facts,
)
from tests.route_client import sign_in

_TECH_TOKEN_RE = re.compile(
    r"[a-z]+_[a-z_]+|[A-Z]{2,}_[A-Z_]+|\$\.|\{|\}|Traceback|Error\b|__|ALLOW_LIVE_AI|GEMINI_API_KEY"
)
_ADD_MISSING_DATA_CUES = (
    "chưa cho đủ dữ kiện",
    "chưa đủ dữ kiện",
    "bổ sung dữ kiện",
    "bổ sung số đo còn thiếu",
    "thiếu dữ kiện",
)
_BLAME_PROBLEM_WRONG_CUES = (
    "đề bài sai",
    "dữ kiện mâu thuẫn",
    "mâu thuẫn nhau",
)


@pytest.fixture
def analyze_client(monkeypatch):
    with TestClient(M.app) as client:
        sign_in(client)
        yield client


# ── 1. Deductive / constructive capability gaps MUST NOT be misclassified as MATHEMATICALLY_UNDERDETERMINED ─────────

@pytest.mark.parametrize(
    "label,text",
    [
        (
            "right_isosceles_hypotenuse_pyramid",
            "Câu 33: Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân ở B, cạnh AC = 2a. "
            "Cạnh SA vuông góc với mặt đáy (ABC), tam giác SAB cân. Thể tích khối chóp S.ABC theo a bằng",
        ),
        (
            "rhombus_angle_and_diagonal_line_plane_angle_prism",
            "Câu 43. Cho khối lăng trụ đứng ABCDA'B'C'D' có đáy ABCD là hình thoi, ∠BAD = 60°, "
            "cạnh bên AA' = 2a và AC' hợp với đáy góc 30°. Thể tích khối lăng trụ đã cho bằng",
        ),
        (
            "angle_coupled_square_base_before_trig_deduction",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông, SA vuông góc với mặt phẳng đáy, SA = a, "
            "góc giữa SB và mặt phẳng (ABCD) bằng 60°. Tính thể tích khối chóp S.ABCD.",
        ),
    ],
)
def test_uniquely_determined_deduction_gaps_never_classified_as_underdetermined(label, text):
    """In P0 (or whenever a constructive deduction rule is absent), unconsumed angle/metric constraints prevent
    certifying two diverging Euclidean models. If not yet SERVED, the refusal MUST classify as CAPABILITY_UNSUPPORTED
    with determinacy_status='UNPROVED_DUE_TO_CAPABILITY_GAP' — never MATHEMATICALLY_UNDERDETERMINED."""
    out = route_text_input(text, allow_live_ai=False)
    rd = out.response["route_d"]
    if rd["status"] == "SERVED":
        # Forward-compatible once Stage P1 trig construction lands and serves the exact answer.
        assert rd.get("answer_exact"), label
        return

    env = out.response["envelope"]
    diag = rd["local_diagnostics"]
    det = rd.get("determinacy_audit") or {}

    assert diag["failure_dimension"] == "IMPLEMENTATION_CAPABILITY", (label, diag)
    assert diag["taxonomy_class"] == "CAPABILITY_UNSUPPORTED", (label, diag)
    assert diag["determinacy_status"] == "UNPROVED_DUE_TO_CAPABILITY_GAP", (label, diag)
    assert diag["root_cause"] != "INSUFFICIENT_CONSTRAINTS", (label, diag)
    assert diag["learner_summary"]["rewrite_may_help"] is False
    assert det.get("schema_version") == DETERMINACY_AUDIT_VERSION
    assert det.get("status") == "UNPROVED_DUE_TO_CAPABILITY_GAP"
    assert (
        len(det.get("unconsumed_constraint_ids") or []) >= 1
        or det.get("witness_kind") == "CONSTRUCTIBLE_WHEN_DIMENSION_COUPLED_BY_OTHER_PREMISES"
    )

    # Envelope 6-key contract + capability_gap + UNKNOWN cause + honest Vietnamese copy
    assert set(env.keys()) == {
        "status", "reason_code", "reason", "learner_reason", "failure_category", "refusal_cause"
    }
    assert env["failure_category"] == "capability_gap", (label, env)
    assert env["refusal_cause"] == "UNKNOWN", (label, env)
    for msg in (env["learner_reason"], diag["learner_summary"]["message"]):
        assert _TECH_TOKEN_RE.search(msg) is None, msg
        assert not any(cue in msg.lower() for cue in _ADD_MISSING_DATA_CUES), msg
        assert not any(cue in msg.lower() for cue in _BLAME_PROBLEM_WRONG_CUES), msg


# ── 2. True mathematically underdetermined problems MUST carry machine-verified witnesses ───────────────────────────

@pytest.mark.parametrize(
    "label,text,expected_witness",
    [
        (
            "missing_all_dimensions_volume",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông, SA vuông góc với mặt phẳng đáy. "
            "Tính thể tích khối chóp S.ABCD.",
            {"TWO_VALID_REALIZATIONS_DIVERGE", "HOMOTHETY_SCALE_DEGREE_POSITIVE"},
        ),
        (
            "angle_only_without_scale_volume",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông, SA vuông góc với mặt phẳng đáy, "
            "góc giữa SB và mặt phẳng (ABCD) bằng 45°. Tính thể tích khối chóp S.ABCD.",
            {"TWO_VALID_REALIZATIONS_DIVERGE", "HOMOTHETY_SCALE_DEGREE_POSITIVE"},
        ),
        (
            "uncoupled_square_base_and_apex_height",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông, SA vuông góc với mặt phẳng đáy và SA = 2a. "
            "Tính thể tích khối chóp S.ABCD.",
            {"TWO_VALID_REALIZATIONS_DIVERGE"},
        ),
        (
            "missing_rectangle_second_side",
            "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật có AB = a, SA vuông góc với mặt phẳng đáy và SA = a. "
            "Tính thể tích khối chóp S.ABCD.",
            {"TWO_VALID_REALIZATIONS_DIVERGE"},
        ),
        (
            "missing_height_with_fixed_square_base",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy. "
            "Tính thể tích khối chóp S.ABCD.",
            {"TWO_VALID_REALIZATIONS_DIVERGE"},
        ),
        (
            "scale_free_rectangle_aspect_ratio_open_angle_goal",
            "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, SA vuông góc với mặt phẳng đáy và SA = AB. "
            "Tính góc giữa đường thẳng SC và mặt phẳng (ABCD).",
            {"TWO_VALID_REALIZATIONS_DIVERGE"},
        ),
        (
            "plane_pencil_non_unique_section",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
            "Mặt phẳng (P) chứa AB và song song với CD. Xác định thiết diện của hình chóp cắt bởi mặt phẳng (P).",
            {"EXPLICIT_FREE_LOCUS_ZERO_UNCONSUMED_FACTS"},
        ),
    ],
)
def test_true_underdetermined_problems_certified_by_determinacy_audit(label, text, expected_witness):
    out = route_text_input(text, allow_live_ai=False)
    rd = out.response["route_d"]
    env = out.response["envelope"]
    diag = rd["local_diagnostics"]
    det = rd.get("determinacy_audit") or {}

    assert rd["status"] == "REFUSED", label
    assert diag["failure_dimension"] == "MATHEMATICAL_DETERMINACY", (label, diag)
    assert diag["taxonomy_class"] == "MATHEMATICALLY_UNDERDETERMINED", (label, diag)
    assert diag["determinacy_status"] == "PROVED_UNDERDETERMINED", (label, diag)
    assert diag["root_cause"] == "INSUFFICIENT_CONSTRAINTS", (label, diag)
    assert det.get("status") == "PROVED_UNDERDETERMINED", (label, det)
    assert det.get("witness_kind") in expected_witness, (label, det)
    if det.get("witness_kind") == "TWO_VALID_REALIZATIONS_DIVERGE":
        models = det.get("counterexample_models") or []
        assert len(models) == 2 and models[0]["answers"] != models[1]["answers"], (label, models)

    assert env["failure_category"] == "insufficient_specification", (label, env)
    assert env["refusal_cause"] == "SOURCE", (label, env)
    assert _TECH_TOKEN_RE.search(env["learner_reason"]) is None


# ── 3. All 6 orthogonal states separated cleanly ────────────────────────────────────────────────────────────────────

def test_semantic_input_incomplete_and_unread_value_subphrase():
    # Unread relation ("chu vi") -> SEMANTIC_INPUT_INCOMPLETE
    text_unread = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với đáy, chu vi tam giác SAB bằng 5a. "
        "Tính thể tích khối chóp S.ABCD."
    )
    out = route_text_input(text_unread, allow_live_ai=False)
    diag = out.response["route_d"]["local_diagnostics"]
    assert diag["failure_dimension"] == "SEMANTIC_COMPLETENESS"
    assert diag["taxonomy_class"] == "SEMANTIC_INPUT_INCOMPLETE"
    assert diag["determinacy_status"] == "NOT_EVALUATED_SEMANTIC_INCOMPLETE"
    assert "chu vi tam giác SAB bằng 5a" in diag["learner_summary"]["unread_excerpts"][0]

    # UNREAD_VALUE subphrase slicing: quotes only the unread subphrase, not the entire exam stem
    text_val = (
        "Câu 39: Cho hình chóp tứ giác đều S.ABCD có độ dài cạnh bên bằng 3 và chu vi đáy bằng 8 "
        "(tham khảo hình bên dưới). Tính thể tích khối chóp S.ABCD."
    )
    out_val = route_text_input(text_val, allow_live_ai=False)
    diag_val = out_val.response["route_d"]["local_diagnostics"]
    assert diag_val["taxonomy_class"] == "SEMANTIC_INPUT_INCOMPLETE"
    ex = diag_val["learner_summary"]["unread_excerpts"][0]
    assert "chu vi đáy bằng 8" in ex
    assert "Câu 39" not in ex


@pytest.mark.parametrize(
    "text",
    [
        # Unresolved plane reference (Q)
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
        "Xác định thiết diện của hình chóp cắt bởi mặt phẳng (Q).",
        # Unrecognized point definition entity
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
        "Gọi M là tâm đường tròn Euler của tam giác SAB. Tính khoảng cách từ M đến (ABCD).",
        # Unnamed described point standing as premise operand
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, hình chiếu vuông góc của S lên (ABC) "
        "trùng với trọng tâm của tam giác ABC, SA = 2a. Tính thể tích khối chóp S.ABC.",
    ],
)
def test_semantic_entity_unresolved_state(text):
    out = route_text_input(text, allow_live_ai=False)
    diag = out.response["route_d"]["local_diagnostics"]
    assert diag["failure_dimension"] == "SEMANTIC_COMPLETENESS", diag
    assert diag["taxonomy_class"] == "SEMANTIC_ENTITY_UNRESOLVED", diag
    assert diag["determinacy_status"] == "NOT_EVALUATED_SEMANTIC_INCOMPLETE", diag


@pytest.mark.parametrize(
    "label,text,expected_det_status",
    [
        (
            "irrational_gram_chart_vmmu_r266_class",
            "Câu 12. Cho khối chóp S.ABC có SA vuông góc với đáy, SA = 3, AB = 3, CB = 4 và ∠ABC = 30°. "
            "Thể tích khối chóp đã cho bằng",
            "PROVED_DETERMINATE_EXACT_DOMAIN_EXCEEDED",
        ),
        (
            "unsupported_reflection_point_construction",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với đáy và SA = a. "
            "Gọi M là điểm đối xứng của A qua C. Tính khoảng cách từ M đến mặt phẳng (SBD).",
            "UNPROVED_DUE_TO_CAPABILITY_GAP",
        ),
        (
            "free_point_on_segment_without_invariance_proof",
            "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với đáy và SA = a. "
            "Gọi I là một điểm thuộc cạnh BC. Tính khoảng cách từ I đến mặt phẳng (SAB).",
            "UNPROVED_DUE_TO_CAPABILITY_GAP",
        ),
        (
            "invariant_distance_with_open_rectangle_side",
            "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật có AB = a, SA vuông góc với mặt phẳng đáy và SA = a. "
            "Tính khoảng cách từ B đến mặt phẳng (SAD).",
            "UNPROVED_DUE_TO_CAPABILITY_GAP",
        ),
    ],
)
def test_capability_unsupported_states_and_honest_determinacy_scope(label, text, expected_det_status):
    out = route_text_input(text, allow_live_ai=False)
    diag = out.response["route_d"]["local_diagnostics"]
    assert diag["failure_dimension"] == "IMPLEMENTATION_CAPABILITY", (label, diag)
    assert diag["taxonomy_class"] == "CAPABILITY_UNSUPPORTED", (label, diag)
    assert diag["determinacy_status"] == expected_det_status, (label, diag)
    assert diag["learner_summary"]["rewrite_may_help"] is False
    msg = diag["learner_summary"]["message"]
    assert not any(cue in msg.lower() for cue in _BLAME_PROBLEM_WRONG_CUES), msg


def test_contradictory_constraints_state_and_preview_isolation():
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, AB = 2a, "
        "SA vuông góc với mặt phẳng đáy và SA = a. Tính thể tích khối chóp S.ABCD."
    )
    out = route_text_input(text, allow_live_ai=False)
    env = out.response["envelope"]
    diag = out.response["route_d"]["local_diagnostics"]
    assert diag["failure_dimension"] == "CONTRADICTORY_CONSTRAINTS"
    assert diag["taxonomy_class"] == "CONTRADICTORY_CONSTRAINTS"
    assert diag["determinacy_status"] == "NO_VALID_REALIZATION"
    assert diag["root_cause"] == "SOURCE_CONFLICT"
    assert env["failure_category"] == "geometry_generation_failed"
    assert env["refusal_cause"] == "SOURCE"
    assert _TECH_TOKEN_RE.search(env["learner_reason"]) is None

    # Preview / non-local-complete classify_refusal MUST keep refusal_cause == "UNKNOWN" for H09/H10 compatibility
    assert classify_refusal("INCONSISTENT_FACTS", problem_text=text).refusal_cause == "UNKNOWN"
    assert classify_refusal("MISSING_DIMENSION", problem_text=text).refusal_cause == "UNKNOWN"


# ── 4. Phase 2 API 503 Contract: MISSING_API_KEY vs LIVE_AI_DISABLED & HYBRID_LOCAL_FIRST=1 ─────────────────────────

def test_local_first_partial_parse_with_allow_live_ai_1_and_no_key_reports_missing_api_key(analyze_client, monkeypatch):
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-first")
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    partial_text = (
        "Cho hình chóp S.ABC có SA vuông góc với đáy, tam giác ABC đều cạnh a, chu vi tam giác SAB bằng 5a. "
        "Tính thể tích khối chóp S.ABC."
    )
    res = analyze_client.post("/api/analyze", json={"input": {"type": "text", "content": partial_text}})
    assert res.status_code == 503
    body = res.json()
    assert body["reason_code"] == "MISSING_API_KEY"
    assert body["failure_kind"] == "INFRASTRUCTURE_FAILURE"
    assert body["taxonomy_class"] == "INFRASTRUCTURE_UNAVAILABLE"
    lu = body["local_understanding"]
    assert lu["root_cause"] == "UNRECOGNIZED_RELATION"
    assert lu["taxonomy_class"] == "SEMANTIC_INPUT_INCOMPLETE"
    assert "chu vi tam giác SAB bằng 5a" in body["error"]
    assert _TECH_TOKEN_RE.search(body["error"]) is None


def test_live_mode_with_hybrid_local_first_1_serves_local_complete_when_allow_live_ai_0(analyze_client, monkeypatch):
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "live")
    monkeypatch.setenv("HYBRID_LOCAL_FIRST", "1")
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    complete_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
        "Tính thể tích khối chóp S.ABCD."
    )
    res = analyze_client.post("/api/analyze", json={"input": {"type": "text", "content": complete_text}})
    assert res.status_code == 200
    body = res.json()
    assert body["route_d"]["status"] == "SERVED"
    assert body["envelope"]["status"] == "ok"


def test_learner_messages_capability_gap_mentions_spatial_geometry_not_legacy_informatics():
    msg = learner_reason({"status": "unsupported", "failure_category": "capability_gap", "reason": "tech"})
    assert "từ chối trung thực" in msg
    assert "hình học không gian" in msg
    assert "số nhị phân" not in msg and "cổng logic" not in msg
    assert _TECH_TOKEN_RE.search(msg) is None


# ── 5. Pure construction (`ask_calls == []`) & standalone `curved_solid` goal-dependence regressions ─────────────────

@pytest.mark.parametrize(
    "label,text",
    [
        (
            "midpoint_cross_section_open_height",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a và SA vuông góc với mặt phẳng (ABCD). "
            "Gọi M, N, P lần lượt là trung điểm của SA, SB, SC. "
            "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MNP).",
        ),
        (
            "affine_intersection_line_open_height",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a và SA vuông góc với mặt phẳng (ABCD). "
            "Tìm giao tuyến của hai mặt phẳng (SAC) và (SBD).",
        ),
    ],
)
def test_pure_construction_cross_section_and_intersection_line_invariance_not_marked_underdetermined(label, text):
    """When `ask_calls == []` and a cross-section or intersection-line goal is affine-invariant across `SA > 0`,
    `determinacy_audit` must NEVER crash (`ROUTE_INTERNAL_ERROR`) and must NEVER falsely claim `PROVED_UNDERDETERMINED`
    merely because solid vertex distances vary with `SA`."""
    out = route_text_input(text, allow_live_ai=False)
    rd = out.response["route_d"]
    env = out.response["envelope"]
    assert env["reason_code"] != "ROUTE_INTERNAL_ERROR", (label, env)
    if rd["status"] == "SERVED":
        return

    diag = rd["local_diagnostics"]
    det = rd.get("determinacy_audit") or {}
    assert det.get("status") == "UNPROVED_DUE_TO_CAPABILITY_GAP", (label, det)
    assert det.get("witness_kind") == "CONSTANT_ACROSS_SAMPLED_REALIZATIONS_UNPROVED_INVARIANCE", (label, det)
    assert diag["failure_dimension"] == "IMPLEMENTATION_CAPABILITY", (label, diag)
    assert diag["taxonomy_class"] == "CAPABILITY_UNSUPPORTED", (label, diag)
    assert diag["determinacy_status"] == "UNPROVED_DUE_TO_CAPABILITY_GAP", (label, diag)
    assert diag["root_cause"] == "SHAPE_FREEDOM_UNCERTIFIED", (label, diag)
    assert env["failure_category"] == "capability_gap", (label, env)
    assert env["refusal_cause"] == "UNKNOWN", (label, env)
    for msg in (env["learner_reason"], diag["learner_summary"]["message"]):
        assert _TECH_TOKEN_RE.search(msg) is None, msg
        assert not any(cue in msg.lower() for cue in _ADD_MISSING_DATA_CUES), msg
        assert not any(cue in msg.lower() for cue in _BLAME_PROBLEM_WRONG_CUES), msg


def test_pure_solid_construction_metric_g_diverges_without_attribute_error():
    """When `ask_calls == []`, `section_calls == []`, and `intersection_line_ids == ()`, `_answer_signature` compares
    the exact squared-distance spectrum via `Metric.g` (`G.g`) across `h2=1` vs `h2=4`."""
    problem_text = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a và SA vuông góc với mặt phẳng (ABCD)."
    plan = {
        "calls": [
            {
                "id": "s1",
                "fn": "pyramid",
                "args": {"apex": "S", "base": ["A", "B", "C", "D"]},
                "source": {"quotes": ["Cho hình chóp S.ABCD"]},
            },
            {
                "id": "p1",
                "fn": "regular_polygon",
                "args": {"vertices": ["A", "B", "C", "D"], "side": "a"},
                "source": {"quotes": ["đáy ABCD là hình vuông cạnh a"]},
            },
            {
                "id": "p2",
                "fn": "perpendicular_line_plane",
                "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
                "source": {"quotes": ["SA vuông góc với mặt phẳng (ABCD)"]},
            },
        ]
    }
    det = audit_determinacy(
        problem_text,
        plan,
        (),
        (),
        SimpleNamespace(code="MISSING_DIMENSION", details={"consumed_call_ids": ["s1", "p1", "p2"]}),
    )
    assert det["status"] == "PROVED_UNDERDETERMINED"
    assert det["witness_kind"] == "TWO_VALID_REALIZATIONS_DIVERGE"
    models = det["counterexample_models"]
    assert len(models) == 2
    assert models[0]["construction_signature"] != models[1]["construction_signature"]


def test_standalone_curved_solid_shortcut_respects_goal_dependence():
    """Standalone `curved_solid` missing `height` with `radius='2a'` supplied:
    - `ask_radius` (already determined by supplied radius) -> `UNPROVED_DUE_TO_CAPABILITY_GAP`
    - `ask_curved_volume_ratio` (homogeneity degree 0) -> `UNPROVED_DUE_TO_CAPABILITY_GAP`
    - `ask_curved_volume` (degree 3, depends on missing height) -> `PROVED_UNDERDETERMINED`
    - `ask_calls == []` (pure solid construction missing height) -> `PROVED_UNDERDETERMINED`
    """
    base_call = {
        "id": "c0",
        "fn": "curved_solid",
        "args": {"kind": "cylinder", "solid": "T", "radius": "2a"},
        "source": {"quotes": ["Cho hình trụ T có bán kính đáy bằng 2a"]},
    }
    refused = SimpleNamespace(code="MISSING_DIMENSION", details={})

    # 1. ask_radius when radius is already supplied
    det_rad = audit_determinacy(
        "Cho hình trụ T có bán kính đáy bằng 2a. Tính bán kính đáy.",
        {
            "calls": [
                base_call,
                {"id": "c1", "fn": "ask_radius", "args": {"solid": "T"}, "source": {"quotes": ["Tính bán kính đáy"]}},
            ]
        },
        (),
        ("Tính bán kính đáy",),
        refused,
    )
    assert det_rad["status"] == "UNPROVED_DUE_TO_CAPABILITY_GAP"

    # 2. ask_curved_volume_ratio (degree 0)
    det_ratio = audit_determinacy(
        "Cho hình nón N có bán kính đáy bằng 2a. Tính tỉ số thể tích của hai khối nón N1 và N.",
        {
            "calls": [
                {
                    "id": "c0",
                    "fn": "curved_solid",
                    "args": {"kind": "cone", "solid": "N", "radius": "2a"},
                    "source": {"quotes": ["Cho hình nón N có bán kính đáy bằng 2a"]},
                },
                {
                    "id": "c1",
                    "fn": "ask_curved_volume_ratio",
                    "args": {"first": "N1", "second": "N"},
                    "source": {"quotes": ["Tính tỉ số thể tích của hai khối nón N1 và N"]},
                },
            ]
        },
        (),
        ("Tính tỉ số thể tích của hai khối nón N1 và N",),
        refused,
    )
    assert det_ratio["status"] == "UNPROVED_DUE_TO_CAPABILITY_GAP"

    # 3. ask_curved_volume (degree 3, genuinely depends on missing height)
    det_vol = audit_determinacy(
        "Cho hình trụ T có bán kính đáy bằng 2a. Tính thể tích hình trụ.",
        {
            "calls": [
                base_call,
                {
                    "id": "c1",
                    "fn": "ask_curved_volume",
                    "args": {"solid": "T"},
                    "source": {"quotes": ["Tính thể tích hình trụ"]},
                },
            ]
        },
        (),
        ("Tính thể tích hình trụ",),
        refused,
    )
    assert det_vol["status"] == "PROVED_UNDERDETERMINED"
    assert det_vol["witness_kind"] == "EXPLICIT_FREE_LOCUS_ZERO_UNCONSUMED_FACTS"

    # 4. Pure curved solid construction (`ask_calls == []`) missing height
    det_no_ask = audit_determinacy(
        "Cho hình trụ T có bán kính đáy bằng 2a.",
        {"calls": [base_call]},
        (),
        (),
        refused,
    )
    assert det_no_ask["status"] == "PROVED_UNDERDETERMINED"
    assert det_no_ask["witness_kind"] == "EXPLICIT_FREE_LOCUS_ZERO_UNCONSUMED_FACTS"
