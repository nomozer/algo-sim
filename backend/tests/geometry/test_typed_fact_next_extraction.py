"""Source-only extraction boundary: replay and fake transport, never a provider call."""
from copy import deepcopy
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
