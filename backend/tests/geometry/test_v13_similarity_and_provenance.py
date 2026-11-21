"""AXO HYBRID /13 tests for §17 Unit Similarity and §19 Polygon Center & Point O Provenance."""
from __future__ import annotations

import pytest

from app.ai import adaptive_input_router as AIR
from app.ai.adaptive_input_router import route_text_input, route_text_input_local_slm
from app.ai.function_route import run_function_route
from app.ai.local_geometry_parser import parse_geometry_problem_locally
from app.ai.local_slm_extractor import (
    LocalSlmExtractionResult,
    V9_CLOSURE_MODE,
    build_compact_clause_context,
    validate_and_lower_compact_clause,
)
from app.simulation.geometry_functions import engine, planner, registry
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2


def _point_o_decls_and_stmts(text: str, point_label: str = "O"):
    lp = parse_geometry_problem_locally(text)
    assert lp.status == "LOCAL_PARSE_COMPLETE" and lp.payload is not None, lp.to_dict()
    b = bridge_v2(lp.payload)
    p = planner.lap_ke_hoach({"facts": b["facts"]}, text)
    tok = registry._CHINH_SACH_XUAT.set(b["bridge"].get("output_policies"))
    try:
        kr = engine.dung_tu_loi_goi(
            text,
            {"calls": p.calls},
            auxiliary=tuple(p.auxiliary),
            read_quotes=tuple(q for g in (*p.goals, *p.negated) if g.get("call") for q in g["call"]["source"]["quotes"]),
        )
    finally:
        registry._CHINH_SACH_XUAT.reset(tok)
    assert kr.status == "SERVED", kr
    sp = kr.spec.model_dump() if hasattr(kr.spec, "model_dump") else kr.spec
    decls = {d["name"]: d for d in (sp.get("memory_declarations") or [])}
    stmts = [s for s in (sp.get("statements") or []) if s.get("target_var") == point_label]
    return kr, decls, stmts


# ── §17 Unit Similarity ───────────────────────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "text",
    [
        "Vẽ hình lập phương ABCD.A'B'C'D'.",
        "Dựng hình tứ diện đều ABCD.",
        "Vẽ tứ diện đều O.ABC.",
        "Mô phỏng hình chóp tứ giác đều S.ABCD có tất cả các cạnh bằng nhau.",
        "Mô phỏng hình lăng trụ tam giác đều ABC.A'B'C' có các cạnh đều bằng nhau.",
    ],
)
def test_similarity_serves_1dof_simulate_only_with_representative_policy(text: str) -> None:
    out = route_text_input(text, allow_live_ai=False)
    assert out.status == "SERVED", out.response
    rd = out.response["route_d"]
    assert rd.get("scale_policy") == "UNIT_SIMILARITY_REPRESENTATIVE"
    assert rd.get("answers") == {}
    assert rd.get("scene_configuration", {}).get("kind") == "SIMILARITY_SCALE_ILLUSTRATIVE"
    scene = out.response["envelope"]["scene3d"]
    assert any(o.get("type") == "solid" for o in scene["objects"])


@pytest.mark.parametrize(
    "text",
    [
        "Vẽ hình lập phương ABCD.A'B'C'D' và tính thể tích khối lập phương đó.",
        "Cho tứ diện đều ABCD. Tính khoảng cách từ A đến mặt phẳng (BCD).",
        "Cho hình chóp tứ giác đều S.ABCD có các cạnh bằng nhau. Tính diện tích toàn phần.",
        "Cho hình lập phương ABCD.A'B'C'D'. Tính diện tích một mặt.",
        "Hãy mô phỏng hình chóp S.ABCD có đáy ABCD là hình vuông và SA vuông góc với đáy.",
        "Mô phỏng hình lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều.",
        "Cho hình chóp S.ABC có đáy là tam giác vuông tại B và SA vuông góc với (ABC). Hãy vẽ hình.",
        "Mô phỏng hình chóp tứ giác đều S.ABCD có các cạnh bên bằng nhau.",
    ],
)
def test_similarity_refuses_metric_queries_and_multi_dof_solids(text: str) -> None:
    out = route_text_input(text, allow_live_ai=False)
    assert out.status == "REFUSED", (text, out.response)
    rd = out.response["route_d"]
    assert rd.get("scale_policy") is None


def test_similarity_unitless_tetrahedron_slm_lowering() -> None:
    text = "Dựng tứ diện đều M.NPQ không cần tính toán."
    ctx = build_compact_clause_context(text)
    payload, env = validate_and_lower_compact_clause(
        ctx=ctx,
        raw_slm_json={"s": [0, "pyr", 0, 1], "r": [], "g": []},
        closure_mode=V9_CLOSURE_MODE,
    )
    assert payload is not None, env
    prems = payload["premises"]
    assert any(p["kind"] == "regular_polygon" and p["args"].get("side") is None for p in prems)
    assert any(p["kind"] == "equal_length" for p in prems)


# ── §19 Derived Point O & Polygon Center Provenance ───────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "text,expected_expr_kind",
    [
        ("Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 2, cạnh bên bằng 3.", "divide_segment"),
        ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 2, cạnh bên bằng 3.", "midpoint"),
        ("Cho hình chóp lục giác đều S.ABCDEF có cạnh đáy bằng 2, cạnh bên bằng 3.", "midpoint"),
    ],
)
def test_implicit_point_o_never_uses_layout_derived(text: str, expected_expr_kind: str) -> None:
    _kr, decls, stmts = _point_o_decls_and_stmts(text, "O")
    assert "O" in decls
    assert decls["O"].get("provenance") != "LAYOUT_DERIVED"
    assert len(stmts) == 1 and stmts[0]["kind"] == "construct_point"
    assert stmts[0]["expr"]["kind"] == expected_expr_kind


def test_existing_center_label_reused_without_phantom_o() -> None:
    text = "Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 2, cạnh bên bằng 3. Gọi G là trọng tâm tam giác ABC."
    kr, decls, _stmts = _point_o_decls_and_stmts(text, "G")
    assert "G" in decls
    assert decls["G"].get("provenance") != "LAYOUT_DERIVED"
    assert "O" not in decls
    sp = kr.spec.model_dump() if hasattr(kr.spec, "model_dump") else kr.spec
    layout_derived = {d["name"] for d in sp.get("memory_declarations", []) if d.get("provenance") == "LAYOUT_DERIVED"}
    assert layout_derived <= {"A", "B", "C", "S"}


@pytest.mark.parametrize(
    "text,expected_answer",
    [
        (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2. Gọi O là tâm của đáy, SO vuông góc với (ABCD), SO = 3. Tính thể tích khối chóp S.ABCD.",
            "4",
        ),
        (
            "Cho hình chóp S.ABCD có đáy là hình chữ nhật ABCD, AB = 2, AD = 4. Gọi O là tâm đáy, SO vuông góc với (ABCD), SO = 3. Tính thể tích khối chóp S.ABCD.",
            "8",
        ),
        (
            "Cho hình chóp S.ABCD có đáy là hình thoi ABCD cạnh 2, góc BAD bằng 60 độ. Gọi O là tâm đáy, SO vuông góc với đáy, SO = 3. Tính thể tích khối chóp S.ABCD.",
            "2√3",
        ),
        (
            "Cho hình chóp S.ABCD có đáy ABCD là hình bình hành tâm O, AB = 2, AD = 3, góc BAD bằng 60°, SO vuông góc với (ABCD), SO = 2. Tính thể tích khối chóp S.ABCD.",
            "2√3",
        ),
        (
            "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2. Gọi O là tâm đáy, SO vuông góc với (ABC), SO = 3. Tính thể tích khối chóp S.ABC.",
            "√3",
        ),
        (
            "Cho hình chóp S.ABCDEF có đáy là lục giác đều ABCDEF cạnh 2. Gọi O là tâm đáy, SO vuông góc với (ABCDEF), SO = 3. Vẽ hình.",
            None,
        ),
    ],
)
def test_explicit_polygon_center_positive_across_centrally_symmetric_and_equilateral_bases(
    text: str,
    expected_answer: str | None,
) -> None:
    out = route_text_input(text, allow_live_ai=False)
    assert out.status == "SERVED", (text, out.response)
    rd = out.response["route_d"]
    if expected_answer is not None:
        assert rd["answers"]["q1"] == expected_answer
    else:
        assert rd["answers"] == {}
    _kr, decls, stmts = _point_o_decls_and_stmts(text, "O")
    assert "O" in decls and decls["O"].get("provenance") != "LAYOUT_DERIVED"
    assert len(stmts) == 1 and stmts[0]["kind"] == "construct_point"


@pytest.mark.parametrize(
    "text",
    [
        "Cho hình chóp S.ABCD có đáy ABCD là hình thang, AD song song BC, AD = 4, BC = 2. Gọi O là tâm đáy, SO vuông góc với (ABCD), SO = 3. Vẽ hình.",
        "Cho hình chóp S.ABCD có đáy ABCD là hình thang cân có tâm O, SA vuông góc với (ABCD), SA = 2, AB = 2, AD = 4, BC = 2. Vẽ hình.",
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = 3, BC = 4. Gọi O là tâm tam giác ABC, SO vuông góc với (ABC), SO = 2. Vẽ hình.",
        "Cho hình chóp S.ABC có đáy là tam giác ABC, AB = 2, AC = 3, BC = 4. Gọi O là tâm tam giác ABC. Vẽ hình.",
    ],
)
def test_explicit_polygon_center_negative_on_trapezoid_and_non_equilateral_triangle(text: str) -> None:
    out = route_text_input(text, allow_live_ai=False)
    assert out.status == "REFUSED", (text, out.response)


def test_source_gate_rejects_forged_center_on_trapezoid_and_right_triangle() -> None:
    de_trap = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thang với AD song song BC. "
        "Gọi O là tâm đáy. Vẽ hình."
    )
    res_trap = run_function_route(
        de_trap,
        {
            "calls": [
                {"id": "p1", "function": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]},
                 "source": {"quotes": ["Cho hình chóp S.ABCD"]}},
                {"id": "p2", "function": "trapezoid", "args": {"vertices": ["A", "B", "C", "D"], "base_a": ["A", "D"], "base_b": ["B", "C"]},
                 "source": {"quotes": ["đáy ABCD là hình thang với AD song song BC"]}},
                {"id": "p3", "function": "midpoint", "args": {"point": "O", "segment": ["A", "C"]},
                 "source": {"quotes": ["Gọi O là tâm đáy"]}},
            ]
        },
    )
    assert res_trap.status == "REFUSED", res_trap

    de_tri = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B. "
        "Gọi O là tâm tam giác ABC. Vẽ hình."
    )
    res_tri = run_function_route(
        de_tri,
        {
            "calls": [
                {"id": "p1", "function": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]},
                 "source": {"quotes": ["Cho hình chóp S.ABC"]}},
                {"id": "p2", "function": "right_angle", "args": {"vertex": "B", "rays": ["A", "C"]},
                 "source": {"quotes": ["đáy ABC là tam giác vuông tại B"]}},
                {"id": "p3", "function": "centroid", "args": {"point": "O", "polygon": ["A", "B", "C"]},
                 "source": {"quotes": ["Gọi O là tâm tam giác ABC"]}},
            ]
        },
    )
    assert res_tri.status == "REFUSED", res_tri


def test_slm_lowering_explicit_center_positive_and_negative() -> None:
    pos = "Cho hình chóp S.ABCD có đáy là hình thoi ABCD cạnh 2, góc BAD = 60°. Gọi O là tâm đáy, SO vuông góc với đáy, SO = 3. Vẽ hình."
    ctx_pos = build_compact_clause_context(pos)
    c_rhom = next(c.clause_id for c in ctx_pos.clauses if "hình thoi" in c.text)
    c_ctr = next(c.clause_id for c in ctx_pos.clauses if "O là tâm đáy" in c.text)
    c_perp = next(c.clause_id for c in ctx_pos.clauses if "vuông góc" in c.text)
    e_poly = next(i for i, e in enumerate(ctx_pos.entities) if e.kind == "poly" and set(e.vertices) == {"A", "B", "C", "D"})
    e_o = next(i for i, e in enumerate(ctx_pos.entities) if e.kind == "point" and e.label == "O")
    e_so = next(i for i, e in enumerate(ctx_pos.entities) if e.kind == "seg" and set(e.vertices) == {"S", "O"})
    q_side = next(i for i, q in enumerate(ctx_pos.quantities) if q.canon_expr == "2")
    payload_pos, env_pos = validate_and_lower_compact_clause(
        ctx=ctx_pos,
        raw_slm_json={
            "s": [0, "pyr", 0, 0],
            "r": [
                {"c": c_rhom, "p": "rhom", "a": e_poly, "q": q_side},
                {"c": c_ctr, "p": "cent", "pt": e_o, "a": e_poly},
                {"c": c_perp, "p": "perp_lp", "a": e_so, "b": e_poly},
            ],
            "g": [],
        },
        closure_mode=V9_CLOSURE_MODE,
    )
    assert payload_pos is not None, env_pos
    assert any(p["kind"] == "midpoint" and p["args"]["point"] == "O" for p in payload_pos["premises"])

    neg = "Cho hình chóp S.ABCD có đáy ABCD là hình thang, AD song song BC. Gọi O là tâm đáy."
    ctx_neg = build_compact_clause_context(neg)
    c_neg = next(c.clause_id for c in ctx_neg.clauses if "O là tâm đáy" in c.text)
    e_npoly = next(i for i, e in enumerate(ctx_neg.entities) if e.kind == "poly" and set(e.vertices) == {"A", "B", "C", "D"})
    e_no = next(i for i, e in enumerate(ctx_neg.entities) if e.kind == "point" and e.label == "O")
    payload_neg, _env_neg = validate_and_lower_compact_clause(
        ctx=ctx_neg,
        raw_slm_json={
            "s": [0, "pyr", 0, 0],
            "r": [{"c": c_neg, "p": "cent", "pt": e_no, "a": e_npoly}],
            "g": [],
        },
        closure_mode=V9_CLOSURE_MODE,
    )
    assert payload_neg is None or not any(
        p["kind"] in ("midpoint", "centroid") and p["args"].get("point") == "O"
        for p in payload_neg["premises"]
    )


# ── §6.G Underdetermined Clarification Surfacing (I05 / VI06) ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "text,expect_proved_source_cat",
    [
        ("Hãy mô phỏng hình chóp S.ABCD có đáy ABCD là hình vuông và SA vuông góc với đáy.", False),
        ("Mô phỏng hình lăng trụ đứng ABC.A'B'C' có đáy là tam giác đều.", False),
        ("Cho hình chóp S.ABC có đáy là tam giác vuông tại B và SA vuông góc với (ABC). Hãy vẽ hình.", True),
        ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, cạnh bên SA = 3. Vẽ hình.", True),
    ],
)
def test_underdetermined_parser_prompts_surface_clarification_without_capability_gap(
    text: str,
    expect_proved_source_cat: bool,
) -> None:
    out = route_text_input(text, allow_live_ai=False)
    assert out.status == "REFUSED", out.response
    env = out.response["envelope"]
    rd = out.response["route_d"]
    if expect_proved_source_cat:
        assert env["failure_category"] == "insufficient_specification", env
        assert env["refusal_cause"] == "SOURCE", env
    clar = rd.get("clarification")
    assert isinstance(clar, dict) and clar.get("schema_version") == "route-d-clarification/1", rd
    assert clar.get("nlu_class") == "MISSING_DATA", clar
    assert isinstance(clar.get("question"), str) and clar["question"].strip()
    assert "chưa hỗ trợ" not in clar["question"].lower()
    assert "ngoài phạm vi" not in clar["question"].lower()
    assert rd["refusal"].get("clarification_question") == clar["question"]
    assert rd["refusal"].get("nlu_class") == clar["nlu_class"]


def test_underdetermined_slm_grounded_and_rejected_paths_surface_clarification(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.ai.local_slm_extractor as LSE

    text_foot = "Hãy vẽ giúp mình hình chóp S.ABCD với đáy ABCD là hình vuông cạnh 2, biết cạnh bên SA = 3."
    grounded_payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text_foot,
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "hình chóp S.ABCD"}],
        "premises": [
            {"kind": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "2"}, "quote": "đáy ABCD là hình vuông cạnh 2", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "3"}, "quote": "cạnh bên SA = 3", "solid_id": "s1"},
        ],
        "math_goals": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Hãy vẽ giúp mình hình chóp S.ABCD"}],
        "unresolved": [],
    }
    monkeypatch.setattr(
        LSE,
        "run_local_slm_extraction",
        lambda *_a, **_kw: LocalSlmExtractionResult(
            ok=True,
            strategy="compact_clause",
            model_key="qwen3-0.6b-axov9",
            model_sha256="test",
            norm_text=text_foot,
            wire_payload={},
            canonical_payload=grounded_payload,
            reason_code=None,
            reason_detail=None,
            failure_taxonomy="NONE",
            grounding_envelope={"grounding_status": "GROUNDED"},
        ),
    )
    out_grounded = route_text_input_local_slm(text_foot, closure_mode=V9_CLOSURE_MODE, normalizer_version="v3")
    assert out_grounded.status == "REFUSED", out_grounded.response
    assert out_grounded.response["envelope"]["failure_category"] == "insufficient_specification", out_grounded.response
    assert out_grounded.response["envelope"]["refusal_cause"] == "SOURCE"
    clar_g = out_grounded.response["route_d"].get("clarification")
    assert clar_g and clar_g["schema_version"] == "route-d-clarification/1"
    assert out_grounded.response["route_d"]["contract_version"] == "typed-fact-next/2"

    text_rej = "Vẽ hình chóp S.ABCD chưa rõ số đo đáy."
    monkeypatch.setattr(
        LSE,
        "run_local_slm_extraction",
        lambda *_a, **_kw: LocalSlmExtractionResult(
            ok=False,
            strategy="compact_clause",
            model_key="qwen3-0.6b-axov9",
            model_sha256="test",
            norm_text=text_rej,
            wire_payload=None,
            canonical_payload=None,
            reason_code="MISSING_DIMENSION",
            reason_detail="missing_dim",
            failure_taxonomy="GROUNDING_REJECTED",
            grounding_envelope={"grounding_status": "REJECTED_MISSING_OR_INVALID_SOLID"},
        ),
    )
    out_rej = route_text_input_local_slm(text_rej, closure_mode=V9_CLOSURE_MODE, normalizer_version="v3")
    assert out_rej.status == "REFUSED", out_rej.response
    assert out_rej.response["route_d"]["contract_version"] == "typed-fact-next/2"
    assert out_rej.response["envelope"]["failure_category"] == "insufficient_specification"
    assert out_rej.response["envelope"]["refusal_cause"] == "SOURCE"
    clar_r = out_rej.response["route_d"].get("clarification")
    assert clar_r and clar_r["schema_version"] == "route-d-clarification/1"
    assert "chưa hỗ trợ" not in clar_r["question"].lower()


@pytest.mark.parametrize("text", [
    "Mô phỏng hình hộp chữ nhật EFGH.E'F'G'H' có EF = 6.",
    "Dựng lăng trụ đứng MNP.M'N'P' có đáy là tam giác vuông tại M và MN = 6.",
])
def test_missing_base_size_and_prism_height_surface_clarification(text):
    out = route_text_input(text, allow_live_ai=False)
    assert out.status == "REFUSED"
    assert out.response["envelope"]["failure_category"] == "insufficient_specification"
    assert out.response["envelope"]["refusal_cause"] == "SOURCE"
    rd = out.response["route_d"]
    assert rd["determinacy_audit"]["status"] == "PROVED_UNDERDETERMINED"
    assert rd["clarification"]["nlu_class"] == "MISSING_DATA"
    assert rd["clarification"]["question"]
