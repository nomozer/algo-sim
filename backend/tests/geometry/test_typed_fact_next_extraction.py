"""Source-only extraction boundary: replay and fake transport, never a provider call."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
import importlib.util
import json

import pytest


TEXT = "Cho hình chóp S.ABC. Dựng hình chóp S.ABC."


def payload(text=TEXT):
    return {
        "schema_version": "typed-fact-next/2", "problem_text": text,
        "solids": [{"solid_id": "pyr", "notation": "S.ABC", "quote": "Cho hình chóp S.ABC."}],
        "simulation_goals": [{"goal_id": "g", "kind": "construct_object", "target_solid_id": "pyr",
                              "quote": "Dựng hình chóp S.ABC."}],
    }


def test_product_extraction_seam_exists():
    assert importlib.util.find_spec("app.ai.typed_fact_next_extraction") is not None


def test_replay_copies_source_only_output_and_never_claims_semantic_verification():
    from app.ai.typed_fact_next_extraction import ReplayExtractor, extract_typed_fact_next_v2
    raw = payload()
    replay = ReplayExtractor({TEXT: raw})
    result = extract_typed_fact_next_v2(TEXT, replay)
    assert result.code is None and result.payload.schema_version == "typed-fact-next/2"
    assert result.diagnostics["validation"] == "SCHEMA_AND_SOURCE_IDENTITY/QUOTE_VALID"
    assert result.diagnostics["semantic_gate"] == "NOT_EXECUTED"
    copy = replay.extract(TEXT)
    copy["solids"][0]["quote"] = "changed"
    assert raw["solids"][0]["quote"] == "Cho hình chóp S.ABC."


@pytest.mark.parametrize("change,code", [
    (lambda p: p.update(schema_version="typed-fact-next/1"), "SCHEMA_VERSION_MISMATCH"),
    (lambda p: p.update(problem_text=" " + TEXT), "REPLAY_SOURCE_IDENTITY_MISMATCH"),
    (lambda p: p["simulation_goals"][0].update(quote="Dựng một khối khác."), "QUOTE_NOT_IN_SOURCE"),
    (lambda p: p["solids"][0].update(coordinates=[0, 0, 0]), "INVALID_TYPED_FACT_NEXT"),
    (lambda p: p.update(negated=False), "INVALID_TYPED_FACT_NEXT"),
    (lambda p: p.update(simulation_goals=[]), "EMPTY_SIMULATION_GOALS"),
])
def test_invalid_or_unbound_extraction_is_refused(change, code):
    from app.ai.typed_fact_next_extraction import ReplayExtractor, extract_typed_fact_next_v2
    raw = payload()
    change(raw)
    result = extract_typed_fact_next_v2(TEXT, ReplayExtractor({TEXT: raw}))
    assert result.payload is None and result.code == code


@pytest.mark.parametrize("change,code", [
    (lambda p: p["simulation_goals"][0].update(target_solid_id="nope"), "UNKNOWN_SOLID_ID"),   # raised in a validator
    (lambda p: p["solids"][0].update(coordinates=[0, 0, 0]), "INVALID_TYPED_FACT_NEXT"),       # control: plain schema
])
def test_a_refused_extraction_releases_its_payload_and_error(change, code):
    """Found by the bounded load check of run `hybrid-backend-reliability`: live parsed payloads grew by one per refused
    request, forever. `_parse` re-raised the validator's error `from` pydantic's ValidationError inside the `except`
    block; that ValidationError holds the same error in `errors()[i]['ctx']`, so error → cause/traceback frame →
    ValidationError → error is a cycle through a pydantic-core object, which gc.collect() never freed."""
    import gc

    from app.ai.typed_fact_next_extraction import ReplayExtractor, extract_typed_fact_next_v2
    from app.simulation.geometry_functions.typed_fact_next import TypedFactNextValidationError

    def live() -> int:
        gc.collect()
        return sum(1 for o in gc.get_objects() if isinstance(o, TypedFactNextValidationError))

    raw = payload()
    change(raw)
    before = live()
    for _ in range(50):
        assert extract_typed_fact_next_v2(TEXT, ReplayExtractor({TEXT: deepcopy(raw)})).code == code
    assert live() - before <= 1


def test_unknown_replay_source_is_an_explicit_extraction_failure():
    from app.ai.typed_fact_next_extraction import ReplayExtractor, extract_typed_fact_next_v2
    result = extract_typed_fact_next_v2(TEXT, ReplayExtractor({}))
    assert result.payload is None and result.code == "NO_RECORDED_EXTRACTION"


def test_source_identity_preserves_legitimate_outer_whitespace():
    from app.ai.typed_fact_next_extraction import ReplayExtractor, extract_typed_fact_next_v2
    text = " \n" + TEXT + "\n "
    result = extract_typed_fact_next_v2(text, ReplayExtractor({text: payload(text)}))
    assert result.code is None and result.payload.problem_text == text


def test_quote_whitespace_is_checked_before_schema_strips_it():
    from app.ai.typed_fact_next_extraction import ReplayExtractor, extract_typed_fact_next_v2
    raw = payload()
    raw["simulation_goals"][0]["quote"] += " "
    result = extract_typed_fact_next_v2(TEXT, ReplayExtractor({TEXT: raw}))
    assert result.payload is None and result.code == "QUOTE_NOT_IN_SOURCE"


@pytest.mark.parametrize("prefix,code", [
    ("Nếu ", "CONDITIONAL_CLAUSE"), ("Không phải ", "NEGATED_CLAUSE"),
    ("Chứng minh rằng ", "GOAL_CLAUSE_NOT_PREMISE"),
])
def test_premise_quote_cannot_hide_its_enclosing_clause_role(prefix, code):
    from app.ai.typed_fact_next_extraction import ReplayExtractor, extract_typed_fact_next_v2
    clause = "SA vuông góc với (ABC)"
    text = TEXT + " " + prefix + clause + "."
    raw = payload(text)
    raw["premises"] = [{"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]},
                        "quote": clause}]
    result = extract_typed_fact_next_v2(text, ReplayExtractor({text: raw}))
    assert result.payload is None and result.code == code


def test_extractor_fault_is_sanitized():
    from app.ai.typed_fact_next_extraction import extract_typed_fact_next_v2
    class Broken:
        def extract(self, problem_text):
            raise RuntimeError("secret provider body")
    result = extract_typed_fact_next_v2(TEXT, Broken())
    assert result.payload is None and result.code == "EXTRACTOR_INTERNAL_ERROR"
    assert "secret" not in repr(result)


def body(raw, finish="STOP"):
    return {"candidates": [{"finishReason": finish, "content": {"parts": [{"text": json.dumps(raw)}]}}]}


def test_transport_requests_canonical_v2_and_runs_one_source_only_call():
    from app.ai.typed_fact_next_extraction import TransportExtractor, extract_typed_fact_next_v2
    requests = []
    def transport(request):
        requests.append(deepcopy(request))
        return body(payload())
    result = extract_typed_fact_next_v2(TEXT, TransportExtractor(transport))
    assert result.code is None and result.payload.problem_text == TEXT
    assert len(requests) == 1
    request = requests[0]
    assert TEXT in request["contents"][0]["parts"][0]["text"]
    assert "tools" not in request
    schema = request["generationConfig"]["responseSchema"]
    assert "solids" in schema["properties"] and "facts" not in schema["properties"]


@pytest.mark.parametrize("response,code", [
    (body(payload(), "MAX_TOKENS"), "RESPONSE_TRUNCATED"),
    ({"candidates": []}, "NO_CANDIDATE"),
    ({"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "{"}]}}]}, "JSON_INVALID"),
    (body({"facts": []}), "SCHEMA_VERSION_MISMATCH"),
])
def test_transport_failure_or_legacy_payload_never_reaches_canonical_output(response, code):
    from app.ai.typed_fact_next_extraction import TransportExtractor, extract_typed_fact_next_v2
    result = extract_typed_fact_next_v2(TEXT, TransportExtractor(lambda request: response))
    assert result.payload is None and result.code == code


def test_transport_exception_does_not_leak_details():
    from app.ai.typed_fact_next_extraction import TransportExtractor, extract_typed_fact_next_v2
    def transport(request):
        raise RuntimeError("private token")
    result = extract_typed_fact_next_v2(TEXT, TransportExtractor(transport))
    assert result.payload is None and result.code == "PROVIDER_ERROR"
    assert "private token" not in repr(result)


def test_source_references_keep_all_occurrences_in_original_unicode_source():
    from app.ai.typed_fact_next_extraction import ReplayExtractor, extract_typed_fact_next_v2

    text = " \n" + TEXT + "\n " + TEXT
    raw = payload(text)
    result = extract_typed_fact_next_v2(text, ReplayExtractor({text: raw}))
    assert result.code is None
    references = {ref.path: ref for ref in result.source_references}
    assert set(references) == {("solids", 0, "quote"), ("simulation_goals", 0, "quote")}
    for path, quote in [(('solids', 0, 'quote'), raw['solids'][0]['quote']),
                        (('simulation_goals', 0, 'quote'), raw['simulation_goals'][0]['quote'])]:
        spans = references[path].spans
        assert len(spans) == 2
        assert [text[start:end] for start, end in spans] == [quote, quote]
        assert spans[0][0] < spans[1][0]
    assert references[("solids", 0, "quote")].spans[0][0] == 2


def test_source_references_are_immutable_and_detached_from_extractor_output():
    from app.ai.typed_fact_next_extraction import extract_typed_fact_next_v2

    raw = payload()
    class LocalExtractor:
        def extract(self, source_text):
            return raw

    result = extract_typed_fact_next_v2(TEXT, LocalExtractor())
    original = result.source_references
    raw["solids"][0]["quote"] = "changed after extraction"
    assert isinstance(original, tuple) and original
    assert result.source_references == original
    with pytest.raises(FrozenInstanceError):
        original[0].spans = ()
    assert all(isinstance(ref.spans, tuple) and isinstance(ref.path, tuple) for ref in original)


def test_role_refusal_exposes_no_partial_source_reference_evidence():
    from app.ai.typed_fact_next_extraction import ReplayExtractor, extract_typed_fact_next_v2

    text = TEXT + " Chứng minh rằng SA vuông góc với (ABC)."
    raw = payload(text)
    raw["premises"] = [{"kind": "perpendicular_line_plane",
                        "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]},
                        "quote": "SA vuông góc với (ABC)"}]
    result = extract_typed_fact_next_v2(text, ReplayExtractor({text: raw}))
    assert result.code == "GOAL_CLAUSE_NOT_PREMISE" and result.payload is None
    assert result.source_references == ()


def test_provider_cannot_supply_its_own_source_reference_certificate():
    from app.ai.typed_fact_next_extraction import ReplayExtractor, extract_typed_fact_next_v2

    raw = payload()
    raw["source_references"] = [{"path": ["solids", 0, "quote"], "spans": [[0, len(TEXT)]]}]
    result = extract_typed_fact_next_v2(TEXT, ReplayExtractor({TEXT: raw}))
    assert result.code == "INVALID_TYPED_FACT_NEXT" and result.payload is None
    assert result.source_references == ()


def test_overlapping_occurrences_are_all_reported():
    from app.ai.typed_fact_next_extraction import _occurrences

    assert _occurrences("S.AAA", "AA") == ((2, 4), (3, 5))


_GEMINI_SCHEMA_KEYS = {
    "type", "description", "required", "items", "properties", "propertyOrdering",
}
_GEMINI_TYPES = {"OBJECT", "ARRAY", "STRING", "INTEGER", "NUMBER", "BOOLEAN"}
_FORBIDDEN_FSM_BLOWUP_KEYS = {
    "pattern", "minLength", "maxLength", "minItems", "maxItems", "nullable", "enum", "anyOf",
}


def _walk_gemini_schema(node, path="root"):
    assert isinstance(node, dict), f"{path} is not a dict"
    assert not (set(node) & _FORBIDDEN_FSM_BLOWUP_KEYS), (
        f"{path} contains FSM-expanding keys {set(node) & _FORBIDDEN_FSM_BLOWUP_KEYS}"
    )
    assert set(node) <= _GEMINI_SCHEMA_KEYS, f"{path} has unsupported keys {set(node) - _GEMINI_SCHEMA_KEYS}"
    t = node.get("type")
    assert t in _GEMINI_TYPES, f"{path} has invalid type {t!r}"
    if t == "ARRAY":
        assert isinstance(node.get("items"), dict), f"{path} ARRAY missing items"
        _walk_gemini_schema(node["items"], f"{path}.items")
    if t == "OBJECT":
        props = node.get("properties")
        assert isinstance(props, dict) and props, f"{path} OBJECT missing non-empty properties"
        req = node.get("required") or []
        assert set(req) <= set(props), f"{path} required keys not in properties"
        assert node.get("propertyOrdering") == list(props.keys()), f"{path} missing exact propertyOrdering"
        assert len(props) - len(req) <= 4, f"{path} has >4 optional properties ({len(props) - len(req)})"
        for k, v in props.items():
            _walk_gemini_schema(v, f"{path}.properties[{k}]")


def test_transport_response_schema_is_valid_compact_gemini_v1beta_subset():
    from app.ai.fact_extraction import facts_response_schema, surface_fingerprint as fe_fp
    from app.ai.function_calling import surface_fingerprint as fc_fp
    from app.ai.typed_fact_next_extraction import build_typed_fact_next_v2_request

    schema = build_typed_fact_next_v2_request(TEXT)["generationConfig"]["responseSchema"]
    _walk_gemini_schema(schema)

    def _strip_po(n):
        return {k: (_strip_po(v) if isinstance(v, dict) else v) for k, v in n.items() if k != "propertyOrdering"}

    flat_bytes = len(json.dumps(facts_response_schema("flat"), ensure_ascii=False).encode("utf-8"))
    v2_bytes = len(json.dumps(schema, ensure_ascii=False).encode("utf-8"))
    v2_struct_bytes = len(json.dumps(_strip_po(schema), ensure_ascii=False).encode("utf-8"))
    assert v2_struct_bytes < flat_bytes and v2_bytes <= 4500, (
        f"v2 wire schema too large: total={v2_bytes}, struct={v2_struct_bytes}, flat={flat_bytes}"
    )

    order = schema["propertyOrdering"]
    assert order.index("solids") < order.index("described_points") < order.index("derived_sections")
    assert order.index("derived_sections") < order.index("simulation_goals") < order.index("math_goals")

    vb = schema["properties"]["solids"]["items"]["properties"]["vertex_bindings"]
    assert vb == {"type": "ARRAY", "items": {"type": "STRING"}}

    assert fc_fp() == "7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25"
    assert fe_fp("flat") == "485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a"
    assert fe_fp("v3") == "4bff35bbf690a9973b2b7834019b908d507bbbb4277928e36d12dcff657e226f"


def _pad_constrained_decoding(schema: dict, value):
    """Simulate Gemini constrained decoding emitting explicit empty-array placeholders for optional list properties."""
    if value is None:
        return None
    t = schema.get("type")
    if t == "ARRAY":
        return [_pad_constrained_decoding(schema["items"], item) for item in value]
    if t == "OBJECT" and isinstance(value, dict):
        props = schema["properties"]
        req = set(schema.get("required") or ())
        out = {}
        for k in schema["propertyOrdering"]:
            sub = props[k]
            if k in value:
                out[k] = _pad_constrained_decoding(sub, value[k])
            elif sub.get("type") == "ARRAY":
                out[k] = []
            elif sub.get("type") == "STRING" and k not in req:
                out[k] = ""
        return out
    return value


def test_transport_schema_and_normalizer_preserve_all_pilot_gold_payloads():
    from pathlib import Path
    from scripts import run_s2_student_language_pilot as R
    from app.ai.fact_extraction import schema_accepts
    from app.ai.typed_fact_next_extraction import (
        TransportExtractor,
        build_typed_fact_next_v2_request,
        extract_typed_fact_next_v2,
        to_wire_typed_fact_next_v2,
    )
    from app.simulation.geometry_functions.typed_fact_next import parse_typed_fact_next_v2

    schema = build_typed_fact_next_v2_request(TEXT)["generationConfig"]["responseSchema"]
    base = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement"
    checked = 0
    for fname in ("k1-live-pilot-corpus.json", "s2-student-language-pilot-corpus.json", "r1-live-pilot-corpus.json"):
        corpus = json.loads((base / fname).read_text(encoding="utf-8"))
        for case in corpus["cases"]:
            gold = case["gold_extraction"]
            wire_gold = to_wire_typed_fact_next_v2(gold)
            assert schema_accepts(schema, wire_gold), f"{fname}:{case['id']} rejected by responseSchema"
            padded = _pad_constrained_decoding(schema, wire_gold)
            assert schema_accepts(schema, padded), f"{fname}:{case['id']} padded rejected by responseSchema"
            for candidate_wire in (wire_gold, padded, gold):
                ext = TransportExtractor(lambda _req, p=candidate_wire: body(p))
                raw_norm = ext.extract(case["problem_text"])
                res = extract_typed_fact_next_v2(
                    case["problem_text"], TransportExtractor(lambda _req, p=candidate_wire: body(p))
                )
                assert res.code is None, f"{fname}:{case['id']} failed extraction with {res.code}"
                assert res.payload == parse_typed_fact_next_v2(gold)
                assert R.project(raw_norm) == R.project(gold), f"{fname}:{case['id']} projection drift"
            checked += 1
    assert checked == 70


def test_transport_normalizer_unpacks_entries_and_fails_closed_on_malformed_wire_entries():
    from app.ai.fact_extraction import schema_accepts
    from app.ai.typed_fact_next_extraction import (
        TransportExtractor,
        build_typed_fact_next_v2_request,
        extract_typed_fact_next_v2,
        to_wire_typed_fact_next_v2,
    )

    schema = build_typed_fact_next_v2_request(TEXT)["generationConfig"]["responseSchema"]
    rich_text = (
        "Cho hình chóp S.ABC và S.DBC chung mặt (SBC), SA = 2. "
        "Mặt phẳng (P) đi qua trung điểm của SA và song song với (ABC). "
        "Dựng hình chóp S.ABC và tính diện tích thiết diện."
    )
    rich_canonical = {
        "schema_version": "typed-fact-next/2",
        "problem_text": rich_text,
        "length_unit": "1",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "pyramid",
                "notation": "S.ABC",
                "quote": "Cho hình chóp S.ABC",
                "vertex_bindings": {"S": "S", "A": "A"},
            },
            {
                "solid_id": "s2",
                "solid_type": "pyramid",
                "notation": "S.DBC",
                "quote": "S.DBC",
            },
        ],
        "premises": [
            {
                "kind": "segment_length",
                "args": {"segment": ["s1::S", "s1::A"], "value": "2"},
                "quote": "SA = 2",
                "solid_id": "s1",
            }
        ],
        "described_points": [
            {
                "described_id": "m1",
                "kind": "midpoint",
                "segment": ["s1::S", "s1::A"],
                "quote": "trung điểm của SA",
            }
        ],
        "derived_sections": [
            {
                "section_id": "sec1",
                "plane_name": "P",
                "target_solid_id": "s1",
                "plane_kind": "through_point_parallel_plane",
                "through_point": "@m1",
                "parallel_plane": ["s1::A", "s1::B", "s1::C"],
                "stated_intersections": [],
                "quote": "Mặt phẳng (P) đi qua trung điểm của SA và song song với (ABC)",
            }
        ],
        "relations": [
            {
                "relation_id": "r1",
                "kind": "shared_vertices",
                "pairs": [["s1::S", "s2::S"], ["s1::B", "s2::B"], ["s1::C", "s2::C"]],
                "quote": "chung mặt (SBC)",
            }
        ],
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "s1",
                "quote": "Dựng hình chóp S.ABC",
            }
        ],
        "math_goals": [
            {
                "goal_id": "mg1",
                "kind": "measurement",
                "goal_type": "area",
                "solid_id": "s1",
                "target": {"section_id": "sec1"},
                "quote": "tính diện tích thiết diện",
            }
        ],
    }
    wire_rich = to_wire_typed_fact_next_v2(rich_canonical)
    assert schema_accepts(schema, wire_rich)
    res_rich = extract_typed_fact_next_v2(rich_text, TransportExtractor(lambda _req: body(wire_rich)))
    assert res_rich.code is None
    assert res_rich.payload.solids[0].vertex_bindings == {"S": "S", "A": "A"}
    assert res_rich.payload.relations[0].pairs == (("s1::S", "s2::S"), ("s1::B", "s2::B"), ("s1::C", "s2::C"))

    blank_opt_text = "Mặt phẳng (P) đi qua A, B và vuông góc với một mặt bên."
    blank_opt_wire = {
        "schema_version": "typed-fact-next/2",
        "problem_text": blank_opt_text,
        "length_unit": "1",
        "solids": [],
        "premises": [],
        "simulation_goals": [],
        "math_goals": [],
        "unresolved": [{
            "unresolved_id": "u1",
            "kind": "ambiguous",
            "subject_ref": "",
            "missing_roles": ["target_line_or_plane"],
            "candidate_relations": ["perpendicular"],
            "quote": "vuông góc với một mặt bên",
        }],
    }
    res_blank = extract_typed_fact_next_v2(blank_opt_text, TransportExtractor(lambda _req: body(blank_opt_wire)))
    assert res_blank.code is None and res_blank.payload.unresolved[0].subject_ref is None

    for mutate, expected_code in [
        (lambda w: w["solids"][0].update(vertex_bindings=["A=A1", "A=A2"]),
         "INVALID_TYPED_FACT_NEXT"),
        (lambda w: w["premises"][0].update(args=["value=2", "value=3"]),
         "INVALID_TYPED_FACT_NEXT"),
        (lambda w: w["premises"][0].update(args=["segment_without_equals"]),
         "INVALID_TYPED_FACT_NEXT"),
        (lambda w: w["premises"][0].update(args=["segment=S,,A"]),
         "INVALID_TYPED_FACT_NEXT"),
        (lambda w: w["solids"][0].update(params=["quote=Cho hình chóp S.ABC."]),
         "INVALID_TYPED_FACT_NEXT"),
        (lambda w: w.update(math_goals=[{
            "goal_id": "m1", "kind": "measurement", "goal_type": "volume", "solid_id": "pyr",
            "target": ["solid_id=pyr"],
            "params": ["numerator_solid_id=pyr"],
            "quote": "Dựng hình chóp S.ABC.",
        }]), "INVALID_MATH_GOAL"),
    ]:
        bad = to_wire_typed_fact_next_v2({
            **payload(),
            "length_unit": "1",
            "solids": [{**payload()["solids"][0], "solid_type": "pyramid"}],
            "premises": [{"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "2"},
                          "quote": "Cho hình chóp S.ABC.", "solid_id": "pyr"}],
        })
        mutate(bad)
        res_bad = extract_typed_fact_next_v2(TEXT, TransportExtractor(lambda _req, b=bad: body(b)))
        assert res_bad.payload is None and res_bad.code == expected_code


def test_transport_normalizer_handles_observed_live_gemini_wire_patterns():
    from app.ai.typed_fact_next_extraction import TransportExtractor, extract_typed_fact_next_v2

    sec_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD) và SA = 2. "
        "Mặt phẳng (P) đi qua A, B và vuông góc với (SBD). "
        "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó."
    )
    sec_wire = {
        "schema_version": "typed-fact-next/2",
        "problem_text": sec_text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "hình chóp S.ABCD"}],
        "premises": [
            {"kind": "regular_polygon", "args": ["vertices=A,B,C,D", "side=2"], "quote": "đáy ABCD là hình vuông cạnh 2", "solid_id": "s1"},
            {"kind": "perpendicular_line_plane", "args": ["line=S,A", "plane=A,B,C,D"], "quote": "SA vuông góc với (ABCD)", "solid_id": "s1"},
            {"kind": "segment_length", "args": ["segment=S,A", "value=2"], "quote": "SA = 2", "solid_id": "s1"},
        ],
        "derived_sections": [{
            "section_id": "sec1",
            "plane_name": "P",
            "target_solid_id": "s1",
            "plane_kind": "constrained",
            "constraints": ["contains_points=A,B", "perpendicular_to_plane=S,B,D"],
            "quote": "Mặt phẳng (P) đi qua A, B và vuông góc với (SBD)",
        }],
        "simulation_goals": [
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "hình chóp S.ABCD"},
            {"goal_id": "sg2", "kind": "construct_object", "target_section_id": "sec1", "quote": "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P)"},
        ],
        "math_goals": [{
            "goal_id": "mg1",
            "kind": "measurement",
            "goal_type": "area",
            "target": ["section_id=sec1"],
            "quote": "tính diện tích thiết diện đó",
        }],
    }
    ext = TransportExtractor(lambda _req: body(sec_wire))
    norm_dict = ext.extract(sec_text)
    assert norm_dict["simulation_goals"][1]["kind"] == "construct_plane_section"
    assert norm_dict["math_goals"][0]["solid_id"] == "s1"
    res_sec = extract_typed_fact_next_v2(sec_text, ext)
    assert res_sec.code is None
    assert res_sec.payload.simulation_goals[1].kind == "construct_plane_section"
    assert res_sec.payload.math_goals[0].solid_id == "s1"

    # Conflicting both target_solid_id + target_section_id on construct_object must still fail closed.
    both_targets = deepcopy(sec_wire)
    both_targets["simulation_goals"][1]["target_solid_id"] = "s1"
    res_conflict = extract_typed_fact_next_v2(sec_text, TransportExtractor(lambda _req: body(both_targets)))
    assert res_conflict.payload is None and res_conflict.code == "INVALID_SIMULATION_GOAL"

    # Unresolved wire hints outside closed enums filter cleanly without crashing UnresolvedSpec,
    # while an invalid unresolved kind still fails closed.
    amb_text = "Tính khoảng cách từ trực tâm của một tam giác có ba đỉnh thuộc hình chóp đến mặt phẳng (SAB)."
    amb_wire = {
        "schema_version": "typed-fact-next/2",
        "problem_text": amb_text,
        "length_unit": "1",
        "solids": [],
        "premises": [],
        "simulation_goals": [],
        "math_goals": [],
        "unresolved": [{
            "unresolved_id": "u1",
            "kind": "ambiguous",
            "missing_roles": ["polygon", "source_point"],
            "candidate_relations": ["orthocenter", "distance"],
            "quote": "trực tâm của một tam giác có ba đỉnh thuộc hình chóp",
        }],
    }
    res_amb = extract_typed_fact_next_v2(amb_text, TransportExtractor(lambda _req: body(amb_wire)))
    assert res_amb.code is None
    assert res_amb.payload.unresolved[0].missing_roles == ("source_point",)
    assert res_amb.payload.unresolved[0].candidate_relations == ("distance",)

    bad_unres = deepcopy(amb_wire)
    bad_unres["unresolved"][0]["kind"] = "invented_kind"
    res_bad_unres = extract_typed_fact_next_v2(amb_text, TransportExtractor(lambda _req: body(bad_unres)))
    assert res_bad_unres.payload is None and res_bad_unres.code == "INVALID_TYPED_FACT_NEXT"

