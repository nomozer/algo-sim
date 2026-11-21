# -*- coding: utf-8 -*-
"""Source-Gate-respecting bridge from `typed-facts/2` or `TypedFactNext /2` -> `(InitialGeometryFrame, GoalSpec)`.

Runs `planner.lap_ke_hoach` + `registry.kiem_nguon` / `engine.dung_tu_loi_goi` FIRST so:
- Source quotes, roles, negations, units, and labels are NEVER bypassed;
- Only AFTER Source Gate acceptance are the certified solid coordinates + SPD Gram metric
  extracted, and stated point/section constructions translated into `PendingConstruction`s
  plus `GoalSpec` for `DynamicConstructionPlanner`!
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from app.simulation.geometry import exact as E
from app.simulation.geometry_functions import engine, planner, registry
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2

from . import VERIFIED_INPUT_BRIDGE_VERSION
from .construction_operators import GoalSpec
from .construction_state import (
    InitialGeometryFrame,
    PendingConstruction,
    build_initial_frame,
)

os.environ.setdefault("ALLOW_LIVE_AI", "0")
os.environ.setdefault("GEMINI_API_KEY", "")


@dataclass(frozen=True)
class VerifiedBridgeOutcome:
    bridge_version: str
    accepted: bool
    source_gate_status: str  # VERIFIED | REFUSED
    source_gate_code: str | None
    source_gate_reason: str | None
    frame: InitialGeometryFrame | None
    goal_spec: GoalSpec | None
    baseline_calls: tuple[dict[str, Any], ...] = ()


_POINT_KINDS = frozenset({"midpoint", "centroid", "divide_segment", "point_reflection", "intersect_line_line", "intersect_line_plane"})


def bridge_verified_facts_to_construction_input(
    *,
    case_id: str,
    problem_text: str,
    raw_facts_payload: dict[str, Any],
    point_distance_semantics: bool = False,
) -> VerifiedBridgeOutcome:
    """Translate verified `typed-facts/2` or `typed-fact-next/2` without bypassing `Source Gate`."""
    schema = raw_facts_payload.get("schema") or raw_facts_payload.get("schema_version")
    try:
        if schema == "typed-fact-next/2":
            tf2 = bridge_v2(raw_facts_payload)
        else:
            tf2 = dict(raw_facts_payload)
    except Exception as exc:
        code = str(getattr(exc, "code", None) or "BRIDGE_VALIDATION_ERROR")
        return VerifiedBridgeOutcome(VERIFIED_INPUT_BRIDGE_VERSION, False, "REFUSED", code, str(exc), None, None)

    facts = list(tf2.get("facts") or ())
    try:
        kh = planner.lap_ke_hoach({"schema": "typed-facts/2", "facts": facts}, problem_text)
    except Exception as exc:
        code = str(getattr(exc, "code", None) or "PLANNER_REFUSED")
        return VerifiedBridgeOutcome(VERIFIED_INPUT_BRIDGE_VERSION, False, "REFUSED", code, str(exc), None, None)

    # Run Source Gate (`registry.kiem_nguon`) directly on planned calls without modifying backend/app/**!
    try:
        ke_hoach = registry.doc_ke_hoach({"calls": kh.calls})
        registry.kiem_nguon(
            ke_hoach,
            problem_text,
            auxiliary=tuple(kh.auxiliary),
        )
    except registry.TuChoi as exc:
        return VerifiedBridgeOutcome(VERIFIED_INPUT_BRIDGE_VERSION, False, "REFUSED", exc.code, exc.reason, None, None, tuple(kh.calls))
    except Exception as exc:
        code = str(getattr(exc, "code", None) or "SOURCE_GATE_ERROR")
        return VerifiedBridgeOutcome(VERIFIED_INPUT_BRIDGE_VERSION, False, "REFUSED", code, str(exc), None, None, tuple(kh.calls))

    # Map verified `tf2["facts"]` (and solid topology) into clean solid_spec, chart_premises, pending, and GoalSpec
    solid_fact = next((f for f in facts if f.get("kind") == "solid" and f.get("role", "premise") == "premise"), None)
    if solid_fact is None:
        return VerifiedBridgeOutcome(VERIFIED_INPUT_BRIDGE_VERSION, False, "REFUSED", "UNSUPPORTED_GOAL", "No base solid premise.", None, None, tuple(kh.calls))

    # Extract solid vertices using `planner.lap_ke_hoach` / `engine.dung_tu_loi_goi` on premise-only calls
    stype = str(solid_fact.get("solid_type") or "pyramid")
    raw_solid = str(solid_fact.get("solid") or "")
    solid_spec: dict[str, Any] = {
        "fact_id": str(solid_fact.get("id") or "s1"),
        "solid_name": raw_solid,
        "solid_type": "cube" if (stype in ("prism", "cube") and raw_solid == "ABCD.A'B'C'D'" and solid_fact.get("right")) else stype,
        "regular": bool(solid_fact.get("regular", False)),
        "quote": str((solid_fact.get("quotes") or [""])[0]),
    }
    if solid_fact.get("right") is not None:
        solid_spec["right"] = bool(solid_fact.get("right"))
    if "." in raw_solid:
        top_part, bot_part = raw_solid.split(".", 1)
        if stype == "pyramid":
            solid_spec["apex"] = top_part
            solid_spec["base_vertices"] = _split_vertex_str(bot_part)
        else:
            solid_spec["base_vertices"] = _split_vertex_str(top_part)
            solid_spec["top_vertices"] = _split_vertex_str(bot_part)

    chart_premises: list[dict[str, Any]] = []
    pending: list[PendingConstruction] = []
    goal_spec: GoalSpec | None = None
    seq = 0
    for f in facts:
        kind = f.get("kind")
        role = f.get("role", "premise")
        if kind == "solid":
            continue
        if role == "question" and kind == "question":
            if f.get("quantity") == "area" and f.get("plane_relation") == "parallel" and f.get("point") and f.get("points_b"):
                seq += 1
                ref_pts = list(f.get("points_b") or ())
                base_lbls = list(solid_spec.get("base_vertices") or ())
                target_pl_ref: Any = f"day_{''.join(base_lbls)}" if base_lbls and set(ref_pts) == set(base_lbls) else ref_pts[:3]
                if isinstance(target_pl_ref, list):
                    pl_id = f"pl_{''.join(target_pl_ref)}"
                    pending.append(PendingConstruction(f"pend_{seq}_pl", "op.plane_through_point_parallel_plane", "pl_sec", {"point": str(f["point"]), "plane": target_pl_ref}, description=str((f.get("quotes") or [""])[0])))
                else:
                    pending.append(PendingConstruction(f"pend_{seq}_pl", "op.plane_through_point_parallel_plane", "pl_sec", {"point": str(f["point"]), "plane": target_pl_ref}, description=str((f.get("quotes") or [""])[0])))
                goal_spec = GoalSpec("section_area", {"plane": "pl_sec"}, "a")
            else:
                goal_spec = _fact_to_goal(f, solid_spec, point_distance_semantics=point_distance_semantics)
            continue
        if kind == "unsupported" and role == "question":
            goal_spec = GoalSpec("unsupported_goal", {"reason": str(f.get("reason") or "Unsupported question")}, "a")
            continue
        if kind in ("polygon_shape", "right_angle", "equal_lengths", "length", "perpendicular", "altitude", "vertex_angle", "line_plane_angle", "dihedral_angle"):
            chart_premises.append(f)
        elif kind == "point_def":
            pk = f.get("point_kind")
            lbl = str(f.get("point") or "")
            seq += 1
            if pk == "midpoint":
                pts = list(f.get("points") or ())
                pending.append(PendingConstruction(f"pend_{seq}", "op.midpoint_segment", lbl, {"a": pts[0], "b": pts[1]}, description=str((f.get("quotes") or [""])[0])))
            elif pk == "centroid":
                pts = list(f.get("points") or ())
                pending.append(PendingConstruction(f"pend_{seq}", "op.triangle_centroid", lbl, {"a": pts[0], "b": pts[1], "c": pts[2]}, description=str((f.get("quotes") or [""])[0])))
            elif pk == "divide_segment":
                pts = list(f.get("points") or ())
                pending.append(PendingConstruction(f"pend_{seq}", "op.divide_segment_ratio", lbl, {"a": pts[0], "b": pts[1]}, params={"ratio": str(f.get("value") or "1/2")}, description=str((f.get("quotes") or [""])[0])))
            elif pk == "intersect_line_line":
                pa, pb = list(f.get("points_a") or ()), list(f.get("points_b") or ())
                la_id, lb_id = f"ln_{pa[0]}_{pa[1]}", f"ln_{pb[0]}_{pb[1]}"
                pending.append(PendingConstruction(f"pend_{seq}_la", "op.line_through_points", la_id, {"a": pa[0], "b": pa[1]}))
                pending.append(PendingConstruction(f"pend_{seq}_lb", "op.line_through_points", lb_id, {"a": pb[0], "b": pb[1]}))
                pending.append(PendingConstruction(f"pend_{seq}", "op.intersect_coplanar_lines", lbl, {"line1": la_id, "line2": lb_id}, description=str((f.get("quotes") or [""])[0])))
            elif pk == "intersect_line_plane":
                pa, pb = list(f.get("points_a") or ()), list(f.get("points_b") or ())
                la_id = f"ln_{pa[0]}_{pa[1]}"
                pl_id = f"pl_{''.join(pb[:3])}"
                pending.append(PendingConstruction(f"pend_{seq}_la", "op.line_through_points", la_id, {"a": pa[0], "b": pa[1]}))
                pending.append(PendingConstruction(f"pend_{seq}_pl", "op.plane_through_three_points", pl_id, {"a": pb[0], "b": pb[1], "c": pb[2]}))
                pending.append(PendingConstruction(f"pend_{seq}", "op.intersect_line_plane", lbl, {"line": la_id, "plane": pl_id}, description=str((f.get("quotes") or [""])[0])))
        elif kind == "segment_ratio":
            seq += 1
            pa, pb = list(f.get("points_a") or ()), list(f.get("points_b") or ())
            # pa = [S, K], pb = [S, A] -> K divides segment [S, A] at value
            pending.append(PendingConstruction(f"pend_{seq}", "op.divide_segment_ratio", pa[1], {"a": pb[0], "b": pb[1]}, params={"ratio": str(f.get("value") or "1/2")}, description=str((f.get("quotes") or [""])[0])))
        elif kind == "point_reflection":
            seq += 1
            lbl = str(f.get("at") or "")
            pt = str(f.get("point") or "")
            ctr = str((f.get("points") or [""])[0])
            pending.append(PendingConstruction(f"pend_{seq}", "op.point_reflection", lbl, {"point": pt, "center": ctr}, description=str((f.get("quotes") or [""])[0])))

    if goal_spec is None:
        return VerifiedBridgeOutcome(VERIFIED_INPUT_BRIDGE_VERSION, False, "REFUSED", "MISSING_GOAL", "No supported question fact found.", None, None, tuple(kh.calls))

    # Since full `problem_text` ALREADY passed `registry.kiem_nguon` above, pass premise-only text
    # into `build_initial_frame` so `engine.dung_tu_loi_goi` extracts ONLY the base frame & Gram metric
    # with zero goal leakage and without triggering `REQUEST_NOT_ANSWERED`.
    premise_quotes = [solid_spec["quote"], *(str((cp.get("quotes") or [""])[0]) for cp in chart_premises)]
    premise_only_text = ". ".join(dict.fromkeys(q for q in premise_quotes if q)).rstrip(". ") + "."

    frame = build_initial_frame(
        case_id=case_id,
        problem_text=premise_only_text,
        solid_spec=solid_spec,
        chart_premises=chart_premises,
        pending_constructions=pending,
        length_unit="a",
    )
    return VerifiedBridgeOutcome(VERIFIED_INPUT_BRIDGE_VERSION, True, "VERIFIED", None, None, frame, goal_spec, tuple(kh.calls))


def _split_vertex_str(s: str) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(s):
        tok = s[i]
        i += 1
        while i < len(s) and (s[i].isdigit() or s[i] == "'"):
            tok += s[i]
            i += 1
        out.append(tok)
    return out


def _fact_to_goal(f: dict[str, Any], solid_spec: dict[str, Any], *, point_distance_semantics: bool = False) -> GoalSpec:
    qty = f.get("quantity")
    if qty == "length":
        pts = list(f.get("points") or ())
        if point_distance_semantics:
            return GoalSpec("point_distance", {"a": pts[0], "b": pts[1]}, "a")
        return GoalSpec("segment_length", {"a": pts[0], "b": pts[1]}, "a")
    if qty == "distance":
        pa = list(f.get("points_a") or ())
        pb = list(f.get("points_b") or ())
        if len(pa) == 1 and len(pb) >= 3:
            return GoalSpec("distance_point_plane", {"point": pa[0], "plane": pb[:3]}, "a")
        if len(pa) == 1 and len(pb) == 2:
            return GoalSpec("distance_point_line", {"point": pa[0], "line": pb[:2]}, "a")
        if len(pa) == 2 and len(pb) >= 3:
            return GoalSpec("distance_line_plane", {"line": pa[:2], "plane": pb[:3]}, "a")
        if len(pa) == 2 and len(pb) == 2:
            return GoalSpec("distance_skew_lines", {"line1": pa[:2], "line2": pb[:2]}, "a")
    if qty == "angle":
        pa = list(f.get("points_a") or ())
        pb = list(f.get("points_b") or ())
        if len(pa) == 2 and len(pb) >= 3:
            return GoalSpec("angle_line_plane", {"line": pa[:2], "plane": pb[:3]}, "a")
        if len(pa) == 2 and len(pb) == 2:
            return GoalSpec("angle_lines", {"line1": pa[:2], "line2": pb[:2]}, "a")
        if len(pa) >= 3 and len(pb) >= 3:
            return GoalSpec("angle_plane_plane", {"plane1": pa[:3], "plane2": pb[:3]}, "a")
    if qty == "area":
        if f.get("points"):
            pts = list(f["points"])
            if f.get("solid") or any(w in " ".join(f.get("quotes") or ()).lower() for w in ("thiết diện", "cắt")):
                return GoalSpec("section_area", {"plane": pts[:3]}, "a")
            return GoalSpec("polygon_area", {"points": pts}, "a")
        if f.get("plane_relation") == "parallel" and f.get("point") and f.get("points_b"):
            base_pl = f"day_{''.join(solid_spec.get('base_vertices') or f['points_b'])}"
            return GoalSpec("section_area", {"plane": base_pl}, "a")  # resolved if section_parallel pending built
    if qty == "volume":
        apex = solid_spec.get("apex")
        base = solid_spec.get("base_vertices") or ()
        if apex and len(base) >= 3:
            return GoalSpec("solid_volume", {"apex": apex, "base": list(base)}, "a")
    return GoalSpec("unsupported_goal", {"reason": f"Unsupported question fact {qty!r}"}, "a")
