# -*- coding: utf-8 -*-
"""Paired LLM_ONLY vs Hybrid harness (`scripts/run_paired_route_evaluation.py`): scoring, statistics and the live gate.

All offline. Dry runs read recorded arm outputs. The live path runs against a MOCK provider (`httpx.post` /
`httpx.AsyncClient.post` replaced; the conftest transport guard still blocks the real network underneath) with approved
TERMS passed in memory — automation never writes an approval value (AGENTS.md). A mock run is never live evidence.
"""
from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import httpx
import pytest

from tests.geometry.test_typed_fact_next_v2_distance_bridge import _prism

_spec = importlib.util.spec_from_file_location(
    "run_paired_route_evaluation", Path(__file__).resolve().parents[1] / "scripts/run_paired_route_evaluation.py")
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)

SERVED = _prism()                                      # d(A', (ABC)) = 12


def _quantity(producer, exact, group=("target",)):
    return {"type": "quantity", "display_group": list(group), "producer": producer, "exact": exact}


def _ok(*objects):
    return {"status": "ok", "scene3d": {"objects": list(objects)}}


def _rational(v):
    return {"kind": "rational", "value": v}


def _write(tmp_path, cases, name="corpus.json"):
    path = tmp_path / name
    path.write_text(json.dumps({"cases": cases}, ensure_ascii=False), encoding="utf-8")
    return path


def _impossible():
    """Grounded in its own text but geometrically impossible (right angle at A, AB = 6, AC = 8 ⇒ BC = 10, not 11)."""
    p = deepcopy(SERVED)
    p["problem_text"] = p["problem_text"].replace("AA' = 12.", "AA' = 12. BC = 11.")
    p["premises"].append({"kind": "segment_length", "args": {"segment": ["B", "C"], "value": "11"}, "quote": "BC = 11."})
    return p


def _corpus(tmp_path):
    impossible = _impossible()
    return _write(tmp_path, [
        {"id": "C1", "problem_text": SERVED["problem_text"], "expect": "SERVE", "oracle": {"distance": ["12"]},
         "dry_run": {"hybrid_extraction": SERVED, "llm_only_envelope": _ok(_quantity("measure.distance", _rational("12")))}},
        {"id": "C2", "problem_text": SERVED["problem_text"] + " Vẽ hình.", "expect": "SERVE", "oracle": {"distance": ["12"]},
         "dry_run": {"hybrid_extraction": None,                                 # Hybrid: nothing extracted → refusal
                     "llm_only_envelope": _ok(_quantity("measure.distance", _rational("13")))}},
        {"id": "C3", "problem_text": impossible["problem_text"], "expect": "REFUSE", "refusal_class": "CONTRADICTORY_DATA",
         "dry_run": {"hybrid_extraction": impossible,
                     "llm_only_envelope": {"status": "unsupported", "failure_category": "geometry_generation_failed"}}},
    ])


def _terms(corpus_path, **over):
    ident = E.runtime_identity()
    return {"corpus_sha256": E.sha256_file(corpus_path), "max_requests": 40, "max_usd": 7.0, "model": ident["model"],
            "measured_system": ident["measured_system"], "harness_sha256": ident["harness_sha256"],
            "input_usd_per_million": 0.30, "output_usd_per_million": 2.50,
            "llm_only_output_reservation_tokens": 65536, "corpus_author": "", "authoring_independence": "NOT_ESTABLISHED",
            "evaluator_independence": "NOT_ESTABLISHED", **over}


def _rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# ── scoring (B1, B3) and statistics ──────────────────────────────────────────────────────────────────────────────────

def test_scorer_compares_exact_numbers_with_pi_and_never_by_names():
    case = {"expect": "SERVE", "oracle": {"volume": ["36π"]}}
    pi36 = {"kind": "radical", "coefficient": "36", "radicand": 1, "pi": 1}
    assert E.score(case, _ok(_quantity("measure.volume", pi36)))["served_correct"] is True
    assert E.score(case, _ok(_quantity("measure.volume", _rational("36"))))["wrong_served"] is True   # π is not dropped
    case = {"expect": "SERVE", "oracle": {"distance": ["2√6/3"], "angle_cos_sq": ["1/2"]}}
    env = _ok(_quantity("measure.distance", {"kind": "radical", "coefficient": "2/3", "radicand": 6}),
              _quantity("measure.angle_cos_sq", _rational("1/2")),
              _quantity("measure.volume", _rational("5"), group=("given",)))                     # not a target
    assert E.score(case, env)["served_correct"] is True


def test_ratio_and_residual_producers_and_the_pre_registered_extra_value_rule():
    case = {"expect": "SERVE", "oracle": {"volume_ratio": ["1/24"], "residual_volume": ["1/3"]}}
    env = _ok(_quantity("assign.volume_ratio", _rational("1/24")), _quantity("assign.residual_volume", _rational("1/3")),
              _quantity("measure.volume", _rational("1/24")), _quantity("measure.volume", _rational("1/24")))
    s = E.score(case, env)
    assert s["served_correct"] and s["unverified_extra_targets"] == {"volume": ["1/24", "1/24"]}   # other kind: reported
    noisy = _ok(*env["scene3d"]["objects"], _quantity("assign.volume_ratio", _rational("1/2")))
    s = E.score(case, noisy)
    assert s["wrong_served"] and s["served_correct_lenient"] and s["extra_same_kind_values"] == {"volume_ratio": ["1/2"]}
    with pytest.raises(Exception):                                            # an unreadable exact form is never guessed
        E.score({"expect": "SERVE", "oracle": {"distance": ["1"]}},
                _ok(_quantity("measure.distance", {"kind": "mystery", "value": "1"})))


def test_a_wrong_value_the_learner_sees_is_never_correct():
    """Review round 2, N2: oracle 12, shown 12 and 13 ⇒ wrong-served under the primary rule."""
    case = {"expect": "SERVE", "oracle": {"distance": ["12"]}}
    s = E.score(case, _ok(_quantity("measure.distance", _rational("12")), _quantity("measure.distance", _rational("13"))))
    assert s["wrong_served"] and not s["served_correct"] and s["served_correct_lenient"]


def test_decimal_oracles_are_refused():
    for bad in ("1.4142", 0.1, "1,5", "1e3"):
        with pytest.raises(E.LiveRefused):
            E.parse_oracle(bad)
    assert str(E.parse_oracle("√2")) == "√2"


def test_proof_requests_are_out_of_scope_and_not_simulation_suitable_is_its_own_class():
    """Review round 2, N1: LLM_ONLY builds the figure for a proof request by design, so a proof request is not an
    expected refusal; a `not_simulation_suitable` refusal is not `OUT_OF_DOMAIN`."""
    assert "PROOF_REQUEST" not in E.REFUSAL_CLASSES
    assert E.refusal_class("LLM_ONLY", {"failure_category": "not_simulation_suitable"}, None) == "NOT_SIMULATION_SUITABLE"
    with pytest.raises(E.LiveRefused):
        E.validate_corpus({"cases": [{"id": "p", "problem_text": "Chứng minh BD vuông góc SC.", "expect": "REFUSE",
                                      "refusal_class": "PROOF_REQUEST"}]})


def test_refusal_classes_are_pre_registered_and_unstated_reasons_are_unspecific():
    assert E.refusal_class("HYBRID", {"status": "unsupported", "failure_category": "out_of_scope"}, None) == "OUT_OF_DOMAIN"
    assert E.refusal_class("HYBRID", {"status": "unsupported"}, "INCONSISTENT_FACTS") == "CONTRADICTORY_DATA"
    assert E.refusal_class("LLM_ONLY", {"status": "unsupported", "failure_category": "out_of_scope"}, None) == "OUT_OF_DOMAIN"
    assert E.refusal_class("LLM_ONLY", {"status": "unsupported",
                                        "failure_category": "geometry_generation_failed"}, "x") == "UNSPECIFIC"
    assert "CURVED" not in " ".join(E.REFUSAL_CLASSES)                        # B2: LLM_ONLY serves curved solids


def test_dry_run_scores_both_arms_pairs_them_and_never_touches_a_provider(tmp_path, monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: pytest.fail("dry run sent a provider request"))
    out = E.evaluate(_corpus(tmp_path), tmp_path / "rows.jsonl", None)
    assert out["measurement_class"] == "OFFLINE_DETERMINISTIC_FIXTURE_TEST" and out["http_requests"] == 0
    rows = {(r["case_id"], r["arm"]): r for r in out["rows"]}
    assert rows["C1", "HYBRID"]["served_correct"] and rows["C1", "LLM_ONLY"]["served_correct"]
    assert rows["C2", "HYBRID"]["false_refusal"] and rows["C2", "LLM_ONLY"]["wrong_served"]
    assert rows["C3", "HYBRID"]["refusal_code"] == "INCONSISTENT_FACTS" and rows["C3", "HYBRID"]["refusal_reason_correct"]
    assert rows["C3", "LLM_ONLY"]["refusal_class"] == "UNSPECIFIC" and not rows["C3", "LLM_ONLY"]["refusal_reason_correct"]
    assert rows["C1", "HYBRID"]["source_references"] and rows["C1", "HYBRID"]["source_grounding"] == "VERIFIED"
    s = out["summary"]
    assert (s["HYBRID"]["served_correct"], s["HYBRID"]["wrong_served"], s["HYBRID"]["false_refusal"]) == (1, 0, 1)
    assert (s["LLM_ONLY"]["served_correct"], s["LLM_ONLY"]["wrong_served"]) == (1, 1)
    assert s["paired"]["served_correct_mcnemar_p"] == 1.0 and s["paired"]["wrong_served_only_LLM_ONLY"] == 1
    assert s["HYBRID"]["usd_total"] == "UNKNOWN"                              # no usage ⇒ UNKNOWN, not 0
    written = _rows(tmp_path / "rows.jsonl")                                   # M1: streamed JSONL, header … summary
    assert [w["type"] for w in written] == ["header"] + ["row"] * 6 + ["summary"]
    assert out["completed"] is True and written[0]["runtime_identity"]["cache_version"] == "131"


def test_hybrid_arm_passes_the_production_domain_gate_first(tmp_path):
    cases = [{"id": "D1", "problem_text": "Viết chương trình Python in dãy Fibonacci tới số thứ mười.", "expect": "REFUSE",
              "refusal_class": "OUT_OF_DOMAIN",
              "dry_run": {"hybrid_extraction": None, "llm_only_envelope": {"status": "unsupported",
                                                                           "failure_category": "out_of_scope"}}}]
    out = E.evaluate(_write(tmp_path, cases), tmp_path / "rows.jsonl", None)
    assert all(r["refusal_reason_correct"] and not r["technical_failure"] for r in out["rows"])


def test_arm_order_is_seeded_and_varies():
    orders = {E.arm_order(f"case-{i}") for i in range(40)}
    assert orders == {("HYBRID", "LLM_ONLY"), ("LLM_ONLY", "HYBRID")}
    assert E.arm_order("case-7") == E.arm_order("case-7")


def test_statistics():
    lo, hi = E.wilson(9, 10)
    assert 0.59 < lo < 0.60 and 0.98 < hi < 0.99
    assert E.wilson(0, 0) is None
    assert E.mcnemar_exact(0, 6) == pytest.approx(2 / 64) and E.mcnemar_exact(3, 3) == 1.0


# ── §7 acceptance as code (amendment A1: observed wrong-served, not an interval against an observed rate) ─────────────

def _composition():
    classes = ["SERVE"] * 45 + ["OUT_OF_DOMAIN", "CONTRADICTORY_DATA", "MISSING_DATA"] * 5
    return {"cases": [{"id": f"K{i:02d}", "expect": "SERVE" if c == "SERVE" else "REFUSE",
                       **({} if c == "SERVE" else {"refusal_class": c})} for i, c in enumerate(classes)]}


def _arm_rows(corpus, arm, wrong=(), not_correct=(), technical=(), latency=1.0, usd=0.01, reason_ok=True):
    """Synthetic scored rows: every expected-serve case served correct and every negative refused, except as listed."""
    rows = []
    for c in corpus["cases"]:
        pos, cid = c["expect"] == "SERVE", c["id"]
        tech, bad = cid in technical, cid in wrong
        correct = pos and not bad and not tech and cid not in not_correct
        served = correct or bad
        rows.append({"case_id": cid, "arm": arm, "expect": c["expect"], "served": served, "served_correct": correct,
                     "served_correct_lenient": correct, "wrong_served": bad, "technical_failure": tech,
                     "false_refusal": pos and not served and not tech,
                     "refusal_reason_correct": not pos and not served and not tech and reason_ok,
                     "repair_attempts": 0, "latency_s": latency, "usd": usd, "usd_upper": usd, "outcome": "SCORED"})
    return rows


_INDEPENDENT = {"corpus_author": "named by the Owner", "authoring_independence": "ESTABLISHED",
                "evaluator_independence": "ESTABLISHED"}


def _verdict(corpus, hybrid_rows, llm_rows, approval=_INDEPENDENT, **record):
    rec = {"completed": True, "stop_reason": None, "stopped_arms": {}, **record,
           "summary": E.summarize(hybrid_rows + llm_rows)}
    return E.acceptance(corpus, rec, approval)


def test_acceptance_zero_wrong_in_both_arms_is_go_and_the_interval_is_only_reported():
    """The pre-amendment rule (Wilson upper of Hybrid ≤ observed LLM_ONLY rate) is NO-GO here: 6.02 % > 0 %."""
    k = _composition()
    out = _verdict(k, _arm_rows(k, "HYBRID"), _arm_rows(k, "LLM_ONLY"))
    assert out["verdict"] == "HYBRID_CUTOVER_GO" and out["failed"] == []
    lo, hi = out["uncertainty"]["HYBRID_wrong_served_ci95"]
    assert lo == 0.0 and hi == pytest.approx(0.0602, abs=5e-4)          # 0/60 is not a zero production error rate
    assert hi > 0.0                                                      # the old comparison would have failed


def test_acceptance_wrong_served_cases():
    k = _composition()
    one_llm = _verdict(k, _arm_rows(k, "HYBRID"), _arm_rows(k, "LLM_ONLY", wrong={"K00"}))
    many_llm = _verdict(k, _arm_rows(k, "HYBRID"), _arm_rows(k, "LLM_ONLY", wrong={f"K{i:02d}" for i in range(10)}))
    one_hybrid = _verdict(k, _arm_rows(k, "HYBRID", wrong={"K00"}), _arm_rows(k, "LLM_ONLY"))
    assert one_llm["verdict"] == many_llm["verdict"] == "HYBRID_CUTOVER_GO"
    assert one_hybrid["verdict"] == "HYBRID_CUTOVER_NO_GO"
    assert {"1_hybrid_zero_wrong_served", "1_no_excess_wrong_served"} <= set(one_hybrid["failed"])
    both = _verdict(k, _arm_rows(k, "HYBRID", wrong={"K00"}), _arm_rows(k, "LLM_ONLY", wrong={"K00", "K01"}))
    assert "1_hybrid_zero_wrong_served" in both["failed"]                # fewer than the control is still not zero


def test_acceptance_an_incomplete_or_unequal_evaluation_is_never_go():
    k = _composition()
    h, l = _arm_rows(k, "HYBRID"), _arm_rows(k, "LLM_ONLY")
    stopped = _verdict(k, h[:30], l, completed=False, stop_reason="USD_80_PERCENT")
    unequal = _verdict(k, h[:59], l)                                     # a row missing, even if "completed"
    for out in (stopped, unequal):
        assert out["verdict"] == "HYBRID_CUTOVER_NO_GO" and "0_complete_paired_evaluation" in out["failed"]
        assert out["criteria"]["2_served_correct_not_worse"] is None     # not evaluated, never assumed
    early = _verdict(k, _arm_rows(k, "HYBRID", wrong={"K45"})[:46], l, completed=False,
                     stopped_arms={"HYBRID": "SERVED_EXPECTED_REFUSAL"})
    assert early["verdict"] == "HYBRID_CUTOVER_NO_GO" and early["criteria"]["1_hybrid_zero_wrong_served"] is False
    assert _verdict(k, [], [])["verdict"] == "HYBRID_CUTOVER_NO_GO"        # empty result set
    assert E.acceptance(k, {}, _INDEPENDENT)["verdict"] == "HYBRID_CUTOVER_NO_GO"
    small = {"cases": k["cases"][:10]}                                   # not the pre-registered 45 + 15
    out = _verdict(small, _arm_rows(small, "HYBRID"), _arm_rows(small, "LLM_ONLY"))
    assert "0_pre_registered_composition" in out["failed"]


def test_acceptance_technical_failures_served_correct_and_independence():
    k = _composition()
    l = _arm_rows(k, "LLM_ONLY")
    tech3 = _verdict(k, _arm_rows(k, "HYBRID", technical={"K00", "K01", "K02"}), l)          # 3/60 = 5 %
    tech4 = _verdict(k, _arm_rows(k, "HYBRID", technical={"K00", "K01", "K02", "K03"}), l)   # 4/60 > 5 %
    assert "6_technical_and_scorer" not in tech3["failed"] and "6_technical_and_scorer" in tech4["failed"]
    assert "1_hybrid_zero_wrong_served" not in tech4["failed"]           # a technical failure is not wrong-served
    drop3 = _verdict(k, _arm_rows(k, "HYBRID", not_correct={"K00", "K01"}), l)               # −2/45 = −4.4 pp
    drop3b = _verdict(k, _arm_rows(k, "HYBRID", not_correct={"K00", "K01", "K02"}), l)       # −6.7 pp
    assert drop3["criteria"]["2_served_correct_not_worse"] is True and "2_served_correct_not_worse" in drop3b["failed"]
    for approval in (None, {}, {**_INDEPENDENT, "corpus_author": " "},
                     {**_INDEPENDENT, "authoring_independence": "NOT_ESTABLISHED"}):
        out = _verdict(k, _arm_rows(k, "HYBRID"), l, approval=approval)
        assert out["verdict"] == "HYBRID_CUTOVER_NO_GO" and out["failed"] == ["7_independence"]


def test_acceptance_refusal_latency_and_cost():
    k = _composition()
    l = _arm_rows(k, "LLM_ONLY", latency=10.0, usd=0.05)
    assert _verdict(k, _arm_rows(k, "HYBRID", reason_ok=False), l)["failed"] == ["3_refusals"]
    assert _verdict(k, _arm_rows(k, "HYBRID", latency=11.0), l)["failed"] == ["4_latency"]
    assert _verdict(k, _arm_rows(k, "HYBRID", usd=0.06), l)["failed"] == ["5_usd_per_served_correct"]
    assert _verdict(k, _arm_rows(k, "HYBRID", usd="UNKNOWN"), l)["criteria"]["5_usd_per_served_correct"] is None
    nothing = {f"K{i:02d}" for i in range(45)}                           # Hybrid serves nothing correct: undefined
    out = _verdict(k, _arm_rows(k, "HYBRID", not_correct=nothing), _arm_rows(k, "LLM_ONLY", not_correct=nothing))
    assert out["criteria"]["5_usd_per_served_correct"] is None and out["verdict"] == "HYBRID_CUTOVER_NO_GO"
    llm_none = _verdict(k, _arm_rows(k, "HYBRID"), _arm_rows(k, "LLM_ONLY", not_correct=nothing))
    assert llm_none["criteria"]["5_usd_per_served_correct"] is True
    assert llm_none["flags"] == ["CONTROL_ARM_DEGENERATE"] and _verdict(k, _arm_rows(k, "HYBRID"), l)["flags"] == []


def test_the_run_summary_carries_the_acceptance_verdict(tmp_path):
    out = E.evaluate(_corpus(tmp_path), tmp_path / "rows.jsonl", None)
    assert out["acceptance"]["verdict"] == "HYBRID_CUTOVER_NO_GO"        # a 3-case fixture is never a GO
    assert _rows(tmp_path / "rows.jsonl")[-1]["acceptance"] == json.loads(json.dumps(out["acceptance"]))


def test_a_scorer_bug_never_loses_a_row(tmp_path, monkeypatch):
    monkeypatch.setattr(E, "score", lambda *a, **k: (_ for _ in ()).throw(KeyError("bug")))
    out = E.evaluate(_corpus(tmp_path), tmp_path / "rows.jsonl", None)
    assert {r["outcome"] for r in out["rows"]} == {"SCORER_ERROR"} and out["summary"]["HYBRID"]["scorer_errors"] == 3


# ── authorization and corpus integrity: refused before any request ───────────────────────────────────────────────────

def test_live_is_refused_before_any_request(tmp_path, monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: pytest.fail("a refused run sent a request"))
    corpus = _corpus(tmp_path)
    monkeypatch.delenv("ALLOW_LIVE_AI", raising=False)
    with pytest.raises(E.LiveRefused):
        E.authorize_live(corpus, None)
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key-never-sent")
    with pytest.raises(E.LiveRefused):
        E.authorize_live(corpus, None)
    pending = tmp_path / "approval.json"
    pending.write_text(json.dumps({**_terms(corpus), "owner_decision": "PENDING_OWNER_DECISION"}), encoding="utf-8")
    with pytest.raises(E.LiveRefused):
        E.authorize_live(corpus, pending)
    data = corpus.read_bytes()
    for bad in ({"corpus_sha256": "0" * 64}, {"model": "another-model"}, {"max_requests": 10_000},
                {"llm_only_output_reservation_tokens": 8192}, {"measured_system": "0" * 64},
                {"harness_sha256": "0" * 64}):
        with pytest.raises(E.LiveRefused):
            E.check_approval_terms(data, _terms(corpus, **bad))
    assert E.check_approval_terms(data, _terms(corpus))["max_requests"] == 40
    with pytest.raises(E.LiveRefused):                                        # evaluate re-checks the exact bytes
        E.evaluate(corpus, tmp_path / "x.jsonl", _terms(corpus, corpus_sha256="0" * 64))
    assert not (tmp_path / "x.jsonl").exists()


@pytest.mark.parametrize("mutate", [
    lambda cs: cs.append(dict(cs[0], id="dup-text", problem_text=" " + cs[0]["problem_text"].upper())),  # normalized dup
    lambda cs: cs.append(dict(cs[1], problem_text="khác")) or cs[-1].update(id=cs[0]["id"]),   # duplicate id
    lambda cs: cs[0].update(oracle={}),                                   # construction-only / no oracle
    lambda cs: cs[0].update(oracle={"perimeter": ["4"]}),                 # unknown kind
    lambda cs: cs[0].update(oracle={"distance": ["mười hai"]}),           # not an exact number
    lambda cs: cs[2].update(refusal_class="CURVED_SOLID"),                # not a pre-registered refusal class
])
def test_an_invalid_corpus_is_refused_before_any_request(tmp_path, mutate):
    cases = json.loads(_corpus(tmp_path).read_text(encoding="utf-8"))["cases"]
    mutate(cases)
    bad = _write(tmp_path, cases, "bad.json")
    with pytest.raises(E.LiveRefused):
        E.evaluate(bad, tmp_path / "out.jsonl", None)
    assert not (tmp_path / "out.jsonl").exists()


def test_contamination_scan_works_inside_a_checkout_under_a_skipped_name(tmp_path):
    """Review round 2, M4 regression: the skip set was tested on the ABSOLUTE path, so a worktree under
    `.superpowers/` scanned nothing. Only names inside the repository count."""
    repo = tmp_path / ".superpowers" / "worktrees" / "wt"
    (repo / "frontend/src/data").mkdir(parents=True)
    text = "Cho hình lập phương ABCD.A'B'C'D' cạnh 4. Tính độ dài đường chéo AC'."
    (repo / "frontend/src/data/samples.json").write_text(json.dumps({"p": text}), encoding="utf-8")
    (repo / "node_modules").mkdir()
    (repo / "node_modules/copy.json").write_text(json.dumps({"p": text}), encoding="utf-8")
    hits = E.contamination_scan({"cases": [{"id": "c", "problem_text": text}]}, repo)
    assert hits == {"c": {"exact": ["frontend/src/data/samples.json"], "near": []}}


def test_an_interrupted_run_is_reported_as_interrupted(tmp_path, monkeypatch):
    """Review round 2, N3: the summary written in `finally` must not claim completion."""
    calls = [0]
    real = E.score

    def interrupt(*a, **k):
        calls[0] += 1
        if calls[0] == 3:
            raise KeyboardInterrupt
        return real(*a, **k)

    monkeypatch.setattr(E, "score", interrupt)
    with pytest.raises(KeyboardInterrupt):
        E.evaluate(_corpus(tmp_path), tmp_path / "rows.jsonl", None)
    summary = _rows(tmp_path / "rows.jsonl")[-1]
    assert summary["type"] == "summary" and summary["completed"] is False
    assert summary["stop_reason"] == "INTERRUPTED:KeyboardInterrupt"


def test_an_empty_candidate_list_is_infrastructure_in_both_arms(tmp_path, monkeypatch):
    out = _live(tmp_path, monkeypatch, Provider({"candidates": []}), cases=[_one()])
    hybrid = next(r for r in out["rows"] if r["arm"] == "HYBRID")
    assert hybrid["hybrid_code"] == "NO_CANDIDATE" and hybrid["technical_failure"] and not hybrid["false_refusal"]


def test_contamination_scan_finds_opened_text_and_reports_its_limits(tmp_path):
    repo = tmp_path / "repo"
    (repo / "docs/evaluation/run").mkdir(parents=True)
    (repo / "backend/scripts").mkdir(parents=True)
    opened = "Cho hình chóp S.ABC có SA = 3 và đáy là tam giác đều cạnh 2. Tính thể tích khối chóp."
    (repo / "docs/evaluation/run/cases.json").write_text(json.dumps({"t": opened}, ensure_ascii=True), encoding="utf-8")
    (repo / "backend/scripts/gen.py").write_text("T = " + json.dumps(opened, ensure_ascii=True) + "\n", encoding="utf-8")
    corpus_file = repo / "docs/evaluation/run/heldout.json"
    corpus = {"cases": [
        {"id": "copied", "problem_text": "  cho HÌNH chóp S.ABC có SA = 3 và đáy là tam giác đều cạnh 2. Tính thể tích khối chóp. "},
        {"id": "near", "problem_text": "Cho hình chóp S.ABC có SA = 3 và đáy là tam giác đều cạnh 2. Tính diện tích xung quanh."},
        {"id": "fresh", "problem_text": "Cho lăng trụ đứng ABC.A'B'C' có AA' = 5 và đáy vuông tại A."}]}
    corpus_file.write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
    hits = E.contamination_scan(corpus, repo, exclude=corpus_file)            # the corpus never matches itself
    assert sorted(hits["copied"]["exact"]) == ["backend/scripts/gen.py", "docs/evaluation/run/cases.json"]
    assert hits["near"]["near"] and not hits["near"]["exact"] and "fresh" not in hits


# ── mock provider: every live failure mode is contained, counted and never scored as a model result ──────────────────

def _body(payload=None, finish="STOP", text=None, block=None):
    if block:
        return {"promptFeedback": {"blockReason": block}}
    return {"candidates": [{"content": {"parts": [{"text": text if text is not None else json.dumps(payload,
                                                                                                    ensure_ascii=False)}]},
                            "finishReason": finish}],
            "usageMetadata": {"promptTokenCount": 9000, "candidatesTokenCount": 700, "totalTokenCount": 9700}}


class Provider:
    """Scripted `httpx.post` replacement: each call pops the next action (a body dict, an int status, or an exception)."""

    def __init__(self, *script, default=None):
        self.script, self.default, self.calls = list(script), default, 0

    def __call__(self, url, **kwargs):
        assert "key=" not in url and kwargs["headers"]["x-goog-api-key"]          # the key travels in a header
        self.calls += 1
        step = self.script.pop(0) if self.script else self.default
        if isinstance(step, Exception):
            raise step
        request = httpx.Request("POST", url)
        if isinstance(step, int):
            return httpx.Response(step, json={"error": {"code": step}}, request=request)
        return httpx.Response(200, json=step, request=request)


def _env(monkeypatch, provider, llm_only=None):
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key-never-sent")
    monkeypatch.setattr(httpx, "post", provider)

    async def fake_llm_only(text, api_key):
        if isinstance(llm_only, Exception):
            raise llm_only
        return llm_only or {"status": "unsupported", "failure_category": "geometry_generation_failed"}

    monkeypatch.setattr(E, "run_llm_only", fake_llm_only)


def _live(tmp_path, monkeypatch, provider, cases=None, llm_only=None, **terms):
    corpus = _write(tmp_path, cases) if cases is not None else _corpus(tmp_path)
    _env(monkeypatch, provider, llm_only)
    return E.evaluate(corpus, tmp_path / "live.jsonl", _terms(corpus, **terms), sleep=lambda s: None)


def _one(case_id="L1", payload=SERVED, expect="SERVE"):
    c = {"id": case_id, "problem_text": payload["problem_text"], "expect": expect}
    return c | ({"oracle": {"distance": ["12"]}} if expect == "SERVE" else {"refusal_class": "CONTRADICTORY_DATA"})


def _hybrid_first(prefix):
    return next(f"{prefix}{i}" for i in range(100) if E.arm_order(f"{prefix}{i}")[0] == "HYBRID")


def test_mock_success_is_scored_with_usage_and_cost(tmp_path, monkeypatch):
    out = _live(tmp_path, monkeypatch, Provider(_body(SERVED)), cases=[_one()])
    row = next(r for r in out["rows"] if r["arm"] == "HYBRID")
    assert row["served_correct"] and row["http_requests"] == 1 and row["requests_with_usage"] == 1
    assert row["usd"] == pytest.approx(9000 * 0.30e-6 + 700 * 2.50e-6) and row["extraction_valid"]
    assert out["measurement_class"] == "PREREGISTERED_LIVE_PAIRED_EVALUATION" and out["completed"]


def test_mock_rate_limit_is_retried_like_call_gemini_and_each_retry_is_budgeted(tmp_path, monkeypatch):
    out = _live(tmp_path, monkeypatch, Provider(429, 503, _body(SERVED)), cases=[_one()])
    row = next(r for r in out["rows"] if r["arm"] == "HYBRID")
    assert row["served_correct"] and row["http_requests"] == 3


@pytest.mark.parametrize("action,attempts", [(httpx.ReadTimeout("mock timeout"), 4), (500, 4), (400, 1)])
def test_mock_transport_failures_are_infrastructure_never_model_or_geometry_outcomes(tmp_path, monkeypatch, action,
                                                                                      attempts):
    out = _live(tmp_path, monkeypatch, Provider(default=action), cases=[_one()])
    row = next(r for r in out["rows"] if r["arm"] == "HYBRID")
    assert row["technical_failure"] and row["hybrid_code"] == "PROVIDER_ERROR" and not row["served"]
    assert row["false_refusal"] is False and row["http_requests"] == attempts   # 4xx is not retried; transient is


@pytest.mark.parametrize("body,code", [
    (_body(SERVED, finish="MAX_TOKENS"), "RESPONSE_TRUNCATED"),                # partial / truncated output
    (_body(text='{"schema_version": "typed-fact-next/2", "problem_text": '), "JSON_INVALID"),   # invalid JSON
])
def test_mock_bad_model_output_is_not_served_in_both_arms_alike(tmp_path, monkeypatch, body, code):
    """M2: LLM_ONLY re-asks an invalid output and ends `geometry_generation_failed` (not served, not technical); Hybrid's
    truncated/invalid output is classified the same way, not as infrastructure."""
    out = _live(tmp_path, monkeypatch, Provider(body), cases=[_one()])
    rows = {r["arm"]: r for r in out["rows"]}
    assert rows["HYBRID"]["hybrid_code"] == code
    for arm in ("HYBRID", "LLM_ONLY"):
        assert not rows[arm]["served"] and not rows[arm]["technical_failure"] and rows[arm]["false_refusal"]


@pytest.mark.parametrize("body", [_body(block="SAFETY"), _body(SERVED, finish="SAFETY")])
def test_a_provider_block_stops_the_run(tmp_path, monkeypatch, body):
    out = _live(tmp_path, monkeypatch, Provider(default=body),
                cases=[_one(), _one("L2", dict(SERVED, problem_text=SERVED["problem_text"] + " Vẽ hình."))])
    hybrid = next(r for r in out["rows"] if r["arm"] == "HYBRID")
    assert hybrid["technical_failure"] and out["stop_reason"] == "PROVIDER_BLOCK"


def test_request_cap_blocks_the_next_request_before_it_is_sent(tmp_path, monkeypatch):
    provider = Provider(default=httpx.ConnectError("mock: unreachable"))
    out = _live(tmp_path, monkeypatch, provider, max_requests=1)
    assert provider.calls == 1 and out["http_requests"] == 1
    assert out["stop_reason"] == "REQUEST_CAP" and out["completed"] is False
    assert out["summary"]["paired"]["unpaired_cases"] in ([], ["C1"])
    from app.ai import gemini
    assert gemini.BUDGET is None                                                # the cap never leaks into production


def test_the_runtime_ceiling_is_the_exact_payload_bound_per_request(tmp_path, monkeypatch):
    """With the planning estimate neutralized, the per-request guard alone decides: a capped Hybrid request (8192
    output) fits under USD 0.10; the real LLM_ONLY request (no output cap ⇒ 65 536, ≥ USD 0.164) is blocked BEFORE
    `call_gemini` sends it."""
    async_calls = []

    async def never(self, url, *a, **k):
        async_calls.append(url)
        raise AssertionError("an over-ceiling LLM_ONLY request was sent")

    monkeypatch.setattr(E, "worst_case_request_usd", lambda corpus, approval: 0.0)
    monkeypatch.setattr(httpx.AsyncClient, "post", never)
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key-never-sent")
    provider = Provider(default=_body(SERVED))
    monkeypatch.setattr(httpx, "post", provider)
    corpus = _write(tmp_path, [_one(_hybrid_first("H"))])
    out = E.evaluate(corpus, tmp_path / "live.jsonl", _terms(corpus, max_usd=0.10), sleep=lambda s: None)
    assert provider.calls == 1 and async_calls == [] and out["stop_reason"] == "COST_CEILING"
    hybrid = next(r for r in out["rows"] if r["arm"] == "HYBRID")
    assert hybrid["served_correct"] and hybrid["usd_upper"] < 0.10
    terms = _terms(corpus)
    assert E.request_ceiling_usd({"generationConfig": {"maxOutputTokens": 8192}}, terms) < 0.021
    assert E.request_ceiling_usd({"generationConfig": {}}, terms) >= 65536 * 2.50e-6


def test_infrastructure_streak_stops_the_run(tmp_path, monkeypatch):
    cases = [_one(f"L{i}", dict(SERVED, problem_text=SERVED["problem_text"] + f" Câu {i}.")) for i in range(4)]
    out = _live(tmp_path, monkeypatch, Provider(default=500), cases=cases, llm_only=RuntimeError("mock: provider down"))
    assert out["stop_reason"] == "INFRASTRUCTURE_STREAK" and len(out["rows"]) == 3


def test_a_served_expected_refusal_stops_only_that_arm(tmp_path, monkeypatch):
    """§5.1 / review B2: the arm that served an expected refusal stops and is reported; the other arm goes on."""
    cases = [_one("R1", expect="REFUSE"), _one("L2", dict(SERVED, problem_text=SERVED["problem_text"] + " Vẽ hình."))]
    out = _live(tmp_path, monkeypatch, Provider(default=_body(SERVED)), cases=cases)
    assert out["stopped_arms"] == {"HYBRID": "SERVED_EXPECTED_REFUSAL"} and out["completed"] is False
    assert [r["case_id"] for r in out["rows"] if r["arm"] == "HYBRID"] == ["R1"]
    assert [r["case_id"] for r in out["rows"] if r["arm"] == "LLM_ONLY"] == ["R1", "L2"]


def test_the_control_arm_is_never_stopped_by_its_own_wrong_serve(tmp_path, monkeypatch):
    """Amendment A2: stopping LLM_ONLY would leave the pairs incomplete, so a GO would become unreachable exactly when
    the control is the unsafe arm. Its served expected-refusal is recorded as wrong-served and the run goes on."""
    cases = [_one("R1", expect="REFUSE"), _one("L2", dict(SERVED, problem_text=SERVED["problem_text"] + " Vẽ hình."))]
    out = _live(tmp_path, monkeypatch, Provider(default=_body(None)), cases=cases,
                llm_only=_ok(_quantity("measure.distance", _rational("12"))))
    llm = {r["case_id"]: r for r in out["rows"] if r["arm"] == "LLM_ONLY"}
    assert out["stopped_arms"] == {} and llm["R1"]["wrong_served"] and set(llm) == {"R1", "L2"}


def test_an_identity_change_mid_run_stops_before_the_next_request(tmp_path, monkeypatch):
    cases = [_one(_hybrid_first("I")), _one("L2", dict(SERVED, problem_text=SERVED["problem_text"] + " Vẽ hình."))]
    corpus = _write(tmp_path, cases)
    terms = _terms(corpus)                                    # computed before the identity starts drifting
    real, calls = E.runtime_identity(), [0]

    def drifting():                                           # 1: approval check · 2: run identity · 3: case 1 · 4: case 2
        calls[0] += 1
        return real if calls[0] <= 3 else {**real, "measured_system": "changed"}

    monkeypatch.setattr(E, "runtime_identity", drifting)
    provider = Provider(default=_body(SERVED))
    _env(monkeypatch, provider)
    out = E.evaluate(corpus, tmp_path / "live.jsonl", terms, sleep=lambda s: None)
    assert out["stop_reason"] == "IDENTITY_CHANGED" and provider.calls == 1


def test_the_real_llm_only_arm_is_held_by_the_same_request_cap(tmp_path, monkeypatch):
    """Production `run_pipeline` → `call_gemini` (not a fake): its HTTP attempts pass the same budget, so the cap holds
    across both arms. The mock provider answers 429 forever; nothing reaches the network (conftest guard)."""
    async_calls = []

    async def rate_limited(self, url, *a, **k):
        async_calls.append(url)
        return httpx.Response(429, json={"error": {"code": 429}}, request=httpx.Request("POST", url))

    import app.ai.gemini as gemini
    monkeypatch.setattr(gemini, "BACKOFF_BASE_SECONDS", 0.0)
    monkeypatch.setattr(httpx.AsyncClient, "post", rate_limited)
    monkeypatch.setenv("ALLOW_LIVE_AI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key-never-sent")
    provider = Provider(default=_body(SERVED))
    monkeypatch.setattr(httpx, "post", provider)
    corpus = _write(tmp_path, [_one()])
    out = E.evaluate(corpus, tmp_path / "live.jsonl", _terms(corpus, max_requests=3), sleep=lambda s: None)
    llm = next(r for r in out["rows"] if r["arm"] == "LLM_ONLY")
    assert llm["technical_failure"] and not llm["served"] and async_calls
    assert len(async_calls) + provider.calls == 3 == out["http_requests"] and out["stop_reason"] == "REQUEST_CAP"


def test_a_deserved_go_is_reachable_end_to_end_with_zero_call_domain_gate_refusals(tmp_path, monkeypatch):
    """Review B1/M1: the 5 out-of-domain cases are refused by the deterministic gate with 0 requests (no usage). Under
    the §3 cost rule they cost a known 0.0, so a run that deserves a GO gets one through `evaluate()` itself."""
    from app.ai.telemetry import record_usage

    def variant(i, mutate=None):
        p = deepcopy(SERVED)
        p["problem_text"] = p["problem_text"].replace("AB = 6.", f"AB = {6 + i}.")     # d(A', (ABC)) = AA' = 12 still
        p["premises"][1] = {**p["premises"][1], "args": {"segment": ["A", "B"], "value": str(6 + i)},
                            "quote": f"AB = {6 + i}."}
        if mutate:
            mutate(p)
        return p

    def ambiguous(p):
        p["solids"].append({**p["solids"][0], "solid_id": "pr2"})

    def impossible(p):
        p["problem_text"] = p["problem_text"].replace("AA' = 12.", "AA' = 12. BC = 11.")
        p["premises"].append({"kind": "segment_length", "args": {"segment": ["B", "C"], "value": "11"}, "quote": "BC = 11."})

    cases, script, llm_by_text = [], [], {}
    for i in range(45):
        p = variant(i)
        cases.append({"id": f"S{i:02d}", "problem_text": p["problem_text"], "expect": "SERVE", "oracle": {"distance": ["12"]}})
        script.append(_body(p))
        llm_by_text[p["problem_text"]] = _ok(_quantity("measure.distance", _rational("12")))
    for i, (klass, mutate) in enumerate([("CONTRADICTORY_DATA", impossible), ("MISSING_DATA", ambiguous)] * 5):
        p = variant(100 + i, mutate)
        cases.append({"id": f"R{i:02d}", "problem_text": p["problem_text"], "expect": "REFUSE", "refusal_class": klass})
        script.append(_body(p))
    for i in range(5):
        cases.append({"id": f"O{i}", "problem_text": f"Viết chương trình Python in {i + 10} số Fibonacci đầu tiên.",
                      "expect": "REFUSE", "refusal_class": "OUT_OF_DOMAIN"})
    clock = [0.0]
    monkeypatch.setattr(E.time, "perf_counter", lambda: clock[0])

    async def llm_only(text, api_key):
        clock[0] += 10.0
        if text in llm_by_text:
            record_usage("semantic_analyze", {"promptTokenCount": 12000, "candidatesTokenCount": 4000})
        from app.main import _ngoai_pham_vi
        return llm_by_text.get(text) or _ngoai_pham_vi(text) or {"status": "unsupported",
                                                                  "failure_category": "geometry_generation_failed"}
    corpus = _write(tmp_path, cases)
    _env(monkeypatch, Provider(*script))
    monkeypatch.setattr(E, "run_llm_only", llm_only)
    out = E.evaluate(corpus, tmp_path / "go.jsonl", _terms(corpus, max_requests=400, max_usd=70.0, **_INDEPENDENT),
                     sleep=lambda s: None)
    gate_rows = [r for r in out["rows"] if r["case_id"].startswith("O")]
    assert all(r["http_requests"] == 0 and r["usd"] == "UNKNOWN" and r["usd_upper"] == 0.0 for r in gate_rows)
    assert out["acceptance"]["verdict"] == "HYBRID_CUTOVER_GO", out["acceptance"]["failed"]


def test_a_finished_run_is_never_overwritten(tmp_path):
    corpus = _corpus(tmp_path)
    E.evaluate(corpus, tmp_path / "rows.jsonl", None)
    with pytest.raises(FileExistsError):
        E.evaluate(corpus, tmp_path / "rows.jsonl", None)
