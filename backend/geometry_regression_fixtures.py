"""Explicit split-candidate pytest plugin for a research branch; no production hook.

The immutable A/B runner's budgets refer to its OLD provider surface, not the
expanded Registry. Supply ALGOSIM_FROZEN_AB_WORKTREE to test that exact surface
while all other tests (including expansion adapters) keep the current surface.
Without the opt-in, runner tests continue to test current payloads normally.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def frozen_ab_payloads():
    root = Path(os.environ["ALGOSIM_FROZEN_AB_WORKTREE"]).resolve()
    command = "from app.ai import function_calling as a,fact_extraction as b; from scripts.freeze_evaluation_candidate import measured_system_hash; import json; print(json.dumps({'A':a.build_request(''),'B':b.build_request(''),'product':measured_system_hash()[0]}))"
    result = subprocess.run([sys.executable, "-c", command], cwd=root / "backend", capture_output=True,
                            encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8", "ALLOW_LIVE_AI": "0"}, check=True)
    data = json.loads(result.stdout)
    assert data["product"] == "12da4768495572d7b4d04af733edf0c787337a6ab486ce2cae42f7c94bbbce52"
    for arm in ("A", "B"):
        data[arm].pop("contents")
    return data


@pytest.fixture(autouse=True)
def locked_runner_surface(request, monkeypatch):
    if not os.environ.get("ALGOSIM_FROZEN_AB_WORKTREE") or request.module.__name__.split(".")[-1] not in {
        "test_hybrid_ab_pilot_runner", "test_hybrid_ab_pilot_mutations"}:
        return
    data = request.getfixturevalue("frozen_ab_payloads")
    from app.ai import function_calling as a, fact_extraction as b
    def build(arm, text):
        return {**copy.deepcopy(data[arm]), "contents": [{"role": "user", "parts": [{"text": f'Đề bài:\n"""\n{text}\n"""'}]}]}
    monkeypatch.setattr(a, "build_request", lambda text, mode="ANY": build("A", text))
    monkeypatch.setattr(b, "build_request", lambda text: build("B", text))
