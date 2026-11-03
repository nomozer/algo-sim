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
    "type", "description", "enum", "required", "minItems", "maxItems",
    "pattern", "minLength", "maxLength", "nullable", "items", "properties",
}
_GEMINI_TYPES = {"OBJECT", "ARRAY", "STRING", "INTEGER", "NUMBER", "BOOLEAN"}


def _walk_gemini_schema(node, path="root"):
    assert isinstance(node, dict), f"{path} is not a dict"
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
        for k, v in props.items():
            _walk_gemini_schema(v, f"{path}.properties[{k}]")


def test_transport_response_schema_is_valid_gemini_v1beta_openapi_subset():
    from app.ai.fact_extraction import surface_fingerprint as fe_fp
    from app.ai.function_calling import surface_fingerprint as fc_fp
    from app.ai.typed_fact_next_extraction import build_typed_fact_next_v2_request
    from app.simulation.geometry_functions.typed_fact_next import (
        GOAL_OPERAND_SHAPES,
        _ARGS_GOC_VUONG,
        _ARGS_LOI,
    )

    schema = build_typed_fact_next_v2_request(TEXT)["generationConfig"]["responseSchema"]
    _walk_gemini_schema(schema)

    expected_arg_keys = {k for m in (*_ARGS_LOI.values(), *_ARGS_GOC_VUONG) for k in m}
    arg_props = schema["properties"]["premises"]["items"]["properties"]["args"]["properties"]
    assert set(arg_props) == expected_arg_keys

    target_props = schema["properties"]["math_goals"]["items"]["properties"]["target"]["properties"]
    assert set(target_props) == set(GOAL_OPERAND_SHAPES)

    vb = schema["properties"]["solids"]["items"]["properties"]["vertex_bindings"]
    assert vb["type"] == "ARRAY" and set(vb["items"]["properties"]) == {"local", "canonical"}

    assert fc_fp() == "7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25"
    assert fe_fp("flat") == "485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a"
    assert fe_fp("v3") == "4bff35bbf690a9973b2b7834019b908d507bbbb4277928e36d12dcff657e226f"


def _pad_constrained_decoding(schema: dict, value):
    """Simulate Gemini constrained decoding emitting explicit null/default placeholders for unused properties."""
    if value is None:
        return None
    t = schema.get("type")
    if t == "ARRAY":
        return [_pad_constrained_decoding(schema["items"], item) for item in value]
    if t == "OBJECT" and isinstance(value, dict):
        props = schema["properties"]
        out = {}
        for k, sub in props.items():
            if k in value:
                out[k] = _pad_constrained_decoding(sub, value[k])
            elif sub.get("nullable"):
                out[k] = None
            elif sub.get("type") == "ARRAY":
                out[k] = []
            elif k == "coordinate_frame_id":
                out[k] = "root"
            elif k == "style_role":
                out[k] = "primary"
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
    )
    from app.simulation.geometry_functions.typed_fact_next import parse_typed_fact_next_v2

    schema = build_typed_fact_next_v2_request(TEXT)["generationConfig"]["responseSchema"]
    base = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement"
    checked = 0
    for fname in ("k1-live-pilot-corpus.json", "s2-student-language-pilot-corpus.json", "r1-live-pilot-corpus.json"):
        corpus = json.loads((base / fname).read_text(encoding="utf-8"))
        for case in corpus["cases"]:
            gold = case["gold_extraction"]
            wire_gold = deepcopy(gold)
            for s in wire_gold.get("solids") or []:
                if isinstance(s.get("vertex_bindings"), dict):
                    s["vertex_bindings"] = [{"local": k, "canonical": v} for k, v in s["vertex_bindings"].items()]
            assert schema_accepts(schema, wire_gold), f"{fname}:{case['id']} rejected by responseSchema"
            padded = _pad_constrained_decoding(schema, wire_gold)
            assert schema_accepts(schema, padded), f"{fname}:{case['id']} padded rejected by responseSchema"
            ext = TransportExtractor(lambda _req, p=padded: body(p))
            raw_norm = ext.extract(case["problem_text"])
            res = extract_typed_fact_next_v2(case["problem_text"], TransportExtractor(lambda _req, p=padded: body(p)))
            assert res.code is None, f"{fname}:{case['id']} failed extraction with {res.code}"
            assert res.payload == parse_typed_fact_next_v2(gold)
            assert R.project(raw_norm) == R.project(gold), f"{fname}:{case['id']} projection drift"
            checked += 1
    assert checked == 70


def test_transport_normalizer_unpacks_vertex_bindings_and_refuses_non_null_inapplicable_fields():
    from app.ai.typed_fact_next_extraction import TransportExtractor, extract_typed_fact_next_v2

    raw = payload()
    raw["solids"][0]["solid_type"] = "pyramid"
    raw["solids"][0]["vertex_bindings"] = [{"local": "S", "canonical": "S"}, {"local": "A", "canonical": "A1"}]
    res = extract_typed_fact_next_v2(TEXT, TransportExtractor(lambda _req: body(raw)))
    assert res.code is None
    assert res.payload.solids[0].vertex_bindings == {"S": "S", "A": "A1"}

    dup = payload()
    dup["solids"][0]["solid_type"] = "pyramid"
    dup["solids"][0]["vertex_bindings"] = [{"local": "A", "canonical": "A1"}, {"local": "A", "canonical": "A2"}]
    res_dup = extract_typed_fact_next_v2(TEXT, TransportExtractor(lambda _req: body(dup)))
    assert res_dup.payload is None and res_dup.code == "INVALID_TYPED_FACT_NEXT"

    bad = payload()
    bad["math_goals"] = [{"goal_id": "m1", "kind": "measurement", "goal_type": "volume",
                          "target": {"solid_id": "pyr"}, "numerator_solid_id": "pyr",
                          "quote": "Dựng hình chóp S.ABC."}]
    res_bad = extract_typed_fact_next_v2(TEXT, TransportExtractor(lambda _req: body(bad)))
    assert res_bad.payload is None and res_bad.code == "INVALID_MATH_GOAL"
