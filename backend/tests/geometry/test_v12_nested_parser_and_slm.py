from __future__ import annotations

import json
import pytest

from app.ai.local_geometry_parser import (
    LOCAL_GEOMETRY_PARSER_VERSION,
    LOCAL_PARSE_AMBIGUOUS,
    LOCAL_PARSE_COMPLETE,
    LOCAL_PARSE_PARTIAL,
    parse_geometry_problem_locally,
)
from app.ai.local_slm_extractor import (
    LOCAL_SLM_EXTRACTOR_V9_VERSION,
    SLM_GROUNDING_VALIDATOR_V9_VERSION,
    V9_CLOSURE_MODE,
    _build_compact_clause_messages,
    build_compact_clause_context,
    build_compact_grammar_for_context,
    index_source_clauses,
    is_simulation_only_source,
    run_local_slm_extraction,
    simulation_request_span,
    validate_and_lower_compact_clause,
)
from app.ai.local_slm_runtime import LocalSlmInferenceResult
from app.simulation.geometry_functions import planner, registry
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2


def _gate_ok(payload: dict, raw_text: str) -> None:
    b = bridge_v2(payload)
    p = planner.lap_ke_hoach({"facts": b["facts"]}, raw_text)
    doc_q = tuple(
        q for g in (*p.goals, *p.negated) if g.get("call") for q in g["call"]["source"]["quotes"]
    )
    calls = registry.doc_ke_hoach({"calls": p.calls})
    tok = registry._CHINH_SACH_XUAT.set(b["bridge"].get("output_policies"))
    try:
        registry.kiem_nguon(calls, raw_text, tuple(p.auxiliary), doc_q)
    finally:
        registry._CHINH_SACH_XUAT.reset(tok)


@pytest.mark.parametrize(
    "text, expected_sim_goals, expected_math_goals",
    [
        ("Chỉ cần vẽ hình, không cần tính toán: hình chóp S.ABC có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4, SA vuông góc với (ABC) và SA = 6.", 1, 0),
        ("Cho hình lập phương ABCD.EFGH có cạnh 4. Hãy dựng hình 3D của hình lập phương này.", 1, 0),
        ("Hãy vẽ giúp em hình chóp tam giác đều S.ABC, cạnh đáy bằng 2a, cạnh bên bằng 3a.", 1, 0),
        ("Cho khối lăng trụ tam giác đều ABC.A'B'C' có tất cả các cạnh bằng a. Biểu diễn khối lăng trụ đã cho.", 1, 0),
        ("Một hình chóp S.ABCD có đáy là hình vuông ABCD cạnh 3cm, cạnh SA vuông góc với đáy và SA = 4cm. Em hãy mô phỏng hình chóp đó.", 1, 0),
        ("Vẽ khối chóp S.ABCD, đáy ABCD là hình thoi cạnh 2, góc ABC = 60°, SA ⊥ (ABCD), SA = 3.", 1, 0),
        ("Mô phỏng hình chóp đều S.ABCD với đáy là hình vuông cạnh 2a và chiều cao bằng a.", 1, 0),
        ("Cho hình chóp S.ABC có đáy ABC là tam giác cân tại B với BA = BC = a, góc ABC bằng 120°, SB vuông góc với đáy, SB = a. Vẽ hình chóp.", 1, 0),
        ("Hãy dựng hình chóp S.ABCD có đáy là hình chữ nhật với AB = 3, BC = 4; cạnh bên SA vuông góc với đáy, SA = 5. Không cần tính gì thêm.", 1, 0),
        ("Hình chóp S.ABCD có ABCD là hình vuông cạnh 4, SA vuông góc mặt đáy, SA = 4; điểm N nằm trên cạnh SD với SN = 3ND. Hãy vẽ hình chóp và điểm N.", 1, 0),
        ("Dựng hình chóp tứ giác đều S.MNPQ có tất cả các cạnh bằng 2.", 1, 0),
        ("Hãy mô phỏng khối hộp chữ nhật ABCD.A'B'C'D' biết AB = a, AD = a√2, AA' = a√3.", 1, 0),
        ("Em muốn xem hình chóp S.ABC có đáy là tam giác ABC vuông cân tại A, AB = AC = 2 và SA vuông góc với đáy, SA = 2.", 1, 0),
        ("Mo phong hinh lap phuong ABCD.A'B'C'D' canh 2.", 1, 0),
        ("Hay dung hinh chop S.ABC co day ABC la tam giac deu canh a, SA vuong goc voi day, SA = 2a.", 1, 0),
        ("Vẽ hình lập phương ABCD.A'B'C'D' cạnh 2 và tính độ dài đoạn AC'.", 1, 1),
        ("Cho hình chóp đều S.ABCD đáy ABCD là hình vuông cạnh 2, SA = 2; hãy dựng hình 3D rồi tính chiều cao của hình chóp.", 1, 1),
        ("Mô phỏng hình chóp S.ABCD có đáy là hình thoi ABCD cạnh a, góc BAD = 60°, SA vuông góc đáy, SA = a; tìm khoảng cách từ A đến (SCD).", 1, 1),
        ("Hinh chop S.ABCD co day ABCD la hinh vuong canh 2, SA vuong goc voi day, SA = 3. Tinh the tich khoi chop.", 1, 1),
    ],
)
def test_v12_parser_nested_compositional_and_source_gate(
    text: str, expected_sim_goals: int, expected_math_goals: int
) -> None:
    assert LOCAL_GEOMETRY_PARSER_VERSION == "local-geometry-parser/3"
    res = parse_geometry_problem_locally(text)
    assert res.status == LOCAL_PARSE_COMPLETE, f"Unexpected {res.status} ({res.reason_code}) for {text!r}"
    assert res.payload is not None
    assert len(res.payload.get("simulation_goals") or []) == expected_sim_goals
    assert len(res.payload.get("math_goals") or []) == expected_math_goals
    _gate_ok(res.payload, text)


def test_v12_parser_preserves_indirect_slm_target_and_ambiguity() -> None:
    s17 = "Hãy mô phỏng hình hộp chữ nhật ABCD.A'B'C'D' có đáy là hình vuông cạnh a và chiều cao 2a."
    res_s17 = parse_geometry_problem_locally(s17)
    assert res_s17.status == LOCAL_PARSE_PARTIAL

    amb = "Hãy mô phỏng hình chóp S.ABCD có đáy là hình vuông cạnh 2, SA vuông góc đáy, SA = 3 và biểu diễn khoảng cách từ A đến (SBC)."
    res_amb = parse_geometry_problem_locally(amb)
    assert res_amb.status == LOCAL_PARSE_AMBIGUOUS
    assert res_amb.reason_code == "AMBIGUOUS_FACT"


def test_v12_slm_clause_indexing_sim_only_and_prompt_canonicalization() -> None:
    assert LOCAL_SLM_EXTRACTOR_V9_VERSION == "local-slm-extractor/6"
    assert SLM_GROUNDING_VALIDATOR_V9_VERSION == "slm-grounding-validator/6"

    s09 = "Chỉ cần vẽ hình, không cần tính toán: hình chóp S.ABC có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4, SA vuông góc với (ABC) và SA = 6."
    cl_s09 = index_source_clauses(s09)
    assert len(cl_s09) == 1
    assert cl_s09[0].text.startswith("hình chóp S.ABC")
    ctx_s09 = build_compact_clause_context(s09)
    assert is_simulation_only_source(ctx_s09) is True

    s17 = "Hãy mô phỏng hình hộp chữ nhật ABCD.A'B'C'D' có đáy là hình vuông cạnh a và chiều cao 2a."
    ctx_s17 = build_compact_clause_context(s17)
    assert is_simulation_only_source(ctx_s17) is True
    assert simulation_request_span(ctx_s17.clauses, ctx_s17.working_text) is not None
    msgs_s17 = _build_compact_clause_messages(ctx_s17)
    assert "[0] Cho hình hộp chữ nhật ABCD.A'B'C'D'" in msgs_s17[1]["content"]
    gbnf_s17 = build_compact_grammar_for_context(ctx_s17, closure_mode=V9_CLOSURE_MODE)
    assert "root ::=" in gbnf_s17
    assert '\\"reg_poly\\"' in gbnf_s17 and '\\"height\\"' in gbnf_s17

    q_inline = "Hãy mô phỏng hình chóp S.ABC có đáy là tam giác đều cạnh 2a, SA ⊥ (ABC), SA = a, rồi tính thể tích khối chóp."
    cl_q = index_source_clauses(q_inline)
    assert len(cl_q) == 2
    assert cl_q[1].text.startswith("tính thể tích")
    assert is_simulation_only_source(build_compact_clause_context(q_inline)) is False


def test_v12_slm_lowering_s17_q05_and_diacritic_quote_restoration() -> None:
    s17 = "Hãy mô phỏng hình hộp chữ nhật ABCD.A'B'C'D' có đáy là hình vuông cạnh a và chiều cao 2a."
    ctx_s17 = build_compact_clause_context(s17)
    raw_s17 = {
        "s": [0, "box", "ABCD.A'B'C'D'", 1],
        "r": [
            {"c": 0, "p": "reg_poly", "a": "ABCD", "q": "a"},
            {"c": 0, "p": "height", "a": "ABCD.A'B'C'D'", "q": "2a"},
        ],
        "g": [],
        "u": [],
    }
    low_s17, diag_s17 = validate_and_lower_compact_clause(ctx=ctx_s17, raw_slm_json=raw_s17, closure_mode=V9_CLOSURE_MODE)
    assert low_s17 is not None and diag_s17["grounding_status"] == "GROUNDED_AND_LOWERED"
    _gate_ok(low_s17, s17)

    q05 = "Vẽ hình chóp đều S.ABCD đáy ABCD là hình vuông cạnh 2, SA = 2 và tính chiều cao của hình chóp."
    ctx_q05 = build_compact_clause_context(q05)
    gbnf_q05 = build_compact_grammar_for_context(ctx_q05, closure_mode=V9_CLOSURE_MODE)
    assert "dist_pt_plane" in gbnf_q05
    raw_q05 = {
        "s": [0, "pyr", "S.ABCD", 1],
        "r": [
            {"c": 0, "p": "reg_poly", "a": "ABCD", "q": "2"},
            {"c": 0, "p": "len", "a": "SA", "q": "2"},
        ],
        "g": [{"c": 1, "t": "dist_pt_plane", "a": "S", "b": "ABCD"}],
        "u": [],
    }
    low_q05, diag_q05 = validate_and_lower_compact_clause(ctx=ctx_q05, raw_slm_json=raw_q05, closure_mode=V9_CLOSURE_MODE)
    assert low_q05 is not None and diag_q05["grounding_status"] == "GROUNDED_AND_LOWERED"
    _gate_ok(low_q05, q05)

    class _FakeRuntime:
        def __init__(self, obj: dict) -> None:
            self._obj = obj

        def chat_completion_json(self, **kwargs):
            return LocalSlmInferenceResult(
                raw_content=json.dumps(self._obj, ensure_ascii=False),
                parsed_json=self._obj,
                model_key="fake-v9",
                model_sha256="deadbeef",
                runtime_version="fake/1",
                server_load_time_ms=0.0,
                inference_time_ms=1.0,
                prompt_tokens=100,
                completion_tokens=40,
                thinking_stripped=False,
                server_restarted=False,
                python_rss_mib=50.0,
                server_rss_mib=0.0,
                combined_rss_mib=50.0,
                server_peak_rss_mib=0.0,
                threads=4,
                ctx_size=2048,
            )

    ascii_prompt = "Hinh chop S.ABCD co day ABCD la hinh vuong canh 2, SA vuong goc voi day, SA = 3. Tinh the tich khoi chop."
    res_ascii = run_local_slm_extraction(
        ascii_prompt,
        closure_mode=V9_CLOSURE_MODE,
        use_cache=False,
        runtime=_FakeRuntime({
            "s": [0, "pyr", "S.ABCD", 0],
            "r": [
                {"c": 0, "p": "reg_poly", "a": "ABCD", "q": "2"},
                {"c": 0, "p": "perp_lp", "a": "SA", "b": "ABCD"},
                {"c": 0, "p": "len", "a": "SA", "q": "3"},
            ],
            "g": [{"c": 1, "t": "vol", "tgt": "S.ABCD"}],
            "u": [],
        }),
    )
    assert res_ascii.ok and res_ascii.canonical_payload is not None
    for coll_key in ("solids", "premises", "simulation_goals", "math_goals"):
        for item in res_ascii.canonical_payload.get(coll_key) or ():
            assert item["quote"] in ascii_prompt
    _gate_ok(res_ascii.canonical_payload, ascii_prompt)

    res_a3 = run_local_slm_extraction(
        "Cho hình chóp S.ABC có đáy là tam giác đều cạnh 2, SA = 3 vuông góc đáy và biểu diễn khoảng cách từ A đến (SBC).",
        closure_mode=V9_CLOSURE_MODE,
        use_cache=False,
        runtime=_FakeRuntime({}),
    )
    assert res_a3.ok is False and res_a3.reason_code == "AMBIGUOUS_FACT"
