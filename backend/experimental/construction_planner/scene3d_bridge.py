# -*- coding: utf-8 -*-
"""Scene3D compatibility bridge (`construction-scene3d-bridge/1`) for `AXO CONSTRUCTION /1`.

Translates a verified `(ConstructionProofGraph, PresentationStepGraph)` into a
`Scene3D` dictionary compatible with `scene3d.py`, `formation.py`, and
`Scene3DExplorer.tsx`, then validates cumulative geometric continuity via
`construction_continuity.validate_construction_continuity` (`L4`).
"""
from __future__ import annotations

from typing import Any

from app.simulation.geometry import exact as E
from app.simulation.geometry import section as S
from app.simulation.geometry_functions import certificates, construction_continuity

from . import SCENE3D_BRIDGE_VERSION
from .construction_graph import ConstructionProofGraph, PresentationStepGraph
from .construction_objects import ConstructionObject, vec3_to_rational_list
from .construction_state import InitialGeometryFrame


def _scene_object_from_construction_obj(
    obj: ConstructionObject,
    proof_graph: ConstructionProofGraph,
    points_rat_map: dict[str, list[Any]],
) -> dict[str, Any]:
    nid = obj.supporting_node_id
    node = proof_graph.node_map().get(nid) if nid else None
    is_given = obj.origin == "GIVEN_OBJECT"
    deps = list(node.input_object_ids) if node is not None else []
    producer = None if is_given else (node.producing_operation_id if node else "dynamic_planner")
    base: dict[str, Any] = {
        "id": obj.object_id,
        "label": obj.label,
        "notation": obj.object_id if obj.object_kind == "point3" else obj.label,
        "reference": obj.object_id,
        "role": (node.scene3d_render_hints.get("learner_text") if node else None) or obj.label,
        "display_label": obj.label,
        "type": obj.object_kind if obj.object_kind != "relation" else "quantity",
        "origin": "given" if is_given else "derived",
        "producer": producer,
        "depends": [d for d in deps if d in proof_graph.objects and d != obj.object_id],
        "dependency_edges": [{"source_id": d, "relation": "construction"} for d in deps if d in proof_graph.objects and d != obj.object_id],
        "display_group": ["given"] if is_given else (["auxiliary"] if obj.origin == "AUXILIARY_CONSTRUCTION" else ["construction"]),
        "visual_transform": {"translate": [0, 0, 0], "scale": 1},
        "source": {
            "provenance": obj.origin,
            "proof_node_id": nid,
            "producing_operation_id": producer,
        },
        "computational_depends": [d for d in deps if d in proof_graph.objects and d != obj.object_id],
        "visible_prerequisites": [d for d in deps if d in proof_graph.objects and d != obj.object_id],
    }

    val = obj.exact_value
    if obj.object_kind == "point3" and isinstance(val, E.Vec3):
        base["render"] = "point_marker"
        base["xyz"] = vec3_to_rational_list(val)
    elif obj.object_kind == "segment3" and isinstance(val, E.Segment3):
        base["render"] = "segment"
        base["point_a"] = vec3_to_rational_list(val.point_a)
        base["point_b"] = vec3_to_rational_list(val.point_b)
        base["endpoints"] = [base["point_a"], base["point_b"]]
        # Attach endpoint IDs from point canonical matches in proof graph
        ep_ids: list[str] = []
        for target_pt in (base["point_a"], base["point_b"]):
            for oid, coords in sorted(points_rat_map.items()):
                if [str(x) for x in coords] == target_pt:
                    ep_ids.append(oid)
                    if oid not in base["depends"]:
                        base["depends"].append(oid)
                    break
        if len(ep_ids) == 2 and ep_ids[0] != ep_ids[1]:
            base["endpoint_ids"] = ep_ids
    elif obj.object_kind == "line3" and isinstance(val, E.Line3):
        base["render"] = "line"
        base["point"] = vec3_to_rational_list(val.point)
        base["direction"] = vec3_to_rational_list(val.direction)
    elif obj.object_kind == "plane3" and isinstance(val, E.Plane3):
        base["render"] = "surface"
        base["point"] = vec3_to_rational_list(val.point)
        base["normal"] = vec3_to_rational_list(val.normal)
    elif obj.object_kind == "solid" and isinstance(val, S.Polyhedron):
        base["render"] = "mesh"
        v_ids = list(obj.metadata.get("vertex_ids") or ())
        base["vertices"] = [vec3_to_rational_list(v) for v in val.vertices]
        base["vertex_ids"] = v_ids or [oid for oid, o in sorted(proof_graph.objects.items()) if o.object_kind == "point3" and o.origin == "GIVEN_OBJECT"][:len(val.vertices)]
        base["faces"] = [list(f) for f in val.faces]
        base["depends"] = [vid for vid in base["vertex_ids"] if vid in points_rat_map]
        base["shape_class"] = "PYRAMID_LIKE" if len(val.vertices) <= 5 else "PRISM_LIKE"
        base["formation_requirements"] = ["CONSTRUCT_BASE", "CONSTRUCT_LATERAL_BOUNDARY", "CLOSE_SOLID"]
    elif obj.object_kind == "section" and isinstance(val, S.Section):
        base["render"] = "polygon"
        base["polygon"] = [vec3_to_rational_list(v) for v in val.polygon]
        base["closed"] = True
        base["steps"] = []
        base["vertex_sources"] = []
        base["shape_class"] = "SECTION_POLYGON"
        base["formation_requirements"] = ["CUT_SOLID", "CLOSE_SECTION"]
        if "solid_main" in proof_graph.objects and "solid_main" not in base["depends"]:
            base["depends"].append("solid_main")
    elif obj.object_kind == "quantity":
        base["render"] = "readout"
        ex = val if isinstance(val, dict) else {"text": str(val), "coef": str(val), "dim": 0, "unit": ""}
        base["value"] = str(ex.get("text") or ex.get("coef") or "")
        base["exact"] = dict(ex)
    else:
        base["render"] = "non_visual"
    return base


def compile_proof_graph_to_scene3d(
    frame: InitialGeometryFrame,
    proof_graph: ConstructionProofGraph,
    presentation_graph: PresentationStepGraph,
) -> dict[str, Any]:
    """Compile verified proof & presentation graphs into Scene3D format and run L4 validation."""
    from fractions import Fraction

    points_rat_map: dict[str, list[Fraction]] = {
        pid: [pt.x, pt.y, pt.z]
        for pid, pt in frame.points.items()
    }
    for oid, o in proof_graph.objects.items():
        if o.object_kind == "point3" and isinstance(o.exact_value, E.Vec3):
            points_rat_map[oid] = [o.exact_value.x, o.exact_value.y, o.exact_value.z]

    scene_objs: list[dict[str, Any]] = []
    included_ids: set[str] = set()
    # Preserve full GIVEN solid vertices & mesh across pruned alternative plans (multi-plan Scene3D invariance)
    for pid, pt in sorted(frame.points.items()):
        if pid in proof_graph.objects and proof_graph.objects[pid].origin == "GIVEN_OBJECT":
            scene_objs.append(_scene_object_from_construction_obj(proof_graph.objects[pid], proof_graph, points_rat_map))
            included_ids.add(pid)
        elif pid not in proof_graph.objects:
            frame_pt_obj = ConstructionObject(
                object_id=pid,
                object_kind="point3",
                origin="GIVEN_OBJECT",
                canonical_geom_key="",
                label=f"Điểm {pid}",
                exact_value=pt,
                source_fact_refs=frame.source_fact_refs.get("solid", ("s1",)),
                supporting_node_id=None,
            )
            scene_objs.append(_scene_object_from_construction_obj(frame_pt_obj, proof_graph, points_rat_map))
            included_ids.add(pid)

    if frame.polyhedron is not None and "solid_main" not in included_ids:
        if "solid_main" in proof_graph.objects and proof_graph.objects["solid_main"].origin == "GIVEN_OBJECT":
            scene_objs.append(_scene_object_from_construction_obj(proof_graph.objects["solid_main"], proof_graph, points_rat_map))
            included_ids.add("solid_main")
        elif "solid_main" not in proof_graph.objects:
            frame_solid_obj = ConstructionObject(
                object_id="solid_main",
                object_kind="solid",
                origin="GIVEN_OBJECT",
                canonical_geom_key="",
                label="Khối đa diện",
                exact_value=frame.polyhedron,
                source_fact_refs=frame.source_fact_refs.get("solid", ("s1",)),
                supporting_node_id=None,
                metadata={"vertex_ids": sorted(frame.points.keys())},
            )
            scene_objs.append(_scene_object_from_construction_obj(frame_solid_obj, proof_graph, points_rat_map))
            included_ids.add("solid_main")

    # Emit remaining GIVEN objects from proof graph, then derived/aux objects in topological node order
    for oid, obj in sorted(proof_graph.objects.items()):
        if oid not in included_ids and obj.origin == "GIVEN_OBJECT" and obj.object_kind in ("point3", "solid", "segment3"):
            scene_objs.append(_scene_object_from_construction_obj(obj, proof_graph, points_rat_map))
            included_ids.add(oid)
    for node in proof_graph.nodes:
        for oid in node.output_objects:
            if oid in proof_graph.objects and oid not in included_ids and proof_graph.objects[oid].object_kind != "relation":
                scene_objs.append(_scene_object_from_construction_obj(proof_graph.objects[oid], proof_graph, points_rat_map))
                included_ids.add(oid)
    for oid, obj in sorted(proof_graph.objects.items()):
        if oid not in included_ids and obj.object_kind != "relation":
            scene_objs.append(_scene_object_from_construction_obj(obj, proof_graph, points_rat_map))
            included_ids.add(oid)

    # Attach exact perpendicular_witness to any perpendicular segment whose endpoints verify perp_point_plane_witness
    obj_map = {o["id"]: o for o in scene_objs}
    for oid, o in obj_map.items():
        if o.get("type") == "segment3" and o.get("producer") in ("op.project_point_to_plane",) and len(o.get("endpoint_ids") or ()) == 2:
            pa_id, pb_id = o["endpoint_ids"]
            src_node = proof_graph.node_map().get(o["source"].get("proof_node_id") or "")
            pl_id = (src_node.geometry_context.get("inputs") or {}).get("plane") if src_node else None
            if pl_id and pl_id in proof_graph.objects and isinstance(proof_graph.objects[pl_id].exact_value, E.Plane3):
                pl_obj = proof_graph.objects[pl_id].exact_value
                # Find any 3 point IDs lying in pl_id
                in_pl_ids = [
                    pid for pid, pval in sorted(points_rat_map.items())
                    if pl_obj.signed_eval(E.Vec3(*pval)) == 0
                ]
                # Determine which endpoint lies on pl_obj (`foot_id`) vs away (`from_id`)
                foot_id = pb_id if pl_obj.signed_eval(E.Vec3(*points_rat_map[pb_id])) == 0 else pa_id
                from_id = pa_id if foot_id == pb_id else pb_id
                if len(in_pl_ids) >= 3:
                    try:
                        cert = certificates.certify_line_plane_perpendicularity(
                            from_id=from_id,
                            foot_id=foot_id,
                            plane_id=pl_id,
                            plane_vertex_ids=in_pl_ids[:3],
                            points_by_id=points_rat_map,
                            chart_metric=frame.chart_metric,
                            provenance_status="PROVEN",
                            rule="dynamic_planner_orthogonal_projection",
                        )
                        o["perpendicular_witness"] = cert
                    except certificates.CertificateError:
                        pass

    events: list[dict[str, Any]] = []
    formation_steps: list[dict[str, Any]] = []
    cumulative_visible: list[str] = []
    seen_created: set[str] = set()
    step_id_to_created: dict[str, list[str]] = {}

    # Step 0 must expose all GIVEN point/solid/segment objects included in initial stage
    given_init_ids = [
        o["id"]
        for o in scene_objs
        if o["origin"] == "given" and o["type"] in ("point3", "solid", "segment3")
    ]
    # Also ensure given plane/line dependencies of step 0 are initialized at step 0 cleanly
    extra_given_ids = [
        o["id"]
        for o in scene_objs
        if o["origin"] == "given" and o["id"] not in given_init_ids and o["type"] in ("line3", "plane3")
    ]
    all_init_ids = [*given_init_ids, *extra_given_ids]
    events.append(
        {
            "step_index": 0,
            "action": "INIT",
            "object": "solid_main" if "solid_main" in all_init_ids else (all_init_ids[0] if all_init_ids else None),
            "objects": all_init_ids,
            "depends": [],
            "explanation": "Khởi tạo các điểm, cạnh và khối ban đầu từ giả thiết đã kiểm chứng.",
            "semantic_kind": "GEOMETRY_CONSTRUCTION",
            "learner_text": "Khởi tạo hình ban đầu từ giả thiết của đề bài.",
        }
    )
    cumulative_visible.extend(all_init_ids)
    seen_created.update(all_init_ids)
    step_id_to_created["pstep_0"] = list(all_init_ids)

    formation_steps.append(
        {
            "step_index": 0,
            "step_id": "pstep_0",
            "coordinate_frame_id": construction_continuity.CANONICAL_COORDINATE_FRAME_ID,
            "visible_ids": list(cumulative_visible),
            "readout_ids": [],
            "focus_ids": [oid for oid in given_init_ids if obj_map[oid]["type"] in ("point3", "solid")][:6],
            "depends_on": [],
            "visible_prerequisites": [],
            "preconditions": ["frame:canonical_chart_v1", "source_gate:verified"],
            "created_ids": list(all_init_ids),
            "reused_ids": [],
            "highlighted_ids": [],
            "retired_ids": [],
            "verification_refs": ["source_gate:verified", "spd_metric:verified"],
            "semantic_kind": "GEOMETRY_CONSTRUCTION",
            "learner_text": "Khởi tạo hình ban đầu từ giả thiết của đề bài.",
        }
    )

    pstep_idx = 0
    for pstep in presentation_graph.steps:
        if pstep.action_type == "INIT_GIVEN":
            continue
        pstep_idx += 1
        new_vis_objs = [oid for oid in pstep.object_ids if oid in obj_map and oid not in seen_created and obj_map[oid]["type"] != "quantity"]
        new_read_objs = [oid for oid in pstep.object_ids if oid in obj_map and obj_map[oid]["type"] == "quantity"]
        # Ensure any dependency of new_vis_objs/new_read_objs is already visible
        for oid in [*new_vis_objs, *new_read_objs]:
            for dep in obj_map[oid].get("depends") or ():
                if dep in obj_map and dep not in seen_created and obj_map[dep]["type"] != "quantity":
                    new_vis_objs.insert(0, dep)
                    seen_created.add(dep)
            seen_created.add(oid)

        for oid in new_vis_objs:
            if oid not in cumulative_visible:
                cumulative_visible.append(oid)

        if pstep.action_type == "MEASURE_GOAL" or new_read_objs:
            skind = "FINAL_RESULT"
            ev_act = "READOUT"
            ev_obj = new_read_objs[0] if new_read_objs else None
        else:
            skind = "GEOMETRY_CONSTRUCTION"
            ev_act = "CREATE" if new_vis_objs else "HIGHLIGHT"
            ev_obj = new_vis_objs[0] if new_vis_objs else (pstep.object_ids[0] if pstep.object_ids else None)

        ev_deps = sorted({dep for oid in [*new_vis_objs, *new_read_objs] for dep in (obj_map[oid].get("depends") or ())})
        events.append(
            {
                "step_index": pstep_idx,
                "action": ev_act,
                "object": ev_obj,
                "objects": [*new_vis_objs, *new_read_objs] if new_vis_objs or new_read_objs else list(pstep.visual_emphasis),
                "depends": ev_deps,
                "explanation": pstep.learner_text,
                "semantic_kind": skind,
                "learner_text": pstep.learner_text,
            }
        )
        # Reused IDs: dependencies that were already seen in earlier steps
        prior_set = set(cumulative_visible) - set(new_vis_objs)
        reused = [d for d in ev_deps if d in prior_set]
        formation_steps.append(
            {
                "step_index": pstep_idx,
                "step_id": pstep.step_id,
                "coordinate_frame_id": construction_continuity.CANONICAL_COORDINATE_FRAME_ID,
                "visible_ids": list(cumulative_visible),
                "readout_ids": list(new_read_objs),
                "focus_ids": list(new_vis_objs or new_read_objs or pstep.visual_emphasis),
                "depends_on": list(reused),
                "visible_prerequisites": list(reused),
                "preconditions": list((pstep.explanation_evidence.get("preconditions") or [])),
                "created_ids": [*new_vis_objs, *new_read_objs],
                "reused_ids": list(reused),
                "highlighted_ids": [eid for eid in pstep.visual_emphasis if eid in prior_set],
                "retired_ids": [],
                "verification_refs": [f"proof_node:{ref}" for ref in pstep.construction_graph_refs],
                "semantic_kind": skind,
                "learner_text": pstep.learner_text,
            }
        )

    scene3d: dict[str, Any] = {
        "bridge_version": SCENE3D_BRIDGE_VERSION,
        "objects": scene_objs,
        "events": events,
        "formation": {"steps": formation_steps},
        "free_objects": [],
        "unused_auxiliary_ids": [],
        "diagnostics": {
            "source_proof_graph_id": proof_graph.graph_id,
            "source_presentation_graph_id": presentation_graph.graph_id,
            "dynamic_planner_used": True,
        },
        "chart_metric": [list(r) for r in frame.chart_metric_strs],
        "length_unit": frame.length_unit,
    }
    construction_continuity.enrich_construction_continuity(scene3d)
    return scene3d
