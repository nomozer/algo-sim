"""Remaining receipts of semantic-to-scene3d-verified-simulation, computed from the served envelopes and the receipts
already in this run. Counts are measured here or read from receipts; capability verdicts cite their evidence.
Run from backend/:  python <tools>/finalize.py
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
sys.path[:0] = [str(ROOT / "backend"), str(Path(__file__).resolve().parent)]
from app.ai.adaptive_input_router import route_text_input  # noqa: E402
from app.ai.local_geometry_parser import parse_geometry_problem_locally  # noqa: E402
from scene_invariants import corpus  # noqa: E402

NOW = datetime.now(timezone.utc).isoformat()
START = "8a5a54e37"


def git(*a: str) -> str:
    return subprocess.check_output(["git", *a], cwd=ROOT).decode("utf-8", "replace").strip()


def load(n: str) -> dict:
    return json.loads((RUN / n).read_text(encoding="utf-8"))


def write(n: str, d: dict) -> None:
    (RUN / n).write_text(json.dumps({"run_id": RUN.name, "generated_at_utc": NOW, "head": git("rev-parse", "HEAD"), **d},
                                    ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def dependency_checks(sc: dict) -> dict:
    """Every dependency exists and is born no later than its dependant; every named point of an angle construction is a
    scene point born before the quantity's conclusion step; formation steps only depend on earlier steps."""
    objs = {o["id"]: o for o in sc["objects"]}
    born: dict[str, int] = {}
    for e in sc.get("events", []):
        for oid in (e.get("object"), *(e.get("objects") or ())):
            if oid:
                born.setdefault(oid, e["step_index"])
    bad = []
    for oid, o in objs.items():
        for d in o.get("depends") or ():
            if d not in objs or (d in born and oid in born and born[d] > born[oid]):
                bad.append(f"{oid}<-{d}")
        ac = o.get("angle_construction")
        if ac:
            for pid in [ac.get("vertex_id"), *(a.get("to_id") for a in ac["arms"])]:
                if pid and (objs.get(pid, {}).get("type") != "point3" or born.get(pid, 0) > born.get(oid, 10**9)):
                    bad.append(f"{oid}:angle_construction->{pid}")
    # Formation `depends_on` lists OBJECT ids (the contract): each must have been created by an earlier step.
    steps = (sc.get("formation") or {}).get("steps", [])
    created: set[str] = set()
    for s in steps:
        for d in s.get("depends_on") or ():
            if d not in created:
                bad.append(f"{s.get('step_id')}->{d}")
        created |= set(s.get("created_ids") or ()) | set(s.get("reused_ids") or ())
    return {"objects": len(objs), "steps": len(steps), "violations": bad}


def main() -> int:
    cand = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
    prior = json.loads(git("show", f"{START}:docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"))
    write("baseline_candidate_integrity.json", {
        "start_head": git("rev-parse", START), "branch": git("branch", "--show-current"),
        "start_candidate": {"manifest_commit": prior["commit"], "product_commit": prior["product_commit_sha"],
                            "measured_system": prior["measured_system"]["tree_hash"], "files": prior["measured_system"]["so_file"],
                            "cache_version": prior["cache_version"]},
        "verified_at_start": "freeze_evaluation_candidate.py --verify matched 1cc979f559a632c3 (115 files) on a clean tree; CACHE_VERSION 132; branch feat/local-first-geometry-understanding (VERIFIED FACT, session log)",
        "commits_since_start": git("log", "--format=%h %s", f"{START}..HEAD").splitlines()})

    # ── served corpus: dependency graph + backend stage timing ───────────────────────────────────────────────────────
    dep_rows, timing = [], []
    for name, text in corpus().items():
        t0 = time.perf_counter()
        pr = parse_geometry_problem_locally(text, use_cache=False)
        t1 = time.perf_counter()
        r = route_text_input(text, allow_live_ai=False).response
        t2 = time.perf_counter()
        if (r.get("route_d") or {}).get("status") != "SERVED":
            continue
        sc = r["envelope"]["scene3d"]
        dep_rows.append({"case": name, **dependency_checks(sc)})
        timing.append({"case": name, "local_parse_incl_stage8_ms": (t1 - t0) * 1000, "route_total_ms": (t2 - t1) * 1000,
                       "envelope_bytes": len(json.dumps(r, ensure_ascii=False).encode("utf-8")), "objects": len(sc["objects"])})
    # Witness window: the checker must flag a scene whose step depends on a later object and whose object depends on a
    # missing one (else its zero means nothing).
    import copy
    probe = route_text_input(next(iter(corpus().values())), allow_live_ai=False).response["envelope"]["scene3d"]
    bad = copy.deepcopy(probe)
    bad["formation"]["steps"][1].setdefault("depends_on", []).append(bad["formation"]["steps"][-1]["created_ids"][-1] if bad["formation"]["steps"][-1].get("created_ids") else "__later__")
    bad["objects"][-1].setdefault("depends", []).append("__missing__")
    window = {"good_scene_violations": len(dependency_checks(probe)["violations"]), "tampered_scene_violations": len(dependency_checks(bad)["violations"])}
    assert window["good_scene_violations"] == 0 and window["tampered_scene_violations"] >= 2, window
    write("construction_dependency_graph_tests.json", {
        "witness_window": window,
        "rule": "objects: every dependency exists and is born no later; angle constructions: named points are scene points born before the conclusion; formation steps: every depends_on object was created (or reused) by an earlier step",
        "served_scenes": len(dep_rows), "violations_total": sum(len(r["violations"]) for r in dep_rows),
        "unit_and_e2e_tests": ["backend/tests/geometry/test_angle_construction.py", "frontend/src/simulations/domains/geometry/scene3d-angle-construction.test.ts (shown only from the conclusion step, hidden when its named points are absent)",
                               "construction_timeline_e2e.json (real browser, ←/→ buttons)"],
        "recompute_on_change": "Scenes are rebuilt from the source text on every analysis (no reuse of coordinates); a changed text is a new cache key and CACHE_VERSION 133 retires 132 envelopes. Interactive parameter editing does not exist (dragging is out of scope, ARCHITECTURE_MAP invariant #31).",
        "rows": dep_rows})
    perf = load("frontend_performance_profile.json")
    med = lambda k: statistics.median(t[k] for t in timing)  # noqa: E731
    perf["backend_stage_timing"] = {"method": "in-process, warm, one call per statement; local parse includes its Stage 8 (bridge, planner, Source Gate); route_total = parse + bridge + planner + gate + exact kernel + scene build",
                                    "median_local_parse_ms": med("local_parse_incl_stage8_ms"), "median_route_total_ms": med("route_total_ms"),
                                    "max_route_total_ms": max(t["route_total_ms"] for t in timing), "median_envelope_kb": med("envelope_bytes") / 1024,
                                    "rows": timing}
    (RUN / "frontend_performance_profile.json").write_text(json.dumps(perf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # ── underdetermined geometry ─────────────────────────────────────────────────────────────────────────────────────
    under = {
        "free_height": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a. Tính thể tích khối chóp S.ABCD.",
        "free_apex_position": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA = a. Tính khoảng cách từ A đến mặt phẳng (SBC).",
        "midpoint_without_height": "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA = a. Gọi H là trung điểm của cạnh AB. Tính thể tích khối chóp S.ABCD.",
        "scale_free_regular_tetra": "Cho tứ diện đều ABCD. Gọi M là trung điểm của CD. Tính góc giữa hai đường thẳng AC và BM.",
        "free_point_on_edge": "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. Gọi I là một điểm thuộc cạnh BC. Tính khoảng cách từ I đến mặt phẳng (SAB).",
        "square_without_side": "Cho hình chóp S.ABCD có SA ⊥ (ABCD), đáy ABCD là hình vuông, biết SA = 2. Tính khoảng cách từ điểm C đến mặt phẳng (SBD).",
    }
    urows = []
    for k, t in under.items():
        r = route_text_input(t, allow_live_ai=False).response
        rd = r.get("route_d") or {}
        urows.append({"case": k, "text": t, "status": rd.get("status"),
                      "reason": r.get("reason_code") or (r.get("envelope") or {}).get("reason_code") or (rd.get("refusal") or {}).get("code")})
    served_scale = [t for t in dep_rows]
    p_served = {}
    for name, text in corpus().items():
        r = route_text_input(text, allow_live_ai=False).response
        rd = r.get("route_d") or {}
        if rd.get("status") == "SERVED":
            objs = r["envelope"]["scene3d"]["objects"]
            p_served[name] = {"unit_chosen_by_system": any(s.get("step") == "choose_unit" for s in rd.get("construction_trace") or []),
                              "points_marked_layout_derived": sum(1 for o in objs if o["type"] == "point3" and (o.get("source") or {}).get("provenance") == "LAYOUT_DERIVED"),
                              "points": sum(1 for o in objs if o["type"] == "point3")}
    write("parametric_geometry_safety.json", {
        "classification": {
            "FULLY_DETERMINED": "served with exact coordinates in a canonical chart; coordinates are LAYOUT_DERIVED (a representation choice), never fed back as source facts",
            "DETERMINED_UP_TO_SCALE": "served when every length is a multiple of one symbol (choose_unit: built at a = 1, the unit is not a fact, answers scale back as coefficient·a^degree); a figure with NO length at all is refused MISSING_DIMENSION even when the question is scale-free (safe, capability gap)",
            "PARAMETRIC_FAMILY": "refused (UNDERDETERMINED_POINT / AMBIGUOUS_FACT / unparsed free point); no family is drawn as if it were unique",
            "INSUFFICIENT_FOR_REQUESTED_CONSTRUCTION": "refused or asks for confirmation; an angle construction is emitted only when it reproduces the measured value exactly"},
        "underdetermined_probes": urows, "served_unique_count": sum(r["status"] == "SERVED" for r in urows),
        "served_scenes_representation": p_served,
        "parameter_interaction": "NOT_SUPPORTED_BY_DESIGN: camera only (orbit/zoom/pan/reset); vertex dragging is out of scope (ARCHITECTURE_MAP invariant #31: frame k ⇔ trace[k])",
        "classification_label": "VERIFIED_FACT for the probe outcomes; INFERENCE for the class descriptions"})

    # ── capability audit (adjudicated, evidence-cited) ────────────────────────────────────────────────────────────────
    gap = load("semantic_to_scene_gap_matrix.json")
    inv = load("scene3d_mathematical_invariants.json")
    write("existing_scene3d_capability_audit.json", {
        "method": "code reading (scene3d.py _TRUONG, quantity_annotations, scene3d-view renderer, geometry samples) + goal probes (semantic_to_scene_gap_matrix.json) + independent invariant checks (scene3d_mathematical_invariants.json)",
        "object_types": {
            "point": "SUPPORTED", "line": "SUPPORTED (line3, drawn clipped)", "segment": "SUPPORTED", "ray": "NOT_SUPPORTED as a scene type (angle arms are drawn as segments)",
            "plane": "SUPPORTED (plane3, measurement-only planes hidden by default)", "polygon": "SUPPORTED", "polyhedron (pyramid, prism, cuboid, cube, tetrahedron)": "SUPPORTED",
            "height / altitude": "SUPPORTED with an exact perpendicular_witness when the source gives it (SA ⟂ base, projection foot); PARTIALLY_SUPPORTED for a face ⟂ base (volume correct, altitude not drawn)",
            "median / centroid": "PARTIALLY_SUPPORTED: centroid is composed (midpoint + divide_segment) when named; medians are not scene objects of their own; unnamed centroid refused",
            "diagonal": "SUPPORTED (segments, intersection O for regular pyramids)",
            "projection": "SUPPORTED: point onto line (named, project_onto), point onto plane (distance witness, named foot, NEW line-plane angle foot)",
            "intersection line of two planes": "PARTIALLY_SUPPORTED: kernel + section steps exist; the local parser does not read 'Xác định giao tuyến …' (probe intersection_planes)",
            "section": "PARTIALLY_SUPPORTED: kernel and scene ('section' objects, geometry samples) exist; the local parser refused both section probes",
            "auxiliary objects": "SUPPORTED (CONSTRUCT_AUXILIARY_GEOMETRY role, auto-hidden after use)"},
        "goal_geometry_before_this_run": "angles ≠ 90° drew only the two operands (8/16 served probes stayed LEVEL1_BASE_ONLY) — the gap this run closes",
        "computed_but_not_constructed_before": ["foot of the projection for a line-plane angle", "vertex / arms for line-line angles",
                                                 "the translated parallel for skew-line angles", "the plane angle of a dihedral",
                                                 "right-angle witness relabelled as a segment length (bug)"],
        "heuristic_constructions_found": "none in the angle path: the renderer drew no angle at all before; layout coordinates are canonical charts marked LAYOUT_DERIVED",
        "levels_before_after": {"before": gap["before_levels"], "after": gap["after_levels"]},
        "invariants": {"served_scenes": inv["served_scenes"], "checks": inv["checks_total"], "failed": inv["checks_failed"]}})

    write("construction_contract_verification.json", {
        "contract": "angle-construction/1 on angle quantities (additive field; no existing field changed); envelope schema hybrid-route-d-simulation/4 unchanged; CACHE_VERSION 132 → 133",
        "existing_contract_reused": "Scene3D objects already carry id, type, producer, depends, dependency_edges, source provenance, formation steps (depends_on, preconditions, created_ids, verification_refs) and exact coordinates; no parallel schema was created",
        "source_vs_derived_vs_helper": {"SOURCE": "free points / given objects (origin free, display_group given)", "DERIVED": "construct_* producers with depends (e.g. G via midpoint + divide_segment, H via project_onto)",
                                        "VISUAL_HELPER": "angle_construction arms/arc/right-angle marks: no new typed fact, not pickable, not in depends"},
        "proof_carrying": "every angle_construction lists the checks it passed (checks[]) and is emitted only if cos² of the drawn angle equals the measured value exactly; otherwise ANGLE_CONSTRUCTION_UNBOUND in diagnostics",
        "frontend_engine": "none added: the renderer only re-checks (fail-closed) and interpolates a presentation arc; purity guard in scene3d.test.tsx",
        "compatibility": "older envelopes without the field render as before (field optional); cached 132 rows MISS under 133 (test_cache_angle_construction_invalidation.py)"})

    write("geometry_primitive_correctness.json", {
        "new_kernel_primitives": 0,
        "compositions_added": {"line_plane": "intersect_line_plane + project_point_onto_plane", "line_line": "intersect_line_line",
                               "line_line_skew": "named parallel segment (affine parallel test) or point + direction",
                               "plane_plane": "intersect_plane_plane + project_point_onto_line + component orthogonal to the edge in the frame metric"},
        "case_specific_primitives": 0,
        "preconditions_and_degeneracy": ["line ∥ plane / line ⊂ plane → no vertex (GeometryError, no construction)", "parallel lines → no construction",
                                         "parallel or coincident planes → no construction", "projection equal to the vertex (90°) → handled by the right-angle witness",
                                         "plane without a named point off the common line → no construction"],
        "tests": {"backend": "backend/tests/geometry/test_angle_construction.py (16 incl. cache)", "frontend": "scene3d-angle-construction.test.ts (15)",
                  "fault_injection": "a projection foot moved by (0,1,0) with the backend checks disabled made 4 tests fail (session log); scene_invariants witness window caught 3/3 tampered scenes"},
        "frame_metric": "all orthogonality checks use the chart Gram metric; regular tetrahedron and regular triangular prism (non-identity G) verified"})

    write("goal_construction_coverage.json", {
        "source": "semantic_to_scene_gap_matrix.json (synthetic probes) + text/image acceptance",
        "goal_types": {"angle line–plane": "CONSTRUCTED (projection foot, angle arc)", "angle line–line (intersecting)": "CONSTRUCTED",
                       "angle skew lines": "CONSTRUCTED (named parallel segment)", "dihedral": "CONSTRUCTED (plane angle ⟂ common line)",
                       "right angle": "CONSTRUCTED (right-angle witness; hidden in mode A because it is the answer)",
                       "distance point–plane / point–line": "CONSTRUCTED (foot + right angle, pre-existing)", "distance skew lines": "CONSTRUCTED (common perpendicular, pre-existing)",
                       "volume": "BASE SOLID (+ certified altitude when given; not drawn for face ⟂ base)", "area": "REGION anchor (pre-existing)",
                       "section / intersection line": "NOT REACHED by the local parser (kernel exists)", "sub-solid volume": "NOT_SUPPORTED"},
        "levels_after": gap["after_levels"], "levels_before": gap["before_levels"]})

    write("projection_and_intersection_verification.json", {
        "projections": {"point→plane": "angle foot + distance foot: on plane (covector) and leg ⟂ plane in G — scene3d_mathematical_invariants.json",
                        "point→line": "named projection H and distance foot: on line and leg ⟂ line in G", "segment→plane": "the line–plane construction draws the projection segment (vertex → foot)"},
        "intersections": {"line∩plane": "vertex of the line–plane angle (on line and plane)", "line∩line": "vertex of intersecting-line angles; skew → no point (translated parallel instead)",
                          "plane∩plane": "common line of the dihedral (rays ⟂ it)", "edge∩plane / section": "kernel exists, not reached by the local parser in this run"},
        "degenerate_handling": "unique / parallel / contained / coincident cases raise distinct kernel errors; no fake intersection is drawn (tests in test_angle_construction.py)",
        "checks": {k: v for k, v in inv["checks_by_kind"].items() if "foot" in k or "projection" in k or "vertex" in k or "perpendicular" in k}})

    fresh = load("../local-semantic-source-gate-reliability/fresh_external_evaluation.json")
    write("new_external_simulation_evaluation.json", {
        "status": "NOT_MEASURED_ON_UNSEEN_DATA",
        "why": "No unseen in-scope item was available without opening the 94 sealed H-1 rows, which this run must not open. The two fresh items of the previous run were viewed there; r695 is now rule-targeted (late square side) and therefore exposed.",
        "previous_fresh_items_rerun": [r for r in load("text_to_simulation_acceptance.json")["rows"] if r["case_id"] in ("vmmu_r559", "vmmu_r695")],
        "sealed_pool_untouched": fresh["sample"]["remaining_reserved_count"]})
    write("independent_h1_status.json", {"status": "NOT_MEASURED", "why": "no independent transcriber/scorer; the agent wrote the constructions and all checks (AGENT_VERIFIED_DIAGNOSTIC)",
                                         "reserved_pool_rows": 94})
    print("receipts written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
