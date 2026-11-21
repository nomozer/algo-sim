"""Causal / visual-semantics mutations of real served Route D scenes (run `scene3d-causal-pedagogical-integrity`).

Each mutation breaks one invariant and must be caught — by the independent `causal_audit` (structure) or by the product
adapter `build_adapter4_response` (geometry, proof ↔ scene binding). A mutation counts as caught only when the original
scene is clean / served and the mutant is flagged / refused.

  python causal_mutations.py <out.json>        # from the worktree root, backend interpreter
"""
from __future__ import annotations

import copy
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path[:0] = [str(ROOT / "backend"), str(Path(__file__).resolve().parent)]
os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""

SQ = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a"
SECTION = SQ + ", M là trung điểm của SA, mặt phẳng (P) đi qua M và song song với mặt đáy. Xác định thiết diện của hình chóp bởi (P)."
RB = "Cho hình chóp S.ABC có đáy là tam giác vuông tại B, SA vuông góc với đáy và SA = AB. "
PERP = RB + "Tính góc giữa hai mặt phẳng (SAC) và (ABC)."
ANGLE = RB + "Tính góc giữa hai mặt phẳng (SBC) và (ABC)."


def _ev(sc, oid):
    return next(e for e in sc["events"] if e.get("object") == oid and e.get("action") == "CREATE")


def _obj(sc, oid):
    return next(o for o in sc["objects"] if o["id"] == oid)


def swap_birth(sc):            # the plane (P) is created before the point H it passes through
    plane = next(o["id"] for o in sc["objects"] if o["type"] == "plane3" and "H" in (o.get("visible_prerequisites") or ()))
    e_p, e_h = _ev(sc, plane), _ev(sc, "H")
    e_p["step_index"], e_h["step_index"] = e_h["step_index"], e_p["step_index"]


def delete_create(sc):         # H is never created
    sc["events"] = [e for e in sc["events"] if not (e.get("object") == "H" and e.get("action") == "CREATE")]


def before_prerequisite(sc):   # the plane through H is moved to step 1, before H is created
    plane = next(o for o in sc["objects"] if o["type"] == "plane3" and "H" in (o.get("visible_prerequisites") or ()))
    e = _ev(sc, plane["id"])
    e["step_index"] = 1


def hidden_vector(sc):         # H's visual prerequisite replaced by the internal vector it was computed with
    vec = next(o["id"] for o in sc["objects"] if o.get("type") == "vector3")
    _obj(sc, "H")["visible_prerequisites"] = [vec]


def delete_source(sc):         # the source point M is removed from the scene
    sc["objects"] = [o for o in sc["objects"] if o["id"] != "M"]


def unsourced_object(sc):      # an object depending on nothing that exists
    sc["objects"].append({"id": "X_fake", "type": "point3", "render": "point_marker", "origin": "derived",
                          "depends": ["ghost"], "visible_prerequisites": ["ghost"], "xyz": ["9", "9", "9"]})


def remove_helper(sc):         # the auxiliary H the plane (P) is built through disappears
    sc["objects"] = [o for o in sc["objects"] if o["id"] != "H"]


def readout_uncertified(sc):   # a readout of a quantity that does not exist
    sc["formation"]["steps"][-1]["readout_ids"] = ["kq_unknown"]


def duplicate_create(sc):
    e = copy.deepcopy(_ev(sc, "H"))
    e["step_index"] += 1
    sc["events"].append(e)


STRUCTURAL = [("swap_create_order", swap_birth), ("delete_create", delete_create), ("object_before_prerequisite", before_prerequisite),
              ("visual_dependency_replaced_by_hidden_vector", hidden_vector), ("delete_source_object", delete_source),
              ("insert_unsourced_object", unsourced_object), ("delete_required_helper", remove_helper),
              ("readout_for_uncertified_quantity", readout_uncertified), ("duplicate_create", duplicate_create)]


def move_point(r):             # a drawn point moved off its kernel coordinates (an intersection / construction point)
    o = next(o for o in r.scene3d["objects"] if o["id"] == "H")
    o["xyz"] = [str(int(o["xyz"][0]) + 1) if o["xyz"][0].lstrip("-").isdigit() else "7", *o["xyz"][1:]]


def wrong_plane_ray(r):        # the plane-angle ray drawn in the wrong plane (consistent points)
    q = next(o for o in r.scene3d["objects"] if o["id"] == "kq_q1")
    pts = {o["id"]: o["xyz"] for o in r.scene3d["objects"] if o["type"] == "point3"}
    q["angle_construction"]["arms"][1] = {"to": list(pts["C"]), "to_id": "C"}


def right_angle_to_other(r):   # a proven right angle drawn as another kind of angle
    q = next(o for o in r.scene3d["objects"] if o["id"] == "kq_q1")
    q["angle_construction"]["relation"] = "line_plane"


GEOMETRIC = [("move_intersection_point", SECTION, move_point), ("ray_in_wrong_plane", ANGLE, wrong_plane_ray),
             ("right_angle_changed_to_other_kind", PERP, right_angle_to_other)]


def main(out: Path) -> int:
    from causal_audit import audit
    from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route
    from app.ai.local_geometry_parser import parse_geometry_problem_locally as P
    rows = []
    base = run_typed_fact_next_v2_route(P(SECTION, use_cache=False).payload).scene3d
    assert audit(base)["violation_count"] == 0
    for name, f in STRUCTURAL:
        sc = copy.deepcopy(base)
        f(sc)
        a = audit(sc)
        rows.append({"mutation": name, "checker": "causal_audit", "caught": a["violation_count"] > 0,
                     "violations": sorted(a["violations"])})
    for name, text, f in GEOMETRIC:
        r = run_typed_fact_next_v2_route(P(text, use_cache=False).payload)
        ok = build_adapter4_response(r, text)["route_d"]["status"] == "SERVED"
        bad = copy.deepcopy(r)
        f(bad)
        refused = build_adapter4_response(bad, text)["route_d"]["status"] == "REFUSED"
        rows.append({"mutation": name, "checker": "build_adapter4_response", "caught": ok and refused})
    data = {"run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "base_scene_clean": True,
            "rows": rows, "caught": sum(r["caught"] for r in rows), "total": len(rows)}
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(data["caught"], "/", data["total"], [r["mutation"] for r in rows if not r["caught"]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1])))
