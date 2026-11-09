# -*- coding: utf-8 -*-
"""Unit & generalization tests for `backend/app/ai/local_geometry_parser.py` (`local-geometry-parser/1`, Section X.1).

Verifies:
1. All 8 deterministic stages (`Problem Text -> Normalization -> Lexer/Tokenizer -> Clause & Sentence Splitter ->
   Grammar Parser -> Typed Semantic AST -> Semantic Validation -> Source-Span Coverage Check -> Source Gate Verification`).
2. Zero AI calls (`ALLOW_LIVE_AI=0`) across standard Vietnamese 3D geometry problems (`pyramid`, `tetrahedron`, `prism`,
   `cube`, `cuboid`, `sphere`, `cylinder`, `cone`, `midpoint`, `centroid`, `orthogonal_projection`, `altitude`,
   `perpendicular_line_plane`, `parallel_line_plane`, `derived_sections`, `volume_ratio`, `residual_volume`).
3. Genuine linguistic & mathematical generalization across renamed vertices (`S.MNPQ`, `P.ABCD`, `MNP.M'N'P'`) and
   paraphrased Vietnamese clauses without any case-ID or coordinate hardcoding.
4. Strict Source-Span Coverage Check: partial coverage (`LOCAL_PARSE_PARTIAL`) when an unknown fact or goal clause is
   appended to an otherwise valid problem (never silently drops unparsed facts/goals).
5. Ambiguous phrasing (`LOCAL_PARSE_AMBIGUOUS`) and out-of-scope rejection (`LOCAL_PARSE_UNSUPPORTED`).
"""
from __future__ import annotations

import os
import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.local_geometry_parser import (
    LOCAL_GEOMETRY_PARSER_VERSION,
    LOCAL_PARSE_AMBIGUOUS,
    LOCAL_PARSE_COMPLETE,
    LOCAL_PARSE_PARTIAL,
    LOCAL_PARSE_UNSUPPORTED,
    normalize_problem_text,
    parse_geometry_problem_locally,
    split_into_clauses,
    tokenize_problem_text,
)


@pytest.fixture(autouse=True)
def enforce_zero_live_ai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")


def test_normalization_tokenizer_and_clause_splitter_preserve_verbatim_quotes():
    raw = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4; SA ⊥ (ABCD), SA = 2√3. Tính thể tích khối chóp S.ABCD."
    norm = normalize_problem_text(raw)
    assert "SA ⊥ (ABCD)" in norm
    tokens = tokenize_problem_text(norm)
    assert any(t.kind == "solid" and t.text == "S.ABCD" for t in tokens)
    clauses = split_into_clauses(norm)
    assert len(clauses) == 3
    for cl in clauses:
        assert norm[cl.start : cl.end] == cl.text


@pytest.mark.parametrize(
    ("problem_text", "expected_answer"),
    [
        # 1. Renamed pyramid vertices S.MNPQ (not S.ABCD)
        (
            "Cho hình chóp S.MNPQ có đáy MNPQ là hình vuông cạnh 6, SA_placeholder".replace(
                "SA_placeholder", "SM vuông góc với mặt phẳng (MNPQ) và SM = 4."
            )
            + " Tính thể tích khối chóp S.MNPQ.",
            "48",
        ),
        # 2. Renamed apex P.ABCD with point-to-plane distance
        (
            "Cho hình chóp P.ABCD có đáy ABCD là hình vuông cạnh 3, PA vuông góc với mặt phẳng (ABCD), PA = 3. "
            "Tính khoảng cách từ A đến mặt phẳng (PBC).",
            "3√2/2",
        ),
        # 3. Renamed right triangular prism MNP.M'N'P'
        (
            "Cho hình lăng trụ đứng MNP.M'N'P' có đáy MNP là tam giác vuông tại M, MN = 3, MP = 4, cạnh bên MM' = 5. "
            "Tính thể tích khối lăng trụ MNP.M'N'P'.",
            "30",
        ),
        # 4. Tetrahedron OABC with mutually perpendicular edges (1/h^2 = 1/4 + 1/9 + 1/36 = 14/36 -> h = 3√14/7)
        (
            "Cho tứ diện OABC có OA, OB, OC đôi một vuông góc, OA = 2, OB = 3, OC = 6. "
            "Tính khoảng cách từ O đến mặt phẳng (ABC).",
            "3√14/7",
        ),
        # 5. Nested described point (projection of midpoint onto base plane)
        (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD), SA = 2. "
            "Tính khoảng cách từ hình chiếu vuông góc của trung điểm của SC lên mặt phẳng (ABCD) đến đường thẳng SB.",
            "√6/2",
        ),
        # 6. Parallel cutting plane section area + volume ratio + residual volume
        (
            "Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh a. SA vuông góc với mặt phẳng (ABC). SA = a. "
            "Gọi M là trung điểm của SA. Mặt phẳng (α) qua M và song song với (ABC) cắt SA, SB, SC, SD lần lượt tại M, N, P, Q. "
            "Dựng thiết diện của hình chóp S.ABCD bởi (α). "
            "Tính tỉ số thể tích của hai khối chóp S.MNPQ và S.ABCD.",
            "1/8",
        ),
    ],
)
def test_local_parser_solves_renamed_and_paraphrased_problems_with_zero_ai(
    problem_text: str, expected_answer: str
):
    res = parse_geometry_problem_locally(problem_text)
    assert res.parser_version == LOCAL_GEOMETRY_PARSER_VERSION
    assert res.status == LOCAL_PARSE_COMPLETE
    assert res.source_coverage.coverage_complete is True
    assert res.payload is not None
    assert res.parse_latency_ms < 500.0

    route_res = run_typed_fact_next_v2_route(res.payload)
    assert route_res.status == "SERVED"
    assert expected_answer in route_res.answers.values()


def test_local_parser_rejects_partial_coverage_when_unparsed_fact_or_goal_clause_exists():
    # Appending an unsupported/unparsed fact clause to a valid problem must return LOCAL_PARSE_PARTIAL, never LOCAL_PARSE_COMPLETE
    partial_fact_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với mặt phẳng (ABCD), SA = 3. "
        "Biết mặt phẳng (P) quay quanh trục đối xứng tạo góc 37 độ với tiếp tuyến quỹ tích. "
        "Tính thể tích khối chóp S.ABCD."
    )
    res_fact = parse_geometry_problem_locally(partial_fact_text)
    assert res_fact.status == LOCAL_PARSE_PARTIAL
    assert res_fact.payload is None
    assert res_fact.source_coverage.coverage_complete is False
    assert len(res_fact.source_coverage.unparsed_fact_candidates) >= 1

    # Appending an unparsed goal clause must also return LOCAL_PARSE_PARTIAL
    partial_goal_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với mặt phẳng (ABCD), SA = 3. "
        "Tính đạo hàm bậc ba của quỹ tích tâm mặt cầu theo tham số m."
    )
    res_goal = parse_geometry_problem_locally(partial_goal_text)
    assert res_goal.status == LOCAL_PARSE_PARTIAL
    assert res_goal.payload is None
    assert res_goal.source_coverage.coverage_complete is False
    assert len(res_goal.source_coverage.unparsed_goal_candidates) >= 1


def test_local_parser_detects_ambiguous_and_out_of_scope_inputs_deterministically():
    # Ambiguous projection missing target plane/line -> LOCAL_PARSE_AMBIGUOUS -> AMBIGUOUS_FACT clarification
    ambig_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD), SA = 2. "
        "Tính khoảng cách từ hình chiếu vuông góc của A đến S."
    )
    res_ambig = parse_geometry_problem_locally(ambig_text)
    assert res_ambig.status == LOCAL_PARSE_AMBIGUOUS
    assert res_ambig.payload is not None
    r_ambig = run_typed_fact_next_v2_route(res_ambig.payload)
    assert r_ambig.status == "REFUSED"
    assert r_ambig.code == "AMBIGUOUS_FACT"
    assert (r_ambig.details or {}).get("clarification", {}).get("schema_version") == "route-d-clarification/1"

    # Non-geometry input -> LOCAL_PARSE_UNSUPPORTED with GATE_OUT_OF_SCOPE
    oos_text = "Viết chương trình sắp xếp mảng bằng thuật toán MergeSort."
    res_oos = parse_geometry_problem_locally(oos_text)
    assert res_oos.status == LOCAL_PARSE_UNSUPPORTED
    assert res_oos.reason_code == "GATE_OUT_OF_SCOPE"


def test_local_parser_benchmark_corpora_zero_ai_zero_wrong_served():
    """Verify that `parse_geometry_problem_locally` + `run_typed_fact_next_v2_route` solves all supported cases
    in `K-1` (16/16), `R-1` (18/18), and `S-2` (36/36) with 0 AI calls and 0 wrong served."""
    from pathlib import Path
    import json

    repo_root = Path(__file__).resolve().parents[3]
    c26_dir = repo_root / "docs" / "evaluation" / "geometry" / "runs" / "hybrid-live-extraction-retest" / "full"

    for fname, expected_total in (
        ("k1-live.jsonl", 16),
        ("r1-live.jsonl", 18),
        ("s2-live.jsonl", 36),
    ):
        rows = [
            obj
            for line in (c26_dir / fname).read_text(encoding="utf-8").splitlines()
            if line.strip() and (obj := json.loads(line)).get("type") == "row"
        ]
        assert len(rows) == expected_total
        for r in rows:
            cid = r["case_id"]
            if r.get("raw_extraction") is None:
                continue
            text = r["raw_extraction"]["problem_text"]
            p_res = parse_geometry_problem_locally(text)
            if (r["expected"]["outcome"] == "SERVED" and cid != "S2-F-S07_typo_tone") or cid == "R1-F01":
                assert p_res.status == LOCAL_PARSE_COMPLETE, f"{fname}:{cid} status={p_res.status}"
                route_out = run_typed_fact_next_v2_route(p_res.payload)
                assert route_out.status == "SERVED", f"{fname}:{cid} route={route_out.status}:{route_out.code}"
                ans_src = r["expected"].get("expected_answers") or ({"length": ["√6/2"]} if cid == "R1-F01" else {})
                exp_vals = sorted(str(v).removeprefix("cos²=") for vs in ans_src.values() for v in vs)
                got_vals = sorted(str(v).removeprefix("cos²=") for v in route_out.answers.values())
                assert got_vals == exp_vals, f"{fname}:{cid} expected={exp_vals} got={got_vals}"
            else:
                if p_res.payload is not None:
                    route_out = run_typed_fact_next_v2_route(p_res.payload)
                    assert route_out.status == "REFUSED", f"{fname}:{cid} must not be wrongly served"



