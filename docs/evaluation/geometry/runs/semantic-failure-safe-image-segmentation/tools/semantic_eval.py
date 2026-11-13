"""Clause-level diagnostics, root-cause attribution and before/after on the DEVELOPMENT corpora of run
`semantic-failure-safe-image-segmentation` (never a locked W2/W3 row, never H-1).

  python semantic_eval.py <before_backend_dir> [--only-after]      # from the worktree root, backend interpreter
  python semantic_eval.py --child                                  # internal
Corpora: DEV (tools/semantic_dev_corpus.py, agent-written, development), REAL27 (25 controlled-vision transcriptions + 2
earlier fresh items, all exposed), PROBES (the 39 plane-constraint probes of the previous run, exposed). Diagnostics of
both sides are computed by the SAME module from each side's own parser telemetry, so the instrument is constant.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
RUNS = RUN.parent
sys.path[:0] = [str(Path(__file__).resolve().parent), str(RUNS / "independent-geometry-plane-constraints/tools")]

GOAL_OF = {"measure.volume": "volume", "measure.distance": "distance", "measure.angle_cos_sq": "angle", "measure.angle_cos": "angle",
           "measure.area": "area"}


def child() -> None:
    os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
    from app.ai.adaptive_input_router import route_text_input, normalize_problem_text, strip_trailing_multiple_choice_options
    from app.ai.local_geometry_parser import parse_geometry_problem_locally
    out = {}
    for k, t in json.loads(sys.stdin.read()).items():
        r = route_text_input(t, allow_live_ai=False).response
        rd = r.get("route_d") or {}
        norm = strip_trailing_multiple_choice_options(normalize_problem_text(t))
        lp = parse_geometry_problem_locally(norm)
        sc = (r.get("envelope") or {}).get("scene3d") or {}
        objs = sc.get("objects") or []
        goals = sorted({GOAL_OF.get(o.get("producer"), "other") for o in objs if o.get("type") == "quantity" and "target" in (o.get("display_group") or [])})
        if any(o["type"] == "section" for o in objs):
            goals.append("section")
        if any(o.get("producer") == "intersect_plane_plane" for o in objs):
            goals.append("intersection")
        out[k] = {"status": rd.get("status") or "REFUSED", "code": (rd.get("refusal") or {}).get("code") or r.get("reason_code"),
                  "parse_status": lp.status, "parse_reason": lp.reason_code, "fallback_reason": lp.fallback_reason,
                  "coverage": lp.source_coverage.to_dict(), "normalized_text": norm, "goals": goals,
                  "answers": rd.get("answers") if rd.get("status") == "SERVED" else None,
                  "section_vertices": sorted(len(o.get("polygon") or []) for o in objs if o["type"] == "section"),
                  "planner": rd.get("planner"), "unresolved_kinds": [u.get("kind") for u in (lp.payload or {}).get("unresolved") or []]}
    print(json.dumps(out, ensure_ascii=False, default=str))


def run(backend: Path, texts: dict) -> dict:
    env = {**os.environ, "PYTHONPATH": str(backend), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "ALLOW_LIVE_AI": "0", "GEMINI_API_KEY": ""}
    res = subprocess.run([sys.executable, __file__, "--child"], input=json.dumps(texts, ensure_ascii=False), capture_output=True,
                         text=True, cwd=backend, env=env, encoding="utf-8", check=True)
    return json.loads(res.stdout.strip().splitlines()[-1])


def corpora() -> dict[str, dict[str, dict]]:
    from semantic_dev_corpus import CORPUS
    from plane_constraint_probes import PROBES
    items = json.loads((RUNS / "controlled-vision-real-image-validation/new_in_scope_image_manifest.json").read_text(encoding="utf-8"))["items"]
    items += json.loads((RUNS / "local-semantic-source-gate-reliability/fresh_external_manifest.json").read_text(encoding="utf-8"))["items"]
    return {"DEV": {k: {"text": v["text"], "group": v["group"], "expect": v["expect"], "same_as": v.get("same_as")} for k, v in CORPUS.items()},
            "REAL27": {i["case_id"]: {"text": i["statement"], "group": "real_exposed", "expect": None} for i in items},
            "PROBES": {k: {"text": t, "group": c, "expect": (e[0], None)} for k, (c, e, t) in PROBES.items()}}


def diag(raw: dict) -> dict:
    sys.path.insert(0, str(ROOT / "backend"))
    from app.ai.local_failure_diagnostics import diagnose
    if raw["status"] == "SERVED":
        return {"root_cause": None}
    terminal = raw["code"]
    d = diagnose(parse_status=raw["parse_status"], parse_reason=raw["parse_reason"], fallback_reason=raw["fallback_reason"],
                 source_coverage=raw["coverage"], terminal_code=terminal, fallback_allowed=False, planner=raw.get("planner"),
                 unresolved_kinds=raw.get("unresolved_kinds"))
    return d


def layer_of(d: dict) -> str:
    rc = d.get("root_cause")
    if rc is None:
        return "SERVED"
    if rc in ("UNRECOGNIZED_GEOMETRIC_ENTITY",):
        return "ENTITY_RESOLUTION"
    if rc in ("UNRESOLVED_REFERENCE",):
        return "ENTITY_REFERENCE"
    if rc in ("UNRECOGNIZED_RELATION",):
        return "RELATION_EXTRACTION"
    if rc in ("UNRECOGNIZED_GOAL",):
        return "GOAL_EXTRACTION"
    if rc in ("UNSUPPORTED_GOAL_FUNCTION", "UNSUPPORTED_GOAL_KIND"):
        return "GOAL_UNDERSTOOD_UNSUPPORTED"
    if rc in ("INCOMPLETE_FACT_EXTRACTION",):
        return "CLAUSE_PARTIALLY_READ"
    if rc in ("SOURCE_PROVENANCE_MISSING",):
        return "SOURCE_GATE"
    if rc in ("INSUFFICIENT_CONSTRAINTS", "SOURCE_CONFLICT", "QUESTION_PREMISE_AMBIGUITY", "DIAGRAM_DEPENDENT_FACT"):
        return "SOURCE_FACTS"
    return "PLANNER_KERNEL"


def main(before: Path | None) -> int:
    cs = corpora()
    sides = {"after": ROOT / "backend"} | ({"before": before} if before else {})
    res = {side: {name: run(b, {k: v["text"] for k, v in items.items()}) for name, items in cs.items()} for side, b in sides.items()}
    now = datetime.now(timezone.utc).isoformat()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    cand = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
    meta = {"run_id": RUN.name, "generated_at_utc": now, "head": head, "measured_candidate_note": "development measurement on the working product; the frozen candidate identity is in candidate_freeze.json",
            "candidate_at_measurement": {"commit": cand["commit"], "measured_system": cand["measured_system"]["tree_hash"]},
            "environment": {"ALLOW_LIVE_AI": "0", "route": "route_text_input (local-first)"},
            "command": "python docs/evaluation/geometry/runs/semantic-failure-safe-image-segmentation/tools/semantic_eval.py <before_backend>",
            "dataset_partition": "DEVELOPMENT ONLY (DEV agent-written, REAL27 exposed, PROBES exposed); no locked W2/W3 row, no H-1",
            "oracle_status": "AGENT_DIAGNOSTIC (expected outcomes written by the agent from geometry and the product's documented scope)"}

    def put(name: str, data: dict) -> None:
        (RUN / name).write_text(json.dumps({**meta, **data}, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")

    diags = {side: {name: {k: diag(v) for k, v in r.items()} for name, r in by.items()} for side, by in res.items()}
    rows = {}
    for name, items in cs.items():
        for k, it in items.items():
            row = {"corpus": name, "id": k, "group": it["group"], "text_sha256": hashlib.sha256(it["text"].encode()).hexdigest()[:16]}
            for side in sides:
                raw, d = res[side][name][k], diags[side][name][k]
                row[side] = {"status": raw["status"], "terminal": raw["code"], "goals": raw["goals"], "root_cause": d.get("root_cause"),
                             "layer": layer_of(d), "first_loss_layer": d.get("first_loss_layer"), "detected_by": d.get("detected_by"),
                             "clauses_total": d.get("clauses_total"), "clauses_recognized": d.get("clauses_recognized"),
                             "clauses_unrecognized": d.get("clauses_unrecognized")}
                exp = it["expect"]
                if exp and exp[1] is not None and name == "DEV":
                    ok = (raw["status"] == "SERVED" and exp[1] in raw["goals"]) if exp[0] == "SERVED" else \
                         (raw["status"] != "SERVED" and d.get("root_cause") == exp[1])
                    row[side]["meets_expectation"] = ok
                elif exp and name == "PROBES":
                    row[side]["meets_expectation"] = (raw["status"] == "SERVED") == (exp[0] == "SERVED")
            rows[f"{name}:{k}"] = row

    # metamorphic agreement (DEV `same_as`): same outcome, same goals, same answers / section vertex counts
    meta_rows = []
    for k, it in cs["DEV"].items():
        if not it["same_as"]:
            continue
        for side in sides:
            a, b = res[side]["DEV"][k], res[side]["DEV"][it["same_as"]]
            agree = a["status"] == b["status"] and a["goals"] == b["goals"] and a["answers"] == b["answers"] and a["section_vertices"] == b["section_vertices"]
            meta_rows.append({"id": k, "base": it["same_as"], "side": side, "agree": agree, "status": a["status"], "base_status": b["status"]})

    def summary(side: str, name: str) -> dict:
        rs = [r for r in rows.values() if r["corpus"] == name]
        s = {"items": len(rs), "served": sum(r[side]["status"] == "SERVED" for r in rs),
             "by_layer": dict(Counter(r[side]["layer"] for r in rs)), "by_root_cause": dict(Counter(str(r[side]["root_cause"]) for r in rs)),
             "fully_recognized": sum((r[side]["clauses_unrecognized"] or 0) == 0 and r[side]["root_cause"] not in ("INCOMPLETE_FACT_EXTRACTION",) for r in rs),
             "partially_recognized": sum(bool(r[side]["clauses_recognized"]) and bool(r[side]["clauses_unrecognized"]) for r in rs),
             "missing_clauses": sum(r[side]["clauses_unrecognized"] or 0 for r in rs)}
        if any("meets_expectation" in r[side] for r in rs):
            s["meets_expectation"] = sum(bool(r[side].get("meets_expectation")) for r in rs)
        return s

    summ = {side: {name: summary(side, name) for name in cs} for side in sides}
    clause_rows = {f"DEV:{k}": diags["after"]["DEV"][k].get("clauses") for k in cs["DEV"]} | \
                  {f"REAL27:{k}": diags["after"]["REAL27"][k].get("clauses") for k in cs["REAL27"]}
    put("clause_level_semantic_diagnostics.json", {
        "instrument": "backend/app/ai/local_failure_diagnostics.py (local-failure-diagnostics/1)",
        "clause_fields": ["clause_id", "start_offset", "end_offset", "parser_classification", "semantic_status", "clause_type", "clause_type_cues",
                          "role", "labels", "plane_names", "unresolved_plane_names", "downstream_dependency", "failure_reason"],
        "segmentation": "the parser's own clause splitter (sentence ends, ';', and clause-level commas it already uses); offsets are into the normalized text the parser read",
        "refused_items_after": {k: v for k, v in clause_rows.items() if v}})
    put("end_to_end_failure_attribution.json", {
        "rule": "root cause = the first layer that lost information (parser coverage, a fact the gate could not ground, schema), else the layer that refused a fully read problem (source facts, planner, kernel); terminal reason kept separately",
        "rows": [r for r in rows.values() if r["corpus"] in ("REAL27", "DEV")]})
    put("semantic_root_cause_matrix.json", {"summary": summ,
        "layer_meaning": {"ENTITY_RESOLUTION": "an object/point/plane definition not read", "ENTITY_REFERENCE": "a name used but never defined",
                          "RELATION_EXTRACTION": "a relation/property clause not read", "GOAL_EXTRACTION": "the question not read or read as another object",
                          "GOAL_UNDERSTOOD_UNSUPPORTED": "the question is read but its output (cos/tan of an angle) is outside output-policy/1",
                          "CLAUSE_PARTIALLY_READ": "the parser claimed a clause the gate found partly unread", "SOURCE_GATE": "a parser fact whose quote does not ground it",
                          "SOURCE_FACTS": "read correctly; the givens are insufficient / contradictory / ambiguous", "PLANNER_KERNEL": "read correctly; construction unsupported or degenerate"}})
    put("semantic_repair_before_after.json", {"summary": summ,
        "dev_expectation_rows": {r["id"]: {s: r[s].get("meets_expectation") for s in sides} for r in rows.values() if r["corpus"] == "DEV"}})
    put("semantic_negative_and_metamorphic_tests.json", {
        "metamorphic": meta_rows,
        "metamorphic_agreement": {side: f"{sum(m['agree'] for m in meta_rows if m['side'] == side)}/{sum(m['side'] == side for m in meta_rows)}" for side in sides},
        "negatives": {r["id"]: {s: {"status": r[s]["status"], "root_cause": r[s]["root_cause"]} for s in sides}
                      for r in rows.values() if r["corpus"] == "DEV" and cs["DEV"][r["id"]]["expect"][0] == "REFUSED"},
        "wrong_served_dev_negatives": {s: [r["id"] for r in rows.values() if r["corpus"] == "DEV" and cs["DEV"][r["id"]]["expect"][0] == "REFUSED" and r[s]["status"] == "SERVED"] for s in sides}})
    put("semantic_development_corpus_manifest.json", {
        "partition": {"DEV": "NEW_DIAGNOSTIC_DEVELOPMENT (agent-written in this run; never blind)", "REAL27": "DEVELOPMENT_EXPOSED", "PROBES": "DEVELOPMENT_EXPOSED"},
        "items": {name: {k: {"group": v["group"], "expect": v["expect"], "same_as": v.get("same_as"), "text_sha256": hashlib.sha256(v["text"].encode()).hexdigest()}
                         for k, v in items.items()} for name, items in cs.items()},
        "groups": dict(Counter(v["group"] for v in cs["DEV"].values())),
        "source_file": "tools/semantic_dev_corpus.py", "locked_rows_used": 0, "h1_rows_used": 0})
    print(json.dumps(summ, ensure_ascii=False))
    print("metamorphic", {side: f"{sum(m['agree'] for m in meta_rows if m['side'] == side)}/{sum(m['side'] == side for m in meta_rows)}" for side in sides})
    return 0


if __name__ == "__main__":
    if "--child" in sys.argv:
        child()
        raise SystemExit(0)
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "--only-after" else None))
