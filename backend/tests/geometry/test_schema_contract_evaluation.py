"""Schema-Contract v3 runner: arm isolation and identity; offline only (synthetic inputs, ReplayProvider)."""
from __future__ import annotations

from scripts import run_schema_contract_evaluation as R


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
