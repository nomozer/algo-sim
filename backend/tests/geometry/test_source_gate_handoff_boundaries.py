# -*- coding: utf-8 -*-
"""P5 Reproducible Source Gate Ownership Boundary & Security Tests (no edits to registry.py)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.ai.hybrid_offline import ReplayExtractor, hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.local_slm_extractor import build_compact_clause_context, validate_and_lower_compact_clause  # noqa: E402
from app.ai.slm_verified_normalizer import normalize_for_slm_grounding  # noqa: E402


def _run_gold_typed_facts(
    problem_text: str,
    *,
    solid_type: str,
    notation: str,
    solid_quote: str,
    premises: list[dict],
    goals: list[dict],
) -> dict:
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": problem_text,
        "length_unit": "a",
        "solids": [{"solid_id": "s1", "solid_type": solid_type, "notation": notation, "quote": solid_quote}],
        "premises": premises,
        "derived_sections": [],
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": solid_quote}],
        "math_goals": goals,
    }
    pol = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
    ho = run_hybrid_offline(problem_text, ReplayExtractor({problem_text: payload}), policy=pol)
    return ho.response.get("route_d") or {}


# ── 1. Current Blocked Native Source Gate Boundaries (without v2 normalizer) ──

def test_native_source_gate_blocks_unnormalized_handoff_forms_read_only() -> None:
    """Pins exact native Source Gate behavior on un-normalized handoff forms without mutating registry.py."""
    # Item 1: _C_VAI lacks `mọi cạnh bên dài` without VN05_MOI_CANH_BEN
    t1 = "Cho hình chóp tam giác đều E.MNP, mặt đáy có cạnh bằng 2a và mọi cạnh bên dài 2a√2. Tính thể tích khối chóp E.MNP."
    rd1 = _run_gold_typed_facts(
        t1,
        solid_type="pyramid",
        notation="E.MNP",
        solid_quote="Cho hình chóp tam giác đều E.MNP",
        premises=[
            {"kind": "regular_polygon", "args": {"vertices": ["M", "N", "P"], "side": "2a"}, "quote": "mặt đáy có cạnh bằng 2a", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["E", "M"], "value": "2a√2"}, "quote": "mọi cạnh bên dài 2a√2", "solid_id": "s1"},
        ],
        goals=[{"goal_id": "q1", "kind": "measurement", "goal_type": "volume", "target": {"solid_id": "s1"}, "solid_id": "s1", "quote": "Tính thể tích khối chóp E.MNP"}],
    )
    assert rd1.get("status") == "REFUSED"

    # Item 2: _C_MAT rejects `"nằm vuông góc với"` without VN05_NAM_VUONG_GOC_FACE
    t2 = "Cho khối chóp M.ABCD có đáy ABCD là hình vuông cạnh 2a. Mặt bên MAB là tam giác đều nằm vuông góc với mặt đáy (ABCD). Tính thể tích M.ABCD."
    rd2 = _run_gold_typed_facts(
        t2,
        solid_type="pyramid",
        notation="M.ABCD",
        solid_quote="Cho khối chóp M.ABCD",
        premises=[
            {"kind": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "2a"}, "quote": "đáy ABCD là hình vuông cạnh 2a", "solid_id": "s1"},
            {"kind": "regular_polygon", "args": {"vertices": ["M", "A", "B"], "side": ""}, "quote": "Mặt bên MAB là tam giác đều", "solid_id": "s1"},
            {"kind": "face_perpendicular_base", "args": {"face": ["M", "A", "B"], "base": ["A", "B", "C", "D"]}, "quote": "Mặt bên MAB là tam giác đều nằm vuông góc với mặt đáy (ABCD)", "solid_id": "s1"},
        ],
        goals=[{"goal_id": "q1", "kind": "measurement", "goal_type": "volume", "target": {"solid_id": "s1"}, "solid_id": "s1", "quote": "Tính thể tích M.ABCD"}],
    )
    assert rd2.get("status") == "REFUSED"

    # Item 3: Compound projection+midpoint sentence without VN05_PROJ_MIDPOINT
    t3 = "Cho hình chóp H.KLM có đáy KLM là tam giác đều cạnh 2a. Hình chiếu vuông góc của H lên mặt đáy (KLM) là trung điểm I của KL, HK=2a. Tính thể tích khối chóp H.KLM."
    rd3 = _run_gold_typed_facts(
        t3,
        solid_type="pyramid",
        notation="H.KLM",
        solid_quote="Cho hình chóp H.KLM",
        premises=[
            {"kind": "regular_polygon", "args": {"vertices": ["K", "L", "M"], "side": "2a"}, "quote": "đáy KLM là tam giác đều cạnh 2a", "solid_id": "s1"},
            {"kind": "midpoint", "args": {"point": "I", "segment": ["K", "L"]}, "quote": "trung điểm I của KL", "solid_id": "s1"},
            {"kind": "orthogonal_projection", "args": {"point": "H", "image": "I", "plane": ["K", "L", "M"]}, "quote": "Hình chiếu vuông góc của H lên mặt đáy (KLM) là trung điểm I của KL", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["H", "K"], "value": "2a"}, "quote": "HK=2a", "solid_id": "s1"},
        ],
        goals=[{"goal_id": "q1", "kind": "measurement", "goal_type": "volume", "target": {"solid_id": "s1"}, "solid_id": "s1", "quote": "Tính thể tích khối chóp H.KLM"}],
    )
    assert rd3.get("status") == "REFUSED"

    # Verified normalizer v2 bridges these cleanly without weakening Source Gate
    for txt in (t1, t2, t3):
        nr = normalize_for_slm_grounding(txt, normalizer_version="v2")
        assert nr.changed
        assert all(s.validation_result == "VALIDATED_MEANING_PRESERVING" for s in nr.steps)


def test_reordered_rect_base_and_conversational_prefix_pass_gold_source_gate() -> None:
    """Validates v7h_p8_01..05 Gold compact_clause passes Source Gate -> Kernel SERVED even with conversational prefix."""
    t = "Thưa thầy, nhờ giải bài: Cho khối chóp H.UVWX có cạnh HU vuông góc mặt đáy (UVWX) và HU=3a. Biết UVWX là hình chữ nhật với UV=a√2, VW=2a. Lấy T là trung điểm WX. Hãy tìm khoảng cách từ điểm T đến (HVW)."
    nr = normalize_for_slm_grounding(t, normalizer_version="v2")
    ctx = build_compact_clause_context(nr.canonical_text)
    gold = {
        "s": [0, "pyr", "H.UVWX", 0],
        "r": [
            {"c": 0, "p": "perp_lp", "a": "HU", "b": "UVWX"},
            {"c": 0, "p": "len", "a": "HU", "q": "3a"},
            {"c": 1, "p": "rect", "a": "UVWX"},
            {"c": 1, "p": "len", "a": "UV", "q": "a√2"},
            {"c": 1, "p": "len", "a": "VW", "q": "2a"},
            {"c": 2, "p": "mid", "pt": "T", "a": "WX"},
        ],
        "g": [{"c": 3, "t": "dist_pt_plane", "a": "T", "b": "HVW"}],
        "u": [],
    }
    payload, diag = validate_and_lower_compact_clause(ctx=ctx, raw_slm_json=gold, closure_mode="v7")
    assert payload is not None and diag["grounding_status"] == "GROUNDED_AND_LOWERED"
    pol = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
    ho = run_hybrid_offline(nr.canonical_text, ReplayExtractor({nr.canonical_text: payload}), policy=pol)
    rd = ho.response.get("route_d") or {}
    assert rd.get("status") == "SERVED"


def test_source_gate_catches_swapped_projection_args_as_in_v7h_p5_09() -> None:
    """Validates _C_CHIEU rejects inverted point/image arguments (`v7h_p5_09` exact failure boundary)."""
    t = "Cho hình chóp G.RST có đáy RST là tam giác đều cạnh 4a. Gọi I là trung điểm của cạnh RS, hình chiếu vuông góc của G lên (RST) trùng với điểm I. Góc giữa GT với mặt phẳng (RST) là 60°. Tính thể tích G.RST."
    rd_bad = _run_gold_typed_facts(
        t,
        solid_type="pyramid",
        notation="G.RST",
        solid_quote="Cho hình chóp G.RST",
        premises=[
            {"kind": "regular_polygon", "args": {"vertices": ["R", "S", "T"], "side": "4a"}, "quote": "đáy RST là tam giác đều cạnh 4a", "solid_id": "s1"},
            {"kind": "midpoint", "args": {"point": "I", "segment": ["R", "S"]}, "quote": "Gọi I là trung điểm của cạnh RS", "solid_id": "s1"},
            {"kind": "orthogonal_projection", "args": {"point": "R", "image": "G", "plane": ["R", "S", "T"]}, "quote": "hình chiếu vuông góc của G lên (RST) trùng với điểm I", "solid_id": "s1"},
            {"kind": "line_plane_angle", "args": {"line": ["G", "T"], "plane": ["R", "S", "T"], "value": "60", "unit": "deg"}, "quote": "Góc giữa GT với mặt phẳng (RST) là 60°", "solid_id": "s1"},
        ],
        goals=[{"goal_id": "q1", "kind": "measurement", "goal_type": "volume", "target": {"solid_id": "s1"}, "solid_id": "s1", "quote": "Tính thể tích G.RST"}],
    )
    assert rd_bad.get("status") == "REFUSED"
    assert rd_bad.get("refusal", {}).get("code") == "SOURCE_OBJECT_MISMATCH"


# ── 2. Mandatory Adversarial Negative Security Invariants (§12) ──────────────

@pytest.mark.parametrize(
    "case_name,problem_text,premises",
    [
        (
            "no_conditional_to_premise_conversion",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a. Nếu SA vuông góc với (ABCD) thì SA=2a. Tính thể tích khối chóp S.ABCD.",
            [
                {"kind": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "a"}, "quote": "đáy ABCD là hình vuông cạnh a", "solid_id": "s1"},
                {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "quote": "Nếu SA vuông góc với (ABCD) thì SA=2a", "solid_id": "s1"},
                {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "2a"}, "quote": "Nếu SA vuông góc với (ABCD) thì SA=2a", "solid_id": "s1"},
            ],
        ),
        (
            "no_negation_loss",
            "Cho hình chóp S.ABC có đáy ABC đều cạnh a, SA không vuông góc với (ABC) và SA=2a. Tính thể tích khối chóp S.ABC.",
            [
                {"kind": "regular_polygon", "args": {"vertices": ["A", "B", "C"], "side": "a"}, "quote": "đáy ABC đều cạnh a", "solid_id": "s1"},
                {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]}, "quote": "SA không vuông góc với (ABC)", "solid_id": "s1"},
                {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "2a"}, "quote": "SA=2a", "solid_id": "s1"},
            ],
        ),
        (
            "no_invented_dimension",
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với (ABCD). Tính thể tích khối chóp S.ABCD.",
            [
                {"kind": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "a"}, "quote": "đáy ABCD là hình vuông cạnh a", "solid_id": "s1"},
                {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "quote": "SA vuông góc với (ABCD)", "solid_id": "s1"},
                {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "3a"}, "quote": "SA=3a", "solid_id": "s1"},
            ],
        ),
        (
            "no_ambiguous_lateral_promotion",
            "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a và một cạnh bên bằng 2a. Tính thể tích khối chóp S.ABC.",
            [
                {"kind": "regular_polygon", "args": {"vertices": ["A", "B", "C"], "side": "a"}, "quote": "đáy ABC là tam giác đều cạnh a", "solid_id": "s1"},
                {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "2a"}, "quote": "một cạnh bên bằng 2a", "solid_id": "s1"},
            ],
        ),
        (
            "no_contrastive_true_if_bypass",
            "Cho lăng trụ đứng ABC.A'B'C' có đáy ABC vuông tại A, AB=a, AC=2a. Nếu cạnh bên AA'=3a thì tính thể tích ABC.A'B'C'.",
            [
                {"kind": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]}, "quote": "đáy ABC vuông tại A", "solid_id": "s1"},
                {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "a"}, "quote": "AB=a", "solid_id": "s1"},
                {"kind": "segment_length", "args": {"segment": ["A", "C"], "value": "2a"}, "quote": "AC=2a", "solid_id": "s1"},
                {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "3a"}, "quote": "Nếu cạnh bên AA'=3a thì", "solid_id": "s1"},
            ],
        ),
    ],
)
def test_adversarial_source_gate_security_invariants(case_name: str, problem_text: str, premises: list[dict]) -> None:
    """Ensures zero bypass for conditionals, negations, invented quantities, or ambiguous references."""
    if "lăng trụ" in problem_text:
        stype, notn, sq = "prism", "ABC.A'B'C'", "Cho lăng trụ đứng ABC.A'B'C'"
    elif "ABCD" in problem_text:
        stype, notn, sq = "pyramid", "S.ABCD", "Cho hình chóp S.ABCD"
    else:
        stype, notn, sq = "pyramid", "S.ABC", "Cho hình chóp S.ABC"
    goal_q = "Tính thể tích khối chóp " + notn if "khối chóp" in problem_text else "tính thể tích " + notn
    rd = _run_gold_typed_facts(
        problem_text,
        solid_type=stype,
        notation=notn,
        solid_quote=sq,
        premises=premises,
        goals=[{"goal_id": "q1", "kind": "measurement", "goal_type": "volume", "target": {"solid_id": "s1"}, "solid_id": "s1", "quote": goal_q}],
    )
    assert rd.get("status") == "REFUSED", f"{case_name} unexpectedly served: {rd}"
    code = (rd.get("refusal") or {}).get("code")
    assert code != "EMPTY_SIMULATION_GOALS", f"{case_name} short-circuited on structural test wiring!"
    assert code in {"CONDITIONAL_CLAUSE", "NEGATED_CLAUSE", "QUOTE_NOT_IN_SOURCE", "AMBIGUOUS_FACT", "UNGROUNDED_VALUE", "SOURCE_OBJECT_MISMATCH"}, (case_name, code, rd)

    nr = normalize_for_slm_grounding(problem_text, normalizer_version="v2")
    assert "không vuông góc" in nr.canonical_text or "không" not in problem_text
    if "nếu " in problem_text.lower() and " thì " in problem_text.lower():
        assert "thì" in nr.canonical_text.lower() or "nếu" in nr.canonical_text.lower()
