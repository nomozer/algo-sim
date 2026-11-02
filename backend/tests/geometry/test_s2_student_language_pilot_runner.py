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
            "runner_sha256": ident["runner_sha256"], "paired_harness_sha256": ident["paired_harness_sha256"],
            "scorer_sha256": ident["scorer_sha256"], **over}


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
    # Baseline of the product under test. At candidate 800ab355 it was 33/36 (F05 "k/c … mp(SBC)" and F06 "đt … mp"
    # also refused, `s2-pilot-gold-replay-r2.jsonl`); SL-3 (thirteenth continuation, registry /29) reads that shorthand.
    assert (sup["end_to_end_correct"]["numerator"], sup["end_to_end_correct"]["denominator"]) == (35, 36)
    # the tone-typo serve case is refused by the Source Gate on the GOLD extraction (S-1 policy, not guessed): whatever a
    # live model does there in the same way, it cannot be scored as its fault (Master directive §VII)
    failed = {r["case_id"]: (r["hybrid_code"], r["attribution"]) for r in out["rows"] if not r["end_to_end_correct"]}
    assert failed == {"S2-F-S07_typo_tone": ("UNGROUNDED_VALUE", "DETERMINISTIC_LAYER_REPRODUCED_WITH_GOLD")}
    assert sup["false_refusal"]["numerator"] == 1


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
    ({"scorer_sha256": "0" * 64}, "scorer_sha256"),          # C14 review MINOR: the scorer that writes the summary
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


# ── C15: the same runner measures the R-1 described-point study ─────────────────────────────────────────────────────

_R1_TEXT = ("Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). SA = 2. "
            "Tính khoảng cách từ giao điểm của AC và BD đến mặt phẳng (SBC).")


def _r1_case(cid="R1-A-X", stratum="R1-A"):
    """An R-1 case whose gold asks through an UNNAMED described point (C13 probe row C2, oracle √2/2)."""
    gold = {"schema_version": "typed-fact-next/2", "problem_text": _R1_TEXT, "length_unit": "1",
            "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
            "premises": [
                {"kind": "regular_polygon", "args": {"vertices": list("ABCD"), "side": "2"},
                 "quote": "Đáy ABCD là hình vuông cạnh 2", "solid_id": "s1"},
                {"kind": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": list("ABCD")},
                 "quote": "SA vuông góc với (ABCD)", "solid_id": "s1"},
                {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "2"}, "quote": "SA = 2",
                 "solid_id": "s1"}],
            "derived_sections": [], "relations": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1",
                                  "quote": "Cho hình chóp S.ABCD"}],
            "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance",
                            "target": {"point": "@o1", "plane": ["S", "B", "C"]}, "solid_id": "s1",
                            "quote": "Tính khoảng cách từ giao điểm của AC và BD đến mặt phẳng (SBC)"}],
            "described_points": [{"described_id": "o1", "kind": "intersect_line_line", "quote": "giao điểm của AC và BD",
                                  "line1": ["A", "C"], "line2": ["B", "D"]}]}
    return {"id": cid, "stratum": stratum, "problem_text": _R1_TEXT, "gold_extraction": gold,
            "expected": {"outcome": "SERVED", "oracle": {"distance": ["√2/2"]}}}


def _write_study(tmp_path, study, cases):
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps({"study": study, "cases": cases}, ensure_ascii=False), encoding="utf-8")
    return path


def test_c15_a_corpus_names_its_study_and_the_s2_corpus_stays_s2(tmp_path):
    R.validate_corpus({"cases": [_case("S2-A-I02_ve")]})                         # no `study` ⇒ S-2, as locked
    R.validate_corpus({"study": "R-1", "cases": [_r1_case()]})
    with pytest.raises(R.LiveRefused, match="stratum"):
        R.validate_corpus({"study": "R-1", "cases": [_case("S2-A-I02_ve")]})      # an S-2 stratum is not an R-1 one
    with pytest.raises(R.LiveRefused, match="study"):
        R.validate_corpus({"study": "R-9", "cases": [_r1_case()]})
    with pytest.raises(R.LiveRefused, match="1..18"):
        R.validate_corpus({"study": "R-1", "cases": [_r1_case(f"R1-A-{i}") for i in range(19)]})


def test_c15_an_approval_binds_exactly_one_study(tmp_path):
    corpus = _write_study(tmp_path, "R-1", [_r1_case()])
    with pytest.raises(R.LiveRefused, match="R-1"):
        R.check_approval_terms(corpus.read_bytes(), _terms(corpus))              # an S-2 approval on the R-1 corpus
    with pytest.raises(R.LiveRefused, match="max_requests"):
        R.check_approval_terms(corpus.read_bytes(), _terms(corpus, pilot="R-1", max_requests=19))
    assert R.check_approval_terms(corpus.read_bytes(), _terms(corpus, pilot="R-1", max_requests=18))["pilot"] == "R-1"
    s2 = _write(tmp_path, [_case("S2-A-I02_ve")])
    with pytest.raises(R.LiveRefused, match="S-2"):
        R.check_approval_terms(s2.read_bytes(), _terms(s2, pilot="R-1"))


def test_c15_realizing_the_models_own_described_point_is_not_a_discovered_composition(tmp_path):
    """C15 review MAJOR-1: the planner calls the step that builds a described point its own, and labels the plan
    DISCOVERED; but that step is exactly what the extraction stated, so the plan is source-explicit."""
    out = R.evaluate(_write_study(tmp_path, "R-1", [_r1_case()]), tmp_path / "dry.jsonl", None)
    row = out["rows"][0]
    # planner /24 (C16) no longer self-labels this DISCOVERED: the product label and the runner's rule now agree
    assert row["end_to_end_correct"] and row["search"]["classification"] == "SOURCE_EXPLICIT_SEQUENCE"
    assert [s["fn"] for s in row["search"]["planner_steps"]] == ["intersect_line_line"]
    assert row["composition_label"] == "SOURCE_EXPLICIT_SEQUENCE"
    assert out["supplementary"]["composition_labels"] == {"SOURCE_EXPLICIT_SEQUENCE": 1}
    assert set(out["supplementary"]["by_stratum"]) == {"R1-A", "R1-B", "R1-C", "R1-D", "R1-E", "R1-F", "R1-G"}
    no_step = dict(row, search={"classification": "DISCOVERED_FUNCTION_COMPOSITION", "planner_steps": []})
    assert R.composition_label(no_step) == "SOURCE_EXPLICIT_SEQUENCE"   # the planner's own label is never evidence
    assert R.composition_label(dict(row, search={})) == "NOT_ESTABLISHED"   # no recorded steps: nothing to judge


def test_c16_the_rule_runs_whatever_the_planner_calls_its_plan():
    """C16 review MAJOR: /24 never self-labels DISCOVERED, so a rule gated on that label would never run."""
    new = {"id": "q1_aux3", "fn": "centroid", "args": {"point": "G", "polygon": ["S", "A", "B"]}}
    row = dict(_served([new]), search={"classification": "SOURCE_EXPLICIT_SEQUENCE", "planner_steps": [new]})
    assert R.composition_label(row) == "DISCOVERED_FUNCTION_COMPOSITION"
    base = {"id": "f1_day", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"]}}   # a definition
    assert R.composition_label(_served([base])) == "SOURCE_EXPLICIT_SEQUENCE"


def _served(steps, described=()):
    return {"technical_failure": False, "end_to_end_correct": True, "expected": {"outcome": "SERVED"},
            "observed": {"status": "SERVED"}, "raw_extraction": {"described_points": list(described)},
            "search": {"classification": "DISCOVERED_FUNCTION_COMPOSITION", "planner_steps": list(steps)}}


def test_c15_only_a_step_beyond_the_description_and_the_registered_rules_is_discovered():
    h1 = {"described_id": "h1", "kind": "orthogonal_projection", "quote": "q", "point": "B", "plane": ["S", "A", "C"]}
    real = {"id": "q1_aux", "fn": "orthogonal_projection", "args": {"point": "B", "plane": ["S", "A", "C"], "image": "H"}}
    rule = {"id": "q1_aux2", "fn": "orthogonal_projection_line", "args": {"point": "H", "line": ["C", "S"], "image": "H1"}}
    new = {"id": "q1_aux3", "fn": "centroid", "args": {"point": "G", "polygon": ["S", "A", "B"]}}
    assert R.composition_label(_served([real], [h1])) == "SOURCE_EXPLICIT_SEQUENCE"
    assert R.composition_label(_served([real, rule], [h1])) == "REGISTERED_DECOMPOSITION"     # distance(point,line)
    assert R.composition_label(_served([real, rule, new], [h1])) == "DISCOVERED_FUNCTION_COMPOSITION"
    # not the stated point; C17 put `orthogonal_projection` in a declared rule, so a function outside every rule is used
    moved = {"id": "a", "fn": "centroid", "args": {"point": "G", "polygon": ["S", "A", "C"]}}
    assert R.composition_label(_served([moved], [h1])) == "DISCOVERED_FUNCTION_COMPOSITION"
    swapped = dict(real, args={"point": "B", "plane": ["C", "S", "A"], "image": "H"})        # same plane, other order
    assert R.composition_label(_served([swapped], [h1])) == "SOURCE_EXPLICIT_SEQUENCE"
    # round 2: a scope-qualified label is the same point (MINOR-A); the operands are matched in any order (NIT-1) —
    # `intersect_line_plane` specs name the plane first in JSON order, the call names the line first
    qualified = dict(h1, point="s1::B", plane=["s1::S", "s1::A", "s1::C"])
    assert R.composition_label(_served([real], [qualified])) == "SOURCE_EXPLICIT_SEQUENCE"
    i1 = {"described_id": "i1", "kind": "intersect_line_plane", "quote": "q", "plane": ["S", "B", "D"], "line": ["A", "M"]}
    call = {"id": "a", "fn": "intersect_line_plane", "args": {"point": "I", "line": ["A", "M"], "plane": ["S", "B", "D"]}}
    assert R.composition_label(_served([call], [i1])) == "SOURCE_EXPLICIT_SEQUENCE"
    ll = {"described_id": "o1", "kind": "intersect_line_line", "quote": "q", "line1": ["A", "C"], "line2": ["B", "D"]}
    swap = {"id": "a", "fn": "intersect_line_line", "args": {"point": "O", "line1": ["D", "B"], "line2": ["C", "A"]}}
    assert R.composition_label(_served([swap], [ll])) == "SOURCE_EXPLICIT_SEQUENCE"
    mid = {"described_id": "m1", "kind": "midpoint", "quote": "q", "segment": ["S", "B"]}
    assert R.composition_label(_served([{"id": "a", "fn": "midpoint", "args": {"point": "M", "segment": ["B", "S"]}}],
                                       [mid])) == "SOURCE_EXPLICIT_SEQUENCE"


def test_c15_the_registered_r1_corpus_and_its_gold_replay_are_locked(tmp_path):
    """C15 review MINOR-2: the corpus validates, and its gold replay reproduces the committed receipt."""
    corpus = CORPUS.parent / "r1-live-pilot-corpus.json"
    R.validate_corpus(json.loads(corpus.read_text(encoding="utf-8")))
    out = R.evaluate(corpus, tmp_path / "dry.jsonl", None)
    receipt = _rows(CORPUS.parent / "r1-live-pilot-gold-replay-r2.jsonl")   # C16: runner records label disagreements
    # the receipt hashed the LF bytes it ran on; a fresh checkout under core.autocrlf=true holds CRLF (Full T3 attempt 1)
    import hashlib
    assert receipt[0]["corpus_sha256"] == hashlib.sha256(corpus.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert {r["case_id"]: r["composition_label"] for r in out["rows"]} == {
        r["case_id"]: r["composition_label"] for r in receipt if r["type"] == "row"}
    sup = dict(out["supplementary"])
    outcomes = sup.pop("hybrid_outcomes")                    # C19: a new field the C16 receipt predates
    assert sup == receipt[-1]["supplementary"]
    assert out["score"]["metrics"]["wrong_served_end_to_end"]["numerator"] == 0
    assert (outcomes["SERVED_CORRECT"], outcomes["FALSE_REFUSAL"], outcomes["SERVED_WRONG"]) == (11, 2, 0)


def test_c15_the_models_own_described_points_are_checked_against_gold():
    gold = _r1_case()["gold_extraction"]
    assert R.described_check(gold, gold, _R1_TEXT) == {"emitted": True, "kinds_match": True, "refs_resolve": True,
                                                        "quotes_verbatim": True}
    assert R.described_check(_case("S2-A-I02_ve")["gold_extraction"], gold, _R1_TEXT) is None   # gold declares none
    named = deepcopy(gold)                                   # the model named the point instead of describing it
    named.pop("described_points")
    named["math_goals"][0]["target"]["point"] = "O"
    assert R.described_check(gold, named, _R1_TEXT)["emitted"] is False
    wrong = deepcopy(gold)
    wrong["described_points"][0].update(kind="midpoint", quote="giao điểm của AC")          # paraphrase is fine
    wrong["math_goals"][0]["target"]["point"] = "@x9"
    assert R.described_check(gold, wrong, _R1_TEXT) == {"emitted": True, "kinds_match": False, "refs_resolve": False,
                                                         "quotes_verbatim": True}
    wrong["described_points"][0]["quote"] = "giao điểm hai đường chéo"
    assert R.described_check(gold, wrong, _R1_TEXT)["quotes_verbatim"] is False
    assert R.described_check(gold, None, _R1_TEXT)["emitted"] is False                     # no readable extraction
    # C15 review MINOR-1: each condition is load-bearing
    unref = deepcopy(gold)                                    # a spec is emitted but nothing refers to it
    unref["math_goals"][0]["target"]["point"] = "O"
    assert R.described_check(gold, unref, _R1_TEXT)["refs_resolve"] is False
    empty = deepcopy(gold)
    empty["described_points"][0]["quote"] = ""                # "" is in every text: never verbatim
    assert R.described_check(gold, empty, _R1_TEXT)["quotes_verbatim"] is False
    two = deepcopy(gold)                                      # gold has 1 intersection; 2 intersections ≠ the multiset
    two["described_points"].append(dict(two["described_points"][0], described_id="o2"))
    assert R.described_check(gold, two, _R1_TEXT)["kinds_match"] is False
    assert R.described_check(gold, named, _R1_TEXT)["quotes_verbatim"] is False   # no spec: never vacuously verbatim


def test_c15_mock_live_a_model_that_names_the_point_is_an_extraction_failure_never_a_serve(tmp_path, monkeypatch):
    named = deepcopy(_r1_case()["gold_extraction"])
    named.pop("described_points")
    named["math_goals"][0]["target"]["point"] = "O"                      # invents a label the text never gives
    corpus = _write_study(tmp_path, "R-1", [_r1_case()])
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key-never-sent")
    monkeypatch.setattr(httpx, "post", Provider(_body(named)))
    out = R.evaluate(corpus, tmp_path / "live.jsonl", _terms(corpus, pilot="R-1", max_requests=18), sleep=lambda s: None)
    row = out["rows"][0]
    assert out["completed"] and row["observed"]["status"] != "SERVED" and row["gold_replay_end_to_end_correct"]
    assert row["composition_label"] == "EXTRACTION_FAILURE" and row["described_check"]["emitted"] is False
    assert out["supplementary"]["described_points"]["emitted"]["rate"] == 0.0


@pytest.mark.parametrize("code,attribution,label", [
    ("BRIDGE_UNSUPPORTED_DESCRIBED_POINT", "DETERMINISTIC_LAYER_REPRODUCED_WITH_GOLD", "REPRESENTATION_BLOCKED"),
    ("SOURCE_OBJECT_MISMATCH", "DETERMINISTIC_LAYER_REPRODUCED_WITH_GOLD", "SOURCE_GROUNDING_FAILURE"),
    ("PLAN_TOO_LARGE", "DETERMINISTIC_LAYER_REPRODUCED_WITH_GOLD", "PLANNER_SEARCH_FAILURE"),
    ("UNSUPPORTED_CAPABILITY", "DETERMINISTIC_LAYER_REPRODUCED_WITH_GOLD", "MISSING_PRIMITIVE"),
    ("ENGINE_SELF_CHECK_FAILED", "DETERMINISTIC_LAYER_REPRODUCED_WITH_GOLD", "KERNEL_VERIFICATION_FAILURE"),
    ("SOURCE_OBJECT_MISMATCH", "LLM_EXTRACTION_DIFFERS_FROM_GOLD", "EXTRACTION_FAILURE"),
    ("SOURCE_OBJECT_MISMATCH", "UNATTRIBUTED", "NOT_ESTABLISHED"),
])
def test_c15_a_failed_row_is_labelled_by_the_layer_its_gold_reproduction_names(code, attribution, label):
    row = {"technical_failure": False, "end_to_end_correct": False, "attribution": attribution, "hybrid_code": code,
           "expected": {"outcome": "SERVED"}, "observed": {"status": "REFUSED"}}
    assert R.composition_label(row) == label
    assert R.composition_label(dict(row, observed={"status": "SERVED"})) == "WRONG_SERVED"
    assert R.composition_label(dict(row, technical_failure=True)) == "NOT_ESTABLISHED"
    assert R.composition_label(dict(row, end_to_end_correct=True, expected={"outcome": "CLARIFY"})) == "CORRECT_REFUSAL"


class _Ran(Exception):
    pass


def test_one_approval_one_live_run_and_a_second_is_refused_before_any_request(tmp_path, monkeypatch):
    """C14: the caps count requests per process, so a second `--live` under the same approval would re-send requests
    the first one already counted. An interrupted run is never resumed under the approval it consumed."""
    corpus = _write(tmp_path, [_case("S2-A-I02_ve")])
    approval = tmp_path / "approval.json"
    approval.write_text("{}", encoding="utf-8")         # `authorize_live` is stubbed: tests never write an approval value
    monkeypatch.setattr(R, "authorize_live", lambda c, a: _terms(corpus))
    runs = []

    def ran(c, out, terms):
        runs.append(out)
        raise _Ran
    monkeypatch.setattr(R, "evaluate", ran)
    argv = ["--corpus", str(corpus), "--live", "--approval-file", str(approval), "--out"]
    (tmp_path / "taken.jsonl").write_text("earlier\n", encoding="utf-8")
    with pytest.raises(FileExistsError):                # a taken --out is refused before the approval is consumed
        R.main([*argv, str(tmp_path / "taken.jsonl")])
    with pytest.raises(_Ran):
        R.main([*argv, str(tmp_path / "first.jsonl")])
    with pytest.raises(R.LiveRefused, match="consumed"):
        R.main([*argv, str(tmp_path / "second.jsonl")])
    assert runs == [tmp_path / "first.jsonl"]


def test_a_run_never_overwrites_an_earlier_output(tmp_path):
    out = tmp_path / "dry.jsonl"
    out.write_text("earlier\n", encoding="utf-8")
    with pytest.raises(FileExistsError):
        R.evaluate(CORPUS, out, None)
    assert out.read_text(encoding="utf-8") == "earlier\n"


# ── review round 1 (M1–M3, m1, m3): each finding locked ─────────────────────────────────────────────────────────────

def test_M1_a_reversed_segment_is_the_same_goal_and_a_correct_serve_is_not_wrong_served(tmp_path, monkeypatch):
    case = _case("S2-B-I11_mo_phong_va_tinh_SC")
    rev = deepcopy(case["gold_extraction"])
    rev["math_goals"][0]["target"]["segment"] = ["C", "S"]
    rev["premises"][1]["args"]["plane"] = ["D", "C", "B", "A"]          # a plane's labels are a set
    assert R.project(rev) == R.project(case["gold_extraction"])
    out = _live(tmp_path, monkeypatch, Provider(_body(rev)), [case])
    row = out["rows"][0]
    assert row["observed"]["status"] == "SERVED" and row["end_to_end_correct"] and row["attribution"] is None
    assert out["score"]["metrics"]["wrong_served_end_to_end"]["numerator"] == 0


def test_M1_polygon_order_still_matters():
    gold = _case("S2-B-I11_mo_phong_va_tinh_SC")["gold_extraction"]
    swapped = deepcopy(gold)
    swapped["premises"][0]["args"]["vertices"] = ["A", "C", "B", "D"]
    assert R.project(swapped)["facts_signature"] != R.project(gold)["facts_signature"]


def test_M2_an_inconsistent_case_refused_for_the_wrong_reason_is_not_correct(tmp_path, monkeypatch):
    case = _case("S2-D-D03_contradictory_length")
    dropped = deepcopy(case["gold_extraction"])
    dropped["premises"] = [p for p in dropped["premises"] if p["quote"] != "SC = 5"]   # the contradiction left unread
    out = _live(tmp_path, monkeypatch, Provider(_body(dropped)), [case])
    row = out["rows"][0]
    assert row["observed"]["status"] == "REFUSED" and row["observed"]["refusal_group"] != "INVALID_DATA"
    assert row["end_to_end_correct"] is False and row["gold_replay_end_to_end_correct"] is True
    assert row["attribution"] == "LLM_EXTRACTION_DIFFERS_FROM_GOLD"


def test_M3_a_gold_failing_case_does_not_excuse_a_different_model_fault(tmp_path, monkeypatch):
    case = _case("S2-F-S07_typo_tone")                           # gold refused UNGROUNDED_VALUE ("hình chop")
    forged = deepcopy(case["gold_extraction"])
    forged["math_goals"][0]["quote"] = "Tính thể tích khối chóp S.ABCD bằng"           # not in the source
    out = _live(tmp_path, monkeypatch, Provider(_body(forged)), [case])
    row = out["rows"][0]
    assert row["hybrid_code"] != "UNGROUNDED_VALUE" and not row["gold_replay_end_to_end_correct"]
    assert row["attribution"] == "LLM_EXTRACTION_DIFFERS_FROM_GOLD"
    (tmp_path / "same").mkdir()
    same = _live(tmp_path / "same", monkeypatch, Provider(_body(case["gold_extraction"])), [case])
    assert same["rows"][0]["attribution"] == "DETERMINISTIC_LAYER_REPRODUCED_WITH_GOLD"


@pytest.mark.parametrize("over", [{"max_usd": float("nan")}, {"max_usd": float("inf")}, {"max_usd": 0},
                                  {"max_usd": True}, {"input_usd_per_million": 0}, {"output_usd_per_million": -2.5},
                                  {"max_requests": True}, {"max_requests": 3.0}])
def test_m1_numeric_terms_that_would_disable_a_cap_are_refused(tmp_path, over):
    corpus = _write(tmp_path, [_case("S2-A-I02_ve")])
    with pytest.raises(R.LiveRefused):
        R.check_approval_terms(corpus.read_bytes(), _terms(corpus, **over))


def test_m3_a_domain_gate_row_costs_zero_and_the_run_reports_its_status(tmp_path, monkeypatch):
    provider = Provider(default=500)
    out = _live(tmp_path, monkeypatch, provider, [_case("S2-E-E01_oxyz")])
    assert provider.calls == 0 and out["rows"][0]["usd"] == 0.0 and out["spent_reported_usd"] == 0.0
    assert out["run_status"] == "COMPLETE" and out["rows"][0]["attribution"] is None


# ── review round 2 (MINOR 1–3) ──────────────────────────────────────────────────────────────────────────────────────

def test_r2_labels_inside_a_symmetric_pair_are_canonical_too():
    g = lambda t: R.project({"solids": [], "math_goals": [{"goal_id": "g", "kind": "measurement", "goal_type": "distance",
                                                            "target": t, "quote": "q"}]})["goals"]
    assert g({"line1": ["S", "C"], "line2": ["A", "B"]}) == g({"line1": ["B", "A"], "line2": ["C", "S"]})
    assert g({"plane1": ["S", "B", "C"], "plane2": list("ABCD")}) == g({"plane1": list("DCBA"), "plane2": ["S", "C", "B"]})
    assert g({"line1": ["S", "C"], "line2": ["A", "B"]}) != g({"line1": ["S", "A"], "line2": ["C", "B"]})


def test_r2_the_segment_of_a_ratio_keeps_its_direction():
    p = lambda seg: R.project({"solids": [], "premises": [{"kind": "divide_segment", "quote": "q", "args": {
        "point": "M", "segment": seg, "ratio": "1/3"}}]})["facts_signature"]
    assert p(["S", "C"]) != p(["C", "S"])
    m = lambda seg: R.project({"solids": [], "premises": [{"kind": "midpoint", "quote": "q", "args": {
        "point": "M", "segment": seg}}]})["facts_signature"]
    assert m(["S", "C"]) == m(["C", "S"])


def test_r2_a_wrong_serve_of_the_gold_facts_is_the_deterministic_layer_but_other_facts_are_not():
    gold = _case("S2-B-I11_mo_phong_va_tinh_SC")["gold_extraction"]
    expected = R.expected_record(_case("S2-B-I11_mo_phong_va_tinh_SC"))
    wrong = {"status": "SERVED", "answers": {"distance": ["3"]}, "certificate_verified": True,
             "quotes_verbatim_in_raw": True}
    row = {"technical_failure": False, "end_to_end_correct": False, "expected": expected, "observed": wrong,
           "hybrid_code": None, "raw_extraction": gold}
    assert R.attribute(row, dict(wrong), None, gold) == "DETERMINISTIC_LAYER_REPRODUCED_WITH_GOLD"
    other = deepcopy(gold)
    other["premises"][2]["args"]["value"] = "3"
    assert R.attribute(row | {"raw_extraction": other}, dict(wrong), None, gold) == "LLM_EXTRACTION_DIFFERS_FROM_GOLD"


def test_r1_project_normalizes_described_point_ids_without_leaking_uppercase_id_tokens():
    a = {
        "solids": [{"solid_id": "s1", "notation": "S.ABCD", "quote": "q"}],
        "described_points": [{"described_id": "m1", "kind": "midpoint", "segment": ["S", "C"], "quote": "q"}],
        "math_goals": [{"goal_id": "g1", "kind": "measurement", "goal_type": "distance",
                        "target": {"point": "@m1", "plane": ["A", "B", "C"]}, "quote": "q"}],
    }
    b = {
        "solids": [{"solid_id": "pyr", "notation": "S.ABCD", "quote": "q2"}],
        "described_points": [{"described_id": "M9", "kind": "midpoint", "segment": ["C", "S"], "quote": "q2"}],
        "math_goals": [{"goal_id": "g9", "kind": "measurement", "goal_type": "distance",
                        "target": {"point": "@M9", "plane": ["C", "B", "A"]}, "quote": "q2"}],
    }
    diff = deepcopy(b)
    diff["described_points"][0]["segment"] = ["S", "A"]
    assert R.project(a) == R.project(b)
    assert "M9" not in R.project(b)["operands"]
    assert R.project(a) != R.project(diff)


def test_r1_project_ignores_openapi_nullable_none_fields_and_outer_whitespace_on_described_refs():
    """Review MINOR-3: Gemini OpenAPI `nullable: True` emits explicit `None` for unused optional fields on
    `DescribedPointSpec` / goals, and `is_described_ref` trims outer whitespace."""
    gold = {
        "solids": [{"solid_id": "s1", "notation": "S.ABCD", "quote": "q"}],
        "described_points": [{"described_id": "m1", "kind": "midpoint", "segment": ["S", "C"], "quote": "q"}],
        "math_goals": [{"goal_id": "g1", "kind": "measurement", "goal_type": "distance",
                        "target": {"point": "@m1", "plane": ["A", "B", "C"]}, "quote": "q"}],
    }
    nullable = {
        "solids": [{"solid_id": "s1", "notation": "S.ABCD", "quote": "q", "center": None, "radius": None}],
        "described_points": [{
            "described_id": "m1", "kind": "midpoint", "segment": ["S", "C"], "quote": "q",
            "point": None, "polygon": None, "line": None, "line1": None, "line2": None, "plane": None,
        }],
        "math_goals": [{
            "goal_id": "g1", "kind": "measurement", "goal_type": "distance", "solid_id": None,
            "target": {"point": "  @m1  ", "plane": ["A", "B", "C"]}, "quote": "q",
        }],
    }
    assert R.project(nullable) == R.project(gold)


# ── C19: K-1 (constraint planes, points named by a property) and the Hybrid-only outcome taxonomy ────────────────────

K1 = CORPUS.parent / "k1-live-pilot-corpus.json"


def _k1(cid):
    return next(c for c in json.loads(K1.read_text(encoding="utf-8"))["cases"] if c["id"] == cid)


def _k1_live(tmp_path, monkeypatch, provider, cases, **terms):
    corpus = _write_study(tmp_path, "K-1", cases)
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key-never-sent")
    monkeypatch.setattr(httpx, "post", provider)
    return R.evaluate(corpus, tmp_path / "live.jsonl", _terms(corpus, pilot="K-1", max_requests=16, max_usd=1.0, **terms),
                      sleep=lambda s: None)


def test_c19_the_k1_gold_replay_is_the_locked_attribution_baseline(tmp_path, monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: pytest.fail("a dry run sent a provider request"))
    out = R.evaluate(K1, tmp_path / "dry.jsonl", None)
    assert out["completed"] and out["cases_run"] == 16 and out["http_requests"] == 0 and out["cases_not_measured"] == 0
    sup = out["supplementary"]
    assert (sup["end_to_end_correct"]["numerator"], sup["end_to_end_correct"]["denominator"]) == (16, 16)
    assert sup["hybrid_outcomes"] == {"SERVED_CORRECT": 10, "SERVED_WRONG": 0, "CORRECT_REFUSAL": 4, "FALSE_REFUSAL": 0,
                                      "WRONG_REASON_REFUSAL": 0, "CORRECT_CLARIFICATION": 2,
                                      "WRONG_REASON_CLARIFICATION": 0, "FALSE_CLARIFICATION": 0,
                                      "INFRASTRUCTURE_FAILURE": 0}
    assert {r["reason_verified"] for r in out["rows"] if r["expected"]["outcome"] != "SERVED"} == {True}
    assert sup["constraints"]["operands_match"]["numerator"] == 6 and sup["described_points"]["kinds_match"]["numerator"] == 8
    assert out["latency_median_s"] == "NOT_MEASURED" and out["spent_reported_usd"] == "NOT_MEASURED"   # offline: no cost


def test_c19_constraint_check_sees_a_wrong_kind_a_wrong_operand_and_an_invented_construction():
    gold = _k1("K-A01")["gold_extraction"]
    text = gold["problem_text"]
    assert R.constraint_check(gold, gold, text) == dict.fromkeys(
        ("emitted", "kinds_match", "operands_match", "quotes_verbatim", "no_invented_construction"), True)
    wrong = deepcopy(gold)
    wrong["derived_sections"][0]["constraints"][1]["kind"] = "parallel_to_line"
    assert R.constraint_check(gold, wrong, text)["kinds_match"] is False
    other = deepcopy(gold)
    other["derived_sections"][0]["constraints"][1]["operands"] = ["S", "B", "C"]
    c = R.constraint_check(gold, other, text)
    assert c["kinds_match"] and c["operands_match"] is False
    built = deepcopy(gold)                                    # the model writes a foot the source never states
    built["described_points"] = [{"described_id": "h9", "kind": "orthogonal_projection", "quote": "A", "point": "A",
                                  "plane": ["S", "C", "D"]}]
    assert R.constraint_check(gold, built, text)["no_invented_construction"] is False
    assert R.constraint_check(gold, None, text)["emitted"] is False
    assert R.constraint_check(_k1("K-C01")["gold_extraction"], gold, text) is None       # no constrained plane in gold


@pytest.mark.parametrize("exp,obs,e2e,tech,want", [
    ("SERVED", "SERVED", True, False, "SERVED_CORRECT"),
    ("SERVED", "SERVED", False, False, "SERVED_WRONG"),        # e.g. a dropped goal: answers ≠ expected
    ("SERVED", "REFUSED", False, False, "FALSE_REFUSAL"),
    ("SERVED", "CLARIFY", False, False, "FALSE_CLARIFICATION"),
    ("REFUSED_INCONSISTENT", "REFUSED", True, False, "CORRECT_REFUSAL"),
    ("REFUSED_INCONSISTENT", "REFUSED", False, False, "WRONG_REASON_REFUSAL"),
    ("REFUSED_INCONSISTENT", "SERVED", False, False, "SERVED_WRONG"),
    ("CLARIFY", "CLARIFY", True, False, "CORRECT_CLARIFICATION"),
    ("CLARIFY", "REFUSED", False, False, "WRONG_REASON_REFUSAL"),
    ("REFUSED_UNSUPPORTED", "NOT_RECOVERABLE", None, True, "INFRASTRUCTURE_FAILURE"),   # never a correct refusal
])
def test_c19_hybrid_outcome_taxonomy(exp, obs, e2e, tech, want):
    row = {"expected": {"outcome": exp}, "observed": {"status": obs}, "end_to_end_correct": e2e, "technical_failure": tech}
    assert R.hybrid_outcome(row) == want


@pytest.mark.parametrize("exp,obs,want", [("REFUSED_INCONSISTENT", "REFUSED", "WRONG_REASON_REFUSAL"),
                                          ("CLARIFY", "CLARIFY", "WRONG_REASON_CLARIFICATION")])
def test_c19_review_major1_the_right_status_for_another_reason_is_not_correct(exp, obs, want):
    row = {"expected": {"outcome": exp}, "observed": {"status": obs}, "end_to_end_correct": True,
           "technical_failure": False, "reason_verified": False}
    assert R.hybrid_outcome(row) == want


def test_c19_review_major1_a_model_that_drops_the_constraint_gets_the_same_code_but_not_a_correct_refusal(
        tmp_path, monkeypatch):
    case = _k1("K-B01")
    bad = deepcopy(case["gold_extraction"])
    bad["derived_sections"][0]["constraints"] = [c for c in bad["derived_sections"][0]["constraints"]
                                                 if c["kind"] != "perpendicular_to_plane"]
    out = _k1_live(tmp_path, monkeypatch, Provider(_body(bad)), [case])
    row = out["rows"][0]
    assert row["hybrid_code"] == "PLANE_NOT_UNIQUE" and row["end_to_end_correct"]      # the old, status-only verdict
    assert row["reason_verified"] is False and row["hybrid_outcome"] == "WRONG_REASON_REFUSAL"
    assert row["attribution"] == "LLM_EXTRACTION_DIFFERS_FROM_GOLD"


def test_c19_review_major1_a_clarification_on_another_phrase_is_not_correct(tmp_path, monkeypatch):
    case = _k1("K-E01")
    bad = deepcopy(case["gold_extraction"])
    bad["unresolved"] = [{"unresolved_id": "u1", "kind": "missing_operand", "quote": "SA = 2",
                          "missing_roles": ["dimension"]}]
    out = _k1_live(tmp_path, monkeypatch, Provider(_body(bad)), [case])
    row = out["rows"][0]
    assert row["observed"]["status"] == "CLARIFY" and row["reason_verified"] is False
    assert row["hybrid_outcome"] == "WRONG_REASON_CLARIFICATION"
    good = _k1_live(tmp_path / "g", monkeypatch, Provider(_body(case["gold_extraction"])), [case]) if (
        (tmp_path / "g").mkdir() or True) else None
    assert good["rows"][0]["hybrid_outcome"] == "CORRECT_CLARIFICATION"


def test_c19_review_major2_a_model_that_drops_one_of_two_goals_is_never_served_correct(tmp_path, monkeypatch):
    case = _case("S2-B-P07_shared_intermediate_two_goals")
    bad = deepcopy(case["gold_extraction"])
    bad["math_goals"] = bad["math_goals"][:1]
    out = _live(tmp_path, monkeypatch, Provider(_body(bad)), [case])
    assert out["rows"][0]["hybrid_outcome"] != "SERVED_CORRECT"


def test_c19_an_unanswered_expected_quantity_is_served_wrong(tmp_path, monkeypatch):
    case = _k1("K-C01")
    two = deepcopy(case)                                       # the protocol asks two quantities; the model keeps one
    two["expected"]["oracle"] = {"distance": ["1", "√6/2"]}
    out = _k1_live(tmp_path, monkeypatch, Provider(_body(case["gold_extraction"])), [two])
    assert out["rows"][0]["hybrid_outcome"] == "SERVED_WRONG"
    assert out["score"]["metrics"]["wrong_served_end_to_end"]["numerator"] == 1


def test_c19_mock_live_a_model_that_drops_a_constraint_is_an_extraction_failure_never_a_serve(tmp_path, monkeypatch):
    case = _k1("K-A01")
    bad = deepcopy(case["gold_extraction"])
    bad["derived_sections"][0]["constraints"] = bad["derived_sections"][0]["constraints"][:1]   # "⊥ (SCD)" lost
    out = _k1_live(tmp_path, monkeypatch, Provider(_body(bad)), [case])
    row = out["rows"][0]
    assert row["observed"]["status"] != "SERVED" and row["hybrid_outcome"] == "FALSE_REFUSAL"
    assert row["attribution"] == "LLM_EXTRACTION_DIFFERS_FROM_GOLD" and row["constraint_check"]["kinds_match"] is False
    assert out["http_requests"] == 1 and isinstance(row["usd"], float)


def test_c19_mock_live_a_model_that_calls_the_orthocenter_a_circumcenter_is_never_served(tmp_path, monkeypatch):
    case = _k1("K-C01")
    bad = deepcopy(case["gold_extraction"])
    bad["described_points"][0]["kind"] = "circumcenter"
    out = _k1_live(tmp_path, monkeypatch, Provider(_body(bad)), [case])
    row = out["rows"][0]
    assert row["observed"]["status"] != "SERVED" and row["described_check"]["kinds_match"] is False
    assert row["attribution"] == "LLM_EXTRACTION_DIFFERS_FROM_GOLD"


def test_c19_an_unrun_case_is_not_measured_never_zero(tmp_path, monkeypatch):
    cases = [_k1(c) for c in ("K-A01", "K-A02", "K-A03", "K-A04")]
    out = _k1_live(tmp_path, monkeypatch, Provider(default=400), cases)
    assert out["stop_reason"] == "INFRASTRUCTURE_STREAK" and out["cases_not_measured"] == 1
    assert out["supplementary"]["hybrid_outcomes"]["INFRASTRUCTURE_FAILURE"] == 3
    assert out["supplementary"]["hybrid_outcomes"]["CORRECT_REFUSAL"] == 0


def _h1_cases():
    """One case per H-1 stratum (the K-1 texts reused only to exercise validation; never a benchmark)."""
    src = json.loads(K1.read_text(encoding="utf-8"))["cases"]
    return [dict(src[i % len(src)], id=f"H{i:02d}", stratum=s,
                 problem_text=src[i % len(src)]["problem_text"] + " " * i) | (
        {"gold_extraction": dict(src[i % len(src)]["gold_extraction"],
                                 problem_text=src[i % len(src)]["problem_text"] + " " * i)}
        if src[i % len(src)].get("gold_extraction") else {})
            for i, s in enumerate(R.STUDIES["H-1"][0])]


_ATTESTED = {"author": "X", "independent_of_implementer": True, "independence_attested_by": "OWNER",
             "gold_confirmed_by_author": True}


def test_c19_an_h1_corpus_is_refused_live_unless_the_owner_attests_an_independent_author(tmp_path):
    for authoring, why in ((None, "Owner-attested"),
                           ({"author": "implementer (agent)", "independent_of_implementer": True}, "Owner-attested"),
                           ({**_ATTESTED, "gold_confirmed_by_author": False}, "confirmed by the author"),
                           (_ATTESTED, None)):
        path = tmp_path / f"h1-{why}.json"
        body = {"study": "H-1", "cases": _h1_cases(), **({"authoring": authoring} if authoring else {})}
        path.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
        terms = _terms(path, pilot="H-1", max_requests=13, max_usd=1.0)
        if why is None:
            assert R.check_approval_terms(path.read_bytes(), terms)["pilot"] == "H-1"
        else:
            with pytest.raises(R.LiveRefused, match=why):
                R.check_approval_terms(path.read_bytes(), terms)


@pytest.mark.parametrize("mutate,why", [
    (lambda cs: cs.pop(), "covers every stratum"),                                         # a weak stratum dropped
    (lambda cs: cs[0].pop("gold_extraction"), "author-confirmed gold"),                    # a SERVED case without gold
])
def test_c19_review_major2_an_h1_corpus_needs_every_stratum_and_a_gold_for_every_serve(mutate, why):
    cases = _h1_cases()
    assert cases[0]["expected"]["outcome"] == "SERVED"
    mutate(cases)
    with pytest.raises(R.LiveRefused, match=why):
        R.validate_corpus({"study": "H-1", "authoring": _ATTESTED, "cases": cases})
