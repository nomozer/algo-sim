from __future__ import annotations

import pytest

from app.ai.compositional_clause_analysis import (
    COMPOSITIONAL_CLAUSE_ANALYZER_VERSION,
    ROLE_CONDITIONAL_PREMISE,
    ROLE_CONTEXT_HEADER,
    ROLE_MEASUREMENT_REQUEST,
    ROLE_NEGATED_REQUEST,
    ROLE_OBJECT_DECLARATION,
    ROLE_SIMULATION_REQUEST,
    ROLE_VISUALIZATION_REQUEST,
    analyze_compositional_geometry,
    build_source_span_provenance_records,
    normalize_with_spans,
)


def test_span_preserving_normalization_unicode_crlf_and_spaces():
    # NFD + CRLF + tabs/double-spaces + Δ notation + degree symbol º
    raw = "Ve\u0303   hi\u0300nh cho\u0301p   S.ABC\r\nco\u0301  ΔABC  đê\u0300u   ca\u0323nh 2a, go\u0301c 60º."
    mapped = normalize_with_spans(raw)
    assert "tam giác ABC" in mapped.normalized_text
    assert "60°" in mapped.normalized_text
    assert "  " not in mapped.normalized_text
    assert "\r" not in mapped.normalized_text
    # Every normalized slice maps back cleanly into an exact original substring
    idx = mapped.normalized_text.index("S.ABC")
    q = mapped.orig_quote(idx, idx + 5)
    assert q == "S.ABC"
    # Even across NFD accented characters and collapsed spaces, orig_quote stays strictly inside raw
    oa, ob = mapped.orig_span(0, len(mapped.normalized_text))
    assert raw[oa:ob] == raw.strip()


def test_diacritic_free_projection_preserves_original_quotes_and_blocks_decoys():
    raw = "Mo phong hinh lap phuong ABCD.A'B'C'D' canh 2."
    ana = analyze_compositional_geometry(raw)
    assert ana.mapped.diacritic_projected is True
    assert ana.has_simulation_request is True
    assert ana.is_simulation_only_intent is True
    # Quotes MUST remain verbatim slices of `raw` (not synthesized accented forms)
    for cl in ana.clauses:
        assert raw[cl.orig_start:cl.orig_end] == cl.orig_text
        assert cl.orig_text in raw
        assert "mô phỏng" not in cl.orig_text.lower()

    # Out-of-domain decoys must NOT trigger diacritic projection
    for decoy in (
        "Cho mang hinh chu nhat 3x4, tim duong di ngan nhat.",
        "Tinh goc quay con lac lo xo co bien do 4cm.",
        "Tim canh nho nhat trong do thi bang thuat toan Kruskal.",
    ):
        d = analyze_compositional_geometry(decoy)
        assert d.mapped.diacritic_projected is False
        assert d.mapped.ambiguous_diacritic_blocked is True


def test_nested_declaration_with_and_without_trailing_metric_goal():
    s_with_goal = "Câu 2 (2 điểm). Vẽ hình chóp S.ABCD có đáy ABCD là hình vuông, SA vuông góc với (ABCD), SA = 2a, AB = a và tính thể tích!"
    ana1 = analyze_compositional_geometry(s_with_goal)
    roles1 = [c.role for c in ana1.clauses]
    assert roles1 == [
        ROLE_CONTEXT_HEADER,
        ROLE_SIMULATION_REQUEST,
        ROLE_OBJECT_DECLARATION,
        ROLE_MEASUREMENT_REQUEST,
    ]
    assert ana1.has_simulation_request is True
    assert ana1.has_measurement_request is True
    assert ana1.is_simulation_only_intent is False
    assert ana1.is_mixed_simulation_and_query is True
    assert "tính thể tích" in ana1.clauses[-1].orig_text
    assert "hình chóp S.ABCD có đáy" in ana1.clauses[2].orig_text

    s_sim_only = "Hãy dựng hình chóp S.ABCD có đáy là hình chữ nhật với AB = 3cm, BC = 4cm; cạnh bên SA vuông góc với đáy, SA = 5cm. Không cần tính gì thêm."
    ana2 = analyze_compositional_geometry(s_sim_only)
    assert ana2.has_simulation_request is True
    assert ana2.has_measurement_request is False
    assert ana2.has_meta_no_calc is True
    assert ana2.is_simulation_only_intent is True
    assert any(c.role == ROLE_NEGATED_REQUEST and c.subkind == "meta_no_calc" for c in ana2.clauses)

    s_leading_meta = "Chỉ cần vẽ hình, không cần tính toán: hình chóp S.ABC có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4, SA vuông góc với (ABC) và SA = 6."
    ana3 = analyze_compositional_geometry(s_leading_meta)
    assert ana3.has_meta_no_calc is True
    assert ana3.has_simulation_request is True
    assert ana3.is_simulation_only_intent is True
    assert any(c.role == ROLE_OBJECT_DECLARATION and "hình chóp S.ABC" in c.orig_text for c in ana3.clauses)


def test_negation_and_conditional_scoping_never_promote_to_positive_premise():
    c_neg_p = analyze_compositional_geometry("Không có SA vuông góc với (ABCD).")
    assert c_neg_p.has_negated_premise is True
    assert c_neg_p.is_simulation_only_intent is False

    c_neg_cmd = analyze_compositional_geometry("Không mô phỏng hình chóp S.ABCD có đáy là hình vuông cạnh a.")
    assert c_neg_cmd.has_negated_command is True
    assert c_neg_cmd.has_simulation_request is False

    c_cond = analyze_compositional_geometry("Nếu đáy ABCD là hình vuông thì hãy vẽ hình chóp S.ABCD với SA = a.")
    assert c_cond.has_conditional_premise is True
    assert any(c.role == ROLE_CONDITIONAL_PREMISE for c in c_cond.clauses)
    assert c_cond.is_simulation_only_intent is False

    # Contrast: "Em muốn xem..." MUST NOT be misclassified as conditional!
    c_want = analyze_compositional_geometry("Em muốn xem hình chóp S.ABC có đáy là tam giác vuông tại A, AB = AC = 2, SA = 2.")
    assert c_want.has_conditional_premise is False
    assert c_want.has_simulation_request is True
    assert c_want.is_simulation_only_intent is True


def test_visualization_vs_measurement_disambiguation_a3_and_provenance_records():
    # Ambiguous without "tính": must flag AMBIGUOUS_DISTANCE_OR_ANGLE_VISUALIZATION and not invent measurement role
    a1 = analyze_compositional_geometry("Biểu diễn khoảng cách từ điểm S đến mặt phẳng (ABCD).")
    assert len(a1.ambiguous_visualization_clauses) == 1
    assert a1.ambiguous_visualization_clauses[0].role == ROLE_VISUALIZATION_REQUEST
    assert a1.has_measurement_request is False

    # Concrete named visualization + explicit calc: no ambiguity
    a2 = analyze_compositional_geometry("Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2, đường cao SA = 3. Biểu diễn đường cao SA và tính thể tích.")
    assert len(a2.ambiguous_visualization_clauses) == 0
    assert a2.has_measurement_request is True

    # 11-field SourceSpanProvenanceRecord verification
    records = build_source_span_provenance_records(a2, payload={"solids": [], "premises": [], "math_goals": [], "simulation_goals": []})
    assert len(records) == len(a2.clauses)
    for rec in records:
        d = rec.as_dict()
        for field in (
            "original_text", "original_offsets", "normalized_text", "normalized_offsets",
            "clause_boundaries", "clause_role", "quoted_source_span", "entity_binding",
            "extracted_fact", "grounding_verdict", "subkind",
        ):
            assert field in d
        assert a2.mapped.original_text[d["original_offsets"][0]:d["original_offsets"][1]] == d["quoted_source_span"]
