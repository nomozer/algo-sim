"""Live-pilot readiness of the CURRENT provider surface (review I3, 2026-10-11): NO-GO, locked as a test.

Three questions are kept apart:
  1. Does the locked A/B pilot still reproduce? — `test_hybrid_ab_pilot_runner` / `_mutations`, pinned to the frozen,
     hash-verified surface by `geometry_regression_fixtures`.
  2. Is the current product correct? — the product/geometry suites, on the current adapters.
  3. May the current surface run a live pilot under the locked caps? — here. The expanded registry (27 functions)
     makes the SMOKE_AB reservation exceed the pre-registered 500 000 accounted-token cap; the runner must refuse
     before any request, and the caps must not move. A new pilot needs its own pre-registered budget.
"""
from __future__ import annotations

import pytest

from geometry_regression_fixtures import FROZEN_AB_MODULES, frozen_payloads, locked_surface_hashes
from scripts import run_hybrid_ab_pilot as R

LOCKED_SMOKE_TOKENS = 500_000


def _current_surface_hashes() -> dict[str, str]:
    from app.ai import fact_extraction as b, function_calling as a

    out = {}
    for arm, adapter in (("A", a), ("B", b)):
        payload = R.effective_payload(adapter.build_request(""))
        payload.pop("contents")
        out[arm] = R._sha(payload)
    return out


def test_locked_caps_are_unchanged():
    assert R.CAPS[R.PilotMode.SMOKE_AB].accounted_tokens == LOCKED_SMOKE_TOKENS
    assert R.CAPS[R.PilotMode.FULL_AB].accounted_tokens == 6_000_000


def test_frozen_surface_reproduces_the_locked_certification():
    frozen_payloads()  # raises unless both arms hash to the locked certification


@pytest.mark.parametrize("arm", ["A", "B"])
def test_a_tampered_frozen_surface_is_refused(arm, tmp_path, monkeypatch):
    """Mutant: the pin cannot hide a changed surface — one edited instruction and the reproduction refuses to run."""
    import json

    import geometry_regression_fixtures as G

    data = json.loads(G.FROZEN_SURFACE.read_text(encoding="utf-8"))
    data[arm]["generationConfig"]["temperature"] = 0.5
    tampered = tmp_path / "surface.json"
    tampered.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(G, "FROZEN_SURFACE", tampered)
    with pytest.raises(AssertionError, match=f"frozen surface {arm}"):
        G.frozen_payloads()


def test_current_surface_is_not_the_locked_surface():
    """The pinned surface is used for reproduction only because the current one really differs."""
    assert _current_surface_hashes() != locked_surface_hashes()


def test_current_surface_exceeds_the_locked_smoke_budget():
    audit = R.audit_reservations()
    smoke = audit[3072]["smoke"]["tokens"]
    assert smoke > LOCKED_SMOKE_TOKENS, smoke


def test_current_surface_cannot_complete_the_smoke_pilot(tmp_path):
    """With the CURRENT adapters the locked SMOKE_AB budget holds (TOKEN_CAP, cap never exceeded) but the pilot stops
    short of its 24 pre-registered calls — an incomplete pilot, so NO-GO. The calls made before the stop go to a fake
    transport here; against a real provider they would be spent, which is why the pilot is not authorized."""
    from tests.geometry import test_hybrid_ab_pilot_runner as RT  # its Fake transport stays the single source

    assert __name__.split(".")[-1] not in FROZEN_AB_MODULES
    fake = RT.Fake()
    result = R.run_pilot(R.PilotMode.SMOKE_AB, fake, tmp_path)
    assert result["stop_reason"] == "TOKEN_CAP"
    assert len(fake.calls) < 24
    assert result["live_model_calls"] == 0
