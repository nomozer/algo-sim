"""Scorer, dataset protocol and offline replay harness of the Vietnamese NL → TypedFacts V2 evaluation (run
`hybrid-v2-nl-certificates-e2e`). Offline, 0 provider calls. The shipped dataset is DEV_AUTHORED by the implementing
agent: these tests prove the HARNESS (that it detects what it must detect), never extraction quality."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import nl_eval_scoring as SC  # noqa: E402
import run_nl_eval_offline as RUN  # noqa: E402

RUNDIR = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-v2-nl-certificates-e2e"
ITEMS = json.loads((RUNDIR / "inputs/nl_dev_authored.json").read_text(encoding="utf-8"))["items"]
BY_ID = {i["id"]: i for i in ITEMS}


# ── exact values ──────────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("a,b", [("√17", "√17"), ("24/5", "24/5"), ("12√29/5", "12√29/5"), ("cos²=32/41", "32/41"),
                                 ("4", "16/4"), ("2√2", "√8"), ("-√3", "−√3")])
def test_same_value_is_exact_not_textual(a, b):
    assert SC.same_value(a, b) is True


@pytest.mark.parametrize("a,b", [("√17", "√18"), ("24/5", "4.8"), ("√3", "-√3"), ("1/2", "1/3")])
def test_different_or_inexact_values_never_pass(a, b):
    assert SC.same_value(a, b) is not True


def test_float_like_answer_is_ungradable_not_correct():
    assert SC.same_value("4.8", "24/5") is None


# ── outcome classification ────────────────────────────────────────────────────────────────────────────────────────────

SERVE = {"disposition": "SERVE", "values": {"q": "√17"}}
REFUSE = {"disposition": "REFUSE", "category": "INSUFFICIENT", "allowed_codes": ["MISSING_DIMENSION"]}


@pytest.mark.parametrize("exp,route,want", [
    (SERVE, {"status": "SERVED", "answers": {"q": "√17"}}, "CORRECT_SERVED"),
    (SERVE, {"status": "SERVED", "answers": {"q": "√18"}}, "INCORRECT_SERVED"),
    (SERVE, {"status": "SERVED", "answers": {}}, "INCORRECT_SERVED"),
    (SERVE, {"status": "SERVED", "answers": {"q": "4.1"}}, "INCORRECT_SERVED"),
    (SERVE, {"status": "REFUSED", "code": "UNGROUNDED_VALUE"}, "INCORRECT_REFUSED"),
    (SERVE, {"status": "REFUSED", "code": "NO_RECORDED_EXTRACTION"}, "EXTRACTION_FAILURE"),
    (REFUSE, {"status": "SERVED", "answers": {"q": "√17"}}, "INCORRECT_SERVED"),
    (REFUSE, {"status": "REFUSED", "code": "MISSING_DIMENSION"}, "CORRECT_REFUSED"),
    (REFUSE, {"status": "REFUSED", "code": "CONDITIONAL_CLAUSE"}, "CORRECT_REFUSED"),
    (REFUSE, {"status": "REFUSED", "code": "PROVIDER_ERROR"}, "EXTRACTION_FAILURE"),     # never a correct refusal
    (REFUSE, {"status": "REFUSED", "code": "ROUTE_INTERNAL_ERROR"}, "EXTRACTION_FAILURE"),
])
def test_classify_outcome(exp, route, want):
    assert SC.classify_outcome(exp, route)["outcome"] == want


def test_refusal_code_outside_the_allowed_set_is_flagged_not_hidden():
    r = SC.classify_outcome(REFUSE, {"status": "REFUSED", "code": "CONDITIONAL_CLAUSE"})
    assert r["outcome"] == "CORRECT_REFUSED" and r["code_in_allowed"] is False


# ── canonical forms and layer scorers ─────────────────────────────────────────────────────────────────────────────────

GOLD = BY_ID["py-dist-goal-0"]["gold"]["payload"]


def test_canonical_form_ignores_order_primes_and_quotes():
    p = copy.deepcopy(GOLD)
    p["premises"][1]["args"]["plane"] = ["D", "C", "B", "A"]
    p["premises"][1]["args"]["line"] = ["A", "S"]
    s = SC.score_extraction(p, GOLD)
    assert s["facts"] == {"tp": 3, "fp": 0, "fn": 0} and s["entity"]["exact"] and s["goal"]["exact"]
    assert SC.canon({"plane": ["B′", "C"]}) == SC.canon({"plane": ["C", "B'"]})


@pytest.mark.parametrize("mutate,check", [
    (lambda p: p["premises"].pop(), lambda s: s["facts"] == {"tp": 2, "fp": 0, "fn": 1}),
    (lambda p: p["premises"][2]["args"].update(value="4"), lambda s: s["facts"] == {"tp": 2, "fp": 1, "fn": 1}),
    (lambda p: p["math_goals"][0].update(target={"point": "S", "line": ["B", "C"]}), lambda s: s["goal"]["exact"] is False),
    (lambda p: p["math_goals"][0].update(goal_type="angle"), lambda s: s["goal"]["exact"] is False),
    (lambda p: p["premises"][2]["args"].update(segment=["S", "Z"]),
     lambda s: s["entity"]["exact"] is False and s["entity"]["extra"] == ["Z"]),
    (lambda p: p["premises"][2].update(quote="SA = 9."), lambda s: s["provenance"]["ok"] is False),
    (lambda p: p["premises"][2].update(quote="Đáy ABCD là hình vuông cạnh 4."), lambda s: s["provenance"]["ok"] is False),
])
def test_each_layer_detects_its_own_fault(mutate, check):
    p = copy.deepcopy(GOLD)
    mutate(p)
    s = SC.score_extraction(p, GOLD)
    assert check(s), s
    assert all(k in s for k in ("entity", "facts", "goal", "provenance"))   # layers stay separate, nothing is summed


def test_no_extraction_scores_nothing_not_zero_faults():
    s = SC.score_extraction(None, GOLD)
    assert s["facts"]["tp"] == 0 and s["facts"]["fn"] == 3 and not s["provenance"]["ok"] and not s["goal"]["exact"]


# ── dataset protocol ──────────────────────────────────────────────────────────────────────────────────────────────────

def test_shipped_dataset_is_valid_and_labelled_dev_authored():
    assert SC.validate_dataset(ITEMS) == []
    assert {i["split"] for i in ITEMS} == {"DEV_AUTHORED"} and SC.claim_ceiling(ITEMS) == "DEV_AUTHORED_NOT_INDEPENDENT"
    assert all(i["exposure"]["label"] == "EXPOSED" and i["provenance"]["author_kind"] == "SAME_AGENT" for i in ITEMS)
    assert len(SC.dataset_sha256(ITEMS)) == 64


def test_holdout_rules():
    h = copy.deepcopy(ITEMS[:2])
    for i in h:
        i["split"] = "HOLDOUT"
    assert any("HOLDOUT item must be FRESH" in e for e in SC.validate_dataset(h))            # same-agent / exposed
    for i in h:
        i["provenance"]["author_kind"], i["exposure"]["label"] = "BLIND_AGENT", "FRESH"
    assert SC.validate_dataset(h) == []
    assert SC.claim_ceiling(h) == "HOLDOUT_UNREGISTERED_TREAT_AS_DEV"                           # no registered hash
    man = {"dataset_sha256": SC.dataset_sha256(h), "registered_before_tuning": True}
    assert SC.claim_ceiling(h, man) == "INDEPENDENT_HOLDOUT"
    h[0]["problem_text"] += " "                                                                 # any edit voids the registration
    assert SC.claim_ceiling(h, man) == "HOLDOUT_UNREGISTERED_TREAT_AS_DEV"


@pytest.mark.parametrize("mutate,needle", [
    (lambda i: i.update(split="TRAIN"), "split"),
    (lambda i: i["provenance"].pop("author_kind"), "provenance"),
    (lambda i: i["exposure"].pop("label"), "exposure"),
    (lambda i: i["gold"]["expectation"].update(values={}), "exact values"),
    (lambda i: i["gold"]["payload"].update(problem_text="other"), "own problem_text"),
])
def test_validate_dataset_rejects(mutate, needle):
    it = copy.deepcopy(BY_ID["py-dist-goal-0"])
    mutate(it)
    assert any(needle in e for e in SC.validate_dataset([it]))


# ── offline replay: GOLD arm, STRESS arm, stop policy, live refusal ───────────────────────────────────────────────────

@pytest.fixture(scope="module")
def gold_report():
    return SC.run_dataset(ITEMS, SC.gold_extractor, SC.StopPolicy(len(ITEMS), stop_on_incorrect_served=False))


def test_gold_arm_never_serves_a_wrong_answer(gold_report):
    s = gold_report["summary"]
    assert s["outcomes"]["INCORRECT_SERVED"] == 0 and gold_report["provider_calls"] == 0
    assert s["contradiction"] == {"n": 2, "refused_by_gate": 2, "served": 0}
    assert sum(s["outcomes"].values()) == len(ITEMS) == s["n"]


def test_known_wording_gaps_stay_visible(gold_report):
    """Valid wordings the Source Gate still refuses are LISTED, not hidden: this test pins the current gap list, so a
    fix (or a regression) must change it knowingly."""
    gaps = sorted(r["id"] for r in gold_report["rows"] if r["outcome"] == "INCORRECT_REFUSED")
    assert gaps == ["pr-gap-plane-containing-face", "py-gap-notation-d", "py-gap-plane-day-labelled", "py-gap-side-in-parentheses"]


def test_stress_extractions_are_never_served():
    rows = RUN.stress_rows(ITEMS)
    assert rows and all(r["outcome"] == "CORRECT_REFUSED" for r in rows), [(r["id"], r["outcome"]) for r in rows]


def test_wording_metamorphic_values_follow_the_formula_not_the_text(gold_report):
    by = {r["id"]: r for r in gold_report["rows"]}
    ids = [i["id"] for i in ITEMS if i["id"].startswith(("py-rename", "py-base-", "py-perp-", "py-len-", "pr-plane-"))]
    assert ids and all(by[rid]["outcome"] == "CORRECT_SERVED" for rid in ids)


def test_stop_policy():
    p = SC.StopPolicy(2)
    assert p.allow_next()
    p.record({"outcome": "CORRECT_SERVED"})
    p.record({"outcome": "CORRECT_SERVED"})
    assert not p.allow_next() and p.stopped == "BUDGET_EXHAUSTED"
    q = SC.StopPolicy(10)
    q.record({"outcome": "INCORRECT_SERVED"})
    assert not q.allow_next() and q.stopped == "STOP_INCORRECT_SERVED"
    r = SC.StopPolicy(10, max_extraction_failures=1)
    r.record({"outcome": "EXTRACTION_FAILURE"})
    r.record({"outcome": "EXTRACTION_FAILURE"})
    assert r.stopped == "STOP_EXTRACTION_FAILURES"


def test_live_is_refused_and_overwrite_is_refused(tmp_path, capsys):
    assert RUN.main(["x.json", "--out", str(tmp_path / "o.json"), "--live"]) == 3
    assert SC.LIVE_PROVIDER_GO_REQUIRED in capsys.readouterr().out
    (tmp_path / "exists.json").write_text("{}")
    assert RUN.main([str(RUNDIR / "inputs/nl_dev_authored.json"), "--out", str(tmp_path / "exists.json")]) == 2


def test_runner_has_no_provider_transport():
    src = Path(SC.__file__).read_text(encoding="utf-8") + Path(RUN.__file__).read_text(encoding="utf-8")
    for banned in ("httpx", "requests", "live_transport", "GEMINI_API_KEY", "generativelanguage"):
        assert banned not in src
