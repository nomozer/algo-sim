"""Scorer v2 adversaries: source obligations and executed objects, independent of fact pairing."""
from copy import deepcopy

import pytest

from scripts import run_semantic_extraction_evaluation as E


def request(rid="r", points=None, **kw):
    return {"rid": rid, "intent": "calculate", "quantity": "length", "target": {"points": points or ["A", "C'"]},
            "disposition": "answer", "oracle": {"value_squared": "169"}, **kw}


def row(points=None, value="169"):
    return {"status": "SERVED", "answers": {"F5": "13"}, "values": {"F5": value},
            "calls": [{"id": "F5", "fn": "ask_length", "args": {"segment": points or ["A", "C'"]}}],
            "executed_calls": ["F5"], "auxiliary": []}


def test_served_correctness_is_independent_of_raw_fact_pairing():
    # L01 failure mechanism, synthetic receipt: irrelevant TypedFact slots have no place in this API.
    assert E.score_served([request()], row())["classification"] == "CORRECT_COMPLETE"


@pytest.mark.parametrize("r", [row(["A", "B'"]), row(value="144")])
def test_wrong_target_even_with_equal_value_and_wrong_value_are_unsafe(r):
    assert E.score_served([request()], r)["classification"] == "WRONG_SERVED"


def test_recorded_l01_live_facts_are_correct_complete_under_v2_and_frozen_verdict_is_untouched():
    """Real receipt, 0 model calls: the frozen scorer's L01 WRONG_SERVED came from fact pairing, not the served object."""
    import json
    from app.ai.function_route import run_fact_route
    old = E.ROOT / "docs/evaluation/geometry/runs/independent-nlu-extraction-evaluation"
    row_ = next(r for r in json.loads((old / "results/live-locked/manifest.json").read_bytes())["rows"] if r["case_id"] == "L01")
    case = next(c for c in json.loads((old / "inputs/corpus-authoring/corpus.json").read_bytes())["cases"] if c["id"] == "L01")
    (rid, ev), = case["expected_values"].items()
    req = request(rid, points=["A", "C'"], oracle={"value_squared": ev["value_squared"]})
    rec = E.route_record(run_fact_route(case["source_text"], {"facts": deepcopy(row_["facts"])}))
    assert E.score_served([req], rec)["classification"] == "CORRECT_COMPLETE"
    assert E.score_served([request(rid, points=["A", "B'"], oracle=req["oracle"])], rec)["classification"] == "WRONG_SERVED"
    frozen = json.loads((old / "results/live-locked/score.json").read_bytes())
    assert next(s["e2e"] for s in frozen["scored"] if s["case_id"] == "L01") == "WRONG_SERVED"


def test_renamed_ids_do_not_change_the_requested_object():
    r = row()
    r["answers"], r["values"] = {"renamed": "13"}, {"renamed": "169"}
    r["calls"][0]["id"] = "renamed"
    r["executed_calls"] = ["renamed"]
    assert E.score_served([request()], r)["classification"] == "CORRECT_COMPLETE"


def test_a_second_numeric_or_unsupported_goal_cannot_disappear():
    for second in (request("r2", ["B", "D'"]), request("r2", quantity="unsupported", target={"description": "explain"},
                                                        disposition="unsupported", oracle=None)):
        assert E.score_served([request(), second], row())["classification"] == "PARTIAL_SERVED"


def test_missing_projection_execution_is_incomplete_even_if_numeric_answer_is_correct():
    construct = request("r0", intent="construct", quantity="projection", target={"point": "S", "at": "H", "points": ["A", "B", "C"]}, oracle=None)
    r = row()
    assert E.score_served([construct, request()], r)["classification"] == "PARTIAL_SERVED"
    r["calls"].append({"id": "p", "fn": "orthogonal_projection", "args": {"point": "S", "image": "H", "plane": ["A", "B", "C"]}})
    r["executed_calls"].append("p")
    assert E.score_served([construct, request()], r)["classification"] == "CORRECT_COMPLETE"


def test_capability_gap_construction_that_actually_executed_is_fulfilled_not_missing():
    # A capability_gap label predicts lack of support; executed matching evidence still fulfils the request.
    construct = request("r1", intent="construct", quantity="projection", target={"point": "I", "at": "J", "points": ["V", "K"]},
                        disposition="capability_gap", oracle=None)
    r = row(["V", "I"])
    r["calls"].append({"id": "p", "fn": "orthogonal_projection_line", "args": {"point": "I", "image": "J", "line": ["V", "K"]}})
    r["executed_calls"].append("p")
    assert E.score_served([construct, request(points=["V", "I"])], r)["classification"] == "CORRECT_COMPLETE"
    r["answers"], r["values"] = {}, {}
    assert E.score_served([construct], r)["classification"] == "CORRECT_COMPLETE"
    r["executed_calls"].remove("p")
    assert E.score_served([construct], r)["classification"] == "PARTIAL_SERVED"


@pytest.mark.parametrize("disposition", ["unsupported", "ambiguous", "missing_source"])
def test_requests_that_must_not_be_answered_stay_unsafe_when_served(disposition):
    assert E.score_served([request(disposition=disposition)], row())["classification"] == "WRONG_SERVED"


def test_extra_answer_and_duplicate_answer_cannot_be_hidden():
    r = row()
    r["answers"]["extra"], r["values"]["extra"] = "13", "169"
    r["calls"].append({"id": "extra", "fn": "ask_length", "args": {"segment": ["B", "D'"]}})
    r["executed_calls"].append("extra")
    assert E.score_served([request()], r)["classification"] == "OVER_SERVED"
    assert E.score_served([request(), request("r2")], row())["classification"] == "PARTIAL_SERVED"


@pytest.mark.parametrize("missing", ["calls", "executed_calls", "values"])
def test_missing_measurement_evidence_never_passes(missing):
    r = row()
    r.pop(missing)
    assert E.score_served([request()], r)["classification"] == "UNSCORABLE"


def test_squared_length_or_finite_segment_distance_is_not_ordinary_length_or_line():
    assert E.score_served([request(quantity="squared_length")], row())["classification"] == "WRONG_SERVED"
    req = request(quantity="distance", target={"points_a": ["S"], "points_b": ["A", "B"], "domain": "segment"})
    r = row()
    r["calls"][0]["args"] = {"segment": ["S", "H"]}
    r["calls"].append({"id": "foot", "fn": "orthogonal_projection_line", "args": {"point": "S", "image": "H", "line": ["A", "B"]}})
    r["executed_calls"].append("foot")
    r["auxiliary"] = [{"ask": "F5", "construct": "foot", "rule": "distance(point,line)", "point": "S", "line": ["A", "B"]}]
    assert E.score_served([req], r)["classification"] == "WRONG_SERVED"


def test_angle_degrees_is_not_silently_scored_as_cos_squared():
    req = request(quantity="angle", target={"points_a": ["S", "A"], "points_b": ["A", "B", "C"]}, oracle={"degrees": "90"})
    r = row()
    r["calls"][0].update(fn="ask_angle_line_plane", args={"line": ["S", "A"], "plane": ["A", "B", "C"]})
    r["value_forms"] = {"F5": "cos_squared"}
    assert E.score_served([req], r)["classification"] == "UNSCORABLE"


def test_refusal_and_parse_failure_have_separate_outcomes():
    assert E.score_served([request()], {"status": "REFUSED"})["classification"] == "FALSE_REFUSAL"
    assert E.score_served([request(disposition="ambiguous")], {"status": "REFUSED"})["classification"] == "SAFE_REFUSAL"
    assert E.score_served([request()], {"status": "REFUSED"}, parse_ok=False)["classification"] == "NO_PARSE"


def test_malformed_numeric_receipt_is_unknown():
    assert E.score_served([request()], row(value="UNKNOWN"))["classification"] == "UNSCORABLE"


def test_unused_question_slots_do_not_penalize_goal_agreement():
    q = {"id": "q", "rid": "r", "kind": "question", "role": "question", "quantity": "length", "points": ["A", "C'"], "quotes": ["Tính AC'."]}
    c = {"source_text": "Tính AC'.", "entities": ["A", "C'"], "requests": [request()]}
    ext = E.extraction(c, {"facts": [q]}, [{**q, "measure": "segment", "solid": "unused"}])
    assert ext["goal_match"] == 1 and ext["complete_goals"]


@pytest.mark.parametrize("gold_extra,live_extra,match", [
    ({"solid_type": "cuboid", "right": True}, {"solid_type": "cuboid"}, True),          # L01 premise: implied by cuboid
    ({"solid_type": "prism", "regular": True, "right": True}, {"solid_type": "prism", "regular": True}, True),
    ({"solid_type": "prism", "right": True}, {"solid_type": "prism"}, False),            # an oblique prism is another solid
])
def test_solid_rightness_compares_as_the_planner_derives_it(gold_extra, live_extra, match):
    base = {"id": "s", "kind": "solid", "role": "premise", "solid": "ABC.DEF", "quotes": ["lăng trụ ABC.DEF"]}
    c = {"source_text": "Cho lăng trụ ABC.DEF.", "entities": list("ABCDEF"), "requests": []}
    ext = E.extraction(c, {"facts": [{**base, **gold_extra}]}, [{**base, **live_extra}])
    assert (ext["premise_match"] == 1) is match


def test_parse_failure_stays_in_goal_operand_solid_denominators():
    reqs = [request(), request("v", quantity="volume", target={"solid": "S.ABC"})]
    facts = [{"id": "q", "rid": "r", "kind": "question", "role": "question", "quantity": "length", "points": ["A", "C'"], "quotes": ["Tính AC'."]},
             {"id": "v", "rid": "v", "kind": "question", "role": "question", "quantity": "volume", "solid": "S.ABC", "quotes": ["Tính thể tích S.ABC."]}]
    inp = {"cases": {"x": {"id": "x", "requests": reqs}}, "gold": {"cases": {"x": {"facts": facts}}}}
    s = E.summarize(inp, [{"case_id": "x", "facts": None, "parse_code": "JSON_INVALID", "route": {"status": "REFUSED"}}])
    assert s["counts"]["requests_gold"] == 2
    assert s["counts"]["operand_required"] == 1 and s["counts"]["solid_required"] == 1


def test_symmetric_distance_operands_are_the_same_requested_goal():
    req = request(quantity="distance", target={"points_a": ["A", "B"], "points_b": ["C", "D"]})
    r = row()
    r["calls"][0].update(fn="ask_distance_lines", args={"line1": ["D", "C"], "line2": ["B", "A"]})
    assert E.score_served([req], r)["classification"] == "CORRECT_COMPLETE"


@pytest.mark.parametrize("fn,args,target", [
    ("ask_angle_line_plane", {"line": ["A", "S"], "plane": ["C", "B", "A"]}, {"points_a": ["A", "B", "C"], "points_b": ["S", "A"]}),
    ("ask_angle_plane_plane", {"plane1": ["S", "B", "C"], "plane2": ["A", "B", "C", "D"]}, {"points_a": ["A", "B", "C", "D"], "points_b": ["S", "B", "C"]}),
    ("ask_distance_point_plane", {"point": "S", "plane": ["A", "B", "C"]}, {"points_a": ["A", "B", "C"], "points_b": ["S"]}),
])
def test_unsigned_angle_and_distance_are_symmetric_in_their_two_objects(fn, args, target):
    req = request(quantity="angle" if "angle" in fn else "distance", target=target)
    r = row()
    r["calls"][0].update(fn=fn, args=args)
    assert E.score_served([req], r)["classification"] == "CORRECT_COMPLETE"


def test_symmetry_never_lets_a_line_stand_for_a_plane():
    req = request(quantity="angle", target={"points_a": ["S", "A"], "points_b": ["A", "B", "C"]})
    r = row()
    r["calls"][0].update(fn="ask_angle_plane_plane", args={"plane1": ["S", "A", "B"], "plane2": ["A", "B", "C"]})
    assert E.score_served([req], r)["classification"] == "WRONG_SERVED"


@pytest.mark.parametrize("polygon,ok", [
    (["B", "C", "D", "A"], True), (["D", "C", "B", "A"], True),        # rotation, reflection: same polygon
    (["A", "C", "B", "D"], False), (["A", "B", "D", "C"], False),      # another quadrilateral on the same vertices
])
def test_polygon_area_is_cyclic_not_an_unordered_label_set(polygon, ok):
    req = request(quantity="area", target={"points": ["A", "B", "C", "D"]})
    r = row()
    r["calls"][0].update(fn="ask_area", args={"polygon": polygon})
    assert E.score_served([req], r)["classification"] == ("CORRECT_COMPLETE" if ok else "WRONG_SERVED")


def test_section_plane_is_a_label_set_but_owner_solid_is_exact():
    req = request(quantity="area", target={"solid": "ABCD.EFGH", "points": ["A", "C", "G", "E"]})
    r = row()
    r["calls"][0].update(fn="ask_section_area", args={"solid": "ABCD.EFGH", "plane": ["A", "C", "G"]})
    assert E.score_served([req], r)["classification"] == "CORRECT_COMPLETE"
    r["calls"][0]["args"]["solid"] = "S.ABCD"
    assert E.score_served([req], r)["classification"] == "WRONG_SERVED"


def test_extracted_polygon_order_is_part_of_goal_agreement():
    q = {"id": "q", "rid": "r", "kind": "question", "role": "question", "quantity": "area", "points": list("ABCD"), "quotes": ["diện tích ABCD"]}
    c = {"source_text": "Tính diện tích ABCD.", "entities": list("ABCD"), "requests": [request(quantity="area")]}
    assert E.extraction(c, {"facts": [q]}, [{**q, "points": list("CDAB")}])["goal_match"] == 1
    assert E.extraction(c, {"facts": [q]}, [{**q, "points": list("ACBD")}])["goal_match"] == 0


def test_projection_point_and_image_are_not_interchangeable():
    construct = request("p", intent="construct", quantity="projection", target={"point": "S", "at": "H", "points": ["A", "B", "C"]}, oracle=None)
    r = row()
    r["answers"], r["values"] = {}, {}
    r["calls"] = [{"id": "p", "fn": "orthogonal_projection", "args": {"point": "H", "image": "S", "plane": ["A", "B", "C"]}}]
    r["executed_calls"] = ["p"]
    assert E.score_served([construct], r)["classification"] == "PARTIAL_SERVED"


def test_unrecognized_binding_is_unscorable_rather_than_claiming_wrong_geometry():
    r = row()
    r["calls"][0]["fn"] = "future_answer"
    assert E.score_served([request()], r)["classification"] == "UNSCORABLE"


def test_section_area_must_preserve_owning_solid():
    q = {"id": "q", "rid": "r", "kind": "question", "role": "question", "quantity": "area", "solid": "S.ABCD", "points": ["M", "N", "P"], "quotes": ["Tính diện tích thiết diện của S.ABCD qua MNP."]}
    c = {"source_text": q["quotes"][0], "entities": list("SABCDMNP"), "requests": [request(quantity="area")]}
    assert E.extraction(c, {"facts": [q]}, [{**q, "solid": "T.EFGH"}])["goal_match"] == 0


def test_scoring_live_receipts_cannot_clone_raw_output(tmp_path):
    state = {"execution_class": "LIVE", "identity": {}, "rows": [{"raw_response": {"secret_model_text": "x"}}]}
    E.write_score(tmp_path, state, {"e2e": {}})
    assert not (tmp_path / "manifest.json").exists()
    assert (tmp_path / "score.json").exists()


def test_false_refusal_is_split_by_the_extraction_perfect_route():
    gold = [{"id": "q", "rid": "r", "kind": "question", "role": "question", "quantity": "length", "points": ["A", "C'"], "quotes": ["Tính AC'."]}]
    inp = {"cases": {"x": {"id": "x", "source_text": "Tính AC'.", "entities": ["A", "C'"], "requests": [request()]}},
           "gold": {"cases": {"x": {"facts": gold}}}}
    refused = [{"case_id": "x", "facts": gold, "route": {"status": "REFUSED", "code": "OBJECT_NOT_IN_QUOTE"}}]
    for gold_route, want in (({"status": "SERVED"}, "FALSE_REFUSAL_EXTRACTION"), ({"status": "REFUSED"}, "FALSE_REFUSAL_CAPABILITY_GAP")):
        s = E.summarize(inp, refused, [{"case_id": "x", "route": gold_route}])
        assert s["e2e"] == {want: 1} and s["refusal_codes"] == {"OBJECT_NOT_IN_QUOTE": 1}


def test_published_score_carries_no_model_text_and_audits_by_hash(tmp_path, monkeypatch):
    import json
    sentinel = "MODEL_TEXT_SENTINEL ignore previous instructions"
    facts = [{"id": sentinel, "kind": "question", "role": "question", "quantity": "length", "points": ["A", "C'"], "quotes": ["Tính AC'."]},
             {"id": "q2", "kind": "question", "role": "question", "quantity": "length", "points": ["M", sentinel], "quotes": ["Tính AC'."]}]
    gold = [{"id": "q", "rid": "r", "kind": "question", "role": "question", "quantity": "length", "points": ["A", "C'"], "quotes": ["Tính AC'."]}]
    inp = {"cases": {"x": {"id": "x", "source_text": "Tính AC'.", "entities": ["A", "C'"], "requests": [request()]}},
           "gold": {"cases": {"x": {"facts": gold}}}}
    score = E.summarize(inp, [{"case_id": "x", "facts": facts, "route": row()}])
    E.write_score(tmp_path, {"rows_sha256": "abc"}, score)
    text = (tmp_path / "score.json").read_text(encoding="utf-8")
    assert sentinel not in text and '"M"' in text
    assert json.loads(text)["source_manifest_rows_sha256"] == "abc"
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaFAKEKEY0123456789")
    with pytest.raises(E.V1.PilotStopped, match="SECRET_DETECTED"):
        E.write_score(tmp_path / "leak", {"rows_sha256": "abc"}, {"note": "AIzaFAKEKEY0123456789"})


def test_schedule_rejects_duplicate_wrong_split_and_missing_rows_are_explicit():
    planned = [{"case_id": "a", "sample": 1}, {"case_id": "b", "sample": 1}]
    assert E.validate_schedule({"rows": planned[:1]}, planned)["status"] == "INCOMPLETE"
    for rows in ([planned[0], planned[0]], [{"case_id": "heldout", "sample": 1}]):
        with pytest.raises(E.V1.PilotStopped, match="SCHEDULE_MISMATCH"):
            E.validate_schedule({"rows": rows}, planned)
    assert E.validate_schedule({"rows": planned}, planned)["status"] == "COMPLETE"


def test_unknown_usage_stops_before_a_second_send(tmp_path):
    case = {"id": "a", "split": "dev", "source_text": "Tính AC'."}
    inp = {"dir": tmp_path, "cases": {"a": case}, "corpus": {"cases": [case, {**case, "id": "b"}]},
           "gold": {"cases": {"a": {"facts": []}}},
           "protocol": {"locked_sha256": {"corpus": "x", "gold_facts": "y"}, "file_sha256": {"oracle.py": "z"},
                        "caps": {"PILOT": {"logical_calls": 2, "http_attempts": 2, "accounted_tokens": 1000000, "usd": 2.0, "samples": 1}}}}
    h = E.harness("v2", inp)
    provider = h.ReplayProvider(inp)
    original = provider.send
    sent = []

    def send(*args):
        sent.append(1)
        body = original(*args)
        body.pop("usageMetadata")
        return body
    provider.send = send
    with pytest.raises(E.V1.PilotStopped, match="USAGE_UNKNOWN"):
        h.run_eval(inp, "PILOT", provider, tmp_path / "out")
    assert len(sent) == 1


# ── independent scorer review (pre-lock): one RED test per finding ───────────────────────────────────────────────────

@pytest.mark.parametrize("asked,served_as,ok", [
    ("OPQR", "R.OPQ", True), ("OPQR", "R.OPS", False),                 # the planner renames a tetrahedron (planner.py)
    ("S.ABCD", "S.BCDA", True), ("S.ABCD", "S.ACBD", False), ("S.ABCD", "A.SBCD", False),
    ("ABC.A'B'C'", "BCA.B'C'A'", True), ("ABC.A'B'C'", "A'B'C'.ABC", True), ("ABC.A'B'C'", "ABC.B'C'A'", False),
])
def test_solid_identity_follows_vertex_structure_not_spelling(asked, served_as, ok):
    req = request(quantity="volume", target={"solid": asked})
    r = row()
    r["calls"][0].update(fn="ask_volume", args={"solid": served_as})
    assert E.score_served([req], r)["classification"] == ("CORRECT_COMPLETE" if ok else "WRONG_SERVED")


def test_operand_ratio_numerator_and_denominator_share_one_population():
    gap = {"rid": "u", "intent": "calculate", "quantity": "distance", "target": {"description": "segment"},
           "disposition": "unsupported", "oracle": None}
    gold = [{"id": "q", "rid": "r", "kind": "question", "role": "question", "quantity": "length", "points": ["A", "C'"], "quotes": ["Tính AC'."]},
            {"id": "x", "rid": "u", "kind": "unsupported", "role": "question", "reason": "segment", "quotes": ["Tính AC'."]}]
    inp = {"cases": {"x": {"id": "x", "source_text": "Tính AC'.", "entities": ["A", "C'"], "requests": [request(), gap]}},
           "gold": {"cases": {"x": {"facts": gold}}}}
    c = E.summarize(inp, [{"case_id": "x", "facts": gold, "route": {"status": "REFUSED"}}])["counts"]
    assert c["operand_correct"] <= c["operand_required"] == 1


def test_solid_slot_labels_count_as_invented_entities():
    q = {"id": "v", "rid": "r", "kind": "question", "role": "question", "quantity": "volume", "solid": "S.ABC", "quotes": ["Tính thể tích S.ABC."]}
    c = {"source_text": "Tính thể tích S.ABC.", "entities": list("SABC"), "requests": [request(quantity="volume")]}
    assert E.extraction(c, {"facts": [q]}, [{**q, "solid": "S.ABCZ"}])["invented_entities"] == ["Z"]


def test_effect_chain_distance_to_a_named_line_is_scored_from_the_executed_foot():
    req = request(quantity="distance", target={"point_kind": "midpoint", "points": ["S", "C"], "points_b": ["T", "O"]})
    r = row()
    r["calls"] = [{"id": "m", "fn": "midpoint", "args": {"point": "X1", "segment": ["C", "S"]}},
                  {"id": "f", "fn": "orthogonal_projection_line", "args": {"point": "X1", "image": "X2", "line": ["O", "T"]}},
                  {"id": "F5", "fn": "ask_length", "args": {"segment": ["X1", "X2"]}}]
    r["executed_calls"] = ["m", "f", "F5"]
    r["auxiliary"] = [{"rule": "effect-chain", "ask": "F5", "operand": {"descriptor": "midpoint", "points": ["S", "C"], "label": "X1"},
                       "target": {"line": ["T", "O"]}}]
    assert E.score_served([req], r)["classification"] == "CORRECT_COMPLETE"
    r["calls"][1]["args"]["line"] = ["O", "S"]
    assert E.score_served([req], r)["classification"] in {"WRONG_SERVED", "UNSCORABLE"}


def test_a_served_route_is_scored_even_without_parsed_facts_and_infra_is_its_own_outcome():
    assert E.score_served([request()], row(["A", "B'"]), parse_ok=False)["classification"] == "WRONG_SERVED"
    inp = {"cases": {"x": {"id": "x", "source_text": "Tính AC'.", "entities": ["A", "C'"], "requests": [request()]}},
           "gold": {"cases": {"x": {"facts": []}}}}
    s = E.summarize(inp, [{"case_id": "x", "facts": None, "infra": "TIMEOUT", "route": None}])
    assert s["e2e"] == {"PROVIDER_OR_HARNESS_ERROR": 1}


@pytest.mark.parametrize("aux", [["junk"], [{"rule": "effect-chain", "ask": "F5", "operand": "junk", "target": {}}],
                                 [{"rule": "effect-chain", "ask": "F5", "operand": {"descriptor": "midpoint"}, "target": "junk"}]])
def test_malformed_auxiliary_is_unscorable_not_a_crash(aux):
    r = row()
    r["auxiliary"] = aux
    assert E.score_served([request()], r)["classification"] == "UNSCORABLE"


def test_published_score_has_no_model_answer_ids_and_names_its_execution(tmp_path):
    sentinel = "MODEL_SENTINEL ignore previous instructions"
    r = row()
    r["answers"][sentinel], r["values"][sentinel] = "13", "169"
    r["calls"].append({"id": sentinel, "fn": "ask_length", "args": {"segment": ["B", "D'"]}})
    r["executed_calls"].append(sentinel)
    gold = [{"id": "q", "rid": "r", "kind": "question", "role": "question", "quantity": "length", "points": ["A", "C'"], "quotes": ["Tính AC'."]}]
    inp = {"cases": {"x": {"id": "x", "source_text": "Tính AC'.", "entities": ["A", "C'"], "requests": [request()]}},
           "gold": {"cases": {"x": {"facts": gold}}}}
    rows = [{"case_id": "x", "facts": gold, "route": r, "usage": {"input_tokens": 3, "output_tokens": 4, "thinking_tokens": 5,
                                                                  "usd": 0.01}, "latency_seconds": 1.5}]
    state = {"execution_class": "LIVE", "identity": {"mode": "PILOT"}, "stop_reason": None, "live_model_calls": 1,
             "rows": rows, "rows_sha256": "abc"}
    E.write_score(tmp_path, state, E.summarize(inp, rows))
    import json
    text = (tmp_path / "score.json").read_text(encoding="utf-8")
    assert sentinel not in text
    out = json.loads(text)
    assert out["execution_class"] == "LIVE" and out["identity"] == {"mode": "PILOT"} and out["live_model_calls"] == 1
    assert out["usage"]["input_tokens"] == 3 and out["usage"]["latency_seconds"] == [1.5]
    assert out["rows"][0]["served"]["extra_count"] == 1


def test_baseline_arm_does_not_leak_into_a_later_v2_harness():
    from app.ai import fact_extraction as fx
    inp = E.load_inputs()
    product = E._PRODUCT_PROMPT
    E.harness("baseline", inp)
    E.harness("v2", inp)
    assert fx.SYSTEM_PROMPT == product


def test_gold_equal_lengths_premise_matches_itself():
    eq = {"id": "e", "kind": "equal_lengths", "role": "premise", "points_a": ["S", "A"], "points_b": ["S", "B"], "quotes": ["SA = SB"]}
    c = {"source_text": "Cho SA = SB.", "entities": list("SAB"), "requests": []}
    assert E.extraction(c, {"facts": [eq]}, [{**eq, "points_a": ["B", "S"], "points_b": ["A", "S"]}])["premise_match"] == 1
    assert E.extraction(c, {"facts": [eq]}, [{**eq, "points_b": ["A", "B"]}])["premise_match"] == 0


# ── scorer /3 (schema-contract candidate review) ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("a,b", [(["A"], ["C'"]), (["C'"], ["A"])])
def test_point_point_distance_is_the_served_segment_length(a, b):
    # I3: the route serves "khoảng cách từ A đến C'" as ask_length(AC'); the same object must not score WRONG_SERVED.
    req = request(quantity="distance", target={"points_a": a, "points_b": b})
    assert E.score_served([req], row())["classification"] == "CORRECT_COMPLETE"
    assert E.score_served([req], row(points=["A", "B"]))["classification"] == "WRONG_SERVED"


def test_point_line_distance_is_still_not_a_segment_length():
    req = request(quantity="distance", target={"points_a": ["A"], "points_b": ["B", "C'"]})
    assert E.score_served([req], row())["classification"] == "WRONG_SERVED"


@pytest.mark.parametrize("live_solid,match", [("S.ABC", True), ("S.BCA", True), ("A.SBC", False)])
def test_a_height_is_owned_by_its_apex(live_solid, match):
    # M2: S.ABC and A.SBC are one tetrahedron but two different heights.
    h = {"id": "h", "kind": "length", "role": "premise", "measure": "height", "solid": "S.ABC", "value": "3", "quotes": ["chiều cao 3"]}
    c = {"source_text": "Cho hình chóp S.ABC có chiều cao 3.", "entities": list("SABC"), "requests": []}
    ext = E.extraction(c, {"facts": [h]}, [{**h, "solid": live_solid}])
    assert (ext["premise_match"] == 1) is match
