# -*- coding: utf-8 -*-
"""Tests for three-tier scoring (Mathematical / Semantic Goal / Strict Contract) & H-1 corpus sealing verifier."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import score_independent_holdout_equivalence as S

REPO = Path(__file__).resolve().parents[3]


def _make_section_row(
    case_id: str,
    problem_text: str,
    *,
    observed_goals: list[str],
    expected_goals: list[str],
    answer: str = "3√2/2",
    expected_answer: str = "3√2/2",
    cert_ok: bool = True,
) -> dict:
    raw = {
        "schema_version": "typed-fact-next/2",
        "problem_text": problem_text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "hình chóp S.ABCD"}],
        "premises": [
            {"kind": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "2"}, "quote": "hình vuông cạnh 2", "solid_id": "s1"},
            {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "quote": "SA vuông góc với (ABCD)", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "2"}, "quote": "SA = 2", "solid_id": "s1"},
        ],
        "described_points": [],
        "derived_sections": [
            {
                "section_id": "sec1",
                "plane_name": "P",
                "target_solid_id": "s1",
                "plane_kind": "constrained",
                "constraints": [
                    {"kind": "contains_points", "operands": ["A", "B"]},
                    {"kind": "perpendicular_to_plane", "operands": ["S", "C", "D"]},
                ],
                "quote": "Mặt phẳng (P) đi qua A, B và vuông góc với (SCD)",
            }
        ],
        "relations": [],
        "simulation_goals": [{"goal_id": "g1", "kind": "construct_object", "target_solid_id": "s1", "quote": "hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "m1", "kind": "measurement", "goal_type": "area", "solid_id": "s1", "target": {"section_id": "sec1"}, "quote": "diện tích thiết diện"}],
        "unresolved": [],
    }
    return {
        "type": "row",
        "case_id": case_id,
        "technical_failure": False,
        "raw_extraction": raw,
        "expected": {
            "outcome": "SERVED",
            "is_ambiguous": False,
            "expected_facts_signature": "sig1",
            "expected_goals": expected_goals,
            "expected_operands": ["2", "S.ABCD"],
            "expected_answers": {"area": [expected_answer]},
        },
        "observed": {
            "status": "SERVED",
            "facts_signature": "sig1",
            "extracted_goals": observed_goals,
            "operands": ["2", "S.ABCD"],
            "quotes_verbatim_in_raw": True,
            "answers": {"area": [answer]},
            "certificate_verified": cert_ok,
        },
    }


def test_offline_guard_and_empty_not_measured_invariants(monkeypatch):
    rep = S.score_three_tier_rows([])
    assert rep["measurement_status"] == "NOT_MEASURED"
    for v in rep["tiers"].values():
        assert v == {"numerator": "UNKNOWN", "denominator": 0, "rate": "NOT_MEASURED"}

    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    with pytest.raises(RuntimeError, match="strictly offline"):
        S.score_three_tier_rows([])
    with pytest.raises(RuntimeError, match="strictly offline"):
        S.build_h1_corpus_integrity_receipt()


def test_explicit_section_determination_clause_boundary():
    assert S.has_explicit_section_determination_request(
        "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó."
    )
    assert S.has_explicit_section_determination_request(
        "Tìm thiết diện tạo bởi mặt phẳng (α) với hình lăng trụ và tính diện tích của nó."
    )
    assert not S.has_explicit_section_determination_request(
        "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (P)."
    )
    assert not S.has_explicit_section_determination_request(
        "Không xác định thiết diện, chỉ tính thể tích khối chóp S.ABCD."
    )


def test_three_tier_scorer_separates_compound_section_area_from_unasked_or_dropped_goals():
    g_obj = '["sim", {"kind": "construct_object", "target_solid_id": "solid:S.ABCD"}]'
    g_sec = '["sim", {"kind": "construct_plane_section", "target_section_id": "section:P"}]'
    g_sec_scoped = '["sim", {"kind": "construct_plane_section", "target_section_id": "section:P", "target_solid_id": "solid:S.ABCD"}]'
    g_area = '["math", {"goal_type": "area", "kind": "measurement", "solid_id": "solid:S.ABCD", "target": {"section_id": "section:P"}}]'
    g_extra_vol = '["math", {"goal_type": "volume", "kind": "measurement", "solid_id": "solid:S.ABCD", "target": {"solid_id": "solid:S.ABCD"}}]'

    rows = [
        # 1. Compound "Xác định thiết diện ... và tính diện tích": semantic=True, strict=False, math=True
        _make_section_row(
            "H-CMP-1",
            "Cho hình chóp S.ABCD có đáy hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 2. Mặt phẳng (P) đi qua A, B và vuông góc với (SCD). Xác định thiết diện của hình chóp cắt bởi (P) và tính diện tích thiết diện đó.",
            expected_goals=[g_area, g_obj],
            observed_goals=[g_area, g_obj, g_sec_scoped],
        ),
        # 2. Single-clause "Tính diện tích thiết diện..." (NO section determination asked): semantic=False, strict=False
        _make_section_row(
            "H-AREA-ONLY",
            "Cho hình chóp S.ABCD có đáy hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 2. Mặt phẳng (P) đi qua A, B và vuông góc với (SCD). Tính diện tích thiết diện của hình chóp cắt bởi (P).",
            expected_goals=[g_area, g_obj],
            observed_goals=[g_area, g_obj, g_sec],
        ),
        # 3. Unasked extra math goal (volume) even when "Xác định thiết diện" is present: semantic=False, strict=False
        _make_section_row(
            "H-EXTRA-MATH",
            "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó.",
            expected_goals=[g_area, g_obj],
            observed_goals=[g_area, g_obj, g_sec, g_extra_vol],
        ),
        # 4. Dropped expected goal: semantic=False, strict=False
        _make_section_row(
            "H-DROPPED",
            "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó.",
            expected_goals=[g_area, g_obj, g_sec],
            observed_goals=[g_obj, g_sec],
        ),
        # 5. Wrong mathematical answer: math=False, semantic_wrong_served=True, strict_wrong_served=True
        _make_section_row(
            "H-WRONG-MATH",
            "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (P).",
            expected_goals=[g_area, g_obj],
            observed_goals=[g_area, g_obj],
            answer="999",
            expected_answer="3√2/2",
        ),
    ]

    scored = S.score_three_tier_rows(rows)
    by_id = {c["case_id"]: c for c in scored["per_case"]}

    assert by_id["H-CMP-1"]["mathematical_served_correct"] is True
    assert by_id["H-CMP-1"]["semantic_goal_correct"] is True
    assert by_id["H-CMP-1"]["semantic_served_correct"] is True
    assert by_id["H-CMP-1"]["strict_goal_correct"] is False
    assert by_id["H-CMP-1"]["strict_served_correct"] is False
    assert scored["strict_vs_semantic_divergences"] == ["H-CMP-1"]

    for bad_goal_id in ("H-AREA-ONLY", "H-EXTRA-MATH", "H-DROPPED"):
        assert by_id[bad_goal_id]["semantic_goal_correct"] is False
        assert by_id[bad_goal_id]["semantic_wrong_served"] is True
        assert by_id[bad_goal_id]["strict_goal_correct"] is False
        assert by_id[bad_goal_id]["strict_wrong_served"] is True

    assert by_id["H-WRONG-MATH"]["mathematical_served_correct"] is False
    assert by_id["H-WRONG-MATH"]["mathematical_wrong_served"] is True
    assert by_id["H-WRONG-MATH"]["semantic_wrong_served"] is True
    assert by_id["H-WRONG-MATH"]["strict_wrong_served"] is True


def test_c26_recorded_rows_verify_read_only_across_all_three_tiers():
    """Verify the 70 recorded C26 live rows without modifying any historical K-1/S-2/R-1 gold file."""
    c26_full = REPO / "docs" / "evaluation" / "geometry" / "runs" / "hybrid-live-extraction-retest" / "full"
    rows = S._load_jsonl_rows([c26_full / "k1-live.jsonl", c26_full / "s2-live.jsonl", c26_full / "r1-live.jsonl"])
    assert len(rows) == 70
    scored = S.score_three_tier_rows(rows)
    tiers = scored["tiers"]
    # Mathematical: 37/41 expected-SERVE served with exact oracle & certificate; 0/70 wrong-served
    assert tiers["mathematical_served_correct"] == {"numerator": 37, "denominator": 41, "rate": 0.902439}
    assert tiers["mathematical_wrong_served"] == {"numerator": 0, "denominator": 70, "rate": 0.0}
    # Semantic: all 7 compound section+area SERVED rows resolve cleanly; 0/70 semantic wrong-served
    assert tiers["semantic_served_correct"] == {"numerator": 37, "denominator": 41, "rate": 0.902439}
    assert tiers["semantic_wrong_served"] == {"numerator": 0, "denominator": 70, "rate": 0.0}
    # Strict: preserves the unchanged C26 strict count (30/41 strict served-correct, 7/70 strict wrong-served)
    assert tiers["strict_served_correct"] == {"numerator": 30, "denominator": 41, "rate": 0.731707}
    assert tiers["strict_wrong_served"] == {"numerator": 7, "denominator": 70, "rate": 0.1}
    assert scored["strict_vs_semantic_divergences"] == [
        "K-A01", "K-A02", "K-A03", "K-A04", "K-B01", "K-B02", "R1-B01", "R1-B02", "R1-C02",
    ]


def test_h1_corpus_integrity_receipt_honest_pre_corpus_and_sealing_guards(tmp_path):
    # 1. Missing corpus -> honest NOT_ESTABLISHED / NOT_MEASURED receipt
    pre = S.build_h1_corpus_integrity_receipt(tmp_path / "missing-h1.json", repo_root=REPO)
    assert pre["status"] == "AWAITING_INDEPENDENT_CORPUS"
    assert pre["h1_authoring_independence"] == "NOT_ESTABLISHED"
    assert pre["h1_measurement"] == "NOT_MEASURED"
    assert pre["corpus_present"] is False
    assert pre["corpus_sha256"] is None and pre["oracle_sha256"] is None
    assert pre["candidate_identity"]["frozen_candidate_commit"] == "180db769"

    # 2. Build a clean miniature repo root + synthetic 60-case corpus to test sealing and contamination guards
    fake_repo = tmp_path / "repo"
    (fake_repo / "docs" / "evaluation" / "semantic-benchmark").mkdir(parents=True)
    cand_src = REPO / "docs" / "evaluation" / "semantic-benchmark" / "EVALUATION_CANDIDATE.json"
    (fake_repo / "docs" / "evaluation" / "semantic-benchmark" / "EVALUATION_CANDIDATE.json").write_bytes(
        cand_src.read_bytes()
    )
    import subprocess
    subprocess.run(["git", "init"], cwd=fake_repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=fake_repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=fake_repo, check=True)
    (fake_repo / "README.md").write_text("clean repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=fake_repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=fake_repo, check=True, capture_output=True)

    cases = []
    for i in range(45):
        cases.append({
            "id": f"H1-S{i + 1:02d}",
            "problem_text": f"Cho tứ diện vuông OABC có OA = {i + 3}, OB = {i + 4}, OC = {i + 5}. Tính thể tích khối tứ diện OABC.",
            "expect": "SERVE",
            "oracle": {"volume": [f"{(i + 3) * (i + 4) * (i + 5)}/6"]},
        })
    for idx, rclass in enumerate(("OUT_OF_DOMAIN",) * 5 + ("CONTRADICTORY_DATA",) * 5 + ("MISSING_DATA",) * 5):
        cases.append({
            "id": f"H1-R{idx + 1:02d}",
            "problem_text": f"Bài kiểm tra từ chối độc lập số {idx + 101} thuộc nhóm {rclass}.",
            "expect": "REFUSE",
            "refusal_class": rclass,
        })

    cpath = fake_repo / "h1-corpus.json"
    cpath.write_text(
        json.dumps(
            {
                "schema": "hybrid-master-paired-heldout/2",
                "author": "Independent Geometry Teacher A",
                "authoring_independence": "ESTABLISHED",
                "cases": cases,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    sealed = S.build_h1_corpus_integrity_receipt(cpath, repo_root=fake_repo)
    assert sealed["status"] == "CORPUS_SEALED_AWAITING_BUDGET"
    assert sealed["h1_authoring_independence"] == "ESTABLISHED"
    assert sealed["h1_measurement"] == "NOT_MEASURED"
    assert len(sealed["corpus_sha256"]) == 64 and len(sealed["oracle_sha256"]) == 64
    assert sealed["blocking_conditions"] == ["PAIRED_LIVE_CAMPAIGN_BUDGET_NOT_APPROVED_BY_OWNER"]

    # 3. Exact overlap with an existing repo file is rejected fail-closed
    (fake_repo / "dev_leak.json").write_text(json.dumps({"q": cases[0]["problem_text"]}), encoding="utf-8")
    with pytest.raises(S.P.LiveRefused, match="exact overlap"):
        S.build_h1_corpus_integrity_receipt(cpath, repo_root=fake_repo)
