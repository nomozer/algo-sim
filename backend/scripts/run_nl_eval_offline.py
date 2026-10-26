# -*- coding: utf-8 -*-
"""Offline replay runner for the Vietnamese NL → TypedFacts V2 evaluation (run `hybrid-v2-nl-certificates-e2e`).

    cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/run_nl_eval_offline.py <dataset.json> --out <fresh.json>

Arms (all 0 provider calls):
  GOLD    the extraction IS the gold payload — measures validation, Source Gate, planner and exact engine alone
  STRESS  `stress_payloads` / `stress_payloads_must_refuse` of an item — unfaithful extractions the gate must not serve
`--live` is refused: a live extraction needs its own protocol and a separate Owner GO (LIVE_PROVIDER_GO_REQUIRED).
Refuses to overwrite an existing artifact (a measurement that cannot be re-run silently is the point).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import nl_eval_scoring as SC  # noqa: E402


def stress_rows(items: list[dict]) -> list[dict]:
    from app.ai.typed_fact_next_extraction import ReplayExtractor

    rows = []
    for it in items:
        stress = [(p, it["gold"]["expectation"]) for p in it.get("stress_payloads", [])]
        stress += [(p, {"disposition": "REFUSE", "category": "UNSUPPORTED", "allowed_codes": []})
                   for p in it.get("stress_payloads_must_refuse", [])]
        for n, (payload, expectation) in enumerate(stress):
            variant = {**it, "id": f"{it['id']}#stress{n}", "problem_text": payload["problem_text"],
                       "gold": {**it["gold"], "expectation": expectation, "payload": payload}}
            row = SC.run_item(variant, ReplayExtractor({payload["problem_text"]: payload}))
            rows.append(row)
    return rows


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset")
    ap.add_argument("--out", required=True)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--max-items", type=int, default=10_000)
    a = ap.parse_args(argv)
    if a.live:
        print(SC.LIVE_PROVIDER_GO_REQUIRED)
        return 3
    out = Path(a.out)
    if out.exists():
        print("refusing to overwrite", out)
        return 2
    data = json.loads(Path(a.dataset).read_text(encoding="utf-8"))
    items = data["items"]
    if errs := SC.validate_dataset(items):
        print("INVALID DATASET:", *errs, sep="\n  ")
        return 2
    gold = SC.run_dataset(items, SC.gold_extractor, SC.StopPolicy(a.max_items, stop_on_incorrect_served=False))
    stress = stress_rows(items)
    report = {"schema": "nl-eval-report/1", "dataset_sha256": SC.dataset_sha256(items), "claim_ceiling": SC.claim_ceiling(items),
              "provider_calls": 0, "gold_arm": {"summary": gold["summary"], "rows": gold["rows"]},
              "stress_arm": {"summary": SC.summarize(stress) if stress else None, "rows": stress}}
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"claim_ceiling": report["claim_ceiling"], "gold": gold["summary"]["outcomes"],
                      "stress": (report["stress_arm"]["summary"] or {}).get("outcomes")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
