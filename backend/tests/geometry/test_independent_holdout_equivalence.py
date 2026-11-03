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
    g_extra_dist = '["math", {"goal_type": "distance", "kind": "measurement", "solid_id": "solid:S.ABCD", "target": {"plane": ["A", "B", "C", "D"], "point": "S"}}]'

    rows = [
        # 1. P1 Case A: Compound "Xác định thiết diện ... và tính diện tích": requires construct_plane_section + area
        _make_section_row(
            "H-CMP-1",
            "Cho hình chóp S.ABCD có đáy hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 2. Mặt phẳng (P) đi qua A, B và vuông góc với (SCD). Xác định thiết diện của hình chóp cắt bởi (P) và tính diện tích thiết diện đó.",
            expected_goals=[g_area, g_obj],
            observed_goals=[g_area, g_obj, g_sec_scoped],
        ),
        # 1b. P1 Case A missing construct_plane_section: even if legacy expected_goals omitted g_sec, P1 requires BOTH!
        _make_section_row(
            "H-CMP-MISSING-SEC",
            "Cho hình chóp S.ABCD có đáy hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 2. Mặt phẳng (P) đi qua A, B và vuông góc với (SCD). Xác định thiết diện của hình chóp cắt bởi (P) và tính diện tích thiết diện đó.",
            expected_goals=[g_area, g_obj],
            observed_goals=[g_area, g_obj],
        ),
        # 2. P1 Case B: Single-clause "Tính diện tích thiết diện..." -> area ONLY (construct_plane_section rejected)
        _make_section_row(
            "H-AREA-ONLY",
            "Cho hình chóp S.ABCD có đáy hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 2. Mặt phẳng (P) đi qua A, B và vuông góc với (SCD). Tính diện tích thiết diện của hình chóp cắt bởi (P).",
            expected_goals=[g_area, g_obj],
            observed_goals=[g_area, g_obj, g_sec],
        ),
        # 3a. P1 Case C (volume): Unasked extra volume goal -> wrong goal
        _make_section_row(
            "H-EXTRA-MATH",
            "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó.",
            expected_goals=[g_area, g_obj],
            observed_goals=[g_area, g_obj, g_sec, g_extra_vol],
        ),
        # 3b. P1 Case C (distance): Area-only prompt where Gemini adds distance -> wrong goal
        _make_section_row(
            "H-EXTRA-DIST",
            "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (P).",
            expected_goals=[g_area, g_obj],
            observed_goals=[g_area, g_obj, g_extra_dist],
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
    assert scored["strict_vs_semantic_divergences"] == ["H-CMP-1", "H-CMP-MISSING-SEC"]

    for bad_goal_id in ("H-CMP-MISSING-SEC", "H-AREA-ONLY", "H-EXTRA-MATH", "H-EXTRA-DIST", "H-DROPPED"):
        assert by_id[bad_goal_id]["semantic_goal_correct"] is False
        assert by_id[bad_goal_id]["semantic_wrong_served"] is True

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
    families = ("pyramid", "prism", "cuboid", "cube", "sphere", "cylinder", "cone")
    questions = ("section_measure", "distance", "angle", "volume", "area")
    for i in range(45):
        cases.append({
            "id": f"H1-S{i + 1:02d}",
            "problem_text": f"Cho tứ diện vuông OABC có OA = {i + 3}, OB = {i + 4}, OC = {i + 5} và câu dẫn bối cảnh riêng biệt thứ {'một ' * ((i % 4) + 1)}số {i + 100}. Tính thể tích khối tứ diện OABC.",
            "expect": "SERVE",
            "stratum": {"family": families[i % len(families)], "question": questions[i % len(questions)]},
            "oracle": {"volume": [f"{(i + 3) * (i + 4) * (i + 5)}/6"]},
            "oracle_derivation": f"V = 1/6 * OA * OB * OC = 1/6 * {i + 3} * {i + 4} * {i + 5}.",
            "semantic_annotations": {"explicit_goals": ["volume"]},
            "provenance": "Biên soạn mới độc lập ngày 2026-11-03, giải tay độc lập.",
        })
    for idx, rclass in enumerate(("OUT_OF_DOMAIN",) * 5 + ("CONTRADICTORY_DATA",) * 5 + ("MISSING_DATA",) * 5):
        cases.append({
            "id": f"H1-R{idx + 1:02d}",
            "problem_text": f"Bài kiểm tra từ chối độc lập số {idx + 101} thuộc nhóm {rclass}.",
            "expect": "REFUSE",
            "refusal_class": rclass,
            "provenance": "Biên soạn mới độc lập ngày 2026-11-03.",
        })

    cpath = fake_repo / "h1-corpus.json"
    # 2a. Bare "authoring_independence": "ESTABLISHED" WITHOUT independence_evidence / written_before_any_system_run
    #     must NOT be blindly trusted (§V.2)!
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
    unverified = S.build_h1_corpus_integrity_receipt(cpath, repo_root=fake_repo)
    assert unverified["h1_authoring_independence"] == "NOT_ESTABLISHED"
    assert unverified["status"] == "CORPUS_NEEDS_REVIEW"
    assert unverified["sealing_checklist"]["6_evaluation_manifest_sealed"] is False

    # 2b. Full independent provenance + derivations + semantic annotations -> seals cleanly
    full_corpus = {
        "schema": "hybrid-master-paired-heldout/2",
        "author": "Independent Geometry Teacher A",
        "author_affiliation": "THPT Chuyên Độc Lập",
        "authoring_independence": "ESTABLISHED",
        "written_before_any_system_run": True,
        "independence_evidence": "Tự biên soạn mới 100% ngày 2026-11-03, giải độc lập bằng tay + SymPy, chưa chạy trên AlgoSim.",
        "cases": cases,
    }
    cpath.write_text(json.dumps(full_corpus, ensure_ascii=False), encoding="utf-8")
    sealed = S.build_h1_corpus_integrity_receipt(cpath, repo_root=fake_repo)
    assert sealed["status"] == "CORPUS_SEALED_AWAITING_BUDGET"
    assert sealed["h1_authoring_independence"] == "ESTABLISHED"
    assert sealed["h1_measurement"] == "NOT_MEASURED"
    assert len(sealed["corpus_sha256"]) == 64 and len(sealed["oracle_sha256"]) == 64
    assert sealed["blocking_conditions"] == ["PAIRED_LIVE_CAMPAIGN_BUDGET_NOT_APPROVED_BY_OWNER"]

    # 3. Copying H1_AUTHORING_HANDOFF.md's illustrative example verbatim is rejected fail-closed;
    #    merely renaming vertices & numbers ("S.ABCD" -> "P.MNPQ", 4 -> 6, 3 -> 5) is caught as a template clone!
    handoff_dst = fake_repo / "docs" / "evaluation" / "geometry" / "runs" / "hybrid-independent-h1"
    handoff_dst.mkdir(parents=True, exist_ok=True)
    handoff_src = REPO / "docs" / "evaluation" / "geometry" / "runs" / "hybrid-independent-h1" / "H1_AUTHORING_HANDOFF.md"
    (handoff_dst / "H1_AUTHORING_HANDOFF.md").write_bytes(handoff_src.read_bytes())

    copied_cases = [dict(c) for c in cases]
    copied_cases[0] = {
        **copied_cases[0],
        "problem_text": (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, cạnh bên SA vuông góc với mặt phẳng đáy và SA = 3. "
            "Gọi M là trung điểm của cạnh SB. Mặt phẳng (P) đi qua M và song song với mặt phẳng (ABCD). "
            "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó."
        ),
        "oracle": {"area": ["4"]},
        "semantic_annotations": {"explicit_goals": ["construct_plane_section", "area"]},
    }
    cpath.write_text(json.dumps({**full_corpus, "cases": copied_cases}, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(S.P.LiveRefused, match="exact overlap"):
        S.build_h1_corpus_integrity_receipt(cpath, repo_root=fake_repo)

    renamed_cases = [dict(c) for c in cases]
    renamed_cases[0] = {
        **renamed_cases[0],
        "problem_text": (
            "Cho hình chóp P.MNPQ có đáy MNPQ là hình vuông cạnh 6, cạnh bên PM vuông góc với mặt phẳng đáy và PM = 5. "
            "Gọi N là trung điểm của cạnh PN. Mặt phẳng (Q) đi qua N và song song với mặt phẳng (MNPQ). "
            "Xác định thiết diện của hình chóp P.MNPQ cắt bởi (Q) và tính diện tích thiết diện đó."
        ),
        "oracle": {"area": ["9"]},
        "semantic_annotations": {"explicit_goals": ["construct_plane_section", "area"]},
    }
    cpath.write_text(json.dumps({**full_corpus, "cases": renamed_cases}, ensure_ascii=False), encoding="utf-8")
    cloned = S.build_h1_corpus_integrity_receipt(cpath, repo_root=fake_repo)
    assert cloned["status"] == "CORPUS_NEEDS_REVIEW"
    assert cloned["sealing_checklist"]["6_evaluation_manifest_sealed"] is False
    assert "H1-S01" in cloned["contamination_scan"]["structural_template_clones"]


def test_c28_stratum_semantic_annotations_oracle_review_and_template_completeness(tmp_path):
    # 1. Self-contained handoff template inside hybrid-independent-h1/ must exist and declare all required C28 fields
    tpl_path = REPO / "docs" / "evaluation" / "geometry" / "runs" / "hybrid-independent-h1" / "h1-corpus-template.json"
    assert tpl_path.is_file(), "h1-corpus-template.json must exist in hybrid-independent-h1/"
    tpl = json.loads(tpl_path.read_text(encoding="utf-8"))
    assert tpl["schema"] == "hybrid-master-paired-heldout/2"
    for top_key in ("author", "author_affiliation", "authoring_independence", "written_before_any_system_run", "independence_evidence"):
        assert top_key in tpl
    serve_tpl, refuse_tpl = tpl["cases"][0], tpl["cases"][1]
    for k in ("id", "problem_text", "expect", "oracle", "oracle_derivation", "stratum", "semantic_annotations", "provenance"):
        assert k in serve_tpl
    for k in ("id", "problem_text", "expect", "refusal_class", "provenance"):
        assert k in refuse_tpl

    # 2. Verify C28 §IV checks 4 (7 families >=3 & 5 questions >=3), 6 (oracle review status), and 7 (P1 semantic annotations)
    fake_repo = tmp_path / "repo2"
    (fake_repo / "docs" / "evaluation" / "semantic-benchmark").mkdir(parents=True)
    cand_src = REPO / "docs" / "evaluation" / "semantic-benchmark" / "EVALUATION_CANDIDATE.json"
    (fake_repo / "docs" / "evaluation" / "semantic-benchmark" / "EVALUATION_CANDIDATE.json").write_bytes(cand_src.read_bytes())
    import subprocess
    subprocess.run(["git", "init"], cwd=fake_repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=fake_repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=fake_repo, check=True)
    (fake_repo / "README.md").write_text("clean\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=fake_repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=fake_repo, check=True, capture_output=True)

    families = ("pyramid", "prism", "cuboid", "cube", "sphere", "cylinder", "cone")
    questions = ("section_measure", "distance", "angle", "volume", "area")
    valid_cases = []
    for i in range(45):
        valid_cases.append({
            "id": f"H1-S{i + 1:02d}",
            "problem_text": f"Cho khối đa diện thử nghiệm riêng biệt số {i + 200} với nhánh từ ngữ {'bổ trợ ' * ((i % 4) + 1)}và cạnh gốc {i + 5}. Tính thể tích khối đó.",
            "expect": "SERVE",
            "stratum": {"family": families[i % len(families)], "question": questions[i % len(questions)]},
            "oracle": {"volume": [f"{i + 5}"]},
            "oracle_derivation": f"Theo công thức thể tích chuẩn: V = {i + 5}.",
            "semantic_annotations": {"explicit_goals": ["volume"]},
            "provenance": "Biên soạn độc lập ngày 2026-11-03.",
        })
    for idx, rclass in enumerate(("OUT_OF_DOMAIN",) * 5 + ("CONTRADICTORY_DATA",) * 5 + ("MISSING_DATA",) * 5):
        valid_cases.append({
            "id": f"H1-R{idx + 1:02d}",
            "problem_text": f"Đề kiểm tra từ chối an toàn độc lập số {idx + 300} lớp {rclass}.",
            "expect": "REFUSE",
            "refusal_class": rclass,
            "provenance": "Biên soạn độc lập ngày 2026-11-03.",
        })

    base_doc = {
        "schema": "hybrid-master-paired-heldout/2",
        "author": "Giáo viên Toán Độc Lập B",
        "author_affiliation": "THPT Độc Lập",
        "authoring_independence": "ESTABLISHED",
        "written_before_any_system_run": True,
        "independence_evidence": "Biên soạn mới hoàn toàn ngày 2026-11-03, giải độc lập bằng tay và SymPy.",
    }
    cpath = fake_repo / "h1.json"

    # 2a. Missing `cone` family (< 3 cases) blocks stratification sealing
    skewed_cases = [dict(c, stratum={"family": "pyramid", "question": "volume"}) if c["expect"] == "SERVE" else dict(c)
                    for c in valid_cases]
    cpath.write_text(json.dumps({**base_doc, "cases": skewed_cases}, ensure_ascii=False), encoding="utf-8")
    skewed_res = S.build_h1_corpus_integrity_receipt(cpath, repo_root=fake_repo)
    assert skewed_res["sealing_checklist"]["3_count_and_stratification_45_5_5_5_verified"] is False
    assert skewed_res["status"] == "CORPUS_NEEDS_REVIEW"
    assert "INSUFFICIENT_STRATUM_COVERAGE" in skewed_res["blocking_conditions"]

    # 2b. P1 semantic_annotations mismatch (area-only text claiming construct_plane_section) blocks sealing
    bad_sem_cases = [dict(c) for c in valid_cases]
    bad_sem_cases[0] = {
        **bad_sem_cases[0],
        "problem_text": "Cho khối chóp riêng biệt số 991 có cạnh đáy 4 và chiều cao 6. Tính diện tích thiết diện của khối chóp cắt bởi mặt phẳng (P).",
        "oracle": {"area": ["8"]},
        "semantic_annotations": {"explicit_goals": ["construct_plane_section", "area"]},
    }
    cpath.write_text(json.dumps({**base_doc, "cases": bad_sem_cases}, ensure_ascii=False), encoding="utf-8")
    bad_sem_res = S.build_h1_corpus_integrity_receipt(cpath, repo_root=fake_repo)
    assert bad_sem_res["status"] == "CORPUS_NEEDS_REVIEW"
    assert "INVALID_SEMANTIC_ANNOTATIONS" in bad_sem_res["blocking_conditions"]

    # 2c. Valid corpus records oracle_verification with honest expert review status
    cpath.write_text(json.dumps({**base_doc, "cases": valid_cases}, ensure_ascii=False), encoding="utf-8")
    ok_res = S.build_h1_corpus_integrity_receipt(cpath, repo_root=fake_repo)
    assert ok_res["status"] == "CORPUS_SEALED_AWAITING_BUDGET"
    assert ok_res["stratum_coverage"]["valid"] is True
    assert ok_res["oracle_verification"]["exact_syntax_verified"] is True
    assert ok_res["oracle_verification"]["expert_mathematical_review_status"] == "PENDING_HUMAN_EXPERT_VERIFICATION"


def test_c28_paired_comparison_markdown_table():
    corpus = {
        "cases": [
            {"id": "H1-S01", "expect": "SERVE", "oracle": {"volume": ["12"]}},
            {"id": "H1-R01", "expect": "REFUSE", "refusal_class": "CONTRADICTORY_DATA"},
        ]
    }
    rows = [
        {"type": "row", "case_id": "H1-S01", "arm": "LLM_ONLY", "expect": "SERVE", "served": False,
         "served_correct": False, "wrong_served": False, "false_refusal": True, "refusal_class": "UNSPECIFIC",
         "served_quantities": {}, "technical_failure": False},
        {"type": "row", "case_id": "H1-S01", "arm": "HYBRID", "expect": "SERVE", "served": True,
         "served_correct": True, "wrong_served": False, "false_refusal": False, "refusal_class": None,
         "served_quantities": {"volume": ["12"]}, "technical_failure": False},
        {"type": "row", "case_id": "H1-R01", "arm": "LLM_ONLY", "expect": "REFUSE", "served": False,
         "served_correct": False, "wrong_served": False, "false_refusal": False, "refusal_reason_correct": False,
         "refusal_class": "UNSPECIFIC", "served_quantities": {}, "technical_failure": False},
        {"type": "row", "case_id": "H1-R01", "arm": "HYBRID", "expect": "REFUSE", "served": False,
         "served_correct": False, "wrong_served": False, "false_refusal": False, "refusal_reason_correct": True,
         "refusal_class": "CONTRADICTORY_DATA", "served_quantities": {}, "technical_failure": False},
    ]
    md = S.render_paired_comparison_table(corpus, rows)
    assert "| Case | H-1 Oracle | LLM_ONLY | HYBRID | Comparison |" in md
    assert "| `H1-S01` |" in md and "HYBRID_ONLY_CORRECT" in md
    assert "| `H1-R01` |" in md and "BOTH_REFUSED" in md
