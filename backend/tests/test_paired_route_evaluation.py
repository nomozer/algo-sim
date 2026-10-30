# -*- coding: utf-8 -*-
"""Paired LLM_ONLY vs Hybrid harness (`scripts/run_paired_route_evaluation.py`): scoring, statistics and the live gate.

All offline: dry runs read recorded arm outputs; the live path is exercised with a fake provider and approved TERMS passed
in memory — automation never writes an approval value (AGENTS.md). 0 provider calls (network guard in conftest).
"""
from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

import pytest

from tests.geometry.test_typed_fact_next_v2_distance_bridge import _prism

_spec = importlib.util.spec_from_file_location(
    "run_paired_route_evaluation", Path(__file__).resolve().parents[1] / "scripts/run_paired_route_evaluation.py")
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)


def _quantity(producer, exact, group=("target",)):
    return {"type": "quantity", "display_group": list(group), "producer": producer, "exact": exact}


def _ok(*objects):
    return {"status": "ok", "scene3d": {"objects": list(objects)}}


def _corpus(tmp_path):
    served = _prism()
    contradiction = deepcopy(served)
    contradiction["premises"][1]["args"]["value"] = "7"                        # text says AB = 6
    twelve = _quantity("measure.distance", {"kind": "rational", "value": "12"})
    cases = [
        {"id": "C1", "problem_text": served["problem_text"], "expect": "SERVE", "oracle": {"distance": ["144"]},
         "dry_run": {"hybrid_extraction": served, "llm_only_envelope": _ok(twelve)}},
        {"id": "C2", "problem_text": served["problem_text"] + " ", "expect": "SERVE", "oracle": {"distance": ["144"]},
         "dry_run": {"hybrid_extraction": None,                                 # Hybrid: nothing extracted → refusal
                     "llm_only_envelope": _ok(_quantity("measure.distance", {"kind": "rational", "value": "13"}))}},
        {"id": "C3", "problem_text": served["problem_text"], "expect": "REFUSE",
         "acceptable_refusal_codes": ["UNGROUNDED_VALUE", "GATE_INCONSISTENT"],
         "dry_run": {"hybrid_extraction": contradiction,
                     "llm_only_envelope": {"status": "unsupported", "error_code": "GATE_INCONSISTENT"}}},
    ]
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps({"cases": cases}, ensure_ascii=False), encoding="utf-8")
    return path


def test_one_scorer_reads_learner_visible_targets_by_kind_as_exact_multisets():
    env = _ok(_quantity("measure.distance", {"kind": "radical", "coefficient": "2/3", "radicand": 6}),
              _quantity("measure.angle_cos_sq", {"kind": "rational", "value": "1/2"}),
              _quantity("measure.volume", {"kind": "rational", "value": "5"}, group=("given",)))   # not a target
    assert E.served_quantities(env) == {"distance": [Fraction(8, 3)], "angle_cos_sq": [Fraction(1, 2)]}
    case = {"expect": "SERVE", "oracle": {"distance": ["8/3"], "angle_cos_sq": ["1/2"]}}
    assert E.score(case, env)["served_correct"] is True
    extra = _ok(*env["scene3d"]["objects"], _quantity("measure.area", {"kind": "rational", "value": "3"}))
    assert E.score(case, extra)["wrong_served"] is True                       # an unasked served target is not correct
    assert E.score({"expect": "REFUSE"}, {"status": "unsupported", "error_code": "X"})["refusal_reason_correct"] is False


def test_dry_run_scores_both_arms_and_pairs_them(tmp_path):
    out = E.evaluate(_corpus(tmp_path), tmp_path / "rows.json", None)
    assert out["measurement_class"] == "OFFLINE_DETERMINISTIC_FIXTURE_TEST" and out["http_requests"] == 0
    rows = {(r["case_id"], r["arm"]): r for r in out["rows"]}
    assert rows["C1", "HYBRID"]["served_correct"] and rows["C1", "LLM_ONLY"]["served_correct"]
    assert rows["C2", "HYBRID"]["false_refusal"] and rows["C2", "LLM_ONLY"]["wrong_served"]
    assert rows["C3", "HYBRID"]["refusal_code"] == "UNGROUNDED_VALUE" and rows["C3", "HYBRID"]["refusal_reason_correct"]
    assert rows["C1", "HYBRID"]["source_references"]                          # provenance from the receipt
    s = out["summary"]
    assert (s["HYBRID"]["served_correct"], s["HYBRID"]["wrong_served"], s["HYBRID"]["false_refusal"]) == (1, 0, 1)
    assert (s["LLM_ONLY"]["served_correct"], s["LLM_ONLY"]["wrong_served"]) == (1, 1)
    assert s["paired"]["mcnemar_p"] == 1.0 and s["HYBRID"]["usd_total"] == "UNKNOWN"   # no usage ⇒ UNKNOWN, not 0
    assert out["stop_reason"] is None


def test_statistics():
    lo, hi = E.wilson(9, 10)
    assert 0.59 < lo < 0.60 and 0.98 < hi < 0.99
    assert E.wilson(0, 0) is None
    assert E.mcnemar_exact(0, 6) == pytest.approx(2 / 64) and E.mcnemar_exact(3, 3) == 1.0


def _terms(corpus_path, **over):
    return {"corpus_sha256": E.sha256_file(corpus_path), "max_requests": 3, "max_usd": 5.0, "model": "gemini-2.5-flash",
            "input_usd_per_million": 0.30, "output_usd_per_million": 2.50,
            "llm_only_output_reservation_tokens": 65536, **over}


def test_live_is_refused_before_any_request(tmp_path, monkeypatch):
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
    for bad in ({"corpus_sha256": "0" * 64}, {"model": "another-model"}, {"max_requests": 10_000}):
        with pytest.raises(E.LiveRefused):
            E.check_approval_terms(corpus, _terms(corpus, **bad))
    assert E.check_approval_terms(corpus, _terms(corpus))["max_requests"] == 3


def test_live_path_enforces_the_request_cap_before_sending(tmp_path, monkeypatch):
    """Fake provider: the cap blocks the 2nd Hybrid request BEFORE it is sent, and the run stops with a reason."""
    import httpx

    corpus = _corpus(tmp_path)
    sent = []

    def fake_post(url, **kwargs):
        sent.append(url)
        raise httpx.ConnectError("fake provider: unreachable by design")

    async def fake_llm_only(text, api_key):
        return {"status": "unsupported", "error_code": "FAKE"}

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr(E, "run_llm_only", fake_llm_only)
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key-never-sent")
    out = E.evaluate(corpus, tmp_path / "live.json", _terms(corpus, max_requests=1))
    assert len(sent) == 1 and out["http_requests"] == 1
    assert out["stop_reason"] == "REQUEST_CAP"
    assert out["summary"]["paired"]["unpaired_cases"] == ["C2"]                # a stopped pair is reported, not scored
    from app.ai import gemini
    assert gemini.BUDGET is None                                                # the cap never leaks into production
