"""Continuation 11 (§§4, 6, 7, 8) — Generalized Planner Recomposition & Independent Planning Oracle Tests."""

from __future__ import annotations

import ast
from dataclasses import replace
from fractions import Fraction
import inspect
import json
from pathlib import Path

import pytest

from app.ai.function_route import run_fact_route
from app.simulation.geometry.radical import Radical
from app.simulation.geometry_functions import engine, planner, registry
from scripts import planning_oracle


#: C11 C1a: "Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên SD." — the question describes the point.
_C1A = [
    {"id": "f1", "kind": "solid", "role": "premise", "quotes": ["Cho hình chóp S.ABCD."], "solid": "S.ABCD",
     "solid_type": "pyramid"},
    {"id": "f2", "kind": "polygon_shape", "role": "premise", "quotes": ["Đáy ABCD là hình vuông cạnh 3."],
     "points": ["A", "B", "C", "D"], "shape": "square", "value": "3"},
    {"id": "f3", "kind": "perpendicular", "role": "premise", "quotes": ["SA vuông góc với (ABCD)."],
     "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"]},
    {"id": "f4", "kind": "length", "role": "premise", "quotes": ["SA = 4."], "points": ["S", "A"], "measure": "segment",
     "value": "4"},
    {"id": "q1", "kind": "question", "role": "question",
     "quotes": ["Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên SD."], "quantity": "length",
     "point_kind": "orthogonal_projection_line", "points": ["A", "S", "D"], "points_b": ["C"]},
]


def test_c16_a_function_known_only_by_its_contract_is_selected_without_dispatch_code(monkeypatch):
    """§V.5.5 (planner level only — the clone has no IR of its own, so nothing is executed): a new Registry entry
    carrying the SAME contracts as `orthogonal_projection_line` is selected by the effect resolver (ties by name), written
    from its contract template, and tagged source-defined; no planner code names it."""
    src = registry.REGISTRY["orthogonal_projection_line"]
    monkeypatch.setitem(registry.REGISTRY, "a_projection_onto_line", replace(src, name="a_projection_onto_line"))
    k = planner.lap_ke_hoach({"facts": _C1A}, "")
    step = next(c for c in k.calls if c["id"] not in k.fact_ids)
    assert step["fn"] == "a_projection_onto_line" and step["args"]["point"] == "A"
    assert k.search_telemetry["source_defined_steps"] == [step["id"]]


def test_c16_removing_the_only_producer_refuses_instead_of_guessing(monkeypatch):
    """The refusal comes from the planner's library pre-check (no Registry function can build the described point),
    before the effect resolver runs (C16 review MINOR-5)."""
    monkeypatch.delitem(registry.REGISTRY, "orthogonal_projection_line")
    with pytest.raises(registry.TuChoi) as e:
        planner.lap_ke_hoach({"facts": _C1A}, "")
    assert e.value.code == "UNSUPPORTED_CAPABILITY"


def test_c16_a_definition_the_solid_word_carries_is_source_defined_not_a_registered_rule():
    """C16 review MINOR-2: "hình lập phương" ⇒ its base is a regular polygon. The planner writes that step itself
    (`<solid>_day`), but it restates the source's own definition — /23 called the plan source-explicit, and so must /24."""
    from tests.geometry.test_hybrid_section_slice import _area, _section, f
    q = ["Cho hình lập phương ABCD.A'B'C'D' cạnh 2.", "Xác định thiết diện của hình lập phương cắt bởi mặt phẳng (A'BD).",
         "Tính diện tích thiết diện của hình lập phương cắt bởi mặt phẳng (A'BD)."]
    facts = [f("f1", "solid", q[0], solid="ABCD.A'B'C'D'", solid_type="cube"),
             f("f2", "length", q[0], solid="ABCD.A'B'C'D'", measure="edge", value="2"),
             _section("f3", q[1], ["A'", "B", "D"], solid="ABCD.A'B'C'D'"),
             _area(q[2], ["A'", "B", "D"], solid="ABCD.A'B'C'D'")]
    tel = run_fact_route(" ".join(q), {"facts": facts}).planner["search_telemetry"]
    assert tel["source_defined_steps"] == ["f1_day"] and not tel["registered_decomposition_steps"]
    assert tel["classification"] == "SOURCE_EXPLICIT_SEQUENCE"


def _honest(tel: dict) -> bool:
    """C16: these compositions build the point the question describes (SOURCE-defined) and, for a section, a declared
    rule (REGISTERED); the planner no longer calls them discovered (`route-b-composition-relabel.json`)."""
    own = set(tel["planner_originated_steps"])
    return (tel["classification"] in ("SOURCE_EXPLICIT_SEQUENCE", "REGISTERED_DECOMPOSITION")
            and not tel["search_generated_steps"] and bool(tel["source_defined_steps"])
            and own == set(tel["source_defined_steps"]) | set(tel["registered_decomposition_steps"]))
from scripts.planning_oracle import (
    ORACLE_STEP_LIMIT,
    audit_registry_contracts,
    verify_reachability_oracle,
)


def _pyr_text_and_facts(side: int = 2, sa: int = 2) -> tuple[str, list[dict]]:
    s1 = "Cho hình chóp S.ABCD."
    s2 = f"Đáy ABCD là hình vuông cạnh {side}."
    s3 = "SA vuông góc với (ABCD)."
    s4 = f"SA = {sa}."
    txt = f"{s1} {s2} {s3} {s4} "
    facts = [
        {"id": "f1", "kind": "solid", "role": "premise", "quotes": [s1], "solid": "S.ABCD", "solid_type": "pyramid"},
        {"id": "f2", "kind": "polygon_shape", "role": "premise", "quotes": [s2], "points": ["A", "B", "C", "D"], "shape": "square", "value": str(side)},
        {"id": "f3", "kind": "perpendicular", "role": "premise", "quotes": [s3], "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"]},
        {"id": "f4", "kind": "length", "role": "premise", "quotes": [s4], "points": ["S", "A"], "measure": "segment", "value": str(sa)},
    ]
    return txt, facts


def _pyr_base_calls(side: int = 2, sa: int = 2, quote: str = "Cho hình chóp S.ABCD.") -> list[dict]:
    src = {"quote": quote}
    return [
        {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": src, "depends_on": []},
        {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": str(side)}, "source": src, "depends_on": ["c1"]},
        {"id": "c3", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "source": src, "depends_on": ["c1"]},
        {"id": "c4", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": str(sa)}, "source": src, "depends_on": ["c1"]},
    ]


def _run(text: str, facts: list[dict]):
    return run_fact_route(text, json.loads(json.dumps({"facts": facts})))


def _exact_vals(r) -> dict[str, object]:
    return {qid: r.exec_result.final_memory[f"kq_{qid}"] for qid in (r.answers or {})}


def test_planning_oracle_has_zero_imports_from_planner():
    tree = ast.parse(Path(planning_oracle.__file__).read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            imported.append(mod)
            imported.extend(f"{mod}.{alias.name}" for alias in node.names)
    assert not any("planner" in name for name in imported), imported


def test_registry_contract_audit_covers_all_functions_and_cross_cutting_axes():
    report = audit_registry_contracts()
    assert report["total_functions"] == len(registry.REGISTRY)
    assert report["total_functions"] >= 40
    for fn_rec in report["functions"]:
        for key in (
            "name",
            "kind",
            "inputs",
            "outputs",
            "preconditions",
            "postconditions",
            "needs",
            "effects",
            "object_types",
            "source_requirements",
            "derived_dependencies",
            "computational_limitations",
            "verification_authority",
        ):
            assert key in fn_rec, (fn_rec["name"], key)
    cc = report["cross_cutting"]
    assert "Point" in cc["multi_producer_effects"]
    assert len(cc["multi_producer_effects"]["Point"]) >= 6
    assert "section" in cc["multi_step_intermediate_consumers"]
    assert "ask_section_area" in cc["multi_step_intermediate_consumers"]


def test_oracle_confirms_flagship_indirect_plane_section_reachability_independently():
    base_txt, _ = _pyr_text_and_facts(side=3, sa=4)
    src = (
        base_txt
        + "Mặt phẳng (P) đi qua hình chiếu vuông góc của A lên SD và song song với mặt phẳng (SBC). "
        "Xác định thiết diện của hình chóp cắt bởi (P) và tính diện tích thiết diện đó."
    )
    verdict = verify_reachability_oracle(
        source_text=src,
        base_calls=_pyr_base_calls(side=3, sa=4, quote=src),
        solid_vertices=["S", "A", "B", "C", "D"],
        goals=[
            {
                "kind": "section",
                "solid": "S.ABCD",
                "plane_spec": {
                    "relation": "parallel_plane",
                    "through": {"kind": "orthogonal_projection_line", "point": "A", "line": ["S", "D"]},
                    "target_plane": ["S", "B", "C"],
                },
            },
            {
                "kind": "ask_section_area",
                "solid": "S.ABCD",
                "plane_spec": {
                    "relation": "parallel_plane",
                    "through": {"kind": "orthogonal_projection_line", "point": "A", "line": ["S", "D"]},
                    "target_plane": ["S", "B", "C"],
                },
            },
        ],
    )
    assert verdict.classification == "REACHABLE", verdict.reason
    assert verdict.plan_exists is True
    assert verdict.kernel_confirmed is True
    assert verdict.has_dependency_cycle is False
    assert "1107/250" in verdict.exact_answers.values()


def test_c1_unhinted_orthogonal_projection_line_to_length():
    base_txt, base_facts = _pyr_text_and_facts(side=3, sa=4)
    ask = "Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên SD."
    r = _run(
        base_txt + ask,
        [
            *base_facts,
            {
                "id": "q1",
                "kind": "question",
                "role": "question",
                "quotes": [ask],
                "quantity": "length",
                "point_kind": "orthogonal_projection_line",
                "points": ["A", "S", "D"],
                "points_b": ["C"],
            },
        ],
    )
    assert r.status == "SERVED", (r.code, r.reason)
    assert _exact_vals(r)["q1"] == Radical(Fraction(3, 5), 34)
    assert _honest(r.planner["search_telemetry"])


def test_c2_unhinted_orthogonal_projection_plane_to_length():
    base_txt, base_facts = _pyr_text_and_facts(side=2, sa=2)
    ask = "Tính độ dài đoạn thẳng nối điểm D với hình chiếu vuông góc của A lên mặt phẳng (SBC)."
    r = _run(
        base_txt + ask,
        [
            *base_facts,
            {
                "id": "q1",
                "kind": "question",
                "role": "question",
                "quotes": [ask],
                "quantity": "length",
                "point_kind": "orthogonal_projection",
                "points": ["A", "S", "B", "C"],
                "points_b": ["D"],
            },
        ],
    )
    assert r.status == "SERVED", (r.code, r.reason)
    assert _exact_vals(r)["q1"] == Radical(1, 6)
    assert _honest(r.planner["search_telemetry"])


def test_c3_unhinted_intersect_line_line_to_distance_pyramid_and_cube():
    base_txt, base_facts = _pyr_text_and_facts(side=2, sa=2)
    ask_pyr = "Tính khoảng cách từ giao điểm của hai đường chéo AC và BD đến (SBC)."
    r_pyr = _run(
        base_txt + ask_pyr,
        [
            *base_facts,
            {
                "id": "q1",
                "kind": "question",
                "role": "question",
                "quotes": [ask_pyr],
                "quantity": "distance",
                "point_kind": "intersect_line_line",
                "points": ["A", "C", "B", "D"],
                "points_b": ["S", "B", "C"],
            },
        ],
    )
    assert r_pyr.status == "SERVED", (r_pyr.code, r_pyr.reason)
    assert _exact_vals(r_pyr)["q1"] == Radical(Fraction(1, 2), 2)
    assert _honest(r_pyr.planner["search_telemetry"])

    s1 = "Cho hình lập phương ABCD.A'B'C'D' cạnh 2."
    ask_cube = "Tính khoảng cách từ giao điểm của AC và BD đến (A'BC')."
    r_cube = _run(
        f"{s1} {ask_cube}",
        [
            {"id": "f1", "kind": "solid", "role": "premise", "quotes": [s1], "solid": "ABCD.A'B'C'D'", "solid_type": "cube"},
            {"id": "f2", "kind": "length", "role": "premise", "quotes": [s1], "solid": "ABCD.A'B'C'D'", "measure": "edge", "value": "2"},
            {
                "id": "q1",
                "kind": "question",
                "role": "question",
                "quotes": [ask_cube],
                "quantity": "distance",
                "point_kind": "intersect_line_line",
                "points": ["A", "C", "B", "D"],
                "points_b": ["A'", "B", "C'"],
            },
        ],
    )
    assert r_cube.status == "SERVED", (r_cube.code, r_cube.reason)
    assert _exact_vals(r_cube)["q1"] == Radical(Fraction(2, 3), 3)


def test_c4_unhinted_intersect_line_plane_multi_goal_shared_intermediate_reuse():
    base_txt, base_facts = _pyr_text_and_facts(side=2, sa=2)
    s_mid = "Gọi M là trung điểm của SC."
    ask = (
        "Tính độ dài đoạn thẳng nối điểm A với giao điểm của AM và mặt phẳng (SBD), "
        "và khoảng cách từ giao điểm của AM và mặt phẳng (SBD) đến (ABCD)."
    )
    r = _run(
        f"{base_txt}{s_mid} {ask}",
        [
            *base_facts,
            {"id": "f5", "kind": "point_def", "role": "premise", "quotes": [s_mid], "point": "M", "point_kind": "midpoint", "points": ["S", "C"]},
            {
                "id": "q1",
                "kind": "question",
                "role": "question",
                "quotes": [ask],
                "quantity": "length",
                "point_kind": "intersect_line_plane",
                "points": ["A", "M", "S", "B", "D"],
                "points_b": ["A"],
            },
            {
                "id": "q2",
                "kind": "question",
                "role": "question",
                "quotes": [ask],
                "quantity": "distance",
                "point_kind": "intersect_line_plane",
                "points": ["A", "M", "S", "B", "D"],
                "points_b": ["A", "B", "C", "D"],
            },
        ],
    )
    assert r.status == "SERVED", (r.code, r.reason)
    vals = _exact_vals(r)
    assert vals["q1"] == Radical(Fraction(2, 3), 3)
    assert vals["q2"] == Fraction(2, 3)
    ilp_calls = [c for c in r.planner["calls"] if c["fn"] == "intersect_line_plane"]
    assert len(ilp_calls) == 1
    assert r.planner["search_telemetry"]["reused_intermediates"] >= 1


def test_c5_flagship_unhinted_indirect_point_parallel_plane_section_and_area_and_adversarial_twin():
    base_txt, base_facts = _pyr_text_and_facts(side=3, sa=4)
    s_pl = "Mặt phẳng (P) đi qua hình chiếu vuông góc của A lên SD và song song với mặt phẳng (SBC)."
    s_ask = "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó."
    r = _run(
        f"{base_txt}{s_pl} {s_ask}",
        [
            *base_facts,
            {
                "id": "sec1",
                "kind": "section",
                "role": "question",
                "quotes": [s_pl, s_ask],
                "solid": "S.ABCD",
                "plane_name": "P",
                "point_kind": "orthogonal_projection_line",
                "points": ["A", "S", "D"],
                "plane_relation": "parallel",
                "points_b": ["S", "B", "C"],
            },
            {
                "id": "q1",
                "kind": "question",
                "role": "question",
                "quotes": [s_pl, s_ask],
                "quantity": "area",
                "solid": "S.ABCD",
                "plane_name": "P",
                "point_kind": "orthogonal_projection_line",
                "points": ["A", "S", "D"],
                "plane_relation": "parallel",
                "points_b": ["S", "B", "C"],
            },
        ],
    )
    assert r.status == "SERVED", (r.code, r.reason)
    assert _exact_vals(r)["q1"] == Fraction(1107, 250)
    fns = [c["fn"] for c in r.planner["calls"]]
    assert "orthogonal_projection_line" in fns
    assert "translate_point" in fns
    assert "section" in fns
    assert "ask_section_area" in fns
    assert _honest(r.planner["search_telemetry"])

    # Invalidating constraint twin: foot of A on SB already lies in (SBC), so (P) coincides with face (SBC)
    s_pl_bad = s_pl.replace("lên SD", "lên SB")
    r_bad = _run(
        f"{base_txt}{s_pl_bad} {s_ask}",
        [
            *base_facts,
            {
                "id": "sec1",
                "kind": "section",
                "role": "question",
                "quotes": [s_pl_bad, s_ask],
                "solid": "S.ABCD",
                "plane_name": "P",
                "point_kind": "orthogonal_projection_line",
                "points": ["A", "S", "B"],
                "plane_relation": "parallel",
                "points_b": ["S", "B", "C"],
            },
            {
                "id": "q1",
                "kind": "question",
                "role": "question",
                "quotes": [s_pl_bad, s_ask],
                "quantity": "area",
                "solid": "S.ABCD",
                "plane_name": "P",
                "point_kind": "orthogonal_projection_line",
                "points": ["A", "S", "B"],
                "plane_relation": "parallel",
                "points_b": ["S", "B", "C"],
            },
        ],
    )
    assert r_bad.status == "REFUSED"
    assert r_bad.code in ("PLANE_DOES_NOT_CUT", "DERIVED_PLANE_IS_REFERENCE", "PLANE_IS_FACE", "PLANE_TOUCHES_EDGE")


def test_c6_unhinted_indirect_point_perp_line_and_derived_line_so_section_area():
    base_txt, base_facts = _pyr_text_and_facts(side=2, sa=2)
    s_pl_a = "Mặt phẳng (P) đi qua trung điểm của SA và vuông góc với SC."
    s_ask_a = "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó."
    r_a = _run(
        f"{base_txt}{s_pl_a} {s_ask_a}",
        [
            *base_facts,
            {
                "id": "sec1",
                "kind": "section",
                "role": "question",
                "quotes": [s_pl_a, s_ask_a],
                "solid": "S.ABCD",
                "plane_name": "P",
                "point_kind": "midpoint",
                "points": ["S", "A"],
                "plane_relation": "perpendicular",
                "points_b": ["S", "C"],
            },
            {
                "id": "q1",
                "kind": "question",
                "role": "question",
                "quotes": [s_pl_a, s_ask_a],
                "quantity": "area",
                "solid": "S.ABCD",
                "plane_name": "P",
                "point_kind": "midpoint",
                "points": ["S", "A"],
                "plane_relation": "perpendicular",
                "points_b": ["S", "C"],
            },
        ],
    )
    assert r_a.status == "SERVED", (r_a.code, r_a.reason)
    assert _exact_vals(r_a)["q1"] == Radical(Fraction(1, 6), 3)

    s_o = "Gọi O là giao điểm của AC và BD."
    s_pl_b = "Mặt phẳng (P) đi qua hình chiếu vuông góc của O lên SC và vuông góc với SO."
    s_ask_b = "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó."
    full_b = f"{base_txt}{s_o} {s_pl_b} {s_ask_b}"
    r_b = _run(
        full_b,
        [
            *base_facts,
            {"id": "f5", "kind": "point_def", "role": "premise", "quotes": [s_o], "point": "O", "point_kind": "intersect_line_line", "points_a": ["A", "C"], "points_b": ["B", "D"]},
            {
                "id": "sec1",
                "kind": "section",
                "role": "question",
                "quotes": [s_pl_b, s_ask_b],
                "solid": "S.ABCD",
                "plane_name": "P",
                "point_kind": "orthogonal_projection_line",
                "points": ["O", "S", "C"],
                "plane_relation": "perpendicular",
                "points_b": ["S", "O"],
            },
            {
                "id": "q1",
                "kind": "question",
                "role": "question",
                "quotes": [s_pl_b, s_ask_b],
                "quantity": "area",
                "solid": "S.ABCD",
                "plane_name": "P",
                "point_kind": "orthogonal_projection_line",
                "points": ["O", "S", "C"],
                "plane_relation": "perpendicular",
                "points_b": ["S", "O"],
            },
        ],
    )
    assert r_b.status == "SERVED", (r_b.code, r_b.reason)
    orc_b = verify_reachability_oracle(
        source_text=full_b,
        base_calls=[
            *_pyr_base_calls(side=2, sa=2, quote=full_b),
            {"id": "c5", "fn": "intersect_line_line", "args": {"point": "O", "line1": ["A", "C"], "line2": ["B", "D"]}, "source": {"quote": s_o}, "depends_on": ["c1"]},
        ],
        solid_vertices=["S", "A", "B", "C", "D"],
        goals=[
            {
                "kind": "ask_section_area",
                "solid": "S.ABCD",
                "plane_spec": {
                    "relation": "perpendicular_line",
                    "through": {"kind": "orthogonal_projection_line", "point": "O", "line": ["S", "C"]},
                    "target_line": ["S", "O"],
                    "anchors": ["A", "B"],
                },
            }
        ],
    )
    assert orc_b.classification == "REACHABLE", orc_b.reason
    assert engine.dinh_dang(_exact_vals(r_b)["q1"]) in orc_b.exact_answers.values()


def test_c7_prism_topology_unhinted_orthogonal_projection_line():
    s1 = "Cho hình lăng trụ đứng ABC.A'B'C'."
    s2 = "Đáy ABC là tam giác vuông tại A."
    s3 = "AB = 3, AC = 4, AA' = 4."
    ask = "Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên A'B."
    r = _run(
        f"{s1} {s2} {s3} {ask}",
        [
            {"id": "f1", "kind": "solid", "role": "premise", "quotes": [s1], "solid": "ABC.A'B'C'", "solid_type": "prism", "right": True},
            {"id": "f2", "kind": "right_angle", "role": "premise", "quotes": [s2], "at": "A", "points": ["B", "C"]},
            {"id": "f3", "kind": "length", "role": "premise", "quotes": [s3], "points": ["A", "B"], "measure": "segment", "value": "3"},
            {"id": "f4", "kind": "length", "role": "premise", "quotes": [s3], "points": ["A", "C"], "measure": "segment", "value": "4"},
            {"id": "f5", "kind": "length", "role": "premise", "quotes": [s3], "points": ["A", "A'"], "measure": "segment", "value": "4"},
            {
                "id": "q1",
                "kind": "question",
                "role": "question",
                "quotes": [ask],
                "quantity": "length",
                "point_kind": "orthogonal_projection_line",
                "points": ["A", "A'", "B"],
                "points_b": ["C"],
            },
        ],
    )
    assert r.status == "SERVED", (r.code, r.reason)
    assert _exact_vals(r)["q1"] == Radical(Fraction(4, 5), 34)


def test_three_way_telemetry_distinguishes_explicit_vs_registered_decomposition_vs_discovered():
    base_txt, base_facts = _pyr_text_and_facts(2, 2)
    s_mid = "Gọi M là trung điểm của SC."
    ask_a = "Tính độ dài đoạn AM."
    r_a = _run(
        f"{base_txt}{s_mid} {ask_a}",
        [
            *base_facts,
            {"id": "f5", "kind": "point_def", "role": "premise", "quotes": [s_mid], "point": "M", "point_kind": "midpoint", "points": ["S", "C"]},
            {"id": "q1", "kind": "question", "role": "question", "quotes": [ask_a], "quantity": "length", "points": ["A", "M"]},
        ],
    )
    assert r_a.status == "SERVED", (r_a.code, r_a.reason)
    assert r_a.planner["search_telemetry"]["classification"] == "SOURCE_EXPLICIT_SEQUENCE"

    # B: REGISTERED_DECOMPOSITION — named point M distance to line AD (spawns foot H via registered distance rule, no unnamed Point descriptor)
    ask_b = "Tính khoảng cách từ M đến AD."
    r_b = _run(
        f"{base_txt}{s_mid} {ask_b}",
        [
            *base_facts,
            {"id": "f5", "kind": "point_def", "role": "premise", "quotes": [s_mid], "point": "M", "point_kind": "midpoint", "points": ["S", "C"]},
            {"id": "q1", "kind": "question", "role": "question", "quotes": [ask_b], "quantity": "distance", "points_a": ["M"], "points_b": ["A", "D"]},
        ],
    )
    assert r_b.status == "SERVED", (r_b.code, r_b.reason)
    assert r_b.planner["search_telemetry"]["classification"] == "REGISTERED_DECOMPOSITION"


def test_role_swapped_projection_and_derived_marked_as_given_fail_closed():
    base_txt, base_facts = _pyr_text_and_facts(side=3, sa=4)
    # Role swap: text says projection of B onto SA, facts claim projection of A onto SB
    ask_swap = "Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của B lên SA."
    r_swap = _run(
        base_txt + ask_swap,
        [
            *base_facts,
            {
                "id": "q1",
                "kind": "question",
                "role": "question",
                "quotes": [ask_swap],
                "quantity": "length",
                "point_kind": "orthogonal_projection_line",
                "points": ["A", "S", "B"],
                "points_b": ["C"],
            },
        ],
    )
    assert r_swap.status == "REFUSED"
    assert r_swap.code in ("UNGROUNDED_STEP", "SOURCE_MISMATCH", "SOURCE_OBJECT_MISMATCH")

    # DERIVED marked as GIVEN: setting arbitrary length on derived midpoint M without source support
    s_mid = "Gọi M là trung điểm của SC."
    ask_len = "Tính độ dài đoạn AM."
    r_forged = _run(
        f"{base_txt}{s_mid} {ask_len}",
        [
            *base_facts,
            {"id": "f5", "kind": "point_def", "role": "premise", "quotes": [s_mid], "point": "M", "point_kind": "midpoint", "points": ["S", "C"]},
            {"id": "f6", "kind": "length", "role": "premise", "quotes": [s_mid], "points": ["A", "M"], "measure": "segment", "value": "9"},
            {"id": "q1", "kind": "question", "role": "question", "quotes": [ask_len], "quantity": "length", "points": ["A", "M"]},
        ],
    )
    assert r_forged.status == "REFUSED"


def test_metamorphic_vertex_rename_fact_permutation_and_scale_homogeneity():
    # Rename S.ABCD -> P.MNRQ, permute independent facts, and double scale (3,4) -> (6,8): area scales by 2^2 = 4!
    s1 = "Cho hình chóp P.MNRQ."
    s2 = "Đáy MNRQ là hình vuông cạnh 6."
    s3 = "PM vuông góc với (MNRQ)."
    s4 = "PM = 8."
    s_pl = "Mặt phẳng (K) đi qua hình chiếu vuông góc của M lên PQ và song song với mặt phẳng (PNR)."
    s_ask = "Xác định thiết diện của hình chóp P.MNRQ cắt bởi (K) và tính diện tích thiết diện đó."
    r_ren = _run(
        f"{s1} {s2} {s3} {s4} {s_pl} {s_ask}",
        [
            {"id": "f4", "kind": "length", "role": "premise", "quotes": [s4], "points": ["P", "M"], "measure": "segment", "value": "8"},
            {"id": "f1", "kind": "solid", "role": "premise", "quotes": [s1], "solid": "P.MNRQ", "solid_type": "pyramid"},
            {"id": "f3", "kind": "perpendicular", "role": "premise", "quotes": [s3], "points_a": ["P", "M"], "points_b": ["M", "N", "R", "Q"]},
            {"id": "f2", "kind": "polygon_shape", "role": "premise", "quotes": [s2], "points": ["M", "N", "R", "Q"], "shape": "square", "value": "6"},
            {
                "id": "sec1",
                "kind": "section",
                "role": "question",
                "quotes": [s_pl, s_ask],
                "solid": "P.MNRQ",
                "plane_name": "K",
                "point_kind": "orthogonal_projection_line",
                "points": ["M", "P", "Q"],
                "plane_relation": "parallel",
                "points_b": ["P", "N", "R"],
            },
            {
                "id": "q1",
                "kind": "question",
                "role": "question",
                "quotes": [s_pl, s_ask],
                "quantity": "area",
                "solid": "P.MNRQ",
                "plane_name": "K",
                "point_kind": "orthogonal_projection_line",
                "points": ["M", "P", "Q"],
                "plane_relation": "parallel",
                "points_b": ["P", "N", "R"],
            },
        ],
    )
    assert r_ren.status == "SERVED", (r_ren.code, r_ren.reason)
    assert _exact_vals(r_ren)["q1"] == 4 * Fraction(1107, 250)


def test_lying_projection_contract_is_caught_by_engine_gram_verifier(monkeypatch):
    base_txt, base_facts = _pyr_text_and_facts(side=3, sa=4)
    ask = "Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên SD."
    opl_spec = registry.REGISTRY["orthogonal_projection_line"]
    opl_pc = next(c for c in registry.planning_contracts(opl_spec) if c.descriptor == "orthogonal_projection_line")
    fake_mid_pc = replace(
        opl_pc,
        inputs=(registry.PlanningTerm("Point", ("P",)), registry.PlanningTerm("Line", ("L",))),
        call=(("point", "H"), ("segment", "L")),
    )
    monkeypatch.setitem(registry.REGISTRY, "orthogonal_projection_line", replace(opl_spec, planning_extra=()))
    monkeypatch.setitem(registry.REGISTRY, "midpoint", replace(registry.REGISTRY["midpoint"], planning_extra=(fake_mid_pc,)))
    r = _run(
        base_txt + ask,
        [
            *base_facts,
            {
                "id": "q1",
                "kind": "question",
                "role": "question",
                "quotes": [ask],
                "quantity": "length",
                "point_kind": "orthogonal_projection_line",
                "points": ["A", "S", "D"],
                "points_b": ["C"],
            },
        ],
    )
    assert r.status == "REFUSED"
    assert r.code == "ENGINE_SELF_CHECK_FAILED"


def test_search_exhausted_exposes_explicit_outcome_and_telemetry(monkeypatch):
    monkeypatch.setattr(planner, "MAX_EFFECT_CANDIDATES", 0)
    base_txt, base_facts = _pyr_text_and_facts(side=3, sa=4)
    ask = "Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên SD."
    r = _run(
        base_txt + ask,
        [
            *base_facts,
            {
                "id": "q1",
                "kind": "question",
                "role": "question",
                "quotes": [ask],
                "quantity": "length",
                "point_kind": "orthogonal_projection_line",
                "points": ["A", "S", "D"],
                "points_b": ["C"],
            },
        ],
    )
    assert r.status == "REFUSED"
    assert r.code == "PLAN_TOO_LARGE"
    assert (r.details or {}).get("outcome") == "SEARCH_EXHAUSTED"


def test_oracle_missing_primitive_unsupported_domain_insufficient_givens_and_not_established():
    assert (
        verify_reachability_oracle(
            source_text="Tâm đường tròn ngoại tiếp",
            base_calls=_pyr_base_calls(),
            goals=[{"kind": "circumcenter"}],
        ).classification
        == "MISSING_PRIMITIVE"
    )
    assert (
        verify_reachability_oracle(
            source_text="Tổng arccos vô tỉ",
            base_calls=_pyr_base_calls(),
            goals=[{"kind": "ask_angle_lines", "domain": "transcendental_arccos_degree_sum"}],
        ).classification
        == "UNSUPPORTED_EXACT_DOMAIN"
    )
    assert (
        verify_reachability_oracle(
            source_text="Thiếu SA",
            base_calls=_pyr_base_calls()[:3],
            goals=[{"kind": "ask_length", "a": "S", "b": "C"}],
        ).classification
        == "INSUFFICIENT_GIVENS"
    )
    assert (
        verify_reachability_oracle(
            source_text="Vượt giới hạn hữu hạn",
            base_calls=_pyr_base_calls(),
            goals=[{"kind": "ask_length", "a": "S", "b": "C"}],
            max_extra_steps=ORACLE_STEP_LIMIT + 1,
        ).classification
        == "NOT_ESTABLISHED"
    )


def test_remaining_reachable_but_search_missed_due_to_flat_typedfact_expressivity():
    base_txt, base_facts = _pyr_text_and_facts(side=2, sa=2)
    base_calls = _pyr_base_calls(side=2, sa=2)

    # R1: Recursive 2-level unnamed point descriptor (projection of midpoint(SC) onto (ABCD))
    orc_r1 = verify_reachability_oracle(
        source_text="Tính độ dài đoạn nối C với hình chiếu vuông góc của trung điểm SC lên (ABCD).",
        base_calls=base_calls,
        goals=[
            {
                "kind": "ask_length",
                "a": "C",
                "b": {"kind": "orthogonal_projection", "point": {"kind": "midpoint", "segment": ["S", "C"]}, "plane": ["A", "B", "C", "D"]},
            }
        ],
    )
    assert orc_r1.classification == "REACHABLE" and orc_r1.kernel_confirmed
    assert "√2" in orc_r1.exact_answers.values()
    r_r1 = _run(
        base_txt + "Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của trung điểm SC lên (ABCD).",
        [
            *base_facts,
            {
                "id": "q1",
                "kind": "question",
                "role": "question",
                "quotes": ["Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của trung điểm SC lên (ABCD)."],
                "quantity": "length",
                "point_kind": "orthogonal_projection",
                "points": ["S", "C", "A", "B", "C", "D"],
                "points_b": ["C"],
            },
        ],
    )
    assert r_r1.status == "REFUSED"

    # R2: Dual unnamed point descriptors in a single binary goal (midpoint(SA) to midpoint(BC))
    orc_r2 = verify_reachability_oracle(
        source_text="Tính độ dài đoạn thẳng nối trung điểm của SA với trung điểm của BC.",
        base_calls=base_calls,
        goals=[
            {
                "kind": "ask_length",
                "a": {"kind": "midpoint", "segment": ["S", "A"]},
                "b": {"kind": "midpoint", "segment": ["B", "C"]},
            }
        ],
    )
    assert orc_r2.classification == "REACHABLE" and orc_r2.kernel_confirmed
    assert "√6" in orc_r2.exact_answers.values()
    r_r2 = _run(
        base_txt + "Tính độ dài đoạn thẳng nối trung điểm của SA với trung điểm của BC.",
        [
            *base_facts,
            {
                "id": "q1",
                "kind": "question",
                "role": "question",
                "quotes": ["Tính độ dài đoạn thẳng nối trung điểm của SA với trung điểm của BC."],
                "quantity": "length",
                "point_kind": "midpoint",
                "points": ["S", "A"],
                "points_b": ["B", "C"],
            },
        ],
    )
    assert r_r2.status == "REFUSED"


def test_no_composed_descriptor_names_hardcoded_in_effect_resolver():
    R = planner._EffectResolver
    src = "".join(
        inspect.getsource(x)
        for x in (
            R._resolve,
            R._emit,
            R.goal,
            R._chuoi,
            planner._toan_hang_muc_tieu,
            planner._dich_muc_tieu,
            planner._doc_toan_hang_mo_ta,
            planner._doi_tac,
        )
    )
    for forbidden in (
        "centroid",
        "midpoint",
        "orthogonal_projection",
        "orthogonal_projection_line",
        "intersect_line_line",
        "intersect_line_plane",
        "ask_angle_lines",
        "ask_angle_line_plane",
        "ask_area",
        "ask_length",
    ):
        assert f"'{forbidden}'" not in src and f'"{forbidden}"' not in src, forbidden


# ── Adversarial Review Round 1 Closure (BLOCKER-3, BLOCKER-4, MAJOR-1, MAJOR-2, MAJOR-3) ─────────────────────────────


def test_blocker3_effect_resolver_existing_projection_line_and_two_hop_reuse_do_not_type_error():
    base_txt, base_facts = _pyr_text_and_facts(side=2, sa=2)
    # 1. Existing premise orthogonal_projection_line + goal distance(midpoint, line)
    s_k = "Gọi K là hình chiếu vuông góc của A lên SC."
    s_q1 = "Tính khoảng cách từ trung điểm của SB đến BD."
    r1 = _run(
        f"{base_txt}{s_k} {s_q1}",
        [
            *base_facts,
            {"id": "f5", "kind": "projection", "role": "premise", "point": "A", "points": ["S", "C"], "at": "K", "quotes": [s_k]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "distance", "point_kind": "midpoint", "points": ["S", "B"], "points_b": ["B", "D"], "quotes": [s_q1]},
        ],
    )
    assert r1.status == "SERVED", (r1.code, r1.reason)
    assert _exact_vals(r1)["q1"] == Radical(Fraction(1, 2), 6)

    # 2. Two distinct distance(midpoint, line) goals in one plan
    s_q2 = "Tính khoảng cách từ trung điểm của SD đến BD."
    r2 = _run(
        f"{base_txt}{s_q1} {s_q2}",
        [
            *base_facts,
            {"id": "q1", "kind": "question", "role": "question", "quantity": "distance", "point_kind": "midpoint", "points": ["S", "B"], "points_b": ["B", "D"], "quotes": [s_q1]},
            {"id": "q2", "kind": "question", "role": "question", "quantity": "distance", "point_kind": "midpoint", "points": ["S", "D"], "points_b": ["B", "D"], "quotes": [s_q2]},
        ],
    )
    assert r2.status == "SERVED", (r2.code, r2.reason)
    assert _exact_vals(r2)["q1"] == Radical(Fraction(1, 2), 6)
    assert _exact_vals(r2)["q2"] == Radical(Fraction(1, 2), 6)

    # 3. Genuine 2-step reuse when both M = midpoint(S, B) and H = foot(M, BD) already exist in premises
    s_m = "Gọi M là trung điểm của SB."
    s_h = "Gọi H là hình chiếu vuông góc của M lên BD."
    r3 = _run(
        f"{base_txt}{s_m} {s_h} {s_q1}",
        [
            *base_facts,
            {"id": "f5", "kind": "point_def", "role": "premise", "point": "M", "point_kind": "midpoint", "points": ["S", "B"], "quotes": [s_m]},
            {"id": "f6", "kind": "projection", "role": "premise", "point": "M", "points": ["B", "D"], "at": "H", "quotes": [s_h]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "distance", "point_kind": "midpoint", "points": ["S", "B"], "points_b": ["B", "D"], "quotes": [s_q1]},
        ],
    )
    assert r3.status == "SERVED", (r3.code, r3.reason)
    assert _exact_vals(r3)["q1"] == Radical(Fraction(1, 2), 6)
    assert r3.planner["search_telemetry"]["reused_intermediates"] >= 2


def test_blocker4_degenerate_collinear_centroid_and_coincident_midpoint_refused():
    # 1. Collinear centroid (A, M=midpoint(AB), B) — both unhinted descriptor and explicit point_def
    t1 = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2, SA vuông góc với (ABC), SA = 2. "
        "Gọi M là trung điểm của AB. Tính độ dài của đoạn thẳng nối S với trọng tâm của tam giác AMB."
    )
    r_desc_cent = _run(
        t1,
        [
            {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.ABC", "quotes": ["Cho hình chóp S.ABC"]},
            {"id": "f2", "kind": "polygon_shape", "role": "premise", "shape": "equilateral_triangle", "points": ["A", "B", "C"], "value": "2", "quotes": ["đáy ABC là tam giác đều cạnh 2"]},
            {"id": "f3", "kind": "perpendicular", "role": "premise", "points_a": ["S", "A"], "points_b": ["A", "B", "C"], "quotes": ["SA vuông góc với (ABC)"]},
            {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "A"], "value": "2", "quotes": ["SA = 2"]},
            {"id": "f5", "kind": "point_def", "role": "premise", "point": "M", "point_kind": "midpoint", "points": ["A", "B"], "quotes": ["Gọi M là trung điểm của AB"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "length", "point_kind": "centroid", "points": ["A", "M", "B"], "points_b": ["S"], "quotes": ["Tính độ dài của đoạn thẳng nối S với trọng tâm của tam giác AMB"]},
        ],
    )
    assert r_desc_cent.status == "REFUSED" and r_desc_cent.code == "COLLINEAR_POINTS"

    # 2. Coincident-endpoint midpoint (H = proj(S, ABC) == A, midpoint of AH)
    t2 = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2, SA vuông góc với (ABC), SA = 2. "
        "Gọi H là hình chiếu vuông góc của S lên (ABC). Tính độ dài của đoạn thẳng nối C với trung điểm của đoạn thẳng AH."
    )
    r_desc_mid = _run(
        t2,
        [
            {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.ABC", "quotes": ["Cho hình chóp S.ABC"]},
            {"id": "f2", "kind": "polygon_shape", "role": "premise", "shape": "equilateral_triangle", "points": ["A", "B", "C"], "value": "2", "quotes": ["đáy ABC là tam giác đều cạnh 2"]},
            {"id": "f3", "kind": "perpendicular", "role": "premise", "points_a": ["S", "A"], "points_b": ["A", "B", "C"], "quotes": ["SA vuông góc với (ABC)"]},
            {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "A"], "value": "2", "quotes": ["SA = 2"]},
            {"id": "f5", "kind": "projection", "role": "premise", "point": "S", "points": ["A", "B", "C"], "at": "H", "quotes": ["Gọi H là hình chiếu vuông góc của S lên (ABC)"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "length", "point_kind": "midpoint", "points": ["A", "H"], "points_b": ["C"], "quotes": ["Tính độ dài của đoạn thẳng nối C với trung điểm của đoạn thẳng AH"]},
        ],
    )
    assert r_desc_mid.status == "REFUSED" and r_desc_mid.code == "DEGENERATE_POINTS"


@pytest.mark.parametrize("bad_pk", ["orthogonal_projection", "orthogonal_projection_line"])
def test_major1_point_def_rejects_projection_point_kind_without_coercing_to_centroid(bad_pk: str):
    txt = "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2, SA vuông góc với (ABC), SA = 2. Gọi G là trọng tâm của tam giác SAB. Tính độ dài CG."
    r = _run(
        txt,
        [
            {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.ABC", "quotes": ["Cho hình chóp S.ABC"]},
            {"id": "f2", "kind": "polygon_shape", "role": "premise", "shape": "equilateral_triangle", "points": ["A", "B", "C"], "value": "2", "quotes": ["đáy ABC là tam giác đều cạnh 2"]},
            {"id": "f3", "kind": "perpendicular", "role": "premise", "points_a": ["S", "A"], "points_b": ["A", "B", "C"], "quotes": ["SA vuông góc với (ABC)"]},
            {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "A"], "value": "2", "quotes": ["SA = 2"]},
            {"id": "f5", "kind": "point_def", "role": "premise", "point": "G", "point_kind": bad_pk, "points": ["S", "A", "B"], "quotes": ["Gọi G là trọng tâm của tam giác SAB"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "length", "points": ["C", "G"], "quotes": ["Tính độ dài CG"]},
        ],
    )
    assert r.status == "REFUSED" and r.code == "SCHEMA_INVALID"


def test_major2_mat_vuong_duong_transitive_carrier_anchors_serve_two_hop_diagonal_and_face_perp_foot():
    # r_e1: O = AC ∩ BD, M = midpoint(O, C), plane through M ⊥ AM on square-base pyramid (side 2, SA = 2)
    base_txt, base_facts = _pyr_text_and_facts(side=2, sa=2)
    s_o = "Gọi O là giao điểm của AC và BD, M là trung điểm của OC."
    s_q = "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng qua M vuông góc với AM."
    r_e1 = _run(
        f"{base_txt}{s_o} {s_q}",
        [
            *base_facts,
            {"id": "f5", "kind": "point_def", "role": "premise", "point": "O", "point_kind": "intersect_line_line", "points_a": ["A", "C"], "points_b": ["B", "D"], "quotes": [s_o]},
            {"id": "f6", "kind": "point_def", "role": "premise", "point": "M", "point_kind": "midpoint", "points": ["O", "C"], "quotes": [s_o]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "area", "solid": "S.ABCD", "point": "M", "plane_relation": "perpendicular", "points_b": ["A", "M"], "quotes": [s_q]},
        ],
    )
    assert r_e1.status == "SERVED", (r_e1.code, r_e1.reason)

    # r_e2: (SAB) ⊥ (ABC), SA = SB = 2, H = proj(S, ABC), M = midpoint(H, B), plane through M ⊥ BH
    t_e2 = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2, mặt bên (SAB) vuông góc với mặt phẳng (ABC), SA = 2, SB = 2. "
        "Gọi H là hình chiếu vuông góc của S lên (ABC), M là trung điểm của HB. "
        "Tính diện tích thiết diện của hình chóp S.ABC cắt bởi mặt phẳng qua M vuông góc với BH."
    )
    r_e2 = _run(
        t_e2,
        [
            {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.ABC", "quotes": ["Cho hình chóp S.ABC"]},
            {"id": "f2", "kind": "polygon_shape", "role": "premise", "shape": "equilateral_triangle", "points": ["A", "B", "C"], "value": "2", "quotes": ["đáy ABC là tam giác đều cạnh 2"]},
            {"id": "f3", "kind": "perpendicular", "role": "premise", "points_a": ["S", "A", "B"], "points_b": ["A", "B", "C"], "quotes": ["mặt bên (SAB) vuông góc với mặt phẳng (ABC)"]},
            {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "A"], "value": "2", "quotes": ["SA = 2"]},
            {"id": "f5", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "B"], "value": "2", "quotes": ["SB = 2"]},
            {"id": "f6", "kind": "projection", "role": "premise", "point": "S", "points": ["A", "B", "C"], "at": "H", "quotes": ["Gọi H là hình chiếu vuông góc của S lên (ABC)"]},
            {"id": "f7", "kind": "point_def", "role": "premise", "point": "M", "point_kind": "midpoint", "points": ["H", "B"], "quotes": ["M là trung điểm của HB"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "area", "solid": "S.ABC", "point": "M", "plane_relation": "perpendicular", "points_b": ["B", "H"], "quotes": ["Tính diện tích thiết diện của hình chóp S.ABC cắt bởi mặt phẳng qua M vuông góc với BH"]},
        ],
    )
    assert r_e2.status == "SERVED", (r_e2.code, r_e2.reason)


def test_major3_recomposition_matrix_records_true_search_depth_without_zero_masking():
    run_dir = Path(__file__).resolve().parents[3] / "docs" / "evaluation" / "geometry" / "runs" / "hybrid-master-backend-replacement"
    mat = json.loads((run_dir / "planner-recomposition-matrix.json").read_text(encoding="utf-8"))
    disc = [c for c in mat["cases"] if c["classification"] == "DISCOVERED_FUNCTION_COMPOSITION"]
    assert len(disc) >= 9
    for row in disc:
        assert isinstance(row["search_depth"], int) and row["search_depth"] >= 1, row["case_id"]
        assert "max_fresh_points" in row["search_budget"], row["case_id"]


def test_blocker_r2_2_preplaced_degenerate_midpoint_centroid_divide_and_zero_vector_orthogonality_refused():
    from app.simulation.geometry_functions import engine, registry

    def _c(cid: str, fn: str, quote: str, **args) -> dict:
        return {"id": cid, "fn": fn, "args": args, "source": {"quote": quote}, "depends_on": []}

    base_calls = [
        _c("c1", "pyramid", "hình chóp S.ABC", apex="S", base=["A", "B", "C"]),
        _c("c2", "regular_polygon", "tam giác đều cạnh 2", vertices=["A", "B", "C"], side="2"),
        _c("c3", "perpendicular_line_plane", "SA vuông góc (ABC)", line=["S", "A"], plane=["A", "B", "C"]),
        _c("c4", "segment_length", "SA = 2", segment=["S", "A"], value="2"),
        _c("c5", "orthogonal_projection", "H là hình chiếu của S", point="S", plane=["A", "B", "C"], image="H"),
        _c("c6", "orthogonal_projection", "K là hình chiếu của S", point="S", plane=["A", "B", "C"], image="K"),
        _c("q1", "ask_length", "Tính SB", segment=["S", "B"]),
    ]
    src = "Cho hình chóp S.ABC có đáy là tam giác đều cạnh 2, SA vuông góc (ABC), SA = 2. H là hình chiếu của S. K là hình chiếu của S. Tính SB."

    def _run_kiem(raw_calls: list[dict], text: str) -> None:
        calls = registry.doc_ke_hoach({"calls": raw_calls})
        d = engine._Dung(calls, text, None)
        d.thu_khoi()
        d.bo_cuc_day()
        d.giai_phu_thuoc()
        d.chon_ba_mat([])
        d.kiem()

    for extra in (
        _c("d1", "midpoint", "H là hình chiếu của S", point="K", segment=["H", "A"]),
        _c("d1", "divide_segment", "H là hình chiếu của S", point="K", segment=["H", "A"], ratio="1/3"),
        _c("d1", "right_angle", "H là hình chiếu của S", vertex="A", rays=["H", "B"]),
        _c("d1", "perpendicular_lines", "H là hình chiếu của S", line1=["A", "H"], line2=["A", "B"]),
    ):
        with pytest.raises(registry.TuChoi) as exc:
            _run_kiem([*base_calls[:-1], extra, base_calls[-1]], src)
        assert exc.value.code == "INCONSISTENT_FACTS", extra["fn"]

    # Collinear pre-placed centroid AND zero-vector perpendicular_line_plane: G = AC ∩ BD and M = midpoint(A, C) both equal (1, 1, 0)
    sq_src = "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 2, SA vuông góc (ABCD), SA = 2. Tính SB."
    sq_base = [
        _c("c1", "pyramid", "hình chóp S.ABCD", apex="S", base=["A", "B", "C", "D"]),
        _c("c2", "regular_polygon", "hình vuông cạnh 2", vertices=["A", "B", "C", "D"], side="2"),
        _c("c3", "perpendicular_line_plane", "SA vuông góc (ABCD)", line=["S", "A"], plane=["A", "B", "C", "D"]),
        _c("c4", "segment_length", "SA = 2", segment=["S", "A"], value="2"),
        _c("c5", "intersect_line_line", "hình vuông cạnh 2", point="G", line1=["A", "C"], line2=["B", "D"]),
        _c("c6", "midpoint", "hình vuông cạnh 2", point="M", segment=["A", "C"]),
    ]
    for sq_extra in (
        _c("d1", "centroid", "hình vuông cạnh 2", point="G", polygon=["A", "M", "C"]),
        _c("d1", "perpendicular_line_plane", "hình vuông cạnh 2", line=["G", "M"], plane=["A", "B", "C", "D"]),
    ):
        with pytest.raises(registry.TuChoi) as exc_sq:
            _run_kiem([*sq_base, sq_extra, _c("q1", "ask_length", "Tính SB", segment=["S", "B"])], sq_src)
        assert exc_sq.value.code == "INCONSISTENT_FACTS", sq_extra["fn"]

    # Collinear plane in perpendicular_line_plane construction raises COLLINEAR_POINTS (never ENGINE_SELF_CHECK_FAILED)
    with pytest.raises(registry.TuChoi) as exc_col_pl:
        _run_kiem([
            _c("c1", "pyramid", "hình chóp S.ABCD", apex="S", base=["A", "B", "C", "D"]),
            _c("c2", "regular_polygon", "hình vuông cạnh 2", vertices=["A", "B", "C", "D"], side="2"),
            _c("c6", "midpoint", "hình vuông cạnh 2", point="M", segment=["A", "C"]),
            _c("c3", "perpendicular_line_plane", "SA vuông góc (ABCD)", line=["S", "A"], plane=["A", "M", "C"]),
            _c("c4", "segment_length", "SA = 2", segment=["S", "A"], value="2"),
            _c("q1", "ask_length", "Tính SB", segment=["S", "B"]),
        ], sq_src)
    assert exc_col_pl.value.code == "COLLINEAR_POINTS"


def test_major_r2_1_mat_vuong_duong_2d_carrier_plane_anchors_serve_face_centroid_and_face_projection():
    # 1. G = centroid(S, A, B), M = midpoint(S, G), plane through M ⊥ SG on S.ABC
    t_cent = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2, SA vuông góc với (ABC), SA = 2. "
        "Gọi G là trọng tâm của tam giác SAB, M là trung điểm của SG. "
        "Tính diện tích thiết diện của hình chóp S.ABC cắt bởi mặt phẳng qua M vuông góc với SG."
    )
    r_cent = _run(
        t_cent,
        [
            {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.ABC", "quotes": ["Cho hình chóp S.ABC"]},
            {"id": "f2", "kind": "polygon_shape", "role": "premise", "shape": "equilateral_triangle", "points": ["A", "B", "C"], "value": "2", "quotes": ["đáy ABC là tam giác đều cạnh 2"]},
            {"id": "f3", "kind": "perpendicular", "role": "premise", "points_a": ["S", "A"], "points_b": ["A", "B", "C"], "quotes": ["SA vuông góc với (ABC)"]},
            {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "A"], "value": "2", "quotes": ["SA = 2"]},
            {"id": "f5", "kind": "point_def", "role": "premise", "point": "G", "point_kind": "centroid", "points": ["S", "A", "B"], "quotes": ["Gọi G là trọng tâm của tam giác SAB"]},
            {"id": "f6", "kind": "point_def", "role": "premise", "point": "M", "point_kind": "midpoint", "points": ["S", "G"], "quotes": ["M là trung điểm của SG"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "area", "solid": "S.ABC", "point": "M", "plane_relation": "perpendicular", "points_b": ["S", "G"], "quotes": ["Tính diện tích thiết diện của hình chóp S.ABC cắt bởi mặt phẳng qua M vuông góc với SG"]},
        ],
    )
    assert r_cent.status == "SERVED", (r_cent.code, r_cent.reason)

    # 2. H = proj(C, SAB), M = midpoint(S, H), plane through M ⊥ SH on S.ABC
    t_proj = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2, SA vuông góc với (ABC), SA = 2. "
        "Gọi H là hình chiếu vuông góc của C lên (SAB), M là trung điểm của SH. "
        "Tính diện tích thiết diện của hình chóp S.ABC cắt bởi mặt phẳng qua M vuông góc với SH."
    )
    r_proj = _run(
        t_proj,
        [
            {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.ABC", "quotes": ["Cho hình chóp S.ABC"]},
            {"id": "f2", "kind": "polygon_shape", "role": "premise", "shape": "equilateral_triangle", "points": ["A", "B", "C"], "value": "2", "quotes": ["đáy ABC là tam giác đều cạnh 2"]},
            {"id": "f3", "kind": "perpendicular", "role": "premise", "points_a": ["S", "A"], "points_b": ["A", "B", "C"], "quotes": ["SA vuông góc với (ABC)"]},
            {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "A"], "value": "2", "quotes": ["SA = 2"]},
            {"id": "f5", "kind": "projection", "role": "premise", "point": "C", "points": ["S", "A", "B"], "at": "H", "quotes": ["Gọi H là hình chiếu vuông góc của C lên (SAB)"]},
            {"id": "f6", "kind": "point_def", "role": "premise", "point": "M", "point_kind": "midpoint", "points": ["S", "H"], "quotes": ["M là trung điểm của SH"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "area", "solid": "S.ABC", "point": "M", "plane_relation": "perpendicular", "points_b": ["S", "H"], "quotes": ["Tính diện tích thiết diện của hình chóp S.ABC cắt bởi mặt phẳng qua M vuông góc với SH"]},
        ],
    )
    assert r_proj.status == "SERVED", (r_proj.code, r_proj.reason)


