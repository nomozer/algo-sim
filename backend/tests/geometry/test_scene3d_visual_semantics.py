# -*- coding: utf-8 -*-
"""Regression contract for cross-family Scene3D visual semantics."""
from __future__ import annotations

import re

from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.scene3d import build_scene3d
from app.simulation.semantic_program.simulation_state import build_simulation_state


def _pyramid_scene() -> dict:
    spec = SemanticProgramSpec.model_validate({
        "spec_version": "1.0",
        "title": "Thể tích khối chóp S.ABC",
        "memory_declarations": [
            {"name": "A", "type": "point3", "initial_value": [0, 0, 0],
             "provenance": "LAYOUT_DERIVED"},
            {"name": "B", "type": "point3", "initial_value": [3, 0, 0],
             "provenance": "LAYOUT_DERIVED"},
            {"name": "C", "type": "point3", "initial_value": [0, 4, 0],
             "provenance": "LAYOUT_DERIVED"},
            {"name": "S", "type": "point3", "initial_value": [0, 0, 5],
             "provenance": "LAYOUT_DERIVED"},
            {"name": "AB_length", "type": "float", "initial_value": "3",
             "provenance": "GIVEN", "source_fact_id": "f_ab"},
            {"name": "AC_length", "type": "float", "initial_value": "4",
             "provenance": "GIVEN", "source_fact_id": "f_ac"},
            {"name": "SA_length", "type": "float", "initial_value": "5",
             "provenance": "GIVEN", "source_fact_id": "f_sa"},
            {"name": "day_ABC", "type": "polygon3"},
            {"name": "khoi_chop", "type": "solid"},
            {"name": "dien_tich_day_ABC", "type": "float"},
            {"name": "the_tich_khoi_chop", "type": "float"},
        ],
        "statements": [
            {"kind": "construct_polygon", "target_var": "day_ABC",
             "vertices": ["A", "B", "C"], "label": "Tam giác đáy ABC"},
            {"kind": "construct_solid", "target_var": "khoi_chop",
             "vertices": ["S", "A", "B", "C"],
             "faces": [["A", "B", "C"], ["S", "A", "B"],
                       ["S", "B", "C"], ["S", "C", "A"]],
             "label": "Khối chóp S.ABC"},
            {"kind": "assign", "target_var": "dien_tich_day_ABC",
             "expr": {"kind": "measure", "quantity": "area", "of": "day_ABC"}},
            {"kind": "assign", "target_var": "the_tich_khoi_chop",
             "expr": {"kind": "measure", "quantity": "volume", "of": "khoi_chop"}},
        ],
        "visual_bindings": {},
    })
    result = SemanticProgramInterpreter().execute(spec)
    return build_scene3d(build_simulation_state(spec, result))


def test_volume_has_typed_numerical_area_and_height_dependencies():
    scene = _pyramid_scene()
    volume = next(o for o in scene["objects"] if o["id"] == "the_tich_khoi_chop")
    numerical = {
        e["source_id"] for e in volume["dependency_edges"]
        if e["relation"] == "numerical"
    }
    assert numerical == {"dien_tich_day_ABC", "SA_length"}
    assert {e["relation"] for e in volume["dependency_edges"]} >= {
        "numerical", "structural",
    }


def test_volume_formula_references_only_existing_learner_entities():
    scene = _pyramid_scene()
    by_id = {o["id"]: o for o in scene["objects"]}
    volume = by_id["the_tich_khoi_chop"]
    formula = volume["formula"]
    assert "AA′" not in formula["text"]
    assert "SA" in formula["text"]
    assert {r["entity_id"] for r in formula["references"]} == {
        "dien_tich_day_ABC", "SA_length",
    }
    assert all(r["entity_id"] in by_id for r in formula["references"])


def test_formation_is_explicit_and_does_not_show_all_points_at_start():
    scene = _pyramid_scene()
    formation = scene["formation"]
    snapshots = [tuple(s["visible_ids"]) for s in formation["steps"]]
    assert snapshots
    assert len(set(snapshots)) >= 4
    assert set(snapshots[0]) != {o["id"] for o in scene["objects"]}
    assert set(snapshots[-1]) == {o["id"] for o in scene["objects"]}
    assert all(s["learner_text"] for s in formation["steps"])


def test_event_learner_text_never_exposes_machine_identifiers():
    scene = _pyramid_scene()
    visible = " ".join(e["learner_text"] for e in scene["events"])
    internal_ids = {o["id"] for o in scene["objects"]}
    for token in internal_ids:
        if "_" not in token:
            continue
        assert not re.search(rf"(?<![\w]){re.escape(token)}(?![\w])", visible)


def test_scene3d_exposes_additive_learner_display_contract():
    scene = _pyramid_scene()
    assert scene["formation"]["steps"]
    for event in scene["events"]:
        assert event["learner_text"]
        assert "display_label" in event
    for obj in scene["objects"]:
        assert obj["display_label"]
        assert obj["display_role"] in {
            "visual_owner", "measurement", "non_visual",
        }


def test_layout_nodes_never_enter_volume_numerical_closure():
    scene = _pyramid_scene()
    volume = next(o for o in scene["objects"] if o["id"] == "the_tich_khoi_chop")
    numerical = {
        edge["source_id"]
        for edge in volume["dependency_edges"]
        if edge["relation"] == "numerical"
    }
    assert numerical == {"dien_tich_day_ABC", "SA_length"}
    assert numerical.isdisjoint({"A", "B", "C", "S", "khoi_chop", "day_ABC"})
