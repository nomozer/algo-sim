# -*- coding: utf-8 -*-
"""Per-row layer attribution of LIVE_LOCKED and the gold arm → `layer_rows.json` (analysis; the frozen score is untouched).

Layer = which stage stopped the row, from its refusal code, with two receipt-checked refinements:
- a Planner `UNSUPPORTED_CAPABILITY` raised on a live request that has no operands is an extraction failure (the
  planner reads a missing operand as a plane; review finding L19), not a capability gap;
- `CONDITIONAL_CLAUSE` from the planner's role gate (a fact the extractor marked `condition`) is planner input, the
  same code from the source gate (`registry.kiem_nguon`) is Source Grounding — told apart by the reason text.
`correct_refusal` marks rows whose refusal is the right disposition (e.g. inconsistent or missing data), so an engine
stop there is not counted as a capability gap. Extraction correctness is reported under both scorers.

    cd backend && python ../docs/evaluation/geometry/runs/independent-nlu-extraction-evaluation/results/live-locked/attribute_layers.py
"""
from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
ROOT = RUN.parents[4]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


E = _load("E", ROOT / "backend/scripts/run_nlu_extraction_evaluation.py")
C = _load("C", RUN / "corrections/rescore_ignoring_unused_slots.py")

PARSE = {"JSON_INVALID", "RESPONSE_TRUNCATED", "PROVIDER_REFUSED", "NO_CANDIDATE", "MALFORMED_RESPONSE_PART"}
INPUT = {"SCHEMA_INVALID", "FACT_INCOMPLETE", "UNKNOWN_SOLID", "AMBIGUOUS_FACT", "AMBIGUOUS_REFERENCE", "DEGENERATE_LINE",
         "UNKNOWN_DERIVED_REFERENCE", "DERIVED_REFERENCE_TYPE_MISMATCH"}
GROUNDING = {"QUOTE_NOT_IN_SOURCE", "UNKNOWN_LABEL", "GOAL_CLAUSE_NOT_PREMISE", "CONDITIONAL_CLAUSE", "NEGATED_CLAUSE",
             "PREDICATE_NOT_IN_QUOTE", "PLANE_NOT_IN_QUOTE", "ROLE_NOT_IN_QUOTE", "AMBIGUOUS_VALUE_QUOTE", "UNGROUNDED_VALUE",
             "SOURCE_OBJECT_MISMATCH", "SOURCE_PREMISE_UNREAD", "QUESTION_CONTEXT_UNSUPPORTED", "OBJECT_NOT_IN_QUOTE",
             "NOT_ASKED_IN_SOURCE", "REQUEST_NOT_ANSWERED", "QUESTION_LOCAL_GIVEN_UNVERIFIED", "QUESTION_LOCAL_GIVEN_CONFLICT"}
ENGINE = {"UNSUPPORTED_CAPABILITY", "UNSUPPORTED_BASE_SHAPE", "MISSING_DIMENSION", "UNDERDETERMINED_POINT",
          "FIGURE_NOT_UNIQUE", "PLANE_NOT_UNIQUE", "PLAN_TOO_LARGE", "INCONSISTENT_FACTS", "PARALLEL_NO_INTERSECTION",
          "PROOF_UNVERIFIABLE"}
_OPERANDS = ("points", "points_a", "points_b", "solid", "line_ref", "point")


def layer(route: dict, facts: list | None) -> str:
    if route["status"] == "SERVED":
        return "SERVED"
    code, reason = route["code"], route.get("reason") or ""
    if code in PARSE:
        return "PROVIDER_PARSE"
    if code == "OUT_OF_SCOPE":
        return "EXTRACTION_FLAGGED_UNSUPPORTED"
    if code == "CONDITIONAL_CLAUSE" and "không phải giả thiết vô điều kiện" in reason:
        return "PLANNER_INPUT"          # planner role gate: a fact the extractor marked `condition`
    if code == "UNSUPPORTED_CAPABILITY" and facts:
        fid = reason.split(":", 1)[0].strip()
        f = next((x for x in facts if isinstance(x, dict) and x.get("id") == fid), None)
        if f is not None and f.get("kind") == "question" and not any(f.get(k) for k in _OPERANDS):
            return "PLANNER_INPUT"      # request without operands read as plane–plane: extraction failure
    if code in INPUT:
        return "PLANNER_INPUT"
    if code in GROUNDING:
        return "SOURCE_GROUNDING"
    if code in ENGINE:
        return "PLANNER_ENGINE"
    return f"UNMAPPED:{code}"


def main() -> None:
    inp = E.load_inputs()
    manifest = RUN / "results/live-locked/manifest.json"
    gold_rows = json.loads((RUN / "results/gold/gold_rows.json").read_bytes())["rows"]
    gby = {r["case_id"]: r for r in gold_rows}
    frozen = {s["case_id"]: s for s in C.score(manifest, gold_rows, inp, False)["scored"]}
    relaxed = {s["case_id"]: s for s in C.score(manifest, gold_rows, inp, True)["scored"]}
    gscore = {s["case_id"]: s for s in E.summarize(inp, gold_rows, gold_rows)["scored"]}
    rows = []
    for r in json.loads(manifest.read_bytes())["rows"]:
        cid, case = r["case_id"], inp["cases"][r["case_id"]]
        g = gby[cid]
        rows.append({"case": cid, "group": case["group"], "disposition": E.effective_disposition(case),
                     "live_layer": layer(r["route"], r["facts"]), "live_code": r["route"]["code"],
                     "gold_layer": layer(g["route"], g["facts"]), "gold_code": g["route"]["code"],
                     "live_e2e_frozen": frozen[cid]["e2e"], "live_e2e_relaxed": relaxed[cid]["e2e"],
                     "gold_e2e": gscore[cid]["e2e"],
                     "live_extraction_correct_frozen": (frozen[cid]["extraction"] or {}).get("correct"),
                     "live_extraction_correct_relaxed": (relaxed[cid]["extraction"] or {}).get("correct"),
                     "correct_refusal": relaxed[cid]["e2e"] == "SAFE_REFUSAL"})
    dest = HERE / "layer_rows.json"
    if dest.exists():
        raise SystemExit(f"{dest} exists — never overwritten")
    dest.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    live = Counter(x["live_layer"] for x in rows)
    print("live layer:", dict(live))
    print("gold layer:", dict(Counter(x["gold_layer"] for x in rows)))
    print("live layer × extraction correct (relaxed):",
          dict(Counter((x["live_layer"], x["live_extraction_correct_relaxed"]) for x in rows)))
    print("gold capability gaps (engine layer, not a correct refusal):",
          [x["case"] for x in rows if x["gold_layer"] == "PLANNER_ENGINE" and x["gold_e2e"] != "SAFE_REFUSAL"])
    print("gold engine stops that are correct refusals:",
          [x["case"] for x in rows if x["gold_layer"] == "PLANNER_ENGINE" and x["gold_e2e"] == "SAFE_REFUSAL"])
    print("same layer / same code in both arms (grounding):",
          sum(x["live_layer"] == x["gold_layer"] == "SOURCE_GROUNDING" for x in rows),
          sum(x["live_layer"] == x["gold_layer"] == "SOURCE_GROUNDING" and x["live_code"] == x["gold_code"] for x in rows))
    wrong = [x for x in rows if x["live_extraction_correct_relaxed"] is False]
    print("wrong-extraction rows by stopping layer:", dict(Counter(x["live_layer"] for x in wrong)),
          "| unsafe among them:", sum(x["live_e2e_relaxed"] in E.UNSAFE for x in wrong))


if __name__ == "__main__":
    main()
