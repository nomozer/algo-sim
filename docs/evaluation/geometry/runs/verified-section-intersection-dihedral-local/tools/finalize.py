"""Remaining receipts of verified-section-intersection-dihedral-local: parser phrasing tests, Source Gate integrity,
degenerate sections, dependency graph, timing before/after, capability audit, dihedral audit and status receipts.
Counts are measured here or read from receipts in this run; adjudicated text says so.
Run from backend/:  python <tools>/finalize.py <before_backend_dir>
"""
from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
PRIOR = RUN.parent / "semantic-to-scene3d-verified-simulation/tools"
sys.path[:0] = [str(ROOT / "backend"), str(Path(__file__).resolve().parent), str(PRIOR)]
from verify_constructions import PROBES  # noqa: E402

NOW = datetime.now(timezone.utc).isoformat()
P = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
CUBE = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. "
PARSER_CASES = [
    # (category, text, expectation: SERVED | NOT_SERVED)
    ("positive_section_xac_dinh", P + "Gọi M là trung điểm của SC. Xác định thiết diện của hình chóp cắt bởi mặt phẳng (ABM).", "SERVED"),
    ("positive_section_dung", P + "Gọi M là trung điểm của SC. Dựng thiết diện của hình chóp cắt bởi mặt phẳng (ABM).", "SERVED"),
    ("positive_section_tim_tao_boi", P + "Gọi M là trung điểm của SC. Tìm thiết diện của hình chóp tạo bởi mặt phẳng (ABM).", "SERVED"),
    ("positive_section_named_solid", P + "Gọi M là trung điểm của SC. Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (ABM).", "SERVED"),
    ("positive_section_no_word_mat_phang", P + "Gọi M là trung điểm của SC. Xác định thiết diện của hình chóp cắt bởi (ABM).", "SERVED"),
    ("positive_section_area", P + "Gọi M là trung điểm của SC. Tính diện tích thiết diện của hình chóp cắt bởi mặt phẳng (ABM).", "SERVED"),
    ("positive_section_prime_unicode", CUBE.replace("'", "′") + "Xác định thiết diện của hình lập phương cắt bởi mặt phẳng (A′BD).", "SERVED"),
    ("positive_intersection_tim", P + "Tìm giao tuyến của hai mặt phẳng (SAC) và (SBD).", "SERVED"),
    ("positive_intersection_xac_dinh", P + "Xác định giao tuyến của hai mặt phẳng (SAB) và (SCD).", "SERVED"),
    ("positive_intersection_dung_mp", P + "Dựng giao tuyến của mặt phẳng (SAD) và mặt phẳng (SBC).", "SERVED"),
    ("positive_intersection_named_line", P + "Gọi d là giao tuyến của (SAB) và (SCD).", "SERVED"),
    ("reordered_clauses", "Cho hình chóp S.ABCD có SA vuông góc với mặt phẳng đáy, đáy ABCD là hình vuông cạnh a và SA = a. Gọi M là trung điểm của SC. Dựng thiết diện của hình chóp cắt bởi mặt phẳng (ABM).", "SERVED"),
    ("renamed_vertices", "Cho hình chóp T.MNPQ có đáy MNPQ là hình vuông cạnh a, TM vuông góc với mặt phẳng đáy và TM = a. Tìm giao tuyến của hai mặt phẳng (TMN) và (TPQ).", "SERVED"),
    ("negative_question_form_goal_as_premise", P + "Gọi M là trung điểm của SC. Mặt phẳng (ABM) cắt hình chóp theo thiết diện là hình gì?", "NOT_SERVED"),
    ("negative_missing_parentheses", P + "Gọi M là trung điểm của SC. Xác định thiết diện của hình chóp cắt bởi mặt phẳng ABM.", "NOT_SERVED"),
    ("negative_unknown_point", P + "Xác định thiết diện của hình chóp cắt bởi mặt phẳng (XYZ).", "NOT_SERVED"),
    ("negative_collinear_points", P + "Gọi M là trung điểm của AC. Xác định thiết diện của hình chóp cắt bởi mặt phẳng (AMC).", "NOT_SERVED"),
    ("negative_other_solid", P + "Xác định thiết diện của hình chóp T.ABCD cắt bởi mặt phẳng (SAB).", "NOT_SERVED"),
    ("negative_same_plane_twice", P + "Xác định giao tuyến của hai mặt phẳng (SAB) và (SBA).", "NOT_SERVED"),
    ("negative_parallel_planes", CUBE + "Xác định giao tuyến của hai mặt phẳng (ABC) và (A'B'C').", "NOT_SERVED"),
    ("ambiguous_unnamed_plane", P + "Gọi M là trung điểm của SC. Xác định thiết diện của hình chóp cắt bởi mặt phẳng đi qua M và song song với đáy.", "NOT_SERVED"),
    ("contradictory_premises", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy, SA = a và SA = 2a. Gọi M là trung điểm của SC. Dựng thiết diện của hình chóp cắt bởi mặt phẳng (ABM).", "NOT_SERVED"),
    ("diagram_dependent", "Cho hình chóp S.ABCD như hình vẽ. Gọi M là trung điểm của SC. Dựng thiết diện của hình chóp cắt bởi mặt phẳng (ABM).", "NOT_SERVED"),
    ("multiple_goals_section_and_intersection", P + "Gọi M là trung điểm của SC. Xác định giao tuyến của hai mặt phẳng (SAB) và (SCD). Dựng thiết diện của hình chóp cắt bởi mặt phẳng (ABM).", "SERVED"),
]


def git(*a):
    return subprocess.check_output(["git", *a], cwd=ROOT).decode("utf-8", "replace").strip()


def load(n):
    return json.loads((RUN / n).read_text(encoding="utf-8"))


def write(n, d):
    (RUN / n).write_text(json.dumps({"run_id": RUN.name, "generated_at_utc": NOW, "head": git("rev-parse", "HEAD"), **d},
                                    ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def timing_child() -> None:
    from app.ai.adaptive_input_router import route_text_input
    texts = json.loads(sys.stdin.read())
    for t in texts:
        route_text_input(t, allow_live_ai=False)            # warm
    out = []
    for t in texts:
        xs = []
        for _ in range(5):
            t0 = time.perf_counter()
            route_text_input(t, allow_live_ai=False)
            xs.append((time.perf_counter() - t0) * 1000)
        out.append(statistics.median(xs))
    print(json.dumps(out))


def timing(backend: Path, texts: list[str]) -> list[float]:
    env = {**os.environ, "PYTHONPATH": str(backend), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "ALLOW_LIVE_AI": "0", "GEMINI_API_KEY": ""}
    res = subprocess.run([sys.executable, __file__, "--timing"], input=json.dumps(texts, ensure_ascii=False), capture_output=True,
                         text=True, cwd=backend, env=env, encoding="utf-8", check=True)
    return json.loads(res.stdout.strip().splitlines()[-1])


def main() -> int:
    from app.ai.adaptive_input_router import route_text_input
    import importlib.util                            # previous run's dependency checker (object births + formation order)
    spec = importlib.util.spec_from_file_location("prior_finalize", PRIOR / "finalize.py")
    prior_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior_mod)
    dependency_checks = prior_mod.dependency_checks
    cand = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
    prior = json.loads(git("show", "ffc62f6fe:docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"))
    write("baseline_candidate_integrity.json", {
        "start_head": git("rev-parse", "ffc62f6fe"), "branch": git("branch", "--show-current"),
        "start_candidate": {"manifest_commit": prior["commit"], "stored_in": "15e98444b", "product_commit": prior["product_commit_sha"],
                            "measured_system": prior["measured_system"]["tree_hash"], "files": prior["measured_system"]["so_file"],
                            "cache_version": prior["cache_version"]},
        "relations": "manifest commit fe835d424 = HEAD when frozen; 15e98444b stores the manifest; product 70e393fd8 is the last commit touching measured paths; report HEAD ffc62f6fe descends from all three (git merge-base --is-ancestor)",
        "verified_at_start": "freeze --verify matched b222260d9a59bfc0 (115 files); lock_cache_identity --verify matched 133 / 3d5400a5; tree clean; no server on 8767/8770 (VERIFIED FACT, session log)",
        "commits_since_start": git("log", "--format=%h %s", "ffc62f6fe..HEAD").splitlines()})

    rows = []
    for cat, text, want in PARSER_CASES:
        r = route_text_input(text, allow_live_ai=False).response
        rd = r.get("route_d") or {}
        sc = (r.get("envelope") or {}).get("scene3d") or {}
        got = "SERVED" if rd.get("status") == "SERVED" else "NOT_SERVED"
        rows.append({"category": cat, "text": text, "expected": want, "got": got, "ok": got == want,
                     "reason": r.get("reason_code") or (rd.get("refusal") or {}).get("code"),
                     "sections": sum(o["type"] == "section" for o in sc.get("objects", [])),
                     "intersection_lines": sum(o.get("producer") == "intersect_plane_plane" for o in sc.get("objects", []))})
    write("local_section_intersection_parser_tests.json", {
        "cases": len(rows), "as_expected": sum(r["ok"] for r in rows), "unexpected": [r["category"] for r in rows if not r["ok"]],
        "unit_tests": ["backend/tests/geometry/test_section_intersection_local.py"], "rows": rows})

    write("source_gate_construction_integrity.json", {
        "source_gate_changed": False,
        "what_changed_upstream": "parser rules 7c-0/7c-1 emit facts the gate already grounds (`constrained` contains_points section, intersection_line question); the /2 bridge maps construct_intersection_line to the planner's existing intersection_line",
        "goal_as_premise_guard": "a section plane stated inside a question sentence (\"… theo thiết diện là hình gì?\") is refused by the gate (QUESTION_CLAUSE_NOT_PREMISE); the parser leaves that form unparsed rather than loosening the guard",
        "intersection_goal_never_a_premise": "the construct_intersection_line goal carries only the two planes; no premise mentions the line (test_intersection_goal_is_never_a_premise_and_needs_two_distinct_planes)",
        "refusals_observed": dict(Counter(r["reason"] for r in rows if r["got"] == "NOT_SERVED")),
        "unexpected_serves": [r["category"] for r in rows if r["expected"] == "NOT_SERVED" and r["got"] == "SERVED"]})

    sec = load("polyhedron_section_correctness.json")["rows"]
    write("section_degenerate_cases.json", {
        "cases": [{"probe": r["probe"], "status": r["after"]["status"], "reason": r["after"]["reason"],
                   "section_vertices": (r["after"].get("objects") or {}).get("sections"), "failed_checks": r["after"]["failed_checks"]}
                  for r in sec],
        "notes": {"plane_is_a_face": "(ABC) of S.ABCD is the base plane: the section is that face (4 vertices), which is the intersection",
                  "contains_edge": "(ABC') contains edge AB: rectangle ABC'D'",
                  "triangle": "(A'BD): 3 vertices", "hexagon": "(MNP) through three edge midpoints: 6 vertices",
                  "collinear": "COLLINEAR_POINTS refusal", "unknown_point": "UNDERDETERMINED_POINT refusal",
                  "point_or_segment_intersection": "NOT_MEASURED through the local route: no supported phrasing names a plane that touches the solid in only a point or an edge without containing a face; the engine's closure certificate refuses a non-closed boundary",
                  "coincident_planes": "refused, but with the code PARALLEL_PLANES (safe, imprecise code — backlog)"}})

    dep = []
    for k, (_g, t) in PROBES.items():
        r = route_text_input(t, allow_live_ai=False).response
        if (r.get("route_d") or {}).get("status") == "SERVED":
            dep.append({"probe": k, **dependency_checks(r["envelope"]["scene3d"])})
    write("construction_dependency_graph_tests.json", {
        "rule": "objects: dependencies exist and are born no later; angle constructions: named points born before the conclusion; formation steps: every depends_on object was created by an earlier step",
        "checker": "semantic-to-scene3d-verified-simulation/tools/finalize.py::dependency_checks (witness window recorded in that run)",
        "served_scenes": len(dep), "violations_total": sum(len(r["violations"]) for r in dep), "rows": dep,
        "browser": "browser_construction_timeline.json — the goal object is absent at the first step and present at the last (real ←/→ buttons)"})

    texts = [t for _k, (_g, t) in PROBES.items()]
    before = timing(Path(sys.argv[1]), texts)
    after = timing(ROOT / "backend", texts)
    bperf = load("browser_performance_profile.json")
    stepms = [x for r in bperf["rows"] for x in r["step_ms"]]
    write("performance_impact.json", {
        "backend_route_ms": {"method": "route_text_input median of 5 warm calls per probe, before (ffc62f6fe) and after in separate child processes on the same host",
                             "median_before": statistics.median(before), "median_after": statistics.median(after),
                             "per_probe": [{"probe": k, "before": b, "after": a} for k, b, a in zip(PROBES, before, after)],
                             "note": "probes refused before (sections, intersections) do more work after because they are now solved — not a regression of the same work"},
        "browser": {"first_model_ms": [r["first_model_ms"] for r in bperf["rows"]], "step_ms_median": statistics.median(stepms),
                    "step_ms_max": max(stepms), "orbit_ms": [r["orbit_ms"] for r in bperf["rows"]], "source": "browser_performance_profile.json (headless host)"},
        "physical_low_end": "PHYSICAL_LOW_END_NOT_MEASURED"})

    clean = load("resource_cleanup_audit.json")
    clean_cls = {"MEMORY_LEAK": "INCONCLUSIVE",
                 "why": "heap after forced GC grew %.2f MB over 12 signed-in analyses (history keeps every envelope by design) and the 15 timeline walks of one problem went %s — not monotonic; canvas count constant; React/Three.js object counts are not exposed separately" % (
                     clean.get("heap_growth_mb") or 0, " → ".join(f"{x:.1f}" for x in clean.get("timeline_walk_heap_mb") or [])),
                 "not_measured_separately": ["Three.js BufferGeometry/material/texture counts", "event listeners", "detached DOM nodes"]}
    (RUN / "resource_cleanup_audit.json").write_text(json.dumps({**clean, "classification": clean_cls}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    inv = load("scene3d_mathematical_invariants.json")
    write("existing_intersection_section_capability_audit.json", {
        "capabilities": {
            "line–plane intersection (kernel intersect_line_plane: unique / parallel / contained)": "EXISTING_AND_REUSABLE",
            "plane–plane intersection (kernel intersect_plane_plane; planner intersection_line; scene line3)": "EXISTING_BUT_NOT_CONNECTED → connected (local parser + /2 goal)",
            "polyhedron section by a three-point plane (planner section, engine closure certificate, step-by-step face edges)": "EXISTING_BUT_NOT_CONNECTED → connected (local parser)",
            "section by a named plane defined in a separate clause (6c/6d)": "EXISTING_AND_REUSABLE (already local)",
            "section plane stated in a question sentence": "PARTIALLY_SUPPORTED (Source Gate refuses by design)",
            "section of a curved solid": "EXISTING_AND_REUSABLE (not in scope here)",
            "Scene3D section polygon and section plane rendering": "EXISTING_AND_REUSABLE",
            "plane–plane intersection rendering (line3)": "EXISTING_AND_REUSABLE",
            "altitude from a lateral face ⟂ base": "SCENE_RENDERING_GAP → constructed (altitude-construction/1)",
            "coincident planes reason code": "PARTIALLY_SUPPORTED (refused as PARALLEL_PLANES)",
        },
        "new_kernel_primitives": 0,
        "evidence": {"before_after": {"sections": load("polyhedron_section_correctness.json")["served_before"], "sections_after": load("polyhedron_section_correctness.json")["served_after"],
                                      "intersections_before": load("plane_intersection_correctness.json")["served_before"], "intersections_after": load("plane_intersection_correctness.json")["served_after"]},
                     "invariants": {"checks": inv["checks_total"], "failed": inv["checks_failed"]}}})

    ang = load("angle_construction_before_after.json")
    write("dihedral_angle_semantic_audit.json", {
        "conventions": {"line_line": "non-oriented, [0°, 90°] (ask_angle_lines, measure.degrees)", "line_plane": "[0°, 90°] (ask_angle_line_plane)",
                        "plane_plane": "non-oriented angle between planes, [0°, 90°] (ask_angle_plane_plane)",
                        "dihedral (oriented half-planes, (0°, 180°))": "premise fact only (dihedral_angle with point_a, edge, point_b); never an asked quantity, so no oriented dihedral is constructed"},
        "defect_found": "VERIFIED FACT: angle-construction/1 chose rays toward the first named points, so the angle between (SBC) and (SCD) of a pyramid with SA ⟂ base (60°) was drawn as the 120° dihedral B-SC-D; the cos²-only certificate passed it (cos² 60° = cos² 120° = 1/4)",
        "before_obtuse_drawn": ang["before_obtuse_drawn"], "after_obtuse_drawn": ang["after_obtuse_drawn"],
        "fix": "commit 420851be6: second ray flipped to its opposite when the rays open an obtuse angle; certificate = signed cos ≥ 0 AND cos² = measured; angle_domain declared; renderer refuses obtuse rays or a missing domain",
        "contract": "angle-construction/1 kept: additive field angle_domain, the meaning of arms (rays of the drawn angle) unchanged; old envelopes without the field are not drawn (fail-closed) and CACHE_VERSION 134 retires them",
        "when_the_source_only_gives_planes": "the asked angle between planes is drawn acute; no half-plane is chosen as a claim about an oriented dihedral"})
    write("dihedral_complementary_angle_counterexamples.json", {
        "backend_tests": "backend/tests/geometry/test_angle_construction_domain.py — 60°/120° (SBC)/(SCD) both plane orders; renamed T.MNPQ; synthetic half-planes at 45°/135° (cos² 1/2 both) drawn acute; wrong cos value refused; lines whose named points open 135° drawn at 45°; parallel and coincident planes have no construction",
        "frontend_tests": "frontend/src/simulations/domains/geometry/scene3d-angle-construction.test.ts — (SBC)/(SCD) rays meet at 60°; second ray reflected to the supplement ⇒ not drawn; missing angle_domain ⇒ not drawn",
        "red_before_fix": "15 of 18 new backend tests failed before 420851be6 (session log)",
        "mutation_flip_angle_ray": ang["mutation_summary"].get("flip_angle_ray"),
        "independent_recheck": "verify_constructions.py signed-cos check: before 3 obtuse constructions (SBC/SCD, swapped order, renamed), after 0"})

    write("fresh_external_simulation_evaluation.json", {
        "status": "NOT_MEASURED",
        "why": "No unseen, rights-cleared in-scope dataset other than the 94 sealed H-1 rows was available in this run; the sealed rows were not downloaded, viewed or read. The 25 controlled-vision items and the 2 previous fresh items are exposed (text/image acceptance in this run are development evidence).",
        "sealed_rows_opened": 0})
    write("independent_h1_status.json", {"status": "NOT_MEASURED", "sealed_rows": 94, "opened": 0,
                                         "why": "no independent selector, transcriber or scorer; all checks are AGENT_DIAGNOSTIC"})
    print("receipts written")
    return 0


if __name__ == "__main__":
    if "--timing" in sys.argv:
        timing_child()
    else:
        raise SystemExit(main())
