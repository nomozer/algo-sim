# -*- coding: utf-8 -*-
"""Re-measure the two historical offline receipts this run's product change moves, as DELTA LAYERS (the receipts stay
byte-identical; the tests apply layers in order). 0 model calls: gold arm + offline replay only.

- `results/historical-gold-delta.json`   — `independent-nlu-extraction-evaluation` gold rows, after the
  `hybrid-master-backend-replacement` layer (consumer: tests/geometry/test_nlu_extraction_evaluation.py).
- `results/historical-regression-delta.json` — `semantic-extraction-v3-runtime-revision` 8 offline cells, after the
  `goal-directed-function-composition` layer (consumer: tests/geometry/test_hybrid_backend_integration.py::_after_delta).

Run from `backend/` (PYTHONIOENCODING=utf-8 ALLOW_LIVE_AI=0): python <this file>
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
RUN = Path(__file__).resolve().parents[1]
RUNS = ROOT / "docs/evaluation/geometry/runs"
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend/tests/geometry"))
AGG = ("e2e", "refusal_codes", "counts", "multi_goal")


def nlu_gold() -> dict:
    from scripts import run_nlu_extraction_evaluation as E
    rec = json.loads((E.RUN / "results/gold/gold_rows.json").read_bytes())["rows"]
    key = lambda r: (r["route"]["status"], r["route"]["code"], r["route"]["values"])  # noqa: E731
    state = {r["case_id"]: key(r) for r in rec}
    for layer in ("hybrid-semantic-extraction-v2", "semantic-extraction-schema-contract", "goal-directed-function-composition",
                  "geometry-capability-expansion", "source-gate-hardening", "hybrid-master-backend-replacement"):
        for c, d in json.loads((RUNS / layer / "results/historical-gold-delta.json").read_bytes())["changed"].items():
            state[c] = (d["after"]["status"], d["after"]["code"], d["after"]["values"])
    now = {r["case_id"]: key(r) for r in E.run_gold(E.load_inputs())}
    corpus = {c["id"]: c for c in json.loads((E.RUN / "inputs/corpus-authoring/corpus.json").read_bytes())["cases"]}
    changed = {}
    for c in state:
        if state[c] != now[c]:
            b, a = state[c], now[c]
            changed[c] = {"before": dict(zip(("status", "code", "values"), b)), "after": dict(zip(("status", "code", "values"), a)),
                          "split": corpus[c]["split"], "source_text": corpus[c]["source_text"],
                          "independent_expectation": corpus[c].get("expected_values")}
    return {"schema": "HISTORICAL_GOLD_REMEASURE/1",
            "measured_receipt": "docs/evaluation/geometry/runs/independent-nlu-extraction-evaluation/results/gold/gold_rows.json",
            "applies_after": "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/results/historical-gold-delta.json",
            "cause": "run hybrid-reasoning-generalization: engine `_tam_giac` Pythagoras over a right angle stated outside "
                     "the base / as perpendicular_lines with a shared endpoint, and `_dinh_tu_ba_canh_ben` (apex by three "
                     "lateral edges) — trirectangular tetrahedra are now laid out",
            "model_calls": 0, "rows_compared": len(now), "changed": changed}


def v3_matrix() -> dict:
    import test_hybrid_backend_integration as T
    from scripts import run_schema_contract_evaluation as R
    T.REGRESSION_DELTA_REASONING = {"v3_matrix": {"changed_cells": {}}}    # `before` = state the EARLIER layers left
    inp = R.V1.load_inputs(T.V3_REV_RUN / "inputs")
    cells = {}
    for mode in ("PILOT", "LOCKED"):
        for arm in ("flat", "v3"):
            h = R.harness(arm, inp, mode)
            gold_rows = h.run_gold(inp)
            scores = {f"gold-{arm}-{mode}": R.E.summarize(inp, gold_rows, gold_rows)}
            with tempfile.TemporaryDirectory() as tmp:
                st = h.run_eval(inp, mode, h.ReplayProvider(inp), Path(tmp))
            scores[f"replay-{arm}-{mode}"] = R.E.summarize(inp, st["rows"], gold_rows)
            for cell, now in scores.items():
                prev = T._after_delta(cell, json.loads((T.V3_REV_RUN / f"results/offline/{cell}/score.json").read_bytes()))
                rows = {b["case_id"]: {"before": b, "after": a} for b, a in zip(prev["rows"], now["rows"]) if a != b}
                if rows or any(prev[k] != now[k] for k in AGG):
                    cells[cell] = {"before": {k: prev[k] for k in AGG}, "after": {k: now[k] for k in AGG}, "rows": rows}
    return {"schema": "HISTORICAL_REGRESSION_REMEASURE/1", "model_calls": 0,
            "v3_matrix": {"baseline": "docs/evaluation/geometry/runs/semantic-extraction-v3-runtime-revision/results/offline",
                          "applies_after": "docs/evaluation/geometry/runs/goal-directed-function-composition/results/"
                                           "historical-regression-delta.json",
                          "cells_compared": 8, "changed_cells": cells}}


def main() -> None:
    for name, data in (("historical-gold-delta.json", nlu_gold()), ("historical-regression-delta.json", v3_matrix())):
        p = RUN / "results" / name
        p.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("WROTE", p)


if __name__ == "__main__":
    main()
