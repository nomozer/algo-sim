# -*- coding: utf-8 -*-
"""Schema-Contract v3 evaluation: paired response-contract arms on the SAME product prompt — `flat` (the product
contract) vs `v3` (kind/goal anyOf contract). The difference between arms is therefore the schema effect alone.

Reuses scorer /2 (`run_semantic_extraction_evaluation`) and the frozen executor unchanged; one arm per process; live
only with an owner approval naming the exact arm identity; raw live output only under git-ignored `.superpowers/`.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from scripts import run_semantic_extraction_evaluation as E  # noqa: E402

V1 = E.V1
RUN = ROOT / "docs/evaluation/geometry/runs/semantic-extraction-schema-contract"
ARMS = ("flat", "v3")


def harness(arm, inp):
    """Scorer /2 harness with the product prompt; the arm only selects the provider response contract."""
    from app.ai import fact_extraction as fx
    if arm not in ARMS:
        raise ValueError(f"unknown arm {arm!r}")
    h = E.harness("v2", inp)          # product prompt (`_PRODUCT_PROMPT`), route record, persistence, base identity
    fx.RESPONSE_CONTRACT = arm        # set on every call: an earlier arm in the same process never leaks
    base = h.identity
    if arm == "v3":
        # The GOLD ceiling of an arm is "perfect extraction the arm's contract can express": a gold payload v3 cannot
        # carry is refused exactly as the live check would refuse it, never assumed expressible.
        from app.simulation.geometry_functions import KetQuaTuyen
        contract, gold_route = fx.facts_response_schema("v3"), h.run_gold

        def run_gold(data):
            rows = gold_route(data)
            for r in rows:
                if not fx.schema_accepts(contract, h.gold_payload(data, r["case_id"])):
                    r["route"] = h.route_record(KetQuaTuyen("REFUSED", "RESPONSE_CONTRACT_INVALID", "gold not expressible in v3"))
            return rows
        h.run_gold = run_gold

    def identity(data, mode):
        return {**base(data, mode), "arm": arm, "contract": arm, "contract_runner_sha256": V1._lf_sha(Path(__file__))}
    h.identity = identity
    return h


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["identity", "gold", "replay", "live", "score"])
    p.add_argument("--arm", choices=ARMS, default="v3")
    p.add_argument("--mode", choices=["PILOT", "LOCKED"], default="PILOT")
    p.add_argument("--inputs", type=Path, default=RUN / "inputs")
    p.add_argument("--out", type=Path)
    p.add_argument("--manifest", type=Path)
    p.add_argument("--approval", type=Path)
    args = p.parse_args()
    inp = E.load_inputs(args.inputs)
    h = harness(args.arm, inp)
    if args.action == "identity":
        print(json.dumps(h.identity(inp, args.mode), indent=2))
        return
    if args.out is None or args.out.exists():
        raise V1.PilotStopped("OUTPUT_REQUIRED_OR_EXISTS")
    if args.action == "score":
        state = json.loads(args.manifest.read_bytes())
        if state["identity"] != h.identity(inp, args.mode) or state["rows_sha256"] != V1._sha(state["rows"]):
            raise V1.PilotStopped("IDENTITY_MISMATCH")
    elif args.action == "gold":
        rows = [r for r in h.run_gold(inp) if inp["cases"][r["case_id"]]["split"] == h.MODES[args.mode][0]]
        state = {"execution_class": "GOLD", "identity": h.identity(inp, args.mode), "rows": rows, "rows_sha256": V1._sha(rows),
                 "live_model_calls": 0}
    else:
        if args.action == "live" and not args.out.resolve().is_relative_to(ROOT / ".superpowers"):
            raise V1.PilotStopped("LIVE_RAW_OUTPUT_REQUIRES_IGNORED_DIRECTORY")
        if args.action == "live":
            import app.persistence.db  # noqa: F401 — the product's own loader of backend/.env (key never printed)
        provider = h.live_provider(inp, args.mode, args.approval) if args.action == "live" else h.ReplayProvider(inp)
        secrets = (os.environ["GEMINI_API_KEY"],) if args.action == "live" else ()
        state = h.run_eval(inp, args.mode, provider, args.out, secrets=secrets)
    args.out.mkdir(parents=True, exist_ok=True)
    if args.action == "gold":
        V1._persist(args.out / "manifest.json", state, ())
    gold_rows = state["rows"] if args.action == "gold" else h.run_gold(inp)
    score = E.summarize(inp, state["rows"], gold_rows)
    score["schedule"] = E.validate_schedule(state, h.schedule(inp, args.mode))
    E.write_score(args.out, state, score)
    print(json.dumps({"action": args.action, "arm": args.arm, "rows": len(state["rows"]),
                      "live_model_calls": state.get("live_model_calls", 0), "e2e": score["e2e"]}))


if __name__ == "__main__":
    main()
