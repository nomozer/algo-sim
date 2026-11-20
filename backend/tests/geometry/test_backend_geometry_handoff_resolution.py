# -*- coding: utf-8 -*-
"""Regression suite for AXO Backend Geometry Handoff (GEO-BE-V9415-001..004 + Section 6).

Tests verify:
1. GEO-BE-V9415-001: Coplanar Euclidean section lineage vs explicit algebraic
   line-plane fallback disclosure, plus detection of unused auxiliary points.
2. GEO-BE-V9415-002: Certified mathematical meaning & non-generic explanations
   across all 7 BANG_PHEP_DO quantities (= 0 and != 0), vector_from_points,
   scalar arithmetic assignments, and non-overclaiming on arbitrary zero scalars.
3. GEO-BE-V9415-003: Separation of computational_depends vs visible_prerequisites
   (transitively unwrapping render="non_visual" carriers like vector3), both in
   standalone build_scene3d and after enrich_construction_continuity.
4. GEO-BE-V9415-004: Read-only verification reproducing the static Frontend
   coincident_elements_pyramid fixture gap (SB_line CREATE & readout_ids).
5. Section 6 Cross-Check: Canonical pentagon section boundary edge emission
   ensuring all 5 edges (ME, EN, NP, PF, FM — including EN) are present.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.simulation.geometry_functions.construction_continuity import (
    enrich_construction_continuity,
)
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.pipeline_adapter import (
    compile_semantic_program_to_envelope,
)
from app.simulation.semantic_program.scene3d import build_scene3d
from app.simulation.semantic_program.simulation_state import build_simulation_state


REPO_ROOT = Path(__file__).resolve().parents[3]


def _pt(name: str, xyz: list[int | str], label: str | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "type": "point3",
        "initial_value": xyz,
        "label": label or name,
        "provenance": "GIVEN",
    }


def _assert_no_python_floats(obj: Any, path: str = "root") -> None:
    assert not isinstance(obj, float), f"Unexpected Python float at {path}: {obj!r}"
    if isinstance(obj, dict):
        for k, v in obj.items():
            _assert_no_python_floats(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            _assert_no_python_floats(item, f"{path}[{idx}]")


def _run_pipeline(
    spec_dict: dict[str, Any],
    *,
    compiler_geometry: bool = False,
) -> tuple[SemanticProgramSpec, Any, dict[str, Any], dict[str, Any]]:
    spec = SemanticProgramSpec.model_validate(spec_dict)
    if compiler_geometry:
        _ = compile_semantic_program_to_envelope(spec)
    interp = SemanticProgramInterpreter()
    interp._compiler_geometry = compiler_geometry
    exec_result = interp.execute(spec)
    state = build_simulation_state(
        spec,
        exec_result,
        prefer_declared_plane_names=True,
        common_perpendicular_witness=True,
    )
    scene3d = build_scene3d(state)
    # Check standalone scene3d invariance before enrich_construction_continuity mutates steps
    for ev, st in zip(scene3d["events"], scene3d["formation"]["steps"]):
        if "visible_prerequisites" in ev:
            assert st["visible_prerequisites"] == ev["visible_prerequisites"]
    enrich_construction_continuity(scene3d, trace=state.get("timeline"))
    return spec, exec_result, state, scene3d


# ── GEO-BE-V9415-002 ──────────────────────────────────────────────────────────


def test_all_measure_quantities_and_non_overclaiming_zeros() -> None:
    """Every BANG_PHEP_DO quantity (= 0 & != 0) must emit structured measured_quantity,
    non-generic explanations, exact certified meanings, and zero false perpendicularity."""
    spec_dict: dict[str, Any] = {
        "spec_version": "1.0",
        "title": "Measure semantics comprehensive regression",
        "description": "Test all measure quantities, zeros, non-zeros, vectors, and scalars.",
        "pedagogical_intent": "computational_verify",
        "memory_declarations": [
            _pt("A", [0, 0, 0]),
            _pt("B", [4, 0, 0]),
            _pt("C", [4, 4, 0]),
            _pt("D", [0, 4, 0]),
            _pt("S", [0, 0, 4]),
            *({"name": vn, "type": "vector3"} for vn in ("vec_AS", "vec_AB", "vec_DC", "vec_BA")),
            *(
                {"name": qn, "type": "float"}
                for qn in (
                    "goc_SA_AB",
                    "goc_SA_ABCD",
                    "goc_SAB_ABCD",
                    "goc_AB_CD",
                    "goc_SD_AC",
                    "cos_AS_AB",
                    "cos_AB_DC",
                    "cos_AB_BA",
                    "d_A_ABCD",
                    "d_SA_AB",
                    "d_S_ABCD",
                    "S_ABCD",
                    "V",
                    "V_residual",
                    "goc_gia_0",
                    "goc_arith_0",
                )
            ),
        ],
        "statements": [
            {
                "kind": "construct_solid",
                "target_var": "SABCD",
                "vertices": ["S", "A", "B", "C", "D"],
                "faces": [
                    ["A", "B", "C", "D"],
                    ["S", "A", "B"],
                    ["S", "B", "C"],
                    ["S", "C", "D"],
                    ["S", "D", "A"],
                ],
                "label": "S.ABCD",
            },
            {"kind": "construct_polygon", "target_var": "ABCD_poly", "vertices": ["A", "B", "C", "D"], "label": "ABCD"},
            {"kind": "construct_line", "target_var": "SA", "through_a": "S", "through_b": "A", "label": "SA"},
            {"kind": "construct_line", "target_var": "AB", "through_a": "A", "through_b": "B", "label": "AB"},
            {"kind": "construct_line", "target_var": "CD", "through_a": "C", "through_b": "D", "label": "CD"},
            {"kind": "construct_line", "target_var": "SD", "through_a": "S", "through_b": "D", "label": "SD"},
            {"kind": "construct_line", "target_var": "AC", "through_a": "A", "through_b": "C", "label": "AC"},
            {"kind": "construct_plane", "target_var": "mp_ABCD", "through": ["A", "B", "C"], "label": "(ABCD)"},
            {"kind": "construct_plane", "target_var": "mp_SAB", "through": ["S", "A", "B"], "label": "(SAB)"},
            # Orthogonal & parallel & oblique angle_cos_sq
            {"kind": "assign", "target_var": "goc_SA_AB", "expr": {"kind": "measure", "quantity": "angle_cos_sq", "of": "SA", "wrt": "AB"}, "label": "cos²(SA, AB)"},
            {"kind": "assign", "target_var": "goc_SA_ABCD", "expr": {"kind": "measure", "quantity": "angle_cos_sq", "of": "SA", "wrt": "mp_ABCD"}, "label": "cos²(SA, (ABCD))"},
            {"kind": "assign", "target_var": "goc_SAB_ABCD", "expr": {"kind": "measure", "quantity": "angle_cos_sq", "of": "mp_SAB", "wrt": "mp_ABCD"}, "label": "cos²((SAB), (ABCD))"},
            {"kind": "assign", "target_var": "goc_AB_CD", "expr": {"kind": "measure", "quantity": "angle_cos_sq", "of": "AB", "wrt": "CD"}, "label": "cos²(AB, CD)"},
            {"kind": "assign", "target_var": "goc_SD_AC", "expr": {"kind": "measure", "quantity": "angle_cos_sq", "of": "SD", "wrt": "AC"}, "label": "cos²(SD, AC)"},
            # Directed vectors + angle_cos (= 0, 1, -1, oblique)
            {"kind": "assign", "target_var": "vec_AS", "expr": {"kind": "vector_from_points", "from_point": "A", "to_point": "S"}, "label": "vectơ AS"},
            {"kind": "assign", "target_var": "vec_AB", "expr": {"kind": "vector_from_points", "from_point": "A", "to_point": "B"}, "label": "vectơ AB"},
            {"kind": "assign", "target_var": "vec_DC", "expr": {"kind": "vector_from_points", "from_point": "D", "to_point": "C"}, "label": "vectơ DC"},
            {"kind": "assign", "target_var": "vec_BA", "expr": {"kind": "vector_from_points", "from_point": "B", "to_point": "A"}, "label": "vectơ BA"},
            {"kind": "assign", "target_var": "cos_AS_AB", "expr": {"kind": "measure", "quantity": "angle_cos", "of": "vec_AS", "wrt": "vec_AB"}, "label": "cos(AS, AB)"},
            {"kind": "assign", "target_var": "cos_AB_DC", "expr": {"kind": "measure", "quantity": "angle_cos", "of": "vec_AB", "wrt": "vec_DC"}, "label": "cos(AB, DC)"},
            {"kind": "assign", "target_var": "cos_AB_BA", "expr": {"kind": "measure", "quantity": "angle_cos", "of": "vec_AB", "wrt": "vec_BA"}, "label": "cos(AB, BA)"},
            # Distances (= 0 point on plane, = 0 intersecting lines, > 0 point to plane)
            {"kind": "assign", "target_var": "d_A_ABCD", "expr": {"kind": "measure", "quantity": "distance", "of": "A", "wrt": "mp_ABCD"}, "label": "d(A, (ABCD))"},
            {"kind": "assign", "target_var": "d_SA_AB", "expr": {"kind": "measure", "quantity": "distance", "of": "SA", "wrt": "AB"}, "label": "d(SA, AB)"},
            {"kind": "assign", "target_var": "d_S_ABCD", "expr": {"kind": "measure", "quantity": "distance", "of": "S", "wrt": "mp_ABCD"}, "label": "d(S, (ABCD))"},
            # Area & volume & derived scalar arithmetic (never hallucinate perp!)
            {"kind": "assign", "target_var": "S_ABCD", "expr": {"kind": "measure", "quantity": "area", "of": "ABCD_poly"}, "label": "S(ABCD)"},
            {"kind": "assign", "target_var": "V", "expr": {"kind": "measure", "quantity": "volume", "of": "SABCD"}, "label": "Thể tích V"},
            {"kind": "assign", "target_var": "V_residual", "expr": {"kind": "arith", "op": "-", "left": {"kind": "var", "name": "V"}, "right": {"kind": "var", "name": "d_S_ABCD"}}, "label": "hiệu thử"},
            {"kind": "assign", "target_var": "goc_gia_0", "expr": {"kind": "literal", "value": 0}, "label": "giá trị thử 0"},
            {"kind": "assign", "target_var": "goc_arith_0", "expr": {"kind": "arith", "op": "-", "left": {"kind": "var", "name": "d_S_ABCD"}, "right": {"kind": "var", "name": "d_S_ABCD"}}, "label": "giá trị hiệu 0"},
        ],
        "visual_bindings": {},
    }

    for compiler_flag in (False, True):
        _, exec_result, _, scene3d = _run_pipeline(spec_dict, compiler_geometry=compiler_flag)
        _assert_no_python_floats(scene3d)

        # No generic legacy narration anywhere
        for step in exec_result.trace:
            assert "Ghi nhận giá trị vừa tính được" not in step.tier1_narration, step.tier1_narration
        for ev in scene3d["events"]:
            assert "Ghi nhận giá trị vừa tính được" not in (ev.get("explanation") or ""), ev
            assert "Ghi nhận giá trị vừa tính được" not in (ev.get("learner_text") or ""), ev

        objs = {o["id"]: o for o in scene3d["objects"]}

        # Certified meanings on angle_cos_sq = 0
        assert objs["goc_SA_AB"]["measured_quantity"]["certified_relation"] == "perpendicular_lines"
        assert objs["goc_SA_ABCD"]["measured_quantity"]["certified_relation"] == "perpendicular_line_plane"
        assert objs["goc_SAB_ABCD"]["measured_quantity"]["certified_relation"] == "perpendicular_planes"
        assert objs["goc_AB_CD"]["measured_quantity"]["certified_relation"] == "parallel_lines"
        assert objs["goc_SD_AC"]["measured_quantity"].get("certified_relation") is None

        # Certified meanings on angle_cos
        assert objs["cos_AS_AB"]["measured_quantity"]["certified_relation"] == "orthogonal_vectors"
        assert objs["cos_AB_DC"]["measured_quantity"]["certified_relation"] == "same_direction_vectors"
        assert objs["cos_AB_BA"]["measured_quantity"]["certified_relation"] == "opposite_direction_vectors"

        # distance == 0 MUST NOT claim perpendicularity
        assert objs["d_A_ABCD"]["measured_quantity"]["certified_relation"] == "point_on_plane"
        assert objs["d_SA_AB"]["measured_quantity"]["certified_relation"] == "coplanar_intersecting_or_coincident_lines"

        # Arbitrary scalars named goc_* == 0 MUST NOT claim perpendicularity or have measured_quantity
        assert "goc_gia_0" not in objs or objs["goc_gia_0"].get("measured_quantity") is None
        assert objs["goc_arith_0"].get("measured_quantity") is None

        ev_by_obj = {e["object"]: e for e in scene3d["events"] if e.get("action") == "MEASURE"}
        assert "vuông góc" in ev_by_obj["goc_SA_AB"]["explanation"].lower()
        assert "vuông góc" in ev_by_obj["goc_SA_ABCD"]["explanation"].lower()
        assert "vuông góc" in ev_by_obj["goc_SAB_ABCD"]["explanation"].lower()
        assert "vuông góc" not in ev_by_obj["d_SA_AB"]["explanation"].lower()
        assert "vuông góc" not in ev_by_obj["goc_gia_0"]["explanation"].lower()
        assert "vuông góc" not in ev_by_obj["goc_arith_0"]["explanation"].lower()
        assert ev_by_obj["goc_SA_AB"]["measured_quantity"]["quantity_kind"] == "angle_cos_sq"

        # Vector narration must not leak Vec3(...) repr
        vec_ev = next(e for e in scene3d["events"] if e.get("object") == "vec_AS")
        assert "Vec3" not in (vec_ev.get("explanation") or "")
        assert "Vec3" not in (vec_ev.get("learner_text") or "")


def test_curved_solid_radius_and_lateral_area() -> None:
    """radius and lateral_area measures must carry structured metadata and clear narrations."""
    spec_dict: dict[str, Any] = {
        "spec_version": "1.0",
        "title": "Curved solid radius and lateral_area",
        "description": "Cone section radius and lateral area measurement.",
        "pedagogical_intent": "computational_verify",
        "memory_declarations": [
            _pt("O", [0, 0, 0]),
            _pt("S", [0, 0, 4]),
            _pt("M", [3, 0, 0]),
            _pt("P1", [0, 0, 2]),
            _pt("P2", [1, 0, 2]),
            _pt("P3", [0, 1, 2]),
            {"name": "C_sec", "type": "circle3"},
            {"name": "r_sec", "type": "float"},
            {"name": "Sxq", "type": "float"},
        ],
        "statements": [
            {"kind": "construct_curved_solid", "target_var": "cone_N", "curved_kind": "cone", "anchor": "O", "apex_or_top": "S", "rim_point": "M", "label": "hình nón (N)"},
            {"kind": "construct_plane", "target_var": "mp_cut", "through": ["P1", "P2", "P3"], "label": "(P)"},
            {"kind": "assign", "target_var": "C_sec", "expr": {"kind": "intersect_plane_curved", "plane": "mp_cut", "solid": "cone_N"}, "label": "đường tròn cắt"},
            {"kind": "assign", "target_var": "r_sec", "expr": {"kind": "measure", "quantity": "radius", "of": "C_sec"}, "label": "bán kính thiết diện"},
            {"kind": "assign", "target_var": "Sxq", "expr": {"kind": "measure", "quantity": "lateral_area", "of": "cone_N"}, "label": "diện tích xung quanh"},
        ],
        "visual_bindings": {},
    }
    _, _, _, scene3d = _run_pipeline(spec_dict)
    _assert_no_python_floats(scene3d)
    for ev in scene3d["events"]:
        assert "Ghi nhận giá trị vừa tính được" not in (ev.get("explanation") or "")
    objs = {o["id"]: o for o in scene3d["objects"]}
    assert objs["r_sec"]["measured_quantity"]["quantity_kind"] == "radius"
    assert objs["r_sec"]["measured_quantity"]["subject_ids"] == ["C_sec"]
    assert objs["Sxq"]["measured_quantity"]["quantity_kind"] == "lateral_area"
    assert objs["Sxq"]["measured_quantity"]["subject_ids"] == ["cone_N"]


# ── GEO-BE-V9415-001 & Section 6 Cross-Check ──────────────────────────────────


def _assert_section_index_aligned(objs: dict[str, Any], sec: dict[str, Any]) -> None:
    """`ordered_vertex_ids[i]` IS `polygon[i]` (and `vertex_sources[i]`): consumers pair names with coordinates by
    index. /13 merge: the cycle was re-aligned for its name while `polygon` kept the kernel order, so the frontend read
    `SA ⊥ SC tại S` off the diagonal section (SAC) of a pyramid with SA ⊥ (ABCD) — the right angle is at A."""
    ids = sec["ordered_vertex_ids"]
    assert [objs[i]["xyz"] for i in ids] == sec["polygon"]
    assert len(sec["vertex_sources"]) == len(sec["polygon"])


_PYRAMID_DECLS = [_pt("A", [0, 0, 0]), _pt("B", [2, 0, 0]), _pt("C", [2, 2, 0]), _pt("D", [0, 2, 0]), _pt("S", [0, 0, 4])]
_PYRAMID = {"kind": "construct_solid", "target_var": "chop", "vertices": ["A", "B", "C", "D", "S"],
            "faces": [["A", "B", "C", "D"], ["S", "A", "B"], ["S", "B", "C"], ["S", "C", "D"], ["S", "D", "A"]],
            "label": "S.ABCD"}


@pytest.mark.parametrize("statements, symbols", [
    # Diagonal plane named by the section label itself: (SAC).
    ([{"kind": "construct_plane", "target_var": "sac", "through": ["S", "A", "C"], "label": "(SAC)"},
      {"kind": "construct_section", "target_var": "td", "solid": "chop", "plane": "sac",
       "label": "thiết diện theo mặt phẳng (SAC)"}],
     ["S", "A", "C"]),
    # Section label names no cycle: the cutting plane (MNP) decides how the cycle is read (MNPQ, not NMQP).
    ([{"kind": "construct_point", "target_var": "M", "label": "M", "expr": {"kind": "midpoint", "a": "S", "b": "A"}},
      {"kind": "construct_point", "target_var": "N", "label": "N", "expr": {"kind": "midpoint", "a": "S", "b": "B"}},
      {"kind": "construct_point", "target_var": "P", "label": "P", "expr": {"kind": "midpoint", "a": "S", "b": "C"}},
      {"kind": "construct_plane", "target_var": "mp", "label": "(MNP)", "through": ["M", "N", "P"]},
      {"kind": "construct_line", "target_var": "sd", "label": "SD", "through_a": "S", "through_b": "D"},
      {"kind": "construct_point", "target_var": "Q", "label": "Q",
       "expr": {"kind": "intersect_line_plane", "line": "sd", "plane": "mp"}},
      {"kind": "construct_section", "target_var": "td", "label": "thiết diện", "solid": "chop", "plane": "mp"}],
     ["M", "N", "P", "Q"]),
])
def test_section_cycle_is_named_and_index_aligned(statements, symbols) -> None:
    _, _, _, scene3d = _run_pipeline({
        "spec_version": "1.0", "title": "section cycle", "description": "section cycle",
        "pedagogical_intent": "construct_and_show", "memory_declarations": _PYRAMID_DECLS,
        "statements": [_PYRAMID, *statements], "visual_bindings": {},
    })
    objs = {o["id"]: o for o in scene3d["objects"]}
    sec = objs["td"]
    assert sec["ordered_vertex_symbols"] == symbols
    assert sec["notation"] == "".join(symbols)
    _assert_section_index_aligned(objs, sec)


def test_route_d_rows_written_before_the_section_cycle_fix_miss() -> None:
    """CACHE_VERSION 147 -> 148 (/13): served sections are now index-aligned and read from the cutting plane, so a
    `147:route-d` row may carry the misaligned cycle the frontend turns into `SA ⊥ SC tại S`; it must MISS."""
    from tests.cache_policy import assert_cache_policy_at_least, assert_route_d_row_misses

    assert_cache_policy_at_least(148)
    assert_route_d_row_misses("147:route-d")


def test_coplanar_section_lineage_unused_point_and_pentagon_edges() -> None:
    """Coplanar Euclidean section must label intersecting lines cleanly, avoid false
    unused auxiliaries when absent, flag dead points when present, and emit all 5
    pentagon edges (including EN) on section MENPF."""
    base_decls = [
        _pt("A", [0, 0, 0]),
        _pt("B", [4, 0, 0]),
        _pt("C", [4, 4, 0]),
        _pt("D", [0, 4, 0]),
        _pt("S", [0, 0, 4]),
    ]
    coplanar_stmts = [
        {
            "kind": "construct_solid",
            "target_var": "SABCD",
            "vertices": ["S", "A", "B", "C", "D"],
            "faces": [
                ["A", "B", "C", "D"],
                ["S", "A", "B"],
                ["S", "B", "C"],
                ["S", "C", "D"],
                ["S", "D", "A"],
            ],
            "label": "S.ABCD",
        },
        {"kind": "construct_point", "target_var": "M", "expr": {"kind": "midpoint", "a": "S", "b": "A"}, "label": "M"},
        {"kind": "construct_point", "target_var": "N", "expr": {"kind": "midpoint", "a": "B", "b": "C"}, "label": "N"},
        {"kind": "construct_point", "target_var": "P", "expr": {"kind": "midpoint", "a": "C", "b": "D"}, "label": "P"},
        {"kind": "construct_line", "target_var": "NP", "through_a": "N", "through_b": "P", "label": "NP"},
        {"kind": "construct_line", "target_var": "AB", "through_a": "A", "through_b": "B", "label": "AB"},
        {"kind": "construct_line", "target_var": "AD", "through_a": "A", "through_b": "D", "label": "AD"},
        {"kind": "construct_line", "target_var": "SB", "through_a": "S", "through_b": "B", "label": "SB"},
        {"kind": "construct_line", "target_var": "SD", "through_a": "S", "through_b": "D", "label": "SD"},
        # Coplanar intersections in (ABCD), (SAB), (SAD)
        {"kind": "construct_point", "target_var": "I1", "expr": {"kind": "intersect_line_line", "line_a": "NP", "line_b": "AB"}, "label": "I1"},
        {"kind": "construct_point", "target_var": "I2", "expr": {"kind": "intersect_line_line", "line_a": "NP", "line_b": "AD"}, "label": "I2"},
        {"kind": "construct_line", "target_var": "MI1", "through_a": "M", "through_b": "I1", "label": "MI1"},
        {"kind": "construct_line", "target_var": "MI2", "through_a": "M", "through_b": "I2", "label": "MI2"},
        {"kind": "construct_point", "target_var": "E", "expr": {"kind": "intersect_line_line", "line_a": "MI1", "line_b": "SB"}, "label": "E"},
        {"kind": "construct_point", "target_var": "F", "expr": {"kind": "intersect_line_line", "line_a": "MI2", "line_b": "SD"}, "label": "F"},
        {"kind": "construct_plane", "target_var": "MNP", "through": ["M", "N", "P"], "label": "(MNP)"},
        {"kind": "construct_section", "target_var": "MENPF", "solid": "SABCD", "plane": "MNP", "label": "thiết diện MENPF"},
    ]
    _, _, _, scene3d = _run_pipeline({
        "spec_version": "1.0",
        "title": "Coplanar Euclidean section MENPF",
        "description": "Pure Euclidean coplanar construction of section MENPF.",
        "pedagogical_intent": "construct_and_show",
        "memory_declarations": base_decls,
        "statements": coplanar_stmts,
        "visual_bindings": {},
    })
    _assert_no_python_floats(scene3d)

    objs = {o["id"]: o for o in scene3d["objects"]}
    # Coplanar lineage
    assert objs["E"]["construction_lineage"]["mode"] == "euclidean_coplanar_intersection"
    assert objs["F"]["construction_lineage"]["mode"] == "euclidean_coplanar_intersection"
    # Continuity validation reason for intersect_line_line must NOT be fallback generic
    step_E = next(s for s in scene3d["formation"]["steps"] if "E" in s.get("created_ids", []))
    assert "đồng phẳng" in (step_E["step_summary"].get("validity") or "").lower()

    # No unused auxiliaries in clean coplanar spec
    assert scene3d["unused_auxiliary_ids"] == []

    # Section 6 Cross-Check: MENPF exposes ALL 5 edges including EN!
    sec = objs["MENPF"]
    assert sec["ordered_vertex_symbols"] == ["M", "E", "N", "P", "F"]
    assert sec["ordered_boundary_edges"] == ["ME", "EN", "NP", "PF", "FM"]
    _assert_section_index_aligned(objs, sec)
    sec_close_ev = next(
        e for e in scene3d["events"]
        if e.get("object") == "MENPF" and e.get("action") == "STEP"
    )
    for edge in ("ME", "EN", "NP", "PF", "FM"):
        assert edge in sec_close_ev["details"]["ordered_boundary_edges"]
        assert edge in sec_close_ev["explanation"]

    # Now add a dead point O = midpoint(A, C) and verify unused_auxiliary detection!
    _, _, _, scene_with_O = _run_pipeline({
        "spec_version": "1.0",
        "title": "Section with dead auxiliary O",
        "description": "Detect unused auxiliary point O.",
        "pedagogical_intent": "construct_and_show",
        "memory_declarations": base_decls,
        "statements": [
            *coplanar_stmts[:1],
            {"kind": "construct_point", "target_var": "O", "expr": {"kind": "midpoint", "a": "A", "b": "C"}, "label": "O"},
            *coplanar_stmts[1:],
        ],
        "visual_bindings": {},
    })
    assert "O" in scene_with_O["unused_auxiliary_ids"]
    o_obj = next(o for o in scene_with_O["objects"] if o["id"] == "O")
    assert o_obj["is_unused_auxiliary"] is True


def test_algebraic_line_plane_intersection_discloses_limitation() -> None:
    """When intersect_line_plane is used directly, Backend must disclose algebraic mode
    rather than pretending it is a pure Euclidean coplanar intersection."""
    _, _, _, scene3d = _run_pipeline({
        "spec_version": "1.0",
        "title": "Algebraic line plane intersection disclosure",
        "description": "Explicit disclosure of algebraic intersection mode.",
        "pedagogical_intent": "construct_and_show",
        "memory_declarations": [
            _pt("A", [0, 0, 0]),
            _pt("B", [4, 0, 0]),
            _pt("C", [4, 4, 0]),
            _pt("D", [0, 4, 0]),
            _pt("S", [0, 0, 4]),
        ],
        "statements": [
            {"kind": "construct_point", "target_var": "M", "expr": {"kind": "midpoint", "a": "S", "b": "A"}, "label": "M"},
            {"kind": "construct_point", "target_var": "N", "expr": {"kind": "midpoint", "a": "B", "b": "C"}, "label": "N"},
            {"kind": "construct_point", "target_var": "P", "expr": {"kind": "midpoint", "a": "C", "b": "D"}, "label": "P"},
            {"kind": "construct_plane", "target_var": "MNP", "through": ["M", "N", "P"], "label": "(MNP)"},
            {"kind": "construct_line", "target_var": "SB", "through_a": "S", "through_b": "B", "label": "SB"},
            {"kind": "construct_point", "target_var": "E", "expr": {"kind": "intersect_line_plane", "line": "SB", "plane": "MNP"}, "label": "E"},
        ],
        "visual_bindings": {},
    })
    objs = {o["id"]: o for o in scene3d["objects"]}
    lineage = objs["E"]["construction_lineage"]
    assert lineage["mode"] == "algebraic_line_plane_intersection"
    assert lineage.get("pedagogical_limitation")


# ── GEO-BE-V9415-003 ──────────────────────────────────────────────────────────


def test_circumsphere_separates_computational_and_visible_prerequisites() -> None:
    """Circumsphere fixture from probe-contract-waves-2 must preserve vec_OB/vec_OC
    computational provenance while providing clean visible_prerequisites without
    non_visual vector3 carriers."""
    final_path = REPO_ROOT / "docs" / "evaluation" / "geometry" / "probe-contract-waves-2" / "cases" / "circumsphere" / "final.json"
    if not final_path.exists():
        pytest.skip(f"Missing probe fixture: {final_path}")

    raw_spec = json.loads(final_path.read_text(encoding="utf-8"))
    _, _, _, scene3d = _run_pipeline(raw_spec["chuong_trinh"])
    _assert_no_python_floats(scene3d)

    objs = {o["id"]: o for o in scene3d["objects"]}
    assert objs["vec_OB"]["type"] == "vector3"
    assert objs["vec_OB"]["render"] == "non_visual"

    # Computational provenance stays intact
    assert "vec_OB" in objs["A_prime"]["computational_depends"]
    assert "vec_OC" in objs["D"]["computational_depends"]

    # Visible prerequisites unwrap non_visual vector3 carriers to point3 sources
    assert objs["A_prime"]["visible_prerequisites"] == ["A", "B", "O"]
    assert objs["D"]["visible_prerequisites"] == ["A_prime", "C", "O"]
    assert all(
        objs[dep]["render"] != "non_visual"
        for dep in objs["A_prime"]["visible_prerequisites"]
    )
    assert objs["A_prime"]["construction_lineage"]["mode"] == "vector_translation"

    # dependency_edges flags non-visual carriers cleanly
    edge_map = {e["source_id"]: e for e in objs["A_prime"]["dependency_edges"]}
    assert edge_map["vec_OB"]["is_non_visual_carrier"] is True
    assert edge_map["vec_OB"]["resolved_visible_sources"] == ["B", "O"]

    # Formation steps propagate visible_prerequisites alongside dependencies
    step_A_prime = next(s for s in scene3d["formation"]["steps"] if "A_prime" in s.get("created_ids", []))
    assert step_A_prime["visible_prerequisites"] == ["A", "B", "O"]


# ── GEO-BE-V9415-004 ──────────────────────────────────────────────────────────


def test_static_frontend_fixture_reproduction_signature() -> None:
    """coincident_elements_pyramid used to exhibit the Frontend authoring gap (no CREATE event for SB_line before K,
    no readout_ids on formation.steps). main closed it in `b5810dcc3` ("integrate verified backend geometry
    contracts"); since the /13 merge of main this test pins the CLOSED state so the gap cannot silently reopen."""
    fixture_path = REPO_ROOT / "frontend" / "src" / "simulations" / "domains" / "geometry" / "scene3d-regression-archetypes-fixtures.json"
    if not fixture_path.exists():
        pytest.skip(f"Missing archetype fixture: {fixture_path}")

    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    case = data["coincident_elements_pyramid"]
    scene = case["scene3d"]
    created_before_K: list[str] = []
    for ev in scene["events"]:
        if ev.get("object") == "K":
            break
        if ev.get("action") == "CREATE" and ev.get("object"):
            created_before_K.append(ev["object"])
    k_ev = next(ev for ev in scene["events"] if ev.get("object") == "K")
    assert "SB_line" in k_ev.get("depends", [])
    assert "SB_line" in created_before_K
    assert any("readout_ids" in step for step in scene["formation"]["steps"])
