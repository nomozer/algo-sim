"""Schema-Contract v3 runner: arm isolation and identity; offline only (synthetic inputs, ReplayProvider)."""
from __future__ import annotations

import pytest

from scripts import run_schema_contract_evaluation as R


@pytest.fixture(autouse=True)
def _restore_arm_globals(monkeypatch):
    # harness() sets module globals on purpose (one arm per process); a failing test must not leak "v3" into later ones.
    from app.ai import fact_extraction as fx
    monkeypatch.setattr(fx, "RESPONSE_CONTRACT", fx.RESPONSE_CONTRACT)
    monkeypatch.setattr(fx, "SYSTEM_PROMPT", fx.SYSTEM_PROMPT)


def _inp(tmp_path):
    case = {"id": "a", "split": "dev", "source_text": "Tính AC'."}
    return {"dir": tmp_path, "cases": {"a": case}, "corpus": {"cases": [case]}, "gold": {"cases": {"a": {"facts": []}}},
            "protocol": {"locked_sha256": {"corpus": "x", "gold_facts": "y"}, "file_sha256": {"oracle.py": "z"},
                         "caps": {"PILOT": {"logical_calls": 1, "http_attempts": 1, "accounted_tokens": 10 ** 6, "usd": 1.0,
                                            "samples": 1}}}}


def test_arms_send_the_same_prompt_and_differ_only_in_the_response_contract(tmp_path):
    from app.ai import fact_extraction as fx
    inp = _inp(tmp_path)
    sent = {}
    for arm in ("v3", "flat"):
        R.harness(arm, inp)
        sent[arm] = fx.build_request("Tính AC'.")
    assert sent["flat"]["systemInstruction"] == sent["v3"]["systemInstruction"]
    assert sent["flat"]["generationConfig"]["responseSchema"] == fx.facts_response_schema("flat")
    assert sent["v3"]["generationConfig"]["responseSchema"] == fx.facts_response_schema("v3")
    assert fx.RESPONSE_CONTRACT == "flat"          # the last harness wins; nothing leaks from the earlier arm


def test_identity_names_the_arm_and_its_surface(tmp_path):
    from app.ai import fact_extraction as fx
    inp = _inp(tmp_path)
    ids = {}
    for arm in ("flat", "v3"):
        h = R.harness(arm, inp)
        ids[arm] = h.identity(inp, "PILOT")
        assert ids[arm]["arm"] == ids[arm]["contract"] == arm
        assert ids[arm]["surface_sha256"] == fx.surface_fingerprint(arm)
    assert ids["flat"]["surface_sha256"] != ids["v3"]["surface_sha256"]
    R.harness("flat", inp)


def test_unknown_arm_is_refused(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        R.harness("v4", _inp(tmp_path))


def test_v3_gold_ceiling_refuses_gold_the_contract_cannot_carry(tmp_path, monkeypatch):
    # I4: the v3 arm's GOLD ceiling must not assume every authored payload is v3-expressible.
    from app.ai import fact_extraction as fx
    inp = _inp(tmp_path)
    bad = {"id": "q", "kind": "question", "role": "question", "quantity": "length", "quotes": ["Tính AC'."]}   # no operand
    inp["gold"]["cases"]["a"]["facts"] = [bad]
    rows = {arm: R.harness(arm, inp).run_gold(inp) for arm in ("flat", "v3")}
    assert rows["v3"][0]["route"]["code"] == "RESPONSE_CONTRACT_INVALID"
    assert rows["flat"][0]["route"]["code"] != "RESPONSE_CONTRACT_INVALID"
    R.harness("flat", inp)


@pytest.mark.parametrize("mode,split,count", [("PILOT", "dev", 12), ("LOCKED", "heldout", 24)])
@pytest.mark.parametrize("arm", ["flat", "v3"])
@pytest.mark.parametrize("action", ["gold", "replay"])
@pytest.mark.parametrize("fail", [False, True])
def test_routes_only_selected_split_before_processing(tmp_path, monkeypatch, mode, split, count, arm, action, fail):
    from app.ai import fact_extraction, function_route
    from app.simulation.geometry_functions import KetQuaTuyen
    inp = _inp(tmp_path)
    cases = [{"id": f"case{i}", "split": "dev" if i % 3 == 0 else "heldout", "source_text": f"source{i}"}
             for i in range(36)]
    inp.update(corpus={"cases": cases}, cases={c["id"]: c for c in cases},
               gold={"cases": {c["id"]: {"facts": []} for c in cases}})
    inp["protocol"]["caps"][mode] = {**inp["protocol"]["caps"]["PILOT"], "logical_calls": 36, "http_attempts": 36,
                                    "accounted_tokens": 10**7, "usd": 10}
    calls = []

    def route(source, data):
        calls.append(source)
        if fail:
            raise RuntimeError("synthetic route failure")
        return KetQuaTuyen("REFUSED", "SYNTHETIC", "split boundary test")

    monkeypatch.setattr(function_route, "run_fact_route", route)
    monkeypatch.setattr(fact_extraction, "run_fact_route", route)
    h = R.harness(arm, inp, mode=mode)
    expected = [c["source_text"] for c in cases if c["split"] == split]
    if action == "gold":
        if fail:
            with pytest.raises(RuntimeError, match="synthetic route failure"):
                h.run_gold(inp)
        else:
            assert len(h.run_gold(inp)) == count
    else:
        h.run_eval(inp, mode, h.ReplayProvider(inp), tmp_path / "replay")
    assert calls == (expected[:1] if fail else expected)
