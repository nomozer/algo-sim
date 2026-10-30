# -*- coding: utf-8 -*-
"""Hybrid master Phase A — Route D cache identity (D-02), rollback (D-12) and the declared `/api/analyze` opt-in gate.

The opt-in boundary is the existing `HYBRID_V2_LOCAL=offline-replay` + loopback gate (`test_hybrid_v2_local_analyze.py`);
no new mode. Route D rows live in their own key namespace and policy tag, bound to the EXACT source text, the recorded
extraction and the Route D surface; only SERVED results are stored. Rollback = the routing switch (controlled), never a
silent fallback: a Hybrid refusal is returned as a refusal and `LLM_ONLY` never runs. 0 provider calls.
"""
from __future__ import annotations

import json
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app import main as main_module
from app.ai import hybrid_offline as H
from app.main import _cache_key, app
from app.persistence.db import SessionLocal, SimulationCache, init_db
from tests.geometry.test_typed_fact_next_v2_distance_bridge import _prism

LOOPBACK = ("127.0.0.1", 50124)
LLM_ONLY_SENTINEL = {"status": "ok", "simulation_id": "llm-only-sentinel", "marker": "LLM_ONLY"}


def _post(text, client=LOOPBACK):
    return TestClient(app, client=client).post("/api/analyze", json={"input": {"type": "text", "content": text}})


def _write(path, *payloads):
    path.write_text(json.dumps({"schema": H.LOCAL_REPLAY_SCHEMA, "outputs": {p["problem_text"]: p for p in payloads}},
                               ensure_ascii=False), encoding="utf-8")


def _purge(*texts):
    init_db()
    with SessionLocal() as s:
        for t in texts:
            s.query(SimulationCache).filter(SimulationCache.problem_text == t).delete()
        s.commit()


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Hybrid ON (loopback), corpus with the served prism; LLM_ONLY must not run unless a test installs a fake."""
    raw = _prism()
    path = tmp_path / "corpus.json"
    _write(path, raw)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("HYBRID_V2_LOCAL", "offline-replay")
    monkeypatch.setenv("HYBRID_V2_LOCAL_REPLAY_CORPUS", str(path))

    def pipeline_must_not_run(*_a, **_k):
        raise AssertionError("LLM_ONLY pipeline ran on the Hybrid path (silent fallback)")

    monkeypatch.setattr(main_module, "run_pipeline", pipeline_must_not_run)
    _purge(raw["problem_text"])
    yield raw, path
    _purge(raw["problem_text"])


def _count_route_runs(monkeypatch):
    calls = []
    real = H.run_typed_fact_next_v2_route
    monkeypatch.setattr(H, "run_typed_fact_next_v2_route", lambda p: calls.append(1) or real(p))
    return calls


# ── D-02: Route D cache identity ─────────────────────────────────────────────────────────────────────────────────────

def test_served_result_is_cached_and_a_repeat_is_a_hit_without_re_execution(env, monkeypatch):
    raw, _ = env
    runs = _count_route_runs(monkeypatch)
    first = _post(raw["problem_text"])
    second = _post(raw["problem_text"])
    assert first.status_code == second.status_code == 200
    assert first.headers["x-algosim-cache"] == "miss" and second.headers["x-algosim-cache"] == "hit"
    assert second.json() == first.json() and first.json()["route_d"]["status"] == "SERVED"
    assert second.headers["cache-control"] == "no-store"                 # server cache only, never HTTP caches
    assert len(runs) == 1


def test_route_d_rows_never_reuse_the_llm_only_key_or_policy(env):
    raw, path = env
    _post(raw["problem_text"])
    prep = H.prepare_local_replay(raw["problem_text"], str(path))
    assert prep.cache_key is not None and prep.cache_key != _cache_key(raw["problem_text"])
    with SessionLocal() as s:
        row = s.query(SimulationCache).filter_by(key=prep.cache_key).one()
        assert row.policy_version == main_module.ROUTE_D_CACHE_POLICY
        assert main_module._cache_lookup(s, prep.cache_key, main_module._policy_identity(
            main_module.route_policy_snapshot())) is None                   # LLM_ONLY identity cannot read it
        assert s.query(SimulationCache).filter_by(key=_cache_key(raw["problem_text"])).count() == 0


def test_a_changed_recorded_extraction_for_the_same_text_misses(env, monkeypatch):
    raw, path = env
    runs = _count_route_runs(monkeypatch)
    _post(raw["problem_text"])
    changed = deepcopy(raw)
    changed["math_goals"][0]["goal_id"] = "q2"                            # same source, different recorded extraction
    _write(path, changed)
    r = _post(raw["problem_text"])
    assert r.headers["x-algosim-cache"] == "miss" and len(runs) == 2
    assert "q2" in r.json()["route_d"]["answer_exact"]


def test_a_changed_route_surface_misses(env, monkeypatch):
    raw, _ = env
    runs = _count_route_runs(monkeypatch)
    _post(raw["problem_text"])
    from app.simulation.geometry_functions import planner
    monkeypatch.setattr(planner, "PLANNER_VERSION", planner.PLANNER_VERSION + "+test")
    assert _post(raw["problem_text"]).headers["x-algosim-cache"] == "miss" and len(runs) == 2


def test_identity_is_bound_to_the_exact_source_not_a_normalized_one(env):
    raw, path = env
    a = H.prepare_local_replay(raw["problem_text"], str(path))
    variant = "  " + raw["problem_text"].upper()                         # same LLM_ONLY key (normalized), other source
    assert _cache_key(variant) == _cache_key(raw["problem_text"])
    changed = deepcopy(raw)
    changed["problem_text"] = variant
    _write(path, raw, changed)
    b = H.prepare_local_replay(variant, str(path))
    assert a.cache_key and b.cache_key and a.cache_key != b.cache_key


def test_refusals_are_never_cached(env):
    raw, path = env
    text = raw["problem_text"] + " Tính thêm thể tích khối lăng trụ."
    r = _post(text)
    assert r.json()["route_d"]["status"] == "REFUSED"
    assert H.prepare_local_replay(text, str(path)).cache_key is None    # nothing recorded ⇒ not cacheable
    bad = deepcopy(raw)
    bad["premises"][1]["args"]["value"] = "7"                           # text says AB = 6
    _write(path, bad)
    r = _post(raw["problem_text"])
    assert r.json()["route_d"]["status"] == "REFUSED" and r.headers["x-algosim-cache"] == "none"
    key = H.prepare_local_replay(raw["problem_text"], str(path)).cache_key
    with SessionLocal() as s:
        assert s.query(SimulationCache).filter_by(key=key).count() == 0


@pytest.mark.parametrize("stored", ["not json", json.dumps({"route_d": {"status": "REFUSED"}}), json.dumps([1])])
def test_a_stored_row_that_is_not_a_served_response_is_a_miss_and_is_replaced(env, monkeypatch, stored):
    raw, path = env
    runs = _count_route_runs(monkeypatch)
    key = H.prepare_local_replay(raw["problem_text"], str(path)).cache_key
    with SessionLocal() as s:
        s.add(SimulationCache(key=key, problem_text=raw["problem_text"], simulation_id="poison", envelope_json=stored,
                              dsl_version=main_module.DSL_VERSION, policy_version=main_module.ROUTE_D_CACHE_POLICY))
        s.commit()
    r = _post(raw["problem_text"])
    assert r.json()["route_d"]["status"] == "SERVED" and r.headers["x-algosim-cache"] == "miss" and len(runs) == 1
    assert _post(raw["problem_text"]).headers["x-algosim-cache"] == "hit"


def test_a_concurrent_writer_conflict_still_returns_the_verified_result(env, monkeypatch):
    raw, _ = env
    real_commit = main_module._store_route_d

    def racing(*a, **k):
        raise IntegrityError("INSERT", {}, Exception("UNIQUE constraint failed"))

    monkeypatch.setattr(main_module, "_store_route_d", racing)
    r = _post(raw["problem_text"])
    assert r.status_code == 200 and r.json()["route_d"]["status"] == "SERVED"
    monkeypatch.setattr(main_module, "_store_route_d", real_commit)


def _mutant(monkeypatch, module, name, old, new):
    import inspect
    import textwrap
    src = textwrap.dedent(inspect.getsource(getattr(module, name)))
    assert src.count(old) == 1, old
    ns = dict(vars(module))
    exec(compile(src.replace(old, new), "<mutant>", "exec"), ns)
    monkeypatch.setattr(module, name, ns[name])


def test_mutant_identity_without_the_recorded_extraction_is_caught(env, monkeypatch):
    _mutant(monkeypatch, H, "prepare_local_replay", "'recorded_extraction': recorded,", "")
    with pytest.raises(AssertionError):
        test_a_changed_recorded_extraction_for_the_same_text_misses(env, monkeypatch)


def test_mutant_reusing_a_non_served_row_is_caught(env, monkeypatch):
    _mutant(monkeypatch, main_module, "_served_route_d",
            'if isinstance(body, dict) and (body.get("route_d") or {}).get("status") == "SERVED"', "if True")
    raw, path = env
    key = H.prepare_local_replay(raw["problem_text"], str(path)).cache_key
    with SessionLocal() as s:
        s.add(SimulationCache(key=key, problem_text=raw["problem_text"], simulation_id="poison",
                              envelope_json=json.dumps({"route_d": {"status": "REFUSED"}, "envelope": {}}),
                              dsl_version=main_module.DSL_VERSION, policy_version=main_module.ROUTE_D_CACHE_POLICY))
        s.commit()
    assert _post(raw["problem_text"]).json()["route_d"]["status"] == "REFUSED"   # the mutant serves the poisoned row


# ── D-12: rollback is the routing switch, never a silent fallback ────────────────────────────────────────────────────

def _fake_llm_only(monkeypatch, calls):
    async def fake(text, api_key, **kwargs):
        calls.append(kwargs["route_policy"])
        return dict(LLM_ONLY_SENTINEL)
    monkeypatch.setattr(main_module, "run_pipeline", fake)
    monkeypatch.setenv("GEMINI_API_KEY", "offline-test-key-never-sent")


def test_rollback_after_a_hybrid_session_runs_llm_only_untouched_and_re_enabling_reuses_route_d(env, monkeypatch):
    raw, _ = env
    assert _post(raw["problem_text"]).headers["x-algosim-cache"] == "miss"     # Hybrid session wrote a Route D row
    calls = []
    _fake_llm_only(monkeypatch, calls)
    monkeypatch.delenv("HYBRID_V2_LOCAL")                                       # ROLLBACK_TO_LEGACY_MODE
    body = _post(raw["problem_text"]).json()
    assert body["marker"] == "LLM_ONLY" and "route_d" not in body and len(calls) == 1
    assert calls[0].hybrid_preview_enabled is False and calls[0].fingerprint() is None   # default policy, unchanged
    cached = _post(raw["problem_text"]).json()                                   # LLM_ONLY's own row, not Route D's
    assert cached["marker"] == "LLM_ONLY" and cached["cached"] is True and len(calls) == 1
    monkeypatch.setenv("HYBRID_V2_LOCAL", "offline-replay")                      # re-enable
    r = _post(raw["problem_text"])
    assert r.headers["x-algosim-cache"] == "hit" and r.json()["route_d"]["status"] == "SERVED"


def test_llm_only_response_is_identical_with_or_without_route_d_rows_present(env, monkeypatch):
    raw, _ = env
    calls = []
    monkeypatch.delenv("HYBRID_V2_LOCAL")
    _fake_llm_only(monkeypatch, calls)
    before = _post(raw["problem_text"]).content
    _purge(raw["problem_text"])
    monkeypatch.setenv("HYBRID_V2_LOCAL", "offline-replay")
    monkeypatch.setattr(main_module, "run_pipeline", lambda *a, **k: (_ for _ in ()).throw(AssertionError("fallback")))
    assert _post(raw["problem_text"]).headers["x-algosim-cache"] == "miss"
    monkeypatch.delenv("HYBRID_V2_LOCAL")
    _fake_llm_only(monkeypatch, calls)
    assert _post(raw["problem_text"]).content == before


# ── The declared gate: typed refusals, no fallback, no partial scene ─────────────────────────────────────────────────

def _missing_fact(p):            # the AA' premise is dropped: its sentence stays unread
    p["premises"] = [x for x in p["premises"] if x["args"].get("segment") != ["A", "A'"]]
def _contradiction(p):           # payload value disagrees with the text
    p["premises"][2]["args"]["value"] = "9"
def _ownership(p):               # premise scoped to an undeclared solid
    p["premises"][1]["solid_id"] = "other"
def _ambiguous(p):               # a second solid owning the same labels, unscoped premise
    p["solids"].append({**p["solids"][0], "solid_id": "pr2"})
def _unsupported(p):             # a question kind the deterministic route does not offer for a prism
    p["math_goals"][0].update(goal_type="radius", target={"solid": p["solids"][0]["notation"]})
def _geometry(p):                # well-formed and grounded in the text, but geometrically impossible (BC = 10)
    p["problem_text"] = p["problem_text"].replace("AA' = 12.", "AA' = 12. BC = 11.")
    p["premises"].append({"kind": "segment_length", "args": {"segment": ["B", "C"], "value": "11"}, "quote": "BC = 11."})


@pytest.mark.parametrize("mutate,code", [
    (_missing_fact, "SOURCE_PREMISE_UNREAD"), (_contradiction, "UNGROUNDED_VALUE"), (_ownership, "UNKNOWN_SOLID_ID"),
    (_ambiguous, "AMBIGUOUS_REFERENCE"), (_unsupported, "BRIDGE_UNSUPPORTED_MEASUREMENT"),
    (_geometry, "INCONSISTENT_FACTS")])
def test_invalid_requests_are_typed_refusals_without_scene_or_fallback(env, mutate, code):
    raw, path = env
    bad = deepcopy(raw)
    mutate(bad)
    _write(path, bad)
    r = _post(bad["problem_text"])
    body = r.json()
    assert r.status_code == 200 and body["route_d"]["status"] == "REFUSED"
    assert body["envelope"]["status"] == "unsupported" and "scene3d" not in body["envelope"]
    assert body["envelope"]["reason_code"] == code and r.headers["x-algosim-cache"] == "none"
    assert not body["route_d"].get("answer_exact")


def test_an_adapter_fault_is_a_typed_technical_refusal_not_a_500_or_fallback(env, monkeypatch):
    raw, _ = env
    real = H.build_adapter4_response

    def broken(result, source):
        if result.status == "SERVED":
            raise RuntimeError("scene builder bug")
        return real(result, source)

    monkeypatch.setattr(H, "build_adapter4_response", broken)
    r = _post(raw["problem_text"])
    body = r.json()
    assert r.status_code == 200 and body["route_d"]["status"] == "REFUSED"
    assert body["envelope"]["reason_code"] == "ADAPTER_INTERNAL_ERROR" and "scene3d" not in body["envelope"]
    assert r.headers["x-algosim-cache"] == "none"


def test_a_deadline_is_a_typed_technical_refusal(env, monkeypatch):
    raw, _ = env
    clock = iter(range(0, 10_000, 100))
    monkeypatch.setattr(H, "perf_counter", lambda: next(clock))           # every stage looks 100 s long
    body = _post(raw["problem_text"]).json()
    assert body["route_d"]["status"] == "REFUSED" and body["envelope"]["reason_code"] == "HYBRID_DEADLINE_EXCEEDED"


def test_runtime_call_trace_goes_through_extraction_route_d_and_adapter4(env, monkeypatch):
    raw, _ = env
    trace = []
    for name in ("extract_typed_fact_next_v2", "run_typed_fact_next_v2_route", "build_adapter4_response"):
        real = getattr(H, name)
        monkeypatch.setattr(H, name, (lambda n, f: lambda *a, **k: trace.append(n) or f(*a, **k))(name, real))
    body = _post(raw["problem_text"]).json()
    assert trace == ["extract_typed_fact_next_v2", "run_typed_fact_next_v2_route", "build_adapter4_response"]
    assert body["schema_version"] == "hybrid-route-d-simulation/4" and body["route_d"]["status"] == "SERVED"
    trace.clear()
    _post(raw["problem_text"])                                            # cache hit: no stage re-runs
    assert trace == []
