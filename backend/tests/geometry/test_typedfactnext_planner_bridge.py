# -*- coding: utf-8 -*-
"""Run `typedfactnext-planner-bridge`: Source Gate / preview defects (P3) and the TypedFactNext → planner bridge (P2).

Expected values are closed-form (independent of the engine): a pyramid cut at SM/SA, SN/SB, SP/SC has
V(S.MNP)/V(S.ABC) = (SM/SA)(SN/SB)(SP/SC); an equilateral base of side s has area s²√3/4.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import re

import pytest

from app.ai.function_route import run_fact_route


def _square(coef: str) -> Fraction:
    """Independent reader of an exact display coefficient "p", "p/q", "p√r", "p√r/q", "√r/q"."""
    m = re.fullmatch(r"(?P<p>\d+)?(?:√(?P<r>\d+))?(?:/(?P<q>\d+))?", coef)
    assert m and (m["p"] or m["r"]), coef
    p, r, q = Fraction(m["p"] or 1), Fraction(m["r"] or 1), Fraction(m["q"] or 1)
    return p * p * r / (q * q)


SIMSON = ("Cho hình chóp S.ABC. Đáy ABC là tam giác đều cạnh 2a. SA vuông góc với (ABC). SA = 3a. "
          "Điểm M thuộc cạnh SA sao cho SM = 1/3 SA. Gọi N là trung điểm của SB. Gọi P là trung điểm của SC. "
          "Xét hình chóp S.MNP. Tính tỉ số thể tích của hai khối chóp S.MNP và S.ABC. "
          "Tính thể tích phần còn lại của khối chóp S.ABC sau khi cắt bỏ khối chóp S.MNP.")


def _simson_facts(text: str = SIMSON) -> dict:
    q = lambda s: [s] if s in text else pytest.fail(f"quote not in text: {s}")  # noqa: E731
    return {"facts": [
        {"id": "f_root", "kind": "solid", "role": "premise", "quotes": q("Cho hình chóp S.ABC."), "solid": "S.ABC",
         "solid_type": "pyramid"},
        {"id": "f_base", "kind": "polygon_shape", "role": "premise", "quotes": q("Đáy ABC là tam giác đều cạnh 2a."),
         "shape": "equilateral_triangle", "points": ["A", "B", "C"], "value": "2a"},
        {"id": "f_perp", "kind": "perpendicular", "role": "premise", "quotes": q("SA vuông góc với (ABC)."),
         "points_a": ["S", "A"], "points_b": ["A", "B", "C"]},
        {"id": "f_sa", "kind": "length", "role": "premise", "quotes": q("SA = 3a."), "measure": "segment",
         "points": ["S", "A"], "value": "3a"},
        {"id": "f_m", "kind": "point_def", "role": "premise", "quotes": q("Điểm M thuộc cạnh SA sao cho SM = 1/3 SA."),
         "point_kind": "divide_segment", "point": "M", "points": ["S", "A"], "value": "1/3"},
        {"id": "f_n", "kind": "point_def", "role": "premise", "quotes": q("Gọi N là trung điểm của SB."),
         "point_kind": "midpoint", "point": "N", "points": ["S", "B"]},
        {"id": "f_p", "kind": "point_def", "role": "premise", "quotes": q("Gọi P là trung điểm của SC."),
         "point_kind": "midpoint", "point": "P", "points": ["S", "C"]},
        {"id": "f_sub", "kind": "solid", "role": "premise", "quotes": q("Xét hình chóp S.MNP."), "solid": "S.MNP",
         "solid_type": "pyramid"},
        {"id": "g_ratio", "kind": "question", "role": "question",
         "quotes": q("Tính tỉ số thể tích của hai khối chóp S.MNP và S.ABC."), "quantity": "volume_ratio",
         "points_a": ["S", "M", "N", "P"], "points_b": ["S", "A", "B", "C"]},
        {"id": "g_res", "kind": "question", "role": "question",
         "quotes": q("Tính thể tích phần còn lại của khối chóp S.ABC sau khi cắt bỏ khối chóp S.MNP."),
         "quantity": "residual_volume", "solid": "S.ABC", "points_a": ["S", "M", "N", "P"]},
    ]}


# ── P3.1: a ratio point's stated coefficient is read by the ratio equation, so it is owned ─────────────────────────

def test_divide_segment_coefficient_is_owned_by_the_ratio_equation():
    r = run_fact_route(SIMSON, _simson_facts())
    assert r.status == "SERVED", (r.code, r.reason)
    t = Fraction(1, 3) * Fraction(1, 2) * Fraction(1, 2)            # Simson: SM/SA · SN/SB · SP/SC
    v_parent_sq = Fraction(1, 9) * (Fraction(2) ** 4 * Fraction(3, 16)) * Fraction(3) ** 2  # (⅓ · s²√3/4 · h)², s=2, h=3
    assert r.answer_exact["g_ratio"]["dim"] == 0 and _square(r.answer_exact["g_ratio"]["coef"]) == t * t
    res = r.answer_exact["g_res"]
    assert res["dim"] == 3 and res["unit"] == "a" and _square(res["coef"]) == (1 - t) ** 2 * v_parent_sq


def test_a_number_the_ratio_equation_does_not_read_still_refuses():
    text = SIMSON.replace("sao cho SM = 1/3 SA.", "sao cho SM = 1/3 SA và MB = 4.")
    facts = _simson_facts(text.replace("Điểm M thuộc cạnh SA sao cho SM = 1/3 SA và MB = 4.",
                                       "Điểm M thuộc cạnh SA sao cho SM = 1/3 SA."))
    for f in facts["facts"]:
        if f["id"] == "f_m":
            f["quotes"] = ["Điểm M thuộc cạnh SA sao cho SM = 1/3 SA và MB = 4."]
    r = run_fact_route(text, facts)
    assert (r.status, r.code) == ("REFUSED", "SOURCE_PREMISE_UNREAD"), (r.code, r.reason)


def test_a_coefficient_that_does_not_solve_to_the_call_ratio_is_not_credited():
    facts = _simson_facts()
    for f in facts["facts"]:
        if f["id"] == "f_m":
            f["value"] = "2/3"                          # the source says SM = 1/3 SA: t = 1/3, never 2/3
    r = run_fact_route(SIMSON, facts)
    assert r.status == "REFUSED", (r.code, r.answers)


# ── P3.2: the preview validator reads births the way the timeline does (group events carry `objects`) ─────────────

def _served_simson_midpoint():
    text = SIMSON.replace("Điểm M thuộc cạnh SA sao cho SM = 1/3 SA.", "Gọi M là trung điểm của SA.")
    facts = _simson_facts(text.replace("Gọi M là trung điểm của SA.", "Điểm M thuộc cạnh SA sao cho SM = 1/3 SA."))
    for f in facts["facts"]:
        if f["id"] == "f_m":
            f.update(quotes=["Gọi M là trung điểm của SA."], point_kind="midpoint")
            f.pop("value")
    # The preview adapts the extraction route: an offline transport returns the provider-shaped body (0 network calls).
    from app.ai.fact_extraction import run_ai_fact_route
    import json
    body = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(facts, ensure_ascii=False)}]}}]}
    r = run_ai_fact_route(text, lambda _payload: deepcopy(body), contract="flat")
    assert r.status == "SERVED", (r.code, r.reason)
    return text, r


def _preview_policy():
    from app.ai.pipeline import route_policy_snapshot
    return route_policy_snapshot({"HYBRID_ROUTE_D_PREVIEW": "1"}, preview=True)


def test_preview_accepts_edges_born_inside_a_group_event():
    from app.ai.hybrid_preview import adapt_result
    text, r = _served_simson_midpoint()
    group = [e for e in r.scene3d["events"] if "canh_ben_S_M" in (e.get("objects") or [])]
    assert group and not any(e.get("object") == "canh_ben_S_M" for e in r.scene3d["events"])
    envelope = adapt_result(r, _preview_policy(), text)
    assert envelope.envelope["status"] == "ok"
    assert envelope.route_d["answer_exact"]["g_ratio"]["coef"] == "1/8"


def test_preview_still_refuses_an_edge_born_before_its_endpoint():
    from app.ai.hybrid_preview import PreviewInvalid, adapt_result
    text, r = _served_simson_midpoint()
    events = r.scene3d["events"]
    for e in events:
        if "canh_ben_S_M" in (e.get("objects") or []):
            e["objects"] = [o for o in e["objects"] if o != "canh_ben_S_M"]
    events[1] = deepcopy(events[1])
    events[1]["objects"] = [*(events[1].get("objects") or []), "canh_ben_S_M"]   # born before M (step 4)
    with pytest.raises(PreviewInvalid, match="PREVIEW_DEPENDENCY_INVALID"):
        adapt_result(r, _preview_policy(), text)


# ── P2: section vertices on stated cut edges + derived pyramid (`DINH_CAT_CANH`) ────────────────────────────────────

CUT_RULE = "section vertices on the stated cut edges of a derived plane"


def _base(sa: str = "a", m: dict | None = None) -> list[dict]:
    return [
        {"id": "s", "kind": "solid", "role": "premise", "quotes": ["Cho hình chóp S.ABC"], "solid": "S.ABC",
         "solid_type": "pyramid"},
        {"id": "b", "kind": "polygon_shape", "role": "premise", "quotes": ["đáy ABC là tam giác đều cạnh a"],
         "shape": "equilateral_triangle", "points": ["A", "B", "C"], "value": "a"},
        {"id": "p", "kind": "perpendicular", "role": "premise", "quotes": ["SA vuông góc với mặt phẳng (ABC)"],
         "points_a": ["S", "A"], "points_b": ["A", "B", "C"]},
        {"id": "l", "kind": "length", "role": "premise", "quotes": [f"SA = {sa}"], "measure": "segment",
         "points": ["S", "A"], "value": sa},
        m or {"id": "m", "kind": "point_def", "role": "premise", "quotes": ["Gọi M là trung điểm của SA."], "point": "M",
              "point_kind": "midpoint", "points": ["S", "A"]},
    ]


HEAD = "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng (ABC) và SA = a. "
NAMED = HEAD + ("Gọi M là trung điểm của SA. Mặt phẳng (α) qua M và song song với (ABC) cắt SB, SC lần lượt tại N, P. "
                "Dựng thiết diện của hình chóp S.ABC bởi (α). Tính tỉ số thể tích của hai khối chóp S.MNP và S.ABC.")
NAMED_CLAUSE = "Mặt phẳng (α) qua M và song song với (ABC) cắt SB, SC lần lượt tại N, P."
RATIO_Q = "Tính tỉ số thể tích của hai khối chóp S.MNP và S.ABC."


def _named(text: str = NAMED, edges=(("S", "B"), ("S", "C")), points=("N", "P"), clause: str = NAMED_CLAUSE,
           ref: tuple[str, str, str] = ("A", "B", "C")) -> dict:
    return {"facts": _base() + [
        {"id": "td", "kind": "section", "role": "question", "quotes": [clause, "Dựng thiết diện của hình chóp S.ABC bởi (α)."],
         "solid": "S.ABC", "point": "M", "plane_relation": "parallel", "points_b": list(ref),
         "cut_edges": [list(e) for e in edges], "cut_points": list(points)},
        {"id": "sub", "kind": "solid", "role": "premise", "quotes": [RATIO_Q], "solid_type": "pyramid", "point": "S",
         "plane_ref": "td"},
        {"id": "g", "kind": "question", "role": "question", "quotes": [RATIO_Q], "quantity": "volume_ratio",
         "points_a": ["S", "M", "N", "P"], "points_b": ["S", "A", "B", "C"]},
    ]}


ANON = HEAD.replace("SA = a.", "SA = 2a.") + (
    "Điểm M thuộc cạnh SA sao cho SM = 2/3 SA. Mặt phẳng (α) qua M và song song với (ABC) cắt SB, SC. "
    "Dựng thiết diện của hình chóp S.ABC bởi (α) và khối chóp đỉnh S cắt bởi (α).")


def _anon(text: str = ANON, edges=(("S", "B"), ("S", "C"))) -> dict:
    m = {"id": "m", "kind": "point_def", "role": "premise", "quotes": ["Điểm M thuộc cạnh SA sao cho SM = 2/3 SA."],
         "point": "M", "point_kind": "divide_segment", "points": ["S", "A"], "value": "2/3"}
    return {"facts": _base("2a", m) + [
        {"id": "td", "kind": "section", "role": "question",
         "quotes": ["Mặt phẳng (α) qua M và song song với (ABC) cắt " + ", ".join("".join(e) for e in edges) + ".",
                    "Dựng thiết diện của hình chóp S.ABC bởi (α)"],
         "solid": "S.ABC", "point": "M", "plane_relation": "parallel", "points_b": ["A", "B", "C"],
         "cut_edges": [list(e) for e in edges]},
        {"id": "kd", "kind": "solid", "role": "question", "quotes": ["khối chóp đỉnh S cắt bởi (α)."], "solid_type": "pyramid",
         "point": "S", "plane_ref": "td"},
    ]}


def _choices(r) -> list[tuple[str, str, int]]:
    return [(s["need"], s["selection"], s["cost"]) for s in r.planner["trace"] if s.get("step") == "effect_resolution"]


def test_named_cut_reuses_the_through_point_and_composes_into_a_ratio():
    r = run_fact_route(NAMED, _named())
    assert r.status == "SERVED", (r.code, r.reason)
    assert _square(r.answer_exact["g"]["coef"]) == Fraction(1, 8) ** 2      # α ∥ (ABC) through the midpoint: (1/2)³
    assert _choices(r) == [("SectionVertex(SA, plane through M)", "reuse_through_point", 0),
                           ("SectionVertex(SB, plane through M)", "named_intersection", 1),
                           ("SectionVertex(SC, plane through M)", "named_intersection", 1)]
    fns = [c["fn"] for c in r.planner["calls"]]
    assert fns.count("translate_point") == 2 and fns.count("intersect_line_plane") == 2   # one plane, reused by every cut
    assert [c["args"]["base"] for c in r.planner["calls"] if c["id"] == "sub"] == [["M", "N", "P"]]


def test_anonymous_cut_builds_the_derived_pyramid_without_leaking_planner_labels():
    r = run_fact_route(ANON, _anon())
    assert r.status == "SERVED" and r.answers == {}, (r.code, r.reason)
    assert [x[1] for x in _choices(r)] == ["reuse_through_point", "fresh_intersection", "fresh_intersection"]
    cert = next(d for d in r.planner["auxiliary"] if d.get("rule") == CUT_RULE)
    fresh = cert["labels"]
    assert len(fresh) == 2 and all(x not in ANON for x in fresh)
    t = [Fraction(s["t"]) for s in r.trace if s.get("step") == "certify_section_vertex"]
    assert sorted(t) == [Fraction(2, 3)] * 3                                  # α ∥ (ABC), SM/SA = 2/3 ⇒ every cut at t = 2/3
    learner = [str(o.get(k)) for o in r.scene3d["objects"] for k in ("label", "display_label", "reference", "notation", "role")]
    learner += [str(e.get(k)) for e in r.scene3d["events"] for k in ("display_label", "learner_text", "explanation")]
    learner += [s.get("learner_text", "") for s in r.scene3d["formation"]["steps"]]
    tok = re.compile(r"(?<![\w'])[A-Z0-9'.]*(?:" + "|".join(map(re.escape, fresh)) + r")[A-Z0-9'.]*(?![\w'])")
    assert not [s for s in learner if tok.search(s)]
    solid = next(o for o in r.scene3d["objects"] if o.get("type") == "solid" and o["id"] != "khoi_S_ABC")
    assert solid["notation"] is None and solid["label"] == "Khối chóp đỉnh S cắt bởi (α)"


def test_a_fresh_label_never_collides_with_a_label_of_the_source():
    text = ANON.replace("Dựng thiết diện", "Gọi I là trung điểm của BC. Dựng thiết diện")
    facts = _anon(text)
    facts["facts"].append({"id": "i", "kind": "point_def", "role": "premise", "quotes": ["Gọi I là trung điểm của BC."],
                           "point": "I", "point_kind": "midpoint", "points": ["B", "C"]})
    r = run_fact_route(text, facts)
    assert r.status == "SERVED", (r.code, r.reason)
    cert = next(d for d in r.planner["auxiliary"] if d.get("rule") == CUT_RULE)
    assert "I" not in cert["labels"] and len(set(cert["labels"])) == 2


@pytest.mark.parametrize("case", ["no_clause", "order", "swapped_names", "extra_condition"])
def test_the_cut_clause_is_bound_exactly_or_refused(case):
    """no_clause: the source states no cut, the facts claim one · order: the same edges in another order · swapped_names:
    "lần lượt tại N, P" puts N on SB · extra_condition: an unread condition follows the cut clause."""
    text, kw = NAMED, {}
    if case == "no_clause":
        text = NAMED.replace(" cắt SB, SC lần lượt tại N, P.", ".")
        kw = {"clause": "Mặt phẳng (α) qua M và song song với (ABC)."}
    if case == "order":
        kw = {"edges": (("S", "C"), ("S", "B")), "points": ("P", "N")}
    if case == "swapped_names":
        kw = {"points": ("P", "N")}
    if case == "extra_condition":
        text = NAMED.replace("lần lượt tại N, P.", "lần lượt tại N, P sao cho NP = BC.")
        kw = {"clause": NAMED_CLAUSE.replace("N, P.", "N, P sao cho NP = BC.")}
    r = run_fact_route(text, _named(text, **kw))
    assert (r.status, r.code) == ("REFUSED", "SOURCE_OBJECT_MISMATCH"), (r.code, r.reason)


def test_swapped_cut_names_are_refused_without_any_later_question_to_catch_them():
    """Construction only: no ratio names S.MNP afterwards, so the cut-clause binding is the only barrier."""
    text = NAMED.replace(" " + RATIO_Q, "")

    def section_only(**kw) -> dict:
        return {"facts": [f for f in _named(text, **kw)["facts"] if f["id"] not in ("sub", "g")]}

    assert run_fact_route(text, section_only()).status == "SERVED"
    r = run_fact_route(text, section_only(points=("P", "N")))
    assert (r.status, r.code) == ("REFUSED", "SOURCE_OBJECT_MISMATCH"), (r.code, r.reason)


def test_a_derived_pyramid_needs_every_lateral_edge():
    text = ANON.replace("cắt SB, SC.", "cắt SB.")
    r = run_fact_route(text, _anon(text, edges=(("S", "B"),)))
    assert (r.status, r.code) == ("REFUSED", "SECTION_NOT_CLOSED_ON_LATERAL_EDGES"), (r.code, r.reason)


def test_an_anonymous_derived_pyramid_is_not_a_groundable_ratio_operand():
    text = ANON + " Tính tỉ số thể tích."
    facts = _anon(text)
    facts["facts"].append({"id": "g", "kind": "question", "role": "question", "quotes": ["Tính tỉ số thể tích."],
                           "quantity": "volume_ratio", "solid_refs": ["kd", "s"]})
    r = run_fact_route(text, facts)
    # The operand's vertices are planner labels the source never wrote: refused before any ratio grammar is consulted.
    assert (r.status, r.code) == ("REFUSED", "UNKNOWN_LABEL"), (r.code, r.reason)


def test_an_edge_parallel_to_the_plane_is_refused():
    clause = NAMED_CLAUSE.replace("(ABC)", "(SBC)")
    text = NAMED.replace(NAMED_CLAUSE, clause)
    r = run_fact_route(text, _named(text, clause=clause, ref=("S", "B", "C")))
    # α ∥ (SBC) contains no point of SB: the kernel refuses constructing that intersection, before any certificate check
    assert (r.status, r.code) == ("REFUSED", "PARALLEL_NO_INTERSECTION"), (r.code, r.reason)


def test_engine_refuses_a_vertex_outside_its_edge(monkeypatch):
    """Fault injection past the gate: the certificate claims N on edge NB (t = 0) — the engine's own check refuses."""
    from app.simulation.geometry_functions import engine, registry
    from app.simulation.geometry_functions.planner import lap_ke_hoach

    k = lap_ke_hoach(_named(), NAMED)
    real = registry.kiem_nguon(registry.doc_ke_hoach({"calls": k.calls}), NAMED, tuple(k.auxiliary))
    aux = deepcopy(k.auxiliary)
    cert = next(d for d in aux if d.get("rule") == CUT_RULE)
    cert["vertices"][1]["edge"] = ["N", "B"]
    monkeypatch.setattr(engine, "kiem_nguon", lambda *a, **kw: real)
    r = engine.dung_tu_loi_goi(NAMED, {"calls": k.calls}, tuple(aux))
    assert (r.status, r.code) == ("REFUSED", "SECTION_VERTEX_OFF_EDGE"), (r.code, r.reason)


def test_internal_fields_are_absent_from_the_provider_schema_and_refused_from_a_provider():
    import json
    from app.ai.fact_extraction import facts_response_schema, run_ai_fact_route
    from app.simulation.geometry_functions.planner import INTERNAL_FACT_FIELDS, TypedFact

    for schema in (TypedFact.model_json_schema(), facts_response_schema("flat"), facts_response_schema("v3")):
        assert not any(f in json.dumps(schema) for f in INTERNAL_FACT_FIELDS)
    body = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(_named(), ensure_ascii=False)}]}}]}
    r = run_ai_fact_route(NAMED, lambda _p: deepcopy(body), contract="flat")
    assert (r.status, r.code) == ("REFUSED", "INTERNAL_FIELD_FROM_PROVIDER")


SQUARE = ("Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh a. SA vuông góc với mặt phẳng (ABC). SA = a. "
          "Gọi M là trung điểm của SA. Mặt phẳng (α) qua M và {rel} cắt SB, SC, SD lần lượt tại N, P, Q. "
          "Dựng thiết diện của hình chóp S.ABCD bởi (α). Tính tỉ số thể tích của hai khối chóp S.MNPQ và S.ABCD. "
          "Tính thể tích phần còn lại của khối chóp S.ABCD sau khi cắt bỏ khối chóp S.MNPQ.")


def _square_case(rel: str) -> tuple[str, dict]:
    text = SQUARE.format(rel=rel)
    ratio_q, res_q = text.split(". Tính")[1:]
    ratio_q, res_q = "Tính" + ratio_q + ".", "Tính" + res_q
    clause = f"Mặt phẳng (α) qua M và {rel} cắt SB, SC, SD lần lượt tại N, P, Q."
    perp = rel.startswith("vuông")
    return text, {"facts": [
        {"id": "s", "kind": "solid", "role": "premise", "quotes": ["Cho hình chóp S.ABCD."], "solid": "S.ABCD",
         "solid_type": "pyramid"},
        {"id": "b", "kind": "polygon_shape", "role": "premise", "quotes": ["Đáy ABCD là hình vuông cạnh a."], "shape": "square",
         "points": ["A", "B", "C", "D"], "value": "a"},
        {"id": "p", "kind": "perpendicular", "role": "premise", "quotes": ["SA vuông góc với mặt phẳng (ABC)."],
         "points_a": ["S", "A"], "points_b": ["A", "B", "C"]},
        {"id": "l", "kind": "length", "role": "premise", "quotes": ["SA = a."], "measure": "segment", "points": ["S", "A"],
         "value": "a"},
        {"id": "m", "kind": "point_def", "role": "premise", "quotes": ["Gọi M là trung điểm của SA."], "point": "M",
         "point_kind": "midpoint", "points": ["S", "A"]},
        {"id": "td", "kind": "section", "role": "question", "quotes": [clause, "Dựng thiết diện của hình chóp S.ABCD bởi (α)."],
         "solid": "S.ABCD", "point": "M", "plane_relation": "perpendicular" if perp else "parallel",
         "points_b": ["S", "A"] if perp else ["A", "B", "C"], "cut_edges": [["S", "B"], ["S", "C"], ["S", "D"]],
         "cut_points": ["N", "P", "Q"]},
        {"id": "sub", "kind": "solid", "role": "premise", "quotes": [ratio_q], "solid_type": "pyramid", "point": "S",
         "plane_ref": "td"},
        {"id": "g", "kind": "question", "role": "question", "quotes": [ratio_q], "quantity": "volume_ratio",
         "solid_refs": ["sub", "s"]},
        {"id": "h", "kind": "question", "role": "question", "quotes": [res_q], "quantity": "residual_volume",
         "solid_refs": ["s", "sub"]},
    ]}


def test_teaching_expansion_over_the_ir_budget_is_skipped_and_recorded_not_refused():
    text, facts = _square_case("song song với (ABC)")
    r = run_fact_route(text, facts)
    assert r.status == "SERVED", (r.code, r.reason)
    assert _square(r.answer_exact["g"]["coef"]) == Fraction(1, 64)                      # (1/2)³, square base
    assert _square(r.answer_exact["h"]["coef"]) == (Fraction(7, 8) * Fraction(1, 3)) ** 2  # (1 − 1/8)·a²·a/3
    assert [s["rule"] for s in r.trace if s.get("step") == "formation_budget"] == ["pedagogical_expansion_skipped"]


def test_a_compiled_program_over_the_ir_budget_is_a_typed_refusal(monkeypatch):
    # Run `backend-hybrid-contract-unification`: this plan was 33 declarations only because each cut re-declared the
    # section plane and each foot re-declared SA; canonicalized it is 30 and serves. The refusal path itself is kept under
    # test by a budget one below the program's real size.
    import app.simulation.semantic_program.validator as V

    text, facts = _square_case("vuông góc với SA")
    r = run_fact_route(text, facts)
    assert r.status == "SERVED" and len(r.program["memory_declarations"]) == 30, (r.code, r.reason)
    monkeypatch.setattr(V, "MAX_MEMORY_DECLARATIONS", 29)
    r = run_fact_route(text, facts)
    assert (r.status, r.code) == ("REFUSED", "IR_MEMORY_BUDGET_EXCEEDED"), (r.code, r.reason)


def test_a_named_derived_pyramid_may_follow_another_solid_in_the_ratio_list():
    text = NAMED.replace(RATIO_Q, "Tính tỉ số thể tích của hai khối chóp S.ABC và S.MNP.")
    facts = _named(text)
    for f in facts["facts"]:
        if f["id"] in ("sub", "g"):
            f["quotes"] = ["Tính tỉ số thể tích của hai khối chóp S.ABC và S.MNP."]
        if f["id"] == "g":
            f.update(points_a=["S", "A", "B", "C"], points_b=["S", "M", "N", "P"])
    r = run_fact_route(text, facts)
    assert r.status == "SERVED", (r.code, r.reason)
    assert _square(r.answer_exact["g"]["coef"]) == Fraction(8) ** 2                     # reciprocal of (1/2)³


# ── review round 1 regressions ──────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("cut", ["cắt BC, CA lần lượt tại N, P", "cắt SA, SB lần lượt tại N, P", "cắt SB, SC lần lượt tại P, N"])
def test_a_second_cut_clause_that_contradicts_the_bound_one_is_refused(cut):
    """BLOCKER 1: a request sentence may not restate the cut with other edges or names."""
    req = f"Dựng thiết diện của hình chóp S.ABC bởi (α) {cut}."
    text = NAMED.replace("Dựng thiết diện của hình chóp S.ABC bởi (α).", req)
    facts = _named(text)
    facts["facts"][5]["quotes"][1] = req
    r = run_fact_route(text, facts)
    assert (r.status, r.code) == ("REFUSED", "SOURCE_OBJECT_MISMATCH"), (r.code, r.reason)


def test_restating_the_same_cut_clause_is_consistent():
    req = "Dựng thiết diện của hình chóp S.ABC bởi (α) cắt SB, SC lần lượt tại N, P."
    text = NAMED.replace("Dựng thiết diện của hình chóp S.ABC bởi (α).", req)
    facts = _named(text)
    facts["facts"][5]["quotes"][1] = req
    assert run_fact_route(text, facts).status == "SERVED"


@pytest.mark.parametrize("neg", ["nhưng không dựng", "nhưng đừng dựng", "nhưng bỏ qua", "nhưng không xét"])
def test_a_negated_derived_pyramid_request_is_refused(neg):
    """IMPORTANT 2: the shared negation lexicon has no request verbs; the derived-pyramid binding reads its own clause."""
    text = ANON.replace("bởi (α) và khối chóp", f"bởi (α) {neg} khối chóp")
    facts = _anon(text)
    facts["facts"][-1]["quotes"] = ["khối chóp đỉnh S cắt bởi (α)."]
    r = run_fact_route(text, facts)
    assert (r.status, r.code) == ("REFUSED", "NEGATED_CLAUSE"), (r.code, r.reason)


@pytest.mark.parametrize("lead", ["thay vì", "thay cho", "trừ", "ngoại trừ", "không quên dựng"])
def test_a_derived_pyramid_without_a_known_positive_lead_in_is_refused(lead):
    """Review round 2, IMPORTANT 1: a blacklist misses contrastive wording ("thay vì …"); only a closed set of positive
    lead-ins reads as a request. "không quên dựng" is a positive request refused on purpose (fail-closed, documented)."""
    text = ANON.replace("bởi (α) và khối chóp", f"bởi (α) {lead} khối chóp")
    r = run_fact_route(text, _anon(text))
    assert (r.status, r.code) == ("REFUSED", "NEGATED_CLAUSE"), (r.code, r.reason)


@pytest.mark.parametrize("lead", ["và dựng thêm", "rồi xác định", "và vẽ", "và hãy dựng"])
def test_a_derived_pyramid_after_a_positive_lead_in_is_served(lead):
    text = ANON.replace("bởi (α) và khối chóp", f"bởi (α) {lead} khối chóp")
    r = run_fact_route(text, _anon(text))
    assert r.status == "SERVED", (r.code, r.reason)


ANON_REQ = "Dựng thiết diện của hình chóp S.ABC bởi (α) và khối chóp đỉnh S cắt bởi (α)."


@pytest.mark.parametrize("req", [
    "Dựng thiết diện của hình chóp S.ABC bởi (α), không dựng mặt đáy và khối chóp đỉnh S cắt bởi (α).",
    "Chỉ dựng thiết diện của hình chóp S.ABC bởi (α), không dựng mặt đáy, đường cao và khối chóp đỉnh S cắt bởi (α).",
    "Dựng thiết diện của hình chóp S.ABC bởi (α) và khối chóp đỉnh S cắt bởi (α) hay không?",
])
def test_a_negation_governing_a_list_or_following_the_derived_pyramid_is_refused(req):
    """Review round 3: the empty lead-in after "và" / "," passed the allow-list while a negation governed the list."""
    text = ANON.replace(ANON_REQ, req)
    facts = _anon(text)
    facts["facts"][5]["quotes"][1] = "thiết diện của hình chóp S.ABC bởi (α)"
    facts["facts"][6]["quotes"] = ["khối chóp đỉnh S cắt bởi (α)"]
    r = run_fact_route(text, facts)
    assert (r.status, r.code) == ("REFUSED", "NEGATED_CLAUSE"), (r.code, r.reason)


def test_a_ratio_question_without_a_request_verb_is_served():
    q = "Tỉ số thể tích của hai khối chóp S.MNP và S.ABC bằng bao nhiêu?"
    text = NAMED.replace(RATIO_Q, q)
    facts = _named(text)
    for f in facts["facts"]:
        if f["id"] in ("sub", "g"):
            f["quotes"] = [q]
    r = run_fact_route(text, facts)
    assert r.status == "SERVED", (r.code, r.reason)
    assert _square(r.answer_exact["g"]["coef"]) == Fraction(1, 8) ** 2


@pytest.mark.parametrize("case", ["named", "anon"])
def test_cut_vertices_and_their_operand_planes_speak_the_source_plane_name(case):
    """Review round 2, IMPORTANT 2: the planner's point-built plane name ("(MHH1)") and its per-cut duplicate
    construction ("Dựng mặt phẳng qua M, H, H1") never reach the learner; the source name (α) does."""
    r = run_fact_route(NAMED, _named()) if case == "named" else run_fact_route(ANON, _anon())
    assert r.status == "SERVED", (r.code, r.reason)
    sc = r.scene3d
    ky = next(o for o in sc["objects"] if o["id"] == "mp_td_td")["notation"]
    assert ky and ky != "(α)"
    learner = [str(o.get("role")) for o in sc["objects"]]
    learner += [str(e.get(k)) for e in sc["events"] for k in ("display_label", "learner_text", "explanation")]
    learner += [s.get("learner_text", "") for s in sc["formation"]["steps"]]
    assert not [s for s in learner if ky in s or "mặt phẳng qua" in s]
    dup = [s["learner_text"] for s in sc["formation"]["steps"] if any(f.endswith("_plane") and f.startswith("derived_")
                                                                       for f in s["focus_ids"])]
    # Run `backend-hybrid-contract-unification`: the two cuts read ONE plane object (IR canonicalization), so the plane is
    # "considered" once; each cut keeps its own step naming its edge and (α).
    assert dup == ["Xét mặt phẳng (α) để tìm giao điểm với SB."]
    cuts = [s["learner_text"] for s in sc["formation"]["steps"] if "giao điểm của S" in s["learner_text"]]
    assert [("SB" in x, "SC" in x, "(α)" in x) for x in cuts] == [(True, False, True), (False, True, True)]
    if case == "named":
        assert next(o for o in sc["objects"] if o["id"] == "N")["role"] == "Giao điểm của SB và (α)"


def test_an_identical_intersection_already_planned_is_reused_at_cost_zero():
    """The `reuse_intersection` candidate: a second section fact on the same plane reuses the cuts of the first."""
    from app.simulation.geometry_functions.planner import lap_ke_hoach
    facts = _named()
    twin = deepcopy(facts["facts"][5])
    twin["id"] = "td2"
    facts["facts"].insert(6, twin)
    k = lap_ke_hoach(facts, NAMED)
    sel = [(s["fact"], s["selection"], s["cost"]) for s in k.trace if s.get("step") == "effect_resolution"]
    assert [x for x in sel if x[0] == "td2"] == [("td2", "reuse_through_point", 0), ("td2", "reuse_intersection", 0),
                                                 ("td2", "reuse_intersection", 0)]
    assert [c["fn"] for c in k.calls].count("intersect_line_plane") == 2      # nothing recomputed
    assert [c["fn"] for c in k.calls].count("translate_point") == 2           # one plane


def test_engine_refuses_a_reused_vertex_whose_edge_lies_in_the_plane(monkeypatch):
    """Fault injection past the gate: the certificate's plane replaced by the face (SAB), which contains the lateral edge
    SA of the reused through-point M — the engine's own parallel check refuses."""
    from app.simulation.geometry_functions import engine, registry
    from app.simulation.geometry_functions.planner import lap_ke_hoach

    k = lap_ke_hoach(_named(), NAMED)
    real = registry.kiem_nguon(registry.doc_ke_hoach({"calls": k.calls}), NAMED, tuple(k.auxiliary))
    aux = deepcopy(k.auxiliary)
    cert = next(d for d in aux if d.get("rule") == CUT_RULE)
    cert["plane"] = ["S", "A", "B"]
    monkeypatch.setattr(engine, "kiem_nguon", lambda *a, **kw: real)
    r = engine.dung_tu_loi_goi(NAMED, {"calls": k.calls}, tuple(aux))
    assert (r.status, r.code) == ("REFUSED", "LINE_PARALLEL_TO_PLANE"), (r.code, r.reason)


def test_the_teaching_expansion_fallback_is_limited_to_section_vertex_plans(monkeypatch):
    """IMPORTANT 4: a plan without a `DINH_CAT_CANH` certificate keeps main's behaviour when the expansion is over budget."""
    from app.simulation.semantic_program import validator
    monkeypatch.setattr(validator, "MAX_MEMORY_DECLARATIONS", 20)   # both plans: compiled ≤ 20 < expanded (15/23, 19/23)
    r = run_fact_route(SIMSON, _simson_facts())                       # no cut certificate: refused as on main
    assert (r.status, r.code) == ("REFUSED", "ENGINE_EXECUTION_FAILED"), (r.code, r.reason)
    r = run_fact_route(ANON, _anon())                                 # cut certificate: unexpanded, recorded
    assert r.status == "SERVED", (r.code, r.reason)
    assert [s["rule"] for s in r.trace if s.get("step") == "formation_budget"] == ["pedagogical_expansion_skipped"]


# ── P1/P2: the TypedFactNext bridge (pure translation into the one planner / gate / engine) ──────────────────────────

def _next(text: str, sections: list, sim: list, math: list = ()) -> dict:
    return {"schema_version": "typed-fact-next/1", "problem_text": text,
            "solids": [{"solid_id": "pyr", "solid_type": "pyramid", "notation": "S.ABC", "quote": "Cho hình chóp S.ABC"}],
            "premises": [
                {"kind": "base_is_equilateral_triangle", "args": {"vertices": ["A", "B", "C"], "side": "a"},
                 "quote": "đáy ABC là tam giác đều cạnh a"},
                {"kind": "line_perp_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]},
                 "quote": "SA vuông góc với mặt phẳng (ABC)"},
                {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "a"}, "quote": "SA = a"},
                {"kind": "point_is_midpoint", "args": {"point": "M", "segment": ["S", "A"]},
                 "quote": "Gọi M là trung điểm của SA."}],
            "derived_sections": sections, "simulation_goals": sim, "math_goals": list(math)}


SEC = {"section_id": "sec", "plane_name": "α", "target_solid_id": "pyr", "plane_kind": "through_point_parallel_plane",
       "through_point": "M", "parallel_plane": ["A", "B", "C"], "cut_edges": [["S", "B"], ["S", "C"]],
       "named_intersections": {"S-B": "N", "S-C": "P"}, "quote": NAMED_CLAUSE}
SEC_GOAL = {"goal_id": "g_sec", "kind": "construct_plane_section", "target_section_id": "sec",
            "quote": "Dựng thiết diện của hình chóp S.ABC bởi (α)."}


def test_bridge_serves_a_named_derived_pyramid_ratio_through_the_planner():
    from app.ai.function_route import run_typed_fact_next_planner_route
    payload = _next(NAMED, [SEC],
                    [SEC_GOAL, {"goal_id": "g_sub", "kind": "construct_derived_solid", "derived_solid_id": "sub",
                                "target_section_id": "sec", "apex_ref": "S", "parent_solid_id": "pyr", "quote": RATIO_Q}],
                    [{"goal_id": "g", "kind": "volume_ratio", "numerator_solid_id": "sub", "denominator_solid_id": "pyr",
                      "quote": RATIO_Q}])
    r = run_typed_fact_next_planner_route(payload)
    assert r.status == "SERVED", (r.code, r.reason)
    assert _square(r.answer_exact["g"]["coef"]) == Fraction(1, 64)
    assert r.planner["bridge"]["version"] == "typed-fact-next-bridge/1"


def test_bridge_serves_a_construction_only_section_with_unnamed_vertices():
    from app.ai.function_route import run_typed_fact_next_planner_route
    text = NAMED.replace(" lần lượt tại N, P", "").replace(" " + RATIO_Q, "")
    sec = {**SEC, "named_intersections": {}, "quote": NAMED_CLAUSE.replace(" lần lượt tại N, P", "")}
    r = run_typed_fact_next_planner_route(_next(text, [sec], [SEC_GOAL]))
    assert r.status == "SERVED" and r.answers == {}, (r.code, r.reason)


@pytest.mark.parametrize("case,code", [
    ("curved", "BRIDGE_UNSUPPORTED_CURVED"),
    ("qualified", "BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY"),
    ("plane_kind", "BRIDGE_UNSUPPORTED_PLANE_KIND"),
    ("relation", "BRIDGE_UNSUPPORTED_RELATION"),
    ("no_cut_edges", "BRIDGE_CUT_EDGES_NOT_STATED"),
])
def test_bridge_refuses_what_typedfact_cannot_express(case, code):
    from app.ai.function_route import run_typed_fact_next_planner_route
    payload = _next(NAMED, [deepcopy(SEC)], [{"goal_id": "g_sub", "kind": "construct_derived_solid", "derived_solid_id": "sub",
                                              "target_section_id": "sec", "apex_ref": "S", "parent_solid_id": "pyr",
                                              "quote": "Dựng thiết diện của hình chóp S.ABC bởi (α)."}])
    if case == "curved":
        payload["solids"].append({"solid_id": "cone", "solid_type": "cone", "notation": "S.O", "center": "O",
                                  "quote": "Cho hình chóp S.ABC"})
    if case == "qualified":
        payload["solids"][0]["vertex_bindings"] = {"S": "S1"}
    if case == "plane_kind":
        payload["derived_sections"][0].update(plane_kind="parallel_to_base_at_ratio", ratio_from_apex="1/2")
    if case == "relation":
        payload["relations"] = [{"relation_id": "r", "kind": "containment", "quote": "Cho hình chóp S.ABC",
                                 "container_ref": "pyr", "member_ref": "M"}]
    if case == "no_cut_edges":
        payload["derived_sections"][0].update(cut_edges=[], named_intersections={})
    r = run_typed_fact_next_planner_route(payload)
    assert (r.status, r.code) == ("REFUSED", code), (r.code, r.reason)


@pytest.mark.parametrize("case,code", [
    # Run `hybrid-contract-v2` (P1): premise argument shapes are now checked by the shared schema at parse time, so these
    # input errors are refused earlier and more precisely (INVALID_PREMISE_ARGS) — still before any compilation.
    ("missing_point", "INVALID_PREMISE_ARGS"),
    ("non_string_point", "INVALID_PREMISE_ARGS"),
    ("non_sequence_segment", "INVALID_PREMISE_ARGS"),
    ("invalid_qualified_syntax", "INVALID_PREMISE_ARGS"),
    ("unknown_qualifier", "UNKNOWN_SOLID_ID"),
    ("unknown_local_vertex", "UNKNOWN_VERTEX_REF"),
    ("unknown_named_edge_qualifier", "UNKNOWN_SOLID_ID"),
    ("contradictory_unit", "NON_HOMOGENEOUS_LENGTHS"),
    ("unrepresentable_unit", "BRIDGE_UNSUPPORTED_LENGTH_UNIT"),
    ("wrong_plane_name", "SOURCE_OBJECT_MISMATCH"),
    ("reference_plane_name", "SOURCE_OBJECT_MISMATCH"),
])
def test_bridge_preserves_input_constraints_or_refuses(case, code):
    from app.ai.function_route import run_typed_fact_next_planner_route
    payload = _next(NAMED.replace(" " + RATIO_Q, ""), [deepcopy(SEC)], [deepcopy(SEC_GOAL)])
    control = run_typed_fact_next_planner_route(payload)
    assert control.status == "SERVED", (control.code, control.reason)
    args = payload["premises"][3]["args"]
    if case == "missing_point":
        del args["point"]
    elif case == "non_string_point":
        args["point"] = 1
    elif case == "non_sequence_segment":
        args["segment"] = 1
    elif case == "invalid_qualified_syntax":
        args["point"] = "ghost::m"
    elif case == "unknown_qualifier":
        payload["derived_sections"][0]["through_point"] = "ghost::M"
    elif case == "unknown_local_vertex":
        payload["derived_sections"][0]["through_point"] = "pyr::M"
    elif case == "unknown_named_edge_qualifier":
        payload["derived_sections"][0]["named_intersections"] = {"ghost::S-ghost::B": "N", "S-C": "P"}
    elif case == "contradictory_unit":
        payload["length_unit"] = "1"
    elif case == "unrepresentable_unit":
        payload["length_unit"] = "a"
        payload["problem_text"] = payload["problem_text"].replace("cạnh a", "cạnh 1").replace("SA = a", "SA = 1")
        for prem in payload["premises"]:
            prem["quote"] = prem["quote"].replace("cạnh a", "cạnh 1").replace("SA = a", "SA = 1")
            for key in ("side", "value"):
                if prem["args"].get(key) == "a":
                    prem["args"][key] = "1"
    else:
        payload["derived_sections"][0]["plane_name"] = "ABC" if case == "reference_plane_name" else "β"
    r = run_typed_fact_next_planner_route(payload)
    assert (r.status, r.code) == ("REFUSED", code), (r.code, r.reason)
    assert r.scene3d is None and not r.answers


def test_bridge_accepts_matching_units_and_declared_qualified_vertices():
    from app.ai.function_route import run_typed_fact_next_planner_route
    payload = _next(NAMED.replace(" " + RATIO_Q, ""), [deepcopy(SEC)], [deepcopy(SEC_GOAL)])
    payload["length_unit"] = "a"
    payload["simulation_goals"][0]["goal_id"] = "g::S"
    payload["premises"][1]["args"]["line"] = ["pyr::S", "pyr::A"]
    r = run_typed_fact_next_planner_route(payload)
    assert r.status == "SERVED" and r.length_unit == "a", (r.code, r.reason)
