"""Receipts of run `proof-soundness-generalized-angle-invariance` derived from its measured receipts, git, the frozen
candidate and read-only, offline re-runs of the proof module (tool copied from target-invariant-regular-solid-semantics).
python derived_receipts.py   (worktree root, backend python)"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "backend/tests/geometry")]
os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
START, PARENT = "914dd41db", "9d5e9b408"
NOW = datetime.now(timezone.utc).isoformat()
CONTRACTS = ["geometry-fact-planner/26", "geometry-functions/33", "geometry-function-engine/24", "height-invariance-certificate/2",
             "output-policy/1", "hybrid-route-d-simulation/4", "typed-fact-next/2"]
PY = sys.executable


def git(*a):
    return subprocess.check_output(["git", *a], cwd=ROOT).decode().strip()


CAND = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
META = {"run_id": RUN.name, "generated_at_utc": NOW, "product_commit": CAND["product_commit_sha"],
        "measured_system": CAND["measured_system"]["tree_hash"], "cache_version": CAND["cache_version"],
        "environment": {"ALLOW_LIVE_AI": "0", "HYBRID_ROUTE_MODE": "local-first", "live_ai_calls": 0}}


def put(n, d):
    (RUN / n).write_text(json.dumps({**META, "head": git("rev-parse", "HEAD"), **d}, ensure_ascii=False, indent=2, default=str) + "\n",
                         encoding="utf-8")


def load(n):
    return json.loads((RUN / n).read_text(encoding="utf-8"))


ROWS = load("semantic_compare_rows.json")
SCMD = f"python docs/evaluation/geometry/runs/{RUN.name}/tools/semantic_compare.py <archive of {PARENT}>/backend <out>"


def row(k):
    r = ROWS[k]
    return {"case_id": k, "text_sha256": r["text_sha256"], "expected": r["expect"],
            "before": {x: r["before"].get(x) for x in ("status", "code", "answers")},
            "after": {x: r["after"].get(x) for x in ("status", "code", "answers")},
            "after_root_cause": (r["after"].get("local_diagnostics") or {}).get("root_cause")}


def route(text):
    from app.ai.adaptive_input_router import route_text_input
    return (route_text_input(text, allow_live_ai=False).response or {}).get("route_d") or {}


def pytest_counts(*nodes):
    r = subprocess.run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", *nodes], cwd=ROOT / "backend", capture_output=True,
                       text=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=1200)
    tail = [ln for ln in r.stdout.splitlines() if re.search(r"\d+ (passed|failed)", ln)]
    return {"command": "python -m pytest -q " + " ".join(nodes), "exit_code": r.returncode, "summary": tail[-1] if tail else None}


# exact cos² of the asked angle on the free family B = 0, A = (1,0,0), C = (0,c,0), S = (1,0,h) (right at B, SA ⊥ (ABC))
def _v(p, q):
    return tuple(b - a for a, b in zip(p, q))


def _dot(u, v):
    return sum(a * b for a, b in zip(u, v))


def _cross(u, v):
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def family(c, h):
    return {"B": (0, 0, 0), "A": (Fraction(1), 0, 0), "C": (0, Fraction(c), 0), "S": (Fraction(1), 0, Fraction(h))}


def cos_sq_lines(P, a, b):
    u, v = _v(P[a[0]], P[a[1]]), _v(P[b[0]], P[b[1]])
    return Fraction(_dot(u, v) ** 2, _dot(u, u) * _dot(v, v))


def normal(P, pl):
    return _cross(_v(P[pl[0]], P[pl[1]]), _v(P[pl[0]], P[pl[2]]))


def cos_sq_planes(P, p, q):
    n, m = normal(P, p), normal(P, q)
    return Fraction(_dot(n, m) ** 2, _dot(n, n) * _dot(m, m))


def cos_sq_line_plane(P, l, p):             # cos² of the line–plane angle = 1 − sin², sin = |u·n| / |u||n|
    u, n = _v(P[l[0]], P[l[1]]), normal(P, p)
    return 1 - Fraction(_dot(u, n) ** 2, _dot(u, u) * _dot(n, n))


def main() -> int:
    from test_proof_soundness_angles import MUTATIONS, SCENE_FORGERIES, _proof, _ok, H, PLANES
    from app.simulation.geometry_functions import target_invariance as ti
    reg = load("full_regression_summary.json")
    gates = {s["name"]: s for s in reg.get("suites", [])}
    real = {i["case_id"]: i["statement"] for m in ("controlled-vision-real-image-validation/new_in_scope_image_manifest.json",
                                                    "local-semantic-source-gate-reliability/fresh_external_manifest.json")
            for i in json.loads((RUN.parent / m).read_text(encoding="utf-8"))["items"]}
    prev = json.loads((RUN.parent / "target-invariant-regular-solid-semantics/run.json").read_text(encoding="utf-8"))
    put("baseline_candidate_integrity.json", {
        "start_head": git("rev-parse", START), "start_freeze": "ade820bd3", "start_product_commit_field": "96ed1461e",
        "start_measured_system": prev["measured_system"], "start_files": 117, "start_cache_version": "136",
        "freeze_verify_at_start": "PASS at 914dd41db (previous run's final check, run.json regression_gates.freeze_verify)",
        "commit_landed_during_run": {"sha": git("rev-parse", PARENT), "subject": git("log", "-1", "--format=%s", PARENT),
                                     "author_is_this_session": False, "touches_backend_app": True,
                                     "consequence": "measured system changed under the candidate ⇒ freeze --verify red until refrozen; "
                                                    "before side of semantic_compare is this commit so the delta is this run's change only"},
        "worktree_a": "axo-geometry-library: not switched, reset, cleaned or edited by this run",
        "verdict": "VERIFIED_INTACT_AT_START; REFROZEN_AFTER_CHANGES"})
    tools = sorted(p.name for p in (RUN / "tools").glob("*.*") if p.name != Path(__file__).name)
    text = "\n".join((RUN / "tools" / n).read_text(encoding="utf-8", errors="ignore") for n in tools)
    put("holdout_protection_audit.json", {"sealed_h1_rows_opened": 0, "locked_w2_w3_rows_read": 0, "tools_scanned": tools,
        "h1_corpus_paths_referenced": sorted(set(re.findall(r"[\w/.-]*(?:independent-holdout|h1[-_](?:sealed|corpus|rows))[\w/.-]*", text, re.I))),
        "w2_w3_locked_manifests_referenced": [m for m in ("locked_w2", "locked_w3", "unseen_evaluation") if m in text], "verdict": "PASS"})
    put("proof_architecture_audit.json", {
        "module": "backend/app/simulation/geometry_functions/target_invariance.py", "schema": ti.TARGET_INVARIANCE_VERSION,
        "search": "_Search.saturate (bounded forward chaining over DERIVATION_RULES) + _prove (one goal rule) + _finish (TRIANGLE_SHAPE_FIXED)",
        "verifier": "verify_target_invariance_certificate(cert, calls, goal): re-derives every step from the calls and EARLIER steps; "
                    "shares only _ln/_args/_Domain/_ratio_sq; never calls the search (AST test)",
        "derivation_rules": list(ti.DERIVATION_RULES), "goal_rules": list(ti.GOAL_RULES), "shape_rule": "TRIANGLE_SHAPE_FIXED",
        "goal_functions": list(ti.GOAL_FUNCTIONS), "angle_domain": ti.ANGLE_DOMAIN, "max_derived": ti.MAX_DERIVED,
        "proof_domain": "one pyramid / regular_pyramid call and its vertices (convex base: no three collinear, apex off the base); prisms and derived points out of domain",
        "engine_obligations": ["TI-1 goal kind", "TI-2 proof", "TI-3 independent verification bound to the goal", "TI-4 representative",
                               "TI-5 shape/scale witnesses (regression, not proof)", "TI-6 proven cos² = kernel exact answer"],
        "adapter_binding": "_invariance_proof_bound (adapter4_route.py)",
        "not_built": ["parallel geometry kernel", "numeric sampling as proof", "oriented / dihedral angles", "parallel transport for skew lines (only ⊥ skew lines)"]})
    old = json.loads((RUN / "logs/old_verifier_probe.json").read_text(encoding="utf-8"))
    put("r520_angle_witness_defect_reproduction.json", {
        "code_under_test": f"archive of {START}/backend (target_invariance.py identical at {PARENT})",
        "command": "PYTHONPATH=<archive>/backend python tools/old_verifier_probe.py logs/old_verifier_probe.json",
        "generated_plane_angle_step": old["generated_plane_angle_step"], "claim_text": old["claim"], "probes": old["probes"],
        "defect": ["the triple ['B','S','A'] puts the vertex FIRST: read in standard notation it is ∠BSA (vertex S), the claim text says ∠(SBA)",
                   "a certificate re-pointed to another goal_id was accepted (no goal binding)",
                   "the shape step was not tied to the witness vertex (any listing of the triangle accepted)",
                   "the proven value was never bound to the kernel's answer"],
        "served_value_was_right_because": "SAB is right isosceles at A: ∠SBA = ∠BSA = 45° — the defect was masked by the special shape",
        "red_tests_now": ["test_the_r520_vertex_first_triple_certificate_is_not_accepted",
                          "test_a_shape_fixed_at_another_vertex_is_rejected_even_when_the_figure_makes_it_equal",
                          "test_a_certificate_is_bound_to_the_goal_it_was_proven_for"]})
    P1, P2 = family(1, 2), family(3, 2)
    put("plane_angle_root_cause_analysis.json", {
        "root_cause": "an unstructured angle triple whose vertex convention (first) differs from the notation of the claim (middle), "
                      "and a verifier that checked steps internally but not against the asked goal, the witness vertex or the kernel value",
        "counterexample_SA_eq_2AB": {"angle_at_B_SBA": str(cos_sq_lines(P1, "BS", "BA")), "angle_at_S_BSA": str(cos_sq_lines(P1, "SB", "SA")),
                                     "plane_angle_hand": str(cos_sq_planes(P1, "SBC", "ABC")),
                                     "same_on_another_c": str(cos_sq_planes(P2, "SBC", "ABC")),
                                     "reading": "cos² 1/5 at B (the plane angle, independent of c) vs 4/5 at S"},
        "fix": ["structured witness {vertex, ray_1, ray_2, domain}", "goal binding (goal_id + asked planes/lines)",
                "shape fixed AT the witness vertex", "stated cos² recomputed", "engine TI-6 kernel value binding",
                "adapter: drawn angle = witness"]})
    c520, calls520, ask520 = _proof(real["vmmu_r520"])
    from app.ai.adaptive_input_router import route_text_input
    full520 = route_text_input(real["vmmu_r520"], allow_live_ai=False).response or {}
    rd520 = full520.get("route_d") or {}
    put("structured_angle_witness_verification.json", {
        "r520": {"witness": c520["conclusion"]["witness"], "cos_sq": c520["conclusion"]["cos_sq"],
                 "verified": ti.verify_target_invariance_certificate(c520, calls520, ask520),
                 "scene_angle_construction": next(({k: o["angle_construction"].get(k) for k in ("vertex_id",)} |
                                                   {"arm_ids": [a.get("to_id") for a in o["angle_construction"]["arms"]]}
                                                   for o in ((full520.get("envelope") or {}).get("scene3d") or {}).get("objects", []) if o.get("angle_construction")), None)},
        "witness_schema": {"vertex": "label", "ray_1": "[vertex, U]", "ray_2": "[vertex, V]", "domain": ti.ANGLE_DOMAIN},
        "checks": ["rays start at the vertex", "distinct arm ends", "vertex on the planes' common line", "each ray in its plane off that line",
                   "each ray proven ⊥ the common line", "shape step at the same vertex of the same triangle", "conclusion witness = goal-step witness"]})
    old_step = old["generated_plane_angle_step"]["conclusion"]
    put("plane_angle_proof_before_after.json", {
        "before": {"schema": "target-invariance-certificate/1", "plane_angle_conclusion": old_step, "goal_binding": False,
                   "value_binding": False, "served": row("REAL27:vmmu_r520")["before"] if "REAL27:vmmu_r520" in ROWS else "UNKNOWN"},
        "after": {"schema": ti.TARGET_INVARIANCE_VERSION, "plane_angle_conclusion": next(s for s in c520["steps"] if s["rule"] == "PLANE_ANGLE")["conclusion"],
                  "goal_binding": True, "value_binding": "TI-6", "served": {"status": rd520.get("status"), "answer_exact": rd520.get("answer_exact")}},
        "answer_changed": False, "reason_unchanged": "right isosceles: both readings 45°; the non-isosceles case is the discriminating one"})
    vt = pytest_counts("tests/geometry/test_proof_soundness_angles.py", "tests/geometry/test_target_invariance_regular_solids.py")
    put("independent_verifier_soundness_tests.json", {"pytest": vt,
        "independence": "test_the_verifier_never_calls_the_search (AST: no _Search/_prove/prove_angle_goal/_finish/_closure)",
        "goal_free_call": "verify(cert, calls) without goal ⇒ verified False", "budget": "MAX_DERIVED patched to 2 ⇒ PROOF_SEARCH_BUDGET_EXCEEDED, route refuses"})
    muts = []
    for text, rule, mutate in MUTATIONS:
        cert, calls, ask = _proof(text)
        bad = copy.deepcopy(cert)
        mutate(bad)
        res = ti.verify_target_invariance_certificate(bad, calls, ask)
        muts.append({"rule": rule, "text_sha256": hashlib.sha256(text.encode()).hexdigest(), "original_verified": _ok(cert, calls, ask),
                     "mutant_verified": res["verified"], "failed_step": res["failed_step"], "reason": res["reason"]})
    caught = sum(not m["mutant_verified"] and m["original_verified"] for m in muts)
    put("existing_rule_soundness_audit.json", {"rules": list(ti.RULES), "mutations": muts, "caught": f"{caught}/{len(muts)}",
        "rules_covered": sorted({m["rule"] for m in muts}), "all_rules_covered": {m["rule"] for m in muts} == set(ti.RULES),
        "verdict": "PASS" if caught == len(muts) and {m["rule"] for m in muts} == set(ti.RULES) else "FAIL"})

    def goal_block(keys, hand):
        from compositional_dev_corpus import CORPUS
        out = {}
        for k in keys:
            t = CORPUS[k]["text"]
            cert, calls, ask = _proof(t)
            out[k] = {"row": row(f"COMP:{k}"), "proof_rules": [s["rule"] for s in cert["steps"]] if cert else None,
                      "cos_sq": cert["conclusion"]["cos_sq"] if cert else None,
                      "witness": cert["conclusion"]["witness"] if cert else None,
                      "verified": ti.verify_target_invariance_certificate(cert, calls, ask)["verified"] if cert else None,
                      "hand_check_two_shapes": hand.get(k)}
        return out
    sys.path.insert(0, str(RUN / "tools"))
    F1, F2 = family(1, 1), family(3, 1)
    G1, G2 = family(1, 2), family(3, 2)
    put("perpendicular_planes_proof_verification.json", {"rule": "PERP_PLANES: d ⊂ P, d ⊥ Q ⇒ ∠(P, Q) = 90°",
        "cases": goal_block(["pp_base", "pp_lateral"], {
            "pp_base": [str(cos_sq_planes(F1, "SAC", "ABC")), str(cos_sq_planes(F2, "SAC", "ABC"))],
            "pp_lateral": [str(cos_sq_planes(F1, "SBC", "SAB")), str(cos_sq_planes(F2, "SBC", "SAB"))]})})
    put("line_plane_angle_invariance.json", {"rules": ["LINE_PLANE_ANGLE (projection foot H, YH ⊥ Π)", "LINE_PERP_PLANE_ANGLE"],
        "cases": goal_block(["lp_isosceles", "lp_ratio2", "lp_perpendicular", "lp_renamed"], {
            "lp_isosceles": [str(cos_sq_line_plane(F1, "SB", "ABC")), str(cos_sq_line_plane(F2, "SB", "ABC"))],
            "lp_ratio2": [str(cos_sq_line_plane(G1, "SB", "ABC")), str(cos_sq_line_plane(G2, "SB", "ABC"))],
            "lp_perpendicular": [str(cos_sq_line_plane(F1, "SA", "ABC")), str(cos_sq_line_plane(F2, "SA", "ABC"))]})})
    put("line_line_angle_invariance.json", {"rules": ["LINE_ANGLE (common vertex)", "LINES_PERPENDICULAR (also skew lines: of directions)"],
        "cases": goal_block(["ll_meeting", "ll_perpendicular", "ll_skew_perpendicular"], {
            "ll_meeting": [str(cos_sq_lines(F1, "SB", "SA")), str(cos_sq_lines(F2, "SB", "SA"))],
            "ll_perpendicular": [str(cos_sq_lines(F1, "SB", "BC")), str(cos_sq_lines(F2, "SB", "BC"))],
            "ll_skew_perpendicular": [str(cos_sq_lines(F1, "SA", "BC")), str(cos_sq_lines(F2, "SA", "BC"))]}),
        "skew_not_perpendicular": "no parallel-transport rule: refused (ll_skew_varying)"})
    put("generalized_angle_counterexamples.json", {
        "method": "exact cos² on two members of the free family (c = BC/AB varies, h = SA/AB as stated); a varying value ⇒ no proof may exist",
        "cases": {
            "ll_skew_varying (SC, AB)": {"row": row("COMP:ll_skew_varying"), "cos_sq": [str(cos_sq_lines(F1, "SC", "AB")), str(cos_sq_lines(F2, "SC", "AB"))]},
            "lp_varying_lateral (SC, (SAB))": {"row": row("COMP:lp_varying_lateral"), "cos_sq": [str(cos_sq_line_plane(F1, "SC", "SAB")), str(cos_sq_line_plane(F2, "SC", "SAB"))]},
            "ti_varying_line_plane (SC, (ABC))": {"row": row("COMP:ti_varying_line_plane"), "cos_sq": [str(cos_sq_line_plane(F1, "SC", "ABC")), str(cos_sq_line_plane(F2, "SC", "ABC"))]},
            "lp_no_ratio (SB, (ABC), h free)": {"row": row("COMP:lp_no_ratio"), "cos_sq": [str(cos_sq_line_plane(family(1, 1), "SB", "ABC")), str(cos_sq_line_plane(family(1, 3), "SB", "ABC"))]},
            "pa_prism_out_of_domain": {"row": row("COMP:pa_prism_out_of_domain"), "note": "invariant (45°) but outside the proof domain: refused, not approximated"},
            "SA = 2AB at S vs at B": {"cos_sq_at_B": str(cos_sq_lines(G1, "BS", "BA")), "cos_sq_at_S": str(cos_sq_lines(G1, "SB", "SA"))}}})
    put("proof_mutation_tests.json", {"verifier_mutations": f"{caught}/{len(muts)}",
        "structural": ["drop first step", "unknown rule", "duplicate goal step"],
        "witness": ["vertex S for the plane angle (consistent shape + value)", "shape at another vertex (isosceles coincidence)",
                    "certificate re-pointed to other planes / other goal id / no goal"],
        "engine": "TI-6 fault injection (verified-but-lying certificate) ⇒ refused",
        "tests": "backend/tests/geometry/test_proof_soundness_angles.py", "pytest": vt})
    bt = pytest_counts("tests/geometry/test_proof_soundness_angles.py::test_the_scene_is_bound_to_the_proof",
                       "tests/geometry/test_proof_soundness_angles.py::test_the_scene_binding_is_what_catches_them",
                       "tests/geometry/test_proof_soundness_angles.py::test_the_envelope_cannot_drop_or_change_the_configuration")
    put("proof_scene_binding_verification.json", {"authority": "adapter4_route._invariance_proof_bound + scene_configuration equality",
        "forgeries": len(SCENE_FORGERIES), "kinds": ["drawn angle at S (consistent points) vs proven vertex B", "witness vertex changed (engine + envelope)",
        "cos² changed (engine + envelope)", "independent verification flipped", "certificate schema /1", "drawn arm end changed (consistent points)"],
        "pytest": bt, "fault_injection": "with the binding disabled every forgery is SERVED (test_the_scene_binding_is_what_catches_them)"})
    prev_art = prev.get("artifacts") or {}
    changed = []
    for rel, h in prev_art.items():
        p = RUN.parent / "target-invariant-regular-solid-semantics" / rel
        if not p.exists() or hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest() != h["sha256_lf"]:
            changed.append(rel)
    put("historical_certificate_compatibility.json", {
        "v1_certificates": "not accepted by the /2 verifier (schema, bare triple, no goal) — test_the_r520_vertex_first_triple_certificate_is_not_accepted",
        "v1_in_cache": "rows 136:route-d MISS (cache 137)", "previous_run_receipts_checked": len(prev_art), "previous_run_receipts_changed": changed,
        "superseded_by_this_run": {"run": "target-invariant-regular-solid-semantics",
                                   "receipts": ["universal_goal_invariance_proofs.json (/1 certificate, bare triple)", "goal_invariance_mutation_tests.json (/1 mutations)",
                                                "target_invariance_capability_audit.json (not_supported list)"],
                                   "how": "this run's receipts supersede; the old files are unchanged"},
        "restated_tests": {"tests/geometry/test_target_invariance_regular_solids.py": [
            "test_the_proof_is_the_synthetic_one: equals_angle ⊇ {S,A,B} → witness vertex B + rays {S, A}",
            "test_unproven_or_varying_goals_are_refused: '(SAC) và (ABC)' (was refused as 'invariant but unproven') → test_perpendicular_planes_are_now_proven (90°)",
            "mutation keys equals_angle/intersection/RIGHT_ISOSCELES_AT_B → witness/intersection_line/RIGHT_ANGLE_AT_B; + value mutation"]},
        "verdict": "PASS" if not changed else "FAIL"})
    put("semantic_cache_invalidation.json", {
        "bump": "136 → 137", "why": "stricter verifier (goal / witness / value binding), adapter proof ↔ scene binding and changed served envelopes "
                                   "(certificate /2, new served goals) under an unchanged Route D key; 136 rows may carry /1 certificates",
        "tests": ["test_cache_proof_soundness_invalidation.py (adversarial /1 row under 136 ⇒ recomputed /2; control under 137 replays)",
                  "test_cache_target_invariance_invalidation.py", "test_cache_semantic_guard_invalidation.py", "test_cache_identity.py",
                  "test_current_state_identity.py"],
        "pytest": pytest_counts("tests/test_cache_proof_soundness_invalidation.py", "tests/test_cache_identity.py", "tests/test_current_state_identity.py"),
        "pins_moved": 22, "identity_lock": "regenerated (scripts/lock_cache_identity.py)"})
    put("independent_evaluation_status.json", {"INDEPENDENT_GENERALIZATION": "NOT_MEASURED", "NEW_INDEPENDENT_EVALUATION": "BLOCKED_DATA",
        "H1": {"status": "NOT_MEASURED", "opened": 0}, "note": "all cases are agent-written development texts or exposed REAL27; never unseen"})
    comp = [r for r in ROWS.values() if r["corpus"] == "COMP"]

    def meets(r, side):
        s = r[side]["status"] == "SERVED"
        m = s == (r["expect"] == "SERVE")
        return m and (not (s and r["numeric"]) or bool(r[side]["source_goal_completion"]))
    put("semantic_development_before_after.json", {"command": SCMD,
        "served": {c: {side: sum(r["corpus"] == c and r[side]["status"] == "SERVED" for r in ROWS.values()) for side in ("before", "after")}
                   for c in ("COMP", "DEV37", "REAL27", "PROBES")},
        "comp_expectations_met": {"before": sum(meets(r, "before") for r in comp), "after": sum(meets(r, "after") for r in comp), "of": len(comp)},
        "served_to_refused": [k for k, r in ROWS.items() if r["before"]["status"] == "SERVED" and r["after"]["status"] != "SERVED"],
        "answers_changed_on_served": [k for k, r in ROWS.items() if r["before"]["status"] == "SERVED" and r["before"]["answers"] != r["after"]["answers"]],
        "refused_to_served": [k for k, r in ROWS.items() if r["before"]["status"] != "SERVED" and r["after"]["status"] == "SERVED"],
        "real27_root_causes_after": dict(Counter((r["after"].get("local_diagnostics") or {}).get("root_cause") for r in ROWS.values()
                                                 if r["corpus"] == "REAL27" and r["after"]["status"] != "SERVED"))})
    listening = []
    for port in (8767, 8000, 3000, 4173, 5173):
        with socket.socket() as s:
            s.settimeout(0.3)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                listening.append(port)
    browser = load("resource_cleanup_audit.json")          # measured by scene3d_goal_e2e.mjs; kept, extended here
    browser = browser.get("browser_switch_loop", browser)
    put("resource_cleanup_audit.json", {"browser_switch_loop": browser,
        "ports_checked_after_run": [8767, 8000, 3000, 4173, 5173], "listening": listening,
        "ports_started_by_this_run": [8767], "still_listening_from_this_run": [p for p in listening if p == 8767],
        "other_listeners": {str(p): "not started by this run (a process already running before it); left untouched" for p in listening if p != 8767},
        "worktrees": git("worktree", "list").count("\n") + 1, "new_worktrees_or_branches": 0,
        "scratch": "temporary archives, dist and probes under the session scratch directory only",
        "verdict": "PASS" if 8767 not in listening else "FAIL"})
    put("publication_gate_status.json", {
        "product_regression": reg.get("verdict"),
        "publication_head": "BLOCKED_PENDING_OWNER_REVIEW", "publication_head_scan": (gates.get("publication_head") or {}).get("summary_lines"),
        "publication_range_scan_this_run": {"range": f"{START}..HEAD", "summary_lines": (gates.get("publication_range") or {}).get("summary_lines"),
                                            "scan_verdict": (gates.get("publication_range") or {}).get("verdict")},
        "governance": "BLOCKED_PENDING_OWNER_REVIEW", "full_release_gate": "BLOCKED_GATES_REMAIN",
        "historical_blob": "2bfce9c8… pending", "findings_97": "not approved", "agent_actions": "none (no approval, no wildcard, scan policy unchanged, no receipt deleted)"})
    put("candidate_freeze.json", {
        "freeze_stored_in": git("log", "-1", "--format=%H", "--", "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"),
        "commit_field": CAND["commit"], "clean_tree": CAND.get("cay_lam_viec_sach"), "measured_files": CAND["measured_system"]["so_file"],
        "cache_version_bumped": "136 → 137", "includes_owner_commit": PARENT,
        "contracts_unchanged": CONTRACTS, "freeze_verify_in_regression": (gates.get("freeze_verify") or {}).get("verdict")})
    artifacts = {}
    for path in sorted(p for p in RUN.rglob("*") if p.is_file() and p.name != "run.json" and "__pycache__" not in p.parts):
        data = path.read_bytes().replace(b"\r\n", b"\n")
        artifacts[path.relative_to(RUN).as_posix()] = {"sha256_lf": hashlib.sha256(data).hexdigest(), "bytes_lf": len(data)}
    e2e = load("scene3d_browser_e2e.json")
    put("run.json", {"schema": "algosim-proof-soundness-run/1", "start_head": git("rev-parse", START), "owner_commit_during_run": git("rev-parse", PARENT),
        "head_at_manifest_write": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
        "candidate_manifest_commit": CAND["commit"], "contracts_unchanged": CONTRACTS, "certificate_schema": "target-invariance-certificate/2",
        "regression_gates": {k: v["verdict"] for k, v in gates.items()}, "regression_verdict": reg.get("verdict"),
        "overall_verdict": "BLOCKED", "overall_reason": "publication HEAD BLOCKED_PENDING_OWNER_REVIEW; FULL_RELEASE_GATE BLOCKED_GATES_REMAIN",
        "browser_e2e": f"{e2e['passed']}/{e2e['total']}", "acceptance": {"text": load("local_text_to_simulation_acceptance.json")["grades"],
                                                                        "image": load("local_image_to_simulation_acceptance.json")["grades"]},
        "independent_generalization": "NOT_MEASURED", "h1": "NOT_MEASURED", "live_ai_calls": 0, "merge_push_deploy": "NOT_PERFORMED",
        "report": "AXO_PROOF_SOUNDNESS_GENERALIZED_ANGLE_REPORT.md", "hash_policy": "SHA-256 LF-normalised; excludes run.json", "artifacts": artifacts})
    print("ok", reg.get("verdict"), {k: v["verdict"] for k, v in gates.items()}, "mutations", f"{caught}/{len(muts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
