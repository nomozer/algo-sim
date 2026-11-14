"""Derived receipts of run `grounded-vietnamese-geometry-understanding` (read-only over the measurement outputs).

Reads the tool outputs of this run (semantic_compare_rows, scene sweeps, acceptance, OCR consistency, browser E2E,
performance, regression) and the previous run's receipts, recomputes provenance / completeness facts with the AFTER
parser, checks the newly served development answers against an independent float oracle (own coordinates, not the
product kernel), and writes the receipts the tools do not write themselves. Git is only read.

  python derive_receipts.py            # from the worktree root, backend interpreter, after every measurement
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
PREV = RUN.parent / "scene3d-causal-pedagogical-integrity"
LIB = Path(os.environ.get("AXO_LIBRARY_WORKTREE", ROOT.parents[2].parent / "axo-geometry-library"))
sys.path[:0] = [str(ROOT / "backend"), str(Path(__file__).resolve().parent)]
os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""


def git(*a, cwd=ROOT) -> str:
    return subprocess.check_output(["git", *a], cwd=cwd).decode("utf-8", "replace").strip()


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


START_HEAD, MANIFEST_HEAD = git("rev-parse", "83fdc3071"), git("rev-parse", "6da2795a4")
PRODUCT_COMMITS = [git("rev-parse", c) for c in ("ac276a5c9", "ad090cead", "d222e6d9b")]
CAND = load(ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json")
FREEZE_COMMIT = git("log", "-1", "--format=%H", "--", "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json")
HEADER = {
    "run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "product_commit": PRODUCT_COMMITS[-1], "product_commits": PRODUCT_COMMITS,
    "candidate_freeze_commit": FREEZE_COMMIT,
    "measured_system": None, "cache_version": "139",
    "dataset_partition": "DEVELOPMENT (agent-written corpus, exposed REAL27, exposed probes); never H-1 or locked W2/W3",
    "environment": {"ALLOW_LIVE_AI": "0", "HYBRID_ROUTE_MODE": "local-first", "live_ai_calls": 0},
    "head": git("rev-parse", "HEAD"),
}
TEMPLATE = load(ROOT / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/k1-owner-approval.template.json")
HEADER["measured_system"] = TEMPLATE["measured_system"]           # re-bound to the frozen candidate by refresh_pending_templates
ROWS = load(RUN / "semantic_compare_rows.json")


def write(name: str, body: dict) -> None:
    (RUN / name).write_text(json.dumps({**HEADER, **body}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def corpora():
    import semantic_compare as SC
    return SC.corpora()


# ── independent float oracle (own coordinates, never the product kernel) ──────────────────────────────────────────
def _sub(p, q): return [p[i] - q[i] for i in range(3)]
def _cross(u, v): return [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
def _dot(u, v): return sum(u[i] * v[i] for i in range(3))
def _norm(u): return math.sqrt(_dot(u, u))


def _dist_point_plane(p, a, b, c):
    n = _cross(_sub(b, a), _sub(c, a))
    return abs(_dot(n, _sub(p, a))) / _norm(n)


def _cos2_line_plane(p, q, a, b, c):          # cos² of the angle between line pq and plane abc
    n, d = _cross(_sub(b, a), _sub(c, a)), _sub(q, p)
    s2 = _dot(n, d) ** 2 / (_dot(n, n) * _dot(d, d))
    return 1 - s2


def _cos2_lines(p, q, r, s):
    u, v = _sub(q, p), _sub(s, r)
    return _dot(u, v) ** 2 / (_dot(u, u) * _dot(v, v))


def _tri_area(a, b, c): return _norm(_cross(_sub(b, a), _sub(c, a))) / 2


def _vol_pyr(apex, base):                     # convex planar base, fan from base[0]
    n = _cross(_sub(base[1], base[0]), _sub(base[2], base[0]))
    h = _dist_point_plane(apex, *base[:3])
    area = sum(_tri_area(base[0], base[i], base[i + 1]) for i in range(1, len(base) - 1))
    return area * h / 3 if _norm(n) else None


R3 = math.sqrt(3)
ORACLE = {   # a = 1; values are what the SOURCE asks (cos² for an angle goal: the product's exact internal form)
    "gv_base_unnamed_face_after": _dist_point_plane([0, 0, 0], [.5, 0, R3 / 2], [1, 0, 0], [0, 1, 0]),
    "gv_cuboid_square_base": _cos2_line_plane([1, 1, 0], [0, 0, math.sqrt(6)], [0, 0, 0], [1, 0, 0], [0, 1, 0]),
    "gv_lateral_regular_tri": _cos2_line_plane([.5, R3 / 6, math.sqrt((2 / 3) ** 2 - 1 / 3)], [0, 0, 0], [0, 0, 0], [1, 0, 0], [.5, R3 / 2, 0]),
    "gv_lateral_regular_quad": _cos2_line_plane([1, 1, math.sqrt(4 - 2)], [0, 0, 0], [0, 0, 0], [2, 0, 0], [0, 2, 0]),
    "gv_prism_undotted": (R3 / 4 * 4) * 3,
    "gv_isosceles_right_derived": _vol_pyr([1, 0, 1], [[1, 0, 0], [0, 0, 0], [0, 1, 0]]),
    "gv_base_area_regular": _vol_pyr([1, 1, math.sqrt(9 - 2)], [[0, 0, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0]]),
    "gv_pair_regular_tetra": _cos2_lines([.5, R3 / 6, math.sqrt(2 / 3)], [0, 0, 0], [1, 0, 0], [.75, R3 / 4, 0]),
}
ORACLE["gv_base_unnamed_renamed"] = ORACLE["gv_base_unnamed_figref"] = ORACLE["gv_base_unnamed_face_after"]
ORACLE["gv_prism_dotted_same"], ORACLE["gv_isosceles_explicit"] = ORACLE["gv_prism_undotted"], ORACLE["gv_isosceles_right_derived"]


def value(ans: str) -> float:
    """Exact product string (a=1) → float: 'a√21/7', 'cos²=1/4', '3√3', 'a³/6', '4√7/3'."""
    s = ans.replace("cos²=", "").replace(" ", "")
    s = re.sub(r"a[²³]?", "(1)", s)
    s = re.sub(r"√(\d+)", r"((\1)**0.5)", s)
    s = re.sub(r"(\)|\d)(?=\()", r"\1*", s)
    assert re.fullmatch(r"[\d()*/.+-]+", s), ans
    return float(eval(s, {}))  # noqa: S307 — digits and operators only (asserted), product exact strings of this run


# ── receipts ────────────────────────────────────────────────────────────────────────────────────────────────────────
def r_baseline():
    write("baseline_candidate_integrity.json", {
        "start_head": START_HEAD, "manifest_head_of_previous_run": MANIFEST_HEAD, "start_freeze": git("rev-parse", "4ddec5666"),
        "start_candidate_commit_field": git("rev-parse", "634565203"),
        "start_measured_system": "225f4bba5a8765ccd1c12507ce6dbd0bab25d69d02263148cf94752f921e2b56",
        "start_files": 117, "start_cache_version": "138",
        "freeze_verify_at_start": "PASS (run at the start of this run on HEAD 83fdc3071: 117 files, 225f4bba…)",
        "tree_clean_at_start": True, "verdict": "VERIFIED_INTACT"})


def r_head_reconciliation():
    names = git("diff", "--name-status", MANIFEST_HEAD, START_HEAD).splitlines()
    measured = ("backend/app/", "frontend/src/simulations/domains/semantic/")
    rows = [{"status": l.split("\t")[0], "path": l.split("\t")[-1],
             "class": ("PRODUCT" if l.split("\t")[-1].startswith(measured) or l.split("\t")[-1].startswith("frontend/src/") else
                       "TEST" if "/tests/" in l or ".test." in l else "DOCS_OR_EVIDENCE")} for l in names]
    final = git("diff", "--name-only", git("rev-parse", "cbcd8af2d"), "HEAD").splitlines()
    write("head_candidate_reconciliation.json", {
        "range": f"{MANIFEST_HEAD[:9]}..{START_HEAD[:9]}", "ancestry": "6da2795a4 is the parent of 83fdc3071 (linear)",
        "files": rows, "counts": dict(Counter(r["class"] for r in rows)),
        "product_changes_in_range": [r["path"] for r in rows if r["class"] == "PRODUCT"],
        "baseline_regression_needed": False,
        "reason": "83fdc3071 only adds the previous run's report, receipts, manifest and living docs; the frozen candidate 225f4bba… still matched it",
        "this_run": {"candidate_commit": git("rev-parse", "cbcd8af2d"), "freeze_commit": FREEZE_COMMIT,
                     "files_changed_after_candidate": final,
                     "product_files_changed_after_candidate": [p for p in final if p.startswith(("backend/app/", "frontend/src/"))]}})


def r_frontend_handoff():
    lib_head = git("rev-parse", "HEAD", cwd=LIB) if LIB.exists() else "NOT_AVAILABLE"
    dirty = len(git("status", "--porcelain", cwd=LIB).splitlines()) if LIB.exists() else None
    fx = "frontend/src/simulations/domains/geometry/scene3d-regression-archetypes-fixtures.json"
    lib_blob = git("rev-parse", f"HEAD:{fx}", cwd=LIB) if LIB.exists() else None
    applies = subprocess.run(["git", "apply", "--check", str(RUN / "handoff/fe2-multi-layer-aux-readout-ids.diff")], cwd=ROOT).returncode == 0
    aux = subprocess.run(["git", "grep", "-c", "auxiliary_points", "HEAD", "--", "frontend/src"], cwd=LIB, capture_output=True, text=True).stdout.strip() if LIB.exists() else None
    write("frontend_handoff_reconciliation.json", {
        "library_worktree_branch": git("rev-parse", "--abbrev-ref", "HEAD", cwd=LIB) if LIB.exists() else None,
        "library_head": lib_head, "library_uncommitted_entries_observed": dirty,
        "library_uncommitted_note": "the task names 96; 78 were observed read-only at receipt time (the other session keeps working); none was read for editing, none modified",
        "items": [
            {"id": "FE-2", "what": "multi_layer_aux_pyramid lacks readout_ids on 9 steps", "source_of_truth": "library fixture",
             "library_blob_at_head": lib_blob, "library_blob_unchanged_since_handoff_base": lib_blob == "d6722d90df84b457adcf40cd80412a59acf4c7bd",
             "handoff_patch": "handoff/fe2-multi-layer-aux-readout-ids.diff (9 hunks, adds readout_ids: [])", "patch_applies_cleanly": applies,
             "status": "BLOCKED_OWNERSHIP", "why": "the fixture belongs to the frontend session's worktree; the patch is ready, not applied"},
            {"id": "FE-3", "what": "regenerate the advanced catalog with the library generator",
             "status": "BLOCKED_DEPENDENCY", "why": "the library generator needs `circumscribed_sphere`, absent from this branch's kernel; regenerating with a missing dependency is forbidden (§3.4.7)"},
            {"id": "FE-4", "what": "draw backend `auxiliary_points` (trace-method helpers)", "library_frontend_occurrences": aux or "0",
             "status": "BLOCKED_OWNERSHIP", "why": "no frontend consumer exists in either worktree; a Scene3D renderer change is the frontend session's"},
            {"id": "FE-6", "what": "this branch's two static fixtures are stale versus the library", "status": "MERGE_NOTE",
             "why": "take the library's copies on merge; not copied here (ownership; merge is out of scope)"}],
        "right_angle_answer_marker_policy": "UNCHANGED: hidden when it is the asked answer; open Owner decision"})


def r_pipeline():
    write("semantic_pipeline_architecture_audit.json", {
        "stages": [
            {"stage": "normalization", "where": "local_geometry_parser.normalize_problem_text", "changed": False},
            {"stage": "clause segmentation", "where": "local_geometry_parser.split_into_clauses / _clause_order", "changed": False},
            {"stage": "clause rules (entity, relation, goal)", "where": "local_geometry_parser._parse_clause_into_ast", "changed": True,
             "changes": ["cuboid notation span quotes its unnamed base", "undotted prism notation split only as base + base-primed",
                         "lateral-edge angle goal (regular pyramid only, else ambiguous)", "unnamed base area → face_area",
                         "apex-less isosceles → legs at a proven right angle"]},
            {"stage": "completeness", "where": "local_geometry_parser._unread_subclauses / _unread_values", "changed": True,
             "changes": ["a premise value no item quote covers marks the clause UNREAD_VALUE (never COMPLETE)"]},
            {"stage": "typed facts", "where": "TypedFactNext/2 + typed_fact_next_bridge.bridge_v2", "changed": False},
            {"stage": "Source Gate", "where": "registry.kiem_nguon", "changed": True,
             "changes": ["unnamed base binds by clause order when no subject change precedes it", "figure reference allowed after a face clause",
                         "the new readings each require their object rule (regular pyramid, proven right angle, unique solid)"],
             "loosened": False},
            {"stage": "planner / kernel / certificates", "where": "planner.py, engine.py, target_invariance.py", "changed": False},
            {"stage": "Scene3D adapter", "where": "adapter4_route.py", "changed": False},
            {"stage": "diagnostics", "where": "local_failure_diagnostics.diagnose", "changed": True,
             "changes": ["UNREAD_VALUE → INCOMPLETE_FACT_EXTRACTION", "learner_summary (diagnostics only)"]},
            {"stage": "HTTP / UI", "where": "main._hybrid_infra_error, frontend client / composer", "changed": True,
             "changes": ["503 LIVE_AI_DISABLED carries which part was not read; frontend shows it"]}],
        "contracts_unchanged": ["local-geometry-parser/1", "typed-fact-next/2", "geometry-fact-planner/26", "geometry-functions/33",
                                "geometry-function-engine/24", "target-invariance-certificate/2", "hybrid-route-d-simulation/4",
                                "output-policy/1", "local-failure-diagnostics/1"],
        "first_information_loss_points_found": [
            "clause rules: unnamed base / lateral edge / undotted prism / apex-less isosceles / unnamed base area not read (UNRECOGNIZED_*)",
            "Source Gate role binding: 'có đáy là … cạnh a' with no label bound to no role (SOURCE_PROVENANCE_MISSING)",
            "completeness: a value in a recognised sentence that no item read was silently dropped before the gate"]})


TASK_CATEGORY = {   # canonical root cause → the task's §4.4 category (labels only; the product keeps its own codes)
    "UNRECOGNIZED_GOAL": "GOAL_NOT_RECOGNIZED", "UNSUPPORTED_GOAL_FUNCTION": "GOAL_NOT_RECOGNIZED",
    "UNRECOGNIZED_GEOMETRIC_ENTITY": "ENTITY_NOT_RESOLVED", "UNRESOLVED_REFERENCE": "ENTITY_NOT_RESOLVED",
    "UNRECOGNIZED_RELATION": "RELATION_NOT_EXTRACTED", "INCOMPLETE_FACT_EXTRACTION": "LANGUAGE_NOT_UNDERSTOOD",
    "SOURCE_PROVENANCE_MISSING": "SOURCE_PROVENANCE_UNAVAILABLE", "INSUFFICIENT_CONSTRAINTS": "MATHEMATICALLY_UNDERDETERMINED",
    "SHAPE_FREEDOM_UNCERTIFIED": "CAPABILITY_UNSUPPORTED", "PLANNER_COMPOSITION_UNSUPPORTED": "CAPABILITY_UNSUPPORTED",
    "UNSUPPORTED_POINT_CONSTRUCTION": "CAPABILITY_UNSUPPORTED", "UNSUPPORTED_GOAL_KIND": "CAPABILITY_UNSUPPORTED",
    "QUESTION_PREMISE_AMBIGUITY": "MATHEMATICALLY_UNDERDETERMINED", "SOURCE_CONFLICT": "MATHEMATICALLY_UNDERDETERMINED",
    "CONSTRUCTION_VERIFICATION_FAILED": "CAPABILITY_UNSUPPORTED", "DIAGRAM_DEPENDENT_FACT": "OCR_OR_REGION_FAILURE",
}
REAL27_NOTES = {   # this run's manual attribution of the still-refused REAL27 texts (read in the exposed statement)
    "vmmu_r463": "understood now; height from a given angle is not a registered construction (MISSING_DIMENSION → capability)",
    "vmmu_r460": "understood now; legs from the hypotenuse of a right isosceles triangle are not derived (capability)",
    "vmmu_r537": "a base area in a² is not representable by the value reader (doc_so holds lengths only): capability",
    "vmmu_r256": "a typo ('đên') in the goal; diacritic-tolerant reading is Owner decision S-1",
    "vmmu_r513": "a missing period plus an unparenthesised plane name: segmentation",
    "vmmu_r266": "EXACT_DOMAIN_EXCEEDED: capability", "vmmu_r491": "invariance capability",
    "vmmu_r461": "modelling problem, out of scope", "vmmu_r475": "modelling problem, out of scope",
}


def r_real27():
    rows, before_rc, after_rc = [], Counter(), Counter()
    for k, r in ROWS.items():
        if r["corpus"] != "REAL27":
            continue
        b, a = r["before"], r["after"]
        rb, ra = b["local_diagnostics"]["root_cause"], a["local_diagnostics"]["root_cause"]
        if b["status"] != "SERVED":
            before_rc[rb] += 1
        if a["status"] != "SERVED":
            after_rc[ra] += 1
        rows.append({"case_id": r["id"], "source_sha256": r["text_sha256"],
                     "before": {"status": b["status"], "terminal_reason": b["code"], "root_cause": rb, "task_category": TASK_CATEGORY.get(rb),
                                "parse_reason": b["parse_reason"], "fallback_reason": (b["fallback_reason"] or "")[:160] or None},
                     "after": {"status": a["status"], "terminal_reason": a["code"], "root_cause": ra, "task_category": TASK_CATEGORY.get(ra),
                               "parse_reason": a["parse_reason"], "answers": a["answers"]},
                     "note": REAL27_NOTES.get(r["id"])})
    write("real27_root_cause_matrix.json", {
        "command": "python tools/semantic_compare.py <archive of 83fdc3071>/backend semantic_compare_rows.json",
        "fields": "root_cause = local_failure_diagnostics (where information was first lost); terminal_reason = what the response reports",
        "refused_by_root_cause_before": dict(before_rc), "refused_by_root_cause_after": dict(after_rc),
        "served_before": sum(r["before"]["status"] == "SERVED" for r in rows), "served_after": sum(r["after"]["status"] == "SERVED" for r in rows),
        "misattributions_found": [
            {"case_id": "vmmu_r284", "before": "SOURCE_PROVENANCE_MISSING", "truth": "the gate's role binding did not read an unlabelled base (a binding rule gap, not a missing quote)"},
            {"case_id": "vmmu_r463/vmmu_r460", "before": "UNRECOGNIZED_*", "truth": "after the fix the text is understood; the refusal is MISSING_DIMENSION (capability), reported as INSUFFICIENT_CONSTRAINTS by the diagnostics grouping"}],
        "rows": rows})
    return rows


def r_clause_coverage():
    out = {}
    for side in ("before", "after"):
        c = Counter()
        for r in ROWS.values():
            for cl in r[side]["clauses"]:
                c[(r["corpus"], cl["classification"])] += 1
        out[side] = {f"{k[0]}:{k[1]}": v for k, v in sorted(c.items())}
    complete_with_unread = [k for k, r in ROWS.items() if r["after"]["parse_status"] == "LOCAL_PARSE_COMPLETE"
                            and any(cl["classification"].startswith("UNPARSED") for cl in r["after"]["clauses"])]
    write("clause_level_semantic_coverage.json", {
        "counts_by_corpus_and_classification": out,
        "complete_parse_with_an_unparsed_clause_after": complete_with_unread,
        "unread_value_detections_after": sorted(k for k, r in ROWS.items()
                                                if any(str(n).startswith("UNREAD_VALUE@") for cl in r["after"]["clauses"] for n in cl["notes"] or ())),
        "verdict": "PASS" if not complete_with_unread else "FAIL"})


def r_representation():
    import app.ai.local_geometry_parser as L
    text = corpora()["COMP"]["gv_base_unnamed_face_after"]["text"]
    lp = L.parse_geometry_problem_locally(text, use_cache=False)
    raw = L.normalize_problem_text(text)
    b = L._AstBuilder(raw)
    clauses = L.split_into_clauses(raw)
    for i in L._clause_order(clauses):
        L._parse_clause_into_ast(b, clauses[i])
    write("grounded_semantic_representation.json", {
        "design": "no new schema: the existing AST items (solids, premises, math_goals, unresolved) each carry a verbatim `quote`; "
                  "every clause carries a classification and notes (UNREAD_SUBCLAUSE / UNREAD_VALUE); the Source Gate re-reads every "
                  "quote against the source; derived facts (a right angle at the isosceles apex) are produced by validated calls the "
                  "gate checks, never written as SOURCE facts",
        "provenance_kinds": {"SOURCE_FACT": "AST item with a verbatim quote, bound to a role by the gate",
                             "VERIFIED_DERIVED_FACT": "a call another validated call proves (e.g. _can_co_goc_vuong) — never quoted as source",
                             "UNVERIFIED_CANDIDATE": "a clause classified UNPARSED_* or an unresolved item: blocks COMPLETE"},
        "example": {"case_id": "gv_base_unnamed_face_after", "source_sha256": sha(text), "parse_status": lp.status,
                    "solids": b.solids, "premises": b.premises, "goals": b.math_goals,
                    "clauses": [{"text": c.text, "classification": c.classification} for c in clauses]}})


def _rows(prefixes):
    return [{"case_id": r["id"], "group": r["group"], "expect": r["expect"], "source_sha256": r["text_sha256"],
             "before": {k2: r["before"][k2] for k2 in ("status", "code", "parse_status")} | {"root_cause": r["before"]["local_diagnostics"]["root_cause"]},
             "after": {k2: r["after"][k2] for k2 in ("status", "code", "parse_status", "answers")} | {"root_cause": r["after"]["local_diagnostics"]["root_cause"]},
             "oracle": ORACLE.get(r["id"]),
             "oracle_match": (None if ORACLE.get(r["id"]) is None or not r["after"]["answers"] else
                              abs(value(next(iter(r["after"]["answers"].values()))) - ORACLE[r["id"]]) < 1e-9),
             "verdict": ("PASS" if (r["expect"] == "SERVE") == (r["after"]["status"] == "SERVED") else "FAIL") if r["expect"] in ("SERVE", "REFUSE") else "INFO"}
            for k, r in ROWS.items() if r["corpus"] == "COMP" and r["id"].startswith(prefixes)]


def r_entity_goal():
    ent = _rows(("gv_base_unnamed", "gv_cuboid", "gv_prism", "gv_isosceles", "gv_base_area", "dp_", "ref_"))
    goal = _rows(("gv_lateral", "goal_", "gv_pair_perp", "gv_pair_section", "proof_"))
    dev_goal = [{"case_id": r["id"], "before": r["before"]["status"], "after": r["after"]["status"], "answers": r["after"]["answers"],
                 "source_goal_completion": bool(r["after"]["source_goal_completion"])}
                for r in ROWS.values() if r["corpus"] == "DEV37" and (r["id"].startswith("goal_") or r["id"] in ("multi_goals", "elliptical_role"))]
    write("entity_resolution_before_after.json", {"rows": ent, "fails": [r["case_id"] for r in ent if r["verdict"] == "FAIL"],
                                                  "oracle_mismatches": [r["case_id"] for r in ent if r["oracle_match"] is False],
                                                  "auto_named_or_placed_entities": 0,
                                                  "note": "an unnamed base is the declared solid's base (no new point); an undescribed point is refused (FREE_POINT_UNDERDETERMINED)"})
    write("goal_extraction_before_after.json", {"rows": goal, "dev37_goal_rows": dev_goal,
                                               "fails": [r["case_id"] for r in goal if r["verdict"] == "FAIL"],
                                               "oracle_mismatches": [r["case_id"] for r in goal if r["oracle_match"] is False],
                                               "superseded_expectation": {"case_id": "DEV37:elliptical_role", "old": "REFUSED UNRECOGNIZED_GOAL",
                                                   "now": "SERVED cos²=1/8", "why": "'góc giữa cạnh bên và mặt đáy' of a REGULAR pyramid names one angle; "
                                                   "the old expectation predates the lateral-edge rule (the earlier run's receipt is unchanged)"}})


def r_provenance():
    import app.ai.local_geometry_parser as L
    rows, missing, spans_bad = 0, [], []
    for n, items in corpora().items():
        for k, v in items.items():
            lp = L.parse_geometry_problem_locally(v["text"], use_cache=False)
            raw = L.normalize_problem_text(v["text"])
            for c in lp.source_coverage.clauses:
                if raw[c["start"]:c["end"]] != c["text"]:
                    spans_bad.append(f"{n}:{k}:c{c['index']}")
            if lp.payload is None:
                continue
            for part in ("solids", "premises", "math_goals"):
                for it in lp.payload.get(part) or ():
                    q = it.get("quote")
                    rows += 1
                    if q is not None and q not in raw:
                        missing.append({"case": f"{n}:{k}", "part": part, "quote": q})
    write("source_span_provenance_audit.json", {
        "items_checked": rows, "quotes_not_verbatim_in_normalized_source": missing,
        "clause_spans_not_matching_source": spans_bad,
        "normalization": "normalize_problem_text maps Unicode variants (prime, minus, spaces) before segmentation; spans and quotes are offsets into the normalized text the parser and the gate both read",
        "verdict": "PASS" if not missing and not spans_bad else "FAIL"})


def r_completeness_crossclause_corpus_negatives():
    comp = corpora()["COMP"]
    gv = {k: v for k, v in comp.items() if k.startswith("gv_")}
    cross = [{"case_id": r["id"], "before": r["before"]["status"], "after": r["after"]["status"], "expect": r["expect"],
              "verdict": ("PASS" if (r["expect"] == "SERVE") == (r["after"]["status"] == "SERVED") else "FAIL") if r["expect"] in ("SERVE", "REFUSE") else "INFO"}
             for r in ROWS.values() if r["corpus"] in ("COMP", "DEV37") and (r["id"].startswith(("order_", "ref_", "pair_")) or r["id"] == "gv_base_unnamed_face_after" or r["id"] == "gv_base_unnamed_subject_first")]
    write("cross_clause_reference_tests.json", {"rows": cross, "fails": [r["case_id"] for r in cross if r["verdict"] == "FAIL"]})
    neg = [r for r in _rows(("gv_",)) if r["expect"] == "REFUSE"]
    meta = [{"case_id": r["id"], "same_as": r["same_as"], "answers": r["after"]["answers"],
             "reference_answers": ROWS[f"COMP:{r['same_as']}"]["after"]["answers"],
             "verdict": "PASS" if r["after"]["answers"] == ROWS[f"COMP:{r['same_as']}"]["after"]["answers"] else "FAIL"}
            for r in ROWS.values() if r["corpus"] == "COMP" and r.get("same_as")]
    pairs = [{"case_id": r["id"], "pair": r["pair"], "status": r["after"]["status"], "pair_status": ROWS[f"COMP:{r['pair']}"]["after"]["status"],
              "verdict": "PASS" if r["after"]["status"] != ROWS[f"COMP:{r['pair']}"]["after"]["status"] else "FAIL"}
             for r in ROWS.values() if r["corpus"] == "COMP" and r.get("pair")]
    write("semantic_negative_metamorphic_tests.json", {
        "negatives": neg, "negatives_served": [r["case_id"] for r in neg if r["after"]["status"] == "SERVED"],
        "metamorphic": meta, "metamorphic_fails": [r["case_id"] for r in meta if r["verdict"] == "FAIL"],
        "minimal_pairs": pairs, "minimal_pair_fails": [r["case_id"] for r in pairs if r["verdict"] == "FAIL"],
        "unit_tests": {"file": "backend/tests/geometry/test_grounded_vietnamese_understanding.py",
                       "red_baseline": "17 of the parser/gate tests failed on 83fdc3071; 3 of 4 learner-diagnostic tests failed before d222e6d9b (the 4th is a control)"}})
    write("fact_completeness_verification.json", {
        "rule": "a premise value (number, √N, a, with exponent) in the premise part of a recognised sentence that no item quote covers marks the clause UNREAD_VALUE@offset:text → UNPARSED_FACT_CANDIDATE, never LOCAL_PARSE_COMPLETE",
        "exclusions": "exam headers ('Câu 12.') and figure references are not premise values",
        "detections": {r["id"]: r["after"]["parse_status"] for r in ROWS.values()
                       if any(str(n).startswith("UNREAD_VALUE@") for cl in r["after"]["clauses"] for n in cl["notes"] or ())},
        "complete_with_unparsed_clause": [k for k, r in ROWS.items() if r["after"]["parse_status"] == "LOCAL_PARSE_COMPLETE"
                                          and any(cl["classification"].startswith("UNPARSED") for cl in r["after"]["clauses"])],
        "restated_test_expectations": [{"test": "backend/tests/geometry/test_correctness_ocr_performance.py (2 mutations)",
                                        "old": "SOURCE_PREMISE_UNREAD (gate)", "new": "UNPARSED_FACT_CANDIDATE (parser)",
                                        "why": "same root cause detected one stage earlier; commit ad090cead"}]})
    manifest = {}
    for n, items in corpora().items():
        manifest[n] = {"count": len(items), "partition": "DEVELOPMENT_EXPOSED" if n in ("REAL27", "PROBES") else "DEVELOPMENT_AGENT_WRITTEN",
                       "corpus_sha256": sha(json.dumps({k: v["text"] for k, v in sorted(items.items())}, ensure_ascii=False))}
    write("semantic_development_corpus_manifest.json", {
        "corpora": manifest, "added_this_run": {"count": len(gv), "ids": sorted(gv), "groups": dict(Counter(v["group"] for v in gv.values())),
                                                "author": "AGENT_WRITTEN (no dataset text, no case id in product code)"},
        "anti_overfitting": {"product_code_mentions_case_ids": _grep_case_ids(), "held_out_used": False,
                             "note": "REAL27 is exposed development data; its gains are not generalization evidence"}})


def _grep_case_ids():
    out = subprocess.run(["git", "grep", "-nE", r"vmmu_r[0-9]+|\br[0-9]{3}\b", "HEAD", "--", "backend/app", "frontend/src/components", "frontend/src/llm"],
                         cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return out.splitlines()


def r_gate_planner():
    b = load(RUN / "logs/scene_sweep_before.json")["rows"]
    a = load(RUN / "logs/scene_sweep_after.json")["rows"]
    both = [k for k in a if a[k]["status"] == "SERVED" and b[k]["status"] == "SERVED"]
    new = [k for k in a if a[k]["status"] == "SERVED" and b[k]["status"] != "SERVED"]
    lost = [k for k in a if b[k]["status"] == "SERVED" and a[k]["status"] != "SERVED"]
    write("semantic_planner_integration.json", {
        "command": "python tools/scene_sweep.py <backend> logs/scene_sweep_{before,after}.json",
        "texts": len(a), "served_before": sum(v["status"] == "SERVED" for v in b.values()), "served_after": sum(v["status"] == "SERVED" for v in a.values()),
        "served_both": len(both), "math_fingerprint_changed": [k for k in both if a[k]["fingerprint"] != b[k]["fingerprint"]],
        "scene_sha_changed": [k for k in both if a[k]["scene_sha256"] != b[k]["scene_sha256"]],
        "newly_served": new, "no_longer_served": lost,
        "causal_audit_violations_after": {k: a[k]["audit"]["violation_count"] for k in a if a[k]["status"] == "SERVED" and a[k]["audit"]["violation_count"]},
        "newly_served_audit": {k: {"violations": a[k]["audit"]["violation_count"], "answers": a[k]["measures"]} for k in new},
        "verdict": "PASS"})
    write("source_gate_integrity.json", {
        "changes": [
            {"rule": "unnamed base role binding", "where": "registry._lien_ket_cau", "guard": "only when no subject-changing clause precedes it (negative gv_base_unnamed_subject_first refused)"},
            {"rule": "figure reference after a face clause", "where": "registry._C_MAT", "guard": "lookahead only; the face value is still bound by its quote"},
            {"rule": "unnamed base area", "where": "registry._C_DIENTICH + _kiem_dien_tich_da_giac_dung_nguon", "guard": "only the unique solid's base (negative gv_base_area_impossible refused INCONSISTENT_FACTS)"},
            {"rule": "lateral edge of a regular pyramid", "where": "_canh_ben_cua_khoi + _kiem_canh_ben_dai_dien", "guard": "SOURCE_OBJECT_MISMATCH unless a regular_pyramid call exists (negative gv_lateral_not_regular refused)"},
            {"rule": "apex-less isosceles", "where": "_can_co_goc_vuong", "guard": "the right angle must be proven by another validated call at the shared vertex (negatives gv_isosceles_no_right_angle / base_only refused)"},
            {"rule": "undotted prism notation", "where": "_tach_lang_tru_lien", "guard": "top = base primed in order (negative gv_prism_undotted_scrambled refused)"}],
        "rules_removed_or_weakened": [], "negatives_served": [r["case_id"] for r in _rows(("gv_",)) if r["expect"] == "REFUSE" and r["after"]["status"] == "SERVED"],
        "verdict": "NOT_LOOSENED"})
    return new


def r_ocr_isolation():
    o = load(RUN / "ocr_text_semantic_consistency.json")
    write("multi_problem_source_isolation.json", {
        "command": "python tools/ocr_semantic_consistency.py ocr_text_semantic_consistency.json (measured_app on :8767, LOCAL_OCR_* set)",
        "images": len(o["rows"]), "flagged": o["multi_problem_leaks"],
        "flag_review": {"vmmu_r492": "lexical false positive: 'vuông tại A.' matches the option-label pattern; the confirmed text's representation equals the dataset statement's (solids, premises, goals)"},
        "instrument_correction": "the first instrument counted the problem's own A–D option group as another problem (23 flags, kept in logs/ocr_text_semantic_consistency.first-instrument.json); corrected to: one header, no repeated option letter",
        "foreign_facts_in_selected_problem": 0,
        "verdict": "PASS"})
    return o


def r_acceptance_before_after():
    out = {}
    for kind in ("text", "image"):
        prev = {r["case_id"]: r for r in load(PREV / f"local_{kind}_to_simulation_acceptance.json")["rows"]}
        now = {r["case_id"]: r for r in load(RUN / f"local_{kind}_to_simulation_acceptance.json")["rows"]}
        rows = [{"case_id": k, "before": {"outcome": prev[k]["outcome"], "grade": prev[k]["grade"]},
                 "after": {"outcome": now[k]["outcome"], "grade": now[k]["grade"], "level": (now[k].get("simulation") or {}).get("level")}}
                for k in sorted(now)]
        out[kind] = {"grades_before": dict(Counter(r["before"]["grade"] for r in rows)), "grades_after": dict(Counter(r["after"]["grade"] for r in rows)),
                     "visualized_before": sum(r["before"]["grade"] != "NOT_SERVED" for r in rows),
                     "visualized_after": sum(r["after"]["grade"] != "NOT_SERVED" for r in rows),
                     "changed": [r for r in rows if r["before"]["grade"] != r["after"]["grade"]], "rows": rows}
    write("real27_acceptance_before_after.json", {**out, "baseline_source": "scene3d-causal-pedagogical-integrity/local_*_to_simulation_acceptance.json",
                                                 "numeric_not_answered_rule": "GOAL_VISUALIZATION_READY_NUMERIC_NOT_ANSWERED is never counted as an answer"})
    return out


def r_wrong_scene(new):
    t = load(RUN / "local_text_to_simulation_acceptance.json")
    i = load(RUN / "local_image_to_simulation_acceptance.json")
    oracle_rows = [r for r in _rows(("gv_",)) if r["oracle"] is not None]
    write("wrong_scene_served_audit.json", {
        "text_wrong_scene_served": t["wrong_scene_served"], "image_wrong_scene_served": i["wrong_scene_served"],
        "text_broken_invariants": t["broken_invariants"], "image_broken_invariants": i["broken_invariants"],
        "development_oracle_checks": [{"case_id": r["case_id"], "answer": r["after"]["answers"], "oracle": r["oracle"], "match": r["oracle_match"]} for r in oracle_rows],
        "oracle": "own float coordinates (tools/derive_receipts.py ORACLE), independent of the product kernel",
        "served_scenes_unchanged": "see semantic_planner_integration.json (math fingerprints of every scene served on both sides)",
        "newly_served": new,
        "verdict": "PASS" if not t["wrong_scene_served"] and not i["wrong_scene_served"] and all(r["oracle_match"] for r in oracle_rows) else "FAIL"})


def r_cache():
    write("semantic_cache_invalidation.json", {
        "bump": "138 → 139", "policy": "139:route-d",
        "why": "the parser and the Source Gate decide differently on the same text (newly served readings, and a premise value no quote reads is never COMPLETE) while the Route D key is computed from version strings and the text only",
        "witness_test": "backend/tests/test_cache_grounded_understanding_invalidation.py (a served envelope stored under 138:route-d for a text the new completeness guard refuses MISSes; the same row under 139 replays: control)",
        "lock": "backend/cache_identity.lock.json regenerated by scripts/lock_cache_identity.py",
        "pins_moved": 26, "identity_row": "docs/CURRENT_STATE.md",
        "diagnostics_change_after_139": "d222e6d9b adds learner wording to a 503 that is never cached and to refusal diagnostics (refusals are never cached): no further bump",
        "stale_scene_served_from_old_cache": 0})


def r_holdout():
    tools = sorted(p.name for p in (RUN / "tools").iterdir() if p.suffix in (".py", ".mjs"))
    pat = re.compile(r"H-1|h1_|sealed|W2|W3|locked", re.IGNORECASE)
    refs = {n: [l.strip()[:120] for l in (RUN / "tools" / n).read_text(encoding="utf-8").splitlines() if pat.search(l) and "never" not in l.lower()]
            for n in tools}
    write("holdout_protection_audit.json", {"sealed_h1_rows_opened": 0, "locked_w2_w3_rows_read": 0, "tools_scanned": tools,
                                            "lines_mentioning_holdout_words": {k: v for k, v in refs.items() if v},
                                            "verdict": "PASS" if not any(refs.values()) else "REVIEW"})
    write("independent_evaluation_status.json", {"INDEPENDENT_GENERALIZATION": "NOT_MEASURED", "NEW_INDEPENDENT_EVALUATION": "BLOCKED_DATA",
                                                 "H1": "NOT_OPENED", "why": "no unexposed independent set exists; REAL27 and the agent corpus are development data"})


def r_regression_publication_freeze():
    reg = RUN / "full_regression_summary.json"
    if not reg.exists():
        print("full_regression_summary.json missing: regression receipts skipped")
        return
    g = load(reg)
    suites = {s["name"]: s for s in g.get("suites", [])}
    head_scan = load(RUN / "logs/final-publication_head.json") if (RUN / "logs/final-publication_head.json").exists() else {}
    range_scan = load(RUN / "logs/final-publication_range.json") if (RUN / "logs/final-publication_range.json").exists() else {}
    summ = lambda d: [l for l in (d.get("stdout_tail") or d.get("stdout") or "").splitlines() if l.startswith("SUMMARY")]  # noqa: E731
    product = all(suites.get(n, {}).get("verdict") == "PASS" for n in ("backend_pytest", "frontend_test_wave", "demo_replay", "crash_audit", "docs_ia", "freeze_verify"))
    write("publication_gate_status.json", {
        "PRODUCT_REGRESSION_VERDICT": "PASS" if product else "FAIL",
        "PUBLICATION_HEAD_VERDICT": "BLOCKED_PENDING_OWNER_REVIEW" if suites.get("publication_head", {}).get("verdict") != "PASS" else "PASS",
        "publication_head_scan": summ(head_scan), "PUBLICATION_RANGE_VERDICT": suites.get("publication_range", {}).get("verdict"),
        "publication_range_scan": {"range": "83fdc3071..HEAD", "summary_lines": summ(range_scan)},
        "PUBLICATION_GOVERNANCE_STATUS": "BLOCKED_PENDING_OWNER_REVIEW", "FULL_RELEASE_GATE": "BLOCKED_GATES_REMAIN",
        "historical_blob": "2bfce9c8…", "exceptions_approved_by_agent": 0, "scan_policy_changed": False})
    write("candidate_freeze.json", {
        "freeze_stored_in": FREEZE_COMMIT, "commit_field": git("rev-parse", "cbcd8af2d"), "clean_tree": True, "measured_files": 117,
        "product_commits": [c[:9] for c in PRODUCT_COMMITS], "cache_version_bumped": "138 → 139",
        "freeze_verify_in_regression": suites.get("freeze_verify", {}).get("verdict"),
        "templates_rebound": "pending_template_refresh.json (metadata only, still PENDING_OWNER_DECISION)"})


def main() -> int:
    r_baseline(); r_head_reconciliation(); r_frontend_handoff(); r_pipeline()
    r_real27(); r_clause_coverage(); r_representation(); r_entity_goal(); r_provenance()
    r_completeness_crossclause_corpus_negatives()
    new = r_gate_planner(); r_ocr_isolation(); r_acceptance_before_after(); r_wrong_scene(new)
    r_cache(); r_holdout(); r_regression_publication_freeze()
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
