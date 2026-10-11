"""Frozen A/B provider surface for the locked hybrid A/B runner reproduction tests (review I3, 2026-10-11).

The pilot runner's budgets (SMOKE_AB 500 000 accounted tokens, …) were certified for the provider surface of
product 12da4768…, not for whatever the registry exposes today. The two reproduction modules below therefore
ALWAYS run against that frozen surface, with no environment switch:

- the surface is a committed fixture (`tests/geometry/fixtures/hybrid_ab_frozen_provider_surface.json`, extracted
  from commit 2990d87d) and is accepted only if its runner surface hashes equal the ones recorded in the locked
  certification (`docs/evaluation/geometry/runs/hybrid-ab-pilot-readiness/fake-provider/final/CERTIFICATION.json`);
- budget, hash, source and network guards stay on; only `build_request` is pinned.

Whether the CURRENT surface may run a pilot is a separate question, answered NO-GO by
`tests/geometry/test_hybrid_ab_branch_readiness.py`.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent
FROZEN_SURFACE = BACKEND / "tests" / "geometry" / "fixtures" / "hybrid_ab_frozen_provider_surface.json"
LOCKED_CERTIFICATION = (BACKEND.parent / "docs" / "evaluation" / "geometry" / "runs" / "hybrid-ab-pilot-readiness"
                        / "fake-provider" / "final" / "CERTIFICATION.json")
LOCKED_PRODUCT = "12da4768495572d7b4d04af733edf0c787337a6ab486ce2cae42f7c94bbbce52"
PLACEHOLDER = "<<PROBLEM_TEXT>>"
#: Reproduction modules of the locked A/B pilot — named here, not selected by an environment variable.
FROZEN_AB_MODULES = frozenset({"test_hybrid_ab_pilot_runner", "test_hybrid_ab_pilot_mutations"})


def locked_surface_hashes() -> dict[str, str]:
    """Surface hashes the locked certification recorded, one per arm; every mode must agree on them."""
    results = json.loads(LOCKED_CERTIFICATION.read_text(encoding="utf-8"))["results"]
    identities = [r["identity"] for r in results.values()]
    assert {i["product_sha256"] for i in identities} == {LOCKED_PRODUCT}
    surfaces = {json.dumps(i["surfaces"], sort_keys=True) for i in identities}
    assert len(surfaces) == 1, "locked certification disagrees on the provider surface"
    return json.loads(surfaces.pop())


def frozen_payloads() -> dict[str, dict]:
    """Committed frozen surface, refused unless it reproduces the locked hashes."""
    from scripts.run_hybrid_ab_pilot import _sha, effective_payload

    data = json.loads(FROZEN_SURFACE.read_text(encoding="utf-8"))
    expected = locked_surface_hashes()
    for arm in ("A", "B"):
        payload = effective_payload(data[arm])
        payload.pop("contents")
        assert _sha(payload) == expected[arm], f"frozen surface {arm} does not match the locked certification"
    return {arm: data[arm] for arm in ("A", "B")}


def _with_text(payload: dict, text: str) -> dict:
    value = copy.deepcopy(payload)
    for content in value["contents"]:
        for part in content["parts"]:
            part["text"] = part["text"].replace(PLACEHOLDER, text)
    return value


@pytest.fixture(scope="session")
def frozen_ab_payloads():
    return frozen_payloads()


@pytest.fixture(autouse=True)
def locked_runner_surface(request, monkeypatch):
    if request.module.__name__.split(".")[-1] not in FROZEN_AB_MODULES:
        return
    data = request.getfixturevalue("frozen_ab_payloads")
    from app.ai import fact_extraction as b, function_calling as a

    monkeypatch.setattr(a, "build_request", lambda text, mode="ANY": _with_text(data["A"], text))
    monkeypatch.setattr(b, "build_request", lambda text: _with_text(data["B"], text))
