"""Lock on the shared live-acceptance harness (`docs/evaluation/geometry/harness/live-acceptance/`, run
`axo-hybrid-local-model1-finalization-test-consolidation`).

The harness replaced per-run copies whose default output was the run directory they sat in. Equivalence is shown on
the frozen /12 evidence: the oracle and the aggregator, run on /12 inputs, reproduce the /12 deliverables exactly
(only `schema`/`harness_version` keys were renamed); the samplers, proxy and bench are byte-copies of the /12 tools
apart from bench identity strings. Every tool refuses to write over existing output."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
H = ROOT / "docs/evaluation/geometry/harness/live-acceptance"
R12 = ROOT / "docs/evaluation/geometry/runs/axo-hybrid-compositional-geometry-language-grounded-simulation"
OUTPUTS = ("LIVE_ACCEPTANCE_RESULTS", "SLM_LIVE_CONTRIBUTION_AUDIT", "VISUAL_AND_INTERACTION_ACCEPTANCE",
           "NETWORK_ISOLATION_PROOF")


def _py(*args):
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8",
                          env=env, timeout=300)


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _norm(d):
    return {k: v for k, v in d.items() if k not in ("schema", "harness_version")}


def test_oracle_selfcheck_and_replay_reproduce_the_frozen_12_verification(tmp_path):
    assert _py(H / "scene_oracle.py", "--selfcheck").returncode == 0
    out = tmp_path / "oracle.json"
    r = _py(H / "scene_oracle.py", R12 / "V12_ACCEPTANCE_MANIFEST.json", R12 / "evidence/v12_responses.jsonl", out)
    assert r.returncode == 0, r.stderr[-2000:]
    assert _load(out)["results"] == _load(R12 / "SCENE_ORACLE_VERIFICATION.json")["results"]
    before = out.read_bytes()
    r = _py(H / "scene_oracle.py", R12 / "V12_ACCEPTANCE_MANIFEST.json", R12 / "evidence/v12_responses.jsonl", out)
    assert r.returncode != 0 and "refusing to overwrite" in r.stderr and out.read_bytes() == before


def test_aggregate_replay_on_12_inputs_equals_the_frozen_12_deliverables(tmp_path):
    out = tmp_path / "agg"
    r = _py(H / "aggregate.py", "--run-dir", R12, "--layout", "v12", "--out-dir", out,
            "--proxy-selfcheck-ok", "--proxy-selfcheck-records", "2")
    assert r.returncode == 0, r.stderr[-2000:]
    for name in OUTPUTS:
        fresh = _load(out / f"{name}.json")
        assert _norm(fresh) == _norm(_load(R12 / f"{name}.json")), name
    assert _load(out / "LIVE_ACCEPTANCE_RESULTS.json")["harness_version"] == "axo-live-acceptance-harness/1"
    r = _py(H / "aggregate.py", "--run-dir", R12, "--layout", "v12", "--out-dir", out)
    assert r.returncode != 0 and "refusing to write into non-empty" in r.stderr


def test_unchanged_tools_are_byte_copies_of_the_12_tools():
    for name in ("egress_blackhole_proxy.py", "stack_memory_sampler.ps1", "tcp_egress_sampler.ps1"):
        assert (H / name).read_bytes() == (R12 / "tools" / name).read_bytes(), name


def test_no_harness_tool_defaults_its_output_into_a_run_directory():
    for p in H.iterdir():
        if p.suffix in (".py", ".mjs"):
            text = p.read_text(encoding="utf-8")
            assert "runs/" not in text and "V12_ACCEPTANCE_MANIFEST" not in text.replace('"V12_ACCEPTANCE_MANIFEST.json"', ""), p.name
    shared = (H / "harness_paths.mjs").read_text(encoding="utf-8")
    assert "--out-dir is required" in shared and "refusing to write into non-empty" in shared
    for name in ("live_browser_acceptance.mjs", "ui_scenarios.mjs"):
        text = (H / name).read_text(encoding="utf-8")
        assert 'freshOutDir(ARGS.values["out-dir"])' in text and "process.env.AXO_" not in text, name
