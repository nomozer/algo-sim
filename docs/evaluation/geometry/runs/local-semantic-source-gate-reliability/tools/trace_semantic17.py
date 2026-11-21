"""Layer-by-layer trace of the controlled-vision polyhedron statements the solver did not finish without AI.

Input: the previous run's frozen manifest (agent transcriptions, AGENT_TRANSCRIBED_UNVERIFIED) and its gap backlog.
For every case: clause classification with the parser's own guard notes, the typed facts the parser built (also
for partial parses), the Bridge / planner / Source Gate verdict when the parser reaches its Stage 8, and the first
failing layer. ALLOW_LIVE_AI stays 0; nothing calls a provider.  Run from backend/:
    python <tools>/trace_semantic17.py [--out NAME] [--cases all|backlog]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

os.environ["ALLOW_LIVE_AI"] = "0"
RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
PRIOR = RUN.parent / "controlled-vision-real-image-validation"
sys.path.insert(0, str(ROOT / "backend"))

from app.ai import local_geometry_parser as P  # noqa: E402
from app.ai.typed_fact_next_extraction import TypedFactNextValidationError, parse_typed_fact_next_v2  # noqa: E402
from app.simulation.geometry_functions import planner, registry  # noqa: E402
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2  # noqa: E402
from app.simulation.geometry_functions.registry import TuChoi  # noqa: E402


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def measured_system() -> str:
    sys.path.insert(0, str(ROOT / "backend/scripts"))
    import freeze_evaluation_candidate as F
    return F.measured_system_hash()[0]


def internal_parse(text: str) -> dict:
    """Same stages as the parser, but keeps what a partial parse built (the public result drops it)."""
    raw = P.normalize_problem_text(text)
    clauses = P.split_into_clauses(raw)
    builder = P._AstBuilder(raw)
    for clause in clauses:
        P._parse_clause_into_ast(builder, clause)
    return {"raw": raw, "clauses": [{"index": c.index, "text": c.text, "classification": c.classification, "notes": list(c.notes)} for c in clauses],
            "solids": builder.solids, "premises": builder.premises, "relations": builder.relations,
            "described_points": builder.described_points, "derived_sections": builder.derived_sections,
            "math_goals": builder.math_goals, "simulation_goals": builder.simulation_goals, "unresolved": builder.unresolved}


def downstream(payload: dict, raw: str) -> dict:
    """Schema -> Bridge -> planner -> Source Gate, each step recorded separately."""
    out: dict = {}
    try:
        spec = parse_typed_fact_next_v2(payload)
        out["schema"] = "VALID"
    except TypedFactNextValidationError as exc:
        return {"schema": f"INVALID:{exc.code}", "first_failure": "TYPED_FACT_SCHEMA"}
    try:
        bridged = bridge_v2(spec)
        out["bridge_facts"] = len(bridged["facts"])
        out["bridge_ambiguities"] = bridged["bridge"].get("ambiguities") if isinstance(bridged.get("bridge"), dict) else None
    except Exception as exc:  # noqa: BLE001
        return {**out, "bridge": f"{type(exc).__name__}:{getattr(exc, 'code', '')}", "first_failure": "BRIDGE"}
    try:
        plan = planner.lap_ke_hoach({"facts": bridged["facts"]}, raw)
        out["planner"] = {"calls": len(plan.calls), "goals": len(plan.goals), "negated": len(plan.negated)}
    except TuChoi as exc:
        return {**out, "planner": f"REFUSED:{exc.code}", "planner_reason": str(exc.reason)[:300], "first_failure": "PLANNER"}
    try:
        doc_quotes = tuple(q for g in (*plan.goals, *plan.negated) if g.get("call") for q in g["call"]["source"]["quotes"])
        calls = registry.doc_ke_hoach({"calls": plan.calls})
        token = registry._CHINH_SACH_XUAT.set(bridged["bridge"].get("output_policies"))
        try:
            registry.kiem_nguon(calls, raw, tuple(plan.auxiliary), doc_quotes)
        finally:
            registry._CHINH_SACH_XUAT.reset(token)
        out["source_gate"] = "ACCEPTED"
    except TuChoi as exc:
        return {**out, "source_gate": f"REFUSED:{exc.code}", "source_gate_reason": str(exc.reason)[:400], "first_failure": "SOURCE_GATE"}
    return out


def first_failure(result, internal, gate) -> str:
    if result.status == P.LOCAL_PARSE_COMPLETE and not internal["unresolved"]:
        return "NONE_LOCAL_PARSE_COMPLETE"
    if result.status == P.LOCAL_PARSE_AMBIGUOUS:
        return "PARSER_CLARIFICATION"
    if (result.reason_code or "").startswith("UNPARSED") or result.reason_code == "INCOMPLETE_SOLID_OR_GOAL":
        return "PARSER_COVERAGE"
    if result.reason_code == "EMPTY_SOLIDS":
        return "PARSER_COVERAGE"
    return gate.get("first_failure", "UNKNOWN")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="semantic17_case_diagnostics.json")
    parser.add_argument("--cases", choices=["backlog", "all"], default="backlog")
    args = parser.parse_args()
    manifest = {i["case_id"]: i for i in json.loads((PRIOR / "new_in_scope_image_manifest.json").read_text(encoding="utf-8"))["items"]}
    backlog = {c["case_id"]: c for c in json.loads((PRIOR / "geometry_capability_gap_backlog.json").read_text(encoding="utf-8"))["cases"]}
    diag = {c["case_id"]: c for c in json.loads((PRIOR / "transcription_solver_diagnostic.json").read_text(encoding="utf-8"))["cases"]}
    ids = [cid for cid in manifest if (args.cases == "all" or backlog.get(cid, {}).get("owning_layer") in ("LOCAL_PARSER_COVERAGE", "SOURCE_GATE"))]
    rows = []
    for cid in ids:
        item = manifest[cid]
        result = P.parse_geometry_problem_locally(item["statement"], use_cache=False)
        internal = internal_parse(item["statement"])
        payload = {"schema_version": "typed-fact-next/2", "problem_text": internal["raw"], "length_unit": P._detect_length_unit(internal["raw"]),
                   **{k: internal[k] for k in ("solids", "premises", "relations", "derived_sections", "simulation_goals", "math_goals")}}
        if internal["described_points"]:
            payload["described_points"] = internal["described_points"]
        gate = downstream(payload, internal["raw"]) if internal["solids"] else {"first_failure": "PARSER_COVERAGE", "schema": "NO_SOLID"}
        rows.append({
            "case_id": cid, "source_image_hash": item["sha256"], "problem_text": item["statement"],
            "transcription_verification_status": item["ground_truth_status"], "dataset_partition": item["partition"],
            "problem_type": item["tags"], "expected_answer": item["expected_answer"], "oracle_status": item["oracle"]["status"],
            "previous_layer_label": backlog.get(cid, {}).get("owning_layer"), "previous_reason_code": backlog.get(cid, {}).get("reason_code"),
            "local_parser": {"status": result.status, "reason_code": result.reason_code, "fallback_reason": (result.fallback_reason or "")[:300]},
            "clauses": internal["clauses"],
            "typed_facts_built": {k: internal[k] for k in ("solids", "premises", "described_points", "relations", "math_goals", "unresolved")},
            "downstream_on_built_facts": gate,
            "first_failure_layer": first_failure(result, internal, gate),
            "solve_on_transcription_previous_run": diag.get(cid, {}).get("scope_basis")})
        print(cid, rows[-1]["first_failure_layer"], result.reason_code, [c["notes"] for c in internal["clauses"] if c["notes"]], gate.get("source_gate") or gate.get("planner") or gate.get("first_failure"), flush=True)
    (RUN / args.out).write_text(json.dumps({
        "run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "head": git("rev-parse", "HEAD"),
        "measured_system_working_tree": measured_system(), "input_manifest": "controlled-vision-real-image-validation/new_in_scope_image_manifest.json",
        "reference_status": "AGENT_TRANSCRIBED_UNVERIFIED (not human verified, not H-1)",
        "method": "Parser stages replayed in-process to keep partial typed facts; the downstream check runs Schema -> Bridge -> planner -> kiem_nguon on whatever the parser built.",
        "cases": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
