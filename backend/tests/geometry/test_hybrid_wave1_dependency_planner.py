# -*- coding: utf-8 -*-
"""Wave 1B TDD suite: Dependency-Aware Planner Ordering (`GAP-C1` / `ISSUE-RESEARCH-HYBRID-AUXILIARY-BEFORE-SOLID`).

Covers all 8 required properties:
1. Auxiliary/premise ordering before solid/base construction (and apex-foot exception).
2. Nested dependencies (`point -> line/plane -> projection/section -> measurement`).
3. Independent call stability (preserving existing order when no dependency is violated, including `H12`).
4. Dependency cycle rejection (`DEPENDENCY_CYCLE`) fail-closed.
5. Missing dependency rejection (`DANGLING_DEPENDENCY` / `UNKNOWN_SOLID`) fail-closed.
6. Multi-goal composition ordering (`ask_*` after auxiliary constructions emitted by later goals).
7. Reordered equivalent inputs producing valid served results and identical exact answers.
8. Scene3D timeline consistency when consuming planner outputs.
"""
from __future__ import annotations

from copy import deepcopy
import pytest

from app.ai.function_route import run_fact_route
from app.simulation.geometry_functions.planner import lap_ke_hoach
from app.simulation.geometry_functions.registry import TuChoi
from tests.test_hybrid_preview_contract import hold, corpus


def _call_index_map(plan) -> dict[str, int]:
    return {c["id"]: i for i, c in enumerate(plan.calls)}


def test_auxiliary_midpoint_placed_after_solid_and_base_foundation():
    """1a. When an auxiliary point construction (`f1: midpoint M of SC`) is given with a smaller ID than
    the base polygon and altitude premises (`f2..f5`), the planner places the solid/base foundation first."""
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 3. "
        "Gọi M là trung điểm của SC. Tính độ dài đoạn AM."
    )
    payload = {
        "facts": [
            {
                "id": "f1",
                "kind": "point_def",
                "role": "premise",
                "quotes": ["Gọi M là trung điểm của SC"],
                "point": "M",
                "point_kind": "midpoint",
                "points": ["S", "C"],
            },
            {
                "id": "f2",
                "kind": "length",
                "role": "premise",
                "quotes": ["SA = 3"],
                "measure": "segment",
                "points": ["S", "A"],
                "value": "3",
            },
            {
                "id": "f3",
                "kind": "perpendicular",
                "role": "premise",
                "quotes": ["SA vuông góc với (ABCD)"],
                "points_a": ["S", "A"],
                "points_b": ["A", "B", "C", "D"],
            },
            {
                "id": "f4",
                "kind": "polygon_shape",
                "role": "premise",
                "quotes": ["đáy ABCD là hình vuông cạnh 2"],
                "points": ["A", "B", "C", "D"],
                "shape": "square",
                "value": "2",
            },
            {
                "id": "f5",
                "kind": "solid",
                "role": "premise",
                "quotes": ["Cho hình chóp S.ABCD"],
                "solid": "S.ABCD",
                "solid_type": "pyramid",
            },
            {
                "id": "f6",
                "kind": "question",
                "role": "question",
                "quotes": ["Tính độ dài đoạn AM"],
                "quantity": "length",
                "points": ["A", "M"],
            },
        ]
    }
    plan = lap_ke_hoach(payload, text)
    idx = _call_index_map(plan)
    assert idx["f5"] < idx["f4"] < idx["f1"] < idx["f6"]
    assert idx["f3"] < idx["f1"]
    assert idx["f2"] < idx["f1"]


def test_apex_foot_midpoint_placed_after_base_and_before_apex_perpendicular():
    """1b. When midpoint `M` of `AB` is the foot of the altitude `SM ⊥ (ABC)`, `M` must be constructed
    after the solid/base declaration (`S.ABC`, `regular_polygon ABC`) and BEFORE `SM ⊥ (ABC)` and `SM = 3`."""
    text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2. "
        "Gọi M là trung điểm của AB, biết SM vuông góc với (ABC) và SM = 3. Tính thể tích khối chóp S.ABC."
    )
    payload = {
        "facts": [
            {
                "id": "f1",
                "kind": "perpendicular",
                "role": "premise",
                "quotes": ["SM vuông góc với (ABC)"],
                "points_a": ["S", "M"],
                "points_b": ["A", "B", "C"],
            },
            {
                "id": "f2",
                "kind": "length",
                "role": "premise",
                "quotes": ["SM = 3"],
                "measure": "segment",
                "points": ["S", "M"],
                "value": "3",
            },
            {
                "id": "f3",
                "kind": "point_def",
                "role": "premise",
                "quotes": ["Gọi M là trung điểm của AB"],
                "point": "M",
                "point_kind": "midpoint",
                "points": ["A", "B"],
            },
            {
                "id": "f4",
                "kind": "polygon_shape",
                "role": "premise",
                "quotes": ["đáy ABC là tam giác đều cạnh 2"],
                "points": ["A", "B", "C"],
                "shape": "equilateral_triangle",
                "value": "2",
            },
            {
                "id": "f5",
                "kind": "solid",
                "role": "premise",
                "quotes": ["Cho hình chóp S.ABC"],
                "solid": "S.ABC",
                "solid_type": "pyramid",
            },
            {
                "id": "f6",
                "kind": "question",
                "role": "question",
                "quotes": ["Tính thể tích khối chóp S.ABC"],
                "quantity": "volume",
                "solid": "S.ABC",
            },
        ]
    }
    plan = lap_ke_hoach(payload, text)
    idx = _call_index_map(plan)
    assert idx["f5"] < idx["f4"] < idx["f3"] < idx["f1"] < idx["f6"]
    assert idx["f3"] < idx["f2"] < idx["f6"]


def test_nested_point_line_projection_section_dependencies_ordered():
    """2. Intra-phase nested dependencies (`midpoint M -> orthogonal_projection K -> section -> ask`)
    and (`intersection_line d -> orthogonal_projection_line H`) are ordered by true data dependency,
    not by flat category phase."""
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 3. "
        "Gọi M là trung điểm của SC, K là hình chiếu vuông góc của M lên (ABCD). "
        "Tìm giao tuyến của (SAB) và (SCD). Gọi H là hình chiếu vuông góc của K lên giao tuyến của (SAB) và (SCD). "
        "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB). Tính độ dài đoạn KH."
    )
    payload = {
        "facts": [
            {
                "id": "f1",
                "kind": "section",
                "role": "question",
                "quotes": ["Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (MAB)."],
                "solid": "S.ABCD",
                "points": ["M", "A", "B"],
            },
            {
                "id": "f2",
                "kind": "projection",
                "role": "premise",
                "quotes": ["Gọi H là hình chiếu vuông góc của K lên giao tuyến của (SAB) và (SCD)."],
                "point": "K",
                "line_ref": "f4",
                "at": "H",
            },
            {
                "id": "f3",
                "kind": "projection",
                "role": "premise",
                "quotes": ["K là hình chiếu vuông góc của M lên (ABCD)"],
                "point": "M",
                "points": ["A", "B", "C", "D"],
                "at": "K",
            },
            {
                "id": "f4",
                "kind": "intersection_line",
                "role": "premise",
                "quotes": ["Tìm giao tuyến của (SAB) và (SCD)."],
                "points_a": ["S", "A", "B"],
                "points_b": ["S", "C", "D"],
            },
            {
                "id": "f5",
                "kind": "point_def",
                "role": "premise",
                "quotes": ["Gọi M là trung điểm của SC"],
                "point": "M",
                "point_kind": "midpoint",
                "points": ["S", "C"],
            },
            {
                "id": "f6",
                "kind": "length",
                "role": "premise",
                "quotes": ["SA = 3"],
                "measure": "segment",
                "points": ["S", "A"],
                "value": "3",
            },
            {
                "id": "f7",
                "kind": "perpendicular",
                "role": "premise",
                "quotes": ["SA vuông góc với (ABCD)"],
                "points_a": ["S", "A"],
                "points_b": ["A", "B", "C", "D"],
            },
            {
                "id": "f8",
                "kind": "polygon_shape",
                "role": "premise",
                "quotes": ["đáy ABCD là hình vuông cạnh 2"],
                "points": ["A", "B", "C", "D"],
                "shape": "square",
                "value": "2",
            },
            {
                "id": "f9",
                "kind": "solid",
                "role": "premise",
                "quotes": ["Cho hình chóp S.ABCD"],
                "solid": "S.ABCD",
                "solid_type": "pyramid",
            },
            {
                "id": "f10",
                "kind": "question",
                "role": "question",
                "quotes": ["Tính độ dài đoạn KH."],
                "quantity": "length",
                "points": ["K", "H"],
            },
        ]
    }
    plan = lap_ke_hoach(payload, text)
    idx = _call_index_map(plan)
    # Solid & base foundation precede all auxiliary constructions
    assert idx["f9"] < idx["f8"] < idx["f5"]
    assert idx["f7"] < idx["f5"]
    assert idx["f6"] < idx["f5"]
    # M (f5) must precede K (f3) and section (f1)
    assert idx["f5"] < idx["f3"]
    assert idx["f5"] < idx["f1"]
    # K (f3) and intersection_line (f4) must both precede H (f2)
    assert idx["f3"] < idx["f2"]
    assert idx["f4"] < idx["f2"]
    # All constructions precede ask_length (f10)
    assert idx["f2"] < idx["f10"]
    assert idx["f1"] < idx["f10"]


def test_independent_calls_preserve_existing_order_including_h12():
    """3. Inputs whose calls already satisfy all dependency edges keep their exact original call order."""
    h12 = hold("H12_PROJECTION_MIDPOINT_ANGLE")
    plan_h12 = lap_ke_hoach(h12["payload"], h12["text"])
    assert [c["id"] for c in plan_h12.calls] == ["f5", "f1", "f2", "f3", "f4", "f6", "f7"]

    # Independent midpoint constructions M and N keep their relative order
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 3. "
        "Gọi M là trung điểm của AB, N là trung điểm của CD. Tính độ dài đoạn MN."
    )
    base_facts = [
        {"id": "f1", "kind": "solid", "role": "premise", "quotes": ["Cho hình chóp S.ABCD"], "solid": "S.ABCD", "solid_type": "pyramid"},
        {"id": "f2", "kind": "polygon_shape", "role": "premise", "quotes": ["đáy ABCD là hình vuông cạnh 2"], "points": ["A", "B", "C", "D"], "shape": "square", "value": "2"},
        {"id": "f3", "kind": "perpendicular", "role": "premise", "quotes": ["SA vuông góc với (ABCD)"], "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"]},
        {"id": "f4", "kind": "length", "role": "premise", "quotes": ["SA = 3"], "measure": "segment", "points": ["S", "A"], "value": "3"},
    ]
    m_fact = {"id": "f5", "kind": "point_def", "role": "premise", "quotes": ["Gọi M là trung điểm của AB"], "point": "M", "point_kind": "midpoint", "points": ["A", "B"]}
    n_fact = {"id": "f6", "kind": "point_def", "role": "premise", "quotes": ["N là trung điểm của CD"], "point": "N", "point_kind": "midpoint", "points": ["C", "D"]}
    q_fact = {"id": "f7", "kind": "question", "role": "question", "quotes": ["Tính độ dài đoạn MN."], "quantity": "length", "points": ["M", "N"]}

    plan_mn = lap_ke_hoach({"facts": [*base_facts, m_fact, n_fact, q_fact]}, text)
    assert [c["id"] for c in plan_mn.calls] == ["f1", "f2", "f3", "f4", "f5", "f6", "f7"]

    # Swapping IDs of independent M and N preserves their new relative order (N then M)
    m_fact_swapped = {**m_fact, "id": "f6"}
    n_fact_swapped = {**n_fact, "id": "f5"}
    plan_nm = lap_ke_hoach({"facts": [*base_facts, n_fact_swapped, m_fact_swapped, q_fact]}, text)
    assert [c["id"] for c in plan_nm.calls] == ["f1", "f2", "f3", "f4", "f5", "f6", "f7"]


def test_dependency_cycle_rejected_fail_closed():
    """4. Cyclic point constructions are rejected with `DEPENDENCY_CYCLE` even when `_EffectResolver` is not used."""
    text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2, SA vuông góc với (ABC), SA = 3. "
        "Gọi M là hình chiếu vuông góc của N lên (ABC), N là hình chiếu vuông góc của M lên (SBC). "
        "Tính độ dài đoạn MN."
    )
    payload = {
        "facts": [
            {"id": "f1", "kind": "solid", "role": "premise", "quotes": ["Cho hình chóp S.ABC"], "solid": "S.ABC", "solid_type": "pyramid"},
            {"id": "f2", "kind": "polygon_shape", "role": "premise", "quotes": ["đáy ABC là tam giác đều cạnh 2"], "points": ["A", "B", "C"], "shape": "equilateral_triangle", "value": "2"},
            {"id": "f3", "kind": "perpendicular", "role": "premise", "quotes": ["SA vuông góc với (ABC)"], "points_a": ["S", "A"], "points_b": ["A", "B", "C"]},
            {"id": "f4", "kind": "length", "role": "premise", "quotes": ["SA = 3"], "measure": "segment", "points": ["S", "A"], "value": "3"},
            {"id": "f5", "kind": "projection", "role": "premise", "quotes": ["M là hình chiếu vuông góc của N lên (ABC)"], "point": "N", "points": ["A", "B", "C"], "at": "M"},
            {"id": "f6", "kind": "projection", "role": "premise", "quotes": ["N là hình chiếu vuông góc của M lên (SBC)"], "point": "M", "points": ["S", "B", "C"], "at": "N"},
            {"id": "f7", "kind": "question", "role": "question", "quotes": ["Tính độ dài đoạn MN."], "quantity": "length", "points": ["M", "N"]},
        ]
    }
    with pytest.raises(TuChoi) as exc_info:
        lap_ke_hoach(payload, text)
    assert exc_info.value.code == "DEPENDENCY_CYCLE"


def test_missing_dependency_rejected_fail_closed():
    """5. Dangling `line_ref` or unknown `solid` is rejected fail-closed with a structured refusal code."""
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 3. "
        "Tính khoảng cách từ A đến giao tuyến của (SAB) và (SCD)."
    )
    payload_dangling_question = {
        "facts": [
            {"id": "f1", "kind": "solid", "role": "premise", "quotes": ["Cho hình chóp S.ABCD"], "solid": "S.ABCD", "solid_type": "pyramid"},
            {"id": "f2", "kind": "polygon_shape", "role": "premise", "quotes": ["đáy ABCD là hình vuông cạnh 2"], "points": ["A", "B", "C", "D"], "shape": "square", "value": "2"},
            {"id": "f3", "kind": "perpendicular", "role": "premise", "quotes": ["SA vuông góc với (ABCD)"], "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"]},
            {"id": "f4", "kind": "length", "role": "premise", "quotes": ["SA = 3"], "measure": "segment", "points": ["S", "A"], "value": "3"},
            {
                "id": "q1",
                "kind": "question",
                "role": "question",
                "quotes": ["Tính khoảng cách từ A đến giao tuyến của (SAB) và (SCD)."],
                "quantity": "distance",
                "points_a": ["A"],
                "line_ref": "f_nonexistent_line",
            },
        ]
    }
    with pytest.raises(TuChoi) as exc_info:
        lap_ke_hoach(payload_dangling_question, text)
    assert exc_info.value.code == "UNKNOWN_DERIVED_REFERENCE"

    # Also verify DANGLING_DEPENDENCY on a call plan with a missing line_ref / depends_on target
    plan = lap_ke_hoach(
        {
            "facts": [
                payload_dangling_question["facts"][0],
                payload_dangling_question["facts"][1],
                payload_dangling_question["facts"][2],
                payload_dangling_question["facts"][3],
            ]
        },
        text,
    )
    from app.simulation.geometry_functions.planner import _sap_xep_phu_thuoc_loi_goi

    plan_dangling = deepcopy(plan)
    plan_dangling.calls.append(
        {
            "id": "f_proj",
            "fn": "orthogonal_projection_line",
            "args": {"point": "A", "line_ref": "f_missing_line", "image": "H"},
            "source": {"quotes": ["Tính khoảng cách từ A đến giao tuyến của (SAB) và (SCD)."]},
        }
    )
    with pytest.raises(TuChoi) as exc_dangling:
        _sap_xep_phu_thuoc_loi_goi(plan_dangling)
    assert exc_dangling.value.code == "DANGLING_DEPENDENCY"

    payload_unknown_solid = deepcopy(payload_dangling_question)
    payload_unknown_solid["facts"][-1] = {
        "id": "q1",
        "kind": "question",
        "role": "question",
        "quotes": ["Tính khoảng cách từ A đến giao tuyến của (SAB) và (SCD)."],
        "quantity": "volume",
        "solid": "S.XYZ",
    }
    with pytest.raises(TuChoi) as exc_solid:
        lap_ke_hoach(payload_unknown_solid, text)
    assert exc_solid.value.code == "UNKNOWN_SOLID"


def test_multi_goal_composition_places_all_auxiliary_constructions_before_asks():
    """6. In multi-goal problems where an earlier question (`q1: ask_volume`) precedes a composed question
    (`q2: ask_area` with unnamed midpoint), all auxiliary construction calls (`q2_aux`) precede all `ask_*` calls."""
    c = corpus("pyramid-shared-midpoint-area-and-distance", "positive")
    facts = deepcopy(c["payload"]["facts"])
    # Insert a volume question q0 before q1 and q2
    text = c["text"].replace("Tính diện tích", "Tính thể tích khối chóp S.ABCD. Tính diện tích")
    facts.insert(
        0,
        {
            "id": "q0",
            "kind": "question",
            "role": "question",
            "quotes": ["Tính thể tích khối chóp S.ABCD."],
            "quantity": "volume",
            "solid": "S.ABCD",
        },
    )
    plan = lap_ke_hoach({"facts": facts}, text)
    ask_indices = [i for i, call in enumerate(plan.calls) if call["fn"].startswith("ask_")]
    construct_indices = [i for i, call in enumerate(plan.calls) if not call["fn"].startswith("ask_")]
    assert max(construct_indices) < min(ask_indices)

    res = run_fact_route(text, {"facts": facts})
    assert res.status == "SERVED", (res.code, res.reason)
    assert set(res.answers.keys()) == {"q0", "q1", "q2"}


@pytest.mark.parametrize(
    "case_source",
    [
        ("holdout", "H11_SKEW_DISTANCE_COMPOSITION"),
        ("holdout", "H12_PROJECTION_MIDPOINT_ANGLE"),
        ("corpus", "pyramid-projection-and-unnamed-midpoint-area"),
    ],
)
def test_reordered_equivalent_inputs_produce_valid_served_results_and_identical_answers(case_source):
    """7 & 8. Reversing fact order and reassigning reversed fact IDs produces a valid served result,
    identical exact answers, and a monotonic Scene3D timeline where dependencies precede dependents."""
    kind, cid = case_source
    case = hold(cid) if kind == "holdout" else corpus(cid, "positive")
    baseline = run_fact_route(case["text"], case["payload"])
    assert baseline.status == "SERVED", (baseline.code, baseline.reason)

    orig_facts = deepcopy(case["payload"]["facts"])
    # Reverse the list AND invert non-question premise IDs so auxiliary premises have smaller IDs than solid/base
    premises = [f for f in orig_facts if f["kind"] != "question"]
    questions = [f for f in orig_facts if f["kind"] == "question"]
    prem_ids = [f["id"] for f in premises]
    id_map = dict(zip(prem_ids, reversed(prem_ids)))
    reordered_premises = []
    for f in reversed(premises):
        f_new = deepcopy(f)
        f_new["id"] = id_map[f["id"]]
        if f_new.get("line_ref") in id_map:
            f_new["line_ref"] = id_map[f_new["line_ref"]]
        reordered_premises.append(f_new)
    reordered_questions = []
    for q in reversed(questions):
        q_new = deepcopy(q)
        if q_new.get("line_ref") in id_map:
            q_new["line_ref"] = id_map[q_new["line_ref"]]
        reordered_questions.append(q_new)

    reordered_payload = {"facts": reordered_questions + reordered_premises}
    res = run_fact_route(case["text"], reordered_payload)
    assert res.status == "SERVED", (res.code, res.reason)
    assert res.answer_exact == baseline.answer_exact
    assert res.points == baseline.points
    assert res.metric == baseline.metric

    # Verify Scene3D timeline consistency (Requirement 8)
    scene = res.scene3d
    steps = scene["formation"]["steps"]
    assert [s["step_index"] for s in steps] == list(range(len(steps)))
    born: dict[str, int] = {}
    for st in steps:
        for vid in st["visible_ids"]:
            born.setdefault(vid, st["step_index"])
    for obj in scene["objects"]:
        if obj["id"] in born:
            for dep in obj.get("depends") or ():
                if dep in born:
                    assert born[dep] <= born[obj["id"]], (obj["id"], dep, born[dep], born[obj["id"]])
                    if obj.get("origin") == "derived" and obj["type"] == "point3":
                        assert born[dep] < born[obj["id"]], (obj["id"], dep, born[dep], born[obj["id"]])
