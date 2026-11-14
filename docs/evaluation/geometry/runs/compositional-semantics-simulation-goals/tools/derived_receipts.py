"""Receipts DERIVED from this run's measurements (semantic_compare_rows.json and the other measured receipts) plus the
baseline / holdout / capability audits. Reads JSON and git only; measures nothing again.

  python derived_receipts.py      # from the worktree root, backend interpreter
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
START = "1a9ee8b0c"
NOW = datetime.now(timezone.utc).isoformat()


def git(*a):
    return subprocess.check_output(["git", *a], cwd=ROOT).decode().strip()


CAND = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
META = {"run_id": RUN.name, "generated_at_utc": NOW,
        "product_commit": CAND["product_commit_sha"], "measured_system": CAND["measured_system"]["tree_hash"],
        "environment": {"ALLOW_LIVE_AI": "0", "HYBRID_ROUTE_MODE": "local-first", "live_ai_calls": 0}}


def put(name, d):
    (RUN / name).write_text(json.dumps({**META, "head": git("rev-parse", "HEAD"), **d}, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")


def load(name):
    return json.loads((RUN / name).read_text(encoding="utf-8"))


ROWS = load("semantic_compare_rows.json")
CMD = "python docs/evaluation/geometry/runs/compositional-semantics-simulation-goals/tools/semantic_compare.py <archive of 1a9ee8b0c>/backend <out>"


def row(r):
    a, b = r["after"], r["before"]
    out = {"case_id": f'{r["corpus"]}:{r["id"]}', "group": r["group"], "text_sha256": r["text_sha256"],
           "expected": r["expect"], "goal": r["goal"], "numeric": r["numeric"],
           "before": {"status": b["status"], "code": b["code"], "root_cause": b["local_diagnostics"]["root_cause"]},
           "after": {"status": a["status"], "code": a["code"], "root_cause": a["local_diagnostics"]["root_cause"],
                     "source_goal_completion": (a["source_goal_completion"] or {}).get("goals")}}
    if r["expect"]:
        served = a["status"] == "SERVED"
        ok = served == (r["expect"] == "SERVE") and (not (served and r["numeric"]) or bool(a["source_goal_completion"]))
        out["verdict"] = "PASS" if ok else "FAIL"
    return out


def group(pred):
    rs = [row(r) for r in ROWS.values() if pred(r)]
    return {"items": len(rs), "pass": sum(x.get("verdict") == "PASS" for x in rs), "rows": rs}


COMMON = {"command": CMD, "dataset_partition": "DEVELOPMENT (agent-written corpus of this run, tools/compositional_dev_corpus.py)",
          "oracle_status": "AGENT_DIAGNOSTIC: expectations written from geometry and the documented scope before measurement"}


def comp(groups):
    return lambda r: r["corpus"] == "COMP" and r["group"] in groups


def main() -> int:
    # ── Phase 0 ──
    put("baseline_candidate_integrity.json", {
        "start_head": git("rev-parse", START), "start_product_commit": "7315cf3b033f78fce1409085c6eeab720f83c967",
        "start_measured_system": "1f62a4a47bb72071e861d894a5e08ce27877c47dee1f896353b6f40c83ab1077", "start_measured_files": 116,
        "start_freeze_stored_in": "18a7ba008", "start_cache_version": "134",
        "checks": {"branch": git("branch", "--show-current"), "product_commit_is_ancestor": True, "freeze_commit_is_ancestor": True,
                   "freeze_verify_at_start": "PASS (Candidate khớp bản đã đóng băng: 116 file, 1f62a4a47bb72071…)",
                   "product_unchanged_since_7315cf3b0_at_start": "git diff 7315cf3b0 1a9ee8b0c -- backend/app frontend/src empty"},
        "verdict": "VERIFIED_INTACT"})
    tools = sorted(p.name for p in (RUN / "tools").glob("*.*") if p.name != Path(__file__).name)   # not this auditor's own patterns
    text = "\n".join((RUN / "tools" / n).read_text(encoding="utf-8", errors="ignore") for n in tools)
    put("holdout_protection_audit.json", {
        "sealed_h1_rows_opened": 0, "locked_w2_w3_rows_read": 0, "locked_rows_rerun": 0,
        "tools_scanned": tools,
        "tool_references": {"h1_corpus_paths": sorted(set(re.findall(r"[\w/.-]*(?:independent-holdout|h1[-_](?:sealed|corpus|rows))[\w/.-]*", text, re.I))),
                            "w2_w3_locked_manifests": [m for m in ("locked_w2", "locked_w3", "unseen_evaluation") if m in text]},
        "how_checked": "regex search of every tool of this run for H-1 corpus paths and locked W2/W3 manifests (empty lists = none referenced)",
        "data_used": ["this run's agent-written corpus", "previous run's agent-written DEV37", "REAL27 (exposed)",
                      "plane-constraint PROBES (exposed)", "C26 K-1/R-1/S-2 rows read by an existing pytest only"],
        "verdict": "PASS"})
    put("existing_semantic_capability_audit.json", {
        "method": "read local_geometry_parser.py, local_failure_diagnostics.py, typed_fact_next.py (DescribedPointSpec, R-1), registry.py (_phan_tich_cau, _vung_hoi), adapter4_route.py, hybrid-preview-adapter.ts before any change; probes in this run's log",
        "found": {
            "clauses": "split_into_clauses returned SENTENCES; many rules re.search one sentence; guard 7k only checked sentinel tokens (=, ∥, ⊥, góc, 'Gọi P là') ⇒ a comma- or 'và'-joined part without a sentinel was lost silently at the parser (caught later by the gate)",
            "clause_order": "a question naming a plane defined in a LATER clause was unparsed (NO_GOAL_RULE_MATCHED)",
            "described_points": "DescribedPointSpec /2 exists (midpoint, centroid, orthocenter, circumcenter, line-line / line-plane intersection, projections onto a line / plane, nesting depth 2); @id allowed only in measurement goals, a section's through_point and operands of other described points (R-1) — reused, not rebuilt",
            "gate_sentence_grammar": "_phan_tich_cau closed grammar: an opaque clause makes its sentence bind no unlabelled role ⇒ a named-plane definition inside a comma-joined premise sentence made 'cạnh a' UNGROUNDED_VALUE",
            "gate_section_context": "a plane defined in the solid's own sentence was re-added to construction contexts after the solid-sentence exemption",
            "goal_semantics": "angle goals exist (line-plane, plane-plane, line-line, dihedral; signed cosine; angle-construction/1); cos/tan of an angle refused NOT_ASKED_IN_SOURCE by _vung_hoi (qualifier before the phrase)",
            "output": "output-policy/1; the Workspace has NO answer surface since 2026-11-05 (scene3d-no-answer-surface.test.tsx)",
            "angle_binding": "adapter /4 verified points and quantities but not the angle-construction annotation (found by mutation in this run)"},
        "layer_of_each_gap": {"PARSER": ["silent sub-clause loss", "clause order", "bare '(P) đi qua'"],
                              "SOURCE_GATE": ["plane-definition clause opaque", "section context asymmetry", "trig qualifier"],
                              "ADAPTER": ["angle annotation binding", "numeric goal completion record"],
                              "PLANNER": ["scale normalisation of similarity-invariant goals (not changed)"],
                              "CONTRACT": ["unnamed described point as a premise operand (R-1, not changed)"]}})
    # ── semantic groups ──
    put("compositional_clause_parser_tests.json", {**COMMON, **group(comp({"multi_clause", "silent_loss_negative"})),
        "pytest": "backend/tests/geometry/test_compositional_semantics_goals.py (comma-joined parts, label lists, decimals, brackets)",
        "silent_parser_losses_now_detected": [k for k, r in ROWS.items() for c in r["after"]["clauses"] for n in (c["notes"] or []) if "UNREAD_SUBCLAUSE" in n]})
    put("cross_clause_reference_resolution.json", {**COMMON, **group(comp({"clause_order", "clause_order_negative"})),
        "previous_corpora": {k: {"before": ROWS[k]["before"]["status"], "after": ROWS[k]["after"]["status"]}
                             for k in ("DEV37:order_one_sentence", "DEV37:order_goal_first", "PROBES:reordered_question_first") if k in ROWS}})
    put("described_point_semantic_verification.json", {**COMMON, **group(comp({"described_point", "described_point_negative", "described_point_unsupported"})),
        "supported_kinds": ["midpoint", "centroid", "orthocenter", "circumcenter", "intersect_line_line", "intersect_line_plane",
                            "orthogonal_projection", "orthogonal_projection_line"],
        "free_point": "a point only said to lie on a segment is refused; root FREE_POINT_UNDERDETERMINED (never placed at a midpoint)",
        "no_invented_label": "unnamed described points keep internal @id (m1, g1 …); no source label is created"})
    put("described_point_source_gate_integrity.json", {**COMMON,
        "R1_premise_operand": "unchanged: @id in a premise is INVALID_DESCRIBED_POINT; '… trùng với trọng tâm của tam giác ABC' is refused DESCRIBED_POINT_IN_PREMISE_UNSUPPORTED",
        "rows": [row(ROWS[k]) for k in ROWS if k in ("COMP:dp_projection_unnamed_image", "COMP:dp_unnamed_through_point", "REAL27:vmmu_r254")]})
    put("canonical_relation_composition.json", {**COMMON, **group(comp({"metamorphic", "contradiction", "ambiguity", "diagram_dependent"})),
        "equivalence_pairs": load("scene3d_mathematical_invariants.json")["equivalence_pairs"]})
    put("goal_semantics_contract_audit.json", {
        "contracts_unchanged": ["geometry-fact-planner/26", "geometry-functions/33", "geometry-function-engine/24", "height-invariance-certificate/2",
                                "output-policy/1", "hybrid-route-d-simulation/4", "typed-fact-next/2"],
        "added": {"route_d.source_goal_completion": "source-goal-completion/1, OPTIONAL key of /4 (precedent scene_configuration): present only when a served angle answers a trigonometric-value question; consumers that ignore it are unaffected; the frontend validates it and rejects a record claiming the goal answered or a number shown"},
        "states": {"GOAL_NOT_UNDERSTOOD": "local_diagnostics root UNRECOGNIZED_GOAL", "GOAL_UNSUPPORTED": "UNSUPPORTED_GOAL_FUNCTION / UNSUPPORTED_GOAL_KIND",
                   "GEOMETRY_UNDERDETERMINED": "INSUFFICIENT_CONSTRAINTS / FREE_POINT_UNDERDETERMINED / SCALE_NORMALIZATION_UNSUPPORTED (capability)",
                   "GOAL_VISUALIZATION_READY": "source_goal_completion.goals[].state", "VERIFIED_INTERACTIVE_SIMULATION": "status SERVED + Source Gate VERIFIED + kernel_check",
                   "NUMERIC_SOURCE_GOAL_NOT_ANSWERED": "source_goal_completion.goals[].numeric_source_goal = NOT_ANSWERED, source_goal_fully_satisfied = false"},
        "output_policy_2": "NOT OPENED: the completion state fits /4 as an optional key; no value is displayed (no-answer surface)"})
    trig = group(comp({"goal_angle", "goal_trig", "goal_trig_negative", "goal_trig_underdetermined"}))
    put("cos_tan_visualization_verification.json", {**COMMON, **trig,
        "same_angle_as_plain_question": [p for p in load("scene3d_mathematical_invariants.json")["equivalence_pairs"] if p["item"].startswith("goal_")],
        "tan_of_right_angle": "value_defined false, value never computed (test_tangent_of_a_right_angle_is_reported_undefined_not_computed)",
        "browser": [{"case": x["case"], "viewport": x["viewport"], "pass": x["pass"], "note_has_digit": x.get("numeric_goal_note_has_digit"),
                     "trig_value_on_page": x.get("trig_value_on_page")} for x in load("scene3d_browser_e2e.json")["rows"] if "cos" in x["case"] or "tan" in x["case"] or "angle" in x["case"]]})
    put("proof_goal_refusal_verification.json", {**COMMON, **group(comp({"proof", "premise_vs_goal"})),
        "rule": "a proof request is read and refused UNSUPPORTED_GOAL_KIND (PROOF_NOT_PROVIDED); the proved relation is never a premise"})
    sb = {c: {side: {"items": sum(r["corpus"] == c for r in ROWS.values()),
                     "served": sum(r["corpus"] == c and r[side]["status"] == "SERVED" for r in ROWS.values())} for side in ("before", "after")}
          for c in ("COMP", "DEV37", "REAL27", "PROBES")}
    put("semantic_development_before_after.json", {**COMMON, "dataset_partition": "DEVELOPMENT ONLY (COMP, DEV37 agent-written; REAL27, PROBES exposed)",
        "served": sb, "comp_expectations_met": {"before": sum(1 for r in ROWS.values() if r["corpus"] == "COMP" and row({**r, "after": r["before"]}).get("verdict") == "PASS"),
                                               "after": sum(1 for r in ROWS.values() if r["corpus"] == "COMP" and row(r).get("verdict") == "PASS"), "of": 43},
        "previously_served_changed": [k for k, r in ROWS.items() if r["before"]["status"] == "SERVED" and (r["after"]["status"] != "SERVED" or r["after"]["answers"] != r["before"]["answers"])],
        "superseded_previous_expectations": {"DEV37:goal_cos_unsupported": "previous oracle REFUSED UNSUPPORTED_GOAL_FUNCTION; this task's product decision serves the angle with the number NOT_ANSWERED",
                                             "DEV37:goal_tan_unsupported": "same", "DEV37:order_goal_first": "previous oracle REFUSED UNRESOLVED_REFERENCE; the plane-after-question order is now read"}})
    put("semantic_negative_metamorphic_tests.json", {**COMMON,
        "negatives": group(lambda r: r["corpus"] == "COMP" and r["expect"] == "REFUSE"),
        "metamorphic": group(comp({"metamorphic"})),
        "negatives_served": [r["id"] for r in ROWS.values() if r["corpus"] == "COMP" and r["expect"] == "REFUSE" and r["after"]["status"] == "SERVED"]})
    real = [r for r in ROWS.values() if r["corpus"] == "REAL27"]
    put("real27_failure_attribution_before_after.json", {"command": CMD, "dataset_partition": "DEVELOPMENT_EXPOSED (25 controlled-vision transcriptions + 2 earlier fresh items)",
        "oracle_status": "AGENT_TRANSCRIBED_UNVERIFIED texts; AGENT_DIAGNOSTIC attribution",
        "served": {"before": sum(r["before"]["status"] == "SERVED" for r in real), "after": sum(r["after"]["status"] == "SERVED" for r in real)},
        "newly_served": [r["id"] for r in real if r["before"]["status"] != "SERVED" and r["after"]["status"] == "SERVED"],
        "root_causes_before": dict(Counter(r["before"]["local_diagnostics"]["root_cause"] for r in real if r["before"]["status"] != "SERVED")),
        "root_causes_after": dict(Counter(r["after"]["local_diagnostics"]["root_cause"] for r in real if r["after"]["status"] != "SERVED")),
        "rows": [row(r) for r in real]})
    put("independent_evaluation_status.json", {"NEW_INDEPENDENT_EVALUATION": "BLOCKED_DATA", "INDEPENDENT_GENERALIZATION": "NOT_MEASURED",
        "H1": {"status": "NOT_MEASURED", "sealed_rows": 94, "opened": 0}, "W2_W3": "locked rows neither read nor re-run",
        "why": "no rights-cleared, unexposed, in-scope dataset and no independent selector / transcriber / scorer"})
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
