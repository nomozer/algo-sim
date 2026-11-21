# -*- coding: utf-8 -*-
"""Comprehensive tests for AXO HYBRID /7 deterministic language closure (`slm-verified-normalizer/2` & `local-slm-extractor/3`)."""

from __future__ import annotations

import pytest

from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.local_slm_extractor import (
    DEFAULT_CLOSURE_MODE,
    LOCAL_SLM_EXTRACTOR_VERSION,
    SLM_GROUNDING_VALIDATOR_VERSION,
    _cand_has_contiguous,
    _strip_conversational_prefix,
    build_compact_clause_context,
    build_compact_grammar_for_context,
    select_clean_quote,
    validate_and_lower_compact_clause,
)
from app.ai.local_slm_runtime import LOCAL_SLM_CACHE_NAMESPACE, LOCAL_SLM_RUNTIME_VERSION
from app.ai.slm_verified_normalizer import (
    SLM_VERIFIED_NORMALIZER_V1_VERSION,
    SLM_VERIFIED_NORMALIZER_VERSION,
    normalize_for_slm_grounding,
)
from app.ai.typed_fact_next_extraction import ReplayExtractor

_TEN_PROVENANCE_KEYS = {
    "original_text",
    "original_span",
    "original_clause_id",
    "normalized_text",
    "transformation_rule_id",
    "original_entity_refs",
    "scope",
    "polarity",
    "semantic_equivalence_evidence",
    "validation_status",
}


def test_v7_version_identities_distinct():
    assert LOCAL_SLM_RUNTIME_VERSION == "local-slm-runtime/3"
    assert LOCAL_SLM_CACHE_NAMESPACE == "HYBRID_V7_LOCAL_SLM"
    assert LOCAL_SLM_EXTRACTOR_VERSION == "local-slm-extractor/3"
    assert SLM_GROUNDING_VALIDATOR_VERSION == "slm-grounding-validator/3"
    assert SLM_VERIFIED_NORMALIZER_VERSION == "slm-verified-normalizer/2"
    assert DEFAULT_CLOSURE_MODE == "v7"


def test_normalizer_v2_ten_field_provenance_and_span_audit():
    raw = (
        "Xét hình chóp tam giác đều E.MNP, mặt đáy có cạnh bằng 2a và mọi cạnh bên dài 2a√2. "
        "Hãy xác định thể tích khối chóp E.MNP."
    )
    res = normalize_for_slm_grounding(raw, normalizer_version="v2")
    assert res.normalizer_version == SLM_VERIFIED_NORMALIZER_VERSION
    assert not res.typo_detected
    assert res.changed
    assert "Cho hình chóp tam giác đều E.MNP có cạnh đáy bằng 2a" in res.canonical_text
    assert "các cạnh bên bằng 2a√2" in res.canonical_text
    assert "Tính thể tích khối chóp E.MNP." in res.canonical_text

    prov = res.to_provenance_dict()
    assert len(prov["steps"]) >= 3
    for step in prov["steps"]:
        assert _TEN_PROVENANCE_KEYS.issubset(step.keys()), f"Missing keys in {step}"
        assert step["polarity"] == "AFFIRMATIVE"
        assert step["validation_status"] == "VALIDATED_MEANING_PRESERVING"
        assert isinstance(step["original_clause_id"], int) and step["original_clause_id"] >= 0
        s0, s1 = step["original_span"]
        assert 0 <= s0 <= s1 <= len(raw)


def test_group_a_universal_quantifier_positives_and_negatives():
    # Positives: universal lateral edges & regular tetrahedron
    tet = "Xét tứ diện đều MNPQ có tất cả các cạnh bằng 3a. Hãy xác định thể tích khối tứ diện MNPQ."
    vt = normalize_for_slm_grounding(tet, normalizer_version="v2")
    assert vt.canonical_text == "Cho tứ diện đều MNPQ có cạnh bằng 3a. Tính thể tích khối tứ diện MNPQ."

    # Negatives: NEVER rewrite ambiguous singular, partial quantifier, conditional, or negation
    neg_samples = [
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, cạnh bên dài 2a. Tính thể tích.",
        "Cho hình chóp tam giác đều S.ABC có cạnh bên bằng 2a. Tính thể tích.",
        "Cho hình chóp S.ABC có đáy ABC đều cạnh a, một số các cạnh bên dài 2a. Tính thể tích.",
        "Cho hình chóp S.ABC có đáy đều cạnh a. Nếu các cạnh bên dài 2a thì tính thể tích.",
        "Cho hình chóp S.ABC có đáy đều cạnh a. Các cạnh bên không dài 2a. Tính thể tích.",
    ]
    # Note: sample 2 ("chóp tam giác đều ... có cạnh bên bằng 2a") should NEVER get mangled by VN04_REG_PYR_BASE into "có cạnh đáy bằng bên"!
    for s in neg_samples:
        vs = normalize_for_slm_grounding(s, normalizer_version="v2")
        assert "cạnh đáy bằng bên" not in vs.canonical_text
        if "Nếu" in s or "không" in s or "một số" in s or s.startswith("Cho hình chóp S.ABC"):
            assert "các cạnh bên bằng 2a" not in vs.canonical_text


def test_group_b_face_perpendicular_vs_line_plane_and_negation():
    pos = (
        "Cho khối chóp M.ABCD nhận hình vuông ABCD có cạnh 2a làm đáy, "
        "đồng thời mặt bên MAB là tam giác đều nằm vuông góc với mặt đáy (ABCD). "
        "Hãy tìm khoảng cách từ A tới mặt phẳng (MCD)."
    )
    vp = normalize_for_slm_grounding(pos, normalizer_version="v2")
    assert "ABCD là hình vuông cạnh 2a. Mặt bên MAB là tam giác đều và vuông góc với đáy ABCD." in vp.canonical_text

    # Negative: 2-letter line must NEVER match VN05_NAM_VUONG_GOC_FACE, nor negated/conditional face perp
    neg_line = "Cho hình chóp S.ABC có đáy ABC đều cạnh a, SA không nằm vuông góc với đáy. Tính thể tích."
    vn = normalize_for_slm_grounding(neg_line, normalizer_version="v2")
    assert "không nằm vuông góc với đáy" in vn.canonical_text
    assert "nằm trong mặt phẳng" not in vn.canonical_text


def test_group_c_contrastive_con_thi_vs_genuine_conditional():
    pos = "Bài tập 12: Cho hình hộp chữ nhật DEFG.D'E'F'G' có DE=a, DG=3a, còn DD' thì có độ dài bằng 2a. Yêu cầu tính thể tích của khối hộp DEFG.D'E'F'G'."
    vp = normalize_for_slm_grounding(pos, normalizer_version="v2")
    assert "còn DD' thì" not in vp.canonical_text
    assert ", DD'=2a." in vp.canonical_text

    # Genuine conditionals MUST stay untouched (even when a solid notation dot S.ABCD precedes "còn ... thì")
    for cond in (
        "Cho hình hộp ABCD.A'B'C'D' có AB=a, AD=2a. Nếu AA'=3a thì tính thể tích.",
        "Cho hình chóp S.ABC có đáy đều cạnh a, khi SA=2a còn SB thì bằng 3a. Tính thể tích.",
        "Nếu hình chóp S.ABCD có đáy hình vuông cạnh a, còn SA thì vuông góc đáy thì tính thể tích.",
    ):
        vc = normalize_for_slm_grounding(cond, normalizer_version="v2")
        assert vc.canonical_text == cond


def test_group_d_base_vocative_prism_and_implicit_apostrophe():
    # Polite vocative comma (slm_h09)
    h09 = "Thưa thầy, bài cho hình chóp S.ABCD với đáy ABCD là hình chữ nhật có AB=a, AD=2a. Tính thể tích."
    assert normalize_for_slm_grounding(h09, normalizer_version="v2").canonical_text.startswith("Cho hình chóp S.ABCD")

    # Primed prism implicit base (slm_h10)
    h10 = "Cho mình hỏi bài này với: lăng trụ đứng ABC.A'B'C' nhận tam giác đều cạnh 2a làm đáy, độ dài cạnh bên AA' bằng a. Tính thể tích."
    v10 = normalize_for_slm_grounding(h10, normalizer_version="v2")
    assert "ABC.A'B'C' có đáy ABC là tam giác đều cạnh 2a" in v10.canonical_text
    assert "AA'=a" in v10.canonical_text

    # Ensure v1 reproduces /6 behavior (apostrophe bug preserved only under explicit v1 ablation mode)
    v10_v1 = normalize_for_slm_grounding(h10, normalizer_version="v1")
    assert v10_v1.normalizer_version == SLM_VERIFIED_NORMALIZER_V1_VERSION
    assert "nhận tam giác đều cạnh 2a làm đáy" in v10_v1.canonical_text

    # Prism height equivalence (v6h_f1_04)
    f1_04 = "Trong lăng trụ đứng GHK.G'H'K', đáy GHK là tam giác đều cạnh 2a√3 và chiều cao GG'=2a. Tìm thể tích của khối lăng trụ GHK.G'H'K'."
    v_f1 = normalize_for_slm_grounding(f1_04, normalizer_version="v2")
    assert "GHK.G'H'K' có đáy GHK là tam giác đều cạnh 2a√3, GG'=2a." in v_f1.canonical_text


def test_group_e_contiguous_quotes_conversational_em_bug_and_proj_midpoint():
    # 1. Segment label "EM " must NEVER be stripped in v7 (regression guard against /6 re.IGNORECASE bug)
    em_clause = "EM vuông góc với (MNP), biết góc giữa (ENP) và (MNP) bằng 45°."
    assert _strip_conversational_prefix(em_clause, closure_mode="v7") == em_clause
    assert _strip_conversational_prefix(em_clause, closure_mode="v6") != em_clause  # v6 config B parity check
    q_em = select_clean_quote(
        em_clause,
        ["E", "M", "M", "N", "P"],
        em_clause,
        required_contiguous=["EM"],
        required_cues=("vuông góc",),
        closure_mode="v7",
    )
    assert q_em == "EM vuông góc với (MNP)"

    # 2. Boundary check prevents "AB" matching inside "S.ABC" or "UV" inside "UVWX"
    assert not _cand_has_contiguous("Cho hình chóp S.ABC", "AB")
    assert not _cand_has_contiguous("Cho khối chóp M.ABCD có đáy ABCD là hình vuông", "MAB")
    assert _cand_has_contiguous("mặt bên MAB là tam giác đều", "MAB")
    assert not _cand_has_contiguous("Cho hình chữ nhật UVWX", "UV")

    # 3. Compound projection-midpoint decomposition + downstream SERVED check (v6h_f8_03)
    raw_f8 = "Cho hình chóp H.KLM có đáy KLM là tam giác đều cạnh 2a. Hình chiếu vuông góc của H lên mặt đáy (KLM) là trung điểm I của KL, HK=2a. Tính thể tích khối chóp H.KLM."
    vn8 = normalize_for_slm_grounding(raw_f8, normalizer_version="v2")
    assert "Gọi I là trung điểm của KL. Hình chiếu vuông góc của H lên mặt phẳng (KLM) là I, HK=2a." in vn8.canonical_text

    ctx8 = build_compact_clause_context(vn8.canonical_text)
    payload8, env8 = validate_and_lower_compact_clause(
        ctx=ctx8,
        raw_slm_json={
            "s": [0, "pyr", "H.KLM", 0],
            "r": [
                {"c": 0, "p": "reg_poly", "a": "KLM", "q": "2a"},
                {"c": 1, "p": "mid", "pt": "I", "a": "KL"},
                {"c": 2, "p": "proj", "pt": "I", "a": "H", "b": "KLM"},
                {"c": 2, "p": "len", "a": "HK", "q": "2a"},
            ],
            "g": [{"c": 3, "t": "vol", "tgt": "H.KLM"}],
            "u": [],
        },
        closure_mode="v7",
    )
    assert payload8 is not None and env8["grounding_status"] == "GROUNDED_AND_LOWERED"
    pol = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
    out8 = run_hybrid_offline(vn8.canonical_text, ReplayExtractor({vn8.canonical_text: payload8}), policy=pol)
    assert out8.response["route_d"]["status"] == "SERVED"


def test_tetrahedron_lowering_and_perp_lp_v7_gbnf_guard():
    # Regular tetrahedron lowers end-to-end without Source Gate issues
    raw_tet = "Xét tứ diện đều MNPQ có tất cả các cạnh bằng 3a. Hãy xác định thể tích khối tứ diện MNPQ."
    v_tet = normalize_for_slm_grounding(raw_tet, normalizer_version="v2")
    ctx_t = build_compact_clause_context(v_tet.canonical_text)
    payload_t, env_t = validate_and_lower_compact_clause(
        ctx=ctx_t,
        raw_slm_json={"s": [0, "pyr", "M.NPQ", 1], "r": [{"c": 0, "p": "len", "a": "M.NPQ", "q": "3a"}], "g": [{"c": 1, "t": "vol", "tgt": "M.NPQ"}], "u": []},
        closure_mode="v7",
    )
    assert payload_t is not None and env_t["grounding_status"] == "GROUNDED_AND_LOWERED"
    pol = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
    out_t = run_hybrid_offline(v_tet.canonical_text, ReplayExtractor({v_tet.canonical_text: payload_t}), policy=pol)
    assert out_t.response["route_d"]["status"] == "SERVED"

    # v7 GBNF must NOT allow spurious perp_lp on "lăng trụ đứng" or "tam giác vuông cân" without "vuông góc"/"⊥"
    prism_txt = "Cho hình lăng trụ đứng MNP.M'N'P' có đáy MNP là tam giác vuông cân tại M, MN=a, MM'=2a. Tính thể tích."
    ctx_p = build_compact_clause_context(prism_txt)
    g_v7 = build_compact_grammar_for_context(ctx_p, closure_mode="v7")
    g_v6 = build_compact_grammar_for_context(ctx_p, closure_mode="v6")
    assert "perp_lp" not in g_v7
    assert "perp_lp" in g_v6


def test_v6_ablation_quote_fidelity_and_sentence_boundary_rules():
    # 1. closure_mode="v6" preserves exact /6 quote selection on cal_p03_sq_pyramid_angle while v7 enforces contiguous + cues
    c03 = "Khối chóp S.ABCD có đáy ABCD là hình vuông cạnh a. Cạnh SA vuông góc với đáy, góc giữa SC và (ABCD) bằng 45°. Tính thể tích khối chóp S.ABCD."
    q_v6 = select_clean_quote("Cạnh SA vuông góc với đáy, góc giữa SC và (ABCD) bằng 45°", ["S", "A", "A", "B", "C", "D"], c03, closure_mode="v6")
    assert q_v6 == "Cạnh SA vuông góc với đáy, góc giữa SC và (ABCD) bằng 45°"
    q_ang_v7 = select_clean_quote(
        "Cạnh SA vuông góc với đáy, góc giữa SC và (ABCD) bằng 45°",
        ["S", "C", "A", "B", "C", "D", "45"],
        c03,
        required_contiguous=["SC"],
        required_cues=("góc", "°"),
        closure_mode="v7",
    )
    assert q_ang_v7 == "góc giữa SC và (ABCD) bằng 45°"

    # 2. VN05_SPLIT_MAT_BEN_CLAUSE & VN05_NAM_TRONG_FACE_PERP with parenthesized base
    f6_04 = (
        "Cho khối chóp M.ABCD nhận hình vuông ABCD có cạnh 2a làm đáy, "
        "đồng thời mặt bên MAB là tam giác đều nằm vuông góc với mặt đáy (ABCD). "
        "Hãy tìm khoảng cách từ A tới mặt phẳng (MCD)."
    )
    vn = normalize_for_slm_grounding(f6_04, normalizer_version="v2")
    assert "ABCD là hình vuông cạnh 2a. Mặt bên MAB là tam giác đều và vuông góc với đáy ABCD." in vn.canonical_text

    # 3. VN05_VUONG_GOC_MAT_DAY_PAREN canonicalizes "vuông góc với mặt đáy (MNP)" safely, never touching negations
    f7_02 = "Cho hình chóp K.MNP có đáy MNP là tam giác đều cạnh 2a, KM vuông góc với mặt đáy (MNP), KM=3a."
    v72 = normalize_for_slm_grounding(f7_02, normalizer_version="v2")
    assert "KM vuông góc với (MNP)" in v72.canonical_text
    neg_72 = "Cho hình chóp K.MNP có đáy MNP là tam giác đều cạnh 2a, KM không vuông góc với mặt đáy (MNP)."
    assert "không vuông góc với mặt đáy (MNP)" in normalize_for_slm_grounding(neg_72, normalizer_version="v2").canonical_text

    # 4. Normalized Local Parser reconciliation upgrades misquoted SLM premises on cal_p04 deterministically -> SERVED
    p04 = (
        "Đặt M là điểm chính giữa cạnh SC trong hình chóp S.ABC. "
        "Tam giác đáy ABC vuông tại B có AB=a, BC=a√3, SA vuông góc mặt đáy (ABC), SA=a. "
        "Tính khoảng cách từ M đến (ABC)."
    )
    vn04 = normalize_for_slm_grounding(p04, normalizer_version="v2")
    ctx04 = build_compact_clause_context(vn04.canonical_text)
    payload04, env04 = validate_and_lower_compact_clause(
        ctx=ctx04,
        raw_slm_json={
            "s": [0, "pyr", "S.ABC", 0],
            "r": [{"c": 0, "p": "mid", "pt": "M", "a": "SC"}],
            "g": [{"c": 2, "t": "dist_pt_plane", "a": "M", "b": "ABC"}],
            "u": [],
        },
        closure_mode="v7",
    )
    assert payload04 is not None and env04["grounding_status"] == "GROUNDED_AND_LOWERED"
    pol = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
    out = run_hybrid_offline(vn04.canonical_text, ReplayExtractor({vn04.canonical_text: payload04}), policy=pol)
    assert out.response["route_d"]["status"] == "SERVED"
