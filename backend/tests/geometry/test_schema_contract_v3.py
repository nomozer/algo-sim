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


def _structure(node):
    """The schema without descriptions: what the provider must compile into constraints."""
    if isinstance(node, dict):
        return {k: _structure(v) for k, v in node.items() if k != "description"}
    return [_structure(x) for x in node] if isinstance(node, list) else node


def test_v3_uses_only_the_documented_schema_subset_and_stays_bounded():
    assert set(_keys(V3)) <= ALLOWED, set(_keys(V3)) - ALLOWED
    # Regression ceiling on the STRUCTURE the provider must compile (descriptions repeat per variant by design, see the
    # next test; this subset has no $ref). The earlier "< 7 x flat" compared v3-without-descriptions to flat-with-them;
    # like for like the structure was always ~11.7 x flat. Whether Gemini accepts it is NOT_MEASURED (HTTP 400 stops a run).
    # 34 -> 40 (goal-directed-function-composition): questions on a described point now come from the Registry goal
    # contracts — area ×2 descriptors, angle–line ×2, angle–plane ×2 (length kept). Structure 24.5k -> ~29.7k characters;
    # provider acceptance of the larger schema stays NOT_MEASURED (v3 is a research contract, flat is the default).
    assert len(ITEM["anyOf"]) == 40
    assert len(json.dumps(_structure(V3), ensure_ascii=False)) <= 30_000


def test_v3_keeps_every_flat_field_description():
    # The arms must differ in structure only: a lost description ("NGUYÊN VĂN", "ĐỨNG", ambiguous…) would confound them.
    flat = fx.facts_response_schema()["properties"]["facts"]["items"]
    assert ITEM["description"] == flat["description"]
    for variant in ITEM["anyOf"]:
        for k, s in variant["properties"].items():
            if "description" in flat["properties"].get(k, {}) and not (variant["properties"]["kind"]["enum"] == ["right_angle"]
                                                                         and k == "points"):
                assert s.get("description") == flat["properties"][k]["description"], (variant["properties"]["kind"], k)


def test_v3_centroid_keeps_every_named_vertex():
    four = {"id": "p", "kind": "point_def", "role": "premise", "quotes": ["G là trọng tâm tứ giác ABCD"],
            "point": "G", "point_kind": "centroid", "points": ["A", "B", "C", "D"]}
    assert fx.schema_accepts(ITEM, four)


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


_SOLID = {"pyramid": "S.ABC", "prism": "ABC.DEF", "tetrahedron": "ABCD", "cube": "ABCD.EFGH", "cuboid": "ABCD.EFGH"}
_PRODUCER = {"id": "L", "kind": "intersection_line", "role": "premise", "quotes": ["x"],
             "points_a": ["S", "A", "B"], "points_b": ["S", "C", "D"]}


def _minimal_instances(variant):
    """One minimal accepted instance per enum combination of the variant's required slots (labels fresh per instance)."""
    import itertools
    props, req = variant["properties"], variant["required"]
    kind = props["kind"]["enum"][0]
    enums = [k for k in req if k not in ("kind", "role") and len(props[k].get("enum", ())) > 1]
    for combo in itertools.product(*[props[k]["enum"] for k in enums]):
        labels = iter("MNPQRTUVWXYZ")
        inst = {"id": "f", "kind": kind, "role": "question" if kind == "question" else "premise", "quotes": ["x"],
                **dict(zip(enums, combo))}
        for k in (k for k in req if k not in inst):
            s = props[k]
            inst[k] = (s["enum"][0] if s.get("enum") else _SOLID.get(inst.get("solid_type"), "S.ABC") if k == "solid"
                       else "L" if k == "line_ref" else [next(labels) for _ in range(s.get("minItems", 1))] if s["type"] == "ARRAY"
                       else "3" if s.get("pattern") == fx.NUMBER_PATTERN else next(labels) if s.get("pattern") else "r")
        yield inst


def _intake_rejections(item):
    """Accepted v3 shapes that TypedFact or the planner's intake (`doc_du_kien`) rejects as malformed."""
    from app.simulation.geometry_functions.planner import doc_du_kien
    from app.simulation.geometry_functions.registry import TuChoi
    out = []
    for v in item["anyOf"]:
        for inst in _minimal_instances(v):
            assert fx.schema_accepts(item, inst), inst
            try:
                doc_du_kien({"facts": [inst] + ([_PRODUCER] if "line_ref" in inst else [])})
            except TuChoi as e:
                # A described centroid has no Registry builder: an honest capability refusal of a faithful extraction.
                if e.code != "UNSUPPORTED_CAPABILITY":
                    out.append((e.code, inst))
    return out


def test_every_accepted_v3_variant_is_a_well_formed_typedfact():
    assert not _intake_rejections(ITEM)


def test_intake_guard_catches_a_widened_variant():
    import copy
    widened = copy.deepcopy(ITEM)
    two_lines = next(v for v in widened["anyOf"] if v["properties"].get("plane_relation", {}).get("enum") == ["parallel_two_lines"])
    two_lines["required"].remove("points_a")
    assert [code for code, _ in _intake_rejections(widened)] == ["FACT_INCOMPLETE"]


@pytest.mark.parametrize("value", ["1/0", "3/0", "a/0", "2a√3/0", "0/0"])
def test_zero_denominator_is_a_coded_refusal_not_a_crash(value):
    # NUMBER_PATTERN (shared by TypedFact and the v3 provider schema) admits a zero denominator; the reader must refuse it.
    from app.simulation.geometry_functions.registry import TuChoi, doc_so, so_trong
    assert fx.schema_accepts({"type": "STRING", "pattern": fx.NUMBER_PATTERN}, value)
    with pytest.raises(TuChoi) as e:
        doc_so(value)
    assert e.value.code == "SCHEMA_INVALID"
    assert so_trong(f"AB = {value}") == []


def test_v3_checks_the_returned_contract_before_planning(monkeypatch):
    monkeypatch.setattr(fx, "RESPONSE_CONTRACT", "v3")
    malformed = {"facts": [q(quantity="distance", points_a=["A"])]}
    body = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(malformed)}]}}]}
    result = fx.run_ai_fact_route("Tính khoảng cách từ A đến (BCD).", lambda _: body)
    # Its own code, distinct from the planner's SCHEMA_INVALID, so contract violations are countable per arm.
    assert (result.status, result.code) == ("REFUSED", "RESPONSE_CONTRACT_INVALID")
