# -*- coding: utf-8 -*-
"""Harness gates of `scripts/run_nlu_extraction_evaluation.py` on a synthetic three-case input (0 network calls).

The locked corpus is not used here; its integrity is checked separately at the bottom of this file."""
from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

_R = Path(__file__).resolve().parents[2] / "scripts" / "run_nlu_extraction_evaluation.py"
_spec = importlib.util.spec_from_file_location("run_nlu_extraction_evaluation", _R)
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)

PYR = "Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). SA = 3. "
BASE = [
    {"id": "f1", "kind": "solid", "role": "premise", "quotes": ["Cho hình chóp S.ABCD."], "solid": "S.ABCD", "solid_type": "pyramid"},
    {"id": "f2", "kind": "polygon_shape", "role": "premise", "quotes": ["Đáy ABCD là hình vuông cạnh 2."],
     "points": ["A", "B", "C", "D"], "shape": "square", "value": "2"},
    {"id": "f3", "kind": "perpendicular", "role": "premise", "quotes": ["SA vuông góc với (ABCD)."],
     "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"]},
    {"id": "f4", "kind": "length", "role": "premise", "quotes": ["SA = 3."], "points": ["S", "A"], "measure": "segment", "value": "3"},
]


def _q(label: str) -> dict:
    return {"id": "q", "rid": "r1", "kind": "question", "role": "question",
            "quotes": [f"Tính khoảng cách từ trung điểm của S{label} đến (SAB)."], "quantity": "distance",
            "point_kind": "midpoint", "points": ["S", label], "points_b": ["S", "A", "B"]}


def _case(cid: str, split: str, label: str, disp: str) -> dict:
    ev = {"r1": {"value_squared": "1"}} if disp == "answer_all" else {}
    return {"id": cid, "split": split, "group": "A", "structure_id": cid,
            "source_text": PYR + f"Tính khoảng cách từ trung điểm của S{label} đến (SAB).", "gold_disposition": disp,
            "expected_values": ev, "requests": [{"rid": "r1"}], "n_source_requests": 1}


@pytest.fixture
def inp(tmp_path: Path) -> dict:
    d = tmp_path / "inputs"
    d.mkdir()
    corpus = {"cases": [_case("T1", "dev", "C", "answer_all"), _case("T2", "dev", "E", "refuse_nonexistent_object"),
                        _case("T3", "locked", "C", "answer_all")]}
    gold = {"cases": {"T1": {"facts": BASE + [_q("C")]}, "T2": {"facts": BASE + [_q("E")]},
                      "T3": {"facts": BASE + [_q("C")]}}}
    caps = {"logical_calls": 10, "http_attempts": 10, "accounted_tokens": 10_000_000, "usd": 5.0, "samples": 2}
    protocol = {"locked_sha256": {"corpus": E._sha(corpus), "gold_facts": E._sha(gold)},
                "caps": {"PILOT": caps, "LOCKED": {**caps, "samples": 1}}}
    for name, v in (("corpus", corpus), ("gold_facts", gold), ("protocol", protocol)):
        (d / f"{name}.json").write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8")
    return E.load_inputs(d)


class Scripted(E.ReplayProvider):
    """Replay provider whose n-th send may raise, return a mutated body, or rewrite the facts."""

    def __init__(self, inp, actions=None, facts=None):
        super().__init__(inp)
        self.actions, self.facts, self.sent = actions or {}, facts, 0

    def send(self, payload, timeout_seconds):
        self.sent += 1
        act = self.actions.get(self.sent)
        if isinstance(act, Exception):
            raise act
        body = super().send(payload, timeout_seconds)
        if self.facts is not None:
            body["candidates"][0]["content"]["parts"][0]["text"] = json.dumps({"facts": self.facts(self.current)},
                                                                               ensure_ascii=False)
        if callable(act):
            act(body)
        return body


def _summary(inp, state):
    return E.summarize(inp, state["rows"], E.run_gold(inp))


def test_replay_pilot_sends_nothing_live_and_scores_like_gold(inp, tmp_path):
    state = E.run_eval(inp, "PILOT", E.ReplayProvider(inp), tmp_path / "out")
    assert (len(state["rows"]), state["stop_reason"], state["live_model_calls"], state["execution_class"]) == (4, None, 0, "FAKE")
    s = _summary(inp, state)
    assert s["e2e"] == {"CORRECT_COMPLETE": 2, "SAFE_REFUSAL": 2}
    assert s["extraction"]["extraction_correct"] == "4/4" and s["extraction"]["goal_entity"] == "4/4"
    assert s["cells"] == {"LLM_CORRECT_SERVED_CORRECT": 2, "LLM_CORRECT_SAFE_REFUSAL": 2}


def test_single_provider_error_is_recorded_and_the_run_continues(inp, tmp_path):
    p = Scripted(inp, {1: RuntimeError("boom")})
    state = E.run_eval(inp, "PILOT", p, tmp_path / "out")
    assert len(state["rows"]) == 4 and state["stop_reason"] is None and p.sent == 4
    assert state["rows"][0]["infra"] == "PROVIDER_ERROR" and state["rows"][0]["route"]["status"] == "REFUSED"
    assert _summary(inp, state)["e2e"]["PROVIDER_OR_HARNESS_ERROR"] == 1


def test_three_consecutive_infra_errors_stop_the_run(inp, tmp_path):
    p = Scripted(inp, {i: TimeoutError("t") for i in range(1, 9)})
    state = E.run_eval(inp, "PILOT", p, tmp_path / "out")
    assert (len(state["rows"]), state["stop_reason"], p.sent) == (3, "CONSECUTIVE_INFRA_ERRORS", 3)


def test_quota_or_auth_status_stops_at_once_without_retry(inp, tmp_path):
    from app.ai.function_calling import ProviderHTTPError
    p = Scripted(inp, {1: ProviderHTTPError(429, {"error": {"code": 429}})})
    state = E.run_eval(inp, "PILOT", p, tmp_path / "out")
    assert (len(state["rows"]), state["stop_reason"], p.sent) == (1, "HTTP_429", 1)


def test_budget_cap_refuses_before_sending_and_fabricates_no_row(inp, tmp_path):
    inp["protocol"]["caps"]["PILOT"]["logical_calls"] = 1
    p = Scripted(inp)
    state = E.run_eval(inp, "PILOT", p, tmp_path / "out")
    assert (len(state["rows"]), state["stop_reason"], p.sent) == (1, "LOGICAL_CAP", 1)


def test_secret_in_a_response_stops_and_never_reaches_disk(inp, tmp_path):
    secret = "AIzaSECRET-not-a-real-key"
    p = Scripted(inp, {1: lambda b: b.update(responseId=secret)})
    state = E.run_eval(inp, "PILOT", p, tmp_path / "out", secrets=(secret,))
    assert state["stop_reason"] == "SECRET_DETECTED"
    assert secret.encode() not in (tmp_path / "out" / "manifest.json").read_bytes()


def test_model_version_change_stops_instead_of_silently_mixing_models(inp, tmp_path):
    p = Scripted(inp, {1: lambda b: b.update(modelVersion="gemini-other")})
    state = E.run_eval(inp, "PILOT", p, tmp_path / "out")
    assert (len(state["rows"]), state["stop_reason"]) == (1, "MODEL_VERSION_MISMATCH")
    assert state["rows"][0]["infra"] == "MODEL_VERSION_MISMATCH"


def test_resume_replays_nothing_and_an_uncertain_request_blocks_resume(inp, tmp_path):
    out = tmp_path / "out"
    E.run_eval(inp, "PILOT", E.ReplayProvider(inp), out)
    with pytest.raises(E.PilotStopped, match="OUTPUT_EXISTS"):
        E.run_eval(inp, "PILOT", E.ReplayProvider(inp), out)
    p = Scripted(inp)
    assert len(E.run_eval(inp, "PILOT", p, out, resume=True)["rows"]) == 4 and p.sent == 0
    m = json.loads((out / "manifest.json").read_bytes())
    m["pending"] = {"position": 4}
    (out / "manifest.json").write_bytes(E.canonical_json(m))
    with pytest.raises(E.PilotStopped, match="REQUEST_STATE_UNKNOWN"):
        E.run_eval(inp, "PILOT", Scripted(inp), out, resume=True)


def test_live_needs_the_flag_the_key_and_an_approval_of_this_exact_identity(inp, tmp_path, monkeypatch):
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)
    with pytest.raises(E.PilotStopped, match="LIVE_NOT_AUTHORIZED"):
        E.live_provider(inp, "PILOT", None)
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    ap = tmp_path / "approval.json"
    ident = E.identity(inp, "PILOT")
    ap.write_text(json.dumps({"decision": "HUMAN_APPROVED_LIVE_EXECUTION", "identities": {"PILOT": {**ident, "model": "x"}}}))
    with pytest.raises(E.PilotStopped, match="LIVE_NOT_AUTHORIZED"):
        E.live_provider(inp, "PILOT", ap)
    ap.write_text(json.dumps({"decision": "HUMAN_APPROVED_LIVE_EXECUTION", "identities": {"PILOT": ident}}))
    assert E.live_provider(inp, "PILOT", ap).is_live
    with pytest.raises(E.PilotStopped, match="LIVE_NOT_AUTHORIZED"):
        E.live_provider(inp, "LOCKED", ap)


def test_changed_locked_input_is_refused(inp, tmp_path):
    d = tmp_path / "inputs"
    corpus = json.loads((d / "corpus.json").read_text(encoding="utf-8"))
    corpus["cases"][0]["gold_disposition"] = "refuse_ambiguous"
    (d / "corpus.json").write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(E.PilotStopped, match="INPUT_IDENTITY_MISMATCH"):
        E.load_inputs(d)


def test_scorer_separates_omission_hallucination_and_unsafe_acceptance(inp, tmp_path):
    def wrong_value(cid):          # SA = 4 instead of 3: a changed premise the source does not say
        f = deepcopy(E.gold_payload(inp, cid)["facts"])
        f[3]["value"] = "4"
        return f

    def dropped_question(cid):     # the request is silently omitted
        return [f for f in E.gold_payload(inp, cid)["facts"] if f["role"] != "question"]

    def extra_premise(cid):        # an added fact with an invented quote
        return E.gold_payload(inp, cid)["facts"] + [{"id": "x", "kind": "length", "role": "premise", "quotes": ["AB = 5."],
                                                     "points": ["A", "B"], "measure": "segment", "value": "5"}]
    rows = {}
    for name, fn in (("wrong", wrong_value), ("drop", dropped_question), ("extra", extra_premise)):
        rows[name] = E.run_eval(inp, "PILOT", Scripted(inp, facts=fn), tmp_path / name)
    gold = E.run_gold(inp)
    s = {k: E.summarize(inp, v["rows"], gold) for k, v in rows.items()}
    first = {k: v["scored"][0] for k, v in s.items()}   # T1 sample 1: an answerable case
    # Source grounding catches the changed value (it is not in the quote): extraction wrong, refused safely.
    assert first["wrong"]["e2e"] == "FALSE_REFUSAL_EXTRACTION" and first["wrong"]["cell"] == "LLM_WRONG_REFUSED"
    assert first["wrong"]["extraction"]["premise_match"] == 3
    assert first["drop"]["e2e"].startswith("FALSE_REFUSAL") or first["drop"]["e2e"] == "PARTIAL_SERVED"
    assert first["drop"]["extraction"]["goal_match"] == 0 and not first["drop"]["extraction"]["correct"]
    assert first["extra"]["extraction"]["extra_premises"] == 1
    assert first["extra"]["extraction"]["ungrounded_quote_facts"] == 1 and not first["extra"]["extraction"]["correct"]


def test_a_served_wrong_value_from_a_wrong_extraction_is_unsafe_acceptance(inp):
    facts = deepcopy(E.gold_payload(inp, "T1")["facts"])
    facts[3]["value"] = "4"
    row = {"case_id": "T1", "sample": 1, "infra": None, "facts": facts,
           "route": {"status": "SERVED", "code": None, "answers": {"q": "x"}, "values": {"q": "2"}}}
    s = E.score_row(inp["cases"]["T1"], inp["gold"]["cases"]["T1"], row, None)
    assert (s["e2e"], s["cell"]) == ("WRONG_SERVED", "LLM_WRONG_UNSAFE_ACCEPTED")
    row["route"]["values"] = {}
    assert E.score_row(inp["cases"]["T1"], inp["gold"]["cases"]["T1"], row, None)["e2e"] == "PARTIAL_SERVED"


def test_model_version_accepts_only_the_locked_model_or_its_numbered_pin():
    assert E.model_ok("gemini-2.5-flash") and E.model_ok("gemini-2.5-flash-001")
    assert not E.model_ok("gemini-2.5-flash-lite") and not E.model_ok("gemini-3.8-flash") and not E.model_ok(None)


def test_persistence_failure_before_a_send_stops_and_sends_nothing(inp, tmp_path, monkeypatch):
    real, calls = E._persist, {"n": 0}

    def flaky(path, state, secrets):
        calls["n"] += 1
        if calls["n"] == 2:            # the pending marker before the first request
            raise E.PilotStopped("PERSISTENCE_FAILED")
        return real(path, state, secrets)
    monkeypatch.setattr(E, "_persist", flaky)
    p = Scripted(inp)
    state = E.run_eval(inp, "PILOT", p, tmp_path / "out")
    assert (state["stop_reason"], len(state["rows"]), p.sent) == ("PERSISTENCE_FAILED", 0, 0)


def _ext(gold_facts, live, text=PYR + "Tính khoảng cách từ trung điểm của SC đến (SAB).", **case):
    return E.extraction({"source_text": text, **case}, {"facts": gold_facts}, live)


def test_audit_regressions_equivalent_encodings_are_accepted():
    sq = [f for f in BASE if f["kind"] != "perpendicular"]
    # The base plane named by three of its four labels is the same plane.
    three = sq + [{**BASE[2], "points_b": ["A", "B", "C"]}, _q("C")]
    assert _ext(BASE + [_q("C")], three)["correct"]
    # "AB = AD = 2" as two lengths or as equal_lengths + one length.
    text = "Cho AB = AD = 2. Tính độ dài SC."
    gold = [{"id": "a", "kind": "length", "role": "premise", "quotes": ["AB = AD = 2"], "points": ["A", "B"], "measure": "segment", "value": "2"},
            {"id": "b", "kind": "length", "role": "premise", "quotes": ["AB = AD = 2"], "points": ["A", "D"], "measure": "segment", "value": "2"}]
    live = [gold[0], {"id": "e", "kind": "equal_lengths", "role": "premise", "quotes": ["AB = AD = 2"], "points_a": ["A", "B"], "points_b": ["A", "D"]}]
    e = _ext(gold, live, text)
    assert (e["premise_match"], e["extra_premises"]) == (2, 0)
    # Extra whitespace in a quote is grounded exactly as the product's normaliser grounds it.
    spaced = BASE[:3] + [{**BASE[3], "quotes": ["SA  =  3."]}, _q("C")]
    assert _ext(BASE + [_q("C")], spaced)["ungrounded_quote_facts"] == 0


def test_audit_regressions_content_free_and_malformed_facts_do_not_score_as_correct():
    text = PYR + "Tính khoảng cách từ C đến tâm của mặt bên SAB."
    gap = {"id": "u", "rid": "r1", "kind": "unsupported", "role": "question", "quotes": ["Tính khoảng cách từ C đến tâm của mặt bên SAB."]}
    wrong_region = {"id": "x", "kind": "unsupported", "role": "question", "quotes": ["SA = 3."]}
    e = _ext(BASE + [gap], BASE + [wrong_region], text)
    assert e["schema_gap_flagged"] == 0 and not e["correct"]
    approx = {"id": "y", "kind": "question", "role": "question", "quotes": [gap["quotes"][0]], "quantity": "distance",
              "points_a": ["C"], "points_b": ["S", "A", "B"]}
    e = _ext(BASE + [gap], BASE + [approx], text)
    assert (e["schema_gap_flagged"], e["schema_gap_approximated"], e["correct"]) == (0, 1, False)
    assert _ext(BASE + [gap], BASE + [{**gap, "id": "z"}], text)["schema_gap_flagged"] == 1
    # Non-string labels and non-dict facts are scored, not crashed on.
    e = _ext(BASE + [_q("C")], BASE + [{**_q("C"), "points": [1, "C"], "solid": 5}, "junk"])
    assert not e["correct"] and e["non_dict_facts"] == 1


def test_audit_regressions_served_rows_with_unasked_or_wrong_object_answers_are_unsafe(inp):
    case, gold = inp["cases"]["T1"], inp["gold"]["cases"]["T1"]
    facts = E.gold_payload(inp, "T1")["facts"]
    other = {"id": "q9", "kind": "question", "role": "question", "quotes": ["SA = 3."], "quantity": "length", "points": ["S", "A"]}
    row = {"case_id": "T1", "sample": 1, "infra": None, "facts": facts + [other],
           "route": {"status": "SERVED", "code": None, "answers": {"q": "x", "q9": "y"}, "values": {"q": "1", "q9": "9"}}}
    assert E.score_row(case, gold, row, None)["e2e"] == "OVER_SERVED"
    wrong_obj = [f for f in facts if f["id"] != "q"] + [{**other, "id": "q2"}]
    row = {**row, "facts": wrong_obj, "route": {**row["route"], "answers": {"q2": "y"}, "values": {"q2": "9"}}}
    s = E.score_row(case, gold, row, None)
    assert (s["e2e"], s["cell"]) == ("WRONG_SERVED", "LLM_WRONG_UNSAFE_ACCEPTED")
    # An unmatched request with nothing else matched must not fall back to an identity mapping.
    row = {**row, "facts": [{**f, "id": f"z{i}"} for i, f in enumerate(facts)],
           "route": {**row["route"], "answers": {"z4": "y"}, "values": {"z4": "1"}}}
    assert E.score_row(case, gold, row, None)["e2e"] in E.SERVED_OK
    row = {**row, "facts": [], "route": {**row["route"], "answers": {"q": "y"}, "values": {"q": "1"}}}
    assert E.score_row(case, gold, row, None)["e2e"] == "WRONG_SERVED"


def test_unparsed_output_is_its_own_class_not_a_safe_refusal(inp):
    row = {"case_id": "T2", "sample": 1, "infra": None, "facts": None, "parse_code": "JSON_INVALID",
           "route": {"status": "REFUSED", "code": "JSON_INVALID", "answers": {}, "values": {}}}
    assert E.score_row(inp["cases"]["T2"], inp["gold"]["cases"]["T2"], row, None)["e2e"] == "NO_PARSE"


def test_pilot_gate_and_decision_rule_are_mechanical(inp, tmp_path):
    state = E.run_eval(inp, "PILOT", Scripted(inp, {1: RuntimeError("x")}), tmp_path / "out")
    gate = E.pilot_gate(state, None, 4)
    assert gate["parsed"] == 3 and gate["verdict"] == "STOP"     # 3 < 28 on this tiny schedule
    assert E.clopper_pearson(0, 44)[1] == pytest.approx(0.0804, abs=1e-3)
    assert E.clopper_pearson(44, 44)[0] == pytest.approx(0.9196, abs=1e-3)
    s = {"e2e": {"CORRECT_COMPLETE": 40}, "rows": 44,
         "extraction": {"goal_entity_expressible": "50/52", "extraction_correct": "40/44"}}
    assert E.decide(s)["answer"] == "YES_ON_THIS_CORPUS"
    assert E.decide({**s, "e2e": {"WRONG_SERVED": 1}})["answer"] == "UNSAFE"
    assert E.decide({**s, "extraction": {**s["extraction"], "goal_entity_expressible": "30/52"}})["answer"] == "NO"


def test_locked_inputs_keep_their_registered_hashes_and_gold_outcomes():
    """The real preregistered corpus/gold load under their locked hashes, and the deterministic gold arm still gives
    the recorded per-case status/code/values (a product change that moves them must be re-measured, not absorbed)."""
    real = E.load_inputs()
    rec = json.loads((E.RUN / "results" / "gold" / "gold_rows.json").read_bytes())["rows"]
    now = E.run_gold(real)
    key = lambda r: (r["case_id"], r["route"]["status"], r["route"]["code"], r["route"]["values"])
    assert [key(r) for r in now] == [key(r) for r in rec]
    assert sum(c["split"] == "locked" for c in real["corpus"]["cases"]) == 44


def test_scores_recompute_from_the_persisted_receipt(inp, tmp_path):
    state = E.run_eval(inp, "PILOT", Scripted(inp, {2: RuntimeError("x")}), tmp_path / "out")
    disk = json.loads((tmp_path / "out" / "manifest.json").read_bytes())
    gold = E.run_gold(inp)
    assert E.summarize(inp, disk["rows"], gold) == E.summarize(inp, state["rows"], gold)
