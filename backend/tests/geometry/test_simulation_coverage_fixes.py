# -*- coding: utf-8 -*-
"""Session 1 P3 — RED->GREEN Regression Tests for Simulation & Timeline Fixes.

Covers:
1. `scene3d.py`: `construct_curved_solid` timeline event action is `CREATE` (not `STEP`),
   and `circle3` / `ellipse3` intersection steps are classified as `action="CREATE"`,
   `semantic_kind="GEOMETRY_CONSTRUCTION"`, with clean Vietnamese learner narration
   (`Dựng ...`) and no raw `Circle3(...)` / `Ellipse3(...)` Python repr leakage.
2. `simulation_state.py`: `typed_dependency_graph` classifies `curved_solid`,
   `circle3`, and `ellipse3` dependency edges as `"structural"` (not `"layout"`).
"""
from __future__ import annotations

from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.scene3d import build_scene3d
from app.simulation.semantic_program.simulation_state import build_simulation_state


def _compile_spec(raw: dict) -> tuple[dict, dict]:
    spec = SemanticProgramSpec.model_validate(raw)
    res = SemanticProgramInterpreter().execute(spec)
    state = build_simulation_state(spec, res)
    scene = build_scene3d(state)
    return state, scene


def test_curved_solid_and_circle3_section_events_and_structural_dependencies():
    state, scene = _compile_spec({
        "spec_version": "1.0",
        "title": "Mặt cầu cắt bởi mặt phẳng",
        "memory_declarations": [
            {"name": "I", "type": "point3", "initial_value": [0, 0, 0], "provenance": "MODEL_ASSUMPTION", "model_assumption": "Chọn tâm I tại gốc tọa độ"},
            {"name": "R", "type": "float", "initial_value": 5, "provenance": "GIVEN", "source_fact_id": "f_R"},
            {"name": "cau", "type": "curved_solid"},
            {"name": "mp", "type": "plane3"},
            {"name": "duong_tron_giao", "type": "circle3"},
            {"name": "r_giao", "type": "float"},
        ],
        "statements": [
            {"kind": "construct_curved_solid", "target_var": "cau", "curved_kind": "ball", "anchor": "I", "radius": "R", "label": "Mặt cầu (S) tâm I"},
            {"kind": "construct_plane_from_equation", "target_var": "mp", "a": 0, "b": 0, "c": 1, "d": -3, "label": "Mặt phẳng (α): z - 3 = 0"},
            {"kind": "assign", "target_var": "duong_tron_giao", "expr": {"kind": "intersect_plane_curved", "plane": "mp", "solid": "cau"}},
            {"kind": "assign", "target_var": "r_giao", "expr": {"kind": "measure", "quantity": "radius", "of": "duong_tron_giao"}},
        ],
        "visual_bindings": {},
    })

    events_by_obj = {e.get("object"): e for e in scene["events"] if e.get("object")}
    # 1. construct_curved_solid must emit action == "CREATE" (not "STEP")
    cau_evt = events_by_obj["cau"]
    assert cau_evt["action"] == "CREATE"
    assert cau_evt["semantic_kind"] == "GEOMETRY_CONSTRUCTION"
    assert cau_evt["learner_text"].startswith("Dựng ")

    # 2. circle3 intersection must emit action == "CREATE" and GEOMETRY_CONSTRUCTION, without raw Circle3(...) repr
    cir_evt = events_by_obj["duong_tron_giao"]
    assert cir_evt["action"] == "CREATE"
    assert cir_evt["semantic_kind"] == "GEOMETRY_CONSTRUCTION"
    assert "Circle3(" not in cir_evt["learner_text"]
    assert "Vec3(" not in cir_evt["learner_text"]
    assert cir_evt["learner_text"].startswith("Dựng ")

    # 3. typed_dependency_graph must classify curved_solid and circle3 dependencies as "structural"
    dep_edges = state["dependency_edges"]
    cir_edges = {edge["source_id"]: edge["relation"] for edge in dep_edges["duong_tron_giao"]}
    assert cir_edges["cau"] == "structural"

    r_edges = {edge["source_id"]: edge["relation"] for edge in dep_edges["r_giao"]}
    assert r_edges["duong_tron_giao"] == "structural"


def test_ellipse3_section_event_and_structural_dependency():
    state, scene = _compile_spec({
        "spec_version": "1.0",
        "title": "Hình trụ cắt bởi mặt phẳng xiên",
        "memory_declarations": [
            {"name": "O", "type": "point3", "initial_value": [0, 0, 0], "provenance": "MODEL_ASSUMPTION", "model_assumption": "Chọn tâm đáy O làm gốc tọa độ"},
            {"name": "O_top", "type": "point3", "initial_value": [0, 0, 5], "provenance": "MODEL_ASSUMPTION", "model_assumption": "Tâm đáy trên O'"},
            {"name": "A", "type": "point3", "initial_value": [3, 0, 0], "provenance": "MODEL_ASSUMPTION", "model_assumption": "Điểm A trên đường tròn đáy"},
            {"name": "tru", "type": "curved_solid"},
            {"name": "mp_xien", "type": "plane3"},
            {"name": "elip_giao", "type": "ellipse3"},
            {"name": "S_elip", "type": "float"},
        ],
        "statements": [
            {"kind": "construct_curved_solid", "target_var": "tru", "curved_kind": "cylinder", "anchor": "O", "apex_or_top": "O_top", "rim_point": "A", "label": "Hình trụ tâm OO'"},
            {"kind": "construct_plane_from_equation", "target_var": "mp_xien", "a": 3, "b": 0, "c": 4, "d": -10, "label": "Mặt phẳng xiên (β)"},
            {"kind": "assign", "target_var": "elip_giao", "expr": {"kind": "intersect_plane_curved_ellipse", "plane": "mp_xien", "solid": "tru"}},
            {"kind": "assign", "target_var": "S_elip", "expr": {"kind": "measure", "quantity": "area", "of": "elip_giao"}},
        ],
        "visual_bindings": {},
    })

    events_by_obj = {e.get("object"): e for e in scene["events"] if e.get("object")}
    elip_evt = events_by_obj["elip_giao"]
    assert elip_evt["action"] == "CREATE"
    assert elip_evt["semantic_kind"] == "GEOMETRY_CONSTRUCTION"
    assert "Ellipse3(" not in elip_evt["learner_text"]
    assert elip_evt["learner_text"].startswith("Dựng ")

    dep_edges = state["dependency_edges"]
    s_edges = {edge["source_id"]: edge["relation"] for edge in dep_edges["S_elip"]}
    assert s_edges["elip_giao"] == "structural"
