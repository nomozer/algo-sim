# -*- coding: utf-8 -*-
"""Correction layer (post hoc, reported BESIDE the locked score, never instead of it).

Finding after LIVE_LOCKED: L01 was scored WRONG_SERVED although the route answered exactly the asked object (AC') with
the oracle value (13). The live facts differed from gold only in slots the planner never reads for that kind
(`planner._CAN`, `_khoi`): `measure` on a `question`, `points` on a `solid`, `right` on a cube/cuboid (implied). The
frozen fact key compared them, the question did not pair, and the correct answer counted as "unasked".

This script re-scores recorded rows with ONLY those slots neutralised. The runner, its identity, labels, gold, oracle
and the recorded rows are untouched; outputs go to `corrections/`. 0 model calls.

    cd backend && python ../docs/evaluation/geometry/runs/independent-nlu-extraction-evaluation/corrections/rescore_ignoring_unused_slots.py
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
ROOT = RUN.parents[4]
spec = importlib.util.spec_from_file_location("E", ROOT / "backend/scripts/run_nlu_extraction_evaluation.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)

UNUSED = {"question": ("measure", "shape", "solid_type", "right", "regular"),
          "solid": ("points",)}
_frozen_sig = E._sig


def relaxed_sig(f, by_id, depth=0):
    g = dict(f) if isinstance(f, dict) else f
    if isinstance(g, dict):
        for k in UNUSED.get(g.get("kind"), ()):
            g.pop(k, None)
        if g.get("kind") == "solid" and g.get("solid_type") in ("cube", "cuboid"):
            g.pop("right", None)          # implied by the type (`_khoi`: dung = right or regular or cube/cuboid)
    return _frozen_sig(g, by_id, depth)


def score(manifest_path: Path, gold_rows, inp, relaxed: bool):
    E._sig = relaxed_sig if relaxed else _frozen_sig
    try:
        return E.score_manifest(inp, json.loads(manifest_path.read_bytes()), gold_rows)
    finally:
        E._sig = _frozen_sig


def main() -> None:
    inp = E.load_inputs()
    gold_rows = json.loads((RUN / "results/gold/gold_rows.json").read_bytes())["rows"]
    out = {"schema": "SCORER_CORRECTION/1", "corrects": "results/live-locked/score.json, results/live-pilot/score.json",
           "rule": "neutralise slots the planner never reads: question.{measure,shape,solid_type,right,regular}; "
                   "solid.points; solid.right when solid_type is cube/cuboid",
           "locked_score_unchanged": True, "model_calls": 0, "runs": {}}
    for name in ("live-locked", "live-pilot"):
        mp = RUN / "results" / name / "manifest.json"
        a, b = score(mp, gold_rows, inp, False), score(mp, gold_rows, inp, True)
        changed = [{"case_id": x["case_id"], "sample": x["sample"], "frozen": [x["e2e"], x["cell"]], "relaxed": [y["e2e"], y["cell"]]}
                   for x, y in zip(a["scored"], b["scored"]) if (x["e2e"], x["cell"]) != (y["e2e"], y["cell"])]
        out["runs"][name] = {"frozen": {k: a[k] for k in ("e2e", "cells", "extraction")} | {"decision": a.get("decision")},
                             "relaxed": {k: b[k] for k in ("e2e", "cells", "extraction")} | {"decision": b.get("decision")},
                             "rows_changed": changed}
    dest = HERE / "scorer-unused-slots.json"
    if dest.exists():
        raise SystemExit(f"{dest} exists — never overwritten")
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for name, r in out["runs"].items():
        print(name, "rows changed:", r["rows_changed"])
        print("  frozen  e2e", r["frozen"]["e2e"], "decision", (r["frozen"]["decision"] or {}).get("answer"))
        print("  relaxed e2e", r["relaxed"]["e2e"], "decision", r["relaxed"]["decision"])
        print("  relaxed extraction", r["relaxed"]["extraction"])


if __name__ == "__main__":
    main()
