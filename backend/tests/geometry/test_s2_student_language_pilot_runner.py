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
    # At registry /32 (`r1-live-pilot-gold-replay-r2.jsonl`, `r1-live-pilot-gold-replay-c19-r3.jsonl`) R1-G01/R1-G02
    # refused at Source Gate `(11, 2, 0)`; registry /33 grounds "điểm chính giữa" and "đi qua/nối" -> `(13, 0, 0)`.
    receipt = _rows(CORPUS.parent / "r1-live-pilot-gold-replay-final.jsonl")
    # the receipt hashed the LF bytes it ran on; a fresh checkout under core.autocrlf=true holds CRLF (Full T3 attempt 1)
    import hashlib
    assert receipt[0]["corpus_sha256"] == hashlib.sha256(corpus.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert {r["case_id"]: r["composition_label"] for r in out["rows"]} == {
        r["case_id"]: r["composition_label"] for r in receipt if r["type"] == "row"}
    assert out["supplementary"] == receipt[-1]["supplementary"]
    outcomes = out["supplementary"]["hybrid_outcomes"]
    assert out["score"]["metrics"]["wrong_served_end_to_end"]["numerator"] == 0
    assert (outcomes["SERVED_CORRECT"], outcomes["FALSE_REFUSAL"], outcomes["SERVED_WRONG"]) == (13, 0, 0)


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

    def ran(c, out, terms, *, approval_path=None):
        assert approval_path == approval
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
                                      "REASON_NOT_VERIFIED": 0, "INFRASTRUCTURE_FAILURE": 0}
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
    row = {"expected": {"outcome": exp}, "observed": {"status": obs}, "end_to_end_correct": e2e, "technical_failure": tech,
           "reason_verified": True if exp != "SERVED" else None}
    assert R.hybrid_outcome(row) == want


@pytest.mark.parametrize("exp,obs", [("REFUSED_INCONSISTENT", "REFUSED"), ("CLARIFY", "CLARIFY")])
def test_c19_review_round2_majorC_a_reason_nothing_can_verify_is_never_correct(exp, obs):
    row = {"expected": {"outcome": exp}, "observed": {"status": obs}, "end_to_end_correct": True,
           "technical_failure": False, "reason_verified": None}
    assert R.hybrid_outcome(row) == "REASON_NOT_VERIFIED"


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
    assert row["hybrid_code"] == "PLANE_NOT_UNIQUE" and row["end_to_end_status_only"]   # the old, status-only verdict
    assert row["reason_verified"] is False and row["hybrid_outcome"] == "WRONG_REASON_REFUSAL"
    assert row["attribution"] == "LLM_EXTRACTION_DIFFERS_FROM_GOLD"
    # review round 2 MAJOR-A: every summary rate and label uses the same verdict
    assert row["end_to_end_correct"] is False and row["composition_label"] != "CORRECT_REFUSAL"
    sup = out["supplementary"]
    assert sup["end_to_end_correct"]["numerator"] == 0 and sup["by_stratum"]["K-B"]["numerator"] == 0


@pytest.mark.parametrize("quotes,ok", [
    (["vuông góc với một mặt bên"], True),
    (["góc với một mặt bên"], True),                                 # most of the gold wording, inside its span
    (["một mặt bên"], False),                                        # only half of it: conservative, counted wrong
    (["với"], False),                                                # a function word (review round 2 MAJOR-B)
    (["vuông góc với"], False),                                      # half of it, also the stated "SA vuông góc với …"
    (["bên"], False),
    (["Mặt phẳng (P) đi qua A, B và vuông góc với một mặt bên"], False),  # the whole sentence: far longer
    (["vuông góc với một mặt bên", "SA = 2"], False),                # one relevant entry cannot carry another
])
def test_c19_review_round2_majorB_a_clarification_must_name_the_gold_wording(tmp_path, monkeypatch, quotes, ok):
    case = _k1("K-E01")
    bad = deepcopy(case["gold_extraction"])
    bad["unresolved"] = [{"unresolved_id": f"u{i}", "kind": "ambiguous", "quote": q} for i, q in enumerate(quotes)]
    out = _k1_live(tmp_path, monkeypatch, Provider(_body(bad)), [case])
    row = out["rows"][0]
    assert row["observed"]["status"] == "CLARIFY"
    assert row["reason_verified"] is ok and (row["hybrid_outcome"] == "CORRECT_CLARIFICATION") is ok


def test_c19_review_round2_majorC_a_refusal_without_gold_is_not_verified_and_h1_requires_gold_everywhere(
        tmp_path, monkeypatch):
    case = dict(_k1("K-B01"))
    bad = deepcopy(case["gold_extraction"])
    bad["derived_sections"][0]["constraints"] = bad["derived_sections"][0]["constraints"][:1]
    case.pop("gold_extraction")
    row = _k1_live(tmp_path, monkeypatch, Provider(_body(bad)), [case])["rows"][0]
    assert row["reason_verified"] is None and row["hybrid_outcome"] == "REASON_NOT_VERIFIED"
    assert row["end_to_end_correct"] is False and row["attribution"] == "REASON_NOT_VERIFIED"
    cases = _h1_cases()
    k = next(i for i, c in enumerate(cases) if c["expected"]["outcome"] != "SERVED")
    cases[k].pop("gold_extraction")
    with pytest.raises(R.LiveRefused, match="every H-1 case needs"):
        R.validate_corpus({"study": "H-1", "authoring": _ATTESTED, "cases": cases})


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


# ── C21: EXPLICIT_OWNER_DELEGATED_EXECUTION, paid-project gate, secret hygiene, two-tier global budget ──────────────

_FAKE_AQ_KEY = "AQ." + "Ab8RN6FakeStudioSecretKeyForOfflineTestsOnly12345"


def _delegated_terms(corpus_path, pilot="K-1", max_requests=16, max_usd=1.0, **over):
    ident = R.runtime_identity()
    delegation = {
        "authorization_source": "EXPLICIT_OWNER_INSTRUCTION",
        "directive_id": "CONTINUATION_21_MASTER_DIRECTIVE",
        "authorized_pilots": ["K-1", "S-2", "R-1"],
        "authorized_model": "gemini-2.5-flash",
        "candidate_commit": "15d236eb",
        "global_max_requests": 70,
        "global_max_usd": 4.0,
        "issued_at": "2026-11-02T14:00:00Z",
        "template_path": f"{pilot.lower().replace('-', '')}-owner-approval.template.json",
        "template_git_blob": "a" * 40,
        "paid_project_verification": {
            "verified": True,
            "source": "CLOUD_BILLING_API",
            "project_id": "algosim-paid-test",
            "billing_enabled": True,
        },
    }
    if "delegation" in over and isinstance(over["delegation"], dict):
        delegation = {**delegation, **over.pop("delegation")}
    return {
        "authorization_mode": R.DELEGATED_MODE,
        "owner_decision": R.DELEGATED_DECISION,
        "pilot": pilot,
        "model": ident["model"],
        "paid_project_confirmed": True,
        "max_requests": max_requests,
        "max_usd": max_usd,
        "input_usd_per_million": 0.30,
        "output_usd_per_million": 2.50,
        "corpus_sha256": R.sha256_file(corpus_path),
        "measured_system": ident["measured_system"],
        "runner_sha256": ident["runner_sha256"],
        "paired_harness_sha256": ident["paired_harness_sha256"],
        "scorer_sha256": ident["scorer_sha256"],
        "delegation": delegation,
        **over,
    }


def test_c21_delegated_authorization_accepts_in_scope_pilots_and_refuses_h1_or_forged_terms(tmp_path, monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", _FAKE_AQ_KEY)
    k1 = _write_study(tmp_path / "k1", "K-1", [_k1("K-A01")]) if ((tmp_path / "k1").mkdir() or True) else None
    ap = tmp_path / "k1-delegated.json"
    terms = _delegated_terms(k1, pilot="K-1", max_requests=16, max_usd=1.0)
    ap.write_text(json.dumps(terms, ensure_ascii=False), encoding="utf-8")
    # MAJOR-1: CLI --live (allow_delegated=False) and evaluate(..., global_budget=None) refuse delegated terms
    monkeypatch.setattr(httpx, "post", lambda *a, **k: pytest.fail("delegated bypass sent a request"))
    with pytest.raises(R.LiveRefused, match="delegated-c21"):
        R.authorize_live(k1, ap, trusted_paid_verification=terms["delegation"]["paid_project_verification"])
    with pytest.raises(R.LiveRefused, match="delegated-c21"):
        R.main(["--corpus", str(k1), "--live", "--approval-file", str(ap), "--out", str(tmp_path / "bypass.jsonl")])
    with pytest.raises(R.LiveRefused, match="GlobalBudgetLedger"):
        R.evaluate(k1, tmp_path / "direct.jsonl", terms, sleep=lambda s: None)
    # Forged CLOUD_BILLING_API JSON on disk without live/verified Cloud Billing confirmation is refused even when allow_delegated=True
    with pytest.raises(R.LiveRefused, match="Cloud Billing|PAID_PROJECT_NOT_VERIFIED"):
        R.authorize_live(k1, ap, allow_delegated=True)
    assert R.authorize_live(
        k1, ap, allow_delegated=True, trusted_paid_verification=terms["delegation"]["paid_project_verification"]
    )["pilot"] == "K-1"

    # H-1 is outside EXPLICIT_OWNER_DELEGATED_EXECUTION even with an Owner-attested independent author
    h1 = tmp_path / "h1.json"
    h1.write_text(json.dumps({"study": "H-1", "authoring": _ATTESTED, "cases": _h1_cases()}, ensure_ascii=False),
                  encoding="utf-8")
    with pytest.raises(R.LiveRefused, match="outside EXPLICIT_OWNER_DELEGATED_EXECUTION"):
        R.check_approval_terms(h1.read_bytes(), _delegated_terms(h1, pilot="H-1", max_requests=13, max_usd=1.0))

    # Per-pilot USD cap (S-2 <= $2.0, K-1 <= $1.0, R-1 <= $1.0) and global caps (<= 70 req, <= $4.0) enforced
    s2 = _write(tmp_path, [_case("S2-A-I02_ve")])
    assert R.check_approval_terms(s2.read_bytes(), _delegated_terms(s2, pilot="S-2", max_requests=36, max_usd=2.0))
    with pytest.raises(R.LiveRefused, match="max_usd"):
        R.check_approval_terms(s2.read_bytes(), _delegated_terms(s2, pilot="S-2", max_requests=36, max_usd=2.01))
    with pytest.raises(R.LiveRefused, match="global_max_requests"):
        R.check_approval_terms(k1.read_bytes(), _delegated_terms(k1, delegation={"global_max_requests": 71}))
    with pytest.raises(R.LiveRefused, match="global_max_usd"):
        R.check_approval_terms(k1.read_bytes(), _delegated_terms(k1, delegation={"global_max_usd": 4.01}))
    with pytest.raises(R.LiveRefused, match="paid_project_verification"):
        R.check_approval_terms(k1.read_bytes(), _delegated_terms(
            k1, delegation={"paid_project_verification": {"verified": True, "source": "DOTENV_PRESENT"}}))
    with pytest.raises(R.LiveRefused, match="authorized_pilots"):
        R.check_approval_terms(k1.read_bytes(), _delegated_terms(
            k1, delegation={"authorized_pilots": ["K-1", "H-1"]}))


def test_c21_paid_project_verifier_never_treats_dotenv_as_paid_and_verifies_trustworthy_sources(tmp_path):
    # Neither project/OAuth nor attestation -> PAID_PROJECT_NOT_VERIFIED with zero HTTP calls
    calls = []
    res = R.verify_paid_project(http_get=lambda *a, **k: calls.append(a))
    assert res["verified"] is False and res["stop_reason"] == "PAID_PROJECT_NOT_VERIFIED" and calls == []

    # Cloud Billing API: validates project_id, rejects API keys passed as OAuth tokens, and requires matching projectId + billingEnabled
    def fake_billing_unpaid(url, headers, timeout):
        calls.append((url, headers))
        assert _FAKE_AQ_KEY not in json.dumps(headers)
        return 200, {"projectId": "algosim-paid-01", "billingEnabled": False}

    assert R.verify_paid_project(project_id="bad/id", oauth_token="tok-123456789012",
                                 http_get=lambda *a, **k: pytest.fail("invalid project_id called HTTP"))["verified"] is False
    assert R.verify_paid_project(project_id="algosim-paid-01", oauth_token=_FAKE_AQ_KEY,
                                 http_get=lambda *a, **k: pytest.fail("API key sent to billing HTTP"))["verified"] is False
    unpaid = R.verify_paid_project(project_id="algosim-paid-01", oauth_token="tok-123456789012", http_get=fake_billing_unpaid)
    assert unpaid["verified"] is False and unpaid["stop_reason"] == "PAID_PROJECT_NOT_VERIFIED"
    no_pid = R.verify_paid_project(
        project_id="algosim-paid-01", oauth_token="tok-123456789012",
        http_get=lambda u, h, t: (200, {"billingEnabled": True}),
    )
    assert no_pid["verified"] is False

    paid = R.verify_paid_project(
        project_id="algosim-paid-01", oauth_token="tok-123456789012",
        http_get=lambda u, h, t: (200, {"projectId": "algosim-paid-01", "billingEnabled": True}),
    )
    assert paid["verified"] is True and paid["source"] == "CLOUD_BILLING_API"

    # Separate explicit Owner paid-project attestation file (forbids C21 directive self-reference & trivial quotes; relative path inside repo)
    bad_att = tmp_path / "self-ref.json"
    bad_att.write_text(json.dumps({
        "schema": "owner-paid-project-attestation/1",
        "authorization_source": "EXPLICIT_OWNER_SEPARATE_STATEMENT",
        "statement_ref": "CONTINUATION_21_MASTER_DIRECTIVE",
        "statement_quote": "Project gan voi backend/.env da bat Paid Cloud Billing.",
        "paid_project_confirmed": True,
    }), encoding="utf-8")
    assert R.verify_paid_project(attestation_path=bad_att)["verified"] is False

    att = tmp_path / "paid-attestation.json"
    att.write_text(json.dumps({
        "schema": "owner-paid-project-attestation/1",
        "authorization_source": "EXPLICIT_OWNER_SEPARATE_STATEMENT",
        "statement_ref": "CONTINUATION_22_OWNER_MESSAGE",
        "statement_quote": "Project gan voi backend/.env da bat Paid Cloud Billing.",
        "paid_project_confirmed": True,
    }, ensure_ascii=False), encoding="utf-8")
    by_att = R.verify_paid_project(attestation_path=att, repo_root=tmp_path,
                                   http_get=lambda *a, **k: pytest.fail("unexpected HTTP"))
    assert by_att["verified"] is True and by_att["source"] == "EXPLICIT_OWNER_PAID_ATTESTATION"
    assert by_att["attestation_sha256"] == R.sha256_file(att)
    assert by_att["attestation_path"] == "paid-attestation.json"
    # MINOR-1: standalone ya29. OAuth tokens are redacted even without extra_secrets
    fake_ya29 = "ya29." + "a0AfH6SMB" + "z" * 40
    assert fake_ya29 not in R.redact_secrets(f"gcloud token={fake_ya29}")


def _mini_suite_spec(tmp_path):
    """Builds a miniature 3-pilot Git-tracked template + corpus fixture for K-1, S-2, R-1."""
    import subprocess
    repo = tmp_path / "suite_repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    ident = R.runtime_identity()
    pilots = {}
    for slug, study, case, req_cap, usd_cap in (
        ("k1", "K-1", _k1("K-A01"), 16, 1.0),
        ("s2", "S-2", _case("S2-B-I11_mo_phong_va_tinh_SC"), 36, 2.0),
        ("r1", "R-1", _r1_case(), 18, 1.0),
    ):
        cpath = repo / f"{slug}-corpus.json"
        body = {"cases": [case]} if study == "S-2" else {"study": study, "cases": [case]}
        cpath.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8", newline="\n")
        tpath = repo / f"{slug}-owner-approval.template.json"
        tmpl = {
            "owner_decision": "PENDING_OWNER_DECISION",
            "pilot": study,
            "model": ident["model"],
            "paid_project_confirmed": False,
            "max_requests": req_cap,
            "max_usd": usd_cap,
            "input_usd_per_million": 0.30,
            "output_usd_per_million": 2.50,
            "corpus_sha256": R.sha256_file(cpath),
            "measured_system": ident["measured_system"],
            "runner_sha256": ident["runner_sha256"],
            "paired_harness_sha256": ident["paired_harness_sha256"],
            "scorer_sha256": ident["scorer_sha256"],
        }
        tpath.write_text(json.dumps(tmpl, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        blob = subprocess.run(["git", "hash-object", str(tpath)], cwd=repo, capture_output=True, check=True,
                              text=True).stdout.strip()
        pilots[study] = {"slug": slug, "corpus_path": cpath, "template_path": tpath, "expected_template_blob": blob,
                         "max_requests": req_cap, "max_usd": usd_cap}
    return repo, pilots


def test_c21_suite_halts_before_first_request_when_paid_not_verified_and_redacts_aq_key(tmp_path, monkeypatch):
    repo, pilots = _mini_suite_spec(tmp_path)
    dotenv = tmp_path / "root.env"
    dotenv.write_text(f"# root env\nGEMINI_API_KEY={_FAKE_AQ_KEY}\n", encoding="utf-8")
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(httpx, "post", lambda *a, **k: pytest.fail("blocked run sent a Gemini request"))
    out_dir = tmp_path / "c21_blocked"
    receipt = R.run_delegated_c21_suite(
        out_dir=out_dir, dotenv_path=dotenv, pilot_specs=pilots, git_cwd=repo, sleep=lambda s: None,
    )
    assert receipt["status"] == "BLOCKED_PREFLIGHT"
    assert receipt["stop_reason"] == "PAID_PROJECT_NOT_VERIFIED"
    assert receipt["total_http_requests"] == 0 and receipt["total_spent_upper_usd"] == 0.0
    assert receipt["approvals_created"] == []
    assert "ALLOW_LIVE_AI" not in R.os.environ
    for f in out_dir.rglob("*"):
        if f.is_file():
            text = f.read_text(encoding="utf-8")
            assert _FAKE_AQ_KEY not in text and "AQ." not in text
            assert "APPROVED" + "_BY_USER" not in text


def test_c21_suite_executes_k1_s2_r1_automatically_and_enforces_global_caps_and_model_check(tmp_path, monkeypatch):
    repo, pilots = _mini_suite_spec(tmp_path)
    dotenv = tmp_path / "root.env"
    dotenv.write_text(f"GEMINI_API_KEY={_FAKE_AQ_KEY}\n", encoding="utf-8")
    att = tmp_path / "paid.json"
    att.write_text(json.dumps({
        "schema": "owner-paid-project-attestation/1",
        "authorization_source": "EXPLICIT_OWNER_SEPARATE_STATEMENT",
        "statement_ref": "OWNER_PAID_CONFIRMATION_TEST",
        "statement_quote": "Confirmed paid Cloud Billing enabled.",
        "paid_project_confirmed": True,
    }), encoding="utf-8")
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    # 1. Full K-1 -> S-2 -> R-1 automatic execution with mock Gemini returning gold extractions
    golds = [_k1("K-A01")["gold_extraction"], _case("S2-B-I11_mo_phong_va_tinh_SC")["gold_extraction"],
             _r1_case()["gold_extraction"]]
    seq = iter(golds)
    calls = []

    def mock_post(url, **kwargs):
        calls.append(url)
        assert url.endswith("/models/gemini-2.5-flash:generateContent")
        return Provider(_body(next(seq)))(url, **kwargs)

    monkeypatch.setattr(httpx, "post", mock_post)
    out_ok = tmp_path / "c21_ok"
    res = R.run_delegated_c21_suite(
        out_dir=out_ok, dotenv_path=dotenv, paid_attestation_path=att, pilot_specs=pilots, git_cwd=repo,
        sleep=lambda s: None,
    )
    assert res["status"] == "COMPLETE" and res["stop_reason"] is None
    assert res["total_http_requests"] == 3 and len(calls) == 3
    assert [p["study"] for p in res["pilots"]] == ["K-1", "S-2", "R-1"]
    assert all(p["completed"] for p in res["pilots"])
    assert len(res["approvals_created"]) == 3
    assert "ALLOW_LIVE_AI" not in R.os.environ and "GEMINI_API_KEY" not in R.os.environ
    for f in out_ok.rglob("*"):
        if f.is_file():
            txt = f.read_text(encoding="utf-8")
            assert _FAKE_AQ_KEY not in txt and "APPROVED" + "_BY_USER" not in txt

    # MAJOR-2a: Re-running against ANY out_dir (same or new!) is refused by the shared campaign ledger in repo
    with pytest.raises(R.LiveRefused, match="global budget ledger"):
        R.run_delegated_c21_suite(out_dir=out_ok, dotenv_path=dotenv, paid_attestation_path=att, pilot_specs=pilots,
                                  git_cwd=repo, sleep=lambda s: None)
    with pytest.raises(R.LiveRefused, match="global budget ledger"):
        R.run_delegated_c21_suite(out_dir=tmp_path / "c21_other_outdir", dotenv_path=dotenv, paid_attestation_path=att,
                                  pilot_specs=pilots, git_cwd=repo, sleep=lambda s: None)

    # 2. Global request cap (< sum of per-pilot caps) halts before the 3rd request (fresh test ledger_dir)
    seq2 = iter(golds)
    calls2 = []
    monkeypatch.setattr(httpx, "post", lambda url, **kw: (calls2.append(url), Provider(_body(next(seq2)))(url, **kw))[1])
    res_cap = R.run_delegated_c21_suite(
        out_dir=tmp_path / "c21_reqcap", ledger_dir=tmp_path / "ledger_reqcap", dotenv_path=dotenv,
        paid_attestation_path=att, pilot_specs=pilots, git_cwd=repo, global_max_requests=2, sleep=lambda s: None,
    )
    assert len(calls2) == 2 and res_cap["total_http_requests"] == 2
    assert res_cap["stop_reason"] == "GLOBAL_REQUEST_CAP"

    # 3. PROVIDER_MODEL_UNAVAILABLE (HTTP 404 on K-1 request 1) halts immediately after 1 request, skipping S-2 & R-1
    calls3 = []
    monkeypatch.setattr(httpx, "post", lambda url, **kw: (calls3.append(url), Provider(default=404)(url, **kw))[1])
    res_404 = R.run_delegated_c21_suite(
        out_dir=tmp_path / "c21_404", ledger_dir=tmp_path / "ledger_404", dotenv_path=dotenv,
        paid_attestation_path=att, pilot_specs=pilots, git_cwd=repo, sleep=lambda s: None,
    )
    assert len(calls3) == 1 and res_404["total_http_requests"] == 1
    assert res_404["stop_reason"] == "PROVIDER_MODEL_UNAVAILABLE"
    assert [p["study"] for p in res_404["pilots"]] == ["K-1"]

    # 4. Global USD ceiling (< sum of per-pilot caps) blocks before exceeding global_max_usd across pilots
    tiny_pilots = {k: {**v, "max_requests": 1, "max_usd": 0.25} for k, v in pilots.items()}
    for sp in tiny_pilots.values():
        tpath = Path(sp["template_path"])
        t = json.loads(tpath.read_text(encoding="utf-8"))
        t.update(max_requests=1, max_usd=0.25)
        tpath.write_text(json.dumps(t, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        import subprocess
        sp["expected_template_blob"] = subprocess.run(
            ["git", "hash-object", str(tpath)], cwd=repo, capture_output=True, check=True, text=True
        ).stdout.strip()
    calls4 = []
    # Return empty usageMetadata so each sent request is charged at its full provable ceiling (~0.025 USD)
    no_usage_seq = iter([{** _body(g), "usageMetadata": {}} for g in golds])
    monkeypatch.setattr(httpx, "post",
                        lambda url, **kw: (calls4.append(url), Provider(next(no_usage_seq))(url, **kw))[1])
    res_usd = R.run_delegated_c21_suite(
        out_dir=tmp_path / "c21_usdcap", ledger_dir=tmp_path / "ledger_usd1", dotenv_path=dotenv,
        paid_attestation_path=att, pilot_specs=tiny_pilots, git_cwd=repo, global_max_usd=0.26, sleep=lambda s: None,
    )
    assert res_usd["total_spent_upper_usd"] <= 0.26
    calls5 = []
    no_usage_seq2 = iter([{**_body(g), "usageMetadata": {}} for g in golds])
    monkeypatch.setattr(httpx, "post",
                        lambda url, **kw: (calls5.append(url), Provider(next(no_usage_seq2))(url, **kw))[1])
    one_ceil = res_usd["pilots"][0]["spent_upper_usd"]
    tight_pilots = {k: {**v, "max_usd": one_ceil * 1.2} for k, v in tiny_pilots.items()}
    for sp in tight_pilots.values():
        tpath = Path(sp["template_path"])
        t = json.loads(tpath.read_text(encoding="utf-8"))
        t.update(max_usd=one_ceil * 1.2)
        tpath.write_text(json.dumps(t, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        import subprocess
        sp["expected_template_blob"] = subprocess.run(
            ["git", "hash-object", str(tpath)], cwd=repo, capture_output=True, check=True, text=True
        ).stdout.strip()
    res_tight = R.run_delegated_c21_suite(
        out_dir=tmp_path / "c21_tight_usd", ledger_dir=tmp_path / "ledger_usd2", dotenv_path=dotenv,
        paid_attestation_path=att, pilot_specs=tight_pilots, git_cwd=repo, global_max_usd=one_ceil * 2.5,
        sleep=lambda s: None,
    )
    assert len(calls5) == 2 and res_tight["total_http_requests"] == 2
    assert res_tight["stop_reason"] == "GLOBAL_COST_CEILING"
    assert res_tight["total_spent_upper_usd"] <= one_ceil * 2.5


def test_c21_review_r1_interrupt_persists_ledger_and_receipt_and_100pct_failure_is_not_verified_live(tmp_path, monkeypatch):
    repo, pilots = _mini_suite_spec(tmp_path)
    dotenv = tmp_path / "root.env"
    dotenv.write_text(f"GEMINI_API_KEY={_FAKE_AQ_KEY}\n", encoding="utf-8")
    att = repo / "paid.json"
    att.write_text(json.dumps({
        "schema": "owner-paid-project-attestation/1",
        "authorization_source": "EXPLICIT_OWNER_SEPARATE_STATEMENT",
        "statement_ref": "OWNER_PAID_CONFIRMATION_R2",
        "statement_quote": "Confirmed paid Cloud Billing enabled for AlgoSim.",
        "paid_project_confirmed": True,
    }), encoding="utf-8")
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    # MAJOR-2b: KeyboardInterrupt during S-2 after K-1 spent 1 request still records ledger spend and writes receipt
    n = [0]

    def interrupt_on_second(url, **kw):
        n[0] += 1
        if n[0] == 2:
            raise KeyboardInterrupt
        return Provider(_body(_k1("K-A01")["gold_extraction"]))(url, **kw)

    monkeypatch.setattr(httpx, "post", interrupt_on_second)
    int_out = tmp_path / "c21_interrupted"
    int_led = tmp_path / "ledger_int"
    with pytest.raises(KeyboardInterrupt):
        R.run_delegated_c21_suite(out_dir=int_out, ledger_dir=int_led, dotenv_path=dotenv, paid_attestation_path=att,
                                  pilot_specs=pilots, git_cwd=repo, sleep=lambda s: None)
    assert not (int_led / "c21-global-budget.lock").exists()
    led_data = json.loads((int_led / "c21-global-budget-ledger.json").read_text(encoding="utf-8"))
    rec_data = json.loads((int_out / "c21-delegated-execution-receipt.json").read_text(encoding="utf-8"))
    assert led_data["requests_used"] == 2 and led_data["spent_upper_usd"] > 0.0
    assert rec_data["status"] == "INTERRUPTED" and rec_data["total_http_requests"] == 2

    # Atomic acquire() TOCTOU race guard if lock appears between __init__ and acquire()
    race_dir = tmp_path / "ledger_race"
    race_ledger = R.GlobalBudgetLedger(race_dir)
    (race_dir / "c21-global-budget.lock").write_text("{}", encoding="utf-8")
    with pytest.raises(R.LiveRefused, match="lock already held"):
        race_ledger.acquire()

    # MAJOR-4: 100%-failed HTTP 400 (generic bad request, not model-not-found) reports model_availability == UNKNOWN
    monkeypatch.setattr(httpx, "post", Provider(default=400))
    fail_res = R.run_delegated_c21_suite(
        out_dir=tmp_path / "c21_all_fail", ledger_dir=tmp_path / "ledger_fail", dotenv_path=dotenv,
        paid_attestation_path=att, pilot_specs=pilots, git_cwd=repo, sleep=lambda s: None,
    )
    assert fail_res["model_availability"] == "UNKNOWN"

    # MINOR-4: Mutating template max_usd or owner_decision is caught at preflight before paid_check
    bad_pilots = deepcopy(pilots)
    kt = Path(bad_pilots["K-1"]["template_path"])
    t_obj = json.loads(kt.read_text(encoding="utf-8"))
    t_obj["owner_decision"] = "SOMETHING_ELSE"
    kt.write_text(json.dumps(t_obj, indent=1) + "\n", encoding="utf-8", newline="\n")
    bad_pilots["K-1"].pop("expected_template_blob", None)
    with pytest.raises(R.LiveRefused, match="PENDING_OWNER_DECISION"):
        R.run_delegated_c21_suite(out_dir=tmp_path / "c21_bad_tmpl", dotenv_path=dotenv, pilot_specs=bad_pilots,
                                  git_cwd=repo, sleep=lambda s: None)


def test_c21_malformed_usage_without_prompt_tokens_is_unknown_never_zero(tmp_path, monkeypatch):
    case = _case("S2-A-I02_ve")
    body = _body(case["gold_extraction"])
    body["usageMetadata"] = {"modelVersion": "gemini-2.5-flash"}   # non-empty dict, 0 prompt tokens -> UNKNOWN, not 0.0
    out = _live(tmp_path, monkeypatch, Provider(body), [case])
    row = out["rows"][0]
    assert row["usd"] == "UNKNOWN" and out["spent_reported_usd"] == "UNKNOWN"
    assert isinstance(row["usd_upper"], float) and row["usd_upper"] > 0.0

    # Missing output tokens on a candidate-bearing response also stays UNKNOWN and charges full ceiling
    body2 = _body(case["gold_extraction"])
    body2["usageMetadata"] = {"promptTokenCount": 9000}
    out2 = _live(tmp_path / "m2", monkeypatch, Provider(body2), [case]) if ((tmp_path / "m2").mkdir() or True) else None
    assert out2["rows"][0]["usd"] == "UNKNOWN" and out2["spent_reported_usd"] == "UNKNOWN"

    # MAJOR-3: Partial transient retry (503 without usage -> 200 with usage) sends 2 HTTP requests while only 1 has usage;
    # reported USD must be UNKNOWN (never pricing the first attempt at 0.0), while usd_upper includes both attempts.
    ok_body = _body(case["gold_extraction"])
    out3 = _live(tmp_path / "m3", monkeypatch, Provider(503, ok_body), [case]) if ((tmp_path / "m3").mkdir() or True) else None
    r3 = out3["rows"][0]
    assert r3["http_requests"] == 2 and r3["usd"] == "UNKNOWN" and out3["spent_reported_usd"] == "UNKNOWN"
    single_usd = R.P.usd(
        {"hybrid_extraction": {"prompt_tokens": 9000, "candidates_tokens": 700, "thoughts_tokens": 0, "calls": 1}},
        _terms(_write(tmp_path / "m3c", [case])) if ((tmp_path / "m3c").mkdir() or True) else None,
    )
    assert r3["usd_upper"] > single_usd


def test_c21_registered_approval_templates_bind_current_runtime_identity_and_stale_runner_is_refused():
    ident = R.runtime_identity()
    specs = R.default_c21_pilot_specs()
    for study, sp in specs.items():
        tmpl = json.loads(Path(sp["template_path"]).read_text(encoding="utf-8"))
        assert tmpl["owner_decision"] == "PENDING_OWNER_DECISION" and tmpl["paid_project_confirmed"] is False
        assert tmpl["pilot"] == study and tmpl["model"] == "gemini-2.5-flash"
        assert tmpl["max_requests"] == sp["max_requests"] and tmpl["max_usd"] == sp["max_usd"]
        cbytes = Path(sp["corpus_path"]).read_bytes().replace(b"\r\n", b"\n")
        assert tmpl["corpus_sha256"] in (R.sha256_file(Path(sp["corpus_path"])),
                                         R.hashlib.sha256(cbytes).hexdigest())
        for k in ("measured_system", "runner_sha256", "paired_harness_sha256", "scorer_sha256"):
            assert tmpl[k] == ident[k], f"{study} template {k} drifted from runtime_identity"
        stale = {k: v for k, v in tmpl.items() if k != "owner_decision"} | {
            "paid_project_confirmed": True,
            "runner_sha256": "e3d3b2ec063c4b9332ae46bbfe7afc0cc81a362033f95a5d84a633276880ea4a",
        }
        with pytest.raises(R.LiveRefused, match="runner_sha256"):
            R.check_approval_terms(cbytes, stale)


def test_sha256_file_and_approval_terms_are_invariant_under_windows_crlf_checkout(tmp_path):
    lf_py = tmp_path / "runner_lf.py"
    crlf_py = tmp_path / "runner_crlf.py"
    lf_py.write_bytes(b"def f():\n    return 1\n")
    crlf_py.write_bytes(b"def f():\r\n    return 1\r\n")
    assert R.sha256_file(lf_py) == R.sha256_file(crlf_py)
    assert R.P.sha256_file(lf_py) == R.P.sha256_file(crlf_py)

    specs = R.default_c21_pilot_specs()
    k1_corpus_lf = Path(specs["K-1"]["corpus_path"]).read_bytes().replace(b"\r\n", b"\n")
    k1_corpus_crlf = k1_corpus_lf.replace(b"\n", b"\r\n")
    k1_tmpl = json.loads(Path(specs["K-1"]["template_path"]).read_text(encoding="utf-8"))
    k1_approved = {k: v for k, v in k1_tmpl.items() if k != "owner_decision"} | {"paid_project_confirmed": True}
    assert R.check_approval_terms(k1_corpus_crlf, k1_approved)["pilot"] == "K-1"
