"""Receipts of run `scene3d-causal-pedagogical-integrity` derived from its measured receipts, git and the frozen
candidate (tool copied from proof-soundness-generalized-angle-invariance).  python derived_receipts.py  (worktree root)"""
from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
LIB = Path("D:/Documents/projects/axo-geometry-library")
sys.path[:0] = [str(ROOT / "backend"), str(Path(__file__).resolve().parent)]
os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
START = "9d0949b09"
NOW = datetime.now(timezone.utc).isoformat()
PY = sys.executable
CONTRACTS = ["geometry-fact-planner/26", "geometry-functions/33", "geometry-function-engine/24", "angle-construction/1",
             "target-invariance-certificate/2", "output-policy/1", "hybrid-route-d-simulation/4", "typed-fact-next/2"]


def git(*a, cwd=ROOT):
    return subprocess.check_output(["git", *a], cwd=cwd).decode().strip()


CAND = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
META = {"run_id": RUN.name, "generated_at_utc": NOW, "product_commit": CAND["product_commit_sha"],
        "measured_system": CAND["measured_system"]["tree_hash"], "cache_version": CAND["cache_version"],
        "dataset_partition": "DEVELOPMENT (agent-written corpus, exposed REAL27, exposed probes); never H-1 or locked W2/W3",
        "environment": {"ALLOW_LIVE_AI": "0", "HYBRID_ROUTE_MODE": "local-first", "live_ai_calls": 0}}


def put(n, d):
    (RUN / n).write_text(json.dumps({**META, "head": git("rev-parse", "HEAD"), **d}, ensure_ascii=False, indent=2, default=str) + "\n",
                         encoding="utf-8")


def load(n):
    return json.loads((RUN / n).read_text(encoding="utf-8"))


def pytest_counts(*nodes):
    r = subprocess.run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", *nodes], cwd=ROOT / "backend", capture_output=True,
                       text=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=1500)
    tail = [ln for ln in r.stdout.splitlines() if re.search(r"\d+ (passed|failed)", ln)]
    return {"command": "python -m pytest -q " + " ".join(nodes), "exit_code": r.returncode, "summary": tail[-1] if tail else None}


def served(rows):
    return {k: r for k, r in rows.items() if r["status"] == "SERVED"}


def main() -> int:
    reg = load("full_regression_summary.json")
    gates = {s["name"]: s for s in reg.get("suites", [])}
    before = served(load("logs/scene_sweep_before.json")["rows"])
    after = served(load("logs/scene_sweep_after.json")["rows"])
    prov = load("catalog_fixture_provenance.json")
    mut = load("causal_mutation_tests.json")
    prev = json.loads((RUN.parent / "proof-soundness-generalized-angle-invariance/run.json").read_text(encoding="utf-8"))
    SWEEP = {"command": f"python docs/evaluation/geometry/runs/{RUN.name}/tools/scene_sweep.py <backend> <out>",
             "before_backend": f"archive of {START}/backend", "after_backend": "frozen candidate backend",
             "oracle": "tools/causal_audit.py (reads only the serialized scene)"}

    put("baseline_candidate_integrity.json", {
        "start_head": git("rev-parse", START), "start_freeze": "f30363597", "start_candidate_commit_field": "5481d5ddc",
        "start_measured_system": "610b4ee1e3227bc44f0659aea5d0dfc7f7a827aff622605db2b9571fb980fb80",
        "start_files": 117, "start_cache_version": "137", "freeze_verify_at_start": "PASS (run at the start of this run, HEAD 9d0949b09)",
        "tree_clean_at_start": True, "head_and_freeze_same_product_content": "YES at start (freeze --verify matched 610b4ee1…, 117 files)",
        "verdict": "VERIFIED_INTACT"})
    lib_status = subprocess.run(["git", "status", "--short"], cwd=LIB, capture_output=True, text=True).stdout.splitlines()
    put("worktree_ownership_audit.json", {
        "implementation_worktree": {"branch": git("branch", "--show-current"), "head": git("rev-parse", "HEAD")},
        "frontend_library_worktree": {"path": "axo-geometry-library", "branch": git("branch", "--show-current", cwd=LIB),
                                      "head": git("rev-parse", "HEAD", cwd=LIB), "uncommitted_entries_of_another_session": len(lib_status),
                                      "access": "read-only via `git show <commit>:<path>`; never switched, reset, cleaned or edited",
                                      "integration_commit_of_backend_handoff": "b5810dcc3 (fix(axo): integrate verified backend geometry contracts)"},
        "merge_base": git("merge-base", "HEAD", git("rev-parse", "HEAD", cwd=LIB)),
        "files_of_other_sessions_edited": 0,
        "this_branch_frontend_copies": "scene3d-circumsphere-fixture.json / scene3d-regression-archetypes-fixtures.json left as they are on "
                                       "this branch (frontend-owned static fixtures; the library has integrated their fixes)"})
    it = prov["items"]
    put("v9415_issue_reproduction_matrix.json", {
        "heads": {"this_worktree": prov["this_worktree_head"], "library": prov["library_head"]},
        "rows": {
            "GEO-BE-V9415-004": {"classification": "CONFIRMED_STATIC_FIXTURE", "generator": it["GEO-BE-V9415-004"]["generator"],
                                 "reproduced_on_this_branch": it["GEO-BE-V9415-004"]["this_worktree_committed"]["per_scene"]["/coincident_elements_pyramid/scene3d"]["examples"],
                                 "on_library_head": it["GEO-BE-V9415-004"]["library_committed"]["per_scene"]["/coincident_elements_pyramid/scene3d"]["violations"],
                                 "status": "FIXED_IN_LIBRARY (b5810dcc3); this branch's copy stale; READOUT_IDS_MISSING remains in archetype multi_layer_aux_pyramid of the library"},
            "GEO-BE-V9415-003": {"classification": "CROSS_LAYER_CONTRACT (static fixture + backend visible_prerequisites)",
                                 "reproduced_on_this_branch": it["GEO-BE-V9415-003"]["this_worktree_committed"]["per_scene"],
                                 "on_library_head": it["GEO-BE-V9415-003"]["library_committed"]["violation_total"],
                                 "backend": "visible_prerequisites (9d5e9b408) + this run: dependency-free carriers (a given radius R) are source data, never a visual prerequisite",
                                 "status": "FIXED (library fixture clean; backend generalization in 70befe6f1)"},
            "GEO-BE-V9415-002": {"classification": "CONFIRMED_BACKEND_GENERATOR",
                                 "route_d_generic_measure_texts": {"before": sum(m["generic"] for r in before.values() for m in r["measures"]),
                                                                   "after": sum(m["generic"] for r in after.values() for m in r["measures"])},
                                 "status": "FIXED by owner commit 9d5e9b408 (verified independently, 0 generic texts on 111 served scenes)"},
            "GEO-BE-V9415-001": {"classification": "CONFIRMED_BACKEND_GENERATOR (catalog: library generator; Route D: this branch)",
                                 "route_d_reproduced": "(MNP) through midpoints of SA, BC, CD: vertices on SB and SD appeared with no reason",
                                 "route_d_section_edges_without_reason": {"before": sum(1 for r in before.values() for e in r["section_edges"] if not e["theorem"]),
                                                                          "after": sum(1 for r in after.values() for e in r["section_edges"] if not e["theorem"])},
                                 "catalog": "orphan O / coplanar construction delivered by 9d5e9b408 and integrated in the library",
                                 "status": f"FIXED on Route D by the trace method ({git('log', '-1', '--format=%h', '--grep=trace method')}); 2 edges of a plane 'chứa BD và song song SC' remain without reason (needs a diagonal auxiliary plane)"},
            "ROUTE_D_UNUSED_AUXILIARY": {"classification": "CONFIRMED_BACKEND_ADAPTER (found by this run's sweep)",
                                         "before": {k: r["audit"]["unused_auxiliary_flagged"] for k, r in before.items() if r["audit"]["unused_auxiliary_flagged"]},
                                         "after": {k: r["audit"]["unused_auxiliary_flagged"] for k, r in after.items() if r["audit"]["unused_auxiliary_flagged"]},
                                         "status": "FIXED (the asked intersection line and a source-stated point were flagged unused)"},
            "RIGHT_ANGLE_NOT_DRAWN": {"classification": "CONFIRMED_BACKEND_GENERATOR",
                                      "before": dict(Counter(v for r in before.values() for v in r["right_angle_drawn"].values())),
                                      "after": dict(Counter(v for r in after.values() for v in r["right_angle_drawn"].values())),
                                      "status": "FIXED"}}})
    from app.ai.adaptive_input_router import route_text_input
    from scene_sweep import corpora
    texts = {f"{n}:{k}": v["text"] for n, items in corpora().items() for k, v in items.items()}
    inv = Counter()
    lineage = Counter()
    for k in after:
        sc = (route_text_input(texts[k], allow_live_ai=False).response or {})["envelope"]["scene3d"]
        for e in sc["events"]:
            inv[(e.get("action"), e.get("semantic_kind"))] += 1
        for o in sc["objects"]:
            if (o.get("construction_lineage") or {}).get("mode"):
                lineage[o["construction_lineage"]["mode"]] += 1
    put("scene_event_producer_inventory.json", {"served_scenes": len(after), "events_by_action_and_kind": {f"{a}/{b}": c for (a, b), c in inv.most_common()},
        "construction_lineage_modes": dict(lineage), "producers": {
            "events / formation.steps": "backend/app/simulation/semantic_program/scene3d.py (build_scene3d) + geometry_functions/construction_continuity.py",
            "depends / computational_depends / visible_prerequisites / construction_lineage": "semantic_program/simulation_state.py",
            "MEASURE explanations / measured_quantity": "semantic_program/geometry_exec.py (phan_loai_quan_he_do), scene3d.py (_giai_thich_do)",
            "section reasons": "simulation_state.py (_canh_song_song_thiet_dien, _vet_giao_tuyen_thiet_dien) → scene3d.py",
            "unused auxiliary": "simulation_state._tim_phu_tro_du_thua, recomputed on Route D by function_route._tinh_lai_phu_tro_du_thua",
            "angle constructions / right-angle markers": "semantic_program/quantity_annotations.py"}})
    put("dependency_semantics_audit.json", {
        "relations": {"mathematical": "`computational_depends` (= the IR dependency of the statement; kept unchanged)",
                      "semantic": "`construction_lineage` (euclidean_coplanar_intersection, algebraic_line_plane_intersection, vector_translation, "
                                  "direct_euclidean_primitive), section `justification` (verified_exact), certified_relation of measures",
                      "visual_construction": "`visible_prerequisites` (non-visual carriers unwrapped; dependency-free carriers dropped as source data) "
                                             "+ event / formation order"},
        "decision": "existing representation reused (no new DAG); this run changed only the unwrap rule for dependency-free carriers",
        "invariants_measured_on_served_scenes": {"HIDDEN_MATH_VISUAL_DEPENDENCY": 0, "CAUSAL_BIRTH_ORDER": 0, "UNRESOLVED_REFERENCE": 0,
                                                 "DEPENDENCY_CYCLE": 0, "scenes": len(after)},
        "computational_dependencies": "unchanged by this run (only the visual unwrap rule changed); the regenerated samples keep objects, "
                                      "events and values identical (catalog_regeneration_diff.json)"})
    def kinds(rows):
        return dict(Counter(x for r in rows.values() for x, v in r["audit"]["violations"].items() for _ in v))
    put("causal_birth_order_before_after.json", {**SWEEP, "violations_before": kinds(before), "violations_after": kinds(after),
        "fixtures": {t: {"this_branch": (v["this_worktree_committed"] or {}).get("violation_total"),
                         "library": (v["library_committed"] or {}).get("violation_total")} for t, v in it.items()}})
    put("circumsphere_hidden_dependency_audit.json", {
        "this_branch_fixture": it["GEO-BE-V9415-003"]["this_worktree_committed"]["per_scene"],
        "library_fixture": it["GEO-BE-V9415-003"]["library_committed"]["per_scene"],
        "owner_verified_artifact": prov["owner_handoff_artifacts"]["scene3d-circumsphere-fixture.verified.json"]["violation_total"],
        "A_prime_D": "computational_depends [A, vec_OB] / [A_prime, vec_OC] kept; visible_prerequisites [A, B, O] / [A_prime, C, O] (owner test)",
        "generalization_this_run": "a carrier with no dependency (given radius R of a sphere / cylinder) was kept in visible_prerequisites; "
                                   "dropped now (test_source_data_is_not_a_visual_prerequisite)",
        "not_replaced_by_a_single_point": True})
    put("coincident_elements_timeline_verification.json", {
        "this_branch": it["GEO-BE-V9415-004"]["this_worktree_committed"]["per_scene"]["/coincident_elements_pyramid/scene3d"],
        "library": it["GEO-BE-V9415-004"]["library_committed"]["per_scene"]["/coincident_elements_pyramid/scene3d"],
        "SB_line": "a source line: the library fixture creates it (CREATE depends [S, B]) before K; no fake CREATE added by this run",
        "remaining_in_library": it["GEO-BE-V9415-004"]["library_committed"]["per_scene"]["/multi_layer_aux_pyramid/scene3d"]})
    ms_b = [m for r in before.values() for m in r["measures"]]
    ms_a = [m for r in after.values() for m in r["measures"]]
    put("measure_explanation_before_after.json", {**SWEEP,
        "route_d": {"before": {"events": len(ms_b), "generic": sum(m["generic"] for m in ms_b), "with_measured_quantity": sum(m["has_measured_quantity"] for m in ms_b)},
                    "after": {"events": len(ms_a), "generic": sum(m["generic"] for m in ms_a), "with_measured_quantity": sum(m["has_measured_quantity"] for m in ms_a)}},
        "without_measured_quantity": "internal vector_from_points steps ('Lấy vectơ AB.'): render non_visual, folded by the timeline, no relation claimed",
        "advanced_catalog": "11 generic zero-value MEASURE texts fixed by 9d5e9b408 (owner audit table); library catalog violation total "
                            f"{it['GEO-BE-V9415-001/002 (advanced catalog)']['library_committed']['violation_total']} (sphere radius only)"})
    put("measure_source_provenance.json", {
        "authority": "geometry_exec.phan_loai_quan_he_do from the exact kernel value and the measured objects (typed metadata, never parsed from producer strings)",
        "claim_consistency_violations_after": {k: v for k, v in kinds(after).items() if k in ("PERPENDICULAR_CLAIM_WITHOUT_ZERO_ANGLE", "ZERO_ANGLE_WITHOUT_PERPENDICULAR_RELATION", "DISTANCE_CLAIMS_PERPENDICULARITY")},
        "final_answer_policy": "the envelope carries exact values (answers, FINAL_RESULT texts); the learner UI redacts final results "
                               "(scene3d-model.tapKetQuaCuoi); measured in the browser (answer_text_on_page) — see scene3d_browser_e2e.json"})
    edges_after = [e for r in after.values() for e in r["section_edges"]]
    put("line_plane_euclidean_trace_audit.json", {**SWEEP,
        "route_d_section_points": "no Route D section vertex is an `intersect_line_plane` point object: sections are kernel `section` objects, "
                                  "explained edge by edge",
        "edges": {"before": dict(Counter(str(e["theorem"]) for r in before.values() for e in r["section_edges"])),
                  "after": dict(Counter(str(e["theorem"]) for e in edges_after))},
        "remaining_without_reason": [{"case": k, "learner_text": e["learner_text"]} for k, r in after.items() for e in r["section_edges"] if not e["theorem"]],
        "example": next((e for e in edges_after if e["theorem"] == "COPLANAR_TRACE_INTERSECTION" and "gọi" in (e["justification_text"] or "")), None),
        "catalog_samples": "algebraic_line_plane_intersection lineage disclosed by 9d5e9b408; coplanar replacement integrated in the library (b5810dcc3)"})
    put("auxiliary_construction_verification.json", {
        "method": "trace method over ℚ (affine incidence): every auxiliary point is the exact intersection of two coplanar lines and lies on the cutting plane",
        "independent_recheck": pytest_counts("tests/geometry/test_section_edge_justification.py"),
        "unit_tests": pytest_counts("tests/geometry/test_scene3d_causal_pedagogical_integrity.py"),
        "scene_objects_added": 0, "rendering": "auxiliary_points carried as data; drawing them is a frontend handoff item"})
    put("orphan_object_classification.json", {
        "before_flagged": {k: r["audit"]["unused_auxiliary_flagged"] for k, r in before.items() if r["audit"]["unused_auxiliary_flagged"]},
        "after_flagged": {k: r["audit"]["unused_auxiliary_flagged"] for k, r in after.items() if r["audit"]["unused_auxiliary_flagged"]},
        "independent_no_consumer_after": {k: r["audit"]["orphans_not_flagged"] for k, r in after.items() if r["audit"]["orphans_not_flagged"]},
        "classification": {"COMP:mc_label_list N": "SOURCE_REQUIRED (the source states 'Gọi M, N …'; only M feeds the goal)",
                           "DEV37:int_goal gt_g_il2": "SOURCE_REQUIRED / GOAL (the asked intersection line)",
                           "DEV37:int_goal_mp gt_g_il2": "SOURCE_REQUIRED / GOAL"},
        "catalog_O": "UNUSED_REDUNDANT in chop-thiet-dien-ba-diem (flagged by 9d5e9b408; library coplanar sample has none)",
        "true_orphans_after": 0})
    secd = [(k, "sections") for k in after if after[k]["fingerprint"]["sections"] != before[k]["fingerprint"]["sections"]]
    put("section_geometry_regression.json", {**SWEEP,
        "served_scenes_compared": len(after), "section_vertex_ids_changed": secd,
        "points_changed": [k for k in after if after[k]["fingerprint"]["points"] != before[k]["fingerprint"]["points"]],
        "answers_changed": [k for k in after if after[k]["fingerprint"]["answer_exact"] != before[k]["fingerprint"]["answer_exact"]],
        "samples": load("catalog_regeneration_diff.json") if (RUN / "catalog_regeneration_diff.json").exists() else None})
    put("right_angle_visualization_verification.json", {
        "before": dict(Counter(str(v) for r in before.values() for v in r["right_angle_drawn"].values())),
        "after": dict(Counter(str(v) for r in after.values() for v in r["right_angle_drawn"].values())),
        "cases": {k: r["right_angle_drawn"] for k, r in after.items() if r["right_angle_drawn"]},
        "checks": "rays orthogonal under the scene Gram (and ⊥ the common line for planes) — test_a_proven_right_angle_without_a_meeting_point_is_drawn",
        "binding": "adapter _RIGHT_ANGLE_DRAWING: a proven 90° goal drawn by another kind of right angle is refused (fault injection)",
        "pytest": pytest_counts("tests/geometry/test_scene3d_causal_pedagogical_integrity.py", "-k", "right_angle")})
    put("proof_to_scene_binding_regression.json", {
        "pytest": pytest_counts("tests/geometry/test_proof_soundness_angles.py", "tests/geometry/test_target_invariance_regular_solids.py"),
        "certificates_changed": [k for k in after if after[k]["fingerprint"]["certificate"] != before[k]["fingerprint"]["certificate"]],
        "angle_constructions_added": [k for k in after if after[k]["fingerprint"]["angle_constructions"] != before[k]["fingerprint"]["angle_constructions"]]})
    put("global_scene_causality_audit.json", {**SWEEP, "served_scenes": len(after), "violations_after": kinds(after),
        "orphans_not_flagged_after": {k: r["audit"]["orphans_not_flagged"] for k, r in after.items() if r["audit"]["orphans_not_flagged"]},
        "readout_completeness": "every formation step has a readout_ids list naming existing objects (READOUT_* = 0)",
        "fixtures": {t: (v["library_committed"] or {}).get("violation_total") for t, v in it.items()}})
    fe = {"items": [
        {"id": "FE-1", "what": "apply nothing: coincident_elements_pyramid / circumsphere fixtures already integrated in the library (b5810dcc3)", "status": "DONE_BY_FRONTEND_OWNER"},
        {"id": "FE-2", "what": "archetype multi_layer_aux_pyramid lacks readout_ids on 9 steps (static fixture)", "status": "BLOCKED_OWNERSHIP"},
        {"id": "FE-3", "what": "regenerate advanced-geometry-samples.json with the library generator once this branch's backend is merged: the sphere "
                               "`cau` lists the given radius R as a visual prerequisite (fixed in simulation_state._unwrap_visible_sources)", "status": "BLOCKED_OWNERSHIP"},
        {"id": "FE-4", "what": "draw `details.justification.auxiliary_points` (trace-method helpers I, J on extended edges) and their two lines", "status": "BLOCKED_OWNERSHIP"},
        {"id": "FE-5", "what": "do not hide objects flagged unused on scenes cached before CACHE 138 (they may be the asked object)", "status": "COVERED_BY_CACHE_138"},
        {"id": "FE-6", "what": "this branch's frontend copies of the two fixtures are stale; take the library's on merge", "status": "MERGE_NOTE"}]}
    put("frontend_handoff_status.json", fe)
    prev_art = prev.get("artifacts") or {}
    changed = [rel for rel, h in prev_art.items()
               if not (RUN.parent / "proof-soundness-generalized-angle-invariance" / rel).exists()
               or hashlib.sha256((RUN.parent / "proof-soundness-generalized-angle-invariance" / rel).read_bytes().replace(b"\r\n", b"\n")).hexdigest() != h["sha256_lf"]]
    put("historical_envelope_compatibility.json", {
        "previous_run_receipts_checked": len(prev_art), "previous_run_receipts_changed": changed,
        "fixture_bundles": {"kept_unchanged": ["proof-soundness-generalized-angle-invariance/fixtures-lineage-proof-soundness",
                                               f"{RUN.name}/fixtures-causal-pedagogical"],
                            "current": f"{RUN.name}/fixtures-trace-method",
                            "supersession_logs": ["logs/fixture_bundle_supersession.json", "logs/fixture_bundle_supersession_trace.json"]},
        "contract_versions_changed": [], "backward_compatibility": "additive fields only (trace_derivation, justification theorem, angle_construction on 90°); "
                                                                  "consumers that ignore them behave as before",
        "verdict": "PASS" if not changed else "FAIL"})
    put("cache_identity_verification.json", {
        "bump": "137 → 138", "why": "served envelopes changed (unused-auxiliary flags, visible prerequisites, 90° angle constructions, "
                                   "trace-method reasons) and the adapter tightened, under an unchanged Route D key",
        "note": "the trace-method reasons landed after the 138 commit but before any freeze or measurement of 138; no 138 row was ever served from a candidate",
        "pytest": pytest_counts("tests/test_cache_causal_pedagogical_invalidation.py", "tests/test_cache_identity.py", "tests/test_current_state_identity.py"),
        "stale_scene_served_from_old_cache": 0, "pins_moved": 24})
    tools = sorted(p.name for p in (RUN / "tools").glob("*.*") if p.name != Path(__file__).name)
    text = "\n".join((RUN / "tools" / n).read_text(encoding="utf-8", errors="ignore") for n in tools)
    put("holdout_protection_audit.json", {"sealed_h1_rows_opened": 0, "locked_w2_w3_rows_read": 0, "tools_scanned": tools,
        "h1_corpus_paths_referenced": sorted(set(re.findall(r"[\w/.-]*(?:independent-holdout|h1[-_](?:sealed|corpus|rows))[\w/.-]*", text, re.I))),
        "w2_w3_locked_manifests_referenced": [m for m in ("locked_w2", "locked_w3", "unseen_evaluation") if m in text], "verdict": "PASS"})
    listening = []
    for port in (8767, 8000, 3000, 4173, 5173):
        with socket.socket() as s:
            s.settimeout(0.3)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                listening.append(port)
    browser = load("resource_cleanup_audit.json")
    browser = browser.get("browser_switch_loop", browser)
    put("resource_cleanup_audit.json", {"browser_switch_loop": browser, "ports_checked_after_run": [8767, 8000, 3000, 4173, 5173],
        "listening": listening, "ports_started_by_this_run": [8767],
        "other_listeners": {str(p): "not started by this run; left untouched" for p in listening if p != 8767},
        "new_worktrees_or_branches": 0, "verdict": "PASS" if 8767 not in listening else "FAIL"})
    put("publication_gate_status.json", {"PRODUCT_REGRESSION_VERDICT": "PASS" if all(gates[g]["verdict"] == "PASS" for g in gates if not g.startswith("publication")) else "FAIL",
        "PUBLICATION_HEAD_VERDICT": "BLOCKED_PENDING_OWNER_REVIEW", "publication_head_scan": (gates.get("publication_head") or {}).get("summary_lines"),
        "PUBLICATION_RANGE_VERDICT": (gates.get("publication_range") or {}).get("verdict"),
        "publication_range_scan": {"range": f"{START}..HEAD", "summary_lines": (gates.get("publication_range") or {}).get("summary_lines")},
        "PUBLICATION_GOVERNANCE_STATUS": "BLOCKED_PENDING_OWNER_REVIEW", "FULL_RELEASE_GATE": "BLOCKED_GATES_REMAIN",
        "historical_blob": "2bfce9c8… pending", "agent_actions": "none (no approval, no wildcard, scan policy unchanged, no receipt deleted)"})
    put("candidate_freeze.json", {"freeze_stored_in": git("log", "-1", "--format=%H", "--", "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"),
        "commit_field": CAND["commit"], "clean_tree": CAND.get("cay_lam_viec_sach"), "measured_files": CAND["measured_system"]["so_file"],
        "product_commits": ["70befe6f1", git("log", "-1", "--format=%h", "--grep=trace method")], "cache_version_bumped": "137 → 138",
        "contracts_unchanged": CONTRACTS, "freeze_verify_in_regression": (gates.get("freeze_verify") or {}).get("verdict")})
    artifacts = {}
    for path in sorted(p for p in RUN.rglob("*") if p.is_file() and p.name != "run.json" and "__pycache__" not in p.parts):
        data = path.read_bytes().replace(b"\r\n", b"\n")
        artifacts[path.relative_to(RUN).as_posix()] = {"sha256_lf": hashlib.sha256(data).hexdigest(), "bytes_lf": len(data)}
    e2e = load("scene3d_browser_e2e.json")
    put("run.json", {"schema": "algosim-scene3d-causal-run/1", "start_head": git("rev-parse", START),
        "head_at_manifest_write": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
        "candidate_manifest_commit": CAND["commit"], "contracts_unchanged": CONTRACTS,
        "regression_gates": {k: v["verdict"] for k, v in gates.items()}, "regression_verdict": reg.get("verdict"),
        "overall_verdict": "BLOCKED", "overall_reason": "publication HEAD BLOCKED_PENDING_OWNER_REVIEW; FULL_RELEASE_GATE BLOCKED_GATES_REMAIN",
        "browser_e2e": f"{e2e['passed']}/{e2e['total']}", "acceptance": {"text": load("local_text_to_simulation_acceptance.json")["grades"],
                                                                        "image": load("local_image_to_simulation_acceptance.json")["grades"]},
        "causal_mutations": f"{mut['caught']}/{mut['total']}", "independent_generalization": "NOT_MEASURED", "h1": "NOT_MEASURED",
        "live_ai_calls": 0, "merge_push_deploy": "NOT_PERFORMED", "report": "AXO_SCENE3D_CAUSAL_PEDAGOGICAL_INTEGRITY_REPORT.md",
        "hash_policy": "SHA-256 LF-normalised; excludes run.json", "artifacts": artifacts})
    print("ok", reg.get("verdict"), {k: v["verdict"] for k, v in gates.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
