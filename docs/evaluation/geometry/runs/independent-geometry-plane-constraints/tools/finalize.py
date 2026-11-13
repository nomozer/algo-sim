"""Development receipts of run `independent-geometry-plane-constraints` (agent-written probes, AGENT_DIAGNOSTIC oracle).

  python finalize.py <before_backend_dir>      # from the worktree root, backend interpreter
  python finalize.py --timing                  # child (internal)
Before = an archive of the start product ea4b2a197; after = the worktree. Nothing here reads the locked holdouts.
"""
from __future__ import annotations

import copy
import json
import os
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_plane_constraints as V  # noqa: E402
from plane_constraint_probes import PROBES, P, CUBE  # noqa: E402

NOW = datetime.now(timezone.utc).isoformat()
ANGLE_TEXTS = {
    "planes_SBC_SCD_60": P + "Tính góc giữa hai mặt phẳng (SBC) và (SCD).",
    "planes_SCD_SBC_swapped": P + "Tính góc giữa hai mặt phẳng (SCD) và (SBC).",
    "planes_cube_A'BD_C'BD": CUBE + "Tính góc giữa hai mặt phẳng (A'BD) và (C'BD).",
    "planes_SAB_SAD_90": P + "Tính góc giữa hai mặt phẳng (SAB) và (SAD).",
    "planes_same_plane_0": P + "Tính góc giữa hai mặt phẳng (SAB) và (SAB).",
    "dihedral_bracket_BSCD_120": P + "Tính số đo của góc nhị diện [B, SC, D].",
    "dihedral_half_planes": P + "Tính góc nhị diện tạo bởi hai nửa mặt phẳng (SBC) và (SCD) có cạnh chung SC.",
    "dihedral_cube_A_BD_C'": CUBE + "Tính số đo góc nhị diện [A, BD, C'].",
}


def git(*a):
    return subprocess.check_output(["git", *a], cwd=ROOT).decode("utf-8", "replace").strip()


def write(n, d):
    (RUN / n).write_text(json.dumps({"run_id": RUN.name, "generated_at_utc": NOW, "head": git("rev-parse", "HEAD"), **d},
                                    ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def timing_child() -> None:
    from app.ai.adaptive_input_router import route_text_input
    texts = json.loads(sys.stdin.read())
    for t in texts:
        route_text_input(t, allow_live_ai=False)
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


def prov_checks(sc: dict) -> list[dict]:
    """Provenance of the drawn section: it depends on its solid and its plane; the plane depends on ≥ 3 drawn points."""
    obj = {o["id"]: o for o in sc["objects"]}
    out = []
    for o in sc["objects"]:
        if o["type"] == "section":
            dep = o.get("depends") or []
            pl = obj.get(dep[1]) if len(dep) > 1 else None
            out.append({"check": "section_depends_on_solid_and_plane",
                        "ok": len(dep) >= 2 and obj.get(dep[0], {}).get("type") == "solid" and (pl or {}).get("type") == "plane3"})
            out.append({"check": "cutting_plane_depends_on_drawn_points",
                        "ok": bool(pl) and len([x for x in pl.get("depends") or [] if obj.get(x, {}).get("type") == "point3"]) >= 3})
    return out


def all_checks(text: str, sc: dict) -> list[dict]:
    return V.VC.check("p", sc) + V.plane_checks(text, sc) + prov_checks(sc)


def _sec(sc):
    return next((o for o in sc["objects"] if o["type"] == "section"), None)


def _shift(poly, k, d):
    return [[str(F(x) + (d if i == k else 0)) for i, x in enumerate(p)] for p in poly]


def m_normal(sc, text):                       # tilt the plane: one vertex leaves it
    s = _sec(sc); s["polygon"][0] = _shift([s["polygon"][0]], 2, F(1, 7))[0]; return True


def m_position(sc, text):                     # translate the whole section along z
    s = _sec(sc); s["polygon"] = _shift(s["polygon"], 2, F(1, 9)); return True


def m_point_replaced(sc, text):               # the stated through-point moves
    import re
    m = re.search(r"(?:đi qua|qua|Qua)\s+([A-Z]'?)\s", text)
    o = next((o for o in sc["objects"] if m and o["id"] == m.group(1).replace("'", "_prime") and o["type"] == "point3"), None)
    if o is None:
        return False
    o["xyz"] = [str(F(x) + d) for x, d in zip(o["xyz"], (F(1, 5), F(2, 7), F(3, 11)))]; return True   # generic: in no probe plane


def m_drop_vertex(sc, text):
    s = _sec(sc); del s["polygon"][1]; return True


def m_wrong_edges(sc, text):                  # connect non-adjacent vertices (only meaningful from 4 vertices on)
    s = _sec(sc)
    if len(s["polygon"]) < 4:
        return False
    s["polygon"][1], s["polygon"][2] = s["polygon"][2], s["polygon"][1]; return True


def m_vertex_replaced(sc, text):
    s = _sec(sc); s["polygon"][0] = list(s["polygon"][1]); return True


def m_provenance(sc, text):
    s = _sec(sc); s["depends"] = []; return True


def m_flip_ray(sc, text):
    return V.VC.MUTATIONS["flip_angle_ray"](sc)


MUTS = {"plane_normal_changed": m_normal, "plane_position_shifted": m_position, "point_on_plane_replaced": m_point_replaced,
        "section_vertex_dropped": m_drop_vertex, "section_edges_connected_wrongly": m_wrong_edges,
        "section_vertex_replaced": m_vertex_replaced, "provenance_removed": m_provenance, "angle_ray_flipped": m_flip_ray}


def main(before: Path) -> int:
    texts = {k: t for k, (_c, _e, t) in PROBES.items()}
    after_rows, before_rows = V.evaluate(ROOT / "backend"), V.evaluate(before)
    raw_after = V.run(ROOT / "backend", {**texts, **ANGLE_TEXTS})
    raw_before_angles = V.run(before, ANGLE_TEXTS)
    sec_probes = [k for k, (c, e, _t) in PROBES.items() if e[0] == "SERVED" and e[1] != "line"]
    ref_probes = [k for k, (c, e, _t) in PROBES.items() if e[0] == "REFUSED"]

    def outcome(rows, ks):
        return {k: rows[k]["outcome"] for k in ks}

    # ── grammar / parser receipt ────────────────────────────────────────────────────────────────────────────────────
    sys.path.insert(0, str(ROOT / "backend"))
    os.environ["ALLOW_LIVE_AI"] = "0"
    from app.ai.local_geometry_parser import parse_geometry_problem_locally
    grammar = []
    for k, (cat, exp, t) in PROBES.items():
        r = parse_geometry_problem_locally(t, use_cache=False)
        pl = r.payload or {}
        grammar.append({"probe": k, "category": cat, "expected": exp[0], "parse_status": r.status,
                        "unparsed_clauses": list(r.source_coverage.unparsed_fact_candidates) + list(r.source_coverage.unparsed_goal_candidates),
                        "planes": [{"plane_kind": s.get("plane_kind"), "through_point": s.get("through_point"),
                                    "parallel_plane": s.get("parallel_plane"), "perpendicular_line": s.get("perpendicular_line"),
                                    "constraints": s.get("constraints")} for s in pl.get("derived_sections") or []],
                        "section_goals": [g.get("kind") for g in pl.get("simulation_goals") or [] if "section" in g.get("kind", "")],
                        "before": before_rows[k]["outcome"], "after": after_rows[k]["outcome"], "reason_after": after_rows[k]["reason"]})
    write("plane_constraint_grammar_tests.json", {
        "probe_class": "NEW_DIAGNOSTIC_DEVELOPMENT (agent-written, tools/plane_constraint_probes.py)",
        "unit_tests": ["backend/tests/geometry/test_plane_constraint_sections.py"],
        "categories": sorted({r["category"] for r in grammar}),
        "as_expected_before": sum(r["before"] == "AS_EXPECTED" for r in grammar),
        "as_expected_after": sum(r["after"] == "AS_EXPECTED" for r in grammar), "probes": len(grammar),
        "wrong_served_before": sum(r["before"] == "WRONG_SERVED" for r in grammar),
        "wrong_served_after": sum(r["after"] == "WRONG_SERVED" for r in grammar),
        "not_served_after": [r["probe"] for r in grammar if r["after"] == "NOT_SERVED"],
        "rows": grammar})

    # ── uniqueness / degenerate / composition ───────────────────────────────────────────────────────────────────────
    serv = [k for k in sec_probes if after_rows[k]["status"] == "SERVED"]
    write("plane_uniqueness_verification.json", {
        "rule": "a plane is built only when the stated constraints fix exactly one plane: the engine's affine-rank certificate (rank 2: unique; < 2: PLANE_NOT_UNIQUE; inconsistent: INCONSISTENT_FACTS) and, independently here, every served cutting plane is rechecked against the stated relation",
        "served_with_checks": {k: {"checks": len(after_rows[k]["checks"]), "failed": after_rows[k]["failed_checks"],
                                   "relation_checks": [c["check"] for c in after_rows[k]["checks"] if c["check"].startswith(("cut_plane", "stated_line", "segment_"))]}
                               for k in serv},
        "underdetermined_refused": {k: after_rows[k]["reason"] for k in ref_probes if PROBES[k][0] == "underconstrained"},
        "underdetermined_reason_note": "underdetermined wordings are not read locally (refused LIVE_AI_DISABLED, i.e. not understood); the engine's PLANE_NOT_UNIQUE is reached when a read definition is underdetermined (compound_contains_parallel_not_unique)"})
    write("plane_contradiction_and_degenerate_cases.json", {
        "cases": {k: {"category": PROBES[k][0], "status": after_rows[k]["status"], "reason": after_rows[k]["reason"]}
                  for k in ref_probes},
        "coincident_vs_parallel": {"before": "coincident planes refused with PARALLEL_PLANES", "after": "CONTAINED_INFINITE_INTERSECTION (existing kernel code: the intersection is the whole plane); distinct parallel planes keep PARALLEL_PLANES",
                                   "tests": "test_plane_constraint_sections.py::test_coincident_planes_are_not_called_parallel"},
        "point_or_edge_contact": "NOT_REACHED by any supported wording (no constraint-defined plane in the probes touches the solid only in a point or an edge); the kernel codes PLANE_TOUCHES_VERTEX / PLANE_TOUCHES_EDGE exist",
        "wrong_served": sum(after_rows[k]["outcome"] == "WRONG_SERVED" for k in ref_probes)})
    write("constraint_to_section_composition.json", {
        "chain": "verified point + verified plane/line + stated relation → engine plane (existence/uniqueness certificate) → polyhedron section (closure certificate) → Scene3D section polygon",
        "before": outcome(before_rows, sec_probes), "after": outcome(after_rows, sec_probes),
        "served_before": sum(before_rows[k]["status"] == "SERVED" for k in sec_probes),
        "served_after": sum(after_rows[k]["status"] == "SERVED" for k in sec_probes), "section_probes": len(sec_probes),
        "served_after_checks_failed": sum(len(after_rows[k].get("failed_checks") or []) for k in sec_probes),
        "area_sq_after": {k: after_rows[k].get("area_sq") for k in serv},
        "boundary_after": {k: after_rows[k].get("boundary") for k in serv}})
    il = "intersection_with_derived_plane"
    write("constraint_to_intersection_composition.json", {
        "probe": il, "text": texts[il], "before": before_rows[il]["outcome"], "after": after_rows[il]["outcome"],
        "reason_after": after_rows[il]["reason"],
        "status": "NOT_SUPPORTED: an intersection line with a plane defined by relations is not read — the planner's intersection_line takes two three-label planes and the Source Gate grounds both in the quote; a constraint-defined plane has no three source labels. Three-label planes (verified-section-intersection-dihedral-local) are unchanged.",
        "new_intersection_lines": 0})
    write("source_grounding_verification.json", {
        "source_gate_changed": True,
        "change": "closed grammar `_MAT_TEN_DIEM_RE` (registry): a named plane defined by a line and a point, or by two lines with exactly one common label, names the plane of those three labels; read only in the call's own quotes, a name defined twice with different points is dropped; the section request 'xác định / tìm / dựng / vẽ thiết diện … cắt bởi (P)' is read only when (P) is such a definition of exactly the call's plane",
        "not_loosened": ["no existing pattern removed or widened", "four distinct labels or 'song song' lines are never read",
                         "an undefined plane name is never read (parser and gate)", "goal-as-premise and conditional guards unchanged",
                         "a dihedral question substituted into a plane–plane angle payload is refused (test_a_dihedral_question_is_never_served_as_the_angle_between_two_planes)"],
        "facts_without_source": 0,
        "refusals_after": {k: after_rows[k]["reason"] for k in ref_probes}})
    write("existing_plane_constraint_capability_audit.json", {
        "kernel_and_planner": {
            "plane through three points": "EXISTING (planner section points / engine Plane3.through)",
            "plane through a point parallel to a plane": "EXISTING (MAT_SONG_SONG; engine checks ∥, not the same plane, not a face)",
            "plane through a point perpendicular to a line": "EXISTING (MAT_VUONG_DUONG; ⊥ certificate in G)",
            "plane through a point parallel to two lines": "EXISTING (MAT_HAI_DUONG; dependent directions ⇒ PLANE_NOT_UNIQUE)",
            "plane by relations (contains points, ∥ line, ⊥ plane)": "EXISTING (MAT_RANG_BUOC C17; affine-rank existence/uniqueness)",
            "plane through a point perpendicular to a plane": "REFUSED by design (PLANE_NOT_UNIQUE)",
            "plane–plane intersection": "EXISTING (intersect_plane_plane)", "orthogonal projection": "EXISTING",
            "polyhedron section": "EXISTING (closure certificate)"},
        "local_parser_before": {"named plane definitions (6c/6c-2/6d)": "read", "section question on a named plane": "only 'Dựng thiết diện … bởi (P)' (rule 7c) — 'Xác định / Tìm thiết diện … cắt bởi (P)' unread",
                                "'song song với (mặt phẳng) đáy'": "unread", "line + point / two lines": "unread",
                                "mặt phẳng trung trực": "unread", "intersection with a named plane": "unread"},
        "new_kernel_primitives": 0, "new_planner_rules": 0,
        "source_gate_grammar_added": "named plane by a line and a point / two intersecting lines (see source_grounding_verification.json)",
        "evidence": "plane_constraint_grammar_tests.json (before/after per probe)"})

    # ── angle semantics ─────────────────────────────────────────────────────────────────────────────────────────────
    def ang(raw):
        out = {}
        for k in ANGLE_TEXTS:
            r = raw[k]
            sc = r["scene"] or {}
            ac = [o["angle_construction"] for o in sc.get("objects", []) if o.get("angle_construction")]
            cks = [c for c in V.VC.check("a", sc) if c["check"].startswith("angle")] if r["status"] == "SERVED" else []
            out[k] = {"status": r["status"] or "REFUSED", "reason": r["reason"], "constructions": len(ac),
                      "angle_domain": [a.get("angle_domain") for a in ac], "checks_failed": [c["check"] for c in cks if not c["ok"]]}
        return out
    write("angle_semantics_audit.json", {
        "types": {"ANGLE_BETWEEN_LINES": "non-oriented, [0°, 90°]", "ANGLE_BETWEEN_LINE_AND_PLANE": "[0°, 90°]",
                  "ANGLE_BETWEEN_PLANES": "non-oriented, [0°, 90°] — drawn rays with signed cos ≥ 0 (angle_domain)",
                  "DIHEDRAL_ANGLE": "a premise only (dihedral_angle with two half-planes, (0°, 180°)); never an asked quantity"},
        "dihedral_question_behaviour": "a question asking a dihedral angle by its half-planes ([B, SC, D], 'hai nửa mặt phẳng') is not read on the local route and, substituted into a plane–plane angle payload, is refused by the Source Gate's closed ask grammar ('góc giữa / tạo bởi / hợp bởi'): an acute substitute is never served. Canonical code: no new code is added; the refusal is QUESTION_CONTEXT_UNSUPPORTED (payload) / LIVE_AI_DISABLED (local, unread).",
        "before": ang(raw_before_angles), "after": ang(raw_after),
        "tests": ["backend/tests/geometry/test_angle_construction_domain.py (60/120, 45/135, swapped, renamed, lines 135→45, parallel)",
                  "backend/tests/geometry/test_plane_constraint_sections.py::test_a_dihedral_question_is_never_served_as_the_angle_between_two_planes"],
        "degenerate": {"0°": "the same plane twice: served cos² = 1, no construction drawn", "90°": "served cos² = 0, no construction (right angle is the answer)",
                       "180°": "not meaningful for an angle between planes; dihedral 180° not asked (unsupported)"}})

    # ── mutations ───────────────────────────────────────────────────────────────────────────────────────────────────
    mut = {k: {"applied": 0, "caught": 0, "missed": []} for k in MUTS}
    for k, t in {**texts, **ANGLE_TEXTS}.items():
        sc = raw_after[k]["scene"] if raw_after[k]["status"] == "SERVED" else None
        if not sc:
            continue
        base = [c["check"] for c in all_checks(t, sc) if not c["ok"]]
        for name, fn in MUTS.items():
            if name == "angle_ray_flipped" and not any(o.get("angle_construction") for o in sc["objects"]):
                continue
            if name != "angle_ray_flipped" and _sec(sc) is None:
                continue
            m = copy.deepcopy(sc)
            if not fn(m, t):
                continue
            mut[name]["applied"] += 1
            failed = [c["check"] for c in all_checks(t, m) if not c["ok"]]
            if set(failed) - set(base):
                mut[name]["caught"] += 1
            else:
                mut[name]["missed"].append(k)
    write("geometry_mutation_verification.json", {
        "oracle_level": "AGENT_DIAGNOSTIC (independent code path: Fractions + envelope Gram G; same agent as the construction)",
        "policy": "a mutation counts as caught when a check that passed on the served scene fails on the mutated one; reversing the cyclic order of a polygon is not an error (orientation is not in the contract) and is not applied",
        "mutations": mut, "applied": sum(v["applied"] for v in mut.values()), "caught": sum(v["caught"] for v in mut.values())})

    # ── backend latency ─────────────────────────────────────────────────────────────────────────────────────────────
    sample = [texts[k] for k in serv[:12]]
    tb, ta = timing(before, sample), timing(ROOT / "backend", sample)
    write("performance_impact.json", {
        "backend_route_ms": {"method": "route_text_input median of 5 warm calls per probe, before (ea4b2a197 archive) and after, separate child processes, same host",
                             "probes": serv[:12], "before": tb, "after": ta,
                             "median_before": statistics.median(tb), "median_after": statistics.median(ta),
                             "note": "before refuses most of these texts at parse time (no planner/engine work), so after > before is the cost of now building the section"},
        "browser": "scene3d_browser_e2e.json (measured separately)", "physical_low_end": "PHYSICAL_LOW_END_NOT_MEASURED"})
    print("grammar", sum(r["after"] == "AS_EXPECTED" for r in grammar), "/", len(grammar), "mut", {k: (v["applied"], v["caught"]) for k, v in mut.items()},
          "ms", statistics.median(tb), statistics.median(ta))
    return 0


if __name__ == "__main__":
    if "--timing" in sys.argv:
        timing_child()
        raise SystemExit(0)
    raise SystemExit(main(Path(sys.argv[1])))
