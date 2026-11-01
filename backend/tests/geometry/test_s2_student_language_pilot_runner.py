# -*- coding: utf-8 -*-
"""S-2 pilot runner (`scripts/run_s2_student_language_pilot.py`): gold-replay baseline, projection, live gate, mocks.

All offline. The live path runs against a MOCK provider (the paired harness's scripted `httpx.post`; the conftest
transport guard still blocks the real network underneath) with approved TERMS passed in memory — automation never
writes an approval value (AGENTS.md). A mock run is never live evidence.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import httpx
import pytest

from scripts import run_s2_student_language_pilot as R
from tests.test_paired_route_evaluation import Provider, _body

CORPUS = (Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement"
          / "s2-student-language-pilot-corpus.json")


def _case(cid):
    return next(c for c in json.loads(CORPUS.read_text(encoding="utf-8"))["cases"] if c["id"] == cid)


def _write(tmp_path, cases):
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps({"cases": cases}, ensure_ascii=False), encoding="utf-8")
    return path


def _terms(corpus_path, **over):
    ident = R.runtime_identity()
    return {"pilot": "S-2", "model": ident["model"], "paid_project_confirmed": True, "max_requests": 36,
            "max_usd": 3.0, "input_usd_per_million": 0.30, "output_usd_per_million": 2.50,
            "corpus_sha256": R.sha256_file(corpus_path), "measured_system": ident["measured_system"],
            "runner_sha256": ident["runner_sha256"], "paired_harness_sha256": ident["paired_harness_sha256"], **over}


def _rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _live(tmp_path, monkeypatch, provider, cases, **terms):
    corpus = _write(tmp_path, cases)
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key-never-sent")
    monkeypatch.setattr(httpx, "post", provider)
    return R.evaluate(corpus, tmp_path / "live.jsonl", _terms(corpus, **terms), sleep=lambda s: None)


# ── gold-replay baseline on the registered corpus ───────────────────────────────────────────────────────────────────

def test_gold_replay_of_the_registered_corpus_is_the_attribution_baseline(tmp_path, monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: pytest.fail("a dry run sent a provider request"))
    out = R.evaluate(CORPUS, tmp_path / "dry.jsonl", None)
    assert out["completed"] and out["cases_run"] == 36 and out["http_requests"] == 0
    assert out["measurement_class"] == "OFFLINE_DETERMINISTIC_FIXTURE_TEST"
    m = out["score"]["metrics"]
    assert m["wrong_served_end_to_end"]["numerator"] == 0 and m["false_clarification"]["numerator"] == 0
    sup = out["supplementary"]
    assert (sup["end_to_end_correct"]["numerator"], sup["end_to_end_correct"]["denominator"]) == (33, 36)
    # the three shorthand / tone-typo serve cases are refused by the Source Gate on the GOLD extraction: whatever a live
    # model does there, it cannot be scored as its fault (Master directive §VII)
    failed = {r["case_id"]: (r["hybrid_code"], r["attribution"]) for r in out["rows"] if not r["end_to_end_correct"]}
    assert failed == {"S2-F-S07_typo_tone": ("UNGROUNDED_VALUE", "DETERMINISTIC_LAYER_REPRODUCED_WITH_GOLD"),
                      "S2-F-F05_kc_mp_shorthand": ("SOURCE_OBJECT_MISMATCH", "DETERMINISTIC_LAYER_REPRODUCED_WITH_GOLD"),
                      "S2-F-F06_dt_mp_shorthand": ("SOURCE_OBJECT_MISMATCH", "DETERMINISTIC_LAYER_REPRODUCED_WITH_GOLD")}
    assert sup["false_refusal"]["numerator"] == 3


def test_the_eight_metrics_alone_cannot_see_a_false_refusal(tmp_path):
    """Why `supplementary` exists: on the gold replay all eight metrics are perfect while 3 serve cases are refused."""
    out = R.evaluate(CORPUS, tmp_path / "dry.jsonl", None)
    m = out["score"]["metrics"]
    assert all(m[k]["rate"] == 1.0 for k in ("extraction_accuracy", "goal_completeness", "operand_preservation",
                                             "ambiguity_detection", "clarification_correctness",
                                             "unsupported_classification"))
    assert out["supplementary"]["false_refusal"]["rate"] > 0


# ── projection: one function for gold and observed ──────────────────────────────────────────────────────────────────

def test_projection_ignores_ids_quotes_and_order_but_not_facts():
    gold = _case("S2-B-P07_shared_intermediate_two_goals")["gold_extraction"]
    renamed = deepcopy(gold)
    renamed["solids"][0]["solid_id"] = "chop"
    for item in (*renamed["premises"], *renamed["math_goals"]):
        item["solid_id"] = "chop"
    renamed["simulation_goals"][0]["target_solid_id"] = "chop"
    renamed["premises"].reverse()
    renamed["math_goals"].reverse()
    for g in renamed["math_goals"]:
        g["goal_id"], g["quote"] = g["goal_id"] + "x", "Tính"
    assert R.project(renamed) == R.project(gold)
    wrong = deepcopy(gold)
    wrong["premises"][2]["args"]["value"] = "3"
    assert R.project(wrong)["facts_signature"] != R.project(gold)["facts_signature"]
    assert "3" in R.project(wrong)["operands"] and "3" not in R.project(gold)["operands"]
    dropped = deepcopy(gold)
    dropped["math_goals"].pop()
    assert R.project(dropped)["goals"] != R.project(gold)["goals"]
    assert R.project(None) is None and R.project({"solids": [{"notation": "x"}]}) is None


def test_extraction_fields_are_expected_only_where_evaluable():
    assert "expected_facts_signature" in R.expected_record(_case("S2-D-D03_contradictory_length"))
    assert "expected_facts_signature" not in R.expected_record(_case("S2-C-A01_goc_chieu"))   # honest exit
    assert "expected_facts_signature" not in R.expected_record(_case("S2-E-E01_oxyz"))        # honest exit


@pytest.mark.parametrize("mutate", [
    lambda cs: cs * 2,                                                          # duplicates
    lambda cs: [c | {"id": f"{c['id']}-{i}", "problem_text": f"{c['problem_text']} {i}"} for i, c in enumerate(cs * 37)],
    lambda cs: [cs[0] | {"stratum": "S2-Z"}],
    lambda cs: [cs[0] | {"expected": {"outcome": "CLARIFY", "is_ambiguous": False}}],
    lambda cs: [cs[0] | {"expected": {"outcome": "CLARIFY", "is_ambiguous": True,
                                      "allowed_clarification_codes": ["INCOMPLETE_GOAL_OPERAND"]}}],
    lambda cs: [cs[0] | {"expected": {"outcome": "SERVED", "is_ambiguous": False, "oracle": {"volume": ["2.67"]}}}],
    lambda cs: [cs[0] | {"expected": {"outcome": "SERVED", "is_ambiguous": False}}],             # no oracle at all
    lambda cs: [cs[0] | {"gold_extraction": _case("S2-B-I07_ve_va_tinh")["gold_extraction"]}],  # another text's gold
])
def test_an_invalid_corpus_is_refused(mutate):
    with pytest.raises(R.LiveRefused):
        R.validate_corpus({"cases": mutate([_case("S2-A-I02_ve")])})


# ── live gate (§4): refused before any request ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("over,why", [
    ({"pilot": "paired"}, "S-2"), ({"paid_project_confirmed": "yes"}, "paid"), ({"max_requests": 37}, "max_requests"),
    ({"max_requests": 36, "max_usd": 0.01}, "exceeds max_usd"), ({"corpus_sha256": "0" * 64}, "data scope"),
    ({"runner_sha256": "0" * 64}, "runner_sha256"), ({"paired_harness_sha256": "0" * 64}, "paired_harness"),
    ({"measured_system": "0" * 64}, "measured_system"), ({"model": "gemini-other"}, "model"),
])
def test_the_approved_terms_are_checked_before_any_request(tmp_path, over, why):
    corpus = _write(tmp_path, [_case("S2-A-I02_ve")])
    with pytest.raises(R.LiveRefused, match=why):
        R.check_approval_terms(corpus.read_bytes(), _terms(corpus, **over))
    terms = _terms(corpus)
    del terms["paid_project_confirmed"]
    with pytest.raises(R.LiveRefused, match="lacks"):
        R.check_approval_terms(corpus.read_bytes(), terms)


def test_live_is_refused_without_the_environment_or_an_owner_approval(tmp_path, monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: pytest.fail("a refused run sent a request"))
    corpus = _write(tmp_path, [_case("S2-A-I02_ve")])
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)
    with pytest.raises(R.LiveRefused, match="ALLOW_LIVE_AI"):
        R.authorize_live(corpus, None)
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key-never-sent")
    with pytest.raises(R.LiveRefused, match="approval file"):
        R.authorize_live(corpus, tmp_path / "missing.json")
    approval = tmp_path / "approval.json"
    approval.write_text(json.dumps(_terms(corpus) | {"owner_decision": "PENDING"}), encoding="utf-8")
    with pytest.raises(R.LiveRefused, match="APPROVED_BY_USER"):
        R.authorize_live(corpus, approval)


# ── mock provider ───────────────────────────────────────────────────────────────────────────────────────────────────

def test_mock_faithful_extraction_is_scored_with_cost_and_the_key_is_never_written(tmp_path, monkeypatch):
    case = _case("S2-B-I11_mo_phong_va_tinh_SC")
    out = _live(tmp_path, monkeypatch, Provider(_body(case["gold_extraction"])), [case])
    row = out["rows"][0]
    assert out["completed"] and out["measurement_class"] == "LIVE_DEVELOPMENT_PILOT" and out["http_requests"] == 1
    assert row["end_to_end_correct"] and row["attribution"] is None and row["observed"]["answers"] == {"distance": ["2√3"]}
    assert isinstance(row["usd"], float) and 0 < row["usd"] <= row["usd_upper"]
    assert "offline-test-key-never-sent" not in (tmp_path / "live.jsonl").read_text(encoding="utf-8")


def test_mock_extractor_error_is_attributed_to_the_extraction_not_the_engine(tmp_path, monkeypatch):
    case = _case("S2-A-I02_ve")
    bad = deepcopy(case["gold_extraction"])                          # an invented volume goal on a simulation request
    bad["math_goals"] = [{"goal_id": "mg1", "kind": "measurement", "goal_type": "volume", "target": {"solid_id": "s1"},
                          "quote": bad["simulation_goals"][0]["quote"], "solid_id": "s1"}]
    out = _live(tmp_path, monkeypatch, Provider(_body(bad)), [case])
    row = out["rows"][0]
    assert not row["end_to_end_correct"] and row["gold_replay_end_to_end_correct"]
    assert row["attribution"] == "LLM_EXTRACTION_DIFFERS_FROM_GOLD"
    assert out["score"]["metrics"]["wrong_served_end_to_end"]["numerator"] == 0      # refused, never served


def test_mock_honest_exit_becomes_a_clarification(tmp_path, monkeypatch):
    case = _case("S2-C-D05_projection_missing_target")
    out = _live(tmp_path, monkeypatch, Provider(_body(case["gold_extraction"])), [case])
    obs = out["rows"][0]["observed"]
    assert obs["status"] == "CLARIFY" and obs["clarification_code"] == "MISSING_DATA" and obs["unresolved_flagged"]
    assert out["score"]["metrics"]["ambiguity_detection"]["numerator"] == 1


def test_three_infrastructure_failures_stop_the_run_and_are_never_scored(tmp_path, monkeypatch):
    cases = [_case(c) for c in ("S2-A-I02_ve", "S2-A-I04_mo_phong", "S2-A-I05_cho_minh_xem", "S2-A-I08_trailing_ve")]
    out = _live(tmp_path, monkeypatch, Provider(default=400), cases)
    assert out["stop_reason"] == "INFRASTRUCTURE_STREAK" and not out["completed"] and out["cases_run"] == 3
    assert out["score"]["evaluable_records"] == 0 and out["score"]["not_recoverable_records"] == 3
    assert out["score"]["metrics"]["wrong_served_end_to_end"]["rate"] == "UNKNOWN"         # never coerced to 0
    assert {r["attribution"] for r in out["rows"]} == {"INFRASTRUCTURE"}
    assert _rows(tmp_path / "live.jsonl")[-1]["stop_reason"] == "INFRASTRUCTURE_STREAK"


def test_request_cap_blocks_the_next_request_before_it_is_sent(tmp_path, monkeypatch):
    provider = Provider(default=httpx.ConnectError("mock: unreachable"))
    out = _live(tmp_path, monkeypatch, provider, [_case("S2-A-I02_ve")], max_requests=1)
    assert provider.calls == 1 and out["stop_reason"] == "REQUEST_CAP" and not out["completed"]


def test_a_run_never_overwrites_an_earlier_output(tmp_path):
    out = tmp_path / "dry.jsonl"
    out.write_text("earlier\n", encoding="utf-8")
    with pytest.raises(FileExistsError):
        R.evaluate(CORPUS, out, None)
    assert out.read_text(encoding="utf-8") == "earlier\n"
