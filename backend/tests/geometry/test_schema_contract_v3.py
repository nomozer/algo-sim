"""Schema-Contract v3 (research): a kind/goal-specific provider response schema. The parser, TypedFact, planner and the
default product request are unchanged; v3 is selected explicitly. Offline only — no model call."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ai import fact_extraction as fx
from app.simulation.geometry_functions.planner import _CAN, TypedFact

RUNS = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs"
V3 = fx.facts_response_schema("v3")
ITEM = V3["properties"]["facts"]["items"]
GOLD_ONLY = ("required", "alternatives", "rid")


def gold_facts():
    for run in ("hybrid-semantic-extraction-v2", "independent-nlu-extraction-evaluation"):
        g = json.loads((RUNS / run / "inputs/gold_facts.json").read_text(encoding="utf-8"))
        for cid, c in g["cases"].items():
            for f in c["facts"]:
                yield f"{run}:{cid}:{f['id']}", {k: v for k, v in f.items() if k not in GOLD_ONLY}


def q(**kw):
    return {"id": "q", "kind": "question", "role": "question", "quotes": ["Tính."], **kw}


# ── the default product request is untouched ─────────────────────────────────────────────────────────────────────

def test_default_request_and_surface_are_the_flat_product_contract():
    assert fx.facts_response_schema() == fx.facts_response_schema("flat")
    assert fx.build_request("x")["generationConfig"]["responseSchema"] == fx.facts_response_schema()
    assert fx.surface_fingerprint() == "485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a"
    assert fx.surface_fingerprint("v3") != fx.surface_fingerprint()


# ── coverage: every legitimate authored fact remains expressible ─────────────────────────────────────────────────

def test_every_authored_gold_fact_fits_v3():
    misses = [fid for fid, f in gold_facts() if not fx.schema_accepts(ITEM, f)]
    assert not misses, misses[:10]


def test_every_v3_shape_is_a_typedfact():
    # Each variant only restricts the flat contract: an instance it accepts must still validate as TypedFact.
    for fid, f in gold_facts():
        TypedFact.model_validate(f)


# ── exclusion: the measured pilot failure shapes cannot be emitted ───────────────────────────────────────────────

@pytest.mark.parametrize("bad", [
    q(quantity="length"),                                              # question without operands
    q(quantity="distance", solid="S.ABC"),                             # only quantity + solid
    q(quantity="length", value="AG"),                                  # operand placed in `value`
    q(quantity="area", value="ABCD"),
    q(quantity="angle", points_a=["S", "A"]),                          # second operand missing
    q(quantity="volume"),                                              # volume without its solid
    {"id": "r", "kind": "right_angle", "role": "premise", "quotes": ["vuông tại A"], "at": "A", "points": ["B", "A", "C"]},
    {"id": "l", "kind": "length", "role": "premise", "quotes": ["cạnh đáy 4"], "measure": "base_edge", "value": "4"},
    {"id": "h", "kind": "altitude", "role": "premise", "quotes": ["SA là đường cao"], "points": ["S", "A"]},
    {"id": "s", "kind": "solid", "role": "premise", "quotes": ["hình chóp"], "solid_type": "pyramid"},
    {"id": "p", "kind": "length", "role": "premise", "quotes": ["AB = 3"], "measure": "segment", "points": ["A", "B"], "value": "AB"},
    {"id": "x", "kind": "question", "role": "question", "quotes": []},  # no source quote
])
def test_measured_failure_shapes_are_not_representable(bad):
    assert not fx.schema_accepts(ITEM, bad)


# ── honest exits: missing / ambiguous / unsupported never force invention ────────────────────────────────────────

@pytest.mark.parametrize("exit_", [
    {"id": "u", "kind": "unsupported", "role": "question", "quotes": ["tính khoảng cách tới đoạn AB"], "reason": "finite segment"},
    {"id": "u", "kind": "unsupported", "role": "prove", "quotes": ["chứng minh MN // BC"], "reason": "parallel",
     "points_a": ["M", "N"], "points_b": ["B", "C"]},
    {"id": "u", "kind": "unsupported", "role": "premise", "quotes": ["một hình chóp"], "reason": "solid not named",
     "ambiguous": True},
    {"id": "u", "kind": "unsupported", "role": "prove", "quotes": ["MN // BC"], "reason": "parallel"},
])
def test_unsupported_and_ambiguous_exits_need_no_invented_operand(exit_):
    assert fx.schema_accepts(ITEM, exit_)


def test_every_variant_requires_at_least_what_the_planner_requires():
    # A variant may demand more (the goal's operands), never less than the planner's own required slots.
    for v in ITEM["anyOf"]:
        kind = v["properties"]["kind"]["enum"]
        assert len(kind) == 1
        req, need = set(v["required"]), set(_CAN[kind[0]])
        # the planner's own overrides in `doc_du_kien`: relational plane, referenced line, intersection point
        if "plane_relation" in req:
            need = {"solid", "point", "points_b"}
        elif "line_ref" in req and kind[0] == "projection":
            need = {"point", "at", "line_ref"}
        elif kind[0] == "point_def" and set(v["properties"]["point_kind"]["enum"]) <= {"intersect_line_line", "intersect_line_plane"}:
            need = {"point", "point_kind", "points_a", "points_b"}
        assert need <= req, (kind, v["required"])
        assert {"id", "kind", "role", "quotes"} <= set(v["required"])


# ── provider compatibility: the documented Gemini Schema subset only, bounded size ───────────────────────────────

ALLOWED = {"type", "format", "description", "nullable", "enum", "maxItems", "minItems", "properties", "required",
           "pattern", "items", "anyOf", "minLength", "maxLength", "propertyOrdering"}


def _keys(node):
    if isinstance(node, dict):
        for k, v in node.items():
            yield k
            if k == "properties":
                for p in v.values():
                    yield from _keys(p)
            elif k in ("items",):
                yield from _keys(v)
            elif k == "anyOf":
                for x in v:
                    yield from _keys(x)


def test_v3_uses_only_the_documented_schema_subset_and_stays_bounded():
    assert set(_keys(V3)) <= ALLOWED, set(_keys(V3)) - ALLOWED
    size = len(json.dumps(V3, ensure_ascii=False))
    assert size < 7 * len(json.dumps(fx.facts_response_schema(), ensure_ascii=False)), size


def test_existing_served_described_point_to_result_line_fits_v3():
    from app.ai.function_route import run_fact_route
    data = json.loads((RUNS / "goal-directed-function-discovery/corpus.json").read_text(encoding="utf-8"))
    cases = [c for c in data["positive"] if c["id"] in
             ("pyr-midpoint-to-result-line", "cuboid-midpoint-to-result-line")]
    assert len(cases) == 2
    for c in cases:
        assert run_fact_route(c["text"], c["payload"]).status == "SERVED"
        assert fx.schema_accepts(V3, c["payload"]), c["id"]


@pytest.mark.parametrize("a,b", [(["A"], ["B"]), (["A", "B"], ["C"]), (["A", "B", "C"], ["S"])])
def test_distance_preserves_both_operand_orientations(a, b):
    assert fx.schema_accepts(ITEM, q(quantity="distance", points_a=a, points_b=b))


@pytest.mark.parametrize("bad", [
    {"id": "p", "kind": "point_def", "role": "premise", "quotes": ["M là trung điểm AB"],
     "point": "M", "point_kind": "midpoint", "points": ["A", "B", "C"]},
    {"id": "p", "kind": "point_def", "role": "premise", "quotes": ["G là trọng tâm ABC"],
     "point": "G", "point_kind": "centroid", "points": ["A", "B"]},
    {"id": "p", "kind": "point_def", "role": "premise", "quotes": ["M = AB giao (SCD)"],
     "point": "M", "point_kind": "intersect_line_plane", "points_a": ["A", "B"], "points_b": ["S", "C"]},
    {"id": "s", "kind": "section", "role": "question", "quotes": ["Dựng thiết diện"], "solid": "S.ABCD",
     "point": "M", "points_b": ["A", "B"], "plane_relation": "parallel_two_lines"},
    q(quantity="area", solid="S.ABCD", point="M", points_b=["A", "B"], plane_relation="parallel"),
])
def test_discriminated_operand_arities_cannot_be_omitted(bad):
    assert not fx.schema_accepts(ITEM, bad)


@pytest.mark.parametrize("extra", [{"negated": None}, {"bogus": None}])
def test_null_fields_do_not_bypass_contract_validation(extra):
    assert not fx.schema_accepts(ITEM, q(quantity="length", points=["A", "B"], **extra))


def test_nullable_property_accepts_null_only_when_declared():
    assert fx.schema_accepts({"type": "STRING", "nullable": True}, None)
    assert not fx.schema_accepts({"type": "STRING"}, None)


@pytest.mark.parametrize("bad", [q(id="", quantity="length", points=["A", "B"]),
    {"id": "u", "kind": "unsupported", "role": "prove", "quotes": ["MN // BC"], "reason": "parallel", "value": "MN // BC"}])
def test_v3_never_widens_typedfact_id_or_numeric_value(bad):
    assert not fx.schema_accepts(ITEM, bad)


def test_v3_checks_the_returned_contract_before_planning(monkeypatch):
    monkeypatch.setattr(fx, "RESPONSE_CONTRACT", "v3")
    malformed = {"facts": [q(quantity="distance", points_a=["A"])]}
    body = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(malformed)}]}}]}
    result = fx.run_ai_fact_route("Tính khoảng cách từ A đến (BCD).", lambda _: body)
    assert (result.status, result.code) == ("REFUSED", "SCHEMA_INVALID")
